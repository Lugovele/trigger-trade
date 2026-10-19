"""Bounded synthetic C1 splitter benchmark and frozen pre-optimization reference.

This module has no historical source reader or development-study entry point.
"""

from __future__ import annotations

from dataclasses import asdict
from math import ceil
from pathlib import Path
import json
import sys
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
    if not 12 <= rows <= 1500:
        raise ValueError("bounded synthetic row count must be in [12,1500]")
    states = tuple(tuple(float(((i * (j + 3) + i * i % 17) % (rows + 11)) / 31)
                         for j in range(comparator.FEATURE_COUNT)) for i in range(rows))
    labels = tuple((i * 7 + i // 13) % 3 for i in range(rows))
    return states, labels


def benchmark(*, rows: int = 600, trees: int = 4) -> dict:
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


if __name__ == "__main__":
    print(json.dumps(benchmark(), sort_keys=True))
