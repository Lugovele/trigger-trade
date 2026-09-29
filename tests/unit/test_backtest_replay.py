from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
import sqlite3

import pytest

from triggertrade.backtest import BACKTEST_EVIDENCE_SOURCE, BacktestPlan, BacktestStatus, ExactBacktestTriggerSetResolver, run_backtest
from triggertrade.backtest.comparison import compare_backtest_runs
from triggertrade.backtest.data import BybitHistoricalDataSource, HistoricalDataError, HistoricalKlineCache, validate_historical_candles
from triggertrade.backtest.engine import BacktestEngineError
from triggertrade.backtest.models import BACKTEST_SIMULATOR_VERSION, HistoricalCandle
from triggertrade.backtest.simulator import BacktestFuturesSimulator, BacktestSimulationError
from triggertrade.config import ExecutionVenue, load_config
from triggertrade.dashboard.__main__ import render_backtest_detail, render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.execution import OrderType
from triggertrade.execution.futures import FuturesTradeIntent, PositionAction, PositionState
from triggertrade.market_data import ContractCategory, FuturesInstrumentMetadata
from triggertrade.persistence import FuturesExecutionStore, RuntimeStore, TraceStore, TriggerSetStore, bootstrap_current_trigger_sets, current_futures_active_trigger_set
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType, TriggerSetStatus
from triggertrade.triggers import DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY, DECLARATIVE_METRIC_PREDICATE_SCHEMA
from triggertrade.exchanges import BybitResponse


def test_historical_candles_reject_invalid_order_duplicates_gaps_and_scope():
    candles = _candles(5)

    assert validate_historical_candles(candles)
    with pytest.raises(HistoricalDataError, match="ordered"):
        validate_historical_candles(tuple(reversed(candles)))
    with pytest.raises(HistoricalDataError, match="duplicate"):
        validate_historical_candles(candles + (candles[-1],))
    with pytest.raises(HistoricalDataError, match="gap"):
        validate_historical_candles(candles[:2] + candles[3:])
    with pytest.raises(HistoricalDataError, match="symbol"):
        validate_historical_candles((replace(candles[0], symbol="ETHUSDT"),))
    with pytest.raises(HistoricalDataError, match="completed"):
        validate_historical_candles((replace(candles[0], completed=False),))


def test_aligned_7d_historical_window_passes_strict_boundary_validation():
    start = datetime(2026, 9, 19, 10, 49, tzinfo=UTC)
    end = datetime(2026, 9, 26, 10, 49, tzinfo=UTC)
    candles = tuple(_candle(index, start=start) for index in range(7 * 24 * 60))

    validated = validate_historical_candles(candles, start=start, end=end)

    assert validated[0].open_time == start
    assert validated[-1].close_time == end
    assert len(validated) == 10080


def test_off_boundary_historical_window_still_fails_closed():
    start = datetime(2026, 9, 19, 10, 49, tzinfo=UTC)
    end = datetime(2026, 9, 19, 10, 52, tzinfo=UTC)
    candles = tuple(_candle(index, start=start) for index in range(3))

    with pytest.raises(HistoricalDataError, match="boundary"):
        validate_historical_candles(candles, start=start + timedelta(seconds=58, microseconds=413000), end=end)
    with pytest.raises(HistoricalDataError, match="boundary"):
        validate_historical_candles(candles, start=start, end=end + timedelta(seconds=58, microseconds=413000))


def test_historical_cache_reuses_same_validated_content(tmp_path):
    cache = HistoricalKlineCache(tmp_path / "history")
    candles = _candles(5)
    start, end = candles[0].open_time, candles[-1].close_time

    saved = cache.save(candles, symbol="BTCUSDT", category="linear", timeframe="1m", start=start, end=end)
    loaded = cache.load(symbol="BTCUSDT", category="linear", timeframe="1m", start=start, end=end)

    assert loaded is not None
    assert loaded.content_hash == saved.content_hash
    assert loaded.candles == saved.candles

    with pytest.raises(HistoricalDataError, match="boundary"):
        cache.save(candles[1:], symbol="BTCUSDT", category="linear", timeframe="1m", start=start, end=end)


