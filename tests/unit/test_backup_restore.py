from decimal import Decimal
import json
import sqlite3

import pytest

from triggertrade.accounting import EquitySnapshot, FuturesFillEvent
from triggertrade.config import load_config
from triggertrade.execution.contracts import OrderStatus
from triggertrade.execution.futures import PositionState
from triggertrade.persistence import (
    FuturesExecutionRecord,
    FuturesExecutionStore,
    MessageStore,
    OperatorStateStore,
    ResearchStore,
    TraceStore,
    TradingRulesStore,
    TriggerSetStore,
    bootstrap_current_trigger_sets,
)
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.persistence.futures_position_store import FuturesPositionRecord, FuturesPositionStore
from triggertrade.rules import TradingRulesService
from triggertrade.services.backup_restore import BackupRestoreError, BackupService, critical_state_fingerprint
from triggertrade.services.research import ResearchService


def test_create_backup_and_restore_preserves_critical_state_in_isolated_copy(tmp_path):
    db = _seed_operational_db(tmp_path)
    service = BackupService(db, backup_dir=tmp_path / "backups", restore_dir=tmp_path / "restore")
    before = critical_state_fingerprint(db)

    manifest = service.create_backup(created_at="2026-09-09T03:00:00+00:00")
    verification = service.verify_backup(manifest.backup_id)
    restored = service.verify_restore(manifest.backup_id)

    assert manifest.backup_id == "triggertrade-20260909T030000Z"
    assert manifest.integrity_check_result == "ok"
    assert manifest.sha256
    assert manifest.contains_secrets is False
    assert manifest.table_counts["trading_rules_versions"] >= 1
    assert verification.valid is True
    assert verification.checksum_ok is True
    assert restored.restored_path.exists()
    assert restored.restored_path != db
    assert restored.integrity_check_result == "ok"
    assert restored.critical_identity_match is True
    assert restored.source_fingerprint["active_set"] == restored.restored_fingerprint["active_set"]
    assert restored.source_fingerprint["current_rules_version_id"] == restored.restored_fingerprint["current_rules_version_id"]
    assert critical_state_fingerprint(db) == before


def test_list_backups_returns_safe_metadata_newest_first(tmp_path):
    db = _seed_operational_db(tmp_path)
    service = BackupService(db, backup_dir=tmp_path / "backups")

    old = service.create_backup(created_at="2026-09-09T03:00:00+00:00")
    new = service.create_backup(created_at="2026-09-09T03:01:00+00:00")

    backups = service.list_backups()

    assert [item.backup_id for item in backups[:2]] == [new.backup_id, old.backup_id]
    assert all(item.source_db == db.name for item in backups)


def test_concurrent_backup_uses_consistent_sqlite_snapshot(tmp_path):
    db = _seed_operational_db(tmp_path)
    open_conn = sqlite3.connect(db)
    try:
        open_conn.execute(
            """
            INSERT INTO audit_events(
                event_id, created_at, event_type, source_type, source_id, scope,
                entity_type, entity_id, related_entity_type, related_entity_id,
                set_id, set_version, rules_version_id, trigger_id, trigger_version,
                research_id, run_id, position_id, order_id, result, reason_code,
                safe_metadata, schema_version
            )
            VALUES (
                'audit-open-connection', '2026-09-09T03:02:00+00:00', 'OPERATOR_ACTION',
                'SYSTEM', 'unit', 'ACTIVE', 'operator_action', 'open-connection',
                NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                'SUCCESS', NULL, '{}', 'audit-event-v1'
            )
            """
        )
        open_conn.commit()

        manifest = BackupService(db, backup_dir=tmp_path / "backups").create_backup(
            created_at="2026-09-09T03:02:00+00:00"
        )
    finally:
        open_conn.close()

    assert manifest.table_counts["audit_events"] == critical_state_fingerprint(db)["audit_events_count"]


def test_restore_with_open_position_requires_reconciliation_before_entries(tmp_path):
    db = _seed_operational_db(tmp_path, include_open_position=True)
    service = BackupService(db, backup_dir=tmp_path / "backups", restore_dir=tmp_path / "restore")

    manifest = service.create_backup(created_at="2026-09-09T03:03:00+00:00")
    restored = service.verify_restore(manifest.backup_id)

    assert restored.restored_fingerprint["open_positions_count"] == 1
    assert restored.reconciliation_required is True


