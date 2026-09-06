"""Bridge explicit futures execution facts into accounting facts."""

from __future__ import annotations

from decimal import Decimal

from triggertrade.accounting import FuturesFillEvent, close_futures_trade
from triggertrade.execution.contracts import OrderStatus
from triggertrade.execution.futures import FuturesTradeIntent, PositionAction, PositionState
from triggertrade.persistence import FuturesExecutionRecord
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore


class FuturesAccountingBridge:
    def __init__(self, *, accounting_store: FuturesAccountingStore, adapter) -> None:
        self._accounting_store = accounting_store
        self._adapter = adapter

    def ingest_execution(
        self,
        *,
        record: FuturesExecutionRecord,
        intent: FuturesTradeIntent | None = None,
        trade_id: str | None = None,
    ) -> None:
        if intent is not None and intent.intent_id != record.intent_id:
            raise ValueError("futures accounting bridge intent/record mismatch")
        if record.status not in {OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED}:
            return
        if not hasattr(self._adapter, "fetch_executions"):
            return
        rows = self._adapter.fetch_executions(symbol=record.symbol, client_order_id=record.client_order_id)
        for row in rows:
            event = _fill_event(record, row, trade_id=trade_id, intent=intent)
            self._accounting_store.record_fill(event)
        _try_close_trade(record, self._accounting_store, trade_id=trade_id)


def _fill_event(record: FuturesExecutionRecord, row: dict, *, trade_id: str | None = None, intent: FuturesTradeIntent | None = None) -> FuturesFillEvent:
    exec_id = str(row.get("execId") or row.get("exec_id") or f"{record.client_order_id}-{row.get('execTime', '')}")
    qty = Decimal(str(row.get("execQty") or row.get("qty") or "0"))
    price = Decimal(str(row.get("execPrice") or row.get("price") or record.requested_price))
    fee = Decimal(str(row.get("execFee") or row.get("fee") or "0"))
    occurred_at = str(row.get("execTime") or row.get("createdTime") or record.updated_at)
    if occurred_at.isdigit():
        from datetime import UTC, datetime

        occurred_at = datetime.fromtimestamp(int(occurred_at) / 1000, UTC).isoformat()
    return FuturesFillEvent(
        event_id=f"bybit-{exec_id}",
        trade_id=trade_id or _trade_id(record.intent_id),
        execution_id=record.client_order_id,
        symbol=record.symbol,
        direction=_direction(record.position_action),
        action=record.position_action,
        quantity=qty,
        price=price,
        fee=fee,
        fee_asset=str(row.get("feeCurrency") or row.get("feeCoin") or "USDT"),
        occurred_at=occurred_at,
        requested_price=Decimal(record.requested_price),
        trigger_set_id=record.trigger_set_id,
        trigger_set_version=record.trigger_set_version,
        regime_label=None if trade_id is None or intent is None else intent.regime_state,
        source="exchange",
    )


def _try_close_trade(record: FuturesExecutionRecord, store: FuturesAccountingStore, *, trade_id: str | None = None) -> None:
    trade_id = trade_id or _trade_id(record.intent_id)
    fills = store.list_fills(trade_id)
    entry = tuple(fill for fill in fills if fill.action in {PositionAction.OPEN_LONG.value, PositionAction.OPEN_SHORT.value})
    exit_fills = tuple(fill for fill in fills if fill.action in {PositionAction.CLOSE_LONG.value, PositionAction.CLOSE_SHORT.value})
    if not entry or not exit_fills:
        return
    result = close_futures_trade(
        trade_id=trade_id,
        entry_fills=entry,
        exit_fills=exit_fills,
        funding_events=store.list_funding(trade_id),
        leverage=Decimal(record.leverage),
    )
    store.record_closed_trade(result)


def _direction(action: str) -> PositionState:
    if action in {PositionAction.OPEN_LONG.value, PositionAction.CLOSE_LONG.value}:
        return PositionState.LONG
    return PositionState.SHORT


def _trade_id(intent_id: str) -> str:
    return f"trade-{intent_id}"
