"""Complete immutable Section 22.2 origin record and separate later outcome join."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
import json
from math import exp, isfinite, ulp
from typing import Callable, Iterable

from . import FEATURE_REGISTRY, SPEC_ID, SPEC_VERSION
from .calendar import Horizon, iso, origin, utc
from .manifests import canonical_json, digest
from .model import CLASSES
from .evaluation_metrics import ProbabilityState, hard_class
from .source import SYMBOLS

REASON_ORDER = (
    "UNSUPPORTED_SYMBOL", "INVALID_ORIGIN", "SOURCE_VERSION_CONFLICT",
    "MISSING_REQUIRED_MINUTE", "INVALID_REQUIRED_OHLC", "INCOMPLETE_FINALIZATION",
    "UNVERIFIED_AVAILABILITY", "DATA_LATE", "INVALID_PREDICTOR_SCALE",
    "NUMERICAL_FEATURE_ERROR", "FITTED_STATE_UNAVAILABLE", "MODEL_NOT_ESTIMABLE",
    "FIT_FAILED", "CALIBRATION_FAILED", "NUMERICAL_PREDICTION_ERROR", "MISSED_DEADLINE",
)


def _parse(value: str | None) -> datetime | None:
    return utc(datetime.fromisoformat(value.replace("Z", "+00:00"))) if value is not None else None


@dataclass(frozen=True)
class OriginIdentity:
    spec_id: str
    specification_revision: str
    specification_sha256: str
    feature_registry: str
    feature_registry_sha256: str
    evidence_cohort_id: str
    physical_symbol: str
    logical_alias: str | None
    horizon_minutes: int
    fit_id: str | None
    preprocessing_id: str | None
    calibrator_id: str | None


@dataclass(frozen=True)
class OriginTimes:
    prediction_origin: str
    feature_timestamp: str
    information_cutoff: str
    prediction_timestamp: str | None
    terminal_status_recorded_at: str
    fitted_state_available_at: str | None


@dataclass(frozen=True)
class OriginStatus:
    record_kind: str
    prediction_status: str
    unavailable_reasons: tuple[str, ...]
    live_deadline_status: str
    provenance_mode: str | None


@dataclass(frozen=True)
class SourceVersionAudit:
    physical_symbol: str
    interval_start: str
    interval_end: str
    version_id: str
    raw_payload_sha256: str
    receipt_evidence_ref: str | None
    finalization_evidence_ref: str | None


@dataclass(frozen=True)
class OriginInputs:
    source_snapshot_id: str | None
    selected_source_versions: tuple[SourceVersionAudit, ...]
    receipt_evidence_refs: tuple[str, ...]
    finalization_evidence_refs: tuple[str, ...]
    clock_evidence_ref: str | None
    local_support_span: tuple[str, str] | None
    btc_support_span: tuple[str, str] | None
    asof_verification_ref: str | None


@dataclass(frozen=True)
class FeatureAudit:
    raw_35: tuple[float, ...] | None
    raw_immutable_ref: str | None
    transformed_35: tuple[float, ...] | None
    transformed_immutable_ref: str | None
    constant_flags: tuple[int, ...] | None
    mask_flags: tuple[int, ...] | None
    predictor_sigma_48_u: float | None


@dataclass(frozen=True)
class ProbabilityAudit:
    raw_logits: tuple[float, float, float] | None
    calibrated_logits: tuple[float, float, float] | None
    raw_log_probabilities: tuple[float, float, float] | None
    calibrated_log_probabilities: tuple[float, float, float] | None
    p_L: float | None
    p_S: float | None
    p_N: float | None
    predicted_class: str | None
    confidence: float | None

    @classmethod
    def unavailable(cls) -> ProbabilityAudit:
        return cls(None, None, None, None, None, None, None, None, None)


@dataclass(frozen=True)
class DiagnosticLinks:
    baseline_state_ids: tuple[tuple[str, str], ...]
    baseline_outputs: tuple[tuple[str, str], ...]
    comparator_status_sha256: str | None
    comparator_output_ref: str | None
    shadow_status_sha256: str | None
    shadow_output_ref: str | None


@dataclass(frozen=True)
class LaterOutcomeLinkage:
    canonical_target_key: tuple[str, str, int] | None
    canonical_target_status: str | None
    target_file_sha256: str | None
    source_vintage_id: str | None
    calculation_version: str | None
    horizon_maturity_at: str | None
    outcome_dataset_seal_sha256: str | None

    @classmethod
    def pending(cls) -> LaterOutcomeLinkage:
        return cls(None, None, None, None, None, None, None)


@dataclass(frozen=True)
class OriginRecord:
    identity: OriginIdentity
    times: OriginTimes
    status: OriginStatus
    inputs: OriginInputs
    features: FeatureAudit
    probabilities: ProbabilityAudit
    diagnostics: DiagnosticLinks
    later_outcome: LaterOutcomeLinkage
    record_sha256: str

    @property
    def key(self) -> tuple[str, str, str, str, int]:
        return (self.identity.specification_revision, self.identity.evidence_cohort_id,
                self.identity.physical_symbol, self.times.prediction_origin,
                self.identity.horizon_minutes)

    def body(self) -> dict[str, object]:
        value = asdict(self)
        value.pop("record_sha256")
        return value

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    @classmethod
    def from_json(cls, text: str) -> OriginRecord:
        data = json.loads(text)
        data["identity"] = OriginIdentity(**data["identity"])
        data["times"] = OriginTimes(**data["times"])
        status = data["status"]
        status["unavailable_reasons"] = tuple(status["unavailable_reasons"])
        data["status"] = OriginStatus(**status)
        inputs = data["inputs"]
        inputs["selected_source_versions"] = tuple(SourceVersionAudit(**item)
                                                    for item in inputs["selected_source_versions"])
        for name in ("receipt_evidence_refs", "finalization_evidence_refs"):
            inputs[name] = tuple(inputs[name])
        for name in ("local_support_span", "btc_support_span"):
            if inputs[name] is not None:
                inputs[name] = tuple(inputs[name])
        data["inputs"] = OriginInputs(**inputs)
        features = data["features"]
        for name in ("raw_35", "transformed_35", "constant_flags", "mask_flags"):
            if features[name] is not None:
                features[name] = tuple(features[name])
        data["features"] = FeatureAudit(**features)
        probabilities = data["probabilities"]
        for name in ("raw_logits", "calibrated_logits", "raw_log_probabilities",
                     "calibrated_log_probabilities"):
            if probabilities[name] is not None:
                probabilities[name] = tuple(probabilities[name])
        data["probabilities"] = ProbabilityAudit(**probabilities)
        diagnostics = data["diagnostics"]
        for name in ("baseline_state_ids", "baseline_outputs"):
            diagnostics[name] = tuple(tuple(item) for item in diagnostics[name])
        data["diagnostics"] = DiagnosticLinks(**diagnostics)
        later = data["later_outcome"]
        if later["canonical_target_key"] is not None:
            later["canonical_target_key"] = tuple(later["canonical_target_key"])
        data["later_outcome"] = LaterOutcomeLinkage(**later)
        result = cls(**data)
        if result.record_sha256 != digest(result.body()):
            raise ValueError("origin record hash mismatch")
        return result

    def validate(self, *, asof_verifier: Callable[[OriginRecord], bool] | None = None,
                 snapshot_verifier: Callable[[OriginRecord], bool] | None = None
                 ) -> tuple[str, ...]:
        errors = []
        i, t, s, inputs, features, probabilities = (self.identity, self.times, self.status,
                                                     self.inputs, self.features, self.probabilities)
        if self.record_sha256 != digest(self.body()):
            errors.append("RECORD_HASH_MISMATCH")
        if (i.spec_id != SPEC_ID or i.specification_revision != SPEC_VERSION or
                i.feature_registry != FEATURE_REGISTRY or i.physical_symbol not in SYMBOLS or
                i.horizon_minutes not in (60, 120) or not i.evidence_cohort_id or
                not i.specification_sha256 or not i.feature_registry_sha256):
            errors.append("IDENTITY_INVALID")
        if i.logical_alias is not None and (
                i.logical_alias != "PEPEUSDT" or i.physical_symbol != "1000PEPEUSDT"):
            errors.append("LOGICAL_ALIAS_INVALID")
        prediction_origin = None
        try:
            prediction_origin = origin(_parse(t.prediction_origin))
            if (_parse(t.feature_timestamp) != prediction_origin - timedelta(minutes=1) or
                    _parse(t.information_cutoff) != prediction_origin):
                errors.append("FEATURE_WATERMARK_OR_CUTOFF_INVALID")
            emitted_at, recorded_at = _parse(t.prediction_timestamp), _parse(t.terminal_status_recorded_at)
            fitted_at = _parse(t.fitted_state_available_at)
            if recorded_at is None:
                errors.append("ACTUAL_TERMINAL_RECORD_TIME_MISSING")
            if s.record_kind == "PROSPECTIVE_FORECAST" and s.prediction_status == "AVAILABLE":
                if (emitted_at is None or not prediction_origin <= emitted_at <
                        prediction_origin + timedelta(minutes=5)):
                    errors.append("MISSED_DEADLINE_OR_BACKDATED_EMISSION")
                if fitted_at is None or fitted_at > prediction_origin:
                    errors.append("FITTED_STATE_BY_T_UNVERIFIED")
            elif s.prediction_status == "UNAVAILABLE" and emitted_at is not None:
                errors.append("UNAVAILABLE_HAS_EMISSION_TIME")
            elif s.record_kind == "HISTORICAL_SIMULATION" and s.prediction_status == "AVAILABLE" and emitted_at is None:
                errors.append("HISTORICAL_ACTUAL_COMPUTATION_TIME_MISSING")
        except (TypeError, ValueError):
            errors.append("INVALID_ACTUAL_TIMESTAMP")
        if (s.record_kind not in {"PROSPECTIVE_FORECAST", "HISTORICAL_SIMULATION"} or
                s.prediction_status not in {"AVAILABLE", "UNAVAILABLE"} or
                s.live_deadline_status not in {"ON_TIME", "MISSED_DEADLINE", "NOT_APPLICABLE"}):
            errors.append("STATUS_INVALID")
        if s.record_kind == "HISTORICAL_SIMULATION" and (
                s.provenance_mode not in {None, "EVENT_TIME_ONLY"} or
                s.live_deadline_status != "NOT_APPLICABLE"):
            errors.append("HISTORICAL_PROVENANCE_INVALID")
        if s.record_kind == "PROSPECTIVE_FORECAST" and s.prediction_status == "AVAILABLE" and (
                s.provenance_mode != "ASOF_VERIFIED" or s.live_deadline_status != "ON_TIME"):
            errors.append("PROSPECTIVE_PROVENANCE_INVALID")
        if (s.record_kind == "PROSPECTIVE_FORECAST" and s.prediction_status == "UNAVAILABLE" and
                s.provenance_mode == "ASOF_VERIFIED" and not inputs.asof_verification_ref):
            errors.append("UNVERIFIED_ASOF_CLAIM")
        if (len(set(s.unavailable_reasons)) != len(s.unavailable_reasons) or
                any(reason not in REASON_ORDER for reason in s.unavailable_reasons) or
                tuple(sorted(s.unavailable_reasons, key=REASON_ORDER.index)) != s.unavailable_reasons):
            errors.append("UNAVAILABLE_REASONS_OUT_OF_ORDER")
        if s.prediction_status == "UNAVAILABLE":
            if not s.unavailable_reasons:
                errors.append("UNAVAILABLE_REASON_MISSING")
            if probabilities != ProbabilityAudit.unavailable() or t.prediction_timestamp is not None:
                errors.append("UNAVAILABLE_OUTPUTS_NOT_NULL")
        else:
            if s.unavailable_reasons or not all((i.fit_id, i.preprocessing_id, i.calibrator_id,
                    inputs.source_snapshot_id)):
                errors.append("AVAILABLE_ARTIFACT_OR_SNAPSHOT_MISSING")
            if ((features.raw_35 is None) == (features.raw_immutable_ref is None) or
                    (features.transformed_35 is None) == (features.transformed_immutable_ref is None)):
                errors.append("FEATURE_VECTOR_OR_IMMUTABLE_REF_MISSING")
            for values in (features.raw_35, features.transformed_35):
                if values is not None and (len(values) != 35 or any(not isfinite(v) for v in values)):
                    errors.append("FEATURE_VECTOR_INVALID")
            for flags in (features.constant_flags, features.mask_flags):
                if (flags is None or any(not isinstance(v, int) or isinstance(v, bool) or
                                         not 1 <= v <= 35 for v in flags) or
                        tuple(sorted(set(flags))) != flags):
                    errors.append("FEATURE_AUDIT_FLAGS_INVALID")
            if features.mask_flags is not None and features.mask_flags != (
                    tuple(range(24,31)) if i.physical_symbol == "BTCUSDT" else ()):
                errors.append("BTC_CONTEXT_MASK_INVALID")
            if (i.physical_symbol == "BTCUSDT" and features.transformed_35 is not None and
                    len(features.transformed_35) == 35 and
                    any(value != 0.0 for value in features.transformed_35[23:30])):
                errors.append("BTC_CONTEXT_NOT_ZERO_AFTER_PREPROCESSING")
            expected_baselines = ("B0", "B1", "B2", "B3")
            for linkage in (self.diagnostics.baseline_state_ids,
                            self.diagnostics.baseline_outputs):
                if (tuple(name for name, _ in linkage) != expected_baselines or
                        any(not reference for _, reference in linkage)):
                    errors.append("BASELINE_LINKAGE_INCOMPLETE")
            if (not self.diagnostics.comparator_status_sha256 or
                    not self.diagnostics.shadow_status_sha256):
                errors.append("REPORT_ONLY_STATUS_LINKAGE_INCOMPLETE")
            if (features.predictor_sigma_48_u is None or
                    not isfinite(features.predictor_sigma_48_u) or
                    features.predictor_sigma_48_u <= 0):
                errors.append("PREDICTOR_SIGMA_48_U_INVALID")
            elif features.raw_35 is not None and len(features.raw_35) == 35:
                try:
                    recovered = exp(features.raw_35[19])
                    declared = features.predictor_sigma_48_u
                    if abs(recovered-declared) > 4*max(ulp(recovered), ulp(declared)):
                        errors.append("PREDICTOR_SIGMA_48_U_MISMATCH")
                except OverflowError:
                    errors.append("PREDICTOR_SIGMA_48_U_MISMATCH")
            if (inputs.local_support_span is None or
                    (i.physical_symbol != "BTCUSDT" and inputs.btc_support_span is None)):
                errors.append("SOURCE_SUPPORT_SPAN_MISSING")
            else:
                try:
                    if prediction_origin is None:
                        raise ValueError("invalid origin")
                    expected = (prediction_origin - timedelta(minutes=1446),
                                prediction_origin - timedelta(minutes=1))
                    if tuple(_parse(value) for value in inputs.local_support_span) != expected or (
                            i.physical_symbol != "BTCUSDT" and
                            tuple(_parse(value) for value in inputs.btc_support_span) != expected):
                        errors.append("SOURCE_SUPPORT_SPAN_INVALID")
                except (TypeError, ValueError):
                    errors.append("SOURCE_SUPPORT_SPAN_INVALID")
            if (not inputs.selected_source_versions or snapshot_verifier is None or
                    not snapshot_verifier(self)):
                errors.append("SOURCE_SNAPSHOT_UNRESOLVED")
            triplets = (probabilities.raw_logits, probabilities.calibrated_logits,
                        probabilities.raw_log_probabilities, probabilities.calibrated_log_probabilities)
            if (any(values is None or len(values) != 3 or any(not isfinite(v) for v in values)
                    for values in triplets) or
                    any(value is None or not isfinite(value) or value < 0 or value > 1
                        for value in (probabilities.p_L, probabilities.p_S, probabilities.p_N)) or
                    probabilities.predicted_class not in CLASSES or
                    probabilities.confidence is None):
                errors.append("AVAILABLE_PROBABILITIES_INVALID")
            elif (abs(probabilities.p_L + probabilities.p_S + probabilities.p_N - 1) > 1e-12 or
                    probabilities.confidence != max(probabilities.p_L, probabilities.p_S, probabilities.p_N)):
                errors.append("AVAILABLE_SIMPLEX_OR_CONFIDENCE_INVALID")
            if all(value is not None for value in triplets) and all(
                    value is not None for value in (probabilities.p_L, probabilities.p_S, probabilities.p_N)):
                try:
                    raw_logs = probabilities.raw_log_probabilities
                    ProbabilityState(tuple(exp(v) for v in raw_logs), raw_logs,
                        hard_class(probabilities.raw_logits),
                        probabilities.raw_logits)
                    calibrated = ProbabilityState(
                        (probabilities.p_L, probabilities.p_S, probabilities.p_N),
                        probabilities.calibrated_log_probabilities,
                        probabilities.predicted_class, probabilities.calibrated_logits)
                    if calibrated.hard_class != probabilities.predicted_class:
                        errors.append("PREDICTED_CLASS_MISMATCH")
                except (ValueError, OverflowError, TypeError):
                    errors.append("PROBABILITY_LOGIT_IDENTITY_MISMATCH")
        if s.provenance_mode == "ASOF_VERIFIED":
            if (s.record_kind != "PROSPECTIVE_FORECAST" or not inputs.source_snapshot_id or
                    not inputs.selected_source_versions or not inputs.receipt_evidence_refs or
                    not inputs.finalization_evidence_refs or not inputs.clock_evidence_ref or
                    not inputs.asof_verification_ref or asof_verifier is None or not asof_verifier(self)):
                errors.append("ASOF_UNVERIFIED")
        if self.later_outcome != LaterOutcomeLinkage.pending():
            errors.append("OUTCOME_MUTATED_IN_ORIGIN_RECORD")
        return tuple(dict.fromkeys(errors))


def seal_origin_record(identity: OriginIdentity, times: OriginTimes, status: OriginStatus,
                       inputs: OriginInputs, features: FeatureAudit,
                       probabilities: ProbabilityAudit, diagnostics: DiagnosticLinks,
                       *, asof_verifier: Callable[[OriginRecord], bool] | None = None,
                       snapshot_verifier: Callable[[OriginRecord], bool] | None = None) -> OriginRecord:
    provisional = OriginRecord(identity, times, status, inputs, features, probabilities,
                               diagnostics, LaterOutcomeLinkage.pending(), "")
    result = replace(provisional, record_sha256=digest(provisional.body()))
    errors = result.validate(asof_verifier=asof_verifier, snapshot_verifier=snapshot_verifier)
    if errors:
        raise ValueError(";".join(errors))
    return result


def assert_unique_origin_keys(records: Iterable[OriginRecord]) -> None:
    seen = set()
    for record in records:
        if record.key in seen:
            raise ValueError("duplicate specification/cohort/symbol/origin/horizon key")
        seen.add(record.key)


@dataclass(frozen=True)
class JoinedOriginOutcome:
    origin_record_sha256: str
    origin_key: tuple[str, str, str, str, int]
    outcome: LaterOutcomeLinkage
    canonical_class: str | None
    evaluation_record_sha256: str

    def body(self) -> dict[str, object]:
        body = asdict(self)
        body.pop("evaluation_record_sha256")
        return body


def join_outcome(origin_record: OriginRecord, outcome: LaterOutcomeLinkage,
                 canonical_class: str | None) -> JoinedOriginOutcome:
    if (origin_record.record_sha256 != digest(origin_record.body()) or
            origin_record.later_outcome != LaterOutcomeLinkage.pending() or (
            outcome.canonical_target_key != (origin_record.identity.physical_symbol,
                                             origin_record.times.prediction_origin,
                                             origin_record.identity.horizon_minutes))):
        raise ValueError("outcome key must match immutable origin record")
    if outcome.canonical_target_status == "VALID" and canonical_class not in CLASSES:
        raise ValueError("valid canonical outcome requires class")
    if outcome.canonical_target_status == "VALID" and not all((
            outcome.target_file_sha256, outcome.source_vintage_id,
            outcome.calculation_version, outcome.horizon_maturity_at,
            outcome.outcome_dataset_seal_sha256)):
        raise ValueError("valid outcome requires complete canonical and dataset identities")
    if outcome.canonical_target_status != "VALID" and canonical_class is not None:
        raise ValueError("unavailable target cannot carry class")
    provisional = JoinedOriginOutcome(origin_record.record_sha256, origin_record.key,
                                      outcome, canonical_class, "")
    return replace(provisional, evaluation_record_sha256=digest(provisional.body()))
