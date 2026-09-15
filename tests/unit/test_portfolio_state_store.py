from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    PortfolioStateConflict,
    PortfolioStateStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.persistence.postgres import OwnerStateRevisionConflict
from triggertrade.portfolio_state import (
    CommitmentBuckets,
    PortfolioHealth,
    PortfolioState,
    initial_portfolio_state,
    mark_live,
    mark_reconciling,
    mark_stale,
)


pytest.importorskip("psycopg")

NOW = "2026-09-15T00:00:00Z"


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_pr001_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_portfolio_state_store_recovers_current_state_and_replays_identical_evidence():
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
        ]
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        initial = initial_portfolio_state(portfolio_id="portfolio-main", as_of=NOW)
        reconciling = mark_reconciling(
            state=initial,
            as_of="2026-09-15T00:01:00Z",
            evidence_id="order-event-1",
            reason_code="ORDER_EVENT_RECEIVED",
        )
        stale = mark_stale(
            state=reconciling,
            as_of="2026-09-15T00:02:00Z",
            evidence_id="portfolio-data-missing-1",
            reason_code="PORTFOLIO_FACTS_UNAVAILABLE",
        )

        with PostgresUnitOfWork(factory) as uow:
            store = PortfolioStateStore(uow.connection)
            recorded, inserted = store.record(state=reconciling, evidence_kind="ORDER_EVENT")
            assert inserted is True
            replayed, inserted = store.record(state=reconciling, evidence_kind="ORDER_EVENT")
            assert inserted is False
            assert replayed.payload_digest == recorded.payload_digest
            store.record(state=stale, evidence_kind="PORTFOLIO_DATA_REQUEST")

        with PostgresUnitOfWork(factory) as restarted:
            current = PortfolioStateStore(restarted.connection).get_current(portfolio_id="portfolio-main")

        assert current is not None
        assert current.state.health == PortfolioHealth.STALE
        assert current.state.reason_code == "PORTFOLIO_FACTS_UNAVAILABLE"
        assert current.state.revision == 3
    finally:
        _drop_schema(settings)


def test_portfolio_state_store_rejects_changed_evidence_and_stale_revision():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        initial = initial_portfolio_state(portfolio_id="portfolio-main", as_of=NOW)
        reconciling = mark_reconciling(
            state=initial,
            as_of="2026-09-15T00:01:00Z",
            evidence_id="order-event-1",
            reason_code="ORDER_EVENT_RECEIVED",
        )
        changed_same_evidence = PortfolioState(
            portfolio_id="portfolio-main",
            revision=2,
            health=PortfolioHealth.RECONCILING,
            as_of="2026-09-15T00:01:00Z",
            evidence_id="order-event-1",
            reason_code="ORDER_EVENT_RECEIVED",
            global_buckets=CommitmentBuckets(held_committed_capital="1"),
        )
        live_same_revision = mark_live(
            state=initial,
            as_of="2026-09-15T00:02:00Z",
            evidence_id="portfolio-data-confirmed-1",
        )

        with PostgresUnitOfWork(factory) as uow:
            store = PortfolioStateStore(uow.connection)
            store.record(state=reconciling, evidence_kind="ORDER_EVENT")
            with pytest.raises(PortfolioStateConflict):
                store.record(state=changed_same_evidence, evidence_kind="ORDER_EVENT")
            with pytest.raises(OwnerStateRevisionConflict):
                store.record(state=live_same_revision, evidence_kind="PORTFOLIO_DATA_REQUEST")
    finally:
        _drop_schema(settings)
