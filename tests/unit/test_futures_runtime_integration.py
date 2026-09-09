from __future__ import annotations

from datetime import UTC, datetime, timedelta
from dataclasses import replace
from decimal import Decimal
import sqlite3

import pytest

from triggertrade.config import ExecutionVenue, load_config
from triggertrade.accounting import ClosedTradeResult, EquitySnapshot
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.execution import OrderStatus, OrderType
from triggertrade.execution.futures import FuturesTradeIntent, PositionAction, PositionState
from triggertrade.exchanges import BybitApiError, BybitResponse
from triggertrade.market_data import ContractCategory, FuturesAccountState, FuturesInstrumentMetadata
from triggertrade.market_data import FuturesMarketEvent, MarketRegimeContext, MarketRegimeLabel, RegimeCapability
from triggertrade.persistence import (
    FuturesExecutionStore,
    MessageStore,
    ResearchStore,
    TradingRulesStore,
    FuturesExecutionRecord,
    FuturesPositionRecord,
    FuturesPositionStore,
    LaneCandleLifecycle,
    OperatorStateStore,
    RuntimeStore,
    LaneRuntimeCheckpoint,
    TraceStore,
    TriggerSetStore,
    bootstrap_current_trigger_sets,
    current_futures_active_trigger_set,
    InstrumentCatalogStore,
)
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.services.futures_runtime import FuturesDualLaneRuntime, _is_futures_set
from triggertrade.services.instrument_catalog import InstrumentCatalogService
from triggertrade.services.research import ResearchService
from triggertrade.rules import DirectionMode, TakeProfitMode, TradingRulesService
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


