"""Atomic Portfolio current hold and Submit Authorized workflow for B8C."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.portfolio_current_booking import (
    PortfolioCurrentBookingEvaluation,
    PortfolioCurrentBookingPolicy,
    PortfolioCurrentBookingStatus,
    evaluate_current_portfolio_booking,
)
from triggertrade.portfolio_state import PortfolioState

from .capital_grant_store import CapitalGrantStore
from .order_spec_store import OrderSpecStore
from .portfolio_cooldown_store import PortfolioCooldownRecord, PortfolioCooldownStore
from .position_construction_store import PositionConstructionStore
from .postgres import OwnerStateConflict, OwnerStateStore, PostgresPersistenceError
from .submit_authorization_store import SubmitAuthorizationRecord, SubmitAuthorizationStore


class PortfolioCurrentBookingConflict(PostgresPersistenceError):
    """Raised when a booking identity is replayed with different content."""


@dataclass(frozen=True)
class PortfolioCurrentBookingRecord:
    booking_id: str
    authorization_id: str
    construction_result_id: str
    capital_grant_id: str
    status: str
    primary_reason: str
    payload: dict[str, Any]
    payload_digest: str
    authorization: SubmitAuthorizationRecord | None
    cooldown: PortfolioCooldownRecord | None


class PortfolioCurrentBookingWorkflow:
    """Evaluate, retain and atomically publish B8C current booking effects."""

    def __init__(self, connection) -> None:
        self._connection = connection
        self._owner_state = OwnerStateStore(connection)
        self._grants = CapitalGrantStore(connection)
        self._constructions = PositionConstructionStore(connection)
        self._specs = OrderSpecStore(connection)
        self._authorizations = SubmitAuthorizationStore(connection)
        self._cooldowns = PortfolioCooldownStore(connection)

    def evaluate_and_record(
        self,
        *,
        booking_id: str,
        authorization_id: str,
        construction_result_id: str,
        portfolio_state: PortfolioState,
        policy: PortfolioCurrentBookingPolicy,
        authorized_at: str,
    ) -> tuple[PortfolioCurrentBookingRecord, bool]:
        existing = self.get_by_construction_result_id(construction_result_id=construction_result_id)
        if existing is not None:
            return existing, False
        construction_record = self._constructions.get_by_construction_result_id(
            construction_result_id=construction_result_id
        )
        if construction_record is None:
            raise PostgresPersistenceError("construction result does not exist")
        if construction_record.outcome != "CONSTRUCTED":
            raise PostgresPersistenceError("current booking requires constructed result")
        grant_record = self._grants.get_by_grant_id(capital_grant_id=construction_record.capital_grant_id)
        if grant_record is None:
            raise PostgresPersistenceError("capital grant does not exist")
        spec_record = self._specs.get_by_construction_result_id(construction_result_id=construction_result_id)
        if spec_record is None:
            raise PostgresPersistenceError("constructed result exists without order spec")
        if spec_record.order_spec_id != construction_record.order_spec_id:
            raise PostgresPersistenceError("order spec identity does not match construction result")
        if spec_record.payload_digest != construction_record.order_spec_digest:
            raise PostgresPersistenceError("order spec digest does not match construction result")

        evaluation = evaluate_current_portfolio_booking(
            booking_id=booking_id,
            authorization_id=authorization_id,
            capital_grant=grant_record.payload,
            construction_result=construction_record.payload,
            portfolio_state=portfolio_state,
            policy=policy,
            authorized_at=authorized_at,
        )
        payload = _workflow_payload(evaluation, portfolio_state=portfolio_state, policy=policy)
        digest = canonical_json_digest(payload)
        try:
            state, inserted = self._owner_state.put_if_absent(
                owner="Portfolio",
                state_type="portfolio_current_booking",
                state_id=construction_result_id,
                payload=payload,
            )
        except OwnerStateConflict as exc:
            raise PortfolioCurrentBookingConflict("portfolio current booking already exists with different content") from exc
        if state.payload_digest != digest:
            raise PortfolioCurrentBookingConflict("portfolio current booking already exists with different content")

        stored = state.payload["portfolio_current_booking_workflow"]
        authorization_record = None
        cooldown_record = None
        if stored["booking"]["status"] == PortfolioCurrentBookingStatus.AUTHORIZED.value:
            submit_authorized = stored["booking"]["submit_authorized"]
            authorization_record, _ = self._authorizations.authorize(
                capital_grant=grant_record.payload,
                construction_result=construction_record.payload,
                submit_authorized=submit_authorized,
            )
            auth_body = authorization_record.payload["submit_authorized"]
            cooldown_record, _ = self._cooldowns.create_pin(
                authorization_id=auth_body["authorization_id"],
                tranche_id=auth_body["tranche_id"],
                symbol=auth_body["symbol"],
                portfolio_config_id=policy.portfolio_config_id,
                portfolio_config_version=policy.portfolio_config_version,
                portfolio_config_digest=policy.portfolio_config_digest,
                pinned_cooldown_duration_seconds=policy.pinned_cooldown_duration_seconds,
            )
        return _record_from_payload(
            state.payload,
            state.payload_digest,
            authorization=authorization_record,
            cooldown=cooldown_record,
        ), inserted

    def get_by_construction_result_id(self, *, construction_result_id: str) -> PortfolioCurrentBookingRecord | None:
        state = self._owner_state.get(
            owner="Portfolio",
            state_type="portfolio_current_booking",
            state_id=construction_result_id,
        )
        if state is None:
            return None
        booking = state.payload["portfolio_current_booking_workflow"]["booking"]
        authorization = None
        cooldown = None
        if booking["status"] == PortfolioCurrentBookingStatus.AUTHORIZED.value:
            authorization = self._authorizations.get_by_construction_result_id(
                construction_result_id=construction_result_id
            )
            if authorization is None:
                raise PostgresPersistenceError("authorized Portfolio booking exists without submit authorization")
            body = authorization.payload["submit_authorized"]
            cooldown = self._cooldowns.get(authorization_id=body["authorization_id"], tranche_id=body["tranche_id"])
            if cooldown is None:
                raise PostgresPersistenceError("authorized Portfolio booking exists without cooldown pin")
        return _record_from_payload(state.payload, state.payload_digest, authorization=authorization, cooldown=cooldown)


def _workflow_payload(
    evaluation: PortfolioCurrentBookingEvaluation,
    *,
    portfolio_state: PortfolioState,
    policy: PortfolioCurrentBookingPolicy,
) -> dict[str, Any]:
    booking = evaluation.to_payload()["portfolio_current_booking"]
    return {
        "portfolio_current_booking_workflow": {
            "state_version": 1,
            "booking": booking,
            "current_portfolio_state": portfolio_state.to_payload(),
            "policy": {
                "global_position_cap": policy.global_position_cap,
                "coin_allocation_cap": policy.coin_allocation_cap,
                "max_open_positions": policy.max_open_positions,
                "max_positions_per_coin": policy.max_positions_per_coin,
                "portfolio_config_id": policy.portfolio_config_id,
                "portfolio_config_version": policy.portfolio_config_version,
                "portfolio_config_digest": policy.portfolio_config_digest,
                "pinned_cooldown_duration_seconds": policy.pinned_cooldown_duration_seconds,
                "daily_loss_blocked": policy.daily_loss_blocked,
                "cooldown_status": policy.cooldown_status,
                "incident_frontier_clear": policy.incident_frontier_clear,
            },
        }
    }


def _record_from_payload(
    payload: dict[str, Any],
    payload_digest: str,
    *,
    authorization: SubmitAuthorizationRecord | None,
    cooldown: PortfolioCooldownRecord | None,
) -> PortfolioCurrentBookingRecord:
    workflow = payload["portfolio_current_booking_workflow"]
    booking = workflow["booking"]
    construction = booking["construction_result"]["position_construction_result"]
    return PortfolioCurrentBookingRecord(
        booking_id=str(booking["booking_id"]),
        authorization_id=str(booking["authorization_id"]),
        construction_result_id=str(construction["construction_result_id"]),
        capital_grant_id=str(construction["capital_grant_id"]),
        status=str(booking["status"]),
        primary_reason=str(booking["primary_reason"]),
        payload=json.loads(json.dumps(payload), parse_float=Decimal),
        payload_digest=payload_digest,
        authorization=authorization,
        cooldown=cooldown,
    )
