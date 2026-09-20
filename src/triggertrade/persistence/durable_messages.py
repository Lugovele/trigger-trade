"""Durable business outbox/inbox primitives for inter-block messages."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import json
import re
from typing import Any

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text

from .postgres import PostgresPersistenceError


_STABLE_TEXT_RE = re.compile(r"^[^\x00]{1,200}$")


class DurableMessageConflict(PostgresPersistenceError):
    """Raised when a message identity or dedupe key is replayed with new content."""


class TransportFrontierGap(PostgresPersistenceError):
    """Raised when a scoped committed-prefix frontier cannot be advanced safely."""


class TransportFrontierConflict(PostgresPersistenceError):
    """Raised when a scoped frontier identity is replayed with different content."""


@dataclass(frozen=True)
class OutboxMessageRecord:
    message_id: str
    producer: str
    consumer: str
    message_type: str
    message_version: str
    payload: dict[str, Any]
    payload_digest: str
    status: str
    aggregate_id: str | None
    causation_id: str | None
    correlation_id: str | None
    dedupe_key: str | None
    attempt_count: int
    available_at: datetime
    created_at: datetime
    locked_by: str | None
    locked_at: datetime | None
    lock_expires_at: datetime | None
    consumed_at: datetime | None


@dataclass(frozen=True)
class InboxMessageRecord:
    consumer: str
    message_id: str
    producer: str
    message_type: str
    message_version: str
    payload: dict[str, Any]
    payload_digest: str
    status: str
    received_at: datetime
    processed_at: datetime | None


@dataclass(frozen=True)
class TransportFrontierHead:
    scope_key: str
    committed_head: int


@dataclass(frozen=True)
class TransportFrontierMessage:
    scope_key: str
    sequence: int
    message_id: str
    payload_digest: str


@dataclass(frozen=True)
class TransportFrontierApplied:
    scope_key: str
    consumer: str
    applied_sequence: int


class DurableMessageStore:
    """PostgreSQL-backed outbox/inbox store for business-block messages."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def append_outbox(
        self,
        *,
        message_id: str,
        producer: str,
        consumer: str,
        message_type: str,
        message_version: str,
        payload: Mapping[str, Any],
        aggregate_id: str | None = None,
        causation_id: str | None = None,
        correlation_id: str | None = None,
        dedupe_key: str | None = None,
        available_at: datetime | None = None,
    ) -> tuple[OutboxMessageRecord, bool]:
        message_id = _stable_text(message_id, field="message_id")
        producer = _stable_text(producer, field="producer")
        consumer = _stable_text(consumer, field="consumer")
        message_type = _stable_text(message_type, field="message_type")
        message_version = _stable_text(message_version, field="message_version")
        aggregate_id = _optional_stable_text(aggregate_id, field="aggregate_id")
        causation_id = _optional_stable_text(causation_id, field="causation_id")
        correlation_id = _optional_stable_text(correlation_id, field="correlation_id")
        dedupe_key = _optional_stable_text(dedupe_key, field="dedupe_key")
        payload_text, digest = _payload_text_and_digest(payload)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_outbox_messages (
                    message_id, producer, consumer, message_type, message_version,
                    aggregate_id, causation_id, correlation_id, dedupe_key,
                    payload_json, payload_digest, available_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s::jsonb, %s, COALESCE(%s, now())
                )
                ON CONFLICT DO NOTHING
                RETURNING
                    message_id, producer, consumer, message_type, message_version,
                    aggregate_id, causation_id, correlation_id, dedupe_key,
                    payload_json::text, payload_digest, status, attempt_count,
                    available_at, created_at, locked_by, locked_at, lock_expires_at, consumed_at
                """,
                (
                    message_id,
                    producer,
                    consumer,
                    message_type,
                    message_version,
                    aggregate_id,
                    causation_id,
                    correlation_id,
                    dedupe_key,
                    payload_text,
                    digest,
                    available_at,
                ),
            )
            row = cursor.fetchone()
        if row is not None:
            return _outbox_from_row(row), True

        existing = self.get_outbox(message_id=message_id)
        if existing is None and dedupe_key is not None:
            existing = self.get_outbox_by_dedupe(producer=producer, dedupe_key=dedupe_key)
        if existing is None:
            raise PostgresPersistenceError("outbox insert conflicted but no record was found")
        if (
            existing.payload_digest != digest
            or existing.producer != producer
            or existing.consumer != consumer
            or existing.message_type != message_type
            or existing.message_version != message_version
            or existing.aggregate_id != aggregate_id
            or existing.causation_id != causation_id
            or existing.correlation_id != correlation_id
            or existing.dedupe_key != dedupe_key
        ):
            raise DurableMessageConflict("outbox identity or dedupe key already exists with different content")
        return existing, False

    def get_outbox(self, *, message_id: str) -> OutboxMessageRecord | None:
        message_id = _stable_text(message_id, field="message_id")
        with self._connection.cursor() as cursor:
            cursor.execute(_OUTBOX_SELECT + " WHERE message_id = %s", (message_id,))
            row = cursor.fetchone()
        return None if row is None else _outbox_from_row(row)

    def get_outbox_by_dedupe(self, *, producer: str, dedupe_key: str) -> OutboxMessageRecord | None:
        producer = _stable_text(producer, field="producer")
        dedupe_key = _stable_text(dedupe_key, field="dedupe_key")
        with self._connection.cursor() as cursor:
            cursor.execute(
                _OUTBOX_SELECT + " WHERE producer = %s AND dedupe_key = %s",
                (producer, dedupe_key),
            )
            row = cursor.fetchone()
        return None if row is None else _outbox_from_row(row)

    def claim_outbox(
        self,
        *,
        consumer: str,
        worker_id: str,
        limit: int = 1,
        lock_seconds: int = 60,
    ) -> tuple[OutboxMessageRecord, ...]:
        consumer = _stable_text(consumer, field="consumer")
        worker_id = _stable_text(worker_id, field="worker_id")
        if limit < 1 or limit > 100:
            raise PostgresPersistenceError("claim limit must be between 1 and 100")
        if lock_seconds < 1 or lock_seconds > 3600:
            raise PostgresPersistenceError("lock_seconds must be between 1 and 3600")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                WITH candidate AS (
                    SELECT message_id
                    FROM triggertrade_outbox_messages
                    WHERE consumer = %s
                      AND available_at <= now()
                      AND (
                          status = 'PENDING'
                          OR (status = 'IN_FLIGHT' AND lock_expires_at <= now())
                      )
                    ORDER BY created_at, message_id
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE triggertrade_outbox_messages AS outbox
                SET status = 'IN_FLIGHT',
                    locked_by = %s,
                    locked_at = now(),
                    lock_expires_at = now() + (%s * interval '1 second'),
                    attempt_count = attempt_count + 1
                FROM candidate
                WHERE outbox.message_id = candidate.message_id
                RETURNING
                    outbox.message_id, outbox.producer, outbox.consumer,
                    outbox.message_type, outbox.message_version,
                    outbox.aggregate_id, outbox.causation_id, outbox.correlation_id,
                    outbox.dedupe_key, outbox.payload_json::text, outbox.payload_digest,
                    outbox.status, outbox.attempt_count, outbox.available_at,
                    outbox.created_at, outbox.locked_by, outbox.locked_at,
                    outbox.lock_expires_at, outbox.consumed_at
                """,
                (consumer, limit, worker_id, lock_seconds),
            )
            rows = cursor.fetchall()
        return tuple(_outbox_from_row(row) for row in rows)

    def mark_outbox_consumed(self, *, message_id: str) -> OutboxMessageRecord:
        message_id = _stable_text(message_id, field="message_id")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE triggertrade_outbox_messages
                SET status = 'CONSUMED',
                    consumed_at = COALESCE(consumed_at, now()),
                    lock_expires_at = NULL
                WHERE message_id = %s
                RETURNING
                    message_id, producer, consumer, message_type, message_version,
                    aggregate_id, causation_id, correlation_id, dedupe_key,
                    payload_json::text, payload_digest, status, attempt_count,
                    available_at, created_at, locked_by, locked_at, lock_expires_at, consumed_at
                """,
                (message_id,),
            )
            row = cursor.fetchone()
        if row is None:
            raise PostgresPersistenceError("outbox message id not found")
        return _outbox_from_row(row)

    def record_inbox(
        self,
        *,
        consumer: str,
        message_id: str,
        producer: str,
        message_type: str,
        message_version: str,
        payload: Mapping[str, Any],
    ) -> tuple[InboxMessageRecord, bool]:
        consumer = _stable_text(consumer, field="consumer")
        message_id = _stable_text(message_id, field="message_id")
        producer = _stable_text(producer, field="producer")
        message_type = _stable_text(message_type, field="message_type")
        message_version = _stable_text(message_version, field="message_version")
        payload_text, digest = _payload_text_and_digest(payload)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_inbox_messages (
                    consumer, message_id, producer, message_type, message_version,
                    payload_json, payload_digest
                ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (consumer, message_id) DO NOTHING
                RETURNING
                    consumer, message_id, producer, message_type, message_version,
                    payload_json::text, payload_digest, status, received_at, processed_at
                """,
                (consumer, message_id, producer, message_type, message_version, payload_text, digest),
            )
            row = cursor.fetchone()
        if row is not None:
            return _inbox_from_row(row), True

        existing = self.get_inbox(consumer=consumer, message_id=message_id)
        if existing is None:
            raise PostgresPersistenceError("inbox insert conflicted but no record was found")
        if (
            existing.payload_digest != digest
            or existing.producer != producer
            or existing.message_type != message_type
            or existing.message_version != message_version
        ):
            raise DurableMessageConflict("inbox message identity already exists with different content")
        return existing, False

    def get_inbox(self, *, consumer: str, message_id: str) -> InboxMessageRecord | None:
        consumer = _stable_text(consumer, field="consumer")
        message_id = _stable_text(message_id, field="message_id")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT consumer, message_id, producer, message_type, message_version,
                       payload_json::text, payload_digest, status, received_at, processed_at
                FROM triggertrade_inbox_messages
                WHERE consumer = %s AND message_id = %s
                """,
                (consumer, message_id),
            )
            row = cursor.fetchone()
        return None if row is None else _inbox_from_row(row)

    def mark_inbox_processed(self, *, consumer: str, message_id: str) -> InboxMessageRecord:
        consumer = _stable_text(consumer, field="consumer")
        message_id = _stable_text(message_id, field="message_id")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE triggertrade_inbox_messages
                SET status = 'PROCESSED',
                    processed_at = COALESCE(processed_at, now())
                WHERE consumer = %s AND message_id = %s
                RETURNING consumer, message_id, producer, message_type, message_version,
                          payload_json::text, payload_digest, status, received_at, processed_at
                """,
                (consumer, message_id),
            )
            row = cursor.fetchone()
        if row is None:
            raise PostgresPersistenceError("inbox message id not found")
        return _inbox_from_row(row)

    def append_frontier_outbox(
        self,
        *,
        scope_key: str,
        message_id: str,
        producer: str,
        consumer: str,
        message_type: str,
        message_version: str,
        payload: Mapping[str, Any],
        aggregate_id: str | None = None,
        causation_id: str | None = None,
        correlation_id: str | None = None,
        dedupe_key: str | None = None,
        available_at: datetime | None = None,
    ) -> tuple[OutboxMessageRecord, TransportFrontierMessage, bool]:
        """Append an outbox message and advance the scoped committed-prefix head atomically."""

        scope_key = _stable_text(scope_key, field="scope_key")
        head = self.lock_frontier_head(scope_key=scope_key)
        outbox, _ = self.append_outbox(
            message_id=message_id,
            producer=producer,
            consumer=consumer,
            message_type=message_type,
            message_version=message_version,
            payload=payload,
            aggregate_id=aggregate_id,
            causation_id=causation_id,
            correlation_id=correlation_id,
            dedupe_key=dedupe_key,
            available_at=available_at,
        )
        existing = self.get_frontier_message(scope_key=scope_key, message_id=outbox.message_id)
        if existing is not None:
            if existing.payload_digest != outbox.payload_digest:
                raise TransportFrontierConflict("frontier message identity already exists with different content")
            return outbox, existing, False

        sequence = head.committed_head + 1
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_transport_frontier_messages (
                    scope_key, sequence, message_id, payload_digest
                ) VALUES (%s, %s, %s, %s)
                RETURNING scope_key, sequence, message_id, payload_digest
                """,
                (scope_key, sequence, outbox.message_id, outbox.payload_digest),
            )
            row = cursor.fetchone()
            cursor.execute(
                """
                UPDATE triggertrade_transport_frontier_heads
                SET committed_head = %s,
                    updated_at = now()
                WHERE scope_key = %s
                """,
                (sequence, scope_key),
            )
        if row is None:
            raise PostgresPersistenceError("frontier append did not return a record")
        return outbox, _frontier_message_from_row(row), True

    def lock_frontier_head(self, *, scope_key: str) -> TransportFrontierHead:
        scope_key = _stable_text(scope_key, field="scope_key")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_transport_frontier_heads (scope_key, committed_head)
                VALUES (%s, 0)
                ON CONFLICT (scope_key) DO NOTHING
                """,
                (scope_key,),
            )
            cursor.execute(
                """
                SELECT scope_key, committed_head
                FROM triggertrade_transport_frontier_heads
                WHERE scope_key = %s
                FOR UPDATE
                """,
                (scope_key,),
            )
            row = cursor.fetchone()
        if row is None:
            raise PostgresPersistenceError("frontier head could not be locked")
        return _frontier_head_from_row(row)

    def get_frontier_head(self, *, scope_key: str) -> TransportFrontierHead | None:
        scope_key = _stable_text(scope_key, field="scope_key")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT scope_key, committed_head
                FROM triggertrade_transport_frontier_heads
                WHERE scope_key = %s
                """,
                (scope_key,),
            )
            row = cursor.fetchone()
        return None if row is None else _frontier_head_from_row(row)

    def get_frontier_message(
        self,
        *,
        scope_key: str,
        message_id: str,
    ) -> TransportFrontierMessage | None:
        scope_key = _stable_text(scope_key, field="scope_key")
        message_id = _stable_text(message_id, field="message_id")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT scope_key, sequence, message_id, payload_digest
                FROM triggertrade_transport_frontier_messages
                WHERE scope_key = %s AND message_id = %s
                """,
                (scope_key, message_id),
            )
            row = cursor.fetchone()
        return None if row is None else _frontier_message_from_row(row)

    def list_frontier_messages(
        self,
        *,
        scope_key: str,
        after_sequence: int = 0,
        through_sequence: int | None = None,
    ) -> tuple[TransportFrontierMessage, ...]:
        scope_key = _stable_text(scope_key, field="scope_key")
        if after_sequence < 0:
            raise TransportFrontierGap("after_sequence cannot be negative")
        if through_sequence is not None and through_sequence < after_sequence:
            raise TransportFrontierGap("through_sequence cannot be before after_sequence")
        query = """
            SELECT scope_key, sequence, message_id, payload_digest
            FROM triggertrade_transport_frontier_messages
            WHERE scope_key = %s AND sequence > %s
        """
        params: tuple[Any, ...]
        if through_sequence is None:
            query += " ORDER BY sequence"
            params = (scope_key, after_sequence)
        else:
            query += " AND sequence <= %s ORDER BY sequence"
            params = (scope_key, after_sequence, through_sequence)
        with self._connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        return tuple(_frontier_message_from_row(row) for row in rows)

    def apply_frontier_prefix(
        self,
        *,
        scope_key: str,
        consumer: str,
        through_sequence: int,
    ) -> TransportFrontierApplied:
        scope_key = _stable_text(scope_key, field="scope_key")
        consumer = _stable_text(consumer, field="consumer")
        if through_sequence < 0:
            raise TransportFrontierGap("through_sequence cannot be negative")
        head = self.lock_frontier_head(scope_key=scope_key)
        if through_sequence > head.committed_head:
            raise TransportFrontierGap("cannot apply beyond committed frontier head")
        current = self._lock_frontier_applied(scope_key=scope_key, consumer=consumer)
        if through_sequence <= current.applied_sequence:
            return current
        rows = self.list_frontier_messages(
            scope_key=scope_key,
            after_sequence=current.applied_sequence,
            through_sequence=through_sequence,
        )
        expected = tuple(range(current.applied_sequence + 1, through_sequence + 1))
        actual = tuple(record.sequence for record in rows)
        if actual != expected:
            raise TransportFrontierGap("frontier prefix has a missing committed sequence")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE triggertrade_transport_frontier_applied
                SET applied_sequence = %s,
                    updated_at = now()
                WHERE scope_key = %s AND consumer = %s
                RETURNING scope_key, consumer, applied_sequence
                """,
                (through_sequence, scope_key, consumer),
            )
            row = cursor.fetchone()
        if row is None:
            raise PostgresPersistenceError("frontier applied row could not be updated")
        return _frontier_applied_from_row(row)

    def get_frontier_applied(self, *, scope_key: str, consumer: str) -> TransportFrontierApplied | None:
        scope_key = _stable_text(scope_key, field="scope_key")
        consumer = _stable_text(consumer, field="consumer")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT scope_key, consumer, applied_sequence
                FROM triggertrade_transport_frontier_applied
                WHERE scope_key = %s AND consumer = %s
                """,
                (scope_key, consumer),
            )
            row = cursor.fetchone()
        return None if row is None else _frontier_applied_from_row(row)

    def _lock_frontier_applied(self, *, scope_key: str, consumer: str) -> TransportFrontierApplied:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_transport_frontier_applied (scope_key, consumer, applied_sequence)
                VALUES (%s, %s, 0)
                ON CONFLICT (scope_key, consumer) DO NOTHING
                """,
                (scope_key, consumer),
            )
            cursor.execute(
                """
                SELECT scope_key, consumer, applied_sequence
                FROM triggertrade_transport_frontier_applied
                WHERE scope_key = %s AND consumer = %s
                FOR UPDATE
                """,
                (scope_key, consumer),
            )
            row = cursor.fetchone()
        if row is None:
            raise PostgresPersistenceError("frontier applied row could not be locked")
        return _frontier_applied_from_row(row)


_OUTBOX_SELECT = """
SELECT message_id, producer, consumer, message_type, message_version,
       aggregate_id, causation_id, correlation_id, dedupe_key,
       payload_json::text, payload_digest, status, attempt_count,
       available_at, created_at, locked_by, locked_at, lock_expires_at, consumed_at
