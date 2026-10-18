"""Section 22 artifact inventories; records only, with no fitting or scoring path."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import re
from typing import Callable, Mapping

from . import FEATURE_REGISTRY, SPEC_ID, SPEC_VERSION
from .calendar import FIT_DEFINITIONS
from .manifests import RowManifest, canonical_json, digest
from .model import CLASSES
from .registry_identity import EnvironmentIdentity, RegistryDescriptor, frozen_registry
from .source import SYMBOLS

_SHA = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class ArtifactField:
    """A value and its evidence state. Missing facts are never imputed."""

    value: object | None
    status: str  # AVAILABLE, NOT_AVAILABLE, UNVERIFIED, SYNTHETIC_FIXTURE
    evidence_ref: str | None = None

    def verify(self) -> None:
        if self.status not in {"AVAILABLE", "NOT_AVAILABLE", "UNVERIFIED", "SYNTHETIC_FIXTURE"}:
            raise ValueError("invalid artifact evidence state")
        if self.status == "NOT_AVAILABLE" and self.value is not None:
            raise ValueError("missing field cannot carry a value")
        if self.status == "AVAILABLE" and (self.value is None or not self.evidence_ref):
            raise ValueError("available field requires value and evidence reference")


FIT_FIELD_NAMES = (
    "canonical_release_id", "canonical_configuration_sha256", "canonical_calculation_sha256",
    "canonical_source_sha256", "actual_label_file_hashes", "nominal_training_bounds",
    "effective_training_bounds", "nominal_calibration_bounds", "effective_calibration_bounds",
    "purge_embargo_inequalities", "actual_fit_at", "source_evidence_mode",
    "preprocessing_id", "preprocessing_means_scales", "preprocessing_scaling_populations",
    "preprocessing_constant_flags",
    "feature_domain_checks", "lambda_value", "objective_normalization", "penalty_mask",
    "q_basis", "state_coefficients", "symbol_intercepts",
    "indicator_equivalent_coefficients", "solver_configuration", "iteration_count",
    "terminal_objective", "gradient_certificate", "convergence_state",
    "numerical_reduction_threading",
    "calibration_family_bounds_temperature", "calibration_membership", "calibration_loss_status",
    "calibration_completion_certificate", "b0_state_counts_priors",
    "b1_state_counts_sign_bins", "b3_state_counts_sign_bins", "b2_contract",
    "comparator_configuration_status", "shadow_configuration_status",
    "software_revision", "rng_identity",
    "actual_artifact_created_at", "actual_sealed_at", "parent_hashes",
)
FINAL_FIELD_NAMES = (
    "evidence_cohort_id", "F_H", "R_H", "P0_H", "P1_H", "outcome_seal_at",
    "final_readiness_evidence", "collector_readiness_evidence", "registered_at",
)


@dataclass(frozen=True)
class FitContractManifest:
    spec_id: str
    spec_version: str
    role: str
    horizon_minutes: int
    fit_id: str
    symbol_order: tuple[str, ...]
    class_order: tuple[str, ...]
    registry: RegistryDescriptor
    environment: EnvironmentIdentity
    base_manifest_sha256: str
    calibration_manifest_sha256: str
    base_selected_keys: tuple[tuple[str, str], ...]
    calibration_selected_keys: tuple[tuple[str, str], ...]
    base_counts_by_symbol: tuple[int, ...]
    base_counts_by_class: tuple[int, ...]
    calibration_counts_by_symbol: tuple[int, ...]
    calibration_counts_by_class: tuple[int, ...]
    base_exclusions_by_reason: tuple[tuple[str, int], ...]
    calibration_exclusions_by_reason: tuple[tuple[str, int], ...]
    fields: tuple[tuple[str, ArtifactField], ...]
    contract_sha256: str

    def body(self) -> dict[str, object]:
        result = asdict(self)
        result.pop("contract_sha256")
        return result

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    def validate(self, *, require_prospective_ready: bool = False,
                 external_verifier: Callable[[str, ArtifactField], bool] | None = None
                 ) -> tuple[str, ...]:
        errors = []
        if (self.spec_id != SPEC_ID or self.spec_version != SPEC_VERSION or
                self.horizon_minutes not in (60, 120) or self.fit_id not in FIT_DEFINITIONS or
                self.role not in {"PRIMARY", "SHADOW"} or self.symbol_order != SYMBOLS or
                self.class_order != CLASSES or self.registry.registry_id != FEATURE_REGISTRY):
            errors.append("FIT_IDENTITY_INVALID")
        if self.contract_sha256 != digest(self.body()):
            errors.append("FIT_CONTRACT_HASH_MISMATCH")
        try:
            self.registry.verify()
        except ValueError:
            errors.append("FIT_REGISTRY_INVALID")
        if self.registry.descriptor_sha256 != frozen_registry().descriptor_sha256:
            errors.append("FIT_REGISTRY_NOT_FROZEN_V1")
        if (self.environment.identity_sha256 != digest(self.environment.body()) or
                self.environment.dependency_lock_status not in {"NOT_AVAILABLE", "DECLARED_UNVERIFIED"} or
                (self.environment.dependency_lock_sha256 is None) !=
                (self.environment.dependency_lock_ref is None) or
                (self.environment.dependency_lock_sha256 is not None and
                 not _SHA.fullmatch(self.environment.dependency_lock_sha256))):
            errors.append("FIT_ENVIRONMENT_IDENTITY_INVALID")
        names = tuple(name for name, _ in self.fields)
        required = FIT_FIELD_NAMES + (FINAL_FIELD_NAMES if self.fit_id == "FINAL" else ())
        if names != required:
            errors.append("FIT_FIELD_SCHEMA_INCOMPLETE")
        for _, field in self.fields:
            try:
                field.verify()
            except ValueError:
                errors.append("FIT_FIELD_EVIDENCE_INVALID")
        if require_prospective_ready and (self.fit_id != "FINAL" or any(
                field.status != "AVAILABLE" for _, field in self.fields)):
            errors.append("PROSPECTIVE_FIT_EVIDENCE_INCOMPLETE")
        if require_prospective_ready and (external_verifier is None or any(
                not external_verifier(name, field) for name, field in self.fields)):
            errors.append("PROSPECTIVE_FIT_EVIDENCE_UNAUTHENTICATED")
        if self.environment.dependency_lock_sha256 is None:
            errors.append("DEPENDENCY_LOCK_UNVERIFIED") if require_prospective_ready else None
        return tuple(dict.fromkeys(errors))


def build_fit_contract(*, role: str, base: RowManifest, calibration: RowManifest,
                       registry: RegistryDescriptor, environment: EnvironmentIdentity,
                       fields: Mapping[str, ArtifactField]) -> FitContractManifest:
    if (base.segment_type != "BASE" or calibration.segment_type != "CALIBRATION" or
            base.horizon_minutes != calibration.horizon_minutes or
            base.fit_id != calibration.fit_id):
        raise ValueError("base/calibration must share one fit and horizon")
    required = FIT_FIELD_NAMES + (FINAL_FIELD_NAMES if base.fit_id == "FINAL" else ())
    if set(fields) != set(required):
        raise ValueError("exact fit contract fields required")
    provisional = FitContractManifest(SPEC_ID, SPEC_VERSION, role, base.horizon_minutes,
        base.fit_id, SYMBOLS, CLASSES, registry, environment,
        base.manifest_sha256, calibration.manifest_sha256,
        tuple(item.key for item in base.selected), tuple(item.key for item in calibration.selected),
        base.counts_by_symbol, base.counts_by_class,
        calibration.counts_by_symbol, calibration.counts_by_class,
        base.exclusions_by_reason, calibration.exclusions_by_reason,
        tuple((name, fields[name]) for name in required), "")
    result = replace(provisional, contract_sha256=digest(provisional.body()))
    if result.validate():
        raise ValueError("invalid fit contract: " + ",".join(result.validate()))
    return result


DOSSIER_REFERENCES = (
    "complete_expected_key_ledger", "D_population_coverage", "H1_population_coverage",
    "P_H_population_coverage", "calibrated_scores", "raw_scores",
    "baseline_diagnostics", "comparator_diagnostics", "shadow_diagnostics",
    "seven_day_bootstrap", "fourteen_day_bootstrap", "registered_decision_vector",
    "undefined_statistics", "simultaneous_bands", "gate_statuses_reasons",
    "bootstrap_draw_manifest", "rng_state", "replicate_statistic_arrays",
    "phase8_decision_trace",
)


@dataclass(frozen=True)
class EvaluationDossierManifest:
    spec_id: str
    spec_version: str
    horizon_minutes: int
    fit_contract_sha256: str
    folds: tuple[tuple[str, str], ...]
    symbols: tuple[str, ...]
    classes: tuple[str, ...]
    references: tuple[tuple[str, ArtifactField], ...]
    verdict: str
    replicate_count: int
    fixture_only: bool
    dossier_sha256: str

    def body(self) -> dict[str, object]:
        result = asdict(self)
        result.pop("dossier_sha256")
        return result

    def validate(self, *, external_verifier: Callable[[str, ArtifactField], bool] | None = None
                 ) -> tuple[str, ...]:
        errors = []
        if (self.spec_id != SPEC_ID or self.spec_version != SPEC_VERSION or
                self.horizon_minutes not in (60, 120) or
                tuple(name for name, _ in self.folds) != ("F1", "F2", "F3", "F4", "F5") or
                self.symbols != SYMBOLS or self.classes != CLASSES or
                tuple(name for name, _ in self.references) != DOSSIER_REFERENCES):
            errors.append("DOSSIER_SCHEMA_INVALID")
        if not self.fixture_only and self.replicate_count != 10000:
            errors.append("BOOTSTRAP_REPLICATE_COUNT_INVALID")
        if self.verdict in {"ACCEPT", "REJECT"} and (
                self.fixture_only or any(field.status != "AVAILABLE" for _, field in self.references) or
                external_verifier is None or any(
                    not external_verifier(name, field) for name, field in self.references)):
            errors.append("CONFIRMATORY_VERDICT_WITHOUT_COMPLETE_EVIDENCE")
        if self.dossier_sha256 != digest(self.body()):
            errors.append("DOSSIER_HASH_MISMATCH")
        if self.verdict not in {"NOT_ASSESSED", "ACCEPT", "REJECT", "CONTINUE_RESEARCH", "INVALID"}:
            errors.append("DOSSIER_VERDICT_INVALID")
        for _, field in self.references:
            try:
                field.verify()
            except ValueError:
                errors.append("DOSSIER_REFERENCE_INVALID")
        return tuple(dict.fromkeys(errors))


def build_dossier(*, horizon_minutes: int, fit_contract_sha256: str,
                  fold_hashes: Mapping[str, str], references: Mapping[str, ArtifactField],
                  verdict: str = "NOT_ASSESSED", replicate_count: int = 0,
                  fixture_only: bool = False,
                  external_verifier: Callable[[str, ArtifactField], bool] | None = None
                  ) -> EvaluationDossierManifest:
    if set(fold_hashes) != {"F1", "F2", "F3", "F4", "F5"} or set(references) != set(DOSSIER_REFERENCES):
        raise ValueError("complete five-fold and dossier reference inventory required")
    provisional = EvaluationDossierManifest(SPEC_ID, SPEC_VERSION, horizon_minutes,
        fit_contract_sha256, tuple((name, fold_hashes[name]) for name in
                                  ("F1", "F2", "F3", "F4", "F5")),
        SYMBOLS, CLASSES, tuple((name, references[name]) for name in DOSSIER_REFERENCES),
        verdict, replicate_count, fixture_only, "")
    result = replace(provisional, dossier_sha256=digest(provisional.body()))
    errors = result.validate(external_verifier=external_verifier)
    if errors:
        raise ValueError("invalid evaluation dossier: " + ",".join(errors))
    return result
