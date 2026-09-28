from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import uuid

import pytest

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.persistence import research_set_from_package_record
from triggertrade.persistence import ResearchBacktestStatus, ResearchStore, TradingRulesStore, TriggerSetStore
from triggertrade.research_v1_execution import (
    RESEARCH_V1_ALLOCATION_BY_SYMBOL,
    RESEARCH_V1_SYMBOLS,
    ResearchV1ExecutionError,
    ResearchV1SharedPortfolioState,
    apply_research_v1_portfolio_events,
    build_research_v1_execution_definition,
    load_research_v1_build_spec,
    research_v1_backtest_allocation_supported,
    research_v1_config_pin_payload,
    research_v1_definition_from_pin_payload,
    research_v1_rules_allocation_supported,
    resolve_research_v1_symbol_bindings,
    run_research_v1_backtest_orchestration,
    run_research_v1_demo_orchestration,
)
from triggertrade.backtest import BacktestResult, BacktestStatus
from triggertrade.persistence.research_store import ResearchBacktestRunRecord, ResearchDecision, ResearchRecord, ResearchStatus
from triggertrade.services.research_backtest_execution import CanonicalResearchBacktestExecutionExecutor
from triggertrade.services.research_demo_execution import CanonicalResearchDemoExecutionExecutor
from triggertrade.services.research import (
    ResearchBacktestExecutionHandoffResult,
    ResearchDemoExecutionHandoffResult,
    ResearchDemoIsolation,
    ResearchService,
)
from triggertrade.rules import TradingRulesVersion
from triggertrade.rules.trading import CoinRule, StopLossMode, TakeProfitMode, draft_from_json
from triggertrade.services.research import _backtest_block_reason
from triggertrade.persistence.postgres_research_registry import PostgresResearchConfigurationRegistryClient
from tests.unit.test_backtest_replay import _config
from triggertrade.config import load_config
from tests.unit.test_research_demo_execution import _demo_runtime_env


SETS_PACKAGE = Path("docs/research-import/sets/RESEARCH_V1_SETS.json")
RULES_WEB_IMPORT = Path("docs/research-import/rules/RESEARCH_V1_RULES_WEB_IMPORT.json")


def test_research_v1_execution_pin_covers_full_symbol_set_and_allocation_bindings():
    definition = build_research_v1_execution_definition("R-001")
    payload = research_v1_config_pin_payload(definition, created_source="unit")
    config = payload["config_pins"]["research_v1_execution"]
    digest = canonical_json_digest(payload)
    reconstructed = research_v1_definition_from_pin_payload(payload)

    assert config["research_id"] == "R-001"
    assert config["hypothesis_id"] == "R-001"
    assert config["selected_arm"] == "VARIANT"
    assert config["variant"]["btc"]["set_version_id"] == "SET-R-BTC-001-V2"
    assert config["variant"]["non_btc"]["set_version_id"] == "SET-R-001-V2"
    assert config["variant"]["rules_version_id"] == "TRV-R-POS-001-PR-201"
    assert tuple(config["ordered_symbols"]) == RESEARCH_V1_SYMBOLS
    assert set(config["allocation_by_symbol"].values()) == {"0.1"}
    assert config["segment_scope"] == ["MAJORS", "HIGH_VOLATILITY_HIGH_BETA", "DIVERSIFIERS"]
    assert config["direction_scope"]["values"] == ["LONG", "SHORT"]
    assert tuple(config["applicable_coins"]) == tuple(definition.applicable_coins)
    assert tuple(config["source_refs"]) == definition.source_refs
    assert reconstructed.selected_binding.btc.set_version_id == "SET-R-BTC-001-V2"
    assert reconstructed.direction_scope == definition.direction_scope

    changed = json.loads(json.dumps(payload))
    changed["config_pins"]["research_v1_execution"]["symbol_bindings"][0]["set_version_id"] = "SET-R-BTC-001-V1"
    assert canonical_json_digest(changed) != digest

    changed = json.loads(json.dumps(payload))
    changed["config_pins"]["research_v1_execution"]["allocation_by_symbol"]["BTCUSDT"] = "0.20"
    assert canonical_json_digest(changed) != digest


def test_r001_remains_ordinary_baseline_variant_binding_model():
    definition = build_research_v1_execution_definition("R-001")

    assert definition.set_binding_model == "SYMBOL_SET_BINDING"
    assert definition.rules_binding_model == "ARM_TRADING_RULES_VERSION"
    assert definition.selected_arm == "VARIANT"
    assert definition.baseline.btc.set_version_id == "SET-R-BTC-001-V1"
    assert definition.baseline.non_btc.set_version_id == "SET-R-001-V1"
    assert definition.variant.btc.set_version_id == "SET-R-BTC-001-V2"
    assert definition.variant.non_btc.set_version_id == "SET-R-001-V2"
    assert tuple(binding.arm for binding in definition.execution_bindings) == ("VARIANT",)


def test_r029_parses_exact_four_interaction_cells():
    definition = build_research_v1_execution_definition("R-029")

    assert definition.set_binding_model == "INTERACTION_CELL_SYMBOL_SET_BINDING"
    assert definition.rules_binding_model == "INTERACTION_CELL_TRADING_RULES_VERSION"
    assert definition.selected_arm == "11"
    assert tuple(definition.interaction_cells) == ("00", "01", "10", "11")
    assert _cell_tuple(definition, "00") == ("SET-R-BTC-001-V1", "SET-R-001-V1", "TRV-R-POS-001-PR-201")
    assert _cell_tuple(definition, "01") == ("SET-R-BTC-001-V1", "SET-R-001-V1", "TRV-R-POS-001-PR-207")
    assert _cell_tuple(definition, "10") == ("SET-R-BTC-003-V2", "SET-R-003-V2", "TRV-R-POS-001-PR-201")
    assert _cell_tuple(definition, "11") == ("SET-R-BTC-003-V2", "SET-R-003-V2", "TRV-R-POS-001-PR-207")


