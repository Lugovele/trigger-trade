"""Durable Research Backtest execution handoff and worker dispatch."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from triggertrade.backtest import BacktestPlan, BacktestResult, BacktestStatus, ExactBacktestTriggerSetResolver, run_backtest
from triggertrade.backtest.data import HistoricalDataError
from triggertrade.backtest.engine import BacktestEngineError
from triggertrade.backtest.models import BACKTEST_DATA_SOURCE_VERSION, HistoricalCandle
from triggertrade.canonical_json import canonical_json_digest
from triggertrade.config import AppConfig
from triggertrade.instruments import FuturesInstrument
from triggertrade.market_data import FuturesInstrumentMetadata
from triggertrade.persistence.durable_messages import DurableMessageStore
from triggertrade.persistence.market_data_fact_store import MarketDataFactStore
from triggertrade.persistence.postgres import PostgresConnectionFactory, PostgresPersistenceError, PostgresUnitOfWork
from triggertrade.persistence.postgres_research_registry import (
    PostgresResearchConfigurationRegistry,
    PostgresResearchRunStore,
)
from triggertrade.persistence.postgres_research_set_registry import PostgresResearchSetRegistry, ResearchSetVersion
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
from triggertrade.persistence.research_store import ResearchBacktestRunRecord, ResearchBacktestStatus, ResearchRecord
from triggertrade.rules import TradingRulesVersion
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
from triggertrade.trigger_sets import RuleDefinition, TriggerSetVersion


RESEARCH_BACKTEST_PRODUCER = "Research"
RESEARCH_BACKTEST_CONSUMER = "ResearchBacktestExecution"
RESEARCH_BACKTEST_MESSAGE_TYPE = "RESEARCH_BACKTEST_START"
RESEARCH_BACKTEST_MESSAGE_VERSION = "1"
RESEARCH_V1_PORTFOLIO_LIFECYCLE_BOUNDARY_REASON = "research_v1_portfolio_lifecycle_not_yet_wired"


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
                end=plan.research_end,
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
        with PostgresUnitOfWork(self._factory) as uow:
            return PostgresResearchRunStore(uow.connection).update_backtest_run(
                research_id=record.research_id,
                run_id=record.run_id,
                status=ResearchBacktestStatus.FAILED,
                engine_run_id=None,
                metrics=metrics,
                unavailable_reason=RESEARCH_V1_PORTFOLIO_LIFECYCLE_BOUNDARY_REASON,
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
        )
        evidence = {
            **evidence,
            **portfolio_evidence,
        }
        return _research_v1_position_result(
            plan=plan,
            candles=candles,
            evidence=evidence,
            intents=1,
            rejected_intents=0,
            no_action_count=0,
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
        "canonical_source": "order_spec.economics.actual_committed_capital",
        "position_decision_id": spec["position_decision_id"],
        "construction_result_id": spec["construction_result_id"],
        "order_spec_id": spec["order_spec_id"],
        "order_spec_digest": canonical_json_digest(order_spec_payload),
    }
    return payload, (event,)


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
    return PortfolioGrantPolicy(
        minimum_tranche_capital=_decimal_text(draft.minimum_tranche_capital or Decimal("0")),
        global_position_cap=_decimal_text(portfolio_state.aggregate_capital_cap),
        coin_allocation_cap=_decimal_text(portfolio_state.total_capital * allocation),
        max_open_positions=max_open,
        max_positions_per_coin=max_per_coin,
        daily_loss_blocked=bool(draft.daily_loss_limit_enabled),
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
        "set_result_id": set_resolution.set_result_id,
        "decision_cycle_id": set_resolution.decision_cycle_id,
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
        trades=0,
        closed_trades=0,
        rejected_intents=rejected_intents,
        no_action_count=no_action_count,
        technical_failures=0,
        net_pnl=Decimal("0"),
        expectancy=None,
        profit_factor=None,
        max_drawdown=Decimal("0"),
        fees=Decimal("0"),
        funding=Decimal("0"),
        long_trades=long_trades,
        short_trades=short_trades,
        by_regime={},
        research_v1_certified_position_evidence=evidence,
        research_v1_portfolio_events=portfolio_events,
    )

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
