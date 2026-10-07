"""Shell runner for the Research V2 J0-J7 7D screen.

This module is deliberately thin orchestration. It validates the frozen dataset,
loads job definitions from the repository specification package, checkpoints
per-job results, and builds summaries. Trading execution is delegated to an
executor callable so this runner does not duplicate Research V2 logic.
"""

from __future__ import annotations

import argparse
from bisect import bisect_left
import csv
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import gzip
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from triggertrade.backtest.models import HistoricalCandle  # noqa: E402
from triggertrade.canonical_json import canonical_json_digest  # noqa: E402
from triggertrade.portfolio_accounting_day import accounting_day_window  # noqa: E402
from triggertrade.research_v2 import (  # noqa: E402
    ResearchV2JobConfig,
    ResearchV2ScreeningOutput,
    ResearchV2SetResolution,
    V2DecisionStatus,
    V2Direction,
    V2SignalResult,
    aggregate_completed_bars,
    atr15,
    compression_breakout_signal,
    continuation_signal,
    ema15,
    latest_protective_swing5,
    load_common_profile,
    load_research_v2_jobs,
    physical_symbol_for_research_v2,
    ret5_ret15_or_signal,
    ret_or_episode_reset_ready,
    return_pct_points,
    reversal_reset_ready,
    reversal_signal,
    resolve_research_v2_set_resolution,
    rvol5,
    turnover_acceleration,
    wilder_atr_series,
)
from triggertrade.research_v2_execution import (  # noqa: E402
    ResearchV2ExecutionError,
    V2PortfolioExposureState,
    VenueConstraints,
    build_research_v2_canonical_execution_profile,
    construct_research_v2_order_spec,
    evaluate_research_v2_g0_structural_eligibility,
    evaluate_research_v2_portfolio_grant,
)
from triggertrade.research_v2_handoff import produce_research_v2_market_handoff  # noqa: E402
from triggertrade.services.research_backtest_execution import (  # noqa: E402
    ResearchV1BacktestLifecycleResult,
    _closed_lifecycle_result,
    _research_v1_backtest_funding_amount,
    _simulate_research_v1_backtest_lifecycle,
)
from triggertrade.set_engine import HandoffContext, HandoffFacts, HandoffReferenceLevel, directional_efficiency, q18_export_text  # noqa: E402


EXPECTED_DATASET_ID = "research-v2-7d-20260819-20260826-v1"
INITIAL_JOBS_PATH = ROOT / "docs" / "research-v2" / "jobs" / "INITIAL_7D_JOBS.json"
_G0_EVIDENCE_TIMELINE_CACHE: dict[tuple[str, str, str, str], FeatureTimeline] = {}
SUPPORTED_ECONOMIC_GATES = {"ECONOMIC_PASS", "MECHANISM_PASS", "FAIL", "DATA_INVALID"}
RESULT_FIELDS = (
    "job_id",
    "config_fingerprint",
    "status",
    "evaluation_start",
    "evaluation_end",
    "unique_signal_episodes",
    "matched",
    "approved",
    "blocked",
    "accepted",
    "filled",
    "closed",
    "censored",
    "open_at_end",
    "pending_at_end",
    "gross_pnl",
    "fees",
    "closed_trade_fees",
    "all_known_execution_fees",
    "open_position_entry_fees",
    "funding",
    "net_closed_pnl",
    "end_mtm_contribution",
    "account_net",
    "actual_margin_used",
    "actual_notional_turnover",
    "mean_net_notional_expectancy",
    "max_mtm_drawdown",
    "stress_net",
    "leave_best_event_out_net",
    "data_invalid_reasons",
    "economic_gate_result",
)
SUMMARY_FIELDS = (
    "job_id",
    "status",
    "account_net_usdt",
    "account_return_pct",
    "fills",
    "unique_filled_episodes",
    "closed",
    "censored",
    "notional_turnover",
    "net_notional_expectancy",
    "fees",
    "closed_trade_fees",
    "all_known_execution_fees",
    "open_position_entry_fees",
    "funding",
    "max_mtm_drawdown_pct",
    "stress_net",
    "leave_best_event_out_net",
    "economic_gate",
)


class ResearchV2RunnerError(RuntimeError):
    """Raised when the shell runner cannot proceed safely."""


JobExecutor = Callable[[ResearchV2JobConfig, Mapping[str, Any], Path], Mapping[str, Any]]


@dataclass(frozen=True)
class FeatureTimeline:
    symbol: str
    physical_symbol: str
    candles: tuple[HistoricalCandle, ...]
    close_times: tuple[datetime, ...]
    by_close: Mapping[datetime, HistoricalCandle]
    return5: Mapping[datetime, Decimal]
    return15: Mapping[datetime, Decimal]
    atr15: Mapping[datetime, Decimal]
    ema20: Mapping[datetime, Decimal]
    ema50: Mapping[datetime, Decimal]
    rvol5: Mapping[datetime, Decimal]
    turnover_acceleration: Mapping[datetime, Decimal]
    compression_atr_median96: Mapping[datetime, Decimal]
    prior_12_range: Mapping[datetime, tuple[Decimal, Decimal]]
    swing_long: Mapping[datetime, Decimal]
    swing_short: Mapping[datetime, Decimal]
    swing_low_refs: tuple["V2TimelineSwingReference", ...]
    swing_high_refs: tuple["V2TimelineSwingReference", ...]


@dataclass(frozen=True)
class V2TimelineSwingReference:
    price: Decimal
    formed_at: datetime
    confirmed_at: datetime
    available_at: datetime
    kind: str


@dataclass(frozen=True)
class RawTradePoint:
    occurred_at: datetime
    price: Decimal
    quantity: Decimal
    source_row_offset: int | None = None
    source_path: str | None = None


@dataclass(frozen=True)
class V2ReplayExposure:
    symbol: str
    physical_symbol: str
    margin: Decimal
    gross_notional: Decimal
    stop_risk: Decimal
    release_at: datetime | None
    context_id: str
    lifecycle_status: str
    order_spec_id: str | None = None
    direction: str | None = None
    entry_price: Decimal | None = None
    quantity: Decimal | None = None
    entry_fee: Decimal = Decimal("0")
    funding: Decimal = Decimal("0")
    opened_at: datetime | None = None
    funding_events: tuple[Mapping[str, Any], ...] = ()


_EVENT_ORDER = {
    "ACCOUNTING_DAY_BOUNDARY": 0,
    "FUNDING_BOUNDARY": 10,
    "PROTECTIVE_EXIT": 20,
    "EXIT_FEE": 30,
    "FINAL_CLOSE": 40,
    "ORDER_CANCEL_REQUEST": 45,
    "ENTRY_CANCELLED_UNFILLED": 46,
    "RESERVATION_RELEASE": 50,
    "ORDER_ACCEPTED": 60,
    "ENTRY_FILLED": 70,
    "ENTRY_FEE": 80,
}


@dataclass(frozen=True)
class V2ReplayAccountEvent:
    timestamp: datetime
    sequence: int
    event_type: str
    context_id: str
    symbol: str
    physical_symbol: str
    order_spec_id: str | None = None
    quantity: Decimal | None = None
    cashflow_amount: Decimal = Decimal("0")
    realized_gross_pnl: Decimal = Decimal("0")
    fee_amount: Decimal = Decimal("0")
    funding_amount: Decimal = Decimal("0")
    source_provenance: Mapping[str, Any] = field(default_factory=dict)
    causal_sequence: int = 0
    admission_ordinal: int | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "timestamp": _iso(self.timestamp),
            "sequence": self.sequence,
            "event_type": self.event_type,
            "context_id": self.context_id,
            "symbol": self.symbol,
            "physical_symbol": self.physical_symbol,
            "order_spec_id": self.order_spec_id,
            "quantity": None if self.quantity is None else str(self.quantity),
            "cashflow_amount": str(self.cashflow_amount),
            "realized_gross_pnl": str(self.realized_gross_pnl),
            "fee_amount": str(self.fee_amount),
            "funding_amount": str(self.funding_amount),
            "source_provenance": dict(self.source_provenance),
            "causal_sequence": self.causal_sequence,
            "admission_ordinal": self.admission_ordinal,
        }
        if self.event_type == "FUNDING_BOUNDARY":
            provenance = dict(self.source_provenance)
            for key in (
                "event_id",
                "funding_timestamp",
                "funding_source_hash",
                "funding_source_provenance",
                "mark_timestamp",
                "mark_source_hash",
                "mark_source_provenance",
                "factual_boundary_mark",
                "funding_rate",
            ):
                payload[key] = provenance.get(key)
        return payload


@dataclass
class V2ReplayPortfolioBook:
    account_capital: Decimal
    active: list[V2ReplayExposure]
    last_accepted_at: dict[str, datetime] = field(default_factory=dict)
    realized_net_by_day: dict[str, Decimal] = field(default_factory=dict)
    realized_fees_by_day: dict[str, Decimal] = field(default_factory=dict)
    realized_funding_by_day: dict[str, Decimal] = field(default_factory=dict)
    account_events: list[V2ReplayAccountEvent] = field(default_factory=list)
    day_opening_equity: dict[str, Decimal] = field(default_factory=dict)
    next_causal_sequence: int = 1
    next_admission_ordinal: int = 1
    factual_timeline_guard_evidence: list[dict[str, Any]] = field(default_factory=list)

    def _allocate_sequence(self) -> int:
        value = self.next_causal_sequence
        self.next_causal_sequence += 1
        return value

    def _allocate_admission_ordinal(self) -> int:
        value = self.next_admission_ordinal
        self.next_admission_ordinal += 1
        return value

    def apply_due(self, as_of: datetime) -> None:
        self.active = [exposure for exposure in self.active if exposure.release_at is None or exposure.release_at > as_of]

    def state_for_symbol(self, symbol: str) -> V2PortfolioExposureState:
        total_margin = sum((item.margin for item in self.active), Decimal("0"))
        symbol_margin = sum((item.margin for item in self.active if item.symbol == symbol), Decimal("0"))
        total_notional = sum((item.gross_notional for item in self.active), Decimal("0"))
        total_stop_risk = sum((item.stop_risk for item in self.active), Decimal("0"))
        total_count = len(self.active)
        symbol_count = sum(1 for item in self.active if item.symbol == symbol)
        return V2PortfolioExposureState(
            account_capital=self.account_capital,
            committed_margin=total_margin,
            coin_committed_margin=symbol_margin,
            gross_notional=total_notional,
            stop_risk=total_stop_risk,
            open_pending_count=total_count,
            coin_open_pending_count=symbol_count,
        )

    def cancel_pending_for_daily_guard(
        self,
        *,
        as_of: datetime,
        trigger: Mapping[str, Any] | None = None,
        retain_until_release: bool = False,
    ) -> list[V2ReplayAccountEvent]:
        cancel_events: list[V2ReplayAccountEvent] = []
        retained: list[V2ReplayExposure] = []
        cancelled_contexts: set[str] = set()
        for exposure in self.active:
            if (exposure.opened_at is None or exposure.opened_at > as_of) and (exposure.release_at is None or exposure.release_at > as_of):
                cancelled_contexts.add(exposure.context_id)
                source = {"reason": "DAILY_LOSS_LIMIT_REACHED_PENDING_CANCEL"}
                if trigger:
                    source.update(dict(trigger))
                cancel_events.append(
                    _account_event(
                        timestamp=as_of,
                        event_type="ORDER_CANCEL_REQUEST",
                        context_id=exposure.context_id,
                        symbol=exposure.symbol,
                        physical_symbol=exposure.physical_symbol,
                        order_spec_id=exposure.order_spec_id,
                        quantity=exposure.quantity,
                        causal_sequence=self._allocate_sequence(),
                        source_provenance=source,
                    )
                )
                cancel_events.append(
                    _account_event(
                        timestamp=as_of,
                        event_type="ENTRY_CANCELLED_UNFILLED",
                        context_id=exposure.context_id,
                        symbol=exposure.symbol,
                        physical_symbol=exposure.physical_symbol,
                        order_spec_id=exposure.order_spec_id,
                        quantity=exposure.quantity,
                        causal_sequence=self._allocate_sequence(),
                        source_provenance=source,
                    )
                )
                cancel_events.append(
                    _account_event(
                        timestamp=as_of,
                        event_type="RESERVATION_RELEASE",
                        context_id=exposure.context_id,
                        symbol=exposure.symbol,
                        physical_symbol=exposure.physical_symbol,
                        order_spec_id=exposure.order_spec_id,
                        quantity=exposure.quantity,
                        causal_sequence=self._allocate_sequence(),
                        source_provenance=source,
                    )
                )
                if retain_until_release:
                    retained.append(
                        replace(
                            exposure,
                            release_at=as_of,
                            lifecycle_status="ENTRY_CANCELLED_UNFILLED",
                        )
                    )
                continue
            retained.append(exposure)
        self.active = retained
        if cancelled_contexts:
            self.account_events = [
                event
                for event in self.account_events
                if not (
                    event.context_id in cancelled_contexts
                    and event.timestamp >= as_of
                    and event.event_type != "ORDER_ACCEPTED"
                )
            ]
        self.account_events.extend(cancel_events)
        self.account_events.sort(key=_account_event_sort_key)
        return cancel_events

    def pending_entry_exposures(self, as_of: datetime) -> tuple[V2ReplayExposure, ...]:
        return tuple(
            exposure
            for exposure in self.active
            if (exposure.opened_at is None or exposure.opened_at > as_of)
            and (exposure.release_at is None or exposure.release_at > as_of)
        )

    def open_position_exposures(self, as_of: datetime) -> tuple[V2ReplayExposure, ...]:
        return tuple(
            exposure
            for exposure in self.active
            if exposure.opened_at is not None
            and exposure.opened_at <= as_of
            and (exposure.release_at is None or exposure.release_at > as_of)
        )

    def commit(
        self,
        *,
        symbol: str,
        physical_symbol: str | None = None,
        economics: Mapping[str, Any],
        release_at: datetime | None,
        context_id: str,
        lifecycle_status: str,
        accepted_at: datetime | None = None,
        order_spec: Mapping[str, Any] | None = None,
        lifecycle: Any = None,
        funding_facts: Sequence[Mapping[str, Any]] = (),
        dataset_manifest: Mapping[str, Any] | None = None,
        mark_cache: dict[str, tuple[HistoricalCandle, ...]] | None = None,
        funding_end_at: datetime | None = None,
    ) -> list[V2ReplayAccountEvent]:
        spec = order_spec["order_spec"] if order_spec is not None else {
            "direction": None,
            "entry": {"price": "0", "quantity": "0"},
            "economics": {"maker_fee_rate": "0"},
        }
        if accepted_at is not None:
            self.last_accepted_at[symbol] = accepted_at
        admission_ordinal = self._allocate_admission_ordinal() if accepted_at is not None else None
        physical = physical_symbol or symbol
        evidence = _lifecycle_evidence(lifecycle)
        opened_at = _optional_time(evidence.get("entry_filled_at"))
        closed = lifecycle.closed_result if isinstance(getattr(lifecycle, "closed_result", None), Mapping) else None
        closed_at = _optional_time(closed.get("closed_at")) if isinstance(closed, Mapping) else None
        order_spec_id = spec.get("order_spec_id")
        quantity = _decimal(spec["entry"]["quantity"])
        direction = str(spec.get("direction") or "").upper()
        entry = _decimal(spec["entry"]["price"])
        entry_fee = _decimal(economics["actual_order_notional"]) * _decimal(spec["economics"]["maker_fee_rate"])
        endpoint_open = closed_at is None and str(getattr(lifecycle, "status", "")) == "FILLED_OPEN_AT_ENDPOINT"
        funding_events = (
            _funding_events_for_position(
                funding_facts=funding_facts,
                dataset_manifest=dataset_manifest,
                mark_cache=mark_cache,
                order=spec,
                context_id=context_id,
                opened_at=opened_at,
                closed_at=closed_at or funding_end_at,
                include_right_boundary=not endpoint_open,
            )
            if opened_at is not None
            else ()
        )
        new_events = _account_events_for_lifecycle(
            symbol=symbol,
            physical_symbol=physical,
            context_id=context_id,
            order_spec_id=str(order_spec_id) if order_spec_id is not None else None,
            accepted_at=accepted_at,
            opened_at=opened_at,
            release_at=release_at,
            closed=closed,
            direction=direction,
            entry=entry,
            quantity=quantity,
            entry_fee=entry_fee,
            exit_fee=_decimal(closed.get("exit_fee", "0")) if isinstance(closed, Mapping) else Decimal("0"),
            funding_events=funding_events,
            causal_sequence_factory=self._allocate_sequence,
            admission_ordinal=admission_ordinal,
        )
        self.account_events.extend(new_events)
        self.account_events.sort(key=_account_event_sort_key)
        self.active.append(
            V2ReplayExposure(
                symbol=symbol,
                physical_symbol=physical,
                margin=_decimal(economics["actual_committed_margin"]),
                gross_notional=_decimal(economics["actual_order_notional"]),
                stop_risk=_decimal(economics["actual_stop_risk"]),
                release_at=release_at,
                context_id=context_id,
                lifecycle_status=lifecycle_status,
                order_spec_id=None if order_spec_id is None else str(order_spec_id),
                direction=str(spec.get("direction")),
                entry_price=_decimal(spec["entry"]["price"]),
                quantity=_decimal(spec["entry"]["quantity"]),
                entry_fee=entry_fee,
                funding=Decimal("0"),
                opened_at=opened_at,
                funding_events=funding_events,
            )
        )
        return new_events

    def cooldown_evidence(self, *, symbol: str, accepted_at: datetime, cooldown_minutes: int) -> dict[str, Any]:
        previous = self.last_accepted_at.get(symbol)
        cooldown_until = None if previous is None else previous + timedelta(minutes=cooldown_minutes)
        remaining = None if cooldown_until is None else max((cooldown_until - accepted_at).total_seconds(), 0)
        passed = cooldown_until is None or accepted_at >= cooldown_until
        return {
            "candidate_allowed": passed,
            "candidate_acceptance_time": _iso(accepted_at),
            "accepted": False,
            "accepted_at": None,
            "candidate_accepted_at": _iso(accepted_at),
            "previous_same_symbol_accepted_at": None if previous is None else _iso(previous),
            "cooldown_minutes": cooldown_minutes,
            "cooldown_until": None if cooldown_until is None else _iso(cooldown_until),
            "cooldown_remaining_seconds": None if remaining is None else str(Decimal(str(remaining)).quantize(Decimal("0.000001"))),
            "cooldown_decision": "PASS" if passed else "REJECT",
            "reason_code": "ALLOW" if passed else "COOLDOWN_ACTIVE",
        }


class RawTradeIndex:
    def __init__(self, *, logical_symbol: str, physical_symbol: str, archives: Sequence[Path]) -> None:
        self.logical_symbol = logical_symbol
        self.physical_symbol = physical_symbol
        self._archives = tuple(archives)
        self._records_by_day: dict[str, tuple[RawTradePoint, ...]] = {}
        self._timestamps_by_day: dict[str, tuple[datetime, ...]] = {}
        self._minute_candles_by_day: dict[str, tuple[HistoricalCandle, ...]] = {}
        self._minute_times_by_day: dict[str, tuple[datetime, ...]] = {}

    def range_as_candles(self, *, start: datetime, end: datetime) -> tuple[HistoricalCandle, ...]:
        candles: list[HistoricalCandle] = []
        day = start.date()
        while day <= end.date():
            rows = self._day_minute_candles(day.isoformat())
            times = self._day_minute_times(day.isoformat())
            left = bisect_left(times, start.replace(second=0, microsecond=0))
            for candle in rows[left:]:
                if candle.open_time >= end:
                    break
                if candle.close_time <= start:
                    continue
                candles.append(candle)
            day = day + timedelta(days=1)
        if not candles:
            raise ResearchV2RunnerError(f"RAW_TRADES_DATA_INVALID:{self.logical_symbol}:{_iso(start)}:{_iso(end)}")
        return tuple(candles)

    def _range(self, *, start: datetime, end: datetime) -> tuple[RawTradePoint, ...]:
        out: list[RawTradePoint] = []
        day = start.date()
        while day <= end.date():
            rows = self._day(day.isoformat())
            timestamps = self._day_timestamps(day.isoformat())
            left = bisect_left(timestamps, start)
            for row in rows[left:]:
                if row.occurred_at >= end:
                    break
                if row.occurred_at >= start:
                    out.append(row)
            day = day + timedelta(days=1)
        return tuple(out)

    def _day(self, day: str) -> tuple[RawTradePoint, ...]:
        if day not in self._records_by_day:
            archive = self._archive_for_day(day)
            if archive is None:
                self._records_by_day[day] = ()
            else:
                self._records_by_day[day] = tuple(_iter_raw_trade_points(archive))
        return self._records_by_day[day]

    def _archive_for_day(self, day: str) -> Path | None:
        return next((path for path in self._archives if day in path.name), None)

    def source_identity_for_time(self, timestamp: datetime) -> dict[str, Any]:
        archive = self._archive_for_day(timestamp.date().isoformat())
        if archive is None:
            return {"source_file": None, "source_hash": None, "physical_symbol": self.physical_symbol}
        return {"source_file": str(archive), "source_hash": sha256_file(archive), "physical_symbol": self.physical_symbol}

    def _day_timestamps(self, day: str) -> tuple[datetime, ...]:
        if day not in self._timestamps_by_day:
            self._timestamps_by_day[day] = tuple(row.occurred_at for row in self._day(day))
        return self._timestamps_by_day[day]

    def _day_minute_candles(self, day: str) -> tuple[HistoricalCandle, ...]:
        if day not in self._minute_candles_by_day:
            buckets: dict[datetime, list[RawTradePoint]] = defaultdict(list)
            for record in self._day(day):
                minute = record.occurred_at.replace(second=0, microsecond=0)
                buckets[minute].append(record)
            candles: list[HistoricalCandle] = []
            for minute in sorted(buckets):
                rows = buckets[minute]
                candles.append(
                    HistoricalCandle(
                        symbol=self.physical_symbol,
                        category="linear",
                        timeframe="1m",
                        open_time=minute,
                        close_time=minute + timedelta(minutes=1),
                        open=rows[0].price,
                        high=max(row.price for row in rows),
                        low=min(row.price for row in rows),
                        close=rows[-1].price,
                        volume=sum((row.quantity for row in rows), Decimal("0")),
                        turnover=sum((row.quantity * row.price for row in rows), Decimal("0")),
                        completed=True,
                    )
                )
            self._minute_candles_by_day[day] = tuple(candles)
            self._minute_times_by_day[day] = tuple(candle.open_time for candle in candles)
        return self._minute_candles_by_day[day]

    def _day_minute_times(self, day: str) -> tuple[datetime, ...]:
        if day not in self._minute_times_by_day:
            self._day_minute_candles(day)
        return self._minute_times_by_day[day]


