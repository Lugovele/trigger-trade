"""PostgreSQL close acquire-or-join authority ledger."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text
from triggertrade.lifecycle_close_authority import (
    ACTIVE_CLOSE_INTENT_STATES,
    OPEN_CHILD_STATES,
    close_child_id_for_intent,
    close_intent_id_for_tranche,
    validate_child_state,
    validate_close_state,
    validate_decimal_text,
)

from .postgres import PostgresPersistenceError


class LifecycleCloseAuthorityConflict(PostgresPersistenceError):
    """Raised when close authority cannot be safely acquired or advanced."""


@dataclass(frozen=True)
class LifecycleCloseIntentRecord:
    close_intent_id: str
    tranche_id: str
    intent_revision: int
    state: str
    native_side: str | None
    confirmed_target_quantity: str
    confirmed_residual_quantity: str
    authorized_reduction_quantity: str
    executed_reduction_quantity: str
    close_commitment_quantity_basis: str
    cause_event_ids: tuple[str, ...]
    entry_order_ids: tuple[str, ...]
    protection_child_ids: tuple[str, ...]
    unresolved_request_ids: tuple[str, ...]
    payload: dict[str, Any]
    payload_digest: str
    acquired_at: str
    resolved_at: str | None


@dataclass(frozen=True)
class LifecycleCloseChildRecord:
    close_child_id: str
    close_intent_id: str
    child_sequence: int
    child_revision: int
    client_order_link_id: str
    exchange_order_id: str | None
    authorized_reduction_quantity: str
    state: str
    payload: dict[str, Any]
    payload_digest: str
    authorized_at: str


@dataclass(frozen=True)
class CloseAcquireResult:
    intent: LifecycleCloseIntentRecord
    acquired: bool
    joined: bool
    resolved_tombstone: bool


class LifecycleCloseAuthorityStore:
    """Durable P5 acquire-or-join ledger for close authority."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def acquire_or_join(
        self,
        *,
        tranche_id: str,
        cause_event_id: str,
        cause_type: str,
        received_at: str,
        native_side: str | None = None,
        confirmed_target_quantity: str = "0",
        confirmed_residual_quantity: str = "0",
        close_commitment_quantity_basis: str = "0",
        entry_order_ids: Sequence[str] = (),
        protection_child_ids: Sequence[str] = (),
        unresolved_request_ids: Sequence[str] = (),
    ) -> CloseAcquireResult:
        tranche_id = _text(tranche_id, field="tranche_id")
        cause_event_id = _text(cause_event_id, field="cause_event_id")
        cause_type = _text(cause_type, field="cause_type")
        received_at = _text(received_at, field="received_at")
        native_side = None if native_side is None else _text(native_side, field="native_side")
        confirmed_target_quantity = validate_decimal_text(confirmed_target_quantity, field="confirmed_target_quantity")
        confirmed_residual_quantity = validate_decimal_text(confirmed_residual_quantity, field="confirmed_residual_quantity")
        close_commitment_quantity_basis = validate_decimal_text(
            close_commitment_quantity_basis,
            field="close_commitment_quantity_basis",
        )
        entry_ids = _stable_unique_tuple(entry_order_ids, field="entry_order_ids")
        protection_ids = _stable_unique_tuple(protection_child_ids, field="protection_child_ids")
        unresolved_ids = _stable_unique_tuple(unresolved_request_ids, field="unresolved_request_ids")

        with self._connection.cursor() as cursor:
            active = self._select_for_update(cursor, tranche_id=tranche_id, active=True)
            if active is not None:
                record = self._append_cause_and_reload(
                    cursor,
                    intent=active,
                    cause_event_id=cause_event_id,
                    cause_type=cause_type,
                    received_at=received_at,
                )
                return CloseAcquireResult(intent=record, acquired=False, joined=True, resolved_tombstone=False)

            resolved = self._select_for_update(cursor, tranche_id=tranche_id, active=False)
            if resolved is not None:
                return CloseAcquireResult(intent=resolved, acquired=False, joined=False, resolved_tombstone=True)

            close_intent_id = close_intent_id_for_tranche(tranche_id)
            payload = _intent_payload(
                close_intent_id=close_intent_id,
                tranche_id=tranche_id,
                intent_revision=0,
                state="ACQUIRED",
                native_side=native_side,
                confirmed_target_quantity=confirmed_target_quantity,
                confirmed_residual_quantity=confirmed_residual_quantity,
                authorized_reduction_quantity="0",
                executed_reduction_quantity="0",
                close_commitment_quantity_basis=close_commitment_quantity_basis,
                cause_event_ids=(cause_event_id,),
                entry_order_ids=entry_ids,
                protection_child_ids=protection_ids,
                unresolved_request_ids=unresolved_ids,
                acquired_at=received_at,
                resolved_at=None,
            )
            digest = canonical_json_digest(payload)
            cursor.execute(
                """
                INSERT INTO triggertrade_lifecycle_close_intents (
                    close_intent_id, tranche_id, intent_revision, state, native_side,
                    confirmed_target_quantity, confirmed_residual_quantity,
                    authorized_reduction_quantity, executed_reduction_quantity,
                    close_commitment_quantity_basis, cause_event_ids, entry_order_ids,
                    protection_child_ids, unresolved_request_ids, payload_json,
                    payload_digest, acquired_at, resolved_at
                ) VALUES (
                    %s, %s, 0, 'ACQUIRED', %s,
                    %s, %s,
                    '0', '0',
                    %s, %s::jsonb, %s::jsonb,
                    %s::jsonb, %s::jsonb, %s::jsonb,
                    %s, %s::timestamptz, NULL
                )
                ON CONFLICT DO NOTHING
                RETURNING
                    close_intent_id, tranche_id, intent_revision, state, native_side,
                    confirmed_target_quantity, confirmed_residual_quantity,
                    authorized_reduction_quantity, executed_reduction_quantity,
                    close_commitment_quantity_basis, cause_event_ids::text, entry_order_ids::text,
                    protection_child_ids::text, unresolved_request_ids::text, payload_json::text,
                    payload_digest, acquired_at::text, resolved_at::text
                """,
                (
                    close_intent_id,
                    tranche_id,
                    native_side,
                    confirmed_target_quantity,
                    confirmed_residual_quantity,
                    close_commitment_quantity_basis,
                    canonical_json_text(list((cause_event_id,))),
                    canonical_json_text(list(entry_ids)),
                    canonical_json_text(list(protection_ids)),
                    canonical_json_text(list(unresolved_ids)),
                    canonical_json_text(payload),
                    digest,
                    received_at,
                ),
            )
            row = cursor.fetchone()
            if row is None:
                active = self._select_for_update(cursor, tranche_id=tranche_id, active=True)
                if active is not None:
                    record = self._append_cause_and_reload(
                        cursor,
                        intent=active,
                        cause_event_id=cause_event_id,
                        cause_type=cause_type,
                        received_at=received_at,
                    )
                    return CloseAcquireResult(intent=record, acquired=False, joined=True, resolved_tombstone=False)
                resolved = self._select_for_update(cursor, tranche_id=tranche_id, active=False)
                if resolved is not None:
                    return CloseAcquireResult(intent=resolved, acquired=False, joined=False, resolved_tombstone=True)
                raise PostgresPersistenceError("close intent insert conflicted but no record was found")
            record = _intent_from_row(row)
            self._insert_cause(
                cursor,
                close_intent_id=record.close_intent_id,
                cause_event_id=cause_event_id,
                cause_type=cause_type,
                received_at=received_at,
            )
            return CloseAcquireResult(intent=record, acquired=True, joined=False, resolved_tombstone=False)

    def authorize_reduction_child(
        self,
        *,
        close_intent_id: str,
        expected_intent_revision: int,
        child_sequence: int,
        client_order_link_id: str,
        authorized_reduction_quantity: str,
        authorized_at: str,
    ) -> LifecycleCloseChildRecord:
        close_intent_id = _text(close_intent_id, field="close_intent_id")
        client_order_link_id = _text(client_order_link_id, field="client_order_link_id")
        authorized_reduction_quantity = validate_decimal_text(
            authorized_reduction_quantity,
            field="authorized_reduction_quantity",
        )
        authorized_at = _text(authorized_at, field="authorized_at")
        if not isinstance(expected_intent_revision, int) or isinstance(expected_intent_revision, bool) or expected_intent_revision < 0:
            raise PostgresPersistenceError("expected_intent_revision must be a nonnegative integer")

        with self._connection.cursor() as cursor:
            intent = self._get_by_id_for_update(cursor, close_intent_id=close_intent_id)
            if intent is None:
                raise PostgresPersistenceError("close intent not found")
            if intent.state not in ACTIVE_CLOSE_INTENT_STATES:
                raise LifecycleCloseAuthorityConflict("close intent is not active")
            if intent.intent_revision != expected_intent_revision:
                raise LifecycleCloseAuthorityConflict("close intent revision changed before child authorization")
            if self._has_open_child(cursor, close_intent_id=close_intent_id):
                raise LifecycleCloseAuthorityConflict("close intent already has unresolved child authority")

            close_child_id = close_child_id_for_intent(close_intent_id, child_sequence)
            payload = _child_payload(
                close_child_id=close_child_id,
                close_intent_id=close_intent_id,
                child_sequence=child_sequence,
                child_revision=0,
                client_order_link_id=client_order_link_id,
                exchange_order_id=None,
                authorized_reduction_quantity=authorized_reduction_quantity,
                state="AUTHORIZED",
                authorized_at=authorized_at,
            )
            digest = canonical_json_digest(payload)
            cursor.execute(
                """
                INSERT INTO triggertrade_lifecycle_close_children (
                    close_child_id, close_intent_id, child_sequence, child_revision,
                    client_order_link_id, exchange_order_id, authorized_reduction_quantity,
                    state, payload_json, payload_digest, authorized_at
                ) VALUES (
                    %s, %s, %s, 0,
                    %s, NULL, %s,
                    'AUTHORIZED', %s::jsonb, %s, %s::timestamptz
                )
                RETURNING
                    close_child_id, close_intent_id, child_sequence, child_revision,
                    client_order_link_id, exchange_order_id, authorized_reduction_quantity,
                    state, payload_json::text, payload_digest, authorized_at::text
                """,
                (
                    close_child_id,
                    close_intent_id,
                    child_sequence,
                    client_order_link_id,
                    authorized_reduction_quantity,
                    canonical_json_text(payload),
                    digest,
                    authorized_at,
                ),
            )
            row = cursor.fetchone()
            if row is None:
                raise PostgresPersistenceError("close child insert returned no record")
            child = _child_from_row(row)
            updated_intent = _intent_payload(
                close_intent_id=intent.close_intent_id,
                tranche_id=intent.tranche_id,
                intent_revision=intent.intent_revision + 1,
                state="REDUCTION_AUTHORIZED",
                native_side=intent.native_side,
                confirmed_target_quantity=intent.confirmed_target_quantity,
                confirmed_residual_quantity=intent.confirmed_residual_quantity,
                authorized_reduction_quantity=authorized_reduction_quantity,
                executed_reduction_quantity=intent.executed_reduction_quantity,
                close_commitment_quantity_basis=intent.close_commitment_quantity_basis,
                cause_event_ids=intent.cause_event_ids,
                entry_order_ids=intent.entry_order_ids,
                protection_child_ids=intent.protection_child_ids,
                unresolved_request_ids=intent.unresolved_request_ids,
                acquired_at=intent.acquired_at,
                resolved_at=intent.resolved_at,
            )
            cursor.execute(
                """
                UPDATE triggertrade_lifecycle_close_intents
                SET intent_revision = intent_revision + 1,
                    state = 'REDUCTION_AUTHORIZED',
                    authorized_reduction_quantity = %s,
                    payload_json = %s::jsonb,
                    payload_digest = %s,
                    updated_at = now()
                WHERE close_intent_id = %s
                  AND intent_revision = %s
                """,
                (
                    authorized_reduction_quantity,
                    canonical_json_text(updated_intent),
                    canonical_json_digest(updated_intent),
                    close_intent_id,
                    expected_intent_revision,
                ),
            )
            if cursor.rowcount != 1:
                raise LifecycleCloseAuthorityConflict("close intent revision changed before child authorization")
            return child

    def resolve_intent(self, *, close_intent_id: str, resolved_at: str) -> LifecycleCloseIntentRecord:
        close_intent_id = _text(close_intent_id, field="close_intent_id")
        resolved_at = _text(resolved_at, field="resolved_at")
        with self._connection.cursor() as cursor:
            intent = self._get_by_id_for_update(cursor, close_intent_id=close_intent_id)
            if intent is None:
                raise PostgresPersistenceError("close intent not found")
            payload = _intent_payload(
                close_intent_id=intent.close_intent_id,
                tranche_id=intent.tranche_id,
                intent_revision=intent.intent_revision + 1,
                state="RESOLVED",
                native_side=intent.native_side,
                confirmed_target_quantity=intent.confirmed_target_quantity,
                confirmed_residual_quantity=intent.confirmed_residual_quantity,
                authorized_reduction_quantity=intent.authorized_reduction_quantity,
                executed_reduction_quantity=intent.executed_reduction_quantity,
                close_commitment_quantity_basis=intent.close_commitment_quantity_basis,
                cause_event_ids=intent.cause_event_ids,
                entry_order_ids=intent.entry_order_ids,
                protection_child_ids=intent.protection_child_ids,
                unresolved_request_ids=intent.unresolved_request_ids,
                acquired_at=intent.acquired_at,
                resolved_at=resolved_at,
            )
            cursor.execute(
                """
                UPDATE triggertrade_lifecycle_close_intents
                SET intent_revision = intent_revision + 1,
                    state = 'RESOLVED',
                    resolved_at = %s::timestamptz,
                    payload_json = %s::jsonb,
                    payload_digest = %s,
                    updated_at = now()
                WHERE close_intent_id = %s
                RETURNING
                    close_intent_id, tranche_id, intent_revision, state, native_side,
                    confirmed_target_quantity, confirmed_residual_quantity,
                    authorized_reduction_quantity, executed_reduction_quantity,
                    close_commitment_quantity_basis, cause_event_ids::text, entry_order_ids::text,
                    protection_child_ids::text, unresolved_request_ids::text, payload_json::text,
                    payload_digest, acquired_at::text, resolved_at::text
                """,
                (resolved_at, canonical_json_text(payload), canonical_json_digest(payload), close_intent_id),
            )
            row = cursor.fetchone()
        if row is None:
            raise PostgresPersistenceError("close intent resolve returned no record")
        return _intent_from_row(row)

    def get_active_for_tranche(self, *, tranche_id: str) -> LifecycleCloseIntentRecord | None:
        with self._connection.cursor() as cursor:
            return self._select_for_update(cursor, tranche_id=_text(tranche_id, field="tranche_id"), active=True)

    def list_children(self, *, close_intent_id: str) -> tuple[LifecycleCloseChildRecord, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_CHILD + " WHERE close_intent_id = %s ORDER BY child_sequence", (close_intent_id,))
            rows = cursor.fetchall()
        return tuple(_child_from_row(row) for row in rows)

    def _select_for_update(self, cursor, *, tranche_id: str, active: bool) -> LifecycleCloseIntentRecord | None:
        predicate = "state <> 'RESOLVED'" if active else "state = 'RESOLVED'"
        cursor.execute(
            _SELECT_INTENT + f" WHERE tranche_id = %s AND {predicate} ORDER BY intent_revision DESC LIMIT 1 FOR UPDATE",
            (tranche_id,),
        )
        row = cursor.fetchone()
        return None if row is None else _intent_from_row(row)

    def _get_by_id_for_update(self, cursor, *, close_intent_id: str) -> LifecycleCloseIntentRecord | None:
        cursor.execute(_SELECT_INTENT + " WHERE close_intent_id = %s FOR UPDATE", (close_intent_id,))
        row = cursor.fetchone()
        return None if row is None else _intent_from_row(row)

    def _append_cause_and_reload(
        self,
        cursor,
        *,
        intent: LifecycleCloseIntentRecord,
        cause_event_id: str,
        cause_type: str,
        received_at: str,
    ) -> LifecycleCloseIntentRecord:
        inserted = self._insert_cause(
            cursor,
            close_intent_id=intent.close_intent_id,
            cause_event_id=cause_event_id,
            cause_type=cause_type,
            received_at=received_at,
        )
        if not inserted:
            return intent
        cause_event_ids = tuple(dict.fromkeys((*intent.cause_event_ids, cause_event_id)))
        payload = _intent_payload(
            close_intent_id=intent.close_intent_id,
            tranche_id=intent.tranche_id,
            intent_revision=intent.intent_revision + 1,
            state=intent.state,
            native_side=intent.native_side,
            confirmed_target_quantity=intent.confirmed_target_quantity,
            confirmed_residual_quantity=intent.confirmed_residual_quantity,
            authorized_reduction_quantity=intent.authorized_reduction_quantity,
            executed_reduction_quantity=intent.executed_reduction_quantity,
            close_commitment_quantity_basis=intent.close_commitment_quantity_basis,
            cause_event_ids=cause_event_ids,
            entry_order_ids=intent.entry_order_ids,
            protection_child_ids=intent.protection_child_ids,
            unresolved_request_ids=intent.unresolved_request_ids,
            acquired_at=intent.acquired_at,
            resolved_at=intent.resolved_at,
        )
        cursor.execute(
            """
            UPDATE triggertrade_lifecycle_close_intents
            SET intent_revision = intent_revision + 1,
                cause_event_ids = %s::jsonb,
                payload_json = %s::jsonb,
                payload_digest = %s,
                updated_at = now()
            WHERE close_intent_id = %s
            RETURNING
                close_intent_id, tranche_id, intent_revision, state, native_side,
                confirmed_target_quantity, confirmed_residual_quantity,
                authorized_reduction_quantity, executed_reduction_quantity,
                close_commitment_quantity_basis, cause_event_ids::text, entry_order_ids::text,
                protection_child_ids::text, unresolved_request_ids::text, payload_json::text,
                payload_digest, acquired_at::text, resolved_at::text
            """,
            (
                canonical_json_text(list(cause_event_ids)),
                canonical_json_text(payload),
                canonical_json_digest(payload),
                intent.close_intent_id,
            ),
        )
        row = cursor.fetchone()
        if row is None:
            raise PostgresPersistenceError("close intent cause update returned no record")
        return _intent_from_row(row)

    def _insert_cause(
        self,
        cursor,
        *,
        close_intent_id: str,
        cause_event_id: str,
        cause_type: str,
        received_at: str,
    ) -> bool:
        payload = {
            "close_intent_cause": {
                "close_intent_id": close_intent_id,
                "cause_event_id": cause_event_id,
                "cause_type": cause_type,
                "received_at": received_at,
            }
        }
        cursor.execute(
            """
            INSERT INTO triggertrade_lifecycle_close_intent_causes (
                close_intent_id, cause_event_id, cause_type, received_at, payload_json, payload_digest
            ) VALUES (%s, %s, %s, %s::timestamptz, %s::jsonb, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                close_intent_id,
                cause_event_id,
                cause_type,
                received_at,
                canonical_json_text(payload),
                canonical_json_digest(payload),
            ),
        )
        return cursor.rowcount == 1

    def _has_open_child(self, cursor, *, close_intent_id: str) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM triggertrade_lifecycle_close_children
            WHERE close_intent_id = %s
              AND state = ANY(%s)
            LIMIT 1
            """,
            (close_intent_id, list(OPEN_CHILD_STATES)),
        )
        return cursor.fetchone() is not None


