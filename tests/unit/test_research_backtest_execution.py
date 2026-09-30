from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

from triggertrade.backtest import BacktestResult, BacktestStatus, ExactBacktestTriggerSetResolver
from triggertrade.backtest.data import HistoricalDataError
from triggertrade.backtest.engine import BacktestEngineError
from triggertrade.instruments import CatalogError, FuturesInstrument
import pytest

from triggertrade.persistence import ResearchBacktestRunRecord, ResearchBacktestStatus
from triggertrade.research_pins import research_run_pin_payload
from triggertrade.research_v1_execution import RESEARCH_V1_ALLOCATION_BY_SYMBOL, ResearchV1SharedPortfolioState
from triggertrade.services.research_backtest_execution import (
    CanonicalResearchBacktestExecutionExecutor,
    _backtest_unavailable_reason,
    _load_research_v1_last_traded_price_response,
    _research_v1_approved_position_to_order_spec,
    _run_research_v1_certified_position_backtest,
)
from triggertrade.services.runtime import _research_backtest_instrument
from tests.unit.test_backtest_replay import _config, _instrument, _trade_candles
from tests.unit.test_position_opportunity_b7a import (
    PositionOpportunityHandler,
    command_for,
    handoff,
    rules_version as _position_rules_version,
)
from tests.unit.test_research_demo_execution import _research_record, _rules_version, _trigger_set
from tests.unit.test_research_v1_historical_handoff import (
    _instrument as _catalog_instrument,
    _matched_btc_fact_candles,
    _research_set,
    _rules_for,
    _last_traded_price_response,
)


def test_canonical_research_backtest_executor_loads_exact_config_fetches_history_and_persists_result(tmp_path, monkeypatch):
    record = _backtest_record()
    candles = _trade_candles(volume_spike=True)[:-1]
    source = _FakeHistoricalSource(candles)
    captured_engine = {}

    def fake_run_backtest(**kwargs):
        captured_engine.update(kwargs)
        return BacktestResult(
            "engine-worker-1",
            BacktestStatus.COMPLETED,
            len(kwargs["candles"]),
            1,
            1,
            1,
            1,
            0,
            0,
            0,
            Decimal("3"),
            Decimal("3"),
            Decimal("2"),
            Decimal("0"),
            Decimal("0.01"),
            Decimal("0"),
            1,
            0,
            {},
        )

    store = _install_executor_fakes(monkeypatch, record)
    monkeypatch.setattr("triggertrade.services.research_backtest_execution.run_backtest", fake_run_backtest)
    executor = CanonicalResearchBacktestExecutionExecutor(
        config=_config(tmp_path / "runtime.sqlite3"),
        db_path=tmp_path / "runtime.sqlite3",
        factory=object(),
        historical_source=source,
        instrument_provider=lambda symbol: _instrument(),
    )

    updated = executor.start_research_backtest(record)

    assert source.calls == [
        {
            "symbol": "BTCUSDT",
            "category": "linear",
            "timeframe": "1m",
            "start": datetime(2026, 9, 5, 13, 0, tzinfo=UTC),
            "end": datetime(2026, 9, 5, 14, 14, tzinfo=UTC),
            "use_cache": True,
        }
    ]
    assert captured_engine["trigger_set_id"] == "triggertrade-futures-core"
    assert captured_engine["trigger_set_version"] == "v1"
    assert isinstance(captured_engine["trigger_set_store"], ExactBacktestTriggerSetResolver)
    assert captured_engine["trigger_set_store"].get_set("triggertrade-futures-core", "v1") == _trigger_set()
    assert captured_engine["plan"].symbol == "BTCUSDT"
    assert captured_engine["plan"].warmup_candles == 60
    assert captured_engine["candles"] == candles
    assert updated.status is ResearchBacktestStatus.COMPLETED
    assert updated.engine_run_id == "engine-worker-1"
    assert updated.metrics["closed_trades"] == 1
    assert updated.unavailable_reason is None
    assert store.updates[-1]["run_id"] == record.run_id


