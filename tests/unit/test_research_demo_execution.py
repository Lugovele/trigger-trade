from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

import triggertrade.services.research_demo_execution as research_demo_execution
from triggertrade.accounting import EquitySnapshot
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
from triggertrade.persistence.postgres_research_registry import (
    PostgresResearchConfigurationRegistry,
    _demo_from_execution_owner,
    _merge_demo_execution_projection,
)
from triggertrade.persistence.research_store import ResearchDecision, ResearchDemoRunRecord, ResearchDemoStatus, ResearchRecord, ResearchStatus
from triggertrade.config import ConfigError, ExecutionVenue, load_config
from triggertrade.rules import CoinRule, DirectionMode, TakeProfitMode, TradingRulesVersion, TradingRulesVersionDraft
from triggertrade.services.research import ResearchDemoIsolation
from triggertrade.services.research_demo_execution import (
    CanonicalResearchDemoExecutionExecutor,
    CanonicalResearchDemoTradingCycleProvider,
    RESEARCH_DEMO_CONSUMER,
    RESEARCH_DEMO_MESSAGE_TYPE,
    RESEARCH_DEMO_MESSAGE_VERSION,
    RESEARCH_DEMO_PRODUCER,
    PostgresResearchDemoExecutionHandoff,
    ResearchDemoExecutionDispatcher,
    ResearchDemoExecutionRecord,
    ResearchDemoExecutionStore,
    _ResearchDemoAccountingStore,
    _PostgresResearchDemoDailyLossStore,
    _PostgresResearchDemoMessageStore,
)
from triggertrade.services.futures_runtime import FuturesDualLaneResult
from triggertrade.services.runtime import RuntimeCycleResult
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
    assert store.rechecks == [record.demo_run_id]
    assert executor.calls == [record.demo_run_id]

    store.record = _copy_record(store.record, status="COMPLETED")
    replay = ResearchDemoExecutionDispatcher(store=store, executor=executor).dispatch(record.demo_run_id)

    assert replay == "research_demo_replay:COMPLETED"
    assert executor.calls == [record.demo_run_id]


def test_demo_projection_same_run_pending_execution_overrides_stale_running_store():
    stale = _demo_run_projection(status=ResearchDemoStatus.RUNNING, started_at="2026-09-24T00:00:00Z")
    execution = _demo_from_execution_owner(_execution_owner_record(status="PENDING", started_at=None))

    projected = _merge_demo_execution_projection(stale, execution)

    assert projected.status is ResearchDemoStatus.PENDING
    assert projected.started_at is None
    assert projected.metrics == {}
    assert projected.blocked_reason is None


def test_demo_projection_same_run_running_uses_factual_worker_started_at():
    stale = _demo_run_projection(status=ResearchDemoStatus.RUNNING, started_at="2026-09-24T00:00:00Z")
    execution = _demo_from_execution_owner(_execution_owner_record(status="RUNNING", started_at="2026-09-24T00:01:00Z"))

    projected = _merge_demo_execution_projection(stale, execution)

    assert projected.status is ResearchDemoStatus.RUNNING
    assert projected.started_at == "2026-09-24T00:01:00Z"


@pytest.mark.parametrize("status,expected", [("FAILED", ResearchDemoStatus.FAILED), ("BLOCKED", ResearchDemoStatus.BLOCKED)])
def test_demo_projection_same_run_failed_or_blocked_uses_execution_error(status, expected):
    stale = _demo_run_projection(status=ResearchDemoStatus.RUNNING, started_at="2026-09-24T00:00:00Z")
    execution = _demo_from_execution_owner(
        _execution_owner_record(
            status=status,
            started_at="2026-09-24T00:01:00Z",
            completed_at="2026-09-24T00:02:00Z",
            error="research_demo_canonical_execution_cycle_unavailable:canonical_lifecycle_invoked",
        )
    )

    projected = _merge_demo_execution_projection(stale, execution)

    assert projected.status is expected
    assert projected.stopped_at == "2026-09-24T00:02:00Z"
    assert projected.blocked_reason == "research_demo_canonical_execution_cycle_unavailable:canonical_lifecycle_invoked"


def test_demo_projection_same_run_completed_exposes_execution_result_metrics():
    stale = _demo_run_projection(status=ResearchDemoStatus.RUNNING, metrics={"old": "stale"})
    execution = _demo_from_execution_owner(
        _execution_owner_record(
            status="COMPLETED",
            started_at="2026-09-24T00:01:00Z",
            completed_at="2026-09-24T00:02:00Z",
            result={"result": {"source": "canonical_futures_accounting", "trades": 2, "net_pnl": "3"}},
        )
    )

    projected = _merge_demo_execution_projection(stale, execution)

    assert projected.status is ResearchDemoStatus.STOPPED
    assert projected.stopped_at == "2026-09-24T00:02:00Z"
    assert projected.metrics["result"]["trades"] == 2
    assert projected.metrics["result"]["source"] == "canonical_futures_accounting"


def test_demo_projection_execution_only_run_is_recovered():
    recovered = _demo_from_execution_owner(_execution_owner_record(status="RUNNING", started_at="2026-09-24T00:01:00Z"))

    assert recovered.run_id == "rdm-unit-1"
    assert recovered.status is ResearchDemoStatus.RUNNING
    assert recovered.started_at == "2026-09-24T00:01:00Z"


def test_demo_projection_research_run_store_only_legacy_run_is_unchanged():
    legacy = _demo_run_projection(
        status=ResearchDemoStatus.RUNNING,
        started_at="2026-09-24T00:00:00Z",
        metrics={"legacy": True},
    )

    assert legacy.status is ResearchDemoStatus.RUNNING
    assert legacy.started_at == "2026-09-24T00:00:00Z"
    assert legacy.metrics == {"legacy": True}


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
        assert state.progress["duration_seconds"] == 7 * 24 * 60 * 60
        assert state.progress["duration_elapsed"] is False
        assert state.progress["factual_progress_source"] == "canonical_research_demo_owner_state"
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


def test_canonical_research_demo_executor_reconstructs_config_and_projects_running_progress(monkeypatch):
    executor = _executor(monkeypatch, now="2026-09-25T00:00:00+00:00")
    record = _copy_record(_demo_record(), started_at="2026-09-24T00:00:00Z", requested_at="2026-09-24T00:00:00Z")

    result = executor.start_research_demo(record)

    assert result["terminal"] is False
    assert result["execution_owner"] == "trading-worker"
    assert result["configuration"] == {
        "research_id": record.research_id,
        "set_id": record.set_id,
        "set_version": record.set_version,
        "rules_version_id": record.rules_version_id,
    }
    assert result["progress"]["duration_days"] == 7
    assert result["progress"]["duration_elapsed"] is False


