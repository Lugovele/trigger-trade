from __future__ import annotations

from fractions import Fraction

import pytest

from triggertrade.numeric_policy import parse_decimal_text
from triggertrade.set_engine import (
    Candle,
    ClassifierInputs,
    Direction,
    IndicatorStatus,
    SignEvidence,
    SwingPoint,
    SwingSequenceState,
    TriggerResult,
    classify_direction,
    directional_efficiency,
    evaluate_f001_price_displacement,
    evaluate_f002_participation,
    normalize_working,
    swing_points,
    swing_sequence_state,
    wilder_atr_seed,
    wilder_atr_update,
    zscore_working,
)
from triggertrade.set_engine.formulas import SetKernelError


def _candle(
    candle_id: str,
    *,
    close: str = "100",
    high: str | None = None,
    low: str | None = None,
    volume: str = "1",
    timeframe: str = "1m",
    symbol: str = "SOLUSDT",
    opened_at: str | None = None,
) -> Candle:
    opened = opened_at or f"2026-09-21T00:{int(candle_id.split('-')[-1]) % 60:02d}:00Z"
    return Candle(
        candle_id=candle_id,
        symbol=symbol,
        timeframe=timeframe,
        opened_at=opened,
        closed_at=opened.replace(":00Z", ":59Z"),
        high=high or close,
        low=low or close,
        close=close,
        volume=volume,
    )


def test_f001_signed_endpoint_displacement_current_state_boundaries_and_invalids():
    equality = evaluate_f001_price_displacement(
        reference=_candle("c-01", close="100"),
        observed=_candle("c-02", close="101"),
        theta_move_pct="1",
        requested_slot="2026-09-21T00:02:00Z",
    )
    below = evaluate_f001_price_displacement(
        reference=_candle("c-03", close="100"),
        observed=_candle("c-04", close="100.999999"),
        theta_move_pct="1",
        requested_slot="2026-09-21T00:04:00Z",
    )
    zero_observed = evaluate_f001_price_displacement(
        reference=_candle("c-05", close="100"),
        observed=_candle("c-06", close="0"),
        theta_move_pct="100",
        requested_slot="2026-09-21T00:06:00Z",
    )
    invalid_threshold = evaluate_f001_price_displacement(
        reference=_candle("c-07", close="100"),
        observed=_candle("c-08", close="101"),
        theta_move_pct="0",
        requested_slot="2026-09-21T00:08:00Z",
    )
    invalid_reference = evaluate_f001_price_displacement(
        reference=_candle("c-09", close="0"),
        observed=_candle("c-10", close="101"),
        theta_move_pct="1",
        requested_slot="2026-09-21T00:10:00Z",
    )
    malformed_geometry = evaluate_f001_price_displacement(
        reference=_candle("c-11", high="99", low="100", close="100"),
        observed=_candle("c-12", close="101"),
        theta_move_pct="1",
        requested_slot="2026-09-21T00:12:00Z",
    )
    duplicate_identity = evaluate_f001_price_displacement(
        reference=_candle("same-13", close="100", opened_at="2026-09-21T00:13:00Z"),
        observed=_candle("same-13", close="101", opened_at="2026-09-21T00:14:00Z"),
        theta_move_pct="1",
        requested_slot="2026-09-21T00:14:00Z",
    )

    assert equality.trigger_result is TriggerResult.TRUE
    assert equality.move_pct_work == "1"
    assert equality.sign_evidence is SignEvidence.UP
    assert below.trigger_result is TriggerResult.FALSE
    assert zero_observed.move_pct_work == "-100"
    assert zero_observed.sign_evidence is SignEvidence.DOWN
    assert zero_observed.trigger_result is TriggerResult.TRUE
    assert invalid_threshold.arithmetic_status is IndicatorStatus.AVAILABLE
    assert invalid_threshold.trigger_result is TriggerResult.UNAVAILABLE
    assert invalid_reference.arithmetic_status is IndicatorStatus.UNAVAILABLE
    assert malformed_geometry.arithmetic_status is IndicatorStatus.UNAVAILABLE
    assert duplicate_identity.arithmetic_status is IndicatorStatus.UNAVAILABLE


