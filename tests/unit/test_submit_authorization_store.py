from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    DurableMessageStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    SubmitAuthorizationConflict,
    SubmitAuthorizationStore,
    apply_postgres_migrations,
)
from triggertrade.persistence.postgres import PostgresPersistenceError
from triggertrade.submit_authorizations import build_submit_authorized
from tests.unit.test_capital_grants import NOW, build_grant
from tests.unit.test_submit_authorizations import constructed_result


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_pr004_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_submit_authorization_store_persists_replays_and_publishes_outbox():
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
        ]
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        grant = build_grant()
        construction = constructed_result(grant)
        authorization = _authorization(grant, construction)

        with PostgresUnitOfWork(factory) as uow:
            store = SubmitAuthorizationStore(uow.connection)
            record, inserted = store.authorize(
                capital_grant=grant,
                construction_result=construction,
                submit_authorized=authorization,
            )
            assert inserted is True
            replayed, inserted = store.authorize(
                capital_grant=grant,
                construction_result=construction,
                submit_authorized=authorization,
            )
            assert inserted is False
            assert replayed.payload_digest == record.payload_digest
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id="auth-1")
            assert outbox is not None
            assert outbox.producer == "Portfolio"
            assert outbox.consumer == "Lifecycle"
            assert outbox.message_type == "SUBMIT_AUTHORIZED"
            assert outbox.causation_id == "construction-result-1"

        with PostgresUnitOfWork(factory) as restarted:
            stored = SubmitAuthorizationStore(restarted.connection).get_by_construction_result_id(
                construction_result_id="construction-result-1"
            )
        assert stored is not None
        assert stored.authorization_id == "auth-1"
        assert stored.held_committed_capital == "100"
    finally:
        _drop_schema(settings)


def test_submit_authorization_store_rejects_changed_duplicate_and_invalid_authorization():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        grant = build_grant()
        construction = constructed_result(grant)
        authorization = _authorization(grant, construction)
        changed = _authorization(grant, construction)
        changed["submit_authorized"]["held_committed_capital"] = "99"
        mismatched = _authorization(grant, construction)
        mismatched["submit_authorized"]["order_spec_id"] = "different-spec"

        with PostgresUnitOfWork(factory) as uow:
            store = SubmitAuthorizationStore(uow.connection)
            store.authorize(
                capital_grant=grant,
                construction_result=construction,
                submit_authorized=authorization,
            )
            with pytest.raises(SubmitAuthorizationConflict):
                store.authorize(
                    capital_grant=grant,
                    construction_result=construction,
                    submit_authorized=changed,
                )
            with pytest.raises(PostgresPersistenceError, match="order_spec_id"):
                store.authorize(
                    capital_grant=grant,
                    construction_result=construction,
                    submit_authorized=mismatched,
                )
    finally:
        _drop_schema(settings)


def test_submit_authorization_store_fences_grant_to_one_hold():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        grant = build_grant()
        construction = constructed_result(grant)
        authorization = _authorization(grant, construction)
        second_construction = constructed_result(grant)
        second_construction["position_construction_result"]["construction_result_id"] = "construction-result-2"
        second_construction["position_construction_result"]["order_spec_id"] = "order-spec-2"
        second_authorization = build_submit_authorized(
            authorization_id="auth-2",
            capital_grant=grant,
            construction_result=second_construction,
            authorized_at=NOW,
        ).to_payload()

        with PostgresUnitOfWork(factory) as uow:
            store = SubmitAuthorizationStore(uow.connection)
            store.authorize(
                capital_grant=grant,
                construction_result=construction,
                submit_authorized=authorization,
            )
            with pytest.raises(SubmitAuthorizationConflict):
                store.authorize(
                    capital_grant=grant,
                    construction_result=second_construction,
                    submit_authorized=second_authorization,
                )
    finally:
        _drop_schema(settings)


def _authorization(grant: dict[str, object], construction: dict[str, object]) -> dict[str, object]:
    return build_submit_authorized(
        authorization_id="auth-1",
        capital_grant=grant,
        construction_result=construction,
        authorized_at=NOW,
    ).to_payload()
