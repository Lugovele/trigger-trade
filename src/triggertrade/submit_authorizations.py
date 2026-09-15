"""Submit Authorized v5 construction and hold gate validation."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

from triggertrade.contracts import ContractError, TargetContract, parse_contract


class SubmitAuthorizationError(ValueError):
    """Raised when Portfolio cannot authorize order submission safely."""


def build_submit_authorized(
    *,
    authorization_id: str,
    capital_grant: Mapping[str, Any],
    construction_result: Mapping[str, Any],
    authorized_at: str,
) -> TargetContract:
    grant = _grant_body(capital_grant)
    construction = _construction_body(construction_result)
    _validate_binding(grant=grant, construction=construction)
    held_committed_capital = str(construction["approved_economics"]["approved_actual_committed_capital"])
    _validate_capacity(grant=grant, held_committed_capital=held_committed_capital)
    payload = {
        "submit_authorized": {
            "contract_version": 5,
            "authorization_id": _text(authorization_id, field="authorization_id"),
            "capital_grant_id": grant["capital_grant_id"],
            "decision_cycle_id": grant["decision_cycle_id"],
            "set_result_id": grant["set_result_id"],
            "position_decision_id": grant["position_decision_id"],
            "construction_result_id": construction["construction_result_id"],
            "position_plan_id": construction["position_plan_id"],
            "tranche_id": construction["tranche_id"],
            "order_spec_id": construction["order_spec_id"],
            "symbol": grant["symbol"],
            "order_spec_digest": construction["order_spec_digest"],
            "held_committed_capital": held_committed_capital,
            "authorized_at": _text(authorized_at, field="authorized_at"),
            "numeric_policy_version": "TT_NUMERIC_V1",
            "order_spec_contract_version": 5,
        }
    }
    return _parse_submit_authorized(payload)


def validate_submit_authorized(
    *,
    capital_grant: Mapping[str, Any],
    construction_result: Mapping[str, Any],
    submit_authorized: Mapping[str, Any],
) -> TargetContract:
    grant = _grant_body(capital_grant)
    construction = _construction_body(construction_result)
    _validate_binding(grant=grant, construction=construction)
    parsed = _parse_submit_authorized(submit_authorized)
    authorization = parsed.to_payload()["submit_authorized"]
    expected = build_submit_authorized(
        authorization_id=str(authorization["authorization_id"]),
        capital_grant=capital_grant,
        construction_result=construction_result,
        authorized_at=str(authorization["authorized_at"]),
    ).to_payload()["submit_authorized"]
    for field, value in expected.items():
        if authorization[field] != value:
            raise SubmitAuthorizationError(f"submit authorization {field} must match grant and construction result")
    return parsed


def _validate_binding(*, grant: Mapping[str, Any], construction: Mapping[str, Any]) -> None:
    for field in ("capital_grant_id", "position_decision_id", "decision_cycle_id", "set_result_id", "symbol"):
        if grant[field] != construction[field]:
            raise SubmitAuthorizationError(f"construction result {field} must match capital grant")
    if construction["outcome"] != "CONSTRUCTED":
        raise SubmitAuthorizationError("submit authorization requires CONSTRUCTED outcome")


def _validate_capacity(*, grant: Mapping[str, Any], held_committed_capital: str) -> None:
    held = _decimal(held_committed_capital, field="held_committed_capital")
    for field in ("requested_capital_per_tranche", "remaining_coin_capital", "remaining_global_capital"):
        if held > _decimal(str(grant[field]), field=field):
            raise SubmitAuthorizationError(f"held_committed_capital exceeds {field}")
    for field in ("remaining_coin_slots", "remaining_global_slots"):
        if int(grant[field]) < 1:
            raise SubmitAuthorizationError(f"{field} must have capacity for a submission hold")


def _grant_body(payload: Mapping[str, Any]) -> dict[str, Any]:
    try:
        parsed = parse_contract("CAPITAL_AND_LIMITS", payload)
    except ContractError as exc:
        raise SubmitAuthorizationError(str(exc)) from exc
    return parsed.to_payload()["capital_and_limits"]


def _construction_body(payload: Mapping[str, Any]) -> dict[str, Any]:
    try:
        parsed = parse_contract("APPROVE_REJECT", payload, definition="APPROVE_REJECT.constructed")
    except ContractError as exc:
        raise SubmitAuthorizationError(str(exc)) from exc
    return parsed.to_payload()["position_construction_result"]


def _parse_submit_authorized(payload: Mapping[str, Any]) -> TargetContract:
    try:
        return parse_contract("SUBMIT_AUTHORIZED", payload)
    except ContractError as exc:
        raise SubmitAuthorizationError(str(exc)) from exc


def _text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise SubmitAuthorizationError(f"{field} is required")
    return value


def _decimal(value: str, *, field: str) -> Decimal:
    if not isinstance(value, str) or not value:
        raise SubmitAuthorizationError(f"{field} must be an exact decimal string")
    try:
        resolved = Decimal(value)
    except InvalidOperation as exc:
        raise SubmitAuthorizationError(f"{field} must be an exact decimal string") from exc
    if not resolved.is_finite() or resolved < 0:
        raise SubmitAuthorizationError(f"{field} must be a finite nonnegative decimal string")
    return resolved
