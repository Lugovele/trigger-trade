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
from tests.unit.test_set_scope import configuration_binding


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
            "0006",
            "0007",
            "0008",
            "0009",
            "0010",
            "0011",
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
            result = store.apply_to_set(open_payload, configuration_binding=configuration_binding())
            assert [state.scope_revision for state in result.applied] == [1]
            assert result.ignored == ()
            assert [epoch.formation_epoch for epoch in result.opened_epochs] == [1]
            delayed = store.apply_to_set(delayed_close_payload)
            assert delayed.applied == ()
            assert [delta.scope_revision for delta in delayed.ignored] == [0]
            current = store.get_set_scope(symbol="BTCUSDT")
            assert current is not None
            assert current.action is CoinsAction.OPEN
            assert current.scope_revision == 1
            active_epoch = store.get_active_formation_epoch(symbol="BTCUSDT")
            assert active_epoch is not None
            assert active_epoch.formation_epoch == 1
            assert active_epoch.configuration_binding == configuration_binding()
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


def test_set_scope_epochs_reset_on_close_and_newer_open_and_survive_restart():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        open_10 = build_coins_contract(
            event_id="coins-open-10",
            occurred_at=NOW,
            symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=10, action=CoinsAction.OPEN),),
        ).to_payload()
        close_11 = build_coins_contract(
            event_id="coins-close-11",
            occurred_at=NOW,
            symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=11, action=CoinsAction.CLOSE),),
        ).to_payload()
        open_12 = build_coins_contract(
            event_id="coins-open-12",
            occurred_at=NOW,
            symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=12, action=CoinsAction.OPEN),),
        ).to_payload()

        with PostgresUnitOfWork(factory) as uow:
            store = CoinsScopeStore(uow.connection)
            opened = store.apply_to_set(open_10, configuration_binding=configuration_binding())
            assert [epoch.formation_epoch for epoch in opened.opened_epochs] == [10]
            closed = store.apply_to_set(close_11)
            assert [epoch.formation_epoch for epoch in closed.terminated_epochs] == [10]
            reopened = store.apply_to_set(open_12, configuration_binding=configuration_binding())
            assert [epoch.formation_epoch for epoch in reopened.opened_epochs] == [12]

        with PostgresUnitOfWork(factory) as restarted:
            store = CoinsScopeStore(restarted.connection)
            old_epoch = store.get_formation_epoch(symbol="BTCUSDT", formation_epoch=10)
            active_epoch = store.get_active_formation_epoch(symbol="BTCUSDT")
        assert old_epoch is not None
        assert old_epoch.epoch_state == "TERMINATED"
        assert old_epoch.terminated_by_scope_revision == 11
        assert old_epoch.terminated_by_action == "CLOSE"
        assert active_epoch is not None
        assert active_epoch.formation_epoch == 12
        assert active_epoch.epoch_state == "ACTIVE"
    finally:
        _drop_schema(settings)


def test_newer_open_supersedes_previous_unfinished_epoch_and_binding_is_required():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        open_10 = build_coins_contract(
            event_id="coins-open-10",
            occurred_at=NOW,
            symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=10, action=CoinsAction.OPEN),),
        ).to_payload()
        open_12 = build_coins_contract(
            event_id="coins-open-12",
            occurred_at=NOW,
            symbols=(CoinScopeDelta(symbol="BTCUSDT", scope_revision=12, action=CoinsAction.OPEN),),
        ).to_payload()

        with PostgresUnitOfWork(factory) as uow:
            store = CoinsScopeStore(uow.connection)
            with pytest.raises(PostgresPersistenceError, match="configuration binding"):
                store.apply_to_set(open_10)
            store.apply_to_set(open_10, configuration_binding=configuration_binding())
            superseded = store.apply_to_set(open_12, configuration_binding=configuration_binding())
            assert [epoch.formation_epoch for epoch in superseded.terminated_epochs] == [10]
            assert [epoch.formation_epoch for epoch in superseded.opened_epochs] == [12]
            old_epoch = store.get_formation_epoch(symbol="BTCUSDT", formation_epoch=10)
            assert old_epoch is not None
            assert old_epoch.terminated_by_scope_revision == 12
            assert old_epoch.terminated_by_action == "OPEN"
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
