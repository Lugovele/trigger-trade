"""Read-only dashboard query model over TriggerTrade SQLite persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
import json
import sqlite3
from typing import Any

from triggertrade.analytics import TradePerformanceFact, compare_baseline, compute_futures_performance
from triggertrade.governance import EvidenceCapability, GovernanceEvidence, GovernancePolicy, evaluate_readiness


@dataclass(frozen=True)
class RuntimeStateView:
    status: str
    trading_mode: str
    market_source: str
    symbol: str
    timeframe: str
    last_processed_candle_id: str | None
    last_processed_candle_open_time: str | None
    last_processed_at: str | None
    db_health: str


@dataclass(frozen=True)
class DecisionView:
    candle_id: str | None
    candle_open_time: str | None
    trigger_rule: str
    trigger_result: str
    signal_type: str
    strategy_result: str
    risk_result: str
    execution_result: str
    reason: str


@dataclass(frozen=True)
class ActivityRow:
    candle_id: str
    time: str
    symbol: str
    candle: str
    trigger_result: str
    strategy_decision: str
    risk_result: str
    execution_status: str


@dataclass(frozen=True)
class PaperTradeRow:
    time: str
    symbol: str
    side: str
    quantity: str
    requested_price: str
    fill_price: str
    status: str
    intent_id: str
    risk_decision_id: str
    execution_id: str


@dataclass(frozen=True)
class TraceView:
    candle_id: str
    lifecycle: dict[str, Any] | None
    trigger: dict[str, Any] | None
    signal: dict[str, Any] | None
    strategy: dict[str, Any] | None
    trade_intent: dict[str, Any] | None
    risk: dict[str, Any] | None
    execution: dict[str, Any] | None
    fills: tuple[dict[str, Any], ...]
    regime: dict[str, Any] | None = None


@dataclass(frozen=True)
class TriggerSetRow:
    set_id: str
    version: str
    purpose: str
    rules_count: int
    created_at: str
    status: str
    symbol: str
    timeframe: str
    rules: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class RuleRow:
    rule_id: str
    name: str
    asset_scope: str
    condition: str
    used_in: str
    version: str
    status: str


@dataclass(frozen=True)
class RuleDetailView:
    rule: dict[str, Any]
    versions: tuple[dict[str, Any], ...]
    used_in_sets: tuple[dict[str, Any], ...]
    recommendations: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class RecommendationRow:
    recommendation_id: str
    created_at: str
    status: str
    title: str
    resulting_test_set: str
    evidence: str


@dataclass(frozen=True)
class RecommendationDetailView:
    recommendation: dict[str, Any]
    linked_set: TriggerSetRow | None
    linked_rules: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class PerformanceRow:
    set_id: str
    version: str
    status: str
    period: str
    candles_processed: int
    signals: int
    candidate_intents: int
    test_executions: int
    unavailable_metrics: str
    closed_trades: int = 0
    win_rate: str = "unavailable"
    expectancy: str = "unavailable"
    profit_factor: str = "unavailable"
    net_pnl: str = "unavailable"
    max_drawdown: str = "unavailable"
    fees: str = "unavailable"
    funding: str = "unavailable"
    fees_gross_profit_pct: str = "unavailable"
    readiness: str = "unavailable"
    recommendation: str = "unavailable"
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class TestSetEvidenceRow:
    set_id: str
    version: str
    status: str
    testing_started_at: str
    age_days: int
    signals_observed: int
    closed_trades_observed: str
    regime_coverage: str
    readiness: str
    recommendation_action: str
    missing_evidence: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    comparison_available: bool
    policy: str


@dataclass(frozen=True)
class FuturesTradeRow:
    time: str
    symbol: str
    category: str
    action: str
    exchange_side: str
    quantity: str
    requested_price: str
    leverage: str
    status: str
    expected_net_edge: str
    intent_id: str
    risk_decision_id: str
    execution_id: str


@dataclass(frozen=True)
class FuturesClosedTradeRow:
    trade_id: str
    opened_at: str
    closed_at: str
    symbol: str
    direction: str
    quantity: str
    leverage: str
    entry_vwap: str
    exit_vwap: str
    gross_pnl: str
    fees: str
    funding: str
    net_pnl: str
    duration_seconds: int
    trigger_set: str
    regime: str
    accounting_version: str
    evidence_source: str
    simulation_model_version: str
    entry_slippage: str
    exit_slippage: str


@dataclass(frozen=True)
class FuturesPositionView:
    state: str
    symbol: str
    direction: str
    quantity: str
    entry: str
    mark: str
    leverage: str
    liquidation: str
    take_profit: str
    stop_loss: str
    notional: str
    unrealized_pnl: str
    trigger_set: str
    regime: str
    opened_at: str
    source: str


@dataclass(frozen=True)
class FuturesEquityRow:
    observed_at: str
    source: str
    wallet_balance: str
    equity: str
    available_margin: str
    used_margin: str
    unrealized_pnl: str
    realized_pnl: str
    drawdown_absolute: str
    drawdown_percent: str
    max_drawdown: str


@dataclass(frozen=True)
class BacktestRunRow:
    run_id: str
    status: str
    created_at: str
    trigger_set: str
    period: str
    stage: str
    simulation_model: str
    closed_trades: str
    net_pnl: str
    expectancy: str
    profit_factor: str
    max_drawdown: str


@dataclass(frozen=True)
class BaselineComparisonRow:
    candidate_set: str
    baseline_set: str
    available: bool
    period: str
    baseline_closed_trades: int
    candidate_closed_trades: int
    baseline_net_pnl: str
    candidate_net_pnl: str
    baseline_expectancy: str
    candidate_expectancy: str
    baseline_fees: str
    candidate_fees: str
    baseline_direction_mix: str
    candidate_direction_mix: str
    reason: str


@dataclass(frozen=True)
class MarketRegimeView:
    context_id: str
    state: str
    rule: str
    symbol: str
    timeframe: str
    observed_at: str
    window_return_pct: str
    normalized_trend: str
    directional_persistence: str
    reason: str


@dataclass(frozen=True)
class RegimeAnalyticsRow:
    regime: str
    signals: int
    closed_trades: int
    net_pnl: str
    expectancy: str
    fees_gross_profit_pct: str
    long_trades: int
    short_trades: int


@dataclass(frozen=True)
class OperatorStateView:
    state: str
    changed_at: str
    source: str
    reason: str


@dataclass(frozen=True)
class PortfolioSnapshotView:
    as_of: str
    source: str
    freshness_state: str
    total_equity: str | None
    available_capital: str | None
    in_positions: str
    realized_pnl_today: str | None
    unrealized_pnl: str | None
    open_positions_count: int
    currency: str = "USDT"
    entries_paused: bool = False
    last_reconciliation_at: str | None = None
    data_warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PortfolioOpenPositionRow:
    position_id: str
    symbol: str
    side: str
    leverage: str
    qty: str
    qty_unit: str
    value: str
    entry_price: str
    current_price: str | None
    price_source: str
    take_profit_pct: str
    take_profit_price: str
    stop_loss_pct: str
    stop_loss_price: str
    unrealized_pnl_pct: str | None
    unrealized_pnl_amount: str | None
    set_id: str | None
    set_version: str | None
    rules_version_id: str | None
    opened_at: str
    age_seconds: int | None
    status: str
    close_action_available: bool


@dataclass(frozen=True)
class PortfolioClosedPositionRow:
    trade_id: str
    position_id: str
    symbol: str
    side: str
    leverage: str
    qty: str
    qty_unit: str
    value: str
    entry_price: str
    exit_price: str
    planned_tp_pct: str
    planned_tp_price: str
    planned_sl_pct: str
    planned_sl_price: str
    realized_pnl_pct: str
    realized_pnl_amount: str
    close_reason: str
    set_id: str | None
    set_version: str | None
    rules_version_id: str | None
    opened_at: str
    closed_at: str
    duration_seconds: int


@dataclass(frozen=True)
class PortfolioClosedSummaryView:
    closed_today_count: int
    realized_pnl_today: str | None
    win_rate_today: str | None


@dataclass(frozen=True)
class PortfolioOpenSummaryView:
    open_count: int
    capital_in_open_positions: str
    unrealized_pnl: str | None


@dataclass(frozen=True)
class OverviewView:
    lane: str
    status: str
    rule_set: str
    rules_count: int
    latest_candle: str
    latest_signal: str
    trades_count: int
    last_execution: str


@dataclass(frozen=True)
class LogRow:
    time: str
    message: str
    status: str


class DashboardReadModel:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def get_latest_runtime_state(self) -> RuntimeStateView:
        if not self.db_path.exists():
            return _empty_runtime_state("missing_db")
        try:
            with self._connect() as conn:
                row = _fetch_optional(
                    conn,
                    """
                    SELECT symbol, timeframe, last_processed_candle_id,
                           last_processed_candle_open_time, last_processed_at,
                           runtime_version
                    FROM runtime_candle_state
                    ORDER BY last_processed_at DESC
                    LIMIT 1
                    """,
                )
        except sqlite3.Error:
            return _empty_runtime_state("db_unavailable")
        if row is None:
            return _empty_runtime_state("empty_db")
        return RuntimeStateView(
            status="UNKNOWN",
            trading_mode="PAPER",
            market_source="Bybit Demo",
            symbol=row["symbol"],
            timeframe=row["timeframe"],
            last_processed_candle_id=row["last_processed_candle_id"],
            last_processed_candle_open_time=row["last_processed_candle_open_time"],
            last_processed_at=row["last_processed_at"],
            db_health="OK",
        )

    def get_latest_decision(self) -> DecisionView:
        rows = self.list_recent_activity(limit=1)
        if not rows:
            return DecisionView(None, None, "TRG-001", "none", "none", "none", "none", "none", "No runtime activity yet.")
        trace = self.get_trace(rows[0].candle_id)
        return _decision_from_trace(trace)

    def list_recent_activity(self, limit: int = 25) -> tuple[ActivityRow, ...]:
        if not self.db_path.exists():
            return ()
        safe_limit = max(1, min(int(limit), 100))
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT l.candle_id, l.symbol, l.timeframe, l.candle_open_time,
                           l.status, l.signal_id, l.intent_id, l.risk_decision_id,
                           l.execution_intent_id, l.processed_at, l.error,
                           t.signal_type, t.condition_result,
                           s.intent_id AS strategy_intent_id,
                           r.approved AS risk_approved, r.blocking_rule_ids,
                           e.status AS execution_status
                    FROM runtime_candle_lifecycles l
                    LEFT JOIN trigger_evaluations t ON t.signal_id = l.signal_id
                    LEFT JOIN strategy_decisions s ON s.intent_id = l.intent_id
                    LEFT JOIN risk_decisions r ON r.risk_decision_id = l.risk_decision_id
                    LEFT JOIN execution_orders e ON e.intent_id = l.execution_intent_id
                    ORDER BY COALESCE(l.processed_at, l.candle_open_time) DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
        except sqlite3.Error:
            return ()
        return tuple(_activity_row(row) for row in rows)

    def list_recent_paper_trades(self, limit: int = 25) -> tuple[PaperTradeRow, ...]:
        if not self.db_path.exists():
            return ()
        safe_limit = max(1, min(int(limit), 100))
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT DISTINCT e.intent_id, e.risk_decision_id, e.client_order_id,
                           e.exchange_order_id, e.symbol, e.side, e.order_type,
                           e.requested_qty, e.requested_price, e.status,
                           e.created_at, e.updated_at, e.exchange_status,
                           e.reconciliation_state,
                           f.price AS fill_price, f.quantity AS fill_quantity,
                           f.created_at AS fill_time
                    FROM runtime_candle_lifecycles l
                    JOIN execution_orders e ON e.intent_id = l.execution_intent_id
                    LEFT JOIN execution_fills f ON f.intent_id = e.intent_id
                    ORDER BY COALESCE(f.created_at, e.updated_at) DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
        except sqlite3.Error:
            return ()
        return tuple(_trade_row(row) for row in rows)

    def get_trace(self, candle_id: str) -> TraceView | None:
        if not candle_id or len(candle_id) > 200 or not self.db_path.exists():
            return None
        try:
            with self._connect() as conn:
                lifecycle = _fetch_optional(
                    conn,
                    """
                    SELECT candle_id, symbol, timeframe, candle_open_time, status,
                           signal_id, intent_id, risk_decision_id,
                           execution_intent_id, processed_at, error,
                           regime_context_id, regime_state
                    FROM runtime_candle_lifecycles
                    WHERE candle_id = ?
                    """,
                    (candle_id,),
                )
                if lifecycle is None:
                    return None
                trigger = None
                if lifecycle["signal_id"]:
                    trigger = _fetch_optional(
                        conn,
                        """
                        SELECT signal_id, trigger_rule_id, trigger_rule_version,
                               symbol, observed_at, window, input_snapshot,
                               condition_result, signal_type
                        FROM trigger_evaluations
                        WHERE signal_id = ?
                        """,
                        (lifecycle["signal_id"],),
                    )
                strategy = None
                if lifecycle["intent_id"]:
                    strategy = _fetch_optional(
                        conn,
                        """
                        SELECT intent_id, strategy_rule_id, strategy_rule_version,
                               symbol, side, signal_ids, trigger_ids, created_at,
                               regime_context_id, regime_rule_id, regime_rule_version,
                               regime_state
                        FROM strategy_decisions
                        WHERE intent_id = ?
                        """,
                        (lifecycle["intent_id"],),
                    )
                risk = None
                if lifecycle["risk_decision_id"]:
                    risk = _fetch_optional(
                        conn,
                        """
                        SELECT risk_decision_id, intent_id, approved,
                               checked_rule_ids, blocking_rule_ids,
                               approved_notional, approved_quantity,
                               rejection_reason, created_at
                        FROM risk_decisions
                        WHERE risk_decision_id = ?
                        """,
                        (lifecycle["risk_decision_id"],),
                    )
                execution = None
                fills: tuple[dict[str, Any], ...] = ()
                if lifecycle["execution_intent_id"]:
                    execution = _fetch_optional(
                        conn,
                        """
                        SELECT intent_id, risk_decision_id, client_order_id,
                               exchange_order_id, symbol, side, order_type,
                               requested_qty, requested_price, status, created_at,
                               updated_at, exchange_status, reconciliation_state,
                               last_error_code
                        FROM execution_orders
                        WHERE intent_id = ?
                        """,
                        (lifecycle["execution_intent_id"],),
                    )
                    fill_rows = conn.execute(
                        """
                        SELECT fill_id, intent_id, client_order_id, symbol, side,
                               quantity, price, fee, created_at
                        FROM execution_fills
                        WHERE intent_id = ?
                        ORDER BY created_at
                        """,
                        (lifecycle["execution_intent_id"],),
                    ).fetchall()
                    fills = tuple(_safe_dict(dict(row)) for row in fill_rows)
        except sqlite3.Error:
            return None
        trigger_view = _decode_json_fields(trigger, {"input_snapshot"})
        strategy_view = _decode_json_fields(strategy, {"signal_ids", "trigger_ids"})
        regime = self._regime_for_context(lifecycle["regime_context_id"]) if lifecycle["regime_context_id"] else None
        return TraceView(
            candle_id=candle_id,
            lifecycle=_safe_dict(dict(lifecycle)),
            trigger=trigger_view,
            signal=_signal_view(trigger_view),
            strategy=strategy_view,
            trade_intent=_trade_intent_view(strategy_view),
            risk=_decode_json_fields(risk, {"checked_rule_ids", "blocking_rule_ids"}),
            execution=_safe_dict(dict(execution)) if execution is not None else None,
            fills=fills,
            regime=regime,
        )

    def get_latest_lane_trace(self, lane: str) -> TraceView | None:
        if not lane or len(lane) > 20 or not self.db_path.exists():
            return None
        try:
            with self._connect() as conn:
                lifecycle = _fetch_optional(
                    conn,
                    """
                    SELECT lane, symbol, timeframe, candle_id, candle_open_time,
                           trigger_set_id, trigger_set_version, status, signal_id,
                           intent_id, risk_decision_id, execution_intent_id,
                           processed_at, error, regime_context_id, regime_state
                    FROM runtime_lane_lifecycles
                    WHERE lane = ?
                    ORDER BY COALESCE(processed_at, candle_open_time) DESC
                    LIMIT 1
                    """,
                    (lane,),
                )
        except sqlite3.Error:
            return None
        if lifecycle is None:
            return None
        return self.get_lane_trace(
            lane=lifecycle["lane"],
            symbol=lifecycle["symbol"],
            timeframe=lifecycle["timeframe"],
            candle_id=lifecycle["candle_id"],
            trigger_set_id=lifecycle["trigger_set_id"],
            trigger_set_version=lifecycle["trigger_set_version"],
        )

    def get_lane_trace(
        self,
        *,
        lane: str,
        symbol: str,
        timeframe: str,
        candle_id: str,
        trigger_set_id: str,
        trigger_set_version: str,
    ) -> TraceView | None:
        values = (lane, symbol, timeframe, candle_id, trigger_set_id, trigger_set_version)
        if any(not value or len(value) > 240 for value in values) or not self.db_path.exists():
            return None
        try:
            with self._connect() as conn:
                lifecycle = _fetch_optional(
                    conn,
                    """
                    SELECT lane, symbol, timeframe, candle_id, candle_open_time,
                           trigger_set_id, trigger_set_version, status, signal_id,
                           intent_id, risk_decision_id, execution_intent_id,
                           processed_at, error, regime_context_id, regime_state
                    FROM runtime_lane_lifecycles
                    WHERE lane = ? AND symbol = ? AND timeframe = ? AND candle_id = ?
                      AND trigger_set_id = ? AND trigger_set_version = ?
                    """,
                    values,
                )
                if lifecycle is None:
                    return None
                trigger = None
                if lifecycle["signal_id"]:
                    trigger = _fetch_optional(
                        conn,
                        """
                        SELECT signal_id, trigger_rule_id, trigger_rule_version,
                               symbol, observed_at, window, input_snapshot,
                               condition_result, signal_type, lane,
                               trigger_set_id, trigger_set_version
                        FROM trigger_evaluations
                        WHERE signal_id = ?
                        """,
                        (lifecycle["signal_id"],),
                    )
                strategy = None
                if lifecycle["intent_id"]:
                    strategy = _fetch_optional(
                        conn,
                        """
                        SELECT intent_id, strategy_rule_id, strategy_rule_version,
                               symbol, side, signal_ids, trigger_ids, created_at,
                               lane, trigger_set_id, trigger_set_version,
                               regime_context_id, regime_rule_id, regime_rule_version,
                               regime_state
                        FROM strategy_decisions
                        WHERE intent_id = ?
                        """,
                        (lifecycle["intent_id"],),
                    )
                risk = None
                if lifecycle["risk_decision_id"]:
                    risk = _fetch_optional(
                        conn,
                        """
                        SELECT risk_decision_id, intent_id, approved,
                               checked_rule_ids, blocking_rule_ids,
                               approved_notional, approved_quantity,
                               rejection_reason, created_at, lane,
                               trigger_set_id, trigger_set_version
                        FROM risk_decisions
                        WHERE risk_decision_id = ?
                        """,
                        (lifecycle["risk_decision_id"],),
                    )
                execution = None
                fills: tuple[dict[str, Any], ...] = ()
                if lifecycle["execution_intent_id"]:
                    execution = _fetch_optional(
                        conn,
                        """
                        SELECT intent_id, risk_decision_id, client_order_id,
                               exchange_order_id, symbol, side, order_type,
                               requested_qty, requested_price, status, created_at,
                               updated_at, exchange_status, reconciliation_state,
                               last_error_code, lane, trigger_set_id, trigger_set_version
                        FROM execution_orders
                        WHERE intent_id = ?
                        """,
                        (lifecycle["execution_intent_id"],),
                    )
                    fill_rows = conn.execute(
                        """
                        SELECT fill_id, intent_id, client_order_id, symbol, side,
                               quantity, price, fee, created_at
                        FROM execution_fills
                        WHERE intent_id = ?
                        ORDER BY created_at
                        """,
                        (lifecycle["execution_intent_id"],),
                    ).fetchall()
                    fills = tuple(_safe_dict(dict(row)) for row in fill_rows)
        except sqlite3.Error:
            return None
        trigger_view = _decode_json_fields(trigger, {"input_snapshot"})
        strategy_view = _decode_json_fields(strategy, {"signal_ids", "trigger_ids"})
        regime = self._regime_for_context(lifecycle["regime_context_id"]) if lifecycle["regime_context_id"] else None
        return TraceView(
            candle_id=candle_id,
            lifecycle=_safe_dict(dict(lifecycle)),
            trigger=trigger_view,
            signal=_signal_view(trigger_view),
            strategy=strategy_view,
            trade_intent=_trade_intent_view(strategy_view),
            risk=_decode_json_fields(risk, {"checked_rule_ids", "blocking_rule_ids"}),
            execution=_safe_dict(dict(execution)) if execution is not None else None,
            fills=fills,
            regime=regime,
        )

    def get_live_overview(self) -> OverviewView:
        return self._overview("ACTIVE")

    def get_test_overview(self) -> OverviewView:
        return self._overview("TEST")

    def list_trigger_sets(self) -> tuple[TriggerSetRow, ...]:
        if not self.db_path.exists():
            return ()
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT s.set_id, s.version, s.purpose, s.status, s.symbol,
                           s.timeframe, s.created_at, COUNT(m.rule_id) AS rules_count
                    FROM trigger_set_versions s
                    LEFT JOIN trigger_set_memberships m
                      ON m.set_id = s.set_id AND m.set_version = s.version
                    GROUP BY s.set_id, s.version, s.purpose, s.status, s.symbol,
                             s.timeframe, s.created_at
                    ORDER BY s.created_at DESC, s.set_id, s.version
                    """
                ).fetchall()
        except sqlite3.Error:
            return _legacy_trigger_sets()
        return tuple(
            TriggerSetRow(
                set_id=row["set_id"],
                version=row["version"],
                purpose=row["purpose"],
                rules_count=int(row["rules_count"]),
                created_at=row["created_at"],
                status=row["status"],
                symbol=row["symbol"],
                timeframe=row["timeframe"],
                rules=self._rules_for_set(row["set_id"], row["version"]),
            )
            for row in rows
        )

    def list_rules(self) -> tuple[RuleRow, ...]:
        if not self.db_path.exists():
            return ()
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT r.rule_id, r.version, r.name, r.status, r.asset_scope,
                           r.condition,
                           GROUP_CONCAT(m.set_version, ', ') AS used_in
                    FROM rule_definitions r
                    LEFT JOIN trigger_set_memberships m
                      ON m.rule_id = r.rule_id AND m.rule_version = r.version
                    GROUP BY r.rule_id, r.version, r.name, r.status, r.asset_scope,
                             r.condition
                    ORDER BY r.rule_id, r.version
                    """
                ).fetchall()
        except sqlite3.Error:
            return ()
        return tuple(
            RuleRow(
                rule_id=row["rule_id"],
                version=row["version"],
                name=row["name"],
                status=row["status"],
                asset_scope=row["asset_scope"],
                condition=row["condition"],
                used_in=row["used_in"] or "-",
            )
            for row in rows
        )

    def get_trigger_set(self, set_id: str, version: str) -> TriggerSetRow | None:
        return next((item for item in self.list_trigger_sets() if item.set_id == set_id and item.version == version), None)

    def get_rule_detail(self, rule_id: str, version: str | None = None) -> RuleDetailView | None:
        if not rule_id or len(rule_id) > 80 or (version is not None and len(version) > 40) or not self.db_path.exists():
            return None
        try:
            with self._connect() as conn:
                if version is None:
                    rule = _fetch_optional(
                        conn,
                        """
                        SELECT rule_id, version, name, status, asset_scope, rule_type,
                               condition, definition, created_at, updated_at, provenance
                        FROM rule_definitions
                        WHERE rule_id = ?
                        ORDER BY created_at DESC, version DESC
                        LIMIT 1
                        """,
                        (rule_id,),
                    )
                else:
                    rule = _fetch_optional(
                        conn,
                        """
                        SELECT rule_id, version, name, status, asset_scope, rule_type,
                               condition, definition, created_at, updated_at, provenance
                        FROM rule_definitions
                        WHERE rule_id = ? AND version = ?
                        """,
                        (rule_id, version),
                    )
                if rule is None:
                    return None
                versions = conn.execute(
                    """
                    SELECT rule_id, version, name, status, condition, definition,
                           created_at, updated_at, provenance
                    FROM rule_definitions
                    WHERE rule_id = ?
                    ORDER BY created_at DESC, version DESC
                    """,
                    (rule_id,),
                ).fetchall()
                used = conn.execute(
                    """
                    SELECT s.set_id, s.version, s.status, s.purpose, s.symbol, s.timeframe,
                           m.rule_version
                    FROM trigger_set_memberships m
                    JOIN trigger_set_versions s
                      ON s.set_id = m.set_id AND s.version = m.set_version
                    WHERE m.rule_id = ? AND m.rule_version = ?
                    ORDER BY s.created_at DESC, s.set_id, s.version
                    """,
                    (rule["rule_id"], rule["version"]),
                ).fetchall()
                recs = _recommendations_for_rule(conn, rule["rule_id"], rule["version"])
        except sqlite3.Error:
            return None
        return RuleDetailView(
            rule=_decode_rule_row(rule),
            versions=tuple(_decode_rule_row(row) for row in versions),
            used_in_sets=tuple(_safe_dict(dict(row)) for row in used),
            recommendations=recs,
        )

    def list_recommendations(self) -> tuple[RecommendationRow, ...]:
        if not self.db_path.exists():
            return ()
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT recommendation_id, status, created_at, title, payload FROM recommendations ORDER BY created_at DESC, recommendation_id"
                ).fetchall()
        except sqlite3.Error:
            return ()
        return tuple(_recommendation_row(row) for row in rows)

    def get_recommendation(self, recommendation_id: str) -> RecommendationDetailView | None:
        if not recommendation_id or len(recommendation_id) > 120 or not self.db_path.exists():
            return None
        try:
            with self._connect() as conn:
                row = _fetch_optional(
                    conn,
                    "SELECT recommendation_id, status, created_at, title, payload FROM recommendations WHERE recommendation_id = ?",
                    (recommendation_id,),
                )
                if row is None:
                    return None
                data = _json_value(row["payload"])
                data["status"] = row["status"]
                linked_set = None
                set_id = data.get("resulting_test_set_id")
                set_version = data.get("resulting_test_set_version")
                if set_id and set_version:
                    set_row = _fetch_optional(
                        conn,
                        """
                        SELECT s.set_id, s.version, s.purpose, s.status, s.symbol,
                               s.timeframe, s.created_at, COUNT(m.rule_id) AS rules_count
                        FROM trigger_set_versions s
                        LEFT JOIN trigger_set_memberships m
                          ON m.set_id = s.set_id AND m.set_version = s.version
                        WHERE s.set_id = ? AND s.version = ?
                        GROUP BY s.set_id, s.version, s.purpose, s.status, s.symbol,
                                 s.timeframe, s.created_at
                        """,
                        (set_id, set_version),
                    )
                    if set_row is not None:
                        linked_set = TriggerSetRow(
                            set_id=set_row["set_id"], version=set_row["version"], purpose=set_row["purpose"],
                            rules_count=int(set_row["rules_count"]), created_at=set_row["created_at"],
                            status=set_row["status"], symbol=set_row["symbol"], timeframe=set_row["timeframe"],
                            rules=(),
                        )
                linked_rules = tuple(
                    _decode_rule_row(rule)
                    for rule_id, version in data.get("source_rule_versions", [])
                    for rule in [_fetch_optional(
                        conn,
                        """
                        SELECT rule_id, version, name, status, asset_scope, rule_type,
                               condition, definition, created_at, updated_at, provenance
                        FROM rule_definitions WHERE rule_id = ? AND version = ?
                        """,
                        (rule_id, version),
                    )]
                    if rule is not None
                )
        except sqlite3.Error:
            return None
        return RecommendationDetailView(recommendation=_safe_dict(data), linked_set=linked_set, linked_rules=linked_rules)

    def list_set_performance(self) -> tuple[PerformanceRow, ...]:
        sets = self.list_trigger_sets()
        if not sets or not self.db_path.exists():
            return ()
        readiness_by_set = {f"{row.set_id}@{row.version}": row for row in self.list_test_set_evidence()}
        rows: list[PerformanceRow] = []
        with self._connect() as conn:
            for trigger_set in sets:
                try:
                    counts = _fetch_optional(
                        conn,
                        """
                        SELECT COUNT(*) AS candles,
                               SUM(CASE WHEN t.signal_type IS NOT NULL AND t.signal_type != 'NO_SIGNAL' THEN 1 ELSE 0 END) AS signals,
                               SUM(CASE WHEN l.intent_id IS NOT NULL THEN 1 ELSE 0 END) AS intents,
                               SUM(CASE WHEN l.status = 'test_recorded' THEN 1 ELSE 0 END) AS test_executions,
                               MIN(l.candle_open_time) AS start_time,
                               MAX(l.candle_open_time) AS end_time
                        FROM runtime_lane_lifecycles l
                        LEFT JOIN trigger_evaluations t ON t.signal_id = l.signal_id
                        WHERE l.trigger_set_id = ? AND l.trigger_set_version = ?
                        """,
                        (trigger_set.set_id, trigger_set.version),
                    )
                except sqlite3.Error:
                    try:
                        counts = _fetch_optional(
                            conn,
                            """
                            SELECT COUNT(*) AS candles,
                                   0 AS signals,
                                   SUM(CASE WHEN intent_id IS NOT NULL THEN 1 ELSE 0 END) AS intents,
                                   SUM(CASE WHEN status = 'test_recorded' THEN 1 ELSE 0 END) AS test_executions,
                                   MIN(candle_open_time) AS start_time,
                                   MAX(candle_open_time) AS end_time
                            FROM runtime_lane_lifecycles
                            WHERE trigger_set_id = ? AND trigger_set_version = ?
                            """,
                            (trigger_set.set_id, trigger_set.version),
                        )
                    except sqlite3.Error:
                        counts = None
                period = "unavailable"
                if counts is not None and counts["start_time"] and counts["end_time"]:
                    period = f"{counts['start_time']} -> {counts['end_time']}"
                facts = _accounting_trade_facts(conn, trigger_set.set_id, trigger_set.version)
                if counts is None and not facts:
                    continue
                candles = int(counts["candles"] or 0) if counts is not None else 0
                signals = int(counts["signals"] or 0) if counts is not None else 0
                intents = int(counts["intents"] or 0) if counts is not None else 0
                test_executions = int(counts["test_executions"] or 0) if counts is not None else 0
                if candles == 0 and not facts:
                    continue
                metrics = (
                    compute_futures_performance(
                        set_id=trigger_set.set_id,
                        version=trigger_set.version,
                        status=trigger_set.status,
                        trades=facts,
                        max_drawdown=None,
                    )
                    if facts
                    else None
                )
                if metrics is not None and period == "unavailable":
                    period = metrics.period
                readiness = readiness_by_set.get(f"{trigger_set.set_id}@{trigger_set.version}")
                rows.append(
                    PerformanceRow(
                        set_id=trigger_set.set_id,
                        version=trigger_set.version,
                        status=trigger_set.status,
                        period=period,
                        candles_processed=candles,
                        signals=signals,
                        candidate_intents=intents,
                        test_executions=test_executions,
                        unavailable_metrics="P&L/accounting sample unavailable" if metrics is None else "; ".join(metrics.warnings),
                        closed_trades=0 if metrics is None else metrics.closed_trades,
                        win_rate=_pct(metrics.win_rate_pct) if metrics else "unavailable",
                        expectancy=_decimal(metrics.expectancy_per_trade) if metrics else "unavailable",
                        profit_factor=_decimal(metrics.profit_factor) if metrics and metrics.profit_factor is not None else (metrics.profit_factor_reason if metrics else "unavailable"),
                        net_pnl=_decimal(metrics.net_pnl) if metrics else "unavailable",
                        max_drawdown=_decimal(metrics.max_drawdown) if metrics else "unavailable",
                        fees=_decimal(metrics.fees) if metrics else "unavailable",
                        funding=_decimal(metrics.funding) if metrics else "unavailable",
                        fees_gross_profit_pct=_pct(metrics.fees_as_pct_of_gross_profit) if metrics else "unavailable",
                        readiness=readiness.readiness if readiness else "unavailable",
                        recommendation=(
                            "; ".join(metrics.recommendation_observations)
                            if metrics and metrics.recommendation_observations
                            else (readiness.recommendation_action if readiness else "unavailable")
                        ),
                        warnings=() if metrics is None else metrics.warnings,
                    )
                )
        return tuple(rows)

    def list_test_set_evidence(self) -> tuple[TestSetEvidenceRow, ...]:
        testing_sets = tuple(row for row in self.list_trigger_sets() if row.status == "TESTING")
        if not testing_sets:
            return ()
        active_available = any(row.status == "ACTIVE" for row in self.list_trigger_sets())
        policy = GovernancePolicy()
        rows: list[TestSetEvidenceRow] = []
        for trigger_set in testing_sets:
            signals, failures = self._test_set_counts(trigger_set.set_id, trigger_set.version)
            closed_trades = self._closed_trade_count(trigger_set.set_id, trigger_set.version)
            regime_coverage = self._regime_coverage(trigger_set.set_id, trigger_set.version)
            evidence = GovernanceEvidence(
                testing_started_at=trigger_set.created_at,
                age_days=_age_days(trigger_set.created_at),
                signals_observed=signals,
                closed_trades_observed=closed_trades,
                closed_trades_capability=(
                    EvidenceCapability.AVAILABLE
                    if closed_trades is not None
                    else EvidenceCapability.UNAVAILABLE
                ),
                regime_coverage=regime_coverage,
                regime_capability=EvidenceCapability.AVAILABLE,
                baseline_comparison_available=active_available and self._baseline_comparison_available(trigger_set.set_id, trigger_set.version),
                critical_failures=failures,
            )
            result = evaluate_readiness(evidence, policy)
            rows.append(
                TestSetEvidenceRow(
                    set_id=trigger_set.set_id,
                    version=trigger_set.version,
                    status=trigger_set.status,
                    testing_started_at=result.testing_started_at,
                    age_days=result.age_days,
                    signals_observed=result.signals_observed,
                    closed_trades_observed=(
                        "unavailable" if result.closed_trades_observed is None else str(result.closed_trades_observed)
                    ),
                    regime_coverage=result.regime_coverage,
                    readiness=result.readiness.value,
                    recommendation_action=result.recommendation_action.value,
                    missing_evidence=result.evidence_gaps,
                    blocking_reasons=result.blocking_reasons,
                    comparison_available=result.comparison_available,
                    policy=f"{result.policy_id}@{result.policy_version}",
                )
            )
        return tuple(rows)

    def _closed_trade_count(self, set_id: str, version: str) -> int | None:
        if not self.db_path.exists():
            return None
        try:
            with self._connect() as conn:
                non_backtest = _non_backtest_clause(conn)
                row = _fetch_optional(
                    conn,
                    f"SELECT COUNT(*) AS count FROM futures_closed_trades WHERE trigger_set_id = ? AND trigger_set_version = ? {non_backtest}",
                    (set_id, version),
                )
        except sqlite3.Error:
            return None
        return None if row is None else int(row["count"] or 0)

    def _regime_coverage(self, set_id: str, version: str) -> str | None:
        if not self.db_path.exists():
            return None
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT DISTINCT regime_state
                    FROM runtime_lane_lifecycles
                    WHERE trigger_set_id = ? AND trigger_set_version = ?
                      AND regime_state IS NOT NULL
                      AND regime_state NOT IN ('UNKNOWN', 'INSUFFICIENT_DATA')
                    ORDER BY regime_state
                    """,
                    (set_id, version),
                ).fetchall()
        except sqlite3.Error:
            return None
        regimes = [row["regime_state"] for row in rows]
        return None if not regimes else f"{len(regimes)} regimes: {', '.join(regimes)}"

    def _baseline_comparison_available(self, set_id: str, version: str) -> bool:
        if not self.db_path.exists():
            return False
        active = next((row for row in self.list_trigger_sets() if row.status == "ACTIVE"), None)
        if active is None:
            return False
        try:
            with self._connect() as conn:
                candidate = _accounting_trade_facts(conn, set_id, version)
                baseline = _accounting_trade_facts(conn, active.set_id, active.version)
        except sqlite3.Error:
            return False
        if not candidate or not baseline:
            return False
        return max(min(trade.closed_at for trade in candidate), min(trade.closed_at for trade in baseline)) <= min(
            max(trade.closed_at for trade in candidate),
            max(trade.closed_at for trade in baseline),
        )

    def list_recent_futures_trades(self, limit: int = 20) -> tuple[FuturesTradeRow, ...]:
        if not self.db_path.exists():
            return ()
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT intent_id, risk_decision_id, client_order_id, symbol,
                           category, position_action, exchange_side, requested_qty,
                           requested_price, leverage, status, expected_net_edge,
                           updated_at
                    FROM futures_execution_orders
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        except sqlite3.Error:
            return ()
        return tuple(
            FuturesTradeRow(
                time=row["updated_at"],
                symbol=row["symbol"],
                category=row["category"],
                action=row["position_action"],
                exchange_side=row["exchange_side"],
                quantity=row["requested_qty"],
                requested_price=row["requested_price"],
                leverage=row["leverage"],
                status=row["status"],
                expected_net_edge=row["expected_net_edge"] or "unsupported",
                intent_id=row["intent_id"],
                risk_decision_id=row["risk_decision_id"],
                execution_id=row["client_order_id"],
            )
            for row in rows
        )

    def list_futures_closed_trades(self, limit: int = 20) -> tuple[FuturesClosedTradeRow, ...]:
        if not self.db_path.exists():
            return ()
        try:
            with self._connect() as conn:
                non_backtest = _non_backtest_clause(conn, prefix="WHERE")
                rows = conn.execute(
                    f"""
                    SELECT trade_id, opened_at, closed_at, symbol, direction, quantity,
                           leverage, entry_vwap, exit_vwap, gross_pnl, entry_fee,
                           exit_fee, other_fees, funding, net_pnl, duration_seconds,
                           accounting_version, trigger_set_id, trigger_set_version,
                           regime_label, entry_slippage_cost, exit_slippage_cost,
                           evidence_source, simulation_model_version
                    FROM futures_closed_trades
                    {non_backtest}
                    ORDER BY closed_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        except sqlite3.Error:
            return ()
        return tuple(
            FuturesClosedTradeRow(
                trade_id=row["trade_id"],
                opened_at=row["opened_at"],
                closed_at=row["closed_at"],
                symbol=row["symbol"],
                direction=row["direction"],
                quantity=row["quantity"],
                leverage=row["leverage"],
                entry_vwap=row["entry_vwap"],
                exit_vwap=row["exit_vwap"],
                gross_pnl=row["gross_pnl"],
                fees=str(row["entry_fee"]) + " + " + str(row["exit_fee"]) + " + " + str(row["other_fees"]),
                funding=row["funding"],
                net_pnl=row["net_pnl"],
                duration_seconds=int(row["duration_seconds"]),
                trigger_set=_compact_set(row["trigger_set_id"], row["trigger_set_version"]),
                regime=row["regime_label"] or "unavailable",
                accounting_version=row["accounting_version"],
                evidence_source=row["evidence_source"],
                simulation_model_version=row["simulation_model_version"] or "-",
                entry_slippage=row["entry_slippage_cost"] or "unavailable",
                exit_slippage=row["exit_slippage_cost"] or "unavailable",
            )
            for row in rows
        )

    def list_closed_trades_by_source(self, source: str, limit: int = 20) -> tuple[FuturesClosedTradeRow, ...]:
        if not self.db_path.exists():
            return ()
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT trade_id, opened_at, closed_at, symbol, direction, quantity,
                           leverage, entry_vwap, exit_vwap, gross_pnl, entry_fee,
                           exit_fee, other_fees, funding, net_pnl, duration_seconds,
                           accounting_version, trigger_set_id, trigger_set_version,
                           regime_label, entry_slippage_cost, exit_slippage_cost,
                           evidence_source, simulation_model_version
                    FROM futures_closed_trades
                    WHERE evidence_source = ?
                    ORDER BY closed_at DESC
                    LIMIT ?
                    """,
                    (source, limit),
                ).fetchall()
        except sqlite3.Error:
            return ()
        return tuple(
            FuturesClosedTradeRow(
                trade_id=row["trade_id"],
                opened_at=row["opened_at"],
                closed_at=row["closed_at"],
                symbol=row["symbol"],
                direction=row["direction"],
                quantity=row["quantity"],
                leverage=row["leverage"],
                entry_vwap=row["entry_vwap"],
                exit_vwap=row["exit_vwap"],
                gross_pnl=row["gross_pnl"],
                fees=str(row["entry_fee"]) + " + " + str(row["exit_fee"]) + " + " + str(row["other_fees"]),
                funding=row["funding"],
                net_pnl=row["net_pnl"],
                duration_seconds=int(row["duration_seconds"]),
                trigger_set=_compact_set(row["trigger_set_id"], row["trigger_set_version"]),
                regime=row["regime_label"] or "unavailable",
                accounting_version=row["accounting_version"],
                evidence_source=row["evidence_source"],
                simulation_model_version=row["simulation_model_version"] or "-",
                entry_slippage=row["entry_slippage_cost"] or "unavailable",
                exit_slippage=row["exit_slippage_cost"] or "unavailable",
            )
            for row in rows
        )

    def get_current_futures_position(self) -> FuturesPositionView:
        if not self.db_path.exists():
            return _unavailable_position("runtime DB not present")
        return _unavailable_position("no authoritative futures position snapshot recorded")

    def get_futures_trade_detail(self, trade_id: str) -> dict[str, Any] | None:
        safe_trade_id = str(trade_id)[:160]
        if not self.db_path.exists():
            return None
        try:
            with self._connect() as conn:
                trade = _fetch_optional(
                    conn,
                    """
                    SELECT trade_id, opened_at, closed_at, symbol, direction, quantity,
                           leverage, entry_vwap, exit_vwap, gross_pnl, entry_fee,
                           exit_fee, other_fees, funding, net_pnl, duration_seconds,
                           accounting_version, trigger_set_id, trigger_set_version,
                           regime_label, entry_slippage_cost, exit_slippage_cost,
                           evidence_source, simulation_model_version
                    FROM futures_closed_trades
                    WHERE trade_id = ?
                    """,
                    (safe_trade_id,),
                )
                if trade is None:
                    return None
                fills = conn.execute(
                    """
                    SELECT event_id, execution_id, action, quantity, price, fee,
                           fee_asset, occurred_at, requested_price, source
                    FROM futures_accounting_fills
                    WHERE trade_id = ?
                    ORDER BY occurred_at, event_id
                    """,
                    (safe_trade_id,),
                ).fetchall()
        except sqlite3.Error:
            return None
        value = _safe_dict(dict(trade))
        value["trigger_set"] = _compact_set(value.get("trigger_set_id"), value.get("trigger_set_version"))
        value["fees"] = f"{value.get('entry_fee')} + {value.get('exit_fee')} + {value.get('other_fees')}"
        value["fills"] = tuple(_safe_dict(dict(row)) for row in fills)
        return value

    def list_backtest_runs(self, limit: int = 20) -> tuple[BacktestRunRow, ...]:
        if not self.db_path.exists():
            return ()
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT r.backtest_run_id, r.status, r.created_at, r.trigger_set_id,
                           r.trigger_set_version, r.period_start, r.period_end,
                           r.payload, b.payload AS result_payload
                    FROM backtest_runs r
                    LEFT JOIN backtest_results b ON b.backtest_run_id = r.backtest_run_id
                    ORDER BY r.created_at DESC, r.backtest_run_id
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        except sqlite3.Error:
            return ()
        output = []
        for row in rows:
            payload = _json_dict(row["payload"])
            result = _json_dict(row["result_payload"])
            output.append(
                BacktestRunRow(
                    run_id=row["backtest_run_id"],
                    status=row["status"],
                    created_at=row["created_at"],
                    trigger_set=_compact_set(row["trigger_set_id"], row["trigger_set_version"]),
                    period=f"{row['period_start']} -> {row['period_end']}",
                    stage="BACKTEST",
                    simulation_model=str(payload.get("simulation_model_version") or "-"),
                    closed_trades=str(result.get("closed_trades", "-")),
                    net_pnl=str(result.get("net_pnl", "unavailable")),
                    expectancy=str(result.get("expectancy", "unavailable")),
                    profit_factor=str(result.get("profit_factor", "unavailable")),
                    max_drawdown=str(result.get("max_drawdown", "unavailable")),
                )
            )
        return tuple(output)

    def get_backtest_detail(self, run_id: str) -> dict[str, Any] | None:
        safe_run_id = str(run_id)[:160]
        if not self.db_path.exists():
            return None
        try:
            with self._connect() as conn:
                row = _fetch_optional(
                    conn,
                    """
                    SELECT r.backtest_run_id, r.status, r.created_at, r.payload,
                           b.payload AS result_payload
                    FROM backtest_runs r
                    LEFT JOIN backtest_results b ON b.backtest_run_id = r.backtest_run_id
                    WHERE r.backtest_run_id = ?
                    """,
                    (safe_run_id,),
                )
        except sqlite3.Error:
            return None
        if row is None:
            return None
        return {
            "run_id": row["backtest_run_id"],
            "status": row["status"],
            "created_at": row["created_at"],
            "run": _safe_dict(_json_dict(row["payload"])),
            "result": _safe_dict(_json_dict(row["result_payload"])),
        }
    def get_latest_futures_equity(self) -> FuturesEquityRow | None:
        if not self.db_path.exists():
            return None
        try:
            with self._connect() as conn:
                row = _fetch_optional(
                    conn,
                    """
                    SELECT *
                    FROM futures_equity_snapshots
                    ORDER BY observed_at DESC, snapshot_id DESC
                    LIMIT 1
                    """,
                )
        except sqlite3.Error:
            return None
        if row is None:
            return None
        return FuturesEquityRow(
            observed_at=row["observed_at"],
            source=row["source"],
            wallet_balance=row["wallet_balance"],
            equity=row["equity"],
            available_margin=row["available_margin"],
            used_margin=row["used_margin"],
            unrealized_pnl=row["unrealized_pnl"],
            realized_pnl=row["realized_pnl"],
            drawdown_absolute=row["drawdown_absolute"],
            drawdown_percent=row["drawdown_percent"],
            max_drawdown=row["max_drawdown"],
        )

    def list_baseline_comparisons(self) -> tuple[BaselineComparisonRow, ...]:
        if not self.db_path.exists():
            return ()
        sets = self.list_trigger_sets()
        active = next((row for row in sets if row.status == "ACTIVE"), None)
        testing = tuple(row for row in sets if row.status == "TESTING")
        if active is None or not testing:
            return ()
        rows: list[BaselineComparisonRow] = []
        with self._connect() as conn:
            baseline_facts = _accounting_trade_facts(conn, active.set_id, active.version)
            for candidate in testing:
                comparison = compare_baseline(
                    baseline_set=f"{active.set_id}@{active.version}",
                    candidate_set=f"{candidate.set_id}@{candidate.version}",
                    baseline_trades=baseline_facts,
                    candidate_trades=_accounting_trade_facts(conn, candidate.set_id, candidate.version),
                )
                rows.append(
                    BaselineComparisonRow(
                        candidate_set=comparison.candidate_set,
                        baseline_set=comparison.baseline_set,
                        available=comparison.available,
                        period=comparison.overlap_period or "unavailable",
                        baseline_closed_trades=comparison.baseline_closed_trades,
                        candidate_closed_trades=comparison.candidate_closed_trades,
                        baseline_net_pnl=_decimal(comparison.baseline_net_pnl),
                        candidate_net_pnl=_decimal(comparison.candidate_net_pnl),
                        baseline_expectancy=_decimal(comparison.baseline_expectancy),
                        candidate_expectancy=_decimal(comparison.candidate_expectancy),
                        baseline_fees=_decimal(comparison.baseline_fees),
                        candidate_fees=_decimal(comparison.candidate_fees),
                        baseline_direction_mix=comparison.baseline_direction_mix or "unavailable",
                        candidate_direction_mix=comparison.candidate_direction_mix or "unavailable",
                        reason=comparison.reason or "overlapping accounting sample available",
                    )
                )
        return tuple(rows)

    def get_current_market_regime(self, symbol: str = "BTCUSDT", timeframe: str = "1m") -> MarketRegimeView | None:
        if not self.db_path.exists():
            return None
        try:
            with self._connect() as conn:
                row = _fetch_optional(
                    conn,
                    """
                    SELECT * FROM market_regime_evaluations
                    WHERE symbol = ? AND timeframe = ?
                    ORDER BY observed_at DESC
                    LIMIT 1
                    """,
                    (symbol.upper(), timeframe),
                )
        except sqlite3.Error:
            return None
        return None if row is None else _regime_view(row)

    def list_regime_analytics(self) -> tuple[RegimeAnalyticsRow, ...]:
        if not self.db_path.exists():
            return ()
        rows: list[RegimeAnalyticsRow] = []
        signal_counts: dict[str, int] = {}
        trade_rows = ()
        facts_by_regime: dict[str, tuple[TradePerformanceFact, ...]] = {}
        try:
            with self._connect() as conn:
                signal_counts = {
                    row["regime"]: int(row["signals"] or 0)
                    for row in conn.execute(
                        """
                        SELECT COALESCE(l.regime_state, 'unavailable') AS regime,
                               SUM(CASE WHEN t.signal_type IS NOT NULL AND t.signal_type != 'NO_SIGNAL' THEN 1 ELSE 0 END) AS signals
                        FROM runtime_lane_lifecycles l
                        LEFT JOIN trigger_evaluations t ON t.signal_id = l.signal_id
                        GROUP BY COALESCE(l.regime_state, 'unavailable')
                        """
                    ).fetchall()
                }
        except sqlite3.Error:
            signal_counts = {}
        try:
            with self._connect() as conn:
                non_backtest = _non_backtest_clause(conn, prefix="WHERE")
                trade_rows = conn.execute(
                    f"""
                    SELECT COALESCE(regime_label, 'unavailable') AS regime,
                           COUNT(*) AS closed_trades,
                           SUM(CASE WHEN direction = 'LONG' THEN 1 ELSE 0 END) AS long_trades,
                           SUM(CASE WHEN direction = 'SHORT' THEN 1 ELSE 0 END) AS short_trades
                    FROM futures_closed_trades
                    {non_backtest}
                    GROUP BY COALESCE(regime_label, 'unavailable')
                    """
                ).fetchall()
        except sqlite3.Error:
            trade_rows = ()
        regimes = set(signal_counts) | {row["regime"] for row in trade_rows}
        if trade_rows:
            try:
                with self._connect() as conn:
                    facts_by_regime = {
                        regime: _accounting_trade_facts_by_regime(conn, regime)
                        for regime in regimes
                        if regime not in {"unavailable", "UNKNOWN", "INSUFFICIENT_DATA"}
                    }
            except sqlite3.Error:
                facts_by_regime = {}
        trade_count_by_regime = {row["regime"]: row for row in trade_rows}
        for regime in sorted(regimes):
            facts = facts_by_regime.get(regime, ())
            counts = trade_count_by_regime.get(regime)
            net, expectancy, fees_pct = _regime_metric_values(facts)
            rows.append(
                RegimeAnalyticsRow(
                    regime=regime,
                    signals=signal_counts.get(regime, 0),
                    closed_trades=int(counts["closed_trades"] or 0) if counts is not None else 0,
                    net_pnl=net,
                    expectancy=expectancy,
                    fees_gross_profit_pct=fees_pct,
                    long_trades=int(counts["long_trades"] or 0) if counts is not None else 0,
                    short_trades=int(counts["short_trades"] or 0) if counts is not None else 0,
                )
            )
        return tuple(rows)

    def get_operator_trading_state(self) -> OperatorStateView:
        if not self.db_path.exists():
            return OperatorStateView("TRADING_ENABLED", "-", "system_default", "default: no persisted operator pause")
        try:
            with self._connect() as conn:
                row = _fetch_optional(
                    conn,
                    """
                    SELECT state, changed_at, source, reason
                    FROM operator_trading_state
                    WHERE scope = 'ACTIVE'
                    """,
                )
        except sqlite3.Error:
            return OperatorStateView("UNKNOWN", "-", "read_model", "operator state unavailable")
        if row is None:
            return OperatorStateView("TRADING_ENABLED", "-", "system_default", "default: no persisted operator pause")
        return OperatorStateView(
            state=row["state"],
            changed_at=row["changed_at"],
            source=row["source"],
            reason=row["reason"] or "-",
        )

    def get_portfolio_snapshot(self) -> PortfolioSnapshotView:
        operator = self.get_operator_trading_state()
        if not self.db_path.exists():
            return PortfolioSnapshotView(
                as_of="-",
                source="runtime_db_missing",
                freshness_state="UNAVAILABLE",
                total_equity=None,
                available_capital=None,
                in_positions="0",
                realized_pnl_today=None,
                unrealized_pnl=None,
                open_positions_count=0,
                entries_paused=operator.state == "TRADING_PAUSED",
                data_warnings=("runtime DB not present",),
            )
        equity = self.get_latest_futures_equity()
        open_rows = self.list_portfolio_open_positions()
        in_positions = sum((Decimal(row.value) for row in open_rows), Decimal("0"))
        realized_today = self.get_portfolio_closed_summary().realized_pnl_today
        if equity is None:
            return PortfolioSnapshotView(
                as_of="-",
                source="account_equity_unavailable",
                freshness_state="UNAVAILABLE",
                total_equity=None,
                available_capital=None,
                in_positions=str(in_positions),
                realized_pnl_today=realized_today,
                unrealized_pnl=None,
                open_positions_count=len(open_rows),
                entries_paused=operator.state == "TRADING_PAUSED",
                data_warnings=("authoritative account equity snapshot unavailable",),
            )
        return PortfolioSnapshotView(
            as_of=equity.observed_at,
            source=equity.source,
            freshness_state=_freshness_state(equity.observed_at),
            total_equity=equity.equity,
            available_capital=equity.available_margin,
            in_positions=str(in_positions),
            realized_pnl_today=realized_today,
            unrealized_pnl=equity.unrealized_pnl,
            open_positions_count=len(open_rows),
            entries_paused=operator.state == "TRADING_PAUSED",
            last_reconciliation_at=self._last_reconciliation_at(),
            data_warnings=() if _freshness_state(equity.observed_at) == "FRESH" else ("account equity snapshot is stale",),
        )

    def list_portfolio_open_positions(
        self,
        *,
        symbol: str | None = None,
        side: str | None = None,
        set_version: str | None = None,
        limit: int = 100,
    ) -> tuple[PortfolioOpenPositionRow, ...]:
        if not self.db_path.exists():
            return ()
        clauses = ["status = 'OPEN'", _portfolio_source_clause()]
        values: list[Any] = []
        _append_optional_filter(clauses, values, "symbol", symbol)
        _append_optional_filter(clauses, values, "side", side)
        _append_optional_filter(clauses, values, "trigger_set_version", set_version)
        try:
            with self._connect() as conn:
                if not _has_table(conn, "futures_positions"):
                    return ()
                rows = conn.execute(
                    f"""
                    SELECT position_id, symbol, side, leverage, current_qty,
                           position_value, entry_price, tp_pct, tp_price, sl_pct,
                           sl_price, trigger_set_id, trigger_set_version,
                           rules_version_id, opened_at, status
                    FROM futures_positions
                    WHERE {' AND '.join(clauses)}
                    ORDER BY opened_at DESC, position_id DESC
                    LIMIT ?
                    """,
                    (*values, max(1, min(int(limit), 250))),
                ).fetchall()
        except (sqlite3.Error, ValueError):
            return ()
        return tuple(_portfolio_open_position_row(row) for row in rows)

    def list_portfolio_closed_positions(
        self,
        *,
        symbol: str | None = None,
        side: str | None = None,
        set_version: str | None = None,
        close_reason: str | None = None,
        limit: int = 100,
    ) -> tuple[PortfolioClosedPositionRow, ...]:
        if not self.db_path.exists():
            return ()
        clauses = [_portfolio_source_clause()]
        values: list[Any] = []
        _append_optional_filter(clauses, values, "symbol", symbol)
        _append_optional_filter(clauses, values, "direction", side)
        _append_optional_filter(clauses, values, "trigger_set_version", set_version)
        _append_optional_filter(clauses, values, "close_reason", close_reason)
        try:
            with self._connect() as conn:
                if not _has_table(conn, "futures_closed_positions"):
                    return ()
                rows = conn.execute(
                    f"""
                    SELECT trade_id, position_id, symbol, direction, leverage, qty,
                           position_value, entry_vwap, exit_vwap, planned_tp_pct,
                           planned_tp_price, planned_sl_pct, planned_sl_price,
                           realized_pnl_pct, net_pnl, close_reason, trigger_set_id,
                           trigger_set_version, rules_version_id, opened_at, closed_at,
                           duration_seconds
                    FROM futures_closed_positions
                    WHERE {' AND '.join(clauses)}
                    ORDER BY closed_at DESC, trade_id DESC
                    LIMIT ?
                    """,
                    (*values, max(1, min(int(limit), 250))),
                ).fetchall()
        except (sqlite3.Error, ValueError):
            return ()
        return tuple(_portfolio_closed_position_row(row) for row in rows)

    def get_portfolio_open_summary(self) -> PortfolioOpenSummaryView:
        rows = self.list_portfolio_open_positions()
        capital = sum((Decimal(row.value) for row in rows), Decimal("0"))
        equity = self.get_latest_futures_equity()
        return PortfolioOpenSummaryView(
            open_count=len(rows),
            capital_in_open_positions=str(capital),
            unrealized_pnl=None if equity is None else equity.unrealized_pnl,
        )

    def get_portfolio_closed_summary(self) -> PortfolioClosedSummaryView:
        rows = self._portfolio_closed_today_rows()
        if not rows:
            return PortfolioClosedSummaryView(0, None, None)
        realized = sum((Decimal(row.realized_pnl_amount) for row in rows), Decimal("0"))
        winners = sum(1 for row in rows if Decimal(row.realized_pnl_amount) > 0)
        return PortfolioClosedSummaryView(
            closed_today_count=len(rows),
            realized_pnl_today=str(realized),
            win_rate_today=str((Decimal(winners) / Decimal(len(rows)) * Decimal("100")).quantize(Decimal("0.01"))),
        )

    def _portfolio_closed_today_rows(self) -> tuple[PortfolioClosedPositionRow, ...]:
        today = datetime.now(UTC).date().isoformat()
        return tuple(row for row in self.list_portfolio_closed_positions(limit=250) if _date_prefix(row.closed_at) == today)

    def _last_reconciliation_at(self) -> str | None:
        if not self.db_path.exists():
            return None
        try:
            with self._connect() as conn:
                if not _has_table(conn, "futures_executions"):
                    return None
                row = _fetch_optional(conn, "SELECT MAX(updated_at) AS updated_at FROM futures_executions")
        except sqlite3.Error:
            return None
        return None if row is None else row["updated_at"]

    def _regime_for_context(self, context_id: str) -> dict[str, Any] | None:
        try:
            with self._connect() as conn:
                row = _fetch_optional(conn, "SELECT * FROM market_regime_evaluations WHERE context_id = ?", (context_id,))
        except sqlite3.Error:
            return None
        if row is None:
            return None
        value = _safe_dict(dict(row))
        value["input_snapshot"] = _json_value(value.get("input_snapshot"))
        value["normalized_features"] = _json_value(value.get("normalized_features"))
        value["thresholds"] = _json_value(value.get("thresholds"))
        return value

    def list_logs(self, limit: int = 20) -> tuple[LogRow, ...]:
        if not self.db_path.exists():
            return ()
        safe_limit = max(1, min(int(limit), 100))
        try:
            with self._connect() as conn:
                lane_rows = conn.execute(
                    """
                    SELECT processed_at, lane, status, candle_id, trigger_set_version, error
                    FROM runtime_lane_lifecycles
                    ORDER BY COALESCE(processed_at, candle_open_time) DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
        except sqlite3.Error:
            lane_rows = ()
        logs = [
            LogRow(
                time=row["processed_at"] or "",
                message=f"{row['lane']} {row['trigger_set_version']} {row['status']} for {row['candle_id']}",
                status=row["lane"],
            )
            for row in lane_rows
        ]
        if logs:
            return tuple(logs)
        return tuple(
            LogRow(
                time=row.time,
                message=f"{row.symbol} {row.trigger_result} -> {row.risk_result} -> {row.execution_status}",
                status="ACTIVE",
            )
            for row in self.list_recent_activity(limit=safe_limit)
        )

    def get_api_health(self) -> tuple[dict[str, str], ...]:
        state = self.get_latest_runtime_state()
        return (
            {
                "connection": "Bybit Demo public market data",
                "status": "available" if state.db_health == "OK" else "unknown",
                "uptime": "not measured",
                "last_success": state.last_processed_at or "not recorded",
                "disconnects_24h": "not measured",
                "last_error": "not recorded",
            },
        )

    def list_lane_trades(self, lane: str, limit: int = 25) -> tuple[PaperTradeRow, ...]:
        rows = self.list_recent_paper_trades(limit=limit)
        if not self.db_path.exists():
            return rows
        try:
            with self._connect() as conn:
                has_lane = any(row["name"] == "lane" for row in conn.execute("PRAGMA table_info(execution_orders)").fetchall())
        except sqlite3.Error:
            return rows
        if not has_lane:
            return rows if lane == "ACTIVE" else ()
        try:
            with self._connect() as conn:
                query_rows = conn.execute(
                    """
                    SELECT e.intent_id, e.risk_decision_id, e.client_order_id,
                           e.exchange_order_id, e.symbol, e.side, e.order_type,
                           e.requested_qty, e.requested_price, e.status,
                           e.created_at, e.updated_at, e.exchange_status,
                           e.reconciliation_state,
                           f.price AS fill_price, f.quantity AS fill_quantity,
                           f.created_at AS fill_time
                    FROM runtime_lane_lifecycles l
                    JOIN execution_orders e ON e.intent_id = l.execution_intent_id
                    LEFT JOIN execution_fills f ON f.intent_id = e.intent_id
                    WHERE l.lane = ?
                    ORDER BY COALESCE(f.created_at, e.updated_at) DESC
                    LIMIT ?
                    """,
                    (lane, max(1, min(int(limit), 100))),
                ).fetchall()
        except sqlite3.Error:
            return ()
        return tuple(_trade_row(row) for row in query_rows)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=1)
        conn.row_factory = sqlite3.Row
        return conn

    def _overview(self, lane: str) -> OverviewView:
        sets = self.list_trigger_sets()
        status = "ACTIVE" if lane == "ACTIVE" else "TESTING"
        trigger_set = next((item for item in sets if item.status == status), None)
        trades = self.list_lane_trades(lane)
        logs = [row for row in self.list_logs(50) if row.status == lane]
        latest = logs[0] if logs else None
        return OverviewView(
            lane=lane,
            status=status if trigger_set else "UNKNOWN",
            rule_set="-" if trigger_set is None else trigger_set.version,
            rules_count=0 if trigger_set is None else trigger_set.rules_count,
            latest_candle="-" if latest is None else latest.message.rsplit(" ", 1)[-1],
            latest_signal=self.get_latest_decision().signal_type if lane == "ACTIVE" else ("recorded" if latest else "none"),
            trades_count=len(trades),
            last_execution="none" if not trades else trades[0].status,
        )

    def _rules_for_set(self, set_id: str, version: str) -> tuple[dict[str, Any], ...]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT r.rule_id, r.version, r.name, r.condition, r.status
                    FROM trigger_set_memberships m
                    JOIN rule_definitions r
                      ON r.rule_id = m.rule_id AND r.version = m.rule_version
                    WHERE m.set_id = ? AND m.set_version = ?
                    ORDER BY m.position
                    """,
                    (set_id, version),
                ).fetchall()
        except sqlite3.Error:
            return ()
        return tuple(_safe_dict(dict(row)) for row in rows)

    def _test_set_counts(self, set_id: str, version: str) -> tuple[int, int]:
        if not self.db_path.exists():
            return 0, 0
        try:
            with self._connect() as conn:
                row = _fetch_optional(
                    conn,
                    """
                    SELECT
                        SUM(CASE WHEN t.signal_type IS NOT NULL AND t.signal_type != 'NO_SIGNAL' THEN 1 ELSE 0 END) AS signals,
                        SUM(CASE WHEN l.status = 'execution_error' THEN 1 ELSE 0 END) AS failures
                    FROM runtime_lane_lifecycles l
                    LEFT JOIN trigger_evaluations t ON t.signal_id = l.signal_id
                    WHERE l.lane = 'TEST' AND l.trigger_set_id = ? AND l.trigger_set_version = ?
                    """,
                    (set_id, version),
                )
        except sqlite3.Error:
            return 0, 0
        if row is None:
            return 0, 0
        return int(row["signals"] or 0), int(row["failures"] or 0)


