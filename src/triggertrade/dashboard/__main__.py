"""Local read-only TriggerTrade v6 dashboard."""

from __future__ import annotations

from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
from urllib.parse import parse_qs, unquote, urlparse

from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.persistence import OperatorStateStore
from triggertrade.services.bootstrap import ensure_runtime_registry_for_env, merged_runtime_env, runtime_db_path


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


class DashboardServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address,
        handler_class,
        *,
        read_model: DashboardReadModel,
        operator_store: OperatorStateStore,
    ) -> None:
        super().__init__(server_address, handler_class)
        self.read_model = read_model
        self.operator_store = operator_store
        self.operator_control_token = secrets.token_urlsafe(24)


class DashboardHandler(BaseHTTPRequestHandler):
    server: DashboardServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/rules", "/analytics"}:
            selected_set = parse_qs(parsed.query).get("set", [""])[0]
            initial_page = parsed.path.strip("/") or "overview"
            self._send_html(render_dashboard(self.server.read_model, selected_set, initial_page))
            return
        if parsed.path.startswith("/set/"):
            self._send_html(render_dashboard(self.server.read_model, unquote(parsed.path.removeprefix("/set/"))))
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
        if parsed.path in {"/operator/pause", "/operator/resume"}:
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(min(length, 2048)).decode("utf-8")
            values = parse_qs(body)
            if (
                values.get("confirm", [""])[0] != "yes"
                or values.get("token", [""])[0] != self.server.operator_control_token
            ):
                self._send_html(render_not_found("operator confirmation required"), HTTPStatus.BAD_REQUEST)
                return
            if parsed.path.endswith("/pause"):
                self.server.operator_store.pause(reason="confirmed local STOP TRADING")
            else:
                self.server.operator_store.resume(reason="confirmed local Resume")
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
        self.end_headers()
        self.wfile.write(payload)

    def _send_text(self, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def render_dashboard(read_model: DashboardReadModel, selected_set: str = "", initial_page: str = "overview") -> str:
    if initial_page not in {"overview", "rules", "analytics", "logs", "settings"}:
        initial_page = "overview"
    live = read_model.get_live_overview()
    test = read_model.get_test_overview()
    trigger_sets = read_model.list_trigger_sets()
    rules = read_model.list_rules()
    futures_trades = getattr(read_model, "list_recent_futures_trades", lambda: ())()
    logs = read_model.list_logs()
    health = read_model.get_api_health()
    operator_state = getattr(read_model, "get_operator_trading_state", lambda: None)()
    operator_token = getattr(read_model, "operator_control_token", "")
    recommendations = getattr(read_model, "list_recommendations", lambda: ())()
    performance = getattr(read_model, "list_set_performance", lambda: ())()
    test_evidence = getattr(read_model, "list_test_set_evidence", lambda: ())()
    futures_closed_trades = getattr(read_model, "list_futures_closed_trades", lambda: ())()
    live_closed_trades = getattr(read_model, "list_closed_trades_by_source", lambda source: ())("exchange")
    test_closed_trades = getattr(read_model, "list_closed_trades_by_source", lambda source: ())("test_simulation")
    futures_equity = getattr(read_model, "get_latest_futures_equity", lambda: None)()
    futures_position = getattr(read_model, "get_current_futures_position", lambda: None)()
    baseline_comparisons = getattr(read_model, "list_baseline_comparisons", lambda: ())()
    current_regime = getattr(read_model, "get_current_market_regime", lambda: None)()
    regime_analytics = getattr(read_model, "list_regime_analytics", lambda: ())()
    live_trace = read_model.get_latest_lane_trace("ACTIVE")
    test_trace = read_model.get_latest_lane_trace("TEST")
    return _page(
        title="TriggerTrade v6",
        body=f"""
<div class="app">
<main class="main">
  <div class="toolbar"><div class="container toolbar-inner">
    <div class="brand-top">TriggerTrade</div>
    <div class="utility-actions">
      {_operator_controls(operator_state, operator_token)}
      <button class="utility-btn" onclick="showPage('logs')">Logs</button>
      <button class="utility-btn" onclick="showPage('settings')">Settings</button>
      <button class="utility-btn" onclick="copyData()">Copy</button>
    </div>
  </div></div>
  <div class="tabsbar"><div class="container tabsbar-inner"><div class="tabs"><button class="tabbtn {_active_tab(initial_page, 'overview')}" data-page="overview">Overview</button><button class="tabbtn {_active_tab(initial_page, 'rules')}" data-page="rules">Rules</button><button class="tabbtn {_active_tab(initial_page, 'analytics')}" data-page="analytics">Analytics</button></div></div></div>
  <div class="content container">
    <section class="page {_active_page(initial_page, 'overview')}" id="overview">
      <div style="display:flex;justify-content:flex-end;margin-bottom:8px"><div class="env-switch" id="envSwitch"{_env_switch_style(initial_page)}><button id="liveBtn" class="active live" onclick="setEnv('live')">LIVE</button><button id="testBtn" onclick="setEnv('test')">TEST</button></div></div>
      {_overview_section("liveOverview", live, futures_trades, live_closed_trades, live_trace, True, current_regime, futures_equity, futures_position, operator_state)}
      {_overview_section("testOverview", test, (), test_closed_trades, test_trace, False, current_regime, None, None, operator_state)}
    </section>
    <section class="page {_active_page(initial_page, 'rules')}" id="rules">{_trigger_sets_panel(trigger_sets)}{_rules_panel(rules)}</section>
    <section class="page {_active_page(initial_page, 'analytics')}" id="analytics">{_test_evidence_panel(test_evidence)}{_regime_analytics_panel(regime_analytics)}{_futures_accounting_panel(futures_equity, futures_closed_trades)}{_futures_panel(futures_trades)}{_performance_panel(performance)}{_baseline_comparison_panel(baseline_comparisons)}{_recommendations_panel(recommendations)}</section>
    <section class="page {_active_page(initial_page, 'logs')}" id="logs"><div class="panel"><div class="activity">{_logs(logs)}</div></div></section>
    <section class="page {_active_page(initial_page, 'settings')}" id="settings">{_health_panel(health)}<div class="panel"><div class="panel-head"><div class="panel-title">Connection events</div></div><div class="activity">{_logs(logs[:5])}</div></div></section>
  </div>
</main>
</div>
{_drawer()}
{_modal()}
<script>
let env='live';
const setData={_script_json(_set_data(trigger_sets))};
{_script()}
</script>
""",
    )


def render_not_found(value: str) -> str:
    return _page("Not Found", f"<div class='content'><div class='panel'><div class='panel-head'><div class='panel-title'>Not Found</div></div><div class='activity'>{_h(value)}</div></div></div>")


def create_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, db_path: str | Path = "runtime/triggertrade_paper.sqlite3") -> DashboardServer:
    if host != DEFAULT_HOST:
        raise ValueError("dashboard binds to 127.0.0.1 only; non-local bind is not supported")
    read_model = DashboardReadModel(db_path)
    server = DashboardServer(
        (host, port),
        DashboardHandler,
        read_model=read_model,
        operator_store=OperatorStateStore(db_path),
    )
    read_model.operator_control_token = server.operator_control_token
    return server