def test_canonical_research_demo_executor_progress_uses_processed_candle_time(monkeypatch):
    executor = _executor(
        monkeypatch,
        now="2026-09-25T00:00:00+00:00",
        trading_cycle=_CycleWithRuntime("BTCUSDT:1m:2026-09-24T00:05:00Z"),
    )
    record = _copy_record(_demo_record(), started_at="2026-09-24T00:00:00Z", requested_at="2026-09-24T00:00:00Z")

    result = executor.start_research_demo(record)

    assert result["terminal"] is False
    assert result["progress"]["observed_at"] == "2026-09-24T00:05:00Z"
    assert result["progress"]["elapsed_seconds"] == 300
    assert result["progress"]["started_at"] == "2026-09-24T00:00:00Z"


def test_canonical_research_demo_dispatch_repeated_cycles_refresh_same_parent(monkeypatch):
    record = _copy_record(_demo_record(), started_at="2026-09-24T00:00:00Z", requested_at="2026-09-24T00:00:00Z")
    store = _FakeResearchDemoStore(record)
    first = _executor(
        monkeypatch,
        trading_cycle=_CycleWithRuntime("BTCUSDT:1m:2026-09-24T00:05:00Z"),
    )
    second = _executor(
        monkeypatch,
        trading_cycle=_CycleWithRuntime("BTCUSDT:1m:2026-09-24T00:10:00Z"),
    )

    first_detail = ResearchDemoExecutionDispatcher(store=store, executor=first).dispatch(record.demo_run_id)
    second_detail = ResearchDemoExecutionDispatcher(store=store, executor=second).dispatch(record.demo_run_id)

    assert first_detail == f"research_demo_running:{record.demo_run_id}"
    assert second_detail == f"research_demo_running:{record.demo_run_id}"
    assert store.record.demo_run_id == record.demo_run_id
    assert store.record.revision > record.revision
    assert store.record.progress["observed_at"] == "2026-09-24T00:10:00Z"
    assert store.record.progress["elapsed_seconds"] == 600
    assert store.record.started_at == "2026-09-24T00:00:00Z"
    assert store.rechecks == [record.demo_run_id, record.demo_run_id]


def test_canonical_research_demo_executor_no_signal_cycle_advances_progress(monkeypatch):
    executor = _executor(
        monkeypatch,
        trading_cycle=_CycleWithRuntime("BTCUSDT:1m:2026-09-24T00:07:00Z", signal_type="NO_SIGNAL", execution_status=None),
    )
    record = _copy_record(_demo_record(), started_at="2026-09-24T00:00:00Z", requested_at="2026-09-24T00:00:00Z")

    result = executor.start_research_demo(record)

    assert result["progress"]["observed_at"] == "2026-09-24T00:07:00Z"
    assert result["progress"]["elapsed_seconds"] == 420


def test_canonical_research_demo_executor_checkpoint_recovery_advances_progress(monkeypatch):
    executor = _executor(
        monkeypatch,
        trading_cycle=_CycleWithRuntime(
            "BTCUSDT:1m:2026-09-24T00:11:00Z",
            skipped_reason="checkpoint_recovery_processed",
        ),
    )
    record = _copy_record(_demo_record(), started_at="2026-09-24T00:00:00Z", requested_at="2026-09-24T00:00:00Z")

    result = executor.start_research_demo(record)

    assert result["progress"]["observed_at"] == "2026-09-24T00:11:00Z"
    assert result["progress"]["elapsed_seconds"] == 660
    assert result["progress"]["started_at"] == "2026-09-24T00:00:00Z"


def test_canonical_research_demo_executor_older_replay_preserves_newer_parent_progress(monkeypatch):
    executor = _executor(
        monkeypatch,
        trading_cycle=_CycleWithRuntime("BTCUSDT:1m:2026-09-24T00:05:00Z"),
    )
    record = _copy_record(
        _demo_record(),
        started_at="2026-09-24T00:00:00Z",
        requested_at="2026-09-24T00:00:00Z",
        progress={
            "observed_at": "2026-09-24T00:10:00Z",
            "elapsed_seconds": 600,
            "duration_seconds": 604800,
            "duration_elapsed": False,
            "factual_progress_source": "canonical_research_demo_owner_state",
        },
    )

    result = executor.start_research_demo(record)

    assert result["terminal"] is False
    assert result["progress"]["observed_at"] == "2026-09-24T00:10:00Z"
    assert result["progress"]["elapsed_seconds"] == 600
    assert result["progress"]["duration_elapsed"] is False


def test_canonical_research_demo_dispatch_same_candle_replay_is_semantically_idempotent(monkeypatch):
    record = _copy_record(_demo_record(), started_at="2026-09-24T00:00:00Z", requested_at="2026-09-24T00:00:00Z")
    store = _FakeResearchDemoStore(record)
    executor = _executor(
        monkeypatch,
        trading_cycle=_CycleWithRuntime("BTCUSDT:1m:2026-09-24T00:05:00Z"),
    )

    first = ResearchDemoExecutionDispatcher(store=store, executor=executor).dispatch(record.demo_run_id)
    progress_after_first = dict(store.record.progress)
    second = ResearchDemoExecutionDispatcher(store=store, executor=executor).dispatch(record.demo_run_id)

    assert first == f"research_demo_running:{record.demo_run_id}"
    assert second == f"research_demo_running:{record.demo_run_id}"
    assert store.record.demo_run_id == record.demo_run_id
    assert store.record.progress["observed_at"] == "2026-09-24T00:05:00Z"
    assert store.record.progress["elapsed_seconds"] == 300
    assert store.record.progress["duration_elapsed"] == progress_after_first["duration_elapsed"]
    assert store.record.progress["observed_at"] == progress_after_first["observed_at"]
    assert store.record.progress["elapsed_seconds"] == progress_after_first["elapsed_seconds"]


def test_canonical_research_demo_executor_no_factual_timestamp_does_not_use_wall_clock(monkeypatch):
    executor = _executor(
        monkeypatch,
        now="2026-10-02T00:00:01+00:00",
        trading_cycle=_CycleWithRuntime("unparseable-candle-id"),
        accounting=_FakeAccountingStore(({"trade_id": "must-not-complete"},)),
    )
    record = _copy_record(
        _demo_record(),
        started_at="2026-09-24T00:00:00Z",
        requested_at="2026-09-24T00:00:00Z",
        progress={
            "observed_at": "2026-09-24T00:05:00Z",
            "elapsed_seconds": 300,
            "duration_seconds": 604800,
            "duration_elapsed": False,
            "factual_progress_source": "canonical_research_demo_owner_state",
        },
    )

    result = executor.start_research_demo(record)

    assert result["terminal"] is False
    assert "progress" not in result
    assert "result" not in result


