r"""Server-rendered product UI shell for the approved TriggerTrade dashboard.

The HTML is adapted from the approved local file
C:\Users\Елена\Desktop\triggertrade_research_interactive_v4.html.
Fixture values inside the shell are non-persistent UI fixtures used only until the
corresponding read-model contracts are wired; trading decisions are never made here.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from html import escape
import re
from typing import Any

_ALLOWED_PAGES = {
    "portfolio",
    "sets",
    "trigger-catalog",
    "trigger-detail",
    "rules",
    "rules-version",
    "research",
    "research-detail",
    "messages",
}

_PRODUCT_UI_HTML = '<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8"/>\n<meta name="viewport" content="width=device-width,initial-scale=1"/>\n<title>TriggerTrade — Live UX concept</title>\n<style>\n:root{\n  --bg:#f6f7f9; --panel:#fff; --text:#19191b; --muted:#74747c; --line:#e5e5e8; --line2:#d5d5d9;\n  --green:#16783c; --green-bg:#eef9f2; --red:#b42318; --red-bg:#fff1f0; --blue:#2457d6; --blue-bg:#eef4ff;\n  --amber:#9a6700; --amber-bg:#fff8e6; --page:1460px; --pad:22px;\n}\n*{box-sizing:border-box}\nhtml,body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}\nbutton,input,select{font:inherit}\n.container{max-width:var(--page);margin:0 auto;padding:0 var(--pad)}\n.top{position:sticky;top:0;z-index:30;background:#fff;border-bottom:1px solid var(--line)}\n.topin{height:58px;display:flex;align-items:center;justify-content:space-between}\n.brand{font-size:15px;font-weight:820;letter-spacing:-.01em;display:flex;align-items:center;gap:9px}\n.live-dot{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 0 4px var(--green-bg)}\n.actions{display:flex;align-items:center;gap:8px}\n.badge{display:inline-flex;align-items:center;padding:4px 7px;border-radius:999px;border:1px solid transparent;font-size:10px;font-weight:800;white-space:nowrap}\n.badge.live{background:#171719;color:#fff}.badge.green{background:var(--green-bg);color:var(--green);border-color:#d8f0df}\n.badge.red{background:var(--red-bg);color:var(--red);border-color:#ffd4cf}.badge.blue{background:var(--blue-bg);color:var(--blue);border-color:#dce7ff}\n.badge.gray{background:#f4f4f5;color:#53535a;border-color:#e5e5e8}.badge.amber{background:var(--amber-bg);color:var(--amber);border-color:#f4e4ad}\n.btn{border:1px solid var(--line2);background:#fff;border-radius:8px;padding:7px 10px;font-size:11px;font-weight:750;color:#3f3f46;cursor:pointer}\n.btn.red{background:var(--red);color:#fff;border-color:var(--red)}\n.tabsbar{position:sticky;top:58px;z-index:29;background:#fff;border-bottom:1px solid var(--line)}\n.tabs{height:41px;display:flex;align-items:flex-end;gap:23px}\n.tab{border:0;background:transparent;padding:0 0 9px;border-bottom:2px solid transparent;color:var(--muted);font-size:12px;font-weight:760;cursor:pointer}\n.tab.active{color:var(--text);border-bottom-color:var(--text)}\nmain{padding-top:12px;padding-bottom:30px}.page{display:none}.page.active{display:block}\n.pagehead{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:10px}\n.pagetitle{font-size:17px;font-weight:800;letter-spacing:-.02em}.pagesub{font-size:10px;color:var(--muted);margin-top:2px}\n.kpis{display:flex;gap:7px;overflow:auto;margin-bottom:10px;scrollbar-width:none}.kpis::-webkit-scrollbar{display:none}\n.kpi{background:#fff;border:1px solid var(--line);border-radius:9px;padding:10px 11px;flex:1 1 0;min-width:155px}\n.klabel{font-size:9px;color:var(--muted);margin-bottom:4px}.kvalue{font-size:17px;font-weight:800;letter-spacing:-.015em}.ksub{font-size:9px;color:var(--muted);margin-top:4px}\n.pos{color:var(--green)}.neg{color:var(--red)}\n.panel{background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-bottom:10px}\n.panelhead{padding:11px 13px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:10px}\n.title{font-size:13px;font-weight:760}.meta{font-size:10px;color:var(--muted);margin-top:2px}\n.moneybar{display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr;gap:0}\n.moneyitem{padding:13px;border-right:1px solid var(--line)}.moneyitem:last-child{border-right:0}\n.mlabel{font-size:9px;color:var(--muted);margin-bottom:3px}.mval{font-size:14px;font-weight:760}.mnote{font-size:9px;color:var(--muted);margin-top:3px}\n.attn{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:10px 12px}\n.attn-card{border:1px solid var(--line);border-radius:8px;padding:9px 10px;background:#fafafa}\n.attn-title{font-size:10px;font-weight:760}.attn-text{font-size:10px;color:var(--muted);margin-top:3px;line-height:1.35}\n.filters{display:flex;gap:7px;align-items:center;flex-wrap:wrap}\n.segment{display:inline-flex;border:1px solid var(--line2);border-radius:8px;padding:2px;background:#f7f7f8}\n.segment button{border:0;background:transparent;border-radius:6px;padding:5px 9px;font-size:10px;font-weight:800;color:#76767d;cursor:pointer}\n.segment button.active{background:#fff;color:#222;box-shadow:0 1px 2px rgba(0,0,0,.07)}\n.search,select{border:1px solid var(--line2);background:#fff;border-radius:8px;padding:7px 9px;font-size:11px;color:#3f3f46}\n.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:12px}\nth{padding:8px 10px;background:#fafafa;border-bottom:1px solid var(--line);text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);white-space:nowrap}\ntd{padding:10px;border-bottom:1px solid #f0f0f1;white-space:nowrap;vertical-align:middle}tbody tr:last-child td{border-bottom:0}\n.coin{font-weight:750}.link{border:0;background:transparent;padding:0;text-decoration:underline;text-decoration-color:#a1a1aa;text-underline-offset:3px;font-weight:760;cursor:pointer}\n.summaryline{display:flex;gap:18px;align-items:center;flex-wrap:wrap;font-size:10px;color:var(--muted)}\n.summaryline b{font-size:11px;color:var(--text)}\n.placeholder{padding:50px 20px;text-align:center;color:var(--muted);font-size:11px}\n.modalbg{display:none;position:fixed;inset:0;background:rgba(24,24,27,.22);z-index:60}.modalbg.open{display:block}\n.modal{width:min(650px,calc(100% - 28px));margin:80px auto;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}\n.modalbody{padding:15px}.notice{background:var(--amber-bg);border:1px solid #f4e4ad;border-radius:8px;padding:10px;font-size:11px}\n.modalactions{display:flex;justify-content:flex-end;gap:8px;margin-top:14px}\n@media(max-width:850px){.moneybar{grid-template-columns:1fr 1fr}.moneyitem:nth-child(2){border-right:0}.moneyitem:nth-child(-n+2){border-bottom:1px solid var(--line)}.attn{grid-template-columns:1fr}}\n@media(max-width:620px){:root{--pad:12px}.topin{height:auto;min-height:54px;padding-block:8px}.actions .badge.green{display:none}.tabs{gap:20px}.kpi{flex:0 0 145px;min-width:145px}.pagehead{flex-direction:column}.moneybar{grid-template-columns:1fr 1fr}.panelhead{align-items:flex-start;flex-direction:column}.filters{width:100%}}\n\n.icon-action{\n  border:0;background:transparent;color:#65656d;width:30px;height:30px;border-radius:7px;\n  display:inline-grid;place-items:center;font-size:15px;cursor:pointer;padding:0\n}\n.icon-action:hover{background:#f4f4f5;color:#222}\n.subtle-status{justify-content:flex-end;margin-bottom:8px;gap:10px;font-size:9px;color:#a1a1aa}\n.positions-right{display:flex;align-items:center;gap:14px;flex-wrap:wrap;justify-content:flex-end}\n.danger-actions{display:flex;align-items:center;gap:5px}\n.danger-actions .btn{padding:6px 8px;font-size:10px}\n.stop-new{color:#8a5a00;border-color:#e7d5a2;background:#fffdf6}\n.close-all{color:var(--red);border-color:#efb9b4;background:#fff}\n.confirm-field{margin-top:12px}\n.confirm-field label{display:block;font-size:10px;color:var(--muted);margin-bottom:5px}\n.confirm-field input{width:100%}\n.row-close{\n  border:1px solid #efb9b4;background:#fff;color:var(--red);border-radius:7px;\n  padding:4px 7px;font-size:9px;font-weight:800;cursor:pointer\n}\n.row-close:hover{background:var(--red-bg)}\n\n\n.summaryline b.pos{color:var(--green)}\n.summaryline b.neg{color:var(--red)}\n\n\n.detail-top{margin-bottom:9px}\n.back-link{border:0;background:transparent;padding:0;color:#62626a;font-size:11px;font-weight:750;cursor:pointer}\n.back-link:hover{text-decoration:underline;text-underline-offset:3px}\n.detail-actions{display:flex;align-items:center;gap:7px}\n.detail-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-top:0}\n.detail-grid>div{padding:12px 13px;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}\n.detail-grid>div:nth-child(3n){border-right:0}\n.detail-value{font-size:12px;font-weight:680}\n.detail-note{padding:13px;font-size:12px}\n.logic-body{padding:13px}\n.formula-block{font-family:Consolas,monospace;font-size:11px;line-height:1.55;background:#fafafa;border:1px solid var(--line);border-radius:8px;padding:11px;white-space:pre-wrap}\n@media(max-width:760px){\n  .detail-grid{grid-template-columns:1fr 1fr}\n  .detail-grid>div:nth-child(3n){border-right:1px solid var(--line)}\n  .detail-grid>div:nth-child(2n){border-right:0}\n}\n\n\n.parameter-editor{border-top:1px solid var(--line);padding:12px 13px;background:#fcfcfd}\n.parameter-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}\n.parameter-grid label{font-size:9px;color:var(--muted);display:grid;gap:5px}\n.parameter-grid input{border:1px solid var(--line2);border-radius:8px;padding:7px 8px;font-size:11px;background:#fff;color:var(--text)}\n.parameter-actions{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:10px}\n.parameter-note{font-size:9px;color:var(--muted)}\n@media(max-width:760px){\n  .tabsbar{top:54px}\n  .parameter-grid{grid-template-columns:1fr}\n}\n\n\n.set-simple-grid{grid-template-columns:repeat(3,1fr)}\n.logic-choice{display:flex;gap:14px;align-items:center;padding:13px}\n.logic-choice label{font-size:11px;font-weight:700;display:flex;gap:6px;align-items:center}\n.explain-text{font-size:11px;line-height:1.5;margin-bottom:10px;color:#4b4b52}\n.coins-list{display:flex;gap:6px;flex-wrap:wrap;padding:13px}\n.coin-chip{display:inline-flex;padding:5px 8px;border:1px solid var(--line);border-radius:7px;background:#fafafa;font-size:10px;font-weight:700}\n@media(max-width:760px){\n  .set-simple-grid{grid-template-columns:1fr}\n  .logic-choice{flex-wrap:wrap}\n}\n\n\n.trigger-list{display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center}\n\n\n.used-in-list{display:grid;gap:4px;justify-items:start}\n.tiny-state{font-size:8px;font-weight:800;letter-spacing:.02em;margin-left:5px}\n.tiny-state.active{color:var(--green)}\n.tiny-state.testing{color:var(--blue)}\n.tiny-state.archived{color:#8a8a91}\n\n\n.message-action{position:relative}\n.message-count{\n  position:absolute;top:-3px;right:-7px;min-width:18px;height:15px;padding:0 4px;border-radius:999px;\n  background:var(--blue);color:#fff;font-size:8px;font-weight:800;line-height:15px;text-align:center;\n  box-shadow:0 0 0 2px #fff\n}\n\n\n#sets{padding-top:8px}\n\n\n.catalog-entry{margin-top:8px}\n.catalog-button{\n  width:100%;border:1px solid var(--line);background:#fff;border-radius:10px;padding:11px 13px;\n  display:flex;align-items:center;justify-content:space-between;color:var(--text);\n  font-size:11px;font-weight:760;cursor:pointer\n}\n.catalog-button:hover{background:#fafafa}\n.catalog-arrow{color:#8b8b93;font-size:14px}\n\n\n.subtle-status{\n  min-height:24px;\n  margin:2px 0 10px;\n  display:flex;\n  align-items:center;\n  justify-content:flex-end;\n  color:#9a9aa2;\n  font-size:9px;\n}\n\n#sets{padding-top:12px}\n\n.rules-grid{\n  display:grid;\n  grid-template-columns:repeat(3,1fr);\n  gap:10px;\n  padding-top:10px;\n}\n.rules-span{grid-column:1 / -1}\n.rule-form{display:grid}\n.rule-row{\n  display:grid;\n  grid-template-columns:1fr auto;\n  gap:18px;\n  align-items:center;\n  padding:12px 13px;\n  border-bottom:1px solid #f0f0f1;\n}\n.rule-row:last-child{border-bottom:0}\n.rule-name{font-size:11px;font-weight:760}\n.rule-desc{font-size:9px;color:var(--muted);margin-top:3px}\n.rule-control input,\n.rule-control select{\n  width:112px;\n  border:1px solid var(--line2);\n  background:#fff;\n  border-radius:8px;\n  padding:7px 8px;\n  font-size:11px;\n  color:var(--text);\n}\n.suffix-control{\n  position:relative;\n}\n.suffix-control input{padding-right:28px}\n.suffix-control span{\n  position:absolute;\n  right:9px;\n  top:50%;\n  transform:translateY(-50%);\n  color:#888;\n  font-size:10px;\n  pointer-events:none;\n}\n.rule-actions{display:flex;gap:6px;align-items:center}\n.coins-editor{\n  border-top:1px solid var(--line);\n  background:#fcfcfd;\n  padding:12px 13px;\n}\n.coins-toolbar{\n  display:flex;\n  gap:8px;\n  align-items:center;\n  margin-bottom:10px;\n}\n.coins-toolbar .search{flex:1;max-width:320px}\n.coin-options{\n  display:grid;\n  grid-template-columns:repeat(5,1fr);\n  gap:7px;\n}\n.coin-options label{\n  border:1px solid var(--line);\n  background:#fff;\n  border-radius:8px;\n  padding:8px 9px;\n  font-size:10px;\n  display:flex;\n  align-items:center;\n  gap:6px;\n}\n.coins-footer{\n  display:flex;\n  align-items:center;\n  justify-content:space-between;\n  gap:10px;\n  margin-top:10px;\n}\n.rules-footer{\n  grid-column:1 / -1;\n  display:flex;\n  justify-content:flex-end;\n  align-items:center;\n  gap:10px;\n  padding:2px 0 4px;\n}\n.rules-save-state{font-size:9px;color:var(--muted)}\n.primary-rule{\n  background:#18181b;\n  color:#fff;\n  border-color:#18181b;\n}\n.primary-rule:hover{background:#27272a}\n\n@media(max-width:900px){\n  .rules-grid{grid-template-columns:1fr}\n  .rules-span,.rules-footer{grid-column:auto}\n  .coin-options{grid-template-columns:repeat(3,1fr)}\n}\n@media(max-width:620px){\n  .coin-options{grid-template-columns:repeat(2,1fr)}\n  .rule-row{grid-template-columns:1fr}\n  .rule-control input,.rule-control select{width:100%}\n  .coins-toolbar{flex-direction:column;align-items:stretch}\n  .coins-toolbar .search{max-width:none}\n}\n\n\n.rule-required{\n  display:inline-block;margin-left:6px;font-size:8px;font-weight:800;color:#77777f;\n  vertical-align:1px\n}\n.mini-toggle{display:inline-flex;vertical-align:middle;margin-left:7px;cursor:pointer}\n.mini-toggle input{display:none}\n.mini-toggle span{\n  width:25px;height:14px;border-radius:999px;background:#d8d8dd;display:block;position:relative;transition:.15s\n}\n.mini-toggle span:after{\n  content:"";position:absolute;width:10px;height:10px;border-radius:50%;background:#fff;left:2px;top:2px;\n  box-shadow:0 1px 2px rgba(0,0,0,.18);transition:.15s\n}\n.mini-toggle input:checked + span{background:#18181b}\n.mini-toggle input:checked + span:after{left:13px}\n.coin-options label{justify-content:space-between}\n.coin-options label>span:first-child{display:flex;align-items:center;gap:6px}\n.coin-limit{display:flex;align-items:center;gap:3px;color:#888;font-size:9px}\n.coin-limit input{\n  width:42px;border:0;border-bottom:1px solid var(--line2);border-radius:0;padding:2px 1px;\n  background:transparent;font-size:9px;text-align:right\n}\n.coin-chip small{font-size:8px;color:#8a8a91;margin-left:3px}\n\n\n.rr-control{position:relative}\n.rr-control input{\n  width:112px;\n  border:1px solid var(--line2);\n  background:#fff;\n  border-radius:8px;\n  padding:7px 34px 7px 8px;\n  font-size:11px;\n  color:var(--text);\n}\n.rr-control span{\n  position:absolute;\n  right:9px;\n  top:50%;\n  transform:translateY(-50%);\n  color:#888;\n  font-size:10px;\n  pointer-events:none;\n}\n\n\n#research{padding-top:10px}\n.research-toolbar{\n  display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px\n}\n.research-selects{display:flex;gap:7px;flex-wrap:wrap}\n.research-selects select{\n  border:1px solid var(--line2);background:#fff;border-radius:8px;padding:7px 9px;font-size:11px\n}\n.research-stages{\n  display:grid;\n  grid-template-columns:1fr auto 1fr auto 1fr;\n  align-items:center;\n  gap:8px;\n  margin-bottom:10px\n}\n.stage-card{\n  background:#fff;border:1px solid var(--line);border-radius:10px;padding:11px 12px;\n  display:grid;grid-template-columns:auto 1fr auto;gap:9px;align-items:center\n}\n.stage-card.active-stage{border-color:#d7e6da}\n.stage-kicker{\n  width:22px;height:22px;border-radius:50%;background:#f4f4f5;color:#666;display:grid;place-items:center;\n  font-size:9px;font-weight:800\n}\n.stage-name{font-size:11px;font-weight:780}\n.stage-status{font-size:9px;color:var(--muted);margin-top:2px}\n.stage-arrow{font-size:15px;color:#b0b0b7}\n.research-panel-actions{display:flex;gap:6px}\n.research-kpis{\n  display:grid;grid-template-columns:repeat(6,1fr);border-bottom:1px solid var(--line)\n}\n.research-kpi{padding:11px 12px;border-right:1px solid var(--line)}\n.research-kpi:last-child{border-right:0}\n.research-value{font-size:13px;font-weight:760}\n.progress-line{padding:12px 13px}\n.progress-labels{display:flex;justify-content:space-between;font-size:9px;color:var(--muted);margin-bottom:6px}\n.progress-track{height:6px;background:#f0f0f1;border-radius:999px;overflow:hidden}\n.progress-track span{display:block;height:100%;background:#18181b}\n.demo-empty{padding:22px 13px}\n.demo-empty-title{font-size:12px;font-weight:760}\n.demo-empty-meta{font-size:9px;color:var(--muted);margin-top:4px}\n.muted-row{color:#9a9aa2}\n@media(max-width:1000px){\n  .research-kpis{grid-template-columns:repeat(3,1fr)}\n  .research-kpi:nth-child(3){border-right:0}\n}\n@media(max-width:760px){\n  .research-toolbar{align-items:stretch;flex-direction:column}\n  .research-stages{display:flex;overflow:auto}\n  .stage-card{min-width:220px}\n  .stage-arrow{flex:0 0 auto}\n  .research-kpis{grid-template-columns:repeat(2,1fr)}\n  .research-kpi:nth-child(3){border-right:1px solid var(--line)}\n  .research-kpi:nth-child(2n){border-right:0}\n}\n\n\n#research{padding-top:10px}\n.research-list{margin-bottom:10px}\n.research-detail{display:none}\n.research-detail.open{display:block}\n.research-detail-head{display:flex;align-items:center;gap:14px;margin:2px 0 10px}\n.research-detail-title{font-size:13px;font-weight:800}\n.research-flow{\n  display:grid;\n  grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;\n  gap:8px;\n  align-items:center;\n  margin-bottom:10px\n}\n.research-flow-step{\n  background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 12px\n}\n.research-flow-step.done{border-color:#d8eddc;background:#fbfffc}\n.research-flow-step.active{border-color:#d9e5ff;background:#fbfdff}\n.flow-label{font-size:10px;font-weight:800}\n.flow-state{font-size:9px;color:var(--muted);margin-top:2px}\n.flow-arrow{color:#b2b2b8}\n.research-panel-actions{display:flex;gap:6px}\n.research-kpis{\n  display:grid;\n  grid-template-columns:repeat(6,1fr);\n  border-bottom:1px solid var(--line)\n}\n.research-kpi{padding:11px 12px;border-right:1px solid var(--line)}\n.research-kpi:last-child{border-right:0}\n.research-value{font-size:13px;font-weight:760}\n.demo-table-head{padding:10px 13px;border-bottom:1px solid var(--line)}\n.compare-head,.compare-row{\n  display:grid;\n  grid-template-columns:1.2fr 1fr 1fr 1fr;\n  gap:0;\n}\n.compare-head{background:#fafafa;border-bottom:1px solid var(--line)}\n.compare-head>div,.compare-row>div{padding:9px 11px;border-right:1px solid #f0f0f1}\n.compare-head>div:last-child,.compare-row>div:last-child{border-right:0}\n.compare-label{font-size:9px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}\n.compare-row{border-bottom:1px solid #f0f0f1;font-size:11px}\n.compare-row:last-child{border-bottom:0}\n.decision-actions{display:flex;gap:7px;justify-content:flex-end;padding:12px 13px;flex-wrap:wrap}\n@media(max-width:980px){\n  .research-kpis{grid-template-columns:repeat(3,1fr)}\n  .research-kpi:nth-child(3){border-right:0}\n}\n@media(max-width:760px){\n  .research-flow{display:flex;overflow:auto}\n  .research-flow-step{min-width:170px}\n  .flow-arrow{flex:0 0 auto}\n  .research-kpis{grid-template-columns:repeat(2,1fr)}\n  .research-kpi:nth-child(3){border-right:1px solid var(--line)}\n  .research-kpi:nth-child(2n){border-right:0}\n  .compare-head,.compare-row{grid-template-columns:1fr 1fr 1fr 1fr;min-width:620px}\n  .decision-actions{justify-content:flex-start}\n}\n\n\n.run-use-head,.run-use-cell{width:46px;text-align:center!important}\n.run-use-cell input[type="radio"]{width:14px;height:14px;accent-color:#18181b;cursor:pointer}\n.research-runs-table th.run-use-head{padding-left:6px;padding-right:6px}\n.research-runs-table td.run-use-cell{padding-left:6px;padding-right:6px}\n</style>\n<style>\n\n.current-rules-heading{\n  display:flex;\n  align-items:center;\n  font-size:13px;\n  font-weight:500;\n  color:#19191b;\n  letter-spacing:-.005em;\n  margin:0;\n}\n#rules .rules-topbar{\n  min-height:26px;\n  display:flex;\n  align-items:center;\n  margin:0 0 5px;\n}\n#rules .rules-topbar .current-rules-heading{padding-left:13px}\n#rules .rules-bottom-actions{\n  grid-column:1 / -1;\n  display:flex;\n  align-items:center;\n  justify-content:flex-end;\n  gap:10px;\n  min-height:30px;\n  margin-top:-2px;\n  margin-bottom:2px;\n}\n#rules .rules-grid,#rules-version .rules-grid{grid-template-columns:minmax(0,1fr) minmax(0,1fr) minmax(250px,.68fr);align-items:start;column-gap:12px;row-gap:6px;padding-top:4px}\n#rules .rules-span,#rules-version .rules-span{grid-column:1/-1}\n#rules .coins-list,#rules-version .coins-list{display:grid;grid-template-columns:1fr;gap:5px;padding:8px 10px}\n#rules .coin-chip,#rules-version .coin-chip{justify-content:space-between;align-items:center;min-height:30px;padding:6px 9px;font-size:10px;background:#fff}\n#rules .coin-chip small,#rules-version .coin-chip small{font-size:10px;font-weight:800;color:#3f3f46;background:#f4f4f5;border:1px solid #e5e5e8;border-radius:999px;padding:3px 7px;margin-left:10px;line-height:1}\n#rules .coins-toolbar{flex-direction:column;align-items:stretch}\n#rules .coins-toolbar .search{max-width:none}\n#rules .coin-options{grid-template-columns:1fr}\n#rules .coin-limit{font-size:10px;font-weight:750;color:#4b4b52}\n#rules .coin-limit input{width:48px;font-size:10px;font-weight:750}\n@media(max-width:1180px){#rules .rules-grid,#rules-version .rules-grid,#rules .rules-topbar{grid-template-columns:minmax(0,1fr) minmax(0,1fr) minmax(230px,.72fr)}}\n@media(max-width:1000px){#rules .rules-grid,#rules-version .rules-grid,#rules .rules-topbar{grid-template-columns:1fr 1fr}#rules .rules-grid>.panel:nth-of-type(3),#rules-version .rules-grid>.panel:nth-of-type(3){grid-column:1/-1}#rules .coins-list,#rules-version .coins-list{grid-template-columns:repeat(3,minmax(0,1fr))}}\n@media(max-width:760px){#rules .rules-grid,#rules-version .rules-grid,#rules .rules-topbar{grid-template-columns:1fr}#rules .rules-grid>.panel:nth-of-type(3),#rules-version .rules-grid>.panel:nth-of-type(3){grid-column:auto}#rules .coins-list,#rules-version .coins-list{grid-template-columns:1fr 1fr}}\n@media(max-width:520px){#rules .coins-list,#rules-version .coins-list{grid-template-columns:1fr}}\n@media(max-width:760px){#rules .rules-topbar{min-height:44px}}\n#rules-version .readonly-control input,#rules-version .readonly-control select{pointer-events:none;background:#fafafa;color:#4b4b52}\n#rules-version .readonly-control .mini-toggle{pointer-events:none}\n#rules-version \n#rules .rule-row,#rules-version .rule-row{padding:9px 13px}\n#rules .panelhead,#rules-version .panelhead{padding:9px 13px}\n#rules .version-history-table{margin-top:5px !important;margin-bottom:4px !important}\n.rules-version-header{\n  display:flex;\n  align-items:flex-start;\n  padding:10px 13px;\n  margin:0 0 10px;\n}\n#rules-version .rules-version-header-inner{\n  display:flex;\n  flex-direction:column;\n  gap:10px;\n}\n#rules-version .rules-version-header .current-rules-heading{height:auto;min-height:0;margin:0;font-size:13px;font-weight:500;color:#19191b;line-height:1.2}\n#rules-version .rules-version-header .pagesub{margin:0;line-height:1.2}\n#rules-version .version-context{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:0;font-size:9px;color:var(--muted);line-height:1.2}\n</style>\n\n<style id="research-summary-refine">\n#research .research-summary-panel{margin-top:10px}\n#research .research-summary-table{table-layout:fixed}\n#research .research-summary-table th:nth-child(1){width:16%}\n#research .research-summary-table th:nth-child(2){width:14%}\n#research .research-summary-table th:nth-child(3){width:18%}\n#research .research-summary-table th:nth-child(4){width:18%}\n#research .research-summary-table th:nth-child(5){width:20%}\n#research .research-summary-table th:nth-child(6){width:14%}\n#research .research-summary-table th{padding-top:10px;padding-bottom:10px}\n#research .research-summary-table td{height:60px;padding:9px 10px}\n#research .research-summary-table tbody tr{cursor:pointer}\n#research .research-summary-table tbody tr:hover{background:#fafafa}\n#research .research-summary-table tbody tr:focus-within{background:#fafafa}\n.pf-cell{display:grid;gap:2px;justify-items:start}\n.pf-trades{font-size:9px;color:var(--muted);font-weight:650}\n.research-object-link{border:0;background:transparent;padding:0;display:inline-flex;align-items:baseline;gap:6px;color:var(--text);font-weight:760;cursor:pointer;text-decoration:underline;text-decoration-color:#a1a1aa;text-underline-offset:3px}\n.research-object-link small{font-size:9px;font-weight:700;color:var(--muted);text-decoration:none}\n.research-object-link:hover{text-decoration-color:#18181b}\n.pf-value{font-size:13px;font-weight:800;letter-spacing:-.01em;color:var(--text)}\n.pf-value.weak{color:var(--red)}\n.pf-empty{color:#aaaab1}\n.compare-result,.decision-status{display:inline-flex;align-items:center;min-height:22px;padding:4px 7px;border-radius:7px;font-size:9px;font-weight:800;white-space:nowrap;border:1px solid transparent}\n.compare-result.better{color:var(--green);background:var(--green-bg);border-color:#d8f0df}\n.compare-result.muted{color:#74747c;background:#f6f6f7;border-color:#e8e8eb}\n.decision-status.attention{color:var(--amber);background:var(--amber-bg);border-color:#f4e4ad}\n.decision-status.running{color:var(--blue);background:var(--blue-bg);border-color:#dce7ff}\n.decision-status.neutral{color:#56565d;background:#f4f4f5;border-color:#e5e5e8}\n.decision-status.archived{color:#7c7c83;background:#f7f7f8;border-color:#e8e8eb}\n@media(max-width:900px){#research .research-summary-table{min-width:860px}}\n</style>\n\n<style id="research-detail-compact-refine">\n#research .research-detail-object-head{display:flex;align-items:center;gap:8px;margin:4px 0 10px;padding:0 1px;min-height:28px}\n#research .research-detail-object-link{border:0;background:transparent;padding:0;color:var(--text);font-size:13px;font-weight:600;cursor:pointer;text-decoration:underline;text-decoration-color:#a1a1aa;text-underline-offset:3px}\n#research .research-detail-separator{color:#a1a1aa;font-size:12px}\n#research .research-runs-panel .panelhead{padding:9px 12px}\n#research .research-runs-table th{padding:7px 10px}\n#research .research-runs-table td{padding:8px 10px;height:38px}\n#research .research-runs-table .latest-run{background:#fcfcfd}\n#research .latest-run-label{display:inline-block;margin-left:7px;font-size:8px;font-weight:800;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}\n#research .research-flow{margin-bottom:10px}\n#research .research-flow-step{padding:9px 11px}\n</style>\n\n\n\n\n\n\n\n\n\n\n<style id="research-table-sync">\n#researchDetail .research-run-table{\n  width:100%;\n  table-layout:fixed;\n}\n\n/* Balanced widths across both Backtest and Demo. */\n#researchDetail .research-run-table col.run{width:10%}\n#researchDetail .research-run-table col.status{width:9%}\n#researchDetail .research-run-table col.period{width:14%}\n#researchDetail .research-run-table col.trades{width:11%}\n#researchDetail .research-run-table col.pnl{width:12%}\n#researchDetail .research-run-table col.winrate{width:11%}\n#researchDetail .research-run-table col.pf{width:12%}\n#researchDetail .research-run-table col.dd{width:14%}\n#researchDetail .research-run-table col.use{width:7%}\n\n#researchDetail .research-run-table th,\n#researchDetail .research-run-table td{\n  box-sizing:border-box;\n  white-space:nowrap;\n  overflow:hidden;\n  text-overflow:ellipsis;\n  text-align:center !important;\n  vertical-align:middle;\n}\n\n/* Keep status visually quiet. */\n#researchDetail .run-status{\n  display:inline;\n  padding:0;\n  border:0;\n  background:transparent;\n  border-radius:0;\n  box-shadow:none;\n  font-size:9px;\n  line-height:1.2;\n  font-weight:500;\n  letter-spacing:0;\n  color:#77777f;\n}\n#researchDetail .run-status.running{color:#2457d6}\n#researchDetail .run-status.draft{color:#8a8a91}\n#researchDetail .run-status.completed{color:#6f6f76}\n\n#researchDetail .latest-tag{\n  margin-left:5px;\n  font-size:8px;\n  font-weight:600;\n  color:#9a9aa2;\n  letter-spacing:.02em;\n  text-transform:uppercase;\n}\n</style>\n\n\n<style id="research-run-launch-css">\n.research-panel-actions .btn.run-primary{\n  background:#18181b;color:#fff;border-color:#18181b;\n}\n.run-modal{\n  width:min(520px,calc(100% - 28px));\n  margin:96px auto;\n  background:#fff;\n  border:1px solid var(--line);\n  border-radius:12px;\n  overflow:hidden;\n}\n.run-modal-head{\n  display:flex;\n  align-items:center;\n  justify-content:space-between;\n  padding:13px 15px;\n  border-bottom:1px solid var(--line);\n}\n.run-modal-body{padding:15px}\n.run-date-grid{\n  display:grid;\n  grid-template-columns:1fr 1fr;\n  gap:10px;\n}\n.run-date-grid label{\n  display:grid;\n  gap:5px;\n  font-size:9px;\n  color:var(--muted);\n}\n.run-date-grid input{\n  border:1px solid var(--line2);\n  background:#fff;\n  border-radius:8px;\n  padding:8px 9px;\n  font-size:11px;\n  color:var(--text);\n}\n.run-context{\n  margin-top:12px;\n  padding:9px 10px;\n  border:1px solid var(--line);\n  border-radius:8px;\n  background:#fafafa;\n  display:flex;\n  gap:12px 18px;\n  flex-wrap:wrap;\n  font-size:9px;\n  color:var(--muted);\n}\n.run-context b{color:#4b4b52;font-weight:650}\n.run-modal-actions{\n  display:flex;\n  justify-content:flex-end;\n  gap:8px;\n  margin-top:14px;\n}\n.run-status.inline-running{\n  color:#2457d6;\n}\n.run-spinner{\n  width:10px;\n  height:10px;\n  border:1.5px solid #cfd7eb;\n  border-top-color:#2457d6;\n  border-radius:50%;\n  display:inline-block;\n  vertical-align:-1px;\n  margin-right:5px;\n  animation:runSpin .7s linear infinite;\n}\n@keyframes runSpin{to{transform:rotate(360deg)}}\n@media(max-width:620px){\n  .run-date-grid{grid-template-columns:1fr}\n}\n</style>\n\n\n<style id="research-compare-refine">\n.backtest-model-note{\n  padding:6px 13px 9px;\n  font-size:8px;\n  line-height:1.35;\n  color:#9a9aa2;\n}\n.compare-row .diff-pos{color:var(--green);font-weight:650}\n.compare-row .diff-neg{color:var(--red);font-weight:650}\n.compare-row .diff-neutral{color:#6f6f76}\n.compare-head .compare-label{font-weight:700}\n</style>\n\n\n<style id="research-new-research-css">\n.research-toolbar-main{\n  display:flex;\n  align-items:center;\n  justify-content:space-between;\n  gap:12px;\n  margin-bottom:10px;\n}\n.research-toolbar-title{\n  font-size:13px;\n  font-weight:760;\n  color:var(--text);\n}\n.new-research-btn{\n  display:inline-flex;\n  align-items:center;\n  gap:7px;\n  border:1px solid var(--line2);\n  background:#fff;\n  color:var(--text);\n  border-radius:9px;\n  padding:7px 10px;\n  font-size:11px;\n  font-weight:760;\n  cursor:pointer;\n}\n.new-research-btn .plus{\n  width:18px;height:18px;border-radius:999px;border:1px solid var(--line2);\n  display:grid;place-items:center;font-size:13px;line-height:1;\n}\n.new-research-btn:hover{background:#fafafa}\n\n.research-create-modal{\n  width:min(520px,calc(100% - 28px));\n  margin:90px auto;\n  background:#fff;\n  border:1px solid var(--line);\n  border-radius:12px;\n  overflow:hidden;\n}\n.research-create-head{\n  display:flex;\n  align-items:center;\n  justify-content:space-between;\n  padding:13px 15px;\n  border-bottom:1px solid var(--line);\n}\n.research-create-body{padding:15px}\n.research-create-grid{\n  display:grid;\n  gap:12px;\n}\n.research-create-grid label{\n  display:grid;\n  gap:5px;\n  font-size:9px;\n  color:var(--muted);\n}\n.research-create-grid select{\n  border:1px solid var(--line2);\n  background:#fff;\n  border-radius:8px;\n  padding:8px 9px;\n  font-size:11px;\n  color:var(--text);\n}\n.research-create-note{\n  margin-top:11px;\n  font-size:9px;\n  color:var(--muted);\n  line-height:1.4;\n}\n.research-create-actions{\n  display:flex;\n  justify-content:flex-end;\n  gap:8px;\n  margin-top:14px;\n}\n\n.decision-compact{\n  display:flex;\n  align-items:center;\n  justify-content:space-between;\n  gap:14px;\n  padding:12px 13px;\n}\n.decision-left{\n  display:flex;\n  align-items:center;\n  gap:10px;\n  flex-wrap:wrap;\n}\n.decision-title-inline{\n  font-size:12px;\n  font-weight:760;\n  color:var(--text);\n}\n.decision-state-inline{\n  font-size:10px;\n  color:var(--muted);\n}\n.decision-actions-inline{\n  display:flex;\n  align-items:center;\n  gap:8px;\n  flex-wrap:wrap;\n}\n.decision-actions-inline .btn{\n  padding:7px 10px;\n}\n.decision-empty{\n  padding:12px 13px;\n  font-size:10px;\n  color:var(--muted);\n}\n@media(max-width:760px){\n  .research-toolbar-main{align-items:stretch;flex-direction:column}\n  .new-research-btn{justify-content:center}\n  .decision-compact{align-items:flex-start;flex-direction:column}\n  .decision-actions-inline{justify-content:flex-start}\n}\n</style>\n\n\n<style id="research-interactive-v2-css">\n.new-research-btn .plus{display:none!important}\n.new-research-btn{gap:0}\n.research-detail-topbar{\n  display:flex;\n  align-items:center;\n  justify-content:space-between;\n  gap:12px;\n  margin-bottom:8px;\n}\n.detail-new-research-btn{\n  flex:0 0 auto;\n}\n.empty-run-row td{\n  color:#8a8a91;\n  font-size:10px;\n  text-align:center !important;\n  padding:14px 10px;\n}\n.compare-empty{\n  padding:14px 13px;\n  font-size:10px;\n  color:#8a8a91;\n}\n.decision-state-inline.draft{color:#8a8a91}\n.decision-state-inline.running{color:#2457d6}\n.decision-state-inline.archived{color:#8a8a91}\n.decision-state-inline.active{color:#1f7a3e}\n.run-status.stopped{color:#8a8a91}\n.run-status.completed{color:#6f6f76}\n.compare-row .diff-pos{color:var(--green);font-weight:650}\n.compare-row .diff-neg{color:var(--red);font-weight:650}\n.compare-row .diff-neutral{color:#6f6f76}\n.backtest-model-note{padding-top:7px}\n</style>\n\n\n<style id="research-pipeline-state-css">\n#researchDetail .research-flow-step.state-draft{\n  background:#fff;\n  border-color:var(--line);\n}\n#researchDetail .research-flow-step.state-done{\n  border-color:#d8eddc;\n  background:#fbfffc;\n}\n#researchDetail .research-flow-step.state-running{\n  border-color:#d9e5ff;\n  background:#fbfdff;\n}\n#researchDetail .research-flow-step.state-available{\n  border-color:#e5e5e8;\n  background:#fff;\n}\n#researchDetail .research-flow-step.state-pending{\n  border-color:#eee1bd;\n  background:#fffdf6;\n}\n#researchDetail .research-flow-step .flow-state{\n  color:var(--muted);\n}\n</style>\n\n\n<style id="research-detail-topbar-clean-css">\n.research-detail-topbar{\n  justify-content:flex-start;\n}\n</style>\n\n</head>\n<body>\n\n<header class="top">\n  <div class="container topin">\n    <div class="brand"><span class="live-dot" id="botDot" title="Bot running"></span>TriggerTrade</div>\n    <div class="actions">\n      <button class="icon-action message-action" title="Messages" aria-label="Messages" onclick="openMessages()">\n        ✉\n        <span class="message-count" aria-hidden="true">+2</span>\n      </button>\n      <button class="icon-action" title="Copy logs" aria-label="Copy logs" onclick="copySystemHistory()">⧉</button>\n      <button class="icon-action" title="Settings" aria-label="Settings">⚙</button>\n    </div>\n  </div>\n</header>\n\n<div class="tabsbar">\n  <div class="container tabs">\n    <button class="tab active" data-page="portfolio">Portfolio</button>\n    <button class="tab" data-page="sets">Sets</button>\n    <button class="tab" data-page="rules">Rules</button>\n    <button class="tab" data-page="research">Research</button>\n  </div>\n</div>\n\n<main class="container">\n\n<section class="page active" id="portfolio">\n\n  <div class="context subtle-status">\n    <span>Last update 02:58</span>\n  </div>\n\n  <div class="kpis">\n    <div class="kpi">\n      <div class="klabel">Total</div>\n      <div class="kvalue">$10,248.42</div>\n    </div>\n    <div class="kpi">\n      <div class="klabel">Available</div>\n      <div class="kvalue">$6,812.10</div>\n    </div>\n    <div class="kpi">\n      <div class="klabel">In positions</div>\n      <div class="kvalue">$3,436.32</div>\n    </div>\n    <div class="kpi">\n      <div class="klabel">Realized P&L today</div>\n      <div class="kvalue pos">+$126.32</div>\n    </div>\n    <div class="kpi">\n      <div class="klabel">Unrealized P&L</div>\n      <div class="kvalue pos">+$84.18</div>\n    </div>\n    <div class="kpi">\n      <div class="klabel">Open positions</div>\n      <div class="kvalue">27</div>\n    </div>\n  </div>\n\n  <div class="panel">\n    <div class="panelhead">\n      <div class="filters">\n        <div class="segment">\n          <button id="openFilter" class="active" onclick="setPositionMode(\'open\')">Open</button>\n          <button id="closedFilter" onclick="setPositionMode(\'closed\')">Closed</button>\n        </div>\n        <select><option>Coin: All</option><option>BTCUSDT</option><option>ETHUSDT</option><option>SOLUSDT</option><option>AVAXUSDT</option><option>LINKUSDT</option></select>\n        <select><option>Side: All</option><option>LONG</option><option>SHORT</option></select>\n        <select><option>Set: All</option><option>v4</option><option>v5</option></select>\n        <select id="closeReasonFilter" style="display:none">\n          <option>Close reason: All</option>\n          <option>Take Profit</option>\n          <option>Stop Loss</option>\n          <option>Manual</option>\n        </select>\n      </div>\n      <div class="positions-right">\n        <div class="summaryline" id="positionSummary"><span>Open <b>27</b></span><span>Capital <b>$3,436</b></span><span>Unrealized <b class="pos">+$84</b></span></div>\n        <div class="danger-actions">\n          <button class="btn stop-new" onclick="openControlModal(\'pause\')">Pause Entries</button>\n          <button class="btn close-all" onclick="openControlModal(\'close\')">Close All</button>\n        </div>\n      </div>\n    </div>\n\n    <div class="tablewrap">\n      <table>\n        <thead id="positionHead"></thead>\n        <tbody id="positionBody"></tbody>\n      </table>\n    </div>\n  </div>\n\n</section>\n\n\n\n\n\n<section class="page" id="sets">\n  <div class="panel">\n\n    <div class="tablewrap">\n      <table>\n        <thead>\n          <tr>\n            <th>Set</th>\n            <th>Version</th>\n            <th>Status</th>\n            <th>Triggers</th>\n          </tr>\n        </thead>\n        <tbody id="researchTableBody">\n          <tr>\n            <td class="coin">Set 1</td>\n            <td>v4</td>\n            <td><span class="badge green">ACTIVE</span></td>\n            <td>\n              <div class="trigger-list">\n                <button class="link" onclick="openTriggerDetail(\'TRG-001\')">Price Move</button>\n                <button class="link" onclick="openTriggerDetail(\'TRG-003\')">Market Direction</button>\n                <button class="link" onclick="openTriggerDetail(\'TRG-002\')">Robust Volume Confirmation</button>\n              </div>\n            </td>\n          </tr>\n\n          <tr>\n            <td class="coin">Set 2</td>\n            <td>v5</td>\n            <td><span class="badge blue">TESTING</span></td>\n            <td>\n              <div class="trigger-list">\n                <button class="link" onclick="openTriggerDetail(\'TRG-001\')">Price Move</button>\n                <button class="link" onclick="openTriggerDetail(\'TRG-002\')">Robust Volume Confirmation</button>\n              </div>\n            </td>\n          </tr>\n\n          <tr>\n            <td class="coin">Set 3</td>\n            <td>v6</td>\n            <td><span class="badge blue">TESTING</span></td>\n            <td>\n              <div class="trigger-list">\n                <button class="link" onclick="openTriggerDetail(\'TRG-001\')">Price Move</button>\n                <button class="link" onclick="openTriggerDetail(\'TRG-003\')">Market Direction</button>\n              </div>\n            </td>\n          </tr>\n\n          <tr>\n            <td class="coin">Set 4</td>\n            <td>v2</td>\n            <td><span class="badge gray">ARCHIVED</span></td>\n            <td>\n              <div class="trigger-list">\n                <button class="link" onclick="openTriggerDetail(\'TRG-001\')">Price Move</button>\n              </div>\n            </td>\n          </tr>\n        </tbody>\n      </table>\n    </div>\n  </div>\n\n  \n  <div class="catalog-entry">\n    <button class="catalog-button" onclick="showPage(\'trigger-catalog\')">\n      <span>Trigger Catalog</span>\n      <span class="catalog-arrow">→</span>\n    </button>\n  </div>\n\n</section>\n\n\n<section class="page" id="trigger-catalog">\n  <div class="detail-top">\n    <button class="back-link" onclick="showPage(\'sets\')">← Back to Sets</button>\n  </div>\n\n  <div class="panel">\n    <div class="tablewrap">\n      <table>\n        <thead>\n          <tr>\n            <th>Trigger</th>\n            <th>Version</th>\n            <th>What it checks</th>\n          </tr>\n        </thead>\n        <tbody>\n          <tr>\n            <td><button class="link" onclick="openTriggerDetail(\'TRG-001\')">Price Move</button></td>\n            <td>0.1.0</td>\n            <td>Price displacement</td>\n          </tr>\n          <tr>\n            <td><button class="link" onclick="openTriggerDetail(\'TRG-002\')">Robust Volume Confirmation</button></td>\n            <td>0.1.0</td>\n            <td>Relative volume + percentile</td>\n          </tr>\n          <tr>\n            <td><button class="link" onclick="openTriggerDetail(\'TRG-003\')">Market Direction</button></td>\n            <td>0.2.0</td>\n            <td>Directional market context</td>\n          </tr>\n        </tbody>\n      </table>\n    </div>\n  </div>\n</section>\n\n<section class="page" id="trigger-detail">\n  <div class="detail-top">\n    <button class="back-link" onclick="showPage(\'sets\')">← Back</button>\n  </div>\n\n  <div class="panel">\n    <div class="panelhead">\n      <div>\n        <div class="title" id="triggerDetailTitle">TRG-002 · Robust Volume Confirmation</div>\n        <div class="meta">Version 0.1.0</div>\n      </div>\n\n    </div>\n  </div>\n\n  <div class="panel">\n    <div class="panelhead">\n      <div class="title">How it works</div>\n    </div>\n    <div class="logic-body">\n      <div class="explain-text">Current completed-candle volume is compared with the median volume of the previous completed candles and with its percentile inside that historical window.</div>\n      <div class="formula-block">median_volume = median(previous completed candle volumes)\n\nrelative_volume = current_volume / median_volume\n\nvolume_percentile =\ncount(previous_volume ≤ current_volume) / lookback × 100\n\nCONFIRMED when:\nrelative_volume ≥ relative_volume_threshold\nAND\nvolume_percentile ≥ percentile_threshold</div>\n    </div>\n  </div>\n\n  <div class="panel">\n    <div class="panelhead">\n      <div class="title">Parameters</div>\n    </div>\n    <div class="tablewrap">\n      <table>\n        <thead><tr><th>Parameter</th><th>Current value</th><th>Meaning</th></tr></thead>\n        <tbody>\n          <tr><td>Lookback</td><td>60</td><td>Previous completed candles</td></tr>\n          <tr><td>Relative volume threshold</td><td>2.0×</td><td>Current volume vs median</td></tr>\n          <tr><td>Percentile threshold</td><td>90%</td><td>Position inside the lookback window</td></tr>\n        </tbody>\n      </table>\n    </div>\n    \n  </div>\n\n  <div class="panel">\n    <div class="panelhead"><div><div class="title">Used in</div></div></div>\n    <div class="tablewrap">\n      <table>\n        <thead><tr><th>Set</th><th>Version</th><th>Status</th></tr></thead>\n        <tbody>\n<tr><td>Set 1</td><td>v4</td><td><span class="badge green">ACTIVE</span></td></tr>\n<tr><td>Set 2</td><td>v5</td><td><span class="badge blue">TESTING</span></td></tr>\n</tbody>\n      </table>\n    </div>\n  </div>\n\n  <div class="panel">\n    <div class="panelhead"><div><div class="title">Version history</div></div></div>\n    <div class="tablewrap">\n      <table>\n        <thead><tr><th>Version</th><th>Date</th><th>Change</th></tr></thead>\n        <tbody><tr><td>0.1.0</td><td>05 Sep</td><td>Initial version</td></tr></tbody>\n      </table>\n    </div>\n  </div>\n</section>\n\n\n\n\n\n\n<section class="page" id="rules">\n  <div class="rules-topbar">\n    <div class="current-rules-heading">Current Rules Configuration</div>\n  </div>\n  <div class="rules-grid">\n\n    <div class="panel">\n      <div class="panelhead">\n        <div class="title">Position Rules</div>\n      </div>\n\n      <div class="rule-form">\n        <div class="rule-row">\n          <div>\n            <div class="rule-name">Position size</div>\n            <div class="rule-desc">% of available capital allocated to one new position</div>\n          </div>\n          <div class="rule-control suffix-control">\n            <input type="number" value="2.0" step="0.1" min="0.1" max="100">\n            <span>%</span>\n          </div>\n        </div>\n\n        <div class="rule-row">\n          <div>\n            <div class="rule-name">Take Profit mode</div>\n            <div class="rule-desc">How the target is determined</div>\n          </div>\n          <div class="rule-control">\n            <select id="tpMode" onchange="syncTpMode()">\n              <option>Fixed</option>\n              <option selected>Dynamic</option>\n            </select>\n          </div>\n        </div>\n\n        <div class="rule-row" id="fixedTpRow" style="display:none">\n          <div>\n            <div class="rule-name">Fixed Take Profit</div>\n            <div class="rule-desc">Exact target move from entry</div>\n          </div>\n          <div class="rule-control suffix-control">\n            <input type="number" value="1.0" step="0.1" min="0.1">\n            <span>%</span>\n          </div>\n        </div>\n\n        <div class="rule-row" id="minTpRow">\n          <div>\n            <div class="rule-name">Minimum Take Profit</div>\n            <div class="rule-desc">Dynamic target cannot be lower than this level</div>\n          </div>\n          <div class="rule-control suffix-control">\n            <input type="number" value="0.8" step="0.1" min="0.1">\n            <span>%</span>\n          </div>\n        </div>\n\n        <div class="rule-row">\n          <div>\n            <div class="rule-name">Stop Loss</div>\n            <div class="rule-desc">Maximum planned move against the position</div>\n          </div>\n          <div class="rule-control suffix-control">\n            <input type="number" value="0.6" step="0.1" min="0.1">\n            <span>%</span>\n          </div>\n        </div>\n\n        <div class="rule-row">\n          <div>\n            <div class="rule-name">Minimum Risk / Reward</div>\n            <div class="rule-desc">Minimum expected reward relative to planned risk</div>\n          </div>\n          <div class="rule-control rr-control">\n            <input type="number" value="1.5" step="0.1" min="0.1">\n            <span>: 1</span>\n          </div>\n        </div>\n\n        <div class="rule-row">\n          <div>\n            <div class="rule-name">Minimum Net Edge <label class="mini-toggle"><input type="checkbox" checked><span></span></label></div>\n            <div class="rule-desc">Minimum expected result after trading costs</div>\n          </div>\n          <div class="rule-control suffix-control">\n            <input type="number" value="0.5" step="0.1" min="0">\n            <span>%</span>\n          </div>\n        </div>\n\n        <div class="rule-row">\n          <div>\n            <div class="rule-name">Leverage</div>\n            <div class="rule-desc">Default leverage for new positions</div>\n          </div>\n          <div class="rule-control">\n            <select>\n              <option selected>1×</option>\n              <option>2×</option>\n              <option>3×</option>\n              <option>5×</option>\n            </select>\n          </div>\n        </div>\n      </div>\n    </div>\n\n    <div class="panel">\n      <div class="panelhead">\n        <div class="title">Portfolio Rules</div>\n      </div>\n\n      <div class="rule-form">\n        <div class="rule-row">\n          <div>\n            <div class="rule-name">Max capital in positions</div>\n            <div class="rule-desc">Maximum share of total capital allowed in open positions</div>\n          </div>\n          <div class="rule-control suffix-control">\n            <input type="number" value="60" step="1" min="1" max="100">\n            <span>%</span>\n          </div>\n        </div>\n\n        <div class="rule-row">\n          <div>\n            <div class="rule-name">Max open positions <label class="mini-toggle"><input type="checkbox" checked><span></span></label></div>\n            <div class="rule-desc">Maximum number of simultaneous positions</div>\n          </div>\n          <div class="rule-control">\n            <input type="number" value="20" step="1" min="1">\n          </div>\n        </div>\n\n        <div class="rule-row">\n          <div>\n            <div class="rule-name">Max positions per coin <label class="mini-toggle"><input type="checkbox"><span></span></label></div>\n            \n          </div>\n          <div class="rule-control">\n            <input type="number" value="1" step="1" min="1">\n          </div>\n        </div>\n\n        <div class="rule-row">\n          <div>\n            <div class="rule-name">Direction</div>\n            <div class="rule-desc">Allowed trade directions</div>\n          </div>\n          <div class="rule-control">\n            <select>\n              <option selected>LONG + SHORT</option>\n              <option>LONG only</option>\n              <option>SHORT only</option>\n            </select>\n          </div>\n        </div>\n\n        <div class="rule-row">\n          <div>\n            <div class="rule-name">Daily loss limit <label class="mini-toggle"><input type="checkbox"><span></span></label></div>\n            \n          </div>\n          <div class="rule-control suffix-control">\n            <input type="number" value="3.0" step="0.1" min="0">\n            <span>%</span>\n          </div>\n        </div>\n      </div>\n    </div>\n\n    <div class="panel">\n      <div class="panelhead">\n        <div class="title">Coins</div>\n        <div class="rule-actions">\n          <button class="btn" onclick="toggleCoinsEditor()">Edit</button>\n        </div>\n      </div>\n\n      <div class="coins-list" id="coinsList">\n        <span class="coin-chip">BTCUSDT <small>8%</small></span>\n        <span class="coin-chip">ETHUSDT <small>8%</small></span>\n        <span class="coin-chip">SOLUSDT <small>5%</small></span>\n        <span class="coin-chip">AVAXUSDT</span>\n        <span class="coin-chip">LINKUSDT</span>\n      </div>\n\n      <div class="coins-editor" id="coinsEditor" style="display:none">\n        <div class="coins-toolbar">\n          <input class="search" id="coinSearch" placeholder="Search exchange symbols" oninput="filterCoinOptions()">\n          <button class="btn" onclick="mockRefreshSymbols()">Refresh from exchange</button>\n        </div>\n\n        <div class="coin-options" id="coinOptions">\n          <label><span><input type="checkbox" checked> BTCUSDT</span><span class="coin-limit"><input type="number" value="8" min="1" max="100">%</span></label>\n          <label><span><input type="checkbox" checked> ETHUSDT</span><span class="coin-limit"><input type="number" value="8" min="1" max="100">%</span></label>\n          <label><span><input type="checkbox" checked> SOLUSDT</span><span class="coin-limit"><input type="number" value="5" min="1" max="100">%</span></label>\n          <label><span><input type="checkbox" checked> AVAXUSDT</span><span class="coin-limit"><input type="number" placeholder="—" min="1" max="100">%</span></label>\n          <label><span><input type="checkbox" checked> LINKUSDT</span><span class="coin-limit"><input type="number" placeholder="—" min="1" max="100">%</span></label>\n          <label><span><input type="checkbox"> DOGEUSDT</span><span class="coin-limit"><input type="number" placeholder="—" min="1" max="100">%</span></label>\n          <label><span><input type="checkbox"> XRPUSDT</span><span class="coin-limit"><input type="number" placeholder="—" min="1" max="100">%</span></label>\n          <label><span><input type="checkbox"> ADAUSDT</span><span class="coin-limit"><input type="number" placeholder="—" min="1" max="100">%</span></label>\n          <label><span><input type="checkbox"> SUIUSDT</span><span class="coin-limit"><input type="number" placeholder="—" min="1" max="100">%</span></label>\n          <label><span><input type="checkbox"> TONUSDT</span><span class="coin-limit"><input type="number" placeholder="—" min="1" max="100">%</span></label>\n        </div>\n\n        <div class="coins-footer">\n          <span class="meta">Optional % = max share of total capital for that coin. Blank = no coin-specific limit.</span>\n          <button class="btn" onclick="applyCoins()">Apply</button>\n        </div>\n      </div>\n    </div>\n\n\n    <div class="rules-bottom-actions">\n      <div class="rules-save-state" id="rulesSaveState">No unsaved changes</div>\n      <button class="btn primary-rule" onclick="saveRules()">Save as New Version</button>\n    </div>\n\n    <div class="panel rules-span version-history-table">\n      <div class="tablewrap">\n        <table>\n          <thead><tr><th>Version</th><th>Change</th><th>Used in</th></tr></thead>\n          <tbody>\n            <tr><td><button class="link" onclick="openRulesVersion(\'v4\')">v4</button></td><td>Minimum Net Edge 0.5% → 0.6%</td><td>Current</td></tr>\n            <tr><td><button class="link" onclick="openRulesVersion(\'v3\')">v3</button></td><td>Stop Loss 0.5% → 0.6%</td><td>Research · Set 2 · v5</td></tr>\n            <tr><td><button class="link" onclick="openRulesVersion(\'v2\')">v2</button></td><td>TP mode Fixed → Dynamic</td><td>Research · Set 3 · v6</td></tr>\n            <tr><td><button class="link" onclick="openRulesVersion(\'v1\')">v1</button></td><td>Initial configuration</td><td>—</td></tr>\n          </tbody>\n        </table>\n      </div>\n    </div>\n\n  </div>\n</section>\n\n\n\n<section class="page" id="rules-version">\n  <div class="rules-version-header">\n    <div class="rules-version-header-inner">\n      <div class="current-rules-heading" id="rulesVersionTitle">Rules · v3</div>\n      <div class="pagesub">Saved rules configuration · read only</div>\n      <div class="version-context"><span id="rulesVersionChange">Change: Stop Loss 0.5% → 0.6%</span><span id="rulesVersionUsed">Used in: Research · Set 2 · v5</span></div>\n    </div>\n  </div>\n  <div class="rules-grid readonly-control">\n    <div class="panel">\n      <div class="panelhead"><div class="title">Position Rules</div></div>\n      <div class="rule-form">\n        <div class="rule-row"><div><div class="rule-name">Position size</div><div class="rule-desc">% of available capital allocated to one new position</div></div><div class="rule-control suffix-control"><input id="rvPosSize" type="number" value="2.0" readonly><span>%</span></div></div>\n        <div class="rule-row"><div><div class="rule-name">Take Profit mode</div><div class="rule-desc">How the target is determined</div></div><div class="rule-control"><select id="rvTpMode" disabled><option>Fixed</option><option selected>Dynamic</option></select></div></div>\n        <div class="rule-row"><div><div class="rule-name">Minimum Take Profit</div><div class="rule-desc">Dynamic target cannot be lower than this level</div></div><div class="rule-control suffix-control"><input id="rvMinTp" type="number" value="0.8" readonly><span>%</span></div></div>\n        <div class="rule-row"><div><div class="rule-name">Stop Loss</div><div class="rule-desc">Maximum planned move against the position</div></div><div class="rule-control suffix-control"><input id="rvSl" type="number" value="0.6" readonly><span>%</span></div></div>\n        <div class="rule-row"><div><div class="rule-name">Minimum Risk / Reward</div><div class="rule-desc">Minimum expected reward relative to planned risk</div></div><div class="rule-control rr-control"><input id="rvRR" type="number" value="1.5" readonly><span>: 1</span></div></div>\n        <div class="rule-row"><div><div class="rule-name">Minimum Net Edge <label class="mini-toggle"><input id="rvEdgeOn" type="checkbox" checked disabled><span></span></label></div><div class="rule-desc">Minimum expected result after trading costs</div></div><div class="rule-control suffix-control"><input id="rvEdge" type="number" value="0.5" readonly><span>%</span></div></div>\n        <div class="rule-row"><div><div class="rule-name">Leverage</div><div class="rule-desc">Default leverage for new positions</div></div><div class="rule-control"><select id="rvLev" disabled><option selected>1×</option><option>2×</option><option>3×</option></select></div></div>\n      </div>\n    </div>\n    <div class="panel">\n      <div class="panelhead"><div class="title">Portfolio Rules</div></div>\n      <div class="rule-form">\n        <div class="rule-row"><div><div class="rule-name">Max capital in positions</div><div class="rule-desc">Maximum share of total capital allowed in open positions</div></div><div class="rule-control suffix-control"><input id="rvCap" type="number" value="60" readonly><span>%</span></div></div>\n        <div class="rule-row"><div><div class="rule-name">Max open positions <label class="mini-toggle"><input id="rvMaxOpenOn" type="checkbox" checked disabled><span></span></label></div><div class="rule-desc">Maximum number of simultaneous positions</div></div><div class="rule-control"><input id="rvMaxOpen" type="number" value="20" readonly></div></div>\n        <div class="rule-row"><div><div class="rule-name">Max positions per coin <label class="mini-toggle"><input id="rvPerCoinOn" type="checkbox" disabled><span></span></label></div></div><div class="rule-control"><input id="rvPerCoin" type="number" value="1" readonly></div></div>\n        <div class="rule-row"><div><div class="rule-name">Direction</div><div class="rule-desc">Allowed trade directions</div></div><div class="rule-control"><select id="rvDirection" disabled><option selected>LONG + SHORT</option><option>LONG only</option><option>SHORT only</option></select></div></div>\n        <div class="rule-row"><div><div class="rule-name">Daily loss limit <label class="mini-toggle"><input id="rvDailyOn" type="checkbox" disabled><span></span></label></div></div><div class="rule-control suffix-control"><input id="rvDaily" type="number" value="3.0" readonly><span>%</span></div></div>\n      </div>\n    </div>\n    <div class="panel">\n      <div class="panelhead"><div class="title">Coins</div></div>\n      <div class="coins-list" id="rulesVersionCoins"></div>\n    </div>\n  </div>\n</section>\n\n\n<section class="page" id="research">\n\n  <div class="research-toolbar-main">\n    <div class="research-toolbar-title">Research</div>\n    <button class="new-research-btn" onclick="openNewResearchModal()">New Research</button>\n  </div>\n\n\n  <div class="research-list panel research-summary-panel">\n    <div class="tablewrap">\n      <table class="research-summary-table" id="researchSummaryTable">\n        <thead>\n          <tr>\n            <th>Set</th>\n            <th>Rules</th>\n            <th>Backtest Profit Factor</th>\n            <th>Demo Profit Factor</th>\n            <th>Compare to Active</th>\n            <th>Decision</th>\n          </tr>\n        </thead>\n        <tbody id="researchSummaryBody">\n          <tr onclick="openResearchSet(\'Set 2\')">\n            <td><button class="research-object-link" onclick="event.stopPropagation();openSetFromResearch(\'Set 2\',\'v5\')"><span>Set 2</span><small>v5</small></button></td>\n            <td><button class="research-object-link" onclick="event.stopPropagation();openRulesVersion(\'v3\')"><span>Rules</span><small>v3</small></button></td>\n            <td><div class="pf-cell"><span class="pf-value" id="summaryBacktestPf">1.22</span><span class="pf-trades" id="summaryBacktestTrades">311 trades</span></div></td>\n            <td><div class="pf-cell"><span class="pf-value" id="summaryDemoPf">1.34</span><span class="pf-trades" id="summaryDemoTrades">84 trades</span></div></td>\n            <td><span class="compare-result better">3 of 4 better</span></td>\n            <td><span class="decision-status running">Demo running</span></td>\n          </tr>\n          <tr onclick="openResearchSet(\'Set 3\')">\n            <td><button class="research-object-link" onclick="event.stopPropagation();openSetFromResearch(\'Set 3\',\'v6\')"><span>Set 3</span><small>v6</small></button></td>\n            <td><button class="research-object-link" onclick="event.stopPropagation();openRulesVersion(\'v2\')"><span>Rules</span><small>v2</small></button></td>\n            <td><div class="pf-cell"><span class="pf-value">1.18</span><span class="pf-trades">286 trades</span></div></td>\n            <td><div class="pf-cell"><span class="pf-value">0.94</span><span class="pf-trades">71 trades</span></div></td>\n            <td><span class="compare-result weak">1 of 4 better</span></td>\n            <td><span class="decision-status attention">Decision needed</span></td>\n          </tr>\n          <tr onclick="openResearchSet(\'Set 4\')">\n            <td><button class="research-object-link" onclick="event.stopPropagation();openSetFromResearch(\'Set 4\',\'v7\')"><span>Set 4</span><small>v7</small></button></td>\n            <td><button class="research-object-link" onclick="event.stopPropagation();openRulesVersion(\'v1\')"><span>Rules</span><small>v1</small></button></td>\n            <td><div class="pf-cell"><span class="pf-value weak">0.88</span><span class="pf-trades">304 trades</span></div></td>\n            <td><span class="pf-empty">—</span></td>\n            <td><span class="compare-result muted">—</span></td>\n            <td><span class="decision-status archived">Archived</span></td>\n          </tr>\n        </tbody>\n      </table>\n    </div>\n  </div>\n\n  <section class="research-detail" id="researchDetail">\n    <div class="research-detail-topbar">\n      <div class="research-detail-object-head">\n        <button class="research-detail-object-link" id="researchDetailSetLink" onclick="openSetFromResearch(\'Set 2\',\'v5\')">Set 2 · v5</button>\n        <span class="research-detail-separator">·</span>\n        <button class="research-detail-object-link" id="researchDetailRulesLink" onclick="openRulesVersion(\'v3\')">Rules · v3</button>\n      </div>\n    </div>\n\n    <div class="research-flow">\n      <div class="research-flow-step done">\n        <div class="flow-label">Backtest</div>\n        <div class="flow-state" id="flowBacktestState">Completed</div>\n      </div>\n      <div class="flow-arrow">→</div>\n      <div class="research-flow-step active">\n        <div class="flow-label">Demo</div>\n        <div class="flow-state" id="flowDemoState">Running</div>\n      </div>\n      <div class="flow-arrow">→</div>\n      <div class="research-flow-step">\n        <div class="flow-label">Compare</div>\n        <div class="flow-state" id="flowCompareState">Available</div>\n      </div>\n      <div class="flow-arrow">→</div>\n      <div class="research-flow-step">\n        <div class="flow-label">Decision</div>\n        <div class="flow-state" id="flowDecisionState">Pending</div>\n      </div>\n    </div>\n\n    <div class="panel research-runs-panel">\n      <div class="panelhead">\n        <div class="title">Backtest</div>\n        <div class="research-panel-actions"><button class="btn run-primary" onclick="openBacktestRunModal()">Run</button></div>\n      </div>\n      <div class="tablewrap">\n        <table class="research-runs-table research-run-table" id="backtestRunsTable">\n      <colgroup>\n        <col class="run">\n        <col class="status">\n        <col class="period">\n        <col class="trades">\n        <col class="pnl">\n        <col class="winrate">\n        <col class="pf">\n        <col class="dd">\n        <col class="use">\n      </colgroup>\n    \n          \n          <thead>\n          <tr>\n            <th>Run</th>\n            <th>Status</th>\n            <th>Period</th>\n            <th>Trades</th>\n            <th>Net P/L</th>\n            <th>Win Rate</th>\n            <th>Profit Factor</th>\n            <th>Max Drawdown</th>\n            <th>Use</th>\n          </tr>\n        </thead>\n          <tbody id="backtestRunsBody">\n<tr><td><button class="link">BT-014</button></td><td><span class="run-status completed">Completed</span></td><td>08 Jun — 05 Sep</td><td>311</td><td class="pos">+$550.12</td><td>58.2%</td><td><b>1.22</b></td><td class="neg">−4.7%</td><td class="run-use-cell"><input type="radio" name="backtestUse" checked aria-label="Use BT-014 in Research summary" onchange="selectResearchRun(\'backtest\',\'1.22\',\'311\')"></td></tr>\n<tr><td><button class="link">BT-013</button></td><td><span class="run-status completed">Completed</span></td><td>08 Jul — 05 Sep</td><td>207</td><td class="pos">+$318.40</td><td>56.5%</td><td>1.16</td><td class="neg">−5.1%</td><td class="run-use-cell"><input type="radio" name="backtestUse" aria-label="Use BT-013 in Research summary" onchange="selectResearchRun(\'backtest\',\'1.16\',\'207\')"></td></tr>\n<tr><td><button class="link">BT-012</button></td><td><span class="run-status completed">Completed</span></td><td>08 Aug — 05 Sep</td><td>102</td><td class="pos">+$141.08</td><td>54.9%</td><td>1.09</td><td class="neg">−3.8%</td><td class="run-use-cell"><input type="radio" name="backtestUse" aria-label="Use BT-012 in Research summary" onchange="selectResearchRun(\'backtest\',\'1.09\',\'102\')"></td></tr>\n</tbody>\n        </table>\n<div class="backtest-model-note">Backtest execution model currently excludes historical spread and slippage. Use Demo results for execution-sensitive validation.</div>\n      </div>\n    </div>\n\n    <div class="panel research-runs-panel">\n      <div class="panelhead">\n        <div class="title">Demo</div>\n        <div class="research-panel-actions"><button class="btn run-primary" id="demoToggleBtn" onclick="toggleDemoRun()">Stop Demo</button></div>\n      </div>\n      <div class="tablewrap">\n        <table class="research-runs-table research-run-table" id="demoRunsTable">\n      <colgroup>\n        <col class="run">\n        <col class="status">\n        <col class="period">\n        <col class="trades">\n        <col class="pnl">\n        <col class="winrate">\n        <col class="pf">\n        <col class="dd">\n        <col class="use">\n      </colgroup>\n    \n          \n          <thead>\n          <tr>\n            <th>Run</th>\n            <th>Status</th>\n            <th>Period</th>\n            <th>Trades</th>\n            <th>Net P/L</th>\n            <th>Win Rate</th>\n            <th>Profit Factor</th>\n            <th>Max Drawdown</th>\n            <th>Use</th>\n          </tr>\n        </thead>\n          <tbody id="demoRunsBody">\n<tr><td><button class="link">DM-006</button></td><td><span class="run-status running">Running</span></td><td>05 Sep — now</td><td>84</td><td class="pos">+$88.74</td><td>60.0%</td><td><b>1.34</b></td><td class="neg">−1.9%</td><td class="run-use-cell"><input type="radio" name="demoUse" checked aria-label="Use DM-006 in Research summary" onchange="selectResearchRun(\'demo\',\'1.34\',\'84\')"></td></tr>\n<tr><td><button class="link">DM-005</button></td><td><span class="run-status completed">Completed</span></td><td>01 Sep — 05 Sep</td><td>63</td><td class="pos">+$51.20</td><td>57.1%</td><td>1.21</td><td class="neg">−2.4%</td><td class="run-use-cell"><input type="radio" name="demoUse" aria-label="Use DM-005 in Research summary" onchange="selectResearchRun(\'demo\',\'1.21\',\'63\')"></td></tr>\n</tbody>\n        </table>\n      </div>\n    </div>\n\n    <div class="panel" id="comparePanel">\n      <div class="panelhead"><div class="title">Compare Demo to Active</div></div>\n      <div class="compare-head"><div></div><div class="compare-label">Research</div><div class="compare-label">Active</div><div class="compare-label">Difference</div></div>\n      \n      <div class="compare-row">\n        <div>Days</div><div>3</div><div>12</div><div class="diff-neutral">—</div>\n      </div>\n<div class="compare-row"><div>Closed trades</div><div>84</div><div>91</div><div>−7</div></div>\n      <div class="compare-row"><div>Win Rate</div><div>60.0%</div><div>55.7%</div><div class="diff-pos">+4.3 pp</div></div>\n      <div class="compare-row"><div>Profit Factor</div><div>1.34</div><div>1.28</div><div class="diff-pos">+0.06</div></div>\n      <div class="compare-row"><div>Net P/L</div><div class="pos">+$88.74</div><div class="pos">+$81.20</div><div class="diff-pos">+$7.54</div></div>\n      <div class="compare-row"><div>Max Drawdown</div><div>−1.9%</div><div>−2.8%</div><div class="diff-pos">+0.9 pp</div></div>\n    </div>\n\n    \n<div class="panel decision-panel">\n  <div class="decision-compact" id="decisionBox">\n    <div class="decision-left">\n      <div class="decision-title-inline">Decision</div>\n      <div class="decision-state-inline" id="decisionStateInline">Decision needed</div>\n    </div>\n    <div class="decision-actions-inline" id="decisionActionsInline">\n      <button class="btn" onclick="archiveResearch()">Archive</button>\n      <button class="btn primary-rule" onclick="makeResearchActive()">Make Active</button>\n    </div>\n  </div>\n</div>\n\n  </section>\n\n\n</section>\n\n<section class="page" id="messages">\n  <div class="panel">\n    <div class="tablewrap">\n      <table>\n        <thead>\n          <tr><th>Time</th><th>Message</th><th>Type</th></tr>\n        </thead>\n        <tbody>\n          <tr><td>02:41</td><td>BTCUSDT is approaching its configured Stop Loss level.</td><td><span class="badge amber">ATTENTION</span></td></tr>\n          <tr><td>02:18</td><td>Set 2 Demo evidence reached 40 closed trades.</td><td><span class="badge blue">INFO</span></td></tr>\n          <tr><td>01:56</td><td>No critical account issues detected.</td><td><span class="badge gray">INFO</span></td></tr>\n        </tbody>\n      </table>\n    </div>\n  </div>\n</section>\n\n<div class="modalbg" id="newResearchModal">\n  <div class="research-create-modal">\n    <div class="research-create-head">\n      <div>\n        <div class="title">New Research</div>\n        <div class="meta">Choose the trigger Set and Rules version</div>\n      </div>\n      <button class="icon-action" onclick="closeNewResearchModal()">✕</button>\n    </div>\n    <div class="research-create-body">\n      <div class="research-create-grid">\n        <label>\n          Trigger Set\n          <select id="newResearchSet">\n            <option>Set 2 · v5</option>\n            <option>Set 3 · v6</option>\n            <option>Set 4 · v7</option>\n          </select>\n        </label>\n        <label>\n          Rules\n          <select id="newResearchRules">\n            <option>Rules · v4</option>\n            <option>Rules · v3</option>\n            <option>Rules · v2</option>\n            <option>Rules · v1</option>\n          </select>\n        </label>\n      </div>\n      <div class="research-create-note">\n        The new Research will be created for the selected Set and Rules version.\n        Backtest and Demo runs can be started afterward from inside Research.\n      </div>\n      <div class="research-create-actions">\n        <button class="btn" onclick="closeNewResearchModal()">Cancel</button>\n        <button class="btn primary-rule" onclick="createNewResearch()">Create Research</button>\n      </div>\n    </div>\n  </div>\n</div>\n\n<div class="modalbg" id="backtestRunModal">\n  <div class="run-modal">\n    <div class="run-modal-head">\n      <div>\n        <div class="title">Run Backtest</div>\n        <div class="meta">Choose the historical period</div>\n      </div>\n      <button class="icon-action" onclick="closeBacktestRunModal()">✕</button>\n    </div>\n    <div class="run-modal-body">\n      <div class="run-date-grid">\n        <label>From\n          <input id="btRunFrom" type="date" value="2026-06-08">\n        </label>\n        <label>To\n          <input id="btRunTo" type="date" value="2026-09-05">\n        </label>\n      </div>\n      <div class="run-context">\n        <span>Capital <b>$1,000</b></span>\n        <span>Set <b>Set 2 · v5</b></span>\n        <span>Rules <b>Rules · v3</b></span>\n        <span>Execution <b>Bybit data · system model</b></span>\n      </div>\n      <div class="run-modal-actions">\n        <button class="btn" onclick="closeBacktestRunModal()">Cancel</button>\n        <button class="btn primary-rule" onclick="createBacktestRun()">Run</button>\n      </div>\n    </div>\n  </div>\n</div>\n\n<div class="modalbg" id="controlModal">\n  <div class="modal">\n    <div class="panelhead">\n      <div>\n        <div class="title" id="controlTitle">Confirm action</div>\n        <div class="meta" id="controlMeta"></div>\n      </div>\n    </div>\n    <div class="modalbody">\n      <div class="notice" id="controlNotice"></div>\n      <div class="confirm-field" id="confirmField" style="display:none">\n        <label for="confirmInput">Type CLOSE ALL to confirm</label>\n        <input id="confirmInput" class="search" autocomplete="off" placeholder="CLOSE ALL">\n      </div>\n      <div class="modalactions">\n        <button class="btn" onclick="closeControlModal()">Cancel</button>\n        <button class="btn red" id="controlConfirm" onclick="confirmControlAction()">Confirm</button>\n      </div>\n    </div>\n  </div>\n</div>\n\n<script>\nconst openRows = [\n["BTCUSDT","LONG","1×","0.018 BTC","$1,055","$58,420","$58,612","+1.0% · $59,004","−0.6% · $58,069","+1.78% · +$18.74","v4","43m"],\n["ETHUSDT","SHORT","1×","0.217 ETH","$740","$3,412","$3,398","+0.8% · $3,385","−0.5% · $3,429","+0.42% · +$3.12","v4","18m"],\n["SOLUSDT","LONG","2×","3.86 SOL","$510","$132.10","$134.11","+1.2% · $133.69","−0.7% · $131.18","+1.52% · +$7.74","v5","1h 02m"],\n["AVAXUSDT","SHORT","1×","11.11 AVAX","$420","$37.80","$38.04","+0.9% · $37.46","−0.5% · $37.99","−0.63% · −$2.66","v4","27m"],\n["LINKUSDT","LONG","2×","27.45 LINK","$390","$14.21","$14.28","+1.1% · $14.37","−0.7% · $14.11","+0.49% · +$1.92","v5","11m"]\n];\n\nconst closedRows = [\n["BTCUSDT","SHORT","1×","0.0166 BTC","$980","$58,910","$58,540","+0.9% · $58,380","−0.5% · $59,205","+0.63% · +$5.78","TAKE PROFIT","v4","34m"],\n["SOLUSDT","LONG","2×","3.82 SOL","$500","$131.02","$132.41","+1.2% · $132.59","−0.7% · $130.10","+1.00% · +$5.00","TAKE PROFIT","v5","26m"],\n["ETHUSDT","LONG","1×","0.212 ETH","$710","$3,356","$3,321","+0.8% · $3,383","−0.6% · $3,336","−1.00% · −$7.12","STOP LOSS","v4","19m"],\n["LINKUSDT","SHORT","2×","31.2 LINK","$445","$14.26","$14.19","+1.0% · $14.12","−0.6% · $14.35","+0.42% · +$1.88","MANUAL","v5","12m"]\n];\n\nfunction badge(side){\n  return side==="LONG" ? \'<span class="badge green">LONG</span>\' : \'<span class="badge red">SHORT</span>\';\n}\nfunction pnl(v){ return v.trim().startsWith("+") ? `<span class="pos">${v}</span>` : `<span class="neg">${v}</span>`; }\n\nfunction signedClass(value){\n  const s = String(value).trim();\n  return s.startsWith("-") || s.startsWith("−") ? "neg" : s.startsWith("+") ? "pos" : "";\n}\n\n\nfunction setPositionMode(mode){\n  openFilter.classList.toggle("active", mode==="open");\n  closedFilter.classList.toggle("active", mode==="closed");\n  if(mode==="open"){\n    closeReasonFilter.style.display="none";\n    positionHead.innerHTML=`<tr><th>Coin</th><th>Side</th><th>Leverage</th><th>Qty</th><th>Value</th><th>Entry</th><th title="Exchange mark price used for unrealized P&L and liquidation calculations">Current Price</th><th>Take Profit</th><th>Stop Loss</th><th>Unrealized P&L</th><th>Set</th><th>Age</th><th></th></tr>`;\n    positionBody.innerHTML=openRows.map(r=>`<tr><td class="coin">${r[0]}</td><td>${badge(r[1])}</td><td>${r[2]}</td><td>${r[3]}</td><td>${r[4]}</td><td>${r[5]}</td><td>${r[6]}</td><td>${r[7]}</td><td>${r[8]}</td><td>${pnl(r[9])}</td><td><button class="link" onclick="showPage(\'sets\')">${r[10]}</button></td><td>${r[11]}</td><td><button class="row-close" onclick="openSingleClose(\'${r[0]}\')">Close</button></td></tr>`).join("");\n    positionSummary.innerHTML=\'<span>Open <b>27</b></span><span>Capital <b>$3,436</b></span><span>Unrealized P&L <b class="pos">+$84</b></span>\';\n  }else{\n    closeReasonFilter.style.display="";\n    positionHead.innerHTML=`<tr><th>Coin</th><th>Side</th><th>Leverage</th><th>Qty</th><th>Value</th><th>Entry</th><th>Exit</th><th>Planned TP</th><th>Planned SL</th><th>Realized P&L</th><th>Close reason</th><th>Set</th><th>Duration</th></tr>`;\n    positionBody.innerHTML=closedRows.map(r=>`<tr><td class="coin">${r[0]}</td><td>${badge(r[1])}</td><td>${r[2]}</td><td>${r[3]}</td><td>${r[4]}</td><td>${r[5]}</td><td>${r[6]}</td><td>${r[7]}</td><td>${r[8]}</td><td>${pnl(r[9])}</td><td>${r[10]}</td><td><button class="link" onclick="showPage(\'sets\')">${r[11]}</button></td><td>${r[12]}</td></tr>`).join("");\n    positionSummary.innerHTML=\'<span>Closed today <b>18</b></span><span>Realized P&L <b class="pos">+$126</b></span><span>Win rate <b>61%</b></span>\';\n  }\n}\nsetPositionMode("open");\n\nfunction showPage(id){\n  document.querySelectorAll(".page").forEach(p=>p.classList.toggle("active",p.id===id));\n  document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("active",t.dataset.page===id));\n}\ndocument.querySelectorAll(".tab").forEach(t=>t.onclick=()=>showPage(t.dataset.page));\n\nlet controlAction = null;\n\nlet singleCloseSymbol = null;\n\nfunction openSingleClose(symbol){\n  singleCloseSymbol = symbol;\n  controlAction = "single-close";\n  confirmInput.value = "";\n  controlTitle.textContent = "Close " + symbol + "?";\n  controlMeta.textContent = "Single position";\n  controlNotice.textContent = "This will request closure of this position only.";\n  confirmField.style.display = "none";\n  controlConfirm.textContent = "Close";\n  controlModal.classList.add("open");\n}\n\nfunction openControlModal(action){\n  controlAction = action;\n  confirmInput.value = "";\n  if(action === "pause"){\n    controlTitle.textContent = "Pause new entries?";\n    controlMeta.textContent = "Protected trading control";\n    controlNotice.textContent = "The bot will stop opening new positions. Existing positions remain active and continue to be managed.";\n    confirmField.style.display = "none";\n    controlConfirm.textContent = "Pause Entries";\n  }else{\n    controlTitle.textContent = "Close All?";\n    controlMeta.textContent = "Emergency portfolio action";\n    controlNotice.textContent = "This will request closure of every currently open position. This action affects the whole portfolio.";\n    confirmField.style.display = "block";\n    controlConfirm.textContent = "Close All";\n  }\n  controlModal.classList.add("open");\n}\nfunction closeControlModal(){ controlModal.classList.remove("open"); }\n\nfunction confirmControlAction(){\n  if(controlAction === "close" && confirmInput.value.trim() !== "CLOSE ALL"){\n    confirmInput.focus();\n    return;\n  }\n  closeControlModal();\n  if(controlAction === "pause"){\n    botDot.style.background = "#a16207";\n    botDot.style.boxShadow = "0 0 0 4px #fff8e6";\n    botDot.title = "Bot running · new entries paused";\n  }\n  if(controlAction === "single-close"){\n    singleCloseSymbol = null;\n  }\n}\n\nasync function copySystemHistory(){\n  const snapshot = [\n    "TriggerTrade system history export",\n    "Portfolio state",\n    "Positions",\n    "Orders and executions",\n    "Set/rule decisions",\n    "Risk decisions",\n    "Runtime and operator actions",\n    "Errors and reconciliation events"\n  ].join("\\\\n");\n  try{\n    await navigator.clipboard.writeText(snapshot);\n  }catch(e){}\n}\n\nfunction openTriggerDetail(code){\n  const map = {\n    "TRG-001":"TRG-001 · Price Move",\n    "TRG-002":"TRG-002 · Robust Volume Confirmation",\n    "TRG-003":"TRG-003 · Regime Gate",\n    "TRG-OLD":"TRG-OLD · Legacy Spike"\n  };\n  document.getElementById("triggerDetailTitle").textContent = map[code] || code;\n  showPage("trigger-detail");\n}\n\n\nfunction openTriggerDetail(code){\n  const map = {\n    "TRG-001":"TRG-001 · Price Move",\n    "TRG-002":"TRG-002 · Robust Volume Confirmation",\n    "TRG-003":"TRG-003 · Market Direction",\n    "TRG-OLD":"TRG-OLD · Legacy Spike"\n  };\n  document.getElementById("triggerDetailTitle").textContent = map[code] || code;\n  showPage("trigger-detail");\n}\n\n\nfunction openMessages(){\n  showPage("messages");\n  const badge = document.querySelector(".message-count");\n  if(badge) badge.style.display = "none";\n}\n\nfunction toggleCoinsEditor(){\n  const el = document.getElementById("coinsEditor");\n  el.style.display = el.style.display === "none" ? "block" : "none";\n}\n\nfunction filterCoinOptions(){\n  const q = document.getElementById("coinSearch").value.trim().toUpperCase();\n  document.querySelectorAll("#coinOptions label").forEach(label=>{\n    label.style.display = label.textContent.toUpperCase().includes(q) ? "flex" : "none";\n  });\n}\n\nfunction mockRefreshSymbols(){\n  const state = document.getElementById("rulesSaveState");\n  state.textContent = "Exchange symbol list refreshed";\n}\n\nfunction applyCoins(){\n  const selected = [...document.querySelectorAll("#coinOptions input:checked")]\n    .map(x=>x.parentElement.textContent.trim());\n  document.getElementById("coinsList").innerHTML =\n    selected.map(s=>`<span class="coin-chip">${s}</span>`).join("");\n  document.getElementById("coinsEditor").style.display = "none";\n  document.getElementById("rulesSaveState").textContent = "Unsaved changes";\n}\n\nfunction saveRules(){\n  document.getElementById("rulesSaveState").textContent = "Saved";\n}\n\n\nfunction syncTpMode(){\n  const mode = document.getElementById("tpMode").value;\n  const fixed = document.getElementById("fixedTpRow");\n  const minTp = document.getElementById("minTpRow");\n  if(mode === "Fixed"){\n    fixed.style.display = "grid";\n    minTp.style.display = "none";\n  }else{\n    fixed.style.display = "none";\n    minTp.style.display = "grid";\n  }\n}\n\n\nconst rulesVersions = {\n  v4:{change:\'Minimum Net Edge 0.5% → 0.6%\',used:\'Current\',sl:0.6,edge:0.6,tp:\'Dynamic\',minTp:0.8,pos:2.0,cap:60,maxOpen:20,coins:[[\'BTCUSDT\',\'8%\'],[\'ETHUSDT\',\'8%\'],[\'SOLUSDT\',\'5%\'],[\'AVAXUSDT\',\'\'],[\'LINKUSDT\',\'\']]},\n  v3:{change:\'Stop Loss 0.5% → 0.6%\',used:\'Research · Set 2 · v5\',sl:0.6,edge:0.5,tp:\'Dynamic\',minTp:0.8,pos:2.0,cap:60,maxOpen:20,coins:[[\'BTCUSDT\',\'8%\'],[\'ETHUSDT\',\'8%\'],[\'SOLUSDT\',\'5%\'],[\'AVAXUSDT\',\'\'],[\'LINKUSDT\',\'\']]},\n  v2:{change:\'TP mode Fixed → Dynamic\',used:\'Research · Set 3 · v6\',sl:0.5,edge:0.5,tp:\'Dynamic\',minTp:0.8,pos:2.0,cap:60,maxOpen:18,coins:[[\'BTCUSDT\',\'8%\'],[\'ETHUSDT\',\'8%\'],[\'SOLUSDT\',\'5%\'],[\'LINKUSDT\',\'\']]},\n  v1:{change:\'Initial configuration\',used:\'—\',sl:0.5,edge:0.5,tp:\'Fixed\',minTp:1.0,pos:2.0,cap:50,maxOpen:15,coins:[[\'BTCUSDT\',\'8%\'],[\'ETHUSDT\',\'8%\'],[\'SOLUSDT\',\'5%\']]}\n};\nfunction openRulesVersion(v){\n  const d=rulesVersions[v]||rulesVersions.v4;\n  rulesVersionTitle.textContent=\'Rules · \'+v;\n  rulesVersionChange.textContent=\'Change: \'+d.change;\n  rulesVersionUsed.textContent=\'Used in: \'+d.used;\n  rvPosSize.value=d.pos; rvSl.value=d.sl; rvEdge.value=d.edge; rvMinTp.value=d.minTp; rvCap.value=d.cap; rvMaxOpen.value=d.maxOpen;\n  [...rvTpMode.options].forEach(o=>o.selected=o.text===d.tp);\n  rulesVersionCoins.innerHTML=d.coins.map(([coin,limit])=>`<span class="coin-chip">${coin}${limit?` <small>${limit}</small>`:\'\'}</span>`).join(\'\');\n  showPage(\'rules-version\');\n}\n\nfunction openSetFromResearch(name,version){\n  showPage(\'sets\');\n  const rows=[...document.querySelectorAll(\'#sets tbody tr\')];\n  rows.forEach(r=>{\n    const match=r.textContent.includes(name) && r.textContent.includes(version);\n    r.style.background=match?\'#fffdf6\':\'\';\n  });\n}\n\nfunction openResearchSet(name){\n  document.querySelector(".research-list").style.display = "none";\n  const detail = document.getElementById("researchDetail");\n  detail.classList.add("open");\n  const map={\n    "Set 2":{setVersion:"v5",rulesVersion:"v3"},\n    "Set 3":{setVersion:"v6",rulesVersion:"v2"},\n    "Set 4":{setVersion:"v7",rulesVersion:"v1"}\n  };\n  const cfg=map[name]||map["Set 2"];\n  const setLink=document.getElementById("researchDetailSetLink");\n  const rulesLink=document.getElementById("researchDetailRulesLink");\n  if(setLink){setLink.textContent=name+" · "+cfg.setVersion;setLink.onclick=()=>openSetFromResearch(name,cfg.setVersion);}\n  if(rulesLink){rulesLink.textContent="Rules · "+cfg.rulesVersion;rulesLink.onclick=()=>openRulesVersion(cfg.rulesVersion);}\n}\nfunction closeResearchSet(){\n  document.querySelector(".research-list").style.display = "block";\n  document.getElementById("researchDetail").classList.remove("open");\n}\n\n</script>\n<script id="research-run-launch-js">\nlet mockBtCounter = 15;\nlet mockDemoCounter = 8;\n\nfunction openBacktestRunModal(){\n  const modal = document.getElementById(\'backtestRunModal\');\n  if(modal) modal.classList.add(\'open\');\n}\nfunction closeBacktestRunModal(){\n  const modal = document.getElementById(\'backtestRunModal\');\n  if(modal) modal.classList.remove(\'open\');\n}\nfunction formatRunPeriod(from,to){\n  if(!from || !to) return \'—\';\n  const opts={day:\'2-digit\',month:\'short\'};\n  const a=new Date(from+\'T00:00:00\');\n  const b=new Date(to+\'T00:00:00\');\n  return a.toLocaleDateString(\'en-GB\',opts)+\' — \'+b.toLocaleDateString(\'en-GB\',opts);\n}\nfunction nextUseRadio(name){\n  return \'<input type="radio" name="\'+name+\'">\';\n}\nfunction createBacktestRun(){\n  const from=document.getElementById(\'btRunFrom\').value;\n  const to=document.getElementById(\'btRunTo\').value;\n  if(!from || !to) return;\n  const table=document.getElementById(\'backtestRunsTable\');\n  const body=table ? table.querySelector(\'tbody\') : null;\n  if(!body) return;\n  const id=\'BT-\'+String(mockBtCounter++).padStart(3,\'0\');\n  const tr=document.createElement(\'tr\');\n  tr.innerHTML=\n    \'<td><button class="link">\'+id+\'</button></td>\'+\n    \'<td><span class="run-status inline-running"><span class="run-spinner"></span>Running</span></td>\'+\n    \'<td>\'+formatRunPeriod(from,to)+\'</td>\'+\n    \'<td>—</td><td>—</td><td>—</td><td>—</td><td>—</td>\'+\n    \'<td>\'+nextUseRadio(\'btUse\')+\'</td>\';\n  body.prepend(tr);\n  closeBacktestRunModal();\n\n  // Visual mock only: keep the row in Running state for a moment,\n  // then show illustrative completed metrics.\n  setTimeout(()=>{\n    const status=tr.children[1];\n    status.innerHTML=\'<span class="run-status completed">Completed</span>\';\n    tr.children[3].textContent=\'298\';\n    tr.children[4].innerHTML=\'<span class="pos">+$486.30</span>\';\n    tr.children[5].textContent=\'57.4%\';\n    tr.children[6].textContent=\'1.19\';\n    tr.children[7].innerHTML=\'<span class="neg">−4.9%</span>\';\n  },1200);\n}\nfunction startDemoRun(){\n  const table=document.getElementById(\'demoRunsTable\');\n  const body=table ? table.querySelector(\'tbody\') : null;\n  if(!body) return;\n  const id=\'DM-\'+String(mockDemoCounter++).padStart(3,\'0\');\n  const now=new Date();\n  const opts={day:\'2-digit\',month:\'short\',hour:\'2-digit\',minute:\'2-digit\'};\n  const started=now.toLocaleString(\'en-GB\',opts).replace(\',\',\' ·\');\n  const tr=document.createElement(\'tr\');\n  tr.innerHTML=\n    \'<td><button class="link">\'+id+\'</button></td>\'+\n    \'<td><span class="run-status running">Running</span></td>\'+\n    \'<td>\'+started+\' — now</td>\'+\n    \'<td>0</td><td>$0.00</td><td>—</td><td>—</td><td>—</td>\'+\n    \'<td>\'+nextUseRadio(\'demoUse\')+\'</td>\';\n  body.prepend(tr);\n}\n</script>\n\n\n<script id="research-new-research-js">\nlet researchCounter = 5;\n\nfunction openNewResearchModal(){\n  const m = document.getElementById(\'newResearchModal\');\n  if(m) m.classList.add(\'open\');\n}\nfunction closeNewResearchModal(){\n  const m = document.getElementById(\'newResearchModal\');\n  if(m) m.classList.remove(\'open\');\n}\n\nfunction createNewResearch(){\n  const setValue = document.getElementById(\'newResearchSet\').value;\n  const rulesValue = document.getElementById(\'newResearchRules\').value.replace(\'Rules · \',\'\');\n  const body = document.getElementById(\'researchTableBody\');\n  if(!body) return;\n\n  const tr = document.createElement(\'tr\');\n  tr.innerHTML = `\n    <td><button class="link" onclick="openResearchSet(\'${setValue.split(\' · \')[0]}\')">${setValue}</button></td>\n    <td><button class="link" onclick="showPage(\'rules\')">${document.getElementById(\'newResearchRules\').value}</button></td>\n    <td>—</td>\n    <td>—</td>\n    <td>—</td>\n    <td>Draft</td>\n  `;\n  body.prepend(tr);\n  closeNewResearchModal();\n}\n\nfunction setDecisionState(state){\n  const label = document.getElementById(\'decisionStateInline\');\n  const actions = document.getElementById(\'decisionActionsInline\');\n  if(label) label.textContent = state;\n\n  if(!actions) return;\n\n  if(state === \'Demo running\'){\n    actions.innerHTML = \'\';\n    return;\n  }\n  if(state === \'Archived\'){\n    actions.innerHTML = \'\';\n    return;\n  }\n  if(state === \'Made active\'){\n    actions.innerHTML = \'\';\n    return;\n  }\n  actions.innerHTML = `\n    <button class="btn" onclick="archiveResearch()">Archive</button>\n    <button class="btn primary-rule" onclick="makeResearchActive()">Make Active</button>\n  `;\n}\n\nfunction archiveResearch(){\n  setDecisionState(\'Archived\');\n}\nfunction makeResearchActive(){\n  setDecisionState(\'Made active\');\n}\n</script>\n\n\n<script id="research-interactive-v2-js">\n(function(){\n  const activeBenchmark = { days: 12, trades: 91, winRate: 55.7, profitFactor: 1.28, netPL: 81.20, maxDrawdown: -2.8 };\n\n  let currentResearchId = "R-001";\n  let backtestCounter = 15;\n  let demoCounter = 8;\n\n  const researches = [\n    {\n      id:"R-001",\n      setName:"Set 2", setVersion:"v5",\n      rulesVersion:"v3", rulesLabel:"Rules · v3",\n      decision:"Demo running",\n      backtests:[\n        {id:"BT-014", status:"Completed", period:"08 Jun — 05 Sep", trades:311, netPL:550.12, winRate:58.2, profitFactor:1.22, maxDrawdown:-4.7, selected:true},\n        {id:"BT-013", status:"Completed", period:"01 Jun — 31 Aug", trades:286, netPL:469.88, winRate:56.1, profitFactor:1.18, maxDrawdown:-5.1, selected:false}\n      ],\n      demos:[\n        {id:"DM-006", status:"Running", period:"05 Sep — now", days:3, trades:84, netPL:88.74, winRate:60.0, profitFactor:1.34, maxDrawdown:-1.9, selected:true},\n        {id:"DM-005", status:"Stopped", period:"02 Sep — 04 Sep", days:2, trades:63, netPL:54.21, winRate:57.1, profitFactor:1.21, maxDrawdown:-2.2, selected:false}\n      ]\n    },\n    {\n      id:"R-002",\n      setName:"Set 3", setVersion:"v6",\n      rulesVersion:"v2", rulesLabel:"Rules · v2",\n      decision:"Decision needed",\n      backtests:[\n        {id:"BT-011", status:"Completed", period:"08 Jun — 05 Sep", trades:286, netPL:402.55, winRate:54.6, profitFactor:1.18, maxDrawdown:-5.3, selected:true}\n      ],\n      demos:[\n        {id:"DM-004", status:"Stopped", period:"05 Sep — 07 Sep", days:2, trades:71, netPL:-6.80, winRate:48.2, profitFactor:0.94, maxDrawdown:-3.4, selected:true}\n      ]\n    },\n    {\n      id:"R-003",\n      setName:"Set 4", setVersion:"v7",\n      rulesVersion:"v1", rulesLabel:"Rules · v1",\n      decision:"Archived",\n      backtests:[\n        {id:"BT-009", status:"Completed", period:"08 Jun — 05 Sep", trades:304, netPL:-42.11, winRate:45.5, profitFactor:0.88, maxDrawdown:-6.0, selected:true}\n      ],\n      demos:[]\n    }\n  ];\n\n  function fmtNum(n, digits=2){\n    if(n === null || n === undefined || n === \'\') return \'—\';\n    return Number(n).toFixed(digits).replace(/\\.00$/,\'\');\n  }\n  function fmtPF(n){ return n === null || n === undefined ? \'—\' : Number(n).toFixed(2); }\n  function fmtTrades(n){ return (n === null || n === undefined) ? \'—\' : `${n} trades`; }\n  function fmtPL(n){\n    if(n === null || n === undefined) return \'—\';\n    return `${n >= 0 ? \'+\' : \'−\'}$${Math.abs(n).toFixed(2)}`;\n  }\n  function fmtPct(n, suffix=\'%\'){\n    if(n === null || n === undefined) return \'—\';\n    return `${n >= 0 ? \'\' : \'−\'}${Math.abs(n).toFixed(1)}${suffix}`;\n  }\n  function statusClass(decision){\n    if(decision === \'Demo running\') return \'running\';\n    if(decision === \'Decision needed\') return \'attention\';\n    if(decision === \'Archived\') return \'archived\';\n    if(decision === \'Made active\') return \'running\';\n    return \'muted\';\n  }\n  function decisionClass(decision){\n    if(decision === \'Draft\') return \'draft\';\n    if(decision === \'Demo running\') return \'running\';\n    if(decision === \'Archived\') return \'archived\';\n    if(decision === \'Made active\') return \'active\';\n    return \'\';\n  }\n  function selectedRun(list){ return (list || []).find(r => r.selected) || null; }\n  function hasRunningDemo(r){ return (r.demos || []).some(d => d.status === \'Running\'); }\n  function flowStateBacktest(r){ return r.backtests.length ? \'Completed\' : \'Draft\'; }\n  function flowStateDemo(r){\n    if(hasRunningDemo(r)) return \'Running\';\n    if(r.demos.length) return \'Stopped\';\n    return \'Draft\';\n  }\n  function flowStateCompare(r){ return selectedRun(r.demos) ? \'Available\' : \'Not available\'; }\n  function flowStateDecision(r){ return r.decision; }\n\n  function compareMetrics(r){\n    const demo = selectedRun(r.demos);\n    if(!demo) return null;\n\n    let better = 0;\n    if(demo.winRate > activeBenchmark.winRate) better += 1;\n    if(demo.profitFactor > activeBenchmark.profitFactor) better += 1;\n    if(demo.netPL > activeBenchmark.netPL) better += 1;\n    if(demo.maxDrawdown > activeBenchmark.maxDrawdown) better += 1; // less negative is better\n\n    return {\n      better,\n      demoDays: demo.days ?? \'—\',\n      demoTrades: demo.trades ?? \'—\',\n      demoWinRate: demo.winRate ?? null,\n      demoPF: demo.profitFactor ?? null,\n      demoPL: demo.netPL ?? null,\n      demoDD: demo.maxDrawdown ?? null,\n      diffTrades: (demo.trades ?? 0) - activeBenchmark.trades,\n      diffWinRate: (demo.winRate ?? 0) - activeBenchmark.winRate,\n      diffPF: (demo.profitFactor ?? 0) - activeBenchmark.profitFactor,\n      diffPL: (demo.netPL ?? 0) - activeBenchmark.netPL,\n      diffDD: (demo.maxDrawdown ?? 0) - activeBenchmark.maxDrawdown\n    };\n  }\n\n  function compareSummaryText(r){\n    const c = compareMetrics(r);\n    if(!c) return \'—\';\n    return `${c.better} of 4 better`;\n  }\n  function compareSummaryClass(r){\n    const c = compareMetrics(r);\n    if(!c) return \'muted\';\n    if(c.better >= 3) return \'better\';\n    if(c.better <= 1) return \'weak\';\n    return \'neutral\';\n  }\n\n  function showResearchList(){\n    const list = document.querySelector(\'.research-list\');\n    const detail = document.getElementById(\'researchDetail\');\n    if(list) list.style.display = \'block\';\n    if(detail) detail.classList.remove(\'open\');\n  }\n\n  function renderSummary(){\n    const body = document.getElementById(\'researchSummaryBody\');\n    if(!body) return;\n    body.innerHTML = researches.map(r => {\n      const bt = selectedRun(r.backtests);\n      const demo = selectedRun(r.demos);\n      return `\n        <tr data-research-id="${r.id}" onclick="openResearchById(\'${r.id}\')">\n          <td><button class="research-object-link" onclick="event.stopPropagation();openSetFromResearch(\'${r.setName}\',\'${r.setVersion}\')"><span>${r.setName}</span><small>${r.setVersion}</small></button></td>\n          <td><button class="research-object-link" onclick="event.stopPropagation();openRulesVersion(\'${r.rulesVersion}\')"><span>Rules</span><small>${r.rulesVersion}</small></button></td>\n          <td>${bt ? `<div class="pf-cell"><span class="pf-value">${fmtPF(bt.profitFactor)}</span><span class="pf-trades">${fmtTrades(bt.trades)}</span></div>` : \'<span class="pf-empty">—</span>\'}</td>\n          <td>${demo ? `<div class="pf-cell"><span class="pf-value">${fmtPF(demo.profitFactor)}</span><span class="pf-trades">${fmtTrades(demo.trades)}</span></div>` : \'<span class="pf-empty">—</span>\'}</td>\n          <td><span class="compare-result ${compareSummaryClass(r)}">${compareSummaryText(r)}</span></td>\n          <td><span class="decision-status ${statusClass(r.decision)}">${r.decision}</span></td>\n        </tr>\n      `;\n    }).join(\'\');\n  }\n\n  function getCurrentResearch(){\n    return researches.find(r => r.id === currentResearchId) || researches[0];\n  }\n\n  function renderRuns(kind, runs){\n    const emptyMessage = kind === \'backtest\' ? \'No backtest runs yet\' : \'No demo runs yet\';\n    if(!runs.length){\n      return `<tr class="empty-run-row"><td colspan="9">${emptyMessage}</td></tr>`;\n    }\n    return runs.map((run, idx) => `\n      <tr>\n        <td><button class="link">${run.id}</button></td>\n        <td><span class="run-status ${String(run.status).toLowerCase().replace(/\\s+/g,\'-\')}">${run.status}</span></td>\n        <td>${run.period}</td>\n        <td>${run.trades ?? \'—\'}</td>\n        <td class="${run.netPL < 0 ? \'neg\' : \'pos\'}">${run.netPL === null || run.netPL === undefined ? \'—\' : fmtPL(run.netPL)}</td>\n        <td>${run.winRate === null || run.winRate === undefined ? \'—\' : fmtPct(run.winRate)}</td>\n        <td>${run.profitFactor === null || run.profitFactor === undefined ? \'—\' : `<b>${fmtPF(run.profitFactor)}</b>`}</td>\n        <td class="${run.maxDrawdown < 0 ? \'neg\' : \'\'}">${run.maxDrawdown === null || run.maxDrawdown === undefined ? \'—\' : fmtPct(run.maxDrawdown)}</td>\n        <td class="run-use-cell"><input type="radio" name="${kind}Use" ${run.selected ? \'checked\' : \'\'} onchange="setSelectedRun(\'${kind}\',${idx})"></td>\n      </tr>\n    `).join(\'\');\n  }\n\n  function renderComparePanel(r){\n    const panel = document.getElementById(\'comparePanel\');\n    if(!panel) return;\n    const c = compareMetrics(r);\n    let body = \'\';\n    if(!c){\n      body = `<div class="compare-empty">Compare becomes available after a Demo run is selected.</div>`;\n    } else {\n      const diffClass = (val, mode=\'normal\') => {\n        if(mode === \'neutral\') return \'diff-neutral\';\n        if(val > 0) return \'diff-pos\';\n        if(val < 0) return \'diff-neg\';\n        return \'diff-neutral\';\n      };\n      body = `\n        <div class="compare-head"><div></div><div class="compare-label">Research Demo</div><div class="compare-label">Active</div><div class="compare-label">Difference</div></div>\n        <div class="compare-row">\n          <div>Days</div><div>${c.demoDays}</div><div>${activeBenchmark.days}</div><div class="diff-neutral">—</div>\n        </div>\n        <div class="compare-row">\n          <div>Closed trades</div><div>${c.demoTrades}</div><div>${activeBenchmark.trades}</div><div class="diff-neutral">${c.diffTrades > 0 ? \'+\' : \'\'}${c.diffTrades}</div>\n        </div>\n        <div class="compare-row">\n          <div>Win Rate</div><div>${fmtPct(c.demoWinRate)}</div><div>${fmtPct(activeBenchmark.winRate)}</div><div class="${diffClass(c.diffWinRate)}">${c.diffWinRate > 0 ? \'+\' : \'−\'}${Math.abs(c.diffWinRate).toFixed(1)} pp</div>\n        </div>\n        <div class="compare-row">\n          <div>Profit Factor</div><div>${fmtPF(c.demoPF)}</div><div>${fmtPF(activeBenchmark.profitFactor)}</div><div class="${diffClass(c.diffPF)}">${c.diffPF > 0 ? \'+\' : \'−\'}${Math.abs(c.diffPF).toFixed(2)}</div>\n        </div>\n        <div class="compare-row">\n          <div>Net P/L</div><div class="${c.demoPL < 0 ? \'neg\' : \'pos\'}">${fmtPL(c.demoPL)}</div><div class="${activeBenchmark.netPL < 0 ? \'neg\' : \'pos\'}">${fmtPL(activeBenchmark.netPL)}</div><div class="${diffClass(c.diffPL)}">${fmtPL(c.diffPL)}</div>\n        </div>\n        <div class="compare-row">\n          <div>Max Drawdown</div><div>${fmtPct(c.demoDD)}</div><div>${fmtPct(activeBenchmark.maxDrawdown)}</div><div class="${c.diffDD > 0 ? \'diff-pos\' : c.diffDD < 0 ? \'diff-neg\' : \'diff-neutral\'}">${c.diffDD > 0 ? \'+\' : \'−\'}${Math.abs(c.diffDD).toFixed(1)} pp</div>\n        </div>\n      `;\n    }\n    panel.innerHTML = `<div class="panelhead"><div class="title">Compare Demo to Active</div></div>${body}`;\n  }\n\n  function renderDecision(r){\n    const label = document.getElementById(\'decisionStateInline\');\n    const actions = document.getElementById(\'decisionActionsInline\');\n    if(label){\n      label.textContent = r.decision;\n      label.className = `decision-state-inline ${decisionClass(r.decision)}`;\n    }\n    if(!actions) return;\n    if(r.decision === \'Decision needed\'){\n      actions.innerHTML = `\n        <button class="btn" onclick="archiveResearch()">Archive</button>\n        <button class="btn primary-rule" onclick="makeResearchActive()">Make Active</button>\n      `;\n    } else {\n      actions.innerHTML = \'\';\n    }\n  }\n\n  \n  function applyPipelineState(el, state){\n    if(!el) return;\n    const step = el.closest(\'.research-flow-step\');\n    if(!step) return;\n    step.classList.remove(\'done\',\'active\',\'state-draft\',\'state-done\',\'state-running\',\'state-available\',\'state-pending\');\n    let cls = \'state-draft\';\n    if(state === \'Completed\') cls = \'state-done\';\n    else if(state === \'Running\') cls = \'state-running\';\n    else if(state === \'Available\') cls = \'state-available\';\n    else if(state === \'Decision needed\') cls = \'state-pending\';\n    else if(state === \'Archived\' || state === \'Made active\') cls = \'state-done\';\n    step.classList.add(cls);\n  }\n\nfunction renderDetail(){\n    const r = getCurrentResearch();\n    const list = document.querySelector(\'.research-list\');\n    const detail = document.getElementById(\'researchDetail\');\n    if(list) list.style.display = \'none\';\n    if(detail) detail.classList.add(\'open\');\n\n    const setLink = document.getElementById(\'researchDetailSetLink\');\n    const rulesLink = document.getElementById(\'researchDetailRulesLink\');\n    if(setLink){\n      setLink.textContent = `${r.setName} · ${r.setVersion}`;\n      setLink.onclick = () => openSetFromResearch(r.setName, r.setVersion);\n    }\n    if(rulesLink){\n      rulesLink.textContent = r.rulesLabel;\n      rulesLink.onclick = () => openRulesVersion(r.rulesVersion);\n    }\n\n    const f1 = document.getElementById(\'flowBacktestState\');\n    const f2 = document.getElementById(\'flowDemoState\');\n    const f3 = document.getElementById(\'flowCompareState\');\n    const f4 = document.getElementById(\'flowDecisionState\');\n\n    const s1 = r.backtests.length ? (r.backtests.some(x => x.status === \'Running\') ? \'Running\' : \'Completed\') : \'Not started\';\n    const s2 = hasRunningDemo(r) ? \'Running\' : (r.demos.length ? \'Stopped\' : \'Not started\');\n    const s3 = selectedRun(r.demos) ? \'Available\' : \'Not available\';\n    const s4 = r.decision === \'Draft\' ? \'Not ready\' : r.decision;\n\n    if(f1){ f1.textContent = s1; applyPipelineState(f1, s1); }\n    if(f2){ f2.textContent = s2; applyPipelineState(f2, s2); }\n    if(f3){ f3.textContent = s3; applyPipelineState(f3, s3); }\n    if(f4){ f4.textContent = s4; applyPipelineState(f4, s4); }\n\n    const btBody = document.getElementById(\'backtestRunsBody\');\n    const dmBody = document.getElementById(\'demoRunsBody\');\n    if(btBody) btBody.innerHTML = renderRuns(\'backtest\', r.backtests);\n    if(dmBody) dmBody.innerHTML = renderRuns(\'demo\', r.demos);\n\n    renderComparePanel(r);\n    renderDecision(r);\n\n    const demoBtn = document.getElementById(\'demoToggleBtn\');\n    if(demoBtn){\n      demoBtn.textContent = hasRunningDemo(r) ? \'Stop Demo\' : \'Run\';\n    }\n  }\n\n  // Expose functions.\n  window.openResearchById = function(id){\n    currentResearchId = id;\n    renderDetail();\n  };\n\n  window.openResearchSet = function(name){\n    const found = researches.find(r => r.setName === name);\n    currentResearchId = found ? found.id : researches[0].id;\n    renderDetail();\n  };\n\n  window.closeResearchSet = function(){\n    showResearchList();\n  };\n\n  window.setSelectedRun = function(kind, idx){\n    const r = getCurrentResearch();\n    const list = kind === \'backtest\' ? r.backtests : r.demos;\n    list.forEach((item, i) => item.selected = i === idx);\n    if(kind === \'demo\' && hasRunningDemo(r)) r.decision = \'Demo running\';\n    renderSummary();\n    renderDetail();\n  };\n\n  window.createNewResearch = function(){\n    const setValue = document.getElementById(\'newResearchSet\').value;\n    const rulesRaw = document.getElementById(\'newResearchRules\').value;\n    const rulesVersion = rulesRaw.replace(\'Rules · \',\'\');\n    const rulesLabel = rulesRaw;\n    const [setName, setVersion] = setValue.split(\' · \');\n    const newResearch = {\n      id:`R-00${researches.length+1}`,\n      setName, setVersion,\n      rulesVersion,\n      rulesLabel,\n      decision:\'Draft\',\n      backtests:[],\n      demos:[]\n    };\n    researches.unshift(newResearch);\n    currentResearchId = newResearch.id;\n    if(typeof closeNewResearchModal === \'function\') closeNewResearchModal();\n    renderSummary();\n    renderDetail();\n  };\n\n  window.archiveResearch = function(){\n    const r = getCurrentResearch();\n    r.decision = \'Archived\';\n    renderSummary();\n    renderDetail();\n  };\n\n  window.makeResearchActive = function(){\n    const r = getCurrentResearch();\n    r.decision = \'Made active\';\n    // if there is a running demo, stop it visually\n    const running = r.demos.find(d => d.status === \'Running\');\n    if(running){\n      running.status = \'Stopped\';\n      running.period = running.period.replace(\'— now\', \'— today\');\n    }\n    renderSummary();\n    renderDetail();\n  };\n\n  window.toggleDemoRun = function(){\n    const r = getCurrentResearch();\n    const running = r.demos.find(d => d.status === \'Running\');\n    if(running){\n      running.status = \'Stopped\';\n      running.period = running.period.replace(\'— now\', \'— today\');\n      if(running.days == null) running.days = 1;\n      r.decision = \'Decision needed\';\n    } else {\n      const id = `DM-${String(demoCounter++).padStart(3,\'0\')}`;\n      r.demos.forEach(d => d.selected = false);\n      r.demos.unshift({\n        id,\n        status:\'Running\',\n        period:\'Today — now\',\n        days:1,\n        trades:12,\n        netPL:14.22,\n        winRate:58.3,\n        profitFactor:1.11,\n        maxDrawdown:-0.8,\n        selected:true\n      });\n      r.decision = \'Demo running\';\n    }\n    renderSummary();\n    renderDetail();\n  };\n\n  window.openBacktestRunModal = function(){\n    const modal = document.getElementById(\'backtestRunModal\');\n    if(modal) modal.classList.add(\'open\');\n  };\n  window.closeBacktestRunModal = function(){\n    const modal = document.getElementById(\'backtestRunModal\');\n    if(modal) modal.classList.remove(\'open\');\n  };\n  function formatRunPeriod(from,to){\n    if(!from || !to) return \'—\';\n    const opts={day:\'2-digit\',month:\'short\'};\n    const a=new Date(from+\'T00:00:00\');\n    const b=new Date(to+\'T00:00:00\');\n    return a.toLocaleDateString(\'en-GB\',opts)+\' — \'+b.toLocaleDateString(\'en-GB\',opts);\n  }\n  window.createBacktestRun = function(){\n    const from = document.getElementById(\'btRunFrom\').value;\n    const to = document.getElementById(\'btRunTo\').value;\n    if(!from || !to) return;\n    const r = getCurrentResearch();\n    const id = `BT-${String(backtestCounter++).padStart(3,\'0\')}`;\n    r.backtests.forEach(b => b.selected = false);\n    const newRun = {\n      id, status:\'Running\', period:formatRunPeriod(from,to),\n      trades:null, netPL:null, winRate:null, profitFactor:null, maxDrawdown:null,\n      selected:true\n    };\n    r.backtests.unshift(newRun);\n    closeBacktestRunModal();\n    renderSummary();\n    renderDetail();\n\n    setTimeout(() => {\n      newRun.status = \'Completed\';\n      newRun.trades = 298;\n      newRun.netPL = 486.30;\n      newRun.winRate = 57.4;\n      newRun.profitFactor = 1.19;\n      newRun.maxDrawdown = -4.9;\n      // Backtest completion alone does not require a final decision.\n      renderSummary();\n      renderDetail();\n    }, 900);\n  };\n\n  // Ensure top Research tab returns to the list view.\n  const originalShowPage = window.showPage;\n  if(originalShowPage){\n    window.showPage = function(id){\n      originalShowPage(id);\n      if(id === \'research\') showResearchList();\n    };\n    document.querySelectorAll(\'.tab[data-page="research"]\').forEach(t => {\n      t.onclick = () => window.showPage(\'research\');\n    });\n  }\n\n  // Initial render\n  renderSummary();\n})();\n</script>\n\n\n<script id="research-summary-sync-fix">\n(function(){\n  function refreshResearchSummarySafely(){\n    const body = document.getElementById(\'researchSummaryBody\');\n    if(body && typeof window.openResearchById === \'function\'){\n      // renderSummary is private to the interactive closure, so state-changing\n      // handlers already call it. This function exists only as a DOM sanity check.\n      body.dataset.synced = \'true\';\n    }\n  }\n  document.addEventListener(\'change\', function(e){\n    if(e.target && e.target.matches(\'#researchDetail input[type="radio"]\')){\n      setTimeout(refreshResearchSummarySafely, 0);\n    }\n  });\n})();\n</script>\n\n</body>\n</html>'


def _fixture_boundary_html(*, portfolio_live: bool, registry_live: bool) -> str:
    if portfolio_live and registry_live:
        return (
            '<div class="fixture-boundary" role="note">'
            "UI fixture preview boundary: Portfolio, Sets and Trigger Catalog are backed by runtime read models. "
            "Rules and Research may still include non-persistent UI preview state until their backend contracts are wired; "
            "those preview values are not live trading/account facts."
            "</div>"
        )
    if portfolio_live:
        return (
            '<div class="fixture-boundary" role="note">'
            "UI fixture preview boundary: Portfolio is backed by runtime read models. "
            "Sets, Rules and Research may still include non-persistent UI preview state "
            "until their backend contracts are wired; those preview values are not live trading/account facts."
            "</div>"
        )
    return (
        '<div class="fixture-boundary" role="note">'
        "UI fixture preview: displayed balances, positions, rules and research rows are "
        "non-persistent and are not live trading/account facts."
        "</div>"
    )


def _operator_forms_html(token: str) -> str:
    safe_token = escape(token, quote=True)
    return (
        '<form id="operatorPauseForm" method="post" action="/operator/pause" hidden>'
        '<input type="hidden" name="confirm" value="yes">'
        f'<input type="hidden" name="token" value="{safe_token}">'
        "</form>"
        '<form id="operatorResumeForm" method="post" action="/operator/resume" hidden>'
        '<input type="hidden" name="confirm" value="yes">'
        f'<input type="hidden" name="token" value="{safe_token}">'
        "</form>"
        '<form id="operatorCloseOneForm" method="post" action="/operator/close-one" hidden>'
        '<input type="hidden" name="confirm" value="yes">'
        f'<input type="hidden" name="token" value="{safe_token}">'
        '<input type="hidden" name="position_id" value="">'
        '<input type="hidden" name="symbol" value="">'
        "</form>"
        '<form id="operatorCloseAllForm" method="post" action="/operator/close-all" hidden>'
        '<input type="hidden" name="confirm" value="yes">'
        f'<input type="hidden" name="token" value="{safe_token}">'
        '<input type="hidden" name="phrase" value="CLOSE ALL">'
        "</form>"
    )


def _server_boundary_script(state: str, has_operator_token: bool) -> str:
    state_json = json.dumps(state)
    return """
