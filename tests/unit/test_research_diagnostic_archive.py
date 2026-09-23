from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from shutil import rmtree
import uuid

import pytest

from triggertrade.backtest.data import BybitHistoricalDataSource, HistoricalDataError, validate_historical_candles
from triggertrade.backtest.models import HistoricalCandle
from triggertrade.analytics import ENTRY_REPORT_ITEMS, TAKE_PROFIT_REPORT_ITEMS
from triggertrade.persistence import ResearchStore, ResearchStoreError


START = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
END = START + timedelta(minutes=1)


def test_research_diagnostic_archive_is_immutable_replayable_and_lineage_pinned():
    with _research_store() as (root, store):
        payload = {"candles": [_candle_row("BTCUSDT")], "note": "diagnostic source only"}
        provenance = {
            "source_kind": "SUPPLIED_DIAGNOSTIC_DATASET",
            "retrieved_at": START.isoformat().replace("+00:00", "Z"),
            "source_ref": "unit://diagnostic/BTCUSDT/1m",
        }
        manifest = {
            "dataset_kind": "OHLCV_CANDLES",
            "symbols": ["BTCUSDT"],
            "timeframe": "1m",
            "period_start": START.isoformat().replace("+00:00", "Z"),
            "period_end": END.isoformat().replace("+00:00", "Z"),
            "intrabar_first_touch_ordering": "UNAVAILABLE",
        }

        record, inserted = store.archive_diagnostic_dataset(
            dataset_id="diag-BTCUSDT-1m-1",
            source_payload=payload,
            source_provenance=provenance,
            manifest=manifest,
            created_at=START.isoformat().replace("+00:00", "Z"),
        )
        replayed, replay_inserted = store.archive_diagnostic_dataset(
            dataset_id="diag-BTCUSDT-1m-1",
            source_payload=payload,
            source_provenance=provenance,
            manifest=manifest,
            created_at=START.isoformat().replace("+00:00", "Z"),
        )

        assert inserted is True
        assert replay_inserted is False
        assert replayed.content_digest == record.content_digest
        assert record.manifest["intrabar_first_touch_ordering"] == "UNAVAILABLE"
        assert (root / "research-diagnostic-objects" / f"{record.content_digest}.json").exists()
        assert store.get_diagnostic_dataset("diag-BTCUSDT-1m-1") == record
        assert store.list_diagnostic_datasets() == (record,)


def test_research_diagnostic_archive_rejects_conflicting_identity_and_manifest_without_source_object():
    with _research_store() as (_root, store):
        store.archive_diagnostic_dataset(
            dataset_id="diag-BTCUSDT-1m-1",
            source_payload={"candles": [_candle_row("BTCUSDT")]},
            source_provenance=_provenance(),
            manifest=_manifest("BTCUSDT"),
        )
        with pytest.raises(ResearchStoreError, match="different content"):
            store.archive_diagnostic_dataset(
                dataset_id="diag-BTCUSDT-1m-1",
                source_payload={"candles": [_candle_row("BTCUSDT", close="101")]},
                source_provenance=_provenance(),
                manifest=_manifest("BTCUSDT"),
            )

        with pytest.raises(ResearchStoreError, match="after source object write"):
            store.archive_diagnostic_dataset(
                dataset_id="diag-ETHUSDT-1m-1",
                source_payload={"candles": [_candle_row("ETHUSDT")]},
                source_provenance=_provenance(source_ref="unit://diagnostic/ETHUSDT/1m"),
                manifest=_manifest("ETHUSDT"),
                _fault_after_object=True,
            )
        assert store.get_diagnostic_dataset("diag-ETHUSDT-1m-1") is None


def test_research_diagnostic_archive_accepts_provenance_complete_non_btc_dataset_without_downloader_claim():
    with _research_store() as (_root, store):
        record, _ = store.archive_diagnostic_dataset(
            dataset_id="diag-ETHUSDT-1m-1",
            source_payload={"candles": [_candle_row("ETHUSDT")]},
            source_provenance=_provenance(source_ref="unit://diagnostic/ETHUSDT/1m"),
            manifest=_manifest("ETHUSDT"),
        )

    assert record.manifest["symbols"] == ["ETHUSDT"]
    assert record.source_provenance["source_kind"] == "SUPPLIED_DIAGNOSTIC_DATASET"


