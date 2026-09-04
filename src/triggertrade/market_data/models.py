"""Internal market data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


@dataclass(frozen=True)
class MarketObservation:
    symbol: str
    observed_at: datetime
    current_price: Decimal | None
    previous_price: Decimal | None
    window: str
    source: str
    stale_after_seconds: int

    def is_stale(self, now: datetime | None = None) -> bool:
        current_time = now or datetime.now(UTC)
        observed = self.observed_at
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=UTC)
        return (current_time - observed).total_seconds() > self.stale_after_seconds
