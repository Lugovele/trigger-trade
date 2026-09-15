"""PostgreSQL native observation and reconciliation evidence ledger."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_text
from triggertrade.lifecycle_reconciliation import (
    LifecycleReconciliationEvidence,
    validate_reconciliation_event,
)

from .postgres import PostgresPersistenceError


class LifecycleReconciliationConflict(PostgresPersistenceError):
    """Raised when reconciliation evidence replays with different content."""


@dataclass(frozen=True)
class LifecycleReconciliationRecord:
    evidence_id: str
    evidence_kind: str
    native_observation_id: str
    native_scope_revision: int
    revision_id: str
    evidence_revision: int
    native_scope: dict[str, Any]
    payload: dict[str, Any]
    payload_digest: str
    complete: bool
    accepted: bool
    integrity_state: str
    occurred_at: str


@dataclass(frozen=True)
class LifecycleObservationTombstone:
    native_observation_id: str
    native_scope_revision: int
    native_scope: dict[str, Any]
    state: str
    latest_revision_id: str | None
    latest_evidence_revision: int | None
    complete_payload_digest: str | None
    unresolved_block_active: bool
    integrity_state: str


@dataclass(frozen=True)
class LifecycleReconciliationApplyResult:
    record: LifecycleReconciliationRecord
    tombstone: LifecycleObservationTombstone
    inserted: bool
    replayed: bool
    stale: bool
    resolved: bool


class LifecycleReconciliationStore:
    """Durable P9/P15 evidence ledger with per-observation replay state."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def record_event(self, payload: dict[str, Any]) -> LifecycleReconciliationApplyResult:
        evidence = validate_reconciliation_event(payload)
        with self._connection.cursor() as cursor:
            existing = self._get_record(cursor, evidence_id=evidence.evidence_id)
            if existing is not None:
                if existing.payload_digest != evidence.payload_digest:
                    self._mark_integrity_conflict(cursor, native_observation_id=existing.native_observation_id)
                    raise LifecycleReconciliationConflict("reconciliation evidence identity already exists with different content")
                tombstone = self._get_or_create_tombstone(cursor, evidence=evidence)
                return LifecycleReconciliationApplyResult(
                    record=existing,
                    tombstone=tombstone,
                    inserted=False,
                    replayed=True,
                    stale=False,
                    resolved=tombstone.state == "RESOLVED",
                )

            tombstone = self._get_or_create_tombstone(cursor, evidence=evidence)
            accepted, stale = self._classify_revision(cursor, evidence=evidence, tombstone=tombstone)
            record = self._insert_record(cursor, evidence=evidence, accepted=accepted)
            if accepted:
                tombstone = self._advance_tombstone(cursor, evidence=evidence, previous=tombstone)
            return LifecycleReconciliationApplyResult(
                record=record,
                tombstone=tombstone,
                inserted=True,
                replayed=False,
                stale=stale,
                resolved=tombstone.state == "RESOLVED",
            )

    def get_tombstone(self, *, native_observation_id: str) -> LifecycleObservationTombstone | None:
        with self._connection.cursor() as cursor:
            return self._get_tombstone(cursor, native_observation_id=_text(native_observation_id, field="native_observation_id"))

    def list_records(self, *, native_observation_id: str) -> tuple[LifecycleReconciliationRecord, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                _SELECT_RECORD
                + """
                WHERE native_observation_id = %s
                ORDER BY evidence_revision, evidence_id
                """,
                (_text(native_observation_id, field="native_observation_id"),),
            )
            rows = cursor.fetchall()
        return tuple(_record_from_row(row) for row in rows)

    def _classify_revision(
        self,
        cursor,
        *,
        evidence: LifecycleReconciliationEvidence,
        tombstone: LifecycleObservationTombstone,
    ) -> tuple[bool, bool]:
        cursor.execute(
            """
            SELECT payload_digest
            FROM triggertrade_lifecycle_reconciliation_records
            WHERE native_observation_id = %s
              AND revision_id = %s
              AND evidence_revision = %s
            """,
            (evidence.native_observation_id, evidence.revision_id, evidence.evidence_revision),
        )
        same_revision = cursor.fetchall()
        if same_revision and all(str(row[0]) != evidence.payload_digest for row in same_revision):
            self._mark_integrity_conflict(cursor, native_observation_id=evidence.native_observation_id)
            raise LifecycleReconciliationConflict("reconciliation revision already exists with different content")
        if tombstone.latest_evidence_revision is None:
            return True, False
        if tombstone.state == "RESOLVED":
            if evidence.evidence_revision <= tombstone.latest_evidence_revision:
                return False, True
            self._mark_integrity_conflict(cursor, native_observation_id=evidence.native_observation_id)
            raise LifecycleReconciliationConflict("resolved tombstone cannot accept newer reconciliation evidence")
        if evidence.evidence_revision < tombstone.latest_evidence_revision:
            return False, True
        return True, False

    def _insert_record(
        self,
        cursor,
        *,
        evidence: LifecycleReconciliationEvidence,
        accepted: bool,
    ) -> LifecycleReconciliationRecord:
        body = evidence.body
        cursor.execute(
            """
            INSERT INTO triggertrade_lifecycle_reconciliation_records (
                evidence_id, evidence_kind, native_observation_id, native_scope_revision,
                revision_id, evidence_revision, native_scope_json, payload_json,
                payload_digest, complete, accepted, integrity_state, occurred_at
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s::jsonb, %s::jsonb,
                %s, %s, %s, 'CLEAR', %s::timestamptz
            )
            RETURNING
                evidence_id, evidence_kind, native_observation_id, native_scope_revision,
                revision_id, evidence_revision, native_scope_json::text, payload_json::text,
                payload_digest, complete, accepted, integrity_state, occurred_at::text
            """,
            (
                evidence.evidence_id,
                evidence.evidence_kind,
                evidence.native_observation_id,
                evidence.native_scope_revision,
                evidence.revision_id,
                evidence.evidence_revision,
                canonical_json_text(evidence.native_scope),
                canonical_json_text(evidence.payload),
                evidence.payload_digest,
                evidence.complete,
                accepted,
                body["occurred_at"],
            ),
        )
        row = cursor.fetchone()
        if row is None:
            raise PostgresPersistenceError("reconciliation evidence insert returned no record")
        return _record_from_row(row)

    def _get_or_create_tombstone(
        self,
        cursor,
        *,
        evidence: LifecycleReconciliationEvidence,
    ) -> LifecycleObservationTombstone:
        existing = self._get_tombstone(cursor, native_observation_id=evidence.native_observation_id)
        if existing is not None:
            if existing.native_scope_revision != evidence.native_scope_revision or existing.native_scope != evidence.native_scope:
                self._mark_integrity_conflict(cursor, native_observation_id=evidence.native_observation_id)
                raise LifecycleReconciliationConflict("native observation identity replayed with different native scope")
            return existing
        cursor.execute(
            """
            INSERT INTO triggertrade_lifecycle_reconciliation_tombstones (
                native_observation_id, native_scope_revision, native_scope_json,
                state, latest_revision_id, latest_evidence_revision,
                complete_payload_digest, unresolved_block_active, integrity_state
            ) VALUES (%s, %s, %s::jsonb, 'UNRESOLVED', NULL, NULL, NULL, TRUE, 'CLEAR')
            RETURNING
                native_observation_id, native_scope_revision, native_scope_json::text,
                state, latest_revision_id, latest_evidence_revision,
                complete_payload_digest, unresolved_block_active, integrity_state
            """,
            (
                evidence.native_observation_id,
                evidence.native_scope_revision,
                canonical_json_text(evidence.native_scope),
            ),
        )
        row = cursor.fetchone()
        if row is None:
            raise PostgresPersistenceError("reconciliation tombstone insert returned no record")
        return _tombstone_from_row(row)

    def _advance_tombstone(
        self,
        cursor,
        *,
        evidence: LifecycleReconciliationEvidence,
        previous: LifecycleObservationTombstone,
    ) -> LifecycleObservationTombstone:
        state = "RESOLVED" if evidence.complete else previous.state
        unresolved = False if evidence.complete else previous.unresolved_block_active
        complete_digest = evidence.payload_digest if evidence.complete else previous.complete_payload_digest
        cursor.execute(
            """
            UPDATE triggertrade_lifecycle_reconciliation_tombstones
            SET state = %s,
                latest_revision_id = %s,
                latest_evidence_revision = %s,
                complete_payload_digest = %s,
                unresolved_block_active = %s,
                updated_at = now()
            WHERE native_observation_id = %s
            RETURNING
                native_observation_id, native_scope_revision, native_scope_json::text,
                state, latest_revision_id, latest_evidence_revision,
                complete_payload_digest, unresolved_block_active, integrity_state
            """,
            (
                state,
                evidence.revision_id,
                evidence.evidence_revision,
                complete_digest,
                unresolved,
                evidence.native_observation_id,
            ),
        )
        row = cursor.fetchone()
        if row is None:
            raise PostgresPersistenceError("reconciliation tombstone update returned no record")
        return _tombstone_from_row(row)

    def _get_record(self, cursor, *, evidence_id: str) -> LifecycleReconciliationRecord | None:
        cursor.execute(_SELECT_RECORD + " WHERE evidence_id = %s", (evidence_id,))
        row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def _get_tombstone(self, cursor, *, native_observation_id: str) -> LifecycleObservationTombstone | None:
        cursor.execute(
            _SELECT_TOMBSTONE + " WHERE native_observation_id = %s FOR UPDATE",
            (native_observation_id,),
        )
        row = cursor.fetchone()
        return None if row is None else _tombstone_from_row(row)

    def _mark_integrity_conflict(self, cursor, *, native_observation_id: str) -> None:
        cursor.execute(
            """
            UPDATE triggertrade_lifecycle_reconciliation_tombstones
            SET integrity_state = 'CONFLICT',
                unresolved_block_active = TRUE,
                updated_at = now()
            WHERE native_observation_id = %s
            """,
            (native_observation_id,),
        )


