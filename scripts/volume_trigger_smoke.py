"""Opt-in TRG-002 public-data smoke for Bybit Demo BTCUSDT Spot candles.

Run from the repository root with:
    RUN_TRIGGERTRADE_VOLUME_SMOKE=1 python scripts/volume_trigger_smoke.py
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from triggertrade.config import load_config  # noqa: E402
from triggertrade.exchanges import BybitDemoClient, BybitApiError  # noqa: E402
from triggertrade.market_data import parse_spot_candles  # noqa: E402
from triggertrade.triggers import RobustVolumeConfirmationTrigger, VolumeCandleWindow  # noqa: E402


def main() -> int:
    if os.environ.get("RUN_TRIGGERTRADE_VOLUME_SMOKE") != "1":
        print("TRG-002 volume smoke skipped: set RUN_TRIGGERTRADE_VOLUME_SMOKE=1")
        return 0
    env = dict(os.environ)
    env.setdefault("TRIGGERTRADE_TRADING_MODE", "paper")
    env.setdefault("TRIGGERTRADE_BYBIT_ENV", "demo")
    env.setdefault("TRIGGERTRADE_EXCHANGE", "bybit")
    env.setdefault("TRIGGERTRADE_MARKET", "spot")
    env.setdefault("TRIGGERTRADE_WATCHLIST", "BTCUSDT")
    config = load_config(env)
    if config.bybit.base_url != "https://api-demo.bybit.com":
        print("TRG-002 smoke refused unsafe non-demo base URL")
        return 1
    client = BybitDemoClient(config=config.bybit)
    try:
        candles = parse_spot_candles(client.recent_candles("BTCUSDT", interval="1", limit=70).result)
    except (BybitApiError, ValueError) as exc:
        print(f"TRG-002 smoke failed safely: {exc.__class__.__name__}")
        return 1
    ordered = tuple(sorted(candles, key=lambda item: item.start_time_ms))
    now = datetime.now(UTC)
    completed = tuple(
        candle for candle in ordered if datetime.fromtimestamp(candle.start_time_ms / 1000, UTC) + timedelta(minutes=1) <= now
    )
    if len(completed) < 61:
        print("TRG-002 smoke insufficient completed candles")
        return 1
    current = completed[-1]
    previous = completed[-61:-1]
    observed_at = datetime.fromtimestamp(current.start_time_ms / 1000, UTC) + timedelta(minutes=1)
    evaluation = RobustVolumeConfirmationTrigger().evaluate(
        VolumeCandleWindow(
            symbol="BTCUSDT",
            timeframe="1m",
            observed_at=observed_at,
            current_candle=current,
            previous_candles=previous,
            current_candle_completed=True,
        ),
        now=now,
    )
    print("TRG-002 public Bybit Demo smoke OK")
    print(f"symbol: {evaluation.symbol}")
    print(f"current_volume: {evaluation.current_volume}")
    print(f"median_volume_60: {evaluation.median_volume_60}")
    print(f"relative_volume: {evaluation.relative_volume}")
    print(f"volume_percentile: {evaluation.volume_percentile}")
    print(f"result: {evaluation.result.value}")
    print("private/order API calls: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
