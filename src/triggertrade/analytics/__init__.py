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
from .research_reports import (
    ENTRY_REPORT_ITEMS,
    ENTRY_SOURCE_ROWS,
    TAKE_PROFIT_REPORT_ITEMS,
    TAKE_PROFIT_SOURCE_ROWS,
    AssembledResearchReport,
    ResearchReportError,
    assemble_entry_report,
    assemble_take_profit_report,
)

__all__ = [
    "AssembledResearchReport",
    "BaselineComparison",
    "ENTRY_REPORT_ITEMS",
    "ENTRY_SOURCE_ROWS",
    "FuturesPerformanceMetrics",
    "PerformanceQualityPolicy",
    "ResearchReportError",
    "TAKE_PROFIT_REPORT_ITEMS",
    "TAKE_PROFIT_SOURCE_ROWS",
    "TradePerformanceFact",
    "assemble_entry_report",
    "assemble_take_profit_report",
    "compare_baseline",
    "compute_futures_performance",
    "group_trade_facts",
]
