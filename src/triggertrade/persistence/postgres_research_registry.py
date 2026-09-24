"""PostgreSQL-backed immutable Research configuration registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from triggertrade.persistence.postgres import (
    OwnerStateRecord,
    OwnerStateStore,
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresUnitOfWork,
)
from triggertrade.persistence.research_store import ResearchDecision, ResearchRecord, ResearchStatus
from triggertrade.rules import TradingRulesVersion
from triggertrade.rules.trading import draft_from_json, draft_to_json
from triggertrade.trigger_sets import TriggerSetStatus, TriggerSetVersion


RESEARCH_CONFIG_OWNER = "ResearchConfigurationRegistry"
RESEARCH_STATE_TYPE = "RESEARCH_DEFINITION"
TRIGGER_SET_STATE_TYPE = "TRIGGER_SET_VERSION"
TRADING_RULES_STATE_TYPE = "TRADING_RULES_VERSION"


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


class PostgresResearchConfigurationRegistryClient:
    """Unit-of-work wrapper for production write/read boundaries."""

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


def _required_text(value: object, *, field: str, max_len: int = 240) -> str:
    raw = str(value or "").strip()
    if not raw or "\x00" in raw or len(raw) > max_len:
        raise ResearchConfigurationRegistryError(f"{field} must be a non-empty stable string")
    return raw


def _optional_text(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field=field)
