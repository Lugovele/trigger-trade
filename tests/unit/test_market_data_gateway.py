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


def _build_single_result_response(selection, result):
    return build_market_data_response(
        request_id="mdr-validation-1",
        response_id="mdr-validation-response-1",
        symbol="BTCUSDT",
        snapshot_started_at=NOW,
        snapshot_completed_at=NOW,
        as_of=NOW,
        selection_results=(result,),
        expected_selections=(selection,),
    )


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


def test_last_traded_price_as_of_contract_preserves_ticker_shape_and_physical_provenance():
    selection = market_selection(
        selection_id="sel-last-traded-price-1",
        dataset="LAST_TRADED_PRICE",
        mode="AS_OF",
        as_of=NOW,
        page_size=1,
    )
    result = market_selection_result(
        symbol="PEPEUSDT",
        selection=selection,
        page_id="page-last-traded-price-1",
        page_index=0,
        source_snapshot_id="snapshot-last-traded-price-1",
        payload=dataset_payload(
            dataset="LAST_TRADED_PRICE",
            status="AVAILABLE",
            as_of=NOW,
            source_endpoint="/v5/market/recent-trade?category=linear&symbol=1000PEPEUSDT",
            data={
                "price": "0.012345",
                "observed_at": "2026-09-13T23:59:59.999000Z",
                "source_record_id": "bybit-trade-123",
                "venue": "BYBIT",
                "instrument_symbol": "1000PEPEUSDT",
            },
        ),
        coverage=coverage(
            coverage_complete=True,
            pagination_complete=True,
            next_cursor=None,
            expected_page_ids=("page-last-traded-price-1",),
            source_finality_confirmed=True,
        ),
    )

    parsed = build_market_data_response(
        request_id="mdr-last-traded-price-1",
        response_id="mdr-last-traded-price-response-1",
        symbol="PEPEUSDT",
        snapshot_started_at=NOW,
        snapshot_completed_at=NOW,
        as_of=NOW,
        selection_results=(result,),
        expected_selections=(selection,),
    )
    payload = parsed.to_payload()["market_data_response"]

    assert payload["symbol"] == "PEPEUSDT"
    assert payload["selection_results"][0]["selection"]["dataset"] == "LAST_TRADED_PRICE"
    assert payload["selection_results"][0]["payload"]["LAST_TRADED_PRICE"]["data"] == {
        "price": "0.012345",
        "observed_at": "2026-09-13T23:59:59.999000Z",
        "source_record_id": "bybit-trade-123",
        "venue": "BYBIT",
        "instrument_symbol": "1000PEPEUSDT",
    }
    assert parse_contract("MARKET_DATA_REQUEST", parsed.to_payload(), definition="MARKET_DATA_REQUEST.response")


