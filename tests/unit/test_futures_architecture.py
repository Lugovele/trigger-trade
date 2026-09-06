from decimal import Decimal
import json
from urllib.parse import parse_qs, urlparse

import pytest

from triggertrade.config import ApiCredentials, BybitEnvironment, TradingMode
from triggertrade.dashboard.__main__ import render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.execution import OrderStatus, OrderType
from triggertrade.execution.futures import (
    FUTURES_RISK_RULE_IDS,
    FundingEstimate,
    FuturesExecutionConfig,
    FuturesExecutionService,
    FuturesRiskDecision,
    FuturesRiskManager,
    FuturesTradeIntent,
    PositionAction,
    PositionState,
    estimate_costs,
    estimate_net_edge,
    futures_exchange_side,
    next_position_state,
)
from triggertrade.execution.position_lifecycle import build_fixed_protective_exit_plan
from triggertrade.exchanges import BybitApiError, BybitDemoClient
from triggertrade.market_data import ContractCategory, FuturesAccountState, FuturesInstrumentMetadata, RegimeCapability
from triggertrade.market_data.bybit import parse_linear_instrument
from triggertrade.market_data.futures import MarketRegimeContext
from triggertrade.persistence import FuturesExecutionStore, OperatorStateStore, TradingState


def test_position_state_machine_allows_only_explicit_open_close():
    assert next_position_state(PositionState.FLAT, PositionAction.OPEN_LONG) is PositionState.LONG
    assert next_position_state(PositionState.LONG, PositionAction.CLOSE_LONG) is PositionState.FLAT
    assert next_position_state(PositionState.FLAT, PositionAction.OPEN_SHORT) is PositionState.SHORT
    assert next_position_state(PositionState.SHORT, PositionAction.CLOSE_SHORT) is PositionState.FLAT
    assert next_position_state(PositionState.LONG, PositionAction.OPEN_SHORT) is None
    assert next_position_state(PositionState.SHORT, PositionAction.OPEN_LONG) is None


def test_long_short_intents_map_to_exchange_side_only_in_execution_boundary():
    assert futures_exchange_side(PositionAction.OPEN_LONG).value == "Buy"
    assert futures_exchange_side(PositionAction.CLOSE_SHORT).value == "Buy"
    assert futures_exchange_side(PositionAction.OPEN_SHORT).value == "Sell"
    assert futures_exchange_side(PositionAction.CLOSE_LONG).value == "Sell"


def test_default_futures_leverage_is_one_x():
    assert FuturesExecutionConfig().default_leverage == Decimal("1")
    assert FuturesExecutionConfig().max_configured_leverage == Decimal("1")
    assert _intent(PositionAction.OPEN_LONG).configured_leverage == Decimal("1")


def test_cost_and_net_edge_decimal_gate():
    cost = estimate_costs(
        notional=Decimal("10"),
        maker_fee_rate=Decimal("0.0002"),
        taker_fee_rate=Decimal("0.00055"),
        spread_cost=Decimal("0.01"),
        slippage_cost=Decimal("0.02"),
        funding_cost=Decimal("0"),
    )
    edge = estimate_net_edge(
        expected_gross_price_move=Decimal("0.10"),
        minimum_net_edge=Decimal("0.05"),
        cost=cost,
        funding=_funding(),
    )

    assert cost.total_estimated_cost == Decimal("0.03750")
    assert edge.expected_net_edge == Decimal("0.06250")
    assert edge.approved is True


def test_missing_expected_move_fails_net_edge_closed():
    edge = estimate_net_edge(
        expected_gross_price_move=None,
        minimum_net_edge=Decimal("0.01"),
        cost=_cost(),
        funding=_funding(),
    )

    assert edge.approved is False
    assert edge.reason == "expected gross move unavailable"


def test_market_regime_context_is_capability_gap_not_fake_sideways():
    context = MarketRegimeContext(
        context_id="regime-BTCUSDT-1m",
        version="market-regime-v1",
        symbol="BTCUSDT",
        timeframe="1m",
        observed_at="2026-09-05T00:00:00+00:00",
        capability=RegimeCapability.UNSUPPORTED,
    )

    assert context.label is None
    assert context.capability is RegimeCapability.UNSUPPORTED


