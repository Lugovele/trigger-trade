from __future__ import annotations

import re
from types import SimpleNamespace

from triggertrade.dashboard.product_ui import render_product_dashboard


def _html(**kwargs) -> str:
    return render_product_dashboard(
        operator_state=SimpleNamespace(state="TRADING_ENABLED"),
        operator_command_submit_enabled=True,
        portfolio={
            "snapshot": {
                "total_equity": "1000.00",
                "available_capital": "750.00",
                "in_positions": "250.00",
                "realized_pnl_today": "12.50",
                "unrealized_pnl": "-3.25",
                "open_positions_count": 1,
            },
            "open_positions": (
                {
                    "position_id": "pos-1",
                    "symbol": "BTCUSDT",
                    "side": "LONG",
                    "qty": "0.01",
                    "qty_unit": "BTC",
                    "value": "250.00",
                    "entry_price": "25000",
                    "current_price": "25100",
                    "take_profit_pct": "2",
                    "take_profit_price": "25500",
                    "stop_loss_pct": "-1",
                    "stop_loss_price": "24750",
                    "unrealized_pnl_pct": "-0.4",
                    "unrealized_pnl_amount": "-3.25",
                    "set_version": "SET-CORE V1",
                    "age_seconds": 7200,
                },
            ),
            "closed_positions": (),
            "filters": {"symbols": ("BTCUSDT",), "set_versions": ("SET-CORE V1",)},
        },
        registry={
            "sets": (
                {
                    "set_id": "SET-CORE",
                    "display_name": "Core Set",
                    "version": "V1",
                    "status": "ACTIVE",
                    "trigger_versions": ({"trigger_id": "TR-001", "version": "V1"},),
                    "symbol": "BTCUSDT",
                    "timeframe": "1m",
                },
            ),
            "triggers": (
                {
                    "trigger_id": "TR-001",
                    "display_name": "ATR expansion",
                    "version": "V1",
                    "what_it_checks": "ATR_PCT greater than threshold",
                    "immutable": True,
                },
            ),
        },
        rules={
            "current": {
                "rules_version_id": "rules-1",
                "display_version": "V1",
                "position_rules": {
                    "position_size_pct": "10",
                    "fixed_take_profit_pct": "2",
                    "minimum_take_profit_pct": "1",
                    "stop_loss_pct": "1",
                    "minimum_risk_reward": "1.5",
                    "minimum_net_edge_pct": "0.2",
                    "leverage": "2",
                },
                "portfolio_rules": {
                    "max_capital_in_positions_pct": "50",
                    "max_open_positions": "3",
                    "max_positions_per_coin": "1",
                    "direction_mode": "LONG_ONLY",
                    "daily_loss_limit_pct": "5",
                },
                "coins": ({"symbol": "BTCUSDT", "max_allocation_pct": "25"},),
            },
            "history": (),
        },
        research={
            "summaries": (
                {
                    "research_id": "RES-1",
                    "set_id": "SET-CORE",
                    "set_version": "V1",
                    "rules_display_version": "V1",
                    "rules_version_id": "rules-1",
                    "selected_demo_run_id": None,
                    "selected_demo_profit_factor": None,
                    "compare_to_active": "Unavailable",
                    "decision": "NONE",
                    "status": "DRAFT",
                },
            )
        },
        **kwargs,
    )


def test_reference_top_level_navigation_and_forbidden_sections_are_preserved():
    html = _html()

    assert 'class="top-tab' in html
    assert re.search(r'data-page="overview"[\s\S]*?>\s*Overview\s*</button>', html)
    assert re.search(r'data-page="configuration"[\s\S]*?>\s*Trading Configuration\s*</button>', html)
    assert re.search(r'data-page="research"[\s\S]*?>\s*Research\s*</button>', html)
    assert "Position Groups" not in html


def test_reference_desktop_overview_table_and_mobile_overview_shell_are_present():
    html = _html()

    assert '<div class="overview-kpis">' in html
    assert '<tbody id="positions-body"></tbody>' in html
    assert "<th>Current / Exit Price</th>" in html
    assert "<th>Close / Cancel Reason</th>" in html
    assert 'id="tt-mobile-reference"' in html
    assert '<div class="phone">' in html
    assert '<button id="placed-tab"' in html
    assert 'onclick="openFilters()"' in html
    assert 'id="count" class="count">0</span>' in html
    assert 'id="triggertrade-mobile-reference-css"' in html
    assert 'q(".value", node)' in html
    assert 'classList.add("show")' in html
    assert 'activeFilters' in html
    assert 'class="card"' in html


def test_reference_trading_configuration_layout_is_preserved():
    html = _html()

    assert re.search(r'<div class="group-label">\s*Signal Logic\s*</div>', html)
    assert re.search(r'data-config="metrics"[\s\S]*?>\s*Metrics\s*</button>', html)
    assert re.search(r'data-config="triggers"[\s\S]*?>\s*Triggers\s*</button>', html)
    assert re.search(r'data-config="sets"[\s\S]*?>\s*Sets\s*</button>', html)
    assert re.search(r'<div class="group-label">\s*Trading\s*</div>', html)
    assert 'data-config="rules"' in html
    assert "Trading Rules" in html
    assert '<div id="metric-details" class="panel"></div>' in html
    assert "What this metric means" in html
    assert "Data from exchange" in html
    assert "How it is calculated" in html
    assert "Unavailable when" in html
    assert '<div id="trigger-details" class="panel"></div>' in html
    assert '<div id="set-details" class="panel"></div>' in html