def test_canonical_research_backtest_executor_empty_history_fails_closed(tmp_path, monkeypatch):
    record = _backtest_record(run_id="rbt-empty")
    store = _install_executor_fakes(monkeypatch, record)
    executor = CanonicalResearchBacktestExecutionExecutor(
        config=_config(tmp_path / "runtime.sqlite3"),
        db_path=tmp_path / "runtime.sqlite3",
        factory=object(),
        historical_source=_FakeHistoricalSource(()),
        instrument_provider=lambda symbol: _instrument(),
    )

    updated = executor.start_research_backtest(record)

    assert updated.status is ResearchBacktestStatus.FAILED
    assert updated.engine_run_id is None
    assert updated.unavailable_reason == "backend_historical_replay_inputs_unavailable"
    assert store.updates[-1]["metrics"] == {}


def test_canonical_research_backtest_executor_forbidden_history_maps_geo_block(tmp_path, monkeypatch):
    record = _backtest_record(run_id="rbt-403")
    _install_executor_fakes(monkeypatch, record)
    executor = CanonicalResearchBacktestExecutionExecutor(
        config=_config(tmp_path / "runtime.sqlite3"),
        db_path=tmp_path / "runtime.sqlite3",
        factory=object(),
        historical_source=_ForbiddenHistoricalSource(),
        instrument_provider=lambda symbol: _instrument(),
    )

    updated = executor.start_research_backtest(record)

    assert updated.status is ResearchBacktestStatus.FAILED
    assert updated.engine_run_id is None
    assert updated.unavailable_reason == "historical_source_geo_blocked"


def test_canonical_research_backtest_executor_does_not_mutate_existing_failed_runs(tmp_path, monkeypatch):
    current = _backtest_record(run_id="rbt-current")
    historical_failed = _backtest_record(run_id="rbt-old-failed", status=ResearchBacktestStatus.FAILED)
    store = _install_executor_fakes(monkeypatch, current, existing=(historical_failed,))
    executor = CanonicalResearchBacktestExecutionExecutor(
        config=_config(tmp_path / "runtime.sqlite3"),
        db_path=tmp_path / "runtime.sqlite3",
        factory=object(),
        historical_source=_FakeHistoricalSource(()),
        instrument_provider=lambda symbol: _instrument(),
    )

    executor.start_research_backtest(current)

    assert historical_failed.run_id not in {update["run_id"] for update in store.updates}
    assert store.records[historical_failed.run_id] == historical_failed


def test_canonical_research_backtest_executor_mismatched_authoritative_set_fails_closed(tmp_path, monkeypatch):
    record = _backtest_record(run_id="rbt-mismatch")
    mismatched = replace(_trigger_set(), set_id="triggertrade-futures-candidate")
    store = _install_executor_fakes(monkeypatch, record, trigger_set=mismatched)
    executor = CanonicalResearchBacktestExecutionExecutor(
        config=_config(tmp_path / "runtime.sqlite3"),
        db_path=tmp_path / "runtime.sqlite3",
        factory=object(),
        historical_source=_FakeHistoricalSource(_trade_candles()),
        instrument_provider=lambda symbol: _instrument(),
    )

    updated = executor.start_research_backtest(record)

    assert updated.status is ResearchBacktestStatus.FAILED
    assert updated.engine_run_id is None
    assert updated.unavailable_reason == "research_configuration_unavailable"
    assert store.updates[-1]["metrics"] == {}


def test_canonical_research_backtest_executor_engine_errors_are_not_historical_fetch_failures(tmp_path, monkeypatch):
    record = _backtest_record(run_id="rbt-engine-error")
    store = _install_executor_fakes(monkeypatch, record)

    def failing_run_backtest(**kwargs):
        raise BacktestEngineError("unknown trigger set version")

    monkeypatch.setattr("triggertrade.services.research_backtest_execution.run_backtest", failing_run_backtest)
    executor = CanonicalResearchBacktestExecutionExecutor(
        config=_config(tmp_path / "runtime.sqlite3"),
        db_path=tmp_path / "runtime.sqlite3",
        factory=object(),
        historical_source=_FakeHistoricalSource(_trade_candles()),
        instrument_provider=lambda symbol: _instrument(),
    )

    updated = executor.start_research_backtest(record)

    assert updated.status is ResearchBacktestStatus.FAILED
    assert updated.engine_run_id is None
    assert updated.unavailable_reason == "research_trigger_set_unavailable"
    assert updated.unavailable_reason != "historical_fetch_failed"
    assert store.updates[-1]["metrics"] == {}


