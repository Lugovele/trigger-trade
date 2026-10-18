"""Section 19 report-only diagnostics over frozen rows and fitted states."""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from math import ceil, exp, isfinite, sqrt
from typing import Iterable

from .calendar import FIVE_MINUTES, Horizon, ProspectiveSchedule, iso, origin, utc
from .evaluation_coverage import coverage_report
from .evaluation_metrics import EvaluationRecord, SealedPrediction, cell_metrics, _mean
from .evaluation_stage import StageEvidence, StageMetrics, compute_stage
from .features import RawFeatureRow
from .manifests import RowManifest, RowMetadata, digest
from .model import CLASSES
from .orchestration import FitBundle, _assert_manifest
from .preprocessing import ProcessedFeatureRow, transform
from .features import GROUPS
from .source import SYMBOLS

# One-based raw, pre-standardization registry coordinates.
REFLECTION_NEGATE = (1, 2, 3, 4, 5, 6, 9, 10, 12, 14, 24, 25, 28, 29)
REFLECTION_SWAPS = ((16, 17), (18, 19))


@dataclass(frozen=True)
class ReportingWindow:
    window_id: str
    start: datetime
    end: datetime


def prospective_windows(schedule: ProspectiveSchedule) -> tuple[tuple[ReportingWindow, ...],
                                                                 tuple[ReportingWindow, ...]]:
    start, end = schedule.start, schedule.end
    if end != start + timedelta(days=90):
        raise ValueError("own-horizon prospective schedule must last 90 days")
    thirty = tuple(ReportingWindow(f"P30_{i+1}", start + timedelta(days=30*i),
                                     start + timedelta(days=30*(i+1))) for i in range(3))
    operations = tuple(ReportingWindow(f"P_W{i+1:02d}", start + timedelta(days=7*i),
                                        start + timedelta(days=7*(i+1))) for i in range(12))
    return thirty, operations + (ReportingWindow("P_W13", start + timedelta(days=84), end),)


def _equal_symbol_metrics(rows: tuple[EvaluationRecord, ...]) -> dict[str, float | None]:
    cells = [cell_metrics(row for row in rows if row.prediction.physical_symbol == symbol)
             for symbol in SYMBOLS]
    names = set().union(*(cell.values.keys() for cell in cells))
    return {name: _mean(cell.values.get(name) for cell in cells) for name in names}


@dataclass(frozen=True)
class StabilityWindowReport:
    window: ReportingWindow
    metrics: dict[str, float | None]
    coverage_by_symbol: dict[str, tuple[int, int, int]]  # scheduled, emitted, matched


@dataclass(frozen=True)
class SymbolTimeReport:
    horizon_minutes: int
    stage: str
    metrics: StageMetrics
    coverage_by_symbol: dict[str, dict[str, object]]
    thirty_day: tuple[StabilityWindowReport, ...]
    operational: tuple[StabilityWindowReport, ...]
    leave_one_period_out: dict[str, dict[str, float | None]]


def symbol_time_report(stage: StageEvidence) -> SymbolTimeReport:
    """Reuses Section 17 arithmetic; diagnostic partitions never refit anything."""
    metrics = compute_stage(stage)
    coverage = coverage_report(stage)
    thirty: tuple[StabilityWindowReport, ...] = ()
    operations: tuple[StabilityWindowReport, ...] = ()
    if stage.stage == "P":
        if stage.prospective_schedule is None or stage.prospective_schedule.horizon_minutes != stage.horizon_minutes:
            raise ValueError("P diagnostics require own-horizon registered start")
        phase = stage.phases[0]
        def report(window: ReportingWindow) -> StabilityWindowReport:
            rows = tuple(row for row in phase.records
                         if window.start <= row.prediction.prediction_origin < window.end)
            scheduled = sum(window.start <= t < window.end for t in phase.positions)
            counts = {symbol: (scheduled,
                sum(r.prediction.emitted for r in rows if r.prediction.physical_symbol == symbol),
                sum(r.matched for r in rows if r.prediction.physical_symbol == symbol))
                for symbol in SYMBOLS}
            return StabilityWindowReport(window, _equal_symbol_metrics(rows), counts)
        thirty_windows, operational_windows = prospective_windows(stage.prospective_schedule)
        thirty = tuple(map(report, thirty_windows))
        operations = tuple(map(report, operational_windows))
    return SymbolTimeReport(stage.horizon_minutes, stage.stage, metrics, coverage.by_symbol,
                            thirty, operations, metrics.leave_one_out)


