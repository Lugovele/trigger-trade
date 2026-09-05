"""Bybit Demo USDT perpetual futures execution adapter."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from triggertrade.execution.bybit import map_bybit_order_status
from triggertrade.execution.contracts import OrderStatus
from triggertrade.execution.futures import PositionAction, futures_exchange_side
from triggertrade.exchanges import BybitDemoClient, BybitResponse


class BybitFuturesExecutionAdapter:
    uses_private_exchange_orders = True
    category = "linear"

    def __init__(self, client: BybitDemoClient) -> None:
        self._client = client

    def create_limit_order(
        self,
        *,
        symbol: str,
        action: PositionAction,
        quantity: Decimal,
        price: Decimal,
        client_order_id: str,
    ) -> BybitResponse:
        return self._client._create_linear_limit_order(
            symbol=symbol,
            side=futures_exchange_side(action).value,
            qty=str(quantity),
            price=str(price),
            order_link_id=client_order_id,
            reduce_only=action in {PositionAction.CLOSE_LONG, PositionAction.CLOSE_SHORT},
        )

    def fetch_order(self, *, symbol: str, client_order_id: str) -> dict[str, Any] | None:
        return _first_order(self._client._get_linear_order_realtime(symbol, client_order_id).result)

    def fetch_order_history(self, *, symbol: str, client_order_id: str) -> dict[str, Any] | None:
        return _first_order(self._client._get_linear_order_history(symbol, client_order_id).result)

    def cancel_order(self, *, symbol: str, client_order_id: str) -> BybitResponse:
        return self._client._cancel_linear_order(symbol=symbol, order_link_id=client_order_id)

    def fetch_executions(self, *, symbol: str, client_order_id: str) -> tuple[dict[str, Any], ...]:
        rows = self._client._get_linear_executions(symbol, client_order_id).result.get("list") or []
        return tuple(dict(row) for row in rows)

    def reconcile_order(self, *, symbol: str, client_order_id: str) -> dict[str, Any] | None:
        return self.fetch_order(symbol=symbol, client_order_id=client_order_id) or self.fetch_order_history(
            symbol=symbol,
            client_order_id=client_order_id,
        )

    def map_order_status(self, raw_status: str | None) -> OrderStatus:
        return map_bybit_order_status(raw_status)


def _first_order(result: dict[str, Any]) -> dict[str, Any] | None:
    rows = result.get("list") or []
    return rows[0] if rows else None