def test_research_diagnostic_report_is_immutable_pinned_and_read_only():
    with _research_store() as (_root, store):
        dataset, _ = store.archive_diagnostic_dataset(
            dataset_id="diag-BTCUSDT-1m-1",
            source_payload={"candles": [_candle_row("BTCUSDT")]},
            source_provenance=_provenance(),
            manifest=_manifest("BTCUSDT"),
        )
        definition = _report_definition("ENTRY_REPORT", dataset.dataset_id)
        payload = _report_payload("ENTRY_REPORT", dataset)

        report, inserted = store.archive_diagnostic_report(
            report_id="entry-report-b12-1",
            report_kind="ENTRY_REPORT",
            dataset_id=dataset.dataset_id,
            report_definition=definition,
            report_payload=payload,
            created_at=START.isoformat().replace("+00:00", "Z"),
        )
        replayed, replay_inserted = store.archive_diagnostic_report(
            report_id="entry-report-b12-1",
            report_kind="ENTRY_REPORT",
            dataset_id=dataset.dataset_id,
            report_definition=definition,
            report_payload=payload,
            created_at=START.isoformat().replace("+00:00", "Z"),
        )

        assert inserted is True
        assert replay_inserted is False
        assert replayed == report
        assert report.dataset_manifest_digest == dataset.manifest_digest
        assert report.report_definition["methodology_revision"] == "v1.2.15"
        assert report.report_payload["canonical_feedback"] is False
        assert store.get_diagnostic_report("entry-report-b12-1") == report
        assert store.list_diagnostic_reports() == (report,)


def test_research_diagnostic_report_rejects_conflict_missing_dataset_and_feedback():
    with _research_store() as (_root, store):
        dataset, _ = store.archive_diagnostic_dataset(
            dataset_id="diag-BTCUSDT-1m-1",
            source_payload={"candles": [_candle_row("BTCUSDT")]},
            source_provenance=_provenance(),
            manifest=_manifest("BTCUSDT"),
        )
        definition = _report_definition("TAKE_PROFIT_REPORT", dataset.dataset_id)
        payload = _report_payload("TAKE_PROFIT_REPORT", dataset)
        store.archive_diagnostic_report(
            report_id="tp-report-b12-1",
            report_kind="TAKE_PROFIT_REPORT",
            dataset_id=dataset.dataset_id,
            report_definition=definition,
            report_payload=payload,
        )

        with pytest.raises(ResearchStoreError, match="different content"):
            store.archive_diagnostic_report(
                report_id="tp-report-b12-1",
                report_kind="TAKE_PROFIT_REPORT",
                dataset_id=dataset.dataset_id,
                report_definition=definition,
                report_payload={**payload, "availability": {**payload["availability"], "TP-RPT-01": "UNAVAILABLE"}},
            )
        with pytest.raises(ResearchStoreError, match="archived dataset"):
            store.archive_diagnostic_report(
                report_id="entry-report-missing-dataset",
                report_kind="ENTRY_REPORT",
                dataset_id="missing-dataset",
                report_definition=_report_definition("ENTRY_REPORT", "missing-dataset"),
                report_payload={**_report_payload("ENTRY_REPORT", dataset), "source_dataset_id": "missing-dataset"},
            )
        with pytest.raises(ResearchStoreError, match="canonical_feedback false"):
            store.archive_diagnostic_report(
                report_id="entry-report-feedback",
                report_kind="ENTRY_REPORT",
                dataset_id=dataset.dataset_id,
                report_definition=_report_definition("ENTRY_REPORT", dataset.dataset_id),
                report_payload={**_report_payload("ENTRY_REPORT", dataset), "canonical_feedback": True},
            )
        with pytest.raises(ResearchStoreError, match="pin methodology v1.2.15"):
            store.archive_diagnostic_report(
                report_id="entry-report-stale-methodology",
                report_kind="ENTRY_REPORT",
                dataset_id=dataset.dataset_id,
                report_definition={**_report_definition("ENTRY_REPORT", dataset.dataset_id), "methodology_revision": "v1.2.14"},
                report_payload=_report_payload("ENTRY_REPORT", dataset),
            )
        with pytest.raises(ResearchStoreError, match="definition kind"):
            store.archive_diagnostic_report(
                report_id="entry-report-wrong-kind",
                report_kind="ENTRY_REPORT",
                dataset_id=dataset.dataset_id,
                report_definition=_report_definition("TAKE_PROFIT_REPORT", dataset.dataset_id),
                report_payload=_report_payload("ENTRY_REPORT", dataset),
            )
        with pytest.raises(ResearchStoreError, match="source dataset"):
            store.archive_diagnostic_report(
                report_id="entry-report-wrong-dataset",
                report_kind="ENTRY_REPORT",
                dataset_id=dataset.dataset_id,
                report_definition=_report_definition("ENTRY_REPORT", "other-dataset"),
                report_payload=_report_payload("ENTRY_REPORT", dataset),
            )


