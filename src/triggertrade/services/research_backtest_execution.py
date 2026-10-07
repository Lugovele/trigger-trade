"""Durable Research Backtest execution handoff and worker dispatch."""

from __future__ import annotations

import json
import csv
import time as monotonic_time
from dataclasses import asdict, dataclass, is_dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol, Sequence

from triggertrade.backtest import BacktestPlan, BacktestResult, BacktestStatus, ExactBacktestTriggerSetResolver, run_backtest
from triggertrade.backtest.data import HistoricalDataError, HistoricalKlineCache, validate_historical_candles
from triggertrade.backtest.engine import BacktestEngineError
from triggertrade.backtest.models import BACKTEST_DATA_SOURCE_VERSION, BACKTEST_EVIDENCE_SOURCE, HistoricalCandle
from triggertrade.canonical_json import canonical_json_digest
from triggertrade.config import AppConfig
from triggertrade.instruments import FuturesInstrument, catalog_hash
from triggertrade.instruments.catalog import with_catalog_hash
from triggertrade.market_data import FuturesInstrumentMetadata
from triggertrade.market_data.raw_trades import (
    BYBIT_PUBLIC_TRADE_ARCHIVE_REVISION,
    build_bybit_archive_raw_trades_response,
    build_last_traded_price_response_from_raw_trades,
    bybit_raw_trade_archive_manifest,
    instrument_symbol_for_logical_symbol,
)
from triggertrade.persistence.durable_messages import DurableMessageStore
from triggertrade.persistence.market_data_fact_store import MarketDataFactStore
from triggertrade.persistence.postgres import PostgresConnectionFactory, PostgresPersistenceError, PostgresUnitOfWork
from triggertrade.persistence.postgres_research_registry import (
    PostgresResearchConfigurationRegistry,
    PostgresResearchRunStore,
)
from triggertrade.persistence.postgres_research_set_registry import (
    PostgresResearchSetRegistry,
    ResearchSetVersion,
    research_set_digest,
    research_set_member_payload,
    research_set_from_package_record,
)
from triggertrade.persistence.postgres_trigger_registry import PostgresTriggerRegistry
from triggertrade.portfolio_grants import PortfolioGrantPolicy, PortfolioGrantStatus, evaluate_portfolio_grant
from triggertrade.portfolio_state import CoinPortfolioState, CommitmentBuckets, PortfolioHealth, PortfolioState
from triggertrade.position_rules import ConstructionStatus, PositionConstructionCommand, evaluate_position_construction
from triggertrade.position_rules import (
    PositionOpportunityCommand,
    PositionOpportunityHandler,
)
from triggertrade.research_v1_historical_handoff import (
    ResearchV1HistoricalMarketHandoffUnavailable,
    produce_research_v1_historical_market_handoff,
)
from triggertrade.research_v1_historical_sets import ResearchV1HistoricalSetError, resolve_research_v1_historical_set
from triggertrade.research_v1_historical_sets import HistoricalSetResolution
from triggertrade.persistence.research_store import ResearchBacktestRunRecord, ResearchBacktestStatus, ResearchRecord
from triggertrade.rules import TradingRulesVersion
from triggertrade.rules.trading import draft_from_json
from triggertrade.research_v1_execution import (
    ResearchV1SharedPortfolioState,
    apply_research_v1_portfolio_events,
    is_research_v1_pin_payload,
    research_set_to_trigger_set,
    research_v1_definition_from_pin_payload,
    resolve_research_v1_symbol_bindings,
    run_research_v1_backtest_orchestration,
)
from triggertrade.services.research import ResearchBacktestExecutionHandoffResult, _backtest_metrics
from triggertrade.services.runtime import interval_delta
from triggertrade.set_engine import DirectionResolutionScope
from triggertrade.set_scope import SetConfigurationBinding
from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType, TriggerSetVersion
from triggertrade.triggers import Signal, SignalType
from triggertrade.research_v1_historical_triggers import HistoricalTriggerEvaluation


RESEARCH_BACKTEST_PRODUCER = "Research"
RESEARCH_BACKTEST_CONSUMER = "ResearchBacktestExecution"
RESEARCH_BACKTEST_MESSAGE_TYPE = "RESEARCH_BACKTEST_START"
RESEARCH_BACKTEST_MESSAGE_VERSION = "1"
RESEARCH_V1_PORTFOLIO_LIFECYCLE_BOUNDARY_REASON = "research_v1_portfolio_lifecycle_not_yet_wired"
RESEARCH_V1_BACKTEST_EXECUTION_MODEL = "HISTORICAL_LIQUID_MARKET_APPROXIMATION_V1"


class HistoricalReplaySource(Protocol):
    def load(self, *, symbol: str, category: str, timeframe: str, start: datetime, end: datetime, use_cache: bool = True): ...


class BacktestInstrumentProvider(Protocol):
    def __call__(self, symbol: str) -> FuturesInstrumentMetadata | FuturesInstrument: ...


class ResearchBacktestExecutionExecutor(Protocol):
    canonical_research_backtest_executor: bool

    def start_research_backtest(self, record: ResearchBacktestRunRecord) -> ResearchBacktestRunRecord: ...


@dataclass(frozen=True)
class ResearchV1CertifiedPositionBacktestResult:
    backtest_run_id: str
    status: BacktestStatus
    candles_processed: int
    signals: int
    intents: int
    trades: int
    closed_trades: int
    rejected_intents: int
    no_action_count: int
    technical_failures: int
    net_pnl: Decimal
    expectancy: Decimal | None
    profit_factor: Decimal | None
    max_drawdown: Decimal | None
    fees: Decimal
    funding: Decimal
    long_trades: int
    short_trades: int
    by_regime: dict[str, int]
    research_v1_certified_position_evidence: dict[str, Any]
    research_v1_portfolio_events: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class ResearchV1BacktestLifecycleResult:
    status: str
    reason_code: str
    accepted: bool
    filled: bool
    completed: bool
    censored: bool
    closed_result: Any | None = None
    evidence: dict[str, Any] | None = None


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

    def start_research_v1_backtest(
        self,
        *,
        research: ResearchRecord,
        rules: TradingRulesVersion,
        plan: BacktestPlan,
        created_at: str,
        pin_payload: dict[str, Any],
    ) -> ResearchBacktestExecutionHandoffResult:
        with PostgresUnitOfWork(self._factory) as uow:
            PostgresResearchConfigurationRegistry(uow.connection).put_research(research)
            PostgresResearchConfigurationRegistry(uow.connection).put_trading_rules_version(rules)
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
                if is_research_v1_pin_payload(research.pin_payload):
                    return self._start_research_v1_backtest(record, research, plan)
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

    def _start_research_v1_backtest(
        self,
        record: ResearchBacktestRunRecord,
        research: ResearchRecord,
        plan: BacktestPlan,
    ) -> ResearchBacktestRunRecord:
        definition = research_v1_definition_from_pin_payload(research.pin_payload)
        with PostgresUnitOfWork(self._factory) as uow:
            config_registry = PostgresResearchConfigurationRegistry(uow.connection)
            sets = PostgresResearchSetRegistry(uow.connection).list_research_sets()
            rules_by_id = {
                binding.rules_version_id: config_registry.get_trading_rules_version(binding.rules_version_id)
                for binding in definition.execution_bindings
            }
        if any(rules is None for rules in rules_by_id.values()):
            raise PostgresPersistenceError("research_v1_rules_configuration_missing")
        set_by_version = {item.set_version: item for item in sets}
        resolve_research_v1_symbol_bindings(definition, available_sets=set_by_version, instrument_resolver=self._instrument_provider)

        def portfolio_for_rules(rules_version_id: str) -> ResearchV1SharedPortfolioState:
            rules = rules_by_id[rules_version_id]
            if rules is None:
                raise PostgresPersistenceError("research_v1_rules_configuration_missing")
            return ResearchV1SharedPortfolioState(
                total_capital=Decimal("1000"),
                max_capital_in_positions_pct=rules.draft.max_capital_in_positions_pct,
                allocation_by_symbol={coin.symbol.upper(): coin.max_allocation_pct for coin in rules.draft.coins if coin.enabled and coin.max_allocation_pct is not None},
                max_open_positions=rules.draft.max_open_positions or 1,
                max_positions_per_coin=rules.draft.max_positions_per_coin or 1,
            )

        portfolio = portfolio_for_rules(definition.selected_binding.rules_version_id)

        def runner(binding, portfolio_state):
            research_set = set_by_version[str(binding.set_version_id)]
            replay = self._historical_source.load(
                symbol=binding.instrument_symbol,
                category=plan.category,
                timeframe=plan.timeframe,
                start=_historical_replay_load_start(plan),
                end=plan.validation_end or plan.research_end + interval_delta(plan.timeframe),
                use_cache=True,
            )
            physical_candles = tuple(replay.candles)
            if not physical_candles:
                raise HistoricalDataError("backend_historical_replay_inputs_unavailable")
            candles = _research_v1_logical_candles(
                physical_candles,
                logical_symbol=binding.symbol,
                instrument_symbol=binding.instrument_symbol,
            )
            instrument = self._instrument_provider(binding.instrument_symbol)
            symbol_plan = BacktestPlan(
                binding.symbol,
                plan.category,
                plan.timeframe,
                plan.research_start,
                plan.research_end,
                validation_start=plan.validation_start,
                validation_end=plan.validation_end,
                warmup_candles=plan.warmup_candles,
            )
            trigger_set = research_set_to_trigger_set(research_set, symbol=binding.symbol)
            result = _run_research_v1_certified_position_backtest(
                trigger_set=trigger_set,
                research_set=research_set,
                trigger_rules_loader=lambda research_set=research_set: _load_trigger_rules_for_research_set(
                    self._factory,
                    research_set,
                ),
                rules=rules_by_id[binding.rules_version_id],
                plan=symbol_plan,
                candles=candles,
                instrument=instrument,
                portfolio_state=portfolio_state,
                last_traded_price_responses=_replay_sequence(replay, "last_traded_price_responses"),
                last_traded_price_response_loader=lambda symbol, as_of: _load_research_v1_last_traded_price_response(
                    self._factory,
                    symbol=symbol,
                    as_of=as_of,
                ),
                companion_candles=_replay_mapping(replay, "companion_candles"),
                companion_instrument_metadata=_replay_mapping(replay, "companion_instrument_metadata"),
                raw_trades_pages=_replay_sequence(replay, "raw_trades_pages"),
                symbol_binding={
                    "logical_symbol": binding.symbol,
                    "instrument_symbol": binding.instrument_symbol,
                    "asset": binding.asset,
                    "set_version_id": binding.set_version_id,
                    "rules_version_id": binding.rules_version_id,
                },
            )
            portfolio_events = _research_v1_portfolio_events_from_execution_result(result)
            next_portfolio = apply_research_v1_portfolio_events(portfolio_state, portfolio_events)
            payload: dict[str, Any] = {
                "status": result.status.value,
                "engine_run_id": result.backtest_run_id,
                "closed_trades": result.closed_trades,
                "net_pnl": None if result.net_pnl is None else str(result.net_pnl),
            }
            evidence = getattr(result, "research_v1_certified_position_evidence", None)
            if isinstance(evidence, dict):
                payload["certified_position_evidence"] = evidence
            if portfolio_events:
                payload["portfolio_events"] = portfolio_events
            return payload, next_portfolio

        result = run_research_v1_backtest_orchestration(
            definition,
            available_sets=set_by_version,
            run_profile=_backtest_run_profile(record),
            portfolio=portfolio,
            symbol_runner=runner,
            portfolio_factory=lambda cell: portfolio_for_rules(cell.rules_version_id),
        )
        closed_trades = sum(int(item.get("closed_trades") or 0) for item in result.symbol_results)
        metrics = {
            "research_v1": True,
            "closed_trades": closed_trades,
            "symbols_executed": len(result.symbol_results),
            "not_applicable": tuple(item.symbol for item in result.not_applicable),
            "symbol_results": tuple(dict(item) for item in result.symbol_results),
            "portfolio": dict(result.portfolio_snapshot),
        }
        unresolved_lifecycle = _research_v1_backtest_has_unresolved_lifecycle(result.symbol_results)
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).update_backtest_run(
                research_id=record.research_id,
                run_id=record.run_id,
                status=(
                    ResearchBacktestStatus.FAILED
                    if unresolved_lifecycle
                    else ResearchBacktestStatus.COMPLETED
                    if closed_trades > 0
                    else ResearchBacktestStatus.COMPLETED_NO_TRADES
                ),
                engine_run_id=None if unresolved_lifecycle else f"research-v1-backtest-{record.run_id}",
                metrics=metrics,
                unavailable_reason=RESEARCH_V1_PORTFOLIO_LIFECYCLE_BOUNDARY_REASON if unresolved_lifecycle else None,
                updated_at=datetime.now(UTC).isoformat(),
            )

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


def _backtest_run_profile(record: ResearchBacktestRunRecord) -> str:
    try:
        start = datetime.fromisoformat(record.period_start)
        end = datetime.fromisoformat(record.period_end)
    except ValueError:
        return "BACKTEST_7D"
    days = max(1, round((end - start).total_seconds() / 86400))
    if days >= 90:
        return "BACKTEST_90D"
    if days >= 30:
        return "BACKTEST_30D"
    return "BACKTEST_7D"


def _research_v1_portfolio_events_from_execution_result(result: object) -> tuple[dict[str, Any], ...]:
    raw = getattr(result, "research_v1_portfolio_events", None)
    if raw is None and isinstance(result, dict):
        raw = result.get("research_v1_portfolio_events")
    if raw is None:
        return ()
    return tuple(dict(item) for item in raw)


_CERTIFIED_POPULATION_PORTFOLIOS: dict[str, ResearchV1SharedPortfolioState] = {}
_CERTIFIED_POPULATION_PENDING_EVENTS: dict[str, tuple[dict[str, Any], ...]] = {}
_CERTIFIED_POPULATION_EVENT_JOURNAL: dict[str, list[dict[str, Any]]] = {}
_CERTIFIED_INPUT_CACHE: dict[str, dict[Any, Any]] = {
    "research_sets": {},
    "trigger_rules": {},
    "trading_rules": {},
    "rules_for_set": {},
    "physical_candles": {},
    "logical_candles": {},
    "instrument": {},
    "archive_manifest": {},
    "raw_trades": {},
    "last_traded_price": {},
}
_CERTIFIED_CACHE_STATS: dict[str, dict[str, int]] = {
    name: {"hits": 0, "misses": 0} for name in _CERTIFIED_INPUT_CACHE
}


