"""Durable Order Lifecycle start-gate records."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_text
from triggertrade.lifecycle_start_gate import (
    LifecycleStartGateError,
    lifecycle_start_gate_digest,
    match_lifecycle_start_gate,
)

from .postgres import PostgresPersistenceError


class LifecycleStartGateConflict(PostgresPersistenceError):
    """Raised when a start-gate identity is replayed with different content."""


@dataclass(frozen=True)
class LifecycleStartGateRecord:
    start_gate_id: str
    order_spec_id: str
    authorization_id: str
    capital_grant_id: str
    decision_cycle_id: str
    set_result_id: str
    position_decision_id: str
    construction_result_id: str
    position_plan_id: str
    tranche_id: str
    symbol: str
    direction: str
    lifecycle_state: str
    order_spec_digest: str
    submit_authorized_digest: str
    held_committed_capital: str
    payload: dict[str, Any]
    payload_digest: str


class LifecycleStartGateStore:
    """Persist the atomic pre-submit gate after spec and authorization match."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def accept(
        self,
        *,
        start_gate_id: str,
        order_spec: dict[str, Any],
        submit_authorized: dict[str, Any],
    ) -> tuple[LifecycleStartGateRecord, bool]:
        if not isinstance(start_gate_id, str) or not start_gate_id or "\x00" in start_gate_id:
            raise PostgresPersistenceError("start_gate_id is required")
        try:
            match = match_lifecycle_start_gate(order_spec=order_spec, submit_authorized=submit_authorized)
        except LifecycleStartGateError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        payload = match.to_payload()
        payload_text = canonical_json_text(payload)
        digest = lifecycle_start_gate_digest(match)
        body = payload["lifecycle_start_gate"]
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_lifecycle_start_gates (
                    start_gate_id, order_spec_id, authorization_id, capital_grant_id,
                    decision_cycle_id, set_result_id, position_decision_id,
                    construction_result_id, position_plan_id, tranche_id, symbol,
                    direction, lifecycle_state, order_spec_digest,
                    submit_authorized_digest, held_committed_capital,
                    payload_json, payload_digest
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s::jsonb, %s
                )
                ON CONFLICT DO NOTHING
                RETURNING
                    start_gate_id, order_spec_id, authorization_id, capital_grant_id,
                    decision_cycle_id, set_result_id, position_decision_id,
                    construction_result_id, position_plan_id, tranche_id, symbol,
                    direction, lifecycle_state, order_spec_digest,
                    submit_authorized_digest, held_committed_capital::text,
                    payload_json::text, payload_digest
                """,
                (
                    start_gate_id,
                    body["order_spec_id"],
                    body["authorization_id"],
                    body["capital_grant_id"],
                    body["decision_cycle_id"],
                    body["set_result_id"],
                    body["position_decision_id"],
                    body["construction_result_id"],
                    body["position_plan_id"],
                    body["tranche_id"],
                    body["symbol"],
                    body["direction"],
                    body["lifecycle_state"],
                    body["order_spec_digest"],
                    body["submit_authorized_digest"],
                    body["held_committed_capital"],
                    payload_text,
                    digest,
                ),
            )
            row = cursor.fetchone()
        if row is not None:
            return _record_from_row(row), True
        existing = self.get_by_start_gate_id(start_gate_id=start_gate_id)
        if existing is None:
            existing = self.get_by_order_spec_id(order_spec_id=body["order_spec_id"])
        if existing is None:
            existing = self.get_by_authorization_id(authorization_id=body["authorization_id"])
        if existing is None:
            raise PostgresPersistenceError("lifecycle start gate insert conflicted but no record was found")
        if (
            existing.payload_digest != digest
            or existing.start_gate_id != start_gate_id
            or existing.order_spec_id != body["order_spec_id"]
            or existing.authorization_id != body["authorization_id"]
            or existing.order_spec_digest != body["order_spec_digest"]
            or existing.submit_authorized_digest != body["submit_authorized_digest"]
            or existing.held_committed_capital != body["held_committed_capital"]
        ):
            raise LifecycleStartGateConflict("lifecycle start gate already exists with different content")
        return existing, False

    def get_by_start_gate_id(self, *, start_gate_id: str) -> LifecycleStartGateRecord | None:
        return self._get("start_gate_id", start_gate_id)

    def get_by_order_spec_id(self, *, order_spec_id: str) -> LifecycleStartGateRecord | None:
        return self._get("order_spec_id", order_spec_id)

    def get_by_authorization_id(self, *, authorization_id: str) -> LifecycleStartGateRecord | None:
        return self._get("authorization_id", authorization_id)

    def _get(self, field: str, value: str) -> LifecycleStartGateRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_START_GATE + f" WHERE {field} = %s", (value,))
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)


_SELECT_START_GATE = """
SELECT
    start_gate_id, order_spec_id, authorization_id, capital_grant_id,
    decision_cycle_id, set_result_id, position_decision_id,
    construction_result_id, position_plan_id, tranche_id, symbol,
    direction, lifecycle_state, order_spec_digest,
    submit_authorized_digest, held_committed_capital::text,
    payload_json::text, payload_digest
FROM triggertrade_lifecycle_start_gates
"""


def _record_from_row(row: tuple[Any, ...]) -> LifecycleStartGateRecord:
    return LifecycleStartGateRecord(
        start_gate_id=str(row[0]),
        order_spec_id=str(row[1]),
        authorization_id=str(row[2]),
        capital_grant_id=str(row[3]),
        decision_cycle_id=str(row[4]),
        set_result_id=str(row[5]),
        position_decision_id=str(row[6]),
        construction_result_id=str(row[7]),
        position_plan_id=str(row[8]),
        tranche_id=str(row[9]),
        symbol=str(row[10]),
        direction=str(row[11]),
        lifecycle_state=str(row[12]),
        order_spec_digest=str(row[13]),
        submit_authorized_digest=str(row[14]),
        held_committed_capital=_decimal_text(str(row[15])),
        payload=json.loads(str(row[16]), parse_float=Decimal),
        payload_digest=str(row[17]),
    )


def _decimal_text(value: str) -> str:
    resolved = Decimal(value)
    return format(resolved.normalize(), "f") if resolved != 0 else "0"
