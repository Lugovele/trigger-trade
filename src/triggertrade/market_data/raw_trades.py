"""Factual RAW_TRADES archive normalization for deterministic replay."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import csv
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
import gzip
from hashlib import sha256
from pathlib import Path
from typing import Any
import zipfile

from triggertrade.api_adapter_gateway import (
    build_market_data_response,
    coverage,
    dataset_payload,
    market_selection,
    market_selection_result,
)
from triggertrade.canonical_json import canonical_decimal_text, canonical_json_digest


BYBIT_PUBLIC_TRADE_ARCHIVE_REVISION = "bybit_public_trading_archive_v1"
BYBIT_PUBLIC_TRADE_ARCHIVE_BASE_URL = "https://public.bybit.com/trading"
BYBIT_PUBLIC_TRADE_ARCHIVE_SCHEMA = (
    "timestamp",
    "symbol",
    "side",
    "size",
    "price",
    "tickDirection",
    "trdMatchID",
    "grossValue",
    "homeNotional",
    "foreignNotional",
)
RAW_TRADES_UNAVAILABLE_MISSING_ARCHIVE_DAY = "raw_trades_archive_missing_source_day"
RAW_TRADES_UNAVAILABLE_ARCHIVE_MANIFEST_MISMATCH = "raw_trades_archive_manifest_mismatch"
RAW_TRADES_UNAVAILABLE_ARCHIVE_COMPLETENESS_UNATTESTED = "raw_trades_archive_completeness_unattested"

_FINAL_ARCHIVE_VALIDATION_STATUSES = frozenset({"OBJECTIVE_REMOTE_METADATA_VERIFIED", "OPERATOR_ATTESTED_COMPLETE"})


class RawTradesSourceError(ValueError):
    """Raised when factual raw trade source data cannot be normalized safely."""


@dataclass(frozen=True)
class RawTradeRecord:
    venue: str
    logical_symbol: str
    instrument_symbol: str
    trade_id: str
    executed_at: datetime
    taker_side: str
    price: Decimal
    quantity_base: Decimal
    notional_quote: Decimal
    source_endpoint: str
    source_revision: str
    source_file: str | None = None
    source_row_number: int | None = None

    def __post_init__(self) -> None:
        venue = _text(self.venue, field="venue").upper()
        logical_symbol = _symbol(self.logical_symbol)
        instrument_symbol = _symbol(self.instrument_symbol)
        if instrument_symbol != instrument_symbol_for_logical_symbol(logical_symbol):
            raise RawTradesSourceError("instrument symbol does not match logical Research symbol binding")
        trade_id = _text(self.trade_id, field="trade_id")
        executed_at = _utc(self.executed_at)
        side = _bybit_taker_side(self.taker_side)
        price = _positive_decimal(self.price, field="price")
        quantity = _positive_decimal(self.quantity_base, field="quantity_base")
        notional = _positive_decimal(self.notional_quote, field="notional_quote")
        source_endpoint = _text(self.source_endpoint, field="source_endpoint")
        source_revision = _text(self.source_revision, field="source_revision")
        object.__setattr__(self, "venue", venue)
        object.__setattr__(self, "logical_symbol", logical_symbol)
        object.__setattr__(self, "instrument_symbol", instrument_symbol)
        object.__setattr__(self, "trade_id", trade_id)
        object.__setattr__(self, "executed_at", executed_at)
        object.__setattr__(self, "taker_side", side)
        object.__setattr__(self, "price", price)
        object.__setattr__(self, "quantity_base", quantity)
        object.__setattr__(self, "notional_quote", notional)
        object.__setattr__(self, "source_endpoint", source_endpoint)
        object.__setattr__(self, "source_revision", source_revision)

    @property
    def factual_identity(self) -> tuple[str, str, str]:
        return (self.venue, self.instrument_symbol, self.trade_id)

    @property
    def provenance_digest(self) -> str:
        return canonical_json_digest(self.provenance_payload())

    def provenance_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "venue": self.venue,
            "logical_symbol": self.logical_symbol,
            "instrument_symbol": self.instrument_symbol,
            "trade_id": self.trade_id,
            "executed_at": _iso(self.executed_at),
            "taker_side": self.taker_side,
            "price": canonical_decimal_text(self.price),
            "quantity_base": canonical_decimal_text(self.quantity_base),
            "notional_quote": canonical_decimal_text(self.notional_quote),
            "source_endpoint": self.source_endpoint,
            "source_revision": self.source_revision,
        }
        if self.source_file is not None:
            payload["source_file"] = self.source_file
        return payload

    def contract_payload(self) -> dict[str, str]:
        return {
            "trade_id": self.trade_id,
            "occurred_at": _iso(self.executed_at),
            "taker_side": self.taker_side,
            "price": canonical_decimal_text(self.price),
            "quantity_base": canonical_decimal_text(self.quantity_base),
            "notional_quote": canonical_decimal_text(self.notional_quote),
        }


@dataclass(frozen=True)
class BybitRawTradeArchiveManifest:
    venue: str
    logical_symbol: str
    instrument_symbol: str
    archive_date: date
    canonical_source_url: str
    local_path: Path
    content_sha256: str
    byte_size: int
    source_revision: str
    schema_identifier: str
    factual_validation_status: str
    remote_etag: str | None = None
    remote_last_modified: str | None = None
    remote_byte_size: int | None = None

    def __post_init__(self) -> None:
        venue = _text(self.venue, field="venue").upper()
        logical = _symbol(self.logical_symbol)
        instrument = _symbol(self.instrument_symbol)
        if instrument != instrument_symbol_for_logical_symbol(logical):
            raise RawTradesSourceError("archive manifest instrument does not match logical Research symbol binding")
        expected_url = bybit_public_trade_archive_url(instrument, self.archive_date)
        if self.canonical_source_url != expected_url:
            raise RawTradesSourceError("archive manifest source URL does not match canonical Bybit path")
        digest = _hex_sha256(self.content_sha256, field="content_sha256")
        if not isinstance(self.byte_size, int) or isinstance(self.byte_size, bool) or self.byte_size <= 0:
            raise RawTradesSourceError("archive byte_size must be positive")
        source_revision = _text(self.source_revision, field="source_revision")
        schema = _text(self.schema_identifier, field="schema_identifier")
        if schema != ",".join(BYBIT_PUBLIC_TRADE_ARCHIVE_SCHEMA):
            raise RawTradesSourceError("archive schema identifier does not match verified Bybit archive schema")
        status = _text(self.factual_validation_status, field="factual_validation_status").upper()
        remote_size = self.remote_byte_size
        if remote_size is not None and (not isinstance(remote_size, int) or isinstance(remote_size, bool) or remote_size <= 0):
            raise RawTradesSourceError("remote_byte_size must be positive when present")
        object.__setattr__(self, "venue", venue)
        object.__setattr__(self, "logical_symbol", logical)
        object.__setattr__(self, "instrument_symbol", instrument)
        object.__setattr__(self, "local_path", Path(self.local_path))
        object.__setattr__(self, "content_sha256", digest)
        object.__setattr__(self, "source_revision", source_revision)
        object.__setattr__(self, "schema_identifier", schema)
        object.__setattr__(self, "factual_validation_status", status)

    @property
    def manifest_digest(self) -> str:
        return canonical_json_digest(self.manifest_payload())

    def manifest_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "venue": self.venue,
            "logical_symbol": self.logical_symbol,
            "instrument_symbol": self.instrument_symbol,
            "archive_date": self.archive_date.isoformat(),
            "canonical_source_url": self.canonical_source_url,
            "content_sha256": self.content_sha256,
            "byte_size": self.byte_size,
            "source_revision": self.source_revision,
            "schema_identifier": self.schema_identifier,
            "factual_validation_status": self.factual_validation_status,
        }
        if self.remote_etag is not None:
            payload["remote_etag"] = self.remote_etag
        if self.remote_last_modified is not None:
            payload["remote_last_modified"] = self.remote_last_modified
        if self.remote_byte_size is not None:
            payload["remote_byte_size"] = self.remote_byte_size
        return payload


@dataclass(frozen=True)
class RawTradesBackfillResult:
    response_payload: dict[str, Any]
    records: tuple[RawTradeRecord, ...]
    complete: bool
    missing_dates: tuple[date, ...]


def instrument_symbol_for_logical_symbol(logical_symbol: str) -> str:
    """Return the factual Bybit instrument symbol for a Research logical symbol."""

    symbol = _symbol(logical_symbol)
    asset = symbol.removesuffix("USDT")
    return str(_research_v1_instrument_symbol_overrides().get(asset, symbol)).upper()


def bybit_public_trade_archive_url(instrument_symbol: str, archive_date: date) -> str:
    symbol = _symbol(instrument_symbol)
    return f"{BYBIT_PUBLIC_TRADE_ARCHIVE_BASE_URL}/{symbol}/{symbol}{archive_date.isoformat()}.csv.gz"


def bybit_raw_trade_archive_manifest(
    path: str | Path,
    *,
    logical_symbol: str,
    archive_date: date,
    factual_validation_status: str,
    remote_etag: str | None = None,
    remote_last_modified: str | None = None,
    remote_byte_size: int | None = None,
    source_revision: str = BYBIT_PUBLIC_TRADE_ARCHIVE_REVISION,
) -> BybitRawTradeArchiveManifest:
    """Validate one official Bybit daily trade archive and build immutable provenance."""

    resolved = Path(path)
    raw = resolved.read_bytes()
    if not raw:
        raise RawTradesSourceError("archive file is empty")
    logical = _symbol(logical_symbol)
    instrument = instrument_symbol_for_logical_symbol(logical)
    header, rows = _read_csv_archive(resolved)
    _validate_bybit_archive_header(header)
    if not rows:
        raise RawTradesSourceError("archive contains no trade rows; empty-source finality requires external proof")
    records = normalize_bybit_public_trade_rows(
        rows,
        logical_symbol=logical,
        source_endpoint=bybit_public_trade_archive_url(instrument, archive_date),
        source_revision=source_revision,
        source_file=resolved.name,
    )
    for record in records:
        if record.instrument_symbol != instrument:
            raise RawTradesSourceError("archive contains wrong instrument")
        if record.executed_at.date() != archive_date:
            raise RawTradesSourceError("archive contains trades outside its UTC archive date")
    return BybitRawTradeArchiveManifest(
        venue="BYBIT",
        logical_symbol=logical,
        instrument_symbol=instrument,
        archive_date=archive_date,
        canonical_source_url=bybit_public_trade_archive_url(instrument, archive_date),
        local_path=resolved,
        content_sha256=sha256(raw).hexdigest(),
        byte_size=len(raw),
        source_revision=source_revision,
        schema_identifier=",".join(BYBIT_PUBLIC_TRADE_ARCHIVE_SCHEMA),
        factual_validation_status=factual_validation_status,
        remote_etag=remote_etag,
        remote_last_modified=remote_last_modified,
        remote_byte_size=remote_byte_size,
    )


def read_bybit_public_trade_archive(
    path: str | Path,
    *,
    logical_symbol: str,
    source_revision: str = BYBIT_PUBLIC_TRADE_ARCHIVE_REVISION,
    source_endpoint: str | None = None,
) -> tuple[RawTradeRecord, ...]:
    """Read one operator-supplied official Bybit public trade archive file."""

    resolved = Path(path)
    endpoint = source_endpoint or f"file://{resolved.name}"
    header, rows = _read_csv_archive(resolved)
    _validate_bybit_archive_header(header)
    return normalize_bybit_public_trade_rows(
        rows,
        logical_symbol=logical_symbol,
        source_endpoint=endpoint,
        source_revision=source_revision,
        source_file=resolved.name,
    )


def normalize_bybit_public_trade_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    logical_symbol: str,
    source_endpoint: str,
    source_revision: str = BYBIT_PUBLIC_TRADE_ARCHIVE_REVISION,
    source_file: str | None = None,
) -> tuple[RawTradeRecord, ...]:
    """Normalize verified Bybit public trade archive rows into RAW_TRADES facts."""

    logical = _symbol(logical_symbol)
    instrument = instrument_symbol_for_logical_symbol(logical)
    by_identity: dict[tuple[str, str, str], RawTradeRecord] = {}
    for index, row in enumerate(rows, start=1):
        _validate_bybit_archive_row_schema(row)
        record = _record_from_bybit_archive_row(
            row,
            logical_symbol=logical,
            instrument_symbol=instrument,
            source_endpoint=source_endpoint,
            source_revision=source_revision,
            source_file=source_file,
            source_row_number=index,
        )
        existing = by_identity.get(record.factual_identity)
        if existing is None:
            by_identity[record.factual_identity] = record
            continue
        if _factual_trade_payload(existing) != _factual_trade_payload(record):
            raise RawTradesSourceError(f"conflicting duplicate trade identity: {record.trade_id}")
    return tuple(sorted(by_identity.values(), key=lambda item: (item.executed_at, item.trade_id)))


def build_raw_trades_response(
    *,
    logical_symbol: str,
    records: Sequence[RawTradeRecord],
    range_from: datetime,
    range_to: datetime,
    request_id: str,
    response_id: str,
    selection_id: str,
    source_snapshot_id: str,
    source_endpoint: str,
    snapshot_started_at: datetime | None = None,
    snapshot_completed_at: datetime | None = None,
) -> dict[str, Any]:
    """Build a complete one-page MARKET_DATA_REQUEST.response for RAW_TRADES."""

    logical = _symbol(logical_symbol)
    start = _utc(range_from)
    end = _utc(range_to)
    if start >= end:
        raise RawTradesSourceError("RAW_TRADES range_from must be before range_to")
    instrument = instrument_symbol_for_logical_symbol(logical)
    filtered: list[RawTradeRecord] = []
    for record in records:
        if record.logical_symbol != logical or record.instrument_symbol != instrument:
            raise RawTradesSourceError("RAW_TRADES record symbol binding mismatch")
        if start <= record.executed_at < end:
            filtered.append(record)
        elif record.executed_at >= end:
            continue
    ordered = tuple(sorted(filtered, key=lambda item: (item.executed_at, item.trade_id)))
    trade_payload = tuple(record.contract_payload() for record in ordered)
    record_provenance_digest = canonical_json_digest(tuple(record.provenance_payload() for record in ordered))
    selection = market_selection(
        selection_id=selection_id,
        dataset="RAW_TRADES",
        mode="INTERVAL",
        as_of=end,
        range_from=start,
        range_to=end,
        completed_only=False,
        page_size=max(1, len(trade_payload) or 1),
    )
    page_id = _page_id(
        logical_symbol=logical,
        source_snapshot_id=source_snapshot_id,
        selection_id=selection_id,
        page_index=0,
        trades=trade_payload,
        record_provenance_digest=record_provenance_digest,
    )
    result = market_selection_result(
        symbol=logical,
        selection=selection,
        page_id=page_id,
        page_index=0,
        source_snapshot_id=source_snapshot_id,
        payload=dataset_payload(
            dataset="RAW_TRADES",
            status="AVAILABLE",
            as_of=end,
            source_endpoint=source_endpoint,
            data=trade_payload,
        ),
        coverage=coverage(
            covered_ranges=({"from": start, "to": end},),
            missing_ranges=(),
            coverage_complete=True,
            pagination_complete=True,
            next_cursor=None,
            expected_page_ids=(page_id,),
            source_finality_confirmed=True,
        ),
    )
    snapshot_start = snapshot_started_at or end
    snapshot_end = snapshot_completed_at or end
    return build_market_data_response(
        request_id=request_id,
        response_id=response_id,
        symbol=logical,
        snapshot_started_at=snapshot_start,
        snapshot_completed_at=snapshot_end,
        as_of=end,
        selection_results=(result,),
        expected_selections=(selection,),
    ).to_payload()


def build_unavailable_raw_trades_response(
    *,
    logical_symbol: str,
    range_from: datetime,
    range_to: datetime,
    request_id: str,
    response_id: str,
    selection_id: str,
    source_snapshot_id: str,
    source_endpoint: str,
    reason_code: str,
) -> dict[str, Any]:
    """Build an unavailable RAW_TRADES response without pretending coverage is complete."""

    logical = _symbol(logical_symbol)
    start = _utc(range_from)
    end = _utc(range_to)
    selection = market_selection(
        selection_id=selection_id,
        dataset="RAW_TRADES",
        mode="INTERVAL",
        as_of=end,
        range_from=start,
        range_to=end,
        completed_only=False,
        page_size=1,
    )
    page_id = _page_id(
        logical_symbol=logical,
        source_snapshot_id=source_snapshot_id,
        selection_id=selection_id,
        page_index=0,
        trades=(),
    )
    result = market_selection_result(
        symbol=logical,
        selection=selection,
        page_id=page_id,
        page_index=0,
        source_snapshot_id=source_snapshot_id,
        payload=dataset_payload(
            dataset="RAW_TRADES",
            status="UNAVAILABLE",
            as_of=end,
            source_endpoint=source_endpoint,
            data=None,
        ),
        coverage=coverage(
            covered_ranges=(),
            missing_ranges=({"from": start, "to": end},),
            coverage_complete=False,
            pagination_complete=True,
            next_cursor=None,
            expected_page_ids=(page_id,),
            source_finality_confirmed=False,
            reason_code=reason_code,
        ),
    )
    return build_market_data_response(
        request_id=request_id,
        response_id=response_id,
        symbol=logical,
        snapshot_started_at=end,
        snapshot_completed_at=end,
        as_of=end,
        selection_results=(result,),
        expected_selections=(selection,),
    ).to_payload()


def build_bybit_archive_raw_trades_response(
    *,
    logical_symbol: str,
    range_from: datetime,
    range_to: datetime,
    archive_manifests_by_date: Mapping[date, BybitRawTradeArchiveManifest],
    request_id: str,
    response_id: str,
    selection_id: str,
    source_snapshot_id: str,
) -> RawTradesBackfillResult:
    """Build RAW_TRADES response from validated Bybit daily archive manifests."""

    logical = _symbol(logical_symbol)
    start = _utc(range_from)
    end = _utc(range_to)
    required_dates = _required_utc_dates(start, end)
    manifests_by_date = dict(archive_manifests_by_date)
    missing = tuple(day for day in required_dates if day not in manifests_by_date)
    instrument = instrument_symbol_for_logical_symbol(logical)
    source_endpoint = _archive_source_endpoint(instrument, required_dates)
    if missing:
        return RawTradesBackfillResult(
            response_payload=build_unavailable_raw_trades_response(
                logical_symbol=logical,
                range_from=start,
                range_to=end,
                request_id=request_id,
                response_id=response_id,
                selection_id=selection_id,
                source_snapshot_id=source_snapshot_id,
                source_endpoint=source_endpoint,
                reason_code=RAW_TRADES_UNAVAILABLE_MISSING_ARCHIVE_DAY,
            ),
            records=(),
            complete=False,
            missing_dates=missing,
        )
    records: list[RawTradeRecord] = []
    manifests: list[BybitRawTradeArchiveManifest] = []
    for day in required_dates:
        manifest = manifests_by_date[day]
        if (
            manifest.archive_date != day
            or manifest.logical_symbol != logical
            or manifest.instrument_symbol != instrument
            or manifest.canonical_source_url != bybit_public_trade_archive_url(instrument, day)
        ):
            return RawTradesBackfillResult(
                response_payload=build_unavailable_raw_trades_response(
                    logical_symbol=logical,
                    range_from=start,
                    range_to=end,
                    request_id=request_id,
                    response_id=response_id,
                    selection_id=selection_id,
                    source_snapshot_id=f"raw-trades-archive-invalid-{day.isoformat()}",
                    source_endpoint=source_endpoint,
                    reason_code=RAW_TRADES_UNAVAILABLE_ARCHIVE_MANIFEST_MISMATCH,
                ),
                records=(),
                complete=False,
                missing_dates=(),
            )
        if manifest.factual_validation_status not in _FINAL_ARCHIVE_VALIDATION_STATUSES:
            return RawTradesBackfillResult(
                response_payload=build_unavailable_raw_trades_response(
                    logical_symbol=logical,
                    range_from=start,
                    range_to=end,
                    request_id=request_id,
                    response_id=response_id,
                    selection_id=selection_id,
                    source_snapshot_id=f"raw-trades-archive-unattested-{day.isoformat()}",
                    source_endpoint=source_endpoint,
                    reason_code=RAW_TRADES_UNAVAILABLE_ARCHIVE_COMPLETENESS_UNATTESTED,
                ),
                records=(),
                complete=False,
                missing_dates=(),
            )
        manifests.append(manifest)
        records.extend(
            read_bybit_public_trade_archive(
                manifest.local_path,
                logical_symbol=logical,
                source_endpoint=_source_endpoint_with_manifest(manifest),
                source_revision=manifest.source_revision,
            )
        )
    deduped = _dedupe_records(records)
    manifest_digest = _combined_manifest_digest(
        manifests,
        logical_symbol=logical,
        instrument_symbol=instrument,
        range_from=start,
        range_to=end,
    )
    return RawTradesBackfillResult(
        response_payload=build_raw_trades_response(
            logical_symbol=logical,
            records=deduped,
            range_from=start,
            range_to=end,
            request_id=request_id,
            response_id=response_id,
            selection_id=selection_id,
            source_snapshot_id=f"raw-trades-archive-{manifest_digest[:32]}",
            source_endpoint=_combined_source_endpoint(
                instrument_symbol=instrument,
                logical_symbol=logical,
                required_dates=required_dates,
                manifest_digest=manifest_digest,
                source_revision=BYBIT_PUBLIC_TRADE_ARCHIVE_REVISION,
            ),
        ),
        records=deduped,
        complete=True,
        missing_dates=(),
    )


def _record_from_bybit_archive_row(
    row: Mapping[str, Any],
    *,
    logical_symbol: str,
    instrument_symbol: str,
    source_endpoint: str,
    source_revision: str,
    source_file: str | None,
    source_row_number: int,
) -> RawTradeRecord:
    row_symbol = _field(row, ("symbol",))
    if _symbol(row_symbol) != instrument_symbol:
        raise RawTradesSourceError("Bybit trade row symbol does not match requested instrument")
    trade_id = _field(row, ("trdMatchID",))
    price = _decimal_field(row, ("price",))
    quantity = _decimal_field(row, ("size",))
    notional = _optional_decimal_field(row, ("foreignNotional",))
    if notional is None:
        notional = price * quantity
    return RawTradeRecord(
        venue="BYBIT",
        logical_symbol=logical_symbol,
        instrument_symbol=instrument_symbol,
        trade_id=str(trade_id),
        executed_at=_parse_trade_timestamp(_field(row, ("timestamp",))),
        taker_side=str(_field(row, ("side",))),
        price=price,
        quantity_base=quantity,
        notional_quote=notional,
        source_endpoint=source_endpoint,
        source_revision=source_revision,
        source_file=source_file,
        source_row_number=source_row_number,
    )


def _dedupe_records(records: Iterable[RawTradeRecord]) -> tuple[RawTradeRecord, ...]:
    by_identity: dict[tuple[str, str, str], RawTradeRecord] = {}
    for record in records:
        existing = by_identity.get(record.factual_identity)
        if existing is None:
            by_identity[record.factual_identity] = record
            continue
        if _factual_trade_payload(existing) != _factual_trade_payload(record):
            raise RawTradesSourceError(f"conflicting duplicate trade identity: {record.trade_id}")
    return tuple(sorted(by_identity.values(), key=lambda item: (item.executed_at, item.trade_id)))


def _factual_trade_payload(record: RawTradeRecord) -> dict[str, Any]:
    return {
        "venue": record.venue,
        "logical_symbol": record.logical_symbol,
        "instrument_symbol": record.instrument_symbol,
        **record.contract_payload(),
    }


def _read_csv_archive(path: Path) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    if path.suffix.lower() == ".gz":
        with gzip.open(path, mode="rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return tuple(reader.fieldnames or ()), tuple(reader)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = sorted(name for name in archive.namelist() if not name.endswith("/"))
            if not names:
                raise RawTradesSourceError("empty Bybit trade archive zip")
            with archive.open(names[0]) as raw:
                text = raw.read().decode("utf-8")
            reader = csv.DictReader(text.splitlines())
            return tuple(reader.fieldnames or ()), tuple(reader)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), tuple(reader)


def _validate_bybit_archive_header(header: Sequence[str]) -> None:
    if tuple(header) != BYBIT_PUBLIC_TRADE_ARCHIVE_SCHEMA:
        raise RawTradesSourceError("Bybit archive header does not match verified public trade archive schema")


def _validate_bybit_archive_row_schema(row: Mapping[str, Any]) -> None:
    if tuple(row.keys()) != BYBIT_PUBLIC_TRADE_ARCHIVE_SCHEMA:
        raise RawTradesSourceError("Bybit archive row does not match verified public trade archive schema")


def _required_utc_dates(start: datetime, end: datetime) -> tuple[date, ...]:
    current = datetime.combine(start.date(), time.min, tzinfo=UTC).date()
    last = (end - timedelta(microseconds=1)).date()
    days: list[date] = []
    while current <= last:
        days.append(current)
        current = current + timedelta(days=1)
    return tuple(days)


def _archive_source_endpoint(instrument_symbol: str, days: Sequence[date]) -> str:
    if not days:
        return f"{BYBIT_PUBLIC_TRADE_ARCHIVE_BASE_URL}/{_symbol(instrument_symbol)}"
    return f"{BYBIT_PUBLIC_TRADE_ARCHIVE_BASE_URL}/{_symbol(instrument_symbol)}/{days[0].isoformat()}..{days[-1].isoformat()}"


def _source_endpoint_with_manifest(manifest: BybitRawTradeArchiveManifest) -> str:
    return (
        f"{manifest.canonical_source_url}"
        f"#manifest_digest={manifest.manifest_digest}"
        f";content_sha256={manifest.content_sha256}"
        f";bytes={manifest.byte_size}"
        f";logical={manifest.logical_symbol}"
        f";instrument={manifest.instrument_symbol}"
        f";revision={manifest.source_revision}"
        f";validation={manifest.factual_validation_status}"
    )


def _combined_manifest_digest(
    manifests: Sequence[BybitRawTradeArchiveManifest],
    *,
    logical_symbol: str,
    instrument_symbol: str,
    range_from: datetime,
    range_to: datetime,
) -> str:
    return canonical_json_digest(
        {
            "dataset": "RAW_TRADES",
            "logical_symbol": logical_symbol,
            "instrument_symbol": instrument_symbol,
            "range_from": _iso(range_from),
            "range_to": _iso(range_to),
            "archive_manifests": [manifest.manifest_payload() for manifest in manifests],
        }
    )


def _combined_source_endpoint(
    *,
    instrument_symbol: str,
    logical_symbol: str,
    required_dates: Sequence[date],
    manifest_digest: str,
    source_revision: str,
) -> str:
    base = _archive_source_endpoint(instrument_symbol, required_dates)
    return (
        f"{base}"
        f"#manifest_digest={manifest_digest}"
        f";logical={logical_symbol}"
        f";instrument={instrument_symbol}"
        f";revision={source_revision}"
    )


def _page_id(
    *,
    logical_symbol: str,
    source_snapshot_id: str,
    selection_id: str,
    page_index: int,
    trades: Sequence[Mapping[str, Any]],
    record_provenance_digest: str | None = None,
) -> str:
    digest = canonical_json_digest(
        {
            "dataset": "RAW_TRADES",
            "logical_symbol": logical_symbol,
            "source_snapshot_id": source_snapshot_id,
            "selection_id": selection_id,
            "page_index": page_index,
            "trades": list(trades),
            "record_provenance_digest": record_provenance_digest,
        }
    )
    return f"mdp-raw-trades-{digest[:24]}"


def _field(row: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in {None, ""}:
            return value
    raise RawTradesSourceError(f"Bybit trade row missing required field: {keys[0]}")


def _optional_field(row: Mapping[str, Any], keys: Sequence[str]) -> Any | None:
    for key in keys:
        value = row.get(key)
        if value not in {None, ""}:
            return value
    return None


def _decimal_field(row: Mapping[str, Any], keys: Sequence[str]) -> Decimal:
    value = _field(row, keys)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise RawTradesSourceError(f"invalid decimal field: {keys[0]}") from exc


def _optional_decimal_field(row: Mapping[str, Any], keys: Sequence[str]) -> Decimal | None:
    value = _optional_field(row, keys)
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise RawTradesSourceError(f"invalid decimal field: {keys[0]}") from exc


def _parse_trade_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return _utc(value)
    text = str(value).strip()
    if not text:
        raise RawTradesSourceError("trade timestamp is required")
    if text.isdigit():
        raw = int(text)
        if raw >= 100_000_000_000_000_000:
            seconds, remainder = divmod(raw, 1_000_000_000)
            return datetime.fromtimestamp(seconds, tz=UTC) + timedelta(microseconds=remainder // 1_000)
        if raw >= 100_000_000_000_000:
            seconds, remainder = divmod(raw, 1_000_000)
            return datetime.fromtimestamp(seconds, tz=UTC) + timedelta(microseconds=remainder)
        if raw >= 100_000_000_000:
            seconds, remainder = divmod(raw, 1_000)
            return datetime.fromtimestamp(seconds, tz=UTC) + timedelta(milliseconds=remainder)
        return datetime.fromtimestamp(raw, tz=UTC)
    normalized = text.replace("Z", "+00:00")
    try:
        return _utc(datetime.fromisoformat(normalized))
    except ValueError as exc:
        raise RawTradesSourceError("invalid trade timestamp") from exc


def _bybit_taker_side(value: str) -> str:
    side = _text(value, field="taker_side").upper()
    if side == "BUY":
        return "BUY"
    if side == "SELL":
        return "SELL"
    raise RawTradesSourceError("Bybit taker side must be Buy/Sell")


def _positive_decimal(value: Decimal, *, field: str) -> Decimal:
    try:
        resolved = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise RawTradesSourceError(f"{field} must be decimal") from exc
    if not resolved.is_finite() or resolved <= 0:
        raise RawTradesSourceError(f"{field} must be a positive finite decimal")
    return resolved


def _utc(value: datetime) -> datetime:
    resolved = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return resolved.astimezone(UTC)


def _iso(value: datetime) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def _symbol(value: str) -> str:
    return _text(value, field="symbol").upper()


def _text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise RawTradesSourceError(f"{field} is required")
    if "\x00" in value:
        raise RawTradesSourceError(f"{field} cannot contain NUL")
    return value


def _research_v1_instrument_symbol_overrides() -> Mapping[str, str]:
    from triggertrade.research_v1_execution import RESEARCH_V1_INSTRUMENT_SYMBOL_OVERRIDES

    return RESEARCH_V1_INSTRUMENT_SYMBOL_OVERRIDES


def _hex_sha256(value: str, *, field: str) -> str:
    text = _text(value, field=field).lower()
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise RawTradesSourceError(f"{field} must be a SHA-256 hex digest")
    return text