def test_research_v1_backtest_fails_closed_without_factual_last_traded_price_handoff_input():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _matched_btc_fact_candles()

    with pytest.raises(HistoricalDataError, match="LAST_TRADED_PRICE_UNAVAILABLE"):
        _run_research_v1_certified_position_backtest(
            trigger_set=replace(_trigger_set(), set_id=research_set.set_id, version=research_set.set_version),
            research_set=research_set,
            trigger_rules=_rules_for(research_set),
            rules=_position_rules_version(metadata={"stop_loss_mode": "DYNAMIC"}, minimum_risk_reward_enabled=False),
            plan=_backtest_plan(research_end=candles[-1].close_time),
            candles=candles,
            instrument=replace(_catalog_instrument("BTCUSDT"), updated_at="2026-08-01T00:00:00+00:00"),
            portfolio_state=object(),
        )


def test_research_v1_backtest_loads_canonical_last_traded_price_for_set_decision_slot():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _matched_btc_fact_candles()
    rules = _position_rules_version(metadata={"stop_loss_mode": "DYNAMIC"}, minimum_risk_reward_enabled=False)
    captured = {}

    def load_last_traded_price(symbol, as_of):
        captured["symbol"] = symbol
        captured["as_of"] = as_of
        return _last_traded_price_response(symbol, as_of, "1")

    result = _run_research_v1_certified_position_backtest(
        trigger_set=replace(_trigger_set(), set_id=research_set.set_id, version=research_set.set_version),
        research_set=research_set,
        trigger_rules=_rules_for(research_set),
        rules=rules,
        plan=_backtest_plan(research_end=candles[-1].close_time),
        candles=candles,
        instrument=replace(_catalog_instrument("BTCUSDT"), updated_at="2026-08-01T00:00:00+00:00"),
        portfolio_state=object(),
        last_traded_price_response_loader=load_last_traded_price,
    )

    evidence = result.research_v1_certified_position_evidence
    handoff = evidence["position_state"]["source_contracts"]["market_handoff"]["market_handoff"]

    assert captured == {"symbol": "BTCUSDT", "as_of": candles[-1].close_time}
    assert handoff["decision_cycle_id"] == evidence["decision_cycle_id"]
    assert handoff["set_result_id"] == evidence["set_result_id"]
    assert handoff["snapshot"]["set_match_reference_price"] == "1"


def test_research_v1_last_traded_price_store_loader_uses_market_data_fact_store(monkeypatch):
    response = _last_traded_price_response("BTCUSDT", datetime(2026, 8, 17, 0, 15, tzinfo=UTC), "1")
    captured = {}

    class FakeUnitOfWork:
        connection = object()

        def __init__(self, factory):
            captured["factory"] = factory

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeMarketDataFactStore:
        def __init__(self, connection):
            captured["connection"] = connection

        def latest_last_traded_price_response_as_of(self, *, symbol, as_of):
            captured["symbol"] = symbol
            captured["as_of"] = as_of
            return response

    monkeypatch.setattr("triggertrade.services.research_backtest_execution.PostgresUnitOfWork", FakeUnitOfWork)
    monkeypatch.setattr("triggertrade.services.research_backtest_execution.MarketDataFactStore", FakeMarketDataFactStore)

    selected = _load_research_v1_last_traded_price_response(
        object(),
        symbol="BTCUSDT",
        as_of=datetime(2026, 8, 17, 0, 15, tzinfo=UTC),
    )

    assert selected == response
    assert captured["symbol"] == "BTCUSDT"
    assert captured["as_of"] == datetime(2026, 8, 17, 0, 15, tzinfo=UTC)


def test_research_v1_historical_fail_closed_reason_is_preserved():
    reason = _backtest_unavailable_reason(HistoricalDataError("research_v1_historical_market_handoff_unavailable"))

    assert reason == "research_v1_historical_market_handoff_unavailable"
    assert reason != "historical_fetch_failed"