def create_server_from_env(
    process_env: dict[str, str] | None = None,
    *,
    env_file: str | Path = ".env",
) -> tuple[DashboardServer, Path]:
    env = merged_runtime_env(os.environ if process_env is None else process_env, env_file=env_file)
    config, bootstrap = ensure_runtime_registry_for_env(env)
    host = env.get("TRIGGERTRADE_DASHBOARD_HOST", DEFAULT_HOST)
    port = int(env.get("TRIGGERTRADE_DASHBOARD_PORT", str(DEFAULT_PORT)))
    db_path = runtime_db_path(config, env)
    return create_server(host=host, port=port, db_path=db_path), bootstrap.db_path


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

def _active_page(current: str, expected: str) -> str:
    return "active" if current == expected else ""


def _active_tab(current: str, expected: str) -> str:
    return "active" if current == expected else ""


def _env_switch_style(current: str) -> str:
    return "" if current == "overview" else " style=\"display:none\""

def _overview_section(element_id, overview, open_orders, closed_trades, trace, is_live: bool, current_regime=None, equity=None, position=None, operator_state=None) -> str:
    style = "" if is_live else ' style="display:none"'
    lane = "LIVE" if is_live else "TEST"
    lane_sub = "ACTIVE Bybit Demo Linear Perpetual" if is_live else "Local Futures Simulation"
    rule_label = "ACTIVE Set" if is_live else "Testing Set"
    regime_value = "unavailable" if current_regime is None else current_regime.state
    operator_value = "UNKNOWN" if operator_state is None else operator_state.state.replace("TRADING_", "")
    return (
        f"<div id=\"{element_id}\"{style}>"
        f"<div class=\"context-strip\"><span class=\"badge {'live' if is_live else 'test'}\">{lane}</span>"
        f"<span>Bybit Demo</span><span>Linear Perpetual</span><span>BTCUSDT</span><span>1m</span>"
        f"<span>{_h(rule_label)}: {_h(overview.rule_set)}</span><span>Regime: {_h(regime_value)}</span></div>"
        f"<div class=\"cards kpi-scroll\">{_account_cards(equity, closed_trades, open_orders, is_live, operator_value)}</div>"
        f"{_lane_summary_panel(overview, lane_sub, operator_value, current_regime)}"
        f"{_market_regime_panel(current_regime)}"
        f"{_positions_panel(position, is_live)}"
        f"{_closed_trades_panel(closed_trades, is_live)}"
        f"{_open_futures_orders_panel(open_orders) if is_live else ''}"
        f"{_trace_panel(trace, is_live)}"
        "</div>"
    )


