"""PostgreSQL-backed Portfolio Rules state revision store."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text
from triggertrade.portfolio_state import PortfolioState

from .postgres import OwnerStateRevisionConflict, PostgresPersistenceError


class PortfolioStateConflict(PostgresPersistenceError):
    """Raised when Portfolio state evidence is replayed with different content."""


@dataclass(frozen=True)
class PortfolioStateRecord:
    state: PortfolioState
    payload_digest: str


class PortfolioStateStore:
    """Persist Portfolio state revisions and current pointer transactionally."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def record(self, *, state: PortfolioState, evidence_kind: str) -> tuple[PortfolioStateRecord, bool]:
        if not isinstance(evidence_kind, str) or not evidence_kind:
            raise PostgresPersistenceError("evidence_kind is required")
        if not state.evidence_id:
            raise PostgresPersistenceError("Portfolio state revision requires evidence_id")
        payload = state.to_payload()
        payload_text = canonical_json_text(payload)
        digest = canonical_json_digest(payload)
        existing = self.get_by_evidence(portfolio_id=state.portfolio_id, evidence_id=state.evidence_id)
        if existing is not None:
            if existing.payload_digest != digest:
                raise PortfolioStateConflict("portfolio state evidence already exists with different content")
            return existing, False
        current = self.get_current(portfolio_id=state.portfolio_id, for_update=True)
        if current is not None and state.revision <= current.state.revision:
            raise OwnerStateRevisionConflict("portfolio state revision must advance current revision")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_portfolio_state_revisions (
                    portfolio_id, revision, evidence_id, evidence_kind, health, as_of, payload_json, payload_digest
                ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (portfolio_id, evidence_id) DO NOTHING
                RETURNING portfolio_id, revision, health, as_of, payload_json::text, payload_digest
                """,
                (
                    state.portfolio_id,
                    state.revision,
                    state.evidence_id,
                    evidence_kind,
                    state.health.value,
                    state.as_of,
                    payload_text,
                    digest,
                ),
            )
            row = cursor.fetchone()
            if row is None:
                replayed = self.get_by_evidence(portfolio_id=state.portfolio_id, evidence_id=state.evidence_id)
                if replayed is None:
                    raise PostgresPersistenceError("portfolio state evidence conflicted but no record was found")
                if replayed.payload_digest != digest:
                    raise PortfolioStateConflict("portfolio state evidence already exists with different content")
                return replayed, False
            cursor.execute(
                """
                INSERT INTO triggertrade_portfolio_state_current (
                    portfolio_id, revision, health, as_of, payload_json, payload_digest
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (portfolio_id) DO UPDATE
                SET revision = EXCLUDED.revision,
                    health = EXCLUDED.health,
                    as_of = EXCLUDED.as_of,
                    payload_json = EXCLUDED.payload_json,
                    payload_digest = EXCLUDED.payload_digest,
                    updated_at = now()
                WHERE triggertrade_portfolio_state_current.revision < EXCLUDED.revision
                """,
                (state.portfolio_id, state.revision, state.health.value, state.as_of, payload_text, digest),
            )
        return _record_from_row(row), True

    def get_current(self, *, portfolio_id: str, for_update: bool = False) -> PortfolioStateRecord | None:
        suffix = " FOR UPDATE" if for_update else ""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT portfolio_id, revision, health, as_of, payload_json::text, payload_digest
                FROM triggertrade_portfolio_state_current
                WHERE portfolio_id = %s
                """ + suffix,
                (portfolio_id,),
            )
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def get_by_evidence(self, *, portfolio_id: str, evidence_id: str) -> PortfolioStateRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT portfolio_id, revision, health, as_of, payload_json::text, payload_digest
                FROM triggertrade_portfolio_state_revisions
                WHERE portfolio_id = %s AND evidence_id = %s
                """,
                (portfolio_id, evidence_id),
            )
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)


def _record_from_row(row: tuple[Any, ...]) -> PortfolioStateRecord:
    payload = json.loads(str(row[4]), parse_float=Decimal)
    return PortfolioStateRecord(
        state=PortfolioState.from_payload(payload),
        payload_digest=str(row[5]),
    )
