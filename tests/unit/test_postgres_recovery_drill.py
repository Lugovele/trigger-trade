from __future__ import annotations

import os

import pytest

from scripts.postgres_recovery_drill import run_drill
from triggertrade.persistence.postgres import PostgresPersistenceError


pytest.importorskip("psycopg")


def test_postgres_recovery_drill_rejects_non_drill_schemas():
    with pytest.raises(PostgresPersistenceError, match="must start"):
        run_drill("postgresql://example.invalid/db", source_schema="public", restore_schema="tt_recovery_drill_restore_unit")


def test_postgres_recovery_drill_verifies_isolated_restore_round_trip():
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")

    result = run_drill(
        dsn,
        source_schema="tt_recovery_drill_src_unit",
        restore_schema="tt_recovery_drill_restore_unit",
        keep_schemas=False,
    )

    assert result["status"] == "PASS"
    assert result["restore_second_apply_applied"] == []
    assert result["table_counts"]["triggertrade_outbox_messages"] == 2
    assert result["table_counts"]["triggertrade_inbox_messages"] == 1
    assert result["table_counts"]["triggertrade_owner_state_records"] == 2
    assert result["durable_state"]["promotion_outbox_consumer"] == "Scheduler"
    assert result["durable_state"]["inbox_status"] == "RECEIVED"
