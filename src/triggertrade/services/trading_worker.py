"""Canonical message-driven trading worker."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import socket
import threading
import time
from typing import Callable, Iterable, Protocol

from triggertrade.persistence import RuntimeHeartbeat
from triggertrade.persistence.durable_messages import OutboxMessageRecord
from triggertrade.persistence.postgres import PostgresConnectionFactory, PostgresUnitOfWork
from triggertrade.persistence.postgres_runtime_store import PostgresRuntimeStore
from triggertrade.services.owner_dispatch import OwnerDispatchBlocked, OwnerDispatchResult
from triggertrade.services.operator_execution_bridge import OPERATOR_EXECUTION_CONSUMER, OperatorExecutionExecutor
from triggertrade.services.research_backtest_execution import RESEARCH_BACKTEST_CONSUMER, ResearchBacktestExecutionExecutor
from triggertrade.services.research_demo_execution import RESEARCH_DEMO_CONSUMER, ResearchDemoExecutionExecutor


TRADING_WORKER_COMPONENT = "trading-worker"
TRADING_WORKER_CONSUMERS = (
    "Portfolio",
    "Set",
    "Position",
    "Lifecycle",
    OPERATOR_EXECUTION_CONSUMER,
    RESEARCH_BACKTEST_CONSUMER,
    RESEARCH_DEMO_CONSUMER,
)


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

    def renew_outbox_lock(
        self,
        *,
        message_id: str,
        worker_id: str,
        lock_seconds: int = 60,
    ) -> OutboxMessageRecord | None: ...

    def dispatch_claimed(
        self,
        message: OutboxMessageRecord,
        *,
        ack_worker_id: str | None = None,
        lease_guard=None,
    ) -> OwnerDispatchResult: ...


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
        research_lease_renewal_seconds: float | None = None,
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
        renewal_seconds = (
            min(max(float(lock_seconds) / 3.0, 1.0), 30.0)
            if research_lease_renewal_seconds is None
            else float(research_lease_renewal_seconds)
        )
        if renewal_seconds <= 0:
            raise ValueError("research_lease_renewal_seconds must be positive")
        self._research_lease_renewal_seconds = min(renewal_seconds, max(float(lock_seconds) / 2.0, 0.1))
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
        recovered = self._recover_startup_work()
        if recovered:
            self._record_heartbeat(
                "RUNNING",
                f"research_demo_recovery_scheduled:{recovered}",
                metadata={"research_demo_recovery_scheduled": str(recovered)},
            )
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
                limit=_claim_limit_for_consumer(consumer, self._claim_limit),
                lock_seconds=self._lock_seconds,
            )
            claimed += len(messages)
            for message in messages:
                try:
                    with self._active_research_dispatch(client, message) as lease_guard:
                        dispatch_result = client.dispatch_claimed(
                            message,
                            ack_worker_id=self._worker_id if _is_long_running_research_consumer(message.consumer) else None,
                            lease_guard=lease_guard if _is_long_running_research_consumer(message.consumer) else None,
                        )
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

    def _active_research_dispatch(self, client: DurableMessageClient, message: OutboxMessageRecord):
        if not _is_long_running_research_consumer(message.consumer):
            return _NoopRenewal()
        return _ResearchLeaseRenewal(
            worker=self,
            client=client,
            message=message,
            interval_seconds=self._research_lease_renewal_seconds,
            lock_seconds=self._lock_seconds,
        )

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

    def _recover_startup_work(self) -> int:
        client = self._message_client_factory()
        recover = getattr(client, "recover_startup_research_demos", None)
        if not callable(recover):
            return 0
        return int(recover())


def build_target_trading_worker(
    *,
    factory: PostgresConnectionFactory,
    runtime_store: PostgresRuntimeStore,
    operator_executor: OperatorExecutionExecutor | None = None,
    research_backtest_executor: ResearchBacktestExecutionExecutor | None = None,
    research_demo_executor: ResearchDemoExecutionExecutor | None = None,
    worker_id: str | None = None,
    consumers: Iterable[str] = TRADING_WORKER_CONSUMERS,
    poll_seconds: float = 5.0,
) -> TargetTradingWorker:
    return TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: _PostgresMessageClient(
            factory,
            operator_executor=operator_executor,
            research_backtest_executor=research_backtest_executor,
            research_demo_executor=research_demo_executor,
        ),
        worker_id=worker_id,
        consumers=consumers,
        poll_seconds=poll_seconds,
    )


class _PostgresMessageClient:
    def __init__(
        self,
        factory: PostgresConnectionFactory,
        *,
        operator_executor: OperatorExecutionExecutor | None = None,
        research_backtest_executor: ResearchBacktestExecutionExecutor | None = None,
        research_demo_executor: ResearchDemoExecutionExecutor | None = None,
    ) -> None:
        self._factory = factory
        self._operator_executor = operator_executor
        self._research_backtest_executor = research_backtest_executor
        self._research_demo_executor = research_demo_executor

    def claim_outbox(self, **kwargs):
        from triggertrade.persistence import DurableMessageStore

        with PostgresUnitOfWork(self._factory) as uow:
            return DurableMessageStore(uow.connection).claim_outbox(**kwargs)

    def renew_outbox_lock(self, **kwargs):
        from triggertrade.persistence import DurableMessageStore

        with PostgresUnitOfWork(self._factory) as uow:
            return DurableMessageStore(uow.connection).renew_outbox_lock(**kwargs)

    def dispatch_claimed(
        self,
        message: OutboxMessageRecord,
        *,
        ack_worker_id: str | None = None,
        lease_guard=None,
    ) -> OwnerDispatchResult:
        from triggertrade.services.owner_dispatch import CanonicalOwnerDispatcher

        with PostgresUnitOfWork(self._factory) as uow:
            return CanonicalOwnerDispatcher(
                uow.connection,
                operator_executor=self._operator_executor,
                research_backtest_executor=self._research_backtest_executor,
                research_demo_executor=self._research_demo_executor,
            ).dispatch(message, ack_worker_id=ack_worker_id, lease_guard=lease_guard)

    def recover_startup_research_demos(self) -> int:
        from triggertrade.services.research_demo_execution import ResearchDemoExecutionStore

        with PostgresUnitOfWork(self._factory) as uow:
            store = ResearchDemoExecutionStore(uow.connection)
            records = store.list_resume_candidates()
            scheduled = 0
            for record in records:
                if store.enqueue_startup_recovery(record):
                    scheduled += 1
            return scheduled


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


def _is_long_running_research_consumer(consumer: str) -> bool:
    return consumer in {RESEARCH_BACKTEST_CONSUMER, RESEARCH_DEMO_CONSUMER}


def _claim_limit_for_consumer(consumer: str, default_limit: int) -> int:
    return 1 if _is_long_running_research_consumer(consumer) else default_limit


class _NoopRenewal:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        return False

    def assert_active(self) -> None:
        return None


class _ResearchLeaseRenewal:
    def __init__(
        self,
        *,
        worker: TargetTradingWorker,
        client: DurableMessageClient,
        message: OutboxMessageRecord,
        interval_seconds: float,
        lock_seconds: int,
    ) -> None:
        self._worker = worker
        self._client = client
        self._message = message
        self._interval_seconds = interval_seconds
        self._lock_seconds = lock_seconds
        self._stop = threading.Event()
        self._failure: Exception | None = None
        self._thread = threading.Thread(
            target=self._run,
            name=f"tt-lease-renewal-{message.message_id[:32]}",
            daemon=False,
        )

    def __enter__(self):
        self._worker._record_heartbeat(
            "RUNNING",
            "research_dispatch_active",
            metadata={
                "message_id": self._message.message_id,
                "consumer": self._message.consumer,
                "message_type": self._message.message_type,
                "lease_renewal": "active",
            },
        )
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        self._stop.set()
        self._thread.join()
        return False

    def assert_active(self) -> None:
        if self._failure is not None:
            raise OwnerDispatchBlocked(str(self._failure)) from self._failure

    def _run(self) -> None:
        while not self._stop.wait(self._interval_seconds):
            try:
                renewed = self._client.renew_outbox_lock(
                    message_id=self._message.message_id,
                    worker_id=self._worker.worker_id,
                    lock_seconds=self._lock_seconds,
                )
            except Exception as exc:  # noqa: BLE001 - renewal failure must block final acknowledgement.
                self._failure = OwnerDispatchBlocked("research_dispatch_lease_renewal_failed")
                self._failure.__cause__ = exc
                self._worker._record_heartbeat(
                    "BLOCKED",
                    "research_dispatch_lease_renewal_failed",
                    metadata={
                        "message_id": self._message.message_id,
                        "consumer": self._message.consumer,
                        "message_type": self._message.message_type,
                    },
                )
                self._stop.set()
                return
            if renewed is None:
                self._failure = OwnerDispatchBlocked("research_dispatch_lease_ownership_lost")
                self._worker._record_heartbeat(
                    "BLOCKED",
                    "research_dispatch_lease_renewal_lost",
                    metadata={
                        "message_id": self._message.message_id,
                        "consumer": self._message.consumer,
                        "message_type": self._message.message_type,
                    },
                )
                self._stop.set()
                return
            self._worker._record_heartbeat(
                "RUNNING",
                "research_dispatch_active",
                metadata={
                    "message_id": self._message.message_id,
                    "consumer": self._message.consumer,
                    "message_type": self._message.message_type,
                    "lease_renewed": "true",
                    "lock_expires_at": renewed.lock_expires_at.isoformat()
                    if renewed.lock_expires_at is not None
                    else None,
                },
            )
