from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from triggertrade.execution import OrderStatus, OrderType
from triggertrade.execution.futures import (
    FUTURES_RISK_RULE_IDS,
    FundingEstimate,
    FuturesExecutionConfig,
    FuturesRiskDecision,
    FuturesRiskManager,
    FuturesTradeIntent,
    PositionAction,
    PositionState,
    estimate_costs,
    estimate_net_edge,
)
from triggertrade.execution.position_lifecycle import (
    CloseReason,
    FuturesPositionLifecycleService,
    PositionRiskConfig,
    PositionStatus,
    ProtectiveExitMode,
    TakeProfitPlan,
    build_fixed_protective_exit_plan,
    calculate_position_size,
    evaluate_risk_reward,
    futures_position_id,
    should_trigger_protective_exit,
    unrealized_pnl_pct,
)
from triggertrade.execution.service import ExecutionError
from triggertrade.market_data import ContractCategory, FuturesAccountState, FuturesInstrumentMetadata
from triggertrade.persistence import FuturesExecutionRecord, FuturesExecutionStore, FuturesPositionStore, OperatorStateStore
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore


def test_tp_sl_are_mandatory_and_side_validated(tmp_path):
    manager = _manager(tmp_path)
    missing = manager.evaluate(intent=_intent(PositionAction.OPEN_LONG, with_exits=False), instrument=_instrument(), account=_account(), cost=_cost(), funding=_funding())
    assert missing.approved is False
    assert "FRSK-012" in missing.blocking_rule_ids

    tp, sl = _exits(PositionAction.OPEN_SHORT)
    invalid = replace(tp, target_price=Decimal("101"))
    with pytest.raises(ExecutionError, match="side/price"):
        _service(tmp_path).open_position(
            intent=_intent(PositionAction.OPEN_SHORT, tp=invalid, sl=sl),
            risk_decision=_approved_risk("short-intent"),
            take_profit=invalid,
            stop_loss=sl,
        )


def test_tp_sl_boundary_semantics_for_long_and_short():
    long_position = _position_record(PositionState.LONG, tp="101", sl="99")
    short_position = _position_record(PositionState.SHORT, tp="99", sl="101")

    assert should_trigger_protective_exit(position=long_position, mark_price=Decimal("100")) is None
    assert should_trigger_protective_exit(position=long_position, mark_price=Decimal("101")) is CloseReason.TAKE_PROFIT
    assert should_trigger_protective_exit(position=long_position, mark_price=Decimal("98.9")) is CloseReason.STOP_LOSS
    assert should_trigger_protective_exit(position=short_position, mark_price=Decimal("99")) is CloseReason.TAKE_PROFIT
    assert should_trigger_protective_exit(position=short_position, mark_price=Decimal("101")) is CloseReason.STOP_LOSS
    assert should_trigger_protective_exit(position=short_position, mark_price=Decimal("100")) is None


def test_risk_reward_decimal_boundaries():
    tp, sl = _exits(PositionAction.OPEN_LONG, entry=Decimal("100"), tp_pct=Decimal("0.015"), sl_pct=Decimal("0.01"))
    exact = evaluate_risk_reward(action=PositionAction.OPEN_LONG, entry_price=Decimal("100"), take_profit=tp, stop_loss=sl, minimum_ratio=Decimal("1.5"))
    below = evaluate_risk_reward(action=PositionAction.OPEN_LONG, entry_price=Decimal("100"), take_profit=replace(tp, target_price=Decimal("101.4")), stop_loss=sl, minimum_ratio=Decimal("1.5"))
    zero_risk = evaluate_risk_reward(action=PositionAction.OPEN_LONG, entry_price=Decimal("100"), take_profit=tp, stop_loss=replace(sl, stop_price=Decimal("100")), minimum_ratio=Decimal("1"))

    assert exact.approved is True
    assert exact.ratio == Decimal("1.5")
    assert below.approved is False
    assert zero_risk.approved is False


def test_position_sizing_floors_to_step_and_rejects_minimum():
    plan = calculate_position_size(account=_account(available_margin=Decimal("100")), instrument=_instrument(), entry_price=Decimal("10000"), leverage=Decimal("1"), config=PositionRiskConfig(max_position_notional=Decimal("10")))
    assert plan.quantity == Decimal("0.001")
    assert plan.notional == Decimal("10.000")
    with pytest.raises(ExecutionError, match="invalid exchange quantity"):
        calculate_position_size(account=_account(available_margin=Decimal("1")), instrument=_instrument(), entry_price=Decimal("10000"), leverage=Decimal("1"), config=PositionRiskConfig(max_position_notional=Decimal("1")))


