from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.persistence.postgres import (
    OwnerStateConflict,
    OwnerStateRevisionConflict,
    OwnerStateStore,
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_test_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_postgres_settings_never_accepts_unsafe_schema_identifier():
    with pytest.raises(PostgresPersistenceError):
        PostgresSettings(dsn="postgresql://example.invalid/db", schema="public;select")


def test_migrations_owner_state_restart_rollback_and_cas():
    settings = _settings()
    try:
        applied = apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        assert [migration.version for migration in applied] == ["0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008"]
        assert apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema) == ()

        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        initial_payload = {"status": "LIVE", "bucket": "portfolio", "revision_note": "initial"}
        with PostgresUnitOfWork(factory) as uow:
            store = OwnerStateStore(uow.connection)
            record, inserted = store.put_if_absent(
                owner="Portfolio Rules",
                state_type="portfolio_state",
                state_id="portfolio:main",
                payload=initial_payload,
            )
            assert inserted is True
            assert record.revision == 1
            assert record.payload_digest == canonical_json_digest(initial_payload)

        with PostgresUnitOfWork(factory) as restarted:
            store = OwnerStateStore(restarted.connection)
            existing = store.get(
                owner="Portfolio Rules",
                state_type="portfolio_state",
                state_id="portfolio:main",
            )
            assert existing is not None
            assert existing.payload["status"] == "LIVE"
            updated = store.compare_and_set(
                owner="Portfolio Rules",
                state_type="portfolio_state",
                state_id="portfolio:main",
                expected_revision=1,
                payload={"status": "RECONCILING", "bucket": "portfolio"},
            )
            assert updated.revision == 2
            with pytest.raises(OwnerStateRevisionConflict):
                store.compare_and_set(
                    owner="Portfolio Rules",
                    state_type="portfolio_state",
                    state_id="portfolio:main",
                    expected_revision=1,
                    payload={"status": "STALE", "bucket": "portfolio"},
                )
            with pytest.raises(OwnerStateConflict):
                store.put_if_absent(
                    owner="Portfolio Rules",
                    state_type="portfolio_state",
                    state_id="portfolio:main",
                    payload={"status": "DIFFERENT"},
                )

        with pytest.raises(RuntimeError):
            with PostgresUnitOfWork(factory) as rolled_back:
                store = OwnerStateStore(rolled_back.connection)
                store.put_if_absent(
                    owner="Set",
                    state_type="cycle",
                    state_id="cycle:rollback",
                    payload={"status": "MATCHED"},
                )
                raise RuntimeError("force rollback")

        with PostgresUnitOfWork(factory) as verify:
            store = OwnerStateStore(verify.connection)
            assert (
                store.get(owner="Set", state_type="cycle", state_id="cycle:rollback")
                is None
            )
    finally:
        _drop_schema(settings)
