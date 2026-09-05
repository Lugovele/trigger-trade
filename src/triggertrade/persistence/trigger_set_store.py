"""SQLite persistence for rule registry and versioned Trigger Sets."""

from __future__ import annotations

from pathlib import Path
import json
import sqlite3
from typing import Iterable

from triggertrade.trigger_sets import Recommendation, RuleDefinition, RuleStatus, RuleType, TriggerSetStatus, TriggerSetVersion


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


class TriggerSetStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_rule(self, rule: RuleDefinition) -> RuleDefinition:
        definition = json.dumps(_rule_definition_payload(rule), sort_keys=True)
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

    def get_rule(self, rule_id: str, version: str | None = None) -> RuleDefinition | None:
        with self._connect() as conn:
            if version is None:
                row = conn.execute(
                    """
                    SELECT rule_id, version, name, status, asset_scope, rule_type,
                           condition, definition, created_at, updated_at, provenance
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
                           condition, definition, created_at, updated_at, provenance
                    FROM rule_definitions
                    WHERE rule_id = ? AND version = ?
                    """,
                    (rule_id, version),
                ).fetchone()
        return None if row is None else _row_to_rule(row)

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

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


def bootstrap_current_trigger_sets(store: TriggerSetStore, *, created_at: str = "2026-09-05T00:00:00+00:00") -> None:
    for rule in current_rule_definitions(created_at=created_at):
        store.save_rule(rule)
    store.create_set(current_active_trigger_set(created_at=created_at))
    store.create_set(current_testing_trigger_set(created_at=created_at))
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
    store.create_set(current_futures_active_trigger_set(created_at=created_at))
    store.create_set(current_futures_testing_trigger_set(created_at=created_at))
    store.save_recommendation(current_volume_recommendation(created_at=created_at))


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
        "semantic_hash": rule.semantic_hash,
        "change_summary": rule.change_summary,
    }
    metadata = {key: value for key, value in semantic_fields.items() if value is not None}
    if metadata:
        payload["_version_metadata"] = metadata
    return payload


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
