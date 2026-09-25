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
    ResearchBacktestRunRecord,
    ResearchBacktestStatus,
    ResearchDecision,
    ResearchDemoRunRecord,
    ResearchDemoStatus,
    ResearchRecord,
    ResearchStatus,
    ResearchStore,
    ResearchStoreError,
)
from triggertrade.services.operator_auth import OperatorCommandAuthorizer
from triggertrade.services.research import ResearchDemoExecutionHandoffResult
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
    authorizer = OperatorCommandAuthorizer(db, auth_mode="managed_oidc", allowed_principals=("azure-object-id",))
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
            principal_id="azure-object-id",
            encoded_claim_id="mapped-claim-object-id",
        )["research"]
        demo = _managed_json_request(
            host,
            port,
            "POST",
            f"/api/research/{created['research_id']}/demo/start",
            {"idempotency_key": "research-demo-managed"},
            expected=HTTPStatus.CONFLICT,
            principal_id="azure-object-id",
            encoded_claim_id="mapped-claim-object-id",
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
            set_id="triggertrade-futures-core",
            version="v1",
            purpose="Current futures set",
            status=TriggerSetStatus.ACTIVE,
            symbol="BTCUSDT",
            timeframe="1m",
            rule_versions=(("TRG-001", "0.2.0"),),
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

    assert '"set_id": "triggertrade-futures-core"' in html
    assert '"version": "v1"' in html
    assert current.rules_version_id in html
    assert "triggertrade-futures-candidate" not in html


def test_research_api_uses_postgres_registry_for_list_and_detail(tmp_path):
    db, rules = _research_db(tmp_path)
    current = rules.get_current_rules_version()
    store = ResearchStore(db)
    stored, _created = store.create_research(
        set_id="pg-canonical-set",
        set_version="v42",
        rules_version_id=current.rules_version_id,
        rules_display_version=current.version,
        created_source="unit",
    )
    backtest = store.add_backtest_run(
        research_id=stored.research_id,
        period_start="2026-09-18T00:00:00+00:00",
        period_end="2026-09-25T00:00:00+00:00",
        timeframe="7D",
        status=ResearchBacktestStatus.FAILED,
        metrics={"closed_trades": 0},
        unavailable_reason="historical replay input unavailable",
    )
    demo = store.add_demo_run(
        research_id=stored.research_id,
        status=ResearchDemoStatus.RUNNING,
        started_at="2026-09-25T00:00:00+00:00",
        execution_scope_id="demo-scope-001",
        account_scope="bybit-demo",
        metrics={"closed_trades": 0},
    )
    record = _research_record(
        research_id=stored.research_id,
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
    run_store = _FakeResearchRunStore(research=(record,), backtests=(backtest,), demos=(demo,))
    server = create_server(port=0, db_path=db, research_config_registry=registry, research_run_store=run_store)
    host, port = server.server_address
    thread = _start(server)
    try:
        listed = _json_request(host, port, "GET", "/api/research")["research"]
        detail = _json_request(host, port, "GET", f"/api/research/{stored.research_id}")

        assert listed[0]["research_id"] == stored.research_id
        assert listed[0]["set_id"] == "pg-canonical-set"
        assert detail["research"]["set_id"] == "pg-canonical-set"
        assert detail["research"]["set_version"] == "v42"
        assert detail["run_projection"] == {"available": True}
        assert detail["backtests"][0]["run_id"] == backtest.run_id
        assert detail["backtests"][0]["status"] == "FAILED"
        assert detail["backtests"][0]["unavailable_reason"] == "historical replay input unavailable"
        assert detail["demos"][0]["run_id"] == demo.run_id
        assert detail["demos"][0]["status"] == "RUNNING"
        assert detail["demos"][0]["execution_scope_id"] == "demo-scope-001"
    finally:
        _stop(server, thread)


def test_postgres_registry_research_without_sqlite_mirror_can_start_backtest_and_detail(tmp_path):
    db, rules = _research_db(tmp_path)
    current = rules.get_current_rules_version()
    record = _research_record(
        research_id="res-pg-only-001",
        set_id="pg-canonical-set",
        set_version="v42",
        rules_version_id=current.rules_version_id,
        rules_display_version=current.version,
    )
    registry = _FakeResearchConfigRegistry(
        trigger_set=_trigger_set("pg-canonical-set", "v42"),
        rules=current,
        research=(record,),
    )
    run_store = _FakeResearchRunStore(research=(record,))
    server = create_server(
        port=0,
        db_path=db,
        operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"),
        research_config_registry=registry,
        research_run_store=run_store,
    )
    host, port = server.server_address
    thread = _start(server)
    try:
        result = _json_request(
            host,
            port,
            "POST",
            f"/api/research/{record.research_id}/backtests",
            {
                "token": server.operator_control_token,
                "research_start": "2026-09-18T00:00:00+00:00",
                "research_end": "2026-09-25T00:00:00+00:00",
                "timeframe": "1m",
                "idempotency_key": "research-backtest-pg-only-001",
            },
            expected=HTTPStatus.CREATED,
        )
        detail = _json_request(host, port, "GET", f"/api/research/{record.research_id}")

        assert result["backtest"]["research_id"] == record.research_id
        assert result["backtest"]["status"] == "FAILED"
        assert detail["run_projection"] == {"available": True}
        assert detail["backtests"][0]["run_id"] == result["backtest"]["run_id"]
        assert detail["backtests"][0]["unavailable_reason"] == "backend_historical_replay_inputs_unavailable"
    finally:
        _stop(server, thread)


def test_postgres_registry_research_without_sqlite_mirror_can_start_demo_and_detail(tmp_path):
    db, rules = _research_db(tmp_path)
    current = rules.get_current_rules_version()
    record = _research_record(
        research_id="res-pg-only-demo",
        set_id="pg-canonical-set",
        set_version="v42",
        rules_version_id=current.rules_version_id,
        rules_display_version=current.version,
    )
    registry = _FakeResearchConfigRegistry(
        trigger_set=_trigger_set("pg-canonical-set", "v42"),
        rules=current,
        research=(record,),
    )
    run_store = _FakeResearchRunStore(research=(record,))
    handoff = _FakeDemoHandoff()
    server = create_server(
        port=0,
        db_path=db,
        operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"),
        research_config_registry=registry,
        research_run_store=run_store,
        research_demo_handoff=handoff,
    )
    host, port = server.server_address
    thread = _start(server)
    try:
        result = _json_request(
            host,
            port,
            "POST",
            f"/api/research/{record.research_id}/demo/start",
            {"token": server.operator_control_token, "idempotency_key": "research-demo-pg-only-001"},
            expected=HTTPStatus.CREATED,
        )
        detail = _json_request(host, port, "GET", f"/api/research/{record.research_id}")

        assert result["demo"]["research_id"] == record.research_id
        assert result["demo"]["status"] == "RUNNING"
        assert handoff.requests[0]["research_id"] == record.research_id
        assert detail["run_projection"] == {"available": True}
        assert detail["demos"][0]["run_id"] == result["demo"]["run_id"]
        assert detail["demos"][0]["status"] == "RUNNING"
    finally:
        _stop(server, thread)


def test_demo_start_reuses_existing_running_postgres_run_without_duplicate_handoff(tmp_path):
    db, rules = _research_db(tmp_path)
    current = rules.get_current_rules_version()
    record = _research_record(
        research_id="res-pg-demo-retry",
        set_id="pg-canonical-set",
        set_version="v42",
        rules_version_id=current.rules_version_id,
        rules_display_version=current.version,
    )
    existing = ResearchDemoRunRecord(
        research_id=record.research_id,
        run_id="rdm-existing-running",
        created_at="2026-09-25T00:00:00+00:00",
        updated_at="2026-09-25T00:00:00+00:00",
        status=ResearchDemoStatus.RUNNING,
        started_at="2026-09-25T00:00:00+00:00",
        stopped_at=None,
        execution_scope_id="research-demo-worker",
        account_scope="research-demo-account",
        selected_for_use=False,
        metrics={},
        blocked_reason=None,
        pin_payload={},
        pin_digest="unit-existing-demo",
    )
    registry = _FakeResearchConfigRegistry(
        trigger_set=_trigger_set("pg-canonical-set", "v42"),
        rules=current,
        research=(record,),
    )
    run_store = _FakeResearchRunStore(research=(record,), demos=(existing,))
    handoff = _FakeDemoHandoff()
    server = create_server(
        port=0,
        db_path=db,
        operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"),
        research_config_registry=registry,
        research_run_store=run_store,
        research_demo_handoff=handoff,
    )
    host, port = server.server_address
    thread = _start(server)
    try:
        result = _json_request(
            host,
            port,
            "POST",
            f"/api/research/{record.research_id}/demo/start",
            {"token": server.operator_control_token, "idempotency_key": "research-demo-retry-001"},
            expected=HTTPStatus.CREATED,
        )

        assert result["demo"]["run_id"] == existing.run_id
        assert handoff.requests == []
    finally:
        _stop(server, thread)


def test_postgres_research_runs_survive_service_reconstruction_and_replica_visibility(tmp_path):
    db, rules = _research_db(tmp_path)
    current = rules.get_current_rules_version()
    record = _research_record(
        research_id="res-shared-run-store",
        set_id="pg-canonical-set",
        set_version="v42",
        rules_version_id=current.rules_version_id,
        rules_display_version=current.version,
    )
    registry = _FakeResearchConfigRegistry(
        trigger_set=_trigger_set("pg-canonical-set", "v42"),
        rules=current,
        research=(record,),
    )
    shared_state = _SharedResearchRunState(research=(record,))
    first_replica = _FakeResearchRunStore(state=shared_state)
    second_replica = _FakeResearchRunStore(state=shared_state)
    server_a = create_server(
        port=0,
        db_path=db,
        operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"),
        research_config_registry=registry,
        research_run_store=first_replica,
    )
    host, port = server_a.server_address
    thread = _start(server_a)
    try:
        created = _json_request(
            host,
            port,
            "POST",
            f"/api/research/{record.research_id}/backtests",
            {
                "token": server_a.operator_control_token,
                "research_start": "2026-08-26T00:00:00+00:00",
                "research_end": "2026-09-25T00:00:00+00:00",
                "timeframe": "1m",
                "idempotency_key": "research-backtest-replica-001",
            },
            expected=HTTPStatus.CREATED,
        )
    finally:
        _stop(server_a, thread)

    server_b = create_server(
        port=0,
        db_path=tmp_path / "replica-b-local.sqlite3",
        research_config_registry=registry,
        research_run_store=second_replica,
    )
    detail = dashboard_main._research_detail_payload(server_b, record.research_id)
    server_b.server_close()

    assert detail is not None
    assert detail["run_projection"] == {"available": True}
    assert detail["backtests"][0]["run_id"] == created["backtest"]["run_id"]


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


def _managed_json_request(
    host,
    port,
    method,
    path,
    payload=None,
    *,
    expected=HTTPStatus.OK,
    principal_id="operator-1",
    encoded_claim_id=None,
):
    conn = HTTPConnection(host, port, timeout=3)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        **_managed_principal_headers(
            principal_id,
            encoded_claims=[
                {"typ": "oid", "val": encoded_claim_id or principal_id},
                {"typ": "roles", "val": "TriggerTrade.Operator"},
            ],
        ),
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

    def get_trigger_set_version(self, set_id, version):
        if self._trigger_set.set_id == set_id and self._trigger_set.version == version:
            return self._trigger_set
        return None

    def list_trading_rules_versions(self):
        return (self._rules,)

    def list_research(self):
        return self._research

    def get_research(self, research_id):
        for record in self._research:
            if record.research_id == research_id:
                return record
        return None

    def put_configuration(self, *, research, trigger_set, rules):
        if self.get_research(research.research_id) is None:
            self._research = (*self._research, research)

    def get_trading_rules_version(self, rules_version_id):
        return self._rules if self._rules.rules_version_id == rules_version_id else None


class _SharedResearchRunState:
    def __init__(self, *, research=(), backtests=(), demos=()):
        self.research = {record.research_id: record for record in research}
        self.backtests = {}
        self.demos = {}
        for record in backtests:
            self.backtests.setdefault(record.research_id, []).append(record)
        for record in demos:
            self.demos.setdefault(record.research_id, []).append(record)


class _FakeResearchRunStore:
    path = None

    def __init__(self, *, state=None, research=(), backtests=(), demos=()):
        self._state = state or _SharedResearchRunState(research=research, backtests=backtests, demos=demos)

    def get_research(self, research_id):
        return self._state.research.get(research_id)

    def list_backtest_runs(self, research_id):
        return tuple(self._state.backtests.get(research_id, ()))

    def list_demo_runs(self, research_id):
        return tuple(self._state.demos.get(research_id, ()))

    def add_backtest_run(
        self,
        *,
        research_id,
        period_start,
        period_end,
        timeframe,
        status,
        engine_run_id=None,
        metrics=None,
        unavailable_reason=None,
        pin_payload=None,
        created_at=None,
    ):
        if research_id not in self._state.research:
            raise ResearchStoreError("research id not found")
        created_at = created_at or "2026-09-25T00:00:00+00:00"
        run_id = f"rbt-unit-{len(self._state.backtests.get(research_id, ())) + 1}"
        record = ResearchBacktestRunRecord(
            research_id=research_id,
            run_id=run_id,
            created_at=created_at,
            updated_at=created_at,
            status=status,
            period_start=period_start,
            period_end=period_end,
            timeframe=timeframe,
            engine_run_id=engine_run_id,
            selected_for_use=False,
            metrics=metrics or {},
            unavailable_reason=unavailable_reason,
            pin_payload=pin_payload or {},
            pin_digest="unit-run-digest",
        )
        self._state.backtests.setdefault(research_id, []).insert(0, record)
        research = self._state.research[research_id]
        self._state.research[research_id] = _record_with_status(
            research,
            ResearchStatus.FAILED if status is ResearchBacktestStatus.FAILED else ResearchStatus.BACKTEST_READY,
            updated_at=created_at,
        )
        return record

    def add_demo_run(
        self,
        *,
        research_id,
        status,
        run_id=None,
        started_at=None,
        stopped_at=None,
        execution_scope_id=None,
        account_scope=None,
        metrics=None,
        blocked_reason=None,
        pin_payload=None,
        created_at=None,
    ):
        if research_id not in self._state.research:
            raise ResearchStoreError("research id not found")
        created_at = created_at or "2026-09-25T00:00:00+00:00"
        run_id = run_id or f"rdm-unit-{len(self._state.demos.get(research_id, ())) + 1}"
        record = ResearchDemoRunRecord(
            research_id=research_id,
            run_id=run_id,
            created_at=created_at,
            updated_at=created_at,
            status=status,
            started_at=started_at,
            stopped_at=stopped_at,
            execution_scope_id=execution_scope_id,
            account_scope=account_scope,
            selected_for_use=False,
            metrics=metrics or {},
            blocked_reason=blocked_reason,
            pin_payload=pin_payload or {},
            pin_digest="unit-demo-digest",
        )
        self._state.demos.setdefault(research_id, []).insert(0, record)
        research = self._state.research[research_id]
        self._state.research[research_id] = _record_with_status(
            research,
            ResearchStatus.DEMO_RUNNING if status is ResearchDemoStatus.RUNNING else ResearchStatus.BLOCKED,
            updated_at=created_at,
        )
        return record


class _FakeDemoHandoff:
    canonical_worker_handoff = True

    def __init__(self):
        self.requests = []

    def start_research_demo(self, *, research, trigger_set, rules, isolation, started_at, pin_payload, demo_run_id):
        self.requests.append({"research_id": research.research_id, "demo_run_id": demo_run_id})
        return ResearchDemoExecutionHandoffResult(
            handoff_id=f"unit-handoff-{demo_run_id}",
            execution_owner="trading-worker",
            durable=True,
        )


def _record_with_status(record, status, *, updated_at):
    return ResearchRecord(
        research_id=record.research_id,
        created_at=record.created_at,
        updated_at=updated_at,
        status=status,
        set_id=record.set_id,
        set_version=record.set_version,
        rules_version_id=record.rules_version_id,
        rules_display_version=record.rules_display_version,
        selected_backtest_run_id=record.selected_backtest_run_id,
        selected_demo_run_id=record.selected_demo_run_id,
        decision=record.decision,
        decision_at=record.decision_at,
        archived_at=record.archived_at,
        made_active_at=record.made_active_at,
        promoted_set_id=record.promoted_set_id,
        promoted_set_version=record.promoted_set_version,
        promoted_rules_version_id=record.promoted_rules_version_id,
        previous_active_set_id=record.previous_active_set_id,
        previous_active_set_version=record.previous_active_set_version,
        previous_rules_version_id=record.previous_rules_version_id,
        promotion_result_metadata=record.promotion_result_metadata,
        created_source=record.created_source,
        schema_version=record.schema_version,
        pin_payload=record.pin_payload,
        pin_digest=record.pin_digest,
    )


def _trigger_set(set_id, version):
    return TriggerSetVersion(
        set_id=set_id,
        version=version,
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
    )


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
