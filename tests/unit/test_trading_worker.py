from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
import threading
import time

from triggertrade.persistence import RuntimeHeartbeat
from triggertrade.services.owner_dispatch import OwnerDispatchBlocked, OwnerDispatchResult
from triggertrade.services.operator_execution_bridge import OPERATOR_EXECUTION_CONSUMER
from triggertrade.services.research_backtest_execution import RESEARCH_BACKTEST_CONSUMER
from triggertrade.services.research_demo_execution import RESEARCH_DEMO_CONSUMER
from triggertrade.services.trading_worker import TargetTradingWorker


class FakeRuntimeStore:
    def __init__(self) -> None:
        self.heartbeats: list[RuntimeHeartbeat] = []

    def record_heartbeat(self, heartbeat: RuntimeHeartbeat) -> RuntimeHeartbeat:
        self.heartbeats.append(heartbeat)
        return heartbeat


class FakeMessageClient:
    def __init__(self, messages=(), dispatch_results=None, startup_recovered=0) -> None:
        self._messages = tuple(messages)
        self._dispatch_results = dict(dispatch_results or {})
        self._startup_recovered = startup_recovered
        self.recoveries = 0
        self.claims: list[dict[str, object]] = []
        self.dispatched = []
        self.consumed_message_ids = set()
        self.renewals: list[dict[str, object]] = []
        self.dispatch_started = threading.Event()
        self.release_dispatch = threading.Event()
        self.block_dispatch = False
        self.renewal_returns_none = False
        self.renewal_exception: Exception | None = None

    def recover_startup_research_demos(self):
        self.recoveries += 1
        return self._startup_recovered

    def claim_outbox(self, **kwargs):
        self.claims.append(kwargs)
        return tuple(
            message
            for message in self._messages
            if message.consumer == kwargs["consumer"] and message.message_id not in self.consumed_message_ids
        )[: int(kwargs.get("limit", 1))]

    def renew_outbox_lock(self, **kwargs):
        self.renewals.append(kwargs)
        if self.renewal_exception is not None:
            raise self.renewal_exception
        if self.renewal_returns_none:
            return None
        return SimpleNamespace(lock_expires_at=datetime(2026, 9, 15, 0, 1, tzinfo=UTC))

    def dispatch_claimed(self, message, *, ack_worker_id=None, lease_guard=None):
        self.dispatched.append(message)
        self.dispatch_started.set()
        if self.block_dispatch:
            self.release_dispatch.wait(timeout=2)
        if lease_guard is not None:
            lease_guard.assert_active()
        self.consumed_message_ids.add(message.message_id)
        if getattr(message, "message_type") in self._dispatch_results:
            return self._dispatch_results[message.message_type]
        if getattr(message, "message_type") == "ORDER_SPEC":
            return OwnerDispatchResult(processed=True, detail="processed:Lifecycle:ORDER_SPEC:start_gate")
        raise OwnerDispatchBlocked(
            f"handler_not_certified:{message.consumer}:{message.message_type}:{message.message_version}"
        )


def test_target_trading_worker_hydrates_and_idles_without_legacy_runtime():
    runtime_store = FakeRuntimeStore()
    client = FakeMessageClient()
    worker = TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: client,
        worker_id="worker-1",
        poll_seconds=1,
        sleeper=lambda _: None,
        clock=lambda: datetime(2026, 9, 15, tzinfo=UTC),
    )

    worker.run_forever(max_cycles=1)

    assert [heartbeat.status for heartbeat in runtime_store.heartbeats] == ["RUNNING", "RUNNING"]
    assert runtime_store.heartbeats[-1].detail == "idle"
    assert client.recoveries == 1
    assert {claim["consumer"] for claim in client.claims} == {
        "Portfolio",
        "Set",
        "Position",
        "Lifecycle",
        OPERATOR_EXECUTION_CONSUMER,
        RESEARCH_BACKTEST_CONSUMER,
        RESEARCH_DEMO_CONSUMER,
    }


def test_target_trading_worker_startup_recovery_without_running_demo_keeps_idle_behavior():
    runtime_store = FakeRuntimeStore()
    client = FakeMessageClient(startup_recovered=0)
    worker = TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: client,
        worker_id="worker-1",
        poll_seconds=1,
        sleeper=lambda _: None,
        clock=lambda: datetime(2026, 9, 15, tzinfo=UTC),
    )

    worker.run_forever(max_cycles=1)

    assert client.recoveries == 1
    assert client.dispatched == []
    assert [heartbeat.detail for heartbeat in runtime_store.heartbeats] == ["worker hydrated durable state", "idle"]