def test_reference_research_summary_and_detail_layout_are_preserved():
    html = _html()

    assert '<tbody id="research-summary-body"></tbody>' in html
    assert "<th>Demo PF</th>" in html
    assert "<th>Active PF</th>" in html
    assert "<th>Δ PF</th>" in html
    assert 'id="page-research-detail"' in html
    assert '<tbody id="backtest-body"></tbody>' in html
    assert '<tbody id="demo-body"></tbody>' in html
    assert 'id="compare-table"' in html
    assert 'id="decision-state"' in html


def test_trading_rules_layout_uses_desktop_columns_and_mobile_single_column():
    html = _html()

    assert "#config-rules .rules-stack" in html
    assert "grid-template-columns:minmax(0,3fr) minmax(0,2fr)" in html
    assert "#config-rules .rules-stack>.rules-section:nth-child(1)" in html
    assert "grid-column:1;" in html
    assert "#config-rules .rules-stack>.rules-section:nth-child(2)" in html
    assert "grid-column:2;" in html
    assert "#config-rules .rules-stack>.rules-section:nth-child(3)" in html
    assert "#config-rules .rules-stack>.history-panel" in html
    assert "grid-column:1 / -1;" in html
    assert "#config-rules .rules-stack>.rules-save" in html
    assert "margin:10px 0;" in html
    assert "@media(max-width:760px)" in html
    assert "grid-template-columns:1fr;" in html


def test_trading_rules_coin_editor_uses_pending_allocations_and_existing_save_path():
    html = _html()

    assert "let coinDraftVersion = null, coinDraft = [];" in html
    assert "function rulePayload()" in html
    assert 'position_size_pct: ruleInputValue(body, "Position Size", pr.position_size_pct)' in html
    assert 'take_profit_mode: ruleModeValue(body, "Take Profit", pr.take_profit_mode || "DYNAMIC")' in html
    assert 'direction_mode: directionPayload(ruleSelectValue(body, "Direction", po.direction_mode))' in html
    assert "max_allocation_pct: normalizeCoinAllocation(x.max_allocation_pct)" in html
    assert "coinPayload()" in html
    assert "coins: coinPayload()" in html
    assert "state.rules.coins" in html
    assert "prompt(\"Coin symbol\")" not in html
    assert 'class="coin-add-select"' in html
    assert "availableCoinSymbols()" in html
    assert "Symbol is not available in the supported instrument catalog." in html
    assert '<div class="coin-list">' in html
    assert 'class="coin-row"' in html
    assert 'class="coin-symbol"' in html
    assert 'class="coin-allocation-input js-coin-allocation"' in html
    assert 'class="coin-percent">%</span>' in html
    assert 'class="coin-remove js-remove-coin"' in html
    assert "coinDraft = coinDraft.filter" in html
    assert "#config-rules .coin-allocation-input" in html
    assert "width:84px;" in html
    assert "text-align:right;" in html
    assert "#config-rules .coin-remove" in html
    assert "width:28px;" in html
    assert "height:28px;" in html


def test_trigger_and_set_details_render_full_reference_structure_from_backend_data():
    html = _html()

    assert "What this Trigger means" in html
    assert "How it works" in html
    assert "Unavailable behavior" in html
    assert "Used in Set Versions" in html
    assert "Version History" in html
    assert 'class="reference-link js-open-set"' in html
    assert 'data-set-id="${h(s.set_id)}"' in html
    assert "Trigger Versions Used" in html
    assert "Human-readable Set Logic" in html
    assert "Direction: LONG / SHORT / NONE" in html
    assert "Direction = NONE." in html
    assert 'class="reference-link js-open-trigger"' in html
    assert 'data-trigger-id="${h(t.trigger_id)}"' in html
    assert "This panel renders the exact selected Set Version" in html


def test_backend_wiring_payload_and_visible_controls_are_present_without_token():
    html = _html()

    assert '"total_equity": "1000.00"' in html
    assert '"symbol": "BTCUSDT"' in html
    assert 'id="operatorPauseForm"' in html
    assert 'id="operatorCloseAllForm"' in html
    assert 'data-position-id="${h(r.id)}"' in html
    assert "onclick=\"closePosition('" not in html
    assert 'name="token"' not in html
    assert "/api/research/" in html
    assert "/api/rules/versions" in html
    assert "window.openConfig = function(view)" in html
    assert "window.renderResearchSummary = renderResearchSummary" in html
    assert "window.setCompareScope = function(scope)" in html
    assert "window.setComparePeriod = function(period)" in html
    assert "Compare by ${h(compareScope)} is unavailable until the backend exposes factual segmented comparison dimensions." in html
    assert "Compare period ${h(comparePeriod)} is unavailable until the backend exposes factual period-specific comparison dimensions." in html
    assert 'demo_status || r.selected_demo_status' in html
    assert "const demoState = (r) =>" in html
    assert "demoState(r).replace" in html
    assert "Prototype: Pause Entries" not in html
    assert "onclick=\"action('pause')\"" in html
    assert "onclick=\"action('close')\"" in html


def test_research_reference_actions_are_backend_wired_without_fixture_values():
    html = _html()

    assert "function researchSetOptions()" in html
    assert "function researchRulesOptions()" in html
    assert "function setupNewResearch()" in html
    assert "function setNewResearchState(message)" in html
    assert 'q("#new-set", desktop)' in html
    assert 'q("#new-rules", desktop)' in html
    assert "insertAdjacentElement(\"afterend\", node)" in html
    assert "window.createResearch = async function()" in html
    assert 'postJson("/api/research", {set_id, set_version, rules_version_id})' in html
    assert "window.runBacktest = async function(period)" in html
    assert "research_start:start.toISOString()" in html
    assert "window.runDemo = async function()" in html
    assert "window.setDecision = async function(value)" in html
    assert 'idempotency_key:"ui-"+Date.now()' in html
    assert "<td>R-001</td>" not in html
    assert "BT-012" not in html
    assert "DM-006" not in html