@dataclass(frozen=True)
class CausalStrata:
    physical_symbol: str
    horizon_minutes: int
    fit_id: str
    base_manifest_sha256: str
    predictor_sigma_48_u_thresholds: tuple[float, float, float, float]
    base_count: int
    strata_sha256: str

    def assign(self, predictor_sigma_48_u: float) -> int:
        if not isfinite(predictor_sigma_48_u) or predictor_sigma_48_u <= 0:
            raise ValueError("positive finite predictor sigma_48(U) required")
        return bisect_left(self.predictor_sigma_48_u_thresholds, predictor_sigma_48_u)


def fit_causal_strata(base_manifest: RowManifest,
                      base_rows: Iterable[RowMetadata]) -> dict[str, CausalStrata]:
    """Empirical-CDF quantiles from selected BASE rows only; never target RMS48(T)."""
    if base_manifest.segment_type != "BASE":
        raise ValueError("causal strata require BASE manifest")
    rows = _assert_manifest(base_manifest, tuple(base_rows))
    result = {}
    for symbol in SYMBOLS:
        try:
            values = sorted(exp(row.feature_row.values[19]) for row in rows
                            if row.physical_symbol == symbol)
        except OverflowError as exc:
            raise ValueError("nonfinite predictor sigma_48(U) in base rows") from exc
        if not values or any(not isfinite(value) or value <= 0 for value in values):
            raise ValueError("each symbol needs positive predictor sigma_48(U) base values")
        n = len(values)
        thresholds = tuple(values[ceil(q*n)-1] for q in (0.2, 0.4, 0.6, 0.8))
        body = {"symbol": symbol, "horizon": base_manifest.horizon_minutes,
                "fit_id": base_manifest.fit_id, "base_manifest": base_manifest.manifest_sha256,
                "thresholds": thresholds, "base_count": n}
        result[symbol] = CausalStrata(symbol, base_manifest.horizon_minutes, base_manifest.fit_id,
                                      base_manifest.manifest_sha256, thresholds, n, digest(body))
    return result


@dataclass(frozen=True)
class DiagnosticObservation:
    evaluation: EvaluationRecord
    raw: RawFeatureRow | None
    processed: ProcessedFeatureRow | None


@dataclass(frozen=True)
class StateCell:
    symbol: str
    phase_id: str
    stratum: int | None
    utc_hour: int
    weekend: bool
    scheduled_count: int
    feature_available_count: int
    matched_count: int
    exact_zero_mom_1_count: int
    flat_range_count: int
    out_of_training_range_count: int
    mean_rms_dominance_48: float | None
    class_counts: tuple[int, int, int]
    metrics: dict[str, float | None]