def test_checksum_mismatch_refuses_restore_without_touching_source(tmp_path):
    db = _seed_operational_db(tmp_path)
    service = BackupService(db, backup_dir=tmp_path / "backups", restore_dir=tmp_path / "restore")
    manifest = service.create_backup(created_at="2026-09-09T03:04:00+00:00")
    before = critical_state_fingerprint(db)

    backup_path = tmp_path / "backups" / f"{manifest.backup_id}.sqlite3"
    with backup_path.open("ab") as handle:
        handle.write(b"tamper")

    with pytest.raises(BackupRestoreError, match="checksum mismatch"):
        service.verify_backup(manifest.backup_id)
    with pytest.raises(BackupRestoreError, match="checksum mismatch"):
        service.restore_to_isolated_copy(manifest.backup_id)
    assert critical_state_fingerprint(db) == before


def test_corrupted_backup_refuses_restore_after_checksum_matches_corrupt_file(tmp_path):
    db = _seed_operational_db(tmp_path)
    service = BackupService(db, backup_dir=tmp_path / "backups", restore_dir=tmp_path / "restore")
    manifest = service.create_backup(created_at="2026-09-09T03:05:00+00:00")
    backup_path = tmp_path / "backups" / f"{manifest.backup_id}.sqlite3"
    backup_path.write_bytes(b"not a sqlite database")
    manifest_path = tmp_path / "backups" / f"{manifest.backup_id}.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["sha256"] = _sha256(backup_path)
    payload["size_bytes"] = backup_path.stat().st_size
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(BackupRestoreError, match="integrity check failed|file is not a database"):
        service.verify_backup(manifest.backup_id)


def test_unknown_or_traversal_backup_ids_are_refused(tmp_path):
    db = _seed_operational_db(tmp_path)
    service = BackupService(db, backup_dir=tmp_path / "backups", restore_dir=tmp_path / "restore")

    with pytest.raises(BackupRestoreError, match="invalid backup id"):
        service.verify_backup("../runtime/triggertrade_paper")
    with pytest.raises(BackupRestoreError, match="invalid restore id"):
        service.restore_to_isolated_copy("triggertrade-20260909T030000Z", restore_id="../active")
    with pytest.raises(BackupRestoreError, match="backup manifest not found"):
        service.verify_backup("triggertrade-20260909T030000Z")


