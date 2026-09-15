"""Portfolio-owned attempt-scoped cooldown pins."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.lifecycle_order_events import LifecycleOrderEventError, validate_order_event


class PortfolioCooldownError(ValueError):
    """Raised when a Portfolio cooldown pin cannot be represented."""


class CooldownState(StrEnum):
    PENDING_ACCEPTANCE = "PENDING_ACCEPTANCE"
    ACTIVE = "ACTIVE"
    UNRESOLVED_ACCEPTANCE_TIME = "UNRESOLVED_ACCEPTANCE_TIME"
    UNRESOLVED_CONFLICT = "UNRESOLVED_CONFLICT"
    CLEARED = "CLEARED"


@dataclass(frozen=True)
class CooldownPin:
    authorization_id: str
    tranche_id: str
    symbol: str
    portfolio_config_id: str
    portfolio_config_version: str
    portfolio_config_digest: str
    pinned_cooldown_duration_seconds: int
    cooldown_state: CooldownState = CooldownState.PENDING_ACCEPTANCE
    entry_accepted_at: str | None = None
    cooldown_until: str | None = None
    last_order_event_id: str | None = None
    last_lifecycle_revision: int | None = None
    cleared_at: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "authorization_id", _text(self.authorization_id, field="authorization_id"))
        object.__setattr__(self, "tranche_id", _text(self.tranche_id, field="tranche_id"))
        object.__setattr__(self, "symbol", _text(self.symbol, field="symbol").upper())
        object.__setattr__(self, "portfolio_config_id", _text(self.portfolio_config_id, field="portfolio_config_id"))
        object.__setattr__(self, "portfolio_config_version", _text(self.portfolio_config_version, field="portfolio_config_version"))
        object.__setattr__(self, "portfolio_config_digest", _text(self.portfolio_config_digest, field="portfolio_config_digest"))
        if (
            not isinstance(self.pinned_cooldown_duration_seconds, int)
            or isinstance(self.pinned_cooldown_duration_seconds, bool)
            or self.pinned_cooldown_duration_seconds < 0
        ):
            raise PortfolioCooldownError("pinned_cooldown_duration_seconds must be a nonnegative integer")
        object.__setattr__(self, "cooldown_state", CooldownState(self.cooldown_state))
        if self.last_lifecycle_revision is not None and (
            not isinstance(self.last_lifecycle_revision, int)
            or isinstance(self.last_lifecycle_revision, bool)
            or self.last_lifecycle_revision < 0
        ):
            raise PortfolioCooldownError("last_lifecycle_revision must be a nonnegative integer or null")

    def to_payload(self) -> dict[str, Any]:
        return {
            "portfolio_cooldown_pin": {
                "pin_version": 1,
                "authorization_id": self.authorization_id,
                "tranche_id": self.tranche_id,
                "symbol": self.symbol,
                "portfolio_config_id": self.portfolio_config_id,
                "portfolio_config_version": self.portfolio_config_version,
                "portfolio_config_digest": self.portfolio_config_digest,
                "pinned_cooldown_duration_seconds": self.pinned_cooldown_duration_seconds,
                "cooldown_state": self.cooldown_state.value,
                "entry_accepted_at": self.entry_accepted_at,
                "cooldown_until": self.cooldown_until,
                "last_order_event_id": self.last_order_event_id,
                "last_lifecycle_revision": self.last_lifecycle_revision,
                "cleared_at": self.cleared_at,
            }
        }


@dataclass(frozen=True)
class CooldownGate:
    symbol: str
    status: str
    cooldown_until: str | None
    reason_code: str | None


def cooldown_pin_digest(pin: CooldownPin) -> str:
    return canonical_json_digest(pin.to_payload())


def apply_order_event_to_cooldown_pin(pin: CooldownPin, order_event: dict[str, Any]) -> CooldownPin:
    body = _order_event_body(order_event)
    _require_attempt_match(pin, body)
    revision = _revision(body)
    if pin.last_lifecycle_revision is not None and revision < pin.last_lifecycle_revision:
        return pin
    integrity_state = body["entry_acceptance_integrity"]["state"]
    if pin.cooldown_state == CooldownState.UNRESOLVED_CONFLICT and integrity_state != "RESOLVED":
        return _replace_from_event(
            pin,
            body,
            cooldown_state=CooldownState.UNRESOLVED_CONFLICT,
            entry_accepted_at=pin.entry_accepted_at,
            cooldown_until=None,
            cleared_at=None,
        )
    if integrity_state == "CONFLICT" or body["entry_acceptance_status"] == "CONFLICT":
        return _replace_from_event(
            pin,
            body,
            cooldown_state=CooldownState.UNRESOLVED_CONFLICT,
            entry_accepted_at=body.get("entry_accepted_at"),
            cooldown_until=None,
            cleared_at=None,
        )
    if body["lifecycle_state"] == "CANCELLED_ZERO_FILL":
        return _replace_from_event(
            pin,
            body,
            cooldown_state=CooldownState.CLEARED,
            entry_accepted_at=pin.entry_accepted_at,
            cooldown_until=pin.cooldown_until,
            cleared_at=body["occurred_at"],
        )
    if body["entry_acceptance_status"] == "PROVEN":
        accepted_at = _text(body.get("entry_accepted_at"), field="entry_accepted_at")
        return _replace_from_event(
            pin,
            body,
            cooldown_state=CooldownState.ACTIVE,
            entry_accepted_at=accepted_at,
            cooldown_until=_add_seconds(accepted_at, pin.pinned_cooldown_duration_seconds),
            cleared_at=None,
        )
    if body["entry_acceptance_status"] == "UNAVAILABLE" and body["lifecycle_state"] in {
        "PENDING_ENTRY",
        "PARTIALLY_FILLED",
        "OPEN",
        "CANCEL_PENDING",
        "CLOSE_PENDING",
        "RECONCILING",
    }:
        return _replace_from_event(
            pin,
            body,
            cooldown_state=CooldownState.UNRESOLVED_ACCEPTANCE_TIME,
            entry_accepted_at=None,
            cooldown_until=None,
            cleared_at=None,
        )
    return _replace_from_event(
        pin,
        body,
        cooldown_state=pin.cooldown_state,
        entry_accepted_at=pin.entry_accepted_at,
        cooldown_until=pin.cooldown_until,
        cleared_at=pin.cleared_at,
    )


def cooldown_gate_for_pins(symbol: str, pins: tuple[CooldownPin, ...], *, as_of: str) -> CooldownGate:
    symbol = _text(symbol, field="symbol").upper()
    active = [pin for pin in pins if pin.symbol == symbol and pin.cooldown_state == CooldownState.ACTIVE]
    unresolved = [
        pin
        for pin in pins
        if pin.symbol == symbol
        and pin.cooldown_state in {CooldownState.UNRESOLVED_ACCEPTANCE_TIME, CooldownState.UNRESOLVED_CONFLICT}
    ]
    if unresolved:
        reason = "ENTRY_ACCEPTANCE_CONFLICT" if any(pin.cooldown_state == CooldownState.UNRESOLVED_CONFLICT for pin in unresolved) else "ENTRY_ACCEPTANCE_TIME_UNAVAILABLE"
        return CooldownGate(symbol=symbol, status="UNAVAILABLE", cooldown_until=None, reason_code=reason)
    now = _parse_time(as_of)
    surviving_until = [pin.cooldown_until for pin in active if pin.cooldown_until and _parse_time(pin.cooldown_until) > now]
    if surviving_until:
        return CooldownGate(symbol=symbol, status="BLOCKED", cooldown_until=max(surviving_until), reason_code="COOLDOWN_ACTIVE")
    return CooldownGate(symbol=symbol, status="PASS", cooldown_until=None, reason_code=None)


def _order_event_body(order_event: dict[str, Any]) -> dict[str, Any]:
    try:
        event = validate_order_event(order_event)
    except LifecycleOrderEventError as exc:
        raise PortfolioCooldownError(str(exc)) from exc
    if event.definition != "ORDER_EVENT.logical":
        raise PortfolioCooldownError("Portfolio cooldown consumes only ORDER_EVENT.logical")
    return event.body


def _replace_from_event(
    pin: CooldownPin,
    body: dict[str, Any],
    *,
    cooldown_state: CooldownState,
    entry_accepted_at: str | None,
    cooldown_until: str | None,
    cleared_at: str | None,
) -> CooldownPin:
    return CooldownPin(
        authorization_id=pin.authorization_id,
        tranche_id=pin.tranche_id,
        symbol=pin.symbol,
        portfolio_config_id=pin.portfolio_config_id,
        portfolio_config_version=pin.portfolio_config_version,
        portfolio_config_digest=pin.portfolio_config_digest,
        pinned_cooldown_duration_seconds=pin.pinned_cooldown_duration_seconds,
        cooldown_state=cooldown_state,
        entry_accepted_at=entry_accepted_at,
        cooldown_until=cooldown_until,
        last_order_event_id=body["event_id"],
        last_lifecycle_revision=_revision(body),
        cleared_at=cleared_at,
    )


def _require_attempt_match(pin: CooldownPin, body: dict[str, Any]) -> None:
    if body.get("authorization_id") != pin.authorization_id or body.get("tranche_id") != pin.tranche_id:
        raise PortfolioCooldownError("order event does not match cooldown attempt")
    if body.get("symbol") != pin.symbol:
        raise PortfolioCooldownError("order event symbol does not match cooldown pin")


def _revision(body: dict[str, Any]) -> int:
    value = body.get("lifecycle_revision")
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise PortfolioCooldownError("lifecycle_revision must be a nonnegative integer")
    return value


def _add_seconds(timestamp: str, seconds: int) -> str:
    return _format_time(_parse_time(timestamp) + timedelta(seconds=seconds))


def _parse_time(timestamp: str) -> datetime:
    if not isinstance(timestamp, str) or not timestamp:
        raise PortfolioCooldownError("timestamp is required")
    try:
        resolved = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PortfolioCooldownError("timestamp must be an RFC3339 datetime") from exc
    if resolved.tzinfo is None:
        raise PortfolioCooldownError("timestamp must include timezone")
    return resolved.astimezone(UTC)


def _format_time(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PortfolioCooldownError(f"{field} is required")
    return value
