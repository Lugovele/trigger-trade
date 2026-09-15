"""Durable immutable Portfolio Capital and Limits grants."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text
from triggertrade.capital_grants import CapitalGrantError, validate_capital_grant_for_decision

from .durable_messages import DurableMessageStore
from .postgres import PostgresPersistenceError


class CapitalGrantConflict(PostgresPersistenceError):
    """Raised when a grant identity or approved decision is replayed with different content."""


@dataclass(frozen=True)
class CapitalGrantRecord:
    capital_grant_id: str
    position_decision_id: str
    decision_cycle_id: str
    set_result_id: str
    symbol: str
    payload: dict[str, Any]
    payload_digest: str


class CapitalGrantStore:
    """Persist immutable grants and publish Capital and Limits to Position."""

    def __init__(self, connection) -> None:
        self._connection = connection
        self._messages = DurableMessageStore(connection)

    def issue(
        self,
        *,
        approved_decision: dict[str, Any],
        capital_grant: dict[str, Any],
    ) -> tuple[CapitalGrantRecord, bool]:
        try:
            parsed = validate_capital_grant_for_decision(
                approved_decision=approved_decision,
                capital_grant=capital_grant,
            )
        except CapitalGrantError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        payload = parsed.to_payload()
        body = payload["capital_and_limits"]
        payload_text = canonical_json_text(payload)
        digest = canonical_json_digest(payload)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_capital_grants (
                    capital_grant_id, position_decision_id, decision_cycle_id, set_result_id, symbol,
                    created_at, as_of, portfolio_state_revision, payload_json, payload_digest
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT DO NOTHING
                RETURNING
                    capital_grant_id, position_decision_id, decision_cycle_id, set_result_id, symbol,
                    payload_json::text, payload_digest
                """,
                (
                    body["capital_grant_id"],
                    body["position_decision_id"],
                    body["decision_cycle_id"],
                    body["set_result_id"],
                    body["symbol"],
                    body["created_at"],
                    body["as_of"],
                    body["portfolio_state_revision"],
                    payload_text,
                    digest,
                ),
            )
            row = cursor.fetchone()
        if row is not None:
            record = _record_from_row(row)
            self._publish(record)
            return record, True
        existing = self.get_by_grant_id(capital_grant_id=body["capital_grant_id"])
        if existing is None:
            existing = self.get_by_position_decision(position_decision_id=body["position_decision_id"])
        if existing is None:
            raise PostgresPersistenceError("capital grant insert conflicted but no record was found")
        if (
            existing.payload_digest != digest
            or existing.capital_grant_id != body["capital_grant_id"]
            or existing.position_decision_id != body["position_decision_id"]
            or existing.decision_cycle_id != body["decision_cycle_id"]
            or existing.set_result_id != body["set_result_id"]
            or existing.symbol != body["symbol"]
        ):
            raise CapitalGrantConflict("capital grant identity or approved decision already exists with different content")
        self._publish(existing)
        return existing, False

    def get_by_grant_id(self, *, capital_grant_id: str) -> CapitalGrantRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                _SELECT_GRANT + " WHERE capital_grant_id = %s",
                (capital_grant_id,),
            )
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def get_by_position_decision(self, *, position_decision_id: str) -> CapitalGrantRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                _SELECT_GRANT + " WHERE position_decision_id = %s",
                (position_decision_id,),
            )
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def _publish(self, record: CapitalGrantRecord) -> None:
        self._messages.append_outbox(
            message_id=record.capital_grant_id,
            producer="Portfolio",
            consumer="Position",
            message_type="CAPITAL_AND_LIMITS",
            message_version="5",
            payload=record.payload,
            aggregate_id=record.position_decision_id,
            dedupe_key=f"CAPITAL_AND_LIMITS:{record.position_decision_id}",
        )


_SELECT_GRANT = """
SELECT
    capital_grant_id, position_decision_id, decision_cycle_id, set_result_id, symbol,
    payload_json::text, payload_digest
FROM triggertrade_capital_grants
"""


def _record_from_row(row: tuple[Any, ...]) -> CapitalGrantRecord:
    return CapitalGrantRecord(
        capital_grant_id=str(row[0]),
        position_decision_id=str(row[1]),
        decision_cycle_id=str(row[2]),
        set_result_id=str(row[3]),
        symbol=str(row[4]),
        payload=json.loads(str(row[5]), parse_float=Decimal),
        payload_digest=str(row[6]),
    )
