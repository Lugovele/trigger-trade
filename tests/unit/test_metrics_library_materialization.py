from __future__ import annotations

from http import HTTPStatus
from http.client import HTTPConnection
import json
from pathlib import Path
import subprocess
import threading
from uuid import uuid4

from triggertrade.dashboard.__main__ import create_server, render_dashboard
from triggertrade.dashboard.metrics_library import get_metric, metrics_payload
from triggertrade.dashboard.product_ui import render_product_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel


EXPECTED_IDS = (
    *(f"F-{index:03d}" for index in range(1, 17)),
    *(f"A-{index:03d}" for index in range(1, 10)),
    *(f"M-{index:03d}" for index in range(1, 9)),
    *(f"N-{index:03d}" for index in range(1, 9)),
    *(f"S-{index:03d}" for index in range(1, 7)),
)


def _start(server):
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread


def _stop(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def _json_request(host, port, method, path, *, expected=HTTPStatus.OK):
    conn = HTTPConnection(host, port, timeout=3)
    try:
        conn.request(method, path)
        response = conn.getresponse()
        data = response.read().decode("utf-8")
    finally:
        conn.close()
    assert response.status == expected
    return json.loads(data)


def _tmp_db_path() -> Path:
    path = Path(".tt-tmp") / f"metrics-{uuid4().hex}" / "dashboard.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def test_metrics_registry_exposes_exact_approved_population():
    payload = metrics_payload()
    metrics = payload["metrics"]
    ids = [metric["id"] for metric in metrics]

    assert ids == list(EXPECTED_IDS)
    assert len(metrics) == 47
    assert len(set(ids)) == 47
    assert sum(metric_id.startswith("F-") for metric_id in ids) == 16
    assert sum(metric_id.startswith("A-") for metric_id in ids) == 9
    assert sum(metric_id.startswith("M-") for metric_id in ids) == 8
    assert sum(metric_id.startswith("N-") for metric_id in ids) == 8
    assert sum(metric_id.startswith("S-") for metric_id in ids) == 6
    assert not any(metric_id.startswith("T-") for metric_id in ids)
    assert payload["semantic_source"] == "docs/METRICS_LIBRARY_V1.md"
    assert not any(
        f"\n# {family} - " in value
        for metric in metrics
        for value in metric.values()
        if isinstance(value, str)
        for family in ("F", "A", "M", "N", "S")
    )


def test_metrics_registry_preserves_targeted_semantic_boundaries():
    f002 = get_metric("F-002")
    assert f002 is not None
    assert f002["name"] == "1m Relative Participation Volume Confirmation"
    assert "current completed 1m base-coin volume" in f002["what_it_is"]
    assert "It is not 5m relative turnover" in f002["important_boundaries"]
    assert f002["formula_or_rule"] != "Relative Turnover = Current Turnover / Reference Turnover"

    assert all(get_metric(f"M-{index:03d}")["status"] == "RESEARCH_ONLY" for index in range(1, 9))

    s005 = get_metric("S-005")
    assert s005["status"] == "RESEARCH_ONLY"
    assert "research/demo diagnostic" in s005["what_it_is"].lower()
    assert "must not affect certified F-005 direction" in s005["important_boundaries"]
    assert "live trading decisions" in s005["important_boundaries"]

    s006 = get_metric("S-006")
    assert s006["type"] == "NOT_A_FORMULA"
    assert s006["status"] == "ARCHITECTURE_RULE"
    assert "architecture/runtime classification rule" in s006["what_it_means"]

    a007 = get_metric("A-007")
    a009 = get_metric("A-009")
    m004 = get_metric("M-004")
    assert "live account snapshot" in a007["what_it_is"]
    assert "accounting-day realized aggregation" in a009["important_boundaries"]
    assert "research max drawdown metric" in m004["what_it_is"]
    assert "M-004" in a007["important_boundaries"]
    assert "A-009" in m004["what_it_means"]

    f004 = get_metric("F-004")
    assert "does not itself select LONG/SHORT" in f004["important_boundaries"]
    assert "F-005" in f004["important_boundaries"]
    assert "DIRECTION_SCORE" in f004["output"]
    assert "no weight redistribution" in f004["unavailable_behavior"]


def test_metrics_registry_does_not_generate_synthetic_examples():
    payload = metrics_payload()
    missing_examples = [
        metric
        for metric in payload["metrics"]
        if metric["worked_example_status"] == "NO_CANONICAL_WORKED_EXAMPLE"
    ]

    assert missing_examples
    assert all(metric["worked_example"] == "No canonical worked example specified." for metric in missing_examples)


def test_metrics_api_is_read_only_and_returns_not_found_for_invalid_id():
    server = create_server(port=0, db_path=_tmp_db_path())
    host, port = server.server_address
    thread = _start(server)
    try:
        payload = _json_request(host, port, "GET", "/api/metrics")
        detail = _json_request(host, port, "GET", "/api/metrics/F-002")
        missing = _json_request(host, port, "GET", "/api/metrics/T-001", expected=HTTPStatus.NOT_FOUND)
    finally:
        _stop(server, thread)

    assert len(payload["metrics"]) == 47
    assert [metric["id"] for metric in payload["metrics"]] == list(EXPECTED_IDS)
    assert payload["counts"] == {"total": 47, "F": 16, "A": 9, "M": 8, "N": 8, "S": 6, "T": 0}
    assert detail["metric"]["id"] == "F-002"
    assert detail["metric"]["name"] == "1m Relative Participation Volume Confirmation"
    assert missing["error"] == "metric id not found"


def test_final_rendered_dashboard_contains_backend_backed_metrics_library():
    html = render_dashboard(DashboardReadModel(_tmp_db_path()), initial_page="config")

    assert 'id="config-metrics"' in html
    assert 'id="metrics-body"' in html
    assert 'id="metric-details"' in html
    assert 'id="metricFamilyFilters"' in html
    assert 'id="metricTimeframe"' not in html
    assert "<th>ID</th><th>Name</th><th>Family</th><th>Type</th><th>Status</th>" in html
    assert "metricDocs" not in html
    assert "metricRows=[" not in html
    assert '"name": "Relative Turnover"' not in html
    assert '"timeframe": "5m"' not in html

    for metric_id in EXPECTED_IDS:
        assert f'"id": "{metric_id}"' in html

    assert '"name": "1m Relative Participation Volume Confirmation"' in html
    assert "current completed 1m base-coin volume" in html
    assert "M-001" in html and '"status": "RESEARCH_ONLY"' in html
    assert "No canonical worked example specified." in html
    assert "function metricSection" in html
    assert "formula_or_rule" in html
    assert "calculateMetric" not in html
    assert "computeMetric" not in html
    assert "eval(" not in html
    assert "new Function" not in html


def test_final_rendered_metrics_ui_filters_and_search_are_interactive():
    html = render_dashboard(DashboardReadModel(_tmp_db_path()), initial_page="config")
    script_start = html.index('<script id="triggertrade-reference-backend-wiring">')
    script_start = html.index(">", script_start) + 1
    script_end = html.index("</script>", script_start)
    script = html[script_start:script_end]
    state_start = script.index("const state = ") + len("const state = ")
    state_end = script.index(";\n  const desktop", state_start)
    state = json.loads(script[state_start:state_end])
    metrics_start = script.index("  const metricsRegistry = state.metrics || {metrics: []};")
    metrics_end = script.index("  function renderTriggers()", metrics_start)
    metrics_script = script[metrics_start:metrics_end]

    harness = r"""
const fs = require("fs");
const payload = JSON.parse(fs.readFileSync(0, "utf8"));
const state = payload.state;
const window = {};

function assert(condition, message){
  if(!condition) throw new Error(message);
}
function h(value){
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;",
    "<":"&lt;",
    ">":"&gt;",
    '"':"&quot;",
    "'":"&#39;"
  })[c]);
}
function badge(value){ return `<span class="badge">${h(value)}</span>`; }

const nodesById = new Map();
let metricRowNodes = [];

class FakeElement {
  constructor({id="", dataset={}, className=""} = {}){
    this.id = id;
    this.dataset = {...dataset};
    this.value = "";
    this.listeners = {};
    this.children = [];
    this._innerHTML = "";
    this.classes = new Set(className ? className.split(/\s+/).filter(Boolean) : []);
    this.classList = {
      toggle: (name, force) => {
        const enabled = force === undefined ? !this.classes.has(name) : Boolean(force);
        if(enabled) this.classes.add(name);
        else this.classes.delete(name);
        return enabled;
      },
      contains: name => this.classes.has(name)
    };
    if(id) nodesById.set(id, this);
  }
  addEventListener(type, handler){
    if(!this.listeners[type]) this.listeners[type] = [];
    this.listeners[type].push(handler);
  }
  dispatch(type){
    for(const handler of this.listeners[type] || []) handler({target:this});
  }
  click(){
    this.dispatch("click");
    if(typeof this.onclick === "function") this.onclick({target:this});
  }
  set innerHTML(value){
    this._innerHTML = String(value);
    if(this.id === "metrics-body"){
      metricRowNodes = [];
      const pattern = /<tr class="catalog-row" data-metric="([^"]+)">/g;
      let match;
      while((match = pattern.exec(this._innerHTML))){
        metricRowNodes.push(new FakeElement({dataset:{metric: match[1]}, className:"catalog-row"}));
      }
    }
  }
  get innerHTML(){ return this._innerHTML; }
  querySelector(selector){ return querySelector(selector, this); }
  querySelectorAll(selector){ return querySelectorAll(selector, this); }
}

const desktop = new FakeElement({id:"tt-desktop-reference"});
const header = new FakeElement();
const familyFilters = new FakeElement({id:"metricFamilyFilters"});
const search = new FakeElement({id:"metricSearch"});
const thead = new FakeElement();
const metricsBody = new FakeElement({id:"metrics-body"});
const metricDetails = new FakeElement({id:"metric-details"});
const filterButtons = ["ALL", "F", "A", "M", "N", "S"].map(family =>
  new FakeElement({dataset:{family}, className:"metric-family-filter" + (family === "ALL" ? " active" : "")})
);

function querySelector(selector, root){
  if(selector === "#config-metrics .panel-header") return header;
  if(selector === "#config-metrics thead") return thead;
  if(selector === "#config-metrics tbody") return metricsBody;
  if(selector === ".metric-family-filter") return filterButtons[0] || null;
  if(selector.startsWith("#")) return nodesById.get(selector.slice(1)) || null;
  return null;
}
function querySelectorAll(selector, root){
  if(selector === ".metric-family-filter") return filterButtons;
  if(selector === "[data-metric]") return metricRowNodes;
  return [];
}
const document = {
  getElementById: id => nodesById.get(id) || null,
  querySelector,
  querySelectorAll
};
function q(selector, root=document){ return root.querySelector(selector); }
function qa(selector, root=document){ return Array.from(root.querySelectorAll(selector)); }
function ids(){ return metricRowNodes.map(row => row.dataset.metric); }
function clickFamily(family, expectedCount){
  const button = filterButtons.find(candidate => candidate.dataset.family === family);
  assert(button, `missing ${family} filter`);
  button.click();
  const visible = ids();
  assert(visible.length === expectedCount, `${family} expected ${expectedCount}, got ${visible.length}`);
  if(family !== "ALL"){
    assert(visible.every(id => id.startsWith(`${family}-`)), `${family} filter leaked ids: ${visible.join(",")}`);
  }
}

eval(payload.metricsScript + `
setupMetricsShell();
setupMetricsShell();
assert((search.listeners.input || []).length === 1, "search handler must be bound exactly once");
filterButtons.forEach(button => assert((button.listeners.click || []).length === 1, button.dataset.family + " handler must be bound exactly once"));
renderMetrics();
assert(ids().length === 47, "ALL render should expose 47 metrics");
clickFamily("F", 16);
clickFamily("A", 9);
clickFamily("M", 8);
clickFamily("N", 8);
clickFamily("S", 6);
clickFamily("ALL", 47);
clickFamily("F", 16);
search.value = "F-002";
search.dispatch("input");
assert(ids().length === 1 && ids()[0] === "F-002", "search should reduce F-filtered rows to F-002");
search.value = "";
search.dispatch("input");
assert(ids().length === 16 && ids().every(id => id.startsWith("F-")), "clearing search should restore current family filter");
`);

console.log(JSON.stringify({
  counts: {ALL:47, F:16, A:9, M:8, N:8, S:6},
  search: "PASS",
  duplicateListenerProtection: "PASS"
}));
"""

    result = subprocess.run(
        ["node", "-e", harness],
        input=json.dumps({"state": state, "metricsScript": metrics_script}),
        text=True,
        capture_output=True,
        check=True,
    )

    assert json.loads(result.stdout)["duplicateListenerProtection"] == "PASS"


def test_product_renderer_injects_metrics_without_frontend_mutation_api():
    html = render_product_dashboard(operator_control_token="secret-token", operator_command_submit_enabled=True)

    assert '"metrics": [' in html
    assert '"id": "S-006"' in html
    assert '"type": "NOT_A_FORMULA"' in html
    assert "/api/metrics" not in html
    assert "postJson(\"/api/metrics" not in html
