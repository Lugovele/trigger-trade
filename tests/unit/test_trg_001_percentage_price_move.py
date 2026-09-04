from datetime import UTC, datetime, timedelta
from decimal import Decimal

from triggertrade.config import TriggerRuleConfig
from triggertrade.market_data import MarketObservation
from triggertrade.triggers import PercentagePriceMoveTrigger, SignalType


def test_threshold_not_reached_returns_no_signal():
    signal = _trigger().evaluate(_observation(current=Decimal("99.01"), previous=Decimal("100")))

    assert signal.signal_type is SignalType.NO_SIGNAL
    assert signal.condition_result is False


def test_exact_boundary_returns_buy_candidate():
    signal = _trigger().evaluate(_observation(current=Decimal("99.00"), previous=Decimal("100")))

    assert signal.signal_type is SignalType.BUY_CANDIDATE
    assert signal.condition_result is True


def test_threshold_exceeded_returns_buy_candidate():
    signal = _trigger().evaluate(_observation(current=Decimal("98.99"), previous=Decimal("100")))

    assert signal.signal_type is SignalType.BUY_CANDIDATE


def test_missing_data_returns_no_signal():
    signal = _trigger().evaluate(_observation(current=None, previous=Decimal("100")))

    assert signal.signal_type is SignalType.NO_SIGNAL
    assert signal.reason == "missing_price"


def test_stale_data_returns_no_signal():
    now = datetime(2026, 9, 5, tzinfo=UTC)
    signal = _trigger().evaluate(
        _observation(
            current=Decimal("98"),
            previous=Decimal("100"),
            observed_at=now - timedelta(seconds=61),
        ),
        now=now,
    )

    assert signal.signal_type is SignalType.NO_SIGNAL
    assert signal.reason == "stale_observation"


def test_wrong_symbol_or_window_returns_no_signal():
    assert _trigger().evaluate(_observation(symbol="ETHUSDT")).reason == "wrong_symbol"
    assert _trigger().evaluate(_observation(window="5m")).reason == "wrong_window"


def test_deterministic_repeatability():
    trigger = _trigger()
    observation = _observation(current=Decimal("99"), previous=Decimal("100"))

    first = trigger.evaluate(observation)
    second = trigger.evaluate(observation)

    assert first == second


def _trigger():
    return PercentagePriceMoveTrigger(
        TriggerRuleConfig(threshold_pct=Decimal("-1.0"), lookback_window="1m")
    )


def _observation(
    *,
    current=Decimal("99"),
    previous=Decimal("100"),
    symbol="BTCUSDT",
    window="1m",
    observed_at=datetime(2026, 9, 5, tzinfo=UTC),
):
    return MarketObservation(
        symbol=symbol,
        observed_at=observed_at,
        current_price=current,
        previous_price=previous,
        window=window,
        source="unit",
        stale_after_seconds=60,
    )
