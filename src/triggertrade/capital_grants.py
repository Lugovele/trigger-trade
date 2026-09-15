"""Capital and Limits v5 grant construction and APPROVE binding checks."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from triggertrade.contracts import ContractError, TargetContract, parse_contract


class CapitalGrantError(ValueError):
    """Raised when a Capital and Limits grant cannot be issued safely."""


def build_capital_and_limits_grant(
    *,
    capital_grant_id: str,
    approved_decision: Mapping[str, Any],
    created_at: str,
    as_of: str,
    portfolio_state_revision: int,
    requested_capital_per_tranche: str,
    minimum_tranche_capital: str,
    remaining_coin_capital: str,
    remaining_global_capital: str,
    remaining_coin_slots: int,
    remaining_global_slots: int,
    relevant_portfolio_limits: Mapping[str, Any],
    accounting_policy: Mapping[str, Any],
    venue_facts: Mapping[str, Any],
) -> TargetContract:
    decision = _approved_decision_body(approved_decision)
    payload = {
        "capital_and_limits": {
            "contract_version": 5,
            "capital_grant_id": _text(capital_grant_id, field="capital_grant_id"),
            "position_decision_id": decision["position_decision_id"],
            "decision_cycle_id": decision["decision_cycle_id"],
            "set_result_id": decision["set_result_id"],
            "symbol": decision["symbol"],
            "created_at": _text(created_at, field="created_at"),
            "as_of": _text(as_of, field="as_of"),
            "grant_state_at_issue": "ISSUED",
            "portfolio_state_revision": _nonnegative_int(portfolio_state_revision, field="portfolio_state_revision"),
            "requested_capital_per_tranche": _decimal_text(
                requested_capital_per_tranche, field="requested_capital_per_tranche"
            ),
            "minimum_tranche_capital": _decimal_text(minimum_tranche_capital, field="minimum_tranche_capital"),
            "remaining_coin_capital": _decimal_text(remaining_coin_capital, field="remaining_coin_capital"),
            "remaining_global_capital": _decimal_text(remaining_global_capital, field="remaining_global_capital"),
            "remaining_coin_slots": _nonnegative_int(remaining_coin_slots, field="remaining_coin_slots"),
            "remaining_global_slots": _nonnegative_int(remaining_global_slots, field="remaining_global_slots"),
            "relevant_portfolio_limits": dict(relevant_portfolio_limits),
            "accounting_policy": dict(accounting_policy),
            "venue_facts": dict(venue_facts),
            "numeric_policy_version": "TT_NUMERIC_V1",
        }
    }
    return _parse_grant(payload)


def validate_capital_grant_for_decision(
    *,
    approved_decision: Mapping[str, Any],
    capital_grant: Mapping[str, Any],
) -> TargetContract:
    decision = _approved_decision_body(approved_decision)
    parsed = _parse_grant(capital_grant)
    grant = parsed.to_payload()["capital_and_limits"]
    for field in ("position_decision_id", "decision_cycle_id", "set_result_id", "symbol"):
        if grant[field] != decision[field]:
            raise CapitalGrantError(f"capital grant {field} must match approved decision")
    return parsed


def _approved_decision_body(payload: Mapping[str, Any]) -> dict[str, Any]:
    try:
        parsed = parse_contract("APPROVE_REJECT", payload, definition="APPROVE_REJECT.initial")
    except ContractError as exc:
        raise CapitalGrantError(str(exc)) from exc
    body = parsed.to_payload()["position_decision"]
    if body["decision"] != "APPROVE":
        raise CapitalGrantError("Capital and Limits may only be issued for APPROVE decisions")
    return body


def _parse_grant(payload: Mapping[str, Any]) -> TargetContract:
    try:
        return parse_contract("CAPITAL_AND_LIMITS", payload)
    except ContractError as exc:
        raise CapitalGrantError(str(exc)) from exc


def _text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise CapitalGrantError(f"{field} is required")
    return value


def _decimal_text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise CapitalGrantError(f"{field} must be an exact decimal string")
    return value


def _nonnegative_int(value: int, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CapitalGrantError(f"{field} must be a nonnegative integer")
    return value
