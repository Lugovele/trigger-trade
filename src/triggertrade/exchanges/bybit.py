"""Read-only Bybit Demo REST client."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import hmac
import json
import time
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from triggertrade.config import ApiCredentials, BybitConfig


class BybitApiError(RuntimeError):
    """Raised for sanitized Bybit API failures."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class BybitResponse:
    ret_code: int
    ret_msg: str
    result: dict[str, Any]


HttpTransport = Callable[[Request, int], bytes]


class BybitDemoClient:
    """Minimal Bybit Demo spot/account client with a narrow endpoint allowlist."""

    _WALLET_BALANCE_PATH = "/v5/account/wallet-balance"
    _ORDER_CREATE_PATH = "/v5/order/create"
    _ORDER_CANCEL_PATH = "/v5/order/cancel"
    _ORDER_REALTIME_PATH = "/v5/order/realtime"
    _ORDER_HISTORY_PATH = "/v5/order/history"
    _EXECUTION_LIST_PATH = "/v5/execution/list"
    _POSITION_LIST_PATH = "/v5/position/list"
    _SIGNED_GET_ALLOWLIST = frozenset(
        {
            _WALLET_BALANCE_PATH,
            _ORDER_REALTIME_PATH,
            _ORDER_HISTORY_PATH,
            _EXECUTION_LIST_PATH,
            _POSITION_LIST_PATH,
        }
    )
    _SIGNED_POST_ALLOWLIST = frozenset(
        {
            _ORDER_CREATE_PATH,
            _ORDER_CANCEL_PATH,
        }
    )

    def __init__(
        self,
        config: BybitConfig | None = None,
        credentials: ApiCredentials | None = None,
        transport: HttpTransport | None = None,
        clock_ms: Callable[[], int] | None = None,
    ) -> None:
        self._config = config or BybitConfig()
        self._credentials = credentials
        self._transport = transport or _urlopen_transport
        self._clock_ms = clock_ms or (lambda: int(time.time() * 1000))

    @property
    def base_url(self) -> str:
        return self._config.base_url

    def public_connectivity(self) -> BybitResponse:
        return self._public_get("/v5/market/time")

    def instrument_metadata(self, symbol: str = "BTCUSDT") -> BybitResponse:
        return self._public_get(
            "/v5/market/instruments-info",
            {"category": "spot", "symbol": _spot_symbol(symbol)},
        )

    def linear_instrument_metadata(self, symbol: str = "BTCUSDT") -> BybitResponse:
        return self._public_get(
            "/v5/market/instruments-info",
            {"category": "linear", "symbol": _linear_public_symbol(symbol)},
        )

    def linear_instruments_info(self, *, cursor: str | None = None, limit: int = 1000) -> BybitResponse:
        query = {"category": "linear", "limit": str(limit)}
        if cursor:
            query["cursor"] = cursor
        return self._public_get("/v5/market/instruments-info", query)

    def ticker(self, symbol: str = "BTCUSDT") -> BybitResponse:
        return self._public_get(
            "/v5/market/tickers",
            {"category": "spot", "symbol": _spot_symbol(symbol)},
        )

    def linear_ticker(self, symbol: str = "BTCUSDT") -> BybitResponse:
        return self._public_get(
            "/v5/market/tickers",
            {"category": "linear", "symbol": _linear_symbol(symbol)},
        )

    def recent_candles(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1",
        limit: int = 3,
    ) -> BybitResponse:
        return self._public_get(
            "/v5/market/kline",
            {
                "category": "spot",
                "symbol": _spot_symbol(symbol),
                "interval": interval,
                "limit": str(limit),
            },
        )

    def linear_recent_candles(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1",
        limit: int = 3,
    ) -> BybitResponse:
        return self._public_get(
            "/v5/market/kline",
            {
                "category": "linear",
                "symbol": _linear_symbol(symbol),
                "interval": interval,
                "limit": str(limit),
            },
        )

    def linear_historical_candles(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1",
        start_ms: int | None = None,
        end_ms: int | None = None,
        limit: int = 200,
    ) -> BybitResponse:
        query = {
            "category": "linear",
            "symbol": _linear_symbol(symbol),
            "interval": interval,
            "limit": str(limit),
        }
        if start_ms is not None:
            query["start"] = str(start_ms)
        if end_ms is not None:
            query["end"] = str(end_ms)
        return self._public_get("/v5/market/kline", query)

    def wallet_balance(self, account_type: str = "UNIFIED") -> BybitResponse:
        if self._credentials is None:
            raise BybitApiError("Bybit credentials are required for private connectivity")
        normalized_account = account_type.strip().upper()
        if normalized_account not in self._config.account_types:
            allowed = ", ".join(self._config.account_types)
            raise BybitApiError(f"unsupported Bybit account type; expected one of: {allowed}")
        return self._private_get_wallet_balance({"accountType": normalized_account})

    def linear_position_list(self, symbol: str = "BTCUSDT") -> BybitResponse:
        return self._private_get(
            self._POSITION_LIST_PATH,
            {
                "category": "linear",
                "symbol": _linear_symbol(symbol),
            },
        )

    def _create_spot_limit_order(
        self,
        *,
        symbol: str,
        side: str,
        qty: str,
        price: str,
        order_link_id: str,
    ) -> BybitResponse:
        _validate_order_link_id(order_link_id)
        body = {
            "category": "spot",
            "symbol": _spot_symbol(symbol),
            "side": side,
            "orderType": "Limit",
            "qty": qty,
            "price": price,
            "timeInForce": "PostOnly",
            "isLeverage": 0,
            "orderFilter": "Order",
            "orderLinkId": order_link_id,
        }
        return self._private_post(self._ORDER_CREATE_PATH, body)

    def _create_linear_limit_order(
        self,
        *,
        symbol: str,
        side: str,
        qty: str,
        price: str,
        order_link_id: str,
        reduce_only: bool = False,
    ) -> BybitResponse:
        _validate_order_link_id(order_link_id)
        body = {
            "category": "linear",
            "symbol": _linear_symbol(symbol),
            "side": side,
            "orderType": "Limit",
            "qty": qty,
            "price": price,
            "timeInForce": "PostOnly",
            "reduceOnly": reduce_only,
            "orderLinkId": order_link_id,
        }
        return self._private_post(self._ORDER_CREATE_PATH, body)

    def _get_spot_order_realtime(self, symbol: str, order_link_id: str) -> BybitResponse:
        _validate_order_link_id(order_link_id)
        return self._private_get(
            self._ORDER_REALTIME_PATH,
            {
                "category": "spot",
                "symbol": _spot_symbol(symbol),
                "orderLinkId": order_link_id,
                "orderFilter": "Order",
            },
        )

    def _get_linear_order_realtime(self, symbol: str, order_link_id: str) -> BybitResponse:
        _validate_order_link_id(order_link_id)
        return self._private_get(
            self._ORDER_REALTIME_PATH,
            {
                "category": "linear",
                "symbol": _linear_symbol(symbol),
                "orderLinkId": order_link_id,
            },
        )

    def _get_spot_order_history(self, symbol: str, order_link_id: str) -> BybitResponse:
        _validate_order_link_id(order_link_id)
        return self._private_get(
            self._ORDER_HISTORY_PATH,
            {
                "category": "spot",
                "symbol": _spot_symbol(symbol),
                "orderLinkId": order_link_id,
                "orderFilter": "Order",
            },
        )

    def _get_linear_order_history(self, symbol: str, order_link_id: str) -> BybitResponse:
        _validate_order_link_id(order_link_id)
        return self._private_get(
            self._ORDER_HISTORY_PATH,
            {
                "category": "linear",
                "symbol": _linear_symbol(symbol),
                "orderLinkId": order_link_id,
            },
        )

    def _get_linear_executions(self, symbol: str, order_link_id: str) -> BybitResponse:
        _validate_order_link_id(order_link_id)
        return self._private_get(
            self._EXECUTION_LIST_PATH,
            {
                "category": "linear",
                "symbol": _linear_symbol(symbol),
                "orderLinkId": order_link_id,
            },
        )

    def _cancel_spot_order(self, *, symbol: str, order_link_id: str) -> BybitResponse:
        _validate_order_link_id(order_link_id)
        return self._private_post(
            self._ORDER_CANCEL_PATH,
            {
                "category": "spot",
                "symbol": _spot_symbol(symbol),
                "orderLinkId": order_link_id,
                "orderFilter": "Order",
            },
        )

    def _cancel_linear_order(self, *, symbol: str, order_link_id: str) -> BybitResponse:
        _validate_order_link_id(order_link_id)
        return self._private_post(
            self._ORDER_CANCEL_PATH,
            {
                "category": "linear",
                "symbol": _linear_symbol(symbol),
                "orderLinkId": order_link_id,
            },
        )

    def _public_get(
        self,
        path: str,
        query: dict[str, str] | None = None,
    ) -> BybitResponse:
        request = Request(self._url(path, query), method="GET")
        return self._send(request)

    def _private_get_wallet_balance(self, query: dict[str, str]) -> BybitResponse:
        return self._private_get(self._WALLET_BALANCE_PATH, query)

    def _private_get(self, path: str, query: dict[str, str]) -> BybitResponse:
        if path not in self._SIGNED_GET_ALLOWLIST:
            raise BybitApiError("private GET endpoint is not allowlisted")
        if self._credentials is None:
            raise BybitApiError("Bybit credentials are required for private connectivity")
        query_string = urlencode(query)
        headers = self._signed_headers(query_string)
        request = Request(
            self._url(path, query),
            headers=headers,
            method="GET",
        )
        return self._send(request)

    def _private_post(self, path: str, body: dict[str, Any]) -> BybitResponse:
        if path not in self._SIGNED_POST_ALLOWLIST:
            raise BybitApiError("private POST endpoint is not allowlisted")
        if self._credentials is None:
            raise BybitApiError("Bybit credentials are required for private connectivity")
        body_json = json.dumps(body, separators=(",", ":"))
        headers = self._signed_headers(body_json)
        headers["Content-Type"] = "application/json"
        request = Request(
            self._url(path),
            data=body_json.encode("utf-8"),
            headers=headers,
            method="POST",
        )
        return self._send(request)

    def _signed_headers(self, payload: str) -> dict[str, str]:
        if self._credentials is None:
            raise BybitApiError("Bybit credentials are required for private connectivity")
        timestamp = str(self._clock_ms())
        recv_window = str(self._config.recv_window_ms)
        signature = _sign_request(
            timestamp=timestamp,
            api_key=self._credentials.api_key,
            recv_window=recv_window,
            payload=payload,
            api_secret=self._credentials.api_secret,
        )
        return {
            "X-BAPI-API-KEY": self._credentials.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": "2",
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
        }

    def _send(self, request: Request) -> BybitResponse:
        try:
            payload = self._transport(request, 10)
        except HTTPError as exc:
            raise BybitApiError(f"Bybit API HTTP error: {exc.code}") from exc
        except OSError as exc:
            raise BybitApiError(f"Bybit API request failed: {exc.__class__.__name__}") from exc

        try:
            raw = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BybitApiError("Bybit API returned an invalid JSON payload") from exc

        response = BybitResponse(
            ret_code=int(raw.get("retCode", -1)),
            ret_msg=str(raw.get("retMsg", "")),
            result=raw.get("result") or {},
        )
        if response.ret_code != 0:
            raise BybitApiError(
                f"Bybit API returned retCode={response.ret_code}",
                code=str(response.ret_code),
            )
        return response

    def _url(self, path: str, query: dict[str, str] | None = None) -> str:
        url = f"{self._config.base_url}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        return url