def test_r030_parses_exact_four_interaction_cells():
    definition = build_research_v1_execution_definition("R-030")

    assert definition.set_binding_model == "INTERACTION_CELL_SYMBOL_SET_BINDING"
    assert definition.rules_binding_model == "INTERACTION_CELL_TRADING_RULES_VERSION"
    assert definition.selected_arm == "11"
    assert _cell_tuple(definition, "00") == ("SET-R-BTC-001-V1", "SET-R-001-V1", "TRV-R-POS-001-PR-201")
    assert _cell_tuple(definition, "01") == ("SET-R-BTC-001-V1", "SET-R-001-V1", "TRV-R-POS-001-PR-201")
    assert _cell_tuple(definition, "10") == ("SET-R-BTC-001-V2", "SET-R-001-V2", "TRV-R-POS-003-PR-201")
    assert _cell_tuple(definition, "11") == ("SET-R-BTC-001-V2", "SET-R-001-V2", "TRV-R-POS-003-PR-201")


def test_interaction_pin_payload_and_roundtrip_preserve_all_four_cells():
    definition = build_research_v1_execution_definition("R-029")
    payload = research_v1_config_pin_payload(
        definition,
        created_source="unit",
        instrument_resolver=lambda symbol: SimpleNamespace(symbol=symbol),
    )
    config = payload["config_pins"]["research_v1_execution"]
    reconstructed = research_v1_definition_from_pin_payload(payload)

    assert config["set_binding_model"] == "INTERACTION_CELL_SYMBOL_SET_BINDING"
    assert config["rules_binding_model"] == "INTERACTION_CELL_TRADING_RULES_VERSION"
    assert tuple(config["interaction_cells"]) == ("00", "01", "10", "11")
    assert tuple(config["cell_symbol_bindings"]) == ("00", "01", "10", "11")
    assert config["cell_symbol_bindings"]["00"][0]["cell_id"] == "00"
    assert config["cell_symbol_bindings"]["11"][0]["set_version_id"] == "SET-R-BTC-003-V2"
    assert tuple(reconstructed.interaction_cells) == ("00", "01", "10", "11")
    assert _cell_tuple(reconstructed, "01") == ("SET-R-BTC-001-V1", "SET-R-001-V1", "TRV-R-POS-001-PR-207")


def test_research_v1_symbol_resolver_binds_btc_and_non_btc_sets_exactly():
    definition = build_research_v1_execution_definition("R-001")
    bindings = resolve_research_v1_symbol_bindings(
        definition,
        available_sets=_research_v1_sets_by_version(),
        instrument_resolver=lambda symbol: SimpleNamespace(symbol=symbol),
    )
    by_asset = {binding.asset: binding for binding in bindings}

    assert by_asset["BTC"].set_version_id == "SET-R-BTC-001-V2"
    for asset in ("ETH", "SOL", "XRP", "DOGE", "SUI", "PEPE", "AVAX", "LINK", "BNB"):
        assert by_asset[asset].set_version_id == "SET-R-001-V2"
        assert by_asset[asset].rules_version_id == "TRV-R-POS-001-PR-201"

    missing = dict(_research_v1_sets_by_version())
    missing.pop("SET-R-BTC-001-V2")
    with pytest.raises(ResearchV1ExecutionError, match="does not resolve"):
        resolve_research_v1_symbol_bindings(definition, available_sets=missing)

    wrong_version = {
        key: replace(value, set_version="SET-R-BTC-001-V9") if key == "SET-R-BTC-001-V2" else value
        for key, value in _research_v1_sets_by_version().items()
    }
    wrong_version.pop("SET-R-BTC-001-V2")
    wrong_version["SET-R-BTC-001-V9"] = replace(_research_v1_sets_by_version()["SET-R-BTC-001-V2"], set_version="SET-R-BTC-001-V9")
    with pytest.raises(ResearchV1ExecutionError, match="does not resolve"):
        resolve_research_v1_symbol_bindings(definition, available_sets=wrong_version)
    with pytest.raises(ResearchV1ExecutionError, match="mismatched symbol"):
        resolve_research_v1_symbol_bindings(
            definition,
            available_sets=_research_v1_sets_by_version(),
            instrument_resolver=lambda symbol: SimpleNamespace(symbol="BTCUSDT"),
        )


def test_r006_preserves_btc_universe_allocation_but_skips_execution_as_not_applicable():
    definition = build_research_v1_execution_definition("R-006")
    bindings = resolve_research_v1_symbol_bindings(definition, available_sets=_research_v1_sets_by_version())
    btc = next(binding for binding in bindings if binding.asset == "BTC")

    assert "BTC" in definition.ordered_assets
    assert definition.allocation_by_symbol["BTCUSDT"] == Decimal("0.10")
    assert btc.applicable is False
    assert btc.applicability == "NOT_APPLICABLE"
    assert btc.reason == "SOURCE_LOGIC_NOT_MEANINGFUL_FOR_BTC"
    assert btc.set_version_id is None
    assert sum(binding.allocation_pct for binding in bindings if binding.applicable) == Decimal("0.90")
    assert {binding.allocation_pct for binding in bindings} == {Decimal("0.10")}


