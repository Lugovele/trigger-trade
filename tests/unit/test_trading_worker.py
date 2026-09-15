from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from triggertrade.persistence import RuntimeHeartbeat
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
        self.inbox_records: list[dict[str, object]] = []

    def claim_outbox(self, **kwargs):
        self.claims.append(kwargs)
        if kwargs["consumer"] == "Portfolio":
            return self._messages
        return ()

    def record_inbox(self, **kwargs):
        self.inbox_records.append(kwargs)
        return SimpleNamespace(status="RECEIVED"), True


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
    assert {claim["consumer"] for claim in client.claims} == {"Portfolio", "Set", "Position", "Lifecycle"}


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
    assert result.detail == "handler_not_certified:Portfolio:APPROVE_REJECT"
    assert client.inbox_records == []
    assert runtime_store.heartbeats[-1].status == "BLOCKED"
    assert runtime_store.heartbeats[-1].metadata["message_id"] == "msg-1"
