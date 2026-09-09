from decimal import Decimal

from triggertrade.accounting import EquitySnapshot
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.config import load_config
from triggertrade.persistence import LaneCandleLifecycle, MessageStore, RuntimeStore, TradingRulesStore
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.rules import TradingRulesService
from triggertrade.persistence.operator_state_store import OperatorStateStore
from triggertrade.services.research import ResearchService
from triggertrade.services.system_history import SystemHistoryExporter
from tests.unit.test_dashboard_read_model import _empty_db, _save_buy_lifecycle


def test_system_history_export_contains_factual_sections_without_research_fabrication(tmp_path):
    db = _empty_db(tmp_path)
    _save_buy_lifecycle(db)
    operator_store = OperatorStateStore(db)
    operator_store.record_operator_action(action="PAUSE_ENTRIES", target="ACTIVE", result="SUCCESS", source="unit")

    text = SystemHistoryExporter(
        read_model=DashboardReadModel(db),
        operator_store=operator_store,
        message_store=MessageStore(db),
    ).build_export(generated_at="2026-09-08T12:00:00+00:00")

    for section in (
        "SYSTEM",
        "PORTFOLIO",
        "EXECUTION",
        "SETS / TRIGGERS",
        "RULES",
        "INSTRUMENTS",
        "RESEARCH",
        "RISK / DECISIONS",
        "ERRORS",
    ):
        assert section in text
    assert "2026-09-08T12:00:00+00:00" in text
    assert "PAUSE_ENTRIES" in text
    assert "rules_version_id" in text
    assert "triggertrade-futures-core" in text
    assert "research: " not in text
    assert "none_available: true" in text


def test_system_history_export_includes_allowlisted_daily_loss_state(tmp_path):
    db = _empty_db(tmp_path)
    config = load_config({"TRIGGERTRADE_RUNTIME_DB_PATH": str(db), "TRIGGERTRADE_WATCHLIST": "BTCUSDT", "TRIGGERTRADE_RUNTIME_SYMBOL": "BTCUSDT"})
    rules = TradingRulesService(TradingRulesStore(db))
    rules.ensure_initial_version(config)
    rules.create_rules_version_from_current(
        changes={"daily_loss_limit_enabled": True, "daily_loss_limit_pct": Decimal("0.02")},
        created_source="unit",
        created_at="2026-09-05T00:00:00+00:00",
    )
    FuturesAccountingStore(db).record_equity_snapshot(
        EquitySnapshot(
            snapshot_id="daily-loss-export-equity",
            observed_at="2026-09-08T00:00:01+00:00",
            source="exchange_wallet",
            wallet_balance=Decimal("100"),
            equity=Decimal("100"),
            available_margin=Decimal("100"),
            used_margin=Decimal("0"),
            unrealized_pnl=Decimal("0"),
            realized_pnl=Decimal("0"),
            running_peak=Decimal("100"),
            drawdown_absolute=Decimal("0"),
            drawdown_percent=Decimal("0"),
            max_drawdown=Decimal("0"),
        )
    )

    text = SystemHistoryExporter(read_model=DashboardReadModel(db)).build_export(generated_at="2026-09-08T12:00:00+00:00")

    assert "daily_loss:" in text
    assert "baseline_equity=100" in text
    assert "limit_amount=2.00" in text
    assert "raw" not in text
    assert "RESEARCH" in text


def test_system_history_export_includes_bounded_factual_research(tmp_path):
    from triggertrade.persistence import MessageStore, ResearchStore, TriggerSetStore, bootstrap_current_trigger_sets

    db = _empty_db(tmp_path)
    bootstrap_current_trigger_sets(TriggerSetStore(db))
    config = load_config({"TRIGGERTRADE_RUNTIME_DB_PATH": str(db), "TRIGGERTRADE_WATCHLIST": "BTCUSDT", "TRIGGERTRADE_RUNTIME_SYMBOL": "BTCUSDT"})
    rules = TradingRulesService(TradingRulesStore(db))
    current = rules.ensure_initial_version(config)
    service = ResearchService(
        store=ResearchStore(db),
        trigger_set_store=TriggerSetStore(db),
        trading_rules_store=TradingRulesStore(db),
        message_store=MessageStore(db),
    )
    record = service.create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=current.rules_version_id,
        created_at="2026-09-08T12:00:00+00:00",
    )
    service.request_make_active(record.research_id)

    text = SystemHistoryExporter(read_model=DashboardReadModel(db)).build_export()

    assert "RESEARCH" in text
    assert record.research_id in text
    assert "triggertrade-futures-candidate" in text
    assert "active_pair:" in text
    assert "source_research_id" in text
    assert current.rules_version_id in text
    assert "Research backend" not in text


