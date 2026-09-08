from triggertrade.dashboard.__main__ import render_dashboard
from triggertrade.dashboard.product_ui import render_product_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from tests.unit.test_dashboard_read_model import _empty_db


def _html(tmp_path, initial_page="portfolio"):
    return render_dashboard(DashboardReadModel(_empty_db(tmp_path)), initial_page=initial_page)


def test_dashboard_uses_approved_product_shell_and_nav(tmp_path):
    html = _html(tmp_path)

    assert 'class="top"' in html
    assert 'class="live-dot"' in html
    assert '>TriggerTrade<' in html
    assert 'class="message-count"' in html
    assert 'title="Messages"' in html
    assert 'title="Copy logs"' in html
    assert 'title="Settings"' in html
    assert 'class="tabsbar"' in html
    assert 'data-page="portfolio"' in html
    assert 'data-page="sets"' in html
    assert 'data-page="rules"' in html
    assert 'data-page="research"' in html
    assert 'data-page="overview"' not in html.lower()
    assert 'data-page="analytics"' not in html.lower()
    assert 'data-page="logs"' not in html.lower()
    assert 'data-page="trading"' not in html.lower()
    assert "UI fixture preview" in html
    assert "non-persistent" in html
    assert "not live trading/account facts" in html


def test_portfolio_matches_open_and_closed_positions_contract(tmp_path):
    html = _html(tmp_path)

    assert 'id="portfolio"' in html
    assert 'Last update' in html
    for label in (
        'Total',
        'Available',
        'In positions',
        'Realized P&L today',
        'Unrealized P&L',
        'Open positions',
    ):
        assert label in html
    for label in ('Coin: All', 'Side: All', 'Set: All'):
        assert f'<option>{label}</option>' in html
    assert '<option>Close reason: All</option>' in html
    assert 'Open</button>' in html
    assert 'Closed</button>' in html
    assert 'id="positionSummary"' in html
    assert 'Open <b>' in html
    assert 'Closed today <b' in html
    for column in (
        'Coin',
        'Side',
        'Leverage',
        'Qty',
        'Value',
        'Entry',
        'Current Price',
        'Take Profit',
        'Stop Loss',
        'Unrealized P&L',
        'Planned TP',
        'Planned SL',
        'Realized P&L',
        'Close reason',
        'Duration',
    ):
        assert column in html
    assert 'Mark</th>' not in html
    assert 'SIGNAL EXIT' not in html


def test_operator_controls_and_confirmations_match_target(tmp_path):
    html = _html(tmp_path)

    assert 'Pause Entries' in html
    assert 'Close All' in html
    assert 'Pause new entries?' in html
    assert 'The bot will stop opening new positions.' in html
    assert 'Type CLOSE ALL to confirm' in html
    assert 'id="operatorPauseForm"' in html
    assert 'action="/operator/pause"' in html
    assert 'id="operatorResumeForm"' in html
    assert 'action="/operator/resume"' in html
    assert 'openSingleClose(' in html
    assert 'openControlModal' in html
    assert '/order/create' not in html
    assert 'manual BUY' not in html
    assert 'manual SELL' not in html


def test_sets_catalog_and_trigger_detail_are_present_and_read_only(tmp_path):
    html = _html(tmp_path)

    assert 'id="sets"' in html
    assert 'Set</th>' in html
    assert 'Version</th>' in html
    assert 'Status</th>' in html
    assert 'Triggers</th>' in html
    assert 'Trigger Catalog' in html
    assert 'id="trigger-catalog"' in html
    assert 'What it checks' in html
    assert 'id="trigger-detail"' in html
    assert 'How it works' in html
    assert 'formula-block' in html
    assert 'Parameters' in html
    assert 'Used in' in html
    assert 'Version history' in html
    assert 'No trigger editing controls' not in html
    assert 'Testing</span>' not in html


def test_sets_and_trigger_catalog_render_backend_registry_not_set_fixtures(tmp_path):
    html = _html(tmp_path, initial_page="sets")
    sets_section = _section(html, 'id="sets"', 'id="trigger-catalog"')
    catalog_section = _section(html, 'id="trigger-catalog"', 'id="trigger-detail"')

    assert "Set 1" not in sets_section
    assert "Set 2" not in sets_section
    assert "triggertrade-futures-core" in html
    assert "triggertrade-futures-candidate" in html
    assert "TRG-001" in html
    assert "TRG-002" in html
    assert "STR-FUT" not in catalog_section
    assert "RSK-FUTURES" not in catalog_section
    assert "TRG-003" not in catalog_section
    assert "Trigger Catalog" in sets_section