def test_research_v1_backtest_rejects_instrument_metadata_from_after_decision_slot():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _matched_btc_fact_candles()
    rules = _position_rules_version(
        metadata={"stop_loss_mode": "DYNAMIC"},
        minimum_risk_reward_enabled=False,
    )
    future_instrument = replace(
        _catalog_instrument("BTCUSDT"),
        updated_at="2099-01-01T00:00:00+00:00",
    )

    with pytest.raises(
        HistoricalDataError,
        match="research_v1_historical_instrument_metadata_snapshot_unavailable",
    ):
        _run_research_v1_certified_position_backtest(
            trigger_set=replace(
                _trigger_set(),
                set_id=research_set.set_id,
                version=research_set.set_version,
            ),
            research_set=research_set,
            trigger_rules=_rules_for(research_set),
            rules=rules,
            plan=_backtest_plan(research_end=candles[-1].close_time),
            candles=candles,
            instrument=future_instrument,
            portfolio_state=object(),
            last_traded_price_responses=(
                _last_traded_price_response(
                    "BTCUSDT",
                    candles[-1].close_time,
                    "1",
                ),
            ),
        )


def test_research_v1_backtest_wires_factual_handoff_to_canonical_position_decision():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _matched_btc_fact_candles()
    rules = _position_rules_version(metadata={"stop_loss_mode": "DYNAMIC"}, minimum_risk_reward_enabled=False)

    result = _run_research_v1_certified_position_backtest(
        trigger_set=replace(_trigger_set(), set_id=research_set.set_id, version=research_set.set_version),
        research_set=research_set,
        trigger_rules=_rules_for(research_set),
        rules=rules,
        plan=_backtest_plan(research_end=candles[-1].close_time),
        candles=candles,
        instrument=replace(_catalog_instrument("BTCUSDT"), updated_at="2026-08-01T00:00:00+00:00"),
        portfolio_state=object(),
        last_traded_price_responses=(_last_traded_price_response("BTCUSDT", candles[-1].close_time, "1"),),
    )

    evidence = result.research_v1_certified_position_evidence
    state = evidence["position_state"]
    handoff = state["source_contracts"]["market_handoff"]["market_handoff"]
    evaluation = state["evaluation"]

    assert evidence["research_set_id"] == research_set.set_id
    assert evidence["research_set_version"] == research_set.set_version
    assert evidence["rules_version_id"] == rules.rules_version_id
    assert evidence["set_direction"] == "LONG"
    assert handoff["snapshot"]["direction"] == "LONG"
    assert evaluation["direction"] == handoff["snapshot"]["direction"]
    assert state["decision"]["decision"] in {"APPROVE", "REJECT"}
    assert state["decision"]["construction_gates"] == "NOT_YET_EVALUATED"
    assert evidence["portfolio_boundary"] == "CAPITAL_AND_LIMITS_NOT_EVALUATED"
    assert evidence["order_spec_status"] == "NOT_EVALUATED_REQUIRES_PORTFOLIO_GRANT"
    assert result.trades == 0
    assert result.closed_trades == 0


def test_research_v1_factual_repeating_atr_distance_returns_canonical_reject():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _matched_btc_fact_candles()
    rules = _position_rules_version(metadata={"stop_loss_mode": "DYNAMIC"}, minimum_risk_reward_enabled=False)

    result = _run_research_v1_certified_position_backtest(
        trigger_set=replace(_trigger_set(), set_id=research_set.set_id, version=research_set.set_version),
        research_set=research_set,
        trigger_rules=_rules_for(research_set),
        rules=rules,
        plan=_backtest_plan(research_end=candles[-1].close_time),
        candles=candles,
        instrument=replace(_catalog_instrument("BTCUSDT"), updated_at="2026-08-01T00:00:00+00:00"),
        portfolio_state=object(),
        last_traded_price_responses=(_last_traded_price_response("BTCUSDT", candles[-1].close_time, "125"),),
    )

    evidence = result.research_v1_certified_position_evidence
    evaluation = evidence["position_state"]["evaluation"]

    assert evaluation["decision"] == "REJECT"
    assert evaluation["reason_code"] == "ENTRY_ATR_DISTANCE_OUT_OF_RANGE"
    assert evaluation["entry"]["reason_code"] == "ATR_DISTANCE_OUT_OF_RANGE"
    assert evaluation["entry"]["traversal"][0]["distance_atr"] == "2.142223132297475895"
    assert evidence["portfolio_boundary"] == "CAPITAL_AND_LIMITS_NOT_EVALUATED"
    assert evidence["order_spec_status"] == "NOT_EVALUATED_REQUIRES_PORTFOLIO_GRANT"
    assert "portfolio_grant_status" not in evidence
    assert result.research_v1_portfolio_events == ()


