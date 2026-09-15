"""Lifecycle-to-Set Order Placed synchronization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.contracts import ContractError, ContractType, TargetContract, parse_contract
from triggertrade.lifecycle_order_events import LifecycleOrderEventError, validate_order_event


class LifecycleSetSyncError(ValueError):
    """Raised when an Order Event cannot produce a valid Lifecycle-to-Set sync."""


@dataclass(frozen=True)
class LifecycleSetSync:
    payload: dict[str, Any]
    definition: str
    payload_digest: str
    source_order_event_id: str
    decision_cycle_id: str
    lifecycle_revision: int

    @property
    def body(self) -> dict[str, Any]:
        top_key = "order_placed" if self.definition == "ORDER_PLACED.placed" else "entry_lifecycle_event"
        return self.payload[top_key]


TERMINAL_ENTRY_EVENT_TYPES = frozenset(
    {
        "FULL_FILL",
        "CANCELLED_ZERO_FILL",
        "ENTRY_REMAINDER_CANCELLED",
        "SUBMISSION_FAILED_AFTER_PLACEMENT_RECONCILIATION",
    }
)


def build_lifecycle_set_sync_from_order_event(payload: dict[str, Any]) -> LifecycleSetSync | None:
    """Build the canonical ORDER_PLACED v3 sync payload for a logical Order Event.

    Returns ``None`` when the Order Event is not eligible to emit a Set sync
    message, such as ambiguous placement without an exchange order id.
    """

    try:
        order_event = validate_order_event(payload)
    except LifecycleOrderEventError as exc:
        raise LifecycleSetSyncError(str(exc)) from exc
    if order_event.definition != "ORDER_EVENT.logical":
        raise LifecycleSetSyncError("only logical tranche Order Events can produce Lifecycle-to-Set sync")

    body = order_event.body
    event_type = body.get("event_type")
    if event_type in TERMINAL_ENTRY_EVENT_TYPES:
        return _terminal_sync(body)
    return _placed_sync(body)


def _placed_sync(body: dict[str, Any]) -> LifecycleSetSync | None:
    order_leg = _order_leg(body)
    client_order_link_id = order_leg.get("client_order_link_id")
    exchange_order_id = order_leg.get("exchange_order_id")
    if not isinstance(client_order_link_id, str) or not client_order_link_id:
        return None
    if not isinstance(exchange_order_id, str) or not exchange_order_id:
        return None

    sync_body = {
        "contract_version": 3,
        "event_id": _event_id("order-placed", _text(body, "event_id")),
        "lifecycle_revision": _revision(body),
        "decision_cycle_id": _text(body, "decision_cycle_id"),
        "set_result_id": _text(body, "set_result_id"),
        "position_plan_id": _text(body, "position_plan_id"),
        "tranche_id": _text(body, "tranche_id"),
        "symbol": _text(body, "symbol"),
        "client_order_link_id": client_order_link_id,
        "exchange_order_id": exchange_order_id,
        "order_placed_at": _text(body, "occurred_at"),
    }
    return _validated_sync(
        {"order_placed": sync_body},
        definition="ORDER_PLACED.placed",
        source_order_event_id=_text(body, "event_id"),
    )


def _terminal_sync(body: dict[str, Any]) -> LifecycleSetSync:
    sync_body = {
        "contract_version": 3,
        "event_id": _event_id("entry-lifecycle", _text(body, "event_id")),
        "lifecycle_revision": _revision(body),
        "decision_cycle_id": _text(body, "decision_cycle_id"),
        "set_result_id": _text(body, "set_result_id"),
        "tranche_id": _text(body, "tranche_id"),
        "symbol": _text(body, "symbol"),
        "event_type": _text(body, "event_type"),
        "occurred_at": _text(body, "occurred_at"),
    }
    return _validated_sync(
        {"entry_lifecycle_event": sync_body},
        definition="ORDER_PLACED.terminal",
        source_order_event_id=_text(body, "event_id"),
    )


def _validated_sync(
    payload: dict[str, Any],
    *,
    definition: str,
    source_order_event_id: str,
) -> LifecycleSetSync:
    try:
        parsed: TargetContract = parse_contract(ContractType.ORDER_PLACED, payload, version=3, definition=definition)
    except ContractError as exc:
        raise LifecycleSetSyncError(str(exc)) from exc
    resolved = parsed.to_payload()
    body = resolved["order_placed"] if definition == "ORDER_PLACED.placed" else resolved["entry_lifecycle_event"]
    return LifecycleSetSync(
        payload=resolved,
        definition=definition,
        payload_digest=canonical_json_digest(resolved),
        source_order_event_id=source_order_event_id,
        decision_cycle_id=str(body["decision_cycle_id"]),
        lifecycle_revision=int(body["lifecycle_revision"]),
    )


def _order_leg(body: dict[str, Any]) -> dict[str, Any]:
    value = body.get("order_leg")
    if isinstance(value, dict):
        return value
    raise LifecycleSetSyncError("order_event.order_leg must be present")


def _text(body: dict[str, Any], field: str) -> str:
    value = body.get(field)
    if not isinstance(value, str) or not value:
        raise LifecycleSetSyncError(f"order_event.{field} is required")
    return value


def _revision(body: dict[str, Any]) -> int:
    value = body.get("lifecycle_revision")
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise LifecycleSetSyncError("order_event.lifecycle_revision must be a nonnegative integer")
    return value


def _event_id(prefix: str, source_event_id: str) -> str:
    digest = sha256(f"{prefix}:{source_event_id}".encode("utf-8")).hexdigest()[:24]
    return f"{prefix}-{digest}"