class ProgressReporter:
    def __init__(self, *, output_dir: Path, global_units_total: int) -> None:
        self.output_dir = output_dir
        self.path = output_dir / "progress.json"
        self.started = time.perf_counter()
        self.last_write = 0.0
        self.global_units_total = max(global_units_total, 1)
        self.payload: dict[str, Any] = {
            "status": "RUNNING",
            "phase": "INITIALIZING",
            "current_set": None,
            "current_job": None,
            "current_symbol": None,
            "current_observed_at": None,
            "phase_units_done": 0,
            "phase_units_total": 0,
            "global_units_done": 0,
            "global_units_total": self.global_units_total,
            "progress_pct": 0.0,
            "elapsed_seconds": 0.0,
            "units_per_second": 0.0,
            "eta_seconds": None,
            "set_evaluations": 0,
            "matched_episodes": 0,
            "execution_contexts_total": 0,
            "execution_contexts_done": 0,
            "position_evaluations": 0,
            "orders_created": 0,
            "fills": 0,
            "closed": 0,
            "last_update": now_iso(),
        }
        self.write(force=True)

    def update(self, *, force: bool = False, **kwargs: Any) -> None:
        self.payload.update(kwargs)
        self.write(force=force)

    def write(self, *, force: bool = False) -> None:
        now = time.perf_counter()
        if not force and now - self.last_write < 2:
            return
        elapsed = max(now - self.started, 0.000001)
        done = int(self.payload.get("global_units_done") or 0)
        total = max(int(self.payload.get("global_units_total") or self.global_units_total), 1)
        rate = done / elapsed
        eta = None if done <= 0 or rate <= 0 else max((total - done) / rate, 0)
        self.payload.update(
            {
                "progress_pct": float(min(max(Decimal(done) / Decimal(total) * Decimal("100"), Decimal("0")), Decimal("100"))),
                "elapsed_seconds": elapsed,
                "units_per_second": rate,
                "eta_seconds": eta,
                "last_update": now_iso(),
            }
        )
        write_json(self.path, self.payload)
        self.last_write = now
        print(
            f"[{self.payload['phase']}] {self.payload.get('current_job') or '-'} | "
            f"{self.payload.get('current_symbol') or '-'} | {self.payload['progress_pct']:.1f}% total | "
            f"{done}/{total} | matches={self.payload.get('matched_episodes')} | "
            f"ETA {'' if eta is None else int(eta)}s",
            flush=True,
        )

    def complete(self) -> None:
        self.payload["status"] = "COMPLETE"
        self.payload["global_units_done"] = self.payload["global_units_total"]
        self.write(force=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Research V2 J0-J7 7D screen from a frozen dataset.")
    parser.add_argument("--dataset", required=True, type=Path, help="Path to dataset_manifest.json")
    parser.add_argument("--output", required=True, type=Path, help="Output directory for checkpoints and summaries")
    parser.add_argument("--jobs", required=True, help="Comma-separated job IDs or ALL")
    parser.add_argument("--population", type=Path, default=None, help="Existing materialized Research V2 Set population")
    parser.add_argument("--replay-only", action="store_true", help="Skip Set materialization and replay an existing population")
    parser.add_argument("--resume", action="store_true", help="Resume from completed job checkpoints in the output directory")
    parser.add_argument("--max-jobs", type=int, default=None, help="Optional maximum number of pending jobs to execute")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        completed, total = run_screen(
            dataset_path=args.dataset,
            output_dir=args.output,
            jobs_arg=args.jobs,
            resume=args.resume,
            max_jobs=args.max_jobs,
            population_path=args.population,
            replay_only=args.replay_only,
        )
    except ResearchV2RunnerError as exc:
        print(f"BLOCKED: {exc}")
        return 2
    print(f"COMPLETE: {completed}/{total}")
    print(f"OUTPUT: {args.output}")
    return 0


def finalize_research_v2_existing_run(
    *,
    output_dir: Path,
    dataset_path: Path,
    jobs_arg: str = "ALL",
) -> dict[str, Any]:
    """Refresh evidence-only artifacts for a completed Research V2 run.

    This path intentionally does not replay trading decisions. It consumes the
    completed lifecycle/ledger artifacts, synchronizes derived evidence, and
    verifies that economic event identities are unchanged by finalization.
    """
    manifest = validate_dataset(dataset_path)
    selected_jobs = select_jobs(jobs_arg, load_ordered_jobs())
    output_dir = output_dir.resolve()
    lifecycle_path = output_dir / "lifecycle_results.jsonl"
    ledger_path = output_dir / "account_event_ledger.jsonl"
    if not lifecycle_path.exists():
        raise ResearchV2RunnerError(f"EVIDENCE_FINALIZATION_BLOCKED:LIFECYCLE_RESULTS_MISSING:{lifecycle_path}")
    if not ledger_path.exists():
        raise ResearchV2RunnerError(f"EVIDENCE_FINALIZATION_BLOCKED:ACCOUNT_EVENT_LEDGER_MISSING:{ledger_path}")
    before = _economic_event_fingerprint(output_dir)
    _write_phase_b_job_results(
        output_dir,
        selected_jobs,
        contexts=(),
        dataset_manifest=manifest,
        apply_daily_cancel_overrides=False,
    )
    after = _economic_event_fingerprint(output_dir)
    if before["digest"] != after["digest"]:
        raise ResearchV2RunnerError("ECONOMIC_EVENT_FINGERPRINT_CHANGED")
    progress = json.loads((output_dir / "progress.json").read_text(encoding="utf-8")) if (output_dir / "progress.json").exists() else {}
    lifecycle_rows = read_jsonl(lifecycle_path)
    return {
        "status": "COMPLETE",
        "mode": "EVIDENCE_ONLY_FINALIZATION",
        "output_dir": str(output_dir),
        "dataset_manifest": str(dataset_path),
        "jobs": jobs_arg,
        "contexts": len(lifecycle_rows),
        "accepted": progress.get("orders_created"),
        "fills": progress.get("fills"),
        "closed": progress.get("closed"),
        "economic_event_fingerprint": after["digest"],
        "economic_event_fingerprint_changed": False,
    }


def run_screen(
    *,
    dataset_path: Path,
    output_dir: Path,
    jobs_arg: str,
    resume: bool = False,
    max_jobs: int | None = None,
    executor: JobExecutor | None = None,
    population_path: Path | None = None,
    replay_only: bool = False,
) -> tuple[int, int]:
    manifest = validate_dataset(dataset_path)
    jobs = load_ordered_jobs()
    selected_jobs = select_jobs(jobs_arg, jobs)
    if max_jobs is not None:
        if max_jobs < 0:
            raise ResearchV2RunnerError("--max-jobs must be non-negative")
        selected_jobs = selected_jobs[:max_jobs]

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "jobs").mkdir(exist_ok=True)
    if population_path is not None and not replay_only:
        raise ResearchV2RunnerError("--population requires --replay-only")
    if replay_only and population_path is None:
        raise ResearchV2RunnerError("--replay-only requires --population")
    if replay_only and executor is not None:
        raise ResearchV2RunnerError("--replay-only uses the canonical V2 replay path and cannot use an injected executor")
    if executor is None:
        if replay_only:
            assert population_path is not None
            return run_screen_replay_only(
                manifest=manifest,
                selected_jobs=selected_jobs,
                output_dir=output_dir,
                population_path=population_path,
                resume=resume,
            )
        return run_screen_two_phase(
            manifest=manifest,
            selected_jobs=selected_jobs,
            output_dir=output_dir,
            resume=resume,
        )
    completed_identities = completed_checkpoint_identities(output_dir) if resume else set()
    active_executor = executor

    completed_count = 0
    total = len(selected_jobs)
    for index, job in enumerate(selected_jobs, start=1):
        identity = job_identity(job)
        if identity in completed_identities:
            completed_count += 1
            print(f"[{job.job_id}] {completed_count}/{total} complete | status=SKIPPED_RESUME | net=NA | fills=NA")
            continue
        try:
            result = normalize_job_result(active_executor(job, manifest, output_dir), job=job)
            persist_job_result(output_dir, job, result)
            append_jsonl(output_dir / "job_results.jsonl", result)
            completed_count += 1
            write_run_state(output_dir, selected_jobs, completed_count=completed_count, failed_count=count_jsonl(output_dir / "job_errors.jsonl"))
            print(
                f"[{job.job_id}] {completed_count}/{total} complete | "
                f"status={result['status']} | net={result['account_net']} | fills={result['filled']}"
            )
        except Exception as exc:  # noqa: BLE001
            error = {
                "job_id": job.job_id,
                "config_fingerprint": job.config_fingerprint,
                "error": str(exc),
                "error_type": type(exc).__name__,
                "recorded_at": now_iso(),
            }
            append_jsonl(output_dir / "job_errors.jsonl", error)
            write_run_state(output_dir, selected_jobs, completed_count=completed_count, failed_count=count_jsonl(output_dir / "job_errors.jsonl"))
            rebuild_summary(output_dir)
            raise ResearchV2RunnerError(f"{job.job_id} failed: {exc}") from exc

    rebuild_summary(output_dir)
    write_run_state(output_dir, selected_jobs, completed_count=completed_count, failed_count=count_jsonl(output_dir / "job_errors.jsonl"))
    return completed_count, total


def run_screen_replay_only(
    *,
    manifest: Mapping[str, Any],
    selected_jobs: Sequence[ResearchV2JobConfig],
    output_dir: Path,
    population_path: Path,
    resume: bool = False,
) -> tuple[int, int]:
    resolved_population_path = _resolve_population_path(population_path)
    _validate_replay_only_output_dir(output_dir=output_dir, population_path=resolved_population_path, resume=resume)
    population = load_research_v2_set_population(
        resolved_population_path,
        dataset_manifest=manifest,
        selected_jobs=selected_jobs,
    )
    contexts = _execution_contexts_from_population(population, selected_jobs)
    reporter = ProgressReporter(output_dir=output_dir, global_units_total=max(len(contexts), 1))
    reporter.update(
        phase="REPLAY",
        phase_units_total=len(contexts),
        global_units_total=max(len(contexts), 1),
        execution_contexts_total=len(contexts),
        force=True,
    )
    completed, total = replay_research_v2_materialized_population(
        contexts=contexts,
        dataset_manifest=manifest,
        output_dir=output_dir,
        resume=resume,
        progress=reporter,
        phase_a_units_done=0,
    )
    _write_phase_b_job_results(output_dir, selected_jobs, contexts, dataset_manifest=manifest)
    rebuild_summary(output_dir)
    write_run_state(output_dir, selected_jobs, completed_count=completed, failed_count=count_jsonl(output_dir / "job_errors.jsonl"))
    reporter.complete()
    return completed, total


def run_screen_two_phase(
    *,
    manifest: Mapping[str, Any],
    selected_jobs: Sequence[ResearchV2JobConfig],
    output_dir: Path,
    resume: bool = False,
) -> tuple[int, int]:
    materialize_jobs = [job for job in selected_jobs if job.signal_family != "LEGACY_SET"]
    phase_a_units = _phase_a_units(materialize_jobs, manifest)
    reporter = ProgressReporter(output_dir=output_dir, global_units_total=phase_a_units + 1)
    population = materialize_research_v2_set_population(
        jobs=materialize_jobs,
        dataset_manifest=manifest,
        output_dir=output_dir,
        progress=reporter,
    )
    contexts = _execution_contexts_from_population(population, selected_jobs)
    reporter.payload["global_units_total"] = phase_a_units + max(len(contexts), 1)
    reporter.payload["execution_contexts_total"] = len(contexts)
    completed, total = replay_research_v2_materialized_population(
        contexts=contexts,
        dataset_manifest=manifest,
        output_dir=output_dir,
        resume=resume,
        progress=reporter,
        phase_a_units_done=phase_a_units,
    )
    _write_phase_b_job_results(output_dir, selected_jobs, contexts, dataset_manifest=manifest)
    rebuild_summary(output_dir)
    write_run_state(output_dir, selected_jobs, completed_count=completed, failed_count=count_jsonl(output_dir / "job_errors.jsonl"))
    reporter.complete()
    return completed, total


def load_research_v2_set_population(
    population_path: Path,
    *,
    dataset_manifest: Mapping[str, Any],
    selected_jobs: Sequence[ResearchV2JobConfig],
) -> dict[str, Any]:
    resolved = _resolve_population_path(population_path)
    if not resolved.exists():
        raise ResearchV2RunnerError(f"population file missing: {resolved}")
    population = json.loads(resolved.read_text(encoding="utf-8"))
    if population.get("artifact_type") != "RESEARCH_V2_MATERIALIZED_SET_POPULATION":
        raise ResearchV2RunnerError(f"unsupported population artifact_type: {population.get('artifact_type')}")
    if population.get("dataset_id") != dataset_manifest.get("dataset_id"):
        raise ResearchV2RunnerError(
            f"population dataset_id mismatch: {population.get('dataset_id')} != {dataset_manifest.get('dataset_id')}"
        )
    records = population.get("records")
    if not isinstance(records, list):
        raise ResearchV2RunnerError("population records must be a list")

    selected_job_ids = {job.job_id for job in selected_jobs if job.signal_family != "LEGACY_SET"}
    population_job_ids = {
        str(job_id)
        for record in records
        for job_id in record.get("applicable_jobs", ())
    }
    missing = sorted(selected_job_ids - population_job_ids)
    if missing:
        raise ResearchV2RunnerError(f"population does not contain selected jobs: {','.join(missing)}")
    for index, record in enumerate(records):
        _validate_population_record(record, index=index)
    return population


def _resolve_population_path(population_path: Path) -> Path:
    return (population_path if population_path.is_absolute() else ROOT / population_path).resolve()


def _validate_replay_only_output_dir(*, output_dir: Path, population_path: Path, resume: bool) -> None:
    resolved_output = output_dir.resolve()
    if resolved_output == population_path.parent.resolve():
        raise ResearchV2RunnerError("replay-only output_dir must be fresh and must not be the population source directory")
    if resume:
        return
    stale_files = (
        "lifecycle_results.jsonl",
        "lifecycle_errors.jsonl",
        "job_results.jsonl",
        "job_errors.jsonl",
        "screen_summary.json",
        "screen_summary.csv",
        "run_state.json",
    )
    existing = [name for name in stale_files if (output_dir / name).exists()]
    if existing:
        raise ResearchV2RunnerError(
            "fresh output directory required for replay-only; found existing checkpoint files: " + ",".join(existing)
        )


def _validate_population_record(record: Mapping[str, Any], *, index: int) -> None:
    required = (
        "applicable_jobs",
        "config_fingerprint",
        "decision_cycle_id",
        "direction",
        "observed_at",
        "physical_symbol",
        "set_result_id",
        "set_scan_key",
        "symbol",
    )
    missing = [field for field in required if field not in record]
    if missing:
        raise ResearchV2RunnerError(f"population record {index} missing fields: {','.join(missing)}")
    if "evidence_digest" not in record and "source_evidence_digest" not in record:
        raise ResearchV2RunnerError(f"population record {index} missing evidence digest")
    if any(field in record for field in ("portfolio_grant", "order_spec", "backtest_lifecycle", "lifecycle_result")):
        raise ResearchV2RunnerError(f"population record {index} contains replay state")


def materialize_research_v2_set_population(
    *,
    jobs: Sequence[ResearchV2JobConfig],
    dataset_manifest: Mapping[str, Any],
    output_dir: Path,
    progress: ProgressReporter | None = None,
) -> dict[str, Any]:
    artifact_path = output_dir / "research_v2_set_population.json"
    set_jobs = _dedupe_set_scan_jobs(jobs)
    phase_total = _phase_a_units(set_jobs, dataset_manifest)
    records: list[dict[str, Any]] = []
    diagnostics = {
        "calendar_slots_evaluated": 0,
        "unique_set_configurations_scanned": len(set_jobs),
        "duplicate_episodes_removed": 0,
        "matched_by_set": defaultdict(int),
        "matched_by_symbol": defaultdict(int),
        "matched_by_direction": defaultdict(int),
        "j4_j7_shared_population": any(job.job_id == "J4" for job in set_jobs) and any(job.job_id == "J7" for job in jobs),
    }
    seen_episodes: set[tuple[str, str, str, str]] = set()
    timelines: dict[str, FeatureTimeline] = {}
    done = 0
    started = time.perf_counter()
    for job in set_jobs:
        for symbol in job.symbols:
            physical = physical_symbol_for_research_v2(symbol)
            timeline = timelines.get(symbol)
            if timeline is None:
                timeline = build_research_v2_feature_timeline(
                    symbol=symbol,
                    physical_symbol=physical,
                    candles=_load_dataset_candles(dataset_manifest, physical_symbol=physical),
                )
                timelines[symbol] = timeline
            venue = _load_dataset_venue(dataset_manifest, physical_symbol=physical)
            active_episode: V2Direction | None = None
            reset_buffer: list[tuple[Decimal, Decimal]] = []
            for observed_at in _job_calendar_cutoffs(job, timeline.candles):
                signal, evidence = _evaluate_job_signal_from_timeline(job, timeline=timeline, cutoff=observed_at, venue=venue)
                _append_candidate_census(
                    output_dir=output_dir,
                    job=job,
                    symbol=symbol,
                    observed_at=observed_at,
                    signal=signal,
                    evidence=evidence,
                )
                diagnostics["calendar_slots_evaluated"] += 1
                done += 1
                if progress is not None:
                    progress.update(
                        phase="MATERIALIZE",
                        current_set=_set_scan_key(job),
                        current_job=job.job_id,
                        current_symbol=symbol,
                        current_observed_at=_iso(observed_at),
                        phase_units_done=done,
                        phase_units_total=phase_total,
                        global_units_done=done,
                        set_evaluations=diagnostics["calendar_slots_evaluated"],
                        matched_episodes=len(records),
                    )
                r5 = _optional_decimal(evidence.get("return5_pct_points"))
                r15 = _optional_decimal(evidence.get("return15_pct_points"))
                if r5 is not None and r15 is not None:
                    reset_buffer.append((r5, r15))
                    reset_buffer = reset_buffer[-2:]
                reset_ready = _episode_reset_ready(job, reset_buffer)
                if signal.status is V2DecisionStatus.PASS and active_episode == signal.direction:
                    diagnostics["duplicate_episodes_removed"] += 1
                    continue
                if signal.status is V2DecisionStatus.PASS:
                    active_episode = signal.direction
                elif reset_ready:
                    active_episode = None
                if signal.status is not V2DecisionStatus.PASS:
                    continue
                resolution = resolve_research_v2_set_resolution(
                    job=job,
                    symbol=symbol,
                    physical_symbol=physical,
                    observed_at=observed_at,
                    signal_result=signal,
                    source_feature_evidence=evidence,
                )
                if resolution.status != "MATCHED":
                    continue
                episode_key = (_set_scan_key(job), symbol, resolution.direction.value, resolution.signal_episode_id)
                if episode_key in seen_episodes:
                    diagnostics["duplicate_episodes_removed"] += 1
                    continue
                seen_episodes.add(episode_key)
                record = {
                    "set_family": str(job.runtime_profile["signal"]["family"]),
                    "set_scan_key": _set_scan_key(job),
                    "applicable_jobs": [item.job_id for item in jobs if _set_scan_key(item) == _set_scan_key(job)],
                    "research_identity": _research_identity_payload(job),
                    "symbol": symbol,
                    "physical_symbol": physical,
                    "observed_at": resolution.observed_at,
                    "direction": resolution.direction.value,
                    "episode_id": resolution.signal_episode_id,
                    "decision_cycle_id": resolution.decision_cycle_id,
                    "set_result_id": resolution.set_result_id,
                    "config_fingerprint": resolution.config_fingerprint,
                    "job_config_fingerprint": resolution.job_config_fingerprint,
                    "source_evidence_digest": resolution.source_evidence_digest,
                    "factual_feature_evidence": dict(evidence),
                    "source_dataset_id": dataset_manifest.get("dataset_id"),
                    "resolution": resolution.to_payload(),
                }
                records.append(record)
                diagnostics["matched_by_set"][_set_scan_key(job)] += 1
                diagnostics["matched_by_symbol"][symbol] += 1
                diagnostics["matched_by_direction"][resolution.direction.value] += 1
    artifact = {
        "artifact_type": "RESEARCH_V2_MATERIALIZED_SET_POPULATION",
        "dataset_id": dataset_manifest.get("dataset_id"),
        "created_at": now_iso(),
        "selected_jobs": [job.job_id for job in jobs],
        "records": sorted(records, key=lambda item: (item["observed_at"], item["symbol"], item["set_scan_key"], item["set_result_id"])),
        "summary": {
            "calendar_slots_evaluated": diagnostics["calendar_slots_evaluated"],
            "unique_set_configurations_scanned": diagnostics["unique_set_configurations_scanned"],
            "symbol_count": len({record["symbol"] for record in records}),
            "matched_episodes": len(records),
            "matched_by_set": dict(sorted(diagnostics["matched_by_set"].items())),
            "matched_by_symbol": dict(sorted(diagnostics["matched_by_symbol"].items())),
            "matched_by_direction": dict(sorted(diagnostics["matched_by_direction"].items())),
            "duplicate_episodes_removed": diagnostics["duplicate_episodes_removed"],
            "j4_j7_shared_population": diagnostics["j4_j7_shared_population"],
            "feature_timeline_build_and_scan_seconds": time.perf_counter() - started,
        },
    }
    write_json(artifact_path, artifact)
    return artifact


def replay_research_v2_materialized_population(
    *,
    contexts: Sequence[Mapping[str, Any]],
    dataset_manifest: Mapping[str, Any],
    output_dir: Path,
    resume: bool,
    progress: ProgressReporter | None,
    phase_a_units_done: int,
) -> tuple[int, int]:
    results_path = output_dir / "lifecycle_results.jsonl"
    errors_path = output_dir / "lifecycle_errors.jsonl"
    completed = {_context_identity(row["context"]) for row in read_jsonl(results_path)} if resume else set()
    errors = {_context_identity(row["context"]) for row in read_jsonl(errors_path)} if resume else set()
    done = 0
    raw_indexes: dict[str, RawTradeIndex] = {}
    candles_cache: dict[str, tuple[HistoricalCandle, ...]] = {}
    venue_cache: dict[str, VenueConstraints] = {}
    funding_cache: dict[str, tuple[Mapping[str, Any], ...]] = {}
    mark_cache: dict[str, tuple[HistoricalCandle, ...]] = {}
    portfolio_state: dict[str, V2ReplayPortfolioBook] = {}
    for index, context in enumerate(contexts, start=1):
        identity = _context_identity(context)
        if identity in completed or identity in errors:
            done += 1
            continue
        if progress is not None:
            progress.update(
                phase="REPLAY",
                current_set=str(context["set_scan_key"]),
                current_job=str(context["job_id"]),
                current_symbol=str(context["symbol"]),
                current_observed_at=str(context["observed_at"]),
                phase_units_done=done,
                phase_units_total=len(contexts),
                global_units_done=phase_a_units_done + done,
                execution_contexts_done=done,
                execution_contexts_total=len(contexts),
            )
        try:
            result = _replay_one_context(
                context=context,
                dataset_manifest=dataset_manifest,
                raw_indexes=raw_indexes,
                candles_cache=candles_cache,
                venue_cache=venue_cache,
                funding_cache=funding_cache,
                mark_cache=mark_cache,
                portfolio_state=portfolio_state,
            )
            row = {"index": index, "context": _context_payload(context), "result": result}
            append_jsonl(results_path, row)
            _append_replay_evidence(
                output_dir=output_dir,
                context=context,
                result=result,
                dataset_manifest=dataset_manifest,
                lifecycle_index=index,
            )
            completed.add(identity)
            if progress is not None:
                lifecycle = result.get("backtest_lifecycle", {})
                progress.update(
                    position_evaluations=int(progress.payload.get("position_evaluations") or 0) + 1,
                    orders_created=int(progress.payload.get("orders_created") or 0) + (1 if result.get("order_spec") else 0),
                    fills=int(progress.payload.get("fills") or 0) + (1 if lifecycle.get("filled") else 0),
                    closed=int(progress.payload.get("closed") or 0) + (1 if lifecycle.get("status") == "CLOSED" else 0),
                )
        except Exception as exc:  # noqa: BLE001
            row = {"index": index, "context": _context_payload(context), "exception_type": type(exc).__name__, "exception": str(exc)}
            append_jsonl(errors_path, row)
            errors.add(identity)
        done += 1
        if progress is not None:
            progress.update(
                phase="REPLAY",
                phase_units_done=done,
                phase_units_total=len(contexts),
                global_units_done=phase_a_units_done + done,
                execution_contexts_done=done,
                execution_contexts_total=len(contexts),
                force=done == len(contexts),
            )
    return len(completed), len(contexts)


def build_research_v2_feature_timeline(
    *,
    symbol: str,
    physical_symbol: str,
    candles: Sequence[HistoricalCandle],
) -> FeatureTimeline:
    rows = tuple(sorted(candles, key=lambda item: item.close_time))
    by_close = {candle.close_time: candle for candle in rows if candle.completed}
    ret5: dict[datetime, Decimal] = {}
    ret15: dict[datetime, Decimal] = {}
    for candle in rows:
        for minutes, target in ((5, ret5), (15, ret15)):
            ref = by_close.get(candle.close_time - timedelta(minutes=minutes))
            if ref is not None and ref.close != 0:
                target[candle.close_time] = ((candle.close / ref.close) - Decimal("1")) * Decimal("100")
    bars5 = aggregate_completed_bars(rows, timeframe_minutes=5)
    bars15 = aggregate_completed_bars(rows, timeframe_minutes=15)
    atr_series = dict(wilder_atr_series(bars15, period=14))
    ema20 = _ema_series(bars15, 20)
    ema50 = _ema_series(bars15, 50)
    rvol: dict[datetime, Decimal] = {}
    accel: dict[datetime, Decimal] = {}
    prior_range: dict[datetime, tuple[Decimal, Decimal]] = {}
    for idx, bar in enumerate(bars5):
        if idx >= 20:
            mean = sum((item.turnover for item in bars5[idx - 20:idx]), Decimal("0")) / Decimal("20")
            if mean != 0:
                rvol[bar.close_time] = bar.turnover / mean
        if idx >= 1 and bars5[idx - 1].turnover != 0:
            accel[bar.close_time] = bar.turnover / bars5[idx - 1].turnover
        if idx >= 12:
            prior = bars5[idx - 12:idx]
            prior_range[bar.close_time] = (max(item.high for item in prior), min(item.low for item in prior))
    atr_median: dict[datetime, Decimal] = {}
    atr_items = tuple(sorted(atr_series.items()))
    for idx, (ts, _value) in enumerate(atr_items):
        if idx >= 96:
            atr_median[ts] = _median_decimal(tuple(value for _ts, value in atr_items[idx - 96:idx]))
    swing_long, swing_short, swing_lows, swing_highs = _latest_swing_maps(bars5)
    return FeatureTimeline(
        symbol=symbol,
        physical_symbol=physical_symbol,
        candles=rows,
        close_times=tuple(candle.close_time for candle in rows),
        by_close=by_close,
        return5=ret5,
        return15=ret15,
        atr15=atr_series,
        ema20=ema20,
        ema50=ema50,
        rvol5=rvol,
        turnover_acceleration=accel,
        compression_atr_median96=atr_median,
        prior_12_range=prior_range,
        swing_long=swing_long,
        swing_short=swing_short,
        swing_low_refs=swing_lows,
        swing_high_refs=swing_highs,
    )


