"""PostgreSQL-backed runtime state for canonical restart recovery."""

from __future__ import annotations

import json
from typing import Any

from triggertrade.market_data import MarketRegimeContext, MarketRegimeLabel, RegimeCapability
from triggertrade.persistence.postgres import (
    OwnerStateRecord,
    OwnerStateStore,
    PostgresConnectionFactory,
    PostgresUnitOfWork,
)
from triggertrade.persistence.runtime_store import (
    CandleLifecycle,
    LaneCandleLifecycle,
    LaneRuntimeCheckpoint,
    RuntimeCheckpoint,
    RuntimeHeartbeat,
    RuntimeStoreError,
)


RUNTIME_OWNER = "Cross-System"


class PostgresRuntimeStore:
    """Runtime checkpoint and heartbeat state without local filesystem truth."""

    def __init__(self, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def checkpoint(self, checkpoint: RuntimeCheckpoint) -> None:
        self._upsert_current_state(
            state_type="runtime_checkpoint",
            state_id=_runtime_checkpoint_id(checkpoint.symbol, checkpoint.timeframe),
            payload=_runtime_checkpoint_payload(checkpoint),
        )

    def get_checkpoint(self, symbol: str, timeframe: str) -> RuntimeCheckpoint | None:
        record = self._get_state(
            state_type="runtime_checkpoint",
            state_id=_runtime_checkpoint_id(symbol, timeframe),
        )
        return None if record is None else _runtime_checkpoint_from_payload(record.payload)

    def save_lifecycle(self, lifecycle: CandleLifecycle) -> None:
        self._upsert_current_state(
            state_type="runtime_candle_lifecycle",
            state_id=_runtime_lifecycle_id(lifecycle.candle_id),
            payload=_runtime_lifecycle_payload(lifecycle),
        )

    def get_lifecycle(self, candle_id: str) -> CandleLifecycle | None:
        record = self._get_state(
            state_type="runtime_candle_lifecycle",
            state_id=_runtime_lifecycle_id(candle_id),
        )
        return None if record is None else _runtime_lifecycle_from_payload(record.payload)

    def processed_count(self, candle_id: str) -> int:
        return 0 if self.get_lifecycle(candle_id) is None else 1

    def lane_checkpoint(self, checkpoint: LaneRuntimeCheckpoint) -> None:
        self._upsert_current_state(
            state_type="runtime_lane_checkpoint",
            state_id=_lane_checkpoint_id(
                checkpoint.lane,
                checkpoint.symbol,
                checkpoint.timeframe,
                checkpoint.trigger_set_id,
                checkpoint.trigger_set_version,
            ),
            payload=_lane_checkpoint_payload(checkpoint),
        )

    def get_lane_checkpoint(
        self,
        *,
        lane: str,
        symbol: str,
        timeframe: str,
        trigger_set_id: str,
        trigger_set_version: str,
    ) -> LaneRuntimeCheckpoint | None:
        record = self._get_state(
            state_type="runtime_lane_checkpoint",
            state_id=_lane_checkpoint_id(lane, symbol, timeframe, trigger_set_id, trigger_set_version),
        )
        return None if record is None else _lane_checkpoint_from_payload(record.payload)

    def save_lane_lifecycle(self, lifecycle: LaneCandleLifecycle) -> None:
        self._upsert_current_state(
            state_type="runtime_lane_lifecycle",
            state_id=_lane_lifecycle_id(
                lifecycle.lane,
                lifecycle.symbol,
                lifecycle.timeframe,
                lifecycle.candle_id,
                lifecycle.trigger_set_id,
                lifecycle.trigger_set_version,
            ),
            payload=_lane_lifecycle_payload(lifecycle),
        )

    def get_lane_lifecycle(
        self,
        *,
        lane: str,
        symbol: str,
        timeframe: str,
        candle_id: str,
        trigger_set_id: str,
        trigger_set_version: str,
    ) -> LaneCandleLifecycle | None:
        record = self._get_state(
            state_type="runtime_lane_lifecycle",
            state_id=_lane_lifecycle_id(lane, symbol, timeframe, candle_id, trigger_set_id, trigger_set_version),
        )
        return None if record is None else _lane_lifecycle_from_payload(record.payload)

    def lane_processed_count(
        self,
        *,
        lane: str,
        symbol: str,
        timeframe: str,
        candle_id: str,
        trigger_set_id: str,
        trigger_set_version: str,
    ) -> int:
        return (
            0
            if self.get_lane_lifecycle(
                lane=lane,
                symbol=symbol,
                timeframe=timeframe,
                candle_id=candle_id,
                trigger_set_id=trigger_set_id,
                trigger_set_version=trigger_set_version,
            )
            is None
            else 1
        )

    def save_market_regime(self, context: MarketRegimeContext) -> None:
        state_id = _market_regime_id(context.context_id)
        payload = _market_regime_payload(context)
        with PostgresUnitOfWork(self._factory) as uow:
            store = OwnerStateStore(uow.connection)
            existing = store.get(owner=RUNTIME_OWNER, state_type="market_regime_evaluation", state_id=state_id)
            if existing is not None and existing.payload != payload:
                raise RuntimeStoreError("market regime evaluation is immutable for its business key")
            store.put_if_absent(
                owner=RUNTIME_OWNER,
                state_type="market_regime_evaluation",
                state_id=state_id,
                payload=payload,
            )

    def get_market_regime(self, context_id: str) -> MarketRegimeContext | None:
        record = self._get_state(
            state_type="market_regime_evaluation",
            state_id=_market_regime_id(context_id),
        )
        return None if record is None else _market_regime_from_payload(record.payload)

    def latest_market_regime(self, symbol: str, timeframe: str) -> MarketRegimeContext | None:
        with PostgresUnitOfWork(self._factory) as uow:
            with uow.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT payload_json::text
                    FROM triggertrade_owner_state_records
                    WHERE owner = %s
                      AND state_type = %s
                      AND payload_json->>'symbol' = %s
                      AND payload_json->>'timeframe' = %s
                    ORDER BY payload_json->>'observed_at' DESC
                    LIMIT 1
                    """,
                    (RUNTIME_OWNER, "market_regime_evaluation", symbol.upper(), timeframe),
                )
                row = cursor.fetchone()
        return None if row is None else _market_regime_from_payload(json.loads(str(row[0])))

    def record_heartbeat(self, heartbeat: RuntimeHeartbeat) -> RuntimeHeartbeat:
        normalized = _normalize_heartbeat(heartbeat)
        self._upsert_current_state(
            state_type="runtime_heartbeat",
            state_id=_heartbeat_id(normalized.component),
            payload=_heartbeat_payload(normalized),
        )
        return normalized

    def list_heartbeats(self) -> tuple[RuntimeHeartbeat, ...]:
        with PostgresUnitOfWork(self._factory) as uow:
            with uow.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT payload_json::text
                    FROM triggertrade_owner_state_records
                    WHERE owner = %s AND state_type = %s
                    ORDER BY state_id
                    """,
                    (RUNTIME_OWNER, "runtime_heartbeat"),
                )
                rows = cursor.fetchall()
        return tuple(_heartbeat_from_payload(json.loads(str(row[0]))) for row in rows)

    def _get_state(self, *, state_type: str, state_id: str) -> OwnerStateRecord | None:
        with PostgresUnitOfWork(self._factory) as uow:
            return OwnerStateStore(uow.connection).get(
                owner=RUNTIME_OWNER,
                state_type=state_type,
                state_id=state_id,
            )

    def _upsert_current_state(self, *, state_type: str, state_id: str, payload: dict[str, Any]) -> OwnerStateRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            store = OwnerStateStore(uow.connection)
            existing = store.get(owner=RUNTIME_OWNER, state_type=state_type, state_id=state_id)
            if existing is None:
                record, _ = store.put_if_absent(
                    owner=RUNTIME_OWNER,
                    state_type=state_type,
                    state_id=state_id,
                    payload=payload,
                )
                return record
            return store.compare_and_set(
                owner=RUNTIME_OWNER,
                state_type=state_type,
                state_id=state_id,
                expected_revision=existing.revision,
                payload=payload,
            )


