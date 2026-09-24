"""PostgreSQL-backed futures execution, position, and accounting stores."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from triggertrade.accounting import ClosedTradeResult, EquitySnapshot, FuturesFillEvent, FuturesFundingEvent
from triggertrade.execution.contracts import OrderStatus
from triggertrade.execution.futures import PositionState
from triggertrade.persistence.futures_accounting_store import (
    _closed_trade_values,
    _equity_values,
    _fill_values,
    _funding_values,
)
from triggertrade.persistence.futures_execution_store import FuturesExecutionRecord
from triggertrade.persistence.futures_position_store import (
    FuturesClosedPositionRecord,
    FuturesPositionEvent,
    FuturesPositionRecord,
)
from triggertrade.persistence.operator_state_store import OperatorActionAudit, OperatorTradingState, TradingState
from triggertrade.persistence.postgres import OwnerStateStore, PostgresConnectionFactory, PostgresPersistenceError, PostgresUnitOfWork


_EXECUTION_OWNER = "FuturesExecution"
_EXECUTION_STATE = "FUTURES_EXECUTION_ORDER"
_POSITION_OWNER = "FuturesPosition"
_POSITION_STATE = "FUTURES_POSITION"
_POSITION_EVENT_STATE = "FUTURES_POSITION_EVENT"
_CLOSED_POSITION_STATE = "FUTURES_CLOSED_POSITION"
_CLOSE_ALL_STATE = "FUTURES_CLOSE_ALL_OPERATION"
_ACCOUNTING_OWNER = "FuturesAccounting"
_FILL_STATE = "FUTURES_ACCOUNTING_FILL"
_FUNDING_STATE = "FUTURES_ACCOUNTING_FUNDING"
_CLOSED_TRADE_STATE = "FUTURES_CLOSED_TRADE"
_EQUITY_STATE = "FUTURES_EQUITY_SNAPSHOT"
_OPERATOR_OWNER = "OperatorState"
_TRADING_STATE = "TRADING_STATE"
_ACTION_AUDIT_STATE = "OPERATOR_ACTION_AUDIT"


class PostgresFuturesExecutionStore:
    """Canonical futures execution evidence over OwnerStateStore."""

    __triggertrade_lifecycle_store_role__ = "postgres_canonical_futures_execution"

    def __init__(self, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def reserve(self, record: FuturesExecutionRecord) -> tuple[FuturesExecutionRecord, bool]:
        with PostgresUnitOfWork(self._factory) as uow:
            _advisory_lock(uow.connection, "futures-execution-intent", record.intent_id)
            _advisory_lock(uow.connection, "futures-execution-client-order", record.client_order_id)
            _advisory_lock(uow.connection, "futures-execution-risk", record.risk_decision_id)
            existing = self._get_by_intent(record.intent_id, uow.connection)
            if existing is not None:
                return existing, False
            collided = self._find_one(
                uow.connection,
                _EXECUTION_STATE,
                lambda payload: payload.get("client_order_id") == record.client_order_id
                or payload.get("risk_decision_id") == record.risk_decision_id,
            )
            if collided is not None:
                return _execution_from_payload(collided), False
            owner, created = OwnerStateStore(uow.connection).put_if_absent(
                owner=_EXECUTION_OWNER,
                state_type=_EXECUTION_STATE,
                state_id=record.intent_id,
                payload=_execution_payload(record),
            )
            return _execution_from_payload(owner.payload), created

    def update(self, record: FuturesExecutionRecord) -> FuturesExecutionRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            owner = OwnerStateStore(uow.connection)
            current = owner.get(owner=_EXECUTION_OWNER, state_type=_EXECUTION_STATE, state_id=record.intent_id)
            if current is None:
                persisted, _ = owner.put_if_absent(
                    owner=_EXECUTION_OWNER,
                    state_type=_EXECUTION_STATE,
                    state_id=record.intent_id,
                    payload=_execution_payload(record),
                )
                return _execution_from_payload(persisted.payload)
            updated = owner.compare_and_set(
                owner=_EXECUTION_OWNER,
                state_type=_EXECUTION_STATE,
                state_id=record.intent_id,
                expected_revision=current.revision,
                payload=_execution_payload(record),
            )
            return _execution_from_payload(updated.payload)

    def get_by_intent(self, intent_id: str, conn=None) -> FuturesExecutionRecord | None:
        if conn is not None:
            return self._get_by_intent(intent_id, conn)
        with PostgresUnitOfWork(self._factory) as uow:
            return self._get_by_intent(intent_id, uow.connection)

    def get_by_client_order_id(self, client_order_id: str) -> FuturesExecutionRecord | None:
        with PostgresUnitOfWork(self._factory) as uow:
            payload = self._find_one(
                uow.connection,
                _EXECUTION_STATE,
                lambda item: item.get("client_order_id") == client_order_id,
            )
        return None if payload is None else _execution_from_payload(payload)

    def unresolved(self) -> tuple[FuturesExecutionRecord, ...]:
        statuses = {"created", "submitting", "submitted", "partially_filled", "cancel_pending", "unknown"}
        with PostgresUnitOfWork(self._factory) as uow:
            payloads = _list_payloads(uow.connection, owner=_EXECUTION_OWNER, state_type=_EXECUTION_STATE)
        return tuple(
            _execution_from_payload(payload)
            for payload in payloads
            if str(payload.get("status") or "").lower() in statuses
        )

    def list_recent(self, limit: int = 20) -> tuple[FuturesExecutionRecord, ...]:
        with PostgresUnitOfWork(self._factory) as uow:
            payloads = _list_payloads(uow.connection, owner=_EXECUTION_OWNER, state_type=_EXECUTION_STATE)
        rows = sorted(payloads, key=lambda item: str(item.get("updated_at") or ""), reverse=True)
        return tuple(_execution_from_payload(payload) for payload in rows[: max(1, int(limit))])

    def _get_by_intent(self, intent_id: str, conn) -> FuturesExecutionRecord | None:
        record = OwnerStateStore(conn).get(owner=_EXECUTION_OWNER, state_type=_EXECUTION_STATE, state_id=intent_id)
        return None if record is None else _execution_from_payload(record.payload)

    def _find_one(self, conn, state_type: str, predicate) -> dict[str, Any] | None:
        for payload in _list_payloads(conn, owner=_EXECUTION_OWNER, state_type=state_type):
            if predicate(payload):
                return payload
        return None


class PostgresFuturesPositionStore:
    """Canonical futures position lifecycle state over OwnerStateStore."""

    def __init__(self, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def save_open_position(self, record: FuturesPositionRecord) -> FuturesPositionRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            _advisory_lock(uow.connection, "futures-position", record.position_id)
            _advisory_lock(uow.connection, "futures-position-symbol", record.symbol)
            existing = self._get_position(record.position_id, uow.connection)
            if existing is not None:
                if existing.open_intent_id != record.open_intent_id:
                    raise ValueError("immutable futures position conflict")
                return existing
            if self._open_position_for_symbol(record.symbol, uow.connection) is not None:
                raise ValueError("one open futures position per symbol is allowed")
            owner, _ = OwnerStateStore(uow.connection).put_if_absent(
                owner=_POSITION_OWNER,
                state_type=_POSITION_STATE,
                state_id=record.position_id,
                payload=_position_payload(record),
            )
            return _position_from_payload(owner.payload)

    def mark_closing(self, position_id: str, close_intent_id: str, close_risk_decision_id: str, close_reason: str) -> FuturesPositionRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            position = self._get_position(position_id, uow.connection)
            if position is None:
                raise ValueError("position not found")
            if position.status == "CLOSED":
                return position
            if position.close_intent_id and position.close_intent_id != close_intent_id:
                raise ValueError("position already has a different close intent")
            updated = FuturesPositionRecord(
                **{
                    **position.__dict__,
                    "status": "CLOSING",
                    "close_intent_id": close_intent_id,
                    "close_risk_decision_id": close_risk_decision_id,
                    "close_reason": close_reason,
                    "updated_at": _now(),
                }
            )
            return self._put_position(updated, uow.connection)

    def mark_open(self, position_id: str, updated_at: str) -> FuturesPositionRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            position = self._get_position(position_id, uow.connection)
            if position is None:
                raise ValueError("position not found")
            if position.status != "UNKNOWN":
                return position
            updated = FuturesPositionRecord(**{**position.__dict__, "status": "OPEN", "updated_at": updated_at})
            return self._put_position(updated, uow.connection)

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
        with PostgresUnitOfWork(self._factory) as uow:
            position = self._get_position(position_id, uow.connection)
            if position is None:
                raise ValueError("position not found")
            updated = FuturesPositionRecord(
                **{
                    **position.__dict__,
                    "current_qty": current_qty,
                    "entry_price": entry_price,
                    "position_value": position_value,
                    "status": status,
                    "updated_at": updated_at,
                }
            )
            return self._put_position(updated, uow.connection)

    def attach_close_execution(self, position_id: str, close_execution_id: str) -> FuturesPositionRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            position = self._get_position(position_id, uow.connection)
            if position is None:
                raise ValueError("position not found")
            updated = FuturesPositionRecord(
                **{**position.__dict__, "close_execution_id": close_execution_id, "updated_at": _now()}
            )
            return self._put_position(updated, uow.connection)

    def mark_closed(self, position_id: str, closed_at: str) -> FuturesPositionRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            position = self._get_position(position_id, uow.connection)
            if position is None:
                raise ValueError("position not found")
            closed = self._get_closed_position(position_id, uow.connection)
            if closed is None:
                raise ValueError("closed position evidence is required before CLOSED transition")
            updated = FuturesPositionRecord(
                **{
                    **position.__dict__,
                    "status": "CLOSED",
                    "closed_at": closed_at,
                    "current_qty": "0",
                    "updated_at": closed_at,
                }
            )
            return self._put_position(updated, uow.connection)

    def save_closed_position(self, record: FuturesClosedPositionRecord) -> bool:
        values = _closed_position_payload(record)
        with PostgresUnitOfWork(self._factory) as uow:
            owner = OwnerStateStore(uow.connection)
            existing = owner.get(owner=_POSITION_OWNER, state_type=_CLOSED_POSITION_STATE, state_id=record.trade_id)
            if existing is not None:
                if existing.payload != values:
                    raise ValueError("immutable futures closed position conflict")
                return False
            owner.put_if_absent(
                owner=_POSITION_OWNER,
                state_type=_CLOSED_POSITION_STATE,
                state_id=record.trade_id,
                payload=values,
            )
            return True

    def get_closed_position(self, position_id: str) -> FuturesClosedPositionRecord | None:
        with PostgresUnitOfWork(self._factory) as uow:
            return self._get_closed_position(position_id, uow.connection)

    def record_event(self, event: FuturesPositionEvent) -> bool:
        payload = _position_event_payload(event)
        with PostgresUnitOfWork(self._factory) as uow:
            owner = OwnerStateStore(uow.connection)
            existing = owner.get(owner=_POSITION_OWNER, state_type=_POSITION_EVENT_STATE, state_id=event.event_id)
            if existing is not None:
                if existing.payload != payload:
                    raise ValueError("immutable futures position event conflict")
                return False
            owner.put_if_absent(
                owner=_POSITION_OWNER,
                state_type=_POSITION_EVENT_STATE,
                state_id=event.event_id,
                payload=payload,
            )
            return True

    def get_position(self, position_id: str, conn=None) -> FuturesPositionRecord | None:
        if conn is not None:
            return self._get_position(position_id, conn)
        with PostgresUnitOfWork(self._factory) as uow:
            return self._get_position(position_id, uow.connection)

    def open_position_for_symbol(self, symbol: str, conn=None) -> FuturesPositionRecord | None:
        if conn is not None:
            return self._open_position_for_symbol(symbol, conn)
        with PostgresUnitOfWork(self._factory) as uow:
            return self._open_position_for_symbol(symbol, uow.connection)

    def list_open_positions(self, *, include_unknown: bool = False) -> tuple[FuturesPositionRecord, ...]:
        statuses = {"OPEN", "CLOSING", "UNKNOWN"} if include_unknown else {"OPEN"}
        with PostgresUnitOfWork(self._factory) as uow:
            rows = [
                _position_from_payload(payload)
                for payload in _list_payloads(uow.connection, owner=_POSITION_OWNER, state_type=_POSITION_STATE)
            ]
        return tuple(sorted((row for row in rows if row.status in statuses), key=lambda item: item.opened_at))

    def open_position_count(self) -> int:
        return len(self.list_open_positions())

    def total_open_notional(self) -> Decimal:
        return sum((Decimal(row.position_value) for row in self.list_open_positions()), Decimal("0"))

    def has_unresolved_for_symbol(self, symbol: str) -> bool:
        return self.open_position_for_symbol(symbol) is not None

    def begin_close_all(self, close_all_id: str) -> None:
        with PostgresUnitOfWork(self._factory) as uow:
            OwnerStateStore(uow.connection).put_if_absent(
                owner=_POSITION_OWNER,
                state_type=_CLOSE_ALL_STATE,
                state_id=close_all_id,
                payload={"close_all_id": close_all_id, "status": "RUNNING", "started_at": _now(), "completed_at": None},
            )

    def complete_close_all(self, close_all_id: str, status: str) -> None:
        with PostgresUnitOfWork(self._factory) as uow:
            owner = OwnerStateStore(uow.connection)
            current = owner.get(owner=_POSITION_OWNER, state_type=_CLOSE_ALL_STATE, state_id=close_all_id)
            completed = status in {"completed", "completed_with_failures"}
            payload = {
                "close_all_id": close_all_id,
                "status": status,
                "started_at": _now(),
                "completed_at": _now() if completed else None,
            }
            if current is None:
                owner.put_if_absent(owner=_POSITION_OWNER, state_type=_CLOSE_ALL_STATE, state_id=close_all_id, payload=payload)
            else:
                payload["started_at"] = str(current.payload.get("started_at") or payload["started_at"])
                owner.compare_and_set(
                    owner=_POSITION_OWNER,
                    state_type=_CLOSE_ALL_STATE,
                    state_id=close_all_id,
                    expected_revision=current.revision,
                    payload=payload,
                )

    def close_all_running(self) -> bool:
        with PostgresUnitOfWork(self._factory) as uow:
            return any(
                str(payload.get("status") or "").upper() in {"RUNNING", "IN_PROGRESS"}
                for payload in _list_payloads(uow.connection, owner=_POSITION_OWNER, state_type=_CLOSE_ALL_STATE)
            )

    def _get_position(self, position_id: str, conn) -> FuturesPositionRecord | None:
        record = OwnerStateStore(conn).get(owner=_POSITION_OWNER, state_type=_POSITION_STATE, state_id=position_id)
        return None if record is None else _position_from_payload(record.payload)

    def _get_closed_position(self, position_id: str, conn) -> FuturesClosedPositionRecord | None:
        for payload in _list_payloads(conn, owner=_POSITION_OWNER, state_type=_CLOSED_POSITION_STATE):
            if payload.get("position_id") == position_id:
                return _closed_position_from_payload(payload)
        return None

    def _open_position_for_symbol(self, symbol: str, conn) -> FuturesPositionRecord | None:
        for payload in _list_payloads(conn, owner=_POSITION_OWNER, state_type=_POSITION_STATE):
            if payload.get("symbol") == symbol and payload.get("status") in {"OPEN", "CLOSING", "UNKNOWN"}:
                return _position_from_payload(payload)
        return None

    def _put_position(self, record: FuturesPositionRecord, conn) -> FuturesPositionRecord:
        owner = OwnerStateStore(conn)
        current = owner.get(owner=_POSITION_OWNER, state_type=_POSITION_STATE, state_id=record.position_id)
        if current is None:
            persisted, _ = owner.put_if_absent(
                owner=_POSITION_OWNER,
                state_type=_POSITION_STATE,
                state_id=record.position_id,
                payload=_position_payload(record),
            )
        else:
            persisted = owner.compare_and_set(
                owner=_POSITION_OWNER,
                state_type=_POSITION_STATE,
                state_id=record.position_id,
                expected_revision=current.revision,
                payload=_position_payload(record),
            )
        return _position_from_payload(persisted.payload)


class PostgresFuturesAccountingStore:
    """Canonical immutable futures accounting evidence over OwnerStateStore."""

    def __init__(self, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def record_fill(self, event: FuturesFillEvent) -> bool:
        return self._put_immutable(_FILL_STATE, event.event_id, _fill_payload(event), "immutable futures fill event conflict")

    def record_funding(self, event: FuturesFundingEvent) -> bool:
        return self._put_immutable(_FUNDING_STATE, event.event_id, _funding_payload(event), "immutable futures funding event conflict")

    def record_closed_trade(self, result: ClosedTradeResult) -> bool:
        return self._put_immutable(_CLOSED_TRADE_STATE, result.trade_id, _closed_trade_payload(result), "immutable futures closed trade conflict")

    def record_equity_snapshot(self, snapshot: EquitySnapshot) -> bool:
        return self._put_immutable(_EQUITY_STATE, snapshot.snapshot_id, _equity_payload(snapshot), "immutable futures equity snapshot conflict")

    def list_fills(self, trade_id: str) -> tuple[FuturesFillEvent, ...]:
        with PostgresUnitOfWork(self._factory) as uow:
            rows = [
                _fill_from_payload(payload)
                for payload in _list_payloads(uow.connection, owner=_ACCOUNTING_OWNER, state_type=_FILL_STATE)
                if payload.get("trade_id") == trade_id
            ]
        return tuple(sorted(rows, key=lambda row: (row.occurred_at, row.event_id)))

    def list_funding(self, trade_id: str) -> tuple[FuturesFundingEvent, ...]:
        with PostgresUnitOfWork(self._factory) as uow:
            rows = [
                _funding_from_payload(payload)
                for payload in _list_payloads(uow.connection, owner=_ACCOUNTING_OWNER, state_type=_FUNDING_STATE)
                if payload.get("trade_id") == trade_id
            ]
        return tuple(sorted(rows, key=lambda row: (row.funding_time, row.event_id)))

    def list_closed_trades(self, limit: int = 20) -> tuple[dict[str, Any], ...]:
        with PostgresUnitOfWork(self._factory) as uow:
            rows = _list_payloads(uow.connection, owner=_ACCOUNTING_OWNER, state_type=_CLOSED_TRADE_STATE)
        return tuple(sorted(rows, key=lambda item: str(item.get("closed_at") or ""), reverse=True)[: max(1, int(limit))])

    def latest_equity_snapshot(self) -> dict[str, Any] | None:
        with PostgresUnitOfWork(self._factory) as uow:
            rows = _list_payloads(uow.connection, owner=_ACCOUNTING_OWNER, state_type=_EQUITY_STATE)
        if not rows:
            return None
        return sorted(rows, key=lambda item: (str(item.get("observed_at") or ""), str(item.get("snapshot_id") or "")), reverse=True)[0]

    def first_equity_snapshot_for_utc_day(self, trading_day: str) -> dict[str, Any] | None:
        start, end = _utc_day_bounds(trading_day)
        with PostgresUnitOfWork(self._factory) as uow:
            rows = _list_payloads(uow.connection, owner=_ACCOUNTING_OWNER, state_type=_EQUITY_STATE)
        candidates = [
            row
            for row in rows
            if start <= str(row.get("observed_at") or "") < end
            and str(row.get("source") or "exchange_wallet").upper() in {"ACTIVE", "EXCHANGE", "EXCHANGE_WALLET", "BYBIT_DEMO_ACCOUNT"}
        ]
        return None if not candidates else sorted(candidates, key=lambda item: (str(item.get("observed_at") or ""), str(item.get("snapshot_id") or "")))[0]

    def realized_net_pnl_for_utc_day(self, trading_day: str) -> Decimal:
        start, end = _utc_day_bounds(trading_day)
        with PostgresUnitOfWork(self._factory) as uow:
            rows = _list_payloads(uow.connection, owner=_ACCOUNTING_OWNER, state_type=_CLOSED_TRADE_STATE)
        return sum(
            (
                Decimal(str(row.get("net_pnl") or "0"))
                for row in rows
                if start <= str(row.get("closed_at") or "") < end
                and str(row.get("evidence_source") or "exchange").upper() in {"ACTIVE", "EXCHANGE"}
            ),
            Decimal("0"),
        )

    def _put_immutable(self, state_type: str, state_id: str, payload: dict[str, Any], conflict_message: str) -> bool:
        with PostgresUnitOfWork(self._factory) as uow:
            owner = OwnerStateStore(uow.connection)
            existing = owner.get(owner=_ACCOUNTING_OWNER, state_type=state_type, state_id=state_id)
            if existing is not None:
                if existing.payload != payload:
                    raise ValueError(conflict_message)
                return False
            owner.put_if_absent(owner=_ACCOUNTING_OWNER, state_type=state_type, state_id=state_id, payload=payload)
            return True


class PostgresOperatorStateStore:
    """PostgreSQL operator trading state used by worker-owned execution."""

    def __init__(self, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def get_trading_state(self) -> OperatorTradingState:
        with PostgresUnitOfWork(self._factory) as uow:
            record = OwnerStateStore(uow.connection).get(owner=_OPERATOR_OWNER, state_type=_TRADING_STATE, state_id="ACTIVE")
        if record is None:
            return OperatorTradingState(TradingState.TRADING_PAUSED, _now(), "system_default_fail_closed")
        payload = record.payload
        return OperatorTradingState(
            state=TradingState(str(payload.get("state") or TradingState.TRADING_ENABLED.value)),
            changed_at=str(payload.get("changed_at") or _now()),
            source=str(payload.get("source") or "system_default"),
            reason=None if payload.get("reason") is None else str(payload.get("reason")),
        )

    def record_operator_action(
        self,
        *,
        action: str,
        target: str | None,
        result: str,
        source: str = "trading_worker",
        error: str | None = None,
        changed_at: str | None = None,
    ) -> OperatorActionAudit:
        changed_at = changed_at or _now()
        audit = OperatorActionAudit(action, changed_at, target, result, source, _safe_error(error))
        state_id = f"{changed_at}:{action}:{target or 'ACTIVE'}"
        with PostgresUnitOfWork(self._factory) as uow:
            OwnerStateStore(uow.connection).put_if_absent(
                owner=_OPERATOR_OWNER,
                state_type=_ACTION_AUDIT_STATE,
                state_id=state_id,
                payload=asdict(audit),
            )
        return audit


def _list_payloads(conn, *, owner: str, state_type: str) -> tuple[dict[str, Any], ...]:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT payload_json::text
            FROM triggertrade_owner_state_records
            WHERE owner = %s AND state_type = %s
            """,
            (owner, state_type),
        )
        rows = cursor.fetchall()
    import json

    return tuple(json.loads(str(row[0]), parse_float=Decimal) for row in rows)


