from http import HTTPStatus
from http.client import HTTPConnection
from urllib.request import Request, urlopen
from pathlib import Path
import threading
from uuid import uuid4

import pytest

from triggertrade.dashboard.__main__ import (
    DEFAULT_HOST,
    LOCAL_DEV_OPERATOR_COOKIE,
    LOCAL_DEV_OPERATOR_HEADER,
    create_server,
    create_server_from_env,
    render_dashboard,
)
from triggertrade.dashboard.product_ui import render_product_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.persistence import TraceStore
from triggertrade.persistence.operator_state_store import OperatorStateStore
from triggertrade.services.operator_auth import OPERATOR_AUTH_EVENT_TYPE, OperatorCommandAuthorizer
from tests.unit.test_dashboard_read_model import _empty_db, _save_no_signal


def _tmpdir():
    path = Path(".tt-tmp") / f"http-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_default_bind_is_localhost():
    tmp_path = _tmpdir()
    server = create_server(port=0, db_path=tmp_path / "missing.sqlite3")
    try:
        assert server.server_address[0] == DEFAULT_HOST
    finally:
        server.server_close()


@pytest.mark.parametrize("host", [DEFAULT_HOST, "0.0.0.0"])
def test_allowed_dashboard_hosts_can_bind(host):
    tmp_path = _tmpdir()
    server = create_server(host=host, port=0, db_path=tmp_path / "missing.sqlite3")
    try:
        assert server.server_address[0] == host
    finally:
        server.server_close()


def test_unsupported_dashboard_host_is_rejected():
    tmp_path = _tmpdir()
    with pytest.raises(ValueError, match="dashboard host must be one of"):
        create_server(host="192.0.2.10", port=0, db_path=tmp_path / "missing.sqlite3")


def test_empty_state_renders_final_product_ui_without_traceback_or_secrets():
    tmp_path = _tmpdir()
    html = render_dashboard(DashboardReadModel(tmp_path / "missing.sqlite3"))

    assert "TriggerTrade" in html
    assert "Overview" in html
    assert "Trading Configuration" in html
    assert "Research" in html
    assert "Positions" in html
    assert "New Research" in html
    assert "Traceback" not in html
    assert "BYBIT_API_SECRET" not in html
    assert "Authorization" not in html
    assert "sample data" not in html.lower()


def test_dashboard_http_product_routes_use_new_information_architecture():
    tmp_path = _tmpdir()
    db = _empty_db(tmp_path)
    _save_no_signal(db)
    server = create_server(port=0, db_path=db)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"
    try:
        for route, expected in (
            ("/", "Overview"),
            ("/overview", "Positions"),
            ("/portfolio", "Positions"),
            ("/trading-configuration", "Trading Rules"),
            ("/sets", "Trading Configuration"),
            ("/trigger-catalog", "Trading Configuration"),
            ("/rules", "Trading Configuration"),
            ("/research", "New Research"),
            ("/research-detail", "Run 7D"),
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


def test_no_write_or_order_route_names_rendered():
    tmp_path = _tmpdir()
    db = _empty_db(tmp_path)
    html = render_dashboard(DashboardReadModel(db))

    assert "/order/create" not in html
    assert "ExecutionService" not in html
    assert "https://api-demo.bybit.com" not in html
    assert "api.bybit.com" not in html
    assert "BYBIT_API_SECRET" not in html
    assert "BYBIT_API_KEY" not in html


def test_operator_controls_are_protected_frontend_boundaries():
    tmp_path = _tmpdir()
    db = _empty_db(tmp_path)
    server = create_server(port=0, db_path=db)
    try:
        html = render_dashboard(server.read_model)
    finally:
        server.server_close()

    assert "Pause Entries" in html
    assert "Close All" in html
    assert "Confirm pause new entries." in html
    assert "operatorCommandStatus" in html
    assert 'id="operatorPauseForm"' in html
    assert 'action="/operator/pause"' in html
    assert server.operator_control_token == ""
    assert 'id="operatorResumeForm"' in html
    assert 'action="/operator/resume"' in html
    assert "/order/create" not in html
    assert "manual BUY" not in html
    assert "manual SELL" not in html


def test_product_renderer_never_emits_process_local_token_argument():
    html = render_product_dashboard(operator_control_token="process-secret-token", operator_command_submit_enabled=True)

    assert "process-secret-token" not in html
    assert 'name="token"' not in html


def test_local_dev_browser_commands_use_http_only_cookie_without_rendered_token():
    tmp_path = _tmpdir()
    db = _empty_db(tmp_path)
    server = create_server(
        port=0,
        db_path=db,
        operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"),
    )
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/overview")
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        cookie = response.getheader("Set-Cookie") or ""

        assert response.status == HTTPStatus.OK
        assert LOCAL_DEV_OPERATOR_COOKIE in cookie
        assert "HttpOnly" in cookie
        assert "SameSite=Strict" in cookie
        assert server.operator_control_token
        assert server.operator_control_token not in body
        assert '"canSubmitOperatorControl": true' in body
        assert 'name="token"' not in body

        conn.request(
            "POST",
            "/operator/pause",
            body="confirm=yes",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": cookie,
                LOCAL_DEV_OPERATOR_HEADER: "1",
                "Origin": f"http://{host}:{port}",
                "Referer": f"http://{host}:{port}/overview",
            },
        )
        pause = conn.getresponse()
        pause.read()
        assert pause.status == HTTPStatus.SEE_OTHER
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert OperatorStateStore(db).get_trading_state().state.value == "TRADING_PAUSED"


