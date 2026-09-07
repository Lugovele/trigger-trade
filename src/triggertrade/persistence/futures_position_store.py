"""SQLite store for authoritative futures position lifecycle state."""

from __future__ import annotations

from dataclasses import dataclass, fields
from decimal import Decimal
import json
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class FuturesPositionRecord:
    position_id: str
    trade_id: str
    symbol: str
    side: str
    status: str
    opened_at: str
    closed_at: str | None
    entry_price: str
    current_qty: str
    initial_qty: str
    leverage: str
    position_value: str
    tp_price: str
    tp_pct: str
    sl_price: str
    sl_pct: str
    trigger_set_id: str | None
    trigger_set_version: str | None
    strategy_rule_id: str
    strategy_rule_version: str
    risk_rule_version: str
    protective_exit_version: str
    evidence_source: str
    open_intent_id: str
    open_risk_decision_id: str
    open_execution_id: str
    close_intent_id: str | None
    close_risk_decision_id: str | None
    close_execution_id: str | None
    close_reason: str | None
    rule_snapshot: dict[str, str | None]
    updated_at: str
    rules_version_id: str | None = None
    instrument_snapshot: dict[str, str | None] | None = None


@dataclass(frozen=True)
class FuturesPositionEvent:
    event_id: str
    position_id: str
    event_type: str
    occurred_at: str
    reason: str
    execution_id: str | None
    error: str | None


@dataclass(frozen=True)
class FuturesClosedPositionRecord:
    trade_id: str
    position_id: str
    symbol: str
    direction: str
    entry_vwap: str
    exit_vwap: str
    qty: str
    position_value: str
    leverage: str
    planned_tp_pct: str
    planned_tp_price: str
    planned_sl_pct: str
    planned_sl_price: str
    realized_pnl_pct: str
    gross_pnl: str
    fees: str
    funding: str
    net_pnl: str
    opened_at: str
    closed_at: str
    duration_seconds: int
    close_reason: str
    trigger_set_id: str | None
    trigger_set_version: str | None
    strategy_rule_id: str
    strategy_rule_version: str
    risk_rule_version: str
    evidence_source: str
    accounting_version: str
    rules_version_id: str | None = None


class FuturesPositionStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_open_position(self, record: FuturesPositionRecord) -> FuturesPositionRecord:
        with self._connect() as conn:
            existing = self.get_position(record.position_id, conn)
            if existing is not None:
                if existing.open_intent_id != record.open_intent_id:
                    raise ValueError("immutable futures position conflict")
                return existing
            if self.open_position_for_symbol(record.symbol, conn) is not None:
                raise ValueError("one open futures position per symbol is allowed")
            conn.execute(
                f"INSERT INTO futures_positions ({', '.join(_POSITION_COLUMNS)}) VALUES ({', '.join('?' for _ in _POSITION_COLUMNS)})",
                _position_values(record),
            )
        return record

    def mark_closing(self, position_id: str, close_intent_id: str, close_risk_decision_id: str, close_reason: str) -> FuturesPositionRecord:
        with self._connect() as conn:
            current = self.get_position(position_id, conn)
            if current is None:
                raise ValueError("position not found")
            if current.status == "CLOSED":
                return current
            if current.close_intent_id and current.close_intent_id != close_intent_id:
                raise ValueError("position already has a different close intent")
            conn.execute(
                """
                UPDATE futures_positions
                SET status = 'CLOSING', close_intent_id = ?, close_risk_decision_id = ?,
                    close_reason = ?, updated_at = datetime('now')
                WHERE position_id = ?
                """,
                (close_intent_id, close_risk_decision_id, close_reason, position_id),
            )
        return self.get_position(position_id)  # type: ignore[return-value]

    def mark_open(self, position_id: str, updated_at: str) -> FuturesPositionRecord:
        with self._connect() as conn:
            conn.execute(
                "UPDATE futures_positions SET status = 'OPEN', updated_at = ? WHERE position_id = ? AND status = 'UNKNOWN'",
                (updated_at, position_id),
            )
        return self.get_position(position_id)  # type: ignore[return-value]

    def update_open_fill(
        self,
        position_id: str,
        *,
        current_qty: str,
        entry_price: str,
        position_value: str,
        status: str,
        updated_at: str,
    ) -> FuturesPositionRecord:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE futures_positions
                SET current_qty = ?, entry_price = ?, position_value = ?,
                    status = ?, updated_at = ?
                WHERE position_id = ?
                """,
                (current_qty, entry_price, position_value, status, updated_at, position_id),
            )
        return self.get_position(position_id)  # type: ignore[return-value]

    def attach_close_execution(self, position_id: str, close_execution_id: str) -> FuturesPositionRecord:
        with self._connect() as conn:
            conn.execute(
                "UPDATE futures_positions SET close_execution_id = ?, updated_at = datetime('now') WHERE position_id = ?",
                (close_execution_id, position_id),
            )
        return self.get_position(position_id)  # type: ignore[return-value]

    def mark_closed(self, position_id: str, closed_at: str) -> FuturesPositionRecord:
        with self._connect() as conn:
            conn.execute(
                "UPDATE futures_positions SET status = 'CLOSED', closed_at = ?, current_qty = '0', updated_at = ? WHERE position_id = ?",
                (closed_at, closed_at, position_id),
            )
        return self.get_position(position_id)  # type: ignore[return-value]

    def save_closed_position(self, record: FuturesClosedPositionRecord) -> bool:
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM futures_closed_positions WHERE trade_id = ?", (record.trade_id,)).fetchone()
            values = _closed_values(record)
            if existing is not None:
                if tuple(existing[key] for key in _CLOSED_COLUMNS) != values:
                    raise ValueError("immutable futures closed position conflict")
                return False
            conn.execute(
                f"INSERT INTO futures_closed_positions ({', '.join(_CLOSED_COLUMNS)}) VALUES ({', '.join('?' for _ in _CLOSED_COLUMNS)})",
                values,
            )
        return True

    def get_closed_position(self, position_id: str) -> FuturesClosedPositionRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM futures_closed_positions WHERE position_id = ?", (position_id,)).fetchone()
        return None if row is None else _row_to_closed(row)

    def record_event(self, event: FuturesPositionEvent) -> bool:
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM futures_position_events WHERE event_id = ?", (event.event_id,)).fetchone()
            values = (event.event_id, event.position_id, event.event_type, event.occurred_at, event.reason, event.execution_id, event.error)
            if existing is not None:
                if tuple(existing[key] for key in _EVENT_COLUMNS) != values:
                    raise ValueError("immutable futures position event conflict")
                return False
            conn.execute(
                "INSERT INTO futures_position_events (event_id, position_id, event_type, occurred_at, reason, execution_id, error) VALUES (?, ?, ?, ?, ?, ?, ?)",
                values,
            )
        return True

    def get_position(self, position_id: str, conn: sqlite3.Connection | None = None) -> FuturesPositionRecord | None:
        if conn is not None:
            row = conn.execute("SELECT * FROM futures_positions WHERE position_id = ?", (position_id,)).fetchone()
        else:
            with self._connect() as local:
                row = local.execute("SELECT * FROM futures_positions WHERE position_id = ?", (position_id,)).fetchone()
        return None if row is None else _row_to_position(row)

    def open_position_for_symbol(self, symbol: str, conn: sqlite3.Connection | None = None) -> FuturesPositionRecord | None:
        query = "SELECT * FROM futures_positions WHERE symbol = ? AND status IN ('OPEN', 'CLOSING', 'UNKNOWN') LIMIT 1"
        if conn is not None:
            row = conn.execute(query, (symbol,)).fetchone()
        else:
            with self._connect() as local:
                row = local.execute(query, (symbol,)).fetchone()
        return None if row is None else _row_to_position(row)

    def list_open_positions(self, *, include_unknown: bool = False) -> tuple[FuturesPositionRecord, ...]:
        statuses = ("OPEN", "CLOSING", "UNKNOWN") if include_unknown else ("OPEN",)
        placeholders = ", ".join("?" for _ in statuses)
        with self._connect() as conn:
            rows = conn.execute(f"SELECT * FROM futures_positions WHERE status IN ({placeholders}) ORDER BY opened_at", statuses).fetchall()
        return tuple(_row_to_position(row) for row in rows)

    def open_position_count(self) -> int:
        return len(self.list_open_positions())

    def total_open_notional(self) -> Decimal:
        return sum((Decimal(row.position_value) for row in self.list_open_positions()), Decimal("0"))

    def has_unresolved_for_symbol(self, symbol: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM futures_positions WHERE symbol = ? AND status IN ('CLOSING', 'UNKNOWN') LIMIT 1",
                (symbol,),
            ).fetchone()
        return row is not None

    def begin_close_all(self, close_all_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO futures_close_all_operations (close_all_id, status, started_at, completed_at) VALUES (?, 'RUNNING', datetime('now'), NULL)",
                (close_all_id,),
            )

    def complete_close_all(self, close_all_id: str, status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE futures_close_all_operations SET status = ?, completed_at = datetime('now') WHERE close_all_id = ?",
                (status, close_all_id),
            )

    def close_all_running(self) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM futures_close_all_operations WHERE status = 'RUNNING' LIMIT 1").fetchone()
        return row is not None

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS futures_positions (
                    position_id TEXT PRIMARY KEY,
                    trade_id TEXT NOT NULL UNIQUE,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    status TEXT NOT NULL,
                    opened_at TEXT NOT NULL,
                    closed_at TEXT,
                    entry_price TEXT NOT NULL,
                    current_qty TEXT NOT NULL,
                    initial_qty TEXT NOT NULL,
                    leverage TEXT NOT NULL,
                    position_value TEXT NOT NULL,
                    tp_price TEXT NOT NULL,
                    tp_pct TEXT NOT NULL,
                    sl_price TEXT NOT NULL,
                    sl_pct TEXT NOT NULL,
                    trigger_set_id TEXT,
                    trigger_set_version TEXT,
                    strategy_rule_id TEXT NOT NULL,
                    strategy_rule_version TEXT NOT NULL,
                    risk_rule_version TEXT NOT NULL,
                    protective_exit_version TEXT NOT NULL,
                    evidence_source TEXT NOT NULL,
                    open_intent_id TEXT NOT NULL UNIQUE,
                    open_risk_decision_id TEXT NOT NULL,
                    open_execution_id TEXT NOT NULL,
                    close_intent_id TEXT UNIQUE,
                    close_risk_decision_id TEXT,
                    close_execution_id TEXT,
                    close_reason TEXT,
                    rule_snapshot TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    rules_version_id TEXT,
                    instrument_snapshot TEXT
                )
                """
            )
            _add_column_if_missing(conn, "futures_positions", "rules_version_id", "TEXT")
            _add_column_if_missing(conn, "futures_positions", "instrument_snapshot", "TEXT")
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_futures_one_open_per_symbol ON futures_positions(symbol) WHERE status IN ('OPEN', 'CLOSING', 'UNKNOWN')"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS futures_position_events (
                    event_id TEXT PRIMARY KEY,
                    position_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    execution_id TEXT,
                    error TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS futures_closed_positions (
                    trade_id TEXT PRIMARY KEY,
                    position_id TEXT NOT NULL UNIQUE,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_vwap TEXT NOT NULL,
                    exit_vwap TEXT NOT NULL,
                    qty TEXT NOT NULL,
                    position_value TEXT NOT NULL,
                    leverage TEXT NOT NULL,
                    planned_tp_pct TEXT NOT NULL,
                    planned_tp_price TEXT NOT NULL,
                    planned_sl_pct TEXT NOT NULL,
                    planned_sl_price TEXT NOT NULL,
                    realized_pnl_pct TEXT NOT NULL,
                    gross_pnl TEXT NOT NULL,
                    fees TEXT NOT NULL,
                    funding TEXT NOT NULL,
                    net_pnl TEXT NOT NULL,
                    opened_at TEXT NOT NULL,
                    closed_at TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    close_reason TEXT NOT NULL,
                    trigger_set_id TEXT,
                    trigger_set_version TEXT,
                    strategy_rule_id TEXT NOT NULL,
                    strategy_rule_version TEXT NOT NULL,
                    risk_rule_version TEXT NOT NULL,
                    evidence_source TEXT NOT NULL,
                    accounting_version TEXT NOT NULL,
                    rules_version_id TEXT
                )
                """
            )
            _add_column_if_missing(conn, "futures_closed_positions", "rules_version_id", "TEXT")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS futures_close_all_operations (
                    close_all_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


_POSITION_COLUMNS = tuple(field.name for field in fields(FuturesPositionRecord))
_EVENT_COLUMNS = ("event_id", "position_id", "event_type", "occurred_at", "reason", "execution_id", "error")
_CLOSED_COLUMNS = tuple(field.name for field in fields(FuturesClosedPositionRecord))


def _position_values(record: FuturesPositionRecord) -> tuple[str | None, ...]:
    values = []
    for key in _POSITION_COLUMNS:
        if key == "rule_snapshot":
            values.append(json.dumps(record.rule_snapshot, sort_keys=True))
        elif key == "instrument_snapshot":
            values.append(None if record.instrument_snapshot is None else json.dumps(record.instrument_snapshot, sort_keys=True))
        else:
            values.append(getattr(record, key))
    return tuple(values)


def _closed_values(record: FuturesClosedPositionRecord) -> tuple[str | int | None, ...]:
    return tuple(getattr(record, key) for key in _CLOSED_COLUMNS)


def _row_to_position(row: sqlite3.Row) -> FuturesPositionRecord:
    data = {key: row[key] for key in _POSITION_COLUMNS}
    data["rule_snapshot"] = json.loads(data["rule_snapshot"])
    data["instrument_snapshot"] = None if data.get("instrument_snapshot") in {None, ""} else json.loads(data["instrument_snapshot"])
    return FuturesPositionRecord(**data)


def _row_to_closed(row: sqlite3.Row) -> FuturesClosedPositionRecord:
    return FuturesClosedPositionRecord(**{key: row[key] for key in _CLOSED_COLUMNS})


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
