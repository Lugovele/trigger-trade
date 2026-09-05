"""STR-FUT-001 demo-only futures directional integration strategy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256

from triggertrade.execution import OrderType
from triggertrade.execution.futures import FuturesTradeIntent, PositionAction, PositionState
from triggertrade.market_data import ContractCategory, FuturesMarketEvent, MarketRegimeContext, MarketRegimeLabel
from triggertrade.trigger_sets import Lane, TriggerSetVersion
from triggertrade.triggers import Signal, SignalType


STR_FUT_RULE_ID = "STR-FUT-001"
STR_FUT_VERSION = "0.1.0"


@dataclass(frozen=True)
class FuturesStrategyDecision:
    action: PositionAction | None
    intent: FuturesTradeIntent | None
    reason: str


class IntegrationDirectionalFuturesStrategy:
    """Reduced integration strategy: OPEN_LONG only, demo/test evidence only."""

    def decide(
        self,
        *,
        trigger_set: TriggerSetVersion,
        lane: Lane,
        event: FuturesMarketEvent,
        primary_signal: Signal,
        volume_signal: Signal | None,
        regime_context: MarketRegimeContext,
        position_state: PositionState,
        quantity: Decimal,
        limit_price: Decimal,
        leverage: Decimal,
        expected_gross_move: Decimal | None,
        created_at: datetime,
    ) -> FuturesStrategyDecision:
        if not _signal_matches_event(primary_signal, event, trigger_set, lane, rule_id="TRG-001", version="0.2.0"):
            return FuturesStrategyDecision(None, None, "primary_trigger_provenance_mismatch")
        if position_state is not PositionState.FLAT:
            return FuturesStrategyDecision(None, None, "position_not_flat")
        if primary_signal.signal_type is not SignalType.BUY_CANDIDATE:
            return FuturesStrategyDecision(None, None, "primary_trigger_not_buy_candidate")
        if ("TRG-002", "0.2.0") in trigger_set.rule_versions and (
            volume_signal is None
            or volume_signal.signal_type is not SignalType.CONFIRMED
            or not _signal_matches_event(volume_signal, event, trigger_set, lane, rule_id="TRG-002", version="0.2.0")
        ):
            return FuturesStrategyDecision(None, None, "volume_not_confirmed")
        if not _regime_matches_event(regime_context, event):
            return FuturesStrategyDecision(None, None, "regime_provenance_mismatch")
        if regime_context.label not in {MarketRegimeLabel.DOWNTREND, MarketRegimeLabel.STRONG_DOWNTREND}:
            return FuturesStrategyDecision(None, None, "regime_not_downtrend_reversal_context")
        if expected_gross_move is None or expected_gross_move <= 0:
            return FuturesStrategyDecision(None, None, "demo_expected_gross_move_unavailable")

        intent = FuturesTradeIntent(
            intent_id=_intent_id(trigger_set, lane, event, primary_signal, regime_context),
            symbol=event.symbol,
            category=ContractCategory.LINEAR,
            action=PositionAction.OPEN_LONG,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=limit_price,
            current_position_state=position_state,
            configured_leverage=leverage,
            strategy_rule_id=STR_FUT_RULE_ID,
            strategy_rule_version=STR_FUT_VERSION,
            expected_gross_price_move=expected_gross_move,
            created_at=created_at.astimezone(UTC).isoformat(),
            lane=lane.value,
            trigger_set_id=trigger_set.set_id,
            trigger_set_version=trigger_set.version,
            regime_context_id=regime_context.context_id,
            regime_rule_id=regime_context.rule_id,
            regime_rule_version=regime_context.version,
            regime_state=None if regime_context.label is None else regime_context.label.value,
        )
        return FuturesStrategyDecision(PositionAction.OPEN_LONG, intent, "open_long_downtrend_reversal_candidate")


def _intent_id(
    trigger_set: TriggerSetVersion,
    lane: Lane,
    event: FuturesMarketEvent,
    primary_signal: Signal,
    regime_context: MarketRegimeContext,
) -> str:
    raw = "|".join(
        [
            STR_FUT_RULE_ID,
            STR_FUT_VERSION,
            lane.value,
            trigger_set.set_id,
            trigger_set.version,
            event.candle_id,
            primary_signal.signal_id,
            regime_context.context_id,
        ]
    )
    return f"fintent-{sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _signal_matches_event(
    signal: Signal,
    event: FuturesMarketEvent,
    trigger_set: TriggerSetVersion,
    lane: Lane,
    *,
    rule_id: str,
    version: str,
) -> bool:
    return (
        signal.trigger_rule_id == rule_id
        and signal.trigger_rule_version == version
        and signal.symbol == event.symbol
        and signal.window == event.timeframe
        and signal.observed_at == event.close_time.isoformat()
        and signal.lane == lane.value
        and signal.trigger_set_id == trigger_set.set_id
        and signal.trigger_set_version == trigger_set.version
        and event.category == ContractCategory.LINEAR.value
    )


def _regime_matches_event(regime_context: MarketRegimeContext, event: FuturesMarketEvent) -> bool:
    return (
        regime_context.rule_id == "CTX-REGIME"
        and regime_context.version == "0.1.0"
        and regime_context.symbol == event.symbol
        and regime_context.timeframe == event.timeframe
        and regime_context.observed_at == event.close_time.isoformat()
        and regime_context.capability.value == "available"
        and regime_context.label
        not in {
            MarketRegimeLabel.UNKNOWN,
            MarketRegimeLabel.INSUFFICIENT_DATA,
            None,
        }
        and (regime_context.input_snapshot or {}).get("category") == ContractCategory.LINEAR.value
    )
