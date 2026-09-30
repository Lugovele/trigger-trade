from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import gzip
import io
import os
from pathlib import Path
import shutil
import uuid

import pytest

from triggertrade.contracts import parse_contract
from triggertrade.backtest.models import HistoricalCandle
from triggertrade.market_data import (
    BYBIT_PUBLIC_TRADE_ARCHIVE_SCHEMA,
    RAW_TRADES_UNAVAILABLE_ARCHIVE_COMPLETENESS_UNATTESTED,
    RAW_TRADES_UNAVAILABLE_ARCHIVE_MANIFEST_MISMATCH,
    RAW_TRADES_UNAVAILABLE_MISSING_ARCHIVE_DAY,
    RawTradesSourceError,
    build_bybit_archive_raw_trades_response,
    build_last_traded_price_response_from_raw_trades,
    build_raw_trades_response,
    bybit_public_trade_archive_url,
    bybit_raw_trade_archive_manifest,
    instrument_symbol_for_logical_symbol,
    normalize_bybit_public_trade_rows,
)
from triggertrade.research_v1_historical_triggers import (
    ResearchV1HistoricalTriggerInputUnavailable,
    metric_readiness,
    produce_research_v1_historical_metric,
)
from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType


START = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)
END = datetime(2026, 9, 1, 0, 5, tzinfo=UTC)
SCRATCH = Path(".phase9_raw_trade_test_files")


@pytest.fixture(autouse=True)
def _clean_scratch():
    shutil.rmtree(SCRATCH, ignore_errors=True)
    yield
    shutil.rmtree(SCRATCH, ignore_errors=True)


def test_bybit_archive_trade_normalization_preserves_taker_side_and_exact_quote_notional():
    records = normalize_bybit_public_trade_rows(
        (
            _archive_row("t-2", "2026-09-01T00:00:02Z", side="Sell", price="100.25", qty="2"),
            _archive_row("t-1", "2026-09-01T00:00:01Z", side="Buy", price="100", qty="1.5"),
        ),
        logical_symbol="BTCUSDT",
        source_endpoint=bybit_public_trade_archive_url("BTCUSDT", date(2026, 9, 1)),
    )

    assert [item.trade_id for item in records] == ["t-1", "t-2"]
    assert records[0].taker_side == "BUY"
    assert records[1].taker_side == "SELL"
    assert records[1].notional_quote == Decimal("200.50")
    assert records[1].contract_payload()["notional_quote"] == "200.5"


def test_bybit_archive_current_rpi_schema_and_fractional_epoch_timestamp_are_supported():
    records = normalize_bybit_public_trade_rows(
        (
            _archive_row(
                "official-rpi",
                "1786925699.2724",
                price="62884.20",
                qty="0.002",
                rpi="0",
            ),
        ),
        logical_symbol="BTCUSDT",
        source_endpoint=bybit_public_trade_archive_url("BTCUSDT", date(2026, 8, 17)),
    )

    assert records[0].executed_at.isoformat().replace("+00:00", "Z") == "2026-08-17T00:14:59.272400Z"
    assert records[0].price == Decimal("62884.20")
    assert records[0].source_row_number == 1


def test_duplicate_trade_ids_are_idempotent_but_conflicts_fail_closed():
    rows = (
        _archive_row("same", "2026-09-01T00:00:01Z", price="10", qty="2"),
        _archive_row("same", "2026-09-01T00:00:01Z", price="10", qty="2"),
    )
    assert len(normalize_bybit_public_trade_rows(rows, logical_symbol="BTCUSDT", source_endpoint="archive")) == 1

    with pytest.raises(RawTradesSourceError, match="conflicting duplicate"):
        normalize_bybit_public_trade_rows(
            rows + (_archive_row("same", "2026-09-01T00:00:01Z", price="10.1", qty="2"),),
            logical_symbol="BTCUSDT",
            source_endpoint="archive",
        )


