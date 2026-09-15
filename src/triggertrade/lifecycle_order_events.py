"""Order Event v7 payload helpers for the target Lifecycle ledger."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.contracts import ContractError, ContractType, parse_contract


class LifecycleOrderEventError(ValueError):
    """Raised when a Lifecycle Order Event cannot be represented."""


@dataclass(frozen=True)
class LifecycleOrderEvent:
    payload: dict[str, Any]
    definition: str
    payload_digest: str

    @property
    def body(self) -> dict[str, Any]:
        return self.payload["order_event"]


def validate_order_event(payload: dict[str, Any]) -> LifecycleOrderEvent:
    try:
        parsed = parse_contract(ContractType.ORDER_EVENT, payload, version=7)
    except ContractError as exc:
        raise LifecycleOrderEventError(str(exc)) from exc
    resolved = parsed.to_payload()
    return LifecycleOrderEvent(payload=resolved, definition=parsed.definition, payload_digest=canonical_json_digest(resolved))


def build_order_event_from_submission(
    record: Any,
    *,
    event_id: str | None = None,
    event_type: str = "ENTRY_SUBMISSION_INTENT",
    occurred_at: str,
    lifecycle_revision: int = 0,
) -> LifecycleOrderEvent:
    state = _submission_state(record.lifecycle_state)
    accepted = _accepted_fields(record)
    payload = _logical_payload(
        event_id=event_id or _event_id("submission", record.submission_intent_id, str(lifecycle_revision)),
        event_type=event_type,
        occurred_at=occurred_at,
        lifecycle_revision=lifecycle_revision,
        authorization_id=record.authorization_id,
        capital_grant_id=record.capital_grant_id,
        decision_cycle_id=record.decision_cycle_id,
        set_result_id=record.set_result_id,
        position_decision_id=record.position_decision_id,
        construction_result_id=record.construction_result_id,
        position_plan_id=record.position_plan_id,
        tranche_id=record.tranche_id,
        order_spec_id=record.order_spec_id,
        symbol=record.symbol,
        client_order_link_id=record.target_client_order_id,
        exchange_order_id=record.exchange_order_id,
        lifecycle_state=state,
        entry_accepted_at=accepted["entry_accepted_at"],
        entry_acceptance_status=accepted["entry_acceptance_status"],
        entry_acceptance_provenance=None,
    )
    return validate_order_event(payload)


def _logical_payload(
    *,
    event_id: str,
    event_type: str,
    occurred_at: str,
    lifecycle_revision: int,
    authorization_id: str | None,
    capital_grant_id: str,
    decision_cycle_id: str,
    set_result_id: str,
    position_decision_id: str,
    construction_result_id: str,
    position_plan_id: str,
    tranche_id: str,
    order_spec_id: str,
    symbol: str,
    client_order_link_id: str | None,
    exchange_order_id: str | None,
    lifecycle_state: str,
    entry_accepted_at: str | None,
    entry_acceptance_status: str,
    entry_acceptance_provenance: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "order_event": {
            "contract_version": 7,
            "event_variant": "LOGICAL_TRANCHE",
            "event_id": _text(event_id, field="event_id"),
            "event_type": _text(event_type, field="event_type"),
            "occurred_at": _text(occurred_at, field="occurred_at"),
            "lifecycle_revision": _revision(lifecycle_revision),
            "authorization_id": authorization_id,
            "capital_grant_id": _text(capital_grant_id, field="capital_grant_id"),
            "decision_cycle_id": _text(decision_cycle_id, field="decision_cycle_id"),
            "set_result_id": _text(set_result_id, field="set_result_id"),
            "position_decision_id": _text(position_decision_id, field="position_decision_id"),
            "construction_result_id": _text(construction_result_id, field="construction_result_id"),
            "position_plan_id": _text(position_plan_id, field="position_plan_id"),
            "tranche_id": _text(tranche_id, field="tranche_id"),
            "order_spec_id": _text(order_spec_id, field="order_spec_id"),
            "symbol": _text(symbol, field="symbol"),
            "order_leg": {
                "role": "ENTRY",
                "client_order_link_id": client_order_link_id,
                "exchange_order_id": exchange_order_id,
                "parent_exchange_order_id": None,
                "protection_generation": None,
                "close_intent_id": None,
                "close_child_id": None,
                "protection_child_id": None,
            },
            "native_allocation": None,
            "lifecycle_state": lifecycle_state,
            "exposure_qty": "0",
            "cumulative_entry_filled_qty": "0",
            "remaining_entry_qty": "0",
            "close_intent_active": False,
            "close_commitment_quantity_basis": None,
            "terminal_predicates": {
                "logical_exposure_zero": False,
                "entry_remainder_terminal": False,
                "children_terminal_or_disabled": False,
                "close_intent_resolved": False,
                "financial_finality_established": False,
                "no_competing_execution_authority": False,
            },
            "external_cause": None,
            "financial_result": None,
            "entry_accepted_at": entry_accepted_at,
            "entry_acceptance_status": entry_acceptance_status,
            "entry_acceptance_provenance": entry_acceptance_provenance,
            "numeric_policy_version": "TT_NUMERIC_V1",
            "entry_acceptance_integrity": {
                "state": "CLEAR",
                "revision": 0,
                "conflict_id": None,
                "evidence": [],
                "resolution_id": None,
                "resolution_evidence_ref": None,
            },
        }
    }


def _accepted_fields(record: LifecycleSubmissionRecord) -> dict[str, str | None]:
    if record.lifecycle_state == "SUBMITTED" and record.exchange_order_id is not None:
        return {"entry_accepted_at": None, "entry_acceptance_status": "UNAVAILABLE"}
    return {"entry_accepted_at": None, "entry_acceptance_status": "UNAVAILABLE"}


def _submission_state(state: str) -> str:
    mapping = {
        "READY_TO_SUBMIT": "READY_TO_SUBMIT",
        "SUBMITTING": "SUBMITTING",
        "SUBMISSION_UNCERTAIN": "SUBMISSION_UNCERTAIN",
        "SUBMITTED": "PENDING_ENTRY",
    }
    try:
        return mapping[state]
    except KeyError as exc:
        raise LifecycleOrderEventError(f"unsupported submission lifecycle state: {state}") from exc


def _event_id(*parts: str) -> str:
    source = ":".join(_text(part, field="event_id_part") for part in parts)
    return f"order-event-{sha256(source.encode('utf-8')).hexdigest()[:24]}"


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise LifecycleOrderEventError(f"{field} is required")
    return value


def _revision(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise LifecycleOrderEventError("lifecycle_revision must be a nonnegative integer")
    return value
