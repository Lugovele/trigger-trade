"""Minimal execution contracts with no exchange-specific behavior."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


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


@dataclass(frozen=True)
class ExecutionRequest:
    intent_id: str
    idempotency_key: str
    symbol: str


@dataclass(frozen=True)
class ExecutionResult:
    request_id: str
    status: OrderStatus
    exchange_order_id: str | None = None


class ExecutionAdapter(Protocol):
    def submit(self, request: ExecutionRequest) -> ExecutionResult:
        """Submit through an execution adapter after risk approval."""
