"""Read-only dashboard query model over TriggerTrade SQLite persistence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import sqlite3
from typing import Any

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
class OperatorStateView:
    state: str
    changed_at: str
    source: str
    reason: str


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
                           execution_intent_id, processed_at, error
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
                               symbol, side, signal_ids, trigger_ids, created_at
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
                           processed_at, error
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
                           processed_at, error
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
                               lane, trigger_set_id, trigger_set_version
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
                if counts is None or int(counts["candles"] or 0) == 0:
                    continue
                rows.append(
                    PerformanceRow(
                        set_id=trigger_set.set_id,
                        version=trigger_set.version,
                        status=trigger_set.status,
                        period=period,
                        candles_processed=int(counts["candles"] or 0),
                        signals=int(counts["signals"] or 0),
                        candidate_intents=int(counts["intents"] or 0),
                        test_executions=int(counts["test_executions"] or 0),
                        unavailable_metrics="P&L, win rate, return and drawdown unavailable: no accounting semantics yet",
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
            evidence = GovernanceEvidence(
                testing_started_at=trigger_set.created_at,
                age_days=_age_days(trigger_set.created_at),
                signals_observed=signals,
                closed_trades_observed=None,
                closed_trades_capability=EvidenceCapability.UNAVAILABLE,
                regime_coverage=None,
                regime_capability=EvidenceCapability.UNAVAILABLE,
                baseline_comparison_available=active_available,
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
                    closed_trades_observed="unavailable",
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


def _json_list(raw: Any) -> list[str]:
    value = _json_value(raw)
    if isinstance(value, list):
        return [str(item) for item in value]
    return []
