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


def _operator_forms_html() -> str:
    return (
        '<form id="operatorPauseForm" method="post" action="/operator/pause" hidden>'
        '<input type="hidden" name="confirm" value="yes">'
        '<input type="hidden" name="idempotency_key" value="">'
        "</form>"
        '<form id="operatorResumeForm" method="post" action="/operator/resume" hidden>'
        '<input type="hidden" name="confirm" value="yes">'
        '<input type="hidden" name="idempotency_key" value="">'
        "</form>"
        '<form id="operatorCloseOneForm" method="post" action="/operator/close-one" hidden>'
        '<input type="hidden" name="confirm" value="yes">'
        '<input type="hidden" name="idempotency_key" value="">'
        '<input type="hidden" name="position_id" value="">'
        '<input type="hidden" name="symbol" value="">'
        "</form>"
        '<form id="operatorCloseAllForm" method="post" action="/operator/close-all" hidden>'
        '<input type="hidden" name="confirm" value="yes">'
        '<input type="hidden" name="idempotency_key" value="">'
        '<input type="hidden" name="phrase" value="CLOSE ALL">'
        "</form>"
    )


def _server_boundary_script(
    state: str,
    operator_command_submit_enabled: bool,
    state_available: bool,
    local_dev_operator_controls: bool = False,
) -> str:
    state_json = json.dumps(state)
    return """
<script id="triggertrade-server-boundaries">
(function(){
  const operatorState = %s;
  const operatorStateAvailable = %s;
  const canSubmitOperatorControl = %s;
  const localDevOperatorControls = %s;
  let serverControlAction = null;
  let serverClosePosition = null;

  function applyOperatorControlLabels(){
    const buttons = document.querySelectorAll('.stop-new, button[onclick*="confirmPauseEntries"], button[onclick*="action(\\'pause\\')"]');
    if(!operatorStateAvailable){
      buttons.forEach((button) => {
        button.textContent = "Pause Entries";
        button.setAttribute("aria-label", "Pause Entries");
      });
      return;
    }
    buttons.forEach((button) => {
      if(operatorState === "TRADING_PAUSED"){
        button.textContent = "Resume Entries";
        button.setAttribute("aria-label", "Resume Entries");
      } else {
        button.textContent = "Pause Entries";
        button.setAttribute("aria-label", "Pause Entries");
      }
    });
  }

  function operatorStatusNode(){
    let node = document.getElementById("operatorCommandStatus");
    if(node) return node;
    node = document.createElement("div");
    node.id = "operatorCommandStatus";
    node.className = "panel-meta";
    node.style.minWidth = "180px";
    const target =
      document.querySelector("#tt-desktop-reference .positions-actions") ||
      document.querySelector(".positions-actions") ||
      document.querySelector(".header-actions") ||
      document.body;
    target.appendChild(node);
    return node;
  }

  function setOperatorStatus(message, tone){
    const node = operatorStatusNode();
    if(!node) return;
    node.textContent = message || "";
    node.className = "panel-meta " + (tone || "neutral");
  }

  function ensureControlModal(){
    let modal = document.getElementById("controlModal");
    if(!modal){
      const wrapper = document.createElement("div");
      wrapper.innerHTML = '<div class="modalbg sheet-bg" id="controlModal"><div class="modal sheet"><div class="panelhead panel-header"><div><div class="title panel-title" id="controlTitle">Confirm action</div><div class="meta panel-meta" id="controlMeta"></div></div></div><div class="modalbody"><div class="notice body-text" id="controlNotice"></div><div class="confirm-field" id="confirmField" style="display:none"><label for="confirmInput">Type CLOSE ALL to confirm</label><input id="confirmInput" class="search" autocomplete="off" placeholder="CLOSE ALL"></div><div class="modalactions" style="display:flex;justify-content:flex-end;gap:8px;margin-top:14px"><button class="btn row-action js-cancel-operator-command" type="button" id="controlCancel">Cancel</button><button class="btn danger red row-action js-confirm-operator-command" type="button" id="controlConfirm">Confirm</button></div></div></div></div>';
      modal = wrapper.firstElementChild;
      (document.getElementById("tt-desktop-reference") || document.body).appendChild(modal);
    }
    const desktopRoot = document.getElementById("tt-desktop-reference");
    if(desktopRoot && !desktopRoot.contains(modal)){
      desktopRoot.appendChild(modal);
    }
    let cancelButton = document.getElementById("controlCancel") || modal.querySelector(".modalactions button:not(#controlConfirm)");
    if(cancelButton){
      cancelButton.id = "controlCancel";
      cancelButton.type = "button";
      cancelButton.classList.add("row-action", "js-cancel-operator-command");
      cancelButton.onclick = null;
      if(!cancelButton.dataset.serverBoundaryBound){
        cancelButton.addEventListener("click", closeBoundaryModal);
        cancelButton.dataset.serverBoundaryBound = "true";
      }
    }
    const confirmButton = document.getElementById("controlConfirm");
    if(confirmButton){
      confirmButton.type = "button";
      confirmButton.classList.add("row-action", "js-confirm-operator-command");
      confirmButton.onclick = null;
      if(!confirmButton.dataset.serverBoundaryBound){
        confirmButton.addEventListener("click", function(){ window.confirmControlAction(); });
        confirmButton.dataset.serverBoundaryBound = "true";
      }
    }
    return modal;
  }

  function setModalText(title, meta, notice, confirmText, requiresPhrase){
    ensureControlModal();
    document.querySelectorAll("#operatorCommandStatus .js-confirm-operator-command, #operatorCommandStatus .js-cancel-operator-command").forEach((node) => node.remove());
    document.querySelectorAll("#tt-desktop-reference .js-confirm-operator-command, #tt-desktop-reference .js-cancel-operator-command").forEach((node) => {
      if(node.id !== "controlConfirm" && node.id !== "controlCancel") node.remove();
    });
    document.getElementById("controlTitle").textContent = title;
    document.getElementById("controlMeta").textContent = meta || "";
    document.getElementById("controlNotice").textContent = notice || "";
    const field = document.getElementById("confirmField");
    const input = document.getElementById("confirmInput");
    if(input) input.value = "";
    if(field) field.style.display = requiresPhrase ? "block" : "none";
    document.getElementById("controlConfirm").textContent = confirmText || "Confirm";
  }

  function openBoundaryModal(){
    const modal = ensureControlModal();
    modal.classList.add("open");
    modal.classList.add("show");
    modal.style.display = "flex";
  }

  function closeBoundaryModal(){
    const modal = document.getElementById("controlModal");
    if(!modal) return;
    modal.classList.remove("open");
    modal.classList.remove("show");
    modal.style.display = "";
  }

  window.closeControlModal = closeBoundaryModal;

  function assignIdempotency(form){
    const field = form && form.querySelector('input[name="idempotency_key"]');
    if(field && !field.value){
      field.value = form.id + "-" + Date.now() + "-" + Math.random().toString(16).slice(2);
    }
  }

  function publicFormError(text){
    return String(text || "Command failed").replace(/<[^>]*>/g, " ").replace(/\\s+/g, " ").trim().slice(0, 180) || "Command failed";
  }

  function commandHeaders(contentType){
    const headers = {"Content-Type": contentType};
    if(localDevOperatorControls){
      headers["X-TriggerTrade-Local-Operator"] = "1";
    }
    return headers;
  }

  function successMessageForForm(form){
    if(!form) return "Command submitted.";
    if(form.id === "operatorPauseForm") return "Entries paused.";
    if(form.id === "operatorResumeForm") return "Entries resumed.";
    if(form.id === "operatorCloseOneForm") return "Close Position submitted.";
    if(form.id === "operatorCloseAllForm") return "Close All submitted.";
    return "Command submitted.";
  }

  async function submitOperatorForm(form){
    if(!canSubmitOperatorControl){
      setOperatorStatus("Operator command submission is unavailable.", "negative");
      closeBoundaryModal();
      return;
    }
    if(!form){
      setOperatorStatus("Operator command form is unavailable.", "negative");
      closeBoundaryModal();
      return;
    }
    assignIdempotency(form);
    if(!window.fetch){
      form.submit();
      return;
    }
    const body = new URLSearchParams(new FormData(form));
    setOperatorStatus("Submitting...", "neutral");
    try{
      const response = await fetch(form.action, {
        method: "POST",
        credentials: "same-origin",
        headers: commandHeaders("application/x-www-form-urlencoded"),
        body
      });
      const text = await response.text();
      if(!response.ok) throw new Error(publicFormError(text));
      closeBoundaryModal();
      setOperatorStatus(successMessageForForm(form), "positive");
    }catch(error){
      closeBoundaryModal();
      setOperatorStatus(error.message || "Command failed.", "negative");
    }
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
  window.openSingleCloseById = function(positionId, symbol){
    if(!canSubmitOperatorControl){
      setOperatorStatus("Operator command submission is unavailable.", "negative");
      return;
    }
    serverClosePosition = {positionId, symbol};
    serverControlAction = "single-close";
    setModalText(
      "Close " + (symbol || "position") + "?",
      "Single position",
      "This will request closure of this position only.",
      "Close",
      false
    );
    openBoundaryModal();
  };
  window.closePosition = function(positionId, symbol){
    if(!canSubmitOperatorControl){
      setOperatorStatus("Operator command submission is unavailable.", "negative");
      return;
    }
    window.openSingleCloseById(positionId, symbol);
  };
  window.closeOne = window.closePosition;

  window.openControlModal = function(action){
    if(!canSubmitOperatorControl){
      setOperatorStatus("Operator command submission is unavailable.", "negative");
      return;
    }
    const normalizedAction = action === "pause" && operatorState === "TRADING_PAUSED" ? "resume" : action;
    serverControlAction = normalizedAction;
    if(normalizedAction === "pause"){
      setModalText(
        "Pause Entries?",
        "Protected trading control",
        "New entries will be paused. Existing positions remain active and continue to be managed.",
        "Pause Entries",
        false
      );
      openBoundaryModal();
      return;
    }
    if(normalizedAction === "resume"){
      setModalText(
        "Resume Entries?",
        "Protected trading control",
        "New entries will be resumed. Existing positions remain active and continue to be managed.",
        "Resume Entries",
        false
      );
      openBoundaryModal();
      return;
    }
    if(normalizedAction === "close"){
      setModalText(
        "Close All?",
        "Emergency portfolio action",
        "This will request closure of every currently open position. This action affects the whole portfolio.",
        "Close All",
        true
      );
      openBoundaryModal();
      return;
    }
    if(typeof originalOpenControlModal === "function"){
      originalOpenControlModal(normalizedAction);
    }
  };

  window.confirmPauseEntries = function(){
    window.openControlModal("pause");
  };

  window.confirmCloseAll = function(){
    window.openControlModal("close");
  };

  window.confirmControlAction = function(){
    if(serverControlAction === "pause" || serverControlAction === "resume"){
      const formId = serverControlAction === "resume" ? "operatorResumeForm" : "operatorPauseForm";
      const form = document.getElementById(formId);
      submitOperatorForm(form);
      return;
    }
    if(serverControlAction === "single-close"){
      const form = document.getElementById("operatorCloseOneForm");
      if(form && serverClosePosition){
        form.querySelector('input[name="position_id"]').value = serverClosePosition.positionId;
        form.querySelector('input[name="symbol"]').value = serverClosePosition.symbol;
      }
      submitOperatorForm(form);
      return;
    }
    if(serverControlAction === "close"){
      const input = document.getElementById("confirmInput");
      if(!input || input.value !== "CLOSE ALL"){
        setOperatorStatus("Type CLOSE ALL to confirm.", "negative");
        if(input) input.focus();
        return;
      }
      const form = document.getElementById("operatorCloseAllForm");
      submitOperatorForm(form);
      return;
    }
    if(typeof originalConfirmControlAction === "function"){
      originalConfirmControlAction();
    }
  };

  window.action = function(name){
    if(typeof window.backdrop === "function"){
      window.backdrop("actions-bg");
      window.backdrop("actionsSheet");
    }
    if(name === "pause") window.confirmPauseEntries();
    if(name === "close") window.confirmCloseAll();
  };

  document.addEventListener("click", function(event){
    const closeButton = event.target.closest(".js-close-position");
    if(closeButton){
      event.preventDefault();
      event.stopImmediatePropagation();
      window.openSingleCloseById(closeButton.dataset.positionId || "", closeButton.dataset.symbol || "");
      return;
    }
    const button = event.target.closest("button");
    if(!button) return;
    const onclick = button.getAttribute("onclick") || "";
    const text = (button.textContent || "").trim();
    if(onclick.indexOf("confirmPauseEntries") >= 0 || onclick.indexOf("action('pause')") >= 0 || ((text === "Pause Entries" || text === "Resume Entries") && button.closest(".positions-actions, #actionsSheet"))){
      event.preventDefault();
      event.stopImmediatePropagation();
      window.confirmPauseEntries();
      return;
    }
    if(onclick.indexOf("confirmCloseAll") >= 0 || onclick.indexOf("action('close')") >= 0 || (text === "Close All" && button.closest(".positions-actions, #actionsSheet"))){
      event.preventDefault();
      event.stopImmediatePropagation();
      window.confirmCloseAll();
    }
  }, true);

  applyOperatorControlLabels();
  applyOperatorStateIndicator();
})();
</script>
""" % (
        state_json,
        "true" if state_available else "false",
        "true" if operator_command_submit_enabled else "false",
        "true" if local_dev_operator_controls else "false",
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
      const idempotency_key=`research-promotion-${{id}}-${{Date.now()}}`;
      const data=await postJson(`/api/research/${{encodeURIComponent(id)}}/decision/make-active`, {{token,idempotency_key}});
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
    operator_command_submit_enabled: bool = False,
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
    operator_control_token = ""
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
        + _operator_forms_html()
        + _server_boundary_script(state, operator_command_submit_enabled, state_available, bool(operator_control_token))
        + _portfolio_wiring_script(portfolio)
        + _registry_wiring_script(registry)
        + _rules_wiring_script(rules, operator_control_token)
        + _messages_wiring_script(messages, operator_control_token)
        + _research_wiring_script(research, operator_control_token)
    )
    return html.replace(marker, script + marker)


def render_product_not_found(value: str) -> str:
    return """<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Not Found</title></head><body><main style="font-family:Inter,system-ui,sans-serif;padding:22px"><h1>Not Found</h1><p>{}</p></main></body></html>""".format(escape(value, quote=True))