def test_research_v1_shared_portfolio_state_is_global_with_per_coin_caps():
    state = ResearchV1SharedPortfolioState(
        total_capital=Decimal("1000"),
        max_capital_in_positions_pct=Decimal("0.25"),
        allocation_by_symbol=RESEARCH_V1_ALLOCATION_BY_SYMBOL,
        max_open_positions=3,
        max_positions_per_coin=2,
    )

    after_btc = state.reserve("BTCUSDT", Decimal("100"))
    assert after_btc.available_capital == Decimal("150")

    after_eth = after_btc.reserve("ETHUSDT", Decimal("100"))
    assert after_eth.available_capital == Decimal("50")
    with pytest.raises(ResearchV1ExecutionError, match="per-coin allocation cap"):
        after_eth.reserve("BTCUSDT", Decimal("1"))
    with pytest.raises(ResearchV1ExecutionError, match="aggregate portfolio cap"):
        after_eth.reserve("SOLUSDT", Decimal("51"))


def test_research_v1_allocation_rules_are_supported_but_other_allocation_shapes_fail_closed():
    rules = _research_v1_rules()["TRV-R-POS-001-PR-201"]
    fixed_supported = replace(
        rules,
        draft=replace(
            rules.draft,
            take_profit_mode=TakeProfitMode.FIXED,
            fixed_take_profit_pct=Decimal("0.02"),
            stop_loss_mode=StopLossMode.FIXED,
            stop_loss_pct=Decimal("0.01"),
            max_capital_in_positions_pct=Decimal("1"),
        ),
    )
    assert research_v1_rules_allocation_supported(rules) is True
    assert research_v1_backtest_allocation_supported(rules, "BTCUSDT") is True
    assert _backtest_block_reason(fixed_supported, _config(Path(".tmp") / "research-v1-runtime.db"), _plan("BTCUSDT")) == "research_backtest_coin_allocation_rules_unimplemented"
    assert _backtest_block_reason(
        fixed_supported,
        _config(Path(".tmp") / "research-v1-runtime.db"),
        _plan("BTCUSDT"),
        research_v1_execution=True,
    ) != "research_backtest_coin_allocation_rules_unimplemented"

    draft = rules.draft
    unsupported = replace(
        rules,
        draft=replace(
            draft,
                take_profit_mode=TakeProfitMode.FIXED,
                fixed_take_profit_pct=Decimal("0.02"),
                stop_loss_mode=StopLossMode.FIXED,
                stop_loss_pct=Decimal("0.01"),
            coins=(CoinRule(symbol="BTCUSDT", enabled=True, max_allocation_pct=Decimal("0.50")),),
        ),
    )
    assert research_v1_rules_allocation_supported(unsupported) is False
    assert _backtest_block_reason(unsupported, _config(Path(".tmp") / "research-v1-runtime.db"), _plan("BTCUSDT")) == "research_backtest_coin_allocation_rules_unimplemented"


def test_research_v1_backtest_orchestration_preserves_symbol_set_attribution():
    definition = build_research_v1_execution_definition("R-001")
    portfolio = _portfolio()
    calls = []

    def runner(binding, shared_portfolio):
        calls.append((binding.symbol, binding.set_version_id, shared_portfolio is portfolio))
        return {"status": "COMPLETED"}

    result = run_research_v1_backtest_orchestration(
        definition,
        available_sets=_research_v1_sets_by_version(),
        run_profile="BACKTEST_7D",
        portfolio=portfolio,
        symbol_runner=runner,
    )

    assert len(calls) == 10
    assert calls[0] == ("BTCUSDT", "SET-R-BTC-001-V2", True)
    assert {set_id for symbol, set_id, _shared in calls if symbol != "BTCUSDT"} == {"SET-R-001-V2"}
    assert len(result.symbol_results) == 10
    assert result.symbol_results[0]["set_version_id"] == "SET-R-BTC-001-V2"


def test_interaction_backtest_executes_all_four_cells_with_isolated_portfolios():
    definition = build_research_v1_execution_definition("R-029")
    portfolio = ResearchV1SharedPortfolioState(
        total_capital=Decimal("1000"),
        max_capital_in_positions_pct=Decimal("0.25"),
        allocation_by_symbol=RESEARCH_V1_ALLOCATION_BY_SYMBOL,
        max_open_positions=4,
        max_positions_per_coin=2,
    )
    observed = []

    def runner(binding, shared_portfolio):
        observed.append((binding.cell_id, binding.symbol, shared_portfolio.committed_capital, shared_portfolio.available_capital))
        if binding.symbol == "BTCUSDT":
            return {"status": "OBSERVED"}, shared_portfolio.reserve(binding.symbol, Decimal("100"))
        if binding.symbol == "ETHUSDT":
            return {"status": "OBSERVED"}, shared_portfolio.reserve(binding.symbol, Decimal("100"))
        return {"status": "OBSERVED"}, shared_portfolio

    result = run_research_v1_backtest_orchestration(
        definition,
        available_sets=_research_v1_sets_by_version(),
        run_profile="BACKTEST_7D",
        portfolio=portfolio,
        symbol_runner=runner,
    )

    assert len(result.symbol_results) == 40
    assert {item["cell_id"] for item in result.symbol_results} == {"00", "01", "10", "11"}
    assert observed[0] == ("00", "BTCUSDT", Decimal("0"), Decimal("250.00"))
    assert observed[1] == ("00", "ETHUSDT", Decimal("100"), Decimal("150.00"))
    assert observed[2] == ("00", "SOLUSDT", Decimal("200"), Decimal("50.00"))
    assert observed[10] == ("01", "BTCUSDT", Decimal("0"), Decimal("250.00"))
    assert result.portfolio_snapshot["00"]["committed_capital"] == "200"
    assert result.portfolio_snapshot["01"]["committed_capital"] == "200"


