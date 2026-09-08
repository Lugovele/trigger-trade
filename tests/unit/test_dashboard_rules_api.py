from __future__ import annotations

from decimal import Decimal
from http import HTTPStatus
from http.client import HTTPConnection
import json
import threading

from triggertrade.dashboard.__main__ import create_server
from triggertrade.persistence import TradingRulesStore
from triggertrade.rules import TradingRulesService
from tests.unit.test_instrument_catalog import _catalog_service
from tests.unit.test_trading_rules_registry import _config


def test_rules_api_current_history_detail_are_backend_backed(tmp_path):
    db, catalog, rules_service = _rules_api_db(tmp_path)
    current = rules_service.get_current_rules_version()
    server = create_server(port=0, db_path=db, trading_rules_service=rules_service, instrument_catalog_service=catalog)
    host, port = server.server_address
    thread = _start(server)
    try:
        current_payload = _json_request(host, port, "GET", "/api/rules/current")
        history_payload = _json_request(host, port, "GET", "/api/rules/history")
        detail_payload = _json_request(host, port, "GET", f"/api/rules/version/{current.rules_version_id}")
        html = _text_request(host, port, "GET", "/rules")

        assert current_payload["rules_version_id"] == current.rules_version_id
        assert current_payload["display_version"] == "v1"
        assert current_payload["position_rules"]["take_profit_mode"] == "FIXED"
        assert current_payload["runtime_support"]["take_profit_modes"]["DYNAMIC"] == "unsupported_fail_closed"
        assert current_payload["runtime_support"]["daily_loss_enforcement"] == "accounting_backed_new_entries"
        assert history_payload["versions"][0]["rules_version_id"] == current.rules_version_id
        assert detail_payload["rules_version_id"] == current.rules_version_id
        assert "Rules · v1" in html
        rules_section = _section(html, 'id="rules"', 'id="rules-version"')
        assert "DOGEUSDT" not in rules_section
        assert "Minimum Net Edge 0.5%" not in rules_section
    finally:
        _stop(server, thread)


def test_rules_api_save_creates_new_immutable_version_and_rejects_noop(tmp_path):
    db, catalog, rules_service = _rules_api_db(tmp_path)
    server = create_server(port=0, db_path=db, trading_rules_service=rules_service, instrument_catalog_service=catalog)
    host, port = server.server_address
    thread = _start(server)
    try:
        current = _json_request(host, port, "GET", "/api/rules/current")
        payload = _editable_rules_payload(current, server.operator_control_token)
        payload["position_rules"]["fixed_take_profit_pct"] = "2.0"
        created = _json_request(host, port, "POST", "/api/rules/versions", payload, expected=HTTPStatus.CREATED)

        assert created["changed"] is True
        assert created["rules"]["display_version"] == "v2"
        assert created["rules"]["created_from_version_id"] == current["rules_version_id"]
        assert rules_service.get_rules_version(current["rules_version_id"]).draft.fixed_take_profit_pct == Decimal("0.01")

        noop_payload = _editable_rules_payload(created["rules"], server.operator_control_token)
        noop = _json_request(host, port, "POST", "/api/rules/versions", noop_payload, expected=HTTPStatus.BAD_REQUEST)
        assert noop["changed"] is False
        assert [row["display_version"] for row in _json_request(host, port, "GET", "/api/rules/history")["versions"]] == ["v2", "v1"]
    finally:
        _stop(server, thread)


def test_rules_api_stale_conflict_and_symbol_validation_fail_closed(tmp_path):
    db, catalog, rules_service = _rules_api_db(tmp_path)
    server = create_server(port=0, db_path=db, trading_rules_service=rules_service, instrument_catalog_service=catalog)
    host, port = server.server_address
    thread = _start(server)
    try:
        v1 = _json_request(host, port, "GET", "/api/rules/current")
        rules_service.create_rules_version_from_current(changes={"fixed_take_profit_pct": Decimal("0.02")}, created_source="unit")
        stale = _editable_rules_payload(v1, server.operator_control_token)
        stale["position_rules"]["fixed_take_profit_pct"] = "3.0"
        conflict = _json_request(host, port, "POST", "/api/rules/versions", stale, expected=HTTPStatus.CONFLICT)
        assert conflict["current"]["display_version"] == "v2"
        assert [row["display_version"] for row in _json_request(host, port, "GET", "/api/rules/history")["versions"]] == ["v2", "v1"]

        invalid = _editable_rules_payload(conflict["current"], server.operator_control_token)
        invalid["coins"] = [{"symbol": "DOGEUSDT", "enabled": True, "max_allocation_pct": None}]
        rejected = _json_request(host, port, "POST", "/api/rules/versions", invalid, expected=HTTPStatus.BAD_REQUEST)
        assert "catalog" in rejected["error"]
    finally:
        _stop(server, thread)