def reset_research_v1_certified_backtest_caches(*, include_portfolio: bool = False) -> None:
    """Clear audit adapter caches without changing canonical trading behavior."""

    for cache in _CERTIFIED_INPUT_CACHE.values():
        cache.clear()
    for stats in _CERTIFIED_CACHE_STATS.values():
        stats["hits"] = 0
        stats["misses"] = 0
    if include_portfolio:
        _CERTIFIED_POPULATION_PORTFOLIOS.clear()
        _CERTIFIED_POPULATION_PENDING_EVENTS.clear()
        _CERTIFIED_POPULATION_EVENT_JOURNAL.clear()


def research_v1_certified_backtest_cache_stats() -> dict[str, dict[str, int]]:
    return {name: dict(stats) for name, stats in sorted(_CERTIFIED_CACHE_STATS.items())}


def _certified_cache_get(cache_name: str, key: Any, loader: Callable[[], Any]) -> Any:
    cache = _CERTIFIED_INPUT_CACHE[cache_name]
    stats = _CERTIFIED_CACHE_STATS[cache_name]
    if key in cache:
        stats["hits"] += 1
        return cache[key]
    stats["misses"] += 1
    value = loader()
    cache[key] = value
    return value


def _certified_timed(timings: dict[str, float], name: str, func: Callable[[], Any]) -> Any:
    started = monotonic_time.perf_counter()
    try:
        return func()
    finally:
        timings[name] = timings.get(name, 0.0) + (monotonic_time.perf_counter() - started)


