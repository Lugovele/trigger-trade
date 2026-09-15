"""PostgreSQL persistence for Portfolio attempt-scoped cooldown pins."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_text
from triggertrade.portfolio_cooldown import (
    CooldownGate,
    CooldownPin,
    PortfolioCooldownError,
    apply_order_event_to_cooldown_pin,
    cooldown_gate_for_pins,
    cooldown_pin_digest,
)

from .postgres import PostgresPersistenceError


class PortfolioCooldownConflict(PostgresPersistenceError):
    """Raised when a cooldown pin identity is replayed with different content."""


@dataclass(frozen=True)
class PortfolioCooldownRecord:
    pin: CooldownPin
    pin_payload_digest: str


class PortfolioCooldownStore:
    """Persist Portfolio-owned cooldown pins by authorization/tranche attempt."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def create_pin(
        self,
        *,
        authorization_id: str,
        tranche_id: str,
        symbol: str,
        portfolio_config_id: str,
        portfolio_config_version: str,
        portfolio_config_digest: str,
        pinned_cooldown_duration_seconds: int,
    ) -> tuple[PortfolioCooldownRecord, bool]:
        try:
            pin = CooldownPin(
                authorization_id=authorization_id,
                tranche_id=tranche_id,
                symbol=symbol,
                portfolio_config_id=portfolio_config_id,
                portfolio_config_version=portfolio_config_version,
                portfolio_config_digest=portfolio_config_digest,
                pinned_cooldown_duration_seconds=pinned_cooldown_duration_seconds,
            )
        except PortfolioCooldownError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        return self._upsert_new_pin(pin)

    def apply_order_event(self, order_event: dict[str, Any]) -> PortfolioCooldownRecord:
        body = _event_body(order_event)
        existing = self.get(authorization_id=body["authorization_id"], tranche_id=body["tranche_id"])
        if existing is None:
            raise PostgresPersistenceError("cooldown pin does not exist for order event attempt")
        try:
            updated = apply_order_event_to_cooldown_pin(existing.pin, order_event)
        except PortfolioCooldownError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        if updated == existing.pin:
            return existing
        return self._update_pin(updated)

    def get(self, *, authorization_id: str, tranche_id: str) -> PortfolioCooldownRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_PIN + " WHERE authorization_id = %s AND tranche_id = %s", (authorization_id, tranche_id))
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def list_for_symbol(self, *, symbol: str) -> tuple[PortfolioCooldownRecord, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_PIN + " WHERE symbol = %s ORDER BY updated_at, authorization_id, tranche_id", (symbol.upper(),))
            rows = cursor.fetchall()
        return tuple(_record_from_row(row) for row in rows)

    def gate_for_symbol(self, *, symbol: str, as_of: str) -> CooldownGate:
        pins = tuple(record.pin for record in self.list_for_symbol(symbol=symbol))
        try:
            return cooldown_gate_for_pins(symbol, pins, as_of=as_of)
        except PortfolioCooldownError as exc:
            raise PostgresPersistenceError(str(exc)) from exc

    def _upsert_new_pin(self, pin: CooldownPin) -> tuple[PortfolioCooldownRecord, bool]:
        payload_text = canonical_json_text(pin.to_payload())
        digest = cooldown_pin_digest(pin)
        body = pin.to_payload()["portfolio_cooldown_pin"]
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_portfolio_cooldown_pins (
                    authorization_id, tranche_id, symbol, portfolio_config_id,
                    portfolio_config_version, portfolio_config_digest,
                    pinned_cooldown_duration_seconds, cooldown_state,
                    entry_accepted_at, cooldown_until, last_order_event_id,
                    last_lifecycle_revision, cleared_at, pin_payload_json, pin_payload_digest
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s::timestamptz, %s::timestamptz, %s,
                    %s, %s::timestamptz, %s::jsonb, %s
                )
                ON CONFLICT DO NOTHING
                RETURNING
                    authorization_id, tranche_id, symbol, portfolio_config_id,
                    portfolio_config_version, portfolio_config_digest,
                    pinned_cooldown_duration_seconds, cooldown_state,
                    entry_accepted_at::text, cooldown_until::text, last_order_event_id,
                    last_lifecycle_revision, cleared_at::text, pin_payload_json::text,
                    pin_payload_digest
                """,
                _pin_values(body, payload_text, digest),
            )
            row = cursor.fetchone()
        if row is not None:
            return _record_from_row(row), True
        existing = self.get(authorization_id=pin.authorization_id, tranche_id=pin.tranche_id)
        if existing is None:
            raise PostgresPersistenceError("cooldown pin insert conflicted but no record was found")
        if existing.pin_payload_digest != digest:
            raise PortfolioCooldownConflict("cooldown pin attempt already exists with different content")
        return existing, False

    def _update_pin(self, pin: CooldownPin) -> PortfolioCooldownRecord:
        payload_text = canonical_json_text(pin.to_payload())
        digest = cooldown_pin_digest(pin)
        body = pin.to_payload()["portfolio_cooldown_pin"]
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE triggertrade_portfolio_cooldown_pins
                SET cooldown_state = %s,
                    entry_accepted_at = %s::timestamptz,
                    cooldown_until = %s::timestamptz,
                    last_order_event_id = %s,
                    last_lifecycle_revision = %s,
                    cleared_at = %s::timestamptz,
                    pin_payload_json = %s::jsonb,
                    pin_payload_digest = %s,
                    updated_at = now()
                WHERE authorization_id = %s
                  AND tranche_id = %s
                  AND (
                    last_lifecycle_revision IS NULL
                    OR last_lifecycle_revision <= %s
                  )
                RETURNING
                    authorization_id, tranche_id, symbol, portfolio_config_id,
                    portfolio_config_version, portfolio_config_digest,
                    pinned_cooldown_duration_seconds, cooldown_state,
                    entry_accepted_at::text, cooldown_until::text, last_order_event_id,
                    last_lifecycle_revision, cleared_at::text, pin_payload_json::text,
                    pin_payload_digest
                """,
                (
                    body["cooldown_state"],
                    body["entry_accepted_at"],
                    body["cooldown_until"],
                    body["last_order_event_id"],
                    body["last_lifecycle_revision"],
                    body["cleared_at"],
                    payload_text,
                    digest,
                    body["authorization_id"],
                    body["tranche_id"],
                    body["last_lifecycle_revision"],
                ),
            )
            row = cursor.fetchone()
        if row is None:
            existing = self.get(authorization_id=pin.authorization_id, tranche_id=pin.tranche_id)
            if existing is None:
                raise PostgresPersistenceError("cooldown pin does not exist")
            return existing
        return _record_from_row(row)