def test_target_trading_worker_startup_recovery_schedules_and_dispatches_running_demo_recheck():
    runtime_store = FakeRuntimeStore()
    message = SimpleNamespace(
        message_id="research-demo-recheck-recovered",
        producer="Research",
        consumer=RESEARCH_DEMO_CONSUMER,
        message_type="RESEARCH_DEMO_START",
        message_version="1",
        payload={"research_demo": {"demo_run_id": "rdm-existing"}},
    )
    client = FakeMessageClient(
        (message,),
        dispatch_results={"RESEARCH_DEMO_START": OwnerDispatchResult(processed=True, detail="research_demo_running:rdm-existing")},
        startup_recovered=1,
    )
    worker = TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: client,
        worker_id="worker-1",
        poll_seconds=1,
        sleeper=lambda _: None,
        clock=lambda: datetime(2026, 9, 15, tzinfo=UTC),
    )

    worker.run_forever(max_cycles=1)

    assert client.recoveries == 1
    assert client.dispatched == [message]
    assert runtime_store.heartbeats[1].detail == "research_demo_recovery_scheduled:1"
    assert runtime_store.heartbeats[-2].detail == "research_demo_running:rdm-existing"
    assert runtime_store.heartbeats[-2].metadata["message_id"] == "research-demo-recheck-recovered"


def test_target_trading_worker_startup_recovery_is_idempotent_across_cycles():
    runtime_store = FakeRuntimeStore()
    message = SimpleNamespace(
        message_id="research-demo-recheck-pending",
        producer="Research",
        consumer=RESEARCH_DEMO_CONSUMER,
        message_type="RESEARCH_DEMO_START",
        message_version="1",
        payload={"research_demo": {"demo_run_id": "rdm-existing"}},
    )
    client = FakeMessageClient(
        (message,),
        dispatch_results={"RESEARCH_DEMO_START": OwnerDispatchResult(processed=True, detail="research_demo_running:rdm-existing")},
        startup_recovered=1,
    )
    worker = TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: client,
        worker_id="worker-1",
        poll_seconds=1,
        sleeper=lambda _: None,
        clock=lambda: datetime(2026, 9, 15, tzinfo=UTC),
    )

    worker.run_forever(max_cycles=2)

    assert client.recoveries == 1
    assert client.dispatched == [message]
    assert runtime_store.heartbeats[-1].detail == "idle"


def test_target_trading_worker_startup_recovery_ignores_terminal_demo_candidates():
    runtime_store = FakeRuntimeStore()
    client = FakeMessageClient(startup_recovered=0)
    worker = TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: client,
        worker_id="worker-1",
        poll_seconds=1,
        sleeper=lambda _: None,
        clock=lambda: datetime(2026, 9, 15, tzinfo=UTC),
    )

    worker.run_forever(max_cycles=1)

    assert client.recoveries == 1
    assert client.dispatched == []
    assert runtime_store.heartbeats[-1].detail == "idle"


def test_target_trading_worker_fails_closed_for_unhandled_business_message():
    runtime_store = FakeRuntimeStore()
    message = SimpleNamespace(
        message_id="msg-1",
        producer="Set",
        consumer="Portfolio",
        message_type="APPROVE_REJECT",
        message_version="5",
        payload={"decision": "APPROVE"},
    )
    client = FakeMessageClient((message,))
    worker = TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: client,
        worker_id="worker-1",
        clock=lambda: datetime(2026, 9, 15, tzinfo=UTC),
    )

    result = worker.process_once()

    assert result.blocked is True
    assert result.detail == "handler_not_certified:Portfolio:APPROVE_REJECT:5"
    assert client.dispatched == [message]
    assert runtime_store.heartbeats[-1].status == "BLOCKED"
    assert runtime_store.heartbeats[-1].metadata["message_id"] == "msg-1"