def test_open_long_and_open_short_persist_position_and_accounting(tmp_path):
    long_service = _service(tmp_path, adapter=FilledAdapter(action=PositionAction.OPEN_LONG))
    long_result = _open(long_service, PositionAction.OPEN_LONG, "long-intent")
    assert long_result.position is not None
    assert long_result.position.side == "LONG"
    assert long_result.position.tp_price == "101.0"
    assert long_result.position.rule_snapshot["minimum_risk_reward"] == "1.5"
    assert FuturesPositionStore(tmp_path / "runtime.sqlite3").open_position_for_symbol("BTCUSDT") is not None

    short_service = _service(tmp_path, db_name="short.sqlite3", adapter=FilledAdapter(action=PositionAction.OPEN_SHORT), account=_account(symbol="ETHUSDT"))
    short_result = _open(short_service, PositionAction.OPEN_SHORT, "short-intent", symbol="ETHUSDT")
    assert short_result.position is not None
    assert short_result.position.side == "SHORT"
    assert short_result.position.tp_price == "99.0"


def test_cancelled_open_reconciliation_does_not_leave_phantom_position(tmp_path):
    db = tmp_path / "cancelled-open.sqlite3"
    service = _service(tmp_path, db=db, adapter=ScriptedLifecycleAdapter(default_open_status="Cancelled"))

    opened = _open(service, PositionAction.OPEN_LONG, "cancelled-open")
    recovered = service.reconcile_position(opened.position.position_id)

    assert opened.position.status == PositionStatus.CLOSED.value
    assert recovered.status == PositionStatus.CLOSED.value
    assert FuturesPositionStore(db).open_position_for_symbol("BTCUSDT") is None


def test_partial_open_uses_executed_quantity_for_reduce_only_close(tmp_path):
    db = tmp_path / "partial-open.sqlite3"
    adapter = PartialThenCloseAdapter()
    service = _service(tmp_path, db=db, adapter=adapter)

    opened = _open(service, PositionAction.OPEN_LONG, "partial-open", qty=Decimal("0.002"))
    closed = service.close_position(position_id=opened.position.position_id, close_reason=CloseReason.MANUAL, price=Decimal("101"))

    assert opened.position.status == PositionStatus.OPEN.value
    assert opened.position.current_qty == "0.001"
    assert opened.position.position_value == "0.100"
    assert adapter.created[-1]["action"] is PositionAction.CLOSE_LONG
    assert adapter.created[-1]["quantity"] == Decimal("0.001")
    assert closed.closed_trade is not None


def test_duplicate_same_symbol_and_direct_flip_rejected(tmp_path):
    service = _service(tmp_path, adapter=FilledAdapter(action=PositionAction.OPEN_LONG))
    _open(service, PositionAction.OPEN_LONG, "first")
    with pytest.raises(ExecutionError, match="one net"):
        _open(service, PositionAction.OPEN_LONG, "duplicate")

    flip = FuturesRiskManager(config=FuturesExecutionConfig(), store=FuturesExecutionStore(tmp_path / "other.sqlite3")).evaluate(
        intent=_intent(PositionAction.OPEN_SHORT, intent_id="flip", current=PositionState.LONG),
        instrument=_instrument(),
        account=_account(position_size=Decimal("0.001")),
        cost=_cost(),
        funding=_funding(),
    )
    assert "FRSK-005" in flip.blocking_rule_ids


def test_pause_blocks_entries_but_allows_manual_close(tmp_path):
    db = tmp_path / "runtime.sqlite3"
    operator = OperatorStateStore(db)
    operator.pause(source="unit")
    blocked = _service(tmp_path, db=db, operator=operator, adapter=FilledAdapter(action=PositionAction.OPEN_LONG))
    with pytest.raises(ExecutionError, match="operator pause"):
        _open(blocked, PositionAction.OPEN_LONG, "paused-open")

    operator.resume(source="unit")
    service = _service(tmp_path, db=db, operator=operator, adapter=FilledThenCloseAdapter())
    opened = _open(service, PositionAction.OPEN_LONG, "closeable")
    operator.pause(source="unit")
    closed = service.close_position(position_id=opened.position.position_id, close_reason=CloseReason.MANUAL, price=Decimal("101"))
    assert closed.closed_trade is not None
    assert closed.closed_trade.close_reason == "MANUAL"