def test_f002_relative_participation_uses_own_trigger_population_not_classifier_population():
    history = [_candle(f"h-{i}", volume="1") for i in range(60)]
    equal_boundary = evaluate_f002_participation(
        current=_candle("c-60", volume="2"),
        historical=history,
        evaluation_slot="2026-09-21T01:00:00Z",
    )
    population_changed = evaluate_f002_participation(
        current=_candle("c-61", volume="2"),
        historical=[_candle(f"x-{i}", volume="2") for i in range(60)],
        evaluation_slot="2026-09-21T01:01:00Z",
    )
    rank_54_true = evaluate_f002_participation(
        current=_candle("c-65", volume="2"),
        historical=[
            *[_candle(f"r54-low-{i}", volume="1") for i in range(54)],
            *[_candle(f"r54-high-{i}", volume="3") for i in range(6)],
        ],
        evaluation_slot="2026-09-21T01:05:00Z",
    )
    rank_53_false = evaluate_f002_participation(
        current=_candle("c-66", volume="2"),
        historical=[
            *[_candle(f"r53-low-{i}", volume="1") for i in range(53)],
            *[_candle(f"r53-high-{i}", volume="3") for i in range(7)],
        ],
        evaluation_slot="2026-09-21T01:06:00Z",
    )
    zero_median = evaluate_f002_participation(
        current=_candle("c-62", volume="1"),
        historical=[_candle(f"z-{i}", volume="0") for i in range(60)],
        evaluation_slot="2026-09-21T01:02:00Z",
    )
    duplicate_identity = evaluate_f002_participation(
        current=_candle("dup-0", volume="2"),
        historical=[_candle("dup-0" if i == 0 else f"dup-{i}", volume="1") for i in range(60)],
        evaluation_slot="2026-09-21T01:05:00Z",
    )
    malformed_geometry = evaluate_f002_participation(
        current=_candle("c-64", high="99", low="100", close="100", volume="2"),
        historical=history,
        evaluation_slot="2026-09-21T01:04:00Z",
    )
    nonterminating_rank_percent = evaluate_f002_participation(
        current=_candle("c-63", volume="0.5"),
        historical=[_candle("nt-0", volume="0.5"), *[_candle(f"nt-{i}", volume="1") for i in range(1, 60)]],
        evaluation_slot="2026-09-21T01:03:00Z",
    )

    assert equal_boundary.trigger_result is TriggerResult.TRUE
    assert equal_boundary.median_baseline == "1"
    assert equal_boundary.rank_count == 60
    assert equal_boundary.relative_volume == "2"
    assert equal_boundary.rank_percent == "100"
    assert population_changed.trigger_result is TriggerResult.FALSE
    assert population_changed.relative_volume == "1"
    assert rank_54_true.trigger_result is TriggerResult.TRUE
    assert rank_54_true.rank_count == 54
    assert rank_53_false.trigger_result is TriggerResult.FALSE
    assert rank_53_false.rank_count == 53
    assert zero_median.status is IndicatorStatus.UNAVAILABLE
    assert malformed_geometry.status is IndicatorStatus.UNAVAILABLE
    assert duplicate_identity.status is IndicatorStatus.UNAVAILABLE
    assert nonterminating_rank_percent.status is IndicatorStatus.AVAILABLE
    assert nonterminating_rank_percent.rank_percent == "5/3"


def test_f003_wilder_atr_seed_update_zero_close_and_exports_are_exact():
    seed = wilder_atr_seed(
        seed_candles=[
            _candle(f"seed-{i}", high="101", low="100", close="100", timeframe="15m")
            for i in range(14)
        ],
        predecessor_close="100",
    )
    update = wilder_atr_update(
        prior_atr_work=seed.atr_work or "",
        candle=_candle("update-14", high="102", low="100", close="100", timeframe="15m"),
        previous_close="100",
    )
    zero_close = wilder_atr_update(
        prior_atr_work=seed.atr_work or "",
        candle=_candle("zero-15", high="2", low="0", close="0", timeframe="15m"),
        previous_close="1",
    )
    malformed = wilder_atr_update(
        prior_atr_work=seed.atr_work or "",
        candle=_candle("bad-16", high="99", low="100", close="100", timeframe="15m"),
        previous_close="100",
    )
    wrong_timeframe = wilder_atr_update(
        prior_atr_work=seed.atr_work or "",
        candle=_candle("wrong-17", high="102", low="100", close="100", timeframe="1m"),
        previous_close="100",
    )
    incomplete = wilder_atr_update(
        prior_atr_work=seed.atr_work or "",
        candle=Candle(
            candle_id="incomplete-18",
            symbol="SOLUSDT",
            timeframe="15m",
            opened_at="2026-09-21T00:00:00Z",
            closed_at="2026-09-21T00:15:00Z",
            high="102",
            low="100",
            close="100",
            completed=False,
        ),
        previous_close="100",
    )
    hidden_precision = wilder_atr_update(
        prior_atr_work="1.0000000000000000000000000000000000005",
        candle=_candle("hidden-19", high="102", low="100", close="100", timeframe="15m"),
        previous_close="100",
    )
    mixed_seed = wilder_atr_seed(
        seed_candles=[_candle(f"mixed-{i}", high="101", low="100", close="100", timeframe="15m" if i else "1m") for i in range(14)],
        predecessor_close="100",
    )
    duplicate_seed = wilder_atr_seed(
        seed_candles=[
            _candle(
                "seed-dup" if i in {0, 1} else f"seed-unique-{i}",
                high="101",
                low="100",
                close="100",
                timeframe="15m",
                opened_at=f"2026-09-21T{i:02d}:00:00Z",
            )
            for i in range(14)
        ],
        predecessor_close="100",
    )

    assert seed.status is IndicatorStatus.AVAILABLE
    assert seed.atr_work == "1"
    assert update.atr_work == "1.071428571428571428571428571428571429"
    assert update.atr_wire == "1.071428571428571429"
    assert update.atr_pct_work == "1.071428571428571428571428571428571429"
    assert zero_close.status is IndicatorStatus.AVAILABLE
    assert zero_close.atr_pct_work is None
    assert zero_close.reason_code == "ATR_PCT_CLOSE_ZERO"
    assert malformed.status is IndicatorStatus.UNAVAILABLE
    assert wrong_timeframe.status is IndicatorStatus.UNAVAILABLE
    assert incomplete.status is IndicatorStatus.UNAVAILABLE
    assert hidden_precision.status is IndicatorStatus.UNAVAILABLE
    assert mixed_seed.status is IndicatorStatus.UNAVAILABLE
    assert duplicate_seed.status is IndicatorStatus.UNAVAILABLE


