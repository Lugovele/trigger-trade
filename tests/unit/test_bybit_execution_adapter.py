import json
from urllib.parse import parse_qs, urlparse

import pytest

from triggertrade.config import ApiCredentials
from triggertrade.exchanges import BybitApiError, BybitDemoClient


def test_create_order_uses_post_only_spot_order_shape():
    seen = []

    def transport(request, timeout):
        seen.append(request)
        return _payload({"orderId": "exchange-1", "orderLinkId": "tt-safe"})

    client = BybitDemoClient(
        credentials=ApiCredentials("unit-key", "unit-signing-value"),
        transport=transport,
        clock_ms=lambda: 123,
    )
    client._create_spot_limit_order(
        symbol="BTCUSDT",
        side="Buy",
        qty="0.001",
        price="10000.00",
        order_link_id="tt-safe",
    )

    request = seen[0]
    body = json.loads(request.data.decode("utf-8"))
    assert request.full_url.endswith("/v5/order/create")
    assert body == {
        "category": "spot",
        "symbol": "BTCUSDT",
        "side": "Buy",
        "orderType": "Limit",
        "qty": "0.001",
        "price": "10000.00",
        "timeInForce": "PostOnly",
        "isLeverage": 0,
        "orderFilter": "Order",
        "orderLinkId": "tt-safe",
    }


def test_fetch_and_cancel_order_use_order_link_id_and_spot_category():
    seen = []

    def transport(request, timeout):
        seen.append(request)
        return _payload({"list": []} if request.get_method() == "GET" else {"orderLinkId": "tt-safe"})

    client = BybitDemoClient(
        credentials=ApiCredentials("unit-key", "unit-signing-value"),
        transport=transport,
    )
    client._get_spot_order_realtime("BTCUSDT", "tt-safe")
    client._get_spot_order_history("BTCUSDT", "tt-safe")
    client._cancel_spot_order(symbol="BTCUSDT", order_link_id="tt-safe")

    queries = [parse_qs(urlparse(request.full_url).query) for request in seen[:2]]
    assert queries[0]["category"] == ["spot"]
    assert queries[0]["orderLinkId"] == ["tt-safe"]
    assert queries[1]["category"] == ["spot"]
    assert queries[1]["orderLinkId"] == ["tt-safe"]
    cancel_body = json.loads(seen[2].data.decode("utf-8"))
    assert cancel_body["category"] == "spot"
    assert cancel_body["orderLinkId"] == "tt-safe"
    assert "orderId" not in cancel_body


def test_private_signing_helpers_reject_non_allowlisted_paths():
    client = BybitDemoClient(
        credentials=ApiCredentials("unit-key", "unit-signing-value"),
        transport=lambda request, timeout: _payload({}),
    )

    with pytest.raises(BybitApiError):
        client._private_get("/v5/asset/transfer/query", {})
    with pytest.raises(BybitApiError):
        client._private_post("/v5/position/set-leverage", {})


def test_private_api_error_includes_sanitized_ret_msg():
    def transport(request, timeout):
        return json.dumps(
            {
                "retCode": 110072,
                "retMsg": "Duplicate orderLinkId API_KEY=secret Authorization:bearer",
                "result": {},
            }
        ).encode()

    client = BybitDemoClient(
        credentials=ApiCredentials("unit-key", "unit-signing-value"),
        transport=transport,
    )

    with pytest.raises(BybitApiError) as raised:
        client._create_linear_limit_order(
            symbol="BTCUSDT",
            side="Buy",
            qty="0.001",
            price="10000.00",
            order_link_id="tt-safe",
        )

    assert raised.value.code == "110072"
    assert "retCode=110072" in str(raised.value)
    assert "Duplicate orderLinkId" in str(raised.value)
    assert "secret" not in str(raised.value)
    assert "bearer" not in str(raised.value)


def _payload(result):
    return json.dumps({"retCode": 0, "retMsg": "OK", "result": result}).encode()
