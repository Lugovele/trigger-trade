"""Bounded synthetic Phase 6 conformance; no historical corpus or fold execution."""

from __future__ import annotations

from dataclasses import replace
from math import exp, isclose, log

import numpy as np
import pytest

from triggertrade.live_direction_estimator_v1.baselines import (B0State, B1State, B3State, BaselineFitRow, BaselineState,
                                                                 b2_trailing_h_sign, fit_baselines)
from triggertrade.live_direction_estimator_v1.calibration import (CalibrationRow, ScalarCalibrator, _loss_derivative,
                                                                   fit_scalar_calibrator, hard_class)
from triggertrade.live_direction_estimator_v1.model import (CLASSES, LAMBDA, Q, ModelArtifact,
                                                             ModelError, ModelFitRow, _log_probabilities, _objective,
                                                             fit_model)
from triggertrade.live_direction_estimator_v1.source import SYMBOLS


def rows():
    # Six per symbol, all classes represented; columns 2–32 exactly constant.
    return tuple(ModelFitRow(s, (float(i % 3 - 1),) + (0.0,) * 31, CLASSES[i % 3])
                 for s in SYMBOLS for i in range(6))


MASK = tuple(range(2, 33))


def model():
    return fit_model(rows(), horizon_minutes=60, zero_slope_state_indices=MASK,
                     order="SUPPLIED_CANONICAL")


def test_q_gauge_objective_and_ridge_mask():
    m = model()
    assert m.l2_lambda == LAMBDA == 0.01
    assert np.allclose(Q.T @ Q, np.eye(2), atol=1e-15)
    assert all(abs(sum(b)) < 1e-15 for b in m.b)
    assert all(abs(sum(a)) < 1e-15 for a in m.alpha_by_symbol)
    assert m.b[0][0] != -m.b[0][1]  # No forced LONG/SHORT symmetry.
    assert all(m.b[j] == (0.0, 0.0, 0.0) for j in range(1, 32))
    theta = np.array([0.4, -0.2, 0.1, 0.3, 0, 0, 0, 0, 0, 0], dtype=np.float64)
    x = np.array([[2.0]], dtype=np.float64)
    symbols = np.array([0], dtype=np.int64)
    labels = np.array([1], dtype=np.int64)
    objective, gradient, hessian = _objective(theta, x, symbols, labels, 1, derivatives=True)
    z = Q @ (theta[:2] * 2 + theta[2:4])
    expected = log(sum(exp(float(v)) for v in z)) - z[1] + 0.005 * sum(theta[:2] ** 2)
    assert isclose(objective, expected, abs_tol=1e-14)
    assert hessian[0, 0] > 0 and np.all(np.isfinite(gradient))
    # Adding an unpenalized symbol intercept changes only NLL, not ridge.
    shifted = theta.copy()
    shifted[2] += 0.2
    changed, _, _ = _objective(shifted, x, symbols, labels, 1, derivatives=False)
    assert changed != objective
    # Two-row sum form must scale ridge by N, unlike a library default penalty.
    x2 = np.array([[2.0], [-1.0]], dtype=np.float64)
    y2 = np.array([1, 0], dtype=np.int64)
    mean_objective, _, _ = _objective(theta, x2, np.array([0, 0]), y2, 1, derivatives=False)
    logits2 = [Q @ (theta[:2] * value + theta[2:4]) for value in (2.0, -1.0)]
    sum_loss = sum(log(sum(exp(float(v)) for v in logits2[i])) - logits2[i][y2[i]]
                   for i in range(2))
    sum_objective = sum_loss + (LAMBDA * 2 / 2) * sum(theta[:2] ** 2)
    assert isclose(mean_objective * 2, sum_objective, abs_tol=1e-14)


def test_estimability_and_newton_determinism_and_prediction():
    with pytest.raises(ModelError, match="MODEL_NOT_ESTIMABLE"):
        fit_model(rows()[:18], horizon_minutes=60, zero_slope_state_indices=MASK,
                  order="SUPPLIED_CANONICAL")
    m = model()
    assert m.convergence_status == "CONVERGED" and m.gradient_infinity_norm <= 1e-8
    assert m.to_json() == model().to_json()
    p = m.raw_prediction("BTCUSDT", (0.0,) * 32)
    assert isclose(sum(p.probabilities), 1.0, abs_tol=1e-12)
    assert m.raw_batch((("BTCUSDT", (0.0,) * 32),))[0] == p
    assert ModelArtifact.from_json(m.to_json()).raw_prediction("BTCUSDT", (0.0,) * 32) == p