def _account_cards(equity, closed_trades, open_orders, is_live: bool, operator_value: str) -> str:
    if equity is None:
        values = {
            "Balance": "unavailable",
            "Equity": "unavailable",
            "Available margin": "unavailable",
            "Open exposure": "unavailable",
            "Realized P&L": "unavailable",
            "Unrealized P&L": "unavailable",
            "Fees": _sum_closed_fees(closed_trades),
            "Funding": _sum_closed_field(closed_trades, "funding"),
            "Max drawdown": "unavailable",
        }
        source = "No authoritative equity snapshot" if is_live else "TEST simulation evidence only"
    else:
        values = {
            "Balance": equity.wallet_balance,
            "Equity": equity.equity,
            "Available margin": equity.available_margin,
            "Open exposure": equity.used_margin,
            "Realized P&L": equity.realized_pnl,
            "Unrealized P&L": equity.unrealized_pnl,
            "Fees": _sum_closed_fees(closed_trades),
            "Funding": _sum_closed_field(closed_trades, "funding"),
            "Max drawdown": equity.max_drawdown,
        }
        source = f"{equity.source} | Accounting v1"
    cards = [
        f"<div class='card'><div class='label'>{_h(label)}</div><div class='value'>{_h(value)}</div><div class='sub'>{_h(source if label in {'Balance','Equity'} else ('ACTIVE executions blocked' if operator_value == 'PAUSED' and is_live else 'backend fact or unavailable'))}</div></div>"
        for label, value in values.items()
    ]
    return "".join(cards)


def _sum_closed_field(rows, field: str) -> str:
    if not rows:
        return "unavailable"
    try:
        from decimal import Decimal

        return str(sum((Decimal(str(getattr(row, field))) for row in rows), Decimal("0")))
    except Exception:
        return "unavailable"


def _sum_closed_fees(rows) -> str:
    if not rows:
        return "unavailable"
    return "accounting fact"