def test_research_v1_orchestration_propagates_shared_portfolio_state_between_symbols():
    definition = build_research_v1_execution_definition("R-001")
    portfolio = ResearchV1SharedPortfolioState(
        total_capital=Decimal("1000"),
        max_capital_in_positions_pct=Decimal("0.25"),
        allocation_by_symbol=RESEARCH_V1_ALLOCATION_BY_SYMBOL,
        max_open_positions=4,
        max_positions_per_coin=2,
    )
    observed = []

    def runner(binding, shared_portfolio):
        observed.append((binding.symbol, shared_portfolio.committed_capital, shared_portfolio.available_capital))
        if binding.symbol in {"BTCUSDT", "ETHUSDT"}:
            return {"status": "OBSERVED"}, shared_portfolio.reserve(binding.symbol, Decimal("100"))
        return {"status": "OBSERVED"}, shared_portfolio

    result = run_research_v1_demo_orchestration(
        definition,
        available_sets=_research_v1_sets_by_version(),
        portfolio=portfolio,
        symbol_runner=runner,
    )

    assert observed[0] == ("BTCUSDT", Decimal("0"), Decimal("250.00"))
    assert observed[1] == ("ETHUSDT", Decimal("100"), Decimal("150.00"))
    assert observed[2] == ("SOLUSDT", Decimal("200"), Decimal("50.00"))
    assert result.portfolio_snapshot["committed_capital"] == "200"
    assert result.run_kind == "DEMO"
    assert result.run_profile == "DEMO_7D"


def test_research_service_persists_full_v1_pin_and_uses_v1_backtest_handoff():
    db = _ephemeral_db_path("research-v1-service")
    registry = _FakeResearchV1ConfigurationRegistry()
    handoff = _FakeResearchV1BacktestHandoff(db)
    service = _research_v1_service(db, registry=registry, backtest_handoff=handoff)
    rules = _fixed_research_v1_rule("TRV-R-POS-001-PR-201")
    registry.rules[rules.rules_version_id] = rules

    research = service.create_research_v1(
        research_id="R-001",
        created_at="2026-09-28T00:00:00+00:00",
        instrument_resolver=lambda symbol: SimpleNamespace(symbol=symbol),
    )
    plan = _plan("BTCUSDT")
    run = service.run_backtest(
        research_id=research.research_id,
        plan=plan,
        created_at=plan.research_start,
    )
    reloaded = ResearchStore(db).get_research(research.research_id)
    reconstructed = research_v1_definition_from_pin_payload(reloaded.pin_payload)

    assert reconstructed.research_id == "R-001"
    assert reloaded.pin_payload["config_pins"]["research_v1_execution"]["symbol_bindings"][0]["set_version_id"] == "SET-R-BTC-001-V2"
    assert reloaded.pin_payload["config_pins"]["research_v1_execution"]["symbol_bindings"][1]["set_version_id"] == "SET-R-001-V2"
    assert run.status.value == "RUNNING"
    assert handoff.requests == [
        {
            "research_id": research.research_id,
            "rules_version_id": "TRV-R-POS-001-PR-201",
            "selected_arm": "VARIANT",
            "btc_set_version_id": "SET-R-BTC-001-V2",
            "non_btc_set_version_id": "SET-R-001-V2",
            "symbol_bindings": 10,
        }
    ]
    assert registry.research[research.research_id].pin_digest == research.pin_digest


def test_research_service_uses_v1_demo_handoff_from_durable_pin():
    db = _ephemeral_db_path("research-v1-demo-service")
    registry = _FakeResearchV1ConfigurationRegistry()
    handoff = _FakeResearchV1DemoHandoff()
    service = _research_v1_service(
        db,
        registry=registry,
        demo_handoff=handoff,
        demo_isolation=ResearchDemoIsolation(
            available=True,
            execution_scope_id="research-v1-demo",
            account_scope="research-v1-account",
            adapter_scope_id="research-v1-paper",
            state_scope_id="research-v1-state",
        ),
    )
    rules = _fixed_research_v1_rule("TRV-R-POS-001-PR-201")
    registry.rules[rules.rules_version_id] = rules
    research = service.create_research_v1(
        research_id="R-001",
        created_at="2026-09-28T00:00:00+00:00",
        instrument_resolver=lambda symbol: SimpleNamespace(symbol=symbol),
    )

    run = service.start_demo_run(research.research_id, created_at="2026-09-28T00:01:00+00:00")

    assert run.status.value == "RUNNING"
    assert handoff.requests == [
        {
            "research_id": research.research_id,
            "rules_version_id": "TRV-R-POS-001-PR-201",
            "selected_arm": "VARIANT",
            "btc_set_version_id": "SET-R-BTC-001-V2",
            "non_btc_set_version_id": "SET-R-001-V2",
            "demo_run_id": run.run_id,
        }
    ]


