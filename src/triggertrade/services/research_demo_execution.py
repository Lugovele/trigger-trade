"""Durable Research Demo execution handoff and worker dispatch."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, DivisionByZero, InvalidOperation
from hashlib import sha256
from typing import Any, Protocol

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.config import AppConfig, BybitEnvironment, ConfigError, ExecutionVenue, Market
from triggertrade.persistence import RuntimeHeartbeat
from triggertrade.persistence.daily_loss_store import DailyLossRecord
from triggertrade.persistence.durable_messages import DurableMessageStore
from triggertrade.persistence.message_store import MessageRecord, MessageSeverity
from triggertrade.persistence.postgres_research_registry import PostgresResearchConfigurationRegistry
from triggertrade.persistence.postgres import (
    OwnerStateRecord,
    OwnerStateRevisionConflict,
    OwnerStateStore,
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresUnitOfWork,
)
from triggertrade.persistence.research_store import ResearchRecord
from triggertrade.persistence.trigger_set_store import ActiveTradingPair, TriggerSetStoreError
from triggertrade.rules import TradingRulesVersion
from triggertrade.services.futures_runtime import FuturesDualLaneResult, FuturesDualLaneRuntime
from triggertrade.trigger_sets import Lane, RuleDefinition, RuleStatus, RuleType, TriggerSetVersion
from triggertrade.services.research import (
    ResearchDemoExecutionHandoffResult,
    ResearchDemoIsolation,
)


RESEARCH_DEMO_OWNER = "ResearchDemoExecution"
RESEARCH_DEMO_STATE_TYPE = "RESEARCH_DEMO_RUN"
RESEARCH_DEMO_PRODUCER = "Research"
RESEARCH_DEMO_CONSUMER = "ResearchDemoExecution"
RESEARCH_DEMO_MESSAGE_TYPE = "RESEARCH_DEMO_START"
RESEARCH_DEMO_MESSAGE_VERSION = "1"
TERMINAL_RESEARCH_DEMO_STATUSES = {"COMPLETED", "FAILED", "BLOCKED"}
DEMO_DURATION_DAYS = 7
RESEARCH_DEMO_RECHECK_DELAY_SECONDS = 60


@dataclass(frozen=True)
class ResearchDemoExecutionRecord:
    demo_run_id: str
    research_id: str
    set_id: str
    set_version: str
    rules_version_id: str
    rules_display_version: str
    requested_at: str
    started_at: str | None
    completed_at: str | None
    execution_owner: str
    handoff_message_id: str
    status: str
    progress: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    pin_payload: dict[str, Any]
    pin_digest: str
    revision: int = 0


class ResearchDemoExecutionExecutor(Protocol):
    canonical_research_demo_executor: bool

    def start_research_demo(self, record: ResearchDemoExecutionRecord) -> dict[str, Any]: ...


class ResearchDemoTradingCycle(Protocol):
    canonical_research_demo_trading_cycle: bool

    def run_research_demo_cycle(self, *, record: ResearchDemoExecutionRecord, configuration) -> dict[str, Any]: ...


class ResearchDemoAccountingProjection(Protocol):
    def list_closed_trades(self, limit: int = 20) -> tuple[dict[str, Any], ...]: ...


class CanonicalFuturesResearchDemoStateObserver:
    """Read canonical futures state without certifying trading decisions."""

    canonical_research_demo_trading_cycle = False

    def __init__(self, *, futures_execution_store, position_store) -> None:
        self._futures_execution_store = futures_execution_store
        self._position_store = position_store

    def run_research_demo_cycle(self, *, record: ResearchDemoExecutionRecord, configuration) -> dict[str, Any]:
        unresolved = tuple(self._futures_execution_store.unresolved())
        positions = tuple(self._position_store.list_open_positions(include_unknown=True))
        matching_positions = tuple(
            position
            for position in positions
            if getattr(position, "rules_version_id", None) in {None, record.rules_version_id}
            and str(getattr(position, "evidence_source", "")).upper() in {"ACTIVE", "EXCHANGE"}
        )
        return {
            "canonical_cycle": False,
            "cycle_mode": "canonical_futures_reconciliation_state",
            "reconciliation_before_resubmit": True,
            "exchange_submissions": 0,
            "resubmitted_without_reconciliation": False,
            "canonical_trading_decisions_invoked": False,
            "canonical_lifecycle_invoked": False,
            "canonical_futures_execution_invoked": False,
            "unresolved_executions": len(unresolved),
            "open_positions": len(matching_positions),
            "unresolved_obligations": len(unresolved) + len(matching_positions),
            "set_id": configuration.trigger_set.set_id,
            "set_version": configuration.trigger_set.version,
            "rules_version_id": configuration.rules.rules_version_id,
        }


class CanonicalResearchDemoTradingCycleProvider:
    """Run the existing canonical futures runtime against exact Research Demo pins."""

    canonical_research_demo_trading_cycle = True

    def __init__(
        self,
        *,
        config: AppConfig,
        factory: PostgresConnectionFactory,
        market_client,
        futures_execution_store,
        accounting_store,
        runtime_store,
        operator_state_store,
        position_store,
        instrument_catalog,
        active_adapter,
        account_provider=None,
        allow_uncertified_active_formula_execution: bool = False,
        clock=None,
    ) -> None:
        self._config = config
        self._factory = factory
        self._market_client = market_client
        self._futures_execution_store = futures_execution_store
        self._accounting_store = accounting_store
        self._runtime_store = runtime_store
        self._operator_state_store = operator_state_store
        self._position_store = position_store
        self._instrument_catalog = instrument_catalog
        self._active_adapter = active_adapter
        self._account_provider = account_provider
        self._allow_uncertified_active_formula_execution = allow_uncertified_active_formula_execution
        self._clock = clock

    def run_research_demo_cycle(self, *, record: ResearchDemoExecutionRecord, configuration) -> dict[str, Any]:
        trigger_set = configuration.trigger_set
        rules = configuration.rules
        trace_store = _PostgresResearchDemoTraceStore(self._factory, demo_run_id=record.demo_run_id)
        accounting_store = _ResearchDemoAccountingStore(
            inner=self._accounting_store,
            factory=self._factory,
            demo_run_id=record.demo_run_id,
            set_id=record.set_id,
            set_version=record.set_version,
        )
        runtime_trigger_set = _runtime_scoped_trigger_set(trigger_set, demo_run_id=record.demo_run_id)
        position_store = _ResearchDemoPositionStore(
            inner=self._position_store,
            trigger_set_id=trigger_set.set_id,
            trigger_set_version=runtime_trigger_set.version,
            rules_version_id=record.rules_version_id,
        )
        futures_execution_store = _ResearchDemoExecutionStore(
            inner=self._futures_execution_store,
            trigger_set_id=trigger_set.set_id,
            trigger_set_version=runtime_trigger_set.version,
        )
        runtime = FuturesDualLaneRuntime(
            config=self._config,
            market_client=self._market_client,
            futures_execution_store=futures_execution_store,
            accounting_store=accounting_store,
            trace_store=trace_store,
            runtime_store=_ResearchDemoRuntimeStore(self._runtime_store, demo_run_id=record.demo_run_id),
            trigger_set_store=_ExactResearchDemoTriggerSetStore(trigger_set=runtime_trigger_set, rules=rules),
            operator_state_store=self._operator_state_store,
            trading_rules_store=_ExactResearchDemoTradingRulesStore(rules),
            daily_loss_store=_PostgresResearchDemoDailyLossStore(self._factory, demo_run_id=record.demo_run_id),
            message_store=_PostgresResearchDemoMessageStore(self._factory),
            position_store=position_store,
            active_adapter=self._active_adapter,
            account_provider=self._account_provider,
            instrument_catalog=self._instrument_catalog,
            allow_uncertified_active_formula_execution=self._allow_uncertified_active_formula_execution,
            clock=self._clock,
        )
        result = runtime.process_once()
        unresolved = tuple(futures_execution_store.unresolved())
        positions = tuple(position_store.list_open_positions(include_unknown=True))
        matching_positions = tuple(
            position
            for position in positions
            if getattr(position, "rules_version_id", None) in {None, record.rules_version_id}
            and str(getattr(position, "evidence_source", "")).upper() in {"ACTIVE", "EXCHANGE", "BYBIT_DEMO_ACCOUNT"}
        )
        active_payloads = tuple(_cycle_result_payload(item) for item in result.active)
        runtime_wait_state = _canonical_runtime_wait_state(result, active_payloads)
        decision_invoked = any(item["signal_type"] not in {None, ""} for item in active_payloads)
        lifecycle_invoked = any(
            item["risk_decision_id"] not in {None, ""}
            or item["intent_id"] not in {None, ""}
            or item["signal_type"] not in {None, ""}
            for item in active_payloads
        )
        futures_execution_invoked = any(item["execution_status"] not in {None, "", "test_simulated"} for item in active_payloads)
        reconciled_before_resubmit = (
            not futures_execution_invoked
            or any(str(item["execution_status"]).upper() != "UNKNOWN" for item in active_payloads)
        )
        return {
            "canonical_cycle": True,
            "cycle_mode": "futures_dual_lane_runtime",
            "reconciliation_before_resubmit": reconciled_before_resubmit,
            "resubmitted_without_reconciliation": False,
            "canonical_runtime_wait_state": runtime_wait_state,
            "canonical_trading_decisions_invoked": decision_invoked,
            "canonical_lifecycle_invoked": lifecycle_invoked,
            "canonical_futures_execution_invoked": futures_execution_invoked,
            "unresolved_executions": len(unresolved),
            "open_positions": len(matching_positions),
            "unresolved_obligations": len(unresolved) + len(matching_positions),
            "set_id": trigger_set.set_id,
            "set_version": trigger_set.version,
            "rules_version_id": rules.rules_version_id,
            "runtime": _runtime_result_payload(result),
            "audit_events_recorded": trace_store.audit_events_recorded,
        }


class CanonicalResearchDemoExecutionExecutor:
    """Trading-worker owned Research Demo executor over canonical Postgres state."""

    canonical_research_demo_executor = True

    def __init__(
        self,
        *,
        config: AppConfig,
        factory: PostgresConnectionFactory,
        trading_cycle: ResearchDemoTradingCycle,
        accounting_store: ResearchDemoAccountingProjection,
        clock=None,
    ) -> None:
        self._config = config
        self._factory = factory
        self._trading_cycle = trading_cycle
        self._accounting_store = accounting_store
        self._clock = clock or (lambda: datetime.now(UTC))
        self._validate_demo_runtime()
        if not getattr(trading_cycle, "canonical_research_demo_trading_cycle", False):
            raise ConfigError("Research Demo executor requires canonical trading cycle dependency")

    def start_research_demo(self, record: ResearchDemoExecutionRecord) -> dict[str, Any]:
        configuration = self._load_exact_configuration(record)
        cycle_result = self._trading_cycle.run_research_demo_cycle(record=record, configuration=configuration)
        if bool(cycle_result.get("resubmitted_without_reconciliation")):
            raise PostgresPersistenceError("research_demo_reconciliation_before_resubmit_failed")
        _require_canonical_cycle_evidence(cycle_result)
        unresolved = int(cycle_result.get("unresolved_obligations") or 0)
        progress = _progress(record=record, now=self._clock())
        if not progress["duration_elapsed"]:
            return {
                "terminal": False,
                "execution_owner": "trading-worker",
                "durable": True,
                "canonical_execution": True,
                "configuration": _configuration_identity(configuration),
                "progress": progress,
                "cycle": dict(cycle_result),
            }
        if unresolved > 0:
            return {
                "terminal": False,
                "execution_owner": "trading-worker",
                "durable": True,
                "canonical_execution": True,
                "configuration": _configuration_identity(configuration),
                "progress": {**progress, "completion_blocked_reason": "unresolved_execution_obligations"},
                "cycle": dict(cycle_result),
            }
        result = _project_result_from_accounting(
            accounting_store=self._accounting_store,
            factory=self._factory,
            demo_run_id=record.demo_run_id,
            set_id=record.set_id,
            set_version=record.set_version,
        )
        return {
            "terminal": True,
            "execution_owner": "trading-worker",
            "durable": True,
            "canonical_execution": True,
            "configuration": _configuration_identity(configuration),
            "progress": {**progress, "completion_source": "canonical_accounting_projection"},
            "cycle": dict(cycle_result),
            "result": result,
        }

    def _load_exact_configuration(self, record: ResearchDemoExecutionRecord):
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchConfigurationRegistry(uow.connection).get_research_demo_configuration(
                research_id=record.research_id,
                set_id=record.set_id,
                set_version=record.set_version,
                rules_version_id=record.rules_version_id,
            )

    def _validate_demo_runtime(self) -> None:
        if self._config.live_trading_enabled:
            raise ConfigError("Research Demo executor rejects live trading")
        if self._config.bybit.environment is not BybitEnvironment.DEMO:
            raise ConfigError("Research Demo executor requires Bybit demo environment")
        if self._config.bybit.base_url != "https://api-demo.bybit.com":
            raise ConfigError("Research Demo executor requires BYBIT_BASE_URL=https://api-demo.bybit.com")
        if self._config.market is not Market.LINEAR:
            raise ConfigError("Research Demo executor requires linear market")
        if self._config.execution_venue is not ExecutionVenue.BYBIT_DEMO_FUTURES:
            raise ConfigError("Research Demo executor requires Bybit Demo Futures execution venue")
        if self._config.futures_runtime.active_execution_venue is not ExecutionVenue.BYBIT_DEMO_FUTURES:
            raise ConfigError("Research Demo executor requires active Bybit Demo Futures venue")
        if self._config.futures_runtime.category != "linear":
            raise ConfigError("Research Demo executor requires linear futures category")


class PostgresResearchDemoExecutionHandoff:
    """Web-side ingress that persists Research Demo work for the trading worker."""

    canonical_worker_handoff = True

    def __init__(self, *, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def start_research_demo(
        self,
        *,
        research: ResearchRecord,
        trigger_set: TriggerSetVersion,
        rules: TradingRulesVersion,
        isolation: ResearchDemoIsolation,
        started_at: str,
        pin_payload: dict[str, Any],
        demo_run_id: str,
    ) -> ResearchDemoExecutionHandoffResult:
        with PostgresUnitOfWork(self._factory) as uow:
            PostgresResearchConfigurationRegistry(uow.connection).put_configuration(
                research=research,
                trigger_set=trigger_set,
                rules=rules,
            )
            record = ResearchDemoExecutionStore(uow.connection).submit(
                research=research,
                rules=rules,
                isolation=isolation,
                started_at=started_at,
                pin_payload=pin_payload,
                demo_run_id=demo_run_id,
            )
        return ResearchDemoExecutionHandoffResult(
            handoff_id=record.handoff_message_id,
            execution_owner=record.execution_owner,
            durable=True,
        )


class ResearchDemoExecutionStore:
    """PostgreSQL owner-state wrapper for durable Research Demo execution state."""

    def __init__(self, connection) -> None:
        self._owner_state = OwnerStateStore(connection)
        self._messages = DurableMessageStore(connection)

    def submit(
        self,
        *,
        research: ResearchRecord,
        rules: TradingRulesVersion,
        isolation: ResearchDemoIsolation,
        started_at: str,
        pin_payload: dict[str, Any],
        demo_run_id: str,
    ) -> ResearchDemoExecutionRecord:
        demo_run_id = _required_text(demo_run_id, field="demo_run_id")
        started_at = _required_text(started_at, field="started_at")
        message_id = _message_id(demo_run_id)
        pin_digest = canonical_json_digest(pin_payload)
        existing = self.get(demo_run_id)
        if existing is not None:
            if existing.pin_digest != pin_digest or existing.research_id != research.research_id:
                raise PostgresPersistenceError("research demo run identity already exists with different content")
            if existing.status not in TERMINAL_RESEARCH_DEMO_STATUSES:
                self._append_outbox(existing)
            return existing

        record = ResearchDemoExecutionRecord(
            demo_run_id=demo_run_id,
            research_id=research.research_id,
            set_id=research.set_id,
            set_version=research.set_version,
            rules_version_id=rules.rules_version_id,
            rules_display_version=rules.version,
            requested_at=started_at,
            started_at=None,
            completed_at=None,
            execution_owner="trading-worker",
            handoff_message_id=message_id,
            status="PENDING",
            progress={
                "duration_days": 7,
                "started_at": None,
                "completed_at": None,
                "factual_progress_source": "canonical_research_demo_owner_state",
            },
            result=None,
            error=None,
            pin_payload=dict(pin_payload),
            pin_digest=pin_digest,
        )
        owner, _ = self._owner_state.put_if_absent(
            owner=RESEARCH_DEMO_OWNER,
            state_type=RESEARCH_DEMO_STATE_TYPE,
            state_id=demo_run_id,
            payload=_record_payload(record),
        )
        persisted = _record_from_owner(owner)
        self._append_outbox(persisted)
        return persisted

    def get(self, demo_run_id: str) -> ResearchDemoExecutionRecord | None:
        record = self._owner_state.get(
            owner=RESEARCH_DEMO_OWNER,
            state_type=RESEARCH_DEMO_STATE_TYPE,
            state_id=_required_text(demo_run_id, field="demo_run_id"),
        )
        return None if record is None else _record_from_owner(record)

    def mark_running(self, demo_run_id: str, *, progress: dict[str, Any] | None = None) -> ResearchDemoExecutionRecord:
        current = self.get(demo_run_id)
        if current is None:
            raise PostgresPersistenceError("research demo execution state not found")
        if current.status in TERMINAL_RESEARCH_DEMO_STATUSES:
            return current
        now = _timestamp()
        return self._transition(
            current,
            status="RUNNING",
            started_at=current.started_at or now,
            progress={**current.progress, **(progress or {}), "started_at": current.started_at or now},
        )

    def mark_completed(self, demo_run_id: str, *, result: dict[str, Any]) -> ResearchDemoExecutionRecord:
        current = self.get(demo_run_id)
        if current is None:
            raise PostgresPersistenceError("research demo execution state not found")
        if current.status in TERMINAL_RESEARCH_DEMO_STATUSES:
            return current
        now = _timestamp()
        return self._transition(
            current,
            status="COMPLETED",
            completed_at=now,
            progress={**current.progress, "completed_at": now, "terminal": True},
            result=result,
        )

    def mark_failed(self, demo_run_id: str, *, error: str) -> ResearchDemoExecutionRecord:
        current = self.get(demo_run_id)
        if current is None:
            raise PostgresPersistenceError("research demo execution state not found")
        if current.status in TERMINAL_RESEARCH_DEMO_STATUSES:
            return current
        now = _timestamp()
        return self._transition(
            current,
            status="FAILED",
            completed_at=now,
            progress={**current.progress, "completed_at": now, "terminal": True},
            error=_public_error(error),
        )

    def _transition(
        self,
        current: ResearchDemoExecutionRecord,
        *,
        status: str,
        started_at: str | None = None,
        completed_at: str | None = None,
        progress: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> ResearchDemoExecutionRecord:
        updated = ResearchDemoExecutionRecord(
            demo_run_id=current.demo_run_id,
            research_id=current.research_id,
            set_id=current.set_id,
            set_version=current.set_version,
            rules_version_id=current.rules_version_id,
            rules_display_version=current.rules_display_version,
            requested_at=current.requested_at,
            started_at=started_at if started_at is not None else current.started_at,
            completed_at=completed_at if completed_at is not None else current.completed_at,
            execution_owner=current.execution_owner,
            handoff_message_id=current.handoff_message_id,
            status=status,
            progress=progress if progress is not None else current.progress,
            result=result if result is not None else current.result,
            error=error if error is not None else current.error,
            pin_payload=current.pin_payload,
            pin_digest=current.pin_digest,
            revision=current.revision,
        )
        for _ in range(3):
            try:
                owner = self._owner_state.compare_and_set(
                    owner=RESEARCH_DEMO_OWNER,
                    state_type=RESEARCH_DEMO_STATE_TYPE,
                    state_id=current.demo_run_id,
                    expected_revision=current.revision,
                    payload=_record_payload(updated),
                )
                return _record_from_owner(owner)
            except OwnerStateRevisionConflict:
                latest = self.get(current.demo_run_id)
                if latest is None:
                    raise
                if latest.status in TERMINAL_RESEARCH_DEMO_STATUSES:
                    return latest
                current = latest
        raise OwnerStateRevisionConflict("research demo execution state changed concurrently")

    def _append_outbox(self, record: ResearchDemoExecutionRecord) -> None:
        if record.status in TERMINAL_RESEARCH_DEMO_STATUSES:
            return
        self._messages.append_outbox(
            message_id=record.handoff_message_id,
            producer=RESEARCH_DEMO_PRODUCER,
            consumer=RESEARCH_DEMO_CONSUMER,
            message_type=RESEARCH_DEMO_MESSAGE_TYPE,
            message_version=RESEARCH_DEMO_MESSAGE_VERSION,
            payload={"research_demo": _record_payload(record)},
            aggregate_id=record.research_id,
            causation_id=record.demo_run_id,
            correlation_id=record.demo_run_id,
            dedupe_key=f"RESEARCH_DEMO_START:{record.demo_run_id}",
        )

    def enqueue_recheck(self, record: ResearchDemoExecutionRecord) -> None:
        if record.status in TERMINAL_RESEARCH_DEMO_STATUSES:
            return
        self._messages.append_outbox(
            message_id=_recheck_message_id(record),
            producer=RESEARCH_DEMO_PRODUCER,
            consumer=RESEARCH_DEMO_CONSUMER,
            message_type=RESEARCH_DEMO_MESSAGE_TYPE,
            message_version=RESEARCH_DEMO_MESSAGE_VERSION,
            payload={"research_demo": _record_payload(record)},
            aggregate_id=record.research_id,
            causation_id=record.handoff_message_id,
            correlation_id=record.demo_run_id,
            dedupe_key=f"RESEARCH_DEMO_RECHECK:{record.demo_run_id}:{record.revision}",
            available_at=datetime.now(UTC) + timedelta(seconds=RESEARCH_DEMO_RECHECK_DELAY_SECONDS),
        )


class ResearchDemoExecutionDispatcher:
    """Trading-worker side dispatcher for durable Research Demo handoffs."""

    def __init__(
        self,
        *,
        store: ResearchDemoExecutionStore,
        executor: ResearchDemoExecutionExecutor | None,
    ) -> None:
        self._store = store
        self._executor = executor

    def dispatch(self, demo_run_id: str) -> str:
        record = self._store.get(demo_run_id)
        if record is None:
            raise PostgresPersistenceError("research_demo_execution_state_not_found")
        if record.status in TERMINAL_RESEARCH_DEMO_STATUSES:
            return f"research_demo_replay:{record.status}"
        if self._executor is None or not getattr(self._executor, "canonical_research_demo_executor", False):
            raise PostgresPersistenceError("research_demo_canonical_executor_unavailable")
        record = self._store.mark_running(record.demo_run_id)
        result = self._executor.start_research_demo(record)
        if bool(result.get("terminal")):
            completed = self._store.mark_completed(record.demo_run_id, result=dict(result))
            return f"research_demo_completed:{completed.demo_run_id}"
        progress = result.get("progress")
        if isinstance(progress, dict):
            record = self._store.mark_running(record.demo_run_id, progress=progress)
        self._store.enqueue_recheck(record)
        return f"research_demo_running:{record.demo_run_id}"


def research_demo_run_id(*, research_id: str, pin_digest: str, started_at: str) -> str:
    source = "|".join(
        [
            _required_text(research_id, field="research_id"),
            _required_text(pin_digest, field="pin_digest"),
            _required_text(started_at, field="started_at"),
        ]
    )
    return f"rdm-{sha256(source.encode('utf-8')).hexdigest()[:20]}"


def _record_payload(record: ResearchDemoExecutionRecord) -> dict[str, Any]:
    return {
        "demo_run_id": record.demo_run_id,
        "research_id": record.research_id,
        "set_id": record.set_id,
        "set_version": record.set_version,
        "rules_version_id": record.rules_version_id,
        "rules_display_version": record.rules_display_version,
        "requested_at": record.requested_at,
        "started_at": record.started_at,
        "completed_at": record.completed_at,
        "execution_owner": record.execution_owner,
        "handoff_message_id": record.handoff_message_id,
        "status": record.status,
        "progress": record.progress,
        "result": record.result,
        "error": record.error,
        "pin_payload": record.pin_payload,
        "pin_digest": record.pin_digest,
    }


def _record_from_owner(record: OwnerStateRecord) -> ResearchDemoExecutionRecord:
    payload = record.payload
    return ResearchDemoExecutionRecord(
        demo_run_id=_required_text(payload.get("demo_run_id"), field="demo_run_id"),
        research_id=_required_text(payload.get("research_id"), field="research_id"),
        set_id=_required_text(payload.get("set_id"), field="set_id"),
        set_version=_required_text(payload.get("set_version"), field="set_version"),
        rules_version_id=_required_text(payload.get("rules_version_id"), field="rules_version_id"),
        rules_display_version=_required_text(payload.get("rules_display_version"), field="rules_display_version"),
        requested_at=_required_text(payload.get("requested_at"), field="requested_at"),
        started_at=_optional_text(payload.get("started_at"), field="started_at"),
        completed_at=_optional_text(payload.get("completed_at"), field="completed_at"),
        execution_owner=_required_text(payload.get("execution_owner"), field="execution_owner"),
        handoff_message_id=_required_text(payload.get("handoff_message_id"), field="handoff_message_id"),
        status=_required_text(payload.get("status"), field="status"),
        progress=dict(payload.get("progress") or {}),
        result=None if payload.get("result") is None else dict(payload.get("result") or {}),
        error=_optional_text(payload.get("error"), field="error"),
        pin_payload=dict(payload.get("pin_payload") or {}),
        pin_digest=_required_text(payload.get("pin_digest"), field="pin_digest"),
        revision=record.revision,
    )


class _ExactResearchDemoTriggerSetStore:
    def __init__(self, *, trigger_set: TriggerSetVersion, rules: TradingRulesVersion) -> None:
        self._trigger_set = trigger_set
        self._rules = rules

    def get_active_trading_pair(self, symbol: str, timeframe: str) -> ActiveTradingPair | None:
        if self._trigger_set.symbol != symbol.upper() or self._trigger_set.timeframe != timeframe:
            return None
        return ActiveTradingPair(
            trigger_set=self._trigger_set,
            rules_version=self._rules,
            activated_at=None,
            source_research_id=None,
        )

    def list_testing_sets(self, symbol: str, timeframe: str) -> tuple[TriggerSetVersion, ...]:
        return ()

    def resolve_trigger_version(self, trigger_set: TriggerSetVersion, trigger_id: str) -> RuleDefinition:
        versions = [version for rule_id, version in trigger_set.rule_versions if rule_id == trigger_id]
        if not versions:
            raise TriggerSetStoreError(f"trigger set does not include exact trigger version: {trigger_id}")
        if len(versions) > 1:
            raise TriggerSetStoreError(f"trigger set has ambiguous trigger version: {trigger_id}")
        version = versions[0]
        return RuleDefinition(
            rule_id=trigger_id,
            version=version,
            name=trigger_id,
            status=RuleStatus.ACTIVE,
            asset_scope=trigger_set.symbol,
            rule_type=RuleType.TRIGGER,
            condition=f"exact pinned Research Demo trigger {trigger_id}@{version}",
            definition={"source": "research_demo_exact_pinned_config"},
            created_at=trigger_set.created_at,
            provenance="postgres_research_configuration_registry",
            semantic_hash="POSTGRES_PINNED_TRIGGER_VERSION",
        )


class _ExactResearchDemoTradingRulesStore:
    def __init__(self, rules: TradingRulesVersion) -> None:
        self._rules = rules

    def bootstrap_initial(self, *args, before_commit=None, **kwargs) -> TradingRulesVersion:
        if before_commit is not None:
            before_commit(self._rules)
        return self._rules

    def get_current(self) -> TradingRulesVersion:
        return self._rules

    def get_version(self, rules_version_id_or_version: str) -> TradingRulesVersion | None:
        if rules_version_id_or_version in {self._rules.rules_version_id, self._rules.version}:
            return self._rules
        return None

    def list_versions(self, *, limit: int | None = None) -> tuple[TradingRulesVersion, ...]:
        return (self._rules,)

    def record_usage(self, usage) -> bool:
        return False


class _ResearchDemoExecutionStore:
    def __init__(self, *, inner, trigger_set_id: str, trigger_set_version: str) -> None:
        self._inner = inner
        self._trigger_set_id = trigger_set_id
        self._trigger_set_version = trigger_set_version

    def reserve(self, record):
        self._require_scope(record)
        return self._inner.reserve(record)

    def update(self, record):
        self._require_scope(record)
        return self._inner.update(record)

    def get_by_intent(self, intent_id: str, conn=None):
        record = self._inner.get_by_intent(intent_id, conn) if conn is not None else self._inner.get_by_intent(intent_id)
        return record if self._belongs(record) else None

    def get_by_client_order_id(self, client_order_id: str):
        record = self._inner.get_by_client_order_id(client_order_id)
        return record if self._belongs(record) else None

    def unresolved(self) -> tuple[Any, ...]:
        return tuple(record for record in self._inner.unresolved() if self._belongs(record))

    def list_recent(self, limit: int = 20):
        rows = tuple(record for record in self._inner.list_recent(limit=limit) if self._belongs(record))
        return rows[:limit]

    def __getattr__(self, name: str):
        return getattr(self._inner, name)

    def _require_scope(self, record) -> None:
        if not self._belongs(record):
            raise PostgresPersistenceError("research demo execution evidence escaped scoped runtime")

    def _belongs(self, record) -> bool:
        if record is None:
            return False
        return (
            str(getattr(record, "trigger_set_id", "") or "") == self._trigger_set_id
            and str(getattr(record, "trigger_set_version", "") or "") == self._trigger_set_version
        )


class _ResearchDemoPositionStore:
    def __init__(self, *, inner, trigger_set_id: str, trigger_set_version: str, rules_version_id: str) -> None:
        self._inner = inner
        self._trigger_set_id = trigger_set_id
        self._trigger_set_version = trigger_set_version
        self._rules_version_id = rules_version_id

    def save_open_position(self, record):
        self._require_scope(record)
        return self._inner.save_open_position(record)

    def get_position(self, position_id: str, conn=None):
        record = self._inner.get_position(position_id, conn) if conn is not None else self._inner.get_position(position_id)
        return record if self._belongs(record) else None

    def open_position_for_symbol(self, symbol: str, conn=None):
        del conn
        normalized = symbol.upper()
        return next((record for record in self.list_open_positions(include_unknown=True) if record.symbol == normalized), None)

    def list_open_positions(self, *, include_unknown: bool = False) -> tuple[Any, ...]:
        return tuple(record for record in self._inner.list_open_positions(include_unknown=include_unknown) if self._belongs(record))

    def open_position_count(self) -> int:
        return len(self.list_open_positions())

    def total_open_notional(self) -> Decimal:
        return sum((Decimal(row.position_value) for row in self.list_open_positions()), Decimal("0"))

    def has_unresolved_for_symbol(self, symbol: str) -> bool:
        return self.open_position_for_symbol(symbol) is not None

    def mark_closing(self, position_id: str, close_intent_id: str, close_risk_decision_id: str, close_reason: str):
        current = self._require_existing(position_id)
        updated = self._inner.mark_closing(current.position_id, close_intent_id, close_risk_decision_id, close_reason)
        self._require_scope(updated)
        return updated

    def mark_open(self, position_id: str, updated_at: str):
        current = self._require_existing(position_id)
        updated = self._inner.mark_open(current.position_id, updated_at)
        self._require_scope(updated)
        return updated

    def update_open_fill(self, position_id: str, **kwargs):
        current = self._require_existing(position_id)
        updated = self._inner.update_open_fill(current.position_id, **kwargs)
        self._require_scope(updated)
        return updated

    def attach_close_execution(self, position_id: str, close_execution_id: str):
        current = self._require_existing(position_id)
        updated = self._inner.attach_close_execution(current.position_id, close_execution_id)
        self._require_scope(updated)
        return updated

    def mark_closed(self, position_id: str, closed_at: str):
        current = self._require_existing(position_id)
        updated = self._inner.mark_closed(current.position_id, closed_at)
        self._require_scope(updated)
        return updated

    def __getattr__(self, name: str):
        return getattr(self._inner, name)

    def _require_existing(self, position_id: str):
        record = self.get_position(position_id)
        if record is None:
            raise PostgresPersistenceError("research demo position escaped scoped runtime")
        return record

    def _require_scope(self, record) -> None:
        if not self._belongs(record):
            raise PostgresPersistenceError("research demo position escaped scoped runtime")

    def _belongs(self, record) -> bool:
        if record is None:
            return False
        rules_version_id = getattr(record, "rules_version_id", None)
        return (
            str(getattr(record, "trigger_set_id", "") or "") == self._trigger_set_id
            and str(getattr(record, "trigger_set_version", "") or "") == self._trigger_set_version
            and (rules_version_id is None or str(rules_version_id) == self._rules_version_id)
        )


def _runtime_scoped_trigger_set(trigger_set: TriggerSetVersion, *, demo_run_id: str) -> TriggerSetVersion:
    return replace(trigger_set, version=_scoped_runtime_version(demo_run_id, trigger_set.version))


def _scoped_runtime_version(demo_run_id: str, version: str) -> str:
    return f"{demo_run_id}::{version}"


def _unscoped_runtime_version(demo_run_id: str, version: str) -> str:
    prefix = f"{demo_run_id}::"
    return version[len(prefix):] if version.startswith(prefix) else version


class _ResearchDemoRuntimeStore:
    def __init__(self, inner, *, demo_run_id: str) -> None:
        self._inner = inner
        self._demo_run_id = demo_run_id

    def save_market_regime(self, context) -> None:
        self._inner.save_market_regime(context)

    def get_lane_lifecycle(self, **kwargs):
        scoped = self._scope_kwargs(kwargs)
        lifecycle = self._inner.get_lane_lifecycle(**scoped)
        return None if lifecycle is None else self._unscope_lifecycle(lifecycle)

    def save_lane_lifecycle(self, lifecycle) -> None:
        self._inner.save_lane_lifecycle(self._scope_lifecycle(lifecycle))

    def lane_processed_count(self, **kwargs) -> int:
        return self._inner.lane_processed_count(**self._scope_kwargs(kwargs))

    def lane_checkpoint(self, checkpoint) -> None:
        self._inner.lane_checkpoint(self._scope_checkpoint(checkpoint))

    def get_lane_checkpoint(self, **kwargs):
        checkpoint = self._inner.get_lane_checkpoint(**self._scope_kwargs(kwargs))
        return None if checkpoint is None else self._unscope_checkpoint(checkpoint)

    def record_heartbeat(self, heartbeat: RuntimeHeartbeat) -> RuntimeHeartbeat:
        scoped = replace(
            heartbeat,
            component=f"research-demo:{self._demo_run_id}:{heartbeat.component}",
            metadata={**(heartbeat.metadata or {}), "research_demo_run_id": self._demo_run_id},
        )
        return self._inner.record_heartbeat(scoped)

    def _scope_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        scoped = dict(kwargs)
        scoped["trigger_set_version"] = self._scope_version(str(scoped["trigger_set_version"]))
        return scoped

    def _scope_lifecycle(self, lifecycle):
        return replace(lifecycle, trigger_set_version=self._scope_version(lifecycle.trigger_set_version))

    def _unscope_lifecycle(self, lifecycle):
        return replace(lifecycle, trigger_set_version=self._unscope_version(lifecycle.trigger_set_version))

    def _scope_checkpoint(self, checkpoint):
        return replace(checkpoint, trigger_set_version=self._scope_version(checkpoint.trigger_set_version))

    def _unscope_checkpoint(self, checkpoint):
        return replace(checkpoint, trigger_set_version=self._unscope_version(checkpoint.trigger_set_version))

    def _scope_version(self, version: str) -> str:
        return _scoped_runtime_version(self._demo_run_id, version)

    def _unscope_version(self, version: str) -> str:
        return _unscoped_runtime_version(self._demo_run_id, version)


class _ResearchDemoAccountingStore:
    def __init__(
        self,
        *,
        inner,
        factory: PostgresConnectionFactory,
        demo_run_id: str,
        set_id: str,
        set_version: str,
    ) -> None:
        self._inner = inner
        self._factory = factory
        self._demo_run_id = demo_run_id
        self._set_id = set_id
        self._set_version = set_version

    def record_closed_trade(self, result) -> bool:
        created = self._inner.record_closed_trade(result)
        payload = {
            "trade_id": result.trade_id,
            "research_demo_run_id": self._demo_run_id,
            "execution_owner": RESEARCH_DEMO_CONSUMER,
            "research_demo_result_scope": "RESEARCH_DEMO",
            "trigger_set_id": self._set_id,
            "trigger_set_version": self._set_version,
            "runtime_trigger_set_version": result.trigger_set_version,
            "evidence_source": result.evidence_source,
        }
        with PostgresUnitOfWork(self._factory) as uow:
            record, _ = OwnerStateStore(uow.connection).put_if_absent(
                owner=RESEARCH_DEMO_OWNER,
                state_type="research_demo_closed_trade_attribution",
                state_id=str(result.trade_id),
                payload=payload,
            )
            if record.payload != payload:
                raise PostgresPersistenceError("research demo closed-trade attribution conflict")
        return created

    def record_equity_snapshot(self, snapshot) -> bool:
        created = self._inner.record_equity_snapshot(snapshot)
        payload = {
            "snapshot_id": snapshot.snapshot_id,
            "research_demo_run_id": self._demo_run_id,
            "execution_owner": RESEARCH_DEMO_CONSUMER,
            "research_demo_result_scope": "RESEARCH_DEMO",
            "observed_at": snapshot.observed_at,
            "source": snapshot.source,
            "wallet_balance": str(snapshot.wallet_balance),
            "equity": str(snapshot.equity),
            "available_margin": str(snapshot.available_margin),
            "used_margin": str(snapshot.used_margin),
            "unrealized_pnl": str(snapshot.unrealized_pnl),
            "realized_pnl": str(snapshot.realized_pnl),
            "running_peak": str(snapshot.running_peak),
            "drawdown_absolute": str(snapshot.drawdown_absolute),
            "drawdown_percent": str(snapshot.drawdown_percent),
            "max_drawdown": str(snapshot.max_drawdown),
            "accounting_version": snapshot.accounting_version,
        }
        with PostgresUnitOfWork(self._factory) as uow:
            record, _ = OwnerStateStore(uow.connection).put_if_absent(
                owner=RESEARCH_DEMO_OWNER,
                state_type="research_demo_equity_snapshot_attribution",
                state_id=str(snapshot.snapshot_id),
                payload=payload,
            )
            if record.payload != payload:
                raise PostgresPersistenceError("research demo equity snapshot attribution conflict")
        return created

    def list_closed_trades(self, limit: int = 20) -> tuple[dict[str, Any], ...]:
        return self._inner.list_closed_trades(limit=limit)

    def realized_net_pnl_for_utc_day(self, trading_day: str) -> Decimal:
        start, end = _utc_day_bounds(trading_day)
        attributed = _attributed_trades(factory=self._factory, demo_run_id=self._demo_run_id)
        return sum(
            (
                _decimal(row.get("net_pnl"))
                for row in self._inner.list_closed_trades(limit=10000)
                if start <= str(row.get("closed_at") or "") < end
                and _row_belongs_to_research_demo(
                    row,
                    attributed=attributed,
                    demo_run_id=self._demo_run_id,
                    set_id=self._set_id,
                    set_version=self._set_version,
                )
            ),
            Decimal("0"),
        )

    def first_equity_snapshot_for_utc_day(self, trading_day: str) -> dict[str, Any] | None:
        start, end = _utc_day_bounds(trading_day)
        snapshots = [
            snapshot
            for snapshot in _attributed_equity_snapshots(factory=self._factory, demo_run_id=self._demo_run_id)
            if start <= str(snapshot.get("observed_at") or "") < end
        ]
        if not snapshots:
            return None
        return sorted(snapshots, key=lambda item: (str(item.get("observed_at") or ""), str(item.get("snapshot_id") or "")))[0]

    def latest_equity_snapshot(self) -> dict[str, Any] | None:
        snapshots = tuple(_attributed_equity_snapshots(factory=self._factory, demo_run_id=self._demo_run_id))
        if not snapshots:
            return None
        return sorted(
            snapshots,
            key=lambda item: (str(item.get("observed_at") or ""), str(item.get("snapshot_id") or "")),
            reverse=True,
        )[0]

    def __getattr__(self, name: str):
        return getattr(self._inner, name)


class _PostgresResearchDemoTraceStore:
    def __init__(self, factory: PostgresConnectionFactory, *, demo_run_id: str) -> None:
        self._factory = factory
        self._demo_run_id = demo_run_id
        self.audit_events_recorded = 0

    def save_trigger_evaluation(self, signal) -> None:
        self._put(
            state_type="research_demo_trigger_evaluation",
            state_id=str(signal.signal_id),
            payload={
                "demo_run_id": self._demo_run_id,
                "signal_id": signal.signal_id,
                "trigger_rule_id": signal.trigger_rule_id,
                "trigger_rule_version": signal.trigger_rule_version,
                "symbol": signal.symbol,
                "observed_at": signal.observed_at,
                "window": signal.window,
                "input_snapshot": dict(signal.input_snapshot),
                "condition_result": signal.condition_result,
                "signal_type": signal.signal_type.value,
                "lane": signal.lane,
                "trigger_set_id": signal.trigger_set_id,
                "trigger_set_version": signal.trigger_set_version,
            },
        )

    def save_futures_strategy_decision(self, intent, signal_ids: tuple[str, ...]) -> None:
        self._put(
            state_type="research_demo_strategy_decision",
            state_id=str(intent.intent_id),
            payload={
                "demo_run_id": self._demo_run_id,
                "intent_id": intent.intent_id,
                "symbol": intent.symbol,
                "action": intent.action.value,
                "signal_ids": tuple(signal_ids),
                "created_at": intent.created_at,
                "lane": intent.lane,
                "trigger_set_id": intent.trigger_set_id,
                "trigger_set_version": intent.trigger_set_version,
                "rules_version_id": intent.rules_version_id,
            },
        )

    def save_futures_risk_decision(self, decision, *, trigger_set_id: str | None = None, trigger_set_version: str | None = None) -> None:
        self._put(
            state_type="research_demo_risk_decision",
            state_id=str(decision.risk_decision_id),
            payload={
                "demo_run_id": self._demo_run_id,
                "risk_decision_id": decision.risk_decision_id,
                "intent_id": decision.intent_id,
                "approved": decision.approved,
                "checked_rule_ids": tuple(decision.checked_rule_ids),
                "blocking_rule_ids": tuple(decision.blocking_rule_ids),
                "rejection_reason": decision.rejection_reason,
                "created_at": decision.created_at,
                "lane": decision.lane,
                "trigger_set_id": trigger_set_id,
                "trigger_set_version": trigger_set_version,
            },
        )

    def record_audit_event(self, **kwargs):
        event_id = str(kwargs.get("event_id") or canonical_json_digest({"demo_run_id": self._demo_run_id, **kwargs}))
        payload = {"demo_run_id": self._demo_run_id, **kwargs, "event_id": event_id}
        self._put(state_type="research_demo_audit_event", state_id=event_id, payload=payload)
        self.audit_events_recorded += 1
        return type("AuditEvent", (), payload)()

    def _put(self, *, state_type: str, state_id: str, payload: dict[str, Any]) -> None:
        scoped_state_id = f"{self._demo_run_id}::{state_id}"
        with PostgresUnitOfWork(self._factory) as uow:
            store = OwnerStateStore(uow.connection)
            existing = store.get(owner=RESEARCH_DEMO_OWNER, state_type=state_type, state_id=scoped_state_id)
            if existing is None:
                store.put_if_absent(owner=RESEARCH_DEMO_OWNER, state_type=state_type, state_id=scoped_state_id, payload=payload)
            elif existing.payload != payload:
                raise PostgresPersistenceError("research demo trace evidence conflict")


class _PostgresResearchDemoDailyLossStore:
    def __init__(self, factory: PostgresConnectionFactory, *, demo_run_id: str) -> None:
        self._factory = factory
        self._demo_run_id = demo_run_id

    def get_record(self, trading_day: str) -> DailyLossRecord | None:
        with PostgresUnitOfWork(self._factory) as uow:
            record = OwnerStateStore(uow.connection).get(
                owner=RESEARCH_DEMO_OWNER,
                state_type="research_demo_daily_loss",
                state_id=self._state_id(trading_day),
            )
        return None if record is None else _daily_loss_record_from_payload(record.payload)

    def ensure_baseline(
        self,
        *,
        trading_day: str,
        baseline_equity: Decimal,
        baseline_source: str,
        baseline_observed_at: str,
        updated_at: str,
    ) -> DailyLossRecord:
        payload = {
            "trading_day": trading_day,
            "baseline_equity": str(baseline_equity),
            "baseline_source": baseline_source,
            "baseline_observed_at": baseline_observed_at,
            "latched": False,
            "latched_at": None,
            "latched_rules_version_id": None,
            "latched_reason": None,
            "notified_at": None,
            "updated_at": updated_at,
        }
        with PostgresUnitOfWork(self._factory) as uow:
            record, _ = OwnerStateStore(uow.connection).put_if_absent(
                owner=RESEARCH_DEMO_OWNER,
                state_type="research_demo_daily_loss",
                state_id=self._state_id(trading_day),
                payload=payload,
            )
        return _daily_loss_record_from_payload(record.payload)

    def latch(self, *, trading_day: str, latched_at: str, rules_version_id: str, reason: str) -> DailyLossRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            store = OwnerStateStore(uow.connection)
            state_id = self._state_id(trading_day)
            current = store.get(owner=RESEARCH_DEMO_OWNER, state_type="research_demo_daily_loss", state_id=state_id)
            if current is None:
                raise PostgresPersistenceError("daily loss latch requires baseline")
            payload = {
                **current.payload,
                "latched": True,
                "latched_at": current.payload.get("latched_at") or latched_at,
                "latched_rules_version_id": current.payload.get("latched_rules_version_id") or rules_version_id,
                "latched_reason": current.payload.get("latched_reason") or reason,
                "updated_at": latched_at,
            }
            updated = store.compare_and_set(
                owner=RESEARCH_DEMO_OWNER,
                state_type="research_demo_daily_loss",
                state_id=state_id,
                expected_revision=current.revision,
                payload=payload,
            )
        return _daily_loss_record_from_payload(updated.payload)

    def mark_notified(self, *, trading_day: str, notified_at: str) -> DailyLossRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            store = OwnerStateStore(uow.connection)
            state_id = self._state_id(trading_day)
            current = store.get(owner=RESEARCH_DEMO_OWNER, state_type="research_demo_daily_loss", state_id=state_id)
            if current is None:
                raise PostgresPersistenceError("daily loss notification requires baseline")
            payload = {**current.payload, "notified_at": current.payload.get("notified_at") or notified_at, "updated_at": notified_at}
            updated = store.compare_and_set(
                owner=RESEARCH_DEMO_OWNER,
                state_type="research_demo_daily_loss",
                state_id=state_id,
                expected_revision=current.revision,
                payload=payload,
            )
        return _daily_loss_record_from_payload(updated.payload)

    def _state_id(self, trading_day: str) -> str:
        return f"{self._demo_run_id}::{trading_day}"


class _PostgresResearchDemoMessageStore:
    def __init__(self, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def create_message(self, **kwargs) -> MessageRecord:
        created_at = str(kwargs.get("created_at") or datetime.now(UTC).isoformat())
        dedupe_key = kwargs.get("dedupe_key")
        message_id = "research-demo-msg-" + sha256(str(dedupe_key or canonical_json_digest(kwargs)).encode("utf-8")).hexdigest()[:32]
        severity = MessageSeverity(str(kwargs.get("severity") or kwargs.get("type") or MessageSeverity.INFO.value))
        payload = {
            "message_id": message_id,
            "created_at": created_at,
            "type": str(kwargs.get("type") or severity.value).upper(),
            "severity": severity.value,
            "title": kwargs.get("title"),
            "body": str(kwargs.get("body") or ""),
            "source": str(kwargs.get("source") or "research_demo"),
            "entity_type": kwargs.get("entity_type"),
            "entity_id": kwargs.get("entity_id"),
            "is_read": False,
            "read_at": None,
            "dedupe_key": dedupe_key,
            "expires_at": kwargs.get("expires_at"),
            "metadata": dict(kwargs.get("metadata") or {}),
        }
        with PostgresUnitOfWork(self._factory) as uow:
            record, _ = OwnerStateStore(uow.connection).put_if_absent(
                owner=RESEARCH_DEMO_OWNER,
                state_type="research_demo_message",
                state_id=message_id,
                payload=payload,
            )
        return _message_record_from_payload(record.payload)


def _configuration_identity(configuration) -> dict[str, str]:
    return {
        "research_id": configuration.research.research_id,
        "set_id": configuration.trigger_set.set_id,
        "set_version": configuration.trigger_set.version,
        "rules_version_id": configuration.rules.rules_version_id,
    }


def _runtime_result_payload(result: FuturesDualLaneResult) -> dict[str, Any]:
    return {
        "candle_id": result.candle_id,
        "skipped_reason": result.skipped_reason,
        "active": tuple(_cycle_result_payload(item) for item in result.active),
        "test": tuple(_cycle_result_payload(item) for item in result.test),
    }


def _cycle_result_payload(result) -> dict[str, Any]:
    return {
        "candle_id": result.candle_id,
        "signal_type": result.signal_type,
        "intent_id": result.intent_id,
        "risk_decision_id": result.risk_decision_id,
        "risk_approved": result.risk_approved,
        "execution_status": result.execution_status,
        "skipped_reason": result.skipped_reason,
    }


def _canonical_runtime_wait_state(result: FuturesDualLaneResult, active_payloads: tuple[dict[str, Any], ...]) -> bool:
    if result.skipped_reason == "no_completed_candle":
        return True
    return bool(active_payloads) and all(item["skipped_reason"] == "already_processed" for item in active_payloads)


def _daily_loss_record_from_payload(payload: dict[str, Any]) -> DailyLossRecord:
    return DailyLossRecord(
        trading_day=_required_text(payload.get("trading_day"), field="trading_day"),
        baseline_equity=Decimal(str(payload.get("baseline_equity") or "0")),
        baseline_source=_required_text(payload.get("baseline_source"), field="baseline_source"),
        baseline_observed_at=_required_text(payload.get("baseline_observed_at"), field="baseline_observed_at"),
        latched=bool(payload.get("latched")),
        latched_at=_optional_payload_text(payload.get("latched_at")),
        latched_rules_version_id=_optional_payload_text(payload.get("latched_rules_version_id")),
        latched_reason=_optional_payload_text(payload.get("latched_reason")),
        notified_at=_optional_payload_text(payload.get("notified_at")),
        updated_at=_required_text(payload.get("updated_at"), field="updated_at"),
    )


def _message_record_from_payload(payload: dict[str, Any]) -> MessageRecord:
    return MessageRecord(
        message_id=_required_text(payload.get("message_id"), field="message_id"),
        created_at=_required_text(payload.get("created_at"), field="created_at"),
        type=_required_text(payload.get("type"), field="message_type"),
        severity=MessageSeverity(str(payload.get("severity") or MessageSeverity.INFO.value)),
        title=_optional_payload_text(payload.get("title")),
        body=str(payload.get("body") or ""),
        source=str(payload.get("source") or "research_demo"),
        entity_type=_optional_payload_text(payload.get("entity_type")),
        entity_id=_optional_payload_text(payload.get("entity_id")),
        is_read=bool(payload.get("is_read")),
        read_at=_optional_payload_text(payload.get("read_at")),
        dedupe_key=_optional_payload_text(payload.get("dedupe_key")),
        expires_at=_optional_payload_text(payload.get("expires_at")),
        metadata=dict(payload.get("metadata") or {}),
    )


def _progress(*, record: ResearchDemoExecutionRecord, now: datetime) -> dict[str, Any]:
    started_at = _parse_time(record.started_at or record.requested_at)
    elapsed = max(now.astimezone(UTC) - started_at, timedelta(0))
    duration = timedelta(days=DEMO_DURATION_DAYS)
    elapsed_seconds = int(elapsed.total_seconds())
    duration_seconds = int(duration.total_seconds())
    return {
        "duration_days": DEMO_DURATION_DAYS,
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "observed_at": now.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "elapsed_seconds": elapsed_seconds,
        "duration_seconds": duration_seconds,
        "duration_elapsed": elapsed >= duration,
        "factual_progress_source": "canonical_research_demo_owner_state",
    }


def _project_result_from_accounting(
    *,
    accounting_store: ResearchDemoAccountingProjection,
    factory: PostgresConnectionFactory | None = None,
    demo_run_id: str,
    set_id: str,
    set_version: str,
) -> dict[str, Any]:
    attributed = _attributed_trades(factory=factory, demo_run_id=demo_run_id)
    rows = tuple(
        row
        for row in accounting_store.list_closed_trades(limit=10000)
        if _row_belongs_to_research_demo(
            row,
            attributed=attributed,
            demo_run_id=demo_run_id,
            set_id=set_id,
            set_version=set_version,
        )
    )
    net_values = [_decimal(row.get("net_pnl")) for row in rows]
    gross_values = [_decimal(row.get("gross_pnl")) for row in rows]
    wins = sum(1 for value in net_values if value > 0)
    losses = [abs(value) for value in net_values if value < 0]
    gains = [value for value in net_values if value > 0]
    profit_factor = None if not losses else str(sum(gains, Decimal("0")) / sum(losses, Decimal("0")))
    return {
        "source": "canonical_futures_accounting",
        "trades": len(rows),
        "net_pnl": str(sum(net_values, Decimal("0"))),
        "gross_pnl": str(sum(gross_values, Decimal("0"))),
        "win_rate": None if not rows else str(Decimal(wins) / Decimal(len(rows))),
        "profit_factor": profit_factor,
        "unavailable": () if rows else ("no_closed_trade_facts",),
    }


def _row_belongs_to_research_demo(
    row: dict[str, Any],
    *,
    attributed: dict[str, dict[str, Any]],
    demo_run_id: str,
    set_id: str,
    set_version: str,
) -> bool:
    trade_id = str(row.get("trade_id") or "")
    attribution = attributed.get(trade_id)
    if attribution is not None:
        return (
            str(attribution.get("research_demo_run_id") or "") == demo_run_id
            and str(attribution.get("execution_owner") or "") == RESEARCH_DEMO_CONSUMER
            and str(attribution.get("research_demo_result_scope") or "") == "RESEARCH_DEMO"
            and str(attribution.get("trigger_set_id") or "") == set_id
            and str(attribution.get("trigger_set_version") or "") == set_version
            and str(attribution.get("evidence_source") or row.get("evidence_source") or "").upper()
            in {"ACTIVE", "EXCHANGE", "BYBIT_DEMO_ACCOUNT"}
        )
    return (
        str(row.get("research_demo_run_id") or "") == demo_run_id
        and str(row.get("execution_owner") or "") == RESEARCH_DEMO_CONSUMER
        and str(row.get("research_demo_result_scope") or "") == "RESEARCH_DEMO"
        and str(row.get("trigger_set_id") or "") == set_id
        and str(row.get("trigger_set_version") or "") == set_version
        and str(row.get("evidence_source") or "").upper() in {"ACTIVE", "EXCHANGE", "BYBIT_DEMO_ACCOUNT"}
    )


def _attributed_trades(*, factory: PostgresConnectionFactory | None, demo_run_id: str) -> dict[str, dict[str, Any]]:
    if factory is None or not isinstance(factory, PostgresConnectionFactory):
        return {}
    try:
        with PostgresUnitOfWork(factory) as uow:
            with uow.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT state_id, payload_json::text
                    FROM triggertrade_owner_state_records
                    WHERE owner = %s
                      AND state_type = %s
                      AND payload_json->>'research_demo_run_id' = %s
                      AND payload_json->>'execution_owner' = %s
                      AND payload_json->>'research_demo_result_scope' = %s
                    """,
                    (
                        RESEARCH_DEMO_OWNER,
                        "research_demo_closed_trade_attribution",
                        demo_run_id,
                        RESEARCH_DEMO_CONSUMER,
                        "RESEARCH_DEMO",
                    ),
                )
                rows = cursor.fetchall()
    except Exception as exc:
        raise PostgresPersistenceError("research demo closed-trade attribution query failed") from exc
    import json

    return {str(row[0]): dict(json.loads(str(row[1]))) for row in rows}


