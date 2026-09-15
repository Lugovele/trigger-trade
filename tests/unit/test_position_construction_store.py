from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    DurableMessageStore,
    PositionConstructionConflict,
    PositionConstructionStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.persistence.postgres import PostgresPersistenceError
from tests.unit.test_capital_grants import build_grant
from tests.unit.test_position_construction import constructed_result


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_pos003_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_position_construction_store_persists_replays_and_publishes_outbox():
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
        ]
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        grant = build_grant()
        construction = constructed_result(grant)

        with PostgresUnitOfWork(factory) as uow:
            store = PositionConstructionStore(uow.connection)
            record, inserted = store.record(capital_grant=grant, construction_result=construction)
            assert inserted is True
            replayed, inserted = store.record(capital_grant=grant, construction_result=construction)
            assert inserted is False
            assert replayed.payload_digest == record.payload_digest
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id="construction-result-1")
            assert outbox is not None
            assert outbox.producer == "Position"
            assert outbox.consumer == "Portfolio"
            assert outbox.message_type == "APPROVE_REJECT"
            assert outbox.dedupe_key == "CONSTRUCTION_RESULT:grant-1"

        with PostgresUnitOfWork(factory) as restarted:
            stored = PositionConstructionStore(restarted.connection).get_by_capital_grant_id(capital_grant_id="grant-1")
        assert stored is not None
        assert stored.construction_result_id == "construction-result-1"
        assert stored.order_spec_digest == "a" * 64
    finally:
        _drop_schema(settings)


def test_position_construction_store_rejects_changed_duplicate_and_invalid_binding():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        grant = build_grant()
        construction = constructed_result(grant)
        changed = constructed_result(grant)
        changed["position_construction_result"]["order_spec_digest"] = "b" * 64
        mismatched = constructed_result(grant)
        mismatched["position_construction_result"]["capital_grant_id"] = "different-grant"

        with PostgresUnitOfWork(factory) as uow:
            store = PositionConstructionStore(uow.connection)
            store.record(capital_grant=grant, construction_result=construction)
            with pytest.raises(PositionConstructionConflict):
                store.record(capital_grant=grant, construction_result=changed)
            with pytest.raises(PostgresPersistenceError, match="capital_grant_id"):
                store.record(capital_grant=grant, construction_result=mismatched)
    finally:
        _drop_schema(settings)
