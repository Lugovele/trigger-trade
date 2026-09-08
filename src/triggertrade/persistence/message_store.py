"""Persistent user-facing operational messages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
import json
from pathlib import Path
import re
import sqlite3
import uuid


class MessageStoreError(RuntimeError):
    """Raised when message input cannot be safely stored or updated."""


class MessageSeverity(StrEnum):
    INFO = "INFO"
    ATTENTION = "ATTENTION"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class MessageRecord:
    message_id: str
    created_at: str
    type: str
    severity: MessageSeverity
    title: str | None
    body: str
    source: str
    entity_type: str | None
    entity_id: str | None
    is_read: bool
    read_at: str | None
    dedupe_key: str | None
    expires_at: str | None
    metadata: dict[str, str | int | float | bool | None]


_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
_SECRET_RE = re.compile(
    r"(api[_-]?key|api[_-]?secret|authorization|bearer|cookie|csrf|session|token|password|credential|\.env)",
    re.I,
)


class MessageStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def create_message(
        self,
        *,
        body: str,
        type: str | MessageSeverity | None = None,
        severity: str | MessageSeverity | None = None,
        title: str | None = None,
        source: str = "system",
        entity_type: str | None = None,
        entity_id: str | None = None,
        dedupe_key: str | None = None,
        expires_at: str | None = None,
        metadata: dict | None = None,
        created_at: str | None = None,
    ) -> MessageRecord:
        created_at = created_at or _now()
        severity_value = _severity(severity or type or MessageSeverity.INFO)
        message_type = _text(str(type or severity_value.value), max_len=32, field="type").upper()
        clean_body = _safe_text(body, max_len=800, field="body")
        clean_title = None if title is None else _safe_text(title, max_len=160, field="title")
        clean_source = _safe_text(source, max_len=80, field="source")
        clean_entity_type = None if entity_type is None else _safe_text(entity_type, max_len=80, field="entity_type")
        clean_entity_id = None if entity_id is None else _safe_text(entity_id, max_len=160, field="entity_id")
        clean_dedupe = None if dedupe_key is None else _safe_text(dedupe_key, max_len=200, field="dedupe_key")
        clean_metadata = _safe_metadata(metadata or {})

        if clean_dedupe:
            existing = self._find_active_dedupe(clean_dedupe, created_at)
            if existing is not None:
                return existing

        message_id = "msg_" + uuid.uuid4().hex
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_messages (
                    message_id, created_at, type, severity, title, body, source,
                    entity_type, entity_id, is_read, read_at, dedupe_key, expires_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, ?, ?)
                """,
                (
                    message_id,
                    created_at,
                    message_type,
                    severity_value.value,
                    clean_title,
                    clean_body,
                    clean_source,
                    clean_entity_type,
                    clean_entity_id,
                    clean_dedupe,
                    expires_at,
                    json.dumps(clean_metadata, sort_keys=True),
                ),
            )
        return self.get_message(message_id)

    def get_message(self, message_id: str) -> MessageRecord:
        _validate_ids([message_id])
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM user_messages
                WHERE message_id = ?
                """,
                (message_id,),
            ).fetchone()
        if row is None:
            raise MessageStoreError("message id not found")
        return _record_from_row(row)

    def list_messages(self, *, limit: int = 50, now: str | None = None) -> tuple[MessageRecord, ...]:
        safe_limit = max(1, min(int(limit), 100))
        now_value = now or _now()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM user_messages
                WHERE expires_at IS NULL OR expires_at > ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (now_value, safe_limit),
            ).fetchall()
        return tuple(_record_from_row(row) for row in rows)

    def get_unread_message_count(self, *, now: str | None = None) -> int:
        now_value = now or _now()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM user_messages
                WHERE is_read = 0 AND (expires_at IS NULL OR expires_at > ?)
                """,
                (now_value,),
            ).fetchone()
        return int(row["count"])

    def mark_read(self, message_ids: list[str] | tuple[str, ...], *, read_at: str | None = None) -> int:
        ids = tuple(dict.fromkeys(message_ids))
        _validate_ids(ids)
        if not ids:
            return 0
        if len(ids) > 100:
            raise MessageStoreError("too many message ids")
        read_at = read_at or _now()
        placeholders = ",".join("?" for _ in ids)
        with self._connect() as conn:
            known = conn.execute(
                f"SELECT COUNT(*) AS count FROM user_messages WHERE message_id IN ({placeholders})",
                ids,
            ).fetchone()
            if int(known["count"]) != len(ids):
                raise MessageStoreError("message id not found")
            cursor = conn.execute(
                f"""
                UPDATE user_messages
                SET is_read = 1, read_at = COALESCE(read_at, ?)
                WHERE message_id IN ({placeholders}) AND is_read = 0
                """,
                (read_at, *ids),
            )
        return int(cursor.rowcount)

    def _find_active_dedupe(self, dedupe_key: str, now_value: str) -> MessageRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM user_messages
                WHERE dedupe_key = ? AND is_read = 0 AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (dedupe_key, now_value),
            ).fetchone()
        return None if row is None else _record_from_row(row)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT,
                    body TEXT NOT NULL,
                    source TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id TEXT,
                    is_read INTEGER NOT NULL DEFAULT 0,
                    read_at TEXT,
                    dedupe_key TEXT,
                    expires_at TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_messages_created ON user_messages(created_at DESC, id DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_messages_unread ON user_messages(is_read, expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_messages_dedupe ON user_messages(dedupe_key, is_read)")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


def _record_from_row(row: sqlite3.Row) -> MessageRecord:
    try:
        metadata = json.loads(row["metadata_json"] or "{}")
    except json.JSONDecodeError:
        metadata = {}
    return MessageRecord(
        message_id=row["message_id"],
        created_at=row["created_at"],
        type=row["type"],
        severity=MessageSeverity(row["severity"]),
        title=row["title"],
        body=row["body"],
        source=row["source"],
        entity_type=row["entity_type"],
        entity_id=row["entity_id"],
        is_read=bool(row["is_read"]),
        read_at=row["read_at"],
        dedupe_key=row["dedupe_key"],
        expires_at=row["expires_at"],
        metadata=_safe_metadata(metadata if isinstance(metadata, dict) else {}),
    )


def _severity(value: str | MessageSeverity) -> MessageSeverity:
    try:
        return MessageSeverity(str(value).upper())
    except ValueError as exc:
        raise MessageStoreError("invalid message severity") from exc


def _validate_ids(message_ids: tuple[str, ...] | list[str]) -> None:
    for message_id in message_ids:
        if not isinstance(message_id, str) or _ID_RE.fullmatch(message_id) is None:
            raise MessageStoreError("invalid message id")


def _safe_metadata(metadata: dict) -> dict[str, str | int | float | bool | None]:
    safe: dict[str, str | int | float | bool | None] = {}
    for index, (key, value) in enumerate(metadata.items()):
        if index >= 12:
            break
        clean_key = _text(str(key), max_len=64, field="metadata key")
        if _SECRET_RE.search(clean_key):
            safe[clean_key] = "[redacted]"
            continue
        if value is None or isinstance(value, bool | int | float):
            safe[clean_key] = value
            continue
        text = _text(str(value), max_len=220, field="metadata value")
        safe[clean_key] = "[redacted]" if _SECRET_RE.search(text) else text
    return safe


def _safe_text(value: str, *, max_len: int, field: str) -> str:
    text = _text(value, max_len=max_len, field=field)
    return "[redacted]" if _SECRET_RE.search(text) else text


def _text(value: str, *, max_len: int, field: str) -> str:
    text = " ".join(str(value).replace("\x00", "").split())
    if not text:
        raise MessageStoreError(f"{field} is required")
    return text[:max_len]


def _now() -> str:
    return datetime.now(UTC).isoformat()
