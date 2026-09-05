from decimal import Decimal

import pytest

from triggertrade.analytics import (
    PerformanceQualityPolicy,
    compare_baseline,
    compute_futures_performance,
    group_trade_facts,
)
from triggertrade.analytics.futures import TradePerformanceFact
from triggertrade.accounting import calculate_drawdown_snapshot, close_futures_trade
from triggertrade.accounting.futures import FuturesFillEvent
from triggertrade.dashboard.__main__ import render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.execution.futures import PositionState
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.persistence.trigger_set_store import TriggerSetStore, bootstrap_current_trigger_sets


def test_core_metrics_win_rate_expectancy_profit_factor_fees_and_direction():
    metrics = compute_futures_performance(
        set_id="set",
        version="v1",
        status="ACTIVE",
        trades=(
            _fact("win-long", net=Decimal("10"), direction="LONG", fees=Decimal("2")),
            _fact("loss-short", net=Decimal("-5"), direction="SHORT", fees=Decimal("1")),
            _fact("flat", net=Decimal("0"), direction="LONG", fees=Decimal("0")),
        ),
        max_drawdown=Decimal("3"),
        policy=PerformanceQualityPolicy(minimum_closed_trades=1),
    )

    assert metrics.closed_trades == 3
    assert metrics.wins == 1
    assert metrics.losses == 1
    assert metrics.win_rate_pct == Decimal("33.33333333333333333333333333")
    assert metrics.gross_profit == Decimal("10")
    assert metrics.gross_loss == Decimal("-5")
    assert metrics.net_pnl == Decimal("5")
    assert metrics.average_winner == Decimal("10")
    assert metrics.average_loser == Decimal("-5")
    assert metrics.expectancy_per_trade == Decimal("1.666666666666666666666666667")
    assert metrics.profit_factor == Decimal("2")
    assert metrics.max_drawdown == Decimal("3")
    assert metrics.average_duration_seconds == Decimal("60")
    assert metrics.fees == Decimal("3")
    assert metrics.funding == Decimal("0")
    assert metrics.fees_as_pct_of_gross_profit == Decimal("30.0")
    assert metrics.long is not None and metrics.long.closed_trades == 2
    assert metrics.short is not None and metrics.short.closed_trades == 1


def test_gross_metrics_use_accounting_gross_pnl_while_outcome_metrics_use_net_pnl():
    metrics = compute_futures_performance(
        set_id="set",
        version="v1",
        status="ACTIVE",
        trades=(
            _fact("win", net=Decimal("8"), gross=Decimal("10"), fees=Decimal("2")),
            _fact("loss", net=Decimal("-3"), gross=Decimal("-1"), fees=Decimal("2")),
        ),
        policy=PerformanceQualityPolicy(minimum_closed_trades=1),
    )

    assert metrics.gross_profit == Decimal("10")
    assert metrics.gross_loss == Decimal("-1")
    assert metrics.average_winner == Decimal("8")
    assert metrics.average_loser == Decimal("-3")
    assert metrics.profit_factor == Decimal("8") / Decimal("3")
    assert metrics.fees_as_pct_of_gross_profit == Decimal("40.0")


def test_performance_rejects_mixed_trigger_set_version_samples():
    with pytest.raises(ValueError, match="performance sample contains trade"):
        compute_futures_performance(
            set_id="set",
            version="v1",
            status="ACTIVE",
            trades=(_fact("wrong-set", set_id="other"),),
        )


def test_zero_denominators_empty_all_wins_and_all_losses():
    empty = compute_futures_performance(set_id="set", version="v1", status="TESTING", trades=())
    all_wins = compute_futures_performance(
        set_id="set",
        version="v1",
        status="TESTING",
        trades=(_fact("w1", net=Decimal("1")), _fact("w2", net=Decimal("2"))),
    )
    all_losses = compute_futures_performance(
        set_id="set",
        version="v1",
        status="TESTING",
        trades=(_fact("l1", net=Decimal("-1")), _fact("l2", net=Decimal("-2"))),
    )

    assert empty.win_rate_pct is None
    assert empty.expectancy_per_trade is None
    assert empty.profit_factor is None
    assert "empty sample" in empty.warnings
    assert all_wins.losses == 0
    assert all_wins.profit_factor is None
    assert all_wins.profit_factor_reason == "no losing trades; profit factor undefined"
    assert all_losses.wins == 0
    assert all_losses.average_winner is None
    assert all_losses.fees_as_pct_of_gross_profit is None