def render_product_dashboard(
    *,
    initial_page: str = "overview",
    operator_state: Any = None,
    operator_control_token: str = "",
    operator_command_submit_enabled: bool = False,
    portfolio: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    rules: dict[str, Any] | None = None,
    messages: dict[str, Any] | None = None,
    research: dict[str, Any] | None = None,
) -> str:
    """Render the final three-area TriggerTrade UI over existing backend contracts."""

    page_map = {
        "portfolio": "overview",
        "overview": "overview",
        "sets": "config",
        "trigger-catalog": "config",
        "trigger-detail": "config",
        "rules": "config",
        "rules-version": "config",
        "config": "config",
        "research": "research",
        "research-detail": "research-detail",
        "messages": "research",
    }
    page = page_map.get(initial_page, "overview")
    raw_state = getattr(operator_state, "state", None) if operator_state is not None else None
    state_available = raw_state in {"TRADING_ENABLED", "TRADING_PAUSED"}
    state = raw_state if state_available else "UNKNOWN"
    payload = json.dumps(
        {
            "page": page,
            "operatorState": state,
            "operatorStateAvailable": state_available,
            "canSubmitOperatorControl": bool(operator_command_submit_enabled),
            "portfolio": _safe_payload(portfolio or {}),
            "registry": _safe_payload(registry or {}),
            "rules": _safe_payload(rules or {}),
            "research": _safe_payload(research or {"summaries": ()}),
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TriggerTrade</title>
<style>
:root{{--bg:#f6f8fb;--panel:#fff;--text:#182230;--text2:#475467;--muted:#8a94a6;--line:#e4e9f0;--line2:#d5dce6;--blue:#356ae6;--blue-soft:#eef4ff;--green:#16824b;--green-soft:#edf9f2;--red:#b42318;--red-soft:#fff1f0;--amber:#9a6700;--amber-soft:#fff7e5;--gray:#f2f4f7;--shadow:0 1px 2px rgba(16,24,40,.04)}}
*{{box-sizing:border-box}}body{{margin:0;min-width:320px;background:var(--bg);color:var(--text);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif}}button,input,select{{font:inherit}}button{{cursor:pointer}}.header{{height:58px;display:flex;align-items:center;justify-content:space-between;padding:0 24px;background:#fff;border-bottom:1px solid var(--line)}}.brand{{display:flex;align-items:center;gap:10px;font-size:15px;font-weight:850}}.brand-dot{{width:8px;height:8px;border-radius:50%;background:#1b9a59;box-shadow:0 0 0 4px #edf8f2}}.header-actions{{display:flex;align-items:center;gap:8px}}.icon-btn{{width:32px;height:32px;border:1px solid var(--line);border-radius:8px;background:#fff;color:#667085}}.top-nav{{background:#fff;border-bottom:1px solid var(--line)}}.top-nav-inner{{max-width:1460px;height:42px;margin:auto;padding:0 22px;display:flex;align-items:flex-end;gap:27px;overflow-x:auto}}.top-tab{{padding:0 0 10px;border:0;border-bottom:2px solid transparent;background:none;color:#818999;font-size:12px;font-weight:750;white-space:nowrap}}.top-tab.active{{color:var(--text);border-bottom-color:var(--text)}}.page{{display:none;max-width:1460px;margin:auto;padding:14px 22px 44px}}.page.active{{display:block}}.panel{{overflow:hidden;background:#fff;border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);margin-bottom:12px}}.panel-header{{min-height:54px;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 13px;border-bottom:1px solid var(--line)}}.panel-title{{font-size:13px;font-weight:850}}.panel-meta{{margin-top:2px;color:var(--muted);font-size:9px}}.btn{{min-height:31px;padding:6px 10px;border:1px solid var(--line2);border-radius:8px;background:#fff;color:#475467;font-size:10px;font-weight:800}}.btn.primary{{border-color:var(--blue);background:var(--blue);color:#fff}}.btn.warning{{border-color:#ead7a5;background:#fffaf0;color:#946200}}.btn.danger{{border-color:#f1c7c4;background:#fff6f5;color:#b42318}}input,select{{height:32px;padding:0 10px;border:1px solid var(--line2);border-radius:8px;background:#fff;color:#344054;font-size:10px}}.badge{{display:inline-flex;align-items:center;padding:4px 7px;border-radius:999px;font-size:8px;font-weight:850;white-space:nowrap}}.active,.complete,.opened{{background:var(--green-soft);color:var(--green)}}.research-badge{{background:#f4efff;color:#7047c8}}.placed,.running{{background:var(--blue-soft);color:#315fc9}}.closed,.none,.inactive{{background:var(--gray);color:#667085}}.cancelled,.pending{{background:var(--amber-soft);color:var(--amber)}}.reject,.failed{{background:var(--red-soft);color:var(--red)}}.positive{{color:var(--green)}}.negative{{color:var(--red)}}.neutral{{color:#667085}}.table-wrap{{width:100%;overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:10px}}th{{padding:8px 9px;background:#fafbfc;border-bottom:1px solid var(--line);color:#8d96a5;text-align:left;font-size:8px;font-weight:850;text-transform:uppercase;letter-spacing:.05em;white-space:nowrap}}td{{padding:9px;border-bottom:1px solid #eef1f4;vertical-align:middle}}tbody tr:last-child td{{border-bottom:0}}.kpis{{display:grid;grid-template-columns:repeat(6,minmax(120px,1fr));gap:8px;margin-bottom:12px}}.kpi{{min-height:83px;padding:11px 12px;background:#fff;border:1px solid var(--line);border-radius:9px;box-shadow:var(--shadow)}}.kpi-label{{color:#7e8898;font-size:9px}}.kpi-value{{margin-top:5px;font-size:17px;font-weight:850}}.positions-header{{width:100%;display:flex;align-items:center;justify-content:space-between;gap:12px}}.positions-left,.positions-actions,.filters,.run-actions,.decision-actions{{display:flex;align-items:center;gap:7px;flex-wrap:wrap}}.mobile-filter{{display:none}}.mobile-history-note{{display:none;padding:0 13px 9px;color:#7e8898;font-size:9px;font-weight:800}}.positions-tabs,.history-range,.config-tabs,.compare-tabs,.compare-periods{{display:inline-flex;gap:2px;padding:2px;border:1px solid var(--line);border-radius:8px;background:#f2f4f7}}.positions-tab,.range-btn,.config-tab,.compare-tab,.compare-period{{height:28px;padding:0 10px;border:0;border-radius:6px;background:transparent;color:#7b8493;font-size:9px;font-weight:800;white-space:nowrap}}.positions-tab.active,.range-btn.active,.config-tab.active,.compare-tab.active,.compare-period.active{{background:#fff;color:#253858;box-shadow:0 1px 2px rgba(16,24,40,.08)}}.positions-tools-row,.compare-toolbar{{min-height:50px;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:8px 13px;border-bottom:1px solid var(--line);background:#fbfcfd}}.history-tools{{display:none;align-items:center;gap:7px;margin-left:auto}}.history-tools.show{{display:flex}}.row-action{{min-width:56px;height:28px;padding:0 9px;border:1px solid var(--line2);border-radius:7px;background:#fff;color:#526071;font-size:9px;font-weight:850}}.row-action.danger{{border-color:#f0c5c1;background:#fff7f6;color:#b42318}}.config-nav{{display:flex;margin-bottom:12px;padding:0 14px;background:#fff;border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);overflow:auto}}.config-group{{padding:11px 20px 0 0}}.config-group+.config-group{{margin-left:10px;padding-left:22px;border-left:1px solid var(--line)}}.group-label{{margin:0 0 8px 2px;color:#98a2b3;font-size:8px;font-weight:850;text-transform:uppercase;letter-spacing:.09em}}.config-view{{display:none}}.config-view.active{{display:block}}.layout{{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(360px,.8fr);gap:12px}}.toolbar{{display:grid;grid-template-columns:minmax(120px,1fr) auto;gap:7px;width:100%}}.catalog-row{{cursor:pointer}}.catalog-row:hover{{background:#f8faff}}.details-header,.details-section{{padding:14px;border-bottom:1px solid var(--line)}}.details-id{{color:#7a8494;font-size:10px;font-weight:700}}.details-title{{margin-top:3px;font-size:15px;font-weight:850}}.body-text{{color:#475467;font-size:11px;line-height:1.55}}.formula{{padding:11px 12px;border:1px solid var(--line);border-radius:8px;background:#f8fafc;color:#344054;font-size:11px;line-height:1.55;white-space:pre-wrap}}.set-logic{{display:grid;gap:7px}}.set-logic-row{{display:grid;grid-template-columns:52px minmax(0,1fr);gap:7px}}.logic-keyword{{padding:6px;border-radius:6px;background:#edf3ff;color:#315fc9;text-align:center;font-size:8px;font-weight:900}}.logic-condition{{padding:8px 10px;border:1px solid var(--line);border-radius:7px;background:#fbfcfd;color:#344054;font-size:10px;line-height:1.45}}.rules-stack{{display:grid;gap:12px}}.rules-section{{overflow:hidden;background:#fff;border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow)}}.rules-section-title{{padding:11px 14px;background:#fafbfc;border-bottom:1px solid var(--line);color:#667085;font-size:10px;font-weight:850;text-transform:uppercase}}.rule-row{{min-height:52px;display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:16px;padding:9px 14px;border-bottom:1px solid #eef1f4}}.rule-name{{font-size:11px;font-weight:800}}.rule-description{{margin-top:3px;color:#8b95a6;font-size:9px}}.coins-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(132px,1fr));gap:7px;padding:12px 14px}}.coin-chip{{display:flex;align-items:center;justify-content:space-between;gap:7px;min-height:40px;padding:7px 8px;border:1px solid var(--line);border-radius:8px;background:#fbfcfd;font-size:10px;font-weight:800}}.research-toolbar{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px}}.research-filters{{display:flex;gap:7px;flex-wrap:wrap}}.research-row{{cursor:pointer}}.research-row:hover{{background:#f7faff}}.research-detail-head{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}}.research-detail-title{{font-size:17px;font-weight:850}}.workflow{{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin-bottom:12px}}.workflow-step{{min-height:62px;padding:10px 12px;background:#fff;border:1px solid var(--line);border-radius:9px}}.workflow-step.done{{border-color:#cce8d8;background:#f3fbf6}}.workflow-step.reject-done{{border-color:#f1c7c4;background:#fff6f5}}.workflow-label{{font-size:10px;font-weight:850}}.workflow-state{{margin-top:4px;color:#7e8898;font-size:9px}}.demo-segments{{display:flex;gap:3px;margin-top:7px}}.demo-segment{{flex:1;height:6px;border-radius:99px;background:#e7ebf0}}.demo-segment.filled{{background:#87a8ef}}.base-cell{{background:#f7f8fa;color:#344054;font-weight:850}}.good-cell{{background:#f0faf4;color:#147a45;font-weight:850}}.bad-cell{{background:#fff3f2;color:#b42318;font-weight:850}}.neutral-cell{{color:#667085}}.sheet-bg{{display:none;position:fixed;inset:0;z-index:50;align-items:flex-end;justify-content:center;background:rgba(15,23,42,.30)}}.sheet-bg.show{{display:flex}}.sheet{{width:min(430px,100%);padding:14px;border-radius:14px 14px 0 0;background:#fff}}.desktop-only{{display:block}}.mobile-list{{display:none}}.mobile-card{{padding:11px 10px;border-bottom:1px solid #eef1f4}}.mobile-card-details{{display:none;grid-template-columns:1fr 1fr;gap:9px 12px;margin-top:9px;padding-top:9px;border-top:1px solid #eef1f4}}.mobile-card.expanded .mobile-card-details{{display:grid}}.mobile-top{{display:flex;justify-content:space-between;gap:8px}}.mobile-grid{{display:grid;grid-template-columns:1fr 1fr;gap:9px 12px;margin-top:11px}}.fl{{margin-bottom:2px;color:#98a2b3;font-size:7px;text-transform:uppercase}}.fv{{font-size:10px;font-weight:750}}.empty{{padding:28px 14px;color:#98a2b3;font-size:10px;text-align:center}}@media(max-width:760px){{.header{{height:54px;padding:0 14px}}.brand{{font-size:14px}}.top-nav-inner{{padding:0 14px;gap:22px}}.top-tab{{font-size:10px}}.page{{padding:10px;max-width:430px}}.kpis{{grid-template-columns:1fr 1fr;gap:7px}}.kpi{{min-height:72px;padding:10px}}.kpi-value{{font-size:15px}}.positions-header{{display:block}}.positions-left{{justify-content:space-between;margin-bottom:8px}}.positions-actions{{justify-content:flex-end}}.desktop-action{{display:none}}.mobile-filter{{display:inline-flex}}.mobile-history-note.show{{display:block}}.positions-tools-row{{display:none}}.desktop-only{{display:none}}.mobile-list{{display:block}}.layout{{grid-template-columns:1fr}}.config-nav{{display:flex}}.workflow{{grid-template-columns:1fr 1fr}}.compare-toolbar,.research-toolbar{{align-items:stretch;flex-direction:column}}.run-actions{{justify-content:flex-start}}.panel-header{{align-items:flex-start;flex-direction:column}}}}
</style>
</head>
<body>
<header class="header"><div class="brand"><span class="brand-dot" id="botDot"></span>TriggerTrade</div><div class="header-actions"><span class="badge closed" id="operatorStateBadge">State unavailable</span><button class="icon-btn" title="Settings">⚙</button></div></header>
<nav class="top-nav"><div class="top-nav-inner"><button class="top-tab" data-page="overview">Overview</button><button class="top-tab" data-page="config">Trading Configuration</button><button class="top-tab" data-page="research">Research</button></div></nav>
<main>
<section class="page" id="overview">
  <div class="kpis" id="overviewKpis"></div>
  <section class="panel">
    <div class="panel-header"><div class="positions-header"><div class="positions-left"><div class="panel-title">Positions</div><div class="positions-tabs"><button class="positions-tab active" data-pos="placed">Placed</button><button class="positions-tab" data-pos="open">Open</button><button class="positions-tab" data-pos="history">History</button></div></div><div class="positions-actions"><button class="btn warning desktop-action" onclick="confirmPauseEntries()">Pause Entries</button><button class="btn danger desktop-action" onclick="confirmCloseAll()">Close All</button><button class="btn mobile-filter" onclick="openSheet('filtersSheet')">Filters <span id="mobileFilterCount"></span></button><button class="btn mobile-filter" onclick="openSheet('actionsSheet')">Actions</button></div></div></div>
    <div class="positions-tools-row"><div class="filters"><select id="filterCoin"></select><select id="filterSide"><option value="">Side: All</option><option>LONG</option><option>SHORT</option></select><select id="filterStatus"><option value="">Status: All</option><option>PLACED</option><option>OPENED</option><option>CANCELLED</option><option>CLOSED</option></select><select id="filterSet"></select></div><div class="history-tools" id="historyTools"><div class="history-range"><button class="range-btn active" data-range="24H">24H</button><button class="range-btn" data-range="7D">7D</button><button class="range-btn" data-range="30D">30D</button><button class="range-btn" data-range="90D">90D</button></div><button class="btn" onclick="exportHistory()">Export History</button></div></div>
    <div class="mobile-history-note" id="mobileHistoryNote">Last 24H</div>
    <div class="table-wrap desktop-only"><table><thead><tr><th>Time</th><th>Coin</th><th>Side</th><th>Status</th><th>Qty</th><th>Value</th><th>Entry</th><th>Current / Exit Price</th><th>Take Profit</th><th>Stop Loss</th><th>P&L</th><th>Set</th><th>Age</th><th>Close / Cancel Reason</th><th>Action</th></tr></thead><tbody id="positionsBody"></tbody></table></div>
    <div class="mobile-list" id="positionsCards"></div>
  </section>
</section>
<section class="page" id="config">
  <nav class="config-nav"><div class="config-group"><div class="group-label">Signal Logic</div><div class="config-tabs"><button class="config-tab active" data-config="metrics">Metrics</button><button class="config-tab" data-config="triggers">Triggers</button><button class="config-tab" data-config="sets">Sets</button></div></div><div class="config-group"><div class="group-label">Trading</div><div class="config-tabs"><button class="config-tab" data-config="trading-rules">Trading Rules</button></div></div></nav>
  <div class="config-view active" id="config-metrics"><div class="layout"><section class="panel"><div class="panel-header"><div class="toolbar"><input class="search" id="metricSearch" placeholder="Search by ID or name"><div class="segment" id="metricFamilyFilters"><button type="button" class="metric-family-filter active" data-family="ALL">ALL</button><button type="button" class="metric-family-filter" data-family="F">F</button><button type="button" class="metric-family-filter" data-family="A">A</button><button type="button" class="metric-family-filter" data-family="M">M</button><button type="button" class="metric-family-filter" data-family="N">N</button><button type="button" class="metric-family-filter" data-family="S">S</button></div></div></div><div class="table-wrap"><table><thead><tr><th>ID</th><th>Name</th><th>Family</th><th>Type</th><th>Status</th></tr></thead><tbody id="metricsBody"></tbody></table></div></section><section class="panel" id="metricDetail"></section></div></div>
  <div class="config-view" id="config-triggers"><div class="layout"><section class="panel"><div class="panel-header"><div class="panel-title">Triggers</div></div><div class="table-wrap"><table><thead><tr><th>Trigger</th><th>Version</th><th>Metric</th><th>Condition</th><th>Used in Sets</th><th>Status</th></tr></thead><tbody id="triggersBody"></tbody></table></div></section><section class="panel" id="triggerDetail"></section></div></div>
  <div class="config-view" id="config-sets"><div class="layout"><section class="panel"><div class="panel-header"><div class="panel-title">Sets</div></div><div class="table-wrap"><table><thead><tr><th>Set</th><th>Version</th><th>Direction</th><th>Triggers</th><th>Status</th></tr></thead><tbody id="setsBody"></tbody></table></div></section><section class="panel" id="setDetail"></section></div></div>
  <div class="config-view" id="config-trading-rules"><div class="rules-stack" id="rulesBody"></div></div>
</section>
<section class="page" id="research">
  <div class="research-toolbar"><div class="research-filters"><input id="researchSearch" placeholder="Search"><select id="demoFilter"><option value="">Demo filter</option><option>Complete</option><option>Pending</option><option>Running</option></select><select id="decisionFilter"><option value="">Decision filter</option><option>NONE</option><option>REJECT</option><option>MAKE_ACTIVE</option></select></div><button class="btn primary" onclick="openNewResearch()">+ New Research</button></div>
  <section class="panel"><div class="table-wrap"><table><thead><tr><th>Research</th><th>Set</th><th>Rules</th><th>Demo</th><th>Demo PF</th><th>Active PF</th><th>Δ PF</th><th>Decision</th></tr></thead><tbody id="researchBody"></tbody></table></div></section>
</section>
<section class="page" id="research-detail">
  <div class="research-detail-head"><div class="research-detail-title" id="researchTitle">Research</div><button class="btn" onclick="exportResearch()">Export</button></div>
  <div class="workflow"><div class="workflow-step" id="wfBacktest"><div class="workflow-label">Backtest</div><div class="workflow-state" id="wfBacktestState">Pending</div></div><div class="workflow-step" id="wfDemo"><div class="workflow-label">Demo</div><div class="workflow-state" id="wfDemoState">Pending</div><div class="demo-segments" id="demoSegments"></div></div><div class="workflow-step" id="wfCompare"><div class="workflow-label">Compare</div><div class="workflow-state" id="wfCompareState">Pending</div></div><div class="workflow-step" id="wfDecision"><div class="workflow-label">Decision</div><div class="workflow-state" id="wfDecisionState">NONE</div></div></div>
  <section class="panel"><div class="panel-header"><div class="panel-title">Backtest</div><div class="run-actions"><button class="btn" onclick="runBacktest('7D')">Run 7D</button><button class="btn" onclick="runBacktest('30D')">Run 30D</button><button class="btn" onclick="runBacktest('90D')">Run 90D</button></div></div><div class="table-wrap"><table><thead><tr><th>Run</th><th>Period</th><th>Trades</th><th>Net P/L</th><th>Profit Factor</th><th>Result</th></tr></thead><tbody id="backtestBody"></tbody></table></div></section>
  <section class="panel"><div class="panel-header"><div class="panel-title">Demo</div><button class="btn" onclick="runDemo()">Run Demo 7D</button></div><div class="table-wrap"><table><thead><tr><th>Run</th><th>Period</th><th>Trades</th><th>Net P/L</th><th>Profit Factor</th><th>Result</th></tr></thead><tbody id="demoBody"></tbody></table></div></section>
  <section class="panel"><div class="panel-header"><div class="panel-title">Compare</div></div><div class="compare-toolbar"><div class="compare-tabs"><button class="compare-tab active" data-scope="overall">Overall</button><button class="compare-tab" data-scope="segment">By Segment</button><button class="compare-tab" data-scope="coin">By Coin</button><button class="compare-tab" data-scope="direction">By Direction</button></div><div class="compare-periods"><button class="compare-period active" data-period="7D">7D</button><button class="compare-period" data-period="30D">30D</button><button class="compare-period" data-period="90D">90D</button></div></div><div class="table-wrap"><table id="compareTable"></table></div></section>
  <section class="panel"><div class="panel-header"><div><div class="panel-title">Decision</div><div class="panel-meta" id="decisionStateInline">NONE</div></div><div class="decision-actions"><button class="btn danger" onclick="setDecision('reject')">Reject</button><button class="btn primary" onclick="setDecision('make-active')">Make Active</button></div></div></section>
</section>
</main>
<div id="filtersSheet" class="sheet-bg" onclick="backdrop(event,'filtersSheet')"><div class="sheet"><div class="panel-title">Filters</div><div class="filters" style="display:grid;grid-template-columns:1fr 1fr;margin-top:12px"><select id="mFilterCoin"></select><select id="mFilterSide"><option value="">Side: All</option><option>LONG</option><option>SHORT</option></select><select id="mFilterStatus"><option value="">Status: All</option><option>PLACED</option><option>OPENED</option><option>CANCELLED</option><option>CLOSED</option></select><select id="mFilterSet"></select></div><div style="display:flex;justify-content:flex-end;gap:7px;margin-top:14px"><button class="btn" onclick="resetMobileFilters()">Reset</button><button class="btn primary" onclick="applyMobileFilters()">Apply</button></div></div></div>
<div id="actionsSheet" class="sheet-bg" onclick="backdrop(event,'actionsSheet')"><div class="sheet"><div class="panel-title">Actions</div><button class="btn warning" style="width:100%;margin-top:12px" onclick="confirmPauseEntries()">Pause Entries</button><button class="btn danger" style="width:100%;margin-top:8px" onclick="confirmCloseAll()">Close All</button></div></div>
<div id="newResearchModal" class="sheet-bg" onclick="backdrop(event,'newResearchModal')"><div class="sheet"><div class="panel-title">New Research</div><label class="panel-meta">Trigger Set Version</label><select id="newResearchSet" style="width:100%;margin-top:4px"></select><label class="panel-meta" style="display:block;margin-top:10px">Rules Version</label><select id="newResearchRules" style="width:100%;margin-top:4px"></select><div id="newResearchState" class="panel-meta" style="margin-top:10px"></div><div style="display:flex;justify-content:flex-end;gap:7px;margin-top:14px"><button class="btn" onclick="closeNewResearch()">Cancel</button><button class="btn primary" onclick="createResearch()">Create Research</button></div></div></div>
{_operator_forms_html()}
<script id="triggertrade-data">window.__TT__={payload};</script>
<script>
(function(){{
const state=window.__TT__;
let page=state.page||"overview", posView="placed", historyRange="24H", configView="metrics", compareScope="overall", comparePeriod="7D", currentResearchId=null, currentResearch=null, currentCompare=null;
const html=v=>String(v??"—").replace(/[&<>"']/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}}[c]));
const money=v=>v===null||v===undefined||v===""?"—":"$"+String(v);
const signedMoney=v=>{{if(v===null||v===undefined||v==="")return"—";const n=Number(v);return Number.isNaN(n)?"$"+String(v):(n>=0?"+$":"-$")+Math.abs(n).toFixed(2)}};
const cls=v=>String(v||"").startsWith("-")?"negative":(Number(v)>0||String(v||"").startsWith("+")?"positive":"");
const pct=v=>v===null||v===undefined||v===""?"—":(Number(v)>=0?"+":"")+String(v)+"%";
const duration=s=>s===null||s===undefined?"—":(s<60?`${{s}}s`:s<3600?`${{Math.floor(s/60)}}m`:`${{Math.floor(s/3600)}}h ${{Math.floor((s%3600)/60)}}m`);
const statusBadge=s=>`<span class="badge ${{String(s||"").toLowerCase()}}">${{html(s||"—")}}</span>`;
function showPage(id){{page=id;document.querySelectorAll(".page").forEach(x=>x.classList.toggle("active",x.id===id));document.querySelectorAll(".top-tab").forEach(x=>x.classList.toggle("active",x.dataset.page===(id==="research-detail"?"research":id)));if(id==="research"){{currentResearchId=null;history.replaceState(null,"","/research")}}}}
document.querySelectorAll(".top-tab").forEach(b=>b.onclick=()=>showPage(b.dataset.page));
function applyOperatorState(){{const badge=document.getElementById("operatorStateBadge"),dot=document.getElementById("botDot");if(!state.operatorStateAvailable)return;const paused=state.operatorState==="TRADING_PAUSED";badge.textContent=paused?"Entries paused":"Entries enabled";badge.className="badge "+(paused?"pending":"opened");dot.style.background=paused?"#a16207":"#1b9a59";}}
function canSubmitOperatorAction(){{if(state.canSubmitOperatorControl)return true;alert("Operator command submission is unavailable in this rendered context.");return false;}}
function operatorBoundaryUnavailable(){{alert("Operator control boundary is unavailable in this rendered context.");}}
window.confirmPauseEntries=function(){{if(typeof window.openControlModal==="function")window.openControlModal("pause");else operatorBoundaryUnavailable();}};
window.confirmCloseAll=function(){{if(typeof window.openControlModal==="function")window.openControlModal("close");else operatorBoundaryUnavailable();}};
function closeOne(id,symbol){{if(typeof window.openSingleCloseById==="function")window.openSingleCloseById(id,symbol);else operatorBoundaryUnavailable();}}
window.openSheet=id=>document.getElementById(id).classList.add("show");window.backdrop=(e,id)=>{{if(e.target.id===id)document.getElementById(id).classList.remove("show")}};
function filters(){{return{{coin:filterCoin.value,side:filterSide.value,status:filterStatus.value,set:filterSet.value}}}}
function setSelect(id,items,label){{const node=document.getElementById(id);if(!node)return;node.innerHTML=`<option value="">${{label}}: All</option>`+[...new Set(items.filter(Boolean))].map(x=>`<option>${{html(x)}}</option>`).join("")}}
function normalizeOpen(r){{return{{time:r.opened_at,coin:r.symbol,side:r.side,status:"OPENED",qty:r.qty,value:r.value,entry:r.entry_price,current:r.current_price,takeProfit:r.take_profit_price,tpPct:r.take_profit_pct,stopLoss:r.stop_loss_price,slPct:r.stop_loss_pct,pnl:r.unrealized_pnl_amount,pnlPct:r.unrealized_pnl_pct,set:[r.set_id,r.set_version].filter(Boolean).join(" "),age:duration(r.age_seconds),reason:"—",action:r.close_action_available?"Close":"—",id:r.position_id}}}}
function normalizeClosed(r){{return{{time:r.closed_at,coin:r.symbol,side:r.side,status:"CLOSED",qty:r.qty,value:r.value,entry:r.entry_price,current:r.exit_price,takeProfit:r.planned_tp_price,tpPct:r.planned_tp_pct,stopLoss:r.planned_sl_price,slPct:r.planned_sl_pct,pnl:r.realized_pnl_amount,pnlPct:r.realized_pnl_pct,set:[r.set_id,r.set_version].filter(Boolean).join(" "),age:duration(r.duration_seconds),reason:r.close_reason||"—",action:"—",id:r.position_id}}}}
function allRows(){{const p=state.portfolio||{{}};return{{placed:[],open:(p.open_positions||[]).map(normalizeOpen),history:(p.closed_positions||[]).map(normalizeClosed)}}}}
function renderKpis(){{const s=(state.portfolio||{{}}).snapshot||{{}};const vals=[["Total Equity",money(s.total_equity)],["Available",money(s.available_capital)],["In Positions",money(s.in_positions)],["Realized P&L Today",signedMoney(s.realized_pnl_today),cls(s.realized_pnl_today)],["Unrealized P&L",signedMoney(s.unrealized_pnl),cls(s.unrealized_pnl)],["Open Positions",s.open_positions_count??"—"]];overviewKpis.innerHTML=vals.map(v=>`<div class="kpi"><div class="kpi-label">${{v[0]}}</div><div class="kpi-value ${{v[2]||""}}">${{v[1]}}</div></div>`).join("")}}
function inRange(row){{if(posView!=="history")return true; if(historyRange==="24H"){{const t=Date.parse(row.time);return Number.isNaN(t)||Date.now()-t<=86400000}} if(historyRange==="7D")return Date.now()-Date.parse(row.time)<=7*86400000; if(historyRange==="30D")return Date.now()-Date.parse(row.time)<=30*86400000; if(historyRange==="90D")return Date.now()-Date.parse(row.time)<=90*86400000; return true}}
function rowPass(row){{const f=filters();return(!f.coin||row.coin===f.coin)&&(!f.side||row.side===f.side)&&(!f.status||row.status===f.status)&&(!f.set||row.set.includes(f.set))&&inRange(row)}}
function bindPositionActions(){{document.querySelectorAll(".js-close-position").forEach(b=>b.onclick=ev=>{{ev.stopPropagation();closeOne(b.dataset.positionId||"",b.dataset.symbol||"")}});document.querySelectorAll(".mobile-card").forEach(card=>card.onclick=ev=>{{if(ev.target.closest("button"))return;card.classList.toggle("expanded")}})}}
function renderPositions(){{const rows=allRows()[posView].filter(rowPass);historyTools.classList.toggle("show",posView==="history");mobileHistoryNote.classList.toggle("show",posView==="history");positionsBody.innerHTML=rows.length?rows.map(r=>`<tr><td>${{html(r.time)}}</td><td>${{html(r.coin)}}</td><td>${{html(r.side)}}</td><td>${{statusBadge(r.status)}}</td><td>${{html(r.qty)}}</td><td>${{money(r.value)}}</td><td>${{html(r.entry)}}</td><td>${{html(r.current||"—")}}</td><td>${{html(r.takeProfit)}} <span class="${{cls(r.tpPct)}}">${{pct(r.tpPct)}}</span></td><td>${{html(r.stopLoss)}} <span class="${{cls(-Number(r.slPct||0))}}">${{pct(r.slPct)}}</span></td><td class="${{cls(r.pnl)}}">${{r.pnl==null?"—":signedMoney(r.pnl)}} <span>${{r.pnlPct==null?"":pct(r.pnlPct)}}</span></td><td>${{html(r.set)}}</td><td>${{html(r.age)}}</td><td>${{html(r.reason)}}</td><td>${{r.action==="Close"?`<button class="row-action danger js-close-position" data-position-id="${{html(r.id)}}" data-symbol="${{html(r.coin)}}">Close</button>`:"—"}}</td></tr>`).join(""):`<tr><td colspan="15" class="empty">No factual ${{posView}} records.</td></tr>`;
positionsCards.innerHTML=rows.length?rows.map(r=>`<article class="mobile-card"><div class="mobile-top"><div><b>${{html(r.coin)}}</b> <span class="neutral">${{html(r.side)}}</span></div>${{statusBadge(r.status)}}</div><div class="mobile-grid"><div><div class="fl">Entry</div><div class="fv">${{html(r.entry)}}</div></div><div><div class="fl">Current / Exit</div><div class="fv">${{html(r.current||"—")}}</div></div><div><div class="fl">TP</div><div class="fv">${{html(r.takeProfit)}} ${{pct(r.tpPct)}}</div></div><div><div class="fl">SL</div><div class="fv">${{html(r.stopLoss)}} ${{pct(r.slPct)}}</div></div><div><div class="fl">P&L</div><div class="fv ${{cls(r.pnl)}}">${{r.pnl==null?"—":signedMoney(r.pnl)}} ${{r.pnlPct==null?"":pct(r.pnlPct)}}</div></div><div><div class="fl">Set</div><div class="fv">${{html(r.set)}}</div></div></div><div class="mobile-card-details"><div><div class="fl">Time</div><div class="fv">${{html(r.time)}}</div></div><div><div class="fl">Quantity</div><div class="fv">${{html(r.qty)}}</div></div><div><div class="fl">Value</div><div class="fv">${{money(r.value)}}</div></div><div><div class="fl">Status</div><div class="fv">${{html(r.status)}}</div></div><div><div class="fl">Age</div><div class="fv">${{html(r.age)}}</div></div><div><div class="fl">Reason</div><div class="fv">${{html(r.reason)}}</div></div></div>${{r.action==="Close"?`<button class="row-action danger js-close-position" data-position-id="${{html(r.id)}}" data-symbol="${{html(r.coin)}}" style="width:100%;margin-top:10px">Close Position</button>`:""}}</article>`).join(""):`<div class="empty">No factual ${{posView}} records.</div>`;bindPositionActions()}}
document.querySelectorAll(".positions-tab").forEach(b=>b.onclick=()=>{{posView=b.dataset.pos;document.querySelectorAll(".positions-tab").forEach(x=>x.classList.toggle("active",x===b));renderPositions()}});
document.querySelectorAll(".range-btn").forEach(b=>b.onclick=()=>{{historyRange=b.dataset.range;document.querySelectorAll(".range-btn").forEach(x=>x.classList.toggle("active",x===b));renderPositions()}});
[filterCoin,filterSide,filterStatus,filterSet].forEach(x=>x.onchange=renderPositions);
window.exportHistory=()=>fetch("/api/system-history/export",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{}})}}).then(r=>r.json()).then(d=>{{const blob=new Blob([d.text||JSON.stringify(d,null,2)],{{type:"text/plain"}});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="triggertrade-history.txt";a.click();}});
window.applyMobileFilters=function(){{filterCoin.value=mFilterCoin.value;filterSide.value=mFilterSide.value;filterStatus.value=mFilterStatus.value;filterSet.value=mFilterSet.value;document.getElementById("filtersSheet").classList.remove("show");renderPositions()}};
window.resetMobileFilters=function(){{[mFilterCoin,mFilterSide,mFilterStatus,mFilterSet].forEach(x=>x.value="");applyMobileFilters()}};
function setupOverview(){{const rows=allRows();const coins=[...rows.open,...rows.history].map(r=>r.coin),sets=[...rows.open,...rows.history].map(r=>r.set);["filterCoin","mFilterCoin"].forEach(id=>setSelect(id,coins,"Coin"));["filterSet","mFilterSet"].forEach(id=>setSelect(id,sets,"Set"));renderKpis();renderPositions()}}
const metricCatalog=(state.metrics&&Array.isArray(state.metrics.metrics))?state.metrics.metrics:[];
function renderMetrics(){{metricsBody.innerHTML=metricCatalog.length?metricCatalog.map(m=>`<tr class="catalog-row js-metric-row" data-metric-id="${{html(m.id)}}"><td>${{html(m.id)}}</td><td>${{html(m.name)}}</td><td>${{html(String(m.id||"").split("-")[0])}}</td><td>${{html(m.type)}}</td><td>${{html(m.status)}}</td></tr>`).join(""):`<tr><td colspan="5" class="empty">Metrics Library unavailable.</td></tr>`;document.querySelectorAll(".js-metric-row").forEach(row=>row.onclick=()=>showMetric(row.dataset.metricId||""));if(metricCatalog[0])showMetric(metricCatalog[0].id)}};window.showMetric=id=>{{const m=metricCatalog.find(x=>x.id===id)||metricCatalog[0];if(!m)return;metricDetail.innerHTML=`<div class="details-header"><div class="details-id">${{html(m.id)}} · ${{html(m.status)}}</div><div class="details-title">${{html(m.name)}}</div></div><div class="details-section"><div class="body-text">${{html(m.what_it_is||"")}}</div></div><div class="details-section"><div class="panel-title">Formula / Rule</div><div class="formula">${{html(m.formula_or_rule||"")}}</div></div>`}};
function renderTriggers(){{const triggers=(state.registry.triggers||[]);triggersBody.innerHTML=triggers.length?triggers.map(t=>`<tr class="catalog-row js-trigger-row" data-trigger-id="${{html(t.trigger_id)}}" data-trigger-version="${{html(t.version)}}"><td>${{html(t.display_name||t.trigger_id)}}</td><td>${{html(t.version)}}</td><td>Versioned condition</td><td>${{html(t.what_it_checks)}}</td><td>${{html((state.registry.sets||[]).filter(s=>(s.trigger_versions||[]).some(v=>v.trigger_id===t.trigger_id&&v.version===t.version)).map(s=>s.set_id+" "+s.version).join(", ")||"—")}}</td><td>${{statusBadge(t.immutable?"Active":"Research")}}</td></tr>`).join(""):`<tr><td colspan="6" class="empty">No canonical Trigger versions available.</td></tr>`;document.querySelectorAll(".js-trigger-row").forEach(row=>row.onclick=()=>showTrigger(row.dataset.triggerId||"",row.dataset.triggerVersion||""));if(triggers[0])showTrigger(triggers[0].trigger_id,triggers[0].version)}};window.showTrigger=(id,version)=>{{let t=(state.registry.selected_trigger&&state.registry.selected_trigger.trigger_id===id&&state.registry.selected_trigger.version===version)?state.registry.selected_trigger:(state.registry.triggers||[]).find(x=>x.trigger_id===id&&x.version===version);const params=(t?.parameters||[]).map(p=>`${{p.name}} = ${{p.value}} (${{p.meaning}})`).join("\\n")||"—";const history=(t?.version_history||[]).map(v=>`${{v.version}} · ${{v.created_at}} · ${{v.change_summary}}`).join("\\n")||"—";triggerDetail.innerHTML=`<div class="details-header"><div class="details-id">${{html(id)}} · ${{html(version)}} · ${{t?.immutable?"CURRENT/HISTORICAL USED":"RESEARCH"}}</div><div class="details-title">${{html(t?.display_name||id)}}</div></div><div class="details-section"><div class="body-text">${{html(t?.how_it_works||t?.what_it_checks||"Trigger detail unavailable from backend.")}}</div></div><div class="details-section"><div class="panel-title">Condition</div><div class="formula">${{html(t?.formula_text||t?.what_it_checks||"—")}}</div></div><div class="details-section"><div class="panel-title">Parameters</div><div class="formula">${{html(params)}}</div></div><div class="details-section"><div class="panel-title">Set Versions Using It</div><div class="body-text">${{html((t?.used_in||[]).map(u=>`${{u.set_id||u.set_name}} ${{u.set_version}} ${{u.set_status||""}}`).join(", ")||"—")}}</div></div><div class="details-section"><div class="panel-title">Version History</div><div class="formula">${{html(history)}}</div></div>`}};
function renderSets(){{const sets=state.registry.sets||[];setsBody.innerHTML=sets.length?sets.map(s=>`<tr class="catalog-row js-set-row" data-set-id="${{html(s.set_id)}}" data-set-version="${{html(s.version)}}"><td>${{html(s.display_name||s.set_id)}}</td><td>${{html(s.version)}}</td><td>${{html([s.symbol,s.timeframe].filter(Boolean).join(" · ")||"—")}}</td><td>${{html((s.trigger_versions||[]).map(t=>t.trigger_id+" "+t.version).join(", "))}}</td><td>${{statusBadge(s.status)}}</td></tr>`).join(""):`<tr><td colspan="5" class="empty">No canonical Set versions available.</td></tr>`;document.querySelectorAll(".js-set-row").forEach(row=>row.onclick=()=>showSet(row.dataset.setId||"",row.dataset.setVersion||""));if(sets[0])showSet(sets[0].set_id,sets[0].version)}};window.showSet=(id,version)=>{{const s=(state.registry.sets||[]).find(x=>x.set_id===id&&x.version===version);const members=s?.trigger_versions||[];setDetail.innerHTML=`<div class="details-header"><div class="details-id">${{html(id)}} · ${{html(version)}} · ${{html(s?.status||"UNKNOWN")}}</div><div class="details-title">${{html(s?.display_name||id)}}</div></div><div class="details-section"><div class="set-logic"><div class="set-logic-row"><div class="logic-keyword">IF</div><div class="logic-condition">${{html(members.map(t=>t.trigger_id+" "+t.version+" evaluates TRUE").join(" AND ")||"no trigger membership recorded")}}</div></div><div class="set-logic-row"><div class="logic-keyword">THEN</div><div class="logic-condition">Emit the versioned Set signal for ${{html([s?.symbol,s?.timeframe].filter(Boolean).join(" / ")||"the configured market")}}; strategies convert this deterministic signal into trade intent.</div></div><div class="set-logic-row"><div class="logic-keyword">TRACE</div><div class="logic-condition">Status ${{html(s?.status||"UNKNOWN")}}; created ${{html(s?.created_at||"—")}}; active ${{html(s?.is_active?"yes":"no")}}.</div></div></div></div>`}};
document.querySelectorAll(".config-tab").forEach(b=>b.onclick=()=>{{configView=b.dataset.config;document.querySelectorAll(".config-tab").forEach(x=>x.classList.toggle("active",x.dataset.config===configView));document.querySelectorAll(".config-view").forEach(x=>x.classList.toggle("active",x.id==="config-"+configView));}});
let coinDraft=[], rulesDraftVersion=null;
function inputRule(id,value,type="text"){{return`<input id="${{id}}" type="${{type}}" value="${{html(value??"")}}">`}}
function field(id){{return document.getElementById(id)}}
function currentRulesPayload(){{const c=state.rules.current||{{}};return{{expected_rules_version_id:c.rules_version_id||"",expected_display_version:c.display_version||"",position_rules:{{position_size_pct:field("rulesPositionSize").value,take_profit_mode:field("rulesTpMode").value,fixed_take_profit_pct:field("rulesFixedTp").value,minimum_take_profit_pct:field("rulesMinTp").value,stop_loss_pct:field("rulesStopLoss").value,minimum_risk_reward:field("rulesRiskReward").value,minimum_net_edge_enabled:field("rulesEdgeEnabled").checked,minimum_net_edge_pct:field("rulesEdge").value,leverage:field("rulesLeverage").value}},portfolio_rules:{{max_capital_in_positions_pct:field("rulesMaxCapital").value,max_open_positions_enabled:field("rulesMaxOpenEnabled").checked,max_open_positions:field("rulesMaxOpen").value,max_positions_per_coin_enabled:field("rulesMaxCoinEnabled").checked,max_positions_per_coin:field("rulesMaxCoin").value,direction_mode:field("rulesDirection").value,daily_loss_limit_enabled:field("rulesDailyLossEnabled").checked,daily_loss_limit_pct:field("rulesDailyLoss").value}},coins:coinDraft.map(c=>({{symbol:c.symbol,enabled:c.enabled,max_allocation_pct:c.max_allocation_pct||null}}))}}}}
function bindRulesControls(){{document.querySelectorAll(".js-remove-coin").forEach(b=>b.onclick=()=>{{coinDraft=coinDraft.filter(c=>c.symbol!==b.dataset.symbol);renderRules(true)}});document.getElementById("rulesAddCoin")?.addEventListener("click",()=>{{const symbol=prompt("Coin symbol");if(!symbol)return;coinDraft.push({{symbol:String(symbol).trim().toUpperCase(),enabled:true,max_allocation_pct:null}});renderRules(true)}});document.getElementById("rulesSaveButton")?.addEventListener("click",saveRules)}}
async function saveRules(){{if(!canSubmitOperatorAction())return;const stateNode=document.getElementById("rulesSaveState");stateNode.textContent="Saving...";const res=await fetch("/api/rules/versions",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(currentRulesPayload())}});const data=await res.json();if(!res.ok){{stateNode.textContent=data.error||"Save failed";return}}state.rules.current=data.rules;state.rules.history=data.history||state.rules.history;stateNode.textContent=data.change_summary||"Saved";renderRules()}}
function renderRules(keepDraft=false){{const c=state.rules.current; if(!c){{rulesBody.innerHTML='<section class="panel"><div class="empty">Current Trading Rules version unavailable.</div></section>';return}}; const pr=c.position_rules||{{}},por=c.portfolio_rules||{{}};if(!keepDraft||rulesDraftVersion!==c.rules_version_id){{coinDraft=(c.coins||[]).map(x=>({{symbol:x.symbol,enabled:x.enabled,max_allocation_pct:x.max_allocation_pct}}));rulesDraftVersion=c.rules_version_id}} const row=(n,id,v,d="",type="text")=>`<div class="rule-row"><div><div class="rule-name">${{n}}</div><div class="rule-description">${{d}}</div></div><div>${{inputRule(id,v,type)}}</div></div>`;rulesBody.innerHTML=`<section class="rules-section"><div class="rules-section-title">Position Rules</div>${{row("Position Size", "rulesPositionSize", pr.position_size_pct,"%")}}<div class="rule-row"><div><div class="rule-name">Take Profit mode</div><div class="rule-description">Dynamic TP remains backend fail-closed where unsupported.</div></div><select id="rulesTpMode"><option ${{pr.take_profit_mode==="FIXED"?"selected":""}}>FIXED</option><option ${{pr.take_profit_mode==="DYNAMIC"?"selected":""}}>DYNAMIC</option></select></div>${{row("Fixed TP", "rulesFixedTp", pr.fixed_take_profit_pct,"%")}}${{row("Minimum TP", "rulesMinTp", pr.minimum_take_profit_pct,"%")}}${{row("Stop Loss", "rulesStopLoss", pr.stop_loss_pct,"%")}}${{row("Minimum Risk / Reward", "rulesRiskReward", pr.minimum_risk_reward)}}<div class="rule-row"><div><div class="rule-name">Minimum Net Edge</div><div class="rule-description">Disabled thresholds are preserved by explicit enabled flag.</div></div><div><label><input id="rulesEdgeEnabled" type="checkbox" ${{pr.minimum_net_edge_enabled?"checked":""}}> Enabled</label>${{inputRule("rulesEdge",pr.minimum_net_edge_pct)}}</div></div>${{row("Leverage", "rulesLeverage", pr.leverage)}}</section><section class="rules-section"><div class="rules-section-title">Portfolio Rules</div>${{row("Max Capital in Positions", "rulesMaxCapital", por.max_capital_in_positions_pct,"%")}}<div class="rule-row"><div><div class="rule-name">Max Open Positions</div></div><div><label><input id="rulesMaxOpenEnabled" type="checkbox" ${{por.max_open_positions_enabled?"checked":""}}> Enabled</label>${{inputRule("rulesMaxOpen",por.max_open_positions)}}</div></div><div class="rule-row"><div><div class="rule-name">Max Positions per Coin</div></div><div><label><input id="rulesMaxCoinEnabled" type="checkbox" ${{por.max_positions_per_coin_enabled?"checked":""}}> Enabled</label>${{inputRule("rulesMaxCoin",por.max_positions_per_coin)}}</div></div><div class="rule-row"><div><div class="rule-name">Direction</div><div class="rule-description">Direction filters do not create SHORT alpha.</div></div><select id="rulesDirection"><option ${{por.direction_mode==="LONG_ONLY"?"selected":""}}>LONG_ONLY</option><option ${{por.direction_mode==="SHORT_ONLY"?"selected":""}}>SHORT_ONLY</option><option ${{por.direction_mode==="LONG_SHORT"?"selected":""}}>LONG_SHORT</option></select></div><div class="rule-row"><div><div class="rule-name">Daily Loss Limit</div></div><div><label><input id="rulesDailyLossEnabled" type="checkbox" ${{por.daily_loss_limit_enabled?"checked":""}}> Enabled</label>${{inputRule("rulesDailyLoss",por.daily_loss_limit_pct)}}</div></div></section><section class="rules-section"><div class="rules-section-title">Coins</div><div class="coins-grid">${{coinDraft.map(c=>`<span class="coin-chip">${{html(c.symbol)}}<span>${{html(c.max_allocation_pct||"—")}}%</span><button class="row-action js-remove-coin" data-symbol="${{html(c.symbol)}}">Remove</button></span>`).join("")||'<span class="empty">No coins enabled.</span>'}}</div><div style="padding:12px 14px;display:flex;justify-content:flex-end;gap:7px"><button class="btn" id="rulesAddCoin">Add Coin</button><button class="btn primary" id="rulesSaveButton">Save as New Version</button><span class="panel-meta" id="rulesSaveState">No unsaved changes</span></div></section><section class="rules-section"><div class="rules-section-title">Version History</div><div class="table-wrap"><table><tbody>${{(state.rules.history||[]).map(h=>`<tr><td>${{html(h.display_version)}}</td><td>${{html(h.rules_version_id)}}</td><td>${{html(h.change_summary)}}</td></tr>`).join("")}}</tbody></table></div></section>`;bindRulesControls()}}
function decimalOrNull(v){{const n=Number(v);return Number.isFinite(n)?n:null}}
function fmtDelta(v){{const n=decimalOrNull(v);return n==null?"—":(n>0?"+":"")+n.toFixed(2)}}
function renderResearchSummary(){{const rows=state.research.summaries||[];researchBody.innerHTML=rows.length?rows.map(r=>{{const demo=r.selected_demo_run_id?(r.selected_demo_profit_factor?"Complete":"Running"):"Pending";const demoPf=r.selected_demo_profit_factor??"—",active=r.compare_to_active&&r.compare_to_active!=="Unavailable"?r.compare_to_active:"—";const delta=(decimalOrNull(demoPf)!=null&&decimalOrNull(active)!=null)?fmtDelta(decimalOrNull(demoPf)-decimalOrNull(active)):"—";return`<tr class="research-row js-research-row" data-research-id="${{html(r.research_id)}}"><td><b>${{html(r.research_id)}}</b></td><td>${{html(r.set_id)}}<div class="panel-meta">${{html(r.set_version)}}</div></td><td>${{html(r.rules_display_version)}}<div class="panel-meta">${{html(r.rules_version_id)}}</div></td><td>${{html(demo)}}</td><td>${{html(demoPf)}}</td><td>${{html(active)}}</td><td class="${{cls(delta)}}">${{html(delta)}}</td><td>${{statusBadge(r.decision||"NONE")}}</td></tr>`}}).join(""):`<tr><td colspan="8" class="empty">No Research records.</td></tr>`;document.querySelectorAll(".js-research-row").forEach(row=>row.onclick=()=>openResearchById(row.dataset.researchId||""))}}
window.openResearchById=async id=>{{currentResearchId=id;history.pushState(null,"",`/research/${{encodeURIComponent(id)}}`);showPage("research-detail");const res=await fetch(`/api/research/${{encodeURIComponent(id)}}`);currentResearch=await res.json();renderResearchDetail();await loadCompare()}};
function runRow(r,kind){{const m=r.metrics||{{}};const result=r.status==="RUNNING"?`Running · ${{r.progress_days||0}} / 7`:r.status==="STOPPED"?"Complete":(r.status||"—");return`<tr><td>${{html(r.run_id||r.backtest_run_id)}}</td><td>${{html((r.period_start||r.started_at||"—")+" -> "+(r.period_end||r.stopped_at||"—"))}}</td><td>${{html(m.closed_trades??"—")}}</td><td>${{html(m.net_pnl??"—")}}</td><td>${{html(m.profit_factor??"—")}}</td><td>${{html(result)}}</td></tr>`}}
function renderResearchDetail(){{const r=currentResearch.research||{{}};researchTitle.textContent=`${{r.research_id||currentResearchId}} · ${{r.set_id||"—"}} ${{r.set_version||""}} · Rules ${{r.rules_display_version||r.rules_version_id||"—"}}`;backtestBody.innerHTML=(currentResearch.backtests||[]).map(x=>runRow(x,"backtest")).join("")||'<tr><td colspan="6" class="empty">No Backtest runs.</td></tr>';demoBody.innerHTML=(currentResearch.demos||[]).map(x=>runRow(x,"demo")).join("")||'<tr><td colspan="6" class="empty">No Demo runs.</td></tr>';wfBacktest.classList.toggle("done",(currentResearch.backtests||[]).length>0);wfBacktestState.textContent=(currentResearch.backtests||[]).length?"Complete":"Pending";const demo=(currentResearch.demos||[])[0];const prog=Number(demo?.progress_days||0);wfDemo.classList.toggle("done",demo&&String(demo.status)==="STOPPED");wfDemoState.textContent=demo?(String(demo.status)==="RUNNING"?`Running · ${{prog}} / 7`:"Complete"):"Pending";demoSegments.innerHTML=Array.from({{length:7}},(_,i)=>`<div class="demo-segment ${{i<prog?"filled":""}}"></div>`).join("");wfDecision.classList.toggle("done",r.decision&&r.decision!=="NONE");wfDecision.classList.toggle("reject-done",r.decision==="REJECT");wfDecisionState.textContent=r.decision||"NONE";decisionStateInline.textContent=r.decision||"NONE"}}
async function loadCompare(){{if(!currentResearchId)return;const res=await fetch(`/api/research/${{encodeURIComponent(currentResearchId)}}/compare`);currentCompare=await res.json();wfCompare.classList.toggle("done",!!currentCompare.available);wfCompareState.textContent=currentCompare.available?"Complete":"Pending";renderCompare()}}
const metrics=["Net Realized P/L","Trades","Win Rate","Expectancy","Profit Factor","Max Drawdown","Avg Winner","Avg Loser","Fill Rate","MAE","MFE"];
function compareValue(source,label){{const map={{"Net Realized P/L":"net_pnl","Trades":"closed_trades","Win Rate":"win_rate","Expectancy":"expectancy","Profit Factor":"profit_factor","Max Drawdown":"max_drawdown","Fees":"fees","Funding":"funding"}};const key=map[label];if(!source||!key)return"—";return source[key]??"—"}}
function renderCompare(){{const cols=comparePeriod==="7D"?["Active","Demo","Backtest"]:["Active","Backtest"];if(compareScope!=="overall"){{compareTable.innerHTML='<tbody><tr><td class="empty">Segment, coin, and direction compare are unavailable until backend exposes factual segmented comparisons.</td></tr></tbody>';return}}compareTable.innerHTML=`<thead><tr><th>Metric</th>${{cols.map(c=>`<th>${{c}}</th>`).join("")}}</tr></thead><tbody>${{metrics.map(m=>`<tr><td>${{m}}</td>${{cols.map(c=>{{const source=c==="Active"?currentCompare?.active_benchmark:c==="Demo"?currentCompare?.research_demo:null;return`<td class="${{c==="Active"?"base-cell":"neutral-cell"}}">${{html(compareValue(source,m))}}</td>`}}).join("")}}</tr>`).join("")}}</tbody>`}}
document.querySelectorAll(".compare-tab").forEach(b=>b.onclick=()=>{{compareScope=b.dataset.scope;document.querySelectorAll(".compare-tab").forEach(x=>x.classList.toggle("active",x===b));renderCompare()}});
document.querySelectorAll(".compare-period").forEach(b=>b.onclick=()=>{{comparePeriod=b.dataset.period;document.querySelectorAll(".compare-period").forEach(x=>x.classList.toggle("active",x===b));renderCompare()}});
function windowFor(days){{const end=new Date(),start=new Date(end.getTime()-days*86400000);return{{research_start:start.toISOString(),research_end:end.toISOString()}}}}
window.runBacktest=async p=>{{const days=p==="7D"?7:p==="30D"?30:90;await fetch(`/api/research/${{encodeURIComponent(currentResearchId)}}/backtests`,{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(windowFor(days))}});await openResearchById(currentResearchId)}};
window.runDemo=async()=>{{await fetch(`/api/research/${{encodeURIComponent(currentResearchId)}}/demo/start`,{{method:"POST",headers:{{"Content-Type":"application/json"}},body:"{{}}"}});await openResearchById(currentResearchId)}};
window.setDecision=async what=>{{if(!canSubmitOperatorAction())return;if(what==="reject"){{if(!confirm("Archive this Research configuration?"))return;await fetch(`/api/research/${{encodeURIComponent(currentResearchId)}}/archive`,{{method:"POST",headers:{{"Content-Type":"application/json"}},body:"{{}}"}});await openResearchById(currentResearchId);return}}if(!confirm("Make this Research configuration Active?"))return;const url=`/api/research/${{encodeURIComponent(currentResearchId)}}/decision/make-active`;await fetch(url,{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{idempotency_key:"ui-"+Date.now()}})}});await openResearchById(currentResearchId)}};
window.exportResearch=()=>{{const blob=new Blob([JSON.stringify({{research:currentResearch,compare:currentCompare}},null,2)],{{type:"application/json"}});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=`${{currentResearchId||"research"}}.json`;a.click();}};
window.openNewResearch=()=>{{newResearchModal.classList.add("show")}};window.closeNewResearch=()=>newResearchModal.classList.remove("show");
function setupNewResearch(){{newResearchSet.innerHTML=(state.registry.sets||[]).map(s=>`<option value="${{html(s.set_id+"|"+s.version)}}">${{html(s.set_id+" "+s.version+" · "+s.status)}}</option>`).join("");const versions=[state.rules.current,...(state.rules.history||[])].filter(Boolean);newResearchRules.innerHTML=versions.map(r=>`<option value="${{html(r.rules_version_id)}}">${{html((r.display_version||"Rules")+" · "+r.rules_version_id)}}</option>`).join("")}}
window.createResearch=async()=>{{const [set_id,set_version]=newResearchSet.value.split("|"),rules_version_id=newResearchRules.value;const res=await fetch("/api/research",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{set_id,set_version,rules_version_id}})}});const data=await res.json();if(!res.ok){{newResearchState.textContent=data.error||"Research creation failed";return}}closeNewResearch();await openResearchById(data.research.research_id)}};
function boot(){{applyOperatorState();setupOverview();renderMetrics();renderTriggers();renderSets();renderRules();renderResearchSummary();setupNewResearch();showPage(page);if(page==="research-detail"){{const path=location.pathname.split("/").filter(Boolean);if(path[0]==="research"&&path[1])openResearchById(decodeURIComponent(path[1]));}}}}
boot();
}})();
</script>
</body>
</html>"""


def _reference_body(html_source: str) -> str:
    match = re.search(r"<body[^>]*>(.*)</body>", html_source, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else html_source


def _reference_head(html_source: str) -> str:
    match = re.search(r"<head[^>]*>(.*)</head>", html_source, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else ""


def _without_reference_scripts(body: str) -> str:
    return re.sub(r"<script\b[^>]*>.*?</script>", "", body, flags=re.IGNORECASE | re.DOTALL)


def _neutral_research_detail_placeholders(body: str) -> str:
    """Remove prototype Research detail values from the final server-composed DOM."""

    replacements = {
        "R-022 · SET-012 V2 · Rules V14": "Research",
        "SET-012": "SET unavailable",
        "Running · 4 / 7": "NOT STARTED",
    }
    for old, new in replacements.items():
        body = body.replace(old, new)
    body = re.sub(
        r'(id="workflow-backtest"\s+class="workflow-step)\s+done(")',
        r"\1\2",
        body,
        flags=re.IGNORECASE,
    )
    body = re.sub(
        r'(id="workflow-backtest-state"\s+class="workflow-state"\s*>\s*)Complete(\s*</div>)',
        r"\1NOT STARTED\2",
        body,
        flags=re.IGNORECASE,
    )
    return body


def _reference_styles(html_source: str) -> str:
    return "\n".join(re.findall(r"<style\b[^>]*>.*?</style>", html_source, flags=re.IGNORECASE | re.DOTALL))


def _scoped_mobile_reference_styles(html_source: str) -> str:
    styles = re.findall(r"<style\b[^>]*>(.*?)</style>", html_source, flags=re.IGNORECASE | re.DOTALL)
    if not styles:
        return ""

    def scope_selector(selector: str) -> str:
        selector = selector.strip()
        if selector in {":root", "body"}:
            return "#tt-mobile-reference"
        if selector == "*":
            return "#tt-mobile-reference *"
        return "#tt-mobile-reference " + selector

    scoped_rules: list[str] = []
    for style in styles:
        for chunk in style.split("}"):
            if "{" not in chunk:
                continue
            selectors, declarations = chunk.split("{", 1)
            scoped = ",".join(scope_selector(selector) for selector in selectors.split(",") if selector.strip())
            if scoped:
                scoped_rules.append(scoped + "{" + declarations + "}")
    return "<style id=\"triggertrade-mobile-reference-css\">\n@media(max-width:760px){\n" + "\n".join(scoped_rules) + "\n}\n</style>"


def _reference_backend_script(payload: str) -> str:
    script = r"""