def _evaluate_job_signal_from_timeline(
    job: ResearchV2JobConfig,
    *,
    timeline: FeatureTimeline,
    cutoff: datetime,
    venue: VenueConstraints | None = None,
):
    latest = timeline.by_close.get(cutoff)
    r5 = timeline.return5.get(cutoff)
    r15 = timeline.return15.get(cutoff)
    atr_value = _latest_at_or_before(timeline.atr15, cutoff)
    evidence: dict[str, Any] = {
        "cutoff": _iso(cutoff),
        "reference_price": None if latest is None else str(latest.close),
        "return5_pct_points": None if r5 is None else str(r5),
        "return15_pct_points": None if r15 is None else str(r15),
        "atr15": None if atr_value is None else _q18_decimal_text(atr_value),
    }
    if latest is None or r5 is None or r15 is None or atr_value is None:
        return _unavailable_signal(job, "TIMELINE_FEATURE_UNAVAILABLE"), evidence
    base = ret5_ret15_or_signal(return5_pct_points=r5, return15_pct_points=r15)
    family = str(job.runtime_profile["signal"]["family"])
    if family in {"RET5_RET15_OR", "RET5_OR_RET15"}:
        signal = base
    elif family == "RET_OR_TREND_ONLY":
        ema20_value = _latest_at_or_before(timeline.ema20, cutoff)
        ema50_value = _latest_at_or_before(timeline.ema50, cutoff)
        evidence.update({"ema20": _text_or_none(ema20_value), "ema50": _text_or_none(ema50_value), "rvol5_gate": "DISABLED"})
        if ema20_value is None or ema50_value is None:
            signal = _unavailable_signal(job, "TREND_ONLY_TIMELINE_FEATURE_UNAVAILABLE")
        else:
            signal = _trend_only_signal(job=job, base=base, ema20=ema20_value, ema50=ema50_value, return15_pct_points=r15)
    elif family == "RET_OR_RVOL_ONLY":
        rv = _latest_at_or_before(timeline.rvol5, cutoff)
        min_rv = _decimal(job.runtime_profile["signal"].get("rvol5_min", "1.2"))
        evidence.update({"rvol5": _text_or_none(rv), "trend_gate": "DISABLED", "rvol5_min": str(min_rv)})
        if rv is None:
            signal = _unavailable_signal(job, "RVOL_ONLY_TIMELINE_FEATURE_UNAVAILABLE")
        elif base.status is not V2DecisionStatus.PASS:
            signal = V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, "V2-SIGNAL-RET5-RET15-OR-RVOL-ONLY-V1", base.reason)
        elif rv < min_rv:
            signal = V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, "V2-SIGNAL-RET5-RET15-OR-RVOL-ONLY-V1", "RVOL5_BELOW_THRESHOLD")
        else:
            signal = V2SignalResult(V2DecisionStatus.PASS, base.direction, "V2-SIGNAL-RET5-RET15-OR-RVOL-ONLY-V1")
    elif family == "MOMENTUM_CONTINUATION":
        ema20_value = _latest_at_or_before(timeline.ema20, cutoff)
        ema50_value = _latest_at_or_before(timeline.ema50, cutoff)
        rv = _latest_at_or_before(timeline.rvol5, cutoff)
        evidence.update({"ema20": _text_or_none(ema20_value), "ema50": _text_or_none(ema50_value), "rvol5": _text_or_none(rv)})
        if ema20_value is None or ema50_value is None or rv is None:
            signal = _unavailable_signal(job, "CONTINUATION_TIMELINE_FEATURE_UNAVAILABLE")
        else:
            signal = continuation_signal(base=base, ema20=ema20_value, ema50=ema50_value, return15_pct_points=r15, rvol5_value=rv)
    elif family == "MOMENTUM_CONTINUATION_SHORT_DE":
        ema20_value = _latest_at_or_before(timeline.ema20, cutoff)
        ema50_value = _latest_at_or_before(timeline.ema50, cutoff)
        rv = _latest_at_or_before(timeline.rvol5, cutoff)
        de_result = _directional_efficiency5_from_timeline(timeline=timeline, cutoff=cutoff)
        evidence.update(
            {
                "ema20": _text_or_none(ema20_value),
                "ema50": _text_or_none(ema50_value),
                "rvol5": _text_or_none(rv),
                "directional_efficiency_5m": de_result["value"],
                "directional_efficiency_source_closes": de_result["source_closes"],
                "directional_efficiency_source_close_times": de_result["source_close_times"],
            }
        )
        if ema20_value is None or ema50_value is None or rv is None:
            signal = _unavailable_signal(job, "CONTINUATION_TIMELINE_FEATURE_UNAVAILABLE")
        else:
            signal = continuation_signal(base=base, ema20=ema20_value, ema50=ema50_value, return15_pct_points=r15, rvol5_value=rv)
            if signal.status is V2DecisionStatus.PASS and signal.direction is V2Direction.SHORT:
                threshold = _decimal(job.runtime_profile["signal"].get("short_directional_efficiency_min", "0.30"))
                evidence["short_directional_efficiency_min"] = str(threshold)
                if de_result["value"] is None:
                    signal = V2SignalResult(V2DecisionStatus.UNAVAILABLE, V2Direction.NONE, "V2-SIGNAL-CONTINUATION-SHORT-DE-V1", "DIRECTIONAL_EFFICIENCY_UNAVAILABLE")
                elif _decimal(de_result["value"]) < threshold:
                    signal = V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, "V2-SIGNAL-CONTINUATION-SHORT-DE-V1", "DIRECTIONAL_EFFICIENCY_BELOW_0_30")
                else:
                    signal = V2SignalResult(V2DecisionStatus.PASS, V2Direction.SHORT, "V2-SIGNAL-CONTINUATION-SHORT-DE-V1")
    elif family == "MOMENTUM_CONTINUATION_TURNOVER":
        ema20_value = _latest_at_or_before(timeline.ema20, cutoff)
        ema50_value = _latest_at_or_before(timeline.ema50, cutoff)
        rv = _latest_at_or_before(timeline.rvol5, cutoff)
        accel = _latest_at_or_before(timeline.turnover_acceleration, cutoff)
        evidence.update({"ema20": _text_or_none(ema20_value), "ema50": _text_or_none(ema50_value), "rvol5": _text_or_none(rv), "turnover_acceleration": _text_or_none(accel)})
        if ema20_value is None or ema50_value is None or rv is None or accel is None:
            signal = _unavailable_signal(job, "CONTINUATION_TURNOVER_TIMELINE_FEATURE_UNAVAILABLE")
        else:
            signal = continuation_signal(base=base, ema20=ema20_value, ema50=ema50_value, return15_pct_points=r15, rvol5_value=rv)
            threshold = _decimal(job.runtime_profile["signal"].get("turnover_acceleration_min", "1.2"))
            evidence["turnover_acceleration_min"] = str(threshold)
            if signal.status is V2DecisionStatus.PASS and accel < threshold:
                signal = V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, "V2-SIGNAL-CONTINUATION-TURNOVER-V1", "TURNOVER_ACCELERATION_BELOW_THRESHOLD")
    elif family == "COMPRESSION_BREAKOUT":
        rv = _latest_at_or_before(timeline.rvol5, cutoff)
        accel = _latest_at_or_before(timeline.turnover_acceleration, cutoff)
        median = _latest_at_or_before(timeline.compression_atr_median96, cutoff)
        range_pair = _latest_at_or_before(timeline.prior_12_range, cutoff)
        evidence.update({"rvol5": _text_or_none(rv), "turnover_acceleration": _text_or_none(accel), "atr15_median96": _text_or_none(median)})
        if rv is None or accel is None or median is None or range_pair is None:
            signal = _unavailable_signal(job, "COMPRESSION_TIMELINE_FEATURE_UNAVAILABLE")
        else:
            signal = compression_breakout_signal(
                atr15_value=atr_value,
                preceding_atr15_values=(median,) * 96,
                close=latest.close,
                prior_range_high=range_pair[0],
                prior_range_low=range_pair[1],
                rvol5_value=rv,
                turnover_acceleration_value=accel,
                compression_ratio_max=_decimal(job.runtime_profile["signal"].get("compression_ratio_max", "0.80")),
            )
            evidence["compression_ratio"] = None if median == 0 else str(atr_value / median)
            evidence["compression_ratio_max"] = str(job.runtime_profile["signal"].get("compression_ratio_max", "0.80"))
            evidence["compression_ratio_bucket"] = _compression_ratio_bucket(atr_value=atr_value, median=median)
    elif family == "EXHAUSTION_REVERSAL":
        accel = _latest_at_or_before(timeline.turnover_acceleration, cutoff)
        right = bisect_left(timeline.close_times, cutoff + timedelta(microseconds=1))
        left = bisect_left(timeline.close_times, cutoff - timedelta(minutes=15) + timedelta(microseconds=1))
        recent = timeline.candles[left:right]
        evidence["turnover_acceleration"] = _text_or_none(accel)
        if accel is None or len(recent) < 2:
            signal = _unavailable_signal(job, "REVERSAL_TIMELINE_FEATURE_UNAVAILABLE")
        else:
            signal = reversal_signal(
                return15_pct_points=r15,
                latest_close=latest.close,
                high_15m=max(c.high for c in recent),
                low_15m=min(c.low for c in recent),
                atr15_value=atr_value,
                last_two_closes=tuple(c.close for c in recent[-2:]),
                turnover_acceleration_value=accel,
            )
    else:
        signal = _unavailable_signal(job, f"UNSUPPORTED_SIGNAL_FAMILY:{family}")
    signal = _apply_direction_mode(job, signal)
    evidence["signal_status"] = signal.status.value
    evidence["signal_direction"] = signal.direction.value
    evidence["signal_reason"] = signal.reason
    if signal.status is V2DecisionStatus.PASS:
        tick = venue.tick_size if venue is not None else Decimal("0.00000001")
        entry = _entry_price_from_evidence(signal.direction, latest.close, atr_value, tick)
        swing = _latest_protective_swing_from_timeline(timeline=timeline, cutoff=cutoff, direction=signal.direction, entry=entry)
        evidence["structural_reference_price"] = None if swing is None else str(swing.price)
        evidence["structural_reference_formed_at"] = None if swing is None else _iso(swing.formed_at)
        evidence["structural_reference_confirmed_at"] = None if swing is None else _iso(swing.confirmed_at)
        evidence["structural_reference_available_at"] = None if swing is None else _iso(swing.available_at)
        evidence["structural_reference_age_seconds"] = None if swing is None else int((cutoff.astimezone(UTC) - swing.available_at).total_seconds())
    return signal, evidence


def _trend_only_signal(
    *,
    job: ResearchV2JobConfig,
    base,
    ema20: Decimal,
    ema50: Decimal,
    return15_pct_points: Decimal,
):
    if base.status is not V2DecisionStatus.PASS:
        return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, "V2-SIGNAL-RET5-RET15-OR-TREND-ONLY-V1", base.reason)
    if base.direction is V2Direction.LONG and ema20 > ema50 and return15_pct_points > 0:
        return V2SignalResult(V2DecisionStatus.PASS, V2Direction.LONG, "V2-SIGNAL-RET5-RET15-OR-TREND-ONLY-V1")
    if base.direction is V2Direction.SHORT and ema20 < ema50 and return15_pct_points < 0:
        return V2SignalResult(V2DecisionStatus.PASS, V2Direction.SHORT, "V2-SIGNAL-RET5-RET15-OR-TREND-ONLY-V1")
    return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, "V2-SIGNAL-RET5-RET15-OR-TREND-ONLY-V1", "TREND_FILTER_FAILED")


def _apply_direction_mode(job: ResearchV2JobConfig, signal):
    if signal.status is not V2DecisionStatus.PASS:
        return signal
    mode = str(job.runtime_profile.get("hypothesis", {}).get("direction_mode") or job.runtime_profile.get("signal", {}).get("direction_mode") or "LONG_SHORT")
    if mode == "LONG_ONLY" and signal.direction is V2Direction.SHORT:
        return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, signal.signal_version, "DIRECTION_MODE_SHORT_SUPPRESSED")
    if mode == "SHORT_ONLY" and signal.direction is V2Direction.LONG:
        return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, signal.signal_version, "DIRECTION_MODE_LONG_SUPPRESSED")
    return signal


def _directional_efficiency5_from_timeline(*, timeline: FeatureTimeline, cutoff: datetime) -> dict[str, Any]:
    bars = aggregate_completed_bars(timeline.candles, timeframe_minutes=5, cutoff=cutoff)
    source = tuple(bar for bar in bars if bar.close_time <= cutoff)[-9:]
    if len(source) != 9:
        return {"value": None, "source_closes": [str(bar.close) for bar in source], "source_close_times": [_iso(bar.close_time) for bar in source]}
    value = directional_efficiency(closes=(str(bar.close) for bar in source))
    return {"value": value, "source_closes": [str(bar.close) for bar in source], "source_close_times": [_iso(bar.close_time) for bar in source]}


def _compression_ratio_bucket(*, atr_value: Decimal, median: Decimal) -> str | None:
    if median <= 0:
        return None
    ratio = atr_value / median
    if ratio <= Decimal("0.80"):
        return "LTE_0_80"
    if ratio <= Decimal("1.00"):
        return "GT_0_80_LTE_1_00"
    return "GT_1_00"


def _replay_one_context(
    *,
    context: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any],
    raw_indexes: dict[str, RawTradeIndex],
    candles_cache: dict[str, tuple[HistoricalCandle, ...]],
    venue_cache: dict[str, VenueConstraints],
    funding_cache: dict[str, tuple[Mapping[str, Any], ...]],
    portfolio_state: dict[str, V2ReplayPortfolioBook] | dict[str, V2PortfolioExposureState],
    mark_cache: dict[str, tuple[HistoricalCandle, ...]] | None = None,
) -> dict[str, Any]:
    job = context["job"]
    record = context["record"]
    physical = str(record["physical_symbol"])
    logical = str(record["symbol"])
    observed_at = _parse_time(str(record["observed_at"]))
    if physical not in raw_indexes:
        raw_indexes[physical] = RawTradeIndex(
            logical_symbol=logical,
            physical_symbol=physical,
            archives=_raw_archive_paths(dataset_manifest, physical_symbol=physical),
        )
    raw_index = raw_indexes[physical]
    if physical not in candles_cache:
        candles_cache[physical] = _load_dataset_candles(dataset_manifest, physical_symbol=physical)
    candles = candles_cache[physical]
    if physical not in venue_cache:
        venue_cache[physical] = _load_dataset_venue(dataset_manifest, physical_symbol=physical)
    venue = venue_cache[physical]
    if physical not in funding_cache:
        funding_cache[physical] = _canonical_lifecycle_funding_facts(
            _load_dataset_funding_facts(dataset_manifest, physical_symbol=physical),
            dataset_manifest=dataset_manifest,
            mark_cache=mark_cache,
            physical_symbol=physical,
        )
    funding = funding_cache[physical]
    profile = build_research_v2_canonical_execution_profile(job)
    resolution = _resolution_from_record(record)
    g0_eligibility = _g0_eligibility_only_result(job=job, record=record, venue=venue, direction=resolution.direction)
    if g0_eligibility is not None and g0_eligibility.status != "PASS":
        return {
            "status": "HYPOTHESIS_REJECTED",
            "reason_code": f"G0_ELIGIBILITY_{g0_eligibility.reason_code}",
            "job_id": job.job_id,
            "symbol": logical,
            "observed_at": record["observed_at"],
            "research_identity": _research_identity_payload(job, execution_profile_fingerprint=profile.config_fingerprint),
            "g0_eligibility_evidence": {
                **g0_eligibility.evidence,
                "result": g0_eligibility.status,
                "reason_code": g0_eligibility.reason_code,
                "portfolio_grant_evaluated": False,
                "order_spec_created": False,
                "cooldown_evaluated": False,
                "account_state_mutated": False,
            },
            "market_handoff": None,
            "portfolio_grant": None,
            "daily_equity_guard_evidence": None,
            "cooldown_evidence": None,
            "order_spec": None,
            "reservation_committed": False,
            "reservation_released": False,
            "reservation_release_at": None,
            "state_committed": False,
            "account_event_ledger": [],
        }
    handoff = produce_research_v2_market_handoff(
        resolution=resolution,
        facts=_handoff_facts_from_evidence(
            symbol=logical,
            physical_symbol=physical,
            observed_at=observed_at,
            direction=resolution.direction,
            candles=candles,
            evidence=record["factual_feature_evidence"],
            venue=venue,
        ),
    )
    key = _portfolio_book_key(context)
    book = _portfolio_book(portfolio_state, key)
    book.apply_due(observed_at)
    state = book.state_for_symbol(logical)
    daily_equity = _daily_equity_guard_evidence(
        book=book,
        job_id=job.job_id,
        as_of=observed_at,
        dataset_manifest=dataset_manifest,
        mark_cache=mark_cache,
        daily_loss_fraction=_decimal(profile.sizing_profile.get("daily_loss_fraction_max", "0.0225")),
    )
    if daily_equity["loss_guard_decision"] == "REJECT":
        pending_before_cancel = book.pending_entry_exposures(observed_at)
        protected_positions = book.open_position_exposures(observed_at)
        guard_release_events = book.cancel_pending_for_daily_guard(as_of=observed_at)
        factual_guard_row = {
            "job_id": job.job_id,
            "evaluated_at": _iso(observed_at),
            "trigger_context_id": str(context["context_id"]),
            "trigger_lifecycle_index": None,
            "factual_timeline_guard": False,
            "candidate_time_guard": True,
            "day_opening_equity": daily_equity["day_opening_equity"],
            "current_factual_equity": daily_equity["current_factual_equity"],
            "daily_equity_delta_fraction": daily_equity["daily_equity_delta_fraction"],
            "configured_loss_threshold_fraction": daily_equity["configured_loss_threshold_fraction"],
            "breached": True,
            "pending_order_context_ids": [exposure.context_id for exposure in pending_before_cancel],
            "pending_order_spec_ids": [exposure.order_spec_id for exposure in pending_before_cancel],
            "protected_open_position_context_ids": [exposure.context_id for exposure in protected_positions],
            "protected_open_position_order_spec_ids": [exposure.order_spec_id for exposure in protected_positions],
            "open_positions": daily_equity["open_positions"],
            "cancellation_obligations_generated": len({event.context_id for event in guard_release_events if event.event_type == "ENTRY_CANCELLED_UNFILLED"}),
            "cancellation_events_generated": [event.to_payload() for event in guard_release_events],
            "reservation_releases_generated": [event.context_id for event in guard_release_events if event.event_type == "RESERVATION_RELEASE"],
            "source_provenance": daily_equity["source_provenance"],
        }
        return {
            "status": "PORTFOLIO_BLOCKED",
            "reason_code": "DAILY_LOSS_LIMIT_REACHED",
            "market_handoff": handoff.payload,
            "portfolio_grant": {
                "v2_portfolio_grant": {
                    "contract_version": 1,
                    "status": "BLOCK",
                    "reason_code": "DAILY_LOSS_LIMIT_REACHED",
                    "account_capital": _decimal_text(state.account_capital),
                    "free_margin": _decimal_text(max(_decimal(profile.sizing_profile["total_margin_fraction_max"]) * state.account_capital - state.committed_margin, Decimal("0"))),
                    "remaining_coin_margin": _decimal_text(max(_decimal(profile.sizing_profile["per_coin_margin_fraction_cap"]) * state.account_capital - state.coin_committed_margin, Decimal("0"))),
                    "remaining_gross_notional": _decimal_text(max(_decimal(profile.sizing_profile["gross_notional_fraction_max"]) * state.account_capital - state.gross_notional, Decimal("0"))),
                    "remaining_stop_risk": _decimal_text(max(_decimal(profile.sizing_profile["portfolio_open_and_pending_stop_risk_fraction_max"]) * state.account_capital - state.stop_risk, Decimal("0"))),
                    "remaining_global_slots": max(int(profile.sizing_profile["max_open_and_pending_orders"]) - state.open_pending_count, 0),
                    "remaining_coin_slots": max(int(profile.sizing_profile["max_positions_per_coin"]) - state.coin_open_pending_count, 0),
                    "execution_profile_fingerprint": profile.config_fingerprint,
                }
            },
            "daily_equity_guard_evidence": daily_equity,
            "daily_guard_action": {
                "canonical_breach_action": "halt new entries and cancel pending; do not remove protective exits",
                "pending_cancel_required": True,
                "pending_cancelled_count": len({event.context_id for event in guard_release_events if event.event_type == "ENTRY_CANCELLED_UNFILLED"}),
                "effective_at": _iso(observed_at),
                "reason_code": "DAILY_LOSS_LIMIT_REACHED",
            },
            "factual_timeline_guard_evidence": [factual_guard_row],
            "account_event_ledger": [event.to_payload() for event in guard_release_events],
            "order_spec": None,
            "state_committed": False,
        }
    cooldown_minutes = _profile_cooldown_minutes(profile)
    cooldown = book.cooldown_evidence(symbol=logical, accepted_at=observed_at, cooldown_minutes=cooldown_minutes)
    if cooldown["cooldown_decision"] != "PASS":
        return {
            "status": "PORTFOLIO_BLOCKED",
            "reason_code": "COOLDOWN_ACTIVE",
            "market_handoff": handoff.payload,
            "portfolio_grant": {
                "v2_portfolio_grant": {
                    "contract_version": 1,
                    "status": "BLOCK",
                    "reason_code": "COOLDOWN_ACTIVE",
                    "account_capital": _decimal_text(state.account_capital),
                    "free_margin": _decimal_text(max(_decimal(profile.sizing_profile["total_margin_fraction_max"]) * state.account_capital - state.committed_margin, Decimal("0"))),
                    "remaining_coin_margin": _decimal_text(max(_decimal(profile.sizing_profile["per_coin_margin_fraction_cap"]) * state.account_capital - state.coin_committed_margin, Decimal("0"))),
                    "remaining_gross_notional": _decimal_text(max(_decimal(profile.sizing_profile["gross_notional_fraction_max"]) * state.account_capital - state.gross_notional, Decimal("0"))),
                    "remaining_stop_risk": _decimal_text(max(_decimal(profile.sizing_profile["portfolio_open_and_pending_stop_risk_fraction_max"]) * state.account_capital - state.stop_risk, Decimal("0"))),
                    "remaining_global_slots": max(int(profile.sizing_profile["max_open_and_pending_orders"]) - state.open_pending_count, 0),
                    "remaining_coin_slots": max(int(profile.sizing_profile["max_positions_per_coin"]) - state.coin_open_pending_count, 0),
                    "execution_profile_fingerprint": profile.config_fingerprint,
                }
            },
            "daily_equity_guard_evidence": daily_equity,
            "cooldown_evidence": cooldown,
            "order_spec": None,
            "state_committed": False,
        }
    grant = evaluate_research_v2_portfolio_grant(profile=profile, state=state)
    try:
        construction = construct_research_v2_order_spec(
            order_spec_id=_order_spec_id(job=job, resolution=resolution),
            spec_created_at=_iso(observed_at),
            market_handoff=handoff.payload,
            profile=profile,
            portfolio_grant=grant,
            venue=venue,
            reference_price=_decimal(record["factual_feature_evidence"]["reference_price"]),
            atr15=_decimal(record["factual_feature_evidence"]["atr15"]),
            structural_reference_price=_optional_decimal(record["factual_feature_evidence"].get("structural_reference_price")),
        )
    except ResearchV2ExecutionError as exc:
        return {
            "status": "CONSTRUCTION_REJECTED",
            "reason_code": str(exc),
            "market_handoff": handoff.payload,
            "portfolio_grant": grant.to_payload(),
            "daily_equity_guard_evidence": daily_equity,
            "cooldown_evidence": cooldown,
            "order_spec": None,
            "state_committed": False,
        }
    if construction.status != "CONSTRUCTED" or construction.order_spec is None:
        return {
            "status": "CONSTRUCTION_REJECTED",
            "reason_code": construction.reason_code,
            "market_handoff": handoff.payload,
            "portfolio_grant": grant.to_payload(),
            "daily_equity_guard_evidence": daily_equity,
            "cooldown_evidence": cooldown,
            "order_spec": None,
            "state_committed": False,
        }
    economics = construction.order_spec["order_spec"]["economics"]
    lifecycle = _simulate_bounded_research_v2_lifecycle(
        raw_index=raw_index,
        order_spec=construction.order_spec,
        position_state=_position_state_for_lifecycle(handoff.payload),
        submitted_at=observed_at,
        window_end=_parse_time(str(job.window_end)),
        funding_facts=funding,
    )
    lifecycle = _resolve_intrabar_with_raw_if_possible(
        lifecycle=lifecycle,
        raw_index=raw_index,
        order_spec=construction.order_spec,
        position_state=_position_state_for_lifecycle(handoff.payload),
        submitted_at=observed_at,
        funding_facts=funding,
    )
    reservation_committed = bool(lifecycle.accepted)
    release_at = _v2_lifecycle_release_at(lifecycle=lifecycle, order_spec=construction.order_spec)
    state_committed = _v2_lifecycle_owns_final_portfolio_state(lifecycle)
    endpoint_mtm = None
    account_events: list[V2ReplayAccountEvent] = []
    if str(lifecycle.status) == "FILLED_OPEN_AT_ENDPOINT":
        if mark_cache is not None and physical not in mark_cache:
            try:
                mark_cache[physical] = _load_dataset_mark_candles(dataset_manifest, physical_symbol=physical)
            except ResearchV2RunnerError:
                mark_cache[physical] = ()
        marks = () if mark_cache is None else mark_cache.get(physical, ())
        endpoint_mtm = _endpoint_mtm_evidence(
            job_id=job.job_id,
            logical_symbol=logical,
            physical_symbol=physical,
            order_spec=construction.order_spec,
            lifecycle=lifecycle,
            endpoint=_parse_time(str(job.window_end)),
            marks=marks,
            funding_facts=funding,
            dataset_manifest=dataset_manifest,
        )
    if reservation_committed:
        account_events = book.commit(
            symbol=logical,
            physical_symbol=physical,
            economics=economics,
            release_at=release_at,
            context_id=str(context["context_id"]),
            lifecycle_status=str(lifecycle.status),
            accepted_at=observed_at,
            order_spec=construction.order_spec,
            lifecycle=lifecycle,
            funding_facts=funding,
            dataset_manifest=dataset_manifest,
            mark_cache=mark_cache,
            funding_end_at=_parse_time(str(job.window_end)),
        )
        factual_guard_evidence, factual_guard_events = _factual_timeline_daily_guard_enforcement(
            book=book,
            job_id=job.job_id,
            start_at=observed_at,
            window_end=_parse_time(str(job.window_end)),
            dataset_manifest=dataset_manifest,
            mark_cache=mark_cache,
            daily_loss_fraction=_decimal(profile.sizing_profile.get("daily_loss_fraction_max", "0.0225")),
            trigger_context_id=str(context["context_id"]),
        )
        if factual_guard_events:
            account_events = account_events + factual_guard_events
    else:
        factual_guard_evidence = []
    return {
        "status": "COMPLETE",
        "job_id": job.job_id,
        "symbol": logical,
        "observed_at": record["observed_at"],
        "research_identity": _research_identity_payload(job, execution_profile_fingerprint=profile.config_fingerprint),
        "g0_eligibility_evidence": None
        if g0_eligibility is None
        else {
            **g0_eligibility.evidence,
            "result": g0_eligibility.status,
            "reason_code": g0_eligibility.reason_code,
            "portfolio_grant_evaluated": True,
            "order_spec_created": construction.order_spec is not None,
            "cooldown_evaluated": True,
            "account_state_mutated": reservation_committed,
        },
        "market_handoff": handoff.payload,
        "portfolio_grant": grant.to_payload(),
        "daily_equity_guard_evidence": daily_equity,
        "cooldown_evidence": {
            **cooldown,
            "accepted": bool(lifecycle.accepted),
            "accepted_at": _iso(observed_at) if lifecycle.accepted else None,
        },
        "order_spec": construction.order_spec,
        "reservation_committed": reservation_committed,
        "reservation_released": reservation_committed and release_at is not None,
        "reservation_release_at": _iso(release_at) if release_at is not None else None,
        "state_committed": state_committed,
        "raw_trades_execution_source": "RAW_TRADES_INDEXED_MINUTE_BARS",
        "endpoint_mtm": endpoint_mtm,
        "instrument_constraints": _instrument_constraints_evidence(dataset_manifest, physical_symbol=physical, venue=venue),
        "factual_timeline_guard_evidence": factual_guard_evidence,
        "account_event_ledger": [event.to_payload() for event in account_events],
        "backtest_lifecycle": asdict(lifecycle),
    }


def _g0_eligibility_only_result(
    *,
    job: ResearchV2JobConfig,
    record: Mapping[str, Any],
    venue: VenueConstraints,
    direction: V2Direction,
):
    signal_profile = job.runtime_profile.get("signal", {})
    if not isinstance(signal_profile, Mapping) or not signal_profile.get("g0_eligibility_only"):
        return None
    evidence = record.get("factual_feature_evidence")
    if not isinstance(evidence, Mapping):
        raise ResearchV2RunnerError("G0 eligibility requires factual feature evidence")
    common = load_common_profile()
    result = evaluate_research_v2_g0_structural_eligibility(
        direction=direction.value,
        stop_profile=common["stop_G0"],
        venue=venue,
        reference_price=_decimal(evidence["reference_price"]),
        atr15=_decimal(evidence["atr15"]),
        structural_reference_price=_optional_decimal(evidence.get("structural_reference_price")),
    )
    result.evidence.update(
        {
            "reference_identity": "v2-protective-reference",
            "reference_formed_at": evidence.get("structural_reference_formed_at"),
            "reference_confirmed_at": evidence.get("structural_reference_confirmed_at"),
            "reference_available_at": evidence.get("structural_reference_available_at"),
            "reference_age_seconds": evidence.get("structural_reference_age_seconds"),
            "actual_operative_stop_family": str(job.runtime_profile.get("stop", {}).get("type")),
        }
    )
    return result


