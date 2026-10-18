"""Complete-grid evaluation populations and registered equal-cell estimands."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Mapping

from .calendar import (FIVE_MINUTES, FOLDS, H1_END, H1_START, PURGE,
                       Horizon, ProspectiveSchedule, origin)
from .evaluation_metrics import EvaluationRecord, CellMetrics, _mean, cell_metrics
from .model import CLASSES
from .source import SYMBOLS

CORE = (
    "delta_ll.B1", "delta_ll.B3", "delta_bs.B1", "delta_bs.B3",
    "delta_macro_auc.B3", *(f"auc_excess.{c}" for c in CLASSES),
    "delta_side_ll.B1", "delta_side_ll.B3", "side_auc_excess",
    "gamma.B1", "gamma.B3", "forced_side_benefit", "selected_incidence_benefit",
)


@dataclass(frozen=True)
class PhaseGrid:
    phase_id: str
    positions: tuple[datetime, ...]
    records: tuple[EvaluationRecord, ...]

    def __post_init__(self) -> None:
        if not self.positions or len(set(self.positions)) != len(self.positions):
            raise ValueError("complete nonempty unique scheduled grid required")
        if any(origin(t) != t for t in self.positions):
            raise ValueError("invalid scheduled origin")
        if any(b - a != FIVE_MINUTES for a, b in zip(self.positions, self.positions[1:])):
            raise ValueError("scheduled grid must retain every five-minute position")
        if any(r.prediction.phase_id != self.phase_id or
               r.prediction.prediction_origin not in self.positions for r in self.records):
            raise ValueError("record outside its phase grid")

    @property
    def key_counts(self) -> dict[tuple[datetime, str, int], int]:
        counts: dict[tuple[datetime, str, int], int] = {}
        for row in self.records:
            p = row.prediction
            key = p.prediction_origin, p.physical_symbol, p.horizon_minutes
            counts[key] = counts.get(key, 0) + 1
        return counts


@dataclass(frozen=True)
class StageEvidence:
    horizon_minutes: int
    stage: str
    phases: tuple[PhaseGrid, ...]
    contract_mode: str = "SYNTHETIC_FIXTURE"
    prospective_schedule: ProspectiveSchedule | None = None

    def __post_init__(self) -> None:
        Horizon(self.horizon_minutes)
        expected = ("F1", "F2", "F3", "F4", "F5") if self.stage == "D" else (
            ("H1",) if self.stage == "H1" else ("P",) if self.stage == "P" else ())
        if not expected or tuple(p.phase_id for p in self.phases) != expected:
            raise ValueError("stage requires registered ordered phase units")
        if any(r.prediction.horizon_minutes != self.horizon_minutes
               for phase in self.phases for r in phase.records):
            raise ValueError("cross-horizon evaluation evidence")
        expected_kind = "PROSPECTIVE_FORECAST" if self.stage == "P" else "HISTORICAL_SIMULATION"
        if any(r.prediction.record_kind != expected_kind for phase in self.phases for r in phase.records):
            raise ValueError("stage/record provenance kind mismatch")
        if self.contract_mode not in {"SYNTHETIC_FIXTURE", "REGISTERED"}:
            raise ValueError("invalid grid contract mode")
        if self.stage == "P" and self.contract_mode == "REGISTERED" and (
                self.prospective_schedule is None or
                self.prospective_schedule.horizon_minutes != self.horizon_minutes):
            raise ValueError("registered P grid requires own-horizon schedule")

    @property
    def registered_grid_complete(self) -> bool:
        if self.contract_mode != "REGISTERED":
            return False
        for phase in self.phases:
            if self.stage == "D":
                definition = next(f for f in FOLDS if f.fit_id == phase.phase_id)
                lower = definition.score.nominal_start + PURGE
                upper = definition.score.nominal_end - PURGE
            elif self.stage == "H1":
                lower, upper = H1_START + PURGE, H1_END - PURGE
            else:
                lower, upper = self.prospective_schedule.start, self.prospective_schedule.end
            if (phase.positions[0] != lower or phase.positions[-1] != upper - FIVE_MINUTES or
                    len(phase.positions) != int((upper - lower) / FIVE_MINUTES)):
                return False
            counts = phase.key_counts
            if len(counts) != len(phase.positions) * len(SYMBOLS) or any(v != 1 for v in counts.values()):
                return False
        return True


@dataclass(frozen=True)
class StageMetrics:
    horizon_minutes: int
    stage: str
    aggregate: dict[str, float | None]
    by_phase: dict[str, dict[str, float | None]]
    by_symbol: dict[str, dict[str, float | None]]
    cells: dict[tuple[str, str], CellMetrics]
    pooled_rows: CellMetrics
    registered_vector: dict[str, float | None]
    temporal_units: dict[str, dict[str, float | None]]
    leave_one_out: dict[str, dict[str, float | None]]
    registered_grid_complete: bool


def _aggregate(cells: list[CellMetrics]) -> dict[str, float | None]:
    names = set().union(*(cell.values.keys() for cell in cells))
    return {name: _mean(cell.values.get(name) for cell in cells) for name in names}


def _point_cells(stage: StageEvidence, draws: Mapping[str, tuple[int, ...]] | None
                 ) -> tuple[dict[tuple[str, str], CellMetrics], dict[str, list[EvaluationRecord]]]:
    cells = {}
    selected_rows: dict[str, list[EvaluationRecord]] = {}
    for phase in stage.phases:
        indexes = (draws[phase.phase_id] if draws is not None else tuple(range(len(phase.positions))))
        if any(not 0 <= index < len(phase.positions) for index in indexes):
            raise ValueError("draw index outside scheduled grid")
        by_time: dict[datetime, list[EvaluationRecord]] = {}
        for row in phase.records:
            by_time.setdefault(row.prediction.prediction_origin, []).append(row)
        rows = [row for index in indexes for row in by_time.get(phase.positions[index], ())]
        selected_rows[phase.phase_id] = rows
        for symbol in SYMBOLS:
            cells[phase.phase_id, symbol] = cell_metrics(
                row for row in rows if row.prediction.physical_symbol == symbol)
    return cells, selected_rows


def _reaggregate(cell_map: dict[tuple[str, str], CellMetrics], phase_ids: tuple[str, ...]
                 ) -> dict[str, float | None]:
    phases = [_aggregate([cell_map[phase_id, symbol] for symbol in SYMBOLS])
              for phase_id in phase_ids]
    names = set().union(*(phase.keys() for phase in phases))
    return {name: _mean(phase.get(name) for phase in phases) for name in names}


def _temporal(stage: StageEvidence, rows_by_phase: dict[str, list[EvaluationRecord]]
              ) -> dict[str, dict[str, float | None]]:
    if stage.stage == "D":
        return {phase.phase_id: _aggregate([cell_metrics(
                    row for row in rows_by_phase[phase.phase_id]
                    if row.prediction.physical_symbol == symbol) for symbol in SYMBOLS])
                for phase in stage.phases}
    if stage.stage != "P":
        return {}
    start = stage.phases[0].positions[0]
    rows = rows_by_phase["P"]
    intervals = {}
    for i in range(3):
        lower, upper = start + timedelta(days=30 * i), start + timedelta(days=30 * (i + 1))
        intervals[f"P30_{i+1}"] = _aggregate([cell_metrics(
            row for row in rows if row.prediction.physical_symbol == symbol and
            lower <= row.prediction.prediction_origin < upper) for symbol in SYMBOLS])
    return intervals


def _registered(aggregate: dict[str, float | None],
                by_phase: dict[str, dict[str, float | None]],
                by_symbol: dict[str, dict[str, float | None]],
                stage: str) -> dict[str, float | None]:
    vector = {f"agg.{name}": aggregate.get(name) for name in CORE}
    for cls in CLASSES:
        for baseline in ("B1", "B3"):
            name = f"delta_bs.{baseline}.{cls}"
            vector[f"agg.{name}"] = aggregate.get(name)
    for symbol in SYMBOLS:
        for metric in ("delta_ll.B1", "delta_ll.B3", "delta_side_ll.B1", "delta_side_ll.B3",
                       *(f"auc_excess.{cls}" for cls in CLASSES)):
            vector[f"symbol.{symbol}.{metric}"] = by_symbol[symbol].get(metric)
    if stage == "D":
        for phase in ("F1", "F2", "F3", "F4", "F5"):
            for metric in ("delta_ll.B1", "delta_ll.B3", "delta_side_ll.B1", "delta_side_ll.B3"):
                vector[f"fold.{phase}.{metric}"] = by_phase[phase].get(metric)
    return vector


def compute_stage(stage: StageEvidence, *, draws: Mapping[str, tuple[int, ...]] | None = None
                  ) -> StageMetrics:
    """Recompute every score from selected scheduled-position multiplicities."""
    cells, rows_by_phase = _point_cells(stage, draws)
    phase_ids = tuple(phase.phase_id for phase in stage.phases)
    by_phase = {phase_id: _aggregate([cells[phase_id, symbol] for symbol in SYMBOLS])
                for phase_id in phase_ids}
    by_symbol = {symbol: _aggregate([cells[phase_id, symbol] for phase_id in phase_ids])
                 for symbol in SYMBOLS}
    aggregate = _reaggregate(cells, phase_ids)
    temporal = _temporal(stage, rows_by_phase)
    leave_one_out = {}
    if stage.stage == "D":
        leave_one_out = {phase: _reaggregate(cells, tuple(p for p in phase_ids if p != phase))
                         for phase in phase_ids}
    elif stage.stage == "P":
        rows = rows_by_phase["P"]
        start = stage.phases[0].positions[0]
        for i in range(3):
            lo, hi = start + timedelta(days=30 * i), start + timedelta(days=30 * (i + 1))
            leave_one_out[f"P30_{i+1}"] = _aggregate([cell_metrics(
                row for row in rows if row.prediction.physical_symbol == symbol and
                not lo <= row.prediction.prediction_origin < hi) for symbol in SYMBOLS])
    pooled = cell_metrics(row for rows in rows_by_phase.values() for row in rows)
    return StageMetrics(stage.horizon_minutes, stage.stage, aggregate, by_phase, by_symbol,
                        cells, pooled, _registered(aggregate, by_phase, by_symbol, stage),
                        temporal, leave_one_out, stage.registered_grid_complete)