def test_raw_trades_response_applies_exact_interval_boundaries_and_excludes_future():
    records = normalize_bybit_public_trade_rows(
        (
            _archive_row("left", "2026-09-01T00:00:00Z"),
            _archive_row("inside", "2026-09-01T00:04:59Z"),
            _archive_row("right", "2026-09-01T00:05:00Z"),
            _archive_row("future", "2026-09-01T00:06:00Z"),
        ),
        logical_symbol="BTCUSDT",
        source_endpoint="archive",
    )

    payload = build_raw_trades_response(
        logical_symbol="BTCUSDT",
        records=records,
        range_from=START,
        range_to=END,
        request_id="mdr-raw-1",
        response_id="mdr-raw-response-1",
        selection_id="sel-raw-1",
        source_snapshot_id="snapshot-raw-1",
        source_endpoint="archive",
    )

    parsed = parse_contract("MARKET_DATA_REQUEST", payload, definition="MARKET_DATA_REQUEST.response").to_payload()
    data = parsed["market_data_response"]["selection_results"][0]["payload"]["RAW_TRADES"]["data"]
    assert [item["trade_id"] for item in data] == ["left", "inside"]
    coverage = parsed["market_data_response"]["selection_results"][0]["coverage"]
    assert coverage["coverage_complete"] is True
    assert coverage["source_finality_confirmed"] is True


def test_last_traded_price_response_selects_latest_factual_trade_at_or_before_cutoff():
    records = normalize_bybit_public_trade_rows(
        (
            _archive_row("older", "2026-09-01T00:00:01Z", price="100"),
            _archive_row("chosen", "2026-09-01T00:04:59Z", price="101"),
            _archive_row("future", "2026-09-01T00:05:01Z", price="102"),
        ),
        logical_symbol="BTCUSDT",
        source_endpoint="archive",
    )

    result = build_last_traded_price_response_from_raw_trades(
        logical_symbol="BTCUSDT",
        records=records,
        as_of=END,
        request_id="mdr-ltp-1",
        response_id="mdr-ltp-response-1",
        selection_id="sel-ltp-1",
        source_snapshot_id="snapshot-ltp-1",
        source_endpoint="archive#manifest_digest=abc;logical=BTCUSDT;instrument=BTCUSDT",
    )
    payload = parse_contract("MARKET_DATA_REQUEST", result.response_payload, definition="MARKET_DATA_REQUEST.response").to_payload()
    page = payload["market_data_response"]["selection_results"][0]
    data = page["payload"]["LAST_TRADED_PRICE"]["data"]

    assert result.available is True
    assert result.selected_record is not None
    assert result.selected_record.trade_id == "chosen"
    assert data == {
        "price": "101",
        "observed_at": "2026-09-01T00:04:59Z",
        "source_record_id": "chosen",
        "venue": "BYBIT",
        "instrument_symbol": "BTCUSDT",
    }
    assert page["selection"]["dataset"] == "LAST_TRADED_PRICE"
    assert page["selection"]["mode"] == "AS_OF"
    assert page["coverage"]["coverage_complete"] is True


def test_last_traded_price_equal_timestamp_selection_is_deterministic():
    rows = (
        _archive_row("b", "2026-09-01T00:04:59Z", price="102"),
        _archive_row("a", "2026-09-01T00:04:59Z", price="101"),
    )
    first = normalize_bybit_public_trade_rows(rows, logical_symbol="BTCUSDT", source_endpoint="archive")
    second = normalize_bybit_public_trade_rows(tuple(reversed(rows)), logical_symbol="BTCUSDT", source_endpoint="archive")

    first_result = build_last_traded_price_response_from_raw_trades(
        logical_symbol="BTCUSDT",
        records=first,
        as_of=END,
        request_id="mdr-ltp-equal-1",
        response_id="mdr-ltp-equal-response-1",
        selection_id="sel-ltp-equal-1",
        source_snapshot_id="snapshot-ltp-equal-1",
        source_endpoint="archive",
    )
    second_result = build_last_traded_price_response_from_raw_trades(
        logical_symbol="BTCUSDT",
        records=second,
        as_of=END,
        request_id="mdr-ltp-equal-1",
        response_id="mdr-ltp-equal-response-1",
        selection_id="sel-ltp-equal-1",
        source_snapshot_id="snapshot-ltp-equal-1",
        source_endpoint="archive",
    )

    assert first_result.selected_record is not None
    assert first_result.selected_record.trade_id == "b"
    assert first_result.response_payload == second_result.response_payload