def test_grouping_by_set_symbol_direction_and_regime():
    trades = (
        _fact("a", set_id="set-a", symbol="BTCUSDT", direction="LONG", regime="UPTREND"),
        _fact("b", set_id="set-b", symbol="ETHUSDT", direction="SHORT", regime=None),
    )

    assert set(group_trade_facts(trades, dimension="trigger_set")) == {"set-a@v1", "set-b@v1"}
    assert set(group_trade_facts(trades, dimension="symbol")) == {"BTCUSDT", "ETHUSDT"}
    assert set(group_trade_facts(trades, dimension="direction")) == {"LONG", "SHORT"}
    assert set(group_trade_facts(trades, dimension="regime")) == {"UPTREND", "unavailable"}


def test_baseline_comparison_requires_overlapping_period_and_samples():
    baseline = (_fact("base", set_id="active", closed_at="2026-09-05T00:00:00+00:00", net=Decimal("2")),)
    candidate = (_fact("cand", set_id="test", set_version="v2", closed_at="2026-09-05T00:00:00+00:00", net=Decimal("3")),)
    no_overlap = (_fact("late", set_id="test", set_version="v2", closed_at="2026-09-06T00:00:00+00:00", net=Decimal("3")),)

    comparison = compare_baseline(
        baseline_set="active@v1",
        candidate_set="test@v2",
        baseline_trades=baseline,
        candidate_trades=candidate,
    )
    unavailable = compare_baseline(
        baseline_set="active@v1",
        candidate_set="test@v2",
        baseline_trades=baseline,
        candidate_trades=no_overlap,
    )

    assert comparison.available is True
    assert comparison.baseline_net_pnl == Decimal("2")
    assert comparison.candidate_expectancy == Decimal("3")
    assert comparison.baseline_direction_mix == "LONG 1/1; SHORT 0/1"
    assert unavailable.available is False
    assert unavailable.reason == "closed-trade periods do not overlap"


def test_baseline_comparison_rejects_mismatched_samples():
    with pytest.raises(ValueError, match="candidate sample contains trade"):
        compare_baseline(
            baseline_set="active@v1",
            candidate_set="test@v2",
            baseline_trades=(_fact("base", set_id="active"),),
            candidate_trades=(_fact("cand", set_id="other", set_version="v2"),),
        )


def test_sample_quality_warnings_and_recommendation_observations():
    metrics = compute_futures_performance(
        set_id="set",
        version="v1",
        status="TESTING",
        trades=(
            _fact("a", net=Decimal("1"), direction="LONG", fees=Decimal("1")),
            _fact("b", net=Decimal("1"), direction="LONG", fees=Decimal("1")),
        ),
        policy=PerformanceQualityPolicy(minimum_closed_trades=50, high_fee_drag_pct=Decimal("30")),
    )

    assert any("low sample size" in warning for warning in metrics.warnings)
    assert any("extreme symbol concentration" in warning for warning in metrics.warnings)
    assert any("extreme direction concentration" in warning for warning in metrics.warnings)
    assert "regime diversity unavailable" in metrics.warnings
    assert "fee drag is high" in metrics.recommendation_observations
    assert "test set lacks sample" in metrics.recommendation_observations


def test_readiness_uses_accounting_closed_trades_when_tables_exist(tmp_path):
    db = tmp_path / "readiness.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db))
    accounting = FuturesAccountingStore(db)
    result = close_futures_trade(
        trade_id="candidate-closed",
        entry_fills=(_fill("candidate-entry", trade_id="candidate-closed", set_id="triggertrade-futures-candidate", set_version="v2-test"),),
        exit_fills=(_fill("candidate-exit", trade_id="candidate-closed", action="CLOSE_LONG", price=Decimal("101"), set_id="triggertrade-futures-candidate", set_version="v2-test"),),
    )
    accounting.record_closed_trade(result)

    row = DashboardReadModel(db).list_test_set_evidence()[0]

    assert row.closed_trades_observed == "1"
    assert any("1 / 50 required closed trades" in gap for gap in row.missing_evidence)


