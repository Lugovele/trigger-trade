"""Opt-in Bybit Demo Spot order lifecycle smoke check.

Run from the repository root with:
    RUN_BYBIT_DEMO_ORDER_SMOKE=1 python scripts/bybit_demo_order_smoke.py
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from triggertrade.config import (  # noqa: E402
    ConfigError,
    ExecutionVenue,
    load_bybit_credentials,
    load_config,
)
from triggertrade.execution import ExecutionError, ExecutionService, OrderStatus, OrderType, RiskDecision, Side, TradeIntent  # noqa: E402
from triggertrade.execution.bybit import BybitExecutionAdapter  # noqa: E402
from triggertrade.exchanges import BybitApiError, BybitDemoClient, parse_wallet_balance  # noqa: E402
from triggertrade.market_data import parse_spot_instrument, parse_spot_ticker  # noqa: E402
from triggertrade.persistence import ExecutionStore  # noqa: E402


@dataclass(frozen=True)
class SmokeResult:
    created: bool
    symbol: str
    order_type: str
    final_status: OrderStatus
    duplicate_count: int
    reconciled: bool


def main() -> int:
    if os.environ.get("RUN_BYBIT_DEMO_ORDER_SMOKE") != "1":
        print("Bybit Demo order smoke skipped: set RUN_BYBIT_DEMO_ORDER_SMOKE=1")
        return 0

    env = _load_env(ROOT / ".env")
    env.setdefault("TRIGGERTRADE_EXECUTION_VENUE", ExecutionVenue.BYBIT_DEMO.value)

    try:
        result = run_smoke(env)
    except (BybitApiError, ConfigError, ExecutionError, ValueError) as exc:
        print(f"Bybit Demo order smoke failed: {exc}")
        return 1

    print("demo environment OK")
    print(f"order created: {result.created}")
    print(f"symbol: {result.symbol}")
    print(f"order type: {result.order_type}")
    print(f"final status: {result.final_status.value}")
    print(f"duplicate local records: {result.duplicate_count}")
    print(f"reconciled: {result.reconciled}")
    return 0


def run_smoke(env: dict[str, str]) -> SmokeResult:
    config = load_config(env)
    credentials = load_bybit_credentials(env)
    client = BybitDemoClient(config=config.bybit, credentials=credentials)
    instrument = parse_spot_instrument(client.instrument_metadata("BTCUSDT").result)
    ticker = parse_spot_ticker(client.ticker("BTCUSDT").result)
    balances = _first_available_balance(client, config.bybit.account_types)
    quantity, price = _derive_safe_buy_order(instrument, ticker.last_price, balances.get("USDT", Decimal("0")))

    store_path = ROOT / "runtime" / "bybit_demo_order_smoke.sqlite3"
    store = ExecutionStore(store_path)
    service = ExecutionService(
        config=config,
        adapter=BybitExecutionAdapter(client),
        store=store,
        instrument=instrument,
        available_quote_balance=balances.get("USDT", Decimal("0")),
    )
    intent = TradeIntent(
        intent_id=f"manual-bybit-demo-btcusdt-{os.getpid()}",
        symbol="BTCUSDT",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
    )
    risk = RiskDecision(
        risk_decision_id=f"manual-risk-{intent.intent_id}",
        intent_id=intent.intent_id,
        approved=True,
        checked_rule_ids=("RSK-001", "RSK-002", "RSK-003", "RSK-004", "RSK-005"),
        blocking_rule_ids=(),
        approved_notional=quantity * price,
        approved_quantity=quantity,
        reason="manual demo smoke allow fixture",
    )

    record = service.submit_approved_limit_order(intent=intent, risk_decision=risk)
    created = record.exchange_order_id is not None
    fetched = service.reconcile(record)
    final = fetched
    if fetched.status in {OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED, OrderStatus.UNKNOWN}:
        final = service.cancel(fetched)
        final = service.reconcile(final)

    duplicate_count = store.count_by_client_order_id(final.client_order_id)
    if duplicate_count != 1:
        raise ExecutionError("idempotency check failed")
    if final.status not in {
        OrderStatus.CANCELLED,
        OrderStatus.FILLED,
        OrderStatus.PARTIALLY_FILLED,
        OrderStatus.UNKNOWN,
    }:
        raise ExecutionError("final order state is not an expected lifecycle state")

    return SmokeResult(
        created=created,
        symbol=final.symbol,
        order_type=final.order_type,
        final_status=final.status,
        duplicate_count=duplicate_count,
        reconciled=final.reconciliation_state == "reconciled",
    )


def _derive_safe_buy_order(instrument, last_price: Decimal, usdt_balance: Decimal):
    post_only_price = _floor_to_step(last_price * Decimal("0.80"), instrument.price_tick)
    if post_only_price <= 0:
        raise ValueError("could not derive a positive safe limit price")
    min_notional_qty = _ceil_to_step(
        instrument.min_order_amount / post_only_price,
        instrument.quantity_step,
    )
    quantity = max(instrument.min_order_quantity, min_notional_qty)
    notional = quantity * post_only_price
    if usdt_balance < notional:
        raise ValueError("insufficient demo USDT balance for minimum safe limit order")
    return quantity, post_only_price


def _first_available_balance(client: BybitDemoClient, account_types: tuple[str, ...]):
    last_error: Exception | None = None
    for account_type in account_types:
        try:
            return parse_wallet_balance(client.wallet_balance(account_type).result)
        except BybitApiError as exc:
            last_error = exc
    raise BybitApiError("demo wallet balance unavailable") from last_error


def _floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def _ceil_to_step(value: Decimal, step: Decimal) -> Decimal:
    units = (value / step).to_integral_value(rounding=ROUND_DOWN)
    if units * step < value:
        units += 1
    return units * step


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
