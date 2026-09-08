from datetime import UTC, datetime
from http import HTTPStatus
from http.client import HTTPConnection
import json
import threading

import pytest

from scripts.triggertrade_demo_soak import OPT_IN_FLAG, run_soak
from triggertrade.dashboard.__main__ import create_server
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.instruments import InstrumentCatalogRefreshResult
from triggertrade.persistence import InstrumentCatalogStore, LaneCandleLifecycle, RuntimeHeartbeat, RuntimeStore
from triggertrade.persistence.operator_state_store import OperatorStateStore
from triggertrade.services.futures_runtime import FuturesDualLaneResult, _heartbeat_outcome
from triggertrade.services.runtime import RuntimeCycleResult
from triggertrade.services.system_history import SystemHistoryExporter
from tests.unit.test_dashboard_read_model import _empty_db


def test_runtime_heartbeat_persists_across_restart_and_is_bounded_by_component(tmp_path):
    db = _empty_db(tmp_path)
    store = RuntimeStore(db)
    first = RuntimeHeartbeat(
        component="futures_runtime",
        status="RUNNING",
        observed_at="2026-09-08T12:00:00+00:00",
        detail="cycle ok",
        metadata={"symbol": "BTCUSDT"},
    )
    second = RuntimeHeartbeat(
        component="futures_runtime",
        status="DEGRADED",
        observed_at="2026-09-08T12:01:00+00:00",
        detail="market timeout",
        metadata={"symbol": "BTCUSDT"},
    )

    store.record_heartbeat(first)
    store.record_heartbeat(second)

    restarted = RuntimeStore(db).list_heartbeats()
    assert len(restarted) == 1
    assert restarted[0].component == "futures_runtime"
    assert restarted[0].status == "DEGRADED"
    assert restarted[0].detail == "market timeout"


def test_runtime_heartbeat_rejects_unbounded_or_unknown_status(tmp_path):
    store = RuntimeStore(_empty_db(tmp_path))

    with pytest.raises(Exception, match="heartbeat status"):
        store.record_heartbeat(
            RuntimeHeartbeat(
                component="futures_runtime",
                status="GREEN",
                observed_at=datetime.now(UTC).isoformat(),
            )
        )
    with pytest.raises(Exception, match="stable identifier"):
        store.record_heartbeat(
            RuntimeHeartbeat(
                component="../runtime",
                status="RUNNING",
                observed_at=datetime.now(UTC).isoformat(),
            )
        )


def test_demo_readiness_reports_factual_heartbeat_and_operator_block(tmp_path):
    db = _empty_db(tmp_path)
    RuntimeStore(db).record_heartbeat(
        RuntimeHeartbeat(
            component="futures_runtime",
            status="RUNNING",
            observed_at=datetime.now(UTC).isoformat(),
            detail="cycle ok",
        )
    )
    OperatorStateStore(db).pause(changed_at="2026-09-08T12:00:00+00:00", source="unit", reason="operator test")

    readiness = DashboardReadModel(db).get_demo_readiness()

    assert readiness.status == "BLOCKED"
    checks = {check.name: check for check in readiness.checks}
    assert checks["database"].status == "RUNNING"
    assert checks["heartbeat:futures_runtime"].status == "RUNNING"
    assert checks["operator"].status == "BLOCKED"
    assert checks["market_data"].status != "RUNNING"


def test_demo_readiness_uses_fresh_futures_lane_evidence(tmp_path):
    db = _empty_db(tmp_path)
    store = RuntimeStore(db)
    processed_at = datetime.now(UTC).isoformat()
    _record_ok_catalog(db, processed_at)
    _record_equity_snapshot(db, "fresh-account", processed_at)
    store.record_heartbeat(
        RuntimeHeartbeat(
            component="futures_runtime",
            status="RUNNING",
            observed_at=processed_at,
            detail="cycle completed",
        )
    )
    store.save_lane_lifecycle(
        _lane_lifecycle(
            candle_id="BTCUSDT:1m:2026-09-08T12:00:00+00:00",
            status="no_signal",
            processed_at=processed_at,
        )
    )

    readiness = DashboardReadModel(db).get_demo_readiness()

    checks = {check.name: check for check in readiness.checks}
    assert checks["market_data"].status == "RUNNING"
    assert "futures ACTIVE lane processed" in checks["market_data"].detail
    assert checks["account_data"].status == "RUNNING"
    assert "legacy runtime candle state" not in checks["market_data"].detail


