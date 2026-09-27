from __future__ import annotations

import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.persistence.durable_messages import DurableMessageConflict, DurableMessageStore
from triggertrade.persistence.postgres import (
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.persistence.research_promotion_governance import ResearchPromotionGovernanceStore


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_msg_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def _payload(event_id: str = "event-1") -> dict[str, object]:
    return {
        "contract_type": "COINS",
        "event_id": event_id,
        "coins": [{"symbol": "BTCUSDT", "scope_revision": 1}],
    }


def test_outbox_append_restart_dedupe_and_conflict():
    settings = _settings()
    try:
        assert [migration.version for migration in apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)] == [
            "0001",
            "0002",
            "0003",
            "0004",
            "0005",
            "0006",
            "0007",
            "0008",
            "0009",
            "0010",
            "0011",
            "0012",
            "0013",
            "0014",
            "0015",
            "0016",
            "0017",
            "0018",
            "0019",
            "0020",
            "0021",
            "0022",
        ]
        assert apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema) == ()
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            record, inserted = store.append_outbox(
                message_id="msg-1",
                producer="Portfolio Rules",
                consumer="Set",
                message_type="COINS",
                message_version="2",
                aggregate_id="scope:BTCUSDT",
                dedupe_key="scope:BTCUSDT:1",
                payload=_payload(),
            )
            assert inserted is True
            assert record.status == "PENDING"
            assert record.payload_digest == canonical_json_digest(_payload())

        with PostgresUnitOfWork(factory) as restarted:
            store = DurableMessageStore(restarted.connection)
            replay, inserted = store.append_outbox(
                message_id="msg-1",
                producer="Portfolio Rules",
                consumer="Set",
                message_type="COINS",
                message_version="2",
                aggregate_id="scope:BTCUSDT",
                dedupe_key="scope:BTCUSDT:1",
                payload=_payload(),
            )
            assert inserted is False
            assert replay.message_id == "msg-1"

            dedupe_replay, inserted = store.append_outbox(
                message_id="msg-duplicate-delivery-id",
                producer="Portfolio Rules",
                consumer="Set",
                message_type="COINS",
                message_version="2",
                aggregate_id="scope:BTCUSDT",
                dedupe_key="scope:BTCUSDT:1",
                payload=_payload(),
            )
            assert inserted is False
            assert dedupe_replay.message_id == "msg-1"

            with pytest.raises(DurableMessageConflict):
                store.append_outbox(
                    message_id="msg-1",
                    producer="Portfolio Rules",
                    consumer="Set",
                    message_type="COINS",
                    message_version="2",
                    payload=_payload("event-changed"),
                )
            with pytest.raises(DurableMessageConflict):
                store.append_outbox(
                    message_id="msg-1",
                    producer="Portfolio Rules",
                    consumer="Set",
                    message_type="COINS",
                    message_version="2",
                    aggregate_id="scope:ETHUSDT",
                    dedupe_key="scope:BTCUSDT:1",
                    payload=_payload(),
                )
    finally:
        _drop_schema(settings)


def test_competing_consumers_claim_disjoint_outbox_messages():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            for index in range(4):
                store.append_outbox(
                    message_id=f"msg-{index}",
                    producer="Position Rules",
                    consumer="Portfolio Rules",
                    message_type="APPROVE_REJECT",
                    message_version="5",
                    payload=_payload(f"event-{index}"),
                )

        def claim(worker_id: str) -> tuple[str, ...]:
            with PostgresUnitOfWork(factory) as uow:
                store = DurableMessageStore(uow.connection)
                return tuple(
                    message.message_id
                    for message in store.claim_outbox(
                        consumer="Portfolio Rules",
                        worker_id=worker_id,
                        limit=3,
                    )
                )

        with ThreadPoolExecutor(max_workers=2) as pool:
            future_a = pool.submit(claim, "worker-a")
            future_b = pool.submit(claim, "worker-b")
            worker_a = future_a.result()
            worker_b = future_b.result()

        assert set(worker_a).isdisjoint(worker_b)
        assert len(set(worker_a) | set(worker_b)) == 4
    finally:
        _drop_schema(settings)


