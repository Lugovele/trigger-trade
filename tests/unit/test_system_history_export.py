from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.persistence import MessageStore
from triggertrade.persistence.operator_state_store import OperatorStateStore
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
        "RISK / DECISIONS",
        "ERRORS",
    ):
        assert section in text
    assert "2026-09-08T12:00:00+00:00" in text
    assert "PAUSE_ENTRIES" in text
    assert "rules_version_id" in text
    assert "triggertrade-futures-core" in text
    assert "RESEARCH" not in text


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

        def get_latest_decision(self):
            return None

    text = SystemHistoryExporter(read_model=GuardedReadModel()).build_export()

    assert "SETS / TRIGGERS" in text
    assert "current_rules_version_id: unavailable" in text
