from __future__ import annotations

from decimal import Decimal

import pytest

from triggertrade.api_adapter_gateway import (
    OrderManagementGatewayError,
    build_hard_execution_facts,
    build_order_management_hard_response,
    build_order_management_operation_response,
    build_order_management_request,
    exchange_error,
    execution_fact_from_bybit,
    order_fact_from_bybit,
)
from triggertrade.contracts import contract_digest


FIXED_AT = "2026-09-14T12:00:00Z"
BYBIT_MILLIS = "1799928000000"


def test_build_create_entry_request_uses_strict_v4_contract():
    parsed = build_order_management_request(
        request_id="om-req-1",
        operation="CREATE_ENTRY_ORDER",
        requested_at=FIXED_AT,
        correlation=_correlation(),
        exchange_identity={"client_order_link_id": "cl-1", "exchange_order_id": None},
        payload=_entry_payload(),
    )

    payload = parsed.to_payload()["order_management_request"]

    assert parsed.definition == "ORDER_MANAGEMENT.request.CREATE_ENTRY_ORDER"
    assert payload["contract_version"] == 4
    assert payload["operation"] == "CREATE_ENTRY_ORDER"
    assert payload["payload"]["post_only"] is True
    assert payload["payload"]["price"] == "25000.10"


def test_order_management_request_rejects_unknown_operation():
    with pytest.raises(OrderManagementGatewayError, match="unsupported Order Management operation"):
        build_order_management_request(
            request_id="om-req-1",
            operation="LEGACY_SPOT_ORDER",
            requested_at=FIXED_AT,
            correlation=None,
            payload={"symbol": "BTCUSDT"},
        )


def test_order_management_request_rejects_binary_float_payloads():
    payload = _entry_payload()
    payload["price"] = 25000.10

    with pytest.raises(OrderManagementGatewayError, match="unsupported binary float"):
        build_order_management_request(
            request_id="om-req-1",
            operation="CREATE_ENTRY_ORDER",
            requested_at=FIXED_AT,
            correlation=_correlation(),
            payload=payload,
        )


def test_bybit_order_fact_preserves_factual_identity_and_provenance():
    fact = order_fact_from_bybit(
        _bybit_order(),
        source_endpoint="/v5/order/realtime",
        mapping_profile_version="bybit-linear-order-facts-v1",
        evidence_ref="evidence://order/realtime/1",
    )

    assert fact["client_order_link_id"] == "cl-1"
    assert fact["exchange_order_id"] == "bybit-order-1"
    assert fact["remaining_quantity"] == "0.75"
    assert fact["updated_at"] == "2027-01-14T12:00:00Z"
    assert fact["native_created_at"] == "2027-01-14T12:00:00Z"
    assert fact["entry_acceptance_status"] == "UNAVAILABLE"
    assert fact["entry_acceptance_provenance"] is None
    assert fact["native_fact_provenance"][0]["normalized_field"] == "status"


def test_bybit_execution_fact_preserves_chronology_evidence():
    fact = execution_fact_from_bybit(
        _bybit_execution(),
        source_endpoint="/v5/execution/list",
        mapping_profile_version="bybit-linear-execution-facts-v1",
        evidence_ref="evidence://execution/1",
    )

    assert fact["execution_id"] == "exec-1"
    assert fact["quantity"] == "0.25"
    assert fact["price"] == "25005.5"
    assert fact["executed_at"] == "2027-01-14T12:00:00Z"
    assert fact["chronology_provenance"]["source_field"] == "execTime"


def test_operation_response_accepts_order_and_execution_facts_and_digest_is_stable():
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
        operation="GET_ORDER",
        as_of=FIXED_AT,
        result="AVAILABLE",
        client_order_link_id="cl-1",
        exchange_order_id="bybit-order-1",
        exchange_status="PartiallyFilled",
        orders=[order_fact],
        executions=[execution_fact],
    )

    same_payload = parsed.to_payload()

    assert parsed.definition == "ORDER_MANAGEMENT.response.operation"
    assert same_payload["order_management_response"]["orders"][0]["source_endpoint"] == "/v5/order/realtime"
    assert contract_digest(parsed) == contract_digest(same_payload)


def test_hard_execution_response_is_strict_order_management_v4():
    hard_facts = build_hard_execution_facts(
        instrument=_instrument(),
        native_configured_leverage=Decimal("3"),
        supported_native_profile=False,
        facts_complete=True,
        checked_at=FIXED_AT,
        source_ref="bybit-demo:linear:BTCUSDT",
    )

    parsed = build_order_management_hard_response(
        request_id="om-req-hard-1",
        response_id="om-resp-hard-1",
        as_of=FIXED_AT,
        result="AVAILABLE",
        hard_execution_facts=hard_facts,
    )

    response = parsed.to_payload()["order_management_response"]

    assert parsed.definition == "ORDER_MANAGEMENT.response.hard"
    assert response["operation"] == "GET_HARD_EXECUTION_FACTS"
    assert response["hard_execution_facts"]["native_configured_leverage"] == "3"


