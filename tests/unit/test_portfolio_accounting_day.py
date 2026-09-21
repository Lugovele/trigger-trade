from __future__ import annotations

import pytest

from triggertrade.portfolio_accounting_day import (
    PortfolioGateStatus,
    PortfolioLimitConfiguration,
    PortfolioAccountingDayError,
    RolloverState,
    accounting_day_window,
    establish_day_from_boundary_snapshot,
    establish_day_from_reconstruction,
    evaluate_capacity_gate,
    evaluate_daily_loss_gate,
    latch_daily_loss,
    record_live_metrics,
    apply_final_result_to_day,
)
from triggertrade.portfolio_state import CommitmentBuckets


PORTFOLIO_ID = "portfolio-main"
BOUNDARY = "2026-09-05T21:00:00Z"


def test_at_nr_035_01_verified_boundary_snapshot_establishes_fixed_base_and_boundaries():
    day = establish_day_from_boundary_snapshot(
        portfolio_id=PORTFOLIO_ID,
        boundary_instant=BOUNDARY,
        strategy_wallet_capital_excluding_unrealized_pnl="1080.00",
        evidence_id="wallet-boundary-2026-09-06",
    )

    assert day.accounting_day_id == "2026-09-06"
    assert day.boundary_start_at == "2026-09-05T21:00:00Z"
    assert day.boundary_end_at == "2026-09-06T21:00:00Z"
    assert day.daily_portfolio_base == "1080"
    assert day.rollover_state is RolloverState.PROVEN


def test_at_nr_035_02_and_03_unrealized_excluded_and_realized_cash_not_double_added():
    day = establish_day_from_boundary_snapshot(
        portfolio_id=PORTFOLIO_ID,
        boundary_instant=BOUNDARY,
        strategy_wallet_capital_excluding_unrealized_pnl="1080",
        evidence_id="wallet-boundary-2026-09-06",
        evidence={"previous_day_base": "1000", "prior_day_realized_cash": "80", "unrealized_pnl": "-35"},
    )

    assert day.daily_portfolio_base == "1080"
    assert day.daily_portfolio_base != "1160"
    assert day.base_evidence is not None
    assert day.base_evidence.basis["unrealized_pnl"] == "-35"


def test_at_nr_035_04_and_05_live_equity_and_external_flows_do_not_rebase_day():
    day = establish_day_from_boundary_snapshot(
        portfolio_id=PORTFOLIO_ID,
        boundary_instant=BOUNDARY,
        strategy_wallet_capital_excluding_unrealized_pnl="1080",
        evidence_id="wallet-boundary-2026-09-06",
    )
    updated = record_live_metrics(
        day,
        current_portfolio_equity="1120",
        unrealized_pnl="-35",
        external_capital_flow_amount="500",
    )

    assert updated.daily_portfolio_base == "1080"
    assert updated.current_portfolio_equity == "1120"
    assert updated.unrealized_pnl == "-35"
    assert updated.total_pnl == "-35"
    assert updated.external_capital_flow_amount == "500"


def test_at_nr_035_06_and_08_missing_boundary_proof_reconciles_and_blocks_new_exposure():
    day = establish_day_from_reconstruction(
        portfolio_id=PORTFOLIO_ID,
        boundary_instant=BOUNDARY,
        reconstructed_wallet_capital=None,
        evidence_id="first-post-startup-snapshot",
        complete_authoritative_cashflow_history=False,
        reconstruction_basis={"forbidden_substitute": "later_snapshot"},
    )

    assert day.rollover_state is RolloverState.RECONCILING
    assert day.daily_portfolio_base is None
    assert day.is_exposure_blocked_by_rollover is True
    gate = evaluate_daily_loss_gate(day, enabled=True, daily_loss_limit_pct="2", evaluated_at="2026-09-06T10:00:00Z")
    assert gate.status is PortfolioGateStatus.UNAVAILABLE
    assert gate.blocked is True
    assert gate.reason_code == "ACCOUNTING_DAY_BASE_UNPROVEN"


def test_at_nr_035_07_complete_reconstruction_may_establish_base_with_basis():
    day = establish_day_from_reconstruction(
        portfolio_id=PORTFOLIO_ID,
        boundary_instant=BOUNDARY,
        reconstructed_wallet_capital="1075",
        evidence_id="reconstruction-2026-09-06",
        complete_authoritative_cashflow_history=True,
        reconstruction_basis={"cashflow_history": "complete"},
    )

    assert day.rollover_state is RolloverState.PROVEN
    assert day.daily_portfolio_base == "1075"
    assert day.base_evidence is not None
    assert day.base_evidence.source == "COMPLETE_DETERMINISTIC_RECONSTRUCTION"
    assert day.base_evidence.basis["cashflow_history"] == "complete"


