"""Durable dashboard-to-worker operator execution bridge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, Protocol

from triggertrade.persistence.durable_messages import DurableMessageStore
from triggertrade.persistence.postgres import (
    OwnerStateRecord,
    OwnerStateRevisionConflict,
    OwnerStateStore,
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresUnitOfWork,
)


OPERATOR_EXECUTION_OWNER = "OperatorExecution"
OPERATOR_EXECUTION_STATE_TYPE = "OPERATOR_COMMAND"
OPERATOR_EXECUTION_PRODUCER = "Dashboard"
OPERATOR_EXECUTION_CONSUMER = "OperatorExecution"
OPERATOR_EXECUTION_MESSAGE_TYPE = "OPERATOR_COMMAND"
OPERATOR_EXECUTION_MESSAGE_VERSION = "1"
TERMINAL_OPERATOR_STATUSES = {"SUCCEEDED", "FAILED", "PARTIAL"}


@dataclass(frozen=True)
class OperatorExecutionCommandRecord:
    command_id: str
    command_type: str
    requested_by: str
    authorization_source: str
    idempotency_key: str | None
    target: str
    payload: dict[str, Any]
    status: str
    created_at: str
    updated_at: str
    claimed_at: str | None
    completed_at: str | None
    result: dict[str, Any] | None
    error: str | None
    revision: int = 0


class OperatorExecutionExecutor(Protocol):
    def close_position(self, **kwargs): ...

    def close_all_positions(self, **kwargs): ...


class DashboardOperatorExecutionBridge:
    """Web-owned ingress that persists intent but never executes exchange work."""

    canonical_execution_bridge = True

    def __init__(self, *, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def close_position(
        self,
        *,
        position_id: str,
        symbol: str | None = None,
        close_reason: str = "MANUAL",
        requested_by: str = "dashboard",
        authorization_source: str = "unknown",
        idempotency_key: str | None = None,
    ) -> OperatorExecutionCommandRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            return OperatorExecutionCommandStore(uow.connection).submit(
                command_type="CLOSE_POSITION",
                requested_by=requested_by,
                authorization_source=authorization_source,
                idempotency_key=idempotency_key,
                target=_required_text(position_id, field="position_id"),
                payload={
                    "position_id": _required_text(position_id, field="position_id"),
                    "symbol": _optional_text(symbol, field="symbol"),
                    "close_reason": _required_text(close_reason, field="close_reason"),
                },
            )

    def close_all_positions(
        self,
        *,
        scope: str = "ACTIVE",
        requested_by: str = "dashboard",
        authorization_source: str = "unknown",
        idempotency_key: str | None = None,
    ) -> OperatorExecutionCommandRecord:
        resolved_scope = _required_text(scope, field="scope")
        with PostgresUnitOfWork(self._factory) as uow:
            return OperatorExecutionCommandStore(uow.connection).submit(
                command_type="CLOSE_ALL",
                requested_by=requested_by,
                authorization_source=authorization_source,
                idempotency_key=idempotency_key,
                target=resolved_scope,
                payload={"scope": resolved_scope},
            )


class OperatorExecutionCommandStore:
    """PostgreSQL owner-state wrapper for durable operator execution commands."""

    def __init__(self, connection) -> None:
        self._owner_state = OwnerStateStore(connection)
        self._messages = DurableMessageStore(connection)

    def submit(
        self,
        *,
        command_type: str,
        requested_by: str,
        authorization_source: str,
        idempotency_key: str | None,
        target: str,
        payload: dict[str, Any],
    ) -> OperatorExecutionCommandRecord:
        command_type = _command_type(command_type)
        target = _required_text(target, field="target")
        requested_by = _required_text(requested_by, field="requested_by")
        authorization_source = _required_text(authorization_source, field="authorization_source")
        idempotency_key = _optional_text(idempotency_key, field="idempotency_key")
        command_id = _command_id(command_type=command_type, target=target, idempotency_key=idempotency_key)
        existing = self.get(command_id)
        if existing is not None:
            if existing.command_type != command_type or existing.target != target:
                raise PostgresPersistenceError("idempotency key already exists for a different operator command")
            if existing.status not in TERMINAL_OPERATOR_STATUSES:
                self._append_outbox(existing)
            return existing

        now = _timestamp()
        record = OperatorExecutionCommandRecord(
            command_id=command_id,
            command_type=command_type,
            requested_by=requested_by,
            authorization_source=authorization_source,
            idempotency_key=idempotency_key,
            target=target,
            payload=dict(payload),
            status="PENDING",
            created_at=now,
            updated_at=now,
            claimed_at=None,
            completed_at=None,
            result=None,
            error=None,
            revision=0,
        )
        owner_record, _ = self._owner_state.put_if_absent(
            owner=OPERATOR_EXECUTION_OWNER,
            state_type=OPERATOR_EXECUTION_STATE_TYPE,
            state_id=command_id,
            payload=_record_payload(record),
        )
        persisted = _record_from_owner(owner_record)
        self._append_outbox(persisted)
        return persisted

    def get(self, command_id: str) -> OperatorExecutionCommandRecord | None:
        record = self._owner_state.get(
            owner=OPERATOR_EXECUTION_OWNER,
            state_type=OPERATOR_EXECUTION_STATE_TYPE,
            state_id=_required_text(command_id, field="command_id"),
        )
        return None if record is None else _record_from_owner(record)

    def mark_executing(self, command_id: str) -> OperatorExecutionCommandRecord:
        return self._transition(command_id, status="EXECUTING", claimed=True)

    def mark_succeeded(self, command_id: str, *, result: dict[str, Any]) -> OperatorExecutionCommandRecord:
        return self._transition(command_id, status="SUCCEEDED", result=result, completed=True)

    def mark_partial(self, command_id: str, *, result: dict[str, Any]) -> OperatorExecutionCommandRecord:
        return self._transition(command_id, status="PARTIAL", result=result, completed=True)

    def mark_failed(self, command_id: str, *, error: str) -> OperatorExecutionCommandRecord:
        return self._transition(command_id, status="FAILED", error=error[:500], completed=True)

    def _transition(
        self,
        command_id: str,
        *,
        status: str,
        claimed: bool = False,
        completed: bool = False,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> OperatorExecutionCommandRecord:
        for _ in range(3):
            current = self.get(command_id)
            if current is None:
                raise PostgresPersistenceError("operator command does not exist")
            if current.status in TERMINAL_OPERATOR_STATUSES:
                return current
            now = _timestamp()
            updated = OperatorExecutionCommandRecord(
                command_id=current.command_id,
                command_type=current.command_type,
                requested_by=current.requested_by,
                authorization_source=current.authorization_source,
                idempotency_key=current.idempotency_key,
                target=current.target,
                payload=current.payload,
                status=status,
                created_at=current.created_at,
                updated_at=now,
                claimed_at=current.claimed_at or (now if claimed else None),
                completed_at=now if completed else current.completed_at,
                result=result if completed else current.result,
                error=error if completed else current.error,
                revision=current.revision,
            )
            try:
                owner = self._owner_state.compare_and_set(
                    owner=OPERATOR_EXECUTION_OWNER,
                    state_type=OPERATOR_EXECUTION_STATE_TYPE,
                    state_id=current.command_id,
                    expected_revision=current.revision,
                    payload=_record_payload(updated),
                )
                return _record_from_owner(owner)
            except OwnerStateRevisionConflict:
                continue
        raise OwnerStateRevisionConflict("operator command changed concurrently")

    def _append_outbox(self, record: OperatorExecutionCommandRecord) -> None:
        if record.status in TERMINAL_OPERATOR_STATUSES:
            return
        self._messages.append_outbox(
            message_id=record.command_id,
            producer=OPERATOR_EXECUTION_PRODUCER,
            consumer=OPERATOR_EXECUTION_CONSUMER,
            message_type=OPERATOR_EXECUTION_MESSAGE_TYPE,
            message_version=OPERATOR_EXECUTION_MESSAGE_VERSION,
            payload={"operator_command": _record_payload(record)},
            aggregate_id=record.target,
            causation_id=record.idempotency_key,
            correlation_id=record.command_id,
            dedupe_key=f"OPERATOR_COMMAND:{record.command_id}",
        )


class OperatorExecutionDispatcher:
    """Trading-worker side dispatcher for durable operator commands."""

    def __init__(self, *, store: OperatorExecutionCommandStore, executor: OperatorExecutionExecutor | None) -> None:
        self._store = store
        self._executor = executor

    def dispatch(self, command_id: str) -> str:
        if self._executor is None:
            raise PostgresPersistenceError("operator_execution_bridge_unavailable")
        record = self._store.get(command_id)
        if record is None:
            raise PostgresPersistenceError("operator_command_not_found")
        if record.status in TERMINAL_OPERATOR_STATUSES:
            return f"operator_command_replay:{record.status}"
        record = self._store.mark_executing(record.command_id)
        try:
            result = self._execute(record)
        except Exception as exc:  # noqa: BLE001 - durable command failure is terminal and queryable.
            raise PostgresPersistenceError(f"operator_command_reconciliation_required:{_public_error(exc)}") from exc
        if not _is_terminal_execution_result(record.command_type, result):
            raise PostgresPersistenceError(f"operator_command_in_progress:{record.command_type}:{record.command_id}")
        if record.command_type == "CLOSE_ALL" and _is_partial_close_all_result(result):
            completed = self._store.mark_partial(record.command_id, result=result)
        else:
            completed = self._store.mark_succeeded(record.command_id, result=result)
        return f"operator_command_{completed.status.lower()}:{completed.command_type}:{completed.command_id}"

    def _execute(self, record: OperatorExecutionCommandRecord) -> dict[str, Any]:
        if record.command_type == "CLOSE_POSITION":
            result = self._executor.close_position(
                position_id=_required_text(record.payload.get("position_id"), field="position_id"),
                close_reason=_required_text(record.payload.get("close_reason") or "MANUAL", field="close_reason"),
            )
            return _result_payload(result)
        if record.command_type == "CLOSE_ALL":
            result = self._executor.close_all_positions(
                scope=_required_text(record.payload.get("scope"), field="scope"),
                operation_id=record.command_id,
            )
            return _result_payload(result)
        raise PostgresPersistenceError(f"unsupported operator command type: {record.command_type}")


def _record_payload(record: OperatorExecutionCommandRecord) -> dict[str, Any]:
    return {
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
    }


def _record_from_owner(record: OwnerStateRecord) -> OperatorExecutionCommandRecord:
    payload = record.payload
    return OperatorExecutionCommandRecord(
        command_id=_required_text(payload.get("command_id"), field="command_id"),
        command_type=_command_type(str(payload.get("command_type") or "")),
        requested_by=_required_text(payload.get("requested_by"), field="requested_by"),
        authorization_source=_required_text(payload.get("authorization_source"), field="authorization_source"),
        idempotency_key=_optional_text(payload.get("idempotency_key"), field="idempotency_key"),
        target=_required_text(payload.get("target"), field="target"),
        payload=dict(payload.get("payload") or {}),
        status=_required_text(payload.get("status"), field="status"),
        created_at=_required_text(payload.get("created_at"), field="created_at"),
        updated_at=_required_text(payload.get("updated_at"), field="updated_at"),
        claimed_at=_optional_text(payload.get("claimed_at"), field="claimed_at"),
        completed_at=_optional_text(payload.get("completed_at"), field="completed_at"),
        result=None if payload.get("result") is None else dict(payload.get("result") or {}),
        error=_optional_text(payload.get("error"), field="error"),
        revision=record.revision,
    )


def _command_id(*, command_type: str, target: str, idempotency_key: str | None) -> str:
    if idempotency_key:
        source = f"{command_type}\x1f{target}\x1f{idempotency_key}"
    else:
        source = f"{command_type}\x1f{target}\x1f{_timestamp()}"
    return f"operator-command-{sha256(source.encode('utf-8')).hexdigest()[:32]}"


def _command_type(value: str) -> str:
    raw = _required_text(value, field="command_type").upper()
    if raw not in {"CLOSE_POSITION", "CLOSE_ALL"}:
        raise PostgresPersistenceError(f"unsupported operator command type: {value}")
    return raw


def _result_payload(result: Any) -> dict[str, Any]:
    if result is None:
        return {"status": "accepted"}
    if isinstance(result, dict):
        return dict(result)
    payload: dict[str, Any] = {"type": result.__class__.__name__}
    for name in ("position_id", "order_id", "status", "closed_count", "target_count", "results", "failures"):
        if hasattr(result, name):
            payload[name] = _jsonable(getattr(result, name))
    return payload


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _is_partial_close_all_result(result: dict[str, Any]) -> bool:
    if result.get("terminal") is not True:
        return False
    failures = result.get("failures")
    if isinstance(failures, (list, tuple)):
        return len(failures) > 0
    return bool(failures)


def _is_terminal_execution_result(command_type: str, result: dict[str, Any]) -> bool:
    if result.get("terminal") is True:
        return True
    if command_type == "CLOSE_POSITION":
        return _close_item_terminal(result)
    if command_type == "CLOSE_ALL":
        failures = result.get("failures")
        if failures:
            return result.get("terminal") is True
        rows = result.get("results")
        if not isinstance(rows, list):
            return False
        return all(isinstance(row, dict) and _close_item_terminal(row) for row in rows)
    return False


def _close_item_terminal(value: dict[str, Any]) -> bool:
    status = str(value.get("position_status") or value.get("status") or "").upper()
    reason = str(value.get("reason") or "").lower()
    return status == "CLOSED" or reason in {"closed", "already_closed"}


def _required_text(value: object, *, field: str) -> str:
    raw = str(value or "").strip()
    if not raw or "\x00" in raw or len(raw) > 200:
        raise PostgresPersistenceError(f"{field} must be a non-empty stable string")
    return raw


def _optional_text(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field=field)


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _public_error(exc: Exception) -> str:
    text = str(exc)
    lower = text.lower()
    if any(token in lower for token in ("secret", "api_key", "authorization", "x-bapi", "password", "token")):
        return exc.__class__.__name__
    return text[:500]