def test_canonical_research_demo_completion_requires_factual_progress_boundary(monkeypatch):
    record = _copy_record(
        _demo_record(),
        started_at="2026-09-24T00:00:00Z",
        requested_at="2026-09-24T00:00:00Z",
        progress={
            "observed_at": "2026-09-30T23:59:00Z",
            "elapsed_seconds": 604740,
            "duration_seconds": 604800,
            "duration_elapsed": False,
            "factual_progress_source": "canonical_research_demo_owner_state",
        },
    )
    no_timestamp = _executor(
        monkeypatch,
        now="2026-10-02T00:00:01+00:00",
        trading_cycle=_CycleWithRuntime("unparseable-candle-id"),
        accounting=_FakeAccountingStore(({"trade_id": "must-not-complete"},)),
    )
    factual_boundary = _executor(
        monkeypatch,
        now="2026-10-02T00:00:01+00:00",
        trading_cycle=_CycleWithRuntime("BTCUSDT:1m:2026-10-01T00:00:00Z"),
        accounting=_FakeAccountingStore(()),
    )

    before = no_timestamp.start_research_demo(record)
    after = factual_boundary.start_research_demo(record)

    assert before["terminal"] is False
    assert "progress" not in before
    assert after["terminal"] is True
    assert after["progress"]["observed_at"] == "2026-10-01T00:00:00Z"
    assert after["progress"]["elapsed_seconds"] == 604800
    assert after["progress"]["duration_elapsed"] is True
    assert after["result"]["source"] == "canonical_futures_accounting"


def test_canonical_research_demo_executor_checkpoint_recovery_older_does_not_regress(monkeypatch):
    executor = _executor(
        monkeypatch,
        trading_cycle=_CycleWithRuntime(
            "BTCUSDT:1m:2026-09-24T00:04:00Z",
            skipped_reason="checkpoint_recovery_processed",
        ),
    )
    record = _copy_record(
        _demo_record(),
        started_at="2026-09-24T00:00:00Z",
        requested_at="2026-09-24T00:00:00Z",
        progress={
            "observed_at": "2026-09-24T00:11:00Z",
            "elapsed_seconds": 660,
            "duration_seconds": 604800,
            "duration_elapsed": False,
            "factual_progress_source": "canonical_research_demo_owner_state",
        },
    )

    result = executor.start_research_demo(record)

    assert result["progress"]["observed_at"] == "2026-09-24T00:11:00Z"
    assert result["progress"]["elapsed_seconds"] == 660


def test_canonical_research_demo_dispatch_blocked_cycle_does_not_refresh_successful_progress(monkeypatch):
    record = _copy_record(
        _demo_record(),
        status="RUNNING",
        started_at="2026-09-24T00:00:00Z",
        requested_at="2026-09-24T00:00:00Z",
        progress={
            "observed_at": "2026-09-24T00:05:00Z",
            "elapsed_seconds": 300,
            "factual_progress_source": "canonical_research_demo_owner_state",
        },
    )
    store = _FakeResearchDemoStore(record)
    executor = _executor(monkeypatch, trading_cycle=_FakeTradingCycle(canonical=False))

    with pytest.raises(PostgresPersistenceError, match="research_demo_canonical_execution_cycle_unavailable"):
        ResearchDemoExecutionDispatcher(store=store, executor=executor).dispatch(record.demo_run_id)

    assert store.record.progress["observed_at"] == "2026-09-24T00:05:00Z"
    assert store.record.progress["elapsed_seconds"] == 300


def test_demo_execution_projection_uses_progress_observed_at_as_updated_at():
    execution = _demo_from_execution_owner(
        _execution_owner_record(
            status="RUNNING",
            started_at="2026-09-24T00:00:00Z",
            progress={
                "observed_at": "2026-09-24T00:12:00Z",
                "elapsed_seconds": 720,
                "factual_progress_source": "canonical_research_demo_owner_state",
            },
        )
    )

    assert execution.updated_at == "2026-09-24T00:12:00Z"


def test_canonical_research_demo_executor_finalizes_result_from_accounting_once(monkeypatch):
    executor = _executor(
        monkeypatch,
        now="2026-10-02T00:00:01+00:00",
        trading_cycle=_CycleWithRuntime("BTCUSDT:1m:2026-10-02T00:00:01Z"),
        accounting=_FakeAccountingStore(
            (
                {
                    "trade_id": "trade-win",
                    "research_demo_run_id": "rdm-unit-1",
                    "execution_owner": "ResearchDemoExecution",
                    "research_demo_result_scope": "RESEARCH_DEMO",
                    "trigger_set_id": "triggertrade-futures-core",
                    "trigger_set_version": "v1",
                    "evidence_source": "ACTIVE",
                    "net_pnl": "5",
                    "gross_pnl": "6",
                },
                {
                    "trade_id": "trade-loss",
                    "research_demo_run_id": "rdm-unit-1",
                    "execution_owner": "ResearchDemoExecution",
                    "research_demo_result_scope": "RESEARCH_DEMO",
                    "trigger_set_id": "triggertrade-futures-core",
                    "trigger_set_version": "v1",
                    "evidence_source": "EXCHANGE",
                    "net_pnl": "-2",
                    "gross_pnl": "-1",
                },
            )
        ),
    )
    record = _copy_record(_demo_record(), started_at="2026-09-24T00:00:00Z", requested_at="2026-09-24T00:00:00Z")

    first = executor.start_research_demo(record)
    second = executor.start_research_demo(record)

    assert first == second
    assert first["terminal"] is True
    assert first["result"]["source"] == "canonical_futures_accounting"
    assert first["result"]["trades"] == 2
    assert first["result"]["net_pnl"] == "3"
    assert first["result"]["win_rate"] == "0.5"
    assert first["result"]["profit_factor"] == "2.5"


def test_canonical_research_demo_executor_fails_closed_without_canonical_cycle_evidence(monkeypatch):
    executor = _executor(monkeypatch, trading_cycle=_FakeTradingCycle(canonical=False))
    record = _copy_record(_demo_record(), started_at="2026-09-24T00:00:00Z", requested_at="2026-09-24T00:00:00Z")

    with pytest.raises(PostgresPersistenceError, match="research_demo_canonical_execution_cycle_unavailable"):
        executor.start_research_demo(record)