def test_last_traded_price_requires_as_of_and_minimal_point_fact_payload():
    with pytest.raises(MarketDataGatewayError, match="AS_OF"):
        market_selection(
            selection_id="bad-last-traded-price",
            dataset="LAST_TRADED_PRICE",
            mode="INTERVAL",
            as_of=NOW,
            range_from="2026-09-13T00:00:00Z",
            range_to=NOW,
            completed_only=False,
            page_size=1,
        )

    selection = market_selection(
        selection_id="sel-last-traded-price-1",
        dataset="LAST_TRADED_PRICE",
        mode="AS_OF",
        as_of=NOW,
        page_size=1,
    )
    unavailable = market_selection_result(
        symbol="BTCUSDT",
        selection=selection,
        page_id="page-last-traded-price-unavailable",
        page_index=0,
        source_snapshot_id="snapshot-last-traded-price-1",
        payload=dataset_payload(
            dataset="LAST_TRADED_PRICE",
            status="UNAVAILABLE",
            as_of=NOW,
            source_endpoint="/v5/market/recent-trade",
            data=None,
        ),
        coverage=coverage(
            coverage_complete=False,
            pagination_complete=True,
            next_cursor=None,
            expected_page_ids=("page-last-traded-price-unavailable",),
            source_finality_confirmed=False,
            reason_code="LAST_TRADED_PRICE_UNAVAILABLE",
        ),
    )
    assert unavailable["payload"]["LAST_TRADED_PRICE"]["data"] is None

    missing_price = market_selection_result(
        symbol="BTCUSDT",
        selection=selection,
        page_id="page-last-traded-price-missing-price",
        page_index=0,
        source_snapshot_id="snapshot-last-traded-price-1",
        payload=dataset_payload(
            dataset="LAST_TRADED_PRICE",
            status="AVAILABLE",
            as_of=NOW,
            source_endpoint="/v5/market/recent-trade",
            data={
                "observed_at": "2026-09-13T23:59:59Z",
                "source_record_id": "bybit-trade-123",
                "venue": "BYBIT",
                "instrument_symbol": "BTCUSDT",
            },
        ),
        coverage=coverage(
            coverage_complete=True,
            pagination_complete=True,
            next_cursor=None,
            expected_page_ids=("page-last-traded-price-missing-price",),
            source_finality_confirmed=True,
        ),
    )
    with pytest.raises(MarketDataGatewayError, match="missing required fields: price"):
        _build_single_result_response(selection, missing_price)

    mark_price = market_selection_result(
        symbol="BTCUSDT",
        selection=selection,
        page_id="page-last-traded-price-mark",
        page_index=0,
        source_snapshot_id="snapshot-last-traded-price-1",
        payload=dataset_payload(
            dataset="LAST_TRADED_PRICE",
            status="AVAILABLE",
            as_of=NOW,
            source_endpoint="/v5/market/recent-trade",
            data={
                "price": "65000.1",
                "observed_at": "2026-09-13T23:59:59Z",
                "source_record_id": "bybit-trade-123",
                "venue": "BYBIT",
                "instrument_symbol": "BTCUSDT",
                "mark_price": "65000",
            },
        ),
        coverage=coverage(
            coverage_complete=True,
            pagination_complete=True,
            next_cursor=None,
            expected_page_ids=("page-last-traded-price-mark",),
            source_finality_confirmed=True,
        ),
    )
    with pytest.raises(MarketDataGatewayError, match="unknown fields: mark_price"):
        _build_single_result_response(selection, mark_price)

    candle_field = market_selection_result(
        symbol="BTCUSDT",
        selection=selection,
        page_id="page-last-traded-price-candle",
        page_index=0,
        source_snapshot_id="snapshot-last-traded-price-1",
        payload=dataset_payload(
            dataset="LAST_TRADED_PRICE",
            status="AVAILABLE",
            as_of=NOW,
            source_endpoint="/v5/market/recent-trade",
            data={
                "price": "65000.1",
                "observed_at": "2026-09-13T23:59:59Z",
                "source_record_id": "bybit-trade-123",
                "venue": "BYBIT",
                "instrument_symbol": "BTCUSDT",
                "close_time": "2026-09-14T00:00:00Z",
            },
        ),
        coverage=coverage(
            coverage_complete=True,
            pagination_complete=True,
            next_cursor=None,
            expected_page_ids=("page-last-traded-price-candle",),
            source_finality_confirmed=True,
        ),
    )
    with pytest.raises(MarketDataGatewayError, match="unknown fields: close_time"):
        _build_single_result_response(selection, candle_field)

    ticker_last_only = market_selection_result(
        symbol="BTCUSDT",
        selection=market_selection(selection_id="sel-ticker-1", dataset="TICKER", mode="AS_OF", as_of=NOW),
        page_id="page-ticker-last-only",
        page_index=0,
        source_snapshot_id="snapshot-ticker-1",
        payload=dataset_payload(
            dataset="TICKER",
            status="AVAILABLE",
            as_of=NOW,
            source_endpoint="/v5/market/tickers",
            data={"last_price": "65000.1"},
        ),
        coverage=coverage(
            coverage_complete=True,
            pagination_complete=True,
            next_cursor=None,
            expected_page_ids=("page-ticker-last-only",),
            source_finality_confirmed=True,
        ),
    )
    with pytest.raises(MarketDataGatewayError, match="missing required fields: index_price, mark_price"):
        _build_single_result_response(
            market_selection(selection_id="sel-ticker-1", dataset="TICKER", mode="AS_OF", as_of=NOW),
            ticker_last_only,
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