def test_futures_risk_approves_safe_one_x_long(tmp_path):
    store = FuturesExecutionStore(tmp_path / "futures.sqlite3")
    decision = _risk_manager(store).evaluate(
        intent=_intent(PositionAction.OPEN_LONG, expected_move=Decimal("0.10")),
        instrument=_instrument(),
        account=_account(),
        cost=_cost(),
        funding=_funding(),
    )

    assert decision.approved is True
    assert decision.checked_rule_ids == FUTURES_RISK_RULE_IDS
    assert decision.position_state_after is PositionState.LONG
    assert "FRSK-007" in decision.unsupported_capability_rule_ids
    assert "FRSK-011" in decision.unsupported_capability_rule_ids


def test_futures_risk_rejects_leverage_margin_duplicate_and_net_edge(tmp_path):
    store = FuturesExecutionStore(tmp_path / "futures.sqlite3")
    manager = _risk_manager(store)

    high_leverage = manager.evaluate(
        intent=_intent(PositionAction.OPEN_LONG, leverage=Decimal("2"), expected_move=Decimal("1")),
        instrument=_instrument(),
        account=_account(),
        cost=_cost(),
        funding=_funding(),
    )
    assert "FRSK-003" in high_leverage.blocking_rule_ids

    zero_leverage = manager.evaluate(
        intent=_intent(PositionAction.OPEN_LONG, leverage=Decimal("0"), expected_move=Decimal("1")),
        instrument=_instrument(),
        account=_account(),
        cost=_cost(),
        funding=_funding(),
    )
    assert zero_leverage.approved is False
    assert "FRSK-003" in zero_leverage.blocking_rule_ids

    low_margin = manager.evaluate(
        intent=_intent(PositionAction.OPEN_LONG, expected_move=Decimal("1")),
        instrument=_instrument(),
        account=_account(available_margin=Decimal("1")),
        cost=_cost(),
        funding=_funding(),
    )
    assert "FRSK-004" in low_margin.blocking_rule_ids

    missing_edge = manager.evaluate(
        intent=_intent(PositionAction.OPEN_LONG),
        instrument=_instrument(),
        account=_account(),
        cost=_cost(),
        funding=_funding(),
    )
    assert "FRSK-010" in missing_edge.blocking_rule_ids

    unsupported_funding = manager.evaluate(
        intent=_intent(PositionAction.OPEN_LONG, expected_move=Decimal("1")),
        instrument=_instrument(),
        account=_account(),
        cost=_cost(),
        funding=FundingEstimate(None, None, Decimal("0"), Decimal("0"), capability="unsupported"),
    )
    assert "FRSK-010" in unsupported_funding.blocking_rule_ids


def test_futures_risk_rejects_invalid_leverage_step_metadata(tmp_path):
    store = FuturesExecutionStore(tmp_path / "futures.sqlite3")
    manager = _risk_manager(store)

    for bad_step in (Decimal("0"), Decimal("-0.01")):
        decision = manager.evaluate(
            intent=_intent(PositionAction.OPEN_LONG, expected_move=Decimal("1")),
            instrument=FuturesInstrumentMetadata(
                symbol="BTCUSDT",
                category=ContractCategory.LINEAR,
                contract_type="LinearPerpetual",
                settlement_asset="USDT",
                quantity_step=Decimal("0.001"),
                price_tick=Decimal("0.1"),
                minimum_order_quantity=Decimal("0.001"),
                minimum_notional=Decimal("5"),
                max_leverage=Decimal("100"),
                leverage_step=bad_step,
            ),
            account=_account(),
            cost=_cost(),
            funding=_funding(),
        )

        assert decision.approved is False
        assert "FRSK-003" in decision.blocking_rule_ids


