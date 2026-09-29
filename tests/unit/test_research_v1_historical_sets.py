from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
import json
import inspect

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.persistence.postgres_research_set_registry import ResearchSetVersion, research_set_from_package_record
from triggertrade.research_v1_execution import build_research_v1_execution_definition
from triggertrade.research_v1_historical_sets import (
    resolve_research_v1_historical_set,
    resolve_research_v1_historical_set_from_trigger_evaluations,
)
from triggertrade.research_v1_historical_triggers import HistoricalTriggerEvaluation
from triggertrade.set_engine import SetMatchStatus, SetResolutionRequest, SetResultResolutionRequest
from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType
from triggertrade.triggers.contracts import Signal, SignalType

from tests.unit.test_research_v1_historical_triggers import (
    _btc_context_source_minutes,
    _eth_classifier_source_minutes,
    _instrument,
    _raw_trade,
    _raw_trade_response,
    _rule,
)



def test_durable_set_request_keeps_handoff_facts_required_and_historical_request_does_not():
    durable = inspect.signature(SetResolutionRequest)
    pure = inspect.signature(SetResultResolutionRequest)

    assert durable.parameters["handoff_facts"].default is inspect.Parameter.empty
    assert "handoff_facts" not in pure.parameters



def test_historical_set_loads_exact_pinned_trigger_versions_and_factual_trigger_evidence():
    research_set = _research_set("SET-R-001-V1")
    rules = _rules_for(research_set)
    candles = _eth_classifier_source_minutes()
    btc = _btc_context_source_minutes(days=16)
    cutoff = _latest_close(candles)
    raw_trades = _raw_trade_response(
        logical_symbol="ETHUSDT",
        interval_start=cutoff - timedelta(minutes=5),
        interval_end=cutoff,
        records=(
            _raw_trade("eth-buy", cutoff - timedelta(minutes=5), side="BUY", notional="80", logical_symbol="ETHUSDT"),
            _raw_trade("eth-sell", cutoff - timedelta(minutes=3), side="SELL", notional="20", logical_symbol="ETHUSDT"),
        ),
    )

    resolution = resolve_research_v1_historical_set(
        research_set=research_set,
        trigger_rules=rules,
        candles=candles,
        symbol="ETHUSDT",
        instrument_metadata=_instrument("ETHUSDT"),
        companion_candles={"BTCUSDT": btc},
        companion_instrument_metadata={"BTCUSDT": _instrument("BTCUSDT")},
        raw_trades_pages=(raw_trades,),
    )

    assert resolution.set_id == "SET-R-001"
    assert resolution.set_version == "SET-R-001-V1"
    assert [(item.trigger_id, item.trigger_version) for item in resolution.trigger_evaluations] == [
        (member.trigger_id, member.trigger_version) for member in research_set.trigger_members
    ]
    assert all(item.evidence_id.startswith("rv1-trigger-eval-") for item in resolution.trigger_evaluations)
    assert resolution.configuration_binding["set_config_id"] == "SET-R-001"
    assert resolution.configuration_binding["set_config_version"] == "SET-R-001-V1"
    assert resolution.result_payload["set_result"]["direction_scope"] == "F005_GOVERNED"
    assert "market_handoff" not in resolution.result_payload


def test_historical_btc_set_uses_set_owned_generic_branch_direction_without_candle_color():
    research_set = _research_set("SET-R-BTC-001-V2")
    evaluations = _evaluations_for_set(
        research_set,
        {
            "TR-R-002": ("TRUE", True),
            "TR-R-030": ("FALSE", False),
            "TR-R-BTC-001": ("LONG", True),
            "TR-R-BTC-002": ("FALSE", False),
            "TR-R-BTC-005": ("TRUE", True),
            "TR-R-BTC-006": ("TRUE", True),
            "TR-R-BTC-007": ("TRUE", True),
            "TR-R-BTC-008": ("TRUE", True),
        },
    )

    resolution = resolve_research_v1_historical_set_from_trigger_evaluations(
        research_set=research_set,
        trigger_evaluations=evaluations,
        trigger_rules=_rules_for(research_set),
        symbol="BTCUSDT",
    )

    assert resolution.status == SetMatchStatus.MATCHED.value
    assert resolution.formation_result == "TRUE"
    assert resolution.direction == "LONG"
    assert resolution.result_payload["set_result"]["selected_branch_id"] == "TR-R-BTC-001"
    assert resolution.result_payload["set_result"]["generic_branches"][0]["direction"] == "LONG"