def _simulate_bounded_research_v2_lifecycle(
    *,
    raw_index: RawTradeIndex,
    order_spec: Mapping[str, Any],
    position_state: Mapping[str, Any],
    submitted_at: datetime,
    window_end: datetime,
    funding_facts: Sequence[Mapping[str, Any]],
):
    chunk_end = min(window_end, submitted_at + timedelta(hours=6))
    last_lifecycle = None
    while True:
        raw_candles = raw_index.range_as_candles(start=submitted_at, end=chunk_end)
        lifecycle = _simulate_research_v1_backtest_lifecycle(
            order_spec=order_spec,
            position_state=position_state,
            candles=raw_candles,
            submitted_at=_iso(submitted_at),
            funding_facts=funding_facts,
        )
        last_lifecycle = lifecycle
        if _lifecycle_terminal_within_window(lifecycle) or chunk_end >= window_end:
            return lifecycle
        chunk_end = min(window_end, chunk_end + timedelta(hours=6))
    return last_lifecycle


def _lifecycle_terminal_within_window(lifecycle: Any) -> bool:
    status = str(getattr(lifecycle, "status", ""))
    reason = str(getattr(lifecycle, "reason_code", ""))
    if status == "FILLED_OPEN_AT_ENDPOINT":
        return False
    if status in {"CLOSED", "CENSORED", "SIMULATED_REJECTED"}:
        return True
    if status == "ACCEPTED_NOT_FILLED":
        return bool(getattr(lifecycle, "completed", False)) or reason == "ENTRY_ORDER_EXPIRED_UNFILLED"
    return bool(getattr(lifecycle, "completed", False))


def _resolve_intrabar_with_raw_if_possible(
    *,
    lifecycle: ResearchV1BacktestLifecycleResult,
    raw_index: RawTradeIndex,
    order_spec: Mapping[str, Any],
    position_state: Mapping[str, Any],
    submitted_at: datetime,
    funding_facts: Sequence[Mapping[str, Any]],
) -> ResearchV1BacktestLifecycleResult:
    if lifecycle.reason_code not in {"ENTRY_PROTECTION_INTRABAR_SEQUENCE_UNRESOLVED", "TP_SL_INTRABAR_SEQUENCE_UNRESOLVED"}:
        return lifecycle
    spec = order_spec["order_spec"]
    evidence = _lifecycle_evidence(lifecycle)
    entry_filled_at = _optional_time(evidence.get("entry_filled_at"))
    if entry_filled_at is None:
        return lifecycle
    minute_start = entry_filled_at.replace(second=0, microsecond=0)
    minute_end = minute_start + timedelta(minutes=1)
    evidence_start = submitted_at
    rows = raw_index._range(start=evidence_start, end=minute_end)
    source_identity = raw_index.source_identity_for_time(minute_start)
    if not rows:
        return _lifecycle_with_intrabar_evidence(lifecycle, _intrabar_sequence_evidence(rows=(), spec=spec, entry_time=entry_filled_at, resolution="UNRESOLVED_NO_RAW_ROWS", source_identity=source_identity, evidence_start=evidence_start, evidence_end=minute_end))
    direction = str(spec["direction"]).upper()
    entry = _decimal(spec["entry"]["price"])
    tp = _decimal(spec["take_profit"]["price"])
    sl = _decimal(spec["stop_loss"]["price"])
    entry_event = _first_raw_touch(rows, direction=direction, threshold=entry, event="ENTRY")
    if entry_event is None:
        return _lifecycle_with_intrabar_evidence(lifecycle, _intrabar_sequence_evidence(rows=rows, spec=spec, entry_time=entry_filled_at, resolution="UNRESOLVED_ENTRY_NOT_FOUND_IN_RAW", source_identity=source_identity, evidence_start=evidence_start, evidence_end=minute_end))
    tp_event = _first_raw_touch(tuple(row for row in rows if row.occurred_at >= entry_event.occurred_at), direction=direction, threshold=tp, event="TAKE_PROFIT")
    sl_event = _first_raw_touch(tuple(row for row in rows if row.occurred_at >= entry_event.occurred_at), direction=direction, threshold=sl, event="STOP_LOSS")
    candidates = [item for item in (tp_event, sl_event) if item is not None]
    if not candidates:
        return _lifecycle_with_intrabar_evidence(lifecycle, _intrabar_sequence_evidence(rows=rows, spec=spec, entry_time=entry_event.occurred_at, resolution="UNRESOLVED_NO_PROTECTION_TOUCH_AFTER_ENTRY", source_identity=source_identity, evidence_start=evidence_start, evidence_end=minute_end))
    first = min(candidates, key=lambda item: (item.occurred_at, item.price, item.quantity))
    tied = [item for item in candidates if item.occurred_at == first.occurred_at and item is not first]
    if tied:
        return _lifecycle_with_intrabar_evidence(lifecycle, _intrabar_sequence_evidence(rows=rows, spec=spec, entry_time=entry_event.occurred_at, resolution="UNRESOLVED_SIMULTANEOUS_PROTECTION_TOUCH", source_identity=source_identity, evidence_start=evidence_start, evidence_end=minute_end))
    exit_reason = "TAKE_PROFIT" if first is tp_event else "STOP_LOSS"
    exit_price = tp if exit_reason == "TAKE_PROFIT" else sl
    funding = _research_v1_backtest_funding_amount(
        funding_facts=funding_facts,
        spec=spec,
        direction=direction,
        quantity=_decimal(spec["entry"]["quantity"]),
        entry=entry,
        opened_at=entry_event.occurred_at,
        closed_at=first.occurred_at,
    )
    if funding is None:
        return _lifecycle_with_intrabar_evidence(lifecycle, _intrabar_sequence_evidence(rows=rows, spec=spec, entry_time=entry_event.occurred_at, resolution="UNRESOLVED_MISSING_FUNDING_FACTS", source_identity=source_identity, evidence_start=evidence_start, evidence_end=minute_end))
    refined = _closed_lifecycle_result(
        spec=spec,
        direction=direction,
        entry=entry,
        quantity=_decimal(spec["entry"]["quantity"]),
        exit_price=exit_price,
        leverage=_decimal(spec["leverage"]),
        maker_fee_rate=_decimal(spec["economics"]["maker_fee_rate"]),
        taker_fee_rate=_decimal(spec["economics"]["taker_fee_rate"]),
        submitted=submitted_at,
        proxy=_decimal(
            position_state["position_opportunity_state"]["source_contracts"]["market_handoff"]["market_handoff"]["snapshot"][
                "set_match_reference_price"
            ]
        ),
        entry_filled_at=_iso(entry_event.occurred_at),
        exit_reason=exit_reason,
        exit_at=_iso(first.occurred_at),
        tp=tp,
        sl=sl,
        funding=funding,
    )
    return _lifecycle_with_intrabar_evidence(
        refined,
        _intrabar_sequence_evidence(rows=rows, spec=spec, entry_time=entry_event.occurred_at, resolution=f"RESOLVED_{exit_reason}", exit_event=first, source_identity=source_identity, evidence_start=evidence_start, evidence_end=minute_end),
    )


def _first_raw_touch(rows: Sequence[RawTradePoint], *, direction: str, threshold: Decimal, event: str) -> RawTradePoint | None:
    for row in rows:
        price = row.price
        if event == "ENTRY":
            if (direction == "LONG" and price <= threshold) or (direction == "SHORT" and price >= threshold):
                return row
        elif event == "TAKE_PROFIT":
            if (direction == "LONG" and price >= threshold) or (direction == "SHORT" and price <= threshold):
                return row
        elif event == "STOP_LOSS":
            if (direction == "LONG" and price <= threshold) or (direction == "SHORT" and price >= threshold):
                return row
    return None


def _intrabar_sequence_evidence(
    *,
    rows: Sequence[RawTradePoint],
    spec: Mapping[str, Any],
    entry_time: datetime,
    resolution: str,
    exit_event: RawTradePoint | None = None,
    source_identity: Mapping[str, Any] | None = None,
    evidence_start: datetime | None = None,
    evidence_end: datetime | None = None,
) -> dict[str, Any]:
    witness_start, sample_rows = _intrabar_witness_rows(rows=rows, entry_time=entry_time, exit_time=None if exit_event is None else exit_event.occurred_at)
    sample = [
        {
            "row_offset_in_minute": witness_start + offset,
            "row_offset_in_evidence_interval": witness_start + offset,
            "source_row_offset": row.source_row_offset,
            "timestamp": _iso(row.occurred_at),
            "price": str(row.price),
            "quantity": str(row.quantity),
        }
        for offset, row in enumerate(sample_rows)
    ]
    source = dict(source_identity or {})
    return {
        "physical_symbol": spec.get("physical_symbol"),
        "logical_symbol": spec.get("symbol"),
        "minute": _iso(entry_time.replace(second=0, microsecond=0)),
        "decision_time": spec.get("spec_created_at"),
        "submitted_at": spec.get("spec_created_at"),
        "accepted_at": spec.get("spec_created_at"),
        "evidence_coverage_start": None if evidence_start is None else _iso(evidence_start),
        "evidence_coverage_end": None if evidence_end is None else _iso(evidence_end),
        "acceptance_prefix_verified": True,
        "acceptance_prefix_unverified": False,
        "entry_filled_at": _iso(entry_time),
        "entry_level": spec["entry"]["price"],
        "stop_level": spec["stop_loss"]["price"],
        "take_profit_level": spec["take_profit"]["price"],
        "first_qualifying_entry_event": _iso(entry_time),
        "first_subsequent_exit_event": None if exit_event is None else {"timestamp": _iso(exit_event.occurred_at), "price": str(exit_event.price), "quantity": str(exit_event.quantity)},
        "raw_trade_witness": sample,
        "raw_trade_witness_count": len(sample),
        "raw_trade_rows_in_minute": sum(1 for row in rows if row.occurred_at.replace(second=0, microsecond=0) == entry_time.replace(second=0, microsecond=0)),
        "raw_trade_rows_in_evidence_interval": len(rows),
        "raw_trade_witness_start_offset": witness_start,
        "raw_trade_witness_end_offset": witness_start + len(sample_rows) - 1 if sample_rows else None,
        "raw_trade_witness_coverage": "FULL_RAW_MINUTE",
        "source_file": source.get("source_file"),
        "source_hash": source.get("source_hash"),
        "source_physical_symbol": source.get("physical_symbol"),
        "factual_resolution_status": resolution,
    }


def _intrabar_witness_rows(
    *,
    rows: Sequence[RawTradePoint],
    entry_time: datetime,
    exit_time: datetime | None,
) -> tuple[int, tuple[RawTradePoint, ...]]:
    return 0, tuple(rows)


def _lifecycle_with_intrabar_evidence(lifecycle: ResearchV1BacktestLifecycleResult, intrabar: Mapping[str, Any]) -> ResearchV1BacktestLifecycleResult:
    evidence = dict(_lifecycle_evidence(lifecycle))
    evidence["intrabar_sequence_evidence"] = dict(intrabar)
    evidence["evidence_digest"] = canonical_json_digest(evidence)
    return ResearchV1BacktestLifecycleResult(
        status=lifecycle.status,
        reason_code=lifecycle.reason_code,
        accepted=lifecycle.accepted,
        filled=lifecycle.filled,
        completed=lifecycle.completed,
        censored=lifecycle.censored,
        closed_result=lifecycle.closed_result,
        evidence=evidence,
    )


def _v2_lifecycle_owns_final_portfolio_state(lifecycle: Any) -> bool:
    if not bool(lifecycle.accepted):
        return False
    if bool(lifecycle.filled):
        if bool(lifecycle.censored) and str(lifecycle.status) != "FILLED_OPEN_AT_ENDPOINT":
            return False
        return not bool(lifecycle.completed)
    return not bool(lifecycle.completed)


def _v2_lifecycle_release_at(*, lifecycle: Any, order_spec: Mapping[str, Any]) -> datetime | None:
    if not bool(lifecycle.accepted):
        return None
    evidence = lifecycle.evidence if isinstance(lifecycle.evidence, Mapping) else {}
    if bool(lifecycle.filled):
        if bool(lifecycle.censored) and str(lifecycle.status) != "FILLED_OPEN_AT_ENDPOINT":
            terminal_at = evidence.get("exit_at") or evidence.get("entry_filled_at")
            return _parse_time(str(terminal_at)) if terminal_at else None
        if bool(lifecycle.completed):
            exit_at = evidence.get("exit_at")
            return _parse_time(str(exit_at)) if exit_at else None
        return None
    if bool(lifecycle.completed):
        expires_at = (
            order_spec.get("order_spec", {})
            .get("entry", {})
            .get("validity", {})
            .get("expires_at")
        )
        terminal_at = evidence.get("cancelled_at") or evidence.get("expired_at") or expires_at
        return _parse_time(str(terminal_at)) if terminal_at else None
    return None


def _lifecycle_evidence(lifecycle: Any) -> Mapping[str, Any]:
    evidence = getattr(lifecycle, "evidence", None)
    return evidence if isinstance(evidence, Mapping) else {}


def _closed_funding(lifecycle: Any) -> Decimal:
    closed = getattr(lifecycle, "closed_result", None)
    if isinstance(closed, Mapping):
        return _decimal(closed.get("funding", "0"))
    return Decimal("0")


def _account_events_for_lifecycle(
    *,
    symbol: str,
    physical_symbol: str,
    context_id: str,
    order_spec_id: str | None,
    accepted_at: datetime | None,
    opened_at: datetime | None,
    release_at: datetime | None,
    closed: Mapping[str, Any] | None,
    direction: str,
    entry: Decimal,
    quantity: Decimal,
    entry_fee: Decimal,
    exit_fee: Decimal,
    funding_events: Sequence[Mapping[str, Any]],
    causal_sequence_factory,
    admission_ordinal: int | None,
) -> list[V2ReplayAccountEvent]:
    events: list[V2ReplayAccountEvent] = []
    if accepted_at is not None:
        events.append(
            _account_event(
                timestamp=accepted_at,
                event_type="ORDER_ACCEPTED",
                context_id=context_id,
                symbol=symbol,
                physical_symbol=physical_symbol,
                order_spec_id=order_spec_id,
                quantity=quantity,
                causal_sequence=causal_sequence_factory(),
                admission_ordinal=admission_ordinal,
            )
        )
    if opened_at is not None:
        events.append(
            _account_event(
                timestamp=opened_at,
                event_type="ENTRY_FILLED",
                context_id=context_id,
                symbol=symbol,
                physical_symbol=physical_symbol,
                order_spec_id=order_spec_id,
                quantity=quantity,
                causal_sequence=causal_sequence_factory(),
                source_provenance={"entry_price": str(entry), "direction": direction},
            )
        )
        events.append(
            _account_event(
                timestamp=opened_at,
                event_type="ENTRY_FEE",
                context_id=context_id,
                symbol=symbol,
                physical_symbol=physical_symbol,
                order_spec_id=order_spec_id,
                quantity=quantity,
                fee_amount=entry_fee,
                cashflow_amount=-entry_fee,
                causal_sequence=causal_sequence_factory(),
            )
        )
    for funding in funding_events:
        timestamp = _parse_time(str(funding["funding_timestamp"]))
        amount = _decimal(funding["calculated_funding_cashflow"])
        events.append(
            _account_event(
                timestamp=timestamp,
                event_type="FUNDING_BOUNDARY",
                context_id=context_id,
                symbol=symbol,
                physical_symbol=physical_symbol,
                order_spec_id=order_spec_id,
                quantity=quantity,
                cashflow_amount=amount,
                funding_amount=amount,
                causal_sequence=causal_sequence_factory(),
                source_provenance=dict(funding),
            )
        )
    if closed is not None and closed.get("closed_at") is not None:
        closed_at = _parse_time(str(closed["closed_at"]))
        gross = _decimal(closed.get("gross_pnl", "0"))
        events.append(
            _account_event(
                timestamp=closed_at,
                event_type="PROTECTIVE_EXIT",
                context_id=context_id,
                symbol=symbol,
                physical_symbol=physical_symbol,
                order_spec_id=order_spec_id,
                quantity=quantity,
                causal_sequence=causal_sequence_factory(),
                source_provenance={"exit_price": str(closed.get("exit_vwap")), "exit_reason": str(closed.get("exit_reason") or "")},
            )
        )
        events.append(
            _account_event(
                timestamp=closed_at,
                event_type="EXIT_FEE",
                context_id=context_id,
                symbol=symbol,
                physical_symbol=physical_symbol,
                order_spec_id=order_spec_id,
                quantity=quantity,
                fee_amount=exit_fee,
                cashflow_amount=-exit_fee,
                causal_sequence=causal_sequence_factory(),
            )
        )
        events.append(
            _account_event(
                timestamp=closed_at,
                event_type="FINAL_CLOSE",
                context_id=context_id,
                symbol=symbol,
                physical_symbol=physical_symbol,
                order_spec_id=order_spec_id,
                quantity=quantity,
                cashflow_amount=gross,
                realized_gross_pnl=gross,
                causal_sequence=causal_sequence_factory(),
            )
        )
    if release_at is not None:
        events.append(
            _account_event(
                timestamp=release_at,
                event_type="RESERVATION_RELEASE",
                context_id=context_id,
                symbol=symbol,
                physical_symbol=physical_symbol,
                order_spec_id=order_spec_id,
                quantity=quantity,
                causal_sequence=causal_sequence_factory(),
            )
        )
    return events


def _account_event(
    *,
    timestamp: datetime,
    event_type: str,
    context_id: str,
    symbol: str,
    physical_symbol: str,
    order_spec_id: str | None,
    quantity: Decimal | None,
    cashflow_amount: Decimal = Decimal("0"),
    realized_gross_pnl: Decimal = Decimal("0"),
    fee_amount: Decimal = Decimal("0"),
    funding_amount: Decimal = Decimal("0"),
    source_provenance: Mapping[str, Any] | None = None,
    causal_sequence: int = 0,
    admission_ordinal: int | None = None,
) -> V2ReplayAccountEvent:
    return V2ReplayAccountEvent(
        timestamp=timestamp,
        sequence=_EVENT_ORDER[event_type],
        event_type=event_type,
        context_id=context_id,
        symbol=symbol,
        physical_symbol=physical_symbol,
        order_spec_id=order_spec_id,
        quantity=quantity,
        cashflow_amount=cashflow_amount,
        realized_gross_pnl=realized_gross_pnl,
        fee_amount=fee_amount,
        funding_amount=funding_amount,
        source_provenance=dict(source_provenance or {}),
        causal_sequence=causal_sequence,
        admission_ordinal=admission_ordinal,
    )


def _account_event_sort_key(event: V2ReplayAccountEvent) -> tuple[datetime, int, str, str, str]:
    return (
        event.timestamp,
        event.sequence,
        event.causal_sequence,
        event.context_id,
        event.event_type,
        event.order_spec_id or "",
    )


def _funding_events_for_position(
    *,
    funding_facts: Sequence[Mapping[str, Any]],
    dataset_manifest: Mapping[str, Any] | None,
    mark_cache: dict[str, tuple[HistoricalCandle, ...]] | None,
    order: Mapping[str, Any],
    context_id: str,
    opened_at: datetime | None,
    closed_at: datetime | None,
    include_right_boundary: bool = True,
) -> tuple[dict[str, Any], ...]:
    if opened_at is None:
        return ()
    end = closed_at or _parse_time("2026-08-26T00:00:00Z")
    physical = str(order.get("physical_symbol") or order.get("symbol") or "").upper()
    logical = str(order.get("symbol") or physical)
    direction = str(order.get("direction") or "").upper()
    quantity = _decimal(order["entry"]["quantity"])
    out: list[dict[str, Any]] = []
    for fact in funding_facts:
        ts_text = fact.get("funding_time") or fact.get("timestamp") or fact.get("funding_timestamp")
        if ts_text is None:
            continue
        ts = _parse_time(str(ts_text))
        if not (opened_at < ts <= end if include_right_boundary else opened_at < ts < end):
            continue
        mark = _funding_boundary_mark(
            fact=fact,
            dataset_manifest=dataset_manifest,
            mark_cache=mark_cache,
            physical_symbol=physical,
            timestamp=ts,
        )
        rate = fact.get("funding_rate")
        if rate is None or mark is None:
            raise ResearchV2RunnerError(f"FUNDING_FACT_DATA_INVALID:{physical}:{_iso(ts)}:RATE_OR_MARK_MISSING")
        sign = Decimal("-1") if direction == "LONG" else Decimal("1")
        cashflow = sign * quantity * mark["price"] * _decimal(rate)
        event_id = canonical_json_digest(
            {
                "context_id": context_id,
                "order_spec_id": order.get("order_spec_id"),
                "physical_symbol": physical,
                "funding_timestamp": _iso(ts),
                "quantity": str(quantity),
                "direction": direction,
            }
        )
        out.append(
            {
                "event_id": event_id,
                "context_id": context_id,
                "order_spec_id": order.get("order_spec_id"),
                "logical_symbol": logical,
                "physical_symbol": physical,
                "funding_timestamp": _iso(ts),
                "funding_rate": str(rate),
                "funding_source_hash": fact.get("funding_source_hash") or fact.get("sha256") or fact.get("source_hash"),
                "funding_source_provenance": fact.get("funding_source_provenance") or fact.get("source") or fact.get("source_ref") or fact.get("provenance") or "frozen_dataset_funding_facts",
                "factual_boundary_mark": str(mark["price"]),
                "mark_timestamp": _iso(mark["timestamp"]),
                "mark_source_hash": mark.get("source_hash"),
                "mark_source_provenance": mark.get("source_provenance"),
                "held_quantity": str(quantity),
                "direction": direction,
                "sign_convention": "-Q*mark*rate" if direction == "LONG" else "+Q*mark*rate",
                "calculated_funding_cashflow": _compact_decimal_text(cashflow),
                "applied_to_account_at": _iso(ts),
            }
        )
    return tuple(out)


def _canonical_lifecycle_funding_facts(
    funding_facts: Sequence[Mapping[str, Any]],
    *,
    dataset_manifest: Mapping[str, Any],
    mark_cache: dict[str, tuple[HistoricalCandle, ...]] | None,
    physical_symbol: str,
) -> tuple[dict[str, Any], ...]:
    canonical: list[dict[str, Any]] = []
    funding_record = _dataset_file_record(dataset_manifest, physical_symbol=physical_symbol, file_type="funding_facts") or {}
    for fact in funding_facts:
        row = dict(fact)
        row.setdefault("funding_source_hash", row.get("sha256") or row.get("source_hash") or funding_record.get("sha256"))
        row.setdefault("funding_source_provenance", row.get("source") or row.get("source_ref") or row.get("provenance") or funding_record.get("local_path") or "frozen_dataset_funding_facts")
        ts_text = row.get("funding_time") or row.get("timestamp") or row.get("funding_timestamp")
        if ts_text is None:
            canonical.append(row)
            continue
        ts = _parse_time(str(ts_text))
        mark = _funding_boundary_mark(
            fact=row,
            dataset_manifest=dataset_manifest,
            mark_cache=mark_cache,
            physical_symbol=physical_symbol,
            timestamp=ts,
        )
        if mark is not None:
            row.setdefault("mark_price", str(mark["price"]))
            row.setdefault("mark_timestamp", _iso(mark["timestamp"]))
            row.setdefault("mark_source_hash", mark.get("source_hash"))
            row.setdefault("mark_source_provenance", mark.get("source_provenance"))
        canonical.append(row)
    return tuple(canonical)


def _funding_boundary_mark(
    *,
    fact: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any] | None,
    mark_cache: dict[str, tuple[HistoricalCandle, ...]] | None,
    physical_symbol: str,
    timestamp: datetime,
) -> dict[str, Any] | None:
    direct = fact.get("mark_price") or fact.get("funding_rate_mark_price") or fact.get("basis_mark_price")
    if direct is not None:
        return {
            "price": _decimal(direct),
            "timestamp": _parse_time(str(fact.get("mark_timestamp"))) if fact.get("mark_timestamp") else timestamp,
            "source_hash": fact.get("mark_source_hash") or fact.get("sha256") or fact.get("source_hash"),
            "source_provenance": fact.get("mark_source_provenance") or fact.get("source") or fact.get("source_ref") or fact.get("provenance") or "frozen_dataset_funding_fact_mark",
        }
    if dataset_manifest is None:
        return None
    marks = _marks_for_evidence(dataset_manifest=dataset_manifest, mark_cache=mark_cache, physical_symbol=physical_symbol)
    mark = _latest_mark_at_or_before(marks, timestamp)
    if mark is None:
        return None
    record = _dataset_file_record(dataset_manifest, physical_symbol=physical_symbol, file_type="mark_price_1m") or {}
    return {
        "price": mark.close,
        "timestamp": mark.close_time,
        "source_hash": record.get("sha256"),
        "source_provenance": record.get("local_path"),
    }


def _profile_cooldown_minutes(profile: Any) -> int:
    value = profile.sizing_profile.get("cooldown_minutes")
    if value is None:
        return 15
    return int(value)


def _portfolio_book_key(context: Mapping[str, Any]) -> str:
    identity = context.get("research_identity")
    if isinstance(identity, Mapping) and identity.get("batch_id") and identity.get("hypothesis_id"):
        return f"{identity['batch_id']}:{identity['hypothesis_id']}:{context['execution_profile_fingerprint']}"
    return f"{context['job_id']}:{context['execution_profile_fingerprint']}"


def _portfolio_book(
    portfolio_state: dict[str, V2ReplayPortfolioBook] | dict[str, V2PortfolioExposureState],
    key: str,
) -> V2ReplayPortfolioBook:
    existing = portfolio_state.get(key)
    if isinstance(existing, V2ReplayPortfolioBook):
        return existing
    if isinstance(existing, V2PortfolioExposureState):
        book = V2ReplayPortfolioBook(account_capital=existing.account_capital, active=[], last_accepted_at={}, realized_net_by_day={})
    else:
        book = V2ReplayPortfolioBook(account_capital=Decimal("1000"), active=[], last_accepted_at={}, realized_net_by_day={})
    portfolio_state[key] = book  # type: ignore[assignment]
    return book


def _phase_a_units(jobs: Sequence[ResearchV2JobConfig], dataset_manifest: Mapping[str, Any]) -> int:
    total = 0
    for job in _dedupe_set_scan_jobs(jobs):
        for symbol in job.symbols:
            physical = physical_symbol_for_research_v2(symbol)
            try:
                total += len(_job_calendar_cutoffs(job, _load_dataset_candles(dataset_manifest, physical_symbol=physical)))
            except Exception:
                continue
    return max(total, 1)


def _dedupe_set_scan_jobs(jobs: Sequence[ResearchV2JobConfig]) -> list[ResearchV2JobConfig]:
    selected: dict[str, ResearchV2JobConfig] = {}
    for job in jobs:
        if job.signal_family == "LEGACY_SET":
            continue
        selected.setdefault(_set_scan_key(job), job)
    return list(selected.values())


def _set_scan_key(job: ResearchV2JobConfig) -> str:
    signal = dict(job.runtime_profile.get("signal", {}))
    payload: dict[str, Any] = {"signal": signal, "symbols": list(job.symbols), "window": [job.window_start, job.window_end]}
    identity = _research_identity_payload(job)
    if identity:
        payload["research_identity"] = identity
    return canonical_json_digest(payload)


