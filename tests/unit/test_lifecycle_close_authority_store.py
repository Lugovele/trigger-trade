from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    LifecycleCloseAuthorityConflict,
    LifecycleCloseIntentRecord,
    LifecycleCloseAuthorityStore,
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
    return PostgresSettings(dsn=dsn, schema=f"tt_ol006_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_acquire_insert_conflict_path_joins_existing_active_intent(monkeypatch):
    active_record = LifecycleCloseIntentRecord(
        close_intent_id="close-intent-1",
        tranche_id="tranche-1",
        intent_revision=0,
        state="ACQUIRED",
        native_side=None,
        confirmed_target_quantity="0",
        confirmed_residual_quantity="0",
        authorized_reduction_quantity="0",
        executed_reduction_quantity="0",
        close_commitment_quantity_basis="0",
        cause_event_ids=("cause-1",),
        entry_order_ids=(),
        protection_child_ids=(),
        unresolved_request_ids=(),
        payload={"lifecycle_close_intent": {"close_intent_id": "close-intent-1"}},
        payload_digest="0" * 64,
        acquired_at="2026-09-15 10:00:00+00",
        resolved_at=None,
    )
    joined = LifecycleCloseIntentRecord(
        **{**active_record.__dict__, "intent_revision": 1, "cause_event_ids": ("cause-1", "cause-2")}
    )
    store = LifecycleCloseAuthorityStore(_ConflictConnection())
    calls = {"select": 0}

    def fake_select(cursor, *, tranche_id, active):
        calls["select"] += 1
        return None if calls["select"] <= 2 else active_record

    def fake_append(cursor, *, intent, cause_event_id, cause_type, received_at):
        assert intent == active_record
        assert cause_event_id == "cause-2"
        return joined

    monkeypatch.setattr(store, "_select_for_update", fake_select)
    monkeypatch.setattr(store, "_append_cause_and_reload", fake_append)

    result = store.acquire_or_join(
        tranche_id="tranche-1",
        cause_event_id="cause-2",
        cause_type="MANUAL_CLOSE",
        received_at="2026-09-15T10:00:01Z",
    )

    assert result.acquired is False
    assert result.joined is True
    assert result.intent.cause_event_ids == ("cause-1", "cause-2")


def test_close_authority_store_acquires_joins_and_recovers_active_intent():
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

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleCloseAuthorityStore(uow.connection)
            acquired = store.acquire_or_join(
                tranche_id="tranche-1",
                cause_event_id="cause-tp-1",
                cause_type="TAKE_PROFIT",
                received_at="2026-09-15T10:00:00Z",
                native_side="SELL",
                confirmed_target_quantity="0.5",
                confirmed_residual_quantity="0.5",
                close_commitment_quantity_basis="0.5",
                entry_order_ids=("entry-client-1",),
                protection_child_ids=("tp-child-1", "sl-child-1"),
            )
            joined = store.acquire_or_join(
                tranche_id="tranche-1",
                cause_event_id="cause-manual-1",
                cause_type="MANUAL_CLOSE",
                received_at="2026-09-15T10:00:01Z",
            )

        with PostgresUnitOfWork(factory) as restarted:
            active = LifecycleCloseAuthorityStore(restarted.connection).get_active_for_tranche(tranche_id="tranche-1")

        assert acquired.acquired is True
        assert joined.joined is True
        assert joined.intent.close_intent_id == acquired.intent.close_intent_id
        assert joined.intent.intent_revision == 1
        assert joined.intent.cause_event_ids == ("cause-tp-1", "cause-manual-1")
        assert active is not None
        assert active.close_intent_id == acquired.intent.close_intent_id
        assert active.protection_child_ids == ("tp-child-1", "sl-child-1")
    finally:
        _drop_schema(settings)


class _ConflictConnection:
    def cursor(self):
        return _ConflictCursor()


class _ConflictCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, *_args, **_kwargs):
        return None

    def fetchone(self):
        return None


def test_close_authority_store_persists_child_before_side_effect_and_blocks_second_open_child():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleCloseAuthorityStore(uow.connection)
            acquired = store.acquire_or_join(
                tranche_id="tranche-1",
                cause_event_id="cause-sl-1",
                cause_type="STOP_LOSS",
                received_at="2026-09-15T10:00:00Z",
                confirmed_target_quantity="1",
                confirmed_residual_quantity="1",
                close_commitment_quantity_basis="1",
            )
            child = store.authorize_reduction_child(
                close_intent_id=acquired.intent.close_intent_id,
                expected_intent_revision=acquired.intent.intent_revision,
                child_sequence=1,
                client_order_link_id="close-client-1",
                authorized_reduction_quantity="1",
                authorized_at="2026-09-15T10:00:02Z",
            )
            with pytest.raises(LifecycleCloseAuthorityConflict, match="unresolved child"):
                store.authorize_reduction_child(
                    close_intent_id=acquired.intent.close_intent_id,
                    expected_intent_revision=1,
                    child_sequence=2,
                    client_order_link_id="close-client-2",
                    authorized_reduction_quantity="1",
                    authorized_at="2026-09-15T10:00:03Z",
                )

        with PostgresUnitOfWork(factory) as restarted:
            children = LifecycleCloseAuthorityStore(restarted.connection).list_children(
                close_intent_id=acquired.intent.close_intent_id
            )

        assert child.client_order_link_id == "close-client-1"
        assert child.exchange_order_id is None
        assert child.state == "AUTHORIZED"
        assert [item.close_child_id for item in children] == [child.close_child_id]
    finally:
        _drop_schema(settings)


def test_resolved_close_intent_returns_tombstone_and_does_not_reacquire():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleCloseAuthorityStore(uow.connection)
            acquired = store.acquire_or_join(
                tranche_id="tranche-1",
                cause_event_id="cause-manual-1",
                cause_type="MANUAL_CLOSE",
                received_at="2026-09-15T10:00:00Z",
            )
            resolved = store.resolve_intent(
                close_intent_id=acquired.intent.close_intent_id,
                resolved_at="2026-09-15T10:05:00Z",
            )
            tombstone = store.acquire_or_join(
                tranche_id="tranche-1",
                cause_event_id="cause-manual-2",
                cause_type="MANUAL_CLOSE",
                received_at="2026-09-15T10:06:00Z",
            )

        assert resolved.state == "RESOLVED"
        assert tombstone.resolved_tombstone is True
        assert tombstone.intent.close_intent_id == acquired.intent.close_intent_id
        assert tombstone.acquired is False
        assert tombstone.joined is False
    finally:
        _drop_schema(settings)
