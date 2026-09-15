import pytest

from triggertrade.persistence import (
    ExecutionStore,
    FuturesExecutionStore,
    LEGACY_EXECUTION_EVIDENCE_ROLE,
    TARGET_LIFECYCLE_TRUTH_ROLE,
    LegacyExecutionStoreBoundaryError,
    execution_store_role,
    is_legacy_execution_evidence_store,
    require_target_lifecycle_truth_store,
)


def test_legacy_execution_stores_are_marked_as_evidence_not_lifecycle_truth(tmp_path):
    stores = (
        ExecutionStore(tmp_path / "legacy-paper.sqlite3"),
        FuturesExecutionStore(tmp_path / "legacy-futures.sqlite3"),
    )

    for store in stores:
        assert execution_store_role(store) == LEGACY_EXECUTION_EVIDENCE_ROLE
        assert is_legacy_execution_evidence_store(type(store)) is True


def test_legacy_execution_stores_cannot_be_selected_as_target_lifecycle_truth(tmp_path):
    for store in (
        ExecutionStore(tmp_path / "legacy-paper.sqlite3"),
        FuturesExecutionStore(tmp_path / "legacy-futures.sqlite3"),
    ):
        with pytest.raises(LegacyExecutionStoreBoundaryError, match="cannot be selected as canonical Lifecycle truth"):
            require_target_lifecycle_truth_store(store)


def test_target_lifecycle_truth_marker_is_required_for_future_store_selection():
    class TargetLifecycleStore:
        __triggertrade_lifecycle_store_role__ = TARGET_LIFECYCLE_TRUTH_ROLE

    store = TargetLifecycleStore()

    assert require_target_lifecycle_truth_store(store) is store
    assert execution_store_role(store) == TARGET_LIFECYCLE_TRUTH_ROLE