def _research_identity_payload(
    job: ResearchV2JobConfig,
    *,
    dataset_fingerprint: str | None = None,
    population_fingerprint: str | None = None,
    execution_profile_fingerprint: str | None = None,
) -> dict[str, Any]:
    identity_method = getattr(job, "identity_payload", None)
    hypothesis = job.runtime_profile.get("hypothesis", {})
    if not callable(identity_method) and (
        not isinstance(hypothesis, Mapping) or not hypothesis.get("batch_id") or not hypothesis.get("hypothesis_id")
    ):
        return {}
    if callable(identity_method):
        payload = dict(identity_method(dataset_fingerprint=dataset_fingerprint, population_fingerprint=population_fingerprint))
    else:
        payload = {
            "batch_id": hypothesis.get("batch_id"),
            "hypothesis_id": hypothesis.get("hypothesis_id"),
            "parent_job_id": hypothesis.get("parent_job_id"),
            "parent_hypothesis_id": hypothesis.get("parent_hypothesis_id"),
            "research_direction": hypothesis.get("research_direction"),
            "resolved_config": job.normalized_config(),
            "strategy_fingerprint": getattr(job, "signal_config_fingerprint", None),
            "dataset_fingerprint": dataset_fingerprint,
            "window": {"start_inclusive": job.window_start, "end_exclusive": job.window_end},
            "warmup": job.runtime_profile.get("warmup_days"),
            "population_fingerprint": population_fingerprint,
        }
    if execution_profile_fingerprint is not None:
        payload["execution_profile_fingerprint"] = execution_profile_fingerprint
    elif payload.get("execution_profile_fingerprint") is None:
        payload.pop("execution_profile_fingerprint", None)
    return {key: value for key, value in payload.items() if value is not None}


def _append_candidate_census(
    *,
    output_dir: Path,
    job: ResearchV2JobConfig,
    symbol: str,
    observed_at: datetime,
    signal,
    evidence: Mapping[str, Any],
) -> None:
    identity = _research_identity_payload(job)
    if not identity:
        return
    gate_results = {
        key: value
        for key, value in evidence.items()
        if key.endswith("_gate") or key.endswith("_min") or key in {"signal_status", "signal_direction", "signal_reason"}
    }
    unavailable = sorted(key for key, value in evidence.items() if key.endswith("_status") and value != V2DecisionStatus.AVAILABLE.value)
    row = {
        "batch_id": identity.get("batch_id"),
        "hypothesis_id": identity.get("hypothesis_id"),
        "parent_job_id": identity.get("parent_job_id"),
        "timestamp": _iso(observed_at),
        "symbol": symbol,
        "raw_direction": signal.direction.value,
        "status": signal.status.value,
        "first_rejection_reason": None if signal.status is V2DecisionStatus.PASS else signal.reason,
        "simultaneous_blockers": unavailable,
        "gate_results": gate_results,
        "feature_values": dict(evidence),
        "feature_availability": {key: value for key, value in evidence.items() if key.endswith("_status")},
        "research_identity": identity,
    }
    append_jsonl(output_dir / "hypothesis_candidate_census.jsonl", row)


def _execution_contexts_from_population(population: Mapping[str, Any], selected_jobs: Sequence[ResearchV2JobConfig]) -> list[dict[str, Any]]:
    jobs_by_id = {job.job_id: job for job in selected_jobs}
    contexts: list[dict[str, Any]] = []
    for record in population.get("records", ()):
        for job_id in record.get("applicable_jobs", ()):
            job = jobs_by_id.get(str(job_id))
            if job is None:
                continue
            profile = build_research_v2_canonical_execution_profile(job)
            research_identity = _research_identity_payload(job, execution_profile_fingerprint=profile.config_fingerprint)
            contexts.append(
                {
                    "context_id": canonical_json_digest(
                        {
                            "set_result_id": record["set_result_id"],
                            "job_id": job.job_id,
                            "profile": profile.config_fingerprint,
                            "research_identity": research_identity,
                        }
                    ),
                    "job_id": job.job_id,
                    "job": job,
                    "set_scan_key": record["set_scan_key"],
                    "execution_profile_fingerprint": profile.config_fingerprint,
                    "research_identity": research_identity,
                    "record": record,
                    "symbol": record["symbol"],
                    "observed_at": record["observed_at"],
                }
            )
    return sorted(contexts, key=lambda item: (str(item["observed_at"]), str(item["symbol"]), str(item["job_id"]), str(item["context_id"])))


def _context_identity(context: Mapping[str, Any]) -> tuple[str, str]:
    if "record" in context:
        return str(context["job_id"]), str(context["record"]["set_result_id"]), str(context["execution_profile_fingerprint"])
    return str(context["job_id"]), str(context["set_result_id"]), str(context["execution_profile_fingerprint"])


def _context_payload(context: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "context_id": str(context["context_id"]),
        "job_id": str(context["job_id"]),
        "set_result_id": str(context["record"]["set_result_id"]),
        "decision_cycle_id": str(context["record"]["decision_cycle_id"]),
        "execution_profile_fingerprint": str(context["execution_profile_fingerprint"]),
        "symbol": str(context["symbol"]),
        "observed_at": str(context["observed_at"]),
        "set_scan_key": str(context["set_scan_key"]),
    }
    if context.get("research_identity"):
        payload["research_identity"] = dict(context["research_identity"])
    return payload


def _write_phase_b_job_results(
    output_dir: Path,
    selected_jobs: Sequence[ResearchV2JobConfig],
    contexts: Sequence[Mapping[str, Any]],
    *,
    dataset_manifest: Mapping[str, Any] | None = None,
    apply_daily_cancel_overrides: bool = True,
) -> None:
    if apply_daily_cancel_overrides:
        _apply_daily_guard_cancellation_overrides(output_dir)
    _rewrite_account_event_ledger_sorted(output_dir)
    if dataset_manifest is not None:
        _rewrite_factual_timeline_guard_evidence_from_event_ledger(output_dir, selected_jobs=selected_jobs, dataset_manifest=dataset_manifest)
        _write_factual_mtm_series_from_event_ledger(output_dir, selected_jobs=selected_jobs, dataset_manifest=dataset_manifest)
        _write_source_authentication_package(output_dir, dataset_manifest=dataset_manifest)
    job_results_path = output_dir / "job_results.jsonl"
    if job_results_path.exists():
        job_results_path.unlink()
    rows = read_jsonl(output_dir / "lifecycle_results.jsonl")
    by_job: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_job[str(row.get("context", {}).get("job_id"))].append(row)
    for job in selected_jobs:
        job_rows = by_job.get(job.job_id, [])
        counts = {
            "episodes": len(job_rows),
            "matched": len(job_rows),
            "approved": 0,
            "blocked": 0,
            "accepted": 0,
            "filled": 0,
            "closed": 0,
            "censored": 0,
            "open_at_end": 0,
            "pending_at_end": 0,
        }
        money = {
            "gross_pnl": Decimal("0"),
            "fees": Decimal("0"),
            "closed_trade_fees": Decimal("0"),
            "all_known_execution_fees": Decimal("0"),
            "open_position_entry_fees": Decimal("0"),
            "funding": Decimal("0"),
            "net_closed_pnl": Decimal("0"),
            "end_mtm_contribution": Decimal("0"),
            "margin": Decimal("0"),
            "notional": Decimal("0"),
            "accepted_notional": Decimal("0"),
        }
        invalid_reasons: set[str] = set()
        for row in job_rows:
            result = row.get("result", {})
            if result.get("order_spec"):
                counts["approved"] += 1
            elif result.get("status") in {"BLOCKED", "CONSTRUCTION_REJECTED", "PORTFOLIO_BLOCKED", "POSITION_REJECTED", "HYPOTHESIS_REJECTED"}:
                counts["blocked"] += 1
            lifecycle = result.get("backtest_lifecycle", {})
            counts["accepted"] += 1 if lifecycle.get("accepted") else 0
            counts["filled"] += 1 if lifecycle.get("filled") else 0
            counts["censored"] += 1 if lifecycle.get("censored") else 0
            counts["closed"] += 1 if lifecycle.get("status") == "CLOSED" else 0
            if lifecycle.get("status") == "FILLED_OPEN_AT_ENDPOINT":
                counts["open_at_end"] += 1
                endpoint = result.get("endpoint_mtm") if isinstance(result.get("endpoint_mtm"), Mapping) else {}
                if endpoint.get("status") != "MTM_AVAILABLE":
                    invalid_reasons.add("ENDPOINT_OPEN_MTM_UNAVAILABLE")
                else:
                    money["end_mtm_contribution"] = money.get("end_mtm_contribution", Decimal("0")) + _decimal(endpoint.get("endpoint_unrealized_net_contribution", "0"))
            if lifecycle.get("filled") and lifecycle.get("censored") and lifecycle.get("status") != "FILLED_OPEN_AT_ENDPOINT":
                invalid_reasons.add(f"LIFECYCLE_CENSORED:{lifecycle.get('reason_code') or lifecycle.get('reason')}")
            if lifecycle.get("accepted") and not lifecycle.get("filled") and not lifecycle.get("completed"):
                counts["pending_at_end"] += 1
            if lifecycle.get("filled") and result.get("order_spec"):
                econ = result["order_spec"]["order_spec"]["economics"]
                money["margin"] += _decimal(econ.get("actual_committed_margin", "0"))
                entry_notional = _decimal(econ.get("actual_order_notional", "0"))
                money["accepted_notional"] += entry_notional
                money["notional"] += entry_notional
                entry_fee = entry_notional * _decimal(econ.get("maker_fee_rate", "0"))
                money["all_known_execution_fees"] += entry_fee
                if lifecycle.get("status") == "FILLED_OPEN_AT_ENDPOINT":
                    money["open_position_entry_fees"] += entry_fee
            closed = lifecycle.get("closed_result")
            if isinstance(closed, Mapping):
                money["gross_pnl"] += _decimal(closed.get("gross_pnl", "0"))
                closed_fees = _decimal(closed.get("entry_fee", "0")) + _decimal(closed.get("exit_fee", "0")) + _decimal(closed.get("other_fees", "0"))
                money["fees"] += closed_fees
                money["closed_trade_fees"] += closed_fees
                money["all_known_execution_fees"] += _decimal(closed.get("exit_fee", "0")) + _decimal(closed.get("other_fees", "0"))
                money["funding"] += _decimal(closed.get("funding", "0"))
                money["net_closed_pnl"] += _decimal(closed.get("net_pnl", "0"))
                money["notional"] += _decimal(closed.get("exit_vwap", "0")) * _decimal(closed.get("quantity", "0"))
        if job.signal_family == "LEGACY_SET":
            invalid_reasons.add("LEGACY_SET_CALENDAR_EXECUTOR_NOT_EXPOSED_FOR_RESEARCH_V2_RUNNER")
        invalid = tuple(sorted(invalid_reasons))
        result = normalize_job_result(_screening_output(job=job, counts=counts, money=money, invalid=invalid), job=job)
        persist_job_result(output_dir, job, result)
        append_jsonl(job_results_path, result)
    _reconcile_final_progress_counts(output_dir, rows)


def _resolution_from_record(record: Mapping[str, Any]) -> ResearchV2SetResolution:
    payload = record["resolution"]["research_v2_set_resolution"]
    from triggertrade.set_scope import SetConfigurationBinding

    binding = SetConfigurationBinding.from_payload(payload["configuration_binding"])
    return ResearchV2SetResolution(
        job_id=str(payload["job_id"]),
        signal_family=str(payload["signal_family"]),
        signal_episode_id=str(payload["signal_episode_id"]),
        symbol=str(payload["symbol"]),
        physical_symbol=str(payload["physical_symbol"]),
        observed_at=str(payload["observed_at"]),
        direction=V2Direction(str(payload["direction"])),
        status=str(payload["status"]),
        reason_code=None if payload.get("reason_code") is None else str(payload["reason_code"]),
        config_fingerprint=str(payload["config_fingerprint"]),
        job_config_fingerprint=str(payload["job_config_fingerprint"]),
        source_feature_evidence=dict(payload["source_feature_evidence"]),
        source_evidence_digest=str(payload["source_evidence_digest"]),
        decision_cycle_id=None if payload.get("decision_cycle_id") is None else str(payload["decision_cycle_id"]),
        set_result_id=str(payload["set_result_id"]),
        set_config_id=str(payload["set_config_id"]),
        set_config_version=str(payload["set_config_version"]),
        configuration_binding=binding,
        result_payload=dict(payload["canonical_set_result"]),
    )


def _raw_archive_paths(dataset_manifest: Mapping[str, Any], *, physical_symbol: str) -> tuple[Path, ...]:
    paths = []
    for record in dataset_manifest.get("files", ()):
        if record.get("type") != "raw_trades_archive":
            continue
        symbol = str(record.get("physical_symbol") or record.get("symbol") or "").upper()
        if symbol != physical_symbol.upper():
            continue
        path = Path(str(record["local_path"]))
        paths.append((path if path.is_absolute() else ROOT / path).resolve())
    if not paths:
        raise ResearchV2RunnerError(f"RAW_TRADES_DATA_INVALID:{physical_symbol}:ARCHIVES_MISSING")
    return tuple(sorted(paths))


def _iter_raw_trade_points(path: Path) -> Iterator[RawTradePoint]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for offset, row in enumerate(reader):
            timestamp = _parse_raw_trade_time(str(row.get("timestamp") or ""))
            yield RawTradePoint(timestamp, _decimal(row["price"]), _decimal(row["size"]), offset, str(path))


def _parse_raw_trade_time(value: str) -> datetime:
    text = value.strip()
    if text.isdigit():
        number = int(text)
        if number > 10_000_000_000_000:
            return datetime.fromtimestamp(number / 1_000_000, tz=UTC)
        if number > 10_000_000_000:
            return datetime.fromtimestamp(number / 1000, tz=UTC)
        return datetime.fromtimestamp(number, tz=UTC)
    if _is_decimal_epoch_seconds(text):
        epoch = Decimal(text)
        seconds = int(epoch.to_integral_value(rounding=ROUND_FLOOR))
        micros = int(((epoch - Decimal(seconds)) * Decimal("1000000")).to_integral_value(rounding=ROUND_FLOOR))
        if micros >= 1_000_000:
            seconds += 1
            micros -= 1_000_000
        return datetime.fromtimestamp(seconds, tz=UTC).replace(microsecond=micros)
    return _parse_time(value)


def _is_decimal_epoch_seconds(value: str) -> bool:
    if not value or value.count(".") != 1:
        return False
    left, right = value.split(".", 1)
    return left.isdigit() and right.isdigit()


def _ema_series(bars, period: int) -> dict[datetime, Decimal]:
    if len(bars) < period:
        return {}
    seed = sum((bar.close for bar in bars[:period]), Decimal("0")) / Decimal(period)
    multiplier = Decimal("2") / Decimal(period + 1)
    ema = seed
    out = {bars[period - 1].close_time: ema}
    for bar in bars[period:]:
        ema = ((bar.close - ema) * multiplier) + ema
        out[bar.close_time] = ema
    return out


def _latest_swing_maps(
    bars,
) -> tuple[dict[datetime, Decimal], dict[datetime, Decimal], tuple[V2TimelineSwingReference, ...], tuple[V2TimelineSwingReference, ...]]:
    events_long: list[tuple[datetime, Decimal]] = []
    events_short: list[tuple[datetime, Decimal]] = []
    refs_long: list[V2TimelineSwingReference] = []
    refs_short: list[V2TimelineSwingReference] = []
    for idx in range(2, len(bars) - 2):
        left = bars[idx - 2:idx]
        pivot = bars[idx]
        right = bars[idx + 1:idx + 3]
        available = right[-1].close_time
        if pivot.low < min(bar.low for bar in left + right):
            events_long.append((available, pivot.low))
            refs_long.append(
                V2TimelineSwingReference(
                    price=pivot.low,
                    formed_at=pivot.close_time,
                    confirmed_at=available,
                    available_at=available,
                    kind="LOW",
                )
            )
        if pivot.high > max(bar.high for bar in left + right):
            events_short.append((available, pivot.high))
            refs_short.append(
                V2TimelineSwingReference(
                    price=pivot.high,
                    formed_at=pivot.close_time,
                    confirmed_at=available,
                    available_at=available,
                    kind="HIGH",
                )
            )
    return _expand_latest_events(events_long, bars), _expand_latest_events(events_short, bars), tuple(refs_long), tuple(refs_short)


def _latest_protective_swing_from_timeline(
    *,
    timeline: FeatureTimeline,
    cutoff: datetime,
    direction: V2Direction,
    entry: Decimal,
) -> V2TimelineSwingReference | None:
    cutoff_utc = cutoff.astimezone(UTC)
    refs = timeline.swing_low_refs if direction is V2Direction.LONG else timeline.swing_high_refs
    candidates = [
        ref
        for ref in refs
        if ref.available_at <= cutoff_utc
        and cutoff_utc - ref.available_at <= timedelta(minutes=60)
        and ((direction is V2Direction.LONG and ref.price < entry) or (direction is V2Direction.SHORT and ref.price > entry))
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda ref: ref.available_at)


def _expand_latest_events(events: Sequence[tuple[datetime, Decimal]], bars) -> dict[datetime, Decimal]:
    out: dict[datetime, Decimal] = {}
    latest: Decimal | None = None
    events_by_time: dict[datetime, Decimal] = {ts: value for ts, value in events}
    for bar in bars:
        if bar.close_time in events_by_time:
            latest = events_by_time[bar.close_time]
        if latest is not None:
            out[bar.close_time] = latest
    return out


def _latest_at_or_before(mapping: Mapping[datetime, Any], cutoff: datetime) -> Any | None:
    if cutoff in mapping:
        return mapping[cutoff]
    keys = sorted(mapping)
    idx = bisect_left(keys, cutoff)
    if idx == 0:
        return None
    return mapping[keys[idx - 1]]


def _median_decimal(values: Sequence[Decimal]) -> Decimal:
    rows = sorted(values)
    mid = len(rows) // 2
    if len(rows) % 2:
        return rows[mid]
    return (rows[mid - 1] + rows[mid]) / Decimal("2")


def _episode_reset_ready(job: ResearchV2JobConfig, reset_buffer: Sequence[tuple[Decimal, Decimal]]) -> bool:
    family = str(job.runtime_profile["signal"]["family"])
    if family == "EXHAUSTION_REVERSAL":
        return reversal_reset_ready(tuple(item[1] for item in reset_buffer))
    return ret_or_episode_reset_ready(reset_buffer)


def _text_or_none(value: Any) -> str | None:
    return None if value is None else str(value)


def execute_research_v2_job(job: ResearchV2JobConfig, dataset_manifest: Mapping[str, Any], output_dir: Path) -> Mapping[str, Any]:
    """Execute one job by using the V2 two-phase materialize -> replay path."""

    work_dir = output_dir / "_single_job_executor" / job.job_id
    materialized = materialize_research_v2_set_population(
        jobs=[job],
        dataset_manifest=dataset_manifest,
        output_dir=work_dir,
    )
    contexts = _execution_contexts_from_population(materialized, [job])
    replay_research_v2_materialized_population(
        contexts=contexts,
        dataset_manifest=dataset_manifest,
        output_dir=work_dir,
    )
    _write_phase_b_job_results(work_dir, [job], contexts, dataset_manifest=dataset_manifest)
    result_path = work_dir / "jobs" / job.job_id / "job_result.json"
    if result_path.exists():
        return json.loads(result_path.read_text(encoding="utf-8"))
    counts = {
        "episodes": 0,
        "matched": 0,
        "approved": 0,
        "blocked": 0,
        "accepted": 0,
        "filled": 0,
        "closed": 0,
        "censored": 0,
        "open_at_end": 0,
        "pending_at_end": 0,
    }
    money = {
        "gross_pnl": Decimal("0"),
        "fees": Decimal("0"),
        "funding": Decimal("0"),
        "net_closed_pnl": Decimal("0"),
        "margin": Decimal("0"),
        "notional": Decimal("0"),
    }
    return _screening_output(job=job, counts=counts, money=money, invalid=("NO_MATERIALIZED_EXECUTION_CONTEXTS",))


def _screening_output(
    *,
    job: ResearchV2JobConfig,
    counts: Mapping[str, int],
    money: Mapping[str, Decimal],
    invalid: Sequence[str],
) -> dict[str, Any]:
    net = money["net_closed_pnl"]
    endpoint_mtm = money.get("end_mtm_contribution", Decimal("0"))
    turnover = money["notional"]
    status = "DATA_INVALID" if invalid else "COMPLETE"
    output = ResearchV2ScreeningOutput(
        job_id=job.job_id,
        config_fingerprint=job.config_fingerprint,
        status=status,
        evaluation_start=job.window_start,
        evaluation_end=job.window_end,
        symbols=job.symbols,
        unique_signal_episodes=counts["episodes"],
        matched=counts["matched"],
        approved=counts["approved"],
        blocked=counts["blocked"],
        accepted=counts["accepted"],
        filled=counts["filled"],
        closed=counts["closed"],
        censored=counts["censored"],
        open_at_end=counts["open_at_end"],
        pending_at_end=counts["pending_at_end"],
        gross_pnl=money["gross_pnl"],
        fees=money["fees"],
        funding=money["funding"],
        net_closed_pnl=net,
        end_mtm_contribution=endpoint_mtm,
        account_net=None if invalid else net + endpoint_mtm,
        actual_margin_used=money["margin"],
        actual_notional_turnover=turnover,
        mean_net_notional_expectancy=(net / turnover) if turnover else None,
        max_mtm_drawdown=None,
        stress_net=None,
        leave_best_event_out_net=None,
        data_invalid_reasons=tuple(invalid),
        economic_gate_result="DATA_INVALID" if invalid else "NOT_EVALUATED",
    )
    payload = asdict(output)
    payload["closed_trade_fees"] = money.get("closed_trade_fees", money["fees"])
    payload["all_known_execution_fees"] = money.get("all_known_execution_fees", money["fees"])
    payload["open_position_entry_fees"] = money.get("open_position_entry_fees", Decimal("0"))
    return payload


def _load_dataset_candles(dataset_manifest: Mapping[str, Any], *, physical_symbol: str) -> tuple[HistoricalCandle, ...]:
    path = _dataset_file(dataset_manifest, physical_symbol=physical_symbol, file_type="candles_1m")
    rows = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        HistoricalCandle(
            symbol=str(row.get("symbol") or physical_symbol).upper(),
            category=str(row.get("category") or "linear"),
            timeframe=str(row.get("timeframe") or "1m"),
            open_time=_parse_time(str(row["open_time"])),
            close_time=_parse_time(str(row["close_time"])),
            open=_decimal(row["open"]),
            high=_decimal(row["high"]),
            low=_decimal(row["low"]),
            close=_decimal(row["close"]),
            volume=_decimal(row.get("volume", "0")),
            turnover=_decimal(row.get("turnover", "0")),
            completed=bool(row.get("completed", True)),
        )
        for row in rows
    )


def _load_dataset_funding_facts(dataset_manifest: Mapping[str, Any], *, physical_symbol: str) -> tuple[Mapping[str, Any], ...]:
    try:
        path = _dataset_file(dataset_manifest, physical_symbol=physical_symbol, file_type="funding_facts")
    except ResearchV2RunnerError:
        return ()
    rows = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(rows, Mapping):
        rows = rows.get("records") or rows.get("funding") or rows.get("rows") or ()
    return tuple(dict(row) for row in rows)


def _load_dataset_mark_candles(dataset_manifest: Mapping[str, Any], *, physical_symbol: str) -> tuple[HistoricalCandle, ...]:
    path = _dataset_file(dataset_manifest, physical_symbol=physical_symbol, file_type="mark_price_1m")
    rows = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(rows, Mapping):
        rows = rows.get("records") or rows.get("candles") or rows.get("rows") or ()
    return tuple(
        HistoricalCandle(
            symbol=str(row.get("symbol") or physical_symbol).upper(),
            category=str(row.get("category") or "linear"),
            timeframe=str(row.get("timeframe") or "1m"),
            open_time=_parse_time(str(row["open_time"])),
            close_time=_parse_time(str(row["close_time"])),
            open=_decimal(row["open"]),
            high=_decimal(row["high"]),
            low=_decimal(row["low"]),
            close=_decimal(row["close"]),
            volume=_decimal(row.get("volume", "0")),
            turnover=_decimal(row.get("turnover", "0")),
            completed=bool(row.get("completed", True)),
        )
        for row in rows
    )


def _load_dataset_venue(dataset_manifest: Mapping[str, Any], *, physical_symbol: str) -> VenueConstraints:
    try:
        path = _dataset_file(dataset_manifest, physical_symbol=physical_symbol, file_type="instrument_metadata")
    except ResearchV2RunnerError:
        return VenueConstraints(Decimal("0.1"), Decimal("0.001"), Decimal("0.001"), Decimal("5"), Decimal("1000000000"))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, Mapping) and isinstance(payload.get("instrument"), Mapping):
        source = payload["instrument"]
    elif isinstance(payload, Mapping) and isinstance(payload.get("payload"), Mapping):
        source = payload["payload"]
    else:
        source = payload
    if not isinstance(source, Mapping):
        source = {}
    lot = source.get("lotSizeFilter") if isinstance(source.get("lotSizeFilter"), Mapping) else {}
    price = source.get("priceFilter") if isinstance(source.get("priceFilter"), Mapping) else {}
    return VenueConstraints(
        tick_size=_decimal(source.get("tick_size") or price.get("tickSize") or "0.1"),
        qty_step=_decimal(source.get("qty_step") or lot.get("qtyStep") or "0.001"),
        min_qty=_decimal(source.get("min_qty") or lot.get("minOrderQty") or "0.001"),
        min_notional=_decimal(source.get("min_notional") or lot.get("minNotionalValue") or "5"),
        max_qty=_optional_decimal(source.get("max_qty") or lot.get("maxOrderQty")),
    )


def _dataset_file(dataset_manifest: Mapping[str, Any], *, physical_symbol: str, file_type: str) -> Path:
    for record in dataset_manifest.get("files", ()):
        if record.get("type") != file_type:
            continue
        symbol = str(record.get("physical_symbol") or record.get("symbol") or "").upper()
        path_text = str(record.get("local_path") or "")
        if symbol != physical_symbol.upper() and physical_symbol.upper() not in Path(path_text).name.upper():
            continue
        path = Path(path_text)
        return (path if path.is_absolute() else ROOT / path).resolve()
    raise ResearchV2RunnerError(f"dataset missing {file_type} for {physical_symbol}")


