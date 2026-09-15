from __future__ import annotations

import pytest

from triggertrade.lifecycle_order_events import (
    LifecycleOrderEventError,
    build_order_event_from_submission,
    validate_order_event,
)
from tests.unit.test_lifecycle_submission_store import fake_submission_record


def test_order_event_from_submission_is_strict_v7_logical_contract():
    record = fake_submission_record(lifecycle_state="SUBMITTED", exchange_order_id="exchange-1")

    event = build_order_event_from_submission(
        record,
        event_id="order-event-1",
        occurred_at="2026-09-14T12:00:00Z",
        lifecycle_revision=1,
    )

    body = event.payload["order_event"]
    assert event.definition == "ORDER_EVENT.logical"
    assert body["contract_version"] == 7
    assert body["event_variant"] == "LOGICAL_TRANCHE"
    assert body["lifecycle_state"] == "PENDING_ENTRY"
    assert body["financial_result"] is None
    assert body["order_leg"]["client_order_link_id"] == "client-order-1"
    assert body["order_leg"]["exchange_order_id"] == "exchange-1"
    assert event.payload_digest == "90f1c88bdd4ecc0e3c6e7ff14cbab3659886659875e26c0994a9fe4bf5d6392e"


def test_order_event_rejects_unknown_field_and_invalid_revision():
    record = fake_submission_record()
    event = build_order_event_from_submission(
        record,
        event_id="order-event-1",
        occurred_at="2026-09-14T12:00:00Z",
    ).payload
    event["order_event"]["unexpected"] = "nope"

    with pytest.raises(LifecycleOrderEventError, match="unknown fields"):
        validate_order_event(event)
    with pytest.raises(LifecycleOrderEventError, match="lifecycle_revision"):
        build_order_event_from_submission(
            record,
            event_id="order-event-2",
            occurred_at="2026-09-14T12:00:00Z",
            lifecycle_revision=-1,
        )