def test_futures_risk_rejects_invalid_flip_and_non_demo_config(tmp_path):
    store = FuturesExecutionStore(tmp_path / "futures.sqlite3")
    flip = _risk_manager(store).evaluate(
        intent=_intent(PositionAction.OPEN_SHORT, current=PositionState.LONG, expected_move=Decimal("1")),
        instrument=_instrument(),
        account=_account(),
        cost=_cost(),
        funding=_funding(),
    )
    assert "FRSK-005" in flip.blocking_rule_ids

    unsafe = _risk_manager(
        store,
        config=FuturesExecutionConfig(bybit_base_url="https://api.bybit.com"),
    ).evaluate(
        intent=_intent(PositionAction.OPEN_LONG, expected_move=Decimal("1")),
        instrument=_instrument(),
        account=_account(),
        cost=_cost(),
        funding=_funding(),
    )
    assert "FRSK-006" in unsafe.blocking_rule_ids


def test_futures_risk_rejects_mismatched_account_state(tmp_path):
    store = FuturesExecutionStore(tmp_path / "futures.sqlite3")
    manager = _risk_manager(store)

    wrong_symbol = manager.evaluate(
        intent=_intent(PositionAction.OPEN_LONG, expected_move=Decimal("1")),
        instrument=_instrument(),
        account=FuturesAccountState(
            symbol="ETHUSDT",
            category=ContractCategory.LINEAR,
            settlement_asset="USDT",
            available_margin=Decimal("100"),
        ),
        cost=_cost(),
        funding=_funding(),
    )
    assert "FRSK-006" in wrong_symbol.blocking_rule_ids

    inconsistent_flat = manager.evaluate(
        intent=_intent(PositionAction.OPEN_LONG, expected_move=Decimal("1")),
        instrument=_instrument(),
        account=_account(position_size=Decimal("0.1")),
        cost=_cost(),
        funding=_funding(),
    )
    assert "FRSK-005" in inconsistent_flat.blocking_rule_ids


def test_futures_risk_rejects_close_quantity_larger_than_position(tmp_path):
    store = FuturesExecutionStore(tmp_path / "futures.sqlite3")
    manager = _risk_manager(store)

    oversized_close_long = manager.evaluate(
        intent=_intent(PositionAction.CLOSE_LONG, current=PositionState.LONG, expected_move=Decimal("1")),
        instrument=_instrument(),
        account=_account(position_size=Decimal("0.0005")),
        cost=_cost(),
        funding=_funding(),
    )
    oversized_close_short = manager.evaluate(
        intent=_intent(PositionAction.CLOSE_SHORT, current=PositionState.SHORT, expected_move=Decimal("1")),
        instrument=_instrument(),
        account=_account(position_size=Decimal("-0.0005")),
        cost=_cost(),
        funding=_funding(),
    )

    assert "FRSK-005" in oversized_close_long.blocking_rule_ids
    assert "FRSK-005" in oversized_close_short.blocking_rule_ids


def test_futures_execution_requires_approved_risk_and_blocks_spot_leak(tmp_path):
    service = _service(tmp_path)
    intent = _intent(PositionAction.OPEN_LONG, category=ContractCategory.LINEAR, expected_move=Decimal("1"))
    risk = _risk_manager(FuturesExecutionStore(tmp_path / "other.sqlite3")).evaluate(
        intent=intent,
        instrument=_instrument(),
        account=_account(),
        cost=_cost(),
        funding=_funding(),
    )

    service.submit_approved_limit_order(intent=intent, risk_decision=risk)

    assert service._adapter.create_calls == 1
    assert service._adapter.created[0]["action"] is PositionAction.OPEN_LONG

    with pytest.raises(Exception, match="linear"):
        service.submit_approved_limit_order(
            intent=_intent(PositionAction.OPEN_LONG, category="spot", expected_move=Decimal("1")),
            risk_decision=risk,
        )


