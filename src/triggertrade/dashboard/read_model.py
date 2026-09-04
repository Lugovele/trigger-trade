"""Read-only dashboard query model over TriggerTrade SQLite persistence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3
from typing import Any


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

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=1)
        conn.row_factory = sqlite3.Row
        return conn


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
