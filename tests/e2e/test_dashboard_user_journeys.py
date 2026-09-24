from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
import threading

import pytest

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright

from triggertrade.dashboard.__main__ import create_server
from triggertrade.persistence import FuturesClosedPositionRecord, FuturesPositionStore, TradingRulesStore
from triggertrade.rules import TradingRulesService
from triggertrade.services.operator_auth import OperatorCommandAuthorizer
from tests.unit.test_dashboard_read_model import _empty_db, _position_record
from tests.unit.test_instrument_catalog import _catalog_service
from tests.unit.test_trading_rules_registry import _config


@pytest.fixture()
def dashboard_base_url(tmp_path):
    db = _empty_db(tmp_path)
    catalog = _catalog_service(tmp_path, db_path=db)
    rules = TradingRulesService(TradingRulesStore(db), symbol_validator=catalog.validate_symbol)
    rules.ensure_initial_version(_config(db), created_at="2026-09-07T00:00:00+00:00")

    positions = FuturesPositionStore(db)
    positions.save_open_position(_position_record("pos-btc-e2e", "trade-btc-e2e", "BTCUSDT", "LONG", "ACTIVE"))
    now = datetime.now(UTC)
    positions.save_closed_position(
        FuturesClosedPositionRecord(
            trade_id="trade-eth-e2e",
            position_id="pos-eth-e2e",
            symbol="ETHUSDT",
            direction="SHORT",
            entry_vwap="2000",
            exit_vwap="1980",
            qty="0.5",
            position_value="1000.00",
            leverage="2",
            planned_tp_pct="0.02",
            planned_tp_price="1960",
            planned_sl_pct="0.01",
            planned_sl_price="2020",
            realized_pnl_pct="1.00",
            gross_pnl="10.00",
            fees="0.50",
            funding="0",
            net_pnl="9.50",
            opened_at=(now - timedelta(hours=2)).isoformat(),
            closed_at=(now - timedelta(hours=1)).isoformat(),
            duration_seconds=3600,
            close_reason="TAKE_PROFIT",
            trigger_set_id="triggertrade-futures-core",
            trigger_set_version="v1",
            strategy_rule_id="STR-FUTURES",
            strategy_rule_version="0.1.0",
            risk_rule_version="futures-position-risk-v1",
            evidence_source="ACTIVE",
            accounting_version="futures-accounting-v1",
            rules_version_id="rules-v1",
        )
    )

    server = create_server(
        port=0,
        db_path=db,
        trading_rules_service=rules,
        instrument_catalog_service=catalog,
        operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@contextmanager
def chromium_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        try:
            yield page
        finally:
            browser.close()


def test_e2e_overview_tabs_filters_periods_and_operator_feedback(dashboard_base_url):
    with chromium_page() as page:
        page.goto(f"{dashboard_base_url}/overview", wait_until="domcontentloaded")
        desktop = page.locator("#tt-desktop-reference")

        desktop.locator("#open-tab").click()
        assert desktop.locator(".positions-tab.active").inner_text() == "Open"
        assert "BTCUSDT" in desktop.locator("#positions-body").inner_text()

        assert desktop.locator("#filter-side").locator("option").all_text_contents() == ["Side: All", "LONG", "SHORT"]
        assert desktop.locator("#filter-status").locator("option").all_text_contents() == ["Status: All", "OPENED", "CLOSED"]

        desktop.locator("#history-tab").click()
        assert desktop.locator(".positions-tab.active").inner_text() == "History"
        assert "ETHUSDT" in desktop.locator("#positions-body").inner_text()
        desktop.locator(".range-btn").filter(has_text="7D").click()
        assert desktop.locator(".range-btn.active").inner_text() == "7D"
        for label in ("30D", "90D", "24H"):
            desktop.locator(".range-btn").filter(has_text=label).click()
            assert desktop.locator(".range-btn.active").inner_text() == label

        desktop.locator("#filter-coin").select_option(label="ETHUSDT")
        assert "ETHUSDT" in desktop.locator("#positions-body").inner_text()

        desktop.locator("button", has_text="Pause Entries").click()
        with page.expect_response(lambda response: response.url.endswith("/operator/pause") and response.status == 303):
            desktop.locator(".js-confirm-operator-command").click()
        page.wait_for_function(
            "() => document.querySelector('#tt-desktop-reference #operatorCommandStatus')?.innerText === 'Entries paused.'"
        )
        assert desktop.locator("#operatorCommandStatus").inner_text() == "Entries paused."

        desktop.locator("#filter-coin").select_option(value="")
        desktop.locator("#open-tab").click()
        desktop.locator(".js-close-position").click()
        with page.expect_response(lambda response: response.url.endswith("/operator/close-one") and response.status == 503):
            desktop.locator(".js-confirm-operator-command").click()
        page.wait_for_function(
            "() => document.querySelector('#tt-desktop-reference #operatorCommandStatus')?.innerText.includes('execution bridge is not attached')"
        )
        assert "execution bridge is not attached" in desktop.locator("#operatorCommandStatus").inner_text()

        desktop.locator("button", has_text="Close All").click()
        with page.expect_response(lambda response: response.url.endswith("/operator/close-all") and response.status == 503):
            desktop.locator(".js-confirm-operator-command").click()
        page.wait_for_function(
            "() => document.querySelector('#tt-desktop-reference #operatorCommandStatus')?.innerText.includes('execution bridge is not attached')"
        )
        assert "execution bridge is not attached" in desktop.locator("#operatorCommandStatus").inner_text()


def test_e2e_rules_searchable_coin_editor_and_save_version(dashboard_base_url):
    with chromium_page() as page:
        page.goto(f"{dashboard_base_url}/rules", wait_until="domcontentloaded")
        desktop = page.locator("#tt-desktop-reference")
        desktop.locator('[data-config="rules"]').click()

        desktop.locator(".rule-row").filter(has_text="Position Size").locator("input").first.fill("2.00")
        desktop.locator(".rule-row").filter(has_text="Max Open Positions").locator("input").first.fill("4")

        desktop.locator(".js-add-coin").click()
        desktop.locator(".coin-search-input").fill("doge")
        desktop.locator(".js-add-coin").click()
        assert desktop.locator(".coin-search-error").inner_text() == "Symbol is not available in the supported instrument catalog."

        desktop.locator(".coin-search-input").fill("sol")
        page.keyboard.press("Enter")
        assert "SOLUSDT" in desktop.locator(".coin-symbol").all_text_contents()
        desktop.locator('.coin-row[data-symbol="SOLUSDT"] .coin-allocation-input').fill("20.00")
        assert desktop.locator('.coin-row[data-symbol="SOLUSDT"] .coin-allocation-input').input_value() == "20.00"
        desktop.locator('.coin-row[data-symbol="SOLUSDT"] .coin-remove').click()
        assert "SOLUSDT" not in desktop.locator(".coin-symbol").all_text_contents()

        desktop.locator(".js-add-coin").click()
        desktop.locator(".coin-search-input").fill("sol")
        desktop.locator(".coin-search-option", has_text="SOLUSDT").click()
        desktop.locator('.coin-row[data-symbol="SOLUSDT"] .coin-allocation-input').fill("20.00")
        with page.expect_response(lambda response: response.url.endswith("/api/rules/versions") and response.status == 201):
            desktop.locator(".save-btn").click()
        assert desktop.locator(".rules-save-state").inner_text() == "Saved as new version."
        assert "v2" in desktop.locator(".history-panel").inner_text()


def test_e2e_research_create_detail_backtest_demo_compare_export_and_reject(dashboard_base_url):
    with chromium_page() as page:
        page.goto(f"{dashboard_base_url}/research", wait_until="domcontentloaded")
        desktop = page.locator("#tt-desktop-reference")

        desktop.locator("button", has_text="+ New Research").click()
        assert desktop.locator("#new-research-modal.show").count() == 1
        desktop.locator("button", has_text="Create Research").click()
        desktop.locator("#research-detail-title").wait_for()
        assert "/research/" in page.url

        desktop.locator("button", has_text="Run 7D").click()
        page.wait_for_timeout(500)
        assert "rbt-" in desktop.locator("#backtest-body").inner_text()

        desktop.locator("button", has_text="Run Demo 7D").click()
        page.wait_for_timeout(300)
        assert "rdm-" in desktop.locator("#demo-body").inner_text()

        desktop.locator("button", has_text="By Coin").click()
        assert desktop.locator(".compare-tab.active").inner_text() == "By Coin"

        with page.expect_download(timeout=5000) as download:
            desktop.locator('button[onclick="exportResearch()"]').click()
        assert download.value.suggested_filename.endswith("-research.json")

        desktop.locator("button", has_text="Reject").click()
        page.wait_for_timeout(500)
        assert (desktop.locator("#decision-state").or_(desktop.locator("#decisionStateInline"))).inner_text() in {
            "ARCHIVE",
            "ARCHIVED",
            "REJECT",
        }


def test_e2e_trigger_metric_set_exact_version_navigation(dashboard_base_url):
    with chromium_page() as page:
        page.goto(f"{dashboard_base_url}/rules", wait_until="domcontentloaded")
        desktop = page.locator("#tt-desktop-reference")

        desktop.locator('[data-config="triggers"]').click()
        desktop.locator("#config-triggers tbody tr.catalog-row").first.click()
        trigger_title = desktop.locator("#triggerDetail .details-title, #trigger-details .details-title").inner_text()
        assert trigger_title

        desktop.locator("#triggerDetail .reference-link, #trigger-details .reference-link").first.click()
        assert desktop.locator(".config-tab.active").inner_text() == "Metrics"
        assert desktop.locator("#metricDetail .details-title, #metric-details .details-title").inner_text()

        desktop.locator('[data-config="triggers"]').click()
        desktop.locator("#config-triggers tbody tr.catalog-row").first.click()
        desktop.locator("#triggerDetail .js-open-set, #trigger-details .js-open-set").first.click()
        assert desktop.locator(".config-tab.active").inner_text() == "Sets"
        assert "Set " in desktop.locator("#setDetail .details-id, #set-details .details-id").inner_text()

        desktop.locator("#config-sets tbody tr.catalog-row").first.click()
        desktop.locator("#setDetail .reference-link, #set-details .reference-link").first.click()
        assert desktop.locator(".config-tab.active").inner_text() == "Triggers"
        assert "Trigger " in desktop.locator("#triggerDetail .details-id, #trigger-details .details-id").inner_text()