def test_multi_symbol_close_one_and_close_all(tmp_path):
    db = tmp_path / "multi.sqlite3"
    for symbol, state, intent in (("BTCUSDT", PositionAction.OPEN_LONG, "btc"), ("ETHUSDT", PositionAction.OPEN_SHORT, "eth"), ("SOLUSDT", PositionAction.OPEN_LONG, "sol")):
        service = _service(tmp_path, db=db, adapter=FilledAdapter(action=state, symbol=symbol), account=_account(symbol=symbol), config=FuturesExecutionConfig(symbol=symbol))
        _open(service, state, intent, symbol=symbol)

    eth_service = _service(tmp_path, db=db, adapter=FilledThenCloseAdapter(symbol="ETHUSDT"), account=_account(symbol="ETHUSDT"), config=FuturesExecutionConfig(symbol="ETHUSDT"))
    eth = FuturesPositionStore(db).open_position_for_symbol("ETHUSDT")
    eth_service.close_position(position_id=eth.position_id, close_reason=CloseReason.MANUAL, price=Decimal("99"))

    store = FuturesPositionStore(db)
    assert store.open_position_for_symbol("BTCUSDT") is not None
    assert store.open_position_for_symbol("SOLUSDT") is not None
    assert store.open_position_for_symbol("ETHUSDT") is None

    closer = _service(tmp_path, db=db, adapter=FilledThenCloseAdapter(symbol="BTCUSDT"), account=_account(symbol="BTCUSDT"), config=FuturesExecutionConfig(symbol="BTCUSDT"))
    result = closer.close_all_positions()
    assert not result.failures
    assert store.open_position_count() == 0


def test_restart_recovers_open_and_unresolved_without_duplicate(tmp_path):
    db = tmp_path / "restart.sqlite3"
    adapter = FilledAdapter(action=PositionAction.OPEN_LONG)
    first = _service(tmp_path, db=db, adapter=adapter)
    opened = _open(first, PositionAction.OPEN_LONG, "restart")

    restarted = _service(tmp_path, db=db, adapter=adapter)
    recovered = restarted.recover_after_restart()

    assert recovered[0].position_id == opened.position.position_id
    assert adapter.create_calls == 1


def test_unknown_open_recovery_marks_position_open_and_accounting_once(tmp_path):
    db = tmp_path / "unknown-open.sqlite3"
    position = replace(
        _position_record(PositionState.LONG),
        status=PositionStatus.UNKNOWN.value,
        open_intent_id="recovered-open",
        open_execution_id="ttf-recovered-open",
    )
    FuturesPositionStore(db).save_open_position(position)
    FuturesExecutionStore(db).reserve(
        _execution_record(
            intent_id="recovered-open",
            risk_decision_id=position.open_risk_decision_id,
            client_order_id="ttf-recovered-open",
            status=OrderStatus.UNKNOWN,
        )
    )
    service = _service(tmp_path, db=db, adapter=ScriptedLifecycleAdapter(status_by_client_order_id={"ttf-recovered-open": "Filled"}))

    recovered = service.reconcile_position(position.position_id)
    service.reconcile_position(position.position_id)

    fills = FuturesAccountingStore(db).list_fills(position.trade_id)
    assert recovered.status == PositionStatus.OPEN.value
    assert len(fills) == 1


def test_uncertain_close_reconciliation_finalizes_once(tmp_path):
    db = tmp_path / "unknown-close.sqlite3"
    adapter = ScriptedLifecycleAdapter(default_open_status="Filled", default_close_status="New")
    service = _service(tmp_path, db=db, adapter=adapter)
    opened = _open(service, PositionAction.OPEN_LONG, "uncertain-close")

    close = service.close_position(position_id=opened.position.position_id, close_reason=CloseReason.MANUAL, price=Decimal("101"))
    assert close.closed_trade is None
    assert close.position.status == PositionStatus.CLOSING.value

    adapter.default_close_status = "Filled"
    restarted = _service(tmp_path, db=db, adapter=adapter)
    reconciled = restarted.reconcile_position(opened.position.position_id)
    restarted.reconcile_position(opened.position.position_id)

    closed = FuturesPositionStore(db).get_closed_position(opened.position.position_id)
    assert reconciled.status == PositionStatus.CLOSED.value
    assert closed is not None
    assert closed.close_reason == CloseReason.MANUAL.value
    assert len(FuturesAccountingStore(db).list_closed_trades(limit=10)) == 1


