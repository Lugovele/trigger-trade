from __future__ import annotations

from decimal import Decimal

import pytest

from triggertrade.api_adapter_gateway import (
    OrderManagementGatewayError,
    build_order_management_financial_response,
    component_coverage_certificate,
    coverage_certificate,
    financial_facts,
    financial_record,
    normalize_magnitude_with_direction,
)
from triggertrade.contracts import contract_digest


NOW = "2026-09-14T12:00:00Z"


@pytest.mark.parametrize(
    ("magnitude", "direction", "expected"),
    (
        ("0", "ZERO", "0"),
        ("1.25", "CREDIT", "1.25"),
        ("1.25", "DEBIT", "-1.25"),
    ),
)
def test_u05_magnitude_direction_normalization_accepts_exact_valid_matrix(magnitude, direction, expected):
    assert normalize_magnitude_with_direction(magnitude=magnitude, direction=direction) == expected


@pytest.mark.parametrize(
    ("magnitude", "direction"),
    (
        ("1", "ZERO"),
        ("0", "CREDIT"),
        ("0", "DEBIT"),
        ("-1", "DEBIT"),
        (1.5, "DEBIT"),
        ("1", "SIDEWAYS"),
    ),
)
def test_u05_magnitude_direction_normalization_rejects_invalid_raw_sign_matrix(magnitude, direction):
    with pytest.raises(OrderManagementGatewayError):
        normalize_magnitude_with_direction(magnitude=magnitude, direction=direction)


def test_financial_response_accepts_factual_fee_record_aliases_and_coverage_through_public_parser():
    coverage = _complete_coverage()
    facts = financial_facts(
        native_scope=_native_scope(),
        requested_from=NOW,
        requested_to=NOW,
        coverage=coverage,
        component_coverage=[
            component_coverage_certificate(
                component="TRADING_FEE",
                applicable=True,
                not_applicable_evidence=None,
                coverage=coverage,
            ),
            component_coverage_certificate(
                component="FUNDING",
                applicable=False,
                not_applicable_evidence="Bybit funding endpoint returned no event in requested interval",
                coverage=coverage_certificate(
                    status="COMPLETE",
                    coverage_from=NOW,
                    coverage_to=NOW,
                    missing_ranges=(),
                    pagination_complete=True,
                    next_cursor=None,
                    source_watermark_at=NOW,
                    source_finality_confirmed=True,
                    source_endpoints=("/v5/market/funding/history",),
                ),
            ),
        ],
        cashflows=[
            financial_record(
                cashflow_id="cashflow-fee-1",
                transaction_id="tx-1",
                execution_id="exec-1",
                component_type="TRADING_FEE",
                currency="USDT",
                source_amount="0.5",
                source_sign_convention="MAGNITUDE_WITH_DIRECTION",
                economic_direction="DEBIT",
                effective_at=NOW,
                recorded_at=NOW,
                symbol="BTCUSDT",
                native_side="BUY",
                position_idx=1,
                client_order_link_id="cl-1",
                exchange_order_id="order-1",
                source_endpoint="/v5/execution/list",
                source_record_id="exec-1",
                source_field="execFee",
                amount_quantum=Decimal("0.00000001"),
                normalization_profile_version="bybit-linear-financial-facts-v1",
                fee_classification="FEE",
                aliases=(
                    {
                        "source_endpoint": "/v5/account/transaction-log",
                        "source_record_id": "tx-1",
                        "source_field": "fee",
                    },
                ),
            )
        ],
    )

    parsed = build_order_management_financial_response(
        request_id="om-fin-req-1",
        response_id="om-fin-resp-1",
        as_of=NOW,
        result="COMPLETE",
        financial_facts=facts,
    )
    payload = parsed.to_payload()

    assert parsed.definition == "ORDER_MANAGEMENT.response.financial"
    assert payload["order_management_response"]["operation"] == "GET_FINANCIAL_FACTS"
    cashflow = payload["order_management_response"]["financial_facts"]["cashflows"][0]
    assert cashflow["signed_amount"] == "-0.5"
    assert cashflow["aliases"][0]["source_record_id"] == "tx-1"
    assert contract_digest(parsed) == contract_digest(payload)


def test_coverage_certificate_distinguishes_omission_from_not_applicable_and_rejects_false_complete():
    with pytest.raises(OrderManagementGatewayError, match="COMPLETE coverage"):
        coverage_certificate(
            status="COMPLETE",
            coverage_from=NOW,
            coverage_to=NOW,
            missing_ranges=({"from": NOW, "to": NOW},),
            pagination_complete=True,
            next_cursor=None,
            source_watermark_at=NOW,
            source_finality_confirmed=True,
            source_endpoints=("/v5/execution/list",),
        )

    with pytest.raises(OrderManagementGatewayError, match="not-applicable"):
        component_coverage_certificate(
            component="FUNDING",
            applicable=False,
            not_applicable_evidence=None,
            coverage=_complete_coverage(),
        )


def _native_scope() -> dict[str, object]:
    return {
        "account_id": "acct-demo",
        "environment": "TEST",
        "symbol": "BTCUSDT",
        "native_side": "BUY",
        "position_idx": 1,
    }


def _complete_coverage() -> dict[str, object]:
    return coverage_certificate(
        status="COMPLETE",
        coverage_from=NOW,
        coverage_to=NOW,
        missing_ranges=(),
        pagination_complete=True,
        next_cursor=None,
        source_watermark_at=NOW,
        source_finality_confirmed=True,
        source_endpoints=("/v5/execution/list",),
    )
