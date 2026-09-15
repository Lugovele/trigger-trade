from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    MarketDataFactConflict,
    MarketDataFactStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from tests.unit.test_market_data_gateway import valid_market_response


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_api001_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_market_data_fact_store_persists_replays_and_recovers_pages():
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
        ]
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        response = valid_market_response()
        with PostgresUnitOfWork(factory) as uow:
            store = MarketDataFactStore(uow.connection)
            records, inserted = store.put_response(response)
            assert inserted is True
            replayed, inserted = store.put_response(response)
            assert inserted is False
            assert replayed[0].payload_digest == records[0].payload_digest

        with PostgresUnitOfWork(factory) as restarted:
            store = MarketDataFactStore(restarted.connection)
            page = store.get_page(page_id="page-ticker-1")
            pages = store.list_selection_pages(selection_id="sel-ticker-1")
        assert page is not None
        assert page.dataset == "TICKER"
        assert page.selection_digest == records[0].selection_digest
        assert [item.page_id for item in pages] == ["page-ticker-1"]
    finally:
        _drop_schema(settings)


def test_market_data_fact_store_rejects_changed_page_identity():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        response = valid_market_response()
        changed = valid_market_response()
        changed["market_data_response"]["selection_results"][0]["payload"]["TICKER"]["data"]["last_price"] = "65000.2"

        with PostgresUnitOfWork(factory) as uow:
            store = MarketDataFactStore(uow.connection)
            store.put_response(response)
            with pytest.raises(MarketDataFactConflict):
                store.put_response(changed)
    finally:
        _drop_schema(settings)
