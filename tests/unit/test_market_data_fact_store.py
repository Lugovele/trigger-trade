from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import os
import uuid

import pytest

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text
from triggertrade.api_adapter_gateway import (
    build_market_data_response,
    coverage,
    dataset_payload,
    market_selection,
    market_selection_result,
)
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


def test_market_data_fact_store_last_traded_price_lookup_filters_fake_pages_without_postgres():
    older = _last_traded_price_response(page_id="ltp-page-old", selection_id="ltp-selection-old", as_of="2026-09-14T00:00:00Z", price="65000")
    latest = _last_traded_price_response(page_id="ltp-page-latest", selection_id="ltp-selection-latest", as_of="2026-09-14T00:10:00Z", price="65100")
    future = _last_traded_price_response(page_id="ltp-page-future", selection_id="ltp-selection-future", as_of="2026-09-14T00:20:00Z", price="65200")
    wrong_symbol = _last_traded_price_response(page_id="ltp-page-eth", selection_id="ltp-selection-eth", symbol="ETHUSDT", as_of="2026-09-14T00:10:00Z", price="2500")
    incomplete = _last_traded_price_response(
        page_id="ltp-page-incomplete",
        selection_id="ltp-selection-incomplete",
        as_of="2026-09-14T00:12:00Z",
        price="65120",
        coverage_complete=False,
    )
    connection = _FakeMarketDataConnection(
        (
            _row_from_last_traded_price_response(future),
            _row_from_last_traded_price_response(wrong_symbol),
            _row_from_last_traded_price_response(incomplete),
            _row_from_last_traded_price_response(older),
            _row_from_last_traded_price_response(latest),
        )
    )

    selected = MarketDataFactStore(connection).latest_last_traded_price_response_as_of(
        symbol="BTCUSDT",
        as_of=datetime(2026, 9, 14, 0, 15, tzinfo=UTC),
    )

    assert selected is not None
    result = selected["market_data_response"]["selection_results"][0]
    assert result["page_id"] == "ltp-page-latest"
    assert result["payload"]["LAST_TRADED_PRICE"]["data"]["price"] == "65100"
    assert connection.params == ("BTCUSDT", "LAST_TRADED_PRICE")


def test_market_data_fact_store_last_traded_price_lookup_returns_none_without_eligible_page():
    future = _last_traded_price_response(page_id="ltp-page-future-only", selection_id="ltp-selection-future-only", as_of="2026-09-14T00:20:00Z", price="65200")
    incomplete = _last_traded_price_response(
        page_id="ltp-page-incomplete-only",
        selection_id="ltp-selection-incomplete-only",
        as_of="2026-09-14T00:10:00Z",
        price="65100",
        coverage_complete=False,
    )
    connection = _FakeMarketDataConnection((_row_from_last_traded_price_response(future), _row_from_last_traded_price_response(incomplete)))

    assert (
        MarketDataFactStore(connection).latest_last_traded_price_response_as_of(
            symbol="BTCUSDT",
            as_of=datetime(2026, 9, 14, 0, 15, tzinfo=UTC),
        )
        is None
    )


def test_market_data_fact_store_last_traded_price_lookup_does_not_fallback_to_ticker():
    connection = _FakeMarketDataConnection((_row_from_last_traded_price_response(valid_market_response()),))

    assert (
        MarketDataFactStore(connection).latest_last_traded_price_response_as_of(
            symbol="BTCUSDT",
            as_of=datetime(2026, 9, 14, 0, 15, tzinfo=UTC),
        )
        is None
    )
    assert connection.params == ("BTCUSDT", "LAST_TRADED_PRICE")


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
            "0015",
            "0016",
            "0017",
            "0018",
            "0019",
            "0020",
            "0021",
            "0022",
            "0023",
            "0024",
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


def test_market_data_fact_store_selects_latest_eligible_last_traded_price_as_of():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        older = _last_traded_price_response(page_id="ltp-page-old", selection_id="ltp-selection-old", as_of="2026-09-14T00:00:00Z", price="65000")
        latest = _last_traded_price_response(page_id="ltp-page-latest", selection_id="ltp-selection-latest", as_of="2026-09-14T00:10:00Z", price="65100")
        future = _last_traded_price_response(page_id="ltp-page-future", selection_id="ltp-selection-future", as_of="2026-09-14T00:20:00Z", price="65200")

        with PostgresUnitOfWork(factory) as uow:
            store = MarketDataFactStore(uow.connection)
            store.put_response(future)
            store.put_response(older)
            store.put_response(latest)
            selected = store.latest_last_traded_price_response_as_of(
                symbol="BTCUSDT",
                as_of=datetime(2026, 9, 14, 0, 15, tzinfo=UTC),
            )

        assert selected is not None
        result = selected["market_data_response"]["selection_results"][0]
        assert result["page_id"] == "ltp-page-latest"
        assert result["payload"]["LAST_TRADED_PRICE"]["data"]["price"] == "65100"
    finally:
        _drop_schema(settings)


