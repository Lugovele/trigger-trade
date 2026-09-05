"""Canonical completed market event for the futures runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from triggertrade.market_data.bybit import BybitCandle
from triggertrade.market_data.models import MarketObservation


@dataclass(frozen=True)
class FuturesMarketEvent:
    symbol: str
    category: str
    timeframe: str
    candle_id: str
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    previous_close: Decimal
    volume: Decimal
    turnover: Decimal
    completed: bool
    observed_at: datetime
    source: str
    instrument_version: str | None = None

    def to_market_observation(self, *, stale_after_seconds: int) -> MarketObservation:
        return MarketObservation(
            symbol=self.symbol,
            observed_at=self.observed_at,
            current_price=self.close,
            previous_price=self.previous_close,
            window=self.timeframe,
            source=f"{self.source}|category={self.category}",
            stale_after_seconds=stale_after_seconds,
        )

    def to_candle(self) -> BybitCandle:
        return BybitCandle(
            start_time_ms=int(self.open_time.timestamp() * 1000),
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
            turnover=self.turnover,
        )


def volume_window_from_futures_event(
    event: FuturesMarketEvent,
    *,
    previous_candles: tuple[BybitCandle, ...],
):
    from triggertrade.triggers.volume_confirmation import VolumeCandleWindow

    return VolumeCandleWindow(
        symbol=event.symbol,
        timeframe=event.timeframe,
        observed_at=event.observed_at,
        current_candle=event.to_candle(),
        previous_candles=previous_candles,
        current_candle_completed=event.completed,
    )


def futures_event_from_completed_candle(
    *,
    completed,
    source: str = "bybit_demo_linear_kline",
    instrument_version: str | None = None,
) -> FuturesMarketEvent:
    return FuturesMarketEvent(
        symbol=completed.symbol,
        category="linear",
        timeframe=completed.timeframe,
        candle_id=completed.candle_id,
        open_time=completed.open_time.astimezone(UTC),
        close_time=completed.close_time.astimezone(UTC),
        open=completed.candle.open,
        high=completed.candle.high,
        low=completed.candle.low,
        close=completed.candle.close,
        previous_close=completed.previous_candle.close,
        volume=completed.candle.volume,
        turnover=completed.candle.turnover,
        completed=True,
        observed_at=completed.close_time.astimezone(UTC),
        source=source,
        instrument_version=instrument_version,
    )