def test_canonical_research_demo_trading_cycle_provider_uses_exact_pinned_runtime(monkeypatch):
    captured = {}

    class FakeRuntime:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def process_once(self):
            pair = captured["trigger_set_store"].get_active_trading_pair("BTCUSDT", "1m")
            assert pair is not None
            assert pair.trigger_set.set_id == "triggertrade-futures-core"
            assert pair.trigger_set.version == "rdm-unit-1::v1"
            assert pair.rules_version.rules_version_id == "rules-v1"
            assert captured["trading_rules_store"].get_current().rules_version_id == "rules-v1"
            assert [item.position_id for item in captured["position_store"].list_open_positions(include_unknown=True)] == [
                "scoped-position"
            ]
            assert captured["position_store"].open_position_for_symbol("BTCUSDT").position_id == "scoped-position"
            assert [item.intent_id for item in captured["futures_execution_store"].unresolved()] == ["scoped-intent"]
            return FuturesDualLaneResult(
                candle_id="BTCUSDT:1m:2026-09-24T00:00:00Z",
                active=(
                    RuntimeCycleResult(
                        "BTCUSDT:1m:2026-09-24T00:00:00Z",
                        "CONFIRMED",
                        "intent-1",
                        "risk-1",
                        True,
                        "ACKNOWLEDGED",
                    ),
                ),
                test=(),
            )

    monkeypatch.setattr("triggertrade.services.research_demo_execution.FuturesDualLaneRuntime", FakeRuntime)

    class FakeScopedExecutionStore:
        def unresolved(self):
            return (
                SimpleNamespace(
                    intent_id="scoped-intent",
                    trigger_set_id="triggertrade-futures-core",
                    trigger_set_version="rdm-unit-1::v1",
                ),
                SimpleNamespace(
                    intent_id="unrelated-intent",
                    trigger_set_id="triggertrade-futures-core",
                    trigger_set_version="other-run::v1",
                ),
            )

        def get_by_intent(self, intent_id):
            return next((item for item in self.unresolved() if item.intent_id == intent_id), None)

        def get_by_client_order_id(self, client_order_id):
            return None

        def list_recent(self, limit=20):
            return self.unresolved()[:limit]

    class FakeScopedPositionStore:
        def list_open_positions(self, include_unknown=False):
            return (
                SimpleNamespace(
                    position_id="unrelated-position",
                    symbol="BTCUSDT",
                    trigger_set_id="triggertrade-futures-core",
                    trigger_set_version="other-run::v1",
                    rules_version_id="rules-v1",
                    evidence_source="BYBIT_DEMO_ACCOUNT",
                    position_value="10",
                ),
                SimpleNamespace(
                    position_id="scoped-position",
                    symbol="BTCUSDT",
                    trigger_set_id="triggertrade-futures-core",
                    trigger_set_version="rdm-unit-1::v1",
                    rules_version_id="rules-v1",
                    evidence_source="BYBIT_DEMO_ACCOUNT",
                    position_value="10",
                ),
            )

        def open_position_for_symbol(self, symbol):
            return self.list_open_positions(include_unknown=True)[0] if symbol == "BTCUSDT" else None

    provider = CanonicalResearchDemoTradingCycleProvider(
        config=load_config(_demo_runtime_env()),
        factory=object(),
        market_client=object(),
        futures_execution_store=FakeScopedExecutionStore(),
        accounting_store=_FakeAccountingStore(()),
        runtime_store=object(),
        operator_state_store=object(),
        position_store=FakeScopedPositionStore(),
        instrument_catalog=object(),
        active_adapter=object(),
    )

    result = provider.run_research_demo_cycle(
        record=_copy_record(_demo_record(), rules_version_id="rules-v1"),
        configuration=type(
            "Config",
            (),
            {"research": _research_record(), "trigger_set": _trigger_set(), "rules": _rules_version()},
        )(),
    )

    assert result["canonical_cycle"] is True
    assert result["canonical_trading_decisions_invoked"] is True
    assert result["canonical_lifecycle_invoked"] is True
    assert result["canonical_futures_execution_invoked"] is True
    assert result["reconciliation_before_resubmit"] is True
    assert result["runtime"]["active"][0]["execution_status"] == "ACKNOWLEDGED"
    assert result["unresolved_executions"] == 1
    assert result["open_positions"] == 1


def test_canonical_research_demo_trading_cycle_provider_treats_quiet_signal_cycle_as_lifecycle_progress(monkeypatch):
    class FakeRuntime:
        def __init__(self, **kwargs):
            pass

        def process_once(self):
            return FuturesDualLaneResult(
                candle_id="BTCUSDT:1m:2026-09-24T00:00:00Z",
                active=(
                    RuntimeCycleResult(
                        "BTCUSDT:1m:2026-09-24T00:00:00Z",
                        "NO_SIGNAL",
                    ),
                ),
                test=(),
            )

    monkeypatch.setattr("triggertrade.services.research_demo_execution.FuturesDualLaneRuntime", FakeRuntime)
    provider = CanonicalResearchDemoTradingCycleProvider(
        config=load_config(_demo_runtime_env()),
        factory=object(),
        market_client=object(),
        futures_execution_store=_FakeExecutionStore(),
        accounting_store=_FakeAccountingStore(()),
        runtime_store=object(),
        operator_state_store=object(),
        position_store=_FakePositionStore(),
        instrument_catalog=object(),
        active_adapter=object(),
    )

    result = provider.run_research_demo_cycle(
        record=_copy_record(_demo_record(), rules_version_id="rules-v1"),
        configuration=type(
            "Config",
            (),
            {"research": _research_record(), "trigger_set": _trigger_set(), "rules": _rules_version()},
        )(),
    )

    assert result["canonical_trading_decisions_invoked"] is True
    assert result["canonical_lifecycle_invoked"] is True
    assert result["canonical_futures_execution_invoked"] is False
    assert result["unresolved_obligations"] == 0


def test_canonical_research_demo_trading_cycle_provider_treats_already_processed_as_wait_state(monkeypatch):
    class FakeRuntime:
        def __init__(self, **kwargs):
            pass

        def process_once(self):
            return FuturesDualLaneResult(
                candle_id="BTCUSDT:1m:2026-09-24T00:00:00Z",
                active=(
                    RuntimeCycleResult(
                        "BTCUSDT:1m:2026-09-24T00:00:00Z",
                        None,
                        skipped_reason="already_processed",
                    ),
                ),
                test=(),
            )

    monkeypatch.setattr("triggertrade.services.research_demo_execution.FuturesDualLaneRuntime", FakeRuntime)
    provider = CanonicalResearchDemoTradingCycleProvider(
        config=load_config(_demo_runtime_env()),
        factory=object(),
        market_client=object(),
        futures_execution_store=_FakeExecutionStore(),
        accounting_store=_FakeAccountingStore(()),
        runtime_store=object(),
        operator_state_store=object(),
        position_store=_FakePositionStore(),
        instrument_catalog=object(),
        active_adapter=object(),
    )

    result = provider.run_research_demo_cycle(
        record=_copy_record(_demo_record(), rules_version_id="rules-v1"),
        configuration=type(
            "Config",
            (),
            {"research": _research_record(), "trigger_set": _trigger_set(), "rules": _rules_version()},
        )(),
    )

    assert result["canonical_runtime_wait_state"] is True
    assert result["canonical_trading_decisions_invoked"] is False
    assert result["canonical_lifecycle_invoked"] is False
    assert result["unresolved_obligations"] == 0


