"""Opt-in real Bybit Demo smoke test.

Run manually with:
    RUN_BYBIT_DEMO_SMOKE=1 python -m pytest tests/integration/test_bybit_demo_smoke.py
"""

from pathlib import Path
import os

import pytest

from triggertrade.config import load_bybit_credentials, load_config
from triggertrade.exchanges import BybitDemoClient, parse_wallet_balance
from triggertrade.market_data import (
    parse_spot_candles,
    parse_spot_instrument,
    parse_spot_ticker,
)


@pytest.mark.skipif(
    os.environ.get("RUN_BYBIT_DEMO_SMOKE") != "1",
    reason="real Bybit Demo smoke test is opt-in",
)
def test_bybit_demo_read_connectivity_smoke():
    env = _load_env(Path(".env"))
    config = load_config(env)
    client = BybitDemoClient(config=config.bybit, credentials=load_bybit_credentials(env))

    client.public_connectivity()
    assert parse_spot_instrument(client.instrument_metadata("BTCUSDT").result).symbol == "BTCUSDT"
    assert parse_spot_ticker(client.ticker("BTCUSDT").result).symbol == "BTCUSDT"
    assert parse_spot_candles(client.recent_candles("BTCUSDT").result)
    assert _first_available_balance(client, config.bybit.account_types) is not None


def _first_available_balance(client: BybitDemoClient, account_types: tuple[str, ...]):
    last_error: Exception | None = None
    for account_type in account_types:
        try:
            return parse_wallet_balance(client.wallet_balance(account_type).result)
        except Exception as exc:
            last_error = exc
    raise AssertionError("demo wallet balance unavailable") from last_error


def _load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values
