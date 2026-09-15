from __future__ import annotations

import pytest

from triggertrade.portfolio_cooldown import (
    CooldownState,
    PortfolioCooldownError,
    apply_order_event_to_cooldown_pin,
    cooldown_gate_for_pins,
    cooldown_pin_digest,
)
from tests.unit.test_portfolio_cooldown_store import cooldown_pin, order_event


def test_cooldown_pin_uses_pinned_duration_from_original_authorization_attempt():
    pin = cooldown_pin(duration_seconds=3600)

    active = apply_order_event_to_cooldown_pin(
        pin,
        order_event(
            entry_acceptance_status="PROVEN",
            entry_accepted_at="2026-09-15T10:00:00Z",
            revision=2,
        ),
    )

    assert active.cooldown_state == CooldownState.ACTIVE
    assert active.cooldown_until == "2026-09-15T11:00:00Z"
    assert cooldown_gate_for_pins("btcusdt", (active,), as_of="2026-09-15T10:30:00Z").status == "BLOCKED"
    assert cooldown_gate_for_pins("BTCUSDT", (active,), as_of="2026-09-15T11:00:01Z").status == "PASS"
    assert cooldown_pin_digest(active) == "2b3e3256feab3c18115e01e6d3d65efcc937b94b134eb04d9bd2a393949a6cdf"


def test_cooldown_unknown_or_conflicted_acceptance_blocks_without_deadline_guess():
    pin = cooldown_pin()
    unknown = apply_order_event_to_cooldown_pin(
        pin,
        order_event(entry_acceptance_status="UNAVAILABLE", entry_accepted_at=None, lifecycle_state="PENDING_ENTRY"),
    )
    conflicted = apply_order_event_to_cooldown_pin(
        unknown,
        order_event(
            entry_acceptance_status="CONFLICT",
            entry_accepted_at=None,
            integrity_state="CONFLICT",
            revision=2,
        ),
    )

    assert unknown.cooldown_state == CooldownState.UNRESOLVED_ACCEPTANCE_TIME
    assert unknown.cooldown_until is None
    assert cooldown_gate_for_pins("BTCUSDT", (unknown,), as_of="2026-09-15T12:00:00Z").status == "UNAVAILABLE"
    gate = cooldown_gate_for_pins("BTCUSDT", (conflicted,), as_of="2026-09-15T12:00:00Z")
    assert gate.status == "UNAVAILABLE"
    assert gate.reason_code == "ENTRY_ACCEPTANCE_CONFLICT"


def test_cooldown_conflict_cannot_be_erased_by_proven_timestamp_or_zero_fill():
    conflicted = apply_order_event_to_cooldown_pin(
        cooldown_pin(),
        order_event(
            entry_acceptance_status="CONFLICT",
            entry_accepted_at=None,
            integrity_state="CONFLICT",
            revision=2,
        ),
    )

    later_proven = apply_order_event_to_cooldown_pin(
        conflicted,
        order_event(
            entry_acceptance_status="PROVEN",
            entry_accepted_at="2026-09-15T10:00:00Z",
            revision=3,
        ),
    )
    later_cancelled = apply_order_event_to_cooldown_pin(
        later_proven,
        order_event(lifecycle_state="CANCELLED_ZERO_FILL", revision=4),
    )

    assert later_proven.cooldown_state == CooldownState.UNRESOLVED_CONFLICT
    assert later_proven.cooldown_until is None
    assert later_cancelled.cooldown_state == CooldownState.UNRESOLVED_CONFLICT
    assert later_cancelled.cleared_at is None
    gate = cooldown_gate_for_pins("BTCUSDT", (later_cancelled,), as_of="2026-09-15T12:00:00Z")
    assert gate.status == "UNAVAILABLE"
    assert gate.reason_code == "ENTRY_ACCEPTANCE_CONFLICT"


def test_cooldown_zero_fill_clears_only_that_attempt_and_stale_replay_cannot_restore():
    first = apply_order_event_to_cooldown_pin(
        cooldown_pin(tranche_id="tranche-1"),
        order_event(
            tranche_id="tranche-1",
            entry_acceptance_status="PROVEN",
            entry_accepted_at="2026-09-15T10:00:00Z",
            revision=2,
        ),
    )
    second = apply_order_event_to_cooldown_pin(
        cooldown_pin(authorization_id="authorization-2", tranche_id="tranche-2"),
        order_event(
            authorization_id="authorization-2",
            tranche_id="tranche-2",
            entry_acceptance_status="PROVEN",
            entry_accepted_at="2026-09-15T10:30:00Z",
            revision=2,
        ),
    )
    cleared = apply_order_event_to_cooldown_pin(
        first,
        order_event(tranche_id="tranche-1", lifecycle_state="CANCELLED_ZERO_FILL", revision=3),
    )
    stale = apply_order_event_to_cooldown_pin(
        cleared,
        order_event(
            tranche_id="tranche-1",
            entry_acceptance_status="PROVEN",
            entry_accepted_at="2026-09-15T10:00:00Z",
            revision=2,
        ),
    )

    assert stale == cleared
    assert cleared.cooldown_state == CooldownState.CLEARED
    gate = cooldown_gate_for_pins("BTCUSDT", (cleared, second), as_of="2026-09-15T10:45:00Z")
    assert gate.status == "BLOCKED"
    assert gate.cooldown_until == second.cooldown_until


def test_cooldown_rejects_mismatched_attempt_and_invalid_duration():
    with pytest.raises(PortfolioCooldownError, match="duration"):
        cooldown_pin(duration_seconds=-1)
    with pytest.raises(PortfolioCooldownError, match="does not match"):
        apply_order_event_to_cooldown_pin(cooldown_pin(), order_event(authorization_id="other"))