def test_last_traded_price_unavailable_when_no_eligible_trade_exists():
    records = normalize_bybit_public_trade_rows(
        (_archive_row("future", "2026-09-01T00:05:01Z", price="102"),),
        logical_symbol="BTCUSDT",
        source_endpoint="archive",
    )

    result = build_last_traded_price_response_from_raw_trades(
        logical_symbol="BTCUSDT",
        records=records,
        as_of=END,
        request_id="mdr-ltp-missing-1",
        response_id="mdr-ltp-missing-response-1",
        selection_id="sel-ltp-missing-1",
        source_snapshot_id="snapshot-ltp-missing-1",
        source_endpoint="archive",
    )
    payload = parse_contract("MARKET_DATA_REQUEST", result.response_payload, definition="MARKET_DATA_REQUEST.response").to_payload()
    page = payload["market_data_response"]["selection_results"][0]

    assert result.available is False
    assert result.selected_record is None
    assert page["payload"]["LAST_TRADED_PRICE"]["status"] == "UNAVAILABLE"
    assert page["payload"]["LAST_TRADED_PRICE"]["data"] is None
    assert page["coverage"]["coverage_complete"] is False
    assert page["coverage"]["source_finality_confirmed"] is False


def test_last_traded_price_preserves_pepe_logical_and_physical_binding():
    records = normalize_bybit_public_trade_rows(
        (_archive_row("pepe-1", "2026-09-01T00:04:59Z", symbol="1000PEPEUSDT", price="0.0123"),),
        logical_symbol="PEPEUSDT",
        source_endpoint="archive",
    )

    result = build_last_traded_price_response_from_raw_trades(
        logical_symbol="PEPEUSDT",
        records=records,
        as_of=END,
        request_id="mdr-ltp-pepe-1",
        response_id="mdr-ltp-pepe-response-1",
        selection_id="sel-ltp-pepe-1",
        source_snapshot_id="snapshot-ltp-pepe-1",
        source_endpoint="archive#logical=PEPEUSDT;instrument=1000PEPEUSDT",
    )
    payload = parse_contract("MARKET_DATA_REQUEST", result.response_payload, definition="MARKET_DATA_REQUEST.response").to_payload()
    body = payload["market_data_response"]
    data = body["selection_results"][0]["payload"]["LAST_TRADED_PRICE"]["data"]

    assert body["symbol"] == "PEPEUSDT"
    assert data["instrument_symbol"] == "1000PEPEUSDT"


def test_reversed_source_order_produces_same_normalized_order_and_page_identity():
    rows = (
        _archive_row("b", "2026-09-01T00:00:02Z", price="12"),
        _archive_row("a", "2026-09-01T00:00:01Z", price="11"),
    )
    first = normalize_bybit_public_trade_rows(rows, logical_symbol="BTCUSDT", source_endpoint="archive")
    second = normalize_bybit_public_trade_rows(tuple(reversed(rows)), logical_symbol="BTCUSDT", source_endpoint="archive")

    assert [item.trade_id for item in first] == ["a", "b"]
    assert [item.trade_id for item in second] == ["a", "b"]
    assert _raw_page(first)["page_id"] == _raw_page(second)["page_id"]