def state_clock_report(observations: Iterable[DiagnosticObservation],
                       strata: dict[str, CausalStrata]) -> tuple[StateCell, ...]:
    """Retain all five strata, including empty cells when thresholds coincide."""
    rows = tuple(observations)
    groups: dict[tuple[str, str, int | None, int, bool], list[DiagnosticObservation]] = {}
    phases = sorted({row.evaluation.prediction.phase_id for row in rows})
    for row in rows:
        p = row.evaluation.prediction
        if p.physical_symbol not in strata or strata[p.physical_symbol].horizon_minutes != p.horizon_minutes:
            raise ValueError("wrong-horizon frozen causal strata")
        if row.raw is not None and (row.raw.physical_symbol != p.physical_symbol or
                                    row.raw.prediction_origin != p.prediction_origin):
            raise ValueError("diagnostic raw row key mismatch")
        sigma = exp(row.raw.values[19]) if row.raw is not None else None
        stratum = strata[p.physical_symbol].assign(sigma) if sigma is not None else None
        t = p.prediction_origin
        groups.setdefault((p.physical_symbol, p.phase_id, stratum, t.hour,
                           t.weekday() >= 5), []).append(row)
    # Precreate all five strata for observed symbol/phase/hour/weekend partitions.
    clocks = {(s, ph, hour, weekend) for s, ph, _, hour, weekend in groups}
    for symbol, phase, hour, weekend in clocks:
        for stratum in range(5):
            groups.setdefault((symbol, phase, stratum, hour, weekend), [])
    output = []
    for (symbol, phase, stratum, hour, weekend), members in sorted(
            groups.items(), key=lambda item: (SYMBOLS.index(item[0][0]), item[0][1],
                                              -1 if item[0][2] is None else item[0][2],
                                              item[0][3], item[0][4])):
        evaluations = tuple(item.evaluation for item in members)
        known = tuple(item for item in members if item.raw is not None)
        dominance = tuple(item.raw.values[22] for item in known)
        output.append(StateCell(symbol, phase, stratum, hour, weekend, len(members),
            sum(item.evaluation.prediction.feature_status == "AVAILABLE" for item in members),
            sum(item.evaluation.matched for item in members),
            sum(item.raw.values[0] == 0 for item in known),
            sum(item.raw.values[14] == 1 for item in known),
            sum(bool(item.processed.outside_training_range) for item in members if item.processed),
            sum(dominance)/len(dominance) if dominance else None,
            tuple(sum(item.evaluation.truth is not None and
                      item.evaluation.truth.canonical_class == cls for item in members)
                  for cls in CLASSES), cell_metrics(evaluations).values))
    return tuple(output)


@dataclass(frozen=True)
class JumpEvidence:
    source_revision: bool = False
    large_trailing_return_boundary: bool = False
    scale_change: bool = False
    numerical_status_change: bool = False
    evidence_ref: str | None = None


@dataclass(frozen=True)
class AdjacentPair:
    symbol: str
    horizon_minutes: int
    previous_origin: datetime
    origin: datetime
    fitted_bundle_sha256: str
    total_variation: float
    hard_class_flip_long_short: bool
    side_log_odds_change: float
    association: JumpEvidence


@dataclass(frozen=True)
class HardRun:
    symbol: str
    horizon_minutes: int
    fitted_bundle_sha256: str
    predicted_class: str
    first_origin: datetime
    last_origin: datetime
    length: int