def test_durable_backtest_worker_applies_shared_portfolio_events_and_enforces_global_cap(monkeypatch):
    rules = replace(
        _fixed_research_v1_rule("TRV-R-POS-001-PR-201"),
        draft=replace(_fixed_research_v1_rule("TRV-R-POS-001-PR-201").draft, max_capital_in_positions_pct=Decimal("0.25")),
    )
    research = _research_v1_record("R-001")
    record = _backtest_record(research.research_id)
    calls = []

    class FakeRegistry:
        def __init__(self, _connection):
            pass

        def get_trading_rules_version(self, rules_version_id):
            return rules if rules_version_id == rules.rules_version_id else None

    class FakeSetRegistry:
        def __init__(self, _connection):
            pass

        def list_research_sets(self):
            return tuple(_research_v1_sets_by_version().values())

    def fake_run_backtest(**kwargs):
        trigger_set = kwargs["trigger_set_store"].get_set(kwargs["trigger_set_id"], kwargs["trigger_set_version"])
        calls.append((kwargs["plan"].symbol, trigger_set.version))
        amount = "51" if kwargs["plan"].symbol == "SOLUSDT" else "100"
        return _backtest_result(
            kwargs["plan"].symbol,
            research_v1_portfolio_events=(
                {
                    "action": "RESERVE",
                    "symbol": kwargs["plan"].symbol,
                    "actual_committed_capital": amount,
                    "canonical_source": "backtest_canonical_commitment.actual_committed_capital",
                },
            ),
        )

    monkeypatch.setattr("triggertrade.services.research_backtest_execution.PostgresUnitOfWork", _FakeUnitOfWork)
    monkeypatch.setattr("triggertrade.services.research_backtest_execution.PostgresResearchConfigurationRegistry", FakeRegistry)
    monkeypatch.setattr("triggertrade.services.research_backtest_execution.PostgresResearchSetRegistry", FakeSetRegistry)
    monkeypatch.setattr("triggertrade.services.research_backtest_execution.run_backtest", fake_run_backtest)
    executor = CanonicalResearchBacktestExecutionExecutor(
        config=_config(Path(".tmp") / "research-v1-durable-backtest.db"),
        db_path=Path(".tmp") / "research-v1-durable-backtest.db",
        factory=object(),
        historical_source=_FakeHistoricalSource(),
        instrument_provider=lambda symbol: SimpleNamespace(symbol=symbol),
    )

    with pytest.raises(ResearchV1ExecutionError, match="aggregate portfolio cap"):
        executor._start_research_v1_backtest(record, research, _plan("BTCUSDT"))

    assert calls[:3] == [
        ("BTCUSDT", "SET-R-BTC-001-V2"),
        ("ETHUSDT", "SET-R-001-V2"),
        ("SOLUSDT", "SET-R-001-V2"),
    ]


def test_durable_backtest_worker_releases_only_from_closed_finality(monkeypatch):
    rules = replace(
        _fixed_research_v1_rule("TRV-R-POS-001-PR-201"),
        draft=replace(_fixed_research_v1_rule("TRV-R-POS-001-PR-201").draft, max_capital_in_positions_pct=Decimal("0.25")),
    )
    research = _research_v1_record("R-001")
    record = _backtest_record(research.research_id)
    captured_metrics = {}

    class FakeRegistry:
        def __init__(self, _connection):
            pass

        def get_trading_rules_version(self, rules_version_id):
            return rules if rules_version_id == rules.rules_version_id else None

    class FakeSetRegistry:
        def __init__(self, _connection):
            pass

        def list_research_sets(self):
            return tuple(_research_v1_sets_by_version().values())

    class FakeRunStore:
        def __init__(self, _connection):
            pass

        def update_backtest_run(self, **kwargs):
            captured_metrics.update(kwargs["metrics"])
            return record

    def fake_run_backtest(**kwargs):
        events = ()
        if kwargs["plan"].symbol == "BTCUSDT":
            events = (
                {
                    "action": "RESERVE",
                    "symbol": "BTCUSDT",
                    "actual_committed_capital": "100",
                    "canonical_source": "backtest_canonical_commitment.actual_committed_capital",
                },
                {
                    "action": "RELEASE",
                    "symbol": "BTCUSDT",
                    "actual_committed_capital": "100",
                    "lifecycle_state": "CLOSED",
                    "canonical_source": "backtest_canonical_commitment.actual_committed_capital",
                },
            )
        return _backtest_result(kwargs["plan"].symbol, research_v1_portfolio_events=events)

    monkeypatch.setattr("triggertrade.services.research_backtest_execution.PostgresUnitOfWork", _FakeUnitOfWork)
    monkeypatch.setattr("triggertrade.services.research_backtest_execution.PostgresResearchConfigurationRegistry", FakeRegistry)
    monkeypatch.setattr("triggertrade.services.research_backtest_execution.PostgresResearchSetRegistry", FakeSetRegistry)
    monkeypatch.setattr("triggertrade.services.research_backtest_execution.PostgresResearchRunStore", FakeRunStore)
    monkeypatch.setattr("triggertrade.services.research_backtest_execution.run_backtest", fake_run_backtest)
    executor = CanonicalResearchBacktestExecutionExecutor(
        config=_config(Path(".tmp") / "research-v1-durable-release.db"),
        db_path=Path(".tmp") / "research-v1-durable-release.db",
        factory=object(),
        historical_source=_FakeHistoricalSource(),
        instrument_provider=lambda symbol: SimpleNamespace(symbol=symbol),
    )

    executor._start_research_v1_backtest(record, research, _plan("BTCUSDT"))

    assert captured_metrics["portfolio"]["committed_capital"] == "0"
    assert captured_metrics["portfolio"]["available_capital"] == "250.00"
    with pytest.raises(ResearchV1ExecutionError, match="CLOSED finality"):
        apply_research_v1_portfolio_events(
            _portfolio(),
            (
                {
                    "action": "RELEASE",
                    "symbol": "BTCUSDT",
                    "actual_committed_capital": "100",
                    "lifecycle_state": "CLOSING",
                    "canonical_source": "backtest_canonical_commitment.actual_committed_capital",
                },
            ),
        )