def test_at_nr_035_09_next_rollover_preserves_previous_day_identity_and_base():
    first = establish_day_from_boundary_snapshot(
        portfolio_id=PORTFOLIO_ID,
        boundary_instant=BOUNDARY,
        strategy_wallet_capital_excluding_unrealized_pnl="1080",
        evidence_id="wallet-boundary-2026-09-06",
    )
    second = establish_day_from_boundary_snapshot(
        portfolio_id=PORTFOLIO_ID,
        boundary_instant="2026-09-06T21:00:00Z",
        strategy_wallet_capital_excluding_unrealized_pnl="1110",
        evidence_id="wallet-boundary-2026-09-07",
    )

    assert first.accounting_day_id == "2026-09-06"
    assert first.daily_portfolio_base == "1080"
    assert second.accounting_day_id == "2026-09-07"
    assert second.daily_portfolio_base == "1110"


def test_at_nr_035_10_late_historical_final_posts_to_bound_day_only():
    historical = establish_day_from_boundary_snapshot(
        portfolio_id=PORTFOLIO_ID,
        boundary_instant=BOUNDARY,
        strategy_wallet_capital_excluding_unrealized_pnl="1080",
        evidence_id="wallet-boundary-2026-09-06",
    )
    current = establish_day_from_boundary_snapshot(
        portfolio_id=PORTFOLIO_ID,
        boundary_instant="2026-09-06T21:00:00Z",
        strategy_wallet_capital_excluding_unrealized_pnl="1110",
        evidence_id="wallet-boundary-2026-09-07",
    )

    posted = apply_final_result_to_day(historical, realized_pnl="-25", result_id="final-old", tranche_id="tranche-old")

    assert posted.accounting_day_id == "2026-09-06"
    assert posted.daily_realized_pnl == "-25"
    assert posted.daily_portfolio_base == "1080"
    assert current.daily_realized_pnl == "0"
    assert current.daily_portfolio_base == "1110"


def test_at_nr_035_11_and_12_live_equity_and_unrealized_are_separate_metrics():
    day = establish_day_from_boundary_snapshot(
        portfolio_id=PORTFOLIO_ID,
        boundary_instant=BOUNDARY,
        strategy_wallet_capital_excluding_unrealized_pnl="1080",
        evidence_id="wallet-boundary-2026-09-06",
    )
    realized = apply_final_result_to_day(day, realized_pnl="20", result_id="final-1", tranche_id="tranche-1")
    updated = record_live_metrics(realized, current_portfolio_equity="1065", unrealized_pnl="-35")

    assert updated.current_portfolio_equity == "1065"
    assert updated.daily_realized_pnl == "20"
    assert updated.unrealized_pnl == "-35"
    assert updated.total_pnl == "-15"
    assert updated.daily_portfolio_base == "1080"


def test_at_nr_035_14_accounting_day_uses_asia_jerusalem_half_open_boundaries_and_dst():
    before_next = accounting_day_window("2026-03-28T20:59:59Z")
    exact_next = accounting_day_window("2026-03-28T21:00:00Z")
    summer = accounting_day_window("2026-06-01T21:00:00Z")

    assert before_next.accounting_day_id == "2026-03-28"
    assert exact_next.accounting_day_id == "2026-03-29"
    assert exact_next.boundary_start_at == "2026-03-28T21:00:00Z"
    assert exact_next.boundary_end_at == "2026-03-29T21:00:00Z"
    assert summer.accounting_day_id == "2026-06-02"
    assert summer.boundary_start_at == "2026-06-01T21:00:00Z"
    assert summer.boundary_end_at == "2026-06-02T21:00:00Z"


def test_daily_loss_branch_order_disabled_reconciled_threshold_and_latch():
    day = establish_day_from_boundary_snapshot(
        portfolio_id=PORTFOLIO_ID,
        boundary_instant=BOUNDARY,
        strategy_wallet_capital_excluding_unrealized_pnl="1000",
        evidence_id="wallet-boundary-2026-09-06",
    )
    disabled = evaluate_daily_loss_gate(day, enabled=False, daily_loss_limit_pct=None, evaluated_at="2026-09-06T10:00:00Z")
    ok = evaluate_daily_loss_gate(apply_final_result_to_day(day, realized_pnl="-19.99", result_id="r1", tranche_id="t1"), enabled=True, daily_loss_limit_pct="2", evaluated_at="2026-09-06T10:00:00Z")
    threshold = evaluate_daily_loss_gate(apply_final_result_to_day(day, realized_pnl="-20", result_id="r2", tranche_id="t2"), enabled=True, daily_loss_limit_pct="2", evaluated_at="2026-09-06T10:00:00Z")
    latched_day = latch_daily_loss(day, latched_at="2026-09-06T10:00:00Z")
    latched = evaluate_daily_loss_gate(latched_day, enabled=True, daily_loss_limit_pct="2", evaluated_at="2026-09-06T11:00:00Z")

    assert disabled.blocked is False
    assert ok.blocked is False
    assert threshold.blocked is True
    assert threshold.limit_amount == "20"
    assert latched.blocked is True
    assert latched.latched is True


