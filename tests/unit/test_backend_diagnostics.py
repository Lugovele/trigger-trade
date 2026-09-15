from __future__ import annotations

from datetime import UTC, datetime
import json

from triggertrade.services.backend_diagnostics import (
    collect_backend_diagnostics,
    collect_backend_diagnostics_from_connection,
)
from triggertrade.services.process_roles import RuntimeProcessRole


def test_collect_backend_diagnostics_reports_sanitized_operational_snapshot():
    connection = _FakeConnection(
        {
            "triggertrade_schema_migrations": [
                ("0001", "durable_persistence_foundation", datetime(2026, 9, 15, tzinfo=UTC)),
                ("0002", "durable_business_messages", datetime(2026, 9, 15, tzinfo=UTC)),
            ],
            "outbox_counts": [
                ("Portfolio", "PENDING", 2, 1),
                ("Scheduler", "CONSUMED", 1, 1),
            ],
            "inbox_counts": [("Portfolio", "RECEIVED", 1)],
            "owner_state_counts": [
                ("Cross-System", "runtime_heartbeat", 1, datetime(2026, 9, 15, tzinfo=UTC)),
                ("Research", "research_promotion_request", 3, datetime(2026, 9, 15, tzinfo=UTC)),
            ],
            "heartbeats": [
                ("trading-worker", "RUNNING", "2026-09-15T00:00:00+00:00", "token=secret"),
            ],
            "promotion_count": [(3,)],
            "stale_locked_count": [(0,)],
        }
    )

    report = collect_backend_diagnostics_from_connection(
        connection,
        role=RuntimeProcessRole.TRADING_WORKER,
    )

    payload = report.to_payload()
    assert payload["status"] == "DEGRADED"
    assert payload["ready"] is False
    assert payload["research_promotion_requests"] == 3
    assert payload["outbox"] == [
        {"consumer": "Portfolio", "status": "PENDING", "count": 2, "max_attempt_count": 1},
        {"consumer": "Scheduler", "status": "CONSUMED", "count": 1, "max_attempt_count": 1},
    ]
    assert payload["inbox"] == [{"consumer": "Portfolio", "status": "RECEIVED", "count": 1}]
    assert any(check["name"] == "outbox" and "2 pending" in check["detail"] for check in payload["checks"])
    assert payload["heartbeats"][0]["detail"] == "heartbeat detail recorded; see restricted runtime state for full detail"
    assert any(
        check["name"] == "role_heartbeat"
        and check["status"] == "RUNNING"
        and check["detail"] == "heartbeat detail recorded; see restricted runtime state for full detail"
        for check in payload["checks"]
    )

    text = json.dumps(payload)
    assert "payload_json" not in text
    assert "postgresql://" not in text
    assert "secret" not in text
    assert "token=" not in text


def test_backend_diagnostics_flags_expired_outbox_locks():
    connection = _FakeConnection(
        {
            "triggertrade_schema_migrations": [("0002", "durable_business_messages", "now")],
            "outbox_counts": [("Portfolio", "IN_FLIGHT", 1, 4)],
            "inbox_counts": [],
            "owner_state_counts": [],
            "heartbeats": [("trading-worker", "RUNNING", "2026-09-15T00:00:00+00:00", "claimed")],
            "promotion_count": [(0,)],
            "stale_locked_count": [(1,)],
        }
    )

    report = collect_backend_diagnostics_from_connection(
        connection,
        role=RuntimeProcessRole.TRADING_WORKER,
    )

    checks = {check.name: check for check in report.checks}
    assert report.status == "DEGRADED"
    assert checks["outbox"].detail == "1 in-flight message locks have expired"


def test_backend_diagnostics_reports_missing_postgres_without_secret_bearing_configuration():
    report = collect_backend_diagnostics({"TRIGGERTRADE_PROCESS_ROLE": "trading-worker"})

    payload = report.to_payload()
    assert payload["status"] == "UNAVAILABLE"
    assert payload["ready"] is False
    assert payload["checks"] == [
        {
            "name": "postgres",
            "status": "UNAVAILABLE",
            "detail": "TRIGGERTRADE_POSTGRES_DSN is required",
        }
    ]


class _FakeConnection:
    def __init__(self, rows_by_key):
        self._rows_by_key = rows_by_key

    def cursor(self):
        return _FakeCursor(self._rows_by_key)


class _FakeCursor:
    def __init__(self, rows_by_key):
        self._rows_by_key = rows_by_key
        self._rows = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql):
        text = " ".join(sql.lower().split())
        if "from triggertrade_schema_migrations" in text:
            self._rows = self._rows_by_key["triggertrade_schema_migrations"]
        elif "from triggertrade_outbox_messages" in text and "group by consumer, status" in text:
            self._rows = self._rows_by_key["outbox_counts"]
        elif "from triggertrade_inbox_messages" in text:
            self._rows = self._rows_by_key["inbox_counts"]
        elif "from triggertrade_owner_state_records" in text and "group by owner, state_type" in text:
            self._rows = self._rows_by_key["owner_state_counts"]
        elif "payload_json->>'component'" in text:
            self._rows = self._rows_by_key["heartbeats"]
        elif "owner = 'research'" in text:
            self._rows = self._rows_by_key["promotion_count"]
        elif "lock_expires_at <= now()" in text:
            self._rows = self._rows_by_key["stale_locked_count"]
        else:
            raise AssertionError(f"unexpected SQL: {sql}")

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return None if not self._rows else self._rows[0]