def _dataset_file_record(dataset_manifest: Mapping[str, Any], *, physical_symbol: str, file_type: str) -> Mapping[str, Any] | None:
    for record in dataset_manifest.get("files", ()):
        if record.get("type") != file_type:
            continue
        symbol = str(record.get("physical_symbol") or record.get("symbol") or "").upper()
        path_text = str(record.get("local_path") or "")
        if symbol != physical_symbol.upper() and physical_symbol.upper() not in Path(path_text).name.upper():
            continue
        return record
    return None


def _daily_equity_guard_evidence(
    *,
    book: V2ReplayPortfolioBook,
    job_id: str,
    as_of: datetime,
    dataset_manifest: Mapping[str, Any],
    mark_cache: dict[str, tuple[HistoricalCandle, ...]] | None,
    daily_loss_fraction: Decimal,
) -> dict[str, Any]:
    window = accounting_day_window(as_of)
    day_id = window.accounting_day_id
    boundary_start = _parse_time(window.boundary_start_at)
    if day_id not in book.day_opening_equity:
        book.day_opening_equity[day_id] = _equity_from_ledger_events(
            book.account_events,
            as_of=boundary_start,
            dataset_manifest=dataset_manifest,
            mark_cache=mark_cache or {},
            active_exposures=book.active,
        )["equity"]
    day_opening = book.day_opening_equity[day_id]
    snapshot = _equity_from_ledger_events(
        book.account_events,
        as_of=as_of,
        dataset_manifest=dataset_manifest,
        mark_cache=mark_cache or {},
        active_exposures=book.active,
    )
    realized_gross_total = snapshot["realized_gross"]
    realized_fees_total = snapshot["fees"]
    realized_funding_total = snapshot["funding"]
    open_mtm = snapshot["open_mtm"]
    open_positions = snapshot["open_positions"]
    mark_unavailable = any(str(position.get("mark_status")) == "MARK_UNAVAILABLE" for position in open_positions)
    current = snapshot["equity"]
    daily_delta = current - day_opening
    daily_delta_fraction = Decimal("0") if day_opening == 0 else daily_delta / day_opening
    threshold = -daily_loss_fraction
    decision = "DATA_UNAVAILABLE" if mark_unavailable else ("REJECT" if daily_delta_fraction <= threshold else "PASS")
    return {
        "job_id": job_id,
        "evaluated_at": _iso(as_of),
        "accounting_day": day_id,
        "accounting_day_timezone": window.timezone,
        "accounting_day_boundary_start": window.boundary_start_at,
        "accounting_day_boundary_end": window.boundary_end_at,
        "day_opening_equity": str(day_opening),
        "realized_gross_pnl_to_date": str(realized_gross_total),
        "realized_fees_to_date": str(realized_fees_total),
        "realized_funding_to_date": str(realized_funding_total),
        "open_positions": open_positions,
        "current_open_position_factual_mtm": str(open_mtm),
        "current_factual_equity": str(current),
        "daily_equity_delta_usdt": str(daily_delta),
        "daily_equity_delta_fraction": str(daily_delta_fraction),
        "daily_equity_delta_pct": str(daily_delta_fraction * Decimal("100")),
        "configured_loss_threshold_fraction": str(daily_loss_fraction),
        "threshold_operator": "<=",
        "mark_source": "FROZEN_MARK_PRICE_1M",
        "loss_guard_decision": decision,
        "source_provenance": "runtime/data/research-v2/7d_20260819_20260826/dataset_manifest.json",
    }


def _pending_guard_horizon(book: V2ReplayPortfolioBook, *, start_at: datetime, window_end: datetime) -> datetime | None:
    horizons: list[datetime] = []
    for exposure in book.pending_entry_exposures(start_at):
        if exposure.opened_at is not None and exposure.opened_at > start_at:
            horizons.append(exposure.opened_at)
        elif exposure.release_at is not None and exposure.release_at > start_at:
            horizons.append(exposure.release_at)
        else:
            horizons.append(window_end)
    return max(horizons) if horizons else None


def _factual_timeline_guard_points(book: V2ReplayPortfolioBook, *, start_at: datetime, end_at: datetime) -> tuple[datetime, ...]:
    points: set[datetime] = set()
    minute = start_at.replace(second=0, microsecond=0)
    if minute <= start_at:
        minute += timedelta(minutes=1)
    while minute < end_at:
        points.add(minute)
        minute += timedelta(minutes=1)
    for event in book.account_events:
        if start_at < event.timestamp < end_at and event.event_type in {
            "ENTRY_FILLED",
            "ENTRY_FEE",
            "FUNDING_BOUNDARY",
            "PROTECTIVE_EXIT",
            "EXIT_FEE",
            "FINAL_CLOSE",
            "RESERVATION_RELEASE",
        }:
            points.add(event.timestamp)
    return tuple(sorted(points))


def _factual_timeline_daily_guard_enforcement(
    *,
    book: V2ReplayPortfolioBook,
    job_id: str,
    start_at: datetime,
    window_end: datetime,
    dataset_manifest: Mapping[str, Any],
    mark_cache: dict[str, tuple[HistoricalCandle, ...]] | None,
    daily_loss_fraction: Decimal,
    trigger_context_id: str,
    trigger_lifecycle_index: int | None = None,
) -> tuple[list[dict[str, Any]], list[V2ReplayAccountEvent]]:
    horizon = _pending_guard_horizon(book, start_at=start_at, window_end=window_end)
    if horizon is None or horizon <= start_at:
        return [], []
    evidence_rows: list[dict[str, Any]] = []
    for timestamp in _factual_timeline_guard_points(book, start_at=start_at, end_at=horizon):
        pending = book.pending_entry_exposures(timestamp)
        if not pending:
            break
        protected = book.open_position_exposures(timestamp)
        guard = _daily_equity_guard_evidence(
            book=book,
            job_id=job_id,
            as_of=timestamp,
            dataset_manifest=dataset_manifest,
            mark_cache=mark_cache,
            daily_loss_fraction=daily_loss_fraction,
        )
        breached = guard["loss_guard_decision"] == "REJECT"
        row = {
            "job_id": job_id,
            "evaluated_at": _iso(timestamp),
            "trigger_context_id": trigger_context_id,
            "trigger_lifecycle_index": trigger_lifecycle_index,
            "factual_timeline_guard": True,
            "day_opening_equity": guard["day_opening_equity"],
            "current_factual_equity": guard["current_factual_equity"],
            "daily_equity_delta_fraction": guard["daily_equity_delta_fraction"],
            "configured_loss_threshold_fraction": guard["configured_loss_threshold_fraction"],
            "breached": breached,
            "pending_order_context_ids": [exposure.context_id for exposure in pending],
            "pending_order_spec_ids": [exposure.order_spec_id for exposure in pending],
            "protected_open_position_context_ids": [exposure.context_id for exposure in protected],
            "protected_open_position_order_spec_ids": [exposure.order_spec_id for exposure in protected],
            "open_positions": guard["open_positions"],
            "source_provenance": guard["source_provenance"],
        }
        if breached:
            cancel_events = book.cancel_pending_for_daily_guard(
                as_of=timestamp,
                trigger={
                    "trigger_kind": "FACTUAL_TIMELINE_DAILY_GUARD",
                    "trigger_context_id": trigger_context_id,
                    "trigger_lifecycle_index": trigger_lifecycle_index,
                    "trigger_evaluated_at": _iso(timestamp),
                },
                retain_until_release=True,
            )
            row["cancellation_obligations_generated"] = len({event.context_id for event in cancel_events if event.event_type == "ENTRY_CANCELLED_UNFILLED"})
            row["cancellation_events_generated"] = [event.to_payload() for event in cancel_events]
            row["reservation_releases_generated"] = [event.context_id for event in cancel_events if event.event_type == "RESERVATION_RELEASE"]
            evidence_rows.append(row)
            book.factual_timeline_guard_evidence.extend(evidence_rows)
            return evidence_rows, cancel_events
        row["cancellation_obligations_generated"] = 0
        row["cancellation_events_generated"] = []
        row["reservation_releases_generated"] = []
        evidence_rows.append(row)
    book.factual_timeline_guard_evidence.extend(evidence_rows)
    return evidence_rows, []


def _causal_equity_delta_at(
    *,
    book: V2ReplayPortfolioBook,
    as_of: datetime,
    dataset_manifest: Mapping[str, Any],
    mark_cache: dict[str, tuple[HistoricalCandle, ...]] | None,
    include_open_mtm: bool,
) -> Decimal:
    realized_gross = _event_sum(book.account_events, as_of=as_of, since=None, field="realized_gross_pnl", event_types={"FINAL_CLOSE"})
    fees = _event_sum(book.account_events, as_of=as_of, since=None, field="fee_amount", event_types={"ENTRY_FEE", "EXIT_FEE"})
    funding = _event_sum(book.account_events, as_of=as_of, since=None, field="funding_amount", event_types={"FUNDING_BOUNDARY"})
    mtm = Decimal("0")
    if include_open_mtm:
        for exposure in book.active:
            if exposure.opened_at is None or exposure.opened_at > as_of or (exposure.release_at is not None and exposure.release_at <= as_of):
                continue
            if exposure.entry_price is None or exposure.quantity is None:
                continue
            marks = _marks_for_evidence(dataset_manifest=dataset_manifest, mark_cache=mark_cache, physical_symbol=exposure.physical_symbol)
            mark = _latest_mark_at_or_before(marks, as_of)
            if mark is None:
                continue
            mtm += (mark.close - exposure.entry_price) * exposure.quantity if exposure.direction == "LONG" else (exposure.entry_price - mark.close) * exposure.quantity
    return realized_gross - fees + funding + mtm


def _event_sum(
    events: Sequence[V2ReplayAccountEvent],
    *,
    as_of: datetime,
    since: datetime | None,
    field: str,
    event_types: set[str],
) -> Decimal:
    total = Decimal("0")
    for event in events:
        if event.event_type not in event_types:
            continue
        if event.timestamp > as_of:
            continue
        if since is not None and event.timestamp < since:
            continue
        total += getattr(event, field)
    return total


def _marks_for_evidence(
    *,
    dataset_manifest: Mapping[str, Any],
    mark_cache: dict[str, tuple[HistoricalCandle, ...]] | None,
    physical_symbol: str,
) -> tuple[HistoricalCandle, ...]:
    if mark_cache is None:
        return ()
    if physical_symbol not in mark_cache:
        try:
            mark_cache[physical_symbol] = _load_dataset_mark_candles(dataset_manifest, physical_symbol=physical_symbol)
        except ResearchV2RunnerError:
            mark_cache[physical_symbol] = ()
    return mark_cache[physical_symbol]


def _endpoint_mtm_evidence(
    *,
    job_id: str,
    logical_symbol: str,
    physical_symbol: str,
    order_spec: Mapping[str, Any],
    lifecycle: Any,
    endpoint: datetime,
    marks: Sequence[HistoricalCandle],
    funding_facts: Sequence[Mapping[str, Any]],
    dataset_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    spec = order_spec["order_spec"]
    mark = _latest_mark_at_or_before(marks, endpoint)
    evidence = _lifecycle_evidence(lifecycle)
    entry_time = _optional_time(evidence.get("entry_filled_at"))
    entry = _decimal(spec["entry"]["price"])
    quantity = _decimal(spec["entry"]["quantity"])
    direction = str(spec["direction"]).upper()
    entry_fee = _decimal(spec["economics"]["actual_order_notional"]) * _decimal(spec["economics"]["maker_fee_rate"])
    funding = Decimal("0")
    funding_events: tuple[dict[str, Any], ...] = ()
    if entry_time is not None and mark is not None:
        funding_events = _funding_events_for_position(
            funding_facts=funding_facts,
            dataset_manifest=None,
            mark_cache=None,
            order=spec,
            context_id=str(spec.get("order_spec_id") or ""),
            opened_at=entry_time,
            closed_at=endpoint,
            include_right_boundary=False,
        )
        funding = sum((_decimal(event["calculated_funding_cashflow"]) for event in funding_events), Decimal("0"))
    if mark is None:
        record = _dataset_file_record(dataset_manifest, physical_symbol=physical_symbol, file_type="mark_price_1m") if dataset_manifest is not None else None
        return {
            "job_id": job_id,
            "logical_symbol": logical_symbol,
            "physical_symbol": physical_symbol,
            "endpoint_timestamp": _iso(endpoint),
            "endpoint_mark_source": "FROZEN_MARK_PRICE_1M",
            "endpoint_mark_source_path": None if record is None else record.get("local_path"),
            "endpoint_mark_source_hash": None if record is None else record.get("sha256"),
            "status": "MTM_UNAVAILABLE",
            "reservation_still_active": True,
        }
    mark_price = mark.close
    record = _dataset_file_record(dataset_manifest, physical_symbol=physical_symbol, file_type="mark_price_1m") if dataset_manifest is not None else None
    gross = (mark_price - entry) * quantity if direction == "LONG" else (entry - mark_price) * quantity
    net = gross - entry_fee + funding
    return {
        "job_id": job_id,
        "logical_symbol": logical_symbol,
        "physical_symbol": physical_symbol,
        "quantity": str(quantity),
        "direction": direction,
        "entry_price": str(entry),
        "entry_time": None if entry_time is None else _iso(entry_time),
        "endpoint_timestamp": _iso(endpoint),
        "endpoint_mark_source": "FROZEN_MARK_PRICE_1M",
        "endpoint_mark_source_path": None if record is None else record.get("local_path"),
        "endpoint_mark_source_hash": None if record is None else record.get("sha256"),
        "endpoint_mark_price": str(mark_price),
        "endpoint_mark_close_time": _iso(mark.close_time),
        "unrealized_gross_pnl": str(gross),
        "known_entry_fees": str(entry_fee),
        "accrued_factual_funding_through_endpoint": str(funding),
        "funding_boundary_events": list(funding_events),
        "endpoint_unrealized_net_contribution": str(net),
        "reservation_still_active": True,
        "position_remains_open": True,
        "status": "MTM_AVAILABLE",
    }


def _latest_mark_at_or_before(marks: Sequence[HistoricalCandle], endpoint: datetime) -> HistoricalCandle | None:
    best = None
    for mark in marks:
        if mark.close_time <= endpoint and (best is None or mark.close_time > best.close_time):
            best = mark
    return best


def _instrument_constraints_evidence(dataset_manifest: Mapping[str, Any], *, physical_symbol: str, venue: VenueConstraints) -> dict[str, Any]:
    record = _dataset_file_record(dataset_manifest, physical_symbol=physical_symbol, file_type="instrument_metadata") or {}
    payload = None
    path_text = record.get("local_path")
    if path_text:
        path = Path(str(path_text))
        resolved = path if path.is_absolute() else ROOT / path
        if resolved.exists():
            payload = json.loads(resolved.read_text(encoding="utf-8"))
    return {
        "physical_symbol": physical_symbol,
        "tick_size": str(venue.tick_size),
        "quantity_step": str(venue.qty_step),
        "min_order_qty": str(venue.min_qty),
        "max_order_qty": None if venue.max_qty is None else str(venue.max_qty),
        "min_notional": str(venue.min_notional),
        "metadata_effective": record.get("start"),
        "metadata_version": record.get("sha256"),
        "source": record.get("source"),
        "local_path": record.get("local_path"),
        "original_frozen_metadata": payload,
    }


def _job_calendar_cutoffs(job: ResearchV2JobConfig, candles: Sequence[HistoricalCandle]) -> tuple[datetime, ...]:
    start = _parse_time(job.window_start)
    end = _parse_time(job.window_end)
    return tuple(
        candle.close_time
        for candle in sorted(candles, key=lambda item: item.close_time)
        if candle.completed and start < candle.close_time <= end
    )


def _evaluate_job_signal(
    job: ResearchV2JobConfig,
    *,
    candles: Sequence[HistoricalCandle],
    cutoff: datetime,
):
    r5 = return_pct_points(candles, cutoff=cutoff, window_minutes=5)
    r15 = return_pct_points(candles, cutoff=cutoff, window_minutes=15)
    atr = atr15(candles, cutoff=cutoff)
    latest = _completed_candle(candles, cutoff)
    evidence: dict[str, Any] = {
        "cutoff": _iso(cutoff),
        "return5_status": r5.status.value,
        "return15_status": r15.status.value,
        "atr15_status": atr.status.value,
        "reference_price": str(latest.close) if latest else None,
        "atr15": str(atr.value) if atr.value is not None else None,
    }
    if latest is None or r5.status is not V2DecisionStatus.AVAILABLE or r15.status is not V2DecisionStatus.AVAILABLE:
        return _unavailable_signal(job, "RETURN_WINDOW_UNAVAILABLE"), evidence
    base = ret5_ret15_or_signal(return5_pct_points=_decimal(r5.value), return15_pct_points=_decimal(r15.value))
    evidence.update({"return5_pct_points": str(r5.value), "return15_pct_points": str(r15.value)})
    family = str(job.runtime_profile["signal"]["family"])
    if family in {"RET5_RET15_OR", "RET5_OR_RET15"}:
        signal = base
    elif family == "MOMENTUM_CONTINUATION":
        ema20 = ema15(candles, cutoff=cutoff, period=20)
        ema50 = ema15(candles, cutoff=cutoff, period=50)
        rv = rvol5(candles, cutoff=cutoff)
        evidence.update(
            {
                "ema20_status": ema20.status.value,
                "ema50_status": ema50.status.value,
                "rvol5_status": rv.status.value,
                "ema20": str(ema20.value) if ema20.value is not None else None,
                "ema50": str(ema50.value) if ema50.value is not None else None,
                "rvol5": str(rv.value) if rv.value is not None else None,
            }
        )
        if ema20.status is not V2DecisionStatus.AVAILABLE or ema50.status is not V2DecisionStatus.AVAILABLE or rv.status is not V2DecisionStatus.AVAILABLE:
            signal = _unavailable_signal(job, "CONTINUATION_FEATURE_UNAVAILABLE")
        else:
            signal = continuation_signal(
                base=base,
                ema20=_decimal(ema20.value),
                ema50=_decimal(ema50.value),
                return15_pct_points=_decimal(r15.value),
                rvol5_value=_decimal(rv.value),
            )
    elif family == "COMPRESSION_BREAKOUT":
        signal = _compression_signal(job, candles=candles, cutoff=cutoff, latest=latest, atr=atr, evidence=evidence)
    elif family == "EXHAUSTION_REVERSAL":
        signal = _reversal_signal(job, candles=candles, cutoff=cutoff, latest=latest, r15=r15, atr=atr, evidence=evidence)
    else:
        signal = _unavailable_signal(job, f"UNSUPPORTED_SIGNAL_FAMILY:{family}")
    evidence["signal_status"] = signal.status.value
    evidence["signal_direction"] = signal.direction.value
    evidence["signal_reason"] = signal.reason
    if signal.status is V2DecisionStatus.PASS:
        entry = _entry_price_from_evidence(signal.direction, _decimal(evidence["reference_price"]), _decimal(evidence["atr15"]), Decimal("0.1"))
        swing = latest_protective_swing5(candles, cutoff=cutoff, direction=signal.direction, entry_price=entry)
        evidence["structural_reference_price"] = None if swing is None else str(swing.price)
        evidence["structural_reference_available_at"] = None if swing is None else _iso(swing.available_at)
    return signal, evidence


def _compression_signal(
    job: ResearchV2JobConfig,
    *,
    candles: Sequence[HistoricalCandle],
    cutoff: datetime,
    latest: HistoricalCandle,
    atr,
    evidence: dict[str, Any],
):
    rv = rvol5(candles, cutoff=cutoff)
    accel = turnover_acceleration(candles, cutoff=cutoff)
    bars5 = aggregate_completed_bars(candles, timeframe_minutes=5, cutoff=cutoff)
    bars15 = aggregate_completed_bars(candles, timeframe_minutes=15, cutoff=cutoff)
    atr_series = wilder_atr_series(bars15)
    preceding_atr = tuple(value for ts, value in atr_series if ts < cutoff)
    prior = bars5[-13:-1] if len(bars5) >= 13 else ()
    evidence.update(
        {
            "rvol5": str(rv.value) if rv.value is not None else None,
            "turnover_acceleration": str(accel.value) if accel.value is not None else None,
            "preceding_atr15_count": len(preceding_atr),
        }
    )
    if atr.status is not V2DecisionStatus.AVAILABLE or rv.status is not V2DecisionStatus.AVAILABLE or accel.status is not V2DecisionStatus.AVAILABLE or len(prior) < 12:
        return _unavailable_signal(job, "COMPRESSION_FEATURE_UNAVAILABLE")
    return compression_breakout_signal(
        atr15_value=_decimal(atr.value),
        preceding_atr15_values=preceding_atr,
        close=latest.close,
        prior_range_high=max(bar.high for bar in prior),
        prior_range_low=min(bar.low for bar in prior),
        rvol5_value=_decimal(rv.value),
        turnover_acceleration_value=_decimal(accel.value),
        compression_ratio_max=_decimal(job.runtime_profile["signal"].get("compression_ratio_max", "0.80")),
    )


def _reversal_signal(
    job: ResearchV2JobConfig,
    *,
    candles: Sequence[HistoricalCandle],
    cutoff: datetime,
    latest: HistoricalCandle,
    r15,
    atr,
    evidence: dict[str, Any],
):
    accel = turnover_acceleration(candles, cutoff=cutoff)
    recent = tuple(c for c in sorted(candles, key=lambda item: item.close_time) if cutoff - timedelta(minutes=15) < c.close_time <= cutoff)
    evidence["turnover_acceleration"] = str(accel.value) if accel.value is not None else None
    if r15.status is not V2DecisionStatus.AVAILABLE or atr.status is not V2DecisionStatus.AVAILABLE or accel.status is not V2DecisionStatus.AVAILABLE or len(recent) < 2:
        return _unavailable_signal(job, "REVERSAL_FEATURE_UNAVAILABLE")
    return reversal_signal(
        return15_pct_points=_decimal(r15.value),
        latest_close=latest.close,
        high_15m=max(candle.high for candle in recent),
        low_15m=min(candle.low for candle in recent),
        atr15_value=_decimal(atr.value),
        last_two_closes=tuple(candle.close for candle in recent[-2:]),
        turnover_acceleration_value=_decimal(accel.value),
    )


def _unavailable_signal(job: ResearchV2JobConfig, reason: str):
    family = str(job.runtime_profile["signal"]["family"])
    if family == "MOMENTUM_CONTINUATION":
        from triggertrade.research_v2 import V2_SIGNAL_CONTINUATION_VERSION

        version = V2_SIGNAL_CONTINUATION_VERSION
    elif family == "COMPRESSION_BREAKOUT":
        from triggertrade.research_v2 import V2_SIGNAL_COMPRESSION_VERSION

        version = V2_SIGNAL_COMPRESSION_VERSION
    elif family == "EXHAUSTION_REVERSAL":
        from triggertrade.research_v2 import V2_SIGNAL_REVERSAL_VERSION

        version = V2_SIGNAL_REVERSAL_VERSION
    else:
        from triggertrade.research_v2 import V2_SIGNAL_RET_OR_VERSION

        version = V2_SIGNAL_RET_OR_VERSION
    from triggertrade.research_v2 import V2SignalResult

    return V2SignalResult(V2DecisionStatus.UNAVAILABLE, V2Direction.NONE, version, reason)


def _handoff_facts_from_evidence(
    *,
    symbol: str,
    physical_symbol: str,
    observed_at: datetime,
    direction: V2Direction,
    candles: Sequence[HistoricalCandle],
    evidence: Mapping[str, Any],
    venue: VenueConstraints,
) -> HandoffFacts:
    reference = _decimal(evidence["reference_price"])
    atr = _decimal(evidence["atr15"])
    levels = _reference_levels(
        direction=direction,
        observed_at=observed_at,
        reference=reference,
        structural_reference=_optional_decimal(evidence.get("structural_reference_price")),
        structural_formed_at=_optional_time(evidence.get("structural_reference_formed_at")),
        structural_confirmed_at=_optional_time(evidence.get("structural_reference_confirmed_at")),
        structural_available_at=_optional_time(evidence.get("structural_reference_available_at")),
        structural_age_seconds=evidence.get("structural_reference_age_seconds"),
    )
    return HandoffFacts(
        symbol=symbol,
        created_at=_iso(observed_at),
        matched_at=_iso(observed_at),
        market_snapshot_at=_iso(observed_at),
        market_snapshot_id=f"research-v2-snapshot-{canonical_json_digest({'symbol': symbol, 'observed_at': _iso(observed_at)})[:24]}",
        set_match_reference_price=str(reference),
        reference_price_observed_at=_iso(observed_at),
        reference_price_source="RESEARCH_V2_FROZEN_DATASET_CLOSE",
        tick_size=str(venue.tick_size),
        metadata_revision=f"research-v2-dataset:{physical_symbol}",
        metadata_as_of=_iso(observed_at),
        atr_15m=_q18_decimal_text(atr),
        atr_pct_15m=_q18_decimal_text((atr / reference) if reference else Decimal("0")),
        reference_levels=levels,
        entry_context=HandoffContext("GENERIC", "NONE", None, None),
        sl_context=HandoffContext("GENERIC", "NONE", None, None),
        tp_context=HandoffContext("GENERIC", "NONE", None, None),
        core_set_id="RESEARCH_V2_CANONICAL_SET",
    )


def _reference_levels(
    *,
    direction: V2Direction,
    observed_at: datetime,
    reference: Decimal,
    structural_reference: Decimal | None,
    structural_formed_at: datetime | None = None,
    structural_confirmed_at: datetime | None = None,
    structural_available_at: datetime | None = None,
    structural_age_seconds: object | None = None,
) -> tuple[HandoffReferenceLevel, ...]:
    protective = structural_reference
    if protective is None:
        protective = reference * (Decimal("0.99") if direction is V2Direction.LONG else Decimal("1.01"))
    formed_at = structural_formed_at or observed_at
    confirmed_at = structural_confirmed_at or formed_at
    available_at = structural_available_at or confirmed_at
    age_seconds = int(structural_age_seconds) if structural_age_seconds is not None else int((observed_at.astimezone(UTC) - available_at).total_seconds())
    opposite = reference * (Decimal("1.01") if direction is V2Direction.LONG else Decimal("0.99"))
    return (
        HandoffReferenceLevel(
            level_id="v2-protective-reference",
            level_type="SWING_LOW_5M" if direction is V2Direction.LONG else "SWING_HIGH_5M",
            price=str(protective),
            timeframe="5m",
            formed_at=_iso(formed_at),
            confirmed_at=_iso(confirmed_at),
            available_at=_iso(available_at),
            source_metric="research_v2_swing5",
            age_seconds=age_seconds,
            relative_position="BELOW_REFERENCE" if protective < reference else "ABOVE_REFERENCE",
        ),
        HandoffReferenceLevel(
            level_id="v2-opposite-reference",
            level_type="CONTEXT_HIGH" if direction is V2Direction.LONG else "CONTEXT_LOW",
            price=str(opposite),
            timeframe="5m",
            formed_at=_iso(observed_at),
            confirmed_at=_iso(observed_at),
            available_at=_iso(observed_at),
            source_metric="research_v2_context",
            age_seconds=0,
            relative_position="ABOVE_REFERENCE" if opposite > reference else "BELOW_REFERENCE",
        ),
    )


def _position_state_for_lifecycle(handoff_payload: Mapping[str, Any]) -> dict[str, Any]:
    return {"position_opportunity_state": {"source_contracts": {"market_handoff": handoff_payload}}}


def _lifecycle_candles(candles: Sequence[HistoricalCandle], *, submitted_at: datetime) -> tuple[HistoricalCandle, ...]:
    return tuple(candle for candle in candles if candle.open_time >= submitted_at)


def _completed_candle(candles: Sequence[HistoricalCandle], cutoff: datetime) -> HistoricalCandle | None:
    for candle in sorted(candles, key=lambda item: item.close_time, reverse=True):
        if candle.completed and candle.close_time <= cutoff:
            return candle
    return None


def _entry_price_from_evidence(direction: V2Direction, reference: Decimal, atr_value: Decimal, tick: Decimal) -> Decimal:
    raw = reference - Decimal("0.10") * atr_value if direction is V2Direction.LONG else reference + Decimal("0.10") * atr_value
    if direction is V2Direction.LONG:
        return (raw / tick).to_integral_value(rounding=ROUND_FLOOR) * tick
    return (raw / tick).to_integral_value(rounding=ROUND_CEILING) * tick


def _order_spec_id(*, job: ResearchV2JobConfig, resolution) -> str:
    digest = canonical_json_digest({"job_id": job.job_id, "set_result_id": resolution.set_result_id, "profile": job.config_fingerprint})
    return f"research-v2-order-{digest[:32]}"


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _optional_time(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    return _parse_time(str(value))


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decimal(value: Any) -> Decimal:
    if value is None:
        raise ResearchV2RunnerError("required decimal value is unavailable")
    return Decimal(str(value))


def _optional_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value))


