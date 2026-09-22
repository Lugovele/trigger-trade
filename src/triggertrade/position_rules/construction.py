"""Certified post-grant Position construction for v1.2.15 B7B."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Any

from triggertrade.contracts import ContractError, TargetContract, parse_contract
from triggertrade.contracts.bindings import ContractBindingError, validate_contract_edge
from triggertrade.numeric_policy import (
    QCAPITAL,
    canonical_decimal_text,
    exact_divide,
    floor_to_grid,
    parse_decimal_text,
    qcapital_ceil,
    qratio_floor,
)
from triggertrade.order_specs import build_order_spec, order_spec_digest, validate_order_spec_for_construction
from triggertrade.position_construction import (
    build_constructed_position_result,
    build_rejected_position_construction_result,
)


class PositionConstructionEvaluationError(ValueError):
    """Raised when post-grant construction cannot be evaluated deterministically."""


class ConstructionStatus(StrEnum):
    CONSTRUCTED = "CONSTRUCTED"
    REJECT = "REJECT"


@dataclass(frozen=True)
class PositionConstructionEvaluation:
    status: ConstructionStatus
    primary_reason: str
    failed_gates: tuple[str, ...]
    sizing: dict[str, Any]
    economics: dict[str, Any]
    construction_result: TargetContract
    order_spec: TargetContract | None

    def to_payload(self) -> dict[str, Any]:
        return {
            "position_construction_evaluation": {
                "state_version": 1,
                "status": self.status.value,
                "primary_reason": self.primary_reason,
                "failed_gates": list(self.failed_gates),
                "sizing": self.sizing,
                "economics": self.economics,
                "construction_result": self.construction_result.to_payload(),
                "order_spec": None if self.order_spec is None else self.order_spec.to_payload(),
            }
        }


@dataclass(frozen=True)
class PositionConstructionCommand:
    event_id: str
    occurred_at: str
    construction_result_id: str
    position_plan_id: str
    tranche_id: str
    order_spec_id: str
    capital_grant: Mapping[str, Any]
    position_opportunity_state: Mapping[str, Any]


def evaluate_position_construction(command: PositionConstructionCommand) -> PositionConstructionEvaluation:
    grant_contract = _capital_grant(command.capital_grant)
    grant = grant_contract.to_payload()["capital_and_limits"]
    opportunity = _opportunity_state(command.position_opportunity_state)
    decision = opportunity["decision"]
    evaluation = opportunity["evaluation"]
    rules_version = opportunity["source_configuration"]["rules_version"]
    draft = rules_version["draft"]

    failures: list[str] = []
    sizing: dict[str, Any] = {}
    economics: dict[str, Any] = {}

    _validate_identity(grant=grant, decision=decision, evaluation=evaluation)
    if decision["decision"] != "APPROVE":
        failures.append("INITIAL_DECISION_NOT_APPROVED")

    entry = _price_result(evaluation, "entry")
    stop = _price_result(evaluation, "stop")
    take_profit = _price_result(evaluation, "take_profit")
    for label, result in (("ENTRY", entry), ("STOP", stop), ("TP", take_profit)):
        if result["status"] != "AVAILABLE" or result["price"] is None:
            failures.append(f"DEPENDENCY_{label}_UNAVAILABLE")

    sizing_failure = None
    try:
        sizing = _evaluate_sizing(grant=grant, entry=entry, draft=draft)
    except PositionConstructionEvaluationError as exc:
        sizing_failure = str(exc)
        failures.append(sizing_failure)

    economics_rule = _minimum_net_edge_rule(
        enabled=_bool(draft.get("minimum_net_edge_enabled"), field="minimum_net_edge_enabled"),
        status="UNAVAILABLE",
        configured_value=_optional_text(draft.get("minimum_net_edge_pct")),
        calculated_value=None,
        reason_code="DEPENDENCY_SIZING_UNAVAILABLE" if sizing_failure else None,
    )
    if not failures:
        economics, economics_rule, economics_failures = _evaluate_economics(
            grant=grant,
            sizing=sizing,
            entry=entry,
            stop=stop,
            take_profit=take_profit,
            draft=draft,
            direction=str(evaluation["direction"]),
        )
        failures.extend(economics_failures)

    if failures:
        construction = build_rejected_position_construction_result(
            event_id=command.event_id,
            occurred_at=command.occurred_at,
            construction_result_id=command.construction_result_id,
            capital_grant=grant_contract.to_payload(),
            minimum_net_edge=economics_rule,
            failed_gates=tuple(failures),
            reason_code=failures[0],
        )
        return PositionConstructionEvaluation(
            status=ConstructionStatus.REJECT,
            primary_reason=failures[0],
            failed_gates=tuple(failures),
            sizing=sizing,
            economics=economics,
            construction_result=construction,
            order_spec=None,
        )

    side = "BUY" if evaluation["direction"] == "LONG" else "SELL"
    order_spec = build_order_spec(
        order_spec_id=command.order_spec_id,
        spec_created_at=command.occurred_at,
        construction_result_id=command.construction_result_id,
        capital_grant=grant_contract.to_payload(),
        position_plan_id=command.position_plan_id,
        tranche_id=command.tranche_id,
        direction=str(evaluation["direction"]),
        side=side,
        entry={"order_type": "LIMIT", "post_only": True, "price": entry["price"], "quantity": sizing["final_qty"]},
        leverage=sizing["leverage"],
        take_profit=_exit_payload(take_profit, draft=draft, key="take_profit"),
        stop_loss=_exit_payload(stop, draft=draft, key="stop"),
        economics=_order_economics_payload(sizing=sizing, economics=economics, rule=economics_rule, grant=grant),
        venue_validation=_venue_validation_payload(grant),
        provenance=_provenance_payload(opportunity=opportunity, grant=grant),
    )
    digest = order_spec_digest(order_spec)
    construction = build_constructed_position_result(
        event_id=command.event_id,
        occurred_at=command.occurred_at,
        construction_result_id=command.construction_result_id,
        capital_grant=grant_contract.to_payload(),
        position_plan_id=command.position_plan_id,
        tranche_id=command.tranche_id,
        order_spec_id=command.order_spec_id,
        order_spec_digest=digest,
        approved_economics={
            "approved_entry": entry["price"],
            "approved_quantity": sizing["final_qty"],
            "approved_leverage": sizing["leverage"],
            "approved_actual_order_notional": sizing["actual_order_notional"],
            "approved_actual_committed_capital": sizing["actual_committed_capital"],
        },
        minimum_net_edge=economics_rule,
        direction=str(evaluation["direction"]),
    )
    validate_order_spec_for_construction(
        construction_result=construction.to_payload(),
        order_spec=order_spec.to_payload(),
    )
    return PositionConstructionEvaluation(
        status=ConstructionStatus.CONSTRUCTED,
        primary_reason="CONSTRUCTED",
        failed_gates=(),
        sizing=sizing,
        economics=economics,
        construction_result=construction,
        order_spec=order_spec,
    )


def _capital_grant(payload: Mapping[str, Any]) -> TargetContract:
    try:
        parsed = validate_contract_edge(
            producer="Portfolio",
            consumer="Position",
            contract_type="CAPITAL_AND_LIMITS",
            payload=payload,
            definition="CAPITAL_AND_LIMITS",
        )
        return parsed
    except (ContractError, ContractBindingError) as exc:
        raise PositionConstructionEvaluationError(str(exc)) from exc


def _opportunity_state(payload: Mapping[str, Any]) -> dict[str, Any]:
    try:
        state = payload["position_opportunity_state"]
    except KeyError as exc:
        raise PositionConstructionEvaluationError("position_opportunity_state is required") from exc
    decision = state["decision"]
    try:
        parse_contract("APPROVE_REJECT", {"position_decision": decision}, definition="APPROVE_REJECT.initial")
    except ContractError as exc:
        raise PositionConstructionEvaluationError(str(exc)) from exc
    return dict(state)


def _validate_identity(*, grant: Mapping[str, Any], decision: Mapping[str, Any], evaluation: Mapping[str, Any]) -> None:
    for field in ("position_decision_id", "decision_cycle_id", "set_result_id", "symbol"):
        if grant[field] != decision[field] or grant[field] != evaluation[field]:
            raise PositionConstructionEvaluationError("IDENTITY_INVALID")


def _price_result(evaluation: Mapping[str, Any], key: str) -> dict[str, Any]:
    value = dict(evaluation[key])
    if value.get("price") is not None:
        _positive_decimal(value["price"], field=f"{key}.price")
    return value


def _evaluate_sizing(*, grant: Mapping[str, Any], entry: Mapping[str, Any], draft: Mapping[str, Any]) -> dict[str, Any]:
    instrument = grant["venue_facts"]["instrument"]
    C = _positive_decimal(grant["requested_capital_per_tranche"], field="requested_capital_per_tranche")
    if C % QCAPITAL != 0:
        raise PositionConstructionEvaluationError("INVALID_CAPITAL_GRANT")
    L = _positive_decimal(str(draft["leverage"]), field="leverage")
    max_leverage = _positive_decimal(instrument["max_leverage"], field="max_leverage")
    E = _positive_decimal(entry["price"], field="entry.price")
    qty_step = _positive_decimal(instrument["qty_step"], field="qty_step")
    min_qty = _positive_decimal(instrument["min_order_qty"], field="min_order_qty")
    min_notional = _positive_decimal(instrument["min_notional"], field="min_notional")
    if L > max_leverage:
        raise PositionConstructionEvaluationError("LEVERAGE_ABOVE_MAXIMUM")
    target = C * L
    raw_qty = exact_divide(target, E)
    final_qty = floor_to_grid(raw_qty, qty_step)
    actual_notional = final_qty * E
    actual_exact_capital = exact_divide(actual_notional, L)
    held_capital = qcapital_ceil(actual_exact_capital).value
    if actual_exact_capital > C or held_capital > C:
        raise PositionConstructionEvaluationError("CAPITAL_BOUND_VIOLATION")
    if final_qty == 0:
        raise PositionConstructionEvaluationError("QTY_ZERO_AFTER_FLOOR")
    if final_qty < min_qty:
        raise PositionConstructionEvaluationError("QTY_BELOW_MINIMUM")
    max_status = str(instrument["max_order_qty_status"])
    max_order_qty = instrument.get("max_order_qty")
    if max_status == "UNAVAILABLE":
        raise PositionConstructionEvaluationError("MAX_ORDER_QTY_UNAVAILABLE")
    if max_status == "AVAILABLE":
        max_qty = _positive_decimal(max_order_qty, field="max_order_qty")
        if max_qty < min_qty:
            raise PositionConstructionEvaluationError("INVALID_EXCHANGE_FACT")
        if final_qty > max_qty:
            raise PositionConstructionEvaluationError("QTY_ABOVE_MAXIMUM")
    elif max_status == "NOT_APPLICABLE":
        raise PositionConstructionEvaluationError("INVALID_EXCHANGE_FACT")
    else:
        raise PositionConstructionEvaluationError("INVALID_EXCHANGE_FACT")
    if actual_notional < min_notional:
        raise PositionConstructionEvaluationError("NOTIONAL_BELOW_MINIMUM")
    return {
        "requested_capital": canonical_decimal_text(C),
        "leverage": canonical_decimal_text(L),
        "entry_price": canonical_decimal_text(E),
        "target_order_notional": canonical_decimal_text(target),
        "raw_qty": _rational_payload(raw_qty),
        "final_qty": canonical_decimal_text(final_qty),
        "actual_order_notional": canonical_decimal_text(actual_notional),
        "actual_committed_capital_exact": _rational_payload(actual_exact_capital),
        "actual_committed_capital": canonical_decimal_text(held_capital),
    }


def _evaluate_economics(
    *,
    grant: Mapping[str, Any],
    sizing: Mapping[str, Any],
    entry: Mapping[str, Any],
    stop: Mapping[str, Any],
    take_profit: Mapping[str, Any],
    draft: Mapping[str, Any],
    direction: str,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    E = parse_decimal_text(sizing["entry_price"])
    Q = parse_decimal_text(sizing["final_qty"])
    N = parse_decimal_text(sizing["actual_order_notional"])
    SL = _positive_decimal(stop["price"], field="stop.price")
    TP = _positive_decimal(take_profit["price"], field="take_profit.price")
    side = Fraction(1) if direction == "LONG" else Fraction(-1)
    dr = side * (E - SL)
    dw = side * (TP - E)
    failures: list[str] = []
    if dr == 0:
        failures.append("ZERO_RISK_DISTANCE")
    elif dr < 0 or dw <= 0:
        failures.append("INVALID_GEOMETRY")
    maker = _decimal(grant["venue_facts"]["fees"]["maker_fee_rate"], field="maker_fee_rate")
    taker = _decimal(grant["venue_facts"]["fees"]["taker_fee_rate"], field="taker_fee_rate")
    economics: dict[str, Any] = {
        "funding_in_planned_net_edge": False,
        "maker_fee_rate": canonical_decimal_text(maker),
        "taker_fee_rate": canonical_decimal_text(taker),
    }
    if failures:
        rule = _minimum_net_edge_rule(
            enabled=_bool(draft.get("minimum_net_edge_enabled"), field="minimum_net_edge_enabled"),
            status="UNAVAILABLE",
            configured_value=_optional_text(draft.get("minimum_net_edge_pct")),
            calculated_value=None,
            reason_code=failures[0],
        )
        return economics, rule, failures
    gross_rr = exact_divide(dw, dr)
    gross_profit_tp = dw * Q
    entry_fee = N * maker
    tp_exit_notional = TP * Q
    tp_exit_fee = tp_exit_notional * taker
    net_profit_tp = gross_profit_tp - entry_fee - tp_exit_fee
    net_edge_pct = exact_divide(100 * net_profit_tp, N)
    rr_threshold = _decimal(draft.get("minimum_risk_reward"), field="minimum_risk_reward")
    if dw < rr_threshold * dr:
        failures.append("RR_BELOW_MINIMUM")
    enabled = _bool(draft.get("minimum_net_edge_enabled"), field="minimum_net_edge_enabled")
    configured = _optional_text(draft.get("minimum_net_edge_pct"))
    status = "NOT_APPLICABLE"
    reason_code = None
    if enabled:
        threshold = _decimal(configured, field="minimum_net_edge_pct")
        if 100 * net_profit_tp < threshold * N:
            status = "FAIL"
            reason_code = "NET_EDGE_BELOW_MINIMUM"
            failures.append("NET_EDGE_BELOW_MINIMUM")
        else:
            status = "PASS"
    economics.update(
        {
            "risk_distance_price": canonical_decimal_text(dr),
            "reward_distance_price": canonical_decimal_text(dw),
            "gross_rr": qratio_floor(gross_rr).text,
            "gross_rr_exact": _rational_payload(gross_rr),
            "gross_profit_tp": canonical_decimal_text(gross_profit_tp),
            "expected_entry_fee": canonical_decimal_text(entry_fee),
            "tp_exit_notional": canonical_decimal_text(tp_exit_notional),
            "expected_tp_exit_fee": canonical_decimal_text(tp_exit_fee),
            "net_profit_tp": canonical_decimal_text(net_profit_tp),
            "planned_net_edge_pct": qratio_floor(net_edge_pct).text,
            "planned_net_edge_pct_exact": _rational_payload(net_edge_pct),
        }
    )
    return (
        economics,
        _minimum_net_edge_rule(
            enabled=enabled,
            status=status,
            configured_value=configured if enabled else None,
            calculated_value=qratio_floor(net_edge_pct).text,
            reason_code=reason_code,
        ),
        failures,
    )


def _order_economics_payload(
    *,
    sizing: Mapping[str, Any],
    economics: Mapping[str, Any],
    rule: Mapping[str, Any],
    grant: Mapping[str, Any],
) -> dict[str, Any]:
    fees = grant["venue_facts"]["fees"]
    return {
        "target_order_notional": sizing["target_order_notional"],
        "actual_order_notional": sizing["actual_order_notional"],
        "actual_committed_capital": sizing["actual_committed_capital"],
        "gross_rr": economics["gross_rr"],
        "planned_net_edge_pct": economics["planned_net_edge_pct"],
        "minimum_net_edge_enabled": rule["enabled"],
        "minimum_net_edge_result": rule["status"],
        "maker_fee_rate": economics["maker_fee_rate"],
        "taker_fee_rate": economics["taker_fee_rate"],
        "fee_schedule_version": str(fees["fee_schedule_version"]),
        "fee_rate_source_ref": str(fees["source_ref"]),
        "funding_in_planned_net_edge": False,
    }


def _venue_validation_payload(grant: Mapping[str, Any]) -> dict[str, Any]:
    instrument = grant["venue_facts"]["instrument"]
    return {
        "max_order_qty_status": instrument["max_order_qty_status"],
        "max_order_qty": instrument.get("max_order_qty"),
        "max_order_qty_source_field": instrument["max_order_qty_source_field"],
        "max_order_qty_source_ref": instrument["source_ref"],
        "native_profile_revision": instrument["native_profile_revision"],
    }


def _provenance_payload(*, opportunity: Mapping[str, Any], grant: Mapping[str, Any]) -> dict[str, Any]:
    source_config = opportunity["source_configuration"]
    source_contract = opportunity["source_contracts"]["market_handoff"]["market_handoff"]
    return {
        "set_version": str(source_contract.get("set_version", source_contract["set_result_id"])),
        "position_rules_version": str(source_config["version"]),
        "instrument_metadata_revision": grant["venue_facts"]["instrument"]["metadata_revision"],
        "market_snapshot_at": source_contract["snapshot"]["market_snapshot_at"],
    }


def _exit_payload(result: Mapping[str, Any], *, draft: Mapping[str, Any], key: str) -> dict[str, Any]:
    is_fixed = str(result["reason_code"]).startswith("FIXED")
    fixed_pct = None
    if is_fixed and key == "take_profit":
        fixed_pct = _optional_text(draft.get("fixed_take_profit_pct") or draft.get("minimum_take_profit_pct"))
    if is_fixed and key == "stop":
        fixed_pct = _optional_text(draft.get("stop_loss_pct"))
    return {
        "mode": "FIXED" if is_fixed else "DYNAMIC",
        "price": result["price"],
        "execution_type": "MARKET",
        "trigger_by": "LAST_PRICE",
        "scope": "PARTIAL_QUANTITY",
        "fixed_pct": fixed_pct,
    }


def _minimum_net_edge_rule(
    *,
    enabled: bool,
    status: str,
    configured_value: str | None,
    calculated_value: str | None,
    reason_code: str | None,
) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "status": status,
        "configured_value": configured_value if enabled else None,
        "calculated_value": calculated_value,
        "reason_code": reason_code,
    }


def _positive_decimal(value: object, *, field: str) -> Fraction:
    parsed = _decimal(value, field=field)
    if parsed <= 0:
        raise PositionConstructionEvaluationError(field.upper() if field != "requested_capital_per_tranche" else "INVALID_CAPITAL_GRANT")
    return parsed


def _decimal(value: object, *, field: str) -> Fraction:
    try:
        return parse_decimal_text(_text(value, field=field))
    except Exception as exc:
        raise PositionConstructionEvaluationError(f"INVALID_{field.upper()}") from exc


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PositionConstructionEvaluationError(f"{field} is required")
    return value


def _optional_text(value: object) -> str | None:
    return None if value is None else _text(value, field="optional_decimal")


def _bool(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise PositionConstructionEvaluationError("CONFIG_INVALID")
    return value


def _rational_payload(value: Fraction) -> dict[str, str]:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}