def test_no_signal_cycle_refreshes_account_snapshot_without_order(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    client = LinearOnlyMarketClient(candles=_no_signal_candles())
    adapter = RecordingFuturesAdapter(order_status="New")
    provider = RecordingAccountProvider(_instrument(), equity=Decimal("125"), available=Decimal("119"), unrealized=Decimal("-1.5"))

    result = _runtime(
        tmp_path,
        path=path,
        client=client,
        active_adapter=adapter,
        account_provider=provider,
    ).process_once()

    snapshot = FuturesAccountingStore(path).latest_equity_snapshot()
    portfolio = DashboardReadModel(path).get_portfolio_snapshot()

    assert result.active[0].signal_type == "NO_SIGNAL"
    assert provider.calls == 1
    assert adapter.create_calls == 0
    assert snapshot is not None
    assert snapshot["equity"] == "125"
    assert snapshot["available_margin"] == "119"
    assert snapshot["unrealized_pnl"] == "-1.5"
    assert portfolio.as_of == "2026-09-05T13:10:30+00:00"
    assert portfolio.freshness_state == "STALE"


def test_signal_cycle_reuses_refreshed_active_account_once(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    adapter = RecordingFuturesAdapter(order_status="New")
    provider = RecordingAccountProvider(_instrument(), equity=Decimal("130"))

    result = _runtime(
        tmp_path,
        path=path,
        active_adapter=adapter,
        account_provider=provider,
    ).process_once()

    assert result.active[0].execution_status == "submitted"
    assert provider.calls == 1
    assert adapter.create_calls == 1
    assert FuturesAccountingStore(path).latest_equity_snapshot()["equity"] == "130"


def test_account_refresh_failure_retains_old_snapshot_and_blocks_new_entry(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    FuturesAccountingStore(path).record_equity_snapshot(
        _equity_snapshot("old-account", "2026-09-05T12:00:00+00:00", Decimal("100"))
    )
    adapter = RecordingFuturesAdapter(order_status="New")

    result = _runtime(
        tmp_path,
        path=path,
        active_adapter=adapter,
        account_provider=FailingAccountProvider(),
    ).process_once()

    snapshot = FuturesAccountingStore(path).latest_equity_snapshot()

    assert result.skipped_reason == "account_data_unavailable"
    assert snapshot["snapshot_id"] == "old-account"
    assert snapshot["observed_at"] == "2026-09-05T12:00:00+00:00"
    assert adapter.create_calls == 0


def test_runtime_recovers_checkpoint_gap_with_historical_catchup_and_account_refresh(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    store = RuntimeStore(path)
    trigger_sets = TriggerSetStore(path)
    bootstrap_current_trigger_sets(trigger_sets)
    now = datetime.now(UTC).replace(second=30, microsecond=0)
    latest_open = now.replace(second=0, microsecond=0) - timedelta(minutes=1)
    checkpoint_open = latest_open - timedelta(minutes=5)
    history_start = checkpoint_open
    store.lane_checkpoint(_lane_checkpoint(checkpoint_open))
    client = LinearOnlyMarketClient(
        candles=_flat_candles(start_time=latest_open - timedelta(minutes=2), count=3),
        historical_candles=_flat_candles(start_time=history_start, count=6),
    )
    provider = RecordingAccountProvider(_instrument(), equity=Decimal("151"), available=Decimal("149"))

    result = _runtime(
        tmp_path,
        path=path,
        client=client,
        account_provider=provider,
        active_adapter=RecordingFuturesAdapter(order_status="New"),
        clock=lambda: now,
    ).process_once()

    checkpoint = RuntimeStore(path).get_lane_checkpoint(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    )
    snapshot = FuturesAccountingStore(path).latest_equity_snapshot()
    readiness = DashboardReadModel(path).get_demo_readiness()

    assert result.skipped_reason == "checkpoint_recovered"
    assert len(result.active) == 5
    assert checkpoint.last_processed_candle_open_time == latest_open.isoformat()
    assert provider.calls == 1
    assert snapshot["equity"] == "151"
    assert {check.name: check for check in readiness.checks}["market_data"].status == "RUNNING"
    assert client.linear_historical_calls == 1


def test_one_candle_gap_processes_normally_without_historical_recovery(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 8, tzinfo=UTC)))
    client = LinearOnlyMarketClient(candles=_flat_candles(start_minute=7, count=3), historical_candles=_flat_candles(count=10))

    result = _runtime(
        tmp_path,
        path=path,
        client=client,
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()

    assert result.skipped_reason is None
    assert result.candle_id == "BTCUSDT:1m:2026-09-05T13:09:00+00:00"
    assert client.linear_historical_calls == 0


def test_no_gap_restart_is_idempotent_and_does_not_backfill(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    store = RuntimeStore(path)
    store.lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 9, tzinfo=UTC)))
    store.save_lane_lifecycle(
        LaneCandleLifecycle(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            candle_id="BTCUSDT:1m:2026-09-05T13:09:00+00:00",
            candle_open_time="2026-09-05T13:09:00+00:00",
            trigger_set_id="triggertrade-futures-core",
            trigger_set_version="v1",
            status="no_signal",
            processed_at="2026-09-05T13:09:30+00:00",
        )
    )
    client = LinearOnlyMarketClient(candles=_flat_candles(start_minute=7, count=3), historical_candles=_flat_candles(count=10))

    result = _runtime(
        tmp_path,
        path=path,
        client=client,
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()

    assert result.skipped_reason is None
    assert result.active[0].skipped_reason == "already_processed"
    assert client.linear_historical_calls == 0


def test_recovery_suppresses_stale_historical_entry_orders(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 4, tzinfo=UTC)))
    adapter = RecordingFuturesAdapter(order_status="New")
    client = LinearOnlyMarketClient(candles=_flat_candles(start_minute=8, count=3), historical_candles=_recovery_signal_candles())

    result = _runtime(
        tmp_path,
        path=path,
        client=client,
        active_adapter=adapter,
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()

    latest = RuntimeStore(path).get_lane_lifecycle(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id="BTCUSDT:1m:2026-09-05T13:09:00+00:00",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    )

    assert result.skipped_reason == "checkpoint_recovered"
    assert adapter.create_calls == 0
    assert latest.status == "stale_entry_suppressed"
    assert latest.error == "recovery_backfill_no_stale_execution"


def test_checkpoint_recovery_records_deduped_messages(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 4, tzinfo=UTC)))
    client = LinearOnlyMarketClient(candles=_flat_candles(start_minute=8, count=3), historical_candles=_flat_candles(count=10))

    _runtime(
        tmp_path,
        path=path,
        client=client,
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()
    _runtime(
        tmp_path,
        path=path,
        client=client,
        clock=lambda: datetime(2026, 9, 5, 13, 10, 45, tzinfo=UTC),
    ).process_once()

    messages = MessageStore(path).list_messages(limit=10)

    assert sum(1 for message in messages if message.title == "Runtime checkpoint gap detected") == 1
    assert sum(1 for message in messages if message.title == "Runtime checkpoint recovery completed") == 1


def test_recovery_fails_closed_on_conflicting_duplicate_candle(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 4, tzinfo=UTC)))
    historical = _flat_candles(count=10)
    duplicate = list(historical[5])
    duplicate[4] = "101"
    historical.insert(6, duplicate)

    result = _runtime(
        tmp_path,
        path=path,
        client=LinearOnlyMarketClient(candles=_flat_candles(start_minute=8, count=3), historical_candles=historical),
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()

    assert result.skipped_reason == "checkpoint_gap"


def test_recovery_fails_closed_on_out_of_order_historical_page(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 4, tzinfo=UTC)))
    client = OutOfOrderHistoricalClient(candles=_flat_candles(start_minute=8, count=3), historical_candles=_flat_candles(count=10))

    result = _runtime(
        tmp_path,
        path=path,
        client=client,
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()

    assert result.skipped_reason == "checkpoint_gap"


def test_recovery_fails_closed_on_malformed_historical_payload(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 4, tzinfo=UTC)))
    client = MalformedHistoricalClient(candles=_flat_candles(start_minute=8, count=3))
    adapter = RecordingFuturesAdapter(order_status="New")

    result = _runtime(
        tmp_path,
        path=path,
        client=client,
        active_adapter=adapter,
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()

    checkpoint = RuntimeStore(path).get_lane_checkpoint(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    )

    assert result.skipped_reason == "checkpoint_gap"
    assert checkpoint.last_processed_candle_open_time == "2026-09-05T13:04:00+00:00"
    assert adapter.create_calls == 0


def test_recovery_ignores_incomplete_historical_candle(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 4, tzinfo=UTC)))
    historical = _flat_candles(count=10) + _flat_candles(start_minute=10, count=1)

    result = _runtime(
        tmp_path,
        path=path,
        client=LinearOnlyMarketClient(candles=_flat_candles(start_minute=8, count=3), historical_candles=historical),
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()

    checkpoint = RuntimeStore(path).get_lane_checkpoint(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    )

    assert result.skipped_reason == "checkpoint_recovered"
    assert checkpoint.last_processed_candle_open_time == "2026-09-05T13:09:00+00:00"


def test_recovery_failure_keeps_heartbeat_and_readiness_non_green(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 4, tzinfo=UTC)))
    historical = [row for row in _flat_candles(count=10) if "13:07" not in datetime.fromtimestamp(int(row[0]) / 1000, UTC).isoformat()]

    _runtime(
        tmp_path,
        path=path,
        client=LinearOnlyMarketClient(candles=_flat_candles(start_minute=8, count=3), historical_candles=historical),
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).run_forever(max_cycles=1)

    checks = {check.name: check for check in DashboardReadModel(path).get_demo_readiness().checks}

    assert checks["heartbeat:futures_runtime"].status == "DEGRADED"
    assert checks["market_data"].status != "RUNNING"


