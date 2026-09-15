"""Durable Portfolio submission holds and Submit Authorized publication."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text
from triggertrade.submit_authorizations import SubmitAuthorizationError, validate_submit_authorized

from .durable_messages import DurableMessageStore
from .postgres import PostgresPersistenceError


class SubmitAuthorizationConflict(PostgresPersistenceError):
    """Raised when an authorization identity is replayed with different content."""


@dataclass(frozen=True)
class SubmitAuthorizationRecord:
    authorization_id: str
    capital_grant_id: str
    construction_result_id: str
    order_spec_id: str
    order_spec_digest: str
    tranche_id: str
    symbol: str
    held_committed_capital: str
    payload: dict[str, Any]
    payload_digest: str


class SubmitAuthorizationStore:
    """Persist submission holds and publish Submit Authorized to Lifecycle."""

    def __init__(self, connection) -> None:
        self._connection = connection
        self._messages = DurableMessageStore(connection)

    def authorize(
        self,
        *,
        capital_grant: dict[str, Any],
        construction_result: dict[str, Any],
        submit_authorized: dict[str, Any],
    ) -> tuple[SubmitAuthorizationRecord, bool]:
        try:
            parsed = validate_submit_authorized(
                capital_grant=capital_grant,
                construction_result=construction_result,
                submit_authorized=submit_authorized,
            )
        except SubmitAuthorizationError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        payload = parsed.to_payload()
        body = payload["submit_authorized"]
        payload_text = canonical_json_text(payload)
        digest = canonical_json_digest(payload)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_submit_authorizations (
                    authorization_id, capital_grant_id, position_decision_id, construction_result_id,
                    decision_cycle_id, set_result_id, position_plan_id, tranche_id, order_spec_id,
                    symbol, order_spec_digest, held_committed_capital, authorized_at,
                    payload_json, payload_digest
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s::jsonb, %s
                )
                ON CONFLICT DO NOTHING
                RETURNING
                    authorization_id, capital_grant_id, construction_result_id, order_spec_id,
                    order_spec_digest, tranche_id, symbol, held_committed_capital::text,
                    payload_json::text, payload_digest
                """,
                (
                    body["authorization_id"],
                    body["capital_grant_id"],
                    body["position_decision_id"],
                    body["construction_result_id"],
                    body["decision_cycle_id"],
                    body["set_result_id"],
                    body["position_plan_id"],
                    body["tranche_id"],
                    body["order_spec_id"],
                    body["symbol"],
                    body["order_spec_digest"],
                    body["held_committed_capital"],
                    body["authorized_at"],
                    payload_text,
                    digest,
                ),
            )
            row = cursor.fetchone()
        if row is not None:
            record = _record_from_row(row)
            self._publish(record)
            return record, True
        existing = self.get_by_authorization_id(authorization_id=body["authorization_id"])
        if existing is None:
            existing = self.get_by_capital_grant_id(capital_grant_id=body["capital_grant_id"])
        if existing is None:
            existing = self.get_by_construction_result_id(construction_result_id=body["construction_result_id"])
        if existing is None:
            existing = self.get_by_order_spec_id(order_spec_id=body["order_spec_id"])
        if existing is None:
            raise PostgresPersistenceError("submit authorization insert conflicted but no record was found")
        if (
            existing.payload_digest != digest
            or existing.authorization_id != body["authorization_id"]
            or existing.capital_grant_id != body["capital_grant_id"]
            or existing.construction_result_id != body["construction_result_id"]
            or existing.order_spec_id != body["order_spec_id"]
            or existing.order_spec_digest != body["order_spec_digest"]
            or existing.tranche_id != body["tranche_id"]
            or existing.symbol != body["symbol"]
            or existing.held_committed_capital != body["held_committed_capital"]
        ):
            raise SubmitAuthorizationConflict(
                "submit authorization identity, construction result, or order spec already exists with different content"
            )
        self._publish(existing)
        return existing, False

    def get_by_authorization_id(self, *, authorization_id: str) -> SubmitAuthorizationRecord | None:
        return self._get("authorization_id", authorization_id)

    def get_by_capital_grant_id(self, *, capital_grant_id: str) -> SubmitAuthorizationRecord | None:
        return self._get("capital_grant_id", capital_grant_id)

    def get_by_construction_result_id(self, *, construction_result_id: str) -> SubmitAuthorizationRecord | None:
        return self._get("construction_result_id", construction_result_id)

    def get_by_order_spec_id(self, *, order_spec_id: str) -> SubmitAuthorizationRecord | None:
        return self._get("order_spec_id", order_spec_id)

    def _get(self, field: str, value: str) -> SubmitAuthorizationRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_AUTHORIZATION + f" WHERE {field} = %s", (value,))
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def _publish(self, record: SubmitAuthorizationRecord) -> None:
        self._messages.append_outbox(
            message_id=record.authorization_id,
            producer="Portfolio",
            consumer="Lifecycle",
            message_type="SUBMIT_AUTHORIZED",
            message_version="5",
            payload=record.payload,
            aggregate_id=record.tranche_id,
            causation_id=record.construction_result_id,
            correlation_id=record.order_spec_id,
            dedupe_key=f"SUBMIT_AUTHORIZED:{record.construction_result_id}",
        )


_SELECT_AUTHORIZATION = """
SELECT
    authorization_id, capital_grant_id, construction_result_id, order_spec_id,
    order_spec_digest, tranche_id, symbol, held_committed_capital::text,
    payload_json::text, payload_digest
FROM triggertrade_submit_authorizations
"""


def _record_from_row(row: tuple[Any, ...]) -> SubmitAuthorizationRecord:
    return SubmitAuthorizationRecord(
        authorization_id=str(row[0]),
        capital_grant_id=str(row[1]),
        construction_result_id=str(row[2]),
        order_spec_id=str(row[3]),
        order_spec_digest=str(row[4]),
        tranche_id=str(row[5]),
        symbol=str(row[6]),
        held_committed_capital=_decimal_text(str(row[7])),
        payload=json.loads(str(row[8]), parse_float=Decimal),
        payload_digest=str(row[9]),
    )


def _decimal_text(value: str) -> str:
    resolved = Decimal(value)
    return format(resolved.normalize(), "f") if resolved != 0 else "0"