def test_system_history_export_includes_checkpoint_recovery_evidence(tmp_path):
    db = _empty_db(tmp_path)
    MessageStore(db).create_message(
        severity="INFO",
        title="Runtime checkpoint recovery completed",
        body="Futures runtime recovered 5 completed candle(s).",
        source="futures_runtime",
        entity_type="runtime_checkpoint",
        entity_id="triggertrade-futures-core:v1",
        dedupe_key="checkpoint-recovery-completed:unit",
        created_at="2026-09-08T12:06:00+00:00",
    )
    RuntimeStore(db).save_lane_lifecycle(
        LaneCandleLifecycle(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            candle_id="BTCUSDT:1m:2026-09-08T12:04:00+00:00",
            candle_open_time="2026-09-08T12:04:00+00:00",
            trigger_set_id="triggertrade-futures-core",
            trigger_set_version="v1",
            status="stale_entry_suppressed",
            processed_at="2026-09-08T12:05:01+00:00",
            error="recovery_backfill_no_stale_execution",
        )
    )

    text = SystemHistoryExporter(read_model=DashboardReadModel(db)).build_export()

    assert "runtime_recovery:" in text
    assert "stale_entry_suppressed" in text
    assert "recovery_backfill_no_stale_execution" in text
    assert "Runtime checkpoint recovery completed" in text


def test_system_history_export_sanitizes_secret_like_values(tmp_path):
    db = _empty_db(tmp_path)
    store = MessageStore(db)
    store.create_message(
        severity="ERROR",
        title="unsafe",
        body="Authorization: Bearer unit-token",
        source="unit",
        metadata={"cookie": "session=secret", "symbol": "BTCUSDT"},
    )
    operator_store = OperatorStateStore(db)
    operator_store.record_operator_action(
        action="CLOSE_ONE",
        target="pos-1",
        result="FAILED",
        source="unit",
        error="BYBIT_API_SECRET=unit-signing-value",
    )

    text = SystemHistoryExporter(
        read_model=DashboardReadModel(db),
        operator_store=operator_store,
        message_store=store,
    ).build_export()

    assert "unit-token" not in text
    assert "session=secret" not in text
    assert "unit-signing-value" not in text
    assert "[redacted]" in text


def test_system_history_export_is_bounded_and_marks_truncation(tmp_path):
    db = _empty_db(tmp_path)
    store = MessageStore(db)
    for index in range(40):
        store.create_message(
            severity="ERROR",
            title=f"Error {index}",
            body=f"Failure {index}",
            source="unit",
            created_at=f"2026-09-08T12:{index:02d}:00+00:00",
        )

    text = SystemHistoryExporter(
        read_model=DashboardReadModel(db),
        operator_store=OperatorStateStore(db),
        message_store=store,
    ).build_export()

    assert "message_truncated: true; showing latest 30" in text
    assert "Error 39" in text
    assert "Error 0" not in text


def test_system_history_export_reads_operator_actions_with_storage_limit(tmp_path):
    class GuardedOperatorStore:
        def operator_action_rows(self, *, limit=None):
            assert limit == 31
            return ()

    db = _empty_db(tmp_path)

    text = SystemHistoryExporter(
        read_model=DashboardReadModel(db),
        operator_store=GuardedOperatorStore(),
        message_store=MessageStore(db),
    ).build_export()

    assert "EXECUTION" in text


def test_system_history_export_requests_bounded_registry_and_rules_reads():
    class GuardedReadModel:
        def get_latest_runtime_state(self):
            return None

        def get_operator_trading_state(self):
            return None

        def get_portfolio_snapshot(self):
            return None

        def list_portfolio_open_positions(self, *, limit=None):
            return ()

        def list_portfolio_closed_positions(self, *, limit=None):
            return ()

        def list_recent_activity(self, *, limit=None):
            return ()

        def list_set_summaries(self, *, limit=None):
            assert limit == 13
            return ()

        def list_trigger_catalog(self, *, limit=None):
            assert limit == 21
            return ()

        def get_current_rules_version_payload(self):
            return None

        def list_rules_version_payloads(self, *, limit=None):
            assert limit == 13
            return ()

        def get_rules_catalog_state(self):
            return None

        def list_research_summaries(self, *, limit=None):
            assert limit == 21
            return ()

        def get_latest_decision(self):
            return None

    text = SystemHistoryExporter(read_model=GuardedReadModel()).build_export()

    assert "SETS / TRIGGERS" in text
    assert "current_rules_version_id: unavailable" in text