def _event_body(order_event: dict[str, Any]) -> dict[str, Any]:
    try:
        from triggertrade.lifecycle_order_events import LifecycleOrderEventError, validate_order_event

        body = validate_order_event(order_event).body
    except LifecycleOrderEventError as exc:
        raise PostgresPersistenceError(str(exc)) from exc
    if body.get("authorization_id") is None:
        raise PostgresPersistenceError("cooldown order event requires authorization_id")
    return body


def _pin_values(body: dict[str, Any], payload_text: str, digest: str) -> tuple[Any, ...]:
    return (
        body["authorization_id"],
        body["tranche_id"],
        body["symbol"],
        body["portfolio_config_id"],
        body["portfolio_config_version"],
        body["portfolio_config_digest"],
        body["pinned_cooldown_duration_seconds"],
        body["cooldown_state"],
        body["entry_accepted_at"],
        body["cooldown_until"],
        body["last_order_event_id"],
        body["last_lifecycle_revision"],
        body["cleared_at"],
        payload_text,
        digest,
    )


_SELECT_PIN = """
SELECT
    authorization_id, tranche_id, symbol, portfolio_config_id,
    portfolio_config_version, portfolio_config_digest,
    pinned_cooldown_duration_seconds, cooldown_state,
    entry_accepted_at::text, cooldown_until::text, last_order_event_id,
    last_lifecycle_revision, cleared_at::text, pin_payload_json::text,
    pin_payload_digest
FROM triggertrade_portfolio_cooldown_pins
"""


def _record_from_row(row: tuple[Any, ...]) -> PortfolioCooldownRecord:
    payload = json.loads(str(row[13]), parse_float=Decimal)
    body = payload["portfolio_cooldown_pin"]
    pin = CooldownPin(
        authorization_id=str(row[0]),
        tranche_id=str(row[1]),
        symbol=str(row[2]),
        portfolio_config_id=str(row[3]),
        portfolio_config_version=str(row[4]),
        portfolio_config_digest=str(row[5]),
        pinned_cooldown_duration_seconds=int(row[6]),
        cooldown_state=str(row[7]),
        entry_accepted_at=None if row[8] is None else str(body["entry_accepted_at"]),
        cooldown_until=None if row[9] is None else str(body["cooldown_until"]),
        last_order_event_id=None if row[10] is None else str(row[10]),
        last_lifecycle_revision=None if row[11] is None else int(row[11]),
        cleared_at=None if row[12] is None else str(body["cleared_at"]),
    )
    return PortfolioCooldownRecord(pin=pin, pin_payload_digest=str(row[14]))