FROM triggertrade_outbox_messages
"""


def _payload_text_and_digest(payload: Mapping[str, Any]) -> tuple[str, str]:
    payload_text = canonical_json_text(payload)
    return payload_text, canonical_json_digest(payload)


def _outbox_from_row(row: tuple[Any, ...]) -> OutboxMessageRecord:
    return OutboxMessageRecord(
        message_id=str(row[0]),
        producer=str(row[1]),
        consumer=str(row[2]),
        message_type=str(row[3]),
        message_version=str(row[4]),
        aggregate_id=None if row[5] is None else str(row[5]),
        causation_id=None if row[6] is None else str(row[6]),
        correlation_id=None if row[7] is None else str(row[7]),
        dedupe_key=None if row[8] is None else str(row[8]),
        payload=json.loads(str(row[9]), parse_float=Decimal),
        payload_digest=str(row[10]),
        status=str(row[11]),
        attempt_count=int(row[12]),
        available_at=row[13],
        created_at=row[14],
        locked_by=None if row[15] is None else str(row[15]),
        locked_at=row[16],
        lock_expires_at=row[17],
        consumed_at=row[18],
    )


def _inbox_from_row(row: tuple[Any, ...]) -> InboxMessageRecord:
    return InboxMessageRecord(
        consumer=str(row[0]),
        message_id=str(row[1]),
        producer=str(row[2]),
        message_type=str(row[3]),
        message_version=str(row[4]),
        payload=json.loads(str(row[5]), parse_float=Decimal),
        payload_digest=str(row[6]),
        status=str(row[7]),
        received_at=row[8],
        processed_at=row[9],
    )


def _frontier_head_from_row(row: tuple[Any, ...]) -> TransportFrontierHead:
    return TransportFrontierHead(scope_key=str(row[0]), committed_head=int(row[1]))


def _frontier_message_from_row(row: tuple[Any, ...]) -> TransportFrontierMessage:
    return TransportFrontierMessage(
        scope_key=str(row[0]),
        sequence=int(row[1]),
        message_id=str(row[2]),
        payload_digest=str(row[3]),
    )


def _frontier_applied_from_row(row: tuple[Any, ...]) -> TransportFrontierApplied:
    return TransportFrontierApplied(
        scope_key=str(row[0]),
        consumer=str(row[1]),
        applied_sequence=int(row[2]),
    )


def _stable_text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or _STABLE_TEXT_RE.fullmatch(value) is None:
        raise PostgresPersistenceError(f"{field} must be a non-empty stable string")
    return value


def _optional_stable_text(value: str | None, *, field: str) -> str | None:
    if value is None:
        return None
    return _stable_text(value, field=field)
