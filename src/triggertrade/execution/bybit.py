"""Bybit Demo Spot execution adapter."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from triggertrade.execution.contracts import OrderStatus, Side
from triggertrade.exchanges import BybitDemoClient, BybitResponse


class BybitExecutionAdapter:
    def __init__(self, client: BybitDemoClient) -> None:
        self._client = client

    def create_limit_order(
        self,
        *,
        symbol: str,
        side: Side,
        quantity: Decimal,
        price: Decimal,
        client_order_id: str,
    ) -> BybitResponse:
        return self._client._create_spot_limit_order(
            symbol=symbol,
            side=side.value,
            qty=str(quantity),
            price=str(price),
            order_link_id=client_order_id,
        )

    def fetch_order(self, *, symbol: str, client_order_id: str) -> dict[str, Any] | None:
        return _first_order(self._client._get_spot_order_realtime(symbol, client_order_id).result)

    def fetch_order_history(self, *, symbol: str, client_order_id: str) -> dict[str, Any] | None:
        return _first_order(self._client._get_spot_order_history(symbol, client_order_id).result)

    def cancel_order(self, *, symbol: str, client_order_id: str) -> BybitResponse:
        return self._client._cancel_spot_order(symbol=symbol, order_link_id=client_order_id)

    def reconcile_order(self, *, symbol: str, client_order_id: str) -> dict[str, Any] | None:
        return self.fetch_order(symbol=symbol, client_order_id=client_order_id) or self.fetch_order_history(
            symbol=symbol,
            client_order_id=client_order_id,
        )


def map_bybit_order_status(raw_status: str | None) -> OrderStatus:
    status = (raw_status or "").strip()
    mapping = {
        "New": OrderStatus.SUBMITTED,
        "Created": OrderStatus.SUBMITTED,
        "Untriggered": OrderStatus.SUBMITTED,
        "PartiallyFilled": OrderStatus.PARTIALLY_FILLED,
        "Filled": OrderStatus.FILLED,
        "Cancelled": OrderStatus.CANCELLED,
        "PartiallyFilledCanceled": OrderStatus.CANCELLED,
        "Rejected": OrderStatus.REJECTED,
        "Deactivated": OrderStatus.REJECTED,
    }
    return mapping.get(status, OrderStatus.UNKNOWN)


def _first_order(result: dict[str, Any]) -> dict[str, Any] | None:
    rows = result.get("list") or []
    return rows[0] if rows else None
