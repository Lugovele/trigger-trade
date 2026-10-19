"""Bounded synthetic C1 splitter benchmark and frozen pre-optimization reference.

This module has no historical source reader or development-study entry point.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from math import log2
from pathlib import Path
import ctypes
import json
import sys
from hashlib import sha256
from time import perf_counter
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import numpy as np

from triggertrade.live_direction_estimator_v1 import comparator
from triggertrade.live_direction_estimator_v1.evaluation_bootstrap import randint_raw
from triggertrade.live_direction_estimator_v1.manifests import canonical_json


def reference_best_split(states, labels, indices, candidates, minimum, parent):
    """Exact Phase 9 splitter before optimization; test/benchmark only."""
    best = None
    for feature in candidates:
        values = sorted({states[i][feature - 1] for i in indices})
        for lower, upper in zip(values, values[1:]):
            cut = comparator.split_cut(lower, upper)
            left = tuple(i for i in indices if states[i][feature - 1] <= cut)
            right = tuple(i for i in indices if states[i][feature - 1] > cut)
            if len(left) < minimum or len(right) < minimum:
                continue
            gain = comparator.gini_gain(parent, comparator._counts(left, labels),
                                        comparator._counts(right, labels))
            if gain <= 0:
                continue
            if (best is None or gain > best[2] or
                    (gain == best[2] and (feature, cut) < (best[0], best[1]))):
                best = feature, cut, gain, left, right
    return best


def synthetic_population(rows: int):
    if not 12 <= rows <= 20_000:
        raise ValueError("bounded synthetic row count must be in [12,20000]")
    states = tuple(tuple(float(((i * (j + 3) + i * i % 17) % (rows + 11)) / 31)
                         for j in range(comparator.FEATURE_COUNT)) for i in range(rows))
    labels = tuple((i * 7 + i // 13) % 3 for i in range(rows))
    return states, labels


def benchmark(*, rows: int = 600, trees: int = 4) -> dict:
    if rows > 1500:
        raise ValueError("reference benchmark row count must not exceed 1500")
    if not 1 <= trees <= 8:
        raise ValueError("bounded synthetic tree count must be in [1,8]")
    states, labels = synthetic_population(rows)
    indices = tuple(range(rows))
    prior = comparator.pooled_prior(labels)
    minimum = comparator.min_leaf_rows(rows)

    def grow(splitter):
        generator = np.random.PCG64(comparator.SEED_BASE + 60)
        draws = []
        def random_index(m):
            result = randint_raw(generator.random_raw, m)
            draws.append((m, result))
            return result
        with patch.object(comparator, "_best_split", splitter):
            forest = tuple(comparator._grow(states, labels, indices, 0, "", minimum,
                                            prior, random_index) for _ in range(trees))
        return forest, tuple(draws)

    start = perf_counter()
    reference, reference_draws = grow(reference_best_split)
    reference_seconds = perf_counter() - start
    start = perf_counter()
    optimized, optimized_draws = grow(comparator._best_split)
    optimized_seconds = perf_counter() - start
    exact = (canonical_json(tuple(asdict(t) for t in reference)) ==
             canonical_json(tuple(asdict(t) for t in optimized)) and
             reference_draws == optimized_draws)
    if not exact:
        raise AssertionError("optimized comparator differs from frozen reference")
    return {"rows": rows, "feature_count": comparator.FEATURE_COUNT,
            "trees": trees, "reference_seconds": reference_seconds,
            "optimized_seconds": optimized_seconds,
            "speedup": reference_seconds / optimized_seconds,
            "exact_output_and_rng": exact}


def _peak_working_set_bytes() -> int | None:
    """Read the process high-water RSS without sampling or extra allocations."""
    if sys.platform != "win32":
        return None

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = (
            ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        )

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = (
        ctypes.c_void_p, ctypes.POINTER(ProcessMemoryCounters), ctypes.c_ulong)
    psapi.GetProcessMemoryInfo.restype = ctypes.c_int
    process = kernel32.GetCurrentProcess()
    if not psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
        return None
    return int(counters.PeakWorkingSetSize)


def optimized_benchmark(*, rows: int, trees: int) -> dict:
    """Time only the registered optimized tree builder on a bounded fixture."""
    if not 1 <= trees <= 32:
        raise ValueError("bounded optimized tree count must be in [1,32]")
    states, labels = synthetic_population(rows)
    indices = tuple(range(rows))
    prior = comparator.pooled_prior(labels)
    minimum = comparator.min_leaf_rows(rows)
    generator = np.random.PCG64(comparator.SEED_BASE + 60)
    random_index = lambda m: randint_raw(generator.random_raw, m)
    start = perf_counter()
    forest = tuple(comparator._grow(states, labels, indices, 0, "", minimum,
                                    prior, random_index) for _ in range(trees))
    elapsed = perf_counter() - start
    if len(forest) != trees:
        raise AssertionError("optimized benchmark tree count mismatch")
    seconds_per_tree = elapsed / trees
    normalized = seconds_per_tree / (rows * log2(rows)) * 1_000_000
    peak = _peak_working_set_bytes()
    return {
        "rows": rows, "feature_count": comparator.FEATURE_COUNT, "trees": trees,
        "elapsed_seconds": elapsed, "seconds_per_tree": seconds_per_tree,
        "normalized_us_per_row_log2_row_per_tree": normalized,
        "peak_working_set_bytes": peak,
        "minimum_leaf_rows": minimum,
        "rng_generator": "PCG64", "rng_seed": comparator.SEED_BASE + 60,
        "maximum_depth": comparator.MAX_DEPTH,
        "node_candidate_features": comparator.NODE_FEATURES,
        "forest_sha256": sha256(canonical_json(
            tuple(asdict(tree) for tree in forest)).encode("utf-8")).hexdigest(),
    }


def _parallel_job(arguments: tuple[int, int]) -> dict:
    rows, trees = arguments
    return optimized_benchmark(rows=rows, trees=trees)


def parallel_benchmark(*, rows: int = 4000, trees: int = 8,
                       jobs: int = 4, worker_counts=(1, 2, 4)) -> dict:
    """Bounded process-level scaling only; every job owns a frozen comparator RNG."""
    if not 2 <= jobs <= 8:
        raise ValueError("bounded parallel job count must be in [2,8]")
    counts = tuple(worker_counts)
    if not counts or any(isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 4
                         for n in counts):
        raise ValueError("parallel worker counts must be integers in [1,4]")
    measurements = []
    baseline = None
    expected_hashes = None
    for workers in counts:
        start = perf_counter()
        with ProcessPoolExecutor(max_workers=workers) as executor:
            results = tuple(executor.map(_parallel_job, ((rows, trees) for _ in range(jobs))))
        wall = perf_counter() - start
        hashes = tuple(result["forest_sha256"] for result in results)
        if expected_hashes is None:
            expected_hashes = hashes
        elif hashes != expected_hashes:
            raise AssertionError("process scheduling changed frozen comparator output")
        if baseline is None:
            baseline = wall
        measurements.append({
            "workers": workers, "wall_seconds": wall,
            "speedup_vs_1": baseline / wall,
            "parallel_efficiency": baseline / wall / workers,
            "summed_tree_build_seconds": sum(r["elapsed_seconds"] for r in results),
            "maximum_worker_peak_bytes": max(
                (r["peak_working_set_bytes"] or 0 for r in results), default=0) or None,
            "exact_forest_hashes": hashes,
        })
    return {"rows_per_job": rows, "trees_per_job": trees, "jobs": jobs,
            "total_tree_work": jobs * trees, "feature_count": comparator.FEATURE_COUNT,
            "measurements": measurements, "exact_across_worker_counts": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bounded synthetic C1 comparator benchmark")
    parser.add_argument("--optimized-only", action="store_true")
    parser.add_argument("--parallel", action="store_true")
    parser.add_argument("--rows", type=int)
    parser.add_argument("--trees", type=int)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    if args.parallel:
        result = parallel_benchmark(rows=4000 if args.rows is None else args.rows,
                                    trees=8 if args.trees is None else args.trees,
                                    jobs=args.jobs)
    elif args.optimized_only:
        if args.rows is None or args.trees is None:
            parser.error("--optimized-only requires --rows and --trees")
        result = optimized_benchmark(rows=args.rows, trees=args.trees)
    else:
        rows = 600 if args.rows is None else args.rows
        trees = 4 if args.trees is None else args.trees
        result = benchmark(rows=rows, trees=trees)
    print(json.dumps(result, sort_keys=True))