def test_current_historical_downloader_remains_limited_to_bybit_linear_btcusdt_1m():
    source = BybitHistoricalDataSource(_NoNetworkClient(), retry_sleep_seconds=0, cache=None)

    with pytest.raises(HistoricalDataError, match="BTCUSDT only"):
        source.load(symbol="ETHUSDT", category="linear", timeframe="1m", start=START, end=END, use_cache=False)
    with pytest.raises(HistoricalDataError, match="1m historical timeframe"):
        source.load(symbol="BTCUSDT", category="linear", timeframe="5m", start=START, end=END, use_cache=False)
    with pytest.raises(HistoricalDataError, match="linear perpetual only"):
        source.load(symbol="BTCUSDT", category="spot", timeframe="1m", start=START, end=END, use_cache=False)


def test_ohlc_validation_does_not_claim_intrabar_first_touch_ordering():
    candle = HistoricalCandle(
        symbol="BTCUSDT",
        category="linear",
        timeframe="1m",
        open_time=START,
        close_time=END,
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("90"),
        close=Decimal("105"),
        volume=Decimal("1"),
        turnover=Decimal("100"),
        completed=True,
    )

    validated = validate_historical_candles((candle,), start=START, end=END)

    assert validated == (candle,)
    assert not hasattr(validated[0], "intrabar_first_touch_ordering")


class _NoNetworkClient:
    def linear_historical_candles(self, **_kwargs):
        raise AssertionError("unsupported input should fail before network fetch")


class _research_store:
    def __enter__(self) -> tuple[Path, ResearchStore]:
        root = Path("runtime") / f"b3-research-{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
        self._root = root
        return root, ResearchStore(root / "research.sqlite3")

    def __exit__(self, exc_type, exc, tb) -> bool:
        rmtree(self._root, ignore_errors=True)
        return False


def _candle_row(symbol: str, *, close: str = "100") -> dict[str, str | bool]:
    return {
        "symbol": symbol,
        "category": "linear",
        "timeframe": "1m",
        "open_time": START.isoformat(),
        "close_time": END.isoformat(),
        "open": "100",
        "high": "101",
        "low": "99",
        "close": close,
        "volume": "1",
        "turnover": "100",
        "completed": True,
    }


def _provenance(*, source_ref: str = "unit://diagnostic/BTCUSDT/1m") -> dict[str, str]:
    return {
        "source_kind": "SUPPLIED_DIAGNOSTIC_DATASET",
        "retrieved_at": START.isoformat().replace("+00:00", "Z"),
        "source_ref": source_ref,
    }


def _manifest(symbol: str) -> dict[str, object]:
    return {
        "dataset_kind": "OHLCV_CANDLES",
        "symbols": [symbol],
        "timeframe": "1m",
        "period_start": START.isoformat().replace("+00:00", "Z"),
        "period_end": END.isoformat().replace("+00:00", "Z"),
        "intrabar_first_touch_ordering": "UNAVAILABLE",
    }


def _report_definition(report_kind: str, dataset_id: str) -> dict[str, object]:
    items = ENTRY_REPORT_ITEMS if report_kind == "ENTRY_REPORT" else TAKE_PROFIT_REPORT_ITEMS
    return {
        "methodology_revision": "v1.2.15",
        "report_kind": report_kind,
        "source_dataset_id": dataset_id,
        "items": list(items),
        "calculation_policy": "read_only_diagnostic_no_canonical_feedback",
    }


def _report_payload(report_kind: str, dataset) -> dict[str, object]:
    items = ENTRY_REPORT_ITEMS if report_kind == "ENTRY_REPORT" else TAKE_PROFIT_REPORT_ITEMS
    return {
        "canonical_feedback": False,
        "report_kind": report_kind,
        "source_dataset_id": dataset.dataset_id,
        "members": [
            {
                "dataset_id": dataset.dataset_id,
                "content_digest": dataset.content_digest,
                "manifest_digest": dataset.manifest_digest,
            }
        ],
        "availability": {item: ("AVAILABLE" if index == 0 else "UNAVAILABLE") for index, item in enumerate(items)},
        "outputs": {item: {"status": "AVAILABLE" if index == 0 else "UNAVAILABLE"} for index, item in enumerate(items)},
    }
