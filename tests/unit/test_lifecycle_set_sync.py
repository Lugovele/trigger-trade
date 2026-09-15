from __future__ import annotations

import pytest

from triggertrade.lifecycle_order_events import build_order_event_from_submission
from triggertrade.lifecycle_set_sync import LifecycleSetSyncError, build_lifecycle_set_sync_from_order_event
from tests.unit.test_lifecycle_submission_store import fake_submission_record


def placed_event_payload(*, event_id: str = "order-event-1", lifecycle_revision: int = 1) -> dict:
    return build_order_event_from_submission(
        fake_submission_record(lifecycle_state="SUBMITTED", exchange_order_id="exchange-1"),
        event_id=event_id,
        occurred_at="2026-09-14T12:00:00Z",
        lifecycle_revision=lifecycle_revision,
    ).payload


def terminal_event_payload(
    *,
    event_id: str = "order-event-terminal-1",
    event_type: str = "CANCELLED_ZERO_FILL",
    lifecycle_revision: int = 2,
) -> dict:
    payload = placed_event_payload(event_id=event_id, lifecycle_revision=lifecycle_revision)
    payload["order_event"]["event_type"] = event_type
    payload["order_event"]["occurred_at"] = "2026-09-14T12:01:00Z"
    return payload


def test_order_event_with_exchange_acceptance_builds_order_placed_v3_sync():
    sync = build_lifecycle_set_sync_from_order_event(placed_event_payload())

    assert sync is not None
    assert sync.definition == "ORDER_PLACED.placed"
    assert sync.source_order_event_id == "order-event-1"
    assert sync.payload == {
        "order_placed": {
            "contract_version": 3,
            "event_id": "order-placed-9c6314924e273662e5bb5eae",
            "lifecycle_revision": 1,
            "decision_cycle_id": "decision-cycle-1",
            "set_result_id": "set-result-1",
            "position_plan_id": "position-plan-1",
            "tranche_id": "tranche-1",
            "symbol": "BTCUSDT",
            "client_order_link_id": "client-order-1",
            "exchange_order_id": "exchange-1",
            "order_placed_at": "2026-09-14T12:00:00Z",
        }
    }
    assert sync.payload_digest == "24c8f9dc8f664e266e95f8bcafb1a5d3ae58206945d56bd562490bbccfeeac0e"


def test_ambiguous_submission_without_exchange_order_id_does_not_emit_sync():
    payload = build_order_event_from_submission(
        fake_submission_record(lifecycle_state="SUBMITTED", exchange_order_id=None),
        event_id="order-event-ambiguous",
        occurred_at="2026-09-14T12:00:00Z",
        lifecycle_revision=1,
    ).payload

    assert build_lifecycle_set_sync_from_order_event(payload) is None


def test_terminal_entry_event_builds_terminal_v3_sync():
    sync = build_lifecycle_set_sync_from_order_event(terminal_event_payload(event_type="FULL_FILL"))

    assert sync is not None
    assert sync.definition == "ORDER_PLACED.terminal"
    assert sync.payload == {
        "entry_lifecycle_event": {
            "contract_version": 3,
            "event_id": "entry-lifecycle-002cbd71e4cbd99b08a32b27",
            "lifecycle_revision": 2,
            "decision_cycle_id": "decision-cycle-1",
            "set_result_id": "set-result-1",
            "tranche_id": "tranche-1",
            "symbol": "BTCUSDT",
            "event_type": "FULL_FILL",
            "occurred_at": "2026-09-14T12:01:00Z",
        }
    }


def test_invalid_terminal_event_type_remains_non_sync_eligible_without_placement():
    payload = terminal_event_payload(event_type="NOT_TERMINAL")
    payload["order_event"]["order_leg"]["exchange_order_id"] = None

    assert build_lifecycle_set_sync_from_order_event(payload) is None


def test_unknown_order_event_field_is_rejected_before_sync_building():
    payload = placed_event_payload()
    payload["order_event"]["unexpected"] = "nope"

    with pytest.raises(LifecycleSetSyncError, match="unknown fields"):
        build_lifecycle_set_sync_from_order_event(payload)