def test_canonical_research_demo_executor_allows_runtime_wait_state(monkeypatch):
    class WaitTradingCycle:
        canonical_research_demo_trading_cycle = True

        def run_research_demo_cycle(self, *, record, configuration):
            return {
                "canonical_cycle": True,
                "canonical_runtime_wait_state": True,
                "reconciliation_before_resubmit": True,
                "resubmitted_without_reconciliation": False,
                "canonical_trading_decisions_invoked": False,
                "canonical_lifecycle_invoked": False,
                "canonical_futures_execution_invoked": False,
                "unresolved_obligations": 0,
            }

    executor = _executor(monkeypatch, trading_cycle=WaitTradingCycle())
    record = _copy_record(_demo_record(), started_at="2026-09-24T00:00:00Z", requested_at="2026-09-24T00:00:00Z")

    result = executor.start_research_demo(record)

    assert result["terminal"] is False
    assert result["cycle"]["canonical_runtime_wait_state"] is True
    assert "progress" not in result


def test_canonical_research_demo_result_projection_fails_closed_on_attribution_query_error(monkeypatch):
    class BrokenUnitOfWork:
        def __init__(self, factory):
            pass

        def __enter__(self):
            raise RuntimeError("database unavailable")

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(research_demo_execution, "PostgresUnitOfWork", BrokenUnitOfWork)

    with pytest.raises(PostgresPersistenceError, match="closed-trade attribution query failed"):
        research_demo_execution._project_result_from_accounting(
            accounting_store=_FakeAccountingStore(()),
            factory=PostgresConnectionFactory(dsn="postgresql://unit.invalid/triggertrade", schema="unit"),
            demo_run_id="rdm-unit-1",
            set_id="triggertrade-futures-core",
            set_version="v1",
        )


def test_research_demo_daily_loss_store_isolates_same_trading_day_by_demo_run(monkeypatch):
    records: dict[tuple[str, str, str], OwnerStateRecord] = {}
    revisions: dict[tuple[str, str, str], int] = {}

    class FakeOwnerStateStore:
        def __init__(self, connection):
            pass

        def get(self, *, owner, state_type, state_id):
            return records.get((owner, state_type, state_id))

        def put_if_absent(self, *, owner, state_type, state_id, payload):
            key = (owner, state_type, state_id)
            record = records.get(key)
            if record is None:
                revisions[key] = 1
                record = OwnerStateRecord(
                    owner=owner,
                    state_type=state_type,
                    state_id=state_id,
                    payload=payload,
                    payload_digest=canonical_json_digest(payload),
                    revision=revisions[key],
                )
                records[key] = record
            return record, revisions[key] == 1

        def compare_and_set(self, *, owner, state_type, state_id, expected_revision, payload):
            key = (owner, state_type, state_id)
            current = records[key]
            assert current.revision == expected_revision
            revisions[key] = expected_revision + 1
            updated = OwnerStateRecord(
                owner=owner,
                state_type=state_type,
                state_id=state_id,
                payload=payload,
                payload_digest=canonical_json_digest(payload),
                revision=revisions[key],
            )
            records[key] = updated
            return updated

    class FakeUnitOfWork:
        connection = object()

        def __init__(self, factory):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(research_demo_execution, "OwnerStateStore", FakeOwnerStateStore)
    monkeypatch.setattr(research_demo_execution, "PostgresUnitOfWork", FakeUnitOfWork)

    first = _PostgresResearchDemoDailyLossStore(object(), demo_run_id="rdm-one")
    second = _PostgresResearchDemoDailyLossStore(object(), demo_run_id="rdm-two")

    first.ensure_baseline(
        trading_day="2026-09-24",
        baseline_equity=Decimal("100"),
        baseline_source="unit",
        baseline_observed_at="2026-09-24T00:00:00Z",
        updated_at="2026-09-24T00:00:00Z",
    )
    first.latch(
        trading_day="2026-09-24",
        latched_at="2026-09-24T00:01:00Z",
        rules_version_id="rules-v1",
        reason="unit",
    )

    assert first.get_record("2026-09-24").latched is True
    assert second.get_record("2026-09-24") is None

    second.ensure_baseline(
        trading_day="2026-09-24",
        baseline_equity=Decimal("200"),
        baseline_source="unit",
        baseline_observed_at="2026-09-24T00:00:00Z",
        updated_at="2026-09-24T00:00:00Z",
    )

    assert second.get_record("2026-09-24").latched is False
    assert {state_id for _, _, state_id in records} == {"rdm-one::2026-09-24", "rdm-two::2026-09-24"}


def test_research_demo_message_store_replays_same_dedupe_message_with_new_created_at(monkeypatch):
    records: dict[tuple[str, str, str], OwnerStateRecord] = {}

    class FakeOwnerStateStore:
        def __init__(self, connection):
            pass

        def get(self, *, owner, state_type, state_id):
            return records.get((owner, state_type, state_id))

        def put_if_absent(self, *, owner, state_type, state_id, payload):
            key = (owner, state_type, state_id)
            digest = canonical_json_digest(payload)
            existing = records.get(key)
            if existing is not None:
                if existing.payload_digest != digest:
                    raise OwnerStateConflict("owner state identity already exists with different canonical content")
                return existing, False
            record = OwnerStateRecord(
                owner=owner,
                state_type=state_type,
                state_id=state_id,
                payload=payload,
                payload_digest=digest,
                revision=1,
            )
            records[key] = record
            return record, True

    class FakeUnitOfWork:
        connection = object()

        def __init__(self, factory):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(research_demo_execution, "OwnerStateStore", FakeOwnerStateStore)
    monkeypatch.setattr(research_demo_execution, "PostgresUnitOfWork", FakeUnitOfWork)
    store = _PostgresResearchDemoMessageStore(object())
    kwargs = {
        "severity": "ATTENTION",
        "title": "Runtime checkpoint gap detected",
        "body": "Futures runtime detected missed completed candles and is recovering before resuming normal execution.",
        "source": "futures_runtime",
        "entity_type": "runtime_checkpoint",
        "entity_id": "triggertrade-futures-core:v1",
        "dedupe_key": "checkpoint-gap:triggertrade-futures-core:v1",
        "metadata": {
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "checkpoint_before": "2026-09-26T12:01:00+00:00",
        },
    }

    first = store.create_message(created_at="2026-09-26T12:00:00+00:00", **kwargs)
    replay = store.create_message(created_at="2026-09-26T12:05:00+00:00", **kwargs)

    assert replay.message_id == first.message_id
    assert replay.created_at == first.created_at
    assert len(records) == 1