def test_manual_close_feeds_futures_accounting_and_pnl_percent(tmp_path):
    db = tmp_path / "accounting.sqlite3"
    service = _service(tmp_path, db=db, adapter=FilledThenCloseAdapter())
    opened = _open(service, PositionAction.OPEN_LONG, "acct")
    assert unrealized_pnl_pct(position=opened.position, mark_price=Decimal("101")) == Decimal("1.00")

    closed = service.close_position(position_id=opened.position.position_id, close_reason=CloseReason.MANUAL, price=Decimal("101"))
    accounting = FuturesAccountingStore(db).list_closed_trades(limit=1)

    assert closed.closed_trade is not None
    assert closed.closed_trade.realized_pnl_pct == "1.00"
    assert accounting[0]["trade_id"] == opened.position.trade_id
    assert accounting[0]["net_pnl"] == Decimal("0.001").__str__()


def _execution_record(*, intent_id, risk_decision_id, client_order_id, status):
    return FuturesExecutionRecord(
        intent_id=intent_id,
        risk_decision_id=risk_decision_id,
        client_order_id=client_order_id,
        exchange_order_id=None,
        symbol="BTCUSDT",
        category="linear",
        position_action=PositionAction.OPEN_LONG.value,
        exchange_side="Buy",
        order_type="Limit",
        requested_qty="0.001",
        requested_price="100",
        leverage="1",
        status=status,
        created_at="2026-09-06T00:00:00+00:00",
        updated_at="2026-09-06T00:00:00+00:00",
        margin_mode="ISOLATED",
        position_mode="ONE_WAY",
        lane="ACTIVE",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    )


def _open(service, action, intent_id, *, symbol="BTCUSDT", qty=Decimal("0.001")):
    intent = _intent(action, intent_id=intent_id, symbol=symbol, qty=qty)
    risk = _approved_risk(intent.intent_id, qty=intent.quantity, notional=intent.quantity * intent.price)
    return service.open_position(intent=intent, risk_decision=risk, take_profit=intent.take_profit, stop_loss=intent.stop_loss)


def _service(tmp_path, *, db=None, db_name="runtime.sqlite3", adapter=None, account=None, operator=None, config=None):
    path = db or (tmp_path / db_name)
    operator_store = operator or OperatorStateStore(path)
    return FuturesPositionLifecycleService(
        execution_config=config or FuturesExecutionConfig(symbol=(account.symbol if account else "BTCUSDT")),
        risk_config=PositionRiskConfig(max_open_positions=3, max_total_position_notional=Decimal("50")),
        execution_store=FuturesExecutionStore(path),
        position_store=FuturesPositionStore(path),
        accounting_store=FuturesAccountingStore(path),
        adapter=adapter or FilledThenCloseAdapter(),
        instrument=_instrument(symbol=(account.symbol if account else "BTCUSDT")),
        account=account or _account(),
        operator_trading_state=lambda: operator_store.get_trading_state().state.value,
    )


def _intent(action, *, intent_id="intent", symbol="BTCUSDT", current=PositionState.FLAT, with_exits=True, tp=None, sl=None, qty=Decimal("0.001")):
    if with_exits and tp is None and sl is None:
        tp, sl = _exits(action)
    return FuturesTradeIntent(
        intent_id=intent_id,
        symbol=symbol,
        category=ContractCategory.LINEAR,
        action=action,
        order_type=OrderType.LIMIT,
        quantity=qty,
        price=Decimal("100"),
        current_position_state=current,
        configured_leverage=Decimal("1"),
        expected_gross_price_move=Decimal("1"),
        lane="ACTIVE",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
        strategy_rule_id="manual-lifecycle-fixture",
        strategy_rule_version="0.1.0",
        take_profit=tp,
        stop_loss=sl,
        minimum_risk_reward=Decimal("1.5"),
    )


