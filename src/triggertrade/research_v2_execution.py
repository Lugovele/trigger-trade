"""Canonical Research V2 execution-profile bridge.

This module is the versioned downstream contract extension for Research V2.
It does not form signals or run a backtest campaign. It maps an already
resolved Set/MARKET_HANDOFF plus V2 execution profile into portfolio checks,
risk-based sizing, and a lifecycle-consumable Order Spec v6.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import re
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.research_v2 import ResearchV2ExecutionProfile, ResearchV2JobConfig, build_research_v2_execution_profile


ORDER_SPEC_V2_CONTRACT_VERSION = 6
NUMERIC_POLICY_VERSION = "TT_NUMERIC_V1"


class ResearchV2ExecutionError(ValueError):
    """Raised when the Research V2 execution bridge cannot decide canonically."""


@dataclass(frozen=True)
class VenueConstraints:
    tick_size: Decimal
    qty_step: Decimal
    min_qty: Decimal
    min_notional: Decimal
    max_qty: Decimal | None = None


@dataclass(frozen=True)
class V2PortfolioExposureState:
    account_capital: Decimal
    committed_margin: Decimal = Decimal("0")
    coin_committed_margin: Decimal = Decimal("0")
    gross_notional: Decimal = Decimal("0")
    stop_risk: Decimal = Decimal("0")
    open_pending_count: int = 0
    coin_open_pending_count: int = 0


@dataclass(frozen=True)
class V2PortfolioGrant:
    status: str
    reason_code: str
    account_capital: Decimal
    free_margin: Decimal
    remaining_coin_margin: Decimal
    remaining_gross_notional: Decimal
    remaining_stop_risk: Decimal
    remaining_global_slots: int
    remaining_coin_slots: int
    profile_fingerprint: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "v2_portfolio_grant": {
                "contract_version": 1,
                "status": self.status,
                "reason_code": self.reason_code,
                "account_capital": _decimal_text(self.account_capital),
                "free_margin": _decimal_text(self.free_margin),
                "remaining_coin_margin": _decimal_text(self.remaining_coin_margin),
                "remaining_gross_notional": _decimal_text(self.remaining_gross_notional),
                "remaining_stop_risk": _decimal_text(self.remaining_stop_risk),
                "remaining_global_slots": self.remaining_global_slots,
                "remaining_coin_slots": self.remaining_coin_slots,
                "execution_profile_fingerprint": self.profile_fingerprint,
            }
        }


@dataclass(frozen=True)
class V2ConstructionResult:
    status: str
    reason_code: str
    order_spec: dict[str, Any] | None
    sizing: dict[str, Any]
    economics: dict[str, Any]


@dataclass(frozen=True)
class V2G0EligibilityResult:
    status: str
    reason_code: str
    evidence: dict[str, Any]


def build_research_v2_canonical_execution_profile(job: ResearchV2JobConfig) -> ResearchV2ExecutionProfile:
    return build_research_v2_execution_profile(job)


def evaluate_research_v2_portfolio_grant(
    *,
    profile: ResearchV2ExecutionProfile,
    state: V2PortfolioExposureState,
) -> V2PortfolioGrant:
    policy = profile.sizing_profile
    account = state.account_capital
    total_margin_cap = _decimal(policy["total_margin_fraction_max"]) * account
    coin_margin_cap = _decimal(policy["per_coin_margin_fraction_cap"]) * account
    gross_cap = _decimal(policy["gross_notional_fraction_max"]) * account
    stop_risk_cap = _decimal(policy["portfolio_open_and_pending_stop_risk_fraction_max"]) * account
    max_open_pending = int(policy["max_open_and_pending_orders"])
    max_coin = int(policy["max_positions_per_coin"])

    free_margin = total_margin_cap - state.committed_margin
    remaining_coin = coin_margin_cap - state.coin_committed_margin
    remaining_gross = gross_cap - state.gross_notional
    remaining_stop_risk = stop_risk_cap - state.stop_risk
    remaining_slots = max_open_pending - state.open_pending_count
    remaining_coin_slots = max_coin - state.coin_open_pending_count

    checks = (
        ("MAX_OPEN_PENDING_REACHED", remaining_slots <= 0),
        ("MAX_COIN_OPEN_PENDING_REACHED", remaining_coin_slots <= 0),
        ("TOTAL_MARGIN_CAP_REACHED", free_margin <= 0),
        ("PER_COIN_MARGIN_CAP_REACHED", remaining_coin <= 0),
        ("GROSS_NOTIONAL_CAP_REACHED", remaining_gross <= 0),
        ("TOTAL_STOP_RISK_CAP_REACHED", remaining_stop_risk <= 0),
    )
    for reason, failed in checks:
        if failed:
            return V2PortfolioGrant(
                status="BLOCK",
                reason_code=reason,
                account_capital=account,
                free_margin=max(free_margin, Decimal("0")),
                remaining_coin_margin=max(remaining_coin, Decimal("0")),
                remaining_gross_notional=max(remaining_gross, Decimal("0")),
                remaining_stop_risk=max(remaining_stop_risk, Decimal("0")),
                remaining_global_slots=max(remaining_slots, 0),
                remaining_coin_slots=max(remaining_coin_slots, 0),
                profile_fingerprint=profile.config_fingerprint,
            )
    return V2PortfolioGrant(
        status="ALLOW",
        reason_code="ALLOW",
        account_capital=account,
        free_margin=free_margin,
        remaining_coin_margin=remaining_coin,
        remaining_gross_notional=remaining_gross,
        remaining_stop_risk=remaining_stop_risk,
        remaining_global_slots=remaining_slots,
        remaining_coin_slots=remaining_coin_slots,
        profile_fingerprint=profile.config_fingerprint,
    )


def construct_research_v2_order_spec(
    *,
    order_spec_id: str,
    spec_created_at: str,
    market_handoff: Mapping[str, Any],
    profile: ResearchV2ExecutionProfile,
    portfolio_grant: V2PortfolioGrant,
    venue: VenueConstraints,
    reference_price: Decimal,
    atr15: Decimal,
    structural_reference_price: Decimal | None = None,
) -> V2ConstructionResult:
    if portfolio_grant.status != "ALLOW":
        return V2ConstructionResult("REJECT", portfolio_grant.reason_code, None, {}, {})
    handoff = dict(market_handoff["market_handoff"])
    direction = str(handoff["snapshot"]["direction"])
    entry = _entry_price(direction=direction, reference=reference_price, atr15=atr15, tick=venue.tick_size)
    stop = _stop_price(
        direction=direction,
        entry=entry,
        reference=reference_price,
        atr15=atr15,
        tick=venue.tick_size,
        stop_profile=profile.stop_profile,
        structural_reference_price=structural_reference_price,
    )
    if stop is None:
        return V2ConstructionResult("REJECT", "STOP_REFERENCE_UNAVAILABLE", None, {}, {})
    risk_distance = _risk_distance(direction, entry, stop)
    if risk_distance <= 0:
        return V2ConstructionResult("REJECT", "INVALID_STOP_GEOMETRY", None, {}, {})
    geometry_reason = _final_stop_geometry_rejection(
        direction=direction,
        entry=entry,
        stop=stop,
        atr15=atr15,
        stop_profile=profile.stop_profile,
    )
    if geometry_reason is not None:
        return V2ConstructionResult("REJECT", geometry_reason, None, {}, {})
    tp = _tp_price(direction=direction, entry=entry, risk_distance=risk_distance, tick=venue.tick_size)
    if (direction == "LONG" and not (stop < entry < tp)) or (direction == "SHORT" and not (tp < entry < stop)):
        return V2ConstructionResult("REJECT", "INVALID_FINAL_EXECUTABLE_GEOMETRY", None, {}, {})
    sizing = _risk_based_sizing(
        profile=profile,
        grant=portfolio_grant,
        venue=venue,
        entry=entry,
        stop_distance=risk_distance,
    )
    if sizing["status"] != "PASS":
        return V2ConstructionResult("REJECT", sizing["reason_code"], None, sizing, {})
    economics = _economics(profile=profile, entry=entry, stop=stop, tp=tp, quantity=_decimal(sizing["quantity"]))
    if economics["net_tp_floor_result"] != "PASS":
        return V2ConstructionResult("REJECT", "NET_TP_FLOOR_NOT_MET", None, sizing, economics)
    expires_at = _expires_at(spec_created_at, profile.entry_profile.get("TTL_minutes"))
    spec = {
        "order_spec": {
            "contract_version": ORDER_SPEC_V2_CONTRACT_VERSION,
            "order_spec_id": order_spec_id,
            "spec_created_at": spec_created_at,
            "capital_grant_id": f"v2-capital-grant-{canonical_json_digest(portfolio_grant.to_payload())[:24]}",
            "decision_cycle_id": handoff["decision_cycle_id"],
            "set_result_id": handoff["set_result_id"],
            "position_decision_id": f"v2-position-decision-{handoff['decision_cycle_id'].removeprefix('decision-cycle-')[:24]}",
            "construction_result_id": f"v2-construction-{order_spec_id}",
            "position_plan_id": f"v2-position-plan-{order_spec_id}",
            "tranche_id": f"v2-risk-position-{order_spec_id}",
            "symbol": handoff["symbol"],
            "physical_symbol": _physical_symbol_from_handoff(handoff),
            "direction": direction,
            "side": "BUY" if direction == "LONG" else "SELL",
            "entry": {
                "order_type": "LIMIT",
                "post_only": True,
                "price": _decimal_text(entry),
                "quantity": sizing["quantity"],
                "validity": {
                    "time_in_force": "GTC" if expires_at is None else "TTL",
                    "expires_at": expires_at,
                    "cancel_unfilled_on_expiry": expires_at is not None,
                    "chase": False,
                    "reprice": False,
                    "market_fallback": False,
                },
            },
            "leverage": str(profile.rules_profile["leverage"]),
            "take_profit": {
                "mode": "R_MULTIPLE",
                "r_multiple": "2",
                "price": _decimal_text(tp),
                "execution_type": "MARKET",
                "trigger_by": "LAST_PRICE",
                "scope": "FULL_POSITION",
            },
            "stop_loss": {
                "mode": str(profile.stop_profile["type"]),
                "price": _decimal_text(stop),
                "execution_type": "MARKET",
                "trigger_by": "LAST_PRICE",
                "scope": "FULL_POSITION",
            },
            "economics": {
                **economics,
                "target_order_notional": sizing["target_order_notional"],
                "actual_order_notional": sizing["actual_order_notional"],
                "actual_committed_margin": sizing["actual_committed_margin"],
                "actual_stop_risk": sizing["actual_stop_risk"],
                "execution_profile_fingerprint": profile.config_fingerprint,
            },
            "provenance": {
                "research_v2_execution_profile_id": profile.execution_profile_id,
                "research_v2_execution_profile_fingerprint": profile.config_fingerprint,
                "set_result_id": handoff["set_result_id"],
                "market_snapshot_at": handoff["snapshot"]["market_snapshot_at"],
            },
            "numeric_policy_version": NUMERIC_POLICY_VERSION,
        }
    }
    validate_research_v2_order_spec(spec)
    return V2ConstructionResult("CONSTRUCTED", "CONSTRUCTED", spec, sizing, economics)


def evaluate_research_v2_g0_structural_eligibility(
    *,
    direction: str,
    stop_profile: Mapping[str, Any],
    venue: VenueConstraints,
    reference_price: Decimal,
    atr15: Decimal,
    structural_reference_price: Decimal | None,
) -> V2G0EligibilityResult:
    """Pure G0 geometry eligibility check; it creates no order/account effects."""

    evidence: dict[str, Any] = {
        "eligibility_mode": "G0_STRUCTURAL_ONLY",
        "operative_stop_family": "G1_ATR_ONLY",
        "direction": direction,
        "reference_price": _decimal_text(reference_price),
        "atr15": _decimal_text(atr15),
        "structural_reference_price": None if structural_reference_price is None else _decimal_text(structural_reference_price),
        "tick_size": _decimal_text(venue.tick_size),
    }
    if stop_profile.get("type") != "HYBRID_STRUCTURAL":
        return V2G0EligibilityResult("REJECT", "G0_PROFILE_REQUIRED", evidence)
    entry = _entry_price(direction=direction, reference=reference_price, atr15=atr15, tick=venue.tick_size)
    evidence["g0_entry_price_for_eligibility"] = _decimal_text(entry)
    try:
        stop = _stop_price(
            direction=direction,
            entry=entry,
            reference=reference_price,
            atr15=atr15,
            tick=venue.tick_size,
            stop_profile=stop_profile,
            structural_reference_price=structural_reference_price,
        )
    except ResearchV2ExecutionError as exc:
        return V2G0EligibilityResult("REJECT", str(exc), evidence)
    if stop is None:
        return V2G0EligibilityResult("REJECT", "STOP_REFERENCE_UNAVAILABLE", evidence)
    evidence["g0_stop_price_for_eligibility"] = _decimal_text(stop)
    evidence["g0_structural_distance"] = _decimal_text(_risk_distance(direction, entry, stop))
    rejection = _final_stop_geometry_rejection(
        direction=direction,
        entry=entry,
        stop=stop,
        atr15=atr15,
        stop_profile=stop_profile,
    )
    if rejection is not None:
        return V2G0EligibilityResult("REJECT", rejection, evidence)
    return V2G0EligibilityResult("PASS", "PASS", evidence)


def validate_research_v2_order_spec(order_spec: Mapping[str, Any]) -> dict[str, Any]:
    spec = dict(order_spec.get("order_spec") or {})
    required = {
        "contract_version",
        "order_spec_id",
        "spec_created_at",
        "decision_cycle_id",
        "set_result_id",
        "symbol",
        "direction",
        "side",
        "entry",
        "leverage",
        "take_profit",
        "stop_loss",
        "economics",
        "provenance",
        "numeric_policy_version",
    }
    missing = required - set(spec)
    if missing:
        raise ResearchV2ExecutionError(f"ORDER_SPEC_V6 missing required fields: {', '.join(sorted(missing))}")
    if spec["contract_version"] != ORDER_SPEC_V2_CONTRACT_VERSION:
        raise ResearchV2ExecutionError("ORDER_SPEC_V6 contract_version must be 6")
    validity = spec["entry"].get("validity")
    if not isinstance(validity, Mapping):
        raise ResearchV2ExecutionError("ORDER_SPEC_V6 entry.validity is required")
    if validity.get("time_in_force") not in {"GTC", "TTL"}:
        raise ResearchV2ExecutionError("ORDER_SPEC_V6 entry.validity.time_in_force is invalid")
    if validity.get("time_in_force") == "TTL" and not validity.get("expires_at"):
        raise ResearchV2ExecutionError("ORDER_SPEC_V6 TTL requires expires_at")
    if validity.get("chase") or validity.get("reprice") or validity.get("market_fallback"):
        raise ResearchV2ExecutionError("ORDER_SPEC_V6 forbids chase/reprice/market fallback")
    return {"order_spec": spec}


def research_v2_order_validity_status(order_spec: Mapping[str, Any], *, as_of: str, filled_quantity: Decimal) -> str:
    spec = validate_research_v2_order_spec(order_spec)["order_spec"]
    validity = spec["entry"]["validity"]
    if validity["time_in_force"] == "GTC":
        return "ACTIVE"
    expires_at = validity["expires_at"]
    if _parse_time(as_of) < _parse_time(str(expires_at)):
        return "ACTIVE"
    if filled_quantity <= 0:
        return "EXPIRED_CANCEL_UNFILLED"
    return "EXPIRED_KEEP_FILLED_PROTECTION"


def _risk_based_sizing(
    *,
    profile: ResearchV2ExecutionProfile,
    grant: V2PortfolioGrant,
    venue: VenueConstraints,
    entry: Decimal,
    stop_distance: Decimal,
) -> dict[str, Any]:
    policy = profile.sizing_profile
    account = grant.account_capital
    leverage = _decimal(profile.rules_profile["leverage"])
    stress_cost = _decimal(profile.cost_profile["stress_total_approx_fraction"])
    stop_fraction = stop_distance / entry
    denominator = stop_fraction + stress_cost
    if denominator <= 0:
        return {"status": "REJECT", "reason_code": "INVALID_RISK_DENOMINATOR"}
    candidates = {
        "nominal_margin": account * _decimal(policy["nominal_margin_fraction"]) * leverage,
        "per_trade_risk": account * _decimal(policy["risk_per_trade_fraction_max"]) / denominator,
        "free_margin": grant.free_margin * leverage,
        "coin_cap": grant.remaining_coin_margin * leverage,
        "gross_exposure": grant.remaining_gross_notional,
        "portfolio_stop_risk": grant.remaining_stop_risk / denominator,
    }
    target_notional = min(candidates.values())
    binding = min(candidates, key=lambda key: candidates[key])
    quantity = _floor_to_step(target_notional / entry, venue.qty_step)
    if quantity < venue.min_qty:
        return {"status": "REJECT", "reason_code": "QTY_BELOW_MINIMUM", "binding_constraint": binding}
    if venue.max_qty is not None and quantity > venue.max_qty:
        quantity = _floor_to_step(venue.max_qty, venue.qty_step)
    actual_notional = quantity * entry
    if actual_notional < venue.min_notional:
        return {"status": "REJECT", "reason_code": "NOTIONAL_BELOW_MINIMUM", "binding_constraint": binding}
    actual_margin = actual_notional / leverage
    actual_stop_risk = actual_notional * denominator
    min_tranche = _decimal(policy["minimum_tranche_usdt"])
    if actual_margin < min_tranche:
        return {"status": "REJECT", "reason_code": "MINIMUM_TRANCHE_NOT_MET", "binding_constraint": binding}
    violations = (
        ("TOTAL_MARGIN_CAP_AFTER_ROUNDING", actual_margin > grant.free_margin),
        ("PER_COIN_MARGIN_CAP_AFTER_ROUNDING", actual_margin > grant.remaining_coin_margin),
        ("GROSS_NOTIONAL_CAP_AFTER_ROUNDING", actual_notional > grant.remaining_gross_notional),
        ("TOTAL_STOP_RISK_CAP_AFTER_ROUNDING", actual_stop_risk > grant.remaining_stop_risk),
        ("PER_TRADE_RISK_CAP_AFTER_ROUNDING", actual_stop_risk > account * _decimal(policy["risk_per_trade_fraction_max"])),
    )
    for reason, failed in violations:
        if failed:
            return {"status": "REJECT", "reason_code": reason, "binding_constraint": binding}
    return {
        "status": "PASS",
        "reason_code": "PASS",
        "binding_constraint": binding,
        "target_order_notional": _decimal_text(target_notional),
        "quantity": _decimal_text(quantity),
        "actual_order_notional": _decimal_text(actual_notional),
        "actual_committed_margin": _decimal_text(actual_margin),
        "actual_stop_risk": _decimal_text(actual_stop_risk),
        "stop_fraction": _decimal_text(stop_fraction),
    }

def _economics(
    *,
    profile: ResearchV2ExecutionProfile,
    entry: Decimal,
    stop: Decimal,
    tp: Decimal,
    quantity: Decimal,
) -> dict[str, str]:
    direction_sign = Decimal("1") if tp > entry else Decimal("-1")
    risk = abs(entry - stop)
    reward = abs(tp - entry)
    notional = entry * quantity
    gross_tp = reward * quantity
    maker = _decimal(profile.cost_profile["maker_entry_fraction"])
    taker = _decimal(profile.cost_profile["taker_exit_fraction"])
    entry_fee = notional * maker
    exit_fee = (tp * quantity) * taker
    net_tp = gross_tp - entry_fee - exit_fee
    net_fraction = net_tp / notional
    floor = _decimal(profile.take_profit_profile["net_TP_fraction_of_notional_min"])
    return {
        "risk_distance": _decimal_text(risk),
        "reward_distance": _decimal_text(reward),
        "gross_r": _decimal_text(reward / risk),
        "planned_conditional_net_tp": _decimal_text(net_tp),
        "planned_conditional_net_tp_fraction": _decimal_text(net_fraction),
        "net_tp_floor": _decimal_text(floor),
        "net_tp_floor_result": "PASS" if net_fraction >= floor else "FAIL",
        "maker_fee_rate": _decimal_text(maker),
        "taker_fee_rate": _decimal_text(taker),
        "direction_sign": _decimal_text(direction_sign),
    }


def _entry_price(*, direction: str, reference: Decimal, atr15: Decimal, tick: Decimal) -> Decimal:
    raw = reference - Decimal("0.10") * atr15 if direction == "LONG" else reference + Decimal("0.10") * atr15
    return _floor_to_step(raw, tick) if direction == "LONG" else _ceil_to_step(raw, tick)


def _stop_price(
    *,
    direction: str,
    entry: Decimal,
    reference: Decimal,
    atr15: Decimal,
    tick: Decimal,
    stop_profile: Mapping[str, Any],
    structural_reference_price: Decimal | None,
) -> Decimal | None:
    if stop_profile["type"] == "ATR_ONLY":
        raw_distance = atr15 * _decimal(stop_profile["distance_ATR15"])
        distance = min(
            max(raw_distance, entry * _decimal(stop_profile["distance_fraction_floor"])),
            entry * _decimal(stop_profile["distance_fraction_ceiling"]),
        )
        raw = entry - distance if direction == "LONG" else entry + distance
        return _floor_to_step(raw, tick) if direction == "LONG" else _ceil_to_step(raw, tick)
    if structural_reference_price is None:
        return None
    if direction == "LONG" and structural_reference_price >= entry:
        raise ResearchV2ExecutionError("G0_STRUCTURAL_REFERENCE_NOT_PROTECTIVE")
    if direction == "SHORT" and structural_reference_price <= entry:
        raise ResearchV2ExecutionError("G0_STRUCTURAL_REFERENCE_NOT_PROTECTIVE")
    buffer = _decimal(stop_profile["buffer_ATR15"]) * atr15
    raw = structural_reference_price - buffer if direction == "LONG" else structural_reference_price + buffer
    distance = _risk_distance(direction, entry, raw)
    if distance <= 0:
        raise ResearchV2ExecutionError("G0_STRUCTURAL_REFERENCE_NOT_PROTECTIVE")
    min_distance = max(atr15 * _decimal(stop_profile["minimum_distance_ATR15"]), entry * _decimal(stop_profile["minimum_distance_fraction"]))
    max_distance = min(atr15 * _decimal(stop_profile["maximum_distance_ATR15"]), entry * _decimal(stop_profile["maximum_distance_fraction"]))
    if distance > max_distance:
        raise ResearchV2ExecutionError("G0_STRUCTURAL_STOP_BEYOND_MAXIMUM")
    distance = max(distance, min_distance)
    raw = entry - distance if direction == "LONG" else entry + distance
    return _floor_to_step(raw, tick) if direction == "LONG" else _ceil_to_step(raw, tick)


def _tp_price(*, direction: str, entry: Decimal, risk_distance: Decimal, tick: Decimal) -> Decimal:
    raw = entry + Decimal("2") * risk_distance if direction == "LONG" else entry - Decimal("2") * risk_distance
    return _ceil_to_step(raw, tick) if direction == "LONG" else _floor_to_step(raw, tick)


def _risk_distance(direction: str, entry: Decimal, stop: Decimal) -> Decimal:
    return entry - stop if direction == "LONG" else stop - entry


def _final_stop_geometry_rejection(
    *,
    direction: str,
    entry: Decimal,
    stop: Decimal,
    atr15: Decimal,
    stop_profile: Mapping[str, Any],
) -> str | None:
    distance = _risk_distance(direction, entry, stop)
    if distance <= 0:
        return "INVALID_FINAL_EXECUTABLE_GEOMETRY"
    if stop_profile["type"] == "ATR_ONLY":
        min_distance = entry * _decimal(stop_profile["distance_fraction_floor"])
        max_distance = entry * _decimal(stop_profile["distance_fraction_ceiling"])
    else:
        min_distance = max(
            atr15 * _decimal(stop_profile["minimum_distance_ATR15"]),
            entry * _decimal(stop_profile["minimum_distance_fraction"]),
        )
        max_distance = min(
            atr15 * _decimal(stop_profile["maximum_distance_ATR15"]),
            entry * _decimal(stop_profile["maximum_distance_fraction"]),
        )
    if distance < min_distance:
        return "FINAL_STOP_DISTANCE_BELOW_MINIMUM"
    if distance > max_distance:
        return "FINAL_STOP_DISTANCE_EXCEEDS_MAXIMUM"
    return None


def _expires_at(spec_created_at: str, ttl_minutes: object) -> str | None:
    if ttl_minutes is None:
        return None
    return (_parse_time(spec_created_at) + timedelta(minutes=int(ttl_minutes))).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _decimal_text(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == 0:
        return "0"
    return format(normalized, "f")


def _physical_symbol_from_handoff(handoff: Mapping[str, Any]) -> str:
    body = handoff.get("market_handoff") if isinstance(handoff.get("market_handoff"), Mapping) else handoff
    for key in ("physical_symbol", "execution_symbol", "instrument_symbol"):
        candidate = body.get(key)
        if candidate:
            return str(candidate).upper()
    instrument = body.get("instrument") if isinstance(body.get("instrument"), Mapping) else {}
    snapshot = body.get("snapshot") if isinstance(body.get("snapshot"), Mapping) else {}
    for source in (
        instrument.get("physical_symbol"),
        instrument.get("execution_symbol"),
        instrument.get("symbol"),
        instrument.get("metadata_revision"),
        snapshot.get("metadata_revision"),
    ):
        parsed = _symbol_from_metadata_text(source)
        if parsed:
            return parsed
    return str(body.get("symbol") or snapshot.get("symbol") or "").upper()


def _symbol_from_metadata_text(value: Any) -> str | None:
    if not value:
        return None
    matches = re.findall(r"\b[A-Z0-9]+USDT\b", str(value).upper())
    if matches:
        return matches[-1]
    return None


def _floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).to_integral_value(rounding=ROUND_FLOOR) * step


def _ceil_to_step(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).to_integral_value(rounding=ROUND_CEILING) * step
