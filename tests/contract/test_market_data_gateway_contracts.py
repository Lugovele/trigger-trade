from __future__ import annotations

import pytest

from triggertrade.api_adapter_gateway import (
    MarketDataGatewayError,
    build_market_data_request,
    build_market_data_response,
    coverage,
    dataset_payload,
    market_selection,
    market_selection_result,
)
from triggertrade.contracts import contract_digest, implemented_contract_registry, parse_contract
from tests.unit.test_market_data_gateway import NOW


def test_market_gateway_outputs_approved_market_data_request_v3_contracts():
    registry = implemented_contract_registry()
    assert registry["MARKET_DATA_REQUEST"] == {
        "version": 3,
        "definitions": ("MARKET_DATA_REQUEST.request", "MARKET_DATA_REQUEST.response"),
    }
    selection = market_selection(selection_id="sel-instrument-1", dataset="INSTRUMENT_METADATA", mode="AS_OF", as_of=NOW)
    request = build_market_data_request(
        request_id="mdr-contract-1",
        requested_at=NOW,
        symbol="BTCUSDT",
        purpose="INITIAL_ANALYSIS",
        selections=(selection,),
    )
    response = build_market_data_response(
        request_id="mdr-contract-1",
        response_id="mdr-response-1",
        symbol="BTCUSDT",
        snapshot_started_at=NOW,
        snapshot_completed_at=NOW,
        as_of=NOW,
        selection_results=(
            market_selection_result(
                symbol="BTCUSDT",
                selection=selection,
                page_id="page-instrument-1",
                page_index=0,
                source_snapshot_id="snapshot-instrument-1",
                payload=dataset_payload(
                    dataset="INSTRUMENT_METADATA",
                    status="AVAILABLE",
                    as_of=NOW,
                    source_endpoint="/v5/market/instruments-info",
                    data={
                        "tick_size": "0.1",
                        "qty_step": "0.001",
                        "min_order_qty": "0.001",
                        "min_notional": "5",
                        "max_leverage": "50",
                        "contract_type": "LINEAR_USDT_PERPETUAL",
                        "metadata_revision": "instrument:BTCUSDT:1",
                    },
                ),
                coverage=coverage(
                    coverage_complete=True,
                    pagination_complete=True,
                    next_cursor=None,
                    expected_page_ids=("page-instrument-1",),
                    source_finality_confirmed=True,
                ),
            ),
        ),
        expected_selections=(selection,),
    )

    assert parse_contract("MARKET_DATA_REQUEST", request.to_payload(), definition="MARKET_DATA_REQUEST.request")
    assert parse_contract("MARKET_DATA_REQUEST", response.to_payload(), definition="MARKET_DATA_REQUEST.response")
    assert contract_digest(request) == contract_digest(request.to_payload())
    assert contract_digest(response) == contract_digest(response.to_payload())


def test_market_gateway_rejects_unrelated_selection_result():
    expected = market_selection(selection_id="expected", dataset="TICKER", mode="AS_OF", as_of=NOW)
    unrelated = market_selection(selection_id="unrelated", dataset="TICKER", mode="AS_OF", as_of=NOW)
    result = market_selection_result(
        symbol="BTCUSDT",
        selection=unrelated,
        page_id="page-unrelated",
        page_index=0,
        source_snapshot_id="snapshot-1",
        payload=dataset_payload(
            dataset="TICKER",
            status="AVAILABLE",
            as_of=NOW,
            source_endpoint="/v5/market/tickers",
            data={"last_price": "65000.1", "mark_price": "65000", "index_price": "64999"},
        ),
        coverage=coverage(
            coverage_complete=True,
            pagination_complete=True,
            next_cursor=None,
            expected_page_ids=("page-unrelated",),
            source_finality_confirmed=True,
        ),
    )
    with pytest.raises(MarketDataGatewayError, match="exactly cover"):
        build_market_data_response(
            request_id="mdr-contract-1",
            response_id="mdr-response-1",
            symbol="BTCUSDT",
            snapshot_started_at=NOW,
            snapshot_completed_at=NOW,
            as_of=NOW,
            selection_results=(result,),
            expected_selections=(expected,),
        )