def test_secret_like_material_inside_db_blocks_backup(tmp_path):
    db = _seed_operational_db(tmp_path)
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            INSERT INTO user_messages(
                message_id, created_at, type, severity, title, body, source,
                entity_type, entity_id, is_read, read_at, dedupe_key, expires_at, metadata_json
            ) VALUES (
                'msg_secret', '2026-09-09T03:06:00+00:00', 'ERROR', 'ERROR',
                'unsafe', 'Authorization: Bearer unit-secret', 'unit',
                NULL, NULL, 0, NULL, NULL, NULL, '{}'
            )
            """
        )

    with pytest.raises(BackupRestoreError, match="forbidden secret-like material"):
        BackupService(db, backup_dir=tmp_path / "backups").create_backup(created_at="2026-09-09T03:06:00+00:00")


def _seed_operational_db(tmp_path, *, include_open_position: bool = False):
    db = tmp_path / "triggertrade.sqlite3"
    config = load_config({"TRIGGERTRADE_RUNTIME_DB_PATH": str(db), "TRIGGERTRADE_WATCHLIST": "BTCUSDT"})
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")
    current_rules = TradingRulesService(TradingRulesStore(db)).ensure_initial_version(
        config,
        created_at="2026-09-05T00:00:00+00:00",
    )
    trigger_set = TriggerSetStore(db).get_active_set("BTCUSDT", "1m")
    assert trigger_set is not None

    MessageStore(db).create_message(
        severity="INFO",
        title="Backup fixture",
        body="Operational message",
        source="unit",
        created_at="2026-09-09T03:00:00+00:00",
    )
    OperatorStateStore(db).record_operator_action(
        action="PAUSE_ENTRIES",
        target="ACTIVE",
        result="SUCCESS",
        source="unit",
        changed_at="2026-09-09T03:00:01+00:00",
    )
    research_service = ResearchService(
        store=ResearchStore(db),
        trigger_set_store=TriggerSetStore(db),
        trading_rules_store=TradingRulesStore(db),
        message_store=MessageStore(db),
    )
    research_service.create_research(
        set_id=trigger_set.set_id,
        set_version=trigger_set.version,
        rules_version_id=current_rules.rules_version_id,
        created_at="2026-09-09T03:00:02+00:00",
    )
    execution = FuturesExecutionRecord(
        intent_id="intent-backup",
        risk_decision_id="risk-backup",
        client_order_id="client-backup",
        exchange_order_id="exchange-backup",
        symbol="BTCUSDT",
        category="linear",
        position_action="OPEN_LONG",
        exchange_side="Buy",
        order_type="Limit",
        requested_qty="0.001",
        requested_price="50000",
        leverage="1",
        status=OrderStatus.SUBMITTED,
        created_at="2026-09-09T03:00:03+00:00",
        updated_at="2026-09-09T03:00:03+00:00",
        margin_mode="ISOLATED",
        position_mode="ONE_WAY",
        lane="ACTIVE",
        trigger_set_id=trigger_set.set_id,
        trigger_set_version=trigger_set.version,
    )
    FuturesExecutionStore(db).reserve(execution)
    FuturesAccountingStore(db).record_fill(
        FuturesFillEvent(
            event_id="fill-backup",
            trade_id="trade-backup",
            execution_id=execution.intent_id,
            symbol="BTCUSDT",
            direction=PositionState.LONG,
            action="OPEN",
            quantity=Decimal("0.001"),
            price=Decimal("50000"),
            fee=Decimal("0.01"),
            fee_asset="USDT",
            occurred_at="2026-09-09T03:00:04+00:00",
            trigger_set_id=trigger_set.set_id,
            trigger_set_version=trigger_set.version,
        )
    )
    FuturesAccountingStore(db).record_equity_snapshot(
        EquitySnapshot(
            snapshot_id="equity-backup",
            observed_at="2026-09-09T03:00:05+00:00",
            source="bybit_demo_account",
            wallet_balance=Decimal("100"),
            equity=Decimal("101"),
            available_margin=Decimal("90"),
            used_margin=Decimal("10"),
            unrealized_pnl=Decimal("1"),
            realized_pnl=Decimal("0"),
            running_peak=Decimal("101"),
            drawdown_absolute=Decimal("0"),
            drawdown_percent=Decimal("0"),
            max_drawdown=Decimal("0"),
        )
    )
    TraceStore(db).record_audit_event(
        event_type="ENTRY_REJECTED",
        source_type="RUNTIME",
        source_id="unit",
        scope="ACTIVE",
        entity_type="risk_decision",
        entity_id="risk-rejected",
        result="REJECTED",
        reason_code="unit",
        safe_metadata={"symbol": "BTCUSDT"},
        created_at="2026-09-09T03:00:06+00:00",
    )
    if include_open_position:
        FuturesPositionStore(db).save_open_position(
            FuturesPositionRecord(
                position_id="pos-backup",
                trade_id="trade-backup",
                symbol="BTCUSDT",
                side="LONG",
                status="OPEN",
                opened_at="2026-09-09T03:00:07+00:00",
                closed_at=None,
                entry_price="50000",
                current_qty="0.001",
                initial_qty="0.001",
                leverage="1",
                position_value="50",
                tp_price="50500",
                tp_pct="0.01",
                sl_price="49875",
                sl_pct="0.0025",
                trigger_set_id=trigger_set.set_id,
                trigger_set_version=trigger_set.version,
                strategy_rule_id="STR-001",
                strategy_rule_version="0.1.0",
                risk_rule_version="0.1.0",
                protective_exit_version="fixed-v1",
                evidence_source="unit",
                open_intent_id=execution.intent_id,
                open_risk_decision_id=execution.risk_decision_id,
                open_execution_id=execution.intent_id,
                close_intent_id=None,
                close_risk_decision_id=None,
                close_execution_id=None,
                close_reason=None,
                rule_snapshot={"rules_version_id": current_rules.rules_version_id},
                updated_at="2026-09-09T03:00:07+00:00",
                rules_version_id=current_rules.rules_version_id,
                instrument_snapshot={"symbol": "BTCUSDT", "category": "linear"},
            )
        )
    return db


def _sha256(path):
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
