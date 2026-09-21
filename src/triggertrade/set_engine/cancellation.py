"""Set-owned F-013 pending-entry monitor and cancel-signal production."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.contracts import BindingRole, ContractType, validate_contract_edge
from triggertrade.numeric_policy import NumericPolicyError, compare_exact, parse_decimal_text
from triggertrade.persistence.durable_messages import DurableMessageStore
from triggertrade.persistence.postgres import OwnerStateConflict, OwnerStateStore, PostgresPersistenceError


class F013MonitorError(ValueError):
    """Raised when pending-entry monitoring cannot be represented safely."""


class F013MonitorConflict(PostgresPersistenceError):
    """Raised when a monitor identity is replayed with conflicting content."""


class F013PredicateStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class F013PredicateOutcome(StrEnum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID_CONDITION = "INVALID_CONDITION"


class F013PendingValidity(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"
    STOPPED = "STOPPED"
    DEFERRED_UNBOUND = "DEFERRED_UNBOUND"


class F013Action(StrEnum):
    NO_MESSAGE = "NO_MESSAGE"
    EMIT_ORDER_CANCEL_SIGNAL = "EMIT_ORDER_CANCEL_SIGNAL"
    FAIL_CLOSED_RECONCILE_THEN_CANCEL_IF_STILL_PENDING = "FAIL_CLOSED_RECONCILE_THEN_CANCEL_IF_STILL_PENDING"
    RETAIN_UNBOUND_TRANSITION = "RETAIN_UNBOUND_TRANSITION"


class F013UnavailableReason(StrEnum):
    ACTIVATION_IDENTITY_INVALID = "ACTIVATION_IDENTITY_INVALID"
    FROZEN_RECORD_INVALID_OR_UNRESOLVED = "FROZEN_RECORD_INVALID_OR_UNRESOLVED"
    INVALID_CONDITION = "INVALID_CONDITION"
    REQUIRED_EVIDENCE_UNAVAILABLE = "REQUIRED_EVIDENCE_UNAVAILABLE"


class F013PredicateOperator(StrEnum):
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    EQ = "EQ"


@dataclass(frozen=True)
class F013OrderPlacedBinding:
    decision_cycle_id: str
    set_result_id: str
    tranche_id: str
    symbol: str
    client_order_link_id: str
    exchange_order_id: str
    order_placed_at: str
    lifecycle_revision: int

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "F013OrderPlacedBinding":
        parsed = validate_contract_edge(
            producer=BindingRole.LIFECYCLE,
            consumer=BindingRole.SET,
            contract_type=ContractType.ORDER_PLACED,
            payload=payload,
            definition="ORDER_PLACED.placed",
        )
        body = parsed.to_payload()["order_placed"]
        return cls(
            decision_cycle_id=_text(body["decision_cycle_id"], field="decision_cycle_id"),
            set_result_id=_text(body["set_result_id"], field="set_result_id"),
            tranche_id=_text(body["tranche_id"], field="tranche_id"),
            symbol=_symbol(body["symbol"]),
            client_order_link_id=_text(body["client_order_link_id"], field="client_order_link_id"),
            exchange_order_id=_text(body["exchange_order_id"], field="exchange_order_id"),
            order_placed_at=_text(body["order_placed_at"], field="order_placed_at"),
            lifecycle_revision=_nonnegative_int(body["lifecycle_revision"], field="lifecycle_revision"),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "decision_cycle_id": self.decision_cycle_id,
            "set_result_id": self.set_result_id,
            "tranche_id": self.tranche_id,
            "symbol": self.symbol,
            "client_order_link_id": self.client_order_link_id,
            "exchange_order_id": self.exchange_order_id,
            "order_placed_at": self.order_placed_at,
            "lifecycle_revision": self.lifecycle_revision,
        }


@dataclass(frozen=True)
class F013TerminalBinding:
    decision_cycle_id: str
    set_result_id: str
    tranche_id: str
    symbol: str
    event_type: str
    occurred_at: str
    lifecycle_revision: int

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "F013TerminalBinding":
        parsed = validate_contract_edge(
            producer=BindingRole.LIFECYCLE,
            consumer=BindingRole.SET,
            contract_type=ContractType.ORDER_PLACED,
            payload=payload,
            definition="ORDER_PLACED.terminal",
        )
        body = parsed.to_payload()["entry_lifecycle_event"]
        return cls(
            decision_cycle_id=_text(body["decision_cycle_id"], field="decision_cycle_id"),
            set_result_id=_text(body["set_result_id"], field="set_result_id"),
            tranche_id=_text(body["tranche_id"], field="tranche_id"),
            symbol=_symbol(body["symbol"]),
            event_type=_text(body["event_type"], field="event_type"),
            occurred_at=_text(body["occurred_at"], field="occurred_at"),
            lifecycle_revision=_nonnegative_int(body["lifecycle_revision"], field="lifecycle_revision"),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "decision_cycle_id": self.decision_cycle_id,
            "set_result_id": self.set_result_id,
            "tranche_id": self.tranche_id,
            "symbol": self.symbol,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "lifecycle_revision": self.lifecycle_revision,
        }


@dataclass(frozen=True)
class F013PredicateObservation:
    condition_id: str
    status: F013PredicateStatus
    observed_value: str | None
    evidence_digest: str | None
    evidence_effective_at: str | None

    def to_payload(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "status": self.status.value,
            "observed_value": self.observed_value,
            "evidence_digest": self.evidence_digest,
            "evidence_effective_at": self.evidence_effective_at,
        }


@dataclass(frozen=True)
class F013EvaluationRequest:
    decision_cycle_id: str
    set_result_id: str
    tranche_id: str
    symbol: str
    condition_record_id: str
    evaluated_at: str
    source_event_id: str
    placement: F013OrderPlacedBinding | None
    observations: tuple[F013PredicateObservation, ...] = ()
    terminal: F013TerminalBinding | None = None


@dataclass(frozen=True)
class F013EvaluationResult:
    pending_validity: F013PendingValidity
    action: F013Action
    reason_code: str | None
    signal_id: str | None
    signal_payload: dict[str, Any] | None
    outbox_inserted: bool
    state_inserted: bool


@dataclass(frozen=True)
class _FrozenCondition:
    condition_record_id: str
    decision_cycle_id: str
    set_result_id: str
    symbol: str
    conditions: tuple["_FrozenPredicate", ...]
    payload_digest: str


@dataclass(frozen=True)
class _FrozenPredicate:
    condition_id: str
    operator: F013PredicateOperator
    threshold: str
    required: bool = True


@dataclass(frozen=True)
class _PredicateEvaluation:
    condition: _FrozenPredicate
    outcome: F013PredicateOutcome
    observation: F013PredicateObservation | None


class F013PendingEntryMonitor:
    """Evaluate frozen F-013 conditions and persist immutable Set outcomes."""

    def __init__(self, connection) -> None:
        self._owner_state = OwnerStateStore(connection)
        self._messages = DurableMessageStore(connection)

    def evaluate(self, request: F013EvaluationRequest) -> F013EvaluationResult:
        request = _validated_request(request)
        terminal = _matching_terminal(request)
        if terminal is not None:
            payload = _monitor_state_payload(
                request=request,
                pending_validity=F013PendingValidity.STOPPED,
                action=F013Action.NO_MESSAGE,
                reason_code="TERMINAL_ENTRY_EVENT",
                terminal=terminal,
            )
            _, inserted = self._put_monitor_state(request=request, payload=payload, suffix="terminal")
            return F013EvaluationResult(
                pending_validity=F013PendingValidity.STOPPED,
                action=F013Action.NO_MESSAGE,
                reason_code="TERMINAL_ENTRY_EVENT",
                signal_id=None,
                signal_payload=None,
                outbox_inserted=False,
                state_inserted=inserted,
            )
        existing_terminal = self._existing_terminal_result(request)
        if existing_terminal is not None:
            return existing_terminal

        if request.placement is None:
            payload = _monitor_state_payload(
                request=request,
                pending_validity=F013PendingValidity.DEFERRED_UNBOUND,
                action=F013Action.RETAIN_UNBOUND_TRANSITION,
                reason_code=F013UnavailableReason.ACTIVATION_IDENTITY_INVALID.value,
            )
            _, inserted = self._put_monitor_state(request=request, payload=payload, suffix=f"deferred:{request.source_event_id}")
            return F013EvaluationResult(
                pending_validity=F013PendingValidity.DEFERRED_UNBOUND,
                action=F013Action.RETAIN_UNBOUND_TRANSITION,
                reason_code=F013UnavailableReason.ACTIVATION_IDENTITY_INVALID.value,
                signal_id=None,
                signal_payload=None,
                outbox_inserted=False,
                state_inserted=inserted,
            )

        activation_reason = _activation_mismatch_reason(request)
        frozen = self._load_frozen_condition(request.condition_record_id)
        frozen_reason = _frozen_record_reason(request, frozen)
        evaluations = tuple(_evaluate_conditions(frozen, request.observations)) if frozen_reason is None else ()
        unavailable_reason = activation_reason or frozen_reason or _unavailable_reason(evaluations)
        true_evaluation = next((item for item in evaluations if item.outcome is F013PredicateOutcome.TRUE), None)

        if unavailable_reason == F013UnavailableReason.ACTIVATION_IDENTITY_INVALID:
            payload = _monitor_state_payload(
                request=request,
                pending_validity=F013PendingValidity.DEFERRED_UNBOUND,
                action=F013Action.RETAIN_UNBOUND_TRANSITION,
                reason_code=F013UnavailableReason.ACTIVATION_IDENTITY_INVALID.value,
                frozen=frozen,
            )
            _, inserted = self._put_monitor_state(
                request=request,
                payload=payload,
                suffix=f"activation-invalid:{request.source_event_id}",
            )
            return F013EvaluationResult(
                pending_validity=F013PendingValidity.DEFERRED_UNBOUND,
                action=F013Action.RETAIN_UNBOUND_TRANSITION,
                reason_code=F013UnavailableReason.ACTIVATION_IDENTITY_INVALID.value,
                signal_id=None,
                signal_payload=None,
                outbox_inserted=False,
                state_inserted=inserted,
            )
        if true_evaluation is not None:
            return self._emit_or_join_invalidation(request=request, frozen=frozen, evaluation=true_evaluation)
        sticky_unavailable = self._existing_unavailable_result(request)
        if sticky_unavailable is not None:
            return sticky_unavailable
        if unavailable_reason is not None:
            return self._emit_or_join_unavailable(request=request, frozen=frozen, reason=unavailable_reason)

        payload = _monitor_state_payload(
            request=request,
            pending_validity=F013PendingValidity.VALID,
            action=F013Action.NO_MESSAGE,
            reason_code=None,
            frozen=frozen,
            evaluations=evaluations,
        )
        _, inserted = self._put_monitor_state(request=request, payload=payload, suffix=f"valid:{request.source_event_id}")
        return F013EvaluationResult(
            pending_validity=F013PendingValidity.VALID,
            action=F013Action.NO_MESSAGE,
            reason_code=None,
            signal_id=None,
            signal_payload=None,
            outbox_inserted=False,
            state_inserted=inserted,
        )

    def _load_frozen_condition(self, condition_record_id: str) -> _FrozenCondition | None:
        record = self._owner_state.get(owner="SET", state_type="SET_FROZEN_CONDITION", state_id=condition_record_id)
        if record is None:
            return None
        return _frozen_condition_from_payload(record.payload, payload_digest=record.payload_digest)

    def _emit_or_join_invalidation(
        self,
        *,
        request: F013EvaluationRequest,
        frozen: _FrozenCondition | None,
        evaluation: _PredicateEvaluation,
    ) -> F013EvaluationResult:
        if frozen is None or evaluation.observation is None:
            raise F013MonitorError("INVALIDATION requires a frozen condition and selected evidence")
        observation = evaluation.observation
        if observation.evidence_digest is None or observation.evidence_effective_at is None:
            raise F013MonitorError("TRUE invalidation requires evidence digest and effective time")
        signal_id = _signal_id(
            "invalidation",
            request.decision_cycle_id,
            request.set_result_id,
            request.tranche_id,
            request.placement.client_order_link_id if request.placement else "",
            frozen.condition_record_id,
            evaluation.condition.condition_id,
        )
        payload = {
            "order_cancel_signal": {
                "contract_version": 2,
                "cause": "INVALIDATION",
                "signal_id": signal_id,
                "decision_cycle_id": request.decision_cycle_id,
                "set_result_id": request.set_result_id,
                "tranche_id": request.tranche_id,
                "symbol": request.symbol,
                "invalidated_at": observation.evidence_effective_at,
                "reason_code": "F013_FROZEN_CONDITION_TRUE",
                "condition_record_id": frozen.condition_record_id,
                "condition_id": evaluation.condition.condition_id,
                "evidence_digest": observation.evidence_digest,
            }
        }
        return self._persist_signal(
            request=request,
            signal_id=signal_id,
            signal_state_type="F013_INVALIDATION_SIGNAL",
            payload=payload,
            pending_validity=F013PendingValidity.INVALID,
            reason_code="F013_FROZEN_CONDITION_TRUE",
            frozen=frozen,
        )

    def _existing_terminal_result(self, request: F013EvaluationRequest) -> F013EvaluationResult | None:
        state_id = _signal_id("monitor", request.decision_cycle_id, request.set_result_id, request.tranche_id, "terminal")
        existing = self._owner_state.get(owner="SET", state_type="F013_MONITOR_STATE", state_id=state_id)
        if existing is None:
            return None
        terminal = existing.payload["f013_monitor_state"].get("terminal")
        terminal_revision = None if terminal is None else terminal.get("lifecycle_revision")
        if (
            request.placement is not None
            and isinstance(terminal_revision, int)
            and terminal_revision < request.placement.lifecycle_revision
        ):
            return None
        return F013EvaluationResult(
            pending_validity=F013PendingValidity.STOPPED,
            action=F013Action.NO_MESSAGE,
            reason_code=existing.payload["f013_monitor_state"]["reason_code"],
            signal_id=None,
            signal_payload=None,
            outbox_inserted=False,
            state_inserted=False,
        )

    def _emit_or_join_unavailable(
        self,
        *,
        request: F013EvaluationRequest,
        frozen: _FrozenCondition | None,
        reason: F013UnavailableReason,
    ) -> F013EvaluationResult:
        if request.placement is None:
            raise F013MonitorError("MONITORING_UNAVAILABLE publication requires exact placement binding")
        requirement_id = _signal_id(
            "unavailable",
            request.decision_cycle_id,
            request.set_result_id,
            request.tranche_id,
            request.placement.client_order_link_id,
        )
        existing = self._existing_unavailable_result(request, requirement_id=requirement_id)
        if existing is not None:
            return existing

        body = {
            "contract_version": 2,
            "cause": "MONITORING_UNAVAILABLE",
            "signal_id": requirement_id,
            "decision_cycle_id": request.decision_cycle_id,
            "set_result_id": request.set_result_id,
            "tranche_id": request.tranche_id,
            "symbol": request.symbol,
            "unavailable_requirement_id": requirement_id,
            "unavailable_at": request.evaluated_at,
            "unavailable_reason_code": reason.value,
        }
        if frozen is not None:
            body["condition_record_id"] = frozen.condition_record_id
        payload = {"order_cancel_signal": body}
        return self._persist_signal(
            request=request,
            signal_id=requirement_id,
            signal_state_type="F013_UNAVAILABLE_REQUIREMENT",
            payload=payload,
            pending_validity=F013PendingValidity.UNAVAILABLE,
            reason_code=reason.value,
            frozen=frozen,
        )

    def _existing_unavailable_result(
        self,
        request: F013EvaluationRequest,
        *,
        requirement_id: str | None = None,
    ) -> F013EvaluationResult | None:
        if request.placement is None:
            return None
        resolved_id = requirement_id or _signal_id(
            "unavailable",
            request.decision_cycle_id,
            request.set_result_id,
            request.tranche_id,
            request.placement.client_order_link_id,
        )
        existing = self._owner_state.get(owner="SET", state_type="F013_UNAVAILABLE_REQUIREMENT", state_id=resolved_id)
        if existing is None:
            return None
        payload = existing.payload["f013_signal_state"]["order_cancel_signal_payload"]
        original_source_event_id = existing.payload["f013_signal_state"]["source_event_id"]
        outbox_inserted = self._append_signal_outbox(
            request=request,
            signal_id=resolved_id,
            payload=payload,
            causation_id=original_source_event_id,
        )
        return F013EvaluationResult(
            pending_validity=F013PendingValidity.UNAVAILABLE,
            action=F013Action.FAIL_CLOSED_RECONCILE_THEN_CANCEL_IF_STILL_PENDING,
            reason_code=payload["order_cancel_signal"]["unavailable_reason_code"],
            signal_id=resolved_id,
            signal_payload=payload,
            outbox_inserted=outbox_inserted,
            state_inserted=False,
        )

    def _persist_signal(
        self,
        *,
        request: F013EvaluationRequest,
        signal_id: str,
        signal_state_type: str,
        payload: dict[str, Any],
        pending_validity: F013PendingValidity,
        reason_code: str,
        frozen: _FrozenCondition | None,
    ) -> F013EvaluationResult:
        parsed = validate_contract_edge(
            producer=BindingRole.SET,
            consumer=BindingRole.LIFECYCLE,
            contract_type=ContractType.ORDER_CANCEL_SIGNAL,
            payload=payload,
            definition="ORDER_CANCEL_SIGNAL",
        )
        signal_payload = parsed.to_payload()
        state_payload = _signal_state_payload(
            request=request,
            signal_payload=signal_payload,
            pending_validity=pending_validity,
            reason_code=reason_code,
            frozen=frozen,
        )
        try:
            record, inserted = self._owner_state.put_if_absent(
                owner="SET",
                state_type=signal_state_type,
                state_id=signal_id,
                payload=state_payload,
            )
        except OwnerStateConflict as exc:
            raise F013MonitorConflict("F-013 signal identity already exists with different content") from exc
        _assert_payload(record.payload, state_payload, label="F-013 signal")
        outbox_inserted = self._append_signal_outbox(request=request, signal_id=signal_id, payload=signal_payload)
        return F013EvaluationResult(
            pending_validity=pending_validity,
            action=F013Action.EMIT_ORDER_CANCEL_SIGNAL
            if pending_validity is F013PendingValidity.INVALID
            else F013Action.FAIL_CLOSED_RECONCILE_THEN_CANCEL_IF_STILL_PENDING,
            reason_code=reason_code,
            signal_id=signal_id,
            signal_payload=signal_payload,
            outbox_inserted=outbox_inserted,
            state_inserted=inserted,
        )

    def _append_signal_outbox(
        self,
        *,
        request: F013EvaluationRequest,
        signal_id: str,
        payload: Mapping[str, Any],
        causation_id: str | None = None,
    ) -> bool:
        outbox, _, inserted = self._messages.append_frontier_outbox(
            scope_key=f"SET_CANCEL:{request.decision_cycle_id}",
            message_id=signal_id,
            producer="Set",
            consumer="Order Lifecycle",
            message_type="ORDER_CANCEL_SIGNAL",
            message_version="2",
            payload=payload,
            aggregate_id=request.decision_cycle_id,
            causation_id=causation_id or request.source_event_id,
            correlation_id=request.decision_cycle_id,
            dedupe_key=f"ORDER_CANCEL_SIGNAL:{signal_id}",
        )
        if outbox.payload_digest != canonical_json_digest(payload):
            raise PostgresPersistenceError("ORDER_CANCEL_SIGNAL outbox digest mismatch")
        return inserted

    def _put_monitor_state(
        self,
        *,
        request: F013EvaluationRequest,
        payload: Mapping[str, Any],
        suffix: str,
    ):
        state_id = _signal_id("monitor", request.decision_cycle_id, request.set_result_id, request.tranche_id, suffix)
        try:
            record, inserted = self._owner_state.put_if_absent(
                owner="SET",
                state_type="F013_MONITOR_STATE",
                state_id=state_id,
                payload=payload,
            )
        except OwnerStateConflict as exc:
            raise F013MonitorConflict("F-013 monitor state identity already exists with different content") from exc
        _assert_payload(record.payload, payload, label="F-013 monitor state")
        return record, inserted


def _validated_request(request: F013EvaluationRequest) -> F013EvaluationRequest:
    _text(request.decision_cycle_id, field="decision_cycle_id")
    _text(request.set_result_id, field="set_result_id")
    _text(request.tranche_id, field="tranche_id")
    symbol = _symbol(request.symbol)
    _text(request.condition_record_id, field="condition_record_id")
    _text(request.evaluated_at, field="evaluated_at")
    _text(request.source_event_id, field="source_event_id")
    if len({obs.condition_id for obs in request.observations}) != len(request.observations):
        raise F013MonitorError("predicate observations must be unique by condition_id")
    return F013EvaluationRequest(
        decision_cycle_id=request.decision_cycle_id,
        set_result_id=request.set_result_id,
        tranche_id=request.tranche_id,
        symbol=symbol,
        condition_record_id=request.condition_record_id,
        evaluated_at=request.evaluated_at,
        source_event_id=request.source_event_id,
        placement=request.placement,
        observations=request.observations,
        terminal=request.terminal,
    )


def _matching_terminal(request: F013EvaluationRequest) -> F013TerminalBinding | None:
    if request.terminal is None:
        return None
    if (
        request.terminal.decision_cycle_id == request.decision_cycle_id
        and request.terminal.set_result_id == request.set_result_id
        and request.terminal.tranche_id == request.tranche_id
        and request.terminal.symbol == request.symbol
        and (request.placement is None or request.terminal.lifecycle_revision >= request.placement.lifecycle_revision)
    ):
        return request.terminal
    return None


def _activation_mismatch_reason(request: F013EvaluationRequest) -> F013UnavailableReason | None:
    placement = request.placement
    if placement is None:
        return F013UnavailableReason.ACTIVATION_IDENTITY_INVALID
    if (
        placement.decision_cycle_id != request.decision_cycle_id
        or placement.set_result_id != request.set_result_id
        or placement.tranche_id != request.tranche_id
        or placement.symbol != request.symbol
    ):
        return F013UnavailableReason.ACTIVATION_IDENTITY_INVALID
    return None


def _frozen_record_reason(
    request: F013EvaluationRequest,
    frozen: _FrozenCondition | None,
) -> F013UnavailableReason | None:
    if frozen is None:
        return F013UnavailableReason.FROZEN_RECORD_INVALID_OR_UNRESOLVED
    if (
        frozen.condition_record_id != request.condition_record_id
        or frozen.decision_cycle_id != request.decision_cycle_id
        or frozen.set_result_id != request.set_result_id
        or frozen.symbol != request.symbol
        or not frozen.conditions
    ):
        return F013UnavailableReason.FROZEN_RECORD_INVALID_OR_UNRESOLVED
    return None


def _frozen_condition_from_payload(payload: Mapping[str, Any], *, payload_digest: str) -> _FrozenCondition | None:
    root = payload.get("set_frozen_condition")
    if not isinstance(root, Mapping):
        return None
    try:
        source_condition = root.get("source_condition")
        conditions = _condition_definitions(source_condition, fallback_condition_id=root.get("condition_id"))
        return _FrozenCondition(
            condition_record_id=_text(root.get("condition_record_id"), field="condition_record_id"),
            decision_cycle_id=_text(root.get("decision_cycle_id"), field="decision_cycle_id"),
            set_result_id=_text(root.get("set_result_id"), field="set_result_id"),
            symbol=_symbol(root.get("symbol")),
            conditions=conditions,
            payload_digest=payload_digest,
        )
    except (F013MonitorError, ValueError):
        return None


def _condition_definitions(source_condition: Any, *, fallback_condition_id: Any) -> tuple[_FrozenPredicate, ...]:
    if not isinstance(source_condition, Mapping):
        return ()
    raw_conditions = source_condition.get("conditions")
    if raw_conditions is None:
        raw_conditions = (
            {
                "condition_id": source_condition.get("condition_id", fallback_condition_id),
                "operator": source_condition.get("operator"),
                "threshold": source_condition.get("threshold"),
                "required": source_condition.get("required", True),
            },
        )
    if not isinstance(raw_conditions, (list, tuple)):
        return ()
    conditions: list[_FrozenPredicate] = []
    seen: set[str] = set()
    for raw in raw_conditions:
        if not isinstance(raw, Mapping):
            return ()
        condition_id = _text(raw.get("condition_id"), field="condition_id")
        if condition_id in seen:
            raise F013MonitorError("frozen condition IDs must be unique")
        seen.add(condition_id)
        required = raw.get("required", True)
        if not isinstance(required, bool):
            raise F013MonitorError("condition required flag must be boolean")
        conditions.append(
            _FrozenPredicate(
                condition_id=condition_id,
                operator=F013PredicateOperator(_text(raw.get("operator"), field="operator")),
                threshold=_decimal_text(raw.get("threshold"), field="threshold"),
                required=required,
            )
        )
    return tuple(conditions)


def _evaluate_conditions(
    frozen: _FrozenCondition | None,
    observations: tuple[F013PredicateObservation, ...],
) -> tuple[_PredicateEvaluation, ...]:
    if frozen is None:
        return ()
    by_condition = {obs.condition_id: obs for obs in observations}
    return tuple(_evaluate_condition(condition, by_condition.get(condition.condition_id)) for condition in frozen.conditions)


def _evaluate_condition(
    condition: _FrozenPredicate,
    observation: F013PredicateObservation | None,
) -> _PredicateEvaluation:
    if observation is None:
        return _PredicateEvaluation(condition, F013PredicateOutcome.UNAVAILABLE, observation)
    try:
        status = F013PredicateStatus(observation.status)
    except ValueError:
        return _PredicateEvaluation(condition, F013PredicateOutcome.INVALID_CONDITION, observation)
    if status is F013PredicateStatus.UNAVAILABLE:
        return _PredicateEvaluation(condition, F013PredicateOutcome.UNAVAILABLE, observation)
    if observation.observed_value is None or observation.evidence_digest is None or observation.evidence_effective_at is None:
        return _PredicateEvaluation(condition, F013PredicateOutcome.UNAVAILABLE, observation)
    try:
        observed = parse_decimal_text(observation.observed_value)
        threshold = parse_decimal_text(condition.threshold)
    except NumericPolicyError:
        return _PredicateEvaluation(condition, F013PredicateOutcome.INVALID_CONDITION, observation)
    comparison = compare_exact(observed, threshold)
    if condition.operator is F013PredicateOperator.GT:
        result = comparison > 0
    elif condition.operator is F013PredicateOperator.GTE:
        result = comparison >= 0
    elif condition.operator is F013PredicateOperator.LT:
        result = comparison < 0
    elif condition.operator is F013PredicateOperator.LTE:
        result = comparison <= 0
    elif condition.operator is F013PredicateOperator.EQ:
        result = comparison == 0
    else:  # pragma: no cover - StrEnum construction guards this.
        return _PredicateEvaluation(condition, F013PredicateOutcome.INVALID_CONDITION, observation)
    return _PredicateEvaluation(condition, F013PredicateOutcome.TRUE if result else F013PredicateOutcome.FALSE, observation)


def _unavailable_reason(evaluations: tuple[_PredicateEvaluation, ...]) -> F013UnavailableReason | None:
    if any(item.condition.required and item.outcome is F013PredicateOutcome.INVALID_CONDITION for item in evaluations):
        return F013UnavailableReason.INVALID_CONDITION
    if any(item.condition.required and item.outcome is F013PredicateOutcome.UNAVAILABLE for item in evaluations):
        return F013UnavailableReason.REQUIRED_EVIDENCE_UNAVAILABLE
    return None


def _monitor_state_payload(
    *,
    request: F013EvaluationRequest,
    pending_validity: F013PendingValidity,
    action: F013Action,
    reason_code: str | None,
    frozen: _FrozenCondition | None = None,
    evaluations: tuple[_PredicateEvaluation, ...] = (),
    terminal: F013TerminalBinding | None = None,
) -> dict[str, Any]:
    return {
        "f013_monitor_state": {
            "schema_version": "F013_MONITOR_B6_V1",
            "decision_cycle_id": request.decision_cycle_id,
            "set_result_id": request.set_result_id,
            "tranche_id": request.tranche_id,
            "symbol": request.symbol,
            "condition_record_id": request.condition_record_id,
            "pending_validity": pending_validity.value,
            "action": action.value,
            "reason_code": reason_code,
            "evaluated_at": request.evaluated_at,
            "source_event_id": request.source_event_id,
            "placement": None if request.placement is None else request.placement.to_payload(),
            "terminal": None if terminal is None else terminal.to_payload(),
            "frozen_record_digest": None if frozen is None else frozen.payload_digest,
            "evaluations": [_evaluation_payload(item) for item in evaluations],
        }
    }


def _signal_state_payload(
    *,
    request: F013EvaluationRequest,
    signal_payload: Mapping[str, Any],
    pending_validity: F013PendingValidity,
    reason_code: str,
    frozen: _FrozenCondition | None,
) -> dict[str, Any]:
    return {
        "f013_signal_state": {
            "schema_version": "F013_SIGNAL_B6_V1",
            "decision_cycle_id": request.decision_cycle_id,
            "set_result_id": request.set_result_id,
            "tranche_id": request.tranche_id,
            "symbol": request.symbol,
            "pending_validity": pending_validity.value,
            "reason_code": reason_code,
            "source_event_id": request.source_event_id,
            "placement": None if request.placement is None else request.placement.to_payload(),
            "frozen_record_digest": None if frozen is None else frozen.payload_digest,
            "order_cancel_signal_payload": dict(signal_payload),
            "order_cancel_signal_digest": canonical_json_digest(signal_payload),
        }
    }


def _evaluation_payload(item: _PredicateEvaluation) -> dict[str, Any]:
    return {
        "condition_id": item.condition.condition_id,
        "operator": item.condition.operator.value,
        "threshold": item.condition.threshold,
        "required": item.condition.required,
        "outcome": item.outcome.value,
        "observation": None if item.observation is None else item.observation.to_payload(),
    }


def _signal_id(prefix: str, *parts: str) -> str:
    digest = canonical_json_digest({"prefix": prefix, "parts": list(parts)})
    return f"f013-{prefix}-{digest[:32]}"


def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise F013MonitorError(f"{field} is required")
    return value


def _symbol(value: Any) -> str:
    return _text(value, field="symbol").upper()


def _decimal_text(value: Any, *, field: str) -> str:
    text = _text(value, field=field)
    try:
        parse_decimal_text(text)
    except NumericPolicyError as exc:
        raise F013MonitorError(f"{field} must be exact decimal text") from exc
    return text


def _nonnegative_int(value: Any, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise F013MonitorError(f"{field} must be a nonnegative integer")
    return value


def _assert_payload(actual: Mapping[str, Any], expected: Mapping[str, Any], *, label: str) -> None:
    if actual != expected:
        raise F013MonitorConflict(f"{label} identity already exists with different content")
