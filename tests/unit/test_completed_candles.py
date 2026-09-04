from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from triggertrade.market_data import BybitCandle
from triggertrade.services.runtime import candle_id, latest_completed_candle, observation_from_completed_candle


def test_open_current_candle_is_ignored():
    current_open = datetime(2026, 9, 5, 12, 2, tzinfo=UTC)
    candles = (
        _candle(current_open - timedelta(minutes=2), "100"),
        _candle(current_open - timedelta(minutes=1), "99"),
        _candle(current_open, "98"),
    )

    completed = latest_completed_candle(
        candles,
        symbol="BTCUSDT",
        timeframe="1",
        now=current_open + timedelta(seconds=30),
    )

    assert completed is not None
    assert completed.open_time == current_open - timedelta(minutes=1)


def test_completed_candle_accepted_and_observation_uses_close_time():
    open_time = datetime(2026, 9, 5, 12, 1, tzinfo=UTC)
    completed = latest_completed_candle(
        (_candle(open_time - timedelta(minutes=1), "100"), _candle(open_time, "99")),
        symbol="BTCUSDT",
        timeframe="1",
        now=open_time + timedelta(minutes=1),
    )

    assert completed is not None
    assert completed.candle_id == candle_id("BTCUSDT", "1", open_time)
    observation = observation_from_completed_candle(completed, source="unit", stale_after_seconds=60)
    assert observation.current_price == Decimal("99")
    assert observation.previous_price == Decimal("100")
    assert observation.observed_at == open_time + timedelta(minutes=1)


def test_stale_completed_candle_rejected_by_observation():
    open_time = datetime(2026, 9, 5, 12, 1, tzinfo=UTC)
    completed = latest_completed_candle(
        (_candle(open_time - timedelta(minutes=1), "100"), _candle(open_time, "99")),
        symbol="BTCUSDT",
        timeframe="1",
        now=open_time + timedelta(minutes=1),
    )

    observation = observation_from_completed_candle(completed, source="unit", stale_after_seconds=60)

    assert observation.is_stale(open_time + timedelta(minutes=3))


def test_unsupported_timeframe_fails_closed():
    with pytest.raises(ValueError):
        latest_completed_candle((), symbol="BTCUSDT", timeframe="5", now=datetime.now(UTC))


def _candle(open_time: datetime, close: str) -> BybitCandle:
    return BybitCandle(
        start_time_ms=int(open_time.timestamp() * 1000),
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("1"),
        turnover=Decimal(close),
    )