def test_operator_pause_blocks_new_active_futures_but_reconcile_continues(tmp_path):
    db = tmp_path / "futures.sqlite3"
    operator = OperatorStateStore(db)
    operator.pause()
    service = _service(
        tmp_path,
        db=db,
        adapter=FakeFuturesAdapter(order_status="Filled"),
        operator_state=lambda: operator.get_trading_state().state.value,
        lane="ACTIVE",
    )
    intent = _intent(PositionAction.OPEN_LONG, expected_move=Decimal("1"))
    risk = _risk_manager(FuturesExecutionStore(db)).evaluate(
        intent=intent,
        instrument=_instrument(),
        account=_account(),
        cost=_cost(),
        funding=_funding(),
    )

    with pytest.raises(Exception, match="operator pause"):
        service.submit_approved_limit_order(intent=intent, risk_decision=risk)
    assert service._adapter.create_calls == 0
    assert FuturesExecutionStore(db).get_by_intent(intent.intent_id) is None

    record, _ = FuturesExecutionStore(db).reserve(_record())
    assert service.reconcile(record).status is OrderStatus.FILLED


def test_active_futures_execution_requires_operator_state_callback(tmp_path):
    service = _service(tmp_path, lane="ACTIVE")
    intent = _intent(PositionAction.OPEN_LONG, expected_move=Decimal("1"))
    risk = _approved_risk(intent.intent_id)

    with pytest.raises(Exception, match="operator trading state"):
        service.submit_approved_limit_order(intent=intent, risk_decision=risk)

    assert service._adapter.create_calls == 0
    assert FuturesExecutionStore(tmp_path / "futures.sqlite3").get_by_intent(intent.intent_id) is None


def test_manual_demo_validation_lane_is_not_active_pause_path(tmp_path):
    service = _service(tmp_path, lane="MANUAL_DEMO_VALIDATION")
    intent = _intent(PositionAction.OPEN_LONG, expected_move=Decimal("1"))
    risk = _approved_risk(intent.intent_id)

    record = service.submit_approved_limit_order(intent=intent, risk_decision=risk)

    assert record.status is OrderStatus.SUBMITTED
    assert service._adapter.create_calls == 1


def test_paused_idempotent_retry_reconciles_existing_futures_record(tmp_path):
    db = tmp_path / "futures.sqlite3"
    store = FuturesExecutionStore(db)
    existing, _ = store.reserve(_record())
    operator = OperatorStateStore(db)
    operator.pause()
    service = _service(
        tmp_path,
        db=db,
        adapter=FakeFuturesAdapter(order_status="Filled"),
        operator_state=lambda: operator.get_trading_state().state.value,
        lane="ACTIVE",
    )

    result = service.submit_approved_limit_order(
        intent=_intent(PositionAction.OPEN_LONG, expected_move=Decimal("1")),
        risk_decision=_approved_risk(existing.intent_id),
    )

    assert result.status is OrderStatus.FILLED
    assert service._adapter.create_calls == 0


def test_idempotency_timeout_reconcile_does_not_duplicate(tmp_path):
    adapter = FakeFuturesAdapter(order_status="New", raise_on_create=True)
    service = _service(tmp_path, adapter=adapter)
    intent = _intent(PositionAction.OPEN_LONG, expected_move=Decimal("1"))
    risk = _risk_manager(service._store).evaluate(
        intent=intent,
        instrument=_instrument(),
        account=_account(),
        cost=_cost(),
        funding=_funding(),
    )

    first = service.submit_approved_limit_order(intent=intent, risk_decision=risk)
    second = service.submit_approved_limit_order(intent=intent, risk_decision=risk)

    assert first.client_order_id == second.client_order_id
    assert adapter.create_calls == 1
    assert adapter.reconcile_calls >= 1


def test_bybit_linear_order_shape_and_category_enforcement():
    seen = []

    def transport(request, timeout):
        seen.append(request)
        return _payload({"orderId": "exchange-1", "orderLinkId": "ttf-safe"})

    client = BybitDemoClient(
        credentials=ApiCredentials("unit-key", "unit-signing-value"),
        transport=transport,
        clock_ms=lambda: 123,
    )
    client._create_linear_limit_order(
        symbol="BTCUSDT",
        side="Buy",
        qty="0.001",
        price="10000.00",
        order_link_id="ttf-safe",
    )

    body = json.loads(seen[0].data.decode("utf-8"))
    assert body["category"] == "linear"
    assert body["timeInForce"] == "PostOnly"
    assert body["reduceOnly"] is False
    assert "isLeverage" not in body


