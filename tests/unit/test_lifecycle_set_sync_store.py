from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    DurableMessageStore,
    LifecycleSetSyncStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from tests.unit.test_lifecycle_set_sync import placed_event_payload, terminal_event_payload


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_ol004_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_lifecycle_set_sync_store_publishes_placement_replays_and_recovers_state():
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
        ]
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        payload = placed_event_payload()

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleSetSyncStore(uow.connection)
            result = store.publish_from_order_event(payload)
            replayed = store.publish_from_order_event(payload)

        with PostgresUnitOfWork(factory) as restarted:
            state = LifecycleSetSyncStore(restarted.connection).get(decision_cycle_id="decision-cycle-1")
            outbox = DurableMessageStore(restarted.connection).get_outbox(message_id="order-placed-9c6314924e273662e5bb5eae")

        assert result.sync is not None
        assert result.inserted is True
        assert result.published is True
        assert result.outbox_message is not None
        assert result.outbox_message.consumer == "Set"
        assert result.outbox_message.causation_id == "order-event-1"
        assert replayed.inserted is False
        assert replayed.published is False
        assert state is not None
        assert state.placement_lifecycle_revision == 1
        assert state.terminal_lifecycle_revision is None
        assert outbox is not None
        assert outbox.payload == result.sync.payload
    finally:
        _drop_schema(settings)


def test_terminal_tombstone_suppresses_delayed_older_placement():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        terminal = terminal_event_payload(event_id="terminal-event-1", lifecycle_revision=3)
        delayed_placement = placed_event_payload(event_id="delayed-placement", lifecycle_revision=2)

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleSetSyncStore(uow.connection)
            terminal_result = store.publish_from_order_event(terminal)
            delayed_result = store.publish_from_order_event(delayed_placement)

        with PostgresUnitOfWork(factory) as restarted:
            state = LifecycleSetSyncStore(restarted.connection).get(decision_cycle_id="decision-cycle-1")
            delayed_outbox = DurableMessageStore(restarted.connection).get_outbox(
                message_id="order-placed-1e7072526fc45107ebc04e79"
            )

        assert terminal_result.published is True
        assert delayed_result.published is False
        assert delayed_result.suppressed_reason == "terminal_tombstone_dominates"
        assert state is not None
        assert state.terminal_lifecycle_revision == 3
        assert state.terminal_event_type == "CANCELLED_ZERO_FILL"
        assert delayed_outbox is None
    finally:
        _drop_schema(settings)


def test_delayed_older_placement_does_not_overwrite_newer_placement_state():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        newer_placement = placed_event_payload(event_id="newer-placement", lifecycle_revision=3)
        delayed_placement = placed_event_payload(event_id="delayed-placement", lifecycle_revision=2)

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleSetSyncStore(uow.connection)
            newer_result = store.publish_from_order_event(newer_placement)
            delayed_result = store.publish_from_order_event(delayed_placement)

        with PostgresUnitOfWork(factory) as restarted:
            state = LifecycleSetSyncStore(restarted.connection).get(decision_cycle_id="decision-cycle-1")

        assert newer_result.published is True
        assert delayed_result.published is True
        assert state is not None
        assert state.last_lifecycle_revision == 3
        assert state.placement_lifecycle_revision == 3
        assert state.placement_event_id == newer_result.sync.body["event_id"]
        assert state.payload == newer_result.sync.payload
    finally:
        _drop_schema(settings)


def test_non_sync_eligible_order_event_does_not_persist_or_publish():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        payload = placed_event_payload(event_id="ambiguous-placement")
        payload["order_event"]["order_leg"]["exchange_order_id"] = None

        with PostgresUnitOfWork(factory) as uow:
            result = LifecycleSetSyncStore(uow.connection).publish_from_order_event(payload)

        assert result.published is False
        assert result.suppressed_reason == "not_sync_eligible"
        assert result.state is None
    finally:
        _drop_schema(settings)
