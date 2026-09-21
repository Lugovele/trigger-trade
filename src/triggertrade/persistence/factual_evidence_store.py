"""Durable factual evidence intake and known-content preflight."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text

from .postgres import PostgresPersistenceError


class FactualEvidenceConflict(PostgresPersistenceError):
    """Raised when an accepted factual identity is replayed with new content."""


@dataclass(frozen=True)
class FactualEvidenceRecord:
    evidence_id: str
    owner: str
    evidence_kind: str
    accepted_revision: int
    payload: dict[str, Any]
    payload_digest: str
    raw_payload: dict[str, Any]
    raw_digest: str
    provenance: dict[str, Any]


@dataclass(frozen=True)
class FactualPreflightChallenge:
    challenge_id: str
    challenge_scope: str
    challenge_kind: str
    status: str
    anchor_keys: tuple[str, ...]
    accepted_evidence_ids: tuple[str, ...]
    accepted_payload_digest: str | None
    candidate_payload_digest: str | None
    raw_payload: dict[str, Any]
    raw_digest: str
    reason: str
    challenge_digest: str


@dataclass(frozen=True)
class FactualPreflightResult:
    recognized: bool
    accepted: FactualEvidenceRecord | None
    challenge: FactualPreflightChallenge | None
    inserted: bool


class FactualEvidenceStore:
    """Persist immutable accepted facts and raw preflight contradictions.

    The store is deliberately owner-neutral: it records accepted factual content,
    exact raw anchors, and pre-ordinary-validation challenges. Later owner
    checkpoints decide final business consequences.
    """

    def __init__(self, connection) -> None:
        self._connection = connection

    def put_evidence(
        self,
        *,
        evidence_id: str,
        owner: str,
        evidence_kind: str,
        payload: Mapping[str, Any],
        raw_payload: Mapping[str, Any] | None = None,
        provenance: Mapping[str, Any] | None = None,
        anchors: Sequence[str] = (),
    ) -> tuple[FactualEvidenceRecord, bool]:
        evidence_id = _stable_text(evidence_id, field="evidence_id")
        owner = _stable_text(owner, field="owner")
        evidence_kind = _stable_text(evidence_kind, field="evidence_kind")
        clean_payload = _object(payload, field="payload")
        clean_raw = _object(clean_payload if raw_payload is None else raw_payload, field="raw_payload")
        clean_provenance = _object(provenance or {}, field="provenance")
        payload_text, payload_digest = _text_digest(clean_payload)
        raw_text, raw_digest = _text_digest(clean_raw)
        provenance_text = canonical_json_text(clean_provenance)
        with self._connection.cursor() as cursor:
            cursor.execute("SAVEPOINT factual_evidence_put")
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO triggertrade_factual_evidence_records (
                        evidence_id, owner, evidence_kind, accepted_revision,
                        payload_json, payload_digest, raw_json, raw_digest, provenance_json
                    ) VALUES (%s, %s, %s, 1, %s::jsonb, %s, %s::jsonb, %s, %s::jsonb)
                    ON CONFLICT (evidence_id) DO NOTHING
                    RETURNING evidence_id, owner, evidence_kind, accepted_revision,
                              payload_json::text, payload_digest, raw_json::text, raw_digest,
                              provenance_json::text
                    """,
                    (
                        evidence_id,
                        owner,
                        evidence_kind,
                        payload_text,
                        payload_digest,
                        raw_text,
                        raw_digest,
                        provenance_text,
                    ),
                )
                row = cursor.fetchone()
            inserted = row is not None
            if row is None:
                existing = self.get_evidence(evidence_id=evidence_id)
                if existing is None:
                    raise PostgresPersistenceError("factual evidence insert conflicted but no record was found")
                if (
                    existing.owner != owner
                    or existing.evidence_kind != evidence_kind
                    or existing.payload_digest != payload_digest
                    or existing.raw_digest != raw_digest
                    or canonical_json_digest(existing.provenance) != canonical_json_digest(clean_provenance)
                ):
                    raise FactualEvidenceConflict("factual evidence identity already exists with different content")
                record = existing
            else:
                record = _evidence_from_row(row)
            for anchor in anchors:
                self._put_anchor(anchor_key=anchor, evidence_id=evidence_id)
        except Exception:
            with self._connection.cursor() as cursor:
                cursor.execute("ROLLBACK TO SAVEPOINT factual_evidence_put")
                cursor.execute("RELEASE SAVEPOINT factual_evidence_put")
            raise
        with self._connection.cursor() as cursor:
            cursor.execute("RELEASE SAVEPOINT factual_evidence_put")
        return record, inserted

    def get_evidence(self, *, evidence_id: str) -> FactualEvidenceRecord | None:
        evidence_id = _stable_text(evidence_id, field="evidence_id")
        with self._connection.cursor() as cursor:
            cursor.execute(_EVIDENCE_SELECT + " WHERE evidence_id = %s", (evidence_id,))
            row = cursor.fetchone()
        return None if row is None else _evidence_from_row(row)

    def get_evidence_by_anchor(self, *, anchor_key: str) -> FactualEvidenceRecord | None:
        anchor_key = _stable_text(anchor_key, field="anchor_key")
        with self._connection.cursor() as cursor:
            cursor.execute(
                _EVIDENCE_SELECT
                + """
                  JOIN triggertrade_factual_evidence_anchors AS anchor
                    ON anchor.evidence_id = evidence.evidence_id
                  WHERE anchor.anchor_key = %s
                """,
                (anchor_key,),
            )
            row = cursor.fetchone()
        return None if row is None else _evidence_from_row(row)

    def preflight_known_evidence(
        self,
        *,
        challenge_scope: str,
        anchors: Sequence[str],
        raw_payload: Mapping[str, Any],
        candidate_payload: Mapping[str, Any] | None = None,
        reason: str = "known_evidence_content_changed",
    ) -> FactualPreflightResult:
        challenge_scope = _stable_text(challenge_scope, field="challenge_scope")
        anchor_keys = tuple(_stable_text(anchor, field="anchor_key") for anchor in anchors)
        if not anchor_keys:
            return FactualPreflightResult(False, None, None, False)
        accepted = self._records_for_anchors(anchor_keys)
        if not accepted:
            return FactualPreflightResult(False, None, None, False)
        if len({item.evidence_id for item in accepted}) > 1:
            challenge, inserted = self._record_challenge(
                challenge_scope=challenge_scope,
                challenge_kind="AMBIGUOUS_OWNER",
                anchor_keys=anchor_keys,
                accepted=accepted,
                raw_payload=raw_payload,
                candidate_payload=candidate_payload,
                reason="ambiguous accepted evidence anchors",
            )
            return FactualPreflightResult(True, None, challenge, inserted)
        record = accepted[0]
        candidate_digest = None if candidate_payload is None else canonical_json_digest(_object(candidate_payload, field="candidate_payload"))
        if candidate_digest is not None and candidate_digest == record.payload_digest:
            return FactualPreflightResult(True, record, None, False)
        challenge, inserted = self._record_challenge(
            challenge_scope=challenge_scope,
            challenge_kind="CONTENT_CONTRADICTION",
            anchor_keys=anchor_keys,
            accepted=(record,),
            raw_payload=raw_payload,
            candidate_payload=candidate_payload,
            reason=reason,
        )
        return FactualPreflightResult(True, record, challenge, inserted)

    def get_challenge(self, *, challenge_id: str) -> FactualPreflightChallenge | None:
        challenge_id = _stable_text(challenge_id, field="challenge_id")
        with self._connection.cursor() as cursor:
            cursor.execute(_CHALLENGE_SELECT + " WHERE challenge_id = %s", (challenge_id,))
            row = cursor.fetchone()
        return None if row is None else _challenge_from_row(row)

    def list_challenges(self, *, challenge_scope: str) -> tuple[FactualPreflightChallenge, ...]:
        challenge_scope = _stable_text(challenge_scope, field="challenge_scope")
        with self._connection.cursor() as cursor:
            cursor.execute(_CHALLENGE_SELECT + " WHERE challenge_scope = %s ORDER BY created_at, challenge_id", (challenge_scope,))
            rows = cursor.fetchall()
        return tuple(_challenge_from_row(row) for row in rows)

    def _put_anchor(self, *, anchor_key: str, evidence_id: str) -> None:
        anchor_key = _stable_text(anchor_key, field="anchor_key")
        evidence_id = _stable_text(evidence_id, field="evidence_id")
        anchor_payload = {"anchor_key": anchor_key, "evidence_id": evidence_id}
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_factual_evidence_anchors (anchor_key, evidence_id, anchor_json)
                VALUES (%s, %s, %s::jsonb)
                ON CONFLICT (anchor_key) DO NOTHING
                RETURNING evidence_id
                """,
                (anchor_key, evidence_id, canonical_json_text(anchor_payload)),
            )
            row = cursor.fetchone()
        if row is not None:
            return
        existing = self.get_evidence_by_anchor(anchor_key=anchor_key)
        if existing is None:
            raise PostgresPersistenceError("factual evidence anchor conflicted but no record was found")
        if existing.evidence_id != evidence_id:
            raise FactualEvidenceConflict("factual evidence anchor already belongs to another accepted identity")

    def _records_for_anchors(self, anchor_keys: Sequence[str]) -> tuple[FactualEvidenceRecord, ...]:
        records: dict[str, FactualEvidenceRecord] = {}
        for anchor in anchor_keys:
            record = self.get_evidence_by_anchor(anchor_key=anchor)
            if record is not None:
                records[record.evidence_id] = record
        return tuple(records[key] for key in sorted(records))

    def _record_challenge(
        self,
        *,
        challenge_scope: str,
        challenge_kind: str,
        anchor_keys: Sequence[str],
        accepted: Sequence[FactualEvidenceRecord],
        raw_payload: Mapping[str, Any],
        candidate_payload: Mapping[str, Any] | None,
        reason: str,
    ) -> tuple[FactualPreflightChallenge, bool]:
        clean_raw = _object(raw_payload, field="raw_payload")
        raw_text, raw_digest = _text_digest(clean_raw)
        clean_candidate = None if candidate_payload is None else _object(candidate_payload, field="candidate_payload")
        candidate_digest = None if clean_candidate is None else canonical_json_digest(clean_candidate)
        accepted_ids = tuple(record.evidence_id for record in accepted)
        accepted_digest = None
        if len(accepted) == 1:
            accepted_digest = accepted[0].payload_digest
        challenge_basis = {
            "challenge_scope": challenge_scope,
            "challenge_kind": challenge_kind,
            "anchor_keys": list(anchor_keys),
            "accepted_evidence_ids": list(accepted_ids),
            "accepted_payload_digest": accepted_digest,
            "candidate_payload_digest": candidate_digest,
            "raw_digest": raw_digest,
            "reason": reason,
        }
        challenge_digest = canonical_json_digest(challenge_basis)
        challenge_id = f"fact-challenge-{challenge_digest[:24]}"
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_factual_preflight_challenges (
                    challenge_id, challenge_scope, challenge_kind, status,
                    anchor_keys_json, accepted_evidence_ids_json,
                    accepted_payload_digest, candidate_payload_digest,
                    raw_json, raw_digest, reason, challenge_digest
                ) VALUES (
                    %s, %s, %s, 'QUARANTINED',
                    %s::jsonb, %s::jsonb,
                    %s, %s,
                    %s::jsonb, %s, %s, %s
                )
                ON CONFLICT (challenge_digest) DO NOTHING
                RETURNING challenge_id, challenge_scope, challenge_kind, status,
                          anchor_keys_json::text, accepted_evidence_ids_json::text,
                          accepted_payload_digest, candidate_payload_digest,
                          raw_json::text, raw_digest, reason, challenge_digest
                """,
                (
                    challenge_id,
                    challenge_scope,
                    challenge_kind,
                    canonical_json_text(list(anchor_keys)),
                    canonical_json_text(list(accepted_ids)),
                    accepted_digest,
                    candidate_digest,
                    raw_text,
                    raw_digest,
                    reason,
                    challenge_digest,
                ),
            )
            row = cursor.fetchone()
        if row is not None:
            return _challenge_from_row(row), True
        existing = self.get_challenge(challenge_id=challenge_id)
        if existing is None:
            with self._connection.cursor() as cursor:
                cursor.execute(_CHALLENGE_SELECT + " WHERE challenge_digest = %s", (challenge_digest,))
                row = cursor.fetchone()
            if row is None:
                raise PostgresPersistenceError("preflight challenge conflicted but no record was found")
            existing = _challenge_from_row(row)
        return existing, False


