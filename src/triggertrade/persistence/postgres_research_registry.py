"""PostgreSQL-backed immutable Research configuration registry."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
import json
from typing import Any, Protocol

from triggertrade.persistence.postgres import (
    OwnerStateRecord,
    OwnerStateRevisionConflict,
    OwnerStateStore,
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresUnitOfWork,
)
from triggertrade.persistence.research_store import (
    RESEARCH_SCHEMA_VERSION,
    ResearchBacktestRunRecord,
    ResearchBacktestStatus,
    ResearchDecision,
    ResearchDemoRunRecord,
    ResearchDemoStatus,
    ResearchRecord,
    ResearchStatus,
    ResearchStoreError,
    _checked,
    _clean_text,
    _now,
    _pin_json_and_digest,
    _research_id,
    _research_status_after_backtest,
    _research_status_after_demo,
    _run_id,
)
from triggertrade.research_pins import default_store_research_pin_payload, research_run_pin_payload
from triggertrade.rules import TradingRulesVersion
from triggertrade.rules.trading import draft_from_json, draft_to_json
from triggertrade.trigger_sets import TriggerSetStatus, TriggerSetVersion


RESEARCH_CONFIG_OWNER = "ResearchConfigurationRegistry"
RESEARCH_STATE_TYPE = "RESEARCH_DEFINITION"
TRIGGER_SET_STATE_TYPE = "TRIGGER_SET_VERSION"
TRADING_RULES_STATE_TYPE = "TRADING_RULES_VERSION"
RESEARCH_RUN_OWNER = "ResearchRunStore"
RESEARCH_MUTABLE_STATE_TYPE = "RESEARCH_MUTABLE_STATE"
RESEARCH_BACKTEST_RUN_STATE_TYPE = "RESEARCH_BACKTEST_RUN"
RESEARCH_DEMO_RUN_STATE_TYPE = "RESEARCH_DEMO_RUN"
RESEARCH_DEMO_EXECUTION_OWNER = "ResearchDemoExecution"
RESEARCH_DEMO_EXECUTION_STATE_TYPE = "RESEARCH_DEMO_RUN"


class ResearchConfigurationRegistryError(PostgresPersistenceError):
    """Raised when exact Research Demo configuration cannot be reconstructed."""


@dataclass(frozen=True)
class ResearchDemoConfiguration:
    research: ResearchRecord
    trigger_set: TriggerSetVersion
    rules: TradingRulesVersion


class ResearchConfigurationRegistryWriter(Protocol):
    def put_configuration(
        self,
        *,
        research: ResearchRecord,
        trigger_set: TriggerSetVersion,
        rules: TradingRulesVersion,
    ) -> None: ...


class PostgresResearchConfigurationRegistry:
    """Exact-version Research/Set/Rules registry backed by owner-state records."""

    def __init__(self, connection) -> None:
        self._connection = connection
        self._store = OwnerStateStore(connection)

    def put_configuration(
        self,
        *,
        research: ResearchRecord,
        trigger_set: TriggerSetVersion,
        rules: TradingRulesVersion,
    ) -> None:
        if research.set_id != trigger_set.set_id or research.set_version != trigger_set.version:
            raise ResearchConfigurationRegistryError("research pins do not match trigger set version")
        if research.rules_version_id != rules.rules_version_id:
            raise ResearchConfigurationRegistryError("research pins do not match trading rules version")
        self.put_research(research)
        self.put_trigger_set_version(trigger_set)
        self.put_trading_rules_version(rules)

    def put_research(self, research: ResearchRecord) -> tuple[ResearchRecord, bool]:
        record, created = self._store.put_if_absent(
            owner=RESEARCH_CONFIG_OWNER,
            state_type=RESEARCH_STATE_TYPE,
            state_id=research.research_id,
            payload=_research_payload(research),
        )
        return _research_from_owner(record), created

    def get_research(self, research_id: str) -> ResearchRecord | None:
        record = self._store.get(
            owner=RESEARCH_CONFIG_OWNER,
            state_type=RESEARCH_STATE_TYPE,
            state_id=_required_text(research_id, field="research_id"),
        )
        return None if record is None else _research_from_owner(record)

    def list_research(self) -> tuple[ResearchRecord, ...]:
        return tuple(
            _research_from_owner(record)
            for record in self._list_records(state_type=RESEARCH_STATE_TYPE)
        )

    def put_trigger_set_version(self, trigger_set: TriggerSetVersion) -> tuple[TriggerSetVersion, bool]:
        record, created = self._store.put_if_absent(
            owner=RESEARCH_CONFIG_OWNER,
            state_type=TRIGGER_SET_STATE_TYPE,
            state_id=_trigger_set_key(trigger_set.set_id, trigger_set.version),
            payload=_trigger_set_payload(trigger_set),
        )
        return _trigger_set_from_owner(record), created

    def get_trigger_set_version(self, set_id: str, version: str) -> TriggerSetVersion | None:
        record = self._store.get(
            owner=RESEARCH_CONFIG_OWNER,
            state_type=TRIGGER_SET_STATE_TYPE,
            state_id=_trigger_set_key(set_id, version),
        )
        return None if record is None else _trigger_set_from_owner(record)

    def put_trading_rules_version(self, rules: TradingRulesVersion) -> tuple[TradingRulesVersion, bool]:
        record, created = self._store.put_if_absent(
            owner=RESEARCH_CONFIG_OWNER,
            state_type=TRADING_RULES_STATE_TYPE,
            state_id=rules.rules_version_id,
            payload=_rules_payload(rules),
        )
        return _rules_from_owner(record), created

    def get_trading_rules_version(self, rules_version_id: str) -> TradingRulesVersion | None:
        record = self._store.get(
            owner=RESEARCH_CONFIG_OWNER,
            state_type=TRADING_RULES_STATE_TYPE,
            state_id=_required_text(rules_version_id, field="rules_version_id"),
        )
        return None if record is None else _rules_from_owner(record)

    def list_trigger_set_versions(self) -> tuple[TriggerSetVersion, ...]:
        return tuple(
            _trigger_set_from_owner(record)
            for record in self._list_records(state_type=TRIGGER_SET_STATE_TYPE)
        )

    def list_trading_rules_versions(self) -> tuple[TradingRulesVersion, ...]:
        return tuple(
            _rules_from_owner(record)
            for record in self._list_records(state_type=TRADING_RULES_STATE_TYPE)
        )

    def _list_records(self, *, state_type: str) -> tuple[OwnerStateRecord, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT owner, state_type, state_id, revision, payload_json::text, payload_digest
                FROM triggertrade_owner_state_records
                WHERE owner = %s AND state_type = %s
                ORDER BY payload_json->>'created_at' DESC, state_id
                """,
                (RESEARCH_CONFIG_OWNER, state_type),
            )
            rows = cursor.fetchall()
        return tuple(
            OwnerStateRecord(
                owner=str(row[0]),
                state_type=str(row[1]),
                state_id=str(row[2]),
                revision=int(row[3]),
                payload=json.loads(str(row[4])),
                payload_digest=str(row[5]),
            )
            for row in rows
        )

    def get_research_demo_configuration(
        self,
        *,
        research_id: str,
        set_id: str,
        set_version: str,
        rules_version_id: str,
    ) -> ResearchDemoConfiguration:
        research = self.get_research(research_id)
        trigger_set = self.get_trigger_set_version(set_id, set_version)
        rules = self.get_trading_rules_version(rules_version_id)
        missing = [
            name
            for name, value in (
                ("research", research),
                ("trigger_set_version", trigger_set),
                ("trading_rules_version", rules),
            )
            if value is None
        ]
        if missing:
            raise ResearchConfigurationRegistryError(
                f"exact Research Demo configuration missing: {', '.join(missing)}"
            )
        if research.set_id != trigger_set.set_id or research.set_version != trigger_set.version:
            raise ResearchConfigurationRegistryError("reconstructed research does not match trigger set version")
        if research.rules_version_id != rules.rules_version_id:
            raise ResearchConfigurationRegistryError("reconstructed research does not match trading rules version")
        return ResearchDemoConfiguration(research=research, trigger_set=trigger_set, rules=rules)


