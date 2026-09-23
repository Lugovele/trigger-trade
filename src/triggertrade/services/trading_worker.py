"""Canonical message-driven trading worker."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import socket
import time
from typing import Callable, Iterable, Protocol

from triggertrade.persistence import RuntimeHeartbeat
from triggertrade.persistence.durable_messages import OutboxMessageRecord
from triggertrade.persistence.postgres import PostgresConnectionFactory, PostgresUnitOfWork
from triggertrade.persistence.postgres_runtime_store import PostgresRuntimeStore
from triggertrade.services.owner_dispatch import OwnerDispatchBlocked, OwnerDispatchResult


TRADING_WORKER_COMPONENT = "trading-worker"
TRADING_WORKER_CONSUMERS = ("Portfolio", "Set", "Position", "Lifecycle")


class TradingWorkerBlocked(RuntimeError):
    """Raised when the worker encounters work that must fail closed."""


class RuntimeHeartbeatStore(Protocol):
    def record_heartbeat(self, heartbeat: RuntimeHeartbeat) -> RuntimeHeartbeat: ...


class DurableMessageClient(Protocol):
    def claim_outbox(
        self,
        *,
        consumer: str,
        worker_id: str,
        limit: int = 1,
        lock_seconds: int = 60,
    ) -> tuple[OutboxMessageRecord, ...]: ...

    def dispatch_claimed(self, message: OutboxMessageRecord) -> OwnerDispatchResult: ...


@dataclass(frozen=True)
class TradingWorkerCycleResult:
    claimed: int
    blocked: bool
    detail: str


class TargetTradingWorker:
    """Poll durable outboxes without falling back to legacy/demo runtime paths."""

    def __init__(
        self,
        *,
        runtime_store: RuntimeHeartbeatStore,
        message_client_factory: Callable[[], DurableMessageClient],
        worker_id: str | None = None,
        consumers: Iterable[str] = TRADING_WORKER_CONSUMERS,
        claim_limit: int = 10,
        lock_seconds: int = 60,
        poll_seconds: float = 5.0,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._runtime_store = runtime_store
        self._message_client_factory = message_client_factory
        self._worker_id = _worker_id(worker_id)
        self._consumers = tuple(_consumer_name(consumer) for consumer in consumers)
        self._claim_limit = _bounded_int(claim_limit, field="claim_limit", minimum=1, maximum=100)
        self._lock_seconds = _bounded_int(lock_seconds, field="lock_seconds", minimum=1, maximum=3600)
        if poll_seconds <= 0:
            raise ValueError("poll_seconds must be positive")
        self._poll_seconds = min(float(poll_seconds), 300.0)
        self._sleeper = sleeper
        self._clock = clock or (lambda: datetime.now(UTC))
        self._stop_requested = False

    @property
    def worker_id(self) -> str:
        return self._worker_id

    def run_forever(self, max_cycles: int | None = None) -> None:
        cycles = 0
        self._record_heartbeat("RUNNING", "worker hydrated durable state")
        while not self._stop_requested:
            result = self.process_once()
            cycles += 1
            if result.blocked:
                break
            if max_cycles is not None and cycles >= max_cycles:
                break
            self._sleeper(self._poll_seconds)

    def stop(self) -> None:
        self._stop_requested = True

    def process_once(self) -> TradingWorkerCycleResult:
        claimed = 0
        client = self._message_client_factory()
        for consumer in self._consumers:
            messages = client.claim_outbox(
                consumer=consumer,
                worker_id=self._worker_id,
                limit=self._claim_limit,
                lock_seconds=self._lock_seconds,
            )
            claimed += len(messages)
            for message in messages:
                try:
                    dispatch_result = client.dispatch_claimed(message)
                except OwnerDispatchBlocked as exc:
                    detail = str(exc)
                    self._record_heartbeat(
                        "BLOCKED",
                        detail,
                        metadata={
                            "message_id": message.message_id,
                            "consumer": consumer,
                            "message_type": message.message_type,
                        },
                    )
                    return TradingWorkerCycleResult(claimed=claimed, blocked=True, detail=detail)
                self._record_heartbeat(
                    "RUNNING",
                    dispatch_result.detail,
                    metadata={
                        "message_id": message.message_id,
                        "consumer": consumer,
                        "message_type": message.message_type,
                        "processed": str(dispatch_result.processed).lower(),
                    },
                )
        detail = "idle" if claimed == 0 else f"processed:{claimed}"
        self._record_heartbeat("RUNNING", detail, metadata={"claimed": str(claimed)})
        return TradingWorkerCycleResult(claimed=claimed, blocked=False, detail=detail)

    def _record_heartbeat(self, status: str, detail: str, *, metadata: dict[str, str | None] | None = None) -> None:
        self._runtime_store.record_heartbeat(
            RuntimeHeartbeat(
                component=TRADING_WORKER_COMPONENT,
                status=status,
                observed_at=self._clock().isoformat(),
                detail=detail,
                metadata={"worker_id": self._worker_id, **(metadata or {})},
            )
        )


def build_target_trading_worker(
    *,
    factory: PostgresConnectionFactory,
    runtime_store: PostgresRuntimeStore,
    worker_id: str | None = None,
    consumers: Iterable[str] = TRADING_WORKER_CONSUMERS,
    poll_seconds: float = 5.0,
) -> TargetTradingWorker:
    return TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: _PostgresMessageClient(factory),
        worker_id=worker_id,
        consumers=consumers,
        poll_seconds=poll_seconds,
    )


class _PostgresMessageClient:
    def __init__(self, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def claim_outbox(self, **kwargs):
        from triggertrade.persistence import DurableMessageStore

        with PostgresUnitOfWork(self._factory) as uow:
            return DurableMessageStore(uow.connection).claim_outbox(**kwargs)

    def dispatch_claimed(self, message: OutboxMessageRecord) -> OwnerDispatchResult:
        from triggertrade.services.owner_dispatch import CanonicalOwnerDispatcher

        with PostgresUnitOfWork(self._factory) as uow:
            return CanonicalOwnerDispatcher(uow.connection).dispatch(message)


def _worker_id(value: str | None) -> str:
    raw = (value or f"{socket.gethostname()}-{TRADING_WORKER_COMPONENT}").strip()
    if not raw or "\x00" in raw or len(raw) > 200:
        raise ValueError("worker_id must be a stable non-empty string")
    return raw


def _consumer_name(value: str) -> str:
    raw = str(value).strip()
    if raw not in TRADING_WORKER_CONSUMERS:
        raise ValueError(f"unsupported trading worker consumer: {value!r}")
    return raw


def _bounded_int(value: int, *, field: str, minimum: int, maximum: int) -> int:
    number = int(value)
    if number < minimum or number > maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return number