def _exits(action, *, entry=Decimal("100"), tp_pct=Decimal("0.01"), sl_pct=Decimal("0.005")):
    return build_fixed_protective_exit_plan(
        action=action,
        entry_price=entry,
        take_profit_pct=tp_pct,
        stop_loss_pct=sl_pct,
        price_tick=Decimal("0.1"),
        calculated_at="2026-09-06T00:00:00+00:00",
    )


def _approved_risk(intent_id, *, qty=Decimal("0.001"), notional=Decimal("0.100")):
    return FuturesRiskDecision(
        risk_decision_id=f"risk-{intent_id}",
        intent_id=intent_id,
        approved=True,
        checked_rule_ids=FUTURES_RISK_RULE_IDS,
        approved_quantity=qty,
        approved_notional=notional,
        position_state_after=PositionState.LONG,
        net_edge=estimate_net_edge(expected_gross_price_move=Decimal("1"), minimum_net_edge=Decimal("0.01"), cost=_cost(), funding=_funding()),
        lane="ACTIVE",
    )


def _manager(tmp_path):
    return FuturesRiskManager(config=FuturesExecutionConfig(), store=FuturesExecutionStore(tmp_path / "risk.sqlite3"), minimum_net_edge=Decimal("0.01"))


def _instrument(*, symbol="BTCUSDT"):
    return FuturesInstrumentMetadata(
        symbol=symbol,
        category=ContractCategory.LINEAR,
        contract_type="LinearPerpetual",
        settlement_asset="USDT",
        quantity_step=Decimal("0.001"),
        price_tick=Decimal("0.1"),
        minimum_order_quantity=Decimal("0.001"),
        minimum_notional=Decimal("0.01"),
        max_leverage=Decimal("100"),
    )


def _account(*, symbol="BTCUSDT", available_margin=Decimal("100"), position_size=Decimal("0")):
    return FuturesAccountState(
        symbol=symbol,
        category=ContractCategory.LINEAR,
        settlement_asset="USDT",
        available_margin=available_margin,
        equity=available_margin,
        wallet_balance=available_margin,
        configured_leverage=Decimal("1"),
        position_size=position_size,
        mark_price=Decimal("100"),
    )


def _cost():
    return estimate_costs(notional=Decimal("0.1"), maker_fee_rate=Decimal("0"), taker_fee_rate=Decimal("0"))


def _funding():
    return FundingEstimate(Decimal("0"), None, Decimal("0"), Decimal("0"))


def _position_record(side, *, tp="101", sl="99"):
    tp_plan, sl_plan = _exits(PositionAction.OPEN_LONG if side is PositionState.LONG else PositionAction.OPEN_SHORT)
    record = _intent(PositionAction.OPEN_LONG if side is PositionState.LONG else PositionAction.OPEN_SHORT, intent_id=f"{side.value}-pos")
    pos_id = futures_position_id(record.intent_id)
    from triggertrade.persistence import FuturesPositionRecord

    return FuturesPositionRecord(
        position_id=pos_id,
        trade_id=f"trade-{pos_id}",
        symbol="BTCUSDT",
        side=side.value,
        status=PositionStatus.OPEN.value,
        opened_at="2026-09-06T00:00:00+00:00",
        closed_at=None,
        entry_price="100",
        current_qty="0.001",
        initial_qty="0.001",
        leverage="1",
        position_value="0.100",
        tp_price=tp,
        tp_pct=str(tp_plan.target_pct),
        sl_price=sl,
        sl_pct=str(sl_plan.stop_pct),
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
        strategy_rule_id="manual-lifecycle-fixture",
        strategy_rule_version="0.1.0",
        risk_rule_version="futures-position-risk-v1",
        protective_exit_version="protective-exit-v1",
        evidence_source="ACTIVE",
        open_intent_id=record.intent_id,
        open_risk_decision_id="risk",
        open_execution_id="exec",
        close_intent_id=None,
        close_risk_decision_id=None,
        close_execution_id=None,
        close_reason=None,
        rule_snapshot={},
        updated_at="2026-09-06T00:00:00+00:00",
    )