def test_demo_readiness_reports_startup_without_market_data_evidence_as_unavailable(tmp_path):
    db = _empty_db(tmp_path)
    _record_ok_catalog(db, datetime.now(UTC).isoformat())

    readiness = DashboardReadModel(db).get_demo_readiness()

    checks = {check.name: check for check in readiness.checks}
    assert checks["market_data"].status == "UNAVAILABLE"
    assert "no futures or legacy market-data evidence" in checks["market_data"].detail
    assert checks["account_data"].status == "UNAVAILABLE"


def test_demo_readiness_does_not_treat_heartbeat_alone_as_market_data_running(tmp_path):
    db = _empty_db(tmp_path)
    processed_at = datetime.now(UTC).isoformat()
    _record_ok_catalog(db, processed_at)
    _record_equity_snapshot(db, "fresh-account", processed_at)
    RuntimeStore(db).record_heartbeat(
        RuntimeHeartbeat(
            component="futures_runtime",
            status="RUNNING",
            observed_at=processed_at,
            detail="cycle completed",
        )
    )

    readiness = DashboardReadModel(db).get_demo_readiness()

    checks = {check.name: check for check in readiness.checks}
    assert checks["heartbeat:futures_runtime"].status == "RUNNING"
    assert checks["market_data"].status == "UNAVAILABLE"


def test_demo_readiness_reports_stale_futures_lane_evidence_as_degraded(tmp_path):
    db = _empty_db(tmp_path)
    _record_ok_catalog(db, datetime.now(UTC).isoformat())
    RuntimeStore(db).save_lane_lifecycle(
        _lane_lifecycle(
            candle_id="BTCUSDT:1m:2000-01-01T00:00:00+00:00",
            status="no_signal",
            processed_at="2000-01-01T00:01:00+00:00",
        )
    )

    readiness = DashboardReadModel(db).get_demo_readiness()

    checks = {check.name: check for check in readiness.checks}
    assert checks["market_data"].status == "DEGRADED"
    assert "futures ACTIVE lane stale" in checks["market_data"].detail


def test_demo_readiness_latest_futures_failure_overrides_older_success(tmp_path):
    db = _empty_db(tmp_path)
    store = RuntimeStore(db)
    older = "2026-09-08T12:00:00+00:00"
    newer = datetime.now(UTC).isoformat()
    _record_ok_catalog(db, newer)
    store.save_lane_lifecycle(
        _lane_lifecycle(
            candle_id="BTCUSDT:1m:2026-09-08T12:00:00+00:00",
            status="no_signal",
            processed_at=older,
        )
    )
    store.save_lane_lifecycle(
        _lane_lifecycle(
            candle_id="BTCUSDT:1m:2026-09-08T12:01:00+00:00",
            status="execution_error",
            processed_at=newer,
            error="execution_error",
        )
    )

    readiness = DashboardReadModel(db).get_demo_readiness()

    checks = {check.name: check for check in readiness.checks}
    assert checks["market_data"].status == "DEGRADED"
    assert "latest status execution_error" in checks["market_data"].detail