def test_durable_demo_worker_passes_accumulated_shared_portfolio_state(monkeypatch):
    rules = replace(
        _fixed_research_v1_rule("TRV-R-POS-001-PR-201"),
        draft=replace(_fixed_research_v1_rule("TRV-R-POS-001-PR-201").draft, max_capital_in_positions_pct=Decimal("0.25")),
    )
    research = _research_v1_record("R-001")
    record = SimpleNamespace(research_id=research.research_id, demo_run_id="rdm-v1", rules_version_id=rules.rules_version_id)
    observed = []

    class FakeRegistry:
        def __init__(self, _connection):
            pass

        def get_trading_rules_version(self, rules_version_id):
            return rules if rules_version_id == rules.rules_version_id else None

    class FakeSetRegistry:
        def __init__(self, _connection):
            pass

        def list_research_sets(self):
            return tuple(_research_v1_sets_by_version().values())

    class FakeCycle:
        canonical_research_demo_trading_cycle = True

        def run_research_demo_cycle(self, *, record, configuration):
            state = configuration.research_v1_portfolio_state
            symbol = configuration.trigger_set.symbol
            observed.append((symbol, state.committed_capital, state.available_capital))
            events = ()
            if symbol in {"BTCUSDT", "ETHUSDT"}:
                events = (
                    {
                        "action": "RESERVE",
                        "symbol": symbol,
                        "actual_committed_capital": "100",
                        "canonical_source": "lifecycle_start_gate.held_committed_capital",
                    },
                )
            return {
                "canonical_cycle": True,
                "reconciliation_before_resubmit": True,
                "resubmitted_without_reconciliation": False,
                "canonical_runtime_wait_state": False,
                "canonical_trading_decisions_invoked": True,
                "canonical_lifecycle_invoked": True,
                "canonical_futures_execution_invoked": True,
                "unresolved_obligations": 1,
                "research_v1_portfolio_events": events,
            }

    monkeypatch.setattr("triggertrade.services.research_demo_execution.PostgresUnitOfWork", _FakeUnitOfWork)
    monkeypatch.setattr("triggertrade.services.research_demo_execution.PostgresResearchConfigurationRegistry", FakeRegistry)
    monkeypatch.setattr("triggertrade.services.research_demo_execution.PostgresResearchSetRegistry", FakeSetRegistry)
    executor = CanonicalResearchDemoExecutionExecutor(
        config=load_config(_demo_runtime_env()),
        factory=object(),
        trading_cycle=FakeCycle(),
        accounting_store=SimpleNamespace(list_closed_trades=lambda limit=20: ()),
    )

    result = executor._start_research_v1_demo(record, research)

    assert observed[:3] == [
        ("BTCUSDT", Decimal("0"), Decimal("250.00")),
        ("ETHUSDT", Decimal("100"), Decimal("150.00")),
        ("SOLUSDT", Decimal("200"), Decimal("50.00")),
    ]
    assert result["cycle"]["portfolio"]["committed_capital"] == "200"


def test_durable_demo_worker_uses_cell_qualified_runtime_scope_for_interactions(monkeypatch):
    rules = {
        rule_id: replace(_fixed_research_v1_rule(rule_id), draft=replace(_fixed_research_v1_rule(rule_id).draft, max_capital_in_positions_pct=Decimal("0.25")))
        for rule_id in ("TRV-R-POS-001-PR-201", "TRV-R-POS-001-PR-207")
    }
    research = _research_v1_record("R-029")
    record = SimpleNamespace(research_id=research.research_id, demo_run_id="rdm-v1", rules_version_id=research.rules_version_id)
    observed = []

    class FakeRegistry:
        def __init__(self, _connection):
            pass

        def get_trading_rules_version(self, rules_version_id):
            return rules.get(rules_version_id)

    class FakeSetRegistry:
        def __init__(self, _connection):
            pass

        def list_research_sets(self):
            return tuple(_research_v1_sets_by_version().values())

    class FakeCycle:
        canonical_research_demo_trading_cycle = True

        def run_research_demo_cycle(self, *, record, configuration):
            state = configuration.research_v1_portfolio_state
            symbol = configuration.trigger_set.symbol
            cell_id = record.demo_run_id.rsplit("cell-", 1)[-1]
            observed.append((cell_id, record.demo_run_id, symbol, state.committed_capital))
            events = ()
            if symbol == "BTCUSDT":
                events = (
                    {
                        "action": "RESERVE",
                        "symbol": symbol,
                        "actual_committed_capital": "100",
                        "canonical_source": "lifecycle_start_gate.held_committed_capital",
                    },
                )
            return {
                "canonical_cycle": True,
                "research_v1_portfolio_events": events,
            }

    monkeypatch.setattr("triggertrade.services.research_demo_execution.PostgresUnitOfWork", _FakeUnitOfWork)
    monkeypatch.setattr("triggertrade.services.research_demo_execution.PostgresResearchConfigurationRegistry", FakeRegistry)
    monkeypatch.setattr("triggertrade.services.research_demo_execution.PostgresResearchSetRegistry", FakeSetRegistry)
    executor = CanonicalResearchDemoExecutionExecutor(
        config=load_config(_demo_runtime_env()),
        factory=object(),
        trading_cycle=FakeCycle(),
        accounting_store=SimpleNamespace(list_closed_trades=lambda limit=20: ()),
    )

    result = executor._start_research_v1_demo(record, research)

    assert len(result["cycle"]["symbol_results"]) == 40
    assert {item["cell_id"] for item in result["cycle"]["symbol_results"]} == {"00", "01", "10", "11"}
    assert observed[0] == ("00", "rdm-v1:cell-00", "BTCUSDT", Decimal("0"))
    assert observed[1] == ("00", "rdm-v1:cell-00", "ETHUSDT", Decimal("100"))
    assert observed[10] == ("01", "rdm-v1:cell-01", "BTCUSDT", Decimal("0"))