def _decode_rule_row(row: sqlite3.Row) -> dict[str, Any]:
    value = _safe_dict(dict(row))
    value["definition"] = _json_value(value.get("definition"))
    return value


def _recommendation_row(row: sqlite3.Row) -> RecommendationRow:
    data = _json_value(row["payload"])
    set_id = data.get("resulting_test_set_id") or "-"
    set_version = data.get("resulting_test_set_version") or "-"
    return RecommendationRow(
        recommendation_id=row["recommendation_id"],
        created_at=row["created_at"],
        status=row["status"],
        title=row["title"],
        resulting_test_set=f"{set_id}@{set_version}" if set_id != "-" else "-",
        evidence=data.get("evidence", "-"),
    )


def _recommendations_for_rule(conn: sqlite3.Connection, rule_id: str, version: str) -> tuple[dict[str, Any], ...]:
    rows = conn.execute("SELECT status, payload FROM recommendations ORDER BY created_at DESC, recommendation_id").fetchall()
    matches = []
    needle = [rule_id, version]
    for row in rows:
        data = _json_value(row["payload"])
        data["status"] = row["status"]
        proposed = data.get("proposed_rule_changes", {})
        sources = data.get("source_rule_versions", [])
        if needle in sources or proposed.get("add_rule_version") == f"{rule_id}@{version}":
            matches.append(_safe_dict(data))
    return tuple(matches)