<script id="triggertrade-server-boundaries">
(function(){
  const operatorState = %s;
  const canSubmitOperatorControl = %s;
  let serverControlAction = null;

  function applyOperatorControlLabels(){
    document.querySelectorAll(".stop-new").forEach((button) => {
      if(operatorState === "TRADING_PAUSED"){
        button.textContent = "Resume Entries";
        button.setAttribute("aria-label", "Resume Entries");
      } else {
        button.textContent = "Pause Entries";
        button.setAttribute("aria-label", "Pause Entries");
      }
    });
  }

  const originalOpenControlModal = window.openControlModal;
  const originalConfirmControlAction = window.confirmControlAction;
  let serverClosePosition = null;
  window.openSingleCloseById = function(positionId, symbol){
    serverClosePosition = {positionId, symbol};
    serverControlAction = "single-close";
    if(typeof window.openSingleClose === "function"){
      window.openSingleClose(symbol);
    }
  };
  window.openControlModal = function(action){
    const normalizedAction = action === "pause" && operatorState === "TRADING_PAUSED" ? "resume" : action;
    if(normalizedAction !== "pause" && normalizedAction !== "resume"){
      serverControlAction = normalizedAction;
      if(typeof originalOpenControlModal === "function"){
        originalOpenControlModal(normalizedAction);
      }
      return;
    }
    serverControlAction = normalizedAction;
    if(normalizedAction === "pause" && typeof originalOpenControlModal === "function"){
      originalOpenControlModal(normalizedAction);
    } else {
      confirmInput.value = "";
      controlTitle.textContent = "Resume new entries?";
      controlMeta.textContent = "Protected trading control";
      controlNotice.textContent = "The bot may open new ACTIVE positions again after this confirmation.";
      confirmField.style.display = "none";
      controlConfirm.textContent = "Resume Entries";
      controlModal.classList.add("open");
    }
  };

  window.confirmControlAction = function(){
    if(serverControlAction === "pause" || serverControlAction === "resume"){
      const formId = serverControlAction === "resume" ? "operatorResumeForm" : "operatorPauseForm";
      const form = document.getElementById(formId);
      if(canSubmitOperatorControl && form){
        form.submit();
        return;
      }
      closeControlModal();
      return;
    }
    if(serverControlAction === "single-close"){
      const form = document.getElementById("operatorCloseOneForm");
      if(canSubmitOperatorControl && form && serverClosePosition){
        form.querySelector('input[name="position_id"]').value = serverClosePosition.positionId;
        form.querySelector('input[name="symbol"]').value = serverClosePosition.symbol;
        form.submit();
        return;
      }
      closeControlModal();
      return;
    }
    if(serverControlAction === "close"){
      const form = document.getElementById("operatorCloseAllForm");
      if(canSubmitOperatorControl && form){
        form.submit();
        return;
      }
      closeControlModal();
      return;
    }
    if(typeof originalConfirmControlAction === "function"){
      originalConfirmControlAction();
    }
  };

  applyOperatorControlLabels();
})();
</script>
""" % (
        state_json,
        "true" if has_operator_token else "false",
    )


def _safe_payload(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _safe_payload(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [_safe_payload(item) for item in value]
    if isinstance(value, list):
        return [_safe_payload(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _safe_payload(item) for key, item in value.items()}
    return value


def _portfolio_wiring_script(portfolio: dict[str, Any] | None) -> str:
    if portfolio is None:
        return ""
    payload = json.dumps(_safe_payload(portfolio), ensure_ascii=False).replace("</", "<\\/")
    script = """