def test_changed_trade_fact_or_source_revision_changes_page_identity():
    first = normalize_bybit_public_trade_rows(
        (_archive_row("a", "2026-09-01T00:00:01Z", price="11"),),
        logical_symbol="BTCUSDT",
        source_endpoint="archive",
        source_revision="rev-a",
    )
    same_trade_different_revision = normalize_bybit_public_trade_rows(
        (_archive_row("a", "2026-09-01T00:00:01Z", price="11"),),
        logical_symbol="BTCUSDT",
        source_endpoint="archive",
        source_revision="rev-b",
    )
    changed_trade = normalize_bybit_public_trade_rows(
        (_archive_row("a", "2026-09-01T00:00:01Z", price="11.1"),),
        logical_symbol="BTCUSDT",
        source_endpoint="archive",
        source_revision="rev-a",
    )

    assert _raw_page(first)["page_id"] != _raw_page(same_trade_different_revision)["page_id"]
    assert _raw_page(first)["page_id"] != _raw_page(changed_trade)["page_id"]


def test_missing_required_archive_day_remains_unavailable():
    manifest = _manifest(
        rows=(_archive_row("late", "2026-09-01T23:59:30Z"),),
        archive_date=date(2026, 9, 1),
    )
    result = build_bybit_archive_raw_trades_response(
        logical_symbol="BTCUSDT",
        range_from=datetime(2026, 9, 1, 23, 59, tzinfo=UTC),
        range_to=datetime(2026, 9, 2, 0, 1, tzinfo=UTC),
        archive_manifests_by_date={date(2026, 9, 1): manifest},
        request_id="mdr-raw-missing",
        response_id="mdr-raw-response-missing",
        selection_id="sel-raw-missing",
        source_snapshot_id="snapshot-raw-missing",
    )

    raw = result.response_payload["market_data_response"]["selection_results"][0]
    assert result.complete is False
    assert result.missing_dates == (date(2026, 9, 2),)
    assert raw["payload"]["RAW_TRADES"]["status"] == "UNAVAILABLE"
    assert raw["coverage"]["reason_code"] == RAW_TRADES_UNAVAILABLE_MISSING_ARCHIVE_DAY
    assert raw["coverage"]["source_finality_confirmed"] is False


def test_wrong_date_manifest_cannot_prove_requested_date_complete():
    manifest = _manifest(rows=(_archive_row("x", "2026-09-02T00:00:01Z"),), archive_date=date(2026, 9, 2))
    result = build_bybit_archive_raw_trades_response(
        logical_symbol="BTCUSDT",
        range_from=START,
        range_to=END,
        archive_manifests_by_date={date(2026, 9, 1): manifest},
        request_id="mdr-raw-wrong-date",
        response_id="mdr-raw-response-wrong-date",
        selection_id="sel-raw-wrong-date",
        source_snapshot_id="snapshot-raw-wrong-date",
    )

    raw = result.response_payload["market_data_response"]["selection_results"][0]
    assert result.complete is False
    assert raw["coverage"]["reason_code"] == RAW_TRADES_UNAVAILABLE_ARCHIVE_MANIFEST_MISMATCH


def test_wrong_instrument_archive_rejected():
    with pytest.raises(RawTradesSourceError, match="symbol does not match"):
        _manifest(rows=(_archive_row("x", "2026-09-01T00:00:01Z", symbol="ETHUSDT"),), archive_date=date(2026, 9, 1))