class PostgresResearchRunStore:
    """Shared Research mutable/run state over PostgreSQL owner-state records."""

    path = None

    def __init__(self, connection) -> None:
        self._connection = connection
        self._registry = PostgresResearchConfigurationRegistry(connection)
        self._store = OwnerStateStore(connection)

    def create_research(
        self,
        *,
        set_id: str,
        set_version: str,
        rules_version_id: str,
        rules_display_version: str,
        created_source: str,
        pin_payload: dict[str, Any] | None = None,
        created_at: str | None = None,
        before_insert=None,
    ) -> tuple[ResearchRecord, bool]:
        set_id = _checked(set_id, "set_id")
        set_version = _checked(set_version, "set_version")
        rules_version_id = _checked(rules_version_id, "rules_version_id")
        created_at = created_at or _now()
        clean_source = _clean_text(created_source, "created_source", 80)
        clean_display_version = _clean_text(rules_display_version, "rules_display_version", 40)
        pins = pin_payload or default_store_research_pin_payload(
            set_id=set_id,
            set_version=set_version,
            rules_version_id=rules_version_id,
            rules_display_version=clean_display_version,
            created_source=clean_source,
            schema_version=RESEARCH_SCHEMA_VERSION,
        )
        _pin_json, pin_digest = _pin_json_and_digest(pins)
        research_id = _research_id(set_id, set_version, rules_version_id, pin_digest)
        existing = self.get_research(research_id)
        if existing is not None:
            return existing, False
        record = ResearchRecord(
            research_id=research_id,
            created_at=created_at,
            updated_at=created_at,
            status=ResearchStatus.DRAFT,
            set_id=set_id,
            set_version=set_version,
            rules_version_id=rules_version_id,
            rules_display_version=clean_display_version,
            selected_backtest_run_id=None,
            selected_demo_run_id=None,
            decision=ResearchDecision.NONE,
            decision_at=None,
            archived_at=None,
            made_active_at=None,
            promoted_set_id=None,
            promoted_set_version=None,
            promoted_rules_version_id=None,
            previous_active_set_id=None,
            previous_active_set_version=None,
            previous_rules_version_id=None,
            promotion_result_metadata={},
            created_source=clean_source,
            schema_version=RESEARCH_SCHEMA_VERSION,
            pin_payload=pins,
            pin_digest=pin_digest,
        )
        if before_insert is not None:
            before_insert(record)
        else:
            self._registry.put_research(record)
        self._put_mutable_state(_mutable_payload(record))
        stored = self.get_research(research_id)
        if stored is None:
            raise ResearchStoreError("research id not found after PostgreSQL create")
        return stored, True

    def list_research(self, *, limit: int = 50) -> tuple[ResearchRecord, ...]:
        records = tuple(self.get_research(record.research_id) or record for record in self._registry.list_research())
        return records[: max(1, min(int(limit), 100))]

    def get_research(self, research_id: str) -> ResearchRecord | None:
        research = self._registry.get_research(_checked(research_id, "research_id"))
        if research is None:
            return None
        mutable = self._get_mutable_state(research.research_id)
        return research if mutable is None else _apply_mutable_state(research, mutable)

    def add_backtest_run(
        self,
        *,
        research_id: str,
        period_start: str,
        period_end: str,
        timeframe: str,
        status: ResearchBacktestStatus,
        engine_run_id: str | None = None,
        metrics: dict[str, Any] | None = None,
        unavailable_reason: str | None = None,
        pin_payload: dict[str, Any] | None = None,
        created_at: str | None = None,
    ) -> ResearchBacktestRunRecord:
        research = self._required_research(research_id)
        created_at = created_at or _now()
        if engine_run_id is not None:
            engine_run_id = _checked(engine_run_id, "engine_run_id")
        pins = pin_payload or research_run_pin_payload(
            research_pin_digest_value=research.pin_digest,
            run_kind="BACKTEST",
            run_inputs={
                "period_start": period_start,
                "period_end": period_end,
                "timeframe": timeframe,
                "engine_run_id": engine_run_id,
                "status": status.value,
            },
        )
        _pin_json, pin_digest = _pin_json_and_digest(pins)
        run_id = _run_id("rbt", research.research_id, pin_digest, created_at)
        record = ResearchBacktestRunRecord(
            research_id=research.research_id,
            run_id=run_id,
            created_at=created_at,
            updated_at=created_at,
            status=status,
            period_start=_clean_text(period_start, "period_start", 80),
            period_end=_clean_text(period_end, "period_end", 80),
            timeframe=_clean_text(timeframe, "timeframe", 20),
            engine_run_id=engine_run_id,
            selected_for_use=False,
            metrics=_jsonable(metrics or {}),
            unavailable_reason=None if unavailable_reason is None else _clean_text(unavailable_reason, "unavailable_reason", 240),
            pin_payload=pins,
            pin_digest=pin_digest,
        )
        self._store.put_if_absent(
            owner=RESEARCH_RUN_OWNER,
            state_type=RESEARCH_BACKTEST_RUN_STATE_TYPE,
            state_id=_run_state_key(research.research_id, run_id),
            payload=_backtest_payload(record),
        )
        self._update_mutable_state(
            research.research_id,
            updated_at=created_at,
            status=_research_status_after_backtest(status),
        )
        stored = self.get_backtest_run(research.research_id, run_id)
        if stored is None:
            raise ResearchStoreError("backtest run not found after PostgreSQL insert")
        return stored

    def get_backtest_run(self, research_id: str, run_id: str) -> ResearchBacktestRunRecord | None:
        record = self._store.get(
            owner=RESEARCH_RUN_OWNER,
            state_type=RESEARCH_BACKTEST_RUN_STATE_TYPE,
            state_id=_run_state_key(_checked(research_id, "research_id"), _checked(run_id, "run_id")),
        )
        return None if record is None else _backtest_from_owner(record)

    def update_backtest_run(
        self,
        *,
        research_id: str,
        run_id: str,
        status: ResearchBacktestStatus,
        engine_run_id: str | None = None,
        metrics: dict[str, Any] | None = None,
        unavailable_reason: str | None = None,
        updated_at: str | None = None,
    ) -> ResearchBacktestRunRecord:
        research_id = _checked(research_id, "research_id")
        run_id = _checked(run_id, "run_id")
        updated_at = updated_at or _now()
        state_id = _run_state_key(research_id, run_id)
        for _ in range(3):
            owner = self._store.get(owner=RESEARCH_RUN_OWNER, state_type=RESEARCH_BACKTEST_RUN_STATE_TYPE, state_id=state_id)
            if owner is None:
                raise ResearchStoreError("backtest run id not found for research")
            current = _backtest_from_owner(owner)
            updated = replace(
                current,
                updated_at=updated_at,
                status=status,
                engine_run_id=None if engine_run_id is None else _checked(engine_run_id, "engine_run_id"),
                metrics=_jsonable(metrics or {}),
                unavailable_reason=None if unavailable_reason is None else _clean_text(unavailable_reason, "unavailable_reason", 240),
            )
            try:
                stored = self._store.compare_and_set(
                    owner=RESEARCH_RUN_OWNER,
                    state_type=RESEARCH_BACKTEST_RUN_STATE_TYPE,
                    state_id=state_id,
                    expected_revision=owner.revision,
                    payload=_backtest_payload(updated),
                )
                self._update_mutable_state(research_id, updated_at=updated_at, status=_research_status_after_backtest(status))
                return _backtest_from_owner(stored)
            except OwnerStateRevisionConflict:
                continue
        raise OwnerStateRevisionConflict("research backtest run changed concurrently")

    def list_backtest_runs(self, research_id: str) -> tuple[ResearchBacktestRunRecord, ...]:
        research_id = _checked(research_id, "research_id")
        rows = self._list_run_records(state_type=RESEARCH_BACKTEST_RUN_STATE_TYPE, research_id=research_id)
        return tuple(_backtest_from_owner(record) for record in rows)

    def select_backtest_run(self, research_id: str, run_id: str, *, selected_at: str | None = None) -> ResearchRecord:
        selected_at = selected_at or _now()
        run = self.get_backtest_run(research_id, run_id)
        if run is None:
            raise ResearchStoreError("backtest run id not found for research")
        if run.status not in {ResearchBacktestStatus.COMPLETED, ResearchBacktestStatus.COMPLETED_NO_TRADES}:
            raise ResearchStoreError("only completed backtest runs can be selected")
        self._set_backtest_selected(research_id, run_id, selected_at=selected_at)
        self._update_mutable_state(
            research_id,
            updated_at=selected_at,
            status=ResearchStatus.BACKTEST_READY,
            selected_backtest_run_id=run_id,
        )
        return self._required_research(research_id)

    def add_demo_run(
        self,
        *,
        research_id: str,
        status: ResearchDemoStatus,
        run_id: str | None = None,
        started_at: str | None = None,
        stopped_at: str | None = None,
        execution_scope_id: str | None = None,
        account_scope: str | None = None,
        metrics: dict[str, Any] | None = None,
        blocked_reason: str | None = None,
        pin_payload: dict[str, Any] | None = None,
        created_at: str | None = None,
    ) -> ResearchDemoRunRecord:
        research = self._required_research(research_id)
        created_at = created_at or _now()
        pins = pin_payload or research_run_pin_payload(
            research_pin_digest_value=research.pin_digest,
            run_kind="DEMO",
            run_inputs={
                "status": status.value,
                "started_at": started_at,
                "stopped_at": stopped_at,
                "execution_scope_id": execution_scope_id,
                "account_scope": account_scope,
                "blocked_reason": blocked_reason,
            },
        )
        _pin_json, pin_digest = _pin_json_and_digest(pins)
        run_id = _checked(run_id, "run_id") if run_id is not None else _run_id("rdm", research.research_id, pin_digest, created_at)
        record = ResearchDemoRunRecord(
            research_id=research.research_id,
            run_id=run_id,
            created_at=created_at,
            updated_at=created_at,
            status=status,
            started_at=started_at,
            stopped_at=stopped_at,
            execution_scope_id=None if execution_scope_id is None else _clean_text(execution_scope_id, "execution_scope_id", 160),
            account_scope=None if account_scope is None else _clean_text(account_scope, "account_scope", 160),
            selected_for_use=False,
            metrics=_jsonable(metrics or {}),
            blocked_reason=None if blocked_reason is None else _clean_text(blocked_reason, "blocked_reason", 240),
            pin_payload=pins,
            pin_digest=pin_digest,
        )
        self._store.put_if_absent(
            owner=RESEARCH_RUN_OWNER,
            state_type=RESEARCH_DEMO_RUN_STATE_TYPE,
            state_id=_run_state_key(research.research_id, run_id),
            payload=_demo_payload(record),
        )
        self._update_mutable_state(
            research.research_id,
            updated_at=created_at,
            status=_research_status_after_demo(status),
        )
        stored = self.get_demo_run(research.research_id, run_id)
        if stored is None:
            raise ResearchStoreError("demo run not found after PostgreSQL insert")
        return stored

    def get_demo_run(self, research_id: str, run_id: str) -> ResearchDemoRunRecord | None:
        record = self._store.get(
            owner=RESEARCH_RUN_OWNER,
            state_type=RESEARCH_DEMO_RUN_STATE_TYPE,
            state_id=_run_state_key(_checked(research_id, "research_id"), _checked(run_id, "run_id")),
        )
        return None if record is None else _demo_from_owner(record)

    def list_demo_runs(self, research_id: str) -> tuple[ResearchDemoRunRecord, ...]:
        research_id = _checked(research_id, "research_id")
        rows = self._list_run_records(state_type=RESEARCH_DEMO_RUN_STATE_TYPE, research_id=research_id)
        projected_by_id = {record.run_id: record for record in (_demo_from_owner(row) for row in rows)}
        for execution_record in self._list_research_demo_execution_records(research_id):
            execution_projection = _demo_from_execution_owner(execution_record)
            existing = projected_by_id.get(execution_projection.run_id)
            projected_by_id[execution_projection.run_id] = (
                execution_projection if existing is None else _merge_demo_execution_projection(existing, execution_projection)
            )
        return tuple(sorted(projected_by_id.values(), key=lambda record: (record.created_at, record.run_id), reverse=True))

    def stop_demo_run(self, research_id: str, run_id: str, *, stopped_at: str | None = None) -> ResearchDemoRunRecord:
        stopped_at = stopped_at or _now()
        run = self.get_demo_run(research_id, run_id)
        if run is None:
            raise ResearchStoreError("demo run id not found for research")
        if run.status is ResearchDemoStatus.RUNNING:
            run = replace(run, status=ResearchDemoStatus.STOPPED, stopped_at=stopped_at, updated_at=stopped_at)
            self._replace_run_payload(
                state_type=RESEARCH_DEMO_RUN_STATE_TYPE,
                state_id=_run_state_key(research_id, run_id),
                payload=_demo_payload(run),
            )
            self._update_mutable_state(research_id, updated_at=stopped_at, status=ResearchStatus.DEMO_STOPPED)
        return run

    def select_demo_run(self, research_id: str, run_id: str, *, selected_at: str | None = None) -> ResearchRecord:
        selected_at = selected_at or _now()
        run = self.get_demo_run(research_id, run_id)
        if run is None:
            raise ResearchStoreError("demo run id not found for research")
        if run.status is not ResearchDemoStatus.STOPPED:
            raise ResearchStoreError("only stopped demo runs can be selected")
        self._set_demo_selected(research_id, run_id, selected_at=selected_at)
        self._update_mutable_state(
            research_id,
            updated_at=selected_at,
            status=ResearchStatus.DECISION_NEEDED,
            selected_demo_run_id=run_id,
        )
        return self._required_research(research_id)

    def archive_research(self, research_id: str, *, archived_at: str | None = None) -> ResearchRecord:
        archived_at = archived_at or _now()
        self._required_research(research_id)
        self._update_mutable_state(
            research_id,
            updated_at=archived_at,
            status=ResearchStatus.ARCHIVED,
            decision=ResearchDecision.ARCHIVE,
            decision_at=archived_at,
            archived_at=archived_at,
        )
        return self._required_research(research_id)

    def record_make_active_blocked(self, research_id: str, *, reason: str, decided_at: str | None = None) -> ResearchRecord:
        decided_at = decided_at or _now()
        self._required_research(research_id)
        self._update_mutable_state(
            research_id,
            updated_at=decided_at,
            decision=ResearchDecision.MAKE_ACTIVE_BLOCKED,
            decision_at=decided_at,
        )
        return self._required_research(research_id)

    def _required_research(self, research_id: str) -> ResearchRecord:
        research = self.get_research(research_id)
        if research is None:
            raise ResearchStoreError("research id not found")
        return research

    def _get_mutable_state(self, research_id: str) -> dict[str, Any] | None:
        record = self._store.get(
            owner=RESEARCH_RUN_OWNER,
            state_type=RESEARCH_MUTABLE_STATE_TYPE,
            state_id=_checked(research_id, "research_id"),
        )
        return None if record is None else dict(record.payload)

    def _put_mutable_state(self, payload: dict[str, Any]) -> None:
        self._store.put_if_absent(
            owner=RESEARCH_RUN_OWNER,
            state_type=RESEARCH_MUTABLE_STATE_TYPE,
            state_id=_required_text(payload.get("research_id"), field="research_id"),
            payload=payload,
        )

    def _update_mutable_state(self, research_id: str, **changes: Any) -> None:
        research = self._registry.get_research(_checked(research_id, "research_id"))
        if research is None:
            raise ResearchStoreError("research id not found")
        base = self._get_mutable_state(research_id) or _mutable_payload(research)
        base.update(_mutable_change_payload(changes))
        while True:
            existing = self._store.get(
                owner=RESEARCH_RUN_OWNER,
                state_type=RESEARCH_MUTABLE_STATE_TYPE,
                state_id=research_id,
            )
            if existing is None:
                self._store.put_if_absent(
                    owner=RESEARCH_RUN_OWNER,
                    state_type=RESEARCH_MUTABLE_STATE_TYPE,
                    state_id=research_id,
                    payload=base,
                )
                return
            try:
                self._store.compare_and_set(
                    owner=RESEARCH_RUN_OWNER,
                    state_type=RESEARCH_MUTABLE_STATE_TYPE,
                    state_id=research_id,
                    expected_revision=existing.revision,
                    payload=base,
                )
                return
            except OwnerStateRevisionConflict:
                reloaded = self._store.get(
                    owner=RESEARCH_RUN_OWNER,
                    state_type=RESEARCH_MUTABLE_STATE_TYPE,
                    state_id=research_id,
                )
                base = _mutable_payload(research) if reloaded is None else dict(reloaded.payload)
                base.update(_mutable_change_payload(changes))

    def _list_run_records(self, *, state_type: str, research_id: str) -> tuple[OwnerStateRecord, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT owner, state_type, state_id, revision, payload_json::text, payload_digest
                FROM triggertrade_owner_state_records
                WHERE owner = %s AND state_type = %s AND payload_json->>'research_id' = %s
                ORDER BY payload_json->>'created_at' DESC, state_id DESC
                """,
                (RESEARCH_RUN_OWNER, state_type, research_id),
            )
            rows = cursor.fetchall()
        return tuple(
            OwnerStateRecord(
                owner=str(row[0]),
                state_type=str(row[1]),
                state_id=str(row[2]),
                revision=int(row[3]),
                payload=json.loads(str(row[4])),
                payload_digest=str(row[5]),
            )
            for row in rows
        )

    def _list_research_demo_execution_records(self, research_id: str) -> tuple[OwnerStateRecord, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT owner, state_type, state_id, revision, payload_json::text, payload_digest
                FROM triggertrade_owner_state_records
                WHERE owner = %s AND state_type = %s AND payload_json->>'research_id' = %s
                ORDER BY payload_json->>'requested_at' DESC, state_id DESC
                """,
                (RESEARCH_DEMO_EXECUTION_OWNER, RESEARCH_DEMO_EXECUTION_STATE_TYPE, research_id),
            )
            rows = cursor.fetchall()
        return tuple(
            OwnerStateRecord(
                owner=str(row[0]),
                state_type=str(row[1]),
                state_id=str(row[2]),
                revision=int(row[3]),
                payload=json.loads(str(row[4])),
                payload_digest=str(row[5]),
            )
            for row in rows
        )

    def _replace_run_payload(self, *, state_type: str, state_id: str, payload: dict[str, Any]) -> None:
        while True:
            existing = self._store.get(owner=RESEARCH_RUN_OWNER, state_type=state_type, state_id=state_id)
            if existing is None:
                raise ResearchStoreError("run record not found")
            try:
                self._store.compare_and_set(
                    owner=RESEARCH_RUN_OWNER,
                    state_type=state_type,
                    state_id=state_id,
                    expected_revision=existing.revision,
                    payload=payload,
                )
                return
            except OwnerStateRevisionConflict:
                continue

    def _set_backtest_selected(self, research_id: str, run_id: str, *, selected_at: str) -> None:
        for run in self.list_backtest_runs(research_id):
            updated = replace(run, selected_for_use=(run.run_id == run_id), updated_at=selected_at)
            self._replace_run_payload(
                state_type=RESEARCH_BACKTEST_RUN_STATE_TYPE,
                state_id=_run_state_key(research_id, run.run_id),
                payload=_backtest_payload(updated),
            )

    def _set_demo_selected(self, research_id: str, run_id: str, *, selected_at: str) -> None:
        for run in self.list_demo_runs(research_id):
            updated = replace(run, selected_for_use=(run.run_id == run_id), updated_at=selected_at)
            self._replace_run_payload(
                state_type=RESEARCH_DEMO_RUN_STATE_TYPE,
                state_id=_run_state_key(research_id, run.run_id),
                payload=_demo_payload(updated),
            )


