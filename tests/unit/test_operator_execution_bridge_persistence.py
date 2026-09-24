from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import DurableMessageStore
from triggertrade.persistence.postgres import (
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.services.operator_execution_bridge import (
    OPERATOR_EXECUTION_CONSUMER,
    OPERATOR_EXECUTION_MESSAGE_TYPE,
    OPERATOR_EXECUTION_MESSAGE_VERSION,
    OPERATOR_EXECUTION_PRODUCER,
    OperatorExecutionCommandStore,
)


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_operator_bridge_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_operator_command_uses_owner_state_and_outbox_with_idempotent_submit_and_atomic_claim():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = OperatorExecutionCommandStore(uow.connection)
            first = store.submit(
                command_type="CLOSE_POSITION",
                requested_by="operator-1",
                authorization_source="managed_oidc",
                idempotency_key="idem-close-pos-1",
                target="pos-1",
                payload={"position_id": "pos-1", "close_reason": "MANUAL"},
            )
            replay = store.submit(
                command_type="CLOSE_POSITION",
                requested_by="operator-1",
                authorization_source="managed_oidc",
                idempotency_key="idem-close-pos-1",
                target="pos-1",
                payload={"position_id": "pos-1", "close_reason": "MANUAL"},
            )

            assert replay.command_id == first.command_id
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id=first.command_id)
            assert outbox is not None
            assert outbox.producer == OPERATOR_EXECUTION_PRODUCER
            assert outbox.consumer == OPERATOR_EXECUTION_CONSUMER
            assert outbox.message_type == OPERATOR_EXECUTION_MESSAGE_TYPE
            assert outbox.message_version == OPERATOR_EXECUTION_MESSAGE_VERSION

        with PostgresUnitOfWork(factory) as worker_one:
            claimed = DurableMessageStore(worker_one.connection).claim_outbox(
                consumer=OPERATOR_EXECUTION_CONSUMER,
                worker_id="worker-1",
                limit=1,
                lock_seconds=60,
            )
            assert [message.message_id for message in claimed] == [first.command_id]

        with PostgresUnitOfWork(factory) as worker_two:
            claimed = DurableMessageStore(worker_two.connection).claim_outbox(
                consumer=OPERATOR_EXECUTION_CONSUMER,
                worker_id="worker-2",
                limit=1,
                lock_seconds=60,
            )
            assert claimed == ()
    finally:
        _drop_schema(settings)
