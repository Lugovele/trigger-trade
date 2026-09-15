from __future__ import annotations

import pytest

from triggertrade.api_adapter_gateway import (
    OrderManagementGatewayError,
    build_order_management_operation_response,
    build_order_management_request,
    execution_fact_from_bybit,
    order_fact_from_bybit,
)
from triggertrade.contracts import ContractError, implemented_contract_registry, parse_contract
from tests.unit.test_order_management_gateway import (
    FIXED_AT,
    _bybit_execution,
    _bybit_order,
    _correlation,
    _entry_payload,
)
from tests.unit.test_target_contracts import valid_payload


def test_order_management_gateway_matches_approved_current_definitions():
    definitions = set(implemented_contract_registry()["ORDER_MANAGEMENT"]["definitions"])

    assert definitions == {
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
        "ORDER_MANAGEMENT.response.financial",
        "ORDER_MANAGEMENT.response.hard",
        "ORDER_MANAGEMENT.response.operation",
    }


@pytest.mark.parametrize(
    "operation",
    [
        "CREATE_ENTRY_ORDER",
        "CANCEL_ENTRY_ORDER",
        "GET_ORDER",
        "GET_OPEN_ORDERS",
        "GET_ORDER_HISTORY",
        "GET_EXECUTIONS",
        "GET_POSITION",
        "GET_ACCOUNT_EXECUTION_FACTS",
        "GET_FINANCIAL_FACTS",
        "GET_HARD_EXECUTION_FACTS",
    ],
)
def test_representative_order_management_requests_validate(operation: str):
    payload = {
        "CREATE_ENTRY_ORDER": _entry_payload,
        "GET_FINANCIAL_FACTS": _financial_payload,
        "GET_HARD_EXECUTION_FACTS": _hard_payload,
    }.get(operation, _lookup_payload)()
    parsed = build_order_management_request(
        request_id=f"om-req-{operation.lower()}",
        operation=operation,
        requested_at=FIXED_AT,
        correlation=_correlation(),
        exchange_identity={"client_order_link_id": "cl-1", "exchange_order_id": "bybit-order-1"},
        payload=payload,
    )

    assert parsed.definition == f"ORDER_MANAGEMENT.request.{operation}"


def test_representative_protection_and_close_requests_validate():
    protection = build_order_management_request(
        request_id="om-req-protection",
        operation="SET_OR_ATTACH_TP_SL",
        requested_at=FIXED_AT,
        correlation=_correlation(),
        payload=_protection_payload(),
    )
    close = build_order_management_request(
        request_id="om-req-close",
        operation="CLOSE_POSITION_QUANTITY",
        requested_at=FIXED_AT,
        correlation=_correlation(),
        payload=_close_child_payload(),
    )

    assert protection.definition == "ORDER_MANAGEMENT.request.SET_OR_ATTACH_TP_SL"
    assert close.definition == "ORDER_MANAGEMENT.request.CLOSE_POSITION_QUANTITY"


def test_operation_response_rejects_unapproved_response_operation():
    with pytest.raises(OrderManagementGatewayError, match="specialized Order Management response"):
        build_order_management_operation_response(
            request_id="om-req-financial",
            response_id="om-resp-financial",
            operation="GET_FINANCIAL_FACTS",
            as_of=FIXED_AT,
            result="AVAILABLE",
        )


def test_order_management_response_unknown_fields_fail_schema_validation():
    payload = valid_payload("ORDER_MANAGEMENT", "ORDER_MANAGEMENT.response.operation")
    payload["order_management_response"]["unexpected"] = "x"

    with pytest.raises(ContractError, match="unknown fields: unexpected"):
        parse_contract("ORDER_MANAGEMENT", payload, definition="ORDER_MANAGEMENT.response.operation")


def test_bybit_facts_validate_against_approved_operation_response_schema():
    order_fact = order_fact_from_bybit(
        _bybit_order(),
        source_endpoint="/v5/order/realtime",
        mapping_profile_version="bybit-linear-order-facts-v1",
        evidence_ref="evidence://order/realtime/1",
    )
    execution_fact = execution_fact_from_bybit(
        _bybit_execution(),
        source_endpoint="/v5/execution/list",
        mapping_profile_version="bybit-linear-execution-facts-v1",
        evidence_ref="evidence://execution/1",
    )

    parsed = build_order_management_operation_response(
        request_id="om-req-1",
        response_id="om-resp-1",
        operation="GET_EXECUTIONS",
        as_of=FIXED_AT,
        result="AVAILABLE",
        orders=[order_fact],
        executions=[execution_fact],
    )

    assert parsed.to_payload()["order_management_response"]["executions"][0]["execution_id"] == "exec-1"


def _lookup_payload() -> dict[str, object]:
    return {
        "symbol": "BTCUSDT",
        "native_side": "BUY",
        "position_idx": 1,
        "client_order_link_id": "cl-1",
        "exchange_order_id": "bybit-order-1",
        "since": None,
        "until": None,
        "cursor": None,
    }


def _financial_payload() -> dict[str, object]:
    return {
        "native_scope": {
            "account_id": "account-1",
            "environment": "TEST",
            "symbol": "BTCUSDT",
            "native_side": "BUY",
            "position_idx": 1,
        },
        "coverage_from": "2026-09-14T00:00:00Z",
        "coverage_to": "2026-09-14T01:00:00Z",
        "required_components": ["EXECUTIONS", "TRADING_FEE"],
        "exchange_order_ids": ["bybit-order-1"],
        "client_order_link_ids": ["cl-1"],
        "execution_ids": [],
        "cashflow_ids": [],
        "cursor": None,
    }


def _hard_payload() -> dict[str, object]:
    return {
        "symbol": "BTCUSDT",
        "native_side": "BUY",
        "position_idx": 1,
        "approved_metadata_revision": "metadata-v1",
        "approved_native_profile_revision": "native-profile-v1",
        "order_spec_id": "spec-1",
    }


def _protection_payload() -> dict[str, object]:
    return {
        "tranche_id": "tranche-1",
        "protection_child_id": "tp-1",
        "generation": 1,
        "role": "TP",
        "client_order_link_id": "cl-tp-1",
        "exchange_order_id": None,
        "parent_exchange_order_id": "bybit-order-1",
        "trigger_by": "LAST_PRICE",
        "trigger_price": "26000",
        "target_quantity": "1",
        "executed_quantity": "0",
        "status": "NEW",
        "native_side": "SELL",
        "position_idx": 1,
    }


def _close_child_payload() -> dict[str, object]:
    return {
        "close_intent_id": "close-intent-1",
        "intent_revision": 1,
        "tranche_id": "tranche-1",
        "close_child_id": "close-child-1",
        "native_side": "SELL",
        "position_idx": 1,
        "role": "MANUAL_CLOSE",
        "confirmed_target_quantity": "1",
        "confirmed_residual_quantity": "1",
        "authorized_reduction_quantity": "1",
        "executed_reduction_quantity": "0",
        "quantity": "1",
        "reduce_only": True,
        "client_order_link_id": "cl-close-1",
        "execution_authority_revision": 1,
    }
