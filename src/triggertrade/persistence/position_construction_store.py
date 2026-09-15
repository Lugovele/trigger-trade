"""Durable Position construction results."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text
from triggertrade.position_construction import PositionConstructionError, validate_position_construction_result

from .durable_messages import DurableMessageStore
from .postgres import PostgresPersistenceError


class PositionConstructionConflict(PostgresPersistenceError):
    """Raised when a construction result identity or grant is replayed with different content."""


@dataclass(frozen=True)
class PositionConstructionRecord:
    construction_result_id: str
    capital_grant_id: str
    position_decision_id: str
    decision_cycle_id: str
    set_result_id: str
    symbol: str
    outcome: str
    order_spec_id: str | None
    order_spec_digest: str | None
    payload: dict[str, Any]
    payload_digest: str


class PositionConstructionStore:
    """Persist one immutable post-grant construction outcome per grant."""

    def __init__(self, connection) -> None:
        self._connection = connection
        self._messages = DurableMessageStore(connection)

    def record(
        self,
        *,
        capital_grant: dict[str, Any],
        construction_result: dict[str, Any],
    ) -> tuple[PositionConstructionRecord, bool]:
        try:
            parsed = validate_position_construction_result(
                capital_grant=capital_grant,
                construction_result=construction_result,
            )
        except PositionConstructionError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        payload = parsed.to_payload()
        body = payload["position_construction_result"]
        payload_text = canonical_json_text(payload)
        digest = canonical_json_digest(payload)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_position_construction_results (
                    construction_result_id, capital_grant_id, position_decision_id,
                    decision_cycle_id, set_result_id, symbol, outcome, occurred_at,
                    position_plan_id, tranche_id, order_spec_id, order_spec_digest,
                    payload_json, payload_digest
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s::jsonb, %s
                )
                ON CONFLICT DO NOTHING
                RETURNING
                    construction_result_id, capital_grant_id, position_decision_id,
                    decision_cycle_id, set_result_id, symbol, outcome,
                    order_spec_id, order_spec_digest, payload_json::text, payload_digest
                """,
                (
                    body["construction_result_id"],
                    body["capital_grant_id"],
                    body["position_decision_id"],
                    body["decision_cycle_id"],
                    body["set_result_id"],
                    body["symbol"],
                    body["outcome"],
                    body["occurred_at"],
                    body.get("position_plan_id"),
                    body.get("tranche_id"),
                    body.get("order_spec_id"),
                    body.get("order_spec_digest"),
                    payload_text,
                    digest,
                ),
            )
            row = cursor.fetchone()
        if row is not None:
            record = _record_from_row(row)
            self._publish(record)
            return record, True
        existing = self.get_by_construction_result_id(construction_result_id=body["construction_result_id"])
        if existing is None:
            existing = self.get_by_capital_grant_id(capital_grant_id=body["capital_grant_id"])
        if existing is None and body.get("order_spec_id") is not None:
            existing = self.get_by_order_spec_id(order_spec_id=body["order_spec_id"])
        if existing is None:
            raise PostgresPersistenceError("construction result insert conflicted but no record was found")
        if (
            existing.payload_digest != digest
            or existing.construction_result_id != body["construction_result_id"]
            or existing.capital_grant_id != body["capital_grant_id"]
            or existing.position_decision_id != body["position_decision_id"]
            or existing.decision_cycle_id != body["decision_cycle_id"]
            or existing.set_result_id != body["set_result_id"]
            or existing.symbol != body["symbol"]
            or existing.outcome != body["outcome"]
            or existing.order_spec_id != body.get("order_spec_id")
            or existing.order_spec_digest != body.get("order_spec_digest")
        ):
            raise PositionConstructionConflict(
                "construction result identity, grant, or order spec already exists with different content"
            )
        self._publish(existing)
        return existing, False

    def get_by_construction_result_id(self, *, construction_result_id: str) -> PositionConstructionRecord | None:
        return self._get("construction_result_id", construction_result_id)

    def get_by_capital_grant_id(self, *, capital_grant_id: str) -> PositionConstructionRecord | None:
        return self._get("capital_grant_id", capital_grant_id)

    def get_by_order_spec_id(self, *, order_spec_id: str) -> PositionConstructionRecord | None:
        return self._get("order_spec_id", order_spec_id)

    def _get(self, field: str, value: str) -> PositionConstructionRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_CONSTRUCTION + f" WHERE {field} = %s", (value,))
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def _publish(self, record: PositionConstructionRecord) -> None:
        self._messages.append_outbox(
            message_id=record.construction_result_id,
            producer="Position",
            consumer="Portfolio",
            message_type="APPROVE_REJECT",
            message_version="5",
            payload=record.payload,
            aggregate_id=record.capital_grant_id,
            causation_id=record.position_decision_id,
            correlation_id=record.decision_cycle_id,
            dedupe_key=f"CONSTRUCTION_RESULT:{record.capital_grant_id}",
        )


_SELECT_CONSTRUCTION = """
SELECT
    construction_result_id, capital_grant_id, position_decision_id,
    decision_cycle_id, set_result_id, symbol, outcome,
    order_spec_id, order_spec_digest, payload_json::text, payload_digest
FROM triggertrade_position_construction_results
"""


def _record_from_row(row: tuple[Any, ...]) -> PositionConstructionRecord:
    return PositionConstructionRecord(
        construction_result_id=str(row[0]),
        capital_grant_id=str(row[1]),
        position_decision_id=str(row[2]),
        decision_cycle_id=str(row[3]),
        set_result_id=str(row[4]),
        symbol=str(row[5]),
        outcome=str(row[6]),
        order_spec_id=None if row[7] is None else str(row[7]),
        order_spec_digest=None if row[8] is None else str(row[8]),
        payload=json.loads(str(row[9]), parse_float=Decimal),
        payload_digest=str(row[10]),
    )
