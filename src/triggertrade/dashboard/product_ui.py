r"""Server-rendered product UI shell for the approved TriggerTrade dashboard.

The HTML keeps the approved compact dashboard layout while all factual values
come from backend read-model contracts. Trading decisions are never made here.
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

_PRODUCT_UI_HTML = '<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8"/>\n<meta name="viewport" content="width=device-width,initial-scale=1"/>\n<title>TriggerTrade - Dashboard</title>\n<style>\n:root{\n  --bg:#f6f7f9; --panel:#fff; --text:#19191b; --muted:#74747c; --line:#e5e5e8; --line2:#d5d5d9;\n  --green:#16783c; --green-bg:#eef9f2; --red:#b42318; --red-bg:#fff1f0; --blue:#2457d6; --blue-bg:#eef4ff;\n  --amber:#9a6700; --amber-bg:#fff8e6; --page:1460px; --pad:22px;\n}\n*{box-sizing:border-box}\nhtml,body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}\nbutton,input,select{font:inherit}\n.container{max-width:var(--page);margin:0 auto;padding:0 var(--pad)}\n.top{position:sticky;top:0;z-index:30;background:#fff;border-bottom:1px solid var(--line)}\n.topin{height:58px;display:flex;align-items:center;justify-content:space-between}\n.brand{font-size:15px;font-weight:820;letter-spacing:-.01em;display:flex;align-items:center;gap:9px}\n.live-dot{width:7px;height:7px;border-radius:50%;background:#a1a1aa;box-shadow:0 0 0 4px #f4f4f5}\n.actions{display:flex;align-items:center;gap:8px}\n.badge{display:inline-flex;align-items:center;padding:4px 7px;border-radius:999px;border:1px solid transparent;font-size:10px;font-weight:800;white-space:nowrap}\n.badge.live{background:#171719;color:#fff}.badge.green{background:var(--green-bg);color:var(--green);border-color:#d8f0df}\n.badge.red{background:var(--red-bg);color:var(--red);border-color:#ffd4cf}.badge.blue{background:var(--blue-bg);color:var(--blue);border-color:#dce7ff}\n.badge.gray{background:#f4f4f5;color:#53535a;border-color:#e5e5e8}.badge.amber{background:var(--amber-bg);color:var(--amber);border-color:#f4e4ad}\n.btn{border:1px solid var(--line2);background:#fff;border-radius:8px;padding:7px 10px;font-size:11px;font-weight:750;color:#3f3f46;cursor:pointer}\n.btn.red{background:var(--red);color:#fff;border-color:var(--red)}\n.tabsbar{position:sticky;top:58px;z-index:29;background:#fff;border-bottom:1px solid var(--line)}\n.tabs{height:41px;display:flex;align-items:flex-end;gap:23px}\n.tab{border:0;background:transparent;padding:0 0 9px;border-bottom:2px solid transparent;color:var(--muted);font-size:12px;font-weight:760;cursor:pointer}\n.tab.active{color:var(--text);border-bottom-color:var(--text)}\nmain{padding-top:12px;padding-bottom:30px}.page{display:none}.page.active{display:block}\n.pagehead{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:10px}\n.pagetitle{font-size:17px;font-weight:800;letter-spacing:-.02em}.pagesub{font-size:10px;color:var(--muted);margin-top:2px}\n.kpis{display:flex;gap:7px;overflow:auto;margin-bottom:10px;scrollbar-width:none}.kpis::-webkit-scrollbar{display:none}\n.kpi{background:#fff;border:1px solid var(--line);border-radius:9px;padding:10px 11px;flex:1 1 0;min-width:155px}\n.klabel{font-size:9px;color:var(--muted);margin-bottom:4px}.kvalue{font-size:17px;font-weight:800;letter-spacing:-.015em}.ksub{font-size:9px;color:var(--muted);margin-top:4px}\n.pos{color:var(--green)}.neg{color:var(--red)}\n.panel{background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-bottom:10px}\n.panelhead{padding:11px 13px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:10px}\n.title{font-size:13px;font-weight:760}.meta{font-size:10px;color:var(--muted);margin-top:2px}\n.moneybar{display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr;gap:0}\n.moneyitem{padding:13px;border-right:1px solid var(--line)}.moneyitem:last-child{border-right:0}\n.mlabel{font-size:9px;color:var(--muted);margin-bottom:3px}.mval{font-size:14px;font-weight:760}.mnote{font-size:9px;color:var(--muted);margin-top:3px}\n.attn{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:10px 12px}\n.attn-card{border:1px solid var(--line);border-radius:8px;padding:9px 10px;background:#fafafa}\n.attn-title{font-size:10px;font-weight:760}.attn-text{font-size:10px;color:var(--muted);margin-top:3px;line-height:1.35}\n.filters{display:flex;gap:7px;align-items:center;flex-wrap:wrap}\n.segment{display:inline-flex;border:1px solid var(--line2);border-radius:8px;padding:2px;background:#f7f7f8}\n.segment button{border:0;background:transparent;border-radius:6px;padding:5px 9px;font-size:10px;font-weight:800;color:#76767d;cursor:pointer}\n.segment button.active{background:#fff;color:#222;box-shadow:0 1px 2px rgba(0,0,0,.07)}\n.search,select{border:1px solid var(--line2);background:#fff;border-radius:8px;padding:7px 9px;font-size:11px;color:#3f3f46}\n.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:12px}\nth{padding:8px 10px;background:#fafafa;border-bottom:1px solid var(--line);text-align:left;font-size:9px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);white-space:nowrap}\ntd{padding:10px;border-bottom:1px solid #f0f0f1;white-space:nowrap;vertical-align:middle}tbody tr:last-child td{border-bottom:0}\n.coin{font-weight:750}.link{border:0;background:transparent;padding:0;text-decoration:underline;text-decoration-color:#a1a1aa;text-underline-offset:3px;font-weight:760;cursor:pointer}\n.summaryline{display:flex;gap:18px;align-items:center;flex-wrap:wrap;font-size:10px;color:var(--muted)}\n.summaryline b{font-size:11px;color:var(--text)}\n.placeholder{padding:50px 20px;text-align:center;color:var(--muted);font-size:11px}\n.modalbg{display:none;position:fixed;inset:0;background:rgba(24,24,27,.22);z-index:60}.modalbg.open{display:block}\n.modal{width:min(650px,calc(100% - 28px));margin:80px auto;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}\n.modalbody{padding:15px}.notice{background:var(--amber-bg);border:1px solid #f4e4ad;border-radius:8px;padding:10px;font-size:11px}\n.modalactions{display:flex;justify-content:flex-end;gap:8px;margin-top:14px}\n@media(max-width:850px){.moneybar{grid-template-columns:1fr 1fr}.moneyitem:nth-child(2){border-right:0}.moneyitem:nth-child(-n+2){border-bottom:1px solid var(--line)}.attn{grid-template-columns:1fr}}\n@media(max-width:620px){:root{--pad:12px}.topin{height:auto;min-height:54px;padding-block:8px}.actions .badge.state{display:inline-flex}.tabs{gap:20px}.kpi{flex:0 0 145px;min-width:145px}.pagehead{flex-direction:column}.moneybar{grid-template-columns:1fr 1fr}.panelhead{align-items:flex-start;flex-direction:column}.filters{width:100%}}\n\n.icon-action{\n  border:0;background:transparent;color:#65656d;width:30px;height:30px;border-radius:7px;\n  display:inline-grid;place-items:center;font-size:15px;cursor:pointer;padding:0\n}\n.icon-action:hover{background:#f4f4f5;color:#222}\n.subtle-status{justify-content:flex-end;margin-bottom:8px;gap:10px;font-size:9px;color:#a1a1aa}\n.positions-right{display:flex;align-items:center;gap:14px;flex-wrap:wrap;justify-content:flex-end}\n.danger-actions{display:flex;align-items:center;gap:5px}\n.danger-actions .btn{padding:6px 8px;font-size:10px}\n.stop-new{color:#8a5a00;border-color:#e7d5a2;background:#fffdf6}\n.close-all{color:var(--red);border-color:#efb9b4;background:#fff}\n.confirm-field{margin-top:12px}\n.confirm-field label{display:block;font-size:10px;color:var(--muted);margin-bottom:5px}\n.confirm-field input{width:100%}\n.row-close{\n  border:1px solid #efb9b4;background:#fff;color:var(--red);border-radius:7px;\n  padding:4px 7px;font-size:9px;font-weight:800;cursor:pointer\n}\n.row-close:hover{background:var(--red-bg)}\n\n\n.summaryline b.pos{color:var(--green)}\n.summaryline b.neg{color:var(--red)}\n\n\n.detail-top{margin-bottom:9px}\n.back-link{border:0;background:transparent;padding:0;color:#62626a;font-size:11px;font-weight:750;cursor:pointer}\n.back-link:hover{text-decoration:underline;text-underline-offset:3px}\n.detail-actions{display:flex;align-items:center;gap:7px}\n.detail-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-top:0}\n.detail-grid>div{padding:12px 13px;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}\n.detail-grid>div:nth-child(3n){border-right:0}\n.detail-value{font-size:12px;font-weight:680}\n.detail-note{padding:13px;font-size:12px}\n.logic-body{padding:13px}\n.formula-block{font-family:Consolas,monospace;font-size:11px;line-height:1.55;background:#fafafa;border:1px solid var(--line);border-radius:8px;padding:11px;white-space:pre-wrap}\n@media(max-width:760px){\n  .detail-grid{grid-template-columns:1fr 1fr}\n  .detail-grid>div:nth-child(3n){border-right:1px solid var(--line)}\n  .detail-grid>div:nth-child(2n){border-right:0}\n}\n\n\n.parameter-editor{border-top:1px solid var(--line);padding:12px 13px;background:#fcfcfd}\n.parameter-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}\n.parameter-grid label{font-size:9px;color:var(--muted);display:grid;gap:5px}\n.parameter-grid input{border:1px solid var(--line2);border-radius:8px;padding:7px 8px;font-size:11px;background:#fff;color:var(--text)}\n.parameter-actions{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:10px}\n.parameter-note{font-size:9px;color:var(--muted)}\n@media(max-width:760px){\n  .tabsbar{top:54px}\n  .parameter-grid{grid-template-columns:1fr}\n}\n\n\n.set-simple-grid{grid-template-columns:repeat(3,1fr)}\n.logic-choice{display:flex;gap:14px;align-items:center;padding:13px}\n.logic-choice label{font-size:11px;font-weight:700;display:flex;gap:6px;align-items:center}\n.explain-text{font-size:11px;line-height:1.5;margin-bottom:10px;color:#4b4b52}\n.coins-list{display:flex;gap:6px;flex-wrap:wrap;padding:13px}\n.coin-chip{display:inline-flex;padding:5px 8px;border:1px solid var(--line);border-radius:7px;background:#fafafa;font-size:10px;font-weight:700}\n@media(max-width:760px){\n  .set-simple-grid{grid-template-columns:1fr}\n  .logic-choice{flex-wrap:wrap}\n}\n\n\n.trigger-list{display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center}\n\n\n.used-in-list{display:grid;gap:4px;justify-items:start}\n.tiny-state{font-size:8px;font-weight:800;letter-spacing:.02em;margin-left:5px}\n.tiny-state.active{color:var(--green)}\n.tiny-state.testing{color:var(--blue)}\n.tiny-state.archived{color:#8a8a91}\n\n\n.message-action{position:relative}\n.message-count{\n  position:absolute;top:-3px;right:-7px;min-width:18px;height:15px;padding:0 4px;border-radius:999px;\n  background:var(--blue);color:#fff;font-size:8px;font-weight:800;line-height:15px;text-align:center;\n  box-shadow:0 0 0 2px #fff\n}\n\n\n#sets{padding-top:8px}\n\n\n.catalog-entry{margin-top:8px}\n.catalog-button{\n  width:100%;border:1px solid var(--line);background:#fff;border-radius:10px;padding:11px 13px;\n  display:flex;align-items:center;justify-content:space-between;color:var(--text);\n  font-size:11px;font-weight:760;cursor:pointer\n}\n.catalog-button:hover{background:#fafafa}\n.catalog-arrow{color:#8b8b93;font-size:14px}\n\n\n.subtle-status{\n  min-height:24px;\n  margin:2px 0 10px;\n  display:flex;\n  align-items:center;\n  justify-content:flex-end;\n  color:#9a9aa2;\n  font-size:9px;\n}\n\n#sets{padding-top:12px}\n\n.rules-grid{\n  display:grid;\n  grid-template-columns:repeat(3,1fr);\n  gap:10px;\n  padding-top:10px;\n}\n.rules-span{grid-column:1 / -1}\n.rule-form{display:grid}\n.rule-row{\n  display:grid;\n  grid-template-columns:1fr auto;\n  gap:18px;\n  align-items:center;\n  padding:12px 13px;\n  border-bottom:1px solid #f0f0f1;\n}\n.rule-row:last-child{border-bottom:0}\n.rule-name{font-size:11px;font-weight:760}\n.rule-desc{font-size:9px;color:var(--muted);margin-top:3px}\n.rule-control input,\n.rule-control select{\n  width:112px;\n  border:1px solid var(--line2);\n  background:#fff;\n  border-radius:8px;\n  padding:7px 8px;\n  font-size:11px;\n  color:var(--text);\n}\n.suffix-control{\n  position:relative;\n}\n.suffix-control input{padding-right:28px}\n.suffix-control span{\n  position:absolute;\n  right:9px;\n  top:50%;\n  transform:translateY(-50%);\n  color:#888;\n  font-size:10px;\n  pointer-events:none;\n}\n.rule-actions{display:flex;gap:6px;align-items:center}\n.coins-editor{\n  border-top:1px solid var(--line);\n  background:#fcfcfd;\n  padding:12px 13px;\n}\n.coins-toolbar{\n  display:flex;\n  gap:8px;\n  align-items:center;\n  margin-bottom:10px;\n}\n.coins-toolbar .search{flex:1;max-width:320px}\n.coin-options{\n  display:grid;\n  grid-template-columns:repeat(5,1fr);\n  gap:7px;\n}\n.coin-options label{\n  border:1px solid var(--line);\n  background:#fff;\n  border-radius:8px;\n  padding:8px 9px;\n  font-size:10px;\n  display:flex;\n  align-items:center;\n  gap:6px;\n}\n.coins-footer{\n  display:flex;\n  align-items:center;\n  justify-content:space-between;\n  gap:10px;\n  margin-top:10px;\n}\n.rules-footer{\n  grid-column:1 / -1;\n  display:flex;\n  justify-content:flex-end;\n  align-items:center;\n  gap:10px;\n  padding:2px 0 4px;\n}\n.rules-save-state{font-size:9px;color:var(--muted)}\n.primary-rule{\n  background:#18181b;\n  color:#fff;\n  border-color:#18181b;\n}\n.primary-rule:hover{background:#27272a}\n\n@media(max-width:900px){\n  .rules-grid{grid-template-columns:1fr}\n  .rules-span,.rules-footer{grid-column:auto}\n  .coin-options{grid-template-columns:repeat(3,1fr)}\n}\n@media(max-width:620px){\n  .coin-options{grid-template-columns:repeat(2,1fr)}\n  .rule-row{grid-template-columns:1fr}\n  .rule-control input,.rule-control select{width:100%}\n  .coins-toolbar{flex-direction:column;align-items:stretch}\n  .coins-toolbar .search{max-width:none}\n}\n\n\n.rule-required{\n  display:inline-block;margin-left:6px;font-size:8px;font-weight:800;color:#77777f;\n  vertical-align:1px\n}\n.mini-toggle{display:inline-flex;vertical-align:middle;margin-left:7px;cursor:pointer}\n.mini-toggle input{display:none}\n.mini-toggle span{\n  width:25px;height:14px;border-radius:999px;background:#d8d8dd;display:block;position:relative;transition:.15s\n}\n.mini-toggle span:after{\n  content:"";position:absolute;width:10px;height:10px;border-radius:50%;background:#fff;left:2px;top:2px;\n  box-shadow:0 1px 2px rgba(0,0,0,.18);transition:.15s\n}\n.mini-toggle input:checked + span{background:#18181b}\n.mini-toggle input:checked + span:after{left:13px}\n.coin-options label{justify-content:space-between}\n.coin-options label>span:first-child{display:flex;align-items:center;gap:6px}\n.coin-limit{display:flex;align-items:center;gap:3px;color:#888;font-size:9px}\n.coin-limit input{\n  width:42px;border:0;border-bottom:1px solid var(--line2);border-radius:0;padding:2px 1px;\n  background:transparent;font-size:9px;text-align:right\n}\n.coin-chip small{font-size:8px;color:#8a8a91;margin-left:3px}\n\n\n.rr-control{position:relative}\n.rr-control input{\n  width:112px;\n  border:1px solid var(--line2);\n  background:#fff;\n  border-radius:8px;\n  padding:7px 34px 7px 8px;\n  font-size:11px;\n  color:var(--text);\n}\n.rr-control span{\n  position:absolute;\n  right:9px;\n  top:50%;\n  transform:translateY(-50%);\n  color:#888;\n  font-size:10px;\n  pointer-events:none;\n}\n\n\n#research{padding-top:10px}\n.research-toolbar{\n  display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px\n}\n.research-selects{display:flex;gap:7px;flex-wrap:wrap}\n.research-selects select{\n  border:1px solid var(--line2);background:#fff;border-radius:8px;padding:7px 9px;font-size:11px\n}\n.research-stages{\n  display:grid;\n  grid-template-columns:1fr auto 1fr auto 1fr;\n  align-items:center;\n  gap:8px;\n  margin-bottom:10px\n}\n.stage-card{\n  background:#fff;border:1px solid var(--line);border-radius:10px;padding:11px 12px;\n  display:grid;grid-template-columns:auto 1fr auto;gap:9px;align-items:center\n}\n.stage-card.active-stage{border-color:#d7e6da}\n.stage-kicker{\n  width:22px;height:22px;border-radius:50%;background:#f4f4f5;color:#666;display:grid;place-items:center;\n  font-size:9px;font-weight:800\n}\n.stage-name{font-size:11px;font-weight:780}\n.stage-status{font-size:9px;color:var(--muted);margin-top:2px}\n.stage-arrow{font-size:15px;color:#b0b0b7}\n.research-panel-actions{display:flex;gap:6px}\n.research-kpis{\n  display:grid;grid-template-columns:repeat(6,1fr);border-bottom:1px solid var(--line)\n}\n.research-kpi{padding:11px 12px;border-right:1px solid var(--line)}\n.research-kpi:last-child{border-right:0}\n.research-value{font-size:13px;font-weight:760}\n.progress-line{padding:12px 13px}\n.progress-labels{display:flex;justify-content:space-between;font-size:9px;color:var(--muted);margin-bottom:6px}\n.progress-track{height:6px;background:#f0f0f1;border-radius:999px;overflow:hidden}\n.progress-track span{display:block;height:100%;background:#18181b}\n.demo-empty{padding:22px 13px}\n.demo-empty-title{font-size:12px;font-weight:760}\n.demo-empty-meta{font-size:9px;color:var(--muted);margin-top:4px}\n.muted-row{color:#9a9aa2}\n@media(max-width:1000px){\n  .research-kpis{grid-template-columns:repeat(3,1fr)}\n  .research-kpi:nth-child(3){border-right:0}\n}\n@media(max-width:760px){\n  .research-toolbar{align-items:stretch;flex-direction:column}\n  .research-stages{display:flex;overflow:auto}\n  .stage-card{min-width:220px}\n  .stage-arrow{flex:0 0 auto}\n  .research-kpis{grid-template-columns:repeat(2,1fr)}\n  .research-kpi:nth-child(3){border-right:1px solid var(--line)}\n  .research-kpi:nth-child(2n){border-right:0}\n}\n\n\n#research{padding-top:10px}\n.research-list{margin-bottom:10px}\n.research-detail{display:none}\n.research-detail.open{display:block}\n.research-detail-head{display:flex;align-items:center;gap:14px;margin:2px 0 10px}\n.research-detail-title{font-size:13px;font-weight:800}\n.research-flow{\n  display:grid;\n  grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;\n  gap:8px;\n  align-items:center;\n  margin-bottom:10px\n}\n.research-flow-step{\n  background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 12px\n}\n.research-flow-step.done{border-color:#d8eddc;background:#fbfffc}\n.research-flow-step.active{border-color:#d9e5ff;background:#fbfdff}\n.flow-label{font-size:10px;font-weight:800}\n.flow-state{font-size:9px;color:var(--muted);margin-top:2px}\n.flow-arrow{color:#b2b2b8}\n.research-panel-actions{display:flex;gap:6px}\n.research-kpis{\n  display:grid;\n  grid-template-columns:repeat(6,1fr);\n  border-bottom:1px solid var(--line)\n}\n.research-kpi{padding:11px 12px;border-right:1px solid var(--line)}\n.research-kpi:last-child{border-right:0}\n.research-value{font-size:13px;font-weight:760}\n.demo-table-head{padding:10px 13px;border-bottom:1px solid var(--line)}\n.compare-head,.compare-row{\n  display:grid;\n  grid-template-columns:1.2fr 1fr 1fr 1fr;\n  gap:0;\n}\n.compare-head{background:#fafafa;border-bottom:1px solid var(--line)}\n.compare-head>div,.compare-row>div{padding:9px 11px;border-right:1px solid #f0f0f1}\n.compare-head>div:last-child,.compare-row>div:last-child{border-right:0}\n.compare-label{font-size:9px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}\n.compare-row{border-bottom:1px solid #f0f0f1;font-size:11px}\n.compare-row:last-child{border-bottom:0}\n.decision-actions{display:flex;gap:7px;justify-content:flex-end;padding:12px 13px;flex-wrap:wrap}\n@media(max-width:980px){\n  .research-kpis{grid-template-columns:repeat(3,1fr)}\n  .research-kpi:nth-child(3){border-right:0}\n}\n@media(max-width:760px){\n  .research-flow{display:flex;overflow:auto}\n  .research-flow-step{min-width:170px}\n  .flow-arrow{flex:0 0 auto}\n  .research-kpis{grid-template-columns:repeat(2,1fr)}\n  .research-kpi:nth-child(3){border-right:1px solid var(--line)}\n  .research-kpi:nth-child(2n){border-right:0}\n  .compare-head,.compare-row{grid-template-columns:1fr 1fr 1fr 1fr;min-width:620px}\n  .decision-actions{justify-content:flex-start}\n}\n\n\n.run-use-head,.run-use-cell{width:46px;text-align:center!important}\n.run-use-cell input[type="radio"]{width:14px;height:14px;accent-color:#18181b;cursor:pointer}\n.research-runs-table th.run-use-head{padding-left:6px;padding-right:6px}\n.research-runs-table td.run-use-cell{padding-left:6px;padding-right:6px}\n</style>\n</head>\n<body>\n<header class="top">\n  <div class="container topin">\n    <div class="brand"><span class="live-dot" id="botDot" title="Runtime state unavailable"></span><span>TriggerTrade</span></div>\n    <div class="actions">\n      <span class="badge gray state" id="operatorStateBadge">State unavailable</span>\n      <button class="icon-action message-action" title="Messages" aria-label="Messages" onclick="openMessages()">✉<span class="message-count" id="messageUnreadBadge" aria-hidden="true" style="display:none"></span></button>\n      <button class="icon-action" title="Copy system history" aria-label="Copy system history" onclick="copySystemHistory()" data-export-contract="TriggerTrade system history export">⧉</button>\n      <button class="icon-action" title="Settings" aria-label="Settings">⚙</button>\n    </div>\n  </div>\n</header>\n<nav class="tabsbar">\n  <div class="container tabs">\n    <button class="tab active" data-page="portfolio">Portfolio</button>\n    <button class="tab" data-page="sets">Sets</button>\n    <button class="tab" data-page="rules">Rules</button>\n    <button class="tab" data-page="research">Research</button>\n    <button class="tab" data-page="messages">Messages</button>\n  </div>\n</nav>\n<main class="container">\n<section class="page active" id="portfolio">\n  <div class="subtle-status"><span>Last update -</span></div>\n  <div class="pagehead">\n    <div><div class="pagetitle">Portfolio</div><div class="pagesub">Backend account and position state</div></div>\n    <div class="danger-actions"><button class="btn stop-new" onclick="openControlModal(\'pause\')">Pause Entries</button><button class="btn close-all" onclick="openControlModal(\'close\')">Close All</button></div>\n  </div>\n  <div class="kpis">\n    <div class="kpi"><div class="klabel">Total</div><div class="kvalue">-</div><div class="ksub">Account equity</div></div>\n    <div class="kpi"><div class="klabel">Available</div><div class="kvalue">-</div><div class="ksub">Free collateral</div></div>\n    <div class="kpi"><div class="klabel">In positions</div><div class="kvalue">-</div><div class="ksub">Allocated capital</div></div>\n    <div class="kpi"><div class="klabel">Realized P&L today</div><div class="kvalue">-</div><div class="ksub">Closed trades</div></div>\n    <div class="kpi"><div class="klabel">Unrealized P&L</div><div class="kvalue">-</div><div class="ksub">Open trades</div></div>\n    <div class="kpi"><div class="klabel">Open positions</div><div class="kvalue">-</div><div class="ksub">Current count</div></div>\n  </div>\n  <div class="panel">\n    <div class="panelhead">\n      <div><div class="title">Positions</div><div class="meta" id="positionSummary">Open <b>-</b></div></div>\n      <div class="positions-right"><div class="segment"><button id="openFilter" class="active" onclick="setPositionMode(\'open\')">Open</button><button id="closedFilter" onclick="setPositionMode(\'closed\')">Closed</button></div><div class="filters"><select><option>Coin: All</option></select><select><option>Side: All</option><option>LONG</option><option>SHORT</option></select><select><option>Set: All</option></select><select id="closeReasonFilter" style="display:none"><option>Close reason: All</option></select></div></div>\n    </div>\n    <div class="tablewrap"><table><thead id="positionHead"><tr><th>Coin</th><th>Side</th><th>Leverage</th><th>Qty</th><th>Value</th><th>Entry</th><th>Current Price</th><th>Take Profit</th><th>Stop Loss</th><th>Unrealized P&L</th><th>Set</th><th>Age</th><th></th></tr></thead><tbody id="positionBody"><tr><td colspan="13" class="placeholder">Portfolio unavailable.</td></tr></tbody></table></div>\n  </div>\n</section>\n<section class="page" id="sets">\n  <div class="pagehead"><div><div class="pagetitle">Sets</div><div class="pagesub">Registered Set versions</div></div></div>\n  <div class="panel"><div class="panelhead"><div><div class="title">Trigger Sets</div><div class="meta">Backend registry</div></div><button class="link" onclick="showPage(\'trigger-catalog\')">Trigger Catalog</button></div><div class="tablewrap"><table><thead><tr><th>Set</th><th>Version</th><th>Status</th><th>Triggers</th></tr></thead><tbody><tr><td colspan="4" class="placeholder">Sets unavailable.</td></tr></tbody></table></div></div>\n</section>\n<section class="page" id="trigger-catalog">\n  <div class="pagehead"><div><div class="pagetitle">Trigger Catalog</div><div class="pagesub">Registered Trigger versions</div></div></div>\n  <div class="panel"><div class="tablewrap"><table><thead><tr><th>Trigger</th><th>Version</th><th>What it checks</th></tr></thead><tbody><tr><td colspan="3" class="placeholder">Trigger Catalog unavailable.</td></tr></tbody></table></div></div>\n</section>\n<section class="page" id="trigger-detail">\n  <div class="detail-top"><button class="back-link" onclick="showPage(\'sets\')">Back to Sets</button></div>\n  <div class="panel"><div class="panelhead"><div><div class="title" id="triggerDetailTitle">Trigger unavailable</div><div class="meta">Version -</div></div></div><div class="logic-body"><div class="section-title">How it works</div><div class="explain-text">Trigger registry unavailable.</div><div class="formula-block">unavailable</div></div></div>\n  <div class="panel"><div class="panelhead"><div class="title">Parameters</div></div><div class="tablewrap"><table><tbody><tr><td colspan="3" class="placeholder">No parameters available.</td></tr></tbody></table></div></div>\n  <div class="panel"><div class="panelhead"><div class="title">Used in</div></div><div class="tablewrap"><table><tbody><tr><td colspan="3" class="placeholder">No usage available.</td></tr></tbody></table></div></div>\n  <div class="panel"><div class="panelhead"><div class="title">Version history</div></div><div class="tablewrap"><table><tbody><tr><td colspan="3" class="placeholder">No version history available.</td></tr></tbody></table></div></div>\n</section>\n<section class="page" id="rules">\n  <div class="pagehead"><div><div class="pagetitle">Rules</div><div class="pagesub">Rules unavailable.</div></div></div>\n</section>\n<section class="page" id="rules-version">\n  <div class="pagehead"><div><div class="pagetitle">Rules Version</div><div class="pagesub">Rules version unavailable.</div></div></div>\n</section>\n<section class="page" id="research">\n  <div class="pagehead"><div><div class="pagetitle">Research</div><div class="pagesub">Research unavailable.</div></div></div>\n</section>\n<section class="page" id="messages">\n  <div class="pagehead"><div><div class="pagetitle">Messages</div><div class="pagesub" id="messagesState">Unavailable</div></div></div>\n  <div class="panel"><div class="tablewrap"><table><thead><tr><th>Time</th><th>Message</th><th>Severity</th><th>State</th></tr></thead><tbody id="messagesBody"><tr><td colspan="4" class="placeholder">Messages unavailable.</td></tr></tbody></table></div></div>\n</section>\n<div class="modalbg" id="newResearchModal"></div>\n<div class="modalbg" id="controlModal">\n  <div class="modal">\n    <div class="panelhead"><div><div class="title" id="controlTitle">Confirm action</div><div class="meta" id="controlMeta"></div></div></div>\n    <div class="modalbody">\n      <div class="notice" id="controlNotice"></div>\n      <div class="confirm-field" id="confirmField" style="display:none"><label for="confirmInput">Type CLOSE ALL to confirm</label><input id="confirmInput" class="search" autocomplete="off" placeholder="CLOSE ALL"></div>\n      <div class="modalactions"><button class="btn" onclick="closeControlModal()">Cancel</button><button class="btn red" id="controlConfirm" onclick="confirmControlAction()">Confirm</button></div>\n    </div>\n  </div>\n</div>\n<script>\nfunction showPage(id){\n  document.querySelectorAll(".page").forEach(p=>p.classList.toggle("active",p.id===id));\n  document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("active",t.dataset.page===id));\n}\ndocument.querySelectorAll(".tab").forEach(t=>t.onclick=()=>showPage(t.dataset.page));\nlet controlAction = null;\nlet singleCloseSymbol = null;\nfunction openSingleClose(symbol){\n  singleCloseSymbol = symbol;\n  controlAction = "single-close";\n  confirmInput.value = "";\n  controlTitle.textContent = "Close " + symbol + "?";\n  controlMeta.textContent = "Single position";\n  controlNotice.textContent = "This will request closure of this position only.";\n  confirmField.style.display = "none";\n  controlConfirm.textContent = "Close";\n  controlModal.classList.add("open");\n}\nfunction openControlModal(action){\n  controlAction = action;\n  confirmInput.value = "";\n  if(action === "pause"){\n    controlTitle.textContent = "Pause new entries?";\n    controlMeta.textContent = "Protected trading control";\n    controlNotice.textContent = "The bot will stop opening new positions. Existing positions remain active and continue to be managed.";\n    confirmField.style.display = "none";\n    controlConfirm.textContent = "Pause Entries";\n  }else{\n    controlTitle.textContent = "Close All?";\n    controlMeta.textContent = "Emergency portfolio action";\n    controlNotice.textContent = "This will request closure of every currently open position. This action affects the whole portfolio.";\n    confirmField.style.display = "block";\n    controlConfirm.textContent = "Close All";\n  }\n  controlModal.classList.add("open");\n}\nfunction closeControlModal(){ controlModal.classList.remove("open"); }\nfunction confirmControlAction(){ closeControlModal(); }\nfunction openMessages(){ showPage("messages"); }\nfunction copySystemHistory(){\n  const node = document.getElementById("systemHistoryCopyState") || document.createElement("span");\n  node.id = "systemHistoryCopyState";\n  node.className = "meta";\n  node.textContent = "History unavailable";\n  if(!node.parentElement) document.querySelector(".actions")?.appendChild(node);\n}\n</script>\n</main>\n</body>\n</html>'


def _data_provenance_html(*, portfolio_live: bool, registry_live: bool) -> str:
    if portfolio_live and registry_live:
        return (
            '<div class="data-provenance" role="note">'
            "Dashboard state is loaded from backend read models. Unavailable fields are rendered as unavailable rather than sample data."
            "</div>"
        )
    return (
        '<div class="data-provenance" role="note">'
        "Some backend read models are unavailable. Missing runtime values are not substituted with sample data."
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


def _server_boundary_script(state: str, has_operator_token: bool, state_available: bool) -> str:
    state_json = json.dumps(state)
    return """