class PostgresResearchConfigurationRegistryClient:
    """Unit-of-work wrapper for production write/read boundaries."""

    path = None

    def __init__(self, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def put_configuration(
        self,
        *,
        research: ResearchRecord,
        trigger_set: TriggerSetVersion,
        rules: TradingRulesVersion,
    ) -> None:
        with PostgresUnitOfWork(self._factory) as uow:
            PostgresResearchConfigurationRegistry(uow.connection).put_configuration(
                research=research,
                trigger_set=trigger_set,
                rules=rules,
            )

    def put_trigger_set_version(self, trigger_set: TriggerSetVersion) -> None:
        with PostgresUnitOfWork(self._factory) as uow:
            PostgresResearchConfigurationRegistry(uow.connection).put_trigger_set_version(trigger_set)

    def put_trading_rules_version(self, rules: TradingRulesVersion) -> None:
        with PostgresUnitOfWork(self._factory) as uow:
            PostgresResearchConfigurationRegistry(uow.connection).put_trading_rules_version(rules)

    def get_research_demo_configuration(
        self,
        *,
        research_id: str,
        set_id: str,
        set_version: str,
        rules_version_id: str,
    ) -> ResearchDemoConfiguration:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchConfigurationRegistry(uow.connection).get_research_demo_configuration(
                research_id=research_id,
                set_id=set_id,
                set_version=set_version,
                rules_version_id=rules_version_id,
            )

    def get_research(self, research_id: str) -> ResearchRecord | None:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).get_research(research_id)

    def list_research(self) -> tuple[ResearchRecord, ...]:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).list_research()

    def list_trigger_set_versions(self) -> tuple[TriggerSetVersion, ...]:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchConfigurationRegistry(uow.connection).list_trigger_set_versions()

    def list_trading_rules_versions(self) -> tuple[TradingRulesVersion, ...]:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchConfigurationRegistry(uow.connection).list_trading_rules_versions()

    def create_research(self, **kwargs: Any) -> tuple[ResearchRecord, bool]:
        before_insert = kwargs.pop("before_insert", None)
        if before_insert is not None:
            candidate = _candidate_research_from_create_kwargs(**kwargs)
            existing = self.get_research(candidate.research_id)
            if existing is not None:
                return existing, False
            before_insert(candidate)
            with PostgresUnitOfWork(self._factory) as uow:
                store = PostgresResearchRunStore(uow.connection)
                store._put_mutable_state(_mutable_payload(candidate))
                stored = store.get_research(candidate.research_id)
                if stored is None:
                    raise ResearchStoreError("research id not found after PostgreSQL create")
                return stored, True
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).create_research(**kwargs)

    def add_backtest_run(self, **kwargs: Any) -> ResearchBacktestRunRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).add_backtest_run(**kwargs)

    def get_backtest_run(self, research_id: str, run_id: str) -> ResearchBacktestRunRecord | None:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).get_backtest_run(research_id, run_id)

    def list_backtest_runs(self, research_id: str) -> tuple[ResearchBacktestRunRecord, ...]:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).list_backtest_runs(research_id)

    def select_backtest_run(self, research_id: str, run_id: str, *, selected_at: str | None = None) -> ResearchRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).select_backtest_run(
                research_id,
                run_id,
                selected_at=selected_at,
            )

    def add_demo_run(self, **kwargs: Any) -> ResearchDemoRunRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).add_demo_run(**kwargs)

    def get_demo_run(self, research_id: str, run_id: str) -> ResearchDemoRunRecord | None:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).get_demo_run(research_id, run_id)

    def list_demo_runs(self, research_id: str) -> tuple[ResearchDemoRunRecord, ...]:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).list_demo_runs(research_id)

    def stop_demo_run(self, research_id: str, run_id: str, *, stopped_at: str | None = None) -> ResearchDemoRunRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).stop_demo_run(
                research_id,
                run_id,
                stopped_at=stopped_at,
            )

    def select_demo_run(self, research_id: str, run_id: str, *, selected_at: str | None = None) -> ResearchRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).select_demo_run(
                research_id,
                run_id,
                selected_at=selected_at,
            )

    def archive_research(self, research_id: str, *, archived_at: str | None = None) -> ResearchRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).archive_research(
                research_id,
                archived_at=archived_at,
            )

    def record_make_active_blocked(self, research_id: str, *, reason: str, decided_at: str | None = None) -> ResearchRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).record_make_active_blocked(
                research_id,
                reason=reason,
                decided_at=decided_at,
            )