def _runtime_checkpoint_id(symbol: str, timeframe: str) -> str:
    return _state_id("runtime_checkpoint", symbol.upper(), timeframe)


def _runtime_lifecycle_id(candle_id: str) -> str:
    return _state_id("runtime_candle_lifecycle", candle_id)


def _lane_checkpoint_id(lane: str, symbol: str, timeframe: str, set_id: str, set_version: str) -> str:
    return _state_id("runtime_lane_checkpoint", lane.upper(), symbol.upper(), timeframe, set_id, set_version)


def _lane_lifecycle_id(lane: str, symbol: str, timeframe: str, candle_id: str, set_id: str, set_version: str) -> str:
    return _state_id("runtime_lane_lifecycle", lane.upper(), symbol.upper(), timeframe, candle_id, set_id, set_version)


def _market_regime_id(context_id: str) -> str:
    return _state_id("market_regime", context_id)


def _heartbeat_id(component: str) -> str:
    return _state_id("runtime_heartbeat", component.strip().lower())


def _state_id(*parts: str) -> str:
    return "|".join(str(part).replace("\x00", "").strip() for part in parts)


def _runtime_checkpoint_payload(checkpoint: RuntimeCheckpoint) -> dict[str, str]:
    return checkpoint.__dict__.copy()


def _runtime_checkpoint_from_payload(payload: dict[str, Any]) -> RuntimeCheckpoint:
    return RuntimeCheckpoint(**{key: str(payload[key]) for key in RuntimeCheckpoint.__dataclass_fields__})


