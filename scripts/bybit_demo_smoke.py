"""Manual Bybit Demo read-connectivity smoke check.

Run from the repository root with:
    python scripts/bybit_demo_smoke.py
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from triggertrade.config import ConfigError, load_bybit_credentials, load_config
from triggertrade.exchanges import BybitApiError, BybitDemoClient, parse_wallet_balance
from triggertrade.market_data import (
    parse_spot_candles,
    parse_spot_instrument,
    parse_spot_ticker,
)


def main() -> int:
    env = _load_env(ROOT / ".env")
    try:
        config = load_config(env)
        public_client = BybitDemoClient(config=config.bybit)

        public_client.public_connectivity()
        instrument = parse_spot_instrument(public_client.instrument_metadata("BTCUSDT").result)
        ticker = parse_spot_ticker(public_client.ticker("BTCUSDT").result)
        candles = parse_spot_candles(public_client.recent_candles("BTCUSDT").result)
        print("public connectivity OK")
        print(f"BTCUSDT metadata OK: {instrument.base_coin}/{instrument.quote_coin}")
        print(f"BTCUSDT ticker OK: lastPrice={ticker.last_price}")
        print(f"BTCUSDT candles OK: count={len(candles)}")

        credentials = load_bybit_credentials(env)
        private_client = BybitDemoClient(config=config.bybit, credentials=credentials)
        balance = _first_available_balance(private_client, config.bybit.account_types)

    except (BybitApiError, ConfigError, ValueError) as exc:
        print(f"Bybit Demo smoke failed: {exc}")
        return 1

    print("private auth OK")
    print(f"demo balance OK: coins={len(balance)}")
    return 0


def _first_available_balance(client: BybitDemoClient, account_types: tuple[str, ...]):
    last_error: Exception | None = None
    for account_type in account_types:
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