def test_population_sqrt_zscore_and_q36_normalization_are_exact_and_do_not_feed_from_q18():
    z = zscore_working(current="4", population=["1", "2", "3", "4"])
    normalized = normalize_working(current="4", population=["1", "2", "3", "4"])

    assert z is not None
    assert normalized is not None
    assert parse_decimal_text(normalized) <= Fraction(1)
    assert normalize_working(current="1", population=["1", "1", "1"]) is None


def test_swing_points_sequence_state_ties_and_tick_boundaries():
    candles = [
        _candle("s-0", high="10", low="8", close="9", timeframe="15m"),
        _candle("s-1", high="11", low="7", close="9", timeframe="15m"),
        _candle("s-2", high="13", low="6", close="9", timeframe="15m"),
        _candle("s-3", high="13", low="6", close="9", timeframe="15m"),
        _candle("s-4", high="12", low="7", close="9", timeframe="15m"),
        _candle("s-5", high="14", low="7", close="9", timeframe="15m"),
        _candle("s-6", high="15", low="8", close="9", timeframe="15m"),
        _candle("s-7", high="16", low="9", close="10", timeframe="15m"),
        _candle("s-8", high="15", low="10", close="11", timeframe="15m"),
    ]

    highs = swing_points(candles, point_type="HIGH")
    lows = swing_points(candles, point_type="LOW")

    assert highs[0].candle_id == "s-2"
    assert lows[0].candle_id == "s-2"
    assert swing_sequence_state(highs=highs, lows=lows, tick_size="0.01") is SwingSequenceState.UNAVAILABLE
    with pytest.raises(SetKernelError, match="duplicate candle identity"):
        swing_points([candles[0], candles[0], *candles[1:]], point_type="HIGH")
    incomplete_confirmation = list(candles)
    incomplete_confirmation[3] = Candle(
        candle_id="s-3-incomplete",
        symbol="SOLUSDT",
        timeframe="15m",
        opened_at="2026-09-21T00:03:00Z",
        closed_at="2026-09-21T00:18:00Z",
        high="13",
        low="6",
        close="9",
        completed=False,
    )
    with pytest.raises(SetKernelError, match="completed"):
        swing_points(incomplete_confirmation, point_type="HIGH")
    with pytest.raises(SetKernelError):
        swing_sequence_state(
            highs=(
                SwingPoint("HIGH", "h1", "10", "2026-09-21T00:00:00Z"),
                SwingPoint("HIGH", "h2", "11", "2026-09-21T01:00:00Z"),
            ),
            lows=(
                SwingPoint("LOW", "l1", "8", "2026-09-21T00:00:00Z"),
                SwingPoint("LOW", "l2", "9", "2026-09-21T01:00:00Z"),
            ),
            tick_size="0",
        )


