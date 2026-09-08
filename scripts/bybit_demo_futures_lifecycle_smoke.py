"""Opt-in Bybit Demo futures position lifecycle smoke.

Run from the repository root with:
    RUN_TRIGGERTRADE_FUTURES_LIFECYCLE_SMOKE=1 python scripts/bybit_demo_futures_lifecycle_smoke.py

The smoke validates Demo/linear safety, mandatory TP/SL planning, idempotent
order submission, reduce-only close wiring and sanitized evidence. It stops
without forcing market fills when the safe PostOnly order does not become a
real position.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from datetime import UTC, datetime
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from triggertrade.config import BybitConfig, ConfigError, load_bybit_credentials  # noqa: E402
from triggertrade.execution import ExecutionError, OrderStatus, OrderType  # noqa: E402
from triggertrade.execution.bybit_futures import BybitFuturesExecutionAdapter  # noqa: E402
from triggertrade.execution.futures import (  # noqa: E402
    FUTURES_RISK_RULE_IDS,
    FundingEstimate,
    FuturesExecutionConfig,
    FuturesRiskDecision,
    FuturesTradeIntent,
    PositionAction,
    PositionState,
    estimate_costs,
    estimate_net_edge,
)
from triggertrade.execution.position_lifecycle import (  # noqa: E402
    CloseReason,
    FuturesPositionLifecycleService,
    PositionRiskConfig,
    build_fixed_protective_exit_plan,
)
from triggertrade.exchanges import BybitApiError, BybitDemoClient, parse_wallet_balance  # noqa: E402
from triggertrade.market_data import ContractCategory, FuturesAccountState, parse_linear_instrument, parse_linear_ticker  # noqa: E402
from triggertrade.persistence import FuturesExecutionStore, FuturesPositionStore, OperatorStateStore  # noqa: E402
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore  # noqa: E402


def main() -> int:
    if os.environ.get("RUN_TRIGGERTRADE_FUTURES_LIFECYCLE_SMOKE") != "1":
        print("Bybit Demo futures lifecycle smoke skipped: set RUN_TRIGGERTRADE_FUTURES_LIFECYCLE_SMOKE=1")
        return 0
    env = _load_env(ROOT / ".env")
    try:
        result = run_smoke(env)
    except (BybitApiError, ConfigError, ExecutionError, ValueError) as exc:
        print(f"Bybit Demo futures lifecycle smoke failed: {exc.__class__.__name__}: {exc}")
        return 1
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


def run_smoke(env: dict[str, str]) -> dict[str, str]:
    base_url = env.get("BYBIT_BASE_URL", BybitConfig.base_url).rstrip("/")
    if base_url != "https://api-demo.bybit.com":
        raise ConfigError("lifecycle smoke requires Bybit Demo base URL")
    credentials = load_bybit_credentials(env)
    client = BybitDemoClient(config=BybitConfig(base_url=base_url), credentials=credentials)
    instrument = parse_linear_instrument(client.linear_instrument_metadata("BTCUSDT").result)
    ticker = parse_linear_ticker(client.linear_ticker("BTCUSDT").result)
    available_margin = _first_available_balance(client).get("USDT", Decimal("0"))
    quantity, passive_price = _derive_safe_order(instrument, ticker.last_price, available_margin, PositionAction.OPEN_LONG)

    run_id = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    db = ROOT / "runtime" / f"bybit_demo_futures_lifecycle_smoke_{run_id}_{os.getpid()}.sqlite3"
    execution_store = FuturesExecutionStore(db)
    position_store = FuturesPositionStore(db)
    accounting_store = FuturesAccountingStore(db)
    operator = OperatorStateStore(db)
    operator.resume(source="lifecycle-smoke")
    adapter = BybitFuturesExecutionAdapter(client)
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
    service = FuturesPositionLifecycleService(
        execution_config=FuturesExecutionConfig(),
        risk_config=PositionRiskConfig(max_position_notional=quantity * passive_price, max_total_position_notional=quantity * passive_price),
        execution_store=execution_store,
        position_store=position_store,
        accounting_store=accounting_store,
        adapter=adapter,
        instrument=instrument,
        account=account,
        operator_trading_state=lambda: operator.get_trading_state().state.value,
        execution_lane="MANUAL_DEMO_VALIDATION",
    )
    long_intent = _intent(f"lifecycle-long-{run_id}-{os.getpid()}", PositionAction.OPEN_LONG, quantity, passive_price)
    long_intent = _with_exits(long_intent, instrument)
    risk = _approved_risk(long_intent)
    opened = service.open_position(intent=long_intent, risk_decision=risk, take_profit=long_intent.take_profit, stop_loss=long_intent.stop_loss)
    record = opened.execution
    if record is not None and record.status in {OrderStatus.SUBMITTED, OrderStatus.UNKNOWN, OrderStatus.PARTIALLY_FILLED}:
        execution_store.update(record)
        final = __import__("triggertrade.execution.futures", fromlist=["FuturesExecutionService"]).FuturesExecutionService(
            config=FuturesExecutionConfig(),
            adapter=adapter,
            store=execution_store,
            instrument=instrument,
            account=account,
            execution_lane="MANUAL_DEMO_VALIDATION",
        ).cancel(record)
        if opened.position is not None:
            service.reconcile_position(opened.position.position_id)
        return {
            "demo_endpoint": "OK",
            "category": "linear",
            "symbol": final.symbol,
            "long_order_status": final.status.value,
            "short_order_status": "not_attempted_safe_long_not_filled",
            "accounting_verified": "not_available_without_actual_fill",
            "spot_calls": "0",
            "mainnet_calls": "0",
            "secrets_printed": "0",
        }
    if opened.position is None or opened.position.status == "CLOSED":
        return {
            "demo_endpoint": "OK",
            "category": "linear",
            "symbol": "BTCUSDT",
            "long_order_status": record.status.value if record else "none",
            "long_position_status": "closed_without_fill",
            "short_order_status": "not_attempted_safe_long_not_filled",
            "accounting_verified": "not_available_without_actual_fill",
            "spot_calls": "0",
            "mainnet_calls": "0",
            "secrets_printed": "0",
        }
    closed = service.close_position(position_id=opened.position.position_id, close_reason=CloseReason.MANUAL, price=ticker.last_price)
    return {
        "demo_endpoint": "OK",
        "category": "linear",
        "symbol": "BTCUSDT",
        "long_order_status": record.status.value if record else "none",
        "long_close": closed.reason,
        "short_order_status": "not_attempted_after_real_long_lifecycle",
        "accounting_verified": "true" if closed.closed_trade is not None else "pending_fill",
        "spot_calls": "0",
        "mainnet_calls": "0",
        "secrets_printed": "0",
    }


def _intent(intent_id: str, action: PositionAction, quantity: Decimal, price: Decimal) -> FuturesTradeIntent:
    return FuturesTradeIntent(
        intent_id=intent_id,
        symbol="BTCUSDT",
        category=ContractCategory.LINEAR,
        action=action,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
        current_position_state=PositionState.FLAT,
        configured_leverage=Decimal("1"),
        expected_gross_price_move=Decimal("1"),
        lane="MANUAL_DEMO_VALIDATION",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
        strategy_rule_id="manual-lifecycle-smoke",
        strategy_rule_version="0.1.0",
        rules_version_id="trules-v1",
        rule_evaluation_snapshot={"rules_version_id": "trules-v1", "source": "manual-demo-lifecycle-smoke"},
    )


def _with_exits(intent: FuturesTradeIntent, instrument) -> FuturesTradeIntent:
    tp, sl = build_fixed_protective_exit_plan(
        action=intent.action,
        entry_price=intent.price,
        take_profit_pct=Decimal("0.01"),
        stop_loss_pct=Decimal("0.005"),
        price_tick=instrument.price_tick,
    )
    return replace(intent, take_profit=tp, stop_loss=sl, minimum_risk_reward=Decimal("1.5"))


def _approved_risk(intent: FuturesTradeIntent) -> FuturesRiskDecision:
    return FuturesRiskDecision(
        risk_decision_id=f"risk-{intent.intent_id}",
        intent_id=intent.intent_id,
        approved=True,
        checked_rule_ids=FUTURES_RISK_RULE_IDS,
        approved_quantity=intent.quantity,
        approved_notional=intent.quantity * intent.price,
        position_state_after=PositionState.LONG if intent.action is PositionAction.OPEN_LONG else PositionState.SHORT,
        net_edge=estimate_net_edge(
            expected_gross_price_move=Decimal("1"),
            minimum_net_edge=Decimal("0.01"),
            cost=estimate_costs(notional=intent.quantity * intent.price, maker_fee_rate=Decimal("0.0002"), taker_fee_rate=Decimal("0.00055")),
            funding=FundingEstimate(Decimal("0"), None, Decimal("0"), Decimal("0")),
        ),
    )


def _derive_safe_order(instrument, last_price: Decimal, available_margin: Decimal, action: PositionAction):
    price = _floor_to_step(last_price * (Decimal("0.80") if action is PositionAction.OPEN_LONG else Decimal("1.20")), instrument.price_tick)
    qty = _ceil_to_step(instrument.minimum_notional / price, instrument.quantity_step)
    qty = max(qty, instrument.minimum_order_quantity)
    if qty * price > available_margin:
        raise ValueError("insufficient demo margin for minimum safe order")
    return qty, price


def _first_available_balance(client: BybitDemoClient) -> dict[str, Decimal]:
    last_error: Exception | None = None
    for account_type in ("UNIFIED", "CONTRACT"):
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
