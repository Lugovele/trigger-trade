"""The single registered report-only fitted comparator, C1_SHALLOW_RF.

All inputs are caller-supplied sealed Phase 7 rows. This module has no source,
target, primary-fit, evaluation-gate, or prospective scheduling entry point.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
from math import ceil, isfinite, log
import platform
from typing import Callable, Iterable

import numpy as np

from . import FEATURE_REGISTRY, SPEC_ID, SPEC_VERSION
from .calibration import CalibratedPrediction, CalibrationRow, ScalarCalibrator, fit_scalar_calibrator
from .evaluation_bootstrap import randint_raw
from .features import GROUPS, NAMES
from .manifests import RowManifest, RowMetadata, canonical_json, digest
from .model import CLASSES
from .orchestration import FitBundle, ScoredRow, _assert_manifest
from .preprocessing import transform
from .report_only_matching import matched_primary_rows

COMPARATOR_ID = "C1_SHALLOW_RF"
TREES = 256
MAX_DEPTH = 4
NODE_FEATURES = 5
FEATURE_COUNT = 35
PRIOR_CONCENTRATION = 3.0
SEED_BASE = 20261017
REGISTRY_DESCRIPTOR = {"id": FEATURE_REGISTRY, "ordered_names": NAMES,
                       "scaling_groups": GROUPS,
                       "feature_calculation_version": "LDE_V1_ADJ35_U1M_PY_MATH_V1",
                       "btc_context_mask_indices": tuple(range(24, 31))}


@dataclass(frozen=True)
class TreeNode:
    path: str
    depth: int
    counts: tuple[int, int, int]
    probabilities: tuple[float, float, float] | None = None
    feature_index: int | None = None  # one-based registry index
    cut: float | None = None
    gain: float | None = None
    left: TreeNode | None = None
    right: TreeNode | None = None

    @property
    def terminal(self) -> bool:
        return self.probabilities is not None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> TreeNode:
        data = dict(value)
        data["counts"] = tuple(data["counts"])
        if data["probabilities"] is not None:
            data["probabilities"] = tuple(data["probabilities"])
        for side in ("left", "right"):
            if data[side] is not None:
                data[side] = cls.from_dict(data[side])
        return cls(**data)


def min_leaf_rows(n_base: int) -> int:
    if n_base <= 0:
        raise ValueError("nonempty base population required")
    return max(1, ceil(0.01 * n_base))


def sample_features(random_index: Callable[[int], int]) -> tuple[int, ...]:
    """The registered 1..35 partial Fisher-Yates draw, reset at every node."""
    selected = list(range(1, FEATURE_COUNT + 1))
    for k in range(NODE_FEATURES):
        offset = random_index(FEATURE_COUNT - k)
        if not 0 <= offset < FEATURE_COUNT - k:
            raise ValueError("invalid RandInt output")
        other = k + offset
        selected[k], selected[other] = selected[other], selected[k]
    return tuple(sorted(selected[:NODE_FEATURES]))


def split_cut(lower: float, upper: float) -> float:
    """Binary64 midpoint, retaining the cut after lower on endpoint rounding."""
    if not isfinite(lower) or not isfinite(upper) or lower >= upper:
        raise ValueError("strictly increasing finite distinct values required")
    difference = upper - lower
    middle = lower + difference / 2 if isfinite(difference) else lower / 2 + upper / 2
    return lower if middle <= lower or middle >= upper else middle


def _counts(indices: tuple[int, ...], labels: tuple[int, ...]) -> tuple[int, int, int]:
    return tuple(sum(labels[i] == c for i in indices) for c in range(3))


def gini(counts: tuple[int, int, int]) -> float:
    n = sum(counts)
    if n == 0:
        raise ValueError("empty node")
    return 1.0 - sum((count / n) ** 2 for count in counts)


def gini_gain(parent: tuple[int, int, int], left: tuple[int, int, int],
              right: tuple[int, int, int]) -> float:
    n = sum(parent)
    return gini(parent) - (sum(left) / n) * gini(left) - (sum(right) / n) * gini(right)


def pooled_prior(labels: tuple[int, ...]) -> tuple[float, float, float]:
    n = len(labels)
    if n == 0:
        raise ValueError("empty comparator base")
    return tuple((sum(y == c for y in labels) + 0.5) / (n + 1.5) for c in range(3))


def leaf_probabilities(counts: tuple[int, int, int], prior: tuple[float, float, float]
                       ) -> tuple[float, float, float]:
    n = sum(counts)
    return tuple((counts[c] + PRIOR_CONCENTRATION * prior[c]) /
                 (n + PRIOR_CONCENTRATION) for c in range(3))


def _best_split(states: tuple[tuple[float, ...], ...], labels: tuple[int, ...],
                indices: tuple[int, ...], candidates: tuple[int, ...], minimum: int,
                parent: tuple[int, int, int]
                ) -> tuple[int, float, float, tuple[int, ...], tuple[int, ...]] | None:
    best = None
    for feature in candidates:  # sorted one-based feature indices
        column = feature - 1
        # Keep the reference set's representative for equal values (notably
        # -0.0/+0.0), so even a cut rounded to an endpoint is bit-identical.
        values = sorted({states[i][column] for i in indices})
        ordered = sorted(indices, key=lambda i: states[i][column])
        left_counts = [0, 0, 0]
        distinct = 0
        for position, row_index in enumerate(ordered[:-1]):
            left_counts[labels[row_index]] += 1
            if states[row_index][column] == states[ordered[position + 1]][column]:
                continue
            left_size = position + 1
            right_size = len(indices) - left_size
            lower, upper = values[distinct], values[distinct + 1]
            distinct += 1
            if left_size < minimum or right_size < minimum:
                continue
            cut = split_cut(lower, upper)
            left = tuple(left_counts)
            right = tuple(parent[c] - left[c] for c in range(3))
            gain = gini_gain(parent, left, right)
            if gain <= 0:
                continue
            if (best is None or gain > best[2] or
                    (gain == best[2] and (feature, cut) < (best[0], best[1]))):
                best = feature, cut, gain
    if best is None:
        return None
    feature, cut, gain = best
    left = tuple(i for i in indices if states[i][feature - 1] <= cut)
    right = tuple(i for i in indices if states[i][feature - 1] > cut)
    return feature, cut, gain, left, right


def _grow(states: tuple[tuple[float, ...], ...], labels: tuple[int, ...],
          indices: tuple[int, ...], depth: int, path: str, minimum: int,
          prior: tuple[float, float, float], random_index: Callable[[int], int]) -> TreeNode:
    counts = _counts(indices, labels)
    if depth == MAX_DEPTH or sum(c > 0 for c in counts) == 1 or len(indices) < 2 * minimum:
        return TreeNode(path, depth, counts, leaf_probabilities(counts, prior))
    candidates = sample_features(random_index)
    winning = _best_split(states, labels, indices, candidates, minimum, counts)
    if winning is None:
        return TreeNode(path, depth, counts, leaf_probabilities(counts, prior))
    feature, cut, gain, left, right = winning
    # Python evaluates left first: registered depth-first, left-before-right RNG traversal.
    left_node = _grow(states, labels, left, depth + 1, path + "L", minimum, prior, random_index)
    right_node = _grow(states, labels, right, depth + 1, path + "R", minimum, prior, random_index)
    return TreeNode(path, depth, counts, None, feature, cut, gain, left_node, right_node)


def _leaf(node: TreeNode, values: tuple[float, ...]) -> tuple[float, float, float]:
    while not node.terminal:
        node = node.left if values[node.feature_index - 1] <= node.cut else node.right
    return node.probabilities


@dataclass(frozen=True)
class ComparatorPrediction:
    raw_probabilities: tuple[float, float, float]
    raw_log_probabilities: tuple[float, float, float]
    raw_logits: tuple[float, float, float]
    calibrated: CalibratedPrediction
    comparator_sha256: str


@dataclass(frozen=True)
class ComparatorArtifact:
    spec_id: str
    spec_version: str
    comparator_id: str
    horizon_minutes: int
    fit_id: str
    feature_registry: str
    feature_registry_sha256: str
    preprocessing_sha256: str
    base_manifest_sha256: str
    calibration_manifest_sha256: str
    primary_bundle_sha256: str
    tree_count: int
    maximum_depth: int
    minimum_leaf_rows: int
    node_candidate_features: int
    row_sampling: str
    class_weighting: str
    sample_weighting: str
    pooled_training_prior: tuple[float, float, float]
    rng_generator: str
    rng_seed: int
    numerical_runtime: str
    creation_identity: str
    trees: tuple[TreeNode, ...]
    calibrator: ScalarCalibrator
    calibrator_sha256: str
    fit_status: str
    artifact_sha256: str

    def body(self) -> dict[str, object]:
        result = asdict(self)
        result.pop("artifact_sha256")
        return result

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    @classmethod
    def from_json(cls, text: str) -> ComparatorArtifact:
        data = json.loads(text)
        data["pooled_training_prior"] = tuple(data["pooled_training_prior"])
        data["trees"] = tuple(TreeNode.from_dict(tree) for tree in data["trees"])
        data["calibrator"] = ScalarCalibrator.from_json(canonical_json(data["calibrator"]))
        result = cls(**data)
        result.verify()
        return result

    def verify(self) -> None:
        if (self.spec_id != SPEC_ID or self.spec_version != SPEC_VERSION or
                self.comparator_id != COMPARATOR_ID or self.feature_registry != FEATURE_REGISTRY or
                self.feature_registry_sha256 != digest(REGISTRY_DESCRIPTOR) or
                self.horizon_minutes not in (60, 120) or self.tree_count != TREES or
                len(self.trees) != TREES or self.maximum_depth != MAX_DEPTH or
                self.node_candidate_features != NODE_FEATURES or self.row_sampling != "NONE" or
                self.class_weighting != "NONE" or self.sample_weighting != "NONE" or
                self.rng_generator != "NumPy 2.2.5 PCG64.random_raw" or
                self.rng_seed != SEED_BASE + self.horizon_minutes or self.fit_status != "FITTED" or
                self.minimum_leaf_rows != min_leaf_rows(sum(self.trees[0].counts)) or
                any(sum(tree.counts) != sum(self.trees[0].counts) for tree in self.trees) or
                self.calibrator.horizon_minutes != self.horizon_minutes or
                self.calibrator_sha256 != digest(json.loads(self.calibrator.to_json())) or
                self.artifact_sha256 != digest(self.body())):
            raise ValueError("comparator artifact identity or contract mismatch")

    def predict(self, values: Iterable[float]) -> ComparatorPrediction:
        self.verify()
        state = tuple(float(v) for v in values)
        if len(state) != FEATURE_COUNT or not all(isfinite(v) for v in state):
            raise ValueError("35 finite primary-processed columns required")
        probabilities = tuple(sum(_leaf(tree, state)[c] for tree in self.trees) / TREES
                              for c in range(3))
        if any(not isfinite(p) or p <= 0 for p in probabilities):
            raise ArithmeticError("forest probability is not strictly positive")
        logits = tuple(log(p) for p in probabilities)
        return ComparatorPrediction(probabilities, logits, logits,
                                    self.calibrator.predict(logits), self.artifact_sha256)


@dataclass(frozen=True)
class ComparatorScoredRow:
    prediction_origin: str
    physical_symbol: str
    horizon_minutes: int
    primary_score_manifest_sha256: str
    prediction: ComparatorPrediction


def fit_comparator(*, primary: FitBundle, base_manifest: RowManifest,
                   calibration_manifest: RowManifest, base_rows: Iterable[RowMetadata],
                   calibration_rows: Iterable[RowMetadata],
                   progress: Callable[[int, int], None] | None = None) -> ComparatorArtifact:
    """Fit only the primary's exact base and month using its frozen preprocessing."""
    primary.verify_hashes()
    parent = primary.manifest
    if (base_manifest.segment_type != "BASE" or calibration_manifest.segment_type != "CALIBRATION" or
            parent.fit_id != base_manifest.fit_id or parent.fit_id != calibration_manifest.fit_id or
            parent.horizon_minutes != base_manifest.horizon_minutes or
            parent.horizon_minutes != calibration_manifest.horizon_minutes or
            parent.base_manifest_sha256 != base_manifest.manifest_sha256 or
            parent.calibration_manifest_sha256 != calibration_manifest.manifest_sha256):
        raise ValueError("comparator requires exact primary fit populations")
    base = _assert_manifest(base_manifest, tuple(base_rows))
    calibration = _assert_manifest(calibration_manifest, tuple(calibration_rows))
    n = len(base)
    if n == 0:
        raise ValueError("empty comparator base")
    states = tuple(transform(r.feature_row, primary.preprocessing).values for r in base)
    labels = tuple(CLASSES.index(r.canonical_class) for r in base)
    prior = pooled_prior(labels)
    if np.__version__ != "2.2.5":
        raise RuntimeError("registered comparator requires NumPy 2.2.5 PCG64")
    seed = SEED_BASE + parent.horizon_minutes
    generator = np.random.PCG64(seed)  # Reset for every independent fit.
    random_index = lambda m: randint_raw(generator.random_raw, m)
    minimum = min_leaf_rows(n)
    indices = tuple(range(n))
    built_trees = []
    for tree_index in range(TREES):
        built_trees.append(_grow(states, labels, indices, 0, "", minimum, prior, random_index))
        if progress is not None and (tree_index + 1) % 16 == 0:
            progress(tree_index + 1, TREES)
    trees = tuple(built_trees)

    def raw_logits(values: tuple[float, ...]) -> tuple[float, float, float]:
        probability = tuple(sum(_leaf(tree, values)[c] for tree in trees) / TREES
                            for c in range(3))
        return tuple(log(p) for p in probability)

    cal_rows = tuple(CalibrationRow(r.physical_symbol,
        raw_logits(transform(r.feature_row, primary.preprocessing).values), r.canonical_class)
        for r in calibration)
    calibrator = fit_scalar_calibrator(cal_rows, horizon_minutes=parent.horizon_minutes)
    provisional = ComparatorArtifact(
        SPEC_ID, SPEC_VERSION, COMPARATOR_ID, parent.horizon_minutes, parent.fit_id,
        FEATURE_REGISTRY, digest(REGISTRY_DESCRIPTOR), parent.preprocessing_sha256,
        base_manifest.manifest_sha256, calibration_manifest.manifest_sha256,
        parent.bundle_sha256, TREES, MAX_DEPTH, minimum, NODE_FEATURES,
        "NONE", "NONE", "NONE", prior, "NumPy 2.2.5 PCG64.random_raw", seed,
        f"Python {platform.python_version()}; NumPy {np.__version__}; binary64",
        digest({"role": COMPARATOR_ID, "primary_bundle": parent.bundle_sha256}),
        trees, calibrator, digest(json.loads(calibrator.to_json())), "FITTED", "")
    artifact = replace(provisional, artifact_sha256=digest(provisional.body()))
    artifact.verify()
    return artifact


def score_comparator(artifact: ComparatorArtifact, *, primary: FitBundle,
                     scored_manifest: RowManifest, scored_rows: Iterable[RowMetadata],
                     primary_scored_rows: Iterable[ScoredRow]
                     ) -> tuple[ComparatorScoredRow, ...]:
    """Score only sealed primary SCORE keys; no native-coverage substitution."""
    if (scored_manifest.segment_type != "SCORE" or
            scored_manifest.fit_id != artifact.fit_id or
            scored_manifest.horizon_minutes != artifact.horizon_minutes or
            primary.manifest.bundle_sha256 != artifact.primary_bundle_sha256 or
            primary.manifest.preprocessing_sha256 != artifact.preprocessing_sha256):
        raise ValueError("matched primary SCORE manifest and preprocessing required")
    artifact.verify()
    matched = matched_primary_rows(primary=primary, scored_manifest=scored_manifest,
        scored_rows=scored_rows, primary_scored_rows=primary_scored_rows)
    return tuple(ComparatorScoredRow(member.prediction_origin, row.physical_symbol,
        artifact.horizon_minutes, scored_manifest.manifest_sha256,
        artifact.predict(transform(row.feature_row, primary.preprocessing).values))
        for row, member in matched)
