"""Opt-in real Bybit Demo Spot order lifecycle smoke test.

Run manually with:
    RUN_BYBIT_DEMO_ORDER_SMOKE=1 python -m pytest tests/integration/test_bybit_demo_order_smoke.py
"""

import os

import pytest

from scripts.bybit_demo_order_smoke import run_smoke


@pytest.mark.skipif(
    os.environ.get("RUN_BYBIT_DEMO_ORDER_SMOKE") != "1",
    reason="real Bybit Demo order smoke test is opt-in",
)
def test_bybit_demo_order_lifecycle_smoke():
    env = _load_env()
    env.setdefault("TRIGGERTRADE_EXECUTION_VENUE", "bybit_demo")

    result = run_smoke(env)

    assert result.created is True
    assert result.symbol == "BTCUSDT"
    assert result.order_type == "Limit"
    assert result.duplicate_count == 1


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
