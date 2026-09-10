"""Persistent local operator trading state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
import re
import sqlite3

from triggertrade.persistence.trace_store import TraceStore


_SECRET_RE = re.compile(
    r"(api[_-]?key|api[_-]?secret|authorization|bearer|cookie|csrf|session|token|password|credential|signature|\.env)",
    re.I,
)


class TradingState(StrEnum):
    TRADING_ENABLED = "TRADING_ENABLED"
    TRADING_PAUSED = "TRADING_PAUSED"


@dataclass(frozen=True)
class OperatorTradingState:
    state: TradingState
    changed_at: str
    source: str
    reason: str | None = None


@dataclass(frozen=True)
class OperatorActionAudit:
    action: str
    changed_at: str
    target: str | None
    result: str
    source: str
    error: str | None = None


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
        self._audit_operator_event(
            event_type="OPERATOR_TRADING_STATE_CHANGED",
            action=state.value,
            target="ACTIVE",
            result=state.value,
            source=source,
            changed_at=changed_at,
            error=None,
            metadata={"previous_state": previous.state.value, "new_state": state.value, "reason": reason},
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

    def record_operator_action(
        self,
        *,
        action: str,
        target: str | None,
        result: str,
        source: str = "local_dashboard",
        error: str | None = None,
        changed_at: str | None = None,
    ) -> OperatorActionAudit:
        changed_at = changed_at or _now()
        clean_error = _safe_error(error)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO operator_action_audit (
                    changed_at, action, target, result, source, error
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (changed_at, action, target, result, source, clean_error),
            )
        self._audit_operator_event(
            event_type=f"OPERATOR_{action.upper()}",
            action=action,
            target=target,
            result=result,
            source=source,
            changed_at=changed_at,
            error=clean_error,
            metadata={"action": action, "target": target},
        )
        return OperatorActionAudit(action, changed_at, target, result, source, clean_error)

    def operator_action_rows(self, *, limit: int | None = None) -> tuple[OperatorActionAudit, ...]:
        safe_limit = None if limit is None else max(1, min(int(limit), 500))
        limit_clause = "" if safe_limit is None else " LIMIT ?"
        params = () if safe_limit is None else (safe_limit,)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT changed_at, action, target, result, source, error
                FROM operator_action_audit
                ORDER BY changed_at DESC, id DESC
                {limit_clause}
                """,
                params,
            ).fetchall()
        return tuple(
            OperatorActionAudit(
                action=row["action"],
                changed_at=row["changed_at"],
                target=row["target"],
                result=row["result"],
                source=row["source"],
                error=row["error"],
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
                CREATE TABLE IF NOT EXISTS operator_action_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    changed_at TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT,
                    result TEXT NOT NULL,
                    source TEXT NOT NULL,
                    error TEXT
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

    def _audit_operator_event(
        self,
        *,
        event_type: str,
        action: str,
        target: str | None,
        result: str,
        source: str,
        changed_at: str,
        error: str | None,
        metadata: dict,
    ) -> None:
        try:
            TraceStore(self.path).record_audit_event(
                event_type=event_type,
                source_type="USER_OPERATOR",
                source_id=source,
                scope="ACTIVE",
                entity_type="operator_action",
                entity_id=f"{action}:{target or 'ACTIVE'}:{changed_at}",
                related_entity_type=None if target is None else "target",
                related_entity_id=target,
                result=result,
                reason_code=error,
                safe_metadata=metadata,
                created_at=changed_at,
            )
        except Exception:
            return


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _safe_error(value: str | None) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).replace("\x00", "").split())[:500]
    return "[redacted]" if _SECRET_RE.search(text) else text
