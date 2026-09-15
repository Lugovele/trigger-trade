from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.coins_scope import CoinScopeDelta, CoinsAction, build_coins_contract
from triggertrade.persistence import (
    CoinsScopeConflict,
    CoinsScopeStore,
    DurableMessageStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.persistence.postgres import OwnerStateRevisionConflict, PostgresPersistenceError


pytest.importorskip("psycopg")

NOW = "2026-09-15T00:00:00Z"


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_pr002_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_coins_scope_store_publishes_outbox_and_set_applies_newer_revisions_only():
    settings = _settings()
    try:
        assert [migration.version for migration in apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)] == [
            "0001",
            "0002",
            "0003",
            "0004",
            "0005",
        ]
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        open_payload = build_coins_contract(
            event_id="coins-open-1",
            occurred_at=NOW,
            symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=1, action=CoinsAction.OPEN),),
        ).to_payload()
        delayed_close_payload = build_coins_contract(
            event_id="coins-close-delayed",
            occurred_at=NOW,
            symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=0, action=CoinsAction.CLOSE),),
        ).to_payload()

        with PostgresUnitOfWork(factory) as uow:
            store = CoinsScopeStore(uow.connection)
            records, inserted = store.publish(
                event_id="coins-open-1",
                occurred_at=NOW,
                symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=1, action=CoinsAction.OPEN),),
            )
            assert inserted is True
            assert records[0].payload == open_payload
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id="coins-open-1")
            assert outbox is not None
            assert outbox.producer == "Portfolio"
            assert outbox.consumer == "Set"
            assert outbox.message_type == "COINS"

        with PostgresUnitOfWork(factory) as uow:
            store = CoinsScopeStore(uow.connection)
            result = store.apply_to_set(open_payload)
            assert [state.scope_revision for state in result.applied] == [1]
            assert result.ignored == ()
            delayed = store.apply_to_set(delayed_close_payload)
            assert delayed.applied == ()
            assert [delta.scope_revision for delta in delayed.ignored] == [0]
            current = store.get_set_scope(symbol="BTCUSDT")
            assert current is not None
            assert current.action is CoinsAction.OPEN
            assert current.scope_revision == 1
    finally:
        _drop_schema(settings)


def test_coins_scope_store_replays_identical_publication_and_rejects_stale_or_changed_revision():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            store = CoinsScopeStore(uow.connection)
            records, inserted = store.publish(
                event_id="coins-open-1",
                occurred_at=NOW,
                symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=1, action=CoinsAction.OPEN),),
            )
            assert inserted is True
            replayed, inserted = store.publish(
                event_id="coins-open-1",
                occurred_at=NOW,
                symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=1, action=CoinsAction.OPEN),),
            )
            assert inserted is False
            assert replayed[0].payload_digest == records[0].payload_digest
            with pytest.raises(OwnerStateRevisionConflict):
                store.publish(
                    event_id="coins-close-0",
                    occurred_at=NOW,
                    symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=0, action=CoinsAction.CLOSE),),
                )
            with pytest.raises(CoinsScopeConflict):
                store.publish(
                    event_id="coins-open-changed",
                    occurred_at=NOW,
                    symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=1, action=CoinsAction.CLOSE),),
                )
    finally:
        _drop_schema(settings)


def test_set_intake_rejects_malformed_coins_payload_before_canonicalizing():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        valid = build_coins_contract(
            event_id="coins-open-1",
            occurred_at=NOW,
            symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=1, action=CoinsAction.OPEN),),
        ).to_payload()
        unknown_field = {
            "coins": {
                **valid["coins"],
                "unexpected": "silently-droppable",
            }
        }
        wrong_type = {
            "coins": {
                **valid["coins"],
                "event_id": 123,
            }
        }
        with PostgresUnitOfWork(factory) as uow:
            store = CoinsScopeStore(uow.connection)
            with pytest.raises(PostgresPersistenceError, match="unknown fields"):
                store.apply_to_set(unknown_field)
            with pytest.raises(PostgresPersistenceError, match="event_id"):
                store.apply_to_set(wrong_type)
    finally:
        _drop_schema(settings)
