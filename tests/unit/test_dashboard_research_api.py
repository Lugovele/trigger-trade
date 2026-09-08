from http import HTTPStatus

from triggertrade.dashboard.__main__ import create_server, render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.persistence import MessageStore, ResearchBacktestStatus, ResearchDemoStatus, ResearchStore
from tests.unit.test_dashboard_rules_api import _json_request, _start, _stop
from tests.unit.test_research_backend import _research_db


def test_research_api_create_list_detail_and_blocked_demo_are_backend_backed(tmp_path):
    db, rules = _research_db(tmp_path)
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = _start(server)
    try:
        current = rules.get_current_rules_version()
        created = _json_request(
            host,
            port,
            "POST",
            "/api/research",
            {
                "token": server.operator_control_token,
                "set_id": "triggertrade-futures-core",
                "set_version": "v1",
                "rules_version_id": current.rules_version_id,
            },
            expected=HTTPStatus.CREATED,
        )["research"]
        listed = _json_request(host, port, "GET", "/api/research")
        detail = _json_request(host, port, "GET", f"/api/research/{created['research_id']}")
        demo = _json_request(
            host,
            port,
            "POST",
            f"/api/research/{created['research_id']}/demo/start",
            {"token": server.operator_control_token},
            expected=HTTPStatus.CONFLICT,
        )["demo"]

        assert listed["research"][0]["research_id"] == created["research_id"]
        assert detail["research"]["set_version"] == "v1"
        assert detail["backtests"] == []
        assert demo["status"] == "BLOCKED"
        assert demo["blocked_reason"] == "research_demo_exchange_isolation_unavailable"
        assert MessageStore(db).get_unread_message_count() == 1
    finally:
        _stop(server, thread)


def test_research_api_write_routes_require_token_and_reject_path_like_ids(tmp_path):
    db, rules = _research_db(tmp_path)
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = _start(server)
    try:
        current = rules.get_current_rules_version()
        _json_request(
            host,
            port,
            "POST",
            "/api/research",
            {
                "token": "wrong",
                "set_id": "triggertrade-futures-core",
                "set_version": "v1",
                "rules_version_id": current.rules_version_id,
            },
            expected=HTTPStatus.FORBIDDEN,
        )
        bad = _json_request(
            host,
            port,
            "POST",
            "/api/research",
            {
                "token": server.operator_control_token,
                "set_id": "../triggertrade-futures-core",
                "set_version": "v1",
                "rules_version_id": current.rules_version_id,
            },
            expected=HTTPStatus.BAD_REQUEST,
        )

        assert "not found" in bad["error"] or "invalid" in bad["error"]
    finally:
        _stop(server, thread)


def test_research_api_use_selection_updates_backend_summary_metrics(tmp_path):
    db, rules = _research_db(tmp_path)
    current = rules.get_current_rules_version()
    store = ResearchStore(db)
    research, _created = store.create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=current.rules_version_id,
        rules_display_version=current.version,
        created_source="unit",
    )
    backtest = store.add_backtest_run(
        research_id=research.research_id,
        period_start="2026-09-01T00:00:00+00:00",
        period_end="2026-09-02T00:00:00+00:00",
        timeframe="1m",
        status=ResearchBacktestStatus.COMPLETED,
        metrics={"closed_trades": 7, "profit_factor": "1.8"},
    )
    demo = store.add_demo_run(
        research_id=research.research_id,
        status=ResearchDemoStatus.STOPPED,
        started_at="2026-09-03T00:00:00+00:00",
        stopped_at="2026-09-04T00:00:00+00:00",
        execution_scope_id="research-safe",
        account_scope="research-account",
        metrics={"closed_trades": 5, "profit_factor": "1.4"},
    )
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = _start(server)
    try:
        _json_request(
            host,
            port,
            "POST",
            f"/api/research/{research.research_id}/backtests/{backtest.run_id}/select",
            {"token": server.operator_control_token},
        )
        _json_request(
            host,
            port,
            "POST",
            f"/api/research/{research.research_id}/demo/{demo.run_id}/select",
            {"token": server.operator_control_token},
        )
        listed = _json_request(host, port, "GET", "/api/research")["research"][0]
        detail = _json_request(host, port, "GET", f"/api/research/{research.research_id}")

        assert listed["selected_backtest_profit_factor"] == "1.8"
        assert listed["selected_backtest_trades"] == 7
        assert listed["selected_demo_profit_factor"] == "1.4"
        assert listed["selected_demo_trades"] == 5
        assert detail["backtests"][0]["selected_for_use"] is True
        assert detail["demos"][0]["selected_for_use"] is True
    finally:
        _stop(server, thread)


def test_research_dashboard_removes_fixture_rows_without_logs_page(tmp_path):
    db, _rules = _research_db(tmp_path)
    html = render_dashboard(DashboardReadModel(db), initial_page="research")
    research_section = html[html.index('id="research"') : html.index('id="researchDetail"', html.index('id="research"'))]
    modal_section = html[html.index('id="newResearchModal"') : html.index('id="controlModal"')]

    assert "No Research records." in html
    assert "R-001" not in research_section
    assert "BT-012" not in html
    assert "DM-006" not in html
    assert 'data-page="logs"' not in html
    assert "openNewResearchModal" in html
    assert 'value="triggertrade-futures-core|v1"' in modal_section
    assert _rules.get_current_rules_version().rules_version_id in modal_section
    assert "Set 2 · v5" not in modal_section
    assert "Rules · v4" not in modal_section
    assert "location.reload" not in html
    assert "selectBacktestRun" in html
    assert "selectDemoRun" in html
    assert "stopDemoRun" in html
    assert "research_start" in html
