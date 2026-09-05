"""Opt-in Bybit Demo futures accounting fact smoke.

Run from the repository root with:
    RUN_BYBIT_DEMO_FUTURES_ACCOUNTING_SMOKE=1 python scripts/bybit_demo_futures_accounting_smoke.py

This script does not create, amend, or cancel orders. It inspects actual
Bybit Demo linear execution facts for a persisted order when available.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from triggertrade.config import BybitConfig, ConfigError, load_bybit_credentials  # noqa: E402
from triggertrade.execution.bybit_futures import BybitFuturesExecutionAdapter  # noqa: E402
from triggertrade.exchanges import BybitApiError, BybitDemoClient, parse_wallet_balance  # noqa: E402
from triggertrade.persistence.futures_execution_store import FuturesExecutionStore  # noqa: E402


def main() -> int:
    if os.environ.get("RUN_BYBIT_DEMO_FUTURES_ACCOUNTING_SMOKE") != "1":
        print("Bybit Demo futures accounting smoke skipped: set RUN_BYBIT_DEMO_FUTURES_ACCOUNTING_SMOKE=1")
        return 0

    env = _load_env(ROOT / ".env")
    db_path = Path(env.get("TRIGGERTRADE_RUNTIME_DB_PATH", "runtime/triggertrade_paper.sqlite3"))
    try:
        result = run_smoke(env, db_path)
    except (BybitApiError, ConfigError, ValueError) as exc:
        print(f"Bybit Demo futures accounting smoke failed: {exc}")
        return 1

    print("demo endpoint OK")
    print(f"db: {db_path}")
    print(f"execution records inspected: {result['orders']}")
    print(f"actual execution fills discovered: {result['fills']}")
    print(f"wallet balance facts observed: {result['wallet_facts']}")
    print("equity snapshot recorded: False; wallet-only response is not treated as equity/margin/P&L")
    print("funding events discovered: unavailable unless Bybit returns attributed transaction facts")
    print("orders created by this smoke: 0")
    return 0


def run_smoke(env: dict[str, str], db_path: Path) -> dict[str, object]:
    base_url = env.get("BYBIT_BASE_URL", BybitConfig.base_url).rstrip("/")
    if base_url != "https://api-demo.bybit.com":
        raise ConfigError("futures accounting smoke requires Bybit Demo base URL")
    credentials = load_bybit_credentials(env)
    client = BybitDemoClient(config=BybitConfig(base_url=base_url), credentials=credentials)
    adapter = BybitFuturesExecutionAdapter(client)
    execution_store = FuturesExecutionStore(db_path)

    fills_seen = 0
    for record in execution_store.list_recent(limit=5):
        executions = adapter.fetch_executions(symbol=record.symbol, client_order_id=record.client_order_id)
        fills_seen += len(executions)

    balances = _first_available_balance(client)
    return {"orders": len(execution_store.list_recent(limit=5)), "fills": fills_seen, "wallet_facts": len(balances)}


def _first_available_balance(client: BybitDemoClient) -> dict[str, Decimal]:
    last_error: Exception | None = None
    for account_type in ("UNIFIED", "CONTRACT"):
        try:
            return parse_wallet_balance(client.wallet_balance(account_type).result)
        except BybitApiError as exc:
            last_error = exc
    raise BybitApiError("demo wallet balance unavailable") from last_error


def _load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


if __name__ == "__main__":
    raise SystemExit(main())
