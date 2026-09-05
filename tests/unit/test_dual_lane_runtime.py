from datetime import UTC, datetime, timedelta

from triggertrade.config import ExecutionVenue, load_config
from triggertrade.execution import PaperExecutionAdapter
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.dashboard.__main__ import render_dashboard
from triggertrade.persistence import (
    ExecutionStore,
    LaneCandleLifecycle,
    RuntimeStore,
    TraceStore,
    TriggerSetStore,
    bootstrap_current_trigger_sets,
    current_active_trigger_set,
    current_rule_definitions,
    current_testing_trigger_set,
)
from triggertrade.services.dual_lane_runtime import DualLaneRuntime
from triggertrade.trigger_sets import Lane, TriggerSetStatus
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
    assert result.test[0].skipped_reason == "volume_not_confirmed"
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
        trigger_set_version="v2-test",
    )

    assert active.status == "completed"
    assert test.status == "no_intent"
    assert test.intent_id is None
    assert ExecutionStore(path).get_by_intent(active.intent_id).lane == "ACTIVE"


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
    _bootstrap_legacy_spot_sets(trigger_sets, created_at="2026-09-05T00:00:00+00:00")
    trigger_sets.transition_status(
        set_id="triggertrade-core-candidate",
        version="v2-test",
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
    assert result.test[0].skipped_reason == "volume_not_confirmed"
    assert active_adapter.create_calls == 1


def test_testing_set_does_not_auto_promote_to_active(tmp_path):
    path = tmp_path / "dual.sqlite3"
    runtime = _runtime(tmp_path, closes=("100", "98"), path=path)
    runtime.process_once()

    trigger_sets = TriggerSetStore(path)
    assert trigger_sets.get_active_set("BTCUSDT", "1m").version == "v1"
    assert trigger_sets.get_set("triggertrade-core-candidate", "v2-test").status is TriggerSetStatus.TESTING


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
    stale_after_seconds="120",
):
    env = {
        "TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.LOCAL_PAPER.value,
        "TRIGGERTRADE_WATCHLIST": "BTCUSDT",
        "TRIGGERTRADE_RUNTIME_SYMBOL": "BTCUSDT",
        "TRIGGERTRADE_CANDLE_INTERVAL": "1",
        "TRIGGERTRADE_POLL_INTERVAL_SECONDS": "1",
        "TRIGGERTRADE_STALE_AFTER_SECONDS": stale_after_seconds,
    }
    config = load_config(env)
    db_path = path or (tmp_path / "dual.sqlite3")
    trigger_set_store = trigger_sets or TriggerSetStore(db_path)
    if trigger_sets is None:
        _bootstrap_legacy_spot_sets(trigger_set_store)
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
        trigger_set_store=trigger_set_store,
        active_adapter=active_adapter or PaperExecutionAdapter(clock_ms=lambda: 123),
        test_adapter_factory=test_adapter_factory,
        clock=clock or (lambda: datetime(2026, 9, 5, 12, 2, 30, tzinfo=UTC)),
        logger=lambda message: None,
    )