def test_local_dev_cookie_commands_require_same_origin_header():
    tmp_path = _tmpdir()
    db = _empty_db(tmp_path)
    server = create_server(
        port=0,
        db_path=db,
        operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"),
    )
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/overview")
        response = conn.getresponse()
        response.read()
        cookie = response.getheader("Set-Cookie") or ""

        conn.request(
            "POST",
            "/operator/pause",
            body="confirm=yes",
            headers={"Content-Type": "application/x-www-form-urlencoded", "Cookie": cookie},
        )
        missing_header = conn.getresponse()
        missing_header.read()
        assert missing_header.status == HTTPStatus.BAD_REQUEST

        conn.request(
            "POST",
            "/operator/pause",
            body="confirm=yes",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": cookie,
                LOCAL_DEV_OPERATOR_HEADER: "1",
                "Origin": "http://evil.localhost",
            },
        )
        bad_origin = conn.getresponse()
        bad_origin.read()
        assert bad_origin.status == HTTPStatus.BAD_REQUEST
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert OperatorStateStore(db).get_trading_state().state.value == "TRADING_ENABLED"


def test_local_dev_browser_cookie_is_loopback_only_when_binding_all_interfaces():
    tmp_path = _tmpdir()
    db = _empty_db(tmp_path)
    server = create_server(
        host="0.0.0.0",
        port=0,
        db_path=db,
        operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"),
    )
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=2)
        conn.request("GET", "/overview")
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        assert response.status == HTTPStatus.OK
        assert response.getheader("Set-Cookie") is None
        assert server.operator_control_token == ""
        assert '"canSubmitOperatorControl": false' in body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_managed_oidc_operator_pause_does_not_require_local_token():
    tmp_path = _tmpdir()
    db = _empty_db(tmp_path)
    authorizer = OperatorCommandAuthorizer(db, auth_mode="managed_oidc")
    server = create_server(port=0, db_path=db, operator_authorizer=authorizer)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request(
            "POST",
            "/operator/pause",
            body="confirm=yes",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-MS-CLIENT-PRINCIPAL-ID": "operator-1",
                "X-MS-CLIENT-PRINCIPAL-ROLES": "TriggerTrade.Operator",
            },
        )
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.SEE_OTHER
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    state = OperatorStateStore(db).get_trading_state()
    assert state.state.value == "TRADING_PAUSED"
    event = TraceStore(db).list_audit_events(event_type=OPERATOR_AUTH_EVENT_TYPE)[0]
    assert event.source_id == "operator-1"
    assert event.safe_metadata["authz_source"] == "managed_oidc"
    assert server.operator_control_token == ""


def test_portfolio_close_actions_fail_closed_without_execution_bridge():
    tmp_path = _tmpdir()
    db = _empty_db(tmp_path)
    server = create_server(
        port=0,
        db_path=db,
        operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"),
    )
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


def test_portfolio_close_actions_use_injected_backend_contract():
    tmp_path = _tmpdir()
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
    server = create_server(
        port=0,
        db_path=db,
        operator_actions=actions,
        operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"),
    )
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


def test_secret_like_trace_values_are_not_rendered():
    tmp_path = _tmpdir()
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


def test_detail_routes_remain_available_for_existing_read_model_pages():
    tmp_path = _tmpdir()
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

        conn.request("GET", "/triggers/TRG-002/0.2.0")
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert "Robust Volume Confirmation" in body

        conn.request("GET", "/triggers/TRG-002/9.9.9")
        missing = conn.getresponse()
        missing.read()
        assert missing.status == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_dashboard_routes_render_bootstrapped_registry_under_new_ia():
    tmp_path = _tmpdir()
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
        assert "Trading Configuration" in rules_html
        assert "Save as New Version" in rules_html
        assert "Overview" in rules_html
        assert "Research" in rules_html
        assert "Portfolio</button>" not in rules_html

        conn.request("GET", "/sets")
        sets = conn.getresponse()
        sets_html = sets.read().decode("utf-8")
        assert sets.status == 200
        assert "triggertrade-futures-core" in sets_html
        assert "triggertrade-futures-candidate" in sets_html
        assert "TRG-001" in sets_html
        assert "TRG-002" in sets_html
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
