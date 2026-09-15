"""Canonical durable governance for Research promotion requests."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .durable_messages import DurableMessageStore, OutboxMessageRecord
from .postgres import OwnerStateRecord, OwnerStateStore, PostgresConnectionFactory, PostgresUnitOfWork


RESEARCH_PROMOTION_OWNER = "Research"
RESEARCH_PROMOTION_STATE_TYPE = "research_promotion_request"
RESEARCH_PROMOTION_MESSAGE_TYPE = "RESEARCH_PROMOTION_REQUESTED"
RESEARCH_PROMOTION_MESSAGE_VERSION = "1"
RESEARCH_PROMOTION_CONSUMER = "Scheduler"


@dataclass(frozen=True)
class ResearchPromotionGovernanceRecord:
    request_id: str
    state: OwnerStateRecord
    outbox: OutboxMessageRecord
    inserted: bool


class ResearchPromotionGovernanceStore:
    """Persist canonical promotion requests and publish activation work."""

    def __init__(self, connection) -> None:
        self._owner_state = OwnerStateStore(connection)
        self._messages = DurableMessageStore(connection)

    def request_promotion(
        self,
        *,
        request_id: str,
        payload: Mapping[str, Any],
        research_id: str,
        idempotency_key: str,
    ) -> ResearchPromotionGovernanceRecord:
        state, inserted = self._owner_state.put_if_absent(
            owner=RESEARCH_PROMOTION_OWNER,
            state_type=RESEARCH_PROMOTION_STATE_TYPE,
            state_id=request_id,
            payload=payload,
        )
        outbox, _outbox_inserted = self._messages.append_outbox(
            message_id=request_id,
            producer=RESEARCH_PROMOTION_OWNER,
            consumer=RESEARCH_PROMOTION_CONSUMER,
            message_type=RESEARCH_PROMOTION_MESSAGE_TYPE,
            message_version=RESEARCH_PROMOTION_MESSAGE_VERSION,
            payload=state.payload,
            aggregate_id=research_id,
            dedupe_key=f"research_promotion:{idempotency_key}",
        )
        return ResearchPromotionGovernanceRecord(
            request_id=request_id,
            state=state,
            outbox=outbox,
            inserted=inserted,
        )


class ResearchPromotionGovernanceClient:
    """Open one PostgreSQL unit-of-work per promotion request."""

    def __init__(self, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def request_promotion(
        self,
        *,
        request_id: str,
        payload: Mapping[str, Any],
        research_id: str,
        idempotency_key: str,
    ) -> ResearchPromotionGovernanceRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            return ResearchPromotionGovernanceStore(uow.connection).request_promotion(
                request_id=request_id,
                payload=payload,
                research_id=research_id,
                idempotency_key=idempotency_key,
            )
