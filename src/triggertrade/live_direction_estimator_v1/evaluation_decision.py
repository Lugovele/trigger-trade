"""Frozen Section 20 gates and independent per-horizon decision traces."""

from __future__ import annotations

from dataclasses import dataclass
from re import fullmatch

from .calendar import H1Governance, Horizon
from .evaluation_bootstrap import (Band, BootstrapResult, simultaneous_bands,
                                   conservative_envelope)
from .evaluation_coverage import CoverageReport, prospective_coverage_gates
from .evaluation_stage import StageMetrics
from .model import CLASSES
from .source import SYMBOLS

POSITIVE_STRICT = (
    "delta_ll.B1", "delta_ll.B3", "delta_bs.B1", "delta_bs.B3",
    "delta_macro_auc.B3", *(f"auc_excess.{cls}" for cls in CLASSES),
    "delta_side_ll.B1", "delta_side_ll.B3", "side_auc_excess",
    "gamma.B1", "gamma.B3",
)
POSITIVE_NONINFERIOR = ("forced_side_benefit", "selected_incidence_benefit")
BENEFITS = ("delta_ll.B1", "delta_ll.B3", "delta_side_ll.B1", "delta_side_ll.B3")


def _lower(bands: dict[str, Band], name: str) -> float | None:
    band = bands.get(name)
    return band.lower if band and band.status == "ESTIMABLE" else None


def _upper(bands: dict[str, Band], name: str) -> float | None:
    band = bands.get(name)
    return band.upper if band and band.status == "ESTIMABLE" else None


def positive_gates(bands: dict[str, Band]) -> dict[str, bool]:
    return {name: (bound is not None and bound > 0)
            for name in POSITIVE_STRICT for bound in (_lower(bands, f"agg.{name}"),)} | {
            name: (bound is not None and bound >= 0)
            for name in POSITIVE_NONINFERIOR for bound in (_lower(bands, f"agg.{name}"),)}


def stability_gates(metrics: StageMetrics) -> dict[str, bool]:
    gates = {}
    for cls in CLASSES:
        for baseline in ("B1", "B3"):
            name = f"class_brier.{cls}.{baseline}"
            value = metrics.aggregate.get(f"delta_bs.{baseline}.{cls}")
            gates[name] = value is not None and value >= 0
    for symbol in SYMBOLS:
        values = metrics.by_symbol[symbol]
        for name in BENEFITS:
            value = values.get(name)
            gates[f"symbol.{symbol}.{name}"] = value is not None and value >= 0
        for cls in CLASSES:
            value = values.get(f"V1.auc.{cls}")
            gates[f"symbol.{symbol}.auc.{cls}"] = value is not None and value >= 0.5
    if metrics.stage in {"D", "P"}:
        for unit, values in metrics.temporal_units.items():
            for name in BENEFITS:
                value = values.get(name)
                gates[f"temporal.{unit}.{name}"] = value is not None and value >= 0
        for omitted, values in metrics.leave_one_out.items():
            for name in BENEFITS:
                value = values.get(name)
                gates[f"omit.{omitted}.{name}"] = value is not None and value > 0
    return gates


def _majority(metrics: StageMetrics, names: tuple[str, ...], *, auc_side: bool) -> bool:
    if metrics.stage not in {"D", "P"}:
        return False
    threshold = 3 if metrics.stage == "D" else 2
    if len(metrics.temporal_units) != (5 if metrics.stage == "D" else 3):
        return False
    adverse = 0
    for values in metrics.temporal_units.values():
        checks = [values.get(name) is not None and values[name] < 0 for name in names]
        if auc_side:
            auc = values.get("V1.side_auc")
            checks.append(auc is not None and auc < 0.5)
        adverse += int(all(checks))
    return adverse >= threshold


def affirmative_rejection(metrics: StageMetrics, bands: dict[str, Band], *, completed: bool
                          ) -> dict[str, bool]:
    if metrics.stage not in {"D", "P"} or not completed:
        return {"R1": False, "R2": False}
    r1 = all((upper is not None and upper < 0) for upper in (
        _upper(bands, "agg.delta_ll.B1"), _upper(bands, "agg.delta_ll.B3"))) and _majority(
            metrics, ("delta_ll.B1", "delta_ll.B3"), auc_side=False)
    r2 = all((upper is not None and upper < 0) for upper in (
        _upper(bands, "agg.side_auc_excess"), _upper(bands, "agg.delta_side_ll.B1"),
        _upper(bands, "agg.delta_side_ll.B3"))) and _majority(
            metrics, ("delta_side_ll.B1", "delta_side_ll.B3"), auc_side=True)
    return {"R1": r1, "R2": r2}