def _runtime_lifecycle_payload(lifecycle: CandleLifecycle) -> dict[str, Any]:
    return lifecycle.__dict__.copy()


def _runtime_lifecycle_from_payload(payload: dict[str, Any]) -> CandleLifecycle:
    return CandleLifecycle(**_payload_kwargs(payload, CandleLifecycle))


def _lane_checkpoint_payload(checkpoint: LaneRuntimeCheckpoint) -> dict[str, str]:
    return checkpoint.__dict__.copy()


def _lane_checkpoint_from_payload(payload: dict[str, Any]) -> LaneRuntimeCheckpoint:
    return LaneRuntimeCheckpoint(**{key: str(payload[key]) for key in LaneRuntimeCheckpoint.__dataclass_fields__})


def _lane_lifecycle_payload(lifecycle: LaneCandleLifecycle) -> dict[str, Any]:
    return lifecycle.__dict__.copy()


def _lane_lifecycle_from_payload(payload: dict[str, Any]) -> LaneCandleLifecycle:
    return LaneCandleLifecycle(**_payload_kwargs(payload, LaneCandleLifecycle))


def _market_regime_payload(context: MarketRegimeContext) -> dict[str, Any]:
    return {
        "context_id": context.context_id,
        "symbol": context.symbol.upper(),
        "timeframe": context.timeframe,
        "observed_at": context.observed_at,
        "capability": context.capability.value,
        "rule_id": context.rule_id,
        "version": context.version,
        "label": None if context.label is None else context.label.value,
        "input_snapshot": context.input_snapshot or {},
        "normalized_features": context.normalized_features or {},
        "thresholds": context.thresholds or {},
        "reason": context.reason,
    }


def _market_regime_from_payload(payload: dict[str, Any]) -> MarketRegimeContext:
    label = payload.get("label")
    return MarketRegimeContext(
        context_id=str(payload["context_id"]),
        symbol=str(payload["symbol"]),
        timeframe=str(payload["timeframe"]),
        observed_at=str(payload["observed_at"]),
        capability=RegimeCapability(str(payload["capability"])),
        rule_id=str(payload["rule_id"]),
        version=str(payload["version"]),
        label=None if label is None else MarketRegimeLabel(str(label)),
        input_snapshot=dict(payload.get("input_snapshot") or {}),
        normalized_features=dict(payload.get("normalized_features") or {}),
        thresholds=dict(payload.get("thresholds") or {}),
        reason=None if payload.get("reason") is None else str(payload["reason"]),
    )


def _normalize_heartbeat(heartbeat: RuntimeHeartbeat) -> RuntimeHeartbeat:
    component = heartbeat.component.strip().lower()
    if not component or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789_-." for char in component):
        raise RuntimeStoreError("heartbeat component must be a stable identifier")
    status = heartbeat.status.strip().upper()
    if status not in {"RUNNING", "DEGRADED", "BLOCKED", "UNAVAILABLE"}:
        raise RuntimeStoreError("heartbeat status must be RUNNING, DEGRADED, BLOCKED, or UNAVAILABLE")
    return RuntimeHeartbeat(
        component=component,
        status=status,
        observed_at=heartbeat.observed_at,
        detail=heartbeat.detail,
        metadata=heartbeat.metadata or {},
    )


def _heartbeat_payload(heartbeat: RuntimeHeartbeat) -> dict[str, Any]:
    return heartbeat.__dict__.copy()


def _heartbeat_from_payload(payload: dict[str, Any]) -> RuntimeHeartbeat:
    return RuntimeHeartbeat(
        component=str(payload["component"]),
        status=str(payload["status"]),
        observed_at=str(payload["observed_at"]),
        detail=None if payload.get("detail") is None else str(payload["detail"]),
        metadata=dict(payload.get("metadata") or {}),
    )


def _payload_kwargs(payload: dict[str, Any], model: type) -> dict[str, Any]:
    return {key: payload.get(key) for key in model.__dataclass_fields__}