def test_historical_btc_set_zero_or_unavailable_never_becomes_forced_true():
    research_set = _research_set("SET-R-BTC-001-V2")
    zero = resolve_research_v1_historical_set_from_trigger_evaluations(
        research_set=research_set,
        trigger_evaluations=_evaluations_for_set(
            research_set,
            {
                "TR-R-002": ("TRUE", True),
                "TR-R-030": ("FALSE", False),
                "TR-R-BTC-001": ("ZERO", False),
                "TR-R-BTC-002": ("ZERO", False),
                "TR-R-BTC-005": ("TRUE", True),
                "TR-R-BTC-006": ("TRUE", True),
                "TR-R-BTC-007": ("TRUE", True),
                "TR-R-BTC-008": ("TRUE", True),
            },
        ),
        trigger_rules=_rules_for(research_set),
        symbol="BTCUSDT",
    )
    unavailable = resolve_research_v1_historical_set_from_trigger_evaluations(
        research_set=research_set,
        trigger_evaluations=_evaluations_for_set(
            research_set,
            {
                "TR-R-002": ("TRUE", True),
                "TR-R-030": ("FALSE", False),
                "TR-R-BTC-001": ("UNAVAILABLE", False),
                "TR-R-BTC-002": ("FALSE", False),
                "TR-R-BTC-005": ("TRUE", True),
                "TR-R-BTC-006": ("TRUE", True),
                "TR-R-BTC-007": ("TRUE", True),
                "TR-R-BTC-008": ("TRUE", True),
            },
        ),
        trigger_rules=_rules_for(research_set),
        symbol="BTCUSDT",
    )

    assert zero.status == SetMatchStatus.UNMATCHED.value
    assert zero.formation_result == "FALSE"
    assert zero.direction == "NONE"
    assert unavailable.status == SetMatchStatus.UNMATCHED.value
    assert unavailable.formation_result == "UNAVAILABLE"
    assert unavailable.reason_code == "FORMATION_UNAVAILABLE"


def test_historical_set_identities_are_deterministic_and_change_with_trigger_evidence():
    research_set = _research_set("SET-R-BTC-001-V2")
    evaluations = _evaluations_for_set(
        research_set,
        {
            "TR-R-002": ("TRUE", True),
            "TR-R-030": ("FALSE", False),
            "TR-R-BTC-001": ("LONG", True),
            "TR-R-BTC-002": ("FALSE", False),
            "TR-R-BTC-005": ("TRUE", True),
            "TR-R-BTC-006": ("TRUE", True),
            "TR-R-BTC-007": ("TRUE", True),
            "TR-R-BTC-008": ("TRUE", True),
        },
    )

    first = resolve_research_v1_historical_set_from_trigger_evaluations(
        research_set=research_set,
        trigger_evaluations=evaluations,
        trigger_rules=_rules_for(research_set),
        symbol="BTCUSDT",
    )
    second = resolve_research_v1_historical_set_from_trigger_evaluations(
        research_set=research_set,
        trigger_evaluations=tuple(reversed(evaluations)),
        trigger_rules=_rules_for(research_set),
        symbol="BTCUSDT",
    )
    changed = resolve_research_v1_historical_set_from_trigger_evaluations(
        research_set=research_set,
        trigger_evaluations=tuple(
            replace(evaluation, evidence_digest="f" * 64, evidence_id="rv1-trigger-eval-changed")
            if evaluation.trigger_id == "TR-R-BTC-005"
            else evaluation
            for evaluation in evaluations
        ),
        trigger_rules=_rules_for(research_set),
        symbol="BTCUSDT",
    )

    assert first.decision_cycle_id == second.decision_cycle_id
    assert first.set_result_id == second.set_result_id
    assert first.evidence_digest == second.evidence_digest
    assert changed.source_evidence_digest != first.source_evidence_digest
    assert changed.set_result_id != first.set_result_id


def test_r006_btc_not_applicable_and_interaction_cells_remain_isolated():
    spec = json.loads(Path("docs/research-import/build/RESEARCH_V1_BUILD_SPEC.json").read_text(encoding="utf-8"))
    r006 = build_research_v1_execution_definition("R-006", spec=spec)
    r029 = build_research_v1_execution_definition("R-029", spec=spec)
    r030 = build_research_v1_execution_definition("R-030", spec=spec)

    assert r006.special_applicability["btc_result_scope_applicability"] == "NOT_APPLICABLE"
    assert r006.selected_binding.btc.set_version_id is None
    assert set(r029.interaction_cells) == {"00", "01", "10", "11"}
    assert set(r030.interaction_cells) == {"00", "01", "10", "11"}
    assert _cell_tuple(r029, "00") != _cell_tuple(r029, "11")
    assert _cell_tuple(r030, "00") != _cell_tuple(r030, "11")


