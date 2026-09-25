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
    assert checks["bybit_demo_config"].status == "BLOCKED"
    assert checks["execution_bridge_attached"].status == "BLOCKED"
    assert "TRIGGERTRADE_POSTGRES_DSN is required" in checks["postgres_persistence"].detail
    assert "postgres_persistence" in report.unavailable_dependencies


def test_readiness_reports_running_when_runtime_and_postgres_are_reachable(tmp_path):
    db = _runtime_ready_db(tmp_path)

    report = evaluate_dashboard_readiness(
        DashboardReadModel(db),
        env={
            "TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit.invalid/db",
            "TRIGGERTRADE_OPERATOR_PRINCIPALS": "operator-1",
            **_bybit_demo_env(),
        },
        postgres_probe=_running_postgres_probe,
        postgres_runtime_probe=_running_runtime_probe,
        postgres_registry_probe=_running_registry_probe,
        execution_bridge=_CertifiedBridge(),
    )

    assert report.ready is True
    assert report.status == "RUNNING"
    assert report.unavailable_dependencies == ()
    checks = {check.name: check for check in report.checks}
    assert checks["worker_safety"].status == "RUNNING"
    assert checks["postgres_persistence"].status == "RUNNING"
    assert checks["bybit_demo_config"].status == "RUNNING"
    assert checks["execution_bridge_attached"].status == "RUNNING"


def test_readiness_rejects_uncertified_execution_bridge_stub(tmp_path):
    db = _runtime_ready_db(tmp_path)

    report = evaluate_dashboard_readiness(
        DashboardReadModel(db),
        env={
            "TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit.invalid/db",
            "TRIGGERTRADE_OPERATOR_PRINCIPALS": "operator-1",
            **_bybit_demo_env(),
        },
        postgres_probe=_running_postgres_probe,
        postgres_runtime_probe=_running_runtime_probe,
        postgres_registry_probe=_running_registry_probe,
        execution_bridge=object(),
    )

    checks = {check.name: check for check in report.checks}
    assert report.ready is False
    assert checks["execution_bridge_attached"].status == "BLOCKED"
    assert "certified canonical execution bridge" in checks["execution_bridge_attached"].detail


