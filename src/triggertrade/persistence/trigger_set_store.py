"""SQLite persistence for rule registry and versioned Trigger Sets."""

from __future__ import annotations

from pathlib import Path
import json
import sqlite3
from typing import Iterable

from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType, TriggerSetStatus, TriggerSetVersion


class TriggerSetStoreError(RuntimeError):
    pass


class TriggerSetStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_rule(self, rule: RuleDefinition) -> RuleDefinition:
        definition = json.dumps(dict(rule.definition), sort_keys=True)
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT status, condition, definition FROM rule_definitions WHERE rule_id = ? AND version = ?",
                (rule.rule_id, rule.version),
            ).fetchone()
            if existing is not None and (
                existing["status"] != rule.status.value
                or existing["condition"] != rule.condition
                or existing["definition"] != definition
            ):
                raise TriggerSetStoreError("rule versions are immutable; create a new version")
            conn.execute(
                """
                INSERT INTO rule_definitions (
                    rule_id, version, name, status, asset_scope, rule_type,
                    condition, definition, created_at, updated_at, provenance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(rule_id, version) DO NOTHING
                """,
                (
                    rule.rule_id,
                    rule.version,
                    rule.name,
                    rule.status.value,
                    rule.asset_scope,
                    rule.rule_type.value,
                    rule.condition,
                    definition,
                    rule.created_at,
                    rule.updated_at,
                    rule.provenance,
                ),
            )
        return rule

    def create_set(self, trigger_set: TriggerSetVersion) -> TriggerSetVersion:
        if not trigger_set.version:
            raise TriggerSetStoreError("trigger set version is required")
        semantic_hash = _semantic_hash(trigger_set)
        with self._connect() as conn:
            _validate_membership(conn, trigger_set.rule_versions)
            existing = conn.execute(
                "SELECT semantic_hash FROM trigger_set_versions WHERE set_id = ? AND version = ?",
                (trigger_set.set_id, trigger_set.version),
            ).fetchone()
            if existing is not None:
                if existing["semantic_hash"] != semantic_hash:
                    raise TriggerSetStoreError("trigger set versions are immutable; create a new version")
                return trigger_set
            if trigger_set.status is TriggerSetStatus.ACTIVE:
                active = self.get_active_set(trigger_set.symbol, trigger_set.timeframe, conn)
                if active is not None:
                    raise TriggerSetStoreError("only one ACTIVE trigger set is allowed per runtime scope")
            conn.execute(
                """
                INSERT INTO trigger_set_versions (
                    set_id, version, purpose, status, symbol, timeframe,
                    strategy_version, risk_profile_version, config_snapshot,
                    semantic_hash, created_at, provenance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trigger_set.set_id,
                    trigger_set.version,
                    trigger_set.purpose,
                    trigger_set.status.value,
                    trigger_set.symbol,
                    trigger_set.timeframe,
                    trigger_set.strategy_version,
                    trigger_set.risk_profile_version,
                    json.dumps(dict(trigger_set.config_snapshot), sort_keys=True),
                    semantic_hash,
                    trigger_set.created_at,
                    trigger_set.provenance,
                ),
            )
            for position, (rule_id, rule_version) in enumerate(trigger_set.rule_versions):
                conn.execute(
                    """
                    INSERT INTO trigger_set_memberships (
                        set_id, set_version, rule_id, rule_version, position
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (trigger_set.set_id, trigger_set.version, rule_id, rule_version, position),
                )
        return trigger_set

    def transition_status(
        self,
        *,
        set_id: str,
        version: str,
        status: TriggerSetStatus,
        changed_at: str,
        reason: str,
    ) -> TriggerSetVersion:
        with self._connect() as conn:
            current = self.get_set(set_id, version, conn)
            if current is None:
                raise TriggerSetStoreError("trigger set version not found")
            if current.status is status:
                return current
            if status is TriggerSetStatus.ACTIVE:
                active = self.get_active_set(current.symbol, current.timeframe, conn)
                if active is not None and (active.set_id, active.version) != (set_id, version):
                    conn.execute(
                        "UPDATE trigger_set_versions SET status = ? WHERE set_id = ? AND version = ?",
                        (TriggerSetStatus.ARCHIVE.value, active.set_id, active.version),
                    )
                    _insert_transition(conn, active, TriggerSetStatus.ARCHIVE, changed_at, "archived by explicit promotion")
            conn.execute(
                "UPDATE trigger_set_versions SET status = ? WHERE set_id = ? AND version = ?",
                (status.value, set_id, version),
            )
            _insert_transition(conn, current, status, changed_at, reason)
        return self.get_set(set_id, version)  # type: ignore[return-value]

    def get_active_set(
        self,
        symbol: str,
        timeframe: str,
        conn: sqlite3.Connection | None = None,
    ) -> TriggerSetVersion | None:
        return self._fetch_one(
            """
            SELECT set_id, version, purpose, status, symbol, timeframe,
                   strategy_version, risk_profile_version, config_snapshot,
                   created_at, provenance
            FROM trigger_set_versions
            WHERE symbol = ? AND timeframe = ? AND status = ?
            """,
            (symbol, timeframe, TriggerSetStatus.ACTIVE.value),
            conn,
        )

    def list_testing_sets(self, symbol: str, timeframe: str) -> tuple[TriggerSetVersion, ...]:
        return tuple(
            item
            for item in self.list_sets()
            if item.symbol == symbol and item.timeframe == timeframe and item.status is TriggerSetStatus.TESTING
        )

    def list_sets(self) -> tuple[TriggerSetVersion, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT set_id, version, purpose, status, symbol, timeframe,
                       strategy_version, risk_profile_version, config_snapshot,
                       created_at, provenance
                FROM trigger_set_versions
                ORDER BY created_at DESC, set_id, version
                """
            ).fetchall()
            return tuple(self._row_to_set(row, conn) for row in rows)

    def list_rules(self) -> tuple[RuleDefinition, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT rule_id, version, name, status, asset_scope, rule_type,
                       condition, definition, created_at, updated_at, provenance
                FROM rule_definitions
                ORDER BY rule_id, version
                """
            ).fetchall()
        return tuple(_row_to_rule(row) for row in rows)

    def get_set(
        self,
        set_id: str,
        version: str,
        conn: sqlite3.Connection | None = None,
    ) -> TriggerSetVersion | None:
        return self._fetch_one(
            """
            SELECT set_id, version, purpose, status, symbol, timeframe,
                   strategy_version, risk_profile_version, config_snapshot,
                   created_at, provenance
            FROM trigger_set_versions
            WHERE set_id = ? AND version = ?
            """,
            (set_id, version),
            conn,
        )

    def _fetch_one(
        self,
        query: str,
        values: Iterable[str],
        conn: sqlite3.Connection | None,
    ) -> TriggerSetVersion | None:
        if conn is not None:
            row = conn.execute(query, tuple(values)).fetchone()
            return None if row is None else self._row_to_set(row, conn)
        with self._connect() as local_conn:
            row = local_conn.execute(query, tuple(values)).fetchone()
            return None if row is None else self._row_to_set(row, local_conn)

    def _row_to_set(self, row: sqlite3.Row, conn: sqlite3.Connection) -> TriggerSetVersion:
        membership_rows = conn.execute(
            """
            SELECT rule_id, rule_version
            FROM trigger_set_memberships
            WHERE set_id = ? AND set_version = ?
            ORDER BY position
            """,
            (row["set_id"], row["version"]),
        ).fetchall()
        return TriggerSetVersion(
            set_id=row["set_id"],
            version=row["version"],
            purpose=row["purpose"],
            status=TriggerSetStatus(row["status"]),
            symbol=row["symbol"],
            timeframe=row["timeframe"],
            rule_versions=tuple((item["rule_id"], item["rule_version"]) for item in membership_rows),
            strategy_version=row["strategy_version"],
            risk_profile_version=row["risk_profile_version"],
            config_snapshot=json.loads(row["config_snapshot"]),
            created_at=row["created_at"],
            provenance=row["provenance"],
        )

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rule_definitions (
                    rule_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    asset_scope TEXT NOT NULL,
                    rule_type TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    provenance TEXT NOT NULL,
                    PRIMARY KEY (rule_id, version)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trigger_set_versions (
                    set_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    status TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    strategy_version TEXT NOT NULL,
                    risk_profile_version TEXT NOT NULL,
                    config_snapshot TEXT NOT NULL,
                    semantic_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    PRIMARY KEY (set_id, version)
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_trigger_set_one_active
                ON trigger_set_versions(symbol, timeframe)
                WHERE status = 'ACTIVE'
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trigger_set_memberships (
                    set_id TEXT NOT NULL,
                    set_version TEXT NOT NULL,
                    rule_id TEXT NOT NULL,
                    rule_version TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    PRIMARY KEY (set_id, set_version, rule_id, rule_version)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trigger_set_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    set_id TEXT NOT NULL,
                    set_version TEXT NOT NULL,
                    from_status TEXT NOT NULL,
                    to_status TEXT NOT NULL,
                    changed_at TEXT NOT NULL,
                    reason TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


def bootstrap_current_trigger_sets(store: TriggerSetStore, *, created_at: str = "2026-09-05T00:00:00+00:00") -> None:
    for rule in current_rule_definitions(created_at=created_at):
        store.save_rule(rule)
    active = current_active_trigger_set(created_at=created_at)
    if store.get_set(active.set_id, active.version) is None:
        store.create_set(active)
    testing = current_testing_trigger_set(created_at=created_at)
    if store.get_set(testing.set_id, testing.version) is None:
        store.create_set(testing)


def current_rule_definitions(*, created_at: str) -> tuple[RuleDefinition, ...]:
    return (
        RuleDefinition(
            rule_id="TRG-001",
            version="0.1.0",
            name="Percentage price move",
            status=RuleStatus.ACTIVE,
            asset_scope="BTCUSDT spot",
            rule_type=RuleType.TRIGGER,
            condition="price_change_pct <= configured demo threshold pct",
            definition={"lookback_window": "1m", "threshold_source": "TRIGGERTRADE_TRG_001_THRESHOLD_PCT", "boundary": "inclusive_lte"},
            created_at=created_at,
            provenance="implemented vertical slice d081274",
        ),
        RuleDefinition(
            rule_id="STR-001",
            version="0.1.0",
            name="BUY intent from TRG-001 candidate",
            status=RuleStatus.ACTIVE,
            asset_scope="BTCUSDT spot",
            rule_type=RuleType.STRATEGY,
            condition="BUY_CANDIDATE creates one BUY limit TradeIntent when enabled",
            definition={"signal_type": "BUY_CANDIDATE", "side": "Buy", "order_type": "Limit"},
            created_at=created_at,
            provenance="implemented vertical slice d081274",
        ),
        RuleDefinition(
            rule_id="RSK-PAPER-001",
            version="0.1.0",
            name="Paper risk profile RSK-001..RSK-005",
            status=RuleStatus.ACTIVE,
            asset_scope="BTCUSDT spot",
            rule_type=RuleType.RISK,
            condition="deterministic paper gates: notional, duplicate/open intent, balance, demo-only, stale data",
            definition={"rules": "RSK-001,RSK-002,RSK-003,RSK-004,RSK-005"},
            created_at=created_at,
            provenance="implemented vertical slice d081274",
        ),
    )


def current_active_trigger_set(*, created_at: str) -> TriggerSetVersion:
    return TriggerSetVersion(
        set_id="triggertrade-core",
        version="v1",
        purpose="Current active paper runtime set",
        status=TriggerSetStatus.ACTIVE,
        symbol="BTCUSDT",
        timeframe="1m",
        rule_versions=(("TRG-001", "0.1.0"), ("STR-001", "0.1.0"), ("RSK-PAPER-001", "0.1.0")),
        strategy_version="STR-001@0.1.0",
        risk_profile_version="RSK-PAPER-001@0.1.0",
        config_snapshot={"threshold": "demo-config", "execution": "local_paper"},
        created_at=created_at,
        provenance="bootstrap from current implemented rules",
    )


def current_testing_trigger_set(*, created_at: str) -> TriggerSetVersion:
    return TriggerSetVersion(
        set_id="triggertrade-core-candidate",
        version="v1-test",
        purpose="Forward-test candidate using current rule semantics",
        status=TriggerSetStatus.TESTING,
        symbol="BTCUSDT",
        timeframe="1m",
        rule_versions=(("TRG-001", "0.1.0"), ("STR-001", "0.1.0"), ("RSK-PAPER-001", "0.1.0")),
        strategy_version="STR-001@0.1.0",
        risk_profile_version="RSK-PAPER-001@0.1.0",
        config_snapshot={"threshold": "demo-config", "execution": "isolated_test_paper"},
        created_at=created_at,
        provenance="safe candidate fixture for parallel lane plumbing",
    )


def _validate_membership(conn: sqlite3.Connection, memberships: tuple[tuple[str, str], ...]) -> None:
    if not memberships:
        raise TriggerSetStoreError("trigger set requires at least one rule")
    for rule_id, version in memberships:
        row = conn.execute(
            "SELECT status FROM rule_definitions WHERE rule_id = ? AND version = ?",
            (rule_id, version),
        ).fetchone()
        if row is None:
            raise TriggerSetStoreError(f"unknown rule version: {rule_id}@{version}")


def _insert_transition(
    conn: sqlite3.Connection,
    trigger_set: TriggerSetVersion,
    to_status: TriggerSetStatus,
    changed_at: str,
    reason: str,
) -> None:
    conn.execute(
        """
        INSERT INTO trigger_set_transitions (
            set_id, set_version, from_status, to_status, changed_at, reason
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (trigger_set.set_id, trigger_set.version, trigger_set.status.value, to_status.value, changed_at, reason),
    )


def _semantic_hash(trigger_set: TriggerSetVersion) -> str:
    payload = {
        "set_id": trigger_set.set_id,
        "version": trigger_set.version,
        "purpose": trigger_set.purpose,
        "symbol": trigger_set.symbol,
        "timeframe": trigger_set.timeframe,
        "rule_versions": trigger_set.rule_versions,
        "strategy_version": trigger_set.strategy_version,
        "risk_profile_version": trigger_set.risk_profile_version,
        "config_snapshot": dict(trigger_set.config_snapshot),
    }
    return json.dumps(payload, sort_keys=True)


def _row_to_rule(row: sqlite3.Row) -> RuleDefinition:
    return RuleDefinition(
        rule_id=row["rule_id"],
        version=row["version"],
        name=row["name"],
        status=RuleStatus(row["status"]),
        asset_scope=row["asset_scope"],
        rule_type=RuleType(row["rule_type"]),
        condition=row["condition"],
        definition=json.loads(row["definition"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        provenance=row["provenance"],
    )
