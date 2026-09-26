"""Durable Research Backtest execution handoff and worker dispatch."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol

from triggertrade.backtest import BacktestPlan, ExactBacktestTriggerSetResolver, run_backtest
from triggertrade.backtest.data import HistoricalDataError
from triggertrade.backtest.engine import BacktestEngineError
from triggertrade.backtest.models import BACKTEST_DATA_SOURCE_VERSION
from triggertrade.config import AppConfig
from triggertrade.market_data import FuturesInstrumentMetadata
from triggertrade.persistence.durable_messages import DurableMessageStore
from triggertrade.persistence.postgres import PostgresConnectionFactory, PostgresPersistenceError, PostgresUnitOfWork
from triggertrade.persistence.postgres_research_registry import (
    PostgresResearchConfigurationRegistry,
    PostgresResearchRunStore,
)
from triggertrade.persistence.research_store import ResearchBacktestRunRecord, ResearchBacktestStatus, ResearchRecord
from triggertrade.rules import TradingRulesVersion
from triggertrade.services.research import ResearchBacktestExecutionHandoffResult, _backtest_metrics
from triggertrade.services.runtime import interval_delta
from triggertrade.trigger_sets import TriggerSetVersion


RESEARCH_BACKTEST_PRODUCER = "Research"
RESEARCH_BACKTEST_CONSUMER = "ResearchBacktestExecution"
RESEARCH_BACKTEST_MESSAGE_TYPE = "RESEARCH_BACKTEST_START"
RESEARCH_BACKTEST_MESSAGE_VERSION = "1"


class HistoricalReplaySource(Protocol):
    def load(self, *, symbol: str, category: str, timeframe: str, start: datetime, end: datetime, use_cache: bool = True): ...


class BacktestInstrumentProvider(Protocol):
    def __call__(self, symbol: str) -> FuturesInstrumentMetadata: ...


class ResearchBacktestExecutionExecutor(Protocol):
    canonical_research_backtest_executor: bool

    def start_research_backtest(self, record: ResearchBacktestRunRecord) -> ResearchBacktestRunRecord: ...


class PostgresResearchBacktestExecutionHandoff:
    """Web-side ingress that persists Research Backtest work for the trading worker."""

    canonical_worker_handoff = True

    def __init__(self, *, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def start_research_backtest(
        self,
        *,
        research: ResearchRecord,
        trigger_set: TriggerSetVersion,
        rules: TradingRulesVersion,
        plan: BacktestPlan,
        created_at: str,
        pin_payload: dict[str, Any],
    ) -> ResearchBacktestExecutionHandoffResult:
        with PostgresUnitOfWork(self._factory) as uow:
            PostgresResearchConfigurationRegistry(uow.connection).put_configuration(
                research=research,
                trigger_set=trigger_set,
                rules=rules,
            )
            record = PostgresResearchRunStore(uow.connection).add_backtest_run(
                research_id=research.research_id,
                period_start=plan.research_start.astimezone(UTC).isoformat(),
                period_end=plan.research_end.astimezone(UTC).isoformat(),
                timeframe=plan.timeframe,
                status=ResearchBacktestStatus.RUNNING,
                metrics={},
                unavailable_reason=None,
                pin_payload=pin_payload,
                created_at=created_at,
            )
            DurableMessageStore(uow.connection).append_outbox(
                message_id=_message_id(record.run_id),
                producer=RESEARCH_BACKTEST_PRODUCER,
                consumer=RESEARCH_BACKTEST_CONSUMER,
                message_type=RESEARCH_BACKTEST_MESSAGE_TYPE,
                message_version=RESEARCH_BACKTEST_MESSAGE_VERSION,
                payload={"research_backtest": {"research_id": record.research_id, "run_id": record.run_id}},
                aggregate_id=record.research_id,
                causation_id=record.run_id,
                correlation_id=record.run_id,
                dedupe_key=f"RESEARCH_BACKTEST_START:{record.run_id}",
            )
        return ResearchBacktestExecutionHandoffResult(
            handoff_id=_message_id(record.run_id),
            execution_owner="trading-worker",
            durable=True,
            record=record,
        )


class CanonicalResearchBacktestExecutionExecutor:
    """Trading-worker owned Research Backtest executor over canonical Postgres state."""

    canonical_research_backtest_executor = True

    def __init__(
        self,
        *,
        config: AppConfig,
        db_path: str | Path,
        factory: PostgresConnectionFactory,
        historical_source: HistoricalReplaySource,
        instrument_provider: BacktestInstrumentProvider,
    ) -> None:
        self._config = config
        self._db_path = Path(db_path)
        self._factory = factory
        self._historical_source = historical_source
        self._instrument_provider = instrument_provider

    def start_research_backtest(self, record: ResearchBacktestRunRecord) -> ResearchBacktestRunRecord:
        plan = _plan_from_record(record)
        try:
            with PostgresUnitOfWork(self._factory) as uow:
                registry = PostgresResearchConfigurationRegistry(uow.connection)
                research = registry.get_research(record.research_id)
                if research is None:
                    raise PostgresPersistenceError("research_backtest_research_configuration_missing")
                configuration = registry.get_research_demo_configuration(
                    research_id=record.research_id,
                    set_id=research.set_id,
                    set_version=research.set_version,
                    rules_version_id=research.rules_version_id,
                )
                _validate_authoritative_trigger_set(research=research, trigger_set=configuration.trigger_set)
            replay = self._historical_source.load(
                symbol=plan.symbol,
                category=plan.category,
                timeframe=plan.timeframe,
                start=_historical_replay_load_start(plan),
                end=plan.research_end,
                use_cache=True,
            )
            candles = tuple(replay.candles)
            if not candles:
                return self._mark_failed(record, "backend_historical_replay_inputs_unavailable")
            instrument = self._instrument_provider(plan.symbol)
            result = run_backtest(
                config=self._config,
                db_path=self._db_path,
                trigger_set_id=configuration.trigger_set.set_id,
                trigger_set_version=configuration.trigger_set.version,
                plan=plan,
                candles=candles,
                instrument=instrument,
                trigger_set_store=ExactBacktestTriggerSetResolver(configuration.trigger_set),
            )
            status = ResearchBacktestStatus.COMPLETED if result.closed_trades > 0 else ResearchBacktestStatus.COMPLETED_NO_TRADES
            with PostgresUnitOfWork(self._factory) as uow:
                return PostgresResearchRunStore(uow.connection).update_backtest_run(
                    research_id=record.research_id,
                    run_id=record.run_id,
                    status=status,
                    engine_run_id=result.backtest_run_id,
                    metrics=_backtest_metrics(result),
                    unavailable_reason=None,
                    updated_at=datetime.now(UTC).isoformat(),
                )
        except Exception as exc:  # noqa: BLE001 - worker persists bounded factual failure reason.
            return self._mark_failed(record, _backtest_unavailable_reason(exc))

    def _mark_failed(self, record: ResearchBacktestRunRecord, reason: str) -> ResearchBacktestRunRecord:
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).update_backtest_run(
                research_id=record.research_id,
                run_id=record.run_id,
                status=ResearchBacktestStatus.FAILED,
                engine_run_id=None,
                metrics={},
                unavailable_reason=reason,
                updated_at=datetime.now(UTC).isoformat(),
            )


class ResearchBacktestExecutionDispatcher:
    """Trading-worker side dispatcher for durable Research Backtest handoffs."""

    def __init__(self, *, store: PostgresResearchRunStore, executor: ResearchBacktestExecutionExecutor | None) -> None:
        self._store = store
        self._executor = executor

    def dispatch(self, *, research_id: str, run_id: str) -> str:
        record = self._store.get_backtest_run(research_id, run_id)
        if record is None:
            raise PostgresPersistenceError("research_backtest_execution_state_not_found")
        if record.status in {
            ResearchBacktestStatus.COMPLETED,
            ResearchBacktestStatus.COMPLETED_NO_TRADES,
            ResearchBacktestStatus.FAILED,
        }:
            return f"research_backtest_replay:{record.status.value}"
        if self._executor is None or not getattr(self._executor, "canonical_research_backtest_executor", False):
            raise PostgresPersistenceError("research_backtest_canonical_executor_unavailable")
        updated = self._executor.start_research_backtest(record)
        return f"research_backtest_{updated.status.value.lower()}:{updated.run_id}"


def _plan_from_record(record: ResearchBacktestRunRecord) -> BacktestPlan:
    plan = _run_plan(record)
    return BacktestPlan(
        str(plan.get("symbol") or ""),
        str(plan.get("category") or ""),
        str(plan.get("timeframe") or record.timeframe),
        datetime.fromisoformat(str(plan.get("research_start"))),
        datetime.fromisoformat(str(plan.get("research_end"))),
        warmup_candles=int(plan.get("warmup_candles") or 0),
    )


def _run_plan(record: ResearchBacktestRunRecord) -> dict[str, Any]:
    inputs = record.pin_payload.get("run_inputs")
    if not isinstance(inputs, dict):
        raise PostgresPersistenceError("research_backtest_pin_inputs_missing")
    if inputs.get("historical_source") != BACKTEST_DATA_SOURCE_VERSION:
        raise PostgresPersistenceError("research_backtest_historical_source_mismatch")
    plan = inputs.get("plan")
    if not isinstance(plan, dict):
        raise PostgresPersistenceError("research_backtest_plan_missing")
    return plan


def _historical_replay_load_start(plan: BacktestPlan) -> datetime:
    return plan.research_start.astimezone(UTC) - interval_delta(plan.timeframe) * (plan.warmup_candles + 1)


def _validate_authoritative_trigger_set(*, research: ResearchRecord, trigger_set: TriggerSetVersion) -> None:
    if (research.set_id, research.set_version) != (trigger_set.set_id, trigger_set.version):
        raise PostgresPersistenceError("research_backtest_trigger_set_identity_mismatch")


def _backtest_unavailable_reason(exc: Exception) -> str:
    text = str(exc).lower()
    if isinstance(exc, HistoricalDataError):
        if "empty" in text:
            return "historical_candles_empty"
        if any(token in text for token in ("gap", "boundary", "requested", "start", "end", "warmup")):
            return "historical_window_incomplete"
        return "historical_fetch_failed"
    if "403" in text or "forbidden" in text:
        return "historical_source_geo_blocked"
    if isinstance(exc, BacktestEngineError):
        if "trigger set" in text or "unknown trigger set" in text:
            return "research_trigger_set_unavailable"
        return "backtest_engine_failed"
    if isinstance(exc, PostgresPersistenceError):
        if "trigger_set" in text or "configuration" in text or "research_backtest" in text:
            return "research_configuration_unavailable"
        return "research_persistence_unavailable"
    return "backtest_engine_failed"


def _message_id(run_id: str) -> str:
    digest = sha256(run_id.encode("utf-8")).hexdigest()[:20]
    return f"research-backtest-start-{digest}"
