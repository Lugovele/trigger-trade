"""Market Data Request v3 factual envelope builders."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.contracts import ContractError, TargetContract, parse_contract


class MarketDataGatewayError(ValueError):
    """Raised when factual market API data cannot form an approved envelope."""


_DATASETS = {
    "TICKER",
    "BEST_BID_ASK",
    "KLINES",
    "VOLUME",
    "OPEN_INTEREST",
    "FUNDING_RATE",
    "RAW_TRADES",
    "QUOTE_TURNOVER",
    "INSTRUMENT_METADATA",
}
_AS_OF_DATASETS = {"TICKER", "BEST_BID_ASK", "VOLUME", "OPEN_INTEREST", "FUNDING_RATE", "INSTRUMENT_METADATA"}
_INTERVAL_DATASETS = {"KLINES", "RAW_TRADES", "QUOTE_TURNOVER"}
_STATUSES = {"AVAILABLE", "PARTIAL", "UNAVAILABLE"}


@dataclass(frozen=True)
class MarketDataSelection:
    selection_id: str
    dataset: str
    mode: str
    as_of: str
    range_from: str | None
    range_to: str | None
    completed_only: bool
    timeframe: str | None
    count: int | None
    cursor: str | None
    page_size: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "selection_id", _text(self.selection_id, field="selection_id"))
        dataset = _text(self.dataset, field="dataset")
        if dataset not in _DATASETS:
            raise MarketDataGatewayError(f"unsupported market dataset: {dataset}")
        object.__setattr__(self, "dataset", dataset)
        mode = _text(self.mode, field="mode")
        if mode not in {"AS_OF", "INTERVAL"}:
            raise MarketDataGatewayError("mode must be AS_OF or INTERVAL")
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "as_of", _timestamp(self.as_of))
        if not isinstance(self.completed_only, bool):
            raise MarketDataGatewayError("completed_only must be a boolean")
        if not isinstance(self.page_size, int) or isinstance(self.page_size, bool) or self.page_size < 1:
            raise MarketDataGatewayError("page_size must be a positive integer")
        if self.count is not None and (not isinstance(self.count, int) or isinstance(self.count, bool) or self.count < 1):
            raise MarketDataGatewayError("count must be a positive integer or null")
        if self.cursor is not None:
            _text(self.cursor, field="cursor")
        if mode == "AS_OF":
            if dataset not in _AS_OF_DATASETS:
                raise MarketDataGatewayError(f"{dataset} must use INTERVAL mode")
            if self.range_from is not None or self.range_to is not None or self.timeframe is not None or self.count is not None:
                raise MarketDataGatewayError("AS_OF selections require null range_from, range_to, timeframe, and count")
        if mode == "INTERVAL":
            if dataset not in _INTERVAL_DATASETS:
                raise MarketDataGatewayError(f"{dataset} must use AS_OF mode")
            if self.range_from is None or self.range_to is None:
                raise MarketDataGatewayError("INTERVAL selections require range_from and range_to")
            object.__setattr__(self, "range_from", _timestamp(self.range_from))
            object.__setattr__(self, "range_to", _timestamp(self.range_to))
            if self.range_from >= self.range_to or self.range_to > self.as_of:
                raise MarketDataGatewayError("INTERVAL selections require range_from < range_to <= as_of")
            if dataset == "KLINES":
                if not self.completed_only or self.timeframe is None:
                    raise MarketDataGatewayError("KLINES selections require completed_only=true and timeframe")
                _text(self.timeframe, field="timeframe")
            elif self.timeframe is not None or self.count is not None:
                raise MarketDataGatewayError(f"{dataset} selections require null timeframe and count")

    def to_payload(self) -> dict[str, Any]:
        return {
            "selection_id": self.selection_id,
            "dataset": self.dataset,
            "mode": self.mode,
            "as_of": self.as_of,
            "range_from": self.range_from,
            "range_to": self.range_to,
            "bounds": "FROM_INCLUSIVE_TO_EXCLUSIVE",
            "completed_only": self.completed_only,
            "timeframe": self.timeframe,
            "count": self.count,
            "cursor": self.cursor,
            "page_size": self.page_size,
        }


def market_selection(
    *,
    selection_id: str,
    dataset: str,
    mode: str,
    as_of: datetime | str,
    range_from: datetime | str | None = None,
    range_to: datetime | str | None = None,
    completed_only: bool = False,
    timeframe: str | None = None,
    count: int | None = None,
    cursor: str | None = None,
    page_size: int = 1,
) -> MarketDataSelection:
    return MarketDataSelection(
        selection_id=selection_id,
        dataset=dataset,
        mode=mode,
        as_of=_timestamp(as_of),
        range_from=None if range_from is None else _timestamp(range_from),
        range_to=None if range_to is None else _timestamp(range_to),
        completed_only=completed_only,
        timeframe=timeframe,
        count=count,
        cursor=cursor,
        page_size=page_size,
    )


def market_selection_digest(*, symbol: str, selection: MarketDataSelection | Mapping[str, Any]) -> str:
    payload = _selection_payload(selection)
    digest_payload = {"symbol": _symbol(symbol), **{key: value for key, value in payload.items() if key != "cursor"}}
    return canonical_json_digest(digest_payload)


def build_market_data_request(
    *,
    request_id: str,
    requested_at: datetime | str,
    symbol: str,
    purpose: str,
    selections: Sequence[MarketDataSelection | Mapping[str, Any]],
    decision_cycle_id: str | None = None,
    set_result_id: str | None = None,
) -> TargetContract:
    selection_payloads = _selection_payloads(selections)
    _validate_unique_selection_ids(selection_payloads)
    body: dict[str, Any] = {
        "contract_version": 3,
        "request_id": _text(request_id, field="request_id"),
        "requested_at": _timestamp(requested_at),
        "symbol": _symbol(symbol),
        "purpose": purpose,
        "selections": selection_payloads,
    }
    if decision_cycle_id is not None or set_result_id is not None:
        body["decision_cycle_id"] = None if decision_cycle_id is None else _text(decision_cycle_id, field="decision_cycle_id")
        body["set_result_id"] = None if set_result_id is None else _text(set_result_id, field="set_result_id")
    return _parse({"market_data_request": body}, definition="MARKET_DATA_REQUEST.request")


def build_market_data_response(
    *,
    request_id: str,
    response_id: str,
    symbol: str,
    snapshot_started_at: datetime | str,
    snapshot_completed_at: datetime | str,
    as_of: datetime | str,
    selection_results: Sequence[Mapping[str, Any]],
    expected_selections: Sequence[MarketDataSelection | Mapping[str, Any]] | None = None,
) -> TargetContract:
    results = tuple(_copy_mapping(result, field="selection_result") for result in selection_results)
    if not results:
        raise MarketDataGatewayError("market data response requires at least one selection result")
    if expected_selections is not None:
        _validate_selection_result_cardinality(expected_selections, results)
    body = {
        "contract_version": 3,
        "request_id": _text(request_id, field="request_id"),
        "response_id": _text(response_id, field="response_id"),
        "symbol": _symbol(symbol),
        "snapshot_started_at": _timestamp(snapshot_started_at),
        "snapshot_completed_at": _timestamp(snapshot_completed_at),
        "as_of": _timestamp(as_of),
        "source": "exchange_api",
        "selection_results": list(results),
    }
    return _parse({"market_data_response": body}, definition="MARKET_DATA_REQUEST.response")


def market_selection_result(
    *,
    symbol: str,
    selection: MarketDataSelection | Mapping[str, Any],
    page_id: str,
    page_index: int,
    source_snapshot_id: str,
    payload: Mapping[str, Any],
    coverage: Mapping[str, Any],
) -> dict[str, Any]:
    selection_payload = _selection_payload(selection)
    dataset = selection_payload["dataset"]
    payload_copy = _copy_mapping(payload, field="payload")
    if set(payload_copy) != {dataset}:
        raise MarketDataGatewayError("selection result payload must contain exactly the selected dataset key")
    _validate_dataset_payload(dataset, payload_copy[dataset])
    coverage_copy = _copy_mapping(coverage, field="coverage")
    _validate_coverage(coverage_copy, payload_copy[dataset]["status"])
    if not isinstance(page_index, int) or isinstance(page_index, bool) or page_index < 0:
        raise MarketDataGatewayError("page_index must be a nonnegative integer")
    return {
        "selection": selection_payload,
        "selection_digest": market_selection_digest(symbol=symbol, selection=selection_payload),
        "page_id": _text(page_id, field="page_id"),
        "page_index": page_index,
        "source_snapshot_id": _text(source_snapshot_id, field="source_snapshot_id"),
        "payload": payload_copy,
        "coverage": coverage_copy,
    }


def dataset_payload(*, dataset: str, status: str, as_of: datetime | str, source_endpoint: str, data: Any) -> dict[str, Any]:
    dataset = _text(dataset, field="dataset")
    if dataset not in _DATASETS:
        raise MarketDataGatewayError(f"unsupported market dataset: {dataset}")
    status = _text(status, field="status")
    if status not in _STATUSES:
        raise MarketDataGatewayError("status must be AVAILABLE, PARTIAL, or UNAVAILABLE")
    if status == "UNAVAILABLE" and data is not None:
        raise MarketDataGatewayError("UNAVAILABLE market data requires null data")
    if status == "AVAILABLE" and data is None:
        raise MarketDataGatewayError("AVAILABLE market data requires data")
    body: dict[str, Any] = {
        "status": status,
        "as_of": _timestamp(as_of),
        "source_endpoint": _text(source_endpoint, field="source_endpoint"),
        "data": _normalize_data(data),
    }
    if dataset == "QUOTE_TURNOVER":
        body["unit"] = "USDT"
    return {dataset: body}


def coverage(
    *,
    covered_ranges: Sequence[Mapping[str, Any]] = (),
    missing_ranges: Sequence[Mapping[str, Any]] = (),
    coverage_complete: bool,
    pagination_complete: bool,
    next_cursor: str | None,
    expected_page_ids: Sequence[str],
    source_finality_confirmed: bool,
    reason_code: str | None = None,
) -> dict[str, Any]:
    if not all(isinstance(value, bool) for value in (coverage_complete, pagination_complete, source_finality_confirmed)):
        raise MarketDataGatewayError("coverage flags must be boolean")
    return {
        "covered_ranges": [_time_range(item) for item in covered_ranges],
        "missing_ranges": [_time_range(item) for item in missing_ranges],
        "coverage_complete": coverage_complete,
        "pagination_complete": pagination_complete,
        "next_cursor": None if next_cursor is None else _text(next_cursor, field="next_cursor"),
        "expected_page_ids": [_text(page_id, field="expected_page_id") for page_id in expected_page_ids],
        "source_finality_confirmed": source_finality_confirmed,
        "reason_code": None if reason_code is None else _text(reason_code, field="reason_code"),
    }


def _selection_payloads(selections: Sequence[MarketDataSelection | Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not selections:
        raise MarketDataGatewayError("market data request requires at least one selection")
    return [_selection_payload(selection) for selection in selections]


def _selection_payload(selection: MarketDataSelection | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(selection, MarketDataSelection):
        return selection.to_payload()
    payload = _copy_mapping(selection, field="selection")
    return MarketDataSelection(
        selection_id=payload["selection_id"],
        dataset=payload["dataset"],
        mode=payload["mode"],
        as_of=payload["as_of"],
        range_from=payload["range_from"],
        range_to=payload["range_to"],
        completed_only=payload["completed_only"],
        timeframe=payload["timeframe"],
        count=payload["count"],
        cursor=payload["cursor"],
        page_size=payload["page_size"],
    ).to_payload()


def _validate_unique_selection_ids(selections: Sequence[Mapping[str, Any]]) -> None:
    ids = [selection["selection_id"] for selection in selections]
    if len(set(ids)) != len(ids):
        raise MarketDataGatewayError("selection_id values must be unique per request")


def _validate_selection_result_cardinality(
    expected_selections: Sequence[MarketDataSelection | Mapping[str, Any]],
    results: Sequence[Mapping[str, Any]],
) -> None:
    expected = {selection["selection_id"] for selection in _selection_payloads(expected_selections)}
    actual = [result.get("selection", {}).get("selection_id") for result in results]
    if len(set(actual)) != len(actual):
        raise MarketDataGatewayError("selection result cannot repeat a selection_id")
    if set(actual) != expected:
        raise MarketDataGatewayError(f"selection results must exactly cover requested selections: expected={sorted(expected)!r}")


def _validate_dataset_payload(dataset: str, payload: Any) -> None:
    if not isinstance(payload, Mapping):
        raise MarketDataGatewayError("dataset payload must be an object")
    status = payload.get("status")
    if status not in _STATUSES:
        raise MarketDataGatewayError("dataset status must be AVAILABLE, PARTIAL, or UNAVAILABLE")
    data = payload.get("data")
    if status == "UNAVAILABLE" and data is not None:
        raise MarketDataGatewayError("UNAVAILABLE market data requires null data")
    if status == "AVAILABLE" and data is None:
        raise MarketDataGatewayError("AVAILABLE market data requires data")
    if dataset == "QUOTE_TURNOVER" and payload.get("unit") != "USDT":
        raise MarketDataGatewayError("QUOTE_TURNOVER unit must be USDT")


def _validate_coverage(payload: Mapping[str, Any], status: str) -> None:
    if status == "UNAVAILABLE":
        if payload.get("coverage_complete") or payload.get("source_finality_confirmed"):
            raise MarketDataGatewayError("UNAVAILABLE coverage cannot be complete or source-final")
        if not payload.get("reason_code"):
            raise MarketDataGatewayError("UNAVAILABLE coverage requires reason_code")
    if payload.get("pagination_complete") and payload.get("next_cursor") is not None:
        raise MarketDataGatewayError("pagination_complete coverage requires next_cursor=null")
    if payload.get("coverage_complete") and not payload.get("source_finality_confirmed"):
        raise MarketDataGatewayError("complete coverage requires source_finality_confirmed")


def _time_range(value: Mapping[str, Any]) -> dict[str, str]:
    return {"from": _timestamp(value["from"]), "to": _timestamp(value["to"])}


def _normalize_data(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Mapping):
        return {str(key): _normalize_data(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalize_data(item) for item in value]
    if isinstance(value, float):
        raise MarketDataGatewayError("market data decimals must be exact strings, not binary floats")
    return value


def _timestamp(value: datetime | str) -> str:
    if isinstance(value, datetime):
        resolved = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        return resolved.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return _text(value, field="timestamp")


def _symbol(value: str) -> str:
    return _text(value, field="symbol").upper()


def _text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise MarketDataGatewayError(f"{field} is required")
    if "\x00" in value:
        raise MarketDataGatewayError(f"{field} cannot contain NUL")
    return value


def _copy_mapping(value: Mapping[str, Any], *, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise MarketDataGatewayError(f"{field} must be an object")
    return dict(value)


def _parse(payload: Mapping[str, Any], *, definition: str) -> TargetContract:
    try:
        return parse_contract("MARKET_DATA_REQUEST", payload, definition=definition)
    except ContractError as exc:
        raise MarketDataGatewayError(str(exc)) from exc
