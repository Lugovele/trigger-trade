from __future__ import annotations

import os
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


def test_legacy_user_message_store_remains_distinct_from_business_messages(tmp_path):
    from triggertrade.persistence.message_store import MessageStore

    user_message = MessageStore(tmp_path / "messages.sqlite3").create_message(
        body="operator notice",
        severity="INFO",
        source="unit",
    )

    assert user_message.message_id.startswith("msg_")
