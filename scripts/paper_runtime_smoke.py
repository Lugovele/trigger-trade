"""Opt-in continuous paper runtime smoke using real Bybit Demo public data.

Run from the repository root with:
    RUN_TRIGGERTRADE_PAPER_RUNTIME_SMOKE=1 python scripts/paper_runtime_smoke.py
"""

from __future__ import annotations

from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.smoke_guards import require_manual_smoke_opt_in, smoke_metadata  # noqa: E402
from triggertrade.config import ConfigError, ExecutionVenue, load_config  # noqa: E402
from triggertrade.exchanges import BybitDemoClient  # noqa: E402
from triggertrade.persistence import ExecutionStore, RuntimeStore, TraceStore  # noqa: E402
from triggertrade.services.bootstrap import load_env_file  # noqa: E402
from triggertrade.services.runtime import PaperTradingRuntime  # noqa: E402


OPT_IN_FLAG = "RUN_TRIGGERTRADE_PAPER_RUNTIME_SMOKE"


def main() -> int:
    try:
        require_manual_smoke_opt_in(os.environ, OPT_IN_FLAG, "paper runtime smoke")
    except RuntimeError as exc:
        print(f"paper runtime smoke skipped: {exc}")
        return 0

    env = dict(os.environ)
    env.update(load_env_file(ROOT / ".env"))
    env["TRIGGERTRADE_RUNTIME_DB_PATH"] = str(ROOT / "runtime" / "paper_runtime_smoke.sqlite3")

    try:
        runtime = build_legacy_paper_runtime_from_env(env)
        first = runtime.process_once()
        second = build_legacy_paper_runtime_from_env(env).process_once()
    except ConfigError as exc:
        print(f"paper runtime smoke refused unsafe config: {exc}")
        return 1

    print("paper runtime safe config OK")
    print(f"first candle id: {first.candle_id}")
    print(f"first signal: {first.signal_type}")
    print(f"first intent id: {first.intent_id}")
    print(f"first risk approved: {first.risk_approved}")
    print(f"first execution status: {first.execution_status}")
    print(f"second skipped reason: {second.skipped_reason}")
    print("private/order API calls: 0")
    print(f"classification: {smoke_metadata(OPT_IN_FLAG)['classification']}")
    return 0


def build_legacy_paper_runtime_from_env(env: dict[str, str]) -> PaperTradingRuntime:
    config = load_config(env)
    if config.execution_venue is not ExecutionVenue.LOCAL_PAPER:
        raise ConfigError("paper runtime smoke is legacy/demo-only and requires local_paper execution venue")
    db_path = Path(env["TRIGGERTRADE_RUNTIME_DB_PATH"])
    return PaperTradingRuntime(
        config=config,
        market_client=BybitDemoClient(config=config.bybit),
        execution_store=ExecutionStore(db_path),
        trace_store=TraceStore(db_path),
        runtime_store=RuntimeStore(db_path),
    )


if __name__ == "__main__":
    raise SystemExit(main())