def test_bybit_historical_source_supports_research_v1_linear_symbols_and_uses_requested_instrument(tmp_path):
    start = datetime(2026, 9, 19, 10, 49, tzinfo=UTC)
    end = start + timedelta(minutes=2)
    client = _FakeHistoricalClient()
    source = BybitHistoricalDataSource(client, cache=HistoricalKlineCache(tmp_path / "history"), retry_sleep_seconds=0)

    eth = source.load(symbol="ETHUSDT", category="linear", timeframe="1m", start=start, end=end, use_cache=False)
    pepe = source.load(symbol="1000PEPEUSDT", category="linear", timeframe="1m", start=start, end=end, use_cache=False)

    assert client.calls[0]["symbol"] == "ETHUSDT"
    assert client.calls[1]["symbol"] == "1000PEPEUSDT"
    assert {candle.symbol for candle in eth.candles} == {"ETHUSDT"}
    assert {candle.symbol for candle in pepe.candles} == {"1000PEPEUSDT"}


def test_bybit_historical_source_still_fails_closed_for_unsupported_scope(tmp_path):
    start = datetime(2026, 9, 19, 10, 49, tzinfo=UTC)
    end = start + timedelta(minutes=1)
    source = BybitHistoricalDataSource(_FakeHistoricalClient(), cache=HistoricalKlineCache(tmp_path / "history"), retry_sleep_seconds=0)

    source.load(symbol="BTCUSDT", category="linear", timeframe="1m", start=start, end=end, use_cache=False)
    with pytest.raises(HistoricalDataError, match="linear perpetual"):
        source.load(symbol="BTCUSDT", category="spot", timeframe="1m", start=start, end=end, use_cache=False)
    with pytest.raises(HistoricalDataError, match="1m"):
        source.load(symbol="BTCUSDT", category="linear", timeframe="5m", start=start, end=end, use_cache=False)
    with pytest.raises(HistoricalDataError, match="Research V1 linear perpetual"):
        source.load(symbol="UNKNOWNUSDT", category="linear", timeframe="1m", start=start, end=end, use_cache=False)


def test_backtest_simulator_fills_after_decision_candle_and_records_backtest_source(tmp_path):
    store = FuturesAccountingStore(tmp_path / "bt.sqlite3")
    simulator = BacktestFuturesSimulator(
        accounting_store=store,
        maker_fee_rate=Decimal("0.0002"),
        taker_fee_rate=Decimal("0.00055"),
        spread_bps=Decimal("1"),
        slippage_bps=Decimal("1"),
    )
    decision_close = datetime(2026, 9, 5, 13, 10, tzinfo=UTC)
    next_candle = _candle(11, open_price=Decimal("99"), close_price=Decimal("100"))

    trade_id = simulator.simulate_closed_trade(backtest_run_id="btr-unit", intent=_intent(created_at=decision_close), next_candle=next_candle)
    fills = store.list_fills(trade_id)
    closed = store.list_closed_trades(limit=1)[0]

    assert fills[0].occurred_at == next_candle.open_time.isoformat()
    assert datetime.fromisoformat(fills[0].occurred_at) >= decision_close
    assert closed["evidence_source"] == BACKTEST_EVIDENCE_SOURCE
    assert closed["simulation_model_version"] == BACKTEST_SIMULATOR_VERSION
    assert Decimal(closed["entry_vwap"]) > next_candle.open
    assert Decimal(closed["exit_vwap"]) < next_candle.close


