"""Durable API market data response page evidence."""

from __future__ import annotations

from dataclasses import dataclass
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