def test_malformed_or_empty_archive_cannot_be_marked_final():
    SCRATCH.mkdir(exist_ok=True)
    bad = SCRATCH / "BTCUSDT2026-09-01.csv.gz"
    empty = SCRATCH / "BTCUSDT2026-09-01-empty.csv.gz"
    try:
        bad.write_bytes(b"not-a-gzip")
        with pytest.raises(Exception):
            bybit_raw_trade_archive_manifest(
                bad,
                logical_symbol="BTCUSDT",
                archive_date=date(2026, 9, 1),
                factual_validation_status="OPERATOR_ATTESTED_COMPLETE",
            )
        _write_archive(empty, ())
        with pytest.raises(RawTradesSourceError, match="contains no trade rows"):
            bybit_raw_trade_archive_manifest(
                empty,
                logical_symbol="BTCUSDT",
                archive_date=date(2026, 9, 1),
                factual_validation_status="OPERATOR_ATTESTED_COMPLETE",
            )
    finally:
        bad.unlink(missing_ok=True)
        empty.unlink(missing_ok=True)
        _try_rmdir(SCRATCH)


def test_unattested_archive_manifest_does_not_claim_final_coverage():
    manifest = _manifest(
        rows=(_archive_row("x", "2026-09-01T00:00:01Z"),),
        archive_date=date(2026, 9, 1),
        factual_validation_status="LOCAL_FILE_ONLY",
    )
    result = build_bybit_archive_raw_trades_response(
        logical_symbol="BTCUSDT",
        range_from=START,
        range_to=END,
        archive_manifests_by_date={date(2026, 9, 1): manifest},
        request_id="mdr-raw-unattested",
        response_id="mdr-raw-response-unattested",
        selection_id="sel-raw-unattested",
        source_snapshot_id="snapshot-raw-unattested",
    )

    raw = result.response_payload["market_data_response"]["selection_results"][0]
    assert result.complete is False
    assert raw["coverage"]["reason_code"] == RAW_TRADES_UNAVAILABLE_ARCHIVE_COMPLETENESS_UNATTESTED
    assert raw["coverage"]["source_finality_confirmed"] is False


def test_archive_content_hash_and_manifest_digest_are_deterministic_and_sensitive():
    first = _manifest(rows=(_archive_row("x", "2026-09-01T00:00:01Z"),), archive_date=date(2026, 9, 1))
    rebuilt = _manifest(rows=(_archive_row("x", "2026-09-01T00:00:01Z"),), archive_date=date(2026, 9, 1))
    changed = _manifest(rows=(_archive_row("x", "2026-09-01T00:00:01Z", price="10.1"),), archive_date=date(2026, 9, 1))

    assert first.content_sha256 == rebuilt.content_sha256
    assert first.manifest_digest == rebuilt.manifest_digest
    assert first.content_sha256 != changed.content_sha256
    assert first.manifest_digest != changed.manifest_digest


def test_archive_manifest_finality_and_provenance_survive_response_parse_for_pepe():
    manifest = _manifest(
        rows=(_archive_row("pepe-1", "2026-09-01T00:00:01Z", symbol="1000PEPEUSDT", price="0.01234", qty="1000"),),
        archive_date=date(2026, 9, 1),
        logical_symbol="PEPEUSDT",
    )
    result = build_bybit_archive_raw_trades_response(
        logical_symbol="PEPEUSDT",
        range_from=START,
        range_to=END,
        archive_manifests_by_date={date(2026, 9, 1): manifest},
        request_id="mdr-raw-pepe",
        response_id="mdr-raw-response-pepe",
        selection_id="sel-raw-pepe",
        source_snapshot_id="ignored-by-archive-builder",
    )
    parsed = parse_contract("MARKET_DATA_REQUEST", result.response_payload, definition="MARKET_DATA_REQUEST.response").to_payload()
    body = parsed["market_data_response"]
    page = body["selection_results"][0]

    assert result.complete is True
    assert body["symbol"] == "PEPEUSDT"
    assert page["source_snapshot_id"].startswith("raw-trades-archive-")
    assert "instrument=1000PEPEUSDT" in page["payload"]["RAW_TRADES"]["source_endpoint"]
    assert "logical=PEPEUSDT" in page["payload"]["RAW_TRADES"]["source_endpoint"]
    assert f"manifest_digest={manifest.manifest_digest}" in result.records[0].source_endpoint
    assert page["coverage"]["coverage_complete"] is True
    assert page["coverage"]["source_finality_confirmed"] is True
    assert page["selection"]["range_from"] == "2026-09-01T00:00:00Z"
    assert page["selection"]["range_to"] == "2026-09-01T00:05:00Z"
    assert page["payload"]["RAW_TRADES"]["data"][0]["trade_id"] == "pepe-1"


