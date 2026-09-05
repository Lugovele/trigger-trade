"""Local read-only TriggerTrade v6 dashboard."""

from __future__ import annotations

from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from triggertrade.config import load_config
from triggertrade.dashboard.read_model import DashboardReadModel


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
            selected_set = parse_qs(parsed.query).get("set", [""])[0]
            self._send_html(render_dashboard(self.server.read_model, selected_set))
            return
        if parsed.path.startswith("/set/"):
            self._send_html(render_dashboard(self.server.read_model, unquote(parsed.path.removeprefix("/set/"))))
            return
        if parsed.path == "/healthz":
            self._send_text("ok")
            return
        self._send_html(render_not_found(parsed.path), HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
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


def render_dashboard(read_model: DashboardReadModel, selected_set: str = "") -> str:
    live = read_model.get_live_overview()
    test = read_model.get_test_overview()
    trigger_sets = read_model.list_trigger_sets()
    rules = read_model.list_rules()
    live_trades = read_model.list_lane_trades("ACTIVE")
    test_trades = read_model.list_lane_trades("TEST")
    logs = read_model.list_logs()
    health = read_model.get_api_health()
    live_trace = read_model.get_latest_lane_trace("ACTIVE")
    test_trace = read_model.get_latest_lane_trace("TEST")
    return _page(
        title="TriggerTrade v6",
        body=f"""
<div class="app">
<main class="main">
  <div class="toolbar">
    <div class="brand-top">TriggerTrade</div>
    <div class="utility-actions">
      <button class="utility-btn" onclick="showPage('logs')">Logs</button>
      <button class="utility-btn" onclick="showPage('settings')">Settings</button>
      <button class="utility-btn" onclick="copyData()">Copy</button>
    </div>
  </div>
  <div class="tabsbar"><div class="tabs"><button class="tabbtn active" data-page="overview">Overview</button><button class="tabbtn" data-page="rules">Rules</button></div></div>
  <div class="content">
    <section class="page active" id="overview">
      <div style="display:flex;justify-content:flex-end;margin-bottom:8px"><div class="env-switch" id="envSwitch"><button id="liveBtn" class="active live" onclick="setEnv('live')">LIVE</button><button id="testBtn" onclick="setEnv('test')">TEST</button></div></div>
      {_overview_section("liveOverview", live, live_trades, live_trace, True)}
      {_overview_section("testOverview", test, test_trades, test_trace, False)}
    </section>
    <section class="page" id="rules">{_trigger_sets_panel(trigger_sets)}{_rules_panel(rules)}</section>
    <section class="page" id="logs"><div class="panel"><div class="activity">{_logs(logs)}</div></div></section>
    <section class="page" id="settings">{_health_panel(health)}<div class="panel"><div class="panel-head"><div class="panel-title">Connection events</div></div><div class="activity">{_logs(logs[:5])}</div></div></section>
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


def _overview_section(element_id, overview, trades, trace, is_live: bool) -> str:
    style = "" if is_live else ' style="display:none"'
    lane = "LIVE" if is_live else "TEST"
    return f"""<div id="{element_id}"{style}><div class="cards"><div class="card"><div class="label">Runtime lane</div><div class="value">{lane}</div><div class="sub">paper-safe</div></div><div class="card"><div class="label">Rule set</div><div class="value">{_h(overview.rule_set)}</div><div class="sub">{overview.rules_count} rules</div></div><div class="card"><div class="label">Last candle</div><div class="value">{_h(_short(overview.latest_candle))}</div></div><div class="card"><div class="label">Last execution</div><div class="value">{_h(overview.last_execution)}</div><div class="sub">{overview.trades_count} paper records</div></div></div>{_trades_panel(trades, is_live)}{_positions_panel(is_live)}{_trace_panel(trace, is_live)}</div>"""


def _trades_panel(trades, is_live: bool) -> str:
    rows = "".join(
        f"<tr><td class='mono'>{_h(_short(row.execution_id))}</td><td class='mono'>{_h(_compact(row.time))}</td><td>{_h(row.symbol)}</td><td><span class='badge blue'>{_h(row.side)}</span></td><td>{_h(row.requested_price)}</td><td>-</td><td>-</td><td>{_h(row.quantity)}</td><td>{_h(_short(row.intent_id))}</td><td>{_h(row.status)}</td></tr>"
        for row in trades
    ) or "<tr><td colspan='10' class='muted'>No paper trades recorded for this lane.</td></tr>"
    mobile = "".join(
        f"<div class='mcard'><div class='mhead'><div><div class='mtitle'>{_h(row.symbol)}</div><div class='msub mono'>{_h(_compact(row.time))}</div></div><span class='badge {'live' if is_live else 'test'}'>{'LIVE' if is_live else 'TEST'}</span></div><div class='mgrid'><div><div class='fl'>Entry</div><div class='fv'>{_h(row.requested_price)}</div></div><div><div class='fl'>Amount</div><div class='fv'>{_h(row.quantity)}</div></div><div><div class='fl'>Status</div><div class='fv'>{_h(row.status)}</div></div><div><div class='fl'>Set</div><div class='fv'>{_h(_short(row.intent_id))}</div></div></div></div>"
        for row in trades
    ) or "<div class='mcard'><div class='mtitle'>No paper trades recorded</div><div class='msub'>NO_SIGNAL and rejected risk cycles are normal.</div></div>"
    return f"<div class='panel'><div class='panel-head'><div class='panel-title'>Trades</div><div class='panel-actions'><button class='button' onclick=\"openFullList('trades')\">View all</button></div></div><div class='table-wrap desktop-table'><table><thead><tr><th>ID</th><th>Date</th><th>Asset</th><th>Side</th><th>Entry</th><th>TP</th><th>SL</th><th>Amount</th><th>Version</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div><div class='mobile-list'>{mobile}</div></div>"


def _positions_panel(is_live: bool) -> str:
    lane = "live" if is_live else "test"
    label = "LIVE" if is_live else "TEST"
    return f"<div class='panel'><div class='panel-head'><div class='panel-title'>Positions</div><div class='panel-actions'><button class='button' onclick=\"openFullList('positions')\">View all</button></div></div><div class='table-wrap desktop-table'><table><thead><tr><th>Asset</th><th>Qty</th><th>Avg entry</th><th>Current</th><th>TP</th><th>SL</th><th>Market value</th><th>Unrealized P&amp;L</th><th>Version</th></tr></thead><tbody><tr><td colspan='9' class='muted'>Position and P&amp;L accounting are deferred until backend semantics exist.</td></tr></tbody></table></div><div class='mobile-list'><div class='mcard'><div class='mhead'><div><div class='mtitle'>Positions deferred</div><div class='msub'>No fake portfolio or P&amp;L is rendered.</div></div><span class='badge {lane}'>{label}</span></div></div></div></div>"


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
        body = "".join(
            [
                _trace_row("Market", lifecycle.get("candle_id", trace.candle_id), lifecycle.get("candle_open_time", "-")),
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
        f"<tr data-status='{_h(row.status.lower())}'><td><b>{_h(row.name)}</b><div class='mono muted'>{_h(row.rule_id)}</div></td><td>{_h(row.asset_scope)}</td><td>{_h(row.condition)}</td><td>{_h(row.used_in)}</td><td>{_h(row.version)}</td><td>{_status_badge(row.status)}</td></tr>"
        for row in rows
    ) or "<tr><td colspan='6' class='muted'>No rule registry records yet.</td></tr>"
    return f"<div class='filters' style='margin-bottom:12px'><input class='search' id='ruleSearch' placeholder='Search rules...' oninput='filterRules()'><select id='statusFilter' onchange='filterRules()'><option value='all'>All statuses</option><option value='active'>Active</option><option value='testing'>Testing</option><option value='draft'>Draft</option><option value='archive'>Archive</option></select><button class='button dark' disabled title='Read-only dashboard'>+ New rule</button></div><div class='panel'><div class='panel-head'><div><div class='panel-title'>Rule registry</div></div></div><div class='table-wrap'><table id='rulesTable'><thead><tr><th>Rule</th><th>Asset</th><th>Condition</th><th>Used in</th><th>Version</th><th>Status</th></tr></thead><tbody>{body}</tbody></table></div><div class='mobile-list' id='rulesMobile'></div></div>"


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
    return r"""const envPages=new Set(['overview']);function showPage(id){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.tabbtn').forEach(x=>x.classList.toggle('active',x.dataset.page===id));document.getElementById('envSwitch').style.display=envPages.has(id)?'inline-flex':'none';renderEnv()}document.querySelectorAll('.tabbtn').forEach(b=>b.addEventListener('click',()=>showPage(b.dataset.page)));function setEnv(next){env=next;liveBtn.className=next==='live'?'active live':'';testBtn.className=next==='test'?'active test':'';renderEnv()}function renderEnv(){document.getElementById('liveOverview').style.display=env==='live'?'block':'none';document.getElementById('testOverview').style.display=env==='test'?'block':'none'}function filterRules(){const q=ruleSearch.value.toLowerCase(),s=statusFilter.value;document.querySelectorAll('#rulesTable tbody tr').forEach(tr=>{tr.style.display=(tr.innerText.toLowerCase().includes(q)&&(s==='all'||tr.dataset.status===s))?'':'none'})}function filterSets(){const s=document.getElementById('setStatusFilter').value;document.querySelectorAll('#setsTable tbody tr,#setsMobile .mcard').forEach(tr=>{tr.style.display=(s==='all'||tr.dataset.status===s)?'':'none'})}async function copyData(){const txt=document.body.innerText;try{await navigator.clipboard.writeText(txt);alert('Copied')}catch(e){prompt('Copy:',txt)}}function openSet(name){const s=setData[name];if(!s)return;setTitle.textContent=s.version;setBadge.textContent=s.status;setBadge.className='badge '+s.cls;setVersion.textContent=s.version;setCount.textContent=s.count;setPurpose.textContent=s.purpose;setCreated.textContent=s.created;setRules.replaceChildren(...(s.rules.length?s.rules.map(r=>{const d=document.createElement('div');d.className='set-rule';const id=document.createElement('span');id.className='mono';id.textContent=r[0];const condition=document.createElement('span');condition.textContent=r[1];d.append(id,condition);return d;}):[Object.assign(document.createElement('div'),{className:'muted',textContent:'No rules recorded'})]));setDrawerBg.classList.add('open')}function closeSetDrawer(){setDrawerBg.classList.remove('open')}function openFullList(kind){modalTitle.textContent=kind==='trades'?'Trades':'Positions';listModalBg.classList.add('open')}function closeModal(){listModalBg.classList.remove('open')}renderEnv();"""


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
:root{{--bg:#f6f7f9;--panel:#fff;--text:#18181b;--muted:#71717a;--line:#e4e4e7;--line2:#d4d4d8;--green:#15803d;--greenbg:#f0fdf4;--blue:#1d4ed8;--bluebg:#eff6ff;--amber:#a16207;--amberbg:#fffbeb}}*{{box-sizing:border-box}}body{{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--text)}}button,input,select{{font:inherit}}.app{{min-height:100vh}}.main{{min-width:0}}.toolbar{{height:58px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 22px;position:sticky;top:0;z-index:20}}.brand-top{{font-weight:780;font-size:15px;letter-spacing:-.01em}}.utility-actions{{display:flex;align-items:center;gap:8px}}.utility-btn{{border:1px solid var(--line2);background:#fff;border-radius:8px;padding:6px 9px;font-size:11px;font-weight:700;color:#3f3f46;cursor:pointer}}.env-switch{{display:inline-flex;align-items:center;gap:4px;background:#f7f7f8;border:1px solid #ececef;border-radius:999px;padding:2px}}.env-switch button{{border:0;background:transparent;padding:5px 10px;border-radius:999px;font-size:10px;font-weight:700;color:#8a8a91;cursor:pointer;letter-spacing:.02em}}.env-switch button.active.live,.env-switch button.active.test{{background:#fff;color:#27272a;box-shadow:0 1px 2px rgba(24,24,27,.07)}}.tabsbar{{background:#fff;border-bottom:1px solid var(--line);padding:0 22px}}.tabs{{display:flex;gap:22px;height:40px;align-items:flex-end}}.tabbtn{{border:0;background:transparent;padding:0 0 9px;color:#71717a;font-size:12px;font-weight:700;cursor:pointer;border-bottom:2px solid transparent}}.tabbtn.active{{color:#18181b;border-bottom-color:#18181b}}.content{{padding:10px 22px 18px;max-width:1440px;margin:0 auto}}.page{{display:none}}.page.active{{display:block}}.cards{{display:flex;gap:7px;margin-bottom:9px;overflow-x:auto;flex-wrap:nowrap;scrollbar-width:none}}.cards::-webkit-scrollbar{{display:none}}.card{{background:#fff;border:1px solid var(--line);border-radius:9px;padding:9px 11px;min-height:0;flex:1 1 0;min-width:0}}.label{{font-size:9px;color:var(--muted);margin-bottom:3px}}.value{{font-size:16px;font-weight:750;line-height:1.15;overflow-wrap:anywhere}}.sub{{font-size:9px;color:var(--muted);margin-top:2px}}.positive{{color:var(--green)}}.panel{{background:#fff;border:1px solid var(--line);border-radius:11px;overflow:hidden;margin-bottom:11px}}.panel-head{{padding:12px 14px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px}}.panel-title{{font-size:13px;font-weight:700}}.panel-meta{{font-size:10px;color:var(--muted);margin-top:2px}}.table-wrap{{overflow:auto}}table{{width:100%;border-collapse:collapse;font-size:12px}}th{{padding:9px 11px;background:#fafafa;border-bottom:1px solid var(--line);text-align:left;font-size:10px;color:#71717a;text-transform:uppercase;letter-spacing:.03em;white-space:nowrap}}td{{padding:11px;border-bottom:1px solid #f0f0f1;white-space:nowrap;vertical-align:top}}tbody tr:last-child td{{border-bottom:0}}.mono{{font-family:"SFMono-Regular",Consolas,monospace;font-size:11px}}.muted{{color:var(--muted)}}.badge{{display:inline-flex;padding:4px 7px;border-radius:999px;font-size:10px;font-weight:750;border:1px solid transparent}}.badge.live{{background:#18181b;color:#fff}}.badge.test{{background:#fff;color:#52525b;border-color:#d4d4d8}}.badge.green{{background:var(--greenbg);color:var(--green);border-color:#dcfce7}}.badge.blue{{background:var(--bluebg);color:var(--blue);border-color:#dbeafe}}.badge.amber{{background:var(--amberbg);color:var(--amber);border-color:#fef3c7}}.badge.gray{{background:#f4f4f5;color:#52525b;border-color:#e4e4e7}}.filters{{display:flex;gap:8px;align-items:center;flex-wrap:wrap}}.search,select{{border:1px solid var(--line2);background:#fff;border-radius:8px;padding:8px 10px;font-size:12px;outline:none}}.search{{min-width:220px}}.button{{border:1px solid var(--line2);background:#fff;padding:8px 10px;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer}}.button.dark{{background:#18181b;color:#fff;border-color:#18181b}}.button:disabled{{opacity:.45;cursor:not-allowed}}.panel-actions{{display:flex;gap:7px;align-items:center}}.linkbtn{{border:0;background:transparent;padding:0;color:#18181b;text-decoration:underline;text-decoration-color:#a1a1aa;text-underline-offset:3px;font:inherit;font-weight:700;cursor:pointer}}.set-detail{{display:grid;grid-template-columns:1fr 1fr;gap:10px 16px;margin-bottom:12px}}.set-rules{{display:flex;flex-direction:column;gap:8px}}.set-rule{{display:flex;justify-content:space-between;gap:10px;padding:9px 10px;border:1px solid var(--line);border-radius:8px;background:#fafafa;font-size:11px}}.activity{{padding:3px 14px 8px}}.activity-row{{display:grid;grid-template-columns:110px 1fr auto;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f1;font-size:12px}}.activity-row:last-child{{border-bottom:0}}.mobile-list{{display:none;gap:9px}}.mcard{{background:#fff;border:1px solid var(--line);border-radius:11px;padding:13px}}.mhead{{display:flex;justify-content:space-between;gap:10px;margin-bottom:10px}}.mtitle{{font-size:13px;font-weight:750}}.msub{{font-size:10px;color:var(--muted);margin-top:2px}}.mgrid{{display:grid;grid-template-columns:1fr 1fr;gap:8px 12px}}.fl{{font-size:9px;color:var(--muted);margin-bottom:2px}}.fv{{font-size:12px;font-weight:650;overflow-wrap:anywhere}}.drawer-bg{{display:none;position:fixed;inset:0;background:rgba(24,24,27,.18);z-index:50}}.drawer-bg.open{{display:block}}.drawer{{position:absolute;right:0;top:0;bottom:0;width:min(440px,95vw);background:#fff;padding:22px;overflow:auto}}.drawer-head{{display:flex;justify-content:space-between;gap:12px;margin-bottom:18px}}.drawer h2{{font-size:19px;margin:3px 0 7px}}.iconbtn{{width:32px;height:32px;border:1px solid var(--line);background:#fff;border-radius:8px;cursor:pointer}}.section{{padding:16px 0;border-top:1px solid var(--line)}}.section-title{{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin-bottom:10px}}.modal-bg{{display:none;position:fixed;inset:0;background:rgba(24,24,27,.22);z-index:60;padding:28px}}.modal-bg.open{{display:flex;align-items:flex-start;justify-content:center}}.modal{{width:min(1180px,100%);max-height:calc(100vh - 56px);overflow:auto;background:#fff;border-radius:12px;border:1px solid var(--line);box-shadow:0 20px 50px rgba(24,24,27,.14)}}.modal-head{{padding:14px 16px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px;position:sticky;top:0;background:#fff;z-index:2}}.modal-title{{font-size:14px;font-weight:750}}.modal-body{{padding:14px 16px}}.filter-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:14px}}.filter-field label{{display:block;font-size:10px;color:var(--muted);margin-bottom:4px}}.filter-field input,.filter-field select{{width:100%;border:1px solid var(--line2);border-radius:8px;padding:8px 9px;font-size:12px;background:#fff}}.modal-actions{{display:flex;gap:8px;justify-content:flex-end;margin-top:10px}}@media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr)}}}}@media(max-width:760px){{body{{background:#fff}}.app{{display:block}}.main{{padding-bottom:0}}.toolbar{{height:54px;padding:0 12px}}.brand-top{{font-size:14px}}.utility-actions{{gap:5px}}.utility-btn{{padding:5px 7px;font-size:10px}}.tabsbar{{padding:0 12px}}.tabs{{height:38px;gap:18px}}.tabbtn{{font-size:11px;padding-bottom:8px}}.content{{padding:8px 10px 12px}}.cards{{display:flex;gap:6px;overflow-x:auto;flex-wrap:nowrap;padding-bottom:2px;scrollbar-width:none}}.card{{flex:0 0 132px;min-width:132px;padding:8px 9px}}.value{{font-size:15px}}.desktop-table{{display:none}}.mobile-list{{display:grid}}.panel{{margin-bottom:11px}}.panel-head{{padding:10px 11px}}.activity{{padding:0 11px 6px}}.activity-row{{grid-template-columns:70px 1fr;font-size:11px}}.activity-row>:last-child{{display:none}}.filters{{width:100%}}.search{{width:100%;min-width:0}}.panel-actions{{gap:5px}}.panel-actions .button{{padding:6px 8px;font-size:10px}}.modal-bg{{padding:0}}.modal{{width:100%;height:100%;max-height:none;border-radius:0}}.filter-grid{{grid-template-columns:1fr 1fr}}.drawer{{width:100%;padding:16px}}.set-detail{{grid-template-columns:1fr 1fr}}.set-rule{{display:block}}.set-rule span{{display:block}}.set-rule span+span{{margin-top:4px;color:var(--muted)}}}}
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