def _advisory_lock(conn, scope: str, key: str) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (f"{scope}:{key}",),
        )


def _execution_payload(record: FuturesExecutionRecord) -> dict[str, Any]:
    payload = asdict(record)
    payload["status"] = record.status.value
    return payload


def _execution_from_payload(payload: dict[str, Any]) -> FuturesExecutionRecord:
    data = dict(payload)
    data["status"] = OrderStatus(str(data["status"]))
    return FuturesExecutionRecord(**data)


def _position_payload(record: FuturesPositionRecord) -> dict[str, Any]:
    return dict(record.__dict__)


def _position_from_payload(payload: dict[str, Any]) -> FuturesPositionRecord:
    data = dict(payload)
    data["rule_snapshot"] = dict(data.get("rule_snapshot") or {})
    instrument_snapshot = data.get("instrument_snapshot")
    data["instrument_snapshot"] = (
        None if instrument_snapshot is None or instrument_snapshot == "" else dict(instrument_snapshot)
    )
    return FuturesPositionRecord(**data)


def _position_event_payload(event: FuturesPositionEvent) -> dict[str, Any]:
    return dict(event.__dict__)


def _closed_position_payload(record: FuturesClosedPositionRecord) -> dict[str, Any]:
    return dict(record.__dict__)


def _closed_position_from_payload(payload: dict[str, Any]) -> FuturesClosedPositionRecord:
    return FuturesClosedPositionRecord(**dict(payload))