def test_target_trading_worker_dispatches_registered_payload_complete_route():
    runtime_store = FakeRuntimeStore()
    message = SimpleNamespace(
        message_id="msg-1",
        producer="Position",
        consumer="Lifecycle",
        message_type="ORDER_SPEC",
        message_version="5",
        payload={"order_spec": {"order_spec_id": "spec-1"}},
    )
    client = FakeMessageClient((message,))
    worker = TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: client,
        worker_id="worker-1",
        clock=lambda: datetime(2026, 9, 15, tzinfo=UTC),
    )

    result = worker.process_once()

    assert result.blocked is False
    assert result.detail == "processed:1"
    assert client.dispatched == [message]
    assert runtime_store.heartbeats[-2].detail == "processed:Lifecycle:ORDER_SPEC:start_gate"


def test_target_trading_worker_research_demo_recheck_resume_records_running_heartbeat():
    runtime_store = FakeRuntimeStore()
    message = SimpleNamespace(
        message_id="research-demo-recheck-unit",
        producer="Research",
        consumer=RESEARCH_DEMO_CONSUMER,
        message_type="RESEARCH_DEMO_START",
        message_version="1",
        payload={"research_demo": {"demo_run_id": "rdm-unit-1"}},
    )
    client = FakeMessageClient(
        (message,),
        dispatch_results={"RESEARCH_DEMO_START": OwnerDispatchResult(processed=True, detail="research_demo_running:rdm-unit-1")},
    )
    worker = TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: client,
        worker_id="worker-1",
        clock=lambda: datetime(2026, 9, 15, tzinfo=UTC),
    )

    result = worker.process_once()

    assert result.blocked is False
    assert result.detail == "processed:1"
    assert client.dispatched == [message]
    assert runtime_store.heartbeats[-2].status == "RUNNING"
    assert runtime_store.heartbeats[-2].detail == "research_demo_running:rdm-unit-1"
    assert runtime_store.heartbeats[-2].metadata["message_id"] == "research-demo-recheck-unit"


def test_target_trading_worker_renews_research_lease_and_heartbeat_during_long_dispatch():
    runtime_store = FakeRuntimeStore()
    message = SimpleNamespace(
        message_id="research-backtest-start-unit",
        producer="Research",
        consumer=RESEARCH_BACKTEST_CONSUMER,
        message_type="RESEARCH_BACKTEST_START",
        message_version="1",
        payload={"research_backtest": {"backtest_run_id": "rbt-unit-1"}},
    )
    client = FakeMessageClient(
        (message,),
        dispatch_results={"RESEARCH_BACKTEST_START": OwnerDispatchResult(processed=True, detail="research_backtest_completed:rbt-unit-1")},
    )
    client.block_dispatch = True
    worker = TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: client,
        worker_id="worker-1",
        lock_seconds=2,
        research_lease_renewal_seconds=0.05,
        clock=lambda: datetime(2026, 9, 15, tzinfo=UTC),
    )

    thread = threading.Thread(target=worker.process_once)
    thread.start()
    assert client.dispatch_started.wait(timeout=1)
    deadline = time.monotonic() + 1
    while not client.renewals and time.monotonic() < deadline:
        time.sleep(0.01)
    client.release_dispatch.set()
    thread.join(timeout=2)

    assert not thread.is_alive()
    assert client.renewals
    assert {renewal["message_id"] for renewal in client.renewals} == {"research-backtest-start-unit"}
    assert all(renewal["worker_id"] == "worker-1" for renewal in client.renewals)
    active_heartbeats = [heartbeat for heartbeat in runtime_store.heartbeats if heartbeat.detail == "research_dispatch_active"]
    assert active_heartbeats
    assert any(heartbeat.metadata.get("lease_renewed") == "true" for heartbeat in active_heartbeats)