def _research_payload(research: ResearchRecord) -> dict[str, Any]:
    return {
        "schema": RESEARCH_STATE_TYPE,
        "research_id": research.research_id,
        "created_at": research.created_at,
        "set_id": research.set_id,
        "set_version": research.set_version,
        "rules_version_id": research.rules_version_id,
        "rules_display_version": research.rules_display_version,
        "created_source": research.created_source,
        "schema_version": research.schema_version,
        "pin_payload": dict(research.pin_payload),
        "pin_digest": research.pin_digest,
    }


def _research_from_owner(record: OwnerStateRecord) -> ResearchRecord:
    payload = record.payload
    return ResearchRecord(
        research_id=_required_text(payload.get("research_id"), field="research_id"),
        created_at=_required_text(payload.get("created_at"), field="created_at"),
        updated_at=_required_text(payload.get("created_at"), field="created_at"),
        status=ResearchStatus.DRAFT,
        set_id=_required_text(payload.get("set_id"), field="set_id"),
        set_version=_required_text(payload.get("set_version"), field="set_version"),
        rules_version_id=_required_text(payload.get("rules_version_id"), field="rules_version_id"),
        rules_display_version=_required_text(payload.get("rules_display_version"), field="rules_display_version"),
        selected_backtest_run_id=None,
        selected_demo_run_id=None,
        decision=ResearchDecision.NONE,
        decision_at=None,
        archived_at=None,
        made_active_at=None,
        promoted_set_id=None,
        promoted_set_version=None,
        promoted_rules_version_id=None,
        previous_active_set_id=None,
        previous_active_set_version=None,
        previous_rules_version_id=None,
        promotion_result_metadata={},
        created_source=_required_text(payload.get("created_source"), field="created_source"),
        schema_version=_required_text(payload.get("schema_version"), field="schema_version"),
        pin_payload=dict(payload.get("pin_payload") or {}),
        pin_digest=_required_text(payload.get("pin_digest"), field="pin_digest"),
    )