def test_gateway_rejects_invalid_trigger_direction_before_schema_emission():
    raw = _bybit_order()
    raw["triggerDirection"] = "SIDEWAYS"

    with pytest.raises(OrderManagementGatewayError, match="triggerDirection"):
        order_fact_from_bybit(
            raw,
            source_endpoint="/v5/order/realtime",
            mapping_profile_version="bybit-linear-order-facts-v1",
            evidence_ref="evidence://order/realtime/1",
        )


def test_exchange_error_payload_is_strict():
    parsed = build_order_management_operation_response(
        request_id="om-req-1",
        response_id="om-resp-1",
        operation="CANCEL_ENTRY_ORDER",
        as_of=FIXED_AT,
        result="REJECTED",
        exchange_error=exchange_error(
            code="110001",
            message="order not found",
            retryable=False,
            category="NOT_FOUND",
        ),
    )

    assert parsed.to_payload()["order_management_response"]["exchange_error"]["category"] == "NOT_FOUND"


def _correlation() -> dict[str, str | None]:
    return {
        "authorization_id": "auth-1",
        "capital_grant_id": "grant-1",
        "decision_cycle_id": "cycle-1",
        "set_result_id": "set-1",
        "position_decision_id": "decision-1",
        "construction_result_id": "construction-1",
        "position_plan_id": "plan-1",
        "tranche_id": "tranche-1",
        "order_spec_id": "spec-1",
        "symbol": "BTCUSDT",
    }


def _entry_payload() -> dict[str, object]:
    return {
        "side": "BUY",
        "order_type": "LIMIT",
        "post_only": True,
        "price": "25000.10",
        "quantity": "1",
        "leverage": "3",
        "take_profit": {
            "mode": "DYNAMIC",
            "price": "26000",
            "execution_type": "MARKET",
            "trigger_by": "LAST_PRICE",
            "scope": "PARTIAL_QUANTITY",
            "fixed_pct": None,
        },
        "stop_loss": {
            "mode": "DYNAMIC",
            "price": "24500",
            "execution_type": "MARKET",
            "trigger_by": "LAST_PRICE",
            "scope": "PARTIAL_QUANTITY",
            "fixed_pct": None,
        },
    }


def _bybit_order() -> dict[str, object]:
    return {
        "orderId": "bybit-order-1",
        "orderLinkId": "cl-1",
        "symbol": "BTCUSDT",
        "side": "Buy",
        "positionIdx": "1",
        "orderStatus": "PartiallyFilled",
        "qty": "1.000",
        "cumExecQty": "0.250",
        "avgPrice": "25005.5",
        "price": "25000.10",
        "orderType": "Limit",
        "triggerPrice": "",
        "triggerDirection": "0",
        "triggerBy": "",
        "reduceOnly": False,
        "closeOnTrigger": False,
        "stopOrderType": "",
        "createType": "CreateByUser",
        "createdTime": BYBIT_MILLIS,
        "updatedTime": BYBIT_MILLIS,
    }


def _bybit_execution() -> dict[str, object]:
    return {
        "execId": "exec-1",
        "orderId": "bybit-order-1",
        "orderLinkId": "cl-1",
        "symbol": "BTCUSDT",
        "side": "Buy",
        "positionIdx": "1",
        "execQty": "0.250",
        "execPrice": "25005.50",
        "execTime": BYBIT_MILLIS,
        "seq": "100",
    }


def _instrument() -> dict[str, object]:
    return {
        "tick_size": "0.1",
        "qty_step": "0.001",
        "min_order_qty": "0.001",
        "min_notional": "5",
        "max_order_qty": "100",
        "max_order_qty_status": "AVAILABLE",
        "max_order_qty_source_field": "lotSizeFilter.maxOrderQty",
        "max_leverage": "10",
        "contract_type": "LINEAR_USDT_PERPETUAL",
        "metadata_revision": "metadata-v1",
        "native_profile_revision": "native-profile-v1",
        "instrument_supported": True,
        "position_mode": "HEDGE_MODE",
        "margin_mode": "ISOLATED",
        "as_of": FIXED_AT,
        "source_ref": "bybit-demo:/v5/market/instruments-info:BTCUSDT",
    }