def test_demo_readiness_newer_failure_heartbeat_overrides_older_futures_success(tmp_path):
    db = _empty_db(tmp_path)
    store = RuntimeStore(db)
    _record_ok_catalog(db, datetime.now(UTC).isoformat())
    store.save_lane_lifecycle(
        _lane_lifecycle(
            candle_id="BTCUSDT:1m:2026-09-08T12:00:00+00:00",
            status="no_signal",
            processed_at="2026-09-08T12:01:00+00:00",
        )
    )
    store.record_heartbeat(
        RuntimeHeartbeat(
            component="futures_runtime",
            status="DEGRADED",
            observed_at=datetime.now(UTC).isoformat(),
            detail="market_data_unavailable",
        )
    )

    readiness = DashboardReadModel(db).get_demo_readiness()

    checks = {check.name: check for check in readiness.checks}
    assert checks["market_data"].status == "DEGRADED"
    assert checks["market_data"].detail == "futures runtime reported market_data_unavailable"


def test_demo_readiness_reports_stale_account_snapshot_as_degraded(tmp_path):
    db = _empty_db(tmp_path)
    _record_equity_snapshot(db, "stale-account", "2000-01-01T00:00:00+00:00")

    readiness = DashboardReadModel(db).get_demo_readiness()

    checks = {check.name: check for check in readiness.checks}
    assert checks["account_data"].status == "DEGRADED"
    assert checks["account_data"].detail == "account snapshot stale 2000-01-01T00:00:00+00:00"


def test_demo_readiness_reports_stale_heartbeat_as_degraded(tmp_path):
    db = _empty_db(tmp_path)
    RuntimeStore(db).record_heartbeat(
        RuntimeHeartbeat(
            component="futures_runtime",
            status="RUNNING",
            observed_at="2000-01-01T00:00:00+00:00",
            detail="old cycle",
        )
    )

    readiness = DashboardReadModel(db).get_demo_readiness()

    checks = {check.name: check for check in readiness.checks}
    assert checks["heartbeat:futures_runtime"].status == "DEGRADED"
    assert checks["heartbeat:futures_runtime"].detail == "heartbeat is stale"
    assert readiness.status in {"DEGRADED", "UNAVAILABLE"}


def test_demo_readiness_reports_fresh_failed_catalog_as_degraded(tmp_path):
    db = _empty_db(tmp_path)
    InstrumentCatalogStore(db).record_failed_refresh(
        InstrumentCatalogRefreshResult(
            fetched_count=0,
            tradeable_count=0,
            excluded_count=0,
            updated_at=datetime.now(UTC).isoformat(),
            catalog_hash=None,
            status="FAILED",
            error="catalog refresh failed",
        )
    )

    readiness = DashboardReadModel(db).get_demo_readiness()

    checks = {check.name: check for check in readiness.checks}
    assert checks["instrument_catalog"].status == "DEGRADED"
    assert checks["instrument_catalog"].detail == "catalog refresh failed"
    assert readiness.status in {"DEGRADED", "UNAVAILABLE"}


def test_readiness_api_is_read_only_and_does_not_require_secret_payload(tmp_path):
    db = _empty_db(tmp_path)
    RuntimeStore(db).record_heartbeat(
        RuntimeHeartbeat(
            component="futures_runtime",
            status="RUNNING",
            observed_at=datetime.now(UTC).isoformat(),
            detail="cycle ok",
        )
    )
    server = create_server(port=0, db_path=db)
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
    assert payload["status"] in {"RUNNING", "DEGRADED", "BLOCKED", "UNAVAILABLE"}
    assert any(check["name"] == "heartbeat:futures_runtime" for check in payload["checks"])
    text = json.dumps(payload)
    assert "BYBIT_API_KEY" not in text
    assert "Authorization" not in text
    assert ".env" not in text


def test_system_history_export_includes_readiness_and_heartbeat(tmp_path):
    db = _empty_db(tmp_path)
    RuntimeStore(db).record_heartbeat(
        RuntimeHeartbeat(
            component="futures_runtime",
            status="RUNNING",
            observed_at="2026-09-08T12:00:00+00:00",
            detail="cycle ok",
            metadata={"symbol": "BTCUSDT"},
        )
    )

    text = SystemHistoryExporter(read_model=DashboardReadModel(db)).build_export(
        generated_at="2026-09-08T12:01:00+00:00"
    )

    assert "demo_readiness:" in text
    assert "runtime_heartbeat:" in text
    assert "futures_runtime" in text
    assert "cycle ok" in text


