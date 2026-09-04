"""SQLite execution audit trail and idempotency store."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterable

from triggertrade.execution.contracts import OrderStatus


@dataclass(frozen=True)
class ExecutionRecord:
    intent_id: str
    risk_decision_id: str
    client_order_id: str
    exchange_order_id: str | None
    symbol: str
    side: str
    order_type: str
    requested_qty: str
    requested_price: str
    status: OrderStatus
    created_at: str
    updated_at: str
    exchange_status: str | None = None
    reconciliation_state: str | None = None
    last_error_code: str | None = None


@dataclass(frozen=True)
class ExecutionFill:
    fill_id: str
    intent_id: str
    client_order_id: str
    symbol: str
    side: str
    quantity: str
    price: str
    fee: str
    created_at: str


class ExecutionStore:
    def __init__(self, path: str | Path = "runtime/triggertrade.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def reserve(self, record: ExecutionRecord) -> tuple[ExecutionRecord, bool]:
        with self._connect() as conn:
            existing = self.get_by_intent(record.intent_id, conn)
            if existing is not None:
                return existing, False
            try:
                conn.execute(
                    """
                    INSERT INTO execution_orders (
                        intent_id, risk_decision_id, client_order_id, exchange_order_id,
                        symbol, side, order_type, requested_qty, requested_price, status,
                        created_at, updated_at, exchange_status, reconciliation_state,
                        last_error_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    _record_values(record),
                )
            except sqlite3.IntegrityError:
                collided = (
                    self.get_by_intent(record.intent_id, conn)
                    or self._fetch_one(
                        "SELECT * FROM execution_orders WHERE client_order_id = ?",
                        (record.client_order_id,),
                        conn,
                    )
                    or self._fetch_one(
                        "SELECT * FROM execution_orders WHERE risk_decision_id = ?",
                        (record.risk_decision_id,),
                        conn,
                    )
                )
                if collided is not None:
                    return collided, False
                raise
            return record, True

    def update(self, record: ExecutionRecord) -> ExecutionRecord:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE execution_orders
                SET risk_decision_id = ?, client_order_id = ?, exchange_order_id = ?,
                    symbol = ?, side = ?, order_type = ?, requested_qty = ?,
                    requested_price = ?, status = ?, updated_at = ?,
                    exchange_status = ?, reconciliation_state = ?, last_error_code = ?
                WHERE intent_id = ?
                """,
                (
                    record.risk_decision_id,
                    record.client_order_id,
                    record.exchange_order_id,
                    record.symbol,
                    record.side,
                    record.order_type,
                    record.requested_qty,
                    record.requested_price,
                    record.status.value,
                    record.updated_at,
                    record.exchange_status,
                    record.reconciliation_state,
                    record.last_error_code,
                    record.intent_id,
                ),
            )
        return record

    def get_by_intent(
        self,
        intent_id: str,
        conn: sqlite3.Connection | None = None,
    ) -> ExecutionRecord | None:
        return self._fetch_one(
            "SELECT * FROM execution_orders WHERE intent_id = ?",
            (intent_id,),
            conn,
        )

    def get_by_client_order_id(self, client_order_id: str) -> ExecutionRecord | None:
        return self._fetch_one(
            "SELECT * FROM execution_orders WHERE client_order_id = ?",
            (client_order_id,),
            None,
        )

    def count_by_client_order_id(self, client_order_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM execution_orders WHERE client_order_id = ?",
                (client_order_id,),
            ).fetchone()
        return int(row[0])

    def unresolved(self) -> tuple[ExecutionRecord, ...]:
        statuses = (
            OrderStatus.CREATED.value,
            OrderStatus.SUBMITTING.value,
            OrderStatus.SUBMITTED.value,
            OrderStatus.PARTIALLY_FILLED.value,
            OrderStatus.CANCEL_PENDING.value,
            OrderStatus.UNKNOWN.value,
        )
        placeholders = ", ".join("?" for _ in statuses)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM execution_orders WHERE status IN ({placeholders})",
                statuses,
            ).fetchall()
        return tuple(_row_to_record(row) for row in rows)

    def save_fill(self, fill: ExecutionFill) -> ExecutionFill:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO execution_fills (
                    fill_id, intent_id, client_order_id, symbol, side,
                    quantity, price, fee, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fill.fill_id,
                    fill.intent_id,
                    fill.client_order_id,
                    fill.symbol,
                    fill.side,
                    fill.quantity,
                    fill.price,
                    fill.fee,
                    fill.created_at,
                ),
            )
        return fill

    def fills_for_intent(self, intent_id: str) -> tuple[ExecutionFill, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM execution_fills WHERE intent_id = ? ORDER BY created_at, fill_id",
                (intent_id,),
            ).fetchall()
        return tuple(_row_to_fill(row) for row in rows)

    def _fetch_one(
        self,
        query: str,
        values: Iterable[str],
        conn: sqlite3.Connection | None,
    ) -> ExecutionRecord | None:
        if conn is not None:
            row = conn.execute(query, tuple(values)).fetchone()
        else:
            with self._connect() as local_conn:
                row = local_conn.execute(query, tuple(values)).fetchone()
        return None if row is None else _row_to_record(row)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_orders (
                    intent_id TEXT PRIMARY KEY,
                    risk_decision_id TEXT NOT NULL UNIQUE,
                    client_order_id TEXT NOT NULL UNIQUE,
                    exchange_order_id TEXT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    requested_qty TEXT NOT NULL,
                    requested_price TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    exchange_status TEXT,
                    reconciliation_state TEXT,
                    last_error_code TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_fills (
                    fill_id TEXT PRIMARY KEY,
                    intent_id TEXT NOT NULL,
                    client_order_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity TEXT NOT NULL,
                    price TEXT NOT NULL,
                    fee TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


def _record_values(record: ExecutionRecord) -> tuple[str | None, ...]:
    return (
        record.intent_id,
        record.risk_decision_id,
        record.client_order_id,
        record.exchange_order_id,
        record.symbol,
        record.side,
        record.order_type,
        record.requested_qty,
        record.requested_price,
        record.status.value,
        record.created_at,
        record.updated_at,
        record.exchange_status,
        record.reconciliation_state,
        record.last_error_code,
    )


def _row_to_record(row: sqlite3.Row) -> ExecutionRecord:
    return ExecutionRecord(
        intent_id=row["intent_id"],
        risk_decision_id=row["risk_decision_id"],
        client_order_id=row["client_order_id"],
        exchange_order_id=row["exchange_order_id"],
        symbol=row["symbol"],
        side=row["side"],
        order_type=row["order_type"],
        requested_qty=row["requested_qty"],
        requested_price=row["requested_price"],
        status=OrderStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        exchange_status=row["exchange_status"],
        reconciliation_state=row["reconciliation_state"],
        last_error_code=row["last_error_code"],
    )


def _row_to_fill(row: sqlite3.Row) -> ExecutionFill:
    return ExecutionFill(
        fill_id=row["fill_id"],
        intent_id=row["intent_id"],
        client_order_id=row["client_order_id"],
        symbol=row["symbol"],
        side=row["side"],
        quantity=row["quantity"],
        price=row["price"],
        fee=row["fee"],
        created_at=row["created_at"],
    )
