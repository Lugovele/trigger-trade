"""Portfolio-owned once-only receipt records for Lifecycle FINAL results."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any

from triggertrade.lifecycle_order_events import LifecycleOrderEventError, validate_order_event

from .postgres import OwnerStateConflict, OwnerStateStore, PostgresPersistenceError


class PortfolioFinalReceiptConflict(PostgresPersistenceError):
    """Raised when a FINAL result receipt identity conflicts."""


@dataclass(frozen=True)
class PortfolioFinalReceiptRecord:
    receipt_id: str
    result_id: str
    tranche_id: str
    accounting_day_id: str
    delivered_at: str
    net_realized_result: str
    currency: str
    payload: dict[str, Any]
    payload_digest: str


class PortfolioFinalReceiptStore:
    """Persist Portfolio's separate first receipt for Lifecycle FINAL results."""

    def __init__(self, connection) -> None:
        self._connection = connection
        self._owner_state = OwnerStateStore(connection)

    def accept_order_event(
        self,
        *,
        order_event_payload: dict[str, Any],
        delivered_at: str,
    ) -> tuple[PortfolioFinalReceiptRecord, bool]:
        try:
            event = validate_order_event(order_event_payload)
        except LifecycleOrderEventError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        body = event.body
        if body.get("lifecycle_state") != "CLOSED":
            raise PortfolioFinalReceiptConflict("Portfolio receipt requires CLOSED order event")
        financial_result = body.get("financial_result")
        if not isinstance(financial_result, dict) or financial_result.get("financial_state") != "FINAL":
            raise PortfolioFinalReceiptConflict("Portfolio receipt requires FINAL financial_result")
        result_id = _text(financial_result.get("result_id"), field="result_id")
        tranche_id = _text(financial_result.get("tranche_id"), field="tranche_id")
        event_tranche_id = _text(body.get("tranche_id"), field="order_event.tranche_id")
        if tranche_id != event_tranche_id:
            raise PortfolioFinalReceiptConflict("FINAL result tranche does not match ORDER_EVENT tranche")
        _validate_result_equation(financial_result)
        _acquire_receipt_locks(self._connection, result_id=result_id, tranche_id=tranche_id)
        existing = self._get_by_result_or_tranche(result_id=result_id, tranche_id=tranche_id)
        payload = {
            "portfolio_final_receipt": {
                "receipt_version": 1,
                "receipt_id": _receipt_id(result_id=result_id, tranche_id=tranche_id),
                "result_id": result_id,
                "tranche_id": tranche_id,
                "order_event_id": _text(body.get("event_id"), field="order_event_id"),
                "order_event_digest": event.payload_digest,
                "accounting_day_id": _text(financial_result.get("accounting_day_id"), field="accounting_day_id"),
                "delivered_at": _text(delivered_at, field="delivered_at"),
                "accounting_effective_at": _text(
                    financial_result.get("accounting_effective_at"),
                    field="accounting_effective_at",
                ),
                "net_realized_result": _text(
                    financial_result.get("net_realized_result"),
                    field="net_realized_result",
                ),
                "currency": _text(financial_result.get("currency"), field="currency"),
                "terminalized_at": _text(financial_result.get("terminalized_at"), field="terminalized_at"),
            }
        }
        if existing is not None:
            if _same_receipt_except_delivery(existing.payload, payload):
                return existing, False
            raise PortfolioFinalReceiptConflict("Portfolio FINAL receipt already exists with different content")
        try:
            state, inserted = self._owner_state.put_if_absent(
                owner="Portfolio",
                state_type="portfolio_final_receipt",
                state_id=payload["portfolio_final_receipt"]["receipt_id"],
                payload=payload,
            )
        except OwnerStateConflict as exc:
            raise PortfolioFinalReceiptConflict("Portfolio FINAL receipt already exists with different content") from exc
        return _record_from_state(state.payload, state.payload_digest), inserted

    def get_by_result_id(self, *, result_id: str) -> PortfolioFinalReceiptRecord | None:
        return self._get("result_id", _text(result_id, field="result_id"))

    def get_by_tranche_id(self, *, tranche_id: str) -> PortfolioFinalReceiptRecord | None:
        return self._get("tranche_id", _text(tranche_id, field="tranche_id"))

    def _get_by_result_or_tranche(
        self,
        *,
        result_id: str,
        tranche_id: str,
    ) -> PortfolioFinalReceiptRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                _SELECT_RECEIPT
                + """
                  AND (
                    payload_json -> 'portfolio_final_receipt' ->> 'result_id' = %s
                   OR payload_json -> 'portfolio_final_receipt' ->> 'tranche_id' = %s
                  )
                ORDER BY state_id
                LIMIT 1
                """,
                (result_id, tranche_id),
            )
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def _get(self, field: str, value: str) -> PortfolioFinalReceiptRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                _SELECT_RECEIPT
                + f"""
                  AND payload_json -> 'portfolio_final_receipt' ->> '{field}' = %s
                ORDER BY state_id
                LIMIT 1
                """,
                (value,),
            )
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)


