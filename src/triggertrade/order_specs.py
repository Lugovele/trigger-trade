"""Order Spec v5 validation and construction binding."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.contracts import ContractError, TargetContract, parse_contract


class OrderSpecError(ValueError):
    """Raised when an Order Spec cannot be accepted safely."""


def build_order_spec(
    *,
    order_spec_id: str,
    spec_created_at: str,
    construction_result_id: str,
    capital_grant: Mapping[str, Any],
    position_plan_id: str,
    tranche_id: str,
    direction: str,
    side: str,
    entry: Mapping[str, Any],
    leverage: str,
    take_profit: Mapping[str, Any],
    stop_loss: Mapping[str, Any],
    economics: Mapping[str, Any],
    venue_validation: Mapping[str, Any],
    provenance: Mapping[str, Any],
) -> TargetContract:
    """Build an Order Spec from already-determined construction values.

    Formula-owned prices, sizing, leverage, notional, risk/reward, and net-edge
    values are provided by the caller and only validated against the v5 wire
    contract here.
    """

    grant = _grant_body(capital_grant)
    payload = {
        "order_spec": {
            "contract_version": 5,
            "order_spec_id": _text(order_spec_id, field="order_spec_id"),
            "spec_created_at": _text(spec_created_at, field="spec_created_at"),
            "capital_grant_id": grant["capital_grant_id"],
            "decision_cycle_id": grant["decision_cycle_id"],
            "set_result_id": grant["set_result_id"],
            "position_decision_id": grant["position_decision_id"],
            "construction_result_id": _text(construction_result_id, field="construction_result_id"),
            "position_plan_id": _text(position_plan_id, field="position_plan_id"),
            "tranche_id": _text(tranche_id, field="tranche_id"),
            "symbol": grant["symbol"],
            "direction": _text(direction, field="direction"),
            "side": _text(side, field="side"),
            "entry": dict(entry),
            "leverage": _text(leverage, field="leverage"),
            "take_profit": dict(take_profit),
            "stop_loss": dict(stop_loss),
            "economics": dict(economics),
            "venue_validation": dict(venue_validation),
            "accounting_policy": dict(grant["accounting_policy"]),
            "provenance": dict(provenance),
            "numeric_policy_version": "TT_NUMERIC_V1",
        }
    }
    return validate_order_spec(order_spec=payload)


def validate_order_spec(*, order_spec: Mapping[str, Any]) -> TargetContract:
    """Validate an Order Spec against the approved v5 wire contract."""

    try:
        return parse_contract("ORDER_SPEC", order_spec)
    except ContractError as exc:
        raise OrderSpecError(str(exc)) from exc


def validate_order_spec_for_construction(
    *,
    construction_result: Mapping[str, Any],
    order_spec: Mapping[str, Any],
) -> TargetContract:
    """Validate immutable Order Spec identity and scalar duplication."""

    construction = _constructed_body(construction_result)
    parsed = validate_order_spec(order_spec=order_spec)
    spec = parsed.to_payload()["order_spec"]
    for field in (
        "order_spec_id",
        "capital_grant_id",
        "decision_cycle_id",
        "set_result_id",
        "position_decision_id",
        "construction_result_id",
        "position_plan_id",
        "tranche_id",
        "symbol",
        "direction",
    ):
        if spec[field] != construction[field]:
            raise OrderSpecError(f"order spec {field} must match construction result")
    if construction["order_spec_contract_version"] != spec["contract_version"]:
        raise OrderSpecError("construction result order_spec_contract_version must match Order Spec")
    digest = order_spec_digest(parsed)
    if construction["order_spec_digest"] != digest:
        raise OrderSpecError("construction result order_spec_digest must match canonical Order Spec digest")
    economics = spec["economics"]
    approved = construction["approved_economics"]
    comparisons = {
        "approved_entry": spec["entry"]["price"],
        "approved_quantity": spec["entry"]["quantity"],
        "approved_leverage": spec["leverage"],
        "approved_actual_order_notional": economics["actual_order_notional"],
        "approved_actual_committed_capital": economics["actual_committed_capital"],
    }
    for field, value in comparisons.items():
        if approved[field] != value:
            raise OrderSpecError(f"construction result {field} must match Order Spec")
    rule = construction["rule_results"]["minimum_net_edge"]
    if economics["minimum_net_edge_enabled"] != rule["enabled"]:
        raise OrderSpecError("minimum_net_edge enabled flag must match Order Spec economics")
    if economics["minimum_net_edge_result"] != rule["status"]:
        raise OrderSpecError("minimum_net_edge result must match Order Spec economics")
    if economics["planned_net_edge_pct"] != rule["calculated_value"]:
        raise OrderSpecError("minimum_net_edge calculated_value must match Order Spec planned_net_edge_pct")
    return parsed


def order_spec_digest(order_spec: Mapping[str, Any] | TargetContract) -> str:
    """Return the canonical SHA-256 digest for an Order Spec envelope."""

    parsed = order_spec if isinstance(order_spec, TargetContract) else validate_order_spec(order_spec=order_spec)
    return canonical_json_digest(parsed.to_payload())


def _grant_body(payload: Mapping[str, Any]) -> dict[str, Any]:
    try:
        parsed = parse_contract("CAPITAL_AND_LIMITS", payload)
    except ContractError as exc:
        raise OrderSpecError(str(exc)) from exc
    return parsed.to_payload()["capital_and_limits"]


def _constructed_body(payload: Mapping[str, Any]) -> dict[str, Any]:
    try:
        parsed = parse_contract("APPROVE_REJECT", payload, definition="APPROVE_REJECT.constructed")
    except ContractError as exc:
        raise OrderSpecError(str(exc)) from exc
    return parsed.to_payload()["position_construction_result"]


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise OrderSpecError(f"{field} is required")
    return value