def test_research_v1_preflight_all_30_definitions_resolve_symbols_and_rules():
    sets = _research_v1_sets_by_version()
    rules = _research_v1_rules()
    spec = load_research_v1_build_spec()
    definitions = [item["research_id"] for item in spec["research_definitions"]]
    unique_rules = set()

    for research_id in definitions:
        definition = build_research_v1_execution_definition(research_id, spec=spec)
        for binding in definition.execution_bindings:
            assert binding.rules_version_id in rules
            unique_rules.add(binding.rules_version_id)
        symbol_bindings = resolve_research_v1_symbol_bindings(
            definition,
            available_sets=sets,
            instrument_resolver=lambda symbol: SimpleNamespace(symbol=symbol),
        )
        assert len(symbol_bindings) == 10

    assert len(definitions) == 30
    assert len(unique_rules) == 16


def test_postgres_research_configuration_registry_client_gets_exact_rules_version(monkeypatch):
    expected = _fixed_research_v1_rule("TRV-R-POS-001-PR-201")
    calls = []

    class FakeUnitOfWork:
        def __init__(self, factory):
            self.connection = object()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeRegistry:
        def __init__(self, connection):
            pass

        def get_trading_rules_version(self, rules_version_id):
            calls.append(rules_version_id)
            return expected if rules_version_id == expected.rules_version_id else None

    monkeypatch.setattr("triggertrade.persistence.postgres_research_registry.PostgresUnitOfWork", FakeUnitOfWork)
    monkeypatch.setattr("triggertrade.persistence.postgres_research_registry.PostgresResearchConfigurationRegistry", FakeRegistry)

    client = PostgresResearchConfigurationRegistryClient(object())

    assert client.get_trading_rules_version(expected.rules_version_id) == expected
    assert client.get_trading_rules_version("missing") is None
    assert calls == [expected.rules_version_id, "missing"]


def _plan(symbol):
    from datetime import UTC, datetime
    from triggertrade.backtest import BacktestPlan

    return BacktestPlan(symbol, "linear", "1m", datetime(2026, 9, 1, tzinfo=UTC), datetime(2026, 9, 2, tzinfo=UTC))


def _cell_tuple(definition, cell_id: str) -> tuple[str | None, str | None, str]:
    cell = definition.interaction_cells[cell_id]
    return (cell.btc.set_version_id, cell.non_btc.set_version_id, cell.rules_version_id)


def _research_v1_record(research_id: str) -> ResearchRecord:
    definition = build_research_v1_execution_definition(research_id)
    pin_payload = research_v1_config_pin_payload(
        definition,
        created_source="unit",
        instrument_resolver=lambda symbol: SimpleNamespace(symbol=symbol),
    )
    return ResearchRecord(
        research_id=f"res-{research_id.lower()}",
        created_at="2026-09-28T00:00:00+00:00",
        updated_at="2026-09-28T00:00:00+00:00",
        status=ResearchStatus.DRAFT,
        set_id=str(definition.selected_binding.non_btc.set_id),
        set_version=str(definition.selected_binding.non_btc.set_version_id),
        rules_version_id=definition.selected_binding.rules_version_id,
        rules_display_version=definition.selected_binding.rules_version_id,
        selected_backtest_run_id=None,
        selected_demo_run_id=None,
        decision=ResearchDecision.NONE,
        decision_at=None,
        archived_at=None,
        made_active_at=None,
        promoted_set_id=None,
        promoted_set_version=None,
        promoted_rules_version_id=None,
        previous_active_set_id=None,
        previous_active_set_version=None,
        previous_rules_version_id=None,
        promotion_result_metadata={},
        created_source="unit",
        schema_version="research-v1",
        pin_payload=pin_payload,
        pin_digest=canonical_json_digest(pin_payload),
    )


def _backtest_record(research_id: str) -> ResearchBacktestRunRecord:
    return ResearchBacktestRunRecord(
        research_id=research_id,
        run_id=f"rbt-{research_id}",
        created_at="2026-09-28T00:00:00+00:00",
        updated_at="2026-09-28T00:00:00+00:00",
        status=ResearchBacktestStatus.RUNNING,
        period_start="2026-09-01T00:00:00+00:00",
        period_end="2026-09-02T00:00:00+00:00",
        timeframe="1m",
        engine_run_id=None,
        selected_for_use=False,
        metrics={},
        unavailable_reason=None,
        pin_payload={},
        pin_digest="unit",
    )


def _backtest_result(symbol: str, *, research_v1_portfolio_events=()) -> BacktestResult:
    result = BacktestResult(
        backtest_run_id=f"bt-{symbol.lower()}",
        status=BacktestStatus.COMPLETED,
        candles_processed=1,
        signals=1,
        intents=1,
        trades=0,
        closed_trades=0,
        rejected_intents=0,
        no_action_count=0,
        technical_failures=0,
        net_pnl=Decimal("0"),
        expectancy=None,
        profit_factor=None,
        max_drawdown=None,
        fees=Decimal("0"),
        funding=Decimal("0"),
        long_trades=0,
        short_trades=0,
        by_regime={},
    )
    object.__setattr__(result, "research_v1_portfolio_events", tuple(research_v1_portfolio_events))
    return result