def test_target_trading_worker_blocks_ack_when_research_lease_is_lost():
    runtime_store = FakeRuntimeStore()
    message = SimpleNamespace(
        message_id="research-demo-recheck-lost",
        producer="Research",
        consumer=RESEARCH_DEMO_CONSUMER,
        message_type="RESEARCH_DEMO_START",
        message_version="1",
        payload={"research_demo": {"demo_run_id": "rdm-lost"}},
    )
    client = FakeMessageClient(
        (message,),
        dispatch_results={"RESEARCH_DEMO_START": OwnerDispatchResult(processed=True, detail="research_demo_running:rdm-lost")},
    )
    client.block_dispatch = True
    client.renewal_returns_none = True
    worker = TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: client,
        worker_id="worker-1",
        lock_seconds=2,
        research_lease_renewal_seconds=0.05,
        clock=lambda: datetime(2026, 9, 15, tzinfo=UTC),
    )

    thread_result = {}

    def run_worker():
        thread_result["result"] = worker.process_once()

    thread = threading.Thread(target=run_worker)
    thread.start()
    assert client.dispatch_started.wait(timeout=1)
    deadline = time.monotonic() + 1
    while not client.renewals and time.monotonic() < deadline:
        time.sleep(0.01)
    client.release_dispatch.set()
    thread.join(timeout=2)

    result = thread_result["result"]
    assert result.blocked is True
    assert result.detail == "research_dispatch_lease_ownership_lost"
    assert client.consumed_message_ids == set()
    assert runtime_store.heartbeats[-1].status == "BLOCKED"
    assert runtime_store.heartbeats[-1].detail == "research_dispatch_lease_ownership_lost"


def test_target_trading_worker_blocks_ack_when_research_renewal_raises():
    runtime_store = FakeRuntimeStore()
    message = SimpleNamespace(
        message_id="research-backtest-start-renewal-error",
        producer="Research",
        consumer=RESEARCH_BACKTEST_CONSUMER,
        message_type="RESEARCH_BACKTEST_START",
        message_version="1",
        payload={"research_backtest": {"backtest_run_id": "rbt-renewal-error"}},
    )
    client = FakeMessageClient(
        (message,),
        dispatch_results={"RESEARCH_BACKTEST_START": OwnerDispatchResult(processed=True, detail="research_backtest_completed:rbt-renewal-error")},
    )
    client.block_dispatch = True
    client.renewal_exception = RuntimeError("database unavailable")
    worker = TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: client,
        worker_id="worker-1",
        lock_seconds=2,
        research_lease_renewal_seconds=0.05,
        clock=lambda: datetime(2026, 9, 15, tzinfo=UTC),
    )

    thread_result = {}

    def run_worker():
        thread_result["result"] = worker.process_once()

    thread = threading.Thread(target=run_worker)
    thread.start()
    assert client.dispatch_started.wait(timeout=1)
    deadline = time.monotonic() + 1
    while not client.renewals and time.monotonic() < deadline:
        time.sleep(0.01)
    client.release_dispatch.set()
    thread.join(timeout=2)

    result = thread_result["result"]
    assert result.blocked is True
    assert result.detail == "research_dispatch_lease_renewal_failed"
    assert client.consumed_message_ids == set()
    assert runtime_store.heartbeats[-1].status == "BLOCKED"
    assert runtime_store.heartbeats[-1].detail == "research_dispatch_lease_renewal_failed"


def test_target_trading_worker_claims_research_messages_one_at_a_time():
    runtime_store = FakeRuntimeStore()
    research_messages = tuple(
        SimpleNamespace(
            message_id=f"research-backtest-start-{index}",
            producer="Research",
            consumer=RESEARCH_BACKTEST_CONSUMER,
            message_type="RESEARCH_BACKTEST_START",
            message_version="1",
            payload={"research_backtest": {"backtest_run_id": f"rbt-{index}"}},
        )
        for index in range(3)
    )
    lifecycle_messages = tuple(
        SimpleNamespace(
            message_id=f"lifecycle-{index}",
            producer="Position",
            consumer="Lifecycle",
            message_type="ORDER_SPEC",
            message_version="5",
            payload={"order_spec": {"order_spec_id": f"spec-{index}"}},
        )
        for index in range(3)
    )
    client = FakeMessageClient(
        (*research_messages, *lifecycle_messages),
        dispatch_results={"RESEARCH_BACKTEST_START": OwnerDispatchResult(processed=True, detail="research_backtest_completed")},
    )
    worker = TargetTradingWorker(
        runtime_store=runtime_store,
        message_client_factory=lambda: client,
        worker_id="worker-1",
        claim_limit=3,
        clock=lambda: datetime(2026, 9, 15, tzinfo=UTC),
    )

    worker.process_once()

    claims_by_consumer = {claim["consumer"]: claim["limit"] for claim in client.claims}
    assert claims_by_consumer["Lifecycle"] == 3
    assert claims_by_consumer[RESEARCH_BACKTEST_CONSUMER] == 1
    assert client.dispatched.count(research_messages[0]) == 1
    assert research_messages[1] not in client.dispatched
