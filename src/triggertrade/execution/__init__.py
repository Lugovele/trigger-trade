"""Execution boundary for order lifecycle management."""

from .contracts import (
    OrderStatus,
    OrderType,
    RiskDecision,
    Side,
    TradeIntent,
)

__all__ = [
    "ExecutionError",
    "ExecutionService",
    "PaperExecutionAdapter",
    "OrderStatus",
    "OrderType",
    "RiskDecision",
    "Side",
    "TradeIntent",
]


def __getattr__(name: str):
    if name in {"ExecutionError", "ExecutionService"}:
        from .service import ExecutionError, ExecutionService

        return {"ExecutionError": ExecutionError, "ExecutionService": ExecutionService}[name]
    if name == "PaperExecutionAdapter":
        from .paper import PaperExecutionAdapter

        return PaperExecutionAdapter
    raise AttributeError(name)
