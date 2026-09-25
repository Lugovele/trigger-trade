from __future__ import annotations

from http import HTTPStatus
from http.client import HTTPConnection
import json
from pathlib import Path
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


def test_product_renderer_injects_metrics_without_frontend_mutation_api():
    html = render_product_dashboard(operator_control_token="secret-token", operator_command_submit_enabled=True)

    assert '"metrics": [' in html
    assert '"id": "S-006"' in html
    assert '"type": "NOT_A_FORMULA"' in html
    assert "/api/metrics" not in html
    assert "postJson(\"/api/metrics" not in html
