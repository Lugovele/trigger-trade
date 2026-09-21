"""Durable Set handler for B5B MATCHED result and Market Handoff production."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.contracts import BindingRole, validate_contract_edge
from triggertrade.numeric_policy import NumericPolicyError, parse_decimal_text, q18_wire
from triggertrade.persistence.durable_messages import DurableMessageStore
from triggertrade.persistence.postgres import OwnerStateConflict, OwnerStateRecord, OwnerStateStore, PostgresPersistenceError
from triggertrade.set_engine.formulas import ClassifierInputs, Direction, IndicatorStatus, TriggerResult, classify_direction
from triggertrade.set_scope import SetFormationEpoch


class SetHandlerError(ValueError):
    """Raised when Set final resolution cannot be represented safely."""


class SetResultConflict(PostgresPersistenceError):
    """Raised when a Set result or frozen record identity is replayed with new content."""


class DirectionResolutionScope(StrEnum):
    F005_GOVERNED = "F005_GOVERNED"
    GENERIC_FIXED = "GENERIC_FIXED"
    GENERIC_MATCHED_BRANCH = "GENERIC_MATCHED_BRANCH"


class SetMatchStatus(StrEnum):
    MATCHED = "MATCHED"
    UNMATCHED = "UNMATCHED"


@dataclass(frozen=True)
class GenericBranchEvidence:
    branch_id: str
    direction: Direction
    canonical_timestamp: str
    evidence_digest: str


@dataclass(frozen=True)
class DeclaredConflictRule:
    rule_id: str
    selected_branch_id: str
    rule_digest: str


@dataclass(frozen=True)
class GenericFixedDirectionBinding:
    fixed_direction: Direction
    binding_digest: str


@dataclass(frozen=True)
class HandoffReferenceLevel:
    level_id: str
    level_type: str
    price: str
    timeframe: str
    formed_at: str | None
    confirmed_at: str | None
    available_at: str
    source_metric: str | None
    age_seconds: int
    relative_position: str

    def to_payload(self) -> dict[str, Any]:
        if not isinstance(self.age_seconds, int) or isinstance(self.age_seconds, bool) or self.age_seconds < 0:
            raise SetHandlerError("age_seconds must be a nonnegative integer")
        _positive_decimal_text(self.price, field="reference level price")
        if self.relative_position not in {"BELOW_REFERENCE", "AT_REFERENCE", "ABOVE_REFERENCE"}:
            raise SetHandlerError("relative_position is invalid")
        return {
            "level_id": _text(self.level_id, field="level_id"),
            "level_type": _text(self.level_type, field="level_type"),
            "price": self.price,
            "timeframe": _text(self.timeframe, field="timeframe"),
            "formed_at": _optional_text(self.formed_at, field="formed_at"),
            "confirmed_at": _optional_text(self.confirmed_at, field="confirmed_at"),
            "available_at": _text(self.available_at, field="available_at"),
            "source_metric": _optional_text(self.source_metric, field="source_metric"),
            "age_seconds": self.age_seconds,
            "relative_position": self.relative_position,
        }


@dataclass(frozen=True)
class HandoffContext:
    set_family: str
    thesis_reference_policy: str
    thesis_reference_level_id: str | None
    origin_binding: Mapping[str, Any] | None

    def to_payload(self, *, level_ids: set[str]) -> dict[str, Any]:
        if self.set_family not in {"TREND_CONTINUATION", "RANGE", "BREAKOUT_RECLAIM", "GENERIC"}:
            raise SetHandlerError("set_family is invalid")
        if self.thesis_reference_policy not in {"REQUIRED", "PREFERRED", "NONE"}:
            raise SetHandlerError("thesis_reference_policy is invalid")
        if self.thesis_reference_policy == "REQUIRED":
            if self.thesis_reference_level_id not in level_ids:
                raise SetHandlerError("required thesis reference must identify one produced level")
            if self.origin_binding is None:
                raise SetHandlerError("required thesis reference must retain origin binding")
        if self.thesis_reference_level_id is not None:
            if self.thesis_reference_level_id not in level_ids:
                raise SetHandlerError("thesis reference must identify one produced level")
            if self.origin_binding is None:
                raise SetHandlerError("non-null thesis reference must retain origin binding")
        if self.origin_binding is not None and self.thesis_reference_level_id is None:
            raise SetHandlerError("origin binding requires a thesis reference level")
        if self.thesis_reference_policy == "NONE" and (
            self.thesis_reference_level_id is not None or self.origin_binding is not None
        ):
            raise SetHandlerError("NONE thesis reference policy cannot carry a thesis reference")
        binding = None if self.origin_binding is None else _origin_binding_payload(self.origin_binding)
        if binding is not None and binding["level_id"] not in level_ids:
            raise SetHandlerError("origin binding level_id must match a produced reference level")
        if binding is not None and binding["level_id"] != self.thesis_reference_level_id:
            raise SetHandlerError("origin binding level_id must match thesis reference level")
        return {
            "set_family": self.set_family,
            "thesis_reference_policy": self.thesis_reference_policy,
            "thesis_reference_level_id": _optional_text(self.thesis_reference_level_id, field="thesis_reference_level_id"),
            "origin_binding": binding,
        }


@dataclass(frozen=True)
class HandoffFacts:
    symbol: str
    created_at: str
    matched_at: str
    market_snapshot_at: str
    market_snapshot_id: str
    set_match_reference_price: str
    reference_price_observed_at: str
    reference_price_source: str
    tick_size: str
    metadata_revision: str
    metadata_as_of: str
    atr_15m: str
    atr_pct_15m: str
    reference_levels: tuple[HandoffReferenceLevel, ...]
    entry_context: HandoffContext
    sl_context: HandoffContext
    tp_context: HandoffContext
    core_set_id: str
    set_family: str = "GENERIC"


@dataclass(frozen=True)
class SetResolutionRequest:
    formation_epoch: SetFormationEpoch
    direction_scope: DirectionResolutionScope
    formation_result: TriggerResult
    evaluation_event_ids: tuple[str, ...]
    source_evidence_digest: str
    handoff_facts: HandoffFacts
    classifier_inputs: ClassifierInputs | None = None
    fixed_direction_binding: GenericFixedDirectionBinding | None = None
    generic_branches: tuple[GenericBranchEvidence, ...] = ()
    declared_conflict_rule: DeclaredConflictRule | None = None
    frozen_condition: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class SetResolutionRecord:
    status: SetMatchStatus
    decision_cycle_id: str | None
    set_result_id: str
    reason_code: str | None
    direction: Direction
    result_payload: dict[str, Any]
    handoff_payload: dict[str, Any] | None
    outbox_inserted: bool
    result_inserted: bool


class SetDurableHandler:
    """Resolve one Set epoch and persist its immutable Set-owned result."""

    def __init__(self, connection) -> None:
        self._owner_state = OwnerStateStore(connection)
        self._messages = DurableMessageStore(connection)

    def resolve(self, request: SetResolutionRequest) -> SetResolutionRecord:
        result = _resolve_direction(request)
        ids = _set_ids(request=request, status=result.status, direction=result.direction, reason_code=result.reason_code)
        result_payload = _result_payload(request=request, result=result, ids=ids)
        handoff_payload: dict[str, Any] | None = None
        parsed_handoff = None
        if result.status is SetMatchStatus.MATCHED:
            handoff_payload = _market_handoff_payload(request=request, direction=result.direction, ids=ids)
            parsed_handoff = validate_contract_edge(
                producer=BindingRole.SET,
                consumer=BindingRole.POSITION,
                contract_type="MARKET_HANDOFF",
                payload=handoff_payload,
                definition="MARKET_HANDOFF",
            )
        try:
            result_record, result_inserted = self._owner_state.put_if_absent(
                owner="SET",
                state_type="SET_RESULT",
                state_id=ids["set_result_id"],
                payload=result_payload,
            )
        except OwnerStateConflict as exc:
            raise SetResultConflict("Set result identity already exists with different content") from exc
        _assert_existing_payload(result_record, result_payload, label="Set result")

        outbox_inserted = False
        if result.status is SetMatchStatus.MATCHED:
            assert parsed_handoff is not None
            frozen_payload = _frozen_condition_payload(request=request, result=result, ids=ids)
            try:
                frozen_record, _ = self._owner_state.put_if_absent(
                    owner="SET",
                    state_type="SET_FROZEN_CONDITION",
                    state_id=ids["condition_record_id"],
                    payload=frozen_payload,
                )
            except OwnerStateConflict as exc:
                raise SetResultConflict("Set frozen condition identity already exists with different content") from exc
            _assert_existing_payload(frozen_record, frozen_payload, label="Set frozen condition")

            outbox, _, outbox_inserted = self._messages.append_frontier_outbox(
                scope_key=f"SET:{request.formation_epoch.symbol}:{request.formation_epoch.formation_epoch}",
                message_id=ids["decision_cycle_id"],
                producer="Set",
                consumer="Position",
                message_type="MARKET_HANDOFF",
                message_version="4",
                payload=parsed_handoff.to_payload(),
                aggregate_id=ids["set_result_id"],
                causation_id=request.formation_epoch.open_event_id,
                correlation_id=ids["decision_cycle_id"],
                dedupe_key=f"MARKET_HANDOFF:{ids['set_result_id']}",
            )
            if outbox.payload_digest != canonical_json_digest(parsed_handoff.to_payload()):
                raise PostgresPersistenceError("MARKET_HANDOFF outbox digest mismatch")

        return SetResolutionRecord(
            status=result.status,
            decision_cycle_id=ids.get("decision_cycle_id") if result.status is SetMatchStatus.MATCHED else None,
            set_result_id=ids["set_result_id"],
            reason_code=result.reason_code,
            direction=result.direction,
            result_payload=result_record.payload,
            handoff_payload=handoff_payload,
            outbox_inserted=outbox_inserted,
            result_inserted=result_inserted,
        )


@dataclass(frozen=True)
class _Resolution:
    status: SetMatchStatus
    direction: Direction
    reason_code: str | None
    branch_id: str | None = None
    classifier_payload: dict[str, Any] | None = None


def _resolve_direction(request: SetResolutionRequest) -> _Resolution:
    if request.formation_epoch.epoch_state != "ACTIVE":
        return _Resolution(SetMatchStatus.UNMATCHED, Direction.NONE, "FORMATION_EPOCH_NOT_ACTIVE")
    if not request.evaluation_event_ids:
        return _Resolution(SetMatchStatus.UNMATCHED, Direction.NONE, "MISSING_FORMATION_EVENTS")
    if len(set(request.evaluation_event_ids)) != len(request.evaluation_event_ids):
        raise SetHandlerError("evaluation_event_ids must be unique")
    _digest(request.source_evidence_digest, field="source_evidence_digest")
    if request.formation_result is not TriggerResult.TRUE:
        classifier_payload = None
        if request.direction_scope is DirectionResolutionScope.F005_GOVERNED and request.classifier_inputs is not None:
            classifier_payload = classify_direction(request.classifier_inputs).to_payload()
        return _Resolution(
            SetMatchStatus.UNMATCHED,
            Direction.NONE,
            f"FORMATION_{request.formation_result.value}",
            classifier_payload=classifier_payload,
        )

    if request.direction_scope is DirectionResolutionScope.F005_GOVERNED:
        if request.classifier_inputs is None:
            return _Resolution(SetMatchStatus.UNMATCHED, Direction.NONE, "F005_CLASSIFIER_REQUIRED")
        classifier = classify_direction(request.classifier_inputs)
        payload = classifier.to_payload()
        if classifier.status is not IndicatorStatus.AVAILABLE:
            return _Resolution(SetMatchStatus.UNMATCHED, Direction.NONE, "F005_UNAVAILABLE", classifier_payload=payload)
        if classifier.direction is Direction.NONE:
            return _Resolution(SetMatchStatus.UNMATCHED, Direction.NONE, "F005_NONE", classifier_payload=payload)
        return _Resolution(SetMatchStatus.MATCHED, classifier.direction, None, classifier_payload=payload)

    if request.direction_scope is DirectionResolutionScope.GENERIC_FIXED:
        if request.fixed_direction_binding is None:
            return _Resolution(SetMatchStatus.UNMATCHED, Direction.NONE, "GENERIC_FIXED_DIRECTION_REQUIRED")
        if request.classifier_inputs is not None:
            raise SetHandlerError("generic fixed direction must not invoke F-005 classifier")
        binding = request.fixed_direction_binding
        if binding.fixed_direction not in {Direction.LONG, Direction.SHORT}:
            return _Resolution(SetMatchStatus.UNMATCHED, Direction.NONE, "GENERIC_FIXED_DIRECTION_REQUIRED")
        expected_digest = generic_fixed_direction_binding_digest(
            configuration_binding_digest=request.formation_epoch.configuration_binding.digest,
            fixed_direction=binding.fixed_direction,
        )
        if binding.binding_digest != expected_digest:
            raise SetHandlerError("generic fixed direction must match immutable configuration binding")
        return _Resolution(SetMatchStatus.MATCHED, binding.fixed_direction, None)

    if request.direction_scope is DirectionResolutionScope.GENERIC_MATCHED_BRANCH:
        if request.classifier_inputs is not None:
            raise SetHandlerError("generic matched branch direction must not invoke F-005 classifier")
        branches = _validated_generic_branches(request.generic_branches)
        if not branches:
            return _Resolution(SetMatchStatus.UNMATCHED, Direction.NONE, "NO_MATCHED_BRANCH")
        directions = {branch.direction for branch in branches}
        if not directions <= {Direction.LONG, Direction.SHORT}:
            raise SetHandlerError("generic branch directions must be LONG or SHORT")
        if len(directions) == 1:
            return _Resolution(SetMatchStatus.MATCHED, branches[0].direction, None, branch_id=branches[0].branch_id)
        rule = request.declared_conflict_rule
        if rule is None:
            return _Resolution(SetMatchStatus.UNMATCHED, Direction.NONE, "GENERIC_CONFLICT_UNRESOLVED")
        _text(rule.rule_id, field="conflict rule_id")
        _text(rule.selected_branch_id, field="conflict selected_branch_id")
        _digest(rule.rule_digest, field="conflict rule_digest")
        for branch in branches:
            if branch.branch_id == rule.selected_branch_id:
                return _Resolution(SetMatchStatus.MATCHED, branch.direction, None, branch_id=branch.branch_id)
        return _Resolution(SetMatchStatus.UNMATCHED, Direction.NONE, "GENERIC_CONFLICT_RULE_UNRESOLVED")

    raise SetHandlerError("unknown direction resolution scope")


def _set_ids(*, request: SetResolutionRequest, status: SetMatchStatus, direction: Direction, reason_code: str | None) -> dict[str, str]:
    basis = {
        "checkpoint": "B5B_SET_RESULT_V1",
        "symbol": request.formation_epoch.symbol,
        "formation_epoch": request.formation_epoch.formation_epoch,
        "open_event_id": request.formation_epoch.open_event_id,
        "open_payload_digest": request.formation_epoch.open_payload_digest,
    }
    digest = canonical_json_digest(basis)
    return {
        "decision_cycle_id": f"decision-cycle-{digest[:32]}",
        "set_result_id": f"set-result-{digest[32:64]}",
        "condition_record_id": f"condition-record-{digest[:32]}",
        "condition_id": f"condition-{digest[32:64]}",
    }


def _result_payload(*, request: SetResolutionRequest, result: _Resolution, ids: Mapping[str, str]) -> dict[str, Any]:
    return {
        "set_result": {
            "schema_version": "SET_RESULT_B5B_V1",
            "status": result.status.value,
            "reason_code": result.reason_code,
            "direction": result.direction.value,
            "decision_cycle_id": ids["decision_cycle_id"] if result.status is SetMatchStatus.MATCHED else None,
            "set_result_id": ids["set_result_id"],
            "symbol": request.formation_epoch.symbol,
            "formation_epoch": request.formation_epoch.formation_epoch,
            "direction_scope": request.direction_scope.value,
            "configuration_binding": request.formation_epoch.configuration_binding.to_payload(),
            "configuration_binding_digest": request.formation_epoch.configuration_binding.digest,
            "formation_result": request.formation_result.value,
            "evaluation_event_ids": list(request.evaluation_event_ids),
            "source_evidence_digest": request.source_evidence_digest,
            "selected_branch_id": result.branch_id,
            "fixed_direction_binding_digest": (
                None if request.fixed_direction_binding is None else request.fixed_direction_binding.binding_digest
            ),
            "generic_branches": [
                {
                    "branch_id": branch.branch_id,
                    "direction": branch.direction.value,
                    "canonical_timestamp": branch.canonical_timestamp,
                    "evidence_digest": branch.evidence_digest,
                }
                for branch in _validated_generic_branches(request.generic_branches)
            ],
            "declared_conflict_rule": (
                None
                if request.declared_conflict_rule is None
                else {
                    "rule_id": request.declared_conflict_rule.rule_id,
                    "selected_branch_id": request.declared_conflict_rule.selected_branch_id,
                    "rule_digest": request.declared_conflict_rule.rule_digest,
                }
            ),
            "classifier_evidence": result.classifier_payload,
        }
    }


def _validated_generic_branches(branches: tuple[GenericBranchEvidence, ...]) -> tuple[GenericBranchEvidence, ...]:
    resolved = tuple(
        GenericBranchEvidence(
            branch_id=_text(branch.branch_id, field="branch_id"),
            direction=branch.direction,
            canonical_timestamp=_text(branch.canonical_timestamp, field="branch canonical_timestamp"),
            evidence_digest=_digest(branch.evidence_digest, field="branch evidence_digest"),
        )
        for branch in branches
    )
    if len({branch.branch_id for branch in resolved}) != len(resolved):
        raise SetHandlerError("generic branch identities must be unique")
    return tuple(sorted(resolved, key=lambda branch: branch.branch_id))


def _frozen_condition_payload(*, request: SetResolutionRequest, result: _Resolution, ids: Mapping[str, str]) -> dict[str, Any]:
    return {
        "set_frozen_condition": {
            "schema_version": "SET_FROZEN_CONDITION_B5B_V1",
            "condition_record_id": ids["condition_record_id"],
            "frozen_condition_record_id": ids["condition_record_id"],
            "condition_id": ids["condition_id"],
            "decision_cycle_id": ids["decision_cycle_id"],
            "set_result_id": ids["set_result_id"],
            "symbol": request.formation_epoch.symbol,
            "direction": result.direction.value,
            "direction_scope": request.direction_scope.value,
            "formation_epoch": request.formation_epoch.formation_epoch,
            "configuration_binding_digest": request.formation_epoch.configuration_binding.digest,
            "source_evidence_digest": request.source_evidence_digest,
            "source_condition": dict(request.frozen_condition or {}),
        }
    }


def _market_handoff_payload(*, request: SetResolutionRequest, direction: Direction, ids: Mapping[str, str]) -> dict[str, Any]:
    facts = request.handoff_facts
    levels = [level.to_payload() for level in facts.reference_levels]
    if not levels:
        raise SetHandlerError("MARKET_HANDOFF requires at least one reference level")
    level_ids = {str(level["level_id"]) for level in levels}
    if len(level_ids) != len(levels):
        raise SetHandlerError("reference level IDs must be unique")
    atr_15m = _q18_text(facts.atr_15m, field="atr_15m")
    atr_pct_15m = _q18_text(facts.atr_pct_15m, field="atr_pct_15m")
    if parse_decimal_text(atr_15m) <= 0 or parse_decimal_text(atr_pct_15m) <= 0:
        raise SetHandlerError("required ATR exports must be positive")
    set_family = _set_family(facts.set_family)
    return {
        "market_handoff": {
            "contract_version": 4,
            "decision_cycle_id": ids["decision_cycle_id"],
            "set_result_id": ids["set_result_id"],
            "symbol": _text(facts.symbol, field="symbol").upper(),
            "created_at": _text(facts.created_at, field="created_at"),
            "set_provenance": {
                "set_id": request.formation_epoch.configuration_binding.set_config_id,
                "set_version": request.formation_epoch.configuration_binding.set_config_version,
                "core_set_id": _text(facts.core_set_id, field="core_set_id"),
                "set_family": set_family,
            },
            "snapshot": {
                "matched_at": _text(facts.matched_at, field="matched_at"),
                "market_snapshot_at": _text(facts.market_snapshot_at, field="market_snapshot_at"),
                "market_snapshot_id": _text(facts.market_snapshot_id, field="market_snapshot_id"),
                "direction": direction.value,
                "set_match_reference_price": _positive_decimal_text(facts.set_match_reference_price, field="set_match_reference_price"),
                "reference_price_basis": "LAST_TRADED_PRICE",
                "reference_price_observed_at": _text(facts.reference_price_observed_at, field="reference_price_observed_at"),
                "reference_price_source": _text(facts.reference_price_source, field="reference_price_source"),
            },
            "instrument": {
                "tick_size": _positive_decimal_text(facts.tick_size, field="tick_size"),
                "metadata_revision": _text(facts.metadata_revision, field="metadata_revision"),
                "metadata_as_of": _text(facts.metadata_as_of, field="metadata_as_of"),
            },
            "volatility": {"atr_15m": atr_15m, "atr_pct_15m": atr_pct_15m},
            "reference_geometry": {"levels": levels},
            "entry_context": facts.entry_context.to_payload(level_ids=level_ids),
            "sl_context": facts.sl_context.to_payload(level_ids=level_ids),
            "tp_context": facts.tp_context.to_payload(level_ids=level_ids),
            "set_numeric_policy_version": "TT_SET_NUMERIC_V1",
        }
    }


def _handoff_fact_basis(facts: HandoffFacts) -> dict[str, Any]:
    level_ids = {level.level_id for level in facts.reference_levels}
    return {
        "symbol": facts.symbol.upper(),
        "created_at": facts.created_at,
        "matched_at": facts.matched_at,
        "market_snapshot_at": facts.market_snapshot_at,
        "market_snapshot_id": facts.market_snapshot_id,
        "set_match_reference_price": facts.set_match_reference_price,
        "reference_price_observed_at": facts.reference_price_observed_at,
        "reference_price_source": facts.reference_price_source,
        "tick_size": facts.tick_size,
        "metadata_revision": facts.metadata_revision,
        "metadata_as_of": facts.metadata_as_of,
        "atr_15m": facts.atr_15m,
        "atr_pct_15m": facts.atr_pct_15m,
        "reference_levels": [level.to_payload() for level in facts.reference_levels],
        "entry_context": facts.entry_context.to_payload(level_ids=level_ids),
        "sl_context": facts.sl_context.to_payload(level_ids=level_ids),
        "tp_context": facts.tp_context.to_payload(level_ids=level_ids),
        "core_set_id": facts.core_set_id,
        "set_family": facts.set_family,
    }


def _origin_binding_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "binding_id",
        "role_id",
        "core_set_id",
        "core_set_constituent_id",
        "trigger_id",
        "trigger_version",
        "trigger_occurrence_id",
        "reference_key",
        "indicator_id",
        "timeframe",
        "level_id",
    }
    unknown = set(value) - required
    missing = required - set(value)
    if unknown or missing:
        raise SetHandlerError("origin binding must match the frozen reference binding shape")
    return {
        "binding_id": _text(value["binding_id"], field="binding_id"),
        "role_id": _text(value["role_id"], field="role_id"),
        "core_set_id": _text(value["core_set_id"], field="core_set_id"),
        "core_set_constituent_id": _text(value["core_set_constituent_id"], field="core_set_constituent_id"),
        "trigger_id": _text(value["trigger_id"], field="trigger_id"),
        "trigger_version": _text(value["trigger_version"], field="trigger_version"),
        "trigger_occurrence_id": _text(value["trigger_occurrence_id"], field="trigger_occurrence_id"),
        "reference_key": _text(value["reference_key"], field="reference_key"),
        "indicator_id": _optional_text(value["indicator_id"], field="indicator_id"),
        "timeframe": _text(value["timeframe"], field="timeframe"),
        "level_id": _text(value["level_id"], field="level_id"),
    }


def generic_fixed_direction_binding_digest(
    *,
    configuration_binding_digest: str,
    fixed_direction: Direction,
) -> str:
    if fixed_direction not in {Direction.LONG, Direction.SHORT}:
        raise SetHandlerError("fixed_direction must be LONG or SHORT")
    return canonical_json_digest(
        {
            "binding": "SET_GENERIC_FIXED_DIRECTION_V1",
            "configuration_binding_digest": _digest(configuration_binding_digest, field="configuration_binding_digest"),
            "fixed_direction": fixed_direction.value,
        }
    )


def _assert_existing_payload(record: OwnerStateRecord, expected: Mapping[str, Any], *, label: str) -> None:
    if record.payload_digest != canonical_json_digest(expected):
        raise SetResultConflict(f"{label} identity replayed with different content")


def _q18_text(value: str, *, field: str) -> str:
    try:
        parsed = parse_decimal_text(value)
        wire = q18_wire(parsed).text
    except NumericPolicyError as exc:
        raise SetHandlerError(f"{field} must be a TT_SET_NUMERIC_V1 decimal") from exc
    if wire != value:
        raise SetHandlerError(f"{field} must already be a canonical Q18 wire value")
    return value


def _positive_decimal_text(value: str, *, field: str) -> str:
    try:
        parsed = parse_decimal_text(value)
    except NumericPolicyError as exc:
        raise SetHandlerError(f"{field} must be a canonical decimal string") from exc
    if parsed <= 0:
        raise SetHandlerError(f"{field} must be positive")
    return value


def _set_family(value: str) -> str:
    if value not in {"TREND_CONTINUATION", "RANGE", "BREAKOUT_RECLAIM", "GENERIC"}:
        raise SetHandlerError("set_family is invalid")
    return value


def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise SetHandlerError(f"{field} is required")
    return value


def _optional_text(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field=field)


def _digest(value: Any, *, field: str) -> str:
    text = _text(value, field=field)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise SetHandlerError(f"{field} must be a lowercase sha256 digest")
    return text


__all__ = [
    "DeclaredConflictRule",
    "DirectionResolutionScope",
    "GenericFixedDirectionBinding",
    "GenericBranchEvidence",
    "HandoffContext",
    "HandoffFacts",
    "HandoffReferenceLevel",
    "SetDurableHandler",
    "SetHandlerError",
    "SetMatchStatus",
    "SetResolutionRecord",
    "SetResolutionRequest",
    "SetResultConflict",
    "generic_fixed_direction_binding_digest",
]
