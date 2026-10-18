"""Frozen LDE V1 evaluation arithmetic; consumes predictions and later truth only.

No source, feature, fit, calibration, or target-generation code is imported here.
Undefined required denominators remain None throughout aggregation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import exp, floor, isfinite, log, log1p
from typing import Iterable

from .calendar import Horizon, origin, utc
from .model import CLASSES
from .source import SYMBOLS

L, S, N = CLASSES
CLASS_INDEX = {name: i for i, name in enumerate(CLASSES)}
HARD_PRIORITY = (2, 0, 1)  # N, L, S on exact maximizing ties.


def hard_class(probabilities: tuple[float, float, float]) -> str:
    maximum = max(probabilities)
    return CLASSES[next(i for i in HARD_PRIORITY if probabilities[i] == maximum)]


@dataclass(frozen=True)
class ProbabilityState:
    probabilities: tuple[float, float, float]
    log_probabilities: tuple[float, float, float]
    hard_class: str
    ranking_scores: tuple[float, float, float]

    def __post_init__(self) -> None:
        if (len(self.probabilities) != 3 or len(self.log_probabilities) != 3 or
                any(not isfinite(v) or v < 0 or v > 1 for v in self.probabilities) or
                any(not isfinite(v) or v > 1e-12 for v in self.log_probabilities) or
                abs(sum(self.probabilities) - 1) > 1e-12 or
                len(self.ranking_scores) != 3 or
                any(not isfinite(v) for v in self.ranking_scores) or
                self.hard_class != hard_class(self.ranking_scores)):
            raise ValueError("invalid retained probability state")
        for p, lp in zip(self.probabilities, self.log_probabilities):
            if abs(exp(lp) - p) > 1e-12:
                raise ValueError("probability/log-probability mismatch")
        # Retained ranking scores are unrounded logits; a common additive shift is allowed.
        score_max = max(self.ranking_scores)
        log_max = max(self.log_probabilities)
        if any(abs((score - score_max) - (lp - log_max)) >
               1e-12 * max(1.0, abs(lp - log_max))
               for score, lp in zip(self.ranking_scores, self.log_probabilities)):
            raise ValueError("ranking logits disagree with retained log probabilities")
        for i in range(3):
            for j in range(i + 1, 3):
                log_order = (self.log_probabilities[i] > self.log_probabilities[j]) - (
                    self.log_probabilities[i] < self.log_probabilities[j])
                score_order = (self.ranking_scores[i] > self.ranking_scores[j]) - (
                    self.ranking_scores[i] < self.ranking_scores[j])
                # Log-probability normalization may round a strict logit order
                # to a tie, but may never reverse or manufacture a strict order.
                if log_order and score_order != log_order:
                    raise ValueError("ranking logits reverse retained log-probability order")

    @classmethod
    def from_probabilities(cls, values: Iterable[float]) -> ProbabilityState:
        p = tuple(float(v) for v in values)
        if len(p) != 3 or any(v <= 0 for v in p):
            raise ValueError("strictly positive baseline probabilities required")
        lp = tuple(log(v) for v in p)
        return cls(p, lp, hard_class(lp), lp)


@dataclass(frozen=True)
class AsOfEvidence:
    """References to an externally verified Phase 2–5 source and fit-state seal."""

    source_snapshot_id: str
    receipt_evidence_ref: str
    finalization_evidence_ref: str
    clock_attestation_ref: str
    fitted_state_id: str
    source_available_at: datetime
    fitted_state_available_at: datetime
    verification_manifest_sha256: str

    def __post_init__(self) -> None:
        utc(self.source_available_at)
        utc(self.fitted_state_available_at)
        if not all((self.source_snapshot_id, self.receipt_evidence_ref,
                    self.finalization_evidence_ref, self.clock_attestation_ref,
                    self.fitted_state_id,
                    self.verification_manifest_sha256)):
            raise ValueError("complete external as-of evidence references required")

    def admissible_at(self, t: datetime) -> bool:
        return self.source_available_at <= t and self.fitted_state_available_at <= t


@dataclass(frozen=True)
class SealedPrediction:
    prediction_origin: datetime
    physical_symbol: str
    horizon_minutes: int
    phase_id: str
    bundle_sha256: str | None
    calibrated: ProbabilityState | None
    raw: ProbabilityState | None
    b0_hard_class: str | None
    b1: ProbabilityState | None
    b2_hard_class: str | None
    b3: ProbabilityState | None
    emitted: bool
    on_time: bool | None
    provenance_mode: str | None
    unavailable_reasons: tuple[str, ...] = ()
    emission_delay_seconds: float | None = None
    late_receipt_age_seconds: float | None = None
    max_source_available_at: datetime | None = None
    source_version_conflict: bool = False
    vintage_discrepancy: bool = False
    feature_status: str = "AVAILABLE"
    asof_evidence: AsOfEvidence | None = None
    record_kind: str = "HISTORICAL_SIMULATION"

    def __post_init__(self) -> None:
        origin(self.prediction_origin)
        Horizon(self.horizon_minutes)
        if self.physical_symbol not in SYMBOLS or not self.phase_id:
            raise ValueError("invalid prediction key")
        if self.emitted != (self.calibrated is not None) or (self.on_time and not self.emitted):
            raise ValueError("emitted/on-time state inconsistent with calibrated output")
        if self.record_kind == "HISTORICAL_SIMULATION":
            if self.on_time is not None or self.provenance_mode not in {None, "EVENT_TIME_ONLY"}:
                raise ValueError("historical simulation has no live deadline or ASOF claim")
        elif self.record_kind == "PROSPECTIVE_FORECAST":
            if self.on_time is None or (self.emitted and not self.on_time):
                raise ValueError("prospective late diagnostic cannot be emitted forecast")
        else:
            raise ValueError("unsupported record kind")
        if self.emitted and (self.raw is None or not self.bundle_sha256):
            raise ValueError("emitted prediction needs sealed raw and calibrated states")
        if self.provenance_mode not in {None, "EVENT_TIME_ONLY", "ASOF_VERIFIED"}:
            raise ValueError("invalid provenance mode")
        if self.feature_status not in {"AVAILABLE", "UNAVAILABLE"}:
            raise ValueError("invalid feature status")
        if self.emitted and self.feature_status != "AVAILABLE":
            raise ValueError("emitted prediction requires available features")
        if self.provenance_mode == "ASOF_VERIFIED" and self.emitted and (
                self.asof_evidence is None or not self.asof_evidence.admissible_at(self.prediction_origin)):
            raise ValueError("ASOF_VERIFIED output lacks by-T source/fitted-state evidence")

    @property
    def terminal_status(self) -> str:
        return "AVAILABLE" if self.emitted else "UNAVAILABLE"


@dataclass(frozen=True)
class JoinedTruth:
    prediction_origin: datetime
    physical_symbol: str
    horizon_minutes: int
    canonical_target_key: str
    canonical_release_id: str
    outcome_source_vintage_id: str
    target_status: str
    canonical_class: str | None
    unavailable_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        origin(self.prediction_origin)
        Horizon(self.horizon_minutes)
        if (self.physical_symbol not in SYMBOLS or not self.canonical_target_key or
                not self.canonical_release_id or not self.outcome_source_vintage_id):
            raise ValueError("immutable canonical target identity required")
        if self.target_status == "VALID":
            if self.canonical_class not in CLASSES:
                raise ValueError("valid target requires canonical class")
        elif self.canonical_class is not None:
            raise ValueError("unavailable target must not carry class")


@dataclass(frozen=True)
class EvaluationRecord:
    prediction: SealedPrediction
    truth: JoinedTruth | None = None
    frozen_causal_volatility_stratum: str | None = None

    def __post_init__(self) -> None:
        if self.truth is not None and (
                self.truth.prediction_origin != self.prediction.prediction_origin or
                self.truth.physical_symbol != self.prediction.physical_symbol or
                self.truth.horizon_minutes != self.prediction.horizon_minutes):
            raise ValueError("truth key differs from sealed prediction key")

    @property
    def matched(self) -> bool:
        p = self.prediction
        return (self.truth is not None and self.truth.target_status == "VALID" and
                p.calibrated is not None and p.raw is not None and p.b0_hard_class is not None and
                p.b1 is not None and p.b2_hard_class is not None and p.b3 is not None)


def _mean(values: Iterable[float | None]) -> float | None:
    values = tuple(values)
    if not values or any(value is None for value in values):
        return None
    return sum(values) / len(values)


def side_values(state: ProbabilityState, truth: str) -> tuple[float, float, str, float]:
    """Stable side log loss, binary Brier, forced side and ranking log odds."""
    if truth not in (L, S):
        raise ValueError("directional truth required")
    ll, ls = state.log_probabilities[:2]
    high = max(ll, ls)
    centered_denominator = log1p(exp(min(ll, ls) - high))
    q = exp((ll - high) - centered_denominator)
    # Keep log(2) when a huge common negative log-probability shift would
    # round it away in high + log(2).
    selected = ll if truth == L else ls
    return ((high - selected) + centered_denominator,
            (q - (truth == L)) ** 2 + ((1 - q) - (truth == S)) ** 2,
            L if ll >= ls else S, ll - ls)


def exact_auc(scores: Iterable[tuple[float, bool]]) -> float | None:
    ordered = sorted(scores, key=lambda pair: pair[0])
    if any(not isfinite(score) for score, _ in ordered):
        raise ValueError("finite retained log scores required")
    positives = sum(label for _, label in ordered)
    negatives = len(ordered) - positives
    if positives == 0 or negatives == 0:
        return None
    wins = 0.0
    lower_negatives = 0
    at = 0
    while at < len(ordered):
        end = at + 1
        while end < len(ordered) and ordered[end][0] == ordered[at][0]:
            end += 1
        group_positive = sum(label for _, label in ordered[at:end])
        group_negative = end - at - group_positive
        wins += group_positive * (lower_negatives + 0.5 * group_negative)
        lower_negatives += group_negative
        at = end
    return wins / (positives * negatives)


def average_precision(scores: Iterable[tuple[float, bool]]) -> float | None:
    ordered = sorted(scores, key=lambda pair: pair[0], reverse=True)
    if any(not isfinite(score) for score, _ in ordered):
        raise ValueError("finite retained log scores required")
    positives = sum(label for _, label in ordered)
    if not positives:
        return None
    area = 0.0
    seen = found = at = 0
    while at < len(ordered):
        end = at + 1
        while end < len(ordered) and ordered[end][0] == ordered[at][0]:
            end += 1
        newly_found = sum(label for _, label in ordered[at:end])
        seen += end - at
        found += newly_found
        area += (newly_found / positives) * (found / seen)
        at = end
    return area


def fixed_bin(value: float) -> int:
    if not isfinite(value) or not 0 <= value <= 1:
        raise ValueError("finite probability in [0,1] required")
    return min(9, floor(value * 10))


@dataclass(frozen=True)
class CalibrationBin:
    count: int
    mean_probability: float | None
    observed_frequency: float | None
    signed_residual: float | None


@dataclass(frozen=True)
class CellMetrics:
    count: int
    values: dict[str, float | None]
    confusion: dict[str, tuple[tuple[int, int, int], ...]]
    bins: dict[str, tuple[CalibrationBin, ...]]
    confidence_bins: tuple[CalibrationBin, ...]
    selected_direction_count: int
    selected_direction_fraction: float | None
    selected_direction_error_benefit: float | None


def _bins(rows: list[EvaluationRecord], *, class_index: int | None) -> tuple[CalibrationBin, ...]:
    groups: list[list[tuple[float, float]]] = [[] for _ in range(10)]
    for row in rows:
        state = row.prediction.calibrated
        assert state is not None and row.truth is not None
        if class_index is None:
            probability = max(state.probabilities)
            observed = float(state.hard_class == row.truth.canonical_class)
        else:
            probability = state.probabilities[class_index]
            observed = float(row.truth.canonical_class == CLASSES[class_index])
        groups[fixed_bin(probability)].append((probability, observed))
    output = []
    for group in groups:
        if not group:
            output.append(CalibrationBin(0, None, None, None))
        else:
            mp = sum(p for p, _ in group) / len(group)
            my = sum(y for _, y in group) / len(group)
            output.append(CalibrationBin(len(group), mp, my, mp - my))
    return tuple(output)


def _hard(rows: list[EvaluationRecord], method: str) -> tuple[tuple[tuple[int, int, int], ...], dict[str, float | None]]:
    counts = [[0] * 3 for _ in range(3)]
    for row in rows:
        state = row.prediction
        prediction = (state.calibrated.hard_class if method == "V1" else
                      getattr(state, method.lower()).hard_class if method in {"B1", "B3"} else
                      getattr(state, method.lower() + "_hard_class"))
        if prediction is not None:
            counts[CLASS_INDEX[row.truth.canonical_class]][CLASS_INDEX[prediction]] += 1
    values: dict[str, float | None] = {}
    for ci, cls in enumerate(CLASSES):
        tp = counts[ci][ci]
        predicted = sum(counts[yi][ci] for yi in range(3))
        actual = sum(counts[ci])
        precision = tp / predicted if predicted else None
        recall = tp / actual if actual else None
        f1 = 2 * tp / (predicted + actual) if predicted + actual else None
        values[f"{method}.precision.{cls}"] = precision
        values[f"{method}.recall.{cls}"] = recall
        values[f"{method}.f1.{cls}"] = f1
        values[f"{method}.share.{cls}"] = predicted / len(rows) if rows else None
    values[f"{method}.balanced_accuracy"] = _mean(values[f"{method}.recall.{c}"] for c in CLASSES)
    values[f"{method}.accuracy"] = sum(counts[i][i] for i in range(3)) / len(rows) if rows else None
    return tuple(tuple(group) for group in counts), values


def cell_metrics(records: Iterable[EvaluationRecord]) -> CellMetrics:
    rows = [row for row in records if row.matched]
    values: dict[str, float | None] = {}
    confusion = {}
    if not rows:
        return CellMetrics(0, values, confusion, {}, (), 0, None, None)
    for method in ("V1", "B0", "B1", "B2", "B3"):
        matrix, hard_values = _hard(rows, method)
        confusion[method] = matrix
        values.update(hard_values)
    for method in ("V1", "RAW", "B1", "B3"):
        states = [row.prediction.calibrated if method == "V1" else
                  row.prediction.raw if method == "RAW" else getattr(row.prediction, method.lower())
                  for row in rows]
        losses = [-state.log_probabilities[CLASS_INDEX[row.truth.canonical_class]]
                  for row, state in zip(rows, states)]
        values[f"{method}.ll"] = _mean(losses)
        components = [[(state.probabilities[ci] - (row.truth.canonical_class == cls)) ** 2
                       for ci, cls in enumerate(CLASSES)] for row, state in zip(rows, states)]
        for ci, cls in enumerate(CLASSES):
            values[f"{method}.bs.{cls}"] = _mean(component[ci] for component in components)
        values[f"{method}.bs"] = _mean(sum(component) for component in components)
        if method != "RAW":
            for ci, cls in enumerate(CLASSES):
                scores = [(state.log_probabilities[ci], row.truth.canonical_class == cls)
                          for row, state in zip(rows, states)]
                values[f"{method}.auc.{cls}"] = exact_auc(scores)
                values[f"{method}.ap.{cls}"] = average_precision(scores)
            values[f"{method}.macro_auc"] = _mean(values[f"{method}.auc.{cls}"] for cls in CLASSES)
            values[f"{method}.macro_ap"] = _mean(values[f"{method}.ap.{cls}"] for cls in CLASSES)
    directional = [row for row in rows if row.truth.canonical_class in (L, S)]
    for method in ("V1", "B1", "B3"):
        states = [row.prediction.calibrated if method == "V1" else getattr(row.prediction, method.lower())
                  for row in directional]
        pieces = [side_values(state, row.truth.canonical_class) for state, row in zip(states, directional)]
        values[f"{method}.side_ll"] = _mean(piece[0] for piece in pieces)
        values[f"{method}.side_bs"] = _mean(piece[1] for piece in pieces)
        values[f"{method}.side_error"] = _mean(float(piece[2] != row.truth.canonical_class)
                                                 for piece, row in zip(pieces, directional))
        values[f"{method}.side_auc"] = exact_auc((piece[3], row.truth.canonical_class == L)
                                                       for piece, row in zip(pieces, directional))
    for baseline in ("B1", "B3"):
        for metric in ("ll", "bs", "side_ll"):
            a, b = values[f"{baseline}.{metric}"], values[f"V1.{metric}"]
            values[f"delta_{metric}.{baseline}"] = a - b if a is not None and b is not None else None
        for cls in CLASSES:
            values[f"delta_bs.{baseline}.{cls}"] = (
                values[f"{baseline}.bs.{cls}"] - values[f"V1.bs.{cls}"])
        for metric in ("ll", "bs"):
            denominator = values[f"{baseline}.{metric}"]
            values[f"relative_{metric}.{baseline}"] = (
                1 - values[f"V1.{metric}"] / denominator if denominator and denominator > 0 else None)
    values["delta_macro_auc.B3"] = (values["V1.macro_auc"] - values["B3.macro_auc"]
                                     if values["V1.macro_auc"] is not None and
                                     values["B3.macro_auc"] is not None else None)
    for cls in CLASSES:
        values[f"prevalence.{cls}"] = sum(row.truth.canonical_class == cls for row in rows) / len(rows)
        values[f"auc_excess.{cls}"] = (values[f"V1.auc.{cls}"] - 0.5
                                        if values[f"V1.auc.{cls}"] is not None else None)
        ci = CLASS_INDEX[cls]
        values[f"frequency_residual.{cls}"] = _mean(
            row.prediction.calibrated.probabilities[ci] - (row.truth.canonical_class == cls)
            for row in rows)
    values["side_auc_excess"] = (values["V1.side_auc"] - 0.5
                                  if values["V1.side_auc"] is not None else None)
    values["forced_side_benefit"] = (values["B3.side_error"] - values["V1.side_error"]
                                      if directional else None)
    matrix = confusion["V1"]
    values["L_to_S"] = float(matrix[0][1])
    values["S_to_L"] = float(matrix[1][0])
    values["L_denominator"] = float(sum(matrix[0]))
    values["S_denominator"] = float(sum(matrix[1]))
    values["opposite_mass.L"] = _mean(row.prediction.calibrated.probabilities[1]
                                          for row in directional if row.truth.canonical_class == L)
    values["opposite_mass.S"] = _mean(row.prediction.calibrated.probabilities[0]
                                          for row in directional if row.truth.canonical_class == S)
    selected = [row for row in directional if row.prediction.calibrated.hard_class in (L, S)]
    selected_benefits = [float(side_values(row.prediction.b3, row.truth.canonical_class)[2]
                               != row.truth.canonical_class) -
                         float(row.prediction.calibrated.hard_class != row.truth.canonical_class)
                         for row in selected]
    values["selected_error.V1"] = _mean(
        float(row.prediction.calibrated.hard_class != row.truth.canonical_class) for row in selected)
    values["selected_error.B3"] = _mean(
        float(side_values(row.prediction.b3, row.truth.canonical_class)[2] != row.truth.canonical_class)
        for row in selected)
    values["selected_incidence_benefit"] = (sum(selected_benefits) / len(directional)
                                               if directional else None)
    values["selected_conditional_benefit"] = _mean(selected_benefits) if selected else None
    bins = {cls: _bins(rows, class_index=ci) for ci, cls in enumerate(CLASSES)}
    r = 0.0
    for cls in CLASSES:
        values[f"ece.{cls}"] = sum(b.count / len(rows) * abs(b.signed_residual)
                                     for b in bins[cls] if b.count)
        r += sum(b.count / len(rows) * b.signed_residual ** 2 for b in bins[cls] if b.count)
    values["R"] = r
    for baseline in ("B1", "B3"):
        values[f"gamma.{baseline}"] = values[f"delta_bs.{baseline}"] - r
    confidence_bins = _bins(rows, class_index=None)
    values["confidence_ece"] = sum(b.count / len(rows) * abs(b.signed_residual)
                                    for b in confidence_bins if b.count)
    return CellMetrics(len(rows), values, confusion, bins, confidence_bins,
                       len(selected), len(selected) / len(directional) if directional else None,
                       _mean(selected_benefits) if selected else None)
