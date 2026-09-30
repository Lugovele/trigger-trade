"""Durable API market data response page evidence."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text
from triggertrade.contracts import ContractError, parse_contract

from .postgres import PostgresPersistenceError


class MarketDataFactConflict(PostgresPersistenceError):
    """Raised when an immutable market data page identity is replayed with different content."""


@dataclass(frozen=True)
class MarketDataPageRecord:
    page_id: str
    request_id: str
    response_id: str
    symbol: str
    selection_id: str
    selection_digest: str
    dataset: str
    page_index: int
    source_snapshot_id: str
    payload: dict[str, Any]
    payload_digest: str


class MarketDataFactStore:
    """Persist strict Market Data Request v3 response pages for replay evidence."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def put_response(self, payload: dict[str, Any]) -> tuple[tuple[MarketDataPageRecord, ...], bool]:
        try:
            parsed = parse_contract("MARKET_DATA_REQUEST", payload, definition="MARKET_DATA_REQUEST.response")
        except ContractError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        resolved = parsed.to_payload()
        body = resolved["market_data_response"]
        records: list[MarketDataPageRecord] = []
        inserted_any = False
        for result in body["selection_results"]:
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
            payload_text = canonical_json_text(page_payload)
            digest = canonical_json_digest(page_payload)
            dataset = next(iter(result["payload"]))
            with self._connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO triggertrade_market_data_pages (
                        page_id, request_id, response_id, symbol, selection_id, selection_digest,
                        dataset, page_index, source_snapshot_id, payload_json, payload_digest
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT DO NOTHING
                    RETURNING
                        page_id, request_id, response_id, symbol, selection_id, selection_digest,
                        dataset, page_index, source_snapshot_id, payload_json::text, payload_digest
                    """,
                    (
                        result["page_id"],
                        body["request_id"],
                        body["response_id"],
                        body["symbol"],
                        result["selection"]["selection_id"],
                        result["selection_digest"],
                        dataset,
                        result["page_index"],
                        result["source_snapshot_id"],
                        payload_text,
                        digest,
                    ),
                )
                row = cursor.fetchone()
            if row is not None:
                inserted_any = True
                records.append(_record_from_row(row))
                continue
            existing = self.get_page(page_id=result["page_id"])
            if existing is None:
                raise PostgresPersistenceError("market data page insert conflicted but no record was found")
            if (
                existing.payload_digest != digest
                or existing.request_id != body["request_id"]
                or existing.response_id != body["response_id"]
                or existing.symbol != body["symbol"]
                or existing.selection_id != result["selection"]["selection_id"]
                or existing.selection_digest != result["selection_digest"]
                or existing.dataset != dataset
                or existing.page_index != result["page_index"]
                or existing.source_snapshot_id != result["source_snapshot_id"]
            ):
                raise MarketDataFactConflict("market data page identity already exists with different content")
            records.append(existing)
        return tuple(records), inserted_any

    def get_page(self, *, page_id: str) -> MarketDataPageRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_PAGE + " WHERE page_id = %s", (page_id,))
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def list_selection_pages(self, *, selection_id: str) -> tuple[MarketDataPageRecord, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                _SELECT_PAGE + " WHERE selection_id = %s ORDER BY source_snapshot_id, page_index, page_id",
                (selection_id,),
            )
            rows = cursor.fetchall()
        return tuple(_record_from_row(row) for row in rows)

    def latest_last_traded_price_response_as_of(self, *, symbol: str, as_of: datetime) -> dict[str, Any] | None:
        """Return the latest eligible canonical LAST_TRADED_PRICE AS_OF response page."""

        target = _timestamp(as_of)
        with self._connection.cursor() as cursor:
            cursor.execute(
                _SELECT_PAGE + " WHERE symbol = %s AND dataset = %s ORDER BY source_snapshot_id, page_index, page_id",
                (symbol.upper(), "LAST_TRADED_PRICE"),
            )
            rows = cursor.fetchall()
        candidates: list[tuple[datetime, str, dict[str, Any]]] = []
        for row in rows:
            record = _record_from_row(row)
            response = _response_from_page(record)
            result = response["market_data_response"]["selection_results"][0]
            observed_at = _eligible_last_traded_price_observed_at(record=record, result=result)
            if observed_at is None:
                continue
            if observed_at > target:
                continue
            candidates.append((observed_at, record.page_id, response))
        if not candidates:
            return None
        return deepcopy(max(candidates, key=lambda item: (item[0], item[1]))[2])


_SELECT_PAGE = """
SELECT
    page_id, request_id, response_id, symbol, selection_id, selection_digest,
    dataset, page_index, source_snapshot_id, payload_json::text, payload_digest
FROM triggertrade_market_data_pages
"""


def _record_from_row(row: tuple[Any, ...]) -> MarketDataPageRecord:
    return MarketDataPageRecord(
        page_id=str(row[0]),
        request_id=str(row[1]),
        response_id=str(row[2]),
        symbol=str(row[3]),
        selection_id=str(row[4]),
        selection_digest=str(row[5]),
        dataset=str(row[6]),
        page_index=int(row[7]),
        source_snapshot_id=str(row[8]),
        payload=json.loads(str(row[9]), parse_float=Decimal),
        payload_digest=str(row[10]),
    )


def _response_from_page(record: MarketDataPageRecord) -> dict[str, Any]:
    page = record.payload.get("market_data_response_page")
    if not isinstance(page, dict):
        raise PostgresPersistenceError("market data page payload is not a MARKET_DATA_REQUEST response page")
    response = {
        "market_data_response": {
            "contract_version": page["contract_version"],
            "request_id": page["request_id"],
            "response_id": page["response_id"],
            "symbol": page["symbol"],
            "snapshot_started_at": page["snapshot_started_at"],
            "snapshot_completed_at": page["snapshot_completed_at"],
            "as_of": page["as_of"],
            "source": page["source"],
            "selection_results": [page["selection_result"]],
        }
    }
    try:
        return parse_contract("MARKET_DATA_REQUEST", response, definition="MARKET_DATA_REQUEST.response").to_payload()
    except ContractError as exc:
        raise PostgresPersistenceError(str(exc)) from exc


def _eligible_last_traded_price_observed_at(*, record: MarketDataPageRecord, result: dict[str, Any]) -> datetime | None:
    selection = result.get("selection")
    payload = result.get("payload")
    coverage = result.get("coverage")
    if not isinstance(selection, dict) or not isinstance(payload, dict) or not isinstance(coverage, dict):
        return None
    if selection.get("dataset") != "LAST_TRADED_PRICE" or selection.get("mode") != "AS_OF":
        return None
    if not record.selection_digest or not record.source_snapshot_id or not result.get("page_id"):
        return None
    if not _complete_final_coverage(coverage):
        return None
    last_traded_price = payload.get("LAST_TRADED_PRICE")
    if not isinstance(last_traded_price, dict) or last_traded_price.get("status") != "AVAILABLE":
        return None
    source_endpoint = last_traded_price.get("source_endpoint")
    if not isinstance(source_endpoint, str) or not source_endpoint:
        return None
    data = last_traded_price.get("data")
    if not isinstance(data, dict):
        return None
    if not all(isinstance(data.get(field), str) and data.get(field) for field in ("price", "observed_at", "source_record_id", "venue", "instrument_symbol")):
        return None
    try:
        observed_at = _timestamp(data.get("observed_at"))
        if _timestamp(last_traded_price.get("as_of")) < observed_at:
            return None
    except (TypeError, ValueError):
        return None
    return observed_at


def _complete_final_coverage(coverage: dict[str, Any]) -> bool:
    return (
        coverage.get("coverage_complete") is True
        and coverage.get("pagination_complete") is True
        and coverage.get("source_finality_confirmed") is True
        and coverage.get("next_cursor") is None
        and not coverage.get("missing_ranges")
    )


def _timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise TypeError("timestamp value must be datetime or ISO string")
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
