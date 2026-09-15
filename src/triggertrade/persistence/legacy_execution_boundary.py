"""Explicit boundary for legacy execution evidence stores.

These SQLite stores remain useful for compatibility, migration fixtures, and
current runtime evidence while the target Lifecycle ledger is introduced.  They
must not be selected as canonical Lifecycle truth.
"""

from __future__ import annotations

from typing import Any


LEGACY_EXECUTION_EVIDENCE_ROLE = "LEGACY_EXECUTION_EVIDENCE"
TARGET_LIFECYCLE_TRUTH_ROLE = "TARGET_LIFECYCLE_TRUTH"
EXECUTION_STORE_ROLE_ATTR = "__triggertrade_lifecycle_store_role__"


class LegacyExecutionStoreBoundaryError(RuntimeError):
    pass


def execution_store_role(store_or_type: Any) -> str:
    target = store_or_type if isinstance(store_or_type, type) else type(store_or_type)
    role = getattr(target, EXECUTION_STORE_ROLE_ATTR, None)
    return str(role or "UNKNOWN")


def is_legacy_execution_evidence_store(store_or_type: Any) -> bool:
    return execution_store_role(store_or_type) == LEGACY_EXECUTION_EVIDENCE_ROLE


def require_target_lifecycle_truth_store(store: Any) -> Any:
    role = execution_store_role(store)
    if role != TARGET_LIFECYCLE_TRUTH_ROLE:
        raise LegacyExecutionStoreBoundaryError(
            f"{type(store).__name__} has role {role} and cannot be selected as canonical Lifecycle truth"
        )
    return store
