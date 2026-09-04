from decimal import Decimal

import pytest

from triggertrade.execution.precision import PrecisionError, validate_limit_order_precision
from triggertrade.market_data import BybitInstrument


def test_valid_quantity_and_price_pass():
    validate_limit_order_precision(
        instrument=_instrument(),
        quantity=Decimal("0.001000"),
        price=Decimal("10000.00"),
    )


def test_below_minimum_quantity_rejected():
    with pytest.raises(PrecisionError):
        validate_limit_order_precision(
            instrument=_instrument(),
            quantity=Decimal("0.000001"),
            price=Decimal("10000.00"),
        )


def test_invalid_quantity_step_rejected():
    with pytest.raises(PrecisionError):
        validate_limit_order_precision(
            instrument=_instrument(),
            quantity=Decimal("0.0010001"),
            price=Decimal("10000.00"),
        )


def test_invalid_limit_price_tick_rejected():
    with pytest.raises(PrecisionError):
        validate_limit_order_precision(
            instrument=_instrument(),
            quantity=Decimal("0.001000"),
            price=Decimal("10000.001"),
        )


def test_below_minimum_notional_rejected():
    with pytest.raises(PrecisionError):
        validate_limit_order_precision(
            instrument=_instrument(),
            quantity=Decimal("0.000010"),
            price=Decimal("100.00"),
        )


def _instrument():
    return BybitInstrument(
        symbol="BTCUSDT",
        base_coin="BTC",
        quote_coin="USDT",
        price_tick=Decimal("0.01"),
        quantity_step=Decimal("0.000001"),
        min_order_quantity=Decimal("0.00001"),
        min_order_amount=Decimal("5"),
    )
