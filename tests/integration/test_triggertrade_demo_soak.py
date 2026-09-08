"""Opt-in bounded TriggerTrade Bybit Demo soak harness test."""

import os

import pytest

from scripts.triggertrade_demo_soak import run_soak


@pytest.mark.skipif(
    os.environ.get("RUN_TRIGGERTRADE_DEMO_SOAK") != "1",
    reason="real TriggerTrade Demo soak is explicit opt-in",
)
def test_triggertrade_demo_soak_harness():
    result = run_soak(cycles=int(os.environ.get("TRIGGERTRADE_DEMO_SOAK_CYCLES", "1")))

    assert result.status == "RUNNING"
    assert result.cycles_completed == result.cycles_requested
