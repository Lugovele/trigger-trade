"""Bounded synthetic Phase 9 comparator/shadow conformance; no corpus reads."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
import inspect
import json
from math import log

import pytest

from triggertrade.live_direction_estimator_v1.calendar import (
    D0, FIT_DEFINITIONS, ReadinessEvidence, schedule_prospective,
)
from triggertrade.live_direction_estimator_v1.comparator import (
    COMPARATOR_ID, FEATURE_COUNT, MAX_DEPTH, NODE_FEATURES, SEED_BASE, TREES,
    ComparatorArtifact, _best_split, _grow, fit_comparator, gini_gain,
    leaf_probabilities, min_leaf_rows, pooled_prior, sample_features,
    score_comparator, split_cut,
)
from triggertrade.live_direction_estimator_v1.evaluation_bootstrap import randint_raw
from triggertrade.live_direction_estimator_v1.evaluation_decision import decide_horizon
from triggertrade.live_direction_estimator_v1.features import RawFeatureRow
from triggertrade.live_direction_estimator_v1.manifests import RowMetadata, build_manifest
from triggertrade.live_direction_estimator_v1.model import CLASSES, LAMBDA, Q_ID
from triggertrade.live_direction_estimator_v1.orchestration import IdentityReferences, fit_pipeline, score_bundle
from triggertrade.live_direction_estimator_v1.report_only_status import (
    ReportOnlyStatus, seal_report_only_status,
)
from triggertrade.live_direction_estimator_v1.rolling_shadow import (
    SHADOW_ID, ShadowArtifact, build_shadow_base_manifest, fit_shadow,
    score_shadow, shadow_window, subtract_calendar_months,
)
from triggertrade.live_direction_estimator_v1.source import SYMBOLS

FIVE = timedelta(minutes=5)


def _row(symbol, t, label, *, horizon=60, value=0.0):
    values = [0.1 * (j + 1) + value for j in range(32)]
    sign = CLASSES.index(label) - 1
    values[3 if horizon == 60 else 4] = sign * (0.1 + abs(value))
    values[14] = 0.0
    values[30:32] = (0.0, 1.0)
    values += [float(symbol == s) for s in SYMBOLS[1:]]
    raw = RawFeatureRow(symbol, t, t - timedelta(minutes=1),
                        f"phase9-synthetic:{symbol}:{t.isoformat()}:{value}", tuple(values))
    return RowMetadata(symbol, t, horizon, "AVAILABLE", "VALID", label, raw, sign)


def _population(fit_id="F1", horizon=60, *, two_windows=False):
    fold = FIT_DEFINITIONS[fit_id]
    old_start = D0 + timedelta(days=2)
    recent_start = shadow_window(fit_id).lower_bound + timedelta(days=2)
    def twelve(start, value_base):
        return tuple(_row(symbol, start + (3 * si + ci) * FIVE, CLASSES[ci],
                          horizon=horizon, value=value_base + si * 0.07 + ci * 0.03)
                     for si, symbol in enumerate(SYMBOLS) for ci in range(3))
    base = twelve(old_start, 0.0)
    if two_windows:
        base += twelve(recent_start, 0.18)
    calibration = tuple(_row(symbol, fold.calibration.nominal_start + timedelta(hours=2) + si * FIVE,
                             CLASSES[si % 3], horizon=horizon, value=0.3 + si * 0.04)
                        for si, symbol in enumerate(SYMBOLS))
    score = tuple(_row(symbol, fold.score.nominal_start + timedelta(hours=2) + si * FIVE,
                       CLASSES[si % 3], horizon=horizon, value=0.4 + si * 0.04)
                  for si, symbol in enumerate(SYMBOLS)) if fold.score else ()
    bm = build_manifest(base, horizon_minutes=horizon, fit_id=fit_id, segment_type="BASE")
    cm = build_manifest(calibration, horizon_minutes=horizon, fit_id=fit_id, segment_type="CALIBRATION")
    sm = build_manifest(score, horizon_minutes=horizon, fit_id=fit_id, segment_type="SCORE") if score else None
    assert len(bm.selected) == len(base) and len(cm.selected) == len(calibration)
    identities = IdentityReferences("a" * 64, "SYNTHETIC_CANONICAL", "b" * 64, "SYNTHETIC_FIXTURE")
    primary = fit_pipeline(base_manifest=bm, calibration_manifest=cm,
                           base_rows=base, calibration_rows=calibration, identities=identities)
    return primary, base, calibration, score, bm, cm, sm


def test_fixed_rf_configuration_min_leaf_and_exact_randint_sampling():
    assert (TREES, MAX_DEPTH, NODE_FEATURES, FEATURE_COUNT) == (256, 4, 5, 35)
    assert (min_leaf_rows(1), min_leaf_rows(100), min_leaf_rows(101)) == (1, 1, 2)
    calls = []
    def draw(m):
        calls.append(m)
        return m - 1
    assert sample_features(draw) == (1, 2, 3, 4, 35)
    assert calls == [35, 34, 33, 32, 31]
    assert sample_features(lambda _: 0) == (1, 2, 3, 4, 5)
    assert randint_raw(iter([2**64 - 1, 4]).__next__, 3) == 1


def test_terminal_nodes_consume_no_rng_and_depth_first_children():
    states = tuple(tuple(float(i + j) for j in range(35)) for i in range(4))
    def forbidden(_):
        raise AssertionError("terminal node consumed RNG")
    leaf = _grow(states, (0, 0, 0, 0), tuple(range(4)), 0, "", 1,
                 (0.4, 0.3, 0.3), forbidden)
    assert leaf.terminal and leaf.path == ""
    assert _grow(states, (0, 1, 0, 1), tuple(range(4)), 4, "", 1,
                 (0.4, 0.3, 0.3), forbidden).terminal
    assert _grow(states, (0, 1, 0, 1), (0,), 0, "", 1,
                 (0.4, 0.3, 0.3), forbidden).terminal
    calls = []
    node = _grow(states, (0, 0, 1, 1), tuple(range(4)), 0, "", 1,
                 (0.4, 0.3, 0.3), lambda m: (calls.append(m), 0)[1])
    assert len(calls) == 5 and node.left.path == "L" and node.right.path == "R"


def test_split_thresholds_gain_ties_strict_positive_and_smoothing():
    assert split_cut(0.0, 2.0) == 1.0
    assert split_cut(1.0, float.fromhex("0x1.0000000000001p+0")) == 1.0
    assert split_cut(-1e308, 1e308) == 0.0
    states = ((0.0,) * 35, (1.0,) * 35, (2.0,) * 35)
    labels = (0, 1, 0)
    best = _best_split(states, labels, (0, 1, 2), (1, 2), 1, (2, 1, 0))
    assert best[0] == 1 and best[1] == 0.5  # Feature and cut tie rules.
    assert _best_split(states, (0, 0, 0), (0, 1, 2), (1,), 1, (3, 0, 0)) is None
    assert gini_gain((2, 2, 0), (2, 0, 0), (0, 2, 0)) == 0.5
    prior = pooled_prior((0, 0, 1))
    assert prior == pytest.approx((2.5/4.5, 1.5/4.5, 0.5/4.5))
    assert leaf_probabilities((2, 0, 0), prior) == pytest.approx(
        tuple(((2, 0, 0)[c] + 3 * prior[c]) / 5 for c in range(3)))


def test_comparator_exact_primary_population_preprocessing_own_calibration_determinism():
    primary, base, calibration, score, bm, cm, sm = _population()
    before = primary.manifest.to_json(), primary.preprocessing.to_dict(), primary.calibrator.to_json()
    c1 = fit_comparator(primary=primary, base_manifest=bm, calibration_manifest=cm,
                        base_rows=base, calibration_rows=calibration)
    again = fit_comparator(primary=primary, base_manifest=bm, calibration_manifest=cm,
                           base_rows=base, calibration_rows=calibration)
    assert c1 == again and c1.artifact_sha256 == again.artifact_sha256
    assert (c1.comparator_id, c1.tree_count, c1.maximum_depth,
            c1.node_candidate_features, c1.minimum_leaf_rows) == (COMPARATOR_ID, 256, 4, 5, 1)
    assert (c1.row_sampling, c1.class_weighting, c1.sample_weighting) == ("NONE", "NONE", "NONE")
    assert c1.rng_seed == 20261077 and c1.preprocessing_sha256 == primary.manifest.preprocessing_sha256
    assert c1.calibrator is not primary.calibrator
    assert c1.calibrator.row_count == len(calibration)
    assert c1.calibrator.horizon_minutes == 60
    assert c1.calibrator_sha256 != primary.manifest.calibrator_sha256
    assert c1.base_manifest_sha256 == primary.manifest.base_manifest_sha256
    assert c1.calibration_manifest_sha256 == primary.manifest.calibration_manifest_sha256
    assert all(tree.path == "" and tree.depth == 0 for tree in c1.trees)
    assert all(sum(tree.counts) == len(base) for tree in c1.trees)
    assert ComparatorArtifact.from_json(c1.to_json()) == c1
    primary_scores = score_bundle(primary, scored_manifest=sm, scored_rows=score)
    output = score_comparator(c1, primary=primary, scored_manifest=sm, scored_rows=score,
                              primary_scored_rows=primary_scores)
    assert len(output) == len(sm.selected) == 4
    def independently_route(node, values):
        while node.probabilities is None:
            node = node.left if values[node.feature_index - 1] <= node.cut else node.right
        return node.probabilities
    from triggertrade.live_direction_estimator_v1.preprocessing import transform
    processed = transform(score[0].feature_row, primary.preprocessing).values
    manual_mean = tuple(sum(independently_route(tree, processed)[c] for tree in c1.trees) / 256
                        for c in range(3))
    assert output[0].prediction.raw_probabilities == manual_mean
    assert all(sum(row.prediction.raw_probabilities) == pytest.approx(1.0) for row in output)
    assert all(row.prediction.raw_log_probabilities == tuple(log(p) for p in row.prediction.raw_probabilities)
               for row in output)
    assert score_comparator(ComparatorArtifact.from_json(c1.to_json()), primary=primary,
                            scored_manifest=sm, scored_rows=score,
                            primary_scored_rows=primary_scores) == output
    assert tuple(r.physical_symbol for r in score_comparator(
        c1, primary=primary, scored_manifest=sm, scored_rows=score,
        primary_scored_rows=primary_scores[:2])) == tuple(r.physical_symbol for r in output[:2])
    with pytest.raises(ValueError, match="primary scored record differs"):
        score_comparator(c1, primary=primary, scored_manifest=sm, scored_rows=score,
                         primary_scored_rows=(replace(primary_scores[0], bundle_sha256="bad"),))
    assert before == (primary.manifest.to_json(), primary.preprocessing.to_dict(), primary.calibrator.to_json())
    with pytest.raises(ValueError, match="exact primary fit populations"):
        fit_comparator(primary=primary, base_manifest=sm, calibration_manifest=cm,
                       base_rows=score, calibration_rows=calibration)
    with pytest.raises(ValueError, match="matched primary SCORE"):
        score_comparator(c1, primary=primary, scored_manifest=bm, scored_rows=base,
                         primary_scored_rows=primary_scores)


def test_comparator_seed_resets_per_fit_and_horizon_independence():
    p60, b60, c60, _, bm60, cm60, _ = _population(horizon=60)
    p120, b120, c120, _, bm120, cm120, _ = _population(horizon=120)
    a60 = fit_comparator(primary=p60, base_manifest=bm60, calibration_manifest=cm60,
                         base_rows=b60, calibration_rows=c60)
    a120 = fit_comparator(primary=p120, base_manifest=bm120, calibration_manifest=cm120,
                          base_rows=b120, calibration_rows=c120)
    assert (a60.rng_seed, a120.rng_seed) == (20261077, 20261137)
    assert a60.rng_seed == SEED_BASE + 60 and a120.rng_seed == SEED_BASE + 120
    assert a60.artifact_sha256 != a120.artifact_sha256
    assert fit_comparator(primary=p60, base_manifest=bm60, calibration_manifest=cm60,
                          base_rows=b60, calibration_rows=c60).trees == a60.trees


def test_shadow_calendar_exact_six_calendar_months_and_boundaries():
    expected = {"F1": (2024, 10, 2), "F2": (2024, 12, 1),
                "F3": (2025, 3, 1), "F4": (2025, 6, 1),
                "F5": (2025, 9, 1), "FINAL": (2025, 12, 1)}
    for fit_id, (year, month, day) in expected.items():
        window = shadow_window(fit_id)
        assert window.lower_bound == datetime(year, month, day, tzinfo=UTC)
        assert window.upper_boundary == FIT_DEFINITIONS[fit_id].calibration.nominal_start
    assert shadow_window("F1").warmup_status == "WARMUP_LIMITED"
    assert all(shadow_window(f).warmup_status == "DISTINCT_WINDOW" for f in expected if f != "F1")
    assert subtract_calendar_months(datetime(2025, 8, 31, tzinfo=UTC)) == datetime(2025, 2, 28, tzinfo=UTC)
    c = shadow_window("FINAL").calibration_start
    assert shadow_window("FINAL").lower_bound == datetime(2025, 12, 1, tzinfo=UTC)
    assert c - timedelta(minutes=125) + timedelta(minutes=120) < c
    assert c - timedelta(minutes=120) + timedelta(minutes=120) == c


def test_shadow_manifest_window_excludes_old_includes_lower_without_embargo():
    primary, base, _, _, bm, _, _ = _population("F2", two_windows=True)
    lower = shadow_window("F2").lower_bound
    exact = _row("BTCUSDT", lower, CLASSES[0], value=0.02)
    near_upper = _row("AVAXUSDT", shadow_window("F2").upper_boundary - timedelta(minutes=125),
                      CLASSES[1], value=0.2)
    disallowed = _row("SUIUSDT", shadow_window("F2").upper_boundary - timedelta(minutes=120),
                      CLASSES[2], value=0.2)
    more = base + (exact, near_upper, disallowed)
    whole = build_manifest(more, horizon_minutes=60, fit_id="F2", segment_type="BASE")
    shadow = build_shadow_base_manifest(whole, more)
    assert ShadowArtifact  # make explicit shadow namespace, not primary bundle.
    assert shadow.nominal_lower == "2024-12-01T00:00:00.000000Z"
    assert exact.key in {member.key for member in shadow.selected}
    assert near_upper.key in {member.key for member in shadow.selected}
    assert disallowed.key not in {member.key for member in whole.selected}
    assert all(member.prediction_origin >= shadow.nominal_lower for member in shadow.selected)
    assert len(shadow.selected) == 14 and len(shadow.excluded_by_window) == 12
    assert shadow.manifest_sha256 == build_shadow_base_manifest(whole, more).manifest_sha256


def test_shadow_own_family_preprocessing_calibration_hash_roundtrip_matched_keys():
    primary, base, calibration, score, bm, cm, sm = _population("F2", two_windows=True)
    before = primary.manifest.to_json(), primary.model.to_json(), primary.calibrator.to_json()
    shadow = fit_shadow(primary=primary, primary_base_manifest=bm,
                        calibration_manifest=cm, base_rows=base, calibration_rows=calibration)
    assert shadow.shadow_id == SHADOW_ID and shadow.fit_id == "F2"
    assert len(shadow.shadow_base_manifest.selected) == 12
    assert shadow.preprocessing.membership_sha256 != primary.preprocessing.membership_sha256
    assert shadow.preprocessing_sha256 != primary.manifest.preprocessing_sha256
    assert "SHADOW" in shadow.preprocessing.fit_id
    assert shadow.model.l2_lambda == primary.model.l2_lambda == LAMBDA
    assert shadow.model.q_basis_id == primary.model.q_basis_id == Q_ID
    assert shadow.calibrator.horizon_minutes == primary.calibrator.horizon_minutes == 60
    assert shadow.calibrator.row_count == len(calibration)
    assert ShadowArtifact.from_json(shadow.to_json()) == shadow
    primary_scores = score_bundle(primary, scored_manifest=sm, scored_rows=score)
    scored = score_shadow(shadow, primary=primary, scored_manifest=sm, scored_rows=score,
                          primary_scored_rows=primary_scores)
    assert tuple((r.prediction_origin, r.physical_symbol) for r in scored) == tuple(m.key for m in sm.selected)
    assert score_shadow(ShadowArtifact.from_json(shadow.to_json()), primary=primary,
                        scored_manifest=sm, scored_rows=score,
                        primary_scored_rows=primary_scores) == scored
    assert len(score_shadow(shadow, primary=primary, scored_manifest=sm,
                            scored_rows=score, primary_scored_rows=primary_scores[:1])) == 1
    assert score_shadow(shadow, primary=primary, scored_manifest=sm,
                        scored_rows=score, primary_scored_rows=()) == ()
    assert before == (primary.manifest.to_json(), primary.model.to_json(), primary.calibrator.to_json())
    with pytest.raises(ValueError, match="matched primary SCORE"):
        score_shadow(shadow, primary=primary, scored_manifest=bm, scored_rows=base,
                     primary_scored_rows=primary_scores)


def test_f1_shadow_warmup_has_distinct_role_even_when_membership_equals_primary():
    primary, base, calibration, _, bm, cm, _ = _population("F1")
    shadow = fit_shadow(primary=primary, primary_base_manifest=bm,
                        calibration_manifest=cm, base_rows=base, calibration_rows=calibration)
    assert shadow.shadow_base_manifest.warmup_status == "WARMUP_LIMITED"
    assert len(shadow.shadow_base_manifest.selected) == len(bm.selected)
    assert shadow.preprocessing.membership_sha256 == primary.preprocessing.membership_sha256
    assert shadow.preprocessing.fit_id != primary.preprocessing.fit_id
    assert shadow.artifact_sha256 != primary.manifest.bundle_sha256


def test_final_shadow_uses_december_base_and_june_calibration_without_h1():
    primary, base, calibration, _, bm, cm, _ = _population("FINAL", two_windows=True)
    shadow = fit_shadow(primary=primary, primary_base_manifest=bm,
                        calibration_manifest=cm, base_rows=base, calibration_rows=calibration)
    assert shadow.shadow_base_manifest.nominal_lower == "2025-12-01T00:00:00.000000Z"
    assert shadow.shadow_base_manifest.calibration_start == "2026-06-01T00:00:00.000000Z"
    assert len(shadow.shadow_base_manifest.selected) == 12
    assert all(m.prediction_origin >= shadow.shadow_base_manifest.nominal_lower
               for m in shadow.shadow_base_manifest.selected)
    assert all(m.prediction_origin < "2026-05-31T22:00:00.000000Z"
               for m in shadow.shadow_base_manifest.selected)
    assert cm.nominal_start == "2026-06-01T00:00:00.000000Z"
    assert shadow.calibrator.row_count == 4


def test_shadow_horizons_keep_independent_states_and_artifacts():
    p60, b60, c60, _, bm60, cm60, _ = _population(horizon=60)
    p120, b120, c120, _, bm120, cm120, _ = _population(horizon=120)
    s60 = fit_shadow(primary=p60, primary_base_manifest=bm60,
                     calibration_manifest=cm60, base_rows=b60, calibration_rows=c60)
    s120 = fit_shadow(primary=p120, primary_base_manifest=bm120,
                      calibration_manifest=cm120, base_rows=b120, calibration_rows=c120)
    assert s60.horizon_minutes == 60 and s120.horizon_minutes == 120
    assert s60.preprocessing.fit_id != s120.preprocessing.fit_id
    assert s60.artifact_sha256 != s120.artifact_sha256
    assert s60.calibrator.horizon_minutes != s120.calibrator.horizon_minutes


def test_report_only_status_firewall_and_primary_schedule_independence():
    primary, base, cal, score, bm, cm, sm = _population()
    c1 = fit_comparator(primary=primary, base_manifest=bm, calibration_manifest=cm,
                        base_rows=base, calibration_rows=cal)
    timestamp = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    fitted = seal_report_only_status(role=COMPARATOR_ID, horizon_minutes=60, fit_id="F1",
        status="FITTED", reason="", primary_bundle_sha256=primary.manifest.bundle_sha256,
        artifact_sha256=c1.artifact_sha256, artifact_available_at=timestamp,
        evidence_ref="synthetic:seal")
    failed = seal_report_only_status(role=SHADOW_ID, horizon_minutes=60, fit_id="F1",
        status="FIT_FAILED", reason="synthetic fit failed",
        primary_bundle_sha256=primary.manifest.bundle_sha256)
    unassessed = seal_report_only_status(role=COMPARATOR_ID, horizon_minutes=120, fit_id="F1",
        status="NOT_ASSESSED", reason="not ready at primary seal",
        primary_bundle_sha256="c" * 64)
    assert ReportOnlyStatus.from_json(fitted.to_json()) == fitted
    assert ReportOnlyStatus.from_json(failed.to_json()) == failed
    assert ReportOnlyStatus.from_json(unassessed.to_json()) == unassessed
    assert not any(name in inspect.signature(schedule_prospective).parameters for name in ("comparator", "shadow"))
    assert not any(name in inspect.signature(decide_horizon).parameters for name in ("comparator", "shadow"))
    final = ReadinessEvidence(60, "FINAL_ARTIFACT", timestamp, "synthetic:final", "SYNTHETIC_FIXTURE")
    collector = ReadinessEvidence(60, "COLLECTOR", timestamp, "synthetic:collector", "SYNTHETIC_FIXTURE")
    p0 = schedule_prospective(final, collector).start
    assert schedule_prospective(final, collector).start == p0
    assert failed.status == "FIT_FAILED" and unassessed.status == "NOT_ASSESSED"
    assert primary.manifest.bundle_sha256 == c1.primary_bundle_sha256
    with pytest.raises(ValueError, match="fitted diagnostic"):
        seal_report_only_status(role=COMPARATOR_ID, horizon_minutes=60, fit_id="F1",
            status="FITTED", reason="", primary_bundle_sha256=primary.manifest.bundle_sha256,
            artifact_sha256=c1.artifact_sha256)


def test_report_only_serialization_tamper_rejected():
    primary, base, cal, _, bm, cm, _ = _population()
    c1 = fit_comparator(primary=primary, base_manifest=bm, calibration_manifest=cm,
                        base_rows=base, calibration_rows=cal)
    data = json.loads(c1.to_json())
    data["trees"][0]["counts"][0] += 1
    with pytest.raises(ValueError, match="identity or contract"):
        ComparatorArtifact.from_json(json.dumps(data))