def test_outbox_lock_renewal_prevents_reclaim_without_incrementing_attempts():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            store.append_outbox(
                message_id="research-backtest-start-unit",
                producer="Research",
                consumer="ResearchBacktestExecution",
                message_type="RESEARCH_BACKTEST_START",
                message_version="1",
                payload={"research_backtest": {"backtest_run_id": "rbt-unit"}},
            )
            claimed = store.claim_outbox(
                consumer="ResearchBacktestExecution",
                worker_id="worker-a",
                limit=1,
                lock_seconds=5,
            )
            assert len(claimed) == 1
            assert claimed[0].attempt_count == 1

        time.sleep(0.5)
        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            renewed = store.renew_outbox_lock(
                message_id="research-backtest-start-unit",
                worker_id="worker-a",
                lock_seconds=5,
            )
            assert renewed is not None
            assert renewed.locked_by == "worker-a"
            assert renewed.attempt_count == 1

        time.sleep(0.5)
        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            reclaimed = store.claim_outbox(
                consumer="ResearchBacktestExecution",
                worker_id="worker-b",
                limit=1,
                lock_seconds=5,
            )
            current = store.get_outbox(message_id="research-backtest-start-unit")
            assert reclaimed == ()
            assert current is not None
            assert current.locked_by == "worker-a"
            assert current.attempt_count == 1
    finally:
        _drop_schema(settings)


def test_outbox_wrong_owner_cannot_renew_lock():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            store.append_outbox(
                message_id="research-backtest-wrong-owner",
                producer="Research",
                consumer="ResearchBacktestExecution",
                message_type="RESEARCH_BACKTEST_START",
                message_version="1",
                payload={"research_backtest": {"backtest_run_id": "rbt-wrong-owner"}},
            )
            claimed = store.claim_outbox(
                consumer="ResearchBacktestExecution",
                worker_id="worker-a",
                limit=1,
                lock_seconds=30,
            )
            assert len(claimed) == 1

            renewed = store.renew_outbox_lock(
                message_id="research-backtest-wrong-owner",
                worker_id="worker-b",
                lock_seconds=30,
            )
            current = store.get_outbox(message_id="research-backtest-wrong-owner")

            assert renewed is None
            assert current is not None
            assert current.locked_by == "worker-a"
            assert current.attempt_count == 1
    finally:
        _drop_schema(settings)


def test_outbox_expired_owner_cannot_resurrect_lock():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            store.append_outbox(
                message_id="research-demo-expired-renewal",
                producer="Research",
                consumer="ResearchDemoExecution",
                message_type="RESEARCH_DEMO_START",
                message_version="1",
                payload={"research_demo": {"demo_run_id": "rdm-expired-renewal"}},
            )
            claimed = store.claim_outbox(
                consumer="ResearchDemoExecution",
                worker_id="worker-a",
                limit=1,
                lock_seconds=1,
            )
            assert len(claimed) == 1

        time.sleep(1.2)
        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            renewed = store.renew_outbox_lock(
                message_id="research-demo-expired-renewal",
                worker_id="worker-a",
                lock_seconds=30,
            )
            current = store.get_outbox(message_id="research-demo-expired-renewal")

            assert renewed is None
            assert current is not None
            assert current.locked_by == "worker-a"
            assert current.attempt_count == 1
            assert current.lock_expires_at == claimed[0].lock_expires_at
    finally:
        _drop_schema(settings)


def test_outbox_dead_worker_recovery_after_renewal_stops():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            store.append_outbox(
                message_id="research-demo-recheck-unit",
                producer="Research",
                consumer="ResearchDemoExecution",
                message_type="RESEARCH_DEMO_START",
                message_version="1",
                payload={"research_demo": {"demo_run_id": "rdm-unit"}},
            )
            first_claim = store.claim_outbox(
                consumer="ResearchDemoExecution",
                worker_id="worker-a",
                limit=1,
                lock_seconds=1,
            )
            assert len(first_claim) == 1
            renewed = store.renew_outbox_lock(
                message_id="research-demo-recheck-unit",
                worker_id="worker-a",
                lock_seconds=1,
            )
            assert renewed is not None

        time.sleep(1.2)
        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            reclaimed = store.claim_outbox(
                consumer="ResearchDemoExecution",
                worker_id="worker-b",
                limit=1,
                lock_seconds=1,
            )
            assert len(reclaimed) == 1
            assert reclaimed[0].locked_by == "worker-b"
            assert reclaimed[0].attempt_count == 2
    finally:
        _drop_schema(settings)


