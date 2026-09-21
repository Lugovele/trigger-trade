from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.persistence.durable_messages import (
    DurableMessageConflict,
    DurableMessageStore,
    TransportFrontierGap,
)
from triggertrade.persistence.postgres import (
    OwnerStateConflict,
    OwnerStateStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)


pytest.importorskip("psycopg")


EXPECTED_MIGRATIONS = [
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


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_frontier_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def _payload(event_id: str) -> dict[str, object]:
    return {
        "contract_type": "ORDER_EVENT",
        "event_id": event_id,
        "contract_version": 7,
        "symbol": "BTCUSDT",
    }


def _migrate(settings: PostgresSettings) -> PostgresConnectionFactory:
    applied = apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
    assert [migration.version for migration in applied] == EXPECTED_MIGRATIONS
    assert apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema) == ()
    return PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)


def test_owner_state_outbox_inbox_share_one_atomic_unit_of_work():
    settings = _settings()
    try:
        factory = _migrate(settings)

        def write_once(identifier: str, *, fail_after: str | None = None) -> None:
            with PostgresUnitOfWork(factory) as uow:
                state = OwnerStateStore(uow.connection)
                messages = DurableMessageStore(uow.connection)
                if fail_after == "before_owner":
                    raise RuntimeError("forced pre-owner rollback")
                state.put_if_absent(
                    owner="Lifecycle",
                    state_type="committed_prefix_probe",
                    state_id=identifier,
                    payload={"state": "accepted", "identifier": identifier},
                )
                if fail_after == "after_owner":
                    raise RuntimeError("forced post-owner rollback")
                messages.append_outbox(
                    message_id=f"{identifier}:outbox",
                    producer="Lifecycle",
                    consumer="Portfolio Rules",
                    message_type="ORDER_EVENT",
                    message_version="7",
                    payload=_payload(identifier),
                )
                if fail_after == "after_outbox":
                    raise RuntimeError("forced post-outbox rollback")
                messages.record_inbox(
                    consumer="Portfolio Rules",
                    message_id=f"{identifier}:outbox",
                    producer="Lifecycle",
                    message_type="ORDER_EVENT",
                    message_version="7",
                    payload=_payload(identifier),
                )
                messages.mark_inbox_processed(
                    consumer="Portfolio Rules",
                    message_id=f"{identifier}:outbox",
                )
                if fail_after == "after_inbox":
                    raise RuntimeError("forced post-inbox rollback")

        for cutpoint in ("before_owner", "after_owner", "after_outbox", "after_inbox"):
            identifier = f"rollback:{cutpoint}"
            with pytest.raises(RuntimeError):
                write_once(identifier, fail_after=cutpoint)
            with PostgresUnitOfWork(factory) as verify:
                state = OwnerStateStore(verify.connection)
                messages = DurableMessageStore(verify.connection)
                assert state.get(
                    owner="Lifecycle",
                    state_type="committed_prefix_probe",
                    state_id=identifier,
                ) is None
                assert messages.get_outbox(message_id=f"{identifier}:outbox") is None
                assert messages.get_inbox(
                    consumer="Portfolio Rules",
                    message_id=f"{identifier}:outbox",
                ) is None

        write_once("committed")
        with PostgresUnitOfWork(factory) as replay:
            state = OwnerStateStore(replay.connection)
            messages = DurableMessageStore(replay.connection)
            record, inserted = state.put_if_absent(
                owner="Lifecycle",
                state_type="committed_prefix_probe",
                state_id="committed",
                payload={"state": "accepted", "identifier": "committed"},
            )
            outbox, outbox_inserted = messages.append_outbox(
                message_id="committed:outbox",
                producer="Lifecycle",
                consumer="Portfolio Rules",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=_payload("committed"),
            )
            inbox, inbox_inserted = messages.record_inbox(
                consumer="Portfolio Rules",
                message_id="committed:outbox",
                producer="Lifecycle",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=_payload("committed"),
            )
            assert inserted is False
            assert outbox_inserted is False
            assert inbox_inserted is False
            assert record.payload_digest == canonical_json_digest({"state": "accepted", "identifier": "committed"})
            assert outbox.payload_digest == canonical_json_digest(_payload("committed"))
            assert inbox.status == "PROCESSED"

        with PostgresUnitOfWork(factory) as conflict:
            state = OwnerStateStore(conflict.connection)
            messages = DurableMessageStore(conflict.connection)
            with pytest.raises(OwnerStateConflict):
                state.put_if_absent(
                    owner="Lifecycle",
                    state_type="committed_prefix_probe",
                    state_id="committed",
                    payload={"state": "changed"},
                )
            with pytest.raises(DurableMessageConflict):
                messages.append_outbox(
                    message_id="committed:outbox",
                    producer="Lifecycle",
                    consumer="Portfolio Rules",
                    message_type="ORDER_EVENT",
                    message_version="7",
                    payload=_payload("changed"),
                )
            with pytest.raises(DurableMessageConflict):
                messages.record_inbox(
                    consumer="Portfolio Rules",
                    message_id="committed:outbox",
                    producer="Lifecycle",
                    message_type="ORDER_EVENT",
                    message_version="7",
                    payload=_payload("changed"),
                )
    finally:
        _drop_schema(settings)


