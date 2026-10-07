from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from triggertrade.backtest.models import HistoricalCandle
from triggertrade.research_v2 import (
    V2DecisionStatus,
    V2Direction,
    aggregate_completed_bars,
    atr15,
    ceil_to_step,
    compression_breakout_signal,
    confirmed_swing5_references,
    continuation_signal,
    ema15,
    fraction_to_pct_points,
    latest_protective_swing5,
    load_research_v2_jobs,
    pct_points_to_fraction,
    physical_symbol_for_research_v2,
    research_v2_data_requirements,
    ret5_ret15_or_signal,
    ret_or_episode_reset_ready,
    reversal_reset_ready,
    reversal_signal,
    return_pct_points,
    rvol5,
    screening_output_contract_fields,
    turnover_acceleration,
    v2_entry_price,
    v2_risk_based_sizing,
    v2_stop_g0,
    v2_stop_g1,
    v2_take_profit_2r,
)


def test_research_v2_jobs_load_with_deterministic_fingerprints_and_expected_diffs():
    jobs = load_research_v2_jobs()

    assert set(jobs) == {"J0", "J1", "J2", "J3", "J4", "J5", "J6", "J7"}
    assert jobs["J0"].runtime_profile["signal"] == {"family": "LEGACY_SET", "set_version": "SET-R-003-V2"}
    assert jobs["J0"].runtime_profile["entry"]["ttl_minutes"] is None
    assert jobs["J1"].runtime_profile["entry"]["ttl_minutes"] == 15
    assert jobs["J0"].config_fingerprint == load_research_v2_jobs()["J0"].config_fingerprint
    assert jobs["J0"].config_fingerprint != jobs["J1"].config_fingerprint
    assert jobs["J4"].config_fingerprint != jobs["J7"].config_fingerprint

    j4_without_stop = {**jobs["J4"].normalized_config()["runtime_profile"], "stop": None}
    j7_without_stop = {**jobs["J7"].normalized_config()["runtime_profile"], "stop": None}
    assert j4_without_stop == j7_without_stop


def test_research_v2_units_and_pepe_binding_are_explicit():
    assert pct_points_to_fraction(Decimal("0.30")) == Decimal("0.003")
    assert pct_points_to_fraction(Decimal("0.003")) == Decimal("0.00003")
    assert fraction_to_pct_points(Decimal("0.003")) == Decimal("0.300")
    assert physical_symbol_for_research_v2("PEPEUSDT") == "1000PEPEUSDT"
    assert physical_symbol_for_research_v2("AVAXUSDT") == "AVAXUSDT"


def test_common_features_are_causal_and_completed_bar_only():
    start = datetime(2026, 8, 19, tzinfo=UTC)
    candles = _minute_candles(start, 330, price=Decimal("100"), step=Decimal("0.1"), turnover=Decimal("100"))
    cutoff = start + timedelta(minutes=315)

    assert aggregate_completed_bars(candles, timeframe_minutes=15, cutoff=cutoff)[-1].close_time == cutoff
    assert atr15(candles, cutoff=cutoff).status is V2DecisionStatus.AVAILABLE
    assert return_pct_points(candles, cutoff=cutoff, window_minutes=5).value == (
        (Decimal("131.5") / Decimal("131.0")) - Decimal("1")
    ) * Decimal("100")
    assert return_pct_points(candles, cutoff=cutoff, window_minutes=15).value == (
        (Decimal("131.5") / Decimal("130.0")) - Decimal("1")
    ) * Decimal("100")
    assert rvol5(candles, cutoff=cutoff).value == Decimal("1")
    assert turnover_acceleration(candles, cutoff=cutoff).value == Decimal("1")
    assert ema15(candles, cutoff=cutoff, period=20).status is V2DecisionStatus.AVAILABLE
    assert ema15(candles, cutoff=cutoff, period=50).status is V2DecisionStatus.UNAVAILABLE

    incomplete = replace(candles[-1], completed=False)
    assert aggregate_completed_bars((*candles[:-1], incomplete), timeframe_minutes=15, cutoff=start + timedelta(minutes=330))[-1].close_time == cutoff


def test_swing5_confirmation_waits_for_two_right_bars_and_feeds_g0():
    start = datetime(2026, 8, 19, tzinfo=UTC)
    bars = [
        _five_minute_bar(start, 0, high="105", low="100", close="103"),
        _five_minute_bar(start, 1, high="104", low="99", close="102"),
        _five_minute_bar(start, 2, high="103", low="95", close="101"),
        _five_minute_bar(start, 3, high="106", low="99", close="104"),
        _five_minute_bar(start, 4, high="107", low="100", close="105"),
    ]
    candles = tuple(_expand_5m_to_minutes(bar) for bar in bars)
    flat = tuple(item for group in candles for item in group)

    assert confirmed_swing5_references(flat, cutoff=start + timedelta(minutes=20)) == ()
    refs = confirmed_swing5_references(flat, cutoff=start + timedelta(minutes=25))
    assert len(refs) == 1
    assert refs[0].price == Decimal("95")
    assert refs[0].available_at == start + timedelta(minutes=25)

    ref = latest_protective_swing5(flat, cutoff=start + timedelta(minutes=25), direction=V2Direction.LONG, entry_price=Decimal("100"))
    stop = v2_stop_g0(
        direction=V2Direction.LONG,
        entry_price=Decimal("100"),
        atr15_value=Decimal("2"),
        reference=ref,
        observed_at=start + timedelta(minutes=25),
        tick_size=Decimal("0.1"),
    )
    assert stop.status is V2DecisionStatus.REJECT
    assert stop.reason == "STRUCTURAL_STOP_BEYOND_MAX_DISTANCE"


