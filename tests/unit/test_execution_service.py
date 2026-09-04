from decimal import Decimal

import pytest

from triggertrade.config import ExecutionVenue, load_config
from triggertrade.execution import (
    ExecutionError,
    ExecutionService,
    OrderStatus,
    OrderType,
    RiskDecision,
    Side,
    TradeIntent,
)
from triggertrade.execution.bybit import BybitExecutionAdapter
from triggertrade.exchanges import BybitApiError
from triggertrade.market_data import BybitInstrument
from triggertrade.persistence import ExecutionStore


def test_approved_risk_decision_required(tmp_path):
    service = _service(tmp_path)
    intent = _intent()

    with pytest.raises(ExecutionError):
        service.submit_approved_limit_order(
            intent=intent,
            risk_decision=RiskDecision("risk-1", intent.intent_id, False),
        )


def test_wrong_intent_risk_binding_rejected(tmp_path):
    service = _service(tmp_path)

    with pytest.raises(ExecutionError):
        service.submit_approved_limit_order(
            intent=_intent(),
            risk_decision=RiskDecision("risk-1", "other-intent", True),
        )


def test_demo_environment_allowed_and_order_submitted(tmp_path):
    adapter = FakeAdapter(order_status="New")
    service = _service(tmp_path, adapter=adapter)

    record = service.submit_approved_limit_order(intent=_intent(), risk_decision=_risk())

    assert record.status is OrderStatus.SUBMITTED
    assert record.exchange_order_id == "exchange-1"
    assert adapter.create_calls == 1


def test_live_endpoint_blocked(tmp_path):
    config = load_config(
        {
            "TRIGGERTRADE_EXECUTION_VENUE": "bybit_demo",
            "BYBIT_BASE_URL": "https://api.bybit.com",
        }
    )
    service = _service(tmp_path, config=config)

    with pytest.raises(ExecutionError):
        service.submit_approved_limit_order(intent=_intent(), risk_decision=_risk())


def test_buy_submission_requires_available_quote_balance(tmp_path):
    service = _service(tmp_path, available_quote_balance=None)

    with pytest.raises(ExecutionError):
        service.submit_approved_limit_order(intent=_intent(), risk_decision=_risk())


def test_insufficient_available_quote_balance_blocks_submission(tmp_path):
    service = _service(tmp_path, available_quote_balance=Decimal("1"))

    with pytest.raises(ExecutionError):
        service.submit_approved_limit_order(intent=_intent(), risk_decision=_risk())


def test_non_spot_category_blocked_by_config_loader():
    with pytest.raises(Exception):
        load_config({"TRIGGERTRADE_MARKET": "linear"})


def test_same_intent_cannot_create_two_submissions(tmp_path):
    adapter = FakeAdapter(order_status="New")
    service = _service(tmp_path, adapter=adapter)
    intent = _intent()
    risk = _risk()

    first = service.submit_approved_limit_order(intent=intent, risk_decision=risk)
    second = service.submit_approved_limit_order(intent=intent, risk_decision=risk)

    assert first.client_order_id == second.client_order_id
    assert adapter.create_calls == 1


def test_timeout_then_reconciliation_does_not_duplicate(tmp_path):
    adapter = FakeAdapter(order_status="New", raise_on_create=True)
    service = _service(tmp_path, adapter=adapter)

    record = service.submit_approved_limit_order(intent=_intent(), risk_decision=_risk())

    assert record.status is OrderStatus.SUBMITTED
    assert adapter.create_calls == 1
    assert adapter.reconcile_calls >= 1


def test_cancel_open_order_reconciles_terminal_state(tmp_path):
    adapter = FakeAdapter(order_status="Cancelled")
    service = _service(tmp_path, adapter=adapter)
    record = service.submit_approved_limit_order(intent=_intent(), risk_decision=_risk())

    cancelled = service.cancel(record)

    assert cancelled.status is OrderStatus.CANCELLED
    assert adapter.cancel_calls == 1


def test_restart_recovery_reconciles_unresolved_order(tmp_path):
    store = ExecutionStore(tmp_path / "orders.sqlite3")
    adapter = FakeAdapter(order_status="New")
    first_service = _service(tmp_path, adapter=adapter, store=store)
    first_service.submit_approved_limit_order(intent=_intent(), risk_decision=_risk())

    second_service = _service(tmp_path, adapter=FakeAdapter(order_status="Filled"), store=store)
    recovered = second_service.recover_unresolved()

    assert recovered[0].status is OrderStatus.FILLED


def _service(tmp_path, *, adapter=None, config=None, store=None, available_quote_balance=Decimal("100")):
    config = config or load_config({"TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO.value})
    adapter = adapter or FakeAdapter(order_status="New")
    return ExecutionService(
        config=config,
        adapter=adapter,
        store=store or ExecutionStore(tmp_path / "orders.sqlite3"),
        instrument=BybitInstrument(
            symbol="BTCUSDT",
            base_coin="BTC",
            quote_coin="USDT",
            price_tick=Decimal("0.01"),
            quantity_step=Decimal("0.000001"),
            min_order_quantity=Decimal("0.00001"),
            min_order_amount=Decimal("5"),
        ),
        available_quote_balance=available_quote_balance,
    )


def _intent():
    return TradeIntent(
        intent_id="intent-1",
        symbol="BTCUSDT",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.001"),
        price=Decimal("10000.00"),
    )


def _risk():
    return RiskDecision("risk-1", "intent-1", True)


class FakeAdapter(BybitExecutionAdapter):
    def __init__(self, *, order_status: str, raise_on_create: bool = False):
        self.order_status = order_status
        self.raise_on_create = raise_on_create
        self.create_calls = 0
        self.cancel_calls = 0
        self.reconcile_calls = 0

    def create_limit_order(self, **kwargs):
        self.create_calls += 1
        if self.raise_on_create:
            raise BybitApiError("Bybit API request failed: TimeoutError")
        return type("Response", (), {"result": {"orderId": "exchange-1"}})()

    def cancel_order(self, **kwargs):
        self.cancel_calls += 1
        return type("Response", (), {"result": {"orderLinkId": kwargs["client_order_id"]}})()

    def reconcile_order(self, **kwargs):
        self.reconcile_calls += 1
        return {"orderId": "exchange-1", "orderStatus": self.order_status}
