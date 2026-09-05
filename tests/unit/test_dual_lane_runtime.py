from datetime import UTC, datetime, timedelta

from triggertrade.config import ExecutionVenue, load_config
from triggertrade.execution import PaperExecutionAdapter
from triggertrade.persistence import (
    ExecutionStore,
    LaneCandleLifecycle,
    RuntimeStore,
    TraceStore,
    TriggerSetStore,
    bootstrap_current_trigger_sets,
)
from triggertrade.services.dual_lane_runtime import DualLaneRuntime
from triggertrade.trigger_sets import TriggerSetStatus
from tests.unit.test_paper_runtime import FakeMarketClient, FakeResponse, _candle


def test_same_completed_candle_fans_out_to_active_and_test_lanes(tmp_path):
    active_adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    test_adapters = []
    runtime = _runtime(tmp_path, closes=("100", "98"), active_adapter=active_adapter, test_adapters=test_adapters)

    result = runtime.process_once()

    assert result.candle_id == "BTCUSDT:1m:2026-09-05T12:01:00+00:00"
    assert len(result.active) == 1
    assert len(result.test) == 1
    assert result.active[0].candle_id == result.test[0].candle_id
    assert result.active[0].execution_status == "filled"
    assert result.test[0].execution_status == "test_recorded"
    assert active_adapter.create_calls == 1
    assert test_adapters[0].create_calls == 0


def test_lane_and_trigger_set_attribution_is_persisted(tmp_path):
    path = tmp_path / "dual.sqlite3"
    result = _runtime(tmp_path, closes=("100", "98"), path=path).process_once()
    store = RuntimeStore(path)
    active = store.get_lane_lifecycle(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=result.candle_id,
        trigger_set_id="triggertrade-core",
        trigger_set_version="v1",
    )
    test = store.get_lane_lifecycle(
        lane="TEST",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=result.candle_id,
        trigger_set_id="triggertrade-core-candidate",
        trigger_set_version="v1-test",
    )

    assert active.status == "completed"
    assert test.status == "test_recorded"
    assert active.intent_id != test.intent_id
    assert ExecutionStore(path).get_by_intent(active.intent_id).lane == "ACTIVE"
    assert ExecutionStore(path).get_by_intent(test.intent_id) is None


def test_same_candle_same_lane_same_set_is_not_duplicated_after_restart(tmp_path):
    path = tmp_path / "dual.sqlite3"
    active_adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    first = _runtime(tmp_path, closes=("100", "98"), path=path, active_adapter=active_adapter).process_once()
    second = _runtime(tmp_path, closes=("100", "98"), path=path, active_adapter=active_adapter).process_once()

    assert second.active[0].skipped_reason == "already_processed"
    assert second.test[0].skipped_reason == "already_processed"
    assert active_adapter.create_calls == 1
    assert RuntimeStore(path).lane_processed_count(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=first.candle_id,
        trigger_set_id="triggertrade-core",
        trigger_set_version="v1",
    ) == 1



def test_active_restart_reconciles_existing_execution_before_duplicate_risk(tmp_path):
    path = tmp_path / "dual.sqlite3"
    active_adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    first = _runtime(tmp_path, closes=("100", "98"), path=path, active_adapter=active_adapter).process_once()
    active = RuntimeStore(path).get_lane_lifecycle(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=first.candle_id,
        trigger_set_id="triggertrade-core",
        trigger_set_version="v1",
    )
    RuntimeStore(path).save_lane_lifecycle(
        LaneCandleLifecycle(
            lane=active.lane,
            symbol=active.symbol,
            timeframe=active.timeframe,
            candle_id=active.candle_id,
            candle_open_time=active.candle_open_time,
            trigger_set_id=active.trigger_set_id,
            trigger_set_version=active.trigger_set_version,
            status="risk_recorded",
            signal_id=active.signal_id,
            intent_id=active.intent_id,
            risk_decision_id=active.risk_decision_id,
            processed_at=None,
        )
    )

    second = _runtime(tmp_path, closes=("100", "98"), path=path, active_adapter=active_adapter).process_once()
    recovered = RuntimeStore(path).get_lane_lifecycle(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=first.candle_id,
        trigger_set_id="triggertrade-core",
        trigger_set_version="v1",
    )

    assert second.active[0].execution_status == "filled"
    assert recovered.status == "completed"
    assert recovered.execution_intent_id == active.intent_id
    assert active_adapter.create_calls == 1


def test_draft_and_archive_sets_are_not_evaluated(tmp_path):
    path = tmp_path / "dual.sqlite3"
    trigger_sets = TriggerSetStore(path)
    bootstrap_current_trigger_sets(trigger_sets, created_at="2026-09-05T00:00:00+00:00")
    trigger_sets.transition_status(
        set_id="triggertrade-core-candidate",
        version="v1-test",
        status=TriggerSetStatus.ARCHIVE,
        changed_at="2026-09-05T00:10:00+00:00",
        reason="stop test",
    )
    result = _runtime(tmp_path, closes=("100", "98"), path=path, trigger_sets=trigger_sets).process_once()

    assert len(result.active) == 1
    assert result.test == ()


