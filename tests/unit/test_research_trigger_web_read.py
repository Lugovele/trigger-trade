from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from dataclasses import replace
import json
import re
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from triggertrade.dashboard.__main__ import create_server, render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.dashboard.research_triggers import research_trigger_payload
from triggertrade.dashboard.research_sets import research_sets_payload
from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType
from triggertrade.persistence import ResearchSetVersion, research_set_from_package_record


def test_research_trigger_projection_exposes_31_imported_style_records():
    payload = research_trigger_payload(_research_v1_rules())
    triggers = payload["triggers"]

    assert payload["count"] == 31
    assert len(triggers) == 31
    btc = _by_id(triggers, "TR-R-BTC-008")
    assert btc["metric_refs"] == ("TOD_REL_TURNOVER",)
    assert btc["formula_refs"] == ("F-004",)
    assert btc["formula"] == "F-004"
    assert btc["condition"] == "TOD_REL_TURNOVER >= 0.70"
    assert "UNAVAILABLE" in btc["output"]
    assert "BTC" in btc["applicability"]
    assert btc["implementation_key"] == "triggertrade.research.DeclarativeMetricPredicateTrigger"
    assert btc["raw_definition"]["threshold"] == "0.70"


def test_research_trigger_projection_preserves_metric_and_config_semantics():
    triggers = research_trigger_payload(_research_v1_rules())["triggers"]

    simple = _by_id(triggers, "TR-R-BTC-006")
    directional = _by_id(triggers, "TR-R-004")
    fresh_directional = _by_id(triggers, "TR-R-015")
    theta_half = _by_id(triggers, "TR-R-001")
    theta_full = _by_id(triggers, "TR-R-002")
    false_half = _by_id(triggers, "TR-R-029")
    false_full = _by_id(triggers, "TR-R-030")
    zero = _by_id(triggers, "TR-R-BTC-001")
    fresh_btc = _by_id(triggers, "TR-R-BTC-003")
    btc_short = _by_id(triggers, "TR-R-BTC-002")
    unavailable = _by_id(triggers, "TR-R-001")
    contextual = _by_id(triggers, "TR-R-003")

    assert simple["condition"] == "ATR percentile >= 15"
    assert simple["metric"] == "ATR percentile"
    assert simple["formula"] == "F-004"
    assert directional["condition"] == "classifier_direction = LONG"
    assert "LONG" in directional["applicability"]
    assert "CURRENT_STATE" in directional["evaluation_semantics"]
    assert "FRESH_EVENT" in fresh_directional["evaluation_semantics"]
    assert _parameter_value(theta_half, "theta_move_pct") == "0.50"
    assert _parameter_value(theta_full, "theta_move_pct") == "1.00"
    assert _parameter_value(false_half, "theta_move_pct") == "0.50"
    assert _parameter_value(false_full, "theta_move_pct") == "1.00"
    assert zero["version"] == "1.0.1"
    assert zero["output"] == "LONG, ZERO, UNAVAILABLE"
    assert "CURRENT_STATE" in zero["evaluation_semantics"]
    assert "FRESH_EVENT" in fresh_btc["evaluation_semantics"]
    assert btc_short["version"] == "1.0.1"
    assert btc_short["output"] == "SHORT, ZERO, UNAVAILABLE"
    assert "ZERO" in zero["zero_none_unavailable"]
    assert "UNAVAILABLE" in unavailable["unavailable_reason"]
    assert "NONE" in contextual["zero_none_unavailable"]
    assert contextual["raw_definition"]["params"]["parameter_mutability"] == "NONE"


def test_research_trigger_projection_classifies_versions_generically():
    rules = _research_v1_rules()
    current = next(rule for rule in rules if rule.rule_id == "TR-R-BTC-001")
    historical = replace(current, version="1.0.0")

    triggers = research_trigger_payload((*rules, historical))["triggers"]
    current_row = next(row for row in triggers if row["trigger_id"] == "TR-R-BTC-001" and row["version"] == "1.0.1")
    historical_row = next(row for row in triggers if row["trigger_id"] == "TR-R-BTC-001" and row["version"] == "1.0.0")

    assert [row["version"] for row in triggers if row["trigger_id"] == "TR-R-BTC-001"] == ["1.0.1", "1.0.0"]
    assert current_row["version_state"] == "CURRENT"
    assert historical_row["version_state"] == "HISTORICAL"
    assert current_row["output"] == "LONG, ZERO, UNAVAILABLE"
    assert {row["version"]: row["version_state"] for row in current_row["version_history"]} == {
        "1.0.1": "CURRENT",
        "1.0.0": "HISTORICAL",
    }


