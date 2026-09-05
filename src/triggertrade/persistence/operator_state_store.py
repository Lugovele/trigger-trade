"""Persistent local operator trading state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
import sqlite3


class TradingState(StrEnum):
    TRADING_ENABLED = "TRADING_ENABLED"
    TRADING_PAUSED = "TRADING_PAUSED"


@dataclass(frozen=True)
class OperatorTradingState:
    state: TradingState
    changed_at: str
    source: str
    reason: str | None = None


class OperatorStateStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def get_trading_state(self) -> OperatorTradingState:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT state, changed_at, source, reason
                FROM operator_trading_state
                WHERE scope = 'ACTIVE'
                """
            ).fetchone()
        if row is None:
            return OperatorTradingState(TradingState.TRADING_ENABLED, _now(), "system_default")
        return OperatorTradingState(
            state=TradingState(row["state"]),
            changed_at=row["changed_at"],
            source=row["source"],
            reason=row["reason"],
        )

    def pause(self, *, changed_at: str | None = None, source: str = "local_dashboard", reason: str | None = None) -> OperatorTradingState:
        return self.set_trading_state(TradingState.TRADING_PAUSED, changed_at=changed_at, source=source, reason=reason)

    def resume(self, *, changed_at: str | None = None, source: str = "local_dashboard", reason: str | None = None) -> OperatorTradingState:
        return self.set_trading_state(TradingState.TRADING_ENABLED, changed_at=changed_at, source=source, reason=reason)

    def set_trading_state(
        self,
        state: TradingState,
        *,
        changed_at: str | None = None,
        source: str = "local_dashboard",
        reason: str | None = None,
    ) -> OperatorTradingState:
        changed_at = changed_at or _now()
        previous = self.get_trading_state()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO operator_trading_state (
                    scope, state, changed_at, source, reason
                ) VALUES ('ACTIVE', ?, ?, ?, ?)
                """,
                (state.value, changed_at, source, reason),
            )
            conn.execute(
                """
                INSERT INTO operator_trading_state_audit (
                    changed_at, previous_state, new_state, source, reason
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (changed_at, previous.state.value, state.value, source, reason),
            )
        return OperatorTradingState(state, changed_at, source, reason)

    def audit_rows(self) -> tuple[OperatorTradingState, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT new_state AS state, changed_at, source, reason
                FROM operator_trading_state_audit
                ORDER BY changed_at DESC, id DESC
                """
            ).fetchall()
        return tuple(
            OperatorTradingState(
                state=TradingState(row["state"]),
                changed_at=row["changed_at"],
                source=row["source"],
                reason=row["reason"],
            )
            for row in rows
        )

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS operator_trading_state (
                    scope TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    changed_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    reason TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS operator_trading_state_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    changed_at TEXT NOT NULL,
                    previous_state TEXT NOT NULL,
                    new_state TEXT NOT NULL,
                    source TEXT NOT NULL,
                    reason TEXT
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


def _now() -> str:
    return datetime.now(UTC).isoformat()
