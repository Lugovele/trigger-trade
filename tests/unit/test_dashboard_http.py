from http import HTTPStatus
from http.client import HTTPConnection
from urllib.request import Request, urlopen
import threading

import pytest

from triggertrade.dashboard.__main__ import DEFAULT_HOST, create_server, create_server_from_env, render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.persistence.operator_state_store import OperatorStateStore
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
    assert "Dashboard state is loaded from backend read models" in html
    assert "sample data" in html


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
            ("/rules-version", "Rules unavailable"),
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


def test_portfolio_close_actions_fail_closed_without_execution_bridge(tmp_path):
    db = _empty_db(tmp_path)
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        token = server.operator_control_token
        conn = HTTPConnection(host, port, timeout=2)
        conn.request(
            "POST",
            "/operator/close-one",
            body=f"confirm=yes&token={token}&position_id=pos-1&symbol=BTCUSDT",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        assert response.status == HTTPStatus.SERVICE_UNAVAILABLE
        assert "execution bridge is not attached" in body

        conn.request(
            "POST",
            "/operator/close-all",
            body=f"confirm=yes&token={token}&phrase=CLOSE+ALL",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        assert response.status == HTTPStatus.SERVICE_UNAVAILABLE
        assert "execution bridge is not attached" in body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    audit = OperatorStateStore(db).operator_action_rows()
    assert [row.action for row in audit[:2]] == ["CLOSE_ALL", "CLOSE_ONE"]
    assert all(row.result == "FAILED" for row in audit[:2])


def test_portfolio_close_actions_use_injected_backend_contract(tmp_path):
    class FakeOperatorActions:
        def __init__(self):
            self.closed_one = None
            self.closed_all = False

        def close_position(self, *, position_id, symbol, close_reason):
            self.closed_one = (position_id, symbol, close_reason)

        def close_all_positions(self, *, scope):
            self.closed_all = scope == "ACTIVE"

    db = _empty_db(tmp_path)
    actions = FakeOperatorActions()
    server = create_server(port=0, db_path=db, operator_actions=actions)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        token = server.operator_control_token
        conn = HTTPConnection(host, port, timeout=2)
        conn.request(
            "POST",
            "/operator/close-one",
            body=f"confirm=yes&token={token}&position_id=pos-1&symbol=BTCUSDT",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.SEE_OTHER
        assert actions.closed_one == ("pos-1", "BTCUSDT", "MANUAL")

        conn.request(
            "POST",
            "/operator/close-all",
            body=f"confirm=yes&token={token}&phrase=CLOSE+ALL",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.SEE_OTHER
        assert actions.closed_all is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    audit = OperatorStateStore(db).operator_action_rows()
    assert [row.action for row in audit[:2]] == ["CLOSE_ALL", "CLOSE_ONE"]
    assert all(row.result == "SUCCESS" for row in audit[:2])


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


def test_trigger_registry_routes_use_exact_identity_and_no_fixture_fallback(tmp_path):
    from triggertrade.persistence import TriggerSetStore, bootstrap_current_trigger_sets

    db = tmp_path / "dashboard.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/triggers/TRG-002/0.2.0")
        response = conn.getresponse()
        detail = response.read().decode("utf-8")
        assert response.status == 200
        assert "Robust Volume Confirmation" in detail
        assert "Version 0.2.0" in detail
        assert "triggertrade-futures-candidate" in detail
        assert "Set 1" not in _section(detail, 'id="trigger-detail"', 'id="rules"')

        conn.request("GET", "/triggers/TRG-002/9.9.9")
        missing = conn.getresponse()
        body = missing.read().decode("utf-8")
        assert missing.status == 404
        assert "Traceback" not in body

        conn.request("GET", "/set/triggertrade-futures-core/v1")
        set_response = conn.getresponse()
        assert set_response.status == 200

        conn.request("GET", "/set/triggertrade-futures-core/v9")
        missing_set = conn.getresponse()
        missing_set.read()
        assert missing_set.status == 404
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
        assert "Set 1" not in _section(sets_html, 'id="sets"', 'id="trigger-catalog"')
        assert "triggertrade-futures-core" in sets_html
        assert "triggertrade-futures-candidate" in sets_html
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


def _section(html: str, start: str, end: str) -> str:
    start_index = html.index(start)
    end_index = html.index(end, start_index + len(start))
    return html[start_index:end_index]
