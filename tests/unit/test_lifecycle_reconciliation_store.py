from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.lifecycle_reconciliation import validate_reconciliation_event
from triggertrade.persistence import (
    LifecycleReconciliationConflict,
    LifecycleReconciliationStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)

from tests.unit.test_lifecycle_reconciliation import native_event, resolution_event, scope_resolution_event


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_ol008_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_store_detects_same_revision_content_conflict_without_postgres(monkeypatch):
    evidence = validate_reconciliation_event(resolution_event())
    store = LifecycleReconciliationStore(_ConflictConnection())
    marked = {"called": False}

    def mark(_cursor, *, native_observation_id):
        assert native_observation_id == "obs-1"
        marked["called"] = True

    monkeypatch.setattr(store, "_mark_integrity_conflict", mark)

    with pytest.raises(LifecycleReconciliationConflict, match="different content"):
        store._classify_revision(
            _ConflictCursor(rows=[("not-the-same-digest",)]),
            evidence=evidence,
            tombstone=_Tombstone(latest_evidence_revision=1),
        )

    assert marked["called"] is True


def test_store_blocks_newer_progress_after_resolved_tombstone_without_postgres(monkeypatch):
    evidence = validate_reconciliation_event(resolution_event(revision=2, complete=False))
    store = LifecycleReconciliationStore(_ConflictConnection())
    marked = {"called": False}

    def mark(_cursor, *, native_observation_id):
        assert native_observation_id == "obs-1"
        marked["called"] = True

    monkeypatch.setattr(store, "_mark_integrity_conflict", mark)

    with pytest.raises(LifecycleReconciliationConflict, match="resolved tombstone"):
        store._classify_revision(
            _ConflictCursor(rows=[]),
            evidence=evidence,
            tombstone=_Tombstone(latest_evidence_revision=1, state="RESOLVED"),
        )

    assert marked["called"] is True


def test_store_records_resolution_first_and_replays_later_observation():
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
            store = LifecycleReconciliationStore(uow.connection)
            resolved = store.record_event(resolution_event())
            later_observation = native_event()
            later_observation["order_event"]["event_id"] = "native-event-after-resolution"
            stale_observation = store.record_event(later_observation)

        with PostgresUnitOfWork(factory) as restarted:
            store = LifecycleReconciliationStore(restarted.connection)
            tombstone = store.get_tombstone(native_observation_id="obs-1")
            records = store.list_records(native_observation_id="obs-1")

        assert resolved.resolved is True
        assert stale_observation.stale is True
        assert stale_observation.record.accepted is False
        assert tombstone is not None
        assert tombstone.state == "RESOLVED"
        assert tombstone.unresolved_block_active is False
        assert [record.evidence_kind for record in records] == [
            "NATIVE_UNATTRIBUTED_REDUCTION",
            "NATIVE_ATTRIBUTION_RESOLUTION",
        ]
    finally:
        _drop_schema(settings)


def test_store_preserves_identical_replay_and_rejects_changed_identity():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleReconciliationStore(uow.connection)
            first = store.record_event(native_event())
            replay = store.record_event(native_event())
            changed = native_event(quantity="0.50")
            with pytest.raises(LifecycleReconciliationConflict, match="different content"):
                store.record_event(changed)

        assert first.inserted is True
        assert replay.replayed is True
    finally:
        _drop_schema(settings)


def test_store_supports_scope_resolution_first_replay():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            result = LifecycleReconciliationStore(uow.connection).record_event(scope_resolution_event())

        assert result.resolved is True
        assert result.tombstone.native_observation_id == "scope-obs-1"
        assert result.tombstone.state == "RESOLVED"
    finally:
        _drop_schema(settings)


class _Tombstone:
    native_observation_id = "obs-1"
    native_scope_revision = 1
    native_scope = {}
    latest_revision_id = "resolution-1"
    complete_payload_digest = None
    unresolved_block_active = True
    integrity_state = "CLEAR"

    def __init__(self, *, latest_evidence_revision, state="UNRESOLVED"):
        self.latest_evidence_revision = latest_evidence_revision
        self.state = state


class _ConflictConnection:
    def cursor(self):
        return _ConflictCursor()


class _ConflictCursor:
    def __init__(self, rows=None):
        self._rows = rows or []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, *_args, **_kwargs):
        return None

    def fetchall(self):
        return list(self._rows)
