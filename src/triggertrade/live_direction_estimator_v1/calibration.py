"""One bounded scalar inverse temperature per independent horizon."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from math import isfinite, log
from typing import Iterable

import numpy as np

from . import SPEC_ID, SPEC_VERSION
from .model import CLASSES, ModelError, RawPrediction, _log_probabilities
from .source import SYMBOLS


@dataclass(frozen=True)
class CalibrationRow:
    physical_symbol: str
    logits: tuple[float, float, float]
    label: str


@dataclass(frozen=True)
class CalibratedPrediction:
    logits: tuple[float, float, float]
    log_probabilities: tuple[float, float, float]
    probabilities: tuple[float, float, float]
    predicted_class: str
    confidence: float


def hard_class(scores: Iterable[float]) -> str:
    z = tuple(scores)
    if len(z) != 3 or not all(isfinite(v) for v in z):
        raise ModelError("NUMERICAL_PREDICTION_ERROR", "invalid class scores")
    maximum = max(z)
    for i in (2, 0, 1):
        if z[i] == maximum:
            return CLASSES[i]
    raise AssertionError("unreachable")


def _loss_derivative(logits: np.ndarray, labels: np.ndarray, t: float) -> tuple[float, float]:
    loss = derivative = 0.0
    for z, y in zip(logits, labels):
        relative_z = z - float(np.max(z))
        scaled = t * relative_z
        maximum = float(np.max(scaled))
        shifted = scaled - maximum
        exp_shift = np.exp(shifted)
        denominator = float(np.sum(exp_shift, dtype=np.float64))
        prob = exp_shift / denominator
        loss += log(denominator) - float(shifted[y])
        derivative += float(prob @ relative_z) - float(relative_z[y])
    return loss / len(labels), derivative / len(labels)


@dataclass(frozen=True)
class ScalarCalibrator:
    spec_id: str
    spec_version: str
    horizon_minutes: int
    inverse_temperature: float
    status: str
    boundary_flag: str | None
    calibration_nll: float
    row_count: int
    counts_by_symbol_class: tuple[tuple[int, int, int], ...]
    bisections: int
    bracket_width: float

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), allow_nan=False)

    @classmethod
    def from_json(cls, data: str) -> ScalarCalibrator:
        d = json.loads(data)
        d["counts_by_symbol_class"] = tuple(tuple(v) for v in d["counts_by_symbol_class"])
        result = cls(**d)
        if (result.spec_id != SPEC_ID or result.spec_version != SPEC_VERSION or
                result.horizon_minutes not in (60, 120) or
                not 0.05 <= result.inverse_temperature <= 20):
            raise ValueError("incompatible calibrator artifact")
        return result

    def predict(self, raw_logits: Iterable[float] | RawPrediction) -> CalibratedPrediction:
        z = np.asarray(tuple(raw_logits.logits if isinstance(raw_logits, RawPrediction) else raw_logits), dtype=np.float64)
        with np.errstate(over="ignore", invalid="ignore"):
            scaled = self.inverse_temperature * z
        if scaled.shape != (3,) or not np.all(np.isfinite(scaled)):
            raise ModelError("NUMERICAL_PREDICTION_ERROR", "nonfinite calibrated logits")
        relative_scaled = self.inverse_temperature * (z - float(np.max(z)))
        lp, p = _log_probabilities(relative_scaled)
        return CalibratedPrediction(tuple(float(v) for v in scaled), tuple(float(v) for v in lp),
                                    tuple(float(v) for v in p), hard_class(relative_scaled), float(np.max(p)))


def fit_scalar_calibrator(rows: Iterable[CalibrationRow], *, horizon_minutes: int) -> ScalarCalibrator:
    if horizon_minutes not in (60, 120):
        raise ValueError("horizon must be 60 or 120")
    data = tuple(rows)
    if not data:
        raise ModelError("CALIBRATION_FAILED", "empty calibration population")
    counts = np.zeros((4, 3), dtype=np.int64)
    for row in data:
        if row.physical_symbol not in SYMBOLS or row.label not in CLASSES:
            raise ValueError("invalid symbol or class")
        counts[SYMBOLS.index(row.physical_symbol), CLASSES.index(row.label)] += 1
    z = np.asarray([r.logits for r in data], dtype=np.float64)
    if z.shape != (len(data), 3) or not np.all(np.isfinite(z)):
        raise ModelError("CALIBRATION_FAILED", "nonfinite or malformed logits")
    y = np.asarray([CLASSES.index(r.label) for r in data], dtype=np.int64)
    try:
        bisections = 0
        width = 0.0
        boundary = None
        if np.all(z[:, 0] == z[:, 1]) and np.all(z[:, 1] == z[:, 2]):
            t, status = 1.0, "FLAT_CALIBRATOR"
        else:
            low, high = 0.05, 20.0
            _, dlow = _loss_derivative(z, y, low)
            if not isfinite(dlow):
                raise ArithmeticError("nonfinite derivative")
            if dlow >= 0:
                t, status, boundary = low, "LOWER_BOUND", "LOWER_BOUND"
            else:
                _, dhigh = _loss_derivative(z, y, high)
                if not isfinite(dhigh):
                    raise ArithmeticError("nonfinite derivative")
                if dhigh <= 0:
                    t, status, boundary = high, "UPPER_BOUND", "UPPER_BOUND"
                else:
                    status = "INTERIOR"
                    exact = None
                    while high - low > 1e-10 and bisections < 100:
                        middle = (low + high) / 2
                        _, derivative = _loss_derivative(z, y, middle)
                        if not isfinite(derivative):
                            raise ArithmeticError("nonfinite derivative")
                        bisections += 1
                        if derivative == 0:
                            exact = middle
                            break
                        if derivative < 0:
                            low = middle
                        else:
                            high = middle
                    width = 0.0 if exact is not None else high - low
                    if exact is None and width > 1e-10:
                        raise ArithmeticError("bisection did not converge")
                    t = exact if exact is not None else (low + high) / 2
        nll, derivative = _loss_derivative(z, y, t)
        if not isfinite(nll) or not isfinite(derivative):
            raise ArithmeticError("nonfinite fitted calibration")
        return ScalarCalibrator(SPEC_ID, SPEC_VERSION, horizon_minutes, t, status, boundary,
                                nll, len(data), tuple(map(tuple, counts.tolist())), bisections, width)
    except (ArithmeticError, FloatingPointError, OverflowError) as exc:
        raise ModelError("CALIBRATION_FAILED", str(exc)) from exc