def test_demo_soak_harness_requires_explicit_flag_and_demo_linear_config(tmp_path):
    env = {
        "TRIGGERTRADE_RUNTIME_DB_PATH": str(tmp_path / "soak.sqlite3"),
        "TRIGGERTRADE_MARKET": "linear",
        "TRIGGERTRADE_CATEGORY": "linear",
        "TRIGGERTRADE_EXECUTION_VENUE": "bybit_demo_futures",
        "TRIGGERTRADE_ACTIVE_EXECUTION_VENUE": "bybit_demo_futures",
        "TRIGGERTRADE_TEST_EXECUTION_VENUE": "local_test_simulation",
        "TRIGGERTRADE_BYBIT_ENV": "demo",
        "BYBIT_BASE_URL": "https://api-demo.bybit.com",
        "BYBIT_API_KEY": "unit-key",
        "BYBIT_API_SECRET": "unit-secret",
    }

    with pytest.raises(RuntimeError, match=f"{OPT_IN_FLAG}=1"):
        run_soak(env, cycles=1)

    with pytest.raises(RuntimeError, match="refuses live trading"):
        run_soak({**env, OPT_IN_FLAG: "1", "TRIGGERTRADE_LIVE_TRADING_ENABLED": "true"}, cycles=1)


def test_heartbeat_outcome_does_not_report_running_after_execution_uncertainty():
    unknown = FuturesDualLaneResult(
        candle_id="BTCUSDT-1m-1",
        active=(RuntimeCycleResult("BTCUSDT-1m-1", "confirmed", execution_status="unknown", skipped_reason="execution_unknown"),),
        test=(),
    )
    error = FuturesDualLaneResult(
        candle_id="BTCUSDT-1m-2",
        active=(RuntimeCycleResult("BTCUSDT-1m-2", "confirmed", skipped_reason="execution_error"),),
        test=(),
    )

    assert _heartbeat_outcome(unknown) == ("BLOCKED", "execution_unknown")
    assert _heartbeat_outcome(error) == ("BLOCKED", "execution_error")


def _lane_lifecycle(
    *,
    candle_id: str,
    status: str,
    processed_at: str | None,
    error: str | None = None,
) -> LaneCandleLifecycle:
    return LaneCandleLifecycle(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=candle_id,
        candle_open_time=candle_id.removeprefix("BTCUSDT:1m:"),
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
        status=status,
        processed_at=processed_at,
        error=error,
    )


def _record_ok_catalog(db, updated_at: str) -> None:
    InstrumentCatalogStore(db).record_failed_refresh(
        InstrumentCatalogRefreshResult(
            fetched_count=1,
            tradeable_count=1,
            excluded_count=0,
            updated_at=updated_at,
            catalog_hash="unit-catalog",
            status="OK",
            error=None,
        )
    )


def _record_equity_snapshot(db, snapshot_id: str, observed_at: str) -> None:
    from decimal import Decimal

    from triggertrade.accounting import EquitySnapshot
    from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore

    FuturesAccountingStore(db).record_equity_snapshot(
        EquitySnapshot(
            snapshot_id=snapshot_id,
            observed_at=observed_at,
            source="bybit_demo_account",
            wallet_balance=Decimal("100"),
            equity=Decimal("100"),
            available_margin=Decimal("100"),
            used_margin=Decimal("0"),
            unrealized_pnl=Decimal("0"),
            realized_pnl=Decimal("0"),
            running_peak=Decimal("100"),
            drawdown_absolute=Decimal("0"),
            drawdown_percent=Decimal("0"),
            max_drawdown=Decimal("0"),
        )
    )