def test_dashboard_performance_uses_accounting_metrics_and_no_frontend_math(tmp_path):
    db = tmp_path / "dashboard-performance.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db))
    accounting = FuturesAccountingStore(db)
    result = close_futures_trade(
        trade_id="perf-trade",
        entry_fills=(_fill("perf-entry", trade_id="perf-trade", set_id="triggertrade-futures-core", set_version="v1", fee=Decimal("0.1")),),
        exit_fills=(_fill("perf-exit", trade_id="perf-trade", action="CLOSE_LONG", price=Decimal("110"), set_id="triggertrade-futures-core", set_version="v1", fee=Decimal("0.1")),),
    )
    candidate_result = close_futures_trade(
        trade_id="candidate-perf-trade",
        entry_fills=(_fill("candidate-perf-entry", trade_id="candidate-perf-trade", set_id="triggertrade-futures-candidate", set_version="v2-test", fee=Decimal("0.1")),),
        exit_fills=(_fill("candidate-perf-exit", trade_id="candidate-perf-trade", action="CLOSE_LONG", price=Decimal("105"), set_id="triggertrade-futures-candidate", set_version="v2-test", fee=Decimal("0.1")),),
    )
    accounting.record_closed_trade(result)
    accounting.record_closed_trade(candidate_result)

    rows = DashboardReadModel(db).list_set_performance()
    comparisons = DashboardReadModel(db).list_baseline_comparisons()
    html = render_dashboard(DashboardReadModel(db), initial_page="analytics")

    active = next(row for row in rows if row.set_id == "triggertrade-futures-core")
    assert active.closed_trades == 1
    assert active.net_pnl == "0.8"
    assert active.expectancy == "0.8"
    assert "Win rate" in html
    assert "0.8" in html
    assert comparisons[0].available is True
    assert "Baseline Comparison" in html
    assert "Direction mix C/B" in html
    assert "triggertrade-futures-candidate@v2-test" in html
    assert "no frontend financial calculations" in html
    assert "BYBIT_API_SECRET" not in html


def test_drawdown_snapshots_remain_accounting_backed():
    first = calculate_drawdown_snapshot(
        snapshot_id="one",
        observed_at="2026-09-05T00:00:00+00:00",
        source="exchange",
        wallet_balance=Decimal("100"),
        equity=Decimal("100"),
        available_margin=Decimal("90"),
        used_margin=Decimal("10"),
        unrealized_pnl=Decimal("0"),
        realized_pnl=Decimal("0"),
    )
    second = calculate_drawdown_snapshot(
        snapshot_id="two",
        observed_at="2026-09-05T01:00:00+00:00",
        source="exchange",
        wallet_balance=Decimal("95"),
        equity=Decimal("95"),
        available_margin=Decimal("85"),
        used_margin=Decimal("10"),
        unrealized_pnl=Decimal("-5"),
        realized_pnl=Decimal("0"),
        previous_running_peak=first.running_peak,
        previous_max_drawdown=first.max_drawdown,
    )

    assert second.max_drawdown == Decimal("5")
    assert second.drawdown_percent == Decimal("5.00")


def _fact(
    trade_id: str,
    *,
    set_id: str = "set",
    set_version: str = "v1",
    symbol: str = "BTCUSDT",
    direction: str = "LONG",
    closed_at: str = "2026-09-05T00:00:00+00:00",
    net: Decimal = Decimal("1"),
    gross: Decimal | None = None,
    fees: Decimal = Decimal("0"),
    funding: Decimal = Decimal("0"),
    duration: int = 60,
    regime: str | None = None,
) -> TradePerformanceFact:
    return TradePerformanceFact(
        trade_id=trade_id,
        trigger_set_id=set_id,
        trigger_set_version=set_version,
        symbol=symbol,
        direction=direction,
        closed_at=closed_at,
        net_pnl=net,
        gross_pnl=gross if gross is not None else net,
        entry_fee=fees,
        exit_fee=Decimal("0"),
        other_fees=Decimal("0"),
        funding=funding,
        duration_seconds=duration,
        regime_label=regime,
    )


def _fill(
    event_id: str,
    *,
    trade_id: str,
    action: str = "OPEN_LONG",
    price: Decimal = Decimal("100"),
    fee: Decimal = Decimal("0"),
    set_id: str,
    set_version: str,
) -> FuturesFillEvent:
    return FuturesFillEvent(
        event_id=event_id,
        trade_id=trade_id,
        execution_id=f"exec-{event_id}",
        symbol="BTCUSDT",
        direction=PositionState.LONG,
        action=action,
        quantity=Decimal("0.1"),
        price=price,
        fee=fee,
        fee_asset="USDT",
        occurred_at="2026-09-05T00:00:00+00:00" if action == "OPEN_LONG" else "2026-09-05T00:10:00+00:00",
        trigger_set_id=set_id,
        trigger_set_version=set_version,
    )
