"""Research orchestration service for backend-owned product state."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import sqlite3
from typing import Any, Callable

from triggertrade.analytics import TradePerformanceFact, compute_futures_performance
from triggertrade.backtest import BacktestPlan, BacktestResult, HistoricalCandle, run_backtest
from triggertrade.config import AppConfig
from triggertrade.market_data import FuturesInstrumentMetadata
from triggertrade.persistence import MessageStore, TradingRulesStore, TriggerSetStore
from triggertrade.persistence.research_store import (
    ResearchBacktestRunRecord,
    ResearchBacktestStatus,
    ResearchDemoRunRecord,
    ResearchDemoStatus,
    ResearchRecord,
    ResearchStore,
    ResearchStoreError,
)
from triggertrade.rules import DirectionMode, TakeProfitMode, TradingRulesVersion


class ResearchServiceError(ValueError):
    pass


@dataclass(frozen=True)
class ResearchDemoIsolation:
    available: bool = False
    reason: str = "research_demo_exchange_isolation_unavailable"
    execution_scope_id: str | None = None
    account_scope: str | None = None


@dataclass(frozen=True)
class ResearchCompareResult:
    available: bool
    reason: str | None
    overlap_period: str | None = None
    research_demo: dict[str, Any] | None = None
    active_benchmark: dict[str, Any] | None = None
    difference: dict[str, Any] | None = None


BacktestRunner = Callable[..., BacktestResult]


class ResearchService:
    def __init__(
        self,
        *,
        store: ResearchStore,
        trigger_set_store: TriggerSetStore,
        trading_rules_store: TradingRulesStore,
        message_store: MessageStore | None = None,
        config: AppConfig | None = None,
        instrument: FuturesInstrumentMetadata | None = None,
        demo_isolation: ResearchDemoIsolation | None = None,
        backtest_runner: BacktestRunner | None = None,
    ) -> None:
        self._store = store
        self._trigger_set_store = trigger_set_store
        self._trading_rules_store = trading_rules_store
        self._message_store = message_store
        self._config = config
        self._instrument = instrument
        self._demo_isolation = demo_isolation or ResearchDemoIsolation()
        self._backtest_runner = backtest_runner or run_backtest

    def create_research(
        self,
        *,
        set_id: str,
        set_version: str,
        rules_version_id: str,
        created_source: str = "service",
        created_at: str | None = None,
    ) -> ResearchRecord:
        trigger_set = self._trigger_set_store.get_set(set_id, set_version)
        if trigger_set is None:
            raise ResearchServiceError("exact trigger set version not found")
        rules = self._exact_rules_version(rules_version_id)
        record, _created = self._store.create_research(
            set_id=trigger_set.set_id,
            set_version=trigger_set.version,
            rules_version_id=rules.rules_version_id,
            rules_display_version=rules.version,
            created_source=created_source,
            created_at=created_at,
        )
        return record

    def run_backtest(
        self,
        *,
        research_id: str,
        plan: BacktestPlan,
        candles: tuple[HistoricalCandle, ...] = (),
        created_at: datetime | None = None,
    ) -> ResearchBacktestRunRecord:
        research = self._required_research(research_id)
        if self._config is None or self._instrument is None or not candles:
            return self._blocked_backtest(
                research,
                plan=plan,
                reason="backend_historical_replay_inputs_unavailable",
                created_at=(created_at or datetime.now(UTC)).isoformat(),
            )
        rules = self._exact_rules_version(research.rules_version_id)
        block_reason = _backtest_block_reason(rules, self._config, plan)
        if block_reason is not None:
            return self._blocked_backtest(
                research,
                plan=plan,
                reason=block_reason,
                created_at=(created_at or datetime.now(UTC)).isoformat(),
            )
        try:
            result = self._backtest_runner(
                config=_config_for_rules(self._config, rules),
                db_path=self._store.path,
                trigger_set_id=research.set_id,
                trigger_set_version=research.set_version,
                plan=plan,
                candles=candles,
                instrument=self._instrument,
            )
        except Exception as exc:  # noqa: BLE001 - persisted failed evidence must stay bounded and public-safe.
            record = self._store.add_backtest_run(
                research_id=research.research_id,
                period_start=plan.research_start.astimezone(UTC).isoformat(),
                period_end=plan.research_end.astimezone(UTC).isoformat(),
                timeframe=plan.timeframe,
                status=ResearchBacktestStatus.FAILED,
                metrics={},
                unavailable_reason=_public_reason(str(exc)),
                created_at=(created_at or datetime.now(UTC)).isoformat(),
            )
            self._message(
                severity="ERROR",
                title="Research backtest failed",
                body="A Research backtest did not complete.",
                entity_type="research",
                entity_id=research.research_id,
                dedupe_key=f"research:{research.research_id}:backtest_failed:{_public_reason(str(exc))}",
            )
            return record
        status = ResearchBacktestStatus.COMPLETED if result.closed_trades > 0 else ResearchBacktestStatus.COMPLETED_NO_TRADES
        record = self._store.add_backtest_run(
            research_id=research.research_id,
            period_start=plan.research_start.astimezone(UTC).isoformat(),
            period_end=plan.research_end.astimezone(UTC).isoformat(),
            timeframe=plan.timeframe,
            status=status,
            engine_run_id=result.backtest_run_id,
            metrics=_backtest_metrics(result),
            created_at=(created_at or datetime.now(UTC)).isoformat(),
        )
        return record

    def select_backtest_run(self, research_id: str, run_id: str) -> ResearchRecord:
        return self._store.select_backtest_run(research_id, run_id)

    def start_demo_run(self, research_id: str, *, created_at: str | None = None) -> ResearchDemoRunRecord:
        research = self._required_research(research_id)
        rules = self._exact_rules_version(research.rules_version_id)
        block_reason = self._demo_block_reason(rules)
        if block_reason is not None:
            return self._blocked_demo(research, reason=block_reason, created_at=created_at)
        now = created_at or datetime.now(UTC).isoformat()
        scope = self._demo_isolation.execution_scope_id or f"research:{research.research_id}"
        record = self._store.add_demo_run(
            research_id=research.research_id,
            status=ResearchDemoStatus.RUNNING,
            started_at=now,
            execution_scope_id=scope,
            account_scope=self._demo_isolation.account_scope or scope,
            created_at=now,
        )
        return record

    def stop_demo_run(self, research_id: str, run_id: str, *, stopped_at: str | None = None) -> ResearchDemoRunRecord:
        return self._store.stop_demo_run(research_id, run_id, stopped_at=stopped_at)

    def select_demo_run(self, research_id: str, run_id: str) -> ResearchRecord:
        record = self._store.select_demo_run(research_id, run_id)
        self._message(
            severity="ATTENTION",
            title="Research decision needed",
            body="A Research Demo run was selected for comparison and decision.",
            entity_type="research",
            entity_id=record.research_id,
            dedupe_key=f"research:{record.research_id}:decision_needed",
        )
        return record

    def archive_research(self, research_id: str) -> ResearchRecord:
        return self._store.archive_research(research_id)

    def request_make_active(self, research_id: str) -> ResearchRecord:
        return self._store.record_make_active_blocked(
            research_id,
            reason="make_active_activation_semantics_unapproved",
        )

    def compare(self, research_id: str) -> ResearchCompareResult:
        research = self._required_research(research_id)
        if not research.selected_demo_run_id:
            return ResearchCompareResult(False, "selected Research Demo run unavailable")
        demo = self._store.get_demo_run(research.research_id, research.selected_demo_run_id)
        if demo is None or demo.status is not ResearchDemoStatus.STOPPED:
            return ResearchCompareResult(False, "selected Research Demo run is not stopped")
        demo_facts = _facts_from_demo_metrics(research, demo)
        if not demo_facts:
            return ResearchCompareResult(False, "selected Research Demo metrics unavailable")
        active_facts = _active_trade_facts(self._store.path, symbol=demo_facts[0].symbol)
        if not active_facts:
            return ResearchCompareResult(False, "active overlapping benchmark unavailable")
        overlap = _overlap_samples(active_facts, demo_facts)
        if overlap is None:
            return ResearchCompareResult(False, "closed-trade periods do not overlap")
        active_sample, demo_sample, overlap_period = overlap
        active_label = _active_set_label(active_sample)
        active_set_id, active_set_version = active_label.split("@", 1)
        active = compute_futures_performance(set_id=active_set_id, version=active_set_version, status="ACTIVE", trades=active_sample, include_direction_breakdown=False)
        demo_metrics = compute_futures_performance(set_id=research.set_id, version=research.set_version, status="RESEARCH_DEMO", trades=demo_sample, include_direction_breakdown=False)
        research_metrics = _metrics_summary(
            closed_trades=demo_metrics.closed_trades,
            net_pnl=demo_metrics.net_pnl,
            expectancy=demo_metrics.expectancy_per_trade,
            fees=demo_metrics.fees,
        )
        active_metrics = _metrics_summary(
            closed_trades=active.closed_trades,
            net_pnl=active.net_pnl,
            expectancy=active.expectancy_per_trade,
            fees=active.fees,
        )
        return ResearchCompareResult(
            True,
            None,
            overlap_period=overlap_period,
            research_demo=research_metrics,
            active_benchmark=active_metrics,
            difference=_difference(research_metrics, active_metrics),
        )

    def _blocked_backtest(
        self,
        research: ResearchRecord,
        *,
        plan: BacktestPlan,
        reason: str,
        created_at: str,
    ) -> ResearchBacktestRunRecord:
        record = self._store.add_backtest_run(
            research_id=research.research_id,
            period_start=plan.research_start.astimezone(UTC).isoformat(),
            period_end=plan.research_end.astimezone(UTC).isoformat(),
            timeframe=plan.timeframe,
            status=ResearchBacktestStatus.FAILED,
            unavailable_reason=reason,
            created_at=created_at,
        )
        self._message(
            severity="WARNING",
            title="Research backtest unavailable",
            body="A Research backtest could not start because required runtime inputs were unavailable.",
            entity_type="research",
            entity_id=research.research_id,
            dedupe_key=f"research:{research.research_id}:backtest_unavailable:{reason}",
        )
        return record

    def _blocked_demo(
        self,
        research: ResearchRecord,
        *,
        reason: str,
        created_at: str | None,
    ) -> ResearchDemoRunRecord:
        record = self._store.add_demo_run(
            research_id=research.research_id,
            status=ResearchDemoStatus.BLOCKED,
            blocked_reason=reason,
            created_at=created_at,
        )
        self._message(
            severity="WARNING",
            title="Research Demo blocked",
            body="Research Demo did not start because isolated Research execution is not available.",
            entity_type="research",
            entity_id=research.research_id,
            dedupe_key=f"research:{research.research_id}:demo_blocked:{reason}",
            metadata={"reason": reason},
        )
        return record

    def _demo_block_reason(self, rules: TradingRulesVersion) -> str | None:
        draft = rules.draft
        if draft.take_profit_mode is TakeProfitMode.DYNAMIC:
            return "dynamic_take_profit_requires_unimplemented_research_demo_runtime"
        if draft.daily_loss_limit_enabled:
            return "research_daily_loss_accounting_isolation_unavailable"
        if not self._demo_isolation.available:
            return self._demo_isolation.reason
        if not self._demo_isolation.execution_scope_id or not self._demo_isolation.account_scope:
            return "research_demo_isolation_scope_unattributed"
        return None

    def _required_research(self, research_id: str) -> ResearchRecord:
        try:
            record = self._store.get_research(research_id)
        except ResearchStoreError as exc:
            raise ResearchServiceError(str(exc)) from exc
        if record is None:
            raise ResearchServiceError("research id not found")
        return record

    def _exact_rules_version(self, rules_version_id: str) -> TradingRulesVersion:
        rules = self._trading_rules_store.get_version(rules_version_id)
        if rules is None or rules.rules_version_id != rules_version_id:
            raise ResearchServiceError("exact trading rules version not found")
        return rules

    def _message(self, **kwargs: Any) -> None:
        if self._message_store is None:
            return
        try:
            self._message_store.create_message(source="research_service", **kwargs)
        except Exception:
            return


def _backtest_metrics(result: BacktestResult) -> dict[str, Any]:
    data = asdict(result)
    data["status"] = result.status.value
    for key in ("net_pnl", "expectancy", "profit_factor", "max_drawdown", "fees", "funding"):
        data[key] = None if data[key] is None else str(data[key])
    return data


def _config_for_rules(config: AppConfig, rules: TradingRulesVersion) -> AppConfig:
    draft = rules.draft
    minimum_net_edge = draft.minimum_net_edge_pct if draft.minimum_net_edge_enabled and draft.minimum_net_edge_pct is not None else Decimal("0")
    max_open_positions = draft.max_open_positions if draft.max_open_positions_enabled and draft.max_open_positions is not None else config.futures_runtime.max_open_positions
    runtime = replace(
        config.futures_runtime,
        version=rules.rules_version_id,
        leverage=draft.leverage,
        position_size_pct_of_available_capital=draft.position_size_pct,
        max_open_positions=max_open_positions,
        take_profit_pct=draft.fixed_take_profit_pct or draft.minimum_take_profit_pct or config.futures_runtime.take_profit_pct,
        stop_loss_pct=draft.stop_loss_pct,
        minimum_risk_reward=draft.minimum_risk_reward,
        minimum_net_edge=minimum_net_edge,
        maker_fee_rate=draft.maker_fee_rate,
        taker_fee_rate=draft.taker_fee_rate,
        spread_cost=draft.spread_cost,
        slippage_cost=draft.slippage_cost,
        funding_cost=draft.funding_cost,
    )
    return replace(config, futures_runtime=runtime)


def _backtest_block_reason(rules: TradingRulesVersion, config: AppConfig, plan: BacktestPlan) -> str | None:
    draft = rules.draft
    if draft.take_profit_mode is TakeProfitMode.DYNAMIC:
        return "dynamic_take_profit_requires_unimplemented_research_backtest_runtime"
    if draft.daily_loss_limit_enabled:
        return "research_daily_loss_accounting_isolation_unavailable"
    if draft.direction_mode is not DirectionMode.LONG_SHORT:
        return "research_backtest_direction_filters_unimplemented"
    enabled = tuple(coin for coin in draft.coins if coin.enabled)
    if not any(coin.symbol == plan.symbol for coin in enabled):
        return "research_backtest_symbol_not_enabled_by_pinned_rules"
    if any(coin.max_allocation_pct is not None for coin in enabled):
        return "research_backtest_coin_allocation_rules_unimplemented"
    if not draft.max_positions_per_coin_enabled or draft.max_positions_per_coin != 1:
        return "research_backtest_position_per_coin_rules_unimplemented"
    if not draft.max_open_positions_enabled or draft.max_open_positions is None or draft.max_open_positions < 1:
        return "research_backtest_max_open_positions_rules_unimplemented"
    configured_cap = config.futures_runtime.max_total_position_notional / Decimal("100")
    if draft.max_capital_in_positions_pct != configured_cap:
        return "research_backtest_aggregate_capital_rules_unimplemented"
    return None


def _facts_from_demo_metrics(research: ResearchRecord, demo: ResearchDemoRunRecord) -> tuple[TradePerformanceFact, ...]:
    rows = demo.metrics.get("closed_trades")
    if not isinstance(rows, list):
        return ()
    facts: list[TradePerformanceFact] = []
    for row in rows[:250]:
        if not isinstance(row, dict):
            continue
        try:
            facts.append(
                TradePerformanceFact(
                    trade_id=str(row["trade_id"]),
                    trigger_set_id=research.set_id,
                    trigger_set_version=research.set_version,
                    symbol=str(row.get("symbol") or "BTCUSDT"),
                    direction=str(row.get("direction") or "LONG"),
                    closed_at=str(row["closed_at"]),
                    net_pnl=Decimal(str(row["net_pnl"])),
                    gross_pnl=Decimal(str(row.get("gross_pnl", row["net_pnl"]))),
                    entry_fee=Decimal(str(row.get("entry_fee", "0"))),
                    exit_fee=Decimal(str(row.get("exit_fee", "0"))),
                    other_fees=Decimal(str(row.get("other_fees", "0"))),
                    funding=Decimal(str(row.get("funding", "0"))),
                    duration_seconds=int(row.get("duration_seconds", 0)),
                    regime_label=row.get("regime_label"),
                    evidence_source="RESEARCH_DEMO",
                )
            )
        except (KeyError, ValueError, ArithmeticError):
            continue
    return tuple(facts)


def _active_trade_facts(db_path, *, symbol: str) -> tuple[TradePerformanceFact, ...]:
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT trade_id, trigger_set_id, trigger_set_version, symbol, direction,
                       closed_at, net_pnl, gross_pnl, entry_fee, exit_fee, other_fees,
                       funding, duration_seconds, regime_label,
                       COALESCE(evidence_source, 'exchange') AS evidence_source
                FROM futures_closed_trades
                WHERE symbol = ?
                  AND UPPER(COALESCE(evidence_source, 'exchange')) IN ('ACTIVE', 'EXCHANGE')
                ORDER BY closed_at, trade_id
                LIMIT 250
                """,
                (symbol,),
            ).fetchall()
    except sqlite3.Error:
        return ()
    return tuple(
        TradePerformanceFact(
            trade_id=row["trade_id"],
            trigger_set_id=row["trigger_set_id"],
            trigger_set_version=row["trigger_set_version"],
            symbol=row["symbol"],
            direction=row["direction"],
            closed_at=row["closed_at"],
            net_pnl=Decimal(row["net_pnl"]),
            gross_pnl=Decimal(row["gross_pnl"]),
            entry_fee=Decimal(row["entry_fee"]),
            exit_fee=Decimal(row["exit_fee"]),
            other_fees=Decimal(row["other_fees"]),
            funding=Decimal(row["funding"]),
            duration_seconds=int(row["duration_seconds"]),
            regime_label=row["regime_label"],
            evidence_source=row["evidence_source"],
        )
        for row in rows
        if row["trigger_set_id"] and row["trigger_set_version"]
    )


