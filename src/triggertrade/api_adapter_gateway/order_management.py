"""Order Management v4 factual envelope builders."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from triggertrade.contracts import ContractError, TargetContract, parse_contract


class OrderManagementGatewayError(ValueError):
    """Raised when Order Management facts cannot form an approved envelope."""


_REQUEST_OPERATIONS = {
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
}

_OPERATION_RESPONSE_OPERATIONS = _REQUEST_OPERATIONS - {"GET_FINANCIAL_FACTS", "GET_HARD_EXECUTION_FACTS"}


def build_order_management_request(
    *,
    request_id: str,
    operation: str,
    requested_at: datetime | str,
    correlation: Mapping[str, Any] | None,
    exchange_identity: Mapping[str, Any] | None = None,
    payload: Mapping[str, Any],
) -> TargetContract:
    operation = _operation(operation)
    body = {
        "contract_version": 4,
        "request_id": _text(request_id, field="request_id"),
        "operation": operation,
        "requested_at": _timestamp(requested_at),
        "correlation": None if correlation is None else _correlation(correlation),
        "exchange_identity": _exchange_identity(exchange_identity),
        "payload": _copy(payload, field="payload"),
    }
    return _parse({"order_management_request": body}, definition=f"ORDER_MANAGEMENT.request.{operation}")


def build_order_management_operation_response(
    *,
    request_id: str,
    response_id: str,
    operation: str,
    as_of: datetime | str,
    result: str,
    client_order_link_id: str | None = None,
    exchange_order_id: str | None = None,
    exchange_status: str | None = None,
    orders: Sequence[Mapping[str, Any]] = (),
    executions: Sequence[Mapping[str, Any]] = (),
    position: Mapping[str, Any] | None = None,
    coverage: Mapping[str, Any] | None = None,
    exchange_error: Mapping[str, Any] | None = None,
) -> TargetContract:
    operation = _operation(operation)
    if operation not in _OPERATION_RESPONSE_OPERATIONS:
        raise OrderManagementGatewayError(f"{operation} requires a specialized Order Management response")
    body = {
        "contract_version": 4,
        "request_id": _text(request_id, field="request_id"),
        "response_id": _text(response_id, field="response_id"),
        "operation": operation,
        "as_of": _timestamp(as_of),
        "result": result,
        "client_order_link_id": _optional_text(client_order_link_id, field="client_order_link_id"),
        "exchange_order_id": _optional_text(exchange_order_id, field="exchange_order_id"),
        "exchange_status": _optional_text(exchange_status, field="exchange_status"),
        "orders": [_copy(order, field="orders") for order in orders],
        "executions": [_copy(execution, field="executions") for execution in executions],
        "position": None if position is None else _copy(position, field="position"),
        "coverage": None if coverage is None else _copy(coverage, field="coverage"),
        "exchange_error": None if exchange_error is None else _copy(exchange_error, field="exchange_error"),
    }
    return _parse({"order_management_response": body}, definition="ORDER_MANAGEMENT.response.operation")


def build_order_management_hard_response(
    *,
    request_id: str,
    response_id: str,
    as_of: datetime | str,
    result: str,
    hard_execution_facts: Mapping[str, Any] | None,
    exchange_error: Mapping[str, Any] | None = None,
) -> TargetContract:
    body = {
        "contract_version": 4,
        "request_id": _text(request_id, field="request_id"),
        "response_id": _text(response_id, field="response_id"),
        "operation": "GET_HARD_EXECUTION_FACTS",
        "as_of": _timestamp(as_of),
        "result": result,
        "hard_execution_facts": None if hard_execution_facts is None else _copy(hard_execution_facts, field="hard_execution_facts"),
        "exchange_error": None if exchange_error is None else _copy(exchange_error, field="exchange_error"),
    }
    return _parse({"order_management_response": body}, definition="ORDER_MANAGEMENT.response.hard")


def build_order_management_financial_response(
    *,
    request_id: str,
    response_id: str,
    as_of: datetime | str,
    result: str,
    financial_facts: Mapping[str, Any],
    exchange_error: Mapping[str, Any] | None = None,
) -> TargetContract:
    body = {
        "contract_version": 4,
        "request_id": _text(request_id, field="request_id"),
        "response_id": _text(response_id, field="response_id"),
        "operation": "GET_FINANCIAL_FACTS",
        "as_of": _timestamp(as_of),
        "result": result,
        "financial_facts": _copy(financial_facts, field="financial_facts"),
        "exchange_error": None if exchange_error is None else _copy(exchange_error, field="exchange_error"),
    }
    return _parse({"order_management_response": body}, definition="ORDER_MANAGEMENT.response.financial")


def build_hard_execution_facts(
    *,
    instrument: Mapping[str, Any],
    native_configured_leverage: Decimal | str | int | None,
    supported_native_profile: bool,
    facts_complete: bool,
    checked_at: datetime | str,
    source_ref: str,
) -> dict[str, Any]:
    return {
        "instrument": _copy(instrument, field="instrument"),
        "native_configured_leverage": None
        if native_configured_leverage is None
        else _decimal_text(native_configured_leverage, field="native_configured_leverage"),
        "supported_native_profile": _bool(supported_native_profile, field="supported_native_profile"),
        "facts_complete": _bool(facts_complete, field="facts_complete"),
        "checked_at": _timestamp(checked_at),
        "source_ref": _text(source_ref, field="source_ref"),
    }


def coverage_certificate(
    *,
    status: str,
    coverage_from: datetime | str,
    coverage_to: datetime | str,
    missing_ranges: Sequence[Mapping[str, Any]] = (),
    pagination_complete: bool,
    next_cursor: str | None,
    source_watermark_at: datetime | str | None,
    source_finality_confirmed: bool,
    source_endpoints: Sequence[str],
    reason_code: str | None = None,
) -> dict[str, Any]:
    if status not in {"COMPLETE", "PARTIAL", "UNAVAILABLE"}:
        raise OrderManagementGatewayError("coverage status must be COMPLETE, PARTIAL, or UNAVAILABLE")
    if not isinstance(pagination_complete, bool) or not isinstance(source_finality_confirmed, bool):
        raise OrderManagementGatewayError("coverage flags must be boolean")
    if status == "COMPLETE":
        if missing_ranges or not pagination_complete or next_cursor is not None or not source_finality_confirmed:
            raise OrderManagementGatewayError("COMPLETE coverage requires no missing ranges, exhausted pagination, and source finality")
    if status == "UNAVAILABLE" and reason_code is None:
        raise OrderManagementGatewayError("UNAVAILABLE coverage requires reason_code")
    return {
        "status": status,
        "coverage_from": _timestamp(coverage_from),
        "coverage_to": _timestamp(coverage_to),
        "missing_ranges": [_time_range(item) for item in missing_ranges],
        "pagination_complete": pagination_complete,
        "next_cursor": _optional_text(next_cursor, field="next_cursor"),
        "source_watermark_at": None if source_watermark_at is None else _timestamp(source_watermark_at),
        "source_finality_confirmed": source_finality_confirmed,
        "source_endpoints": [_text(item, field="source_endpoint") for item in source_endpoints],
        "reason_code": _optional_text(reason_code, field="reason_code"),
    }


def component_coverage_certificate(
    *,
    component: str,
    applicable: bool,
    not_applicable_evidence: str | None,
    coverage: Mapping[str, Any],
) -> dict[str, Any]:
    if component not in {"EXECUTIONS", "TRADING_FEE", "FUNDING", "OTHER_EXCHANGE_COST"}:
        raise OrderManagementGatewayError("unsupported financial coverage component")
    if not isinstance(applicable, bool):
        raise OrderManagementGatewayError("applicable must be boolean")
    if not applicable and not not_applicable_evidence:
        raise OrderManagementGatewayError("not-applicable component coverage requires evidence")
    return {
        "component": component,
        "applicable": applicable,
        "not_applicable_evidence": _optional_text(not_applicable_evidence, field="not_applicable_evidence"),
        "coverage": _copy(coverage, field="coverage"),
    }


def normalize_magnitude_with_direction(*, magnitude: Decimal | str | int, direction: str) -> str:
    amount = _decimal_value(magnitude, field="magnitude")
    if amount < 0:
        raise OrderManagementGatewayError("magnitude cannot be negative")
    if direction not in {"DEBIT", "CREDIT", "ZERO"}:
        raise OrderManagementGatewayError("economic_direction must be DEBIT, CREDIT, or ZERO")
    if amount == 0:
        if direction != "ZERO":
            raise OrderManagementGatewayError("zero magnitude requires ZERO direction")
        return "0"
    if direction == "ZERO":
        raise OrderManagementGatewayError("nonzero magnitude cannot use ZERO direction")
    return _decimal_to_text(amount if direction == "CREDIT" else -amount)


def financial_record(
    *,
    cashflow_id: str,
    component_type: str,
    currency: str,
    source_amount: Decimal | str | int,
    source_sign_convention: str,
    economic_direction: str,
    effective_at: datetime | str,
    recorded_at: datetime | str,
    source_endpoint: str,
    source_record_id: str,
    source_field: str,
    amount_quantum: Decimal | str | int,
    normalization_profile_version: str,
    transaction_id: str | None = None,
    execution_id: str | None = None,
    symbol: str | None = None,
    native_side: str | None = None,
    position_idx: int | None = None,
    client_order_link_id: str | None = None,
    exchange_order_id: str | None = None,
    parent_exchange_order_id: str | None = None,
    child_id: str | None = None,
    fee_classification: str = "NOT_APPLICABLE",
    funding_classification: str = "NOT_APPLICABLE",
    cost_classification: str = "NOT_APPLICABLE",
    aliases: Sequence[Mapping[str, Any]] = (),
    settlement_price: Decimal | str | int | None = None,
    settlement_price_basis: str | None = None,
    settlement_price_as_of: datetime | str | None = None,
    settlement_source_ref: str | None = None,
    pnl_scope: str = "NOT_APPLICABLE",
    period_scope: str = "NOT_APPLICABLE",
) -> dict[str, Any]:
    signed_amount = _signed_amount(
        source_amount=source_amount,
        source_sign_convention=source_sign_convention,
        economic_direction=economic_direction,
    )
    return {
        "cashflow_id": _text(cashflow_id, field="cashflow_id"),
        "transaction_id": _optional_text(transaction_id, field="transaction_id"),
        "execution_id": _optional_text(execution_id, field="execution_id"),
        "component_type": _enum(
            component_type,
            {"TRADING_FEE", "FUNDING", "REALIZED_TRADING_PNL", "OTHER_EXCHANGE_COST", "DEPOSIT", "WITHDRAWAL"},
            field="component_type",
        ),
        "currency": _text(currency, field="currency"),
        "signed_amount": signed_amount,
        "amount_quantum": _unsigned_decimal_text(amount_quantum, field="amount_quantum"),
        "effective_at": _timestamp(effective_at),
        "recorded_at": _timestamp(recorded_at),
        "symbol": _optional_text(symbol, field="symbol"),
        "native_side": None if native_side is None else _side(native_side),
        "position_idx": None if position_idx is None else _int(position_idx, field="position_idx"),
        "client_order_link_id": _optional_text(client_order_link_id, field="client_order_link_id"),
        "exchange_order_id": _optional_text(exchange_order_id, field="exchange_order_id"),
        "parent_exchange_order_id": _optional_text(parent_exchange_order_id, field="parent_exchange_order_id"),
        "child_id": _optional_text(child_id, field="child_id"),
        "fee_classification": _enum(fee_classification, {"FEE", "REBATE", "NOT_APPLICABLE"}, field="fee_classification"),
        "funding_classification": _enum(
            funding_classification,
            {"PAYMENT", "RECEIPT", "NOT_APPLICABLE"},
            field="funding_classification",
        ),
        "cost_classification": _enum(cost_classification, {"COST", "REFUND", "NOT_APPLICABLE"}, field="cost_classification"),
        "source_endpoint": _text(source_endpoint, field="source_endpoint"),
        "source_record_id": _text(source_record_id, field="source_record_id"),
        "source_field": _text(source_field, field="source_field"),
        "source_amount": _decimal_text(source_amount, field="source_amount"),
        "source_sign_convention": _enum(
            source_sign_convention,
            {"COST_POSITIVE", "CREDIT_POSITIVE", "MAGNITUDE_WITH_DIRECTION"},
            field="source_sign_convention",
        ),
        "economic_direction": _enum(economic_direction, {"DEBIT", "CREDIT", "ZERO"}, field="economic_direction"),
        "normalization_profile_version": _text(normalization_profile_version, field="normalization_profile_version"),
        "aliases": [_financial_alias(alias) for alias in aliases],
        "settlement_price": None if settlement_price is None else _unsigned_decimal_text(settlement_price, field="settlement_price"),
        "settlement_price_basis": _optional_text(settlement_price_basis, field="settlement_price_basis"),
        "settlement_price_as_of": None if settlement_price_as_of is None else _timestamp(settlement_price_as_of),
        "settlement_source_ref": _optional_text(settlement_source_ref, field="settlement_source_ref"),
        "pnl_scope": _enum(pnl_scope, {"GROSS", "NET", "NOT_APPLICABLE"}, field="pnl_scope"),
        "period_scope": _enum(period_scope, {"EVENT", "INTERVAL", "LIFETIME", "NOT_APPLICABLE"}, field="period_scope"),
    }


def financial_facts(
    *,
    native_scope: Mapping[str, Any],
    requested_from: datetime | str,
    requested_to: datetime | str,
    coverage: Mapping[str, Any],
    component_coverage: Sequence[Mapping[str, Any]],
    executions: Sequence[Mapping[str, Any]] = (),
    cashflows: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    return {
        "native_scope": _copy(native_scope, field="native_scope"),
        "requested_from": _timestamp(requested_from),
        "requested_to": _timestamp(requested_to),
        "coverage": _copy(coverage, field="coverage"),
        "component_coverage": [_copy(item, field="component_coverage") for item in component_coverage],
        "executions": [_copy(item, field="executions") for item in executions],
        "cashflows": [_copy(item, field="cashflows") for item in cashflows],
    }


def order_fact_from_bybit(
    raw: Mapping[str, Any],
    *,
    source_endpoint: str,
    mapping_profile_version: str,
    evidence_ref: str,
) -> dict[str, Any]:
    source_record_id = _source_record_id(raw, fallback_fields=("orderId", "orderLinkId"))
    order_id = _text(raw.get("orderId"), field="orderId")
    symbol = _text(raw.get("symbol"), field="symbol")
    qty = _decimal_text(raw.get("qty") or raw.get("quantity") or "0", field="qty")
    cum = _decimal_text(raw.get("cumExecQty") or raw.get("cumExecQuantity") or "0", field="cumExecQty")
    remaining = _nonnegative_difference(qty, cum)
    created_at = _bybit_time(raw.get("createdTime"))
    updated_at = _bybit_time(raw.get("updatedTime")) or created_at
    return {
        "client_order_link_id": _optional_text(raw.get("orderLinkId"), field="orderLinkId"),
        "exchange_order_id": order_id,
        "symbol": symbol,
        "native_side": _side(raw.get("side")),
        "position_idx": _int(raw.get("positionIdx") or 0, field="positionIdx"),
        "status": _text(raw.get("orderStatus") or raw.get("status"), field="orderStatus"),
        "cumulative_filled_quantity": cum,
        "remaining_quantity": remaining,
        "average_fill_price": _optional_decimal(raw.get("avgPrice"), field="avgPrice"),
        "updated_at": updated_at or _required_bybit_time(raw.get("updatedTime"), field="updatedTime"),
        "source_ref": f"{source_endpoint}:{source_record_id}",
        "native_parent_order_id": _optional_text(raw.get("parentOrderId"), field="parentOrderId"),
        "native_parent_client_order_link_id": _optional_text(raw.get("parentOrderLinkId"), field="parentOrderLinkId"),
        "native_link_group_id": _optional_text(raw.get("orderLinkId"), field="orderLinkId"),
        "order_role": _order_role(raw),
        "order_side": _optional_side(raw.get("side")),
        "order_type": _optional_order_type(raw.get("orderType")),
        "order_quantity": qty,
        "order_price": _optional_decimal(raw.get("price"), field="price"),
        "trigger_price": _optional_decimal(raw.get("triggerPrice"), field="triggerPrice"),
        "trigger_direction": _trigger_direction(raw.get("triggerDirection")),
        "trigger_type": "CONDITIONAL_PRICE" if raw.get("triggerPrice") not in {None, "", "0"} else "NOT_APPLICABLE",
        "trigger_source": _trigger_source(raw.get("triggerBy")),
        "protected_qty": _optional_decimal(raw.get("tpslModeQty") or raw.get("qty"), field="protected_qty")
        if _order_role(raw) in {"TP", "SL"}
        else None,
        "protection_scope": "PARTIAL_QUANTITY" if _order_role(raw) in {"TP", "SL"} else None,
        "reduce_only": _optional_bool(raw.get("reduceOnly"), field="reduceOnly"),
        "close_on_trigger": _optional_bool(raw.get("closeOnTrigger"), field="closeOnTrigger"),
        "native_position_mode": "HEDGE_MODE" if _int(raw.get("positionIdx") or 0, field="positionIdx") in {1, 2} else "ONE_WAY_MODE",
        "stop_order_type": _optional_text(raw.get("stopOrderType"), field="stopOrderType"),
        "native_create_type": _optional_text(raw.get("createType"), field="createType"),
        "native_created_at": created_at,
        "entry_accepted_at": None,
        "entry_acceptance_status": "UNAVAILABLE",
        "entry_acceptance_provenance": None,
        "source_endpoint": _text(source_endpoint, field="source_endpoint"),
        "source_record_id": source_record_id,
        "native_fact_provenance": [
            native_field_provenance(
                normalized_field="status",
                source_endpoint=source_endpoint,
                source_record_id=source_record_id,
                source_field="orderStatus",
                native_value=str(raw.get("orderStatus") or raw.get("status") or ""),
                mapping_profile_version=mapping_profile_version,
                evidence_ref=evidence_ref,
            ),
            native_field_provenance(
                normalized_field="cumulative_filled_quantity",
                source_endpoint=source_endpoint,
                source_record_id=source_record_id,
                source_field="cumExecQty",
                native_value=str(raw.get("cumExecQty") or ""),
                mapping_profile_version=mapping_profile_version,
                evidence_ref=evidence_ref,
            ),
        ],
    }


def execution_fact_from_bybit(
    raw: Mapping[str, Any],
    *,
    source_endpoint: str,
    mapping_profile_version: str,
    evidence_ref: str,
) -> dict[str, Any]:
    source_record_id = _source_record_id(raw, fallback_fields=("execId", "orderId", "orderLinkId"))
    return {
        "execution_id": _text(raw.get("execId"), field="execId"),
        "client_order_link_id": _optional_text(raw.get("orderLinkId"), field="orderLinkId"),
        "exchange_order_id": _text(raw.get("orderId"), field="orderId"),
        "parent_exchange_order_id": _optional_text(raw.get("parentOrderId"), field="parentOrderId"),
        "symbol": _text(raw.get("symbol"), field="symbol"),
        "native_side": _side(raw.get("side")),
        "position_idx": _int(raw.get("positionIdx") or 0, field="positionIdx"),
        "order_side": _side(raw.get("side")),
        "quantity": _decimal_text(raw.get("execQty"), field="execQty"),
        "price": _decimal_text(raw.get("execPrice"), field="execPrice"),
        "executed_at": _required_bybit_time(raw.get("execTime"), field="execTime"),
        "native_sequence": _optional_text(raw.get("seq"), field="seq"),
        "fee_cashflow_id": _optional_text(raw.get("execId"), field="execId"),
        "source_endpoint": _text(source_endpoint, field="source_endpoint"),
        "source_record_id": source_record_id,
        "native_sequence_domain": _optional_text(raw.get("symbol"), field="symbol"),
        "native_subsequence": _optional_text(raw.get("execId"), field="execId"),
        "chronology_profile_version": _text(mapping_profile_version, field="mapping_profile_version"),
        "chronology_provenance": native_field_provenance(
            normalized_field="executed_at",
            source_endpoint=source_endpoint,
            source_record_id=source_record_id,
            source_field="execTime",
            native_value=str(raw.get("execTime") or ""),
            mapping_profile_version=mapping_profile_version,
            evidence_ref=evidence_ref,
        ),
    }


def native_field_provenance(
    *,
    normalized_field: str,
    source_endpoint: str,
    source_record_id: str,
    source_field: str,
    native_value: str,
    mapping_profile_version: str,
    evidence_ref: str,
) -> dict[str, Any]:
    return {
        "normalized_field": _text(normalized_field, field="normalized_field"),
        "source_endpoint": _text(source_endpoint, field="source_endpoint"),
        "source_record_id": _text(source_record_id, field="source_record_id"),
        "source_field": _text(source_field, field="source_field"),
        "native_value": str(native_value),
        "mapping_profile_version": _text(mapping_profile_version, field="mapping_profile_version"),
        "evidence_ref": _text(evidence_ref, field="evidence_ref"),
    }


def exchange_error(*, code: str, message: str, retryable: bool, category: str) -> dict[str, Any]:
    return {
        "code": _text(code, field="code"),
        "message": _text(message, field="message"),
        "retryable": _bool(retryable, field="retryable"),
        "category": category,
    }


def _parse(payload: Mapping[str, Any], *, definition: str) -> TargetContract:
    try:
        return parse_contract("ORDER_MANAGEMENT", payload, definition=definition)
    except ContractError as exc:
        raise OrderManagementGatewayError(str(exc)) from exc


def _operation(value: str) -> str:
    if value not in _REQUEST_OPERATIONS:
        raise OrderManagementGatewayError(f"unsupported Order Management operation: {value}")
    return value


def _correlation(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "authorization_id": _optional_text(value.get("authorization_id"), field="authorization_id"),
        "capital_grant_id": _text(value.get("capital_grant_id"), field="capital_grant_id"),
        "decision_cycle_id": _text(value.get("decision_cycle_id"), field="decision_cycle_id"),
        "set_result_id": _text(value.get("set_result_id"), field="set_result_id"),
        "position_decision_id": _text(value.get("position_decision_id"), field="position_decision_id"),
        "construction_result_id": _text(value.get("construction_result_id"), field="construction_result_id"),
        "position_plan_id": _text(value.get("position_plan_id"), field="position_plan_id"),
        "tranche_id": _text(value.get("tranche_id"), field="tranche_id"),
        "order_spec_id": _text(value.get("order_spec_id"), field="order_spec_id"),
        "symbol": _text(value.get("symbol"), field="symbol"),
    }


def _exchange_identity(value: Mapping[str, Any] | None) -> dict[str, Any]:
    values = {} if value is None else value
    return {
        "client_order_link_id": _optional_text(values.get("client_order_link_id"), field="client_order_link_id"),
        "exchange_order_id": _optional_text(values.get("exchange_order_id"), field="exchange_order_id"),
    }


def _copy(value: Mapping[str, Any], *, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise OrderManagementGatewayError(f"{field} must be an object")
    return dict(value)


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise OrderManagementGatewayError(f"{field} is required")
    return value


def _optional_text(value: object, *, field: str) -> str | None:
    if value in {None, ""}:
        return None
    return _text(value, field=field)


def _timestamp(value: datetime | str) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return _text(value, field="timestamp")


def _bybit_time(value: object) -> str | None:
    if value in {None, ""}:
        return None
    digits = str(value)
    try:
        millis = int(digits)
    except ValueError as exc:
        raise OrderManagementGatewayError("Bybit timestamp must be epoch milliseconds") from exc
    return datetime.fromtimestamp(millis / 1000, UTC).isoformat().replace("+00:00", "Z")


def _required_bybit_time(value: object, *, field: str) -> str:
    resolved = _bybit_time(value)
    if resolved is None:
        raise OrderManagementGatewayError(f"{field} is required")
    return resolved


def _decimal_text(value: object, *, field: str) -> str:
    if isinstance(value, float):
        raise OrderManagementGatewayError(f"{field} must be an exact decimal string")
    if value in {None, ""}:
        raise OrderManagementGatewayError(f"{field} is required")
    try:
        decimal = Decimal(str(value))
    except InvalidOperation as exc:
        raise OrderManagementGatewayError(f"{field} must be an exact decimal string") from exc
    if not decimal.is_finite() or decimal < 0:
        raise OrderManagementGatewayError(f"{field} must be a finite nonnegative decimal string")
    return format(decimal.normalize(), "f") if decimal != 0 else "0"


def _optional_decimal(value: object, *, field: str) -> str | None:
    if value in {None, ""}:
        return None
    return _decimal_text(value, field=field)


def _unsigned_decimal_text(value: object, *, field: str) -> str:
    decimal = _decimal_value(value, field=field)
    if decimal < 0:
        raise OrderManagementGatewayError(f"{field} must be nonnegative")
    return _decimal_to_text(decimal)


def _decimal_value(value: object, *, field: str) -> Decimal:
    if isinstance(value, float):
        raise OrderManagementGatewayError(f"{field} must be an exact decimal string")
    if value in {None, ""}:
        raise OrderManagementGatewayError(f"{field} is required")
    try:
        decimal = Decimal(str(value))
    except InvalidOperation as exc:
        raise OrderManagementGatewayError(f"{field} must be an exact decimal string") from exc
    if not decimal.is_finite():
        raise OrderManagementGatewayError(f"{field} must be finite")
    return decimal


def _decimal_to_text(value: Decimal) -> str:
    return format(value.normalize(), "f") if value != 0 else "0"


def _signed_amount(
    *,
    source_amount: Decimal | str | int,
    source_sign_convention: str,
    economic_direction: str,
) -> str:
    amount = _decimal_value(source_amount, field="source_amount")
    if source_sign_convention == "MAGNITUDE_WITH_DIRECTION":
        return normalize_magnitude_with_direction(magnitude=amount, direction=economic_direction)
    if economic_direction not in {"DEBIT", "CREDIT", "ZERO"}:
        raise OrderManagementGatewayError("economic_direction must be DEBIT, CREDIT, or ZERO")
    if source_sign_convention == "COST_POSITIVE":
        return _decimal_to_text(-amount)
    if source_sign_convention == "CREDIT_POSITIVE":
        return _decimal_to_text(amount)
    raise OrderManagementGatewayError("unsupported source_sign_convention")


def _nonnegative_difference(left: str, right: str) -> str:
    result = Decimal(left) - Decimal(right)
    if result < 0:
        raise OrderManagementGatewayError("remaining quantity cannot be negative")
    return format(result.normalize(), "f") if result != 0 else "0"


def _int(value: object, *, field: str) -> int:
    try:
        resolved = int(str(value))
    except (TypeError, ValueError) as exc:
        raise OrderManagementGatewayError(f"{field} must be an integer") from exc
    if resolved < 0:
        raise OrderManagementGatewayError(f"{field} must be nonnegative")
    return resolved


def _bool(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise OrderManagementGatewayError(f"{field} must be a boolean")
    return value


def _optional_bool(value: object, *, field: str) -> bool | None:
    if value in {None, ""}:
        return None
    if isinstance(value, bool):
        return value
    if str(value).lower() in {"true", "1"}:
        return True
    if str(value).lower() in {"false", "0"}:
        return False
    raise OrderManagementGatewayError(f"{field} must be a boolean")


def _side(value: object) -> str:
    side = _text(value, field="side").upper()
    if side not in {"BUY", "SELL"}:
        raise OrderManagementGatewayError("side must be BUY or SELL")
    return side


def _optional_side(value: object) -> str | None:
    if value in {None, ""}:
        return None
    return _side(value)


def _optional_order_type(value: object) -> str | None:
    if value in {None, ""}:
        return None
    normalized = _text(value, field="orderType").upper()
    if normalized not in {"LIMIT", "MARKET"}:
        raise OrderManagementGatewayError("orderType must be LIMIT or MARKET")
    return normalized


def _trigger_direction(value: object) -> str | None:
    if value in {None, "", 0, "0"}:
        return "NOT_APPLICABLE"
    normalized = str(value).upper()
    if normalized in {"1", "RISE"}:
        return "RISE"
    if normalized in {"2", "FALL"}:
        return "FALL"
    raise OrderManagementGatewayError("triggerDirection must be 1/RISE, 2/FALL, or not applicable")


def _trigger_source(value: object) -> str | None:
    if value in {None, ""}:
        return "NOT_APPLICABLE"
    normalized = str(value).upper()
    aliases = {"LASTPRICE": "LAST_PRICE", "MARKPRICE": "MARK_PRICE", "INDEXPRICE": "INDEX_PRICE"}
    resolved = aliases.get(normalized, normalized)
    if resolved not in {"LAST_PRICE", "MARK_PRICE", "INDEX_PRICE", "NOT_APPLICABLE"}:
        raise OrderManagementGatewayError("triggerBy must be LAST_PRICE, MARK_PRICE, INDEX_PRICE, or not applicable")
    return resolved


def _order_role(raw: Mapping[str, Any]) -> str:
    stop_order_type = str(raw.get("stopOrderType") or "").upper()
    if stop_order_type in {"TAKEPROFIT", "TAKE_PROFIT"}:
        return "TP"
    if stop_order_type in {"STOPLOSS", "STOP_LOSS"}:
        return "SL"
    return "UNKNOWN"


def _source_record_id(raw: Mapping[str, Any], *, fallback_fields: Sequence[str]) -> str:
    parts = [_optional_text(raw.get(field), field=field) for field in fallback_fields]
    resolved = tuple(part for part in parts if part is not None)
    if resolved:
        return ":".join(resolved)
    raise OrderManagementGatewayError("source record identity is required")


def _time_range(value: Mapping[str, Any]) -> dict[str, str]:
    return {"from": _timestamp(value["from"]), "to": _timestamp(value["to"])}


def _financial_alias(value: Mapping[str, Any]) -> dict[str, str]:
    alias = _copy(value, field="alias")
    return {
        "source_endpoint": _text(alias.get("source_endpoint"), field="source_endpoint"),
        "source_record_id": _text(alias.get("source_record_id"), field="source_record_id"),
        "source_field": _text(alias.get("source_field"), field="source_field"),
    }


def _enum(value: str, allowed: set[str], *, field: str) -> str:
    text = _text(value, field=field)
    if text not in allowed:
        raise OrderManagementGatewayError(f"{field} must be one of {', '.join(sorted(allowed))}")
    return text
