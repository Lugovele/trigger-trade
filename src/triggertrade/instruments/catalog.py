"""Canonical Bybit USDT linear perpetual instrument catalog domain."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any

from triggertrade.market_data import ContractCategory, FuturesInstrumentMetadata


CATALOG_SOURCE = "bybit_public_v5_instruments_info_linear"


class CatalogError(ValueError):
    """Raised when instrument metadata cannot safely support trading decisions."""


class InstrumentExclusionReason(StrEnum):
    WRONG_PRODUCT = "WRONG_PRODUCT"
    WRONG_SETTLE_COIN = "WRONG_SETTLE_COIN"
    NOT_PERPETUAL = "NOT_PERPETUAL"
    NOT_TRADING = "NOT_TRADING"
    INVALID_PRICE_FILTER = "INVALID_PRICE_FILTER"
    INVALID_QTY_FILTER = "INVALID_QTY_FILTER"
    INCOMPLETE_METADATA = "INCOMPLETE_METADATA"


class PriceNormalizationPurpose(StrEnum):
    ENTRY_LIMIT = "ENTRY_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_LOSS = "STOP_LOSS"
    REDUCE_ONLY_CLOSE = "REDUCE_ONLY_CLOSE"


@dataclass(frozen=True)
class FuturesInstrument:
    symbol: str
    base_coin: str
    quote_coin: str
    settle_coin: str
    contract_type: str
    status: str
    tick_size: Decimal
    price_scale: int | None
    min_order_qty: Decimal
    max_order_qty: Decimal
    qty_step: Decimal
    min_notional_value: Decimal | None
    max_market_order_qty: Decimal | None
    min_leverage: Decimal | None
    max_leverage: Decimal
    leverage_step: Decimal | None
    launch_time: str | None
    delivery_time: str | None
    is_tradeable: bool
    updated_at: str
    source: str = CATALOG_SOURCE
    exclusion_reason: InstrumentExclusionReason | None = None
    catalog_hash: str | None = None


@dataclass(frozen=True)
class InstrumentCatalogRefreshResult:
    fetched_count: int
    tradeable_count: int
    excluded_count: int
    updated_at: str
    catalog_hash: str | None
    status: str
    error: str | None = None
    warnings: tuple[str, ...] = ()


def instrument_from_bybit(item: dict[str, Any], *, updated_at: str, source: str = CATALOG_SOURCE) -> FuturesInstrument:
    symbol = _required_str(item, "symbol").upper()
    base_coin = str(item.get("baseCoin") or symbol.removesuffix("USDT"))
    quote_coin = str(item.get("quoteCoin") or "")
    settle_coin = str(item.get("settleCoin") or "")
    contract_type = str(item.get("contractType") or "")
    status = str(item.get("status") or "")
    price_filter = item.get("priceFilter") or {}
    lot_filter = item.get("lotSizeFilter") or {}
    leverage_filter = item.get("leverageFilter") or {}

    tick_size = _positive_decimal(price_filter.get("tickSize"), InstrumentExclusionReason.INVALID_PRICE_FILTER)
    min_order_qty = _positive_decimal(lot_filter.get("minOrderQty"), InstrumentExclusionReason.INVALID_QTY_FILTER)
    max_order_qty = _positive_decimal(lot_filter.get("maxOrderQty"), InstrumentExclusionReason.INVALID_QTY_FILTER)
    qty_step = _positive_decimal(lot_filter.get("qtyStep"), InstrumentExclusionReason.INVALID_QTY_FILTER)
    max_leverage = _positive_decimal(leverage_filter.get("maxLeverage"), InstrumentExclusionReason.INCOMPLETE_METADATA)
    min_leverage = _optional_positive_decimal(leverage_filter.get("minLeverage"))
    leverage_step = _optional_positive_decimal(leverage_filter.get("leverageStep"))
    min_notional = _optional_positive_decimal(lot_filter.get("minNotionalValue"))
    max_market_qty = _optional_positive_decimal(lot_filter.get("maxMktOrderQty"))
    price_scale = _optional_int(item.get("priceScale"))
    reason = classify_bybit_linear_instrument(
        symbol=symbol,
        quote_coin=quote_coin,
        settle_coin=settle_coin,
        contract_type=contract_type,
        status=status,
        tick_size=tick_size,
        qty_step=qty_step,
        min_order_qty=min_order_qty,
        max_order_qty=max_order_qty,
        min_notional_value=min_notional,
        min_leverage=min_leverage,
        max_leverage=max_leverage,
        leverage_step=leverage_step,
    )
    is_tradeable = reason is None
    return FuturesInstrument(
        symbol=symbol,
        base_coin=base_coin,
        quote_coin=quote_coin,
        settle_coin=settle_coin,
        contract_type=contract_type,
        status=status,
        tick_size=tick_size,
        price_scale=price_scale,
        min_order_qty=min_order_qty,
        max_order_qty=max_order_qty,
        qty_step=qty_step,
        min_notional_value=min_notional,
        max_market_order_qty=max_market_qty,
        min_leverage=min_leverage,
        max_leverage=max_leverage,
        leverage_step=leverage_step,
        launch_time=None if item.get("launchTime") in {None, ""} else str(item.get("launchTime")),
        delivery_time=None if item.get("deliveryTime") in {None, ""} else str(item.get("deliveryTime")),
        is_tradeable=is_tradeable,
        updated_at=updated_at,
        source=source,
        exclusion_reason=reason,
    )


def classify_bybit_linear_instrument(
    *,
    symbol: str,
    quote_coin: str,
    settle_coin: str,
    contract_type: str,
    status: str,
    tick_size: Decimal,
    qty_step: Decimal,
    min_order_qty: Decimal,
    max_order_qty: Decimal,
    min_notional_value: Decimal | None,
    min_leverage: Decimal | None,
    max_leverage: Decimal,
    leverage_step: Decimal | None,
) -> InstrumentExclusionReason | None:
    if not symbol.endswith("USDT") or quote_coin.upper() != "USDT":
        return InstrumentExclusionReason.WRONG_PRODUCT
    if settle_coin.upper() != "USDT":
        return InstrumentExclusionReason.WRONG_SETTLE_COIN
    if contract_type != "LinearPerpetual":
        return InstrumentExclusionReason.NOT_PERPETUAL
    if status != "Trading":
        return InstrumentExclusionReason.NOT_TRADING
    if tick_size <= 0:
        return InstrumentExclusionReason.INVALID_PRICE_FILTER
    if qty_step <= 0 or min_order_qty <= 0 or max_order_qty <= 0 or max_order_qty < min_order_qty:
        return InstrumentExclusionReason.INVALID_QTY_FILTER
    if min_notional_value is None or min_notional_value <= 0:
        return InstrumentExclusionReason.INCOMPLETE_METADATA
    if min_leverage is None or min_leverage <= 0 or max_leverage <= 0 or leverage_step is None or leverage_step <= 0:
        return InstrumentExclusionReason.INCOMPLETE_METADATA
    return None


def normalize_qty_for_instrument(instrument: FuturesInstrument, qty: Decimal, *, price: Decimal | None = None) -> Decimal:
    _require_tradeable_metadata(instrument)
    if qty <= 0:
        raise CatalogError("quantity must be positive")
    normalized = _floor_to_step(qty, instrument.qty_step)
    if normalized <= 0 or normalized < instrument.min_order_qty:
        raise CatalogError("normalized quantity is below minimum order quantity")
    if normalized > instrument.max_order_qty:
        raise CatalogError("normalized quantity exceeds maximum limit order quantity")
    if price is not None and instrument.min_notional_value is not None and normalized * price < instrument.min_notional_value:
        raise CatalogError("normalized quantity is below minimum notional")
    return normalized


def normalize_price_for_instrument(
    instrument: FuturesInstrument,
    price: Decimal,
    *,
    purpose: PriceNormalizationPurpose,
    action,
) -> Decimal:
    _require_tradeable_metadata(instrument, require_tradeable=False)
    if price <= 0:
        raise CatalogError("price must be positive")
    tick = instrument.tick_size
    action_value = getattr(action, "value", str(action))
    if purpose is PriceNormalizationPurpose.TAKE_PROFIT:
        if action_value == "OPEN_LONG":
            return _floor_to_step(price, tick)
        if action_value == "OPEN_SHORT":
            return _ceil_to_step(price, tick)
    if purpose is PriceNormalizationPurpose.STOP_LOSS:
        if action_value == "OPEN_LONG":
            return _ceil_to_step(price, tick)
        if action_value == "OPEN_SHORT":
            return _floor_to_step(price, tick)
    if purpose is PriceNormalizationPurpose.ENTRY_LIMIT:
        if action_value in {"OPEN_LONG", "CLOSE_SHORT"}:
            return _floor_to_step(price, tick)
        return _ceil_to_step(price, tick)
    if purpose is PriceNormalizationPurpose.REDUCE_ONLY_CLOSE:
        return _floor_to_step(price, tick) if action_value == "CLOSE_LONG" else _ceil_to_step(price, tick)
    raise CatalogError("unsupported price normalization purpose")


def instrument_to_metadata(instrument: FuturesInstrument) -> FuturesInstrumentMetadata:
    if instrument.min_notional_value is None or instrument.min_leverage is None or instrument.leverage_step is None:
        raise CatalogError("tradeable instrument metadata is incomplete")
    return FuturesInstrumentMetadata(
        symbol=instrument.symbol,
        category=ContractCategory.LINEAR,
        contract_type=instrument.contract_type,
        settlement_asset=instrument.settle_coin,
        quantity_step=instrument.qty_step,
        price_tick=instrument.tick_size,
        minimum_order_quantity=instrument.min_order_qty,
        minimum_notional=instrument.min_notional_value,
        max_leverage=instrument.max_leverage,
        min_leverage=instrument.min_leverage,
        leverage_step=instrument.leverage_step,
        maximum_order_quantity=instrument.max_order_qty,
        max_market_order_quantity=instrument.max_market_order_qty,
        catalog_hash=instrument.catalog_hash,
        catalog_source=instrument.source,
    )


def instrument_snapshot(instrument: FuturesInstrument) -> dict[str, str | None]:
    return {
        "symbol": instrument.symbol,
        "base_coin": instrument.base_coin,
        "quote_coin": instrument.quote_coin,
        "settle_coin": instrument.settle_coin,
        "category": ContractCategory.LINEAR.value,
        "contract_type": instrument.contract_type,
        "status": instrument.status,
        "tick_size": str(instrument.tick_size),
        "price_scale": None if instrument.price_scale is None else str(instrument.price_scale),
        "min_order_qty": str(instrument.min_order_qty),
        "max_order_qty": str(instrument.max_order_qty),
        "qty_step": str(instrument.qty_step),
        "min_notional_value": None if instrument.min_notional_value is None else str(instrument.min_notional_value),
        "max_market_order_qty": None if instrument.max_market_order_qty is None else str(instrument.max_market_order_qty),
        "min_leverage": None if instrument.min_leverage is None else str(instrument.min_leverage),
        "max_leverage": str(instrument.max_leverage),
        "leverage_step": None if instrument.leverage_step is None else str(instrument.leverage_step),
        "launch_time": instrument.launch_time,
        "delivery_time": instrument.delivery_time,
        "updated_at": instrument.updated_at,
        "source": instrument.source,
        "catalog_hash": instrument.catalog_hash,
    }


def instrument_from_snapshot(snapshot: dict[str, str | None]) -> FuturesInstrument:
    try:
        return FuturesInstrument(
            symbol=str(snapshot["symbol"]),
            base_coin=str(snapshot.get("base_coin") or ""),
            quote_coin=str(snapshot.get("quote_coin") or "USDT"),
            settle_coin=str(snapshot.get("settle_coin") or "USDT"),
            contract_type=str(snapshot.get("contract_type") or "LinearPerpetual"),
            status=str(snapshot.get("status") or "Trading"),
            tick_size=Decimal(str(snapshot["tick_size"])),
            price_scale=None if snapshot.get("price_scale") is None else int(str(snapshot.get("price_scale"))),
            min_order_qty=Decimal(str(snapshot["min_order_qty"])),
            max_order_qty=Decimal(str(snapshot["max_order_qty"])),
            qty_step=Decimal(str(snapshot["qty_step"])),
            min_notional_value=None if snapshot.get("min_notional_value") is None else Decimal(str(snapshot.get("min_notional_value"))),
            max_market_order_qty=None if snapshot.get("max_market_order_qty") is None else Decimal(str(snapshot.get("max_market_order_qty"))),
            min_leverage=None if snapshot.get("min_leverage") is None else Decimal(str(snapshot.get("min_leverage"))),
            max_leverage=Decimal(str(snapshot["max_leverage"])),
            leverage_step=None if snapshot.get("leverage_step") is None else Decimal(str(snapshot.get("leverage_step"))),
            launch_time=snapshot.get("launch_time"),
            delivery_time=snapshot.get("delivery_time"),
            is_tradeable=True,
            updated_at=str(snapshot.get("updated_at") or ""),
            source=str(snapshot.get("source") or CATALOG_SOURCE),
            catalog_hash=snapshot.get("catalog_hash"),
        )
    except Exception as exc:
        raise CatalogError("instrument snapshot is incomplete or invalid") from exc


def catalog_hash(instruments: tuple[FuturesInstrument, ...]) -> str:
    payload = [
        _instrument_payload(instrument)
        for instrument in sorted(instruments, key=lambda item: item.symbol)
    ]
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def with_catalog_hash(instrument: FuturesInstrument, value: str) -> FuturesInstrument:
    return FuturesInstrument(**{**instrument.__dict__, "catalog_hash": value})


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _instrument_payload(instrument: FuturesInstrument) -> dict[str, str | bool | None]:
    return {
        "symbol": instrument.symbol,
        "base_coin": instrument.base_coin,
        "quote_coin": instrument.quote_coin,
        "settle_coin": instrument.settle_coin,
        "contract_type": instrument.contract_type,
        "status": instrument.status,
        "tick_size": str(instrument.tick_size),
        "price_scale": None if instrument.price_scale is None else str(instrument.price_scale),
        "min_order_qty": str(instrument.min_order_qty),
        "max_order_qty": str(instrument.max_order_qty),
        "qty_step": str(instrument.qty_step),
        "min_notional_value": None if instrument.min_notional_value is None else str(instrument.min_notional_value),
        "max_market_order_qty": None if instrument.max_market_order_qty is None else str(instrument.max_market_order_qty),
        "min_leverage": None if instrument.min_leverage is None else str(instrument.min_leverage),
        "max_leverage": str(instrument.max_leverage),
        "leverage_step": None if instrument.leverage_step is None else str(instrument.leverage_step),
        "is_tradeable": instrument.is_tradeable,
        "source": instrument.source,
        "exclusion_reason": None if instrument.exclusion_reason is None else instrument.exclusion_reason.value,
    }


def _require_tradeable_metadata(instrument: FuturesInstrument, *, require_tradeable: bool = True) -> None:
    reason = classify_bybit_linear_instrument(
        symbol=instrument.symbol,
        quote_coin=instrument.quote_coin,
        settle_coin=instrument.settle_coin,
        contract_type=instrument.contract_type,
        status=instrument.status,
        tick_size=instrument.tick_size,
        qty_step=instrument.qty_step,
        min_order_qty=instrument.min_order_qty,
        max_order_qty=instrument.max_order_qty,
        min_notional_value=instrument.min_notional_value,
        min_leverage=instrument.min_leverage,
        max_leverage=instrument.max_leverage,
        leverage_step=instrument.leverage_step,
    )
    if reason is not None:
        raise CatalogError(f"instrument metadata is not safe for order normalization: {reason.value}")
    if require_tradeable and not instrument.is_tradeable:
        raise CatalogError("instrument is not currently tradeable")


def _required_str(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if value in {None, ""}:
        raise CatalogError("instrument metadata is incomplete")
    return str(value)


def _positive_decimal(value: Any, reason: InstrumentExclusionReason) -> Decimal:
    parsed = _optional_decimal(value)
    if parsed is None or parsed <= 0:
        raise CatalogError(reason.value)
    return parsed


def _optional_positive_decimal(value: Any) -> Decimal | None:
    parsed = _optional_decimal(value)
    if parsed is None:
        return None
    if parsed <= 0:
        raise CatalogError("decimal metadata must be positive when provided")
    return parsed


def _optional_decimal(value: Any) -> Decimal | None:
    if value in {None, ""}:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CatalogError("decimal metadata is invalid") from exc


def _optional_int(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(str(value))
    except ValueError as exc:
        raise CatalogError("integer metadata is invalid") from exc


def _floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        raise CatalogError("step must be positive")
    return (value // step) * step


def _ceil_to_step(value: Decimal, step: Decimal) -> Decimal:
    floored = _floor_to_step(value, step)
    return floored if floored == value else floored + step
