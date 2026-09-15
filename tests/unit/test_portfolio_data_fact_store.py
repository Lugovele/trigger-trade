from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.api_adapter_gateway import (
    build_portfolio_data_request,
    build_portfolio_data_response,
    instrument_metadata_item,
)
from triggertrade.persistence.portfolio_data_facts import PortfolioDataFactConflict, PortfolioDataFactStore
from triggertrade.persistence.postgres import (
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from tests.unit.test_portfolio_data_gateway import NOW, _instrument_facts


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_pdr_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_portfolio_data_facts_persist_replay_and_fail_on_conflict():
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
        assert apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema) == ()
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        request = build_portfolio_data_request(
            request_id="pdr-store-1",
            requested_at=NOW,
            scope={"instrument_metadata": True},
            symbols=("BTCUSDT",),
        ).to_payload()
        response = _response("pdr-store-1", "pdr-response-1")

        with PostgresUnitOfWork(factory) as uow:
            store = PortfolioDataFactStore(uow.connection)
            request_record, inserted = store.record_request(request)
            assert inserted is True
            response_record, inserted = store.record_response(response)
            assert inserted is True

        with PostgresUnitOfWork(factory) as restarted:
            store = PortfolioDataFactStore(restarted.connection)
            replayed_request, inserted = store.record_request(request)
            assert inserted is False
            assert replayed_request.payload_digest == request_record.payload_digest
            replayed_response, inserted = store.record_response(response)
            assert inserted is False
            assert replayed_response.payload_digest == response_record.payload_digest

            changed = build_portfolio_data_request(
                request_id="pdr-store-1",
                requested_at=NOW,
                scope={"fee_rates": True},
                symbols=("BTCUSDT",),
            ).to_payload()
            with pytest.raises(PortfolioDataFactConflict):
                store.record_request(changed)
    finally:
        _drop_schema(settings)


def test_portfolio_data_response_requires_existing_request():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with pytest.raises(Exception, match="foreign key"):
            with PostgresUnitOfWork(factory) as uow:
                PortfolioDataFactStore(uow.connection).record_response(_response("missing-request", "pdr-response-1"))
    finally:
        _drop_schema(settings)


def _response(request_id: str, response_id: str) -> dict[str, object]:
    return build_portfolio_data_response(
        request_id=request_id,
        response_id=response_id,
        request_mode="SNAPSHOT",
        snapshot_started_at=NOW,
        snapshot_completed_at=NOW,
        as_of=NOW,
        instrument_metadata={
            "status": "AVAILABLE",
            "items": [
                instrument_metadata_item(
                    symbol="BTCUSDT",
                    status="AVAILABLE",
                    facts=_instrument_facts("BTCUSDT", NOW),
                    as_of=NOW,
                    source_endpoint="/v5/market/instruments-info",
                    source_record_id="linear:BTCUSDT",
                    reason_code=None,
                )
            ],
        },
        requested_symbols=("BTCUSDT",),
    ).to_payload()
