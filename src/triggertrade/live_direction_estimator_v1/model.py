"""Frozen, in-memory LDE V1 multinomial model. No source or label I/O."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
from math import isfinite, log, sqrt
import platform
from typing import Iterable

import numpy as np

from . import FEATURE_REGISTRY, SPEC_ID, SPEC_VERSION
from .preprocessing import PreprocessingState
from .source import SYMBOLS

CLASSES = ("LONG_FAVORED", "SHORT_FAVORED", "NO_DIRECTION")
LAMBDA = 0.01
Q_ID = "LDE_V1_CLASS_CENTERED_Q"
Q = np.array(((1 / sqrt(2), 1 / sqrt(6)),
              (-1 / sqrt(2), 1 / sqrt(6)),
              (0.0, -2 / sqrt(6))), dtype=np.float64)


class ModelError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class ModelFitRow:
    physical_symbol: str
    state: tuple[float, ...]
    label: str
    prediction_origin: datetime | None = None


@dataclass(frozen=True)
class RawPrediction:
    logits: tuple[float, float, float]
    log_probabilities: tuple[float, float, float]
    probabilities: tuple[float, float, float]


def _state(values: Iterable[float]) -> np.ndarray:
    a = np.asarray(tuple(values), dtype=np.float64)
    if a.shape != (32,) or not np.all(np.isfinite(a)):
        raise ValueError("32 finite processed state coordinates required")
    return a


def _log_probabilities(logits: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if logits.shape != (3,) or not np.all(np.isfinite(logits)):
        raise ModelError("NUMERICAL_PREDICTION_ERROR", "nonfinite logits")
    maximum = float(np.max(logits))
    shifted = logits - maximum
    logden_shifted = float(np.log(np.sum(np.exp(shifted), dtype=np.float64)))
    lp = shifted - logden_shifted
    p = np.exp(lp)
    if (not np.all(np.isfinite(lp)) or not np.all(np.isfinite(p)) or
            np.any(p < 0) or abs(float(np.sum(p)) - 1.0) > 1e-12):
        raise ModelError("NUMERICAL_PREDICTION_ERROR", "invalid probability simplex")
    return lp, p


def _cholesky_direction(hessian: np.ndarray, gradient: np.ndarray) -> np.ndarray:
    """Fixed-order binary64 Cholesky/triangular solves without BLAS threading."""
    dimension = len(gradient)
    lower = [[0.0] * dimension for _ in range(dimension)]
    for i in range(dimension):
        for j in range(i + 1):
            value = float(hessian[i, j])
            for k in range(j):
                value -= lower[i][k] * lower[j][k]
            if i == j:
                if not isfinite(value) or value <= 0:
                    raise ArithmeticError("Cholesky factorization failed")
                lower[i][j] = sqrt(value)
            else:
                lower[i][j] = value / lower[j][j]
    intermediate = [0.0] * dimension
    for i in range(dimension):
        value = -float(gradient[i])
        for k in range(i):
            value -= lower[i][k] * intermediate[k]
        intermediate[i] = value / lower[i][i]
    direction = [0.0] * dimension
    for i in range(dimension - 1, -1, -1):
        value = intermediate[i]
        for k in range(i + 1, dimension):
            value -= lower[k][i] * direction[k]
        direction[i] = value / lower[i][i]
    return np.asarray(direction, dtype=np.float64)


def _counts(rows: tuple[ModelFitRow, ...]) -> np.ndarray:
    counts = np.zeros((4, 3), dtype=np.int64)
    for row in rows:
        if row.physical_symbol not in SYMBOLS or row.label not in CLASSES:
            raise ValueError("invalid physical symbol or class")
        counts[SYMBOLS.index(row.physical_symbol), CLASSES.index(row.label)] += 1
    return counts


def _ordered(rows: Iterable[ModelFitRow], order: str) -> tuple[ModelFitRow, ...]:
    result = tuple(rows)
    if all(r.prediction_origin is not None for r in result):
        if any(r.prediction_origin.tzinfo is None or r.prediction_origin.utcoffset().total_seconds() != 0 for r in result):
            raise ValueError("origin must be UTC")
        result = tuple(sorted(result, key=lambda r: (r.prediction_origin, SYMBOLS.index(r.physical_symbol))))
        keys = [(r.prediction_origin, r.physical_symbol) for r in result]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate symbol-origin fit row")
    elif all(r.prediction_origin is None for r in result) and order == "SUPPLIED_CANONICAL":
        pass
    else:
        raise ValueError("provide all UTC origins or explicitly declare SUPPLIED_CANONICAL order")
    return result


def _objective(theta: np.ndarray, x: np.ndarray, symbols: np.ndarray, labels: np.ndarray,
               active_count: int, *, derivatives: bool) -> tuple[float, np.ndarray | None, np.ndarray | None]:
    """Mean NLL, exact state ridge, and optionally full Q-coordinate derivatives."""
    n = len(labels)
    d = active_count + 4
    w = theta.reshape(d, 2)
    loss = 0.0
    gradient = np.zeros((d, 2), dtype=np.float64) if derivatives else None
    hessian = np.zeros((2*d, 2*d), dtype=np.float64) if derivatives else None
    for i in range(n):
        f = np.zeros(d, dtype=np.float64)
        f[:active_count] = x[i]
        f[active_count + symbols[i]] = 1.0
        coordinates = [sum(float(f[j]) * float(w[j, c]) for j in range(d)) for c in range(2)]
        logits = np.asarray([sum(float(Q[k, c]) * coordinates[c] for c in range(2))
                             for k in range(3)], dtype=np.float64)
        maximum = float(np.max(logits))
        shifted = logits - maximum
        exp_shift = np.exp(shifted)
        denominator = float(np.sum(exp_shift, dtype=np.float64))
        loss += log(denominator) - float(shifted[labels[i]])
        if derivatives:
            prob = exp_shift / denominator
            residual = prob.copy()
            residual[labels[i]] -= 1.0
            residual_coordinates = [sum(float(residual[k]) * float(Q[k, c]) for k in range(3))
                                    for c in range(2)]
            gradient += np.outer(f, residual_coordinates) / n
            covariance = np.diag(prob) - np.outer(prob, prob)
            curvature = np.asarray([[sum(float(Q[k, a]) * float(covariance[k, l]) * float(Q[l, b])
                                         for k in range(3) for l in range(3)) for b in range(2)]
                                    for a in range(2)], dtype=np.float64)
            hessian += np.kron(np.outer(f, f), curvature) / n
    objective = loss / n + (LAMBDA / 2) * float(np.sum(w[:active_count] ** 2))
    if derivatives:
        gradient[:active_count] += LAMBDA * w[:active_count]
        for j in range(2*active_count):
            hessian[j, j] += LAMBDA
        return objective, gradient.ravel(), hessian
    return objective, None, None


@dataclass(frozen=True)
class ModelArtifact:
    spec_id: str
    spec_version: str
    horizon_minutes: int
    class_order: tuple[str, ...]
    feature_registry: str
    l2_lambda: float
    q_basis_id: str
    zero_slope_state_indices: tuple[int, ...]
    v: tuple[tuple[float, float], ...]
    b: tuple[tuple[float, float, float], ...]
    alpha_by_symbol: tuple[tuple[float, float, float], ...]
    indicator_differences: tuple[tuple[float, float, float], ...]
    objective: float
    gradient_infinity_norm: float
    iterations: int
    total_line_search_halvings: int
    maximum_line_search_halvings: int
    convergence_status: str
    counts_by_symbol_class: tuple[tuple[int, int, int], ...]
    row_order: str
    numerical_runtime: str
    preprocessing_fit_id: str | None
    preprocessing_membership_sha256: str | None

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), allow_nan=False)

    @classmethod
    def from_json(cls, data: str) -> ModelArtifact:
        d = json.loads(data)
        for key in ("class_order", "zero_slope_state_indices", "v", "b", "alpha_by_symbol",
                    "indicator_differences", "counts_by_symbol_class"):
            if key in ("v", "b", "alpha_by_symbol", "indicator_differences", "counts_by_symbol_class"):
                d[key] = tuple(tuple(a) for a in d[key])
            else:
                d[key] = tuple(d[key])
        result = cls(**d)
        if (result.spec_id != SPEC_ID or result.spec_version != SPEC_VERSION or
                result.class_order != CLASSES or result.feature_registry != FEATURE_REGISTRY or
                result.l2_lambda != LAMBDA or result.q_basis_id != Q_ID or
                len(result.v) != 32 or len(result.b) != 32 or len(result.alpha_by_symbol) != 4):
            raise ValueError("incompatible model artifact")
        return result

    def raw_prediction(self, physical_symbol: str, state: Iterable[float]) -> RawPrediction:
        if physical_symbol not in SYMBOLS:
            raise ValueError("unsupported physical symbol")
        x = _state(state)
        intercept = self.alpha_by_symbol[SYMBOLS.index(physical_symbol)]
        logits = np.asarray([intercept[k] + sum(float(x[j]) * self.b[j][k] for j in range(32))
                             for k in range(3)], dtype=np.float64)
        lp, p = _log_probabilities(logits)
        return RawPrediction(tuple(float(v) for v in logits), tuple(float(v) for v in lp),
                             tuple(float(v) for v in p))

    def raw_batch(self, rows: Iterable[tuple[str, Iterable[float]]]) -> tuple[RawPrediction, ...]:
        return tuple(self.raw_prediction(symbol, state) for symbol, state in rows)


def fit_model(rows: Iterable[ModelFitRow], *, horizon_minutes: int,
              preprocessing: PreprocessingState | None = None,
              zero_slope_state_indices: Iterable[int] | None = None,
              order: str = "ORIGIN_SYMBOL") -> ModelArtifact:
    """Fit only caller-supplied processed base rows; no corpus access."""
    if horizon_minutes not in (60, 120):
        raise ValueError("horizon must be 60 or 120")
    if preprocessing is not None:
        if preprocessing.horizon_minutes != horizon_minutes or preprocessing.registry != FEATURE_REGISTRY:
            raise ValueError("incompatible preprocessing state")
        if zero_slope_state_indices is not None:
            raise ValueError("choose preprocessing metadata or explicit synthetic mask")
        zero_slope_state_indices = preprocessing.zero_slope_state_indices
    elif zero_slope_state_indices is None:
        raise ValueError("preprocessing constant-column metadata or explicit synthetic mask required")
    zero = tuple(sorted(set(zero_slope_state_indices or ())))
    if any(j < 1 or j > 32 for j in zero):
        raise ValueError("invalid one-based constant state index")
    fit_rows = _ordered(rows, order)
    counts = _counts(fit_rows)
    if np.any(counts == 0):
        raise ModelError("MODEL_NOT_ESTIMABLE", "each symbol needs every class")
    active = tuple(j for j in range(32) if j + 1 not in zero)
    states = np.asarray([_state(r.state) for r in fit_rows], dtype=np.float64)
    observed_zero = tuple(j + 1 for j in range(32) if np.all(states[:, j] == states[0, j]))
    if observed_zero != zero:
        raise ValueError("constant-column mask does not match supplied fit rows")
    if preprocessing is not None:
        pooled_counts = {d.count for d in preprocessing.domains if d.group == "P"}
        if pooled_counts != {len(fit_rows)}:
            raise ValueError("model and preprocessing base-row counts differ")
    x = states[:, active] if active else np.zeros((len(fit_rows), 0), dtype=np.float64)
    symbols = np.asarray([SYMBOLS.index(r.physical_symbol) for r in fit_rows], dtype=np.int64)
    labels = np.asarray([CLASSES.index(r.label) for r in fit_rows], dtype=np.int64)
    w = np.zeros((len(active) + 4, 2), dtype=np.float64)
    for s in range(4):
        frequencies = counts[s] / np.sum(counts[s])
        log_frequencies = np.log(frequencies)
        centered = log_frequencies - np.mean(log_frequencies)
        w[len(active) + s] = [sum(float(Q[k, c]) * float(centered[k]) for k in range(3))
                              for c in range(2)]
    theta = w.ravel()
    total_halvings = maximum_halvings = 0
    try:
        for iteration in range(1001):
            objective, gradient, hessian = _objective(theta, x, symbols, labels, len(active), derivatives=True)
            if (not isfinite(objective) or not np.all(np.isfinite(gradient)) or
                    not np.all(np.isfinite(hessian))):
                raise ArithmeticError("nonfinite objective/derivative")
            norm = float(np.max(np.abs(gradient)))
            if norm <= 1e-8:
                break
            if iteration == 1000:
                raise ArithmeticError("Newton iteration limit")
            direction = _cholesky_direction(hessian, gradient)
            directional = sum(float(gradient[j]) * float(direction[j]) for j in range(len(gradient)))
            if not np.all(np.isfinite(direction)) or not isfinite(directional) or directional >= 0:
                raise ArithmeticError("invalid Newton direction")
            for halvings in range(61):
                step = 2.0 ** -halvings
                candidate = theta + step * direction
                candidate_objective, _, _ = _objective(candidate, x, symbols, labels, len(active), derivatives=False)
                if isfinite(candidate_objective) and candidate_objective <= objective + 1e-4 * step * directional:
                    theta = candidate
                    total_halvings += halvings
                    maximum_halvings = max(maximum_halvings, halvings)
                    break
            else:
                raise ArithmeticError("Armijo line search failed")
        fitted = theta.reshape(len(active) + 4, 2)
        v = np.zeros((32, 2), dtype=np.float64)
        v[list(active)] = fitted[:len(active)]
        b = np.asarray([[sum(float(v[j, c]) * float(Q[k, c]) for c in range(2))
                         for k in range(3)] for j in range(32)], dtype=np.float64)
        alpha = np.asarray([[sum(float(fitted[len(active) + s, c]) * float(Q[k, c]) for c in range(2))
                             for k in range(3)] for s in range(4)], dtype=np.float64)
        differences = alpha[1:] - alpha[0]
        return ModelArtifact(SPEC_ID, SPEC_VERSION, horizon_minutes, CLASSES, FEATURE_REGISTRY,
                             LAMBDA, Q_ID, zero, tuple(map(tuple, v.tolist())),
                             tuple(map(tuple, b.tolist())), tuple(map(tuple, alpha.tolist())),
                             tuple(map(tuple, differences.tolist())), float(objective), norm,
                             iteration, total_halvings, maximum_halvings, "CONVERGED",
                             tuple(map(tuple, counts.tolist())), order if fit_rows[0].prediction_origin is None else "ORIGIN_SYMBOL",
                             f"Python {platform.python_version()}; NumPy {np.__version__}; binary64; "
                             "fixed-order Python Cholesky; BLAS/LAPACK unused; sequential rows",
                             preprocessing.fit_id if preprocessing else None,
                             preprocessing.membership_sha256 if preprocessing else None)
    except (ArithmeticError, FloatingPointError, OverflowError) as exc:
        raise ModelError("FIT_FAILED", str(exc)) from exc
