"""CLI for safe public historical replay."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import os

from triggertrade.config import load_config
from triggertrade.exchanges import BybitDemoClient
from triggertrade.market_data import parse_linear_instrument
from triggertrade.persistence import TriggerSetStore, bootstrap_current_trigger_sets
from triggertrade.services.bootstrap import merged_runtime_env, runtime_db_path

from .data import BybitHistoricalDataSource
from .engine import run_backtest
from .models import BacktestPlan


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic TriggerTrade historical replay.")
    parser.add_argument("--set", dest="set_id", default="triggertrade-futures-core")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--warmup-candles", type=int, default=60)
    args = parser.parse_args()

    env = merged_runtime_env()
    env.setdefault("TRIGGERTRADE_MARKET", "linear")
    env.setdefault("TRIGGERTRADE_CATEGORY", "linear")
    env.setdefault("TRIGGERTRADE_EXECUTION_VENUE", "bybit_demo_futures")
    _require_explicit_backtest_assumptions(env)
    config = load_config(env)
    db_path = runtime_db_path(config, env)
    trigger_sets = TriggerSetStore(db_path)
    bootstrap_current_trigger_sets(trigger_sets)

    end = _parse_time(args.end) if args.end else datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(minutes=2)
    evaluation_start = _parse_time(args.start) if args.start else end - timedelta(hours=2)
    warmup_start = evaluation_start - timedelta(minutes=args.warmup_candles + 1)
    client = BybitDemoClient(config=config.bybit)
    record = BybitHistoricalDataSource(client).load(symbol=args.symbol, category="linear", timeframe="1m", start=warmup_start, end=end)
    instrument = _instrument(client, args.symbol)
    result = run_backtest(
        config=config,
        db_path=db_path,
        trigger_set_id=args.set_id,
        trigger_set_version=args.version,
        plan=BacktestPlan(symbol=args.symbol, category="linear", timeframe="1m", research_start=evaluation_start, research_end=end, warmup_candles=args.warmup_candles),
        candles=record.candles,
        instrument=instrument,
    )
    print(
        "backtest completed: "
        f"run={result.backtest_run_id} candles={result.candles_processed} "
        f"signals={result.signals} closed_trades={result.closed_trades} "
        f"evidence=BACKTEST cache_hash={record.content_hash[:12]}"
    )
    return 0


def _instrument(client: BybitDemoClient, symbol: str):
    return parse_linear_instrument(client.linear_instrument_metadata(symbol).result)


def _require_explicit_backtest_assumptions(env: dict[str, str]) -> None:
    required = (
        "TRIGGERTRADE_DEMO_EXPECTED_GROSS_MOVE",
        "TRIGGERTRADE_FUTURES_SPREAD_COST",
        "TRIGGERTRADE_FUTURES_SLIPPAGE_COST",
    )
    missing = [name for name in required if not env.get(name)]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Backtest smoke requires explicit replay assumptions: {joined}")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


if __name__ == "__main__":
    if os.environ.get("RUN_TRIGGERTRADE_BACKTEST_SMOKE") == "1":
        raise SystemExit(main())
    raise SystemExit("Set RUN_TRIGGERTRADE_BACKTEST_SMOKE=1 to run public historical replay smoke.")