def _trigger_set_payload(trigger_set: TriggerSetVersion) -> dict[str, Any]:
    return {
        "schema": TRIGGER_SET_STATE_TYPE,
        "set_id": trigger_set.set_id,
        "version": trigger_set.version,
        "purpose": trigger_set.purpose,
        "symbol": trigger_set.symbol,
        "timeframe": trigger_set.timeframe,
        "rule_versions": tuple({"rule_id": rule_id, "version": version} for rule_id, version in trigger_set.rule_versions),
        "strategy_version": trigger_set.strategy_version,
        "risk_profile_version": trigger_set.risk_profile_version,
        "config_snapshot": dict(trigger_set.config_snapshot),
        "created_at": trigger_set.created_at,
        "provenance": trigger_set.provenance,
    }


def _trigger_set_from_owner(record: OwnerStateRecord) -> TriggerSetVersion:
    payload = record.payload
    return TriggerSetVersion(
        set_id=_required_text(payload.get("set_id"), field="set_id"),
        version=_required_text(payload.get("version"), field="version"),
        purpose=_required_text(payload.get("purpose"), field="purpose"),
        status=TriggerSetStatus.TESTING,
        symbol=_required_text(payload.get("symbol"), field="symbol"),
        timeframe=_required_text(payload.get("timeframe"), field="timeframe"),
        rule_versions=tuple(
            (
                _required_text(item.get("rule_id"), field="rule_id"),
                _required_text(item.get("version"), field="rule_version"),
            )
            for item in (payload.get("rule_versions") or ())
        ),
        strategy_version=_required_text(payload.get("strategy_version"), field="strategy_version"),
        risk_profile_version=_required_text(payload.get("risk_profile_version"), field="risk_profile_version"),
        config_snapshot=dict(payload.get("config_snapshot") or {}),
        created_at=_required_text(payload.get("created_at"), field="created_at"),
        provenance=_required_text(payload.get("provenance"), field="provenance"),
    )