def test_backtest_simulator_blocks_funding_crossing_without_history(tmp_path):
    simulator = BacktestFuturesSimulator(
        accounting_store=FuturesAccountingStore(tmp_path / "bt.sqlite3"),
        maker_fee_rate=Decimal("0.0002"),
        taker_fee_rate=Decimal("0.00055"),
        spread_bps=Decimal("1"),
        slippage_bps=Decimal("1"),
    )
    crossing = HistoricalCandle(
        "BTCUSDT", "linear", "1m", datetime(2026, 9, 5, 7, 59, tzinfo=UTC), datetime(2026, 9, 5, 8, 0, tzinfo=UTC),
        Decimal("100"), Decimal("100"), Decimal("100"), Decimal("100"), Decimal("1"), Decimal("100"), True
    )

    with pytest.raises(BacktestSimulationError, match="funding"):
        simulator.simulate_closed_trade(backtest_run_id="btr-unit", intent=_intent(created_at=crossing.open_time), next_candle=crossing)


def test_backtest_reuses_runtime_components_pins_versions_and_is_reproducible(tmp_path):
    db = tmp_path / "bt.sqlite3"
    _bootstrap(db)
    config = _config(db)
    candles = _trade_candles()
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)

    first = run_backtest(config=config, db_path=db, trigger_set_id="triggertrade-futures-core", trigger_set_version="v1", plan=plan, candles=candles, instrument=_instrument())
    second = run_backtest(config=config, db_path=db, trigger_set_id="triggertrade-futures-core", trigger_set_version="v1", plan=plan, candles=candles, instrument=_instrument())

    assert first == second
    assert first.closed_trades >= 1
    rows = FuturesAccountingStore(db).list_closed_trades(limit=20)
    assert {row["evidence_source"] for row in rows} == {BACKTEST_EVIDENCE_SOURCE}
    run_row = __import__("triggertrade.backtest.store", fromlist=["BacktestStore"]).BacktestStore(db).get_run(first.backtest_run_id)
    assert run_row is not None
    payload = run_row["payload"]
    assert "STR-FUT-001@0.1.0" in run_row["payload"]
    assert "CTX-REGIME@0.1.0" in run_row["payload"]
    assert BACKTEST_SIMULATOR_VERSION in run_row["payload"]
    assert "\"warmup_candles\": \"60\"" in payload
    assert "\"demo_expected_gross_move\": \"1\"" in payload
    assert "\"instrument_quantity_step\": \"0.001\"" in payload
    assert "\"instrument_min_leverage\": \"1\"" in payload
    assert "\"instrument_leverage_step\": \"0.01\"" in payload
    assert "\"instrument_contract_size\": \"\"" in payload