def test_market_data_fact_store_readback_preserves_raw_trade_finality_and_provenance():
    pytest.importorskip("psycopg")
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    from triggertrade.persistence import (
        MarketDataFactStore,
        PostgresConnectionFactory,
        PostgresSettings,
        PostgresUnitOfWork,
        apply_postgres_migrations,
    )

    settings = PostgresSettings(dsn=dsn, schema=f"tt_raw_trades_{uuid.uuid4().hex[:16]}")
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        manifest = _manifest(
            rows=(_archive_row("pepe-1", "2026-09-01T00:00:01Z", symbol="1000PEPEUSDT"),),
            archive_date=date(2026, 9, 1),
            logical_symbol="PEPEUSDT",
        )
        result = build_bybit_archive_raw_trades_response(
            logical_symbol="PEPEUSDT",
            range_from=START,
            range_to=END,
            archive_manifests_by_date={date(2026, 9, 1): manifest},
            request_id="mdr-raw-store",
            response_id="mdr-raw-response-store",
            selection_id="sel-raw-store",
            source_snapshot_id="ignored-by-archive-builder",
        )
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            store = MarketDataFactStore(uow.connection)
            records, inserted = store.put_response(result.response_payload)
            assert inserted is True
            page_id = records[0].page_id
        with PostgresUnitOfWork(factory) as uow:
            page = MarketDataFactStore(uow.connection).get_page(page_id=page_id)
        assert page is not None
        selection_result = page.payload["market_data_response_page"]["selection_result"]
        assert page.symbol == "PEPEUSDT"
        assert page.dataset == "RAW_TRADES"
        assert selection_result["coverage"]["coverage_complete"] is True
        assert selection_result["coverage"]["source_finality_confirmed"] is True
        assert selection_result["source_snapshot_id"].startswith("raw-trades-archive-")
        assert "logical=PEPEUSDT" in selection_result["payload"]["RAW_TRADES"]["source_endpoint"]
        assert "instrument=1000PEPEUSDT" in selection_result["payload"]["RAW_TRADES"]["source_endpoint"]
    finally:
        _drop_schema(settings)


def test_pepe_archive_rejects_wrong_factual_symbol():
    with pytest.raises(RawTradesSourceError, match="symbol does not match"):
        normalize_bybit_public_trade_rows(
            (_archive_row("pepe-1", "2026-09-01T00:00:01Z", symbol="PEPEUSDT"),),
            logical_symbol="PEPEUSDT",
            source_endpoint="archive",
        )


def test_raw_trade_normalization_rejects_ohlcv_proxy_and_candle_direction_fields():
    with pytest.raises(RawTradesSourceError, match="archive row does not match"):
        normalize_bybit_public_trade_rows(
            (
                {
                    "symbol": "BTCUSDT",
                    "open": "10",
                    "high": "11",
                    "low": "9",
                    "close": "11",
                    "volume": "100",
                },
            ),
            logical_symbol="BTCUSDT",
            source_endpoint="ohlcv-is-not-raw-trades",
        )


