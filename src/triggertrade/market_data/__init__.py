"""Market data normalization boundary."""

from .bybit import (
    BybitCandle,
    BybitInstrument,
    BybitTicker,
    parse_linear_instrument,
    parse_linear_ticker,
    parse_spot_candles,
    parse_spot_instrument,
    parse_spot_ticker,
)
from .futures import ContractCategory, FuturesAccountState, FuturesInstrumentMetadata, MarketRegimeContext, MarketRegimeLabel, RegimeCapability
from .models import MarketObservation
from .regime import (
    REGIME_RULE_ID,
    REGIME_VERSION,
    RegimeEvaluationWindow,
    evaluate_market_regime,
    regime_business_key,
)

__all__ = [
    "BybitCandle",
    "BybitInstrument",
    "BybitTicker",
    "ContractCategory",
    "FuturesAccountState",
    "FuturesInstrumentMetadata",
    "MarketRegimeContext",
    "MarketRegimeLabel",
    "MarketObservation",
    "REGIME_RULE_ID",
    "REGIME_VERSION",
    "RegimeCapability",
    "RegimeEvaluationWindow",
    "evaluate_market_regime",
    "parse_linear_instrument",
    "parse_linear_ticker",
    "parse_spot_candles",
    "parse_spot_instrument",
    "parse_spot_ticker",
    "regime_business_key",
]
