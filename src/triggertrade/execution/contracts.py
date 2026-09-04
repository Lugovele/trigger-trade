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


@dataclass(frozen=True)
class RiskDecision:
    risk_decision_id: str
    intent_id: str
    approved: bool
    reason: str = "manual technical fixture"