class _FakeHistoricalSource:
    def load(self, **_kwargs):
        return SimpleNamespace(candles=("canonical-candle",))


class _FakeUnitOfWork:
    def __init__(self, _factory):
        self.connection = object()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _portfolio() -> ResearchV1SharedPortfolioState:
    return ResearchV1SharedPortfolioState(
        total_capital=Decimal("1000"),
        max_capital_in_positions_pct=Decimal("1"),
        allocation_by_symbol=RESEARCH_V1_ALLOCATION_BY_SYMBOL,
        max_open_positions=20,
        max_positions_per_coin=2,
    )


def _research_v1_sets_by_version():
    package = json.loads(SETS_PACKAGE.read_text(encoding="utf-8"))
    return {
        record.set_version: record
        for record in (research_set_from_package_record(item) for item in package["sets"])
    }


def _research_v1_rules() -> dict[str, TradingRulesVersion]:
    payload = json.loads(RULES_WEB_IMPORT.read_text(encoding="utf-8"))
    rules = {}
    for record in payload["trading_rules_versions"]:
        draft = draft_from_json(json.dumps(record["draft"], sort_keys=True, separators=(",", ":")))
        rules[str(record["rules_version_id"])] = TradingRulesVersion(
            rules_version_id=str(record["rules_version_id"]),
            version=str(record["version"]),
            created_at=str(record["created_at"]),
            created_from_version_id=None if record.get("created_from_version_id") is None else str(record["created_from_version_id"]),
            created_source=str(record["created_source"]),
            change_summary=str(record["change_summary"]),
            config_hash=str(record["config_hash"]),
            schema_version=str(record["schema_version"]),
            draft=draft,
            is_current=False,
        )
    return rules


def _fixed_research_v1_rule(rules_version_id: str) -> TradingRulesVersion:
    rules = _research_v1_rules()[rules_version_id]
    return replace(
        rules,
        draft=replace(
            rules.draft,
            take_profit_mode=TakeProfitMode.FIXED,
            fixed_take_profit_pct=Decimal("0.02"),
            stop_loss_mode=StopLossMode.FIXED,
            stop_loss_pct=Decimal("0.01"),
            max_capital_in_positions_pct=Decimal("0.30"),
        ),
    )


def _ephemeral_db_path(prefix: str) -> Path:
    root = Path(".tmp") / "research-v1-service-tests"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{prefix}-{uuid.uuid4().hex}.sqlite3"


def _research_v1_service(
    db: Path,
    *,
    registry,
    backtest_handoff=None,
    demo_handoff=None,
    demo_isolation=None,
) -> ResearchService:
    return ResearchService(
        store=ResearchStore(db),
        trigger_set_store=TriggerSetStore(db),
        trading_rules_store=TradingRulesStore(db),
        config=_config(db),
        research_config_registry=registry,
        backtest_execution_handoff=backtest_handoff,
        demo_execution_handoff=demo_handoff,
        demo_isolation=demo_isolation,
    )


class _FakeResearchV1ConfigurationRegistry:
    def __init__(self) -> None:
        self.rules: dict[str, TradingRulesVersion] = {}
        self.research = {}

    def get_trading_rules_version(self, rules_version_id: str) -> TradingRulesVersion | None:
        return self.rules.get(rules_version_id)

    def put_research(self, research) -> None:
        self.research[research.research_id] = research


class _FakeResearchV1BacktestHandoff:
    canonical_worker_handoff = True

    def __init__(self, db: Path) -> None:
        self.db = db
        self.requests = []

    def start_research_v1_backtest(self, *, research, rules, plan, created_at, pin_payload):
        definition = research_v1_definition_from_pin_payload(research.pin_payload)
        config = research.pin_payload["config_pins"]["research_v1_execution"]
        self.requests.append(
            {
                "research_id": research.research_id,
                "rules_version_id": rules.rules_version_id,
                "selected_arm": definition.selected_arm,
                "btc_set_version_id": definition.selected_binding.btc.set_version_id,
                "non_btc_set_version_id": definition.selected_binding.non_btc.set_version_id,
                "symbol_bindings": len(config["symbol_bindings"]),
            }
        )
        record = ResearchStore(self.db).add_backtest_run(
            research_id=research.research_id,
            period_start=plan.research_start.isoformat(),
            period_end=plan.research_end.isoformat(),
            timeframe=plan.timeframe,
            status=ResearchBacktestStatus.RUNNING,
            metrics={},
            pin_payload=pin_payload,
            created_at=created_at,
        )
        return ResearchBacktestExecutionHandoffResult(
            handoff_id=f"research-v1-backtest:{record.run_id}",
            execution_owner="trading-worker",
            durable=True,
            record=record,
        )


class _FakeResearchV1DemoHandoff:
    canonical_worker_handoff = True

    def __init__(self) -> None:
        self.requests = []

    def start_research_v1_demo(self, *, research, rules, isolation, started_at, pin_payload, demo_run_id):
        definition = research_v1_definition_from_pin_payload(research.pin_payload)
        self.requests.append(
            {
                "research_id": research.research_id,
                "rules_version_id": rules.rules_version_id,
                "selected_arm": definition.selected_arm,
                "btc_set_version_id": definition.selected_binding.btc.set_version_id,
                "non_btc_set_version_id": definition.selected_binding.non_btc.set_version_id,
                "demo_run_id": demo_run_id,
            }
        )
        return ResearchDemoExecutionHandoffResult(
            handoff_id=f"research-v1-demo:{demo_run_id}",
            execution_owner="trading-worker",
            durable=True,
        )
    research_v1_definition_from_pin_payload,
