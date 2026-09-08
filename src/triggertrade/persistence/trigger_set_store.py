"""SQLite persistence for rule registry and versioned Trigger Sets."""

from __future__ import annotations

from pathlib import Path
from hashlib import sha256
import json
import re
import sqlite3
from typing import Iterable

from triggertrade.trigger_sets import (
    TRIGGER_REGISTRY_SCHEMA_VERSION,
    TRIGGER_SET_REGISTRY_SCHEMA_VERSION,
    Recommendation,
    RegistrySyncReport,
    RuleDefinition,
    RuleStatus,
    RuleType,
    TriggerSetStatus,
    TriggerSetVersion,
)


class TriggerSetStoreError(RuntimeError):
    pass


_RECOMMENDATION_TRANSITIONS = {
    "PROPOSED": {"ACCEPTED_FOR_TEST", "REJECTED", "ARCHIVED"},
    "ACCEPTED_FOR_TEST": {"TESTING", "REJECTED", "ARCHIVED"},
    "TESTING": {"EVALUATED", "REJECTED", "ARCHIVED"},
    "EVALUATED": {"ADOPTED", "REJECTED", "ARCHIVED"},
    "ADOPTED": {"ARCHIVED"},
    "REJECTED": {"ARCHIVED"},
    "ARCHIVED": set(),
}

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_SET_VERSION_RE = re.compile(r"^v\d+([-.][a-z0-9]+)*$")
_LEGACY_UNVERIFIED_DEFINITION_HASH = "LEGACY_UNVERIFIED"


class TriggerSetStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_rule(self, rule: RuleDefinition) -> RuleDefinition:
        self._save_rule_result(rule)
        return rule

    def register_trigger_definitions(self, rules: Iterable[RuleDefinition]) -> RegistrySyncReport:
        return self.sync_trigger_registry(rules)

    def sync_trigger_registry(self, rules: Iterable[RuleDefinition]) -> RegistrySyncReport:
        unchanged: list[str] = []
        registered: list[str] = []
        conflicts: list[str] = []
        invalid: list[str] = []
        for rule in rules:
            try:
                result = self._save_rule_result(rule)
            except TriggerSetStoreError as exc:
                message = f"{rule.rule_id}@{rule.version}: {exc}"
                if "invalid" in str(exc) or "required" in str(exc) or "must use" in str(exc):
                    invalid.append(message)
                else:
                    conflicts.append(message)
            else:
                (unchanged if result == "unchanged" else registered).append(f"{rule.rule_id}@{rule.version}")
        return RegistrySyncReport(tuple(unchanged), tuple(registered), tuple(conflicts), tuple(invalid), ())

    def _save_rule_result(self, rule: RuleDefinition) -> str:
        _validate_rule_definition(rule)
        definition = json.dumps(_rule_definition_payload(rule), sort_keys=True)
        rule_hash = definition_hash(rule)
        if rule.semantic_hash is not None and rule.semantic_hash != rule_hash:
            raise TriggerSetStoreError("definition_hash does not match canonical trigger definition")
        with self._connect() as conn:
            existing = conn.execute(
                """
                SELECT rule_id, version, name, status, asset_scope, rule_type,
                       condition, definition, definition_hash, schema_version,
                       created_at, updated_at, provenance
                FROM rule_definitions
                WHERE rule_id = ? AND version = ?
                """,
                (rule.rule_id, rule.version),
            ).fetchone()
            if existing is not None:
                existing_hash = existing["definition_hash"] or _definition_hash_from_row(existing)
                if (
                    existing_hash not in {rule_hash, _LEGACY_UNVERIFIED_DEFINITION_HASH}
                    or existing["status"] != rule.status.value
                    or existing["condition"] != rule.condition
                    or existing["definition"] != definition
                ):
                    raise TriggerSetStoreError("semantic definition changed without Trigger Version bump")
                if existing["definition_hash"] is None and existing_hash == rule_hash:
                    conn.execute(
                        """
                        UPDATE rule_definitions
                        SET definition_hash = ?, schema_version = ?
                        WHERE rule_id = ? AND version = ?
                        """,
                        (rule_hash, TRIGGER_REGISTRY_SCHEMA_VERSION, rule.rule_id, rule.version),
                    )
                return "unchanged"
            conn.execute(
                """
                INSERT INTO rule_definitions (
                    rule_id, version, name, status, asset_scope, rule_type,
                    condition, definition, definition_hash, schema_version,
                    created_at, updated_at, provenance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    rule_hash,
                    TRIGGER_REGISTRY_SCHEMA_VERSION,
                    rule.created_at,
                    rule.updated_at,
                    rule.provenance,
                ),
            )
        return "registered"

    def create_set(self, trigger_set: TriggerSetVersion) -> TriggerSetVersion:
        self._create_set_result(trigger_set)
        return trigger_set

    def register_trigger_sets(self, trigger_sets: Iterable[TriggerSetVersion]) -> RegistrySyncReport:
        return self.sync_trigger_sets(trigger_sets)

    def sync_trigger_sets(self, trigger_sets: Iterable[TriggerSetVersion]) -> RegistrySyncReport:
        unchanged: list[str] = []
        registered: list[str] = []
        conflicts: list[str] = []
        invalid: list[str] = []
        for trigger_set in trigger_sets:
            try:
                result = self._create_set_result(trigger_set)
            except TriggerSetStoreError as exc:
                message = f"{trigger_set.set_id}@{trigger_set.version}: {exc}"
                if "invalid" in str(exc) or "requires" in str(exc) or "unknown" in str(exc):
                    invalid.append(message)
                else:
                    conflicts.append(message)
            else:
                (unchanged if result == "unchanged" else registered).append(f"{trigger_set.set_id}@{trigger_set.version}")
        return RegistrySyncReport(tuple(unchanged), tuple(registered), tuple(conflicts), tuple(invalid), ())

    def _create_set_result(self, trigger_set: TriggerSetVersion) -> str:
        if not trigger_set.version:
            raise TriggerSetStoreError("trigger set version is required")
        _validate_trigger_set_version(trigger_set)
        legacy_semantic_hash = _semantic_hash(trigger_set)
        set_hash = composition_hash(trigger_set)
        with self._connect() as conn:
            _validate_membership(conn, trigger_set.rule_versions)
            existing = conn.execute(
                """
                SELECT set_id, version, purpose, status, symbol, timeframe,
                       strategy_version, risk_profile_version, config_snapshot,
                       semantic_hash, composition_hash, schema_version,
                       created_at, provenance
                FROM trigger_set_versions
                WHERE set_id = ? AND version = ?
                """,
                (trigger_set.set_id, trigger_set.version),
            ).fetchone()
            if existing is not None:
                persisted_set = self._row_to_set(existing, conn)
                persisted_hash = composition_hash(persisted_set)
                existing_hash = existing["composition_hash"] or existing["semantic_hash"]
                if existing_hash not in {set_hash, legacy_semantic_hash}:
                    raise TriggerSetStoreError("semantic composition changed without Set Version bump")
                if persisted_hash != set_hash:
                    raise TriggerSetStoreError("persisted trigger set membership does not match composition_hash; fail closed")
                if existing["composition_hash"] is None:
                    conn.execute(
                        """
                        UPDATE trigger_set_versions
                        SET composition_hash = ?, schema_version = ?
                        WHERE set_id = ? AND version = ?
                        """,
                        (set_hash, TRIGGER_SET_REGISTRY_SCHEMA_VERSION, trigger_set.set_id, trigger_set.version),
                    )
                return "unchanged"
            if trigger_set.status is TriggerSetStatus.ACTIVE:
                active = self.get_active_set(trigger_set.symbol, trigger_set.timeframe, conn)
                if active is not None:
                    raise TriggerSetStoreError("only one ACTIVE trigger set is allowed per runtime scope")
            conn.execute(
                """
                INSERT INTO trigger_set_versions (
                    set_id, version, purpose, status, symbol, timeframe,
                    strategy_version, risk_profile_version, config_snapshot,
                    semantic_hash, composition_hash, schema_version,
                    created_at, provenance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    legacy_semantic_hash,
                    set_hash,
                    TRIGGER_SET_REGISTRY_SCHEMA_VERSION,
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
        return "registered"

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
                       condition, definition, definition_hash, schema_version,
                       created_at, updated_at, provenance
                FROM rule_definitions
                ORDER BY rule_id, version
                """
            ).fetchall()
        return tuple(_row_to_rule(row) for row in rows)

    def get_rule(self, rule_id: str, version: str | None = None) -> RuleDefinition | None:
        with self._connect() as conn:
            if version is None:
                row = conn.execute(
                    """
                    SELECT rule_id, version, name, status, asset_scope, rule_type,
                           condition, definition, definition_hash, schema_version,
                           created_at, updated_at, provenance
                    FROM rule_definitions
                    WHERE rule_id = ?
                    ORDER BY created_at DESC, version DESC
                    LIMIT 1
                    """,
                    (rule_id,),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT rule_id, version, name, status, asset_scope, rule_type,
                           condition, definition, definition_hash, schema_version,
                           created_at, updated_at, provenance
                    FROM rule_definitions
                    WHERE rule_id = ? AND version = ?
                    """,
                    (rule_id, version),
                ).fetchone()
        return None if row is None else _row_to_rule(row)

    def get_exact_rule(self, rule_id: str, version: str) -> RuleDefinition:
        rule = self.get_rule(rule_id, version)
        if rule is None:
            raise TriggerSetStoreError(f"unknown rule version: {rule_id}@{version}")
        return rule

    def resolve_trigger_version(self, trigger_set: TriggerSetVersion, trigger_id: str) -> RuleDefinition:
        versions = [version for rule_id, version in trigger_set.rule_versions if rule_id == trigger_id]
        if not versions:
            raise TriggerSetStoreError(f"trigger set does not include exact trigger version: {trigger_id}")
        if len(versions) > 1:
            raise TriggerSetStoreError(f"trigger set has ambiguous trigger version: {trigger_id}")
        rule = self.get_exact_rule(trigger_id, versions[0])
        if rule.rule_type is not RuleType.TRIGGER:
            raise TriggerSetStoreError(f"rule version is not a trigger: {trigger_id}@{versions[0]}")
        if not rule.semantic_hash:
            raise TriggerSetStoreError(f"unverified trigger definition hash: {trigger_id}@{versions[0]}")
        if rule.semantic_hash != definition_hash(rule):
            raise TriggerSetStoreError(f"trigger definition hash mismatch: {trigger_id}@{versions[0]}")
        return rule

    def list_rule_versions(self, rule_id: str) -> tuple[RuleDefinition, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT rule_id, version, name, status, asset_scope, rule_type,
                       condition, definition, created_at, updated_at, provenance
                FROM rule_definitions
                WHERE rule_id = ?
                ORDER BY created_at DESC, version DESC
                """,
                (rule_id,),
            ).fetchall()
        return tuple(_row_to_rule(row) for row in rows)

    def save_recommendation(self, recommendation: Recommendation) -> Recommendation:
        payload = _recommendation_payload(recommendation)
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT status, payload FROM recommendations WHERE recommendation_id = ?",
                (recommendation.recommendation_id,),
            ).fetchone()
            if existing is not None:
                if existing["payload"] != payload:
                    raise TriggerSetStoreError("recommendations are immutable; create a new recommendation")
                return recommendation
            conn.execute(
                """
                INSERT INTO recommendations (recommendation_id, status, created_at, title, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (recommendation.recommendation_id, recommendation.status, recommendation.created_at, recommendation.title, payload),
            )
        return recommendation

    def transition_recommendation_status(
        self,
        *,
        recommendation_id: str,
        status: str,
        changed_at: str,
        reason: str,
    ) -> Recommendation:
        target = status.strip().upper()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status, payload FROM recommendations WHERE recommendation_id = ?",
                (recommendation_id,),
            ).fetchone()
            if row is None:
                raise TriggerSetStoreError("recommendation not found")
            current = row["status"]
            if current == target:
                return _recommendation_from_row(row)
            if target not in _RECOMMENDATION_TRANSITIONS.get(current, set()):
                raise TriggerSetStoreError("invalid recommendation status transition")
            conn.execute(
                "UPDATE recommendations SET status = ? WHERE recommendation_id = ?",
                (target, recommendation_id),
            )
            conn.execute(
                """
                INSERT INTO recommendation_transitions (
                    recommendation_id, from_status, to_status, changed_at, reason
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (recommendation_id, current, target, changed_at, reason),
            )
            updated = conn.execute(
                "SELECT status, payload FROM recommendations WHERE recommendation_id = ?",
                (recommendation_id,),
            ).fetchone()
        return _recommendation_from_row(updated)

    def list_recommendations(self) -> tuple[Recommendation, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, payload FROM recommendations ORDER BY created_at DESC, recommendation_id"
            ).fetchall()
        return tuple(_recommendation_from_row(row) for row in rows)

    def get_recommendation(self, recommendation_id: str) -> Recommendation | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status, payload FROM recommendations WHERE recommendation_id = ?",
                (recommendation_id,),
            ).fetchone()
        return None if row is None else _recommendation_from_row(row)

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
                    definition_hash TEXT,
                    schema_version TEXT,
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
                    composition_hash TEXT,
                    schema_version TEXT,
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

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recommendations (
                    recommendation_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recommendation_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recommendation_id TEXT NOT NULL,
                    from_status TEXT NOT NULL,
                    to_status TEXT NOT NULL,
                    changed_at TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id)
                )
                """
            )
            _ensure_column(conn, "rule_definitions", "definition_hash", "TEXT")
            _ensure_column(conn, "rule_definitions", "schema_version", "TEXT")
            _ensure_column(conn, "trigger_set_versions", "composition_hash", "TEXT")
            _ensure_column(conn, "trigger_set_versions", "schema_version", "TEXT")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


def bootstrap_current_trigger_sets(store: TriggerSetStore, *, created_at: str = "2026-09-05T00:00:00+00:00") -> RegistrySyncReport:
    reports: list[RegistrySyncReport] = [
        store.sync_trigger_registry(current_rule_definitions(created_at=created_at)),
        store.sync_trigger_sets((current_active_trigger_set(created_at=created_at), current_testing_trigger_set(created_at=created_at))),
    ]
    _raise_on_sync_failure(reports[0])
    _raise_on_sync_failure(reports[-1])
    store.transition_status(
        set_id="triggertrade-core",
        version="v1",
        status=TriggerSetStatus.ARCHIVE,
        changed_at=created_at,
        reason="archived by futures runtime migration; spot history remains readable",
    )
    store.transition_status(
        set_id="triggertrade-core-candidate",
        version="v2-test",
        status=TriggerSetStatus.ARCHIVE,
        changed_at=created_at,
        reason="archived by futures runtime migration; spot test history remains readable",
    )
    reports.append(store.sync_trigger_sets((current_futures_active_trigger_set(created_at=created_at), current_futures_testing_trigger_set(created_at=created_at))))
    for report in reports:
        _raise_on_sync_failure(report)
    store.save_recommendation(current_volume_recommendation(created_at=created_at))
    return _merge_reports(tuple(reports))


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
            rule_id="TRG-001",
            version="0.2.0",
            name="Percentage price move",
            status=RuleStatus.ACTIVE,
            asset_scope="BTCUSDT linear perpetual",
            rule_type=RuleType.TRIGGER,
            condition="linear_perpetual_price_change_pct <= configured demo threshold pct",
            definition={
                "lookback_window": "1m",
                "input_contract": "Bybit Demo category=linear BTCUSDT completed 1m close-to-close observation",
                "threshold_source": "TRIGGERTRADE_TRG_001_THRESHOLD_PCT",
                "boundary": "inclusive_lte",
                "demo_only": "true",
                "profitability_claim": "none",
            },
            created_at=created_at,
            provenance="futures integration remediation; preserves TRG-001@0.1.0 spot semantics",
        ),
        RuleDefinition(
            rule_id="TRG-002",
            version="0.1.0",
            name="Robust Volume Confirmation",
            status=RuleStatus.TESTING,
            asset_scope="BTCUSDT spot",
            rule_type=RuleType.TRIGGER,
            condition="relative_volume >= 2.0 AND volume_percentile >= 90",
            definition={
                "logical_name": "TRG-VOLUME",
                "lookback_completed_candles": "60",
                "volume_unit": "Bybit spot base volume",
                "median": "median of previous 60 completed candle volumes; even count uses average of sorted positions 30 and 31",
                "relative_volume": "current_volume / median_volume_60",
                "percentile_rank": "count(previous_volume <= current_volume) / 60 * 100; ties count as <=",
                "boundary": "inclusive: relative_volume >= 2.0 and percentile_rank >= 90",
                "missing_data": "NOT_CONFIRMED for fewer than 60 previous candles, missing current volume, or zero median",
                "stale_data": "NOT_CONFIRMED for stale or incomplete current candle",
                "candidate_only": "true",
                "source_recommendation_id": "REC-TRG-VOLUME-001",
            },
            created_at=created_at,
            provenance="candidate recommendation REC-TRG-VOLUME-001; not validated profitable production rule",
        ),
        RuleDefinition(
            rule_id="TRG-002",
            version="0.2.0",
            name="Robust Volume Confirmation",
            status=RuleStatus.TESTING,
            asset_scope="BTCUSDT linear perpetual",
            rule_type=RuleType.TRIGGER,
            condition="linear relative_volume >= 2.0 AND volume_percentile >= 90",
            definition={
                "logical_name": "TRG-VOLUME",
                "input_contract": "Bybit Demo category=linear BTCUSDT completed 1m candle volume",
                "lookback_completed_candles": "60",
                "volume_unit": "Bybit linear perpetual contract volume",
                "median": "median of previous 60 completed candle volumes; even count uses average of sorted positions 30 and 31",
                "relative_volume": "current_volume / median_volume_60",
                "percentile_rank": "count(previous_volume <= current_volume) / 60 * 100; ties count as <=",
                "boundary": "inclusive: relative_volume >= 2.0 and percentile_rank >= 90",
                "missing_data": "NOT_CONFIRMED for fewer than 60 previous candles, missing current volume, or zero median",
                "stale_data": "NOT_CONFIRMED for stale or incomplete current candle",
                "candidate_only": "true",
                "profitability_claim": "none",
            },
            created_at=created_at,
            provenance="futures integration remediation; preserves TRG-002@0.1.0 spot semantics",
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
            rule_id="STR-FUT-001",
            version="0.1.0",
            name="Integration Directional Futures Strategy",
            status=RuleStatus.ACTIVE,
            asset_scope="BTCUSDT linear perpetual",
            rule_type=RuleType.STRATEGY,
            condition="OPEN_LONG only for FLAT + TRG-001 futures BUY_CANDIDATE + downtrend regime + explicit demo expected move",
            definition={
                "position_state_required": "FLAT",
                "open_long_regimes": "DOWNTREND,STRONG_DOWNTREND",
                "open_short": "not supported in runtime version 0.1.0",
                "close_or_flip": "not supported in runtime version 0.1.0",
                "expected_move_source": "TRIGGERTRADE_DEMO_EXPECTED_GROSS_MOVE; integration-only, not profitability evidence",
                "no_action": "all other trigger/regime/position/expected-move cases",
                "demo_only": "true",
            },
            created_at=created_at,
            provenance="demo-only ACTIVE futures integration strategy; reduced OPEN_LONG-only semantics with no profitability claim",
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
        RuleDefinition(
            rule_id="RSK-FUTURES-001",
            version="0.1.0",
            name="Futures risk profile FRSK-001..FRSK-011",
            status=RuleStatus.ACTIVE,
            asset_scope="BTCUSDT linear perpetual",
            rule_type=RuleType.RISK,
            condition="demo linear futures gates: position/exposure/leverage/margin/duplicate/pause/net-edge/safety",
            definition={"rules": "FRSK-001..FRSK-011", "demo_only": "true", "default_leverage": "1"},
            created_at=created_at,
            provenance="perpetual futures architecture and runtime integration",
        ),
        RuleDefinition(
            rule_id="CTX-REGIME",
            version="0.1.0",
            name="Intraday Market Regime Context",
            status=RuleStatus.ACTIVE,
            asset_scope="BTCUSDT linear perpetual context",
            rule_type=RuleType.CONTEXT,
            condition="classify observed regime from 30 completed 1m closes using return, normalized trend, and directional persistence",
            definition={
                "lookback_completed_candles": "30",
                "timeframe": "1m",
                "window_return_pct": "(latest_close - oldest_close) / oldest_close * 100",
                "avg_abs_step_return_pct": "mean(abs(adjacent close-to-close return pct))",
                "normalized_trend": "window_return_pct / avg_abs_step_return_pct; zero when all steps are zero",
                "directional_persistence": "(up_steps - down_steps) / 29; flat steps count in denominator",
                "strong_uptrend": "window_return_pct >= 0.50 and normalized_trend >= 5 and directional_persistence >= 0.65",
                "uptrend": "window_return_pct >= 0.15 and normalized_trend >= 2 and directional_persistence >= 0.35",
                "strong_downtrend": "window_return_pct <= -0.50 and normalized_trend <= -5 and directional_persistence <= -0.65",
                "downtrend": "window_return_pct <= -0.15 and normalized_trend <= -2 and directional_persistence <= -0.35",
                "sideways": "all other valid completed-candle windows",
                "insufficient_data": "fewer than 30 completed candles or non-positive close",
                "unknown": "unsupported timeframe, incomplete current candle, malformed/non-contiguous window",
                "predictive_claim": "none; classifies observed state only",
            },
            created_at=created_at,
            provenance="lifecycle unit 5 deterministic context classifier; not a trading trigger",
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
        version="v2-test",
        purpose="Forward-test baseline plus TRG-VOLUME v1 candidate confirmation",
        status=TriggerSetStatus.TESTING,
        symbol="BTCUSDT",
        timeframe="1m",
        rule_versions=(("TRG-001", "0.1.0"), ("TRG-002", "0.1.0"), ("STR-001", "0.1.0"), ("RSK-PAPER-001", "0.1.0")),
        strategy_version="STR-001@0.1.0",
        risk_profile_version="RSK-PAPER-001@0.1.0",
        config_snapshot={"threshold": "demo-config", "execution": "isolated_test_paper", "candidate_rule": "TRG-002@0.1.0"},
        created_at=created_at,
        provenance="REC-TRG-VOLUME-001 accepted for TESTING candidate evaluation; ACTIVE set unchanged",
    )


def current_futures_active_trigger_set(*, created_at: str) -> TriggerSetVersion:
    return TriggerSetVersion(
        set_id="triggertrade-futures-core",
        version="v1",
        purpose="Current active Bybit Demo linear futures runtime set",
        status=TriggerSetStatus.ACTIVE,
        symbol="BTCUSDT",
        timeframe="1m",
        rule_versions=(
            ("TRG-001", "0.2.0"),
            ("STR-FUT-001", "0.1.0"),
            ("RSK-FUTURES-001", "0.1.0"),
            ("CTX-REGIME", "0.1.0"),
        ),
        strategy_version="STR-FUT-001@0.1.0",
        risk_profile_version="RSK-FUTURES-001@0.1.0",
        config_snapshot={"market": "linear", "execution": "bybit_demo_futures", "demo_only": "true"},
        created_at=created_at,
        provenance="futures runtime integration remediation; old spot set archived",
    )


def current_futures_testing_trigger_set(*, created_at: str) -> TriggerSetVersion:
    return TriggerSetVersion(
        set_id="triggertrade-futures-candidate",
        version="v2-test",
        purpose="Forward-test futures baseline plus linear TRG-VOLUME confirmation",
        status=TriggerSetStatus.TESTING,
        symbol="BTCUSDT",
        timeframe="1m",
        rule_versions=(
            ("TRG-001", "0.2.0"),
            ("TRG-002", "0.2.0"),
            ("STR-FUT-001", "0.1.0"),
            ("RSK-FUTURES-001", "0.1.0"),
            ("CTX-REGIME", "0.1.0"),
        ),
        strategy_version="STR-FUT-001@0.1.0",
        risk_profile_version="RSK-FUTURES-001@0.1.0",
        config_snapshot={"market": "linear", "execution": "local_test_simulation", "candidate_rule": "TRG-002@0.2.0", "demo_only": "true"},
        created_at=created_at,
        provenance="futures TEST simulator candidate set; no private Bybit calls",
    )


def current_volume_recommendation(*, created_at: str) -> Recommendation:
    return Recommendation(
        recommendation_id="REC-TRG-VOLUME-001",
        created_at=created_at,
        status="TESTING",
        title="Test robust volume confirmation as a candidate filter",
        observation_window_start=None,
        observation_window_end=None,
        source_set_versions=(("triggertrade-core", "v1"),),
        source_rule_versions=(("TRG-001", "0.1.0"),),
        observation="The current active baseline evaluates price-move conditions without a robust completed-candle volume confirmation rule.",
        evidence="Evidence status: proposed experiment only. No historical performance, P&L, win-rate, drawdown, or causal edge is claimed.",
        hypothesis="Price moves accompanied by abnormal relative volume may be a useful candidate filter for forward testing.",
        recommended_experiment="Create a TESTING trigger set equal to the active baseline plus TRG-VOLUME v1, then compare set-vs-set forward evidence.",
        proposed_rule_changes={"add_rule_version": "TRG-002@0.1.0", "logical_name": "TRG-VOLUME", "status": "TESTING"},
        proposed_trigger_set_definition={"set_id": "triggertrade-core-candidate", "version": "v2-test", "membership": ["TRG-001@0.1.0", "TRG-002@0.1.0", "STR-001@0.1.0", "RSK-PAPER-001@0.1.0"]},
        minimum_test_duration="not yet defined; requires explicit human/reviewer decision before evaluation",
        minimum_sample_size="not yet defined; no automatic promotion allowed",
        resulting_test_set_id="triggertrade-core-candidate",
        resulting_test_set_version="v2-test",
        evaluation_summary="Pending forward evidence; performance is evaluated at Trigger Set level, not as an isolated trigger claim.",
        decision="ACCEPTED_FOR_TEST; no ACTIVE promotion",
    )


def _recommendation_payload(recommendation: Recommendation) -> str:
    return json.dumps(recommendation.__dict__, sort_keys=True)


def _recommendation_from_row(row: sqlite3.Row) -> Recommendation:
    data = json.loads(row["payload"])
    data["status"] = row["status"]
    return Recommendation(
        **{
            **data,
            "source_set_versions": tuple(tuple(item) for item in data["source_set_versions"]),
            "source_rule_versions": tuple(tuple(item) for item in data["source_rule_versions"]),
        }
    )

def _rule_definition_payload(rule: RuleDefinition) -> dict[str, object]:
    payload: dict[str, object] = dict(rule.definition)
    semantic_fields = {
        "logical_name": rule.logical_name,
        "description": rule.description,
        "supersedes_version": rule.supersedes_version,
        "formula": rule.formula,
        "parameter_snapshot": rule.parameter_snapshot,
        "input_contract": rule.input_contract,
        "output_contract": rule.output_contract,
        "boundary_semantics": rule.boundary_semantics,
        "stale_data_semantics": rule.stale_data_semantics,
        "missing_data_semantics": rule.missing_data_semantics,
        "change_summary": rule.change_summary,
    }
    metadata = {key: value for key, value in semantic_fields.items() if value is not None}
    if metadata:
        payload["_version_metadata"] = metadata
    return payload


def definition_hash(rule: RuleDefinition) -> str:
    payload = {
        "schema_version": TRIGGER_REGISTRY_SCHEMA_VERSION,
        "trigger_id": rule.rule_id,
        "version": rule.version,
        "rule_type": rule.rule_type.value,
        "implementation_key": _implementation_key(rule),
        "condition": rule.condition,
        "definition": _semantic_definition_payload(rule),
        "formula": rule.formula,
        "parameter_snapshot": rule.parameter_snapshot,
        "input_contract": rule.input_contract,
        "output_contract": rule.output_contract,
        "boundary_semantics": rule.boundary_semantics,
        "stale_data_semantics": rule.stale_data_semantics,
        "missing_data_semantics": rule.missing_data_semantics,
    }
    return _hash_payload(payload)


def composition_hash(trigger_set: TriggerSetVersion) -> str:
    payload = {
        "schema_version": TRIGGER_SET_REGISTRY_SCHEMA_VERSION,
        "set_id": trigger_set.set_id,
        "version": trigger_set.version,
        "purpose": trigger_set.purpose,
        "symbol": trigger_set.symbol,
        "timeframe": trigger_set.timeframe,
        "composition_mode": trigger_set.config_snapshot.get("composition_mode", "ordered_all"),
        "trigger_versions": tuple(
            {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "position": position,
                "role": _membership_role(rule_id),
            }
            for position, (rule_id, rule_version) in enumerate(trigger_set.rule_versions)
        ),
        "strategy_version": trigger_set.strategy_version,
        "risk_profile_version": trigger_set.risk_profile_version,
        "config_snapshot": dict(trigger_set.config_snapshot),
    }
    return _hash_payload(payload)


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


def _validate_rule_definition(rule: RuleDefinition) -> None:
    if not rule.rule_id or not rule.version:
        raise TriggerSetStoreError("trigger_id and version are required")
    if rule.rule_type is RuleType.TRIGGER and not _SEMVER_RE.match(rule.version):
        raise TriggerSetStoreError("trigger versions must use semantic versioning")
    if rule.rule_type is RuleType.TRIGGER and not _implementation_key(rule):
        raise TriggerSetStoreError("implementation_key is required for trigger versions")
    if not rule.condition:
        raise TriggerSetStoreError("condition is required")


def _validate_trigger_set_version(trigger_set: TriggerSetVersion) -> None:
    if not _SET_VERSION_RE.match(trigger_set.version):
        raise TriggerSetStoreError("trigger set version must use vN naming")
    if not trigger_set.rule_versions:
        raise TriggerSetStoreError("trigger set requires at least one rule")
    if any(not rule_id or not version for rule_id, version in trigger_set.rule_versions):
        raise TriggerSetStoreError("trigger set memberships require exact rule_id and version")
    if any(rule_id.startswith("TRG-") and not _SEMVER_RE.match(version) for rule_id, version in trigger_set.rule_versions):
        raise TriggerSetStoreError("trigger set memberships require exact semantic Trigger Versions")


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


def _semantic_definition_payload(rule: RuleDefinition) -> dict[str, object]:
    payload = dict(rule.definition)
    metadata = payload.get("_version_metadata")
    if isinstance(metadata, dict):
        metadata = {
            key: value
            for key, value in metadata.items()
            if key not in {"definition_hash", "semantic_hash", "schema_version"}
        }
        if metadata:
            payload["_version_metadata"] = metadata
        else:
            payload.pop("_version_metadata", None)
    return payload


def _definition_hash_from_row(row: sqlite3.Row) -> str:
    try:
        return definition_hash(_row_to_rule(row))
    except Exception:
        return _LEGACY_UNVERIFIED_DEFINITION_HASH


def _implementation_key(rule: RuleDefinition) -> str:
    explicit = rule.definition.get("implementation_key")
    if explicit:
        return str(explicit)
    logical = rule.logical_name or rule.definition.get("logical_name")
    known = {
        "TRG-001": "triggertrade.triggers.PercentagePriceMoveTrigger",
        "TRG-002": "triggertrade.triggers.RobustVolumeConfirmationTrigger",
        "CTX-REGIME": "triggertrade.market_data.regime.evaluate_market_regime",
        "STR-001": "triggertrade.strategies.BuyCandidateStrategy",
        "STR-FUT-001": "triggertrade.strategies.IntegrationDirectionalFuturesStrategy",
        "RSK-PAPER-001": "triggertrade.risk.RiskManager",
        "RSK-FUTURES-001": "triggertrade.execution.futures.FuturesRiskManager",
    }
    return known.get(rule.rule_id, "" if logical is None else str(logical))


def _membership_role(rule_id: str) -> str:
    if rule_id.startswith("TRG-"):
        return "TRIGGER"
    if rule_id.startswith("STR-"):
        return "STRATEGY"
    if rule_id.startswith("RSK-"):
        return "RISK"
    if rule_id.startswith("CTX-"):
        return "CONTEXT"
    return "MEMBER"


def _hash_payload(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _merge_reports(reports: tuple[RegistrySyncReport, ...]) -> RegistrySyncReport:
    return RegistrySyncReport(
        unchanged_versions=tuple(item for report in reports for item in report.unchanged_versions),
        new_versions_registered=tuple(item for report in reports for item in report.new_versions_registered),
        conflicts=tuple(item for report in reports for item in report.conflicts),
        invalid_definitions=tuple(item for report in reports for item in report.invalid_definitions),
        warnings=tuple(item for report in reports for item in report.warnings),
    )


def _raise_on_sync_failure(report: RegistrySyncReport) -> None:
    failures = report.conflicts + report.invalid_definitions
    if failures:
        raise TriggerSetStoreError("; ".join(failures))


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
        semantic_hash=row["definition_hash"] if "definition_hash" in row.keys() else None,
    )