<script id="triggertrade-portfolio-read-model">
(function(){
  const portfolio = __PORTFOLIO_PAYLOAD__;
  const money = (value) => value === null || value === undefined || value === "" ? "—" : "$" + String(value);
  const count = (value) => value === null || value === undefined ? "—" : String(value);
  const signedClass = (value) => {
    const text = String(value || "").trim();
    if(text.startsWith("-") || text.startsWith("−")) return "neg";
    if(text.startsWith("+") || (!text.startsWith("—") && Number(text) > 0)) return "pos";
    return "";
  };
  const signedMoney = (value) => {
    if(value === null || value === undefined || value === "") return "—";
    const n = Number(value);
    if(Number.isNaN(n)) return "$" + String(value);
    return (n >= 0 ? "+$" : "−$") + Math.abs(n).toFixed(2);
  };
  const pct = (value) => {
    if(value === null || value === undefined || value === "") return "—";
    const n = Number(value);
    if(Number.isNaN(n)) return String(value) + "%";
    return (n >= 0 ? "+" : "−") + Math.abs(n).toFixed(2) + "%";
  };
  const duration = (seconds) => {
    if(seconds === null || seconds === undefined) return "—";
    const s = Math.max(0, Number(seconds) || 0);
    if(s < 60) return String(s) + "s";
    if(s < 3600) return Math.floor(s / 60) + "m";
    return Math.floor(s / 3600) + "h " + Math.floor((s % 3600) / 60) + "m";
  };
  const sideBadge = (side) => side === "LONG" ? '<span class="badge green">LONG</span>' : '<span class="badge red">SHORT</span>';
  const html = (value) => String(value ?? "—").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const selectedFilter = (select, prefix) => {
    if(!select) return "";
    return String(select.value || "").replace(prefix, "").trim();
  };
  const filterRows = (rows, mode) => {
    const selects = document.querySelectorAll("#portfolio .filters select");
    const symbol = selectedFilter(selects[0], "Coin:");
    const side = selectedFilter(selects[1], "Side:");
    const setVersion = selectedFilter(selects[2], "Set:");
    const closeReason = selectedFilter(document.getElementById("closeReasonFilter"), "Close reason:");
    return rows.filter(row => {
      if(symbol && symbol !== "All" && row.symbol !== symbol) return false;
      if(side && side !== "All" && row.side !== side) return false;
      if(setVersion && setVersion !== "All" && row.set_version !== setVersion) return false;
      if(mode === "closed" && closeReason && closeReason !== "All" && String(row.close_reason).replace(/_/g, " ") !== closeReason.toUpperCase().replace(/ /g, "_").replace(/_/g, " ")) return false;
      return true;
    });
  };
  function setKpis(){
    const values = [
      money(portfolio.snapshot.total_equity),
      money(portfolio.snapshot.available_capital),
      money(portfolio.snapshot.in_positions),
      signedMoney(portfolio.snapshot.realized_pnl_today),
      signedMoney(portfolio.snapshot.unrealized_pnl),
      count(portfolio.snapshot.open_positions_count)
    ];
    document.querySelectorAll("#portfolio .kpi .kvalue").forEach((node, index) => {
      node.textContent = values[index] || "—";
      node.classList.toggle("pos", index >= 3 && signedClass(values[index]) === "pos");
      node.classList.toggle("neg", index >= 3 && signedClass(values[index]) === "neg");
    });
    const last = document.querySelector("#portfolio .subtle-status span");
    if(last) last.textContent = portfolio.snapshot.as_of === "-" ? "Last update —" : "Last update " + portfolio.snapshot.as_of;
  }
  function setFilters(){
    const selects = document.querySelectorAll("#portfolio .filters select");
    const symbols = portfolio.filters.symbols.length ? portfolio.filters.symbols : ["All"];
    const sets = portfolio.filters.set_versions.length ? portfolio.filters.set_versions : ["All"];
    if(selects[0]) selects[0].innerHTML = '<option>Coin: All</option>' + symbols.map(v => `<option>${html(v)}</option>`).join("");
    if(selects[2]) selects[2].innerHTML = '<option>Set: All</option>' + sets.map(v => `<option>${html(v)}</option>`).join("");
  }
  window.setPositionMode = function(mode){
    const openFilterNode = document.getElementById("openFilter");
    const closedFilterNode = document.getElementById("closedFilter");
    const closeReasonNode = document.getElementById("closeReasonFilter");
    const positionHeadNode = document.getElementById("positionHead");
    const positionBodyNode = document.getElementById("positionBody");
    const positionSummaryNode = document.getElementById("positionSummary");
    if(!openFilterNode || !closedFilterNode || !closeReasonNode || !positionHeadNode || !positionBodyNode || !positionSummaryNode){
      return;
    }
    openFilterNode.classList.toggle("active", mode==="open");
    closedFilterNode.classList.toggle("active", mode==="closed");
    if(mode==="open"){
      closeReasonNode.style.display="none";
      positionHeadNode.innerHTML='<tr><th>Coin</th><th>Side</th><th>Leverage</th><th>Qty</th><th>Value</th><th>Entry</th><th title="Exchange mark price used for unrealized P&L and liquidation calculations">Current Price</th><th>Take Profit</th><th>Stop Loss</th><th>Unrealized P&L</th><th>Set</th><th>Age</th><th></th></tr>';
      const openRows = filterRows(portfolio.open_positions, "open");
      positionBodyNode.innerHTML = openRows.length ? openRows.map(r => {
        const pnlText = r.unrealized_pnl_pct === null || r.unrealized_pnl_amount === null ? "—" : `${pct(r.unrealized_pnl_pct)} · ${signedMoney(r.unrealized_pnl_amount)}`;
        const close = r.close_action_available ? `<button class="row-close" onclick="openSingleCloseById('${html(r.position_id)}','${html(r.symbol)}')">Close</button>` : '<button class="row-close" disabled>Close</button>';
        return `<tr><td class="coin">${html(r.symbol)}</td><td>${sideBadge(r.side)}</td><td>${html(r.leverage)}×</td><td>${html(r.qty)} ${html(r.qty_unit)}</td><td>${money(r.value)}</td><td>${money(r.entry_price)}</td><td>${money(r.current_price)}</td><td>${pct(r.take_profit_pct)} · ${money(r.take_profit_price)}</td><td>${pct(r.stop_loss_pct)} · ${money(r.stop_loss_price)}</td><td><span class="${signedClass(pnlText)}">${pnlText}</span></td><td><button class="link" onclick="showPage('sets')">${html(r.set_version || 'legacy/unknown')}</button></td><td>${duration(r.age_seconds)}</td><td>${close}</td></tr>`;
      }).join("") : '<tr><td colspan="13" class="placeholder">No open positions.</td></tr>';
      positionSummaryNode.innerHTML = `<span>Open <b>${count(portfolio.open_summary.open_count)}</b></span><span>Capital <b>${money(portfolio.open_summary.capital_in_open_positions)}</b></span><span>Unrealized P&L <b class="${signedClass(portfolio.open_summary.unrealized_pnl)}">${signedMoney(portfolio.open_summary.unrealized_pnl)}</b></span>`;
    } else {
      closeReasonNode.style.display="";
      positionHeadNode.innerHTML='<tr><th>Coin</th><th>Side</th><th>Leverage</th><th>Qty</th><th>Value</th><th>Entry</th><th>Exit</th><th>Planned TP</th><th>Planned SL</th><th>Realized P&L</th><th>Close reason</th><th>Set</th><th>Duration</th></tr>';
      const closedRows = filterRows(portfolio.closed_positions, "closed");
      positionBodyNode.innerHTML = closedRows.length ? closedRows.map(r => {
        const pnlText = `${pct(r.realized_pnl_pct)} · ${signedMoney(r.realized_pnl_amount)}`;
        return `<tr><td class="coin">${html(r.symbol)}</td><td>${sideBadge(r.side)}</td><td>${html(r.leverage)}×</td><td>${html(r.qty)} ${html(r.qty_unit)}</td><td>${money(r.value)}</td><td>${money(r.entry_price)}</td><td>${money(r.exit_price)}</td><td>${pct(r.planned_tp_pct)} · ${money(r.planned_tp_price)}</td><td>${pct(r.planned_sl_pct)} · ${money(r.planned_sl_price)}</td><td><span class="${signedClass(pnlText)}">${pnlText}</span></td><td>${html(String(r.close_reason).replace(/_/g, " "))}</td><td><button class="link" onclick="showPage('sets')">${html(r.set_version || 'legacy/unknown')}</button></td><td>${duration(r.duration_seconds)}</td></tr>`;
      }).join("") : '<tr><td colspan="13" class="placeholder">No closed positions for the selected period.</td></tr>';
      positionSummaryNode.innerHTML = `<span>Closed today <b>${count(portfolio.closed_summary.closed_today_count)}</b></span><span>Realized P&L <b class="${signedClass(portfolio.closed_summary.realized_pnl_today)}">${signedMoney(portfolio.closed_summary.realized_pnl_today)}</b></span><span>Win rate <b>${portfolio.closed_summary.win_rate_today === null ? "—" : portfolio.closed_summary.win_rate_today + "%"}</b></span>`;
    }
  };
  setKpis();
  setFilters();
  document.querySelectorAll("#portfolio .filters select").forEach(select => {
    select.addEventListener("change", () => window.setPositionMode(closedFilterNodeActive() ? "closed" : "open"));
  });
  function closedFilterNodeActive(){
    const node = document.getElementById("closedFilter");
    return !!node && node.classList.contains("active");
  }
  window.setPositionMode("open");
})();
</script>
"""
    return script.replace("__PORTFOLIO_PAYLOAD__", payload)


def _registry_wiring_script(registry: dict[str, Any] | None) -> str:
    if registry is None:
        return ""
    payload = json.dumps(_safe_payload(registry), ensure_ascii=False).replace("</", "<\\/")
    script = """
