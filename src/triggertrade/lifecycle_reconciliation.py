"""Lifecycle native observation and reconciliation evidence helpers."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.contracts import ContractError, ContractType, parse_contract


class LifecycleReconciliationError(ValueError):
    """Raised when Lifecycle reconciliation evidence cannot be represented."""


NATIVE_EVIDENCE_VARIANTS = frozenset(
    {
        "NATIVE_UNATTRIBUTED_REDUCTION",
        "NATIVE_ATTRIBUTION_RESOLUTION",
        "NATIVE_SCOPE_RECONCILIATION_OBSERVED",
        "NATIVE_SCOPE_RECONCILIATION_RESOLUTION",
    }
)


@dataclass(frozen=True)
class LifecycleReconciliationEvidence:
    payload: dict[str, Any]
    evidence_kind: str
    evidence_id: str
    native_observation_id: str
    native_scope_revision: int
    revision_id: str
    evidence_revision: int
    native_scope: dict[str, Any]
    payload_digest: str
    complete: bool

    @property
    def body(self) -> dict[str, Any]:
        return self.payload["order_event"]


def validate_reconciliation_event(payload: dict[str, Any]) -> LifecycleReconciliationEvidence:
    try:
        parsed = parse_contract(ContractType.ORDER_EVENT, payload, version=7)
    except ContractError as exc:
        raise LifecycleReconciliationError(str(exc)) from exc
    resolved = parsed.to_payload()
    body = resolved["order_event"]
    variant = body["event_variant"]
    if variant not in NATIVE_EVIDENCE_VARIANTS:
        raise LifecycleReconciliationError(f"unsupported reconciliation event variant: {variant}")
    native_observation_id, native_scope_revision, revision_id, revision, native_scope, complete = _identity_fields(body)
    return LifecycleReconciliationEvidence(
        payload=resolved,
        evidence_kind=variant,
        evidence_id=_text(body["event_id"], field="event_id"),
        native_observation_id=native_observation_id,
        native_scope_revision=native_scope_revision,
        revision_id=revision_id,
        evidence_revision=revision,
        native_scope=dict(native_scope),
        payload_digest=canonical_json_digest(resolved),
        complete=complete,
    )


def native_observation_id_for_scope(native_scope: dict[str, Any], *, source_identity: str) -> str:
    basis = ["NATIVE_OBSERVATION_V1", native_scope, _text(source_identity, field="source_identity")]
    return f"native-observation-{_digest(basis)}"


def attribution_resolution_id_for_observation(native_observation_id: str) -> str:
    basis = ["ATTRIBUTION_RESOLUTION_V1", _text(native_observation_id, field="native_observation_id")]
    return f"attribution-resolution-{_digest(basis)}"


def reconciliation_resolution_id_for_observation(native_observation_id: str) -> str:
    basis = ["NATIVE_SCOPE_RESOLUTION_V1", _text(native_observation_id, field="native_observation_id")]
    return f"scope-resolution-{_digest(basis)}"


def _identity_fields(body: dict[str, Any]) -> tuple[str, int, str, int, dict[str, Any], bool]:
    variant = body["event_variant"]
    if variant in {"NATIVE_UNATTRIBUTED_REDUCTION", "NATIVE_SCOPE_RECONCILIATION_OBSERVED"}:
        observation = body["native_observation"]
        revision_id = observation.get("reconciliation_resolution_id") or observation["native_observation_id"]
        return (
            _text(observation["native_observation_id"], field="native_observation_id"),
            _revision(observation["native_scope_revision"], field="native_scope_revision"),
            _text(revision_id, field="revision_id"),
            _revision(observation.get("resolution_revision", observation["native_scope_revision"]), field="evidence_revision"),
            observation["native_scope"],
            False,
        )
    resolution = body["resolution"]
    revision_id = resolution.get("attribution_resolution_id") or resolution["reconciliation_resolution_id"]
    return (
        _text(resolution["native_observation_id"], field="native_observation_id"),
        _revision(resolution["native_scope_revision"], field="native_scope_revision"),
        _text(revision_id, field="revision_id"),
        _revision(resolution["resolution_revision"], field="resolution_revision"),
        resolution["native_scope"],
        bool(resolution["resolution_complete"]),
    )


def _digest(value: Any) -> str:
    return sha256(canonical_json_digest(value).encode("utf-8")).hexdigest()[:24]


def _revision(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise LifecycleReconciliationError(f"{field} must be a nonnegative integer")
    return value


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise LifecycleReconciliationError(f"{field} is required")
    return value
