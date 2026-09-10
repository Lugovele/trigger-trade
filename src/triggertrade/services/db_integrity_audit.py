"""Read-only database integrity and retention audit for TriggerTrade."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3
from typing import Any


RETENTION_PERMANENT_EVIDENCE = "PERMANENT_EVIDENCE"
RETENTION_LONG_TERM_OPERATIONAL = "LONG_TERM_OPERATIONAL"
RETENTION_RECONSTRUCTABLE_CACHE = "RECONSTRUCTABLE_CACHE"
RETENTION_EPHEMERAL_RUNTIME = "EPHEMERAL_RUNTIME"

GROWTH_LOW = "LOW"
GROWTH_MEDIUM = "MEDIUM"
GROWTH_HIGH = "HIGH"
GROWTH_VERY_HIGH = "VERY_HIGH"


def _ret(retention_class: str, growth: str, owner: str, purpose: str) -> dict[str, str]:
    return {
        "retention_class": retention_class,
        "growth": growth,
        "owner": owner,
        "purpose": purpose,
    }


RETENTION_MATRIX: dict[str, dict[str, str]] = {
    "rule_definitions": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_LOW, "TriggerSetStore", "Immutable Trigger Version definitions."),
    "trigger_set_versions": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_LOW, "TriggerSetStore", "Immutable Trigger Set Version identities."),
    "trigger_set_memberships": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_LOW, "TriggerSetStore", "Exact Set to Trigger Version composition."),
    "trigger_set_transitions": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_LOW, "TriggerSetStore", "Active/archive transition history."),
    "recommendations": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_LOW, "TriggerSetStore", "Governed recommendation records."),
    "recommendation_transitions": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_LOW, "TriggerSetStore", "Recommendation lifecycle history."),
    "trading_rules_versions": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_LOW, "TradingRulesStore", "Immutable Trading Rules versions."),
    "trading_rules_current": _ret(RETENTION_LONG_TERM_OPERATIONAL, GROWTH_LOW, "TradingRulesStore", "Current Rules pointer."),
    "trading_rules_coin_rules": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_LOW, "TradingRulesStore", "Rules Version coin scope."),
    "trading_rules_usage": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "TradingRulesStore", "Rules Version attribution."),
    "research_entities": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "ResearchStore", "Research evidence identity and decision state."),
    "research_backtest_runs": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_HIGH, "ResearchStore", "Backtest run metadata and selected evidence."),
    "research_demo_runs": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_HIGH, "ResearchStore", "Demo run metadata and selected evidence."),
    "research_decision_events": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "ResearchStore", "Research decision event history."),
    "futures_execution_orders": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "FuturesExecutionStore", "Exchange order lifecycle evidence."),
    "execution_orders": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "ExecutionStore", "Legacy paper order lifecycle evidence."),
    "execution_fills": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "ExecutionStore", "Legacy fill evidence."),
    "futures_accounting_fills": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "FuturesAccountingStore", "Authoritative futures fill accounting."),
    "futures_accounting_funding": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "FuturesAccountingStore", "Funding accounting evidence."),
    "futures_closed_trades": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "FuturesAccountingStore", "Realized P&L records."),
    "futures_equity_snapshots": _ret(RETENTION_LONG_TERM_OPERATIONAL, GROWTH_HIGH, "FuturesAccountingStore", "Account/equity state history."),
    "futures_positions": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "FuturesPositionStore", "Open position state requiring reconciliation."),
    "futures_closed_positions": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "FuturesPositionStore", "Closed position summaries."),
    "futures_position_events": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "FuturesPositionStore", "Position lifecycle event history."),
    "futures_close_all_operations": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_LOW, "FuturesPositionStore", "Operator close-all evidence."),
    "operator_trading_state": _ret(RETENTION_LONG_TERM_OPERATIONAL, GROWTH_LOW, "OperatorStateStore", "Current operator pause/resume state."),
    "operator_action_audit": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "OperatorStateStore", "Operator action history."),
    "operator_trading_state_audit": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "OperatorStateStore", "Operator state transition history."),
    "user_messages": _ret(RETENTION_LONG_TERM_OPERATIONAL, GROWTH_MEDIUM, "MessageStore", "User-facing operational messages and read state."),
    "audit_events": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_HIGH, "TraceStore", "Canonical causal audit trail."),
    "runtime_lane_state": _ret(RETENTION_LONG_TERM_OPERATIONAL, GROWTH_LOW, "RuntimeStore", "Current lane checkpoint source of truth."),
    "runtime_lane_lifecycles": _ret(RETENTION_LONG_TERM_OPERATIONAL, GROWTH_VERY_HIGH, "RuntimeStore", "Per-candle runtime lifecycle evidence."),
    "runtime_candle_state": _ret(RETENTION_LONG_TERM_OPERATIONAL, GROWTH_LOW, "RuntimeStore", "Legacy candle checkpoint state."),
    "runtime_candle_lifecycles": _ret(RETENTION_LONG_TERM_OPERATIONAL, GROWTH_HIGH, "RuntimeStore", "Legacy candle lifecycle evidence."),
    "runtime_heartbeats": _ret(RETENTION_EPHEMERAL_RUNTIME, GROWTH_LOW, "RuntimeStore", "Latest component heartbeat state."),
    "market_regime_evaluations": _ret(RETENTION_LONG_TERM_OPERATIONAL, GROWTH_HIGH, "RuntimeStore", "Per-candle market regime evidence."),
    "trigger_evaluations": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_VERY_HIGH, "TraceStore", "Trigger signal evaluation evidence."),
    "strategy_decisions": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "TraceStore", "Strategy intent evidence."),
    "risk_decisions": _ret(RETENTION_PERMANENT_EVIDENCE, GROWTH_MEDIUM, "TraceStore", "Risk gate evidence."),
    "futures_instrument_catalog": _ret(RETENTION_RECONSTRUCTABLE_CACHE, GROWTH_MEDIUM, "InstrumentCatalogStore", "Bybit public instrument cache."),
    "futures_instrument_catalog_refreshes": _ret(RETENTION_RECONSTRUCTABLE_CACHE, GROWTH_LOW, "InstrumentCatalogStore", "Catalog refresh status."),
    "daily_loss_state": _ret(RETENTION_LONG_TERM_OPERATIONAL, GROWTH_LOW, "DailyLossStore", "Daily loss latch/baseline state."),
}


@dataclass(frozen=True)
class TableAudit:
    table: str
    purpose: str
    primary_key: tuple[str, ...]
    foreign_keys: tuple[str, ...]
    unique_constraints: tuple[str, ...]
    indexes: tuple[str, ...]
    row_count: int
    estimated_growth_rate: str
    canonical_owner: str
    retention_class: str


@dataclass(frozen=True)
class CheckResult:
    name: str
    count: int
    status: str
    detail: str


@dataclass(frozen=True)
class QueryPlanFinding:
    name: str
    status: str
    plan: tuple[str, ...]


@dataclass(frozen=True)
class DatabaseIntegrityAudit:
    db_path_name: str
    file_size_bytes: int
    page_count: int
    page_size: int
    freelist_count: int
    journal_mode: str
    synchronous: str
    auto_vacuum: str
    integrity_check: str
    foreign_key_check_count: int
    tables: tuple[TableAudit, ...]
    orphan_checks: tuple[CheckResult, ...]
    duplicate_checks: tuple[CheckResult, ...]
    enum_checks: tuple[CheckResult, ...]
    timestamp_checks: tuple[CheckResult, ...]
    active_pair_checks: tuple[CheckResult, ...]
    query_plan_findings: tuple[QueryPlanFinding, ...]

    @property
    def passed(self) -> bool:
        groups = (
            self.orphan_checks,
            self.duplicate_checks,
            self.enum_checks,
            self.timestamp_checks,
            self.active_pair_checks,
        )
        return self.integrity_check == "ok" and self.foreign_key_check_count == 0 and all(
            item.status in {"PASS", "NOT_APPLICABLE"} for group in groups for item in group
        )


def run_database_integrity_audit(db_path: str | Path) -> DatabaseIntegrityAudit:
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError("runtime database not found")
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        tables = _table_names(conn)
        return DatabaseIntegrityAudit(
            db_path_name=path.name,
            file_size_bytes=path.stat().st_size,
            page_count=int(_pragma(conn, "page_count")),
            page_size=int(_pragma(conn, "page_size")),
            freelist_count=int(_pragma(conn, "freelist_count")),
            journal_mode=str(_pragma(conn, "journal_mode")),
            synchronous=str(_pragma(conn, "synchronous")),
            auto_vacuum=str(_pragma(conn, "auto_vacuum")),
            integrity_check=str(_pragma(conn, "integrity_check")),
            foreign_key_check_count=len(conn.execute("PRAGMA foreign_key_check").fetchall()),
            tables=tuple(_table_audit(conn, table) for table in sorted(tables)),
            orphan_checks=tuple(_run_checks(conn, tables, _ORPHAN_CHECKS)),
            duplicate_checks=tuple(_run_checks(conn, tables, _DUPLICATE_CHECKS)),
            enum_checks=tuple(_run_checks(conn, tables, _ENUM_CHECKS)),
            timestamp_checks=tuple(_timestamp_checks(conn, tables)),
            active_pair_checks=tuple(_run_checks(conn, tables, _ACTIVE_PAIR_CHECKS)),
            query_plan_findings=tuple(_query_plan_findings(conn, tables)),
        )


def _table_audit(conn: sqlite3.Connection, table: str) -> TableAudit:
    meta = RETENTION_MATRIX.get(table, _ret(RETENTION_LONG_TERM_OPERATIONAL, GROWTH_MEDIUM, "unknown", "Support table."))
    columns = conn.execute(f'PRAGMA table_info("{_quote(table)}")').fetchall()
    pk_columns = tuple(row["name"] for row in sorted((row for row in columns if row["pk"]), key=lambda item: item["pk"]))
    foreign_keys = tuple(
        f'{row["from"]}->{row["table"]}.{row["to"]}'
        for row in conn.execute(f'PRAGMA foreign_key_list("{_quote(table)}")').fetchall()
    )
    indexes = conn.execute(f'PRAGMA index_list("{_quote(table)}")').fetchall()
    index_names = tuple(row["name"] for row in indexes)
    unique_indexes = tuple(row["name"] for row in indexes if row["unique"])
    return TableAudit(
        table=table,
        purpose=meta["purpose"],
        primary_key=pk_columns,
        foreign_keys=foreign_keys,
        unique_constraints=unique_indexes,
        indexes=index_names,
        row_count=_count(conn, table),
        estimated_growth_rate=meta["growth"],
        canonical_owner=meta["owner"],
        retention_class=meta["retention_class"],
    )


_ORPHAN_CHECKS = (
    (
        "current_rules_pointer_resolves",
        ("trading_rules_current", "trading_rules_versions"),
        """
        SELECT COUNT(*) FROM trading_rules_current c
        LEFT JOIN trading_rules_versions v ON v.rules_version_id = c.rules_version_id
        WHERE v.rules_version_id IS NULL
        """,
        "Current Rules pointer must resolve to immutable version.",
    ),
    (
        "set_memberships_resolve_trigger_versions",
        ("trigger_set_memberships", "rule_definitions"),
        """
        SELECT COUNT(*) FROM trigger_set_memberships m
        LEFT JOIN rule_definitions r ON r.rule_id = m.rule_id AND r.version = m.rule_version
        WHERE r.rule_id IS NULL
        """,
        "Set memberships must resolve exact Trigger Versions.",
    ),
    (
        "research_set_versions_resolve",
        ("research_entities", "trigger_set_versions"),
        """
        SELECT COUNT(*) FROM research_entities r
        LEFT JOIN trigger_set_versions s ON s.set_id = r.set_id AND s.version = r.set_version
        WHERE s.set_id IS NULL
        """,
        "Research must pin an existing Set Version.",
    ),
    (
        "research_rules_versions_resolve",
        ("research_entities", "trading_rules_versions"),
        """
        SELECT COUNT(*) FROM research_entities r
        LEFT JOIN trading_rules_versions v ON v.rules_version_id = r.rules_version_id
        WHERE v.rules_version_id IS NULL
        """,
        "Research must pin an existing Trading Rules Version.",
    ),
    (
        "selected_backtest_runs_resolve",
        ("research_entities", "research_backtest_runs"),
        """
        SELECT COUNT(*) FROM research_entities r
        LEFT JOIN research_backtest_runs b ON b.research_id = r.research_id AND b.run_id = r.selected_backtest_run_id
        WHERE r.selected_backtest_run_id IS NOT NULL AND b.run_id IS NULL
        """,
        "Selected Backtest run must belong to the Research.",
    ),
    (
        "selected_demo_runs_resolve",
        ("research_entities", "research_demo_runs"),
        """
        SELECT COUNT(*) FROM research_entities r
        LEFT JOIN research_demo_runs d ON d.research_id = r.research_id AND d.run_id = r.selected_demo_run_id
        WHERE r.selected_demo_run_id IS NOT NULL AND d.run_id IS NULL
        """,
        "Selected Demo run must belong to the Research.",
    ),
    (
        "futures_fills_resolve_orders",
        ("futures_accounting_fills", "futures_execution_orders"),
        """
        SELECT COUNT(*) FROM futures_accounting_fills f
        LEFT JOIN futures_execution_orders o ON o.intent_id = f.execution_id
        WHERE o.intent_id IS NULL
        """,
        "Futures fill execution id should resolve to stored order intent.",
    ),
    (
        "open_positions_resolve_open_order",
        ("futures_positions", "futures_execution_orders"),
        """
        SELECT COUNT(*) FROM futures_positions p
        LEFT JOIN futures_execution_orders o ON o.intent_id = p.open_execution_id
        WHERE o.intent_id IS NULL
        """,
        "Open positions should resolve their opening execution.",
    ),
)

_DUPLICATE_CHECKS = (
    ("rules_version_display_unique", ("trading_rules_versions",), "SELECT COUNT(*) FROM (SELECT version FROM trading_rules_versions GROUP BY version HAVING COUNT(*) > 1)", "Rules display versions must be unique."),
    ("trigger_version_unique", ("rule_definitions",), "SELECT COUNT(*) FROM (SELECT rule_id, version FROM rule_definitions GROUP BY rule_id, version HAVING COUNT(*) > 1)", "Trigger id+version must be unique."),
    ("set_version_unique", ("trigger_set_versions",), "SELECT COUNT(*) FROM (SELECT set_id, version FROM trigger_set_versions GROUP BY set_id, version HAVING COUNT(*) > 1)", "Set id+version must be unique."),
    ("research_id_unique", ("research_entities",), "SELECT COUNT(*) FROM (SELECT research_id FROM research_entities GROUP BY research_id HAVING COUNT(*) > 1)", "Research ids must be unique."),
    ("futures_client_order_unique", ("futures_execution_orders",), "SELECT COUNT(*) FROM (SELECT client_order_id FROM futures_execution_orders GROUP BY client_order_id HAVING COUNT(*) > 1)", "Client order ids must be unique."),
    ("audit_event_id_unique", ("audit_events",), "SELECT COUNT(*) FROM (SELECT event_id FROM audit_events GROUP BY event_id HAVING COUNT(*) > 1)", "Audit event ids must be unique."),
)

_ENUM_CHECKS = (
    ("set_status_known", ("trigger_set_versions",), "SELECT COUNT(*) FROM trigger_set_versions WHERE status NOT IN ('DRAFT','TESTING','ACTIVE','ARCHIVE')", "Set status must be recognized."),
    ("research_status_known", ("research_entities",), "SELECT COUNT(*) FROM research_entities WHERE status NOT IN ('DRAFT','BACKTEST_READY','DEMO_RUNNING','DEMO_STOPPED','DECISION_NEEDED','ARCHIVED','BLOCKED','MADE_ACTIVE','MAKE_ACTIVE_BLOCKED')", "Research status must be recognized."),
    ("message_severity_known", ("user_messages",), "SELECT COUNT(*) FROM user_messages WHERE severity NOT IN ('INFO','ATTENTION','WARNING','ERROR')", "Message severity must be recognized."),
    ("order_status_known", ("futures_execution_orders",), "SELECT COUNT(*) FROM futures_execution_orders WHERE status NOT IN ('created','submitting','submitted','partially_filled','filled','cancel_pending','cancelled','rejected','unknown')", "Futures order status must be recognized."),
    ("position_status_known", ("futures_positions",), "SELECT COUNT(*) FROM futures_positions WHERE status NOT IN ('OPEN','CLOSING','UNKNOWN')", "Open position status must be recognized."),
    ("audit_schema_known", ("audit_events",), "SELECT COUNT(*) FROM audit_events WHERE schema_version <> 'audit-event-v1'", "Audit schema version must be known."),
)

_ACTIVE_PAIR_CHECKS = (
    (
        "one_active_set_per_symbol_timeframe",
        ("trigger_set_versions",),
        """
        SELECT COUNT(*) FROM (
            SELECT symbol, timeframe
            FROM trigger_set_versions
            WHERE status = 'ACTIVE'
            GROUP BY symbol, timeframe
            HAVING COUNT(*) > 1
        )
        """,
        "There must not be multiple ACTIVE Sets for one symbol/timeframe.",
    ),
    (
        "active_pair_has_current_rules",
        ("trigger_set_versions", "trading_rules_current", "trading_rules_versions"),
        """
        SELECT CASE
            WHEN EXISTS (SELECT 1 FROM trigger_set_versions WHERE status = 'ACTIVE')
             AND EXISTS (
                SELECT 1 FROM trading_rules_current c
                JOIN trading_rules_versions v ON v.rules_version_id = c.rules_version_id
                WHERE c.scope = 'LIVE'
             )
            THEN 0 ELSE 1 END
        """,
        "Active Set and current Rules pointer must both be available.",
    ),
)


def _run_checks(conn: sqlite3.Connection, tables: set[str], checks: tuple[tuple[str, tuple[str, ...], str, str], ...]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for name, required, query, detail in checks:
        if any(table not in tables for table in required):
            results.append(CheckResult(name, 0, "NOT_APPLICABLE", "Required table absent."))
            continue
        count = int(conn.execute(query).fetchone()[0])
        results.append(CheckResult(name, count, "PASS" if count == 0 else "FAIL", detail))
    return results


def _timestamp_checks(conn: sqlite3.Connection, tables: set[str]) -> list[CheckResult]:
    results: list[CheckResult] = []
    timestamp_re = re.compile(r"(?:_at|_time)$")
    for table in sorted(tables):
        columns = [
            row["name"]
            for row in conn.execute(f'PRAGMA table_info("{_quote(table)}")').fetchall()
            if timestamp_re.search(str(row["name"]))
        ]
        for column in columns:
            query = (
                f'SELECT COUNT(*) FROM "{_quote(table)}" '
                f'WHERE "{_quote(column)}" IS NOT NULL '
                f'AND "{_quote(column)}" <> "" '
                f'AND "{_quote(column)}" NOT GLOB "????-??-??T??:??:??*" '
                f'AND "{_quote(column)}" NOT GLOB "[0-9]*"'
            )
            count = int(conn.execute(query).fetchone()[0])
            status = "PASS" if count == 0 else "FAIL"
            results.append(
                CheckResult(
                    f"{table}.{column}.interpretable",
                    count,
                    status,
                    "Timestamp values should be ISO-like UTC-compatible text or numeric exchange epoch text.",
                )
            )
    return results


def _query_plan_findings(conn: sqlite3.Connection, tables: set[str]) -> list[QueryPlanFinding]:
    queries = (
        ("latest_audit_events", ("audit_events",), "SELECT * FROM audit_events ORDER BY created_at DESC, event_id DESC LIMIT 50"),
        ("latest_messages", ("user_messages",), "SELECT * FROM user_messages ORDER BY created_at DESC LIMIT 50"),
        ("latest_equity_snapshot", ("futures_equity_snapshots",), "SELECT * FROM futures_equity_snapshots ORDER BY observed_at DESC, snapshot_id DESC LIMIT 1"),
        ("latest_runtime_lane", ("runtime_lane_lifecycles",), "SELECT * FROM runtime_lane_lifecycles ORDER BY processed_at DESC LIMIT 1"),
        ("research_backtest_runs", ("research_backtest_runs",), "SELECT * FROM research_backtest_runs WHERE research_id = 'unit' ORDER BY created_at DESC"),
        ("futures_order_by_client", ("futures_execution_orders",), "SELECT * FROM futures_execution_orders WHERE client_order_id = 'unit' LIMIT 1"),
    )
    findings: list[QueryPlanFinding] = []
    for name, required, query in queries:
        if any(table not in tables for table in required):
            findings.append(QueryPlanFinding(name, "NOT_APPLICABLE", ("Required table absent.",)))
            continue
        plan = tuple(str(row["detail"]) for row in conn.execute("EXPLAIN QUERY PLAN " + query).fetchall())
        joined = " | ".join(plan).upper()
        status = "WARN" if "SCAN" in joined and "USING INDEX" not in joined and "USING COVERING INDEX" not in joined else "PASS"
        findings.append(QueryPlanFinding(name, status, plan))
    return findings


def _pragma(conn: sqlite3.Connection, name: str) -> Any:
    row = conn.execute(f"PRAGMA {name}").fetchone()
    return None if row is None else row[0]


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'").fetchall()
    return {str(row["name"]) for row in rows}


def _count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f'SELECT COUNT(*) FROM "{_quote(table)}"').fetchone()[0])


def _quote(identifier: str) -> str:
    return identifier.replace('"', '""')
