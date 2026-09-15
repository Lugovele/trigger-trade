"""Durable Lifecycle-to-Set placement synchronization persistence."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_text
from triggertrade.lifecycle_set_sync import LifecycleSetSync, LifecycleSetSyncError, build_lifecycle_set_sync_from_order_event

from .durable_messages import DurableMessageStore, OutboxMessageRecord
from .postgres import PostgresPersistenceError


class LifecycleSetSyncConflict(PostgresPersistenceError):
    """Raised when sync state is replayed with conflicting content."""


@dataclass(frozen=True)
class LifecycleSetSyncRecord:
    decision_cycle_id: str
    set_result_id: str
    symbol: str
    last_lifecycle_revision: int
    terminal_lifecycle_revision: int | None
    terminal_event_id: str | None
    terminal_event_type: str | None
    placement_event_id: str | None
    placement_lifecycle_revision: int | None
    payload: dict[str, Any]
    payload_digest: str


@dataclass(frozen=True)
class LifecycleSetSyncPublishResult:
    sync: LifecycleSetSync | None
    state: LifecycleSetSyncRecord | None
    outbox_message: OutboxMessageRecord | None
    inserted: bool
    published: bool
    suppressed_reason: str | None = None


class LifecycleSetSyncStore:
    """Persist placement sync state and publish Set outbox messages."""

    def __init__(self, connection) -> None:
        self._connection = connection
        self._messages = DurableMessageStore(connection)

    def publish_from_order_event(self, payload: dict[str, Any]) -> LifecycleSetSyncPublishResult:
        try:
            sync = build_lifecycle_set_sync_from_order_event(payload)
        except LifecycleSetSyncError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        if sync is None:
            return LifecycleSetSyncPublishResult(
                sync=None,
                state=None,
                outbox_message=None,
                inserted=False,
                published=False,
                suppressed_reason="not_sync_eligible",
            )

        existing = self.get(decision_cycle_id=sync.decision_cycle_id)
        if sync.definition == "ORDER_PLACED.placed":
            if (
                existing is not None
                and existing.terminal_lifecycle_revision is not None
                and sync.lifecycle_revision <= existing.terminal_lifecycle_revision
            ):
                return LifecycleSetSyncPublishResult(
                    sync=sync,
                    state=existing,
                    outbox_message=None,
                    inserted=False,
                    published=False,
                    suppressed_reason="terminal_tombstone_dominates",
                )
            state, inserted = self._upsert_placed(sync)
        else:
            state, inserted = self._upsert_terminal(sync)

        outbox, published = self._messages.append_outbox(
            message_id=sync.body["event_id"],
            producer="Order Lifecycle",
            consumer="Set",
            message_type="ORDER_PLACED",
            message_version="3",
            payload=sync.payload,
            aggregate_id=sync.decision_cycle_id,
            causation_id=sync.source_order_event_id,
            correlation_id=sync.decision_cycle_id,
            dedupe_key=f"{sync.definition}:{sync.decision_cycle_id}:{sync.lifecycle_revision}",
        )
        return LifecycleSetSyncPublishResult(
            sync=sync,
            state=state,
            outbox_message=outbox,
            inserted=inserted,
            published=published,
        )

    def get(self, *, decision_cycle_id: str) -> LifecycleSetSyncRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_SYNC + " WHERE decision_cycle_id = %s", (decision_cycle_id,))
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def _upsert_placed(self, sync: LifecycleSetSync) -> tuple[LifecycleSetSyncRecord, bool]:
        body = sync.body
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_lifecycle_set_sync (
                    decision_cycle_id, set_result_id, symbol, last_lifecycle_revision,
                    placement_event_id, placement_lifecycle_revision, payload_json, payload_digest
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s::jsonb, %s
                )
                ON CONFLICT (decision_cycle_id) DO UPDATE
                SET set_result_id = EXCLUDED.set_result_id,
                    symbol = EXCLUDED.symbol,
                    last_lifecycle_revision = GREATEST(
                        triggertrade_lifecycle_set_sync.last_lifecycle_revision,
                        EXCLUDED.last_lifecycle_revision
                    ),
                    placement_event_id = CASE
                        WHEN EXCLUDED.placement_lifecycle_revision >= COALESCE(
                            triggertrade_lifecycle_set_sync.placement_lifecycle_revision,
                            0
                        )
                            THEN EXCLUDED.placement_event_id
                        ELSE triggertrade_lifecycle_set_sync.placement_event_id
                    END,
                    placement_lifecycle_revision = GREATEST(
                        COALESCE(triggertrade_lifecycle_set_sync.placement_lifecycle_revision, 0),
                        EXCLUDED.placement_lifecycle_revision
                    ),
                    payload_json = CASE
                        WHEN EXCLUDED.placement_lifecycle_revision >= COALESCE(
                            triggertrade_lifecycle_set_sync.placement_lifecycle_revision,
                            0
                        )
                            THEN EXCLUDED.payload_json
                        ELSE triggertrade_lifecycle_set_sync.payload_json
                    END,
                    payload_digest = CASE
                        WHEN EXCLUDED.placement_lifecycle_revision >= COALESCE(
                            triggertrade_lifecycle_set_sync.placement_lifecycle_revision,
                            0
                        )
                            THEN EXCLUDED.payload_digest
                        ELSE triggertrade_lifecycle_set_sync.payload_digest
                    END,
                    updated_at = now()
                WHERE triggertrade_lifecycle_set_sync.terminal_lifecycle_revision IS NULL
                   OR EXCLUDED.placement_lifecycle_revision > triggertrade_lifecycle_set_sync.terminal_lifecycle_revision
                RETURNING
                    decision_cycle_id, set_result_id, symbol, last_lifecycle_revision,
                    terminal_lifecycle_revision, terminal_event_id, terminal_event_type,
                    placement_event_id, placement_lifecycle_revision, payload_json::text, payload_digest,
                    (xmax = 0) AS inserted
                """,
                (
                    body["decision_cycle_id"],
                    body["set_result_id"],
                    body["symbol"],
                    body["lifecycle_revision"],
                    body["event_id"],
                    body["lifecycle_revision"],
                    canonical_json_text(sync.payload),
                    sync.payload_digest,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            existing = self.get(decision_cycle_id=sync.decision_cycle_id)
            if existing is None:
                raise PostgresPersistenceError("placement sync suppressed but no sync state was found")
            return existing, False
        return _record_from_row(row[:-1]), bool(row[-1])

    def _upsert_terminal(self, sync: LifecycleSetSync) -> tuple[LifecycleSetSyncRecord, bool]:
        body = sync.body
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_lifecycle_set_sync (
                    decision_cycle_id, set_result_id, symbol, last_lifecycle_revision,
                    terminal_lifecycle_revision, terminal_event_id, terminal_event_type,
                    payload_json, payload_digest
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s::jsonb, %s
                )
                ON CONFLICT (decision_cycle_id) DO UPDATE
                SET set_result_id = EXCLUDED.set_result_id,
                    symbol = EXCLUDED.symbol,
                    last_lifecycle_revision = GREATEST(
                        triggertrade_lifecycle_set_sync.last_lifecycle_revision,
                        EXCLUDED.last_lifecycle_revision
                    ),
                    terminal_lifecycle_revision = GREATEST(
                        COALESCE(triggertrade_lifecycle_set_sync.terminal_lifecycle_revision, 0),
                        EXCLUDED.terminal_lifecycle_revision
                    ),
                    terminal_event_id = CASE
                        WHEN EXCLUDED.terminal_lifecycle_revision >= COALESCE(
                            triggertrade_lifecycle_set_sync.terminal_lifecycle_revision,
                            0
                        )
                            THEN EXCLUDED.terminal_event_id
                        ELSE triggertrade_lifecycle_set_sync.terminal_event_id
                    END,
                    terminal_event_type = CASE
                        WHEN EXCLUDED.terminal_lifecycle_revision >= COALESCE(
                            triggertrade_lifecycle_set_sync.terminal_lifecycle_revision,
                            0
                        )
                            THEN EXCLUDED.terminal_event_type
                        ELSE triggertrade_lifecycle_set_sync.terminal_event_type
                    END,
                    payload_json = CASE
                        WHEN EXCLUDED.last_lifecycle_revision >= triggertrade_lifecycle_set_sync.last_lifecycle_revision
                            THEN EXCLUDED.payload_json
                        ELSE triggertrade_lifecycle_set_sync.payload_json
                    END,
                    payload_digest = CASE
                        WHEN EXCLUDED.last_lifecycle_revision >= triggertrade_lifecycle_set_sync.last_lifecycle_revision
                            THEN EXCLUDED.payload_digest
                        ELSE triggertrade_lifecycle_set_sync.payload_digest
                    END,
                    updated_at = now()
                RETURNING
                    decision_cycle_id, set_result_id, symbol, last_lifecycle_revision,
                    terminal_lifecycle_revision, terminal_event_id, terminal_event_type,
                    placement_event_id, placement_lifecycle_revision, payload_json::text, payload_digest,
                    (xmax = 0) AS inserted
                """,
                (
                    body["decision_cycle_id"],
                    body["set_result_id"],
                    body["symbol"],
                    body["lifecycle_revision"],
                    body["lifecycle_revision"],
                    body["event_id"],
                    body["event_type"],
                    canonical_json_text(sync.payload),
                    sync.payload_digest,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise PostgresPersistenceError("terminal sync upsert returned no record")
        return _record_from_row(row[:-1]), bool(row[-1])


_SELECT_SYNC = """
SELECT
    decision_cycle_id, set_result_id, symbol, last_lifecycle_revision,
    terminal_lifecycle_revision, terminal_event_id, terminal_event_type,
    placement_event_id, placement_lifecycle_revision, payload_json::text, payload_digest
FROM triggertrade_lifecycle_set_sync
"""


def _record_from_row(row: tuple[Any, ...]) -> LifecycleSetSyncRecord:
    return LifecycleSetSyncRecord(
        decision_cycle_id=str(row[0]),
        set_result_id=str(row[1]),
        symbol=str(row[2]),
        last_lifecycle_revision=int(row[3]),
        terminal_lifecycle_revision=None if row[4] is None else int(row[4]),
        terminal_event_id=None if row[5] is None else str(row[5]),
        terminal_event_type=None if row[6] is None else str(row[6]),
        placement_event_id=None if row[7] is None else str(row[7]),
        placement_lifecycle_revision=None if row[8] is None else int(row[8]),
        payload=json.loads(str(row[9]), parse_float=Decimal),
        payload_digest=str(row[10]),
    )