<script id="triggertrade-server-boundaries">
(function(){
  const operatorState = %s;
  const operatorStateAvailable = %s;
  const canSubmitOperatorControl = %s;
  let serverControlAction = null;

  function applyOperatorControlLabels(){
    if(!operatorStateAvailable){
      document.querySelectorAll(".stop-new").forEach((button) => {
        button.textContent = "Pause Entries";
        button.setAttribute("aria-label", "Pause Entries");
      });
      return;
    }
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

  function applyOperatorStateIndicator(){
    const dot = document.getElementById("botDot");
    const badge = document.getElementById("operatorStateBadge");
    if(!operatorStateAvailable){
      if(dot){
        dot.style.background = "#a1a1aa";
        dot.style.boxShadow = "0 0 0 4px #f4f4f5";
        dot.title = "Runtime state unavailable";
      }
      if(badge){
        badge.textContent = "State unavailable";
        badge.classList.toggle("green", false);
        badge.classList.toggle("amber", false);
        badge.classList.toggle("gray", true);
      }
      return;
    }
    const paused = operatorState === "TRADING_PAUSED";
    const label = paused ? "Entries paused" : "Entries enabled";
    if(dot){
      dot.style.background = paused ? "#a16207" : "#16783c";
      dot.style.boxShadow = paused ? "0 0 0 4px #fff8e6" : "0 0 0 4px #eef9f2";
      dot.title = label;
    }
    if(badge){
      badge.textContent = label;
      badge.classList.toggle("green", !paused);
      badge.classList.toggle("amber", paused);
      badge.classList.toggle("gray", false);
    }
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
  applyOperatorStateIndicator();
})();
</script>
""" % (
        state_json,
        "true" if state_available else "false",
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


def _render_registry_sections(html: str, registry: dict[str, Any]) -> str:
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


def _render_rules_sections(html: str, rules: dict[str, Any]) -> str:
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
    return html


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


def _render_messages_section(html: str, messages: dict[str, Any] | None) -> str:
    html = html.replace('<span class="message-count" aria-hidden="true">+2</span>', '<span class="message-count" id="messageUnreadBadge" aria-hidden="true" style="display:none"></span>', 1)
    html = html.replace('onclick="copySystemHistory()">⧉</button>', 'onclick="copySystemHistory()" data-export-contract="TriggerTrade system history export">⧉</button>', 1)
    return _replace_between(html, '<section class="page" id="messages">', '<div class="modalbg" id="newResearchModal">', _messages_section_html(messages) + "\n")


def _research_section_html(
    research: dict[str, Any] | None,
    registry: dict[str, Any] | None = None,
    rules: dict[str, Any] | None = None,
) -> str:
    rows = (research or {}).get("summaries") or ()
    body = "".join(
        f'<tr data-research-id="{_h(row.get("research_id"))}">'
        f"<td><button class=\"link\" onclick='openResearchById({_js_arg(row.get('research_id'))})'>{_h(row.get('research_id'))}</button></td>"
        f'<td>{_h(row.get("set_id"))}<div class="meta">{_h(row.get("set_version"))}</div></td>'
        f'<td>{_h(row.get("rules_display_version"))}<div class="meta">{_h(row.get("rules_version_id"))}</div></td>'
        f'<td>{_h(_research_pf_label(row.get("selected_backtest_profit_factor"), row.get("selected_backtest_trades")))}</td>'
        f'<td>{_h(_research_pf_label(row.get("selected_demo_profit_factor"), row.get("selected_demo_trades")))}</td>'
        f'<td>{_h(row.get("compare_to_active") or "Unavailable")}</td>'
        f'<td><span class="decision-status {_research_status_class(row.get("status"))}">{_h(row.get("decision") or row.get("status"))}</span></td>'
        f'</tr>'
        for row in rows
    )
    if not body:
        body = '<tr><td colspan="7" class="placeholder">No Research records.</td></tr>'
    return (
        '<section class="page" id="research">\n'
        '  <div class="research-list">\n'
        '    <div class="research-toolbar"><div><div class="pagetitle">Research</div>'
        '<div class="pagesub">Backend Research records. Backtest -> Demo -> Compare -> Decision.</div></div>'
        '<button class="btn" onclick="openNewResearchModal()">New Research</button></div>\n'
        '    <div class="panel"><div class="panelhead"><div><div class="title">Research Summary</div>'
        '<div class="meta">Exact Set and Rules version pins. Backtest, Demo, Compare, Decision.</div></div></div>'
        '      <div class="tablewrap"><table><thead><tr><th>Research</th><th>Set</th><th>Rules</th>'
        '<th>Backtest Profit Factor</th><th>Demo Profit Factor</th><th>Compare to Active</th><th>Decision</th></tr></thead>'
        f'<tbody id="researchSummaryBody">{body}</tbody></table></div></div>\n'
        '  </div>\n'
        '  <div class="research-detail" id="researchDetail">\n'
        '    <div class="research-detail-head"><button class="back-link" onclick="closeResearchSet()">Back</button>'
        '<div class="research-detail-title" id="researchDetailTitle">Research</div></div>\n'
        '    <div class="research-flow"><div class="research-flow-step"><div class="flow-label">Backtest</div>'
        '<div class="flow-state" id="flowBacktestState">Not started</div></div><div class="flow-arrow">-></div>'
        '<div class="research-flow-step"><div class="flow-label">Demo</div><div class="flow-state" id="flowDemoState">Not started</div></div>'
        '<div class="flow-arrow">-></div><div class="research-flow-step"><div class="flow-label">Compare</div>'
        '<div class="flow-state" id="flowCompareState">Not available</div></div><div class="flow-arrow">-></div>'
        '<div class="research-flow-step"><div class="flow-label">Decision</div><div class="flow-state" id="flowDecisionState">Not ready</div></div></div>\n'
        '    <div class="panel"><div class="panelhead"><div><div class="title">Pinned Versions</div>'
        '<div class="meta" id="researchPinnedMeta">Exact backend identities</div></div></div>'
        '<div class="detail-note" id="researchPinnedBody">No Research selected.</div></div>\n'
        '    <div class="panel"><div class="panelhead"><div class="title">Backtest Runs</div><div class="research-panel-actions"><input class="search" id="researchBacktestStart" type="datetime-local"><input class="search" id="researchBacktestEnd" type="datetime-local"><button class="btn" onclick="createBacktestRun()">Run Backtest</button></div></div>'
        '<div class="tablewrap"><table><thead><tr><th>Run</th><th>Status</th><th>Period</th><th>Trades</th><th>Net P/L</th><th>Win Rate</th><th>Profit Factor</th><th>Max Drawdown</th><th>Use</th></tr></thead><tbody id="backtestRunsBody"></tbody></table></div></div>\n'
        '    <div class="panel"><div class="panelhead"><div class="title">Demo Runs</div><button class="btn" onclick="startResearchDemo()">Start Demo</button></div>'
        '<div class="tablewrap"><table><thead><tr><th>Run</th><th>Status</th><th>Period</th><th>Trades</th><th>Net P/L</th><th>Win Rate</th><th>Profit Factor</th><th>Max Drawdown</th><th>Use</th></tr></thead><tbody id="demoRunsBody"></tbody></table></div></div>\n'
        '    <div class="panel" id="comparePanel"><div class="panelhead"><div class="title">Compare Demo to Active</div></div>'
        '<div class="compare-head"><div></div><div class="compare-label">Research Demo</div><div class="compare-label">Active</div><div class="compare-label">Difference</div></div>'
        '<div class="compare-empty">Compare becomes available after a stopped Demo run is selected and factual active overlap exists.</div></div>\n'
        '    <div class="panel decision-panel"><div class="decision-compact"><div class="decision-left">'
        '<div class="decision-title-inline">Decision</div><div class="decision-state-inline" id="decisionStateInline">Not ready</div></div>'
        '<div class="decision-actions-inline"><button class="btn" onclick="archiveResearch()">Archive</button>'
        '<button class="btn primary-rule" onclick="makeResearchActive()">Make Active</button></div></div></div>\n'
        '  </div>\n'
        '</section>\n'
        f'{_research_create_modal_html(registry, rules)}\n'
    )


def _research_create_modal_html(registry: dict[str, Any] | None, rules: dict[str, Any] | None) -> str:
    set_options = _research_set_options(registry)
    rules_options = _research_rules_options(rules)
    create_disabled = "" if set_options and rules_options else " disabled"
    if not set_options:
        set_options = '<option value="">No backend Trigger Set versions available</option>'
    if not rules_options:
        rules_options = '<option value="">No backend Rules versions available</option>'
    return f"""<div class="modalbg" id="newResearchModal">
  <div class="research-create-modal">
    <div class="research-create-head">
      <div>
        <div class="title">New Research</div>
        <div class="meta">Choose exact backend Set and Rules versions</div>
      </div>
      <button class="icon-action" onclick="closeNewResearchModal()">x</button>
    </div>
    <div class="research-create-body">
      <div class="research-create-grid">
        <label>
          Trigger Set
          <select id="newResearchSet">{set_options}</select>
        </label>
        <label>
          Rules
          <select id="newResearchRules">{rules_options}</select>
        </label>
      </div>
      <div class="research-create-note" id="newResearchState">
        The new Research record will pin the selected exact backend identities.
      </div>
      <div class="research-create-actions">
        <button class="btn" onclick="closeNewResearchModal()">Cancel</button>
        <button class="btn primary-rule" onclick="createNewResearch()"{create_disabled}>Create Research</button>
      </div>
    </div>
  </div>
</div>"""


def _research_set_options(registry: dict[str, Any] | None) -> str:
    rows = (_safe_payload(registry or {}).get("sets") or ())
    options = []
    for row in rows:
        set_id = str(row.get("set_id") or "")
        version = str(row.get("version") or "")
        if not set_id or not version:
            continue
        status = str(row.get("status") or "UNKNOWN")
        label = f"{set_id}@{version} · {status}"
        options.append(f'<option value="{_h(set_id + "|" + version)}">{_h(label)}</option>')
    return "".join(options)


def _research_rules_options(rules: dict[str, Any] | None) -> str:
    payload = _safe_payload(rules or {})
    seen: set[str] = set()
    rows = []
    current = payload.get("current")
    if current:
        rows.append(current)
    rows.extend(payload.get("history") or ())
    options = []
    for row in rows:
        rules_version_id = str(row.get("rules_version_id") or "")
        if not rules_version_id or rules_version_id in seen:
            continue
        seen.add(rules_version_id)
        display = str(row.get("display_version") or "-")
        label = f"{display} · {rules_version_id}"
        options.append(f'<option value="{_h(rules_version_id)}">{_h(label)}</option>')
    return "".join(options)


def _research_pf_label(profit_factor: Any, trades: Any) -> str:
    if profit_factor is None or profit_factor == "":
        return "-"
    suffix = "" if trades is None else f" · {trades} trades"
    return f"{profit_factor}{suffix}"


def _research_wiring_script(research: dict[str, Any] | None, token: str) -> str:
    payload = json.dumps(_safe_payload(research or {"summaries": ()}), ensure_ascii=False).replace("</", "<\\/")
    token_json = json.dumps(token)
    return f"""
<script id="triggertrade-research-read-model">
(function(){{
  const token = {token_json};
  let summaries = ({payload}).summaries || [];
  let currentResearch = null;
  const detail = document.getElementById("researchDetail");
  const list = document.querySelector(".research-list");
  const busy = new Set();
  function html(v){{ return String(v ?? "").replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}}[ch])); }}
  function statusClass(status){{ const value=String(status||"").toUpperCase(); if(value.includes("RUNNING"))return"running"; if(value.includes("BLOCKED")||value.includes("FAILED"))return"attention"; if(value.includes("ARCHIVED"))return"archived"; return"draft"; }}
  function pfLabel(value,trades){{ return value===null || value===undefined || value==="" ? "-" : `${{html(value)}}${{trades===null || trades===undefined ? "" : " · "+html(trades)+" trades"}}`; }}
  function setAction(text){{ const node=document.getElementById("newResearchState"); if(node)node.textContent=text; }}
  function renderSummaryRows(rows){{
    const body=document.getElementById("researchSummaryBody");
    if(!body)return;
    if(!rows || !rows.length){{ body.innerHTML='<tr><td colspan="7" class="placeholder">No Research records.</td></tr>'; return; }}
    body.innerHTML=rows.map(row=>`<tr data-research-id="${{html(row.research_id)}}"><td><button class="link" onclick='openResearchById("${{html(row.research_id)}}")'>${{html(row.research_id)}}</button></td><td>${{html(row.set_id)}}<div class="meta">${{html(row.set_version)}}</div></td><td>${{html(row.rules_display_version)}}<div class="meta">${{html(row.rules_version_id)}}</div></td><td>${{pfLabel(row.selected_backtest_profit_factor,row.selected_backtest_trades)}}</td><td>${{pfLabel(row.selected_demo_profit_factor,row.selected_demo_trades)}}</td><td>${{html(row.compare_to_active||"Unavailable")}}</td><td><span class="decision-status ${{statusClass(row.status)}}">${{html(row.decision||row.status)}}</span></td></tr>`).join("");
  }}
  async function refreshSummaries(){{
    const res=await fetch("/api/research");
    const data=await res.json();
    if(!res.ok)throw new Error(data.error||"Research unavailable");
    summaries=data.research||[];
    renderSummaryRows(summaries);
    return summaries;
  }}
  async function postJson(url, body){{
    const key=url+JSON.stringify(body||{{}});
    if(busy.has(key))return null;
    busy.add(key);
    try{{
      const res=await fetch(url, {{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(body||{{token}})}});
      const data=await res.json().catch(()=>({{}}));
      if(!res.ok)throw new Error(data.error||data.reason||"Request failed");
      return data;
    }}finally{{
      busy.delete(key);
    }}
  }}
  async function refreshAndOpen(id){{
    await refreshSummaries();
    if(id)await window.openResearchById(id);
  }}
  function localDateTimeValue(id){{
    const value=document.getElementById(id)?.value || "";
    if(!value)return "";
    return new Date(value).toISOString();
  }}
  function runRows(rows, kind){{
    if(!rows || !rows.length)return `<tr><td colspan="9" class="placeholder">No ${{kind}} runs.</td></tr>`;
    return rows.map(r=>{{
      const canUse = kind==="backtest" ? ["COMPLETED","COMPLETED_NO_TRADES"].includes(String(r.status)) : String(r.status)==="STOPPED";
      const selectAction = kind==="backtest" ? "selectBacktestRun" : "selectDemoRun";
      const use = canUse ? `<input type="radio" name="${{kind}}Use" ${{r.selected_for_use ? "checked" : ""}} onchange="${{selectAction}}('${{html(r.run_id)}}')">` : "";
      const stop = kind==="demo" && String(r.status)==="RUNNING" ? ` <button class="link" onclick="stopDemoRun('${{html(r.run_id)}}')">Stop</button>` : "";
      return `<tr><td>${{html(r.run_id)}}</td><td>${{html(r.status)}}${{stop}}</td><td>${{html(r.period_start||r.started_at||"-")}} -> ${{html(r.period_end||r.stopped_at||r.blocked_reason||r.unavailable_reason||"-")}}</td><td>${{html(r.metrics?.closed_trades??"-")}}</td><td>${{html(r.metrics?.net_pnl??"-")}}</td><td>${{html(r.metrics?.win_rate??"-")}}</td><td>${{html(r.metrics?.profit_factor??"-")}}</td><td>${{html(r.metrics?.max_drawdown??"-")}}</td><td class="run-use-cell">${{use}}</td></tr>`;
    }}).join("");
  }}
  function renderCompare(data){{
    const panel=document.getElementById("comparePanel");
    if(!panel)return;
    const head=`<div class="panelhead"><div class="title">Compare Demo to Active</div></div><div class="compare-head"><div></div><div class="compare-label">Research Demo</div><div class="compare-label">Active</div><div class="compare-label">Difference</div></div>`;
    if(!data?.available){{
      panel.innerHTML=head+`<div class="compare-empty">${{html(data?.reason||"Compare unavailable")}}</div>`;
      return;
    }}
    const rd=data.research_demo||{{}}, active=data.active_benchmark||{{}}, diff=data.difference||{{}};
    panel.innerHTML=head+[
      ["Closed trades",rd.closed_trades,active.closed_trades,diff.closed_trades],
      ["Net P/L",rd.net_pnl,active.net_pnl,diff.net_pnl],
      ["Expectancy",rd.expectancy,active.expectancy,diff.expectancy],
      ["Fees",rd.fees,active.fees,diff.fees],
    ].map(row=>`<div class="compare-row"><div>${{html(row[0])}}</div><div>${{html(row[1]??"-")}}</div><div>${{html(row[2]??"-")}}</div><div>${{html(row[3]??"-")}}</div></div>`).join("");
  }}
  async function loadCompare(id){{
    const f3=document.getElementById("flowCompareState");
    try{{
      const res=await fetch(`/api/research/${{encodeURIComponent(id)}}/compare`);
      const data=await res.json();
      renderCompare(data);
      if(f3)f3.textContent=data.available ? "Available" : "Not available";
    }}catch(e){{
      renderCompare({{available:false,reason:"research compare unavailable"}});
      if(f3)f3.textContent="Unavailable";
    }}
  }}
  function renderDetail(data){{
    currentResearch = data;
    const r=data.research||{{}};
    if(list)list.style.display="none";
    if(detail)detail.classList.add("open");
    const title=document.getElementById("researchDetailTitle");
    if(title)title.textContent=r.research_id || "Research";
    const pinned=document.getElementById("researchPinnedBody");
    if(pinned)pinned.innerHTML=`Set: <b>${{html(r.set_id)}}@${{html(r.set_version)}}</b><br>Rules: <b>${{html(r.rules_display_version)}} · ${{html(r.rules_version_id)}}</b><br>Decision: ${{html(r.decision)}}`;
    const bt=document.getElementById("backtestRunsBody");
    const dm=document.getElementById("demoRunsBody");
    if(bt)bt.innerHTML=runRows(data.backtests||[], "backtest");
    if(dm)dm.innerHTML=runRows(data.demos||[], "demo");
    const f1=document.getElementById("flowBacktestState"), f2=document.getElementById("flowDemoState"), f3=document.getElementById("flowCompareState"), f4=document.getElementById("flowDecisionState");
    if(f1)f1.textContent=r.selected_backtest_run_id ? "Selected" : ((data.backtests||[]).length ? "Available" : "Not started");
    if(f2)f2.textContent=r.selected_demo_run_id ? "Selected" : ((data.demos||[]).length ? "Available" : "Not started");
    if(f3)f3.textContent=r.selected_demo_run_id ? "Loading compare" : "Not available";
    if(f4)f4.textContent=r.decision==="NONE" ? "Not ready" : html(r.decision);
    const decisionLabel=document.getElementById("decisionStateInline");
    if(decisionLabel)decisionLabel.textContent=r.decision==="NONE" ? "Not ready" : r.decision;
    if(r.research_id)loadCompare(r.research_id);
  }}
  window.openResearchById = async function(id){{
    const res=await fetch(`/api/research/${{encodeURIComponent(id)}}`);
    const data=await res.json();
    if(res.ok)renderDetail(data);
  }};
  window.closeResearchSet = function(){{ if(list)list.style.display="block"; if(detail)detail.classList.remove("open"); }};
  window.openNewResearchModal = function(){{
    const modal=document.getElementById("newResearchModal");
    const state=document.getElementById("newResearchState");
    if(state)state.textContent="The new Research record will pin the selected exact backend identities.";
    if(modal)modal.classList.add("open");
  }};
  window.closeNewResearchModal = function(){{
    const modal=document.getElementById("newResearchModal");
    if(modal)modal.classList.remove("open");
  }};
  window.createNewResearch = async function(){{
    const setValue=document.getElementById("newResearchSet")?.value || "";
    const rules_version_id=document.getElementById("newResearchRules")?.value || "";
    const [set_id,set_version]=setValue.split("|");
    if(!set_id || !set_version || !rules_version_id){{ setAction("Backend Set and Rules versions are unavailable."); return; }}
    try{{
      const data=await postJson("/api/research", {{token,set_id,set_version,rules_version_id}});
      if(!data)return;
      window.closeNewResearchModal();
      await refreshAndOpen(data.research?.research_id);
    }}catch(e){{ setAction(e.message || "Research creation failed"); }}
  }};
  window.createBacktestRun = async function(){{
    if(!currentResearch?.research?.research_id)return;
    const id=currentResearch.research.research_id;
    try{{
      await postJson(`/api/research/${{encodeURIComponent(id)}}/backtests`, {{
        token,
        research_start: localDateTimeValue("researchBacktestStart"),
        research_end: localDateTimeValue("researchBacktestEnd")
      }});
      await refreshAndOpen(id);
    }}catch(e){{ renderCompare({{available:false,reason:e.message || "Backtest unavailable"}}); }}
  }};
  window.startResearchDemo = async function(){{
    if(!currentResearch?.research?.research_id)return;
    const id=currentResearch.research.research_id;
    try{{
      await postJson(`/api/research/${{encodeURIComponent(id)}}/demo/start`, {{token}});
    }}catch(e){{ renderCompare({{available:false,reason:e.message || "Demo start unavailable"}}); }}
    await refreshAndOpen(id);
  }};
  window.stopDemoRun = async function(runId){{
    if(!currentResearch?.research?.research_id)return;
    const id=currentResearch.research.research_id;
    try{{ await postJson(`/api/research/${{encodeURIComponent(id)}}/demo/${{encodeURIComponent(runId)}}/stop`, {{token}}); }}
    catch(e){{ renderCompare({{available:false,reason:e.message || "Demo stop unavailable"}}); }}
    await refreshAndOpen(id);
  }};
  window.selectBacktestRun = async function(runId){{
    if(!currentResearch?.research?.research_id)return;
    const id=currentResearch.research.research_id;
    try{{ await postJson(`/api/research/${{encodeURIComponent(id)}}/backtests/${{encodeURIComponent(runId)}}/select`, {{token}}); }}
    catch(e){{ renderCompare({{available:false,reason:e.message || "Backtest selection unavailable"}}); }}
    await refreshAndOpen(id);
  }};
  window.selectDemoRun = async function(runId){{
    if(!currentResearch?.research?.research_id)return;
    const id=currentResearch.research.research_id;
    try{{ await postJson(`/api/research/${{encodeURIComponent(id)}}/demo/${{encodeURIComponent(runId)}}/select`, {{token}}); }}
    catch(e){{ renderCompare({{available:false,reason:e.message || "Demo selection unavailable"}}); }}
    await refreshAndOpen(id);
  }};
  window.archiveResearch = async function(){{
    if(!currentResearch?.research?.research_id)return;
    const id=currentResearch.research.research_id;
    try{{ await postJson(`/api/research/${{encodeURIComponent(id)}}/archive`, {{token}}); }}
    catch(e){{ renderCompare({{available:false,reason:e.message || "Archive unavailable"}}); }}
    window.closeResearchSet();
    await refreshSummaries();
  }};
  window.makeResearchActive = async function(){{
    if(!currentResearch?.research?.research_id)return;
    const id=currentResearch.research.research_id;
    try{{
      const data=await postJson(`/api/research/${{encodeURIComponent(id)}}/decision/make-active`, {{token}});
      const label=document.getElementById("decisionStateInline");
      if(label)label.textContent=data?.research?.decision || "Decision unavailable";
      await refreshAndOpen(id);
    }}catch(e){{
      const label=document.getElementById("decisionStateInline");
      if(label)label.textContent="MAKE_ACTIVE_BLOCKED";
      const pinned=document.getElementById("researchPinnedBody");
      if(pinned)pinned.innerHTML += `<br>Make Active: ${{html(e.message || "Promotion unavailable")}}`;
      await refreshSummaries();
    }}
  }};
}})();
</script>
"""


def _render_research_sections(
    html: str,
    research: dict[str, Any] | None,
    registry: dict[str, Any] | None = None,
    rules: dict[str, Any] | None = None,
) -> str:
    replacement = _research_section_html(research, registry, rules) + "\n"
    replaced = _replace_between(html, '<section class="page" id="research">', '<section class="page" id="messages">', replacement)
    if replaced != html:
        return replaced
    if '<section class="page" id="messages">' in html:
        return html.replace('<section class="page" id="messages">', replacement + '<section class="page" id="messages">', 1)
    return _replace_between(html, '<section class="page" id="research">', '<div class="modalbg" id="newResearchModal">', replacement)


def _remove_legacy_research_modals(html: str) -> str:
    return _replace_between(html, '<div class="modalbg" id="newResearchModal">', '<div class="modalbg" id="controlModal">', "")


def _remove_legacy_research_scripts(html: str) -> str:
    html = _replace_between(html, '<script id="research-interactive-behavior">', '<script id="research-summary-sync-fix">', "")
    return _replace_between(html, '<script id="research-summary-sync-fix">', "</body>", "")


def _research_status_class(value: Any) -> str:
    status = str(value or "").upper()
    if "RUNNING" in status:
        return "running"
    if "BLOCKED" in status or "FAILED" in status:
        return "attention"
    if "ARCHIVED" in status:
        return "archived"
    return "draft"


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


def render_product_dashboard(
    *,
    initial_page: str = "portfolio",
    operator_state: Any = None,
    operator_control_token: str = "",
    portfolio: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    rules: dict[str, Any] | None = None,
    messages: dict[str, Any] | None = None,
    research: dict[str, Any] | None = None,
) -> str:
    page = initial_page if initial_page in _ALLOWED_PAGES else "portfolio"
    startup = ["window.showPage && window.showPage(" + json.dumps(page) + ");"]
    if page == "messages":
        startup.append("window.openMessages && window.openMessages();")
    if page == "research-detail":
        startup.append("window.showPage && window.showPage('research');")
    raw_state = getattr(operator_state, "state", None) if operator_state is not None else None
    state_available = raw_state in {"TRADING_ENABLED", "TRADING_PAUSED"}
    state = raw_state if state_available else "UNKNOWN"
    if state == "TRADING_PAUSED":
        startup.append("if(window.botDot){botDot.style.background='#a16207';botDot.style.boxShadow='0 0 0 4px #fff8e6';botDot.title='Bot running · new entries paused';}")
    marker = "</body>"
    html = _PRODUCT_UI_HTML.replace(
        "<main class=\"container\">",
        '<main class="container">\n' + _data_provenance_html(portfolio_live=portfolio is not None, registry_live=registry is not None),
        1,
    )
    if registry is not None:
        html = _render_registry_sections(html, registry)
    if rules is not None:
        html = _render_rules_sections(html, rules)
    html = _render_messages_section(html, messages)
    html = _remove_legacy_research_modals(html)
    html = _render_research_sections(html, research, registry, rules)
    html = _remove_legacy_research_scripts(html)
    html = html.replace(
        ".placeholder{padding:50px 20px;text-align:center;color:var(--muted);font-size:11px}",
        ".placeholder{padding:50px 20px;text-align:center;color:var(--muted);font-size:11px}\n"
        ".data-provenance{margin:2px 0 10px;border:1px solid #dce7ff;background:#f8fbff;color:#31519b;"
        "border-radius:8px;padding:8px 10px;font-size:10px;font-weight:700}",
        1,
    )
    script = (
        '\n<script id="triggertrade-server-startup">'
        + "".join(startup)
        + "</script>\n"
        + _operator_forms_html(operator_control_token)
        + _server_boundary_script(state, bool(operator_control_token), state_available)
        + _portfolio_wiring_script(portfolio)
        + _registry_wiring_script(registry)
        + _rules_wiring_script(rules, operator_control_token)
        + _messages_wiring_script(messages, operator_control_token)
        + _research_wiring_script(research, operator_control_token)
    )
    return html.replace(marker, script + marker)


def render_product_not_found(value: str) -> str:
    return """<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Not Found</title></head><body><main style="font-family:Inter,system-ui,sans-serif;padding:22px"><h1>Not Found</h1><p>{}</p></main></body></html>""".format(escape(value, quote=True))
