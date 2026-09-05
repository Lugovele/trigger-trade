"""No-lookahead BACKTEST simulator using existing accounting formulas."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from hashlib import sha256

from triggertrade.accounting import FuturesFillEvent, close_futures_trade
from triggertrade.execution.futures import FuturesTradeIntent, PositionAction, PositionState
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore

from .models import BACKTEST_EVIDENCE_SOURCE, BACKTEST_SIMULATOR_VERSION, HistoricalCandle


class BacktestSimulationError(ValueError):
    pass


class BacktestFuturesSimulator:
    """Versioned one-candle simulator: decision at t, fill no earlier than t+1."""

    uses_private_exchange_orders = False

    def __init__(
        self,
        *,
        accounting_store: FuturesAccountingStore,
        maker_fee_rate: Decimal,
        taker_fee_rate: Decimal,
        spread_bps: Decimal,
        slippage_bps: Decimal,
    ) -> None:
        self._accounting_store = accounting_store
        self._maker_fee_rate = maker_fee_rate
        self._taker_fee_rate = taker_fee_rate
        self._spread_bps = spread_bps
        self._slippage_bps = slippage_bps

    def simulate_closed_trade(self, *, backtest_run_id: str, intent: FuturesTradeIntent, next_candle: HistoricalCandle) -> str:
        if intent.action is not PositionAction.OPEN_LONG:
            raise BacktestSimulationError("backtest simulator v1 matches runtime OPEN_LONG-only capability")
        if intent.category.value != "linear" or next_candle.category != "linear":
            raise BacktestSimulationError("backtest simulator supports linear perpetual only")
        if _crosses_funding_boundary(next_candle):
            raise BacktestSimulationError("funding unsupported for positions crossing funding timestamp")
        trade_id = _trade_id(backtest_run_id, intent)
        entry_price = _apply_cost_bps(next_candle.open, self._spread_bps + self._slippage_bps, long_entry=True)
        exit_price = _apply_cost_bps(next_candle.close, self._spread_bps + self._slippage_bps, long_entry=False)
        entry_fee = intent.quantity * entry_price * self._maker_fee_rate
        exit_fee = intent.quantity * exit_price * self._taker_fee_rate
        entry = FuturesFillEvent(
            event_id=f"{trade_id}-entry",
            trade_id=trade_id,
            execution_id=f"{trade_id}-sim-entry",
            symbol=intent.symbol,
            direction=PositionState.LONG,
            action=PositionAction.OPEN_LONG.value,
            quantity=intent.quantity,
            price=entry_price,
            fee=entry_fee,
            fee_asset="USDT",
            occurred_at=next_candle.open_time.isoformat(),
            requested_price=intent.price,
            trigger_set_id=intent.trigger_set_id,
            trigger_set_version=intent.trigger_set_version,
            regime_label=intent.regime_state,
            source=BACKTEST_EVIDENCE_SOURCE,
        )
        exit_fill = FuturesFillEvent(
            event_id=f"{trade_id}-exit",
            trade_id=trade_id,
            execution_id=f"{trade_id}-sim-exit",
            symbol=intent.symbol,
            direction=PositionState.LONG,
            action=PositionAction.CLOSE_LONG.value,
            quantity=intent.quantity,
            price=exit_price,
            fee=exit_fee,
            fee_asset="USDT",
            occurred_at=next_candle.close_time.isoformat(),
            requested_price=next_candle.close,
            trigger_set_id=intent.trigger_set_id,
            trigger_set_version=intent.trigger_set_version,
            regime_label=intent.regime_state,
            source=BACKTEST_EVIDENCE_SOURCE,
        )
        self._accounting_store.record_fill(entry)
        self._accounting_store.record_fill(exit_fill)
        closed = replace(
            close_futures_trade(trade_id=trade_id, entry_fills=(entry,), exit_fills=(exit_fill,), leverage=intent.configured_leverage),
            evidence_source=BACKTEST_EVIDENCE_SOURCE,
            simulation_model_version=BACKTEST_SIMULATOR_VERSION,
        )
        self._accounting_store.record_closed_trade(closed)
        return trade_id


def _trade_id(backtest_run_id: str, intent: FuturesTradeIntent) -> str:
    raw = "|".join([BACKTEST_SIMULATOR_VERSION, backtest_run_id, intent.trigger_set_id or "", intent.trigger_set_version or "", intent.intent_id])
    return f"btt-{sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _apply_cost_bps(price: Decimal, bps: Decimal, *, long_entry: bool) -> Decimal:
    multiplier = Decimal("1") + (bps / Decimal("10000")) if long_entry else Decimal("1") - (bps / Decimal("10000"))
    return price * multiplier


def _crosses_funding_boundary(candle: HistoricalCandle) -> bool:
    current = candle.open_time.replace(minute=0, second=0, microsecond=0)
    while current <= candle.close_time:
        if current.hour in {0, 8, 16} and candle.open_time < current <= candle.close_time:
            return True
        current += timedelta(hours=1)
    return False