def _lane_summary_panel(overview, lane_sub: str, operator_value: str, current_regime) -> str:
    regime = "unavailable" if current_regime is None else current_regime.state
    return (
        "<div class='panel'><div class='panel-head'><div><div class='panel-title'>Runtime Summary</div>"
        f"<div class='panel-meta'>{_h(lane_sub)} | read-only dashboard</div></div>{_status_badge(operator_value)}</div>"
        "<div class='activity'>"
        f"{_trace_row('Rule set', overview.rule_set, str(overview.rules_count) + ' rules')}"
        f"{_trace_row('Last candle', overview.latest_candle, 'completed candle checkpoint')}"
        f"{_trace_row('Last signal', overview.latest_signal, 'NO_SIGNAL is normal')}"
        f"{_trace_row('Last execution', overview.last_execution, str(overview.trades_count) + ' visible records')}"
        f"{_trace_row('Market regime', regime, 'CTX-REGIME@0.1.0')}"
        "</div></div>"
    )
def _market_regime_panel(current_regime) -> str:
    if current_regime is None:
        return "<div class='panel'><div class='panel-head'><div><div class='panel-title'>Market regime</div><div class='panel-meta'>CTX-REGIME@0.1.0 context, read-only</div></div><span class='badge gray'>unavailable</span></div></div>"
    return (
        "<div class='panel'><div class='panel-head'><div>"
        "<div class='panel-title'>Market regime</div>"
        f"<div class='panel-meta'>{_h(current_regime.rule)} | {_h(current_regime.symbol)} {_h(current_regime.timeframe)} | {_h(current_regime.observed_at)}</div>"
        "</div>"
        f"{_status_badge(current_regime.state)}</div>"
        "<div class='activity'>"
        f"{_trace_row('window_return_pct', current_regime.window_return_pct, current_regime.reason)}"
        f"{_trace_row('normalized_trend', current_regime.normalized_trend, 'volatility-normalized')}"
        f"{_trace_row('directional_persistence', current_regime.directional_persistence, 'flat steps counted')}"
        "</div></div>"
    )


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
        "<form method='post' action='/operator/pause' onsubmit=\"return confirmStopTrading()\">"
        "<input type='hidden' name='confirm' value='yes'>"
        f"{token_input}"
        "<button class='utility-btn stop-btn' type='submit'>STOP TRADING</button>"
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
<div class="app"><main class="main"><div class="toolbar"><div class="container toolbar-inner"><a class="brand-top" href="/">TriggerTrade</a><div class="utility-actions"><a class="utility-btn" href="/">Overview</a></div></div></div>
<div class="tabsbar"><div class="container tabsbar-inner"><div class="tabs"><a class="tabbtn active" href="/rules/{_h(rule.get('rule_id'))}/{_h(rule.get('version'))}">Rule Detail</a><a class="tabbtn" href="/">Registry</a></div></div></div>
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
<div class="app"><main class="main"><div class="toolbar"><div class="container toolbar-inner"><a class="brand-top" href="/">TriggerTrade</a><div class="utility-actions"><a class="utility-btn" href="/">Overview</a><a class="utility-btn" href="/analytics">Analytics</a></div></div></div>
<div class="tabsbar"><div class="container tabsbar-inner"><div class="tabs"><a class="tabbtn active" href="/trades/{_h(detail.get('trade_id'))}">Trade Detail</a><a class="tabbtn" href="/">Dashboard</a></div></div></div>
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
<div class="app"><main class="main"><div class="toolbar"><div class="container toolbar-inner"><a class="brand-top" href="/">TriggerTrade</a><div class="utility-actions"><a class="utility-btn" href="/">Analytics</a></div></div></div>
<div class="tabsbar"><div class="container tabsbar-inner"><div class="tabs"><a class="tabbtn active" href="/recommendations/{_h(rec.get('recommendation_id'))}">Recommendation</a><a class="tabbtn" href="/">Overview</a></div></div></div>
<div class="content container">
  <section class="panel"><div class="panel-head"><div><div class="panel-title">{_h(rec.get('title'))}</div><div class="panel-meta mono">{_h(rec.get('recommendation_id'))}</div></div>{_status_badge(str(rec.get('status')))}</div><div class="section"><div class="set-detail">{_kv('Created', _compact(rec.get('created_at')))}{_kv('Resulting test set', linked)}{_kv('Decision', rec.get('decision') or '-')}</div></div></section>
  {_definition_panel('Observation', rec.get('observation'))}
  {_definition_panel('Evidence', rec.get('evidence'))}
  {_definition_panel('Hypothesis', rec.get('hypothesis'))}
  {_definition_panel('Recommended Experiment', rec.get('recommended_experiment'))}
  {_definition_panel('Proposed Rule Version', rec.get('proposed_rule_changes'))}
  {_definition_panel('Proposed Trigger Set', rec.get('proposed_trigger_set_definition'))}
  {_definition_panel('Test Requirements', {'minimum_test_duration': rec.get('minimum_test_duration'), 'minimum_sample_size': rec.get('minimum_sample_size')})}
  {_definition_panel('Evaluation', rec.get('evaluation_summary') or 'Pending forward evidence.')}
