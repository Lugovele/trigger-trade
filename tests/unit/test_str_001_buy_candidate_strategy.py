from datetime import UTC, datetime
from decimal import Decimal

from triggertrade.config import RiskRulesConfig, StrategyRuleConfig
from triggertrade.market_data import BybitInstrument, MarketObservation
from triggertrade.strategies import BuyCandidateStrategy
from triggertrade.triggers import Signal, SignalType


def test_buy_candidate_creates_trade_intent():
    intent = _strategy().decide(signal=_signal(SignalType.BUY_CANDIDATE), observation=_observation(), instrument=_instrument())

    assert intent is not None
    assert intent.side == "Buy"
    assert intent.strategy_rule_id == "STR-001"
    assert intent.reason_signal_ids == ("sig-1",)
    assert intent.reason_trigger_ids == ("TRG-001",)


def test_no_signal_creates_no_trade_intent():
    intent = _strategy().decide(signal=_signal(SignalType.NO_SIGNAL), observation=_observation(), instrument=_instrument())

    assert intent is None


def test_signal_observation_and_instrument_must_match():
    strategy = _strategy()
    signal = _signal(SignalType.BUY_CANDIDATE)
    mismatched_instrument = BybitInstrument(
        symbol="ETHUSDT",
        base_coin="ETH",
        quote_coin="USDT",
        price_tick=Decimal("0.01"),
        quantity_step=Decimal("0.0001"),
        min_order_quantity=Decimal("0.001"),
        min_order_amount=Decimal("5"),
    )

    assert strategy.decide(signal=signal, observation=_observation(symbol="ETHUSDT"), instrument=_instrument()) is None
    assert strategy.decide(signal=signal, observation=_observation(window="5m"), instrument=_instrument()) is None
    assert strategy.decide(signal=signal, observation=_observation(), instrument=mismatched_instrument) is None


def test_strategy_does_not_call_execution_adapter():
    class ExecutionLike:
        def create_limit_order(self):
            raise AssertionError("strategy must not call execution")

    intent = _strategy().decide(signal=_signal(SignalType.BUY_CANDIDATE), observation=_observation(), instrument=_instrument())

    assert intent is not None
    assert ExecutionLike


def test_same_input_produces_same_logical_decision():
    strategy = _strategy()
    kwargs = {"signal": _signal(SignalType.BUY_CANDIDATE), "observation": _observation(), "instrument": _instrument()}

    first = strategy.decide(**kwargs)
    second = strategy.decide(**kwargs)

    assert first is not None and second is not None
    assert first.intent_id == second.intent_id
    assert first.quantity == second.quantity
    assert first.price == second.price


def _strategy():
    return BuyCandidateStrategy(
        StrategyRuleConfig(enabled=True),
        RiskRulesConfig(max_demo_order_notional=Decimal("6")),
    )


def _signal(signal_type):
    return Signal(
        signal_id="sig-1",
        trigger_rule_id="TRG-001",
        trigger_rule_version="0.1.0",
        symbol="BTCUSDT",
        observed_at="2026-09-05T00:00:00+00:00",
        window="1m",
        input_snapshot={},
        condition_result=signal_type is SignalType.BUY_CANDIDATE,
        signal_type=signal_type,
    )


def _observation(symbol="BTCUSDT", window="1m"):
    return MarketObservation(
        symbol=symbol,
        observed_at=datetime(2026, 9, 5, tzinfo=UTC),
        current_price=Decimal("70000"),
        previous_price=Decimal("71000"),
        window=window,
        source="unit",
        stale_after_seconds=60,
    )


def _instrument():
    return BybitInstrument(
        symbol="BTCUSDT",
        base_coin="BTC",
        quote_coin="USDT",
        price_tick=Decimal("0.01"),
        quantity_step=Decimal("0.000001"),
        min_order_quantity=Decimal("0.00001"),
        min_order_amount=Decimal("5"),
    )
