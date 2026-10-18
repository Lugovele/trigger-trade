"""Small synthetic Phase 8 conformance fixtures; no corpus or real bootstrap."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from math import log

import numpy as np
import pytest

from triggertrade.live_direction_estimator_v1.calendar import FOLDS, H1Governance
from triggertrade.live_direction_estimator_v1.evaluation_bootstrap import (
    PRIMARY_BLOCK, RNG, REPLICATES, SEED, SENSITIVITY_BLOCK, Band,
    BootstrapResult, SimultaneousBands, _bootstrap, conservative_envelope,
    empirical_quantile_95, moving_block_indices, randint_raw, registered_bootstrap,
    simultaneous_bands,
)
from triggertrade.live_direction_estimator_v1.evaluation_coverage import (
    coverage_report, delivered_benefit, prospective_coverage_gates,
)
from triggertrade.live_direction_estimator_v1.evaluation_decision import (
    StageDossier, affirmative_rejection, decide_horizon, positive_gates, stability_gates,
)
from triggertrade.live_direction_estimator_v1.evaluation_metrics import (
    L, N, S, AsOfEvidence, EvaluationRecord, JoinedTruth, ProbabilityState, SealedPrediction,
    average_precision, cell_metrics, exact_auc, fixed_bin, side_values,
)
from triggertrade.live_direction_estimator_v1.evaluation_stage import (
    PhaseGrid, StageEvidence, compute_stage,
)
from triggertrade.live_direction_estimator_v1.model import CLASSES
from triggertrade.live_direction_estimator_v1.source import SYMBOLS

FIVE = timedelta(minutes=5)


def state(p):
    return ProbabilityState.from_probabilities(p)


def row(symbol="BTCUSDT", t=None, phase="F1", truth=L, p=(0.8, 0.1, 0.1),
        b1=(0.4, 0.3, 0.3), b3=(0.35, 0.35, 0.3), *, horizon=60,
        emitted=True, on_time=True):
    t = t or FOLDS[0].score.nominal_start + timedelta(minutes=120)
    prediction = SealedPrediction(t, symbol, horizon, phase, "fixture-seal" if emitted else None,
        state(p) if emitted else None, state(p) if emitted else None, N,
        state(b1), L, state(b3), emitted, None,
        "EVENT_TIME_ONLY" if emitted else None,
        () if emitted else ("MISSING_REQUIRED_MINUTE",))
    return EvaluationRecord(prediction, JoinedTruth(t, symbol, horizon,
        f"canonical:{symbol}:{t.isoformat()}:{horizon}", "SYNTHETIC_CANONICAL",
        "SYNTHETIC_VINTAGE", "VALID", truth))


def test_proper_scores_benefit_brier_components_and_log_retention():
    r = row(p=(0.6, 0.2, 0.2), b1=(0.3, 0.4, 0.3), b3=(0.2, 0.4, 0.4))
    m = cell_metrics([r]).values
    assert m["V1.ll"] == pytest.approx(-log(0.6))
    assert m["V1.bs"] == pytest.approx((0.6-1)**2 + 0.2**2 + 0.2**2)
    assert m[f"V1.bs.{L}"] == pytest.approx(0.16)
    assert m["delta_ll.B1"] > 0 and m["delta_bs.B3"] > 0
    assert m["RAW.ll"] == m["V1.ll"]


def test_exact_auc_ties_and_grouped_stepwise_ap():
    scores = [(0.5, True), (0.5, False), (0.2, True), (0.1, False)]
    assert exact_auc(scores) == pytest.approx(0.625)
    assert average_precision(scores) == pytest.approx(7/12)
    assert exact_auc([(1.0, True)]) is None


def test_truth_join_requires_exact_key_and_retained_canonical_identity():
    r = row()
    assert r.truth.canonical_release_id == "SYNTHETIC_CANONICAL"
    with pytest.raises(ValueError, match="truth key"):
        EvaluationRecord(r.prediction, replace(r.truth, horizon_minutes=120))
    with pytest.raises(ValueError, match="identity"):
        replace(r.truth, outcome_source_vintage_id="")
    assert replace(r, prediction=replace(r.prediction, b2_hard_class=None)).matched is False


def test_unrounded_hard_order_and_prospective_cutoff_evidence():
    # Binary64 probabilities can tie after exponentiation while logits retain order.
    p = ProbabilityState((0.5, 0.5, 0.0),
        (-0.6931471805599453, -0.6931471805599453, -1000.0),
        L, (1.0 + 1e-15, 1.0, 1.0 - 1000.0 + 0.6931471805599453))
    assert p.hard_class == L
    with pytest.raises(ValueError, match="invalid retained"):
        replace(p, hard_class=S)
    with pytest.raises(ValueError, match="ranking logits"):
        replace(p, ranking_scores=(-100.0, -100.0, 1.0), hard_class=N)
    pa, pb = 0.5000000000000002, 0.4999999999999998
    with pytest.raises(ValueError, match="reverse retained"):
        ProbabilityState((pa, pb, 0.0), (log(pa), log(pb), -1000.0),
                         S, (0.0, 1e-15, -1000.0 - log(pa)))
    t = FOLDS[0].score.nominal_start + timedelta(minutes=120)
    evidence = AsOfEvidence("snapshot", "receipt", "final", "clock", "fitted-state",
                             t, t, "synthetic-manifest-hash")
    historical = row(t=t).prediction
    prospective = replace(historical, phase_id="P", on_time=True, record_kind="PROSPECTIVE_FORECAST",
                          provenance_mode="ASOF_VERIFIED", asof_evidence=evidence)
    assert prospective.asof_evidence.admissible_at(t)
    with pytest.raises(ValueError, match="by-T"):
        replace(prospective, asof_evidence=replace(evidence,
                fitted_state_available_at=t+timedelta(microseconds=1)))
    with pytest.raises(ValueError, match="no live deadline"):
        replace(historical, on_time=True)
    synthetic_p = StageEvidence(60, "P", (PhaseGrid("P", (t,),
        (EvaluationRecord(prospective, row(t=t).truth),)),))
    assert coverage_report(synthetic_p).by_symbol["BTCUSDT"]["asof_emitted"] == 0
    assert coverage_report(synthetic_p,
        asof_verifier=lambda sealed: sealed.asof_evidence == evidence).by_symbol["BTCUSDT"]["asof_emitted"] == 1


def test_hard_undefined_zero_side_tie_and_empty_selected_m():
    r = row(truth=L, p=(0.1, 0.1, 0.8))
    m = cell_metrics([r])
    assert m.values[f"V1.precision.{L}"] is None
    assert m.values[f"V1.recall.{L}"] == 0
    assert m.values[f"V1.f1.{L}"] == 0
    assert m.values[f"V1.recall.{S}"] is None
    assert m.selected_direction_count == 0
    assert m.selected_direction_error_benefit is None
    assert m.values["selected_incidence_benefit"] == 0
    tie = state((0.4, 0.4, 0.2))
    assert side_values(tie, L)[2] == L
    severe = ProbabilityState((0.0, 0.0, 1.0), (-1000.0, -1000.0, 0.0), N,
                              (-1000.0, -1000.0, 0.0))
    assert side_values(severe, L)[0] == pytest.approx(log(2))
    assert side_values(severe, L)[2] == L
    huge = ProbabilityState((0.0, 0.0, 1.0), (-1e308, -1e308, 0.0), N,
                            (-1e308, -1e308, 0.0))
    assert side_values(huge, L)[0] == pytest.approx(log(2))
    assert side_values(huge, L)[1] == pytest.approx(0.5)


def test_selected_incidence_uses_all_directional_denominator():
    t = FOLDS[0].score.nominal_start + timedelta(minutes=120)
    a = row(t=t, truth=L, p=(0.8, 0.1, 0.1), b3=(0.1, 0.8, 0.1))
    b = row(t=t+FIVE, truth=S, p=(0.1, 0.1, 0.8), b3=(0.3, 0.6, 0.1))
    m = cell_metrics([a, b])
    assert m.selected_direction_count == 1
    assert m.selected_direction_fraction == 0.5
    assert m.values["selected_incidence_benefit"] == 0.5
    assert m.selected_direction_error_benefit == 1.0


def test_fixed_bins_r_gamma_and_empty_visibility():
    assert fixed_bin(0.1) == 1 and fixed_bin(0.2) == 2
    assert fixed_bin(1.0) == 9
    m = cell_metrics([row(p=(0.8, 0.1, 0.1))])
    assert m.bins[L][8].count == 1
    assert m.bins[L][7].count == 0 and m.bins[L][7].mean_probability is None
    assert m.values["R"] == pytest.approx((0.8-1)**2 + 0.1**2 + 0.1**2)
    assert m.values["gamma.B1"] == pytest.approx(m.values["delta_bs.B1"] - m.values["R"])


def _development(symbol_rows=None):
    phases = []
    for i, fold in enumerate(FOLDS):
        start = fold.score.nominal_start + timedelta(minutes=120)
        positions = tuple(start + j*FIVE for j in range(3))
        records = tuple(row(symbol, t, fold.fit_id, CLASSES[j],
                            p=((0.8, 0.1, 0.1), (0.1, 0.8, 0.1), (0.1, 0.1, 0.8))[j])
                        for symbol in SYMBOLS for j, t in enumerate(positions))
        if symbol_rows and i == 0:
            records += tuple(symbol_rows)
        phases.append(PhaseGrid(fold.fit_id, positions, records))
    return StageEvidence(60, "D", tuple(phases))


def test_equal_symbol_fold_weighting_and_pooled_supplement():
    stage = _development()
    metrics = compute_stage(stage)
    assert metrics.aggregate["V1.ll"] == pytest.approx(
        sum(metrics.by_phase[p.phase_id]["V1.ll"] for p in stage.phases) / 5)
    assert metrics.by_phase["F1"]["V1.ll"] == pytest.approx(
        sum(metrics.cells["F1", s].values["V1.ll"] for s in SYMBOLS) / 4)
    assert metrics.aggregate["V1.macro_auc"] == 1.0
    assert metrics.registered_vector["agg.delta_ll.B1"] > 0
    assert len(metrics.leave_one_out) == 5
    assert len(metrics.registered_vector) == len(set(metrics.registered_vector))
    first = stage.phases[0]
    copied = [r for r in first.records if r.prediction.physical_symbol == "BTCUSDT"]
    with pytest.raises(ValueError, match="record outside"):
        PhaseGrid("F2", first.positions, tuple(copied))
    assert not stage.registered_grid_complete
    assert not replace(stage, contract_mode="REGISTERED").registered_grid_complete


def test_unequal_symbol_and_fold_counts_do_not_change_registered_weights():
    stage = _development()
    phase = stage.phases[0]
    extra_t = phase.positions[-1] + FIVE
    extra = row("BTCUSDT", extra_t, "F1", L, p=(0.2, 0.4, 0.4))
    changed = replace(phase, positions=(*phase.positions, extra_t),
                      records=(*phase.records, extra))
    summary = compute_stage(replace(stage, phases=(changed, *stage.phases[1:])))
    assert summary.cells["F1", "BTCUSDT"].count == 4
    assert all(summary.cells["F1", s].count == 3 for s in SYMBOLS[1:])
    expected_f1 = sum(summary.cells["F1", s].values["V1.ll"] for s in SYMBOLS) / 4
    assert summary.by_phase["F1"]["V1.ll"] == pytest.approx(expected_f1)
    expected_d = sum(summary.by_phase[f"F{i}"]["V1.ll"] for i in range(1, 6)) / 5
    assert summary.aggregate["V1.ll"] == pytest.approx(expected_d)
    assert summary.pooled_rows.values["V1.ll"] != pytest.approx(summary.aggregate["V1.ll"])


def test_delivery_denominator_preserves_missing_primary():
    t = FOLDS[0].score.nominal_start + timedelta(minutes=120)
    available = row(t=t)
    absent = row(t=t+FIVE, emitted=False)
    value, denominator = delivered_benefit((available, absent), baseline="B1")
    assert denominator == 2
    assert value == pytest.approx((log(0.8) - log(0.4)) / 2)


def test_randint_reference_rejection_and_noncircular_blocks():
    raw = iter([(1 << 64)-1, 11]).__next__
    assert randint_raw(raw, 3) == 2  # maximal uint64 rejected, then 11 mod 3.
    assert moving_block_indices(5, 3, lambda m: 2) == (2, 3, 4, 2, 3)
    assert moving_block_indices(2, 3, lambda m: 0) is None
    bitgen = np.random.PCG64(SEED)
    first = bitgen.random_raw()
    assert randint_raw(np.random.PCG64(SEED).random_raw, 7) == first % 7
    assert (PRIMARY_BLOCK, SENSITIVITY_BLOCK, REPLICATES, RNG) == (
        2016, 4032, 10000, "NumPy 2.2.5 PCG64.random_raw")
    assert "replicate_count" not in registered_bootstrap.__code__.co_varnames[:1]


def test_tiny_private_bootstrap_synchronizes_grid_without_compressing_gaps():
    stage = _development()
    result = _bootstrap(stage, lengths=(2, 3), replicate_count=3)
    assert result.horizon_minutes == 60
    assert len(result.replicate_vectors[2]) == 3
    assert result.draw_index_sha256[2] != result.draw_index_sha256[3]
    assert result.envelope["agg.delta_ll.B1"].status == "ESTIMABLE"
    short = _bootstrap(stage, lengths=(4, 5), replicate_count=3)
    assert short.by_block[4].replicate_count == 0
    assert short.envelope["agg.delta_ll.B1"].status == "NOT_ESTIMABLE"
    phase = stage.phases[0]
    with_gap = replace(phase.records[0], prediction=replace(phase.records[0].prediction,
        calibrated=None, raw=None, emitted=False, on_time=None, bundle_sha256=None,
        unavailable_reasons=("MISSING_REQUIRED_MINUTE",)))
    modified = replace(phase, records=(with_gap, *phase.records[1:]))
    assert len(modified.positions) == len(phase.positions)
    assert coverage_report(replace(stage, phases=(modified, *stage.phases[1:]))).expected_keys == 60


def test_simultaneous_quantile_zero_sd_undefined_and_envelope():
    assert empirical_quantile_95(tuple(range(20))) == 18
    observed = {"a": 1.0, "constant": 2.0, "missing": None}
    reps = tuple({"a": 1.0 + i/10, "constant": 2.0, "missing": None} for i in range(20))
    bands = simultaneous_bands(observed, reps)
    assert bands.bands["constant"].lower == bands.bands["constant"].upper == 2.0
    assert bands.bands["missing"].status == "NOT_ESTIMABLE"
    wider = simultaneous_bands(observed, tuple({"a": 1 + i/5, "constant": 2.0, "missing": None}
                                              for i in range(20)))
    envelope = conservative_envelope(bands, wider)
    assert envelope["a"].lower == min(bands.bands["a"].lower, wider.bands["a"].lower)
    assert envelope["a"].upper == max(bands.bands["a"].upper, wider.bands["a"].upper)


def _band(value):
    return Band(value, value, value, 0.0, "ESTIMABLE")


def _dossier(stage="D", positive=True, *, registered=False):
    original = compute_stage(_development())
    metrics = replace(original, stage=stage, registered_grid_complete=True)
    if stage == "P":
        keys = ("P30_1", "P30_2", "P30_3")
        metrics = replace(metrics,
            temporal_units={key: original.by_phase[f"F{i+1}"] for i, key in enumerate(keys)},
            leave_one_out={key: original.aggregate for key in keys})
    elif stage == "H1":
        metrics = replace(metrics, temporal_units={}, leave_one_out={})
    vector = {key: (0.2 if positive else -0.2) for key in original.registered_vector}
    metrics = replace(metrics, registered_vector=vector)
    bands = {key: _band(value) for key, value in vector.items()}
    one = SimultaneousBands(0.0, bands, 10000)
    bootstrap = BootstrapResult(60, stage, vector, {2016: one, 4032: one},
                                conservative_envelope(one, one),
                                {2016: (vector,) * 10000, 4032: (vector,) * 10000},
                                {2016: "a" * 64, 4032: "b" * 64},
                                "REGISTERED" if registered else "SYNTHETIC_FIXTURE")
    return StageDossier(metrics, bootstrap)


def _revalue(dossier, updates):
    vector = {**dossier.metrics.registered_vector, **updates}
    metrics = replace(dossier.metrics, registered_vector=vector)
    bands = {key: _band(value) for key, value in vector.items()}
    one = SimultaneousBands(0.0, bands, 10000)
    bootstrap = replace(dossier.uncertainty, observed=vector,
        by_block={2016: one, 4032: one}, envelope=conservative_envelope(one, one),
        replicate_vectors={2016: (vector,) * 10000, 4032: (vector,) * 10000})
    return StageDossier(metrics, bootstrap)


def test_positive_gate_strict_vs_zero_noninferiority_and_stability():
    bands = {f"agg.{name}": _band(0.1) for name in (
        "delta_ll.B1", "delta_ll.B3", "delta_bs.B1", "delta_bs.B3",
        "delta_macro_auc.B3", *(f"auc_excess.{c}" for c in CLASSES),
        "delta_side_ll.B1", "delta_side_ll.B3", "side_auc_excess", "gamma.B1", "gamma.B3",
        "forced_side_benefit", "selected_incidence_benefit")}
    bands["agg.forced_side_benefit"] = _band(0.0)
    assert all(positive_gates(bands).values())
    bands["agg.delta_ll.B1"] = Band(0.1, 0.0, 0.2, 0.1, "ESTIMABLE")
    assert not positive_gates(bands)["delta_ll.B1"]
    bands["agg.forced_side_benefit"] = Band(0.0, -1e-9, 0.1, 0.1, "ESTIMABLE")
    assert not positive_gates(bands)["forced_side_benefit"]
    assert all(stability_gates(compute_stage(_development())).values())


def test_r1_r2_majority_and_decision_precedence():
    dossier = _dossier(registered=True)
    metrics = dossier.metrics
    negative_period = {**metrics.temporal_units["F1"], "delta_ll.B1": -1.0,
                       "delta_ll.B3": -1.0, "delta_side_ll.B1": -1.0,
                       "delta_side_ll.B3": -1.0, "V1.side_auc": 0.4}
    units = {key: negative_period if i < 3 else value
             for i, (key, value) in enumerate(metrics.temporal_units.items())}
    adverse = replace(metrics, temporal_units=units)
    bands = {**dossier.uncertainty.envelope,
             **{f"agg.{name}": _band(-0.1) for name in (
                 "delta_ll.B1", "delta_ll.B3", "delta_side_ll.B1",
                 "delta_side_ll.B3", "side_auc_excess")}}
    assert affirmative_rejection(adverse, bands, completed=True) == {"R1": True, "R2": True}
    assert affirmative_rejection(adverse, bands, completed=False) == {"R1": False, "R2": False}
    incomplete = {**bands, "agg.delta_ll.B3": _band(0.1)}
    assert not affirmative_rejection(adverse, incomplete, completed=True)["R1"]
    side_only = {**incomplete, "agg.delta_ll.B1": _band(0.1)}
    assert affirmative_rejection(adverse, side_only, completed=True) == {"R1": False, "R2": True}
    adverse_dossier = _revalue(dossier, {name: -0.1 for name in (
        "agg.delta_ll.B1", "agg.delta_ll.B3", "agg.delta_side_ll.B1",
        "agg.delta_side_ll.B3", "agg.side_auc_excess")})
    adverse_dossier = replace(adverse_dossier, metrics=replace(adverse_dossier.metrics,
                                                                temporal_units=units))
    kwargs = dict(horizon_minutes=60, development=adverse_dossier, prospective=None,
                  h1_governance=H1Governance(), h1=None, prospective_coverage=None,
                  prospective_target_sealed=False, ledger_and_artifacts_sealed=False)
    assert decide_horizon(**kwargs).decision == "REJECT"
    assert decide_horizon(**kwargs, integrity_violations=("FABRICATED_RECEIPT",)).decision == "INVALID"
    assert decide_horizon(**{**kwargs, "development": dossier}).decision == "CONTINUE_RESEARCH"


def test_accept_requires_both_stages_coverage_and_clean_h1_handling():
    d, p = _dossier(registered=True), _dossier("P", registered=True)
    assert d.completed_valid_stage and p.completed_valid_stage
    basic = coverage_report(_development())
    by_symbol = {s: {"expected": 100, "emitted": 100, "on_time": 99,
                     "asof_emitted": 100, "emitted_valid_targets": 99,
                     "emitted_target_reason_missing": 0,
                     "window_on_time": [(100, 95)] * 13} for s in SYMBOLS}
    covered = replace(basic, stage="P", registered_grid_complete=True,
                      by_symbol=by_symbol, expected_keys=400, recorded_keys=400)
    kwargs = dict(horizon_minutes=60, development=d, prospective=p,
                  h1_governance=H1Governance(), h1=None, prospective_coverage=covered,
                  prospective_target_sealed=True, ledger_and_artifacts_sealed=True)
    trace = decide_horizon(**kwargs)
    assert trace.decision == "ACCEPT"
    assert all(all(group.values()) for group in trace.positive_gates.values())
    assert all(all(group.values()) for group in trace.stability_gates.values())
    missing_key = "fold.F1.delta_ll.B1"
    missing_vector = {**d.metrics.registered_vector, missing_key: None}
    missing_bands = {**d.uncertainty.by_block[2016].bands,
                     missing_key: Band(None, None, None, None, "NOT_ESTIMABLE")}
    missing_one = SimultaneousBands(0.0, missing_bands, 10000)
    missing_bootstrap = replace(d.uncertainty, observed=missing_vector,
        by_block={2016: missing_one, 4032: missing_one},
        envelope=conservative_envelope(missing_one, missing_one),
        replicate_vectors={2016: (missing_vector,) * 10000,
                           4032: (missing_vector,) * 10000})
    missing_d = StageDossier(replace(d.metrics, registered_vector=missing_vector),
                             missing_bootstrap)
    assert missing_d.completed_valid_stage and not missing_d.required_family_estimable
    assert decide_horizon(**{**kwargs, "development": missing_d}).decision == "CONTINUE_RESEARCH"
    clean = H1Governance(cleanliness_status="ESTIMATOR_RESERVED_CLEAN", audit_evidence_ref="fixture-audit")
    assert decide_horizon(**{**kwargs, "h1_governance": clean}).decision == "CONTINUE_RESEARCH"
    adverse_h1 = _dossier("H1", registered=True)
    adverse_h1 = _revalue(adverse_h1, {"agg.delta_ll.B1": -0.1, "agg.delta_ll.B3": -0.1})
    assert decide_horizon(**{**kwargs, "h1_governance": clean,
                             "h1": adverse_h1}).decision == "CONTINUE_RESEARCH"
    low = {s: {**v, "on_time": 98} for s, v in by_symbol.items()}
    assert decide_horizon(**{**kwargs,
        "prospective_coverage": replace(covered, by_symbol=low)}).decision == "CONTINUE_RESEARCH"
    synthetic_d = _dossier()
    assert not synthetic_d.completed_valid_stage
    assert decide_horizon(**{**kwargs, "development": synthetic_d}).decision == "CONTINUE_RESEARCH"


def test_coverage_windows_and_independent_horizon_rejection():
    # Pure coverage structure: each fixed operational window has its own denominator.
    stage = _development()
    report = coverage_report(stage)
    assert report.expected_keys == 60 and report.matched_scores == 60
    symbol_data = {s: {"expected": 100, "emitted": 100, "on_time": 99,
                       "asof_emitted": 100, "emitted_valid_targets": 99,
                       "emitted_target_reason_missing": 0,
                       "window_on_time": [(100, 95)] * 12 + [(100, 95)]}
                   for s in SYMBOLS}
    prospect = replace(report, stage="P", registered_grid_complete=True,
                       expected_keys=400, recorded_keys=400, by_symbol=symbol_data)
    gates = prospective_coverage_gates(prospect,
        target_sealed=True, required_metrics_evaluable=True, ledger_and_artifacts_sealed=True)
    assert all(gates.values())
    symbol_data[SYMBOLS[0]]["window_on_time"][0] = (100, 94)
    failed = prospective_coverage_gates(prospect,
        target_sealed=True, required_metrics_evaluable=True, ledger_and_artifacts_sealed=True)
    assert not failed["fixed_windows_95_each_symbol"]
    with pytest.raises(ValueError, match="cross-horizon"):
        StageEvidence(120, "D", stage.phases)