def test_research_v1_approved_position_flows_through_portfolio_grant_and_constructs_order_spec():
    rules = _research_v1_position_rules()
    position = PositionOpportunityHandler().evaluate(command_for(handoff=handoff(), rules=rules))
    portfolio = ResearchV1SharedPortfolioState(
        total_capital=Decimal("1000"),
        max_capital_in_positions_pct=Decimal("0.60"),
        allocation_by_symbol=RESEARCH_V1_ALLOCATION_BY_SYMBOL,
        max_open_positions=6,
        max_positions_per_coin=2,
    )

    evidence, events = _research_v1_approved_position_to_order_spec(
        position_state=position.to_state_payload(),
        rules=rules,
        instrument=replace(_catalog_instrument("BTCUSDT"), updated_at="2026-08-01T00:00:00+00:00"),
        portfolio_state=portfolio,
        as_of="2026-09-15T00:00:00Z",
    )

    assert position.to_state_payload()["position_opportunity_state"]["decision"]["decision"] == "APPROVE"
    assert evidence["portfolio_boundary"] == "CAPITAL_AND_LIMITS_EVALUATED"
    assert evidence["portfolio_grant_status"] == "ALLOWED"
    assert evidence["capital_grant"]["capital_and_limits"]["requested_capital_per_tranche"] == "50"
    assert evidence["construction_status"] == "CONSTRUCTED"
    assert evidence["order_spec_status"] == "CONSTRUCTED"
    assert evidence["order_spec"]["order_spec"]["symbol"] == "BTCUSDT"
    assert evidence["order_spec"]["order_spec"]["direction"] == "LONG"
    assert evidence["order_spec"]["order_spec"]["economics"]["actual_committed_capital"] == events[0]["actual_committed_capital"]
    assert events == (
        {
            "action": "RESERVE",
            "symbol": "BTCUSDT",
            "actual_committed_capital": evidence["order_spec"]["order_spec"]["economics"]["actual_committed_capital"],
            "canonical_source": "order_spec.economics.actual_committed_capital",
            "position_decision_id": evidence["order_spec"]["order_spec"]["position_decision_id"],
            "construction_result_id": evidence["order_spec"]["order_spec"]["construction_result_id"],
            "order_spec_id": evidence["order_spec"]["order_spec"]["order_spec_id"],
            "order_spec_digest": evidence["position_construction"]["construction_result"]["position_construction_result"][
                "order_spec_digest"
            ],
        },
    )


def test_research_v1_portfolio_grant_blocks_without_order_spec_when_coin_cap_is_full():
    rules = _research_v1_position_rules()
    position = PositionOpportunityHandler().evaluate(command_for(handoff=handoff(), rules=rules))
    portfolio = ResearchV1SharedPortfolioState(
        total_capital=Decimal("1000"),
        max_capital_in_positions_pct=Decimal("0.60"),
        allocation_by_symbol=RESEARCH_V1_ALLOCATION_BY_SYMBOL,
        max_open_positions=6,
        max_positions_per_coin=2,
        committed_by_symbol={"BTCUSDT": Decimal("100")},
        open_positions_by_symbol={"BTCUSDT": 1},
    )

    evidence, events = _research_v1_approved_position_to_order_spec(
        position_state=position.to_state_payload(),
        rules=rules,
        instrument=replace(_catalog_instrument("BTCUSDT"), updated_at="2026-08-01T00:00:00+00:00"),
        portfolio_state=portfolio,
        as_of="2026-09-15T00:00:00Z",
    )

    assert evidence["portfolio_grant_status"] == "BLOCKED"
    assert evidence["portfolio_grant_reason"] == "COIN_ALLOCATION_REACHED"
    assert evidence["capital_grant"] is None
    assert evidence["construction_status"] == "NOT_EVALUATED"
    assert evidence["order_spec_status"] == "NOT_EVALUATED_REQUIRES_ALLOWED_CAPITAL_GRANT"
    assert events == ()


