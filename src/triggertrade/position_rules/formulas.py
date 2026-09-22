"""Certified initial Position opportunity calculations for v1.2.15 B7A.

This module is Position-owned. It consumes an already-frozen Market Handoff and
an immutable Position configuration version, then returns retained calculation
evidence for the initial opportunity stage only. It does not issue grants,
construct positions, create order specs, or call any API/execution surface.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Any

from triggertrade.contracts import ContractError
from triggertrade.contracts.bindings import ContractBindingError, validate_contract_edge
from triggertrade.numeric_policy import (
    NumericPolicyError,
    RoundingMode,
    canonical_decimal_text,
    exact_divide,
    parse_decimal_text,
    quantize,
)
from triggertrade.rules.trading import TakeProfitMode, TradingRulesVersion


ENTRY_MIN_ATR_DISTANCE = Fraction(1, 10)
ENTRY_MAX_ATR_DISTANCE = Fraction(5, 4)
TAKE_MIN_ATR_DISTANCE = Fraction(3, 4)
TAKE_MAX_ATR_DISTANCE = Fraction(4, 1)
STOP_BUFFER_ATR = Fraction(1, 5)
STOP_MIN_DISTANCE_ATR = Fraction(1, 2)
STOP_MAX_DISTANCE_ATR = Fraction(2, 1)


class PositionOpportunityError(ValueError):
    """Raised when an initial opportunity cannot be evaluated safely."""


class PositionResultStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ReferenceLevel:
    level_id: str
    level_type: str
    price: Fraction
    price_text: str
    timeframe: str
    available_at: str
    relative_position: str
    payload: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ReferenceLevel":
        try:
            price_text = _text(payload["price"], field="level.price")
            return cls(
                level_id=_text(payload["level_id"], field="level.level_id"),
                level_type=_text(payload["level_type"], field="level.level_type"),
                price=parse_decimal_text(price_text),
                price_text=price_text,
                timeframe=_text(payload["timeframe"], field="level.timeframe"),
                available_at=_text(payload["available_at"], field="level.available_at"),
                relative_position=_text(payload["relative_position"], field="level.relative_position"),
                payload=dict(payload),
            )
        except (KeyError, NumericPolicyError) as exc:
            raise PositionOpportunityError(f"invalid reference level: {exc}") from exc


@dataclass(frozen=True)
class PositionPriceResult:
    formula_id: str
    status: PositionResultStatus
    reason_code: str
    price: Fraction | None = None
    raw_price: Fraction | None = None
    reference: ReferenceLevel | None = None
    distance_atr: Fraction | None = None
    traversal: tuple[dict[str, Any], ...] = ()

    @property
    def usable(self) -> bool:
        return self.status is PositionResultStatus.AVAILABLE and self.price is not None

    def to_payload(self) -> dict[str, Any]:
        return {
            "formula_id": self.formula_id,
            "status": self.status.value,
            "reason_code": self.reason_code,
            "price": None if self.price is None else canonical_decimal_text(self.price),
            "raw_price": None if self.raw_price is None else canonical_decimal_text(self.raw_price),
            "reference_level_id": None if self.reference is None else self.reference.level_id,
            "reference_level_type": None if self.reference is None else self.reference.level_type,
            "reference_timeframe": None if self.reference is None else self.reference.timeframe,
            "distance_atr": None if self.distance_atr is None else canonical_decimal_text(self.distance_atr),
            "traversal": [dict(item) for item in self.traversal],
        }


@dataclass(frozen=True)
class PositionOpportunityEvaluation:
    position_decision_id: str
    decision_cycle_id: str
    set_result_id: str
    symbol: str
    direction: str
    decision: str
    reason_code: str
    opportunity_checks: dict[str, str]
    entry: PositionPriceResult
    stop: PositionPriceResult
    take_profit: PositionPriceResult
    gross_risk_reward: Fraction | None
    report: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "position_opportunity": {
                "position_decision_id": self.position_decision_id,
                "decision_cycle_id": self.decision_cycle_id,
                "set_result_id": self.set_result_id,
                "symbol": self.symbol,
                "direction": self.direction,
                "decision": self.decision,
                "reason_code": self.reason_code,
                "opportunity_checks": dict(self.opportunity_checks),
                "entry": self.entry.to_payload(),
                "stop": self.stop.to_payload(),
                "take_profit": self.take_profit.to_payload(),
                "gross_risk_reward": None
                if self.gross_risk_reward is None
                else canonical_decimal_text(self.gross_risk_reward),
                "report": dict(self.report),
            }
        }


def evaluate_initial_position_opportunity(
    *,
    position_decision_id: str,
    market_handoff: Mapping[str, Any],
    rules_version: TradingRulesVersion,
) -> PositionOpportunityEvaluation:
    """Evaluate initial Entry/Stop/TP feasibility from frozen inputs."""

    handoff = _handoff_body(market_handoff)
    direction = _text(handoff["snapshot"]["direction"], field="snapshot.direction")
    symbol = _text(handoff["symbol"], field="symbol").upper()
    tick = _positive_decimal(handoff["instrument"]["tick_size"], field="instrument.tick_size")
    atr = _positive_decimal(handoff["volatility"]["atr_15m"], field="volatility.atr_15m")
    matched_at = _text(handoff["snapshot"]["matched_at"], field="snapshot.matched_at")
    reference_price = _positive_decimal(
        handoff["snapshot"]["set_match_reference_price"],
        field="snapshot.set_match_reference_price",
    )
    levels = _available_levels(handoff["reference_geometry"]["levels"], matched_at=matched_at)

    configuration_status = "PASS"
    direction_status = "PASS" if direction in {"LONG", "SHORT"} else "FAIL"
    market_context = "PASS" if levels else "UNAVAILABLE"

    entry = _dynamic_entry(direction=direction, reference_price=reference_price, atr=atr, tick=tick, levels=levels)
    stop = _stop_result(direction=direction, entry=entry, atr=atr, tick=tick, levels=levels, rules_version=rules_version)
    take_profit = _take_profit_result(direction=direction, entry=entry, atr=atr, tick=tick, levels=levels, rules_version=rules_version)

    price_geometry = _price_geometry(direction=direction, entry=entry, stop=stop, take_profit=take_profit)
    gross_rr = _gross_risk_reward(direction=direction, entry=entry, stop=stop, take_profit=take_profit)
    minimum_rr = _minimum_rr_status(gross_rr, rules_version=rules_version)

    checks = {
        "configuration": configuration_status,
        "set_direction": direction_status,
        "market_context": market_context,
        "price_geometry": price_geometry,
        "minimum_rr": minimum_rr,
    }
    decision = "APPROVE" if all(value == "PASS" for value in checks.values()) else "REJECT"
    reason = "APPROVED" if decision == "APPROVE" else _first_reject_reason(checks, entry=entry, stop=stop, take_profit=take_profit)
    return PositionOpportunityEvaluation(
        position_decision_id=_text(position_decision_id, field="position_decision_id"),
        decision_cycle_id=_text(handoff["decision_cycle_id"], field="decision_cycle_id"),
        set_result_id=_text(handoff["set_result_id"], field="set_result_id"),
        symbol=symbol,
        direction=direction,
        decision=decision,
        reason_code=reason,
        opportunity_checks=checks,
        entry=entry,
        stop=stop,
        take_profit=take_profit,
        gross_risk_reward=gross_rr,
        report={
            "market_handoff_reference": {
                "matched_at": matched_at,
                "market_snapshot_at": handoff["snapshot"]["market_snapshot_at"],
                "market_snapshot_id": handoff["snapshot"]["market_snapshot_id"],
                "metadata_revision": handoff["instrument"]["metadata_revision"],
                "set_match_reference_price": handoff["snapshot"]["set_match_reference_price"],
                "atr_15m": handoff["volatility"]["atr_15m"],
                "tick_size": handoff["instrument"]["tick_size"],
            },
            "configuration": {
                "configuration_id": rules_version.rules_version_id,
                "configuration_version": rules_version.version,
                "take_profit_mode": rules_version.draft.take_profit_mode.value,
                "minimum_risk_reward": str(rules_version.draft.minimum_risk_reward),
            },
            "available_level_ids": [level.level_id for level in levels],
        },
    )


def _dynamic_entry(
    *,
    direction: str,
    reference_price: Fraction,
    atr: Fraction,
    tick: Fraction,
    levels: Sequence[ReferenceLevel],
) -> PositionPriceResult:
    if direction == "LONG":
        candidates = sorted(
            (level for level in levels if _is_low(level) and level.price < reference_price),
            key=lambda level: _entry_rank_key(level, reference_price=reference_price),
        )
        rounding = RoundingMode.FLOOR
        formula_id = "F-008"
    elif direction == "SHORT":
        candidates = sorted(
            (level for level in levels if _is_high(level) and level.price > reference_price),
            key=lambda level: _entry_rank_key(level, reference_price=reference_price),
        )
        rounding = RoundingMode.CEIL
        formula_id = "F-008"
    else:
        return PositionPriceResult("F-008", PositionResultStatus.FAIL, "INVALID_DIRECTION")
    traversal: list[dict[str, Any]] = []
    for level in candidates:
        improvement = abs(reference_price - level.price)
        distance_atr = exact_divide(improvement, atr)
        accepted = ENTRY_MIN_ATR_DISTANCE <= distance_atr <= ENTRY_MAX_ATR_DISTANCE
        traversal.append(
            {
                "level_id": level.level_id,
                "level_type": level.level_type,
                "price": level.price_text,
                "distance_atr": canonical_decimal_text(distance_atr),
                "accepted": accepted,
            }
        )
        if accepted:
            rounded = quantize(level.price, tick, rounding)
            if rounded <= 0:
                return PositionPriceResult(formula_id, PositionResultStatus.FAIL, "ENTRY_ROUNDS_NONPOSITIVE", traversal=tuple(traversal))
            if direction == "LONG" and rounded >= reference_price:
                return PositionPriceResult(formula_id, PositionResultStatus.FAIL, "ENTRY_ROUNDING_ERROR", traversal=tuple(traversal))
            if direction == "SHORT" and rounded <= reference_price:
                return PositionPriceResult(formula_id, PositionResultStatus.FAIL, "ENTRY_ROUNDING_ERROR", traversal=tuple(traversal))
            rounded_distance_atr = exact_divide(abs(reference_price - rounded), atr)
            traversal[-1]["rounded_price"] = canonical_decimal_text(rounded)
            traversal[-1]["rounded_distance_atr"] = canonical_decimal_text(rounded_distance_atr)
            if not ENTRY_MIN_ATR_DISTANCE <= rounded_distance_atr <= ENTRY_MAX_ATR_DISTANCE:
                return PositionPriceResult(
                    formula_id,
                    PositionResultStatus.UNAVAILABLE,
                    "ATR_DISTANCE_OUT_OF_RANGE_AFTER_ROUNDING",
                    traversal=tuple(traversal),
                )
            return PositionPriceResult(
                formula_id,
                PositionResultStatus.AVAILABLE,
                "AVAILABLE",
                price=rounded,
                raw_price=level.price,
                reference=level,
                distance_atr=rounded_distance_atr,
                traversal=tuple(traversal),
            )
    reason = "NO_ELIGIBLE_REFERENCE" if not candidates else "ATR_DISTANCE_OUT_OF_RANGE"
    return PositionPriceResult(formula_id, PositionResultStatus.UNAVAILABLE, reason, traversal=tuple(traversal))


def _stop_result(
    *,
    direction: str,
    entry: PositionPriceResult,
    atr: Fraction,
    tick: Fraction,
    levels: Sequence[ReferenceLevel],
    rules_version: TradingRulesVersion,
) -> PositionPriceResult:
    if not entry.usable:
        return PositionPriceResult("F-009", PositionResultStatus.UNAVAILABLE, "ENTRY_UNAVAILABLE")
    stop_mode = str((rules_version.draft.metadata or {}).get("stop_loss_mode", "FIXED")).upper()
    if stop_mode == "DYNAMIC":
        return _dynamic_stop(direction=direction, entry=entry, atr=atr, tick=tick, levels=levels)
    if stop_mode == "FIXED":
        return _fixed_stop(direction=direction, entry=entry, tick=tick, rules_version=rules_version)
    return PositionPriceResult("F-009", PositionResultStatus.FAIL, "INVALID_STOP_MODE")


def _dynamic_stop(
    *,
    direction: str,
    entry: PositionPriceResult,
    atr: Fraction,
    tick: Fraction,
    levels: Sequence[ReferenceLevel],
) -> PositionPriceResult:
    assert entry.price is not None
    formula_id = "F-006" if direction == "LONG" else "F-007"
    if direction == "LONG":
        candidates = sorted(
            (level for level in levels if _is_low(level) and level.price < entry.price - tick),
            key=lambda level: _distance_rank_key(level, reference_price=entry.price),
        )
        rounding = RoundingMode.FLOOR
    else:
        candidates = sorted(
            (level for level in levels if _is_high(level) and level.price > entry.price + tick),
            key=lambda level: _distance_rank_key(level, reference_price=entry.price),
        )
        rounding = RoundingMode.CEIL
    traversal: list[dict[str, Any]] = []
    for level in candidates:
        if direction == "LONG":
            raw_stop = level.price - STOP_BUFFER_ATR * atr
            minimum_stop = entry.price - STOP_MIN_DISTANCE_ATR * atr
            adjusted_stop = min(raw_stop, minimum_stop)
            pre_rounding_risk = entry.price - adjusted_stop
        else:
            raw_stop = level.price + STOP_BUFFER_ATR * atr
            minimum_stop = entry.price + STOP_MIN_DISTANCE_ATR * atr
            adjusted_stop = max(raw_stop, minimum_stop)
            pre_rounding_risk = adjusted_stop - entry.price
        distance_atr = exact_divide(pre_rounding_risk, atr)
        traversal.append(
            {
                "level_id": level.level_id,
                "level_type": level.level_type,
                "price": level.price_text,
                "raw_stop": canonical_decimal_text(raw_stop),
                "minimum_stop": canonical_decimal_text(minimum_stop),
                "adjusted_stop": canonical_decimal_text(adjusted_stop),
                "distance_atr": canonical_decimal_text(distance_atr),
                "accepted": distance_atr <= STOP_MAX_DISTANCE_ATR,
            }
        )
        if distance_atr > STOP_MAX_DISTANCE_ATR:
            return PositionPriceResult(formula_id, PositionResultStatus.UNAVAILABLE, "SL_TOO_WIDE", traversal=tuple(traversal))
        rounded = quantize(adjusted_stop, tick, rounding)
        if rounded <= 0:
            return PositionPriceResult(formula_id, PositionResultStatus.FAIL, "ROUNDING_ERROR", traversal=tuple(traversal))
        if direction == "LONG":
            valid_side = rounded < level.price and rounded < entry.price
            post_rounding_risk = entry.price - rounded
        else:
            valid_side = rounded > level.price and rounded > entry.price
            post_rounding_risk = rounded - entry.price
        if not valid_side:
            return PositionPriceResult(formula_id, PositionResultStatus.FAIL, "ROUNDING_ERROR", traversal=tuple(traversal))
        post_distance_atr = exact_divide(post_rounding_risk, atr)
        traversal[-1]["rounded_stop"] = canonical_decimal_text(rounded)
        traversal[-1]["rounded_distance_atr"] = canonical_decimal_text(post_distance_atr)
        if post_distance_atr > STOP_MAX_DISTANCE_ATR:
            return PositionPriceResult(formula_id, PositionResultStatus.UNAVAILABLE, "SL_TOO_WIDE", traversal=tuple(traversal))
        return PositionPriceResult(
            formula_id,
            PositionResultStatus.AVAILABLE,
            "AVAILABLE",
            price=rounded,
            raw_price=raw_stop,
            reference=level,
            distance_atr=post_distance_atr,
            traversal=tuple(traversal),
        )
    return PositionPriceResult(formula_id, PositionResultStatus.UNAVAILABLE, "NO_ELIGIBLE_REFERENCE", traversal=tuple(traversal))


def _fixed_stop(
    *,
    direction: str,
    entry: PositionPriceResult,
    tick: Fraction,
    rules_version: TradingRulesVersion,
) -> PositionPriceResult:
    assert entry.price is not None
    pct = Fraction(rules_version.draft.stop_loss_pct)
    if direction == "LONG":
        raw = entry.price * (1 - pct)
        rounded = quantize(raw, tick, RoundingMode.FLOOR)
    else:
        raw = entry.price * (1 + pct)
        rounded = quantize(raw, tick, RoundingMode.CEIL)
    return PositionPriceResult("F-009", PositionResultStatus.AVAILABLE, "FIXED_AVAILABLE", price=rounded, raw_price=raw)


def _take_profit_result(
    *,
    direction: str,
    entry: PositionPriceResult,
    atr: Fraction,
    tick: Fraction,
    levels: Sequence[ReferenceLevel],
    rules_version: TradingRulesVersion,
) -> PositionPriceResult:
    if not entry.usable:
        return PositionPriceResult("F-010", PositionResultStatus.UNAVAILABLE, "ENTRY_UNAVAILABLE")
    if rules_version.draft.take_profit_mode is TakeProfitMode.FIXED:
        return _fixed_take_profit(direction=direction, entry=entry, tick=tick, rules_version=rules_version)
    return _dynamic_take_profit(direction=direction, entry=entry, atr=atr, tick=tick, levels=levels)


def _dynamic_take_profit(
    *,
    direction: str,
    entry: PositionPriceResult,
    atr: Fraction,
    tick: Fraction,
    levels: Sequence[ReferenceLevel],
) -> PositionPriceResult:
    assert entry.price is not None
    if direction == "LONG":
        candidates = sorted(
            (level for level in levels if _is_high(level) and level.price > entry.price + tick),
            key=lambda level: _distance_rank_key(level, reference_price=entry.price),
        )
        rounding = RoundingMode.FLOOR
    else:
        candidates = sorted(
            (level for level in levels if _is_low(level) and level.price < entry.price - tick),
            key=lambda level: _distance_rank_key(level, reference_price=entry.price),
        )
        rounding = RoundingMode.CEIL
    traversal: list[dict[str, Any]] = []
    for level in candidates:
        distance = abs(level.price - entry.price)
        distance_atr = exact_divide(distance, atr)
        accepted = TAKE_MIN_ATR_DISTANCE <= distance_atr <= TAKE_MAX_ATR_DISTANCE
        if distance_atr < TAKE_MIN_ATR_DISTANCE:
            distance_status = "TOO_CLOSE"
        elif distance_atr > TAKE_MAX_ATR_DISTANCE:
            distance_status = "TOO_FAR"
        else:
            distance_status = "ELIGIBLE"
        traversal.append(
            {
                "level_id": level.level_id,
                "level_type": level.level_type,
                "price": level.price_text,
                "distance_atr": canonical_decimal_text(distance_atr),
                "distance_status": distance_status,
                "accepted": accepted,
            }
        )
        if distance_status == "TOO_FAR":
            return PositionPriceResult("F-010", PositionResultStatus.UNAVAILABLE, "TARGET_TOO_FAR", traversal=tuple(traversal))
        if accepted:
            rounded = quantize(level.price, tick, rounding)
            if direction == "LONG":
                valid_side = entry.price < rounded <= level.price
            else:
                valid_side = level.price <= rounded < entry.price
            if not valid_side:
                return PositionPriceResult("F-010", PositionResultStatus.FAIL, "ROUNDING_ERROR", traversal=tuple(traversal))
            rounded_distance_atr = exact_divide(abs(rounded - entry.price), atr)
            traversal[-1]["rounded_price"] = canonical_decimal_text(rounded)
            traversal[-1]["rounded_distance_atr"] = canonical_decimal_text(rounded_distance_atr)
            if rounded_distance_atr < TAKE_MIN_ATR_DISTANCE:
                return PositionPriceResult(
                    "F-010",
                    PositionResultStatus.UNAVAILABLE,
                    "TARGET_TOO_CLOSE_AFTER_ROUNDING",
                    traversal=tuple(traversal),
                )
            if rounded_distance_atr > TAKE_MAX_ATR_DISTANCE:
                return PositionPriceResult("F-010", PositionResultStatus.FAIL, "ROUNDING_ERROR", traversal=tuple(traversal))
            return PositionPriceResult(
                "F-010",
                PositionResultStatus.AVAILABLE,
                "AVAILABLE",
                price=rounded,
                raw_price=level.price,
                reference=level,
                distance_atr=rounded_distance_atr,
                traversal=tuple(traversal),
            )
    reason = "NO_ELIGIBLE_REFERENCE" if not candidates else "ATR_DISTANCE_OUT_OF_RANGE"
    return PositionPriceResult("F-010", PositionResultStatus.UNAVAILABLE, reason, traversal=tuple(traversal))


def _fixed_take_profit(
    *,
    direction: str,
    entry: PositionPriceResult,
    tick: Fraction,
    rules_version: TradingRulesVersion,
) -> PositionPriceResult:
    assert entry.price is not None
    pct = rules_version.draft.fixed_take_profit_pct or rules_version.draft.minimum_take_profit_pct
    if pct is None or pct <= 0:
        return PositionPriceResult("F-010", PositionResultStatus.UNAVAILABLE, "FIXED_TAKE_PROFIT_NOT_CONFIGURED")
    fraction = Fraction(pct)
    if direction == "LONG":
        raw = entry.price * (1 + fraction)
        rounded = quantize(raw, tick, RoundingMode.FLOOR)
    else:
        raw = entry.price * (1 - fraction)
        rounded = quantize(raw, tick, RoundingMode.CEIL)
    return PositionPriceResult("F-010", PositionResultStatus.AVAILABLE, "FIXED_AVAILABLE", price=rounded, raw_price=raw)


def _price_geometry(
    *,
    direction: str,
    entry: PositionPriceResult,
    stop: PositionPriceResult,
    take_profit: PositionPriceResult,
) -> str:
    if not entry.usable or not stop.usable or not take_profit.usable:
        return "UNAVAILABLE"
    assert entry.price is not None and stop.price is not None and take_profit.price is not None
    if direction == "LONG" and stop.price < entry.price < take_profit.price:
        return "PASS"
    if direction == "SHORT" and take_profit.price < entry.price < stop.price:
        return "PASS"
    return "FAIL"


def _gross_risk_reward(
    *,
    direction: str,
    entry: PositionPriceResult,
    stop: PositionPriceResult,
    take_profit: PositionPriceResult,
) -> Fraction | None:
    if _price_geometry(direction=direction, entry=entry, stop=stop, take_profit=take_profit) != "PASS":
        return None
    assert entry.price is not None and stop.price is not None and take_profit.price is not None
    risk = abs(entry.price - stop.price)
    reward = abs(take_profit.price - entry.price)
    if risk <= 0:
        return None
    return exact_divide(reward, risk)


def _minimum_rr_status(gross_rr: Fraction | None, *, rules_version: TradingRulesVersion) -> str:
    if gross_rr is None:
        return "UNAVAILABLE"
    threshold = Fraction(rules_version.draft.minimum_risk_reward)
    return "PASS" if gross_rr >= threshold else "FAIL"


def _available_levels(levels: Any, *, matched_at: str) -> tuple[ReferenceLevel, ...]:
    if not isinstance(levels, Sequence) or isinstance(levels, (str, bytes)):
        raise PositionOpportunityError("reference_geometry.levels must be an array")
    parsed = tuple(ReferenceLevel.from_payload(level) for level in levels)
    return tuple(level for level in parsed if level.available_at <= matched_at)


def _handoff_body(payload: Mapping[str, Any]) -> dict[str, Any]:
    try:
        parsed = validate_contract_edge(
            producer="Set",
            consumer="Position",
            contract_type="MARKET_HANDOFF",
            payload=payload,
            definition="MARKET_HANDOFF",
        )
    except (ContractError, ContractBindingError) as exc:
        raise PositionOpportunityError(str(exc)) from exc
    return parsed.to_payload()["market_handoff"]


def _positive_decimal(value: object, *, field: str) -> Fraction:
    try:
        parsed = parse_decimal_text(_text(value, field=field))
    except NumericPolicyError as exc:
        raise PositionOpportunityError(f"{field}: {exc}") from exc
    if parsed <= 0:
        raise PositionOpportunityError(f"{field} must be positive")
    return parsed


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PositionOpportunityError(f"{field} is required")
    return value


def _is_low(level: ReferenceLevel) -> bool:
    text = level.level_type.upper()
    return "LOW" in text or level.relative_position == "BELOW_REFERENCE"


def _is_high(level: ReferenceLevel) -> bool:
    text = level.level_type.upper()
    return "HIGH" in text or level.relative_position == "ABOVE_REFERENCE"


def _entry_rank_key(level: ReferenceLevel, *, reference_price: Fraction) -> tuple[str, Fraction, str]:
    return (_reverse_lex_key(level.available_at), abs(reference_price - level.price), level.level_id)


def _distance_rank_key(level: ReferenceLevel, *, reference_price: Fraction) -> tuple[str, Fraction, str]:
    return (_reverse_lex_key(level.available_at), abs(reference_price - level.price), level.level_id)


def _reverse_lex_key(text: str) -> str:
    return "".join(chr(0x10FFFF - ord(char)) for char in text)


def _first_reject_reason(
    checks: Mapping[str, str],
    *,
    entry: PositionPriceResult,
    stop: PositionPriceResult,
    take_profit: PositionPriceResult,
) -> str:
    for name, status in checks.items():
        if status != "PASS":
            if name == "price_geometry":
                if not entry.usable:
                    return f"ENTRY_{entry.reason_code}"
                if not stop.usable:
                    return f"STOP_{stop.reason_code}"
                if not take_profit.usable:
                    return f"TAKE_PROFIT_{take_profit.reason_code}"
            return f"{name.upper()}_{status}"
    return "REJECTED"