def test_committed_prefix_frontier_acceptance_matrix():
    settings = _settings()
    try:
        factory = _migrate(settings)
        scope = "account:demo:BTCUSDT"

        with PostgresUnitOfWork(factory) as publish:
            store = DurableMessageStore(publish.connection)
            outbox_1, frontier_1, inserted_1 = store.append_frontier_outbox(
                scope_key=scope,
                message_id="frontier:1",
                producer="Lifecycle",
                consumer="Portfolio Rules",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=_payload("frontier:1"),
            )
            outbox_2, frontier_2, inserted_2 = store.append_frontier_outbox(
                scope_key=scope,
                message_id="frontier:2",
                producer="Lifecycle",
                consumer="Portfolio Rules",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=_payload("frontier:2"),
            )
            replay_outbox, replay_frontier, replay_inserted = store.append_frontier_outbox(
                scope_key=scope,
                message_id="frontier:2",
                producer="Lifecycle",
                consumer="Portfolio Rules",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=_payload("frontier:2"),
            )
            assert inserted_1 is True
            assert inserted_2 is True
            assert replay_inserted is False
            assert outbox_1.message_id == "frontier:1"
            assert outbox_2.message_id == replay_outbox.message_id
            assert frontier_1.sequence == 1
            assert frontier_2.sequence == 2
            assert replay_frontier.sequence == 2

        with PostgresUnitOfWork(factory) as consume:
            store = DurableMessageStore(consume.connection)
            assert store.get_frontier_head(scope_key=scope).committed_head == 2
            assert tuple(message.sequence for message in store.list_frontier_messages(scope_key=scope)) == (1, 2)
            applied = store.apply_frontier_prefix(
                scope_key=scope,
                consumer="Portfolio Rules",
                through_sequence=2,
            )
            assert applied.applied_sequence == 2
            stale_replay = store.apply_frontier_prefix(
                scope_key=scope,
                consumer="Portfolio Rules",
                through_sequence=1,
            )
            assert stale_replay.applied_sequence == 2

        with PostgresUnitOfWork(factory) as isolated:
            store = DurableMessageStore(isolated.connection)
            _, eth_frontier, _ = store.append_frontier_outbox(
                scope_key="account:demo:ETHUSDT",
                message_id="frontier:eth:1",
                producer="Lifecycle",
                consumer="Portfolio Rules",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=_payload("frontier:eth:1"),
            )
            assert eth_frontier.sequence == 1
            assert store.get_frontier_head(scope_key=scope).committed_head == 2

        with pytest.raises(RuntimeError):
            with PostgresUnitOfWork(factory) as publisher_rollback:
                store = DurableMessageStore(publisher_rollback.connection)
                store.append_frontier_outbox(
                    scope_key=scope,
                    message_id="frontier:rollback",
                    producer="Lifecycle",
                    consumer="Portfolio Rules",
                    message_type="ORDER_EVENT",
                    message_version="7",
                    payload=_payload("frontier:rollback"),
                )
                raise RuntimeError("force publisher rollback")

        with PostgresUnitOfWork(factory) as verify_rollback:
            store = DurableMessageStore(verify_rollback.connection)
            assert store.get_frontier_head(scope_key=scope).committed_head == 2
            assert store.get_outbox(message_id="frontier:rollback") is None

        with pytest.raises(RuntimeError):
            with PostgresUnitOfWork(factory) as consumer_rollback:
                store = DurableMessageStore(consumer_rollback.connection)
                store.apply_frontier_prefix(
                    scope_key=scope,
                    consumer="RestartProbe",
                    through_sequence=2,
                )
                raise RuntimeError("force consumer rollback")
        with PostgresUnitOfWork(factory) as verify_consumer_rollback:
            store = DurableMessageStore(verify_consumer_rollback.connection)
            assert store.get_frontier_applied(scope_key=scope, consumer="RestartProbe") is None

        with PostgresUnitOfWork(factory) as consumer_first:
            store = DurableMessageStore(consumer_first.connection)
            applied = store.apply_frontier_prefix(
                scope_key="account:demo:XRPUSDT",
                consumer="Portfolio Rules",
                through_sequence=0,
            )
            assert applied.applied_sequence == 0
        with PostgresUnitOfWork(factory) as publisher_later:
            store = DurableMessageStore(publisher_later.connection)
            _, frontier, _ = store.append_frontier_outbox(
                scope_key="account:demo:XRPUSDT",
                message_id="frontier:xrp:1",
                producer="Lifecycle",
                consumer="Portfolio Rules",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=_payload("frontier:xrp:1"),
            )
            assert frontier.sequence == 1
        with PostgresUnitOfWork(factory) as consume_later:
            store = DurableMessageStore(consume_later.connection)
            applied = store.apply_frontier_prefix(
                scope_key="account:demo:XRPUSDT",
                consumer="Portfolio Rules",
                through_sequence=1,
            )
            assert applied.applied_sequence == 1

        with PostgresUnitOfWork(factory) as restart:
            store = DurableMessageStore(restart.connection)
            assert store.get_frontier_head(scope_key=scope).committed_head == 2
            assert store.get_frontier_applied(scope_key=scope, consumer="Portfolio Rules").applied_sequence == 2
            assert [message.message_id for message in store.list_frontier_messages(scope_key=scope)] == [
                "frontier:1",
                "frontier:2",
            ]

        with PostgresUnitOfWork(factory) as conflict:
            store = DurableMessageStore(conflict.connection)
            with pytest.raises(DurableMessageConflict):
                store.append_frontier_outbox(
                    scope_key=scope,
                    message_id="frontier:1",
                    producer="Lifecycle",
                    consumer="Portfolio Rules",
                    message_type="ORDER_EVENT",
                    message_version="7",
                    payload=_payload("changed"),
                )
    finally:
        _drop_schema(settings)


