"""Registered paired non-circular moving-block uncertainty, with fixed production settings."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite, sqrt
from typing import Callable, Mapping

import numpy as np

from .evaluation_stage import StageEvidence, compute_stage

SEED = 20261017
PRIMARY_BLOCK = 2016
SENSITIVITY_BLOCK = 4032
REPLICATES = 10000
RNG = "NumPy 2.2.5 PCG64.random_raw"
UINT64 = 1 << 64


def _pcg64():
    if np.__version__ != "2.2.5":
        raise RuntimeError("registered bootstrap requires NumPy 2.2.5 PCG64")
    return np.random.PCG64(SEED)


def randint_raw(raw: Callable[[], int], m: int) -> int:
    """Exact rejection-sampled RandInt(m), never a floating conversion."""
    if not isinstance(m, int) or not 1 <= m <= UINT64:
        raise ValueError("RandInt bound must be in [1,2^64]")
    limit = (UINT64 // m) * m
    while True:
        value = int(raw())
        if not 0 <= value < UINT64:
            raise ValueError("raw RNG output is not uint64")
        if value < limit:
            return value % m


def moving_block_indices(n: int, length: int, random_index: Callable[[int], int]
                         ) -> tuple[int, ...] | None:
    if n < 0 or length <= 0:
        raise ValueError("invalid nominal grid/block length")
    if n < length:
        return None
    result: list[int] = []
    for _ in range(ceil(n / length)):
        start = random_index(n - length + 1)
        if not 0 <= start <= n - length:
            raise ValueError("invalid block start")
        result.extend(range(start, start + length))
    return tuple(result[:n])


@dataclass(frozen=True)
class Band:
    observed: float | None
    lower: float | None
    upper: float | None
    sample_sd: float | None
    status: str


@dataclass(frozen=True)
class SimultaneousBands:
    critical_value: float | None
    bands: dict[str, Band]
    replicate_count: int


def empirical_quantile_95(values: tuple[float, ...]) -> float:
    if not values:
        raise ValueError("nonempty empirical distribution required")
    return sorted(values)[ceil(0.95 * len(values)) - 1]


def simultaneous_bands(observed: Mapping[str, float | None],
                       replicates: tuple[Mapping[str, float | None], ...]) -> SimultaneousBands:
    """Undefined components are removed only from the max, never redrawn."""
    if len(replicates) < 2:
        raise ValueError("at least two replicates required")
    standard_deviations: dict[str, float] = {}
    for name, point in observed.items():
        samples = tuple(rep.get(name) for rep in replicates)
        if (point is None or not isfinite(point) or
                any(value is None or not isfinite(value) for value in samples)):
            continue
        if all(value == samples[0] for value in samples):
            standard_deviations[name] = 0.0
        else:
            sample_mean = sum(samples) / len(samples)
            standard_deviations[name] = sqrt(sum((value - sample_mean) ** 2 for value in samples)
                                              / (len(samples) - 1))
    maxima = []
    if standard_deviations:
        for rep in replicates:
            maxima.append(max((abs((rep[name] - observed[name]) / sd)
                               for name, sd in standard_deviations.items() if sd > 0), default=0.0))
        critical = empirical_quantile_95(tuple(maxima))
    else:
        critical = None
    bands = {}
    for name, point in observed.items():
        if name not in standard_deviations:
            bands[name] = Band(point, None, None, None, "NOT_ESTIMABLE")
        else:
            sd = standard_deviations[name]
            bands[name] = Band(point, point - critical * sd, point + critical * sd,
                               sd, "ESTIMABLE")
    return SimultaneousBands(critical, bands, len(replicates))


def conservative_envelope(primary: SimultaneousBands, sensitivity: SimultaneousBands
                          ) -> dict[str, Band]:
    if primary.bands.keys() != sensitivity.bands.keys():
        raise ValueError("7d/14d statistic families differ")
    return {name: (Band(first.observed, min(first.lower, second.lower),
                        max(first.upper, second.upper), None, "ESTIMABLE")
                   if first.status == second.status == "ESTIMABLE" else
                   Band(first.observed, None, None, None, "NOT_ESTIMABLE"))
            for name, first in primary.bands.items()
            for second in (sensitivity.bands[name],)}


@dataclass(frozen=True)
class BootstrapResult:
    horizon_minutes: int
    stage: str
    observed: dict[str, float | None]
    by_block: dict[int, SimultaneousBands]
    envelope: dict[str, Band]
    replicate_vectors: dict[int, tuple[dict[str, float | None], ...]]
    draw_index_sha256: dict[int, str]
    evidence_mode: str = "SYNTHETIC_FIXTURE"


def _bootstrap(stage: StageEvidence, *, lengths: tuple[int, int],
               replicate_count: int) -> BootstrapResult:
    """Private small-fixture seam; production wrapper below freezes all settings."""
    from hashlib import sha256
    from json import dumps

    observed = compute_stage(stage).registered_vector
    by_block = {}
    raw_vectors = {}
    draw_hashes = {}
    for length in lengths:
        if any(len(phase.positions) < length for phase in stage.phases):
            raw_vectors[length] = ()
            by_block[length] = SimultaneousBands(None, {
                name: Band(point, None, None, None, "NOT_ESTIMABLE")
                for name, point in observed.items()}, 0)
            draw_hashes[length] = sha256(b"").hexdigest()
            continue
        generator = _pcg64()  # Fresh stream for each (H,stage,length).
        vectors = []
        index_hash = sha256()
        for _ in range(replicate_count):
            draws = {}
            for phase in stage.phases:  # F1,...,F5 order is validated by StageEvidence.
                selected = moving_block_indices(len(phase.positions), length,
                    lambda m: randint_raw(generator.random_raw, m))
                if selected is None:
                    raise ValueError("NOT_ESTIMABLE: nominal phase shorter than registered block")
                draws[phase.phase_id] = selected
                index_hash.update(dumps((phase.phase_id, selected), separators=(",", ":")).encode())
            vectors.append(compute_stage(stage, draws=draws).registered_vector)
        raw_vectors[length] = tuple(vectors)
        by_block[length] = simultaneous_bands(observed, raw_vectors[length])
        draw_hashes[length] = index_hash.hexdigest()
    return BootstrapResult(stage.horizon_minutes, stage.stage, observed, by_block,
                           conservative_envelope(by_block[lengths[0]], by_block[lengths[1]]),
                           raw_vectors, draw_hashes)


def registered_bootstrap(stage: StageEvidence) -> BootstrapResult:
    """Production contract has no caller-configurable seed, lengths or replicate count."""
    from dataclasses import replace
    if not stage.registered_grid_complete:
        raise ValueError("registered bootstrap requires complete scheduled stage grid")
    return replace(_bootstrap(stage, lengths=(PRIMARY_BLOCK, SENSITIVITY_BLOCK),
                              replicate_count=REPLICATES), evidence_mode="REGISTERED")
