"""Lifecycle submission intent identity and payload helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from triggertrade.canonical_json import canonical_json_digest


READY_TO_SUBMIT = "READY_TO_SUBMIT"
SUBMITTING = "SUBMITTING"
SUBMISSION_UNCERTAIN = "SUBMISSION_UNCERTAIN"
SUBMITTED = "SUBMITTED"
SUBMISSION_STATES = frozenset({READY_TO_SUBMIT, SUBMITTING, SUBMISSION_UNCERTAIN, SUBMITTED})


class LifecycleSubmissionError(ValueError):
    """Raised when a lifecycle submission intent cannot be represented."""


@dataclass(frozen=True)
class LifecycleSubmissionIntent:
    submission_intent_id: str
    start_gate_id: str
    order_spec_id: str
    authorization_id: str
    capital_grant_id: str
    decision_cycle_id: str
    set_result_id: str
    position_decision_id: str
    construction_result_id: str
    position_plan_id: str
    tranche_id: str
    symbol: str
    direction: str
    target_client_order_id: str
    lifecycle_state: str
    order_spec_digest: str
    submit_authorized_digest: str
    start_gate_digest: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "lifecycle_submission_intent": {
                "intent_version": 1,
                "submission_intent_id": self.submission_intent_id,
                "start_gate_id": self.start_gate_id,
                "order_spec_id": self.order_spec_id,
                "authorization_id": self.authorization_id,
                "capital_grant_id": self.capital_grant_id,
                "decision_cycle_id": self.decision_cycle_id,
                "set_result_id": self.set_result_id,
                "position_decision_id": self.position_decision_id,
                "construction_result_id": self.construction_result_id,
                "position_plan_id": self.position_plan_id,
                "tranche_id": self.tranche_id,
                "symbol": self.symbol,
                "direction": self.direction,
                "target_client_order_id": self.target_client_order_id,
                "lifecycle_state": self.lifecycle_state,
                "order_spec_digest": self.order_spec_digest,
                "submit_authorized_digest": self.submit_authorized_digest,
                "start_gate_digest": self.start_gate_digest,
            }
        }


def lifecycle_client_order_id(source_id: str) -> str:
    """Return the deterministic native client order ID for a Lifecycle submit attempt."""

    source_id = _text(source_id, field="source_id")
    return f"ttf-{sha256(source_id.encode('utf-8')).hexdigest()[:24]}"


def build_lifecycle_submission_intent(
    *,
    submission_intent_id: str,
    start_gate: Mapping[str, Any],
    start_gate_digest: str,
    target_client_order_id: str | None = None,
) -> LifecycleSubmissionIntent:
    body = start_gate["lifecycle_start_gate"] if "lifecycle_start_gate" in start_gate else start_gate
    order_spec_id = _text(body.get("order_spec_id"), field="order_spec_id")
    client_order_id = target_client_order_id or lifecycle_client_order_id(order_spec_id)
    return LifecycleSubmissionIntent(
        submission_intent_id=_text(submission_intent_id, field="submission_intent_id"),
        start_gate_id=_text(body.get("start_gate_id"), field="start_gate_id"),
        order_spec_id=order_spec_id,
        authorization_id=_text(body.get("authorization_id"), field="authorization_id"),
        capital_grant_id=_text(body.get("capital_grant_id"), field="capital_grant_id"),
        decision_cycle_id=_text(body.get("decision_cycle_id"), field="decision_cycle_id"),
        set_result_id=_text(body.get("set_result_id"), field="set_result_id"),
        position_decision_id=_text(body.get("position_decision_id"), field="position_decision_id"),
        construction_result_id=_text(body.get("construction_result_id"), field="construction_result_id"),
        position_plan_id=_text(body.get("position_plan_id"), field="position_plan_id"),
        tranche_id=_text(body.get("tranche_id"), field="tranche_id"),
        symbol=_text(body.get("symbol"), field="symbol"),
        direction=_direction(body.get("direction")),
        target_client_order_id=_text(client_order_id, field="target_client_order_id"),
        lifecycle_state=READY_TO_SUBMIT,
        order_spec_digest=_text(body.get("order_spec_digest"), field="order_spec_digest"),
        submit_authorized_digest=_text(body.get("submit_authorized_digest"), field="submit_authorized_digest"),
        start_gate_digest=_text(start_gate_digest, field="start_gate_digest"),
    )


def lifecycle_submission_intent_digest(intent: LifecycleSubmissionIntent) -> str:
    return canonical_json_digest(intent.to_payload())


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise LifecycleSubmissionError(f"{field} is required")
    return value


def _direction(value: object) -> str:
    direction = _text(value, field="direction")
    if direction not in {"LONG", "SHORT"}:
        raise LifecycleSubmissionError("direction must be LONG or SHORT")
    return direction
