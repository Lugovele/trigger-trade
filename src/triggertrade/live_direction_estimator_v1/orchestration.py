"""Caller-supplied, horizon-isolated base/calibration/score wiring.

This module has no corpus reader, label generator, H1 scorer, prospective
runner, or fold loop. The caller owns source/label authentication and permits.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
import json
import re
from typing import Iterable

from . import FEATURE_REGISTRY, SPEC_ID, SPEC_VERSION
from .baselines import BaselineFitRow, BaselineState, b2_trailing_h_sign, fit_baselines
from .calibration import CalibratedPrediction, CalibrationRow, ScalarCalibrator, fit_scalar_calibrator
from .calendar import FIT_DEFINITIONS, iso
from .manifests import RowManifest, RowMetadata, build_manifest, canonical_json, digest
from .model import ModelArtifact, ModelFitRow, RawPrediction, fit_model
from .preprocessing import EligibleBaseRow, PreprocessingState, fit_preprocessing, transform

_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class IdentityReferences:
    source_manifest_sha256: str
    canonical_release_id: str
    canonical_label_sha256: str
    evidence_status: str = "DECLARED_UNVERIFIED"

    def __post_init__(self) -> None:
        if (not _HEX64.fullmatch(self.source_manifest_sha256) or
                not _HEX64.fullmatch(self.canonical_label_sha256) or
                not self.canonical_release_id or
                self.evidence_status not in {"DECLARED_UNVERIFIED", "SYNTHETIC_FIXTURE"}):
            raise ValueError("explicit unverified/synthetic source and canonical identities required")


@dataclass(frozen=True)
class FitBundleManifest:
    spec_id: str
    spec_version: str
    feature_registry: str
    horizon_minutes: int
    fit_id: str
    artifact_id: str
    base_manifest_sha256: str
    calibration_manifest_sha256: str
    preprocessing_sha256: str
    model_sha256: str
    calibrator_sha256: str
    b0_sha256: str
    b1_sha256: str
    b3_sha256: str
    b2_contract_id: str
    identities: IdentityReferences
    bundle_sha256: str

    def body(self) -> dict[str, object]:
        body = asdict(self)
        body.pop("bundle_sha256")
        return body

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> FitBundleManifest:
        body = json.loads(data)
        body["identities"] = IdentityReferences(**body["identities"])
        result = cls(**body)
        if (result.spec_id != SPEC_ID or result.spec_version != SPEC_VERSION or
                result.feature_registry != FEATURE_REGISTRY or
                result.fit_id not in FIT_DEFINITIONS or
                digest(result.body()) != result.bundle_sha256):
            raise ValueError("fit bundle manifest identity mismatch")
        return result


@dataclass(frozen=True)
class FitBundle:
    manifest: FitBundleManifest
    preprocessing: PreprocessingState
    model: ModelArtifact
    calibrator: ScalarCalibrator
    baselines: BaselineState

    def verify_hashes(self) -> None:
        manifest = self.manifest
        if (digest(self.preprocessing.to_dict()) != manifest.preprocessing_sha256 or
                digest(json.loads(self.model.to_json())) != manifest.model_sha256 or
                digest(json.loads(self.calibrator.to_json())) != manifest.calibrator_sha256 or
                digest(json.loads(self.baselines.b0_state().to_json())) != manifest.b0_sha256 or
                digest(json.loads(self.baselines.b1_state().to_json())) != manifest.b1_sha256 or
                digest(json.loads(self.baselines.b3_state().to_json())) != manifest.b3_sha256 or
                digest(manifest.body()) != manifest.bundle_sha256):
            raise ValueError("fit bundle artifact hash mismatch")


@dataclass(frozen=True)
class ScoredRow:
    prediction_origin: str
    physical_symbol: str
    horizon_minutes: int
    feature_row_sha256: str
    source_snapshot_id: str
    bundle_sha256: str
    raw: RawPrediction
    calibrated: CalibratedPrediction
    b0_hard_class: str
    b1_probabilities: tuple[float, float, float]
    b2_hard_class: str
    b3_probabilities: tuple[float, float, float]


def _assert_manifest(manifest: RowManifest, rows: tuple[RowMetadata, ...]) -> tuple[RowMetadata, ...]:
    rebuilt = build_manifest(rows, horizon_minutes=manifest.horizon_minutes, fit_id=manifest.fit_id,
                             segment_type=manifest.segment_type)
    if rebuilt.to_json() != manifest.to_json():
        raise ValueError("caller rows differ from sealed row manifest")
    by_key = {row.key: row for row in rows}
    return tuple(by_key[member.key] for member in manifest.selected)


def _fit_identity(base: RowManifest, calibration: RowManifest,
                  identities: IdentityReferences) -> str:
    parents = digest({"fit_id": base.fit_id, "horizon_minutes": base.horizon_minutes,
                      "base_manifest_sha256": base.manifest_sha256,
                      "calibration_manifest_sha256": calibration.manifest_sha256,
                      "source_and_canonical_identities": asdict(identities)})
    return f"LDE_V1_{base.fit_id}_E{base.horizon_minutes}_{parents}"


def fit_pipeline(*, base_manifest: RowManifest, calibration_manifest: RowManifest,
                 base_rows: Iterable[RowMetadata], calibration_rows: Iterable[RowMetadata],
                 identities: IdentityReferences) -> FitBundle:
    """Single bounded fit call; only registered BASE/CALIBRATION manifests enter."""
    if (base_manifest.segment_type != "BASE" or calibration_manifest.segment_type != "CALIBRATION" or
            base_manifest.fit_id != calibration_manifest.fit_id or
            base_manifest.horizon_minutes != calibration_manifest.horizon_minutes or
            base_manifest.fit_id not in FIT_DEFINITIONS):
        raise ValueError("same-fit BASE and CALIBRATION manifests required")
    base = _assert_manifest(base_manifest, tuple(base_rows))
    calibration = _assert_manifest(calibration_manifest, tuple(calibration_rows))
    horizon = base_manifest.horizon_minutes
    fit_id = _fit_identity(base_manifest, calibration_manifest, identities)
    preprocessing = fit_preprocessing(
        (EligibleBaseRow(r.feature_row, horizon, fit_id, "BASE", True) for r in base),
        horizon_minutes=horizon, fit_id=fit_id)
    processed_base = tuple(transform(r.feature_row, preprocessing) for r in base)
    model = fit_model((ModelFitRow(r.physical_symbol, processed.values[:32], r.canonical_class,
                                   r.prediction_origin)
                       for r, processed in zip(base, processed_base)),
                      horizon_minutes=horizon, preprocessing=preprocessing)
    baselines = fit_baselines((BaselineFitRow(r.physical_symbol, r.canonical_class, r.trailing_h_sign)
                              for r in base), horizon_minutes=horizon)
    expected_symbol_class = tuple(tuple(sum(r.physical_symbol == s and r.canonical_class == c for r in base)
                                        for c in model.class_order) for s in ("BTCUSDT", "AVAXUSDT", "SUIUSDT", "1000PEPEUSDT"))
    if (model.counts_by_symbol_class != expected_symbol_class or
            baselines.counts_by_symbol_class != expected_symbol_class or
            model.preprocessing_membership_sha256 != preprocessing.membership_sha256):
        raise ValueError("base populations differ across preprocessing/model/baselines")
    calibration_logits = tuple(CalibrationRow(r.physical_symbol,
        model.raw_prediction(r.physical_symbol, transform(r.feature_row, preprocessing).values[:32]).logits,
        r.canonical_class) for r in calibration)
    calibrator = fit_scalar_calibrator(calibration_logits, horizon_minutes=horizon)
    artifact_id = f"{SPEC_ID}:{fit_id}"
    provisional = FitBundleManifest(
        SPEC_ID, SPEC_VERSION, FEATURE_REGISTRY, horizon, base_manifest.fit_id, artifact_id,
        base_manifest.manifest_sha256, calibration_manifest.manifest_sha256,
        digest(preprocessing.to_dict()), digest(json.loads(model.to_json())),
        digest(json.loads(calibrator.to_json())),
        digest(json.loads(baselines.b0_state().to_json())),
        digest(json.loads(baselines.b1_state().to_json())),
        digest(json.loads(baselines.b3_state().to_json())),
        f"B2_TRAILING_H_SIGN:E{horizon}:U=T-1m:H+5m-support", identities, "")
    manifest = replace(provisional, bundle_sha256=digest(provisional.body()))
    bundle = FitBundle(manifest, preprocessing, model, calibrator, baselines)
    bundle.verify_hashes()
    return bundle


def score_bundle(bundle: FitBundle, *, scored_manifest: RowManifest,
                 scored_rows: Iterable[RowMetadata]) -> tuple[ScoredRow, ...]:
    """Pure frozen-bundle prediction for F1–F5 score segments; no fit calls."""
    if (scored_manifest.segment_type != "SCORE" or scored_manifest.fit_id == "FINAL" or
            scored_manifest.fit_id != bundle.manifest.fit_id or
            scored_manifest.horizon_minutes != bundle.manifest.horizon_minutes):
        raise ValueError("only same-horizon development SCORE manifest is supported")
    bundle.verify_hashes()
    rows = _assert_manifest(scored_manifest, tuple(scored_rows))
    output = []
    for row, member in zip(rows, scored_manifest.selected):
        processed = transform(row.feature_row, bundle.preprocessing)
        raw = bundle.model.raw_prediction(row.physical_symbol, processed.values[:32])
        calibrated = bundle.calibrator.predict(raw)
        output.append(ScoredRow(iso(row.prediction_origin), row.physical_symbol, row.horizon_minutes,
                                member.feature_row_sha256, member.source_snapshot_id,
                                bundle.manifest.bundle_sha256, raw, calibrated,
                                bundle.baselines.b0_symbol_majority(row.physical_symbol),
                                bundle.baselines.b1_symbol_prior(row.physical_symbol),
                                b2_trailing_h_sign(row.trailing_h_sign),
                                bundle.baselines.b3_symbol_sign_frequency(row.physical_symbol,
                                                                           row.trailing_h_sign)))
    return tuple(output)
