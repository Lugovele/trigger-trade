from http import HTTPStatus
from http.client import HTTPConnection
from urllib.request import Request, urlopen
import threading

import pytest

from triggertrade.dashboard.__main__ import DEFAULT_HOST, create_server, create_server_from_env, render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from tests.unit.test_dashboard_read_model import _empty_db, _save_no_signal


def test_default_bind_is_localhost(tmp_path):
    server = create_server(port=0, db_path=tmp_path / "missing.sqlite3")
    try:
        assert server.server_address[0] == DEFAULT_HOST
    finally:
        server.server_close()


def test_non_local_bind_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        create_server(host="0.0.0.0", port=0, db_path=tmp_path / "missing.sqlite3")


def test_empty_state_renders_approved_product_ui_without_traceback_or_secrets(tmp_path):
    html = render_dashboard(DashboardReadModel(tmp_path / "missing.sqlite3"))

    assert "TriggerTrade" in html
    assert "Portfolio" in html
    assert "Sets" in html
    assert "Rules" in html
    assert "Research" in html
    assert "Open positions" in html
    assert "Current Rules Configuration" in html
    assert "New Research" in html
    assert "Traceback" not in html
    assert "BYBIT_API_SECRET" not in html
    assert "Authorization" not in html
    assert "UI fixture preview" in html
    assert "not live trading/account facts" in html


def test_dashboard_http_product_routes_are_read_only(tmp_path):
    db = _empty_db(tmp_path)
    _save_no_signal(db)
    server = create_server(port=0, db_path=db)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"
    try:
        for route, expected in (
            ("/", "Portfolio"),
            ("/portfolio", "Open positions"),
            ("/sets", "Trigger Catalog"),
            ("/trigger-catalog", "What it checks"),
            ("/trigger-detail", "formula-block"),
            ("/rules", "Current Rules Configuration"),
            ("/rules-version", "Rules · v"),
            ("/research", "New Research"),
            ("/research-detail", "Compare Demo to Active"),
            ("/messages", "Messages"),
            ("/analytics", "Research"),
        ):
            with urlopen(f"{base_url}{route}", timeout=5) as response:
                body = response.read().decode("utf-8")
                assert response.status == HTTPStatus.OK
                assert expected in body
                assert "Traceback" not in body

        request = Request(f"{base_url}/order/create", method="POST", data=b"")
        with pytest.raises(Exception):
            urlopen(request, timeout=5)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_no_write_or_order_route_names_rendered(tmp_path):
    db = _empty_db(tmp_path)
    html = render_dashboard(DashboardReadModel(db))

    assert "/order/create" not in html
    assert "ExecutionService" not in html
    assert "https://api-demo.bybit.com" not in html
    assert "api.bybit.com" not in html
    assert "BYBIT_API_SECRET" not in html
    assert "BYBIT_API_KEY" not in html


def test_operator_controls_are_protected_frontend_boundaries(tmp_path):
    db = _empty_db(tmp_path)
    server = create_server(port=0, db_path=db)
    try:
        html = render_dashboard(server.read_model)
    finally:
        server.server_close()

    assert "Pause Entries" in html
    assert "Close All" in html
    assert "Pause new entries?" in html
    assert "The bot will stop opening new positions." in html
    assert "Existing positions remain active and continue to be managed." in html
    assert "Type CLOSE ALL to confirm" in html
    assert 'id="operatorPauseForm"' in html
    assert 'action="/operator/pause"' in html
    assert f'value="{server.operator_control_token}"' in html
    assert 'id="operatorResumeForm"' in html
    assert 'action="/operator/resume"' in html
    assert "/order/create" not in html
    assert "manual BUY" not in html
    assert "manual SELL" not in html


def test_secret_like_trace_values_are_not_rendered(tmp_path):
    db = _empty_db(tmp_path)
    from triggertrade.persistence import CandleLifecycle, RuntimeStore

    RuntimeStore(db).save_lifecycle(
        CandleLifecycle(
            candle_id="BTCUSDT:1m:2026-09-05T12:06:00+00:00",
            symbol="BTCUSDT",
            timeframe="1",
            candle_open_time="2026-09-05T12:06:00+00:00",
            status="execution_error",
            error="BYBIT_API_SECRET=unit-signing-value",
        )
    )

    html = render_dashboard(DashboardReadModel(db), "BTCUSDT:1m:2026-09-05T12:06:00+00:00")

    assert "BYBIT_API_SECRET" not in html
    assert "unit-signing-value" not in html


def test_detail_routes_remain_available_for_existing_read_model_pages(tmp_path):
    from triggertrade.persistence import TriggerSetStore, bootstrap_current_trigger_sets

    db = tmp_path / "dashboard.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/rules/TRG-002/0.1.0")
        detail = conn.getresponse().read().decode("utf-8")
        assert "Robust Volume Confirmation" in detail
        assert "relative_volume &gt;= 2.0 AND volume_percentile &gt;= 90" in detail
        assert "Version History" in detail
        assert "Used In Trigger Sets" in detail
        assert "TRG-VOLUME" in detail

        conn.request("GET", "/recommendations/REC-TRG-VOLUME-001")
        recommendation = conn.getresponse().read().decode("utf-8")
        assert "Observation" in recommendation
        assert "Hypothesis" in recommendation
        assert "Recommended Experiment" in recommendation
        assert "No historical performance" in recommendation
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_dashboard_missing_detail_ids_are_safe_404(tmp_path):
    from triggertrade.persistence import TriggerSetStore, bootstrap_current_trigger_sets

    db = tmp_path / "dashboard.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("POST", "/recommendations/REC-TRG-VOLUME-001")
        response = conn.getresponse()
        response.read()
        assert response.status == 405

        conn.request("GET", "/rules/DOES-NOT-EXIST")
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        assert response.status == 404
        assert "Traceback" not in body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_dashboard_routes_render_bootstrapped_registry_under_new_ia(tmp_path):
    db = tmp_path / "dashboard.sqlite3"
    server, initialized_db = create_server_from_env(
        {"TRIGGERTRADE_RUNTIME_DB_PATH": str(db), "TRIGGERTRADE_DASHBOARD_PORT": "0"},
        env_file=tmp_path / "missing.env",
    )
    assert initialized_db == db
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/rules")
        rules = conn.getresponse()
        rules_html = rules.read().decode("utf-8")
        assert rules.status == 200
        assert "Current Rules Configuration" in rules_html
        assert "Save as New Version" in rules_html
        assert "Portfolio" in rules_html
        assert "Research" in rules_html
        assert "Overview" not in rules_html

        conn.request("GET", "/sets")
        sets = conn.getresponse()
        sets_html = sets.read().decode("utf-8")
        assert sets.status == 200
        assert "Set 1" in sets_html
        assert "Set 2" in sets_html
        assert "TRG-001" in sets_html
        assert "TRG-002" in sets_html

        conn.request("GET", "/analytics")
        legacy = conn.getresponse()
        legacy_html = legacy.read().decode("utf-8")
        assert legacy.status == 200
        assert "Research" in legacy_html
        assert "Backtest Profit Factor" in legacy_html
        assert "Demo Profit Factor" in legacy_html
        assert "Forward Test" not in legacy_html
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
