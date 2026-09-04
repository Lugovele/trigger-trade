"""Opt-in TriggerTrade e2e demo smoke.

Run from the repository root with:
    RUN_TRIGGERTRADE_E2E_DEMO_SMOKE=1 python scripts/triggertrade_e2e_demo_smoke.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
import os
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from triggertrade.config import ExecutionVenue, load_bybit_credentials, load_config  # noqa: E402
from triggertrade.execution import ExecutionService, OrderStatus  # noqa: E402
from triggertrade.execution.bybit import BybitExecutionAdapter  # noqa: E402
from triggertrade.exchanges import BybitDemoClient, parse_wallet_balance  # noqa: E402
from triggertrade.market_data import MarketObservation, parse_spot_instrument, parse_spot_ticker  # noqa: E402
from triggertrade.persistence import ExecutionStore, TraceStore  # noqa: E402
from triggertrade.risk import RiskManager  # noqa: E402
from triggertrade.strategies import BuyCandidateStrategy  # noqa: E402
from triggertrade.triggers import PercentagePriceMoveTrigger, SignalType  # noqa: E402


@dataclass(frozen=True)
class E2ESmokeResult:
    symbol: str
    signal_type: str
    intent_id: str
    risk_decision_id: str
    approved: bool
    order_type: str
    final_status: OrderStatus
    duplicate_count: int
    reconciled: bool
    trace_complete: bool


def main() -> int:
    if os.environ.get("RUN_TRIGGERTRADE_E2E_DEMO_SMOKE") != "1":
        print("TriggerTrade e2e demo smoke skipped: set RUN_TRIGGERTRADE_E2E_DEMO_SMOKE=1")
        return 0

    env = _load_env(ROOT / ".env")
    env.setdefault("TRIGGERTRADE_EXECUTION_VENUE", ExecutionVenue.BYBIT_DEMO.value)
    result = run_smoke(env)

    print("demo environment OK")
    print(f"symbol: {result.symbol}")
    print(f"signal: {result.signal_type}")
    print(f"intent id: {result.intent_id}")
    print(f"risk decision id: {result.risk_decision_id}")
    print(f"risk approved: {result.approved}")
    print(f"order type: {result.order_type}")
    print(f"final status: {result.final_status.value}")
    print(f"duplicate local records: {result.duplicate_count}")
    print(f"reconciled: {result.reconciled}")
    print(f"trace complete: {result.trace_complete}")
    return 0


def run_smoke(env: dict[str, str]) -> E2ESmokeResult:
    config = load_config(env)
    credentials = load_bybit_credentials(env)
    client = BybitDemoClient(config=config.bybit, credentials=credentials)
    instrument = parse_spot_instrument(client.instrument_metadata("BTCUSDT").result)
    ticker = parse_spot_ticker(client.ticker("BTCUSDT").result)
    balances = _first_available_balance(client, config.bybit.account_types)

    observation = _controlled_observation(config, ticker.last_price)
    signal = PercentagePriceMoveTrigger(config.trigger_rule).evaluate(observation)
    if signal.signal_type is not SignalType.BUY_CANDIDATE:
        raise RuntimeError("controlled observation did not produce BUY_CANDIDATE")

    strategy = BuyCandidateStrategy(config.strategy_rule, config.risk_rules)
    intent = strategy.decide(signal=signal, observation=observation, instrument=instrument)
    if intent is None:
        raise RuntimeError("STR-001 did not create an intent")

    store_path = ROOT / "runtime" / "triggertrade_e2e_demo_smoke.sqlite3"
    execution_store = ExecutionStore(store_path)
    trace_store = TraceStore(store_path)
    trace_store.save_trigger_evaluation(signal)
    trace_store.save_strategy_decision(intent)

    risk = RiskManager(
        config=config,
        risk_config=config.risk_rules,
        execution_store=execution_store,
    ).evaluate(
        intent=intent,
        observation=observation,
        available_quote_balance=balances.get("USDT", Decimal("0")),
    )
    trace_store.save_risk_decision(risk)
    if not risk.approved:
        raise RuntimeError(f"risk rejected demo e2e intent: {risk.rejection_reason}")

    service = ExecutionService(
        config=config,
        adapter=BybitExecutionAdapter(client),
        store=execution_store,
        instrument=instrument,
        available_quote_balance=balances.get("USDT", Decimal("0")),
    )
    record = service.submit_approved_limit_order(intent=intent, risk_decision=risk)
    fetched = service.reconcile(record)
    final = fetched
    if fetched.status in {OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED, OrderStatus.UNKNOWN}:
        final = service.cancel(fetched)
        final = service.reconcile(final)

    duplicate_count = execution_store.count_by_client_order_id(final.client_order_id)
    trace = trace_store.trace_for_intent(intent.intent_id)
    trace_complete = (
        bool(trace["signals"])
        and trace["strategy"] is not None
        and trace["risk"] is not None
        and execution_store.get_by_intent(intent.intent_id) is not None
    )
    if duplicate_count != 1:
        raise RuntimeError("expected exactly one execution lifecycle record")
    if not trace_complete:
        raise RuntimeError("traceability chain is incomplete")

    return E2ESmokeResult(
        symbol=final.symbol,
        signal_type=signal.signal_type.value,
        intent_id=intent.intent_id,
        risk_decision_id=risk.risk_decision_id,
        approved=risk.approved,
        order_type=final.order_type,
        final_status=final.status,
        duplicate_count=duplicate_count,
        reconciled=final.reconciliation_state == "reconciled",
        trace_complete=trace_complete,
    )


def _controlled_observation(config, current_market_price: Decimal) -> MarketObservation:
    synthetic_current = current_market_price * Decimal("0.98")
    return MarketObservation(
        symbol="BTCUSDT",
        observed_at=datetime.now(UTC),
        current_price=synthetic_current,
        previous_price=current_market_price,
        window=config.trigger_rule.lookback_window,
        source="controlled_e2e_demo_fixture",
        stale_after_seconds=config.trigger_rule.stale_after_seconds,
    )


def _first_available_balance(client: BybitDemoClient, account_types: tuple[str, ...]):
    last_error: Exception | None = None
    for account_type in account_types:
        try:
            return parse_wallet_balance(client.wallet_balance(account_type).result)
        except Exception as exc:
            last_error = exc
    raise RuntimeError("demo wallet balance unavailable") from last_error


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
