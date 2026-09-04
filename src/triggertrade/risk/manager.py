"""Minimal deterministic risk manager for the demo e2e slice."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256

from triggertrade.config import (
    AppConfig,
    BybitEnvironment,
    ExecutionVenue,
    Market,
    RiskRulesConfig,
    TradingMode,
)
from triggertrade.execution import OrderType, RiskDecision, Side, TradeIntent
from triggertrade.execution.service import client_order_id_for_intent
from triggertrade.market_data import MarketObservation
from triggertrade.persistence import ExecutionStore


RULE_IDS = ("RSK-001", "RSK-002", "RSK-003", "RSK-004", "RSK-005")


class RiskManager:
    def __init__(
        self,
        *,
        config: AppConfig,
        risk_config: RiskRulesConfig,
        execution_store: ExecutionStore,
    ) -> None:
        self._config = config
        self._risk_config = risk_config
        self._execution_store = execution_store

    def evaluate(
        self,
        *,
        intent: TradeIntent,
        observation: MarketObservation,
        available_quote_balance: Decimal,
        now: datetime | None = None,
    ) -> RiskDecision:
        blocking: list[str] = []
        notional = intent.quantity * intent.price

        if notional > self._risk_config.max_demo_order_notional:
            blocking.append("RSK-001")
        if self._has_duplicate_or_open_intent(intent):
            blocking.append("RSK-002")
        if intent.side is Side.BUY and available_quote_balance < notional:
            blocking.append("RSK-003")
        if not self._demo_safety_ok(intent):
            blocking.append("RSK-004")
        if observation.is_stale(now) or observation.symbol != intent.symbol:
            blocking.append("RSK-005")

        approved = not blocking
        return RiskDecision(
            risk_decision_id=_risk_decision_id(intent.intent_id, tuple(blocking)),
            intent_id=intent.intent_id,
            approved=approved,
            checked_rule_ids=RULE_IDS,
            blocking_rule_ids=tuple(blocking),
            approved_notional=notional if approved else None,
            approved_quantity=intent.quantity if approved else None,
            rejection_reason=",".join(blocking) if blocking else None,
            created_at=datetime.now(UTC).isoformat(),
            reason="deterministic demo risk evaluation",
        )

    def _has_duplicate_or_open_intent(self, intent: TradeIntent) -> bool:
        if self._execution_store.get_by_intent(intent.intent_id) is not None:
            return True
        client_order_id = client_order_id_for_intent(intent.intent_id)
        if self._execution_store.get_by_client_order_id(client_order_id) is not None:
            return True
        return any(record.intent_id == intent.intent_id for record in self._execution_store.unresolved())

    def _demo_safety_ok(self, intent: TradeIntent) -> bool:
        return (
            self._config.trading_mode is TradingMode.PAPER
            and not self._config.live_trading_enabled
            and self._config.execution_venue is ExecutionVenue.BYBIT_DEMO
            and self._config.bybit.environment is BybitEnvironment.DEMO
            and self._config.bybit.base_url == "https://api-demo.bybit.com"
            and self._config.market is Market.SPOT
            and intent.symbol == "BTCUSDT"
            and intent.order_type is OrderType.LIMIT
        )


def _risk_decision_id(intent_id: str, blocking: tuple[str, ...]) -> str:
    raw = f"{intent_id}|{','.join(blocking)}"
    return f"risk-{sha256(raw.encode('utf-8')).hexdigest()[:24]}"
