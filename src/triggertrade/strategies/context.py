"""Strategy context contracts shared by deterministic strategy rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from triggertrade.market_data import MarketRegimeContext


class StrategyContextInterpretation(StrEnum):
    CONTINUATION_CANDIDATE = "CONTINUATION_CANDIDATE"
    REVERSAL_CANDIDATE = "REVERSAL_CANDIDATE"


@dataclass(frozen=True)
class RegimeStrategyContext:
    regime: MarketRegimeContext
    interpretation: StrategyContextInterpretation | None = None
