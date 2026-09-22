"""Durable Portfolio grant evaluation and non-reserving issue for B8B."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.portfolio_grants import (
    PortfolioGrantEvaluation,
    PortfolioGrantPolicy,
    PortfolioGrantStatus,
    evaluate_portfolio_grant,
    validate_approved_initial_decision,
)
from triggertrade.portfolio_state import PortfolioState

from .capital_grant_store import CapitalGrantConflict, CapitalGrantRecord, CapitalGrantStore
from .postgres import OwnerStateConflict, OwnerStateStore, PostgresPersistenceError


class PortfolioGrantDecisionConflict(PostgresPersistenceError):
    """Raised when a Portfolio grant decision replays with different content."""


@dataclass(frozen=True)
class PortfolioGrantDecisionRecord:
    grant_decision_id: str
    position_decision_id: str
    status: str
    primary_reason: str
    payload: dict[str, Any]
    payload_digest: str
    capital_grant: CapitalGrantRecord | None = None


class PortfolioGrantDecisionStore:
    """Evaluate and persist B8B Portfolio grant outcomes atomically."""

    def __init__(self, connection) -> None:
        self._connection = connection
        self._owner_state = OwnerStateStore(connection)
        self._grants = CapitalGrantStore(connection)

    def evaluate_and_record(
        self,
        *,
        grant_decision_id: str,
        capital_grant_id: str,
        approved_decision: dict[str, Any],
        portfolio_state: PortfolioState,
        policy: PortfolioGrantPolicy,
        venue_facts: dict[str, Any],
        as_of: str,
    ) -> tuple[PortfolioGrantDecisionRecord, bool]:
        parsed_decision = validate_approved_initial_decision(approved_decision)
        position_decision_id = str(parsed_decision.to_payload()["position_decision"]["position_decision_id"])
        existing = self._owner_state.get(
            owner="Portfolio",
            state_type="portfolio_grant_decision",
            state_id=position_decision_id,
        )
        if existing is not None:
            record = _record_from_payload(existing.payload, existing.payload_digest, capital_grant=None)
            stored_decision = record.payload["portfolio_grant_decision"]["approved_decision"]
            if canonical_json_digest(stored_decision) != canonical_json_digest(parsed_decision.to_payload()):
                raise PortfolioGrantDecisionConflict("Portfolio grant decision already exists for a different approved decision")
            grant_record = self._repair_allowed_grant(record)
            return _record_from_payload(existing.payload, existing.payload_digest, capital_grant=grant_record), False

        evaluation = evaluate_portfolio_grant(
            grant_decision_id=grant_decision_id,
            capital_grant_id=capital_grant_id,
            approved_decision=approved_decision,
            portfolio_state=portfolio_state,
            policy=policy,
            venue_facts=venue_facts,
            as_of=as_of,
        )
        payload = evaluation.to_payload()
        digest = canonical_json_digest(payload)
        position_decision_id = _position_decision_id(evaluation)
        try:
            state, inserted = self._owner_state.put_if_absent(
                owner="Portfolio",
                state_type="portfolio_grant_decision",
                state_id=position_decision_id,
                payload=payload,
            )
        except OwnerStateConflict as exc:
            replayed = self._existing_same_decision(position_decision_id, parsed_decision.to_payload())
            if replayed is not None:
                return replayed, False
            raise PortfolioGrantDecisionConflict("Portfolio grant decision already exists with different content") from exc
        if state.payload_digest != digest:
            replayed = self._existing_same_decision(position_decision_id, parsed_decision.to_payload())
            if replayed is not None:
                return replayed, False
            raise PortfolioGrantDecisionConflict("Portfolio grant decision already exists with different content")
        grant_record = None
        if evaluation.status is PortfolioGrantStatus.ALLOWED and evaluation.capital_grant is not None:
            try:
                grant_record, _ = self._grants.issue(
                    approved_decision=evaluation.approved_decision.to_payload(),
                    capital_grant=evaluation.capital_grant.to_payload(),
                )
            except CapitalGrantConflict as exc:
                raise PortfolioGrantDecisionConflict("Capital grant already exists with different content") from exc
        return _record_from_payload(state.payload, state.payload_digest, capital_grant=grant_record), inserted

    def get_by_position_decision_id(self, *, position_decision_id: str) -> PortfolioGrantDecisionRecord | None:
        state = self._owner_state.get(
            owner="Portfolio",
            state_type="portfolio_grant_decision",
            state_id=position_decision_id,
        )
        if state is None:
            return None
        grant = CapitalGrantStore(self._connection).get_by_position_decision(position_decision_id=position_decision_id)
        return _record_from_payload(state.payload, state.payload_digest, capital_grant=grant)

    def _existing_same_decision(
        self,
        position_decision_id: str,
        approved_decision: dict[str, Any],
    ) -> PortfolioGrantDecisionRecord | None:
        existing = self._owner_state.get(
            owner="Portfolio",
            state_type="portfolio_grant_decision",
            state_id=position_decision_id,
        )
        if existing is None:
            return None
        record = _record_from_payload(existing.payload, existing.payload_digest, capital_grant=None)
        stored_decision = record.payload["portfolio_grant_decision"]["approved_decision"]
        if canonical_json_digest(stored_decision) != canonical_json_digest(approved_decision):
            return None
        grant_record = self._repair_allowed_grant(record)
        return _record_from_payload(existing.payload, existing.payload_digest, capital_grant=grant_record)

    def _repair_allowed_grant(self, record: PortfolioGrantDecisionRecord) -> CapitalGrantRecord | None:
        state = record.payload["portfolio_grant_decision"]
        if state["status"] != PortfolioGrantStatus.ALLOWED.value or state["capital_grant"] is None:
            return None
        try:
            grant_record, _ = self._grants.issue(
                approved_decision=state["approved_decision"],
                capital_grant=state["capital_grant"],
            )
        except CapitalGrantConflict as exc:
            raise PortfolioGrantDecisionConflict("Capital grant already exists with different content") from exc
        return grant_record


def _position_decision_id(evaluation: PortfolioGrantEvaluation) -> str:
    return str(evaluation.approved_decision.to_payload()["position_decision"]["position_decision_id"])


def _record_from_payload(
    payload: dict[str, Any],
    payload_digest: str,
    *,
    capital_grant: CapitalGrantRecord | None,
) -> PortfolioGrantDecisionRecord:
    state = payload["portfolio_grant_decision"]
    decision = state["approved_decision"]["position_decision"]
    return PortfolioGrantDecisionRecord(
        grant_decision_id=str(state["grant_decision_id"]),
        position_decision_id=str(decision["position_decision_id"]),
        status=str(state["status"]),
        primary_reason=str(state["primary_reason"]),
        payload=json.loads(json.dumps(payload), parse_float=Decimal),
        payload_digest=payload_digest,
        capital_grant=capital_grant,
    )
