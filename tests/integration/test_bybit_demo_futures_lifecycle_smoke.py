"""Opt-in real Bybit Demo futures position lifecycle smoke."""

import os

import pytest

from scripts.bybit_demo_futures_lifecycle_smoke import run_smoke


@pytest.mark.skipif(
    os.environ.get("RUN_TRIGGERTRADE_FUTURES_LIFECYCLE_SMOKE") != "1",
    reason="real Bybit Demo futures lifecycle smoke is opt-in",
)
def test_bybit_demo_futures_lifecycle_smoke():
    result = run_smoke(_load_env())

    assert result["demo_endpoint"] == "OK"
    assert result["category"] == "linear"
    assert result["symbol"] == "BTCUSDT"
    assert result["spot_calls"] == "0"
    assert result["mainnet_calls"] == "0"


def _load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    with open(".env", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values