def _attributed_equity_snapshots(*, factory: PostgresConnectionFactory | None, demo_run_id: str) -> tuple[dict[str, Any], ...]:
    if factory is None or not isinstance(factory, PostgresConnectionFactory):
        return ()
    try:
        with PostgresUnitOfWork(factory) as uow:
            with uow.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT payload_json::text
                    FROM triggertrade_owner_state_records
                    WHERE owner = %s
                      AND state_type = %s
                      AND payload_json->>'research_demo_run_id' = %s
                      AND payload_json->>'execution_owner' = %s
                      AND payload_json->>'research_demo_result_scope' = %s
                    """,
                    (
                        RESEARCH_DEMO_OWNER,
                        "research_demo_equity_snapshot_attribution",
                        demo_run_id,
                        RESEARCH_DEMO_CONSUMER,
                        "RESEARCH_DEMO",
                    ),
                )
                rows = cursor.fetchall()
    except Exception as exc:
        raise PostgresPersistenceError("research demo equity snapshot attribution query failed") from exc
    import json

    return tuple(dict(json.loads(str(row[0]))) for row in rows)


def _utc_day_bounds(trading_day: str) -> tuple[str, str]:
    start = datetime.fromisoformat(f"{trading_day}T00:00:00+00:00").astimezone(UTC)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def _parse_time(value: str) -> datetime:
    text = _required_text(value, field="timestamp").replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _optional_payload_text(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _decimal(value: object) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except (InvalidOperation, DivisionByZero) as exc:
        raise PostgresPersistenceError("canonical accounting projection contains invalid decimal") from exc


def _require_canonical_cycle_evidence(cycle_result: dict[str, Any]) -> None:
    unresolved = int(cycle_result.get("unresolved_obligations") or 0)
    if bool(cycle_result.get("canonical_runtime_wait_state")) and unresolved == 0:
        if not bool(cycle_result.get("reconciliation_before_resubmit")):
            raise PostgresPersistenceError(
                "research_demo_canonical_execution_cycle_unavailable:reconciliation_before_resubmit"
            )
        return
    required = (
        "canonical_trading_decisions_invoked",
        "canonical_lifecycle_invoked",
        "reconciliation_before_resubmit",
    )
    missing = [name for name in required if not bool(cycle_result.get(name))]
    if unresolved > 0 and not bool(cycle_result.get("canonical_futures_execution_invoked")):
        missing.append("canonical_futures_execution_invoked")
    if missing:
        raise PostgresPersistenceError(
            "research_demo_canonical_execution_cycle_unavailable:"
            + ",".join(missing)
        )


def _message_id(demo_run_id: str) -> str:
    return f"research-demo-start-{sha256(demo_run_id.encode('utf-8')).hexdigest()[:32]}"


def _recheck_message_id(record: ResearchDemoExecutionRecord) -> str:
    source = f"{record.demo_run_id}\x1f{record.revision}\x1f{record.status}"
    return f"research-demo-recheck-{sha256(source.encode('utf-8')).hexdigest()[:32]}"


def _required_text(value: object, *, field: str) -> str:
    raw = str(value or "").strip()
    if not raw or "\x00" in raw or len(raw) > 240:
        raise PostgresPersistenceError(f"{field} must be a non-empty stable string")
    return raw


def _optional_text(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field=field)


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _public_error(value: object) -> str:
    text = " ".join(str(value).replace("\x00", "").split())[:500]
    lowered = text.lower()
    if any(token in lowered for token in ("secret", "api_key", "authorization", "bearer", "token", "password")):
        return "[redacted]"
    return text or "research_demo_execution_failed"
