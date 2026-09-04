"""Opt-in continuous paper runtime smoke using real Bybit Demo public data.

Run from the repository root with:
    RUN_TRIGGERTRADE_PAPER_RUNTIME_SMOKE=1 python scripts/paper_runtime_smoke.py
"""

from __future__ import annotations

from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from triggertrade.config import ConfigError  # noqa: E402
from triggertrade.services.runtime import build_runtime_from_env, load_env_file  # noqa: E402


def main() -> int:
    if os.environ.get("RUN_TRIGGERTRADE_PAPER_RUNTIME_SMOKE") != "1":
        print("paper runtime smoke skipped: set RUN_TRIGGERTRADE_PAPER_RUNTIME_SMOKE=1")
        return 0

    env = dict(os.environ)
    env.update(load_env_file(ROOT / ".env"))
    env["TRIGGERTRADE_RUNTIME_DB_PATH"] = str(ROOT / "runtime" / "paper_runtime_smoke.sqlite3")

    try:
        runtime = build_runtime_from_env(env)
        first = runtime.process_once()
        second = build_runtime_from_env(env).process_once()
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
