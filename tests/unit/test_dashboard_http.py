from http import HTTPStatus
from urllib.request import Request, urlopen
import threading

import pytest

from triggertrade.dashboard.__main__ import DEFAULT_HOST, create_server, render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel, OverviewView, TriggerSetRow
from tests.unit.test_dashboard_read_model import _empty_db, _save_buy_lifecycle, _save_no_signal, _save_rejected_lifecycle


def test_default_bind_is_localhost(tmp_path):
    server = create_server(port=0, db_path=tmp_path / "missing.sqlite3")
    try:
        assert server.server_address[0] == DEFAULT_HOST
    finally:
        server.server_close()


def test_non_local_bind_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        create_server(host="0.0.0.0", port=0, db_path=tmp_path / "missing.sqlite3")


def test_empty_state_renders_without_traceback_or_secrets(tmp_path):
    html = render_dashboard(DashboardReadModel(tmp_path / "missing.sqlite3"))

    assert "Overview" in html
    assert "Rules" in html
    assert "LIVE" in html
    assert "TEST" in html
    assert "No completed Demo futures trades yet" in html
    assert "Traceback" not in html
    assert "BYBIT_API_SECRET" not in html


def test_activity_risk_rejection_trade_and_trace_render(tmp_path):
    db = _empty_db(tmp_path)
    _save_no_signal(db)
    _save_buy_lifecycle(db)
    _save_rejected_lifecycle(db)

    html = render_dashboard(DashboardReadModel(db), "BTCUSDT:1m:2026-09-05T12:01:00+00:00")

    assert "NO_SIGNAL" in html
    assert "REJECTED: RSK-003" in html
    assert "LIVE Trades" in html
    assert "Current Futures Position" in html
    assert "Trigger sets" in html
    assert "Rule registry" in html
    assert "TRG-001" in html
    assert "STR-001" in html
    assert "Traceback" not in html


def test_dashboard_http_routes_are_read_only(tmp_path):
    db = _empty_db(tmp_path)
    _save_no_signal(db)
    server = create_server(port=0, db_path=db)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"
    try:
        with urlopen(f"{base_url}/", timeout=5) as response:
            body = response.read().decode("utf-8")
            assert response.status == HTTPStatus.OK
            assert "TriggerTrade" in body
            assert "NO_SIGNAL" in body

        with pytest.raises(Exception):
            urlopen(f"{base_url}/trace/not-present", timeout=5)

        request = Request(f"{base_url}/order/create", method="POST", data=b"")
        with pytest.raises(Exception):
            urlopen(request, timeout=5)
    finally:
        server.shutdown()
        server.server_close()


def test_no_write_or_order_route_names_rendered(tmp_path):
    db = _empty_db(tmp_path)
    _save_buy_lifecycle(db)
    html = render_dashboard(DashboardReadModel(db))

    assert "/order/create" not in html
    assert "ExecutionService" not in html
    assert "https://api-demo.bybit.com" not in html
    assert "BYBIT_API_SECRET" not in html


def test_operator_pause_resume_controls_require_confirmation(tmp_path):
    html = render_dashboard(DashboardReadModel(_empty_db(tmp_path)))

    assert "confirmStopTrading()" in html
    assert "Stop new trades?" in html
    assert "New ACTIVE executions will be blocked." in html
    assert "/operator/pause" in html
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


def test_trigger_set_drawer_data_is_script_escaped():
    class FakeModel:
        def get_live_overview(self):
            return OverviewView("ACTIVE", "ACTIVE", "bad", 1, "-", "none", 0, "none")

        def get_test_overview(self):
            return OverviewView("TEST", "UNKNOWN", "-", 0, "-", "none", 0, "none")

        def get_latest_lane_trace(self, lane):
            return None

        def list_trigger_sets(self):
            return (
                TriggerSetRow(
                    set_id="bad</script><script>alert(1)</script>",
                    version="v1",
                    purpose="xss probe",
                    rules_count=1,
                    created_at="2026-09-05T00:00:00+00:00",
                    status="ACTIVE",
                    symbol="BTCUSDT",
                    timeframe="1m",
                    rules=({"rule_id": "BAD", "condition": "</script><script>alert(2)</script>"},),
                ),
            )

        def list_rules(self):
            return ()

        def list_lane_trades(self, lane):
            return ()

        def list_logs(self):
            return ()

        def get_api_health(self):
            return ()

    html = render_dashboard(FakeModel())

    assert "</script><script>" not in html
    assert "setRules.replaceChildren" in html
    assert "innerHTML=s.rules" not in html



def test_analytics_and_rule_detail_routes_render(tmp_path):
    from http.client import HTTPConnection
    from triggertrade.dashboard.__main__ import create_server
    from triggertrade.persistence import TriggerSetStore, bootstrap_current_trigger_sets

    db = tmp_path / "dashboard.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    import threading

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/")
        html = conn.getresponse().read().decode("utf-8")
        assert "Analytics" in html
        assert "Performance" in html
        assert "Recommendations" in html
        assert "No set-level runtime evidence recorded yet." in html

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


def test_dashboard_new_routes_are_read_only_and_safe_for_missing_ids(tmp_path):
    from http.client import HTTPConnection
    from triggertrade.dashboard.__main__ import create_server
    from triggertrade.persistence import TriggerSetStore, bootstrap_current_trigger_sets

    db = tmp_path / "dashboard.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    import threading

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

def test_dashboard_rules_and_analytics_alias_routes_render_bootstrapped_registry(tmp_path):
    from http.client import HTTPConnection
    from triggertrade.dashboard.__main__ import create_server_from_env

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
        assert '<button class="tabbtn active" data-page="rules">Rules</button>' in rules_html
        assert '<section class="page active" id="rules">' in rules_html
        assert '<section class="page active" id="overview">' not in rules_html
        assert "TRG-001" in rules_html
        assert "TRG-002" in rules_html
        assert "triggertrade-core-candidate" in rules_html

        conn.request("GET", "/analytics")
        analytics = conn.getresponse()
        analytics_html = analytics.read().decode("utf-8")
        assert analytics.status == 200
        assert '<button class="tabbtn active" data-page="analytics">Analytics</button>' in analytics_html
        assert '<section class="page active" id="analytics">' in analytics_html
        assert '<section class="page active" id="overview">' not in analytics_html
        assert "REC-TRG-VOLUME-001" in analytics_html
        assert "No set-level runtime evidence recorded yet." in analytics_html
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
