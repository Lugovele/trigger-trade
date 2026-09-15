"""Durable immutable Position Order Specs."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_text
from triggertrade.order_specs import OrderSpecError, order_spec_digest, validate_order_spec_for_construction

from .durable_messages import DurableMessageStore
from .postgres import PostgresPersistenceError


class OrderSpecConflict(PostgresPersistenceError):
    """Raised when an Order Spec identity or construction result is replayed with different content."""


@dataclass(frozen=True)
class OrderSpecRecord:
    order_spec_id: str
    construction_result_id: str
    capital_grant_id: str
    position_decision_id: str
    decision_cycle_id: str
    set_result_id: str
    position_plan_id: str
    tranche_id: str
    symbol: str
    direction: str
    payload: dict[str, Any]
    payload_digest: str


class OrderSpecStore:
    """Persist immutable Order Specs and publish them to Order Lifecycle."""

    def __init__(self, connection) -> None:
        self._connection = connection
        self._messages = DurableMessageStore(connection)

    def record(
        self,
        *,
        construction_result: dict[str, Any],
        order_spec: dict[str, Any],
    ) -> tuple[OrderSpecRecord, bool]:
        try:
            parsed = validate_order_spec_for_construction(
                construction_result=construction_result,
                order_spec=order_spec,
            )
        except OrderSpecError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        payload = parsed.to_payload()
        body = payload["order_spec"]
        payload_text = canonical_json_text(payload)
        digest = order_spec_digest(parsed)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_order_specs (
                    order_spec_id, construction_result_id, capital_grant_id,
                    position_decision_id, decision_cycle_id, set_result_id,
                    position_plan_id, tranche_id, symbol, direction,
                    spec_created_at, payload_json, payload_digest
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s::jsonb, %s
                )
                ON CONFLICT DO NOTHING
                RETURNING
                    order_spec_id, construction_result_id, capital_grant_id,
                    position_decision_id, decision_cycle_id, set_result_id,
                    position_plan_id, tranche_id, symbol, direction,
                    payload_json::text, payload_digest
                """,
                (
                    body["order_spec_id"],
                    body["construction_result_id"],
                    body["capital_grant_id"],
                    body["position_decision_id"],
                    body["decision_cycle_id"],
                    body["set_result_id"],
                    body["position_plan_id"],
                    body["tranche_id"],
                    body["symbol"],
                    body["direction"],
                    body["spec_created_at"],
                    payload_text,
                    digest,
                ),
            )
            row = cursor.fetchone()
        if row is not None:
            record = _record_from_row(row)
            self._publish(record)
            return record, True
        existing = self.get_by_order_spec_id(order_spec_id=body["order_spec_id"])
        if existing is None:
            existing = self.get_by_construction_result_id(construction_result_id=body["construction_result_id"])
        if existing is None:
            raise PostgresPersistenceError("order spec insert conflicted but no record was found")
        if (
            existing.payload_digest != digest
            or existing.order_spec_id != body["order_spec_id"]
            or existing.construction_result_id != body["construction_result_id"]
            or existing.capital_grant_id != body["capital_grant_id"]
            or existing.position_decision_id != body["position_decision_id"]
            or existing.decision_cycle_id != body["decision_cycle_id"]
            or existing.set_result_id != body["set_result_id"]
            or existing.position_plan_id != body["position_plan_id"]
            or existing.tranche_id != body["tranche_id"]
            or existing.symbol != body["symbol"]
            or existing.direction != body["direction"]
        ):
            raise OrderSpecConflict("order spec identity or construction result already exists with different content")
        self._publish(existing)
        return existing, False

    def get_by_order_spec_id(self, *, order_spec_id: str) -> OrderSpecRecord | None:
        return self._get("order_spec_id", order_spec_id)

    def get_by_construction_result_id(self, *, construction_result_id: str) -> OrderSpecRecord | None:
        return self._get("construction_result_id", construction_result_id)

    def _get(self, field: str, value: str) -> OrderSpecRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_SPEC + f" WHERE {field} = %s", (value,))
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def _publish(self, record: OrderSpecRecord) -> None:
        self._messages.append_outbox(
            message_id=record.order_spec_id,
            producer="Position",
            consumer="Lifecycle",
            message_type="ORDER_SPEC",
            message_version="5",
            payload=record.payload,
            aggregate_id=record.tranche_id,
            causation_id=record.construction_result_id,
            correlation_id=record.decision_cycle_id,
            dedupe_key=f"ORDER_SPEC:{record.construction_result_id}",
        )


_SELECT_SPEC = """
SELECT
    order_spec_id, construction_result_id, capital_grant_id,
    position_decision_id, decision_cycle_id, set_result_id,
    position_plan_id, tranche_id, symbol, direction,
    payload_json::text, payload_digest
FROM triggertrade_order_specs
"""


def _record_from_row(row: tuple[Any, ...]) -> OrderSpecRecord:
    return OrderSpecRecord(
        order_spec_id=str(row[0]),
        construction_result_id=str(row[1]),
        capital_grant_id=str(row[2]),
        position_decision_id=str(row[3]),
        decision_cycle_id=str(row[4]),
        set_result_id=str(row[5]),
        position_plan_id=str(row[6]),
        tranche_id=str(row[7]),
        symbol=str(row[8]),
        direction=str(row[9]),
        payload=json.loads(str(row[10]), parse_float=Decimal),
        payload_digest=str(row[11]),
    )
