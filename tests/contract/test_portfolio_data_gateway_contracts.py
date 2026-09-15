from __future__ import annotations

import pytest

from triggertrade.api_adapter_gateway import (
    PortfolioDataGatewayError,
    build_portfolio_data_request,
    build_portfolio_data_response,
    instrument_metadata_item,
)
from triggertrade.contracts import contract_digest, parse_contract
from tests.unit.test_portfolio_data_gateway import NOW, _instrument_facts


def test_portfolio_gateway_outputs_parse_as_approved_target_contracts():
    request = build_portfolio_data_request(
        request_id="pdr-contract-1",
        requested_at=NOW,
        scope={"instrument_metadata": True},
        symbols=("BTCUSDT",),
    )
    response = build_portfolio_data_response(
        request_id="pdr-contract-1",
        response_id="pdr-response-1",
        request_mode="SNAPSHOT",
        snapshot_started_at=NOW,
        snapshot_completed_at=NOW,
        as_of=NOW,
        instrument_metadata={
            "status": "AVAILABLE",
            "items": [
                instrument_metadata_item(
                    symbol="BTCUSDT",
                    status="AVAILABLE",
                    facts=_instrument_facts("BTCUSDT", NOW),
                    as_of=NOW,
                    source_endpoint="/v5/market/instruments-info",
                    source_record_id="linear:BTCUSDT",
                    reason_code=None,
                )
            ],
        },
        requested_symbols=("BTCUSDT",),
    )

    assert parse_contract("PORTFOLIO_DATA_REQUEST", request.to_payload(), definition="PORTFOLIO_DATA_REQUEST.request")
    assert parse_contract("PORTFOLIO_DATA_REQUEST", response.to_payload(), definition="PORTFOLIO_DATA_REQUEST.response")
    assert contract_digest(request) == contract_digest(request.to_payload())
    assert contract_digest(response) == contract_digest(response.to_payload())


def test_portfolio_gateway_rejects_extra_symbol_fact_not_requested():
    with pytest.raises(PortfolioDataGatewayError, match="exactly cover requested symbols"):
        build_portfolio_data_response(
            request_id="pdr-contract-1",
            response_id="pdr-response-1",
            request_mode="SNAPSHOT",
            snapshot_started_at=NOW,
            snapshot_completed_at=NOW,
            as_of=NOW,
            instrument_metadata={
                "status": "AVAILABLE",
                "items": [
                    instrument_metadata_item(
                        symbol="BTCUSDT",
                        status="AVAILABLE",
                        facts=_instrument_facts("BTCUSDT", NOW),
                        as_of=NOW,
                        source_endpoint="/v5/market/instruments-info",
                        source_record_id="linear:BTCUSDT",
                        reason_code=None,
                    )
                ],
            },
            requested_symbols=("ETHUSDT",),
        )
