"""Strict target contract envelopes for the approved v1.2.14 wire package."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Any, Mapping

from triggertrade.canonical_json import CanonicalJsonError, canonical_json_digest

from .schema_validator import SchemaValidationError, validate_wire_definition


APPROVED_PACKAGE_REVISION = "v1.2.14"
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


class ContractError(ValueError):
    """Raised when a target wire contract payload is invalid."""


class ContractType(StrEnum):
    COINS = "COINS"
    MARKET_HANDOFF = "MARKET_HANDOFF"
    APPROVE_REJECT = "APPROVE_REJECT"
    CAPITAL_AND_LIMITS = "CAPITAL_AND_LIMITS"
    ORDER_SPEC = "ORDER_SPEC"
    SUBMIT_AUTHORIZED = "SUBMIT_AUTHORIZED"
    ORDER_EVENT = "ORDER_EVENT"
    ORDER_PLACED = "ORDER_PLACED"
    ORDER_CANCEL_SIGNAL = "ORDER_CANCEL_SIGNAL"
    PORTFOLIO_DATA_REQUEST = "PORTFOLIO_DATA_REQUEST"
    ORDER_MANAGEMENT = "ORDER_MANAGEMENT"
    MARKET_DATA_REQUEST = "MARKET_DATA_REQUEST"


@dataclass(frozen=True)
class ContractDefinition:
    contract_type: ContractType
    version: int
    definition: str
    top_key: str
    root_required: tuple[str, ...]
    const_fields: Mapping[str, Any]
    enum_fields: Mapping[str, tuple[Any, ...]]
    digest_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class TargetContract:
    contract_type: ContractType
    version: int
    definition: str
    payload: Mapping[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return _copy_json_value(self.payload)

    @property
    def digest(self) -> str:
        return contract_digest(self)


def implemented_contract_registry() -> dict[str, dict[str, object]]:
    """Return implemented approved families and definitions."""

    families: dict[str, dict[str, object]] = {}
    for contract_type, definitions in _DEFINITIONS.items():
        families[contract_type.value] = {
            "version": definitions[0].version,
            "definitions": tuple(definition.definition for definition in definitions),
        }
    return families


def get_contract_definition(
    contract_type: str | ContractType,
    version: int | None = None,
    definition: str | None = None,
) -> ContractDefinition:
    resolved_type = _contract_type(contract_type)
    definitions = _DEFINITIONS[resolved_type]
    if version is not None and version != definitions[0].version:
        raise ContractError(f"unsupported {resolved_type.value} contract version: {version}")
    if definition is None:
        if len(definitions) != 1:
            raise ContractError(f"{resolved_type.value} requires an explicit definition")
        return definitions[0]
    for candidate in definitions:
        if candidate.definition == definition:
            return candidate
    raise ContractError(f"unknown {resolved_type.value} contract definition: {definition}")


def parse_contract(
    contract_type: str | ContractType,
    payload: Mapping[str, Any],
    *,
    version: int | None = None,
    definition: str | None = None,
) -> TargetContract:
    contract_definition = _match_definition(contract_type, payload, version=version, definition=definition)
    _validate_payload(contract_definition, payload)
    return TargetContract(
        contract_type=contract_definition.contract_type,
        version=contract_definition.version,
        definition=contract_definition.definition,
        payload=_copy_json_value(payload),
    )


def validate_contract(
    contract_type: str | ContractType,
    payload: Mapping[str, Any],
    *,
    version: int | None = None,
    definition: str | None = None,
) -> None:
    parse_contract(contract_type, payload, version=version, definition=definition)


def contract_digest(contract: TargetContract | Mapping[str, Any]) -> str:
    payload = contract.to_payload() if isinstance(contract, TargetContract) else payload_from_mapping(contract)
    try:
        return canonical_json_digest(payload)
    except CanonicalJsonError as exc:
        raise ContractError(str(exc)) from exc


def payload_from_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _copy_json_value(payload)


def _match_definition(
    contract_type: str | ContractType,
    payload: Mapping[str, Any],
    *,
    version: int | None,
    definition: str | None,
) -> ContractDefinition:
    resolved_type = _contract_type(contract_type)
    if definition is not None:
        return get_contract_definition(resolved_type, version=version, definition=definition)

    matches: list[ContractDefinition] = []
    errors: list[str] = []
    for candidate in _DEFINITIONS[resolved_type]:
        try:
            _validate_payload(candidate, payload)
        except ContractError as exc:
            errors.append(str(exc))
        else:
            if version is not None and version != candidate.version:
                raise ContractError(f"unsupported {resolved_type.value} contract version: {version}")
            matches.append(candidate)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ContractError(f"ambiguous {resolved_type.value} contract definition")
    raise ContractError(f"payload does not match {resolved_type.value}: {'; '.join(errors)}")


def _validate_payload(definition: ContractDefinition, payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise ContractError(f"{definition.definition} payload must be an object")
    _reject_unknown(set(payload), {definition.top_key}, definition.definition)
    root = payload.get(definition.top_key)
    if not isinstance(root, Mapping):
        raise ContractError(f"{definition.definition}.{definition.top_key} must be an object")

    required = set(definition.root_required)
    missing = required - set(root)
    if missing:
        raise ContractError(f"{definition.definition} missing required fields: {', '.join(sorted(missing))}")
    _reject_unknown(set(root), required | _OPTIONAL_ROOT_FIELDS.get(definition.definition, set()), definition.definition)

    if root.get("contract_version") != definition.version:
        raise ContractError(
            f"{definition.definition} contract_version must be {definition.version}, got {root.get('contract_version')!r}"
        )
    for field, expected in definition.const_fields.items():
        if root.get(field) != expected:
            raise ContractError(f"{definition.definition}.{field} must be {expected!r}, got {root.get(field)!r}")
    for field, allowed in definition.enum_fields.items():
        if root.get(field) not in allowed:
            raise ContractError(f"{definition.definition}.{field} must be one of {allowed!r}, got {root.get(field)!r}")
    for field in definition.digest_fields:
        value = root.get(field)
        if not isinstance(value, str) or not SHA256_HEX_RE.match(value):
            raise ContractError(f"{definition.definition}.{field} must be a sha256 hex string")
    _validate_json_value(payload, path=definition.definition)
    try:
        validate_wire_definition(definition.definition, payload)
    except SchemaValidationError as exc:
        raise ContractError(str(exc)) from exc


def _reject_unknown(actual: set[str], expected: set[str], name: str) -> None:
    unknown = actual - expected
    if unknown:
        raise ContractError(f"{name} unknown fields: {', '.join(sorted(unknown))}")


def _contract_type(contract_type: str | ContractType) -> ContractType:
    try:
        return ContractType(contract_type)
    except ValueError as exc:
        raise ContractError(f"unknown contract type: {contract_type}") from exc


def _validate_json_value(value: Any, *, path: str) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        raise ContractError(f"{path} contains unsupported binary float")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractError(f"{path} object keys must be strings")
            _validate_json_value(item, path=f"{path}.{key}")
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            _validate_json_value(item, path=f"{path}[{index}]")
        return
    raise ContractError(f"{path} contains unsupported value type: {type(value).__name__}")


def _copy_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Mapping):
        return {key: _copy_json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_copy_json_value(item) for item in value]
    raise ContractError(f"unsupported value type: {type(value).__name__}")


def _definition(
    contract_type: ContractType,
    version: int,
    definition: str,
    top_key: str,
    root_required: tuple[str, ...],
    *,
    const_fields: Mapping[str, Any] | None = None,
    enum_fields: Mapping[str, tuple[Any, ...]] | None = None,
    digest_fields: tuple[str, ...] = (),
) -> ContractDefinition:
    return ContractDefinition(
        contract_type=contract_type,
        version=version,
        definition=definition,
        top_key=top_key,
        root_required=root_required,
        const_fields={"contract_version": version, **dict(const_fields or {})},
        enum_fields=dict(enum_fields or {}),
        digest_fields=digest_fields,
    )


_DEFINITIONS: dict[ContractType, tuple[ContractDefinition, ...]] = {
    ContractType.COINS: (
        _definition(ContractType.COINS, 2, "COINS", "coins", ("contract_version", "event_id", "occurred_at", "symbols")),
    ),
    ContractType.MARKET_HANDOFF: (
        _definition(
            ContractType.MARKET_HANDOFF,
            4,
            "MARKET_HANDOFF",
            "market_handoff",
            (
                "contract_version",
                "decision_cycle_id",
                "set_result_id",
                "symbol",
                "created_at",
                "set_provenance",
                "snapshot",
                "instrument",
                "volatility",
                "reference_geometry",
                "entry_context",
                "sl_context",
                "tp_context",
                "set_numeric_policy_version",
            ),
            const_fields={"set_numeric_policy_version": "TT_SET_NUMERIC_V1"},
        ),
    ),
    ContractType.APPROVE_REJECT: (
        _definition(
            ContractType.APPROVE_REJECT,
            5,
            "APPROVE_REJECT.initial",
            "position_decision",
            (
                "contract_version",
                "event_variant",
                "event_id",
                "occurred_at",
                "position_decision_id",
                "decision_cycle_id",
                "set_result_id",
                "symbol",
                "decision",
                "reason_code",
                "opportunity_checks",
                "construction_gates",
            ),
            const_fields={"event_variant": "OPPORTUNITY_DECISION", "construction_gates": "NOT_YET_EVALUATED"},
            enum_fields={"decision": ("APPROVE", "REJECT")},
        ),
        _definition(
            ContractType.APPROVE_REJECT,
            5,
            "APPROVE_REJECT.constructed",
            "position_construction_result",
            (
                "contract_version",
                "event_variant",
                "event_id",
                "occurred_at",
                "position_decision_id",
                "construction_result_id",
                "capital_grant_id",
                "decision_cycle_id",
                "set_result_id",
                "symbol",
                "reason_code",
                "rule_results",
                "outcome",
                "position_plan_id",
                "tranche_id",
                "order_spec_id",
                "order_spec_digest",
                "approved_economics",
                "numeric_policy_version",
                "direction",
                "order_spec_contract_version",
            ),
            const_fields={
                "event_variant": "CONSTRUCTION_RESULT",
                "outcome": "CONSTRUCTED",
                "numeric_policy_version": "TT_NUMERIC_V1",
                "order_spec_contract_version": 5,
            },
            enum_fields={"direction": ("LONG", "SHORT")},
            digest_fields=("order_spec_digest",),
        ),
        _definition(
            ContractType.APPROVE_REJECT,
            5,
            "APPROVE_REJECT.failed",
            "position_construction_result",
            (
                "contract_version",
                "event_variant",
                "event_id",
                "occurred_at",
                "position_decision_id",
                "construction_result_id",
                "capital_grant_id",
                "decision_cycle_id",
                "set_result_id",
                "symbol",
                "reason_code",
                "rule_results",
                "outcome",
                "failed_gates",
            ),
            const_fields={"event_variant": "CONSTRUCTION_RESULT", "outcome": "REJECT"},
        ),
    ),
    ContractType.CAPITAL_AND_LIMITS: (
        _definition(
            ContractType.CAPITAL_AND_LIMITS,
            5,
            "CAPITAL_AND_LIMITS",
            "capital_and_limits",
            (
                "contract_version",
                "capital_grant_id",
                "position_decision_id",
                "decision_cycle_id",
                "set_result_id",
                "symbol",
                "created_at",
                "as_of",
                "grant_state_at_issue",
                "portfolio_state_revision",
                "requested_capital_per_tranche",
                "minimum_tranche_capital",
                "remaining_coin_capital",
                "remaining_global_capital",
                "remaining_coin_slots",
                "remaining_global_slots",
                "relevant_portfolio_limits",
                "accounting_policy",
                "venue_facts",
                "numeric_policy_version",
            ),
            const_fields={"grant_state_at_issue": "ISSUED", "numeric_policy_version": "TT_NUMERIC_V1"},
        ),
    ),
    ContractType.ORDER_SPEC: (
        _definition(
            ContractType.ORDER_SPEC,
            5,
            "ORDER_SPEC",
            "order_spec",
            (
                "contract_version",
                "order_spec_id",
                "spec_created_at",
                "capital_grant_id",
                "decision_cycle_id",
                "set_result_id",
                "position_decision_id",
                "construction_result_id",
                "position_plan_id",
                "tranche_id",
                "symbol",
                "direction",
                "side",
                "entry",
                "leverage",
                "take_profit",
                "stop_loss",
                "economics",
                "venue_validation",
                "accounting_policy",
                "provenance",
                "numeric_policy_version",
            ),
            const_fields={"numeric_policy_version": "TT_NUMERIC_V1"},
            enum_fields={"direction": ("LONG", "SHORT"), "side": ("BUY", "SELL")},
        ),
    ),
    ContractType.SUBMIT_AUTHORIZED: (
        _definition(
            ContractType.SUBMIT_AUTHORIZED,
            5,
            "SUBMIT_AUTHORIZED",
            "submit_authorized",
            (
                "contract_version",
                "authorization_id",
                "capital_grant_id",
                "decision_cycle_id",
                "set_result_id",
                "position_decision_id",
                "construction_result_id",
                "position_plan_id",
                "tranche_id",
                "order_spec_id",
                "symbol",
                "order_spec_digest",
                "held_committed_capital",
                "authorized_at",
                "numeric_policy_version",
                "order_spec_contract_version",
            ),
            const_fields={"numeric_policy_version": "TT_NUMERIC_V1", "order_spec_contract_version": 5},
            digest_fields=("order_spec_digest",),
        ),
    ),
    ContractType.ORDER_EVENT: (
        _definition(
            ContractType.ORDER_EVENT,
            7,
            "ORDER_EVENT.logical",
            "order_event",
            (
                "contract_version",
                "event_variant",
                "event_id",
                "event_type",
                "occurred_at",
                "lifecycle_revision",
                "authorization_id",
                "capital_grant_id",
                "decision_cycle_id",
                "set_result_id",
                "position_decision_id",
                "construction_result_id",
                "position_plan_id",
                "tranche_id",
                "order_spec_id",
                "symbol",
                "order_leg",
                "native_allocation",
                "lifecycle_state",
                "exposure_qty",
                "cumulative_entry_filled_qty",
                "remaining_entry_qty",
                "close_intent_active",
                "close_commitment_quantity_basis",
                "terminal_predicates",
                "external_cause",
                "financial_result",
                "entry_accepted_at",
                "entry_acceptance_status",
                "entry_acceptance_provenance",
                "numeric_policy_version",
                "entry_acceptance_integrity",
            ),
            const_fields={"event_variant": "LOGICAL_TRANCHE", "numeric_policy_version": "TT_NUMERIC_V1"},
            enum_fields={
                "lifecycle_state": (
                    "READY_TO_SUBMIT",
                    "SUBMITTING",
                    "SUBMISSION_UNCERTAIN",
                    "PENDING_ENTRY",
                    "PARTIALLY_FILLED",
                    "OPEN",
                    "CANCEL_PENDING",
                    "CANCELLED_ZERO_FILL",
                    "CLOSE_PENDING",
                    "CLOSED",
                    "SUBMISSION_FAILED",
                    "RECONCILING",
                    "MANUAL_INTERVENTION_REQUIRED",
                ),
                "entry_acceptance_status": ("PROVEN", "UNAVAILABLE", "NOT_APPLICABLE", "CONFLICT"),
            },
        ),
        _definition(
            ContractType.ORDER_EVENT,
            7,
            "ORDER_EVENT.native",
            "order_event",
            ("contract_version", "event_variant", "event_id", "event_type", "occurred_at", "native_observation"),
            const_fields={"event_variant": "NATIVE_UNATTRIBUTED_REDUCTION", "event_type": "NATIVE_EXPOSURE_REDUCTION_UNATTRIBUTED"},
        ),
        _definition(
            ContractType.ORDER_EVENT,
            7,
            "ORDER_EVENT.resolution",
            "order_event",
            ("contract_version", "event_variant", "event_id", "occurred_at", "resolution"),
            const_fields={"event_variant": "NATIVE_ATTRIBUTION_RESOLUTION"},
        ),
        _definition(
            ContractType.ORDER_EVENT,
            7,
            "ORDER_EVENT.scope_observation",
            "order_event",
            ("contract_version", "event_variant", "event_id", "event_type", "occurred_at", "native_observation"),
            const_fields={"event_variant": "NATIVE_SCOPE_RECONCILIATION_OBSERVED", "event_type": "NATIVE_SCOPE_RECONCILIATION_OBSERVED"},
        ),
        _definition(
            ContractType.ORDER_EVENT,
            7,
            "ORDER_EVENT.scope_resolution",
            "order_event",
            ("contract_version", "event_variant", "event_id", "occurred_at", "resolution"),
            const_fields={"event_variant": "NATIVE_SCOPE_RECONCILIATION_RESOLUTION"},
        ),
        _definition(
            ContractType.ORDER_EVENT,
            7,
            "ORDER_EVENT.integrity",
            "order_event",
            ("contract_version", "event_variant", "event_id", "integrity_incident"),
            const_fields={"event_variant": "POST_FINAL_INTEGRITY"},
        ),
    ),
    ContractType.ORDER_PLACED: (
        _definition(
            ContractType.ORDER_PLACED,
            3,
            "ORDER_PLACED.placed",
            "order_placed",
            (
                "contract_version",
                "event_id",
                "lifecycle_revision",
                "decision_cycle_id",
                "set_result_id",
                "position_plan_id",
                "tranche_id",
                "symbol",
                "client_order_link_id",
                "exchange_order_id",
                "order_placed_at",
            ),
        ),
        _definition(
            ContractType.ORDER_PLACED,
            3,
            "ORDER_PLACED.terminal",
            "entry_lifecycle_event",
            ("contract_version", "event_id", "lifecycle_revision", "decision_cycle_id", "set_result_id", "tranche_id", "symbol", "event_type", "occurred_at"),
            enum_fields={"event_type": ("FULL_FILL", "CANCELLED_ZERO_FILL", "ENTRY_REMAINDER_CANCELLED", "SUBMISSION_FAILED_AFTER_PLACEMENT_RECONCILIATION")},
        ),
    ),
    ContractType.ORDER_CANCEL_SIGNAL: (
        _definition(
            ContractType.ORDER_CANCEL_SIGNAL,
            2,
            "ORDER_CANCEL_SIGNAL",
            "order_cancel_signal",
            ("contract_version", "signal_id", "decision_cycle_id", "set_result_id", "tranche_id", "symbol", "invalidated_at", "reason_code"),
        ),
    ),
    ContractType.PORTFOLIO_DATA_REQUEST: (
        _definition(
            ContractType.PORTFOLIO_DATA_REQUEST,
            5,
            "PORTFOLIO_DATA_REQUEST.request",
            "portfolio_data_request",
            ("contract_version", "request_id", "requested_at", "request_mode", "scope", "filters"),
            enum_fields={"request_mode": ("SNAPSHOT", "HISTORY")},
        ),
        _definition(
            ContractType.PORTFOLIO_DATA_REQUEST,
            5,
            "PORTFOLIO_DATA_REQUEST.response",
            "portfolio_data_response",
            ("contract_version", "request_id", "response_id", "request_mode", "response_consistency", "snapshot_started_at", "snapshot_completed_at", "as_of", "source"),
            const_fields={"source": "exchange_api"},
            enum_fields={"request_mode": ("SNAPSHOT", "HISTORY")},
        ),
    ),
    ContractType.ORDER_MANAGEMENT: (
        *(
            _definition(
                ContractType.ORDER_MANAGEMENT,
                4,
                f"ORDER_MANAGEMENT.request.{operation}",
                "order_management_request",
                ("contract_version", "request_id", "operation", "requested_at", "correlation", "exchange_identity", "payload"),
                const_fields={"operation": operation},
            )
            for operation in (
                "CREATE_ENTRY_ORDER",
                "CANCEL_ENTRY_ORDER",
                "GET_ORDER",
                "GET_OPEN_ORDERS",
                "GET_ORDER_HISTORY",
                "GET_EXECUTIONS",
                "GET_POSITION",
                "SET_OR_ATTACH_TP_SL",
                "CANCEL_PROTECTIVE_ORDER",
                "CLOSE_POSITION_QUANTITY",
                "GET_ACCOUNT_EXECUTION_FACTS",
                "GET_FINANCIAL_FACTS",
                "GET_HARD_EXECUTION_FACTS",
            )
        ),
        _definition(
            ContractType.ORDER_MANAGEMENT,
            4,
            "ORDER_MANAGEMENT.response.financial",
            "order_management_response",
            ("contract_version", "request_id", "response_id", "operation", "as_of", "result", "financial_facts", "exchange_error"),
            const_fields={"operation": "GET_FINANCIAL_FACTS"},
            enum_fields={"result": ("COMPLETE", "PARTIAL", "UNAVAILABLE")},
        ),
        _definition(
            ContractType.ORDER_MANAGEMENT,
            4,
            "ORDER_MANAGEMENT.response.hard",
            "order_management_response",
            ("contract_version", "request_id", "response_id", "operation", "as_of", "result", "hard_execution_facts", "exchange_error"),
            const_fields={"operation": "GET_HARD_EXECUTION_FACTS"},
            enum_fields={"result": ("AVAILABLE", "UNAVAILABLE")},
        ),
        _definition(
            ContractType.ORDER_MANAGEMENT,
            4,
            "ORDER_MANAGEMENT.response.operation",
            "order_management_response",
            (
                "contract_version",
                "request_id",
                "response_id",
                "operation",
                "as_of",
                "result",
                "client_order_link_id",
                "exchange_order_id",
                "exchange_status",
                "orders",
                "executions",
                "position",
                "coverage",
                "exchange_error",
            ),
            enum_fields={
                "operation": (
                    "CREATE_ENTRY_ORDER",
                    "CANCEL_ENTRY_ORDER",
                    "GET_ORDER",
                    "GET_OPEN_ORDERS",
                    "GET_ORDER_HISTORY",
                    "GET_EXECUTIONS",
                    "GET_POSITION",
                    "SET_OR_ATTACH_TP_SL",
                    "CANCEL_PROTECTIVE_ORDER",
                    "CLOSE_POSITION_QUANTITY",
                    "GET_ACCOUNT_EXECUTION_FACTS",
                ),
                "result": ("ACCEPTED", "REJECTED", "AMBIGUOUS", "CANCEL_REQUEST_ACCEPTED", "ALREADY_TERMINAL", "AVAILABLE", "PARTIAL", "UNAVAILABLE"),
            },
        ),
    ),
    ContractType.MARKET_DATA_REQUEST: (
        _definition(
            ContractType.MARKET_DATA_REQUEST,
            3,
            "MARKET_DATA_REQUEST.request",
            "market_data_request",
            ("contract_version", "request_id", "requested_at", "symbol", "purpose", "selections"),
            enum_fields={"purpose": ("INITIAL_ANALYSIS", "PENDING_ORDER_MONITORING")},
        ),
        _definition(
            ContractType.MARKET_DATA_REQUEST,
            3,
            "MARKET_DATA_REQUEST.response",
            "market_data_response",
            ("contract_version", "request_id", "response_id", "symbol", "snapshot_started_at", "snapshot_completed_at", "as_of", "source", "selection_results"),
            const_fields={"source": "exchange_api"},
        ),
    ),
}


_OPTIONAL_ROOT_FIELDS: dict[str, set[str]] = {
    "PORTFOLIO_DATA_REQUEST.response": {
        "account",
        "positions",
        "open_orders",
        "recent_orders",
        "executions",
        "funding",
        "cashflows",
        "instrument_metadata",
        "fee_rates",
    },
    "MARKET_DATA_REQUEST.request": {"decision_cycle_id", "set_result_id"},
}
