"""Traceability persistence for trading decisions and canonical audit events."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import json
import re
import sqlite3
from typing import TYPE_CHECKING, Any

from triggertrade.execution import RiskDecision, TradeIntent
from triggertrade.triggers import Signal

if TYPE_CHECKING:
    from triggertrade.execution.futures import FuturesRiskDecision, FuturesTradeIntent


AUDIT_SCHEMA_VERSION = "audit-event-v1"

_SECRET_RE = re.compile(
    r"(api[_-]?key|api[_-]?secret|authorization|bearer|cookie|csrf|session|token|password|credential|signature|\.env)",
    re.I,
)
_ID_RE = re.compile(r"^[A-Za-z0-9_.:@+-]{1,200}$")


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    created_at: str
    event_type: str
    source_type: str
    source_id: str | None
    scope: str
    entity_type: str
    entity_id: str
    related_entity_type: str | None = None
    related_entity_id: str | None = None
    set_id: str | None = None
    set_version: str | None = None
    rules_version_id: str | None = None
    trigger_id: str | None = None
    trigger_version: str | None = None
    research_id: str | None = None
    run_id: str | None = None
    position_id: str | None = None
    order_id: str | None = None
    result: str = "RECORDED"
    reason_code: str | None = None
    safe_metadata: dict[str, Any] | None = None
    schema_version: str = AUDIT_SCHEMA_VERSION


class TraceStore:
    def __init__(self, path: str | Path = "runtime/triggertrade.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_trigger_evaluation(self, signal: Signal) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO trigger_evaluations (
                    signal_id, trigger_rule_id, trigger_rule_version, symbol,
                    observed_at, window, input_snapshot, condition_result, signal_type,
                    lane, trigger_set_id, trigger_set_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.signal_id,
                    signal.trigger_rule_id,
                    signal.trigger_rule_version,
                    signal.symbol,
                    signal.observed_at,
                    signal.window,
                    json.dumps(dict(signal.input_snapshot), sort_keys=True),
                    int(signal.condition_result),
                    signal.signal_type.value,
                    signal.lane,
                    signal.trigger_set_id,
                    signal.trigger_set_version,
                ),
            )
        self.record_audit_event(
            event_type="TRIGGER_EVALUATED",
            source_type="RUNTIME",
            source_id=signal.signal_id,
            scope=signal.lane or "UNKNOWN",
            entity_type="trigger_evaluation",
            entity_id=signal.signal_id,
            set_id=signal.trigger_set_id,
            set_version=signal.trigger_set_version,
            trigger_id=signal.trigger_rule_id,
            trigger_version=signal.trigger_rule_version,
            result=signal.signal_type.value,
            reason_code=signal.reason,
            safe_metadata={
                "symbol": signal.symbol,
                "window": signal.window,
                "condition_result": str(signal.condition_result),
                "input_snapshot": dict(signal.input_snapshot),
            },
            created_at=signal.observed_at,
        )

    def save_strategy_decision(self, intent: TradeIntent) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO strategy_decisions (
                    intent_id, strategy_rule_id, strategy_rule_version, symbol,
                    side, signal_ids, trigger_ids, created_at,
                    lane, trigger_set_id, trigger_set_version,
                    regime_context_id, regime_rule_id, regime_rule_version,
                    regime_state
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    intent.intent_id,
                    intent.strategy_rule_id,
                    intent.strategy_rule_version,
                    intent.symbol,
                    intent.side.value,
                    json.dumps(intent.reason_signal_ids),
                    json.dumps(intent.reason_trigger_ids),
                    intent.created_at,
                    intent.lane,
                    intent.trigger_set_id,
                    intent.trigger_set_version,
                    intent.regime_context_id,
                    intent.regime_rule_id,
                    intent.regime_rule_version,
                    intent.regime_state,
                ),
            )

    def save_futures_strategy_decision(self, intent: FuturesTradeIntent, signal_ids: tuple[str, ...]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO strategy_decisions (
                    intent_id, strategy_rule_id, strategy_rule_version, symbol,
                    side, signal_ids, trigger_ids, created_at,
                    lane, trigger_set_id, trigger_set_version,
                    regime_context_id, regime_rule_id, regime_rule_version,
                    regime_state
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    intent.intent_id,
                    intent.strategy_rule_id,
                    intent.strategy_rule_version,
                    intent.symbol,
                    intent.action.value,
                    json.dumps(signal_ids),
                    json.dumps(tuple(signal.split("-", 1)[0].upper() for signal in signal_ids)),
                    intent.created_at,
                    intent.lane,
                    intent.trigger_set_id,
                    intent.trigger_set_version,
                    intent.regime_context_id,
                    intent.regime_rule_id,
                    intent.regime_rule_version,
                    intent.regime_state,
                ),
            )
        self.record_audit_event(
            event_type="TRADE_INTENT_CREATED",
            source_type="RUNTIME",
            source_id=intent.intent_id,
            scope=intent.lane or "UNKNOWN",
            entity_type="trade_intent",
            entity_id=intent.intent_id,
            related_entity_type="signal",
            related_entity_id=",".join(signal_ids),
            set_id=intent.trigger_set_id,
            set_version=intent.trigger_set_version,
            rules_version_id=intent.rules_version_id,
            result=intent.action.value,
            safe_metadata={
                "symbol": intent.symbol,
                "category": intent.category.value,
                "qty": str(intent.quantity),
                "price": str(intent.price),
                "order_type": intent.order_type.value,
                "strategy_rule_id": intent.strategy_rule_id,
                "strategy_rule_version": intent.strategy_rule_version,
                "regime_context_id": intent.regime_context_id,
                "regime_state": intent.regime_state,
                "take_profit": getattr(intent.take_profit, "target_price", None),
                "stop_loss": getattr(intent.stop_loss, "stop_price", None),
            },
            created_at=intent.created_at,
        )

    def save_risk_decision(self, decision: RiskDecision) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO risk_decisions (
                    risk_decision_id, intent_id, approved, checked_rule_ids,
                    blocking_rule_ids, approved_notional, approved_quantity,
                    rejection_reason, created_at, lane, trigger_set_id,
                    trigger_set_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.risk_decision_id,
                    decision.intent_id,
                    int(decision.approved),
                    json.dumps(decision.checked_rule_ids),
                    json.dumps(decision.blocking_rule_ids),
                    None if decision.approved_notional is None else str(decision.approved_notional),
                    None if decision.approved_quantity is None else str(decision.approved_quantity),
                    decision.rejection_reason,
                    decision.created_at,
                    decision.lane,
                    decision.trigger_set_id,
                    decision.trigger_set_version,
                ),
            )

    def save_futures_risk_decision(
        self,
        decision: FuturesRiskDecision,
        *,
        trigger_set_id: str | None = None,
        trigger_set_version: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO risk_decisions (
                    risk_decision_id, intent_id, approved, checked_rule_ids,
                    blocking_rule_ids, approved_notional, approved_quantity,
                    rejection_reason, created_at, lane, trigger_set_id,
                    trigger_set_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.risk_decision_id,
                    decision.intent_id,
                    int(decision.approved),
                    json.dumps(decision.checked_rule_ids),
                    json.dumps(decision.blocking_rule_ids),
                    None if decision.approved_notional is None else str(decision.approved_notional),
                    None if decision.approved_quantity is None else str(decision.approved_quantity),
                    decision.rejection_reason,
                    decision.created_at,
                    decision.lane,
                    trigger_set_id,
                    trigger_set_version,
                ),
            )
        approved = bool(decision.approved)
        self.record_audit_event(
            event_type="ENTRY_APPROVED" if approved else "ENTRY_REJECTED",
            source_type="RISK",
            source_id=decision.risk_decision_id,
            scope=decision.lane or "UNKNOWN",
            entity_type="risk_decision",
            entity_id=decision.risk_decision_id,
            related_entity_type="trade_intent",
            related_entity_id=decision.intent_id,
            set_id=trigger_set_id,
            set_version=trigger_set_version,
            result="APPROVED" if approved else "REJECTED",
            reason_code=decision.rejection_reason,
            safe_metadata={
                "checked_rule_ids": decision.checked_rule_ids,
                "blocking_rule_ids": decision.blocking_rule_ids,
                "approved_notional": None if decision.approved_notional is None else str(decision.approved_notional),
                "approved_quantity": None if decision.approved_quantity is None else str(decision.approved_quantity),
                "unsupported_capability_rule_ids": decision.unsupported_capability_rule_ids,
                "net_edge_reason": None if decision.net_edge is None else decision.net_edge.reason,
                "expected_net_edge": None if decision.net_edge is None else str(decision.net_edge.expected_net_edge),
            },
            created_at=decision.created_at,
        )

    def record_audit_event(
        self,
        *,
        event_type: str,
        source_type: str,
        scope: str,
        entity_type: str,
        entity_id: str,
        created_at: str | None = None,
        source_id: str | None = None,
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
        set_id: str | None = None,
        set_version: str | None = None,
        rules_version_id: str | None = None,
        trigger_id: str | None = None,
        trigger_version: str | None = None,
        research_id: str | None = None,
        run_id: str | None = None,
        position_id: str | None = None,
        order_id: str | None = None,
        result: str = "RECORDED",
        reason_code: str | None = None,
        safe_metadata: dict[str, Any] | None = None,
        event_id: str | None = None,
    ) -> AuditEvent:
        created_at = created_at or datetime.now(UTC).isoformat()
        normalized = AuditEvent(
            event_id=_clean_id(
                event_id
                or _audit_event_id(
                    event_type=event_type,
                    created_at=created_at,
                    source_type=source_type,
                    source_id=source_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    result=result,
                ),
                "event_id",
            ),
            created_at=_clean_text(created_at, "created_at", 80),
            event_type=_token(event_type, "event_type"),
            source_type=_token(source_type, "source_type"),
            source_id=_optional_text(source_id, "source_id", 200),
            scope=_token(scope, "scope"),
            entity_type=_token(entity_type, "entity_type"),
            entity_id=_clean_id(entity_id, "entity_id"),
            related_entity_type=_optional_token(related_entity_type, "related_entity_type"),
            related_entity_id=_optional_text(related_entity_id, "related_entity_id", 240),
            set_id=_optional_text(set_id, "set_id", 120),
            set_version=_optional_text(set_version, "set_version", 80),
            rules_version_id=_optional_text(rules_version_id, "rules_version_id", 160),
            trigger_id=_optional_text(trigger_id, "trigger_id", 80),
            trigger_version=_optional_text(trigger_version, "trigger_version", 80),
            research_id=_optional_text(research_id, "research_id", 160),
            run_id=_optional_text(run_id, "run_id", 160),
            position_id=_optional_text(position_id, "position_id", 160),
            order_id=_optional_text(order_id, "order_id", 160),
            result=_token(result, "result"),
            reason_code=_optional_text(reason_code, "reason_code", 240),
            safe_metadata=_safe_metadata(safe_metadata or {}),
        )
        values = _audit_values(normalized)
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM audit_events WHERE event_id = ?", (normalized.event_id,)).fetchone()
            if existing is not None:
                if tuple(existing[key] for key in _AUDIT_COLUMNS) != values:
                    raise TraceStoreError("immutable audit event conflict")
                return normalized
            conn.execute(
                f"INSERT INTO audit_events ({', '.join(_AUDIT_COLUMNS)}) VALUES ({', '.join('?' for _ in _AUDIT_COLUMNS)})",
                values,
            )
        return normalized

    def list_audit_events(
        self,
        *,
        limit: int = 50,
        entity_type: str | None = None,
        entity_id: str | None = None,
        event_type: str | None = None,
    ) -> tuple[AuditEvent, ...]:
        safe_limit = max(1, min(int(limit), 250))
        clauses: list[str] = []
        params: list[Any] = []
        if entity_type is not None:
            clauses.append("entity_type = ?")
            params.append(_token(entity_type, "entity_type"))
        if entity_id is not None:
            clauses.append(
                "(entity_id = ? OR related_entity_id = ? OR position_id = ? OR order_id = ? OR research_id = ? OR run_id = ?)"
            )
            clean = _clean_id(entity_id, "entity_id")
            params.extend([clean] * 6)
        if event_type is not None:
            clauses.append("event_type = ?")
            params.append(_token(event_type, "event_type"))
        where = "" if not clauses else "WHERE " + " AND ".join(clauses)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM audit_events
                {where}
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (*params, safe_limit),
            ).fetchall()
        return tuple(_audit_from_row(row) for row in rows)

    def trace_for_intent(self, intent_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            strategy = conn.execute(
                "SELECT * FROM strategy_decisions WHERE intent_id = ?",
                (intent_id,),
            ).fetchone()
            risk = conn.execute(
                "SELECT * FROM risk_decisions WHERE intent_id = ?",
                (intent_id,),
            ).fetchone()
            signals = []
            if strategy is not None:
                for signal_id in json.loads(strategy["signal_ids"]):
                    signal = conn.execute(
                        "SELECT * FROM trigger_evaluations WHERE signal_id = ?",
                        (signal_id,),
                    ).fetchone()
                    if signal is not None:
                        signals.append(dict(signal))
        return {
            "strategy": None if strategy is None else dict(strategy),
            "risk": None if risk is None else dict(risk),
            "signals": signals,
        }

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trigger_evaluations (
                    signal_id TEXT PRIMARY KEY,
                    trigger_rule_id TEXT NOT NULL,
                    trigger_rule_version TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    window TEXT NOT NULL,
                    input_snapshot TEXT NOT NULL,
                    condition_result INTEGER NOT NULL,
                    signal_type TEXT NOT NULL,
                    lane TEXT,
                    trigger_set_id TEXT,
                    trigger_set_version TEXT
                )
                """
            )
            _add_column_if_missing(conn, "trigger_evaluations", "lane", "TEXT")
            _add_column_if_missing(conn, "trigger_evaluations", "trigger_set_id", "TEXT")
            _add_column_if_missing(conn, "trigger_evaluations", "trigger_set_version", "TEXT")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS strategy_decisions (
                    intent_id TEXT PRIMARY KEY,
                    strategy_rule_id TEXT NOT NULL,
                    strategy_rule_version TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    signal_ids TEXT NOT NULL,
                    trigger_ids TEXT NOT NULL,
                    created_at TEXT,
                    lane TEXT,
                    trigger_set_id TEXT,
                    trigger_set_version TEXT,
                    regime_context_id TEXT,
                    regime_rule_id TEXT,
                    regime_rule_version TEXT,
                    regime_state TEXT
                )
                """
            )
            _add_column_if_missing(conn, "strategy_decisions", "lane", "TEXT")
            _add_column_if_missing(conn, "strategy_decisions", "trigger_set_id", "TEXT")
            _add_column_if_missing(conn, "strategy_decisions", "trigger_set_version", "TEXT")
            _add_column_if_missing(conn, "strategy_decisions", "regime_context_id", "TEXT")
            _add_column_if_missing(conn, "strategy_decisions", "regime_rule_id", "TEXT")
            _add_column_if_missing(conn, "strategy_decisions", "regime_rule_version", "TEXT")
            _add_column_if_missing(conn, "strategy_decisions", "regime_state", "TEXT")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS risk_decisions (
                    risk_decision_id TEXT PRIMARY KEY,
                    intent_id TEXT NOT NULL,
                    approved INTEGER NOT NULL,
                    checked_rule_ids TEXT NOT NULL,
                    blocking_rule_ids TEXT NOT NULL,
                    approved_notional TEXT,
                    approved_quantity TEXT,
                    rejection_reason TEXT,
                    created_at TEXT,
                    lane TEXT,
                    trigger_set_id TEXT,
                    trigger_set_version TEXT
                )
                """
            )
            _add_column_if_missing(conn, "risk_decisions", "lane", "TEXT")
            _add_column_if_missing(conn, "risk_decisions", "trigger_set_id", "TEXT")
            _add_column_if_missing(conn, "risk_decisions", "trigger_set_version", "TEXT")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_id TEXT,
                    scope TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    related_entity_type TEXT,
                    related_entity_id TEXT,
                    set_id TEXT,
                    set_version TEXT,
                    rules_version_id TEXT,
                    trigger_id TEXT,
                    trigger_version TEXT,
                    research_id TEXT,
                    run_id TEXT,
                    position_id TEXT,
                    order_id TEXT,
                    result TEXT NOT NULL,
                    reason_code TEXT,
                    safe_metadata TEXT NOT NULL DEFAULT '{}',
                    schema_version TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_created ON audit_events(created_at DESC, id DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type, created_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_entity ON audit_events(entity_type, entity_id, created_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_research ON audit_events(research_id, created_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_position ON audit_events(position_id, created_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_order ON audit_events(order_id, created_at DESC)")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


class TraceStoreError(RuntimeError):
    pass


_AUDIT_COLUMNS = tuple(field.name for field in fields(AuditEvent))


def _audit_values(event: AuditEvent) -> tuple[Any, ...]:
    values = []
    for key in _AUDIT_COLUMNS:
        value = getattr(event, key)
        if key == "safe_metadata":
            value = json.dumps(value or {}, sort_keys=True)
        values.append(value)
    return tuple(values)


def _audit_from_row(row: sqlite3.Row) -> AuditEvent:
    data = {key: row[key] for key in _AUDIT_COLUMNS}
    data["safe_metadata"] = _json_dict(data["safe_metadata"])
    return AuditEvent(**data)


def _audit_event_id(
    *,
    event_type: str,
    created_at: str,
    source_type: str,
    source_id: str | None,
    entity_type: str,
    entity_id: str,
    result: str,
) -> str:
    digest = sha256("|".join([event_type, created_at, source_type, source_id or "", entity_type, entity_id, result]).encode("utf-8")).hexdigest()[:24]
    return f"audit-{digest}"


def _token(value: str, field: str) -> str:
    text = _clean_text(str(value), field, 80).upper()
    if any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_:-." for char in text):
        raise TraceStoreError(f"invalid {field}")
    return text


def _optional_token(value: str | None, field: str) -> str | None:
    return None if value is None else _token(value, field)


def _clean_id(value: str, field: str) -> str:
    text = _clean_text(value, field, 200)
    if _ID_RE.fullmatch(text) is None or "/" in text or "\\" in text:
        raise TraceStoreError(f"invalid {field}")
    return text


def _optional_text(value: Any, field: str, max_len: int) -> str | None:
    if value is None:
        return None
    text = _clean_text(str(value), field, max_len)
    return "[redacted]" if _SECRET_RE.search(text) else text


def _clean_text(value: str, field: str, max_len: int) -> str:
    text = " ".join(str(value).replace("\x00", "").split())
    if not text:
        raise TraceStoreError(f"{field} is required")
    return text[:max_len]


def _safe_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool | None | list[Any] | dict[str, Any]]:
    safe: dict[str, str | int | float | bool | None | list[Any] | dict[str, Any]] = {}
    for index, (key, value) in enumerate(metadata.items()):
        if index >= 24:
            break
        clean_key = _clean_text(str(key), "metadata key", 80)
        if _SECRET_RE.search(clean_key):
            safe[f"redacted_field_{index}"] = "[redacted]"
            continue
        safe[clean_key] = _safe_metadata_value(value, depth=0)
    return safe


def _safe_metadata_value(value: Any, *, depth: int) -> str | int | float | bool | None | list[Any] | dict[str, Any]:
    if value is None or isinstance(value, bool | int | float):
        return value
    if depth < 2 and isinstance(value, dict):
        result = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 16:
                break
            clean_key = _clean_text(str(key), "metadata key", 80)
            if _SECRET_RE.search(clean_key):
                result[f"redacted_field_{index}"] = "[redacted]"
            else:
                result[clean_key] = _safe_metadata_value(item, depth=depth + 1)
        return result
    if depth < 2 and isinstance(value, (list, tuple)):
        return [_safe_metadata_value(item, depth=depth + 1) for item in value[:16]]
    text = " ".join(str(value).replace("\x00", "").split())[:300]
    if not text:
        return ""
    return "[redacted]" if _SECRET_RE.search(text) else text


def _json_dict(raw: Any) -> dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}
