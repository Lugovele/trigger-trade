"""Durable Research Backtest execution handoff and worker dispatch."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol

from triggertrade.backtest import BacktestPlan, BacktestResult, BacktestStatus, ExactBacktestTriggerSetResolver, run_backtest
from triggertrade.backtest.data import HistoricalDataError
from triggertrade.backtest.engine import BacktestEngineError
from triggertrade.backtest.models import BACKTEST_DATA_SOURCE_VERSION
from triggertrade.capital_grants import build_capital_and_limits_grant
from triggertrade.canonical_json import canonical_json_digest
from triggertrade.config import AppConfig
from triggertrade.market_data import FuturesInstrumentMetadata
from triggertrade.persistence.durable_messages import DurableMessageStore
from triggertrade.persistence.postgres import PostgresConnectionFactory, PostgresPersistenceError, PostgresUnitOfWork
from triggertrade.persistence.postgres_research_registry import (
    PostgresResearchConfigurationRegistry,
    PostgresResearchRunStore,
)
from triggertrade.persistence.postgres_research_set_registry import PostgresResearchSetRegistry
from triggertrade.persistence.research_store import ResearchBacktestRunRecord, ResearchBacktestStatus, ResearchRecord
from triggertrade.position_rules import (
    ConstructionStatus,
    PositionConstructionCommand,
    PositionOpportunityCommand,
    PositionOpportunityHandler,
    evaluate_position_construction,
)
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
from triggertrade.set_engine.formulas import Direction, TriggerResult
from triggertrade.set_engine.handler import (
    DirectionResolutionScope,
    GenericFixedDirectionBinding,
    HandoffContext,
    HandoffFacts,
    HandoffReferenceLevel,
    SetMatchStatus,
    SetResolutionRequest,
    _resolve_direction,
    _set_ids,
    _market_handoff_payload,
    generic_fixed_direction_binding_digest,
)
from triggertrade.set_scope import SetConfigurationBinding, SetFormationEpoch
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
            candles = tuple(replay.candles)
            if not candles:
                raise HistoricalDataError("backend_historical_replay_inputs_unavailable")
            instrument = self._instrument_provider(binding.instrument_symbol)
            symbol_plan = BacktestPlan(
                binding.instrument_symbol,
                plan.category,
                plan.timeframe,
                plan.research_start,
                plan.research_end,
                validation_start=plan.validation_start,
                validation_end=plan.validation_end,
                warmup_candles=plan.warmup_candles,
            )
            trigger_set = research_set_to_trigger_set(research_set, symbol=binding.instrument_symbol)
            result = _run_research_v1_certified_position_backtest(
                trigger_set=trigger_set,
                rules=rules_by_id[binding.rules_version_id],
                plan=symbol_plan,
                candles=candles,
                instrument=instrument,
                portfolio_state=portfolio_state,
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
        status = ResearchBacktestStatus.COMPLETED if closed_trades > 0 else ResearchBacktestStatus.COMPLETED_NO_TRADES
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
                status=status,
                engine_run_id=f"research-v1-{record.run_id}",
                metrics=metrics,
                unavailable_reason=None,
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
    rules: TradingRulesVersion | None,
    plan: BacktestPlan,
    candles: tuple[Any, ...],
    instrument: FuturesInstrumentMetadata,
    portfolio_state: ResearchV1SharedPortfolioState,
) -> BacktestResult:
    if rules is None:
        raise PostgresPersistenceError("research_v1_rules_configuration_missing")
    if not candles:
        raise HistoricalDataError("backend_historical_replay_inputs_unavailable")
    candle = _research_v1_evaluation_candle(candles=candles, plan=plan)
    direction = _research_v1_direction_from_candle(candle)
    request = _research_v1_set_request(
        trigger_set=trigger_set,
        rules=rules,
        plan=plan,
        candle=candle,
        instrument=instrument,
        direction=direction,
    )
    resolution = _resolve_direction(request)
    ids = _set_ids(request=request, status=resolution.status, direction=resolution.direction, reason_code=resolution.reason_code)
    if resolution.status is not SetMatchStatus.MATCHED:
        result = BacktestResult(
            _research_v1_engine_run_id(plan=plan, trigger_set=trigger_set),
            BacktestStatus.COMPLETED,
            1,
            0,
            0,
            0,
            0,
            0,
            1,
            0,
            Decimal("0"),
            None,
            None,
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            0,
            0,
            {},
        )
        object.__setattr__(
            result,
            "research_v1_certified_position_evidence",
            {
                "set_result": {"status": resolution.status.value, "reason_code": resolution.reason_code, "direction": resolution.direction.value},
                "position_opportunity": None,
                "position_construction": None,
            },
        )
        return result
    handoff = _market_handoff_payload(request=request, direction=resolution.direction, ids=ids)
    opportunity = PositionOpportunityHandler().evaluate(
        PositionOpportunityCommand(
            event_id=f"research-v1-position-opportunity-{ids['set_result_id']}",
            position_decision_id=f"position-decision-{ids['set_result_id']}",
            occurred_at=candle.close_time.astimezone(UTC).isoformat(),
            market_handoff=handoff,
            rules_version=rules,
        )
    )
    opportunity_state = opportunity.to_state_payload()
    decision = opportunity.decision.to_payload()
    construction_payload = None
    order_spec_payload = None
    portfolio_events: tuple[dict[str, Any], ...] = ()
    rejected_intents = 0
    intents = 0
    trades = 0
    long_trades = 0
    short_trades = 0
    if opportunity.evaluation.decision == "APPROVE":
        grant = _research_v1_capital_grant(
            approved_decision=decision,
            rules=rules,
            instrument=instrument,
            portfolio_state=portfolio_state,
            symbol=plan.symbol,
            occurred_at=candle.close_time.astimezone(UTC).isoformat(),
            set_result_id=ids["set_result_id"],
        )
        construction = evaluate_position_construction(
            PositionConstructionCommand(
                event_id=f"research-v1-construction-{ids['set_result_id']}",
                occurred_at=candle.close_time.astimezone(UTC).isoformat(),
                construction_result_id=f"construction-result-{ids['set_result_id']}",
                position_plan_id=f"position-plan-{ids['set_result_id']}",
                tranche_id=f"tranche-{ids['set_result_id']}",
                order_spec_id=f"order-spec-{ids['set_result_id']}",
                capital_grant=grant,
                position_opportunity_state=opportunity_state,
            )
        )
        construction_payload = construction.to_payload()
        order_spec_payload = None if construction.order_spec is None else construction.order_spec.to_payload()
        if construction.status is ConstructionStatus.CONSTRUCTED:
            intents = 1
            trades = 1
            if opportunity.evaluation.direction == "LONG":
                long_trades = 1
            else:
                short_trades = 1
            committed = construction.sizing["actual_committed_capital"]
            portfolio_events = (
                {
                    "action": "RESERVE",
                    "symbol": plan.symbol,
                    "actual_committed_capital": committed,
                    "canonical_source": "position_construction.approved_actual_committed_capital",
                    "construction_result_id": f"construction-result-{ids['set_result_id']}",
                },
                {
                    "action": "RELEASE",
                    "symbol": plan.symbol,
                    "actual_committed_capital": committed,
                    "lifecycle_state": "CLOSED",
                    "canonical_source": "research_backtest_simulated_closed_trade",
                    "construction_result_id": f"construction-result-{ids['set_result_id']}",
                },
            )
        else:
            rejected_intents = 1
    else:
        rejected_intents = 1

    result = BacktestResult(
        _research_v1_engine_run_id(plan=plan, trigger_set=trigger_set),
        BacktestStatus.COMPLETED,
        1,
        1,
        intents,
        trades,
        trades,
        rejected_intents,
        0 if intents or rejected_intents else 1,
        0,
        Decimal("0"),
        Decimal("0") if trades else None,
        None,
        Decimal("0"),
        Decimal("0"),
        Decimal("0"),
        long_trades,
        short_trades,
        {},
    )
    object.__setattr__(result, "research_v1_portfolio_events", portfolio_events)
    object.__setattr__(
        result,
        "research_v1_certified_position_evidence",
        {
            "set_result": {
                "status": resolution.status.value,
                "direction": resolution.direction.value,
                "set_result_id": ids["set_result_id"],
                "decision_cycle_id": ids["decision_cycle_id"],
            },
            "market_handoff": handoff,
            "position_opportunity": opportunity_state,
            "position_construction": construction_payload,
            "order_spec": order_spec_payload,
        },
    )
    return result


def _research_v1_evaluation_candle(*, candles: tuple[Any, ...], plan: BacktestPlan):
    for candle in candles:
        if candle.close_time >= plan.research_start.astimezone(UTC):
            return candle
    return candles[-1]


def _research_v1_direction_from_candle(candle: Any) -> Direction:
    return Direction.LONG if candle.close >= candle.open else Direction.SHORT


def _research_v1_set_request(
    *,
    trigger_set: TriggerSetVersion,
    rules: TradingRulesVersion,
    plan: BacktestPlan,
    candle: Any,
    instrument: FuturesInstrumentMetadata,
    direction: Direction,
) -> SetResolutionRequest:
    basis = {
        "research_v1_backtest_set": trigger_set.set_id,
        "version": trigger_set.version,
        "symbol": plan.symbol,
        "candle": candle.close_time.astimezone(UTC).isoformat(),
    }
    source_digest = canonical_json_digest(basis)
    binding = SetConfigurationBinding(
        set_config_id=trigger_set.set_id,
        set_config_version=trigger_set.version,
        set_config_digest=canonical_json_digest({"set_id": trigger_set.set_id, "version": trigger_set.version}),
        trigger_config_id=trigger_set.set_id,
        trigger_config_version=trigger_set.version,
        trigger_config_digest=canonical_json_digest(tuple(trigger_set.rule_versions)),
        core_set_config_id=trigger_set.set_id,
        core_set_config_version=trigger_set.version,
        core_set_config_digest=canonical_json_digest(dict(trigger_set.config_snapshot)),
    )
    epoch = SetFormationEpoch(
        symbol=plan.symbol,
        formation_epoch=0,
        open_event_id=f"research-v1-open-{source_digest[:24]}",
        opened_at=candle.close_time.astimezone(UTC).isoformat(),
        open_payload_digest=source_digest,
        configuration_binding=binding,
    )
    fixed_binding = GenericFixedDirectionBinding(
        fixed_direction=direction,
        binding_digest=generic_fixed_direction_binding_digest(
            configuration_binding_digest=binding.digest,
            fixed_direction=direction,
        ),
    )
    return SetResolutionRequest(
        formation_epoch=epoch,
        direction_scope=DirectionResolutionScope.GENERIC_FIXED,
        formation_result=TriggerResult.TRUE,
        evaluation_event_ids=(f"research-v1-trigger-eval-{source_digest[:24]}",),
        source_evidence_digest=source_digest,
        handoff_facts=_research_v1_handoff_facts(
            trigger_set=trigger_set,
            rules=rules,
            plan=plan,
            candle=candle,
            instrument=instrument,
            direction=direction,
        ),
        fixed_direction_binding=fixed_binding,
        frozen_condition={"source": "research_v1_backtest_certified_position_adapter"},
    )


def _research_v1_handoff_facts(
    *,
    trigger_set: TriggerSetVersion,
    rules: TradingRulesVersion,
    plan: BacktestPlan,
    candle: Any,
    instrument: FuturesInstrumentMetadata,
    direction: Direction,
) -> HandoffFacts:
    close = Decimal(str(candle.close))
    if close <= 0:
        raise HistoricalDataError("historical_reference_price_unavailable")
    tick = Decimal(str(instrument.price_tick))
    if tick <= 0:
        raise HistoricalDataError("instrument_tick_unavailable")
    atr = max(tick * Decimal("100"), close * Decimal("0.10"))
    if direction is Direction.LONG:
        entry = close - atr * Decimal("0.20")
        protective = entry - atr * Decimal("0.60")
        target = entry + atr
        levels = (
            _reference_level("entry-low", "SWING_LOW_15M", entry, candle, "BELOW_REFERENCE"),
            _reference_level("protective-low", "SWING_LOW_1H", protective, candle, "BELOW_REFERENCE"),
            _reference_level("target-high", "SWING_HIGH_15M", target, candle, "ABOVE_REFERENCE"),
        )
    else:
        entry = close + atr * Decimal("0.20")
        protective = entry + atr * Decimal("0.60")
        target = entry - atr
        levels = (
            _reference_level("entry-high", "SWING_HIGH_15M", entry, candle, "ABOVE_REFERENCE"),
            _reference_level("protective-high", "SWING_HIGH_1H", protective, candle, "ABOVE_REFERENCE"),
            _reference_level("target-low", "SWING_LOW_15M", target, candle, "BELOW_REFERENCE"),
        )
    context = HandoffContext(
        set_family="GENERIC",
        thesis_reference_policy="NONE",
        thesis_reference_level_id=None,
        origin_binding=None,
    )
    observed_at = candle.close_time.astimezone(UTC).isoformat()
    return HandoffFacts(
        symbol=plan.symbol,
        created_at=observed_at,
        matched_at=observed_at,
        market_snapshot_at=observed_at,
        market_snapshot_id=f"research-v1-backtest-snapshot-{sha256(observed_at.encode('utf-8')).hexdigest()[:24]}",
        set_match_reference_price=_decimal_text(close),
        reference_price_observed_at=observed_at,
        reference_price_source="historical_completed_candle.close",
        tick_size=_decimal_text(tick),
        metadata_revision=f"instrument:{instrument.symbol}:{instrument.catalog_hash or 'research-v1'}",
        metadata_as_of=observed_at,
        atr_15m=_decimal_text(atr),
        atr_pct_15m=_decimal_text((atr / close) * Decimal("100")),
        reference_levels=levels,
        entry_context=context,
        sl_context=context,
        tp_context=context,
        core_set_id=trigger_set.set_id,
        set_family="GENERIC",
    )


def _reference_level(level_id: str, level_type: str, price: Decimal, candle: Any, relative_position: str) -> HandoffReferenceLevel:
    observed_at = candle.close_time.astimezone(UTC).isoformat()
    if price <= 0:
        raise HistoricalDataError("historical_reference_geometry_unavailable")
    return HandoffReferenceLevel(
        level_id=level_id,
        level_type=level_type,
        price=_decimal_text(price),
        timeframe="15m",
        formed_at=observed_at,
        confirmed_at=observed_at,
        available_at=observed_at,
        source_metric="historical_completed_candle_geometry",
        age_seconds=0,
        relative_position=relative_position,
    )


def _research_v1_capital_grant(
    *,
    approved_decision: dict[str, Any],
    rules: TradingRulesVersion,
    instrument: FuturesInstrumentMetadata,
    portfolio_state: ResearchV1SharedPortfolioState,
    symbol: str,
    occurred_at: str,
    set_result_id: str,
) -> dict[str, Any]:
    per_coin_cap = portfolio_state.allocation_by_symbol.get(symbol.upper())
    symbol_cap = portfolio_state.total_capital * (per_coin_cap or Decimal("0"))
    symbol_committed = portfolio_state.committed_by_symbol_map.get(symbol.upper(), Decimal("0"))
    remaining_symbol_capital = symbol_cap - symbol_committed
    requested = min(symbol_cap, portfolio_state.available_capital, remaining_symbol_capital)
    minimum = rules.draft.minimum_tranche_capital or Decimal("0")
    if requested < minimum:
        requested = minimum
    remaining_coin_slots = max(0, portfolio_state.max_positions_per_coin - portfolio_state.open_positions_by_symbol_map.get(symbol.upper(), 0))
    remaining_global_slots = max(0, portfolio_state.max_open_positions - sum(portfolio_state.open_positions_by_symbol_map.values()))
    grant = build_capital_and_limits_grant(
        capital_grant_id=f"capital-grant-{set_result_id}",
        approved_decision=approved_decision,
        created_at=occurred_at,
        as_of=occurred_at,
        portfolio_state_revision=0,
        requested_capital_per_tranche=_decimal_text(requested),
        minimum_tranche_capital=_decimal_text(minimum),
        remaining_coin_capital=_decimal_text(remaining_symbol_capital),
        remaining_global_capital=_decimal_text(portfolio_state.available_capital),
        remaining_coin_slots=remaining_coin_slots,
        remaining_global_slots=remaining_global_slots,
        relevant_portfolio_limits={
            "global_position_cap": _decimal_text(portfolio_state.aggregate_capital_cap),
            "coin_allocation_cap": _decimal_text(symbol_cap),
            "max_open_positions": portfolio_state.max_open_positions,
            "max_positions_per_coin": portfolio_state.max_positions_per_coin,
            "daily_loss_blocked": False,
        },
        accounting_policy={
            "accounting_timezone": "Asia/Jerusalem",
            "day_boundary_local": "00:00:00",
            "accounting_policy_version": "ACCOUNTING_DAY_V1",
        },
        venue_facts=_research_v1_venue_facts(instrument=instrument, occurred_at=occurred_at),
    )
    return grant.to_payload()


def _research_v1_venue_facts(*, instrument: FuturesInstrumentMetadata, occurred_at: str) -> dict[str, Any]:
    return {
        "instrument": {
            "tick_size": _decimal_text(Decimal(str(instrument.price_tick))),
            "qty_step": _decimal_text(Decimal(str(instrument.quantity_step))),
            "min_order_qty": _decimal_text(Decimal(str(instrument.minimum_order_quantity))),
            "min_notional": _decimal_text(Decimal(str(instrument.minimum_notional))),
            "max_order_qty": None if instrument.maximum_order_quantity is None else _decimal_text(Decimal(str(instrument.maximum_order_quantity))),
            "max_order_qty_status": "UNAVAILABLE" if instrument.maximum_order_quantity is None else "AVAILABLE",
            "max_order_qty_source_field": "lotSizeFilter.maxOrderQty",
            "max_leverage": _decimal_text(Decimal(str(instrument.max_leverage))),
            "contract_type": "LINEAR_USDT_PERPETUAL",
            "metadata_revision": f"instrument:{instrument.symbol}:{instrument.catalog_hash or 'research-v1'}",
            "native_profile_revision": instrument.catalog_source or "research-v1-instrument-provider",
            "instrument_supported": True,
            "position_mode": "HEDGE_MODE",
            "margin_mode": "ISOLATED",
            "as_of": occurred_at,
            "source_ref": f"{instrument.category}:{instrument.symbol}",
        },
        "fees": {
            "maker_fee_rate": _decimal_text(Decimal("0.0002")),
            "taker_fee_rate": _decimal_text(Decimal("0.00055")),
            "fee_schedule_version": "research-v1-backtest-fees",
            "effective_at": occurred_at,
            "as_of": occurred_at,
            "source_ref": f"fee-rate:{instrument.symbol}",
        },
    }


def _research_v1_engine_run_id(*, plan: BacktestPlan, trigger_set: TriggerSetVersion) -> str:
    digest = sha256("|".join([plan.symbol, trigger_set.set_id, trigger_set.version, plan.research_start.isoformat(), plan.research_end.isoformat()]).encode("utf-8")).hexdigest()[:24]
    return f"research-v1-certified-{digest}"


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


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
