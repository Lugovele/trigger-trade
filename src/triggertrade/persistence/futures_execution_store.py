"""SQLite futures execution audit trail."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Iterable

from triggertrade.execution.contracts import OrderStatus


@dataclass(frozen=True)
class FuturesExecutionRecord:
    intent_id: str
    risk_decision_id: str
    client_order_id: str
    exchange_order_id: str | None
    symbol: str
    category: str
    position_action: str
    exchange_side: str
    order_type: str
    requested_qty: str
    requested_price: str
    leverage: str
    status: OrderStatus
    created_at: str
    updated_at: str
    margin_mode: str
    position_mode: str
    cost_model_version: str | None = None
    net_edge_model_version: str | None = None
    expected_net_edge: str | None = None
    exchange_status: str | None = None
    reconciliation_state: str | None = None
    last_error_code: str | None = None
    lane: str | None = None
    trigger_set_id: str | None = None
    trigger_set_version: str | None = None


class FuturesExecutionStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def reserve(self, record: FuturesExecutionRecord) -> tuple[FuturesExecutionRecord, bool]:
        with self._connect() as conn:
            existing = self.get_by_intent(record.intent_id, conn)
            if existing is not None:
                return existing, False
            try:
                conn.execute(
                    """
                    INSERT INTO futures_execution_orders (
                        intent_id, risk_decision_id, client_order_id, exchange_order_id,
                        symbol, category, position_action, exchange_side, order_type,
                        requested_qty, requested_price, leverage, status, created_at,
                        updated_at, margin_mode, position_mode, cost_model_version,
                        net_edge_model_version, expected_net_edge, exchange_status,
                        reconciliation_state, last_error_code, lane, trigger_set_id,
                        trigger_set_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    _record_values(record),
                )
            except sqlite3.IntegrityError:
                collided = (
                    self.get_by_intent(record.intent_id, conn)
                    or self._fetch_one(
                        "SELECT * FROM futures_execution_orders WHERE client_order_id = ?",
                        (record.client_order_id,),
                        conn,
                    )
                    or self._fetch_one(
                        "SELECT * FROM futures_execution_orders WHERE risk_decision_id = ?",
                        (record.risk_decision_id,),
                        conn,
                    )
                )
                if collided is not None:
                    return collided, False
                raise
            return record, True

    def update(self, record: FuturesExecutionRecord) -> FuturesExecutionRecord:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE futures_execution_orders
                SET risk_decision_id = ?, client_order_id = ?, exchange_order_id = ?,
                    symbol = ?, category = ?, position_action = ?, exchange_side = ?,
                    order_type = ?, requested_qty = ?, requested_price = ?, leverage = ?,
                    status = ?, updated_at = ?, margin_mode = ?, position_mode = ?,
                    cost_model_version = ?, net_edge_model_version = ?, expected_net_edge = ?,
                    exchange_status = ?, reconciliation_state = ?, last_error_code = ?,
                    lane = ?, trigger_set_id = ?, trigger_set_version = ?
                WHERE intent_id = ?
                """,
                (
                    record.risk_decision_id,
                    record.client_order_id,
                    record.exchange_order_id,
                    record.symbol,
                    record.category,
                    record.position_action,
                    record.exchange_side,
                    record.order_type,
                    record.requested_qty,
                    record.requested_price,
                    record.leverage,
                    record.status.value,
                    record.updated_at,
                    record.margin_mode,
                    record.position_mode,
                    record.cost_model_version,
                    record.net_edge_model_version,
                    record.expected_net_edge,
                    record.exchange_status,
                    record.reconciliation_state,
                    record.last_error_code,
                    record.lane,
                    record.trigger_set_id,
                    record.trigger_set_version,
                    record.intent_id,
                ),
            )
        return record

    def get_by_intent(self, intent_id: str, conn: sqlite3.Connection | None = None) -> FuturesExecutionRecord | None:
        return self._fetch_one("SELECT * FROM futures_execution_orders WHERE intent_id = ?", (intent_id,), conn)

    def get_by_client_order_id(self, client_order_id: str) -> FuturesExecutionRecord | None:
        return self._fetch_one(
            "SELECT * FROM futures_execution_orders WHERE client_order_id = ?",
            (client_order_id,),
            None,
        )

    def unresolved(self) -> tuple[FuturesExecutionRecord, ...]:
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
                f"SELECT * FROM futures_execution_orders WHERE status IN ({placeholders})",
                statuses,
            ).fetchall()
        return tuple(_row_to_record(row) for row in rows)

    def list_recent(self, limit: int = 20) -> tuple[FuturesExecutionRecord, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM futures_execution_orders ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return tuple(_row_to_record(row) for row in rows)

    def _fetch_one(
        self,
        query: str,
        values: Iterable[str],
        conn: sqlite3.Connection | None,
    ) -> FuturesExecutionRecord | None:
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
                CREATE TABLE IF NOT EXISTS futures_execution_orders (
                    intent_id TEXT PRIMARY KEY,
                    risk_decision_id TEXT NOT NULL UNIQUE,
                    client_order_id TEXT NOT NULL UNIQUE,
                    exchange_order_id TEXT,
                    symbol TEXT NOT NULL,
                    category TEXT NOT NULL,
                    position_action TEXT NOT NULL,
                    exchange_side TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    requested_qty TEXT NOT NULL,
                    requested_price TEXT NOT NULL,
                    leverage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    margin_mode TEXT NOT NULL,
                    position_mode TEXT NOT NULL,
                    cost_model_version TEXT,
                    net_edge_model_version TEXT,
                    expected_net_edge TEXT,
                    exchange_status TEXT,
                    reconciliation_state TEXT,
                    last_error_code TEXT,
                    lane TEXT,
                    trigger_set_id TEXT,
                    trigger_set_version TEXT
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


def _record_values(record: FuturesExecutionRecord) -> tuple[str | None, ...]:
    return (
        record.intent_id,
        record.risk_decision_id,
        record.client_order_id,
        record.exchange_order_id,
        record.symbol,
        record.category,
        record.position_action,
        record.exchange_side,
        record.order_type,
        record.requested_qty,
        record.requested_price,
        record.leverage,
        record.status.value,
        record.created_at,
        record.updated_at,
        record.margin_mode,
        record.position_mode,
        record.cost_model_version,
        record.net_edge_model_version,
        record.expected_net_edge,
        record.exchange_status,
        record.reconciliation_state,
        record.last_error_code,
        record.lane,
        record.trigger_set_id,
        record.trigger_set_version,
    )


def _row_to_record(row: sqlite3.Row) -> FuturesExecutionRecord:
    return FuturesExecutionRecord(
        intent_id=row["intent_id"],
        risk_decision_id=row["risk_decision_id"],
        client_order_id=row["client_order_id"],
        exchange_order_id=row["exchange_order_id"],
        symbol=row["symbol"],
        category=row["category"],
        position_action=row["position_action"],
        exchange_side=row["exchange_side"],
        order_type=row["order_type"],
        requested_qty=row["requested_qty"],
        requested_price=row["requested_price"],
        leverage=row["leverage"],
        status=OrderStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        margin_mode=row["margin_mode"],
        position_mode=row["position_mode"],
        cost_model_version=row["cost_model_version"],
        net_edge_model_version=row["net_edge_model_version"],
        expected_net_edge=row["expected_net_edge"],
        exchange_status=row["exchange_status"],
        reconciliation_state=row["reconciliation_state"],
        last_error_code=row["last_error_code"],
        lane=row["lane"],
        trigger_set_id=row["trigger_set_id"],
        trigger_set_version=row["trigger_set_version"],
    )