def _overlap_samples(
    active_facts: tuple[TradePerformanceFact, ...],
    demo_facts: tuple[TradePerformanceFact, ...],
) -> tuple[tuple[TradePerformanceFact, ...], tuple[TradePerformanceFact, ...], str] | None:
    active_label = _active_set_label(active_facts)
    active_sample_source = tuple(fact for fact in active_facts if f"{fact.trigger_set_id}@{fact.trigger_set_version}" == active_label)
    if not active_sample_source or not demo_facts:
        return None
    overlap_start = max(min(fact.closed_at for fact in active_sample_source), min(fact.closed_at for fact in demo_facts))
    overlap_end = min(max(fact.closed_at for fact in active_sample_source), max(fact.closed_at for fact in demo_facts))
    if overlap_start > overlap_end:
        return None
    active_sample = tuple(fact for fact in active_sample_source if overlap_start <= fact.closed_at <= overlap_end)
    demo_sample = tuple(fact for fact in demo_facts if overlap_start <= fact.closed_at <= overlap_end)
    if not active_sample or not demo_sample:
        return None
    return active_sample, demo_sample, f"{overlap_start} -> {overlap_end}"


def _active_set_label(facts: tuple[TradePerformanceFact, ...]) -> str:
    if not facts:
        return "unavailable@unavailable"
    first = facts[0]
    return f"{first.trigger_set_id}@{first.trigger_set_version}"


def _metrics_summary(
    *,
    closed_trades: int,
    net_pnl: Decimal | None,
    expectancy: Decimal | None,
    fees: Decimal | None,
) -> dict[str, Any]:
    return {
        "closed_trades": closed_trades,
        "net_pnl": None if net_pnl is None else str(net_pnl),
        "expectancy": None if expectancy is None else str(expectancy),
        "fees": None if fees is None else str(fees),
    }


def _difference(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "closed_trades": int(candidate["closed_trades"]) - int(baseline["closed_trades"]),
        "net_pnl": _decimal_diff(candidate.get("net_pnl"), baseline.get("net_pnl")),
        "expectancy": _decimal_diff(candidate.get("expectancy"), baseline.get("expectancy")),
        "fees": _decimal_diff(candidate.get("fees"), baseline.get("fees")),
    }


def _decimal_diff(left: Any, right: Any) -> str | None:
    if left is None or right is None:
        return None
    return str(Decimal(str(left)) - Decimal(str(right)))


def _public_reason(value: str) -> str:
    lowered = value.lower()
    if any(token in lowered for token in ("secret", "api_key", "authorization", "cookie", "token", ".env")):
        return "sanitized_error"
    return " ".join(value.replace("\x00", "").split())[:180] or "unavailable"