def _q18_decimal_text(value: Decimal) -> str:
    return q18_export_text(str(value))


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _compact_decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." not in text:
        return text
    stripped = text.rstrip("0").rstrip(".")
    return stripped if stripped not in {"", "-"} else "0"


def load_ordered_jobs() -> list[ResearchV2JobConfig]:
    if not INITIAL_JOBS_PATH.exists():
        raise ResearchV2RunnerError(f"initial jobs spec missing: {INITIAL_JOBS_PATH}")
    spec_rows = json.loads(INITIAL_JOBS_PATH.read_text(encoding="utf-8"))
    ids = [str(row["job_id"]) for row in spec_rows]
    jobs = load_research_v2_jobs()
    missing = [job_id for job_id in ids if job_id not in jobs]
    if missing:
        raise ResearchV2RunnerError(f"job config load missing ids: {missing}")
    return [jobs[job_id] for job_id in ids]


def select_jobs(jobs_arg: str, jobs: Sequence[ResearchV2JobConfig]) -> list[ResearchV2JobConfig]:
    if jobs_arg.strip().upper() == "ALL":
        return list(jobs)
    requested = [item.strip() for item in jobs_arg.split(",") if item.strip()]
    by_id = {job.job_id: job for job in jobs}
    unknown = [job_id for job_id in requested if job_id not in by_id]
    if unknown:
        raise ResearchV2RunnerError(f"unknown Research V2 job id(s): {unknown}")
    return [by_id[job_id] for job_id in requested]


def validate_dataset(dataset_path: Path) -> dict[str, Any]:
    dataset_path = dataset_path.resolve()
    if not dataset_path.exists():
        raise ResearchV2RunnerError(f"dataset manifest missing: {dataset_path}")
    manifest = json.loads(dataset_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "DATA_READY":
        raise ResearchV2RunnerError(f"dataset status is not DATA_READY: {manifest.get('status')}")
    if manifest.get("dataset_id") != EXPECTED_DATASET_ID:
        raise ResearchV2RunnerError(f"unexpected dataset_id: {manifest.get('dataset_id')}")
    validation = manifest.get("validation", {})
    if validation.get("status") != "PASS":
        raise ResearchV2RunnerError(f"dataset validation status is not PASS: {validation.get('status')}")

    root = dataset_path.parent.resolve()
    for record in manifest.get("files", ()):
        local_path = Path(str(record.get("local_path", "")))
        path = (local_path if local_path.is_absolute() else ROOT / local_path).resolve()
        if not path.exists():
            raise ResearchV2RunnerError(f"dataset file missing: {path}")
        expected_hash = record.get("sha256")
        if expected_hash and sha256_file(path) != expected_hash:
            raise ResearchV2RunnerError(f"dataset file hash mismatch: {path}")
        if root not in path.parents and path != root:
            raise ResearchV2RunnerError(f"dataset file is outside dataset package: {path}")

    job_rows = manifest.get("coverage", {}).get("job_readiness", ())
    readiness = {str(row.get("job_id")): row for row in job_rows}
    for job_id in [f"J{idx}" for idx in range(8)]:
        row = readiness.get(job_id)
        if row is None or row.get("overall_status") != "READY":
            raise ResearchV2RunnerError(f"dataset not ready for {job_id}")
    return manifest


def normalize_job_result(result: Mapping[str, Any] | Any, *, job: ResearchV2JobConfig) -> dict[str, Any]:
    payload = asdict(result) if is_dataclass(result) else dict(result)
    normalized = {field: payload.get(field) for field in RESULT_FIELDS}
    normalized["job_id"] = str(normalized.get("job_id") or job.job_id)
    normalized["config_fingerprint"] = str(normalized.get("config_fingerprint") or job.config_fingerprint)
    normalized["status"] = str(normalized.get("status") or "DATA_INVALID")
    normalized["evaluation_start"] = str(normalized.get("evaluation_start") or job.window_start)
    normalized["evaluation_end"] = str(normalized.get("evaluation_end") or job.window_end)
    for field in (
        "unique_signal_episodes",
        "matched",
        "approved",
        "blocked",
        "accepted",
        "filled",
        "closed",
        "censored",
        "open_at_end",
        "pending_at_end",
    ):
        normalized[field] = int(normalized.get(field) or 0)
    for field in (
        "gross_pnl",
        "fees",
        "funding",
        "net_closed_pnl",
        "end_mtm_contribution",
        "account_net",
        "actual_margin_used",
        "actual_notional_turnover",
        "mean_net_notional_expectancy",
        "max_mtm_drawdown",
        "stress_net",
        "leave_best_event_out_net",
    ):
        normalized[field] = decimal_string_or_none(normalized.get(field))
    reasons = normalized.get("data_invalid_reasons") or ()
    normalized["data_invalid_reasons"] = list(reasons) if not isinstance(reasons, str) else [reasons]
    normalized["economic_gate_result"] = evaluate_economic_gate(normalized)
    return normalized


def evaluate_economic_gate(result: Mapping[str, Any]) -> str:
    existing = str(result.get("economic_gate_result") or "")
    if existing in SUPPORTED_ECONOMIC_GATES:
        return existing
    if result.get("data_invalid_reasons") or str(result.get("status")) == "DATA_INVALID":
        return "DATA_INVALID"
    account_net = decimal_value(result.get("account_net"))
    stress_net = decimal_value(result.get("stress_net"))
    leave_best = decimal_value(result.get("leave_best_event_out_net"))
    if account_net >= Decimal("46.666666666666664") and stress_net > 0 and leave_best > 0:
        return "ECONOMIC_PASS"
    if account_net > 0:
        return "MECHANISM_PASS"
    return "FAIL"


def persist_job_result(output_dir: Path, job: ResearchV2JobConfig, result: Mapping[str, Any]) -> None:
    job_dir = output_dir / "jobs" / job.job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    write_json(job_dir / "job_config.json", job.normalized_config())
    write_json(job_dir / "job_result.json", result)


def rebuild_summary(output_dir: Path) -> list[dict[str, Any]]:
    rows = []
    drawdowns = _max_mtm_drawdown_by_job(output_dir)
    for result in read_jsonl(output_dir / "job_results.jsonl"):
        account_net = result["account_net"]
        drawdown = drawdowns.get(str(result["job_id"]))
        row = {
            "job_id": result["job_id"],
            "status": result["status"],
            "account_net_usdt": account_net,
            "account_return_pct": None
            if account_net is None
            else decimal_string(decimal_value(account_net) / Decimal("1000") * Decimal("100")),
            "fills": result["filled"],
            "unique_filled_episodes": result["filled"],
            "closed": result["closed"],
            "censored": result["censored"],
            "notional_turnover": result["actual_notional_turnover"],
            "net_notional_expectancy": result["mean_net_notional_expectancy"],
            "fees": result["fees"],
            "funding": result["funding"],
            "max_mtm_drawdown_pct": drawdown["max_drawdown_pct"] if drawdown is not None else result["max_mtm_drawdown"],
            "stress_net": result["stress_net"],
            "leave_best_event_out_net": result["leave_best_event_out_net"],
            "economic_gate": result["economic_gate_result"],
        }
        rows.append(row)
    rows.sort(key=lambda item: item["job_id"])
    write_json(output_dir / "screen_summary.json", rows)
    write_csv(output_dir / "screen_summary.csv", rows, SUMMARY_FIELDS)
    return rows


def _max_mtm_drawdown_by_job(output_dir: Path) -> dict[str, dict[str, str]]:
    peaks: dict[str, Decimal] = {}
    out: dict[str, dict[str, str]] = {}
    for row in sorted(read_jsonl(output_dir / "factual_mtm_equity_series.jsonl"), key=lambda item: (str(item.get("job_id")), str(item.get("evaluated_at") or item.get("observed_at")))):
        job_id = str(row.get("job_id"))
        equity_text = row.get("current_factual_equity")
        if equity_text is None:
            continue
        equity = _decimal(equity_text)
        peak = max(peaks.get(job_id, equity), equity)
        peaks[job_id] = peak
        drawdown = peak - equity
        if peak == 0:
            pct = Decimal("0")
        else:
            pct = drawdown / peak * Decimal("100")
        previous = out.get(job_id)
        if previous is None or pct > _decimal(previous["max_drawdown_pct"]):
            out[job_id] = {
                "max_drawdown_usdt": str(drawdown),
                "max_drawdown_pct": str(pct),
                "peak_equity": str(peak),
                "trough_equity": str(equity),
                "trough_timestamp": str(row.get("evaluated_at") or row.get("observed_at")),
            }
    return out


def _append_replay_evidence(
    *,
    output_dir: Path,
    context: Mapping[str, Any],
    result: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any],
    lifecycle_index: int | None = None,
) -> None:
    base = {
        "context_id": str(context["context_id"]),
        "job_id": str(context["job_id"]),
        "set_result_id": str(context["record"]["set_result_id"]),
        "observed_at": str(context["observed_at"]),
        "logical_symbol": str(context["record"]["symbol"]),
        "physical_symbol": str(context["record"]["physical_symbol"]),
    }
    if context.get("research_identity"):
        base["research_identity"] = dict(context["research_identity"])
    if lifecycle_index is not None:
        base["lifecycle_index"] = lifecycle_index
    if isinstance(result.get("g0_eligibility_evidence"), Mapping):
        append_jsonl(output_dir / "g0_eligibility_evidence.jsonl", {**base, **dict(result["g0_eligibility_evidence"])})
    if isinstance(result.get("cooldown_evidence"), Mapping):
        append_jsonl(output_dir / "acceptance_cooldown_evidence.jsonl", {**base, **dict(result["cooldown_evidence"])})
    for event in result.get("account_event_ledger", ()) if isinstance(result.get("account_event_ledger"), Sequence) and not isinstance(result.get("account_event_ledger"), (str, bytes)) else ():
        if isinstance(event, Mapping):
            event_payload = dict(event)
            row = {**base, **event_payload}
            if str(event_payload.get("context_id") or "") != str(base["context_id"]):
                row.update(
                    {
                        "trigger_context_id": base["context_id"],
                        "trigger_lifecycle_index": base.get("lifecycle_index"),
                        "trigger_logical_symbol": base["logical_symbol"],
                        "target_context_id": event_payload.get("context_id"),
                        "target_order_spec_id": event_payload.get("order_spec_id"),
                        "target_logical_symbol": event_payload.get("symbol"),
                        "target_physical_symbol": event_payload.get("physical_symbol"),
                        "logical_symbol": event_payload.get("symbol"),
                        "physical_symbol": event_payload.get("physical_symbol"),
                    }
                )
            append_jsonl(output_dir / "account_event_ledger.jsonl", row)
    if result.get("instrument_constraints"):
        append_jsonl(output_dir / "instrument_constraints.jsonl", {**base, **dict(result["instrument_constraints"])})
    lifecycle = result.get("backtest_lifecycle") if isinstance(result.get("backtest_lifecycle"), Mapping) else {}
    evidence = lifecycle.get("evidence") if isinstance(lifecycle.get("evidence"), Mapping) else {}
    intrabar = evidence.get("intrabar_sequence_evidence") if isinstance(evidence.get("intrabar_sequence_evidence"), Mapping) else None
    if intrabar is not None:
        append_jsonl(output_dir / "intrabar_sequence_evidence.jsonl", {**base, **dict(intrabar)})
    if result.get("endpoint_mtm"):
        append_jsonl(output_dir / "endpoint_mtm_evidence.jsonl", {**base, **dict(result["endpoint_mtm"])})
    for row in _funding_boundary_evidence(base=base, result=result, dataset_manifest=dataset_manifest):
        append_jsonl(output_dir / "funding_boundary_evidence.jsonl", row)
    g0 = _g0_reference_evidence(base=base, record=context["record"], result=result, dataset_manifest=dataset_manifest)
    if g0 is not None:
        append_jsonl(output_dir / "g0_reference_evidence.jsonl", g0)
    equity = _equity_guard_evidence(base=base, result=result)
    append_jsonl(output_dir / "equity_guard_evidence.jsonl", equity)
    append_jsonl(output_dir / "factual_mtm_equity_series.jsonl", equity)
    factual_guard = result.get("factual_timeline_guard_evidence")
    if isinstance(factual_guard, Sequence) and not isinstance(factual_guard, (str, bytes)):
        for row in factual_guard:
            if isinstance(row, Mapping):
                append_jsonl(output_dir / "factual_timeline_daily_guard_evidence.jsonl", {**base, **dict(row)})


def _apply_daily_guard_cancellation_overrides(output_dir: Path) -> None:
    ledger_path = output_dir / "account_event_ledger.jsonl"
    ledger = read_jsonl(ledger_path)
    cancellations: dict[str, tuple[datetime, dict[str, Any]]] = {}
    for row in ledger:
        if row.get("event_type") != "ENTRY_CANCELLED_UNFILLED":
            continue
        context_id = str(row.get("context_id") or "")
        timestamp = _optional_time(row.get("timestamp"))
        if not context_id or timestamp is None:
            continue
        current = cancellations.get(context_id)
        if current is None or timestamp < current[0]:
            cancellations[context_id] = (timestamp, row)
    if not cancellations:
        return

    kept_ledger: list[dict[str, Any]] = []
    cancel_event_types = {"ORDER_CANCEL_REQUEST", "ENTRY_CANCELLED_UNFILLED", "RESERVATION_RELEASE"}
    for row in ledger:
        context_id = str(row.get("context_id") or "")
        cancellation = cancellations.get(context_id)
        if cancellation is None:
            kept_ledger.append(row)
            continue
        timestamp = _optional_time(row.get("timestamp"))
        event_type = str(row.get("event_type") or "")
        if event_type == "ORDER_ACCEPTED":
            kept_ledger.append(row)
            continue
        if timestamp is not None and event_type in cancel_event_types and timestamp == cancellation[0]:
            kept_ledger.append(row)
            continue
        if timestamp is not None and timestamp >= cancellation[0]:
            continue
        kept_ledger.append(row)
    _write_jsonl(ledger_path, kept_ledger)

    events_by_context: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in kept_ledger:
        context_id = str(row.get("context_id") or "")
        if context_id:
            events_by_context[context_id].append(row)

    results_path = output_dir / "lifecycle_results.jsonl"
    result_rows = read_jsonl(results_path)
    changed = False
    for row in result_rows:
        result = row.get("result")
        context = row.get("context")
        if not isinstance(result, dict) or not isinstance(context, Mapping):
            continue
        context_id = str(context.get("context_id") or "")
        cancellation = cancellations.get(context_id)
        if cancellation is None:
            continue
        cancel_at, cancel_event = cancellation
        order = result.get("order_spec", {}).get("order_spec") if isinstance(result.get("order_spec"), Mapping) else {}
        order_spec_id = str(order.get("order_spec_id") or cancel_event.get("order_spec_id") or "")
        lifecycle = dict(result.get("backtest_lifecycle") or {})
        evidence = dict(lifecycle.get("evidence") or {})
        evidence.update(
            {
                "accepted": True,
                "accepted_at": evidence.get("accepted_at") or result.get("cooldown_evidence", {}).get("accepted_at"),
                "filled": False,
                "entry_filled_at": None,
                "completed": True,
                "censored": False,
                "status": "ENTRY_CANCELLED_UNFILLED",
                "reason_code": "DAILY_LOSS_PENDING_CANCELLED",
                "closed_result": None,
                "exit_at": None,
                "exit_price": None,
                "exit_reason": None,
                "daily_guard_cancelled": True,
                "cancelled_at": _iso(cancel_at),
                "reservation_release_at": _iso(cancel_at),
                "order_spec_id": order_spec_id or evidence.get("order_spec_id"),
            }
        )
        lifecycle.update(
            {
                "accepted": True,
                "filled": False,
                "completed": True,
                "censored": False,
                "status": "ENTRY_CANCELLED_UNFILLED",
                "reason_code": "DAILY_LOSS_PENDING_CANCELLED",
                "closed_result": None,
                "evidence": evidence,
            }
        )
        result["backtest_lifecycle"] = lifecycle
        result["endpoint_mtm"] = None
        result["state_committed"] = False
        result["reservation_committed"] = True
        result["reservation_released"] = True
        result["reservation_release_at"] = _iso(cancel_at)
        result["daily_guard_cancelled"] = True
        result["account_event_ledger"] = events_by_context.get(context_id, [])
        changed = True
    if changed:
        _write_jsonl(results_path, result_rows)

    for name in (
        "funding_boundary_evidence.jsonl",
        "intrabar_sequence_evidence.jsonl",
        "endpoint_mtm_evidence.jsonl",
    ):
        path = output_dir / name
        rows = read_jsonl(path)
        if rows:
            _write_jsonl(path, [row for row in rows if str(row.get("context_id") or "") not in cancellations])


def _funding_boundary_evidence(
    *,
    base: Mapping[str, Any],
    result: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    order = result.get("order_spec", {}).get("order_spec") if isinstance(result.get("order_spec"), Mapping) else None
    lifecycle = result.get("backtest_lifecycle") if isinstance(result.get("backtest_lifecycle"), Mapping) else {}
    evidence = lifecycle.get("evidence") if isinstance(lifecycle.get("evidence"), Mapping) else {}
    if not isinstance(order, Mapping) or not lifecycle.get("filled"):
        return ()
    opened = _optional_time(evidence.get("entry_filled_at"))
    closed = _optional_time(evidence.get("exit_at"))
    endpoint = None
    if lifecycle.get("status") == "FILLED_OPEN_AT_ENDPOINT":
        endpoint_mtm = result.get("endpoint_mtm") if isinstance(result.get("endpoint_mtm"), Mapping) else {}
        endpoint = _optional_time(endpoint_mtm.get("endpoint_timestamp")) if isinstance(endpoint_mtm, Mapping) else None
    if opened is None or (closed is None and endpoint is None):
        return ()
    physical = str(order.get("physical_symbol") or base["physical_symbol"])
    facts = _canonical_lifecycle_funding_facts(
        _load_dataset_funding_facts(dataset_manifest, physical_symbol=physical),
        dataset_manifest=dataset_manifest,
        mark_cache={},
        physical_symbol=physical,
    )
    events = _funding_events_for_position(
        funding_facts=facts,
        dataset_manifest=dataset_manifest,
        mark_cache={},
        order=order,
        context_id=str(base["context_id"]),
        opened_at=opened,
        closed_at=closed or endpoint,
        include_right_boundary=closed is not None,
    )
    if not events:
        return ({**base, "order_spec_id": order["order_spec_id"], "funding_boundary_crossed": False},)
    return tuple(
        {
            **base,
            **event,
            "applicable_interval_open": _iso(opened),
            "applicable_interval_close": _iso(closed or endpoint),
            "position_held_at_boundary": True,
        }
        for event in events
    )


def _funding_cashflow_for_fact(*, fact: Mapping[str, Any], order: Mapping[str, Any], direction: str, quantity: Decimal) -> Decimal | None:
    if fact.get("signed_funding_amount") is not None:
        return _decimal(fact["signed_funding_amount"])
    rate = fact.get("funding_rate")
    mark = fact.get("mark_price") or fact.get("funding_rate_mark_price") or fact.get("basis_mark_price")
    if rate is None or mark is None:
        return None
    sign = Decimal("-1") if direction == "LONG" else Decimal("1")
    return sign * quantity * _decimal(mark) * _decimal(rate)


def _g0_reference_evidence(
    *,
    base: Mapping[str, Any],
    record: Mapping[str, Any],
    result: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any],
) -> dict[str, Any] | None:
    evidence = record.get("factual_feature_evidence")
    if not isinstance(evidence, Mapping) or evidence.get("structural_reference_price") is None:
        return None
    order = result.get("order_spec", {}).get("order_spec") if isinstance(result.get("order_spec"), Mapping) else None
    if not isinstance(order, Mapping):
        return None
    if str(order.get("stop_loss", {}).get("mode") or "").upper() != "HYBRID_STRUCTURAL":
        return None
    direction = str(evidence.get("signal_direction") or order.get("direction") or "").upper()
    observed_at = _parse_time(str(record["observed_at"]))
    entry = _decimal(order["entry"]["price"])
    physical = str(record["physical_symbol"])
    timeline = _g0_evidence_timeline(dataset_manifest=dataset_manifest, record=record)
    source_bars = _g0_source_5m_bars(timeline=timeline, observed_at=observed_at)
    refs = timeline.swing_low_refs if direction == "LONG" else timeline.swing_high_refs
    selected_price = _decimal(evidence["structural_reference_price"])
    selected_available = _optional_time(evidence.get("structural_reference_available_at"))
    eligible_refs = [
        ref
        for ref in refs
        if ref.available_at <= observed_at
        and observed_at - ref.available_at <= timedelta(minutes=60)
        and ((direction == "LONG" and ref.price < entry) or (direction == "SHORT" and ref.price > entry))
    ]
    eligible_refs = sorted(eligible_refs, key=lambda ref: (ref.available_at, ref.formed_at, ref.price), reverse=True)
    candidates = [_g0_candidate_payload(ref, rank=index + 1, entry=entry, direction=direction, observed_at=observed_at) for index, ref in enumerate(eligible_refs)]
    selected_rank = None
    selected_candidate_id = None
    for candidate in candidates:
        if _decimal(candidate["price"]) != selected_price:
            continue
        if selected_available is not None and _parse_time(candidate["available_at"]) != selected_available:
            continue
        selected_rank = candidate["rank"]
        selected_candidate_id = candidate["candidate_id"]
        break
    return {
        **base,
        "direction": direction,
        "entry_price": str(entry),
        "selected_candidate_id": selected_candidate_id,
        "selected_swing_type": "LOW" if direction == "LONG" else "HIGH",
        "selected_swing_price": evidence.get("structural_reference_price"),
        "formation_time": evidence.get("structural_reference_formed_at"),
        "confirmation_time": evidence.get("structural_reference_confirmed_at"),
        "availability_time": evidence.get("structural_reference_available_at"),
        "age_seconds": evidence.get("structural_reference_age_seconds"),
        "configured_max_age_seconds": 3600,
        "protective_side_eligibility": True,
        "selected_rank": selected_rank,
        "selected_is_rank_1": selected_rank == 1,
        "total_eligible_candidates": len(candidates),
        "ordered_eligible_candidate_list": candidates,
        "source_completed_5m_bars": source_bars,
        "source_completed_5m_bar_count": len(source_bars),
        "candidate_universe_rebuild_rule": "derive swing5 from source_completed_5m_bars using two completed bars left and two completed bars right; eligible candidates must be available_at<=decision, age<=3600s, correct swing type, and protective side of final entry",
        "candidate_witness_complete": selected_rank is not None and bool(candidates),
    }


def _equity_guard_evidence(*, base: Mapping[str, Any], result: Mapping[str, Any]) -> dict[str, Any]:
    evidence = result.get("daily_equity_guard_evidence")
    if isinstance(evidence, Mapping):
        return {**base, **dict(evidence)}
    return {**base, "status": "DAILY_EQUITY_EVIDENCE_UNAVAILABLE"}


def _g0_candidate_payload(
    ref: V2TimelineSwingReference,
    *,
    rank: int,
    entry: Decimal,
    direction: str,
    observed_at: datetime,
) -> dict[str, Any]:
    payload = {
        "kind": ref.kind,
        "price": str(ref.price),
        "formed_at": _iso(ref.formed_at),
        "confirmed_at": _iso(ref.confirmed_at),
        "available_at": _iso(ref.available_at),
        "age_seconds": int((observed_at - ref.available_at).total_seconds()),
        "rank": rank,
        "protective_side_eligible": (direction == "LONG" and ref.price < entry) or (direction == "SHORT" and ref.price > entry),
    }
    payload["candidate_id"] = canonical_json_digest(
        {
            "kind": payload["kind"],
            "price": payload["price"],
            "formed_at": payload["formed_at"],
            "available_at": payload["available_at"],
        }
    )
    return payload


def _g0_evidence_timeline(*, dataset_manifest: Mapping[str, Any], record: Mapping[str, Any]) -> FeatureTimeline:
    physical = str(record["physical_symbol"])
    candle_record = _dataset_file_record(dataset_manifest, physical_symbol=physical, file_type="candles_1m") or {}
    key = (
        str(dataset_manifest.get("dataset_id") or ""),
        str(record["symbol"]),
        physical,
        str(candle_record.get("sha256") or candle_record.get("local_path") or ""),
    )
    cached = _G0_EVIDENCE_TIMELINE_CACHE.get(key)
    if cached is None:
        cached = build_research_v2_feature_timeline(
            symbol=str(record["symbol"]),
            physical_symbol=physical,
            candles=_load_dataset_candles(dataset_manifest, physical_symbol=physical),
        )
        _G0_EVIDENCE_TIMELINE_CACHE[key] = cached
    return cached


def _g0_source_5m_bars(*, timeline: FeatureTimeline, observed_at: datetime) -> list[dict[str, Any]]:
    start = observed_at - timedelta(minutes=90)
    bars = aggregate_completed_bars(timeline.candles, timeframe_minutes=5, cutoff=observed_at)
    out = []
    for bar in bars:
        if bar.close_time < start or bar.close_time > observed_at:
            continue
        out.append(
            {
                "open_time": _iso(bar.open_time),
                "close_time": _iso(bar.close_time),
                "open": str(bar.open),
                "high": str(bar.high),
                "low": str(bar.low),
                "close": str(bar.close),
                "completed": True,
            }
        )
    return out


