"""Backend analytics over authoritative accounting facts."""

from .futures import (
    BaselineComparison,
    FuturesPerformanceMetrics,
    PerformanceQualityPolicy,
    TradePerformanceFact,
    compare_baseline,
    compute_futures_performance,
    group_trade_facts,
)

__all__ = [
    "BaselineComparison",
    "FuturesPerformanceMetrics",
    "PerformanceQualityPolicy",
    "TradePerformanceFact",
    "compare_baseline",
    "compute_futures_performance",
    "group_trade_facts",
]