def test_v2_entry_g0_g1_tp_and_sizing_semantics():
    entry_long = v2_entry_price(
        direction=V2Direction.LONG,
        last_traded_price=Decimal("100"),
        atr15_value=Decimal("1.23"),
        tick_size=Decimal("0.1"),
    )
    assert entry_long.price == Decimal("99.8")
    entry_short = v2_entry_price(
        direction=V2Direction.SHORT,
        last_traded_price=Decimal("100"),
        atr15_value=Decimal("1.23"),
        tick_size=Decimal("0.1"),
    )
    assert entry_short.price == Decimal("100.2")

    now = datetime(2026, 8, 19, 12, tzinfo=UTC)
    valid_ref = _swing(V2Direction.LONG, "99.1", now)
    too_close = v2_stop_g0(
        direction=V2Direction.LONG,
        entry_price=Decimal("100"),
        atr15_value=Decimal("1"),
        reference=valid_ref,
        observed_at=now,
        tick_size=Decimal("0.1"),
    )
    assert too_close.status is V2DecisionStatus.PASS
    assert too_close.risk_distance >= Decimal("0.5")

    too_far = v2_stop_g0(
        direction=V2Direction.LONG,
        entry_price=Decimal("100"),
        atr15_value=Decimal("1"),
        reference=_swing(V2Direction.LONG, "97", now),
        observed_at=now,
        tick_size=Decimal("0.1"),
    )
    assert too_far.status is V2DecisionStatus.REJECT
    assert too_far.reason == "STRUCTURAL_STOP_BEYOND_MAX_DISTANCE"

    stale = v2_stop_g0(
        direction=V2Direction.SHORT,
        entry_price=Decimal("100"),
        atr15_value=Decimal("1"),
        reference=_swing(V2Direction.SHORT, "100.9", now - timedelta(minutes=61)),
        observed_at=now,
        tick_size=Decimal("0.1"),
    )
    assert stale.status is V2DecisionStatus.UNAVAILABLE

    g1 = v2_stop_g1(direction=V2Direction.SHORT, entry_price=Decimal("100"), atr15_value=Decimal("2"), tick_size=Decimal("0.1"))
    assert g1.status is V2DecisionStatus.PASS
    assert g1.risk_distance == Decimal("1.2")

    tp = v2_take_profit_2r(
        direction=V2Direction.LONG,
        entry_price=Decimal("100"),
        stop_price=Decimal("99"),
        quantity=Decimal("2"),
        tick_size=Decimal("0.1"),
    )
    assert tp.status is V2DecisionStatus.PASS
    assert tp.gross_r == Decimal("2")

    sizing = v2_risk_based_sizing(
        capital=Decimal("1000"),
        entry_price=Decimal("100"),
        stop_price=Decimal("99"),
        free_margin=Decimal("600"),
        remaining_coin_margin=Decimal("330"),
        remaining_gross_exposure=Decimal("1800"),
        remaining_portfolio_stop_risk=Decimal("15"),
    )
    assert sizing.status is V2DecisionStatus.PASS
    assert sizing.binding_constraint == "nominal_margin"
    assert sizing.margin == Decimal("250.00")

    minimum_fail = v2_risk_based_sizing(
        capital=Decimal("100"),
        entry_price=Decimal("100"),
        stop_price=Decimal("99"),
        free_margin=Decimal("10"),
    )
    assert minimum_fail.status is V2DecisionStatus.REJECT
    assert minimum_fail.reason == "MINIMUM_TRANCHE_NOT_MET"


