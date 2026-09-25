"""Local read-only TriggerTrade v6 dashboard."""

from __future__ import annotations

from html import escape
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import secrets
from urllib.parse import parse_qs, unquote, urlparse

from triggertrade.config import ConfigError
from triggertrade.dashboard.read_model import (
    DashboardReadModel,
    ResearchSummaryRow,
    SetSummaryView,
    TriggerSetMembershipView,
    _rules_version_payload,
    _rules_version_summary_payload,
)
from triggertrade.dashboard.readiness import evaluate_dashboard_readiness
from triggertrade.dashboard.commands import DashboardCommandBoundary, DashboardCommandError
from triggertrade.exchanges import BybitDemoClient
from triggertrade.backtest import BacktestPlan
from triggertrade.persistence import (
    InstrumentCatalogStore,
    MessageStore,
    MessageStoreError,
    OperatorStateStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresResearchConfigurationRegistryClient,
    ResearchPromotionGovernanceClient,
    ResearchStore,
    ResearchStoreError,
    TradingRulesStore,
    TriggerSetStore,
    apply_postgres_migrations,
)
from triggertrade.rules import CoinRule, TradingRulesError, TradingRulesService
from triggertrade.services.bootstrap import ensure_runtime_registry_for_env, merged_runtime_env, runtime_db_path
from triggertrade.services.instrument_catalog import InstrumentCatalogService
from triggertrade.services.operator_auth import (
    LOCAL_DEV_AUTH_SOURCE,
    AuthorizedOperatorCommand,
    OperatorAuthorizationError,
    OperatorCommandAuthorizer,
    operator_authorizer_from_env,
)
from triggertrade.services.operator_execution_bridge import DashboardOperatorExecutionBridge
from triggertrade.services.research import ResearchService, ResearchServiceError
from triggertrade.services.research_demo_execution import PostgresResearchDemoExecutionHandoff


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
ALLOWED_HOSTS = frozenset({DEFAULT_HOST, "0.0.0.0"})
LOCAL_DEV_OPERATOR_COOKIE = "tt_local_operator"
LOCAL_DEV_OPERATOR_HEADER = "X-TriggerTrade-Local-Operator"


class DashboardRegistryUnavailable(RuntimeError):
    """Raised when configured production registry reads are unavailable."""


class DashboardServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address,
        handler_class,
        *,
        read_model: DashboardReadModel,
        operator_store: OperatorStateStore,
        message_store: MessageStore,
        trading_rules_service: TradingRulesService,
        instrument_catalog_service: InstrumentCatalogService,
        research_service: ResearchService,
        operator_authorizer: OperatorCommandAuthorizer,
        command_boundary: DashboardCommandBoundary,
        operator_actions=None,
        readiness_env=None,
        postgres_health_probe=None,
        postgres_runtime_probe=None,
        postgres_registry_probe=None,
        research_config_registry=None,
    ) -> None:
        super().__init__(server_address, handler_class)
        self.read_model = read_model
        self.operator_store = operator_store
        self.message_store = message_store
        self.trading_rules_service = trading_rules_service
        self.instrument_catalog_service = instrument_catalog_service
        self.research_service = research_service
        self.operator_authorizer = operator_authorizer
        self.command_boundary = command_boundary
        self.operator_actions = operator_actions
        self.operator_control_token = (
            secrets.token_urlsafe(24)
            if operator_authorizer.auth_mode == LOCAL_DEV_AUTH_SOURCE and _server_is_loopback(self)
            else ""
        )
        self.readiness_env = dict(os.environ if readiness_env is None else readiness_env)
        self.postgres_health_probe = postgres_health_probe
        self.postgres_runtime_probe = postgres_runtime_probe
        self.postgres_registry_probe = postgres_registry_probe
        self.research_config_registry = research_config_registry