def test_bybit_linear_fetch_cancel_use_linear_category():
    seen = []

    def transport(request, timeout):
        seen.append(request)
        return _payload({"list": []} if request.get_method() == "GET" else {"orderLinkId": "ttf-safe"})

    client = BybitDemoClient(credentials=ApiCredentials("unit-key", "unit-signing-value"), transport=transport)
    client._get_linear_order_realtime("BTCUSDT", "ttf-safe")
    client._get_linear_order_history("BTCUSDT", "ttf-safe")
    client._get_linear_executions("BTCUSDT", "ttf-safe")
    client._cancel_linear_order(symbol="BTCUSDT", order_link_id="ttf-safe")

    queries = [parse_qs(urlparse(request.full_url).query) for request in seen[:3]]
    assert queries[0]["category"] == ["linear"]
    assert queries[1]["category"] == ["linear"]
    assert queries[2]["category"] == ["linear"]
    assert "/v5/execution/list" in seen[2].full_url
    assert json.loads(seen[3].data.decode("utf-8"))["category"] == "linear"


def test_parse_linear_instrument_metadata():
    metadata = parse_linear_instrument(
        {
            "list": [
                {
                    "symbol": "BTCUSDT",
                    "contractType": "LinearPerpetual",
                    "quoteCoin": "USDT",
                    "settleCoin": "USDT",
                    "priceFilter": {"tickSize": "0.10"},
                    "lotSizeFilter": {"qtyStep": "0.001", "minOrderQty": "0.001", "minNotionalValue": "5"},
                    "leverageFilter": {"minLeverage": "1", "maxLeverage": "100", "leverageStep": "0.01"},
                }
            ]
        }
    )

    assert metadata.category is ContractCategory.LINEAR
    assert metadata.contract_type == "LinearPerpetual"
    assert metadata.settlement_asset == "USDT"
    assert metadata.max_leverage == Decimal("100")


def test_dashboard_futures_projection_is_read_only_and_no_fake_metrics(tmp_path):
    db = tmp_path / "dashboard.sqlite3"
    store = FuturesExecutionStore(db)
    store.reserve(_record())

    html = render_dashboard(DashboardReadModel(db), initial_page="analytics")

    assert "Futures readiness" in html
    assert "OPEN_LONG" in html
    assert "linear" in html
    assert "No futures execution records yet" not in html
    assert "/v5/order/create" not in html
    assert "BYBIT_API_SECRET" not in html


def _service(tmp_path, *, db=None, adapter=None, config=None, operator_state=None, lane=None):
    path = db or tmp_path / "futures.sqlite3"
    return FuturesExecutionService(
        config=config or FuturesExecutionConfig(),
        adapter=adapter or FakeFuturesAdapter(order_status="New"),
        store=FuturesExecutionStore(path),
        instrument=_instrument(),
        account=_account(),
        execution_lane=lane,
        operator_trading_state=operator_state,
    )


def _risk_manager(store, *, config=None):
    return FuturesRiskManager(
        config=config or FuturesExecutionConfig(),
        store=store,
        minimum_net_edge=Decimal("0.01"),
        max_position_notional=Decimal("20"),
        max_simultaneous_exposure=Decimal("20"),
    )


def _intent(action, *, current=PositionState.FLAT, leverage=Decimal("1"), expected_move=None, category=ContractCategory.LINEAR):
    tp, sl = (None, None)
    if action in {PositionAction.OPEN_LONG, PositionAction.OPEN_SHORT} and category is ContractCategory.LINEAR:
        tp, sl = build_fixed_protective_exit_plan(
            action=action,
            entry_price=Decimal("10000.0"),
            take_profit_pct=Decimal("0.01"),
            stop_loss_pct=Decimal("0.0025"),
            price_tick=Decimal("0.1"),
            calculated_at="2026-09-05T00:00:00+00:00",
        )
    return FuturesTradeIntent(
        intent_id="futures-intent-1",
        symbol="BTCUSDT",
        category=category,
        action=action,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.001"),
        price=Decimal("10000.0"),
        current_position_state=current,
        configured_leverage=leverage,
        expected_gross_price_move=expected_move,
        lane="ACTIVE",
        take_profit=tp,
        stop_loss=sl,
        minimum_risk_reward=Decimal("1.5"),
    )