@dataclass(frozen=True)
class StageDossier:
    metrics: StageMetrics
    uncertainty: BootstrapResult

    def __post_init__(self) -> None:
        if (self.metrics.horizon_minutes != self.uncertainty.horizon_minutes or
                self.metrics.stage != self.uncertainty.stage or
                self.metrics.registered_vector != self.uncertainty.observed or
                set(self.uncertainty.by_block) != {2016, 4032} or
                any(b.replicate_count not in {0, 10000} for b in self.uncertainty.by_block.values()) or
                any(len(self.uncertainty.replicate_vectors.get(length, ())) !=
                    self.uncertainty.by_block[length].replicate_count for length in (2016, 4032)) or
                any(not fullmatch(r"[0-9a-f]{64}", self.uncertainty.draw_index_sha256.get(length, ""))
                    for length in (2016, 4032))):
            raise ValueError("registered 7d/14d bootstrap dossier required")
        for length in (2016, 4032):
            vectors = self.uncertainty.replicate_vectors[length]
            if vectors and simultaneous_bands(self.uncertainty.observed, vectors) != self.uncertainty.by_block[length]:
                raise ValueError("retained replicates disagree with simultaneous bands")
        if conservative_envelope(self.uncertainty.by_block[2016],
                                 self.uncertainty.by_block[4032]) != self.uncertainty.envelope:
            raise ValueError("retained 7d/14d bands disagree with envelope")

    @property
    def completed_valid_stage(self) -> bool:
        expected_temporal = (("F1", "F2", "F3", "F4", "F5") if self.metrics.stage == "D" else
                             ("P30_1", "P30_2", "P30_3") if self.metrics.stage == "P" else ())
        return (self.metrics.registered_grid_complete and
                self.uncertainty.evidence_mode == "REGISTERED" and
                tuple(self.metrics.temporal_units) == expected_temporal and
                tuple(self.metrics.leave_one_out) == expected_temporal and
                all(b.replicate_count == 10000 for b in self.uncertainty.by_block.values()))

    @property
    def required_family_estimable(self) -> bool:
        return (bool(self.metrics.registered_vector) and
                self.metrics.registered_vector.keys() == self.uncertainty.envelope.keys() and
                all(band.status == "ESTIMABLE" for band in self.uncertainty.envelope.values()))


@dataclass(frozen=True)
class DecisionTrace:
    horizon_minutes: int
    decision: str
    stage_observed: dict[str, dict[str, float | None]]
    stage_7d_bands: dict[str, dict[str, Band]]
    stage_14d_bands: dict[str, dict[str, Band]]
    stage_envelopes: dict[str, dict[str, Band]]
    positive_gates: dict[str, dict[str, bool]]
    stability_gates: dict[str, dict[str, bool]]
    coverage_gates: dict[str, bool]
    rejection: dict[str, dict[str, bool]]
    integrity_violations: tuple[str, ...]
    estimable_status: dict[str, dict[str, str]]
    reasons_preventing_accept: tuple[str, ...]
    affirmative_rejection_reason: str | None
    evidence_mode: str


