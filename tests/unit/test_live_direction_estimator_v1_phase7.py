"""Tiny in-memory Phase 7 contract fixtures; no corpus, folds, or H1 accessed."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json

import pytest

from triggertrade.live_direction_estimator_v1.calendar import (
    D0, FINAL, FOLDS, H1Governance, Horizon, ReadinessEvidence, ceil_5m,
    schedule_prospective,
)
from triggertrade.live_direction_estimator_v1.experiment_ledger import (
    ExperimentLedger, LedgerIntegrityError,
)
from triggertrade.live_direction_estimator_v1.features import RawFeatureRow
from triggertrade.live_direction_estimator_v1.manifests import (
    RowManifest, RowMetadata, build_manifest, feature_row_identity,
)
from triggertrade.live_direction_estimator_v1.model import CLASSES
from triggertrade.live_direction_estimator_v1.orchestration import (
    FitBundleManifest, IdentityReferences, fit_pipeline, score_bundle,
)
from triggertrade.live_direction_estimator_v1.source import SYMBOLS

FIVE = timedelta(minutes=5)
TWO_HOURS = timedelta(minutes=120)


def fixture(symbol: str, t: datetime, *, horizon: int = 60, label: str = CLASSES[0],
            sign: int = 1, value: float = 0.0, feature_status: str = "AVAILABLE",
            target_status: str = "VALID") -> RowMetadata:
    values = [0.1 * (j + 1) + value for j in range(32)]
    values[3 if horizon == 60 else 4] = sign * (0.1 + abs(value))
    values[14] = 0.0  # binary zero-range state
    values[30:32] = (0.0, 1.0)  # identity TOD coordinates in this fixture
    values += [float(symbol == s) for s in SYMBOLS[1:]]
    raw = RawFeatureRow(symbol, t, t - timedelta(minutes=1),
                        f"synthetic:{symbol}:{t.isoformat()}:{value}", tuple(values))
    return RowMetadata(symbol, t, horizon, feature_status, target_status,
                       label if target_status == "VALID" else None,
                       raw if feature_status == "AVAILABLE" else None, sign,
                       ("MISSING_REQUIRED_MINUTE",) if feature_status != "AVAILABLE" else ())


def synthetic_populations(horizon=60):
    c = FOLDS[0].calibration.nominal_start
    v = FOLDS[0].score.nominal_start
    base = tuple(fixture(s, D0 + timedelta(days=2) + (3*si + ci)*FIVE,
                         horizon=horizon, label=CLASSES[ci], sign=ci - 1,
                         value=si * 0.07 + ci * 0.03)
                 for si, s in enumerate(SYMBOLS) for ci in range(3))
    cal = tuple(fixture(s, c + TWO_HOURS + si*FIVE, horizon=horizon,
                        label=CLASSES[si % 3], sign=si % 3 - 1, value=0.11 + si*0.04)
                for si, s in enumerate(SYMBOLS))
    score = tuple(fixture(s, v + TWO_HOURS + si*FIVE, horizon=horizon,
                          label=CLASSES[si % 3], sign=si % 3 - 1, value=0.14 + si*0.04)
                  for si, s in enumerate(SYMBOLS))
    return base, cal, score


def manifests(horizon=60):
    base, cal, score = synthetic_populations(horizon)
    return (base, cal, score,
            build_manifest(base, horizon_minutes=horizon, fit_id="F1", segment_type="BASE"),
            build_manifest(cal, horizon_minutes=horizon, fit_id="F1", segment_type="CALIBRATION"),
            build_manifest(score, horizon_minutes=horizon, fit_id="F1", segment_type="SCORE"))


def identities():
    return IdentityReferences("a" * 64, "SYNTHETIC_CANONICAL_RELEASE", "b" * 64,
                              "SYNTHETIC_FIXTURE")


def test_five_fold_calendar_and_exact_purge_embargo():
    expected = ((2025, 3, 1, 2025, 4, 1, 2025, 7, 1),
                (2025, 6, 1, 2025, 7, 1, 2025, 10, 1),
                (2025, 9, 1, 2025, 10, 1, 2026, 1, 1),
                (2025, 12, 1, 2026, 1, 1, 2026, 4, 1),
                (2026, 3, 1, 2026, 4, 1, 2026, 7, 1))
    assert all(f.fit_id == f"F{i}" and f.base.nominal_start == D0 for i, f in enumerate(FOLDS, 1))
    for f, (cy, cm, cd, vy, vm, vd, ey, em, ed) in zip(FOLDS, expected):
        assert f.calibration.nominal_start == datetime(cy, cm, cd, tzinfo=UTC)
        assert f.score.nominal_start == datetime(vy, vm, vd, tzinfo=UTC)
        assert f.score.nominal_end == datetime(ey, em, ed, tzinfo=UTC)
        for left, right in ((f.base, f.calibration), (f.calibration, f.score)):
            boundary = left.nominal_end
            assert left.contains(boundary - timedelta(minutes=125))
            assert not left.contains(boundary - TWO_HOURS)
            assert not right.contains(boundary + timedelta(minutes=115))
            assert right.contains(boundary + TWO_HOURS)
            assert right.contains(boundary + timedelta(hours=3))  # No 24h embargo.
        assert f.score.contains(f.score.nominal_end - timedelta(minutes=125))
        assert not f.score.contains(f.score.nominal_end - TWO_HOURS)
    assert FINAL.score is None


def test_manifest_order_hash_accounting_and_horizon_independence():
    base, _, _, m60, _, _ = manifests(60)
    shuffled = base[::-1]
    assert build_manifest(shuffled, horizon_minutes=60, fit_id="F1", segment_type="BASE") == m60
    assert [member.physical_symbol for member in m60.selected[:3]] == ["BTCUSDT"] * 3
    assert m60.counts_by_symbol == (3, 3, 3, 3)
    assert m60.counts_by_class == (4, 4, 4)
    assert RowManifest.from_json(m60.to_json()) == m60
    changed = list(base)
    changed[0] = replace(changed[0], feature_status="UNAVAILABLE", feature_row=None,
                         feature_reasons=("MISSING_REQUIRED_MINUTE",))
    changed_manifest = build_manifest(changed, horizon_minutes=60, fit_id="F1", segment_type="BASE")
    assert changed_manifest.manifest_sha256 != m60.manifest_sha256
    assert changed_manifest.exclusions_by_reason == (("FEATURE_UNAVAILABLE", 1), ("MISSING_REQUIRED_MINUTE", 1))
    e120 = tuple(fixture(row.physical_symbol, row.prediction_origin, horizon=120,
                         label=row.canonical_class, sign=row.trailing_h_sign,
                         value=row.feature_row.values[0] - 0.1) for row in base)
    m120 = build_manifest(e120, horizon_minutes=120, fit_id="F1", segment_type="BASE")
    assert m120.manifest_sha256 != m60.manifest_sha256
    assert build_manifest(base, horizon_minutes=60, fit_id="F1", segment_type="BASE") == m60
    with pytest.raises(ValueError, match="trailing-H sign disagrees"):
        replace(base[0], trailing_h_sign=1 if base[0].trailing_h_sign != 1 else -1)
    e120_invalid = tuple(replace(row, target_status="UNAVAILABLE", canonical_class=None) if i == 0 else row
                         for i, row in enumerate(e120))
    assert build_manifest(e120_invalid, horizon_minutes=120, fit_id="F1", segment_type="BASE") != m120
    assert build_manifest(base, horizon_minutes=60, fit_id="F1", segment_type="BASE") == m60


def test_bounded_pipeline_seal_no_score_refit_and_identity_firewall():
    base, cal, score, bm, cm, sm = manifests()
    bundle = fit_pipeline(base_manifest=bm, calibration_manifest=cm, base_rows=base,
                          calibration_rows=cal, identities=identities())
    assert bundle.model.preprocessing_membership_sha256 == bundle.preprocessing.membership_sha256
    assert bundle.model.counts_by_symbol_class == bundle.baselines.counts_by_symbol_class
    assert bundle.manifest.base_manifest_sha256 == bm.manifest_sha256
    assert FitBundleManifest.from_json(bundle.manifest.to_json()) == bundle.manifest
    assert bundle.manifest.b0_sha256 != bundle.manifest.b1_sha256
    before = bundle.manifest.to_json(), bundle.model.to_json(), bundle.calibrator.to_json()
    output = score_bundle(bundle, scored_manifest=sm, scored_rows=score)
    assert len(output) == 4 and all(row.bundle_sha256 == bundle.manifest.bundle_sha256 for row in output)
    assert score_bundle(bundle, scored_manifest=sm, scored_rows=score) == output
    assert before == (bundle.manifest.to_json(), bundle.model.to_json(), bundle.calibrator.to_json())
    altered = list(base)
    altered[0] = replace(altered[0], feature_row=replace(altered[0].feature_row,
                                 source_snapshot_id="changed-snapshot"))
    with pytest.raises(ValueError, match="differ from sealed"):
        fit_pipeline(base_manifest=bm, calibration_manifest=cm, base_rows=altered,
                     calibration_rows=cal, identities=identities())
    with pytest.raises(ValueError, match="SCORE manifest"):
        score_bundle(bundle, scored_manifest=bm, scored_rows=base)
    changed_cal = list(cal)
    changed_cal[0] = replace(changed_cal[0], feature_row=replace(changed_cal[0].feature_row,
                                 source_snapshot_id="changed-calibration-snapshot"))
    cm2 = build_manifest(changed_cal, horizon_minutes=60, fit_id="F1", segment_type="CALIBRATION")
    new_bundle = fit_pipeline(base_manifest=bm, calibration_manifest=cm2, base_rows=base,
                              calibration_rows=changed_cal, identities=identities())
    assert new_bundle.manifest.artifact_id != bundle.manifest.artifact_id
    assert new_bundle.preprocessing.fit_id != bundle.preprocessing.fit_id


def test_e60_e120_fit_artifacts_are_independent():
    b60, c60, _, bm60, cm60, _ = manifests(60)
    b120, c120, _, bm120, cm120, _ = manifests(120)
    a60 = fit_pipeline(base_manifest=bm60, calibration_manifest=cm60, base_rows=b60,
                       calibration_rows=c60, identities=identities())
    a120 = fit_pipeline(base_manifest=bm120, calibration_manifest=cm120, base_rows=b120,
                        calibration_rows=c120, identities=identities())
    assert a60.manifest.artifact_id != a120.manifest.artifact_id
    assert a60.manifest.bundle_sha256 != a120.manifest.bundle_sha256
    assert a60.preprocessing.horizon_minutes == a60.model.horizon_minutes == a60.calibrator.horizon_minutes == 60
    assert a120.preprocessing.horizon_minutes == a120.model.horizon_minutes == a120.calibrator.horizon_minutes == 120
    assert a60.baselines.horizon_minutes == 60 and a120.baselines.horizon_minutes == 120


def test_final_artifact_calendar_and_h1_firewall():
    june = FINAL.calibration.nominal_start
    july = FINAL.calibration.nominal_end
    candidates = (fixture("BTCUSDT", june - timedelta(minutes=125)),
                  fixture("AVAXUSDT", june - TWO_HOURS),
                  fixture("SUIUSDT", june + TWO_HOURS))
    base = build_manifest(candidates, horizon_minutes=60, fit_id="FINAL", segment_type="BASE")
    cal = build_manifest(candidates, horizon_minutes=60, fit_id="FINAL", segment_type="CALIBRATION")
    assert [member.physical_symbol for member in base.selected] == ["BTCUSDT"]
    assert [member.physical_symbol for member in cal.selected] == ["SUIUSDT"]
    assert all(member.prediction_origin < "2026-07" for member in (*base.selected, *cal.selected))
    h1 = H1Governance()
    assert h1.cleanliness_status == "CLEANLINESS_UNVERIFIED"
    assert h1.declared_source_end == datetime(2026, 9, 30, tzinfo=UTC)
    with pytest.raises(ValueError, match="audit evidence"):
        H1Governance(cleanliness_status="ESTIMATOR_RESERVED_CLEAN")
    with pytest.raises(ValueError, match="segment unavailable"):
        build_manifest(candidates, horizon_minutes=60, fit_id="FINAL", segment_type="SCORE")
    with pytest.raises(ValueError, match="H1/prospective"):
        build_manifest((fixture("BTCUSDT", july + TWO_HOURS),), horizon_minutes=60,
                       fit_id="FINAL", segment_type="BASE")
    with pytest.raises(ValueError, match="segment unavailable"):
        build_manifest(candidates, horizon_minutes=60, fit_id="FINAL", segment_type="H1")


def test_independent_prospective_schedule_and_outcome_seal():
    exact = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    assert ceil_5m(exact) == exact
    assert ceil_5m(exact + timedelta(microseconds=1)) == exact + FIVE
    f60 = ReadinessEvidence(60, "FINAL_ARTIFACT", exact, "fixture:f60", "SYNTHETIC_FIXTURE")
    r60 = ReadinessEvidence(60, "COLLECTOR", exact + timedelta(minutes=1), "fixture:r60", "SYNTHETIC_FIXTURE")
    p60 = schedule_prospective(f60, r60)
    f120 = ReadinessEvidence(120, "FINAL_ARTIFACT", exact + timedelta(days=2), "fixture:f120", "SYNTHETIC_FIXTURE")
    r120 = ReadinessEvidence(120, "COLLECTOR", exact, "fixture:r120", "SYNTHETIC_FIXTURE")
    p120 = schedule_prospective(f120, r120)
    assert p60.start == exact + timedelta(minutes=125)
    assert p120.start == exact + timedelta(days=2, minutes=120)
    assert p60.end == p60.start + timedelta(days=90)
    assert p60.outcome_seal == p60.end + timedelta(days=7)
    assert p120.start > p60.start and p60.registration_status == "UNREGISTERED"
    assert not p60.operationally_registrable
    with pytest.raises(ValueError, match="same-horizon"):
        schedule_prospective(f60, r120)


def test_append_only_research_ledger_detects_corruption(tmp_path):
    stamp = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    root = tmp_path / "research-ledger"
    ledger = ExperimentLedger(root, clock=lambda: stamp)
    first = ledger.append(actor="synthetic-test", action="MANIFEST_CREATED", horizon_minutes=60,
                          fit_or_cohort_id="F1", partition_accessed="BASE",
                          manifest_hashes=(("base", "a" * 64),), artifact_hashes=(),
                          code_revision_or_hash="fixture-code")
    second = ledger.append(actor="synthetic-test", action="FIT_BUNDLE_SEALED", horizon_minutes=60,
                           fit_or_cohort_id="F1", partition_accessed="CALIBRATION",
                           manifest_hashes=(("base", "a" * 64),),
                           artifact_hashes=(("bundle", "b" * 64),), code_revision_or_hash="fixture-code")
    assert second.previous_entry_sha256 == first.entry_sha256
    assert ExperimentLedger(root).read_all() == (first, second)
    assert first.clock_source == "INJECTED_FIXTURE_CLOCK"
    original = (root / "000000000001.json").read_bytes()
    assert original == first.to_json().encode("utf-8")
    (root / "000000000001.json").write_bytes(original.replace(b"MANIFEST_CREATED", b"MANIFEST_CHANGED"))
    with pytest.raises(LedgerIntegrityError):
        ledger.read_all()
    with pytest.raises(LedgerIntegrityError):
        ledger.append(actor="x", action="y", horizon_minutes=60, fit_or_cohort_id="F1",
                      partition_accessed="BASE", manifest_hashes=(), artifact_hashes=(),
                      code_revision_or_hash="fixture")