<script id="triggertrade-reference-backend-wiring">
(function(){
  const state = __STATE__;
  const desktop = document.getElementById("tt-desktop-reference");
  const mobile = document.getElementById("tt-mobile-reference");
  const pageMap = {overview:"overview",config:"configuration",research:"research","research-detail":"research"};
  let posView = "placed", historyRange = "24H", currentResearchId = null, currentResearch = null, currentCompare = null;
  let compareScope = "overall", comparePeriod = "7D";
  let coinDraftVersion = null, coinDraft = [];
  let coinSearchOpen = false, coinSearchQuery = "", coinSearchIndex = 0, coinSearchError = "";
  const h = (v) => String(v ?? "—").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const money = (v) => v === null || v === undefined || v === "" ? "—" : "$" + String(v);
  const count = (v) => v === null || v === undefined ? "—" : String(v);
  const num = (v) => { const n = Number(v); return Number.isFinite(n) ? n : null; };
  const signedMoney = (v) => { const n = num(v); if(n === null) return "—"; return (n >= 0 ? "+$" : "-$") + Math.abs(n).toFixed(2); };
  const pct = (v) => { const n = num(v); if(n === null) return "—"; return (n >= 0 ? "+" : "-") + Math.abs(n).toFixed(2) + "%"; };
  const pnlClass = (v) => String(v ?? "").startsWith("-") ? "negative" : (num(v) > 0 || String(v ?? "").startsWith("+") ? "positive" : "neutral");
  const dur = (s) => { const n = Number(s); if(!Number.isFinite(n)) return "—"; if(n < 3600) return Math.floor(n / 60) + "m"; return Math.floor(n / 3600) + "h " + Math.floor((n % 3600) / 60) + "m"; };
  const badge = (v) => `<span class="badge ${String(v||"").toLowerCase().replace(/[^a-z0-9]+/g,"-") || "none"}">${h(v || "NONE")}</span>`;
  const sideBadge = (v) => badge(v || "—");
  const q = (sel, root=document) => root.querySelector(sel);
  const qa = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  function canSubmit(){ return !!state.canSubmitOperatorControl; }
  function researchRegistryUnavailable(){ return !!(state.research && state.research.unavailable_reason); }
  function commandUnavailableMessage(){ return "Operator command submission is unavailable."; }
  function commandHeaders(contentType){
    const headers = {"Content-Type": contentType};
    if(state.localDevOperatorControls){
      headers["X-TriggerTrade-Local-Operator"] = "1";
    }
    return headers;
  }
  function commandIdempotencyKey(prefix){
    return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }
  async function postJson(url, body){
    const response = await fetch(url, {method:"POST", credentials:"same-origin", headers:commandHeaders("application/json"), body:JSON.stringify(body || {})});
    const data = await response.json().catch(() => ({}));
    if(!response.ok) throw new Error(data.error || data.reason || "Request failed");
    return data;
  }
  function applyCommandAvailability(){
    const commandUnavailable = !canSubmit();
    qa(".stop-new, .close-all, .row-close, button[onclick*=\"confirmPauseEntries\"], button[onclick*=\"confirmCloseAll\"], button[onclick*=\"action('pause')\"], button[onclick*=\"action('close')\"]", document).forEach(node => {
      node.disabled = commandUnavailable;
      node.setAttribute("aria-disabled", commandUnavailable ? "true" : "false");
      if(commandUnavailable) node.title = commandUnavailableMessage();
    });
    qa('button[onclick^="runBacktest"], button[onclick="runDemo()"], button[onclick^="setDecision"], button[onclick="openNewResearch()"]', desktop).forEach(node => {
      const unavailable = commandUnavailable || researchRegistryUnavailable();
      node.disabled = unavailable;
      node.setAttribute("aria-disabled", unavailable ? "true" : "false");
      if(unavailable) node.title = researchRegistryUnavailable() ? state.research.unavailable_reason : commandUnavailableMessage();
    });
  }
  function normalizeCoinAllocation(v){
    if(v === null || v === undefined) return "";
    return String(v).replace("%", "").trim();
  }
  function coinPayload(){
    return coinDraft.map(c => ({
      symbol: c.symbol,
      enabled: c.enabled !== false,
      max_allocation_pct: normalizeCoinAllocation(c.max_allocation_pct)
    }));
  }
  function catalogSymbols(){
    return (state.rules.coins || state.rules.catalog_coins || state.rules.supported_symbols || []).map(c => String(c.symbol || c).trim().toUpperCase()).filter(Boolean);
  }
  function availableCoinSymbols(){
    const existing = new Set(coinDraft.map(c => c.symbol));
    return catalogSymbols().filter(symbol => !existing.has(symbol));
  }
  function matchingCoinSymbols(){
    const q = coinSearchQuery.trim().toUpperCase();
    const symbols = availableCoinSymbols();
    return q ? symbols.filter(symbol => symbol.includes(q)) : symbols;
  }
  function resetCoinSearch(){
    coinSearchOpen = false;
    coinSearchQuery = "";
    coinSearchIndex = 0;
    coinSearchError = "";
  }
  function addCoinSymbol(symbol){
    const clean = String(symbol || "").trim().toUpperCase();
    const symbols = catalogSymbols();
    if(!symbols.length){ coinSearchError = "Supported instrument catalog is unavailable."; updateCoinSearchResults(); return false; }
    if(!symbols.includes(clean)){ coinSearchError = "Symbol is not available in the supported instrument catalog."; updateCoinSearchResults(); return false; }
    if(coinDraft.some(c => c.symbol === clean)){ coinSearchError = "Coin is already included."; updateCoinSearchResults(); return false; }
    coinDraft = [...coinDraft, {symbol: clean, enabled:true, max_allocation_pct:""}];
    resetCoinSearch();
    renderRules();
    return true;
  }
  function coinSearchResultsHtml(){
    const matches = matchingCoinSymbols();
    const active = Math.min(coinSearchIndex, Math.max(matches.length - 1, 0));
    return `<div class="coin-search-options">${matches.slice(0, 8).map((symbol, index) => `<button class="coin-search-option ${index === active ? "active" : ""}" type="button" data-symbol="${h(symbol)}">${h(symbol)}</button>`).join("") || '<div class="coin-search-empty">No matching supported symbols.</div>'}</div>${coinSearchError ? `<div class="coin-search-error">${h(coinSearchError)}</div>` : ""}`;
  }
  function bindCoinSearchOptions(scope){
    qa(".coin-search-option", scope || desktop).forEach(button => button.addEventListener("click", () => addCoinSymbol(button.dataset.symbol)));
  }
  function updateCoinSearchResults(){
    const box = q("#config-rules .coin-combobox", desktop);
    if(!box) return;
    box.querySelectorAll(".coin-search-options,.coin-search-empty,.coin-search-error").forEach(node => node.remove());
    q(".coin-search-input", box)?.insertAdjacentHTML("afterend", coinSearchResultsHtml());
    bindCoinSearchOptions(box);
  }
  function researchSetOptions(){
    return (state.registry.sets || []).map(s => ({
      set_id: String(s.set_id || "").trim(),
      set_version: String(s.version || s.set_version || "").trim(),
      label: [s.display_name || s.set_id, s.version || s.set_version].filter(Boolean).join(" ")
    })).filter(s => s.set_id && s.set_version);
  }
  function researchRulesOptions(){
    const seen = new Set();
    return [state.rules.current, ...(state.rules.history || [])].filter(Boolean).map(r => ({
      rules_version_id: String(r.rules_version_id || "").trim(),
      label: [r.display_version, r.rules_version_id].filter(Boolean).join(" · ")
    })).filter(r => r.rules_version_id && !seen.has(r.rules_version_id) && seen.add(r.rules_version_id));
  }
  function setStatusLabel(value){
    const text = String(value || "UNKNOWN").toUpperCase();
    if(text === "ACTIVE") return "Active";
    if(text === "TESTING" || text === "DRAFT" || text === "RESEARCH") return "Research";
    if(text === "ARCHIVE" || text === "ARCHIVED" || text === "INACTIVE") return "Inactive";
    return text;
  }
  function triggerStatusLabel(trigger){
    return trigger?.immutable ? "Active" : "Research";
  }
  function operatorStatusNode(){
    let node = q("#operatorCommandStatus", desktop);
    if(!node){
      node = document.createElement("div");
      node.id = "operatorCommandStatus";
      node.className = "panel-meta";
      node.style.minWidth = "180px";
      const mobileActive = window.matchMedia && window.matchMedia("(max-width:760px)").matches;
      const actions = mobileActive ? q(".panel-head", mobile) : q(".positions-actions", desktop);
      if(actions) actions.appendChild(node);
    }
    return node;
  }
  function setOperatorStatus(message, tone="neutral"){
    const node = operatorStatusNode();
    if(!node) return;
    node.innerHTML = h(message || "");
    node.className = "panel-meta " + tone;
  }
  function publicFormError(text){
    return String(text || "Command failed").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim().slice(0, 180) || "Command failed";
  }
  function requestOperatorConfirmation(message, submit){
    const node = operatorStatusNode();
    if(!node) return;
    node.className = "panel-meta";
    node.innerHTML = `${h(message)} <button class="row-action js-confirm-operator-command" type="button">Confirm</button> <button class="row-action js-cancel-operator-command" type="button">Cancel</button>`;
    q(".js-confirm-operator-command", node)?.addEventListener("click", submit);
    q(".js-cancel-operator-command", node)?.addEventListener("click", () => setOperatorStatus("Cancelled."));
  }
  async function submitOperatorForm(id, fill, successMessage, afterSuccess){
    const form = document.getElementById(id);
    if(!canSubmit()){ setOperatorStatus(commandUnavailableMessage(), "negative"); return false; }
    if(!form){ setOperatorStatus("Operator command form is unavailable.", "negative"); return false; }
    if(fill) fill(form);
    const key = form.querySelector('[name="idempotency_key"]');
    if(key) key.value = `${id}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const body = new URLSearchParams(new FormData(form));
    setOperatorStatus("Submitting...", "neutral");
    try{
      const response = await fetch(form.action, {method:"POST", credentials:"same-origin", headers:commandHeaders("application/x-www-form-urlencoded"), body});
      const text = await response.text();
      if(!response.ok) throw new Error(publicFormError(text));
      if(afterSuccess) afterSuccess();
      setOperatorStatus(successMessage || "Command submitted.", "positive");
      return true;
    }catch(error){
      setOperatorStatus(error.message || "Command failed.", "negative");
      return false;
    }
  }
  window.confirmPauseEntries = function(){
    if(!canSubmit()){ setOperatorStatus(commandUnavailableMessage(), "negative"); return; }
    if(typeof window.openControlModal === "function"){
      window.openControlModal("pause");
      return;
    }
    setOperatorStatus("Operator control boundary is unavailable.", "negative");
  };
  window.confirmCloseAll = function(){
    if(!canSubmit()){ setOperatorStatus(commandUnavailableMessage(), "negative"); return; }
    if(typeof window.openControlModal === "function"){
      window.openControlModal("close");
      return;
    }
    setOperatorStatus("Operator control boundary is unavailable.", "negative");
  };
  window.closePosition = function(id, symbol){
    if(!canSubmit()){ setOperatorStatus(commandUnavailableMessage(), "negative"); return; }
    if(typeof window.openSingleCloseById === "function"){
      window.openSingleCloseById(id, symbol);
      return;
    }
    setOperatorStatus("Operator control boundary is unavailable.", "negative");
  };
  document.addEventListener("click", (event) => {
    const button = event.target.closest(".js-close-position");
    if(!button) return;
    event.stopPropagation();
    closePosition(button.dataset.positionId || "", button.dataset.symbol || "");
  });
  document.addEventListener("click", (event) => {
    const triggerButton = event.target.closest(".js-open-trigger");
    if(triggerButton){
      event.stopPropagation();
      openConfig("triggers");
      window.showTrigger(triggerButton.dataset.triggerId || "", triggerButton.dataset.triggerVersion || "");
      return;
    }
    const setButton = event.target.closest(".js-open-set");
    if(setButton){
      event.stopPropagation();
      openConfig("sets");
      window.showSet(setButton.dataset.setId || "", setButton.dataset.setVersion || "");
    }
  });

  function researchIdFromLocation(){
    const parts = location.pathname.split("/").filter(Boolean);
    return parts[0] === "research" && parts[1] ? decodeURIComponent(parts[1]) : "";
  }
  function showPage(page, options={}){
    const normalized = page === "config" ? "configuration" : page;
    const pageId = normalized === "research-detail" ? "page-research-detail" : "page-" + normalized;
    const activeTab = normalized === "research-detail" ? "research" : normalized;
    qa(".page", desktop).forEach(node => node.classList.toggle("active", node.id === pageId));
    qa(".top-tab", desktop).forEach(node => node.classList.toggle("active", node.dataset.page === activeTab));
    if(normalized !== "overview") document.body.classList.remove("tt-mobile-overview-active");
    else document.body.classList.add("tt-mobile-overview-active");
    if(!options.preserveUrl){
      history.replaceState(null, "", normalized === "overview" ? "/overview" : normalized === "configuration" ? "/trading-configuration" : normalized === "research-detail" && currentResearchId ? "/research/" + encodeURIComponent(currentResearchId) : "/" + normalized);
    }
  }
  window.openPage = showPage;
  window.openConfig = function(view){
    showPage("configuration");
    qa(".config-tab", desktop).forEach(node => node.classList.toggle("active", node.dataset.config === view));
    qa(".config-view", desktop).forEach(node => node.classList.toggle("active", node.id === "config-" + view));
  };
  qa(".top-tab", desktop).forEach(node => node.addEventListener("click", () => showPage(node.dataset.page)));
  qa(".nav button", mobile).forEach(node => node.addEventListener("click", () => showPage(pageMap[node.textContent.trim().toLowerCase()] || "overview")));

  function applyOperatorState(){
    const paused = state.operatorState === "TRADING_PAUSED";
    const label = !state.operatorStateAvailable ? "State unavailable" : paused ? "Entries paused" : "Entries enabled";
    qa("#operatorStateBadge").forEach(node => { node.textContent = label; node.className = "badge " + (!state.operatorStateAvailable ? "closed" : paused ? "pending" : "active"); });
    qa("#botDot,.brand-dot").forEach(node => { node.style.background = paused ? "#9a6700" : state.operatorStateAvailable ? "#16824b" : "#98a2b3"; });
    qa(".btn.warning").forEach(node => { if(node.textContent.includes("Pause") || node.textContent.includes("Resume")) node.textContent = paused ? "Resume Entries" : "Pause Entries"; });
  }

  function setupKpis(){
    const snap = state.portfolio.snapshot || {};
    const desktopValues = [
      ["Total Equity", money(snap.total_equity)],
      ["Available", money(snap.available_capital)],
      ["In Positions", money(snap.in_positions)],
      ["Realized P&L Today", signedMoney(snap.realized_pnl_today)],
      ["Unrealized P&L", signedMoney(snap.unrealized_pnl)],
      ["Open Positions", count(snap.open_positions_count)]
    ];
    const mobileValues = [
      ["Total Equity", money(snap.total_equity)],
      ["Available", money(snap.available_capital)],
      ["Realized P&L Today", signedMoney(snap.realized_pnl_today)],
      ["Unrealized P&L", signedMoney(snap.unrealized_pnl)],
      ["In Positions", money(snap.in_positions)],
      ["Open Positions", count(snap.open_positions_count)]
    ];
    const desktopGrid = q(".overview-kpis", desktop);
    if(desktopGrid){
      desktopGrid.innerHTML = desktopValues.map(([label, value]) => `<div class="kpi"><div class="kpi-label">${h(label)}</div><div class="kpi-value ${pnlClass(value)}">${h(value)}</div></div>`).join("");
    }
    qa(".kpi", mobile).forEach((node, index) => {
      const pair = mobileValues[index] || ["", "—"];
      const value = q(".value", node);
      if(value){ value.textContent = pair[1]; value.classList.toggle("good", String(pair[1]).startsWith("+")); value.classList.toggle("bad", String(pair[1]).startsWith("-")); }
    });
  }

  function positionRows(){
    const open = (state.portfolio.open_positions || []).map(r => ({kind:"open", time:r.opened_at || "—", coin:r.symbol, side:r.side, status:"OPENED", qty:[r.qty,r.qty_unit].filter(Boolean).join(" "), value:r.value, entry:r.entry_price, current:r.current_price, tp:[pct(r.take_profit_pct),money(r.take_profit_price)].join(" · "), sl:[pct(r.stop_loss_pct),money(r.stop_loss_price)].join(" · "), pnl:[pct(r.unrealized_pnl_pct),signedMoney(r.unrealized_pnl_amount)].join(" · "), set:r.set_version || "legacy/unknown", age:dur(r.age_seconds), reason:"—", id:r.position_id}));
    const history = (state.portfolio.closed_positions || []).map(r => ({kind:"history", time:r.closed_at || "—", coin:r.symbol, side:r.side, status:"CLOSED", qty:[r.qty,r.qty_unit].filter(Boolean).join(" "), value:r.value, entry:r.entry_price, current:r.exit_price, tp:[pct(r.planned_tp_pct),money(r.planned_tp_price)].join(" · "), sl:[pct(r.planned_sl_pct),money(r.planned_sl_price)].join(" · "), pnl:[pct(r.realized_pnl_pct),signedMoney(r.realized_pnl_amount)].join(" · "), set:r.set_version || "legacy/unknown", age:dur(r.duration_seconds), reason:String(r.close_reason || "—").replace(/_/g," "), id:r.position_id}));
    return {placed: [], open, history};
  }
  function selected(root, id){
    const raw = q("#" + id, root)?.value || "";
    return String(raw).replace(/^[^:]+:\s*/, "");
  }
  function historyRangeMillis(){
    return ({ "24H": 1, "7D": 7, "30D": 30, "90D": 90 }[historyRange] || 1) * 24 * 60 * 60 * 1000;
  }
  function applyHistoryRange(rows){
    if(posView !== "history") return rows;
    const cutoff = Date.now() - historyRangeMillis();
    return rows.filter(row => {
      const ts = Date.parse(row.time || "");
      return Number.isNaN(ts) || ts >= cutoff;
    });
  }
  function filtered(rows, root){
    const coin = selected(root, root === mobile ? "fcoin" : "filter-coin");
    const side = selected(root, root === mobile ? "fside" : "filter-side");
    const status = selected(root, root === mobile ? "fstatus" : "filter-status");
    const set = selected(root, root === mobile ? "fset" : "filter-set");
    return rows.filter(r => (!coin || coin === "All" || r.coin === coin) && (!side || side === "All" || r.side === side) && (!status || status === "All" || r.status === status) && (!set || set === "All" || r.set === set));
  }
  function setupFilters(){
    const rows = [...positionRows().open, ...positionRows().history];
    const coins = ["All", ...new Set(rows.map(r => r.coin).filter(Boolean))];
    const sets = ["All", ...new Set(rows.map(r => r.set).filter(Boolean))];
    const sides = ["All", ...new Set(rows.map(r => r.side).filter(Boolean))];
    const statuses = ["All", ...new Set(rows.map(r => r.status).filter(Boolean))];
    [["filter-coin", coins, "Coin"], ["filter-set", sets, "Set"]].forEach(([id, values, label]) => { const node = q("#"+id, desktop); if(node) node.innerHTML = `<option value="">${label}: All</option>` + values.filter(v=>v!=="All").map(v=>`<option>${h(v)}</option>`).join(""); });
    [["filter-side", sides, "Side"], ["filter-status", statuses, "Status"]].forEach(([id, values, label]) => { const node = q("#"+id, desktop); if(node) node.innerHTML = `<option value="">${label}: All</option>` + values.filter(v=>v!=="All").map(v=>`<option>${h(v)}</option>`).join(""); });
    [["fcoin", coins], ["fset", sets], ["fside", sides], ["fstatus", statuses]].forEach(([id, values]) => { const node = q("#"+id, mobile); if(node) node.innerHTML = values.map(v=>`<option>${h(v)}</option>`).join(""); });
  }
  function historyRangeFromButton(button){
    return button.dataset.range || String(button.textContent || "").trim();
  }
  function renderPositions(){
    const all = positionRows();
    const desktopRows = filtered(applyHistoryRange(all[posView] || []), desktop);
    const body = q("#positions-body", desktop);
    const historyTools = q("#history-tools", desktop);
    const historyNote = q("#history-note", desktop) || q("#history-note", mobile);
    if(historyTools) historyTools.classList.toggle("show", posView === "history");
    if(historyNote){
      historyNote.style.display = posView === "history" ? "" : "none";
      historyNote.textContent = `History range: ${historyRange}`;
    }
    qa(".positions-tab", desktop).forEach(b => b.classList.toggle("active", positionViewFromButton(b) === posView));
    qa(".range-btn", desktop).forEach(b => b.classList.toggle("active", historyRangeFromButton(b) === historyRange));
    qa(".seg button", mobile).forEach(b => b.classList.toggle("active", b.id && b.id.indexOf(posView) === 0));
    if(body){
      body.innerHTML = desktopRows.length ? desktopRows.map(r => `<tr><td>${h(r.time)}</td><td><b>${h(r.coin)}</b></td><td>${sideBadge(r.side)}</td><td>${badge(r.status)}</td><td>${h(r.qty)}</td><td>${money(r.value)}</td><td>${money(r.entry)}</td><td>${money(r.current)}</td><td>${h(r.tp)}</td><td>${h(r.sl)}</td><td class="${pnlClass(r.pnl)}">${h(r.pnl)}</td><td>${h(r.set)}</td><td>${h(r.age)}</td><td>${h(r.reason)}</td><td>${r.kind === "open" ? `<button class="row-action danger js-close-position" data-position-id="${h(r.id)}" data-symbol="${h(r.coin)}">Close</button>` : r.kind === "placed" ? '<button class="row-action" type="button" disabled title="Cancel Order backend command is unavailable">Cancel</button>' : "—"}</td></tr>`).join("") : '<tr><td colspan="15" class="empty">No records.</td></tr>';
    }
    const mobileRows = filtered(applyHistoryRange(all[posView] || []), mobile);
    const list = q("#list", mobile);
    if(list){
      list.innerHTML = mobileRows.length ? mobileRows.map(r => `<article class="card" onclick="this.classList.toggle('expanded')"><div class="card-top"><div class="coin-row"><span class="coin">${h(r.coin)}</span><span class="side">${h(r.side)}</span></div>${badge(r.status)}</div><div class="grid"><div><div class="fl">Entry</div><div class="fv">${money(r.entry)}</div></div><div><div class="fl">${r.status === "CLOSED" ? "Exit" : "Current"}</div><div class="fv">${money(r.current)}</div></div><div><div class="fl">Take Profit</div><div class="fv">${h(r.tp)}</div></div><div><div class="fl">Stop Loss</div><div class="fv">${h(r.sl)}</div></div>${r.pnl !== "—" ? `<div><div class="fl">P&amp;L</div><div class="fv ${pnlClass(r.pnl)}">${h(r.pnl)}</div></div>` : ""}${r.reason !== "—" ? `<div class="reason"><div class="fl">Reason</div><div class="fv">${h(r.reason)}</div></div>` : ""}</div><div class="meta"><span>${h(r.set)}</span><span>${h(r.age)}</span></div><div class="details"><div><div class="fl">Time</div><div class="fv">${h(r.time)}</div></div><div><div class="fl">Quantity</div><div class="fv">${h(r.qty)}</div></div><div><div class="fl">Value</div><div class="fv">${money(r.value)}</div></div><div><div class="fl">Status</div><div class="fv">${h(r.status)}</div></div></div>${r.kind === "open" ? `<button class="row-action danger js-close-position" data-position-id="${h(r.id)}" data-symbol="${h(r.coin)}">Close Position</button>` : ""}</article>`).join("") : '<div class="empty">No records.</div>';
    }
    const countNode = q("#count", mobile);
    if(countNode){
      const activeFilters = ["fcoin","fside","fstatus","fset"].filter(id => {
        const value = q("#" + id, mobile)?.value || "";
        return value && value !== "All";
      }).length;
      countNode.textContent = String(activeFilters);
      countNode.style.display = activeFilters ? "inline-flex" : "none";
    }
  }
  window.setPositionsView = window.setView = function(view){ posView = view; renderPositions(); };
  window.openFilters = function(){ q("#filters-bg", mobile)?.classList.add("show"); };
  window.openActions = function(){ q("#actions-bg", mobile)?.classList.add("show"); };
  window.backdrop = function(eventOrId, maybeId){
    const id = maybeId || eventOrId;
    if(typeof eventOrId === "object" && eventOrId?.target?.id !== id) return;
    q("#"+id, mobile)?.classList.remove("show");
  };
  window.applyFilters = function(){ window.backdrop("filters-bg"); renderPositions(); };
  window.resetFilters = function(){ qa("select", mobile).forEach(s => s.selectedIndex = 0); renderPositions(); };
  window.action = function(name){ window.backdrop("actions-bg"); if(name === "pause") confirmPauseEntries(); if(name === "close") confirmCloseAll(); };
  function positionViewFromButton(button){
    return button.dataset.view || button.dataset.pos || String(button.id || "").replace(/-tab$/, "");
  }
  qa(".positions-tab", desktop).forEach(b => b.addEventListener("click", () => window.setPositionsView(positionViewFromButton(b))));
  qa(".range-btn", desktop).forEach(b => b.addEventListener("click", () => { historyRange = historyRangeFromButton(b) || historyRange; renderPositions(); }));
  qa(".positions-tools-row select", desktop).forEach(s => s.addEventListener("change", renderPositions));

  const metricsRegistry = state.metrics || {metrics: []};
  let metricFamilyFilter = "ALL";
  function metricsList(){
    return Array.isArray(metricsRegistry.metrics) ? metricsRegistry.metrics : [];
  }
  function metricFamilyCode(metric){
    return String(metric?.id || "").split("-")[0] || "";
  }
  function metricFamilyLabel(code){
    return ({
      F:"Formula / system calculations",
      A:"Accounting calculations and rules",
      M:"Research-only performance metrics",
      N:"Numeric and normalization policies",
      S:"State and system classification rules"
    })[code] || code || "Unknown";
  }
  function metricSearchValue(){
    return String(q("#metricSearch", desktop)?.value || "").trim().toLowerCase();
  }
  function metricSection(title, value){
    const text = String(value || "").trim();
    if(!text) return "";
    return `<div class="details-section"><div class="section-title">${h(title)}</div><div class="formula" style="white-space:pre-line">${h(text)}</div></div>`;
  }
  function metricRows(){
    const needle = metricSearchValue();
    return metricsList().filter(metric => {
      const family = metricFamilyCode(metric);
      if(metricFamilyFilter !== "ALL" && family !== metricFamilyFilter) return false;
      if(!needle) return true;
      return [metric.id, metric.name].some(value => String(value || "").toLowerCase().includes(needle));
    });
  }
  function setupMetricsShell(){
    const header = q("#config-metrics .panel-header", desktop);
    if(header && !q("#metricFamilyFilters", header)){
      header.innerHTML = `<div class="toolbar metric-toolbar"><input class="search" id="metricSearch" placeholder="Search by ID or name"><div class="segment" id="metricFamilyFilters">${["ALL","F","A","M","N","S"].map(family => `<button type="button" class="metric-family-filter" data-family="${family}">${family}</button>`).join("")}</div></div>`;
      q("#metricSearch", header)?.addEventListener("input", renderMetrics);
      qa(".metric-family-filter", header).forEach(button => button.addEventListener("click", () => {
        metricFamilyFilter = button.dataset.family || "ALL";
        renderMetrics();
      }));
    }
    const head = q("#config-metrics thead", desktop);
    if(head){
      head.innerHTML = "<tr><th>ID</th><th>Name</th><th>Family</th><th>Type</th><th>Status</th></tr>";
    }
  }
  function renderMetrics(){
    setupMetricsShell();
    const body = q("#metrics-body", desktop) || q("#metricsBody", desktop) || q("#config-metrics tbody", desktop);
    const rows = metricRows();
    qa(".metric-family-filter", desktop).forEach(button => button.classList.toggle("active", (button.dataset.family || "ALL") === metricFamilyFilter));
    if(body) body.innerHTML = rows.length
      ? rows.map(m => `<tr class="catalog-row" data-metric="${h(m.id)}"><td><b>${h(m.id)}</b></td><td>${h(m.name)}</td><td>${h(metricFamilyCode(m))}</td><td>${h(m.type)}</td><td>${badge(m.status)}</td></tr>`).join("")
      : '<tr><td colspan="5" class="empty">No Metrics Library entries match the current filter.</td></tr>';
    qa("[data-metric]", desktop).forEach(row => row.onclick = () => window.showMetric(row.dataset.metric));
    const selected = rows[0] || metricsList()[0];
    if(selected) window.showMetric(selected.id);
  }
  window.showMetric = function(id){
    const m = metricsList().find(x => x.id === id) || metricsList()[0];
    const detail = q("#metric-details", desktop) || q("#metricDetail", desktop);
    qa("[data-metric]", desktop).forEach(row => row.classList.toggle("selected", row.dataset.metric === m?.id));
    if(!detail) return;
    if(!m){
      detail.innerHTML = '<div class="details-section"><div class="body-text">Metrics Library unavailable.</div></div>';
      return;
    }
    detail.innerHTML = `<div class="details-header"><div class="details-id">${h(m.id)} · ${h(m.status)}</div><div class="details-title">${h(m.name)}</div><div class="details-meta"><span class="meta-pill">${h(metricFamilyCode(m))}: ${h(metricFamilyLabel(metricFamilyCode(m)))}</span><span class="meta-pill">Owner: ${h(m.owner)}</span><span class="meta-pill">${h(m.type)}</span></div></div>${metricSection("What it is", m.what_it_is)}${metricSection("What it means", m.what_it_means)}${metricSection("Why it exists", m.why_it_exists)}${metricSection("Inputs", m.inputs)}${metricSection("Data source", m.data_source)}${metricSection("Formula / Rule", m.formula_or_rule)}${metricSection("Calculation / Evaluation steps", m.calculation_steps)}${metricSection("Output", m.output)}${metricSection("Worked example", m.worked_example)}${metricSection("Unavailable / invalid behavior", m.unavailable_behavior)}${metricSection("Dependencies", m.dependencies)}${metricSection("Used by", m.used_by)}${metricSection("Important boundaries", m.important_boundaries)}${metricSection("Technical traceability", m.technical_traceability)}`;
  };
  function renderTriggers(){
    const rows = state.registry.triggers || [];
    const sets = state.registry.sets || [];
    const body = q("#triggers-body", desktop) || q("#triggersBody", desktop) || q("#config-triggers tbody", desktop);
    if(body) body.innerHTML = rows.length ? rows.map(t => `<tr class="catalog-row" data-trigger-id="${h(t.trigger_id)}" data-trigger-version="${h(t.version)}"><td>${h(t.display_name || t.trigger_id)}</td><td>${h(t.version)}</td><td>—</td><td>${h(t.what_it_checks || "—")}</td><td>${h(sets.filter(s => (s.trigger_versions||[]).some(v => v.trigger_id === t.trigger_id && v.version === t.version)).map(s => s.set_id + " " + s.version).join(", ") || "—")}</td><td>${badge(t.immutable ? "ACTIVE" : "RESEARCH")}</td></tr>`).join("") : '<tr><td colspan="6" class="empty">No Trigger versions available.</td></tr>';
    qa("[data-trigger-id]", desktop).forEach(row => row.onclick = () => window.showTrigger(row.dataset.triggerId, row.dataset.triggerVersion));
    if(rows[0]) window.showTrigger(rows[0].trigger_id, rows[0].version);
  }
  window.showTrigger = function(id, version){
    const t = (state.registry.selected_trigger && state.registry.selected_trigger.trigger_id === id && state.registry.selected_trigger.version === version) ? state.registry.selected_trigger : (state.registry.triggers || []).find(x => x.trigger_id === id && x.version === version);
    const detail = q("#trigger-details", desktop) || q("#triggerDetail", desktop);
    const usedIn = (t?.used_in && t.used_in.length)
      ? t.used_in
      : (state.registry.sets || [])
          .filter(s => (s.trigger_versions || []).some(v => v.trigger_id === id && v.version === version))
          .map(s => ({set_id:s.set_id, set_version:s.version, set_status:s.status}));
    const versions = t?.version_history || [];
    if(detail) detail.innerHTML = `<div class="details-header"><div class="details-id">Trigger ${h(id)} · Version ${h(version || t?.version || "—")} · ${h(triggerStatusLabel(t))}</div><div class="details-title">${h(t?.display_name || id || "Trigger")}</div><div class="details-meta"><span class="meta-pill">Status: ${h(triggerStatusLabel(t))}</span><span class="meta-pill">${t?.immutable ? "CURRENT" : "HISTORICAL / RESEARCH"}</span></div></div><div class="details-section"><div class="section-title">Metric</div><div class="reference-links"><button class="reference-link" onclick="openConfig('metrics')">${h(t?.metric || "Metric unavailable")}</button></div></div><div class="details-section"><div class="section-title">Condition</div><div class="formula" style="white-space:pre-line">${h(t?.formula_text || t?.what_it_checks || "Unavailable")}</div></div><div class="details-section"><div class="section-title">What this Trigger means</div><div class="body-text">${h(t?.how_it_works || "Backend trigger detail unavailable.")}</div></div><div class="details-section"><div class="section-title">How it works</div><div class="step-list">${String(t?.how_it_works || "Backend trigger detail unavailable.").split(/\n+|;\s*/).filter(Boolean).map((step,index) => `<div class="calc-step"><div class="step-number">${index+1}</div><div class="step-body">${h(step)}</div></div>`).join("")}</div></div><div class="details-section"><div class="section-title">Unavailable behavior</div><div class="body-text">${h(t?.unavailable_reason || "If required backend observations or metric inputs are unavailable, the Trigger result is unavailable; the frontend does not convert missing facts to zero or fabricate a signal.")}</div></div><div class="details-section"><div class="section-title">Used in Set Versions</div><div class="reference-links">${usedIn.length ? usedIn.map(s => `<button class="reference-link js-open-set" data-set-id="${h(s.set_id)}" data-set-version="${h(s.set_version)}">${h(s.set_id)} ${h(s.set_version)} · ${h(setStatusLabel(s.set_status))}</button>`).join("") : "—"}</div></div><div class="details-section"><div class="section-title">Version History</div><div class="version-list">${versions.length ? versions.map(v => `<button class="version-button js-open-trigger ${v.version === (version || t?.version) ? "selected" : ""}" data-trigger-id="${h(id)}" data-trigger-version="${h(v.version)}">${h(v.version)} · ${h(v.change_summary || v.created_at || "")}</button>`).join("") : "—"}</div></div>`;
  };
  function renderSets(){
    const rows = state.registry.sets || [];
    const body = q("#sets-body", desktop) || q("#setsBody", desktop) || q("#config-sets tbody", desktop);
    if(body) body.innerHTML = rows.length ? rows.map(s => `<tr class="catalog-row" data-set-id="${h(s.set_id)}" data-set-version="${h(s.version)}"><td>${h(s.display_name || s.set_id)}</td><td>${h(s.version)}</td><td>${h([s.symbol, s.timeframe].filter(Boolean).join(" · ") || "—")}</td><td>${h((s.trigger_versions || []).map(t => t.trigger_id + " " + t.version).join(", ") || "—")}</td><td>${badge(s.status || "UNKNOWN")}</td></tr>`).join("") : '<tr><td colspan="5" class="empty">No Set versions available.</td></tr>';
    qa("[data-set-id]", desktop).forEach(row => row.onclick = () => window.showSet(row.dataset.setId, row.dataset.setVersion));
    if(rows[0]) window.showSet(rows[0].set_id, rows[0].version);
  }
  window.showSet = function(id, version){
    const s = (state.registry.sets || []).find(x => x.set_id === id && x.version === version);
    const members = (s?.trigger_versions || s?.rules || []).map(x => ({trigger_id:x.trigger_id || x.rule_id, version:x.version || x.rule_version, display_name:x.display_name || x.name, condition:x.condition}));
    const detail = q("#set-details", desktop) || q("#setDetail", desktop);
    const triggerLinks = members.map(t => `<button class="reference-link js-open-trigger" data-trigger-id="${h(t.trigger_id)}" data-trigger-version="${h(t.version)}">${h(t.trigger_id)} ${h(t.version)}</button>`).join(" ");
    const condition = members.map(t => `<span class="logic-trigger">${h(t.trigger_id)} ${h(t.version)}</span> evaluates TRUE`).join(" AND ");
    if(detail) detail.innerHTML = `<div class="details-header"><div class="details-id">Set ${h(id)} · Version ${h(version)} · ${h(setStatusLabel(s?.status))}</div><div class="details-title">${h(s?.display_name || s?.purpose || id || "Set")}</div><div class="details-meta"><span class="meta-pill">Direction: LONG / SHORT / NONE</span><span class="meta-pill">${h([s?.symbol, s?.timeframe].filter(Boolean).join(" · ") || "Market unavailable")}</span></div></div><div class="details-section"><div class="section-title">Trigger Versions Used</div><div class="reference-links">${triggerLinks || "—"}</div></div><div class="details-section"><div class="section-title">Human-readable Set Logic</div><div class="set-logic"><div class="set-logic-row"><div class="logic-keyword">IF</div><div class="logic-condition">${condition || "No trigger versions recorded"}</div></div><div class="set-logic-row"><div class="logic-keyword">THEN</div><div class="logic-condition">Direction resolves through this Set to LONG / SHORT / NONE for the configured market.</div></div><div class="set-logic-row"><div class="logic-keyword">ELSE</div><div class="logic-condition">Direction = NONE.</div></div></div></div><div class="details-section"><div class="section-title">Historical correctness</div><div class="body-text">This panel renders the exact selected Set Version and the exact Trigger Versions recorded for that version.</div></div>`;
  };
  qa(".config-tab", desktop).forEach(b => b.onclick = () => openConfig(b.dataset.config));

  function renderRules(){
    const c = state.rules.current;
    const body = q("#config-rules .rules-stack", desktop) || q("#rules-body", desktop) || q("#rulesBody", desktop);
    if(!body) return;
    if(!c) return;
    if(coinDraftVersion !== c.rules_version_id){
      coinDraftVersion = c.rules_version_id;
      coinDraft = (c.coins || []).map(x => ({
        symbol: String(x.symbol || "").toUpperCase(),
        enabled: x.enabled !== false,
        max_allocation_pct: normalizeCoinAllocation(x.max_allocation_pct)
      })).filter(x => x.symbol);
    }
    const pr = c.position_rules || {}, po = c.portfolio_rules || {};
    const values = new Map([
      ["Position Size", pr.position_size_pct],
      ["Fixed Take Profit", pr.fixed_take_profit_pct],
      ["Minimum Take Profit", pr.minimum_take_profit_pct],
      ["Stop Loss", pr.stop_loss_pct],
      ["Minimum Risk / Reward", pr.minimum_risk_reward],
      ["Minimum Net Edge", pr.minimum_net_edge_pct],
      ["Max Capital in Positions", po.max_capital_in_positions_pct],
      ["Max Open Positions", po.max_open_positions],
      ["Max Positions per Coin", po.max_positions_per_coin],
      ["Daily Loss Limit", po.daily_loss_limit_pct]
    ]);
    qa(".rule-row", body).forEach(row => {
      const label = q(".rule-name", row)?.textContent?.trim();
      const input = q("input", row);
      if(label && input && values.has(label)) input.value = values.get(label) ?? "";
    });
    const takeProfitRow = qa(".rule-row", body).find(row => q(".rule-name", row)?.textContent?.trim() === "Take Profit");
    if(takeProfitRow){
      const activeMode = String(pr.take_profit_mode || "DYNAMIC").toUpperCase();
      qa(".mode-btn", takeProfitRow).forEach(button => button.classList.toggle("active", button.textContent.trim().toUpperCase() === activeMode));
    }
    const stopLossRow = qa(".rule-row", body).find(row => q(".rule-name", row)?.textContent?.trim() === "Stop Loss");
    if(stopLossRow){
      qa(".mode-btn", stopLossRow).forEach((button, index) => button.classList.toggle("active", index === 0));
    }
    const leverageSelect = qa(".rule-row", body).find(row => q(".rule-name", row)?.textContent?.trim() === "Leverage")?.querySelector("select");
    if(leverageSelect && pr.leverage) leverageSelect.value = String(pr.leverage).endsWith("x") ? String(pr.leverage) : String(pr.leverage) + "x";
    const directionSelect = qa(".rule-row", body).find(row => q(".rule-name", row)?.textContent?.trim() === "Direction")?.querySelector("select");
    if(directionSelect && po.direction_mode){
      const normalized = String(po.direction_mode).replace("_", " ").replace("ONLY", "only");
      Array.from(directionSelect.options).forEach(option => { if(option.textContent.toUpperCase().replace("+", "").includes(normalized.toUpperCase().replace("_", " "))) directionSelect.value = option.value; });
    }
    const coinGrid = q("#coin-grid", body);
    if(coinGrid){
      coinGrid.innerHTML = coinDraft.length ? `<div class="coin-list">${coinDraft.map(x => `<div class="coin-row" data-symbol="${h(x.symbol)}"><div class="coin-symbol">${h(x.symbol)}</div><input class="coin-allocation-input js-coin-allocation" data-symbol="${h(x.symbol)}" type="number" step="0.01" inputmode="decimal" value="${h(x.max_allocation_pct)}"><span class="coin-percent">%</span><button class="coin-remove js-remove-coin" type="button" data-symbol="${h(x.symbol)}" aria-label="Remove ${h(x.symbol)}">×</button></div>`).join("")}</div>` : '<div class="empty">No records.</div>';
      qa(".js-coin-allocation", coinGrid).forEach(input => input.addEventListener("input", () => {
        const item = coinDraft.find(x => x.symbol === input.dataset.symbol);
        if(item) item.max_allocation_pct = input.value;
      }));
      qa(".js-remove-coin", coinGrid).forEach(button => button.addEventListener("click", () => {
        coinDraft = coinDraft.filter(x => x.symbol !== button.dataset.symbol);
        renderRules();
      }));
    }
    const history = q(".history-panel", body);
    if(history){
      history.innerHTML = '<div class="history-title">Version History</div>' + ((state.rules.history || []).map(v => `<div class="history-row"><button class="link">${h(v.display_version)}</button><span class="badge inactive">Inactive</span><div>${h(v.change_summary || "Previous configuration")}</div><div>${h(v.created_at || "—")}</div></div>`).join("") || '<div class="history-row"><button class="link">—</button><span class="badge inactive">Unavailable</span><div>No version history.</div><div>—</div></div>');
    }
    const footer = q(".coins-footer", body);
    if(footer){
      const search = coinSearchOpen ? `<div class="coin-combobox"><input class="coin-search-input" type="text" value="${h(coinSearchQuery)}" placeholder="Search or enter symbol..." autocomplete="off" aria-label="Search or enter symbol">${coinSearchResultsHtml()}</div>` : "";
      footer.innerHTML = `${search}<button class="btn js-add-coin" type="button">+ Add Coin</button>`;
      q(".js-add-coin", footer)?.addEventListener("click", window.addCoinToRules);
      const input = q(".coin-search-input", footer);
      if(input){
        input.addEventListener("input", () => { coinSearchQuery = input.value; coinSearchIndex = 0; coinSearchError = ""; updateCoinSearchResults(); });
        input.addEventListener("keydown", (event) => {
          const options = matchingCoinSymbols();
          if(event.key === "ArrowDown"){ event.preventDefault(); coinSearchIndex = Math.min(coinSearchIndex + 1, Math.max(options.length - 1, 0)); updateCoinSearchResults(); return; }
          if(event.key === "ArrowUp"){ event.preventDefault(); coinSearchIndex = Math.max(coinSearchIndex - 1, 0); updateCoinSearchResults(); return; }
          if(event.key === "Escape"){ event.preventDefault(); resetCoinSearch(); renderRules(); return; }
          if(event.key === "Enter"){ event.preventDefault(); addCoinSymbol(options[coinSearchIndex] || coinSearchQuery); }
        });
        setTimeout(() => q(".coin-search-input", desktop)?.focus(), 0);
      }
      bindCoinSearchOptions(footer);
    }
    qa(".mode-selector .mode-btn", body).forEach(button => button.addEventListener("click", () => {
      qa(".mode-btn", button.closest(".mode-selector")).forEach(node => node.classList.toggle("active", node === button));
    }));
    q(".save-btn", body)?.addEventListener("click", window.saveRulesVersion);
  }
  function setRulesSaveState(message, tone="neutral"){
    const body = q("#config-rules .rules-stack", desktop) || q("#rules-body", desktop) || q("#rulesBody", desktop);
    const row = q(".rules-save", body);
    if(!row) return;
    let node = q(".rules-save-state", row);
    if(!node){
      node = document.createElement("div");
      node.className = "rules-save-state panel-meta";
      row.prepend(node);
    }
    node.className = "rules-save-state panel-meta " + tone;
    node.textContent = message || "";
  }
  function ruleInputValue(body, label, fallback){
    const row = qa(".rule-row", body).find(node => q(".rule-name", node)?.textContent?.trim() === label);
    if(!row) return fallback;
    const input = q("input", row);
    return input ? input.value : fallback;
  }
  function ruleSelectValue(body, label, fallback){
    const row = qa(".rule-row", body).find(node => q(".rule-name", node)?.textContent?.trim() === label);
    if(!row) return fallback;
    const select = q("select", row);
    return select ? select.value : fallback;
  }
  function ruleModeValue(body, label, fallback){
    const row = qa(".rule-row", body).find(node => q(".rule-name", node)?.textContent?.trim() === label);
    if(!row) return fallback;
    const active = q(".mode-btn.active", row);
    return active ? active.textContent.trim().toUpperCase() : fallback;
  }
  function directionPayload(value){
    const normalized = String(value || "").toUpperCase();
    if(normalized.includes("LONG") && normalized.includes("SHORT")) return "LONG_SHORT";
    if(normalized.includes("SHORT")) return "SHORT_ONLY";
    if(normalized.includes("LONG")) return "LONG_ONLY";
    return normalized;
  }
  function rulePayload(){
    const current = state.rules.current || {};
    const pr = current.position_rules || {};
    const po = current.portfolio_rules || {};
    const body = q("#config-rules .rules-stack", desktop) || q("#rules-body", desktop) || q("#rulesBody", desktop);
    return {
      position_rules: {
        ...pr,
        position_size_pct: ruleInputValue(body, "Position Size", pr.position_size_pct),
        take_profit_mode: ruleModeValue(body, "Take Profit", pr.take_profit_mode || "DYNAMIC"),
        fixed_take_profit_pct: ruleInputValue(body, "Fixed Take Profit", pr.fixed_take_profit_pct),
        minimum_take_profit_pct: ruleInputValue(body, "Minimum Take Profit", pr.minimum_take_profit_pct),
        stop_loss_pct: ruleInputValue(body, "Stop Loss", pr.stop_loss_pct),
        minimum_risk_reward: ruleInputValue(body, "Minimum Risk / Reward", pr.minimum_risk_reward),
        minimum_net_edge_pct: ruleInputValue(body, "Minimum Net Edge", pr.minimum_net_edge_pct),
        leverage: String(ruleSelectValue(body, "Leverage", pr.leverage) || "").replace("x", "")
      },
      portfolio_rules: {
        ...po,
        max_capital_in_positions_pct: ruleInputValue(body, "Max Capital in Positions", po.max_capital_in_positions_pct),
        max_open_positions: ruleInputValue(body, "Max Open Positions", po.max_open_positions),
        max_positions_per_coin: ruleInputValue(body, "Max Positions per Coin", po.max_positions_per_coin),
        direction_mode: directionPayload(ruleSelectValue(body, "Direction", po.direction_mode)),
        daily_loss_limit_pct: ruleInputValue(body, "Daily Loss Limit", po.daily_loss_limit_pct)
      }
    };
  }
  window.addCoinToRules = function(){
    if(!coinSearchOpen){
      coinSearchOpen = true;
      coinSearchError = "";
      renderRules();
      return;
    }
    addCoinSymbol(matchingCoinSymbols()[coinSearchIndex] || coinSearchQuery);
  };
  window.saveRulesVersion = async function(){
    if(!canSubmit()){ setRulesSaveState("Operator command submission is unavailable.", "negative"); return; }
    const current = state.rules.current;
    if(!current){ setRulesSaveState("Current rules version is unavailable.", "negative"); return; }
    const payload = {
      expected_rules_version_id: current.rules_version_id || "",
      expected_display_version: current.display_version || "",
      ...rulePayload(),
      coins: coinPayload()
    };
    try{
      setRulesSaveState("Saving...", "neutral");
      const data = await postJson("/api/rules/versions", payload);
      state.rules.current = data.rules || state.rules.current;
      state.rules.history = data.history || state.rules.history;
      renderRules();
      setRulesSaveState("Saved as new version.", "positive");
    }catch(error){
      setRulesSaveState(error.message || "Rules save failed.", "negative");
    }
  };

  function renderResearchSummary(){
    const body = q("#research-summary-body", desktop) || q("#researchBody", desktop);
    const search = String(q("#research-search", desktop)?.value || "").trim().toLowerCase();
    const demoFilter = String(q("#demo-filter", desktop)?.value || "").trim().toLowerCase();
    const decisionFilter = String(q("#decision-filter", desktop)?.value || "").trim().toLowerCase();
    const demoState = (r) => String(r.demo_status || r.selected_demo_status || r.status || "").toLowerCase().includes("running") ? "running" : r.selected_demo_run_id ? "complete" : "pending";
    const rows = (state.research.summaries || []).filter(r => {
      const demo = demoState(r);
      const decision = String(r.decision || r.status || "NONE").toLowerCase();
      const haystack = [r.research_id, r.set_id, r.set_version, r.rules_display_version, r.rules_version_id, decision].join(" ").toLowerCase();
      return (!search || haystack.includes(search)) && (!demoFilter || demo === demoFilter) && (!decisionFilter || decision === decisionFilter);
    });
    if(!body) return;
    if(researchRegistryUnavailable()){
      body.innerHTML = `<tr><td colspan="8" class="empty">Research registry unavailable: ${h(state.research.unavailable_reason)}</td></tr>`;
      applyCommandAvailability();
      return;
    }
    body.innerHTML = rows.length ? rows.map(r => `<tr class="research-row" data-research-id="${h(r.research_id)}"><td><div class="research-id">${h(r.research_id)}</div></td><td>${h(r.set_id)}<div class="panel-meta">${h(r.set_version)}</div></td><td>${h(r.rules_display_version)}<div class="panel-meta">${h(r.rules_version_id)}</div></td><td>${h(demoState(r).replace(/^./, c => c.toUpperCase()))}</td><td>${h(r.selected_demo_profit_factor ?? "—")}</td><td>${h(r.compare_to_active || "—")}</td><td>—</td><td>${badge(r.decision || r.status || "NONE")}</td></tr>`).join("") : '<tr><td colspan="8" class="empty">No Research records.</td></tr>';
    qa("[data-research-id]", desktop).forEach(row => row.onclick = () => window.openResearchById(row.dataset.researchId));
    applyCommandAvailability();
  }
  function showResearchUnavailable(message){
    currentResearchId = "";
    currentResearch = {research:{}, backtests:[], demos:[], run_projection:{available:false, reason:message || "Research record unavailable."}};
    currentCompare = {available:false, reason:message || "Research record unavailable."};
    showPage("research-detail", {preserveUrl:true});
    renderResearchDetail();
    renderCompare();
    setResearchActionButtonsDisabled(true);
    setResearchActionStatus(message || "Research record unavailable.", "negative");
  }
  function showResearchLoading(id){
    currentResearch = {research:{research_id:id}, backtests:null, demos:null, loading:true};
    currentCompare = {available:false, reason:"Loading Research detail."};
    renderResearchDetail();
    renderCompare();
    setResearchActionButtonsDisabled(true);
    setResearchActionStatus("Loading Research detail...", "neutral");
  }
  window.openResearchById = async function(id, options={}){
    const safeId = String(id || "").trim();
    if(!safeId){
      showResearchUnavailable("Research record unavailable.");
      return;
    }
    currentResearchId = safeId;
    showPage("research-detail", {preserveUrl:!!options.preserveUrl});
    if(!options.preserveUrl) history.pushState(null, "", `/research/${encodeURIComponent(safeId)}`);
    showResearchLoading(safeId);
    try{
      const res = await fetch(`/api/research/${encodeURIComponent(safeId)}`, {credentials:"same-origin"});
      const data = await res.json().catch(() => ({}));
      if(!res.ok) throw new Error(data.error || data.reason || "Research record unavailable.");
      currentResearch = data;
      renderResearchDetail();
      if(currentResearch?.run_projection?.available === false){
        setResearchActionStatus(currentResearch.run_projection.reason || "Research run evidence unavailable.", "negative");
      }else{
        setResearchActionStatus("", "neutral");
      }
      await loadCompare();
    }catch(error){
      showResearchUnavailable(error.message || "Research record unavailable.");
    }
  };
  function canonicalStatus(value){ return String(value || "").trim().toUpperCase(); }
  function isTerminalSuccessStatus(value){ return ["COMPLETED","COMPLETE","STOPPED","SUCCEEDED","SUCCESS"].includes(canonicalStatus(value)); }
  function isRunningStatus(value){ return ["RUNNING","PENDING","QUEUED","STARTED","IN_PROGRESS"].includes(canonicalStatus(value)); }
  function isFailureStatus(value){ return ["FAILED","BLOCKED","ERROR","REJECTED","CANCELLED","UNAVAILABLE"].includes(canonicalStatus(value)); }
  function factualRunStatus(row, kind){
    const status = canonicalStatus(row?.status);
    if(kind === "demo" && status === "RUNNING"){
      const progress = row?.progress_days;
      return progress === null || progress === undefined || progress === "" ? "RUNNING" : `RUNNING · ${h(progress)} / 7`;
    }
    return status || "UNKNOWN";
  }
  function workflowBacktestState(rows){
    if(!rows.length) return {label:"NOT STARTED", done:false, failed:false};
    const latest = rows[0] || {};
    const status = factualRunStatus(latest, "backtest");
    return {label:status, done:isTerminalSuccessStatus(latest.status), failed:isFailureStatus(latest.status)};
  }
  function workflowDemoState(rows){
    if(!rows.length) return {label:"NOT STARTED", done:false, failed:false, progress:null};
    const latest = rows[0] || {};
    const progress = latest.progress_days === null || latest.progress_days === undefined || latest.progress_days === "" ? null : Number(latest.progress_days);
    return {label:factualRunStatus(latest, "demo"), done:isTerminalSuccessStatus(latest.status), failed:isFailureStatus(latest.status), progress:Number.isFinite(progress) ? Math.max(0, Math.min(7, progress)) : null};
  }
  function setWorkflowCard(cardId, stateId, result){
    const card = q(cardId, desktop);
    const label = q(stateId, desktop);
    if(label) label.textContent = result.label;
    if(card){
      card.classList.toggle("done", !!result.done);
      card.classList.toggle("reject-done", !!result.failed);
      card.classList.toggle("active", isRunningStatus(result.label));
    }
  }
  function renderDemoSegments(progress){
    const segments = q("#demoSegments, #demo-segments", desktop);
    if(!segments) return;
    if(progress === null || progress === undefined){
      segments.innerHTML = "";
      return;
    }
    segments.innerHTML = Array.from({length:7}, (_, i) => `<div class="demo-segment ${i < progress ? "filled" : ""}"></div>`).join("");
  }
  function runRows(rows, kind){ return rows.length ? rows.map(r => `<tr><td>${h(r.run_id || r.backtest_run_id)}</td><td>${h((r.period_start || r.started_at || "—") + " -> " + (r.period_end || r.stopped_at || "—"))}</td><td>${h(r.metrics?.closed_trades ?? "—")}</td><td>${h(r.metrics?.net_pnl ?? "—")}</td><td>${h(r.metrics?.profit_factor ?? "—")}</td><td>${h(factualRunStatus(r, kind))}</td></tr>`).join("") : '<tr><td colspan="6" class="empty">No runs.</td></tr>'; }
  function renderResearchDetail(){
    const r = currentResearch?.research || {};
    const decisionValue = r.decision || r.status || "NONE";
    const loading = !!currentResearch?.loading;
    const backtests = Array.isArray(currentResearch?.backtests) ? currentResearch.backtests : [];
    const demos = Array.isArray(currentResearch?.demos) ? currentResearch.demos : [];
    const title = q("#research-detail-title", desktop) || q("#researchTitle", desktop);
    if(title) title.textContent = r.research_id ? `${r.research_id} · ${r.set_id} ${r.set_version} · Rules ${r.rules_display_version || r.rules_version_id}` : "Research";
    const bt = q("#backtest-body", desktop) || q("#backtestBody", desktop);
    const dm = q("#demo-body", desktop) || q("#demoBody", desktop);
    if(bt) bt.innerHTML = loading ? '<tr><td colspan="6" class="empty">Loading Research detail.</td></tr>' : runRows(backtests, "backtest");
    if(dm) dm.innerHTML = loading ? '<tr><td colspan="6" class="empty">Loading Research detail.</td></tr>' : runRows(demos, "demo");
    const backtestState = loading ? {label:"LOADING", done:false, failed:false} : workflowBacktestState(backtests);
    const demoState = loading ? {label:"LOADING", done:false, failed:false, progress:null} : workflowDemoState(demos);
    setWorkflowCard("#wfBacktest, #workflow-backtest", "#wfBacktestState, #workflow-backtest-state", backtestState);
    setWorkflowCard("#wfDemo, #workflow-demo", "#wfDemoState, #workflow-demo-state", demoState);
    renderDemoSegments(demoState.progress);
    const decision = q("#decision-state", desktop) || q("#decisionStateInline", desktop);
    if(decision){ decision.textContent = decisionValue; decision.className = "badge " + String(decisionValue || "none").toLowerCase(); }
    const workflowDecision = q("#wfDecisionState, #workflow-decision-state", desktop) || q("#flowDecisionState", desktop);
    if(workflowDecision) workflowDecision.textContent = decisionValue;
    const workflowDecisionCard = q("#wfDecision, #workflow-decision", desktop);
    if(workflowDecisionCard){
      workflowDecisionCard.classList.toggle("done", decisionValue !== "NONE");
      workflowDecisionCard.classList.toggle("reject-done", decisionValue === "REJECT" || decisionValue === "ARCHIVE" || decisionValue === "ARCHIVED");
    }
    if(!currentResearchId || loading) setResearchActionButtonsDisabled(true);
    else applyCommandAvailability();
  }
  async function loadCompare(){
    if(!currentResearchId) return;
    try{
      const res = await fetch(`/api/research/${encodeURIComponent(currentResearchId)}/compare`, {credentials:"same-origin"});
      currentCompare = await res.json();
      if(!res.ok) currentCompare = {available:false, reason:currentCompare.error || currentCompare.reason || "Compare unavailable"};
    }catch(error){
      currentCompare = {available:false, reason:error.message || "Compare unavailable"};
    }
    setWorkflowCard("#wfCompare, #workflow-compare", "#wfCompareState, #workflow-compare-state", {label:currentCompare?.available ? "AVAILABLE" : "WAITING", done:!!currentCompare?.available, failed:false});
    renderCompare();
  }
  function renderCompare(){
    const table = q("#compare-table", desktop) || q("#compareTable", desktop);
    if(!table) return;
    if(compareScope !== "overall"){
      table.innerHTML = `<tbody><tr><td class="empty">Compare by ${h(compareScope)} is unavailable until the backend exposes factual segmented comparison dimensions.</td></tr></tbody>`;
      return;
    }
    if(comparePeriod !== "7D"){
      table.innerHTML = `<tbody><tr><td class="empty">Compare period ${h(comparePeriod)} is unavailable until the backend exposes factual period-specific comparison dimensions.</td></tr></tbody>`;
      return;
    }
    if(!currentCompare?.available){ table.innerHTML = `<tbody><tr><td class="empty">${h(currentCompare?.reason || "Compare unavailable")}</td></tr></tbody>`; return; }
    const rows = [["Closed trades","closed_trades"],["Net P/L","net_pnl"],["Expectancy","expectancy"],["Profit Factor","profit_factor"],["Max Drawdown","max_drawdown"]];
    table.innerHTML = `<thead><tr><th>Metric</th><th>Active</th><th>Demo</th><th>Difference</th></tr></thead><tbody>${rows.map(([label,key]) => `<tr><td>${h(label)}</td><td class="base-cell">${h(currentCompare.active_benchmark?.[key] ?? "—")}</td><td class="neutral-cell">${h(currentCompare.research_demo?.[key] ?? "—")}</td><td>${h(currentCompare.difference?.[key] ?? "—")}</td></tr>`).join("")}</tbody>`;
  }
  function setNewResearchState(message){
    const rulesSelect = q("#new-rules", desktop) || q("#newResearchRules", desktop);
    let node = q("#newResearchState", desktop);
    if(!node && rulesSelect?.parentElement){
      node = document.createElement("div");
      node.id = "newResearchState";
      node.className = "panel-meta";
      node.style.marginTop = "10px";
      rulesSelect.insertAdjacentElement("afterend", node);
    }
    if(node) node.textContent = message || "";
  }
  function setResearchActionStatus(message, tone="neutral"){
    let node = q("#researchActionStatus", desktop);
    if(!node){
      node = document.createElement("div");
      node.id = "researchActionStatus";
      node.className = "panel-meta";
      const head = q(".research-detail-head", desktop);
      if(head) head.appendChild(node);
    }
    if(node){
      node.className = "panel-meta " + tone;
      node.textContent = message || "";
    }
  }
  window.renderResearchSummary = renderResearchSummary;
  window.setCompareScope = function(scope){
    compareScope = scope || "overall";
    qa(".compare-tab", desktop).forEach(node => {
      const label = (node.textContent || "").trim().toLowerCase();
      node.classList.toggle("active", (compareScope === "overall" && label === "overall") || label.includes(compareScope));
    });
    renderCompare();
  };
  window.setComparePeriod = function(period){
    comparePeriod = period || "7D";
    qa(".compare-period", desktop).forEach(node => node.classList.toggle("active", (node.textContent || "").trim() === comparePeriod));
    renderCompare();
  };
  function setResearchActionButtonsDisabled(disabled){
    qa('button[onclick^="runBacktest"], button[onclick="runDemo()"]', desktop).forEach(node => node.disabled = !!disabled);
  }
  window.runBacktest = async function(period){ if(!currentResearchId){ setResearchActionStatus("Research record unavailable.", "negative"); return; } if(!canSubmit()){ setResearchActionStatus(commandUnavailableMessage(), "negative"); return; } if(researchRegistryUnavailable()){ setResearchActionStatus(state.research.unavailable_reason, "negative"); return; } const days = period === "90D" ? 90 : period === "30D" ? 30 : 7; const end = new Date(), start = new Date(end.getTime() - days * 86400000); setResearchActionButtonsDisabled(true); try{ setResearchActionStatus("Submitting backtest...", "neutral"); await postJson(`/api/research/${encodeURIComponent(currentResearchId)}/backtests`, {research_start:start.toISOString(),research_end:end.toISOString(),idempotency_key:commandIdempotencyKey("research-backtest")}); setResearchActionStatus("Backtest submitted.", "positive"); await window.openResearchById(currentResearchId); }catch(error){ currentCompare = {available:false, reason:error.message || "Backtest unavailable"}; setResearchActionStatus(error.message || "Backtest unavailable.", "negative"); renderCompare(); } finally { setResearchActionButtonsDisabled(false); } };
  window.runDemo = async function(){ if(!currentResearchId){ setResearchActionStatus("Research record unavailable.", "negative"); return; } if(!canSubmit()){ setResearchActionStatus(commandUnavailableMessage(), "negative"); return; } if(researchRegistryUnavailable()){ setResearchActionStatus(state.research.unavailable_reason, "negative"); return; } setResearchActionButtonsDisabled(true); try{ setResearchActionStatus("Starting demo...", "neutral"); await postJson(`/api/research/${encodeURIComponent(currentResearchId)}/demo/start`, {idempotency_key:commandIdempotencyKey("research-demo")}); setResearchActionStatus("Demo submitted.", "positive"); await window.openResearchById(currentResearchId); }catch(error){ currentCompare = {available:false, reason:error.message || "Demo start unavailable"}; setResearchActionStatus(error.message || "Demo start unavailable.", "negative"); renderCompare(); } finally { setResearchActionButtonsDisabled(false); } };
  window.setDecision = async function(value){ if(!currentResearchId){ setResearchActionStatus("Research record unavailable.", "negative"); return; } if(!canSubmit()){ setResearchActionStatus(commandUnavailableMessage(), "negative"); return; } if(researchRegistryUnavailable()){ setResearchActionStatus(state.research.unavailable_reason, "negative"); return; } const normalized = String(value || "").toUpperCase(); const url = normalized === "REJECT" ? `/api/research/${encodeURIComponent(currentResearchId)}/archive` : `/api/research/${encodeURIComponent(currentResearchId)}/decision/make-active`; try{ setResearchActionStatus("Submitting decision...", "neutral"); await postJson(url, {idempotency_key:"ui-"+Date.now()}); setResearchActionStatus("Decision submitted.", "positive"); }catch(error){ currentCompare = {available:false, reason:error.message || "Decision unavailable"}; setResearchActionStatus(error.message || "Decision unavailable.", "negative"); renderCompare(); } await window.openResearchById(currentResearchId); };
  window.exportResearch = function(){ const blob = new Blob([JSON.stringify({research:currentResearch, compare:currentCompare}, null, 2)], {type:"application/json"}); const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `${currentResearchId || "research"}-research.json`; a.click(); };
  function setupNewResearch(){
    const setSelect = q("#new-set", desktop) || q("#newResearchSet", desktop);
    const rulesSelect = q("#new-rules", desktop) || q("#newResearchRules", desktop);
    const sets = researchSetOptions();
    const rules = researchRulesOptions();
    if(setSelect) setSelect.innerHTML = sets.length ? sets.map(s => `<option value="${h(s.set_id)}|${h(s.set_version)}">${h(s.label || `${s.set_id} ${s.set_version}`)}</option>`).join("") : '<option value="">Set unavailable</option>';
    if(rulesSelect) rulesSelect.innerHTML = rules.length ? rules.map(r => `<option value="${h(r.rules_version_id)}">${h(r.label || r.rules_version_id)}</option>`).join("") : '<option value="">Rules unavailable</option>';
    setNewResearchState(sets.length && rules.length ? "" : "Backend Set and Rules versions are unavailable.");
  }
  window.openNewResearch = function(){ if(researchRegistryUnavailable()){ setNewResearchState(state.research.unavailable_reason); return; } setupNewResearch(); q("#new-research-modal", desktop)?.classList.add("show"); };
  window.closeNewResearch = function(){ q("#new-research-modal", desktop)?.classList.remove("show"); };
  window.createResearch = async function(){
    if(!canSubmit()){ setNewResearchState(commandUnavailableMessage()); return; }
    if(researchRegistryUnavailable()){ setNewResearchState(state.research.unavailable_reason); return; }
    const setValue = (q("#new-set", desktop) || q("#newResearchSet", desktop))?.value || "";
    const rules_version_id = (q("#new-rules", desktop) || q("#newResearchRules", desktop))?.value || "";
    const [set_id, set_version] = setValue.split("|");
    if(!set_id || !set_version || !rules_version_id){
      setNewResearchState("Backend Set and Rules versions are unavailable.");
      return;
    }
    try{
      const data = await postJson("/api/research", {set_id, set_version, rules_version_id, idempotency_key:commandIdempotencyKey("research-create")});
      window.closeNewResearch();
      await window.openResearchById(data.research?.research_id);
    }catch(error){
      setNewResearchState(error.message || "Research creation failed.");
    }
  };

  setupFilters(); applyOperatorState(); setupKpis(); renderPositions(); renderMetrics(); renderTriggers(); renderSets(); renderRules(); renderResearchSummary(); applyCommandAvailability();
  const initialPage = state.page === "config" ? "configuration" : state.page || "overview";
  const initialResearchId = researchIdFromLocation();
  if(initialPage === "research-detail"){
    if(initialResearchId) window.openResearchById(initialResearchId, {preserveUrl:true});
    else showResearchUnavailable("Research record unavailable.");
  }else{
    showPage(initialPage);
  }
})();
</script>
"""
    return script.replace("__STATE__", payload)


def _metrics_library_reference_panel() -> str:
    return """
  <!-- METRICS -->

  <section id="config-metrics" class="config-view active"><div class="layout"><section class="panel"><div class="panel-header"><div class="toolbar metric-toolbar"><input class="search" id="metricSearch" placeholder="Search by ID or name"><div class="segment" id="metricFamilyFilters"><button type="button" class="metric-family-filter active" data-family="ALL">ALL</button><button type="button" class="metric-family-filter" data-family="F">F</button><button type="button" class="metric-family-filter" data-family="A">A</button><button type="button" class="metric-family-filter" data-family="M">M</button><button type="button" class="metric-family-filter" data-family="N">N</button><button type="button" class="metric-family-filter" data-family="S">S</button></div></div></div><div class="table-wrap"><table><thead><tr><th>ID</th><th>Name</th><th>Family</th><th>Type</th><th>Status</th></tr></thead><tbody id="metrics-body"></tbody></table></div></section><section class="panel" id="metric-details"></section></div></section>
"""


def _replace_metrics_reference_panel(html_source: str) -> str:
    marker_start = html_source.find("  <!-- METRICS -->")
    marker_end = html_source.find("  <!-- TRIGGERS -->", marker_start)
    if marker_start >= 0 and marker_end >= 0:
        return html_source[:marker_start] + _metrics_library_reference_panel() + "\n" + html_source[marker_end:]
    start = html_source.find('<div class="config-view active" id="config-metrics">')
    end = html_source.find('<div class="config-view" id="config-triggers">', start)
    if start < 0 or end < 0:
        return html_source
    return html_source[:start] + _metrics_library_reference_panel() + html_source[end:]


def render_product_dashboard(
    *,
    initial_page: str = "overview",
    operator_state: Any = None,
    operator_control_token: str = "",
    operator_command_submit_enabled: bool = False,
    portfolio: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    rules: dict[str, Any] | None = None,
    messages: dict[str, Any] | None = None,
    research: dict[str, Any] | None = None,
) -> str:
    """Render the approved reference UI with backend state injected underneath."""

    from triggertrade.dashboard.metrics_library import metrics_payload
    from triggertrade.dashboard.reference_ui import DESKTOP_REFERENCE_HTML, MOBILE_OVERVIEW_REFERENCE_HTML

    page_map = {
        "portfolio": "overview",
        "overview": "overview",
        "sets": "config",
        "trigger-catalog": "config",
        "trigger-detail": "config",
        "rules": "config",
        "rules-version": "config",
        "config": "config",
        "research": "research",
        "research-detail": "research-detail",
        "messages": "research",
    }
    raw_state = getattr(operator_state, "state", None) if operator_state is not None else None
    state_available = raw_state in {"TRADING_ENABLED", "TRADING_PAUSED"}
    payload = json.dumps(
        {
            "page": page_map.get(initial_page, "overview"),
            "operatorState": raw_state if state_available else "UNKNOWN",
            "operatorStateAvailable": state_available,
            "canSubmitOperatorControl": bool(operator_command_submit_enabled),
            "localDevOperatorControls": bool(operator_control_token),
            "portfolio": _safe_payload(portfolio or {}),
            "registry": _safe_payload(registry or {}),
            "metrics": _safe_payload(metrics_payload()),
            "rules": _safe_payload(rules or {}),
            "research": _safe_payload(research or {"summaries": ()}),
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")
    desktop_head = _reference_head(DESKTOP_REFERENCE_HTML)
    desktop_body = _replace_metrics_reference_panel(
        _neutral_research_detail_placeholders(_without_reference_scripts(_reference_body(DESKTOP_REFERENCE_HTML)))
    )
    mobile_styles = _scoped_mobile_reference_styles(MOBILE_OVERVIEW_REFERENCE_HTML)
    mobile_body = _neutral_research_detail_placeholders(_without_reference_scripts(_reference_body(MOBILE_OVERVIEW_REFERENCE_HTML)))
    mobile_body = mobile_body.replace("onclick=\"alert('Prototype: Pause Entries')\"", "onclick=\"action('pause')\"")
    mobile_body = mobile_body.replace("onclick=\"confirm('Close all open positions?')\"", "onclick=\"action('close')\"")
    responsive_css = """
<style id="triggertrade-reference-composition">
#tt-desktop-reference{display:contents}
#tt-mobile-reference{display:none}
#config-rules .rules-stack{
  display:grid;
  grid-template-columns:minmax(0,3fr) minmax(0,2fr);
  gap:12px 14px;
  align-items:start;
}
#config-rules .rules-stack>.rules-section:nth-child(1){
  grid-column:1;
  grid-row:1 / span 2;
}
#config-rules .rules-stack>.rules-section:nth-child(2){
  grid-column:2;
  grid-row:1;
}
#config-rules .rules-stack>.rules-section:nth-child(3){
  grid-column:2;
  grid-row:2;
}
#config-rules .rules-stack>.rules-save{
  grid-column:1 / -1;
  display:flex;
  justify-content:flex-end;
  margin:10px 0;
}
#config-rules .rules-stack>.history-panel{
  grid-column:1 / -1;
  margin-top:0;
}
#config-rules .coins-grid{
  display:block;
  padding:6px 14px 8px;
}
#config-rules .coin-list{
  display:flex;
  flex-direction:column;
}
#config-rules .coin-row{
  min-height:44px;
  display:flex;
  align-items:center;
  gap:8px;
  padding:6px 0;
  border-bottom:1px solid #eef1f4;
}
#config-rules .coin-row:last-child{
  border-bottom:0;
}
#config-rules .coin-symbol{
  flex:1;
  min-width:0;
  font-size:10px;
  font-weight:800;
}
#config-rules .coin-allocation-input{
  width:84px;
  text-align:right;
}
#config-rules .coin-percent{
  color:#667085;
  font-size:10px;
}
#config-rules .coin-remove{
  width:28px;
  height:28px;
  min-height:28px;
  padding:0;
  border:1px solid var(--line2);
  border-radius:8px;
  background:#fff;
  color:#667085;
  font-size:16px;
  line-height:1;
}
#config-rules .coins-footer{
  display:flex;
  align-items:flex-start;
  gap:8px;
  justify-content:flex-end;
  padding:0 14px 12px;
}
#config-rules .coin-combobox{
  min-width:220px;
  max-width:320px;
  display:grid;
  gap:4px;
}
#config-rules .coin-search-input{
  width:100%;
}
#config-rules .coin-search-options{
  max-height:154px;
  overflow:auto;
  border:1px solid var(--line);
  border-radius:8px;
  background:#fff;
}
#config-rules .coin-search-option{
  width:100%;
  min-height:30px;
  padding:6px 9px;
  border:0;
  border-bottom:1px solid #eef1f4;
  background:#fff;
  color:#344054;
  text-align:left;
  font-size:10px;
  font-weight:800;
}
#config-rules .coin-search-option:last-child{
  border-bottom:0;
}
#config-rules .coin-search-option.active,
#config-rules .coin-search-option:hover{
  background:#f7faff;
}
#config-rules .coin-search-empty,
#config-rules .coin-search-error{
  padding:7px 9px;
  color:#98a2b3;
  font-size:10px;
}
#config-rules .coin-search-error{
  color:#b42318;
}
@media(max-width:760px){
  body.tt-mobile-overview-active{background:#f5f7fb}
  body.tt-mobile-overview-active #tt-desktop-reference{display:none}
  body.tt-mobile-overview-active #tt-mobile-reference{display:block}
  #config-rules .rules-stack{
    grid-template-columns:1fr;
  }
  #config-rules .rules-stack>.rules-section:nth-child(1),
  #config-rules .rules-stack>.rules-section:nth-child(2),
  #config-rules .rules-stack>.rules-section:nth-child(3),
  #config-rules .rules-stack>.rules-save,
  #config-rules .rules-stack>.history-panel{
    grid-column:1;
    grid-row:auto;
  }
}
</style>
"""
    forms = _operator_forms_html()
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        + desktop_head
        + "\n"
        + mobile_styles
        + responsive_css
        + "\n</head>\n<body class=\"tt-mobile-overview-active\">\n"
        + "<div id=\"tt-desktop-reference\">"
        + desktop_body
        + "</div>\n<div id=\"tt-mobile-reference\">"
        + mobile_body
        + "</div>\n"
        + forms
        + _reference_backend_script(payload)
        + _server_boundary_script(
            raw_state if state_available else "UNKNOWN",
            operator_command_submit_enabled,
            state_available,
            bool(operator_control_token),
        )
        + "\n</body>\n</html>"
    )
