from __future__ import annotations

import pytest

from triggertrade.lifecycle_close_authority import (
    LifecycleCloseAuthorityError,
    close_child_id_for_intent,
    close_intent_id_for_tranche,
    validate_child_state,
    validate_close_state,
    validate_decimal_text,
)


def test_close_authority_ids_are_deterministic():
    intent_id = close_intent_id_for_tranche("tranche-1")

    assert intent_id == "close-intent-04663296ee09ab6f5b6012af"
    assert close_intent_id_for_tranche("tranche-1") == intent_id
    assert close_child_id_for_intent(intent_id, 1) == "close-child-e46d3efb49e0edcc866cb44c"
    assert close_child_id_for_intent(intent_id, 2) != close_child_id_for_intent(intent_id, 1)


def test_close_authority_validates_states_and_decimal_text():
    assert validate_close_state("ACQUIRED") == "ACQUIRED"
    assert validate_close_state("RESOLVED") == "RESOLVED"
    assert validate_child_state("AUTHORIZED") == "AUTHORIZED"
    assert validate_decimal_text("0.125", field="qty") == "0.125"

    with pytest.raises(LifecycleCloseAuthorityError, match="unsupported close intent state"):
        validate_close_state("CLOSED")
    with pytest.raises(LifecycleCloseAuthorityError, match="unsupported close child state"):
        validate_child_state("PENDING")
    with pytest.raises(LifecycleCloseAuthorityError, match="nonnegative decimal"):
        validate_decimal_text("-1", field="qty")
    with pytest.raises(LifecycleCloseAuthorityError, match="positive integer"):
        close_child_id_for_intent("close-intent-1", 0)
