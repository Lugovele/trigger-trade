"""SQLite-safe operational backup and isolated restore verification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import time
from contextlib import closing
from typing import Any

from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.persistence import (
    MessageStore,
    OperatorStateStore,
    ResearchStore,
    RuntimeStore,
    TraceStore,
    TradingRulesStore,
    TriggerSetStore,
)
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.persistence.futures_execution_store import FuturesExecutionStore
from triggertrade.persistence.futures_position_store import FuturesPositionStore
from triggertrade.services.system_history import SystemHistoryExporter


BACKUP_SCHEMA_VERSION = "triggertrade-backup-v1"
DEFAULT_BACKUP_DIR = Path("backups")
DEFAULT_RESTORE_DIR = Path(".tmp") / "restore-verification"
_BACKUP_ID_RE = re.compile(r"^triggertrade-\d{8}T\d{6}Z(?:-[A-Za-z0-9_-]{1,24})?$")
_RESTORE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,120}$")
_SECRET_VALUE_RE = re.compile(
    r"("
    r"api[_-]?key|api[_-]?secret|authorization|bearer|cookie|csrf|session|"
    r"password|credential|signature|private[_-]?key|\.env"
    r")\s*[:=]",
    re.I,
)


class BackupRestoreError(RuntimeError):
    """Raised when backup or restore verification cannot proceed safely."""


@dataclass(frozen=True)
class BackupManifest:
    backup_id: str
    created_at: str
    source_db: str
    source_schema_version: str | None
    source_app_commit: str | None
    backup_file: str
    size_bytes: int
    sha256: str
    integrity_check_result: str
    table_counts: dict[str, int]
    duration_ms: int
    contains_secrets: bool
    secret_findings: tuple[str, ...]
    schema_version: str = BACKUP_SCHEMA_VERSION


@dataclass(frozen=True)
class BackupVerification:
    backup_id: str
    backup_path: Path
    manifest_path: Path
    checksum_ok: bool
    integrity_check_result: str
    contains_secrets: bool
    table_counts: dict[str, int]
    valid: bool


@dataclass(frozen=True)
class RestoreVerification:
    backup_id: str
    restored_path: Path
    integrity_check_result: str
    critical_identity_match: bool
    source_fingerprint: dict[str, Any]
    restored_fingerprint: dict[str, Any]
    system_history_generated: bool
    reconciliation_required: bool


class BackupService:
    """Create verified runtime DB backups and restore them only to isolated copies."""

    def __init__(
        self,
        source_db_path: str | Path,
        *,
        backup_dir: str | Path = DEFAULT_BACKUP_DIR,
        restore_dir: str | Path = DEFAULT_RESTORE_DIR,
        app_commit: str | None = None,
    ) -> None:
        self.source_db_path = Path(source_db_path)
        self.backup_dir = Path(backup_dir)
        self.restore_dir = Path(restore_dir)
        self.app_commit = app_commit

    def create_backup(self, *, created_at: str | None = None, suffix: str | None = None) -> BackupManifest:
        if not self.source_db_path.exists():
            raise BackupRestoreError("source runtime database not found")
        created_at = created_at or datetime.now(UTC).replace(microsecond=0).isoformat()
        backup_id = _backup_id(created_at, suffix)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = self._backup_path(backup_id)
        manifest_path = self._manifest_path(backup_id)
        if backup_path.exists() or manifest_path.exists():
            raise BackupRestoreError("backup already exists")

        start = time.perf_counter()
        with closing(sqlite3.connect(self.source_db_path)) as source:
            source.row_factory = sqlite3.Row
            integrity = _integrity_check(source)
            with closing(sqlite3.connect(backup_path)) as target:
                source.backup(target)
        backup_duration_seconds = round(time.perf_counter() - start, 6)

        with closing(sqlite3.connect(backup_path)) as backup:
            backup.row_factory = sqlite3.Row
            backup_integrity = _integrity_check(backup)
            table_counts = _table_counts(backup)
            source_schema_version = _schema_version(backup)
            secret_findings = _secret_findings(backup)

        if integrity != "ok":
            backup_path.unlink(missing_ok=True)
            raise BackupRestoreError(f"source integrity check failed: {integrity}")
        if backup_integrity != "ok":
            backup_path.unlink(missing_ok=True)
            raise BackupRestoreError(f"backup integrity check failed: {backup_integrity}")
        if secret_findings:
            backup_path.unlink(missing_ok=True)
            raise BackupRestoreError("source database contains forbidden secret-like material")

        manifest = BackupManifest(
            backup_id=backup_id,
            created_at=created_at,
            source_db=self.source_db_path.name,
            source_schema_version=source_schema_version,
            source_app_commit=self.app_commit,
            backup_file=backup_path.name,
            size_bytes=backup_path.stat().st_size,
            sha256=_sha256(backup_path),
            integrity_check_result=backup_integrity,
            table_counts=table_counts,
            duration_ms=int(backup_duration_seconds * 1000),
            contains_secrets=False,
            secret_findings=(),
        )
        manifest_path.write_text(json.dumps(_manifest_dict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return manifest

    def list_backups(self) -> tuple[BackupManifest, ...]:
        if not self.backup_dir.exists():
            return ()
        manifests: list[BackupManifest] = []
        for path in sorted(self.backup_dir.glob("triggertrade-*.json"), reverse=True):
            try:
                manifest = _load_manifest(path)
                self._backup_path(manifest.backup_id)
            except BackupRestoreError:
                continue
            manifests.append(manifest)
        return tuple(sorted(manifests, key=lambda item: item.created_at, reverse=True))

    def verify_backup(self, backup_id: str) -> BackupVerification:
        backup_id = _validate_backup_id(backup_id)
        manifest_path = self._manifest_path(backup_id)
        if not manifest_path.exists():
            raise BackupRestoreError("backup manifest not found")
        manifest = _load_manifest(manifest_path)
        if manifest.backup_id != backup_id:
            raise BackupRestoreError("backup manifest identity mismatch")
        backup_path = self._backup_path(backup_id)
        if manifest.backup_file != backup_path.name:
            raise BackupRestoreError("backup manifest file mismatch")
        if not backup_path.exists():
            raise BackupRestoreError("backup file not found")

        checksum_ok = _sha256(backup_path) == manifest.sha256
        if not checksum_ok:
            raise BackupRestoreError("backup checksum mismatch")
        with closing(sqlite3.connect(backup_path)) as conn:
            conn.row_factory = sqlite3.Row
            integrity = _integrity_check(conn)
            table_counts = _table_counts(conn)
            secret_findings = _secret_findings(conn)
        if integrity != "ok":
            raise BackupRestoreError(f"backup integrity check failed: {integrity}")
        if secret_findings or manifest.contains_secrets:
            raise BackupRestoreError("backup contains forbidden secret-like material")
        return BackupVerification(
            backup_id=backup_id,
            backup_path=backup_path,
            manifest_path=manifest_path,
            checksum_ok=True,
            integrity_check_result=integrity,
            contains_secrets=False,
            table_counts=table_counts,
            valid=True,
        )

    def restore_to_isolated_copy(self, backup_id: str, *, restore_id: str | None = None) -> Path:
        restore_id = _restore_id(restore_id or f"{backup_id}-restored")
        verification = self.verify_backup(backup_id)
        self.restore_dir.mkdir(parents=True, exist_ok=True)
        target_path = self._restore_path(restore_id)
        if _same_path(target_path, self.source_db_path):
            raise BackupRestoreError("restore target must not be the active source database")
        if target_path.exists():
            raise BackupRestoreError("isolated restore target already exists")
        shutil.copy2(verification.backup_path, target_path)
        with closing(sqlite3.connect(target_path)) as restored:
            if _integrity_check(restored) != "ok":
                target_path.unlink(missing_ok=True)
                raise BackupRestoreError("restored copy integrity check failed")
        return target_path

    def verify_restore(self, backup_id: str, *, restore_id: str | None = None) -> RestoreVerification:
        source_before = critical_state_fingerprint(self.source_db_path)
        restored_path = self.restore_to_isolated_copy(backup_id, restore_id=restore_id)
        _open_with_real_stores(restored_path)
        with closing(sqlite3.connect(restored_path)) as restored:
            restored.row_factory = sqlite3.Row
            integrity = _integrity_check(restored)
        source_after = critical_state_fingerprint(self.source_db_path)
        if source_after != source_before:
            raise BackupRestoreError("source database changed during restore verification")
        restored_fingerprint = critical_state_fingerprint(restored_path)
        system_history_generated = _restored_system_history_is_safe(restored_path)
        return RestoreVerification(
            backup_id=_validate_backup_id(backup_id),
            restored_path=restored_path,
            integrity_check_result=integrity,
            critical_identity_match=source_before == restored_fingerprint,
            source_fingerprint=source_before,
            restored_fingerprint=restored_fingerprint,
            system_history_generated=system_history_generated,
            reconciliation_required=bool(restored_fingerprint.get("open_positions_count")),
        )

    def _backup_path(self, backup_id: str) -> Path:
        return _safe_child(self.backup_dir, f"{_validate_backup_id(backup_id)}.sqlite3")

    def _manifest_path(self, backup_id: str) -> Path:
        return _safe_child(self.backup_dir, f"{_validate_backup_id(backup_id)}.json")

    def _restore_path(self, restore_id: str) -> Path:
        return _safe_child(self.restore_dir, f"{_restore_id(restore_id)}.sqlite3")


def critical_state_fingerprint(db_path: str | Path) -> dict[str, Any]:
    path = Path(db_path)
    if not path.exists():
        raise BackupRestoreError("database not found")
    with closing(sqlite3.connect(path)) as conn:
        conn.row_factory = sqlite3.Row
        tables = _table_names(conn)
        current_rules = _scalar(conn, "SELECT rules_version_id FROM trading_rules_current WHERE scope = 'LIVE'") if "trading_rules_current" in tables else None
        active_set = None
        if "trigger_set_versions" in tables:
            row = conn.execute(
                """
                SELECT set_id, version
                FROM trigger_set_versions
                WHERE status = 'ACTIVE'
                ORDER BY set_id, version
                LIMIT 1
                """
            ).fetchone()
            active_set = None if row is None else f"{row['set_id']}@{row['version']}"
        operator = None
        if "operator_trading_state" in tables:
            row = conn.execute("SELECT state, changed_at FROM operator_trading_state WHERE scope = 'ACTIVE'").fetchone()
            operator = None if row is None else {"state": row["state"], "changed_at": row["changed_at"]}
        return {
            "active_set": active_set,
            "current_rules_version_id": current_rules,
            "rules_versions_count": _count(conn, "trading_rules_versions", tables),
            "trigger_versions_count": _count(conn, "rule_definitions", tables),
            "set_versions_count": _count(conn, "trigger_set_versions", tables),
            "set_memberships_count": _count(conn, "trigger_set_memberships", tables),
            "research_count": _count(conn, "research_entities", tables),
            "research_backtest_count": _count(conn, "research_backtest_runs", tables),
            "research_demo_count": _count(conn, "research_demo_runs", tables),
            "orders_count": _count(conn, "futures_execution_orders", tables) + _count(conn, "execution_orders", tables),
            "fills_count": _count(conn, "futures_accounting_fills", tables) + _count(conn, "execution_fills", tables),
            "open_positions_count": _count(conn, "futures_positions", tables),
            "closed_positions_count": _count(conn, "futures_closed_positions", tables) + _count(conn, "futures_closed_trades", tables),
            "audit_events_count": _count(conn, "audit_events", tables),
            "audit_latest_event_id": _scalar(conn, "SELECT event_id FROM audit_events ORDER BY created_at DESC, event_id DESC LIMIT 1") if "audit_events" in tables else None,
            "messages_count": _count(conn, "user_messages", tables),
            "operator_state": operator,
        }


def _open_with_real_stores(db_path: Path) -> None:
    TradingRulesStore(db_path).get_current()
    trigger_store = TriggerSetStore(db_path)
    trigger_store.list_sets()
    ResearchStore(db_path).list_research()
    FuturesExecutionStore(db_path).list_recent()
    FuturesPositionStore(db_path).list_open_positions()
    FuturesAccountingStore(db_path).latest_equity_snapshot()
    OperatorStateStore(db_path).get_trading_state()
    MessageStore(db_path).get_unread_message_count()
    RuntimeStore(db_path).list_heartbeats()
    TraceStore(db_path).list_audit_events(limit=1)


def _restored_system_history_is_safe(db_path: Path) -> bool:
    text = SystemHistoryExporter(
        read_model=DashboardReadModel(db_path),
        operator_store=OperatorStateStore(db_path),
        message_store=MessageStore(db_path),
    ).build_export()
    if _SECRET_VALUE_RE.search(text):
        raise BackupRestoreError("restored system history contains forbidden secret-like material")
    return True


def _backup_id(created_at: str, suffix: str | None) -> str:
    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    base = "triggertrade-" + dt.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    if suffix:
        safe_suffix = re.sub(r"[^A-Za-z0-9_-]", "-", suffix.strip())[:24].strip("-")
        if safe_suffix:
            base = f"{base}-{safe_suffix}"
    return _validate_backup_id(base)


def _validate_backup_id(backup_id: str) -> str:
    value = str(backup_id).strip()
    if not _BACKUP_ID_RE.fullmatch(value):
        raise BackupRestoreError("invalid backup id")
    return value


def _restore_id(restore_id: str) -> str:
    value = str(restore_id).strip()
    if not _RESTORE_ID_RE.fullmatch(value) or ".." in value:
        raise BackupRestoreError("invalid restore id")
    return value


def _safe_child(root: str | Path, name: str) -> Path:
    root_path = Path(root).resolve()
    child = (root_path / name).resolve()
    if root_path != child.parent:
        raise BackupRestoreError("path escapes managed backup directory")
    return child


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _integrity_check(conn: sqlite3.Connection) -> str:
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.Error as exc:
        raise BackupRestoreError(f"backup integrity check failed: {exc}") from exc
    return str(row[0] if row is not None else "missing integrity result")


def _schema_version(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("PRAGMA user_version").fetchone()
    return None if row is None else str(row[0])


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'").fetchall()
    return {str(row["name"] if isinstance(row, sqlite3.Row) else row[0]) for row in rows}


def _table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {table: _count(conn, table, _table_names(conn)) for table in sorted(_table_names(conn))}


def _count(conn: sqlite3.Connection, table: str, tables: set[str]) -> int:
    if table not in tables:
        return 0
    return int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])


def _scalar(conn: sqlite3.Connection, query: str) -> Any:
    row = conn.execute(query).fetchone()
    if row is None:
        return None
    return row[0] if not isinstance(row, sqlite3.Row) else row[0]


def _secret_findings(conn: sqlite3.Connection) -> tuple[str, ...]:
    findings: list[str] = []
    for table in sorted(_table_names(conn)):
        columns = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
        text_columns = [
            str(column["name"] if isinstance(column, sqlite3.Row) else column[1])
            for column in columns
            if "TEXT" in str(column["type"] if isinstance(column, sqlite3.Row) else column[2]).upper()
        ]
        for column in text_columns:
            rows = conn.execute(f'SELECT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL')
            for row in rows:
                value = str(row[0])
                if _SECRET_VALUE_RE.search(value):
                    findings.append(f"{table}.{column}")
                    break
        if len(findings) >= 20:
            break
    return tuple(findings)


def _manifest_dict(manifest: BackupManifest) -> dict[str, Any]:
    return {
        "backup_id": manifest.backup_id,
        "created_at": manifest.created_at,
        "source_db": manifest.source_db,
        "source_schema_version": manifest.source_schema_version,
        "source_app_commit": manifest.source_app_commit,
        "backup_file": manifest.backup_file,
        "size_bytes": manifest.size_bytes,
        "sha256": manifest.sha256,
        "integrity_check_result": manifest.integrity_check_result,
        "table_counts": manifest.table_counts,
        "duration_ms": manifest.duration_ms,
        "contains_secrets": manifest.contains_secrets,
        "secret_findings": list(manifest.secret_findings),
        "schema_version": manifest.schema_version,
    }


def _load_manifest(path: Path) -> BackupManifest:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise BackupRestoreError("invalid backup manifest") from exc
    if data.get("schema_version") != BACKUP_SCHEMA_VERSION:
        raise BackupRestoreError("unsupported backup manifest schema")
    return BackupManifest(
        backup_id=_validate_backup_id(str(data.get("backup_id", ""))),
        created_at=str(data.get("created_at", "")),
        source_db=str(data.get("source_db", "")),
        source_schema_version=data.get("source_schema_version"),
        source_app_commit=data.get("source_app_commit"),
        backup_file=str(data.get("backup_file", "")),
        size_bytes=int(data.get("size_bytes", 0)),
        sha256=str(data.get("sha256", "")),
        integrity_check_result=str(data.get("integrity_check_result", "")),
        table_counts={str(key): int(value) for key, value in dict(data.get("table_counts", {})).items()},
        duration_ms=int(data.get("duration_ms", 0)),
        contains_secrets=bool(data.get("contains_secrets", False)),
        secret_findings=tuple(str(item) for item in data.get("secret_findings", ())),
        schema_version=str(data.get("schema_version", "")),
    )
