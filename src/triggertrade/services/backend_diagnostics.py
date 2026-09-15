"""Read-only operational diagnostics for the frozen backend."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import os
from typing import Any

from triggertrade.persistence.postgres import (
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresSettings,
)
from triggertrade.services.process_roles import RuntimeProcessRole, resolve_process_role


DIAGNOSTIC_STATUSES = frozenset({"RUNNING", "DEGRADED", "BLOCKED", "UNAVAILABLE"})


@dataclass(frozen=True)
class DiagnosticCheck:
    name: str
    status: str
    detail: str

    def to_payload(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass(frozen=True)
class BackendDiagnosticReport:
    role: str
    status: str
    ready: bool
    checks: tuple[DiagnosticCheck, ...]
    migrations: tuple[dict[str, object], ...]
    outbox: tuple[dict[str, object], ...]
    inbox: tuple[dict[str, object], ...]
    owner_state: tuple[dict[str, object], ...]
    heartbeats: tuple[dict[str, object], ...]
    research_promotion_requests: int

    def to_payload(self) -> dict[str, object]:
        return {
            "role": self.role,
            "status": self.status,
            "ready": self.ready,
            "checks": [check.to_payload() for check in self.checks],
            "migrations": list(self.migrations),
            "outbox": list(self.outbox),
            "inbox": list(self.inbox),
            "owner_state": list(self.owner_state),
            "heartbeats": list(self.heartbeats),
            "research_promotion_requests": self.research_promotion_requests,
        }

    def to_json(self, *, indent: int | None = None) -> str:
        return json.dumps(self.to_payload(), indent=indent, sort_keys=True)


def collect_backend_diagnostics(
    env: Mapping[str, str] | None = None,
    *,
    connection_factory: PostgresConnectionFactory | None = None,
) -> BackendDiagnosticReport:
    """Collect a sanitized PostgreSQL-backed backend diagnostic snapshot."""

    values = dict(os.environ if env is None else env)
    role = resolve_process_role(values).role
    try:
        if connection_factory is None:
            settings = PostgresSettings.from_env(values)
            connection_factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with connection_factory.connect() as connection:
            return collect_backend_diagnostics_from_connection(connection, role=role)
    except Exception as exc:  # noqa: BLE001 - diagnostics should report, not expose config or crash.
        return _unavailable_report(role=role, reason=_safe_error(exc))


def collect_backend_diagnostics_from_connection(connection, *, role: RuntimeProcessRole) -> BackendDiagnosticReport:
    migrations = _migrations(connection)
    outbox = _outbox_counts(connection)
    inbox = _inbox_counts(connection)
    owner_state = _owner_state_counts(connection)
    heartbeats = _runtime_heartbeats(connection)
    promotion_requests = _promotion_request_count(connection)
    stale_locked_outbox = _stale_locked_outbox_count(connection)

    checks = [
        DiagnosticCheck("postgres", "RUNNING", "PostgreSQL connection usable"),
        _migration_check(migrations),
        _outbox_check(outbox, stale_locked_outbox),
        _inbox_check(inbox),
        _role_heartbeat_check(role, heartbeats),
        _promotion_governance_check(promotion_requests),
    ]
    status = _rollup(check.status for check in checks)
    return BackendDiagnosticReport(
        role=role.value,
        status=status,
        ready=status == "RUNNING",
        checks=tuple(checks),
        migrations=tuple(migrations),
        outbox=tuple(outbox),
        inbox=tuple(inbox),
        owner_state=tuple(owner_state),
        heartbeats=tuple(heartbeats),
        research_promotion_requests=promotion_requests,
    )


def _migrations(connection) -> list[dict[str, object]]:
    rows = _fetchall(
        connection,
        """
        SELECT version, name, applied_at
        FROM triggertrade_schema_migrations
        ORDER BY version
        """,
    )
    return [
        {"version": str(row[0]), "name": str(row[1]), "applied_at": _string_or_none(row[2])}
        for row in rows
    ]


def _outbox_counts(connection) -> list[dict[str, object]]:
    rows = _fetchall(
        connection,
        """
        SELECT consumer, status, count(*), COALESCE(max(attempt_count), 0)
        FROM triggertrade_outbox_messages
        GROUP BY consumer, status
        ORDER BY consumer, status
        """,
    )
    return [
        {
            "consumer": str(row[0]),
            "status": str(row[1]),
            "count": int(row[2]),
            "max_attempt_count": int(row[3]),
        }
        for row in rows
    ]


def _inbox_counts(connection) -> list[dict[str, object]]:
    rows = _fetchall(
        connection,
        """
        SELECT consumer, status, count(*)
        FROM triggertrade_inbox_messages
        GROUP BY consumer, status
        ORDER BY consumer, status
        """,
    )
    return [
        {"consumer": str(row[0]), "status": str(row[1]), "count": int(row[2])}
        for row in rows
    ]


def _owner_state_counts(connection) -> list[dict[str, object]]:
    rows = _fetchall(
        connection,
        """
        SELECT owner, state_type, count(*), max(updated_at)
        FROM triggertrade_owner_state_records
        GROUP BY owner, state_type
        ORDER BY owner, state_type
        """,
    )
    return [
        {
            "owner": str(row[0]),
            "state_type": str(row[1]),
            "count": int(row[2]),
            "latest_updated_at": _string_or_none(row[3]),
        }
        for row in rows
    ]


def _runtime_heartbeats(connection) -> list[dict[str, object]]:
    rows = _fetchall(
        connection,
        """
        SELECT
            payload_json->>'component',
            payload_json->>'status',
            payload_json->>'observed_at',
            payload_json->>'detail'
        FROM triggertrade_owner_state_records
        WHERE owner = 'Cross-System'
          AND state_type = 'runtime_heartbeat'
        ORDER BY state_id
        """,
    )
    return [
        {
            "component": str(row[0]),
            "status": str(row[1]),
            "observed_at": _string_or_none(row[2]),
            "detail": _heartbeat_detail(row[3]),
        }
        for row in rows
    ]


def _promotion_request_count(connection) -> int:
    row = _fetchone(
        connection,
        """
        SELECT count(*)
        FROM triggertrade_owner_state_records
        WHERE owner = 'Research'
          AND state_type = 'research_promotion_request'
        """,
    )
    return 0 if row is None else int(row[0])


def _stale_locked_outbox_count(connection) -> int:
    row = _fetchone(
        connection,
        """
        SELECT count(*)
        FROM triggertrade_outbox_messages
        WHERE status = 'IN_FLIGHT'
          AND lock_expires_at <= now()
        """,
    )
    return 0 if row is None else int(row[0])


def _fetchall(connection, sql: str) -> list[tuple[Any, ...]]:
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return list(cursor.fetchall())


def _fetchone(connection, sql: str) -> tuple[Any, ...] | None:
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchone()


def _migration_check(migrations: list[dict[str, object]]) -> DiagnosticCheck:
    if not migrations:
        return DiagnosticCheck("migrations", "UNAVAILABLE", "no applied PostgreSQL migrations recorded")
    latest = migrations[-1]
    return DiagnosticCheck("migrations", "RUNNING", f"latest migration {latest['version']} {latest['name']}")


def _outbox_check(outbox: list[dict[str, object]], stale_locked_count: int) -> DiagnosticCheck:
    if stale_locked_count:
        return DiagnosticCheck("outbox", "DEGRADED", f"{stale_locked_count} in-flight message locks have expired")
    pending = sum(int(row["count"]) for row in outbox if row["status"] == "PENDING")
    in_flight = sum(int(row["count"]) for row in outbox if row["status"] == "IN_FLIGHT")
    if pending or in_flight:
        return DiagnosticCheck("outbox", "DEGRADED", f"{pending} pending and {in_flight} in-flight messages")
    return DiagnosticCheck("outbox", "RUNNING", "no pending or in-flight durable outbox messages")


def _inbox_check(inbox: list[dict[str, object]]) -> DiagnosticCheck:
    received = sum(int(row["count"]) for row in inbox if row["status"] == "RECEIVED")
    if received:
        return DiagnosticCheck("inbox", "DEGRADED", f"{received} received messages await processing")
    return DiagnosticCheck("inbox", "RUNNING", "no unprocessed durable inbox messages")


def _role_heartbeat_check(role: RuntimeProcessRole, heartbeats: list[dict[str, object]]) -> DiagnosticCheck:
    if role is RuntimeProcessRole.WEB:
        return DiagnosticCheck("role_heartbeat", "RUNNING", "web role readiness is served by /healthz")
    if role is RuntimeProcessRole.RESEARCH_WORKER:
        return DiagnosticCheck("role_heartbeat", "UNAVAILABLE", "research-worker role is reserved")

    expected = "trading-worker" if role is RuntimeProcessRole.TRADING_WORKER else "scheduler"
    heartbeat = next((row for row in heartbeats if row["component"] == expected), None)
    if heartbeat is None:
        status = "DEGRADED" if role is RuntimeProcessRole.TRADING_WORKER else "RUNNING"
        detail = (
            f"{expected} heartbeat has not been recorded"
            if role is RuntimeProcessRole.TRADING_WORKER
            else "scheduler role has no persisted heartbeat contract yet"
        )
        return DiagnosticCheck("role_heartbeat", status, detail)
    status = str(heartbeat["status"])
    _validate_status(status, "role_heartbeat")
    return DiagnosticCheck("role_heartbeat", status, str(heartbeat.get("detail") or "heartbeat recorded"))


def _promotion_governance_check(count: int) -> DiagnosticCheck:
    if count:
        return DiagnosticCheck("research_promotion_governance", "RUNNING", f"{count} durable promotion requests recorded")
    return DiagnosticCheck("research_promotion_governance", "RUNNING", "no durable promotion requests recorded")


def _rollup(statuses) -> str:
    values = tuple(statuses)
    if not values:
        return "UNAVAILABLE"
    if any(status == "BLOCKED" for status in values):
        return "BLOCKED"
    if any(status == "UNAVAILABLE" for status in values):
        return "UNAVAILABLE"
    if any(status == "DEGRADED" for status in values):
        return "DEGRADED"
    return "RUNNING"


def _validate_status(status: str, name: str) -> None:
    if status not in DIAGNOSTIC_STATUSES:
        raise ValueError(f"diagnostic check {name!r} returned unsupported status {status!r}")


def _unavailable_report(*, role: RuntimeProcessRole, reason: str) -> BackendDiagnosticReport:
    checks = (DiagnosticCheck("postgres", "UNAVAILABLE", reason),)
    return BackendDiagnosticReport(
        role=role.value,
        status="UNAVAILABLE",
        ready=False,
        checks=checks,
        migrations=(),
        outbox=(),
        inbox=(),
        owner_state=(),
        heartbeats=(),
        research_promotion_requests=0,
    )


def _safe_error(exc: BaseException) -> str:
    if isinstance(exc, PostgresPersistenceError):
        return str(exc)
    return f"{exc.__class__.__name__}"


def _heartbeat_detail(value: object) -> str | None:
    if value is None:
        return None
    return "heartbeat detail recorded; see restricted runtime state for full detail"


def _string_or_none(value: object) -> str | None:
    return None if value is None else str(value)