def test_rules_api_invalid_enum_and_non_finite_numbers_are_sanitized(tmp_path):
    db, catalog, rules_service = _rules_api_db(tmp_path)
    server = create_server(port=0, db_path=db, trading_rules_service=rules_service, instrument_catalog_service=catalog)
    host, port = server.server_address
    thread = _start(server)
    try:
        current = _json_request(host, port, "GET", "/api/rules/current")
        invalid_enum = _editable_rules_payload(current, server.operator_control_token)
        invalid_enum["position_rules"]["take_profit_mode"] = "SCRIPT"
        enum_response = _json_request(host, port, "POST", "/api/rules/versions", invalid_enum, expected=HTTPStatus.BAD_REQUEST)
        assert enum_response["error"] == "unsupported take-profit mode"

        invalid_number = _editable_rules_payload(current, server.operator_control_token)
        invalid_number["position_rules"]["position_size_pct"] = "NaN"
        number_response = _json_request(host, port, "POST", "/api/rules/versions", invalid_number, expected=HTTPStatus.BAD_REQUEST)
        assert number_response["error"] == "numeric rules fields must be finite decimals"

        assert [row["display_version"] for row in _json_request(host, port, "GET", "/api/rules/history")["versions"]] == ["v1"]
    finally:
        _stop(server, thread)


def test_instrument_search_and_refresh_are_backend_only_and_sanitized(tmp_path):
    db, catalog, rules_service = _rules_api_db(tmp_path)
    server = create_server(port=0, db_path=db, trading_rules_service=rules_service, instrument_catalog_service=catalog)
    host, port = server.server_address
    thread = _start(server)
    try:
        search = _json_request(host, port, "GET", "/api/instruments/search?q=eth")
        assert [row["symbol"] for row in search["coins"]] == ["ETHUSDT"]

        refreshed = _json_request(host, port, "POST", "/api/instruments/refresh", {"token": server.operator_control_token})
        rendered = json.dumps(refreshed)
        assert refreshed["status"] == "OK"
        assert "api.bybit.com" not in rendered
        assert "BYBIT_API" not in rendered

        forbidden = _json_request(host, port, "POST", "/api/instruments/refresh", {"token": "wrong"}, expected=HTTPStatus.FORBIDDEN)
        assert forbidden["error"] == "operator token required"
    finally:
        _stop(server, thread)


def test_rules_ui_preserves_hidden_coins_leverage_and_disabled_thresholds(tmp_path):
    db, catalog, rules_service = _rules_api_db(tmp_path)
    rules_service.create_rules_version_from_current(
        changes={
            "leverage": Decimal("7"),
            "minimum_net_edge_enabled": False,
            "max_open_positions_enabled": False,
            "daily_loss_limit_enabled": False,
            "coins": (
                __import__("triggertrade.rules", fromlist=["CoinRule"]).CoinRule("BTCUSDT", True, Decimal("0.08")),
                __import__("triggertrade.rules", fromlist=["CoinRule"]).CoinRule("ETHUSDT", True, None),
            ),
        },
        created_source="unit",
    )
    server = create_server(port=0, db_path=db, trading_rules_service=rules_service, instrument_catalog_service=catalog)
    host, port = server.server_address
    thread = _start(server)
    try:
        html = _text_request(host, port, "GET", "/rules")

        assert '<option selected>7x</option>' in html
        assert 'let coinDraft = new Map' in html
        assert 'coins: [...coinDraft.values()]' in html
        assert 'minimum_net_edge_pct: val("rulesEdge")' in html
        assert 'max_open_positions: val("rulesMaxOpen")' in html
        assert 'daily_loss_limit_pct: val("rulesDailyLoss")' in html
        assert "Dynamic TP: unsupported/fail closed" in html
        assert "Direction filters do not create SHORT alpha" in html
        assert "rules_version_id:" in html
        assert 'id="rulesCurrentVersionLabel"' in html
        assert 'id="rulesCurrentIdentity"' in html
        assert "renderCurrentIdentity();" in html
        assert "payloadSignature(currentPayload())!==cleanSnapshot" in html
        assert "refreshDirtyState();" in html
        assert 'id="rulesErrorPanel"' in html
        assert "showRulesError(msg)" in html
    finally:
        _stop(server, thread)


def _rules_api_db(tmp_path):
    db = tmp_path / "rules-api.sqlite3"
    catalog = _catalog_service(tmp_path, db_path=db)
    service = TradingRulesService(TradingRulesStore(db), symbol_validator=catalog.validate_symbol)
    service.ensure_initial_version(_config(db), created_at="2026-09-07T00:00:00+00:00")
    return db, catalog, service


def _start(server):
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread


def _stop(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def _json_request(host, port, method, path, payload=None, *, expected=HTTPStatus.OK):
    conn = HTTPConnection(host, port, timeout=3)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {} if body is None else {"Content-Type": "application/json"}
    conn.request(method, path, body=body, headers=headers)
    response = conn.getresponse()
    data = response.read().decode("utf-8")
    assert response.status == expected
    return json.loads(data)


def _text_request(host, port, method, path):
    conn = HTTPConnection(host, port, timeout=3)
    conn.request(method, path)
    response = conn.getresponse()
    body = response.read().decode("utf-8")
    assert response.status == HTTPStatus.OK
    return body


def _editable_rules_payload(current, token):
    return {
        "token": token,
        "expected_rules_version_id": current["rules_version_id"],
        "expected_display_version": current["display_version"],
        "position_rules": dict(current["position_rules"]),
        "portfolio_rules": dict(current["portfolio_rules"]),
        "coins": [dict(row) for row in current["coins"]],
    }


def _section(html: str, start: str, end: str) -> str:
    start_index = html.index(start)
    end_index = html.index(end, start_index + len(start))
    return html[start_index:end_index]