<script id="triggertrade-registry-read-model">
(function(){
  const registry = __REGISTRY_PAYLOAD__;
  const html = (value) => String(value ?? "—").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const attr = (value) => html(value).replace(/'/g, "&#39;");
  const statusBadge = (status) => {
    const normalized = String(status || "UNKNOWN").toUpperCase();
    let cls = "gray";
    if(normalized === "ACTIVE") cls = "green";
    else if(normalized === "TESTING") cls = "blue";
    else if(normalized === "DRAFT") cls = "amber";
    return `<span class="badge ${cls}">${html(normalized)}</span>`;
  };
  const empty = (cols, message) => `<tr><td colspan="${cols}" class="placeholder">${html(message)}</td></tr>`;
  function renderSets(){
    const body = document.querySelector("#sets table tbody");
    if(!body) return;
    if(registry.integrity_errors && registry.integrity_errors.length){
      body.innerHTML = empty(4, "Trigger Set registry integrity issue: " + registry.integrity_errors.join("; "));
      return;
    }
    const rows = registry.sets || [];
    body.innerHTML = rows.length ? rows.map(set => {
      const triggers = (set.trigger_versions || []).length
        ? `<div class="trigger-list">${set.trigger_versions.map(trigger => `<button class="link" onclick="openTriggerDetail('${attr(trigger.trigger_id)}','${attr(trigger.version)}')">${html(trigger.display_name)}</button>`).join("")}</div>`
        : '<span class="meta">No Trigger Versions recorded</span>';
      return `<tr data-set-id="${attr(set.set_id)}" data-set-version="${attr(set.version)}">
        <td class="coin">${html(set.display_name || set.set_id)}</td>
        <td>${html(set.version)}</td>
        <td>${statusBadge(set.status)}</td>
        <td>${triggers}</td>
      </tr>`;
    }).join("") : empty(4, "No Trigger Sets registered yet.");
  }

  function renderCatalog(){
    const body = document.querySelector("#trigger-catalog table tbody");
    if(!body) return;
    const rows = registry.triggers || [];
    body.innerHTML = rows.length ? rows.map(trigger => `
      <tr data-trigger-id="${attr(trigger.trigger_id)}" data-trigger-version="${attr(trigger.version)}">
        <td><button class="link" onclick="openTriggerDetail('${attr(trigger.trigger_id)}','${attr(trigger.version)}')">${html(trigger.display_name)}</button></td>
        <td>${html(trigger.version)}</td>
        <td>${html(trigger.what_it_checks || "unavailable")}</td>
      </tr>
    `).join("") : empty(3, "No Trigger Versions registered yet.");
  }

  function renderTriggerDetail(detail){
    const safeDetail = detail;
    const title = document.getElementById("triggerDetailTitle");
    const meta = document.querySelector("#trigger-detail .panelhead .meta");
    const explain = document.querySelector("#trigger-detail .explain-text");
    const formula = document.querySelector("#trigger-detail .formula-block");
    const tables = document.querySelectorAll("#trigger-detail table tbody");
    if(!safeDetail){
      if(title) title.textContent = "Trigger unavailable";
      if(meta) meta.textContent = "Version —";
      if(explain) explain.textContent = "Trigger registry unavailable.";
      if(formula) formula.textContent = "unavailable";
      if(tables[0]) tables[0].innerHTML = empty(3, "No parameters registered.");
      if(tables[1]) tables[1].innerHTML = empty(3, "No Set usage recorded.");
      if(tables[2]) tables[2].innerHTML = empty(3, "No version history recorded.");
      return;
    }
    if(title) title.textContent = `${safeDetail.display_name || safeDetail.trigger_id} · ${safeDetail.version}`;
    if(meta) meta.textContent = `Version ${safeDetail.version} · ${safeDetail.trigger_id}`;
    if(explain) explain.textContent = safeDetail.how_it_works || "unavailable";
    if(formula) formula.textContent = safeDetail.formula_text || "unavailable";
    if(tables[0]){
      const params = safeDetail.parameters || [];
      tables[0].innerHTML = params.length ? params.map(row => `<tr><td>${html(row.name)}</td><td>${html(row.value)}</td><td>${html(row.meaning)}</td></tr>`).join("") : empty(3, "No parameters registered for this Trigger Version.");
    }
    if(tables[1]){
      const used = safeDetail.used_in || [];
      tables[1].innerHTML = used.length ? used.map(row => `<tr><td>${html(row.set_name || row.set_id)}</td><td>${html(row.set_version)}</td><td>${statusBadge(row.set_status)}</td></tr>`).join("") : empty(3, "This Trigger Version is not used by any Set Version.");
    }
    if(tables[2]){
      const history = safeDetail.version_history || [];
      tables[2].innerHTML = history.length ? history.map(row => `<tr><td>${html(row.version)}</td><td>${html(row.created_at)}</td><td>${html(row.change_summary)}</td></tr>`).join("") : empty(3, "No version history recorded.");
    }
  }

  window.openTriggerDetail = function(triggerId, version){
    if(!triggerId || !version) return;
    window.location.href = `/triggers/${encodeURIComponent(triggerId)}/${encodeURIComponent(version)}`;
  };

  renderSets();
  renderCatalog();
  renderTriggerDetail(registry.selected_trigger);
})();
</script>
"""
    return script.replace("__REGISTRY_PAYLOAD__", payload)


def _strip_registry_fixtures(html: str, registry: dict[str, Any]) -> str:
    safe_registry = _safe_payload(registry)
    html = _replace_first_tbody(
        html,
        '<section class="page" id="sets">',
        '<section class="page" id="trigger-catalog">',
        _sets_rows_html(safe_registry),
    )
    html = _replace_first_tbody(
        html,
        '<section class="page" id="trigger-catalog">',
        '<section class="page" id="trigger-detail">',
        _trigger_catalog_rows_html(safe_registry),
    )
    detail = safe_registry.get("selected_trigger") or None
    html = re.sub(
        r'<div class="title" id="triggerDetailTitle">.*?</div>\s*<div class="meta">.*?</div>',
        _trigger_detail_title_html(detail),
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'<div class="explain-text">.*?</div>\s*<div class="formula-block">.*?</div>',
        _trigger_detail_logic_html(detail),
        html,
        count=1,
        flags=re.S,
    )
    html = _replace_nth_tbody_after(
        html,
        '<section class="page" id="trigger-detail">',
        1,
        _trigger_parameter_rows_html(detail),
    )
    html = _replace_nth_tbody_after(
        html,
        '<section class="page" id="trigger-detail">',
        2,
        _trigger_used_in_rows_html(detail),
    )
    html = _replace_nth_tbody_after(
        html,
        '<section class="page" id="trigger-detail">',
        3,
        _trigger_history_rows_html(detail),
    )
    html = _remove_legacy_open_trigger_detail(html)
    return html


def _sets_rows_html(registry: dict[str, Any]) -> str:
    errors = registry.get("integrity_errors") or ()
    if errors:
        return f'<tr><td colspan="4" class="placeholder">Trigger Set registry integrity issue: {_h("; ".join(errors))}</td></tr>'
    rows = registry.get("sets") or ()
    if not rows:
        return '<tr><td colspan="4" class="placeholder">No Trigger Sets registered yet.</td></tr>'
    body = []
    for row in rows:
        triggers = row.get("trigger_versions") or ()
        if triggers:
            trigger_html = "".join(
                f"<button class=\"link\" onclick='openTriggerDetail({_js_arg(trigger.get('trigger_id'))},{_js_arg(trigger.get('version'))})'>{_h(trigger.get('display_name'))}</button>"
                for trigger in triggers
            )
            trigger_cell = f'<div class="trigger-list">{trigger_html}</div>'
        else:
            trigger_cell = '<span class="meta">No Trigger Versions recorded</span>'
        body.append(
            f'<tr data-set-id="{_h(row.get("set_id"))}" data-set-version="{_h(row.get("version"))}">'
            f'<td class="coin">{_h(row.get("display_name") or row.get("set_id"))}</td>'
            f'<td>{_h(row.get("version"))}</td>'
            f'<td>{_product_status_badge(row.get("status"))}</td>'
            f"<td>{trigger_cell}</td></tr>"
        )
    return "".join(body)


def _trigger_catalog_rows_html(registry: dict[str, Any]) -> str:
    rows = registry.get("triggers") or ()
    if not rows:
        return '<tr><td colspan="3" class="placeholder">No Trigger Versions registered yet.</td></tr>'
    return "".join(
        f'<tr data-trigger-id="{_h(row.get("trigger_id"))}" data-trigger-version="{_h(row.get("version"))}">'
        f"<td><button class=\"link\" onclick='openTriggerDetail({_js_arg(row.get('trigger_id'))},{_js_arg(row.get('version'))})'>{_h(row.get('display_name'))}</button></td>"
        f"<td>{_h(row.get('version'))}</td>"
        f"<td>{_h(row.get('what_it_checks') or 'unavailable')}</td></tr>"
        for row in rows
    )


def _trigger_detail_title_html(detail: dict[str, Any] | None) -> str:
    if not detail:
        return '<div class="title" id="triggerDetailTitle">Trigger unavailable</div>\n        <div class="meta">Version —</div>'
    return (
        f'<div class="title" id="triggerDetailTitle">{_h(detail.get("display_name") or detail.get("trigger_id"))} · {_h(detail.get("version"))}</div>\n'
        f'        <div class="meta">Version {_h(detail.get("version"))} · {_h(detail.get("trigger_id"))}</div>'
    )


def _trigger_detail_logic_html(detail: dict[str, Any] | None) -> str:
    if not detail:
        return '<div class="explain-text">Trigger registry unavailable.</div>\n      <div class="formula-block">unavailable</div>'
    return f'<div class="explain-text">{_h(detail.get("how_it_works") or "unavailable")}</div>\n      <div class="formula-block">{_h(detail.get("formula_text") or "unavailable")}</div>'


def _trigger_parameter_rows_html(detail: dict[str, Any] | None) -> str:
    rows = (() if not detail else detail.get("parameters")) or ()
    if not rows:
        return '<tr><td colspan="3" class="placeholder">No parameters registered for this Trigger Version.</td></tr>'
    return "".join(
        f"<tr><td>{_h(row.get('name'))}</td><td>{_h(row.get('value'))}</td><td>{_h(row.get('meaning'))}</td></tr>"
        for row in rows
    )


def _trigger_used_in_rows_html(detail: dict[str, Any] | None) -> str:
    rows = (() if not detail else detail.get("used_in")) or ()
    if not rows:
        return '<tr><td colspan="3" class="placeholder">This Trigger Version is not used by any Set Version.</td></tr>'
    return "".join(
        f"<tr><td>{_h(row.get('set_name') or row.get('set_id'))}</td><td>{_h(row.get('set_version'))}</td><td>{_product_status_badge(row.get('set_status'))}</td></tr>"
        for row in rows
    )


def _trigger_history_rows_html(detail: dict[str, Any] | None) -> str:
    rows = (() if not detail else detail.get("version_history")) or ()
    if not rows:
        return '<tr><td colspan="3" class="placeholder">No version history recorded.</td></tr>'
    return "".join(
        f"<tr><td>{_h(row.get('version'))}</td><td>{_h(row.get('created_at'))}</td><td>{_h(row.get('change_summary'))}</td></tr>"
        for row in rows
    )


def _product_status_badge(status: Any) -> str:
    normalized = str(status or "UNKNOWN").upper()
    css = "gray"
    if normalized == "ACTIVE":
        css = "green"
    elif normalized == "TESTING":
        css = "blue"
    elif normalized == "DRAFT":
        css = "amber"
    return f'<span class="badge {css}">{_h(normalized)}</span>'


def _js_arg(value: Any) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def _h(value: Any) -> str:
    return escape("" if value is None else str(value), quote=True)


def _replace_first_tbody(html: str, section_start: str, section_end: str, replacement: str) -> str:
    start = html.find(section_start)
    end = html.find(section_end, start + len(section_start)) if start >= 0 else -1
    if start < 0 or end < 0:
        return html
    tbody_start = html.find("<tbody", start, end)
    if tbody_start < 0:
        return html
    open_end = html.find(">", tbody_start, end)
    close_start = html.find("</tbody>", open_end, end)
    if open_end < 0 or close_start < 0:
        return html
    return html[: open_end + 1] + "\n" + replacement + "\n" + html[close_start:]


def _replace_nth_tbody_after(html: str, marker: str, nth: int, replacement: str) -> str:
    start = html.find(marker)
    if start < 0:
        return html
    pos = start
    for _ in range(nth):
        pos = html.find("<tbody", pos + 1)
        if pos < 0:
            return html
    open_end = html.find(">", pos)
    close_start = html.find("</tbody>", open_end)
    if open_end < 0 or close_start < 0:
        return html
    return html[: open_end + 1] + "\n" + replacement + "\n" + html[close_start:]


def _remove_legacy_open_trigger_detail(html: str) -> str:
    marker = "function openTriggerDetail(code){"
    while marker in html:
        start = html.find(marker)
        next_function = html.find("\n\nfunction ", start + len(marker))
        if next_function < 0:
            return html
        html = html[:start] + html[next_function + 2 :]
    return html


def _strip_rules_fixtures(html: str, rules: dict[str, Any]) -> str:
    html = _replace_between(
        html,
        '<section class="page" id="rules">',
        '<section class="page" id="rules-version">',
        _rules_current_section_html(rules),
    )
    html = _replace_between(
        html,
        '<section class="page" id="rules-version">',
        '<section class="page" id="research">',
        _rules_version_section_html(rules),
    )
    return _remove_legacy_rules_script(html)


def _rules_current_section_html(rules: dict[str, Any]) -> str:
    current = rules.get("current")
    if not current:
        return """<section class="page" id="rules">
  <div class="rules-topbar"><div class="current-rules-heading">Current Rules Configuration</div></div>
  <div class="rules-grid">
    <div class="panel"><div class="panelhead"><div class="title">Position Rules</div></div><div class="rule-form">
      <div class="rule-row"><div><div class="rule-name">Position size</div><div class="rule-desc">% of available capital allocated to one new position</div></div><div class="rule-control suffix-control"><input type="number" disabled><span>%</span></div></div>
      <div class="rule-row"><div><div class="rule-name">Take Profit mode</div><div class="rule-desc">How the target is determined</div></div><div class="rule-control"><select disabled><option>Fixed</option><option>Dynamic</option></select></div></div>
      <div class="rule-row"><div><div class="rule-name">Fixed Take Profit</div><div class="rule-desc">Exact target move from entry</div></div><div class="rule-control suffix-control"><input type="number" disabled><span>%</span></div></div>
      <div class="rule-row"><div><div class="rule-name">Minimum Take Profit</div><div class="rule-desc">Dynamic target cannot be lower than this level</div></div><div class="rule-control suffix-control"><input type="number" disabled><span>%</span></div></div>
      <div class="rule-row"><div><div class="rule-name">Stop Loss</div><div class="rule-desc">Maximum planned move against the position</div></div><div class="rule-control suffix-control"><input type="number" disabled><span>%</span></div></div>
      <div class="rule-row"><div><div class="rule-name">Minimum Risk / Reward</div><div class="rule-desc">Minimum expected reward relative to planned risk</div></div><div class="rule-control rr-control"><input type="number" disabled><span>: 1</span></div></div>
      <div class="rule-row"><div><div class="rule-name">Minimum Net Edge <label class="mini-toggle"><input type="checkbox" disabled><span></span></label></div><div class="rule-desc">Minimum expected result after trading costs</div></div><div class="rule-control suffix-control"><input type="number" disabled><span>%</span></div></div>
      <div class="rule-row"><div><div class="rule-name">Leverage</div><div class="rule-desc">Default leverage for new positions</div></div><div class="rule-control"><select disabled><option>1x</option></select></div></div>
    </div></div>
    <div class="panel"><div class="panelhead"><div class="title">Portfolio Rules</div></div><div class="rule-form">
      <div class="rule-row"><div><div class="rule-name">Max capital in positions</div><div class="rule-desc">Maximum share of total capital allowed in open positions</div></div><div class="rule-control suffix-control"><input type="number" disabled><span>%</span></div></div>
      <div class="rule-row"><div><div class="rule-name">Max open positions <label class="mini-toggle"><input type="checkbox" disabled><span></span></label></div><div class="rule-desc">Maximum number of simultaneous positions</div></div><div class="rule-control"><input type="number" disabled></div></div>
      <div class="rule-row"><div><div class="rule-name">Max positions per coin <label class="mini-toggle"><input type="checkbox" disabled><span></span></label></div></div><div class="rule-control"><input type="number" disabled></div></div>
      <div class="rule-row"><div><div class="rule-name">Direction</div><div class="rule-desc">Allowed trade directions</div></div><div class="rule-control"><select disabled><option>LONG + SHORT</option></select></div></div>
      <div class="rule-row"><div><div class="rule-name">Daily loss limit <label class="mini-toggle"><input type="checkbox" disabled><span></span></label></div></div><div class="rule-control suffix-control"><input type="number" disabled><span>%</span></div></div>
    </div></div>
    <div class="panel"><div class="panelhead"><div class="title">Coins</div><div class="rule-actions"><button class="btn" disabled>Edit</button></div></div><div class="coins-list" id="coinsList"><span class="meta">Current rules unavailable.</span></div><div class="coins-editor"><div class="coins-toolbar"><input class="search" placeholder="Search exchange symbols" disabled><button class="btn" disabled>Refresh from exchange</button></div><div class="coins-footer"><span class="meta">Optional % = max share of total capital for that coin. Blank = no coin-specific limit.</span><button class="btn" disabled>Apply</button></div></div></div>
    <div class="rules-bottom-actions"><div class="rules-save-state" id="rulesSaveState">Current rules unavailable</div><button class="btn primary-rule" disabled>Save as New Version</button></div>
    <div class="panel rules-span version-history-table"><div class="panelhead"><div class="title">Version history</div></div><div class="tablewrap"><table><thead><tr><th>Version</th><th>Change</th><th>Used in</th></tr></thead><tbody><tr><td colspan="3" class="placeholder">Backend bootstrap must create the factual initial version.</td></tr></tbody></table></div></div>
  </div>
</section>

"""
    pos = current["position_rules"]
    port = current["portfolio_rules"]
    return f"""<section class="page" id="rules">
  <div class="rules-topbar">
    <div class="current-rules-heading">Current Rules Configuration <span class="meta" id="rulesCurrentVersionLabel">Rules · {_h(current["display_version"])}</span></div>
  </div>
  <div class="rules-grid">
    <div class="panel"><div class="panelhead"><div class="title">Position Rules</div></div><div class="rule-form">
      {_rule_number_row("Position size", "% of available capital allocated to one new position", "rulesPosSize", pos["position_size_pct"], "%", "0.1", "0.1", "100")}
      <div class="rule-row"><div><div class="rule-name">Take Profit mode</div><div class="rule-desc">How the target is determined</div></div><div class="rule-control"><select id="rulesTpMode" onchange="syncTpMode()">{_option("Fixed", pos["take_profit_mode"] == "FIXED")}{_option("Dynamic", pos["take_profit_mode"] == "DYNAMIC")}</select></div></div>
      <div class="rule-row" id="fixedTpRow"><div><div class="rule-name">Fixed Take Profit</div><div class="rule-desc">Exact target move from entry</div></div><div class="rule-control suffix-control"><input id="rulesFixedTp" type="number" value="{_h(pos["fixed_take_profit_pct"] or "")}" step="0.1" min="0.1"><span>%</span></div></div>
      <div class="rule-row" id="minTpRow"><div><div class="rule-name">Minimum Take Profit</div><div class="rule-desc">Dynamic target cannot be lower than this level</div></div><div class="rule-control suffix-control"><input id="rulesMinTp" type="number" value="{_h(pos["minimum_take_profit_pct"] or "")}" step="0.1" min="0.1"><span>%</span></div></div>
      {_rule_number_row("Stop Loss", "Maximum planned move against the position", "rulesSl", pos["stop_loss_pct"], "%", "0.1", "0.1", "")}
      {_rule_number_row("Minimum Risk / Reward", "Minimum expected reward relative to planned risk", "rulesRR", pos["minimum_risk_reward"], ": 1", "0.1", "0.1", "", "rr-control")}
      {_toggle_number_row("Minimum Net Edge", "Minimum expected result after trading costs", "rulesEdgeOn", "rulesEdge", pos["minimum_net_edge_enabled"], pos["minimum_net_edge_pct"], "%", "0.1", "0")}
      <div class="rule-row"><div><div class="rule-name">Leverage</div><div class="rule-desc">Default leverage for new positions</div></div><div class="rule-control"><select id="rulesLev">{_leverage_options(pos["leverage"])}</select></div></div>
    </div></div>
    <div class="panel"><div class="panelhead"><div class="title">Portfolio Rules</div></div><div class="rule-form">
      {_rule_number_row("Max capital in positions", "Maximum share of total capital allowed in open positions", "rulesCap", port["max_capital_in_positions_pct"], "%", "1", "1", "100")}
      {_toggle_number_row("Max open positions", "Maximum number of simultaneous positions", "rulesMaxOpenOn", "rulesMaxOpen", port["max_open_positions_enabled"], port["max_open_positions"], "", "1", "1")}
      {_toggle_number_row("Max positions per coin", "", "rulesMaxCoinOn", "rulesMaxCoin", port["max_positions_per_coin_enabled"], port["max_positions_per_coin"], "", "1", "1")}
      <div class="rule-row"><div><div class="rule-name">Direction</div><div class="rule-desc">Allowed trade directions</div></div><div class="rule-control"><select id="rulesDirection">{_option("LONG + SHORT", port["direction_mode"] == "LONG_SHORT")}{_option("LONG only", port["direction_mode"] == "LONG_ONLY")}{_option("SHORT only", port["direction_mode"] == "SHORT_ONLY")}</select></div></div>
      {_toggle_number_row("Daily loss limit", "", "rulesDailyLossOn", "rulesDailyLoss", port["daily_loss_limit_enabled"], port["daily_loss_limit_pct"], "%", "0.1", "0")}
    </div></div>
    <div class="panel"><div class="panelhead"><div class="title">Coins</div><div class="rule-actions"><button class="btn" onclick="toggleCoinsEditor()">Edit</button></div></div>
      <div class="coins-list" id="coinsList">{_rules_coin_chips(current["coins"])}</div>
      <div class="coins-editor" id="coinsEditor" style="display:none"><div class="coins-toolbar"><input class="search" id="coinSearch" placeholder="Search exchange symbols" oninput="filterCoinOptions()"><button class="btn" onclick="refreshRulesCatalog()">Refresh from exchange</button></div><div class="coin-options" id="coinOptions"></div><div class="coins-footer"><span class="meta" id="catalogState">Optional % = max share of total capital for that coin. Blank = no coin-specific limit.</span><button class="btn" onclick="applyCoins()">Apply</button></div></div>
    </div>
    <div class="panel rules-span" id="rulesErrorPanel" style="display:none"><div class="panelhead"><div><div class="title">Validation error</div><div class="meta" id="rulesErrorText"></div></div></div></div>
    <div class="rules-bottom-actions"><div class="rules-save-state" id="rulesSaveState">No unsaved changes</div><button class="btn primary-rule" id="rulesSaveButton" onclick="saveRules()" disabled>Save as New Version</button></div>
    <div class="panel rules-span"><div class="panelhead"><div><div class="title">Runtime capability</div><div class="meta">Dynamic TP: unsupported/fail closed · Daily loss enforcement: unsupported/fail closed · Direction filters do not create SHORT alpha</div></div></div></div>
    <div class="panel rules-span"><div class="panelhead"><div><div class="title">Immutable identity</div><div class="meta mono" id="rulesCurrentIdentity">rules_version_id: {_h(current["rules_version_id"])} · config_hash: {_h(current["config_hash"])}</div></div></div></div>
    <div class="panel rules-span version-history-table"><div class="tablewrap"><table><thead><tr><th>Version</th><th>Change</th><th>Used in</th></tr></thead><tbody id="rulesHistoryBody">{_rules_history_rows(rules.get("history") or ())}</tbody></table></div></div>
  </div>
</section>

"""


def _rules_version_section_html(rules: dict[str, Any]) -> str:
    current = rules.get("current")
    title = "Rules · " + str(current.get("display_version")) if current else "Rules unavailable"
    return f"""<section class="page" id="rules-version">
  <div class="rules-version-header"><div class="rules-version-header-inner"><div class="current-rules-heading" id="rulesVersionTitle">{_h(title)}</div><div class="pagesub" id="rulesVersionIdentity">Saved rules configuration · read only</div><div class="version-context"><span id="rulesVersionChange">Change: {_h((current or {}).get("change_summary") or "-")}</span><span id="rulesVersionUsed">Used in: {_h(_rules_used_in_label((current or {}).get("used_in") or ()))}</span></div></div></div>
  <div class="rules-grid readonly-control" id="rulesVersionDetail"></div>
</section>

"""


def _rules_wiring_script(rules: dict[str, Any] | None, token: str) -> str:
    if rules is None:
        return ""
    payload = json.dumps(_safe_payload(rules), ensure_ascii=False).replace("</", "<\\/")
    return f"""
<script id="triggertrade-rules-read-model">
(function(){{
  const state = {payload};
  const token = {json.dumps(token)};
  const html = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
  let draft = JSON.parse(JSON.stringify(state.current || null));
  let coinDraft = new Map((draft ? draft.coins : []).map(c => [c.symbol, Object.assign({{}}, c)]));
  let saving = false;
  let cleanSnapshot = "";
  const modeValue = () => rulesTpMode.value === "Fixed" ? "FIXED" : "DYNAMIC";
  const directionValue = () => rulesDirection.value === "LONG only" ? "LONG_ONLY" : rulesDirection.value === "SHORT only" ? "SHORT_ONLY" : "LONG_SHORT";
  function val(id){{ const node=document.getElementById(id); return node && node.value !== "" ? node.value : null; }}
  function checked(id){{ const node=document.getElementById(id); return !!(node && node.checked); }}
  function syncVisibleCoins(){{ document.querySelectorAll("#coinOptions label").forEach(label => {{ const symbol=label.dataset.symbol; if(!symbol)return; coinDraft.set(symbol, {{symbol, enabled: label.querySelector("input[type=checkbox]").checked, max_allocation_pct: label.querySelector("input[type=number]").value || null}}); }}); }}
  function currentPayload(){{
    syncVisibleCoins();
    return {{
      expected_rules_version_id: state.current && state.current.rules_version_id,
      expected_display_version: state.current && state.current.display_version,
      token,
      position_rules: {{
        position_size_pct: val("rulesPosSize"), take_profit_mode: modeValue(), fixed_take_profit_pct: val("rulesFixedTp"), minimum_take_profit_pct: val("rulesMinTp"),
        stop_loss_pct: val("rulesSl"), minimum_risk_reward: val("rulesRR"), minimum_net_edge_enabled: checked("rulesEdgeOn"), minimum_net_edge_pct: val("rulesEdge"),
        leverage: String(val("rulesLev") || "").replace("x","")
      }},
      portfolio_rules: {{
        max_capital_in_positions_pct: val("rulesCap"), max_open_positions_enabled: checked("rulesMaxOpenOn"), max_open_positions: val("rulesMaxOpen"),
        max_positions_per_coin_enabled: checked("rulesMaxCoinOn"), max_positions_per_coin: val("rulesMaxCoin"),
        direction_mode: directionValue(), daily_loss_limit_enabled: checked("rulesDailyLossOn"), daily_loss_limit_pct: val("rulesDailyLoss")
      }},
      coins: [...coinDraft.values()]
    }};
  }}
  function payloadSignature(payload){{ const copy=JSON.parse(JSON.stringify(payload)); delete copy.token; return JSON.stringify(copy); }}
  function setSave(text, dirty){{ const s=document.getElementById("rulesSaveState"), b=document.getElementById("rulesSaveButton"); if(s)s.textContent=text; if(b)b.disabled=saving || !dirty; }}
  function clearRulesError(){{ const p=document.getElementById("rulesErrorPanel"); if(p)p.style.display="none"; document.querySelectorAll("#rules .rule-row,#rules .coins-editor").forEach(x=>x.style.outline=""); }}
  function showRulesError(message){{ clearRulesError(); const panel=document.getElementById("rulesErrorPanel"), text=document.getElementById("rulesErrorText"); if(panel)panel.style.display="block"; if(text)text.textContent=message; const lower=String(message||"").toLowerCase(); let target=null; if(lower.includes("coin")||lower.includes("catalog")||lower.includes("symbol")) target=document.querySelector("#coinsEditor")||document.querySelector("#coinsList"); else if(lower.includes("take-profit")||lower.includes("profit")) target=document.getElementById("rulesTpMode")?.closest(".rule-row"); else if(lower.includes("position_size")) target=document.getElementById("rulesPosSize")?.closest(".rule-row"); else if(lower.includes("stop_loss")) target=document.getElementById("rulesSl")?.closest(".rule-row"); else if(lower.includes("leverage")) target=document.getElementById("rulesLev")?.closest(".rule-row"); else if(lower.includes("max_open")) target=document.getElementById("rulesMaxOpen")?.closest(".rule-row"); else if(lower.includes("daily")) target=document.getElementById("rulesDailyLoss")?.closest(".rule-row"); if(target)target.style.outline="2px solid #f4e4ad"; }}
  function refreshDirtyState(){{ const dirty=payloadSignature(currentPayload())!==cleanSnapshot; setSave(dirty ? "Unsaved changes" : "No unsaved changes", dirty); }}
  function markDirty(){{ clearRulesError(); refreshDirtyState(); }}
  function coinChip(c){{ return `<span class="coin-chip">${{html(c.symbol)}}${{c.max_allocation_pct ? ` <small>${{html(c.max_allocation_pct)}}%</small>` : ""}}</span>`; }}
  function renderCurrentIdentity(){{ const label=document.getElementById("rulesCurrentVersionLabel"), ident=document.getElementById("rulesCurrentIdentity"); if(label)label.textContent="Rules · "+(state.current?.display_version || "-"); if(ident)ident.textContent=`rules_version_id: ${{state.current?.rules_version_id || "-"}} · config_hash: ${{state.current?.config_hash || "-"}}`; }}
  function renderCoinsList(){{ const node=document.getElementById("coinsList"); if(node) node.innerHTML = (currentPayload().coins.filter(c=>c.enabled).map(coinChip).join("") || '<span class="meta">No enabled coins</span>'); }}
  function renderCoinOptions(list){{ syncVisibleCoins(); const rows = (list && list.length ? list : (state.coins || [])); const node=document.getElementById("coinOptions"); if(!node)return; node.innerHTML = rows.map(c => {{ const cur=coinDraft.get(c.symbol)||{{symbol:c.symbol,enabled:false,max_allocation_pct:null}}; return `<label data-symbol="${{html(c.symbol)}}"><span><input type="checkbox" ${{cur.enabled?'checked':''}}> ${{html(c.symbol)}}</span><span class="coin-limit"><input type="number" value="${{html(cur.max_allocation_pct||"")}}" placeholder="-" min="1" max="100">%</span></label>`; }}).join("") || '<div class="placeholder">No tradeable catalog symbols available.</div>'; node.querySelectorAll("input").forEach(x => x.addEventListener("input", markDirty)); }}
  window.syncTpMode = function(){{ const fixed=document.getElementById("fixedTpRow"), min=document.getElementById("minTpRow"); if(!fixed||!min)return; if(modeValue()==="FIXED"){{fixed.style.display="grid";min.style.display="none";}}else{{fixed.style.display="none";min.style.display="grid";}} }};
  window.toggleCoinsEditor = function(){{ const e=document.getElementById("coinsEditor"); if(e)e.style.display=e.style.display==="none"?"block":"none"; renderCoinOptions(); }};
  window.filterCoinOptions = async function(){{ const q=document.getElementById("coinSearch").value; const res=await fetch(`/api/instruments/search?q=${{encodeURIComponent(q)}}`); const data=await res.json(); renderCoinOptions(data.coins || []); }};
  window.refreshRulesCatalog = async function(){{ setSave("Refreshing catalog...", payloadSignature(currentPayload())!==cleanSnapshot); const res=await fetch("/api/instruments/refresh", {{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{token}})}}); const data=await res.json(); const c=document.getElementById("catalogState"); if(c)c.textContent=res.ok?`Catalog refreshed: ${{data.tradeable_count}} tradeable symbols`:`Catalog refresh failed: ${{data.error || "previous cache preserved"}}`; await window.filterCoinOptions(); refreshDirtyState(); }};
  window.applyCoins = function(){{ renderCoinsList(); markDirty(); }};
  window.saveRules = async function(){{ if(saving)return; saving=true; clearRulesError(); setSave("Saving...", true); const res=await fetch("/api/rules/versions", {{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(currentPayload())}}); const data=await res.json(); saving=false; if(!res.ok){{ const msg=res.status===409?"Conflict - current version changed; refresh current rules before saving":(data.error || "Validation error"); showRulesError(msg); setSave(msg, true); return; }} state.current=data.rules; state.history=data.history; draft=JSON.parse(JSON.stringify(state.current)); coinDraft = new Map((draft ? draft.coins : []).map(c => [c.symbol, Object.assign({{}}, c)])); renderCurrentIdentity(); renderHistory(); renderCoinOptions(); renderCoinsList(); cleanSnapshot=payloadSignature(currentPayload()); setSave(`Saved as ${{state.current.display_version}}`, false); }};
  function renderHistory(){{ const body=document.getElementById("rulesHistoryBody"); if(!body)return; body.innerHTML=(state.history||[]).map(v=>`<tr><td><button class="link" onclick="openRulesVersion('${{html(v.rules_version_id)}}')">${{html(v.display_version)}}</button></td><td>${{html(v.change_summary)}}</td><td>${{html(usedLabel(v.used_in))}}</td></tr>`).join(""); }}
  function usedLabel(rows){{ return (rows||[]).map(r=>r.usage_type+(r.entity_id?` · ${{r.entity_id}}`:"")).join("; ") || "-"; }}
  window.openRulesVersion = async function(v){{ const res=await fetch(`/api/rules/version/${{encodeURIComponent(v)}}`); const d=await res.json(); if(!res.ok)return; rulesVersionTitle.textContent="Rules · "+d.display_version; const ident=document.getElementById("rulesVersionIdentity"); if(ident)ident.textContent=`Saved rules configuration · read only · ${{d.rules_version_id}} · ${{d.config_hash}}`; rulesVersionChange.textContent="Change: "+d.change_summary; rulesVersionUsed.textContent="Used in: "+usedLabel(d.used_in); const node=document.getElementById("rulesVersionDetail"); if(node) node.innerHTML=`<div class="panel"><div class="panelhead"><div class="title">Position Rules</div></div><div class="detail-note">${{html(JSON.stringify(d.position_rules))}}</div></div><div class="panel"><div class="panelhead"><div class="title">Portfolio Rules</div></div><div class="detail-note">${{html(JSON.stringify(d.portfolio_rules))}}</div></div><div class="panel"><div class="panelhead"><div class="title">Coins</div></div><div class="coins-list">${{(d.coins||[]).filter(c=>c.enabled).map(coinChip).join("")}}</div></div>`; showPage("rules-version"); }};
  if(draft){{ document.querySelectorAll("#rules input,#rules select").forEach(x=>x.addEventListener("input", markDirty)); renderCoinOptions(); renderCoinsList(); renderHistory(); syncTpMode(); cleanSnapshot=payloadSignature(currentPayload()); setSave("No unsaved changes", false); }}
}})();
</script>
"""


def _rule_number_row(name: str, desc: str, field_id: str, value: Any, suffix: str, step: str, min_value: str, max_value: str, cls: str = "suffix-control") -> str:
    max_attr = "" if not max_value else f' max="{_h(max_value)}"'
    return f'<div class="rule-row"><div><div class="rule-name">{_h(name)}</div><div class="rule-desc">{_h(desc)}</div></div><div class="rule-control {cls}"><input id="{_h(field_id)}" type="number" value="{_h(value)}" step="{_h(step)}" min="{_h(min_value)}"{max_attr}><span>{_h(suffix)}</span></div></div>'


def _toggle_number_row(name: str, desc: str, toggle_id: str, field_id: str, enabled: Any, value: Any, suffix: str, step: str, min_value: str) -> str:
    checked = " checked" if enabled else ""
    control = "suffix-control" if suffix else ""
    return f'<div class="rule-row"><div><div class="rule-name">{_h(name)} <label class="mini-toggle"><input id="{_h(toggle_id)}" type="checkbox"{checked}><span></span></label></div><div class="rule-desc">{_h(desc)}</div></div><div class="rule-control {control}"><input id="{_h(field_id)}" type="number" value="{_h(value if value is not None else "")}" step="{_h(step)}" min="{_h(min_value)}"><span>{_h(suffix)}</span></div></div>'


def _option(label: str, selected: bool) -> str:
    return f'<option{" selected" if selected else ""}>{_h(label)}</option>'


def _leverage_options(current: Any) -> str:
    values = ["1", "2", "3", "5"]
    current_value = str(current)
    if current_value not in values:
        values.append(current_value)
    return "".join(_option(f"{value}x", current_value == value) for value in values)


def _rules_coin_chips(coins: Any) -> str:
    enabled = [coin for coin in coins if coin.get("enabled")]
    return "".join(f'<span class="coin-chip">{_h(coin.get("symbol"))}{f" <small>{_h(coin.get("max_allocation_pct"))}%</small>" if coin.get("max_allocation_pct") else ""}</span>' for coin in enabled) or '<span class="meta">No enabled coins</span>'


def _rules_history_rows(history: Any) -> str:
    return "".join(f'<tr><td><button class="link" onclick="openRulesVersion({_js_arg(row.get("rules_version_id"))})">{_h(row.get("display_version"))}</button></td><td>{_h(row.get("change_summary"))}</td><td>{_h(_rules_used_in_label(row.get("used_in") or ()))}</td></tr>' for row in history)


def _rules_used_in_label(used_in: Any) -> str:
    labels = [str(row.get("usage_type")) + (f' · {row.get("entity_id")}' if row.get("entity_id") else "") for row in used_in]
    return "; ".join(labels) if labels else "-"


def _messages_section_html(messages: dict[str, Any] | None) -> str:
    payload = messages or {"available": False, "messages": (), "unread_count": None}
    rows = payload.get("messages") or ()
    if not payload.get("available", False):
        body = '<tr><td colspan="4" class="placeholder">Messages unavailable.</td></tr>'
    elif not rows:
        body = '<tr><td colspan="4" class="placeholder">No messages.</td></tr>'
    else:
        body = "".join(
            "<tr"
            + ("" if row.get("is_read") else ' class="unread-message"')
            + f' data-message-id="{_h(row.get("message_id"))}">'
            + f"<td>{_h(_display_time(row.get('created_at')))}</td>"
            + f"<td><div class=\"coin\">{_h(row.get('title') or row.get('body'))}</div><div class=\"meta\">{_h(row.get('body'))}</div></td>"
            + f"<td><span class=\"badge {_message_badge_class(row.get('severity'))}\">{_h(row.get('severity'))}</span></td>"
            + f"<td>{_h('Read' if row.get('is_read') else 'Unread')}</td></tr>"
            for row in rows
        )
    return (
        '<section class="page" id="messages">\n'
        '  <div class="panel">\n'
        '    <div class="panelhead"><div><div class="title">Messages</div>'
        '<div class="meta">User-facing operational messages from the backend.</div></div>'
        '<div class="meta" id="messagesState">Backend messages</div></div>\n'
        '    <div class="tablewrap">\n'
        '      <table>\n'
        '        <thead><tr><th>Time</th><th>Message</th><th>Type</th><th>State</th></tr></thead>\n'
        f'        <tbody id="messagesBody">{body}</tbody>\n'
        "      </table>\n"
        "    </div>\n"
        "  </div>\n"
        "</section>\n"
    )


def _messages_wiring_script(messages: dict[str, Any] | None, token: str) -> str:
    payload = json.dumps(_safe_payload(messages or {"available": False, "messages": (), "unread_count": None}), ensure_ascii=False).replace("</", "<\\/")
    token_json = json.dumps(token)
    return f"""
