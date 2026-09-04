"""SQLite runtime checkpoint state for continuous paper trading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3


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
                    processed_at, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    )
