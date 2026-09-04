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


@dataclass(frozen=True)
class BybitResponse:
    ret_code: int
    ret_msg: str
    result: dict[str, Any]


HttpTransport = Callable[[Request, int], bytes]


class BybitDemoClient:
    """Minimal read-only client for Bybit Demo spot/account checks."""

    _WALLET_BALANCE_PATH = "/v5/account/wallet-balance"

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

    def ticker(self, symbol: str = "BTCUSDT") -> BybitResponse:
        return self._public_get(
            "/v5/market/tickers",
            {"category": "spot", "symbol": _spot_symbol(symbol)},
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

    def wallet_balance(self, account_type: str = "UNIFIED") -> BybitResponse:
        if self._credentials is None:
            raise BybitApiError("Bybit credentials are required for private connectivity")
        normalized_account = account_type.strip().upper()
        if normalized_account not in self._config.account_types:
            allowed = ", ".join(self._config.account_types)
            raise BybitApiError(f"unsupported Bybit account type; expected one of: {allowed}")
        return self._private_get_wallet_balance({"accountType": normalized_account})

    def _public_get(
        self,
        path: str,
        query: dict[str, str] | None = None,
    ) -> BybitResponse:
        request = Request(self._url(path, query), method="GET")
        return self._send(request)

    def _private_get_wallet_balance(self, query: dict[str, str]) -> BybitResponse:
        if self._credentials is None:
            raise BybitApiError("Bybit credentials are required for private connectivity")
        query_string = urlencode(query)
        timestamp = str(self._clock_ms())
        recv_window = str(self._config.recv_window_ms)
        signature = _sign_get_request(
            timestamp=timestamp,
            api_key=self._credentials.api_key,
            recv_window=recv_window,
            query_string=query_string,
            api_secret=self._credentials.api_secret,
        )
        request = Request(
            self._url(self._WALLET_BALANCE_PATH, query),
            headers={
                "X-BAPI-API-KEY": self._credentials.api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": recv_window,
            },
            method="GET",
        )
        return self._send(request)

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
            raise BybitApiError(f"Bybit API returned retCode={response.ret_code}")
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
    payload = f"{timestamp}{api_key}{recv_window}{query_string}"
    return hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()


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


def _urlopen_transport(request: Request, timeout: int) -> bytes:
    with urlopen(request, timeout=timeout) as response:
        return response.read()
