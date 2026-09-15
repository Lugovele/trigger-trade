"""Immutable Order Event v7 ledger persistence."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_text
from triggertrade.lifecycle_order_events import LifecycleOrderEventError, validate_order_event

from .postgres import PostgresPersistenceError


class LifecycleOrderEventConflict(PostgresPersistenceError):
    """Raised when an Order Event identity is replayed with different content."""


@dataclass(frozen=True)
class LifecycleOrderEventRecord:
    event_id: str
    contract_version: int
    event_variant: str
    event_type: str | None
    occurred_at: str | None
    lifecycle_revision: int | None
    tranche_id: str | None
    decision_cycle_id: str | None
    order_spec_id: str | None
    client_order_link_id: str | None
    exchange_order_id: str | None
    lifecycle_state: str | None
    payload: dict[str, Any]
    payload_digest: str


class LifecycleOrderEventStore:
    """Append-only Lifecycle-owned ledger for strict Order Event payloads."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def append(self, payload: dict[str, Any]) -> tuple[LifecycleOrderEventRecord, bool]:
        try:
            event = validate_order_event(payload)
        except LifecycleOrderEventError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        body = event.body
        payload_text = canonical_json_text(event.payload)
        extracted = _extract(body)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_lifecycle_order_events (
                    event_id, contract_version, event_variant, event_type,
                    occurred_at, lifecycle_revision, tranche_id, decision_cycle_id,
                    order_spec_id, client_order_link_id, exchange_order_id,
                    lifecycle_state, payload_json, payload_digest
                ) VALUES (
                    %s, %s, %s, %s,
                    %s::timestamptz, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s::jsonb, %s
                )
                ON CONFLICT DO NOTHING
                RETURNING
                    event_id, contract_version, event_variant, event_type,
                    occurred_at::text, lifecycle_revision, tranche_id, decision_cycle_id,
                    order_spec_id, client_order_link_id, exchange_order_id,
                    lifecycle_state, payload_json::text, payload_digest
                """,
                (
                    body["event_id"],
                    body["contract_version"],
                    body["event_variant"],
                    extracted["event_type"],
                    extracted["occurred_at"],
                    extracted["lifecycle_revision"],
                    extracted["tranche_id"],
                    extracted["decision_cycle_id"],
                    extracted["order_spec_id"],
                    extracted["client_order_link_id"],
                    extracted["exchange_order_id"],
                    extracted["lifecycle_state"],
                    payload_text,
                    event.payload_digest,
                ),
            )
            row = cursor.fetchone()
        if row is not None:
            return _record_from_row(row), True
        existing = self.get_by_event_id(event_id=body["event_id"])
        if existing is None and extracted["tranche_id"] is not None and extracted["lifecycle_revision"] is not None:
            existing = self.get_by_tranche_revision(
                tranche_id=extracted["tranche_id"],
                lifecycle_revision=extracted["lifecycle_revision"],
                event_variant=body["event_variant"],
            )
        if existing is None:
            raise PostgresPersistenceError("order event insert conflicted but no record was found")
        if existing.payload_digest != event.payload_digest or existing.event_id != body["event_id"]:
            raise LifecycleOrderEventConflict("order event identity already exists with different content")
        return existing, False

    def get_by_event_id(self, *, event_id: str) -> LifecycleOrderEventRecord | None:
        return self._get("event_id = %s", (event_id,))

    def get_by_tranche_revision(
        self,
        *,
        tranche_id: str,
        lifecycle_revision: int,
        event_variant: str = "LOGICAL_TRANCHE",
    ) -> LifecycleOrderEventRecord | None:
        return self._get(
            "tranche_id = %s AND lifecycle_revision = %s AND event_variant = %s",
            (tranche_id, lifecycle_revision, event_variant),
        )

    def list_for_tranche(self, *, tranche_id: str) -> tuple[LifecycleOrderEventRecord, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                _SELECT_EVENT
                + """
                WHERE tranche_id = %s
                ORDER BY lifecycle_revision, recorded_at, event_id
                """,
                (tranche_id,),
            )
            rows = cursor.fetchall()
        return tuple(_record_from_row(row) for row in rows)

    def _get(self, predicate: str, values: tuple[Any, ...]) -> LifecycleOrderEventRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_EVENT + f" WHERE {predicate}", values)
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)


def _extract(body: dict[str, Any]) -> dict[str, Any]:
    order_leg = body.get("order_leg") if isinstance(body.get("order_leg"), dict) else {}
    return {
        "event_type": body.get("event_type"),
        "occurred_at": body.get("occurred_at"),
        "lifecycle_revision": body.get("lifecycle_revision"),
        "tranche_id": body.get("tranche_id"),
        "decision_cycle_id": body.get("decision_cycle_id"),
        "order_spec_id": body.get("order_spec_id"),
        "client_order_link_id": order_leg.get("client_order_link_id"),
        "exchange_order_id": order_leg.get("exchange_order_id"),
        "lifecycle_state": body.get("lifecycle_state"),
    }


_SELECT_EVENT = """
SELECT
    event_id, contract_version, event_variant, event_type,
    occurred_at::text, lifecycle_revision, tranche_id, decision_cycle_id,
    order_spec_id, client_order_link_id, exchange_order_id,
    lifecycle_state, payload_json::text, payload_digest
FROM triggertrade_lifecycle_order_events
"""


def _record_from_row(row: tuple[Any, ...]) -> LifecycleOrderEventRecord:
    return LifecycleOrderEventRecord(
        event_id=str(row[0]),
        contract_version=int(row[1]),
        event_variant=str(row[2]),
        event_type=None if row[3] is None else str(row[3]),
        occurred_at=None if row[4] is None else str(row[4]),
        lifecycle_revision=None if row[5] is None else int(row[5]),
        tranche_id=None if row[6] is None else str(row[6]),
        decision_cycle_id=None if row[7] is None else str(row[7]),
        order_spec_id=None if row[8] is None else str(row[8]),
        client_order_link_id=None if row[9] is None else str(row[9]),
        exchange_order_id=None if row[10] is None else str(row[10]),
        lifecycle_state=None if row[11] is None else str(row[11]),
        payload=json.loads(str(row[12]), parse_float=Decimal),
        payload_digest=str(row[13]),
    )