def test_research_v1_position_evidence_changes_with_handoff_and_rules_identity():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _matched_btc_fact_candles()
    rules = _position_rules_version(metadata={"stop_loss_mode": "DYNAMIC"}, minimum_risk_reward_enabled=False)
    kwargs = dict(
        trigger_set=replace(_trigger_set(), set_id=research_set.set_id, version=research_set.set_version),
        research_set=research_set,
        trigger_rules=_rules_for(research_set),
        rules=rules,
        plan=_backtest_plan(research_end=candles[-1].close_time),
        candles=candles,
        instrument=replace(_catalog_instrument("BTCUSDT"), updated_at="2026-08-01T00:00:00+00:00"),
        portfolio_state=object(),
    )

    first = _run_research_v1_certified_position_backtest(
        **kwargs,
        last_traded_price_responses=(_last_traded_price_response("BTCUSDT", candles[-1].close_time, "1"),),
    )
    changed_handoff = _run_research_v1_certified_position_backtest(
        **kwargs,
        last_traded_price_responses=(_last_traded_price_response("BTCUSDT", candles[-1].close_time, "2"),),
    )
    changed_rules = _run_research_v1_certified_position_backtest(
        **{**kwargs, "rules": replace(rules, rules_version_id="rules-v2", version="v2")},
        last_traded_price_responses=(_last_traded_price_response("BTCUSDT", candles[-1].close_time, "1"),),
    )

    assert first.research_v1_certified_position_evidence["evidence_digest"] != changed_handoff.research_v1_certified_position_evidence["evidence_digest"]
    assert first.research_v1_certified_position_evidence["evidence_digest"] != changed_rules.research_v1_certified_position_evidence["evidence_digest"]


def _research_v1_position_rules():
    rules = _position_rules_version(minimum_risk_reward_enabled=False)
    return replace(
        rules,
        draft=replace(
            rules.draft,
            max_open_positions=6,
            max_positions_per_coin=2,
        ),
    )


def test_research_backtest_runtime_provider_returns_factual_catalog_instrument():
    instrument = _research_backtest_instrument(_FakeInstrumentClient(), "BTCUSDT")
    repeated = _research_backtest_instrument(_FakeInstrumentClient(), "BTCUSDT")

    assert isinstance(instrument, FuturesInstrument)
    assert instrument.symbol == "BTCUSDT"
    assert instrument.source == "bybit_public_v5_instruments_info_linear"
    assert instrument.catalog_hash
    assert instrument.updated_at == "2026-09-07T12:00:00+00:00"
    assert repeated.updated_at == instrument.updated_at
    assert repeated.catalog_hash == instrument.catalog_hash


def test_research_backtest_runtime_provider_fails_without_factual_metadata_time():
    with pytest.raises(CatalogError, match="source timestamp unavailable"):
        _research_backtest_instrument(_FakeInstrumentClient(time=None), "BTCUSDT")


