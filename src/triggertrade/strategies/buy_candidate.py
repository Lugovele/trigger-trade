"""STR-001 BUY intent creation from TRG-001 BUY_CANDIDATE signals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_DOWN
from hashlib import sha256

from triggertrade.config import RiskRulesConfig, StrategyRuleConfig
from triggertrade.execution import OrderType, Side, TradeIntent
from triggertrade.market_data import BybitInstrument, MarketObservation, MarketRegimeContext
from triggertrade.triggers import Signal, SignalType


@dataclass(frozen=True)
class BuyCandidateStrategy:
    config: StrategyRuleConfig
    risk_config: RiskRulesConfig

    def decide(
        self,
        *,
        signal: Signal,
        observation: MarketObservation,
        instrument: BybitInstrument,
        blocking_state: bool = False,
        regime_context: MarketRegimeContext | None = None,
    ) -> TradeIntent | None:
        if not self.config.enabled or blocking_state:
            return None
        if signal.signal_type is not SignalType.BUY_CANDIDATE:
            return None
        if signal.trigger_rule_id != "TRG-001":
            return None
        if signal.symbol != observation.symbol:
            return None
        if signal.window != observation.window:
            return None
        if instrument.symbol != signal.symbol:
            return None
        if observation.current_price is None:
            return None

        price = _floor_to_step(observation.current_price * Decimal("0.80"), instrument.price_tick)
        quantity = _demo_quantity(
            target_notional=self.risk_config.max_demo_order_notional,
            price=price,
            instrument=instrument,
        )
        intent_id = _intent_id(self.config.rule_id, self.config.version, signal.signal_id)
        return TradeIntent(
            intent_id=intent_id,
            strategy_rule_id=self.config.rule_id,
            strategy_rule_version=self.config.version,
            symbol=signal.symbol,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price,
            reason_signal_ids=(signal.signal_id,),
            reason_trigger_ids=(signal.trigger_rule_id,),
            created_at=datetime.now(UTC).isoformat(),
            regime_context_id=None if regime_context is None else regime_context.context_id,
            regime_rule_id=None if regime_context is None else regime_context.rule_id,
            regime_rule_version=None if regime_context is None else regime_context.version,
            regime_state=None if regime_context is None or regime_context.label is None else regime_context.label.value,
        )


def _demo_quantity(
    *,
    target_notional: Decimal,
    price: Decimal,
    instrument: BybitInstrument,
) -> Decimal:
    if price <= 0:
        raise ValueError("cannot derive demo quantity for non-positive price")
    target_quantity = _floor_to_step(target_notional / price, instrument.quantity_step)
    min_notional_quantity = _ceil_to_step(
        instrument.min_order_amount / price,
        instrument.quantity_step,
    )
    return max(instrument.min_order_quantity, target_quantity, min_notional_quantity)


def _floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def _ceil_to_step(value: Decimal, step: Decimal) -> Decimal:
    units = (value / step).to_integral_value(rounding=ROUND_DOWN)
    if units * step < value:
        units += 1
    return units * step


def _intent_id(rule_id: str, version: str, signal_id: str) -> str:
    raw = f"{rule_id}|{version}|{signal_id}"
    return f"intent-{sha256(raw.encode('utf-8')).hexdigest()[:24]}"
