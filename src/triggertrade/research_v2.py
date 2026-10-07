"""Research V2 specification primitives.

This module intentionally contains only Research V2 configuration, causal
feature, signal, geometry, sizing, and output-contract helpers. It does not run
market data ingestion or submit lifecycle work; executable campaigns wire these
objects into the existing canonical Research/Position/Portfolio/Lifecycle path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from enum import StrEnum
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from triggertrade.backtest.models import HistoricalCandle
from triggertrade.canonical_json import canonical_json_digest
from triggertrade.instruments.catalog import FuturesInstrument
from triggertrade.set_engine import (
    Direction,
    DirectionResolutionScope,
    GenericFixedDirectionBinding,
    SetResultResolutionRequest,
    TriggerResult,
    generic_fixed_direction_binding_digest,
    resolve_set_result_without_handoff,
)
from triggertrade.set_scope import SetConfigurationBinding, SetFormationEpoch


RESEARCH_V2_ID = "RESEARCH_V2"
RESEARCH_V2_SPEC_DIR = Path(__file__).resolve().parents[2] / "docs" / "research-v2"
V2_SIGNAL_RET_OR_VERSION = "V2-SIGNAL-RET5-RET15-OR-V1"
V2_SIGNAL_CONTINUATION_VERSION = "V2-SIGNAL-CONTINUATION-V1"
V2_SIGNAL_COMPRESSION_VERSION = "V2-SIGNAL-COMPRESSION-BREAKOUT-V1"
V2_SIGNAL_REVERSAL_VERSION = "V2-SIGNAL-EXHAUSTION-REVERSAL-V1"


class ResearchV2Error(ValueError):
    """Raised when a Research V2 primitive cannot be evaluated faithfully."""


class V2Direction(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


class V2DecisionStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    PASS = "PASS"
    REJECT = "REJECT"
    NONE = "NONE"


@dataclass(frozen=True)
class AggregatedBar:
    symbol: str
    timeframe_minutes: int
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    turnover: Decimal


@dataclass(frozen=True)
class V2Observation:
    metric_ref: str
    status: V2DecisionStatus
    value: Decimal | str | None
    reason: str | None = None
    observed_at: datetime | None = None
    available_at: datetime | None = None


@dataclass(frozen=True)
class SwingReference:
    direction: V2Direction
    price: Decimal
    pivot_time: datetime
    available_at: datetime
    kind: str


@dataclass(frozen=True)
class V2EntryResult:
    direction: V2Direction
    raw_price: Decimal
    price: Decimal
    ttl_minutes: int


@dataclass(frozen=True)
class V2StopResult:
    status: V2DecisionStatus
    family: str
    stop_price: Decimal | None
    raw_stop_price: Decimal | None
    risk_distance: Decimal | None
    reason: str | None = None


@dataclass(frozen=True)
class V2TakeProfitResult:
    status: V2DecisionStatus
    tp_price: Decimal | None
    gross_r: Decimal | None
    conditional_net_fraction: Decimal | None
    reason: str | None = None


@dataclass(frozen=True)
class V2SizingResult:
    status: V2DecisionStatus
    notional: Decimal | None
    margin: Decimal | None
    binding_constraint: str | None
    stop_fraction: Decimal | None
    reason: str | None = None


@dataclass(frozen=True)
class V2SignalResult:
    status: V2DecisionStatus
    direction: V2Direction
    signal_version: str
    reason: str | None = None


@dataclass(frozen=True)
class ResearchV2SetResolution:
    job_id: str
    signal_family: str
    signal_episode_id: str
    symbol: str
    physical_symbol: str
    observed_at: str
    direction: V2Direction
    status: str
    reason_code: str | None
    config_fingerprint: str
    job_config_fingerprint: str
    source_feature_evidence: Mapping[str, Any]
    source_evidence_digest: str
    decision_cycle_id: str | None
    set_result_id: str
    set_config_id: str
    set_config_version: str
    configuration_binding: SetConfigurationBinding
    result_payload: Mapping[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "research_v2_set_resolution": {
                "schema_version": "RESEARCH_V2_SET_RESOLUTION_V1",
                "job_id": self.job_id,
                "signal_family": self.signal_family,
                "signal_episode_id": self.signal_episode_id,
                "symbol": self.symbol,
                "physical_symbol": self.physical_symbol,
                "observed_at": self.observed_at,
                "direction": self.direction.value,
                "status": self.status,
                "reason_code": self.reason_code,
                "config_fingerprint": self.config_fingerprint,
                "job_config_fingerprint": self.job_config_fingerprint,
                "source_feature_evidence": _canonicalize(self.source_feature_evidence),
                "source_evidence_digest": self.source_evidence_digest,
                "decision_cycle_id": self.decision_cycle_id,
                "set_result_id": self.set_result_id,
                "set_config_id": self.set_config_id,
                "set_config_version": self.set_config_version,
                "configuration_binding": self.configuration_binding.to_payload(),
                "canonical_set_result": _canonicalize(self.result_payload),
            }
        }


@dataclass(frozen=True)
class ResearchV2ExecutionProfile:
    job_id: str
    execution_profile_id: str
    config_fingerprint: str
    entry_profile: Mapping[str, Any]
    stop_profile: Mapping[str, Any]
    take_profit_profile: Mapping[str, Any]
    sizing_profile: Mapping[str, Any]
    cost_profile: Mapping[str, Any]
    rules_profile: Mapping[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "research_v2_execution_profile": {
                "schema_version": "RESEARCH_V2_EXECUTION_PROFILE_V1",
                "job_id": self.job_id,
                "execution_profile_id": self.execution_profile_id,
                "config_fingerprint": self.config_fingerprint,
                "entry_profile": _canonicalize(self.entry_profile),
                "stop_profile": _canonicalize(self.stop_profile),
                "take_profit_profile": _canonicalize(self.take_profit_profile),
                "sizing_profile": _canonicalize(self.sizing_profile),
                "cost_profile": _canonicalize(self.cost_profile),
                "rules_profile": _canonicalize(self.rules_profile),
            }
        }


@dataclass(frozen=True)
class ResearchV2JobConfig:
    job_id: str
    dependencies: tuple[str, ...]
    signal_family: str
    entry_profile: str
    stop_family: str
    sizing_profile: str
    leverage: Decimal
    margin_fraction: Decimal
    symbols: tuple[str, ...]
    window_start: str
    window_end: str
    runtime_profile: Mapping[str, Any]
    source: Mapping[str, Any]

    def normalized_config(self) -> dict[str, Any]:
        return {
            "program_id": RESEARCH_V2_ID,
            "job_id": self.job_id,
            "dependencies": list(self.dependencies),
            "signal_family": self.signal_family,
            "entry_profile": self.entry_profile,
            "stop_family": self.stop_family,
            "sizing_profile": self.sizing_profile,
            "leverage": str(self.leverage),
            "margin_fraction": str(self.margin_fraction),
            "symbols": list(self.symbols),
            "window": {
                "start_inclusive": self.window_start,
                "end_exclusive": self.window_end,
            },
            "runtime_profile": _canonicalize(self.runtime_profile),
        }

    @property
    def config_fingerprint(self) -> str:
        return canonical_json_digest(self.normalized_config())

    @property
    def signal_config(self) -> dict[str, Any]:
        return research_v2_signal_config(self)

    @property
    def signal_config_fingerprint(self) -> str:
        return canonical_json_digest(self.signal_config)


@dataclass(frozen=True)
class ResearchV2ScreeningOutput:
    job_id: str
    config_fingerprint: str
    status: str
    evaluation_start: str
    evaluation_end: str
    symbols: tuple[str, ...]
    unique_signal_episodes: int = 0
    matched: int = 0
    approved: int = 0
    blocked: int = 0
    accepted: int = 0
    filled: int = 0
    closed: int = 0
    censored: int = 0
    open_at_end: int = 0
    pending_at_end: int = 0
    gross_pnl: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")
    funding: Decimal = Decimal("0")
    net_closed_pnl: Decimal = Decimal("0")
    end_mtm_contribution: Decimal = Decimal("0")
    account_net: Decimal = Decimal("0")
    actual_margin_used: Decimal = Decimal("0")
    actual_notional_turnover: Decimal = Decimal("0")
    mean_net_notional_expectancy: Decimal | None = None
    max_mtm_drawdown: Decimal | None = None
    stress_net: Decimal | None = None
    leave_best_event_out_net: Decimal | None = None
    data_invalid_reasons: tuple[str, ...] = ()
    economic_gate_result: str = "NOT_EVALUATED"


def load_common_profile(spec_dir: Path = RESEARCH_V2_SPEC_DIR) -> dict[str, Any]:
    return _load_json_decimal(spec_dir / "RESEARCH_V2_COMMON_PROFILE.json")


def load_initial_jobs(spec_dir: Path = RESEARCH_V2_SPEC_DIR) -> tuple[dict[str, Any], ...]:
    return tuple(_load_json_decimal(spec_dir / "jobs" / "INITIAL_7D_JOBS.json"))


def load_research_v2_jobs(spec_dir: Path = RESEARCH_V2_SPEC_DIR) -> dict[str, ResearchV2JobConfig]:
    common = load_common_profile(spec_dir)
    jobs = {}
    for row in load_initial_jobs(spec_dir):
        jobs[str(row["job_id"])] = build_research_v2_job_config(row, common)
    return jobs


def build_research_v2_job_config(job: Mapping[str, Any], common: Mapping[str, Any]) -> ResearchV2JobConfig:
    runtime_profile = _runtime_profile_for_job(job, common)
    window = job["window"]
    return ResearchV2JobConfig(
        job_id=str(job["job_id"]),
        dependencies=tuple(str(item) for item in job.get("dependencies", ())),
        signal_family=str(job["signal_family"]),
        entry_profile=str(job["entry_profile"]),
        stop_family=str(job["stop_family"]),
        sizing_profile=str(job["sizing_profile"]),
        leverage=Decimal(str(job["leverage"])),
        margin_fraction=Decimal(str(job["margin_fraction"])),
        symbols=tuple(str(item) for item in job["symbols"]),
        window_start=str(window["start_inclusive"]),
        window_end=str(window["end_exclusive"]),
        runtime_profile=runtime_profile,
        source=dict(job),
    )


def physical_symbol_for_research_v2(logical_symbol: str, common: Mapping[str, Any] | None = None) -> str:
    profile = common if common is not None else load_common_profile()
    binding = profile.get("physical_binding", {})
    return str(binding.get(logical_symbol, logical_symbol))


def research_v2_signal_config(job: ResearchV2JobConfig) -> dict[str, Any]:
    """Return the Set-owned V2 signal configuration, excluding execution knobs."""

    return {
        "program_id": RESEARCH_V2_ID,
        "contract": "RESEARCH_V2_CANONICAL_SET_V1",
        "signal": _canonicalize(job.runtime_profile["signal"]),
        "symbols": list(job.symbols),
        "window": {
            "start_inclusive": job.window_start,
            "end_exclusive": job.window_end,
        },
    }


def build_research_v2_execution_profile(job: ResearchV2JobConfig) -> ResearchV2ExecutionProfile:
    runtime = job.runtime_profile
    payload = {
        "program_id": RESEARCH_V2_ID,
        "contract": "RESEARCH_V2_EXECUTION_PROFILE_V1",
        "job_id": job.job_id,
        "entry": _canonicalize(runtime.get("entry", {})),
        "stop": _canonicalize(runtime.get("stop", {})),
        "take_profit": _canonicalize(runtime.get("take_profit", {})),
        "sizing": _canonicalize(runtime.get("sizing", {})),
        "costs": _canonicalize(runtime.get("costs", {})),
        "rules": {
            "entry_profile": job.entry_profile,
            "stop_family": job.stop_family,
            "sizing_profile": job.sizing_profile,
            "leverage": str(job.leverage),
            "margin_fraction": str(job.margin_fraction),
            "trading_rules_hint": runtime.get("trading_rules_hint"),
        },
    }
    digest = canonical_json_digest(payload)
    return ResearchV2ExecutionProfile(
        job_id=job.job_id,
        execution_profile_id=f"research-v2-execution-profile-{digest[:32]}",
        config_fingerprint=digest,
        entry_profile=runtime.get("entry", {}),
        stop_profile=runtime.get("stop", {}),
        take_profit_profile=runtime.get("take_profit", {}),
        sizing_profile=runtime.get("sizing", {}),
        cost_profile=runtime.get("costs", {}),
        rules_profile=payload["rules"],
    )


def resolve_research_v2_set_resolution(
    *,
    job: ResearchV2JobConfig,
    symbol: str,
    physical_symbol: str,
    observed_at: datetime | str,
    signal_result: V2SignalResult,
    source_feature_evidence: Mapping[str, Any],
    signal_episode_id: str | None = None,
) -> ResearchV2SetResolution:
    """Resolve a V2 signal episode through the canonical generic Set result contract."""

    observed = _iso(observed_at)
    set_config = job.signal_config
    set_config_digest = canonical_json_digest(set_config)
    signal_family = str(job.runtime_profile["signal"]["family"])
    set_config_id = f"RESEARCH-V2-{signal_family}"
    set_config_version = str(job.runtime_profile["signal"].get("version", "LEGACY-SET"))
    binding = SetConfigurationBinding(
        set_config_id=set_config_id,
        set_config_version=set_config_version,
        set_config_digest=set_config_digest,
        trigger_config_id=f"{set_config_id}-TRIGGER",
        trigger_config_version=set_config_version,
        trigger_config_digest=set_config_digest,
        core_set_config_id=set_config_id,
        core_set_config_version=set_config_version,
        core_set_config_digest=set_config_digest,
    )
    evidence_payload = {
        "schema_version": "RESEARCH_V2_SIGNAL_EVIDENCE_V1",
        "signal_family": signal_family,
        "signal_version": signal_result.signal_version,
        "symbol": symbol.upper(),
        "physical_symbol": physical_symbol.upper(),
        "observed_at": observed,
        "direction": signal_result.direction.value,
        "status": signal_result.status.value,
        "reason": signal_result.reason,
        "features": _canonicalize(source_feature_evidence),
        "set_config_fingerprint": job.signal_config_fingerprint,
    }
    source_digest = canonical_json_digest(evidence_payload)
    episode_id = signal_episode_id or f"v2-signal-episode-{source_digest[:32]}"
    request = _research_v2_set_result_request(
        binding=binding,
        symbol=symbol,
        observed_at=observed,
        signal_result=signal_result,
        source_evidence_digest=source_digest,
        signal_episode_id=episode_id,
    )
    record = resolve_set_result_without_handoff(request)
    return ResearchV2SetResolution(
        job_id=job.job_id,
        signal_family=signal_family,
        signal_episode_id=episode_id,
        symbol=symbol.upper(),
        physical_symbol=physical_symbol.upper(),
        observed_at=observed,
        direction=_v2_direction(record.direction),
        status=record.status.value,
        reason_code=record.reason_code,
        config_fingerprint=job.signal_config_fingerprint,
        job_config_fingerprint=job.config_fingerprint,
        source_feature_evidence=dict(source_feature_evidence),
        source_evidence_digest=source_digest,
        decision_cycle_id=record.decision_cycle_id,
        set_result_id=record.set_result_id,
        set_config_id=set_config_id,
        set_config_version=set_config_version,
        configuration_binding=binding,
        result_payload=record.result_payload,
    )


def pct_points_to_fraction(value: Decimal) -> Decimal:
    return value / Decimal("100")


def fraction_to_pct_points(value: Decimal) -> Decimal:
    return value * Decimal("100")


def aggregate_completed_bars(
    candles: Sequence[HistoricalCandle],
    *,
    timeframe_minutes: int,
    cutoff: datetime | None = None,
) -> tuple[AggregatedBar, ...]:
    if timeframe_minutes <= 0:
        raise ResearchV2Error("timeframe_minutes must be positive")
    eligible = sorted(
        (
            candle
            for candle in candles
            if candle.completed and (cutoff is None or _as_utc(candle.close_time) <= _as_utc(cutoff))
        ),
        key=lambda item: item.open_time,
    )
    if not eligible:
        return ()
    groups: dict[datetime, list[HistoricalCandle]] = {}
    for candle in eligible:
        start = _floor_time(_as_utc(candle.open_time), timeframe_minutes)
        close = start + timedelta(minutes=timeframe_minutes)
        if _as_utc(candle.close_time) > close:
            continue
        groups.setdefault(start, []).append(candle)
    bars: list[AggregatedBar] = []
    for start in sorted(groups):
        rows = sorted(groups[start], key=lambda item: item.open_time)
        expected_close = start + timedelta(minutes=timeframe_minutes)
        if _as_utc(rows[-1].close_time) != expected_close:
            continue
        bars.append(
            AggregatedBar(
                symbol=rows[-1].symbol,
                timeframe_minutes=timeframe_minutes,
                open_time=start,
                close_time=expected_close,
                open=rows[0].open,
                high=max(row.high for row in rows),
                low=min(row.low for row in rows),
                close=rows[-1].close,
                volume=sum((row.volume for row in rows), Decimal("0")),
                turnover=sum((row.turnover for row in rows), Decimal("0")),
            )
        )
    return tuple(bars)


def wilder_atr_series(bars: Sequence[AggregatedBar], *, period: int = 14) -> tuple[tuple[datetime, Decimal], ...]:
    rows = sorted(bars, key=lambda item: item.close_time)
    if len(rows) < period:
        return ()
    true_ranges: list[Decimal] = []
    previous_close: Decimal | None = None
    for bar in rows:
        if previous_close is None:
            tr = bar.high - bar.low
        else:
            tr = max(bar.high - bar.low, abs(bar.high - previous_close), abs(bar.low - previous_close))
        true_ranges.append(tr)
        previous_close = bar.close
    atr = sum(true_ranges[:period], Decimal("0")) / Decimal(period)
    out: list[tuple[datetime, Decimal]] = [(rows[period - 1].close_time, atr)]
    for idx in range(period, len(rows)):
        atr = ((atr * Decimal(period - 1)) + true_ranges[idx]) / Decimal(period)
        out.append((rows[idx].close_time, atr))
    return tuple(out)


def atr15(candles: Sequence[HistoricalCandle], *, cutoff: datetime) -> V2Observation:
    bars = aggregate_completed_bars(candles, timeframe_minutes=15, cutoff=cutoff)
    series = wilder_atr_series(bars, period=14)
    if not series:
        return V2Observation("ATR15", V2DecisionStatus.UNAVAILABLE, None, "INSUFFICIENT_COMPLETED_15M_BARS", cutoff, cutoff)
    observed_at, value = series[-1]
    return V2Observation("ATR15", V2DecisionStatus.AVAILABLE, value, None, observed_at, observed_at)


def return_pct_points(candles: Sequence[HistoricalCandle], *, cutoff: datetime, window_minutes: int) -> V2Observation:
    latest = _completed_candle_closing_at(candles, cutoff)
    reference_time = _as_utc(cutoff) - timedelta(minutes=window_minutes)
    reference = _completed_candle_closing_at(candles, reference_time)
    metric = f"return{window_minutes}"
    if latest is None or reference is None or reference.close == 0:
        return V2Observation(metric, V2DecisionStatus.UNAVAILABLE, None, "MISSING_COMPLETED_WINDOW_CLOSE", cutoff, cutoff)
    value = ((latest.close / reference.close) - Decimal("1")) * Decimal("100")
    return V2Observation(metric, V2DecisionStatus.AVAILABLE, value, None, cutoff, cutoff)


def rvol5(candles: Sequence[HistoricalCandle], *, cutoff: datetime) -> V2Observation:
    bars = aggregate_completed_bars(candles, timeframe_minutes=5, cutoff=cutoff)
    if len(bars) < 21:
        return V2Observation("RVOL5", V2DecisionStatus.UNAVAILABLE, None, "INSUFFICIENT_COMPLETED_5M_BARS", cutoff, cutoff)
    latest = bars[-1]
    preceding = bars[-21:-1]
    mean = sum((bar.turnover for bar in preceding), Decimal("0")) / Decimal("20")
    if mean == 0:
        return V2Observation("RVOL5", V2DecisionStatus.UNAVAILABLE, None, "ZERO_PRECEDING_TURNOVER_MEAN", cutoff, cutoff)
    return V2Observation("RVOL5", V2DecisionStatus.AVAILABLE, latest.turnover / mean, None, latest.close_time, latest.close_time)


def turnover_acceleration(candles: Sequence[HistoricalCandle], *, cutoff: datetime) -> V2Observation:
    bars = aggregate_completed_bars(candles, timeframe_minutes=5, cutoff=cutoff)
    if len(bars) < 2:
        return V2Observation("turnover_acceleration", V2DecisionStatus.UNAVAILABLE, None, "INSUFFICIENT_COMPLETED_5M_BARS", cutoff, cutoff)
    previous = bars[-2]
    latest = bars[-1]
    if previous.turnover == 0:
        return V2Observation("turnover_acceleration", V2DecisionStatus.UNAVAILABLE, None, "ZERO_PREVIOUS_TURNOVER", cutoff, cutoff)
    return V2Observation("turnover_acceleration", V2DecisionStatus.AVAILABLE, latest.turnover / previous.turnover, None, latest.close_time, latest.close_time)


def ema15(candles: Sequence[HistoricalCandle], *, cutoff: datetime, period: int) -> V2Observation:
    bars = aggregate_completed_bars(candles, timeframe_minutes=15, cutoff=cutoff)
    metric = f"EMA{period}_15m"
    if len(bars) < period:
        return V2Observation(metric, V2DecisionStatus.UNAVAILABLE, None, "INSUFFICIENT_COMPLETED_15M_BARS", cutoff, cutoff)
    seed = sum((bar.close for bar in bars[:period]), Decimal("0")) / Decimal(period)
    multiplier = Decimal("2") / Decimal(period + 1)
    ema = seed
    for bar in bars[period:]:
        ema = ((bar.close - ema) * multiplier) + ema
    return V2Observation(metric, V2DecisionStatus.AVAILABLE, ema, None, bars[-1].close_time, bars[-1].close_time)


def confirmed_swing5_references(candles: Sequence[HistoricalCandle], *, cutoff: datetime) -> tuple[SwingReference, ...]:
    bars = aggregate_completed_bars(candles, timeframe_minutes=5, cutoff=cutoff)
    refs: list[SwingReference] = []
    for idx in range(2, len(bars) - 2):
        left = bars[idx - 2:idx]
        pivot = bars[idx]
        right = bars[idx + 1:idx + 3]
        available_at = right[-1].close_time
        if available_at > _as_utc(cutoff):
            continue
        if pivot.low < min(bar.low for bar in left + right):
            refs.append(SwingReference(V2Direction.LONG, pivot.low, pivot.close_time, available_at, "LOW"))
        if pivot.high > max(bar.high for bar in left + right):
            refs.append(SwingReference(V2Direction.SHORT, pivot.high, pivot.close_time, available_at, "HIGH"))
    return tuple(refs)


def latest_protective_swing5(
    candles: Sequence[HistoricalCandle],
    *,
    cutoff: datetime,
    direction: V2Direction,
    entry_price: Decimal,
) -> SwingReference | None:
    candidates = [
        ref
        for ref in confirmed_swing5_references(candles, cutoff=cutoff)
        if ref.direction is direction
        and ((direction is V2Direction.LONG and ref.price < entry_price) or (direction is V2Direction.SHORT and ref.price > entry_price))
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda ref: ref.available_at)


def v2_entry_price(
    *,
    direction: V2Direction,
    last_traded_price: Decimal,
    atr15_value: Decimal,
    tick_size: Decimal,
    ttl_minutes: int = 15,
) -> V2EntryResult:
    offset = Decimal("0.10") * atr15_value
    if direction is V2Direction.LONG:
        raw = last_traded_price - offset
        price = floor_to_step(raw, tick_size)
    elif direction is V2Direction.SHORT:
        raw = last_traded_price + offset
        price = ceil_to_step(raw, tick_size)
    else:
        raise ResearchV2Error("entry direction must be LONG or SHORT")
    return V2EntryResult(direction=direction, raw_price=raw, price=price, ttl_minutes=ttl_minutes)


def v2_stop_g0(
    *,
    direction: V2Direction,
    entry_price: Decimal,
    atr15_value: Decimal,
    reference: SwingReference | None,
    observed_at: datetime,
    tick_size: Decimal,
) -> V2StopResult:
    if reference is None:
        return V2StopResult(V2DecisionStatus.UNAVAILABLE, "G0", None, None, None, "NO_CONFIRMED_SWING_REFERENCE")
    if _as_utc(observed_at) - _as_utc(reference.available_at) > timedelta(minutes=60):
        return V2StopResult(V2DecisionStatus.UNAVAILABLE, "G0", None, None, None, "STALE_CONFIRMED_SWING_REFERENCE")
    if direction is V2Direction.LONG and reference.price >= entry_price:
        return V2StopResult(V2DecisionStatus.REJECT, "G0", None, None, None, "SWING_NOT_PROTECTIVE")
    if direction is V2Direction.SHORT and reference.price <= entry_price:
        return V2StopResult(V2DecisionStatus.REJECT, "G0", None, None, None, "SWING_NOT_PROTECTIVE")

    buffer = Decimal("0.10") * atr15_value
    raw = reference.price - buffer if direction is V2Direction.LONG else reference.price + buffer
    distance = _risk_distance(direction, entry_price, raw)
    min_distance = max(Decimal("0.5") * atr15_value, Decimal("0.0025") * entry_price)
    max_distance = min(Decimal("1.5") * atr15_value, Decimal("0.0125") * entry_price)
    if distance > max_distance:
        return V2StopResult(V2DecisionStatus.REJECT, "G0", None, raw, distance, "STRUCTURAL_STOP_BEYOND_MAX_DISTANCE")
    if distance < min_distance:
        raw = entry_price - min_distance if direction is V2Direction.LONG else entry_price + min_distance
    rounded = ceil_to_step(raw, tick_size) if direction is V2Direction.LONG else floor_to_step(raw, tick_size)
    actual_distance = _risk_distance(direction, entry_price, rounded)
    if actual_distance <= 0:
        return V2StopResult(V2DecisionStatus.REJECT, "G0", rounded, raw, actual_distance, "ROUNDED_STOP_NOT_PROTECTIVE")
    if actual_distance > max_distance:
        return V2StopResult(V2DecisionStatus.REJECT, "G0", rounded, raw, actual_distance, "ROUNDED_STOP_BEYOND_MAX_DISTANCE")
    return V2StopResult(V2DecisionStatus.PASS, "G0", rounded, raw, actual_distance)


def v2_stop_g1(
    *,
    direction: V2Direction,
    entry_price: Decimal,
    atr15_value: Decimal,
    tick_size: Decimal,
) -> V2StopResult:
    floor = Decimal("0.0025") * entry_price
    ceiling = Decimal("0.0125") * entry_price
    distance = min(max(atr15_value, floor), ceiling)
    raw = entry_price - distance if direction is V2Direction.LONG else entry_price + distance
    rounded = ceil_to_step(raw, tick_size) if direction is V2Direction.LONG else floor_to_step(raw, tick_size)
    actual_distance = _risk_distance(direction, entry_price, rounded)
    if actual_distance <= 0:
        return V2StopResult(V2DecisionStatus.REJECT, "G1", rounded, raw, actual_distance, "ROUNDED_STOP_NOT_PROTECTIVE")
    return V2StopResult(V2DecisionStatus.PASS, "G1", rounded, raw, actual_distance)


def v2_take_profit_2r(
    *,
    direction: V2Direction,
    entry_price: Decimal,
    stop_price: Decimal,
    quantity: Decimal,
    tick_size: Decimal,
    maker_entry_fee_fraction: Decimal = Decimal("0.0002"),
    taker_exit_fee_fraction: Decimal = Decimal("0.00055"),
    extra_round_trip_cost_fraction: Decimal = Decimal("0.00025"),
    net_floor_fraction: Decimal = Decimal("0.003"),
) -> V2TakeProfitResult:
    risk = _risk_distance(direction, entry_price, stop_price)
    if risk <= 0:
        return V2TakeProfitResult(V2DecisionStatus.REJECT, None, None, None, "INVALID_RISK_DISTANCE")
    raw = entry_price + (Decimal("2") * risk) if direction is V2Direction.LONG else entry_price - (Decimal("2") * risk)
    tp = ceil_to_step(raw, tick_size) if direction is V2Direction.LONG else floor_to_step(raw, tick_size)
    reward = (tp - entry_price) if direction is V2Direction.LONG else (entry_price - tp)
    gross_r = reward / risk
    notional = entry_price * quantity
    if notional <= 0:
        return V2TakeProfitResult(V2DecisionStatus.REJECT, tp, gross_r, None, "INVALID_ENTRY_NOTIONAL")
    gross = reward * quantity
    costs = notional * (maker_entry_fee_fraction + taker_exit_fee_fraction + extra_round_trip_cost_fraction)
    net_fraction = (gross - costs) / notional
    if net_fraction < net_floor_fraction:
        return V2TakeProfitResult(V2DecisionStatus.REJECT, tp, gross_r, net_fraction, "CONDITIONAL_NET_TP_FLOOR_NOT_MET")
    return V2TakeProfitResult(V2DecisionStatus.PASS, tp, gross_r, net_fraction)


def v2_risk_based_sizing(
    *,
    capital: Decimal,
    entry_price: Decimal,
    stop_price: Decimal,
    leverage: Decimal = Decimal("1"),
    free_margin: Decimal | None = None,
    remaining_coin_margin: Decimal | None = None,
    remaining_gross_exposure: Decimal | None = None,
    remaining_portfolio_stop_risk: Decimal | None = None,
    nominal_margin_fraction: Decimal = Decimal("0.25"),
    risk_per_trade_fraction_max: Decimal = Decimal("0.0075"),
    stress_cost_fraction: Decimal = Decimal("0.0015"),
    minimum_tranche_usdt: Decimal = Decimal("25"),
) -> V2SizingResult:
    if capital <= 0 or entry_price <= 0 or leverage <= 0:
        raise ResearchV2Error("capital, entry_price, and leverage must be positive")
    stop_fraction = abs(entry_price - stop_price) / entry_price
    denominator = stop_fraction + stress_cost_fraction
    if denominator <= 0:
        return V2SizingResult(V2DecisionStatus.REJECT, None, None, None, stop_fraction, "INVALID_STOP_OR_COST_FRACTION")
    candidates: list[tuple[str, Decimal]] = [
        ("nominal_margin", capital * nominal_margin_fraction * leverage),
        ("per_trade_risk", (capital * risk_per_trade_fraction_max) / denominator),
    ]
    if free_margin is not None:
        candidates.append(("free_margin", free_margin * leverage))
    if remaining_coin_margin is not None:
        candidates.append(("coin_margin_cap", remaining_coin_margin * leverage))
    if remaining_gross_exposure is not None:
        candidates.append(("gross_exposure_cap", remaining_gross_exposure))
    if remaining_portfolio_stop_risk is not None:
        candidates.append(("portfolio_stop_risk", remaining_portfolio_stop_risk / denominator))
    binding, notional = min(candidates, key=lambda item: item[1])
    margin = notional / leverage
    if margin < minimum_tranche_usdt:
        return V2SizingResult(V2DecisionStatus.REJECT, notional, margin, binding, stop_fraction, "MINIMUM_TRANCHE_NOT_MET")
    return V2SizingResult(V2DecisionStatus.PASS, notional, margin, binding, stop_fraction)


def ret5_ret15_or_signal(
    *,
    return5_pct_points: Decimal,
    return15_pct_points: Decimal,
    threshold5_pct_points: Decimal = Decimal("0.30"),
    threshold15_pct_points: Decimal = Decimal("0.50"),
) -> V2SignalResult:
    long = return5_pct_points >= threshold5_pct_points or return15_pct_points >= threshold15_pct_points
    short = return5_pct_points <= -threshold5_pct_points or return15_pct_points <= -threshold15_pct_points
    if long and short:
        return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, V2_SIGNAL_RET_OR_VERSION, "SIMULTANEOUS_OPPOSING_CONDITIONS")
    if long:
        return V2SignalResult(V2DecisionStatus.PASS, V2Direction.LONG, V2_SIGNAL_RET_OR_VERSION)
    if short:
        return V2SignalResult(V2DecisionStatus.PASS, V2Direction.SHORT, V2_SIGNAL_RET_OR_VERSION)
    return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, V2_SIGNAL_RET_OR_VERSION, "BELOW_THRESHOLDS")


def ret_or_episode_reset_ready(
    latest_two: Sequence[tuple[Decimal, Decimal]],
    *,
    threshold5_pct_points: Decimal = Decimal("0.30"),
    threshold15_pct_points: Decimal = Decimal("0.50"),
) -> bool:
    if len(latest_two) < 2:
        return False
    return all(abs(r5) < threshold5_pct_points and abs(r15) < threshold15_pct_points for r5, r15 in latest_two[-2:])


def continuation_signal(
    *,
    base: V2SignalResult,
    ema20: Decimal,
    ema50: Decimal,
    return15_pct_points: Decimal,
    rvol5_value: Decimal,
) -> V2SignalResult:
    if base.status is not V2DecisionStatus.PASS:
        return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, V2_SIGNAL_CONTINUATION_VERSION, base.reason)
    if rvol5_value < Decimal("1.2"):
        return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, V2_SIGNAL_CONTINUATION_VERSION, "RVOL5_BELOW_1_2")
    if base.direction is V2Direction.LONG and ema20 > ema50 and return15_pct_points > 0:
        return V2SignalResult(V2DecisionStatus.PASS, V2Direction.LONG, V2_SIGNAL_CONTINUATION_VERSION)
    if base.direction is V2Direction.SHORT and ema20 < ema50 and return15_pct_points < 0:
        return V2SignalResult(V2DecisionStatus.PASS, V2Direction.SHORT, V2_SIGNAL_CONTINUATION_VERSION)
    return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, V2_SIGNAL_CONTINUATION_VERSION, "TREND_FILTER_FAILED")


def compression_breakout_signal(
    *,
    atr15_value: Decimal,
    preceding_atr15_values: Sequence[Decimal],
    close: Decimal,
    prior_range_high: Decimal,
    prior_range_low: Decimal,
    rvol5_value: Decimal,
    turnover_acceleration_value: Decimal,
) -> V2SignalResult:
    if len(preceding_atr15_values) < 96:
        return V2SignalResult(V2DecisionStatus.UNAVAILABLE, V2Direction.NONE, V2_SIGNAL_COMPRESSION_VERSION, "INSUFFICIENT_ATR_MEDIAN_HISTORY")
    median = _median_decimal(preceding_atr15_values[-96:])
    if median <= 0 or atr15_value / median > Decimal("0.80"):
        return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, V2_SIGNAL_COMPRESSION_VERSION, "COMPRESSION_FILTER_FAILED")
    if rvol5_value < Decimal("1.5"):
        return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, V2_SIGNAL_COMPRESSION_VERSION, "RVOL5_BELOW_1_5")
    if turnover_acceleration_value < Decimal("1.2"):
        return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, V2_SIGNAL_COMPRESSION_VERSION, "TURNOVER_ACCELERATION_BELOW_1_2")
    buffer = Decimal("0.10") * atr15_value
    if close > prior_range_high + buffer:
        return V2SignalResult(V2DecisionStatus.PASS, V2Direction.LONG, V2_SIGNAL_COMPRESSION_VERSION)
    if close < prior_range_low - buffer:
        return V2SignalResult(V2DecisionStatus.PASS, V2Direction.SHORT, V2_SIGNAL_COMPRESSION_VERSION)
    return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, V2_SIGNAL_COMPRESSION_VERSION, "BREAKOUT_FILTER_FAILED")


def reversal_signal(
    *,
    return15_pct_points: Decimal,
    latest_close: Decimal,
    high_15m: Decimal,
    low_15m: Decimal,
    atr15_value: Decimal,
    last_two_closes: Sequence[Decimal],
    turnover_acceleration_value: Decimal,
) -> V2SignalResult:
    if len(last_two_closes) < 2:
        return V2SignalResult(V2DecisionStatus.UNAVAILABLE, V2Direction.NONE, V2_SIGNAL_REVERSAL_VERSION, "MISSING_TWO_CLOSE_CONFIRMATION")
    if turnover_acceleration_value > Decimal("1.0"):
        return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, V2_SIGNAL_REVERSAL_VERSION, "TURNOVER_ACCELERATION_ABOVE_1_0")
    falling = last_two_closes[-1] < last_two_closes[-2]
    rising = last_two_closes[-1] > last_two_closes[-2]
    if return15_pct_points >= Decimal("1.0") and latest_close <= high_15m - (Decimal("0.5") * atr15_value) and falling:
        return V2SignalResult(V2DecisionStatus.PASS, V2Direction.SHORT, V2_SIGNAL_REVERSAL_VERSION)
    if return15_pct_points <= Decimal("-1.0") and latest_close >= low_15m + (Decimal("0.5") * atr15_value) and rising:
        return V2SignalResult(V2DecisionStatus.PASS, V2Direction.LONG, V2_SIGNAL_REVERSAL_VERSION)
    return V2SignalResult(V2DecisionStatus.NONE, V2Direction.NONE, V2_SIGNAL_REVERSAL_VERSION, "REVERSAL_CONFIRMATION_FAILED")


def reversal_reset_ready(latest_two_return15_pct_points: Sequence[Decimal]) -> bool:
    if len(latest_two_return15_pct_points) < 2:
        return False
    return all(abs(value) < Decimal("0.50") for value in latest_two_return15_pct_points[-2:])


def research_v2_data_requirements(job: ResearchV2JobConfig) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "screen_window": {"start_inclusive": job.window_start, "end_exclusive": job.window_end},
        "warmup_days": 15,
        "symbols": list(job.symbols),
        "physical_binding": {"PEPEUSDT": "1000PEPEUSDT"},
        "context": ["BTCUSDT"],
        "required_inputs": [
            "historical_1m_candles",
            "raw_trades_for_causal_fills",
            "historical_funding_facts",
            "historical_mark_facts_when_required",
            "instrument_metadata",
        ],
        "missing_input_behavior": "DATA_INVALID",
    }


def screening_output_contract_fields() -> tuple[str, ...]:
    return tuple(ResearchV2ScreeningOutput.__dataclass_fields__.keys())


def floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        raise ResearchV2Error("step must be positive")
    return (value / step).to_integral_value(rounding=ROUND_FLOOR) * step


def ceil_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        raise ResearchV2Error("step must be positive")
    return (value / step).to_integral_value(rounding=ROUND_CEILING) * step


def _runtime_profile_for_job(job: Mapping[str, Any], common: Mapping[str, Any]) -> dict[str, Any]:
    job_id = str(job["job_id"])
    if job_id == "J0":
        return {
            "signal": {"family": "LEGACY_SET", "set_version": "SET-R-003-V2"},
            "entry": {"type": "LEGACY_GEOMETRY", "ttl_minutes": None, "time_in_force": "GTC"},
            "stop": {"family": "LEGACY"},
            "take_profit": {"family": "LEGACY"},
            "sizing": {"family": "LEGACY_TRANCHE", "margin_fraction": "0.05", "approx_tranche_usdt": "50"},
            "trading_rules_hint": "POS001/PR201",
        }
    if job_id == "J1":
        base = _runtime_profile_for_job({**job, "job_id": "J0"}, common)
        base = json.loads(json.dumps(base))
        base["entry"]["ttl_minutes"] = 15
        base["entry"]["time_in_force"] = "GTC_WITH_TTL_CANCEL"
        return base
    profile = {
        "signal": _signal_profile_for_job(job_id),
        "entry": common["entry"],
        "stop": common["stop_G1"] if job_id == "J7" else common["stop_G0"],
        "take_profit": common["take_profit"],
        "sizing": common["capital_risk"],
        "features": common["features"],
        "costs": common["costs"],
        "units_policy": common["units_policy"],
    }
    return dict(profile)


def _signal_profile_for_job(job_id: str) -> dict[str, Any]:
    if job_id == "J2":
        return {"family": "LEGACY_SET", "set_version": "SET-R-003-V2"}
    if job_id == "J3":
        return {"family": "RET5_OR_RET15", "version": V2_SIGNAL_RET_OR_VERSION, "thresholds_pct_points": {"return5": "0.30", "return15": "0.50"}}
    if job_id in {"J4", "J7"}:
        return {
            "family": "MOMENTUM_CONTINUATION",
            "version": V2_SIGNAL_CONTINUATION_VERSION,
            "base": V2_SIGNAL_RET_OR_VERSION,
            "rvol5_min": "1.2",
            "btc_filter": "DISABLED",
        }
    if job_id == "J5":
        return {
            "family": "COMPRESSION_BREAKOUT",
            "version": V2_SIGNAL_COMPRESSION_VERSION,
            "compression_ratio_max": "0.80",
            "rvol5_min": "1.5",
            "turnover_acceleration_min": "1.2",
            "validity_minutes": 15,
        }
    if job_id == "J6":
        return {
            "family": "EXHAUSTION_REVERSAL",
            "version": V2_SIGNAL_REVERSAL_VERSION,
            "impulse_abs_return15_pct_points_min": "1.0",
            "turnover_acceleration_max": "1.0",
            "validity_minutes": 15,
        }
    raise ResearchV2Error(f"unsupported Research V2 job_id: {job_id}")


def _load_json_decimal(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return _iso(value)
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return value


def _research_v2_set_result_request(
    *,
    binding: SetConfigurationBinding,
    symbol: str,
    observed_at: str,
    signal_result: V2SignalResult,
    source_evidence_digest: str,
    signal_episode_id: str,
) -> SetResultResolutionRequest:
    direction = _set_engine_direction(signal_result.direction)
    formation_result = _formation_result(signal_result.status)
    fixed_binding = None
    if formation_result is TriggerResult.TRUE and direction in {Direction.LONG, Direction.SHORT}:
        fixed_binding = GenericFixedDirectionBinding(
            fixed_direction=direction,
            binding_digest=generic_fixed_direction_binding_digest(
                configuration_binding_digest=binding.digest,
                fixed_direction=direction,
            ),
        )
    return SetResultResolutionRequest(
        formation_epoch=SetFormationEpoch(
            symbol=symbol,
            formation_epoch=int(_parse_iso(observed_at).timestamp()),
            open_event_id=signal_episode_id,
            opened_at=observed_at,
            open_payload_digest=source_evidence_digest,
            configuration_binding=binding,
        ),
        direction_scope=DirectionResolutionScope.GENERIC_FIXED,
        formation_result=formation_result,
        evaluation_event_ids=(signal_episode_id,),
        source_evidence_digest=source_evidence_digest,
        fixed_direction_binding=fixed_binding,
        frozen_condition={
            "producer": "RESEARCH_V2_SIGNAL",
            "signal_episode_id": signal_episode_id,
            "observed_at": observed_at,
            "signal_status": signal_result.status.value,
            "signal_direction": signal_result.direction.value,
            "signal_reason": signal_result.reason,
        },
    )


def _formation_result(status: V2DecisionStatus) -> TriggerResult:
    if status is V2DecisionStatus.PASS:
        return TriggerResult.TRUE
    if status is V2DecisionStatus.UNAVAILABLE:
        return TriggerResult.UNAVAILABLE
    return TriggerResult.FALSE


def _set_engine_direction(direction: V2Direction) -> Direction:
    if direction is V2Direction.LONG:
        return Direction.LONG
    if direction is V2Direction.SHORT:
        return Direction.SHORT
    return Direction.NONE


def _v2_direction(direction: Direction) -> V2Direction:
    if direction is Direction.LONG:
        return V2Direction.LONG
    if direction is Direction.SHORT:
        return V2Direction.SHORT
    return V2Direction.NONE


def _iso(value: datetime | str) -> str:
    if isinstance(value, str):
        return value.replace("+00:00", "Z")
    return _as_utc(value).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _floor_time(value: datetime, minutes: int) -> datetime:
    value = _as_utc(value)
    total_minutes = value.hour * 60 + value.minute
    floored = (total_minutes // minutes) * minutes
    return value.replace(hour=floored // 60, minute=floored % 60, second=0, microsecond=0)


def _completed_candle_closing_at(candles: Sequence[HistoricalCandle], close_time: datetime) -> HistoricalCandle | None:
    target = _as_utc(close_time)
    for candle in candles:
        if candle.completed and _as_utc(candle.close_time) == target:
            return candle
    return None


def _risk_distance(direction: V2Direction, entry: Decimal, stop: Decimal) -> Decimal:
    if direction is V2Direction.LONG:
        return entry - stop
    if direction is V2Direction.SHORT:
        return stop - entry
    raise ResearchV2Error("direction must be LONG or SHORT")


def _median_decimal(values: Sequence[Decimal]) -> Decimal:
    ordered = sorted(values)
    if not ordered:
        raise ResearchV2Error("median requires at least one value")
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / Decimal("2")