def _empty_runtime_state(db_health: str) -> RuntimeStateView:
    return RuntimeStateView(
        status="UNKNOWN",
        trading_mode="PAPER",
        market_source="Bybit Demo",
        symbol="BTCUSDT",
        timeframe="1m",
        last_processed_candle_id=None,
        last_processed_candle_open_time=None,
        last_processed_at=None,
        db_health=db_health,
    )


def _age_days(value: str) -> int:
    try:
        started = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return 0
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    return max((datetime.now(UTC) - started).days, 0)


def _legacy_trigger_sets() -> tuple[TriggerSetRow, ...]:
    return (
        TriggerSetRow(
            set_id="legacy-runtime",
            version="legacy",
            purpose="Legacy runtime records before Trigger Set registry initialization",
            rules_count=0,
            created_at="-",
            status="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
        ),
    )


def _fetch_optional(conn: sqlite3.Connection, query: str, values: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    return conn.execute(query, values).fetchone()


def _activity_row(row: sqlite3.Row) -> ActivityRow:
    signal_type = row["signal_type"] or "none"
    strategy = "BUY intent" if row["strategy_intent_id"] else _strategy_result(row["status"], signal_type)
    risk = _risk_result(row["risk_approved"], row["blocking_rule_ids"])
    execution = row["execution_status"] or "none"
    return ActivityRow(
        candle_id=row["candle_id"],
        time=row["processed_at"] or row["candle_open_time"],
        symbol=row["symbol"],
        candle=row["candle_open_time"],
        trigger_result=signal_type,
        strategy_decision=strategy,
        risk_result=risk,
        execution_status=execution,
    )


def _unavailable_position(reason: str) -> FuturesPositionView:
    return FuturesPositionView(
        state="Not available",
        symbol="BTCUSDT",
        direction="Not available",
        quantity="-",
        entry="-",
        mark="-",
        leverage="-",
        liquidation="Not available",
        take_profit="Not configured",
        stop_loss="Not configured",
        notional="-",
        unrealized_pnl="unavailable",
        trigger_set="-",
        regime="unavailable",
        opened_at="-",
        source=reason,
    )
def _trade_row(row: sqlite3.Row) -> PaperTradeRow:
    return PaperTradeRow(
        time=row["fill_time"] or row["updated_at"],
        symbol=row["symbol"],
        side=row["side"],
        quantity=row["fill_quantity"] or row["requested_qty"],
        requested_price=row["requested_price"],
        fill_price=row["fill_price"] or "none",
        status=row["status"],
        intent_id=row["intent_id"],
        risk_decision_id=row["risk_decision_id"],
        execution_id=row["exchange_order_id"] or row["client_order_id"],
    )


def _accounting_trade_facts(conn: sqlite3.Connection, set_id: str, version: str) -> tuple[TradePerformanceFact, ...]:
    try:
        source_expr = "evidence_source" if _has_column(conn, "futures_closed_trades", "evidence_source") else "'exchange'"
        non_backtest = _non_backtest_clause(conn)
        rows = conn.execute(
            f"""
            SELECT trade_id, trigger_set_id, trigger_set_version, symbol, direction,
                   closed_at, net_pnl, gross_pnl, entry_fee, exit_fee, other_fees,
                   funding, duration_seconds, regime_label,
                   COALESCE({source_expr}, 'exchange') AS evidence_source
            FROM futures_closed_trades
            WHERE trigger_set_id = ? AND trigger_set_version = ?
              {non_backtest}
            ORDER BY closed_at, trade_id
            """,
            (set_id, version),
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
    )


def _accounting_trade_facts_by_regime(conn: sqlite3.Connection, regime: str) -> tuple[TradePerformanceFact, ...]:
    try:
        source_expr = "evidence_source" if _has_column(conn, "futures_closed_trades", "evidence_source") else "'exchange'"
        non_backtest = _non_backtest_clause(conn)
        rows = conn.execute(
            f"""
            SELECT trade_id, trigger_set_id, trigger_set_version, symbol, direction,
                   closed_at, net_pnl, gross_pnl, entry_fee, exit_fee, other_fees,
                   funding, duration_seconds, regime_label,
                   COALESCE({source_expr}, 'exchange') AS evidence_source
            FROM futures_closed_trades
            WHERE COALESCE(regime_label, 'unavailable') = ?
              {non_backtest}
            ORDER BY closed_at, trade_id
            """,
            (regime,),
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
    )


def _non_backtest_clause(conn: sqlite3.Connection, *, prefix: str = "AND") -> str:
    if not _has_column(conn, "futures_closed_trades", "evidence_source"):
        return ""
    return f"{prefix} COALESCE(evidence_source, 'exchange') != 'BACKTEST'"


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    try:
        return column in {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    except sqlite3.Error:
        return False


def _has_table(conn: sqlite3.Connection, table: str) -> bool:
    try:
        row = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone()
    except sqlite3.Error:
        return False
    return row is not None


def _portfolio_source_clause() -> str:
    return "UPPER(COALESCE(evidence_source, 'ACTIVE')) IN ('ACTIVE', 'EXCHANGE')"


def _append_optional_filter(clauses: list[str], values: list[Any], column: str, raw: str | None) -> None:
    value = (raw or "").strip()
    if value and value.lower() not in {"all", "coin: all", "side: all", "set: all", "close reason: all"}:
        clauses.append(f"{column} = ?")
        values.append(value.upper() if column in {"symbol", "side", "direction", "close_reason"} else value)


def _portfolio_open_position_row(row: sqlite3.Row) -> PortfolioOpenPositionRow:
    opened_at = row["opened_at"]
    age_seconds = _age_seconds(opened_at)
    qty = row["current_qty"]
    symbol = row["symbol"]
    return PortfolioOpenPositionRow(
        position_id=row["position_id"],
        symbol=symbol,
        side=row["side"],
        leverage=row["leverage"],
        qty=qty,
        qty_unit=_base_from_symbol(symbol),
        value=row["position_value"],
        entry_price=row["entry_price"],
        current_price=None,
        price_source="MARK_UNAVAILABLE",
        take_profit_pct=row["tp_pct"],
        take_profit_price=row["tp_price"],
        stop_loss_pct=row["sl_pct"],
        stop_loss_price=row["sl_price"],
        unrealized_pnl_pct=None,
        unrealized_pnl_amount=None,
        set_id=row["trigger_set_id"],
        set_version=row["trigger_set_version"],
        rules_version_id=row["rules_version_id"] if "rules_version_id" in row.keys() else None,
        opened_at=opened_at,
        age_seconds=age_seconds,
        status=row["status"],
        close_action_available=row["status"] == "OPEN",
    )


def _portfolio_closed_position_row(row: sqlite3.Row) -> PortfolioClosedPositionRow:
    symbol = row["symbol"]
    return PortfolioClosedPositionRow(
        trade_id=row["trade_id"],
        position_id=row["position_id"],
        symbol=symbol,
        side=row["direction"],
        leverage=row["leverage"],
        qty=row["qty"],
        qty_unit=_base_from_symbol(symbol),
        value=row["position_value"],
        entry_price=row["entry_vwap"],
        exit_price=row["exit_vwap"],
        planned_tp_pct=row["planned_tp_pct"],
        planned_tp_price=row["planned_tp_price"],
        planned_sl_pct=row["planned_sl_pct"],
        planned_sl_price=row["planned_sl_price"],
        realized_pnl_pct=row["realized_pnl_pct"],
        realized_pnl_amount=row["net_pnl"],
        close_reason=row["close_reason"],
        set_id=row["trigger_set_id"],
        set_version=row["trigger_set_version"],
        rules_version_id=row["rules_version_id"] if "rules_version_id" in row.keys() else None,
        opened_at=row["opened_at"],
        closed_at=row["closed_at"],
        duration_seconds=int(row["duration_seconds"]),
    )


def _freshness_state(observed_at: str) -> str:
    try:
        observed = datetime.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return "UNAVAILABLE"
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=UTC)
    age_seconds = (datetime.now(UTC) - observed).total_seconds()
    if age_seconds < 0:
        return "FRESH"
    return "FRESH" if age_seconds <= 300 else "STALE"


def _age_seconds(value: str | None) -> int | None:
    try:
        opened = datetime.fromisoformat(value or "")
    except ValueError:
        return None
    if opened.tzinfo is None:
        opened = opened.replace(tzinfo=UTC)
    return max(0, int((datetime.now(UTC) - opened).total_seconds()))


def _date_prefix(value: str | None) -> str:
    return "" if not value else value[:10]


def _base_from_symbol(symbol: str) -> str:
    return symbol[:-4] if symbol.endswith("USDT") else symbol


def _regime_metric_values(facts: tuple[TradePerformanceFact, ...]) -> tuple[str, str, str]:
    if not facts:
        return "unavailable", "unavailable", "unavailable"
    net = sum((fact.net_pnl for fact in facts), Decimal("0"))
    expectancy = net / Decimal(len(facts))
    gross_profit = sum((fact.gross_pnl for fact in facts if fact.gross_pnl > 0), Decimal("0"))
    fees = sum((fact.entry_fee + fact.exit_fee + fact.other_fees for fact in facts), Decimal("0"))
    fees_pct = None if gross_profit <= 0 else fees / gross_profit * Decimal("100")
    return str(net), str(expectancy), _pct(fees_pct)


def _regime_view(row: sqlite3.Row) -> MarketRegimeView:
    features = _json_value(row["normalized_features"])
    return MarketRegimeView(
        context_id=row["context_id"],
        state=row["label"] or "UNKNOWN",
        rule=f"{row['rule_id']}@{row['version']}",
        symbol=row["symbol"],
        timeframe=row["timeframe"],
        observed_at=row["observed_at"],
        window_return_pct=str(features.get("window_return_pct", "unavailable")) if isinstance(features, dict) else "unavailable",
        normalized_trend=str(features.get("normalized_trend", "unavailable")) if isinstance(features, dict) else "unavailable",
        directional_persistence=str(features.get("directional_persistence", "unavailable")) if isinstance(features, dict) else "unavailable",
        reason=row["reason"] or "classified",
    )


def _decimal(value: Decimal | None) -> str:
    return "unavailable" if value is None else str(value)


def _pct(value: Decimal | None) -> str:
    return "unavailable" if value is None else f"{value}%"


def _compact_set(set_id: str | None, version: str | None) -> str:
    if not set_id and not version:
        return "unavailable"
    if not set_id:
        return str(version)
    if not version:
        return str(set_id)
    return f"{set_id}@{version}"


def _decision_from_trace(trace: TraceView | None) -> DecisionView:
    if trace is None or trace.lifecycle is None:
        return DecisionView(None, None, "TRG-001", "none", "none", "none", "none", "none", "No runtime activity yet.")
    trigger = trace.trigger or {}
    strategy = trace.strategy or {}
    risk = trace.risk or {}
    execution = trace.execution or {}
    signal_type = trigger.get("signal_type") or "none"
    risk_result = _risk_result(risk.get("approved"), risk.get("blocking_rule_ids"))
    reason = _reason(trace.lifecycle, trigger, risk)
    return DecisionView(
        candle_id=trace.candle_id,
        candle_open_time=trace.lifecycle.get("candle_open_time"),
        trigger_rule=_rule_label(trigger),
        trigger_result=signal_type,
        signal_type=signal_type,
        strategy_result="BUY intent" if strategy else _strategy_result(trace.lifecycle.get("status"), signal_type),
        risk_result=risk_result,
        execution_result=execution.get("status") or "none",
        reason=reason,
    )


def _strategy_result(status: str | None, signal_type: str) -> str:
    if signal_type == "NO_SIGNAL":
        return "not evaluated"
    if status == "no_intent":
        return "no intent"
    return "none"


def _risk_result(approved: Any, blocking_raw: Any) -> str:
    if approved is None:
        return "not evaluated"
    if int(approved) == 1:
        return "APPROVED"
    blockers = _json_list(blocking_raw)
    return "REJECTED" if not blockers else f"REJECTED: {', '.join(blockers)}"


def _reason(lifecycle: dict[str, Any], trigger: dict[str, Any], risk: dict[str, Any]) -> str:
    if trigger.get("signal_type") == "NO_SIGNAL":
        return "Trigger evaluated normally and produced NO_SIGNAL."
    if risk and int(risk.get("approved") or 0) == 0:
        blockers = _json_list(risk.get("blocking_rule_ids"))
        return "Risk blocked execution: " + (", ".join(blockers) if blockers else "unspecified rule")
    if lifecycle.get("status") == "completed":
        return "Lifecycle completed with persisted execution state."
    return lifecycle.get("error") or lifecycle.get("status") or "No further action recorded."


def _rule_label(trigger: dict[str, Any]) -> str:
    if not trigger:
        return "TRG-001"
    return f"{trigger.get('trigger_rule_id')} v{trigger.get('trigger_rule_version')}"


def _decode_json_fields(row: sqlite3.Row | None, fields: set[str]) -> dict[str, Any] | None:
    if row is None:
        return None
    value = _safe_dict(dict(row))
    for field in fields:
        if field in value and value[field] is not None:
            value[field] = _json_value(value[field])
    return value


def _signal_view(trigger: dict[str, Any] | None) -> dict[str, Any] | None:
    if trigger is None:
        return None
    return {
        "signal_id": trigger.get("signal_id"),
        "signal_type": trigger.get("signal_type"),
        "symbol": trigger.get("symbol"),
        "observed_at": trigger.get("observed_at"),
        "source_trigger_rule_id": trigger.get("trigger_rule_id"),
        "source_trigger_rule_version": trigger.get("trigger_rule_version"),
    }


def _trade_intent_view(strategy: dict[str, Any] | None) -> dict[str, Any] | None:
    if strategy is None:
        return None
    return {
        "intent_id": strategy.get("intent_id"),
        "strategy_rule_id": strategy.get("strategy_rule_id"),
        "strategy_rule_version": strategy.get("strategy_rule_version"),
        "symbol": strategy.get("symbol"),
        "side": strategy.get("side"),
        "reason_signal_ids": strategy.get("signal_ids"),
        "reason_trigger_ids": strategy.get("trigger_ids"),
        "created_at": strategy.get("created_at"),
        "regime_context_id": strategy.get("regime_context_id"),
        "regime_rule_id": strategy.get("regime_rule_id"),
        "regime_rule_version": strategy.get("regime_rule_version"),
        "regime_state": strategy.get("regime_state"),
    }


def _safe_dict(row: dict[str, Any]) -> dict[str, Any]:
    return {key: _redact_value(key, value) for key, value in row.items()}


def _redact_value(key: str, value: Any) -> Any:
    key_lower = key.lower()
    if any(token in key_lower for token in ("secret", "api_key", "authorization", "credential")):
        return "[redacted]"
    if isinstance(value, str):
        lower = value.lower()
        if any(token in lower for token in ("bybit_api_secret", "bybit_api_key", "paste_your", "unit-signing-value", "authorization:", "x-bapi-api-key")):
            return "[redacted]"
    return value


def _json_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return raw


def _json_dict(raw: Any) -> dict[str, Any]:
    value = _json_value(raw)
    return value if isinstance(value, dict) else {}


def _json_list(raw: Any) -> list[str]:
    value = _json_value(raw)
    if isinstance(value, list):
        return [str(item) for item in value]
    return []