def _instrument():
    return FuturesInstrumentMetadata(
        symbol="BTCUSDT",
        category=ContractCategory.LINEAR,
        contract_type="LinearPerpetual",
        settlement_asset="USDT",
        quantity_step=Decimal("0.001"),
        price_tick=Decimal("0.1"),
        minimum_order_quantity=Decimal("0.001"),
        minimum_notional=Decimal("5"),
        max_leverage=Decimal("100"),
    )


def _account(*, available_margin=Decimal("100"), position_size=Decimal("0")):
    return FuturesAccountState(
        symbol="BTCUSDT",
        category=ContractCategory.LINEAR,
        settlement_asset="USDT",
        available_margin=available_margin,
        configured_leverage=Decimal("1"),
        position_size=position_size,
        mark_price=Decimal("10000.0"),
    )


def _cost():
    return estimate_costs(
        notional=Decimal("10"),
        maker_fee_rate=Decimal("0.0002"),
        taker_fee_rate=Decimal("0.00055"),
        spread_cost=Decimal("0"),
        slippage_cost=Decimal("0"),
        funding_cost=Decimal("0"),
    )


def _funding():
    return FundingEstimate(
        funding_rate=Decimal("0"),
        next_funding_time="2026-09-05T08:00:00+00:00",
        expected_holding_overlap=Decimal("0"),
        estimated_funding_impact=Decimal("0"),
    )


def _record():
    return __import__("triggertrade.persistence", fromlist=["FuturesExecutionRecord"]).FuturesExecutionRecord(
        intent_id="futures-intent-1",
        risk_decision_id="frisk-1",
        client_order_id="ttf-safe",
        exchange_order_id=None,
        symbol="BTCUSDT",
        category="linear",
        position_action="OPEN_LONG",
        exchange_side="Buy",
        order_type="Limit",
        requested_qty="0.001",
        requested_price="10000.0",
        leverage="1",
        status=OrderStatus.SUBMITTED,
        created_at="2026-09-05T00:00:00+00:00",
        updated_at="2026-09-05T00:00:00+00:00",
        margin_mode="ISOLATED",
        position_mode="ONE_WAY",
        expected_net_edge="0.01",
    )


def _approved_risk(intent_id: str):
    return FuturesRiskDecision(
        risk_decision_id="frisk-approved",
        intent_id=intent_id,
        approved=True,
        checked_rule_ids=FUTURES_RISK_RULE_IDS,
        approved_quantity=Decimal("0.001"),
        approved_notional=Decimal("10.0000"),
        net_edge=estimate_net_edge(
            expected_gross_price_move=Decimal("1"),
            minimum_net_edge=Decimal("0.01"),
            cost=_cost(),
            funding=_funding(),
        ),
    )


class FakeFuturesAdapter:
    def __init__(self, *, order_status: str, raise_on_create: bool = False):
        self.order_status = order_status
        self.raise_on_create = raise_on_create
        self.create_calls = 0
        self.cancel_calls = 0
        self.reconcile_calls = 0
        self.created = []

    def create_limit_order(self, **kwargs):
        self.create_calls += 1
        self.created.append(kwargs)
        if self.raise_on_create:
            raise BybitApiError("Bybit API request failed: TimeoutError")
        return type("Response", (), {"result": {"orderId": "exchange-1"}})()

    def cancel_order(self, **kwargs):
        self.cancel_calls += 1
        return type("Response", (), {"result": {"orderLinkId": kwargs["client_order_id"]}})()

    def reconcile_order(self, **kwargs):
        self.reconcile_calls += 1
        return {"orderId": "exchange-1", "orderStatus": self.order_status}

    def map_order_status(self, raw_status):
        if raw_status == "Filled":
            return OrderStatus.FILLED
        if raw_status == "Cancelled":
            return OrderStatus.CANCELLED
        return OrderStatus.SUBMITTED


def _payload(result):
    return json.dumps({"retCode": 0, "retMsg": "OK", "result": result}).encode()
