"""Order Lifecycle start gate for matching Order Spec and Submit Authorized."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.contracts import ContractError, TargetContract, parse_contract
from triggertrade.order_specs import order_spec_digest


READY_TO_SUBMIT = "READY_TO_SUBMIT"


class LifecycleStartGateError(ValueError):
    """Raised when a Lifecycle start gate cannot become submit-eligible."""


@dataclass(frozen=True)
class LifecycleStartGateMatch:
    """Approved pre-submit Lifecycle gate facts."""

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
    order_spec_digest: str
    submit_authorized_digest: str
    held_committed_capital: str
    lifecycle_state: str = READY_TO_SUBMIT

    def to_payload(self) -> dict[str, Any]:
        return {
            "lifecycle_start_gate": {
                "gate_version": 1,
                "lifecycle_state": self.lifecycle_state,
                "order_spec_id": self.order_spec_id,
                "authorization_id": self.authorization_id,
                "capital_grant_id": self.capital_grant_id,
                "decision_cycle_id": self.decision_cycle_id,
                "set_result_id": self.set_result_id,
                "position_decision_id": self.position_decision_id,
                "construction_result_id": self.construction_result_id,
                "position_plan_id": self.position_plan_id,
                "tranche_id": self.tranche_id,
                "symbol": self.symbol,
                "direction": self.direction,
                "order_spec_digest": self.order_spec_digest,
                "submit_authorized_digest": self.submit_authorized_digest,
                "held_committed_capital": self.held_committed_capital,
            }
        }


def match_lifecycle_start_gate(
    *,
    order_spec: Mapping[str, Any],
    submit_authorized: Mapping[str, Any],
) -> LifecycleStartGateMatch:
    """Validate that the two independent Lifecycle inputs authorize submit readiness."""

    spec_contract = _parse("ORDER_SPEC", order_spec)
    authorization_contract = _parse("SUBMIT_AUTHORIZED", submit_authorized)
    spec_payload = spec_contract.to_payload()["order_spec"]
    authorization_payload = authorization_contract.to_payload()["submit_authorized"]

    spec_digest = order_spec_digest(spec_contract)
    authorization_digest = canonical_json_digest(authorization_contract.to_payload())
    _validate_contract_versions(spec=spec_payload, authorization=authorization_payload)
    _validate_identity(spec=spec_payload, authorization=authorization_payload)
    _validate_digest(spec_digest=spec_digest, authorization=authorization_payload)
    _validate_committed_capital(spec=spec_payload, authorization=authorization_payload)
    _validate_spec_gate_state(spec_payload)

    return LifecycleStartGateMatch(
        order_spec_id=str(spec_payload["order_spec_id"]),
        authorization_id=str(authorization_payload["authorization_id"]),
        capital_grant_id=str(spec_payload["capital_grant_id"]),
        decision_cycle_id=str(spec_payload["decision_cycle_id"]),
        set_result_id=str(spec_payload["set_result_id"]),
        position_decision_id=str(spec_payload["position_decision_id"]),
        construction_result_id=str(spec_payload["construction_result_id"]),
        position_plan_id=str(spec_payload["position_plan_id"]),
        tranche_id=str(spec_payload["tranche_id"]),
        symbol=str(spec_payload["symbol"]),
        direction=str(spec_payload["direction"]),
        order_spec_digest=spec_digest,
        submit_authorized_digest=authorization_digest,
        held_committed_capital=str(authorization_payload["held_committed_capital"]),
    )


def lifecycle_start_gate_digest(match: LifecycleStartGateMatch) -> str:
    """Return a canonical digest for the accepted internal gate facts."""

    return canonical_json_digest(match.to_payload())


def _parse(contract_type: str, payload: Mapping[str, Any]) -> TargetContract:
    try:
        return parse_contract(contract_type, payload)
    except ContractError as exc:
        raise LifecycleStartGateError(str(exc)) from exc


def _validate_contract_versions(*, spec: Mapping[str, Any], authorization: Mapping[str, Any]) -> None:
    if spec["contract_version"] != 5:
        raise LifecycleStartGateError("order spec contract_version must be 5")
    if authorization["contract_version"] != 5:
        raise LifecycleStartGateError("submit authorization contract_version must be 5")
    if authorization["order_spec_contract_version"] != spec["contract_version"]:
        raise LifecycleStartGateError("submit authorization order_spec_contract_version must match Order Spec")


def _validate_identity(*, spec: Mapping[str, Any], authorization: Mapping[str, Any]) -> None:
    for field in (
        "capital_grant_id",
        "decision_cycle_id",
        "set_result_id",
        "position_decision_id",
        "construction_result_id",
        "position_plan_id",
        "tranche_id",
        "order_spec_id",
        "symbol",
    ):
        if authorization[field] != spec[field]:
            raise LifecycleStartGateError(f"submit authorization {field} must match Order Spec")


def _validate_digest(*, spec_digest: str, authorization: Mapping[str, Any]) -> None:
    if authorization["order_spec_digest"] != spec_digest:
        raise LifecycleStartGateError("submit authorization order_spec_digest must match canonical Order Spec digest")


def _validate_committed_capital(*, spec: Mapping[str, Any], authorization: Mapping[str, Any]) -> None:
    committed = str(spec["economics"]["actual_committed_capital"])
    if authorization["held_committed_capital"] != committed:
        raise LifecycleStartGateError(
            "submit authorization held_committed_capital must match Order Spec actual_committed_capital"
        )


def _validate_spec_gate_state(spec: Mapping[str, Any]) -> None:
    economics = spec["economics"]
    if economics["minimum_net_edge_enabled"] is True and economics["minimum_net_edge_result"] != "PASS":
        raise LifecycleStartGateError("minimum_net_edge_enabled=true requires minimum_net_edge_result=PASS")
    if economics["minimum_net_edge_enabled"] is False and economics["minimum_net_edge_result"] != "NOT_APPLICABLE":
        raise LifecycleStartGateError(
            "minimum_net_edge_enabled=false requires minimum_net_edge_result=NOT_APPLICABLE"
        )
    validation = spec["venue_validation"]
    if validation["max_order_qty_status"] == "AVAILABLE":
        quantity = _decimal(str(spec["entry"]["quantity"]), field="entry.quantity")
        max_order_qty = _decimal(str(validation["max_order_qty"]), field="venue_validation.max_order_qty")
        if quantity > max_order_qty:
            raise LifecycleStartGateError("entry quantity exceeds available max_order_qty")


def _decimal(value: str, *, field: str) -> Decimal:
    try:
        resolved = Decimal(value)
    except InvalidOperation as exc:
        raise LifecycleStartGateError(f"{field} must be an exact decimal string") from exc
    if not resolved.is_finite():
        raise LifecycleStartGateError(f"{field} must be finite")
    return resolved