<script id="triggertrade-messages-history-read-model">
(function(){{
  const initial = {payload};
  const token = {token_json};
  let messagesState = initial;
  const badge = document.getElementById("messageUnreadBadge");
  const body = document.getElementById("messagesBody");
  const state = document.getElementById("messagesState");
  function html(v){{ return String(v ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}}[ch])); }}
  function badgeClass(severity){{ const s=String(severity||"").toUpperCase(); if(s==="ERROR")return"red"; if(s==="WARNING"||s==="ATTENTION")return"amber"; return"blue"; }}
  function renderBadge(count, available=true){{
    if(!badge)return;
    if(!available){{ badge.textContent="!"; badge.style.display="inline-block"; return; }}
    const value=Number(count||0);
    if(value>0){{ badge.textContent=String(value); badge.style.display="inline-block"; }}
    else {{ badge.textContent=""; badge.style.display="none"; }}
  }}
  function renderMessages(data){{
    messagesState=data;
    renderBadge(data.unread_count, data.available !== false);
    if(state)state.textContent=data.available===false ? "Unavailable" : `${{(data.messages||[]).length}} shown`;
    if(!body)return;
    if(data.available===false){{ body.innerHTML='<tr><td colspan="4" class="placeholder">Messages unavailable.</td></tr>'; return; }}
    const rows=data.messages||[];
    if(!rows.length){{ body.innerHTML='<tr><td colspan="4" class="placeholder">No messages.</td></tr>'; return; }}
    body.innerHTML=rows.map(m=>`<tr data-message-id="${{html(m.message_id)}}" class="${{m.is_read ? "" : "unread-message"}}"><td>${{html(m.time || m.created_at || "-")}}</td><td><div class="coin">${{html(m.title || m.body)}}</div><div class="meta">${{html(m.body)}}</div></td><td><span class="badge ${{badgeClass(m.severity)}}">${{html(m.severity || m.type)}}</span></td><td>${{m.is_read ? "Read" : "Unread"}}</td></tr>`).join("");
  }}
  async function refreshUnread(){{
    const res=await fetch("/api/messages/unread-count");
    const data=await res.json();
    renderBadge(data.unread_count, res.ok && data.available !== false);
  }}
  async function loadMessages(){{
    const res=await fetch("/api/messages");
    const data=await res.json();
    if(!res.ok){{ renderMessages({{available:false,messages:[],unread_count:null,error:data.error}}); return; }}
    renderMessages(data);
    const unread=(data.messages||[]).filter(m=>!m.is_read).map(m=>m.message_id);
    if(unread.length){{
      const mark=await fetch("/api/messages/mark-read", {{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{token,message_ids:unread}})}});
      if(mark.ok){{ const result=await mark.json(); renderBadge(result.unread_count, true); }}
    }}
  }}
  const baseShowPage=window.showPage;
  function feedback(text){{
    let node=document.getElementById("systemHistoryCopyState");
    if(!node){{ node=document.createElement("span"); node.id="systemHistoryCopyState"; node.className="meta"; document.querySelector(".actions")?.appendChild(node); }}
    node.textContent=text;
    setTimeout(()=>{{ if(node.textContent===text)node.textContent=""; }}, 2600);
  }}
  window.openMessages = async function(){{
    if(typeof baseShowPage === "function") baseShowPage("messages");
    try{{ await loadMessages(); }}catch(e){{ renderMessages({{available:false,messages:[],unread_count:null,error:"unavailable"}}); }}
  }};
  window.copySystemHistory = async function(){{
    try{{
      const res=await fetch("/api/system-history/export", {{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{token}})}});
      const data=await res.json();
      if(!res.ok || !data.text){{ feedback("History unavailable"); return; }}
      await navigator.clipboard.writeText(data.text);
      feedback("Copied");
    }}catch(e){{ feedback("Copy failed"); }}
  }};
  if(baseShowPage){{
    window.showPage=function(id){{ if(id==="messages"){{ window.openMessages(); return; }} baseShowPage(id); }};
  }}
  renderMessages(initial);
}})();
</script>
"""


def _strip_messages_fixtures(html: str, messages: dict[str, Any] | None) -> str:
    html = html.replace('<span class="message-count" aria-hidden="true">+2</span>', '<span class="message-count" id="messageUnreadBadge" aria-hidden="true" style="display:none"></span>', 1)
    html = html.replace('title="Copy logs" aria-label="Copy logs"', 'title="Copy system history" aria-label="Copy system history"', 1)
    html = html.replace('onclick="copySystemHistory()">⧉</button>', 'onclick="copySystemHistory()" data-export-contract="TriggerTrade system history export">⧉</button>', 1)
    return _replace_between(html, '<section class="page" id="messages">', '<div class="modalbg" id="newResearchModal">', _messages_section_html(messages) + "\n")


def _message_badge_class(value: Any) -> str:
    severity = str(value or "").upper()
    if severity == "ERROR":
        return "red"
    if severity in {"WARNING", "ATTENTION"}:
        return "amber"
    return "blue"


def _display_time(value: Any) -> str:
    text = str(value or "-")
    return text[11:16] if len(text) >= 16 and "T" in text else text


def _replace_between(html: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = html.find(start_marker)
    end = html.find(end_marker, start + len(start_marker)) if start >= 0 else -1
    if start < 0 or end < 0:
        return html
    return html[:start] + replacement + html[end:]


def _remove_legacy_rules_script(html: str) -> str:
    pattern = r"\nconst rulesVersions = \{.*?function openRulesVersion\(v\)\{.*?\n\}\n"
    return re.sub(pattern, "\n", html, count=1, flags=re.S)


def render_product_dashboard(
    *,
    initial_page: str = "portfolio",
    operator_state: Any = None,
    operator_control_token: str = "",
    portfolio: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    rules: dict[str, Any] | None = None,
    messages: dict[str, Any] | None = None,
) -> str:
    page = initial_page if initial_page in _ALLOWED_PAGES else "portfolio"
    startup = ["window.showPage && window.showPage(" + json.dumps(page) + ");"]
    if page == "messages":
        startup.append("window.openMessages && window.openMessages();")
    if page == "research-detail":
        startup.append("window.showPage && window.showPage('research'); window.openResearchById && window.openResearchById('R-001');")
    raw_state = getattr(operator_state, "state", "TRADING_ENABLED") if operator_state is not None else "TRADING_ENABLED"
    state = raw_state if raw_state in {"TRADING_ENABLED", "TRADING_PAUSED"} else "TRADING_ENABLED"
    if state == "TRADING_PAUSED":
        startup.append("if(window.botDot){botDot.style.background='#a16207';botDot.style.boxShadow='0 0 0 4px #fff8e6';botDot.title='Bot running · new entries paused';}")
    marker = "</body>"
    html = _PRODUCT_UI_HTML.replace(
        "<main class=\"container\">",
        '<main class="container">\n' + _fixture_boundary_html(portfolio_live=portfolio is not None, registry_live=registry is not None),
        1,
    )
    if registry is not None:
        html = _strip_registry_fixtures(html, registry)
    if rules is not None:
        html = _strip_rules_fixtures(html, rules)
    html = _strip_messages_fixtures(html, messages)
    html = html.replace(
        ".placeholder{padding:50px 20px;text-align:center;color:var(--muted);font-size:11px}",
        ".placeholder{padding:50px 20px;text-align:center;color:var(--muted);font-size:11px}\n"
        ".fixture-boundary{margin:2px 0 10px;border:1px solid #dce7ff;background:#f8fbff;color:#31519b;"
        "border-radius:8px;padding:8px 10px;font-size:10px;font-weight:700}",
        1,
    )
    script = (
        '\n<script id="triggertrade-server-startup">'
        + "".join(startup)
        + "</script>\n"
        + _operator_forms_html(operator_control_token)
        + _server_boundary_script(state, bool(operator_control_token))
        + _portfolio_wiring_script(portfolio)
        + _registry_wiring_script(registry)
        + _rules_wiring_script(rules, operator_control_token)
        + _messages_wiring_script(messages, operator_control_token)
    )
    return html.replace(marker, script + marker)


def render_product_not_found(value: str) -> str:
    return """<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Not Found</title></head><body><main style="font-family:Inter,system-ui,sans-serif;padding:22px"><h1>Not Found</h1><p>{}</p></main></body></html>""".format(escape(value, quote=True))
