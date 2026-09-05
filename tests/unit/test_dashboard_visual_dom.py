from triggertrade.dashboard.__main__ import render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from tests.fixtures.triggertrade_v6_visual_fixture import VISUAL_RULE_NAMES, VISUAL_TRIGGER_SETS
from tests.unit.test_dashboard_read_model import _empty_db, _save_buy_lifecycle, _save_no_signal


def test_dashboard_matches_v6_reference_regions(tmp_path):
    db = _empty_db(tmp_path)
    _save_no_signal(db)
    _save_buy_lifecycle(db)

    html = render_dashboard(DashboardReadModel(db))

    assert "toolbar" in html
    assert "tabsbar" in html
    assert 'id="envSwitch"' in html
    assert 'id="liveOverview"' in html
    assert 'id="testOverview"' in html
    assert 'id="rules"' in html
    assert 'id="logs"' in html
    assert 'id="settings"' in html
    assert "drawer-bg" in html
    assert "modal-bg" in html


def test_dashboard_renders_four_kpi_cards_and_reference_tables(tmp_path):
    db = _empty_db(tmp_path)
    html = render_dashboard(DashboardReadModel(db))

    live_section = html.split('id="liveOverview"', 1)[1].split('id="testOverview"', 1)[0]
    test_section = html.split('id="testOverview"', 1)[1].split('id="rules"', 1)[0]

    assert live_section.count('class="card"') == 4
    assert test_section.count('class="card"') == 4
    assert "<th>ID</th><th>Date</th><th>Asset</th><th>Side</th>" in html
    assert "<th>Asset</th><th>Qty</th><th>Avg entry</th>" in html


def test_dashboard_mobile_drawer_modal_and_badges_are_present(tmp_path):
    db = _empty_db(tmp_path)
    html = render_dashboard(DashboardReadModel(db))

    assert "@media(max-width:760px)" in html
    assert ".desktop-table{display:none}" in html
    assert ".mobile-list{display:grid}" in html
    assert "badge live" in html
    assert "badge test" in html
    assert "openSet(" in html
    assert "openFullList(" in html


def test_visual_fixture_values_are_not_production_data(tmp_path):
    db = _empty_db(tmp_path)
    html = render_dashboard(DashboardReadModel(db))

    assert "$12,420.18" not in html
    assert "R-RSI" not in html
    assert "R-MOMENTUM" not in html
    assert "99.98%" not in html
    assert VISUAL_TRIGGER_SETS[1]["status"] == "TESTING"
    assert "RSI threshold" in VISUAL_RULE_NAMES


def test_dashboard_uses_one_shared_horizontal_container(tmp_path):
    db = _empty_db(tmp_path)
    html = render_dashboard(DashboardReadModel(db))

    assert ':root{--bg:' in html
    assert '--page-max:1440px' in html
    assert '--page-pad:22px' in html
    assert '.container{width:100%;max-width:var(--page-max);margin:0 auto;padding-inline:var(--page-pad)}' in html
    assert 'class="container toolbar-inner"' in html
    assert 'class="container tabsbar-inner"' in html
    assert 'class="content container"' in html
    assert 'padding:0 22px' not in html
    assert 'padding:0 12px' not in html
    assert 'padding:10px 22px 18px' not in html
    assert 'padding:8px 10px 12px' not in html
    assert ':root{--page-pad:12px}' in html
