"""Continuous Bybit Demo linear futures runtime integration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import time
from typing import Callable

from triggertrade.accounting import calculate_drawdown_snapshot
from triggertrade.config import AppConfig, BybitEnvironment, ConfigError, ExecutionVenue, Market, TradingMode
from triggertrade.execution import OrderStatus, OrderType
from triggertrade.execution.service import ExecutionError
from triggertrade.execution.bybit_futures import BybitFuturesExecutionAdapter
from triggertrade.execution.futures import (
    FundingEstimate,
    FuturesExecutionConfig,
    FuturesExecutionService,
    FuturesRiskManager,
    FuturesTradeIntent,
    PositionAction,
    PositionState,
    estimate_costs,
)
from triggertrade.execution.position_lifecycle import build_fixed_protective_exit_plan
from triggertrade.execution.position_lifecycle import FuturesPositionLifecycleService, PositionRiskConfig, calculate_position_size, instrument_metadata_from_position_snapshot
from triggertrade.exchanges import BybitApiError, BybitDemoClient
from triggertrade.instruments import CatalogError
from triggertrade.market_data import (
    FuturesAccountState,
    FuturesInstrumentMetadata,
    MarketRegimeContext,
    RegimeEvaluationWindow,
    evaluate_market_regime,
    futures_event_from_completed_candle,
    parse_linear_instrument,
    parse_spot_candles,
    volume_window_from_futures_event,
)
from triggertrade.market_data.futures import ContractCategory, MarketRegimeLabel
from triggertrade.persistence import (
    DailyLossStore,
    FuturesExecutionStore,
    InstrumentCatalogStore,
    TradingRulesStore,
    LaneCandleLifecycle,
    LaneRuntimeCheckpoint,
    MessageStore,
    MessageSeverity,
    OperatorStateStore,
    RuntimeHeartbeat,
    RuntimeStore,
    TraceStore,
    TriggerSetStore,
)
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.persistence.futures_position_store import FuturesPositionStore
from triggertrade.services.daily_loss import DailyLossEvaluator
from triggertrade.services.futures_accounting_bridge import FuturesAccountingBridge
from triggertrade.services.instrument_catalog import InstrumentCatalogService
from triggertrade.services.runtime import CompletedCandle, RuntimeCycleResult, RuntimeGapError, candle_id, interval_delta, latest_completed_candle, next_completed_candle
from triggertrade.services.test_futures_simulator import TestFuturesSimulator
from triggertrade.rules import DirectionMode, TakeProfitMode, TradingRulesError, TradingRulesService, TradingRulesVersion, coin_rule_for
from triggertrade.strategies import IntegrationDirectionalFuturesStrategy
from triggertrade.trigger_sets import Lane, TriggerSetStatus, TriggerSetVersion
from triggertrade.triggers import PercentagePriceMoveTrigger, RobustVolumeConfirmationTrigger, Signal, SignalType, VolumeConfirmationConfig, VolumeConfirmationResult


@dataclass(frozen=True)
class FuturesDualLaneResult:
    candle_id: str | None
    active: tuple[RuntimeCycleResult, ...]
    test: tuple[RuntimeCycleResult, ...]
    skipped_reason: str | None = None


_RECOVERY_PAGE_LIMIT = 200
_RECOVERY_BATCH_CANDLES = 200
_MAX_RECOVERY_PAGE_REQUESTS = 10000
_RECOVERY_SUCCESS_STATUSES = {
    "no_signal",
    "no_intent",
    "risk_rejected",
    "test_simulated",
    "completed",
    "active_execution_paused",
    "stale_entry_suppressed",
}


class FuturesDualLaneRuntime:
    """Fan out one canonical linear futures market event into ACTIVE and TEST lanes."""

    def __init__(
        self,
        *,
        config: AppConfig,
        market_client: BybitDemoClient,
        futures_execution_store: FuturesExecutionStore,
        accounting_store: FuturesAccountingStore,
        trace_store: TraceStore,
        runtime_store: RuntimeStore,
        trigger_set_store: TriggerSetStore,
        operator_state_store: OperatorStateStore,
        daily_loss_store: DailyLossStore | None = None,
        message_store: MessageStore | None = None,
        position_store: FuturesPositionStore | None = None,
        active_adapter: BybitFuturesExecutionAdapter | None = None,
        test_simulator: TestFuturesSimulator | None = None,
        account_provider: Callable[[FuturesInstrumentMetadata], FuturesAccountState] | None = None,
        instrument_catalog: InstrumentCatalogService | None = None,
        clock: Callable[[], datetime] | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        self._config = config
        self._market_client = market_client
        self._futures_execution_store = futures_execution_store
        self._accounting_store = accounting_store
        self._trace_store = trace_store
        self._runtime_store = runtime_store
        self._trigger_set_store = trigger_set_store
        self._operator_state_store = operator_state_store
        self._daily_loss_store = daily_loss_store or DailyLossStore(config.futures_runtime.db_path)
        self._message_store = message_store or MessageStore(config.futures_runtime.db_path)
        self._position_store = position_store or FuturesPositionStore(config.futures_runtime.db_path)
        self._instrument_catalog = instrument_catalog or InstrumentCatalogService(
            store=InstrumentCatalogStore(config.futures_runtime.db_path),
            client=market_client,
        )
        self._trading_rules_store = TradingRulesStore(config.futures_runtime.db_path)
        self._trading_rules_service = TradingRulesService(self._trading_rules_store, symbol_validator=self._instrument_catalog.validate_symbol)
        self._trading_rules_service.ensure_initial_version(config)
        self._active_adapter = active_adapter or BybitFuturesExecutionAdapter(market_client)
        self._test_simulator = test_simulator or TestFuturesSimulator(
            accounting_store=accounting_store,
            maker_fee_rate=config.futures_runtime.maker_fee_rate,
        )
        self._account_provider = account_provider
        self._clock = clock or (lambda: datetime.now(UTC))
        self._logger = logger or (lambda message: print(message))
        self._stop_requested = False
        self._account_snapshot_sequence = 0

    def process_once(self) -> FuturesDualLaneResult:
        self._validate_safe_config()
        try:
            instrument = self._resolve_runtime_instrument()
            candles = parse_spot_candles(
                self._market_client.linear_recent_candles(
                    self._config.futures_runtime.symbol,
                    interval=_bybit_interval(self._config.futures_runtime.candle_interval),
                    limit=70,
                ).result
            )
            active_pair = self._trigger_set_store.get_active_trading_pair(self._config.futures_runtime.symbol, "1m")
            active_set = active_pair.trigger_set if active_pair is not None else None
            active_checkpoint = _lane_checkpoint(self._runtime_store, Lane.ACTIVE, active_set) if active_set else None
            try:
                completed = next_completed_candle(
                    candles,
                    symbol=self._config.futures_runtime.symbol,
                    timeframe="1m",
                    now=self._clock(),
                    checkpoint=active_checkpoint,
                )
            except RuntimeGapError:
                if active_set is None or active_checkpoint is None:
                    raise
                return self._recover_active_checkpoint_gap(
                    instrument=instrument,
                    recent_candles=candles,
                    active_pair=active_pair,
                    active_set=active_set,
                    active_checkpoint=active_checkpoint,
                )
            if completed is None:
                if active_checkpoint is not None:
                    latest = latest_completed_candle(
                        candles,
                        symbol=self._config.futures_runtime.symbol,
                        timeframe="1m",
                        now=self._clock(),
                    )
                    if latest is not None:
                        checkpoint_open = _aware_utc(datetime.fromisoformat(active_checkpoint.last_processed_candle_open_time))
                        if checkpoint_open > latest.open_time:
                            raise RuntimeGapError("checkpoint is ahead of latest completed exchange candle")
                        if checkpoint_open == latest.open_time:
                            completed = latest
                else:
                    completed = latest_completed_candle(
                        candles,
                        symbol=self._config.futures_runtime.symbol,
                        timeframe="1m",
                        now=self._clock(),
                    )
        except RuntimeGapError as exc:
            self._log(f"futures runtime checkpoint gap: {exc.__class__.__name__}")
            return FuturesDualLaneResult(None, (), (), "checkpoint_gap")
        except CatalogError as exc:
            self._recover_and_monitor_active_positions_from_snapshots()
            self._log(f"futures instrument catalog unavailable: {exc.__class__.__name__}")
            return FuturesDualLaneResult(None, (), (), "market_data_unavailable")
        except (BybitApiError, ValueError) as exc:
            self._log(f"futures market data unavailable: {exc.__class__.__name__}")
            return FuturesDualLaneResult(None, (), (), "market_data_unavailable")
        if completed is None:
            return FuturesDualLaneResult(None, (), (), "no_completed_candle")

        active_account = None
        try:
            active_account = self._refresh_active_account_snapshot(instrument)
        except (BybitApiError, ValueError, ExecutionError) as exc:
            self._log(f"futures account data unavailable: {exc.__class__.__name__}")
            return FuturesDualLaneResult(completed.candle_id, (), (), "account_data_unavailable")
        if active_set is not None:
            self._recover_active_unresolved(instrument, active_account)
            self._monitor_active_positions(instrument, active_account)

        event = futures_event_from_completed_candle(
            completed=completed,
            source="bybit_demo_linear_kline",
            instrument_version=f"{instrument.contract_type}:{instrument.settlement_asset}",
        )
        regime_context = evaluate_market_regime(
            RegimeEvaluationWindow(
                symbol=event.symbol,
                timeframe=event.timeframe,
                observed_at=event.close_time,
                candles=tuple(
                    candle
                    for candle in sorted(candles, key=lambda item: item.start_time_ms)
                    if candle.start_time_ms <= completed.candle.start_time_ms
                ),
                category=event.category,
                current_candle_completed=True,
            )
        )
        self._runtime_store.save_market_regime(regime_context)

        active_results = ()
        if active_set is not None:
            active_results = (
                self._process_lane(
                    lane=Lane.ACTIVE,
                    trigger_set=active_set,
                    completed=completed,
                    event=event,
                    instrument=instrument,
                    candles=candles,
                    regime_context=regime_context,
                    rules_version=active_pair.rules_version if active_pair is not None else None,
                    account=active_account,
                ),
            )
        test_results = tuple(
            self._process_lane(
                lane=Lane.TEST,
                trigger_set=trigger_set,
                completed=completed,
                event=event,
                instrument=instrument,
                candles=candles,
                regime_context=regime_context,
            )
            for trigger_set in self._trigger_set_store.list_testing_sets(event.symbol, event.timeframe)
        )
        return FuturesDualLaneResult(completed.candle_id, active_results, test_results)

    def run_forever(self, max_cycles: int | None = None) -> None:
        cycles = 0
        while not self._stop_requested:
            self._record_heartbeat("RUNNING", "cycle starting")
            try:
                result = self.process_once()
            except Exception as exc:
                self._record_heartbeat("BLOCKED", exc.__class__.__name__)
                raise
            cycles += 1
            status, detail = _heartbeat_outcome(result)
            self._record_heartbeat(status, detail)
            if max_cycles is not None and cycles >= max_cycles:
                break
            time.sleep(self._config.futures_runtime.poll_interval_seconds)

    def stop(self) -> None:
        self._stop_requested = True

    def _process_lane(
        self,
        *,
        lane: Lane,
        trigger_set: TriggerSetVersion,
        completed: CompletedCandle,
        event,
        instrument: FuturesInstrumentMetadata,
        candles,
        regime_context: MarketRegimeContext,
        rules_version: TradingRulesVersion | None = None,
        account: FuturesAccountState | None = None,
        recovery_mode: bool = False,
    ) -> RuntimeCycleResult:
        if trigger_set.status not in {TriggerSetStatus.ACTIVE, TriggerSetStatus.TESTING}:
            return RuntimeCycleResult(completed.candle_id, None, skipped_reason="set_not_eligible")
        if not _is_futures_set(trigger_set):
            return RuntimeCycleResult(completed.candle_id, None, skipped_reason="non_futures_set")
        existing = self._runtime_store.get_lane_lifecycle(
            lane=lane.value,
            symbol=completed.symbol,
            timeframe=completed.timeframe,
            candle_id=completed.candle_id,
            trigger_set_id=trigger_set.set_id,
            trigger_set_version=trigger_set.version,
        )
        if existing is not None and existing.status in _RECOVERY_SUCCESS_STATUSES:
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, None, skipped_reason="already_processed")

        signal = self._price_signal(lane=lane, trigger_set=trigger_set, completed=completed, event=event)
        self._trace_store.save_trigger_evaluation(signal)
        self._save_lane_lifecycle(lane, trigger_set, completed, "trigger_evaluated", signal_id=signal.signal_id, regime_context=regime_context)
        if signal.signal_type is SignalType.NO_SIGNAL:
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "no_signal",
                signal_id=signal.signal_id,
                processed_at=self._clock().isoformat(),
                regime_context=regime_context,
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value)

        signal_ids = [signal.signal_id]
        volume_signal = None
        if ("TRG-002", "0.2.0") in trigger_set.rule_versions:
            volume_signal = self._volume_signal(lane=lane, trigger_set=trigger_set, completed=completed, event=event, candles=candles)
            self._trace_store.save_trigger_evaluation(volume_signal)
            signal_ids.append(volume_signal.signal_id)
            if volume_signal.signal_type is not SignalType.CONFIRMED:
                self._save_lane_lifecycle(
                    lane,
                    trigger_set,
                    completed,
                    "no_intent",
                    signal_id=signal.signal_id,
                    processed_at=self._clock().isoformat(),
                    error=volume_signal.reason,
                    regime_context=regime_context,
                )
                self._checkpoint_lane(lane, trigger_set, completed)
                return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, skipped_reason="volume_not_confirmed")

        rules_version = rules_version or self._trading_rules_service.get_current_rules_version()
        rules = rules_version.draft
        rules_skip = _rules_skip_reason(rules_version, event.symbol)
        if rules_skip is not None:
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "no_intent",
                signal_id=signal.signal_id,
                processed_at=self._clock().isoformat(),
                error=rules_skip,
                regime_context=regime_context,
                rules_version_id=rules_version.rules_version_id,
                rules_evaluation=_rules_rejection_evidence(rules_version, rules_skip, event.symbol),
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, skipped_reason=rules_skip)

        if recovery_mode:
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "stale_entry_suppressed",
                signal_id=signal.signal_id,
                processed_at=self._clock().isoformat(),
                error="recovery_backfill_no_stale_execution",
                regime_context=regime_context,
                rules_version_id=rules_version.rules_version_id,
                rules_evaluation={
                    "rules_version_id": rules_version.rules_version_id,
                    "recovery_mode": "checkpoint_backfill",
                    "stale_entry_suppressed": "true",
                },
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, skipped_reason="stale_entry_suppressed")

        price = _intent_price(event.close, instrument, passive=lane is Lane.ACTIVE)
        account = account if lane is Lane.ACTIVE and account is not None else self._account_state(instrument, lane)
        try:
            position_risk = _position_risk_config_from_rules(rules_version, account)
            sizing = calculate_position_size(
                account=account,
                instrument=instrument,
                entry_price=price,
                leverage=rules.leverage,
                config=position_risk,
            )
        except ExecutionError as exc:
            reason = str(exc)
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "no_intent",
                signal_id=signal.signal_id,
                processed_at=self._clock().isoformat(),
                error=reason,
                regime_context=regime_context,
                rules_version_id=rules_version.rules_version_id,
                rules_evaluation=_rules_rejection_evidence(rules_version, reason, event.symbol),
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, skipped_reason=reason)

        decision = IntegrationDirectionalFuturesStrategy().decide(
            lane=lane,
            trigger_set=trigger_set,
            event=event,
            primary_signal=signal,
            volume_signal=volume_signal,
            regime_context=regime_context,
            position_state=_position_state(account),
            quantity=sizing.quantity,
            limit_price=price,
            leverage=rules.leverage,
            expected_gross_move=self._config.futures_runtime.demo_expected_gross_move,
            created_at=self._clock(),
            expected_gross_move_required=rules.minimum_net_edge_enabled,
        )
        if decision.intent is None:
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "no_intent",
                signal_id=signal.signal_id,
                processed_at=self._clock().isoformat(),
                error=decision.reason,
                regime_context=regime_context,
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, skipped_reason=decision.reason)

        intent = decision.intent
        direction_skip = _direction_skip_reason(rules_version, intent.action)
        if direction_skip is not None:
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "no_intent",
                signal_id=signal.signal_id,
                intent_id=intent.intent_id,
                processed_at=self._clock().isoformat(),
                error=direction_skip,
                regime_context=regime_context,
                rules_version_id=rules_version.rules_version_id,
                rules_evaluation=_rules_rejection_evidence(rules_version, direction_skip, event.symbol),
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, skipped_reason=direction_skip)

        daily_loss = None
        if lane is Lane.ACTIVE and intent.action in {PositionAction.OPEN_LONG, PositionAction.OPEN_SHORT}:
            daily_loss = DailyLossEvaluator(
                accounting_store=self._accounting_store,
                daily_loss_store=self._daily_loss_store,
                message_store=self._message_store,
            ).evaluate(rules_version=rules_version, now=self._clock(), account=account, notify=True)
            if daily_loss.blocked:
                reason = daily_loss.reason or daily_loss.status.lower()
                self._save_lane_lifecycle(
                    lane,
                    trigger_set,
                    completed,
                    "no_intent",
                    signal_id=signal.signal_id,
                    intent_id=intent.intent_id,
                    processed_at=self._clock().isoformat(),
                    error=reason,
                    regime_context=regime_context,
                    rules_version_id=rules_version.rules_version_id,
                    rules_evaluation={
                        **_rules_rejection_evidence(rules_version, reason, event.symbol),
                        **_prefixed_daily_loss_evidence(daily_loss.evidence()),
                    },
                )
                self._checkpoint_lane(lane, trigger_set, completed)
                return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, skipped_reason=reason)

        take_profit, stop_loss = build_fixed_protective_exit_plan(
            action=intent.action,
            entry_price=intent.price,
            take_profit_pct=_fixed_take_profit_pct(rules_version),
            stop_loss_pct=rules.stop_loss_pct,
            price_tick=instrument.price_tick,
            calculated_at=self._clock().isoformat(),
        )
        intent = replace(
            intent,
            take_profit=take_profit,
            stop_loss=stop_loss,
            minimum_risk_reward=rules.minimum_risk_reward,
            rules_version_id=rules_version.rules_version_id,
            rule_evaluation_snapshot=_rule_evaluation_snapshot(rules_version, sizing, account, daily_loss=daily_loss),
        )
        self._trace_store.save_futures_strategy_decision(intent, tuple(signal_ids))
        if lane is Lane.ACTIVE:
            existing = self._futures_execution_store.get_by_intent(intent.intent_id)
            if existing is not None:
                service = FuturesExecutionService(
                    config=_execution_config(self._config),
                    adapter=self._active_adapter,
                    store=self._futures_execution_store,
                    instrument=instrument,
                    account=account,
                    execution_lane=lane.value,
                    operator_trading_state=self._operator_state_value,
                )
                record = service.reconcile(existing)
                FuturesAccountingBridge(accounting_store=self._accounting_store, adapter=self._active_adapter).ingest_execution(
                    record=record,
                    intent=intent,
                )
                if record.status is OrderStatus.UNKNOWN:
                    self._save_lane_lifecycle(
                        lane,
                        trigger_set,
                        completed,
                        "execution_unknown",
                        signal_id=signal.signal_id,
                        intent_id=intent.intent_id,
                        risk_decision_id=record.risk_decision_id,
                        execution_intent_id=record.intent_id,
                        error="execution_reconciliation_unknown",
                        regime_context=regime_context,
                    )
                    return RuntimeCycleResult(
                        completed.candle_id,
                        signal.signal_type.value,
                        intent.intent_id,
                        record.risk_decision_id,
                        True,
                        record.status.value,
                        "execution_unknown",
                    )
                self._save_lane_lifecycle(
                    lane,
                    trigger_set,
                    completed,
                    "completed",
                    signal_id=signal.signal_id,
                    intent_id=intent.intent_id,
                    risk_decision_id=record.risk_decision_id,
                    execution_intent_id=record.intent_id,
                    processed_at=self._clock().isoformat(),
                    regime_context=regime_context,
                )
                self._checkpoint_lane(lane, trigger_set, completed)
                return RuntimeCycleResult(
                    completed.candle_id,
                    signal.signal_type.value,
                    intent.intent_id,
                    record.risk_decision_id,
                    True,
                    record.status.value,
                )
        cost = estimate_costs(
            notional=intent.quantity * intent.price,
            maker_fee_rate=rules.maker_fee_rate,
            taker_fee_rate=rules.taker_fee_rate,
            spread_cost=rules.spread_cost,
            slippage_cost=rules.slippage_cost,
            funding_cost=rules.funding_cost,
        )
        funding = FundingEstimate(
            funding_rate=None,
            next_funding_time=None,
            expected_holding_overlap=Decimal("0"),
            estimated_funding_impact=rules.funding_cost,
        )
        rules_evaluation = _rule_evaluation_snapshot(rules_version, sizing, account, daily_loss=daily_loss)
        risk = FuturesRiskManager(
            config=_execution_config(self._config),
            store=self._futures_execution_store,
            minimum_net_edge=rules.minimum_net_edge_pct if rules.minimum_net_edge_enabled else None,
            max_position_notional=position_risk.max_position_notional,
            max_simultaneous_exposure=position_risk.max_total_position_notional,
        ).evaluate(intent=intent, instrument=instrument, account=account, cost=cost, funding=funding)
        self._trace_store.save_futures_risk_decision(risk, trigger_set_id=trigger_set.set_id, trigger_set_version=trigger_set.version)
        self._save_lane_lifecycle(
            lane,
            trigger_set,
            completed,
            "risk_recorded",
            signal_id=signal.signal_id,
            intent_id=intent.intent_id,
            risk_decision_id=risk.risk_decision_id,
            regime_context=regime_context,
            rules_version_id=rules_version.rules_version_id,
            rules_evaluation=rules_evaluation,
        )
        if not risk.approved:
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "risk_rejected",
                signal_id=signal.signal_id,
                intent_id=intent.intent_id,
                risk_decision_id=risk.risk_decision_id,
                processed_at=self._clock().isoformat(),
                regime_context=regime_context,
                rules_version_id=rules_version.rules_version_id,
                rules_evaluation=rules_evaluation,
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, False)

        if lane is Lane.TEST:
            result = self._test_simulator.simulate_closed_trade(intent=intent, event=event)
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "test_simulated",
                signal_id=signal.signal_id,
                intent_id=intent.intent_id,
                risk_decision_id=risk.risk_decision_id,
                execution_intent_id=result.trade_id,
                processed_at=self._clock().isoformat(),
                regime_context=regime_context,
                rules_version_id=rules_version.rules_version_id,
                rules_evaluation=rules_evaluation,
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, True, "test_simulated")

        try:
            lifecycle = FuturesPositionLifecycleService(
                execution_config=_execution_config(self._config),
                risk_config=position_risk,
                execution_store=self._futures_execution_store,
                position_store=self._position_store,
                accounting_store=self._accounting_store,
                adapter=self._active_adapter,
                instrument=instrument,
                account=account,
                execution_lane=lane.value,
                operator_trading_state=self._operator_state_value,
                trading_rules_store=self._trading_rules_store,
            )
            opened = lifecycle.open_position(
                intent=intent,
                risk_decision=risk,
                take_profit=take_profit,
                stop_loss=stop_loss,
            )
            record = opened.execution
        except Exception as exc:
            status = "active_execution_paused" if "pause" in str(exc).lower() else "execution_error"
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                status,
                signal_id=signal.signal_id,
                intent_id=intent.intent_id,
                risk_decision_id=risk.risk_decision_id,
                processed_at=self._clock().isoformat() if status == "active_execution_paused" else None,
                error=exc.__class__.__name__ if status != "active_execution_paused" else "operator_paused",
                regime_context=regime_context,
                rules_version_id=rules_version.rules_version_id,
                rules_evaluation=rules_evaluation,
            )
            if status == "active_execution_paused":
                self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, True, skipped_reason=status)

        if record is not None and record.status is OrderStatus.UNKNOWN:
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "execution_unknown",
                signal_id=signal.signal_id,
                intent_id=intent.intent_id,
                risk_decision_id=risk.risk_decision_id,
                execution_intent_id=record.intent_id,
                error="execution_reconciliation_unknown",
                regime_context=regime_context,
                rules_version_id=rules_version.rules_version_id,
                rules_evaluation=rules_evaluation,
            )
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, True, record.status.value, "execution_unknown")

        self._save_lane_lifecycle(
            lane,
            trigger_set,
            completed,
            "completed",
            signal_id=signal.signal_id,
            intent_id=intent.intent_id,
            risk_decision_id=risk.risk_decision_id,
            execution_intent_id=record.intent_id,
            processed_at=self._clock().isoformat(),
            regime_context=regime_context,
            rules_version_id=rules_version.rules_version_id,
            rules_evaluation=rules_evaluation,
        )
        self._checkpoint_lane(lane, trigger_set, completed)
        return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, True, None if record is None else record.status.value)

    def _price_signal(self, *, lane: Lane, trigger_set: TriggerSetVersion, completed: CompletedCandle, event) -> Signal:
        trigger_version = self._trigger_set_store.resolve_trigger_version(trigger_set, "TRG-001").version
        observation = event.to_market_observation(stale_after_seconds=self._config.risk_rules.stale_after_seconds)
        observation = replace(observation, source=f"{observation.source}|{lane.value}|{trigger_set.set_id}|{trigger_set.version}")
        config = replace(self._config.trigger_rule, version=trigger_version)
        signal = PercentagePriceMoveTrigger(config, symbol=self._config.futures_runtime.symbol).evaluate(
            observation,
            now=self._clock(),
        )
        return replace(signal, lane=lane.value, trigger_set_id=trigger_set.set_id, trigger_set_version=trigger_set.version)

    def _volume_signal(self, *, lane: Lane, trigger_set: TriggerSetVersion, completed: CompletedCandle, event, candles) -> Signal:
        trigger_version = self._trigger_set_store.resolve_trigger_version(trigger_set, "TRG-002").version
        previous = tuple(
            candle
            for candle in sorted(candles, key=lambda item: item.start_time_ms)
            if candle.start_time_ms < completed.candle.start_time_ms
        )
        evaluation = RobustVolumeConfirmationTrigger(
            VolumeConfirmationConfig(version=trigger_version, stale_after_seconds=self._config.risk_rules.stale_after_seconds),
            symbol=completed.symbol,
        ).evaluate(
            volume_window_from_futures_event(event, previous_candles=previous[-60:]),
            now=self._clock(),
        )
        return Signal(
            signal_id=evaluation.evaluation_id,
            trigger_rule_id=evaluation.rule_id,
            trigger_rule_version=evaluation.rule_version,
            symbol=evaluation.symbol,
            observed_at=evaluation.observed_at,
            window=evaluation.timeframe,
            input_snapshot={
                "category": "linear",
                "current_volume": evaluation.current_volume or "",
                "median_volume_60": evaluation.median_volume_60 or "",
                "relative_volume": evaluation.relative_volume or "",
                "volume_percentile": evaluation.volume_percentile or "",
                "relative_volume_threshold": evaluation.relative_volume_threshold,
                "percentile_threshold": evaluation.percentile_threshold,
                "missing_data_reason": evaluation.missing_data_reason or "",
                "stale_data_reason": evaluation.stale_data_reason or "",
            },
            condition_result=evaluation.condition_result,
            signal_type=SignalType.CONFIRMED if evaluation.result is VolumeConfirmationResult.CONFIRMED else SignalType.NOT_CONFIRMED,
            reason=evaluation.missing_data_reason or evaluation.stale_data_reason or evaluation.result.value.lower(),
            lane=lane.value,
            trigger_set_id=trigger_set.set_id,
            trigger_set_version=trigger_set.version,
        )

    def _recover_and_monitor_active_positions_from_snapshots(self) -> None:
        for position in self._position_store.list_open_positions(include_unknown=True):
            instrument = instrument_metadata_from_position_snapshot(position)
            if instrument is None:
                continue
            try:
                account = self._account_state(instrument, Lane.ACTIVE)
                lifecycle = FuturesPositionLifecycleService(
                    execution_config=replace(_execution_config(self._config), symbol=instrument.symbol),
                    risk_config=_position_risk_config(self._config),
                    execution_store=self._futures_execution_store,
                    position_store=self._position_store,
                    accounting_store=self._accounting_store,
                    adapter=self._active_adapter,
                    instrument=instrument,
                    account=account,
                    execution_lane=Lane.ACTIVE.value,
                    operator_trading_state=self._operator_state_value,
                )
                lifecycle.reconcile_position(position.position_id)
                if account.mark_price is not None:
                    lifecycle.monitor_protective_exit(position_id=position.position_id, mark_price=account.mark_price)
            except Exception as exc:
                self._log(f"futures snapshot recovery skipped: {exc.__class__.__name__}")

    def _recover_active_checkpoint_gap(
        self,
        *,
        instrument: FuturesInstrumentMetadata,
        recent_candles: tuple,
        active_pair,
        active_set: TriggerSetVersion,
        active_checkpoint: LaneRuntimeCheckpoint,
    ) -> FuturesDualLaneResult:
        self._record_heartbeat("DEGRADED", "checkpoint_recovery_in_progress")
        self._message_store.create_message(
            severity=MessageSeverity.ATTENTION,
            title="Runtime checkpoint gap detected",
            body="Futures runtime detected missed completed candles and is recovering before resuming normal execution.",
            source="futures_runtime",
            entity_type="runtime_checkpoint",
            entity_id=f"{active_set.set_id}:{active_set.version}",
            dedupe_key=f"checkpoint-gap:{active_set.set_id}:{active_set.version}",
            metadata={
                "symbol": active_checkpoint.symbol,
                "timeframe": active_checkpoint.timeframe,
                "checkpoint_before": active_checkpoint.last_processed_candle_open_time,
            },
        )
        active_results: list[RuntimeCycleResult] = []
        test_results: list[RuntimeCycleResult] = []
        recovered_count = 0
        recovery_batches = 0
        latest: CompletedCandle | None = None
        while True:
            current_checkpoint = _lane_checkpoint(self._runtime_store, Lane.ACTIVE, active_set)
            if current_checkpoint is None:
                current_checkpoint = active_checkpoint
            try:
                missing = self._missing_completed_candle_batch_from_checkpoint(current_checkpoint, recent_candles)
            except RuntimeGapError as exc:
                self._message_store.create_message(
                    severity=MessageSeverity.ERROR,
                    title="Runtime checkpoint recovery failed",
                    body="Futures runtime could not prove complete candle continuity and remains degraded.",
                    source="futures_runtime",
                    entity_type="runtime_checkpoint",
                    entity_id=f"{active_set.set_id}:{active_set.version}",
                    dedupe_key=f"checkpoint-recovery-failed:{active_set.set_id}:{active_set.version}",
                    metadata={"reason": str(exc)[:160]},
                )
                self._log(f"futures runtime checkpoint recovery failed: {exc.__class__.__name__}")
                return FuturesDualLaneResult(None if latest is None else latest.candle_id, tuple(active_results), tuple(test_results), "checkpoint_gap")
            if not missing:
                break

            recovery_batches += 1
            batch_candles = tuple(item.candle for item in missing)
            for completed in missing:
                event = futures_event_from_completed_candle(
                    completed=completed,
                    source="bybit_demo_linear_kline|checkpoint_recovery",
                    instrument_version=f"{instrument.contract_type}:{instrument.settlement_asset}",
                )
                regime_context = evaluate_market_regime(
                    RegimeEvaluationWindow(
                        symbol=event.symbol,
                        timeframe=event.timeframe,
                        observed_at=event.close_time,
                        candles=tuple(
                            candle
                            for candle in sorted(recent_candles + batch_candles, key=lambda item: item.start_time_ms)
                            if candle.start_time_ms <= completed.candle.start_time_ms
                        ),
                        category=event.category,
                        current_candle_completed=True,
                    )
                )
                self._runtime_store.save_market_regime(regime_context)
                active_results.append(
                    self._process_lane(
                        lane=Lane.ACTIVE,
                        trigger_set=active_set,
                        completed=completed,
                        event=event,
                        instrument=instrument,
                        candles=recent_candles + batch_candles,
                        regime_context=regime_context,
                        rules_version=active_pair.rules_version if active_pair is not None else None,
                        recovery_mode=True,
                    )
                )
                for trigger_set in self._trigger_set_store.list_testing_sets(completed.symbol, completed.timeframe):
                    test_results.append(
                        self._process_lane(
                            lane=Lane.TEST,
                            trigger_set=trigger_set,
                            completed=completed,
                            event=event,
                            instrument=instrument,
                            candles=recent_candles + batch_candles,
                            regime_context=regime_context,
                            recovery_mode=True,
                        )
                    )
                latest = completed
            recovered_count += len(missing)
            self._record_heartbeat(
                "DEGRADED",
                f"checkpoint_recovery_progress:{recovered_count}:{recovery_batches}",
            )

        if latest is None:
            return FuturesDualLaneResult(None, (), (), "no_completed_candle")

        try:
            active_account = self._refresh_active_account_snapshot(instrument)
            self._recover_active_unresolved(instrument, active_account)
            self._monitor_active_positions(instrument, active_account)
        except (BybitApiError, ValueError, ExecutionError) as exc:
            self._log(f"futures account data unavailable after recovery: {exc.__class__.__name__}")
            return FuturesDualLaneResult(latest.candle_id, tuple(active_results), tuple(test_results), "account_data_unavailable")

        self._message_store.create_message(
            severity=MessageSeverity.INFO,
            title="Runtime checkpoint recovery completed",
            body=f"Futures runtime recovered {len(missing)} completed candle(s) and resumed from {latest.open_time.isoformat()}.",
            source="futures_runtime",
            entity_type="runtime_checkpoint",
            entity_id=f"{active_set.set_id}:{active_set.version}",
            dedupe_key=f"checkpoint-recovery-completed:{active_set.set_id}:{active_set.version}:{latest.candle_id}",
            metadata={
                "symbol": latest.symbol,
                "timeframe": latest.timeframe,
                "recovered_candles": recovered_count,
                "recovery_batches": recovery_batches,
                "checkpoint_before": active_checkpoint.last_processed_candle_open_time,
                "checkpoint_after": latest.open_time.isoformat(),
            },
        )
        self._record_heartbeat("RUNNING", "checkpoint_recovered")
        return FuturesDualLaneResult(latest.candle_id, tuple(active_results), tuple(test_results), "checkpoint_recovered")

    def _missing_completed_candle_batch_from_checkpoint(
        self,
        checkpoint: LaneRuntimeCheckpoint,
        recent_candles: tuple,
    ) -> tuple[CompletedCandle, ...]:
        now = self._clock()
        interval = interval_delta(checkpoint.timeframe)
        latest = latest_completed_candle(
            recent_candles,
            symbol=checkpoint.symbol,
            timeframe=checkpoint.timeframe,
            now=now,
        )
        if latest is None:
            raise RuntimeGapError("no completed candle available for checkpoint recovery")
        last_open = _aware_utc(datetime.fromisoformat(checkpoint.last_processed_candle_open_time))
        if last_open > latest.open_time:
            raise RuntimeGapError("checkpoint is ahead of latest completed exchange candle")
        if last_open == latest.open_time:
            return ()

        batch_end = min(latest.open_time, last_open + interval * _RECOVERY_BATCH_CANDLES)
        candles_by_open: dict[datetime, object] = {}
        range_start = last_open
        range_end = batch_end
        requests = 0
        while range_start <= range_end:
            requests += 1
            if requests > _MAX_RECOVERY_PAGE_REQUESTS:
                raise RuntimeGapError("historical recovery pagination exceeded bounded request limit")
            try:
                response = self._market_client.linear_historical_candles(
                    checkpoint.symbol,
                    interval=_bybit_interval(checkpoint.timeframe),
                    start_ms=_to_ms(range_start),
                    end_ms=_to_ms(range_end),
                    limit=_RECOVERY_PAGE_LIMIT,
                )
                page = parse_spot_candles(response.result)
                _validate_monotonic_page(page)
            except RuntimeGapError:
                raise
            except Exception as exc:
                raise RuntimeGapError("historical recovery returned malformed candle payload") from exc
            eligible = [
                candle
                for candle in page
                if range_start <= _candle_open_time(candle) <= range_end and _candle_open_time(candle) + interval <= now
            ]
            if not eligible:
                raise RuntimeGapError("historical recovery returned no eligible completed candles")
            for candle in eligible:
                open_time = _candle_open_time(candle)
                existing = candles_by_open.get(open_time)
                if existing is not None and existing != candle:
                    raise RuntimeGapError("historical recovery returned conflicting duplicate candle")
                candles_by_open[open_time] = candle
            page_opens = {_candle_open_time(candle) for candle in eligible}
            if range_start in page_opens:
                range_start = max(page_opens) + interval
            elif range_end in page_opens:
                range_end = min(page_opens) - interval
            else:
                raise RuntimeGapError("historical recovery pagination did not include a range boundary")
            if all(open_time in candles_by_open for open_time in _expected_opens(last_open, batch_end, interval)):
                break

        expected = _expected_opens(last_open, batch_end, interval)
        missing_open = next((open_time for open_time in expected if open_time not in candles_by_open), None)
        if missing_open is not None:
            raise RuntimeGapError(f"historical recovery missing candle {missing_open.isoformat()}")
        return tuple(
            CompletedCandle(
                symbol=checkpoint.symbol,
                timeframe=checkpoint.timeframe,
                candle_id=candle_id(checkpoint.symbol, checkpoint.timeframe, open_time),
                open_time=open_time,
                close_time=open_time + interval,
                candle=candles_by_open[open_time],
                previous_candle=candles_by_open[open_time - interval],
            )
            for open_time in expected[1:]
        )

    def _resolve_runtime_instrument(self) -> FuturesInstrumentMetadata:
        self._instrument_catalog.ensure_available()
        return self._instrument_catalog.metadata_for_symbol(self._config.futures_runtime.symbol)

    def _account_state(self, instrument: FuturesInstrumentMetadata, lane: Lane) -> FuturesAccountState:
        if lane is Lane.TEST:
            return _test_account(instrument, self._config.futures_runtime.leverage, self._config.futures_runtime.max_position_notional)
        if self._account_provider is not None:
            return self._account_provider(instrument)
        wallet = self._market_client.wallet_balance("UNIFIED").result
        positions = self._market_client.linear_position_list(instrument.symbol).result
        return _account_from_bybit(wallet, positions, instrument, self._config.futures_runtime.leverage)

    def _refresh_active_account_snapshot(self, instrument: FuturesInstrumentMetadata) -> FuturesAccountState:
        account = self._account_state(instrument, Lane.ACTIVE)
        self._persist_account_snapshot(account)
        return account

    def _persist_account_snapshot(self, account: FuturesAccountState) -> None:
        now = self._clock()
        observed_at = now.isoformat()
        self._account_snapshot_sequence += 1
        previous = self._accounting_store.latest_equity_snapshot()
        previous_peak = _optional_decimal(None if previous is None else previous["running_peak"])
        previous_max_drawdown = _optional_decimal(None if previous is None else previous["max_drawdown"]) or Decimal("0")
        equity = account.equity if account.equity is not None else account.available_margin
        wallet_balance = account.wallet_balance if account.wallet_balance is not None else equity
        used_margin = max(equity - account.available_margin, Decimal("0"))
        snapshot = calculate_drawdown_snapshot(
            snapshot_id=f"acct-{now.strftime('%Y%m%d%H%M%S%f')}-{self._account_snapshot_sequence}",
            observed_at=observed_at,
            source="bybit_demo_account" if self._account_provider is None else "runtime_account_provider",
            wallet_balance=wallet_balance,
            equity=equity,
            available_margin=account.available_margin,
            used_margin=used_margin,
            unrealized_pnl=account.unrealized_pnl or Decimal("0"),
            realized_pnl=Decimal("0"),
            previous_running_peak=previous_peak,
            previous_max_drawdown=previous_max_drawdown,
        )
        self._accounting_store.record_equity_snapshot(snapshot)

    def _recover_active_unresolved(self, instrument: FuturesInstrumentMetadata, account: FuturesAccountState | None = None) -> None:
        account = account or self._account_state(instrument, Lane.ACTIVE)
        lifecycle = FuturesPositionLifecycleService(
            execution_config=_execution_config(self._config),
            risk_config=_position_risk_config(self._config),
            execution_store=self._futures_execution_store,
            position_store=self._position_store,
            accounting_store=self._accounting_store,
            adapter=self._active_adapter,
            instrument=instrument,
            account=account,
            execution_lane=Lane.ACTIVE.value,
            operator_trading_state=self._operator_state_value,
        )
        lifecycle.recover_after_restart()
        service = FuturesExecutionService(
            config=_execution_config(self._config),
            adapter=self._active_adapter,
            store=self._futures_execution_store,
            instrument=instrument,
            account=account,
            execution_lane=Lane.ACTIVE.value,
            operator_trading_state=self._operator_state_value,
        )
        bridge = FuturesAccountingBridge(accounting_store=self._accounting_store, adapter=self._active_adapter)
        position_intents = {
            intent_id
            for position in self._position_store.list_open_positions(include_unknown=True)
            for intent_id in (position.open_intent_id, position.close_intent_id)
            if intent_id
        }
        for record in service.recover_unresolved():
            if record.intent_id not in position_intents:
                bridge.ingest_execution(record=record)

    def _monitor_active_positions(self, instrument: FuturesInstrumentMetadata, account: FuturesAccountState | None = None) -> None:
        account = account or self._account_state(instrument, Lane.ACTIVE)
        if account.mark_price is None:
            return
        lifecycle = FuturesPositionLifecycleService(
            execution_config=_execution_config(self._config),
            risk_config=_position_risk_config(self._config),
            execution_store=self._futures_execution_store,
            position_store=self._position_store,
            accounting_store=self._accounting_store,
            adapter=self._active_adapter,
            instrument=instrument,
            account=account,
            execution_lane=Lane.ACTIVE.value,
            operator_trading_state=self._operator_state_value,
        )
        for position in self._position_store.list_open_positions():
            if position.symbol == instrument.symbol:
                lifecycle.monitor_protective_exit(position_id=position.position_id, mark_price=account.mark_price)

    def _save_lane_lifecycle(
        self,
        lane: Lane,
        trigger_set: TriggerSetVersion,
        completed: CompletedCandle,
        status: str,
        *,
        signal_id: str | None = None,
        intent_id: str | None = None,
        risk_decision_id: str | None = None,
        execution_intent_id: str | None = None,
        processed_at: str | None = None,
        error: str | None = None,
        regime_context: MarketRegimeContext | None = None,
        rules_version_id: str | None = None,
        rules_evaluation: dict[str, str | None] | None = None,
    ) -> None:
        self._runtime_store.save_lane_lifecycle(
            LaneCandleLifecycle(
                lane=lane.value,
                symbol=completed.symbol,
                timeframe=completed.timeframe,
                candle_id=completed.candle_id,
                candle_open_time=completed.open_time.isoformat(),
                trigger_set_id=trigger_set.set_id,
                trigger_set_version=trigger_set.version,
                status=status,
                signal_id=signal_id,
                intent_id=intent_id,
                risk_decision_id=risk_decision_id,
                execution_intent_id=execution_intent_id,
                processed_at=processed_at,
                error=error,
                regime_context_id=None if regime_context is None else regime_context.context_id,
                regime_state=None if regime_context is None or regime_context.label is None else regime_context.label.value,
                rules_version_id=rules_version_id,
                rules_evaluation=rules_evaluation,
            )
        )
        self._record_lane_audit_event(
            lane=lane,
            trigger_set=trigger_set,
            completed=completed,
            status=status,
            signal_id=signal_id,
            intent_id=intent_id,
            risk_decision_id=risk_decision_id,
            execution_intent_id=execution_intent_id,
            processed_at=processed_at,
            error=error,
            regime_context=regime_context,
            rules_version_id=rules_version_id,
            rules_evaluation=rules_evaluation,
        )

    def _record_lane_audit_event(
        self,
        *,
        lane: Lane,
        trigger_set: TriggerSetVersion,
        completed: CompletedCandle,
        status: str,
        signal_id: str | None,
        intent_id: str | None,
        risk_decision_id: str | None,
        execution_intent_id: str | None,
        processed_at: str | None,
        error: str | None,
        regime_context: MarketRegimeContext | None,
        rules_version_id: str | None,
        rules_evaluation: dict[str, str | None] | None,
    ) -> None:
        event_type = _audit_event_type_for_lane_status(status)
        if event_type is None:
            return
        result = "REJECTED" if event_type == "ENTRY_REJECTED" else status.upper()
        try:
            self._trace_store.record_audit_event(
                event_type=event_type,
                source_type="RUNTIME",
                source_id=completed.candle_id,
                scope=lane.value,
                entity_type="runtime_candle",
                entity_id=completed.candle_id,
                related_entity_type="trade_intent" if intent_id else "signal" if signal_id else None,
                related_entity_id=intent_id or signal_id,
                set_id=trigger_set.set_id,
                set_version=trigger_set.version,
                rules_version_id=rules_version_id,
                position_id=None,
                order_id=execution_intent_id,
                result=result,
                reason_code=error or status,
                safe_metadata={
                    "symbol": completed.symbol,
                    "timeframe": completed.timeframe,
                    "candle_open_time": completed.open_time.isoformat(),
                    "status": status,
                    "signal_id": signal_id,
                    "intent_id": intent_id,
                    "risk_decision_id": risk_decision_id,
                    "execution_intent_id": execution_intent_id,
                    "regime_context_id": None if regime_context is None else regime_context.context_id,
                    "regime_state": None if regime_context is None or regime_context.label is None else regime_context.label.value,
                    "rules_evaluation": rules_evaluation or {},
                },
                created_at=processed_at or completed.open_time.isoformat(),
            )
        except Exception:
            return

    def _checkpoint_lane(self, lane: Lane, trigger_set: TriggerSetVersion, completed: CompletedCandle) -> None:
        self._runtime_store.lane_checkpoint(
            LaneRuntimeCheckpoint(
                lane=lane.value,
                symbol=completed.symbol,
                timeframe=completed.timeframe,
                trigger_set_id=trigger_set.set_id,
                trigger_set_version=trigger_set.version,
                last_processed_candle_id=completed.candle_id,
                last_processed_candle_open_time=completed.open_time.isoformat(),
                last_processed_at=self._clock().isoformat(),
                runtime_version=self._config.futures_runtime.version,
            )
        )

    def _validate_safe_config(self) -> None:
        if self._config.trading_mode is not TradingMode.PAPER:
            raise ConfigError("futures runtime requires paper-mode configuration")
        if self._config.live_trading_enabled:
            raise ConfigError("futures runtime requires live trading disabled")
        if self._config.bybit.environment is not BybitEnvironment.DEMO:
            raise ConfigError("futures runtime requires Bybit Demo")
        if self._config.bybit.base_url != "https://api-demo.bybit.com":
            raise ConfigError("futures runtime requires Bybit Demo base URL")
        if self._config.market is not Market.LINEAR or self._config.futures_runtime.category != "linear":
            raise ConfigError("futures runtime supports only linear perpetual market data")
        if self._config.futures_runtime.symbol != "BTCUSDT":
            raise ConfigError("futures runtime supports only BTCUSDT")
        if _bybit_interval(self._config.futures_runtime.candle_interval) != "1":
            raise ConfigError("futures runtime supports only 1m candles")
        if self._config.futures_runtime.active_execution_venue is not ExecutionVenue.BYBIT_DEMO_FUTURES:
            raise ConfigError("ACTIVE lane requires Bybit Demo futures execution venue")
        if self._config.futures_runtime.test_execution_venue is not ExecutionVenue.LOCAL_TEST_SIMULATION:
            raise ConfigError("TEST lane requires local test simulation")
        if self._config.execution_venue is ExecutionVenue.LOCAL_PAPER:
            raise ConfigError("futures runtime must not force the legacy LOCAL_PAPER execution venue")

    def _operator_state_value(self) -> str:
        return self._operator_state_store.get_trading_state().state.value

    def _log(self, message: str) -> None:
        self._logger(f"triggertrade futures runtime: {message}")

    def _record_heartbeat(self, status: str, detail: str) -> None:
        try:
            self._runtime_store.record_heartbeat(
                RuntimeHeartbeat(
                    component="futures_runtime",
                    status=status,
                    observed_at=self._clock().isoformat(),
                    detail=detail,
                    metadata={
                        "symbol": self._config.futures_runtime.symbol,
                        "timeframe": self._config.futures_runtime.candle_interval,
                    },
                )
            )
        except Exception:  # noqa: BLE001 - heartbeat observability must not change trading behavior.
            self._log("runtime heartbeat unavailable")


def _execution_config(config: AppConfig) -> FuturesExecutionConfig:
    return FuturesExecutionConfig(
        trading_mode=config.trading_mode,
        live_trading_enabled=config.live_trading_enabled,
        bybit_environment=config.bybit.environment,
        bybit_base_url=config.bybit.base_url,
        category=ContractCategory.LINEAR,
        symbol=config.futures_runtime.symbol,
        default_leverage=config.futures_runtime.leverage,
        max_configured_leverage=config.futures_runtime.leverage,
    )


def _heartbeat_outcome(result: FuturesDualLaneResult) -> tuple[str, str]:
    if result.skipped_reason in {"market_data_unavailable", "checkpoint_gap", "account_data_unavailable"}:
        return "DEGRADED", result.skipped_reason
    if result.skipped_reason is not None:
        return "RUNNING", result.skipped_reason
    lane_results = result.active + result.test
    lane_reasons = {lane.skipped_reason for lane in lane_results}
    lane_statuses = {lane.execution_status for lane in lane_results}
    if "execution_unknown" in lane_reasons or OrderStatus.UNKNOWN.value in lane_statuses:
        return "BLOCKED", "execution_unknown"
    if "execution_error" in lane_reasons:
        return "BLOCKED", "execution_error"
    if "active_execution_paused" in lane_reasons:
        return "BLOCKED", "active_execution_paused"
    return "RUNNING", "cycle completed"


def _audit_event_type_for_lane_status(status: str) -> str | None:
    return {
        "no_signal": "SET_EVALUATED",
        "no_intent": "ENTRY_REJECTED",
        "risk_rejected": "ENTRY_REJECTED",
        "active_execution_paused": "ENTRY_REJECTED",
        "stale_entry_suppressed": "STALE_ENTRY_SUPPRESSED",
        "completed": "RUNTIME_DECISION_COMPLETED",
        "execution_unknown": "ORDER_UNKNOWN",
        "execution_error": "ORDER_REJECTED",
        "test_simulated": "TEST_TRADE_SIMULATED",
    }.get(status)


def _candle_open_time(candle) -> datetime:
    return datetime.fromtimestamp(candle.start_time_ms / 1000, UTC)


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _to_ms(value: datetime) -> int:
    return int(value.astimezone(UTC).timestamp() * 1000)


def _validate_monotonic_page(candles: tuple) -> None:
    if len(candles) < 2:
        return
    opens = [_candle_open_time(candle) for candle in candles]
    ascending = all(left <= right for left, right in zip(opens, opens[1:]))
    descending = all(left >= right for left, right in zip(opens, opens[1:]))
    if not ascending and not descending:
        raise RuntimeGapError("historical recovery returned out-of-order candles")


def _expected_opens(start: datetime, end: datetime, interval: timedelta) -> list[datetime]:
    expected: list[datetime] = []
    cursor = start
    while cursor <= end:
        expected.append(cursor)
        cursor += interval
    return expected



def _position_risk_config_from_rules(rules_version: TradingRulesVersion, account: FuturesAccountState) -> PositionRiskConfig:
    rules = rules_version.draft
    denominator, denominator_source = _capital_denominator(account)
    max_total_notional = denominator * rules.max_capital_in_positions_pct * rules.leverage
    coin = coin_rule_for(rules, account.symbol)
    if coin is not None and coin.max_allocation_pct is not None:
        max_total_notional = min(max_total_notional, denominator * coin.max_allocation_pct * rules.leverage)
    return PositionRiskConfig(
        take_profit_pct=_fixed_take_profit_pct(rules_version),
        stop_loss_pct=rules.stop_loss_pct,
        minimum_risk_reward=rules.minimum_risk_reward,
        position_size_pct_of_available_capital=rules.position_size_pct,
        max_position_notional=max_total_notional,
        max_total_position_notional=max_total_notional,
        max_open_positions=rules.max_open_positions if rules.max_open_positions_enabled else None,
        denominator_source=denominator_source,
        rules_version_id=rules_version.rules_version_id,
    )


def _capital_denominator(account: FuturesAccountState) -> tuple[Decimal, str]:
    if account.equity is not None and account.equity > 0:
        return account.equity, "equity"
    if account.available_margin > 0:
        return account.available_margin, "available_margin_fallback"
    raise ExecutionError("trading rules require positive account equity or available margin")


def _fixed_take_profit_pct(rules_version: TradingRulesVersion) -> Decimal:
    rules = rules_version.draft
    if rules.take_profit_mode is not TakeProfitMode.FIXED or rules.fixed_take_profit_pct is None:
        raise ExecutionError("dynamic take-profit mode is not approved for runtime execution")
    if rules.minimum_take_profit_pct is not None and rules.fixed_take_profit_pct < rules.minimum_take_profit_pct:
        raise ExecutionError("fixed take-profit is below configured minimum take-profit floor")
    return rules.fixed_take_profit_pct


def _rules_skip_reason(rules_version: TradingRulesVersion, symbol: str) -> str | None:
    try:
        _fixed_take_profit_pct(rules_version)
        coin = coin_rule_for(rules_version.draft, symbol)
    except (ExecutionError, TradingRulesError) as exc:
        return str(exc)
    if coin is None:
        return "symbol_not_present_in_current_trading_rules"
    if not coin.enabled:
        return "symbol_disabled_by_current_trading_rules"
    return None



def _rules_rejection_evidence(rules_version: TradingRulesVersion, reason: str, symbol: str) -> dict[str, str | None]:
    rules = rules_version.draft
    coin = coin_rule_for(rules, symbol)
    return {
        "rules_version_id": rules_version.rules_version_id,
        "rules_version": rules_version.version,
        "blocking_rule": reason,
        "symbol": symbol,
        "coin_rule_enabled": None if coin is None else str(coin.enabled),
        "take_profit_mode": rules.take_profit_mode.value,
        "direction_mode": rules.direction_mode.value,
        "daily_loss_limit_enabled": str(rules.daily_loss_limit_enabled),
        "max_positions_per_coin_enabled": str(rules.max_positions_per_coin_enabled),
        "max_positions_per_coin": None if rules.max_positions_per_coin is None else str(rules.max_positions_per_coin),
        "minimum_net_edge_enabled": str(rules.minimum_net_edge_enabled),
    }


def _direction_skip_reason(rules_version: TradingRulesVersion, action: PositionAction) -> str | None:
    mode = rules_version.draft.direction_mode
    if mode is DirectionMode.LONG_ONLY and action is PositionAction.OPEN_SHORT:
        return "short_entries_disabled_by_current_trading_rules"
    if mode is DirectionMode.SHORT_ONLY and action is PositionAction.OPEN_LONG:
        return "long_entries_disabled_by_current_trading_rules"
    return None


def _rule_evaluation_snapshot(rules_version: TradingRulesVersion, sizing, account: FuturesAccountState, *, daily_loss=None) -> dict[str, str | None]:
    rules = rules_version.draft
    denominator, denominator_source = _capital_denominator(account)
    evidence = {
        "rules_version_id": rules_version.rules_version_id,
        "rules_version": rules_version.version,
        "position_size_pct": str(rules.position_size_pct),
        "take_profit_mode": rules.take_profit_mode.value,
        "fixed_take_profit_pct": None if rules.fixed_take_profit_pct is None else str(rules.fixed_take_profit_pct),
        "minimum_take_profit_pct": None if rules.minimum_take_profit_pct is None else str(rules.minimum_take_profit_pct),
        "stop_loss_pct": str(rules.stop_loss_pct),
        "minimum_risk_reward": str(rules.minimum_risk_reward),
        "minimum_net_edge_enabled": str(rules.minimum_net_edge_enabled),
        "minimum_net_edge_pct": None if rules.minimum_net_edge_pct is None else str(rules.minimum_net_edge_pct),
        "leverage": str(rules.leverage),
        "max_capital_in_positions_pct": str(rules.max_capital_in_positions_pct),
        "max_open_positions_enabled": str(rules.max_open_positions_enabled),
        "max_open_positions": None if rules.max_open_positions is None else str(rules.max_open_positions),
        "max_positions_per_coin_enabled": str(rules.max_positions_per_coin_enabled),
        "max_positions_per_coin": None if rules.max_positions_per_coin is None else str(rules.max_positions_per_coin),
        "direction_mode": rules.direction_mode.value,
        "daily_loss_limit_enabled": str(rules.daily_loss_limit_enabled),
        "daily_loss_limit_pct": None if rules.daily_loss_limit_pct is None else str(rules.daily_loss_limit_pct),
        "maker_fee_rate": str(rules.maker_fee_rate),
        "taker_fee_rate": str(rules.taker_fee_rate),
        "spread_cost": str(rules.spread_cost),
        "slippage_cost": str(rules.slippage_cost),
        "funding_cost": str(rules.funding_cost),
        "capital_denominator": str(denominator),
        "capital_denominator_source": denominator_source,
        "sizing_quantity": str(sizing.quantity),
        "sizing_notional": str(sizing.notional),
    }
    if daily_loss is not None:
        evidence.update(_prefixed_daily_loss_evidence(daily_loss.evidence()))
    return evidence


def _prefixed_daily_loss_evidence(evidence: dict[str, str | None]) -> dict[str, str | None]:
    return {f"daily_loss_{key}": value for key, value in evidence.items()}

def _position_risk_config(config: AppConfig) -> PositionRiskConfig:
    return PositionRiskConfig(
        take_profit_pct=config.futures_runtime.take_profit_pct,
        stop_loss_pct=config.futures_runtime.stop_loss_pct,
        minimum_risk_reward=config.futures_runtime.minimum_risk_reward,
        position_size_pct_of_available_capital=config.futures_runtime.position_size_pct_of_available_capital,
        max_position_notional=config.futures_runtime.max_position_notional,
        max_total_position_notional=config.futures_runtime.max_total_position_notional,
        max_open_positions=config.futures_runtime.max_open_positions,
    )


def _account_from_bybit(
    wallet: dict,
    positions: dict,
    instrument: FuturesInstrumentMetadata,
    configured_leverage: Decimal,
) -> FuturesAccountState:
    account = (wallet.get("list") or [{}])[0]
    available = Decimal(str(account.get("totalAvailableBalance") or account.get("totalWalletBalance") or "0"))
    equity = _optional_decimal(account.get("totalEquity"))
    wallet_balance = _optional_decimal(account.get("totalWalletBalance"))
    position_row = _first_position(positions, instrument.symbol)
    size = Decimal("0")
    entry_price = None
    mark_price = None
    liquidation_price = None
    if position_row is not None:
        raw_size = Decimal(str(position_row.get("size") or "0"))
        side = str(position_row.get("side") or "")
        size = -raw_size if side.lower() == "sell" else raw_size
        entry_price = _optional_decimal(position_row.get("avgPrice"))
        mark_price = _optional_decimal(position_row.get("markPrice"))
        unrealized_pnl = _optional_decimal(position_row.get("unrealisedPnl") or position_row.get("unrealizedPnl"))
        liquidation_price = _optional_decimal(position_row.get("liqPrice"))
        configured_leverage = _optional_decimal(position_row.get("leverage")) or configured_leverage
    else:
        unrealized_pnl = _optional_decimal(account.get("totalPerpUPL"))
    return FuturesAccountState(
        symbol=instrument.symbol,
        category=ContractCategory.LINEAR,
        settlement_asset=instrument.settlement_asset,
        available_margin=available,
        equity=equity,
        wallet_balance=wallet_balance,
        configured_leverage=configured_leverage,
        margin_mode="ISOLATED",
        position_mode="ONE_WAY",
        position_size=size,
        entry_price=entry_price,
        mark_price=mark_price,
        unrealized_pnl=unrealized_pnl,
        liquidation_price=liquidation_price,
    )


def _test_account(
    instrument: FuturesInstrumentMetadata,
    leverage: Decimal,
    max_position_notional: Decimal,
) -> FuturesAccountState:
    return FuturesAccountState(
        symbol=instrument.symbol,
        category=ContractCategory.LINEAR,
        settlement_asset=instrument.settlement_asset,
        available_margin=max_position_notional * Decimal("10"),
        equity=max_position_notional * Decimal("10"),
        wallet_balance=max_position_notional * Decimal("10"),
        configured_leverage=leverage,
        margin_mode="ISOLATED",
        position_mode="ONE_WAY",
        position_size=Decimal("0"),
    )


def _first_position(result: dict, symbol: str) -> dict | None:
    for item in result.get("list") or []:
        if item.get("symbol") == symbol:
            return item
    return None


def _position_state(account: FuturesAccountState) -> PositionState:
    if account.position_size > 0:
        return PositionState.LONG
    if account.position_size < 0:
        return PositionState.SHORT
    return PositionState.FLAT


def _intent_price(reference: Decimal, instrument: FuturesInstrumentMetadata, *, passive: bool) -> Decimal:
    price = reference - (instrument.price_tick * Decimal("10")) if passive else reference
    return _floor_to_step(price, instrument.price_tick)


def _intent_quantity(price: Decimal, instrument: FuturesInstrumentMetadata, max_notional: Decimal) -> Decimal | None:
    if price <= 0 or max_notional < instrument.minimum_notional:
        return None
    quantity = _floor_to_step(max_notional / price, instrument.quantity_step)
    if quantity < instrument.minimum_order_quantity:
        quantity = instrument.minimum_order_quantity
    if quantity * price < instrument.minimum_notional or quantity * price > max_notional:
        return None
    return quantity


def _floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    return (value // step) * step


def _lane_checkpoint(store: RuntimeStore, lane: Lane, trigger_set: TriggerSetVersion):
    return store.get_lane_checkpoint(
        lane=lane.value,
        symbol=trigger_set.symbol,
        timeframe=trigger_set.timeframe,
        trigger_set_id=trigger_set.set_id,
        trigger_set_version=trigger_set.version,
    )


def _is_futures_set(trigger_set: TriggerSetVersion) -> bool:
    versions = set(trigger_set.rule_versions)
    mandatory = {
        ("TRG-001", "0.2.0"),
        ("STR-FUT-001", "0.1.0"),
        ("RSK-FUTURES-001", "0.1.0"),
        ("CTX-REGIME", "0.1.0"),
    }
    if not mandatory.issubset(versions):
        return False
    return all(rule_version == "0.2.0" for rule_id, rule_version in versions if rule_id == "TRG-002")


def _optional_decimal(value) -> Decimal | None:
    if value in {None, ""}:
        return None
    return Decimal(str(value))


def _bybit_interval(timeframe: str) -> str:
    if timeframe.strip().lower() in {"1", "1m"}:
        return "1"
    raise ValueError("only 1m candle interval is supported")
