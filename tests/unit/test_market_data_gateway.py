from __future__ import annotations

from decimal import Decimal

import pytest

from triggertrade.api_adapter_gateway import (
    MarketDataGatewayError,
    build_market_data_request,
    build_market_data_response,
    coverage,
    dataset_payload,
    market_selection,
    market_selection_digest,
    market_selection_result,
)
from triggertrade.contracts import parse_contract


NOW = "2026-09-14T00:00:00Z"


def test_market_data_request_builds_strict_as_of_and_interval_selectors():
    ticker = market_selection(
        selection_id="sel-ticker-1",
        dataset="TICKER",
        mode="AS_OF",
        as_of=NOW,
        page_size=1,
    )
    klines = market_selection(
        selection_id="sel-kline-1",
        dataset="KLINES",
        mode="INTERVAL",
        as_of=NOW,
        range_from="2026-09-13T00:00:00Z",
        range_to=NOW,
        completed_only=True,
        timeframe="1m",
        count=10,
        page_size=100,
    )

    parsed = build_market_data_request(
        request_id="mdr-1",
        requested_at=NOW,
        symbol="btcusdt",
        purpose="INITIAL_ANALYSIS",
        selections=(ticker, klines),
    )
    payload = parsed.to_payload()["market_data_request"]

    assert payload["contract_version"] == 3
    assert payload["symbol"] == "BTCUSDT"
    assert [item["selection_id"] for item in payload["selections"]] == ["sel-ticker-1", "sel-kline-1"]
    assert parse_contract("MARKET_DATA_REQUEST", parsed.to_payload(), definition="MARKET_DATA_REQUEST.request")


def test_market_selection_digest_excludes_cursor_but_binds_symbol_and_selector():
    first = market_selection(
        selection_id="sel-trades-1",
        dataset="RAW_TRADES",
        mode="INTERVAL",
        as_of=NOW,
        range_from="2026-09-13T00:00:00Z",
        range_to=NOW,
        completed_only=False,
        cursor=None,
        page_size=100,
    )
    next_page = market_selection(
        selection_id="sel-trades-1",
        dataset="RAW_TRADES",
        mode="INTERVAL",
        as_of=NOW,
        range_from="2026-09-13T00:00:00Z",
        range_to=NOW,
        completed_only=False,
        cursor="next",
        page_size=100,
    )

    assert market_selection_digest(symbol="BTCUSDT", selection=first) == market_selection_digest(
        symbol="BTCUSDT", selection=next_page
    )
    assert market_selection_digest(symbol="ETHUSDT", selection=first) != market_selection_digest(
        symbol="BTCUSDT", selection=first
    )


def test_market_response_validates_payload_coverage_and_selection_cardinality():
    selection = market_selection(selection_id="sel-ticker-1", dataset="TICKER", mode="AS_OF", as_of=NOW, page_size=1)
    result = market_selection_result(
        symbol="BTCUSDT",
        selection=selection,
        page_id="page-ticker-1",
        page_index=0,
        source_snapshot_id="snapshot-1",
        payload=dataset_payload(
            dataset="TICKER",
            status="AVAILABLE",
            as_of=NOW,
            source_endpoint="/v5/market/tickers",
            data={"last_price": Decimal("65000.1"), "mark_price": "65000", "index_price": "64999"},
        ),
        coverage=coverage(
            coverage_complete=True,
            pagination_complete=True,
            next_cursor=None,
            expected_page_ids=("page-ticker-1",),
            source_finality_confirmed=True,
        ),
    )

    parsed = build_market_data_response(
        request_id="mdr-1",
        response_id="mdr-response-1",
        symbol="BTCUSDT",
        snapshot_started_at=NOW,
        snapshot_completed_at=NOW,
        as_of=NOW,
        selection_results=(result,),
        expected_selections=(selection,),
    )
    payload = parsed.to_payload()["market_data_response"]

    assert payload["selection_results"][0]["selection_digest"] == market_selection_digest(
        symbol="BTCUSDT", selection=selection
    )
    assert payload["selection_results"][0]["payload"]["TICKER"]["data"]["last_price"] == "65000.1"
    assert parse_contract("MARKET_DATA_REQUEST", parsed.to_payload(), definition="MARKET_DATA_REQUEST.response")

    with pytest.raises(MarketDataGatewayError, match="requires at least one"):
        build_market_data_response(
            request_id="mdr-1",
            response_id="mdr-response-1",
            symbol="BTCUSDT",
            snapshot_started_at=NOW,
            snapshot_completed_at=NOW,
            as_of=NOW,
            selection_results=(),
            expected_selections=(selection,),
        )


def test_market_gateway_rejects_formula_like_or_invalid_api_choices():
    with pytest.raises(MarketDataGatewayError, match="AS_OF"):
        market_selection(
            selection_id="bad",
            dataset="TICKER",
            mode="INTERVAL",
            as_of=NOW,
            range_from="2026-09-13T00:00:00Z",
            range_to=NOW,
            completed_only=False,
            page_size=1,
        )
    with pytest.raises(MarketDataGatewayError, match="binary floats"):
        dataset_payload(
            dataset="TICKER",
            status="AVAILABLE",
            as_of=NOW,
            source_endpoint="/v5/market/tickers",
            data={"last_price": 65000.1, "mark_price": "65000", "index_price": "64999"},
        )
    with pytest.raises(MarketDataGatewayError, match="UNAVAILABLE"):
        market_selection_result(
            symbol="BTCUSDT",
            selection=market_selection(selection_id="sel-ticker-1", dataset="TICKER", mode="AS_OF", as_of=NOW),
            page_id="page-ticker-1",
            page_index=0,
            source_snapshot_id="snapshot-1",
            payload=dataset_payload(
                dataset="TICKER",
                status="UNAVAILABLE",
                as_of=NOW,
                source_endpoint="/v5/market/tickers",
                data=None,
            ),
            coverage=coverage(
                coverage_complete=True,
                pagination_complete=True,
                next_cursor=None,
                expected_page_ids=("page-ticker-1",),
                source_finality_confirmed=True,
                reason_code="SOURCE_UNAVAILABLE",
            ),
        )


def valid_market_response() -> dict[str, object]:
    selection = market_selection(selection_id="sel-ticker-1", dataset="TICKER", mode="AS_OF", as_of=NOW, page_size=1)
    result = market_selection_result(
        symbol="BTCUSDT",
        selection=selection,
        page_id="page-ticker-1",
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
            expected_page_ids=("page-ticker-1",),
            source_finality_confirmed=True,
        ),
    )
    return build_market_data_response(
        request_id="mdr-1",
        response_id="mdr-response-1",
        symbol="BTCUSDT",
        snapshot_started_at=NOW,
        snapshot_completed_at=NOW,
        as_of=NOW,
        selection_results=(result,),
        expected_selections=(selection,),
    ).to_payload()
