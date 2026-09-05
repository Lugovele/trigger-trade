"""Backtest contracts with exact version pinning and evidence separation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


BACKTEST_EVIDENCE_SOURCE = "BACKTEST"
HISTORICAL_REPLAY_VERSION = "historical-replay-v1"
BACKTEST_SIMULATOR_VERSION = "backtest-sim-v1-next-candle"
BACKTEST_COST_MODEL_VERSION = "backtest-cost-v1-explicit-bps"
BACKTEST_SPREAD_MODEL_VERSION = "spread-fixed-bps-v1"
BACKTEST_SLIPPAGE_MODEL_VERSION = "slippage-fixed-bps-v1"
BACKTEST_FUNDING_MODEL_VERSION = "funding-unsupported-no-overlap-v1"
BACKTEST_DATA_SOURCE_VERSION = "bybit-demo-public-linear-kline-v1"


class BacktestStatus(StrEnum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BacktestStage(StrEnum):
    RESEARCH = "RESEARCH"
    VALIDATION = "VALIDATION"


@dataclass(frozen=True)
class HistoricalCandle:
    symbol: str
    category: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    turnover: Decimal
    completed: bool = True


@dataclass(frozen=True)
class BacktestPlan:
    symbol: str
    category: str
    timeframe: str
    research_start: datetime
    research_end: datetime
    validation_start: datetime | None = None
    validation_end: datetime | None = None
    warmup_candles: int = 60


@dataclass(frozen=True)
class BacktestRun:
    backtest_run_id: str
    created_at: str
    status: BacktestStatus
    symbol: str
    category: str
    timeframe: str
    period_start: str
    period_end: str
    trigger_set_id: str
    trigger_set_version: str
    rule_versions: tuple[tuple[str, str], ...]
    strategy_version: str
    regime_version: str
    risk_profile_version: str
    simulation_model_version: str
    cost_model_version: str
    accounting_version: str
    data_source_version: str
    data_cache_hash: str
    warmup_start: str
    evaluation_start: str
    evaluation_end: str
    spread_bps: Decimal
    slippage_bps: Decimal
    maker_fee_rate: Decimal
    taker_fee_rate: Decimal
    assumptions: dict[str, str]
    funding_model_version: str = BACKTEST_FUNDING_MODEL_VERSION
    notes: str = "internal historical replay; no profitability claim"


@dataclass(frozen=True)
class BacktestResult:
    backtest_run_id: str
    status: BacktestStatus
    candles_processed: int
    signals: int
    intents: int
    trades: int
    closed_trades: int
    rejected_intents: int
    no_action_count: int
    technical_failures: int
    net_pnl: Decimal
    expectancy: Decimal | None
    profit_factor: Decimal | None
    max_drawdown: Decimal | None
    fees: Decimal
    funding: Decimal
    long_trades: int
    short_trades: int
    by_regime: dict[str, int]
