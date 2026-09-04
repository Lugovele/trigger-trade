from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from triggertrade.config import ExecutionVenue, RiskRulesConfig, load_config
from triggertrade.execution import OrderStatus, OrderType, Side, TradeIntent
from triggertrade.execution.service import client_order_id_for_intent
from triggertrade.market_data import MarketObservation
from triggertrade.persistence import ExecutionRecord
from triggertrade.persistence import ExecutionStore
from triggertrade.risk import RULE_IDS, RiskManager


def test_approved_notional_within_limit(tmp_path):
    decision = _manager(tmp_path).evaluate(
        intent=_intent(),
        observation=_observation(),
        available_quote_balance=Decimal("100"),
    )

    assert decision.approved is True
    assert decision.checked_rule_ids == RULE_IDS
    assert decision.approved_notional == Decimal("5.0")


def test_over_max_notional_rejected(tmp_path):
    decision = _manager(tmp_path, max_notional=Decimal("4")).evaluate(
        intent=_intent(),
        observation=_observation(),
        available_quote_balance=Decimal("100"),
    )

    assert decision.approved is False
    assert "RSK-001" in decision.blocking_rule_ids


def test_insufficient_balance_rejected(tmp_path):
    decision = _manager(tmp_path).evaluate(
        intent=_intent(),
        observation=_observation(),
        available_quote_balance=Decimal("1"),
    )

    assert "RSK-003" in decision.blocking_rule_ids


def test_duplicate_open_intent_rejected(tmp_path):
    store = ExecutionStore(tmp_path / "orders.sqlite3")
    manager = _manager(tmp_path, store=store)
    first = manager.evaluate(
        intent=_intent(),
        observation=_observation(),
        available_quote_balance=Decimal("100"),
    )
    store.reserve(
        ExecutionRecord(
            intent_id="intent-1",
            risk_decision_id=first.risk_decision_id,
            client_order_id=client_order_id_for_intent("intent-1"),
            exchange_order_id=None,
            symbol="BTCUSDT",
            side="Buy",
            order_type="Limit",
            requested_qty="0.0001",
            requested_price="50000",
            status=OrderStatus.SUBMITTED,
            created_at="2026-09-05T00:00:00+00:00",
            updated_at="2026-09-05T00:00:00+00:00",
        )
    )

    duplicate = manager.evaluate(
        intent=_intent(),
        observation=_observation(),
        available_quote_balance=Decimal("100"),
    )

    assert "RSK-002" in duplicate.blocking_rule_ids


def test_stale_market_data_rejected(tmp_path):
    now = datetime(2026, 9, 5, tzinfo=UTC)
    decision = _manager(tmp_path).evaluate(
        intent=_intent(),
        observation=_observation(observed_at=now - timedelta(seconds=61)),
        available_quote_balance=Decimal("100"),
        now=now,
    )

    assert "RSK-005" in decision.blocking_rule_ids


def test_mismatched_market_observation_rejected(tmp_path):
    decision = _manager(tmp_path).evaluate(
        intent=_intent(),
        observation=_observation(symbol="ETHUSDT"),
        available_quote_balance=Decimal("100"),
    )

    assert not decision.approved
    assert "RSK-005" in decision.blocking_rule_ids


def test_local_paper_environment_allowed(tmp_path):
    config = load_config({"TRIGGERTRADE_EXECUTION_VENUE": "local_paper"})
    decision = _manager(tmp_path, config=config).evaluate(
        intent=_intent(),
        observation=_observation(),
        available_quote_balance=Decimal("100"),
    )

    assert decision.approved


def test_unsafe_bybit_live_endpoint_rejected(tmp_path):
    config = load_config(
        {
            "TRIGGERTRADE_EXECUTION_VENUE": "bybit_demo",
            "BYBIT_BASE_URL": "https://api.bybit.com",
        }
    )
    decision = _manager(tmp_path, config=config).evaluate(
        intent=_intent(),
        observation=_observation(),
        available_quote_balance=Decimal("100"),
    )

    assert "RSK-004" in decision.blocking_rule_ids


def test_local_paper_with_live_public_endpoint_rejected(tmp_path):
    config = load_config(
        {
            "TRIGGERTRADE_EXECUTION_VENUE": "local_paper",
            "BYBIT_BASE_URL": "https://api.bybit.com",
        }
    )
    decision = _manager(tmp_path, config=config).evaluate(
        intent=_intent(),
        observation=_observation(),
        available_quote_balance=Decimal("100"),
    )

    assert "RSK-004" in decision.blocking_rule_ids


def test_wrong_symbol_rejected(tmp_path):
    decision = _manager(tmp_path).evaluate(
        intent=replace(_intent(), symbol="ETHUSDT"),
        observation=_observation(symbol="ETHUSDT"),
        available_quote_balance=Decimal("100"),
    )

    assert "RSK-004" in decision.blocking_rule_ids


def _manager(tmp_path, *, max_notional=Decimal("6"), config=None, store=None):
    config = config or load_config({"TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO.value})
    return RiskManager(
        config=config,
        risk_config=RiskRulesConfig(max_demo_order_notional=max_notional),
        execution_store=store or ExecutionStore(tmp_path / "orders.sqlite3"),
    )


def _intent():
    return TradeIntent(
        intent_id="intent-1",
        symbol="BTCUSDT",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.0001"),
        price=Decimal("50000"),
    )


def _observation(symbol="BTCUSDT", observed_at=datetime(2026, 9, 5, tzinfo=UTC)):
    return MarketObservation(
        symbol=symbol,
        observed_at=observed_at,
        current_price=Decimal("50000"),
        previous_price=Decimal("51000"),
        window="1m",
        source="unit",
        stale_after_seconds=60,
    )
