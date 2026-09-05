from __future__ import annotations

from datetime import UTC, datetime, timedelta
import os

import pytest

from triggertrade.backtest import BacktestPlan, run_backtest
from triggertrade.backtest.data import BybitHistoricalDataSource, HistoricalKlineCache
from triggertrade.config import ExecutionVenue, load_config
from triggertrade.exchanges import BybitDemoClient
from triggertrade.market_data import parse_linear_instrument
from triggertrade.services.bootstrap import ensure_runtime_registry_for_env


@pytest.mark.skipif(os.environ.get("RUN_TRIGGERTRADE_BACKTEST_SMOKE") != "1", reason="explicit public historical smoke only")
def test_public_bybit_linear_backtest_smoke(tmp_path):
    db = tmp_path / "backtest-smoke.sqlite3"
    env = {
        "TRIGGERTRADE_MARKET": "linear",
        "TRIGGERTRADE_CATEGORY": "linear",
        "TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO_FUTURES.value,
        "TRIGGERTRADE_ACTIVE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO_FUTURES.value,
        "TRIGGERTRADE_TEST_EXECUTION_VENUE": ExecutionVenue.LOCAL_TEST_SIMULATION.value,
        "TRIGGERTRADE_RUNTIME_DB_PATH": str(db),
        "TRIGGERTRADE_RUNTIME_SYMBOL": "BTCUSDT",
        "TRIGGERTRADE_DEMO_EXPECTED_GROSS_MOVE": "1",
        "TRIGGERTRADE_FUTURES_SPREAD_COST": "1",
        "TRIGGERTRADE_FUTURES_SLIPPAGE_COST": "1",
    }
    config = load_config(env)
    ensure_runtime_registry_for_env(env)
    client = BybitDemoClient(config=config.bybit)
    end = datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(minutes=2)
    start = end - timedelta(hours=3)
    data = BybitHistoricalDataSource(client, cache=HistoricalKlineCache(tmp_path / "history")).load(
        symbol="BTCUSDT",
        category="linear",
        timeframe="1m",
        start=start,
        end=end,
    )
    instrument = parse_linear_instrument(client.linear_instrument_metadata("BTCUSDT").result)
    plan = BacktestPlan("BTCUSDT", "linear", "1m", start + timedelta(minutes=61), end)

    first = run_backtest(config=config, db_path=db, trigger_set_id="triggertrade-futures-core", trigger_set_version="v1", plan=plan, candles=data.candles, instrument=instrument)
    second = run_backtest(config=config, db_path=db, trigger_set_id="triggertrade-futures-core", trigger_set_version="v1", plan=plan, candles=data.candles, instrument=instrument)

    assert first == second
    assert first.candles_processed > 0
    assert data.content_hash
