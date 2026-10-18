"""Frozen P/S/A/I scaler state for small, explicitly eligible base rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite, sqrt
import platform
from typing import Iterable

from .features import GROUPS, NAMES, RawFeatureRow
from .source import SYMBOLS


@dataclass(frozen=True)
class ColumnDomainState:
    name: str
    index: int
    construction_id: str
    group: str
    domain: str
    membership_sha256: str
    count: int
    mean: float
    population_sd: float
    constant: bool
    raw_constant: float | None
    minimum: float
    maximum: float
    diagnostic_quantiles: tuple[float, float, float]


@dataclass(frozen=True)
class PreprocessingState:
    horizon_minutes: int
    fit_id: str
    membership_sha256: str
    registry: str
    feature_calculation_version: str
    numeric_runtime: str
    physical_mapping: tuple[tuple[str, str], ...]
    btc_context_mask_indices: tuple[int, ...]
    domains: tuple[ColumnDomainState, ...]
    zero_slope_state_indices: tuple[int, ...]

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["domains"] = [asdict(domain) for domain in self.domains]
        return result


@dataclass(frozen=True)
class ProcessedFeatureRow:
    raw: RawFeatureRow
    values: tuple[float, ...]
    constant_domain_departures: tuple[int, ...]
    outside_training_range: tuple[int, ...]


@dataclass(frozen=True)
class EligibleBaseRow:
    """Membership certificate from the future per-horizon split/target layer."""

    raw: RawFeatureRow
    horizon_minutes: int
    fit_id: str
    partition: str
    own_target_valid: bool


def _ordered_sum(values: Iterable[float]) -> float:
    total = 0.0
    for value in values:
        total += value
    return total


def _stats(values: list[float], name: str, index: int, group: str, domain: str,
           membership_sha256: str) -> ColumnDomainState:
    if not values or not all(isfinite(x) for x in values):
        raise ValueError("empty or nonfinite scaler domain")
    count = len(values)
    mean = _ordered_sum(values) / count
    constant = all(v == values[0] for v in values)
    if constant:
        sd = 0.0
    else:
        variance = _ordered_sum((v - mean) ** 2 for v in values) / count
        if not isfinite(variance) or variance <= 0:
            raise ValueError("numerically collapsed scaler variance")
        sd = sqrt(variance)
        if not isfinite(sd) or sd <= 0:
            raise ValueError("numerically collapsed scaler SD")
    ordered = sorted(values)
    quantiles = (ordered[0], ordered[(count - 1) // 2], ordered[-1])
    return ColumnDomainState(name, index + 1, f"LDE_V1_ADJ35_U1M:{name}", group, domain,
                             membership_sha256, count, mean, sd, constant,
                             values[0] if constant else None, min(values), max(values), quantiles)


def _lookup(state: PreprocessingState) -> dict[tuple[int, str], ColumnDomainState]:
    return {(d.index - 1, d.domain): d for d in state.domains}


def transform(row: RawFeatureRow, state: PreprocessingState) -> ProcessedFeatureRow:
    if row.physical_symbol not in SYMBOLS or len(row.values) != 35 or not all(isfinite(x) for x in row.values):
        raise ValueError("invalid raw feature row")
    domains = _lookup(state)
    values: list[float] = []
    departures: list[int] = []
    outside: list[int] = []
    for i, raw in enumerate(row.values):
        group = GROUPS[i]
        if group == "I":
            processed = raw
        elif group == "A" and row.physical_symbol == "BTCUSDT":
            processed = 0.0
        else:
            domain = row.physical_symbol if group == "S" else "ALT" if group == "A" else "POOL"
            stat = domains[i, domain]
            if raw < stat.minimum or raw > stat.maximum:
                outside.append(i + 1)
            if stat.constant:
                processed = 0.0
                if raw != stat.raw_constant:
                    departures.append(i + 1)
            else:
                processed = (raw - stat.mean) / stat.population_sd
        if not isfinite(processed):
            raise ValueError("nonfinite processed coordinate")
        values.append(processed)
    return ProcessedFeatureRow(row, tuple(values), tuple(departures), tuple(outside))


def fit_preprocessing(base_rows: Iterable[EligibleBaseRow], *, horizon_minutes: int, fit_id: str) -> PreprocessingState:
    """Fit only caller-certified eligible base rows; E60/E120 states differ.

    Row order is T ascending, then BTC, AVAX, SUI, 1000PEPE. This
    interface has no label or corpus reader and cannot silently add rows.
    """
    if horizon_minutes not in (60, 120) or not fit_id:
        raise ValueError("horizon 60/120 and fit identity required")
    certificates = tuple(base_rows)
    if not certificates or any(c.horizon_minutes != horizon_minutes or c.fit_id != fit_id or
                               c.partition != "BASE" or not c.own_target_valid for c in certificates):
        raise ValueError("only own-target-valid base rows for this horizon and fit are eligible")
    rows = tuple(sorted((c.raw for c in certificates),
                        key=lambda r: (r.prediction_origin, SYMBOLS.index(r.physical_symbol))))
    if not rows or any(len(r.values) != 35 or not all(isfinite(x) for x in r.values) for r in rows):
        raise ValueError("nonempty finite base rows required")
    origin_keys = [(r.prediction_origin.isoformat(), r.physical_symbol) for r in rows]
    if len(set(origin_keys)) != len(origin_keys):
        raise ValueError("duplicate symbol-origin base row")
    keys = [(r.prediction_origin.isoformat(), r.physical_symbol, r.source_snapshot_id) for r in rows]
    membership = sha256(json.dumps(keys, separators=(",", ":")).encode()).hexdigest()
    domains = []
    for i, (name, group) in enumerate(zip(NAMES, GROUPS)):
        if group == "I":
            continue
        domain_names = SYMBOLS if group == "S" else ("ALT",) if group == "A" else ("POOL",)
        for domain in domain_names:
            selected = [r.values[i] for r in rows if group == "P" or
                        (group == "S" and r.physical_symbol == domain) or
                        (group == "A" and r.physical_symbol != "BTCUSDT")]
            selected_keys = [keys[j] for j, r in enumerate(rows) if group == "P" or
                             (group == "S" and r.physical_symbol == domain) or
                             (group == "A" and r.physical_symbol != "BTCUSDT")]
            domain_hash = sha256(json.dumps(selected_keys, separators=(",", ":")).encode()).hexdigest()
            domains.append(_stats(selected, name, i, group, domain, domain_hash))
    mapping = (("BTCUSDT", "BTCUSDT"), ("AVAXUSDT", "AVAXUSDT"), ("SUIUSDT", "SUIUSDT"),
               ("PEPEUSDT", "1000PEPEUSDT"))
    provisional = PreprocessingState(horizon_minutes, fit_id, membership, "LDE_V1_ADJ35_U1M",
                                    "LDE_V1_ADJ35_U1M_PY_MATH_V1", f"Python {platform.python_version()} math binary64",
                                    mapping, tuple(range(24, 31)), tuple(domains), ())
    processed = [transform(r, provisional).values for r in rows]
    zero_slopes = tuple(i + 1 for i in range(32) if all(p[i] == processed[0][i] for p in processed))
    return PreprocessingState(horizon_minutes, fit_id, membership, provisional.registry,
                              provisional.feature_calculation_version, provisional.numeric_runtime,
                              mapping, provisional.btc_context_mask_indices, tuple(domains), zero_slopes)
