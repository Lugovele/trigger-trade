from decimal import Decimal

from triggertrade.execution import OrderType, RiskDecision, Side, TradeIntent
from triggertrade.persistence import TraceStore
from triggertrade.triggers import Signal, SignalType


def test_trace_store_reconstructs_signal_strategy_and_risk(tmp_path):
    store = TraceStore(tmp_path / "trace.sqlite3")
    signal = Signal(
        signal_id="sig-1",
        trigger_rule_id="TRG-001",
        trigger_rule_version="0.1.0",
        symbol="BTCUSDT",
        observed_at="2026-09-05T00:00:00+00:00",
        window="1m",
        input_snapshot={"price_change_pct": "-1.0"},
        condition_result=True,
        signal_type=SignalType.BUY_CANDIDATE,
    )
    intent = TradeIntent(
        intent_id="intent-1",
        symbol="BTCUSDT",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.0001"),
        price=Decimal("50000"),
        strategy_rule_id="STR-001",
        strategy_rule_version="0.1.0",
        reason_signal_ids=("sig-1",),
        reason_trigger_ids=("TRG-001",),
    )
    risk = RiskDecision(
        risk_decision_id="risk-1",
        intent_id="intent-1",
        approved=True,
        checked_rule_ids=("RSK-001",),
        approved_notional=Decimal("5"),
        approved_quantity=Decimal("0.0001"),
    )

    store.save_trigger_evaluation(signal)
    store.save_strategy_decision(intent)
    store.save_risk_decision(risk)

    trace = store.trace_for_intent("intent-1")

    assert trace["signals"][0]["signal_id"] == "sig-1"
    assert trace["strategy"]["strategy_rule_id"] == "STR-001"
    assert trace["risk"]["risk_decision_id"] == "risk-1"