def _fill_payload(event: FuturesFillEvent) -> dict[str, Any]:
    keys = tuple(asdict(event).keys())
    return {key: value for key, value in zip(keys, _fill_values(event), strict=True)}


def _fill_from_payload(payload: dict[str, Any]) -> FuturesFillEvent:
    return FuturesFillEvent(
        event_id=str(payload["event_id"]),
        trade_id=str(payload["trade_id"]),
        execution_id=str(payload["execution_id"]),
        symbol=str(payload["symbol"]),
        direction=PositionState(str(payload["direction"])),
        action=str(payload["action"]),
        quantity=Decimal(str(payload["quantity"])),
        price=Decimal(str(payload["price"])),
        fee=Decimal(str(payload["fee"])),
        fee_asset=str(payload["fee_asset"]),
        occurred_at=str(payload["occurred_at"]),
        settlement_asset=str(payload["settlement_asset"]),
        contract_size=Decimal(str(payload["contract_size"])),
        requested_price=None if payload.get("requested_price") is None else Decimal(str(payload["requested_price"])),
        trigger_set_id=None if payload.get("trigger_set_id") is None else str(payload["trigger_set_id"]),
        trigger_set_version=None if payload.get("trigger_set_version") is None else str(payload["trigger_set_version"]),
        regime_label=None if payload.get("regime_label") is None else str(payload["regime_label"]),
        source=str(payload["source"]),
    )