def _sign_get_request(
    *,
    timestamp: str,
    api_key: str,
    recv_window: str,
    query_string: str,
    api_secret: str,
) -> str:
    return _sign_request(
        timestamp=timestamp,
        api_key=api_key,
        recv_window=recv_window,
        payload=query_string,
        api_secret=api_secret,
    )


def _sign_request(
    *,
    timestamp: str,
    api_key: str,
    recv_window: str,
    payload: str,
    api_secret: str,
) -> str:
    raw = f"{timestamp}{api_key}{recv_window}{payload}"
    return hmac.new(api_secret.encode("utf-8"), raw.encode("utf-8"), sha256).hexdigest()


def parse_wallet_balance(result: dict[str, Any]) -> dict[str, Decimal]:
    balances: dict[str, Decimal] = {}
    for account in result.get("list") or []:
        for coin in account.get("coin") or []:
            name = coin.get("coin")
            wallet_balance = coin.get("walletBalance")
            if name and wallet_balance is not None:
                balances[str(name)] = Decimal(str(wallet_balance))
    return balances


def _spot_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if normalized != "BTCUSDT":
        raise BybitApiError("this integration slice supports only spot BTCUSDT")
    return normalized


def _linear_public_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if not normalized.endswith("USDT") or not normalized.removesuffix("USDT").isalnum():
        raise BybitApiError("linear public market data requires a USDT symbol")
    return normalized


def _linear_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if normalized != "BTCUSDT":
        raise BybitApiError("this integration slice supports only linear BTCUSDT perpetual")
    return normalized


def _validate_order_link_id(order_link_id: str) -> None:
    if not order_link_id:
        raise BybitApiError("orderLinkId is required")
    if len(order_link_id) > 36:
        raise BybitApiError("orderLinkId must be no longer than 36 characters")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    if any(char not in allowed for char in order_link_id):
        raise BybitApiError("orderLinkId contains unsupported characters")


def _urlopen_transport(request: Request, timeout: int) -> bytes:
    with urlopen(request, timeout=timeout) as response:
        return response.read()
