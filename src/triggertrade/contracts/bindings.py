"""Contract graph and immutable semantic binding checks.

These helpers validate already-produced owner/API contract envelopes. They do
not create business decisions, owner state, identifiers, or persistence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from triggertrade.canonical_json import canonical_json_digest

from .registry import ContractError, ContractType, TargetContract, parse_contract


class BindingRole(StrEnum):
    PORTFOLIO = "Portfolio"
    SET = "Set"
    POSITION = "Position"
    LIFECYCLE = "Lifecycle"
    API = "API"


class ContractBindingError(ValueError):
    """Raised when a contract envelope violates the approved binding graph."""


@dataclass(frozen=True)
class ContractEdge:
    producer: BindingRole
    consumer: BindingRole
    contract_type: ContractType
    version: int
    definitions: tuple[str, ...]


APPROVED_CONTRACT_EDGES: tuple[ContractEdge, ...] = (
    ContractEdge(BindingRole.PORTFOLIO, BindingRole.SET, ContractType.COINS, 2, ("COINS",)),
    ContractEdge(BindingRole.SET, BindingRole.POSITION, ContractType.MARKET_HANDOFF, 4, ("MARKET_HANDOFF",)),
    ContractEdge(
        BindingRole.POSITION,
        BindingRole.PORTFOLIO,
        ContractType.APPROVE_REJECT,
        5,
        ("APPROVE_REJECT.initial", "APPROVE_REJECT.constructed", "APPROVE_REJECT.failed"),
    ),
    ContractEdge(BindingRole.PORTFOLIO, BindingRole.POSITION, ContractType.CAPITAL_AND_LIMITS, 5, ("CAPITAL_AND_LIMITS",)),
    ContractEdge(BindingRole.POSITION, BindingRole.LIFECYCLE, ContractType.ORDER_SPEC, 5, ("ORDER_SPEC",)),
    ContractEdge(BindingRole.PORTFOLIO, BindingRole.LIFECYCLE, ContractType.SUBMIT_AUTHORIZED, 5, ("SUBMIT_AUTHORIZED",)),
    ContractEdge(
        BindingRole.LIFECYCLE,
        BindingRole.PORTFOLIO,
        ContractType.ORDER_EVENT,
        7,
        (
            "ORDER_EVENT.logical",
            "ORDER_EVENT.native",
            "ORDER_EVENT.resolution",
            "ORDER_EVENT.scope_observation",
            "ORDER_EVENT.scope_resolution",
            "ORDER_EVENT.integrity",
        ),
    ),
    ContractEdge(BindingRole.LIFECYCLE, BindingRole.SET, ContractType.ORDER_PLACED, 3, ("ORDER_PLACED.placed", "ORDER_PLACED.terminal")),
    ContractEdge(BindingRole.SET, BindingRole.LIFECYCLE, ContractType.ORDER_CANCEL_SIGNAL, 2, ("ORDER_CANCEL_SIGNAL",)),
    ContractEdge(BindingRole.PORTFOLIO, BindingRole.API, ContractType.PORTFOLIO_DATA_REQUEST, 5, ("PORTFOLIO_DATA_REQUEST.request",)),
    ContractEdge(BindingRole.API, BindingRole.PORTFOLIO, ContractType.PORTFOLIO_DATA_REQUEST, 5, ("PORTFOLIO_DATA_REQUEST.response",)),
    ContractEdge(BindingRole.SET, BindingRole.API, ContractType.MARKET_DATA_REQUEST, 3, ("MARKET_DATA_REQUEST.request",)),
    ContractEdge(BindingRole.API, BindingRole.SET, ContractType.MARKET_DATA_REQUEST, 3, ("MARKET_DATA_REQUEST.response",)),
    ContractEdge(
        BindingRole.LIFECYCLE,
        BindingRole.API,
        ContractType.ORDER_MANAGEMENT,
        4,
        (
            "ORDER_MANAGEMENT.request.CREATE_ENTRY_ORDER",
            "ORDER_MANAGEMENT.request.CANCEL_ENTRY_ORDER",
            "ORDER_MANAGEMENT.request.GET_ORDER",
            "ORDER_MANAGEMENT.request.GET_OPEN_ORDERS",
            "ORDER_MANAGEMENT.request.GET_ORDER_HISTORY",
            "ORDER_MANAGEMENT.request.GET_EXECUTIONS",
            "ORDER_MANAGEMENT.request.GET_POSITION",
            "ORDER_MANAGEMENT.request.SET_OR_ATTACH_TP_SL",
            "ORDER_MANAGEMENT.request.CANCEL_PROTECTIVE_ORDER",
            "ORDER_MANAGEMENT.request.CLOSE_POSITION_QUANTITY",
            "ORDER_MANAGEMENT.request.GET_ACCOUNT_EXECUTION_FACTS",
            "ORDER_MANAGEMENT.request.GET_FINANCIAL_FACTS",
            "ORDER_MANAGEMENT.request.GET_HARD_EXECUTION_FACTS",
        ),
    ),
    ContractEdge(
        BindingRole.API,
        BindingRole.LIFECYCLE,
        ContractType.ORDER_MANAGEMENT,
        4,
        ("ORDER_MANAGEMENT.response.financial", "ORDER_MANAGEMENT.response.hard", "ORDER_MANAGEMENT.response.operation"),
    ),
)


def validate_contract_edge(
    *,
    producer: str | BindingRole,
    consumer: str | BindingRole,
    contract_type: str | ContractType,
    payload: Mapping[str, Any],
    definition: str | None = None,
) -> TargetContract:
    """Validate an envelope against one approved producer/consumer edge."""

    resolved_producer = _role(producer)
    resolved_consumer = _role(consumer)
    resolved_type = _contract_type(contract_type)
    parsed = _parse_contract(resolved_type, payload, definition=definition)
    edge = _find_edge(
        producer=resolved_producer,
        consumer=resolved_consumer,
        contract_type=resolved_type,
        definition=parsed.definition,
    )
    if parsed.version != edge.version:
        raise ContractBindingError(
            f"{parsed.definition} version {parsed.version} does not match approved edge version {edge.version}"
        )
    return parsed


def approved_contract_graph() -> tuple[ContractEdge, ...]:
    """Return the immutable approved edge inventory."""

    return APPROVED_CONTRACT_EDGES


def contract_body(contract: TargetContract | Mapping[str, Any], *, contract_type: str | ContractType, definition: str | None = None) -> dict[str, Any]:
    """Return the single approved root body after public parser validation."""

    resolved_type = _contract_type(contract_type)
    parsed = contract if isinstance(contract, TargetContract) else _parse_contract(resolved_type, contract, definition=definition)
    if parsed.contract_type != resolved_type:
        raise ContractBindingError(f"{parsed.definition} does not match requested {resolved_type.value}")
    if definition is not None and parsed.definition != definition:
        raise ContractBindingError(f"{parsed.definition} does not match requested {definition}")
    payload = parsed.to_payload()
    if len(payload) != 1:
        raise ContractBindingError(f"{parsed.definition} must have one root object")
    return next(iter(payload.values()))


def require_matching_fields(
    *,
    source_name: str,
    source: Mapping[str, Any],
    target_name: str,
    target: Mapping[str, Any],
    fields: Sequence[str],
) -> None:
    """Require exact duplicated scalar equality across two parsed bodies."""

    for field in fields:
        if field not in source:
            raise ContractBindingError(f"{source_name}.{field} is required for binding")
        if field not in target:
            raise ContractBindingError(f"{target_name}.{field} is required for binding")
        if source[field] != target[field]:
            raise ContractBindingError(f"{target_name}.{field} must match {source_name}.{field}")


def require_expected_fields(
    *,
    payload_name: str,
    payload: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> None:
    """Require exact values for an accepted lineage/configuration binding."""

    for field, value in expected.items():
        if field not in payload:
            raise ContractBindingError(f"{payload_name}.{field} is required for binding")
        if payload[field] != value:
            raise ContractBindingError(f"{payload_name}.{field} must match accepted binding")


def require_digest_binding(
    *,
    payload_name: str,
    payload: TargetContract | Mapping[str, Any],
    supplied_digest: str,
) -> None:
    """Verify a supplied digest independently from the canonical payload."""

    resolved_payload = payload.to_payload() if isinstance(payload, TargetContract) else dict(payload)
    expected = canonical_json_digest(resolved_payload)
    if supplied_digest != expected:
        raise ContractBindingError(f"{payload_name} digest mismatch")


def validate_position_config_pin_binding(
    *,
    pin_payload: Mapping[str, Any],
    market_handoff: Mapping[str, Any],
    configuration_id: str,
    configuration_version: str,
    configuration_content_digest: str,
) -> None:
    """Validate a Position config pin against its frozen handoff/configuration.

    The caller supplies an existing pin payload and selected configuration
    identity. B4 verifies the immutable binding only; it does not select the
    configuration or create a new pin.
    """

    pin_root = pin_payload.get("position_config_pin")
    if not isinstance(pin_root, Mapping):
        raise ContractBindingError("position_config_pin payload is required")
    handoff = contract_body(market_handoff, contract_type=ContractType.MARKET_HANDOFF, definition="MARKET_HANDOFF")
    symbol = handoff["symbol"]
    if isinstance(symbol, str):
        symbol = symbol.upper()
    require_expected_fields(
        payload_name="position_config_pin",
        payload=pin_root,
        expected={
            "decision_cycle_id": handoff["decision_cycle_id"],
            "set_result_id": handoff["set_result_id"],
            "symbol": symbol,
            "market_handoff_digest": canonical_json_digest(market_handoff),
            "configuration_id": configuration_id,
            "configuration_version": configuration_version,
            "configuration_content_digest": configuration_content_digest,
        },
    )


def validate_order_spec_construction_binding(
    *,
    construction_result: Mapping[str, Any],
    order_spec: Mapping[str, Any],
) -> TargetContract:
    """Validate the B4 construction-result to Order Spec identity binding."""

    construction = contract_body(
        construction_result,
        contract_type=ContractType.APPROVE_REJECT,
        definition="APPROVE_REJECT.constructed",
    )
    parsed_spec = _parse_contract(ContractType.ORDER_SPEC, order_spec, definition="ORDER_SPEC")
    spec = contract_body(parsed_spec, contract_type=ContractType.ORDER_SPEC)
    require_matching_fields(
        source_name="construction_result",
        source=construction,
        target_name="order_spec",
        target=spec,
        fields=(
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
        ),
    )
    if construction["order_spec_contract_version"] != spec["contract_version"]:
        raise ContractBindingError("order_spec.contract_version must match construction_result.order_spec_contract_version")
    require_digest_binding(payload_name="order_spec", payload=parsed_spec, supplied_digest=str(construction["order_spec_digest"]))
    economics = spec["economics"]
    approved = construction["approved_economics"]
    scalar_pairs = {
        "approved_entry": spec["entry"]["price"],
        "approved_quantity": spec["entry"]["quantity"],
        "approved_leverage": spec["leverage"],
        "approved_actual_order_notional": economics["actual_order_notional"],
        "approved_actual_committed_capital": economics["actual_committed_capital"],
    }
    for field, expected in scalar_pairs.items():
        if approved[field] != expected:
            raise ContractBindingError(f"construction_result.{field} must match order_spec")
    rule = construction["rule_results"]["minimum_net_edge"]
    if economics["minimum_net_edge_enabled"] != rule["enabled"]:
        raise ContractBindingError("construction_result.minimum_net_edge.enabled must match order_spec economics")
    if economics["minimum_net_edge_result"] != rule["status"]:
        raise ContractBindingError("construction_result.minimum_net_edge.status must match order_spec economics")
    if economics["planned_net_edge_pct"] != rule["calculated_value"]:
        raise ContractBindingError("construction_result.minimum_net_edge.calculated_value must match order_spec economics")
    return parsed_spec


def _find_edge(
    *,
    producer: BindingRole,
    consumer: BindingRole,
    contract_type: ContractType,
    definition: str,
) -> ContractEdge:
    for edge in APPROVED_CONTRACT_EDGES:
        if (
            edge.producer == producer
            and edge.consumer == consumer
            and edge.contract_type == contract_type
            and definition in edge.definitions
        ):
            return edge
    raise ContractBindingError(
        f"{contract_type.value} {definition} is not approved for {producer.value} -> {consumer.value}"
    )


def _parse_contract(contract_type: ContractType, payload: Mapping[str, Any], *, definition: str | None = None) -> TargetContract:
    try:
        return parse_contract(contract_type, payload, definition=definition)
    except ContractError as exc:
        raise ContractBindingError(str(exc)) from exc


def _contract_type(contract_type: str | ContractType) -> ContractType:
    try:
        return ContractType(contract_type)
    except ValueError as exc:
        raise ContractBindingError(f"unknown contract type: {contract_type}") from exc


def _role(role: str | BindingRole) -> BindingRole:
    try:
        return BindingRole(role)
    except ValueError as exc:
        raise ContractBindingError(f"unknown binding role: {role}") from exc
