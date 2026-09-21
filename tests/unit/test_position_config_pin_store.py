from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    PositionConfigPinConflict,
    PositionConfigPinStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from tests.unit.test_position_config_pins import market_handoff, rules_version


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_pos002_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_position_config_pin_store_persists_replays_and_recovers_binding():
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
            store = PositionConfigPinStore(uow.connection)
            record, inserted = store.pin(
                position_decision_id="position-decision-1",
                market_handoff=market_handoff(),
                rules_version=rules_version(),
                pinned_at="2026-09-15T10:00:00Z",
            )
            replayed, replay_inserted = store.pin(
                position_decision_id="position-decision-1",
                market_handoff=market_handoff(),
                rules_version=rules_version(),
                pinned_at="2026-09-15T10:00:00Z",
            )

        with PostgresUnitOfWork(factory) as restarted:
            stored = PositionConfigPinStore(restarted.connection).get_by_decision_cycle_id(
                decision_cycle_id=record.pin.decision_cycle_id
            )

        assert inserted is True
        assert replay_inserted is False
        assert replayed.payload_digest == record.payload_digest
        assert stored is not None
        assert stored.pin.configuration_id == "rules-v1"
    finally:
        _drop_schema(settings)


def test_position_config_pin_store_rejects_changed_cycle_or_config():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = PositionConfigPinStore(uow.connection)
            store.pin(
                position_decision_id="position-decision-1",
                market_handoff=market_handoff(),
                rules_version=rules_version(),
                pinned_at="2026-09-15T10:00:00Z",
            )
            with pytest.raises(PositionConfigPinConflict):
                store.pin(
                    position_decision_id="position-decision-1",
                    market_handoff=market_handoff(),
                    rules_version=rules_version(version="v2", rules_version_id="rules-v2"),
                    pinned_at="2026-09-15T10:00:00Z",
                )
    finally:
        _drop_schema(settings)
