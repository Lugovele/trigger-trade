"""Continuous Bybit Demo linear futures runtime integration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import time
from typing import Callable

from triggertrade.config import AppConfig, BybitEnvironment, ConfigError, ExecutionVenue, Market, TradingMode
from triggertrade.execution import OrderStatus, OrderType
from triggertrade.execution.bybit_futures import BybitFuturesExecutionAdapter
from triggertrade.execution.futures import (
    FundingEstimate,
    FuturesExecutionConfig,
    FuturesExecutionService,
    FuturesRiskManager,
    FuturesTradeIntent,
    PositionState,
    estimate_costs,
)
from triggertrade.exchanges import BybitApiError, BybitDemoClient
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
    FuturesExecutionStore,
    LaneCandleLifecycle,
    LaneRuntimeCheckpoint,
    OperatorStateStore,
    RuntimeStore,
    TraceStore,
    TriggerSetStore,
)
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.services.futures_accounting_bridge import FuturesAccountingBridge
from triggertrade.services.runtime import CompletedCandle, RuntimeCycleResult, RuntimeGapError, latest_completed_candle, next_completed_candle
from triggertrade.services.test_futures_simulator import TestFuturesSimulator
from triggertrade.strategies import IntegrationDirectionalFuturesStrategy
from triggertrade.trigger_sets import Lane, TriggerSetStatus, TriggerSetVersion
from triggertrade.triggers import PercentagePriceMoveTrigger, RobustVolumeConfirmationTrigger, Signal, SignalType, VolumeConfirmationConfig, VolumeConfirmationResult


@dataclass(frozen=True)
class FuturesDualLaneResult:
    candle_id: str | None
    active: tuple[RuntimeCycleResult, ...]
    test: tuple[RuntimeCycleResult, ...]
    skipped_reason: str | None = None


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
        active_adapter: BybitFuturesExecutionAdapter | None = None,
        test_simulator: TestFuturesSimulator | None = None,
        account_provider: Callable[[FuturesInstrumentMetadata], FuturesAccountState] | None = None,
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
        self._active_adapter = active_adapter or BybitFuturesExecutionAdapter(market_client)
        self._test_simulator = test_simulator or TestFuturesSimulator(
            accounting_store=accounting_store,
            maker_fee_rate=config.futures_runtime.maker_fee_rate,
        )
        self._account_provider = account_provider
        self._clock = clock or (lambda: datetime.now(UTC))
        self._logger = logger or (lambda message: print(message))
        self._stop_requested = False

    def process_once(self) -> FuturesDualLaneResult:
        self._validate_safe_config()
        try:
            instrument = parse_linear_instrument(
                self._market_client.linear_instrument_metadata(self._config.futures_runtime.symbol).result
            )
            candles = parse_spot_candles(
                self._market_client.linear_recent_candles(
                    self._config.futures_runtime.symbol,
                    interval=_bybit_interval(self._config.futures_runtime.candle_interval),
                    limit=70,
                ).result
            )
            active_set = self._trigger_set_store.get_active_set(self._config.futures_runtime.symbol, "1m")
            if active_set is not None:
                self._recover_active_unresolved(instrument)
            active_checkpoint = _lane_checkpoint(self._runtime_store, Lane.ACTIVE, active_set) if active_set else None
            completed = next_completed_candle(
                candles,
                symbol=self._config.futures_runtime.symbol,
                timeframe="1m",
                now=self._clock(),
                checkpoint=active_checkpoint,
            )
            if completed is None:
                completed = latest_completed_candle(
                    candles,
                    symbol=self._config.futures_runtime.symbol,
                    timeframe="1m",
                    now=self._clock(),
                )
        except RuntimeGapError as exc:
            self._log(f"futures runtime checkpoint gap: {exc.__class__.__name__}")
            return FuturesDualLaneResult(None, (), (), "checkpoint_gap")
        except (BybitApiError, ValueError) as exc:
            self._log(f"futures market data unavailable: {exc.__class__.__name__}")
            return FuturesDualLaneResult(None, (), (), "market_data_unavailable")
        if completed is None:
            return FuturesDualLaneResult(None, (), (), "no_completed_candle")

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
            self.process_once()
            cycles += 1
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
        if existing is not None and existing.status in {
            "no_signal",
            "no_intent",
            "risk_rejected",
            "test_simulated",
            "completed",
            "active_execution_paused",
        }:
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

        price = _intent_price(event.close, instrument, passive=lane is Lane.ACTIVE)
        quantity = _intent_quantity(price, instrument, self._config.futures_runtime.max_position_notional)
        if quantity is None:
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "no_intent",
                signal_id=signal.signal_id,
                processed_at=self._clock().isoformat(),
                error="instrument_minimum_exceeds_configured_notional",
                regime_context=regime_context,
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, skipped_reason="instrument_minimum_exceeds_configured_notional")

        account = self._account_state(instrument, lane)
        decision = IntegrationDirectionalFuturesStrategy().decide(
            lane=lane,
            trigger_set=trigger_set,
            event=event,
            primary_signal=signal,
            volume_signal=volume_signal,
            regime_context=regime_context,
            position_state=_position_state(account),
            quantity=quantity,
            limit_price=price,
            leverage=self._config.futures_runtime.leverage,
            expected_gross_move=self._config.futures_runtime.demo_expected_gross_move,
            created_at=self._clock(),
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
            maker_fee_rate=self._config.futures_runtime.maker_fee_rate,
            taker_fee_rate=self._config.futures_runtime.taker_fee_rate,
            spread_cost=self._config.futures_runtime.spread_cost,
            slippage_cost=self._config.futures_runtime.slippage_cost,
            funding_cost=self._config.futures_runtime.funding_cost,
        )
        funding = FundingEstimate(
            funding_rate=None,
            next_funding_time=None,
            expected_holding_overlap=Decimal("0"),
            estimated_funding_impact=self._config.futures_runtime.funding_cost,
        )
        risk = FuturesRiskManager(
            config=_execution_config(self._config),
            store=self._futures_execution_store,
            minimum_net_edge=self._config.futures_runtime.minimum_net_edge,
            max_position_notional=self._config.futures_runtime.max_position_notional,
            max_simultaneous_exposure=self._config.futures_runtime.max_position_notional,
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
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, True, "test_simulated")

        service = FuturesExecutionService(
            config=_execution_config(self._config),
            adapter=self._active_adapter,
            store=self._futures_execution_store,
            instrument=instrument,
            account=account,
            execution_lane=lane.value,
            operator_trading_state=self._operator_state_value,
        )
        try:
            record = service.submit_approved_limit_order(intent=intent, risk_decision=risk)
            record = service.reconcile(record)
            FuturesAccountingBridge(accounting_store=self._accounting_store, adapter=self._active_adapter).ingest_execution(
                record=record,
                intent=intent,
            )
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
            )
            if status == "active_execution_paused":
                self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, True, skipped_reason=status)

        if record.status is OrderStatus.UNKNOWN:
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
        )
        self._checkpoint_lane(lane, trigger_set, completed)
        return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, True, record.status.value)

    def _price_signal(self, *, lane: Lane, trigger_set: TriggerSetVersion, completed: CompletedCandle, event) -> Signal:
        observation = event.to_market_observation(stale_after_seconds=self._config.risk_rules.stale_after_seconds)
        observation = replace(observation, source=f"{observation.source}|{lane.value}|{trigger_set.set_id}|{trigger_set.version}")
        config = replace(self._config.trigger_rule, version="0.2.0")
        signal = PercentagePriceMoveTrigger(config, symbol=self._config.futures_runtime.symbol).evaluate(
            observation,
            now=self._clock(),
        )
        return replace(signal, lane=lane.value, trigger_set_id=trigger_set.set_id, trigger_set_version=trigger_set.version)

    def _volume_signal(self, *, lane: Lane, trigger_set: TriggerSetVersion, completed: CompletedCandle, event, candles) -> Signal:
        previous = tuple(
            candle
            for candle in sorted(candles, key=lambda item: item.start_time_ms)
            if candle.start_time_ms < completed.candle.start_time_ms
        )
        evaluation = RobustVolumeConfirmationTrigger(
            VolumeConfirmationConfig(version="0.2.0", stale_after_seconds=self._config.risk_rules.stale_after_seconds),
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

    def _account_state(self, instrument: FuturesInstrumentMetadata, lane: Lane) -> FuturesAccountState:
        if self._account_provider is not None:
            return self._account_provider(instrument)
        if lane is Lane.TEST:
            return _test_account(instrument, self._config.futures_runtime.leverage, self._config.futures_runtime.max_position_notional)
        wallet = self._market_client.wallet_balance("UNIFIED").result
        positions = self._market_client.linear_position_list(instrument.symbol).result
        return _account_from_bybit(wallet, positions, instrument, self._config.futures_runtime.leverage)

    def _recover_active_unresolved(self, instrument: FuturesInstrumentMetadata) -> None:
        account = self._account_state(instrument, Lane.ACTIVE)
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
        for record in service.recover_unresolved():
            bridge.ingest_execution(record=record)

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
            )
        )

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
        liquidation_price = _optional_decimal(position_row.get("liqPrice"))
        configured_leverage = _optional_decimal(position_row.get("leverage")) or configured_leverage
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
