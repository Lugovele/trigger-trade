"""One report-only six-calendar-month shadow of the frozen primary family."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
import json
from typing import Iterable

from . import FEATURE_REGISTRY, SPEC_ID, SPEC_VERSION
from .calibration import CalibratedPrediction, CalibrationRow, ScalarCalibrator, fit_scalar_calibrator
from .calendar import D0, FIT_DEFINITIONS, iso, utc
from .manifests import ManifestMember, RowManifest, RowMetadata, canonical_json, digest
from .model import LAMBDA, Q_ID, ModelArtifact, ModelFitRow, RawPrediction, fit_model
from .orchestration import FitBundle, ScoredRow, _assert_manifest
from .preprocessing import (ColumnDomainState, EligibleBaseRow, PreprocessingState,
                            fit_preprocessing, transform)
from .report_only_matching import matched_primary_rows

SHADOW_ID = "SIX_MONTH_ROLLING_SHADOW"
_PURGE = timedelta(minutes=120)


def subtract_calendar_months(value: datetime, months: int = 6) -> datetime:
    """UTC calendar subtraction; never replace six months with fixed days."""
    value = utc(value)
    if months < 0:
        raise ValueError("nonnegative calendar months required")
    index = value.year * 12 + value.month - 1 - months
    year, zero_month = divmod(index, 12)
    month = zero_month + 1
    return value.replace(year=year, month=month,
                         day=min(value.day, monthrange(year, month)[1]))


@dataclass(frozen=True)
class ShadowWindow:
    fit_id: str
    calibration_start: datetime
    lower_bound: datetime
    upper_boundary: datetime
    warmup_status: str

    def contains(self, row: RowMetadata) -> bool:
        t = row.prediction_origin
        return self.lower_bound <= t and t + _PURGE < self.upper_boundary


def shadow_window(fit_id: str) -> ShadowWindow:
    if fit_id not in FIT_DEFINITIONS:
        raise ValueError("unsupported fit ID")
    c = FIT_DEFINITIONS[fit_id].calibration.nominal_start
    raw_lower = subtract_calendar_months(c)
    lower = max(D0, raw_lower)
    return ShadowWindow(fit_id, c, lower, c,
                        "WARMUP_LIMITED" if raw_lower < D0 else "DISTINCT_WINDOW")


@dataclass(frozen=True)
class ShadowBaseManifest:
    spec_id: str
    spec_version: str
    shadow_id: str
    horizon_minutes: int
    fit_id: str
    nominal_lower: str
    calibration_start: str
    eligibility_inequality: str
    warmup_status: str
    primary_base_manifest_sha256: str
    selected: tuple[ManifestMember, ...]
    excluded_by_window: tuple[tuple[str, str], ...]
    manifest_sha256: str

    def body(self) -> dict[str, object]:
        body = asdict(self)
        body.pop("manifest_sha256")
        return body

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    @classmethod
    def from_json(cls, text: str) -> ShadowBaseManifest:
        data = json.loads(text)
        data["selected"] = tuple(ManifestMember(**item) for item in data["selected"])
        data["excluded_by_window"] = tuple(tuple(item) for item in data["excluded_by_window"])
        result = cls(**data)
        if (result.spec_id != SPEC_ID or result.spec_version != SPEC_VERSION or
                result.shadow_id != SHADOW_ID or result.manifest_sha256 != digest(result.body())):
            raise ValueError("shadow base manifest identity mismatch")
        window = shadow_window(result.fit_id)
        if (result.nominal_lower != iso(window.lower_bound) or
                result.calibration_start != iso(window.calibration_start) or
                result.warmup_status != window.warmup_status):
            raise ValueError("shadow window differs from registered calendar")
        return result


def build_shadow_base_manifest(primary_base: RowManifest,
                               base_rows: Iterable[RowMetadata]) -> ShadowBaseManifest:
    if primary_base.segment_type != "BASE":
        raise ValueError("primary BASE manifest required")
    rows = _assert_manifest(primary_base, tuple(base_rows))
    window = shadow_window(primary_base.fit_id)
    selected = tuple(member for member, row in zip(primary_base.selected, rows)
                     if window.contains(row))
    excluded = tuple(member.key for member, row in zip(primary_base.selected, rows)
                     if not window.contains(row))
    provisional = ShadowBaseManifest(
        SPEC_ID, SPEC_VERSION, SHADOW_ID, primary_base.horizon_minutes, primary_base.fit_id,
        iso(window.lower_bound), iso(window.calibration_start),
        f"{iso(window.lower_bound)} <= t AND t + 120m < {iso(window.calibration_start)}",
        window.warmup_status, primary_base.manifest_sha256, selected, excluded, "")
    return replace(provisional, manifest_sha256=digest(provisional.body()))


def _preprocessing_from_dict(data: dict[str, object]) -> PreprocessingState:
    payload = dict(data)
    payload["physical_mapping"] = tuple(tuple(item) for item in payload["physical_mapping"])
    payload["btc_context_mask_indices"] = tuple(payload["btc_context_mask_indices"])
    payload["zero_slope_state_indices"] = tuple(payload["zero_slope_state_indices"])
    domains = []
    for item in payload["domains"]:
        domain = dict(item)
        domain["diagnostic_quantiles"] = tuple(domain["diagnostic_quantiles"])
        domains.append(ColumnDomainState(**domain))
    payload["domains"] = tuple(domains)
    return PreprocessingState(**payload)


@dataclass(frozen=True)
class ShadowPrediction:
    raw: RawPrediction
    calibrated: CalibratedPrediction
    shadow_sha256: str


@dataclass(frozen=True)
class ShadowArtifact:
    spec_id: str
    spec_version: str
    shadow_id: str
    horizon_minutes: int
    fit_id: str
    feature_registry: str
    primary_bundle_sha256: str
    primary_base_manifest_sha256: str
    shadow_base_manifest: ShadowBaseManifest
    calibration_manifest_sha256: str
    preprocessing: PreprocessingState
    preprocessing_sha256: str
    model: ModelArtifact
    model_sha256: str
    calibrator: ScalarCalibrator
    calibrator_sha256: str
    l2_lambda: float
    q_basis_id: str
    fit_status: str
    artifact_sha256: str

    def body(self) -> dict[str, object]:
        body = asdict(self)
        body.pop("artifact_sha256")
        return body

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    @classmethod
    def from_json(cls, text: str) -> ShadowArtifact:
        data = json.loads(text)
        data["shadow_base_manifest"] = ShadowBaseManifest.from_json(
            canonical_json(data["shadow_base_manifest"]))
        data["preprocessing"] = _preprocessing_from_dict(data["preprocessing"])
        data["model"] = ModelArtifact.from_json(canonical_json(data["model"]))
        data["calibrator"] = ScalarCalibrator.from_json(canonical_json(data["calibrator"]))
        result = cls(**data)
        result.verify()
        return result

    def verify(self) -> None:
        if (self.spec_id != SPEC_ID or self.spec_version != SPEC_VERSION or
                self.shadow_id != SHADOW_ID or self.feature_registry != FEATURE_REGISTRY or
                self.fit_status != "FITTED" or self.l2_lambda != LAMBDA or self.q_basis_id != Q_ID or
                self.horizon_minutes != self.model.horizon_minutes or
                self.horizon_minutes != self.calibrator.horizon_minutes or
                self.horizon_minutes != self.preprocessing.horizon_minutes or
                self.fit_id != self.shadow_base_manifest.fit_id or
                self.primary_base_manifest_sha256 != self.shadow_base_manifest.primary_base_manifest_sha256 or
                "SHADOW" not in self.preprocessing.fit_id or
                self.model.preprocessing_fit_id != self.preprocessing.fit_id or
                self.model.preprocessing_membership_sha256 != self.preprocessing.membership_sha256 or
                self.preprocessing_sha256 != digest(self.preprocessing.to_dict()) or
                self.model_sha256 != digest(json.loads(self.model.to_json())) or
                self.calibrator_sha256 != digest(json.loads(self.calibrator.to_json())) or
                self.artifact_sha256 != digest(self.body())):
            raise ValueError("shadow artifact identity or contract mismatch")

    def predict(self, physical_symbol: str, raw_feature_row) -> ShadowPrediction:
        self.verify()
        if raw_feature_row.physical_symbol != physical_symbol:
            raise ValueError("shadow symbol mismatch")
        processed = transform(raw_feature_row, self.preprocessing)
        raw = self.model.raw_prediction(physical_symbol, processed.values[:32])
        return ShadowPrediction(raw, self.calibrator.predict(raw), self.artifact_sha256)


@dataclass(frozen=True)
class ShadowScoredRow:
    prediction_origin: str
    physical_symbol: str
    horizon_minutes: int
    primary_score_manifest_sha256: str
    prediction: ShadowPrediction


def fit_shadow(*, primary: FitBundle, primary_base_manifest: RowManifest,
               calibration_manifest: RowManifest, base_rows: Iterable[RowMetadata],
               calibration_rows: Iterable[RowMetadata]) -> ShadowArtifact:
    """Own scaler/model/calibrator; only registered rolling base differs."""
    primary.verify_hashes()
    parent = primary.manifest
    if (primary_base_manifest.segment_type != "BASE" or
            calibration_manifest.segment_type != "CALIBRATION" or
            primary_base_manifest.fit_id != parent.fit_id or
            calibration_manifest.fit_id != parent.fit_id or
            primary_base_manifest.horizon_minutes != parent.horizon_minutes or
            calibration_manifest.horizon_minutes != parent.horizon_minutes or
            primary_base_manifest.manifest_sha256 != parent.base_manifest_sha256 or
            calibration_manifest.manifest_sha256 != parent.calibration_manifest_sha256):
        raise ValueError("shadow requires exact primary fit/calendar parents")
    base_rows = tuple(base_rows)
    shadow_manifest = build_shadow_base_manifest(primary_base_manifest, base_rows)
    primary_base = _assert_manifest(primary_base_manifest, base_rows)
    calibration = _assert_manifest(calibration_manifest, tuple(calibration_rows))
    selected_keys = {member.key for member in shadow_manifest.selected}
    base = tuple(row for row in primary_base if row.key in selected_keys)
    if not base:
        raise ValueError("shadow base is empty")
    fit_identity = f"LDE_V1_SHADOW_{parent.fit_id}_E{parent.horizon_minutes}_{digest({'shadow_base': shadow_manifest.manifest_sha256, 'calibration': calibration_manifest.manifest_sha256, 'primary': parent.bundle_sha256})}"
    preprocessing = fit_preprocessing(
        (EligibleBaseRow(row.feature_row, parent.horizon_minutes, fit_identity, "BASE", True)
         for row in base), horizon_minutes=parent.horizon_minutes, fit_id=fit_identity)
    processed_base = tuple(transform(row.feature_row, preprocessing) for row in base)
    model = fit_model((ModelFitRow(row.physical_symbol, processed.values[:32], row.canonical_class,
                                   row.prediction_origin)
                       for row, processed in zip(base, processed_base)),
                      horizon_minutes=parent.horizon_minutes, preprocessing=preprocessing)
    cal_logits = tuple(CalibrationRow(row.physical_symbol,
        model.raw_prediction(row.physical_symbol,
            transform(row.feature_row, preprocessing).values[:32]).logits,
        row.canonical_class) for row in calibration)
    calibrator = fit_scalar_calibrator(cal_logits, horizon_minutes=parent.horizon_minutes)
    provisional = ShadowArtifact(
        SPEC_ID, SPEC_VERSION, SHADOW_ID, parent.horizon_minutes, parent.fit_id,
        FEATURE_REGISTRY, parent.bundle_sha256, primary_base_manifest.manifest_sha256,
        shadow_manifest, calibration_manifest.manifest_sha256,
        preprocessing, digest(preprocessing.to_dict()), model, digest(json.loads(model.to_json())),
        calibrator, digest(json.loads(calibrator.to_json())), LAMBDA, Q_ID, "FITTED", "")
    result = replace(provisional, artifact_sha256=digest(provisional.body()))
    result.verify()
    return result


def score_shadow(artifact: ShadowArtifact, *, primary: FitBundle,
                 scored_manifest: RowManifest, scored_rows: Iterable[RowMetadata],
                 primary_scored_rows: Iterable[ScoredRow]
                 ) -> tuple[ShadowScoredRow, ...]:
    """Matched primary development score keys only; FINAL H1/P use is deferred."""
    if (scored_manifest.segment_type != "SCORE" or
            scored_manifest.fit_id != artifact.fit_id or
            scored_manifest.horizon_minutes != artifact.horizon_minutes or
            primary.manifest.bundle_sha256 != artifact.primary_bundle_sha256):
        raise ValueError("matched primary SCORE manifest required")
    artifact.verify()
    matched = matched_primary_rows(primary=primary, scored_manifest=scored_manifest,
        scored_rows=scored_rows, primary_scored_rows=primary_scored_rows)
    return tuple(ShadowScoredRow(member.prediction_origin, row.physical_symbol,
        artifact.horizon_minutes, scored_manifest.manifest_sha256,
        artifact.predict(row.physical_symbol, row.feature_row))
        for row, member in matched)
