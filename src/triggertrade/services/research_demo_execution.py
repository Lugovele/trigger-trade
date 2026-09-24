"""Durable Research Demo execution handoff and worker dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, Protocol

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.persistence.durable_messages import DurableMessageStore
from triggertrade.persistence.postgres import (
    OwnerStateRecord,
    OwnerStateRevisionConflict,
    OwnerStateStore,
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresUnitOfWork,
)
from triggertrade.persistence.research_store import ResearchRecord
from triggertrade.rules import TradingRulesVersion
from triggertrade.services.research import (
    ResearchDemoExecutionHandoffResult,
    ResearchDemoIsolation,
)


RESEARCH_DEMO_OWNER = "ResearchDemoExecution"
RESEARCH_DEMO_STATE_TYPE = "RESEARCH_DEMO_RUN"
RESEARCH_DEMO_PRODUCER = "Research"
RESEARCH_DEMO_CONSUMER = "ResearchDemoExecution"
RESEARCH_DEMO_MESSAGE_TYPE = "RESEARCH_DEMO_START"
RESEARCH_DEMO_MESSAGE_VERSION = "1"
TERMINAL_RESEARCH_DEMO_STATUSES = {"COMPLETED", "FAILED", "BLOCKED"}


@dataclass(frozen=True)
class ResearchDemoExecutionRecord:
    demo_run_id: str
    research_id: str
    set_id: str
    set_version: str
    rules_version_id: str
    rules_display_version: str
    requested_at: str
    started_at: str | None
    completed_at: str | None
    execution_owner: str
    handoff_message_id: str
    status: str
    progress: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    pin_payload: dict[str, Any]
    pin_digest: str
    revision: int = 0


class ResearchDemoExecutionExecutor(Protocol):
    canonical_research_demo_executor: bool

    def start_research_demo(self, record: ResearchDemoExecutionRecord) -> dict[str, Any]: ...


class PostgresResearchDemoExecutionHandoff:
    """Web-side ingress that persists Research Demo work for the trading worker."""

    canonical_worker_handoff = True

    def __init__(self, *, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def start_research_demo(
        self,
        *,
        research: ResearchRecord,
        rules: TradingRulesVersion,
        isolation: ResearchDemoIsolation,
        started_at: str,
        pin_payload: dict[str, Any],
        demo_run_id: str,
    ) -> ResearchDemoExecutionHandoffResult:
        with PostgresUnitOfWork(self._factory) as uow:
            record = ResearchDemoExecutionStore(uow.connection).submit(
                research=research,
                rules=rules,
                isolation=isolation,
                started_at=started_at,
                pin_payload=pin_payload,
                demo_run_id=demo_run_id,
            )
        return ResearchDemoExecutionHandoffResult(
            handoff_id=record.handoff_message_id,
            execution_owner=record.execution_owner,
            durable=True,
        )


class ResearchDemoExecutionStore:
    """PostgreSQL owner-state wrapper for durable Research Demo execution state."""

    def __init__(self, connection) -> None:
        self._owner_state = OwnerStateStore(connection)
        self._messages = DurableMessageStore(connection)

    def submit(
        self,
        *,
        research: ResearchRecord,
        rules: TradingRulesVersion,
        isolation: ResearchDemoIsolation,
        started_at: str,
        pin_payload: dict[str, Any],
        demo_run_id: str,
    ) -> ResearchDemoExecutionRecord:
        demo_run_id = _required_text(demo_run_id, field="demo_run_id")
        started_at = _required_text(started_at, field="started_at")
        message_id = _message_id(demo_run_id)
        pin_digest = canonical_json_digest(pin_payload)
        existing = self.get(demo_run_id)
        if existing is not None:
            if existing.pin_digest != pin_digest or existing.research_id != research.research_id:
                raise PostgresPersistenceError("research demo run identity already exists with different content")
            if existing.status not in TERMINAL_RESEARCH_DEMO_STATUSES:
                self._append_outbox(existing)
            return existing

        record = ResearchDemoExecutionRecord(
            demo_run_id=demo_run_id,
            research_id=research.research_id,
            set_id=research.set_id,
            set_version=research.set_version,
            rules_version_id=rules.rules_version_id,
            rules_display_version=rules.version,
            requested_at=started_at,
            started_at=None,
            completed_at=None,
            execution_owner="trading-worker",
            handoff_message_id=message_id,
            status="PENDING",
            progress={
                "duration_days": 7,
                "started_at": None,
                "completed_at": None,
                "factual_progress_source": "canonical_research_demo_owner_state",
            },
            result=None,
            error=None,
            pin_payload=dict(pin_payload),
            pin_digest=pin_digest,
        )
        owner, _ = self._owner_state.put_if_absent(
            owner=RESEARCH_DEMO_OWNER,
            state_type=RESEARCH_DEMO_STATE_TYPE,
            state_id=demo_run_id,
            payload=_record_payload(record),
        )
        persisted = _record_from_owner(owner)
        self._append_outbox(persisted)
        return persisted

    def get(self, demo_run_id: str) -> ResearchDemoExecutionRecord | None:
        record = self._owner_state.get(
            owner=RESEARCH_DEMO_OWNER,
            state_type=RESEARCH_DEMO_STATE_TYPE,
            state_id=_required_text(demo_run_id, field="demo_run_id"),
        )
        return None if record is None else _record_from_owner(record)

    def mark_running(self, demo_run_id: str, *, progress: dict[str, Any] | None = None) -> ResearchDemoExecutionRecord:
        current = self.get(demo_run_id)
        if current is None:
            raise PostgresPersistenceError("research demo execution state not found")
        if current.status in TERMINAL_RESEARCH_DEMO_STATUSES:
            return current
        now = _timestamp()
        return self._transition(
            current,
            status="RUNNING",
            started_at=current.started_at or now,
            progress={**current.progress, **(progress or {}), "started_at": current.started_at or now},
        )

    def mark_completed(self, demo_run_id: str, *, result: dict[str, Any]) -> ResearchDemoExecutionRecord:
        current = self.get(demo_run_id)
        if current is None:
            raise PostgresPersistenceError("research demo execution state not found")
        if current.status in TERMINAL_RESEARCH_DEMO_STATUSES:
            return current
        now = _timestamp()
        return self._transition(
            current,
            status="COMPLETED",
            completed_at=now,
            progress={**current.progress, "completed_at": now, "terminal": True},
            result=result,
        )

    def mark_failed(self, demo_run_id: str, *, error: str) -> ResearchDemoExecutionRecord:
        current = self.get(demo_run_id)
        if current is None:
            raise PostgresPersistenceError("research demo execution state not found")
        if current.status in TERMINAL_RESEARCH_DEMO_STATUSES:
            return current
        now = _timestamp()
        return self._transition(
            current,
            status="FAILED",
            completed_at=now,
            progress={**current.progress, "completed_at": now, "terminal": True},
            error=_public_error(error),
        )

    def _transition(
        self,
        current: ResearchDemoExecutionRecord,
        *,
        status: str,
        started_at: str | None = None,
        completed_at: str | None = None,
        progress: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> ResearchDemoExecutionRecord:
        updated = ResearchDemoExecutionRecord(
            demo_run_id=current.demo_run_id,
            research_id=current.research_id,
            set_id=current.set_id,
            set_version=current.set_version,
            rules_version_id=current.rules_version_id,
            rules_display_version=current.rules_display_version,
            requested_at=current.requested_at,
            started_at=started_at if started_at is not None else current.started_at,
            completed_at=completed_at if completed_at is not None else current.completed_at,
            execution_owner=current.execution_owner,
            handoff_message_id=current.handoff_message_id,
            status=status,
            progress=progress if progress is not None else current.progress,
            result=result if result is not None else current.result,
            error=error if error is not None else current.error,
            pin_payload=current.pin_payload,
            pin_digest=current.pin_digest,
            revision=current.revision,
        )
        for _ in range(3):
            try:
                owner = self._owner_state.compare_and_set(
                    owner=RESEARCH_DEMO_OWNER,
                    state_type=RESEARCH_DEMO_STATE_TYPE,
                    state_id=current.demo_run_id,
                    expected_revision=current.revision,
                    payload=_record_payload(updated),
                )
                return _record_from_owner(owner)
            except OwnerStateRevisionConflict:
                latest = self.get(current.demo_run_id)
                if latest is None:
                    raise
                if latest.status in TERMINAL_RESEARCH_DEMO_STATUSES:
                    return latest
                current = latest
        raise OwnerStateRevisionConflict("research demo execution state changed concurrently")

    def _append_outbox(self, record: ResearchDemoExecutionRecord) -> None:
        if record.status in TERMINAL_RESEARCH_DEMO_STATUSES:
            return
        self._messages.append_outbox(
            message_id=record.handoff_message_id,
            producer=RESEARCH_DEMO_PRODUCER,
            consumer=RESEARCH_DEMO_CONSUMER,
            message_type=RESEARCH_DEMO_MESSAGE_TYPE,
            message_version=RESEARCH_DEMO_MESSAGE_VERSION,
            payload={"research_demo": _record_payload(record)},
            aggregate_id=record.research_id,
            causation_id=record.demo_run_id,
            correlation_id=record.demo_run_id,
            dedupe_key=f"RESEARCH_DEMO_START:{record.demo_run_id}",
        )


class ResearchDemoExecutionDispatcher:
    """Trading-worker side dispatcher for durable Research Demo handoffs."""

    def __init__(
        self,
        *,
        store: ResearchDemoExecutionStore,
        executor: ResearchDemoExecutionExecutor | None,
    ) -> None:
        self._store = store
        self._executor = executor

    def dispatch(self, demo_run_id: str) -> str:
        record = self._store.get(demo_run_id)
        if record is None:
            raise PostgresPersistenceError("research_demo_execution_state_not_found")
        if record.status in TERMINAL_RESEARCH_DEMO_STATUSES:
            return f"research_demo_replay:{record.status}"
        if self._executor is None or not getattr(self._executor, "canonical_research_demo_executor", False):
            raise PostgresPersistenceError("research_demo_canonical_executor_unavailable")
        record = self._store.mark_running(record.demo_run_id)
        result = self._executor.start_research_demo(record)
        if bool(result.get("terminal")):
            completed = self._store.mark_completed(record.demo_run_id, result=dict(result))
            return f"research_demo_completed:{completed.demo_run_id}"
        return f"research_demo_running:{record.demo_run_id}"


def research_demo_run_id(*, research_id: str, pin_digest: str, started_at: str) -> str:
    source = "|".join(
        [
            _required_text(research_id, field="research_id"),
            _required_text(pin_digest, field="pin_digest"),
            _required_text(started_at, field="started_at"),
        ]
    )
    return f"rdm-{sha256(source.encode('utf-8')).hexdigest()[:20]}"


def _record_payload(record: ResearchDemoExecutionRecord) -> dict[str, Any]:
    return {
        "demo_run_id": record.demo_run_id,
        "research_id": record.research_id,
        "set_id": record.set_id,
        "set_version": record.set_version,
        "rules_version_id": record.rules_version_id,
        "rules_display_version": record.rules_display_version,
        "requested_at": record.requested_at,
        "started_at": record.started_at,
        "completed_at": record.completed_at,
        "execution_owner": record.execution_owner,
        "handoff_message_id": record.handoff_message_id,
        "status": record.status,
        "progress": record.progress,
        "result": record.result,
        "error": record.error,
        "pin_payload": record.pin_payload,
        "pin_digest": record.pin_digest,
    }


def _record_from_owner(record: OwnerStateRecord) -> ResearchDemoExecutionRecord:
    payload = record.payload
    return ResearchDemoExecutionRecord(
        demo_run_id=_required_text(payload.get("demo_run_id"), field="demo_run_id"),
        research_id=_required_text(payload.get("research_id"), field="research_id"),
        set_id=_required_text(payload.get("set_id"), field="set_id"),
        set_version=_required_text(payload.get("set_version"), field="set_version"),
        rules_version_id=_required_text(payload.get("rules_version_id"), field="rules_version_id"),
        rules_display_version=_required_text(payload.get("rules_display_version"), field="rules_display_version"),
        requested_at=_required_text(payload.get("requested_at"), field="requested_at"),
        started_at=_optional_text(payload.get("started_at"), field="started_at"),
        completed_at=_optional_text(payload.get("completed_at"), field="completed_at"),
        execution_owner=_required_text(payload.get("execution_owner"), field="execution_owner"),
        handoff_message_id=_required_text(payload.get("handoff_message_id"), field="handoff_message_id"),
        status=_required_text(payload.get("status"), field="status"),
        progress=dict(payload.get("progress") or {}),
        result=None if payload.get("result") is None else dict(payload.get("result") or {}),
        error=_optional_text(payload.get("error"), field="error"),
        pin_payload=dict(payload.get("pin_payload") or {}),
        pin_digest=_required_text(payload.get("pin_digest"), field="pin_digest"),
        revision=record.revision,
    )


def _message_id(demo_run_id: str) -> str:
    return f"research-demo-start-{sha256(demo_run_id.encode('utf-8')).hexdigest()[:32]}"


def _required_text(value: object, *, field: str) -> str:
    raw = str(value or "").strip()
    if not raw or "\x00" in raw or len(raw) > 240:
        raise PostgresPersistenceError(f"{field} must be a non-empty stable string")
    return raw


def _optional_text(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field=field)


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _public_error(value: object) -> str:
    text = " ".join(str(value).replace("\x00", "").split())[:500]
    lowered = text.lower()
    if any(token in lowered for token in ("secret", "api_key", "authorization", "bearer", "token", "password")):
        return "[redacted]"
    return text or "research_demo_execution_failed"
