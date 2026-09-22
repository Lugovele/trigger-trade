"""Portfolio-owned non-reserving grant evaluation for v1.2.15 B8B."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Any

from triggertrade.capital_grants import CapitalGrantError, build_capital_and_limits_grant
from triggertrade.contracts import ContractError, TargetContract
from triggertrade.contracts.bindings import ContractBindingError, validate_contract_edge
from triggertrade.numeric_policy import canonical_decimal_text, exact_divide, parse_decimal_text, qcapital_floor
from triggertrade.portfolio_state import CoinPortfolioState, PortfolioHealth, PortfolioState


class PortfolioGrantError(ValueError):
    """Raised when Portfolio cannot evaluate a grant deterministically."""


class PortfolioGrantStatus(StrEnum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class PortfolioGrantPolicy:
    minimum_tranche_capital: str
    global_position_cap: str
    coin_allocation_cap: str
    max_open_positions: int
    max_positions_per_coin: int
    daily_loss_blocked: bool = False
    accounting_timezone: str = "Asia/Jerusalem"
    day_boundary_local: str = "00:00:00"
    accounting_policy_version: str = "ACCOUNTING_DAY_V1"

    def __post_init__(self) -> None:
        _nonnegative_decimal(self.minimum_tranche_capital, field="minimum_tranche_capital")
        _nonnegative_decimal(self.global_position_cap, field="global_position_cap")
        _nonnegative_decimal(self.coin_allocation_cap, field="coin_allocation_cap")
        _nonnegative_int(self.max_open_positions, field="max_open_positions")
        _nonnegative_int(self.max_positions_per_coin, field="max_positions_per_coin")
        if not isinstance(self.daily_loss_blocked, bool):
            raise PortfolioGrantError("daily_loss_blocked must be boolean")

    def relevant_limits_payload(self) -> dict[str, Any]:
        return {
            "global_position_cap": self.global_position_cap,
            "coin_allocation_cap": self.coin_allocation_cap,
            "max_open_positions": self.max_open_positions,
            "max_positions_per_coin": self.max_positions_per_coin,
            "daily_loss_blocked": self.daily_loss_blocked,
        }

    def accounting_policy_payload(self) -> dict[str, Any]:
        return {
            "accounting_timezone": self.accounting_timezone,
            "day_boundary_local": self.day_boundary_local,
            "accounting_policy_version": self.accounting_policy_version,
        }


@dataclass(frozen=True)
class PortfolioGrantEvaluation:
    grant_decision_id: str
    status: PortfolioGrantStatus
    primary_reason: str
    evaluated_reasons: tuple[str, ...]
    gate_results: dict[str, dict[str, Any]]
    approved_decision: TargetContract
    capital_grant: TargetContract | None

    def to_payload(self) -> dict[str, Any]:
        return {
            "portfolio_grant_decision": {
                "state_version": 1,
                "grant_decision_id": self.grant_decision_id,
                "status": self.status.value,
                "primary_reason": self.primary_reason,
                "evaluated_reasons": list(self.evaluated_reasons),
                "gate_results": self.gate_results,
                "approved_decision": self.approved_decision.to_payload(),
                "capital_grant": None if self.capital_grant is None else self.capital_grant.to_payload(),
            }
        }


def evaluate_portfolio_grant(
    *,
    grant_decision_id: str,
    capital_grant_id: str,
    approved_decision: Mapping[str, Any],
    portfolio_state: PortfolioState,
    policy: PortfolioGrantPolicy,
    venue_facts: Mapping[str, Any],
    as_of: str,
) -> PortfolioGrantEvaluation:
    """Evaluate and optionally build one non-reserving Capital and Limits grant."""

    parsed_decision = validate_approved_initial_decision(approved_decision)
    decision = parsed_decision.to_payload()["position_decision"]
    symbol = str(decision["symbol"]).upper()
    gate_results: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []

    if portfolio_state.health is not PortfolioHealth.LIVE:
        gate_results["portfolio_state"] = _gate("UNAVAILABLE", "PORTFOLIO_STATE_UNAVAILABLE")
        return _evaluation(
            grant_decision_id=grant_decision_id,
            status=PortfolioGrantStatus.UNAVAILABLE,
            reasons=("PORTFOLIO_STATE_UNAVAILABLE",),
            gate_results=gate_results,
            approved_decision=parsed_decision,
            capital_grant=None,
        )

    coin_state = _coin_state(portfolio_state, symbol)
    if coin_state is None:
        gate_results["coin_state"] = _gate("UNAVAILABLE", "PORTFOLIO_COIN_STATE_UNAVAILABLE")
        return _evaluation(
            grant_decision_id=grant_decision_id,
            status=PortfolioGrantStatus.UNAVAILABLE,
            reasons=("PORTFOLIO_COIN_STATE_UNAVAILABLE",),
            gate_results=gate_results,
            approved_decision=parsed_decision,
            capital_grant=None,
        )

    global_committed = _bucket_commitment(portfolio_state.global_buckets.to_payload())
    coin_committed = _bucket_commitment(coin_state.buckets.to_payload())
    global_cap = parse_decimal_text(policy.global_position_cap)
    coin_cap = parse_decimal_text(policy.coin_allocation_cap)
    free_global = global_cap - global_committed
    free_coin = coin_cap - coin_committed
    remaining_global_slots = policy.max_open_positions - portfolio_state.global_buckets.committed_tranches
    remaining_coin_slots = policy.max_positions_per_coin - coin_state.buckets.committed_tranches

    candidate = None
    if free_coin > 0 and remaining_coin_slots > 0:
        candidate = qcapital_floor(exact_divide(free_coin, remaining_coin_slots)).value

    _record_gate(
        gate_results,
        reasons,
        gate_id="daily_loss",
        status="FAIL" if policy.daily_loss_blocked else "PASS",
        reason="DAILY_LOSS_LIMIT_REACHED",
        configured=policy.daily_loss_blocked,
    )
    _record_gate(
        gate_results,
        reasons,
        gate_id="global_slots",
        status="PASS" if remaining_global_slots > 0 else "FAIL",
        reason="MAX_OPEN_POSITIONS_REACHED",
        configured=policy.max_open_positions,
        calculated=remaining_global_slots,
    )
    _record_gate(
        gate_results,
        reasons,
        gate_id="coin_slots",
        status="PASS" if remaining_coin_slots > 0 else "FAIL",
        reason="MAX_COIN_POSITIONS_REACHED",
        configured=policy.max_positions_per_coin,
        calculated=remaining_coin_slots,
    )
    _record_gate(
        gate_results,
        reasons,
        gate_id="coin_allocation",
        status="PASS" if free_coin > 0 else "FAIL",
        reason="COIN_ALLOCATION_REACHED",
        configured=policy.coin_allocation_cap,
        calculated=canonical_decimal_text(qcapital_floor(free_coin).value),
    )
    if candidate is not None:
        minimum = parse_decimal_text(policy.minimum_tranche_capital)
        _record_gate(
            gate_results,
            reasons,
            gate_id="minimum_tranche_capital",
            status="PASS" if candidate > 0 and candidate >= minimum else "FAIL",
            reason="MINIMUM_TRANCHE_CAPITAL_NOT_MET",
            configured=policy.minimum_tranche_capital,
            calculated=canonical_decimal_text(candidate),
        )
        _record_gate(
            gate_results,
            reasons,
            gate_id="global_capital",
            status="PASS" if free_global >= candidate else "FAIL",
            reason="INSUFFICIENT_GLOBAL_CAPITAL_FOR_TRANCHE",
            configured=canonical_decimal_text(qcapital_floor(free_global).value),
            calculated=canonical_decimal_text(candidate),
        )
    else:
        gate_results["grant_candidate"] = _gate("UNAVAILABLE", "GRANT_CANDIDATE_UNAVAILABLE")

    if reasons:
        return _evaluation(
            grant_decision_id=grant_decision_id,
            status=PortfolioGrantStatus.BLOCKED,
            reasons=tuple(reasons),
            gate_results=gate_results,
            approved_decision=parsed_decision,
            capital_grant=None,
        )
    if candidate is None:
        return _evaluation(
            grant_decision_id=grant_decision_id,
            status=PortfolioGrantStatus.UNAVAILABLE,
            reasons=("GRANT_CANDIDATE_UNAVAILABLE",),
            gate_results=gate_results,
            approved_decision=parsed_decision,
            capital_grant=None,
        )

    try:
        grant = build_capital_and_limits_grant(
            capital_grant_id=capital_grant_id,
            approved_decision=parsed_decision.to_payload(),
            created_at=as_of,
            as_of=as_of,
            portfolio_state_revision=portfolio_state.revision,
            requested_capital_per_tranche=canonical_decimal_text(candidate),
            minimum_tranche_capital=policy.minimum_tranche_capital,
            remaining_coin_capital=canonical_decimal_text(qcapital_floor(free_coin).value),
            remaining_global_capital=canonical_decimal_text(qcapital_floor(free_global).value),
            remaining_coin_slots=remaining_coin_slots,
            remaining_global_slots=remaining_global_slots,
            relevant_portfolio_limits=policy.relevant_limits_payload(),
            accounting_policy=policy.accounting_policy_payload(),
            venue_facts=venue_facts,
        )
    except CapitalGrantError as exc:
        raise PortfolioGrantError(str(exc)) from exc
    return _evaluation(
        grant_decision_id=grant_decision_id,
        status=PortfolioGrantStatus.ALLOWED,
        reasons=("ALLOWED",),
        gate_results=gate_results,
        approved_decision=parsed_decision,
        capital_grant=grant,
    )


def validate_approved_initial_decision(payload: Mapping[str, Any]) -> TargetContract:
    try:
        parsed = validate_contract_edge(
            producer="Position",
            consumer="Portfolio",
            contract_type="APPROVE_REJECT",
            payload=payload,
            definition="APPROVE_REJECT.initial",
        )
    except (ContractError, ContractBindingError) as exc:
        raise PortfolioGrantError(str(exc)) from exc
    body = parsed.to_payload()["position_decision"]
    if body["decision"] != "APPROVE":
        raise PortfolioGrantError("Portfolio grants require APPROVE initial decisions")
    return parsed


def _evaluation(
    *,
    grant_decision_id: str,
    status: PortfolioGrantStatus,
    reasons: tuple[str, ...],
    gate_results: dict[str, dict[str, Any]],
    approved_decision: TargetContract,
    capital_grant: TargetContract | None,
) -> PortfolioGrantEvaluation:
    return PortfolioGrantEvaluation(
        grant_decision_id=_text(grant_decision_id, field="grant_decision_id"),
        status=status,
        primary_reason=reasons[0],
        evaluated_reasons=reasons,
        gate_results=gate_results,
        approved_decision=approved_decision,
        capital_grant=capital_grant,
    )


def _record_gate(
    gate_results: dict[str, dict[str, Any]],
    reasons: list[str],
    *,
    gate_id: str,
    status: str,
    reason: str,
    configured: Any = None,
    calculated: Any = None,
) -> None:
    gate_results[gate_id] = _gate(status, reason if status != "PASS" else "PASS", configured=configured, calculated=calculated)
    if status == "FAIL":
        reasons.append(reason)


def _gate(status: str, reason: str, *, configured: Any = None, calculated: Any = None) -> dict[str, Any]:
    return {"status": status, "reason": reason, "configured": configured, "calculated": calculated}


def _coin_state(state: PortfolioState, symbol: str) -> CoinPortfolioState | None:
    for coin in state.coins:
        if coin.symbol == symbol:
            return coin
    return None


def _bucket_commitment(payload: Mapping[str, Any]) -> Fraction:
    return (
        parse_decimal_text(str(payload["held_committed_capital"]))
        + parse_decimal_text(str(payload["reserved_committed_capital"]))
        + parse_decimal_text(str(payload["filled_committed_capital"]))
        + parse_decimal_text(str(payload["closing_retained_committed_capital"]))
    )


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PortfolioGrantError(f"{field} is required")
    return value


def _nonnegative_decimal(value: str, *, field: str) -> None:
    if parse_decimal_text(value) < 0:
        raise PortfolioGrantError(f"{field} must be nonnegative")


def _nonnegative_int(value: int, *, field: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise PortfolioGrantError(f"{field} must be a nonnegative integer")
