from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from triggertrade.dashboard.__main__ import create_server, render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.dashboard.research_triggers import research_trigger_payload
from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType


def test_research_trigger_projection_exposes_31_imported_style_records():
    payload = research_trigger_payload(_research_v1_rules())
    triggers = payload["triggers"]

    assert payload["count"] == 31
    assert len(triggers) == 31
    btc = _by_id(triggers, "TR-R-BTC-008")
    assert btc["metric_refs"] == ("TOD_REL_TURNOVER", "F-004")
    assert btc["condition"] == "TOD_REL_TURNOVER >= 0.70"
    assert "UNAVAILABLE" in btc["output"]
    assert "BTC" in btc["applicability"]
    assert btc["implementation_key"] == "triggertrade.research.DeclarativeMetricPredicateTrigger"
    assert btc["raw_definition"]["threshold"] == "0.70"


def test_research_trigger_projection_preserves_metric_and_config_semantics():
    triggers = research_trigger_payload(_research_v1_rules())["triggers"]

    simple = _by_id(triggers, "TR-R-BTC-006")
    directional = _by_id(triggers, "TR-R-004")
    zero = _by_id(triggers, "TR-R-BTC-001")
    btc_short = _by_id(triggers, "TR-R-BTC-002")
    unavailable = _by_id(triggers, "TR-R-001")
    contextual = _by_id(triggers, "TR-R-003")

    assert simple["condition"] == "ATR percentile >= 15"
    assert directional["condition"] == "classifier_direction = LONG"
    assert "LONG" in directional["applicability"]
    assert zero["version"] == "1.0.1"
    assert zero["output"] == "LONG, ZERO, UNAVAILABLE"
    assert btc_short["version"] == "1.0.1"
    assert btc_short["output"] == "SHORT, ZERO, UNAVAILABLE"
    assert "ZERO" in zero["zero_none_unavailable"]
    assert "UNAVAILABLE" in unavailable["unavailable_reason"]
    assert "NONE" in contextual["zero_none_unavailable"]
    assert contextual["raw_definition"]["params"]["parameter_mutability"] == "NONE"


def test_research_trigger_api_is_read_only_and_returns_list_and_detail():
    registry = _FakeTriggerRegistry(_research_v1_rules())
    server = create_server(port=0, db_path=_tmp_db_path(), trigger_registry=registry)
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
        mutation = _json_request(
            host,
            port,
            "POST",
            "/api/research/triggers",
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
    assert detail["trigger"]["metric_refs"] == ["ATR percentile", "F-004"]
    assert detail["trigger"]["raw_definition"]["threshold"] == "15"
    assert missing["error"] == "research trigger not found"
    assert mutation["error"] == "operator token required"


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
    assert '"metric_refs": ["ATR percentile", "F-004"]' in html
    assert '"raw_definition": {' in html
    assert "<th>Metric(s)</th><th>Condition</th><th>Output</th><th>Applicability / Scope</th><th>Status</th>" in html
    assert "/api/research/triggers" not in html
    assert "postJson(\"/api/research/triggers" not in html
    assert "deleteTrigger" not in html
    assert "saveTrigger" not in html


def _by_id(rows, trigger_id: str) -> dict[str, object]:
    return next(row for row in rows if row["trigger_id"] == trigger_id)


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


class _FakeTriggerRegistry:
    def __init__(self, rules: tuple[RuleDefinition, ...]) -> None:
        self._rules = {(rule.rule_id, rule.version): rule for rule in rules}

    def list_trigger_versions(self):
        return tuple(self._rules.values())

    def get_rule(self, rule_id: str, version: str | None = None):
        if version is not None:
            return self._rules.get((rule_id, version))
        candidates = [rule for (candidate_id, _), rule in self._rules.items() if candidate_id == rule_id]
        return candidates[0] if candidates else None