def adjacent_origin_report(predictions: Iterable[SealedPrediction], *,
                           associations: dict[tuple[str, datetime, int], JumpEvidence] | None = None
                           ) -> tuple[tuple[AdjacentPair, ...], tuple[HardRun, ...]]:
    """No bridge over unavailable origins, five-minute gaps, or fitted-state changes."""
    rows = tuple(predictions)
    if len({(p.physical_symbol, p.prediction_origin, p.horizon_minutes) for p in rows}) != len(rows):
        raise ValueError("duplicate adjacent diagnostic key")
    pairs, runs = [], []
    for symbol in SYMBOLS:
        for horizon in (60, 120):
            prior = None
            run_start = None
            run_length = 0
            for p in sorted((p for p in rows if p.physical_symbol == symbol and
                             p.horizon_minutes == horizon), key=lambda p: p.prediction_origin):
                available = p.emitted and p.calibrated is not None
                contiguous = (available and prior is not None and
                              p.prediction_origin - prior.prediction_origin == FIVE_MINUTES and
                              p.bundle_sha256 == prior.bundle_sha256)
                if not contiguous and prior is not None and run_length:
                    runs.append(HardRun(symbol, horizon, prior.bundle_sha256,
                                        prior.calibrated.hard_class, run_start,
                                        prior.prediction_origin, run_length))
                    run_length = 0
                if not available:
                    prior = None
                    continue
                if not contiguous:
                    run_start, run_length = p.prediction_origin, 1
                else:
                    a, b = prior.calibrated, p.calibrated
                    pairs.append(AdjacentPair(symbol, horizon, prior.prediction_origin,
                        p.prediction_origin, p.bundle_sha256,
                        0.5 * sum(abs(b.probabilities[c] - a.probabilities[c]) for c in range(3)),
                        {a.hard_class, b.hard_class} == {CLASSES[0], CLASSES[1]},
                        (b.log_probabilities[0]-b.log_probabilities[1]) -
                        (a.log_probabilities[0]-a.log_probabilities[1]),
                        (associations or {}).get((symbol, p.prediction_origin, horizon), JumpEvidence())))
                    if b.hard_class == a.hard_class:
                        run_length += 1
                    else:
                        runs.append(HardRun(symbol, horizon, prior.bundle_sha256,
                                            a.hard_class, run_start, prior.prediction_origin,
                                            run_length))
                        run_start, run_length = p.prediction_origin, 1
                prior = p
            if prior is not None and run_length:
                runs.append(HardRun(symbol, horizon, prior.bundle_sha256,
                                    prior.calibrated.hard_class, run_start,
                                    prior.prediction_origin, run_length))
    return tuple(pairs), tuple(runs)


def reflect_raw(row: RawFeatureRow) -> RawFeatureRow:
    if len(row.values) != 35:
        raise ValueError("reflection needs exact 35 pre-standardization columns")
    values = list(row.values)
    for index in REFLECTION_NEGATE:
        values[index - 1] = -values[index - 1]
    for first, second in REFLECTION_SWAPS:
        values[first - 1], values[second - 1] = values[second - 1], values[first - 1]
    return replace(row, values=tuple(values))


@dataclass(frozen=True)
class ReflectionGap:
    symbol: str
    period_id: str
    origin: datetime
    original_probabilities: tuple[float, float, float]
    reflected_probabilities: tuple[float, float, float]
    long_short_exchanged_original: tuple[float, float, float]
    probability_gap: tuple[float, float, float]
    total_variation_gap: float


def reflection_gap(bundle: FitBundle, row: RawFeatureRow, *, period_id: str) -> ReflectionGap:
    """Reflect constructed raw coordinates, then original frozen P/S/A/I state."""
    bundle.verify_hashes()
    if not period_id:
        raise ValueError("diagnostic period identity required")
    original = transform(row, bundle.preprocessing)
    reflected = transform(reflect_raw(row), bundle.preprocessing)
    assert len(original.values) == len(reflected.values) == 35
    p = bundle.calibrator.predict(bundle.model.raw_prediction(row.physical_symbol,
                                original.values[:32])).probabilities
    pr = bundle.calibrator.predict(bundle.model.raw_prediction(row.physical_symbol,
                                 reflected.values[:32])).probabilities
    swapped = p[1], p[0], p[2]
    gap = tuple(pr[i] - swapped[i] for i in range(3))
    return ReflectionGap(row.physical_symbol, period_id, row.prediction_origin,
                         p, pr, swapped, gap, 0.5*sum(abs(v) for v in gap))


def reflection_distribution(gaps: Iterable[ReflectionGap]
                            ) -> dict[tuple[str, str], tuple[float, ...]]:
    result: dict[tuple[str, str], list[float]] = {}
    for gap in gaps:
        result.setdefault((gap.symbol, gap.period_id), []).append(gap.total_variation_gap)
    return {key: tuple(sorted(values)) for key, values in result.items()}


@dataclass(frozen=True)
class FittedStateReport:
    horizon_minutes: int
    fit_id: str
    bundle_sha256: str
    q_gauge_slope_norm: float
    active_state_columns: tuple[int, ...]
    constant_state_columns: tuple[int, ...]
    symbol_intercepts: tuple[tuple[float, float, float], ...]
    scaler_domains: tuple[object, ...]
    constructed_unit_slopes: tuple[tuple[int, str, tuple[float, float, float] | None], ...]
    calibrator_inverse_temperature: float
    calibration_status: str
    calibration_boundary: str | None
    solver_certificate: tuple[str, float, float, int]
    training_age_seconds: float
    calibration_age_seconds: float