def test_research_set_projection_exposes_33_records_and_exact_btc_memberships():
    triggers = research_trigger_payload(_research_v1_rules())["triggers"]
    payload = research_sets_payload(_research_v1_sets(), trigger_lookup={(row["trigger_id"], row["version"]): row for row in triggers})
    sets = payload["sets"]
    affected = {
        "SET-R-BTC-001-V1",
        "SET-R-BTC-001-V2",
        "SET-R-BTC-003-V2",
        "SET-R-BTC-007-V2",
        "SET-R-BTC-008-V2",
        "SET-R-BTC-009-V2",
        "SET-R-BTC-011-V2",
        "SET-R-BTC-012-V2",
        "SET-R-BTC-015-V2",
        "SET-R-BTC-016-V2",
        "SET-R-BTC-019-V1",
        "SET-R-BTC-019-V2",
        "SET-R-BTC-020-V1",
        "SET-R-BTC-020-V2",
        "SET-R-BTC-021-V1",
        "SET-R-BTC-021-V2",
    }

    assert payload["count"] == 33
    assert len(sets) == 33
    btc_sets = [row for row in sets if row["version"] in affected]
    assert len(btc_sets) == 16
    assert all(
        member["version"] != "1.0.0"
        for row in btc_sets
        for member in row["trigger_members"]
        if member["trigger_id"] in {"TR-R-BTC-001", "TR-R-BTC-002", "TR-R-BTC-003", "TR-R-BTC-004"}
    )
    assert all(
        member["version"] == "1.0.1"
        for row in btc_sets
        for member in row["trigger_members"]
        if member["trigger_id"] in {"TR-R-BTC-001", "TR-R-BTC-002", "TR-R-BTC-003", "TR-R-BTC-004"}
    )
    first = next(row for row in sets if row["version"] == "SET-R-001-V2")
    assert [member["position"] for member in first["trigger_members"]] == list(range(1, first["trigger_count"] + 1))
    assert first["version_state"] == "CURRENT"
    assert first["direction"] == "CLASSIFIER SIDE"
    assert "classifier side" in first["direction_semantics"]


