from http import HTTPStatus
from http.client import HTTPConnection
from decimal import Decimal
import json
import sqlite3

import triggertrade.dashboard.__main__ as dashboard_main
from triggertrade.dashboard.__main__ import create_server, render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.persistence import (
    MessageStore,
    ResearchBacktestStatus,
    ResearchDecision,
    ResearchDemoStatus,
    ResearchRecord,
    ResearchStatus,
    ResearchStore,
)
from triggertrade.services.operator_auth import OperatorCommandAuthorizer
from triggertrade.trigger_sets import TriggerSetStatus, TriggerSetVersion
from tests.unit.test_dashboard_rules_api import _json_request, _start, _stop
from tests.unit.test_operator_command_auth import _managed_principal_headers
from tests.unit.test_research_backend import _research_db


def test_research_promotion_governance_env_wiring_is_postgres_backed(monkeypatch):
    calls = {}

    class FakeSettings:
        dsn = "postgresql://unit/db"
        schema = "unit_schema"

        @classmethod
        def from_env(cls, env):
            calls["env"] = env
            return cls()

    class FakeFactory:
        def __init__(self, *, dsn, schema):
            self.dsn = dsn
            self.schema = schema

    class FakeClient:
        def __init__(self, factory):
            self.factory = factory

    monkeypatch.setattr(dashboard_main, "PostgresSettings", FakeSettings)
    monkeypatch.setattr(dashboard_main, "PostgresConnectionFactory", FakeFactory)
    monkeypatch.setattr(dashboard_main, "ResearchPromotionGovernanceClient", FakeClient)
    monkeypatch.setattr(
        dashboard_main,
        "apply_postgres_migrations",
        lambda *, dsn, schema: calls.setdefault("migrations", (dsn, schema)),
    )

    assert dashboard_main._promotion_governance_from_env({}) is None
    client = dashboard_main._promotion_governance_from_env({"TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit/db"})

    assert isinstance(client, FakeClient)
    assert client.factory.dsn == "postgresql://unit/db"
    assert client.factory.schema == "unit_schema"
    assert calls["migrations"] == ("postgresql://unit/db", "unit_schema")


