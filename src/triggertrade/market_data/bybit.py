"""Bybit spot market data parsing for the supported bootstrap symbol."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class BybitInstrument:
    symbol: str
    base_coin: str
    quote_coin: str
    price_tick: Decimal
    quantity_step: Decimal
    min_order_quantity: Decimal
    min_order_amount: Decimal


@dataclass(frozen=True)
class BybitTicker:
    symbol: str
    last_price: Decimal
    bid_price: Decimal | None = None
    ask_price: Decimal | None = None


@dataclass(frozen=True)
class BybitCandle:
    start_time_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    turnover: Decimal


def parse_spot_instrument(result: dict[str, Any], symbol: str = "BTCUSDT") -> BybitInstrument:
    item = _single_symbol_item(result, symbol)
    lot_filter = item.get("lotSizeFilter") or {}
    price_filter = item.get("priceFilter") or {}
    return BybitInstrument(
        symbol=item["symbol"],
        base_coin=item["baseCoin"],
        quote_coin=item["quoteCoin"],
        price_tick=Decimal(price_filter["tickSize"]),
        quantity_step=Decimal(lot_filter["basePrecision"]),
        min_order_quantity=Decimal(lot_filter["minOrderQty"]),
        min_order_amount=Decimal(lot_filter["minOrderAmt"]),
    )


def parse_spot_ticker(result: dict[str, Any], symbol: str = "BTCUSDT") -> BybitTicker:
    item = _single_symbol_item(result, symbol)
    return BybitTicker(
        symbol=item["symbol"],
        last_price=Decimal(item["lastPrice"]),
        bid_price=_optional_decimal(item.get("bid1Price")),
        ask_price=_optional_decimal(item.get("ask1Price")),
    )


def parse_spot_candles(result: dict[str, Any]) -> tuple[BybitCandle, ...]:
    candles = result.get("list") or []
    return tuple(
        BybitCandle(
            start_time_ms=int(item[0]),
            open=Decimal(item[1]),
            high=Decimal(item[2]),
            low=Decimal(item[3]),
            close=Decimal(item[4]),
            volume=Decimal(item[5]),
            turnover=Decimal(item[6]),
        )
        for item in candles
    )


def _single_symbol_item(result: dict[str, Any], symbol: str) -> dict[str, Any]:
    expected = symbol.upper()
    for item in result.get("list") or []:
        if item.get("symbol") == expected:
            return item
    raise ValueError(f"Bybit response did not include expected spot symbol {expected}")


def _optional_decimal(raw: str | None) -> Decimal | None:
    if raw in {None, ""}:
        return None
    return Decimal(raw)
