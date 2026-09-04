"""Local read-only TriggerTrade activity dashboard."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from triggertrade.config import load_config
from triggertrade.dashboard.read_model import DashboardReadModel, TraceView


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


class DashboardServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class, *, read_model: DashboardReadModel) -> None:
        super().__init__(server_address, handler_class)
        self.read_model = read_model


class DashboardHandler(BaseHTTPRequestHandler):
    server: DashboardServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            params = parse_qs(parsed.query)
            selected = params.get("trace", [""])[0]
            self._send_html(render_dashboard(self.server.read_model, selected))
            return
        if parsed.path.startswith("/trace/"):
            trace_id = unquote(parsed.path.removeprefix("/trace/"))
            trace = self.server.read_model.get_trace(trace_id)
            if trace is None:
                self._send_html(render_not_found(trace_id), status=HTTPStatus.NOT_FOUND)
                return
            self._send_html(render_dashboard(self.server.read_model, trace_id))
            return
        if parsed.path == "/healthz":
            self._send_text("ok")
            return
        self._send_html(render_not_found(parsed.path), status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        self._send_html(render_not_found("write operations are disabled"), status=HTTPStatus.METHOD_NOT_ALLOWED)

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


def render_dashboard(read_model: DashboardReadModel, selected_trace_id: str = "") -> str:
    runtime = read_model.get_latest_runtime_state()
    latest = read_model.get_latest_decision()
    activity = read_model.list_recent_activity()
    trades = read_model.list_recent_paper_trades()
    selected_id = selected_trace_id or (activity[0].candle_id if activity else "")
    trace = read_model.get_trace(selected_id) if selected_id else None
    return _page(
        title="TriggerTrade Dashboard",
        body=f"""
        <header class="topbar">
          <div>
            <h1>TriggerTrade</h1>
            <p class="subtitle">Local read-only trading activity monitor</p>
          </div>
          <nav aria-label="Runtime scope">
            <span class="pill">PAPER</span>
            <span class="pill">BTCUSDT</span>
            <span class="pill">1m</span>
            <span class="pill">Bybit Demo</span>
            <a class="refresh" href="/">Refresh</a>
          </nav>
        </header>

        <section class="summary-grid" aria-label="Runtime Status">
          {_metric("Runtime Status", runtime.status)}
          {_metric("DB Health", runtime.db_health)}
          {_metric("Last Candle", runtime.last_processed_candle_open_time or "No candle yet")}
          {_metric("Last Processed", runtime.last_processed_at or "No activity yet")}
        </section>

        <section class="band">
          <div class="section-heading">
            <h2>Latest Decision</h2>
            <span>{_short(latest.candle_id) if latest.candle_id else "empty"}</span>
          </div>
          <div class="decision-flow">
            {_stage("Candle", latest.candle_open_time or "none")}
            {_stage("Trigger", f"{latest.trigger_rule} -> {latest.signal_type}")}
            {_stage("Strategy", latest.strategy_result)}
            {_stage("Risk", latest.risk_result)}
            {_stage("Execution", latest.execution_result)}
          </div>
          <p class="reason">{_h(latest.reason)}</p>
        </section>

        <main class="layout">
          <section class="panel wide">
            <div class="section-heading"><h2>Recent Activity</h2><span>{len(activity)} rows</span></div>
            {_activity_table(activity, selected_id)}
          </section>

          <section class="panel">
            <div class="section-heading"><h2>Paper Trades</h2><span>{len(trades)} rows</span></div>
            {_trades_table(trades)}
          </section>
        </main>

        <section class="band">
          <div class="section-heading"><h2>Full Trace</h2><span>{_h(_short(selected_id)) if selected_id else "none selected"}</span></div>
          {_trace_inspector(trace)}
        </section>

        <footer>
          Read-only dashboard. Order placement, config mutation, P&amp;L accounting, and portfolio analytics are intentionally deferred.
        </footer>
        """,
    )


def render_not_found(value: str) -> str:
    return _page(
        title="Not Found",
        body=f"""
        <header class="topbar"><h1>TriggerTrade</h1><a class="refresh" href="/">Back</a></header>
        <section class="band empty"><h2>Not Found</h2><p>No dashboard record matched {_h(value)}.</p></section>
        """,
    )


def create_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, db_path: str | Path = "runtime/triggertrade_paper.sqlite3") -> DashboardServer:
    if host != DEFAULT_HOST:
        raise ValueError("dashboard binds to 127.0.0.1 only by default; explicit non-local bind is not supported")
    return DashboardServer((host, port), DashboardHandler, read_model=DashboardReadModel(db_path))


def main() -> int:
    env = dict(os.environ)
    config = load_config(env)
    host = env.get("TRIGGERTRADE_DASHBOARD_HOST", DEFAULT_HOST)
    port = int(env.get("TRIGGERTRADE_DASHBOARD_PORT", str(DEFAULT_PORT)))
    db_path = env.get("TRIGGERTRADE_RUNTIME_DB_PATH", config.paper_runtime.db_path)
    server = create_server(host=host, port=port, db_path=db_path)
    print(f"TriggerTrade dashboard: http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def _activity_table(rows, selected_id: str = "") -> str:
    if not rows:
        return '<div class="empty">No runtime activity recorded yet.</div>'
    body = "".join(
        f"""
        <tr class="{_h('selected' if row.candle_id == selected_id else '')}">
          <td><a href="/?trace={quote(row.candle_id)}">{_h(_short(row.candle_id))}</a></td>
          <td>{_h(row.symbol)}</td>
          <td>{_h(_compact_time(row.candle))}</td>
          <td>{_badge(row.trigger_result)}</td>
          <td>{_h(row.strategy_decision)}</td>
          <td>{_badge(row.risk_result)}</td>
          <td>{_badge(row.execution_status)}</td>
        </tr>
        """
        for row in rows
    )
    return f"""
    <div class="table-wrap"><table>
      <thead><tr><th>Trace</th><th>Symbol</th><th>Candle</th><th>Trigger</th><th>Strategy</th><th>Risk</th><th>Execution</th></tr></thead>
      <tbody>{body}</tbody>
    </table></div>
    """


def _trades_table(rows) -> str:
    if not rows:
        return '<div class="empty">No paper fills recorded yet.</div>'
    body = "".join(
        f"""
        <tr>
          <td>{_h(_compact_time(row.time))}</td>
          <td>{_h(row.symbol)}</td>
          <td>{_h(row.side)}</td>
          <td>{_h(row.quantity)}</td>
          <td>{_h(row.requested_price)}</td>
          <td>{_h(row.fill_price)}</td>
          <td>{_badge(row.status)}</td>
          <td>{_h(_short(row.intent_id))}</td>
          <td>{_h(_short(row.risk_decision_id))}</td>
          <td>{_h(_short(row.execution_id))}</td>
        </tr>
        """
        for row in rows
    )
    return f"""
    <div class="table-wrap"><table>
      <thead><tr><th>Time</th><th>Symbol</th><th>Side</th><th>Qty</th><th>Req Price</th><th>Fill Price</th><th>Status</th><th>Intent</th><th>Risk</th><th>Exec</th></tr></thead>
      <tbody>{body}</tbody>
    </table></div>
    """


def _trace_inspector(trace: TraceView | None) -> str:
    if trace is None:
        return '<div class="empty">Select an activity row to inspect the full trace.</div>'
    stages = (
        ("Market Observation", trace.lifecycle),
        ("Trigger Evaluation", trace.trigger),
        ("Signal", trace.signal),
        ("Strategy Decision", trace.strategy),
        ("TradeIntent", trace.trade_intent),
        ("Risk Decision", trace.risk),
        ("Execution", trace.execution),
        ("Fills", trace.fills),
    )
    return '<div class="trace">' + "".join(_trace_stage(name, data) for name, data in stages) + "</div>"


def _trace_stage(name: str, data) -> str:
    return f"""
    <details open>
      <summary>{_h(name)}</summary>
      <pre>{_h(_format_data(data))}</pre>
    </details>
    """


def _format_data(data) -> str:
    if data is None or data == ():
        return "not recorded"
    if is_dataclass(data):
        data = asdict(data)
    if isinstance(data, tuple):
        data = list(data)
    if isinstance(data, dict):
        return "\n".join(f"{key}: {_display_value(key, value)}" for key, value in data.items())
    return _harden_text(str(data))


def _display_value(key: str, value) -> str:
    key_lower = key.lower()
    rendered = str(value)
    if any(token in key_lower for token in ("secret", "api_key", "authorization", "credential")):
        return "[redacted]"
    return _harden_text(rendered)


def _harden_text(value: str) -> str:
    lower = value.lower()
    if any(token in lower for token in ("bybit_api_secret", "bybit_api_key", "paste_your", "unit-signing-value", "authorization:", "x-bapi-api-key")):
        return "[redacted]"
    return value


def _metric(label: str, value: str) -> str:
    return f'<div class="metric"><span>{_h(label)}</span><strong>{_h(value)}</strong></div>'


def _stage(label: str, value: str) -> str:
    return f'<div class="stage"><span>{_h(label)}</span><strong>{_h(value)}</strong></div>'


def _badge(value: str) -> str:
    normalized = (value or "none").lower()
    kind = "neutral"
    if "approved" in normalized or "filled" in normalized or "buy_candidate" in normalized:
        kind = "positive"
    elif "rejected" in normalized or "unknown" in normalized or "error" in normalized:
        kind = "blocked"
    elif "no_signal" in normalized or normalized == "none" or "not evaluated" in normalized:
        kind = "quiet"
    return f'<span class="badge {kind}">{_h(value or "none")}</span>'


def _short(value: str | None) -> str:
    if not value:
        return ""
    return value if len(value) <= 18 else f"{value[:10]}...{value[-6:]}"


def _compact_time(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("T", " ").replace("+00:00", "Z")


def _h(value: object) -> str:
    return escape(str(value), quote=True)


def _page(*, title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="20">
  <title>{_h(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #202428;
      --muted: #65707b;
      --line: #d8dde3;
      --panel: #ffffff;
      --page: #f5f7f8;
      --accent: #0a6f68;
      --ok: #1f7a4d;
      --warn: #9a5b00;
      --soft: #eef2f3;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--page);
      font-size: 14px;
      line-height: 1.45;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 20px;
      padding: 22px 28px 16px;
      border-bottom: 1px solid var(--line);
      background: #fff;
      position: sticky;
      top: 0;
      z-index: 2;
    }}
    h1, h2 {{ margin: 0; letter-spacing: 0; }}
    h1 {{ font-size: 24px; }}
    h2 {{ font-size: 16px; }}
    .subtitle {{ margin: 4px 0 0; color: var(--muted); }}
    nav {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }}
    .pill, .refresh {{
      border: 1px solid var(--line);
      background: var(--soft);
      padding: 6px 9px;
      border-radius: 6px;
      font-weight: 650;
      white-space: nowrap;
    }}
    .refresh {{ background: #fff; }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 1px;
      border-bottom: 1px solid var(--line);
      background: var(--line);
    }}
    .metric {{
      background: #fff;
      padding: 16px 28px;
      min-width: 0;
    }}
    .metric span, .stage span {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong, .stage strong {{
      display: block;
      margin-top: 4px;
      overflow-wrap: anywhere;
      font-size: 14px;
    }}
    .band, .panel {{
      margin: 16px 28px;
      padding: 16px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(420px, 0.65fr);
      gap: 16px;
      margin: 0 28px;
    }}
    .layout .panel {{ margin: 0; }}
    .section-heading {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
      margin-bottom: 12px;
    }}
    .section-heading span {{ color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }}
    .decision-flow {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 1px;
      background: var(--line);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    .stage {{ background: #fff; padding: 12px; min-width: 0; }}
    .reason {{ margin: 12px 0 0; color: var(--muted); }}
    .table-wrap {{ width: 100%; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 780px; }}
    th, td {{
      text-align: left;
      border-bottom: 1px solid var(--line);
      padding: 9px 8px;
      vertical-align: top;
      overflow-wrap: anywhere;
    }}
    th {{ color: var(--muted); font-size: 12px; font-weight: 700; }}
    tr.selected td {{ background: #f0faf7; }}
    .badge {{
      display: inline-block;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 3px 6px;
      font-weight: 650;
      max-width: 240px;
      overflow-wrap: anywhere;
    }}
    .badge.positive {{ color: var(--ok); background: #eef8f2; border-color: #bfdfcd; }}
    .badge.blocked {{ color: var(--warn); background: #fff5e6; border-color: #ead1a6; }}
    .badge.quiet {{ color: var(--muted); background: var(--soft); }}
    .trace {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    details {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      min-width: 0;
    }}
    summary {{
      padding: 10px 12px;
      cursor: pointer;
      font-weight: 700;
      border-bottom: 1px solid var(--line);
    }}
    pre {{
      margin: 0;
      padding: 12px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      color: #263238;
      font-size: 12px;
    }}
    .empty {{
      color: var(--muted);
      background: #fff;
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    footer {{ color: var(--muted); padding: 4px 28px 28px; }}
    @media (max-width: 980px) {{
      .summary-grid, .decision-flow, .layout, .trace {{ grid-template-columns: 1fr; }}
      .topbar {{ align-items: flex-start; flex-direction: column; }}
      .layout {{ margin: 0 16px; }}
      .band, .panel {{ margin: 16px; }}
      .metric {{ padding: 14px 16px; }}
    }}
  </style>
</head>
<body>{body}</body>
</html>"""


if __name__ == "__main__":
    raise SystemExit(main())
