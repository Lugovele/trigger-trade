"""Opt-in bounded Bybit Demo soak harness for TriggerTrade futures runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from triggertrade.config import BybitEnvironment, ExecutionVenue, Market, TradingMode, load_config
from triggertrade.persistence import RuntimeHeartbeat, RuntimeStore
from triggertrade.services.bootstrap import merged_runtime_env, runtime_db_path
from triggertrade.services.runtime import build_runtime_from_env


OPT_IN_FLAG = "RUN_TRIGGERTRADE_DEMO_SOAK"


@dataclass(frozen=True)
class DemoSoakResult:
    cycles_requested: int
    cycles_completed: int
    status: str
    db_path: Path


def run_soak(env: dict[str, str] | None = None, *, cycles: int | None = None) -> DemoSoakResult:
    source = merged_runtime_env(os.environ if env is None else env)
    if source.get(OPT_IN_FLAG) != "1":
        raise RuntimeError(f"{OPT_IN_FLAG}=1 is required for the Bybit Demo soak harness")
    if _env_true(source.get("TRIGGERTRADE_LIVE_TRADING_ENABLED")):
        raise RuntimeError("Demo soak refuses live trading")
    if str(source.get("TRIGGERTRADE_TRADING_MODE", "")).strip().lower() == "live":
        raise RuntimeError("Demo soak refuses live trading")
    config = load_config(source)
    _validate_demo_only(config)
    requested = cycles if cycles is not None else int(source.get("TRIGGERTRADE_DEMO_SOAK_CYCLES", "3"))
    requested = max(1, min(requested, 100))
    db_path = runtime_db_path(config, source)
    runtime_store = RuntimeStore(db_path)
    runtime_store.record_heartbeat(
        RuntimeHeartbeat(
            component="demo_soak",
            status="RUNNING",
            observed_at=datetime.now(UTC).isoformat(),
            detail=f"starting bounded soak for {requested} cycles",
            metadata={"cycles_requested": str(requested)},
        )
    )
    completed = 0
    try:
        runtime = build_runtime_from_env(source)
        runtime.run_forever(max_cycles=requested)
        completed = requested
        status = "RUNNING"
        detail = "bounded soak completed"
    except Exception as exc:
        status = "DEGRADED"
        detail = exc.__class__.__name__
    runtime_store.record_heartbeat(
        RuntimeHeartbeat(
            component="demo_soak",
            status=status,
            observed_at=datetime.now(UTC).isoformat(),
            detail=detail,
            metadata={"cycles_requested": str(requested), "cycles_completed": str(completed)},
        )
    )
    if status != "RUNNING":
        raise RuntimeError(detail)
    return DemoSoakResult(requested, completed, status, db_path)


def _validate_demo_only(config) -> None:
    if config.trading_mode is not TradingMode.PAPER:
        raise RuntimeError("Demo soak requires paper trading mode")
    if config.live_trading_enabled:
        raise RuntimeError("Demo soak refuses live trading")
    if config.bybit.environment is not BybitEnvironment.DEMO:
        raise RuntimeError("Demo soak requires Bybit Demo")
    if config.bybit.base_url != "https://api-demo.bybit.com":
        raise RuntimeError("Demo soak requires Bybit Demo base URL")
    if config.market is not Market.LINEAR or config.futures_runtime.category != "linear":
        raise RuntimeError("Demo soak supports only linear futures")
    if config.futures_runtime.active_execution_venue is not ExecutionVenue.BYBIT_DEMO_FUTURES:
        raise RuntimeError("Demo soak requires Bybit Demo futures ACTIVE venue")
    if config.futures_runtime.test_execution_venue is not ExecutionVenue.LOCAL_TEST_SIMULATION:
        raise RuntimeError("Demo soak requires local TEST simulation")


def _env_true(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    try:
        result = run_soak()
    except Exception as exc:  # noqa: BLE001 - CLI reports sanitized class/message without secrets.
        print(f"TriggerTrade Demo soak unavailable: {exc}")
        return 1
    print(
        "TriggerTrade Demo soak completed: "
        f"cycles={result.cycles_completed}/{result.cycles_requested} status={result.status} db={result.db_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
