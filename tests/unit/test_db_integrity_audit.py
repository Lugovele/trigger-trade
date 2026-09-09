import sqlite3

from triggertrade.config import load_config
from triggertrade.persistence import MessageStore, ResearchStore, TradingRulesStore, TriggerSetStore, bootstrap_current_trigger_sets
from triggertrade.persistence.instrument_catalog_store import InstrumentCatalogStore
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.persistence.runtime_store import LaneCandleLifecycle, RuntimeStore
from triggertrade.rules import TradingRulesService
from triggertrade.services.backup_restore import BackupService
from triggertrade.services.db_integrity_audit import (
    RETENTION_PERMANENT_EVIDENCE,
    RETENTION_RECONSTRUCTABLE_CACHE,
    run_database_integrity_audit,
)
from triggertrade.services.research import ResearchService


def test_database_integrity_audit_passes_seeded_runtime_db(tmp_path):
    db = _seed_db(tmp_path)

    audit = run_database_integrity_audit(db)

    assert audit.integrity_check == "ok"
    assert audit.foreign_key_check_count == 0
    assert audit.passed is True
    by_table = {table.table: table for table in audit.tables}
    assert by_table["trading_rules_versions"].retention_class == RETENTION_PERMANENT_EVIDENCE
    assert by_table["futures_instrument_catalog"].retention_class == RETENTION_RECONSTRUCTABLE_CACHE


def test_database_integrity_audit_detects_dangling_research_rules_reference(tmp_path):
    db = _seed_db(tmp_path)
    active = TriggerSetStore(db).get_active_set("BTCUSDT", "1m")
    assert active is not None
    current_rules = TradingRulesStore(db).get_current()
    assert current_rules is not None
    research = ResearchService(
        store=ResearchStore(db),
        trigger_set_store=TriggerSetStore(db),
        trading_rules_store=TradingRulesStore(db),
        message_store=MessageStore(db),
    ).create_research(
        set_id=active.set_id,
        set_version=active.version,
        rules_version_id=current_rules.rules_version_id,
        created_at="2026-09-09T03:00:00+00:00",
    )
    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE research_entities SET rules_version_id = 'missing-rules-version' WHERE research_id = ?",
            (research.research_id,),
        )

    audit = run_database_integrity_audit(db)
    check = _check(audit.orphan_checks, "research_rules_versions_resolve")

    assert audit.passed is False
    assert check.status == "FAIL"
    assert check.count == 1


def test_database_integrity_audit_detects_unknown_enums_and_bad_timestamps(tmp_path):
    db = _seed_db(tmp_path)
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE trigger_set_versions SET status = 'ALIEN' WHERE set_id = 'triggertrade-futures-core'")
        conn.execute("UPDATE trading_rules_versions SET created_at = 'not-a-timestamp'")

    audit = run_database_integrity_audit(db)

    assert _check(audit.enum_checks, "set_status_known").status == "FAIL"
    assert any(item.name == "trading_rules_versions.created_at.interpretable" and item.status == "FAIL" for item in audit.timestamp_checks)


def test_database_integrity_audit_query_plans_use_growth_indexes(tmp_path):
    db = _seed_db(tmp_path)
    RuntimeStore(db).save_lane_lifecycle(
        LaneCandleLifecycle(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            candle_id="BTCUSDT:1m:2026-09-09T03:00:00+00:00",
            candle_open_time="2026-09-09T03:00:00+00:00",
            trigger_set_id="triggertrade-futures-core",
            trigger_set_version="v1",
            status="no_signal",
            processed_at="2026-09-09T03:01:00+00:00",
        )
    )

    audit = run_database_integrity_audit(db)
    plans = {item.name: item for item in audit.query_plan_findings}

    assert plans["latest_equity_snapshot"].status == "PASS"
    assert plans["latest_runtime_lane"].status == "PASS"
    assert plans["research_backtest_runs"].status == "PASS"


def test_database_integrity_audit_preserves_backup_service_compatibility(tmp_path):
    db = _seed_db(tmp_path)
    service = BackupService(db, backup_dir=tmp_path / "backups", restore_dir=tmp_path / "restore")

    manifest = service.create_backup(created_at="2026-09-09T03:30:00+00:00")
    restored = service.verify_restore(manifest.backup_id)

    assert restored.critical_identity_match is True
    assert run_database_integrity_audit(restored.restored_path).passed is True


def _seed_db(tmp_path):
    db = tmp_path / "integrity.sqlite3"
    config = load_config({"TRIGGERTRADE_RUNTIME_DB_PATH": str(db), "TRIGGERTRADE_WATCHLIST": "BTCUSDT"})
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")
    TradingRulesService(TradingRulesStore(db)).ensure_initial_version(config, created_at="2026-09-05T00:00:00+00:00")
    FuturesAccountingStore(db)
    RuntimeStore(db)
    ResearchStore(db)
    InstrumentCatalogStore(db)
    return db


def _check(items, name):
    return next(item for item in items if item.name == name)