def test_research_demo_message_store_still_blocks_conflicting_dedupe_content(monkeypatch):
    records: dict[tuple[str, str, str], OwnerStateRecord] = {}

    class FakeOwnerStateStore:
        def __init__(self, connection):
            pass

        def get(self, *, owner, state_type, state_id):
            return records.get((owner, state_type, state_id))

        def put_if_absent(self, *, owner, state_type, state_id, payload):
            key = (owner, state_type, state_id)
            digest = canonical_json_digest(payload)
            existing = records.get(key)
            if existing is not None:
                if existing.payload_digest != digest:
                    raise OwnerStateConflict("owner state identity already exists with different canonical content")
                return existing, False
            record = OwnerStateRecord(
                owner=owner,
                state_type=state_type,
                state_id=state_id,
                payload=payload,
                payload_digest=digest,
                revision=1,
            )
            records[key] = record
            return record, True

    class FakeUnitOfWork:
        connection = object()

        def __init__(self, factory):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(research_demo_execution, "OwnerStateStore", FakeOwnerStateStore)
    monkeypatch.setattr(research_demo_execution, "PostgresUnitOfWork", FakeUnitOfWork)
    store = _PostgresResearchDemoMessageStore(object())
    common = {
        "severity": "ATTENTION",
        "title": "Runtime checkpoint gap detected",
        "source": "futures_runtime",
        "entity_type": "runtime_checkpoint",
        "entity_id": "triggertrade-futures-core:v1",
        "dedupe_key": "checkpoint-gap:triggertrade-futures-core:v1",
        "metadata": {
            "symbol": "BTCUSDT",
            "timeframe": "1m",
            "checkpoint_before": "2026-09-26T12:01:00+00:00",
        },
    }

    store.create_message(created_at="2026-09-26T12:00:00+00:00", body="original", **common)
    with pytest.raises(PostgresPersistenceError, match="research demo message identity conflict"):
        store.create_message(created_at="2026-09-26T12:05:00+00:00", body="changed", **common)


def test_research_demo_accounting_daily_loss_reads_are_demo_run_scoped(monkeypatch):
    records: dict[tuple[str, str, str], OwnerStateRecord] = {}

    class FakeOwnerStateStore:
        def __init__(self, connection):
            pass

        def get(self, *, owner, state_type, state_id):
            return records.get((owner, state_type, state_id))

        def put_if_absent(self, *, owner, state_type, state_id, payload):
            key = (owner, state_type, state_id)
            record = records.get(key)
            if record is None:
                record = OwnerStateRecord(
                    owner=owner,
                    state_type=state_type,
                    state_id=state_id,
                    payload=payload,
                    payload_digest=canonical_json_digest(payload),
                    revision=1,
                )
                records[key] = record
            return record, True

    class FakeUnitOfWork:
        connection = object()

        def __init__(self, factory):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params):
            owner, state_type, demo_run_id, execution_owner, result_scope = params
            matches = [
                (state_id, record.payload)
                for (row_owner, row_type, state_id), record in records.items()
                if row_owner == owner
                and row_type == state_type
                and record.payload.get("research_demo_run_id") == demo_run_id
                and record.payload.get("execution_owner") == execution_owner
                and record.payload.get("research_demo_result_scope") == result_scope
            ]
            self.with_state_id = "SELECT state_id" in query
            self.rows = matches

        def fetchall(self):
            import json

            if self.with_state_id:
                return tuple((row[0], json.dumps(row[1])) for row in self.rows)
            return tuple((json.dumps(row[1]),) for row in self.rows)

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

    FakeUnitOfWork.connection = FakeConnection()

    class FakeInnerAccounting:
        def __init__(self):
            self.rows = (
                {
                    "trade_id": "trade-demo",
                    "closed_at": "2026-09-24T01:00:00+00:00",
                    "net_pnl": "-3",
                    "gross_pnl": "-3",
                    "evidence_source": "EXCHANGE",
                },
                {
                    "trade_id": "trade-unrelated",
                    "closed_at": "2026-09-24T02:00:00+00:00",
                    "net_pnl": "-999",
                    "gross_pnl": "-999",
                    "evidence_source": "EXCHANGE",
                },
            )

        def record_closed_trade(self, result):
            return True

        def record_equity_snapshot(self, snapshot):
            return True

        def list_closed_trades(self, limit=20):
            return self.rows[:limit]

    monkeypatch.setattr(research_demo_execution, "OwnerStateStore", FakeOwnerStateStore)
    monkeypatch.setattr(research_demo_execution, "PostgresUnitOfWork", FakeUnitOfWork)

    store = _ResearchDemoAccountingStore(
        inner=FakeInnerAccounting(),
        factory=PostgresConnectionFactory(dsn="postgresql://unit.invalid/triggertrade", schema="unit"),
        demo_run_id="rdm-unit-1",
        set_id="triggertrade-futures-core",
        set_version="v1",
    )
    store.record_closed_trade(
        SimpleNamespace(
            trade_id="trade-demo",
            trigger_set_version="rdm-unit-1::v1",
            evidence_source="EXCHANGE",
        )
    )
    store.record_equity_snapshot(
        EquitySnapshot(
            snapshot_id="snapshot-demo",
            observed_at="2026-09-24T00:05:00+00:00",
            source="BYBIT_DEMO_ACCOUNT",
            wallet_balance=Decimal("100"),
            equity=Decimal("100"),
            available_margin=Decimal("100"),
            used_margin=Decimal("0"),
            unrealized_pnl=Decimal("0"),
            realized_pnl=Decimal("0"),
            running_peak=Decimal("100"),
            drawdown_absolute=Decimal("0"),
            drawdown_percent=Decimal("0"),
            max_drawdown=Decimal("0"),
        )
    )
    store.record_equity_snapshot(
        EquitySnapshot(
            snapshot_id="snapshot-demo-later",
            observed_at="2026-09-24T00:10:00+00:00",
            source="BYBIT_DEMO_ACCOUNT",
            wallet_balance=Decimal("125"),
            equity=Decimal("125"),
            available_margin=Decimal("125"),
            used_margin=Decimal("0"),
            unrealized_pnl=Decimal("0"),
            realized_pnl=Decimal("0"),
            running_peak=Decimal("125"),
            drawdown_absolute=Decimal("0"),
            drawdown_percent=Decimal("0"),
            max_drawdown=Decimal("0"),
        )
    )
    unrelated_snapshot_payload = {
        "snapshot_id": "snapshot-unrelated",
        "research_demo_run_id": "rdm-other",
        "execution_owner": RESEARCH_DEMO_CONSUMER,
        "research_demo_result_scope": "RESEARCH_DEMO",
        "observed_at": "2026-09-24T00:15:00+00:00",
        "source": "BYBIT_DEMO_ACCOUNT",
        "equity": "999",
    }
    records[("ResearchDemoExecution", "research_demo_equity_snapshot_attribution", "snapshot-unrelated")] = OwnerStateRecord(
        owner="ResearchDemoExecution",
        state_type="research_demo_equity_snapshot_attribution",
        state_id="snapshot-unrelated",
        payload=unrelated_snapshot_payload,
        payload_digest=canonical_json_digest(unrelated_snapshot_payload),
        revision=1,
    )

    assert store.realized_net_pnl_for_utc_day("2026-09-24") == Decimal("-3")
    snapshot = store.first_equity_snapshot_for_utc_day("2026-09-24")
    assert snapshot is not None
    assert snapshot["snapshot_id"] == "snapshot-demo"
    assert snapshot["equity"] == "100"
    latest = store.latest_equity_snapshot()
    assert latest is not None
    assert latest["snapshot_id"] == "snapshot-demo-later"
    assert latest["equity"] == "125"