_SELECT_INTENT = """
SELECT
    close_intent_id, tranche_id, intent_revision, state, native_side,
    confirmed_target_quantity, confirmed_residual_quantity,
    authorized_reduction_quantity, executed_reduction_quantity,
    close_commitment_quantity_basis, cause_event_ids::text, entry_order_ids::text,
    protection_child_ids::text, unresolved_request_ids::text, payload_json::text,
    payload_digest, acquired_at::text, resolved_at::text
FROM triggertrade_lifecycle_close_intents
"""

_SELECT_CHILD = """
SELECT
    close_child_id, close_intent_id, child_sequence, child_revision,
    client_order_link_id, exchange_order_id, authorized_reduction_quantity,
    state, payload_json::text, payload_digest, authorized_at::text
FROM triggertrade_lifecycle_close_children
"""


def _intent_payload(
    *,
    close_intent_id: str,
    tranche_id: str,
    intent_revision: int,
    state: str,
    native_side: str | None,
    confirmed_target_quantity: str,
    confirmed_residual_quantity: str,
    authorized_reduction_quantity: str,
    executed_reduction_quantity: str,
    close_commitment_quantity_basis: str,
    cause_event_ids: Sequence[str],
    entry_order_ids: Sequence[str],
    protection_child_ids: Sequence[str],
    unresolved_request_ids: Sequence[str],
    acquired_at: str,
    resolved_at: str | None,
) -> dict[str, Any]:
    return {
        "lifecycle_close_intent": {
            "close_intent_id": close_intent_id,
            "tranche_id": tranche_id,
            "intent_revision": intent_revision,
            "state": validate_close_state(state),
            "native_side": native_side,
            "confirmed_target_quantity": validate_decimal_text(
                confirmed_target_quantity,
                field="confirmed_target_quantity",
            ),
            "confirmed_residual_quantity": validate_decimal_text(
                confirmed_residual_quantity,
                field="confirmed_residual_quantity",
            ),
            "authorized_reduction_quantity": validate_decimal_text(
                authorized_reduction_quantity,
                field="authorized_reduction_quantity",
            ),
            "executed_reduction_quantity": validate_decimal_text(
                executed_reduction_quantity,
                field="executed_reduction_quantity",
            ),
            "close_commitment_quantity_basis": validate_decimal_text(
                close_commitment_quantity_basis,
                field="close_commitment_quantity_basis",
            ),
            "cause_event_ids": list(_stable_unique_tuple(cause_event_ids, field="cause_event_ids")),
            "entry_order_ids": list(_stable_unique_tuple(entry_order_ids, field="entry_order_ids")),
            "protection_child_ids": list(_stable_unique_tuple(protection_child_ids, field="protection_child_ids")),
            "unresolved_request_ids": list(_stable_unique_tuple(unresolved_request_ids, field="unresolved_request_ids")),
            "acquired_at": acquired_at,
            "resolved_at": resolved_at,
        }
    }