def test_backtest_resolves_old_set_to_exact_trigger_version_after_new_version_exists(tmp_path):
    db = tmp_path / "bt.sqlite3"
    _bootstrap(db)
    store = TriggerSetStore(db)
    existing = store.get_rule("TRG-001", "0.2.0")
    next_version = existing.__class__(
        **{
            **existing.__dict__,
            "version": "0.3.0",
            "condition": "future example price trigger version",
            "definition": {**existing.definition, "parameter_snapshot": {"threshold_pct": "future-example"}},
            "semantic_hash": None,
        }
    )
    store.save_rule(next_version)
    config = _config(db)
    candles = _trade_candles()
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)

    run_backtest(config=config, db_path=db, trigger_set_id="triggertrade-futures-core", trigger_set_version="v1", plan=plan, candles=candles, instrument=_instrument())

    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT trigger_rule_version
            FROM trigger_evaluations
            WHERE trigger_rule_id = 'TRG-001'
            """
        ).fetchall()
    assert {row[0] for row in rows} == {"0.2.0"}


def test_backtest_never_adds_short_or_private_order_path(tmp_path):
    db = tmp_path / "bt.sqlite3"
    _bootstrap(db)
    config = _config(db)
    candles = _trade_candles()
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)

    result = run_backtest(config=config, db_path=db, trigger_set_id="triggertrade-futures-core", trigger_set_version="v1", plan=plan, candles=candles, instrument=_instrument())

    assert result.short_trades == 0
    assert FuturesExecutionStore(db).unresolved() == ()
    assert RuntimeStore(db).latest_market_regime("BTCUSDT", "1m") is None


def test_candidate_and_active_backtests_can_be_compared_only_like_for_like(tmp_path):
    db = tmp_path / "bt.sqlite3"
    _bootstrap(db)
    config = _config(db)
    candles = _trade_candles(volume_spike=True)
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)
    active = run_backtest(config=config, db_path=db, trigger_set_id="triggertrade-futures-core", trigger_set_version="v1", plan=plan, candles=candles, instrument=_instrument())
    candidate = run_backtest(config=config, db_path=db, trigger_set_id="triggertrade-futures-candidate", trigger_set_version="v2-test", plan=plan, candles=candles, instrument=_instrument())

    comparison = compare_backtest_runs(db_path=db, baseline_run_id=active.backtest_run_id, candidate_run_id=candidate.backtest_run_id)

    assert comparison["baseline_set"] == "triggertrade-futures-core@v1"
    assert comparison["candidate_set"] == "triggertrade-futures-candidate@v2-test"
    mapping_store = __import__("triggertrade.backtest.store", fromlist=["BacktestStore"]).BacktestStore(db)
    active_trade_ids = set(mapping_store.list_trade_ids(active.backtest_run_id))
    candidate_trade_ids = set(mapping_store.list_trade_ids(candidate.backtest_run_id))
    assert active_trade_ids
    assert candidate_trade_ids
    assert active_trade_ids.isdisjoint(candidate_trade_ids)


def test_backtest_comparison_rejects_mismatched_assumptions(tmp_path):
    db = tmp_path / "bt.sqlite3"
    _bootstrap(db)
    config = _config(db)
    candles = _trade_candles(volume_spike=True)
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)
    active = run_backtest(config=config, db_path=db, trigger_set_id="triggertrade-futures-core", trigger_set_version="v1", plan=plan, candles=candles, instrument=_instrument())
    candidate = run_backtest(config=config, db_path=db, trigger_set_id="triggertrade-futures-candidate", trigger_set_version="v2-test", plan=plan, candles=candles, instrument=_instrument())
    with sqlite3.connect(db) as conn:
        row = conn.execute("SELECT payload FROM backtest_runs WHERE backtest_run_id = ?", (candidate.backtest_run_id,)).fetchone()
        payload = json.loads(row[0])
        payload["assumptions"]["spread_bps"] = "99"
        conn.execute("UPDATE backtest_runs SET payload = ? WHERE backtest_run_id = ?", (json.dumps(payload, sort_keys=True), candidate.backtest_run_id))

    with pytest.raises(ValueError, match="assumptions"):
        compare_backtest_runs(db_path=db, baseline_run_id=active.backtest_run_id, candidate_run_id=candidate.backtest_run_id)


def test_dashboard_renders_historical_backtest_section_and_detail(tmp_path):
    db = tmp_path / "bt.sqlite3"
    _bootstrap(db)
    config = _config(db)
    candles = _trade_candles()
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)
    result = run_backtest(config=config, db_path=db, trigger_set_id="triggertrade-futures-core", trigger_set_version="v1", plan=plan, candles=candles, instrument=_instrument())

    html = render_dashboard(DashboardReadModel(db), initial_page="research")
    detail = DashboardReadModel(db).get_backtest_detail(result.backtest_run_id)
    detail_html = render_backtest_detail(detail)
    read_model = DashboardReadModel(db)

    assert "Research" in html
    assert "Backtest" in html
    assert "Demo" in html
    assert "Forward Test" not in html
    assert "No-lookahead" in detail_html
    assert "backtest-sim-v1-next-candle" in detail_html
    assert "BYBIT_API_SECRET" not in html + detail_html
    assert read_model.list_futures_closed_trades() == ()
    assert len(read_model.list_closed_trades_by_source(BACKTEST_EVIDENCE_SOURCE)) == result.closed_trades
    assert all(row.closed_trades_observed == "0" for row in read_model.list_test_set_evidence())
    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT signal_id FROM trigger_evaluations").fetchall()
    assert rows
    assert all(row[0].startswith("btsig-") for row in rows)


def test_backtest_enforces_warmup_before_evaluation_start(tmp_path):
    db = tmp_path / "bt.sqlite3"
    _bootstrap(db)
    config = _config(db)
    candles = _trade_candles()
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[10].close_time, candles[-2].close_time, warmup_candles=60)

    with pytest.raises(ValueError, match="warmup"):
        run_backtest(config=config, db_path=db, trigger_set_id="triggertrade-futures-core", trigger_set_version="v1", plan=plan, candles=candles, instrument=_instrument())


def test_research_backtest_can_use_injected_pinned_set_without_local_sqlite_set(tmp_path):
    db = tmp_path / "bt-exact-set.sqlite3"
    config = _config(db)
    candles = _trade_candles(volume_spike=True)[:-1]
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-1].close_time, warmup_candles=60)
    trigger_set = current_futures_active_trigger_set(created_at="2026-09-05T00:00:00+00:00")

    with pytest.raises(BacktestEngineError, match="unknown trigger set version"):
        run_backtest(config=config, db_path=db, trigger_set_id=trigger_set.set_id, trigger_set_version=trigger_set.version, plan=plan, candles=candles, instrument=_instrument())

    result = run_backtest(
        config=config,
        db_path=db,
        trigger_set_id=trigger_set.set_id,
        trigger_set_version=trigger_set.version,
        plan=plan,
        candles=candles,
        instrument=_instrument(),
        trigger_set_store=ExactBacktestTriggerSetResolver(trigger_set),
    )

    assert result.backtest_run_id
    assert result.status is BacktestStatus.COMPLETED


def test_backtest_dispatches_declarative_research_trigger_without_changing_primary_path(tmp_path):
    db = tmp_path / "bt-declarative.sqlite3"
    _bootstrap(db)
    store = TriggerSetStore(db)
    rule = _research_rule()
    store.save_rule(rule)
    base = current_futures_active_trigger_set(created_at="2026-09-05T00:00:00+00:00")
    trigger_set = replace(
        base,
        set_id="research-v1-backtest-set",
        version="v1",
        status=TriggerSetStatus.TESTING,
        rule_versions=base.rule_versions + ((rule.rule_id, rule.version),),
        config_snapshot={
            **dict(base.config_snapshot),
            "declarative_metric_values": {
                "DE": "0.75",
            },
        },
        provenance="unit test declarative research trigger",
    )
    store.create_set(trigger_set)
    config = _config(db)
    candles = _trade_candles()
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)

    result = run_backtest(
        config=config,
        db_path=db,
        trigger_set_id=trigger_set.set_id,
        trigger_set_version=trigger_set.version,
        plan=plan,
        candles=candles,
        instrument=_instrument(),
    )

    assert result.status is BacktestStatus.COMPLETED
    with sqlite3.connect(db) as conn:
        declarative_rows = conn.execute(
            """
            SELECT trigger_rule_id, trigger_rule_version, input_snapshot, signal_type
            FROM trigger_evaluations
            WHERE trigger_rule_id = ?
            """,
            (rule.rule_id,),
        ).fetchall()
        primary_rows = conn.execute(
            """
            SELECT DISTINCT trigger_rule_id, trigger_rule_version
            FROM trigger_evaluations
            WHERE trigger_rule_id = 'TRG-001'
            """
        ).fetchall()
    assert declarative_rows
    assert {tuple(row) for row in primary_rows} == {("TRG-001", "0.2.0")}
    assert {row[1] for row in declarative_rows} == {"1.0.0"}
    assert {json.loads(row[2])["implementation_key"] for row in declarative_rows} == {DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY}
    assert {row[3] for row in declarative_rows} == {"CONFIRMED"}


def _bootstrap(db):
    bootstrap_current_trigger_sets(TriggerSetStore(db))
    FuturesAccountingStore(db)
    FuturesExecutionStore(db)
    RuntimeStore(db)
    TraceStore(db)


def _config(db):
    return load_config(
        {
            "TRIGGERTRADE_MARKET": "linear",
            "TRIGGERTRADE_CATEGORY": "linear",
            "TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO_FUTURES.value,
            "TRIGGERTRADE_ACTIVE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO_FUTURES.value,
            "TRIGGERTRADE_TEST_EXECUTION_VENUE": ExecutionVenue.LOCAL_TEST_SIMULATION.value,
            "TRIGGERTRADE_RUNTIME_DB_PATH": str(db),
            "TRIGGERTRADE_RUNTIME_SYMBOL": "BTCUSDT",
            "TRIGGERTRADE_STALE_AFTER_SECONDS": "120",
            "TRIGGERTRADE_MAX_FUTURES_POSITION_NOTIONAL": "10",
            "TRIGGERTRADE_MINIMUM_NET_EDGE": "0.01",
            "TRIGGERTRADE_DEMO_EXPECTED_GROSS_MOVE": "1",
            "TRIGGERTRADE_FUTURES_SPREAD_COST": "1",
            "TRIGGERTRADE_FUTURES_SLIPPAGE_COST": "1",
        }
    )


def _instrument():
    return FuturesInstrumentMetadata("BTCUSDT", ContractCategory.LINEAR, "LinearPerpetual", "USDT", Decimal("0.001"), Decimal("0.1"), Decimal("0.001"), Decimal("5"), Decimal("100"))


def _intent(*, created_at):
    return FuturesTradeIntent(
        intent_id="intent-backtest-unit",
        symbol="BTCUSDT",
        category=ContractCategory.LINEAR,
        action=PositionAction.OPEN_LONG,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.1"),
        price=Decimal("100"),
        current_position_state=PositionState.FLAT,
        configured_leverage=Decimal("1"),
        strategy_rule_id="STR-FUT-001",
        strategy_rule_version="0.1.0",
        expected_gross_price_move=Decimal("1"),
        created_at=created_at.isoformat(),
        lane=BACKTEST_EVIDENCE_SOURCE,
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
        regime_state="DOWNTREND",
    )


def _candles(count: int):
    return tuple(_candle(index) for index in range(count))


class _FakeHistoricalClient:
    def __init__(self):
        self.calls = []

    def linear_historical_candles(self, *, symbol, interval, start_ms, end_ms, limit):
        self.calls.append(
            {
                "symbol": symbol,
                "interval": interval,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "limit": limit,
            }
        )
        rows = []
        current = start_ms
        while current <= end_ms:
            rows.append([str(current), "100", "101", "99", "100", "1", "100"])
            current += 60_000
        return BybitResponse(0, "OK", {"list": rows})


def _trade_candles(*, volume_spike: bool = False):
    rows = []
    start = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    for index in range(75):
        close = Decimal("120") - Decimal(index) * Decimal("0.2")
        if index == 65:
            close = Decimal("95")
        volume = Decimal("1")
        if volume_spike and index == 65:
            volume = Decimal("5")
        rows.append(_candle(index, start=start, close_price=close, volume=volume))
    return tuple(rows)


def _candle(index: int, *, start=None, open_price=None, close_price=None, volume=Decimal("1")):
    base = start or datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    open_time = base + timedelta(minutes=index)
    close = close_price or Decimal("100")
    open_value = open_price or close
    return HistoricalCandle("BTCUSDT", "linear", "1m", open_time, open_time + timedelta(minutes=1), open_value, max(open_value, close), min(open_value, close), close, volume, close * volume, True)


def _research_rule() -> RuleDefinition:
    return RuleDefinition(
        rule_id="TR-R-UNIT",
        version="1.0.0",
        name="Unit Research Predicate",
        status=RuleStatus.TESTING,
        asset_scope="BTCUSDT",
        rule_type=RuleType.TRIGGER,
        condition="DE >= 0.30",
        definition={
            "implementation_key": DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY,
            "schema": DECLARATIVE_METRIC_PREDICATE_SCHEMA,
            "metric_ref": "DE",
            "operator": "GTE",
            "threshold": "0.30",
            "output_states": ["TRUE", "FALSE", "UNAVAILABLE"],
        },
        created_at="2026-09-27T00:00:00+00:00",
        provenance="unit test",
    )
