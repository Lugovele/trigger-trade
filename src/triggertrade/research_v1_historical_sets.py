"""Research V1 historical Set formation from factual trigger replay."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from triggertrade.backtest.models import HistoricalCandle
from triggertrade.canonical_json import canonical_json_digest
from triggertrade.instruments import FuturesInstrument
from triggertrade.persistence.postgres_research_set_registry import (
    ResearchSetVersion,
    research_set_digest,
    research_set_member_payload,
)
from triggertrade.research_v1_historical_triggers import (
    HistoricalTriggerEvaluation,
    evaluate_research_v1_historical_triggers,
    produce_research_v1_historical_metric,
)
from triggertrade.set_engine import (
    ClassifierInputs,
    Direction,
    DirectionResolutionScope,
    GenericBranchEvidence,
    SetMatchStatus,
    SetResultResolutionRequest,
    SwingSequenceState,
    TriggerResult,
    resolve_set_result_without_handoff,
)
from triggertrade.set_scope import SetConfigurationBinding, SetFormationEpoch
from triggertrade.trigger_sets import RuleDefinition


RESEARCH_V1_HISTORICAL_SET_PRODUCER_VERSION = "research_v1_historical_set_formation@1"


class ResearchV1HistoricalSetError(ValueError):
    """Raised when Research V1 historical Set formation cannot proceed."""


@dataclass(frozen=True)
class HistoricalSetResolution:
    set_id: str
    set_version: str
    symbol: str
    status: str
    formation_result: str
    direction: str
    decision_cycle_id: str | None
    set_result_id: str
    reason_code: str | None
    configuration_binding: Mapping[str, Any]
    frozen_condition: Mapping[str, Any]
    evaluation_event_ids: tuple[str, ...]
    source_evidence_digest: str
    trigger_evaluations: tuple[HistoricalTriggerEvaluation, ...]
    result_payload: Mapping[str, Any]
    evidence_digest: str
    evidence_id: str


def resolve_research_v1_historical_set(
    *,
    research_set: ResearchSetVersion,
    trigger_rules: Sequence[RuleDefinition],
    candles: Sequence[HistoricalCandle],
    symbol: str,
    observed_at: datetime | None = None,
    instrument_metadata: FuturesInstrument | None = None,
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None = None,
    companion_instrument_metadata: Mapping[str, FuturesInstrument] | None = None,
    raw_trades_pages: Sequence[Mapping[str, Any]] | None = None,
) -> HistoricalSetResolution:
    """Resolve one Research V1 Set version from factual historical triggers."""

    rules = _rules_for_set(research_set=research_set, trigger_rules=trigger_rules)
    evaluations = evaluate_research_v1_historical_triggers(
        rules=rules,
        candles=candles,
        symbol=symbol,
        trigger_set_id=research_set.set_id,
        trigger_set_version=research_set.set_version,
        observed_at=observed_at,
        instrument_metadata=instrument_metadata,
        companion_candles=companion_candles,
        companion_instrument_metadata=companion_instrument_metadata,
        raw_trades_pages=raw_trades_pages,
    )
    return resolve_research_v1_historical_set_from_trigger_evaluations(
        research_set=research_set,
        trigger_evaluations=evaluations,
        trigger_rules=rules,
        candles=candles,
        symbol=symbol,
        observed_at=observed_at,
        instrument_metadata=instrument_metadata,
        companion_candles=companion_candles,
        companion_instrument_metadata=companion_instrument_metadata,
        raw_trades_pages=raw_trades_pages,
    )


def resolve_research_v1_historical_set_from_trigger_evaluations(
    *,
    research_set: ResearchSetVersion,
    trigger_evaluations: Sequence[HistoricalTriggerEvaluation],
    trigger_rules: Sequence[RuleDefinition],
    candles: Sequence[HistoricalCandle] = (),
    symbol: str,
    observed_at: datetime | None = None,
    instrument_metadata: FuturesInstrument | None = None,
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None = None,
    companion_instrument_metadata: Mapping[str, FuturesInstrument] | None = None,
    raw_trades_pages: Sequence[Mapping[str, Any]] | None = None,
) -> HistoricalSetResolution:
    """Resolve Set semantics from already factual trigger evaluations."""

    evaluations = _ordered_evaluations(research_set, trigger_evaluations)
    direction_scope = _direction_scope(research_set)
    formation_result = _formation_result(research_set=research_set, evaluations=evaluations)
    configuration_binding = _configuration_binding(research_set)
    source_evidence_digest = _source_evidence_digest(research_set=research_set, evaluations=evaluations)
    decision_slot = _decision_slot(evaluations)
    frozen_condition = _frozen_condition(research_set=research_set, evaluations=evaluations, decision_slot=decision_slot)
    classifier_inputs = None
    generic_branches: tuple[GenericBranchEvidence, ...] = ()
    if direction_scope is DirectionResolutionScope.F005_GOVERNED and formation_result is TriggerResult.TRUE:
        classifier_inputs = _classifier_inputs_for_set(
            research_set=research_set,
            trigger_rules=trigger_rules,
            candles=candles,
            symbol=symbol,
            observed_at=observed_at,
            instrument_metadata=instrument_metadata,
            companion_candles=companion_candles,
            companion_instrument_metadata=companion_instrument_metadata,
            raw_trades_pages=raw_trades_pages,
        )
    if direction_scope is DirectionResolutionScope.GENERIC_MATCHED_BRANCH and formation_result is TriggerResult.TRUE:
        generic_branches = _generic_branches(research_set=research_set, evaluations=evaluations)
    request = SetResultResolutionRequest(
        formation_epoch=SetFormationEpoch(
            symbol=symbol,
            formation_epoch=int(decision_slot.timestamp()),
            open_event_id=f"rv1-set-open-{source_evidence_digest[:24]}",
            opened_at=_iso(decision_slot),
            open_payload_digest=source_evidence_digest,
            configuration_binding=configuration_binding,
        ),
        direction_scope=direction_scope,
        formation_result=formation_result,
        evaluation_event_ids=tuple(evaluation.evidence_id for evaluation in evaluations),
        source_evidence_digest=source_evidence_digest,
        classifier_inputs=classifier_inputs,
        generic_branches=generic_branches,
        frozen_condition=frozen_condition,
    )
    record = resolve_set_result_without_handoff(request)
    evidence_payload = {
        "producer": RESEARCH_V1_HISTORICAL_SET_PRODUCER_VERSION,
        "set_id": research_set.set_id,
        "set_version": research_set.set_version,
        "symbol": symbol.upper(),
        "status": record.status.value,
        "formation_result": formation_result.value,
        "direction": record.direction.value,
        "decision_cycle_id": record.decision_cycle_id,
        "set_result_id": record.set_result_id,
        "source_evidence_digest": source_evidence_digest,
        "result_payload": record.result_payload,
    }
    evidence_digest = canonical_json_digest(evidence_payload)
    return HistoricalSetResolution(
        set_id=research_set.set_id,
        set_version=research_set.set_version,
        symbol=symbol.upper(),
        status=record.status.value,
        formation_result=formation_result.value,
        direction=record.direction.value,
        decision_cycle_id=record.decision_cycle_id,
        set_result_id=record.set_result_id,
        reason_code=record.reason_code,
        configuration_binding=configuration_binding.to_payload(),
        frozen_condition=frozen_condition,
        evaluation_event_ids=request.evaluation_event_ids,
        source_evidence_digest=source_evidence_digest,
        trigger_evaluations=evaluations,
        result_payload=record.result_payload,
        evidence_digest=evidence_digest,
        evidence_id=f"rv1-set-resolution-{evidence_digest[:24]}",
    )


def _rules_for_set(*, research_set: ResearchSetVersion, trigger_rules: Sequence[RuleDefinition]) -> tuple[RuleDefinition, ...]:
    by_key = {(rule.rule_id, rule.version): rule for rule in trigger_rules}
    rules: list[RuleDefinition] = []
    for member in research_set.trigger_members:
        rule = by_key.get((member.trigger_id, member.trigger_version))
        if rule is None:
            raise ResearchV1HistoricalSetError(
                f"research_v1_historical_set_trigger_rule_missing:{member.trigger_id}@{member.trigger_version}"
            )
        rules.append(rule)
    return tuple(rules)


def _ordered_evaluations(
    research_set: ResearchSetVersion,
    trigger_evaluations: Sequence[HistoricalTriggerEvaluation],
) -> tuple[HistoricalTriggerEvaluation, ...]:
    by_key = {(evaluation.trigger_id, evaluation.trigger_version): evaluation for evaluation in trigger_evaluations}
    ordered: list[HistoricalTriggerEvaluation] = []
    for member in research_set.trigger_members:
        evaluation = by_key.get((member.trigger_id, member.trigger_version))
        if evaluation is None:
            raise ResearchV1HistoricalSetError(
                f"research_v1_historical_set_trigger_evaluation_missing:{member.trigger_id}@{member.trigger_version}"
            )
        ordered.append(evaluation)
    return tuple(ordered)


def _formation_result(*, research_set: ResearchSetVersion, evaluations: Sequence[HistoricalTriggerEvaluation]) -> TriggerResult:
    common = [
        evaluation
        for member, evaluation in zip(research_set.trigger_members, evaluations, strict=True)
        if member.role == "SET_FORMATION_PREDICATE"
    ]
    directional = [
        evaluation
        for member, evaluation in zip(research_set.trigger_members, evaluations, strict=True)
        if member.role in {"DIRECTION_PREDICATE", "BTC_DIRECTION_CONSTRUCTION"}
    ]
    if any(evaluation.output_state == "UNAVAILABLE" or evaluation.metric_value == "UNAVAILABLE" for evaluation in (*common, *directional)):
        return TriggerResult.UNAVAILABLE
    if not common or not directional:
        return TriggerResult.FALSE
    if not all(evaluation.condition_result for evaluation in common):
        return TriggerResult.FALSE
    if any(evaluation.condition_result for evaluation in directional):
        return TriggerResult.TRUE
    return TriggerResult.FALSE


def _direction_scope(research_set: ResearchSetVersion) -> DirectionResolutionScope:
    if research_set.direction_semantics.startswith("F-005"):
        return DirectionResolutionScope.F005_GOVERNED
    if research_set.direction_semantics.startswith("DB-R-BTC-001"):
        return DirectionResolutionScope.GENERIC_MATCHED_BRANCH
    raise ResearchV1HistoricalSetError(f"research_v1_historical_set_direction_scope_unsupported:{research_set.set_version}")


def _classifier_inputs_for_set(
    *,
    research_set: ResearchSetVersion,
    trigger_rules: Sequence[RuleDefinition],
    candles: Sequence[HistoricalCandle],
    symbol: str,
    observed_at: datetime | None,
    instrument_metadata: FuturesInstrument | None,
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None,
    companion_instrument_metadata: Mapping[str, FuturesInstrument] | None,
    raw_trades_pages: Sequence[Mapping[str, Any]] | None,
) -> ClassifierInputs:
    if not candles:
        raise ResearchV1HistoricalSetError("research_v1_historical_set_classifier_inputs_unavailable:NO_CANDLES")
    rule = next(
        (
            rule
            for rule in trigger_rules
            if any(
                member.trigger_id == rule.rule_id
                and member.trigger_version == rule.version
                and member.role == "DIRECTION_PREDICATE"
                for member in research_set.trigger_members
            )
        ),
        None,
    )
    if rule is None:
        raise ResearchV1HistoricalSetError("research_v1_historical_set_classifier_inputs_unavailable:NO_DIRECTION_RULE")
    observation = produce_research_v1_historical_metric(
        metric_ref="classifier_direction",
        rule=rule,
        candles=candles,
        symbol=symbol,
        observed_at=observed_at,
        instrument_metadata=instrument_metadata,
        companion_candles=companion_candles,
        companion_instrument_metadata=companion_instrument_metadata,
        raw_trades_pages=raw_trades_pages,
    )
    payload = dict(observation.payload or {}).get("classifier_direction")
    if observation.status != "AVAILABLE" or not isinstance(payload, Mapping):
        raise ResearchV1HistoricalSetError("research_v1_historical_set_classifier_inputs_unavailable")
    return _classifier_inputs_from_payload(payload.get("classifier_inputs"))


def _classifier_inputs_from_payload(payload: Any) -> ClassifierInputs:
    if not isinstance(payload, Mapping):
        raise ResearchV1HistoricalSetError("research_v1_historical_set_classifier_inputs_unavailable:PAYLOAD_MISSING")
    return ClassifierInputs(
        structure_1h=SwingSequenceState(str(payload["structure_1h"])),
        structure_15m=SwingSequenceState(str(payload["structure_15m"])),
        de_15m=str(payload["de_15m"]),
        momentum_score=str(payload["momentum_score"]),
        vnm_5m_z=str(payload["vnm_5m_z"]),
        relative_score=str(payload["relative_score"]),
        relative_return_z=str(payload["relative_return_z"]),
        aggressive_delta_pct=str(payload["aggressive_delta_pct"]),
        tod_relative_turnover=str(payload["tod_relative_turnover"]),
        atr_pct_percentile_15m=str(payload["atr_pct_percentile_15m"]),
        btc_structure_1h=SwingSequenceState(str(payload["btc_structure_1h"])),
        btc_return_z=str(payload["btc_return_z"]),
    )


def _generic_branches(
    *,
    research_set: ResearchSetVersion,
    evaluations: Sequence[HistoricalTriggerEvaluation],
) -> tuple[GenericBranchEvidence, ...]:
    branches: list[GenericBranchEvidence] = []
    for member, evaluation in zip(research_set.trigger_members, evaluations, strict=True):
        if member.role != "BTC_DIRECTION_CONSTRUCTION" or not evaluation.condition_result:
            continue
        direction = _member_direction(member.direction_applicability)
        branches.append(
            GenericBranchEvidence(
                branch_id=member.trigger_id,
                direction=direction,
                canonical_timestamp=evaluation.observed_at,
                evidence_digest=evaluation.evidence_digest,
            )
        )
    return tuple(branches)


def _member_direction(value: str | None) -> Direction:
    if value == "LONG":
        return Direction.LONG
    if value == "SHORT":
        return Direction.SHORT
    raise ResearchV1HistoricalSetError(f"research_v1_historical_set_direction_unavailable:{value}")


def _configuration_binding(research_set: ResearchSetVersion) -> SetConfigurationBinding:
    set_digest = research_set_digest(research_set)
    member_digest = canonical_json_digest(
        {
            "set_id": research_set.set_id,
            "set_version": research_set.set_version,
            "trigger_members": [research_set_member_payload(member) for member in research_set.trigger_members],
        }
    )
    core_digest = canonical_json_digest(
        {
            "set_digest": set_digest,
            "trigger_member_digest": member_digest,
            "direction_semantics": research_set.direction_semantics,
            "composition": research_set.trigger_composition_logic,
        }
    )
    return SetConfigurationBinding(
        set_config_id=research_set.set_id,
        set_config_version=research_set.set_version,
        set_config_digest=set_digest,
        trigger_config_id=f"{research_set.set_id}:trigger-members",
        trigger_config_version=research_set.set_version,
        trigger_config_digest=member_digest,
        core_set_config_id=research_set.set_id,
        core_set_config_version=research_set.set_version,
        core_set_config_digest=core_digest,
    )


def _source_evidence_digest(
    *,
    research_set: ResearchSetVersion,
    evaluations: Sequence[HistoricalTriggerEvaluation],
) -> str:
    return canonical_json_digest(
        {
            "producer": RESEARCH_V1_HISTORICAL_SET_PRODUCER_VERSION,
            "set_id": research_set.set_id,
            "set_version": research_set.set_version,
            "set_digest": research_set_digest(research_set),
            "trigger_evaluations": [
                {
                    "trigger_id": evaluation.trigger_id,
                    "trigger_version": evaluation.trigger_version,
                    "condition_result": evaluation.condition_result,
                    "output_state": evaluation.output_state,
                    "evidence_id": evaluation.evidence_id,
                    "evidence_digest": evaluation.evidence_digest,
                }
                for evaluation in evaluations
            ],
        }
    )


def _frozen_condition(
    *,
    research_set: ResearchSetVersion,
    evaluations: Sequence[HistoricalTriggerEvaluation],
    decision_slot: datetime,
) -> dict[str, Any]:
    return {
        "schema_version": "RESEARCH_V1_HISTORICAL_SET_FROZEN_CONDITION_V1",
        "set_id": research_set.set_id,
        "set_version": research_set.set_version,
        "decision_slot": _iso(decision_slot),
        "trigger_composition_logic": research_set.trigger_composition_logic,
        "direction_semantics": research_set.direction_semantics,
        "trigger_evaluations": [
            {
                "trigger_id": evaluation.trigger_id,
                "trigger_version": evaluation.trigger_version,
                "output_state": evaluation.output_state,
                "condition_result": evaluation.condition_result,
                "evidence_digest": evaluation.evidence_digest,
            }
            for evaluation in evaluations
        ],
    }


def _decision_slot(evaluations: Sequence[HistoricalTriggerEvaluation]) -> datetime:
    if not evaluations:
        raise ResearchV1HistoricalSetError("research_v1_historical_set_evaluations_empty")
    return max(_parse_iso(evaluation.observed_at) for evaluation in evaluations)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


__all__ = [
    "HistoricalSetResolution",
    "RESEARCH_V1_HISTORICAL_SET_PRODUCER_VERSION",
    "ResearchV1HistoricalSetError",
    "resolve_research_v1_historical_set",
    "resolve_research_v1_historical_set_from_trigger_evaluations",
]