def test_checkpoint_recovery_fails_closed_when_historical_sequence_has_gap(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    checkpoint_open = datetime(2026, 9, 5, 13, 4, tzinfo=UTC)
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(checkpoint_open))
    historical = [row for row in _flat_candles(count=10) if "13:07" not in datetime.fromtimestamp(int(row[0]) / 1000, UTC).isoformat()]
    client = LinearOnlyMarketClient(candles=_flat_candles(start_minute=8, count=3), historical_candles=historical)

    result = _runtime(
        tmp_path,
        path=path,
        client=client,
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()

    checkpoint = RuntimeStore(path).get_lane_checkpoint(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    )

    assert result.skipped_reason == "checkpoint_gap"
    assert checkpoint.last_processed_candle_open_time == checkpoint_open.isoformat()


def test_checkpoint_ahead_of_exchange_fails_closed_without_rewind(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    checkpoint_open = datetime(2026, 9, 5, 13, 10, tzinfo=UTC)
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(checkpoint_open))

    result = _runtime(
        tmp_path,
        path=path,
        client=LinearOnlyMarketClient(candles=_flat_candles(start_minute=7, count=3), historical_candles=_flat_candles(count=11)),
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()

    checkpoint = RuntimeStore(path).get_lane_checkpoint(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    )

    assert result.skipped_reason == "checkpoint_gap"
    assert checkpoint.last_processed_candle_open_time == checkpoint_open.isoformat()


def test_recovery_paginates_large_gap_and_processes_each_candle_once(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 0, tzinfo=UTC)))
    historical = _flat_candles(count=260)
    client = LinearOnlyMarketClient(candles=historical[-3:], historical_candles=historical, page_limit=80)

    result = _runtime(
        tmp_path,
        path=path,
        client=client,
        clock=lambda: datetime(2026, 9, 5, 17, 20, 30, tzinfo=UTC),
    ).process_once()

    assert result.skipped_reason == "checkpoint_recovered"
    assert len(result.active) == 259
    assert client.linear_historical_calls > 1
    assert RuntimeStore(path).lane_processed_count(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id="BTCUSDT:1m:2026-09-05T13:01:00+00:00",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    ) == 1


def test_recovery_paginates_newest_first_exchange_pages(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 0, tzinfo=UTC)))
    historical = _flat_candles(count=260)
    client = NewestFirstHistoricalClient(candles=historical[-3:], historical_candles=historical, page_limit=80)

    result = _runtime(
        tmp_path,
        path=path,
        client=client,
        clock=lambda: datetime(2026, 9, 5, 17, 20, 30, tzinfo=UTC),
    ).process_once()

    checkpoint = RuntimeStore(path).get_lane_checkpoint(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    )

    assert result.skipped_reason == "checkpoint_recovered"
    assert checkpoint.last_processed_candle_open_time == "2026-09-05T17:19:00+00:00"
    assert client.linear_historical_calls > 1