_SELECT_RECORD = """
SELECT
    evidence_id, evidence_kind, native_observation_id, native_scope_revision,
    revision_id, evidence_revision, native_scope_json::text, payload_json::text,
    payload_digest, complete, accepted, integrity_state, occurred_at::text
FROM triggertrade_lifecycle_reconciliation_records
"""

_SELECT_TOMBSTONE = """
SELECT
    native_observation_id, native_scope_revision, native_scope_json::text,
    state, latest_revision_id, latest_evidence_revision,
    complete_payload_digest, unresolved_block_active, integrity_state
FROM triggertrade_lifecycle_reconciliation_tombstones
"""


def _record_from_row(row: tuple[Any, ...]) -> LifecycleReconciliationRecord:
    return LifecycleReconciliationRecord(
        evidence_id=str(row[0]),
        evidence_kind=str(row[1]),
        native_observation_id=str(row[2]),
        native_scope_revision=int(row[3]),
        revision_id=str(row[4]),
        evidence_revision=int(row[5]),
        native_scope=json.loads(str(row[6]), parse_float=Decimal),
        payload=json.loads(str(row[7]), parse_float=Decimal),
        payload_digest=str(row[8]),
        complete=bool(row[9]),
        accepted=bool(row[10]),
        integrity_state=str(row[11]),
        occurred_at=str(row[12]),
    )


def _tombstone_from_row(row: tuple[Any, ...]) -> LifecycleObservationTombstone:
    return LifecycleObservationTombstone(
        native_observation_id=str(row[0]),
        native_scope_revision=int(row[1]),
        native_scope=json.loads(str(row[2]), parse_float=Decimal),
        state=str(row[3]),
        latest_revision_id=None if row[4] is None else str(row[4]),
        latest_evidence_revision=None if row[5] is None else int(row[5]),
        complete_payload_digest=None if row[6] is None else str(row[6]),
        unresolved_block_active=bool(row[7]),
        integrity_state=str(row[8]),
    )


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PostgresPersistenceError(f"{field} is required")
    return value
