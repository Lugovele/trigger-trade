"""Position construction result validation without formula implementation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from triggertrade.contracts import ContractError, TargetContract, parse_contract


class PositionConstructionError(ValueError):
    """Raised when a Position construction result cannot be accepted safely."""


def build_constructed_position_result(
    *,
    event_id: str,
    occurred_at: str,
    construction_result_id: str,
    capital_grant: Mapping[str, Any],
    position_plan_id: str,
    tranche_id: str,
    order_spec_id: str,
    order_spec_digest: str,
    approved_economics: Mapping[str, Any],
    minimum_net_edge: Mapping[str, Any],
    direction: str,
    reason_code: str = "CONSTRUCTED",
) -> TargetContract:
    """Build a CONSTRUCTED result from already-determined construction values.

    Formula-owned values are supplied by the caller and are only bound and
    validated here. This function does not calculate Entry, Stop, Take, sizing,
    leverage, risk/reward, or net-edge formulas.
    """

    grant = _grant_body(capital_grant)
    payload = {
        "position_construction_result": {
            "contract_version": 5,
            "event_variant": "CONSTRUCTION_RESULT",
            "event_id": _text(event_id, field="event_id"),
            "occurred_at": _text(occurred_at, field="occurred_at"),
            "position_decision_id": grant["position_decision_id"],
            "construction_result_id": _text(construction_result_id, field="construction_result_id"),
            "capital_grant_id": grant["capital_grant_id"],
            "decision_cycle_id": grant["decision_cycle_id"],
            "set_result_id": grant["set_result_id"],
            "symbol": grant["symbol"],
            "reason_code": _text(reason_code, field="reason_code"),
            "rule_results": {"minimum_net_edge": dict(minimum_net_edge)},
            "outcome": "CONSTRUCTED",
            "position_plan_id": _text(position_plan_id, field="position_plan_id"),
            "tranche_id": _text(tranche_id, field="tranche_id"),
            "order_spec_id": _text(order_spec_id, field="order_spec_id"),
            "order_spec_digest": _text(order_spec_digest, field="order_spec_digest"),
            "approved_economics": dict(approved_economics),
            "numeric_policy_version": "TT_NUMERIC_V1",
            "direction": _text(direction, field="direction"),
            "order_spec_contract_version": 5,
        }
    }
    return _parse_and_validate(capital_grant=capital_grant, construction_result=payload)


def build_rejected_position_construction_result(
    *,
    event_id: str,
    occurred_at: str,
    construction_result_id: str,
    capital_grant: Mapping[str, Any],
    minimum_net_edge: Mapping[str, Any],
    failed_gates: Sequence[str],
    reason_code: str,
) -> TargetContract:
    """Build a post-grant construction REJECT without successful plan/spec fields."""

    grant = _grant_body(capital_grant)
    payload = {
        "position_construction_result": {
            "contract_version": 5,
            "event_variant": "CONSTRUCTION_RESULT",
            "event_id": _text(event_id, field="event_id"),
            "occurred_at": _text(occurred_at, field="occurred_at"),
            "position_decision_id": grant["position_decision_id"],
            "construction_result_id": _text(construction_result_id, field="construction_result_id"),
            "capital_grant_id": grant["capital_grant_id"],
            "decision_cycle_id": grant["decision_cycle_id"],
            "set_result_id": grant["set_result_id"],
            "symbol": grant["symbol"],
            "reason_code": _text(reason_code, field="reason_code"),
            "rule_results": {"minimum_net_edge": dict(minimum_net_edge)},
            "outcome": "REJECT",
            "failed_gates": [_text(gate, field="failed_gates") for gate in failed_gates],
        }
    }
    return _parse_and_validate(capital_grant=capital_grant, construction_result=payload)


def validate_position_construction_result(
    *,
    capital_grant: Mapping[str, Any],
    construction_result: Mapping[str, Any],
) -> TargetContract:
    """Validate a construction result against its exact Capital and Limits grant."""

    return _parse_and_validate(capital_grant=capital_grant, construction_result=construction_result)


def _parse_and_validate(*, capital_grant: Mapping[str, Any], construction_result: Mapping[str, Any]) -> TargetContract:
    grant = _grant_body(capital_grant)
    parsed = _parse_construction(construction_result)
    body = parsed.to_payload()["position_construction_result"]
    for field in ("capital_grant_id", "position_decision_id", "decision_cycle_id", "set_result_id", "symbol"):
        if body[field] != grant[field]:
            raise PositionConstructionError(f"construction result {field} must match Capital and Limits grant")
    _validate_minimum_net_edge(body)
    return parsed


def _grant_body(payload: Mapping[str, Any]) -> dict[str, Any]:
    try:
        parsed = parse_contract("CAPITAL_AND_LIMITS", payload)
    except ContractError as exc:
        raise PositionConstructionError(str(exc)) from exc
    return parsed.to_payload()["capital_and_limits"]


def _parse_construction(payload: Mapping[str, Any]) -> TargetContract:
    try:
        body = payload["position_construction_result"]
    except KeyError as exc:
        raise PositionConstructionError("position_construction_result is required") from exc
    outcome = body.get("outcome")
    definition = "APPROVE_REJECT.constructed" if outcome == "CONSTRUCTED" else "APPROVE_REJECT.failed"
    try:
        return parse_contract("APPROVE_REJECT", payload, definition=definition)
    except ContractError as exc:
        raise PositionConstructionError(str(exc)) from exc


def _validate_minimum_net_edge(body: Mapping[str, Any]) -> None:
    rule = body["rule_results"]["minimum_net_edge"]
    enabled = rule["enabled"]
    status = rule["status"]
    if body["outcome"] == "CONSTRUCTED":
        if enabled is True and status != "PASS":
            raise PositionConstructionError("enabled minimum_net_edge must PASS for CONSTRUCTED")
        if enabled is False and status != "NOT_APPLICABLE":
            raise PositionConstructionError("disabled minimum_net_edge must be NOT_APPLICABLE for CONSTRUCTED")


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PositionConstructionError(f"{field} is required")
    return value
