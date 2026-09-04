"""Opt-in real TriggerTrade e2e Demo smoke test."""

import os

import pytest

from scripts.triggertrade_e2e_demo_smoke import run_smoke


@pytest.mark.skipif(
    os.environ.get("RUN_TRIGGERTRADE_E2E_DEMO_SMOKE") != "1",
    reason="real TriggerTrade e2e demo smoke is opt-in",
)
def test_triggertrade_e2e_demo_smoke():
    env = _load_env()
    env.setdefault("TRIGGERTRADE_EXECUTION_VENUE", "bybit_demo")

    result = run_smoke(env)

    assert result.signal_type == "BUY_CANDIDATE"
    assert result.approved is True
    assert result.symbol == "BTCUSDT"
    assert result.order_type == "Limit"
    assert result.duplicate_count == 1
    assert result.trace_complete is True


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
