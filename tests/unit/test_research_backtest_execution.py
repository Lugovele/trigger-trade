from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

from triggertrade.backtest import BacktestResult, BacktestStatus, ExactBacktestTriggerSetResolver
from triggertrade.backtest.engine import BacktestEngineError
from triggertrade.market_data import ContractCategory, FuturesInstrumentMetadata
from triggertrade.persistence import ResearchBacktestRunRecord, ResearchBacktestStatus
from triggertrade.research_v1_execution import RESEARCH_V1_ALLOCATION_BY_SYMBOL, ResearchV1SharedPortfolioState
from triggertrade.research_pins import research_run_pin_payload
from triggertrade.rules.trading import StopLossMode, TakeProfitMode
from triggertrade.services.research_backtest_execution import (
    CanonicalResearchBacktestExecutionExecutor,
    _run_research_v1_certified_position_backtest,
)
from tests.unit.test_backtest_replay import _config, _instrument, _trade_candles
from tests.unit.test_research_demo_execution import _research_record, _rules_version, _trigger_set


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


def test_research_v1_certified_position_backtest_uses_dynamic_tp_stop_and_construction():
    rules = replace(
        _rules_version(),
        rules_version_id="TRV-R-POS-001-PR-201",
        draft=replace(
            _rules_version().draft,
            take_profit_mode=TakeProfitMode.DYNAMIC,
            stop_loss_mode=StopLossMode.DYNAMIC,
            stop_loss_pct=Decimal("0.20"),
            minimum_risk_reward=Decimal("1"),
            minimum_tranche_capital=Decimal("10"),
            max_capital_in_positions_pct=Decimal("0.60"),
            max_open_positions_enabled=True,
            max_open_positions=6,
            max_positions_per_coin_enabled=True,
            max_positions_per_coin=2,
        ),
    )

    result = _run_research_v1_certified_position_backtest(
        trigger_set=_trigger_set(),
        rules=rules,
        plan=_backtest_plan(),
        candles=_trade_candles(volume_spike=True),
        instrument=_instrument_with_max_order_qty(),
        portfolio_state=_research_v1_portfolio(),
    )

    evidence = result.research_v1_certified_position_evidence
    evaluation = evidence["position_opportunity"]["position_opportunity_state"]["evaluation"]
    construction = evidence["position_construction"]["position_construction_evaluation"]
    order_spec = evidence["order_spec"]["order_spec"]

    assert evidence["market_handoff"]["market_handoff"]["snapshot"]["direction"] == "LONG"
    assert evaluation["entry"]["formula_id"] == "F-008"
    assert evaluation["stop"]["formula_id"] in {"F-006", "F-007", "F-009"}
    assert evaluation["take_profit"]["formula_id"] == "F-010"
    assert evaluation["take_profit"]["status"] == "AVAILABLE"
    assert "fixed" not in str(evaluation["take_profit"]).lower()
    assert construction["status"] == "CONSTRUCTED"
    assert order_spec["take_profit"]["mode"] == "DYNAMIC"
    assert order_spec["stop_loss"]["mode"] == "DYNAMIC"
    assert result.trades == 1
    assert tuple(event["action"] for event in result.research_v1_portfolio_events) == ("RESERVE", "RELEASE")
    assert result.research_v1_portfolio_events[1]["lifecycle_state"] == "CLOSED"


def test_research_v1_certified_position_backtest_rejects_unavailable_f010_without_fixed_fallback(monkeypatch):
    from triggertrade.services import research_backtest_execution as module

    original_handoff = module._research_v1_handoff_facts

    def no_target_handoff(**kwargs):
        facts = original_handoff(**kwargs)
        return replace(
            facts,
            reference_levels=tuple(level for level in facts.reference_levels if "target" not in level.level_id),
        )

    rules = replace(
        _rules_version(),
        rules_version_id="TRV-R-POS-001-PR-201",
        draft=replace(
            _rules_version().draft,
            take_profit_mode=TakeProfitMode.DYNAMIC,
            stop_loss_mode=StopLossMode.DYNAMIC,
            stop_loss_pct=Decimal("0.20"),
            minimum_risk_reward=Decimal("1"),
            minimum_tranche_capital=Decimal("10"),
            max_capital_in_positions_pct=Decimal("0.60"),
            max_open_positions_enabled=True,
            max_open_positions=6,
            max_positions_per_coin_enabled=True,
            max_positions_per_coin=2,
        ),
    )
    monkeypatch.setattr(module, "_research_v1_handoff_facts", no_target_handoff)

    result = _run_research_v1_certified_position_backtest(
        trigger_set=_trigger_set(),
        rules=rules,
        plan=_backtest_plan(),
        candles=_trade_candles(volume_spike=True),
        instrument=_instrument_with_max_order_qty(),
        portfolio_state=_research_v1_portfolio(),
    )

    evaluation = result.research_v1_certified_position_evidence["position_opportunity"]["position_opportunity_state"]["evaluation"]
    assert evaluation["take_profit"]["formula_id"] == "F-010"
    assert evaluation["take_profit"]["status"] == "UNAVAILABLE"
    assert evaluation["take_profit"]["reason_code"] == "NO_ELIGIBLE_REFERENCE"
    assert result.rejected_intents == 1
    assert result.trades == 0
    assert not hasattr(result, "research_v1_portfolio_events") or result.research_v1_portfolio_events == ()


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


def _backtest_plan():
    from triggertrade.backtest import BacktestPlan

    return BacktestPlan(
        "BTCUSDT",
        "linear",
        "1m",
        datetime(2026, 9, 5, 14, 1, tzinfo=UTC),
        datetime(2026, 9, 5, 14, 14, tzinfo=UTC),
    )


def _instrument_with_max_order_qty():
    return FuturesInstrumentMetadata(
        "BTCUSDT",
        ContractCategory.LINEAR,
        "LinearPerpetual",
        "USDT",
        Decimal("0.001"),
        Decimal("0.001"),
        Decimal("0.001"),
        Decimal("5"),
        Decimal("100"),
        maximum_order_quantity=Decimal("100"),
    )


def _research_v1_portfolio():
    return ResearchV1SharedPortfolioState(
        total_capital=Decimal("1000"),
        max_capital_in_positions_pct=Decimal("0.60"),
        allocation_by_symbol=RESEARCH_V1_ALLOCATION_BY_SYMBOL,
        max_open_positions=6,
        max_positions_per_coin=2,
    )
