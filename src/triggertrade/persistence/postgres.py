"""PostgreSQL persistence foundation for canonical durable state."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from types import TracebackType
from typing import Any

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
_MIGRATION_RE = re.compile(r"^(?P<version>\d{4})_(?P<name>[a-z0-9_]+)\.sql$")


class PostgresPersistenceError(RuntimeError):
    """Raised when target PostgreSQL persistence cannot safely proceed."""


class OwnerStateConflict(PostgresPersistenceError):
    """Raised when a durable owner state identity is replayed with new content."""


class OwnerStateRevisionConflict(PostgresPersistenceError):
    """Raised when compare-and-set sees a stale owner state revision."""


@dataclass(frozen=True)
class PostgresSettings:
    dsn: str
    schema: str = "public"

    def __post_init__(self) -> None:
        if not self.dsn:
            raise PostgresPersistenceError("PostgreSQL DSN is required")
        object.__setattr__(
            self,
            "schema",
            _validate_identifier(self.schema, field="PostgreSQL schema"),
        )

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "PostgresSettings":
        values = os.environ if env is None else env
        dsn = values.get("TRIGGERTRADE_POSTGRES_DSN")
        if not dsn:
            raise PostgresPersistenceError("TRIGGERTRADE_POSTGRES_DSN is required")
        schema = values.get("TRIGGERTRADE_POSTGRES_SCHEMA", "public")
        return cls(dsn=dsn, schema=_validate_identifier(schema, field="PostgreSQL schema"))


@dataclass(frozen=True)
class MigrationRecord:
    version: str
    name: str
    checksum: str


@dataclass(frozen=True)
class OwnerStateRecord:
    owner: str
    state_type: str
    state_id: str
    revision: int
    payload: dict[str, Any]
    payload_digest: str


class PostgresConnectionFactory:
    def __init__(self, *, dsn: str, schema: str = "public") -> None:
        self._dsn = dsn
        self._schema = _validate_identifier(schema, field="PostgreSQL schema")

    @property
    def schema(self) -> str:
        return self._schema

    def connect(self):
        psycopg = _psycopg()
        conn = psycopg.connect(self._dsn, autocommit=False)
        with conn.cursor() as cursor:
            cursor.execute(f"SET search_path TO {_quote_identifier(self._schema)}")
        return conn


class PostgresUnitOfWork(AbstractContextManager["PostgresUnitOfWork"]):
    def __init__(self, factory: PostgresConnectionFactory) -> None:
        self._factory = factory
        self._conn = None

    def __enter__(self) -> "PostgresUnitOfWork":
        self._conn = self._factory.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        if self._conn is None:
            return False
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self._conn.close()
            self._conn = None
        return False

    @property
    def connection(self):
        if self._conn is None:
            raise PostgresPersistenceError("unit of work is not active")
        return self._conn


class OwnerStateStore:
    """Generic durable owner-state primitive for later target stores."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def put_if_absent(
        self,
        *,
        owner: str,
        state_type: str,
        state_id: str,
        payload: Mapping[str, Any],
    ) -> tuple[OwnerStateRecord, bool]:
        owner = _stable_token(owner, field="owner")
        state_type = _stable_token(state_type, field="state_type")
        state_id = _stable_token(state_id, field="state_id")
        payload_text, digest = _payload_text_and_digest(payload)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_owner_state_records (
                    owner, state_type, state_id, revision, payload_json, payload_digest
                ) VALUES (%s, %s, %s, 1, %s::jsonb, %s)
                ON CONFLICT (owner, state_type, state_id) DO NOTHING
                RETURNING owner, state_type, state_id, revision, payload_json::text, payload_digest
                """,
                (owner, state_type, state_id, payload_text, digest),
            )
            row = cursor.fetchone()
        if row is not None:
            return _record_from_row(row), True
        existing = self.get(owner=owner, state_type=state_type, state_id=state_id)
        if existing is None:
            raise PostgresPersistenceError("owner state insert conflicted but no record was found")
        if existing.payload_digest != digest:
            raise OwnerStateConflict("owner state identity already exists with different canonical content")
        return existing, False

    def get(self, *, owner: str, state_type: str, state_id: str) -> OwnerStateRecord | None:
        owner = _stable_token(owner, field="owner")
        state_type = _stable_token(state_type, field="state_type")
        state_id = _stable_token(state_id, field="state_id")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT owner, state_type, state_id, revision, payload_json::text, payload_digest
                FROM triggertrade_owner_state_records
                WHERE owner = %s AND state_type = %s AND state_id = %s
                """,
                (owner, state_type, state_id),
            )
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def compare_and_set(
        self,
        *,
        owner: str,
        state_type: str,
        state_id: str,
        expected_revision: int,
        payload: Mapping[str, Any],
    ) -> OwnerStateRecord:
        if expected_revision < 1:
            raise OwnerStateRevisionConflict("expected revision must be positive")
        owner = _stable_token(owner, field="owner")
        state_type = _stable_token(state_type, field="state_type")
        state_id = _stable_token(state_id, field="state_id")
        payload_text, digest = _payload_text_and_digest(payload)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE triggertrade_owner_state_records
                SET revision = revision + 1,
                    payload_json = %s::jsonb,
                    payload_digest = %s,
                    updated_at = now()
                WHERE owner = %s AND state_type = %s AND state_id = %s AND revision = %s
                RETURNING owner, state_type, state_id, revision, payload_json::text, payload_digest
                """,
                (payload_text, digest, owner, state_type, state_id, expected_revision),
            )
            row = cursor.fetchone()
        if row is None:
            raise OwnerStateRevisionConflict("owner state revision does not match")
        return _record_from_row(row)


def apply_postgres_migrations(
    *,
    dsn: str,
    schema: str = "public",
    migrations_dir: str | Path | None = None,
) -> tuple[MigrationRecord, ...]:
    schema = _validate_identifier(schema, field="PostgreSQL schema")
    migrations_path = Path(migrations_dir) if migrations_dir is not None else _default_migrations_dir()
    migrations = _load_migrations(migrations_path)
    factory = PostgresConnectionFactory(dsn=dsn, schema=schema)
    applied: list[MigrationRecord] = []
    conn = None
    try:
        conn = _psycopg().connect(dsn, autocommit=False)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {_quote_identifier(schema)}")
            cursor.execute(f"SET search_path TO {_quote_identifier(schema)}")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS triggertrade_schema_migrations (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            for migration in migrations:
                cursor.execute(
                    """
                    SELECT checksum
                    FROM triggertrade_schema_migrations
                    WHERE version = %s
                    """,
                    (migration.version,),
                )
                row = cursor.fetchone()
                if row is not None:
                    if row[0] != migration.checksum:
                        raise PostgresPersistenceError(
                            f"migration {migration.version} checksum mismatch"
                        )
                    continue
                cursor.execute(migration.sql)
                cursor.execute(
                    """
                    INSERT INTO triggertrade_schema_migrations (version, name, checksum)
                    VALUES (%s, %s, %s)
                    """,
                    (migration.version, migration.name, migration.checksum),
                )
                applied.append(MigrationRecord(migration.version, migration.name, migration.checksum))
        conn.commit()
    except Exception:
        if conn is not None:
            conn.rollback()
        raise
    finally:
        if conn is not None:
            conn.close()
    # Verify ordinary connections can bind the selected schema after migrations.
    with factory.connect() as verify_conn:
        with verify_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    return tuple(applied)


@dataclass(frozen=True)
class _Migration:
    version: str
    name: str
    checksum: str
    sql: str


def _load_migrations(path: Path) -> tuple[_Migration, ...]:
    if not path.exists():
        raise PostgresPersistenceError(f"migration directory does not exist: {path}")
    migrations: list[_Migration] = []
    for file_path in sorted(path.glob("*.sql")):
        match = _MIGRATION_RE.fullmatch(file_path.name)
        if match is None:
            raise PostgresPersistenceError(f"invalid migration filename: {file_path.name}")
        sql = file_path.read_text(encoding="utf-8")
        migrations.append(
            _Migration(
                version=match.group("version"),
                name=match.group("name"),
                checksum=sha256(sql.encode("utf-8")).hexdigest(),
                sql=sql,
            )
        )
    if not migrations:
        raise PostgresPersistenceError("no PostgreSQL migrations found")
    return tuple(migrations)


def _default_migrations_dir() -> Path:
    configured = os.environ.get("TRIGGERTRADE_POSTGRES_MIGRATIONS_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[3] / "migrations" / "postgres"


def _payload_text_and_digest(payload: Mapping[str, Any]) -> tuple[str, str]:
    payload_text = canonical_json_text(payload)
    return payload_text, canonical_json_digest(payload)


def _record_from_row(row: tuple[Any, ...]) -> OwnerStateRecord:
    return OwnerStateRecord(
        owner=str(row[0]),
        state_type=str(row[1]),
        state_id=str(row[2]),
        revision=int(row[3]),
        payload=json.loads(str(row[4]), parse_float=Decimal),
        payload_digest=str(row[5]),
    )


def _stable_token(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 160 or "\x00" in value:
        raise PostgresPersistenceError(f"{field} must be a non-empty stable string")
    return value


def _validate_identifier(value: str, *, field: str) -> str:
    if _IDENTIFIER_RE.fullmatch(value) is None:
        raise PostgresPersistenceError(f"{field} must be a safe PostgreSQL identifier")
    return value


def _quote_identifier(value: str) -> str:
    return '"' + _validate_identifier(value, field="PostgreSQL identifier").replace('"', '""') + '"'


def _psycopg():
    try:
        import psycopg
    except ImportError as exc:
        raise PostgresPersistenceError("psycopg is required for PostgreSQL persistence") from exc
    return psycopg