def test_daily_loss_retained_latch_precedes_unavailable_base_branch():
    reconciling = establish_day_from_reconstruction(
        portfolio_id=PORTFOLIO_ID,
        boundary_instant=BOUNDARY,
        reconstructed_wallet_capital=None,
        evidence_id="missing-boundary",
        complete_authoritative_cashflow_history=False,
    )
    latched = latch_daily_loss(reconciling, latched_at="2026-09-06T10:00:00Z")

    gate = evaluate_daily_loss_gate(latched, enabled=True, daily_loss_limit_pct="2", evaluated_at="2026-09-06T11:00:00Z")

    assert gate.status is PortfolioGateStatus.BLOCKED
    assert gate.reason_code == "DAILY_LOSS_LIMIT_REACHED"
    assert gate.latched is True


def test_at_nr_036_configuration_sum_above_global_cap_is_valid_and_caps_remain_independent():
    config = PortfolioLimitConfiguration(
        max_capital_in_positions_pct="60",
        coin_allocation_pct={"SOLUSDT": "20", "ETHUSDT": "20", "DOGEUSDT": "20", "BTCUSDT": "20"},
        max_open_positions=4,
        max_positions_per_coin=2,
    )

    assert config.global_capital_cap("1000") == "600"
    assert sum(int(config.coin_capital_cap(symbol=symbol, daily_portfolio_base="1000")) for symbol in config.coin_allocation_pct) == 800


def test_at_nr_036_runtime_capacity_rejects_global_or_coin_excess_and_allows_exact_boundary():
    config = PortfolioLimitConfiguration(
        max_capital_in_positions_pct="60",
        coin_allocation_pct={"SOLUSDT": "20", "ETHUSDT": "20", "DOGEUSDT": "20", "BTCUSDT": "20"},
        max_open_positions=4,
        max_positions_per_coin=2,
    )

    global_excess = evaluate_capacity_gate(
        config=config,
        symbol="SOLUSDT",
        daily_portfolio_base="1000",
        global_buckets=CommitmentBuckets(held_committed_capital="590", committed_tranches=1),
        coin_buckets=CommitmentBuckets(held_committed_capital="150", committed_tranches=1),
        requested_committed_capital="20",
    )
    coin_excess = evaluate_capacity_gate(
        config=config,
        symbol="SOLUSDT",
        daily_portfolio_base="1000",
        global_buckets=CommitmentBuckets(held_committed_capital="500", committed_tranches=1),
        coin_buckets=CommitmentBuckets(held_committed_capital="190", committed_tranches=1),
        requested_committed_capital="20",
    )
    exact_boundary = evaluate_capacity_gate(
        config=config,
        symbol="SOLUSDT",
        daily_portfolio_base="1000",
        global_buckets=CommitmentBuckets(held_committed_capital="580", committed_tranches=1),
        coin_buckets=CommitmentBuckets(held_committed_capital="150", committed_tranches=1),
        requested_committed_capital="20",
    )

    assert global_excess.status is PortfolioGateStatus.BLOCKED
    assert global_excess.reason_code == "GLOBAL_CAPACITY_EXCEEDED"
    assert coin_excess.status is PortfolioGateStatus.BLOCKED
    assert coin_excess.reason_code == "COIN_CAPACITY_EXCEEDED"
    assert exact_boundary.status is PortfolioGateStatus.PASS
    assert exact_boundary.remaining_global_capital == "20"
    assert exact_boundary.remaining_coin_capital == "50"


def test_numeric_policy_rejects_exponent_decimal_text_and_negative_requested_capacity():
    with pytest.raises(PortfolioAccountingDayError, match="daily_portfolio_base"):
        establish_day_from_boundary_snapshot(
            portfolio_id=PORTFOLIO_ID,
            boundary_instant=BOUNDARY,
            strategy_wallet_capital_excluding_unrealized_pnl="1E+3",
            evidence_id="wallet-boundary-2026-09-06",
        )
    config = PortfolioLimitConfiguration(
        max_capital_in_positions_pct="60",
        coin_allocation_pct={"SOLUSDT": "20"},
        max_open_positions=4,
        max_positions_per_coin=2,
    )
    with pytest.raises(PortfolioAccountingDayError, match="requested_committed_capital"):
        evaluate_capacity_gate(
            config=config,
            symbol="SOLUSDT",
            daily_portfolio_base="1000",
            global_buckets=CommitmentBuckets(),
            coin_buckets=CommitmentBuckets(),
            requested_committed_capital="-1",
        )


def test_capacity_arithmetic_uses_exact_rational_math_without_decimal_context_rounding():
    base = "999999999999999999999999999999.999999999999"
    config = PortfolioLimitConfiguration(
        max_capital_in_positions_pct="33.333333333333333333",
        coin_allocation_pct={"SOLUSDT": "33.333333333333333333"},
        max_open_positions=4,
        max_positions_per_coin=2,
    )

    assert config.global_capital_cap(base) == "333333333333333333329999999999.99999999999966666666666666666667"
