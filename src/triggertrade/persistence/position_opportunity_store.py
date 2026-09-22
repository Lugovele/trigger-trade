"""Durable initial Position opportunity records for B7A."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.position_rules import PositionOpportunityCommand, PositionOpportunityHandler, PositionOpportunityResult

from .durable_messages import DurableMessageStore
from .position_config_pin_store import PositionConfigPinConflict, PositionConfigPinStore
from .postgres import OwnerStateConflict, OwnerStateStore, PostgresPersistenceError


class PositionOpportunityConflict(PostgresPersistenceError):
    """Raised when an initial Position opportunity replays with different content."""


@dataclass(frozen=True)
class PositionOpportunityRecord:
    position_decision_id: str
    decision_cycle_id: str
    set_result_id: str
    symbol: str
    decision: str
    payload: dict[str, Any]
    payload_digest: str


class PositionOpportunityStore:
    """Persist one immutable initial Position opportunity and publish its outbox."""

    def __init__(self, connection) -> None:
        self._connection = connection
        self._owner_state = OwnerStateStore(connection)
        self._messages = DurableMessageStore(connection)
        self._pins = PositionConfigPinStore(connection)
        self._handler = PositionOpportunityHandler()

    def evaluate_and_record(self, command: PositionOpportunityCommand) -> tuple[PositionOpportunityRecord, bool]:
        result = self._handler.evaluate(command)
        try:
            self._pins.pin(
                position_decision_id=command.position_decision_id,
                market_handoff=result.market_handoff.to_payload(),
                rules_version=command.rules_version,
                pinned_at=command.occurred_at,
            )
        except PositionConfigPinConflict as exc:
            raise PositionOpportunityConflict("position opportunity configuration pin already exists with different content") from exc
        payload = result.to_state_payload()
        digest = canonical_json_digest(payload)
        try:
            state, inserted = self._owner_state.put_if_absent(
                owner="Position",
                state_type="position_opportunity",
                state_id=result.evaluation.position_decision_id,
                payload=payload,
            )
        except OwnerStateConflict as exc:
            raise PositionOpportunityConflict("position opportunity identity already exists with different content") from exc
        if state.payload_digest != digest:
            raise PositionOpportunityConflict("position opportunity identity already exists with different content")
        record = _record_from_payload(state.payload, state.payload_digest)
        self._publish(result)
        return record, inserted

    def get_by_position_decision_id(self, *, position_decision_id: str) -> PositionOpportunityRecord | None:
        state = self._owner_state.get(owner="Position", state_type="position_opportunity", state_id=position_decision_id)
        if state is None:
            return None
        return _record_from_payload(state.payload, state.payload_digest)

    def _publish(self, result: PositionOpportunityResult) -> None:
        payload = result.decision.to_payload()
        body = payload["position_decision"]
        self._messages.append_outbox(
            message_id=body["event_id"],
            producer="Position",
            consumer="Portfolio",
            message_type="APPROVE_REJECT",
            message_version="5",
            payload=payload,
            aggregate_id=body["position_decision_id"],
            causation_id=body["set_result_id"],
            correlation_id=body["decision_cycle_id"],
            dedupe_key=f"OPPORTUNITY_DECISION:{body['position_decision_id']}",
        )


def _record_from_payload(payload: dict[str, Any], payload_digest: str) -> PositionOpportunityRecord:
    state = payload["position_opportunity_state"]
    decision = state["decision"]
    return PositionOpportunityRecord(
        position_decision_id=str(decision["position_decision_id"]),
        decision_cycle_id=str(decision["decision_cycle_id"]),
        set_result_id=str(decision["set_result_id"]),
        symbol=str(decision["symbol"]),
        decision=str(decision["decision"]),
        payload=json.loads(json.dumps(payload), parse_float=Decimal),
        payload_digest=payload_digest,
    )
