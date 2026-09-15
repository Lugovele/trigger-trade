"""Portfolio Data Request v5 factual envelope builders."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from triggertrade.contracts import ContractError, TargetContract, parse_contract


class PortfolioDataGatewayError(ValueError):
    """Raised when factual Portfolio API data cannot form an approved envelope."""


_SCOPE_FIELDS = (
    "account",
    "wallet",
    "positions",
    "open_orders",
    "recent_orders",
    "executions",
    "fees",
    "funding",
    "realized_pnl",
    "unrealized_pnl",
    "instrument_metadata",
    "fee_rates",
    "cashflows",
)


@dataclass(frozen=True)
class _SymbolCoverage:
    requested: tuple[str, ...]
    actual: tuple[str, ...]


def build_portfolio_data_request(
    *,
    request_id: str,
    requested_at: datetime | str,
    request_mode: str = "SNAPSHOT",
    scope: Mapping[str, bool] | None = None,
    symbols: Sequence[str] = (),
    since: datetime | str | None = None,
    until: datetime | str | None = None,
) -> TargetContract:
    resolved_scope = _scope(scope)
    normalized_symbols = _symbols(symbols)
    if (resolved_scope["instrument_metadata"] or resolved_scope["fee_rates"]) and not normalized_symbols:
        raise PortfolioDataGatewayError("instrument_metadata and fee_rates requests require explicit symbols")
    payload = {
        "portfolio_data_request": {
            "contract_version": 5,
            "request_id": _text(request_id, field="request_id"),
            "requested_at": _timestamp(requested_at),
            "request_mode": request_mode,
            "scope": resolved_scope,
            "filters": {
                "symbols": list(normalized_symbols),
                "since": None if since is None else _timestamp(since),
                "until": None if until is None else _timestamp(until),
            },
        }
    }
    return _parse(payload, definition="PORTFOLIO_DATA_REQUEST.request")


def build_portfolio_data_response(
    *,
    request_id: str,
    response_id: str,
    request_mode: str,
    snapshot_started_at: datetime | str,
    snapshot_completed_at: datetime | str,
    as_of: datetime | str,
    response_consistency: str = "COMPOSITE",
    account: Mapping[str, Any] | None = None,
    positions: Mapping[str, Any] | None = None,
    instrument_metadata: Mapping[str, Any] | None = None,
    fee_rates: Mapping[str, Any] | None = None,
    requested_symbols: Sequence[str] = (),
) -> TargetContract:
    body: dict[str, Any] = {
        "contract_version": 5,
        "request_id": _text(request_id, field="request_id"),
        "response_id": _text(response_id, field="response_id"),
        "request_mode": request_mode,
        "response_consistency": {"mode": response_consistency},
        "snapshot_started_at": _timestamp(snapshot_started_at),
        "snapshot_completed_at": _timestamp(snapshot_completed_at),
        "as_of": _timestamp(as_of),
        "source": "exchange_api",
    }
    if account is not None:
        body["account"] = _copy_section(account, field="account")
    if positions is not None:
        body["positions"] = _copy_section(positions, field="positions")
    if instrument_metadata is not None:
        _validate_symbol_section(
            "instrument_metadata",
            requested_symbols=requested_symbols,
            section_payload=instrument_metadata,
        )
        body["instrument_metadata"] = _copy_section(instrument_metadata, field="instrument_metadata")
    if fee_rates is not None:
        _validate_symbol_section(
            "fee_rates",
            requested_symbols=requested_symbols,
            section_payload=fee_rates,
        )
        body["fee_rates"] = _copy_section(fee_rates, field="fee_rates")
    payload = {"portfolio_data_response": body}
    return _parse(payload, definition="PORTFOLIO_DATA_REQUEST.response")


def portfolio_account_section(
    *,
    status: str,
    as_of: datetime | str,
    source_endpoint: str,
    account_id: str,
    equity: Decimal | str | int | None,
    wallet_balance: Decimal | str | int | None,
    available_balance: Decimal | str | int | None,
    unrealized_pnl: Decimal | str | int | None,
    realized_pnl: Decimal | str | int | None,
) -> dict[str, Any]:
    return {
        "status": status,
        "as_of": _timestamp(as_of),
        "source_endpoint": _text(source_endpoint, field="source_endpoint"),
        "account_id": _text(account_id, field="account_id"),
        "equity": _decimal_or_none(equity, field="equity"),
        "wallet_balance": _decimal_or_none(wallet_balance, field="wallet_balance"),
        "available_balance": _decimal_or_none(available_balance, field="available_balance"),
        "unrealized_pnl": _decimal_or_none(unrealized_pnl, field="unrealized_pnl"),
        "realized_pnl": _decimal_or_none(realized_pnl, field="realized_pnl"),
    }


def portfolio_position_item(
    *,
    symbol: str,
    side: str,
    position_idx: int,
    size: Decimal | str | int,
    avg_entry_price: Decimal | str | int,
    mark_price: Decimal | str | int,
    position_value: Decimal | str | int,
    unrealized_pnl: Decimal | str | int,
    realized_pnl: Decimal | str | int,
) -> dict[str, Any]:
    return {
        "symbol": _symbol(symbol),
        "side": side,
        "position_idx": position_idx,
        "size": _decimal_text(size, field="size", signed=False),
        "avg_entry_price": _decimal_text(avg_entry_price, field="avg_entry_price", signed=False),
        "mark_price": _decimal_text(mark_price, field="mark_price", signed=False),
        "position_value": _decimal_text(position_value, field="position_value", signed=True),
        "unrealized_pnl": _decimal_text(unrealized_pnl, field="unrealized_pnl", signed=True),
        "realized_pnl": _decimal_text(realized_pnl, field="realized_pnl", signed=True),
    }


def instrument_metadata_item(
    *,
    symbol: str,
    status: str,
    as_of: datetime | str,
    source_endpoint: str,
    source_record_id: str,
    facts: Mapping[str, Any] | None,
    reason_code: str | None,
) -> dict[str, Any]:
    return {
        "symbol": _symbol(symbol),
        "status": status,
        "facts": None if facts is None else _copy_section(facts, field="facts"),
        "as_of": _timestamp(as_of),
        "source_endpoint": _text(source_endpoint, field="source_endpoint"),
        "source_record_id": _text(source_record_id, field="source_record_id"),
        "reason_code": None if reason_code is None else _text(reason_code, field="reason_code"),
    }


def fee_rate_item(
    *,
    symbol: str,
    status: str,
    as_of: datetime | str,
    source_endpoint: str,
    source_record_id: str,
    facts: Mapping[str, Any] | None,
    reason_code: str | None,
) -> dict[str, Any]:
    return {
        "symbol": _symbol(symbol),
        "status": status,
        "facts": None if facts is None else _copy_section(facts, field="facts"),
        "as_of": _timestamp(as_of),
        "source_endpoint": _text(source_endpoint, field="source_endpoint"),
        "source_record_id": _text(source_record_id, field="source_record_id"),
        "reason_code": None if reason_code is None else _text(reason_code, field="reason_code"),
    }


def _scope(scope: Mapping[str, bool] | None) -> dict[str, bool]:
    values = {field: False for field in _SCOPE_FIELDS}
    if scope is None:
        return values
    unknown = set(scope) - set(_SCOPE_FIELDS)
    if unknown:
        raise PortfolioDataGatewayError(f"unknown portfolio data scope fields: {', '.join(sorted(unknown))}")
    for field, value in scope.items():
        if not isinstance(value, bool):
            raise PortfolioDataGatewayError(f"scope.{field} must be a boolean")
        values[field] = value
    return values


def _validate_symbol_section(
    section: str,
    *,
    requested_symbols: Sequence[str],
    section_payload: Mapping[str, Any],
) -> None:
    if not isinstance(section_payload, Mapping):
        raise PortfolioDataGatewayError(f"{section} must be an object")
    items = section_payload.get("items", ())
    coverage = _SymbolCoverage(requested=_symbols(requested_symbols), actual=_symbols(_item_symbols(items)))
    if not coverage.requested:
        raise PortfolioDataGatewayError(f"{section} requires requested symbols")
    if coverage.actual != coverage.requested:
        raise PortfolioDataGatewayError(
            f"{section} items must exactly cover requested symbols: requested={coverage.requested!r} actual={coverage.actual!r}"
        )
    item_statuses = tuple(_validate_symbol_fact_item(section, item) for item in items)
    expected_section_status = _aggregate_status(item_statuses)
    if section_payload.get("status") != expected_section_status:
        raise PortfolioDataGatewayError(
            f"{section}.status must be {expected_section_status} for item statuses {item_statuses!r}"
        )


def _validate_symbol_fact_item(section: str, item: Mapping[str, Any]) -> str:
    status = item.get("status")
    if status not in {"AVAILABLE", "UNAVAILABLE"}:
        raise PortfolioDataGatewayError(f"{section} item status must be AVAILABLE or UNAVAILABLE")
    facts = item.get("facts")
    reason_code = item.get("reason_code")
    if status == "AVAILABLE":
        if not isinstance(facts, Mapping):
            raise PortfolioDataGatewayError(f"{section} AVAILABLE item requires facts")
        if reason_code is not None:
            raise PortfolioDataGatewayError(f"{section} AVAILABLE item reason_code must be null")
        if facts.get("as_of") != item.get("as_of"):
            raise PortfolioDataGatewayError(f"{section} AVAILABLE item facts.as_of must equal item as_of")
    if status == "UNAVAILABLE":
        if facts is not None:
            raise PortfolioDataGatewayError(f"{section} UNAVAILABLE item facts must be null")
        if not isinstance(reason_code, str) or not reason_code:
            raise PortfolioDataGatewayError(f"{section} UNAVAILABLE item requires reason_code")
    return str(status)


def _aggregate_status(item_statuses: tuple[str, ...]) -> str:
    unique = set(item_statuses)
    if unique == {"AVAILABLE"}:
        return "AVAILABLE"
    if unique == {"UNAVAILABLE"}:
        return "UNAVAILABLE"
    return "PARTIAL"


def _item_symbols(items: Any) -> tuple[str, ...]:
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise PortfolioDataGatewayError("symbol section items must be an array")
    symbols: list[str] = []
    for item in items:
        if not isinstance(item, Mapping):
            raise PortfolioDataGatewayError("symbol section items must be objects")
        symbols.append(str(item.get("symbol") or ""))
    return tuple(symbols)


def _symbols(symbols: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(_symbol(symbol) for symbol in symbols)
    if len(set(normalized)) != len(normalized):
        raise PortfolioDataGatewayError("symbols must be unique")
    return normalized


def _symbol(value: str) -> str:
    return _text(value, field="symbol").upper()


def _timestamp(value: datetime | str) -> str:
    if isinstance(value, datetime):
        resolved = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        return resolved.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return _text(value, field="timestamp")


def _decimal_or_none(value: Decimal | str | int | None, *, field: str) -> str | None:
    if value is None:
        return None
    return _decimal_text(value, field=field, signed=True)


def _decimal_text(value: Decimal | str | int, *, field: str, signed: bool) -> str:
    if isinstance(value, bool):
        raise PortfolioDataGatewayError(f"{field} must be an exact decimal value")
    if isinstance(value, Decimal):
        text = format(value, "f")
    elif isinstance(value, int):
        text = str(value)
    elif isinstance(value, str):
        text = value
    else:
        raise PortfolioDataGatewayError(f"{field} must be an exact decimal string")
    if not text:
        raise PortfolioDataGatewayError(f"{field} is required")
    if not signed and text.startswith("-"):
        raise PortfolioDataGatewayError(f"{field} must be nonnegative")
    return text


def _text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise PortfolioDataGatewayError(f"{field} is required")
    if "\x00" in value:
        raise PortfolioDataGatewayError(f"{field} cannot contain NUL")
    return value


def _copy_section(value: Mapping[str, Any], *, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise PortfolioDataGatewayError(f"{field} must be an object")
    return dict(value)


def _parse(payload: Mapping[str, Any], *, definition: str) -> TargetContract:
    try:
        return parse_contract("PORTFOLIO_DATA_REQUEST", payload, definition=definition)
    except ContractError as exc:
        raise PortfolioDataGatewayError(str(exc)) from exc
