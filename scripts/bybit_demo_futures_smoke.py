"""Opt-in Bybit Demo linear perpetual lifecycle smoke.

Run from the repository root with:
    RUN_BYBIT_DEMO_FUTURES_SMOKE=1 python scripts/bybit_demo_futures_smoke.py
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from triggertrade.config import BybitConfig, ConfigError, load_bybit_credentials  # noqa: E402
from triggertrade.execution import ExecutionError, OrderStatus, OrderType  # noqa: E402
from triggertrade.execution.bybit_futures import BybitFuturesExecutionAdapter  # noqa: E402
from triggertrade.execution.futures import (  # noqa: E402
    FundingEstimate,
    FuturesExecutionConfig,
    FuturesExecutionService,
    FuturesRiskManager,
    FuturesTradeIntent,
    PositionAction,
    PositionState,
    estimate_costs,
)
from triggertrade.exchanges import BybitApiError, BybitDemoClient, parse_wallet_balance  # noqa: E402
from triggertrade.market_data import ContractCategory, FuturesAccountState, parse_linear_instrument, parse_linear_ticker  # noqa: E402
from triggertrade.persistence import FuturesExecutionStore  # noqa: E402


@dataclass(frozen=True)
class FuturesSmokeResult:
    created: bool
    symbol: str
    category: str
    action: str
    order_type: str
    leverage: str
    final_status: OrderStatus
    reconciled: bool
    duplicate_count: int


def main() -> int:
    if os.environ.get("RUN_BYBIT_DEMO_FUTURES_SMOKE") != "1":
        print("Bybit Demo futures smoke skipped: set RUN_BYBIT_DEMO_FUTURES_SMOKE=1")
        return 0

    env = _load_env(ROOT / ".env")
    try:
        result = run_smoke(env)
    except (BybitApiError, ConfigError, ExecutionError, ValueError) as exc:
        print(f"Bybit Demo futures smoke failed: {exc}")
        return 1

    print("demo endpoint OK")
    print(f"symbol: {result.symbol}")
    print(f"category: {result.category}")
    print(f"action: {result.action}")
    print(f"order type: {result.order_type}")
    print(f"leverage: {result.leverage}x")
    print(f"order created: {result.created}")
    print(f"final status: {result.final_status.value}")
    print(f"reconciled: {result.reconciled}")
    print(f"duplicate local records: {result.duplicate_count}")
    return 0


def run_smoke(env: dict[str, str]) -> FuturesSmokeResult:
    base_url = env.get("BYBIT_BASE_URL", BybitConfig.base_url).rstrip("/")
    if base_url != "https://api-demo.bybit.com":
        raise ConfigError("futures smoke requires Bybit Demo base URL")

    credentials = load_bybit_credentials(env)
    client = BybitDemoClient(config=BybitConfig(base_url=base_url), credentials=credentials)
    instrument = parse_linear_instrument(client.linear_instrument_metadata("BTCUSDT").result)
    ticker = parse_linear_ticker(client.linear_ticker("BTCUSDT").result)
    balances = _first_available_balance(client)
    available_margin = balances.get("USDT", Decimal("0"))
    quantity, price = _derive_safe_long_order(instrument, ticker.last_price, available_margin)

    config = FuturesExecutionConfig()
    account = FuturesAccountState(
        symbol="BTCUSDT",
        category=ContractCategory.LINEAR,
        settlement_asset="USDT",
        available_margin=available_margin,
        configured_leverage=Decimal("1"),
        margin_mode="ISOLATED",
        position_mode="ONE_WAY",
        mark_price=ticker.last_price,
    )
    store = FuturesExecutionStore(ROOT / "runtime" / "bybit_demo_futures_smoke.sqlite3")
    intent = FuturesTradeIntent(
        intent_id=f"manual-bybit-demo-linear-btcusdt-{os.getpid()}",
        symbol="BTCUSDT",
        category=ContractCategory.LINEAR,
        action=PositionAction.OPEN_LONG,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
        current_position_state=PositionState.FLAT,
        configured_leverage=Decimal("1"),
        expected_gross_price_move=Decimal("1"),
        lane="MANUAL_DEMO_VALIDATION",
    )
    cost = estimate_costs(
        notional=quantity * price,
        maker_fee_rate=Decimal("0.0002"),
        taker_fee_rate=Decimal("0.00055"),
    )
    funding = FundingEstimate(
        funding_rate=Decimal("0"),
        next_funding_time=None,
        expected_holding_overlap=Decimal("0"),
        estimated_funding_impact=Decimal("0"),
    )
    derived_notional = quantity * price
    risk = FuturesRiskManager(
        config=config,
        store=store,
        max_position_notional=derived_notional,
        max_simultaneous_exposure=derived_notional,
    ).evaluate(
        intent=intent,
        instrument=instrument,
        account=account,
        cost=cost,
        funding=funding,
    )
    service = FuturesExecutionService(
        config=config,
        adapter=BybitFuturesExecutionAdapter(client),
        store=store,
        instrument=instrument,
        account=account,
        execution_lane="MANUAL_DEMO_VALIDATION",
    )

    record = service.submit_approved_limit_order(intent=intent, risk_decision=risk)
    created = record.exchange_order_id is not None
    final = service.reconcile(record)
    if final.status in {OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED, OrderStatus.UNKNOWN}:
        final = service.cancel(final)
        final = service.reconcile(final)

    duplicate_count = 1 if store.get_by_client_order_id(final.client_order_id) is not None else 0
    if duplicate_count != 1:
        raise ExecutionError("futures idempotency check failed")
    if final.status not in {OrderStatus.CANCELLED, OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED, OrderStatus.UNKNOWN}:
        raise ExecutionError("final futures order state is not expected")

    return FuturesSmokeResult(
        created=created,
        symbol=final.symbol,
        category=final.category,
        action=final.position_action,
        order_type=final.order_type,
        leverage=final.leverage,
        final_status=final.status,
        reconciled=final.reconciliation_state == "reconciled",
        duplicate_count=duplicate_count,
    )


def _derive_safe_long_order(instrument, last_price: Decimal, available_margin: Decimal):
    post_only_price = _floor_to_step(last_price * Decimal("0.80"), instrument.price_tick)
    if post_only_price <= 0:
        raise ValueError("could not derive positive futures limit price")
    min_notional_qty = _ceil_to_step(instrument.minimum_notional / post_only_price, instrument.quantity_step)
    quantity = max(instrument.minimum_order_quantity, min_notional_qty)
    notional = quantity * post_only_price
    if available_margin < notional:
        raise ValueError("insufficient demo USDT margin for minimum futures order")
    return quantity, post_only_price


def _first_available_balance(client: BybitDemoClient) -> dict[str, Decimal]:
    last_error: Exception | None = None
    for account_type in ("UNIFIED", "SPOT"):
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
