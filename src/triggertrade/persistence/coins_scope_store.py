"""Durable Portfolio Coins v2 scope revisions and Set intake state."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text
from triggertrade.coins_scope import (
    CoinScopeDelta,
    CoinsAction,
    SetScopeState,
    apply_set_scope_delta,
    build_coins_contract,
)
from triggertrade.contracts import ContractError, parse_contract
from triggertrade.set_scope import SetConfigurationBinding, SetFormationEpoch, SetScopeError

from .durable_messages import DurableMessageStore
from .postgres import OwnerStateRevisionConflict, PostgresPersistenceError


class CoinsScopeConflict(PostgresPersistenceError):
    """Raised when a Coins revision identity is replayed with different content."""


@dataclass(frozen=True)
class CoinsScopeRevisionRecord:
    symbol: str
    scope_revision: int
    action: CoinsAction
    event_id: str
    occurred_at: str
    payload: dict[str, Any]
    payload_digest: str


@dataclass(frozen=True)
class SetScopeApplyResult:
    applied: tuple[SetScopeState, ...]
    ignored: tuple[CoinScopeDelta, ...]
    opened_epochs: tuple[SetFormationEpoch, ...] = ()
    terminated_epochs: tuple[SetFormationEpoch, ...] = ()


class CoinsScopeStore:
    """Record Portfolio scope deltas, publish them, and apply Set intake monotonically."""

    def __init__(self, connection) -> None:
        self._connection = connection
        self._messages = DurableMessageStore(connection)

    def publish(
        self,
        *,
        event_id: str,
        occurred_at: str,
        symbols: tuple[CoinScopeDelta, ...],
    ) -> tuple[tuple[CoinsScopeRevisionRecord, ...], bool]:
        parsed = build_coins_contract(event_id=event_id, occurred_at=occurred_at, symbols=symbols)
        payload = parsed.to_payload()
        payload_text = canonical_json_text(payload)
        digest = canonical_json_digest(payload)
        records: list[CoinsScopeRevisionRecord] = []
        inserted_any = False
        with self._connection.cursor() as cursor:
            for delta in symbols:
                current = self.get_portfolio_revision(symbol=delta.symbol, scope_revision=delta.scope_revision)
                if current is not None:
                    if current.payload_digest != digest or current.event_id != event_id or current.action != delta.action:
                        raise CoinsScopeConflict("Coins scope revision already exists with different content")
                    records.append(current)
                    continue
                latest = self.get_latest_portfolio_revision(symbol=delta.symbol, for_update=True)
                if latest is not None and delta.scope_revision <= latest.scope_revision:
                    raise OwnerStateRevisionConflict("Coins scope_revision must advance Portfolio scope for the symbol")
                cursor.execute(
                    """
                    INSERT INTO triggertrade_coins_scope_revisions (
                        symbol, scope_revision, action, event_id, occurred_at, payload_json, payload_digest
                    ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT DO NOTHING
                    RETURNING symbol, scope_revision, action, event_id, occurred_at, payload_json::text, payload_digest
                    """,
                    (delta.symbol, delta.scope_revision, delta.action.value, event_id, occurred_at, payload_text, digest),
                )
                row = cursor.fetchone()
                if row is None:
                    replayed = self.get_portfolio_revision(symbol=delta.symbol, scope_revision=delta.scope_revision)
                    if replayed is None:
                        raise PostgresPersistenceError("Coins scope revision conflicted but no record was found")
                    if replayed.payload_digest != digest or replayed.event_id != event_id or replayed.action != delta.action:
                        raise CoinsScopeConflict("Coins scope revision already exists with different content")
                    records.append(replayed)
                else:
                    inserted_any = True
                    records.append(_revision_from_row(row))
        self._messages.append_outbox(
            message_id=event_id,
            producer="Portfolio",
            consumer="Set",
            message_type="COINS",
            message_version="2",
            payload=payload,
            aggregate_id="coins_scope",
            dedupe_key=f"COINS:{event_id}",
        )
        return tuple(records), inserted_any

    def apply_to_set(
        self,
        payload: dict[str, Any],
        *,
        configuration_binding: SetConfigurationBinding | None = None,
    ) -> SetScopeApplyResult:
        try:
            parsed = parse_contract("COINS", payload)
        except ContractError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        resolved = parsed.to_payload()
        digest = canonical_json_digest(resolved)
        body = resolved["coins"]
        applied: list[SetScopeState] = []
        ignored: list[CoinScopeDelta] = []
        opened_epochs: list[SetFormationEpoch] = []
        terminated_epochs: list[SetFormationEpoch] = []
        for delta_payload in body["symbols"]:
            delta = CoinScopeDelta.from_payload(delta_payload)
            current = self.get_set_scope(symbol=delta.symbol, for_update=True)
            next_state = apply_set_scope_delta(
                current,
                delta,
                event_id=body["event_id"],
                occurred_at=body["occurred_at"],
                payload_digest=digest,
            )
            if next_state is None:
                ignored.append(delta)
                continue
            if delta.action is CoinsAction.OPEN and configuration_binding is None:
                raise PostgresPersistenceError("Set configuration binding is required for effective OPEN scope revisions")
            active_epoch = self.get_active_formation_epoch(symbol=delta.symbol, for_update=True)
            if active_epoch is not None:
                terminated_epochs.append(
                    self._terminate_formation_epoch(
                        active_epoch,
                        terminating_revision=delta.scope_revision,
                        event_id=body["event_id"],
                        occurred_at=body["occurred_at"],
                        action=delta.action,
                    )
                )
            with self._connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO triggertrade_set_scope_current (
                        symbol, scope_revision, action, event_id, occurred_at, payload_digest
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol) DO UPDATE
                    SET scope_revision = EXCLUDED.scope_revision,
                        action = EXCLUDED.action,
                        event_id = EXCLUDED.event_id,
                        occurred_at = EXCLUDED.occurred_at,
                        payload_digest = EXCLUDED.payload_digest,
                        updated_at = now()
                    WHERE triggertrade_set_scope_current.scope_revision < EXCLUDED.scope_revision
                    RETURNING symbol, scope_revision, action, event_id, occurred_at, payload_digest
                    """,
                    (
                        next_state.symbol,
                        next_state.scope_revision,
                        next_state.action.value,
                        next_state.event_id,
                        next_state.occurred_at,
                        next_state.payload_digest,
                    ),
                )
                row = cursor.fetchone()
            if row is None:
                ignored.append(delta)
            else:
                applied.append(_set_scope_from_row(row))
                if delta.action is CoinsAction.OPEN:
                    assert configuration_binding is not None
                    opened_epochs.append(
                        self._open_formation_epoch(
                            next_state,
                            configuration_binding=configuration_binding,
                        )
                    )
        return SetScopeApplyResult(
            applied=tuple(applied),
            ignored=tuple(ignored),
            opened_epochs=tuple(opened_epochs),
            terminated_epochs=tuple(terminated_epochs),
        )

    def get_portfolio_revision(self, *, symbol: str, scope_revision: int) -> CoinsScopeRevisionRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT symbol, scope_revision, action, event_id, occurred_at, payload_json::text, payload_digest
                FROM triggertrade_coins_scope_revisions
                WHERE symbol = %s AND scope_revision = %s
                """,
                (symbol.upper(), scope_revision),
            )
            row = cursor.fetchone()
        return None if row is None else _revision_from_row(row)

    def get_latest_portfolio_revision(self, *, symbol: str, for_update: bool = False) -> CoinsScopeRevisionRecord | None:
        suffix = " FOR UPDATE" if for_update else ""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT symbol, scope_revision, action, event_id, occurred_at, payload_json::text, payload_digest
                FROM triggertrade_coins_scope_revisions
                WHERE symbol = %s
                ORDER BY scope_revision DESC
                LIMIT 1
                """ + suffix,
                (symbol.upper(),),
            )
            row = cursor.fetchone()
        return None if row is None else _revision_from_row(row)

    def get_set_scope(self, *, symbol: str, for_update: bool = False) -> SetScopeState | None:
        suffix = " FOR UPDATE" if for_update else ""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT symbol, scope_revision, action, event_id, occurred_at, payload_digest
                FROM triggertrade_set_scope_current
                WHERE symbol = %s
                """ + suffix,
                (symbol.upper(),),
            )
            row = cursor.fetchone()
        return None if row is None else _set_scope_from_row(row)

    def get_formation_epoch(self, *, symbol: str, formation_epoch: int) -> SetFormationEpoch | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                _SELECT_EPOCH + " WHERE symbol = %s AND formation_epoch = %s",
                (symbol.upper(), formation_epoch),
            )
            row = cursor.fetchone()
        return None if row is None else _formation_epoch_from_row(row)

    def get_active_formation_epoch(self, *, symbol: str, for_update: bool = False) -> SetFormationEpoch | None:
        suffix = " FOR UPDATE" if for_update else ""
        with self._connection.cursor() as cursor:
            cursor.execute(
                _SELECT_EPOCH + " WHERE symbol = %s AND epoch_state = 'ACTIVE'" + suffix,
                (symbol.upper(),),
            )
            row = cursor.fetchone()
        return None if row is None else _formation_epoch_from_row(row)

    def _open_formation_epoch(
        self,
        state: SetScopeState,
        *,
        configuration_binding: SetConfigurationBinding,
    ) -> SetFormationEpoch:
        payload = configuration_binding.to_payload()
        payload_text = canonical_json_text(payload)
        digest = configuration_binding.digest
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_set_scope_epochs (
                    symbol, formation_epoch, epoch_state, open_event_id, opened_at,
                    open_payload_digest, configuration_binding_json, configuration_binding_digest
                ) VALUES (%s, %s, 'ACTIVE', %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (symbol, formation_epoch) DO NOTHING
                RETURNING
                    symbol, formation_epoch, epoch_state, open_event_id, opened_at, open_payload_digest,
                    configuration_binding_json::text, configuration_binding_digest,
                    terminated_by_scope_revision, terminated_by_event_id, terminated_at, terminated_by_action
                """,
                (
                    state.symbol,
                    state.scope_revision,
                    state.event_id,
                    state.occurred_at,
                    state.payload_digest,
                    payload_text,
                    digest,
                ),
            )
            row = cursor.fetchone()
        if row is not None:
            return _formation_epoch_from_row(row)
        existing = self.get_formation_epoch(symbol=state.symbol, formation_epoch=state.scope_revision)
        if existing is None:
            raise PostgresPersistenceError("Set formation epoch insert conflicted but no record was found")
        if (
            existing.open_event_id != state.event_id
            or existing.open_payload_digest != state.payload_digest
            or existing.configuration_binding.digest != digest
        ):
            raise CoinsScopeConflict("Set formation epoch already exists with different content")
        return existing

    def _terminate_formation_epoch(
        self,
        epoch: SetFormationEpoch,
        *,
        terminating_revision: int,
        event_id: str,
        occurred_at: str,
        action: CoinsAction,
    ) -> SetFormationEpoch:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE triggertrade_set_scope_epochs
                SET epoch_state = 'TERMINATED',
                    terminated_by_scope_revision = %s,
                    terminated_by_event_id = %s,
                    terminated_at = %s,
                    terminated_by_action = %s,
                    updated_at = now()
                WHERE symbol = %s
                  AND formation_epoch = %s
                  AND epoch_state = 'ACTIVE'
                RETURNING
                    symbol, formation_epoch, epoch_state, open_event_id, opened_at, open_payload_digest,
                    configuration_binding_json::text, configuration_binding_digest,
                    terminated_by_scope_revision, terminated_by_event_id, terminated_at, terminated_by_action
                """,
                (
                    terminating_revision,
                    event_id,
                    occurred_at,
                    action.value,
                    epoch.symbol,
                    epoch.formation_epoch,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            current = self.get_formation_epoch(symbol=epoch.symbol, formation_epoch=epoch.formation_epoch)
            if current is None:
                raise PostgresPersistenceError("Set formation epoch disappeared during termination")
            return current
        return _formation_epoch_from_row(row)


def _revision_from_row(row: tuple[Any, ...]) -> CoinsScopeRevisionRecord:
    return CoinsScopeRevisionRecord(
        symbol=str(row[0]),
        scope_revision=int(row[1]),
        action=CoinsAction(str(row[2])),
        event_id=str(row[3]),
        occurred_at=row[4].isoformat().replace("+00:00", "Z") if hasattr(row[4], "isoformat") else str(row[4]),
        payload=json.loads(str(row[5]), parse_float=Decimal),
        payload_digest=str(row[6]),
    )


def _set_scope_from_row(row: tuple[Any, ...]) -> SetScopeState:
    return SetScopeState(
        symbol=str(row[0]),
        scope_revision=int(row[1]),
        action=CoinsAction(str(row[2])),
        event_id=str(row[3]),
        occurred_at=row[4].isoformat().replace("+00:00", "Z") if hasattr(row[4], "isoformat") else str(row[4]),
        payload_digest=str(row[5]),
    )


_SELECT_EPOCH = """
SELECT
    symbol, formation_epoch, epoch_state, open_event_id, opened_at, open_payload_digest,
    configuration_binding_json::text, configuration_binding_digest,
    terminated_by_scope_revision, terminated_by_event_id, terminated_at, terminated_by_action