def test_recovery_restart_resumes_from_last_committed_checkpoint(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    store = RuntimeStore(path)
    store.lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 6, tzinfo=UTC)))
    store.save_lane_lifecycle(
        LaneCandleLifecycle(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            candle_id="BTCUSDT:1m:2026-09-05T13:06:00+00:00",
            candle_open_time="2026-09-05T13:06:00+00:00",
            trigger_set_id="triggertrade-futures-core",
            trigger_set_version="v1",
            status="no_signal",
            processed_at="2026-09-05T13:06:30+00:00",
        )
    )
    client = LinearOnlyMarketClient(candles=_flat_candles(start_minute=8, count=3), historical_candles=_flat_candles(count=10))

    result = _runtime(
        tmp_path,
        path=path,
        client=client,
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()

    assert result.skipped_reason == "checkpoint_recovered"
    assert len(result.active) == 3
    assert RuntimeStore(path).lane_processed_count(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id="BTCUSDT:1m:2026-09-05T13:06:00+00:00",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    ) == 1


def test_recovery_crash_midstream_resumes_without_duplicate_committed_candles(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    RuntimeStore(path).lane_checkpoint(_lane_checkpoint(datetime(2026, 9, 5, 13, 4, tzinfo=UTC)))
    runtime = _runtime(
        tmp_path,
        path=path,
        client=LinearOnlyMarketClient(candles=_flat_candles(start_minute=8, count=3), historical_candles=_flat_candles(count=10)),
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    )
    original = runtime._process_lane
    calls = {"count": 0}

    def crashing_process_lane(**kwargs):
        result = original(**kwargs)
        if kwargs["lane"] is Lane.ACTIVE:
            calls["count"] += 1
            if calls["count"] == 2:
                raise RuntimeError("simulated recovery crash")
        return result

    runtime._process_lane = crashing_process_lane
    with pytest.raises(RuntimeError, match="simulated recovery crash"):
        runtime.process_once()

    resumed = _runtime(
        tmp_path,
        path=path,
        client=LinearOnlyMarketClient(candles=_flat_candles(start_minute=8, count=3), historical_candles=_flat_candles(count=10)),
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()

    assert resumed.skipped_reason == "checkpoint_recovered"
    assert len(resumed.active) == 3
    assert RuntimeStore(path).lane_processed_count(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id="BTCUSDT:1m:2026-09-05T13:05:00+00:00",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    ) == 1


def test_restart_refreshes_account_snapshot_without_zero_reset(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    FuturesAccountingStore(path).record_equity_snapshot(
        _equity_snapshot("before-restart", "2026-09-05T12:00:00+00:00", Decimal("100"))
    )

    _runtime(
        tmp_path,
        path=path,
        client=LinearOnlyMarketClient(candles=_no_signal_candles()),
        account_provider=RecordingAccountProvider(_instrument(), equity=Decimal("144"), available=Decimal("140")),
        clock=lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC),
    ).process_once()
    _runtime(
        tmp_path,
        path=path,
        client=LinearOnlyMarketClient(candles=_no_signal_candles()),
        account_provider=RecordingAccountProvider(_instrument(), equity=Decimal("145"), available=Decimal("141")),
        clock=lambda: datetime(2026, 9, 5, 13, 11, 30, tzinfo=UTC),
    ).process_once()

    snapshot = FuturesAccountingStore(path).latest_equity_snapshot()

    assert snapshot["equity"] == "145"
    assert snapshot["available_margin"] == "141"
    assert snapshot["wallet_balance"] == "145"


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



def test_runtime_pins_current_trading_rules_version_and_resolved_snapshot(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    config = load_config(_env(path))
    rules = TradingRulesService(TradingRulesStore(path))
    rules.ensure_initial_version(config)
    current = rules.create_rules_version_from_current(
        changes={"fixed_take_profit_pct": Decimal("0.02"), "minimum_take_profit_pct": Decimal("0.01"), "minimum_net_edge_enabled": False},
        created_source="unit",
        created_at="2026-09-07T01:00:00+00:00",
    ).rules

    result = _runtime(tmp_path, path=path, active_adapter=RecordingFuturesAdapter(order_status="New")).process_once()
    active = RuntimeStore(path).get_lane_lifecycle(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=result.candle_id,
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    )
    position = FuturesPositionStore(path).get_position(futures_position_id(active.intent_id))

    assert position.rules_version_id == current.rules_version_id
    assert position.rule_snapshot["rules_version"] == "v2"
    assert position.rule_snapshot["fixed_take_profit_pct"] == "0.02"
    assert position.rule_snapshot["minimum_net_edge_enabled"] == "False"
    assert position.rule_snapshot["capital_denominator_source"] == "equity"
    assert TradingRulesService(TradingRulesStore(path)).get_current_rules_version().version == "v2"


def test_runtime_new_active_entries_use_promoted_research_set_and_rules_pair(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    config = load_config(_env(path))
    bootstrap_current_trigger_sets(TriggerSetStore(path))
    rules = TradingRulesService(TradingRulesStore(path))
    original = rules.ensure_initial_version(config)
    candidate_rules = rules.create_rules_version_from_current(
        changes={"fixed_take_profit_pct": Decimal("0.026"), "minimum_take_profit_pct": Decimal("0.01"), "minimum_net_edge_enabled": False},
        created_source="unit",
    ).rules
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE trading_rules_current SET rules_version_id = ?, updated_at = ? WHERE scope = ?",
            (original.rules_version_id, "2026-09-08T12:00:00+00:00", "LIVE"),
        )
    research_service = ResearchService(
        store=ResearchStore(path),
        trigger_set_store=TriggerSetStore(path),
        trading_rules_store=TradingRulesStore(path),
        message_store=MessageStore(path),
    )
    research = research_service.create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=candidate_rules.rules_version_id,
    )
    research_service.request_make_active(research.research_id)
    adapter = RecordingFuturesAdapter(order_status="New")

    result = _runtime(tmp_path, path=path, active_adapter=adapter).process_once()
    active = RuntimeStore(path).get_lane_lifecycle(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=result.candle_id,
        trigger_set_id="triggertrade-futures-candidate",
        trigger_set_version="v2-test",
    )
    position = FuturesPositionStore(path).get_position(futures_position_id(active.intent_id))

    assert result.active[0].execution_status == "submitted"
    assert active.rules_version_id == candidate_rules.rules_version_id
    assert position.trigger_set_id == "triggertrade-futures-candidate"
    assert position.trigger_set_version == "v2-test"
    assert position.rules_version_id == candidate_rules.rules_version_id
    assert position.rule_snapshot["fixed_take_profit_pct"] == "0.026"


def test_runtime_direction_mode_filters_without_creating_short_alpha(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    config = load_config(_env(path))
    rules = TradingRulesService(TradingRulesStore(path))
    rules.ensure_initial_version(config)
    rules.create_rules_version_from_current(
        changes={"direction_mode": DirectionMode.SHORT_ONLY},
        created_source="unit",
        created_at="2026-09-07T01:00:00+00:00",
    )
    adapter = RecordingFuturesAdapter(order_status="New")

    result = _runtime(tmp_path, path=path, active_adapter=adapter).process_once()

    assert result.active[0].skipped_reason == "long_entries_disabled_by_current_trading_rules"
    assert adapter.create_calls == 0


def test_runtime_dynamic_take_profit_fails_closed_until_algorithm_is_approved(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    config = load_config(_env(path))
    rules = TradingRulesService(TradingRulesStore(path))
    rules.ensure_initial_version(config)
    rules.create_rules_version_from_current(
        changes={"take_profit_mode": TakeProfitMode.DYNAMIC, "fixed_take_profit_pct": None, "minimum_take_profit_pct": Decimal("0.01")},
        created_source="unit",
        created_at="2026-09-07T01:00:00+00:00",
    )
    adapter = RecordingFuturesAdapter(order_status="New")

    result = _runtime(tmp_path, path=path, active_adapter=adapter).process_once()

    assert result.active[0].skipped_reason == "dynamic take-profit mode is not approved for runtime execution"
    assert adapter.create_calls == 0


def test_runtime_daily_loss_enabled_allows_active_entry_before_threshold(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    config = load_config(_env(path))
    rules = TradingRulesService(TradingRulesStore(path))
    rules.ensure_initial_version(config)
    current = rules.create_rules_version_from_current(
        changes={"daily_loss_limit_enabled": True, "daily_loss_limit_pct": Decimal("0.02")},
        created_source="unit",
        created_at="2026-09-07T01:00:00+00:00",
    ).rules
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

    assert result.active[0].execution_status == "submitted"
    assert adapter.create_calls == 1
    position = FuturesPositionStore(path).get_position(futures_position_id(active.intent_id))
    assert position.rules_version_id == current.rules_version_id
    assert position.rule_snapshot["daily_loss_status"] == "OK"
    assert position.rule_snapshot["daily_loss_enabled"] == "True"


def test_runtime_daily_loss_latch_blocks_only_active_new_entries_and_creates_one_message(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    config = load_config(_env(path))
    rules = TradingRulesService(TradingRulesStore(path))
    rules.ensure_initial_version(config)
    current = rules.create_rules_version_from_current(
        changes={"daily_loss_limit_enabled": True, "daily_loss_limit_pct": Decimal("0.02")},
        created_source="unit",
        created_at="2026-09-07T01:00:00+00:00",
    ).rules
    accounting = FuturesAccountingStore(path)
    accounting.record_equity_snapshot(_equity_snapshot("runtime-equity", "2026-09-05T00:00:01+00:00", Decimal("100")))
    accounting.record_closed_trade(_closed_trade("runtime-loss", Decimal("-2"), evidence_source="exchange"))
    accounting.record_closed_trade(_closed_trade("runtime-test-loss", Decimal("-50"), evidence_source="test_simulation"))
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

    assert result.active[0].skipped_reason == "daily_loss_limit_reached"
    assert result.test[0].execution_status == "test_simulated"
    assert adapter.create_calls == 0
    assert active.rules_version_id == current.rules_version_id
    assert active.rules_evaluation["blocking_rule"] == "daily_loss_limit_reached"
    assert active.rules_evaluation["daily_loss_realized_net_pnl"] == "-2"
    assert active.rules_evaluation["daily_loss_latched"] == "True"
    messages = MessageStore(path).list_messages()
    assert len(messages) == 1
    assert messages[0].dedupe_key == "daily_loss:2026-09-05:latched"


def test_runtime_disabled_net_edge_excludes_expected_move_requirement(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    config = load_config(_env(path, demo_expected_gross_move=""))
    rules = TradingRulesService(TradingRulesStore(path))
    rules.ensure_initial_version(config)
    current = rules.create_rules_version_from_current(
        changes={"minimum_net_edge_enabled": False, "minimum_net_edge_pct": None},
        created_source="unit",
        created_at="2026-09-07T01:00:00+00:00",
    ).rules
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
    position = FuturesPositionStore(path).get_position(futures_position_id(active.intent_id))

    assert result.active[0].execution_status == "submitted"
    assert adapter.create_calls == 1
    assert position.rules_version_id == current.rules_version_id
    assert position.rule_snapshot["minimum_net_edge_enabled"] == "False"
    assert position.rule_snapshot["minimum_net_edge_pct"] is None


def test_runtime_rules_rejection_persists_structured_rules_evidence(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    config = load_config(_env(path))
    rules = TradingRulesService(TradingRulesStore(path))
    rules.ensure_initial_version(config)
    current = rules.create_rules_version_from_current(
        changes={"direction_mode": DirectionMode.SHORT_ONLY},
        created_source="unit",
        created_at="2026-09-07T01:00:00+00:00",
    ).rules

    result = _runtime(tmp_path, path=path, active_adapter=RecordingFuturesAdapter(order_status="New")).process_once()
    active = RuntimeStore(path).get_lane_lifecycle(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=result.candle_id,
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
    )

    assert active.rules_version_id == current.rules_version_id
    assert active.rules_evaluation["blocking_rule"] == "long_entries_disabled_by_current_trading_rules"
    assert active.rules_evaluation["direction_mode"] == "SHORT_ONLY"
    assert active.rules_evaluation["symbol"] == "BTCUSDT"



def test_stale_catalog_refresh_failure_blocks_new_entries_even_with_old_cache(tmp_path):
    from datetime import timedelta

    path = tmp_path / "runtime.sqlite3"
    catalog = InstrumentCatalogService(
        store=InstrumentCatalogStore(path),
        client=LinearOnlyMarketClient(),
        clock=lambda: datetime(2026, 9, 5, 13, 0, tzinfo=UTC),
        stale_after=timedelta(seconds=1),
    )
    assert catalog.refresh_instrument_catalog().status == "OK"

    class FailingCatalogClient(LinearOnlyMarketClient):
        def linear_instruments_info(self, *, cursor=None, limit=1000):
            raise BybitApiError("public catalog timeout")

    stale_catalog = InstrumentCatalogService(
        store=InstrumentCatalogStore(path),
        client=FailingCatalogClient(),
        clock=lambda: datetime(2026, 9, 5, 13, 1, tzinfo=UTC),
        stale_after=timedelta(seconds=1),
    )
    adapter = RecordingFuturesAdapter(order_status="New")

    result = _runtime(
        tmp_path,
        path=path,
        client=FailingCatalogClient(),
        active_adapter=adapter,
        instrument_catalog=stale_catalog,
    ).process_once()

    assert result.skipped_reason == "market_data_unavailable"
    assert adapter.create_calls == 0

def test_invalid_catalog_instrument_blocks_new_runtime_entries(tmp_path):
    client = LinearOnlyMarketClient()
    original = client.linear_instruments_info

    def suspended(*, cursor=None, limit=1000):
        payload = original(cursor=cursor, limit=limit).result
        payload["list"][0]["status"] = "PreLaunch"
        return BybitResponse(0, "OK", payload)

    client.linear_instruments_info = suspended

    result = _runtime(tmp_path, client=client, active_adapter=RecordingFuturesAdapter(order_status="New")).process_once()

    assert result.candle_id is None
    assert result.skipped_reason == "market_data_unavailable"


def test_catalog_outage_still_monitors_existing_position_from_snapshot(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    position_store = FuturesPositionStore(path)
    position = _position_record(open_intent_id="snapshot-open")
    position_store.save_open_position(position)
    client = LinearOnlyMarketClient()
    original = client.linear_instruments_info

    def suspended(*, cursor=None, limit=1000):
        payload = original(cursor=cursor, limit=limit).result
        payload["list"][0]["status"] = "PreLaunch"
        return BybitResponse(0, "OK", payload)

    client.linear_instruments_info = suspended
    adapter = RecordingFuturesAdapter(order_status="New")

    result = _runtime(
        tmp_path,
        path=path,
        client=client,
        active_adapter=adapter,
        position_store=position_store,
        account_provider=lambda instrument: _account(instrument, mark_price=Decimal("101")),
    ).process_once()

    assert result.skipped_reason == "market_data_unavailable"
    assert adapter.create_calls == 1
    assert adapter.created[0]["symbol"] == "BTCUSDT"
    assert adapter.created[0]["action"] is PositionAction.CLOSE_LONG

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
    instrument_catalog=None,
    clock=None,
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
        instrument_catalog=instrument_catalog,
        clock=clock or (lambda: datetime(2026, 9, 5, 13, 10, 30, tzinfo=UTC)),
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
    def __init__(self, candles=None, *, historical_candles=None, page_limit=None):
        self._candles = candles or _linear_candles()
        self._historical_candles = historical_candles or self._candles
        self._page_limit = page_limit
        self.linear_instrument_calls = 0
        self.linear_candle_calls = 0
        self.linear_historical_calls = 0
        self.spot_instrument_calls = 0
        self.spot_candle_calls = 0

    def linear_instrument_metadata(self, symbol):
        self.linear_instrument_calls += 1
        return BybitResponse(0, "OK", _instrument_payload())

    def linear_instruments_info(self, *, cursor=None, limit=1000):
        self.linear_instrument_calls += 1
        return BybitResponse(0, "OK", {**_instrument_payload(), "nextPageCursor": ""})

    def linear_recent_candles(self, symbol, interval, limit):
        self.linear_candle_calls += 1
        return BybitResponse(0, "OK", {"list": list(reversed(self._candles))})

    def linear_historical_candles(self, symbol, interval, start_ms=None, end_ms=None, limit=200):
        self.linear_historical_calls += 1
        safe_limit = self._page_limit or limit
        rows = [
            row
            for row in self._historical_candles
            if (start_ms is None or int(row[0]) >= start_ms) and (end_ms is None or int(row[0]) <= end_ms)
        ]
        return BybitResponse(0, "OK", {"list": list(reversed(rows[:safe_limit]))})

    def instrument_metadata(self, symbol):
        self.spot_instrument_calls += 1
        raise AssertionError("spot instrument API must not be used by futures runtime")

    def recent_candles(self, symbol, interval, limit):
        self.spot_candle_calls += 1
        raise AssertionError("spot candle API must not be used by futures runtime")


class NewestFirstHistoricalClient(LinearOnlyMarketClient):
    def linear_historical_candles(self, symbol, interval, start_ms=None, end_ms=None, limit=200):
        self.linear_historical_calls += 1
        safe_limit = self._page_limit or limit
        rows = [
            row
            for row in reversed(self._historical_candles)
            if (start_ms is None or int(row[0]) >= start_ms) and (end_ms is None or int(row[0]) <= end_ms)
        ]
        return BybitResponse(0, "OK", {"list": rows[:safe_limit]})


class OutOfOrderHistoricalClient(LinearOnlyMarketClient):
    def linear_historical_candles(self, symbol, interval, start_ms=None, end_ms=None, limit=200):
        self.linear_historical_calls += 1
        rows = _flat_candles(start_minute=4, count=3)
        return BybitResponse(0, "OK", {"list": [rows[0], rows[2], rows[1]]})


class MalformedHistoricalClient(LinearOnlyMarketClient):
    def linear_historical_candles(self, symbol, interval, start_ms=None, end_ms=None, limit=200):
        self.linear_historical_calls += 1
        return BybitResponse(0, "OK", {"list": [["not-a-timestamp"]]})


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


class RecordingAccountProvider:
    def __init__(
        self,
        instrument,
        *,
        equity=Decimal("100"),
        available=None,
        unrealized=Decimal("0"),
        position_size=Decimal("0"),
        mark_price=None,
    ):
        self.instrument = instrument
        self.equity = equity
        self.available = equity if available is None else available
        self.unrealized = unrealized
        self.position_size = position_size
        self.mark_price = mark_price
        self.calls = 0

    def __call__(self, instrument):
        self.calls += 1
        return _account(
            instrument,
            equity=self.equity,
            available_margin=self.available,
            unrealized_pnl=self.unrealized,
            position_size=self.position_size,
            mark_price=self.mark_price,
        )


class FailingAccountProvider:
    def __call__(self, instrument):
        raise BybitApiError("account read failed")


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


def _flat_candles(*, start_minute=0, count=10, start_time=None):
    start = start_time or datetime(2026, 9, 5, 13, start_minute, tzinfo=UTC)
    rows = []
    for index in range(count):
        open_time = start + timedelta(minutes=index)
        rows.append(
            [
                str(int(open_time.timestamp() * 1000)),
                "100",
                "100",
                "100",
                "100",
                "1",
                "100",
            ]
        )
    return rows


def _recovery_signal_candles():
    rows = _flat_candles(count=10)
    rows[-1][1] = "95"
    rows[-1][2] = "95"
    rows[-1][3] = "95"
    rows[-1][4] = "95"
    rows[-1][5] = "3"
    rows[-1][6] = "285"
    return rows


def _lane_checkpoint(open_time):
    return LaneRuntimeCheckpoint(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
        last_processed_candle_id=f"BTCUSDT:1m:{open_time.isoformat()}",
        last_processed_candle_open_time=open_time.isoformat(),
        last_processed_at=(open_time + timedelta(seconds=30)).isoformat(),
        runtime_version="futures-runtime-v1",
    )


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
                "status": "Trading",
                "quoteCoin": "USDT",
                "settleCoin": "USDT",
                "priceFilter": {"tickSize": "0.1"},
                "lotSizeFilter": {"qtyStep": "0.001", "minOrderQty": "0.001", "maxOrderQty": "100", "minNotionalValue": "5"},
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


def _account(
    instrument,
    *,
    equity=Decimal("100"),
    available_margin=Decimal("100"),
    unrealized_pnl=Decimal("0"),
    position_size=Decimal("0"),
    mark_price=None,
):
    return FuturesAccountState(
        symbol=instrument.symbol,
        category=ContractCategory.LINEAR,
        settlement_asset=instrument.settlement_asset,
        available_margin=available_margin,
        equity=equity,
        wallet_balance=equity,
        configured_leverage=Decimal("1"),
        margin_mode="ISOLATED",
        position_mode="ONE_WAY",
        position_size=position_size,
        mark_price=mark_price,
        unrealized_pnl=unrealized_pnl,
    )


def _equity_snapshot(snapshot_id: str, observed_at: str, equity: Decimal):
    return EquitySnapshot(
        snapshot_id=snapshot_id,
        observed_at=observed_at,
        source="exchange_wallet",
        wallet_balance=equity,
        equity=equity,
        available_margin=equity,
        used_margin=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        realized_pnl=Decimal("0"),
        running_peak=equity,
        drawdown_absolute=Decimal("0"),
        drawdown_percent=Decimal("0"),
        max_drawdown=Decimal("0"),
    )


def _closed_trade(trade_id: str, net_pnl: Decimal, *, evidence_source: str = "exchange"):
    return ClosedTradeResult(
        trade_id=trade_id,
        symbol="BTCUSDT",
        direction=PositionState.LONG,
        quantity=Decimal("1"),
        leverage=Decimal("1"),
        entry_vwap=Decimal("100"),
        exit_vwap=Decimal("99"),
        gross_pnl=net_pnl,
        entry_fee=Decimal("0"),
        exit_fee=Decimal("0"),
        other_fees=Decimal("0"),
        funding=Decimal("0"),
        net_pnl=net_pnl,
        opened_at="2026-09-05T00:00:00+00:00",
        closed_at="2026-09-05T01:00:00+00:00",
        duration_seconds=3600,
        evidence_source=evidence_source,
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
        instrument_snapshot={
            "symbol": "BTCUSDT",
            "category": "linear",
            "contract_type": "LinearPerpetual",
            "settle_coin": "USDT",
            "quote_coin": "USDT",
            "tick_size": "0.1",
            "qty_step": "0.001",
            "min_order_qty": "0.001",
            "max_order_qty": "100",
            "min_notional_value": "5",
            "min_leverage": "1",
            "max_leverage": "100",
            "leverage_step": "0.01",
            "catalog_hash": "unit-catalog",
            "source": "unit",
            "status": "Trading",
        },
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