_EVIDENCE_SELECT = """
SELECT evidence.evidence_id, evidence.owner, evidence.evidence_kind, evidence.accepted_revision,
       evidence.payload_json::text, evidence.payload_digest,
       evidence.raw_json::text, evidence.raw_digest, evidence.provenance_json::text
FROM triggertrade_factual_evidence_records AS evidence
"""

_CHALLENGE_SELECT = """
SELECT challenge_id, challenge_scope, challenge_kind, status,
       anchor_keys_json::text, accepted_evidence_ids_json::text,
       accepted_payload_digest, candidate_payload_digest,
       raw_json::text, raw_digest, reason, challenge_digest
FROM triggertrade_factual_preflight_challenges
"""


def _evidence_from_row(row: tuple[Any, ...]) -> FactualEvidenceRecord:
    return FactualEvidenceRecord(
        evidence_id=str(row[0]),
        owner=str(row[1]),
        evidence_kind=str(row[2]),
        accepted_revision=int(row[3]),
        payload=json.loads(str(row[4]), parse_float=Decimal),
        payload_digest=str(row[5]),
        raw_payload=json.loads(str(row[6]), parse_float=Decimal),
        raw_digest=str(row[7]),
        provenance=json.loads(str(row[8]), parse_float=Decimal),
    )


def _challenge_from_row(row: tuple[Any, ...]) -> FactualPreflightChallenge:
    return FactualPreflightChallenge(
        challenge_id=str(row[0]),
        challenge_scope=str(row[1]),
        challenge_kind=str(row[2]),
        status=str(row[3]),
        anchor_keys=tuple(json.loads(str(row[4]))),
        accepted_evidence_ids=tuple(json.loads(str(row[5]))),
        accepted_payload_digest=None if row[6] is None else str(row[6]),
        candidate_payload_digest=None if row[7] is None else str(row[7]),
        raw_payload=json.loads(str(row[8]), parse_float=Decimal),
        raw_digest=str(row[9]),
        reason=str(row[10]),
        challenge_digest=str(row[11]),
    )


def _text_digest(payload: Mapping[str, Any]) -> tuple[str, str]:
    text = canonical_json_text(payload)
    return text, canonical_json_digest(payload)


def _object(value: Mapping[str, Any], *, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise PostgresPersistenceError(f"{field} must be an object")
    return dict(value)


def _stable_text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 240 or "\x00" in value:
        raise PostgresPersistenceError(f"{field} must be a non-empty stable string")
    return value
