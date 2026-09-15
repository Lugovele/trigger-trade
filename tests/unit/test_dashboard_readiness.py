from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus
from http.client import HTTPConnection
import json
import threading

from triggertrade.dashboard.__main__ import create_server
from triggertrade.dashboard.readiness import DashboardReadinessCheck, evaluate_dashboard_readiness
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.instruments import InstrumentCatalogRefreshResult
from triggertrade.accounting import EquitySnapshot
from triggertrade.persistence import InstrumentCatalogStore, LaneCandleLifecycle, RuntimeHeartbeat, RuntimeStore
from triggertrade.persistence.operator_state_store import OperatorStateStore
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from tests.unit.test_dashboard_read_model import _empty_db


def test_readiness_reports_unavailable_postgres_dependency(tmp_path):
    db = _runtime_ready_db(tmp_path)

    report = evaluate_dashboard_readiness(DashboardReadModel(db), env={})

    checks = {check.name: check for check in report.checks}
    assert report.ready is False
    assert checks["postgres_persistence"].status == "UNAVAILABLE"
    assert "TRIGGERTRADE_POSTGRES_DSN is required" in checks["postgres_persistence"].detail
    assert "postgres_persistence" in report.unavailable_dependencies


def test_readiness_reports_running_when_runtime_and_postgres_are_reachable(tmp_path):
    db = _runtime_ready_db(tmp_path)

    report = evaluate_dashboard_readiness(
        DashboardReadModel(db),
        env={"TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit.invalid/db"},
        postgres_probe=_running_postgres_probe,
    )

    assert report.ready is True
    assert report.status == "RUNNING"
    assert report.unavailable_dependencies == ()
    checks = {check.name: check for check in report.checks}
    assert checks["worker_safety"].status == "RUNNING"
    assert checks["postgres_persistence"].status == "RUNNING"


def test_healthz_returns_not_ready_when_dependency_is_unavailable(tmp_path):
    db = _runtime_ready_db(tmp_path)
    server = create_server(port=0, db_path=db, readiness_env={})
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/healthz")
        response = conn.getresponse()
        body = response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert response.status == HTTPStatus.SERVICE_UNAVAILABLE
    assert body == "not ready"


def test_readiness_api_exposes_dependency_aware_report_without_secrets(tmp_path):
    db = _runtime_ready_db(tmp_path)
    server = create_server(
        port=0,
        db_path=db,
        readiness_env={"TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit:secret@example.invalid/db"},
        postgres_health_probe=_running_postgres_probe,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/api/readiness")
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert response.status == HTTPStatus.OK
    assert payload["ready"] is True
    assert payload["status"] == "RUNNING"
    assert any(check["name"] == "postgres_persistence" for check in payload["checks"])
    assert any(check["name"] == "worker_safety" for check in payload["checks"])
    text = json.dumps(payload)
    assert "secret" not in text
    assert "postgresql://" not in text


def _running_postgres_probe(env):
    assert env.get("TRIGGERTRADE_POSTGRES_DSN")
    return DashboardReadinessCheck("postgres_persistence", "RUNNING", "PostgreSQL persistence reachable")


def _runtime_ready_db(tmp_path):
    db = _empty_db(tmp_path)
    observed_at = datetime.now(UTC).isoformat()
    RuntimeStore(db).record_heartbeat(
        RuntimeHeartbeat(
            component="futures_runtime",
            status="RUNNING",
            observed_at=observed_at,
            detail="cycle completed",
        )
    )
    RuntimeStore(db).save_lane_lifecycle(
        LaneCandleLifecycle(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            candle_id="BTCUSDT:1m:2026-09-08T12:00:00+00:00",
            candle_open_time="2026-09-08T12:00:00+00:00",
            trigger_set_id="triggertrade-futures-core",
            trigger_set_version="v1",
            status="no_signal",
            processed_at=observed_at,
            error=None,
        )
    )
    InstrumentCatalogStore(db).record_failed_refresh(
        InstrumentCatalogRefreshResult(
            fetched_count=1,
            tradeable_count=1,
            excluded_count=0,
            updated_at=observed_at,
            catalog_hash="unit-catalog",
            status="OK",
            error=None,
        )
    )
    FuturesAccountingStore(db).record_equity_snapshot(
        EquitySnapshot(
            snapshot_id="unit-account",
            observed_at=observed_at,
            source="bybit_demo_account",
            wallet_balance=Decimal("1000"),
            equity=Decimal("1000"),
            available_margin=Decimal("1000"),
            used_margin=Decimal("0"),
            unrealized_pnl=Decimal("0"),
            realized_pnl=Decimal("0"),
            running_peak=Decimal("1000"),
            drawdown_absolute=Decimal("0"),
            drawdown_percent=Decimal("0"),
            max_drawdown=Decimal("0"),
        )
    )
    OperatorStateStore(db).resume(changed_at=observed_at, source="unit", reason="readiness fixture")
    return db