def decide_horizon(*, horizon_minutes: int, development: StageDossier | None,
                   prospective: StageDossier | None, h1_governance: H1Governance,
                   h1: StageDossier | None, prospective_coverage: CoverageReport | None,
                   prospective_target_sealed: bool, ledger_and_artifacts_sealed: bool,
                   integrity_violations: tuple[str, ...] = (),
                   h1_exposure_disclosed: bool = True) -> DecisionTrace:
    """INVALID > affirmative REJECT > complete ACCEPT > CONTINUE_RESEARCH."""
    Horizon(horizon_minutes)
    dossiers = {"D": development, "P": prospective, "H1": h1}
    if any(d and d.metrics.horizon_minutes != horizon_minutes for d in dossiers.values()):
        raise ValueError("cross-horizon decision evidence")
    if any(d and d.metrics.stage != stage for stage, d in dossiers.items()):
        raise ValueError("stage dossier mislabeled")
    if prospective_coverage and (prospective_coverage.stage != "P" or
                                 prospective_coverage.horizon_minutes != horizon_minutes):
        raise ValueError("prospective coverage belongs to another stage/horizon")
    observed = {stage: d.metrics.registered_vector for stage, d in dossiers.items() if d}
    first = {stage: d.uncertainty.by_block[2016].bands for stage, d in dossiers.items() if d}
    second = {stage: d.uncertainty.by_block[4032].bands for stage, d in dossiers.items() if d}
    envelopes = {stage: d.uncertainty.envelope for stage, d in dossiers.items() if d}
    positives = {stage: positive_gates(d.uncertainty.envelope) for stage, d in dossiers.items()
                 if d and stage in {"D", "P"}}
    stability = {stage: stability_gates(d.metrics) for stage, d in dossiers.items()
                 if d and stage in {"D", "P"}}
    rejections = {stage: affirmative_rejection(d.metrics, d.uncertainty.envelope,
                                                completed=d.completed_valid_stage)
                  for stage, d in dossiers.items() if d and stage in {"D", "P"}}
    estimable = {stage: {key: band.status for key, band in d.uncertainty.envelope.items()}
                 for stage, d in dossiers.items() if d}
    required_estimable = prospective is not None and prospective.required_family_estimable
    coverage = (prospective_coverage_gates(prospective_coverage,
                target_sealed=prospective_target_sealed,
                required_metrics_evaluable=required_estimable,
                ledger_and_artifacts_sealed=ledger_and_artifacts_sealed)
                if prospective_coverage else {})
    violations = list(integrity_violations)
    if not h1_exposure_disclosed:
        violations.append("UNDISCLOSED_H1_EXPOSURE")
    if coverage and (not coverage["expected_key_accounting"] or
                     not coverage["one_terminal_status"]):
        violations.append("EXPECTED_KEY_INTEGRITY")
    if coverage and not coverage["asof_emitted"]:
        violations.append("FALSE_ASOF_PROVENANCE")
    reasons = []
    for stage in ("D", "P"):
        dossier = dossiers[stage]
        if not dossier or not dossier.completed_valid_stage:
            reasons.append(f"{stage}:INCOMPLETE")
        if dossier and not dossier.required_family_estimable:
            reasons.append(f"{stage}:REQUIRED_FAMILY_NOT_ESTIMABLE")
        for name, passed in positives.get(stage, {}).items():
            if not passed:
                reasons.append(f"{stage}:POSITIVE:{name}")
        for name, passed in stability.get(stage, {}).items():
            if not passed:
                reasons.append(f"{stage}:STABILITY:{name}")
    for name, passed in coverage.items():
        if not passed:
            reasons.append(f"P:COVERAGE:{name}")
    if not coverage:
        reasons.append("P:COVERAGE_MISSING")
    if h1_governance.cleanliness_status == "ESTIMATOR_RESERVED_CLEAN":
        if not h1 or not h1.completed_valid_stage or not h1.required_family_estimable:
            reasons.append("H1:CLEAN_DOSSIER_INCOMPLETE")
        else:
            band = h1.uncertainty.envelope
            adverse_ll = all((bound is not None and bound < 0) for bound in (
                _upper(band, "agg.delta_ll.B1"), _upper(band, "agg.delta_ll.B3")))
            adverse_side = all((bound is not None and bound < 0) for bound in (
                _upper(band, "agg.side_auc_excess"), _upper(band, "agg.delta_side_ll.B1"),
                _upper(band, "agg.delta_side_ll.B3")))
            if adverse_ll or adverse_side:
                reasons.append("H1:ROBUST_ADVERSE_AGGREGATE")
    rejection_reason = next((f"{stage}:{rule}" for stage in ("D", "P")
                             for rule in ("R1", "R2") if rejections.get(stage, {}).get(rule)), None)
    if violations:
        verdict = "INVALID"
    elif rejection_reason:
        verdict = "REJECT"
    elif not reasons:
        verdict = "ACCEPT"
    else:
        verdict = "CONTINUE_RESEARCH"
    return DecisionTrace(horizon_minutes, verdict, observed, first, second, envelopes,
                         positives, stability, coverage, rejections, tuple(violations),
                         estimable, tuple(reasons), rejection_reason,
                         "REGISTERED" if all(d and d.uncertainty.evidence_mode == "REGISTERED"
                                             for d in (development, prospective)) else "SYNTHETIC_OR_INCOMPLETE")
