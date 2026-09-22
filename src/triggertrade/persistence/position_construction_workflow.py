"""Atomic post-grant Position construction workflow for B7B."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.position_rules.construction import (
    ConstructionStatus,
    PositionConstructionCommand,
    PositionConstructionEvaluation,
    evaluate_position_construction,
)

from .order_spec_store import OrderSpecRecord, OrderSpecStore
from .position_construction_store import PositionConstructionRecord, PositionConstructionStore
from .postgres import OwnerStateConflict, OwnerStateStore, PostgresPersistenceError


class PositionConstructionWorkflowConflict(PostgresPersistenceError):
    """Raised when post-grant construction replays with different content."""


@dataclass(frozen=True)
class PositionConstructionWorkflowRecord:
    construction_result_id: str
    capital_grant_id: str
    status: str
    primary_reason: str
    payload: dict[str, Any]
    payload_digest: str
    construction: PositionConstructionRecord
    order_spec: OrderSpecRecord | None


class PositionConstructionWorkflow:
    """Evaluate, persist and publish B7B construction/spec in one transaction."""

    def __init__(self, connection) -> None:
        self._connection = connection
        self._owner_state = OwnerStateStore(connection)
        self._constructions = PositionConstructionStore(connection)
        self._specs = OrderSpecStore(connection)

    def evaluate_and_record(self, command: PositionConstructionCommand) -> tuple[PositionConstructionWorkflowRecord, bool]:
        evaluation = evaluate_position_construction(command)
        payload = evaluation.to_payload()
        digest = canonical_json_digest(payload)
        state_id = command.construction_result_id
        try:
            state, inserted = self._owner_state.put_if_absent(
                owner="Position",
                state_type="position_construction_workflow",
                state_id=state_id,
                payload=payload,
            )
        except OwnerStateConflict as exc:
            raise PositionConstructionWorkflowConflict("position construction workflow already exists with different content") from exc
        if state.payload_digest != digest:
            raise PositionConstructionWorkflowConflict("position construction workflow already exists with different content")
        record_payload = state.payload
        workflow = record_payload["position_construction_evaluation"]
        construction_record, _ = self._constructions.record(
            capital_grant=command.capital_grant,
            construction_result=workflow["construction_result"],
        )
        spec_record = None
        if workflow["status"] == ConstructionStatus.CONSTRUCTED.value:
            spec_record, _ = self._specs.record(
                construction_result=workflow["construction_result"],
                order_spec=workflow["order_spec"],
            )
        return _record_from_payload(
            record_payload,
            state.payload_digest,
            construction=construction_record,
            order_spec=spec_record,
        ), inserted

    def get_by_construction_result_id(self, *, construction_result_id: str) -> PositionConstructionWorkflowRecord | None:
        state = self._owner_state.get(
            owner="Position",
            state_type="position_construction_workflow",
            state_id=construction_result_id,
        )
        if state is None:
            return None
        construction = self._constructions.get_by_construction_result_id(construction_result_id=construction_result_id)
        if construction is None:
            raise PostgresPersistenceError("position construction workflow exists without construction result")
        spec = self._specs.get_by_construction_result_id(construction_result_id=construction_result_id)
        if (
            state.payload["position_construction_evaluation"]["status"] == ConstructionStatus.CONSTRUCTED.value
            and spec is None
        ):
            raise PostgresPersistenceError("constructed position workflow exists without order spec")
        return _record_from_payload(state.payload, state.payload_digest, construction=construction, order_spec=spec)


def _record_from_payload(
    payload: dict[str, Any],
    payload_digest: str,
    *,
    construction: PositionConstructionRecord,
    order_spec: OrderSpecRecord | None,
) -> PositionConstructionWorkflowRecord:
    state = payload["position_construction_evaluation"]
    body = state["construction_result"]["position_construction_result"]
    return PositionConstructionWorkflowRecord(
        construction_result_id=str(body["construction_result_id"]),
        capital_grant_id=str(body["capital_grant_id"]),
        status=str(state["status"]),
        primary_reason=str(state["primary_reason"]),
        payload=json.loads(json.dumps(payload), parse_float=Decimal),
        payload_digest=payload_digest,
        construction=construction,
        order_spec=order_spec,
    )
