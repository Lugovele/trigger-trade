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
    "CostEstimate",
    "FundingEstimate",
    "FuturesExecutionConfig",
    "FuturesExecutionService",
    "FuturesRiskDecision",
    "FuturesRiskManager",
    "FuturesTradeIntent",
    "MarginMode",
    "NetEdgeEstimate",
    "PaperExecutionAdapter",
    "PositionAction",
    "PositionMode",
    "PositionState",
    "OrderStatus",
    "OrderType",
    "RiskDecision",
    "Side",
    "TradeIntent",
    "estimate_costs",
    "estimate_net_edge",
    "futures_client_order_id",
    "futures_exchange_side",
    "next_position_state",
]


def __getattr__(name: str):
    if name in {"ExecutionError", "ExecutionService"}:
        from .service import ExecutionError, ExecutionService

        return {"ExecutionError": ExecutionError, "ExecutionService": ExecutionService}[name]
    if name == "PaperExecutionAdapter":
        from .paper import PaperExecutionAdapter

        return PaperExecutionAdapter
    futures_names = {
        "CostEstimate",
        "FundingEstimate",
        "FuturesExecutionConfig",
        "FuturesExecutionService",
        "FuturesRiskDecision",
        "FuturesRiskManager",
        "FuturesTradeIntent",
        "MarginMode",
        "NetEdgeEstimate",
        "PositionAction",
        "PositionMode",
        "PositionState",
        "estimate_costs",
        "estimate_net_edge",
        "futures_client_order_id",
        "futures_exchange_side",
        "next_position_state",
    }
    if name in futures_names:
        from . import futures

        return getattr(futures, name)
    raise AttributeError(name)
