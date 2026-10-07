from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

import pytest

from triggertrade.backtest import BacktestStatus
from triggertrade.backtest.models import HistoricalCandle
from triggertrade.canonical_json import canonical_json_digest
from triggertrade.instruments import FuturesInstrument
from triggertrade.persistence.postgres_research_set_registry import ResearchSetTriggerMember, ResearchSetVersion, research_set_digest
from triggertrade.research_v1_execution import RESEARCH_V1_ALLOCATION_BY_SYMBOL, ResearchV1SharedPortfolioState
from triggertrade.rules import TradingRulesVersion
from triggertrade.rules.trading import draft_from_json
from triggertrade.services import research_backtest_execution as svc
from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType


@dataclass(frozen=True)
class _FakeResponse:
    response_payload: dict[str, Any]


def _record(
    *,
    symbol: str = "PEPEUSDT",
    physical_symbol: str = "1000PEPEUSDT",
    observed_at: str = "2026-08-02T14:40:00+00:00",
    direction: str = "LONG",
    research_cell_references: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    research_set = _research_set()
    trigger_evidence = _trigger_evidence()
    source_evidence_digest = canonical_json_digest(
        {
            "producer": "research_v1_historical_set_formation@1",
            "set_id": research_set.set_id,
            "set_version": research_set.set_version,
            "set_digest": research_set_digest(research_set),
            "trigger_evaluations": [
                {
                    "trigger_id": item["trigger_id"],
                    "trigger_version": item["trigger_version"],
                    "condition_result": item["condition_result"],
                    "output_state": item["output_state"],
                    "evidence_id": item["evidence_id"],
                    "evidence_digest": item["evidence_digest"],
                }
                for item in trigger_evidence
            ],
        }
    )
    slot = datetime.fromisoformat(observed_at.replace("Z", "+00:00")).astimezone(UTC)
    identity_digest = canonical_json_digest(
        {
            "checkpoint": "B5B_SET_RESULT_V1",
            "symbol": symbol.upper(),
            "formation_epoch": int(slot.timestamp()),
            "open_event_id": f"rv1-set-open-{source_evidence_digest[:24]}",
            "open_payload_digest": source_evidence_digest,
        }
    )
    decision_cycle_id = f"decision-cycle-{identity_digest[:32]}"
    set_result_id = f"set-result-{identity_digest[32:64]}"
    refs = tuple(
        research_cell_references
        if research_cell_references is not None
        else (
            {
                "research_id": "RV1-001",
                "arm": "candidate",
                "cell": "candidate",
                "set_version_id": "SET-R-001-V1",
                "rules_version_id": "TRV-R-POS-001-PR-201",
            },
        )
    )
    return {
        "candidate_pair": {"TR-R-001": "0.30", "TR-R-002": "0.50"},
        "classifier_direction": direction,
        "decision_cycle_id": decision_cycle_id,
        "direction": direction,
        "formation_result": "TRUE",
        "observed_at": observed_at,
        "physical_symbol": physical_symbol,
        "rules_version_id": "TRV-R-POS-001-PR-201",
        "set_id": "SET-R-001",
        "set_result_id": set_result_id,
        "set_status": "MATCHED",
        "set_version": "SET-R-001-V1",
        "source_evidence_digest": source_evidence_digest,
        "set_resolution_evidence_digest": "f" * 64,
        "set_resolution_evidence_id": "rv1-set-resolution-test",
        "symbol": symbol,
        "trigger_evidence": trigger_evidence,
        "research_cell_references": refs,
    }


def _trigger_evidence() -> tuple[dict[str, Any], ...]:
    return (
        {
            "trigger_id": "TR-R-001",
            "trigger_version": "v1",
            "metric_ref": "F-001 trigger_result",
            "metric_value": "TRUE",
            "condition_result": True,
            "output_state": "TRUE",
            "evidence_id": "audit-trigger-eval-001",
            "evidence_digest": "1" * 64,
            "metric_evidence_id": "rv1-metric-001",
            "metric_evidence_digest": "2" * 64,
        },
        {
            "trigger_id": "TR-R-002",
            "trigger_version": "v1",
            "metric_ref": "classifier_direction",
            "metric_value": "LONG",
            "condition_result": True,
            "output_state": "LONG",
            "evidence_id": "audit-trigger-eval-002",
            "evidence_digest": "3" * 64,
            "metric_evidence_id": "rv1-metric-002",
            "metric_evidence_digest": "4" * 64,
        },
    )


def _research_set() -> ResearchSetVersion:
    members = (
        ResearchSetTriggerMember(
            position=1,
            trigger_id="TR-R-001",
            trigger_version="v1",
            role="SET_FORMATION_PREDICATE",
            direction_applicability="BOTH",
            condition="abs(move_pct_work) >= theta_move_pct",
            operator=">=",
            threshold="0.50",
            threshold_unit="percent",
            metric_references=("F-001",),
            formula_references=("F-001",),
            output_states=("TRUE", "FALSE", "UNAVAILABLE"),
            required=True,
        ),
        ResearchSetTriggerMember(
            position=2,
            trigger_id="TR-R-002",
            trigger_version="v1",
            role="DIRECTION_PREDICATE",
            direction_applicability="LONG",
            condition="abs(move_pct_work) >= theta_move_pct",
            operator=">=",
            threshold="1.00",
            threshold_unit="percent",
            metric_references=("F-001",),
            formula_references=("F-001",),
            output_states=("TRUE", "FALSE", "UNAVAILABLE"),
            required=True,
        ),
    )
    return ResearchSetVersion(
        set_id="SET-R-001",
        set_version="SET-R-001-V1",
        backend_set_id="SET-R-001",
        backend_version="SET-R-001-V1",
        display_name="Test Set",
        status="ACTIVE",
        source_hypothesis_ids=("RV1-001",),
        source_candidate_ids=("candidate",),
        source_position_ids=("POS-R-001",),
        source_portfolio_ids=("PF-R-001",),
        coin_applicability=("PEPE", "AVAX"),
        excluded_coins=(),
        segment_applicability="ALL",
        timeframe="1m",
        profile_applicability=("BACKTEST",),
        trigger_members=members,
        trigger_composition_logic="ALL_REQUIRED",
        direction_semantics="F-005_GOVERNED",
        edge_behavior={},
        provenance={},
        source_yaml_excerpt="",
        backend_mapping={},
        created_at="2026-09-01T00:00:00+00:00",
        semantic_hash="test-set-hash",
    )


def _rule(rule_id: str, theta: str) -> RuleDefinition:
    return RuleDefinition(
        rule_id=rule_id,
        version="v1",
        name=rule_id,
        status=RuleStatus.ACTIVE,
        asset_scope="RESEARCH_V1",
        rule_type=RuleType.TRIGGER,
        condition="abs(move_pct_work) >= theta_move_pct",
        definition={"metric_ref": "F-001", "params": {"theta_move_pct": theta}},
        created_at="2026-09-01T00:00:00+00:00",
        provenance="test",
        parameter_snapshot={"theta_move_pct": theta},
    )


def _rules(rules_version_id: str = "TRV-R-POS-001-PR-201") -> TradingRulesVersion:
    draft = draft_from_json(
        """
        {
          "position_size_pct": "1.0",
          "take_profit_mode": "FIXED",
          "fixed_take_profit_pct": "2.0",
          "minimum_take_profit_pct": null,
          "stop_loss_pct": "1.0",
          "minimum_risk_reward": "1.0",
          "minimum_net_edge_enabled": false,
          "minimum_net_edge_pct": null,
          "leverage": "1",
          "max_capital_in_positions_pct": "0.30",
          "max_open_positions_enabled": true,
          "max_open_positions": 20,
          "max_positions_per_coin_enabled": true,
          "max_positions_per_coin": 2,
          "direction_mode": "LONG_SHORT",
          "daily_loss_limit_enabled": false,
          "daily_loss_limit_pct": null,
          "maker_fee_rate": "-0.01",
          "taker_fee_rate": "0.055",
          "spread_cost": "0",
          "slippage_cost": "0",
          "funding_cost": "0",
          "coins": [
            {"symbol": "BTCUSDT", "enabled": true, "max_allocation_pct": "0.1"},
            {"symbol": "ETHUSDT", "enabled": true, "max_allocation_pct": "0.1"},
            {"symbol": "SOLUSDT", "enabled": true, "max_allocation_pct": "0.1"},
            {"symbol": "XRPUSDT", "enabled": true, "max_allocation_pct": "0.1"},
            {"symbol": "DOGEUSDT", "enabled": true, "max_allocation_pct": "0.1"},
            {"symbol": "SUIUSDT", "enabled": true, "max_allocation_pct": "0.1"},
            {"symbol": "PEPEUSDT", "enabled": true, "max_allocation_pct": "0.1"},
            {"symbol": "AVAXUSDT", "enabled": true, "max_allocation_pct": "0.1"},
            {"symbol": "LINKUSDT", "enabled": true, "max_allocation_pct": "0.1"},
            {"symbol": "BNBUSDT", "enabled": true, "max_allocation_pct": "0.1"}
          ],
          "metadata": {},
          "stop_loss_mode": "FIXED",
          "minimum_risk_reward_enabled": true,
          "minimum_tranche_capital": null,
          "cooldown_minutes": 0
        }
        """
    )
    return TradingRulesVersion(
        rules_version_id=rules_version_id,
        version="test",
        created_at="2026-09-01T00:00:00+00:00",
        created_from_version_id=None,
        created_source="test",
        change_summary="test",
        config_hash="test",
        schema_version="trading-rules@1",
        draft=draft,
        is_current=False,
    )


def _candle(symbol: str) -> HistoricalCandle:
    opened = datetime(2026, 8, 2, 14, 39, tzinfo=UTC)
    return HistoricalCandle(
        symbol=symbol,
        category="linear",
        timeframe="1m",
        open_time=opened,
        close_time=opened + timedelta(minutes=1),
        open=Decimal("1"),
        high=Decimal("1.01"),
        low=Decimal("0.99"),
        close=Decimal("1"),
        volume=Decimal("1"),
        turnover=Decimal("1"),
        completed=True,
    )


def _instrument(symbol: str) -> FuturesInstrument:
    physical_symbol = "1000PEPEUSDT" if symbol == "PEPEUSDT" else symbol
    return FuturesInstrument(
        symbol=physical_symbol,
        base_coin=physical_symbol.removesuffix("USDT"),
        quote_coin="USDT",
        settle_coin="USDT",
        contract_type="LinearPerpetual",
        status="Trading",
        tick_size=Decimal("0.000001"),
        price_scale=6,
        min_order_qty=Decimal("1"),
        max_order_qty=Decimal("100000000"),
        qty_step=Decimal("1"),
        min_notional_value=Decimal("1"),
        max_market_order_qty=Decimal("100000000"),
        min_leverage=Decimal("1"),
        max_leverage=Decimal("10"),
        leverage_step=Decimal("0.01"),
        launch_time=None,
        delivery_time=None,
        is_tradeable=True,
        updated_at="2026-09-01T00:00:00+00:00",
        catalog_hash=f"catalog-{symbol}",
    )


@pytest.fixture(autouse=True)
def _clear_certified_portfolio_cache():
    svc._CERTIFIED_POPULATION_PORTFOLIOS.clear()
    svc._CERTIFIED_POPULATION_PENDING_EVENTS.clear()
    svc._CERTIFIED_POPULATION_EVENT_JOURNAL.clear()
    yield
    svc._CERTIFIED_POPULATION_PORTFOLIOS.clear()
    svc._CERTIFIED_POPULATION_PENDING_EVENTS.clear()
    svc._CERTIFIED_POPULATION_EVENT_JOURNAL.clear()


def _patch_adapter_loaders(monkeypatch, captured: list[dict[str, Any]]) -> None:
    research_set = _research_set()
    trading_rules = {
        rules_id: _rules(rules_id)
        for rules_id in (
            "TRV-R-POS-001-PR-201",
            "TRV-R-POS-002-PR-201",
            "TRV-R-POS-003-PR-201",
            "TRV-R-POS-001-PR-204",
            "TRV-R-POS-001-PR-205",
            "TRV-R-POS-001-PR-207",
            "TRV-R-POS-001-PR-208",
        )
    }
    monkeypatch.setattr(svc, "_load_certified_research_sets", lambda: {research_set.set_version: research_set})
    monkeypatch.setattr(svc, "_load_certified_trading_rules", lambda: dict(trading_rules))
    monkeypatch.setattr(svc, "_load_certified_trigger_rules", lambda: (_rule("TR-R-001", "0.50"), _rule("TR-R-002", "1.00")))
    monkeypatch.setattr(svc, "_load_certified_candles", lambda symbol, *, end: (_candle(symbol),))
    monkeypatch.setattr(svc, "_certified_instrument", _instrument)
    monkeypatch.setattr(
        svc,
        "_certified_raw_trades_response",
        lambda logical_symbol, cutoff: _FakeResponse({"symbol": logical_symbol, "cutoff": cutoff.isoformat()}),
    )
    monkeypatch.setattr(
        svc,
        "_certified_last_traded_price_response",
        lambda logical_symbol, cutoff: _FakeResponse({"symbol": logical_symbol, "cutoff": cutoff.isoformat()}),
    )

    def fake_run(**kwargs):
        captured.append(kwargs)
        binding = kwargs["symbol_binding"]
        decision_cycle_id = binding["certified_decision_cycle_id"]
        set_result_id = binding["certified_set_result_id"]
        symbol = binding["logical_symbol"]
        return svc.ResearchV1CertifiedPositionBacktestResult(
            backtest_run_id=f"backtest-{decision_cycle_id}",
            status=BacktestStatus.COMPLETED,
            candles_processed=1,
            signals=1,
            intents=1,
            trades=1,
            closed_trades=1,
            rejected_intents=0,
            no_action_count=0,
            technical_failures=0,
            net_pnl=Decimal("1"),
            expectancy=Decimal("1"),
            profit_factor=None,
            max_drawdown=Decimal("0"),
            fees=Decimal("-0.01"),
            funding=Decimal("0"),
            long_trades=1,
            short_trades=0,
            by_regime={"BACKTEST": 1},
            research_v1_certified_position_evidence={
                "decision_cycle_id": decision_cycle_id,
                "set_result_id": set_result_id,
                "symbol": symbol,
                "set_direction": "LONG",
                "backtest_lifecycle": {
                    "execution_mode": "BACKTEST",
                    "post_only_model_rejected": False,
                    "simulated_accepted_resting": True,
                    "simulated_filled": True,
                    "demo_live_path_invoked": False,
                },
            },
            research_v1_portfolio_events=(
                {
                    "action": "RESERVE",
                    "symbol": symbol,
                    "amount": "10",
                    "event_time": "2026-08-02T14:40:00+00:00",
                    "canonical_source": "backtest_canonical_commitment.actual_committed_capital",
                },
            ),
        )

    monkeypatch.setattr(svc, "_run_research_v1_certified_position_backtest", fake_run)


def _patch_uncached_adapter_loaders(monkeypatch, captured: list[dict[str, Any]], calls: dict[str, int]) -> None:
    research_set = _research_set()
    trading_rules = _rules()

    def count(name, value):
        calls[name] = calls.get(name, 0) + 1
        return value

    monkeypatch.setattr(svc, "_load_certified_research_sets_uncached", lambda: count("research_sets", {research_set.set_version: research_set}))
    monkeypatch.setattr(svc, "_load_certified_trigger_rules_uncached", lambda: count("trigger_rules", (_rule("TR-R-001", "0.50"), _rule("TR-R-002", "1.00"))))
    monkeypatch.setattr(svc, "_load_certified_trading_rules_uncached", lambda: count("trading_rules", {trading_rules.rules_version_id: trading_rules}))
    monkeypatch.setattr(svc, "_load_certified_candles_uncached", lambda symbol, *, start, end: count(f"candles:{symbol}", (_candle(symbol),)))
    monkeypatch.setattr(svc, "_certified_instrument_uncached", lambda symbol: count(f"instrument:{symbol}", _instrument(symbol)))
    monkeypatch.setattr(svc, "_certified_archive_manifest_uncached", lambda logical_symbol, archive_date: count(f"manifest:{logical_symbol}:{archive_date}", object()))
    monkeypatch.setattr(
        svc,
        "_certified_raw_trades_response_uncached",
        lambda logical_symbol, cutoff: count("raw", _FakeResponse({"symbol": logical_symbol, "cutoff": cutoff.isoformat()})),
    )
    monkeypatch.setattr(
        svc,
        "_certified_last_traded_price_response_uncached",
        lambda logical_symbol, cutoff: count("ltp", _FakeResponse({"symbol": logical_symbol, "cutoff": cutoff.isoformat()})),
    )

    def fake_run(**kwargs):
        captured.append(kwargs)
        binding = kwargs["symbol_binding"]
        return svc.ResearchV1CertifiedPositionBacktestResult(
            backtest_run_id=f"backtest-{binding['certified_decision_cycle_id']}",
            status=BacktestStatus.COMPLETED,
            candles_processed=1,
            signals=1,
            intents=1,
            trades=1,
            closed_trades=1,
            rejected_intents=0,
            no_action_count=0,
            technical_failures=0,
            net_pnl=Decimal("1"),
            expectancy=Decimal("1"),
            profit_factor=None,
            max_drawdown=Decimal("0"),
            fees=Decimal("-0.01"),
            funding=Decimal("0"),
            long_trades=1,
            short_trades=0,
            by_regime={"BACKTEST": 1},
            research_v1_certified_position_evidence={
                "decision_cycle_id": binding["certified_decision_cycle_id"],
                "set_result_id": binding["certified_set_result_id"],
                "symbol": binding["logical_symbol"],
                "set_direction": "LONG",
                "position_decision": "APPROVE",
                "portfolio_grant": "GRANTED",
                "order_spec": {"id": "order-spec-test"},
                "backtest_lifecycle": {
                    "execution_mode": "BACKTEST",
                    "status": "CLOSED",
                    "reason_code": "TAKE_PROFIT",
                    "closed_result": {"net_pnl": "1", "fees": "-0.01", "funding": "0"},
                },
            },
            research_v1_portfolio_events=(
                {
                    "action": "RESERVE",
                    "symbol": binding["logical_symbol"],
                    "amount": "10",
                    "event_time": "2026-08-02T14:40:00+00:00",
                    "canonical_source": "backtest_canonical_commitment.actual_committed_capital",
                },
                {
                    "action": "RELEASE",
                    "symbol": binding["logical_symbol"],
                    "amount": "10",
                    "event_time": "2026-08-02T14:41:00+00:00",
                    "canonical_source": "backtest_lifecycle.closed_finality.actual_committed_capital",
                    "lifecycle_state": "CLOSED",
                },
            ),
        )

    monkeypatch.setattr(svc, "_run_research_v1_certified_position_backtest", fake_run)


def _output_dir(name: str) -> Path:
    path = Path(".tmp") / "certified-match-adapter" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_certified_match_adapter_binds_record_to_canonical_backtest(monkeypatch):
    captured: list[dict[str, Any]] = []
    _patch_adapter_loaders(monkeypatch, captured)
    record = _record()

    result = svc.run_research_v1_certified_population_backtest(
        record=record,
        artifact={"candidate_pair": record["candidate_pair"], "data_window": {"end": "2026-08-19T00:00:00Z"}},
        output_dir=_output_dir("single"),
    )

    assert result["status"] == BacktestStatus.COMPLETED.value
    assert result["evidence"]["decision_cycle_id"] == record["decision_cycle_id"]
    assert result["evidence"]["set_result_id"] == record["set_result_id"]
    assert result["evidence"]["certified_match"] == {
        "decision_cycle_id": record["decision_cycle_id"],
        "set_result_id": record["set_result_id"],
        "symbol": "PEPEUSDT",
        "physical_symbol": "1000PEPEUSDT",
        "direction": "LONG",
        "observed_at": "2026-08-02T14:40:00+00:00",
        "set_version": "SET-R-001-V1",
        "research_cell_reference_count": 1,
    }
    assert result["evidence"]["backtest_lifecycle"]["execution_mode"] == "BACKTEST"
    assert result["evidence"]["backtest_lifecycle"]["demo_live_path_invoked"] is False

    call = captured[0]
    certified_resolution = call["certified_set_resolution"]
    assert certified_resolution.decision_cycle_id == record["decision_cycle_id"]
    assert certified_resolution.set_result_id == record["set_result_id"]
    assert certified_resolution.direction == record["direction"]
    assert certified_resolution.set_version == record["set_version"]
    assert call["trigger_set"].version == "SET-R-001-V1"
    assert call["research_set"].set_version == "SET-R-001-V1"
    assert call["rules"].rules_version_id == "TRV-R-POS-001-PR-201"
    assert call["instrument"].symbol == "1000PEPEUSDT"
    assert call["candles"][0].symbol == "PEPEUSDT"
    assert call["symbol_binding"]["logical_symbol"] == "PEPEUSDT"
    assert call["symbol_binding"]["instrument_symbol"] == "1000PEPEUSDT"
    assert call["symbol_binding"]["research_cell_references"] == tuple(record["research_cell_references"])
    assert call["symbol_binding"]["execution_context_id"] == result["execution_context"]["execution_context_id"]
    assert call["symbol_binding"]["research_id"] == "RV1-001"
    assert {rule.rule_id: rule.parameter_snapshot["theta_move_pct"] for rule in call["trigger_rules"]} == {
        "TR-R-001": "0.30",
        "TR-R-002": "0.50",
    }


def test_certified_match_adapter_executes_each_research_cell_requested_rules(monkeypatch):
    captured: list[dict[str, Any]] = []
    _patch_adapter_loaders(monkeypatch, captured)
    refs = (
        {
            "research_id": "R-001",
            "arm": "base",
            "cell": "base",
            "set_version_id": "SET-R-001-V1",
            "rules_version_id": "TRV-R-POS-001-PR-201",
        },
        {
            "research_id": "R-012",
            "arm": "pos-002",
            "cell": "pos-002",
            "set_version_id": "SET-R-001-V1",
            "rules_version_id": "TRV-R-POS-002-PR-201",
        },
        {
            "research_id": "R-013",
            "arm": "pos-003",
            "cell": "pos-003",
            "set_version_id": "SET-R-001-V1",
            "rules_version_id": "TRV-R-POS-003-PR-201",
        },
        {
            "research_id": "R-027",
            "arm": "pr-207",
            "cell": "pr-207",
            "set_version_id": "SET-R-001-V1",
            "rules_version_id": "TRV-R-POS-001-PR-207",
        },
        {
            "research_id": "R-029",
            "arm": "factor-pr-207",
            "cell": "factor-pr-207",
            "set_version_id": "SET-R-001-V1",
            "rules_version_id": "TRV-R-POS-001-PR-207",
        },
        {
            "research_id": "R-030",
            "arm": "factor-pos-003",
            "cell": "factor-pos-003",
            "set_version_id": "SET-R-001-V1",
            "rules_version_id": "TRV-R-POS-003-PR-201",
        },
    )
    record = _record(research_cell_references=refs)

    result = svc.run_research_v1_certified_population_backtest(
        record=record,
        artifact={"candidate_pair": record["candidate_pair"]},
        output_dir=_output_dir("cell-rules"),
    )

    assert result["cell_execution_count"] == len(refs)
    executed = [(call["symbol_binding"]["research_id"], call["rules"].rules_version_id) for call in captured]
    assert ("R-012", "TRV-R-POS-002-PR-201") in executed
    assert ("R-013", "TRV-R-POS-003-PR-201") in executed
    assert ("R-027", "TRV-R-POS-001-PR-207") in executed
    assert ("R-029", "TRV-R-POS-001-PR-207") in executed
    assert ("R-030", "TRV-R-POS-003-PR-201") in executed
    assert all(call["portfolio_state"].committed_capital == Decimal("0") for call in captured)
    assert len({call["symbol_binding"]["execution_context_id"] for call in captured}) == len(refs)
    assert all(
        call["certified_set_resolution"].decision_cycle_id == record["decision_cycle_id"]
        and call["certified_set_resolution"].set_result_id == record["set_result_id"]
        for call in captured
    )


def test_certified_match_adapter_fails_closed_on_cell_set_version_mismatch():
    record = _record(
        research_cell_references=(
            {
                "research_id": "R-001",
                "arm": "bad",
                "cell": "bad",
                "set_version_id": "SET-R-999-V1",
                "rules_version_id": "TRV-R-POS-001-PR-201",
            },
        )
    )

    with pytest.raises(svc.HistoricalDataError, match="CELL_SET_VERSION_MISMATCH"):
        svc._certified_execution_contexts(record)


def test_certified_trading_rules_package_loads_required_research_versions():
    required = {
        "TRV-R-POS-001-PR-201",
        "TRV-R-POS-001-PR-204",
        "TRV-R-POS-001-PR-205",
        "TRV-R-POS-001-PR-207",
        "TRV-R-POS-001-PR-208",
        "TRV-R-POS-002-PR-201",
        "TRV-R-POS-003-PR-201",
        "TRV-R-POS-005-PR-201",
        "TRV-R-POS-006-PR-201",
        "TRV-R-POS-007-PR-201",
        "TRV-R-POS-008-PR-201",
        "TRV-R-POS-010-PR-201",
        "TRV-R-POS-011-PR-201",
        "TRV-R-POS-012-PR-201",
        "TRV-R-POS-013-PR-201",
        "TRV-R-POS-014-PR-201",
    }

    loaded = set(svc._load_certified_trading_rules_uncached())

    assert required <= loaded


def test_certified_match_adapter_preserves_shared_portfolio_and_unique_identities(monkeypatch):
    captured: list[dict[str, Any]] = []
    _patch_adapter_loaders(monkeypatch, captured)

    first = _record()
    second = _record(
        symbol="AVAXUSDT",
        physical_symbol="AVAXUSDT",
        observed_at="2026-08-03T00:05:00+00:00",
    )

    output_dir = _output_dir("batch")
    first_result = svc.run_research_v1_certified_match_backtest(record=first, artifact={"candidate_pair": first["candidate_pair"]}, output_dir=output_dir)
    second_result = svc.run_research_v1_certified_match_backtest(record=second, artifact={"candidate_pair": second["candidate_pair"]}, output_dir=output_dir)

    assert first_result["evidence"]["decision_cycle_id"] == first["decision_cycle_id"]
    assert second_result["evidence"]["decision_cycle_id"] == second["decision_cycle_id"]
    assert len(captured) == 2
    assert isinstance(captured[0]["portfolio_state"], ResearchV1SharedPortfolioState)
    assert captured[0]["portfolio_state"].committed_capital == Decimal("0")
    assert captured[1]["portfolio_state"].committed_capital == Decimal("10")
    assert captured[1]["symbol_binding"]["instrument_symbol"] == "AVAXUSDT"
    assert captured[0]["symbol_binding"]["certified_set_result_id"] != captured[1]["symbol_binding"]["certified_set_result_id"]


def test_certified_match_adapter_fails_closed_on_identity_mismatch(monkeypatch):
    captured: list[dict[str, Any]] = []
    _patch_adapter_loaders(monkeypatch, captured)

    def mismatched_run(**kwargs):
        return svc.ResearchV1CertifiedPositionBacktestResult(
            backtest_run_id="bad",
            status=BacktestStatus.COMPLETED,
            candles_processed=1,
            signals=1,
            intents=1,
            trades=1,
            closed_trades=1,
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
            research_v1_certified_position_evidence={
                "decision_cycle_id": "different",
                "set_result_id": "different",
            },
        )

    monkeypatch.setattr(svc, "_run_research_v1_certified_position_backtest", mismatched_run)

    with pytest.raises(svc.HistoricalDataError, match="CERTIFIED_IDENTITY_MISMATCH"):
        svc.run_research_v1_certified_population_backtest(
            record=_record(),
            artifact={"candidate_pair": {"TR-R-001": "0.30", "TR-R-002": "0.50"}},
            output_dir=_output_dir("mismatch"),
        )


def test_certified_match_adapter_reuses_immutable_input_cache(monkeypatch):
    captured: list[dict[str, Any]] = []
    calls: dict[str, int] = {}
    _patch_uncached_adapter_loaders(monkeypatch, captured, calls)
    svc.reset_research_v1_certified_backtest_caches(include_portfolio=True)
    record = _record()
    out = _output_dir("cache")

    svc.run_research_v1_certified_population_backtest(record=record, artifact={"candidate_pair": record["candidate_pair"]}, output_dir=out)
    svc.run_research_v1_certified_population_backtest(
        record=_record(observed_at="2026-08-02T14:45:00+00:00"),
        artifact={"candidate_pair": record["candidate_pair"]},
        output_dir=out,
    )

    stats = svc.research_v1_certified_backtest_cache_stats()
    assert calls["research_sets"] == 1
    assert calls["trading_rules"] == 1
    assert calls["trigger_rules"] == 1
    assert calls["candles:1000PEPEUSDT"] == 1
    assert calls["candles:BTCUSDT"] == 1
    assert calls["raw"] == 2
    assert calls["ltp"] == 2
    assert stats["research_sets"]["hits"] >= 1
    assert stats["physical_candles"]["hits"] >= 2
    assert stats["raw_trades"]["misses"] == 2
    assert stats["last_traded_price"]["misses"] == 2
    assert captured[0]["symbol_binding"]["instrument_symbol"] == "1000PEPEUSDT"


def test_certified_match_adapter_cached_and_uncached_results_are_equivalent(monkeypatch):
    captured: list[dict[str, Any]] = []
    calls: dict[str, int] = {}
    _patch_uncached_adapter_loaders(monkeypatch, captured, calls)
    record = _record()

    svc.reset_research_v1_certified_backtest_caches(include_portfolio=True)
    uncached = svc.run_research_v1_certified_population_backtest(
        record=record,
        artifact={"candidate_pair": record["candidate_pair"]},
        output_dir=_output_dir("equivalence-uncached"),
    )

    svc.reset_research_v1_certified_backtest_caches(include_portfolio=True)
    # Prime immutable inputs, then run the same record from the same initial portfolio.
    svc.run_research_v1_certified_population_backtest(
        record=record,
        artifact={"candidate_pair": record["candidate_pair"]},
        output_dir=_output_dir("equivalence-prime"),
    )
    svc._CERTIFIED_POPULATION_PORTFOLIOS.clear()
    cached = svc.run_research_v1_certified_population_backtest(
        record=record,
        artifact={"candidate_pair": record["candidate_pair"]},
        output_dir=_output_dir("equivalence-cached"),
    )

    for key in ("decision_cycle_id", "set_result_id", "set_direction", "position_decision", "portfolio_grant", "order_spec", "backtest_lifecycle"):
        assert uncached["evidence"][key] == cached["evidence"][key]
    assert uncached["research_v1_portfolio_events"] == cached["research_v1_portfolio_events"]
    assert uncached["portfolio_snapshot"] == cached["portfolio_snapshot"]


def test_certified_population_checkpoint_and_resume_without_duplicates():
    output_dir = _output_dir("checkpoint")
    for name in (
        "lifecycle_378_checkpoint_results.jsonl",
        "lifecycle_378_checkpoint_errors.jsonl",
        "lifecycle_378_results.json",
        "lifecycle_378_errors.json",
        "lifecycle_378_summary.json",
        "lifecycle_378_rows.csv",
    ):
        path = output_dir / name
        if path.exists():
            path.unlink()
    records = (
        _record(observed_at="2026-08-02T14:40:00+00:00"),
        _record(observed_at="2026-08-02T14:45:00+00:00"),
        _record(observed_at="2026-08-02T14:50:00+00:00"),
    )
    calls: list[str] = []

    def fake_adapter(*, record, artifact, output_dir):
        calls.append(record["decision_cycle_id"])
        return {
            "status": "COMPLETED",
            "evidence": {
                "decision_cycle_id": record["decision_cycle_id"],
                "set_result_id": record["set_result_id"],
                "backtest_lifecycle": {"status": "CLOSED", "reason_code": "TAKE_PROFIT"},
            },
            "research_v1_portfolio_events": (),
            "portfolio_snapshot": {"committed_capital": "0"},
        }

    first = svc.run_research_v1_certified_population_checkpointed_backtest(
        records=records,
        artifact={"candidate_pair": {"TR-R-001": "0.30", "TR-R-002": "0.50"}},
        output_dir=output_dir,
        max_records=2,
        adapter=fake_adapter,
    )
    second = svc.run_research_v1_certified_population_checkpointed_backtest(
        records=records,
        artifact={"candidate_pair": {"TR-R-001": "0.30", "TR-R-002": "0.50"}},
        output_dir=output_dir,
        adapter=fake_adapter,
    )

    results = (output_dir / "lifecycle_378_checkpoint_results.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert first["results"] == 2
    assert second["results"] == 3
    assert calls == [record["decision_cycle_id"] for record in records]
    assert len(results) == 3
    identities = [svc._certified_checkpoint_identity(json.loads(line)["record"]) for line in results]
    assert len(identities) == len(set(identities))
    assert (output_dir / "lifecycle_378_results.json").exists()
    assert (output_dir / "lifecycle_378_summary.json").exists()


def test_checkpoint_resume_preserves_funded_closed_result():
    output_dir = _output_dir("checkpoint-funded")
    for name in (
        "lifecycle_378_checkpoint_results.jsonl",
        "lifecycle_378_checkpoint_errors.jsonl",
        "lifecycle_378_results.json",
        "lifecycle_378_errors.json",
        "lifecycle_378_summary.json",
        "lifecycle_378_rows.csv",
    ):
        path = output_dir / name
        if path.exists():
            path.unlink()
    records = (
        _record(observed_at="2026-08-02T14:40:00+00:00"),
        _record(observed_at="2026-08-02T14:45:00+00:00"),
    )
    calls: list[str] = []

    def fake_adapter(*, record, artifact, output_dir):
        calls.append(record["decision_cycle_id"])
        return {
            "status": "COMPLETED",
            "evidence": {
                "decision_cycle_id": record["decision_cycle_id"],
                "set_result_id": record["set_result_id"],
                "backtest_lifecycle": {
                    "status": "CLOSED",
                    "reason_code": "TAKE_PROFIT",
                    "closed_result": {
                        "gross_pnl": "10.00000",
                        "fees": "-0.08050",
                        "funding": "-0.100",
                        "net_pnl": "9.81950",
                    },
                },
            },
            "research_v1_portfolio_events": (),
            "portfolio_snapshot": {"committed_capital": "0"},
        }

    first = svc.run_research_v1_certified_population_checkpointed_backtest(
        records=records,
        artifact={"candidate_pair": {"TR-R-001": "0.30", "TR-R-002": "0.50"}},
        output_dir=output_dir,
        max_records=1,
        adapter=fake_adapter,
    )
    second = svc.run_research_v1_certified_population_checkpointed_backtest(
        records=records,
        artifact={"candidate_pair": {"TR-R-001": "0.30", "TR-R-002": "0.50"}},
        output_dir=output_dir,
        adapter=fake_adapter,
    )

    checkpoint_rows = [
        json.loads(line)
        for line in (output_dir / "lifecycle_378_checkpoint_results.jsonl").read_text(encoding="utf-8").strip().splitlines()
    ]
    final_rows = json.loads((output_dir / "lifecycle_378_results.json").read_text(encoding="utf-8"))

    assert first["results"] == 1
    assert second["results"] == 2
    assert calls == [record["decision_cycle_id"] for record in records]
    assert len(checkpoint_rows) == 2
    assert len(final_rows) == 2
    assert checkpoint_rows[0]["result"]["evidence"]["backtest_lifecycle"]["closed_result"]["funding"] == "-0.100"
    assert final_rows[0]["result"]["evidence"]["backtest_lifecycle"]["closed_result"]["net_pnl"] == "9.81950"


def test_certified_checkpoint_identity_includes_research_cell_context():
    refs = (
        {
            "research_id": "R-024",
            "arm": "pr-204",
            "cell": "pr-204",
            "set_version_id": "SET-R-001-V1",
            "rules_version_id": "TRV-R-POS-001-PR-204",
        },
        {
            "research_id": "R-025",
            "arm": "pr-205",
            "cell": "pr-205",
            "set_version_id": "SET-R-001-V1",
            "rules_version_id": "TRV-R-POS-001-PR-205",
        },
    )
    records = svc._certified_population_execution_records((_record(research_cell_references=refs),))

    identities = [svc._certified_checkpoint_identity(item) for item in records]

    assert len(records) == 2
    assert len(set(identities)) == 2
    assert {identity[3] for identity in identities} == {"R-024", "R-025"}
    assert {identity[6] for identity in identities} == {"TRV-R-POS-001-PR-204", "TRV-R-POS-001-PR-205"}


def test_event_time_portfolio_does_not_apply_future_release_before_same_timestamp_decisions():
    portfolio = svc._certified_initial_portfolio(_rules())
    t0 = "2026-08-02T14:40:00+00:00"
    t1 = "2026-08-02T15:20:00+00:00"

    first_events = (
        {
            "action": "RESERVE",
            "symbol": "PEPEUSDT",
            "actual_committed_capital": "10",
            "event_time": t0,
            "canonical_source": "order_spec.economics.actual_committed_capital",
            "order_spec_id": "order-1",
        },
        {
            "action": "RELEASE",
            "symbol": "PEPEUSDT",
            "actual_committed_capital": "10",
            "event_time": t1,
            "canonical_source": "backtest_lifecycle.closed_finality.actual_committed_capital",
            "lifecycle_state": "CLOSED",
            "order_spec_id": "order-1",
        },
    )
    second_events = (
        {
            "action": "RESERVE",
            "symbol": "PEPEUSDT",
            "actual_committed_capital": "10",
            "event_time": t0,
            "canonical_source": "order_spec.economics.actual_committed_capital",
            "order_spec_id": "order-2",
        },
        {
            "action": "RELEASE",
            "symbol": "PEPEUSDT",
            "actual_committed_capital": "10",
            "event_time": t1,
            "canonical_source": "backtest_lifecycle.closed_finality.actual_committed_capital",
            "lifecycle_state": "CLOSED",
            "order_spec_id": "order-2",
        },
    )

    portfolio, pending = svc.apply_research_v1_event_time_portfolio_events(
        portfolio,
        new_events=first_events,
        as_of=t0,
    )
    portfolio, pending = svc.apply_research_v1_event_time_portfolio_events(
        portfolio,
        pending_events=pending,
        new_events=second_events,
        as_of=t0,
    )

    assert portfolio.open_positions_by_symbol_map["PEPEUSDT"] == 2
    assert portfolio.committed_capital == Decimal("20")
    grant_state = svc._research_v1_portfolio_state(portfolio, symbol="PEPEUSDT", as_of=t0)
    pepe_state = next(item for item in grant_state.coins if item.symbol == "PEPEUSDT")
    assert pepe_state.buckets.committed_tranches == 2
    assert svc._research_v1_portfolio_grant_policy(
        rules=_rules(),
        portfolio_state=portfolio,
        symbol="PEPEUSDT",
    ).max_positions_per_coin == 2
    assert len(pending) == 2

    later, pending = svc.apply_research_v1_event_time_portfolio_events(
        portfolio,
        pending_events=pending,
        as_of=t1,
    )

    assert later.open_positions_by_symbol_map.get("PEPEUSDT", 0) == 0
    assert later.committed_capital == Decimal("0")
    assert pending == ()


def test_event_time_portfolio_keeps_accepted_not_filled_reservation_pending():
    portfolio = svc._certified_initial_portfolio(_rules())
    t0 = "2026-08-02T14:40:00+00:00"
    later = "2026-08-03T14:40:00+00:00"

    portfolio, pending = svc.apply_research_v1_event_time_portfolio_events(
        portfolio,
        new_events=(
            {
                "action": "RESERVE",
                "symbol": "SUIUSDT",
                "actual_committed_capital": "10",
                "event_time": t0,
                "canonical_source": "order_spec.economics.actual_committed_capital",
                "order_spec_id": "accepted-not-filled",
            },
        ),
        as_of=t0,
    )
    portfolio, pending = svc.apply_research_v1_event_time_portfolio_events(
        portfolio,
        pending_events=pending,
        as_of=later,
    )

    assert portfolio.open_positions_by_symbol_map["SUIUSDT"] == 1
    assert portfolio.committed_capital == Decimal("10")
    assert pending == ()


def test_r014_witness_future_reservations_are_invisible_to_past_decision():
    rules = _rules()
    key = "r014-witness"
    svc._CERTIFIED_POPULATION_EVENT_JOURNAL[key] = [
        {
            "action": "RESERVE",
            "symbol": "PEPEUSDT",
            "actual_committed_capital": "10",
            "event_time": "2026-07-26T23:10:00+00:00",
            "canonical_source": "order_spec.economics.actual_committed_capital",
            "order_spec_id": "future-1",
        },
        {
            "action": "RESERVE",
            "symbol": "PEPEUSDT",
            "actual_committed_capital": "10",
            "event_time": "2026-08-12T23:25:00+00:00",
            "canonical_source": "order_spec.economics.actual_committed_capital",
            "order_spec_id": "future-2",
        },
    ]

    before, pending = svc._certified_portfolio_state_at(
        portfolio_key=key,
        rules=rules,
        as_of=datetime(2026, 7, 26, 2, 25, tzinfo=UTC),
    )
    after_first, pending_after_first = svc._certified_portfolio_state_at(
        portfolio_key=key,
        rules=rules,
        as_of=datetime(2026, 7, 26, 23, 10, tzinfo=UTC),
    )

    assert before.open_positions_by_symbol_map.get("PEPEUSDT", 0) == 0
    assert before.committed_capital == Decimal("0")
    assert len(pending) == 2
    assert after_first.open_positions_by_symbol_map["PEPEUSDT"] == 1
    assert after_first.committed_capital == Decimal("10")
    assert len(pending_after_first) == 1


def test_checkpoint_resume_rebuilds_causal_state_from_event_journal(monkeypatch):
    output_dir = _output_dir("checkpoint-causal")
    for name in (
        "lifecycle_378_checkpoint_results.jsonl",
        "lifecycle_378_checkpoint_errors.jsonl",
        "lifecycle_378_results.json",
        "lifecycle_378_errors.json",
        "lifecycle_378_summary.json",
        "lifecycle_378_rows.csv",
    ):
        path = output_dir / name
        if path.exists():
            path.unlink()
    refs = (
        {
            "research_id": "R-014",
            "arm": "candidate",
            "cell": "candidate",
            "set_version_id": "SET-R-001-V1",
            "rules_version_id": "TRV-R-POS-001-PR-201",
        },
    )
    future = _record(observed_at="2026-07-26T23:10:00+00:00", research_cell_references=refs)
    earlier = _record(observed_at="2026-07-26T02:25:00+00:00", research_cell_references=refs)
    calls: list[tuple[str, str]] = []

    def fake_adapter(*, record, artifact, output_dir):
        context = svc._certified_execution_contexts(record)[0]
        portfolio_key = svc._certified_portfolio_key(
            artifact=artifact,
            output_dir=output_dir,
            rules_version_id=context["rules_version_id"],
            execution_context_id=context["portfolio_context_id"],
        )
        state, _pending = svc._certified_portfolio_state_at(
            portfolio_key=portfolio_key,
            rules=_rules(),
            as_of=datetime.fromisoformat(str(record["observed_at"]).replace("Z", "+00:00")).astimezone(UTC),
        )
        calls.append((str(record["observed_at"]), str(state.committed_capital)))
        return {
            "status": "COMPLETED",
            "evidence": {
                "decision_cycle_id": record["decision_cycle_id"],
                "set_result_id": record["set_result_id"],
                "backtest_lifecycle": {"status": "CLOSED", "reason_code": "TAKE_PROFIT"},
            },
            "research_v1_portfolio_events": (
                {
                    "action": "RESERVE",
                    "symbol": "PEPEUSDT",
                    "actual_committed_capital": "10",
                    "event_time": record["observed_at"],
                    "canonical_source": "order_spec.economics.actual_committed_capital",
                    "order_spec_id": f"order-{record['observed_at']}",
                },
            ),
            "portfolio_snapshot": {"committed_capital": "0"},
        }

    first = svc.run_research_v1_certified_population_checkpointed_backtest(
        records=(future, earlier),
        artifact={"candidate_pair": {"TR-R-001": "0.30", "TR-R-002": "0.50"}},
        output_dir=output_dir,
        max_records=1,
        adapter=fake_adapter,
    )
    second = svc.run_research_v1_certified_population_checkpointed_backtest(
        records=(future, earlier),
        artifact={"candidate_pair": {"TR-R-001": "0.30", "TR-R-002": "0.50"}},
        output_dir=output_dir,
        adapter=fake_adapter,
    )

    assert first["results"] == 1
    assert second["results"] == 2
    assert calls == [
        ("2026-07-26T02:25:00+00:00", "0"),
        ("2026-07-26T23:10:00+00:00", "10"),
    ]
