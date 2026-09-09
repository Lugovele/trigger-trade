"""SQLite runtime checkpoint state for continuous paper trading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3

from triggertrade.market_data import MarketRegimeContext, MarketRegimeLabel, RegimeCapability


@dataclass(frozen=True)
class RuntimeCheckpoint:
    symbol: str
    timeframe: str
    last_processed_candle_id: str
    last_processed_candle_open_time: str
    last_processed_at: str
    runtime_version: str


@dataclass(frozen=True)
class CandleLifecycle:
    candle_id: str
    symbol: str
    timeframe: str
    candle_open_time: str
    status: str
    signal_id: str | None = None
    intent_id: str | None = None
    risk_decision_id: str | None = None
    execution_intent_id: str | None = None
    processed_at: str | None = None
    error: str | None = None
    regime_context_id: str | None = None
    regime_state: str | None = None
    rules_version_id: str | None = None
    rules_evaluation: dict[str, str | None] | None = None


@dataclass(frozen=True)
class LaneRuntimeCheckpoint:
    lane: str
    symbol: str
    timeframe: str
    trigger_set_id: str
    trigger_set_version: str
    last_processed_candle_id: str
    last_processed_candle_open_time: str
    last_processed_at: str
    runtime_version: str


@dataclass(frozen=True)
class LaneCandleLifecycle:
    lane: str
    symbol: str
    timeframe: str
    candle_id: str
    candle_open_time: str
    trigger_set_id: str
    trigger_set_version: str
    status: str
    signal_id: str | None = None
    intent_id: str | None = None
    risk_decision_id: str | None = None
    execution_intent_id: str | None = None
    processed_at: str | None = None
    error: str | None = None
    regime_context_id: str | None = None
    regime_state: str | None = None
    rules_version_id: str | None = None
    rules_evaluation: dict[str, str | None] | None = None


@dataclass(frozen=True)
class RuntimeHeartbeat:
    component: str
    status: str
    observed_at: str
    detail: str | None = None
    metadata: dict[str, str | None] | None = None


class RuntimeStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def checkpoint(self, checkpoint: RuntimeCheckpoint) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO runtime_candle_state (
                    symbol, timeframe, last_processed_candle_id,
                    last_processed_candle_open_time, last_processed_at, runtime_version
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.symbol,
                    checkpoint.timeframe,
                    checkpoint.last_processed_candle_id,
                    checkpoint.last_processed_candle_open_time,
                    checkpoint.last_processed_at,
                    checkpoint.runtime_version,
                ),
            )

    def get_checkpoint(self, symbol: str, timeframe: str) -> RuntimeCheckpoint | None:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM runtime_candle_state WHERE symbol = ? AND timeframe = ?",
                (symbol, timeframe),
            ).fetchall()
        if len(rows) > 1:
            raise RuntimeStoreError("ambiguous runtime checkpoint state")
        return None if not rows else _row_to_checkpoint(rows[0])

    def save_lifecycle(self, lifecycle: CandleLifecycle) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO runtime_candle_lifecycles (
                    candle_id, symbol, timeframe, candle_open_time, status,
                    signal_id, intent_id, risk_decision_id, execution_intent_id,
                    processed_at, error, regime_context_id, regime_state,
                    rules_version_id, rules_evaluation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lifecycle.candle_id,
                    lifecycle.symbol,
                    lifecycle.timeframe,
                    lifecycle.candle_open_time,
                    lifecycle.status,
                    lifecycle.signal_id,
                    lifecycle.intent_id,
                    lifecycle.risk_decision_id,
                    lifecycle.execution_intent_id,
                    lifecycle.processed_at,
                    lifecycle.error,
                    lifecycle.regime_context_id,
                    lifecycle.regime_state,
                    lifecycle.rules_version_id,
                    json.dumps(lifecycle.rules_evaluation or {}, sort_keys=True),
                ),
            )

    def get_lifecycle(self, candle_id: str) -> CandleLifecycle | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM runtime_candle_lifecycles WHERE candle_id = ?",
                (candle_id,),
            ).fetchone()
        return None if row is None else _row_to_lifecycle(row)

    def processed_count(self, candle_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM runtime_candle_lifecycles WHERE candle_id = ?",
                (candle_id,),
            ).fetchone()
        return int(row[0])

    def lane_checkpoint(self, checkpoint: LaneRuntimeCheckpoint) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO runtime_lane_state (
                    lane, symbol, timeframe, trigger_set_id, trigger_set_version,
                    last_processed_candle_id, last_processed_candle_open_time,
                    last_processed_at, runtime_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.lane,
                    checkpoint.symbol,
                    checkpoint.timeframe,
                    checkpoint.trigger_set_id,
                    checkpoint.trigger_set_version,
                    checkpoint.last_processed_candle_id,
                    checkpoint.last_processed_candle_open_time,
                    checkpoint.last_processed_at,
                    checkpoint.runtime_version,
                ),
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
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT lane, symbol, timeframe, trigger_set_id, trigger_set_version,
                       last_processed_candle_id, last_processed_candle_open_time,
                       last_processed_at, runtime_version
                FROM runtime_lane_state
                WHERE lane = ? AND symbol = ? AND timeframe = ?
                  AND trigger_set_id = ? AND trigger_set_version = ?
                """,
                (lane, symbol, timeframe, trigger_set_id, trigger_set_version),
            ).fetchone()
        return None if row is None else _row_to_lane_checkpoint(row)

    def save_lane_lifecycle(self, lifecycle: LaneCandleLifecycle) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO runtime_lane_lifecycles (
                    lane, symbol, timeframe, candle_id, candle_open_time,
                    trigger_set_id, trigger_set_version, status, signal_id,
                    intent_id, risk_decision_id, execution_intent_id,
                    processed_at, error, regime_context_id, regime_state,
                    rules_version_id, rules_evaluation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lifecycle.lane,
                    lifecycle.symbol,
                    lifecycle.timeframe,
                    lifecycle.candle_id,
                    lifecycle.candle_open_time,
                    lifecycle.trigger_set_id,
                    lifecycle.trigger_set_version,
                    lifecycle.status,
                    lifecycle.signal_id,
                    lifecycle.intent_id,
                    lifecycle.risk_decision_id,
                    lifecycle.execution_intent_id,
                    lifecycle.processed_at,
                    lifecycle.error,
                    lifecycle.regime_context_id,
                    lifecycle.regime_state,
                    lifecycle.rules_version_id,
                    json.dumps(lifecycle.rules_evaluation or {}, sort_keys=True),
                ),
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
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT lane, symbol, timeframe, candle_id, candle_open_time,
                       trigger_set_id, trigger_set_version, status, signal_id,
                       intent_id, risk_decision_id, execution_intent_id,
                       processed_at, error, regime_context_id, regime_state,
                       rules_version_id, rules_evaluation
                FROM runtime_lane_lifecycles
                WHERE lane = ? AND symbol = ? AND timeframe = ? AND candle_id = ?
                  AND trigger_set_id = ? AND trigger_set_version = ?
                """,
                (lane, symbol, timeframe, candle_id, trigger_set_id, trigger_set_version),
            ).fetchone()
        return None if row is None else _row_to_lane_lifecycle(row)

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
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) FROM runtime_lane_lifecycles
                WHERE lane = ? AND symbol = ? AND timeframe = ? AND candle_id = ?
                  AND trigger_set_id = ? AND trigger_set_version = ?
                """,
                (lane, symbol, timeframe, candle_id, trigger_set_id, trigger_set_version),
            ).fetchone()
        return int(row[0])

    def save_market_regime(self, context: MarketRegimeContext) -> None:
        label = None if context.label is None else context.label.value
        with self._connect() as conn:
            existing = conn.execute(
                """
                SELECT context_id, capability, label, input_snapshot, normalized_features, thresholds, reason
                FROM market_regime_evaluations
                WHERE symbol = ? AND timeframe = ? AND observed_at = ?
                  AND rule_id = ? AND version = ?
                """,
                (context.symbol, context.timeframe, context.observed_at, context.rule_id, context.version),
            ).fetchone()
            payload = (
                context.context_id,
                context.capability.value,
                label,
                json.dumps(context.input_snapshot or {}, sort_keys=True),
                json.dumps(context.normalized_features or {}, sort_keys=True),
                json.dumps(context.thresholds or {}, sort_keys=True),
                context.reason,
            )
            if existing is not None and tuple(existing) != payload:
                raise RuntimeStoreError("market regime evaluation is immutable for its business key")
            conn.execute(
                """
                INSERT INTO market_regime_evaluations (
                    context_id, symbol, timeframe, observed_at, rule_id, version,
                    capability, label, input_snapshot, normalized_features,
                    thresholds, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, timeframe, observed_at, rule_id, version) DO NOTHING
                """,
                (
                    context.context_id,
                    context.symbol,
                    context.timeframe,
                    context.observed_at,
                    context.rule_id,
                    context.version,
                    payload[1],
                    label,
                    payload[3],
                    payload[4],
                    payload[5],
                    context.reason,
                ),
            )

    def get_market_regime(self, context_id: str) -> MarketRegimeContext | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM market_regime_evaluations WHERE context_id = ?",
                (context_id,),
            ).fetchone()
        return None if row is None else _row_to_market_regime(row)

    def latest_market_regime(self, symbol: str, timeframe: str) -> MarketRegimeContext | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM market_regime_evaluations
                WHERE symbol = ? AND timeframe = ?
                ORDER BY observed_at DESC
                LIMIT 1
                """,
                (symbol.upper(), timeframe),
            ).fetchone()
        return None if row is None else _row_to_market_regime(row)

    def record_heartbeat(self, heartbeat: RuntimeHeartbeat) -> RuntimeHeartbeat:
        component = heartbeat.component.strip().lower()
        if not component or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789_-." for char in component):
            raise RuntimeStoreError("heartbeat component must be a stable identifier")
        status = heartbeat.status.strip().upper()
        if status not in {"RUNNING", "DEGRADED", "BLOCKED", "UNAVAILABLE"}:
            raise RuntimeStoreError("heartbeat status must be RUNNING, DEGRADED, BLOCKED, or UNAVAILABLE")
        normalized = RuntimeHeartbeat(
            component=component,
            status=status,
            observed_at=heartbeat.observed_at,
            detail=heartbeat.detail,
            metadata=heartbeat.metadata or {},
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runtime_heartbeats (
                    component, status, observed_at, detail, metadata
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(component) DO UPDATE SET
                    status = excluded.status,
                    observed_at = excluded.observed_at,
                    detail = excluded.detail,
                    metadata = excluded.metadata
                """,
                (
                    normalized.component,
                    normalized.status,
                    normalized.observed_at,
                    normalized.detail,
                    json.dumps(normalized.metadata or {}, sort_keys=True),
                ),
            )
        return normalized

    def list_heartbeats(self) -> tuple[RuntimeHeartbeat, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT component, status, observed_at, detail, metadata
                FROM runtime_heartbeats
                ORDER BY component
                """
            ).fetchall()
        return tuple(_row_to_heartbeat(row) for row in rows)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_candle_state (
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    last_processed_candle_id TEXT NOT NULL,
                    last_processed_candle_open_time TEXT NOT NULL,
                    last_processed_at TEXT NOT NULL,
                    runtime_version TEXT NOT NULL,
                    PRIMARY KEY (symbol, timeframe)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_candle_lifecycles (
                    candle_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    candle_open_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    signal_id TEXT,
                    intent_id TEXT,
                    risk_decision_id TEXT,
                    execution_intent_id TEXT,
                    processed_at TEXT,
                    error TEXT
                )
                """
            )
            _add_column_if_missing(conn, "runtime_candle_lifecycles", "regime_context_id", "TEXT")
            _add_column_if_missing(conn, "runtime_candle_lifecycles", "regime_state", "TEXT")
            _add_column_if_missing(conn, "runtime_candle_lifecycles", "rules_version_id", "TEXT")
            _add_column_if_missing(conn, "runtime_candle_lifecycles", "rules_evaluation", "TEXT")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_lane_state (
                    lane TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    trigger_set_id TEXT NOT NULL,
                    trigger_set_version TEXT NOT NULL,
                    last_processed_candle_id TEXT NOT NULL,
                    last_processed_candle_open_time TEXT NOT NULL,
                    last_processed_at TEXT NOT NULL,
                    runtime_version TEXT NOT NULL,
                    PRIMARY KEY (lane, symbol, timeframe, trigger_set_id, trigger_set_version)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_lane_lifecycles (
                    lane TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    candle_id TEXT NOT NULL,
                    candle_open_time TEXT NOT NULL,
                    trigger_set_id TEXT NOT NULL,
                    trigger_set_version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    signal_id TEXT,
                    intent_id TEXT,
                    risk_decision_id TEXT,
                    execution_intent_id TEXT,
                    processed_at TEXT,
                    error TEXT,
                    regime_context_id TEXT,
                    regime_state TEXT,
                    rules_version_id TEXT,
                    rules_evaluation TEXT,
                    PRIMARY KEY (lane, symbol, timeframe, candle_id, trigger_set_id, trigger_set_version)
                )
                """
            )
            _add_column_if_missing(conn, "runtime_lane_lifecycles", "regime_context_id", "TEXT")
            _add_column_if_missing(conn, "runtime_lane_lifecycles", "regime_state", "TEXT")
            _add_column_if_missing(conn, "runtime_lane_lifecycles", "rules_version_id", "TEXT")
            _add_column_if_missing(conn, "runtime_lane_lifecycles", "rules_evaluation", "TEXT")
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_runtime_lane_lifecycles_processed
                ON runtime_lane_lifecycles(processed_at DESC)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_regime_evaluations (
                    context_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    label TEXT,
                    input_snapshot TEXT NOT NULL,
                    normalized_features TEXT NOT NULL,
                    thresholds TEXT NOT NULL,
                    reason TEXT,
                    UNIQUE (symbol, timeframe, observed_at, rule_id, version)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_heartbeats (
                    component TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    detail TEXT,
                    metadata TEXT NOT NULL DEFAULT '{}'
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


class RuntimeStoreError(RuntimeError):
    pass


def _row_to_checkpoint(row: sqlite3.Row) -> RuntimeCheckpoint:
    return RuntimeCheckpoint(
        symbol=row["symbol"],
        timeframe=row["timeframe"],
        last_processed_candle_id=row["last_processed_candle_id"],
        last_processed_candle_open_time=row["last_processed_candle_open_time"],
        last_processed_at=row["last_processed_at"],
        runtime_version=row["runtime_version"],
    )


def _row_to_lifecycle(row: sqlite3.Row) -> CandleLifecycle:
    return CandleLifecycle(
        candle_id=row["candle_id"],
        symbol=row["symbol"],
        timeframe=row["timeframe"],
        candle_open_time=row["candle_open_time"],
        status=row["status"],
        signal_id=row["signal_id"],
        intent_id=row["intent_id"],
        risk_decision_id=row["risk_decision_id"],
        execution_intent_id=row["execution_intent_id"],
        processed_at=row["processed_at"],
        error=row["error"],
        regime_context_id=_optional(row, "regime_context_id"),
        regime_state=_optional(row, "regime_state"),
        rules_version_id=_optional(row, "rules_version_id"),
        rules_evaluation=_json_optional(row, "rules_evaluation"),
    )


def _row_to_lane_checkpoint(row: sqlite3.Row) -> LaneRuntimeCheckpoint:
    return LaneRuntimeCheckpoint(
        lane=row["lane"],
        symbol=row["symbol"],
        timeframe=row["timeframe"],
        trigger_set_id=row["trigger_set_id"],
        trigger_set_version=row["trigger_set_version"],
        last_processed_candle_id=row["last_processed_candle_id"],
        last_processed_candle_open_time=row["last_processed_candle_open_time"],
        last_processed_at=row["last_processed_at"],
        runtime_version=row["runtime_version"],
    )


def _row_to_lane_lifecycle(row: sqlite3.Row) -> LaneCandleLifecycle:
    return LaneCandleLifecycle(
        lane=row["lane"],
        symbol=row["symbol"],
        timeframe=row["timeframe"],
        candle_id=row["candle_id"],
        candle_open_time=row["candle_open_time"],
        trigger_set_id=row["trigger_set_id"],
        trigger_set_version=row["trigger_set_version"],
        status=row["status"],
        signal_id=row["signal_id"],
        intent_id=row["intent_id"],
        risk_decision_id=row["risk_decision_id"],
        execution_intent_id=row["execution_intent_id"],
        processed_at=row["processed_at"],
        error=row["error"],
        regime_context_id=_optional(row, "regime_context_id"),
        regime_state=_optional(row, "regime_state"),
        rules_version_id=_optional(row, "rules_version_id"),
        rules_evaluation=_json_optional(row, "rules_evaluation"),
    )


def _row_to_market_regime(row: sqlite3.Row) -> MarketRegimeContext:
    label = row["label"]
    return MarketRegimeContext(
        context_id=row["context_id"],
        symbol=row["symbol"],
        timeframe=row["timeframe"],
        observed_at=row["observed_at"],
        capability=RegimeCapability(row["capability"]),
        rule_id=row["rule_id"],
        version=row["version"],
        label=None if label is None else MarketRegimeLabel(label),
        input_snapshot=json.loads(row["input_snapshot"]),
        normalized_features=json.loads(row["normalized_features"]),
        thresholds=json.loads(row["thresholds"]),
        reason=row["reason"],
    )


def _row_to_heartbeat(row: sqlite3.Row) -> RuntimeHeartbeat:
    return RuntimeHeartbeat(
        component=row["component"],
        status=row["status"],
        observed_at=row["observed_at"],
        detail=row["detail"],
        metadata=_json_optional(row, "metadata") or {},
    )


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _optional(row: sqlite3.Row, key: str):
    return row[key] if key in row.keys() else None


def _json_optional(row: sqlite3.Row, key: str) -> dict[str, str | None] | None:
    raw = _optional(row, key)
    if not raw:
        return None
    return json.loads(raw)
