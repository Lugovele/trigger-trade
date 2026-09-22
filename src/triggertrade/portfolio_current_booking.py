"""Portfolio current hold and submit-authorization gate for v1.2.15 B8C."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

from triggertrade.contracts import ContractError, TargetContract, parse_contract
from triggertrade.portfolio_state import PortfolioHealth, PortfolioState
from triggertrade.submit_authorizations import SubmitAuthorizationError, build_submit_authorized


class PortfolioCurrentBookingError(ValueError):
    """Raised when Portfolio cannot book a current hold deterministically."""


class PortfolioCurrentBookingStatus(StrEnum):
    AUTHORIZED = "AUTHORIZED"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class PortfolioCurrentBookingPolicy:
    global_position_cap: str
    coin_allocation_cap: str
    max_open_positions: int
    max_positions_per_coin: int
    portfolio_config_id: str
    portfolio_config_version: str
    portfolio_config_digest: str
    pinned_cooldown_duration_seconds: int
    daily_loss_blocked: bool = False
    cooldown_status: str = "PASS"
    incident_frontier_clear: bool = True

    def __post_init__(self) -> None:
        _nonnegative_decimal(self.global_position_cap, field="global_position_cap")
        _nonnegative_decimal(self.coin_allocation_cap, field="coin_allocation_cap")
        _nonnegative_int(self.max_open_positions, field="max_open_positions")
        _nonnegative_int(self.max_positions_per_coin, field="max_positions_per_coin")
        _text(self.portfolio_config_id, field="portfolio_config_id")
        _text(self.portfolio_config_version, field="portfolio_config_version")
        _text(self.portfolio_config_digest, field="portfolio_config_digest")
        _nonnegative_int(self.pinned_cooldown_duration_seconds, field="pinned_cooldown_duration_seconds")
        if not isinstance(self.daily_loss_blocked, bool):
            raise PortfolioCurrentBookingError("daily_loss_blocked must be boolean")
        if self.cooldown_status not in {"PASS", "BLOCKED", "UNAVAILABLE"}:
            raise PortfolioCurrentBookingError("cooldown_status must be PASS, BLOCKED, or UNAVAILABLE")
        if not isinstance(self.incident_frontier_clear, bool):
            raise PortfolioCurrentBookingError("incident_frontier_clear must be boolean")


@dataclass(frozen=True)
class PortfolioCurrentBookingEvaluation:
    booking_id: str
    authorization_id: str
    status: PortfolioCurrentBookingStatus
    primary_reason: str
    evaluated_reasons: tuple[str, ...]
    gate_results: dict[str, dict[str, Any]]
    capital_grant: TargetContract
    construction_result: TargetContract
    submit_authorized: TargetContract | None

    def to_payload(self) -> dict[str, Any]:
        return {
            "portfolio_current_booking": {
                "state_version": 1,
                "booking_id": self.booking_id,
                "authorization_id": self.authorization_id,
                "status": self.status.value,
                "primary_reason": self.primary_reason,
                "evaluated_reasons": list(self.evaluated_reasons),
                "gate_results": self.gate_results,
                "capital_grant": self.capital_grant.to_payload(),
                "construction_result": self.construction_result.to_payload(),
                "submit_authorized": None if self.submit_authorized is None else self.submit_authorized.to_payload(),
            }
        }


def evaluate_current_portfolio_booking(
    *,
    booking_id: str,
    authorization_id: str,
    capital_grant: Mapping[str, Any],
    construction_result: Mapping[str, Any],
    portfolio_state: PortfolioState,
    policy: PortfolioCurrentBookingPolicy,
    authorized_at: str,
) -> PortfolioCurrentBookingEvaluation:
    """Evaluate B8C current gates and build Submit Authorized only on success."""

    booking_id = _text(booking_id, field="booking_id")
    authorization_id = _text(authorization_id, field="authorization_id")
    authorized_at = _text(authorized_at, field="authorized_at")
    grant_contract = _capital_grant(capital_grant)
    construction_contract = _constructed_result(construction_result)
    grant = grant_contract.to_payload()["capital_and_limits"]
    construction = construction_contract.to_payload()["position_construction_result"]
    _validate_identity(grant=grant, construction=construction)

    held_capital = str(construction["approved_economics"]["approved_actual_committed_capital"])
    symbol = str(grant["symbol"]).upper()
    gate_results: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []

    _state_gate(portfolio_state, gate_results=gate_results, reasons=reasons)
    _capital_gates(
        portfolio_state,
        symbol=symbol,
        held_capital=held_capital,
        policy=policy,
        gate_results=gate_results,
        reasons=reasons,
    )
    _boolean_gate(
        name="daily_loss",
        blocked=policy.daily_loss_blocked,
        reason="DAILY_LOSS_BLOCKED",
        gate_results=gate_results,
        reasons=reasons,
    )
    if policy.cooldown_status != "PASS":
        gate_results["cooldown"] = {"status": policy.cooldown_status, "reason": "COOLDOWN_ACTIVE"}
        reasons.append("COOLDOWN_ACTIVE" if policy.cooldown_status == "BLOCKED" else "COOLDOWN_UNAVAILABLE")
    else:
        gate_results["cooldown"] = {"status": "PASS", "reason": None}
    _boolean_gate(
        name="incident_frontier",
        blocked=not policy.incident_frontier_clear,
        reason="INCIDENT_FRONTIER_BLOCKED",
        gate_results=gate_results,
        reasons=reasons,
    )

    if reasons:
        status = PortfolioCurrentBookingStatus.UNAVAILABLE if "PORTFOLIO_STATE_UNAVAILABLE" in reasons or "COOLDOWN_UNAVAILABLE" in reasons else PortfolioCurrentBookingStatus.BLOCKED
        return PortfolioCurrentBookingEvaluation(
            booking_id=booking_id,
            authorization_id=authorization_id,
            status=status,
            primary_reason=reasons[0],
            evaluated_reasons=tuple(reasons),
            gate_results=gate_results,
            capital_grant=grant_contract,
            construction_result=construction_contract,
            submit_authorized=None,
        )

    try:
        submit_authorized = build_submit_authorized(
            authorization_id=authorization_id,
            capital_grant=grant_contract.to_payload(),
            construction_result=construction_contract.to_payload(),
            authorized_at=authorized_at,
        )
    except SubmitAuthorizationError as exc:
        raise PortfolioCurrentBookingError(str(exc)) from exc

    return PortfolioCurrentBookingEvaluation(
        booking_id=booking_id,
        authorization_id=authorization_id,
        status=PortfolioCurrentBookingStatus.AUTHORIZED,
        primary_reason="AUTHORIZED",
        evaluated_reasons=("AUTHORIZED",),
        gate_results=gate_results,
        capital_grant=grant_contract,
        construction_result=construction_contract,
        submit_authorized=submit_authorized,
    )


def _capital_grant(payload: Mapping[str, Any]) -> TargetContract:
    try:
        return parse_contract("CAPITAL_AND_LIMITS", payload)
    except ContractError as exc:
        raise PortfolioCurrentBookingError(str(exc)) from exc


def _constructed_result(payload: Mapping[str, Any]) -> TargetContract:
    try:
        return parse_contract("APPROVE_REJECT", payload, definition="APPROVE_REJECT.constructed")
    except ContractError as exc:
        raise PortfolioCurrentBookingError(str(exc)) from exc


def _validate_identity(*, grant: Mapping[str, Any], construction: Mapping[str, Any]) -> None:
    for field in ("capital_grant_id", "position_decision_id", "decision_cycle_id", "set_result_id", "symbol"):
        if grant[field] != construction[field]:
            raise PortfolioCurrentBookingError(f"construction result {field} must match capital grant")
    if construction["outcome"] != "CONSTRUCTED":
        raise PortfolioCurrentBookingError("current booking requires CONSTRUCTED outcome")


def _state_gate(state: PortfolioState, *, gate_results: dict[str, dict[str, Any]], reasons: list[str]) -> None:
    if state.health is not PortfolioHealth.LIVE:
        gate_results["portfolio_state"] = {"status": "UNAVAILABLE", "health": state.health.value}
        reasons.append("PORTFOLIO_STATE_UNAVAILABLE")
        return
    gate_results["portfolio_state"] = {"status": "PASS", "health": state.health.value}


def _capital_gates(
    state: PortfolioState,
    *,
    symbol: str,
    held_capital: str,
    policy: PortfolioCurrentBookingPolicy,
    gate_results: dict[str, dict[str, Any]],
    reasons: list[str],
) -> None:
    held = _decimal(held_capital, field="held_committed_capital")
    global_held = _decimal(state.global_buckets.held_committed_capital, field="global_held")
    global_after = global_held + held
    global_cap = _decimal(policy.global_position_cap, field="global_position_cap")
    if global_after > global_cap:
        gate_results["global_capital"] = {
            "status": "BLOCKED",
            "configured": policy.global_position_cap,
            "current": state.global_buckets.held_committed_capital,
            "held_committed_capital": _decimal_text(held),
            "after": _decimal_text(global_after),
        }
        reasons.append("GLOBAL_CAPITAL_EXCEEDED")
    else:
        gate_results["global_capital"] = {
            "status": "PASS",
            "configured": policy.global_position_cap,
            "current": state.global_buckets.held_committed_capital,
            "held_committed_capital": _decimal_text(held),
            "after": _decimal_text(global_after),
        }

    coin = next((coin for coin in state.coins if coin.symbol == symbol), None)
    if coin is None:
        gate_results["coin_state"] = {"status": "UNAVAILABLE", "symbol": symbol}
        reasons.append("COIN_STATE_UNAVAILABLE")
        coin_held = Decimal("0")
        coin_tranches = 0
    else:
        gate_results["coin_state"] = {"status": "PASS", "symbol": symbol}
        coin_held = _decimal(coin.buckets.held_committed_capital, field="coin_held")
        coin_tranches = coin.buckets.committed_tranches

    coin_after = coin_held + held
    coin_cap = _decimal(policy.coin_allocation_cap, field="coin_allocation_cap")
    if coin_after > coin_cap:
        gate_results["coin_capital"] = {
            "status": "BLOCKED",
            "configured": policy.coin_allocation_cap,
            "current": _decimal_text(coin_held),
            "held_committed_capital": _decimal_text(held),
            "after": _decimal_text(coin_after),
        }
        reasons.append("COIN_CAPITAL_EXCEEDED")
    else:
        gate_results["coin_capital"] = {
            "status": "PASS",
            "configured": policy.coin_allocation_cap,
            "current": _decimal_text(coin_held),
            "held_committed_capital": _decimal_text(held),
            "after": _decimal_text(coin_after),
        }

    if state.global_buckets.committed_tranches + 1 > policy.max_open_positions:
        gate_results["global_slots"] = {
            "status": "BLOCKED",
            "configured": policy.max_open_positions,
            "current": state.global_buckets.committed_tranches,
            "after": state.global_buckets.committed_tranches + 1,
        }
        reasons.append("GLOBAL_SLOT_LIMIT_EXCEEDED")
    else:
        gate_results["global_slots"] = {
            "status": "PASS",
            "configured": policy.max_open_positions,
            "current": state.global_buckets.committed_tranches,
            "after": state.global_buckets.committed_tranches + 1,
        }

    if coin_tranches + 1 > policy.max_positions_per_coin:
        gate_results["coin_slots"] = {
            "status": "BLOCKED",
            "configured": policy.max_positions_per_coin,
            "current": coin_tranches,
            "after": coin_tranches + 1,
        }
        reasons.append("COIN_SLOT_LIMIT_EXCEEDED")
    else:
        gate_results["coin_slots"] = {
            "status": "PASS",
            "configured": policy.max_positions_per_coin,
            "current": coin_tranches,
            "after": coin_tranches + 1,
        }


def _boolean_gate(
    *,
    name: str,
    blocked: bool,
    reason: str,
    gate_results: dict[str, dict[str, Any]],
    reasons: list[str],
) -> None:
    if blocked:
        gate_results[name] = {"status": "BLOCKED", "reason": reason}
        reasons.append(reason)
    else:
        gate_results[name] = {"status": "PASS", "reason": None}


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PortfolioCurrentBookingError(f"{field} is required")
    return value


def _nonnegative_int(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise PortfolioCurrentBookingError(f"{field} must be a nonnegative integer")
    return value


def _nonnegative_decimal(value: str, *, field: str) -> Decimal:
    resolved = _decimal(value, field=field)
    if resolved < 0:
        raise PortfolioCurrentBookingError(f"{field} must be nonnegative")
    return resolved


def _decimal(value: str, *, field: str) -> Decimal:
    if not isinstance(value, str) or not value:
        raise PortfolioCurrentBookingError(f"{field} must be an exact decimal string")
    try:
        resolved = Decimal(value)
    except InvalidOperation as exc:
        raise PortfolioCurrentBookingError(f"{field} must be an exact decimal string") from exc
    if not resolved.is_finite():
        raise PortfolioCurrentBookingError(f"{field} must be finite")
    return resolved


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f") if value != 0 else "0"
