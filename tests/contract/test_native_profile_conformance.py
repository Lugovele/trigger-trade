import pytest

from triggertrade.api_adapter_gateway import (
    NativeProfileConformanceError,
    NativeProfileStatus,
    bybit_demo_native_profile_conformance,
)
from triggertrade.execution.bybit_futures import BybitFuturesExecutionAdapter


def test_bybit_demo_native_profile_review_remains_uncertified_with_unresolved_fields():
    report = bybit_demo_native_profile_conformance(
        {
            "demo_endpoint": "OK",
            "category": "linear",
            "symbol": "BTCUSDT",
            "spot_calls": "0",
            "mainnet_calls": "0",
        }
    )

    assert report.profile_id == "bybit-demo-linear-usdt-perpetual"
    assert report.certified is False
    assert report.exposure_changing_enabled is False
    assert "accepted_time_provenance" in report.unresolved_requirements
    assert "protective_child_linkage" in report.unresolved_requirements
    assert report.evidence[0].status is NativeProfileStatus.REVIEWED
    assert all(item.status is not NativeProfileStatus.REVIEWED for item in report.evidence[1:])


def test_bybit_demo_native_profile_rejects_mainnet_or_spot_smoke_evidence():
    with pytest.raises(NativeProfileConformanceError, match="mainnet_calls"):
        bybit_demo_native_profile_conformance(
            {
                "demo_endpoint": "OK",
                "category": "linear",
                "spot_calls": "0",
                "mainnet_calls": "1",
            }
        )
    with pytest.raises(NativeProfileConformanceError, match="category"):
        bybit_demo_native_profile_conformance(
            {
                "demo_endpoint": "OK",
                "category": "spot",
                "spot_calls": "0",
                "mainnet_calls": "0",
            }
        )


def test_bybit_futures_adapter_exposes_uncertified_native_profile_gate():
    adapter = BybitFuturesExecutionAdapter(client=object())  # type: ignore[arg-type]

    report = adapter.native_profile_conformance()

    assert report.certified is False
    assert report.exposure_changing_enabled is False
    assert report.smoke_evidence == {"available": "false"}


def test_bybit_futures_adapter_exposes_order_management_fact_normalizers():
    adapter = BybitFuturesExecutionAdapter(client=object())  # type: ignore[arg-type]
    order_fact = adapter.order_management_order_fact(
        {
            "orderId": "bybit-order-1",
            "orderLinkId": "cl-1",
            "symbol": "BTCUSDT",
            "side": "Buy",
            "positionIdx": "1",
            "orderStatus": "PartiallyFilled",
            "qty": "1",
            "cumExecQty": "0.25",
            "avgPrice": "25005.5",
            "price": "25000.1",
            "orderType": "Limit",
            "triggerPrice": "",
            "triggerDirection": "0",
            "triggerBy": "",
            "reduceOnly": False,
            "closeOnTrigger": False,
            "stopOrderType": "",
            "createType": "CreateByUser",
            "createdTime": "1799928000000",
            "updatedTime": "1799928000000",
        },
        source_endpoint="/v5/order/realtime",
        mapping_profile_version="bybit-linear-order-facts-v1",
        evidence_ref="evidence://order/realtime/1",
    )
    execution_fact = adapter.order_management_execution_fact(
        {
            "execId": "exec-1",
            "orderId": "bybit-order-1",
            "orderLinkId": "cl-1",
            "symbol": "BTCUSDT",
            "side": "Buy",
            "positionIdx": "1",
            "execQty": "0.25",
            "execPrice": "25005.5",
            "execTime": "1799928000000",
            "seq": "100",
        },
        source_endpoint="/v5/execution/list",
        mapping_profile_version="bybit-linear-execution-facts-v1",
        evidence_ref="evidence://execution/1",
    )

    assert order_fact["source_endpoint"] == "/v5/order/realtime"
    assert execution_fact["chronology_profile_version"] == "bybit-linear-execution-facts-v1"