def test_v2_signal_families():
    assert ret5_ret15_or_signal(return5_pct_points=Decimal("0.30"), return15_pct_points=Decimal("0")).direction is V2Direction.LONG
    assert ret5_ret15_or_signal(return5_pct_points=Decimal("0"), return15_pct_points=Decimal("-0.50")).direction is V2Direction.SHORT
    conflict = ret5_ret15_or_signal(return5_pct_points=Decimal("0.31"), return15_pct_points=Decimal("-0.51"))
    assert conflict.direction is V2Direction.NONE
    assert ret_or_episode_reset_ready([(Decimal("0.29"), Decimal("0.49")), (Decimal("0.01"), Decimal("0.02"))])

    base_long = ret5_ret15_or_signal(return5_pct_points=Decimal("0.31"), return15_pct_points=Decimal("0.60"))
    assert continuation_signal(base=base_long, ema20=Decimal("101"), ema50=Decimal("100"), return15_pct_points=Decimal("0.60"), rvol5_value=Decimal("1.2")).direction is V2Direction.LONG
    assert continuation_signal(base=base_long, ema20=Decimal("99"), ema50=Decimal("100"), return15_pct_points=Decimal("0.60"), rvol5_value=Decimal("1.2")).status is V2DecisionStatus.NONE
    assert continuation_signal(base=base_long, ema20=Decimal("101"), ema50=Decimal("100"), return15_pct_points=Decimal("0.60"), rvol5_value=Decimal("1.19")).reason == "RVOL5_BELOW_1_2"

    compression = compression_breakout_signal(
        atr15_value=Decimal("0.7"),
        preceding_atr15_values=(Decimal("1"),) * 96,
        close=Decimal("105"),
        prior_range_high=Decimal("104"),
        prior_range_low=Decimal("100"),
        rvol5_value=Decimal("1.5"),
        turnover_acceleration_value=Decimal("1.2"),
    )
    assert compression.direction is V2Direction.LONG
    assert compression_breakout_signal(
        atr15_value=Decimal("0.9"),
        preceding_atr15_values=(Decimal("1"),) * 96,
        close=Decimal("105"),
        prior_range_high=Decimal("104"),
        prior_range_low=Decimal("100"),
        rvol5_value=Decimal("1.5"),
        turnover_acceleration_value=Decimal("1.2"),
    ).reason == "COMPRESSION_FILTER_FAILED"

    short_reversal = reversal_signal(
        return15_pct_points=Decimal("1.0"),
        latest_close=Decimal("109"),
        high_15m=Decimal("110"),
        low_15m=Decimal("100"),
        atr15_value=Decimal("1.5"),
        last_two_closes=(Decimal("109.5"), Decimal("109")),
        turnover_acceleration_value=Decimal("1.0"),
    )
    assert short_reversal.direction is V2Direction.SHORT
    assert reversal_reset_ready((Decimal("0.49"), Decimal("-0.49")))


def test_screening_output_contract_and_data_requirements_are_present():
    job = load_research_v2_jobs()["J4"]
    requirements = research_v2_data_requirements(job)
    assert requirements["screen_window"] == {"start_inclusive": "2026-08-19T00:00:00Z", "end_exclusive": "2026-08-26T00:00:00Z"}
    assert requirements["missing_input_behavior"] == "DATA_INVALID"
    assert "historical_funding_facts" in requirements["required_inputs"]
    fields = screening_output_contract_fields()
    for field in (
        "unique_signal_episodes",
        "matched",
        "approved",
        "accepted",
        "filled",
        "closed",
        "censored",
        "funding",
        "account_net",
        "economic_gate_result",
    ):
        assert field in fields


def _minute_candles(
    start: datetime,
    count: int,
    *,
    price: Decimal,
    step: Decimal,
    turnover: Decimal,
) -> tuple[HistoricalCandle, ...]:
    rows = []
    for idx in range(count):
        open_time = start + timedelta(minutes=idx)
        open_price = price + (step * idx)
        close = open_price + step
        rows.append(
            HistoricalCandle(
                symbol="AVAXUSDT",
                category="linear",
                timeframe="1",
                open_time=open_time,
                close_time=open_time + timedelta(minutes=1),
                open=open_price,
                high=close + Decimal("0.1"),
                low=open_price - Decimal("0.1"),
                close=close,
                volume=Decimal("1"),
                turnover=turnover,
            )
        )
    return tuple(rows)


def _five_minute_bar(start: datetime, index: int, *, high: str, low: str, close: str) -> HistoricalCandle:
    open_time = start + timedelta(minutes=5 * index)
    return HistoricalCandle(
        symbol="AVAXUSDT",
        category="linear",
        timeframe="5",
        open_time=open_time,
        close_time=open_time + timedelta(minutes=5),
        open=Decimal(close),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal("1"),
        turnover=Decimal("1"),
    )


def _expand_5m_to_minutes(bar: HistoricalCandle) -> tuple[HistoricalCandle, ...]:
    rows = []
    for idx in range(5):
        open_time = bar.open_time + timedelta(minutes=idx)
        rows.append(
            HistoricalCandle(
                symbol=bar.symbol,
                category=bar.category,
                timeframe="1",
                open_time=open_time,
                close_time=open_time + timedelta(minutes=1),
                open=bar.open,
                high=bar.high if idx == 2 else bar.close,
                low=bar.low if idx == 2 else bar.close,
                close=bar.close,
                volume=Decimal("1"),
                turnover=Decimal("1"),
            )
        )
    return tuple(rows)


def _swing(direction: V2Direction, price: str, when: datetime):
    from triggertrade.research_v2 import SwingReference

    return SwingReference(direction=direction, price=Decimal(price), pivot_time=when, available_at=when, kind="LOW" if direction is V2Direction.LONG else "HIGH")

