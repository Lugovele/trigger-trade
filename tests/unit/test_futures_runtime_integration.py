from __future__ import annotations

from datetime import UTC, datetime, timedelta
from dataclasses import replace
from decimal import Decimal

import pytest

from triggertrade.config import ExecutionVenue, load_config
from triggertrade.execution import OrderStatus, OrderType
from triggertrade.execution.futures import FuturesTradeIntent, PositionAction, PositionState
from triggertrade.exchanges import BybitResponse
from triggertrade.market_data import ContractCategory, FuturesAccountState, FuturesInstrumentMetadata
from triggertrade.market_data import FuturesMarketEvent, MarketRegimeContext, MarketRegimeLabel, RegimeCapability
from triggertrade.persistence import (
    FuturesExecutionStore,
    FuturesExecutionRecord,
    FuturesPositionRecord,
    FuturesPositionStore,
    OperatorStateStore,
    RuntimeStore,
    TraceStore,
    TriggerSetStore,
    bootstrap_current_trigger_sets,
    current_futures_active_trigger_set,
)
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.services.futures_runtime import FuturesDualLaneRuntime, _is_futures_set
from triggertrade.services.runtime import build_runtime_from_env
from triggertrade.execution.position_lifecycle import PositionStatus, futures_position_id
from triggertrade.strategies import IntegrationDirectionalFuturesStrategy
from triggertrade.trigger_sets import Lane
from triggertrade.triggers import Signal, SignalType


def test_runtime_uses_one_linear_market_stream_for_active_and_test(tmp_path):
    client = LinearOnlyMarketClient()
    adapter = RecordingFuturesAdapter(order_status="New")

    result = _runtime(tmp_path, client=client, active_adapter=adapter).process_once()

    assert result.candle_id.endswith("2026-09-05T13:09:00+00:00")
    assert client.linear_instrument_calls == 1
    assert client.linear_candle_calls == 1
    assert client.spot_instrument_calls == 0
    assert client.spot_candle_calls == 0
    assert result.active[0].execution_status == "submitted"
    assert result.test[0].execution_status == "test_simulated"