def test_research_api_create_list_detail_and_blocked_demo_are_backend_backed(tmp_path):
    db, rules = _research_db(tmp_path)
    server = create_server(port=0, db_path=db, operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"))
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


def test_managed_oidc_research_create_and_demo_use_same_production_auth_context(tmp_path):
    db, rules = _research_db(tmp_path)
    authorizer = OperatorCommandAuthorizer(db, auth_mode="managed_oidc", allowed_principals=("operator-1",))
    server = create_server(port=0, db_path=db, operator_authorizer=authorizer)
    host, port = server.server_address
    thread = _start(server)
    try:
        current = rules.get_current_rules_version()
        created = _managed_json_request(
            host,
            port,
            "POST",
            "/api/research",
            {
                "set_id": "triggertrade-futures-core",
                "set_version": "v1",
                "rules_version_id": current.rules_version_id,
                "idempotency_key": "research-create-managed",
            },
            expected=HTTPStatus.CREATED,
        )["research"]
        demo = _managed_json_request(
            host,
            port,
            "POST",
            f"/api/research/{created['research_id']}/demo/start",
            {"idempotency_key": "research-demo-managed"},
            expected=HTTPStatus.CONFLICT,
        )["demo"]
        anonymous = _json_request(
            host,
            port,
            "POST",
            "/api/research",
            {
                "set_id": "triggertrade-futures-core",
                "set_version": "v1",
                "rules_version_id": current.rules_version_id,
            },
            expected=HTTPStatus.FORBIDDEN,
        )

        assert created["set_id"] == "triggertrade-futures-core"
        assert demo["status"] == "BLOCKED"
        assert anonymous["error"] == "operator token required"
        assert server.operator_control_token == ""
    finally:
        _stop(server, thread)


def test_research_api_write_routes_require_token_and_reject_path_like_ids(tmp_path):
    db, rules = _research_db(tmp_path)
    server = create_server(port=0, db_path=db, operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"))
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
    server = create_server(port=0, db_path=db, operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"))
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


def test_research_api_make_active_without_canonical_governance_store_is_blocked(tmp_path):
    db, rules = _research_db(tmp_path)
    current = rules.get_current_rules_version()
    candidate_rules = rules.create_rules_version_from_current(
        changes={"fixed_take_profit_pct": Decimal("0.016")},
        created_source="unit",
    ).rules
    research, _created = ResearchStore(db).create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=candidate_rules.rules_version_id,
        rules_display_version=candidate_rules.version,
        created_source="unit",
    )
    demo = ResearchStore(db).add_demo_run(
        research_id=research.research_id,
        status=ResearchDemoStatus.STOPPED,
        started_at="2026-09-08T12:00:00+00:00",
        stopped_at="2026-09-08T13:00:00+00:00",
        execution_scope_id="research-safe",
        account_scope="research-account",
    )
    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE trading_rules_current SET rules_version_id = ?, updated_at = ? WHERE scope = ?",
            (current.rules_version_id, "2026-09-08T12:00:00+00:00", "LIVE"),
        )
    server = create_server(port=0, db_path=db, operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"))
    host, port = server.server_address
    thread = _start(server)
    try:
        result = _json_request(
            host,
            port,
            "POST",
            f"/api/research/{research.research_id}/demo/{demo.run_id}/select",
            {"token": server.operator_control_token},
        )
        result = _json_request(
            host,
            port,
            "POST",
            f"/api/research/{research.research_id}/decision/make-active",
            {"token": server.operator_control_token, "idempotency_key": "dashboard-promote-001"},
            expected=HTTPStatus.CONFLICT,
        )
        detail = _json_request(host, port, "GET", f"/api/research/{research.research_id}")["research"]

        assert result["blocked"] is True
        assert result["research"]["decision"] == "MAKE_ACTIVE_BLOCKED"
        assert result["research"]["promoted_set_version"] is None
        assert result["research"]["promoted_rules_version_id"] is None
        assert result["research"]["made_active_at"] is None
        assert detail["promotion_result_metadata"] in ({}, "{}")
    finally:
        _stop(server, thread)


def test_research_api_make_active_blocked_state_is_factual(tmp_path):
    db, rules = _research_db(tmp_path)
    current = rules.get_current_rules_version()
    research, _created = ResearchStore(db).create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=current.rules_version_id,
        rules_display_version=current.version,
        created_source="unit",
    )
    demo = ResearchStore(db).add_demo_run(
        research_id=research.research_id,
        status=ResearchDemoStatus.RUNNING,
        started_at="2026-09-08T12:00:00+00:00",
        execution_scope_id="research-safe",
        account_scope="research-account",
    )
    server = create_server(port=0, db_path=db, operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"))
    host, port = server.server_address
    thread = _start(server)
    try:
        result = _json_request(
            host,
            port,
            "POST",
            f"/api/research/{research.research_id}/decision/make-active",
            {"token": server.operator_control_token, "idempotency_key": "dashboard-promote-blocked"},
            expected=HTTPStatus.CONFLICT,
        )

        assert demo.status.value == "RUNNING"
        assert result["blocked"] is True
        assert result["research"]["decision"] == "MAKE_ACTIVE_BLOCKED"
        assert result["research"]["made_active_at"] is None
        assert result["research"]["promotion_result_metadata"] == {}
    finally:
        _stop(server, thread)


def test_research_dashboard_removes_fixture_rows_without_logs_page(tmp_path):
    db, _rules = _research_db(tmp_path)
    html = render_dashboard(DashboardReadModel(db), initial_page="research")
    research_section = html[html.index('id="page-research"') : html.index('id="page-research-detail"', html.index('id="page-research"'))]

    assert "No Research records." in html
    assert "R-001" not in research_section
    assert "BT-012" not in html
    assert "DM-006" not in html
    assert 'data-page="logs"' not in html
    assert "openNewResearch" in html
    assert 'id="new-research-modal"' in html
    assert 'id="new-set"' in html
    assert 'id="new-rules"' in html
    assert "function setupNewResearch()" in html
    assert "window.createResearch = async function()" in html
    assert 'postJson("/api/research", {set_id, set_version, rules_version_id, idempotency_key:commandIdempotencyKey("research-create")})' in html
    assert 'credentials:"same-origin"' in html
    assert 'commandHeaders("application/json")' in html
    assert 'token,set_id,set_version' not in html
    assert '"set_id": "triggertrade-futures-core"' in html
    assert _rules.get_current_rules_version().rules_version_id in html
    assert "Set 2 · v5" not in html
    assert "Rules · v4" not in html
    assert "location.reload" not in html
    assert "/api/research/${encodeURIComponent(currentResearchId)}/backtests" in html
    assert "/api/research/${encodeURIComponent(currentResearchId)}/demo/start" in html
    assert "research_start" in html


def test_research_dashboard_uses_postgres_registry_for_set_and_rules_choices(tmp_path):
    db, rules = _research_db(tmp_path)
    current = rules.get_current_rules_version()
    registry = _FakeResearchConfigRegistry(
        trigger_set=TriggerSetVersion(
            set_id="pg-canonical-set",
            version="v42",
            purpose="Research candidate",
            status=TriggerSetStatus.TESTING,
            symbol="BTCUSDT",
            timeframe="1m",
            rule_versions=(("TRG-001", "0.1.0"),),
            strategy_version="strategy-v1",
            risk_profile_version="risk-v1",
            config_snapshot={},
            created_at="2026-09-25T00:00:00+00:00",
            provenance="unit",
        ),
        rules=current,
    )

    html = render_dashboard(
        DashboardReadModel(tmp_path / "empty-local-read-model.sqlite3"),
        initial_page="research",
        research_config_registry=registry,
    )

    assert '"set_id": "pg-canonical-set"' in html
    assert '"version": "v42"' in html
    assert current.rules_version_id in html
    assert "triggertrade-futures-core" not in html


def test_research_api_uses_postgres_registry_for_list_and_detail(tmp_path):
    db, rules = _research_db(tmp_path)
    current = rules.get_current_rules_version()
    record = _research_record(
        research_id="research-pg-001",
        set_id="pg-canonical-set",
        set_version="v42",
        rules_version_id=current.rules_version_id,
        rules_display_version=current.version,
    )
    registry = _FakeResearchConfigRegistry(
        trigger_set=TriggerSetVersion(
            set_id="pg-canonical-set",
            version="v42",
            purpose="Research candidate",
            status=TriggerSetStatus.TESTING,
            symbol="BTCUSDT",
            timeframe="1m",
            rule_versions=(("TRG-001", "0.1.0"),),
            strategy_version="strategy-v1",
            risk_profile_version="risk-v1",
            config_snapshot={},
            created_at="2026-09-25T00:00:00+00:00",
            provenance="unit",
        ),
        rules=current,
        research=(record,),
    )
    server = create_server(port=0, db_path=db, research_config_registry=registry)
    host, port = server.server_address
    thread = _start(server)
    try:
        listed = _json_request(host, port, "GET", "/api/research")["research"]
        detail = _json_request(host, port, "GET", "/api/research/research-pg-001")

        assert listed[0]["research_id"] == "research-pg-001"
        assert listed[0]["set_id"] == "pg-canonical-set"
        assert detail["research"]["set_id"] == "pg-canonical-set"
        assert detail["backtests"] == []
        assert detail["demos"] == []
    finally:
        _stop(server, thread)


def test_research_registry_unavailable_returns_503_not_empty_success(tmp_path):
    db, _rules = _research_db(tmp_path)
    server = create_server(port=0, db_path=db, research_config_registry=_FailingResearchConfigRegistry())
    host, port = server.server_address
    thread = _start(server)
    try:
        research = _json_request(host, port, "GET", "/api/research", expected=HTTPStatus.SERVICE_UNAVAILABLE)
        rules = _json_request(host, port, "GET", "/api/rules/current", expected=HTTPStatus.SERVICE_UNAVAILABLE)

        assert "registry unavailable" in research["error"].lower()
        assert "registry unavailable" in rules["error"].lower()
    finally:
        _stop(server, thread)


def test_research_registry_unavailable_renders_unavailable_state_not_empty_success(tmp_path):
    db, _rules = _research_db(tmp_path)
    html = render_dashboard(
        DashboardReadModel(db),
        initial_page="research",
        research_config_registry=_FailingResearchConfigRegistry(),
    )

    assert "Research registry unavailable:" in html
    assert "PostgreSQL Research configuration registry unavailable" in html
    assert "researchRegistryUnavailable()" in html
    assert "node.disabled = commandUnavailable" in html


def _managed_json_request(host, port, method, path, payload=None, *, expected=HTTPStatus.OK):
    conn = HTTPConnection(host, port, timeout=3)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        **_managed_principal_headers("operator-1"),
    }
    conn.request(method, path, body=body, headers=headers)
    response = conn.getresponse()
    data = response.read().decode("utf-8")
    assert response.status == expected
    return json.loads(data)


class _FakeResearchConfigRegistry:
    def __init__(self, *, trigger_set, rules, research=()):
        self._trigger_set = trigger_set
        self._rules = rules
        self._research = tuple(research)

    def list_trigger_set_versions(self):
        return (self._trigger_set,)

    def list_trading_rules_versions(self):
        return (self._rules,)

    def list_research(self):
        return self._research

    def get_research(self, research_id):
        for record in self._research:
            if record.research_id == research_id:
                return record
        return None


class _FailingResearchConfigRegistry:
    def list_trigger_set_versions(self):
        raise RuntimeError("registry offline")

    def list_trading_rules_versions(self):
        raise RuntimeError("registry offline")

    def list_research(self):
        raise RuntimeError("registry offline")

    def get_research(self, research_id):
        raise RuntimeError("registry offline")


def _research_record(*, research_id, set_id, set_version, rules_version_id, rules_display_version):
    return ResearchRecord(
        research_id=research_id,
        created_at="2026-09-25T00:00:00+00:00",
        updated_at="2026-09-25T00:00:00+00:00",
        status=ResearchStatus.DRAFT,
        set_id=set_id,
        set_version=set_version,
        rules_version_id=rules_version_id,
        rules_display_version=rules_display_version,
        selected_backtest_run_id=None,
        selected_demo_run_id=None,
        decision=ResearchDecision.NONE,
        decision_at=None,
        archived_at=None,
        made_active_at=None,
        promoted_set_id=None,
        promoted_set_version=None,
        promoted_rules_version_id=None,
        previous_active_set_id=None,
        previous_active_set_version=None,
        previous_rules_version_id=None,
        promotion_result_metadata={},
        created_source="unit",
        schema_version="research.v1",
        pin_payload={
            "set_id": set_id,
            "set_version": set_version,
            "rules_version_id": rules_version_id,
        },
        pin_digest="unit-digest",
    )