def _rules_payload(rules: TradingRulesVersion) -> dict[str, Any]:
    return {
        "schema": TRADING_RULES_STATE_TYPE,
        "rules_version_id": rules.rules_version_id,
        "version": rules.version,
        "created_at": rules.created_at,
        "created_from_version_id": rules.created_from_version_id,
        "created_source": rules.created_source,
        "change_summary": rules.change_summary,
        "config_hash": rules.config_hash,
        "schema_version": rules.schema_version,
        "draft": draft_to_json(rules.draft),
    }


def _rules_from_owner(record: OwnerStateRecord) -> TradingRulesVersion:
    payload = record.payload
    return TradingRulesVersion(
        rules_version_id=_required_text(payload.get("rules_version_id"), field="rules_version_id"),
        version=_required_text(payload.get("version"), field="version"),
        created_at=_required_text(payload.get("created_at"), field="created_at"),
        created_from_version_id=_optional_text(payload.get("created_from_version_id"), field="created_from_version_id"),
        created_source=_required_text(payload.get("created_source"), field="created_source"),
        change_summary=_required_text(payload.get("change_summary"), field="change_summary"),
        config_hash=_required_text(payload.get("config_hash"), field="config_hash"),
        schema_version=_required_text(payload.get("schema_version"), field="schema_version"),
        draft=draft_from_json(_required_text(payload.get("draft"), field="draft", max_len=20000)),
        is_current=False,
    )


