from datetime import UTC, datetime, timedelta
from decimal import Decimal

from triggertrade.market_data import BybitCandle
from triggertrade.triggers import (
    RobustVolumeConfirmationTrigger,
    VolumeCandleWindow,
    VolumeConfirmationResult,
    empirical_percentile_rank,
    median_decimal,
)


def test_median_for_sixty_uses_middle_pair_average():
    values = tuple(Decimal(i) for i in range(1, 61))

    assert median_decimal(values) == Decimal("30.5")


def test_percentile_rank_counts_ties_as_less_or_equal():
    previous = (Decimal("1"),) * 54 + (Decimal("2"),) * 6

    assert empirical_percentile_rank(Decimal("1"), previous) == Decimal("90.0")


def test_trg_002_confirms_on_exact_inclusive_boundaries():
    previous = [_candle(i, "1") for i in range(54)] + [_candle(i, "3") for i in range(54, 60)]
    window = _window(current=_candle(60, "2"), previous=previous)

    result = RobustVolumeConfirmationTrigger().evaluate(window, now=_now())

    assert result.result is VolumeConfirmationResult.CONFIRMED
    assert result.condition_result is True
    assert result.median_volume_60 == "1"
    assert result.relative_volume == "2"
    assert result.volume_percentile == "90.0"


def test_threshold_not_met_returns_not_confirmed():
    previous = [_candle(i, "10") for i in range(60)]

    result = RobustVolumeConfirmationTrigger().evaluate(_window(current=_candle(60, "11"), previous=previous), now=_now())

    assert result.result is VolumeConfirmationResult.NOT_CONFIRMED
    assert result.condition_result is False


def test_insufficient_data_missing_current_zero_median_stale_and_incomplete_fail_closed():
    trigger = RobustVolumeConfirmationTrigger()

    assert trigger.evaluate(_window(current=_candle(60, "2"), previous=[_candle(i, "1") for i in range(59)]), now=_now()).missing_data_reason == "insufficient_previous_candles"
    assert trigger.evaluate(_window(current=None, previous=[_candle(i, "1") for i in range(60)]), now=_now()).missing_data_reason == "missing_current_volume"
    assert trigger.evaluate(_window(current=_candle(60, "2"), previous=[_candle(i, "0") for i in range(60)]), now=_now()).missing_data_reason == "zero_median_volume"
    stale = _window(current=_candle(60, "2"), previous=[_candle(i, "1") for i in range(60)], observed_at=_now() - timedelta(minutes=5))
    assert trigger.evaluate(stale, now=_now()).stale_data_reason == "stale_candle"
    incomplete = _window(current=_candle(60, "2"), previous=[_candle(i, "1") for i in range(60)], completed=False)
    assert trigger.evaluate(incomplete, now=_now()).missing_data_reason == "current_candle_not_completed"


def test_deterministic_repeatability():
    previous = [_candle(i, "1") for i in range(60)]
    window = _window(current=_candle(60, "2"), previous=previous)
    trigger = RobustVolumeConfirmationTrigger()

    first = trigger.evaluate(window, now=_now())
    second = trigger.evaluate(window, now=_now())

    assert first == second


def _window(current, previous, observed_at=None, completed=True):
    return VolumeCandleWindow(
        symbol="BTCUSDT",
        timeframe="1m",
        observed_at=observed_at or datetime(2026, 9, 5, 12, 1, tzinfo=UTC),
        current_candle=current,
        previous_candles=tuple(previous),
        current_candle_completed=completed,
    )


def _candle(index: int, volume: str) -> BybitCandle:
    return BybitCandle(
        start_time_ms=1_778_240_000_000 + index * 60_000,
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal(volume),
        turnover=Decimal("0"),
    )


def _now():
    return datetime(2026, 9, 5, 12, 1, 30, tzinfo=UTC)