class FilledAdapter:
    uses_private_exchange_orders = True
    category = "linear"

    def __init__(self, *, action, symbol="BTCUSDT"):
        self.action = action
        self.symbol = symbol
        self.create_calls = 0
        self.actions_by_client_order_id = {}
        self.created = []

    def create_limit_order(self, **kwargs):
        self.create_calls += 1
        self.created.append(kwargs)
        self.actions_by_client_order_id[kwargs["client_order_id"]] = kwargs["action"]
        return type("Response", (), {"result": {"orderId": f"ex-{kwargs['client_order_id']}"}})()

    def reconcile_order(self, **kwargs):
        return {"orderId": f"ex-{kwargs['client_order_id']}", "orderStatus": "Filled"}

    def map_order_status(self, raw_status):
        return OrderStatus.FILLED

    def fetch_executions(self, *, symbol, client_order_id):
        action = self.action.value
        side = "Buy" if action in {"OPEN_LONG", "CLOSE_SHORT"} else "Sell"
        return (
            {
                "execId": client_order_id,
                "execQty": "0.001",
                "execPrice": "100",
                "execFee": "0",
                "execTime": "1788613800000",
                "feeCurrency": "USDT",
                "side": side,
            },
        )


class FilledThenCloseAdapter(FilledAdapter):
    def __init__(self, *, symbol="BTCUSDT"):
        super().__init__(action=PositionAction.OPEN_LONG, symbol=symbol)

    def fetch_executions(self, *, symbol, client_order_id):
        raw_action = self.actions_by_client_order_id.get(client_order_id, PositionAction.OPEN_LONG)
        action = raw_action.value
        price = "101" if action.startswith("CLOSE") else "100"
        return (
            {
                "execId": client_order_id,
                "execQty": "0.001",
                "execPrice": price,
                "execFee": "0",
                "execTime": "1788617400000" if action.startswith("CLOSE") else "1788613800000",
                "feeCurrency": "USDT",
            },
        )


class PartialThenCloseAdapter(FilledThenCloseAdapter):
    def reconcile_order(self, **kwargs):
        raw_action = self.actions_by_client_order_id.get(kwargs["client_order_id"], PositionAction.OPEN_LONG)
        status = "Filled" if raw_action in {PositionAction.CLOSE_LONG, PositionAction.CLOSE_SHORT} else "PartiallyFilled"
        return {"orderId": f"ex-{kwargs['client_order_id']}", "orderStatus": status}

    def map_order_status(self, raw_status):
        if raw_status == "PartiallyFilled":
            return OrderStatus.PARTIALLY_FILLED
        return super().map_order_status(raw_status)

    def fetch_executions(self, *, symbol, client_order_id):
        raw_action = self.actions_by_client_order_id.get(client_order_id, PositionAction.OPEN_LONG)
        action = raw_action.value
        price = "101" if action.startswith("CLOSE") else "100"
        return (
            {
                "execId": client_order_id,
                "execQty": "0.001",
                "execPrice": price,
                "execFee": "0",
                "execTime": "1788617400000" if action.startswith("CLOSE") else "1788613800000",
                "feeCurrency": "USDT",
            },
        )


class ScriptedLifecycleAdapter(FilledThenCloseAdapter):
    def __init__(self, *, status_by_client_order_id=None, default_open_status="Filled", default_close_status="Filled"):
        super().__init__()
        self.status_by_client_order_id = dict(status_by_client_order_id or {})
        self.default_open_status = default_open_status
        self.default_close_status = default_close_status

    def reconcile_order(self, **kwargs):
        client_order_id = kwargs["client_order_id"]
        action = self.actions_by_client_order_id.get(client_order_id)
        if action is None:
            status = self.status_by_client_order_id.get(client_order_id, self.default_open_status)
        elif action in {PositionAction.CLOSE_LONG, PositionAction.CLOSE_SHORT}:
            status = self.status_by_client_order_id.get(client_order_id, self.default_close_status)
        else:
            status = self.status_by_client_order_id.get(client_order_id, self.default_open_status)
        return {"orderId": f"ex-{client_order_id}", "orderStatus": status}

    def map_order_status(self, raw_status):
        if raw_status == "Filled":
            return OrderStatus.FILLED
        if raw_status == "Cancelled":
            return OrderStatus.CANCELLED
        if raw_status == "PartiallyFilled":
            return OrderStatus.PARTIALLY_FILLED
        if raw_status == "Rejected":
            return OrderStatus.REJECTED
        return OrderStatus.SUBMITTED