def _trigger_set_key(set_id: str, version: str) -> str:
    return f"{_required_text(set_id, field='set_id')}@{_required_text(version, field='set_version')}"


def _run_state_key(research_id: str, run_id: str) -> str:
    return f"{_checked(research_id, 'research_id')}:{_checked(run_id, 'run_id')}"


def _candidate_research_from_create_kwargs(**kwargs: Any) -> ResearchRecord:
    set_id = _checked(str(kwargs["set_id"]), "set_id")
    set_version = _checked(str(kwargs["set_version"]), "set_version")
    rules_version_id = _checked(str(kwargs["rules_version_id"]), "rules_version_id")
    created_at = str(kwargs.get("created_at") or _now())
    clean_source = _clean_text(str(kwargs.get("created_source") or "service"), "created_source", 80)
    clean_display_version = _clean_text(str(kwargs.get("rules_display_version") or rules_version_id), "rules_display_version", 40)
    pins = kwargs.get("pin_payload") or default_store_research_pin_payload(
        set_id=set_id,
        set_version=set_version,
        rules_version_id=rules_version_id,
        rules_display_version=clean_display_version,
        created_source=clean_source,
        schema_version=RESEARCH_SCHEMA_VERSION,
    )
    _pin_json, pin_digest = _pin_json_and_digest(pins)
    return ResearchRecord(
        research_id=_research_id(set_id, set_version, rules_version_id, pin_digest),
        created_at=created_at,
        updated_at=created_at,
        status=ResearchStatus.DRAFT,
        set_id=set_id,
        set_version=set_version,
        rules_version_id=rules_version_id,
        rules_display_version=clean_display_version,
        selected_backtest_run_id=None,
        selected_demo_run_id=None,
        decision=ResearchDecision.NONE,
        decision_at=None,
        archived_at=None,
        made_active_at=None,
        promoted_set_id=None,
        promoted_set_version=None,
        promoted_rules_version_id=None,
        previous_active_set_id=None,
        previous_active_set_version=None,
        previous_rules_version_id=None,
        promotion_result_metadata={},
        created_source=clean_source,
        schema_version=RESEARCH_SCHEMA_VERSION,
        pin_payload=dict(pins),
        pin_digest=pin_digest,
    )


def _mutable_payload(record: ResearchRecord) -> dict[str, Any]:
    return {
        "schema": RESEARCH_MUTABLE_STATE_TYPE,
        "research_id": record.research_id,
        "updated_at": record.updated_at,
        "status": record.status.value,
        "selected_backtest_run_id": record.selected_backtest_run_id,
        "selected_demo_run_id": record.selected_demo_run_id,
        "decision": record.decision.value,
        "decision_at": record.decision_at,
        "archived_at": record.archived_at,
        "made_active_at": record.made_active_at,
        "promoted_set_id": record.promoted_set_id,
        "promoted_set_version": record.promoted_set_version,
        "promoted_rules_version_id": record.promoted_rules_version_id,
        "previous_active_set_id": record.previous_active_set_id,
        "previous_active_set_version": record.previous_active_set_version,
        "previous_rules_version_id": record.previous_rules_version_id,
        "promotion_result_metadata": dict(record.promotion_result_metadata),
    }