def test_large_logit_stability_and_calibrated_ties():
    m = model()
    large = replace(m, alpha_by_symbol=((1000.0, -1000.0, -1000.0),) + m.alpha_by_symbol[1:])
    p = large.raw_prediction("BTCUSDT", (0.0,) * 32)
    assert all(np.isfinite(p.log_probabilities))
    assert p.probabilities[1] == 0.0
    assert isclose(sum(p.probabilities), 1.0, abs_tol=1e-12)
    assert hard_class((2, 2, 1)) == CLASSES[0]
    assert hard_class((2, 1, 2)) == CLASSES[2]
    assert hard_class((1, 2, 2)) == CLASSES[2]
    assert hard_class((2, 2, 2)) == CLASSES[2]
    shifted_logp, shifted_p = _log_probabilities(np.array([1e16 + 4, 1e16 + 2, 1e16]))
    reference_logp, reference_p = _log_probabilities(np.array([4.0, 2.0, 0.0]))
    assert np.array_equal(shifted_logp, reference_logp)
    assert np.array_equal(shifted_p, reference_p)
    shifted_loss, shifted_derivative = _loss_derivative(np.array([[1e16 + 4, 1e16 + 2, 1e16]]),
                                                       np.array([0]), 1.0)
    reference_loss, reference_derivative = _loss_derivative(np.array([[4.0, 2.0, 0.0]]),
                                                           np.array([0]), 1.0)
    assert (shifted_loss, shifted_derivative) == (reference_loss, reference_derivative)
    large_cal = replace(fit_scalar_calibrator((CalibrationRow("BTCUSDT", (1, 1, 1), CLASSES[0]),),
                                              horizon_minutes=60), inverse_temperature=20.0)
    assert large_cal.predict((1e16 + 4, 1e16 + 2, 1e16)).predicted_class == CLASSES[0]
    assert large_cal.predict((1e16 + 4, 1e16 + 2, 1e16)).probabilities == large_cal.predict((4, 2, 0)).probabilities
    with pytest.raises(ModelError, match="NUMERICAL_PREDICTION_ERROR"):
        large_cal.predict((1e308, 1e308, 1e308))


def test_scalar_calibration_flat_bounds_interior_and_roundtrip():
    flat = fit_scalar_calibrator((CalibrationRow("BTCUSDT", (4, 4, 4), CLASSES[0]),), horizon_minutes=60)
    assert flat.inverse_temperature == 1 and flat.status == "FLAT_CALIBRATOR"
    lower = fit_scalar_calibrator((CalibrationRow("BTCUSDT", (5, 0, 0), CLASSES[1]),), horizon_minutes=60)
    upper = fit_scalar_calibrator((CalibrationRow("BTCUSDT", (5, 0, 0), CLASSES[0]),), horizon_minutes=60)
    assert (lower.inverse_temperature, lower.boundary_flag) == (0.05, "LOWER_BOUND")
    assert (upper.inverse_temperature, upper.boundary_flag) == (20, "UPPER_BOUND")
    # Derivative at t=1 is zero: two LONG labels in three rows, p_LONG=2/3.
    gap = log(4.0)
    interior = fit_scalar_calibrator((CalibrationRow("BTCUSDT", (gap, 0, 0), CLASSES[0]),
                                      CalibrationRow("AVAXUSDT", (gap, 0, 0), CLASSES[0]),
                                      CalibrationRow("SUIUSDT", (gap, 0, 0), CLASSES[1])),
                                     horizon_minutes=120)
    assert abs(interior.inverse_temperature - 1) < 1e-8
    assert ScalarCalibrator.from_json(interior.to_json()).predict((1.0, 0.0, -1.0)) == interior.predict((1.0, 0.0, -1.0))
    assert interior.predict((2.0, 2.0, 1.0)).predicted_class == CLASSES[0]
    with pytest.raises(ModelError, match="CALIBRATION_FAILED"):
        fit_scalar_calibrator((), horizon_minutes=60)


def test_baselines_exact_counts_empty_bin_and_roundtrip():
    data = tuple(BaselineFitRow(s, label, sign)
                 for s in SYMBOLS for label, sign in ((CLASSES[0], 1), (CLASSES[1], -1), (CLASSES[2], 0)))
    b = fit_baselines(data, horizon_minutes=60)
    assert b.b0_symbol_majority("BTCUSDT") == CLASSES[2]
    assert b.b1_symbol_prior("BTCUSDT") == (1/3, 1/3, 1/3)
    assert b.b3_symbol_sign_frequency("BTCUSDT", 1) == (0.5, 0.25, 0.25)
    # Empty bin for this symbol in a second fixture returns its B1 prior.
    sparse = fit_baselines(tuple(BaselineFitRow(s, CLASSES[0], 1) for s in SYMBOLS), horizon_minutes=60)
    assert sparse.b3_symbol_sign_frequency("BTCUSDT", 0) == sparse.b1_symbol_prior("BTCUSDT")
    assert BaselineState.from_json(b.to_json()).b3_symbol_sign_frequency("BTCUSDT", 1) == b.b3_symbol_sign_frequency("BTCUSDT", 1)
    assert B0State.from_json(b.b0_state().to_json()).predict("BTCUSDT") == CLASSES[2]
    assert B1State.from_json(b.b1_state().to_json()).predict("BTCUSDT") == b.b1_symbol_prior("BTCUSDT")
    assert B3State.from_json(b.b3_state().to_json()).predict("BTCUSDT", 1) == b.b3_symbol_sign_frequency("BTCUSDT", 1)
    assert [b2_trailing_h_sign(v) for v in (1, -1, 0)] == [CLASSES[0], CLASSES[1], CLASSES[2]]