def test_trigger_detail_renders_backend_formula_used_in_and_history(tmp_path):
    html = render_dashboard(
        DashboardReadModel(_empty_db(tmp_path)),
        initial_page="trigger-detail",
        selected_trigger_id="TRG-002",
        selected_trigger_version="0.2.0",
    )
    detail_section = _section(html, 'id="trigger-detail"', 'id="rules"')

    assert "Robust Volume Confirmation" in detail_section
    assert "Version 0.2.0" in detail_section
    assert "linear relative_volume &gt;= 2.0 AND volume_percentile &gt;= 90" in detail_section
    assert "lookback_completed_candles" in detail_section
    assert "triggertrade-futures-candidate" in detail_section
    assert "0.1.0" in detail_section
    assert "0.2.0" in detail_section
    assert "Set 1" not in detail_section
    assert "TRG-003" not in detail_section


def test_rules_current_history_and_read_only_version_detail(tmp_path):
    html = _html(tmp_path, initial_page="rules")

    assert 'Current Rules Configuration' in html
    for label in (
        'Position Rules',
        'Portfolio Rules',
        'Coins',
        'Position size',
        'Take Profit mode',
        'Fixed Take Profit',
        'Minimum Take Profit',
        'Stop Loss',
        'Minimum Risk / Reward',
        'Minimum Net Edge',
        'Leverage',
        'Max capital in positions',
        'Max open positions',
        'Max positions per coin',
        'Direction',
        'Daily loss limit',
        'Refresh from exchange',
        'Apply',
        'Save as New Version',
        'Version history',
        'Used in',
    ):
        assert label in html
    assert 'id="rules-version"' in html
    assert 'Rules · v' in html
    assert 'disabled' in html
    assert '>Save<' not in html
    assert '>Update<' not in html


def test_research_pages_modal_runs_compare_and_decision_match_target(tmp_path):
    html = _html(tmp_path, initial_page="research")

    assert 'id="research"' in html
    assert 'New Research' in html
    for column in (
        'Set',
        'Rules',
        'Backtest Profit Factor',
        'Demo Profit Factor',
        'Compare to Active',
        'Decision',
    ):
        assert column in html
    assert 'id="newResearchModal"' in html
    assert 'Trigger Set' in html
    assert 'Rules version' in html
    assert 'Create Research' in html
    assert 'id="researchDetail"' in html
    assert 'Backtest' in html
    assert 'Demo' in html
    assert 'Compare' in html
    assert 'Run Backtest' in html
    assert 'Stop Demo' in html or 'Run' in html
    for column in ('Run', 'Status', 'Period', 'Trades', 'Net P/L', 'Win Rate', 'Profit Factor', 'Max Drawdown', 'Use'):
        assert column in html
    assert 'Research Demo' in html
    assert 'Active' in html
    assert 'Difference' in html
    assert 'Archive' in html
    assert 'Make Active' in html
    assert 'Forward Test' not in html
    assert 'forward-test' not in html
    assert 'researchWizard' not in html


def test_messages_copy_and_mobile_structure_are_present(tmp_path):
    html = _html(tmp_path, initial_page="messages")

    assert 'id="messages"' in html
    assert 'Messages' in html
    assert 'openMessages' in html
    assert 'openMessages' in html
    assert 'copySystemHistory' in html
    assert 'TriggerTrade system history export' in html
    assert '@media(max-width:760px)' in html
    assert '@media(max-width:620px)' in html
    assert '.tablewrap{overflow:auto}' in html
    assert '.tabsbar{position:sticky' in html
    assert '.top{position:sticky' in html


def test_dashboard_uses_attached_html_shared_container_without_secret_leakage(tmp_path):
    html = _html(tmp_path)

    assert '--page:1460px' in html
    assert '--pad:22px' in html
    assert '.container{max-width:var(--page);margin:0 auto;padding:0 var(--pad)}' in html
    assert 'class="container topin"' in html
    assert 'class="container tabs"' in html
    assert '<main class="container">' in html
    assert 'BYBIT_API_KEY' not in html
    assert 'BYBIT_API_SECRET' not in html
    assert 'Authorization' not in html
    assert '.env' not in html
    assert 'https://api-demo.bybit.com' not in html


def test_operator_state_is_allowlisted_before_js_injection():
    class CorruptedState:
        state = 'TRADING_PAUSED";alert(1);//'

    html = render_product_dashboard(operator_state=CorruptedState(), operator_control_token="tok")

    assert 'TRADING_PAUSED";alert(1);//' not in html
    assert 'const operatorState = "TRADING_ENABLED";' in html


def _section(html: str, start: str, end: str) -> str:
    start_index = html.index(start)
    end_index = html.index(end, start_index + len(start))
    return html[start_index:end_index]
