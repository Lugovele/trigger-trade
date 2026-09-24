from __future__ import annotations

import inspect

import pytest

from triggertrade.persistence.postgres import PostgresPersistenceError
from triggertrade.services.operator_execution_bridge import (
    DashboardOperatorExecutionBridge,
    OperatorExecutionCommandRecord,
    OperatorExecutionDispatcher,
)


def _record(
    *,
    command_id: str = "operator-command-1",
    command_type: str = "CLOSE_POSITION",
    status: str = "PENDING",
    payload: dict[str, object] | None = None,
) -> OperatorExecutionCommandRecord:
    return OperatorExecutionCommandRecord(
        command_id=command_id,
        command_type=command_type,
        requested_by="operator-1",
        authorization_source="managed_oidc",
        idempotency_key="idem-1",
        target=str((payload or {}).get("position_id") or "pos-1"),
        payload=payload or {"position_id": "pos-1", "close_reason": "MANUAL"},
        status=status,
        created_at="2026-09-24T00:00:00Z",
        updated_at="2026-09-24T00:00:00Z",
        claimed_at=None,
        completed_at=None,
        result=None,
        error=None,
        revision=1,
    )


class FakeStore:
    def __init__(self, record: OperatorExecutionCommandRecord) -> None:
        self.record = record
        self.transitions: list[str] = []

    def get(self, command_id: str):
        assert command_id == self.record.command_id
        return self.record

    def mark_executing(self, command_id: str):
        self.transitions.append("EXECUTING")
        self.record = _copy_record(self.record, status="EXECUTING", claimed_at="claimed")
        return self.record

    def mark_succeeded(self, command_id: str, *, result: dict[str, object]):
        self.transitions.append("SUCCEEDED")
        self.record = _copy_record(self.record, status="SUCCEEDED", result=result, completed_at="done")
        return self.record

    def mark_partial(self, command_id: str, *, result: dict[str, object]):
        self.transitions.append("PARTIAL")
        self.record = _copy_record(self.record, status="PARTIAL", result=result, completed_at="done")
        return self.record

    def mark_failed(self, command_id: str, *, error: str):
        self.transitions.append("FAILED")
        self.record = _copy_record(self.record, status="FAILED", error=error, completed_at="done")
        return self.record


class RecordingExecutor:
    def __init__(self, *, fail: bool = False, close_all_failures: tuple[str, ...] = ()) -> None:
        self.fail = fail
        self.close_all_failures = close_all_failures
        self.calls: list[tuple[str, dict[str, object]]] = []

    def close_position(self, **kwargs):
        self.calls.append(("close_position", kwargs))
        if self.fail:
            raise RuntimeError("api_secret leaked")
        return {"position_id": kwargs["position_id"], "position_status": "CLOSED", "reason": "closed"}

    def close_all_positions(self, **kwargs):
        self.calls.append(("close_all_positions", kwargs))
        return {
            "scope": kwargs["scope"],
            "terminal": True,
            "target_count": 2,
            "closed_count": 1,
            "failures": list(self.close_all_failures),
        }


def test_close_position_dispatch_routes_to_lifecycle_executor_without_exchange_parameters():
    store = FakeStore(_record())
    executor = RecordingExecutor()

    detail = OperatorExecutionDispatcher(store=store, executor=executor).dispatch("operator-command-1")

    assert detail.startswith("operator_command_succeeded:CLOSE_POSITION")
    assert store.transitions == ["EXECUTING", "SUCCEEDED"]
    assert executor.calls == [("close_position", {"position_id": "pos-1", "close_reason": "MANUAL"})]
    assert store.record.result == {"position_id": "pos-1", "position_status": "CLOSED", "reason": "closed"}


def test_close_all_partial_outcome_is_not_marked_succeeded():
    store = FakeStore(_record(command_type="CLOSE_ALL", payload={"scope": "ACTIVE"}))
    executor = RecordingExecutor(close_all_failures=("pos-2:ExecutionError",))

    detail = OperatorExecutionDispatcher(store=store, executor=executor).dispatch("operator-command-1")

    assert detail.startswith("operator_command_partial:CLOSE_ALL")
    assert store.transitions == ["EXECUTING", "PARTIAL"]
    assert executor.calls == [("close_all_positions", {"scope": "ACTIVE", "operation_id": "operator-command-1"})]
    assert store.record.result["failures"] == ["pos-2:ExecutionError"]


def test_terminal_command_replay_does_not_call_executor_again():
    store = FakeStore(_record(status="SUCCEEDED"))
    executor = RecordingExecutor()

    detail = OperatorExecutionDispatcher(store=store, executor=executor).dispatch("operator-command-1")

    assert detail == "operator_command_replay:SUCCEEDED"
    assert store.transitions == []
    assert executor.calls == []


def test_missing_worker_executor_fails_closed_without_terminalizing_command():
    store = FakeStore(_record())

    with pytest.raises(PostgresPersistenceError, match="operator_execution_bridge_unavailable"):
        OperatorExecutionDispatcher(store=store, executor=None).dispatch("operator-command-1")

    assert store.transitions == []
    assert store.record.status == "PENDING"


def test_executor_failure_remains_replayable_and_redacts_error():
    store = FakeStore(_record())
    executor = RecordingExecutor(fail=True)

    with pytest.raises(PostgresPersistenceError, match="operator_command_reconciliation_required:RuntimeError"):
        OperatorExecutionDispatcher(store=store, executor=executor).dispatch("operator-command-1")

    assert store.transitions == ["EXECUTING"]
    assert store.record.status == "EXECUTING"
    assert store.record.error is None


def test_non_terminal_close_result_stays_in_progress_for_replay():
    store = FakeStore(_record())

    class SubmittedOnlyExecutor:
        def close_position(self, **kwargs):
            return {"position_id": kwargs["position_id"], "position_status": "CLOSING", "reason": "close_submitted"}

        def close_all_positions(self, **kwargs):
            raise AssertionError("not used")

    with pytest.raises(PostgresPersistenceError, match="operator_command_in_progress:CLOSE_POSITION"):
        OperatorExecutionDispatcher(store=store, executor=SubmittedOnlyExecutor()).dispatch("operator-command-1")

    assert store.transitions == ["EXECUTING"]
    assert store.record.status == "EXECUTING"


def test_dashboard_bridge_contains_no_direct_exchange_execution_stack():
    source = inspect.getsource(DashboardOperatorExecutionBridge)

    assert "Bybit" not in source
    assert "FuturesExecutionService" not in source
    assert "FuturesPositionLifecycleService" not in source


def _copy_record(record: OperatorExecutionCommandRecord, **changes) -> OperatorExecutionCommandRecord:
    values = {
        "command_id": record.command_id,
        "command_type": record.command_type,
        "requested_by": record.requested_by,
        "authorization_source": record.authorization_source,
        "idempotency_key": record.idempotency_key,
        "target": record.target,
        "payload": record.payload,
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "claimed_at": record.claimed_at,
        "completed_at": record.completed_at,
        "result": record.result,
        "error": record.error,
        "revision": record.revision + 1,
    }
    values.update(changes)
    return OperatorExecutionCommandRecord(**values)