FROM triggertrade_set_scope_epochs
"""


def _formation_epoch_from_row(row: tuple[Any, ...]) -> SetFormationEpoch:
    binding_payload = json.loads(str(row[6]), parse_float=Decimal)
    try:
        binding = SetConfigurationBinding.from_payload(binding_payload)
    except SetScopeError as exc:
        raise PostgresPersistenceError(str(exc)) from exc
    digest = binding.digest
    if digest != str(row[7]):
        raise PostgresPersistenceError("Set formation epoch configuration binding digest mismatch")
    return SetFormationEpoch(
        symbol=str(row[0]),
        formation_epoch=int(row[1]),
        epoch_state=str(row[2]),
        open_event_id=str(row[3]),
        opened_at=row[4].isoformat().replace("+00:00", "Z") if hasattr(row[4], "isoformat") else str(row[4]),
        open_payload_digest=str(row[5]),
        configuration_binding=binding,
        terminated_by_scope_revision=None if row[8] is None else int(row[8]),
        terminated_by_event_id=None if row[9] is None else str(row[9]),
        terminated_at=(
            None
            if row[10] is None
            else row[10].isoformat().replace("+00:00", "Z")
            if hasattr(row[10], "isoformat")
            else str(row[10])
        ),
        terminated_by_action=None if row[11] is None else str(row[11]),
    )
