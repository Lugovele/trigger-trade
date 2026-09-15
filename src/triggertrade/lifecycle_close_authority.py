"""Lifecycle close acquire-or-join identifiers and validation helpers."""

from __future__ import annotations

from hashlib import sha256
import re


class LifecycleCloseAuthorityError(ValueError):
    """Raised when close authority input is not representable."""


ACTIVE_CLOSE_INTENT_STATES = frozenset(
    {
        "ACQUIRED",
        "RECONCILING_CHILDREN",
        "REDUCTION_AUTHORIZED",
        "REDUCTION_UNCERTAIN",
        "AWAITING_EXECUTIONS",
        "AWAITING_FINALITY",
    }
)
TERMINAL_CLOSE_INTENT_STATE = "RESOLVED"
CLOSE_INTENT_STATES = ACTIVE_CLOSE_INTENT_STATES | {TERMINAL_CLOSE_INTENT_STATE}

OPEN_CHILD_STATES = frozenset({"AUTHORIZED", "SUBMITTED", "REDUCTION_UNCERTAIN", "AWAITING_EXECUTIONS"})
TERMINAL_CHILD_STATES = frozenset({"TERMINAL", "DISABLED", "RESOLVED"})
CHILD_STATES = OPEN_CHILD_STATES | TERMINAL_CHILD_STATES

_DECIMAL_TEXT_RE = re.compile(r"^(0|[1-9][0-9]*)(\.[0-9]+)?$")


def close_intent_id_for_tranche(tranche_id: str) -> str:
    return f"close-intent-{_digest(_text(tranche_id, field='tranche_id'))}"


def close_child_id_for_intent(close_intent_id: str, child_sequence: int) -> str:
    if not isinstance(child_sequence, int) or isinstance(child_sequence, bool) or child_sequence < 1:
        raise LifecycleCloseAuthorityError("child_sequence must be a positive integer")
    source = f"{_text(close_intent_id, field='close_intent_id')}:{child_sequence}"
    return f"close-child-{_digest(source)}"


def validate_close_state(state: str) -> str:
    value = _text(state, field="state")
    if value not in CLOSE_INTENT_STATES:
        raise LifecycleCloseAuthorityError(f"unsupported close intent state: {value}")
    return value


def validate_child_state(state: str) -> str:
    value = _text(state, field="child_state")
    if value not in CHILD_STATES:
        raise LifecycleCloseAuthorityError(f"unsupported close child state: {value}")
    return value


def validate_decimal_text(value: str, *, field: str) -> str:
    value = _text(value, field=field)
    if _DECIMAL_TEXT_RE.fullmatch(value) is None:
        raise LifecycleCloseAuthorityError(f"{field} must be a nonnegative decimal string")
    return value


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise LifecycleCloseAuthorityError(f"{field} is required")
    return value


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:24]