def test_healthz_is_liveness_even_when_readiness_dependency_is_unavailable(tmp_path):
    db = _runtime_ready_db(tmp_path)
    server = create_server(port=0, db_path=db, readiness_env={})
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/healthz")
        health_response = conn.getresponse()
        health_body = health_response.read().decode("utf-8")
        conn.close()

        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/api/readiness")
        readiness_response = conn.getresponse()
        readiness_payload = json.loads(readiness_response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert health_response.status == HTTPStatus.OK
    assert health_body == "ok"
    assert readiness_response.status == HTTPStatus.OK
    assert readiness_payload["ready"] is False
    assert readiness_payload["status"] == "BLOCKED"
    assert "postgres_persistence" in readiness_payload["unavailable_dependencies"]
    assert "execution_bridge_attached" in readiness_payload["unavailable_dependencies"]


def test_readiness_api_exposes_dependency_aware_report_without_secrets(tmp_path):
    db = _runtime_ready_db(tmp_path)
    server = create_server(
        port=0,
        db_path=db,
        readiness_env={
            "TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit:secret@example.invalid/db",
            "TRIGGERTRADE_OPERATOR_PRINCIPALS": "operator-1",
            **_bybit_demo_env(),
        },
        operator_actions=_CertifiedBridge(),
        postgres_health_probe=_running_postgres_probe,
        postgres_runtime_probe=_running_runtime_probe,
        postgres_registry_probe=_running_registry_probe,
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
    assert any(check["name"] == "bybit_demo_config" for check in payload["checks"])
    assert any(check["name"] == "execution_bridge_attached" for check in payload["checks"])
    text = json.dumps(payload)
    assert "secret" not in text
    assert "postgresql://" not in text


def test_production_readiness_uses_distributed_postgres_heartbeat_not_local_sqlite(tmp_path):
    db = tmp_path / "missing-local-dashboard.sqlite3"

    report = evaluate_dashboard_readiness(
        DashboardReadModel(db),
        env={
            "TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit.invalid/db",
            "TRIGGERTRADE_OPERATOR_PRINCIPALS": "operator-1",
            **_bybit_demo_env(),
        },
        postgres_probe=_running_postgres_probe,
        postgres_runtime_probe=_running_runtime_probe,
        postgres_registry_probe=_running_registry_probe,
        execution_bridge=_CertifiedBridge(),
    )

    checks = {check.name: check for check in report.checks}
    assert checks["postgres_persistence"].status == "RUNNING"
    assert checks["heartbeat:trading-worker"].status == "RUNNING"
    assert checks["worker_safety"].status == "RUNNING"
    assert checks["web_read_model"].status == "DEGRADED"
    assert "database" not in checks
    assert "heartbeat" not in checks
    assert "postgres_persistence" not in report.unavailable_dependencies
    assert "worker_safety" not in report.unavailable_dependencies


def test_production_readiness_blocks_when_operator_principal_allowlist_missing(tmp_path):
    db = _runtime_ready_db(tmp_path)

    report = evaluate_dashboard_readiness(
        DashboardReadModel(db),
        env={
            "TRIGGERTRADE_RUNTIME_MODE": "production",
            "TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit.invalid/db",
            **_bybit_demo_env(),
        },
        postgres_probe=_running_postgres_probe,
        postgres_runtime_probe=_running_runtime_probe,
        postgres_registry_probe=_running_registry_probe,
        execution_bridge=_CertifiedBridge(),
    )

    checks = {check.name: check for check in report.checks}
    assert report.ready is False
    assert checks["operator_auth_boundary"].status == "BLOCKED"
    assert "allowlist" in checks["operator_auth_boundary"].detail


def test_production_readiness_blocks_local_dev_auth_mode(tmp_path):
    db = _runtime_ready_db(tmp_path)

    report = evaluate_dashboard_readiness(
        DashboardReadModel(db),
        env={
            "TRIGGERTRADE_RUNTIME_MODE": "production",
            "TRIGGERTRADE_AUTH_MODE": "local_dev_compat",
            "TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit.invalid/db",
            "TRIGGERTRADE_OPERATOR_PRINCIPALS": "operator-1",
            **_bybit_demo_env(),
        },
        postgres_probe=_running_postgres_probe,
        postgres_runtime_probe=_running_runtime_probe,
        postgres_registry_probe=_running_registry_probe,
        execution_bridge=_CertifiedBridge(),
    )

    checks = {check.name: check for check in report.checks}
    assert checks["operator_auth_boundary"].status == "BLOCKED"
    assert "local_dev_compat" in checks["operator_auth_boundary"].detail


def test_readiness_redacts_secret_like_distributed_heartbeat_details(tmp_path):
    db = _runtime_ready_db(tmp_path)

    def secret_runtime_probe(env):
        return (
            DashboardReadinessCheck(
                "heartbeat:trading-worker",
                "DEGRADED",
                "worker detail contained postgresql://user:secret@example/db token=abc123",
                datetime.now(UTC).isoformat(),
            ),
        )

    report = evaluate_dashboard_readiness(
        DashboardReadModel(db),
        env={
            "TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit.invalid/db",
            "TRIGGERTRADE_OPERATOR_PRINCIPALS": "operator-1",
            **_bybit_demo_env(),
        },
        postgres_probe=_running_postgres_probe,
        postgres_runtime_probe=secret_runtime_probe,
        postgres_registry_probe=_running_registry_probe,
        execution_bridge=_CertifiedBridge(),
    )

    text = json.dumps(report.to_payload())
    assert "postgresql://" not in text
    assert "token=abc123" not in text
    assert "redacted" in text


def _running_postgres_probe(env):
    assert env.get("TRIGGERTRADE_POSTGRES_DSN")
    return DashboardReadinessCheck("postgres_persistence", "RUNNING", "PostgreSQL persistence reachable")


def _running_runtime_probe(env):
    return (
        DashboardReadinessCheck(
            "heartbeat:trading-worker",
            "RUNNING",
            "worker hydrated durable state",
            datetime.now(UTC).isoformat(),
        ),
    )


def _running_registry_probe(env):
    return DashboardReadinessCheck(
        "research_config_registry",
        "RUNNING",
        "PostgreSQL Research configuration registry reachable; research=1, sets=1, rules=1",
    )


def _bybit_demo_env():
    return {
        "TRIGGERTRADE_BYBIT_ENV": "demo",
        "BYBIT_BASE_URL": "https://api-demo.bybit.com",
        "TRIGGERTRADE_MARKET": "linear",
        "TRIGGERTRADE_CATEGORY": "linear",
    }


class _CertifiedBridge:
    canonical_execution_bridge = True

    def close_position(self, **kwargs):
        return None

    def close_all_positions(self, **kwargs):
        return None


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