def test_canonical_research_demo_executor_fails_closed_when_cycle_has_no_execution_evidence(monkeypatch):
    provider = _FakeTradingCycle(canonical=True, execution_status=None, unresolved=1)
    executor = _executor(monkeypatch, trading_cycle=provider)
    record = _copy_record(_demo_record(), started_at="2026-09-24T00:00:00Z", requested_at="2026-09-24T00:00:00Z")

    with pytest.raises(PostgresPersistenceError, match="canonical_futures_execution_invoked"):
        executor.start_research_demo(record)


def test_canonical_research_demo_executor_allows_quiet_no_trade_cycle(monkeypatch):
    provider = _FakeTradingCycle(canonical=True, execution_status=None, unresolved=0)
    executor = _executor(monkeypatch, trading_cycle=provider)
    record = _copy_record(_demo_record(), started_at="2026-09-24T00:00:00Z", requested_at="2026-09-24T00:00:00Z")

    result = executor.start_research_demo(record)

    assert result["terminal"] is False
    assert result["cycle"]["canonical_futures_execution_invoked"] is False
    assert result["cycle"]["unresolved_obligations"] == 0


def test_canonical_research_demo_executor_rejects_live_or_non_demo_venue(monkeypatch):
    with pytest.raises(ConfigError, match="Bybit Demo Futures"):
        _executor(
            monkeypatch,
            config=load_config(
                {
                    **_demo_runtime_env(),
                    "TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.LOCAL_PAPER.value,
                }
            ),
        )


def test_research_demo_dispatch_completes_terminal_result_with_canonical_executor(monkeypatch):
    executor = _executor(
        monkeypatch,
        now="2026-10-02T00:00:01+00:00",
        trading_cycle=_CycleWithRuntime("BTCUSDT:1m:2026-10-02T00:00:01Z"),
        accounting=_FakeAccountingStore(()),
    )
    record = _copy_record(_demo_record(), started_at="2026-09-24T00:00:00Z", requested_at="2026-09-24T00:00:00Z")
    store = _FakeResearchDemoStore(record)

    detail = ResearchDemoExecutionDispatcher(store=store, executor=executor).dispatch(record.demo_run_id)
    replay = ResearchDemoExecutionDispatcher(store=store, executor=executor).dispatch(record.demo_run_id)

    assert detail == f"research_demo_completed:{record.demo_run_id}"
    assert replay == "research_demo_replay:COMPLETED"
    assert store.transitions == ["RUNNING", "COMPLETED"]


