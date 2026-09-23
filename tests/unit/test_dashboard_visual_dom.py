from pathlib import Path
from uuid import uuid4

from triggertrade.dashboard.__main__ import render_dashboard
from triggertrade.dashboard.product_ui import render_product_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from tests.unit.test_dashboard_read_model import _empty_db


def _tmpdir():
    path = Path(".tt-tmp") / f"visual-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _html(initial_page="overview"):
    return render_dashboard(DashboardReadModel(_empty_db(_tmpdir())), initial_page=initial_page)


def test_dashboard_uses_final_three_area_navigation():
    html = _html()

    assert ">TriggerTrade<" in html
    assert 'data-page="overview"' in html
    assert 'data-page="config"' in html
    assert 'data-page="research"' in html
    assert ">Overview</button>" in html
    assert ">Trading Configuration</button>" in html
    assert ">Research</button>" in html
    assert 'data-page="portfolio"' not in html
    assert 'data-page="sets"' not in html
    assert 'data-page="rules"' not in html


def test_overview_matches_final_positions_contract():
    html = _html()

    assert 'id="overview"' in html
    for label in (
        "Total Equity",
        "Available",
        "In Positions",
        "Realized P&L Today",
        "Unrealized P&L",
        "Open Positions",
    ):
        assert label in html
    for label in (
        "Placed",
        "Open",
        "History",
        "Pause Entries",
        "Close All",
        "24H",
        "7D",
        "30D",
        "90D",
        "Export History",
    ):
        assert label in html
    for column in (
        "Time",
        "Coin",
        "Side",
        "Status",
        "Qty",
        "Value",
        "Entry",
        "Current / Exit Price",
        "Take Profit",
        "Stop Loss",
        "P&L",
        "Set",
        "Age",
        "Close / Cancel Reason",
        "Action",
    ):
        assert column in html


def test_mobile_overview_controls_are_present():
    html = _html()

    assert "@media(max-width:760px)" in html
    assert "Filters <span" in html
    assert ">Actions</button>" in html
    assert 'id="filtersSheet"' in html
    assert 'id="actionsSheet"' in html
    assert "Last 24H" in html


def test_trading_configuration_sections_are_present():
    html = _html(initial_page="config")

    assert "Signal Logic" in html
    assert "Metrics" in html
    assert "Triggers" in html
    assert "Sets" in html
    assert "Trading Rules" in html
    assert "Position Rules" in html
    assert "Portfolio Rules" in html
    assert "Coins" in html
    assert "Save as New Version" in html
    assert "Version History" in html


def test_research_summary_and_standalone_detail_are_present():
    html = _html(initial_page="research")

    assert 'id="research"' in html
    assert 'id="research-detail"' in html
    assert "+ New Research" in html
    for label in (
        "Research",
        "Set",
        "Rules",
        "Demo",
        "Demo PF",
        "Active PF",
        "Δ PF",
        "Decision",
        "Run 7D",
        "Run 30D",
        "Run 90D",
        "Run Demo 7D",
        "Overall",
        "By Segment",
        "By Coin",
        "By Direction",
        "Reject",
        "Make Active",
        "Export",
    ):
        assert label in html


def test_product_ui_source_has_no_legacy_production_fixture_state():
    source = Path("src/triggertrade/dashboard/product_ui.py").read_text(encoding="utf-8-sig")

    forbidden = (
        "openRows = [",
        "closedRows = [",
        "researchRows",
        "rulesVersions =",
        "mockRefreshSymbols",
        "$3,436",
        "BTCUSDT is approaching its configured Stop Loss level.",
        "No critical account issues detected.",
        "R-001",
        "BT-012",
        "DM-006",
        "Forward Test",
        "manual BUY",
        "manual SELL",
    )
    for text in forbidden:
        assert text not in source


def test_dashboard_does_not_leak_secret_names():
    html = _html()

    assert "BYBIT_API_KEY" not in html
    assert "BYBIT_API_SECRET" not in html
    assert "Authorization" not in html
    assert "https://api-demo.bybit.com" not in html
    assert "/order/create" not in html


def test_operator_state_is_allowlisted_before_js_injection():
    class CorruptedState:
        state = 'TRADING_PAUSED";alert(1);//'

    html = render_product_dashboard(operator_state=CorruptedState(), operator_control_token="tok")

    assert 'TRADING_PAUSED";alert(1);//' not in html
    assert '"operatorState": "UNKNOWN"' in html
    assert '"operatorStateAvailable": false' in html
    assert "State unavailable" in html
    assert "process-secret-token" not in render_product_dashboard(
        operator_control_token="process-secret-token",
        operator_command_submit_enabled=True,
    )