def test_test_lane_failure_does_not_corrupt_active_lane(tmp_path):
    class FailingAdapter(PaperExecutionAdapter):
        def create_limit_order(self, **kwargs):
            raise RuntimeError("test adapter failure")

    path = tmp_path / "dual.sqlite3"
    active_adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    runtime = _runtime(
        tmp_path,
        closes=("100", "98"),
        path=path,
        active_adapter=active_adapter,
        test_adapter_factory=lambda: FailingAdapter(clock_ms=lambda: 123),
    )

    result = runtime.process_once()

    assert result.active[0].execution_status == "filled"
    assert result.test[0].execution_status == "test_recorded"
    assert active_adapter.create_calls == 1


def test_testing_set_does_not_auto_promote_to_active(tmp_path):
    path = tmp_path / "dual.sqlite3"
    runtime = _runtime(tmp_path, closes=("100", "98"), path=path)
    runtime.process_once()

    trigger_sets = TriggerSetStore(path)
    assert trigger_sets.get_active_set("BTCUSDT", "1m").version == "v1"
    assert trigger_sets.get_set("triggertrade-core-candidate", "v1-test").status is TriggerSetStatus.TESTING


def _runtime(
    tmp_path,
    *,
    closes=("100", "98"),
    path=None,
    active_adapter=None,
    test_adapters=None,
    test_adapter_factory=None,
    trigger_sets=None,
    market_client=None,
    clock=None,
):
    env = {
        "TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.LOCAL_PAPER.value,
        "TRIGGERTRADE_WATCHLIST": "BTCUSDT",
        "TRIGGERTRADE_RUNTIME_SYMBOL": "BTCUSDT",
        "TRIGGERTRADE_CANDLE_INTERVAL": "1",
        "TRIGGERTRADE_POLL_INTERVAL_SECONDS": "1",
        "TRIGGERTRADE_STALE_AFTER_SECONDS": "120",
    }
    config = load_config(env)
    db_path = path or (tmp_path / "dual.sqlite3")
    if test_adapter_factory is None:
        def test_adapter_factory():
            adapter = PaperExecutionAdapter(clock_ms=lambda: 456)
            if test_adapters is not None:
                test_adapters.append(adapter)
            return adapter
    return DualLaneRuntime(
        config=config,
        market_client=market_client or FakeMarketClient(closes=closes),
        execution_store=ExecutionStore(db_path),
        trace_store=TraceStore(db_path),
        runtime_store=RuntimeStore(db_path),
        trigger_set_store=trigger_sets or TriggerSetStore(db_path),
        active_adapter=active_adapter or PaperExecutionAdapter(clock_ms=lambda: 123),
        test_adapter_factory=test_adapter_factory,
        clock=clock or (lambda: datetime(2026, 9, 5, 12, 2, 30, tzinfo=UTC)),
        logger=lambda message: None,
    )


def test_testing_set_waits_for_candle_after_activation(tmp_path):
    path = tmp_path / "dual.sqlite3"
    trigger_sets = TriggerSetStore(path)
    bootstrap_current_trigger_sets(trigger_sets, created_at="2026-09-05T12:02:30+00:00")

    result = _runtime(tmp_path, closes=("100", "98"), path=path, trigger_sets=trigger_sets).process_once()

    assert result.active[0].skipped_reason == "set_activation_pending"
    assert result.test[0].skipped_reason == "set_activation_pending"
    assert RuntimeStore(path).get_lane_lifecycle(
        lane="TEST",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=result.candle_id,
        trigger_set_id="triggertrade-core-candidate",
        trigger_set_version="v1-test",
    ) is None


def test_lane_checkpoint_gap_fails_closed(tmp_path):
    class GapMarketClient(FakeMarketClient):
        def recent_candles(self, symbol, interval, limit):
            older = _candle(self.start, "100")
            gap_latest = _candle(self.start + timedelta(minutes=3), "98")
            current_open = _candle(self.start + timedelta(minutes=4), "98")
            return FakeResponse({"list": [current_open, gap_latest, older]})

    path = tmp_path / "dual.sqlite3"
    runtime = _runtime(tmp_path, closes=("100", "98"), path=path)
    first = runtime.process_once()
    second = _runtime(tmp_path, path=path, market_client=GapMarketClient(), clock=lambda: datetime(2026, 9, 5, 12, 4, 30, tzinfo=UTC)).process_once()

    assert first.candle_id == "BTCUSDT:1m:2026-09-05T12:01:00+00:00"
    assert second.skipped_reason == "checkpoint_gap"