def test_active_lane_creates_futures_trade_intent_and_bybit_demo_record(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    adapter = RecordingFuturesAdapter(order_status="New")

    result = _runtime(tmp_path, path=path, active_adapter=adapter).process_once()

    active = RuntimeStore(path).get_lane_lifecycle(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=result.candle_id,
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    )
    record = FuturesExecutionStore(path).get_by_intent(active.intent_id)
    trace = TraceStore(path).trace_for_intent(active.intent_id)

    assert record.category == "linear"
    assert record.position_action == "OPEN_LONG"
    assert record.lane == "ACTIVE"
    assert record.trigger_set_id == "triggertrade-futures-core"
    assert adapter.create_calls == 1
    assert adapter.created[0]["action"] is PositionAction.OPEN_LONG
    assert trace["strategy"]["side"] == "OPEN_LONG"
    assert trace["risk"]["approved"] == 1


def test_test_lane_simulates_source_aware_closed_trade_without_private_order(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    adapter = RecordingFuturesAdapter(order_status="New")

    _runtime(tmp_path, path=path, active_adapter=adapter).process_once()
    rows = FuturesAccountingStore(path).list_closed_trades(limit=10)

    assert len(rows) == 1
    assert rows[0]["trigger_set_id"] == "triggertrade-futures-candidate"
    assert rows[0]["evidence_source"] == "test_simulation"
    assert rows[0]["simulation_model_version"] == "test-sim-v1"
    assert adapter.create_calls == 1


def test_same_candle_restart_does_not_duplicate_active_or_test(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    adapter = RecordingFuturesAdapter(order_status="New")

    first = _runtime(tmp_path, path=path, active_adapter=adapter).process_once()
    second = _runtime(tmp_path, path=path, active_adapter=adapter).process_once()

    assert second.active[0].skipped_reason == "already_processed"
    assert second.test[0].skipped_reason == "already_processed"
    assert adapter.create_calls == 1
    assert len(FuturesAccountingStore(path).list_closed_trades(limit=10)) == 1
    assert RuntimeStore(path).lane_processed_count(
        lane="TEST",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=first.candle_id,
        trigger_set_id="triggertrade-futures-candidate",
        trigger_set_version="v2-test",
    ) == 1


def test_unresolved_active_execution_reconciles_before_no_signal_decision(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    store = FuturesExecutionStore(path)
    store.reserve(_execution_record(intent_id="old-intent", risk_decision_id="old-risk"))
    adapter = RecordingFuturesAdapter(order_status="Filled")

    result = _runtime(
        tmp_path,
        path=path,
        client=LinearOnlyMarketClient(candles=_no_signal_candles()),
        active_adapter=adapter,
    ).process_once()

    assert result.active[0].signal_type == "NO_SIGNAL"
    assert store.get_by_intent("old-intent").status is OrderStatus.FILLED
    assert adapter.create_calls == 0
    assert adapter.reconcile_calls == 1


def test_accounting_bridge_rejects_mismatched_current_intent_for_recovered_record(tmp_path):
    from triggertrade.services.futures_accounting_bridge import FuturesAccountingBridge

    record = _execution_record(intent_id="old-intent", risk_decision_id="old-risk", status=OrderStatus.FILLED)
    intent = FuturesTradeIntent(
        intent_id="new-intent",
        symbol="BTCUSDT",
        category=ContractCategory.LINEAR,
        action=PositionAction.OPEN_LONG,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.1"),
        price=Decimal("95"),
        current_position_state=PositionState.FLAT,
    )

    with pytest.raises(ValueError, match="mismatch"):
        FuturesAccountingBridge(accounting_store=FuturesAccountingStore(tmp_path / "acct.sqlite3"), adapter=RecordingFuturesAdapter(order_status="Filled")).ingest_execution(
            record=record,
            intent=intent,
        )


def test_accounting_bridge_is_idempotent_when_same_recovered_fill_is_ingested_with_later_intent(tmp_path):
    from triggertrade.services.futures_accounting_bridge import FuturesAccountingBridge

    class FilledExecutionAdapter(RecordingFuturesAdapter):
        def fetch_executions(self, *, symbol, client_order_id):
            return (
                {
                    "execId": "same-fill-1",
                    "execQty": "0.1",
                    "execPrice": "95",
                    "execFee": "0.01",
                    "execTime": "1788613800000",
                    "feeCurrency": "USDT",
                },
            )

    path = tmp_path / "acct.sqlite3"
    bridge = FuturesAccountingBridge(accounting_store=FuturesAccountingStore(path), adapter=FilledExecutionAdapter(order_status="Filled"))
    record = _execution_record(intent_id="same-intent", risk_decision_id="risk-1", status=OrderStatus.FILLED)
    intent = FuturesTradeIntent(
        intent_id="same-intent",
        symbol="BTCUSDT",
        category=ContractCategory.LINEAR,
        action=PositionAction.OPEN_LONG,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.1"),
        price=Decimal("95"),
        current_position_state=PositionState.FLAT,
        regime_state="DOWNTREND",
    )

    bridge.ingest_execution(record=record)
    bridge.ingest_execution(record=record, intent=intent)

    fills = FuturesAccountingStore(path).list_fills("trade-same-intent")
    assert len(fills) == 1
    assert fills[0].regime_label is None
def test_missing_expected_move_blocks_strategy_before_execution(tmp_path):
    adapter = RecordingFuturesAdapter(order_status="New")
    result = _runtime(
        tmp_path,
        active_adapter=adapter,
        demo_expected_gross_move="",
    ).process_once()

    assert result.active[0].skipped_reason == "demo_expected_gross_move_unavailable"
    assert result.test[0].skipped_reason == "demo_expected_gross_move_unavailable"
    assert adapter.create_calls == 0


def test_operator_pause_blocks_active_but_test_lane_continues(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    operator = OperatorStateStore(path)
    operator.pause(changed_at="2026-09-05T13:00:00+00:00", source="unit")
    adapter = RecordingFuturesAdapter(order_status="New")

    result = _runtime(tmp_path, path=path, active_adapter=adapter, operator_store=operator).process_once()

    assert result.active[0].skipped_reason == "active_execution_paused"
    assert result.test[0].execution_status == "test_simulated"
    assert adapter.create_calls == 0
    assert len(FuturesAccountingStore(path).list_closed_trades(limit=10)) == 1


def test_runtime_entrypoint_no_longer_forces_local_paper_and_requires_futures_config(tmp_path):
    env = _env(tmp_path / "runtime.sqlite3") | {
        "BYBIT_API_KEY": "unit-key",
        "BYBIT_API_SECRET": "unit-secret",
    }

    runtime = build_runtime_from_env(env)

    assert isinstance(runtime, FuturesDualLaneRuntime)
    assert runtime._config.execution_venue is ExecutionVenue.BYBIT_DEMO_FUTURES


def test_runtime_refuses_legacy_spot_or_local_paper_config(tmp_path):
    with pytest.raises(Exception, match="LOCAL_PAPER|linear|futures"):
        _runtime(tmp_path, market="spot").process_once()


def test_futures_strategy_rejects_spot_or_unscoped_signal_provenance():
    trigger_set = current_futures_active_trigger_set(created_at="2026-09-05T00:00:00+00:00")
    event = _event()
    regime = _regime(event)
    strategy = IntegrationDirectionalFuturesStrategy()

    spot_signal = _signal(version="0.1.0", event=event, trigger_set=trigger_set)
    unscoped_signal = _signal(version="0.2.0", event=event, trigger_set=trigger_set, lane=None)
    good_signal = _signal(version="0.2.0", event=event, trigger_set=trigger_set)

    assert strategy.decide(
        trigger_set=trigger_set,
        lane=Lane.ACTIVE,
        event=event,
        primary_signal=spot_signal,
        volume_signal=None,
        regime_context=regime,
        position_state=PositionState.FLAT,
        quantity=Decimal("0.1"),
        limit_price=Decimal("95"),
        leverage=Decimal("1"),
        expected_gross_move=Decimal("1"),
        created_at=datetime(2026, 9, 5, 13, 10, tzinfo=UTC),
    ).reason == "primary_trigger_provenance_mismatch"
    assert strategy.decide(
        trigger_set=trigger_set,
        lane=Lane.ACTIVE,
        event=event,
        primary_signal=unscoped_signal,
        volume_signal=None,
        regime_context=regime,
        position_state=PositionState.FLAT,
        quantity=Decimal("0.1"),
        limit_price=Decimal("95"),
        leverage=Decimal("1"),
        expected_gross_move=Decimal("1"),
        created_at=datetime(2026, 9, 5, 13, 10, tzinfo=UTC),
    ).reason == "primary_trigger_provenance_mismatch"
    assert strategy.decide(
        trigger_set=trigger_set,
        lane=Lane.ACTIVE,
        event=event,
        primary_signal=good_signal,
        volume_signal=None,
        regime_context=regime,
        position_state=PositionState.FLAT,
        quantity=Decimal("0.1"),
        limit_price=Decimal("95"),
        leverage=Decimal("1"),
        expected_gross_move=Decimal("1"),
        created_at=datetime(2026, 9, 5, 13, 10, tzinfo=UTC),
    ).intent.action is PositionAction.OPEN_LONG


def test_futures_strategy_rejects_mismatched_regime_provenance():
    trigger_set = current_futures_active_trigger_set(created_at="2026-09-05T00:00:00+00:00")
    event = _event()
    signal = _signal(version="0.2.0", event=event, trigger_set=trigger_set)
    strategy = IntegrationDirectionalFuturesStrategy()

    for bad_regime in (
        replace(_regime(event), version="0.2.0"),
        replace(_regime(event), symbol="ETHUSDT"),
        replace(_regime(event), timeframe="5m"),
        replace(_regime(event), observed_at="2026-09-05T13:09:00+00:00"),
        replace(_regime(event), input_snapshot={"category": "spot"}),
        replace(_regime(event), label=MarketRegimeLabel.INSUFFICIENT_DATA),
    ):
        assert strategy.decide(
            trigger_set=trigger_set,
            lane=Lane.ACTIVE,
            event=event,
            primary_signal=signal,
            volume_signal=None,
            regime_context=bad_regime,
            position_state=PositionState.FLAT,
            quantity=Decimal("0.1"),
            limit_price=Decimal("95"),
            leverage=Decimal("1"),
            expected_gross_move=Decimal("1"),
            created_at=datetime(2026, 9, 5, 13, 10, tzinfo=UTC),
        ).reason == "regime_provenance_mismatch"


def test_executable_futures_set_requires_exact_mandatory_rule_membership():
    trigger_set = current_futures_active_trigger_set(created_at="2026-09-05T00:00:00+00:00")

    assert _is_futures_set(trigger_set) is True
    missing_trigger = replace(
        trigger_set,
        rule_versions=(("STR-FUT-001", "0.1.0"), ("RSK-FUTURES-001", "0.1.0"), ("CTX-REGIME", "0.1.0")),
    )
    wrong_volume = replace(
        trigger_set,
        rule_versions=trigger_set.rule_versions + (("TRG-002", "0.1.0"),),
    )

    assert _is_futures_set(missing_trigger) is False
    assert _is_futures_set(wrong_volume) is False


def _runtime(
    tmp_path,
    *,
    path=None,
    client=None,
    active_adapter=None,
    operator_store=None,
    position_store=None,
    account_provider=None,
    demo_expected_gross_move="1",
    market="linear",
):
    db_path = path or (tmp_path / "runtime.sqlite3")
    trigger_sets = TriggerSetStore(db_path)
    bootstrap_current_trigger_sets(trigger_sets)
    config = load_config(_env(db_path, demo_expected_gross_move=demo_expected_gross_move, market=market))
    instrument = _instrument()
    return FuturesDualLaneRuntime(
        config=config,
        market_client=client or LinearOnlyMarketClient(),
        futures_execution_store=FuturesExecutionStore(db_path),
        accounting_store=FuturesAccountingStore(db_path),
        trace_store=TraceStore(db_path),
        runtime_store=RuntimeStore(db_path),
        trigger_set_store=trigger_sets,
        operator_state_store=operator_store or OperatorStateStore(db_path),
        position_store=position_store,
        active_adapter=active_adapter or RecordingFuturesAdapter(order_status="New"),
        account_provider=account_provider or (lambda _: _account(instrument)),
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
        logger=lambda message: None,
    )


def _env(db_path, *, demo_expected_gross_move="1", market="linear"):
    env = {
        "TRIGGERTRADE_MARKET": market,
        "TRIGGERTRADE_CATEGORY": market,
        "TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO_FUTURES.value,
        "TRIGGERTRADE_ACTIVE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO_FUTURES.value,
        "TRIGGERTRADE_TEST_EXECUTION_VENUE": ExecutionVenue.LOCAL_TEST_SIMULATION.value,
        "TRIGGERTRADE_WATCHLIST": "BTCUSDT",
        "TRIGGERTRADE_RUNTIME_SYMBOL": "BTCUSDT",
        "TRIGGERTRADE_CANDLE_INTERVAL": "1",
        "TRIGGERTRADE_POLL_INTERVAL_SECONDS": "1",
        "TRIGGERTRADE_STALE_AFTER_SECONDS": "120",
        "TRIGGERTRADE_RUNTIME_DB_PATH": str(db_path),
        "TRIGGERTRADE_MAX_FUTURES_POSITION_NOTIONAL": "20",
        "TRIGGERTRADE_MINIMUM_NET_EDGE": "0.01",
    }
    if demo_expected_gross_move != "":
        env["TRIGGERTRADE_DEMO_EXPECTED_GROSS_MOVE"] = demo_expected_gross_move
    return env


class LinearOnlyMarketClient:
    def __init__(self, candles=None):
        self._candles = candles or _linear_candles()
        self.linear_instrument_calls = 0
        self.linear_candle_calls = 0
        self.spot_instrument_calls = 0
        self.spot_candle_calls = 0

    def linear_instrument_metadata(self, symbol):
        self.linear_instrument_calls += 1
        return BybitResponse(0, "OK", _instrument_payload())

    def linear_recent_candles(self, symbol, interval, limit):
        self.linear_candle_calls += 1
        return BybitResponse(0, "OK", {"list": list(reversed(self._candles))})

    def instrument_metadata(self, symbol):
        self.spot_instrument_calls += 1
        raise AssertionError("spot instrument API must not be used by futures runtime")

    def recent_candles(self, symbol, interval, limit):
        self.spot_candle_calls += 1
        raise AssertionError("spot candle API must not be used by futures runtime")


class RecordingFuturesAdapter:
    uses_private_exchange_orders = True
    category = "linear"

    def __init__(self, *, order_status):
        self.order_status = order_status
        self.create_calls = 0
        self.reconcile_calls = 0
        self.created = []

    def create_limit_order(self, **kwargs):
        self.create_calls += 1
        self.created.append(kwargs)
        return BybitResponse(0, "OK", {"orderId": "exchange-1"})

    def reconcile_order(self, **kwargs):
        self.reconcile_calls += 1
        return {"orderId": "exchange-1", "orderStatus": self.order_status}

    def map_order_status(self, raw_status):
        if raw_status == "Filled":
            return OrderStatus.FILLED
        if raw_status == "Cancelled":
            return OrderStatus.CANCELLED
        return OrderStatus.SUBMITTED


def _linear_candles():
    start = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
    rows = []
    for index in range(70):
        open_time = start + timedelta(minutes=index)
        close = Decimal("112") - Decimal(index) * Decimal("0.2")
        if index == 69:
            close = Decimal("95")
        volume = Decimal("1")
        if index == 69:
            volume = Decimal("2")
        rows.append(
            [
                str(int(open_time.timestamp() * 1000)),
                str(close),
                str(close),
                str(close),
                str(close),
                str(volume),
                str(close * volume),
            ]
        )
    return rows


def _no_signal_candles():
    rows = _linear_candles()
    rows[-1][1] = "98"
    rows[-1][2] = "98"
    rows[-1][3] = "98"
    rows[-1][4] = "98"
    rows[-1][5] = "1"
    rows[-1][6] = "98"
    return rows


def _execution_record(*, intent_id, risk_decision_id, status=OrderStatus.SUBMITTED):
    return FuturesExecutionRecord(
        intent_id=intent_id,
        risk_decision_id=risk_decision_id,
        client_order_id=f"ttf-{intent_id}",
        exchange_order_id=None,
        symbol="BTCUSDT",
        category="linear",
        position_action="OPEN_LONG",
        exchange_side="Buy",
        order_type="Limit",
        requested_qty="0.1",
        requested_price="95",
        leverage="1",
        status=status,
        created_at="2026-09-05T13:00:00+00:00",
        updated_at="2026-09-05T13:00:00+00:00",
        margin_mode="ISOLATED",
        position_mode="ONE_WAY",
        expected_net_edge="1",
        lane="ACTIVE",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    )


def _instrument_payload():
    return {
        "list": [
            {
                "symbol": "BTCUSDT",
                "contractType": "LinearPerpetual",
                "quoteCoin": "USDT",
                "settleCoin": "USDT",
                "priceFilter": {"tickSize": "0.1"},
                "lotSizeFilter": {"qtyStep": "0.001", "minOrderQty": "0.001", "minNotionalValue": "5"},
                "leverageFilter": {"minLeverage": "1", "maxLeverage": "100", "leverageStep": "0.01"},
            }
        ]
    }


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


def _account(instrument, *, position_size=Decimal("0"), mark_price=None):
    return FuturesAccountState(
        symbol=instrument.symbol,
        category=ContractCategory.LINEAR,
        settlement_asset=instrument.settlement_asset,
        available_margin=Decimal("100"),
        equity=Decimal("100"),
        wallet_balance=Decimal("100"),
        configured_leverage=Decimal("1"),
        margin_mode="ISOLATED",
        position_mode="ONE_WAY",
        position_size=position_size,
        mark_price=mark_price,
    )


def _position_record(*, open_intent_id):
    position_id = futures_position_id(open_intent_id)
    return FuturesPositionRecord(
        position_id=position_id,
        trade_id=f"trade-{position_id}",
        symbol="BTCUSDT",
        side="LONG",
        status=PositionStatus.OPEN.value,
        opened_at="2026-09-05T13:00:00+00:00",
        closed_at=None,
        entry_price="100",
        current_qty="0.1",
        initial_qty="0.1",
        leverage="1",
        position_value="10",
        tp_price="101",
        tp_pct="0.01",
        sl_price="99",
        sl_pct="0.01",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
        strategy_rule_id="STR-FUT-001",
        strategy_rule_version="0.1.0",
        risk_rule_version="futures-position-risk-v1",
        protective_exit_version="protective-exit-v1",
        evidence_source="ACTIVE",
        open_intent_id=open_intent_id,
        open_risk_decision_id="risk-open",
        open_execution_id=f"ttf-{open_intent_id}",
        close_intent_id=None,
        close_risk_decision_id=None,
        close_execution_id=None,
        close_reason=None,
        rule_snapshot={"take_profit_pct": "0.01", "stop_loss_pct": "0.01"},
        updated_at="2026-09-05T13:00:00+00:00",
    )


def _event():
    open_time = datetime(2026, 9, 5, 13, 9, tzinfo=UTC)
    return FuturesMarketEvent(
        symbol="BTCUSDT",
        category="linear",
        timeframe="1m",
        candle_id="BTCUSDT:1m:2026-09-05T13:09:00+00:00",
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=Decimal("98"),
        high=Decimal("98"),
        low=Decimal("95"),
        close=Decimal("95"),
        previous_close=Decimal("98"),
        volume=Decimal("2"),
        turnover=Decimal("190"),
        completed=True,
        observed_at=open_time + timedelta(minutes=1),
        source="bybit_demo_linear_kline",
    )


def _regime(event):
    return MarketRegimeContext(
        context_id="regime-unit",
        symbol=event.symbol,
        timeframe=event.timeframe,
        observed_at=event.close_time.isoformat(),
        capability=RegimeCapability.AVAILABLE,
        label=MarketRegimeLabel.DOWNTREND,
        input_snapshot={"category": "linear"},
    )


def _signal(*, version, event, trigger_set, lane="ACTIVE"):
    return Signal(
        signal_id=f"signal-{version}-{lane}",
        trigger_rule_id="TRG-001",
        trigger_rule_version=version,
        symbol=event.symbol,
        observed_at=event.close_time.isoformat(),
        window=event.timeframe,
        input_snapshot={},
        condition_result=True,
        signal_type=SignalType.BUY_CANDIDATE,
        lane=lane,
        trigger_set_id=trigger_set.set_id,
        trigger_set_version=trigger_set.version,
    )