def _rewrite_account_event_ledger_sorted(output_dir: Path) -> None:
    path = output_dir / "account_event_ledger.jsonl"
    rows = read_jsonl(path)
    if not rows:
        return
    rows.sort(
        key=lambda row: (
            str(row.get("job_id")),
            _parse_time(str(row.get("timestamp"))).timestamp() if row.get("timestamp") else float("inf"),
            _ledger_sequence(row),
            int(row.get("causal_sequence") or 0),
            str(row.get("context_id")),
            str(row.get("event_type")),
            str(row.get("order_spec_id")),
        )
    )
    path.write_text(
        "".join(json.dumps(canonicalize(row), sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _ledger_sequence(row: Mapping[str, Any]) -> int:
    event_type = str(row.get("event_type") or "")
    return _EVENT_ORDER.get(event_type, int(row.get("sequence") or 999))


def _rewrite_factual_timeline_guard_evidence_from_event_ledger(
    output_dir: Path,
    *,
    selected_jobs: Sequence[ResearchV2JobConfig],
    dataset_manifest: Mapping[str, Any],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    path = output_dir / "factual_timeline_daily_guard_evidence.jsonl"
    rows = read_jsonl(path)
    if not rows:
        return {}
    ledger = read_jsonl(output_dir / "account_event_ledger.jsonl")
    if not ledger:
        return {}
    by_job: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in ledger:
        by_job[str(event.get("job_id"))].append(event)
    mark_cache: dict[str, tuple[HistoricalCandle, ...]] = {}
    day_openings: dict[tuple[str, str], Decimal] = {}
    selected_job_ids = {job.job_id for job in selected_jobs}
    rewritten: list[dict[str, Any]] = []
    canonical_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        job_id = str(row.get("job_id") or "")
        if selected_job_ids and job_id not in selected_job_ids:
            rewritten.append(row)
            continue
        timestamp = _optional_time(row.get("evaluated_at"))
        if timestamp is None:
            rewritten.append(row)
            continue
        window = accounting_day_window(timestamp)
        day_key = (job_id, window.accounting_day_id)
        job_events = by_job.get(job_id, ())
        if day_key not in day_openings:
            day_openings[day_key] = _equity_from_ledger_events(
                job_events,
                as_of=_parse_time(window.boundary_start_at),
                dataset_manifest=dataset_manifest,
                mark_cache=mark_cache,
            )["equity"]
        snapshot = _equity_from_ledger_events(
            job_events,
            as_of=timestamp,
            dataset_manifest=dataset_manifest,
            mark_cache=mark_cache,
        )
        day_opening = day_openings[day_key]
        daily_delta = snapshot["equity"] - day_opening
        daily_fraction = Decimal("0") if day_opening == 0 else daily_delta / day_opening
        threshold = -_decimal(row.get("configured_loss_threshold_fraction") or "0.0225")
        mark_unavailable = any(str(position.get("mark_status")) == "MARK_UNAVAILABLE" for position in snapshot["open_positions"])
        decision = "DATA_UNAVAILABLE" if mark_unavailable else ("REJECT" if daily_fraction <= threshold else "PASS")
        rebuilt = dict(row)
        rebuilt.update(
            {
                "day_opening_equity": str(day_opening),
                "realized_gross_pnl_to_date": str(snapshot["realized_gross"]),
                "realized_fees_to_date": str(snapshot["fees"]),
                "realized_funding_to_date": str(snapshot["funding"]),
                "open_positions": snapshot["open_positions"],
                "current_open_position_factual_mtm": str(snapshot["open_mtm"]),
                "current_factual_equity": str(snapshot["equity"]),
                "daily_equity_delta_usdt": str(daily_delta),
                "daily_equity_delta_fraction": str(daily_fraction),
                "daily_equity_delta_pct": str(daily_fraction * Decimal("100")),
                "loss_guard_decision": decision,
                "source_provenance": "account_event_ledger.jsonl",
                "breached": decision == "REJECT",
                "protected_open_position_context_ids": _snapshot_open_position_context_ids(snapshot),
                "protected_open_position_order_spec_ids": _snapshot_open_position_order_spec_ids(snapshot),
            }
        )
        key = _factual_guard_key(rebuilt)
        if key is not None:
            canonical_by_key[key] = dict(rebuilt)
        rewritten.append(rebuilt)
    _write_jsonl(path, rewritten)
    _sync_embedded_factual_timeline_guard_evidence(output_dir, canonical_by_key)
    return canonical_by_key


def _factual_guard_key(row: Mapping[str, Any], *, fallback_context_id: Any = None, fallback_job_id: Any = None) -> tuple[str, str, str] | None:
    job_id = row.get("job_id") or fallback_job_id
    context_id = row.get("context_id") or row.get("trigger_context_id") or fallback_context_id
    evaluated_at = row.get("evaluated_at")
    if not job_id or not context_id or not evaluated_at:
        return None
    return str(job_id), str(context_id), str(evaluated_at)


def _snapshot_open_position_context_ids(snapshot: Mapping[str, Any]) -> list[str]:
    positions = snapshot.get("open_positions") if isinstance(snapshot.get("open_positions"), Sequence) else []
    ids = []
    for position in positions:
        if isinstance(position, Mapping) and position.get("context_id") is not None:
            ids.append(str(position["context_id"]))
    return ids


def _snapshot_open_position_order_spec_ids(snapshot: Mapping[str, Any]) -> list[str]:
    positions = snapshot.get("open_positions") if isinstance(snapshot.get("open_positions"), Sequence) else []
    ids = []
    for position in positions:
        if isinstance(position, Mapping) and position.get("order_spec_id") is not None:
            ids.append(str(position["order_spec_id"]))
    return ids


_FACTUAL_GUARD_SYNC_FIELDS = (
    "day_opening_equity",
    "realized_gross_pnl_to_date",
    "realized_fees_to_date",
    "realized_funding_to_date",
    "open_positions",
    "current_open_position_factual_mtm",
    "current_factual_equity",
    "daily_equity_delta_usdt",
    "daily_equity_delta_fraction",
    "daily_equity_delta_pct",
    "loss_guard_decision",
    "source_provenance",
    "breached",
    "protected_open_position_context_ids",
    "protected_open_position_order_spec_ids",
)


def _sync_embedded_factual_timeline_guard_evidence(
    output_dir: Path,
    canonical_by_key: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> None:
    if not canonical_by_key:
        return
    path = output_dir / "lifecycle_results.jsonl"
    rows = read_jsonl(path)
    if not rows:
        return
    changed = False
    rewritten: list[dict[str, Any]] = []
    for row in rows:
        row_copy = dict(row)
        context = row_copy.get("context") if isinstance(row_copy.get("context"), Mapping) else {}
        result = row_copy.get("result") if isinstance(row_copy.get("result"), Mapping) else None
        if not isinstance(result, Mapping):
            rewritten.append(row_copy)
            continue
        embedded = result.get("factual_timeline_guard_evidence")
        if not isinstance(embedded, list):
            rewritten.append(row_copy)
            continue
        synced_rows: list[Any] = []
        for guard_row in embedded:
            if not isinstance(guard_row, Mapping):
                synced_rows.append(guard_row)
                continue
            key = _factual_guard_key(
                guard_row,
                fallback_context_id=context.get("context_id") or row_copy.get("context_id"),
                fallback_job_id=context.get("job_id") or row_copy.get("job_id"),
            )
            canonical = canonical_by_key.get(key) if key is not None else None
            if canonical is None:
                synced_rows.append(dict(guard_row))
                continue
            synced = dict(guard_row)
            for field in _FACTUAL_GUARD_SYNC_FIELDS:
                if field in canonical:
                    synced[field] = canonical[field]
            if synced != dict(guard_row):
                changed = True
            synced_rows.append(synced)
        result_copy = dict(result)
        result_copy["factual_timeline_guard_evidence"] = synced_rows
        row_copy["result"] = result_copy
        rewritten.append(row_copy)
    if changed:
        _write_jsonl(path, rewritten)


def _reconcile_final_progress_counts(output_dir: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    progress_path = output_dir / "progress.json"
    if not progress_path.exists():
        return
    payload = json.loads(progress_path.read_text(encoding="utf-8"))
    orders_created = 0
    fills = 0
    closed = 0
    for row in rows:
        result = row.get("result") if isinstance(row, Mapping) else None
        if not isinstance(result, Mapping):
            continue
        if result.get("order_spec"):
            orders_created += 1
        lifecycle = result.get("backtest_lifecycle") if isinstance(result.get("backtest_lifecycle"), Mapping) else {}
        if lifecycle.get("filled"):
            fills += 1
        if lifecycle.get("status") == "CLOSED":
            closed += 1
    total = len(rows)
    payload.update(
        {
            "position_evaluations": total,
            "orders_created": orders_created,
            "fills": fills,
            "closed": closed,
            "execution_contexts_done": total,
            "execution_contexts_total": total,
            "phase_units_done": total,
            "phase_units_total": total,
            "global_units_done": total,
            "global_units_total": total,
            "progress_pct": 100.0 if total else payload.get("progress_pct", 0.0),
        }
    )
    write_json(progress_path, payload)


_ECONOMIC_LEDGER_EVENT_TYPES = {
    "ORDER_ACCEPTED",
    "ORDER_CANCEL_REQUEST",
    "ENTRY_CANCELLED_UNFILLED",
    "ENTRY_FILLED",
    "ENTRY_FEE",
    "FUNDING_BOUNDARY",
    "PROTECTIVE_EXIT",
    "EXIT_FEE",
    "FINAL_CLOSE",
    "RESERVATION_RELEASE",
}


def _economic_event_fingerprint(output_dir: Path) -> dict[str, Any]:
    ledger_rows = []
    for row in read_jsonl(output_dir / "account_event_ledger.jsonl"):
        event_type = str(row.get("event_type") or "")
        if event_type not in _ECONOMIC_LEDGER_EVENT_TYPES:
            continue
        ledger_rows.append(
            {
                key: row.get(key)
                for key in (
                    "job_id",
                    "timestamp",
                    "event_type",
                    "context_id",
                    "order_spec_id",
                    "symbol",
                    "physical_symbol",
                    "quantity",
                    "cashflow_amount",
                    "fee_amount",
                    "funding_amount",
                    "realized_gross_pnl",
                    "margin_effect",
                    "reservation_effect",
                    "causal_sequence",
                )
                if key in row
            }
        )
    lifecycle_rows = []
    for row in read_jsonl(output_dir / "lifecycle_results.jsonl"):
        context = row.get("context") if isinstance(row.get("context"), Mapping) else {}
        result = row.get("result") if isinstance(row.get("result"), Mapping) else {}
        lifecycle = result.get("backtest_lifecycle") if isinstance(result.get("backtest_lifecycle"), Mapping) else {}
        closed = lifecycle.get("closed_result") if isinstance(lifecycle.get("closed_result"), Mapping) else None
        endpoint = result.get("endpoint_mtm") if isinstance(result.get("endpoint_mtm"), Mapping) else None
        order_spec = result.get("order_spec") if isinstance(result.get("order_spec"), Mapping) else None
        lifecycle_rows.append(
            {
                "job_id": context.get("job_id") or row.get("job_id"),
                "context_id": context.get("context_id") or row.get("context_id"),
                "accepted": lifecycle.get("accepted"),
                "filled": lifecycle.get("filled"),
                "status": lifecycle.get("status"),
                "reason_code": lifecycle.get("reason_code") or lifecycle.get("reason"),
                "entry_filled_at": lifecycle.get("entry_filled_at"),
                "exit_at": lifecycle.get("exit_at"),
                "entry_price": lifecycle.get("entry_price"),
                "exit_price": lifecycle.get("exit_price"),
                "quantity": lifecycle.get("quantity"),
                "order_spec_id": order_spec.get("order_spec_id") if order_spec else lifecycle.get("order_spec_id"),
                "closed_result": closed,
                "endpoint_mtm": endpoint,
            }
        )
    job_rows = []
    for row in read_jsonl(output_dir / "job_results.jsonl"):
        job_rows.append(
            {
                key: row.get(key)
                for key in (
                    "job_id",
                    "account_net",
                    "net_closed_pnl",
                    "gross_pnl",
                    "fees",
                    "funding",
                    "end_mtm_contribution",
                )
                if key in row
            }
        )
    payload = {
        "account_event_ledger": ledger_rows,
        "lifecycle_results": lifecycle_rows,
        "job_results": job_rows,
    }
    text = json.dumps(canonicalize(payload), sort_keys=True, separators=(",", ":"))
    return {"digest": sha256(text.encode("utf-8")).hexdigest(), "payload": payload}


def _write_factual_mtm_series_from_event_ledger(
    output_dir: Path,
    *,
    selected_jobs: Sequence[ResearchV2JobConfig],
    dataset_manifest: Mapping[str, Any],
) -> None:
    ledger = read_jsonl(output_dir / "account_event_ledger.jsonl")
    if not ledger:
        return
    by_job: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger:
        by_job[str(row.get("job_id"))].append(row)
    mark_cache: dict[str, tuple[HistoricalCandle, ...]] = {}
    rows: list[dict[str, Any]] = []
    for job in selected_jobs:
        job_events = sorted(
            by_job.get(job.job_id, ()),
            key=lambda row: (
                _parse_time(str(row.get("timestamp"))).timestamp() if row.get("timestamp") else float("inf"),
                _ledger_sequence(row),
                int(row.get("causal_sequence") or 0),
                str(row.get("context_id")),
                str(row.get("event_type")),
            ),
        )
        if not job_events:
            continue
        start = _parse_time(job.window_start)
        end = _parse_time(job.window_end)
        timestamps = {start, end}
        timestamps.update(_parse_time(str(row["timestamp"])) for row in job_events if row.get("timestamp"))
        for opened_at, closed_at in _open_position_intervals_from_ledger(job_events, window_end=end):
            minute = opened_at.replace(second=0, microsecond=0)
            if minute < opened_at:
                minute += timedelta(minutes=1)
            while minute <= closed_at:
                timestamps.add(minute)
                minute += timedelta(minutes=1)
        boundary = start.replace(hour=21, minute=0, second=0, microsecond=0)
        if boundary > start:
            boundary -= timedelta(days=1)
        while boundary <= end:
            timestamps.add(boundary)
            boundary += timedelta(days=1)
        day_openings: dict[str, Decimal] = {}
        for timestamp in sorted(timestamps):
            window = accounting_day_window(timestamp, timezone="Asia/Jerusalem")
            day_id = window.accounting_day_id
            boundary_start = _parse_time(window.boundary_start_at)
            if day_id not in day_openings:
                day_openings[day_id] = _equity_from_ledger_events(
                    job_events,
                    as_of=boundary_start,
                    dataset_manifest=dataset_manifest,
                    mark_cache=mark_cache,
                )["equity"]
            snapshot = _equity_from_ledger_events(
                job_events,
                as_of=timestamp,
                dataset_manifest=dataset_manifest,
                mark_cache=mark_cache,
            )
            delta = snapshot["equity"] - day_openings[day_id]
            rows.append(
                {
                    "job_id": job.job_id,
                    "evaluated_at": _iso(timestamp),
                    "timestamp": _iso(timestamp),
                    "series_cadence": "REPLAY_START;ACCOUNTING_DAY_BOUNDARY;ECONOMIC_EVENT;ONE_MINUTE_WHILE_OPEN;ENDPOINT",
                    "accounting_day": day_id,
                    "accounting_day_timezone": window.timezone,
                    "accounting_day_boundary_start": window.boundary_start_at,
                    "day_opening_equity": str(day_openings[day_id]),
                    "realized_gross_pnl_to_date": str(snapshot["realized_gross"]),
                    "realized_fees_to_date": str(snapshot["fees"]),
                    "realized_funding_to_date": str(snapshot["funding"]),
                    "current_open_position_factual_mtm": str(snapshot["open_mtm"]),
                    "open_positions": snapshot["open_positions"],
                    "current_factual_equity": str(snapshot["equity"]),
                    "daily_equity_delta_usdt": str(delta),
                    "daily_equity_delta_fraction": str(Decimal("0") if day_openings[day_id] == 0 else delta / day_openings[day_id]),
                    "mark_source": "FROZEN_MARK_PRICE_1M",
                    "source_provenance": "account_event_ledger.jsonl",
                }
            )
    path = output_dir / "factual_mtm_equity_series.jsonl"
    path.write_text(
        "".join(json.dumps(canonicalize(row), sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_source_authentication_package(output_dir: Path, *, dataset_manifest: Mapping[str, Any]) -> None:
    source_dir = output_dir / "source_authentication" / "original_bytes"
    wanted_symbols = {"AVAXUSDT", "SUIUSDT", "1000PEPEUSDT"}
    wanted_types = {"funding_facts", "mark_price_1m"}
    source_paths: dict[Path, dict[str, Any]] = {}
    for record in dataset_manifest.get("files", ()):
        file_type = str(record.get("type") or "")
        physical = str(record.get("physical_symbol") or record.get("symbol") or "").upper()
        if physical not in wanted_symbols or file_type not in wanted_types:
            continue
        raw_path = record.get("local_path")
        if not raw_path:
            continue
        path = Path(str(raw_path))
        path = path if path.is_absolute() else ROOT / path
        source_paths[path.resolve()] = {
            "source_type": file_type,
            "physical_symbol": physical,
            "source_path": str(path.resolve()),
            "declared_sha256": record.get("sha256"),
            "time_coverage_start": record.get("start") or record.get("window_start") or record.get("from"),
            "time_coverage_end": record.get("end") or record.get("window_end") or record.get("to"),
        }
    for row in read_jsonl(output_dir / "intrabar_sequence_evidence.jsonl"):
        source_file = row.get("source_file")
        if not source_file:
            continue
        path = Path(str(source_file))
        path = path if path.is_absolute() else ROOT / path
        source_paths[path.resolve()] = {
            "source_type": "raw_trades_intrabar_witness",
            "physical_symbol": row.get("physical_symbol") or row.get("source_physical_symbol"),
            "source_path": str(path.resolve()),
            "declared_sha256": row.get("source_hash"),
            "time_coverage_start": row.get("evidence_coverage_start"),
            "time_coverage_end": row.get("evidence_coverage_end"),
        }

    records: list[dict[str, Any]] = []
    available = 0
    not_supplied = 0
    recomputations = 0
    mismatches = 0
    for source_path, meta in sorted(source_paths.items(), key=lambda item: str(item[0])):
        record = dict(meta)
        record["hash_algorithm"] = "SHA256"
        if not source_path.exists():
            record.update({"status": "SOURCE_BYTES_NOT_AVAILABLE_LOCALLY", "packaged_path": None, "recomputed_sha256": None})
            not_supplied += 1
            records.append(record)
            continue
        recomputed = sha256_file(source_path)
        recomputations += 1
        target_name = f"{record.get('physical_symbol') or 'UNKNOWN'}__{record['source_type']}__{source_path.name}"
        target = source_dir / target_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target)
        record["status"] = "SOURCE_BYTES_PACKAGED"
        record["packaged_path"] = str(target.relative_to(output_dir))
        record["recomputed_sha256"] = recomputed
        record["hash_match"] = not record.get("declared_sha256") or str(record["declared_sha256"]) == recomputed
        if not record["hash_match"]:
            mismatches += 1
        available += 1
        records.append(record)
    write_json(
        output_dir / "source_authentication_manifest.json",
        {
            "source_files_original_bytes_available": available,
            "source_files_original_bytes_not_supplied": not_supplied,
            "source_file_hash_recomputations": recomputations,
            "source_file_hash_mismatches": mismatches,
            "sources": records,
        },
    )


def _open_position_intervals_from_ledger(
    events: Sequence[Mapping[str, Any]],
    *,
    window_end: datetime,
) -> tuple[tuple[datetime, datetime], ...]:
    opened: dict[str, datetime] = {}
    intervals: list[tuple[datetime, datetime]] = []
    for row in sorted(
        events,
        key=lambda item: (
            _parse_time(str(item.get("timestamp"))).timestamp() if item.get("timestamp") else float("inf"),
            _ledger_sequence(item),
            int(item.get("causal_sequence") or 0),
            str(item.get("context_id")),
            str(item.get("event_type")),
        ),
    ):
        event_type = str(row.get("event_type") or "")
        order_id = str(row.get("order_spec_id") or row.get("context_id"))
        timestamp = _parse_time(str(row["timestamp"]))
        if event_type == "ENTRY_FILLED":
            opened[order_id] = timestamp
        elif event_type == "FINAL_CLOSE":
            opened_at = opened.pop(order_id, None)
            if opened_at is not None and timestamp >= opened_at:
                intervals.append((opened_at, timestamp))
    for opened_at in opened.values():
        if window_end >= opened_at:
            intervals.append((opened_at, window_end))
    return tuple(intervals)


def _equity_from_ledger_events(
    events: Sequence[Mapping[str, Any]],
    *,
    as_of: datetime,
    dataset_manifest: Mapping[str, Any],
    mark_cache: dict[str, tuple[HistoricalCandle, ...]],
    active_exposures: Sequence[V2ReplayExposure] = (),
) -> dict[str, Any]:
    realized_gross = Decimal("0")
    fees = Decimal("0")
    funding = Decimal("0")
    open_positions: dict[str, dict[str, Any]] = {}
    for row in events:
        payload = row.to_payload() if isinstance(row, V2ReplayAccountEvent) else row
        timestamp = _parse_time(str(payload["timestamp"]))
        if timestamp > as_of:
            continue
        event_type = str(payload.get("event_type"))
        order_id = str(payload.get("order_spec_id") or payload.get("context_id"))
        if event_type == "ENTRY_FILLED":
            provenance = payload.get("source_provenance") if isinstance(payload.get("source_provenance"), Mapping) else {}
            open_positions[order_id] = {
                "order_spec_id": order_id,
                "context_id": payload.get("context_id"),
                "logical_symbol": payload.get("symbol"),
                "physical_symbol": payload.get("physical_symbol"),
                "quantity": _decimal(payload.get("quantity")),
                "direction": str(provenance.get("direction") or "").upper(),
                "entry_price": _decimal(provenance.get("entry_price")),
                "entry_time": timestamp,
            }
        elif event_type == "FINAL_CLOSE":
            realized_gross += _decimal(payload.get("realized_gross_pnl", "0"))
            open_positions.pop(order_id, None)
        elif event_type in {"ENTRY_FEE", "EXIT_FEE"}:
            fees += _decimal(payload.get("fee_amount", "0"))
        elif event_type == "FUNDING_BOUNDARY":
            funding += _decimal(payload.get("funding_amount", "0"))
    represented_context_ids = {str(position.get("context_id")) for position in open_positions.values()}
    for exposure in active_exposures:
        order_id = exposure.context_id
        if order_id in open_positions or exposure.context_id in represented_context_ids:
            continue
        if exposure.opened_at is None or exposure.opened_at > as_of:
            continue
        if exposure.release_at is not None and exposure.release_at <= as_of:
            continue
        if exposure.entry_price is None or exposure.quantity is None:
            continue
        open_positions[order_id] = {
            "order_spec_id": order_id,
            "context_id": exposure.context_id,
            "logical_symbol": exposure.symbol,
            "physical_symbol": exposure.physical_symbol,
            "quantity": exposure.quantity,
            "direction": str(exposure.direction or "").upper(),
            "entry_price": exposure.entry_price,
            "entry_time": exposure.opened_at,
        }
    open_mtm = Decimal("0")
    open_payloads: list[dict[str, Any]] = []
    for position in open_positions.values():
        physical = str(position["physical_symbol"])
        marks = _marks_for_evidence(dataset_manifest=dataset_manifest, mark_cache=mark_cache, physical_symbol=physical)
        mark = _latest_mark_at_or_before(marks, as_of)
        record = _dataset_file_record(dataset_manifest, physical_symbol=physical, file_type="mark_price_1m") or {}
        if mark is None:
            open_payloads.append(
                {
                    **position,
                    "mark_status": "MARK_UNAVAILABLE",
                    "mark_source": "FROZEN_MARK_PRICE_1M",
                    "source_provenance": record.get("local_path"),
                    "source_hash": record.get("sha256"),
                }
            )
            continue
        gross = (
            (mark.close - position["entry_price"]) * position["quantity"]
            if position["direction"] == "LONG"
            else (position["entry_price"] - mark.close) * position["quantity"]
        )
        open_mtm += gross
        open_payloads.append(
            {
                "order_spec_id": position["order_spec_id"],
                "context_id": position["context_id"],
                "logical_symbol": position["logical_symbol"],
                "physical_symbol": physical,
                "direction": position["direction"],
                "quantity": str(position["quantity"]),
                "entry_price": str(position["entry_price"]),
                "entry_time": _iso(position["entry_time"]),
                "mark_price": str(mark.close),
                "mark_close_time": _iso(mark.close_time),
                "mark_source": "FROZEN_MARK_PRICE_1M",
                "source_provenance": record.get("local_path"),
                "source_hash": record.get("sha256"),
                "unrealized_gross_pnl": str(gross),
            }
        )
    equity = Decimal("1000") + realized_gross - fees + funding + open_mtm
    return {
        "realized_gross": realized_gross,
        "fees": fees,
        "funding": funding,
        "open_mtm": open_mtm,
        "open_positions": open_payloads,
        "equity": equity,
    }


def write_run_state(
    output_dir: Path,
    selected_jobs: Sequence[ResearchV2JobConfig],
    *,
    completed_count: int,
    failed_count: int,
) -> None:
    write_json(
        output_dir / "run_state.json",
        {
            "updated_at": now_iso(),
            "selected_jobs": [job.job_id for job in selected_jobs],
            "selected_job_count": len(selected_jobs),
            "completed_count": completed_count,
            "failed_count": failed_count,
        },
    )


def completed_checkpoint_identities(output_dir: Path) -> set[tuple[str, str]]:
    return {(str(row["job_id"]), str(row["config_fingerprint"])) for row in read_jsonl(output_dir / "job_results.jsonl")}


def job_identity(job: ResearchV2JobConfig) -> tuple[str, str]:
    return job.job_id, job.config_fingerprint


def append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(canonicalize(row), sort_keys=True, separators=(",", ":")) + "\n")


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(canonicalize(row), sort_keys=True, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def count_jsonl(path: Path) -> int:
    return len(read_jsonl(path))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(canonicalize(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decimal_value(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    return Decimal(str(value))


def decimal_string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return decimal_string(Decimal(str(value)))


def decimal_string(value: Decimal) -> str:
    return format(value, "f")


def canonicalize(value: Any) -> Any:
    if isinstance(value, Decimal):
        return decimal_string(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]
    return value


def now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
