"""Small synthetic conformance fixtures; no corpus, labels, or model."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from math import asinh, isclose, log, sqrt

import pytest

from triggertrade.live_direction_estimator_v1.features import GROUPS, NAMES, _context, _local, _sign, aggregates, build_feature_row, build_feature_rows, compute_features
from triggertrade.live_direction_estimator_v1.preprocessing import EligibleBaseRow, fit_preprocessing, transform
from triggertrade.live_direction_estimator_v1.snapshot import ASOF_VERIFIED, EVENT_TIME_ONLY, SupersessionPolicy, build_snapshot
from triggertrade.live_direction_estimator_v1.source import MINUTE, SourceMinute

T = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
FIRST = T - timedelta(minutes=1446)


def fixture(symbol="BTCUSDT", *, prospective=False):
    rows = []
    for i in range(1445):
        start = FIRST + i * MINUTE
        # Five-minute returns include varying positive, negative and zero steps.
        price = 100.0 + (i // 5) * 0.001 + (i % 13) * 0.0001
        kwargs = (dict(collector_received_at=start + MINUTE, evidence_available_at=(start + MINUTE,),
                       evidence_refs=(f"final:{symbol}:{i}",), collector_receipt_ref=f"receipt:{symbol}:{i}",
                       availability_contract_id="fixture-finalization-v1") if prospective else {})
        rows.append(SourceMinute(symbol, start, start + MINUTE, price, price * 1.001,
                                 price * 0.999, price, f"v{i}", True, **kwargs))
    return tuple(rows)


def four_raw_rows(btc=None):
    btc = btc or fixture()
    return tuple(build_feature_row(symbol, T, btc if symbol == "BTCUSDT" else fixture(symbol) + btc,
                                   mode=EVENT_TIME_ONLY).row
                 for symbol in ("BTCUSDT", "AVAXUSDT", "SUIUSDT", "1000PEPEUSDT"))


def eligible(rows, horizon=60, fit_id="tiny"):
    return tuple(EligibleBaseRow(r, horizon, fit_id, "BASE", True) for r in rows)


def test_cf01_cf05_excluded_minute_and_future_changes():
    rows = fixture()
    base = build_feature_row("BTCUSDT", T, rows, mode=EVENT_TIME_ONLY)
    excluded = SourceMinute("BTCUSDT", T - MINUTE, T, 1, 1, 1, 1, "excluded", True)
    assert build_feature_row("BTCUSDT", T, rows + (excluded,), mode=EVENT_TIME_ONLY) == base
    assert build_feature_row("BTCUSDT", T, rows + (replace(excluded, close=2, high=2),), mode=EVENT_TIME_ONLY) == base
    assert base.row.feature_timestamp == T - MINUTE


def test_cf02_cf03_late_required_minutes_and_exact_cutoff():
    rows = fixture(prospective=True)
    assert build_snapshot("BTCUSDT", T, rows, mode=ASOF_VERIFIED).snapshot is not None
    for index in (0, 1444):
        late = replace(rows[index], collector_received_at=T + MINUTE)
        changed = rows[:index] + (late,) + rows[index + 1:]
        assert build_snapshot("BTCUSDT", T, changed, mode=ASOF_VERIFIED).reasons == ("DATA_LATE",)
    on_cutoff = replace(rows[0], collector_received_at=T, evidence_available_at=(T,))
    assert build_snapshot("BTCUSDT", T, (on_cutoff,) + rows[1:], mode=ASOF_VERIFIED).snapshot


def test_cf04_frozen_snapshot_and_authenticated_supersession():
    rows = fixture(prospective=True)
    frozen = build_snapshot("BTCUSDT", T, rows, mode=ASOF_VERIFIED).snapshot
    revision = replace(rows[0], version_id="revision", close=rows[0].close * 1.0001,
                       collector_received_at=T + MINUTE)
    assert build_snapshot("BTCUSDT", T, rows + (revision,), mode=ASOF_VERIFIED).snapshot == frozen
    assert frozen.local_minutes[0] is rows[0]
    changed_evidence = replace(rows[0], evidence_available_at=(rows[0].interval_end - timedelta(seconds=1),))
    changed = build_snapshot("BTCUSDT", T, (changed_evidence,) + rows[1:], mode=ASOF_VERIFIED).snapshot
    assert changed.source_snapshot_id != frozen.source_snapshot_id
    timely = replace(revision, collector_received_at=T)
    assert "SOURCE_VERSION_CONFLICT" in build_snapshot("BTCUSDT", T, rows + (timely,), mode=ASOF_VERIFIED).reasons
    policy = SupersessionPolicy("provider-v1", {rows[0].version_id: 1, "revision": 2})
    assert build_snapshot("BTCUSDT", T, rows + (timely,), mode=ASOF_VERIFIED, policy=policy).snapshot.local_minutes[0] == timely


def test_cf06_cf07_batch_single_and_registry():
    rows = fixture()
    single = build_feature_row("BTCUSDT", T, rows, mode=EVENT_TIME_ONLY)
    assert build_feature_rows((("BTCUSDT", T),), rows, mode=EVENT_TIME_ONLY) == (single,)
    assert len(NAMES) == len(GROUPS) == len(single.row.values) == 35
    assert NAMES == (
        "mom_1", "mom_3", "mom_6", "mom_12", "mom_24", "mom_48", "abs_mom_12", "abs_mom_48",
        "sign_balance_12", "sign_balance_48", "sign_switch_12", "body_5", "range_5", "close_location_5",
        "zero_range_5", "drawdown_12", "rebound_12", "drawdown_48", "rebound_48", "log_pred_rms48_u",
        "vol_fast", "vol_slow", "rms_dominance_48", "btc_mom_12", "btc_mom_48", "btc_vol_fast",
        "btc_vol_slow", "relative_12", "relative_48", "btc_local_alignment_12", "tod_sin", "tod_cos",
        "is_AVAXUSDT", "is_SUIUSDT", "is_1000PEPEUSDT",
    )
    assert (GROUPS.count("P"), GROUPS.count("S"), GROUPS.count("A"), GROUPS.count("I")) == (21, 1, 7, 6)


def test_cf08_context_dependency_and_btc_exact_zero_after_scaling():
    btc = fixture()
    alt = fixture("AVAXUSDT")
    assert "MISSING_REQUIRED_MINUTE" in build_feature_row("AVAXUSDT", T, alt, mode=EVENT_TIME_ONLY).reasons
    btc_raw = build_feature_row("BTCUSDT", T, btc, mode=EVENT_TIME_ONLY).row
    alt_raw = build_feature_row("AVAXUSDT", T, alt + btc, mode=EVENT_TIME_ONLY).row
    assert alt_raw.values[23:30] != (0.0,) * 7
    state = fit_preprocessing(eligible(four_raw_rows(btc)), horizon_minutes=60, fit_id="tiny")
    assert transform(btc_raw, state).values[23:30] == (0.0,) * 7
    late_btc = replace(btc[0], collector_received_at=T + MINUTE,
                       evidence_available_at=(T,), evidence_refs=("final",),
                       collector_receipt_ref="receipt", availability_contract_id="fixture-finalization-v1")
    alt_pro = fixture("AVAXUSDT", prospective=True)
    btc_pro = fixture(prospective=True)
    assert "DATA_LATE" in build_feature_row("AVAXUSDT", T, alt_pro + (late_btc,) + btc_pro[1:], mode=ASOF_VERIFIED).reasons


def test_cf09_independent_predictor_rms_reference():
    rows = fixture()
    snap = build_snapshot("BTCUSDT", T, rows, mode=EVENT_TIME_ONLY).snapshot
    bars = aggregates(snap.local_minutes)
    closes = [log(bar.close) for bar in bars]
    returns = [closes[k] - closes[k + 1] for k in range(48)]
    independent = sqrt(sum(value * value for value in reversed(returns)) / 48)
    raw = compute_features(snap).row
    assert isclose(raw.values[19], log(independent), rel_tol=0, abs_tol=1e-14)


def test_cf10_exact_support_boundary():
    rows = fixture()
    assert build_snapshot("BTCUSDT", T, rows, mode=EVENT_TIME_ONLY).snapshot
    for index in (0, 578, 1444):
        missing = rows[:index] + rows[index + 1:]
        assert "MISSING_REQUIRED_MINUTE" in build_snapshot("BTCUSDT", T, missing, mode=EVENT_TIME_ONLY).reasons
    prior = SourceMinute("BTCUSDT", FIRST - MINUTE, FIRST, 1, 1, 1, 1, "prior", True)
    original = build_feature_row("BTCUSDT", T, rows, mode=EVENT_TIME_ONLY)
    assert build_feature_row("BTCUSDT", T, rows + (prior,), mode=EVENT_TIME_ONLY) == original
    bars = aggregates(build_snapshot("BTCUSDT", T, rows, mode=EVENT_TIME_ONLY).snapshot.local_minutes)
    assert len(bars) == 289
    assert bars[0].open == rows[-5].open and bars[0].close == rows[-1].close
    assert bars[288].open == rows[0].open and bars[288].close == rows[4].close


def test_cf11_zero_switch_flat_sigma12_and_numerical_log_range():
    assert _sign(0.0) == 0
    rows = fixture()
    snap = build_snapshot("BTCUSDT", T, rows, mode=EVENT_TIME_ONLY).snapshot
    ctx = _context(aggregates(snap.local_minutes))
    altered = dict(ctx)
    altered["r"] = (1.0, 0.0, -1.0) + ctx["r"][3:]
    assert _local(altered)[10] == sum(
        1 for a, b in zip(altered["r"][:11], altered["r"][1:12]) if _sign(a) * _sign(b) < 0
    ) / 11
    # Flat newest five-minute candle with valid older volatility.
    flat = tuple(replace(r, open=100, high=100, low=100, close=100) if i >= 1440 else r for i, r in enumerate(rows))
    flat_result = build_feature_row("BTCUSDT", T, flat, mode=EVENT_TIME_ONLY)
    assert flat_result.row.values[12:15] == (0.0, 0.0, 1.0)
    # Positive raw range can collapse after logarithm for large close prices.
    huge = tuple(replace(r, open=1e300, high=1e300 + 1e284, low=1e300, close=1e300) if i >= 1440 else r for i, r in enumerate(rows))
    assert "NUMERICAL_FEATURE_ERROR" in build_feature_row("BTCUSDT", T, huge, mode=EVENT_TIME_ONLY).reasons
    last_65 = tuple(replace(r, open=101, high=101, low=101, close=101) if i >= 1380 else r for i, r in enumerate(rows))
    assert _context(aggregates(last_65))["s"][12] == 0.0


def test_cf26_parsing_and_source_failures_and_horizon_free_interface():
    row = {"symbol": "BTCUSDT", "open_time": "2026-10-18T11:00:00Z", "close_time": "2026-10-18T11:01:00Z",
           "open": "0.10000000000000001", "high": "0.10000000000000002",
           "low": "0.1", "close": "0.10000000000000001"}
    with pytest.raises(ValueError, match="completion evidence"):
        SourceMinute.from_historical_row(row, version_id="unverified")
    parsed = SourceMinute.from_historical_row(row, version_id="source-row", completion_contract_id="fixture-final-vintage")
    assert parsed.open == float(row["open"])
    assert parsed.source_available_at is None
    last_instant = dict(row, close_time="2026-10-18T11:00:59.999000Z")
    assert SourceMinute.from_historical_row(last_instant, version_id="last-instant",
                                             completion_contract_id="fixture-final-vintage").interval_end == parsed.interval_end
    with pytest.raises(ValueError, match="completed must be"):
        SourceMinute.from_historical_row(dict(row, completed="False"), version_id="invalid-status")
    rows = fixture()
    assert build_feature_row("BTCUSDT", T, rows, mode=EVENT_TIME_ONLY).row
    assert "UNVERIFIED_AVAILABILITY" in build_snapshot("BTCUSDT", T, rows, mode=ASOF_VERIFIED).reasons
    assert "INVALID_REQUIRED_OHLC" in build_snapshot("BTCUSDT", T, (replace(rows[0], low=rows[0].high * 2),) + rows[1:], mode=EVENT_TIME_ONLY).reasons
    assert "INCOMPLETE_FINALIZATION" in build_snapshot("BTCUSDT", T, (replace(rows[0], completed=False),) + rows[1:], mode=EVENT_TIME_ONLY).reasons
    assert "UNSUPPORTED_SYMBOL" in build_snapshot("ETHUSDT", T, (), mode=EVENT_TIME_ONLY).reasons
    assert "INVALID_ORIGIN" in build_snapshot("BTCUSDT", T + MINUTE, (), mode=EVENT_TIME_ONLY).reasons


def test_preprocessing_constants_domains_and_serialization():
    btc, alt, sui, pepe = four_raw_rows()
    later = replace(alt, prediction_origin=T + timedelta(minutes=5), values=tuple(
        value + (0.1 if i == 0 else 0.0) for i, value in enumerate(alt.values)
    ))
    state = fit_preprocessing(eligible((later, alt, btc, sui, pepe), 120, "fixture"), horizon_minutes=120, fit_id="fixture")
    assert state.horizon_minutes == 120
    assert state.to_dict()["registry"] == "LDE_V1_ADJ35_U1M"
    assert state.to_dict()["btc_context_mask_indices"] == (24, 25, 26, 27, 28, 29, 30)
    assert 15 in state.zero_slope_state_indices  # identity constant keeps its raw value
    processed = transform(btc, state)
    assert processed.values[23:30] == (0.0,) * 7
    assert processed.values[14] == btc.values[14]
    departure = replace(btc, values=tuple(v + (1 if i == 1 else 0) for i, v in enumerate(btc.values)))
    assert 2 in transform(departure, state).constant_domain_departures
    with pytest.raises(ValueError, match="base rows"):
        fit_preprocessing((EligibleBaseRow(btc, 120, "fixture", "H1", True),), horizon_minutes=120, fit_id="fixture")
    duplicate_vintage = replace(btc, source_snapshot_id="different-vintage")
    with pytest.raises(ValueError, match="duplicate symbol-origin"):
        fit_preprocessing(eligible((btc, duplicate_vintage, alt, sui, pepe), 120, "fixture"),
                          horizon_minutes=120, fit_id="fixture")