def _mutable_change_payload(changes: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in changes.items():
        if isinstance(value, (ResearchStatus, ResearchDecision)):
            clean[key] = value.value
        else:
            clean[key] = value
    return clean


def _apply_mutable_state(record: ResearchRecord, payload: dict[str, Any]) -> ResearchRecord:
    return replace(
        record,
        updated_at=str(payload.get("updated_at") or record.updated_at),
        status=ResearchStatus(str(payload.get("status") or record.status.value)),
        selected_backtest_run_id=_optional_text(payload.get("selected_backtest_run_id"), field="selected_backtest_run_id"),
        selected_demo_run_id=_optional_text(payload.get("selected_demo_run_id"), field="selected_demo_run_id"),
        decision=ResearchDecision(str(payload.get("decision") or record.decision.value)),
        decision_at=_optional_text(payload.get("decision_at"), field="decision_at"),
        archived_at=_optional_text(payload.get("archived_at"), field="archived_at"),
        made_active_at=_optional_text(payload.get("made_active_at"), field="made_active_at"),
        promoted_set_id=_optional_text(payload.get("promoted_set_id"), field="promoted_set_id"),
        promoted_set_version=_optional_text(payload.get("promoted_set_version"), field="promoted_set_version"),
        promoted_rules_version_id=_optional_text(payload.get("promoted_rules_version_id"), field="promoted_rules_version_id"),
        previous_active_set_id=_optional_text(payload.get("previous_active_set_id"), field="previous_active_set_id"),
        previous_active_set_version=_optional_text(payload.get("previous_active_set_version"), field="previous_active_set_version"),
        previous_rules_version_id=_optional_text(payload.get("previous_rules_version_id"), field="previous_rules_version_id"),
        promotion_result_metadata=dict(payload.get("promotion_result_metadata") or {}),
    )


def _backtest_payload(record: ResearchBacktestRunRecord) -> dict[str, Any]:
    return {
        "schema": RESEARCH_BACKTEST_RUN_STATE_TYPE,
        "research_id": record.research_id,
        "run_id": record.run_id,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "status": record.status.value,
        "period_start": record.period_start,
        "period_end": record.period_end,
        "timeframe": record.timeframe,
        "engine_run_id": record.engine_run_id,
        "selected_for_use": bool(record.selected_for_use),
        "metrics": _jsonable(record.metrics),
        "unavailable_reason": record.unavailable_reason,
        "pin_payload": dict(record.pin_payload),
        "pin_digest": record.pin_digest,
    }


def _backtest_from_owner(record: OwnerStateRecord) -> ResearchBacktestRunRecord:
    payload = record.payload
    return ResearchBacktestRunRecord(
        research_id=_required_text(payload.get("research_id"), field="research_id"),
        run_id=_required_text(payload.get("run_id"), field="run_id"),
        created_at=_required_text(payload.get("created_at"), field="created_at"),
        updated_at=_required_text(payload.get("updated_at"), field="updated_at"),
        status=ResearchBacktestStatus(str(payload.get("status"))),
        period_start=_required_text(payload.get("period_start"), field="period_start"),
        period_end=_required_text(payload.get("period_end"), field="period_end"),
        timeframe=_required_text(payload.get("timeframe"), field="timeframe"),
        engine_run_id=_optional_text(payload.get("engine_run_id"), field="engine_run_id"),
        selected_for_use=bool(payload.get("selected_for_use")),
        metrics=dict(payload.get("metrics") or {}),
        unavailable_reason=_optional_text(payload.get("unavailable_reason"), field="unavailable_reason"),
        pin_payload=dict(payload.get("pin_payload") or {}),
        pin_digest=_required_text(payload.get("pin_digest"), field="pin_digest"),
    )


def _demo_payload(record: ResearchDemoRunRecord) -> dict[str, Any]:
    return {
        "schema": RESEARCH_DEMO_RUN_STATE_TYPE,
        "research_id": record.research_id,
        "run_id": record.run_id,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "status": record.status.value,
        "started_at": record.started_at,
        "stopped_at": record.stopped_at,
        "execution_scope_id": record.execution_scope_id,
        "account_scope": record.account_scope,
        "selected_for_use": bool(record.selected_for_use),
        "metrics": _jsonable(record.metrics),
        "blocked_reason": record.blocked_reason,
        "pin_payload": dict(record.pin_payload),
        "pin_digest": record.pin_digest,
    }


def _demo_from_owner(record: OwnerStateRecord) -> ResearchDemoRunRecord:
    payload = record.payload
    return ResearchDemoRunRecord(
        research_id=_required_text(payload.get("research_id"), field="research_id"),
        run_id=_required_text(payload.get("run_id"), field="run_id"),
        created_at=_required_text(payload.get("created_at"), field="created_at"),
        updated_at=_required_text(payload.get("updated_at"), field="updated_at"),
        status=ResearchDemoStatus(str(payload.get("status"))),
        started_at=_optional_text(payload.get("started_at"), field="started_at"),
        stopped_at=_optional_text(payload.get("stopped_at"), field="stopped_at"),
        execution_scope_id=_optional_text(payload.get("execution_scope_id"), field="execution_scope_id"),
        account_scope=_optional_text(payload.get("account_scope"), field="account_scope"),
        selected_for_use=bool(payload.get("selected_for_use")),
        metrics=dict(payload.get("metrics") or {}),
        blocked_reason=_optional_text(payload.get("blocked_reason"), field="blocked_reason"),
        pin_payload=dict(payload.get("pin_payload") or {}),
        pin_digest=_required_text(payload.get("pin_digest"), field="pin_digest"),
    )


def _demo_from_execution_owner(record: OwnerStateRecord) -> ResearchDemoRunRecord:
    payload = record.payload
    status = _demo_status_from_execution_status(str(payload.get("status") or "PENDING"))
    created_at = _required_text(payload.get("requested_at"), field="requested_at")
    completed_at = _optional_text(payload.get("completed_at"), field="completed_at")
    error = _optional_text(payload.get("error"), field="error")
    result = payload.get("result")
    metrics = dict(result) if isinstance(result, dict) else {}
    progress = payload.get("progress")
    if isinstance(progress, dict) and "progress_days" in progress and "progress_days" not in metrics:
        metrics = {**metrics, "progress_days": progress.get("progress_days")}
    return ResearchDemoRunRecord(
        research_id=_required_text(payload.get("research_id"), field="research_id"),
        run_id=_required_text(payload.get("demo_run_id"), field="demo_run_id"),
        created_at=created_at,
        updated_at=completed_at or _optional_text(payload.get("started_at"), field="started_at") or created_at,
        status=status,
        started_at=_optional_text(payload.get("started_at"), field="started_at"),
        stopped_at=completed_at,
        execution_scope_id=f"research:{_required_text(payload.get('research_id'), field='research_id')}",
        account_scope=f"research:{_required_text(payload.get('research_id'), field='research_id')}",
        selected_for_use=False,
        metrics=metrics,
        blocked_reason=error if status in {ResearchDemoStatus.BLOCKED, ResearchDemoStatus.FAILED} else None,
        pin_payload=dict(payload.get("pin_payload") or {}),
        pin_digest=_required_text(payload.get("pin_digest"), field="pin_digest"),
    )


def _merge_demo_execution_projection(existing: ResearchDemoRunRecord, execution: ResearchDemoRunRecord) -> ResearchDemoRunRecord:
    return replace(
        existing,
        updated_at=execution.updated_at,
        status=execution.status,
        started_at=execution.started_at,
        stopped_at=execution.stopped_at,
        execution_scope_id=execution.execution_scope_id or existing.execution_scope_id,
        account_scope=execution.account_scope or existing.account_scope,
        metrics=execution.metrics,
        blocked_reason=execution.blocked_reason,
    )


def _demo_status_from_execution_status(status: str) -> ResearchDemoStatus:
    normalized = status.upper()
    if normalized == "PENDING":
        return ResearchDemoStatus.PENDING
    if normalized == "COMPLETED":
        return ResearchDemoStatus.STOPPED
    if normalized == "FAILED":
        return ResearchDemoStatus.FAILED
    if normalized == "BLOCKED":
        return ResearchDemoStatus.BLOCKED
    return ResearchDemoStatus.RUNNING


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if value.__class__.__name__ == "Decimal":
        return str(value)
    return value


def _required_text(value: object, *, field: str, max_len: int = 240) -> str:
    raw = str(value or "").strip()
    if not raw or "\x00" in raw or len(raw) > max_len:
        raise ResearchConfigurationRegistryError(f"{field} must be a non-empty stable string")
    return raw


def _optional_text(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field=field)
