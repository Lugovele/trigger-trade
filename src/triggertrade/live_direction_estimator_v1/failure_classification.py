"""Phase 10 failure taxonomy; classification does not alter Section 20 gates."""

from __future__ import annotations

from dataclasses import dataclass

FAILURE_CLASSES = frozenset({"UNAVAILABLE", "MODEL_NOT_ESTIMABLE", "FIT_FAILED",
    "CALIBRATION_FAILED", "NOT_ESTIMABLE", "CONTINUE_RESEARCH", "REJECT", "INVALID"})

_CAUSES = {
    "MISSING_REQUIRED_MINUTE": "UNAVAILABLE",
    "UNVERIFIED_AVAILABILITY": "UNAVAILABLE",
    "DATA_LATE": "UNAVAILABLE",
    "INCOMPLETE_FINALIZATION": "UNAVAILABLE",
    "SOURCE_VERSION_CONFLICT": "UNAVAILABLE",
    "FALSE_ASOF_CLAIM": "INVALID",
    "POST_T_REPAIR": "INVALID",
    "BACKDATED_EMISSION": "INVALID",
    "SYMBOL_CLASS_SUPPORT_ABSENT": "MODEL_NOT_ESTIMABLE",
    "SOLVER_FAILURE": "FIT_FAILED",
    "CALIBRATION_FAILURE": "CALIBRATION_FAILED",
    "UNDEFINED_REQUIRED_BOUND": "NOT_ESTIMABLE",
    "COVERAGE_SHORTFALL": "CONTINUE_RESEARCH",
    "REGISTERED_R1": "REJECT",
    "REGISTERED_R2": "REJECT",
}


@dataclass(frozen=True)
class FailureClassification:
    cause: str
    failure_class: str


def classify_failure(cause: str) -> FailureClassification:
    if cause not in _CAUSES:
        raise ValueError("unregistered failure cause")
    return FailureClassification(cause, _CAUSES[cause])