class DashboardHandler(BaseHTTPRequestHandler):
    server: DashboardServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/rules/current":
            try:
                payload = _current_rules_payload(self.server)
            except DashboardRegistryUnavailable as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
                return
            if payload is None:
                self._send_json({"error": "current trading rules version is unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                self._send_json(payload)
            return
        if parsed.path == "/api/rules/history":
            try:
                self._send_json({"versions": _rules_history_payloads(self.server)})
            except DashboardRegistryUnavailable as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
            return
        if parsed.path.startswith("/api/rules/version/"):
            identity = unquote(parsed.path.removeprefix("/api/rules/version/"))
            try:
                payload = _rules_version_detail_payload(self.server, identity)
            except DashboardRegistryUnavailable as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
                return
            if payload is None:
                self._send_json({"error": "trading rules version not found"}, HTTPStatus.NOT_FOUND)
            else:
                self._send_json(payload)
            return
        if parsed.path == "/api/messages":
            try:
                messages = [_message_payload(row) for row in self.server.message_store.list_messages(limit=50)]
                self._send_json(
                    {
                        "available": True,
                        "messages": messages,
                        "unread_count": self.server.message_store.get_unread_message_count(),
                    }
                )
            except Exception as exc:  # noqa: BLE001 - API returns unavailable instead of fake empty/zero state.
                self._send_json({"available": False, "error": _safe_public_error(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
            return
        if parsed.path == "/api/messages/unread-count":
            try:
                self._send_json({"available": True, "unread_count": self.server.message_store.get_unread_message_count()})
            except Exception as exc:  # noqa: BLE001 - API returns unavailable instead of fake zero.
                self._send_json({"available": False, "error": _safe_public_error(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
            return
        if parsed.path == "/api/readiness":
            self._send_json(_readiness_payload(self.server))
            return
        if parsed.path == "/api/research":
            try:
                self._send_json({"research": [_research_summary_payload(row) for row in _research_summaries(self.server)]})
            except DashboardRegistryUnavailable as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
            return
        if parsed.path.startswith("/api/research/"):
            parts = [unquote(part) for part in parsed.path.strip("/").split("/")]
            if len(parts) == 3 and parts[0] == "api" and parts[1] == "research":
                try:
                    payload = _research_detail_payload(self.server, parts[2])
                except DashboardRegistryUnavailable as exc:
                    self._send_json({"error": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
                    return
                if payload is None:
                    self._send_json({"error": "research id not found"}, HTTPStatus.NOT_FOUND)
                else:
                    self._send_json(payload)
                return
            if len(parts) == 4 and parts[0] == "api" and parts[1] == "research" and parts[3] == "compare":
                self._send_json(self.server.read_model.get_research_compare(parts[2]))
                return
        if parsed.path == "/api/instruments/search":
            query = parse_qs(parsed.query).get("q", [""])[0]
            try:
                registry_coins = _registry_rules_coins(_current_rules_payload(self.server))
            except DashboardRegistryUnavailable as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
                return
            if query and registry_coins:
                normalized_query = query.strip().upper()
                registry_coins = tuple(
                    item for item in registry_coins if normalized_query in str(item.get("symbol") or "")
                )
            self._send_json(
                {
                    "catalog": _catalog_state_payload(self.server.read_model),
                    "coins": registry_coins
                    if self.server.research_config_registry is not None
                    else self.server.read_model.search_rules_catalog_coins(query),
                }
            )
            return
        product_pages = {
            "/": "overview",
            "/overview": "overview",
            "/portfolio": "overview",
            "/trading-configuration": "config",
            "/metrics": "config",
            "/sets": "config",
            "/trigger-catalog": "config",
            "/trigger-detail": "config",
            "/rules": "config",
            "/rules-version": "config",
            "/research": "research",
            "/research-detail": "research-detail",
            "/messages": "messages",
            "/analytics": "research",
        }
        if parsed.path in product_pages:
            self._send_html(
                render_dashboard(
                    self.server.read_model,
                    initial_page=product_pages[parsed.path],
                    research_config_registry=self.server.research_config_registry,
                )
            )
            return
        if parsed.path.startswith("/set/"):
            parts = [unquote(part) for part in parsed.path.strip("/").split("/")]
            set_id = parts[1] if len(parts) > 1 else ""
            version = parts[2] if len(parts) > 2 else ""
            if not set_id or not version or self.server.read_model.get_trigger_set(set_id, version) is None:
                self._send_html(render_not_found(parsed.path), HTTPStatus.NOT_FOUND)
                return
            self._send_html(
                render_dashboard(
                    self.server.read_model,
                    initial_page="sets",
                    research_config_registry=self.server.research_config_registry,
                )
            )
            return
        if parsed.path.startswith("/triggers/"):
            parts = [unquote(part) for part in parsed.path.strip("/").split("/")]
            trigger_id = parts[1] if len(parts) > 1 else ""
            version = parts[2] if len(parts) > 2 else None
            if self.server.read_model.get_trigger_detail(trigger_id, version) is None:
                self._send_html(render_not_found(parsed.path), HTTPStatus.NOT_FOUND)
                return
            self._send_html(
                render_dashboard(
                    self.server.read_model,
                    initial_page="trigger-detail",
                    selected_trigger_id=trigger_id,
                    selected_trigger_version=version,
                    research_config_registry=self.server.research_config_registry,
                )
            )
            return
        if parsed.path.startswith("/rules-version/"):
            self._send_html(
                render_dashboard(
                    self.server.read_model,
                    initial_page="rules-version",
                    research_config_registry=self.server.research_config_registry,
                )
            )
            return
        if parsed.path.startswith("/research/"):
            self._send_html(
                render_dashboard(
                    self.server.read_model,
                    initial_page="research-detail",
                    research_config_registry=self.server.research_config_registry,
                )
            )
            return
        if parsed.path.startswith("/rules/"):
            parts = [unquote(part) for part in parsed.path.strip("/").split("/")]
            rule_id = parts[1] if len(parts) > 1 else ""
            version = parts[2] if len(parts) > 2 else None
            detail = self.server.read_model.get_rule_detail(rule_id, version)
            if detail is None:
                self._send_html(render_not_found(parsed.path), HTTPStatus.NOT_FOUND)
            else:
                self._send_html(render_rule_detail(detail))
            return
        if parsed.path.startswith("/trades/"):
            trade_id = unquote(parsed.path.removeprefix("/trades/"))
            detail = self.server.read_model.get_futures_trade_detail(trade_id)
            if detail is None:
                self._send_html(render_not_found(parsed.path), HTTPStatus.NOT_FOUND)
            else:
                self._send_html(render_trade_detail(detail))
            return
        if parsed.path.startswith("/backtests/"):
            run_id = unquote(parsed.path.removeprefix("/backtests/"))
            detail = self.server.read_model.get_backtest_detail(run_id)
            if detail is None:
                self._send_html(render_not_found(parsed.path), HTTPStatus.NOT_FOUND)
            else:
                self._send_html(render_backtest_detail(detail))
            return
        if parsed.path.startswith("/recommendations/"):
            recommendation_id = unquote(parsed.path.removeprefix("/recommendations/"))
            detail = self.server.read_model.get_recommendation(recommendation_id)
            if detail is None:
                self._send_html(render_not_found(parsed.path), HTTPStatus.NOT_FOUND)
            else:
                self._send_html(render_recommendation_detail(detail))
            return
        if parsed.path == "/healthz":
            self._send_text("ok")
            return
        self._send_html(render_not_found(parsed.path), HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/research":
            payload = self._read_json_body(max_bytes=4096)
            command = self._authorize_json_operator_command("RESEARCH_CREATE", payload, scope="RESEARCH")
            if command is None:
                return
            try:
                record = self.server.command_boundary.create_research(
                    command,
                    set_id=str(payload.get("set_id") or ""),
                    set_version=str(payload.get("set_version") or ""),
                    rules_version_id=str(payload.get("rules_version_id") or ""),
                )
            except ResearchServiceError as exc:
                self._send_json({"error": _safe_public_error(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json({"research": _research_record_payload(record)}, HTTPStatus.CREATED)
            return
        if parsed.path.startswith("/api/research/"):
            parts = [unquote(part) for part in parsed.path.strip("/").split("/")]
            payload = self._read_json_body(max_bytes=4096)
            command_type = _research_command_type(parts)
            command = self._authorize_json_operator_command(command_type, payload, scope="RESEARCH", target=parts[2] if len(parts) > 2 else "RESEARCH")
            if command is None:
                return
            try:
                if len(parts) == 4 and parts[:2] == ["api", "research"] and parts[3] == "backtests":
                    plan = _backtest_plan_from_payload(payload)
                    run = self.server.command_boundary.run_backtest(
                        command,
                        research_id=parts[2],
                        plan=plan,
                    )
                    self._send_json({"backtest": _research_run_payload(run)}, HTTPStatus.CREATED)
                    return
                if len(parts) == 6 and parts[:2] == ["api", "research"] and parts[3] == "backtests" and parts[5] == "select":
                    record = self.server.command_boundary.select_backtest_run(command, research_id=parts[2], run_id=parts[4])
                    self._send_json({"research": _research_record_payload(record)})
                    return
                if len(parts) == 5 and parts[:2] == ["api", "research"] and parts[3] == "demo" and parts[4] == "start":
                    run = self.server.command_boundary.start_demo_run(command, research_id=parts[2])
                    status = HTTPStatus.CONFLICT if getattr(run, "status", None).value == "BLOCKED" else HTTPStatus.CREATED
                    self._send_json({"demo": _research_run_payload(run)}, status)
                    return
                if len(parts) == 6 and parts[:2] == ["api", "research"] and parts[3] == "demo" and parts[5] == "stop":
                    run = self.server.command_boundary.stop_demo_run(command, research_id=parts[2], run_id=parts[4])
                    self._send_json({"demo": _research_run_payload(run)})
                    return
                if len(parts) == 6 and parts[:2] == ["api", "research"] and parts[3] == "demo" and parts[5] == "select":
                    record = self.server.command_boundary.select_demo_run(command, research_id=parts[2], run_id=parts[4])
                    self._send_json({"research": _research_record_payload(record)})
                    return
                if len(parts) == 4 and parts[:2] == ["api", "research"] and parts[3] == "archive":
                    record = self.server.command_boundary.archive_research(command, research_id=parts[2])
                    self._send_json({"research": _research_record_payload(record)})
                    return
                if len(parts) == 5 and parts[:2] == ["api", "research"] and parts[3] == "decision" and parts[4] == "make-active":
                    idempotency_key = str(payload.get("idempotency_key") or "").strip()
                    if not idempotency_key:
                        self._send_json({"error": "idempotency_key required"}, HTTPStatus.BAD_REQUEST)
                        return
                    record = self.server.command_boundary.request_make_active(command, research_id=parts[2], idempotency_key=idempotency_key)
                    blocked = record.decision.value == "MAKE_ACTIVE_BLOCKED"
                    self._send_json({"research": _research_record_payload(record), "blocked": blocked}, HTTPStatus.CONFLICT if blocked else HTTPStatus.OK)
                    return
            except (ResearchServiceError, ResearchStoreError, ValueError) as exc:
                self._send_json({"error": _safe_public_error(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json({"error": "research route not found"}, HTTPStatus.NOT_FOUND)
            return
        if parsed.path == "/api/rules/versions":
            payload = self._read_json_body(max_bytes=16000)
            command = self._authorize_json_operator_command("RULES_VERSION_CREATE", payload, scope="OPERATOR", target="RULES")
            if command is None:
                return
            try:
                changes = _rules_changes_from_payload(payload)
                result = self.server.command_boundary.create_rules_version(
                    command=command,
                    changes=changes,
                    expected_current_rules_version_id=str(payload.get("expected_rules_version_id") or ""),
                    expected_current_display_version=str(payload.get("expected_display_version") or ""),
                )
            except TradingRulesError as exc:
                status = HTTPStatus.CONFLICT if "pointer changed" in str(exc) or "display version changed" in str(exc) else HTTPStatus.BAD_REQUEST
                current = self.server.read_model.get_current_rules_version_payload()
                self._send_json({"error": _safe_public_error(exc), "current": current}, status)
                return
            response = self.server.read_model.get_current_rules_version_payload()
            history = self.server.read_model.list_rules_version_payloads()
            if not result.changed:
                self._send_json({"changed": False, "error": "No semantic changes", "current": response, "history": history}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json({"changed": True, "rules": response, "history": history, "change_summary": result.change_summary}, HTTPStatus.CREATED)
            return
        if parsed.path == "/api/instruments/refresh":
            payload = self._read_json_body(max_bytes=2048)
            command = self._authorize_json_operator_command("INSTRUMENTS_REFRESH", payload, scope="OPERATOR", target="INSTRUMENT_CATALOG")
            if command is None:
                return
            result = self.server.command_boundary.refresh_instrument_catalog(command)
            status = HTTPStatus.OK if result.status == "OK" else HTTPStatus.SERVICE_UNAVAILABLE
            if result.status != "OK":
                self.server.command_boundary.record_instrument_catalog_refresh_failure(result)
            self._send_json(
                {
                    "status": result.status,
                    "fetched_count": result.fetched_count,
                    "tradeable_count": result.tradeable_count,
                    "excluded_count": result.excluded_count,
                    "updated_at": result.updated_at,
                    "error": result.error,
                    "catalog": _catalog_state_payload(self.server.read_model),
                },
                status,
            )
            return
        if parsed.path == "/api/messages/mark-read":
            payload = self._read_json_body(max_bytes=4096)
            command = self._authorize_json_operator_command("MESSAGES_MARK_READ", payload, scope="OPERATOR", target="MESSAGES")
            if command is None:
                return
            raw_ids = payload.get("message_ids")
            if not isinstance(raw_ids, list) or not all(isinstance(item, str) for item in raw_ids):
                self._send_json({"error": "message_ids must be a list of ids"}, HTTPStatus.BAD_REQUEST)
                return
            try:
                changed = self.server.command_boundary.mark_messages_read(command, raw_ids)
            except MessageStoreError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json({"changed": changed, "unread_count": self.server.message_store.get_unread_message_count()})
            return
        if parsed.path == "/api/system-history/export":
            payload = self._read_json_body(max_bytes=2048)
            command = self._authorize_json_operator_command("SYSTEM_HISTORY_EXPORT", payload, scope="OPERATOR", target="SYSTEM_HISTORY")
            if command is None:
                return
            try:
                text = self.server.command_boundary.export_system_history(command)
                self._send_json({"format": "text/plain", "text": text})
            except Exception as exc:  # noqa: BLE001 - export failures are surfaced and audited without leaking payloads.
                error = _safe_public_error(exc)
                self.server.command_boundary.record_system_history_export_failure(command, error)
                self._send_json({"error": error}, HTTPStatus.SERVICE_UNAVAILABLE)
            return
        if parsed.path in {"/operator/pause", "/operator/resume", "/operator/close-one", "/operator/close-all"}:
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(min(length, 2048)).decode("utf-8")
            values = parse_qs(body)
            if values.get("confirm", [""])[0] != "yes":
                self._send_html(render_not_found("operator confirmation required"), HTTPStatus.BAD_REQUEST)
                return
            command = self._authorize_form_operator_command(_operator_form_command_type(parsed.path), values)
            if command is None:
                self._send_html(render_not_found("operator confirmation required"), HTTPStatus.BAD_REQUEST)
                return
            if parsed.path.endswith("/pause"):
                self.server.command_boundary.pause_entries(command)
            elif parsed.path.endswith("/resume"):
                self.server.command_boundary.resume_entries(command)
            elif parsed.path.endswith("/close-one"):
                position_id = values.get("position_id", [""])[0][:160]
                symbol = values.get("symbol", [""])[0][:40]
                if not position_id or not symbol:
                    self._send_html(render_not_found("position id required"), HTTPStatus.BAD_REQUEST)
                    return
                try:
                    self.server.command_boundary.close_one(command, position_id=position_id, symbol=symbol)
                except DashboardCommandError as exc:
                    error = str(exc)
                    self._send_html(render_not_found(error), HTTPStatus.SERVICE_UNAVAILABLE)
                    return
                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", "/")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
            else:
                if values.get("phrase", [""])[0] != "CLOSE ALL":
                    self._send_html(render_not_found("close-all confirmation phrase required"), HTTPStatus.BAD_REQUEST)
                    return
                try:
                    self.server.command_boundary.close_all(command)
                except DashboardCommandError as exc:
                    error = str(exc)
                    self._send_html(render_not_found(error), HTTPStatus.SERVICE_UNAVAILABLE)
                    return
                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", "/")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", "/")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        self._send_html(render_not_found("write operations are disabled"), HTTPStatus.METHOD_NOT_ALLOWED)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_html(self, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        cookie = _local_dev_operator_cookie(self.server)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(payload)

    def _send_text(self, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, value, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(value, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _read_json_body(self, *, max_bytes: int) -> dict:
        length = min(int(self.headers.get("Content-Length", "0") or "0"), max_bytes)
        if length <= 0:
            return {}
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def _authorize_json_operator_command(
        self,
        command_type: str,
        payload: dict,
        *,
        scope: str,
        target: str = "ACTIVE",
    ) -> AuthorizedOperatorCommand | None:
        payload = _payload_with_local_dev_cookie_token(self.headers, payload, self.server)
        try:
            return self.server.operator_authorizer.authorize_http_command(
                command_type,
                headers=self.headers,
                payload=payload,
                local_dev_token=self.server.operator_control_token,
                scope=scope,
                target=target,
                idempotency_key=str(payload.get("idempotency_key") or "") or None,
            )
        except OperatorAuthorizationError as exc:
            message = str(exc)
            status = HTTPStatus.BAD_REQUEST if "invalid" in message or "conflict" in message else HTTPStatus.FORBIDDEN
            public = "operator token required" if message == "operator authorization required" else message
            self._send_json({"error": public}, status)
            return None

    def _authorize_form_operator_command(
        self,
        command_type: str,
        values: dict[str, list[str]],
    ) -> AuthorizedOperatorCommand | None:
        payload = {key: items[0] for key, items in values.items() if items}
        idempotency_key = str(payload.get("idempotency_key") or "").strip()
        if command_type in {"CLOSE_ONE", "CLOSE_ALL"} and not idempotency_key:
            return None
        payload = _payload_with_local_dev_cookie_token(self.headers, payload, self.server)
        try:
            return self.server.operator_authorizer.authorize_http_command(
                command_type,
                headers=self.headers,
                payload=payload,
                local_dev_token=self.server.operator_control_token,
                scope="OPERATOR",
                target="ACTIVE",
                idempotency_key=idempotency_key or None,
            )
        except OperatorAuthorizationError:
            return None


def _local_dev_operator_cookie(server: DashboardServer) -> str:
    if server.operator_authorizer.auth_mode != LOCAL_DEV_AUTH_SOURCE or not server.operator_control_token:
        return ""
    if not _server_is_loopback(server):
        return ""
    cookie = SimpleCookie()
    cookie[LOCAL_DEV_OPERATOR_COOKIE] = server.operator_control_token
    morsel = cookie[LOCAL_DEV_OPERATOR_COOKIE]
    morsel["path"] = "/"
    morsel["httponly"] = True
    morsel["samesite"] = "Strict"
    morsel["max-age"] = "28800"
    return morsel.OutputString()


def _payload_with_local_dev_cookie_token(headers, payload: dict, server: DashboardServer) -> dict:
    if server.operator_authorizer.auth_mode != LOCAL_DEV_AUTH_SOURCE:
        return payload
    if payload.get("token") or not server.operator_control_token:
        return payload
    if not _server_is_loopback(server):
        return payload
    if not _local_dev_cookie_request_is_same_origin(headers, server):
        return payload
    token = _cookie_value(headers.get("Cookie", ""), LOCAL_DEV_OPERATOR_COOKIE)
    if token != server.operator_control_token:
        return payload
    updated = dict(payload)
    updated["token"] = token
    return updated


def _server_is_loopback(server: DashboardServer) -> bool:
    host = str(server.server_address[0])
    return host in {DEFAULT_HOST, "::1", "localhost"}


def _local_dev_cookie_request_is_same_origin(headers, server: DashboardServer) -> bool:
    expected = _server_origin(server)
    if headers.get(LOCAL_DEV_OPERATOR_HEADER) != "1":
        return False
    host = (headers.get("Host") or "").strip().lower()
    if host and host != expected.removeprefix("http://"):
        return False
    origin = (headers.get("Origin") or "").strip().lower()
    if origin and origin != expected:
        return False
    referer = (headers.get("Referer") or "").strip().lower()
    if referer and not (referer == expected or referer.startswith(expected + "/")):
        return False
    return True


def _server_origin(server: DashboardServer) -> str:
    host, port = server.server_address[:2]
    return f"http://{host}:{port}".lower()


def _cookie_value(raw_cookie: str, name: str) -> str:
    if not raw_cookie:
        return ""
    cookie = SimpleCookie()
    try:
        cookie.load(raw_cookie)
    except Exception:  # noqa: BLE001 - malformed cookies simply fail authorization.
        return ""
    morsel = cookie.get(name)
    return morsel.value if morsel is not None else ""


def render_dashboard(
    read_model: DashboardReadModel,
    selected_set: str = "",
    initial_page: str = "portfolio",
    *,
    selected_trigger_id: str | None = None,
    selected_trigger_version: str | None = None,
    research_config_registry=None,
) -> str:
    from triggertrade.dashboard.product_ui import render_product_dashboard

    operator_state = getattr(read_model, "get_operator_trading_state", lambda: None)()
    operator_control_token = str(getattr(read_model, "operator_control_token", "") or "")
    operator_command_submit_enabled = bool(getattr(read_model, "operator_command_submit_enabled", False))
    open_positions = read_model.list_portfolio_open_positions()
    closed_positions = read_model.list_portfolio_closed_positions()
    portfolio = {
        "snapshot": read_model.get_portfolio_snapshot(),
        "open_positions": open_positions,
        "closed_positions": closed_positions,
        "open_summary": read_model.get_portfolio_open_summary(),
        "closed_summary": read_model.get_portfolio_closed_summary(),
        "filters": {
            "symbols": sorted({row.symbol for row in (*open_positions, *closed_positions)}),
            "set_versions": sorted(
                {row.set_version for row in (*open_positions, *closed_positions) if row.set_version}
            ),
        },
    }
    registry_error = ""
    try:
        registry_set_summaries = _registry_set_summaries(research_config_registry)
    except DashboardRegistryUnavailable as exc:
        registry_error = str(exc)
        registry_set_summaries = ()
    registry = {
        "sets": registry_set_summaries if research_config_registry is not None else read_model.list_set_summaries(),
        "triggers": read_model.list_trigger_catalog(),
        "selected_trigger": read_model.get_trigger_detail(selected_trigger_id, selected_trigger_version)
        if selected_trigger_id
        else None,
        "integrity_errors": (*read_model.get_registry_integrity_errors(), *((registry_error,) if registry_error else ())),
    }
    try:
        registry_rules_versions = _registry_rules_versions(research_config_registry)
    except DashboardRegistryUnavailable as exc:
        registry_error = registry_error or str(exc)
        registry_rules_versions = ()
    registry_rules_payloads = tuple(_rules_version_payload(version, ()) for version in registry_rules_versions)
    rules = {
        "current": registry_rules_payloads[0]
        if registry_rules_payloads
        else (None if research_config_registry is not None else read_model.get_current_rules_version_payload()),
        "history": tuple(_rules_version_summary_payload(version, ()) for version in registry_rules_versions)
        if research_config_registry is not None
        else read_model.list_rules_version_payloads(),
        "catalog": _catalog_state_payload(read_model),
        "coins": _registry_rules_coins(registry_rules_payloads[0] if registry_rules_payloads else None)
        if research_config_registry is not None
        else read_model.search_rules_catalog_coins(),
    }
    messages = _messages_payload_from_model(read_model)
    try:
        research_summaries = _registry_research_summaries(research_config_registry)
    except DashboardRegistryUnavailable as exc:
        registry_error = registry_error or str(exc)
        research_summaries = ()
    research = {
        "summaries": tuple(_research_summary_payload(row) for row in research_summaries)
        if research_config_registry is not None
        else tuple(_research_summary_payload(row) for row in read_model.list_research_summaries(limit=50)),
        "unavailable_reason": registry_error,
    }
    if registry_error:
        registry["integrity_errors"] = (*read_model.get_registry_integrity_errors(), registry_error)
    return render_product_dashboard(
        initial_page=initial_page,
        operator_state=operator_state,
        operator_control_token=operator_control_token,
        operator_command_submit_enabled=operator_command_submit_enabled,
        portfolio=portfolio,
        registry=registry,
        rules=rules,
        messages=messages,
        research=research,
    )


def _registry_set_summaries(registry) -> tuple[SetSummaryView, ...]:
    if registry is None or not callable(getattr(registry, "list_trigger_set_versions", None)):
        return ()
    try:
        versions = registry.list_trigger_set_versions()
    except Exception as exc:
        raise DashboardRegistryUnavailable("PostgreSQL Research configuration registry unavailable") from exc
    summaries: list[SetSummaryView] = []
    for version in versions:
        summaries.append(
            SetSummaryView(
                set_id=version.set_id,
                display_name=version.set_id,
                version=version.version,
                status=getattr(version.status, "value", str(version.status)),
                trigger_versions=tuple(
                    TriggerSetMembershipView(
                        trigger_id=rule_id,
                        display_name=rule_id,
                        version=rule_version,
                    )
                    for rule_id, rule_version in version.rule_versions
                ),
                created_at=version.created_at,
                updated_at=None,
                is_active=getattr(version.status, "value", str(version.status)) == "ACTIVE",
                symbol=version.symbol,
                timeframe=version.timeframe,
                integrity_errors=(),
            )
        )
    return tuple(summaries)


def _registry_rules_versions(registry):
    if registry is None or not callable(getattr(registry, "list_trading_rules_versions", None)):
        return ()
    try:
        return tuple(registry.list_trading_rules_versions())
    except Exception as exc:
        raise DashboardRegistryUnavailable("PostgreSQL Research configuration registry unavailable") from exc


def _registry_research_records(registry):
    if registry is None or not callable(getattr(registry, "list_research", None)):
        return ()
    try:
        return tuple(registry.list_research())
    except Exception as exc:
        raise DashboardRegistryUnavailable("PostgreSQL Research configuration registry unavailable") from exc


def _registry_research_summaries(registry) -> tuple[ResearchSummaryRow, ...]:
    return tuple(_research_summary_from_record(record) for record in _registry_research_records(registry))


def _research_summaries(server: DashboardServer) -> tuple[ResearchSummaryRow, ...]:
    if server.research_config_registry is not None:
        return _registry_research_summaries(server.research_config_registry)
    return server.read_model.list_research_summaries(limit=50)


def _research_detail_payload(server: DashboardServer, research_id: str) -> dict[str, object] | None:
    if server.research_config_registry is None:
        return server.read_model.get_research_detail(research_id)
    if not callable(getattr(server.research_config_registry, "get_research", None)):
        raise DashboardRegistryUnavailable("PostgreSQL Research configuration registry unavailable")
    try:
        record = server.research_config_registry.get_research(research_id)
    except Exception as exc:
        raise DashboardRegistryUnavailable("PostgreSQL Research configuration registry unavailable") from exc
    if record is None:
        return None
    run_detail = server.read_model.get_research_detail(research_id)
    research_payload = _research_record_payload(record)
    if run_detail is None:
        return {
            "research": research_payload,
            "backtests": (),
            "demos": (),
            "run_projection": {
                "available": False,
                "reason": "factual Research run store unavailable for this Research",
            },
            "compare": {
                "available": False,
                "reason": "factual Research run store unavailable for this Research",
            },
        }
    run_research = run_detail.get("research")
    if isinstance(run_research, dict):
        mutable_fields = (
            "status",
            "selected_backtest_run_id",
            "selected_demo_run_id",
            "decision",
            "decision_at",
            "archived_at",
            "made_active_at",
            "updated_at",
        )
        for field in mutable_fields:
            if field in run_research:
                research_payload[field] = run_research[field]
    return {
        "research": research_payload,
        "backtests": tuple(run_detail.get("backtests") or ()),
        "demos": tuple(run_detail.get("demos") or ()),
        "run_projection": {"available": True},
    }


def _research_summary_from_record(record) -> ResearchSummaryRow:
    return ResearchSummaryRow(
        research_id=record.research_id,
        status=record.status.value,
        set_id=record.set_id,
        set_version=record.set_version,
        rules_version_id=record.rules_version_id,
        rules_display_version=record.rules_display_version,
        selected_backtest_profit_factor=None,
        selected_backtest_trades=None,
        selected_demo_profit_factor=None,
        selected_demo_trades=None,
        compare_to_active="Unavailable",
        selected_backtest_run_id=record.selected_backtest_run_id,
        selected_demo_run_id=record.selected_demo_run_id,
        decision=record.decision.value,
        updated_at=record.updated_at,
    )


def _registry_rules_coins(rules_payload: dict[str, object] | None) -> tuple[dict[str, str | None], ...]:
    if not rules_payload:
        return ()
    coins = rules_payload.get("coins")
    if not isinstance(coins, (list, tuple)):
        return ()
    return tuple(
        {
            "symbol": str(item.get("symbol") or "").upper(),
            "base_coin": str(item.get("symbol") or "").upper().removesuffix("USDT"),
            "quote_coin": "USDT",
            "status": "TRADING",
            "max_leverage": None,
            "updated_at": None,
        }
        for item in coins
        if isinstance(item, dict) and str(item.get("symbol") or "").strip()
    )


def _current_rules_payload(server: DashboardServer) -> dict[str, object] | None:
    versions = _registry_rules_versions(server.research_config_registry)
    if server.research_config_registry is not None:
        return _rules_version_payload(versions[0], ()) if versions else None
    return server.read_model.get_current_rules_version_payload()


def _rules_history_payloads(server: DashboardServer) -> tuple[dict[str, object], ...]:
    versions = _registry_rules_versions(server.research_config_registry)
    if server.research_config_registry is not None:
        return tuple(_rules_version_summary_payload(version, ()) for version in versions)
    return server.read_model.list_rules_version_payloads()


def _rules_version_detail_payload(server: DashboardServer, identity: str) -> dict[str, object] | None:
    versions = _registry_rules_versions(server.research_config_registry)
    if server.research_config_registry is not None:
        for version in versions:
            if identity in {version.rules_version_id, version.version}:
                return _rules_version_payload(version, ())
        return None
    return server.read_model.get_rules_version_payload(identity)



def render_not_found(value: str) -> str:
    from triggertrade.dashboard.product_ui import render_product_not_found

    return render_product_not_found(value)


def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    db_path: str | Path = "runtime/triggertrade_paper.sqlite3",
    *,
    trading_rules_service: TradingRulesService | None = None,
    instrument_catalog_service: InstrumentCatalogService | None = None,
    research_service: ResearchService | None = None,
    operator_authorizer: OperatorCommandAuthorizer | None = None,
    operator_actions=None,
    readiness_env: dict[str, str] | None = None,
    postgres_health_probe=None,
    postgres_runtime_probe=None,
    postgres_registry_probe=None,
    promotion_governance_store=None,
    research_demo_handoff=None,
    research_config_registry=None,
) -> DashboardServer:
    if host not in ALLOWED_HOSTS:
        raise ValueError("dashboard host must be one of: 127.0.0.1, 0.0.0.0")
    read_model = DashboardReadModel(db_path)
    operator_store = OperatorStateStore(db_path)
    message_store = MessageStore(db_path)
    catalog_service = instrument_catalog_service or InstrumentCatalogService(store=InstrumentCatalogStore(db_path))
    rules_service = trading_rules_service or TradingRulesService(
        TradingRulesStore(db_path),
        symbol_validator=catalog_service.validate_symbol,
        version_registry=research_config_registry,
    )
    research_boundary = research_service or ResearchService(
        store=ResearchStore(db_path),
        trigger_set_store=TriggerSetStore(db_path, version_registry=research_config_registry),
        trading_rules_store=TradingRulesStore(db_path),
        message_store=message_store,
        promotion_governance_store=promotion_governance_store,
        demo_execution_handoff=research_demo_handoff,
        research_config_registry=research_config_registry,
    )
    authorizer = operator_authorizer or operator_authorizer_from_env(db_path, {})
    command_boundary = DashboardCommandBoundary(
        read_model=read_model,
        operator_store=operator_store,
        message_store=message_store,
        trading_rules_service=rules_service,
        instrument_catalog_service=catalog_service,
        research_service=research_boundary,
        operator_actions=operator_actions,
    )
    server = DashboardServer(
        (host, port),
        DashboardHandler,
        read_model=read_model,
        operator_store=operator_store,
        message_store=message_store,
        trading_rules_service=rules_service,
        instrument_catalog_service=catalog_service,
        research_service=research_boundary,
        operator_authorizer=authorizer,
        command_boundary=command_boundary,
        operator_actions=operator_actions,
        readiness_env=readiness_env,
        postgres_health_probe=postgres_health_probe,
        postgres_runtime_probe=postgres_runtime_probe,
        postgres_registry_probe=postgres_registry_probe,
        research_config_registry=research_config_registry,
    )
    read_model.operator_control_token = server.operator_control_token
    read_model.operator_command_submit_enabled = authorizer.browser_commands_supported and (
        authorizer.auth_mode != LOCAL_DEV_AUTH_SOURCE or bool(server.operator_control_token)
    )
    return server


def _research_command_type(parts: list[str]) -> str:
    if len(parts) == 4 and parts[:2] == ["api", "research"] and parts[3] == "backtests":
        return "RESEARCH_BACKTEST_RUN"
    if len(parts) == 6 and parts[:2] == ["api", "research"] and parts[3] == "backtests" and parts[5] == "select":
        return "RESEARCH_BACKTEST_SELECT"
    if len(parts) == 5 and parts[:2] == ["api", "research"] and parts[3] == "demo" and parts[4] == "start":
        return "RESEARCH_DEMO_START"
    if len(parts) == 6 and parts[:2] == ["api", "research"] and parts[3] == "demo" and parts[5] == "stop":
        return "RESEARCH_DEMO_STOP"
    if len(parts) == 6 and parts[:2] == ["api", "research"] and parts[3] == "demo" and parts[5] == "select":
        return "RESEARCH_DEMO_SELECT"
    if len(parts) == 4 and parts[:2] == ["api", "research"] and parts[3] == "archive":
        return "RESEARCH_ARCHIVE"
    if len(parts) == 5 and parts[:2] == ["api", "research"] and parts[3] == "decision" and parts[4] == "make-active":
        return "RESEARCH_PROMOTION_REQUEST"
    return "RESEARCH_UNKNOWN"


def _operator_form_command_type(path: str) -> str:
    if path.endswith("/pause"):
        return "PAUSE_ENTRIES"
    if path.endswith("/resume"):
        return "RESUME_ENTRIES"
    if path.endswith("/close-one"):
        return "CLOSE_ONE"
    if path.endswith("/close-all"):
        return "CLOSE_ALL"
    return "OPERATOR_UNKNOWN"


def _message_payload(row) -> dict[str, object]:
    return {
        "message_id": row.message_id,
        "created_at": row.created_at,
        "time": row.created_at,
        "type": row.type,
        "severity": row.severity.value,
        "title": row.title,
        "body": row.body,
        "source": row.source,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "is_read": row.is_read,
        "read_at": row.read_at,
        "metadata": row.metadata,
    }


def _research_summary_payload(row) -> dict[str, object]:
    return {
        "research_id": row.research_id,
        "status": row.status,
        "set_id": row.set_id,
        "set_version": row.set_version,
        "rules_version_id": row.rules_version_id,
        "rules_display_version": row.rules_display_version,
        "selected_backtest_profit_factor": row.selected_backtest_profit_factor,
        "selected_backtest_trades": row.selected_backtest_trades,
        "selected_demo_profit_factor": row.selected_demo_profit_factor,
        "selected_demo_trades": row.selected_demo_trades,
        "compare_to_active": row.compare_to_active,
        "selected_backtest_run_id": row.selected_backtest_run_id,
        "selected_demo_run_id": row.selected_demo_run_id,
        "decision": row.decision,
        "updated_at": row.updated_at,
    }


def _research_record_payload(record) -> dict[str, object]:
    return {
        "research_id": record.research_id,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "status": record.status.value,
        "set_id": record.set_id,
        "set_version": record.set_version,
        "rules_version_id": record.rules_version_id,
        "rules_display_version": record.rules_display_version,
        "selected_backtest_run_id": record.selected_backtest_run_id,
        "selected_demo_run_id": record.selected_demo_run_id,
        "decision": record.decision.value,
        "decision_at": record.decision_at,
        "archived_at": record.archived_at,
        "made_active_at": record.made_active_at,
        "promoted_set_id": record.promoted_set_id,
        "promoted_set_version": record.promoted_set_version,
        "promoted_rules_version_id": record.promoted_rules_version_id,
        "previous_active_set_id": record.previous_active_set_id,
        "previous_active_set_version": record.previous_active_set_version,
        "previous_rules_version_id": record.previous_rules_version_id,
        "promotion_result_metadata": record.promotion_result_metadata,
        "created_source": record.created_source,
        "schema_version": record.schema_version,
    }


def _research_run_payload(record) -> dict[str, object]:
    payload = {
        "research_id": record.research_id,
        "run_id": record.run_id,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "status": record.status.value,
        "selected_for_use": record.selected_for_use,
        "metrics": record.metrics,
    }
    for name in (
        "period_start",
        "period_end",
        "timeframe",
        "engine_run_id",
        "unavailable_reason",
        "started_at",
        "stopped_at",
        "execution_scope_id",
        "account_scope",
        "blocked_reason",
    ):
        if hasattr(record, name):
            payload[name] = getattr(record, name)
    return payload


def _messages_payload_from_model(read_model: DashboardReadModel) -> dict[str, object]:
    db_path = getattr(read_model, "db_path", None) or getattr(read_model, "_db_path", None) or getattr(read_model, "path", None)
    if db_path is None:
        return {"available": False, "messages": (), "unread_count": None, "error": "message store unavailable"}
    try:
        store = MessageStore(db_path)
        return {
            "available": True,
            "messages": tuple(_message_payload(row) for row in store.list_messages(limit=50)),
            "unread_count": store.get_unread_message_count(),
        }
    except Exception as exc:  # noqa: BLE001 - UI must show unavailable, not fake empty state.
        return {"available": False, "messages": (), "unread_count": None, "error": _safe_public_error(exc)}


def create_server_from_env(
    process_env: dict[str, str] | None = None,
    *,
    env_file: str | Path = ".env",
) -> tuple[DashboardServer, Path]:
    env = merged_runtime_env(os.environ if process_env is None else process_env, env_file=env_file)
    _require_explicit_dashboard_persistence(env)
    research_config_registry = _research_config_registry_from_env(env)
    config, bootstrap = ensure_runtime_registry_for_env(env, version_registry=research_config_registry)
    host = env.get("TRIGGERTRADE_DASHBOARD_HOST", DEFAULT_HOST)
    port = int(env.get("TRIGGERTRADE_DASHBOARD_PORT", str(DEFAULT_PORT)))
    db_path = runtime_db_path(config, env)
    catalog_service = InstrumentCatalogService(store=InstrumentCatalogStore(db_path), client=BybitDemoClient(config=config.bybit))
    authorizer = operator_authorizer_from_env(db_path, env)
    promotion_governance = _promotion_governance_from_env(env)
    operator_actions = _operator_execution_bridge_from_env(env)
    rules_service = TradingRulesService(
        TradingRulesStore(db_path),
        symbol_validator=catalog_service.validate_symbol,
        version_registry=research_config_registry,
    )
    research_demo_handoff = _research_demo_handoff_from_env(env)
    server = create_server(
        host=host,
        port=port,
        db_path=db_path,
        trading_rules_service=rules_service,
        instrument_catalog_service=catalog_service,
        operator_authorizer=authorizer,
        operator_actions=operator_actions,
        promotion_governance_store=promotion_governance,
        research_demo_handoff=research_demo_handoff,
        research_config_registry=research_config_registry,
    )
    _require_production_postgres_configuration_path(
        env,
        research_config_registry=research_config_registry,
        research_demo_handoff=research_demo_handoff,
        server=server,
    )
    return server, bootstrap.db_path


def _require_explicit_dashboard_persistence(env: dict[str, str]) -> None:
    runtime_mode = str(env.get("TRIGGERTRADE_RUNTIME_MODE") or "").strip().lower()
    process_role = str(env.get("TRIGGERTRADE_PROCESS_ROLE") or env.get("TRIGGERTRADE_ROLE") or "").strip().lower().replace("_", "-")
    production_dashboard = runtime_mode == "production" or process_role in {"web", "api", "dashboard"}
    if not production_dashboard:
        return
    if str(env.get("TRIGGERTRADE_POSTGRES_DSN") or "").strip():
        return
    raise ConfigError("production web role requires TRIGGERTRADE_POSTGRES_DSN")


def _require_production_postgres_configuration_path(
    env: dict[str, str],
    *,
    research_config_registry,
    research_demo_handoff,
    server: DashboardServer,
) -> None:
    runtime_mode = str(env.get("TRIGGERTRADE_RUNTIME_MODE") or "").strip().lower()
    process_role = str(env.get("TRIGGERTRADE_PROCESS_ROLE") or env.get("TRIGGERTRADE_ROLE") or "").strip().lower().replace("_", "-")
    production_dashboard = runtime_mode == "production" or process_role in {"web", "api", "dashboard"}
    if not production_dashboard:
        return
    if research_config_registry is None:
        raise ConfigError("production web role requires PostgreSQL Research configuration registry")
    research_service = server.research_service
    if getattr(research_service, "_research_config_registry", None) is not research_config_registry:
        raise ConfigError("production Research writes are not wired to PostgreSQL configuration registry")
    trigger_set_store = getattr(research_service, "_trigger_set_store", None)
    if getattr(trigger_set_store, "_version_registry", None) is not research_config_registry:
        raise ConfigError("production Trigger Set writes are not wired to PostgreSQL configuration registry")
    rules_service = server.trading_rules_service
    if getattr(rules_service, "_version_registry", None) is not research_config_registry:
        raise ConfigError("production Trading Rules writes are not wired to PostgreSQL configuration registry")
    if _env_true(env.get("TRIGGERTRADE_RESEARCH_DEMO_HANDOFF_ENABLED")) and research_demo_handoff is None:
        raise ConfigError("production Research Demo handoff is enabled but PostgreSQL handoff is unavailable")


def _env_true(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _promotion_governance_from_env(env: dict[str, str]):
    if not env.get("TRIGGERTRADE_POSTGRES_DSN"):
        return None
    settings = PostgresSettings.from_env(env)
    apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
    return ResearchPromotionGovernanceClient(
        PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
    )


def _operator_execution_bridge_from_env(env: dict[str, str]):
    if not env.get("TRIGGERTRADE_POSTGRES_DSN"):
        return None
    settings = PostgresSettings.from_env(env)
    apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
    return DashboardOperatorExecutionBridge(
        factory=PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
    )


def _research_config_registry_from_env(env: dict[str, str]):
    if not env.get("TRIGGERTRADE_POSTGRES_DSN"):
        return None
    settings = PostgresSettings.from_env(env)
    apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
    return PostgresResearchConfigurationRegistryClient(
        PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
    )


def _research_demo_handoff_from_env(env: dict[str, str]):
    if not env.get("TRIGGERTRADE_POSTGRES_DSN"):
        return None
    if not _env_true(env.get("TRIGGERTRADE_RESEARCH_DEMO_HANDOFF_ENABLED")):
        return None
    settings = PostgresSettings.from_env(env)
    apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
    return PostgresResearchDemoExecutionHandoff(
        factory=PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
    )


def main() -> int:
    server, db_path = create_server_from_env(os.environ)
    host, port = server.server_address
    print(f"TriggerTrade dashboard: http://{host}:{port}/")
    print(f"TriggerTrade registry DB: {db_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def _catalog_state_payload(read_model: DashboardReadModel) -> dict[str, object]:
    state = read_model.get_rules_catalog_state()
    return {
        "status": state.status,
        "updated_at": state.updated_at,
        "is_stale": state.is_stale,
        "tradeable_count": state.tradeable_count,
        "error": state.error,
    }


def _readiness_report(server: DashboardServer):
    return evaluate_dashboard_readiness(
        server.read_model,
        env=server.readiness_env,
        postgres_probe=server.postgres_health_probe,
        postgres_runtime_probe=server.postgres_runtime_probe,
        postgres_registry_probe=server.postgres_registry_probe,
        execution_bridge=server.operator_actions,
    )


def _readiness_payload(server: DashboardServer) -> dict[str, object]:
    return _readiness_report(server).to_payload()


def _rules_changes_from_payload(payload: dict) -> dict[str, object]:
    position = payload.get("position_rules")
    portfolio = payload.get("portfolio_rules")
    coins = payload.get("coins")
    if not isinstance(position, dict) or not isinstance(portfolio, dict) or not isinstance(coins, list):
        raise TradingRulesError("rules payload is incomplete")
    return {
        "position_size_pct": _pct_to_fraction(position.get("position_size_pct")),
        "take_profit_mode": str(position.get("take_profit_mode") or "").upper(),
        "fixed_take_profit_pct": _optional_pct_to_fraction(position.get("fixed_take_profit_pct")),
        "minimum_take_profit_pct": _optional_pct_to_fraction(position.get("minimum_take_profit_pct")),
        "stop_loss_pct": _pct_to_fraction(position.get("stop_loss_pct")),
        "minimum_risk_reward": _decimal_value(position.get("minimum_risk_reward")),
        "minimum_net_edge_enabled": _bool_value(position.get("minimum_net_edge_enabled")),
        "minimum_net_edge_pct": _optional_pct_to_fraction(position.get("minimum_net_edge_pct")),
        "leverage": _decimal_value(position.get("leverage")),
        "max_capital_in_positions_pct": _pct_to_fraction(portfolio.get("max_capital_in_positions_pct")),
        "max_open_positions_enabled": _bool_value(portfolio.get("max_open_positions_enabled")),
        "max_open_positions": _optional_int(portfolio.get("max_open_positions")),
        "max_positions_per_coin_enabled": _bool_value(portfolio.get("max_positions_per_coin_enabled")),
        "max_positions_per_coin": _optional_int(portfolio.get("max_positions_per_coin")),
        "direction_mode": str(portfolio.get("direction_mode") or "").upper(),
        "daily_loss_limit_enabled": _bool_value(portfolio.get("daily_loss_limit_enabled")),
        "daily_loss_limit_pct": _optional_pct_to_fraction(portfolio.get("daily_loss_limit_pct")),
        "coins": tuple(_coin_rule_from_payload(item) for item in coins),
    }


def _coin_rule_from_payload(item: object) -> CoinRule:
    if not isinstance(item, dict):
        raise TradingRulesError("coin rules must be objects")
    return CoinRule(
        symbol=str(item.get("symbol") or ""),
        enabled=_bool_value(item.get("enabled")),
        max_allocation_pct=_optional_pct_to_fraction(item.get("max_allocation_pct")),
    )


def _pct_to_fraction(value: object) -> Decimal:
    parsed = _decimal_value(value)
    return parsed / Decimal("100")


def _optional_pct_to_fraction(value: object) -> Decimal | None:
    if value in {None, ""}:
        return None
    return _pct_to_fraction(value)


def _decimal_value(value: object) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise TradingRulesError("numeric rules fields must be valid decimals") from exc
    if not parsed.is_finite():
        raise TradingRulesError("numeric rules fields must be finite decimals")
    return parsed


def _finite_decimal(value: object) -> Decimal:
    return _decimal_value(value)


def _optional_int(value: object) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(str(value))
    except ValueError as exc:
        raise TradingRulesError("integer rules fields must be valid integers") from exc


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    raise TradingRulesError("enabled flags require explicit boolean values")


def _backtest_plan_from_payload(payload: dict) -> BacktestPlan:
    start = _iso_datetime(str(payload.get("research_start") or payload.get("start") or ""))
    end = _iso_datetime(str(payload.get("research_end") or payload.get("end") or ""))
    return BacktestPlan(
        symbol=str(payload.get("symbol") or "BTCUSDT").upper(),
        category=str(payload.get("category") or "linear").lower(),
        timeframe=str(payload.get("timeframe") or "1m"),
        research_start=start,
        research_end=end,
        warmup_candles=int(payload.get("warmup_candles") or 60),
    )


def _iso_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("invalid datetime") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _safe_public_error(exc: Exception) -> str:
    text = str(exc)
    lower = text.lower()
    if any(token in lower for token in ("secret", "api_key", "authorization", "x-bapi", "password", "token")):
        return exc.__class__.__name__
    return text[:240]

def _operator_controls(state, token: str = "") -> str:
    if state is None:
        state = type("OperatorState", (), {"state": "TRADING_ENABLED"})()
    token_input = f"<input type='hidden' name='token' value='{_h(token)}'>"
    if state.state == "TRADING_PAUSED":
        return (
            "<form method='post' action='/operator/resume' onsubmit=\"return confirmResumeTrading()\">"
            "<input type='hidden' name='confirm' value='yes'>"
            f"{token_input}"
            "<button class='utility-btn resume-btn' type='submit'>RESUME</button>"
            "</form><span class='badge amber'>PAUSED</span>"
        )
    return (
        "<form method='post' action='/operator/pause' onsubmit=\"return confirmPauseEntries()\">"
        "<input type='hidden' name='confirm' value='yes'>"
        f"{token_input}"
        "<button class='utility-btn stop-btn' type='submit'>Pause Entries</button>"
        "</form><span class='badge green'>ENABLED</span>"
    )


def _closed_trades_panel(rows, is_live: bool) -> str:
    lane = "LIVE" if is_live else "TEST"
    source_label = "ACTIVE Demo futures trades" if is_live else "TEST simulated futures trades"
    empty = "No completed Demo futures trades yet." if is_live else "No TEST simulated trades yet."
    body = "".join(
        f"<tr><td><a class='linkbtn mono' href='/trades/{_h(row.trade_id)}'>{_h(_short(row.trade_id))}</a></td><td class='mono'>{_h(_compact(row.closed_at))}</td><td>{_h(row.symbol)}</td><td><span class='badge blue'>{_h(row.direction)}</span></td><td>{_h(row.entry_vwap)}</td><td>{_h(row.exit_vwap)}</td><td>{_h(row.quantity)}</td><td>{_h(row.leverage)}x</td><td>{_h(str(row.duration_seconds))}s</td><td>{_h(row.gross_pnl)}</td><td>{_h(row.fees)}</td><td>{_h(row.funding)}</td><td>{_h(row.entry_slippage)} / {_h(row.exit_slippage)}</td><td>{_h(row.net_pnl)}</td><td>{_h(row.trigger_set)}</td><td>{_h(row.regime)}</td><td>{_h(row.accounting_version)}</td></tr>"
        for row in rows
    ) or f"<tr><td colspan='17' class='muted'>{empty} Performance metrics will appear after backend accounting records closed trades.</td></tr>"
    mobile = "".join(
        f"<div class='mcard'><div class='mhead'><div><div class='mtitle'>{_h(row.symbol)} {_h(row.direction)}</div><div class='msub mono'>{_h(_compact(row.closed_at))}</div></div><span class='badge {'live' if is_live else 'test'}'>{lane}</span></div><div class='mgrid'><div><div class='fl'>Entry</div><div class='fv'>{_h(row.entry_vwap)}</div></div><div><div class='fl'>Exit</div><div class='fv'>{_h(row.exit_vwap)}</div></div><div><div class='fl'>Net P&L</div><div class='fv'>{_h(row.net_pnl)}</div></div><div><div class='fl'>Source</div><div class='fv'>{_h(row.evidence_source)}</div></div></div></div>"
        for row in rows
    ) or f"<div class='mcard'><div class='mtitle'>{empty}</div><div class='msub'>{source_label}; no fake financial rows are rendered.</div></div>"
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>{lane} Trades</div><div class='panel-meta'>{source_label}; accounting-backed only.</div></div><div class='panel-actions'><button class='button' onclick=\"openFullList('trades')\">View all</button></div></div><div class='table-wrap desktop-table'><table><thead><tr><th>Trade ID</th><th>Date</th><th>Asset</th><th>Direction</th><th>Entry</th><th>Exit</th><th>Size</th><th>Lev</th><th>Duration</th><th>Gross P&amp;L</th><th>Fees</th><th>Funding</th><th>Slippage</th><th>Net P&amp;L</th><th>Set</th><th>Regime</th><th>Status</th></tr></thead><tbody>{body}</tbody></table></div><div class='mobile-list'>{mobile}</div></div>"


def _open_futures_orders_panel(rows) -> str:
    body = "".join(
        f"<tr><td class='mono'>{_h(_short(row.execution_id))}</td><td class='mono'>{_h(_compact(row.time))}</td><td>{_h(row.symbol)}</td><td>{_h(row.category)}</td><td><span class='badge blue'>{_h(row.action)}</span></td><td>{_h(row.exchange_side)}</td><td>{_h(row.quantity)}</td><td>{_h(row.requested_price)}</td><td>{_h(row.leverage)}x</td><td>{_h(row.expected_net_edge)}</td><td>{_h(row.status)}</td></tr>"
        for row in rows
    ) or "<tr><td colspan='11' class='muted'>No active Bybit Demo futures execution records yet.</td></tr>"
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>ACTIVE Futures Execution</div><div class='panel-meta'>Bybit Demo linear perpetual order lifecycle records; read-only.</div></div></div><div class='table-wrap analytics-compact'><table><thead><tr><th>Order</th><th>Updated</th><th>Symbol</th><th>Category</th><th>Action</th><th>Exchange side</th><th>Qty</th><th>Limit</th><th>Lev</th><th>Expected net edge</th><th>Status</th></tr></thead><tbody>{body}</tbody></table></div></div>"


def _positions_panel(position, is_live: bool) -> str:
    lane = "LIVE" if is_live else "TEST"
    if position is None:
        position = type("Position", (), {"state":"Not available","symbol":"BTCUSDT","direction":"Not available","quantity":"-","entry":"-","mark":"-","leverage":"-","liquidation":"Not available","take_profit":"Not configured","stop_loss":"Not configured","notional":"-","unrealized_pnl":"unavailable","trigger_set":"-","regime":"unavailable","opened_at":"-","source":"no authoritative backend position snapshot"})()
    body = (
        f"<tr><td>{_h(position.symbol)}</td><td><span class='badge gray'>{_h(position.direction)}</span></td><td>{_h(position.quantity)}</td><td>{_h(position.entry)}</td><td>{_h(position.mark)}</td><td>{_h(position.leverage)}</td><td>{_h(position.liquidation)}</td><td>{_h(position.take_profit)}</td><td>{_h(position.stop_loss)}</td><td>{_h(position.notional)}</td><td>{_h(position.unrealized_pnl)}</td><td>{_h(position.trigger_set)}</td><td>{_h(position.regime)}</td><td>{_h(position.opened_at)}</td></tr>"
    )
    mobile = f"<div class='mcard'><div class='mhead'><div><div class='mtitle'>{_h(position.symbol)} position</div><div class='msub'>{_h(position.source)}</div></div><span class='badge {'live' if is_live else 'test'}'>{lane}</span></div><div class='mgrid'><div><div class='fl'>Direction</div><div class='fv'>{_h(position.direction)}</div></div><div><div class='fl'>Leverage</div><div class='fv'>{_h(position.leverage)}</div></div><div><div class='fl'>Entry / Mark</div><div class='fv'>{_h(position.entry)} / {_h(position.mark)}</div></div><div><div class='fl'>TP / SL</div><div class='fv'>{_h(position.take_profit)} / {_h(position.stop_loss)}</div></div></div></div>"
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>Current Futures Position</div><div class='panel-meta'>{_h(position.source)}; dashboard does not infer positions from intents.</div></div>{_status_badge(position.state)}</div><div class='table-wrap desktop-table'><table><thead><tr><th>Asset</th><th>Direction</th><th>Qty</th><th>Entry</th><th>Mark</th><th>Leverage</th><th>Liquidation</th><th>Take Profit</th><th>Stop Loss</th><th>Notional</th><th>Unrealized P&amp;L</th><th>Trigger Set</th><th>Regime</th><th>Opened</th></tr></thead><tbody>{body}</tbody></table></div><div class='mobile-list'>{mobile}</div></div>"
def _trace_panel(trace, is_live: bool) -> str:
    label = "LIVE" if is_live else "TEST"
    badge = "live" if is_live else "test"
    if trace is None:
        body = "<div class='activity-row'><div class='mono muted'>-</div><div>No lane trace recorded yet.</div><span class='badge gray'>EMPTY</span></div>"
    else:
        lifecycle = trace.lifecycle or {}
        trigger = trace.trigger or {}
        strategy = trace.strategy or {}
        risk = trace.risk or {}
        execution = trace.execution or {}
        regime = trace.regime or {}
        body = "".join(
            [
                _trace_row("Market", lifecycle.get("candle_id", trace.candle_id), lifecycle.get("candle_open_time", "-")),
                _trace_row("Regime", regime.get("rule_id", "none"), regime.get("label", lifecycle.get("regime_state", "none"))),
                _trace_row("Trigger", trigger.get("trigger_rule_id", "none"), trigger.get("signal_type", lifecycle.get("status", "-"))),
                _trace_row("Signal", (trace.signal or {}).get("signal_id", "none") if trace.signal else "none", trigger.get("condition_result", "-")),
                _trace_row("Strategy", strategy.get("strategy_rule_id", "not evaluated"), strategy.get("intent_id", "none")),
                _trace_row("Risk", risk.get("risk_decision_id", "not evaluated"), _risk_label(risk)),
                _trace_row("Execution", execution.get("intent_id", "none"), execution.get("status", "none")),
            ]
        )
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>Full Trace</div><div class='panel-meta'>Latest {label} lifecycle, read-only</div></div><span class='badge {badge}'>{label}</span></div><div class='activity'>{body}</div></div>"


def _trace_row(stage: str, primary, secondary) -> str:
    return f"<div class='activity-row'><div class='mono muted'>{_h(stage)}</div><div><div class='mono'>{_h(str(primary))}</div><div class='muted'>{_h(str(secondary))}</div></div><span class='badge gray'>trace</span></div>"


def _risk_label(risk: dict) -> str:
    if not risk:
        return "none"
    if risk.get("approved"):
        return "APPROVED"
    blocking = risk.get("blocking_rule_ids") or []
    if isinstance(blocking, list) and blocking:
        return "REJECTED: " + ", ".join(str(item) for item in blocking)
    return "REJECTED"

def _trigger_sets_panel(rows) -> str:
    body = "".join(
        f"<tr data-status='{_h(row.status.lower())}'><td><button class='linkbtn' onclick=\"openSet('{_h(row.set_id)}::{_h(row.version)}')\">{_h(row.version)}</button></td><td>{_h(row.purpose)}</td><td>{row.rules_count}</td><td>{_h(_compact(row.created_at))}</td><td>{_status_badge(row.status)}</td></tr>"
        for row in rows
    ) or "<tr><td colspan='5' class='muted'>No Trigger Sets registered yet.</td></tr>"
    mobile = "".join(
        f"<div class='mcard' data-status='{_h(row.status.lower())}'><div class='mhead'><div><div class='mtitle'><button class='linkbtn' onclick=\"openSet('{_h(row.set_id)}::{_h(row.version)}')\">{_h(row.version)}</button></div><div class='msub'>{_h(row.purpose)}</div></div>{_status_badge(row.status)}</div><div class='mgrid'><div><div class='fl'>Rules</div><div class='fv'>{row.rules_count}</div></div><div><div class='fl'>Created</div><div class='fv'>{_h(_compact(row.created_at))}</div></div></div></div>"
        for row in rows
    )
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>Trigger sets</div><div class='panel-meta'>Versions of the full condition set used for execution</div></div><div class='filters'><select id='setStatusFilter' onchange='filterSets()'><option value='all'>All</option><option value='active'>Active</option><option value='testing'>Testing</option><option value='archive'>Archive</option><option value='draft'>Draft</option></select></div></div><div class='table-wrap'><table id='setsTable'><thead><tr><th>Set</th><th>Purpose</th><th>Rules</th><th>Created</th><th>Status</th></tr></thead><tbody>{body}</tbody></table></div><div class='mobile-list' id='setsMobile'>{mobile}</div></div>"


def _rules_panel(rows) -> str:
    body = "".join(
        f"<tr data-status='{_h(row.status.lower())}'><td><a class='linkbtn' href='/rules/{_h(row.rule_id)}'>{_h(row.name)}</a><div class='mono muted'>{_h(row.rule_id)}</div></td><td>{_h(row.asset_scope)}</td><td>{_h(row.condition)}</td><td>{_h(row.used_in)}</td><td><a class='linkbtn' href='/rules/{_h(row.rule_id)}/{_h(row.version)}'>{_h(row.version)}</a></td><td>{_status_badge(row.status)}</td></tr>"
        for row in rows
    ) or "<tr><td colspan='6' class='muted'>No rule registry records yet.</td></tr>"
    return f"<div class='filters' style='margin-bottom:12px'><input class='search' id='ruleSearch' placeholder='Search rules...' oninput='filterRules()'><select id='statusFilter' onchange='filterRules()'><option value='all'>All statuses</option><option value='active'>Active</option><option value='testing'>Testing</option><option value='draft'>Draft</option><option value='archive'>Archive</option></select><button class='button dark' disabled title='Read-only dashboard'>+ New rule</button></div><div class='panel'><div class='panel-head'><div><div class='panel-title'>Rule registry</div></div></div><div class='table-wrap'><table id='rulesTable'><thead><tr><th>Rule</th><th>Asset</th><th>Condition</th><th>Used in</th><th>Version</th><th>Status</th></tr></thead><tbody>{body}</tbody></table></div><div class='mobile-list' id='rulesMobile'></div></div>"


def render_rule_detail(detail) -> str:
    rule = detail.rule
    definition = rule.get("definition") or {}
    return _page(
        f"{rule.get('rule_id')} {rule.get('version')}",
        f"""
<div class="app"><main class="main"><div class="toolbar"><div class="container toolbar-inner"><a class="brand-top" href="/">TriggerTrade</a><div class="utility-actions"><a class="utility-btn" href="/portfolio">Portfolio</a></div></div></div>
<div class="tabsbar"><div class="container tabsbar-inner"><div class="tabs"><a class="tabbtn active" href="/rules/{_h(rule.get('rule_id'))}/{_h(rule.get('version'))}">Rule Detail</a><a class="tabbtn" href="/trigger-catalog">Trigger Catalog</a></div></div></div>
<div class="content container">
  <section class="panel"><div class="panel-head"><div><div class="panel-title">{_h(rule.get('name'))}</div><div class="panel-meta mono">{_h(rule.get('rule_id'))} @ {_h(rule.get('version'))}</div></div>{_status_badge(str(rule.get('status')))}</div><div class="section"><div class="set-detail">{_kv('Rule ID', rule.get('rule_id'))}{_kv('Version', rule.get('version'))}{_kv('Type', rule.get('rule_type'))}{_kv('Scope', rule.get('asset_scope'))}{_kv('Created', _compact(rule.get('created_at')))}{_kv('Provenance', rule.get('provenance'))}</div></div></section>
  {_definition_panel('Purpose', rule.get('condition'))}
  {_definition_panel('Technical Definition', definition)}
  {_definition_panel('Formula', definition.get('relative_volume') or definition.get('condition') or rule.get('condition'))}
  {_definition_panel('Inputs', definition.get('lookback') or definition.get('volume_unit') or definition)}
  {_definition_panel('Parameters / Thresholds', {k:v for k,v in definition.items() if 'threshold' in k or 'lookback' in k or k in {'boundary','median','percentile_rank'}})}
  {_definition_panel('Boundary / Missing / Stale Behavior', {k:v for k,v in definition.items() if k in {'boundary','missing_data','stale_data'}})}
  {_used_in_panel(detail.used_in_sets)}
  {_version_history_panel(detail.versions)}
  {_rule_recommendations_panel(detail.recommendations)}
</div></main></div>
""",
    )


def render_trade_detail(detail: dict) -> str:
    fills = detail.get("fills") or ()
    fill_rows = "".join(
        f"<tr><td class='mono'>{_h(_short(row.get('event_id')))}</td><td>{_h(row.get('action'))}</td><td>{_h(row.get('quantity'))}</td><td>{_h(row.get('price'))}</td><td>{_h(row.get('fee'))} {_h(row.get('fee_asset'))}</td><td>{_h(_compact(row.get('occurred_at')))}</td><td>{_h(row.get('source'))}</td></tr>"
        for row in fills
    ) or "<tr><td colspan='7' class='muted'>No fills recorded for this trade.</td></tr>"
    return _page(
        f"Trade {_short(detail.get('trade_id'))}",
        f"""
<div class="app"><main class="main"><div class="toolbar"><div class="container toolbar-inner"><a class="brand-top" href="/">TriggerTrade</a><div class="utility-actions"><a class="utility-btn" href="/portfolio">Portfolio</a><a class="utility-btn" href="/research">Research</a></div></div></div>
<div class="tabsbar"><div class="container tabsbar-inner"><div class="tabs"><a class="tabbtn active" href="/trades/{_h(detail.get('trade_id'))}">Trade Detail</a><a class="tabbtn" href="/portfolio">Portfolio</a></div></div></div>
<div class="content container">
  <section class="panel"><div class="panel-head"><div><div class="panel-title">{_h(detail.get('symbol'))} {_h(detail.get('direction'))}</div><div class="panel-meta mono">{_h(detail.get('trade_id'))}</div></div>{_status_badge(detail.get('evidence_source') or 'unknown')}</div><div class="section"><div class="set-detail">{_kv('Opened', _compact(detail.get('opened_at')))}{_kv('Closed', _compact(detail.get('closed_at')))}{_kv('Duration', str(detail.get('duration_seconds')) + 's')}{_kv('Quantity', detail.get('quantity'))}{_kv('Leverage', str(detail.get('leverage')) + 'x')}{_kv('Trigger Set', detail.get('trigger_set'))}{_kv('Regime', detail.get('regime_label') or 'unavailable')}{_kv('Simulation model', detail.get('simulation_model_version') or '-')}</div></div></section>
  <section class="panel"><div class="panel-head"><div><div class="panel-title">Accounting</div><div class="panel-meta">Backend accounting facts only; no frontend P&amp;L calculations.</div></div></div><div class="section"><div class="set-detail">{_kv('Entry VWAP', detail.get('entry_vwap'))}{_kv('Exit VWAP', detail.get('exit_vwap'))}{_kv('Gross P&L', detail.get('gross_pnl'))}{_kv('Fees', detail.get('fees'))}{_kv('Funding', detail.get('funding'))}{_kv('Net P&L', detail.get('net_pnl'))}{_kv('Entry slippage', detail.get('entry_slippage_cost') or 'unavailable')}{_kv('Exit slippage', detail.get('exit_slippage_cost') or 'unavailable')}{_kv('Accounting version', detail.get('accounting_version'))}</div></div></section>
  <section class="panel"><div class="panel-head"><div><div class="panel-title">Execution Fills</div><div class="panel-meta">Immutable execution facts feeding accounting.</div></div></div><div class="table-wrap"><table><thead><tr><th>Fill</th><th>Action</th><th>Qty</th><th>Price</th><th>Fee</th><th>Time</th><th>Source</th></tr></thead><tbody>{fill_rows}</tbody></table></div></section>
  <section class="panel"><div class="panel-head"><div><div class="panel-title">Decision Context</div><div class="panel-meta">Traceable persisted attribution; unavailable fields are not inferred.</div></div></div><div class="activity">{_trace_row('Lane / source', detail.get('evidence_source'), 'ACTIVE exchange or TEST simulation')}{_trace_row('Trigger Set', detail.get('trigger_set'), 'exact set version')}{_trace_row('Market Regime', detail.get('regime_label') or 'unavailable', 'CTX-REGIME@0.1.0 when captured')}{_trace_row('Why opened', 'persisted strategy/risk trace', 'open reason available in lifecycle trace when recorded')}{_trace_row('Why closed', 'unavailable', 'close strategy is not implemented in this UI task')}</div></section>
</div></main></div>
""",
    )

def render_recommendation_detail(detail) -> str:
    rec = detail.recommendation
    linked = "-" if detail.linked_set is None else f"{detail.linked_set.set_id}@{detail.linked_set.version}"
    return _page(
        str(rec.get("title", "Recommendation")),
        f"""
<div class="app"><main class="main"><div class="toolbar"><div class="container toolbar-inner"><a class="brand-top" href="/">TriggerTrade</a><div class="utility-actions"><a class="utility-btn" href="/research">Research</a></div></div></div>
<div class="tabsbar"><div class="container tabsbar-inner"><div class="tabs"><a class="tabbtn active" href="/recommendations/{_h(rec.get('recommendation_id'))}">Recommendation</a><a class="tabbtn" href="/portfolio">Portfolio</a></div></div></div>
<div class="content container">
  <section class="panel"><div class="panel-head"><div><div class="panel-title">{_h(rec.get('title'))}</div><div class="panel-meta mono">{_h(rec.get('recommendation_id'))}</div></div>{_status_badge(str(rec.get('status')))}</div><div class="section"><div class="set-detail">{_kv('Created', _compact(rec.get('created_at')))}{_kv('Resulting test set', linked)}{_kv('Decision', rec.get('decision') or '-')}</div></div></section>
  {_definition_panel('Observation', rec.get('observation'))}
  {_definition_panel('Evidence', rec.get('evidence'))}
  {_definition_panel('Hypothesis', rec.get('hypothesis'))}
  {_definition_panel('Recommended Experiment', rec.get('recommended_experiment'))}
  {_definition_panel('Proposed Rule Version', rec.get('proposed_rule_changes'))}
  {_definition_panel('Proposed Trigger Set', rec.get('proposed_trigger_set_definition'))}
  {_definition_panel('Test Requirements', {'minimum_test_duration': rec.get('minimum_test_duration'), 'minimum_sample_size': rec.get('minimum_sample_size')})}
  {_definition_panel('Evaluation', rec.get('evaluation_summary') or 'Pending Demo evidence.')}
</div></main></div>
""",
    )


def render_backtest_detail(detail: dict) -> str:
    run = detail.get("run") or {}
    result = detail.get("result") or {}
    rules = ", ".join("@".join(item) for item in run.get("rule_versions", ()))
    return _page(
        f"Backtest {_short(detail.get('run_id'))}",
        f"""
<div class="app"><main class="main"><div class="toolbar"><div class="container toolbar-inner"><a class="brand-top" href="/">TriggerTrade</a><div class="utility-actions"><a class="utility-btn" href="/research">Research</a></div></div></div>
<div class="tabsbar"><div class="container tabsbar-inner"><div class="tabs"><a class="tabbtn active" href="/backtests/{_h(detail.get('run_id'))}">Backtest Detail</a><a class="tabbtn" href="/research">Research</a></div></div></div>
<div class="content container">
  <section class="panel"><div class="panel-head"><div><div class="panel-title">Historical Replay Detail</div><div class="panel-meta">Read-only BACKTEST evidence; no private/order API calls and no auto-promotion.</div></div>{_status_badge(str(detail.get('status', 'UNKNOWN')))}</div><div class="section"><div class="set-detail">{_kv('Run', detail.get('run_id'))}{_kv('Set', str(run.get('trigger_set_id', '-')) + '@' + str(run.get('trigger_set_version', '-')))}{_kv('Period', str(run.get('period_start', '-')) + ' -> ' + str(run.get('period_end', '-')))}{_kv('Warmup', str(run.get('warmup_start', '-')) + ' -> ' + str(run.get('evaluation_start', '-')))}{_kv('Rules', rules)}{_kv('Strategy', run.get('strategy_version'))}{_kv('Regime', run.get('regime_version'))}{_kv('Risk', run.get('risk_profile_version'))}{_kv('Simulator', run.get('simulation_model_version'))}{_kv('Cost model', run.get('cost_model_version'))}{_kv('Funding model', run.get('funding_model_version'))}{_kv('Accounting', run.get('accounting_version'))}{_kv('Data source', run.get('data_source_version'))}{_kv('Cache hash', run.get('data_cache_hash'))}{_kv('No-lookahead', 'decision after candle t; earliest fill on candle t+1')}</div></div></section>
  <section class="panel"><div class="panel-head"><div><div class="panel-title">Result Summary</div><div class="panel-meta">Backend replay/accounting/performance facts only.</div></div></div><div class="section"><div class="set-detail">{_kv('Candles processed', result.get('candles_processed'))}{_kv('Signals', result.get('signals'))}{_kv('Intents', result.get('intents'))}{_kv('Closed trades', result.get('closed_trades'))}{_kv('Net P&L', result.get('net_pnl'))}{_kv('Expectancy', result.get('expectancy'))}{_kv('Profit factor', result.get('profit_factor'))}{_kv('Fees', result.get('fees'))}{_kv('Funding', result.get('funding'))}{_kv('LONG / SHORT', str(result.get('long_trades', 0)) + ' / ' + str(result.get('short_trades', 0)))}{_kv('Technical failures', result.get('technical_failures'))}</div></div></section>
</div></main></div>
""",
    )


def _historical_tests_panel(rows) -> str:
    body = "".join(
        f"<tr><td><a class='linkbtn mono' href='/backtests/{_h(row.run_id)}'>{_h(_short(row.run_id))}</a></td><td>{_h(row.trigger_set)}</td><td>{_h(row.period)}</td><td>{_status_badge(row.stage)}</td><td>{_h(row.simulation_model)}</td><td>{_status_badge(row.status)}</td><td>{_h(row.closed_trades)}</td><td>{_h(row.net_pnl)}</td><td>{_h(row.expectancy)}</td><td>{_h(row.profit_factor)}</td><td>{_h(row.max_drawdown)}</td><td>{_h(_compact(row.created_at))}</td></tr>"
        for row in rows
    ) or "<tr><td colspan='12' class='muted'>No historical BACKTEST runs recorded yet.</td></tr>"
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>Historical Tests</div><div class='panel-meta'>Exact Trigger Set replay evidence; BACKTEST is separate from forward TEST and Demo execution.</div></div></div><div class='table-wrap analytics-compact'><table><thead><tr><th>Backtest Run</th><th>Set</th><th>Period</th><th>Stage</th><th>Simulation</th><th>Status</th><th>Trades</th><th>Net P&amp;L</th><th>Expectancy</th><th>PF</th><th>Max DD</th><th>Created</th></tr></thead><tbody>{body}</tbody></table></div></div>"


def _performance_panel(rows) -> str:
    body = "".join(
        f"<tr><td><button class='linkbtn' onclick=\"toggleEvidence('perf::{_h(row.set_id)}::{_h(row.version)}')\">{_h(row.version)}</button><div class='mono muted'>{_h(row.set_id)}</div></td><td>{_status_badge(row.status)}</td><td>{_h(row.period)}</td><td>{row.signals}</td><td>{row.closed_trades}</td><td>{_h(row.win_rate)}</td><td>{_h(row.expectancy)}</td><td>{_h(row.profit_factor)}</td><td>{_h(row.net_pnl)}</td><td>{_h(row.max_drawdown)}</td><td>{_h(row.fees_gross_profit_pct)}</td><td>{_status_badge(row.readiness)}</td><td>{_h(row.recommendation)}</td></tr>"
        f"<tr class='evidence-detail' data-evidence='perf::{_h(row.set_id)}::{_h(row.version)}'><td colspan='13'><div class='set-detail'><div><div class='fl'>Runtime counts</div><div class='fv'>{row.candles_processed} candles; {row.candidate_intents} intents; {row.test_executions} test records</div></div><div><div class='fl'>Fees / funding</div><div class='fv'>fees {_h(row.fees)}; funding {_h(row.funding)}</div></div><div><div class='fl'>Quality warnings</div><div class='fv'>{_h('; '.join(row.warnings) or row.unavailable_metrics)}</div></div><div><div class='fl'>Grouping</div><div class='fv'>Trigger Set Version is the performance unit; rule-level views are diagnostic only.</div></div></div></td></tr>"
        for row in rows
    ) or "<tr><td colspan='13' class='muted'>No set-level runtime evidence recorded yet. No accounting sample is fabricated.</td></tr>"
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>Performance</div><div class='panel-meta'>Trigger Set Version performance from backend accounting facts; no frontend financial calculations.</div></div></div><div class='table-wrap analytics-compact'><table><thead><tr><th>Set</th><th>Status</th><th>Period</th><th>Signals</th><th>Closed trades</th><th>Win rate</th><th>Expectancy</th><th>Profit factor</th><th>Net P&amp;L</th><th>Max DD</th><th>Fees/Gross Profit</th><th>Readiness</th><th>Recommendation</th></tr></thead><tbody>{body}</tbody></table></div></div>"


def _baseline_comparison_panel(rows) -> str:
    body = "".join(
        f"<tr><td class='mono'>{_h(row.candidate_set)}</td><td class='mono'>{_h(row.baseline_set)}</td><td>{_status_badge('AVAILABLE' if row.available else 'UNAVAILABLE')}</td><td>{_h(row.period)}</td><td>{row.candidate_closed_trades} / {row.baseline_closed_trades}</td><td>{_h(row.candidate_net_pnl)} / {_h(row.baseline_net_pnl)}</td><td>{_h(row.candidate_expectancy)} / {_h(row.baseline_expectancy)}</td><td>{_h(row.candidate_fees)} / {_h(row.baseline_fees)}</td><td>{_h(row.candidate_direction_mix)} / {_h(row.baseline_direction_mix)}</td><td class='muted'>{_h(row.reason)}</td></tr>"
        for row in rows
    ) or "<tr><td colspan='10' class='muted'>No overlapping ACTIVE vs TESTING accounting comparison available yet.</td></tr>"
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>Baseline Comparison</div><div class='panel-meta'>TESTING sets compared with ACTIVE only over overlapping closed-trade periods.</div></div></div><div class='table-wrap analytics-compact'><table><thead><tr><th>Candidate</th><th>Baseline</th><th>Status</th><th>Overlap</th><th>Trades C/B</th><th>Net P&amp;L C/B</th><th>Expectancy C/B</th><th>Fees C/B</th><th>Direction mix C/B</th><th>Reason</th></tr></thead><tbody>{body}</tbody></table></div></div>"


def _regime_analytics_panel(rows) -> str:
    body = "".join(
        f"<tr><td>{_status_badge(row.regime)}</td><td>{row.signals}</td><td>{row.closed_trades}</td><td>{_h(row.net_pnl)}</td><td>{_h(row.expectancy)}</td><td>{_h(row.fees_gross_profit_pct)}</td><td>{row.long_trades}</td><td>{row.short_trades}</td></tr>"
        for row in rows
    ) or "<tr><td colspan='8' class='muted'>No accounting-backed or runtime signal regime evidence recorded yet.</td></tr>"
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>By Regime</div><div class='panel-meta'>Backend regime context diagnostics; no frontend classification or financial calculations.</div></div></div><div class='table-wrap analytics-compact'><table><thead><tr><th>Regime</th><th>Signals</th><th>Closed trades</th><th>Net P&amp;L</th><th>Expectancy</th><th>Fees/Gross Profit</th><th>LONG</th><th>SHORT</th></tr></thead><tbody>{body}</tbody></table></div></div>"


def _recommendations_panel(rows) -> str:
    body = "".join(
        f"<tr><td><a class='linkbtn' href='/recommendations/{_h(row.recommendation_id)}'>{_h(row.title)}</a><div class='mono muted'>{_h(row.recommendation_id)}</div></td><td>{_status_badge(row.status)}</td><td>{_h(_compact(row.created_at))}</td><td>{_h(row.resulting_test_set)}</td><td class='muted'>{_h(row.evidence)}</td></tr>"
        for row in rows
    ) or "<tr><td colspan='5' class='muted'>No recommendations registered yet.</td></tr>"
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>Recommendations</div><div class='panel-meta'>Observation, hypothesis and experiment proposals are separated; no automatic promotion.</div></div></div><div class='table-wrap'><table><thead><tr><th>Recommendation</th><th>Status</th><th>Created</th><th>Resulting set</th><th>Evidence</th></tr></thead><tbody>{body}</tbody></table></div></div>"


def _test_evidence_panel(rows) -> str:
    body = "".join(
        f"<tr><td><button class='linkbtn' onclick=\"toggleEvidence('{_h(row.set_id)}::{_h(row.version)}')\">{_h(row.version)}</button><div class='mono muted'>{_h(row.set_id)}</div></td><td>{_status_badge(row.status)}</td><td>{row.age_days}d</td><td>{row.signals_observed}</td><td>{_h(row.closed_trades_observed)}</td><td>{_h(row.regime_coverage)}</td><td>{_status_badge(row.readiness)}</td><td>{_h(row.recommendation_action)}</td></tr>"
        f"<tr class='evidence-detail' data-evidence='{_h(row.set_id)}::{_h(row.version)}'><td colspan='8'><div class='set-detail'><div><div class='fl'>Evidence collected</div><div class='fv'>{row.signals_observed} signals; closed trades {_h(row.closed_trades_observed)}</div></div><div><div class='fl'>Readiness gates</div><div class='fv'>{_h(row.policy)}</div></div><div><div class='fl'>Missing evidence</div><div class='fv'>{_h('; '.join(row.missing_evidence) or 'none')}</div></div><div><div class='fl'>Blocking reasons</div><div class='fv'>{_h('; '.join(row.blocking_reasons) or 'none')}</div></div><div><div class='fl'>Recommendation</div><div class='fv'>{_h(row.recommendation_action)}</div></div><div><div class='fl'>Comparison availability</div><div class='fv'>{'available' if row.comparison_available else 'unavailable'}</div></div></div></td></tr>"
        for row in rows
    ) or "<tr><td colspan='8' class='muted'>No TESTING Trigger Set evidence recorded yet.</td></tr>"
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>TEST SET EVIDENCE</div><div class='panel-meta'>Intraday governance readiness is separate from Trigger Set lifecycle status; no automatic promotion.</div></div></div><div class='table-wrap'><table><thead><tr><th>Set</th><th>Status</th><th>Age</th><th>Signals</th><th>Closed trades</th><th>Regime coverage</th><th>Readiness</th><th>Recommendation</th></tr></thead><tbody>{body}</tbody></table></div></div>"


def _futures_panel(rows) -> str:
    body = "".join(
        f"<tr><td class='mono'>{_h(_compact(row.time))}</td><td>{_h(row.symbol)}</td><td>{_h(row.category)}</td><td>{_h(row.action)}</td><td>{_h(row.exchange_side)}</td><td>{_h(row.quantity)}</td><td>{_h(row.requested_price)}</td><td>{_h(row.leverage)}x</td><td>{_h(row.expected_net_edge)}</td><td>{_h(row.status)}</td><td class='mono'>{_h(_short(row.execution_id))}</td></tr>"
        for row in rows
    ) or "<tr><td colspan='11' class='muted'>No futures execution records yet. Dashboard does not fabricate positions, P&amp;L, fees, or funding.</td></tr>"
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>Futures readiness</div><div class='panel-meta'>Read-only persisted Bybit Demo linear perpetual records; no dashboard order controls.</div></div></div><div class='table-wrap'><table><thead><tr><th>Time</th><th>Symbol</th><th>Category</th><th>Action</th><th>Side</th><th>Qty</th><th>Limit</th><th>Lev</th><th>Net edge</th><th>Status</th><th>Order</th></tr></thead><tbody>{body}</tbody></table></div></div>"


def _futures_accounting_panel(equity, rows) -> str:
    if equity is None:
        equity_body = "<div class='muted'>No futures equity snapshot recorded yet.</div>"
    else:
        equity_body = (
            "<div class='set-detail'>"
            f"{_kv('Source', equity.source)}"
            f"{_kv('Observed', _compact(equity.observed_at))}"
            f"{_kv('Wallet', equity.wallet_balance)}"
            f"{_kv('Equity', equity.equity)}"
            f"{_kv('Available margin', equity.available_margin)}"
            f"{_kv('Used margin', equity.used_margin)}"
            f"{_kv('Unrealized P&L', equity.unrealized_pnl)}"
            f"{_kv('Realized P&L', equity.realized_pnl)}"
            f"{_kv('Drawdown', equity.drawdown_absolute + ' / ' + equity.drawdown_percent + '%')}"
            f"{_kv('Max drawdown', equity.max_drawdown)}"
            "</div>"
        )
    body = "".join(
        f"<tr><td class='mono'>{_h(_short(row.trade_id))}</td><td>{_h(_compact(row.closed_at))}</td><td>{_h(row.evidence_source)}</td><td>{_h(row.simulation_model_version)}</td><td>{_h(row.symbol)}</td><td>{_h(row.direction)}</td><td>{_h(row.quantity)}</td><td>{_h(row.leverage)}x</td><td>{_h(row.entry_vwap)}</td><td>{_h(row.exit_vwap)}</td><td>{_h(row.gross_pnl)}</td><td>{_h(row.fees)}</td><td>{_h(row.funding)}</td><td>{_h(row.net_pnl)}</td><td>{_h(str(row.duration_seconds))}s</td><td>{_h(row.trigger_set)}</td><td>{_h(row.regime)}</td></tr>"
        for row in rows
    ) or "<tr><td colspan='17' class='muted'>No accounting-backed closed futures trades recorded yet.</td></tr>"
    return f"<div class='panel'><div class='panel-head'><div><div class='panel-title'>Futures Accounting Evidence</div><div class='panel-meta'>Backend-computed P&amp;L, fees, funding, equity and drawdown; exchange and TEST simulation facts are labeled by evidence source.</div></div></div>{equity_body}<div class='table-wrap analytics-compact'><table><thead><tr><th>Trade</th><th>Closed</th><th>Source</th><th>Model</th><th>Symbol</th><th>Dir</th><th>Qty</th><th>Lev</th><th>Entry VWAP</th><th>Exit VWAP</th><th>Gross</th><th>Fees</th><th>Funding</th><th>Net</th><th>Duration</th><th>Set</th><th>Regime</th></tr></thead><tbody>{body}</tbody></table></div></div>"


def _definition_panel(title: str, value) -> str:
    if isinstance(value, dict):
        body = "".join(f"<div class='set-rule'><span class='mono'>{_h(k)}</span><span>{_h(v)}</span></div>" for k, v in value.items()) or "<div class='muted'>No values recorded.</div>"
    else:
        body = f"<div class='activity-row'><div class='mono muted'>value</div><div>{_h(value or '-')}</div><span class='badge gray'>read-only</span></div>"
    return f"<section class='panel'><div class='panel-head'><div class='panel-title'>{_h(title)}</div></div><div class='activity'>{body}</div></section>"


def _used_in_panel(rows) -> str:
    body = "".join(f"<tr><td class='mono'>{_h(row.get('set_id'))}</td><td>{_h(row.get('version'))}</td><td>{_status_badge(str(row.get('status')))}</td><td>{_h(row.get('purpose'))}</td></tr>" for row in rows) or "<tr><td colspan='4' class='muted'>This exact rule version is not referenced by a Trigger Set.</td></tr>"
    return f"<section class='panel'><div class='panel-head'><div class='panel-title'>Used In Trigger Sets</div></div><div class='table-wrap'><table><thead><tr><th>Set</th><th>Version</th><th>Status</th><th>Purpose</th></tr></thead><tbody>{body}</tbody></table></div></section>"


def _version_history_panel(rows) -> str:
    body = "".join(f"<tr><td><a class='linkbtn' href='/rules/{_h(row.get('rule_id'))}/{_h(row.get('version'))}'>{_h(row.get('version'))}</a></td><td>{_h(_compact(row.get('created_at')))}</td><td>{_h(row.get('condition'))}</td><td>{_status_badge(str(row.get('status')))}</td><td>{_h((row.get('definition') or {}).get('source_recommendation_id', '-'))}</td></tr>" for row in rows)
    return f"<section class='panel'><div class='panel-head'><div class='panel-title'>Version History</div></div><div class='table-wrap'><table><thead><tr><th>Version</th><th>Created</th><th>Changed parameters / summary</th><th>Status</th><th>Source</th></tr></thead><tbody>{body}</tbody></table></div></section>"


def _rule_recommendations_panel(rows) -> str:
    body = "".join(f"<tr><td><a class='linkbtn' href='/recommendations/{_h(row.get('recommendation_id'))}'>{_h(row.get('title'))}</a></td><td>{_status_badge(str(row.get('status')))}</td><td>{_h(row.get('hypothesis'))}</td></tr>" for row in rows) or "<tr><td colspan='3' class='muted'>No recommendations reference this exact rule version.</td></tr>"
    return f"<section class='panel'><div class='panel-head'><div class='panel-title'>Recommendations</div></div><div class='table-wrap'><table><thead><tr><th>Recommendation</th><th>Status</th><th>Hypothesis</th></tr></thead><tbody>{body}</tbody></table></div></section>"


def _kv(label: str, value) -> str:
    return f"<div><div class='fl'>{_h(label)}</div><div class='fv'>{_h(value or '-')}</div></div>"


def _logs(rows) -> str:
    return "".join(f"<div class='activity-row'><div class='mono muted'>{_h(_compact(row.time))}</div><div>{_h(row.message)}</div>{_status_badge(row.status)}</div>" for row in rows) or "<div class='activity-row'><div class='mono muted'>-</div><div>No activity recorded yet.</div><span class='badge gray'>EMPTY</span></div>"


def _health_panel(rows) -> str:
    body = "".join(f"<tr><td>{_h(row['connection'])}</td><td><span class='badge test'>{_h(row['status'])}</span></td><td>{_h(row['uptime'])}</td><td class='mono'>{_h(row['last_success'])}</td><td>{_h(row['disconnects_24h'])}</td><td class='muted'>{_h(row['last_error'])}</td></tr>" for row in rows)
    return f"<div class='panel'><div class='panel-head'><div class='panel-title'>API health</div></div><div class='table-wrap'><table><thead><tr><th>Connection</th><th>Status</th><th>Uptime</th><th>Last success</th><th>Disconnects 24h</th><th>Last error</th></tr></thead><tbody>{body}</tbody></table></div></div>"


def _drawer() -> str:
    return "<div class='drawer-bg' id='setDrawerBg' onclick=\"if(event.target.id==='setDrawerBg')closeSetDrawer()\"><aside class='drawer'><div class='drawer-head'><div><div class='mono muted'>Trigger set</div><h2 id='setTitle'>-</h2><span class='badge gray' id='setBadge'>UNKNOWN</span></div><button class='iconbtn' onclick='closeSetDrawer()'>&times;</button></div><div class='section'><div class='section-title'>Set</div><div class='set-detail'><div><div class='fl'>Version</div><div class='fv' id='setVersion'>-</div></div><div><div class='fl'>Rules count</div><div class='fv' id='setCount'>0</div></div><div><div class='fl'>Purpose</div><div class='fv' id='setPurpose'>-</div></div><div><div class='fl'>Created</div><div class='fv' id='setCreated'>-</div></div></div></div><div class='section'><div class='section-title'>Included rules</div><div class='set-rules' id='setRules'></div></div></aside></div>"


def _modal() -> str:
    return "<div class='modal-bg' id='listModalBg' onclick=\"if(event.target.id==='listModalBg')closeModal()\"><div class='modal'><div class='modal-head'><div class='modal-title' id='modalTitle'>Trades</div><button class='iconbtn' onclick='closeModal()'>&times;</button></div><div class='modal-body'><div class='filter-grid'><div class='filter-field'><label>From</label><input type='date'></div><div class='filter-field'><label>To</label><input type='date'></div><div class='filter-field'><label>Asset</label><select><option>BTCUSDT</option></select></div><div class='filter-field'><label>Side / status</label><select><option>All</option></select></div></div><div class='modal-actions'><button class='button' disabled>Reset</button><button class='button dark' disabled>Apply</button></div><p class='muted'>Full filtered lists are read-only and use persisted dashboard data.</p></div></div></div>"


def _script_json(value) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")



def _set_data(rows) -> dict[str, dict[str, object]]:
    return {f"{row.set_id}::{row.version}": {"status": row.status, "cls": _status_class(row.status), "version": row.version, "count": row.rules_count, "purpose": row.purpose, "created": _compact(row.created_at), "rules": [[rule.get("rule_id", "-"), rule.get("condition", "-")] for rule in row.rules]} for row in rows}


def _script() -> str:
    return r"""const envPages=new Set(['overview']);function showPage(id){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.tabbtn').forEach(x=>x.classList.toggle('active',x.dataset.page===id));document.getElementById('envSwitch').style.display=envPages.has(id)?'inline-flex':'none';renderEnv()}document.querySelectorAll('.tabbtn').forEach(b=>b.addEventListener('click',()=>showPage(b.dataset.page)));function setEnv(next){env=next;liveBtn.className=next==='live'?'active live':'';testBtn.className=next==='test'?'active test':'';renderEnv()}function renderEnv(){document.getElementById('liveOverview').style.display=env==='live'?'block':'none';document.getElementById('testOverview').style.display=env==='test'?'block':'none'}function filterRules(){const q=ruleSearch.value.toLowerCase(),s=statusFilter.value;document.querySelectorAll('#rulesTable tbody tr').forEach(tr=>{tr.style.display=(tr.innerText.toLowerCase().includes(q)&&(s==='all'||tr.dataset.status===s))?'':'none'})}function filterSets(){const s=document.getElementById('setStatusFilter').value;document.querySelectorAll('#setsTable tbody tr,#setsMobile .mcard').forEach(tr=>{tr.style.display=(s==='all'||tr.dataset.status===s)?'':'none'})}function toggleEvidence(key){document.querySelectorAll('[data-evidence="'+key+'"]').forEach(row=>row.classList.toggle('open'))}function confirmPauseEntries(){return confirm('Pause new entries?\n\nNew ACTIVE executions will be blocked.\nTesting, analytics and reconciliation will continue.')}function confirmResumeTrading(){return confirm('Resume new ACTIVE executions?\n\nTesting, analytics and reconciliation will continue.')}async function copyData(){const txt=document.body.innerText;try{await navigator.clipboard.writeText(txt);alert('Copied')}catch(e){prompt('Copy:',txt)}}function openSet(name){const s=setData[name];if(!s)return;setTitle.textContent=s.version;setBadge.textContent=s.status;setBadge.className='badge '+s.cls;setVersion.textContent=s.version;setCount.textContent=s.count;setPurpose.textContent=s.purpose;setCreated.textContent=s.created;setRules.replaceChildren(...(s.rules.length?s.rules.map(r=>{const d=document.createElement('div');d.className='set-rule';const id=document.createElement('span');id.className='mono';id.textContent=r[0];const condition=document.createElement('span');condition.textContent=r[1];d.append(id,condition);return d;}):[Object.assign(document.createElement('div'),{className:'muted',textContent:'No rules recorded'})]));setDrawerBg.classList.add('open')}function closeSetDrawer(){setDrawerBg.classList.remove('open')}function openFullList(kind){modalTitle.textContent=kind==='trades'?'Trades':'Positions';listModalBg.classList.add('open')}function closeModal(){listModalBg.classList.remove('open')}renderEnv();"""


def _status_badge(status: str) -> str:
    return f"<span class='badge {_status_class(status)}'>{_h(status)}</span>"


def _status_class(status: str) -> str:
    value = status.lower()
    if value in {"active", "live", "active lane"}:
        return "live"
    if value in {"testing", "test"}:
        return "test"
    if value == "archive":
        return "amber"
    return "gray"


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_h(title)}</title>
<style>
:root{{--bg:#f6f7f9;--panel:#fff;--text:#18181b;--muted:#71717a;--line:#e4e4e7;--line2:#d4d4d8;--green:#15803d;--greenbg:#f0fdf4;--blue:#1d4ed8;--bluebg:#eff6ff;--amber:#a16207;--amberbg:#fffbeb;--red:#b91c1c;--redbg:#fef2f2;--page-max:1440px;--page-pad:22px}}*{{box-sizing:border-box}}body{{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--text)}}button,input,select{{font:inherit}}.app{{min-height:100vh}}.main{{min-width:0}}.container{{width:100%;max-width:var(--page-max);margin:0 auto;padding-inline:var(--page-pad)}}.toolbar{{height:58px;background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}}.toolbar-inner{{height:58px;display:flex;align-items:center;justify-content:space-between}}a{{color:inherit}}.brand-top{{font-weight:780;font-size:15px;letter-spacing:-.01em}}.utility-actions{{display:flex;align-items:center;gap:8px}}.utility-actions form{{margin:0}}.utility-btn{{border:1px solid var(--line2);background:#fff;border-radius:8px;padding:6px 9px;font-size:11px;font-weight:700;color:#3f3f46;cursor:pointer}}.stop-btn{{background:var(--redbg);border-color:#fecaca;color:var(--red)}}.resume-btn{{background:#18181b;border-color:#18181b;color:#fff}}.env-switch{{display:inline-flex;align-items:center;gap:4px;background:#f7f7f8;border:1px solid #ececef;border-radius:999px;padding:2px}}.env-switch button{{border:0;background:transparent;padding:5px 10px;border-radius:999px;font-size:10px;font-weight:700;color:#8a8a91;cursor:pointer;letter-spacing:.02em}}.env-switch button.active.live,.env-switch button.active.test{{background:#fff;color:#27272a;box-shadow:0 1px 2px rgba(24,24,27,.07)}}.tabsbar{{background:#fff;border-bottom:1px solid var(--line)}}.tabs{{display:flex;gap:22px;height:40px;align-items:flex-end}}.tabbtn{{border:0;background:transparent;padding:0 0 9px;color:#71717a;font-size:12px;font-weight:700;cursor:pointer;border-bottom:2px solid transparent}}.tabbtn.active{{color:#18181b;border-bottom-color:#18181b}}.content{{padding-top:10px;padding-bottom:18px}}.page{{display:none}}.page.active{{display:block}}.context-strip{{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin-bottom:8px;font-size:11px;color:#52525b}}.context-strip span:not(.badge){{border:1px solid var(--line);background:#fff;border-radius:8px;padding:5px 8px}}.cards{{display:flex;gap:7px;margin-bottom:9px;overflow-x:auto;flex-wrap:nowrap;scrollbar-width:none}}.cards::-webkit-scrollbar{{display:none}}.card{{background:#fff;border:1px solid var(--line);border-radius:9px;padding:9px 11px;min-height:0;flex:1 0 142px;min-width:142px}}.label{{font-size:9px;color:var(--muted);margin-bottom:3px}}.value{{font-size:16px;font-weight:750;line-height:1.15;overflow-wrap:anywhere}}.sub{{font-size:9px;color:var(--muted);margin-top:2px}}.positive{{color:var(--green)}}.panel{{background:#fff;border:1px solid var(--line);border-radius:11px;overflow:hidden;margin-bottom:11px}}.panel-head{{padding:12px 14px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px}}.panel-title{{font-size:13px;font-weight:700}}.panel-meta{{font-size:10px;color:var(--muted);margin-top:2px}}.table-wrap{{overflow:auto}}table{{width:100%;border-collapse:collapse;font-size:12px}}th{{padding:9px 11px;background:#fafafa;border-bottom:1px solid var(--line);text-align:left;font-size:10px;color:#71717a;text-transform:uppercase;letter-spacing:.03em;white-space:nowrap}}td{{padding:11px;border-bottom:1px solid #f0f0f1;white-space:nowrap;vertical-align:top}}tbody tr:last-child td{{border-bottom:0}}.evidence-detail{{display:table-row;background:#fcfcfd}}.mono{{font-family:"SFMono-Regular",Consolas,monospace;font-size:11px}}.muted{{color:var(--muted)}}.badge{{display:inline-flex;padding:4px 7px;border-radius:999px;font-size:10px;font-weight:750;border:1px solid transparent}}.badge.live{{background:#18181b;color:#fff}}.badge.test{{background:#fff;color:#52525b;border-color:#d4d4d8}}.badge.green{{background:var(--greenbg);color:var(--green);border-color:#dcfce7}}.badge.blue{{background:var(--bluebg);color:var(--blue);border-color:#dbeafe}}.badge.amber{{background:var(--amberbg);color:var(--amber);border-color:#fef3c7}}.badge.gray{{background:#f4f4f5;color:#52525b;border-color:#e4e4e7}}.filters{{display:flex;gap:8px;align-items:center;flex-wrap:wrap}}.search,select{{border:1px solid var(--line2);background:#fff;border-radius:8px;padding:8px 10px;font-size:12px;outline:none}}.search{{min-width:220px}}.button{{border:1px solid var(--line2);background:#fff;padding:8px 10px;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer}}.button.dark{{background:#18181b;color:#fff;border-color:#18181b}}.button:disabled{{opacity:.45;cursor:not-allowed}}.panel-actions{{display:flex;gap:7px;align-items:center}}.linkbtn{{border:0;background:transparent;padding:0;color:#18181b;text-decoration:underline;text-decoration-color:#a1a1aa;text-underline-offset:3px;font:inherit;font-weight:700;cursor:pointer}}.set-detail{{display:grid;grid-template-columns:1fr 1fr;gap:10px 16px;margin-bottom:12px}}.set-rules{{display:flex;flex-direction:column;gap:8px}}.set-rule{{display:flex;justify-content:space-between;gap:10px;padding:9px 10px;border:1px solid var(--line);border-radius:8px;background:#fafafa;font-size:11px}}.activity{{padding:3px 14px 8px}}.activity-row{{display:grid;grid-template-columns:110px 1fr auto;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f1;font-size:12px}}.activity-row:last-child{{border-bottom:0}}.mobile-list{{display:none;gap:9px}}.mcard{{background:#fff;border:1px solid var(--line);border-radius:11px;padding:13px}}.mhead{{display:flex;justify-content:space-between;gap:10px;margin-bottom:10px}}.mtitle{{font-size:13px;font-weight:750}}.msub{{font-size:10px;color:var(--muted);margin-top:2px}}.mgrid{{display:grid;grid-template-columns:1fr 1fr;gap:8px 12px}}.fl{{font-size:9px;color:var(--muted);margin-bottom:2px}}.fv{{font-size:12px;font-weight:650;overflow-wrap:anywhere}}.drawer-bg{{display:none;position:fixed;inset:0;background:rgba(24,24,27,.18);z-index:50}}.drawer-bg.open{{display:block}}.drawer{{position:absolute;right:0;top:0;bottom:0;width:min(440px,95vw);background:#fff;padding:22px;overflow:auto}}.drawer-head{{display:flex;justify-content:space-between;gap:12px;margin-bottom:18px}}.drawer h2{{font-size:19px;margin:3px 0 7px}}.iconbtn{{width:32px;height:32px;border:1px solid var(--line);background:#fff;border-radius:8px;cursor:pointer}}.section{{padding:16px 0;border-top:1px solid var(--line)}}.section-title{{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin-bottom:10px}}.modal-bg{{display:none;position:fixed;inset:0;background:rgba(24,24,27,.22);z-index:60;padding:28px}}.modal-bg.open{{display:flex;align-items:flex-start;justify-content:center}}.modal{{width:min(1180px,100%);max-height:calc(100vh - 56px);overflow:auto;background:#fff;border-radius:12px;border:1px solid var(--line);box-shadow:0 20px 50px rgba(24,24,27,.14)}}.modal-head{{padding:14px 16px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px;position:sticky;top:0;background:#fff;z-index:2}}.modal-title{{font-size:14px;font-weight:750}}.modal-body{{padding:14px 16px}}.filter-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:14px}}.filter-field label{{display:block;font-size:10px;color:var(--muted);margin-bottom:4px}}.filter-field input,.filter-field select{{width:100%;border:1px solid var(--line2);border-radius:8px;padding:8px 9px;font-size:12px;background:#fff}}.modal-actions{{display:flex;gap:8px;justify-content:flex-end;margin-top:10px}}@media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr)}}}}@media(max-width:760px){{:root{{--page-pad:12px}}body{{background:#fff}}.app{{display:block}}.main{{padding-bottom:0}}.toolbar{{height:auto;min-height:54px}}.toolbar-inner{{min-height:54px;height:auto;padding-block:8px}}.brand-top{{font-size:14px}}.utility-actions{{gap:5px;flex-wrap:wrap;justify-content:flex-end}}.utility-btn{{padding:5px 7px;font-size:10px}}.tabsbar{{}}.tabs{{height:38px;gap:18px}}.tabbtn{{font-size:11px;padding-bottom:8px}}.content{{padding-top:8px;padding-bottom:12px}}.cards{{display:flex;gap:6px;overflow-x:auto;flex-wrap:nowrap;padding-bottom:2px;scrollbar-width:none}}.card{{flex:0 0 132px;min-width:132px;padding:8px 9px}}.value{{font-size:15px}}.desktop-table{{display:none}}.mobile-list{{display:grid}}.panel{{margin-bottom:11px}}.panel-head{{padding:10px 11px}}.activity{{padding:0 11px 6px}}.activity-row{{grid-template-columns:70px 1fr;font-size:11px}}.activity-row>:last-child{{display:none}}.filters{{width:100%}}.search{{width:100%;min-width:0}}.panel-actions{{gap:5px}}.panel-actions .button{{padding:6px 8px;font-size:10px}}.modal-bg{{padding:0}}.modal{{width:100%;height:100%;max-height:none;border-radius:0}}.filter-grid{{grid-template-columns:1fr 1fr}}.drawer{{width:100%;padding:16px}}.set-detail{{grid-template-columns:1fr 1fr}}.set-rule{{display:block}}.set-rule span{{display:block}}.set-rule span+span{{margin-top:4px;color:var(--muted)}}}}
.evidence-detail td{{white-space:normal}}.evidence-detail .set-detail{{min-width:0}}.analytics-compact table{{table-layout:fixed}}.analytics-compact th,.analytics-compact td{{padding-inline:7px;white-space:normal;overflow-wrap:anywhere;line-height:1.25}}.analytics-compact th{{font-size:9px}}.analytics-compact td{{font-size:11px}}@media(max-width:760px){{.table-wrap table{{min-width:720px}}.evidence-detail .set-detail{{grid-template-columns:1fr 1fr}}}}@media(max-width:480px){{.toolbar-inner{{flex-wrap:wrap;align-content:center;gap:6px}}.utility-actions{{width:100%;justify-content:flex-start}}.table-wrap table{{min-width:680px}}.evidence-detail .set-detail{{grid-template-columns:1fr}}}}
@media(max-width:620px){{.toolbar{{height:auto;min-height:88px}}.toolbar-inner{{display:grid;grid-template-columns:1fr;height:auto;min-height:88px;align-content:center;gap:7px;padding-block:8px}}.brand-top{{min-width:0}}.utility-actions{{width:100%;max-width:100%;justify-content:flex-start;overflow-x:auto;scrollbar-width:none}}.utility-actions::-webkit-scrollbar{{display:none}}}}
</style>
</head>
<body>{body}</body>
</html>"""


def _short(value: str | None) -> str:
    if not value:
        return "-"
    return value if len(value) <= 18 else f"{value[:10]}...{value[-6:]}"


def _compact(value: str | None) -> str:
    if not value:
        return "-"
    return value.replace("T", " ").replace("+00:00", "Z")


def _h(value: object) -> str:
    text = str(value)
    lower = text.lower()
    if any(token in lower for token in ("bybit_api_secret", "bybit_api_key", "authorization:", "x-bapi-api-key", "paste_your")):
        return "[redacted]"
    return escape(text, quote=True)



if __name__ == "__main__":
    raise SystemExit(main())
