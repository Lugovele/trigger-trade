"""PostgreSQL persistence for Portfolio ACCOUNTING_DAY_V1 state."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text
from triggertrade.portfolio_accounting_day import (
    PortfolioAccountingDay,
    PortfolioAccountingDayError,
    apply_final_result_to_day,
    latch_daily_loss,
    record_live_metrics,
)

from .postgres import PostgresPersistenceError


class PortfolioAccountingDayConflict(PostgresPersistenceError):
    """Raised when accounting-day evidence is replayed with different content."""


@dataclass(frozen=True)
class PortfolioAccountingDayRecord:
    day: PortfolioAccountingDay
    base_identity_digest: str
    payload_digest: str


@dataclass(frozen=True)
class PortfolioDayResultRecord:
    result_id: str
    tranche_id: str
    portfolio_id: str
    accounting_day_id: str
    realized_pnl: str
    payload: dict[str, Any]
    payload_digest: str


class PortfolioAccountingDayStore:
    """Persist immutable day/base state and exactly-once Portfolio result postings."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def record_day(self, day: PortfolioAccountingDay) -> tuple[PortfolioAccountingDayRecord, bool]:
        payload = day.to_payload()
        base_identity = _base_identity(day)
        base_identity_text = canonical_json_text(base_identity)
        base_identity_digest = canonical_json_digest(base_identity)
        payload_text = canonical_json_text(payload)
        digest = canonical_json_digest(payload)
        existing = self.get_day(portfolio_id=day.portfolio_id, accounting_day_id=day.accounting_day_id, for_update=True)
        if existing is not None:
            if existing.base_identity_digest != base_identity_digest:
                raise PortfolioAccountingDayConflict("accounting day already exists with different content")
            return existing, False
        body = payload["portfolio_accounting_day"]
        evidence = body["base_evidence"]
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_portfolio_accounting_days (
                    portfolio_id, accounting_day_id, boundary_start_at, boundary_end_at,
                    rollover_state, daily_portfolio_base, base_evidence_id, base_evidence_source,
                    base_evidence_json, base_identity_json, base_identity_digest,
                    current_portfolio_equity, daily_realized_pnl,
                    unrealized_pnl, total_pnl, external_capital_flow_amount,
                    daily_loss_latched, daily_loss_latched_at, daily_loss_reason,
                    payload_json, payload_digest
                ) VALUES (
                    %s, %s, %s::timestamptz, %s::timestamptz,
                    %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s::timestamptz, %s,
                    %s::jsonb, %s
                )
                ON CONFLICT DO NOTHING
                RETURNING portfolio_id, accounting_day_id, payload_json::text, base_identity_digest, payload_digest
                """,
                (
                    body["portfolio_id"],
                    body["accounting_day_id"],
                    body["boundary_start_at"],
                    body["boundary_end_at"],
                    body["rollover_state"],
                    body["daily_portfolio_base"],
                    None if evidence is None else evidence["evidence_id"],
                    None if evidence is None else evidence["source"],
                    None if evidence is None else canonical_json_text(evidence),
                    base_identity_text,
                    base_identity_digest,
                    body["current_portfolio_equity"],
                    body["daily_realized_pnl"],
                    body["unrealized_pnl"],
                    body["total_pnl"],
                    body["external_capital_flow_amount"],
                    body["daily_loss_latched"],
                    body["daily_loss_latched_at"],
                    body["daily_loss_reason"],
                    payload_text,
                    digest,
                ),
            )
            row = cursor.fetchone()
        if row is not None:
            return _day_record_from_row(row), True
        replayed = self.get_day(portfolio_id=day.portfolio_id, accounting_day_id=day.accounting_day_id)
        if replayed is None:
            raise PostgresPersistenceError("accounting day insert conflicted but no record was found")
        if replayed.base_identity_digest != base_identity_digest:
            raise PortfolioAccountingDayConflict("accounting day already exists with different content")
        return replayed, False

    def update_live_metrics(
        self,
        *,
        portfolio_id: str,
        accounting_day_id: str,
        current_portfolio_equity: str,
        unrealized_pnl: str,
        external_capital_flow_amount: str | None = None,
    ) -> PortfolioAccountingDayRecord:
        current = self.get_day(portfolio_id=portfolio_id, accounting_day_id=accounting_day_id, for_update=True)
        if current is None:
            raise PostgresPersistenceError("accounting day does not exist")
        try:
            updated = record_live_metrics(
                current.day,
                current_portfolio_equity=current_portfolio_equity,
                unrealized_pnl=unrealized_pnl,
                external_capital_flow_amount=external_capital_flow_amount,
            )
        except PortfolioAccountingDayError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        return self._update_day(updated)

    def post_final_result_once(
        self,
        *,
        portfolio_id: str,
        accounting_day_id: str,
        result_id: str,
        tranche_id: str,
        realized_pnl: str,
        delivered_at: str,
    ) -> tuple[PortfolioDayResultRecord, bool, PortfolioAccountingDayRecord]:
        current = self.get_day(portfolio_id=portfolio_id, accounting_day_id=accounting_day_id, for_update=True)
        if current is None:
            raise PostgresPersistenceError("accounting day does not exist")
        payload = {
            "portfolio_day_result": {
                "result_id": result_id,
                "tranche_id": tranche_id,
                "portfolio_id": portfolio_id,
                "accounting_day_id": accounting_day_id,
                "realized_pnl": realized_pnl,
                "delivered_at": delivered_at,
            }
        }
        payload_text = canonical_json_text(payload)
        digest = canonical_json_digest(payload)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_portfolio_accounting_day_results (
                    result_id, tranche_id, portfolio_id, accounting_day_id,
                    realized_pnl, delivered_at, payload_json, payload_digest
                ) VALUES (%s, %s, %s, %s, %s, %s::timestamptz, %s::jsonb, %s)
                ON CONFLICT DO NOTHING
                RETURNING result_id, tranche_id, portfolio_id, accounting_day_id,
                    realized_pnl, payload_json::text, payload_digest
                """,
                (result_id, tranche_id, portfolio_id, accounting_day_id, realized_pnl, delivered_at, payload_text, digest),
            )
            row = cursor.fetchone()
        if row is None:
            existing = self.get_result(result_id=result_id)
            if existing is None:
                existing = self.get_result_by_tranche(tranche_id=tranche_id)
            if existing is None:
                raise PostgresPersistenceError("portfolio day result conflicted but no record was found")
            if existing.payload_digest != digest:
                raise PortfolioAccountingDayConflict("portfolio day result already exists with different content")
            return existing, False, current
        try:
            updated_day = apply_final_result_to_day(
                current.day,
                realized_pnl=realized_pnl,
                result_id=result_id,
                tranche_id=tranche_id,
            )
        except PortfolioAccountingDayError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        updated_record = self._update_day(updated_day)
        return _result_record_from_row(row), True, updated_record

    def latch_daily_loss_once(
        self,
        *,
        portfolio_id: str,
        accounting_day_id: str,
        latched_at: str,
        reason_code: str = "DAILY_LOSS_LIMIT_REACHED",
    ) -> PortfolioAccountingDayRecord:
        current = self.get_day(portfolio_id=portfolio_id, accounting_day_id=accounting_day_id, for_update=True)
        if current is None:
            raise PostgresPersistenceError("accounting day does not exist")
        try:
            updated = latch_daily_loss(current.day, latched_at=latched_at, reason_code=reason_code)
        except PortfolioAccountingDayError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        if updated == current.day:
            return current
        return self._update_day(updated)

    def get_day(self, *, portfolio_id: str, accounting_day_id: str, for_update: bool = False) -> PortfolioAccountingDayRecord | None:
        suffix = " FOR UPDATE" if for_update else ""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT portfolio_id, accounting_day_id, payload_json::text, base_identity_digest, payload_digest
                FROM triggertrade_portfolio_accounting_days
                WHERE portfolio_id = %s AND accounting_day_id = %s
                """ + suffix,
                (portfolio_id, accounting_day_id),
            )
            row = cursor.fetchone()
        return None if row is None else _day_record_from_row(row)

    def get_result(self, *, result_id: str) -> PortfolioDayResultRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_RESULT + " WHERE result_id = %s", (result_id,))
            row = cursor.fetchone()
        return None if row is None else _result_record_from_row(row)

    def get_result_by_tranche(self, *, tranche_id: str) -> PortfolioDayResultRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_RESULT + " WHERE tranche_id = %s", (tranche_id,))
            row = cursor.fetchone()
        return None if row is None else _result_record_from_row(row)

    def _update_day(self, day: PortfolioAccountingDay) -> PortfolioAccountingDayRecord:
        payload = day.to_payload()
        body = payload["portfolio_accounting_day"]
        payload_text = canonical_json_text(payload)
        digest = canonical_json_digest(payload)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE triggertrade_portfolio_accounting_days
                SET current_portfolio_equity = %s,
                    daily_realized_pnl = %s,
                    unrealized_pnl = %s,
                    total_pnl = %s,
                    external_capital_flow_amount = %s,
                    daily_loss_latched = %s,
                    daily_loss_latched_at = %s::timestamptz,
                    daily_loss_reason = %s,
                    payload_json = %s::jsonb,
                    payload_digest = %s,
                    updated_at = now()
                WHERE portfolio_id = %s AND accounting_day_id = %s
                RETURNING portfolio_id, accounting_day_id, payload_json::text, base_identity_digest, payload_digest
                """,
                (
                    body["current_portfolio_equity"],
                    body["daily_realized_pnl"],
                    body["unrealized_pnl"],
                    body["total_pnl"],
                    body["external_capital_flow_amount"],
                    body["daily_loss_latched"],
                    body["daily_loss_latched_at"],
                    body["daily_loss_reason"],
                    payload_text,
                    digest,
                    body["portfolio_id"],
                    body["accounting_day_id"],
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise PostgresPersistenceError("accounting day update failed")
        return _day_record_from_row(row)


_SELECT_RESULT = """
SELECT result_id, tranche_id, portfolio_id, accounting_day_id, realized_pnl, payload_json::text, payload_digest
FROM triggertrade_portfolio_accounting_day_results
"""


def _day_record_from_row(row: tuple[Any, ...]) -> PortfolioAccountingDayRecord:
    payload = json.loads(str(row[2]), parse_float=Decimal)
    return PortfolioAccountingDayRecord(
        day=PortfolioAccountingDay.from_payload(payload),
        base_identity_digest=str(row[3]),
        payload_digest=str(row[4]),
    )


def _base_identity(day: PortfolioAccountingDay) -> dict[str, Any]:
    body = day.to_payload()["portfolio_accounting_day"]
    return {
        "portfolio_accounting_day_base": {
            "policy_version": body["policy_version"],
            "timezone": body["timezone"],
            "portfolio_id": body["portfolio_id"],
            "accounting_day_id": body["accounting_day_id"],
            "boundary_start_at": body["boundary_start_at"],
            "boundary_end_at": body["boundary_end_at"],
            "rollover_state": body["rollover_state"],
            "daily_portfolio_base": body["daily_portfolio_base"],
            "base_evidence": body["base_evidence"],
        }
    }


def _result_record_from_row(row: tuple[Any, ...]) -> PortfolioDayResultRecord:
    payload = json.loads(str(row[5]), parse_float=Decimal)
    return PortfolioDayResultRecord(
        result_id=str(row[0]),
        tranche_id=str(row[1]),
        portfolio_id=str(row[2]),
        accounting_day_id=str(row[3]),
        realized_pnl=str(row[4]),
        payload=payload,
        payload_digest=str(row[6]),
    )