def test_research_demo_postgres_executor_persists_progress_completion_and_reconnects():
    psycopg = pytest.importorskip("psycopg")
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        handoff = PostgresResearchDemoExecutionHandoff(factory=factory)
        research = _research_record()
        trigger_set = _trigger_set()
        rules = _rules_version()
        handoff.start_research_demo(
            research=research,
            trigger_set=trigger_set,
            rules=rules,
            isolation=_isolation(),
            started_at="2026-09-24T00:00:00+00:00",
            pin_payload={"pin": "research-demo", "research_id": research.research_id},
            demo_run_id="rdm-postgres-executor",
        )
        executor = CanonicalResearchDemoExecutionExecutor(
            config=load_config(_demo_runtime_env()),
            factory=factory,
            trading_cycle=_FakeTradingCycle(candle_id="BTCUSDT:1m:2026-10-02T00:00:01Z"),
            accounting_store=_FakeAccountingStore(()),
            clock=lambda: datetime.fromisoformat("2026-10-02T00:00:01+00:00"),
        )
        with PostgresUnitOfWork(factory) as uow:
            detail = ResearchDemoExecutionDispatcher(
                store=ResearchDemoExecutionStore(uow.connection),
                executor=executor,
            ).dispatch("rdm-postgres-executor")
        with PostgresUnitOfWork(factory) as uow:
            reloaded = ResearchDemoExecutionStore(uow.connection).get("rdm-postgres-executor")
            replay = ResearchDemoExecutionDispatcher(
                store=ResearchDemoExecutionStore(uow.connection),
                executor=executor,
            ).dispatch("rdm-postgres-executor")

        assert detail == "research_demo_completed:rdm-postgres-executor"
        assert replay == "research_demo_replay:COMPLETED"
        assert reloaded is not None
        assert reloaded.status == "COMPLETED"
        assert reloaded.result is not None
        assert reloaded.result["result"]["source"] == "canonical_futures_accounting"
    finally:
        with psycopg.connect(settings.dsn, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


class _FakeResearchDemoStore:
    def __init__(self, record: ResearchDemoExecutionRecord) -> None:
        self.record = record
        self.transitions: list[str] = []
        self.rechecks: list[str] = []

    def get(self, demo_run_id: str):
        assert demo_run_id == self.record.demo_run_id
        return self.record

    def mark_running(self, demo_run_id: str, *, progress=None):
        self.transitions.append("RUNNING")
        started_at = self.record.started_at or "2026-09-24T00:00:01Z"
        merged_progress = None if progress is None else research_demo_execution._monotonic_progress(record=self.record, candidate=progress)
        self.record = _copy_record(
            self.record,
            status="RUNNING",
            started_at=started_at,
            progress={**self.record.progress, **(merged_progress or {}), "started_at": started_at},
        )
        return self.record

    def mark_completed(self, demo_run_id: str, *, result):
        self.transitions.append("COMPLETED")
        self.record = _copy_record(self.record, status="COMPLETED", result=result)
        return self.record

    def enqueue_recheck(self, record):
        self.rechecks.append(record.demo_run_id)


class _FakeResearchDemoExecutor:
    canonical_research_demo_executor = True

    def __init__(self) -> None:
        self.calls: list[str] = []

    def start_research_demo(self, record):
        self.calls.append(record.demo_run_id)
        return {"terminal": False, "source": "canonical_test_executor"}


class _FakeTradingCycle:
    canonical_research_demo_trading_cycle = True

    def __init__(
        self,
        *,
        unresolved=0,
        canonical=True,
        execution_status="ACKNOWLEDGED",
        candle_id="BTCUSDT:1m:2026-09-25T00:00:00Z",
    ):
        self.unresolved = unresolved
        self.canonical = canonical
        self.execution_status = execution_status
        self.candle_id = candle_id
        self.calls = []

    def run_research_demo_cycle(self, *, record, configuration):
        self.calls.append((record.demo_run_id, configuration.research.research_id))
        return {
            "canonical_cycle": self.canonical,
            "reconciliation_before_resubmit": self.canonical,
            "resubmitted_without_reconciliation": False,
            "canonical_trading_decisions_invoked": self.canonical,
            "canonical_lifecycle_invoked": self.canonical,
            "canonical_futures_execution_invoked": self.canonical and self.execution_status is not None,
            "unresolved_obligations": self.unresolved,
            "runtime": {
                "active": (
                    {
                        "candle_id": self.candle_id,
                        "signal_type": "CONFIRMED",
                        "intent_id": "intent-unit",
                        "risk_decision_id": "risk-unit",
                        "risk_approved": True,
                        "execution_status": self.execution_status,
                        "skipped_reason": None,
                    },
                ),
                "test": (),
            },
        }


class _CycleWithRuntime:
    canonical_research_demo_trading_cycle = True

    def __init__(self, candle_id: str, *, signal_type: str = "CONFIRMED", execution_status="ACKNOWLEDGED", skipped_reason=None):
        self.candle_id = candle_id
        self.signal_type = signal_type
        self.execution_status = execution_status
        self.skipped_reason = skipped_reason

    def run_research_demo_cycle(self, *, record, configuration):
        return {
            "canonical_cycle": True,
            "reconciliation_before_resubmit": True,
            "resubmitted_without_reconciliation": False,
            "canonical_runtime_wait_state": False,
            "canonical_trading_decisions_invoked": True,
            "canonical_lifecycle_invoked": True,
            "canonical_futures_execution_invoked": self.execution_status is not None,
            "unresolved_obligations": 0,
            "runtime": {
                "active": (
                    {
                        "candle_id": self.candle_id,
                        "signal_type": self.signal_type,
                        "intent_id": "intent-unit",
                        "risk_decision_id": "risk-unit",
                        "risk_approved": True,
                        "execution_status": self.execution_status,
                        "skipped_reason": self.skipped_reason,
                    },
                ),
                "test": (),
            },
        }


class _FakeAccountingStore:
    def __init__(self, rows):
        self.rows = tuple(rows)

    def list_closed_trades(self, limit=20):
        return self.rows[:limit]


class _FakeExecutionStore:
    def unresolved(self):
        return ()


class _FakePositionStore:
    def list_open_positions(self, include_unknown=False):
        return ()


def _executor(monkeypatch, *, now="2026-09-25T00:00:00+00:00", config=None, accounting=None, trading_cycle=None):
    class FakeUnitOfWork:
        connection = object()

        def __init__(self, factory):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeRegistry:
        def __init__(self, connection):
            pass

        def get_research_demo_configuration(self, *, research_id, set_id, set_version, rules_version_id):
            research = _research_record()
            trigger_set = _trigger_set()
            rules = _rules_version()
            assert (research_id, set_id, set_version, rules_version_id) == (
                research.research_id,
                trigger_set.set_id,
                trigger_set.version,
                rules.rules_version_id,
            )
            return type("Config", (), {"research": research, "trigger_set": trigger_set, "rules": rules})()

    monkeypatch.setattr("triggertrade.services.research_demo_execution.PostgresUnitOfWork", FakeUnitOfWork)
    monkeypatch.setattr("triggertrade.services.research_demo_execution.PostgresResearchConfigurationRegistry", FakeRegistry)
    return CanonicalResearchDemoExecutionExecutor(
        config=config or load_config(_demo_runtime_env()),
        factory=object(),
        trading_cycle=trading_cycle or _FakeTradingCycle(),
        accounting_store=accounting or _FakeAccountingStore(()),
        clock=lambda: datetime.fromisoformat(now),
    )


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


def _demo_run_projection(*, status: ResearchDemoStatus, started_at=None, stopped_at=None, metrics=None, blocked_reason=None):
    return ResearchDemoRunRecord(
        research_id="res-unit-1",
        run_id="rdm-unit-1",
        created_at="2026-09-24T00:00:00Z",
        updated_at=stopped_at or started_at or "2026-09-24T00:00:00Z",
        status=status,
        started_at=started_at,
        stopped_at=stopped_at,
        execution_scope_id="research-demo-worker",
        account_scope="research-demo-postgres",
        selected_for_use=False,
        metrics=metrics or {},
        blocked_reason=blocked_reason,
        pin_payload={"pin": "research-demo-web"},
        pin_digest="web-pin-digest",
    )


def _execution_owner_record(*, status: str, started_at, completed_at=None, error=None, result=None, progress=None):
    payload = {
        "demo_run_id": "rdm-unit-1",
        "research_id": "res-unit-1",
        "set_id": "triggertrade-futures-core",
        "set_version": "v1",
        "rules_version_id": "rules-v1",
        "rules_display_version": "v1",
        "requested_at": "2026-09-24T00:00:00Z",
        "started_at": started_at,
        "completed_at": completed_at,
        "execution_owner": "trading-worker",
        "handoff_message_id": "research-demo-start-unit-1",
        "status": status,
        "progress": progress or {"factual_progress_source": "canonical_research_demo_owner_state"},
        "result": result,
        "error": error,
        "pin_payload": {"pin": "research-demo-execution"},
        "pin_digest": "execution-pin-digest",
    }
    return OwnerStateRecord(
        owner="ResearchDemoExecution",
        state_type="RESEARCH_DEMO_RUN",
        state_id="rdm-unit-1",
        revision=1,
        payload=payload,
        payload_digest=canonical_json_digest(payload),
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


def _demo_runtime_env() -> dict[str, str]:
    return {
        "TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO_FUTURES.value,
        "TRIGGERTRADE_ACTIVE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO_FUTURES.value,
        "TRIGGERTRADE_TEST_EXECUTION_VENUE": ExecutionVenue.LOCAL_TEST_SIMULATION.value,
        "TRIGGERTRADE_BYBIT_ENV": "demo",
        "BYBIT_BASE_URL": "https://api-demo.bybit.com",
        "TRIGGERTRADE_MARKET": "linear",
        "TRIGGERTRADE_CATEGORY": "linear",
        "TRIGGERTRADE_LIVE_TRADING_ENABLED": "false",
    }
