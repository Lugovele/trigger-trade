"""Deterministic local paper execution adapter.

Paper fills are intentionally simple for the runtime slice: approved limit orders
are accepted locally and reconciled as filled at the requested limit price with
zero slippage and zero fees. This is audit plumbing, not an exchange simulator.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from triggertrade.execution.contracts import Side


@dataclass(frozen=True)
class PaperResponse:
    result: dict[str, Any]


class PaperExecutionAdapter:
    uses_private_exchange_orders = False

    def __init__(self, clock_ms=lambda: 0) -> None:
        self._orders: dict[str, dict[str, Any]] = {}
        self._clock_ms = clock_ms
        self.create_calls = 0
        self.cancel_calls = 0

    def create_limit_order(
        self,
        *,
        symbol: str,
        side: Side,
        quantity: Decimal,
        price: Decimal,
        client_order_id: str,
    ) -> PaperResponse:
        self.create_calls += 1
        order = self._orders.get(client_order_id)
        if order is None:
            timestamp = str(self._clock_ms())
            order = {
                "orderId": f"paper-{client_order_id}",
                "orderLinkId": client_order_id,
                "symbol": symbol,
                "side": side.value,
                "orderStatus": "Filled",
                "cumExecQty": str(quantity),
                "avgPrice": str(price),
                "fills": (
                    {
                        "execId": f"paper-fill-{client_order_id}",
                        "execQty": str(quantity),
                        "execPrice": str(price),
                        "execFee": "0",
                        "execTime": timestamp,
                    },
                ),
            }
            self._orders[client_order_id] = order
        return PaperResponse({"orderId": order["orderId"], "orderLinkId": client_order_id})

    def cancel_order(self, *, symbol: str, client_order_id: str) -> PaperResponse:
        self.cancel_calls += 1
        return PaperResponse({"orderLinkId": client_order_id})

    def reconcile_order(self, *, symbol: str, client_order_id: str) -> dict[str, Any] | None:
        return self._orders.get(client_order_id)
