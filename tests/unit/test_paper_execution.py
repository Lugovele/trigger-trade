from decimal import Decimal

import pytest

from triggertrade.config import ExecutionVenue, load_config
from triggertrade.execution import ExecutionError, ExecutionService, OrderStatus, OrderType, PaperExecutionAdapter, RiskDecision, Side, TradeIntent
from triggertrade.execution.bybit import BybitExecutionAdapter
from triggertrade.exchanges import BybitDemoClient
from triggertrade.market_data import BybitInstrument
from triggertrade.persistence import ExecutionStore


def test_paper_execution_requires_approved_risk_decision(tmp_path):
    service = _service(tmp_path)
    intent = _intent()

    with pytest.raises(ExecutionError):
        service.submit_approved_limit_order(intent=intent, risk_decision=RiskDecision("risk-1", intent.intent_id, False))


def test_paper_execution_fills_and_persists_fill(tmp_path):
    store = ExecutionStore(tmp_path / "paper.sqlite3")
    adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    service = _service(tmp_path, store=store, adapter=adapter)

    record = service.submit_approved_limit_order(intent=_intent(), risk_decision=_risk())
    record = service.reconcile(record)

    assert record.status is OrderStatus.FILLED
    fills = store.fills_for_intent(record.intent_id)
    assert len(fills) == 1
    assert fills[0].price == "10000.00"
    assert fills[0].fee == "0"
    assert adapter.create_calls == 1


def test_same_intent_does_not_duplicate_paper_lifecycle_or_fill(tmp_path):
    store = ExecutionStore(tmp_path / "paper.sqlite3")
    adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    service = _service(tmp_path, store=store, adapter=adapter)
    intent = _intent()
    risk = _risk()

    first = service.reconcile(service.submit_approved_limit_order(intent=intent, risk_decision=risk))
    second = service.reconcile(service.submit_approved_limit_order(intent=intent, risk_decision=risk))

    assert first.client_order_id == second.client_order_id
    assert adapter.create_calls == 1
    assert store.count_by_client_order_id(first.client_order_id) == 1
    assert len(store.fills_for_intent(intent.intent_id)) == 1


def test_local_paper_rejects_private_bybit_order_adapter(tmp_path):
    config = load_config({"TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.LOCAL_PAPER.value})
    service = _service(tmp_path, config=config, adapter=BybitExecutionAdapter(BybitDemoClient(config=config.bybit)))

    with pytest.raises(ExecutionError, match="paper adapter"):
        service.submit_approved_limit_order(intent=_intent(), risk_decision=_risk())


def _service(tmp_path, *, store=None, adapter=None, config=None):
    return ExecutionService(
        config=config or load_config({"TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.LOCAL_PAPER.value}),
        adapter=adapter or PaperExecutionAdapter(clock_ms=lambda: 123),
        store=store or ExecutionStore(tmp_path / "paper.sqlite3"),
        instrument=_instrument(),
        available_quote_balance=Decimal("100"),
    )


def _intent():
    return TradeIntent(
        intent_id="intent-paper-1",
        symbol="BTCUSDT",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.001"),
        price=Decimal("10000.00"),
    )


def _risk():
    return RiskDecision(
        risk_decision_id="risk-paper-1",
        intent_id="intent-paper-1",
        approved=True,
        checked_rule_ids=("RSK-001", "RSK-002", "RSK-003", "RSK-004", "RSK-005"),
        blocking_rule_ids=(),
        approved_quantity=Decimal("0.001"),
        approved_notional=Decimal("10.00000"),
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
