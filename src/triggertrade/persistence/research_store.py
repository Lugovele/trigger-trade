"""Persistent Research orchestration records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
from typing import Any


RESEARCH_SCHEMA_VERSION = "research-v1"


class ResearchStoreError(RuntimeError):
    pass


class ResearchStatus(StrEnum):
    DRAFT = "DRAFT"
    BACKTEST_READY = "BACKTEST_READY"
    DEMO_RUNNING = "DEMO_RUNNING"
    DEMO_STOPPED = "DEMO_STOPPED"
    DECISION_NEEDED = "DECISION_NEEDED"
    ARCHIVED = "ARCHIVED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class ResearchDecision(StrEnum):
    NONE = "NONE"
    ARCHIVE = "ARCHIVE"
    MAKE_ACTIVE_BLOCKED = "MAKE_ACTIVE_BLOCKED"


class ResearchBacktestStatus(StrEnum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    COMPLETED_NO_TRADES = "COMPLETED_NO_TRADES"
    FAILED = "FAILED"


class ResearchDemoStatus(StrEnum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ResearchRecord:
    research_id: str
    created_at: str
    updated_at: str
    status: ResearchStatus
    set_id: str
    set_version: str
    rules_version_id: str
    rules_display_version: str
    selected_backtest_run_id: str | None
    selected_demo_run_id: str | None
    decision: ResearchDecision
    decision_at: str | None
    archived_at: str | None
    made_active_at: str | None
    created_source: str
    schema_version: str


@dataclass(frozen=True)
class ResearchBacktestRunRecord:
    research_id: str
    run_id: str
    created_at: str
    updated_at: str
    status: ResearchBacktestStatus
    period_start: str
    period_end: str
    timeframe: str
    engine_run_id: str | None
    selected_for_use: bool
    metrics: dict[str, Any]
    unavailable_reason: str | None


@dataclass(frozen=True)
class ResearchDemoRunRecord:
    research_id: str
    run_id: str
    created_at: str
    updated_at: str
    status: ResearchDemoStatus
    started_at: str | None
    stopped_at: str | None
    execution_scope_id: str | None
    account_scope: str | None
    selected_for_use: bool
    metrics: dict[str, Any]
    blocked_reason: str | None


_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,160}$")
_DISALLOWED_SELECTORS = {"current", "latest", "active", "..", ".", ""}


class ResearchStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def create_research(
        self,
        *,
        set_id: str,
        set_version: str,
        rules_version_id: str,
        rules_display_version: str,
        created_source: str,
        created_at: str | None = None,
    ) -> tuple[ResearchRecord, bool]:
        _validate_id(set_id, "set_id")
        _validate_id(set_version, "set_version")
        _validate_id(rules_version_id, "rules_version_id")
        created_at = created_at or _now()
        research_id = _research_id(set_id, set_version, rules_version_id)
        with self._connect() as conn:
            existing = self._get_research(conn, research_id)
            if existing is not None:
                return existing, False
            conn.execute(
                """
                INSERT INTO research_entities (
                    research_id, created_at, updated_at, status, set_id, set_version,
                    rules_version_id, rules_display_version, selected_backtest_run_id,
                    selected_demo_run_id, decision, decision_at, archived_at,
                    made_active_at, created_source, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, NULL, NULL, NULL, ?, ?)
                """,
                (
                    research_id,
                    created_at,
                    created_at,
                    ResearchStatus.DRAFT.value,
                    set_id,
                    set_version,
                    rules_version_id,
                    _clean_text(rules_display_version, "rules_display_version", 40),
                    ResearchDecision.NONE.value,
                    _clean_text(created_source, "created_source", 80),
                    RESEARCH_SCHEMA_VERSION,
                ),
            )
            return self._get_research(conn, research_id), True  # type: ignore[return-value]

    def list_research(self, *, limit: int = 50) -> tuple[ResearchRecord, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM research_entities
                ORDER BY updated_at DESC, research_id DESC
                LIMIT ?
                """,
                (max(1, min(int(limit), 100)),),
            ).fetchall()
        return tuple(_research_from_row(row) for row in rows)

    def get_research(self, research_id: str) -> ResearchRecord | None:
        _validate_id(research_id, "research_id")
        with self._connect() as conn:
            return self._get_research(conn, research_id)

    def add_backtest_run(
        self,
        *,
        research_id: str,
        period_start: str,
        period_end: str,
        timeframe: str,
        status: ResearchBacktestStatus,
        engine_run_id: str | None = None,
        metrics: dict[str, Any] | None = None,
        unavailable_reason: str | None = None,
        created_at: str | None = None,
    ) -> ResearchBacktestRunRecord:
        _validate_id(research_id, "research_id")
        if engine_run_id is not None:
            _validate_id(engine_run_id, "engine_run_id")
        created_at = created_at or _now()
        run_id = _run_id("rbt", research_id, period_start, period_end, engine_run_id or status.value, created_at)
        with self._connect() as conn:
            self._ensure_mutable_research(conn, research_id)
            conn.execute(
                """
                INSERT INTO research_backtest_runs (
                    research_id, run_id, created_at, updated_at, status, period_start,
                    period_end, timeframe, engine_run_id, selected_for_use,
                    metrics_json, unavailable_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    research_id,
                    run_id,
                    created_at,
                    created_at,
                    status.value,
                    _clean_text(period_start, "period_start", 80),
                    _clean_text(period_end, "period_end", 80),
                    _clean_text(timeframe, "timeframe", 20),
                    engine_run_id,
                    json.dumps(_jsonable(metrics or {}), sort_keys=True),
                    None if unavailable_reason is None else _clean_text(unavailable_reason, "unavailable_reason", 240),
                ),
            )
            self._update_research_status(conn, research_id, _research_status_after_backtest(status), created_at)
        return self.get_backtest_run(research_id, run_id)  # type: ignore[return-value]

    def get_backtest_run(self, research_id: str, run_id: str) -> ResearchBacktestRunRecord | None:
        _validate_id(research_id, "research_id")
        _validate_id(run_id, "run_id")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM research_backtest_runs WHERE research_id = ? AND run_id = ?",
                (research_id, run_id),
            ).fetchone()
        return None if row is None else _backtest_from_row(row)

    def list_backtest_runs(self, research_id: str) -> tuple[ResearchBacktestRunRecord, ...]:
        _validate_id(research_id, "research_id")
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM research_backtest_runs
                WHERE research_id = ?
                ORDER BY created_at DESC, run_id DESC
                """,
                (research_id,),
            ).fetchall()
        return tuple(_backtest_from_row(row) for row in rows)

    def select_backtest_run(self, research_id: str, run_id: str, *, selected_at: str | None = None) -> ResearchRecord:
        selected_at = selected_at or _now()
        with self._connect() as conn:
            self._ensure_mutable_research(conn, _checked(research_id, "research_id"))
            run = conn.execute(
                "SELECT status FROM research_backtest_runs WHERE research_id = ? AND run_id = ?",
                (research_id, _checked(run_id, "run_id")),
            ).fetchone()
            if run is None:
                raise ResearchStoreError("backtest run id not found for research")
            if run["status"] not in {ResearchBacktestStatus.COMPLETED.value, ResearchBacktestStatus.COMPLETED_NO_TRADES.value}:
                raise ResearchStoreError("only completed backtest runs can be selected")
            conn.execute("UPDATE research_backtest_runs SET selected_for_use = 0 WHERE research_id = ?", (research_id,))
            conn.execute(
                "UPDATE research_backtest_runs SET selected_for_use = 1, updated_at = ? WHERE research_id = ? AND run_id = ?",
                (selected_at, research_id, run_id),
            )
            conn.execute(
                """
                UPDATE research_entities
                SET selected_backtest_run_id = ?, status = ?, updated_at = ?
                WHERE research_id = ?
                """,
                (run_id, ResearchStatus.BACKTEST_READY.value, selected_at, research_id),
            )
            return self._get_research(conn, research_id)  # type: ignore[return-value]

    def add_demo_run(
        self,
        *,
        research_id: str,
        status: ResearchDemoStatus,
        started_at: str | None = None,
        stopped_at: str | None = None,
        execution_scope_id: str | None = None,
        account_scope: str | None = None,
        metrics: dict[str, Any] | None = None,
        blocked_reason: str | None = None,
        created_at: str | None = None,
    ) -> ResearchDemoRunRecord:
        _validate_id(research_id, "research_id")
        created_at = created_at or _now()
        run_id = _run_id("rdm", research_id, status.value, started_at or "", blocked_reason or "", created_at)
        with self._connect() as conn:
            self._ensure_mutable_research(conn, research_id)
            conn.execute(
                """
                INSERT INTO research_demo_runs (
                    research_id, run_id, created_at, updated_at, status, started_at,
                    stopped_at, execution_scope_id, account_scope, selected_for_use,
                    metrics_json, blocked_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    research_id,
                    run_id,
                    created_at,
                    created_at,
                    status.value,
                    started_at,
                    stopped_at,
                    None if execution_scope_id is None else _clean_text(execution_scope_id, "execution_scope_id", 160),
                    None if account_scope is None else _clean_text(account_scope, "account_scope", 160),
                    json.dumps(_jsonable(metrics or {}), sort_keys=True),
                    None if blocked_reason is None else _clean_text(blocked_reason, "blocked_reason", 240),
                ),
            )
            self._update_research_status(conn, research_id, _research_status_after_demo(status), created_at)
        return self.get_demo_run(research_id, run_id)  # type: ignore[return-value]

    def get_demo_run(self, research_id: str, run_id: str) -> ResearchDemoRunRecord | None:
        _validate_id(research_id, "research_id")
        _validate_id(run_id, "run_id")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM research_demo_runs WHERE research_id = ? AND run_id = ?",
                (research_id, run_id),
            ).fetchone()
        return None if row is None else _demo_from_row(row)

    def list_demo_runs(self, research_id: str) -> tuple[ResearchDemoRunRecord, ...]:
        _validate_id(research_id, "research_id")
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM research_demo_runs
                WHERE research_id = ?
                ORDER BY created_at DESC, run_id DESC
                """,
                (research_id,),
            ).fetchall()
        return tuple(_demo_from_row(row) for row in rows)

    def stop_demo_run(self, research_id: str, run_id: str, *, stopped_at: str | None = None) -> ResearchDemoRunRecord:
        stopped_at = stopped_at or _now()
        with self._connect() as conn:
            self._ensure_mutable_research(conn, _checked(research_id, "research_id"))
            row = conn.execute(
                "SELECT status FROM research_demo_runs WHERE research_id = ? AND run_id = ?",
                (research_id, _checked(run_id, "run_id")),
            ).fetchone()
            if row is None:
                raise ResearchStoreError("demo run id not found for research")
            if row["status"] == ResearchDemoStatus.RUNNING.value:
                conn.execute(
                    """
                    UPDATE research_demo_runs
                    SET status = ?, stopped_at = ?, updated_at = ?
                    WHERE research_id = ? AND run_id = ?
                    """,
                    (ResearchDemoStatus.STOPPED.value, stopped_at, stopped_at, research_id, run_id),
                )
                self._update_research_status(conn, research_id, ResearchStatus.DEMO_STOPPED, stopped_at)
        return self.get_demo_run(research_id, run_id)  # type: ignore[return-value]

    def select_demo_run(self, research_id: str, run_id: str, *, selected_at: str | None = None) -> ResearchRecord:
        selected_at = selected_at or _now()
        with self._connect() as conn:
            self._ensure_mutable_research(conn, _checked(research_id, "research_id"))
            run = conn.execute(
                "SELECT status FROM research_demo_runs WHERE research_id = ? AND run_id = ?",
                (research_id, _checked(run_id, "run_id")),
            ).fetchone()
            if run is None:
                raise ResearchStoreError("demo run id not found for research")
            if run["status"] != ResearchDemoStatus.STOPPED.value:
                raise ResearchStoreError("only stopped demo runs can be selected")
            conn.execute("UPDATE research_demo_runs SET selected_for_use = 0 WHERE research_id = ?", (research_id,))
            conn.execute(
                "UPDATE research_demo_runs SET selected_for_use = 1, updated_at = ? WHERE research_id = ? AND run_id = ?",
                (selected_at, research_id, run_id),
            )
            conn.execute(
                """
                UPDATE research_entities
                SET selected_demo_run_id = ?, status = ?, updated_at = ?
                WHERE research_id = ?
                """,
                (run_id, ResearchStatus.DECISION_NEEDED.value, selected_at, research_id),
            )
            return self._get_research(conn, research_id)  # type: ignore[return-value]

    def archive_research(self, research_id: str, *, archived_at: str | None = None) -> ResearchRecord:
        archived_at = archived_at or _now()
        with self._connect() as conn:
            if self._get_research(conn, _checked(research_id, "research_id")) is None:
                raise ResearchStoreError("research id not found")
            conn.execute(
                """
                UPDATE research_entities
                SET status = ?, decision = ?, decision_at = COALESCE(decision_at, ?),
                    archived_at = COALESCE(archived_at, ?), updated_at = ?
                WHERE research_id = ?
                """,
                (
                    ResearchStatus.ARCHIVED.value,
                    ResearchDecision.ARCHIVE.value,
                    archived_at,
                    archived_at,
                    archived_at,
                    research_id,
                ),
            )
            return self._get_research(conn, research_id)  # type: ignore[return-value]

    def record_make_active_blocked(self, research_id: str, *, reason: str, decided_at: str | None = None) -> ResearchRecord:
        decided_at = decided_at or _now()
        with self._connect() as conn:
            self._ensure_mutable_research(conn, _checked(research_id, "research_id"))
            conn.execute(
                """
                UPDATE research_entities
                SET decision = ?, decision_at = ?, updated_at = ?
                WHERE research_id = ?
                """,
                (ResearchDecision.MAKE_ACTIVE_BLOCKED.value, decided_at, decided_at, research_id),
            )
            conn.execute(
                """
                INSERT INTO research_decision_events(research_id, event_at, decision, reason)
                VALUES (?, ?, ?, ?)
                """,
                (research_id, decided_at, ResearchDecision.MAKE_ACTIVE_BLOCKED.value, _clean_text(reason, "reason", 240)),
            )
            return self._get_research(conn, research_id)  # type: ignore[return-value]

    def _get_research(self, conn: sqlite3.Connection, research_id: str) -> ResearchRecord | None:
        row = conn.execute("SELECT * FROM research_entities WHERE research_id = ?", (research_id,)).fetchone()
        return None if row is None else _research_from_row(row)

    def _ensure_mutable_research(self, conn: sqlite3.Connection, research_id: str) -> ResearchRecord:
        record = self._get_research(conn, research_id)
        if record is None:
            raise ResearchStoreError("research id not found")
        if record.status is ResearchStatus.ARCHIVED:
            raise ResearchStoreError("archived research is immutable")
        return record

    def _update_research_status(
        self,
        conn: sqlite3.Connection,
        research_id: str,
        status: ResearchStatus,
        updated_at: str,
    ) -> None:
        current = self._get_research(conn, research_id)
        if current is None or current.status is ResearchStatus.ARCHIVED:
            return
        conn.execute(
            "UPDATE research_entities SET status = ?, updated_at = ? WHERE research_id = ?",
            (status.value, updated_at, research_id),
        )

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS research_entities (
                    research_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    set_id TEXT NOT NULL,
                    set_version TEXT NOT NULL,
                    rules_version_id TEXT NOT NULL,
                    rules_display_version TEXT NOT NULL,
                    selected_backtest_run_id TEXT,
                    selected_demo_run_id TEXT,
                    decision TEXT NOT NULL,
                    decision_at TEXT,
                    archived_at TEXT,
                    made_active_at TEXT,
                    created_source TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    UNIQUE(set_id, set_version, rules_version_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS research_backtest_runs (
                    research_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    engine_run_id TEXT,
                    selected_for_use INTEGER NOT NULL DEFAULT 0,
                    metrics_json TEXT NOT NULL DEFAULT '{}',
                    unavailable_reason TEXT,
                    PRIMARY KEY (research_id, run_id),
                    FOREIGN KEY (research_id) REFERENCES research_entities(research_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS research_demo_runs (
                    research_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    stopped_at TEXT,
                    execution_scope_id TEXT,
                    account_scope TEXT,
                    selected_for_use INTEGER NOT NULL DEFAULT 0,
                    metrics_json TEXT NOT NULL DEFAULT '{}',
                    blocked_reason TEXT,
                    PRIMARY KEY (research_id, run_id),
                    FOREIGN KEY (research_id) REFERENCES research_entities(research_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS research_decision_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    research_id TEXT NOT NULL,
                    event_at TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reason TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_research_updated ON research_entities(updated_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_research_backtests_created ON research_backtest_runs(created_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_research_demo_created ON research_demo_runs(created_at DESC)")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


def _research_from_row(row: sqlite3.Row) -> ResearchRecord:
    return ResearchRecord(
        research_id=row["research_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        status=ResearchStatus(row["status"]),
        set_id=row["set_id"],
        set_version=row["set_version"],
        rules_version_id=row["rules_version_id"],
        rules_display_version=row["rules_display_version"],
        selected_backtest_run_id=row["selected_backtest_run_id"],
        selected_demo_run_id=row["selected_demo_run_id"],
        decision=ResearchDecision(row["decision"]),
        decision_at=row["decision_at"],
        archived_at=row["archived_at"],
        made_active_at=row["made_active_at"],
        created_source=row["created_source"],
        schema_version=row["schema_version"],
    )


def _backtest_from_row(row: sqlite3.Row) -> ResearchBacktestRunRecord:
    return ResearchBacktestRunRecord(
        research_id=row["research_id"],
        run_id=row["run_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        status=ResearchBacktestStatus(row["status"]),
        period_start=row["period_start"],
        period_end=row["period_end"],
        timeframe=row["timeframe"],
        engine_run_id=row["engine_run_id"],
        selected_for_use=bool(row["selected_for_use"]),
        metrics=_json_dict(row["metrics_json"]),
        unavailable_reason=row["unavailable_reason"],
    )


def _demo_from_row(row: sqlite3.Row) -> ResearchDemoRunRecord:
    return ResearchDemoRunRecord(
        research_id=row["research_id"],
        run_id=row["run_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        status=ResearchDemoStatus(row["status"]),
        started_at=row["started_at"],
        stopped_at=row["stopped_at"],
        execution_scope_id=row["execution_scope_id"],
        account_scope=row["account_scope"],
        selected_for_use=bool(row["selected_for_use"]),
        metrics=_json_dict(row["metrics_json"]),
        blocked_reason=row["blocked_reason"],
    )


def _research_status_after_backtest(status: ResearchBacktestStatus) -> ResearchStatus:
    if status in {ResearchBacktestStatus.COMPLETED, ResearchBacktestStatus.COMPLETED_NO_TRADES}:
        return ResearchStatus.BACKTEST_READY
    if status is ResearchBacktestStatus.FAILED:
        return ResearchStatus.FAILED
    return ResearchStatus.DRAFT


def _research_status_after_demo(status: ResearchDemoStatus) -> ResearchStatus:
    if status is ResearchDemoStatus.RUNNING:
        return ResearchStatus.DEMO_RUNNING
    if status is ResearchDemoStatus.STOPPED:
        return ResearchStatus.DEMO_STOPPED
    if status is ResearchDemoStatus.FAILED:
        return ResearchStatus.FAILED
    return ResearchStatus.BLOCKED


def _research_id(set_id: str, set_version: str, rules_version_id: str) -> str:
    digest = sha256("|".join([set_id, set_version, rules_version_id]).encode("utf-8")).hexdigest()[:20]
    return f"res-{digest}"


def _run_id(prefix: str, *parts: str) -> str:
    digest = sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _checked(value: str, field: str) -> str:
    _validate_id(value, field)
    return value


def _validate_id(value: str, field: str) -> None:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise ResearchStoreError(f"invalid {field}")
    if value.lower() in _DISALLOWED_SELECTORS or "/" in value or "\\" in value:
        raise ResearchStoreError(f"invalid {field}")


def _clean_text(value: str, field: str, max_len: int) -> str:
    text = " ".join(str(value).replace("\x00", "").split())
    if not text:
        raise ResearchStoreError(f"{field} is required")
    return text[:max_len]


def _json_dict(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if value.__class__.__name__ == "Decimal":
        return str(value)
    return value


def _now() -> str:
    return datetime.now(UTC).isoformat()