def test_f004_f005_classifier_independence_vetoes_and_data_gates():
    base = ClassifierInputs(
        structure_1h=SwingSequenceState.BULLISH,
        structure_15m=SwingSequenceState.BULLISH,
        de_15m="0.70",
        momentum_score="1",
        vnm_5m_z="0",
        relative_score="1",
        relative_return_z="0",
        aggressive_delta_pct="100",
        tod_relative_turnover="2",
        atr_pct_percentile_15m="50",
        btc_structure_1h=SwingSequenceState.BULLISH,
        btc_return_z="2",
    )
    long_result = classify_direction(base)
    local_veto = classify_direction(ClassifierInputs(**{**base.__dict__, "vnm_5m_z": "-2"}))
    opposite_veto_ignored = classify_direction(ClassifierInputs(**{**base.__dict__, "vnm_5m_z": "2"}))
    unavailable_required = classify_direction(ClassifierInputs(**{**base.__dict__, "btc_structure_1h": SwingSequenceState.UNAVAILABLE}))
    volatility_gate = classify_direction(ClassifierInputs(**{**base.__dict__, "atr_pct_percentile_15m": "98"}))
    de_gate = classify_direction(ClassifierInputs(**{**base.__dict__, "de_15m": "0.299999999999999999"}))
    de_boundary = classify_direction(ClassifierInputs(**{**base.__dict__, "de_15m": "0.30"}))
    activity_boundary = classify_direction(ClassifierInputs(**{**base.__dict__, "tod_relative_turnover": "0.70"}))
    activity_precedes_volatility = classify_direction(
        ClassifierInputs(**{**base.__dict__, "tod_relative_turnover": "0.69", "atr_pct_percentile_15m": "98"})
    )
    malformed_required_diagnostic = classify_direction(
        ClassifierInputs(
            structure_1h=SwingSequenceState.BULLISH,
            structure_15m=SwingSequenceState.AMBIGUOUS,
            de_15m="0.70",
            momentum_score="0",
            vnm_5m_z="1/3",
            relative_score="0",
            relative_return_z="0",
            aggressive_delta_pct="0",
            tod_relative_turnover="2",
            atr_pct_percentile_15m="50",
            btc_structure_1h=SwingSequenceState.AMBIGUOUS,
            btc_return_z="0",
        )
    )
    required_data_priority = classify_direction(
        ClassifierInputs(**{**base.__dict__, "btc_structure_1h": SwingSequenceState.UNAVAILABLE, "tod_relative_turnover": "0.1"})
    )
    short_base = ClassifierInputs(
        structure_1h=SwingSequenceState.BEARISH,
        structure_15m=SwingSequenceState.BEARISH,
        de_15m="0.70",
        momentum_score="-1",
        vnm_5m_z="0",
        relative_score="-1",
        relative_return_z="0",
        aggressive_delta_pct="-100",
        tod_relative_turnover="2",
        atr_pct_percentile_15m="50",
        btc_structure_1h=SwingSequenceState.BEARISH,
        btc_return_z="-2",
    )
    short_result = classify_direction(short_base)
    btc_long_veto = classify_direction(ClassifierInputs(**{**base.__dict__, "btc_structure_1h": SwingSequenceState.BEARISH, "btc_return_z": "-2"}))
    relative_short_veto = classify_direction(ClassifierInputs(**{**short_base.__dict__, "relative_return_z": "2"}))
    opposite_relative_veto_ignored = classify_direction(ClassifierInputs(**{**base.__dict__, "relative_return_z": "2"}))

    assert long_result.direction is Direction.LONG
    assert long_result.score_work is not None
    assert local_veto.direction is Direction.NONE
    assert local_veto.veto_reason == "LOCAL_MOMENTUM_VETO"
    assert opposite_veto_ignored.direction is Direction.LONG
    assert unavailable_required.status is IndicatorStatus.UNAVAILABLE
    assert unavailable_required.rejection_stage == "DATA_UNAVAILABLE"
    assert volatility_gate.direction is Direction.NONE
    assert volatility_gate.rejection_stage == "VOLATILITY_GATE"
    assert de_gate.rejection_stage == "DIRECTIONAL_EFFICIENCY_GATE"
    assert de_boundary.direction is Direction.LONG
    assert activity_boundary.direction is Direction.LONG
    assert activity_precedes_volatility.rejection_stage == "ACTIVITY_GATE"
    assert malformed_required_diagnostic.status is IndicatorStatus.UNAVAILABLE
    assert malformed_required_diagnostic.rejection_stage == "DATA_UNAVAILABLE"
    assert required_data_priority.status is IndicatorStatus.UNAVAILABLE
    assert required_data_priority.rejection_stage == "DATA_UNAVAILABLE"
    assert short_result.direction is Direction.SHORT
    assert btc_long_veto.veto_reason == "BTC_CONTRADICTION_VETO"
    assert relative_short_veto.veto_reason == "RELATIVE_CONTRADICTION_VETO"
    assert opposite_relative_veto_ignored.direction is Direction.LONG


def test_directional_efficiency_zero_denominator_and_exact_range():
    assert directional_efficiency(closes=["1"] * 9) == "0"
    assert directional_efficiency(closes=["1", "2", "3", "4", "5", "6", "7", "8", "9"]) == "1"
