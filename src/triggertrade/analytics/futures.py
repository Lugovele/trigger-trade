"""Deterministic futures performance metrics over accounting facts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class TradePerformanceFact:
    trade_id: str
    trigger_set_id: str
    trigger_set_version: str
    symbol: str
    direction: str
    closed_at: str
    net_pnl: Decimal
    gross_pnl: Decimal
    entry_fee: Decimal
    exit_fee: Decimal
    other_fees: Decimal
    funding: Decimal
    duration_seconds: int
    regime_label: str | None = None


@dataclass(frozen=True)
class PerformanceQualityPolicy:
    minimum_closed_trades: int = 50
    concentration_threshold_pct: Decimal = Decimal("80")
    high_fee_drag_pct: Decimal = Decimal("30")


@dataclass(frozen=True)
class FuturesPerformanceMetrics:
    set_id: str
    version: str
    status: str
    period: str
    closed_trades: int
    wins: int
    losses: int
    win_rate_pct: Decimal | None
    gross_profit: Decimal
    gross_loss: Decimal
    net_pnl: Decimal
    average_winner: Decimal | None
    average_loser: Decimal | None
    expectancy_per_trade: Decimal | None
    profit_factor: Decimal | None
    profit_factor_reason: str | None
    max_drawdown: Decimal | None
    average_duration_seconds: Decimal | None
    fees: Decimal
    funding: Decimal
    fees_as_pct_of_gross_profit: Decimal | None
    long: "FuturesPerformanceMetrics | None" = None
    short: "FuturesPerformanceMetrics | None" = None
    warnings: tuple[str, ...] = ()
    recommendation_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class BaselineComparison:
    baseline_set: str
    candidate_set: str
    overlap_period: str | None
    available: bool
    reason: str | None
    baseline_closed_trades: int = 0
    candidate_closed_trades: int = 0
    baseline_net_pnl: Decimal | None = None
    candidate_net_pnl: Decimal | None = None
    baseline_expectancy: Decimal | None = None
    candidate_expectancy: Decimal | None = None
    baseline_fees: Decimal | None = None
    candidate_fees: Decimal | None = None
    baseline_direction_mix: str | None = None
    candidate_direction_mix: str | None = None


def compute_futures_performance(
    *,
    set_id: str,
    version: str,
    status: str,
    trades: tuple[TradePerformanceFact, ...],
    max_drawdown: Decimal | None = None,
    include_direction_breakdown: bool = True,
    policy: PerformanceQualityPolicy | None = None,
) -> FuturesPerformanceMetrics:
    policy = policy or PerformanceQualityPolicy()
    sample = tuple(trades)
    _validate_trade_membership(sample, set_id=set_id, version=version, label="performance sample")
    closed = len(sample)
    wins = sum(1 for trade in sample if trade.net_pnl > 0)
    losses = sum(1 for trade in sample if trade.net_pnl < 0)
    gross_profit = sum((trade.gross_pnl for trade in sample if trade.gross_pnl > 0), Decimal("0"))
    gross_loss = sum((trade.gross_pnl for trade in sample if trade.gross_pnl < 0), Decimal("0"))
    net_positive_outcomes = sum((trade.net_pnl for trade in sample if trade.net_pnl > 0), Decimal("0"))
    net_negative_outcomes = sum((trade.net_pnl for trade in sample if trade.net_pnl < 0), Decimal("0"))
    net = sum((trade.net_pnl for trade in sample), Decimal("0"))
    fees = sum((trade.entry_fee + trade.exit_fee + trade.other_fees for trade in sample), Decimal("0"))
    funding = sum((trade.funding for trade in sample), Decimal("0"))
    period = _period(sample)
    long_metrics = None
    short_metrics = None
    if include_direction_breakdown and closed:
        long_trades = tuple(trade for trade in sample if trade.direction == "LONG")
        short_trades = tuple(trade for trade in sample if trade.direction == "SHORT")
        long_metrics = compute_futures_performance(
            set_id=set_id,
            version=version,
            status=status,
            trades=long_trades,
            max_drawdown=None,
            include_direction_breakdown=False,
            policy=policy,
        )
        short_metrics = compute_futures_performance(
            set_id=set_id,
            version=version,
            status=status,
            trades=short_trades,
            max_drawdown=None,
            include_direction_breakdown=False,
            policy=policy,
        )
    return FuturesPerformanceMetrics(
        set_id=set_id,
        version=version,
        status=status,
        period=period,
        closed_trades=closed,
        wins=wins,
        losses=losses,
        win_rate_pct=None if closed == 0 else Decimal(wins) / Decimal(closed) * Decimal("100"),
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        net_pnl=net,
        average_winner=None if wins == 0 else net_positive_outcomes / Decimal(wins),
        average_loser=None if losses == 0 else net_negative_outcomes / Decimal(losses),
        expectancy_per_trade=None if closed == 0 else net / Decimal(closed),
        profit_factor=_profit_factor(net_positive_outcomes, net_negative_outcomes),
        profit_factor_reason=_profit_factor_reason(net_positive_outcomes, net_negative_outcomes),
        max_drawdown=max_drawdown,
        average_duration_seconds=None
        if closed == 0
        else sum(Decimal(trade.duration_seconds) for trade in sample) / Decimal(closed),
        fees=fees,
        funding=funding,
        fees_as_pct_of_gross_profit=None if gross_profit <= 0 else fees / gross_profit * Decimal("100"),
        long=long_metrics,
        short=short_metrics,
        warnings=_quality_warnings(sample, gross_profit, fees, policy),
        recommendation_observations=_recommendation_observations(sample, gross_profit, fees, long_metrics, short_metrics, policy),
    )


def compare_baseline(
    *,
    baseline_set: str,
    candidate_set: str,
    baseline_trades: tuple[TradePerformanceFact, ...],
    candidate_trades: tuple[TradePerformanceFact, ...],
) -> BaselineComparison:
    baseline_set_id, baseline_version = _split_set_version(baseline_set, label="baseline_set")
    candidate_set_id, candidate_version = _split_set_version(candidate_set, label="candidate_set")
    _validate_trade_membership(baseline_trades, set_id=baseline_set_id, version=baseline_version, label="baseline sample")
    _validate_trade_membership(candidate_trades, set_id=candidate_set_id, version=candidate_version, label="candidate sample")
    if not baseline_trades or not candidate_trades:
        return BaselineComparison(baseline_set, candidate_set, None, False, "baseline or candidate sample unavailable")
    overlap_start = max(min(trade.closed_at for trade in baseline_trades), min(trade.closed_at for trade in candidate_trades))
    overlap_end = min(max(trade.closed_at for trade in baseline_trades), max(trade.closed_at for trade in candidate_trades))
    if overlap_start > overlap_end:
        return BaselineComparison(baseline_set, candidate_set, None, False, "closed-trade periods do not overlap")
    baseline_sample = _between(baseline_trades, overlap_start, overlap_end)
    candidate_sample = _between(candidate_trades, overlap_start, overlap_end)
    if not baseline_sample or not candidate_sample:
        return BaselineComparison(baseline_set, candidate_set, None, False, "no closed trades inside overlap period")
    baseline = compute_futures_performance(
        set_id=baseline_set_id,
        version=baseline_version,
        status="ACTIVE",
        trades=baseline_sample,
        include_direction_breakdown=False,
    )
    candidate = compute_futures_performance(
        set_id=candidate_set_id,
        version=candidate_version,
        status="TESTING",
        trades=candidate_sample,
        include_direction_breakdown=False,
    )
    return BaselineComparison(
        baseline_set=baseline_set,
        candidate_set=candidate_set,
        overlap_period=f"{overlap_start} -> {overlap_end}",
        available=True,
        reason=None,
        baseline_closed_trades=baseline.closed_trades,
        candidate_closed_trades=candidate.closed_trades,
        baseline_net_pnl=baseline.net_pnl,
        candidate_net_pnl=candidate.net_pnl,
        baseline_expectancy=baseline.expectancy_per_trade,
        candidate_expectancy=candidate.expectancy_per_trade,
        baseline_fees=baseline.fees,
        candidate_fees=candidate.fees,
        baseline_direction_mix=_direction_mix(baseline_sample),
        candidate_direction_mix=_direction_mix(candidate_sample),
    )


def group_trade_facts(
    trades: tuple[TradePerformanceFact, ...],
    *,
    dimension: str,
) -> dict[str, tuple[TradePerformanceFact, ...]]:
    groups: dict[str, list[TradePerformanceFact]] = {}
    for trade in trades:
        if dimension == "trigger_set":
            key = f"{trade.trigger_set_id}@{trade.trigger_set_version}"
        elif dimension == "symbol":
            key = trade.symbol
        elif dimension == "direction":
            key = trade.direction
        elif dimension == "regime":
            key = trade.regime_label or "unavailable"
        else:
            raise ValueError("unsupported performance grouping dimension")
        groups.setdefault(key, []).append(trade)
    return {key: tuple(value) for key, value in groups.items()}


def _profit_factor(gross_profit: Decimal, gross_loss: Decimal) -> Decimal | None:
    if gross_loss == 0:
        return None
    return gross_profit / abs(gross_loss)


def _profit_factor_reason(gross_profit: Decimal, gross_loss: Decimal) -> str | None:
    if gross_loss == 0 and gross_profit > 0:
        return "no losing trades; profit factor undefined"
    if gross_loss == 0:
        return "no losing outcomes; profit factor unavailable"
    return None


def _validate_trade_membership(
    trades: tuple[TradePerformanceFact, ...],
    *,
    set_id: str,
    version: str,
    label: str,
) -> None:
    for trade in trades:
        if trade.trigger_set_id != set_id or trade.trigger_set_version != version:
            actual = f"{trade.trigger_set_id}@{trade.trigger_set_version}"
            expected = f"{set_id}@{version}"
            raise ValueError(f"{label} contains trade {trade.trade_id!r} for {actual}, expected {expected}")


def _split_set_version(value: str, *, label: str) -> tuple[str, str]:
    if "@" not in value:
        raise ValueError(f"{label} must be formatted as set_id@version")
    set_id, version = value.rsplit("@", 1)
    if not set_id or not version:
        raise ValueError(f"{label} must include both set_id and version")
    return set_id, version


def _period(trades: tuple[TradePerformanceFact, ...]) -> str:
    if not trades:
        return "unavailable"
    return f"{min(trade.closed_at for trade in trades)} -> {max(trade.closed_at for trade in trades)}"


def _between(trades: tuple[TradePerformanceFact, ...], start: str, end: str) -> tuple[TradePerformanceFact, ...]:
    return tuple(trade for trade in trades if start <= trade.closed_at <= end)


def _direction_mix(trades: tuple[TradePerformanceFact, ...]) -> str:
    total = len(trades)
    if total == 0:
        return "unavailable"
    long = sum(1 for trade in trades if trade.direction == "LONG")
    short = sum(1 for trade in trades if trade.direction == "SHORT")
    return f"LONG {long}/{total}; SHORT {short}/{total}"


def _quality_warnings(
    trades: tuple[TradePerformanceFact, ...],
    gross_profit: Decimal,
    fees: Decimal,
    policy: PerformanceQualityPolicy,
) -> tuple[str, ...]:
    warnings: list[str] = []
    count = len(trades)
    if count == 0:
        return ("empty sample",)
    if count < policy.minimum_closed_trades:
        warnings.append(f"low sample size: {count}/{policy.minimum_closed_trades} closed trades")
    for label, values in {
        "symbol": [trade.symbol for trade in trades],
        "direction": [trade.direction for trade in trades],
    }.items():
        top = _top_concentration_pct(values)
        if top is not None and top > policy.concentration_threshold_pct:
            warnings.append(f"extreme {label} concentration: {top}%")
    regimes = {trade.regime_label for trade in trades if trade.regime_label}
    if not regimes:
        warnings.append("regime diversity unavailable")
    elif len(regimes) == 1:
        warnings.append("insufficient regime diversity")
    if gross_profit > 0:
        fee_drag = fees / gross_profit * Decimal("100")
        if fee_drag > policy.high_fee_drag_pct:
            warnings.append(f"large fee drag: {fee_drag}% of gross profit")
    return tuple(warnings)


def _recommendation_observations(
    trades: tuple[TradePerformanceFact, ...],
    gross_profit: Decimal,
    fees: Decimal,
    long_metrics: FuturesPerformanceMetrics | None,
    short_metrics: FuturesPerformanceMetrics | None,
    policy: PerformanceQualityPolicy,
) -> tuple[str, ...]:
    observations: list[str] = []
    if len(trades) < policy.minimum_closed_trades:
        observations.append("test set lacks sample")
    if gross_profit > 0 and fees / gross_profit * Decimal("100") > policy.high_fee_drag_pct:
        observations.append("fee drag is high")
    if long_metrics and short_metrics and long_metrics.closed_trades and short_metrics.closed_trades:
        if long_metrics.expectancy_per_trade is not None and short_metrics.expectancy_per_trade is not None:
            if short_metrics.expectancy_per_trade < long_metrics.expectancy_per_trade:
                observations.append("SHORT underperforms LONG")
            elif long_metrics.expectancy_per_trade < short_metrics.expectancy_per_trade:
                observations.append("LONG underperforms SHORT")
    return tuple(observations)


def _top_concentration_pct(values: list[str]) -> Decimal | None:
    if not values:
        return None
    top = max(values.count(value) for value in set(values))
    return Decimal(top) / Decimal(len(values)) * Decimal("100")
