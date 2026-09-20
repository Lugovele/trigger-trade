from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.order_specs import order_spec_digest
from triggertrade.persistence import (
    DurableMessageStore,
    OrderSpecConflict,
    OrderSpecStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.persistence.postgres import PostgresPersistenceError
from tests.unit.test_capital_grants import build_grant
from tests.unit.test_order_specs import valid_order_spec
from tests.unit.test_position_construction import constructed_result


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_pos004_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_order_spec_store_persists_replays_and_publishes_outbox():
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
        ]
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        grant = build_grant()
        spec = valid_order_spec(grant)
        construction = constructed_result(grant, order_spec_digest_value=order_spec_digest(spec))

        with PostgresUnitOfWork(factory) as uow:
            store = OrderSpecStore(uow.connection)
            record, inserted = store.record(construction_result=construction, order_spec=spec)
            assert inserted is True
            replayed, inserted = store.record(construction_result=construction, order_spec=spec)
            assert inserted is False
            assert replayed.payload_digest == record.payload_digest
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id="order-spec-1")
            assert outbox is not None
            assert outbox.producer == "Position"
            assert outbox.consumer == "Lifecycle"
            assert outbox.message_type == "ORDER_SPEC"
            assert outbox.dedupe_key == "ORDER_SPEC:construction-result-1"

        with PostgresUnitOfWork(factory) as restarted:
            stored = OrderSpecStore(restarted.connection).get_by_construction_result_id(
                construction_result_id="construction-result-1"
            )
        assert stored is not None
        assert stored.order_spec_id == "order-spec-1"
        assert stored.payload_digest == order_spec_digest(spec)
    finally:
        _drop_schema(settings)


def test_order_spec_store_rejects_changed_duplicate_and_invalid_digest():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        grant = build_grant()
        spec = valid_order_spec(grant)
        construction = constructed_result(grant, order_spec_digest_value=order_spec_digest(spec))
        changed = valid_order_spec(grant)
        changed["order_spec"]["spec_created_at"] = "2026-09-15T00:00:01Z"
        changed_construction = constructed_result(grant, order_spec_digest_value=order_spec_digest(changed))
        wrong_digest = constructed_result(grant, order_spec_digest_value="b" * 64)

        with PostgresUnitOfWork(factory) as uow:
            store = OrderSpecStore(uow.connection)
            store.record(construction_result=construction, order_spec=spec)
            with pytest.raises(OrderSpecConflict):
                store.record(construction_result=changed_construction, order_spec=changed)
            with pytest.raises(PostgresPersistenceError, match="order_spec_digest"):
                store.record(construction_result=wrong_digest, order_spec=spec)
    finally:
        _drop_schema(settings)
