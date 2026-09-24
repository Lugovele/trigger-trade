from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from triggertrade.persistence.durable_messages import DurableMessageStore
from triggertrade.persistence.postgres import (
    OwnerStateConflict,
    OwnerStateRecord,
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.canonical_json import canonical_json_digest
from triggertrade.persistence.postgres_research_registry import PostgresResearchConfigurationRegistry
from triggertrade.persistence.research_store import ResearchDecision, ResearchRecord, ResearchStatus
from triggertrade.rules import CoinRule, DirectionMode, TakeProfitMode, TradingRulesVersion, TradingRulesVersionDraft
from triggertrade.services.research import ResearchDemoIsolation
from triggertrade.services.research_demo_execution import (
    RESEARCH_DEMO_CONSUMER,
    RESEARCH_DEMO_MESSAGE_TYPE,
    RESEARCH_DEMO_MESSAGE_VERSION,
    RESEARCH_DEMO_PRODUCER,
    PostgresResearchDemoExecutionHandoff,
    ResearchDemoExecutionDispatcher,
    ResearchDemoExecutionRecord,
    ResearchDemoExecutionStore,
)
from triggertrade.trigger_sets import TriggerSetStatus, TriggerSetVersion


def test_research_demo_dispatch_fails_closed_without_canonical_executor():
    record = _demo_record()
    store = _FakeResearchDemoStore(record)

    with pytest.raises(PostgresPersistenceError, match="research_demo_canonical_executor_unavailable"):
        ResearchDemoExecutionDispatcher(store=store, executor=None).dispatch(record.demo_run_id)

    assert store.transitions == []


def test_research_demo_dispatch_marks_running_and_replays_terminal_result_once():
    record = _demo_record()
    store = _FakeResearchDemoStore(record)
    executor = _FakeResearchDemoExecutor()

    detail = ResearchDemoExecutionDispatcher(store=store, executor=executor).dispatch(record.demo_run_id)

    assert detail == f"research_demo_running:{record.demo_run_id}"
    assert store.transitions == ["RUNNING"]
    assert executor.calls == [record.demo_run_id]

    store.record = _copy_record(store.record, status="COMPLETED")
    replay = ResearchDemoExecutionDispatcher(store=store, executor=executor).dispatch(record.demo_run_id)

    assert replay == "research_demo_replay:COMPLETED"
    assert executor.calls == [record.demo_run_id]


def test_research_config_registry_round_trips_exact_versions_without_sqlite(monkeypatch):
    stored: dict[tuple[str, str, str], OwnerStateRecord] = {}

    class FakeOwnerStateStore:
        def __init__(self, connection) -> None:
            self._connection = connection

        def put_if_absent(self, *, owner, state_type, state_id, payload):
            digest = canonical_json_digest(payload)
            key = (owner, state_type, state_id)
            existing = stored.get(key)
            if existing is not None:
                if existing.payload_digest != digest:
                    raise OwnerStateConflict("owner state identity already exists with different canonical content")
                return existing, False
            record = OwnerStateRecord(owner, state_type, state_id, 1, dict(payload), digest)
            stored[key] = record
            return record, True

        def get(self, *, owner, state_type, state_id):
            return stored.get((owner, state_type, state_id))

    monkeypatch.setattr("triggertrade.persistence.postgres_research_registry.OwnerStateStore", FakeOwnerStateStore)
    registry = PostgresResearchConfigurationRegistry(connection=object())
    research = _research_record()
    trigger_set = _trigger_set()
    rules = _rules_version()

    registry.put_configuration(research=research, trigger_set=trigger_set, rules=rules)
    registry.put_configuration(research=research, trigger_set=trigger_set, rules=rules)
    config = registry.get_research_demo_configuration(
        research_id=research.research_id,
        set_id=research.set_id,
        set_version=research.set_version,
        rules_version_id=rules.rules_version_id,
    )

    assert config.research == _immutable_research_view(research)
    assert config.trigger_set == trigger_set
    assert config.rules == _copy_rules_current_flag(rules, is_current=False)
    mutable_research = ResearchRecord(
        **{
            **research.__dict__,
            "updated_at": "2026-09-24T01:00:00Z",
            "status": ResearchStatus.DEMO_RUNNING,
            "selected_backtest_run_id": "rbt-unit",
            "selected_demo_run_id": "rdm-unit",
            "decision": ResearchDecision.PROMOTION_REQUESTED,
            "decision_at": "2026-09-24T01:00:00Z",
            "promotion_result_metadata": {"operator": "unit"},
        }
    )
    registry.put_research(mutable_research)
    assert registry.get_research(research.research_id) == _immutable_research_view(research)
    with pytest.raises(OwnerStateConflict):
        registry.put_research(
            ResearchRecord(
                **{
                    **research.__dict__,
                    "created_source": "changed-without-new-research-id",
                }
            )
        )


def test_research_demo_postgres_handoff_persists_state_outbox_and_idempotency():
    psycopg = pytest.importorskip("psycopg")
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        handoff = PostgresResearchDemoExecutionHandoff(factory=factory)
        research = _research_record()
        trigger_set = _trigger_set()
        rules = _rules_version()
        isolation = _isolation()
        pin_payload = {"pin": "research-demo", "research_id": research.research_id}

        first = handoff.start_research_demo(
            research=research,
            trigger_set=trigger_set,
            rules=rules,
            isolation=isolation,
            started_at="2026-09-24T00:00:00+00:00",
            pin_payload=pin_payload,
            demo_run_id="rdm-unit-1",
        )
        second = handoff.start_research_demo(
            research=research,
            trigger_set=trigger_set,
            rules=rules,
            isolation=isolation,
            started_at="2026-09-24T00:00:00+00:00",
            pin_payload=pin_payload,
            demo_run_id="rdm-unit-1",
        )

        assert first == second
        assert first.execution_owner == "trading-worker"
        assert first.durable is True

        with PostgresUnitOfWork(factory) as uow:
            state = ResearchDemoExecutionStore(uow.connection).get("rdm-unit-1")
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id=first.handoff_id)
            config = PostgresResearchConfigurationRegistry(uow.connection).get_research_demo_configuration(
                research_id=research.research_id,
                set_id=research.set_id,
                set_version=research.set_version,
                rules_version_id=rules.rules_version_id,
            )

        assert state is not None
        assert state.status == "PENDING"
        assert state.set_id == "triggertrade-futures-core"
        assert state.set_version == "v1"
        assert state.rules_version_id == "rules-v1"
        assert outbox is not None
        assert outbox.producer == RESEARCH_DEMO_PRODUCER
        assert outbox.consumer == RESEARCH_DEMO_CONSUMER
        assert outbox.message_type == RESEARCH_DEMO_MESSAGE_TYPE
        assert outbox.message_version == RESEARCH_DEMO_MESSAGE_VERSION
        assert outbox.dedupe_key == "RESEARCH_DEMO_START:rdm-unit-1"
        assert config.research == _immutable_research_view(research)
        assert config.trigger_set == trigger_set
        assert config.rules == _copy_rules_current_flag(rules, is_current=False)
    finally:
        with psycopg.connect(settings.dsn, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_research_config_registry_rejects_immutable_conflicts():
    psycopg = pytest.importorskip("psycopg")
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        research = _research_record()
        trigger_set = _trigger_set()
        rules = _rules_version()
        with PostgresUnitOfWork(factory) as uow:
            registry = PostgresResearchConfigurationRegistry(uow.connection)
            registry.put_configuration(research=research, trigger_set=trigger_set, rules=rules)
            registry.put_configuration(research=research, trigger_set=trigger_set, rules=rules)
            changed_set = TriggerSetVersion(
                **{**trigger_set.__dict__, "purpose": "changed without version bump"}
            )
            with pytest.raises(OwnerStateConflict):
                registry.put_trigger_set_version(changed_set)
            changed_rules = TradingRulesVersion(
                **{**rules.__dict__, "change_summary": "changed without rules version bump"}
            )
            with pytest.raises(OwnerStateConflict):
                registry.put_trading_rules_version(changed_rules)
            with pytest.raises(PostgresPersistenceError, match="exact Research Demo configuration missing"):
                registry.get_research_demo_configuration(
                    research_id=research.research_id,
                    set_id=research.set_id,
                    set_version=research.set_version,
                    rules_version_id="missing-rules",
                )
    finally:
        with psycopg.connect(settings.dsn, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


class _FakeResearchDemoStore:
    def __init__(self, record: ResearchDemoExecutionRecord) -> None:
        self.record = record
        self.transitions: list[str] = []

    def get(self, demo_run_id: str):
        assert demo_run_id == self.record.demo_run_id
        return self.record

    def mark_running(self, demo_run_id: str, *, progress=None):
        self.transitions.append("RUNNING")
        self.record = _copy_record(self.record, status="RUNNING", started_at="2026-09-24T00:00:01Z")
        return self.record

    def mark_completed(self, demo_run_id: str, *, result):
        self.transitions.append("COMPLETED")
        self.record = _copy_record(self.record, status="COMPLETED", result=result)
        return self.record


class _FakeResearchDemoExecutor:
    canonical_research_demo_executor = True

    def __init__(self) -> None:
        self.calls: list[str] = []

    def start_research_demo(self, record):
        self.calls.append(record.demo_run_id)
        return {"terminal": False, "source": "canonical_test_executor"}


def _demo_record() -> ResearchDemoExecutionRecord:
    return ResearchDemoExecutionRecord(
        demo_run_id="rdm-unit-1",
        research_id="res-unit-1",
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id="rules-v1",
        rules_display_version="v1",
        requested_at="2026-09-24T00:00:00Z",
        started_at=None,
        completed_at=None,
        execution_owner="trading-worker",
        handoff_message_id="research-demo-start-unit-1",
        status="PENDING",
        progress={},
        result=None,
        error=None,
        pin_payload={"pin": "research-demo"},
        pin_digest="pin-digest",
        revision=1,
    )


def _copy_record(record: ResearchDemoExecutionRecord, **changes) -> ResearchDemoExecutionRecord:
    values = dict(record.__dict__)
    values.update(changes)
    values["revision"] = record.revision + 1
    return ResearchDemoExecutionRecord(**values)


def _research_record() -> ResearchRecord:
    return ResearchRecord(
        research_id="res-unit-1",
        created_at="2026-09-24T00:00:00Z",
        updated_at="2026-09-24T00:00:00Z",
        status=ResearchStatus.DRAFT,
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id="rules-v1",
        rules_display_version="v1",
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
        created_source="unit",
        schema_version="research-v1",
        pin_payload={"pin": "research"},
        pin_digest="research-pin-digest",
    )


def _immutable_research_view(research: ResearchRecord) -> ResearchRecord:
    return ResearchRecord(
        **{
            **research.__dict__,
            "updated_at": research.created_at,
            "status": ResearchStatus.DRAFT,
            "selected_backtest_run_id": None,
            "selected_demo_run_id": None,
            "decision": ResearchDecision.NONE,
            "decision_at": None,
            "archived_at": None,
            "made_active_at": None,
            "promoted_set_id": None,
            "promoted_set_version": None,
            "promoted_rules_version_id": None,
            "previous_active_set_id": None,
            "previous_active_set_version": None,
            "previous_rules_version_id": None,
            "promotion_result_metadata": {},
        }
    )


def _trigger_set() -> TriggerSetVersion:
    return TriggerSetVersion(
        set_id="triggertrade-futures-core",
        version="v1",
        purpose="Unit Research Demo set",
        status=TriggerSetStatus.TESTING,
        symbol="BTCUSDT",
        timeframe="1m",
        rule_versions=(("TRG-001", "0.2.0"), ("STR-FUT-001", "0.1.0")),
        strategy_version="STR-FUT-001@0.1.0",
        risk_profile_version="RSK-FUTURES-001@0.1.0",
        config_snapshot={"market": "linear", "execution": "bybit_demo_futures"},
        created_at="2026-09-24T00:00:00Z",
        provenance="unit",
    )


def _rules_version() -> TradingRulesVersion:
    return TradingRulesVersion(
        rules_version_id="rules-v1",
        version="v1",
        created_at="2026-09-24T00:00:00Z",
        created_from_version_id=None,
        created_source="unit",
        change_summary="unit",
        config_hash="hash",
        schema_version="trading-rules-v1",
        draft=TradingRulesVersionDraft(
            position_size_pct=Decimal("0.01"),
            take_profit_mode=TakeProfitMode.FIXED,
            fixed_take_profit_pct=Decimal("0.02"),
            minimum_take_profit_pct=None,
            stop_loss_pct=Decimal("0.01"),
            minimum_risk_reward=Decimal("1.5"),
            minimum_net_edge_enabled=False,
            minimum_net_edge_pct=None,
            leverage=Decimal("2"),
            max_capital_in_positions_pct=Decimal("0.2"),
            max_open_positions_enabled=True,
            max_open_positions=1,
            max_positions_per_coin_enabled=True,
            max_positions_per_coin=1,
            direction_mode=DirectionMode.LONG_SHORT,
            daily_loss_limit_enabled=False,
            daily_loss_limit_pct=None,
            maker_fee_rate=Decimal("0.0002"),
            taker_fee_rate=Decimal("0.0006"),
            spread_cost=Decimal("0"),
            slippage_cost=Decimal("0"),
            funding_cost=Decimal("0"),
            coins=(CoinRule("BTCUSDT", True),),
        ),
    )


def _copy_rules_current_flag(rules: TradingRulesVersion, *, is_current: bool) -> TradingRulesVersion:
    values = dict(rules.__dict__)
    values["is_current"] = is_current
    draft_values = dict(rules.draft.__dict__)
    draft_values["metadata"] = draft_values["metadata"] or {}
    values["draft"] = TradingRulesVersionDraft(**draft_values)
    return TradingRulesVersion(**values)


def _isolation() -> ResearchDemoIsolation:
    return ResearchDemoIsolation(
        available=True,
        reason="isolated_unit_scope",
        execution_scope_id="research-demo-unit",
        account_scope="research-demo-account",
        adapter_scope_id="research-demo-adapter",
        state_scope_id="research-demo-state",
    )


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_research_demo_{uuid.uuid4().hex[:16]}")
