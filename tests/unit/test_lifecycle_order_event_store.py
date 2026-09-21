from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.lifecycle_order_events import build_order_event_from_submission
from triggertrade.persistence import (
    LifecycleOrderEventConflict,
    LifecycleOrderEventStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from tests.unit.test_lifecycle_submission_store import fake_submission_record


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_ol003_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_lifecycle_order_event_store_appends_replays_and_lists_by_tranche():
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
        ]
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        payload = build_order_event_from_submission(
            fake_submission_record(),
            event_id="order-event-1",
            occurred_at="2026-09-14T12:00:00Z",
            lifecycle_revision=1,
        ).payload

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleOrderEventStore(uow.connection)
            record, inserted = store.append(payload)
            replayed, replay_inserted = store.append(payload)
            listed = store.list_for_tranche(tranche_id="tranche-1")

        assert inserted is True
        assert replay_inserted is False
        assert replayed.payload_digest == record.payload_digest
        assert record.event_variant == "LOGICAL_TRANCHE"
        assert record.lifecycle_revision == 1
        assert record.client_order_link_id == "client-order-1"
        assert [event.event_id for event in listed] == ["order-event-1"]
    finally:
        _drop_schema(settings)


def test_lifecycle_order_event_store_rejects_conflicting_replay_and_duplicate_revision():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        payload = build_order_event_from_submission(
            fake_submission_record(),
            event_id="order-event-1",
            occurred_at="2026-09-14T12:00:00Z",
            lifecycle_revision=1,
        ).payload
        changed = build_order_event_from_submission(
            fake_submission_record(lifecycle_state="SUBMITTING"),
            event_id="order-event-1",
            occurred_at="2026-09-14T12:00:01Z",
            lifecycle_revision=1,
        ).payload
        duplicate_revision = build_order_event_from_submission(
            fake_submission_record(lifecycle_state="SUBMITTING"),
            event_id="order-event-2",
            occurred_at="2026-09-14T12:00:01Z",
            lifecycle_revision=1,
        ).payload

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleOrderEventStore(uow.connection)
            store.append(payload)
            with pytest.raises(LifecycleOrderEventConflict):
                store.append(changed)
            with pytest.raises(LifecycleOrderEventConflict):
                store.append(duplicate_revision)
    finally:
        _drop_schema(settings)