_SELECT_RECEIPT = """
SELECT state_id, payload_json::text, payload_digest
FROM triggertrade_owner_state_records
WHERE owner = 'Portfolio'
  AND state_type = 'portfolio_final_receipt'
"""


def _acquire_receipt_locks(connection, *, result_id: str, tranche_id: str) -> None:
    lock_keys = sorted(
        {
            _advisory_key(f"portfolio-final-receipt:result:{result_id}"),
            _advisory_key(f"portfolio-final-receipt:tranche:{tranche_id}"),
        }
    )
    with connection.cursor() as cursor:
        for key in lock_keys:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", (key,))


def _advisory_key(value: str) -> int:
    raw = sha256(value.encode("utf-8")).digest()[:8]
    return int.from_bytes(raw, "big", signed=True)


def _receipt_id(*, result_id: str, tranche_id: str) -> str:
    source = f"{_text(result_id, field='result_id')}\x1f{_text(tranche_id, field='tranche_id')}"
    return f"portfolio-final-receipt-{sha256(source.encode('utf-8')).hexdigest()}"


def _record_from_row(row: tuple[Any, ...]) -> PortfolioFinalReceiptRecord:
    return _record_from_state(json.loads(str(row[1]), parse_float=Decimal), str(row[2]))


def _record_from_state(payload: dict[str, Any], payload_digest: str) -> PortfolioFinalReceiptRecord:
    body = payload["portfolio_final_receipt"]
    return PortfolioFinalReceiptRecord(
        receipt_id=str(body["receipt_id"]),
        result_id=str(body["result_id"]),
        tranche_id=str(body["tranche_id"]),
        accounting_day_id=str(body["accounting_day_id"]),
        delivered_at=str(body["delivered_at"]),
        net_realized_result=str(body["net_realized_result"]),
        currency=str(body["currency"]),
        payload=payload,
        payload_digest=payload_digest,
    )


def _same_receipt_except_delivery(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_body = dict(left["portfolio_final_receipt"])
    right_body = dict(right["portfolio_final_receipt"])
    left_body.pop("delivered_at", None)
    right_body.pop("delivered_at", None)
    return left_body == right_body


def _validate_result_equation(financial_result: dict[str, Any]) -> None:
    gross = _decimal(financial_result.get("gross_realized_trading_result"), field="gross_realized_trading_result")
    fees = _decimal(financial_result.get("actual_fees_rebates"), field="actual_fees_rebates")
    funding = _decimal(financial_result.get("allocated_funding"), field="allocated_funding")
    other_costs = _decimal(
        financial_result.get("other_supported_exchange_costs"),
        field="other_supported_exchange_costs",
    )
    net = _decimal(financial_result.get("net_realized_result"), field="net_realized_result")
    if not _decimal_equation_balances(left=net, right_terms=(gross, -fees, funding, -other_costs)):
        raise PortfolioFinalReceiptConflict("FINAL result net equation does not balance")


def _decimal(value: object, *, field: str) -> Decimal:
    try:
        return Decimal(_text(value, field=field))
    except InvalidOperation as exc:
        raise PortfolioFinalReceiptConflict(f"{field} must be exact decimal text") from exc


def _decimal_equation_balances(*, left: Decimal, right_terms: tuple[Decimal, ...]) -> bool:
    decimals = (left, *right_terms)
    scale = max(-value.as_tuple().exponent for value in decimals)
    left_int = _scaled_decimal_int(left, scale=scale)
    right_int = sum(_scaled_decimal_int(value, scale=scale) for value in right_terms)
    return left_int == right_int


def _scaled_decimal_int(value: Decimal, *, scale: int) -> int:
    sign, digits, exponent = value.as_tuple()
    integer = 0
    for digit in digits:
        integer = integer * 10 + digit
    places = scale + exponent
    if places < 0:
        raise PortfolioFinalReceiptConflict("FINAL result decimal scale is inconsistent")
    integer *= 10**places
    return -integer if sign else integer


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PostgresPersistenceError(f"{field} is required")
    return value