class _FakeHistoricalSource:
    def __init__(self, candles):
        self.candles = tuple(candles)
        self.calls = []

    def load(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(candles=self.candles)


class _ForbiddenHistoricalSource:
    def load(self, **kwargs):
        raise RuntimeError("Bybit API HTTP error: 403 Forbidden")


class _FakeInstrumentClient:
    def __init__(self, *, time="1788782400000"):
        self.time = time

    def linear_instrument_metadata(self, symbol):
        return SimpleNamespace(
            time=self.time,
            result={
                "list": [
                    {
                        "symbol": symbol,
                        "baseCoin": symbol.removesuffix("USDT"),
                        "quoteCoin": "USDT",
                        "settleCoin": "USDT",
                        "contractType": "LinearPerpetual",
                        "status": "Trading",
                        "priceFilter": {"tickSize": "0.10", "priceScale": "2"},
                        "lotSizeFilter": {
                            "qtyStep": "0.001",
                            "minOrderQty": "0.001",
                            "maxOrderQty": "100",
                            "minNotionalValue": "5",
                            "maxMktOrderQty": "50",
                        },
                        "leverageFilter": {"minLeverage": "1", "maxLeverage": "100", "leverageStep": "0.01"},
                        "launchTime": "1700000000000",
                        "deliveryTime": "0",
                    }
                ]
            }
        )


class _FakeRunStore:
    active = None

    def __init__(self, connection):
        pass

    def update_backtest_run(self, **kwargs):
        self.updates.append(kwargs)
        record = self.records[kwargs["run_id"]]
        updated = replace(
            record,
            status=kwargs["status"],
            engine_run_id=kwargs.get("engine_run_id"),
            metrics=kwargs.get("metrics") or {},
            unavailable_reason=kwargs.get("unavailable_reason"),
            updated_at=kwargs.get("updated_at") or record.updated_at,
        )
        self.records[updated.run_id] = updated
        return updated


def _install_executor_fakes(monkeypatch, record, *, existing=(), research=None, trigger_set=None):
    class FakeUnitOfWork:
        connection = object()

        def __init__(self, factory):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeRegistry:
        def __init__(self, connection):
            pass

        def get_research(self, research_id):
            assert research_id == record.research_id
            return research or _research_record()

        def get_research_demo_configuration(self, *, research_id, set_id, set_version, rules_version_id):
            assert (research_id, set_id, set_version, rules_version_id) == (
                record.research_id,
                "triggertrade-futures-core",
                "v1",
                "rules-v1",
            )
            return SimpleNamespace(research=research or _research_record(), trigger_set=trigger_set or _trigger_set(), rules=_rules_version())

    store = object.__new__(_FakeRunStore)
    store.records = {item.run_id: item for item in (record, *existing)}
    store.updates = []
    _FakeRunStore.active = store

    def fake_store_factory(connection):
        return store

    monkeypatch.setattr("triggertrade.services.research_backtest_execution.PostgresUnitOfWork", FakeUnitOfWork)
    monkeypatch.setattr("triggertrade.services.research_backtest_execution.PostgresResearchConfigurationRegistry", FakeRegistry)
    monkeypatch.setattr("triggertrade.services.research_backtest_execution.PostgresResearchRunStore", fake_store_factory)
    return store


def _backtest_record(*, run_id="rbt-worker-1", status=ResearchBacktestStatus.RUNNING):
    research = _research_record()
    plan = {
        "symbol": "BTCUSDT",
        "category": "linear",
        "timeframe": "1m",
        "research_start": "2026-09-05T14:01:00+00:00",
        "research_end": "2026-09-05T14:14:00+00:00",
        "validation_start": None,
        "validation_end": None,
        "warmup_candles": 60,
    }
    pin_payload = research_run_pin_payload(
        research_pin_digest_value=research.pin_digest,
        run_kind="BACKTEST",
        run_inputs={"plan": plan, "historical_source": "bybit-demo-public-linear-kline-v1"},
    )
    return ResearchBacktestRunRecord(
        research_id=research.research_id,
        run_id=run_id,
        created_at="2026-09-05T14:15:00+00:00",
        updated_at="2026-09-05T14:15:00+00:00",
        status=status,
        period_start=plan["research_start"],
        period_end=plan["research_end"],
        timeframe="1m",
        engine_run_id=None,
        selected_for_use=False,
        metrics={},
        unavailable_reason="old_failure" if status is ResearchBacktestStatus.FAILED else None,
        pin_payload=pin_payload,
        pin_digest="pin-digest",
    )


def _backtest_plan(*, research_end=None):
    from triggertrade.backtest import BacktestPlan

    end = research_end or datetime(2026, 9, 5, 14, 14, tzinfo=UTC)
    return BacktestPlan(
        "BTCUSDT",
        "linear",
        "1m",
        end,
        end,
    )
