"""Opt-in Bybit Demo public instrument catalog smoke."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from triggertrade.config import BybitConfig, BybitEnvironment  # noqa: E402
from triggertrade.exchanges import BybitDemoClient  # noqa: E402
from triggertrade.persistence import InstrumentCatalogStore  # noqa: E402
from triggertrade.services.instrument_catalog import InstrumentCatalogService  # noqa: E402


def main() -> int:
    if os.environ.get("RUN_TRIGGERTRADE_INSTRUMENT_CATALOG_SMOKE") != "1":
        print("SKIPPED: set RUN_TRIGGERTRADE_INSTRUMENT_CATALOG_SMOKE=1 to fetch Bybit public instrument metadata")
        return 0
    config = BybitConfig(environment=BybitEnvironment.DEMO, base_url="https://api-demo.bybit.com")
    client = BybitDemoClient(config=config)
    with tempfile.TemporaryDirectory(prefix="triggertrade-catalog-", ignore_cleanup_errors=True) as tmp:
        service = InstrumentCatalogService(store=InstrumentCatalogStore(Path(tmp) / "catalog.sqlite3"), client=client)
        result = service.refresh_instrument_catalog()
        if result.status != "OK":
            print(f"FAILED: public catalog refresh failed: {result.error}")
            return 1
        btc = service.validate_symbol("BTCUSDT")
        print("OK: Bybit Demo public linear instrument catalog")
        print(f"source=GET https://api-demo.bybit.com/v5/market/instruments-info category=linear")
        print(f"fetched_count={result.fetched_count}")
        print(f"tradeable_count={result.tradeable_count}")
        print(f"symbol={btc.symbol}")
        print(f"settle_coin={btc.settle_coin}")
        print(f"contract_type={btc.contract_type}")
        print(f"status={btc.status}")
        print(f"tick_size={btc.tick_size}")
        print(f"qty_step={btc.qty_step}")
        print(f"min_order_qty={btc.min_order_qty}")
        print(f"max_leverage={btc.max_leverage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