def run_research_v1_certified_population_backtest(
    *,
    record: Mapping[str, Any],
    artifact: Mapping[str, Any] | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Bind one certified materialized Set MATCHED record to canonical BACKTEST execution.

    The certified population driver calls this once per record.  The function is
    intentionally thin: it loads repository-native objects/evidence, calls
    ``_run_research_v1_certified_position_backtest``, preserves the shared
    portfolio state, and returns the canonical result/evidence without adding
    trading behavior.
    """

    total_started = monotonic_time.perf_counter()
    timings: dict[str, float] = {}
    certified = dict(record)
    contexts = _certified_execution_contexts(certified)
    if len(contexts) > 1 and certified.get("execution_context") is None:
        cell_results = [
            run_research_v1_certified_population_backtest(
                record=_certified_record_for_context(certified, context),
                artifact=artifact,
                output_dir=output_dir,
            )
            for context in contexts
        ]
        first = cell_results[0]
        return {
            "status": "COMPLETED",
            "cell_execution_results": cell_results,
            "cell_execution_count": len(cell_results),
            "evidence": {
                "producer": "research_v1_certified_cell_population@1",
                "decision_cycle_id": certified["decision_cycle_id"],
                "set_result_id": certified["set_result_id"],
                "cell_execution_count": len(cell_results),
                "execution_context_ids": [item["execution_context"]["execution_context_id"] for item in cell_results],
                "first_cell_evidence": first.get("evidence"),
            },
            "research_v1_portfolio_events": tuple(
                event
                for item in cell_results
                for event in item.get("research_v1_portfolio_events", ())
            ),
            "portfolio_snapshot": {
                item["execution_context"]["execution_context_id"]: item.get("portfolio_snapshot", {})
                for item in cell_results
            },
            "performance": {
                "timings_seconds": {
                    "total_per_record": round(monotonic_time.perf_counter() - total_started, 9),
                },
                "cache_stats": research_v1_certified_backtest_cache_stats(),
            },
        }
    execution_context = contexts[0]
    observed_at = _certified_observed_at(certified)
    logical_symbol = str(certified["symbol"]).upper()
    physical_symbol = str(certified.get("physical_symbol") or instrument_symbol_for_logical_symbol(logical_symbol)).upper()
    if physical_symbol != instrument_symbol_for_logical_symbol(logical_symbol):
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:PHYSICAL_SYMBOL_MISMATCH")

    candidate_pair = _certified_candidate_pair(certified=certified, artifact=artifact)
    research_sets = _certified_timed(timings, "binding_load_research_sets", _load_certified_research_sets)
    research_set = research_sets.get(str(certified["set_version"]))
    if research_set is None:
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:RESEARCH_SET_UNAVAILABLE")
    trigger_rules = _certified_timed(
        timings,
        "trigger_rules_preparation",
        lambda: _rules_for_certified_set(research_set, candidate_pair=candidate_pair),
    )
    trading_rules_by_id = _certified_timed(timings, "trading_rules_load", _load_certified_trading_rules)
    trading_rules = trading_rules_by_id.get(str(execution_context["rules_version_id"]))
    if trading_rules is None:
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:TRADING_RULES_UNAVAILABLE")

    end = _certified_data_window_end(artifact) or max(observed_at + timedelta(days=1), datetime(2026, 8, 19, tzinfo=UTC))
    physical_candles = _certified_timed(timings, "historical_candle_load", lambda: _load_certified_candles(physical_symbol, end=end))
    candles = _certified_timed(
        timings,
        "logical_candle_conversion",
        lambda: _certified_logical_candles(
            physical_candles,
            logical_symbol=logical_symbol,
            instrument_symbol=physical_symbol,
            end=end,
        ),
    )
    btc_candles = _certified_timed(timings, "btc_companion_load", lambda: _load_certified_candles("BTCUSDT", end=end))
    instrument = _certified_timed(timings, "instrument_construction", lambda: _certified_instrument(logical_symbol))
    btc_instrument = _certified_timed(timings, "instrument_construction", lambda: _certified_instrument("BTCUSDT"))
    raw_result = _certified_timed(timings, "raw_trades_load_parse", lambda: _certified_raw_trades_response(logical_symbol, observed_at))
    last_traded_price = _certified_timed(timings, "ltp_build", lambda: _certified_last_traded_price_response(logical_symbol, observed_at))
    plan = BacktestPlan(
        logical_symbol,
        "linear",
        "1m",
        observed_at,
        observed_at,
        validation_end=end,
        warmup_candles=0,
    )
    trigger_set = research_set_to_trigger_set(research_set, symbol=logical_symbol)
    certified_set_resolution = _certified_historical_set_resolution(
        certified=certified,
        research_set=research_set,
        trigger_rules=trigger_rules,
        symbol=logical_symbol,
    )
    portfolio_key = _certified_portfolio_key(
        artifact=artifact,
        output_dir=output_dir,
        rules_version_id=trading_rules.rules_version_id,
        execution_context_id=str(execution_context["portfolio_context_id"]),
    )
    portfolio_state, pending_events = _certified_portfolio_state_at(
        portfolio_key=portfolio_key,
        rules=trading_rules,
        as_of=observed_at,
    )
    _CERTIFIED_POPULATION_PORTFOLIOS[portfolio_key] = portfolio_state
    _CERTIFIED_POPULATION_PENDING_EVENTS[portfolio_key] = pending_events
    symbol_binding = {
        "logical_symbol": logical_symbol,
        "instrument_symbol": physical_symbol,
        "asset": logical_symbol.removesuffix("USDT"),
        "set_version_id": research_set.set_version,
        "rules_version_id": trading_rules.rules_version_id,
        "certified_decision_cycle_id": certified["decision_cycle_id"],
        "certified_set_result_id": certified["set_result_id"],
        "research_cell_references": (dict(execution_context["research_cell_reference"]),),
        "execution_context_id": execution_context["execution_context_id"],
        "portfolio_context_id": execution_context["portfolio_context_id"],
        "research_id": execution_context["research_id"],
        "arm": execution_context["arm"],
        "cell": execution_context["cell"],
    }
    result = _certified_timed(
        timings,
        "canonical_execution",
        lambda: _run_research_v1_certified_position_backtest(
            trigger_set=trigger_set,
            research_set=research_set,
            trigger_rules=trigger_rules,
            rules=trading_rules,
            plan=plan,
            candles=candles,
            instrument=instrument,
            portfolio_state=portfolio_state,
            last_traded_price_responses=(last_traded_price.response_payload,),
            companion_candles={"BTCUSDT": btc_candles},
            companion_instrument_metadata={"BTCUSDT": btc_instrument},
            raw_trades_pages=(raw_result.response_payload,),
            symbol_binding=symbol_binding,
            certified_set_resolution=certified_set_resolution,
        ),
    )
    evidence = dict(result.research_v1_certified_position_evidence)
    if evidence.get("decision_cycle_id") != certified["decision_cycle_id"] or evidence.get("set_result_id") != certified["set_result_id"]:
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:CERTIFIED_IDENTITY_MISMATCH")
    events = _research_v1_portfolio_events_from_execution_result(result)
    _CERTIFIED_POPULATION_EVENT_JOURNAL.setdefault(portfolio_key, []).extend(dict(event) for event in events)
    _CERTIFIED_POPULATION_PORTFOLIOS[portfolio_key], _CERTIFIED_POPULATION_PENDING_EVENTS[portfolio_key] = (
        _certified_portfolio_state_at(
            portfolio_key=portfolio_key,
            rules=trading_rules,
            as_of=observed_at,
        )
    )
    timings["total_per_record"] = monotonic_time.perf_counter() - total_started
    return {
        "status": result.status.value,
        "result": result,
        "evidence": {
            **evidence,
            "certified_match": {
                "decision_cycle_id": certified["decision_cycle_id"],
                "set_result_id": certified["set_result_id"],
                "symbol": logical_symbol,
                "physical_symbol": physical_symbol,
                "direction": certified["direction"],
                "observed_at": observed_at.isoformat(),
                "set_version": research_set.set_version,
                "research_cell_reference_count": len(certified.get("research_cell_references", ())),
            },
            "execution_context": dict(execution_context),
        },
        "execution_context": dict(execution_context),
        "research_v1_portfolio_events": events,
        "portfolio_snapshot": _CERTIFIED_POPULATION_PORTFOLIOS[portfolio_key].snapshot(),
        "performance": {
            "timings_seconds": {name: round(value, 9) for name, value in sorted(timings.items())},
            "cache_stats": research_v1_certified_backtest_cache_stats(),
        },
    }


def run_research_v1_certified_match_backtest(
    *,
    record: Mapping[str, Any],
    artifact: Mapping[str, Any] | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    return run_research_v1_certified_population_backtest(record=record, artifact=artifact, output_dir=output_dir)


def _certified_execution_contexts(record: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    existing = record.get("execution_context")
    if isinstance(existing, Mapping):
        context = dict(existing)
        if "portfolio_context_id" not in context:
            context["portfolio_context_id"] = _certified_portfolio_context_id(
                research_id=str(context["research_id"]),
                arm=str(context["arm"]),
                cell=str(context["cell"]),
                rules_version_id=str(context["rules_version_id"]),
            )
        return (context,)
    refs = record.get("research_cell_references")
    if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)) or not refs:
        refs = (
            {
                "research_id": "CERTIFIED_RECORD",
                "arm": "CERTIFIED_RECORD",
                "cell": "CERTIFIED_RECORD",
                "set_version_id": record["set_version"],
                "rules_version_id": record["rules_version_id"],
            },
        )
    contexts: dict[tuple[str, str, str, str, str, str, str], dict[str, Any]] = {}
    for raw_ref in refs:
        if not isinstance(raw_ref, Mapping):
            continue
        ref = dict(raw_ref)
        research_id = str(ref.get("research_id") or "UNKNOWN_RESEARCH")
        arm = str(ref.get("arm") or ref.get("cell") or "DEFAULT")
        cell = str(ref.get("cell") or arm)
        set_version_id = str(ref.get("set_version_id") or record["set_version"])
        rules_version_id = str(ref.get("rules_version_id") or record["rules_version_id"])
        if set_version_id != str(record["set_version"]):
            raise HistoricalDataError("research_v1_certified_match_binding_unavailable:CELL_SET_VERSION_MISMATCH")
        key = (
            str(record["decision_cycle_id"]),
            str(record["set_result_id"]),
            set_version_id,
            research_id,
            arm,
            cell,
            rules_version_id,
        )
        context_id = _certified_execution_context_id(key)
        contexts[key] = {
            "execution_context_id": context_id,
            "portfolio_context_id": _certified_portfolio_context_id(
                research_id=research_id,
                arm=arm,
                cell=cell,
                rules_version_id=rules_version_id,
            ),
            "decision_cycle_id": key[0],
            "set_result_id": key[1],
            "set_version": key[2],
            "research_id": research_id,
            "arm": arm,
            "cell": cell,
            "rules_version_id": rules_version_id,
            "research_cell_reference": ref,
        }
    if not contexts:
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:EXECUTION_CONTEXT_UNAVAILABLE")
    return tuple(contexts[key] for key in sorted(contexts))


def _certified_execution_context_id(key: tuple[str, str, str, str, str, str, str]) -> str:
    digest = canonical_json_digest(
        {
            "schema": "RESEARCH_V1_CERTIFIED_EXECUTION_CONTEXT_V1",
            "decision_cycle_id": key[0],
            "set_result_id": key[1],
            "set_version": key[2],
            "research_id": key[3],
            "arm": key[4],
            "cell": key[5],
            "rules_version_id": key[6],
        }
    )
    return f"certified-context-{digest[:32]}"


def _certified_portfolio_context_id(
    *,
    research_id: str,
    arm: str,
    cell: str,
    rules_version_id: str,
) -> str:
    digest = canonical_json_digest(
        {
            "schema": "RESEARCH_V1_CERTIFIED_PORTFOLIO_CONTEXT_V1",
            "research_id": research_id,
            "arm": arm,
            "cell": cell,
            "rules_version_id": rules_version_id,
        }
    )
    return f"certified-portfolio-{digest[:32]}"


def _certified_record_for_context(record: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(record)
    out["rules_version_id"] = str(context["rules_version_id"])
    out["execution_context"] = dict(context)
    return out


def _certified_historical_set_resolution(
    *,
    certified: Mapping[str, Any],
    research_set: ResearchSetVersion,
    trigger_rules: Sequence[RuleDefinition],
    symbol: str,
) -> HistoricalSetResolution:
    if str(certified.get("set_version")) != research_set.set_version:
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:SET_VERSION_MISMATCH")
    if str(certified.get("set_id")) != research_set.set_id:
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:SET_ID_MISMATCH")
    if str(certified.get("set_status") or "MATCHED") != "MATCHED":
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:SET_NOT_MATCHED")
    decision_slot = _certified_observed_at(certified)
    configuration_binding = _certified_set_configuration_binding(research_set)
    evaluations = _certified_trigger_evaluations(
        certified=certified,
        research_set=research_set,
        trigger_rules=trigger_rules,
        symbol=symbol,
        observed_at=decision_slot,
    )
    source_evidence_digest = _certified_set_source_evidence_digest(research_set=research_set, evaluations=evaluations)
    certified_source_digest = str(certified.get("source_evidence_digest") or "")
    if source_evidence_digest != certified_source_digest:
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:SOURCE_EVIDENCE_DIGEST_MISMATCH")
    _assert_certified_set_ids(
        certified=certified,
        symbol=symbol,
        decision_slot=decision_slot,
        source_evidence_digest=source_evidence_digest,
    )
    frozen_condition = {
        "schema_version": "RESEARCH_V1_HISTORICAL_SET_FROZEN_CONDITION_V1",
        "set_id": research_set.set_id,
        "set_version": research_set.set_version,
        "decision_slot": decision_slot.isoformat(),
        "trigger_composition_logic": research_set.trigger_composition_logic,
        "direction_semantics": research_set.direction_semantics,
        "trigger_evaluations": [
            {
                "trigger_id": evaluation.trigger_id,
                "trigger_version": evaluation.trigger_version,
                "output_state": evaluation.output_state,
                "condition_result": evaluation.condition_result,
                "evidence_digest": evaluation.evidence_digest,
            }
            for evaluation in evaluations
        ],
    }
    direction_scope = _certified_direction_scope(research_set)
    evaluation_event_ids = tuple(evaluation.evidence_id for evaluation in evaluations)
    result_payload = _certified_set_result_payload(
        certified=certified,
        research_set=research_set,
        symbol=symbol,
        decision_slot=decision_slot,
        direction_scope=direction_scope,
        configuration_binding=configuration_binding,
        evaluation_event_ids=evaluation_event_ids,
        source_evidence_digest=source_evidence_digest,
    )
    certified_evidence_digest = str(certified.get("set_resolution_evidence_digest") or "")
    if not certified_evidence_digest:
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:SET_RESOLUTION_DIGEST_MISSING")
    return HistoricalSetResolution(
        set_id=research_set.set_id,
        set_version=research_set.set_version,
        symbol=symbol.upper(),
        status="MATCHED",
        formation_result=str(certified["formation_result"]),
        direction=str(certified["direction"]),
        decision_cycle_id=str(certified["decision_cycle_id"]),
        set_result_id=str(certified["set_result_id"]),
        reason_code=None if certified.get("reason_code") in {None, ""} else str(certified.get("reason_code")),
        configuration_binding=configuration_binding.to_payload(),
        frozen_condition=frozen_condition,
        evaluation_event_ids=evaluation_event_ids,
        source_evidence_digest=source_evidence_digest,
        trigger_evaluations=evaluations,
        result_payload=result_payload,
        evidence_digest=certified_evidence_digest,
        evidence_id=str(certified.get("set_resolution_evidence_id") or f"rv1-set-resolution-{certified_evidence_digest[:24]}"),
    )


def _certified_trigger_evaluations(
    *,
    certified: Mapping[str, Any],
    research_set: ResearchSetVersion,
    trigger_rules: Sequence[RuleDefinition],
    symbol: str,
    observed_at: datetime,
) -> tuple[HistoricalTriggerEvaluation, ...]:
    evidence_by_key = {
        (str(item["trigger_id"]), str(item["trigger_version"])): item
        for item in certified.get("trigger_evidence", ())
        if isinstance(item, Mapping)
    }
    rule_by_key = {(rule.rule_id, rule.version): rule for rule in trigger_rules}
    evaluations: list[HistoricalTriggerEvaluation] = []
    for member in research_set.trigger_members:
        key = (member.trigger_id, member.trigger_version)
        item = evidence_by_key.get(key)
        rule = rule_by_key.get(key)
        if item is None or rule is None:
            raise HistoricalDataError(
                f"research_v1_certified_match_binding_unavailable:TRIGGER_EVIDENCE_MISSING:{member.trigger_id}@{member.trigger_version}"
            )
        metric_ref = str(item["metric_ref"])
        metric_value = str(item["metric_value"])
        output_state = str(item["output_state"])
        signal_type = _certified_signal_type(output_state=output_state, condition_result=bool(item["condition_result"]))
        signal = Signal(
            signal_id=f"certified-signal-{str(item['evidence_digest'])[:24]}",
            trigger_rule_id=member.trigger_id,
            trigger_rule_version=member.trigger_version,
            symbol=symbol.upper(),
            observed_at=observed_at.isoformat(),
            window=_certified_metric_window(metric_ref),
            input_snapshot={
                "implementation_key": "triggertrade.research.DeclarativeMetricPredicateTrigger",
                "metric_ref": metric_ref,
                "operator": str(rule.definition.get("operator") or ""),
                "threshold": str(rule.definition.get("threshold") or ""),
                "metric_value": metric_value,
                "source": f"certified-materialized-set:{str(item['metric_evidence_id'])}",
                "output_state": output_state,
            },
            condition_result=bool(item["condition_result"]),
            signal_type=signal_type,
            reason=None,
            lane="BACKTEST",
            trigger_set_id=research_set.set_id,
            trigger_set_version=research_set.set_version,
        )
        evaluations.append(
            HistoricalTriggerEvaluation(
                trigger_id=member.trigger_id,
                trigger_version=member.trigger_version,
                metric_ref=metric_ref,
                metric_value=metric_value,
                operator=str(rule.definition.get("operator") or ""),
                threshold=str(rule.definition.get("threshold") or ""),
                condition_result=bool(item["condition_result"]),
                output_state=output_state,
                signal_type=signal_type.value,
                observed_at=observed_at.isoformat(),
                available_at=observed_at.isoformat(),
                evidence_id=str(item["evidence_id"]),
                evidence_digest=str(item["evidence_digest"]),
                metric_evidence_id=str(item["metric_evidence_id"]),
                metric_evidence_digest=str(item["metric_evidence_digest"]),
                signal=signal,
            )
        )
    return tuple(evaluations)


def _assert_certified_set_ids(
    *,
    certified: Mapping[str, Any],
    symbol: str,
    decision_slot: datetime,
    source_evidence_digest: str,
) -> None:
    open_event_id = f"rv1-set-open-{source_evidence_digest[:24]}"
    digest = canonical_json_digest(
        {
            "checkpoint": "B5B_SET_RESULT_V1",
            "symbol": symbol.upper(),
            "formation_epoch": int(decision_slot.timestamp()),
            "open_event_id": open_event_id,
            "open_payload_digest": source_evidence_digest,
        }
    )
    expected_decision_cycle_id = f"decision-cycle-{digest[:32]}"
    expected_set_result_id = f"set-result-{digest[32:64]}"
    if str(certified["decision_cycle_id"]) != expected_decision_cycle_id:
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:DECISION_CYCLE_ID_DERIVATION_MISMATCH")
    if str(certified["set_result_id"]) != expected_set_result_id:
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:SET_RESULT_ID_DERIVATION_MISMATCH")


def _certified_signal_type(*, output_state: str, condition_result: bool) -> SignalType:
    if not condition_result or output_state in {"FALSE", "UNAVAILABLE", "NONE"}:
        return SignalType.NO_SIGNAL
    if output_state in {"LONG", "SHORT", "TRUE"}:
        return SignalType.BUY_CANDIDATE
    return SignalType.NO_SIGNAL


def _certified_metric_window(metric_ref: str) -> str:
    if "1h" in metric_ref:
        return "1h"
    if "15m" in metric_ref or "15M" in metric_ref:
        return "15m"
    if "5m" in metric_ref or "5M" in metric_ref:
        return "5m"
    return "1m"


def _certified_set_configuration_binding(research_set: ResearchSetVersion) -> SetConfigurationBinding:
    set_digest = research_set_digest(research_set)
    member_digest = canonical_json_digest(
        {
            "set_id": research_set.set_id,
            "set_version": research_set.set_version,
            "trigger_members": [research_set_member_payload(member) for member in research_set.trigger_members],
        }
    )
    core_digest = canonical_json_digest(
        {
            "set_digest": set_digest,
            "trigger_member_digest": member_digest,
            "direction_semantics": research_set.direction_semantics,
            "composition": research_set.trigger_composition_logic,
        }
    )
    return SetConfigurationBinding(
        set_config_id=research_set.set_id,
        set_config_version=research_set.set_version,
        set_config_digest=set_digest,
        trigger_config_id=f"{research_set.set_id}:trigger-members",
        trigger_config_version=research_set.set_version,
        trigger_config_digest=member_digest,
        core_set_config_id=research_set.set_id,
        core_set_config_version=research_set.set_version,
        core_set_config_digest=core_digest,
    )


def _certified_set_source_evidence_digest(
    *, research_set: ResearchSetVersion, evaluations: Sequence[HistoricalTriggerEvaluation]
) -> str:
    return canonical_json_digest(
        {
            "producer": "research_v1_historical_set_formation@1",
            "set_id": research_set.set_id,
            "set_version": research_set.set_version,
            "set_digest": research_set_digest(research_set),
            "trigger_evaluations": [
                {
                    "trigger_id": evaluation.trigger_id,
                    "trigger_version": evaluation.trigger_version,
                    "condition_result": evaluation.condition_result,
                    "output_state": evaluation.output_state,
                    "evidence_id": evaluation.evidence_id,
                    "evidence_digest": evaluation.evidence_digest,
                }
                for evaluation in evaluations
            ],
        }
    )


def _certified_direction_scope(research_set: ResearchSetVersion) -> DirectionResolutionScope:
    if research_set.direction_semantics.startswith("F-005"):
        return DirectionResolutionScope.F005_GOVERNED
    if research_set.direction_semantics.startswith("DB-R-BTC-001"):
        return DirectionResolutionScope.GENERIC_MATCHED_BRANCH
    raise HistoricalDataError(f"research_v1_certified_match_binding_unavailable:DIRECTION_SCOPE_UNSUPPORTED:{research_set.set_version}")


def _certified_set_result_payload(
    *,
    certified: Mapping[str, Any],
    research_set: ResearchSetVersion,
    symbol: str,
    decision_slot: datetime,
    direction_scope: DirectionResolutionScope,
    configuration_binding: SetConfigurationBinding,
    evaluation_event_ids: Sequence[str],
    source_evidence_digest: str,
) -> dict[str, Any]:
    return {
        "set_result": {
            "schema_version": "SET_RESULT_B5B_V1",
            "status": "MATCHED",
            "reason_code": None if certified.get("reason_code") in {None, ""} else str(certified.get("reason_code")),
            "direction": str(certified["direction"]),
            "decision_cycle_id": str(certified["decision_cycle_id"]),
            "set_result_id": str(certified["set_result_id"]),
            "symbol": symbol.upper(),
            "formation_epoch": int(decision_slot.timestamp()),
            "direction_scope": direction_scope.value,
            "configuration_binding": configuration_binding.to_payload(),
            "configuration_binding_digest": configuration_binding.digest,
            "formation_result": str(certified["formation_result"]),
            "evaluation_event_ids": list(evaluation_event_ids),
            "source_evidence_digest": source_evidence_digest,
            "selected_branch_id": None,
            "fixed_direction_binding_digest": None,
            "generic_branches": [],
            "declared_conflict_rule": None,
            "classifier_evidence": {
                "direction": str(certified.get("classifier_direction") or certified["direction"]),
                "evidence_id": certified.get("classifier_evidence_id"),
                "evidence_digest": certified.get("classifier_evidence_digest"),
            },
        }
    }


def run_research_v1_certified_population_checkpointed_backtest(
    *,
    records: Sequence[Mapping[str, Any]],
    artifact: Mapping[str, Any] | None = None,
    output_dir: str | Path,
    max_records: int | None = None,
    adapter: Callable[..., Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Sequential certified population replay with append-safe checkpoints."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    execution_records = _certified_population_execution_records(records)
    results_path = out / "lifecycle_378_checkpoint_results.jsonl"
    errors_path = out / "lifecycle_378_checkpoint_errors.jsonl"
    replay_adapter = adapter or run_research_v1_certified_population_backtest
    completed_rows = _certified_checkpoint_rows(results_path)
    error_rows = _certified_checkpoint_rows(errors_path)
    completed_identities = {_certified_checkpoint_identity(row["record"]) for row in completed_rows}
    error_identities = {_certified_checkpoint_identity(row["record"]) for row in error_rows}
    _CERTIFIED_POPULATION_PORTFOLIOS.clear()
    _CERTIFIED_POPULATION_PENDING_EVENTS.clear()
    _CERTIFIED_POPULATION_EVENT_JOURNAL.clear()
    _restore_certified_portfolios_from_checkpoint(
        completed_rows,
        artifact=artifact,
        output_dir=out,
    )
    executed = 0
    skipped = 0
    errors = list(error_rows)
    results = list(completed_rows)
    for index, record in enumerate(execution_records, start=1):
        identity = _certified_checkpoint_identity(record)
        if identity in completed_identities or identity in error_identities:
            skipped += 1
            continue
        if max_records is not None and executed >= max_records:
            break
        try:
            result = replay_adapter(record=record, artifact=artifact, output_dir=out)
        except Exception as exc:  # pragma: no cover - exercised by focused tests
            row = {
                "index": index,
                "record": _certified_record_checkpoint_payload(record),
                "identity": _certified_identity_payload(identity),
                "exception_type": type(exc).__name__,
                "exception": str(exc),
            }
            _append_jsonl(errors_path, row)
            errors.append(row)
            error_identities.add(identity)
            executed += 1
            continue
        normalized = _certified_normalize(result)
        evidence = normalized.get("evidence", normalized) if isinstance(normalized, Mapping) else {}
        lifecycle = evidence.get("backtest_lifecycle", {}) if isinstance(evidence, Mapping) else {}
        row = {
            "index": index,
            "record": _certified_record_checkpoint_payload(record),
            "identity": _certified_identity_payload(identity),
            "decision_cycle_id": str(record["decision_cycle_id"]),
            "set_result_id": str(record["set_result_id"]),
            "symbol": str(record["symbol"]),
            "direction": str(record["direction"]),
            "observed_at": str(record["observed_at"]),
            "set_version": str(record["set_version"]),
            "lifecycle_status": str(lifecycle.get("status") or "NO_LIFECYCLE_STATUS"),
            "reason_code": str(lifecycle.get("reason_code") or ""),
            "result": normalized,
        }
        _append_jsonl(results_path, row)
        results.append(row)
        completed_identities.add(identity)
        executed += 1
    _write_certified_population_outputs(out, requested=len(execution_records), results=results, errors=errors)
    return {
        "status": "COMPLETE" if len(results) + len(errors) >= len(execution_records) else "PARTIAL",
        "requested": len(execution_records),
        "certified_set_records": len(records),
        "results": len(results),
        "errors": len(errors),
        "executed": executed,
        "skipped": skipped,
        "checkpoint_results_path": str(results_path),
        "checkpoint_errors_path": str(errors_path),
        "cache_stats": research_v1_certified_backtest_cache_stats(),
    }


def _certified_population_execution_records(records: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    expanded: dict[tuple[str, str, str, str, str, str, str], dict[str, Any]] = {}
    for record in records:
        for context in _certified_execution_contexts(record):
            context_record = _certified_record_for_context(record, context)
            expanded[_certified_checkpoint_identity(context_record)] = context_record
    return tuple(
        item
        for _key, item in sorted(
            (
                (
                    (
                        str(_certified_execution_contexts(item)[0]["portfolio_context_id"]),
                        _certified_observed_at(item).isoformat(),
                        _certified_checkpoint_identity(item),
                    ),
                    item,
                )
                for item in expanded.values()
            ),
            key=lambda pair: pair[0],
        )
    )


def _certified_checkpoint_identity(record: Mapping[str, Any]) -> tuple[str, str, str, str, str, str, str]:
    context = _certified_execution_contexts(record)[0]
    return (
        str(record["decision_cycle_id"]),
        str(record["set_result_id"]),
        str(record["set_version"]),
        str(context["research_id"]),
        str(context["arm"]),
        str(context["cell"]),
        str(context["rules_version_id"]),
    )


def _certified_identity_payload(identity: tuple[str, str, str, str, str, str, str]) -> dict[str, str]:
    decision_cycle_id, set_result_id, set_version, research_id, arm, cell, rules_version_id = identity
    return {
        "decision_cycle_id": decision_cycle_id,
        "set_result_id": set_result_id,
        "set_version": set_version,
        "research_id": research_id,
        "arm": arm,
        "cell": cell,
        "rules_version_id": rules_version_id,
        "execution_context_id": _certified_execution_context_id(identity),
        "portfolio_context_id": _certified_portfolio_context_id(
            research_id=research_id,
            arm=arm,
            cell=cell,
            rules_version_id=rules_version_id,
        ),
    }


def _certified_record_checkpoint_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    context = _certified_execution_contexts(record)[0]
    return {
        "decision_cycle_id": str(record["decision_cycle_id"]),
        "set_result_id": str(record["set_result_id"]),
        "symbol": str(record["symbol"]),
        "physical_symbol": str(record.get("physical_symbol") or ""),
        "direction": str(record["direction"]),
        "observed_at": str(record["observed_at"]),
        "set_version": str(record["set_version"]),
        "rules_version_id": str(record["rules_version_id"]),
        "execution_context": dict(context),
        "execution_context_id": str(context["execution_context_id"]),
        "portfolio_context_id": str(context["portfolio_context_id"]),
        "research_id": str(context["research_id"]),
        "arm": str(context["arm"]),
        "cell": str(context["cell"]),
        "candidate_pair": dict(record.get("candidate_pair") or {}),
        "research_cell_references": [dict(item) for item in record.get("research_cell_references", ())],
    }


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str))
        handle.write("\n")


def _certified_checkpoint_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise HistoricalDataError(f"research_v1_certified_checkpoint_unavailable:MALFORMED_JSONL:{path}:{line_number}") from exc
            if not isinstance(row, dict) or not isinstance(row.get("record"), dict):
                raise HistoricalDataError(f"research_v1_certified_checkpoint_unavailable:MALFORMED_ROW:{path}:{line_number}")
            rows.append(row)
    identities = [_certified_checkpoint_identity(row["record"]) for row in rows]
    if len(identities) != len(set(identities)):
        raise HistoricalDataError(f"research_v1_certified_checkpoint_unavailable:DUPLICATE_IDENTITY:{path}")
    return rows


def _restore_certified_portfolios_from_checkpoint(
    rows: Sequence[Mapping[str, Any]],
    *,
    artifact: Mapping[str, Any] | None,
    output_dir: Path,
) -> None:
    for row in sorted(
        rows,
        key=lambda item: (
            str(_certified_execution_contexts(item["record"])[0]["portfolio_context_id"]),
            _certified_observed_at(item["record"]).isoformat(),
            _certified_checkpoint_identity(item["record"]),
        ),
    ):
        record = row["record"]
        rules = _load_certified_trading_rules().get(str(record["rules_version_id"]))
        if rules is None:
            raise HistoricalDataError("research_v1_certified_checkpoint_unavailable:TRADING_RULES_UNAVAILABLE")
        context = _certified_execution_contexts(record)[0]
        portfolio_key = _certified_portfolio_key(
            artifact=artifact,
            output_dir=output_dir,
            rules_version_id=rules.rules_version_id,
            execution_context_id=str(context["portfolio_context_id"]),
        )
        result = row.get("result")
        events: Sequence[Mapping[str, Any]] = ()
        if isinstance(result, Mapping):
            raw_events = result.get("research_v1_portfolio_events")
            if isinstance(raw_events, Sequence) and not isinstance(raw_events, (str, bytes)):
                events = tuple(item for item in raw_events if isinstance(item, Mapping))
        _CERTIFIED_POPULATION_EVENT_JOURNAL.setdefault(portfolio_key, []).extend(dict(event) for event in events)
        state, pending = _certified_portfolio_state_at(
            portfolio_key=portfolio_key,
            rules=rules,
            as_of=_certified_observed_at(record),
        )
        _CERTIFIED_POPULATION_PORTFOLIOS[portfolio_key] = state
        _CERTIFIED_POPULATION_PENDING_EVENTS[portfolio_key] = pending


def _write_certified_population_outputs(
    output_dir: Path,
    *,
    requested: int,
    results: Sequence[Mapping[str, Any]],
    errors: Sequence[Mapping[str, Any]],
) -> None:
    _write_json(output_dir / "lifecycle_378_results.json", list(results))
    _write_json(output_dir / "lifecycle_378_errors.json", list(errors))
    status_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    for row in results:
        status = str(row.get("lifecycle_status") or "NO_LIFECYCLE_STATUS")
        reason = str(row.get("reason_code") or "")
        status_counts[status] = status_counts.get(status, 0) + 1
        if reason:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    summary = {
        "requested": requested,
        "results": len(results),
        "errors": len(errors),
        "status_counts": dict(sorted(status_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
    }
    _write_json(output_dir / "lifecycle_378_summary.json", summary)
    with (output_dir / "lifecycle_378_rows.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "index",
            "decision_cycle_id",
            "set_result_id",
            "symbol",
            "direction",
            "observed_at",
            "set_version",
            "lifecycle_status",
            "reason_code",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({field: row.get(field) for field in fieldnames})


def _write_json(path: Path, payload: Any) -> None:
    path.write_bytes(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str).encode("utf-8"))


def _certified_normalize(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _certified_normalize(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _certified_normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_certified_normalize(item) for item in value]
    if hasattr(value, "to_state_payload"):
        try:
            return _certified_normalize(value.to_state_payload())
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        try:
            return {key: _certified_normalize(item) for key, item in vars(value).items() if not key.startswith("_")}
        except Exception:
            pass
    return value


def _certified_observed_at(record: Mapping[str, Any]) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(record["observed_at"]).replace("Z", "+00:00"))
    except (KeyError, ValueError) as exc:
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:OBSERVED_AT_UNAVAILABLE") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _certified_candidate_pair(*, certified: Mapping[str, Any], artifact: Mapping[str, Any] | None) -> Mapping[str, Any]:
    pair = certified.get("candidate_pair")
    if not isinstance(pair, Mapping) and artifact is not None:
        pair = artifact.get("candidate_pair")
    if not isinstance(pair, Mapping):
        raise HistoricalDataError("research_v1_certified_match_binding_unavailable:CANDIDATE_PAIR_UNAVAILABLE")
    return pair


def _certified_data_window_end(artifact: Mapping[str, Any] | None) -> datetime | None:
    if not isinstance(artifact, Mapping):
        return None
    window = artifact.get("data_window")
    if not isinstance(window, Mapping):
        return None
    raw = window.get("end")
    if not isinstance(raw, str):
        return None
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _certified_portfolio_key(
    *,
    artifact: Mapping[str, Any] | None,
    output_dir: str | Path | None,
    rules_version_id: str,
    execution_context_id: str | None = None,
) -> str:
    context = execution_context_id or "legacy"
    if output_dir is not None:
        return f"output:{Path(output_dir)}:{rules_version_id}:{context}"
    if artifact is not None:
        return f"artifact:{id(artifact)}:{rules_version_id}:{context}"
    return f"default:{rules_version_id}:{context}"


def _certified_portfolio_state_at(
    *,
    portfolio_key: str,
    rules: TradingRulesVersion,
    as_of: datetime,
) -> tuple[ResearchV1SharedPortfolioState, tuple[dict[str, Any], ...]]:
    state = _certified_initial_portfolio(rules)
    due: list[dict[str, Any]] = []
    future: list[dict[str, Any]] = []
    for event in _CERTIFIED_POPULATION_EVENT_JOURNAL.get(portfolio_key, ()):
        item = dict(event)
        if _research_v1_portfolio_event_time(item) <= as_of:
            due.append(item)
        else:
            future.append(item)
    if due:
        state = apply_research_v1_portfolio_events(
            state,
            tuple(sorted(due, key=_research_v1_portfolio_event_sort_key)),
        )
    return state, tuple(sorted(future, key=_research_v1_portfolio_event_sort_key))


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_certified_research_sets() -> dict[str, ResearchSetVersion]:
    return _certified_cache_get("research_sets", "RESEARCH_V1_SETS", _load_certified_research_sets_uncached)


def _load_certified_research_sets_uncached() -> dict[str, ResearchSetVersion]:
    path = _repository_root() / "docs" / "research-import" / "sets" / "RESEARCH_V1_SETS.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {item.set_version: item for item in (research_set_from_package_record(record) for record in payload["sets"])}


def _load_certified_trigger_rules() -> tuple[RuleDefinition, ...]:
    return _certified_cache_get("trigger_rules", "RESEARCH_V1_TRIGGERS", _load_certified_trigger_rules_uncached)


def _load_certified_trigger_rules_uncached() -> tuple[RuleDefinition, ...]:
    path = _repository_root() / "docs" / "research-import" / "triggers" / "RESEARCH_V1_TRIGGERS_WEB_IMPORT.json"
    records = json.loads(path.read_text(encoding="utf-8"))["records"]
    rules: list[RuleDefinition] = []
    for record in records:
        data = dict(record["rule_definition"])
        data["status"] = RuleStatus(data["status"])
        data["rule_type"] = RuleType(data["rule_type"])
        data.pop("semantic_hash", None)
        rules.append(RuleDefinition(**data))
    return tuple(rules)


def _rules_for_certified_set(research_set: ResearchSetVersion, *, candidate_pair: Mapping[str, Any]) -> tuple[RuleDefinition, ...]:
    pair_key = tuple(sorted((str(key), str(value)) for key, value in candidate_pair.items()))
    return _certified_cache_get(
        "rules_for_set",
        (research_set.set_version, pair_key),
        lambda: _rules_for_certified_set_uncached(research_set, candidate_pair=candidate_pair),
    )


def _rules_for_certified_set_uncached(research_set: ResearchSetVersion, *, candidate_pair: Mapping[str, Any]) -> tuple[RuleDefinition, ...]:
    by_key = {(rule.rule_id, rule.version): rule for rule in _load_certified_trigger_rules()}
    rules: list[RuleDefinition] = []
    for member in research_set.trigger_members:
        rule = by_key.get((member.trigger_id, member.trigger_version))
        if rule is None:
            raise HistoricalDataError(f"research_v1_certified_match_binding_unavailable:TRIGGER_RULE_UNAVAILABLE:{member.trigger_id}@{member.trigger_version}")
        theta = candidate_pair.get(rule.rule_id)
        if theta is not None:
            definition = dict(rule.definition)
            params = dict(definition.get("params") or {})
            params["theta_move_pct"] = str(theta)
            definition["params"] = params
            snapshot = dict(rule.parameter_snapshot or {})
            snapshot["theta_move_pct"] = str(theta)
            rule = replace(rule, definition=definition, parameter_snapshot=snapshot)
        rules.append(rule)
    return tuple(rules)


def _load_certified_trading_rules() -> dict[str, TradingRulesVersion]:
    return _certified_cache_get("trading_rules", "RESEARCH_V1_RULES", _load_certified_trading_rules_uncached)


def _load_certified_trading_rules_uncached() -> dict[str, TradingRulesVersion]:
    path = _repository_root() / "docs" / "research-import" / "rules" / "RESEARCH_V1_RULES_WEB_IMPORT.json"
    records = json.loads(path.read_text(encoding="utf-8"))["trading_rules_versions"]
    out: dict[str, TradingRulesVersion] = {}
    for record in records:
        draft = draft_from_json(json.dumps(record["draft"], sort_keys=True, separators=(",", ":")))
        out[str(record["rules_version_id"])] = TradingRulesVersion(
            rules_version_id=str(record["rules_version_id"]),
            version=str(record["version"]),
            created_at=str(record["created_at"]),
            created_from_version_id=None if record.get("created_from_version_id") is None else str(record["created_from_version_id"]),
            created_source=str(record["created_source"]),
            change_summary=str(record["change_summary"]),
            config_hash=str(record["config_hash"]),
            schema_version=str(record["schema_version"]),
            draft=draft,
            is_current=False,
        )
    return out


def _certified_initial_portfolio(rules: TradingRulesVersion) -> ResearchV1SharedPortfolioState:
    return ResearchV1SharedPortfolioState(
        total_capital=Decimal("1000"),
        max_capital_in_positions_pct=rules.draft.max_capital_in_positions_pct,
        allocation_by_symbol={
            coin.symbol.upper(): coin.max_allocation_pct
            for coin in rules.draft.coins
            if coin.enabled and coin.max_allocation_pct is not None
        },
        max_open_positions=rules.draft.max_open_positions or 1,
        max_positions_per_coin=rules.draft.max_positions_per_coin or 1,
    )


def _load_certified_candles(physical_symbol: str, *, end: datetime) -> tuple[HistoricalCandle, ...]:
    start = datetime(2026, 7, 5, tzinfo=UTC)
    normalized_end = end.astimezone(UTC) if end.tzinfo is not None else end.replace(tzinfo=UTC)
    return _certified_cache_get(
        "physical_candles",
        (physical_symbol.upper(), start.isoformat(), normalized_end.isoformat(), "linear", "1m"),
        lambda: _load_certified_candles_uncached(physical_symbol, start=start, end=normalized_end),
    )


def _load_certified_candles_uncached(physical_symbol: str, *, start: datetime, end: datetime) -> tuple[HistoricalCandle, ...]:
    record = HistoricalKlineCache(_repository_root() / "runtime" / "history").load(
        symbol=physical_symbol,
        category="linear",
        timeframe="1m",
        start=start,
        end=end,
    )
    if record is None:
        raise HistoricalDataError(f"research_v1_certified_match_binding_unavailable:CANDLE_CACHE_MISSING:{physical_symbol}")
    return validate_historical_candles(record.candles, symbol=physical_symbol, category="linear", timeframe="1m", start=start, end=end)


def _certified_logical_candles(
    physical_candles: tuple[HistoricalCandle, ...],
    *,
    logical_symbol: str,
    instrument_symbol: str,
    end: datetime,
) -> tuple[HistoricalCandle, ...]:
    start = datetime(2026, 7, 5, tzinfo=UTC)
    normalized_end = end.astimezone(UTC) if end.tzinfo is not None else end.replace(tzinfo=UTC)
    return _certified_cache_get(
        "logical_candles",
        (logical_symbol.upper(), instrument_symbol.upper(), start.isoformat(), normalized_end.isoformat(), "linear", "1m"),
        lambda: _research_v1_logical_candles(
            physical_candles,
            logical_symbol=logical_symbol,
            instrument_symbol=instrument_symbol,
        ),
    )


def _certified_instrument(logical_symbol: str) -> FuturesInstrument:
    return _certified_cache_get("instrument", logical_symbol.upper(), lambda: _certified_instrument_uncached(logical_symbol))


def _certified_instrument_uncached(logical_symbol: str) -> FuturesInstrument:
    physical = instrument_symbol_for_logical_symbol(logical_symbol)
    tick_by_symbol = {
        "1000PEPEUSDT": "0.000001",
        "AVAXUSDT": "0.001",
        "SUIUSDT": "0.0001",
        "BTCUSDT": "0.10",
    }
    inst = FuturesInstrument(
        symbol=physical,
        base_coin=physical.removesuffix("USDT"),
        quote_coin="USDT",
        settle_coin="USDT",
        contract_type="LinearPerpetual",
        status="Trading",
        tick_size=Decimal(tick_by_symbol.get(physical, "0.0001")),
        price_scale=None,
        min_order_qty=Decimal("0.001"),
        max_order_qty=Decimal("100000000"),
        qty_step=Decimal("0.001"),
        min_notional_value=Decimal("5"),
        max_market_order_qty=Decimal("100000000"),
        min_leverage=Decimal("1"),
        max_leverage=Decimal("100"),
        leverage_step=Decimal("0.01"),
        launch_time=None,
        delivery_time=None,
        is_tradeable=True,
        updated_at="2026-07-20T00:00:00+00:00",
        source="certified_population_local_replay_metadata",
    )
    return with_catalog_hash(inst, catalog_hash((inst,)))


def _certified_archive_manifest(logical_symbol: str, archive_date: date):
    return _certified_cache_get(
        "archive_manifest",
        (logical_symbol.upper(), instrument_symbol_for_logical_symbol(logical_symbol), archive_date.isoformat()),
        lambda: _certified_archive_manifest_uncached(logical_symbol, archive_date),
    )


def _certified_archive_manifest_uncached(logical_symbol: str, archive_date: date):
    physical = instrument_symbol_for_logical_symbol(logical_symbol)
    path = _repository_root() / "tmp_raw_trade_archives" / f"{physical}{archive_date.isoformat()}.csv.gz"
    if not path.exists():
        raise HistoricalDataError(f"research_v1_certified_match_binding_unavailable:RAW_ARCHIVE_MISSING:{physical}:{archive_date.isoformat()}")
    return bybit_raw_trade_archive_manifest(
        path,
        logical_symbol=logical_symbol,
        archive_date=archive_date,
        factual_validation_status="OPERATOR_ATTESTED_COMPLETE",
    )


def _certified_raw_trades_response(logical_symbol: str, cutoff: datetime):
    normalized_cutoff = cutoff.astimezone(UTC) if cutoff.tzinfo is not None else cutoff.replace(tzinfo=UTC)
    return _certified_cache_get(
        "raw_trades",
        (logical_symbol.upper(), normalized_cutoff.isoformat()),
        lambda: _certified_raw_trades_response_uncached(logical_symbol, normalized_cutoff),
    )


def _certified_raw_trades_response_uncached(logical_symbol: str, cutoff: datetime):
    start = cutoff - timedelta(minutes=5)
    manifest = _certified_archive_manifest(logical_symbol, cutoff.date())
    return build_bybit_archive_raw_trades_response(
        logical_symbol=logical_symbol,
        range_from=start,
        range_to=cutoff,
        archive_manifests_by_date={cutoff.date(): manifest},
        request_id=f"certified-raw-{logical_symbol}-{cutoff.strftime('%Y%m%dT%H%M%S')}",
        response_id=f"certified-raw-response-{logical_symbol}-{cutoff.strftime('%Y%m%dT%H%M%S')}",
        selection_id=f"certified-raw-selection-{logical_symbol}-{cutoff.strftime('%Y%m%dT%H%M%S')}",
        source_snapshot_id=f"certified-raw-snapshot-{logical_symbol}-{cutoff.date().isoformat()}",
    )


def _certified_last_traded_price_response(logical_symbol: str, cutoff: datetime):
    normalized_cutoff = cutoff.astimezone(UTC) if cutoff.tzinfo is not None else cutoff.replace(tzinfo=UTC)
    return _certified_cache_get(
        "last_traded_price",
        (logical_symbol.upper(), normalized_cutoff.isoformat()),
        lambda: _certified_last_traded_price_response_uncached(logical_symbol, normalized_cutoff),
    )


def _certified_last_traded_price_response_uncached(logical_symbol: str, cutoff: datetime):
    day_start = datetime.combine(cutoff.date(), time.min, tzinfo=UTC)
    raw = build_bybit_archive_raw_trades_response(
        logical_symbol=logical_symbol,
        range_from=day_start,
        range_to=cutoff,
        archive_manifests_by_date={cutoff.date(): _certified_archive_manifest(logical_symbol, cutoff.date())},
        request_id=f"certified-ltp-raw-{logical_symbol}-{cutoff.strftime('%Y%m%dT%H%M%S')}",
        response_id=f"certified-ltp-raw-response-{logical_symbol}-{cutoff.strftime('%Y%m%dT%H%M%S')}",
        selection_id=f"certified-ltp-raw-selection-{logical_symbol}-{cutoff.strftime('%Y%m%dT%H%M%S')}",
        source_snapshot_id=f"certified-ltp-raw-snapshot-{logical_symbol}-{cutoff.date().isoformat()}",
    )
    return build_last_traded_price_response_from_raw_trades(
        logical_symbol=logical_symbol,
        records=raw.records,
        as_of=cutoff,
        request_id=f"certified-ltp-{logical_symbol}-{cutoff.strftime('%Y%m%dT%H%M%S')}",
        response_id=f"certified-ltp-response-{logical_symbol}-{cutoff.strftime('%Y%m%dT%H%M%S')}",
        selection_id=f"certified-ltp-selection-{logical_symbol}-{cutoff.strftime('%Y%m%dT%H%M%S')}",
        source_snapshot_id=f"certified-ltp-snapshot-{logical_symbol}-{cutoff.date().isoformat()}",
        source_endpoint=f"certified-raw-trades-archive:{logical_symbol}:{cutoff.date().isoformat()}",
    )


def _run_research_v1_certified_position_backtest(
    *,
    trigger_set: TriggerSetVersion,
    research_set: ResearchSetVersion | None = None,
    trigger_rules: tuple[RuleDefinition, ...] | None = None,
    trigger_rules_loader: Callable[[], tuple[RuleDefinition, ...]] | None = None,
    rules: TradingRulesVersion | None,
    plan: BacktestPlan,
    candles: tuple[Any, ...],
    instrument: FuturesInstrumentMetadata | FuturesInstrument,
    portfolio_state: ResearchV1SharedPortfolioState,
    last_traded_price_responses: tuple[Mapping[str, Any], ...] = (),
    last_traded_price_response_loader: Callable[[str, datetime], Mapping[str, Any] | None] | None = None,
    companion_candles: Mapping[str, tuple[Any, ...]] | None = None,
    companion_instrument_metadata: Mapping[str, FuturesInstrument] | None = None,
    raw_trades_pages: tuple[Mapping[str, Any], ...] = (),
    symbol_binding: Mapping[str, Any] | None = None,
    certified_set_resolution: HistoricalSetResolution | None = None,
):
    """Run factual Research V1 Set -> MARKET_HANDOFF -> Position opportunity."""

    if rules is None:
        raise HistoricalDataError("research_v1_historical_position_unavailable:TRADING_RULES_UNAVAILABLE")
    if research_set is None:
        raise HistoricalDataError("research_v1_historical_position_unavailable:RESEARCH_SET_UNAVAILABLE")
    resolved_trigger_rules = trigger_rules
    if resolved_trigger_rules is None and trigger_rules_loader is not None:
        resolved_trigger_rules = trigger_rules_loader()
    if not resolved_trigger_rules:
        raise HistoricalDataError("research_v1_historical_position_unavailable:TRIGGER_RULES_UNAVAILABLE")
    if not isinstance(instrument, FuturesInstrument):
        raise HistoricalDataError("research_v1_historical_market_handoff_unavailable:INSTRUMENT_METADATA_UNAVAILABLE")

    try:
        metadata_as_of = datetime.fromisoformat(instrument.updated_at.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise HistoricalDataError(
            "research_v1_historical_instrument_metadata_snapshot_unavailable"
        )

    if metadata_as_of > plan.research_end.astimezone(UTC):
        raise HistoricalDataError(
            "research_v1_historical_instrument_metadata_snapshot_unavailable"
        )

    try:
        set_resolution = certified_set_resolution
        if set_resolution is None:
            set_resolution = resolve_research_v1_historical_set(
                research_set=research_set,
                trigger_rules=resolved_trigger_rules,
                candles=candles,
                symbol=trigger_set.symbol,
                observed_at=plan.research_end,
                instrument_metadata=instrument,
                companion_candles=companion_candles,
                companion_instrument_metadata=companion_instrument_metadata,
                raw_trades_pages=raw_trades_pages,
            )
        elif (
            set_resolution.set_id != research_set.set_id
            or set_resolution.set_version != research_set.set_version
            or set_resolution.symbol.upper() != trigger_set.symbol.upper()
        ):
            raise HistoricalDataError("research_v1_certified_match_binding_unavailable:CERTIFIED_SET_RESOLUTION_MISMATCH")
        resolved_last_traded_price_responses = last_traded_price_responses
        if not resolved_last_traded_price_responses and last_traded_price_response_loader is not None:
            response = last_traded_price_response_loader(trigger_set.symbol, _research_v1_decision_slot(set_resolution))
            if response is not None:
                resolved_last_traded_price_responses = (response,)
        handoff = produce_research_v1_historical_market_handoff(
            research_set=research_set,
            set_resolution=set_resolution,
            candles=candles,
            symbol=trigger_set.symbol,
            instrument_metadata=instrument,
            last_traded_price_responses=resolved_last_traded_price_responses,
        )
    except (ResearchV1HistoricalSetError, ResearchV1HistoricalMarketHandoffUnavailable) as exc:
        raise HistoricalDataError(str(exc)) from exc

    if handoff is None:
        evidence = _research_v1_position_evidence(
            trigger_set=trigger_set,
            research_set=research_set,
            rules=rules,
            set_resolution=set_resolution,
            handoff=None,
            position_state=None,
            symbol_binding=symbol_binding,
        )
        return _research_v1_position_result(
            plan=plan,
            candles=candles,
            evidence=evidence,
            no_action_count=1,
        )

    position_decision_id = f"rv1-position-decision-{handoff.evidence_digest[:24]}"
    command = PositionOpportunityCommand(
        event_id=f"rv1-position-event-{handoff.evidence_digest[:24]}",
        position_decision_id=position_decision_id,
        occurred_at=handoff.payload["market_handoff"]["created_at"],
        market_handoff=handoff.payload,
        rules_version=rules,
    )
    try:
        position = PositionOpportunityHandler().evaluate(command)
    except ValueError as exc:
        raise HistoricalDataError(f"research_v1_historical_position_unavailable:{exc}") from exc

    position_state = position.to_state_payload()["position_opportunity_state"]
    evidence = _research_v1_position_evidence(
        trigger_set=trigger_set,
        research_set=research_set,
        rules=rules,
        set_resolution=set_resolution,
        handoff=handoff,
        position_state=position_state,
        symbol_binding=symbol_binding,
    )
    decision = str(position_state["decision"]["decision"])
    if decision == "APPROVE":
        portfolio_evidence, portfolio_events = _research_v1_approved_position_to_order_spec(
            position_state=position.to_state_payload(),
            rules=rules,
            instrument=instrument,
            portfolio_state=portfolio_state,
            as_of=handoff.payload["market_handoff"]["created_at"],
            lifecycle_candles=candles,
            funding_facts=(
                tuple(symbol_binding.get("historical_funding_facts", ()))
                if isinstance(symbol_binding, Mapping)
                else ()
            ),
        )
        evidence = {
            **evidence,
            **portfolio_evidence,
        }
        lifecycle = evidence.get("backtest_lifecycle")
        closed = bool(isinstance(lifecycle, Mapping) and lifecycle.get("completed"))
        closed_result = lifecycle.get("closed_result") if isinstance(lifecycle, Mapping) else None
        fees = Decimal("0")
        funding = Decimal("0")
        net_pnl = Decimal("0")
        if isinstance(closed_result, Mapping):
            fees = (
                Decimal(str(closed_result.get("entry_fee", "0")))
                + Decimal(str(closed_result.get("exit_fee", "0")))
                + Decimal(str(closed_result.get("other_fees", "0")))
            )
            funding = Decimal(str(closed_result.get("funding", "0")))
            net_pnl = Decimal(str(closed_result.get("net_pnl", "0")))
        return _research_v1_position_result(
            plan=plan,
            candles=candles,
            evidence=evidence,
            intents=1,
            rejected_intents=0,
            no_action_count=0,
            trades=1 if isinstance(lifecycle, Mapping) and lifecycle.get("accepted") else 0,
            closed_trades=1 if closed else 0,
            net_pnl=net_pnl,
            fees=fees,
            funding=funding,
            portfolio_events=portfolio_events,
        )
    return _research_v1_position_result(
        plan=plan,
        candles=candles,
        evidence=evidence,
        intents=1,
        rejected_intents=1 if decision == "REJECT" else 0,
        no_action_count=0,
    )


def _research_v1_approved_position_to_order_spec(
    *,
    position_state: Mapping[str, Any],
    rules: TradingRulesVersion,
    instrument: FuturesInstrument,
    portfolio_state: ResearchV1SharedPortfolioState,
    as_of: str,
    lifecycle_candles: tuple[Any, ...] | None = None,
    funding_facts: Sequence[Mapping[str, Any]] = (),
) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    state = position_state["position_opportunity_state"]
    decision = state["decision"]
    symbol = str(decision["symbol"]).upper()
    base_id = canonical_json_digest(
        {
            "producer": "research_v1_historical_position_construction@1",
            "position_decision_id": decision["position_decision_id"],
            "rules_version_id": rules.rules_version_id,
            "portfolio_snapshot": portfolio_state.snapshot(),
        }
    )[:24]
    portfolio_eval = evaluate_portfolio_grant(
        grant_decision_id=f"rv1-grant-decision-{base_id}",
        capital_grant_id=f"rv1-capital-grant-{base_id}",
        approved_decision={"position_decision": decision},
        portfolio_state=_research_v1_portfolio_state(portfolio_state, symbol=symbol, as_of=as_of),
        policy=_research_v1_portfolio_grant_policy(rules=rules, portfolio_state=portfolio_state, symbol=symbol),
        venue_facts=_research_v1_venue_facts(rules=rules, instrument=instrument),
        as_of=as_of,
    )
    grant_payload = None if portfolio_eval.capital_grant is None else portfolio_eval.capital_grant.to_payload()
    payload: dict[str, Any] = {
        "portfolio_boundary": "CAPITAL_AND_LIMITS_EVALUATED",
        "portfolio_grant_status": portfolio_eval.status.value,
        "portfolio_grant_reason": portfolio_eval.primary_reason,
        "portfolio_grant_decision": portfolio_eval.to_payload()["portfolio_grant_decision"],
        "capital_grant": grant_payload,
        "construction_status": "NOT_EVALUATED",
        "order_spec_status": "NOT_EVALUATED_REQUIRES_ALLOWED_CAPITAL_GRANT",
        "research_v1_order_spec_evidence_digest": None,
    }
    if portfolio_eval.status is not PortfolioGrantStatus.ALLOWED or grant_payload is None:
        return payload, ()

    construction = evaluate_position_construction(
        PositionConstructionCommand(
            event_id=f"rv1-construction-event-{base_id}",
            occurred_at=as_of,
            construction_result_id=f"rv1-construction-{base_id}",
            position_plan_id=f"rv1-position-plan-{base_id}",
            tranche_id=f"rv1-tranche-{base_id}",
            order_spec_id=f"rv1-order-spec-{base_id}",
            capital_grant=grant_payload,
            position_opportunity_state=position_state,
        )
    )
    construction_payload = construction.to_payload()["position_construction_evaluation"]
    order_spec_payload = None if construction.order_spec is None else construction.order_spec.to_payload()
    evidence_payload = {
        "producer": "research_v1_historical_order_spec@1",
        "portfolio_grant_decision_id": portfolio_eval.grant_decision_id,
        "capital_grant_id": grant_payload["capital_and_limits"]["capital_grant_id"],
        "construction_result_id": construction_payload["construction_result"]["position_construction_result"][
            "construction_result_id"
        ],
        "construction_status": construction.status.value,
        "construction_result": construction_payload["construction_result"],
        "order_spec": order_spec_payload,
    }
    evidence_digest = canonical_json_digest(evidence_payload)
    payload.update(
        {
            "construction_status": construction.status.value,
            "construction_reason": construction.primary_reason,
            "position_construction": construction_payload,
            "order_spec": order_spec_payload,
            "order_spec_status": "CONSTRUCTED" if construction.status is ConstructionStatus.CONSTRUCTED else "REJECTED",
            "research_v1_order_spec_evidence_digest": evidence_digest,
        }
    )
    if construction.status is not ConstructionStatus.CONSTRUCTED or order_spec_payload is None:
        return payload, ()
    spec = order_spec_payload["order_spec"]
    event = {
        "action": "RESERVE",
        "symbol": spec["symbol"],
        "actual_committed_capital": spec["economics"]["actual_committed_capital"],
        "event_time": _parse_time(as_of).astimezone(UTC).isoformat(),
        "canonical_source": "order_spec.economics.actual_committed_capital",
        "position_decision_id": spec["position_decision_id"],
        "construction_result_id": spec["construction_result_id"],
        "order_spec_id": spec["order_spec_id"],
        "order_spec_digest": canonical_json_digest(order_spec_payload),
    }
    events = [event]
    if lifecycle_candles is not None:
        lifecycle = _simulate_research_v1_backtest_lifecycle(
            order_spec=order_spec_payload,
            position_state=position_state,
            candles=tuple(lifecycle_candles),
            submitted_at=as_of,
            funding_facts=tuple(funding_facts),
        )
        payload["backtest_lifecycle"] = lifecycle.evidence
        if lifecycle.completed or lifecycle.status == "SIMULATED_REJECTED":
            events.append(
                {
                    "action": "RELEASE",
                    "symbol": spec["symbol"],
                    "actual_committed_capital": spec["economics"]["actual_committed_capital"],
                    "event_time": _research_v1_lifecycle_release_time(lifecycle.evidence, fallback=as_of).isoformat(),
                    "canonical_source": "backtest_lifecycle.closed_finality.actual_committed_capital",
                    "position_decision_id": spec["position_decision_id"],
                    "construction_result_id": spec["construction_result_id"],
                    "order_spec_id": spec["order_spec_id"],
                    "lifecycle_state": "CLOSED",
                    "backtest_execution_model": RESEARCH_V1_BACKTEST_EXECUTION_MODEL,
                }
            )
    return payload, tuple(events)


def apply_research_v1_event_time_portfolio_events(
    portfolio_state: ResearchV1SharedPortfolioState,
    *,
    pending_events: Sequence[Mapping[str, Any]] = (),
    new_events: Sequence[Mapping[str, Any]] = (),
    as_of: str | datetime,
) -> tuple[ResearchV1SharedPortfolioState, tuple[dict[str, Any], ...]]:
    """Apply only Research V1 portfolio events due at or before ``as_of``.

    This helper is for combined-portfolio historical replay, where lifecycle
    releases discovered by forward simulation must stay pending until their
    market timestamp. Isolated Research-cell replay continues to use the normal
    immediate per-cell projection.
    """

    cutoff = _parse_time(as_of) if isinstance(as_of, str) else as_of.astimezone(UTC)
    due: list[dict[str, Any]] = []
    future: list[dict[str, Any]] = []
    for event in tuple(pending_events) + tuple(new_events):
        item = dict(event)
        event_time = _research_v1_portfolio_event_time(item)
        if event_time <= cutoff:
            due.append(item)
        else:
            future.append(item)
    if due:
        portfolio_state = apply_research_v1_portfolio_events(
            portfolio_state,
            tuple(sorted(due, key=_research_v1_portfolio_event_sort_key)),
        )
    return portfolio_state, tuple(sorted(future, key=_research_v1_portfolio_event_sort_key))


def _research_v1_lifecycle_release_time(evidence: Mapping[str, Any] | None, *, fallback: str) -> datetime:
    if isinstance(evidence, Mapping):
        closed_result = evidence.get("closed_result")
        if isinstance(closed_result, Mapping):
            closed_at = closed_result.get("closed_at")
            if closed_at:
                return _parse_time(str(closed_at))
        for key in ("exit_at", "submitted_at"):
            value = evidence.get(key)
            if value:
                return _parse_time(str(value))
    return _parse_time(fallback)


def _research_v1_portfolio_event_time(event: Mapping[str, Any]) -> datetime:
    value = event.get("event_time") or event.get("occurred_at") or event.get("as_of")
    if value is None:
        raise HistoricalDataError("research_v1_combined_portfolio_unavailable:EVENT_TIME_MISSING")
    return _parse_time(str(value))


def _research_v1_portfolio_event_sort_key(event: Mapping[str, Any]) -> tuple[str, int, str, str]:
    action = str(event.get("action") or event.get("event_type") or "").upper()
    action_rank = 0 if action in {"RELEASE", "CLOSE", "CLOSED"} else 1
    return (
        _research_v1_portfolio_event_time(event).isoformat(),
        action_rank,
        str(event.get("order_spec_id") or ""),
        canonical_json_digest(dict(event)),
    )


def _simulate_research_v1_backtest_lifecycle(
    *,
    order_spec: Mapping[str, Any],
    position_state: Mapping[str, Any],
    candles: tuple[Any, ...],
    submitted_at: str,
    funding_facts: Sequence[Mapping[str, Any]] = (),
) -> ResearchV1BacktestLifecycleResult:
    spec = order_spec["order_spec"]
    direction = str(spec["direction"]).upper()
    entry = _decimal_from_text(spec["entry"]["price"])
    quantity = _decimal_from_text(spec["entry"]["quantity"])
    tp = _decimal_from_text(spec["take_profit"]["price"])
    sl = _decimal_from_text(spec["stop_loss"]["price"])
    maker_fee_rate = _decimal_rate_from_text(spec["economics"]["maker_fee_rate"])
    taker_fee_rate = _decimal_rate_from_text(spec["economics"]["taker_fee_rate"])
    leverage = _decimal_from_text(spec["leverage"])
    submitted = _parse_time(submitted_at)
    proxy = _decimal_from_text(
        position_state["position_opportunity_state"]["source_contracts"]["market_handoff"]["market_handoff"]["snapshot"][
            "set_match_reference_price"
        ]
    )
    if _post_only_marketable(direction=direction, entry=entry, proxy=proxy):
        return _lifecycle_result(
            status="SIMULATED_REJECTED",
            reason="POST_ONLY_MARKETABLE_AT_SUBMISSION",
            accepted=False,
            filled=False,
            completed=False,
            censored=False,
            spec=spec,
            submitted_at=submitted,
            proxy=proxy,
        )
    future = tuple(candle for candle in candles if candle.open_time >= submitted)
    if not future:
        return _lifecycle_result(
            status="ACCEPTED_NOT_FILLED",
            reason="NO_POST_SUBMISSION_CANDLES",
            accepted=True,
            filled=False,
            completed=False,
            censored=True,
            spec=spec,
            submitted_at=submitted,
            proxy=proxy,
        )
    entry_valid_until = _order_entry_valid_until(spec, submitted_at=submitted)
    entry_fill_candidates = future if entry_valid_until is None else tuple(
        candle for candle in future if candle.open_time < entry_valid_until
    )
    entry_fill = _first_entry_fill(entry_fill_candidates, direction=direction, entry=entry)
    if entry_fill is None:
        expired_unfilled = entry_valid_until is not None and any(candle.open_time >= entry_valid_until for candle in future)
        return _lifecycle_result(
            status="ACCEPTED_NOT_FILLED",
            reason="ENTRY_ORDER_EXPIRED_UNFILLED" if expired_unfilled else "ENTRY_LIMIT_NOT_TOUCHED",
            accepted=True,
            filled=False,
            completed=expired_unfilled,
            censored=False,
            spec=spec,
            submitted_at=submitted,
            proxy=proxy,
        )
    entry_index, entry_fill_candle, entry_filled_at, entry_at_open = entry_fill
    touched_tp_in_entry_candle = _touches_take_profit(entry_fill_candle, direction=direction, tp=tp)
    touched_sl_in_entry_candle = _touches_stop_loss(entry_fill_candle, direction=direction, sl=sl)
    if touched_tp_in_entry_candle or touched_sl_in_entry_candle:
        if not entry_at_open or (touched_tp_in_entry_candle and touched_sl_in_entry_candle):
            return _lifecycle_result(
                status="CENSORED",
                reason="ENTRY_PROTECTION_INTRABAR_SEQUENCE_UNRESOLVED",
                accepted=True,
                filled=True,
                completed=False,
                censored=True,
                spec=spec,
                submitted_at=submitted,
                proxy=proxy,
                entry_filled_at=entry_filled_at,
            )
        exit_reason = "TAKE_PROFIT" if touched_tp_in_entry_candle else "STOP_LOSS"
        threshold = tp if touched_tp_in_entry_candle else sl
        exit_price = _market_exit_price(entry_fill_candle, direction=direction, threshold=threshold, reason=exit_reason)
        exit_at = (
            entry_fill_candle.open_time.astimezone(UTC).isoformat()
            if exit_price != threshold
            else (entry_fill_candle.close_time - timedelta(microseconds=1)).astimezone(UTC).isoformat()
        )
        funding = _research_v1_backtest_funding_amount(
            funding_facts=funding_facts,
            spec=spec,
            direction=direction,
            quantity=quantity,
            entry=entry,
            opened_at=_parse_time(entry_filled_at),
            closed_at=_parse_time(exit_at),
        )
        if funding is None:
            return _lifecycle_result(
                status="CENSORED",
                reason="FUNDING_BOUNDARY_REQUIRES_HISTORICAL_FUNDING_FACTS",
                accepted=True,
                filled=True,
                completed=False,
                censored=True,
                spec=spec,
                submitted_at=submitted,
                proxy=proxy,
                entry_filled_at=entry_filled_at,
                exit_reason=exit_reason,
                exit_price=exit_price,
                exit_at=exit_at,
            )
        return _closed_lifecycle_result(
            spec=spec,
            direction=direction,
            entry=entry,
            quantity=quantity,
            exit_price=exit_price,
            leverage=leverage,
            maker_fee_rate=maker_fee_rate,
            taker_fee_rate=taker_fee_rate,
            submitted=submitted,
            proxy=proxy,
            entry_filled_at=entry_filled_at,
            exit_reason=exit_reason,
            exit_at=exit_at,
            tp=tp,
            sl=sl,
            funding=funding,
        )
    exit_candle = None
    exit_reason = None
    exit_price = None
    exit_at = None
    for candle in future[entry_index + 1 :]:
        touched_tp = _touches_take_profit(candle, direction=direction, tp=tp)
        touched_sl = _touches_stop_loss(candle, direction=direction, sl=sl)
        if touched_tp and touched_sl:
            return _lifecycle_result(
                status="CENSORED",
                reason="TP_SL_INTRABAR_SEQUENCE_UNRESOLVED",
                accepted=True,
                filled=True,
                completed=False,
                censored=True,
                spec=spec,
                submitted_at=submitted,
                proxy=proxy,
                entry_filled_at=entry_filled_at,
            )
        if not (touched_tp or touched_sl):
            continue
        exit_candle = candle
        exit_reason = "TAKE_PROFIT" if touched_tp else "STOP_LOSS"
        threshold = tp if touched_tp else sl
        exit_price = _market_exit_price(candle, direction=direction, threshold=threshold, reason=exit_reason)
        exit_at = candle.open_time.astimezone(UTC).isoformat() if exit_price != threshold else (candle.close_time - timedelta(microseconds=1)).astimezone(UTC).isoformat()
        break
    if exit_candle is None or exit_reason is None or exit_price is None or exit_at is None:
        return _lifecycle_result(
            status="FILLED_OPEN_AT_ENDPOINT",
            reason="NO_PROTECTIVE_EXIT_TOUCHED",
            accepted=True,
            filled=True,
            completed=False,
            censored=True,
            spec=spec,
            submitted_at=submitted,
            proxy=proxy,
            entry_filled_at=entry_filled_at,
        )
    funding = _research_v1_backtest_funding_amount(
        funding_facts=funding_facts,
        spec=spec,
        direction=direction,
        quantity=quantity,
        entry=entry,
        opened_at=_parse_time(entry_filled_at),
        closed_at=_parse_time(exit_at),
    )
    if funding is None:
        return _lifecycle_result(
            status="CENSORED",
            reason="FUNDING_BOUNDARY_REQUIRES_HISTORICAL_FUNDING_FACTS",
            accepted=True,
            filled=True,
            completed=False,
            censored=True,
            spec=spec,
            submitted_at=submitted,
            proxy=proxy,
            entry_filled_at=entry_filled_at,
            exit_reason=exit_reason,
            exit_price=exit_price,
            exit_at=exit_at,
        )
    return _closed_lifecycle_result(
        spec=spec,
        direction=direction,
        entry=entry,
        quantity=quantity,
        exit_price=exit_price,
        leverage=leverage,
        maker_fee_rate=maker_fee_rate,
        taker_fee_rate=taker_fee_rate,
        submitted=submitted,
        proxy=proxy,
        entry_filled_at=entry_filled_at,
        exit_reason=exit_reason,
        exit_at=exit_at,
        tp=tp,
        sl=sl,
        funding=funding,
    )


def _closed_lifecycle_result(
    *,
    spec: Mapping[str, Any],
    direction: str,
    entry: Decimal,
    quantity: Decimal,
    exit_price: Decimal,
    leverage: Decimal,
    maker_fee_rate: Decimal,
    taker_fee_rate: Decimal,
    submitted: datetime,
    proxy: Decimal,
    entry_filled_at: str,
    exit_reason: str,
    exit_at: str,
    tp: Decimal,
    sl: Decimal,
    funding: Decimal = Decimal("0"),
) -> ResearchV1BacktestLifecycleResult:
    trade_id = f"rv1-backtest-trade-{canonical_json_digest({'order_spec_id': spec['order_spec_id'], 'entry': entry_filled_at, 'exit': exit_at})[:24]}"
    closed_payload = _simulated_closed_trade_payload(
        trade_id=trade_id,
        symbol=str(spec["symbol"]),
        direction=direction,
        quantity=quantity,
        entry_price=entry,
        exit_price=exit_price,
        maker_fee_rate=maker_fee_rate,
        taker_fee_rate=taker_fee_rate,
        opened_at=entry_filled_at,
        closed_at=exit_at,
        leverage=leverage,
        funding=funding,
    )
    return _lifecycle_result(
        status="CLOSED",
        reason=exit_reason,
        accepted=True,
        filled=True,
        completed=True,
        censored=False,
        spec=spec,
        submitted_at=submitted,
        proxy=proxy,
        entry_filled_at=entry_filled_at,
        exit_reason=exit_reason,
        exit_price=exit_price,
        exit_at=exit_at,
        closed_result=closed_payload,
    )


def _post_only_marketable(*, direction: str, entry: Decimal, proxy: Decimal) -> bool:
    if direction == "LONG":
        return entry >= proxy
    if direction == "SHORT":
        return entry <= proxy
    raise HistoricalDataError("research_v1_backtest_lifecycle_unavailable:UNSUPPORTED_DIRECTION")


def _order_entry_valid_until(spec: Mapping[str, Any], *, submitted_at: datetime) -> datetime | None:
    validity = spec.get("entry", {}).get("validity")
    if not isinstance(validity, Mapping):
        return None
    time_in_force = str(validity.get("time_in_force") or "GTC").upper()
    if time_in_force == "GTC":
        return None
    if time_in_force != "TTL":
        raise HistoricalDataError("research_v1_backtest_lifecycle_unavailable:UNSUPPORTED_ORDER_VALIDITY")
    expires_at = validity.get("expires_at")
    if expires_at:
        parsed = _parse_time(str(expires_at))
        if parsed <= submitted_at:
            raise HistoricalDataError("research_v1_backtest_lifecycle_unavailable:INVALID_ORDER_EXPIRY")
        return parsed
    ttl_minutes = validity.get("ttl_minutes")
    if ttl_minutes is None:
        raise HistoricalDataError("research_v1_backtest_lifecycle_unavailable:MISSING_ORDER_EXPIRY")
    parsed = submitted_at + timedelta(minutes=int(ttl_minutes))
    if parsed <= submitted_at:
        raise HistoricalDataError("research_v1_backtest_lifecycle_unavailable:INVALID_ORDER_EXPIRY")
    return parsed


def _first_entry_fill(candles: tuple[Any, ...], *, direction: str, entry: Decimal) -> tuple[int, Any, str, bool] | None:
    for index, candle in enumerate(candles):
        opened = Decimal(str(candle.open))
        if direction == "LONG" and Decimal(str(candle.low)) <= entry:
            at_open = opened <= entry
            timestamp = candle.open_time if at_open else candle.close_time - timedelta(microseconds=1)
            return index, candle, timestamp.astimezone(UTC).isoformat(), at_open
        if direction == "SHORT" and Decimal(str(candle.high)) >= entry:
            at_open = opened >= entry
            timestamp = candle.open_time if at_open else candle.close_time - timedelta(microseconds=1)
            return index, candle, timestamp.astimezone(UTC).isoformat(), at_open
    return None


def _touches_take_profit(candle: Any, *, direction: str, tp: Decimal) -> bool:
    if direction == "LONG":
        return Decimal(str(candle.high)) >= tp
    if direction == "SHORT":
        return Decimal(str(candle.low)) <= tp
    raise HistoricalDataError("research_v1_backtest_lifecycle_unavailable:UNSUPPORTED_DIRECTION")


def _touches_stop_loss(candle: Any, *, direction: str, sl: Decimal) -> bool:
    if direction == "LONG":
        return Decimal(str(candle.low)) <= sl
    if direction == "SHORT":
        return Decimal(str(candle.high)) >= sl
    raise HistoricalDataError("research_v1_backtest_lifecycle_unavailable:UNSUPPORTED_DIRECTION")


def _market_exit_price(candle: Any, *, direction: str, threshold: Decimal, reason: str) -> Decimal:
    opened = Decimal(str(candle.open))
    if direction == "LONG" and reason == "STOP_LOSS" and opened <= threshold:
        return opened
    if direction == "LONG" and reason == "TAKE_PROFIT" and opened >= threshold:
        return opened
    if direction == "SHORT" and reason == "STOP_LOSS" and opened >= threshold:
        return opened
    if direction == "SHORT" and reason == "TAKE_PROFIT" and opened <= threshold:
        return opened
    return threshold


def _crosses_funding_boundary(opened_at: datetime, closed_at: datetime) -> bool:
    return bool(_research_v1_funding_boundaries(opened_at, closed_at))


def _research_v1_funding_boundaries(opened_at: datetime, closed_at: datetime) -> tuple[datetime, ...]:
    cursor = opened_at.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    if cursor < opened_at:
        cursor += timedelta(hours=1)
    boundaries: list[datetime] = []
    while cursor <= closed_at.astimezone(UTC):
        if cursor.hour in {0, 8, 16} and opened_at < cursor <= closed_at:
            boundaries.append(cursor)
        cursor += timedelta(hours=1)
    return tuple(boundaries)


def _research_v1_backtest_funding_amount(
    *,
    funding_facts: Sequence[Mapping[str, Any]],
    spec: Mapping[str, Any],
    direction: str,
    quantity: Decimal,
    entry: Decimal,
    opened_at: datetime,
    closed_at: datetime,
) -> Decimal | None:
    boundaries = _research_v1_funding_boundaries(opened_at, closed_at)
    if not boundaries:
        return Decimal("0")
    total = Decimal("0")
    symbol = str(spec.get("physical_symbol") or spec["symbol"]).upper()
    for boundary in boundaries:
        fact = _research_v1_funding_fact_for_boundary(
            funding_facts=funding_facts,
            symbol=symbol,
            boundary=boundary,
        )
        if fact is None:
            return None
        amount = _research_v1_signed_funding_from_fact(
            fact=fact,
            direction=direction,
            quantity=quantity,
            entry=entry,
        )
        if amount is None:
            return None
        total += amount
    return total


def _research_v1_funding_fact_for_boundary(
    *,
    funding_facts: Sequence[Mapping[str, Any]],
    symbol: str,
    boundary: datetime,
) -> Mapping[str, Any] | None:
    expected = boundary.astimezone(UTC)
    for fact in funding_facts:
        fact_symbol = str(fact.get("symbol") or "").upper()
        if fact_symbol and fact_symbol != symbol:
            continue
        timestamp = fact.get("funding_time") or fact.get("timestamp") or fact.get("funding_timestamp")
        if timestamp is None:
            continue
        if _parse_time(str(timestamp)) == expected:
            return fact
    return None


def _research_v1_signed_funding_from_fact(
    *,
    fact: Mapping[str, Any],
    direction: str,
    quantity: Decimal,
    entry: Decimal,
) -> Decimal | None:
    if fact.get("signed_funding") is not None:
        return Decimal(str(fact["signed_funding"]))
    if fact.get("signed_funding_amount") is not None:
        return Decimal(str(fact["signed_funding_amount"]))
    rate = Decimal(str(fact.get("funding_rate")))
    mark = fact.get("mark_price") or fact.get("funding_rate_mark_price") or fact.get("basis_mark_price")
    basis_source = fact.get("funding_basis_notional") or fact.get("notional")
    if basis_source is not None:
        basis = Decimal(str(basis_source))
    elif mark is not None:
        basis = quantity * Decimal(str(mark))
    else:
        return None
    amount = basis * rate
    if direction == "LONG":
        return -amount
    if direction == "SHORT":
        return amount
    raise HistoricalDataError("research_v1_backtest_lifecycle_unavailable:UNSUPPORTED_DIRECTION")


def _lifecycle_result(
    *,
    status: str,
    reason: str,
    accepted: bool,
    filled: bool,
    completed: bool,
    censored: bool,
    spec: Mapping[str, Any],
    submitted_at: datetime,
    proxy: Decimal,
    entry_filled_at: str | None = None,
    exit_reason: str | None = None,
    exit_price: Decimal | None = None,
    exit_at: str | None = None,
    closed_result: Mapping[str, Any] | None = None,
) -> ResearchV1BacktestLifecycleResult:
    evidence = {
        "execution_namespace": "BACKTEST",
        "execution_model": RESEARCH_V1_BACKTEST_EXECUTION_MODEL,
        "mode_isolation": "DEMO_LIVE_NATIVE_EXECUTION_UNCHANGED",
        "order_spec_id": spec["order_spec_id"],
        "decision_cycle_id": spec["decision_cycle_id"],
        "set_result_id": spec["set_result_id"],
        "position_decision_id": spec["position_decision_id"],
        "capital_grant_id": spec["capital_grant_id"],
        "status": status,
        "reason_code": reason,
        "submitted_at": submitted_at.astimezone(UTC).isoformat(),
        "post_only_proxy_basis": "MODEL_LAST_PRICE_PROXY",
        "post_only_proxy_price": str(proxy),
        "accepted": accepted,
        "filled": filled,
        "completed": completed,
        "censored": censored,
        "entry_filled_at": entry_filled_at,
        "exit_reason": exit_reason,
        "exit_price": None if exit_price is None else str(exit_price),
        "exit_at": exit_at,
        "fee_model": "configured_maker_entry_taker_protection_exit",
        "funding_model": "zero_only_when_no_funding_timestamp_crossed_otherwise_censor",
        "closed_result": None if closed_result is None else dict(closed_result),
    }
    evidence["evidence_digest"] = canonical_json_digest(evidence)
    return ResearchV1BacktestLifecycleResult(
        status=status,
        reason_code=reason,
        accepted=accepted,
        filled=filled,
        completed=completed,
        censored=censored,
        closed_result=None if closed_result is None else dict(closed_result),
        evidence=evidence,
    )


def _simulated_closed_trade_payload(
    *,
    trade_id: str,
    symbol: str,
    direction: str,
    quantity: Decimal,
    entry_price: Decimal,
    exit_price: Decimal,
    maker_fee_rate: Decimal,
    taker_fee_rate: Decimal,
    opened_at: str,
    closed_at: str,
    leverage: Decimal,
    funding: Decimal = Decimal("0"),
) -> dict[str, str]:
    gross = (exit_price - entry_price) * quantity if direction == "LONG" else (entry_price - exit_price) * quantity
    entry_fee = entry_price * quantity * maker_fee_rate
    exit_fee = exit_price * quantity * taker_fee_rate
    other_fees = Decimal("0")
    net = gross - entry_fee - exit_fee - other_fees + funding
    duration = max(0, int((_parse_time(closed_at) - _parse_time(opened_at)).total_seconds()))
    return {
        "trade_id": trade_id,
        "symbol": symbol,
        "direction": direction,
        "quantity": str(quantity),
        "leverage": str(leverage),
        "entry_vwap": str(entry_price),
        "exit_vwap": str(exit_price),
        "gross_pnl": str(gross),
        "entry_fee": str(entry_fee),
        "exit_fee": str(exit_fee),
        "other_fees": str(other_fees),
        "funding": str(funding),
        "net_pnl": str(net),
        "opened_at": opened_at,
        "closed_at": closed_at,
        "duration_seconds": str(duration),
        "settlement_asset": "USDT",
        "evidence_source": BACKTEST_EVIDENCE_SOURCE,
        "fee_sign_convention": "positive_cost_negative_rebate",
    }


def _decimal_from_text(value: object) -> Decimal:
    parsed = Decimal(str(value))
    if parsed <= 0:
        raise HistoricalDataError("research_v1_backtest_lifecycle_unavailable:NON_POSITIVE_DECIMAL")
    return parsed


def _decimal_rate_from_text(value: object) -> Decimal:
    return Decimal(str(value))


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _research_v1_portfolio_state(
    portfolio: ResearchV1SharedPortfolioState,
    *,
    symbol: str,
    as_of: str,
) -> PortfolioState:
    committed = portfolio.committed_by_symbol_map
    open_positions = portfolio.open_positions_by_symbol_map
    coins = tuple(
        CoinPortfolioState(
            symbol=item,
            buckets=CommitmentBuckets(
                held_committed_capital=_decimal_text(committed.get(item, Decimal("0"))),
                committed_tranches=open_positions.get(item, 0),
            ),
        )
        for item in sorted(set(portfolio.allocation_by_symbol) | {symbol.upper()})
    )
    return PortfolioState(
        portfolio_id="research-v1-backtest",
        revision=1 + sum(open_positions.values()),
        health=PortfolioHealth.LIVE,
        as_of=as_of,
        evidence_id=f"rv1-portfolio-{canonical_json_digest(portfolio.snapshot())[:24]}",
        global_buckets=CommitmentBuckets(
            held_committed_capital=_decimal_text(portfolio.committed_capital),
            committed_tranches=sum(open_positions.values()),
        ),
        coins=coins,
    )


def _research_v1_portfolio_grant_policy(
    *,
    rules: TradingRulesVersion,
    portfolio_state: ResearchV1SharedPortfolioState,
    symbol: str,
) -> PortfolioGrantPolicy:
    draft = rules.draft
    allocation = portfolio_state.allocation_by_symbol.get(symbol.upper())
    if allocation is None:
        raise HistoricalDataError("research_v1_portfolio_unavailable:COIN_ALLOCATION_UNAVAILABLE")
    max_open = draft.max_open_positions if draft.max_open_positions_enabled and draft.max_open_positions else portfolio_state.max_open_positions
    max_per_coin = (
        draft.max_positions_per_coin
        if draft.max_positions_per_coin_enabled and draft.max_positions_per_coin
        else portfolio_state.max_positions_per_coin
    )
    daily_loss_enabled = bool(draft.daily_loss_limit_enabled)
    return PortfolioGrantPolicy(
        minimum_tranche_capital=_decimal_text(draft.minimum_tranche_capital or Decimal("0")),
        global_position_cap=_decimal_text(portfolio_state.aggregate_capital_cap),
        coin_allocation_cap=_decimal_text(portfolio_state.total_capital * allocation),
        max_open_positions=max_open,
        max_positions_per_coin=max_per_coin,
        daily_loss_blocked=daily_loss_enabled,
        daily_loss_status="UNAVAILABLE" if daily_loss_enabled else "PASS",
        daily_loss_reason_code="DAILY_LOSS_DATA_UNAVAILABLE" if daily_loss_enabled else None,
        daily_loss_configured_threshold=None if draft.daily_loss_limit_pct is None else _decimal_text(draft.daily_loss_limit_pct),
        daily_loss_calculated=None,
        daily_loss_availability="DATA_UNAVAILABLE" if daily_loss_enabled else "NOT_CONFIGURED",
    )


def _research_v1_venue_facts(*, rules: TradingRulesVersion, instrument: FuturesInstrument) -> dict[str, Any]:
    if instrument.min_notional_value is None:
        raise HistoricalDataError("research_v1_portfolio_unavailable:INSTRUMENT_MIN_NOTIONAL_UNAVAILABLE")
    if instrument.min_leverage is None or instrument.leverage_step is None:
        raise HistoricalDataError("research_v1_portfolio_unavailable:INSTRUMENT_LEVERAGE_UNAVAILABLE")
    return {
        "instrument": {
            "tick_size": str(instrument.tick_size),
            "qty_step": str(instrument.qty_step),
            "min_order_qty": str(instrument.min_order_qty),
            "min_notional": str(instrument.min_notional_value),
            "max_order_qty": str(instrument.max_order_qty),
            "max_order_qty_status": "AVAILABLE",
            "max_order_qty_source_field": "lotSizeFilter.maxOrderQty",
            "max_leverage": str(instrument.max_leverage),
            "contract_type": "LINEAR_USDT_PERPETUAL",
            "metadata_revision": instrument.catalog_hash or f"{instrument.source}:{instrument.symbol}:{instrument.updated_at}",
            "native_profile_revision": "bybit-linear-futures-catalog-v1",
            "instrument_supported": instrument.is_tradeable,
            "position_mode": "HEDGE_MODE",
            "margin_mode": "ISOLATED",
            "as_of": instrument.updated_at,
            "source_ref": f"{instrument.source}:{instrument.symbol}",
        },
        "fees": {
            "maker_fee_rate": _decimal_text(rules.draft.maker_fee_rate),
            "taker_fee_rate": _decimal_text(rules.draft.taker_fee_rate),
            "fee_schedule_version": f"{rules.rules_version_id}:fees",
            "effective_at": rules.created_at,
            "as_of": rules.created_at,
            "source_ref": f"trading-rules:{rules.rules_version_id}",
        },
    }


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f") if value != 0 else "0"


def _load_trigger_rules_for_research_set(
    factory: PostgresConnectionFactory,
    research_set: ResearchSetVersion,
) -> tuple[RuleDefinition, ...]:
    with PostgresUnitOfWork(factory) as uow:
        registry = PostgresTriggerRegistry(uow.connection)
        rules: list[RuleDefinition] = []
        for member in research_set.trigger_members:
            rule = registry.get_trigger_version(member.trigger_id, member.trigger_version)
            if rule is None:
                raise PostgresPersistenceError(f"research_v1_trigger_version_missing:{member.trigger_id}@{member.trigger_version}")
            rules.append(rule)
        return tuple(rules)


def _load_research_v1_last_traded_price_response(
    factory: PostgresConnectionFactory,
    *,
    symbol: str,
    as_of: datetime,
) -> Mapping[str, Any] | None:
    with PostgresUnitOfWork(factory) as uow:
        return MarketDataFactStore(uow.connection).latest_last_traded_price_response_as_of(symbol=symbol, as_of=as_of)


def _research_v1_decision_slot(set_resolution: object) -> datetime:
    frozen_condition = getattr(set_resolution, "frozen_condition", None)
    if not isinstance(frozen_condition, Mapping):
        raise HistoricalDataError("research_v1_historical_market_handoff_unavailable:DECISION_SLOT_UNAVAILABLE")
    raw = frozen_condition.get("decision_slot")
    if not isinstance(raw, str):
        raise HistoricalDataError("research_v1_historical_market_handoff_unavailable:DECISION_SLOT_UNAVAILABLE")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HistoricalDataError("research_v1_historical_market_handoff_unavailable:DECISION_SLOT_UNAVAILABLE") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _replay_sequence(replay: object, name: str) -> tuple[Mapping[str, Any], ...]:
    value = getattr(replay, name, ())
    if value is None:
        return ()
    return tuple(value)


def _replay_mapping(replay: object, name: str) -> Mapping[str, Any] | None:
    value = getattr(replay, name, None)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise HistoricalDataError(f"research_v1_historical_replay_{name}_invalid")
    return {str(key): tuple(item) if name == "companion_candles" else item for key, item in value.items()}


def _research_v1_logical_candles(
    candles: tuple[HistoricalCandle, ...],
    *,
    logical_symbol: str,
    instrument_symbol: str,
) -> tuple[HistoricalCandle, ...]:
    expected = instrument_symbol.upper()
    requested = logical_symbol.upper()
    converted: list[HistoricalCandle] = []
    for candle in candles:
        if candle.symbol.upper() != expected:
            raise HistoricalDataError("research_v1_historical_physical_symbol_mismatch")
        if requested == expected:
            converted.append(candle)
        else:
            converted.append(replace(candle, symbol=requested))
    return tuple(converted)


def _research_v1_position_evidence(
    *,
    trigger_set: TriggerSetVersion,
    research_set: ResearchSetVersion,
    rules: TradingRulesVersion,
    set_resolution,
    handoff,
    position_state: Mapping[str, Any] | None,
    symbol_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "producer": "research_v1_historical_position_opportunity@1",
        "trigger_set_id": trigger_set.set_id,
        "trigger_set_version": trigger_set.version,
        "research_set_id": research_set.set_id,
        "research_set_version": research_set.set_version,
        "rules_version_id": rules.rules_version_id,
        "rules_version": rules.version,
        "set_resolution_evidence_digest": set_resolution.evidence_digest,
        "set_result_id": str(set_resolution.set_result_id),
        "decision_cycle_id": str(set_resolution.decision_cycle_id),
        "set_direction": set_resolution.direction,
        "market_handoff_evidence_digest": None if handoff is None else handoff.evidence_digest,
        "market_handoff_id": None if handoff is None else handoff.evidence_id,
        "position_state": position_state,
        "symbol_binding": None if symbol_binding is None else dict(symbol_binding),
    }
    digest = canonical_json_digest(payload)
    return {
        **payload,
        "evidence_id": f"rv1-position-opportunity-{digest[:24]}",
        "evidence_digest": digest,
        "portfolio_boundary": "CAPITAL_AND_LIMITS_NOT_EVALUATED",
        "order_spec_status": "NOT_EVALUATED_REQUIRES_PORTFOLIO_GRANT",
    }


def _research_v1_position_result(
    *,
    plan: BacktestPlan,
    candles: tuple[Any, ...],
    evidence: dict[str, Any],
    intents: int = 0,
    rejected_intents: int = 0,
    no_action_count: int = 0,
    trades: int = 0,
    closed_trades: int = 0,
    net_pnl: Decimal = Decimal("0"),
    fees: Decimal = Decimal("0"),
    funding: Decimal = Decimal("0"),
    long_trades: int = 0,
    short_trades: int = 0,
    portfolio_events: tuple[dict[str, Any], ...] = (),
) -> ResearchV1CertifiedPositionBacktestResult:
    return ResearchV1CertifiedPositionBacktestResult(
        backtest_run_id=f"research-v1-position-{evidence['evidence_digest'][:24]}",
        status=BacktestStatus.COMPLETED,
        candles_processed=len(candles),
        signals=1 if intents else 0,
        intents=intents,
        trades=trades,
        closed_trades=closed_trades,
        rejected_intents=rejected_intents,
        no_action_count=no_action_count,
        technical_failures=0,
        net_pnl=net_pnl,
        expectancy=None,
        profit_factor=None,
        max_drawdown=Decimal("0"),
        fees=fees,
        funding=funding,
        long_trades=long_trades,
        short_trades=short_trades,
        by_regime={},
        research_v1_certified_position_evidence=evidence,
        research_v1_portfolio_events=portfolio_events,
    )


def _research_v1_backtest_has_unresolved_lifecycle(symbol_results: tuple[Mapping[str, Any], ...]) -> bool:
    for result in symbol_results:
        evidence = result.get("certified_position_evidence")
        if not isinstance(evidence, Mapping):
            return True
        order_status = evidence.get("order_spec_status")
        if order_status in {None, "REJECTED"}:
            if order_status is None:
                return True
            continue
        if isinstance(order_status, str) and order_status.startswith("NOT_EVALUATED"):
            continue
        if order_status != "CONSTRUCTED":
            return True
        lifecycle = evidence.get("backtest_lifecycle")
        if not isinstance(lifecycle, Mapping):
            return True
        if lifecycle.get("completed") is True:
            continue
        if lifecycle.get("status") == "SIMULATED_REJECTED":
            continue
        return True
    return False


def _historical_replay_load_start(plan: BacktestPlan) -> datetime:
    return plan.research_start.astimezone(UTC) - interval_delta(plan.timeframe) * (plan.warmup_candles + 1)


def _validate_authoritative_trigger_set(*, research: ResearchRecord, trigger_set: TriggerSetVersion) -> None:
    if (research.set_id, research.set_version) != (trigger_set.set_id, trigger_set.version):
        raise PostgresPersistenceError("research_backtest_trigger_set_identity_mismatch")


def _backtest_unavailable_reason(exc: Exception) -> str:
    text = str(exc).lower()
    if isinstance(exc, HistoricalDataError):
        if text.startswith("research_v1_historical_"):
            return text
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
