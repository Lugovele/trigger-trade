"""SQLite persistence for immutable TradingRulesVersion records."""

from __future__ import annotations

from pathlib import Path
import sqlite3

from triggertrade.rules.trading import (
    TRADING_RULES_SCHEMA_VERSION,
    TRADING_RULES_SCOPE_LIVE,
    TradingRulesError,
    TradingRulesUsage,
    TradingRulesVersion,
    TradingRulesVersionDraft,
    draft_from_json,
    draft_to_json,
    rules_version_id,
    semantic_hash,
    validate_rules_draft,
)


class TradingRulesStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def bootstrap_initial(self, draft: TradingRulesVersionDraft, *, created_at: str, created_source: str) -> TradingRulesVersion:
        validate_rules_draft(draft)
        with self._connect() as conn:
            initial_hash = semantic_hash(draft)
            existing_v1 = conn.execute("SELECT * FROM trading_rules_versions WHERE version = ?", ("v1",)).fetchone()
            if existing_v1 is not None and existing_v1["config_hash"] != initial_hash:
                raise TradingRulesError("immutable v1 trading rules version conflicts with configured bootstrap")
            current = self._get_current(conn)
            if current is not None:
                return current
            if existing_v1 is not None:
                version = _row_to_version(existing_v1, existing_v1["rules_version_id"])
            else:
                version = self._insert_version(
                    conn,
                    draft,
                    version="v1",
                    created_at=created_at,
                    created_from_version_id=None,
                    created_source=created_source,
                    change_summary="Initial factual futures rules configuration",
                )
            conn.execute(
                """
                INSERT INTO trading_rules_current(scope, rules_version_id, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(scope) DO UPDATE SET rules_version_id = excluded.rules_version_id, updated_at = excluded.updated_at
                """,
                (TRADING_RULES_SCOPE_LIVE, version.rules_version_id, created_at),
            )
        return self.get_current()  # type: ignore[return-value]

    def create_next_version(
        self,
        draft: TradingRulesVersionDraft,
        *,
        created_from_version_id: str,
        created_source: str,
        change_summary: str,
        created_at: str,
    ) -> TradingRulesVersion:
        validate_rules_draft(draft)
        with self._connect() as conn:
            current = self._get_current(conn)
            if current is None or current.rules_version_id != created_from_version_id:
                raise TradingRulesError("current trading rules pointer changed; retry version creation")
            next_version = f"v{self._max_version_number(conn) + 1}"
            version = self._insert_version(
                conn,
                draft,
                version=next_version,
                created_at=created_at,
                created_from_version_id=created_from_version_id,
                created_source=created_source,
                change_summary=change_summary,
            )
            conn.execute(
                "UPDATE trading_rules_current SET rules_version_id = ?, updated_at = ? WHERE scope = ?",
                (version.rules_version_id, created_at, TRADING_RULES_SCOPE_LIVE),
            )
        return self.get_current()  # type: ignore[return-value]

    def get_current(self) -> TradingRulesVersion | None:
        with self._connect() as conn:
            return self._get_current(conn)

    def get_version(self, rules_version_id_or_version: str) -> TradingRulesVersion | None:
        with self._connect() as conn:
            current_id = self._current_id(conn)
            row = conn.execute(
                """
                SELECT * FROM trading_rules_versions
                WHERE rules_version_id = ? OR version = ?
                LIMIT 1
                """,
                (rules_version_id_or_version, rules_version_id_or_version),
            ).fetchone()
        return None if row is None else _row_to_version(row, current_id)

    def list_versions(self, *, limit: int | None = None) -> tuple[TradingRulesVersion, ...]:
        safe_limit = None if limit is None else max(1, min(int(limit), 500))
        limit_clause = "" if safe_limit is None else " LIMIT ?"
        params = () if safe_limit is None else (safe_limit,)
        with self._connect() as conn:
            current_id = self._current_id(conn)
            rows = conn.execute(
                f"SELECT * FROM trading_rules_versions ORDER BY version_number DESC, created_at DESC{limit_clause}",
                params,
            ).fetchall()
        return tuple(_row_to_version(row, current_id) for row in rows)

    def record_usage(self, usage: TradingRulesUsage) -> bool:
        with self._connect() as conn:
            existing = conn.execute(
                """
                SELECT 1 FROM trading_rules_usage
                WHERE rules_version_id = ? AND usage_type = ? AND entity_id = ? AND COALESCE(entity_version, '') = COALESCE(?, '')
                """,
                (usage.rules_version_id, usage.usage_type, usage.entity_id, usage.entity_version),
            ).fetchone()
            if existing is not None:
                return False
            conn.execute(
                """
                INSERT INTO trading_rules_usage(rules_version_id, usage_type, entity_id, entity_version, context, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (usage.rules_version_id, usage.usage_type, usage.entity_id, usage.entity_version, usage.context, usage.created_at),
            )
        return True

    def list_usage(self, rules_version_id: str) -> tuple[TradingRulesUsage, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM trading_rules_usage WHERE rules_version_id = ? ORDER BY created_at DESC",
                (rules_version_id,),
            ).fetchall()
        return tuple(
            TradingRulesUsage(row["rules_version_id"], row["usage_type"], row["entity_id"], row["entity_version"], row["context"], row["created_at"])
            for row in rows
        )

    def _insert_version(
        self,
        conn: sqlite3.Connection,
        draft: TradingRulesVersionDraft,
        *,
        version: str,
        created_at: str,
        created_from_version_id: str | None,
        created_source: str,
        change_summary: str,
    ) -> TradingRulesVersion:
        config_hash = semantic_hash(draft)
        version_id = rules_version_id(version, config_hash)
        values = (
            version_id,
            version,
            _version_number(version),
            created_at,
            created_from_version_id,
            created_source,
            change_summary,
            config_hash,
            TRADING_RULES_SCHEMA_VERSION,
            draft_to_json(draft),
        )
        existing = conn.execute("SELECT * FROM trading_rules_versions WHERE rules_version_id = ?", (version_id,)).fetchone()
        if existing is not None:
            if tuple(existing[key] for key in _VERSION_COLUMNS) != values:
                raise TradingRulesError("immutable trading rules version conflict")
            return _row_to_version(existing, self._current_id(conn))
        conn.execute(
            f"INSERT INTO trading_rules_versions ({', '.join(_VERSION_COLUMNS)}) VALUES ({', '.join('?' for _ in _VERSION_COLUMNS)})",
            values,
        )
        for coin in draft.coins:
            conn.execute(
                """
                INSERT INTO trading_rules_coin_rules(rules_version_id, symbol, enabled, max_allocation_pct)
                VALUES (?, ?, ?, ?)
                """,
                (version_id, coin.symbol, 1 if coin.enabled else 0, None if coin.max_allocation_pct is None else str(coin.max_allocation_pct)),
            )
        row = conn.execute("SELECT * FROM trading_rules_versions WHERE rules_version_id = ?", (version_id,)).fetchone()
        return _row_to_version(row, self._current_id(conn))

    def _get_current(self, conn: sqlite3.Connection) -> TradingRulesVersion | None:
        current_id = self._current_id(conn)
        if current_id is None:
            return None
        row = conn.execute("SELECT * FROM trading_rules_versions WHERE rules_version_id = ?", (current_id,)).fetchone()
        return None if row is None else _row_to_version(row, current_id)

    def _current_id(self, conn: sqlite3.Connection) -> str | None:
        row = conn.execute("SELECT rules_version_id FROM trading_rules_current WHERE scope = ?", (TRADING_RULES_SCOPE_LIVE,)).fetchone()
        return None if row is None else row["rules_version_id"]

    def _max_version_number(self, conn: sqlite3.Connection) -> int:
        row = conn.execute("SELECT MAX(version_number) AS max_version FROM trading_rules_versions").fetchone()
        return int(row["max_version"] or 0)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_rules_versions (
                    rules_version_id TEXT PRIMARY KEY,
                    version TEXT NOT NULL UNIQUE,
                    version_number INTEGER NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    created_from_version_id TEXT,
                    created_source TEXT NOT NULL,
                    change_summary TEXT NOT NULL,
                    config_hash TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_rules_current (
                    scope TEXT PRIMARY KEY,
                    rules_version_id TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_rules_coin_rules (
                    rules_version_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    max_allocation_pct TEXT,
                    PRIMARY KEY (rules_version_id, symbol)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_rules_usage (
                    rules_version_id TEXT NOT NULL,
                    usage_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    entity_version TEXT,
                    context TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(rules_version_id, usage_type, entity_id, entity_version)
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


_VERSION_COLUMNS = (
    "rules_version_id",
    "version",
    "version_number",
    "created_at",
    "created_from_version_id",
    "created_source",
    "change_summary",
    "config_hash",
    "schema_version",
    "payload",
)


def _row_to_version(row: sqlite3.Row, current_id: str | None) -> TradingRulesVersion:
    return TradingRulesVersion(
        rules_version_id=row["rules_version_id"],
        version=row["version"],
        created_at=row["created_at"],
        created_from_version_id=row["created_from_version_id"],
        created_source=row["created_source"],
        change_summary=row["change_summary"],
        config_hash=row["config_hash"],
        schema_version=row["schema_version"],
        draft=draft_from_json(row["payload"]),
        is_current=row["rules_version_id"] == current_id,
    )


def _version_number(version: str) -> int:
    if not version.startswith("v") or not version[1:].isdigit():
        raise TradingRulesError("trading rules version must use vN numbering")
    return int(version[1:])
