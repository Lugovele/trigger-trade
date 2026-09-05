"""Opt-in public-data smoke for CTX-REGIME@0.1.0."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import os

from triggertrade.config import load_config
from triggertrade.exchanges import BybitDemoClient
from triggertrade.market_data import RegimeEvaluationWindow, evaluate_market_regime, parse_spot_candles
from triggertrade.services.runtime import _bybit_interval


def main() -> int:
    if os.environ.get("RUN_TRIGGERTRADE_REGIME_SMOKE") != "1":
        print("Set RUN_TRIGGERTRADE_REGIME_SMOKE=1 to run the public Bybit Demo regime smoke.")
        return 0
    config = load_config()
    client = BybitDemoClient(config.bybit)
    candles = parse_spot_candles(
        client.linear_recent_candles(
            config.paper_runtime.symbol,
            interval=_bybit_interval(config.paper_runtime.candle_interval),
            limit=40,
        ).result
    )
    completed = tuple(
        candle
        for candle in sorted(candles, key=lambda item: item.start_time_ms)
        if datetime.fromtimestamp(candle.start_time_ms / 1000, UTC) + timedelta(minutes=1) <= datetime.now(UTC)
    )
    if not completed:
        print("regime_smoke status=NO_COMPLETED_CANDLE")
        return 1
    observed_at = datetime.fromtimestamp(completed[-1].start_time_ms / 1000, UTC) + timedelta(minutes=1)
    context = evaluate_market_regime(
        RegimeEvaluationWindow(
            symbol=config.paper_runtime.symbol,
            timeframe="1m",
            observed_at=observed_at,
            candles=completed,
            current_candle_completed=True,
        )
    )
    features = context.normalized_features or {}
    print(
        "regime_smoke "
        f"status=OK symbol={context.symbol} timeframe={context.timeframe} "
        f"version={context.rule_id}@{context.version} state={context.label.value if context.label else 'UNKNOWN'} "
        f"window_return_pct={features.get('window_return_pct', 'unavailable')} "
        f"normalized_trend={features.get('normalized_trend', 'unavailable')} "
        f"directional_persistence={features.get('directional_persistence', 'unavailable')} "
        f"reason={context.reason or 'classified'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