def test_research_trigger_api_is_read_only_and_returns_list_and_detail():
    registry = _FakeTriggerRegistry(_research_v1_rules())
    set_registry = _FakeResearchSetRegistry(_research_v1_sets())
    server = create_server(port=0, db_path=_tmp_db_path(), trigger_registry=registry, research_set_registry=set_registry)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        payload = _json_request(host, port, "GET", "/api/research/triggers")
        detail = _json_request(host, port, "GET", "/api/research/triggers/TR-R-BTC-006/1.0.0")
        missing = _json_request(
            host,
            port,
            "GET",
            "/api/research/triggers/TR-R-MISSING/1.0.0",
            expected=HTTPStatus.NOT_FOUND,
        )
        set_list = _json_request(host, port, "GET", "/api/research/sets")
        set_detail = _json_request(host, port, "GET", "/api/research/sets/SET-R-BTC-001/SET-R-BTC-001-V1")
        mutation = _json_request(
            host,
            port,
            "POST",
            "/api/research/triggers",
            data=b"{}",
            expected=HTTPStatus.FORBIDDEN,
        )
        set_mutation = _json_request(
            host,
            port,
            "POST",
            "/api/research/sets",
            data=b"{}",
            expected=HTTPStatus.FORBIDDEN,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert payload["count"] == 31
    assert len(payload["triggers"]) == 31
    assert detail["trigger"]["condition"] == "ATR percentile >= 15"
    assert detail["trigger"]["metric_refs"] == ["ATR percentile"]
    assert detail["trigger"]["formula_refs"] == ["F-004"]
    assert detail["trigger"]["raw_definition"]["threshold"] == "15"
    assert set_list["count"] == 33
    assert len(set_detail["set"]["trigger_members"]) == set_detail["set"]["trigger_count"]
    assert set_detail["set"]["trigger_members"][0]["trigger_id"].startswith("TR-R-")
    assert missing["error"] == "research trigger not found"
    assert mutation["error"] == "operator token required"
    assert set_mutation["error"] == "operator token required"


def test_dashboard_renders_research_trigger_list_and_detail_without_mutation_controls():
    registry = _FakeTriggerRegistry(_research_v1_rules())
    html = render_dashboard(
        DashboardReadModel(_tmp_db_path()),
        initial_page="trigger-catalog",
        selected_trigger_id="TR-R-BTC-006",
        selected_trigger_version="1.0.0",
        trigger_registry=registry,
    )

    assert '"trigger_id": "TR-R-BTC-006"' in html
    assert '"condition": "ATR percentile >= 15"' in html
    assert '"metric_refs": ["ATR percentile"]' in html
    assert '"formula_refs": ["F-004"]' in html
    assert "<th>Metric</th><th>Formula</th><th>Condition</th><th>Parameters</th><th>Evaluation</th><th>Output</th><th>Applicability</th><th>Status</th><th>Version State</th>" in html
    assert '"name": "theta_move_pct"' in html
    assert '"value": "0.50"' in html
    assert '"value": "1.00"' in html
    assert "CURRENT_STATE" in html
    assert "FRESH_EVENT" in html
    assert '"raw_definition": {' in html
    assert "/api/research/triggers" not in html
    assert "postJson(\"/api/research/triggers" not in html
    assert "deleteTrigger" not in html
    assert "saveTrigger" not in html


def test_trading_configuration_owns_metrics_triggers_sets_and_rules_journeys():
    registry = _FakeTriggerRegistry(_research_v1_rules())
    set_registry = _FakeResearchSetRegistry(_research_v1_sets())
    html = render_dashboard(
        DashboardReadModel(_tmp_db_path()),
        initial_page="config",
        trigger_registry=registry,
        research_set_registry=set_registry,
    )

    assert re.search(r'<div class="group-label">\s*Signal Logic\s*</div>', html)
    assert re.search(r'data-config="metrics"[\s\S]*?>\s*Metrics\s*</button>', html)
    assert re.search(r'data-config="triggers"[\s\S]*?>\s*Triggers\s*</button>', html)
    assert re.search(r'data-config="sets"[\s\S]*?>\s*Sets\s*</button>', html)
    assert re.search(r'<div class="group-label">\s*Trading\s*</div>', html)
    assert 'data-config="rules"' in html
    assert 'id="config-triggers"' in html
    assert 'id="config-sets"' in html
    assert 'id="config-rules"' in html
    assert "Position Rules" in html
    assert "Portfolio Rules" in html
    assert "Coins" in html
    assert "Save New Rules" in html or "Save as New Version" in html
    assert "History" in html
    assert "Back to Triggers" in html
    assert "Back to Sets" in html
    assert "Back to Trading Rules" in html
    assert 'data-research-view="triggers"' not in html
    assert 'data-research-view="sets"' not in html
    assert 'data-research-view="rules"' not in html
    assert 'id="research-triggers"' not in html
    assert 'id="research-sets"' not in html
    assert 'id="research-rules"' not in html
    assert '"trigger_id": "TR-R-BTC-001"' in html
    assert '"set_id": "SET-R-BTC-001"' in html
    assert '"version": "SET-R-BTC-001-V1"' in html
    assert "TRV-R-POS-" not in html
    assert "TRV-R-PORT-" not in html


def test_research_rules_route_is_not_a_configuration_destination():
    registry = _FakeTriggerRegistry(_research_v1_rules())
    set_registry = _FakeResearchSetRegistry(_research_v1_sets())
    server = create_server(port=0, db_path=_tmp_db_path(), trigger_registry=registry, research_set_registry=set_registry)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        payload = _text_request(host, port, "GET", "/research/rules")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert 'data-research-view="rules"' not in payload
    assert 'id="research-rules"' not in payload
    assert "Research Rules import is pending" not in payload


def _by_id(rows, trigger_id: str) -> dict[str, object]:
    return next(row for row in rows if row["trigger_id"] == trigger_id)


def _parameter_value(row: dict[str, object], name: str) -> str | None:
    for parameter in row["parameters"]:
        if parameter["name"] == name:
            return parameter["value"]
    return None


def _tmp_db_path() -> Path:
    path = Path(".tt-tmp") / f"research-trigger-web-{uuid4().hex}" / "dashboard.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _json_request(host, port, method: str, path: str, *, data: bytes | None = None, expected=HTTPStatus.OK):
    request = Request(f"http://{host}:{port}{path}", method=method, data=data)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
            assert response.status == expected
            return json.loads(body) if body.startswith("{") else body
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        assert exc.code == expected
        return json.loads(body) if body.startswith("{") else body


def _text_request(host, port, method: str, path: str, *, expected=HTTPStatus.OK) -> str:
    request = Request(f"http://{host}:{port}{path}", method=method)
    try:
        with urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
            assert response.status == expected
            return body
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        assert exc.code == expected
        return body


def _research_v1_rules() -> tuple[RuleDefinition, ...]:
    package = json.loads(Path("docs/research-import/triggers/RESEARCH_V1_TRIGGERS_WEB_IMPORT.json").read_text(encoding="utf-8"))
    rules: list[RuleDefinition] = []
    for record in package["records"]:
        data = dict(record["rule_definition"])
        data["status"] = RuleStatus(data["status"])
        data["rule_type"] = RuleType(data["rule_type"])
        data.pop("semantic_hash", None)
        rules.append(RuleDefinition(**data))
    return tuple(rules)


def _research_v1_sets() -> tuple[ResearchSetVersion, ...]:
    package = json.loads(Path("docs/research-import/sets/RESEARCH_V1_SETS.json").read_text(encoding="utf-8"))
    return tuple(research_set_from_package_record(record) for record in package["sets"])


class _FakeTriggerRegistry:
    def __init__(self, rules: tuple[RuleDefinition, ...]) -> None:
        self._rules = {(rule.rule_id, rule.version): rule for rule in rules}

    def list_trigger_versions(self):
        return tuple(self._rules.values())

    def get_rule(self, rule_id: str, version: str | None = None):
        if version is not None:
            return self._rules.get((rule_id, version))
        candidates = [rule for (candidate_id, _), rule in self._rules.items() if candidate_id == rule_id]
        return sorted(candidates, key=lambda rule: tuple(int(part) for part in rule.version.split(".") if part.isdigit()), reverse=True)[0] if candidates else None


class _FakeResearchSetRegistry:
    def __init__(self, records: tuple[ResearchSetVersion, ...]) -> None:
        self._records = {(record.set_id, record.set_version): record for record in records}

    def list_research_sets(self):
        return tuple(self._records.values())

    def get_research_set(self, set_id: str, version: str):
        return self._records.get((set_id, version))