def test_stale_worker_cannot_consume_after_reclaim():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            store.append_outbox(
                message_id="research-backtest-stale-consume",
                producer="Research",
                consumer="ResearchBacktestExecution",
                message_type="RESEARCH_BACKTEST_START",
                message_version="1",
                payload={"research_backtest": {"backtest_run_id": "rbt-stale-consume"}},
            )
            first = store.claim_outbox(
                consumer="ResearchBacktestExecution",
                worker_id="worker-a",
                limit=1,
                lock_seconds=1,
            )
            assert len(first) == 1

        time.sleep(1.2)
        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            second = store.claim_outbox(
                consumer="ResearchBacktestExecution",
                worker_id="worker-b",
                limit=1,
                lock_seconds=30,
            )
            assert len(second) == 1
            stale_consume = store.mark_outbox_consumed_by_owner(
                message_id="research-backtest-stale-consume",
                worker_id="worker-a",
            )
            current = store.get_outbox(message_id="research-backtest-stale-consume")

            assert stale_consume is None
            assert current is not None
            assert current.status == "IN_FLIGHT"
            assert current.locked_by == "worker-b"
            assert current.consumed_at is None
            assert current.attempt_count == 2
    finally:
        _drop_schema(settings)


def test_inbox_replay_is_noop_and_changed_content_fails_closed():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = DurableMessageStore(uow.connection)
            receipt, inserted = store.record_inbox(
                consumer="Lifecycle",
                message_id="msg-spec-1",
                producer="Position Rules",
                message_type="ORDER_SPEC",
                message_version="5",
                payload=_payload(),
            )
            assert inserted is True
            assert receipt.status == "RECEIVED"
            processed = store.mark_inbox_processed(consumer="Lifecycle", message_id="msg-spec-1")
            assert processed.status == "PROCESSED"

        with PostgresUnitOfWork(factory) as replayed:
            store = DurableMessageStore(replayed.connection)
            receipt, inserted = store.record_inbox(
                consumer="Lifecycle",
                message_id="msg-spec-1",
                producer="Position Rules",
                message_type="ORDER_SPEC",
                message_version="5",
                payload=_payload(),
            )
            assert inserted is False
            assert receipt.status == "PROCESSED"

            with pytest.raises(DurableMessageConflict):
                store.record_inbox(
                    consumer="Lifecycle",
                    message_id="msg-spec-1",
                    producer="Position Rules",
                    message_type="ORDER_SPEC",
                    message_version="5",
                    payload=_payload("event-changed"),
                )
    finally:
        _drop_schema(settings)


def test_research_promotion_governance_records_owner_state_and_outbox():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        payload = {
            "research_promotion_request": {
                "request_id": "research-promotion:unit-1",
                "research_id": "research-1",
                "target": {"set_id": "set-1", "set_version": "v1", "rules_version_id": "rules-1"},
                "safety": {"sqlite_active_mutation": False, "live_order_side_effect": False},
            }
        }

        with PostgresUnitOfWork(factory) as uow:
            store = ResearchPromotionGovernanceStore(uow.connection)
            record = store.request_promotion(
                request_id="research-promotion:unit-1",
                payload=payload,
                research_id="research-1",
                idempotency_key="unit-1",
            )
            replay = store.request_promotion(
                request_id="research-promotion:unit-1",
                payload=payload,
                research_id="research-1",
                idempotency_key="unit-1",
            )

            assert record.inserted is True
            assert replay.inserted is False
            assert record.state.payload_digest == canonical_json_digest(payload)
            assert replay.outbox.message_id == "research-promotion:unit-1"
            assert replay.outbox.consumer == "Scheduler"
            assert replay.outbox.message_type == "RESEARCH_PROMOTION_REQUESTED"
    finally:
        _drop_schema(settings)


def test_legacy_user_message_store_remains_distinct_from_business_messages(tmp_path):
    from triggertrade.persistence.message_store import MessageStore

    user_message = MessageStore(tmp_path / "messages.sqlite3").create_message(
        body="operator notice",
        severity="INFO",
        source="unit",
    )

    assert user_message.message_id.startswith("msg_")