def test_frontier_gap_fails_closed_until_missing_committed_sequence_arrives():
    settings = _settings()
    try:
        factory = _migrate(settings)
        scope = "account:demo:gap"
        with PostgresUnitOfWork(factory) as setup:
            store = DurableMessageStore(setup.connection)
            first, _, _ = store.append_frontier_outbox(
                scope_key=scope,
                message_id="gap:1",
                producer="Lifecycle",
                consumer="Portfolio Rules",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=_payload("gap:1"),
            )
            second, _ = store.append_outbox(
                message_id="gap:2",
                producer="Lifecycle",
                consumer="Portfolio Rules",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=_payload("gap:2"),
            )
            assert first.message_id == "gap:1"
            with setup.connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE triggertrade_transport_frontier_heads
                    SET committed_head = 2
                    WHERE scope_key = %s
                    """,
                    (scope,),
                )

        with PostgresUnitOfWork(factory) as blocked:
            store = DurableMessageStore(blocked.connection)
            with pytest.raises(TransportFrontierGap):
                store.apply_frontier_prefix(
                    scope_key=scope,
                    consumer="Portfolio Rules",
                    through_sequence=2,
                )

        with PostgresUnitOfWork(factory) as repair:
            with repair.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO triggertrade_transport_frontier_messages (
                        scope_key, sequence, message_id, payload_digest
                    ) VALUES (%s, 2, %s, %s)
                    """,
                    (scope, "gap:2", second.payload_digest),
                )
            store = DurableMessageStore(repair.connection)
            applied = store.apply_frontier_prefix(
                scope_key=scope,
                consumer="Portfolio Rules",
                through_sequence=2,
            )
            assert applied.applied_sequence == 2
    finally:
        _drop_schema(settings)


def test_frontier_publishers_serialize_per_scope_without_cross_scope_blocking():
    settings = _settings()
    try:
        factory = _migrate(settings)

        def publish(scope: str, message_id: str) -> tuple[str, int]:
            with PostgresUnitOfWork(factory) as uow:
                store = DurableMessageStore(uow.connection)
                _, frontier, _ = store.append_frontier_outbox(
                    scope_key=scope,
                    message_id=message_id,
                    producer="Lifecycle",
                    consumer="Portfolio Rules",
                    message_type="ORDER_EVENT",
                    message_version="7",
                    payload=_payload(message_id),
                )
                return scope, frontier.sequence

        with ThreadPoolExecutor(max_workers=4) as pool:
            same_scope = tuple(
                pool.map(
                    lambda value: publish("account:demo:BTCUSDT", value),
                    ("concurrent:btc:1", "concurrent:btc:2"),
                )
            )
            mixed_scope = tuple(
                pool.map(
                    lambda item: publish(*item),
                    (
                        ("account:demo:ETHUSDT", "concurrent:eth:1"),
                        ("account:demo:XRPUSDT", "concurrent:xrp:1"),
                    ),
                )
            )

        assert {sequence for _, sequence in same_scope} == {1, 2}
        assert mixed_scope == (
            ("account:demo:ETHUSDT", 1),
            ("account:demo:XRPUSDT", 1),
        )
    finally:
        _drop_schema(settings)
