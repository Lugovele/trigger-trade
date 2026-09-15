from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    LifecycleStartGateConflict,
    LifecycleStartGateStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.persistence.postgres import PostgresPersistenceError
from tests.unit.test_lifecycle_start_gate import valid_gate_inputs


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_ol001_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_lifecycle_start_gate_store_persists_and_replays_ready_gate():
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
        spec, authorization = valid_gate_inputs()

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleStartGateStore(uow.connection)
            record, inserted = store.accept(
                start_gate_id="start-gate-1",
                order_spec=spec,
                submit_authorized=authorization,
            )
            assert inserted is True
            replayed, inserted = store.accept(
                start_gate_id="start-gate-1",
                order_spec=spec,
                submit_authorized=authorization,
            )
            assert inserted is False
            assert replayed.payload_digest == record.payload_digest

        with PostgresUnitOfWork(factory) as restarted:
            stored = LifecycleStartGateStore(restarted.connection).get_by_order_spec_id(order_spec_id="order-spec-1")
        assert stored is not None
        assert stored.lifecycle_state == "READY_TO_SUBMIT"
        assert stored.authorization_id == "auth-1"
    finally:
        _drop_schema(settings)


def test_lifecycle_start_gate_store_rejects_changed_duplicate_and_mismatch():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        spec, authorization = valid_gate_inputs()
        changed = dict(authorization)
        changed["submit_authorized"] = dict(authorization["submit_authorized"])
        changed["submit_authorized"]["authorization_id"] = "auth-2"
        mismatched = dict(authorization)
        mismatched["submit_authorized"] = dict(authorization["submit_authorized"])
        mismatched["submit_authorized"]["symbol"] = "ETHUSDT"

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleStartGateStore(uow.connection)
            store.accept(
                start_gate_id="start-gate-1",
                order_spec=spec,
                submit_authorized=authorization,
            )
            with pytest.raises(LifecycleStartGateConflict):
                store.accept(
                    start_gate_id="start-gate-1",
                    order_spec=spec,
                    submit_authorized=changed,
                )
            with pytest.raises(PostgresPersistenceError, match="symbol"):
                store.accept(
                    start_gate_id="start-gate-2",
                    order_spec=spec,
                    submit_authorized=mismatched,
                )
    finally:
        _drop_schema(settings)
