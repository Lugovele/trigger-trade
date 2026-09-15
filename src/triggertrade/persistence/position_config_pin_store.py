"""PostgreSQL persistence for Position configuration pins."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_text
from triggertrade.position_config_pins import (
    PositionConfigPin,
    PositionConfigPinError,
    build_position_config_pin,
    position_config_pin_digest,
)
from triggertrade.rules.trading import TradingRulesVersion

from .postgres import PostgresPersistenceError


class PositionConfigPinConflict(PostgresPersistenceError):
    """Raised when a Position decision/cycle pin is replayed with different content."""


@dataclass(frozen=True)
class PositionConfigPinRecord:
    pin: PositionConfigPin
    payload_digest: str


class PositionConfigPinStore:
    """Persist immutable Position configuration bindings by decision/cycle."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def pin(
        self,
        *,
        position_decision_id: str,
        market_handoff: dict[str, Any],
        rules_version: TradingRulesVersion,
        pinned_at: str,
    ) -> tuple[PositionConfigPinRecord, bool]:
        try:
            pin = build_position_config_pin(
                position_decision_id=position_decision_id,
                market_handoff=market_handoff,
                rules_version=rules_version,
                pinned_at=pinned_at,
            )
        except PositionConfigPinError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        return self._insert(pin)

    def get_by_position_decision_id(self, *, position_decision_id: str) -> PositionConfigPinRecord | None:
        return self._get("position_decision_id", position_decision_id)

    def get_by_decision_cycle_id(self, *, decision_cycle_id: str) -> PositionConfigPinRecord | None:
        return self._get("decision_cycle_id", decision_cycle_id)

    def _insert(self, pin: PositionConfigPin) -> tuple[PositionConfigPinRecord, bool]:
        payload = pin.to_payload()
        payload_text = canonical_json_text(payload)
        digest = position_config_pin_digest(pin)
        body = payload["position_config_pin"]
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_position_config_pins (
                    position_decision_id, decision_cycle_id, set_result_id, symbol,
                    market_handoff_digest, configuration_id, configuration_version,
                    configuration_content_digest, pinned_at, payload_json, payload_digest
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s::timestamptz, %s::jsonb, %s
                )
                ON CONFLICT DO NOTHING
                RETURNING
                    position_decision_id, decision_cycle_id, set_result_id, symbol,
                    market_handoff_digest, configuration_id, configuration_version,
                    configuration_content_digest, pinned_at::text, payload_json::text,
                    payload_digest
                """,
                (
                    body["position_decision_id"],
                    body["decision_cycle_id"],
                    body["set_result_id"],
                    body["symbol"],
                    body["market_handoff_digest"],
                    body["configuration_id"],
                    body["configuration_version"],
                    body["configuration_content_digest"],
                    body["pinned_at"],
                    payload_text,
                    digest,
                ),
            )
            row = cursor.fetchone()
        if row is not None:
            return _record_from_row(row), True
        existing = self.get_by_position_decision_id(position_decision_id=pin.position_decision_id)
        if existing is None:
            existing = self.get_by_decision_cycle_id(decision_cycle_id=pin.decision_cycle_id)
        if existing is None:
            raise PostgresPersistenceError("position config pin insert conflicted but no record was found")
        if existing.payload_digest != digest:
            raise PositionConfigPinConflict("position decision or cycle already has a different configuration pin")
        return existing, False

    def _get(self, field: str, value: str) -> PositionConfigPinRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_PIN + f" WHERE {field} = %s", (value,))
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)


_SELECT_PIN = """
SELECT
    position_decision_id, decision_cycle_id, set_result_id, symbol,
    market_handoff_digest, configuration_id, configuration_version,
    configuration_content_digest, pinned_at::text, payload_json::text,
    payload_digest
FROM triggertrade_position_config_pins
"""


def _record_from_row(row: tuple[Any, ...]) -> PositionConfigPinRecord:
    payload = json.loads(str(row[9]), parse_float=Decimal)
    body = payload["position_config_pin"]
    pin = PositionConfigPin(
        position_decision_id=str(row[0]),
        decision_cycle_id=str(row[1]),
        set_result_id=str(row[2]),
        symbol=str(row[3]),
        market_handoff_digest=str(row[4]),
        configuration_id=str(row[5]),
        configuration_version=str(row[6]),
        configuration_content_digest=str(row[7]),
        pinned_at=str(body["pinned_at"]),
    )
    return PositionConfigPinRecord(pin=pin, payload_digest=str(row[10]))
