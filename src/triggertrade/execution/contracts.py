"""Minimal execution contracts with no exchange-specific behavior."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class OrderStatus(StrEnum):
    CREATED = "created"
    SUBMITTING = "submitting"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCEL_PENDING = "cancel_pending"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


class Side(StrEnum):
    BUY = "Buy"
    SELL = "Sell"


class OrderType(StrEnum):
    LIMIT = "Limit"


@dataclass(frozen=True)
class TradeIntent:
    intent_id: str
    symbol: str
    side: Side
    order_type: OrderType
    quantity: Decimal
    price: Decimal
    strategy_rule_id: str = "manual"
    strategy_rule_version: str = "0"
    reason_signal_ids: tuple[str, ...] = ()
    reason_trigger_ids: tuple[str, ...] = ()
    created_at: str | None = None
    lane: str | None = None
    trigger_set_id: str | None = None
    trigger_set_version: str | None = None
    regime_context_id: str | None = None
    regime_rule_id: str | None = None
    regime_rule_version: str | None = None
    regime_state: str | None = None


@dataclass(frozen=True)
class RiskDecision:
    risk_decision_id: str
    intent_id: str
    approved: bool
    checked_rule_ids: tuple[str, ...] = ()
    blocking_rule_ids: tuple[str, ...] = ()
    approved_notional: Decimal | None = None
    approved_quantity: Decimal | None = None
    rejection_reason: str | None = None
    created_at: str | None = None
    reason: str = "manual technical fixture"
    lane: str | None = None
    trigger_set_id: str | None = None
    trigger_set_version: str | None = None
