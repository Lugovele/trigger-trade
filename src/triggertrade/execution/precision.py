"""Decimal precision checks for the Bybit Demo Spot execution slice."""

from __future__ import annotations

from decimal import Decimal

from triggertrade.market_data import BybitInstrument


class PrecisionError(ValueError):
    """Raised when an order violates instrument constraints."""


def validate_limit_order_precision(
    *,
    instrument: BybitInstrument,
    quantity: Decimal,
    price: Decimal,
) -> None:
    if quantity <= 0:
        raise PrecisionError("order quantity must be positive")
    if price <= 0:
        raise PrecisionError("order price must be positive")
    if quantity < instrument.min_order_quantity:
        raise PrecisionError("order quantity is below instrument minimum")
    if quantity * price < instrument.min_order_amount:
        raise PrecisionError("order notional is below instrument minimum")
    if not _is_multiple(quantity, instrument.quantity_step):
        raise PrecisionError("order quantity does not match instrument step size")
    if not _is_multiple(price, instrument.price_tick):
        raise PrecisionError("limit price does not match instrument tick size")


def _is_multiple(value: Decimal, step: Decimal) -> bool:
    if step <= 0:
        raise PrecisionError("instrument precision step must be positive")
    return (value / step) == (value / step).to_integral_value()