def test_market_data_fact_store_last_traded_price_lookup_rejects_ineligible_pages():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        incomplete = _last_traded_price_response(
            page_id="ltp-page-incomplete",
            selection_id="ltp-selection-incomplete",
            as_of="2026-09-14T00:00:00Z",
            price="65000",
            coverage_complete=False,
        )
        wrong_symbol = _last_traded_price_response(
            page_id="ltp-page-eth",
            selection_id="ltp-selection-eth",
            symbol="ETHUSDT",
            as_of="2026-09-14T00:00:00Z",
            price="2500",
        )

        with PostgresUnitOfWork(factory) as uow:
            store = MarketDataFactStore(uow.connection)
            store.put_response(incomplete)
            store.put_response(wrong_symbol)
            selected = store.latest_last_traded_price_response_as_of(
                symbol="BTCUSDT",
                as_of=datetime(2026, 9, 14, 0, 15, tzinfo=UTC),
            )

        assert selected is None
    finally:
        _drop_schema(settings)


def _last_traded_price_response(
    *,
    page_id: str,
    selection_id: str,
    as_of: str,
    price: str,
    symbol: str = "BTCUSDT",
    coverage_complete: bool = True,
    observed_at: str | None = None,
    instrument_symbol: str | None = None,
) -> dict[str, object]:
    physical_symbol = instrument_symbol or symbol
    selection = market_selection(selection_id=selection_id, dataset="LAST_TRADED_PRICE", mode="AS_OF", as_of=as_of, page_size=1)
    payload = dataset_payload(
        dataset="LAST_TRADED_PRICE",
        status="AVAILABLE",
        as_of=as_of,
        source_endpoint=f"bybit-public-trades:{physical_symbol}",
        data={
            "price": Decimal(price),
            "observed_at": observed_at or as_of,
            "source_record_id": f"trade-{page_id}",
            "venue": "BYBIT",
            "instrument_symbol": physical_symbol,
        },
    )
    result = market_selection_result(
        symbol=symbol,
        selection=selection,
        page_id=page_id,
        page_index=0,
        source_snapshot_id=f"ltp-snapshot-{page_id}",
        payload=payload,
        coverage=coverage(
            coverage_complete=coverage_complete,
            pagination_complete=True,
            next_cursor=None,
            expected_page_ids=(page_id,),
            source_finality_confirmed=coverage_complete,
            reason_code=None if coverage_complete else "INCOMPLETE_FIXTURE",
        ),
    )
    return build_market_data_response(
        request_id=f"ltp-request-{page_id}",
        response_id=f"ltp-response-{page_id}",
        symbol=symbol,
        snapshot_started_at=as_of,
        snapshot_completed_at=as_of,
        as_of=as_of,
        selection_results=(result,),
        expected_selections=(selection,),
    ).to_payload()


def _row_from_last_traded_price_response(response: dict[str, object]) -> tuple[object, ...]:
    body = response["market_data_response"]
    result = body["selection_results"][0]
    page_payload = {
        "market_data_response_page": {
            "contract_version": body["contract_version"],
            "request_id": body["request_id"],
            "response_id": body["response_id"],
            "symbol": body["symbol"],
            "snapshot_started_at": body["snapshot_started_at"],
            "snapshot_completed_at": body["snapshot_completed_at"],
            "as_of": body["as_of"],
            "source": body["source"],
            "selection_result": result,
        }
    }
    return (
        result["page_id"],
        body["request_id"],
        body["response_id"],
        body["symbol"],
        result["selection"]["selection_id"],
        result["selection_digest"],
        next(iter(result["payload"])),
        result["page_index"],
        result["source_snapshot_id"],
        canonical_json_text(page_payload),
        canonical_json_digest(page_payload),
    )


class _FakeMarketDataConnection:
    def __init__(self, rows):
        self.rows = tuple(rows)
        self.params = None

    def cursor(self):
        return _FakeMarketDataCursor(self)


class _FakeMarketDataCursor:
    def __init__(self, connection):
        self._connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params):
        self._connection.params = params

    def fetchall(self):
        symbol, dataset = self._connection.params
        return tuple(row for row in self._connection.rows if row[3] == symbol and row[6] == dataset)
