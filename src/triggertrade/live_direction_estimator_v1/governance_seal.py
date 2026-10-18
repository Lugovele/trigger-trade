"""Offline H1 and per-horizon prospective governance contracts.

Hashes and local timestamps are identities, not authentication. Operational
readiness needs an injected independent verifier and genuine external evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
import json
from math import isfinite
import re
from typing import Callable

from . import FEATURE_REGISTRY, SPEC_ID, SPEC_VERSION
from .calendar import (H1_END, H1_START, ProspectiveSchedule, ReadinessEvidence,
                       iso, schedule_prospective, utc)
from .manifests import canonical_json, digest
from .orchestration import FitBundleManifest
from .registry_identity import EnvironmentIdentity, RegistryDescriptor, SpecificationBytes, frozen_registry
from .report_only_status import ReportOnlyStatus

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ACCESS_CATEGORIES = {"PRICES", "LABELS", "COUNTS", "SELECTED_CASES",
                      "FEATURE_DISTRIBUTIONS", "FITTED_OUTPUTS", "PERFORMANCE"}
_PROOF_KINDS = ("SPEC_BYTES", "CLOCK", "ARTIFACT_AVAILABILITY", "LEDGER_ANCHOR",
                "SOURCE_IDENTITY", "LABEL_BYTES", "ENVIRONMENT_LOCK")


def _parse_utc(value: str) -> datetime:
    return utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


@dataclass(frozen=True)
class AuthenticationResult:
    kind: str
    subject_ref: str
    status: str  # UNVERIFIED, SYNTHETIC_FIXTURE, EXTERNAL_VERIFIED
    authority_ref: str | None
    verified_at: str | None
    maximum_error_seconds: float | None = None

    def __post_init__(self) -> None:
        if self.kind not in (*_PROOF_KINDS, "H1_AUDIT", "PRE_H1_FREEZE", "H1_FIRST_SCORE_ACCESS") or not self.subject_ref or self.status not in {
                "UNVERIFIED", "SYNTHETIC_FIXTURE", "EXTERNAL_VERIFIED"}:
            raise ValueError("invalid authentication result")
        if self.status != "UNVERIFIED":
            if not self.authority_ref or not self.verified_at:
                raise ValueError("affirmative authentication requires authority and actual time")
            _parse_utc(self.verified_at)
        if self.kind == "CLOCK" and self.status != "UNVERIFIED" and (
                self.maximum_error_seconds is None or not isfinite(self.maximum_error_seconds) or
                self.maximum_error_seconds < 0):
            raise ValueError("clock attestation requires nonnegative bounded error")


@dataclass(frozen=True)
class H1Access:
    category: str
    accessed_at: str
    evidence_ref: str
    affected_estimator_choices: str  # YES, NO, UNKNOWN

    def __post_init__(self) -> None:
        if (self.category not in _ACCESS_CATEGORIES or not self.evidence_ref or
                self.affected_estimator_choices not in {"YES", "NO", "UNKNOWN"}):
            raise ValueError("invalid H1 access evidence")
        _parse_utc(self.accessed_at)


@dataclass(frozen=True)
class H1GovernanceEvidence:
    nominal_start: str
    nominal_end: str
    accesses: tuple[H1Access, ...]
    audit_inventory_complete: bool
    audit_reference: str | None
    audit_authentication: AuthenticationResult | None
    evidence_sha256: str

    def body(self) -> dict[str, object]:
        body = asdict(self)
        body.pop("evidence_sha256")
        return body

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    @classmethod
    def create(cls, accesses: tuple[H1Access, ...] = (), *,
               audit_inventory_complete: bool = False,
               audit_reference: str | None = None,
               audit_authentication: AuthenticationResult | None = None) -> H1GovernanceEvidence:
        provisional = cls(iso(H1_START), iso(H1_END), accesses,
                          audit_inventory_complete, audit_reference,
                          audit_authentication, "")
        if audit_authentication is not None and (
                audit_authentication.kind != "H1_AUDIT" or
                audit_authentication.subject_ref != provisional.audit_subject()):
            raise ValueError("H1 audit proof must bind the full access inventory and choice-impact claims")
        return replace(provisional, evidence_sha256=digest(provisional.body()))

    def audit_subject(self) -> str:
        return digest({"nominal_start": self.nominal_start, "nominal_end": self.nominal_end,
                       "accesses": tuple(asdict(item) for item in self.accesses),
                       "audit_inventory_complete": self.audit_inventory_complete,
                       "audit_reference": self.audit_reference})

    def cleanliness(self, *, verifier: Callable[[AuthenticationResult], bool] | None = None,
                    fixture_only: bool = False) -> str:
        if any(item.affected_estimator_choices == "YES" for item in self.accesses):
            return "CONTAMINATED"
        proof = self.audit_authentication
        required_status = "SYNTHETIC_FIXTURE" if fixture_only else "EXTERNAL_VERIFIED"
        if (self.nominal_start != iso(H1_START) or self.nominal_end != iso(H1_END) or
                self.evidence_sha256 != digest(self.body()) or
                not self.audit_inventory_complete or not self.audit_reference or
                any(item.affected_estimator_choices == "UNKNOWN" for item in self.accesses) or
                proof is None or proof.subject_ref != self.audit_subject() or
                proof.status != required_status or verifier is None or
                not verifier(proof)):
            return "CLEANLINESS_UNVERIFIED"
        return "ESTIMATOR_RESERVED_CLEAN"


@dataclass(frozen=True)
class PreH1Freeze:
    horizon_minutes: int
    final_bundle_sha256: str
    model_sha256: str
    preprocessing_sha256: str
    calibrator_sha256: str
    baseline_hashes: tuple[str, str, str]
    code_revision: str
    configuration_sha256: str
    metric_implementation_sha256: str
    evaluation_implementation_sha256: str
    comparator_status_sha256: str
    shadow_status_sha256: str
    source_identity_sha256: str
    target_identity_sha256: str
    frozen_at: str
    freeze_sha256: str

    def body(self) -> dict[str, object]:
        body = asdict(self)
        body.pop("freeze_sha256")
        return body

    def structurally_valid(self) -> bool:
        """Local identity check only; does not authenticate timing or H1 cleanliness."""
        return (self.horizon_minutes in (60, 120) and
                _parse_utc(self.frozen_at) is not None and
                self.freeze_sha256 == digest(self.body()) and
                all(_SHA.fullmatch(value) for value in (
                    self.final_bundle_sha256, self.model_sha256, self.preprocessing_sha256,
                    self.calibrator_sha256, *self.baseline_hashes,
                    self.configuration_sha256, self.metric_implementation_sha256,
                    self.evaluation_implementation_sha256,
                    self.comparator_status_sha256, self.shadow_status_sha256,
                    self.source_identity_sha256, self.target_identity_sha256)))

    def authenticated_before_score(self, proof: AuthenticationResult | None,
                                   first_score_access_at: datetime,
                                   access_proof: AuthenticationResult | None, *,
                                   verifier: Callable[[AuthenticationResult], bool] | None,
                                   fixture_only: bool = False) -> bool:
        if (not self.structurally_valid() or proof is None or access_proof is None or
                verifier is None):
            return False
        first_access = utc(first_score_access_at)
        expected = "SYNTHETIC_FIXTURE" if fixture_only else "EXTERNAL_VERIFIED"
        return (proof.kind == "PRE_H1_FREEZE" and proof.subject_ref == self.freeze_sha256 and
                proof.status == expected and proof.verified_at is not None and
                _parse_utc(self.frozen_at) <= _parse_utc(proof.verified_at) < first_access and
                access_proof.kind == "H1_FIRST_SCORE_ACCESS" and
                access_proof.subject_ref == digest({"horizon": self.horizon_minutes,
                                                    "first_score_access_at": iso(first_access)}) and
                access_proof.status == expected and verifier(proof) and verifier(access_proof))


@dataclass(frozen=True)
class SealCodeIdentities:
    source_adapter_sha256: str
    version_precedence_sha256: str
    collector_clock_contract_sha256: str
    feature_code_sha256: str
    preprocessing_code_sha256: str
    prediction_schema_sha256: str
    expected_grid_generator_sha256: str
    terminal_record_protocol_sha256: str
    target_protocol_sha256: str
    prospective_dataset_manifest_sha256: str
    evaluation_code_sha256: str
    bootstrap_code_sha256: str
    metric_code_sha256: str
    gate_code_sha256: str
    rng_implementation: str
    rng_seed: int

    def verify(self) -> None:
        for key, value in asdict(self).items():
            if key.endswith("_sha256") and not _SHA.fullmatch(value):
                raise ValueError(f"missing exact code/contract identity: {key}")
        if self.rng_implementation != "NumPy 2.2.5 PCG64.random_raw" or self.rng_seed != 20261017:
            raise ValueError("registered evaluation RNG identity required")


@dataclass(frozen=True)
class FinalPrimaryIdentity:
    horizon_minutes: int
    fit_id: str
    bundle_sha256: str
    model_sha256: str
    preprocessing_sha256: str
    calibrator_sha256: str
    b0_sha256: str
    b1_sha256: str
    b3_sha256: str
    b2_contract_id: str
    actual_fitted_state_available_at: str | None
    availability_evidence_ref: str | None

    @classmethod
    def from_manifest(cls, manifest: FitBundleManifest, *,
                      actual_fitted_state_available_at: datetime | None,
                      availability_evidence_ref: str | None) -> FinalPrimaryIdentity:
        return cls(manifest.horizon_minutes, manifest.fit_id, manifest.bundle_sha256,
                   manifest.model_sha256, manifest.preprocessing_sha256,
                   manifest.calibrator_sha256, manifest.b0_sha256, manifest.b1_sha256,
                   manifest.b3_sha256, manifest.b2_contract_id,
                   iso(actual_fitted_state_available_at) if actual_fitted_state_available_at else None,
                   availability_evidence_ref)


@dataclass(frozen=True)
class ProspectiveSeal:
    spec_id: str
    spec_version: str
    horizon_minutes: int
    evidence_cohort_id: str
    specification: SpecificationBytes
    registry: RegistryDescriptor
    environment: EnvironmentIdentity
    code: SealCodeIdentities
    final_primary: FinalPrimaryIdentity
    comparator: ReportOnlyStatus
    shadow: ReportOnlyStatus
    source_manifest_sha256: str
    canonical_label_sha256: str
    schedule_start: str
    schedule_end: str
    outcome_seal_at: str
    final_ready_at: str
    final_ready_ref: str
    collector_ready_at: str
    collector_ready_ref: str
    registered_at: str
    ledger_anchor_sha256: str
    authentication: tuple[AuthenticationResult, ...]
    seal_sha256: str

    def body(self) -> dict[str, object]:
        body = asdict(self)
        body.pop("seal_sha256")
        return body

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    def preauthentication_subject(self) -> str:
        """All registered claims, excluding the proofs and final self-hash."""
        body = self.body()
        body.pop("authentication")
        return digest(body)

    def authentication_subjects(self) -> dict[str, str]:
        """Exact claimed facts each independent authority must authenticate."""
        return {
            "SPEC_BYTES": digest(asdict(self.specification)),
            "CLOCK": digest({"clock_contract": self.code.collector_clock_contract_sha256,
                             "collector_ready_at": self.collector_ready_at,
                             "collector_ready_ref": self.collector_ready_ref,
                             "final_ready_at": self.final_ready_at,
                             "registered_at": self.registered_at,
                             "schedule_start": self.schedule_start,
                             "horizon": self.horizon_minutes}),
            "ARTIFACT_AVAILABILITY": digest({"final_primary": asdict(self.final_primary),
                                             "comparator": asdict(self.comparator),
                                             "shadow": asdict(self.shadow),
                                             "final_ready_at": self.final_ready_at,
                                             "final_ready_ref": self.final_ready_ref}),
            "LEDGER_ANCHOR": self.preauthentication_subject(),
            "SOURCE_IDENTITY": digest({"source_manifest": self.source_manifest_sha256,
                                       "source_adapter": self.code.source_adapter_sha256,
                                       "version_precedence": self.code.version_precedence_sha256}),
            "LABEL_BYTES": digest({"canonical_label_sha256": self.canonical_label_sha256,
                                   "target_protocol": self.code.target_protocol_sha256}),
            "ENVIRONMENT_LOCK": digest(asdict(self.environment)),
        }

    @classmethod
    def from_json(cls, text: str) -> ProspectiveSeal:
        data = json.loads(text)
        for key, type_ in (("specification", SpecificationBytes), ("registry", RegistryDescriptor),
                           ("environment", EnvironmentIdentity), ("code", SealCodeIdentities),
                           ("final_primary", FinalPrimaryIdentity)):
            if key == "registry":
                d = data[key]
                d["ordered_columns"] = tuple(tuple(v) for v in d["ordered_columns"])
                for field in ("scaling_contract", "btc_mask_columns", "constant_contract"):
                    d[field] = tuple(d[field])
            data[key] = type_(**data[key])
        data["comparator"] = ReportOnlyStatus.from_json(canonical_json(data["comparator"]))
        data["shadow"] = ReportOnlyStatus.from_json(canonical_json(data["shadow"]))
        data["authentication"] = tuple(AuthenticationResult(**item) for item in data["authentication"])
        result = cls(**data)
        if result.seal_sha256 != digest(result.body()):
            raise ValueError("prospective seal content hash mismatch")
        return result

    def validate(self, *, verifier: Callable[[AuthenticationResult], bool] | None = None,
                 fixture_only: bool = False) -> tuple[str, ...]:
        """Return failure reasons; local hashes/times alone never confer authority."""
        reasons = []
        if self.seal_sha256 != digest(self.body()):
            reasons.append("SEAL_HASH_MISMATCH")
        if (self.spec_id != SPEC_ID or self.spec_version != SPEC_VERSION or
                self.specification.spec_id != SPEC_ID or self.specification.spec_version != SPEC_VERSION or
                not _SHA.fullmatch(self.specification.sha256) or self.specification.byte_size <= 0):
            reasons.append("SPECIFICATION_IDENTITY_INVALID")
        try:
            self.registry.verify()
            self.code.verify()
        except ValueError:
            reasons.append("REGISTRY_OR_CODE_IDENTITY_INVALID")
        if (self.registry.descriptor_sha256 != frozen_registry().descriptor_sha256 or
                self.registry.registry_id != FEATURE_REGISTRY or
                self.environment.identity_sha256 != digest(self.environment.body()) or
                self.environment.dependency_lock_sha256 is None or
                not self.environment.source_revision):
            reasons.append("ENVIRONMENT_OR_REGISTRY_UNVERIFIED")
        if (not self.evidence_cohort_id or self.horizon_minutes not in (60, 120) or
                self.final_primary.horizon_minutes != self.horizon_minutes or
                self.final_primary.fit_id != "FINAL" or
                self.comparator.horizon_minutes != self.horizon_minutes or
                self.shadow.horizon_minutes != self.horizon_minutes or
                self.comparator.fit_id != "FINAL" or self.shadow.fit_id != "FINAL" or
                self.comparator.role != "C1_SHALLOW_RF" or
                self.shadow.role != "SIX_MONTH_ROLLING_SHADOW" or
                self.comparator.primary_bundle_sha256 != self.final_primary.bundle_sha256 or
                self.shadow.primary_bundle_sha256 != self.final_primary.bundle_sha256):
            reasons.append("HORIZON_OR_FINAL_ARTIFACT_MISMATCH")
        for item in (self.comparator, self.shadow):
            try:
                item.verify()
            except ValueError:
                reasons.append("REPORT_ONLY_STATUS_INVALID")
        if (self.final_primary.actual_fitted_state_available_at is None or
                self.final_primary.availability_evidence_ref is None):
            reasons.append("ACTUAL_ARTIFACT_AVAILABILITY_MISSING")
        if not self.final_ready_ref or not self.collector_ready_ref or not self.final_primary.b2_contract_id:
            reasons.append("READINESS_OR_BASELINE_REFERENCE_MISSING")
        start = registered = None
        try:
            f, r = _parse_utc(self.final_ready_at), _parse_utc(self.collector_ready_at)
            start, end, outcome = (_parse_utc(self.schedule_start), _parse_utc(self.schedule_end),
                                   _parse_utc(self.outcome_seal_at))
            registered = _parse_utc(self.registered_at)
            scheduled = schedule_prospective(
                ReadinessEvidence(self.horizon_minutes, "FINAL_ARTIFACT", f, self.final_ready_ref),
                ReadinessEvidence(self.horizon_minutes, "COLLECTOR", r, self.collector_ready_ref))
            if (start, end, outcome) != (scheduled.start, scheduled.end, scheduled.outcome_seal):
                reasons.append("SCHEDULE_IDENTITY_MISMATCH")
            if registered >= start:
                reasons.append("SEAL_NOT_REGISTERED_BEFORE_P0")
            if self.final_primary.actual_fitted_state_available_at is not None and (
                    _parse_utc(self.final_primary.actual_fitted_state_available_at) > f):
                reasons.append("ARTIFACT_AVAILABLE_AFTER_F_H")
            for report_only in (self.comparator, self.shadow):
                if report_only.status == "FITTED" and report_only.artifact_available_at is not None and (
                        _parse_utc(report_only.artifact_available_at) > registered):
                    reasons.append("REPORT_ONLY_ARTIFACT_AVAILABLE_AFTER_REGISTRATION")
        except (TypeError, ValueError):
            reasons.append("INVALID_ACTUAL_TIME_EVIDENCE")
            registered = None
        if any(not _SHA.fullmatch(value) for value in (
                self.source_manifest_sha256, self.canonical_label_sha256,
                self.ledger_anchor_sha256, self.final_primary.bundle_sha256,
                self.final_primary.model_sha256, self.final_primary.preprocessing_sha256,
                self.final_primary.calibrator_sha256, self.final_primary.b0_sha256,
                self.final_primary.b1_sha256, self.final_primary.b3_sha256)):
            reasons.append("MISSING_PARENT_HASH")
        subjects = self.authentication_subjects()
        proofs = {proof.kind: proof for proof in self.authentication}
        if len(proofs) != len(self.authentication):
            reasons.append("DUPLICATE_AUTHENTICATION_KIND")
        status = "SYNTHETIC_FIXTURE" if fixture_only else "EXTERNAL_VERIFIED"
        for kind in _PROOF_KINDS:
            proof = proofs.get(kind)
            if (proof is None or proof.subject_ref != subjects[kind] or proof.status != status or
                    verifier is None or not verifier(proof)):
                reasons.append(f"{kind}_UNVERIFIED")
            elif registered is not None and _parse_utc(proof.verified_at) >= start:
                reasons.append(f"{kind}_VERIFIED_AFTER_P0")
            elif registered is not None and kind != "LEDGER_ANCHOR" and _parse_utc(proof.verified_at) > registered:
                reasons.append(f"{kind}_VERIFIED_AFTER_REGISTRATION")
        clock = proofs.get("CLOCK")
        if (clock is not None and clock.status == status and clock.subject_ref == subjects["CLOCK"] and
                clock.maximum_error_seconds is not None and isfinite(clock.maximum_error_seconds) and
                registered is not None and start is not None and
                registered + timedelta(seconds=clock.maximum_error_seconds) >= start):
            reasons.append("REGISTRATION_UTC_BOUND_OVERLAPS_P0")
        return tuple(dict.fromkeys(reasons))

    @property
    def operationally_ready_without_external_verifier(self) -> bool:
        return False


def build_prospective_seal(*, horizon_minutes: int, evidence_cohort_id: str,
                           specification: SpecificationBytes, registry: RegistryDescriptor,
                           environment: EnvironmentIdentity, code: SealCodeIdentities,
                           final_primary: FinalPrimaryIdentity,
                           comparator: ReportOnlyStatus, shadow: ReportOnlyStatus,
                           source_manifest_sha256: str, canonical_label_sha256: str,
                           schedule: ProspectiveSchedule, registered_at: datetime,
                           ledger_anchor_sha256: str,
                           authentication: tuple[AuthenticationResult, ...] = ()) -> ProspectiveSeal:
    if schedule.horizon_minutes != horizon_minutes:
        raise ValueError("one-horizon schedule required")
    provisional = ProspectiveSeal(SPEC_ID, SPEC_VERSION, horizon_minutes,
        evidence_cohort_id, specification, registry, environment, code,
        final_primary, comparator, shadow, source_manifest_sha256,
        canonical_label_sha256, iso(schedule.start), iso(schedule.end),
        iso(schedule.outcome_seal), iso(schedule.final_ready.ready_at),
        schedule.final_ready.evidence_ref, iso(schedule.collector_ready.ready_at),
        schedule.collector_ready.evidence_ref, iso(registered_at),
        ledger_anchor_sha256, authentication, "")
    return replace(provisional, seal_sha256=digest(provisional.body()))
