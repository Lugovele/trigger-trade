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