def _funding_payload(event: FuturesFundingEvent) -> dict[str, Any]:
    keys = tuple(asdict(event).keys())
    return {key: value for key, value in zip(keys, _funding_values(event), strict=True)}


def _funding_from_payload(payload: dict[str, Any]) -> FuturesFundingEvent:
    return FuturesFundingEvent(
        event_id=str(payload["event_id"]),
        trade_id=str(payload["trade_id"]),
        symbol=str(payload["symbol"]),
        direction=PositionState(str(payload["direction"])),
        funding_time=str(payload["funding_time"]),
        funding_rate=None if payload.get("funding_rate") is None else Decimal(str(payload["funding_rate"])),
        amount=Decimal(str(payload["amount"])),
        asset=str(payload["asset"]),
        source=str(payload["source"]),
    )


def _closed_trade_payload(result: ClosedTradeResult) -> dict[str, Any]:
    keys = (
        "trade_id",
        "symbol",
        "direction",
        "quantity",
        "leverage",
        "entry_vwap",
        "exit_vwap",
        "gross_pnl",
        "entry_fee",
        "exit_fee",
        "other_fees",
        "funding",
        "net_pnl",
        "opened_at",
        "closed_at",
        "duration_seconds",
        "accounting_version",
        "settlement_asset",
        "contract_size",
        "trigger_set_id",
        "trigger_set_version",
        "regime_label",
        "entry_slippage_cost",
        "exit_slippage_cost",
        "evidence_source",
        "simulation_model_version",
    )
    return {key: value for key, value in zip(keys, _closed_trade_values(result), strict=True)}


def _equity_payload(snapshot: EquitySnapshot) -> dict[str, Any]:
    keys = tuple(asdict(snapshot).keys())
    return {key: value for key, value in zip(keys, _equity_values(snapshot), strict=True)}


def _utc_day_bounds(trading_day: str) -> tuple[str, str]:
    start = datetime.fromisoformat(trading_day).replace(tzinfo=UTC)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _safe_error(value: str | None) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).replace("\x00", "").split())[:500]
    lowered = text.lower()
    if any(token in lowered for token in ("secret", "api_key", "authorization", "bearer", "token", "password")):
        return "[redacted]"
    return text
