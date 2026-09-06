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
    "CloseReason",
    "FuturesPositionLifecycleService",
    "PositionRiskConfig",
    "PositionStatus",
    "ProtectiveExitMode",
    "StopLossPlan",
    "TakeProfitPlan",
    "build_fixed_protective_exit_plan",
    "calculate_position_size",
    "evaluate_risk_reward",
    "should_trigger_protective_exit",
    "unrealized_pnl_pct",
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
    position_names = {
        "CloseReason",
        "FuturesPositionLifecycleService",
        "PositionRiskConfig",
        "PositionStatus",
        "ProtectiveExitMode",
        "StopLossPlan",
        "TakeProfitPlan",
        "build_fixed_protective_exit_plan",
        "calculate_position_size",
        "evaluate_risk_reward",
        "should_trigger_protective_exit",
        "unrealized_pnl_pct",
    }
    if name in position_names:
        from . import position_lifecycle

        return getattr(position_lifecycle, name)
    raise AttributeError(name)
