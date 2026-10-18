"""Expected-key, delivery and prospective operational accounting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable, Mapping

from .evaluation_metrics import EvaluationRecord, SealedPrediction, CLASS_INDEX
from .evaluation_stage import StageEvidence
from .source import SYMBOLS


@dataclass(frozen=True)
class CoverageReport:
    horizon_minutes: int
    stage: str
    registered_grid_complete: bool
    expected_keys: int
    recorded_keys: int
    missing_keys: tuple[tuple[str, str, int], ...]
    duplicate_keys: tuple[tuple[str, str, int], ...]
    by_symbol: dict[str, dict[str, object]]
    unavailable_reasons: dict[str, int]
    target_statuses: dict[str, int]
    matched_scores: int
    end_to_end_coverage: float
    emission_delay_seconds: tuple[float, ...]
    late_receipt_ages_seconds: tuple[float, ...]
    max_source_available_at: tuple[str, ...]
    version_conflicts: int
    vintage_discrepancies: int
    boundary_exclusions: dict[str, int]
    feature_eligible: dict[str, int]


def coverage_report(stage: StageEvidence, *, boundary_exclusions: Mapping[str, int] | None = None
                    , asof_verifier: Callable[[SealedPrediction], bool] | None = None
                    ) -> CoverageReport:
    missing = []
    duplicate = []
    expected = recorded = matched = conflicts = vintage = 0
    reasons: dict[str, int] = {}
    statuses: dict[str, int] = {}
    by_symbol = {symbol: {"expected": 0, "emitted": 0, "on_time": 0,
                         "asof_emitted": 0, "valid_targets": 0,
                         "emitted_valid_targets": 0, "emitted_target_reason_missing": 0,
                         "window_on_time": []} for symbol in SYMBOLS}
    delays = []
    late_ages = []
    available_ats = []
    feature_eligible = {symbol: 0 for symbol in SYMBOLS}
    for phase in stage.phases:
        counts = phase.key_counts
        expected += len(phase.positions) * len(SYMBOLS)
        recorded += len(phase.records)
        for t in phase.positions:
            for symbol in SYMBOLS:
                key = t, symbol, stage.horizon_minutes
                if counts.get(key, 0) == 0:
                    missing.append((t.isoformat(), symbol, stage.horizon_minutes))
                elif counts[key] > 1:
                    duplicate.append((t.isoformat(), symbol, stage.horizon_minutes))
                by_symbol[symbol]["expected"] += 1
        for row in phase.records:
            p, truth = row.prediction, row.truth
            dest = by_symbol[p.physical_symbol]
            dest["emitted"] += int(p.emitted)
            feature_eligible[p.physical_symbol] += int(p.feature_status == "AVAILABLE")
            dest["on_time"] += int(p.on_time is True)
            # Structural references alone are never authenticated provenance.
            dest["asof_emitted"] += int(p.emitted and p.provenance_mode == "ASOF_VERIFIED" and
                p.asof_evidence is not None and p.asof_evidence.admissible_at(p.prediction_origin) and
                asof_verifier is not None and asof_verifier(p))
            dest["valid_targets"] += int(truth is not None and truth.target_status == "VALID")
            dest["emitted_valid_targets"] += int(p.emitted and truth is not None and truth.target_status == "VALID")
            dest["emitted_target_reason_missing"] += int(p.emitted and (
                truth is None or (truth.target_status != "VALID" and not truth.unavailable_reasons)))
            matched += int(row.matched)
            for reason in p.unavailable_reasons:
                reasons[reason] = reasons.get(reason, 0) + 1
            if truth is not None:
                statuses[truth.target_status] = statuses.get(truth.target_status, 0) + 1
                for reason in truth.unavailable_reasons:
                    reasons[f"TARGET:{reason}"] = reasons.get(f"TARGET:{reason}", 0) + 1
            if p.emission_delay_seconds is not None:
                delays.append(p.emission_delay_seconds)
            if p.late_receipt_age_seconds is not None:
                late_ages.append(p.late_receipt_age_seconds)
            if p.max_source_available_at is not None:
                available_ats.append(p.max_source_available_at.isoformat())
            conflicts += int(p.source_version_conflict)
            vintage += int(p.vintage_discrepancy)
    if stage.stage == "P":
        phase = stage.phases[0]
        start = phase.positions[0]
        for symbol in SYMBOLS:
            for i in range(13):
                lo = start + timedelta(days=7 * i if i < 12 else 84)
                hi = start + timedelta(days=7 * (i + 1) if i < 12 else 90)
                expected_window = sum(lo <= t < hi for t in phase.positions)
                on_time_window = sum(p.prediction.physical_symbol == symbol and
                                     lo <= p.prediction.prediction_origin < hi and p.prediction.on_time
                                     for p in phase.records)
                by_symbol[symbol]["window_on_time"].append((expected_window, on_time_window))
    return CoverageReport(stage.horizon_minutes, stage.stage, stage.registered_grid_complete,
                          expected, recorded, tuple(missing), tuple(duplicate), by_symbol,
                          reasons, statuses, matched, matched / expected if expected else 0.0,
                          tuple(delays), tuple(late_ages), tuple(available_ats),
                          conflicts, vintage, dict(boundary_exclusions or {}), feature_eligible)


def stratified_accounting(stage: StageEvidence) -> dict[tuple[str, int, str, str, str | None,
                                                               str | None, str | None], dict[str, int]]:
    """Counts by symbol, horizon, phase, UTC ISO week, P window, class and frozen stratum."""
    result = {}
    for phase in stage.phases:
        by_key = {(r.prediction.prediction_origin, r.prediction.physical_symbol): r
                  for r in phase.records}
        start = phase.positions[0]
        for t in phase.positions:
            week = t.isocalendar()
            week_id = f"{week.year}-W{week.week:02d}"
            day = (t - start).days
            window = (f"P_W{min(day // 7 + 1, 13):02d}" if stage.stage == "P" else None)
            for symbol in SYMBOLS:
                row = by_key.get((t, symbol))
                cls = (row.truth.canonical_class if row and row.truth and
                       row.truth.target_status == "VALID" else None)
                stratum = row.frozen_causal_volatility_stratum if row else None
                key = (symbol, stage.horizon_minutes, phase.phase_id, week_id,
                       window, cls, stratum)
                counts = result.setdefault(key, {"expected": 0, "recorded": 0,
                    "feature_eligible": 0, "on_time": 0, "matched": 0})
                counts["expected"] += 1
                if row:
                    counts["recorded"] += 1
                    counts["feature_eligible"] += int(row.prediction.feature_status == "AVAILABLE")
                    counts["on_time"] += int(row.prediction.on_time)
                    counts["matched"] += int(row.matched)
    return result


def prospective_coverage_gates(report: CoverageReport, *, target_sealed: bool,
                               required_metrics_evaluable: bool,
                               ledger_and_artifacts_sealed: bool) -> dict[str, bool]:
    """Pure Section 20.4 thresholds; integrity issues are also surfaced separately."""
    symbols = report.by_symbol.values()
    if report.stage != "P":
        raise ValueError("prospective coverage requires P cohort report")
    return {
        "expected_key_accounting": report.registered_grid_complete and not report.missing_keys and
            not report.duplicate_keys and report.recorded_keys == report.expected_keys,
        "one_terminal_status": not report.missing_keys and not report.duplicate_keys,
        "asof_emitted": all(s["asof_emitted"] == s["emitted"] for s in symbols),
        "on_time_99_each_symbol": all(s["expected"] and s["on_time"] / s["expected"] >= 0.99
                                      for s in symbols),
        "fixed_windows_95_each_symbol": all(len(s["window_on_time"]) == 13 and
            all(n and count / n >= 0.95 for n, count in s["window_on_time"]) for s in symbols),
        "target_maturity_99_each_symbol": target_sealed and all(
            s["emitted"] and s["emitted_valid_targets"] / s["emitted"] >= 0.99
            for s in symbols),
        "target_reasons_retained": all(s["emitted_target_reason_missing"] == 0 for s in symbols),
        "required_metrics_evaluable": required_metrics_evaluable,
        "ledger_artifacts_sealed": ledger_and_artifacts_sealed,
    }


def delivered_benefit(records: tuple[EvaluationRecord, ...], *, baseline: str,
                      loss: str = "ll") -> tuple[float | None, int]:
    if baseline not in {"B1", "B3"} or loss not in {"ll", "bs"}:
        raise ValueError("registered probabilistic baseline and loss required")
    denominator = 0
    numerator = 0.0
    for row in records:
        p, truth = row.prediction, row.truth
        if truth is None or truth.target_status != "VALID":
            continue
        b = p.b1 if baseline == "B1" else p.b3
        if b is None:
            continue
        denominator += 1
        if p.calibrated is None:
            continue  # Missing V1 gives zero delivered improvement, no fallback.
        ci = CLASS_INDEX[truth.canonical_class]
        if loss == "ll":
            numerator += -b.log_probabilities[ci] + p.calibrated.log_probabilities[ci]
        else:
            numerator += sum((b.probabilities[j] - (j == ci)) ** 2 -
                             (p.calibrated.probabilities[j] - (j == ci)) ** 2 for j in range(3))
    return (numerator / denominator if denominator else None, denominator)
