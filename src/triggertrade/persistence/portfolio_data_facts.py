"""Durable factual Portfolio Data Request/response journal."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text
from triggertrade.contracts import ContractError, parse_contract

from .postgres import PostgresPersistenceError


class PortfolioDataFactConflict(PostgresPersistenceError):
    """Raised when a Portfolio Data fact identity is replayed with different content."""


@dataclass(frozen=True)
class PortfolioDataRequestRecord:
    request_id: str
    request_mode: str
    payload: dict[str, Any]
    payload_digest: str


@dataclass(frozen=True)
class PortfolioDataResponseRecord:
    response_id: str
    request_id: str
    request_mode: str
    payload: dict[str, Any]
    payload_digest: str


class PortfolioDataFactStore:
    """Persist approved Portfolio Data v5 envelopes without interpreting business state."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def record_request(self, payload: Mapping[str, Any]) -> tuple[PortfolioDataRequestRecord, bool]:
        parsed = _parse(payload, definition="PORTFOLIO_DATA_REQUEST.request")
        body = parsed["portfolio_data_request"]
        payload_text, digest = _payload_text_and_digest(parsed)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_portfolio_data_requests (
                    request_id, request_mode, requested_at, payload_json, payload_digest
                ) VALUES (%s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (request_id) DO NOTHING
                RETURNING request_id, request_mode, payload_json::text, payload_digest
                """,
                (body["request_id"], body["request_mode"], body["requested_at"], payload_text, digest),
            )
            row = cursor.fetchone()
        if row is not None:
            return _request_from_row(row), True
        existing = self.get_request(request_id=str(body["request_id"]))
        if existing is None:
            raise PostgresPersistenceError("portfolio data request conflicted but no record was found")
        if existing.payload_digest != digest or existing.request_mode != body["request_mode"]:
            raise PortfolioDataFactConflict("portfolio data request id already exists with different content")
        return existing, False

    def record_response(self, payload: Mapping[str, Any]) -> tuple[PortfolioDataResponseRecord, bool]:
        parsed = _parse(payload, definition="PORTFOLIO_DATA_REQUEST.response")
        body = parsed["portfolio_data_response"]
        payload_text, digest = _payload_text_and_digest(parsed)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_portfolio_data_responses (
                    response_id, request_id, request_mode, as_of, payload_json, payload_digest
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (response_id) DO NOTHING
                RETURNING response_id, request_id, request_mode, payload_json::text, payload_digest
                """,
                (body["response_id"], body["request_id"], body["request_mode"], body["as_of"], payload_text, digest),
            )
            row = cursor.fetchone()
        if row is not None:
            return _response_from_row(row), True
        existing = self.get_response(response_id=str(body["response_id"]))
        if existing is None:
            raise PostgresPersistenceError("portfolio data response conflicted but no record was found")
        if (
            existing.payload_digest != digest
            or existing.request_id != body["request_id"]
            or existing.request_mode != body["request_mode"]
        ):
            raise PortfolioDataFactConflict("portfolio data response id already exists with different content")
        return existing, False

    def get_request(self, *, request_id: str) -> PortfolioDataRequestRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT request_id, request_mode, payload_json::text, payload_digest
                FROM triggertrade_portfolio_data_requests
                WHERE request_id = %s
                """,
                (request_id,),
            )
            row = cursor.fetchone()
        return None if row is None else _request_from_row(row)

    def get_response(self, *, response_id: str) -> PortfolioDataResponseRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT response_id, request_id, request_mode, payload_json::text, payload_digest
                FROM triggertrade_portfolio_data_responses
                WHERE response_id = %s
                """,
                (response_id,),
            )
            row = cursor.fetchone()
        return None if row is None else _response_from_row(row)


def _parse(payload: Mapping[str, Any], *, definition: str) -> dict[str, Any]:
    try:
        return parse_contract("PORTFOLIO_DATA_REQUEST", payload, definition=definition).to_payload()
    except ContractError as exc:
        raise PostgresPersistenceError(str(exc)) from exc


def _payload_text_and_digest(payload: Mapping[str, Any]) -> tuple[str, str]:
    payload_text = canonical_json_text(payload)
    return payload_text, canonical_json_digest(payload)


def _request_from_row(row: tuple[Any, ...]) -> PortfolioDataRequestRecord:
    return PortfolioDataRequestRecord(
        request_id=str(row[0]),
        request_mode=str(row[1]),
        payload=json.loads(str(row[2]), parse_float=Decimal),
        payload_digest=str(row[3]),
    )


def _response_from_row(row: tuple[Any, ...]) -> PortfolioDataResponseRecord:
    return PortfolioDataResponseRecord(
        response_id=str(row[0]),
        request_id=str(row[1]),
        request_mode=str(row[2]),
        payload=json.loads(str(row[3]), parse_float=Decimal),
        payload_digest=str(row[4]),
    )
