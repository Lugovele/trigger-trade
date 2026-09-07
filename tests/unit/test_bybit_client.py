import json
from urllib.parse import parse_qs, urlparse

import pytest

from triggertrade.config import ApiCredentials, BybitConfig
from triggertrade.exchanges.bybit import BybitApiError, BybitDemoClient, _sign_get_request


def test_public_requests_enforce_spot_btcusdt_category():
    seen = []

    def transport(request, timeout):
        seen.append(request.full_url)
        return _payload({"list": [{"symbol": "BTCUSDT"}]})

    client = BybitDemoClient(transport=transport)
    client.ticker("BTCUSDT")

    query = parse_qs(urlparse(seen[0]).query)
    assert query["category"] == ["spot"]
    assert query["symbol"] == ["BTCUSDT"]


def test_non_btcusdt_symbol_is_rejected():
    client = BybitDemoClient(transport=lambda request, timeout: _payload({}))

    with pytest.raises(BybitApiError):
        client.ticker("ETHUSDT")



def test_linear_instruments_info_uses_public_paginated_linear_catalog_query():
    seen = []

    def transport(request, timeout):
        seen.append(request)
        return _payload({"list": [], "nextPageCursor": ""})

    client = BybitDemoClient(transport=transport)
    client.linear_instruments_info(cursor="abc", limit=250)

    request = seen[0]
    query = parse_qs(urlparse(request.full_url).query)
    assert request.headers == {}
    assert query["category"] == ["linear"]
    assert query["cursor"] == ["abc"]
    assert query["limit"] == ["250"]

def test_authenticated_wallet_request_signing_headers():
    seen = []
    credentials = ApiCredentials(api_key="unit-key", api_secret="unit-signing-value")

    def transport(request, timeout):
        seen.append(request)
        return _payload({"list": []})

    client = BybitDemoClient(
        credentials=credentials,
        transport=transport,
        clock_ms=lambda: 1234567890,
    )
    client.wallet_balance("UNIFIED")

    request = seen[0]
    expected_signature = _sign_get_request(
        timestamp="1234567890",
        api_key="unit-key",
        recv_window="5000",
        query_string="accountType=UNIFIED",
        api_secret="unit-signing-value",
    )
    assert request.headers["X-bapi-api-key"] == "unit-key"
    assert request.headers["X-bapi-sign"] == expected_signature
    assert request.headers["X-bapi-sign-type"] == "2"
    assert request.headers["X-bapi-timestamp"] == "1234567890"
    assert request.headers["X-bapi-recv-window"] == "5000"
    assert "unit-signing-value" not in str(request.headers)


def test_wallet_balance_is_the_only_private_surface_on_client():
    public_or_safe = {
        "instrument_metadata",
        "linear_historical_candles",
        "linear_instrument_metadata",
        "linear_instruments_info",
        "linear_recent_candles",
        "linear_position_list",
        "linear_ticker",
        "public_connectivity",
        "recent_candles",
        "ticker",
        "wallet_balance",
    }
    callable_methods = {
        name
        for name in dir(BybitDemoClient)
        if not name.startswith("_") and callable(getattr(BybitDemoClient, name))
    }

    assert callable_methods == public_or_safe
    assert not any(name == "order" for name in callable_methods)
    assert "cancel" not in callable_methods


def test_unsupported_wallet_account_type_is_rejected():
    client = BybitDemoClient(
        config=BybitConfig(account_types=("UNIFIED",)),
        credentials=ApiCredentials(api_key="unit-key", api_secret="unit-signing-value"),
        transport=lambda request, timeout: _payload({}),
    )

    with pytest.raises(BybitApiError):
        client.wallet_balance("CONTRACT")


def _payload(result):
    return json.dumps({"retCode": 0, "retMsg": "OK", "result": result}).encode()