def _child_payload(
    *,
    close_child_id: str,
    close_intent_id: str,
    child_sequence: int,
    child_revision: int,
    client_order_link_id: str,
    exchange_order_id: str | None,
    authorized_reduction_quantity: str,
    state: str,
    authorized_at: str,
) -> dict[str, Any]:
    return {
        "lifecycle_close_child": {
            "close_child_id": close_child_id,
            "close_intent_id": close_intent_id,
            "child_sequence": child_sequence,
            "child_revision": child_revision,
            "client_order_link_id": client_order_link_id,
            "exchange_order_id": exchange_order_id,
            "authorized_reduction_quantity": validate_decimal_text(
                authorized_reduction_quantity,
                field="authorized_reduction_quantity",
            ),
            "state": validate_child_state(state),
            "authorized_at": authorized_at,
        }
    }


def _intent_from_row(row: tuple[Any, ...]) -> LifecycleCloseIntentRecord:
    return LifecycleCloseIntentRecord(
        close_intent_id=str(row[0]),
        tranche_id=str(row[1]),
        intent_revision=int(row[2]),
        state=str(row[3]),
        native_side=None if row[4] is None else str(row[4]),
        confirmed_target_quantity=str(row[5]),
        confirmed_residual_quantity=str(row[6]),
        authorized_reduction_quantity=str(row[7]),
        executed_reduction_quantity=str(row[8]),
        close_commitment_quantity_basis=str(row[9]),
        cause_event_ids=tuple(json.loads(str(row[10]), parse_float=Decimal)),
        entry_order_ids=tuple(json.loads(str(row[11]), parse_float=Decimal)),
        protection_child_ids=tuple(json.loads(str(row[12]), parse_float=Decimal)),
        unresolved_request_ids=tuple(json.loads(str(row[13]), parse_float=Decimal)),
        payload=json.loads(str(row[14]), parse_float=Decimal),
        payload_digest=str(row[15]),
        acquired_at=str(row[16]),
        resolved_at=None if row[17] is None else str(row[17]),
    )


def _child_from_row(row: tuple[Any, ...]) -> LifecycleCloseChildRecord:
    return LifecycleCloseChildRecord(
        close_child_id=str(row[0]),
        close_intent_id=str(row[1]),
        child_sequence=int(row[2]),
        child_revision=int(row[3]),
        client_order_link_id=str(row[4]),
        exchange_order_id=None if row[5] is None else str(row[5]),
        authorized_reduction_quantity=str(row[6]),
        state=str(row[7]),
        payload=json.loads(str(row[8]), parse_float=Decimal),
        payload_digest=str(row[9]),
        authorized_at=str(row[10]),
    )


def _stable_unique_tuple(values: Sequence[str], *, field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise PostgresPersistenceError(f"{field} must be a sequence")
    resolved: list[str] = []
    for value in values:
        text = _text(value, field=field)
        if text not in resolved:
            resolved.append(text)
    return tuple(resolved)


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PostgresPersistenceError(f"{field} is required")
    return value
