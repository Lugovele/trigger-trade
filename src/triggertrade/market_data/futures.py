"""Futures market metadata and regime context contracts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class ContractCategory(StrEnum):
    LINEAR = "linear"


class MarketRegimeLabel(StrEnum):
    STRONG_DOWNTREND = "STRONG_DOWNTREND"
    DOWNTREND = "DOWNTREND"
    SIDEWAYS = "SIDEWAYS"
    UPTREND = "UPTREND"
    STRONG_UPTREND = "STRONG_UPTREND"
    UNKNOWN = "UNKNOWN"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class RegimeCapability(StrEnum):
    AVAILABLE = "available"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class FuturesInstrumentMetadata:
    symbol: str
    category: ContractCategory
    contract_type: str
    settlement_asset: str
    quantity_step: Decimal
    price_tick: Decimal
    minimum_order_quantity: Decimal
    minimum_notional: Decimal
    max_leverage: Decimal
    min_leverage: Decimal = Decimal("1")
    leverage_step: Decimal = Decimal("0.01")
    contract_size: Decimal | None = None


@dataclass(frozen=True)
class FuturesAccountState:
    symbol: str
    category: ContractCategory
    settlement_asset: str
    available_margin: Decimal
    equity: Decimal | None = None
    wallet_balance: Decimal | None = None
    configured_leverage: Decimal = Decimal("1")
    margin_mode: str = "ISOLATED"
    position_mode: str = "ONE_WAY"
    position_size: Decimal = Decimal("0")
    entry_price: Decimal | None = None
    mark_price: Decimal | None = None
    liquidation_price: Decimal | None = None
    maintenance_margin: Decimal | None = None


@dataclass(frozen=True)
class MarketRegimeContext:
    context_id: str
    symbol: str
    timeframe: str
    observed_at: str
    capability: RegimeCapability
    rule_id: str = "CTX-REGIME"
    version: str = "0.1.0"
    label: MarketRegimeLabel | None = None
    input_snapshot: dict[str, str] | None = None
    normalized_features: dict[str, str] | None = None
    thresholds: dict[str, str] | None = None
    reason: str | None = None
