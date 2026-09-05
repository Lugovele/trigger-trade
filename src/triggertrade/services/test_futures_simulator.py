"""Isolated deterministic TEST-lane futures simulator."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta
from decimal import Decimal
from hashlib import sha256

from triggertrade.accounting import FuturesFillEvent, close_futures_trade
from triggertrade.execution.futures import FuturesTradeIntent, PositionAction, PositionState
from triggertrade.market_data import FuturesMarketEvent
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore


TEST_SIMULATOR_VERSION = "test-sim-v1"


@dataclass(frozen=True)
class TestSimulationResult:
    trade_id: str
    closed: bool
    evidence_source: str = "test_simulation"
    simulation_model_version: str = TEST_SIMULATOR_VERSION


class TestFuturesSimulator:
    """Small deterministic simulation for TEST evidence; no exchange calls."""

    uses_private_exchange_orders = False

    def __init__(self, *, accounting_store: FuturesAccountingStore, maker_fee_rate: Decimal) -> None:
        self._accounting_store = accounting_store
        self._maker_fee_rate = maker_fee_rate

    def simulate_closed_trade(self, *, intent: FuturesTradeIntent, event: FuturesMarketEvent) -> TestSimulationResult:
        if intent.lane != "TEST":
            raise ValueError("test simulator only accepts TEST lane intents")
        if intent.action is not PositionAction.OPEN_LONG:
            raise ValueError("test simulator v1 supports OPEN_LONG only")
        trade_id = _trade_id(intent)
        entry_fee = intent.quantity * event.close * self._maker_fee_rate
        exit_fee = intent.quantity * event.close * self._maker_fee_rate
        entry = FuturesFillEvent(
            event_id=f"{trade_id}-entry",
            trade_id=trade_id,
            execution_id=f"{trade_id}-sim-entry",
            symbol=intent.symbol,
            direction=PositionState.LONG,
            action=PositionAction.OPEN_LONG.value,
            quantity=intent.quantity,
            price=event.close,
            fee=entry_fee,
            fee_asset="USDT",
            occurred_at=event.close_time.isoformat(),
            requested_price=intent.price,
            trigger_set_id=intent.trigger_set_id,
            trigger_set_version=intent.trigger_set_version,
            regime_label=intent.regime_state,
            source="test_simulation",
        )
        exit_fill = FuturesFillEvent(
            event_id=f"{trade_id}-exit",
            trade_id=trade_id,
            execution_id=f"{trade_id}-sim-exit",
            symbol=intent.symbol,
            direction=PositionState.LONG,
            action=PositionAction.CLOSE_LONG.value,
            quantity=intent.quantity,
            price=event.close,
            fee=exit_fee,
            fee_asset="USDT",
            occurred_at=(event.close_time + timedelta(seconds=1)).isoformat(),
            requested_price=event.close,
            trigger_set_id=intent.trigger_set_id,
            trigger_set_version=intent.trigger_set_version,
            regime_label=intent.regime_state,
            source="test_simulation",
        )
        self._accounting_store.record_fill(entry)
        self._accounting_store.record_fill(exit_fill)
        closed = replace(
            close_futures_trade(trade_id=trade_id, entry_fills=(entry,), exit_fills=(exit_fill,), leverage=intent.configured_leverage),
            evidence_source="test_simulation",
            simulation_model_version=TEST_SIMULATOR_VERSION,
        )
        self._accounting_store.record_closed_trade(closed)
        return TestSimulationResult(trade_id=trade_id, closed=True)


def _trade_id(intent: FuturesTradeIntent) -> str:
    raw = "|".join([TEST_SIMULATOR_VERSION, intent.lane or "", intent.trigger_set_id or "", intent.trigger_set_version or "", intent.intent_id])
    return f"simtrade-{sha256(raw.encode('utf-8')).hexdigest()[:24]}"