</div></main></div>
""",
    )


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
    return r"""const envPages=new Set(['overview']);function showPage(id){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.tabbtn').forEach(x=>x.classList.toggle('active',x.dataset.page===id));document.getElementById('envSwitch').style.display=envPages.has(id)?'inline-flex':'none';renderEnv()}document.querySelectorAll('.tabbtn').forEach(b=>b.addEventListener('click',()=>showPage(b.dataset.page)));function setEnv(next){env=next;liveBtn.className=next==='live'?'active live':'';testBtn.className=next==='test'?'active test':'';renderEnv()}function renderEnv(){document.getElementById('liveOverview').style.display=env==='live'?'block':'none';document.getElementById('testOverview').style.display=env==='test'?'block':'none'}function filterRules(){const q=ruleSearch.value.toLowerCase(),s=statusFilter.value;document.querySelectorAll('#rulesTable tbody tr').forEach(tr=>{tr.style.display=(tr.innerText.toLowerCase().includes(q)&&(s==='all'||tr.dataset.status===s))?'':'none'})}function filterSets(){const s=document.getElementById('setStatusFilter').value;document.querySelectorAll('#setsTable tbody tr,#setsMobile .mcard').forEach(tr=>{tr.style.display=(s==='all'||tr.dataset.status===s)?'':'none'})}function toggleEvidence(key){document.querySelectorAll('[data-evidence="'+key+'"]').forEach(row=>row.classList.toggle('open'))}function confirmStopTrading(){return confirm('Stop new trades?\n\nNew ACTIVE executions will be blocked.\nTesting, analytics and reconciliation will continue.')}function confirmResumeTrading(){return confirm('Resume new ACTIVE executions?\n\nTesting, analytics and reconciliation will continue.')}async function copyData(){const txt=document.body.innerText;try{await navigator.clipboard.writeText(txt);alert('Copied')}catch(e){prompt('Copy:',txt)}}function openSet(name){const s=setData[name];if(!s)return;setTitle.textContent=s.version;setBadge.textContent=s.status;setBadge.className='badge '+s.cls;setVersion.textContent=s.version;setCount.textContent=s.count;setPurpose.textContent=s.purpose;setCreated.textContent=s.created;setRules.replaceChildren(...(s.rules.length?s.rules.map(r=>{const d=document.createElement('div');d.className='set-rule';const id=document.createElement('span');id.className='mono';id.textContent=r[0];const condition=document.createElement('span');condition.textContent=r[1];d.append(id,condition);return d;}):[Object.assign(document.createElement('div'),{className:'muted',textContent:'No rules recorded'})]));setDrawerBg.classList.add('open')}function closeSetDrawer(){setDrawerBg.classList.remove('open')}function openFullList(kind){modalTitle.textContent=kind==='trades'?'Trades':'Positions';listModalBg.classList.add('open')}function closeModal(){listModalBg.classList.remove('open')}renderEnv();"""


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