def test_all_research_v1_set_versions_have_supported_historical_direction_scope():
    package = json.loads(Path("docs/research-import/sets/RESEARCH_V1_SETS.json").read_text(encoding="utf-8"))
    unsupported = []
    for record in package["sets"]:
        research_set = research_set_from_package_record(record)
        try:
            resolve_research_v1_historical_set_from_trigger_evaluations(
                research_set=research_set,
                trigger_evaluations=_unmatched_available_evaluations(research_set),
                trigger_rules=_rules_for(research_set),
                symbol="BTCUSDT" if "BTC" in research_set.coin_applicability else "ETHUSDT",
            )
        except Exception as exc:  # pragma: no cover - assertion prints exact blocker
            unsupported.append((research_set.set_version, str(exc)))

    assert unsupported == []


def _research_set(set_version: str) -> ResearchSetVersion:
    package = json.loads(Path("docs/research-import/sets/RESEARCH_V1_SETS.json").read_text(encoding="utf-8"))
    return research_set_from_package_record(next(item for item in package["sets"] if item["set_version"] == set_version))


def _rules_for(research_set: ResearchSetVersion) -> tuple[RuleDefinition, ...]:
    return tuple(_rule(member.trigger_id) for member in research_set.trigger_members)


def _evaluations_for_set(research_set: ResearchSetVersion, outputs: dict[str, tuple[str, bool]]) -> tuple[HistoricalTriggerEvaluation, ...]:
    return tuple(
        _evaluation(member.trigger_id, member.trigger_version, *outputs[member.trigger_id])
        for member in research_set.trigger_members
    )


def _unmatched_available_evaluations(research_set: ResearchSetVersion) -> tuple[HistoricalTriggerEvaluation, ...]:
    outputs: dict[str, tuple[str, bool]] = {}
    for member in research_set.trigger_members:
        if member.role == "SET_FORMATION_PREDICATE":
            outputs[member.trigger_id] = ("FALSE", False)
        elif member.role == "SET_RESET_PREDICATE":
            outputs[member.trigger_id] = ("FALSE", False)
        elif member.direction_applicability == "LONG":
            outputs[member.trigger_id] = ("FALSE", False)
        elif member.direction_applicability == "SHORT":
            outputs[member.trigger_id] = ("FALSE", False)
        else:
            outputs[member.trigger_id] = ("FALSE", False)
    return _evaluations_for_set(research_set, outputs)


def _evaluation(trigger_id: str, version: str, output_state: str, condition_result: bool) -> HistoricalTriggerEvaluation:
    observed_at = datetime(2026, 8, 17, 0, 15, tzinfo=UTC).isoformat()
    basis = {
        "trigger_id": trigger_id,
        "trigger_version": version,
        "output_state": output_state,
        "condition_result": condition_result,
    }
    digest = canonical_json_digest(basis)
    return HistoricalTriggerEvaluation(
        trigger_id=trigger_id,
        trigger_version=version,
        metric_ref="fixture",
        metric_value=output_state,
        operator="EQ",
        threshold=output_state,
        condition_result=condition_result,
        output_state=output_state,
        signal_type=SignalType.CONFIRMED.value if condition_result else SignalType.NO_SIGNAL.value,
        observed_at=observed_at,
        available_at=observed_at,
        evidence_id=f"rv1-trigger-eval-{digest[:24]}",
        evidence_digest=digest,
        metric_evidence_id=f"rv1-metric-{digest[:24]}",
        metric_evidence_digest=digest,
        signal=Signal(
            signal_id=f"signal-{digest[:24]}",
            trigger_rule_id=trigger_id,
            trigger_rule_version=version,
            symbol="BTCUSDT",
            observed_at=observed_at,
            window="5m",
            input_snapshot={"output_state": output_state, "metric_value": output_state},
            condition_result=condition_result,
            signal_type=SignalType.CONFIRMED if condition_result else SignalType.NO_SIGNAL,
            reason=None if condition_result else "condition_false",
            lane="BACKTEST",
        ),
    )


def _latest_close(candles) -> datetime:
    return max(candle.close_time for candle in candles)


def _cell_tuple(definition, cell_id: str) -> tuple[str | None, str | None, str]:
    cell = definition.interaction_cells[cell_id]
    return (cell.btc.set_version_id, cell.non_btc.set_version_id, cell.rules_version_id)