def test_testing_set_waits_for_candle_after_activation(tmp_path):
    path = tmp_path / "dual.sqlite3"
    trigger_sets = TriggerSetStore(path)
    _bootstrap_legacy_spot_sets(trigger_sets, created_at="2026-09-05T12:02:30+00:00")

    result = _runtime(tmp_path, closes=("100", "98"), path=path, trigger_sets=trigger_sets).process_once()

    assert result.active[0].skipped_reason == "set_activation_pending"
    assert result.test[0].skipped_reason == "set_activation_pending"
    assert RuntimeStore(path).get_lane_lifecycle(
        lane="TEST",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=result.candle_id,
        trigger_set_id="triggertrade-core-candidate",
        trigger_set_version="v2-test",
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




class VolumeConfirmedMarketClient(FakeMarketClient):
    def recent_candles(self, symbol, interval, limit):
        rows = []
        for i in range(60):
            rows.append(_volume_candle(self.start + timedelta(minutes=i), "100", "1"))
        rows.append(_volume_candle(self.start + timedelta(minutes=60), "98", "2"))
        rows.append(_volume_candle(self.start + timedelta(minutes=61), "98", "1"))
        return FakeResponse({"list": list(reversed(rows))})


def test_testing_candidate_evaluates_trg_002_and_records_confirmed_set(tmp_path):
    path = tmp_path / "dual.sqlite3"
    result = _runtime(
        tmp_path,
        path=path,
        market_client=VolumeConfirmedMarketClient(),
        clock=lambda: datetime(2026, 9, 5, 13, 1, 30, tzinfo=UTC),
    ).process_once()

    assert result.test[0].execution_status == "test_recorded"
    test = RuntimeStore(path).get_lane_lifecycle(
        lane="TEST",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=result.candle_id,
        trigger_set_id="triggertrade-core-candidate",
        trigger_set_version="v2-test",
    )
    assert test.status == "test_recorded"

    import sqlite3
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT signal_type, condition_result, input_snapshot
            FROM trigger_evaluations
            WHERE trigger_rule_id = 'TRG-002' AND lane = 'TEST'
            """
        ).fetchone()
    assert row["signal_type"] == "CONFIRMED"
    assert row["condition_result"] == 1
    import json
    assert json.loads(row["input_snapshot"])["relative_volume"] == "2"


def test_market_regime_is_persisted_and_linked_to_lane_trace(tmp_path):
    path = tmp_path / "dual.sqlite3"
    result = _runtime(
        tmp_path,
        path=path,
        market_client=VolumeConfirmedMarketClient(),
        clock=lambda: datetime(2026, 9, 5, 13, 1, 30, tzinfo=UTC),
    ).process_once()
    store = RuntimeStore(path)
    active = store.get_lane_lifecycle(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=result.candle_id,
        trigger_set_id="triggertrade-core",
        trigger_set_version="v1",
    )
    regime = store.get_market_regime(active.regime_context_id)
    trace = DashboardReadModel(path).get_lane_trace(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=result.candle_id,
        trigger_set_id="triggertrade-core",
        trigger_set_version="v1",
    )

    assert active.regime_state == "SIDEWAYS"
    assert regime.rule_id == "CTX-REGIME"
    assert regime.version == "0.1.0"
    assert trace.regime["label"] == "SIDEWAYS"
    assert trace.trade_intent["regime_state"] == "SIDEWAYS"


def test_dashboard_regime_coverage_and_analytics_are_backend_backed(tmp_path):
    path = tmp_path / "dual.sqlite3"
    _runtime(
        tmp_path,
        path=path,
        market_client=VolumeConfirmedMarketClient(),
        clock=lambda: datetime(2026, 9, 5, 13, 1, 30, tzinfo=UTC),
    ).process_once()
    model = DashboardReadModel(path)

    current = model.get_current_market_regime()
    evidence = model.list_test_set_evidence()[0]
    rows = model.list_regime_analytics()

    assert current.state == "SIDEWAYS"
    assert current.rule == "CTX-REGIME@0.1.0"
    assert evidence.regime_coverage == "1 regimes: SIDEWAYS"
    assert any(row.regime == "SIDEWAYS" and row.signals >= 1 for row in rows)
    html = render_dashboard(model, initial_page="analytics")
    overview_html = render_dashboard(model, initial_page="overview")
    assert "By Regime" in html
    assert "Market regime" in overview_html
    assert "SIDEWAYS" in overview_html


def _volume_candle(open_time: datetime, close: str, volume: str) -> list[str]:
    return [
        str(int(open_time.timestamp() * 1000)),
        close,
        close,
        close,
        close,
        volume,
        close,
    ]



def test_trg_002_uses_runtime_stale_after_seconds(tmp_path):
    from triggertrade.services.dual_lane_runtime import _volume_signal
    from triggertrade.services.runtime import CompletedCandle
    from triggertrade.persistence import current_testing_trigger_set
    import json

    candles = parse_candles_for_volume_confirmed()
    completed = CompletedCandle(
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id="BTCUSDT:1m:2026-09-05T13:00:00+00:00",
        open_time=datetime(2026, 9, 5, 13, 0, tzinfo=UTC),
        close_time=datetime(2026, 9, 5, 13, 1, tzinfo=UTC),
        candle=candles[-2],
        previous_candle=candles[-3],
    )
    signal = _volume_signal(
        completed=completed,
        candles=candles,
        lane=Lane.TEST,
        trigger_set=current_testing_trigger_set(created_at="2026-09-05T00:00:00+00:00"),
        now=datetime(2026, 9, 5, 13, 1, 30, tzinfo=UTC),
        stale_after_seconds=10,
    )

    snapshot = signal.input_snapshot
    assert signal.signal_type == "NOT_CONFIRMED"
    assert snapshot["stale_after_seconds"] == "10"
    assert snapshot["stale_data_reason"] == "stale_candle"


def parse_candles_for_volume_confirmed():
    from triggertrade.market_data import parse_spot_candles

    candles = parse_spot_candles(VolumeConfirmedMarketClient().recent_candles("BTCUSDT", "1", 70).result)
    return tuple(sorted(candles, key=lambda candle: candle.start_time_ms))


def _bootstrap_legacy_spot_sets(store: TriggerSetStore, *, created_at: str = "2026-09-05T00:00:00+00:00") -> None:
    for rule in current_rule_definitions(created_at=created_at):
        store.save_rule(rule)
    store.create_set(current_active_trigger_set(created_at=created_at))
    store.create_set(current_testing_trigger_set(created_at=created_at))