def fitted_state_report(bundle: FitBundle, *, training_endpoint: datetime,
                        calibration_endpoint: datetime, observed_at: datetime) -> FittedStateReport:
    bundle.verify_hashes()
    train, cal, observed = utc(training_endpoint), utc(calibration_endpoint), utc(observed_at)
    if train > cal or cal > observed:
        raise ValueError("model age endpoints must be ordered actual/nominal UTC dates")
    model, state = bundle.model, bundle.preprocessing
    slopes = []
    for domain in state.domains:
        coefficient = model.b[domain.index - 1]
        slopes.append((domain.index, domain.domain,
                       None if domain.constant else tuple(v / domain.population_sd for v in coefficient)))
    for index, group in enumerate(GROUPS[:32], 1):
        if group == "I":
            slopes.append((index, "I", tuple(model.b[index - 1])))
    slopes.sort(key=lambda item: (item[0], item[1]))
    return FittedStateReport(model.horizon_minutes, bundle.manifest.fit_id,
        bundle.manifest.bundle_sha256,
        sqrt(sum(v*v for pair in model.v for v in pair)),
        tuple(j for j in range(1, 33) if j not in model.zero_slope_state_indices),
        model.zero_slope_state_indices, model.alpha_by_symbol, state.domains,
        tuple(slopes), bundle.calibrator.inverse_temperature,
        bundle.calibrator.status, bundle.calibrator.boundary_flag,
        (model.convergence_status, model.objective, model.gradient_infinity_norm,
         model.iterations), (observed-train).total_seconds(), (observed-cal).total_seconds())


def compare_fitted_states(a: FittedStateReport, b: FittedStateReport
                          ) -> dict[tuple[int, str], tuple[tuple[float, ...] | None,
                                                          tuple[float, ...] | None]]:
    if a.horizon_minutes != b.horizon_minutes:
        raise ValueError("compare refits only within one horizon")
    left = {(index, domain): slope for index, domain, slope in a.constructed_unit_slopes}
    right = {(index, domain): slope for index, domain, slope in b.constructed_unit_slopes}
    return {key: (left.get(key), right.get(key)) for key in left.keys() | right.keys()}


@dataclass(frozen=True)
class VintageComparison:
    symbol: str
    origin: datetime
    source_snapshot_id: str
    sealed_versions: tuple[tuple[str, str], ...]
    later_versions: tuple[tuple[str, str], ...]
    affected_feature_families: tuple[str, ...]

    @property
    def discrepancy(self) -> bool:
        return self.sealed_versions != self.later_versions


@dataclass(frozen=True)
class VintageReport:
    comparisons: int
    discrepancies: int
    discrepancy_rate: float | None
    affected_symbols: tuple[str, ...]
    affected_feature_families: tuple[str, ...]
    version_differences: tuple[tuple[str, datetime, tuple[tuple[str, str], ...],
                                     tuple[tuple[str, str], ...]], ...]


def reconcile_vintages(rows: Iterable[VintageComparison]) -> VintageReport:
    observations = tuple(rows)
    for row in observations:
        if row.symbol not in SYMBOLS or not row.source_snapshot_id:
            raise ValueError("sealed vintage identity required")
        origin(row.origin)
    changed = tuple(row for row in observations if row.discrepancy)
    return VintageReport(len(observations), len(changed),
        len(changed)/len(observations) if observations else None,
        tuple(sorted({row.symbol for row in changed}, key=SYMBOLS.index)),
        tuple(sorted({family for row in changed for family in row.affected_feature_families})),
        tuple((row.symbol, row.origin, row.sealed_versions, row.later_versions) for row in changed))