def test_aggressive_volume_delta_metric_is_ready_but_unavailable_without_raw_trades():
    rule = RuleDefinition(
        rule_id="TR-R-AGG-TEST",
        version="1.0.0",
        name="Aggressive flow test",
        status=RuleStatus.DRAFT,
        asset_scope="ALL",
        rule_type=RuleType.TRIGGER,
        condition="AGGRESSIVE_VOLUME_DELTA_PCT >= 10",
        definition={
            "metric_ref": "AGGRESSIVE_VOLUME_DELTA_PCT",
            "operator": ">=",
            "threshold": "10",
        },
        created_at="2026-09-01T00:00:00Z",
        provenance="unit-test",
    )

    candles = tuple(
        HistoricalCandle(
            symbol="BTCUSDT",
            category="linear",
            timeframe="1m",
            open_time=START + timedelta(minutes=index),
            close_time=START + timedelta(minutes=index + 1),
            open=Decimal("10"),
            high=Decimal("10"),
            low=Decimal("10"),
            close=Decimal("10"),
            volume=Decimal("1"),
            turnover=Decimal("10"),
            completed=True,
        )
        for index in range(5)
    )

    assert metric_readiness("AGGRESSIVE_VOLUME_DELTA_PCT") == "HISTORICAL_READY"
    observation = produce_research_v1_historical_metric(
        metric_ref="AGGRESSIVE_VOLUME_DELTA_PCT",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )
    assert observation.status == "UNAVAILABLE"
    assert observation.reason_code == "research_v1_historical_aggressive_volume_delta_unavailable:MISSING_RAW_TRADES"


def _archive_row(
    trade_id: str,
    timestamp: str,
    *,
    side: str = "Buy",
    price: str = "10",
    qty: str = "1",
    symbol: str = "BTCUSDT",
    rpi: str | None = None,
) -> dict[str, str]:
    row = {
        "timestamp": timestamp,
        "symbol": symbol,
        "side": side,
        "size": qty,
        "price": price,
        "tickDirection": "PlusTick",
        "trdMatchID": trade_id,
        "grossValue": str(Decimal(price) * Decimal(qty)),
        "homeNotional": qty,
        "foreignNotional": str(Decimal(price) * Decimal(qty)),
    }
    if rpi is not None:
        row["RPI"] = rpi
    return row


def _raw_page(records):
    return build_raw_trades_response(
        logical_symbol="BTCUSDT",
        records=records,
        range_from=START,
        range_to=END,
        request_id="mdr-raw-deterministic",
        response_id="mdr-raw-response-deterministic",
        selection_id="sel-raw-deterministic",
        source_snapshot_id="snapshot-raw-deterministic",
        source_endpoint="archive",
    )["market_data_response"]["selection_results"][0]


def _manifest(
    *,
    rows,
    archive_date: date,
    logical_symbol: str = "BTCUSDT",
    factual_validation_status: str = "OPERATOR_ATTESTED_COMPLETE",
):
    SCRATCH.mkdir(exist_ok=True)
    instrument = instrument_symbol_for_logical_symbol(logical_symbol)
    path = SCRATCH / f"{instrument}{archive_date.isoformat()}-{abs(hash(tuple(tuple(row.items()) for row in rows)))}.csv.gz"
    _write_archive(path, rows)
    return bybit_raw_trade_archive_manifest(
        path,
        logical_symbol=logical_symbol,
        archive_date=archive_date,
        factual_validation_status=factual_validation_status,
        remote_etag='"unit-test-etag"',
        remote_last_modified="Tue, 01 Sep 2026 01:00:00 GMT",
        remote_byte_size=path.stat().st_size,
    )


def _write_archive(path: Path, rows) -> None:
    lines = [",".join(BYBIT_PUBLIC_TRADE_ARCHIVE_SCHEMA)]
    for row in rows:
        lines.append(",".join(str(row[column]) for column in BYBIT_PUBLIC_TRADE_ARCHIVE_SCHEMA))
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
            wrapper = io.TextIOWrapper(gz, encoding="utf-8", newline="")
            wrapper.write(payload.decode("utf-8"))
            wrapper.flush()
            wrapper.detach()


def _try_rmdir(path: Path) -> None:
    try:
        path.rmdir()
    except OSError:
        pass


def _drop_schema(settings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')
