from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from triggertrade.persistence import RuntimeHeartbeat
from triggertrade.services.owner_dispatch import OwnerDispatchBlocked, OwnerDispatchResult
from triggertrade.services.operator_execution_bridge import OPERATOR_EXECUTION_CONSUMER
from triggertrade.services.research_demo_execution import RESEARCH_DEMO_CONSUMER
from triggertrade.services.trading_worker import TargetTradingWorker


class FakeRuntimeStore:
    def __init__(self) -> None:
        self.heartbeats: list[RuntimeHeartbeat] = []

    def record_heartbeat(self, heartbeat: RuntimeHeartbeat) -> RuntimeHeartbeat:
        self.heartbeats.append(heartbeat)
        return heartbeat


class FakeMessageClient:
    def __init__(self, messages=()) -> None:
        self._messages = tuple(messages)
        self.claims: list[dict[str, object]] = []
        self.dispatched = []

    def claim_outbox(self, **kwargs):
        self.claims.append(kwargs)
        return tuple(message for message in self._messages if message.consumer == kwargs["consumer"])

    def dispatch_claimed(self, message):
        self.dispatched.append(message)
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
    assert {claim["consumer"] for claim in client.claims} == {
        "Portfolio",
        "Set",
        "Position",
        "Lifecycle",
        OPERATOR_EXECUTION_CONSUMER,
        RESEARCH_DEMO_CONSUMER,
    }


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
