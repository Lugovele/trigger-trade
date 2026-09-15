from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    CapitalGrantConflict,
    CapitalGrantStore,
    DurableMessageStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.persistence.postgres import PostgresPersistenceError
from tests.unit.test_capital_grants import approved_decision, build_grant


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_pr003_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_capital_grant_store_persists_replays_and_publishes_outbox():
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
        ]
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        decision = approved_decision()
        grant = build_grant(decision)

        with PostgresUnitOfWork(factory) as uow:
            store = CapitalGrantStore(uow.connection)
            record, inserted = store.issue(approved_decision=decision, capital_grant=grant)
            assert inserted is True
            replayed, inserted = store.issue(approved_decision=decision, capital_grant=grant)
            assert inserted is False
            assert replayed.payload_digest == record.payload_digest
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id="grant-1")
            assert outbox is not None
            assert outbox.producer == "Portfolio"
            assert outbox.consumer == "Position"
            assert outbox.message_type == "CAPITAL_AND_LIMITS"

        with PostgresUnitOfWork(factory) as restarted:
            stored = CapitalGrantStore(restarted.connection).get_by_position_decision(
                position_decision_id="position-decision-1"
            )
        assert stored is not None
        assert stored.capital_grant_id == "grant-1"
    finally:
        _drop_schema(settings)


def test_capital_grant_store_rejects_changed_duplicate_and_reject_decision():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        decision = approved_decision()
        grant = build_grant(decision)
        changed = build_grant(decision)
        changed["capital_and_limits"]["remaining_global_slots"] = 3
        rejected = approved_decision()
        rejected["position_decision"]["decision"] = "REJECT"

        with PostgresUnitOfWork(factory) as uow:
            store = CapitalGrantStore(uow.connection)
            store.issue(approved_decision=decision, capital_grant=grant)
            with pytest.raises(CapitalGrantConflict):
                store.issue(approved_decision=decision, capital_grant=changed)
            with pytest.raises(PostgresPersistenceError, match="APPROVE"):
                store.issue(approved_decision=rejected, capital_grant=grant)
    finally:
        _drop_schema(settings)
