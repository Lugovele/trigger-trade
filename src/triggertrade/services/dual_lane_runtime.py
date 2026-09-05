"""Dual-lane runtime fan-out for versioned Trigger Sets."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from hashlib import sha256
import time
from typing import Callable

from triggertrade.config import AppConfig, ConfigError, ExecutionVenue
from triggertrade.execution import ExecutionError, ExecutionService, PaperExecutionAdapter
from triggertrade.exchanges import BybitApiError, BybitDemoClient
from triggertrade.market_data import BybitInstrument, MarketObservation, parse_spot_candles, parse_spot_instrument
from triggertrade.persistence import (
    ExecutionStore,
    LaneCandleLifecycle,
    LaneRuntimeCheckpoint,
    RuntimeCheckpoint,
    RuntimeStore,
    TraceStore,
    TriggerSetStore,
    OperatorStateStore,
)
from triggertrade.risk import RiskManager
from triggertrade.services.runtime import (
    CompletedCandle,
    RuntimeCycleResult,
    RuntimeGapError,
    latest_completed_candle,
    next_completed_candle,
    observation_from_completed_candle,
)
from triggertrade.strategies import BuyCandidateStrategy
from triggertrade.trigger_sets import Lane, TriggerSetStatus, TriggerSetVersion
from triggertrade.triggers import PercentagePriceMoveTrigger, RobustVolumeConfirmationTrigger, Signal, SignalType, VolumeCandleWindow, VolumeConfirmationConfig, VolumeConfirmationResult


@dataclass(frozen=True)
class DualLaneResult:
    candle_id: str | None
    active: tuple[RuntimeCycleResult, ...]
    test: tuple[RuntimeCycleResult, ...]
    skipped_reason: str | None = None


class DualLaneRuntime:
    def __init__(
        self,
        *,
        config: AppConfig,
        market_client: BybitDemoClient,
        execution_store: ExecutionStore,
        trace_store: TraceStore,
        runtime_store: RuntimeStore,
        trigger_set_store: TriggerSetStore,
        operator_state_store: OperatorStateStore | None = None,
        active_adapter: PaperExecutionAdapter | None = None,
        test_adapter_factory: Callable[[], PaperExecutionAdapter] | None = None,
        clock: Callable[[], datetime] | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        self._config = config
        self._market_client = market_client
        self._execution_store = execution_store
        self._trace_store = trace_store
        self._runtime_store = runtime_store
        self._trigger_set_store = trigger_set_store
        self._operator_state_store = operator_state_store
        self._active_adapter = active_adapter or PaperExecutionAdapter(clock_ms=lambda: int(time.time() * 1000))
        self._test_adapter_factory = test_adapter_factory or (lambda: PaperExecutionAdapter(clock_ms=lambda: int(time.time() * 1000)))
        self._clock = clock or (lambda: datetime.now(UTC))
        self._logger = logger or (lambda message: print(message))
        self._stop_requested = False

    def process_once(self) -> DualLaneResult:
        self._validate_safe_config()
        try:
            instrument = parse_spot_instrument(
                self._market_client.instrument_metadata(self._config.paper_runtime.symbol).result
            )
            candles = parse_spot_candles(
                self._market_client.recent_candles(
                    self._config.paper_runtime.symbol,
                    interval=_bybit_interval(self._config.paper_runtime.candle_interval),
                    limit=70,
                ).result
            )
            active_set = self._trigger_set_store.get_active_set(self._config.paper_runtime.symbol, "1m")
            active_checkpoint = None
            if active_set is not None:
                active_checkpoint = self._runtime_store.get_lane_checkpoint(
                    lane=Lane.ACTIVE.value,
                    symbol=self._config.paper_runtime.symbol,
                    timeframe="1m",
                    trigger_set_id=active_set.set_id,
                    trigger_set_version=active_set.version,
                )
            completed = next_completed_candle(
                candles,
                symbol=self._config.paper_runtime.symbol,
                timeframe="1m",
                now=self._clock(),
                checkpoint=active_checkpoint,
            )
            if completed is None:
                completed = latest_completed_candle(
                    candles,
                    symbol=self._config.paper_runtime.symbol,
                    timeframe="1m",
                    now=self._clock(),
                )
        except RuntimeGapError as exc:
            self._log(f"runtime checkpoint gap: {exc.__class__.__name__}")
            return DualLaneResult(None, (), (), "checkpoint_gap")
        except (BybitApiError, ValueError) as exc:
            self._log(f"market data unavailable: {exc.__class__.__name__}")
            return DualLaneResult(None, (), (), "market_data_unavailable")
        if completed is None:
            return DualLaneResult(None, (), (), "no_completed_candle")

        observation = observation_from_completed_candle(
            completed,
            source="bybit_demo_public_candles",
            stale_after_seconds=self._config.risk_rules.stale_after_seconds,
        )
        active_results = ()
        if active_set is not None:
            active_results = (
                self._process_lane(
                    lane=Lane.ACTIVE,
                    trigger_set=active_set,
                    completed=completed,
                    observation=observation,
                    instrument=instrument,
                    adapter=self._active_adapter,
                    candles=candles,
                ),
            )
        test_results = tuple(
            self._process_lane(
                lane=Lane.TEST,
                trigger_set=trigger_set,
                completed=completed,
                observation=observation,
                instrument=instrument,
                adapter=self._test_adapter_factory(),
                candles=candles,
            )
            for trigger_set in self._trigger_set_store.list_testing_sets(completed.symbol, completed.timeframe)
        )
        return DualLaneResult(completed.candle_id, active_results, test_results)

    def run_forever(self, max_cycles: int | None = None) -> None:
        cycles = 0
        while not self._stop_requested:
            self.process_once()
            cycles += 1
            if max_cycles is not None and cycles >= max_cycles:
                break
            time.sleep(self._config.paper_runtime.poll_interval_seconds)

    def stop(self) -> None:
        self._stop_requested = True

    def _process_lane(
        self,
        *,
        lane: Lane,
        trigger_set: TriggerSetVersion,
        completed: CompletedCandle,
        observation: MarketObservation,
        instrument: BybitInstrument,
        adapter: PaperExecutionAdapter,
        candles,
    ) -> RuntimeCycleResult:
        if trigger_set.status not in {TriggerSetStatus.ACTIVE, TriggerSetStatus.TESTING}:
            return RuntimeCycleResult(completed.candle_id, None, skipped_reason="set_not_eligible")
        activation_time = datetime.fromisoformat(trigger_set.created_at)
        if completed.close_time <= activation_time:
            return RuntimeCycleResult(completed.candle_id, None, skipped_reason="set_activation_pending")
        checkpoint = self._runtime_store.get_lane_checkpoint(
            lane=lane.value,
            symbol=completed.symbol,
            timeframe=completed.timeframe,
            trigger_set_id=trigger_set.set_id,
            trigger_set_version=trigger_set.version,
        )
        if checkpoint is not None:
            interval = completed.close_time - completed.open_time
            last_open = datetime.fromisoformat(checkpoint.last_processed_candle_open_time)
            if completed.open_time > last_open + interval:
                self._log(f"lane checkpoint gap: {lane.value} {trigger_set.set_id} {trigger_set.version}")
                return RuntimeCycleResult(completed.candle_id, None, skipped_reason="checkpoint_gap")
        existing = self._runtime_store.get_lane_lifecycle(
            lane=lane.value,
            symbol=completed.symbol,
            timeframe=completed.timeframe,
            candle_id=completed.candle_id,
            trigger_set_id=trigger_set.set_id,
            trigger_set_version=trigger_set.version,
        )
        if existing is not None and existing.status in {"no_signal", "no_intent", "risk_rejected", "test_recorded", "completed", "active_execution_paused"}:
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, None, skipped_reason="already_processed")

        scoped_observation = replace(observation, source=f"{observation.source}|{lane.value}|{trigger_set.set_id}|{trigger_set.version}")
        trigger = PercentagePriceMoveTrigger(self._config.trigger_rule, symbol=self._config.paper_runtime.symbol)
        signal = _scoped_signal(trigger.evaluate(scoped_observation, now=self._clock()), lane, trigger_set)
        self._trace_store.save_trigger_evaluation(signal)
        self._save_lane_lifecycle(lane, trigger_set, completed, "trigger_evaluated", signal_id=signal.signal_id)

        if signal.signal_type is SignalType.NO_SIGNAL:
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "no_signal",
                signal_id=signal.signal_id,
                processed_at=self._clock().isoformat(),
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value)

        if ("TRG-002", "0.1.0") in trigger_set.rule_versions:
            volume_signal = _volume_signal(
                completed=completed,
                candles=candles,
                lane=lane,
                trigger_set=trigger_set,
                now=self._clock(),
                stale_after_seconds=self._config.risk_rules.stale_after_seconds,
            )
            self._trace_store.save_trigger_evaluation(volume_signal)
            if volume_signal.signal_type is not SignalType.CONFIRMED:
                self._save_lane_lifecycle(
                    lane,
                    trigger_set,
                    completed,
                    "no_intent",
                    signal_id=signal.signal_id,
                    processed_at=self._clock().isoformat(),
                    error=volume_signal.reason,
                )
                self._checkpoint_lane(lane, trigger_set, completed)
                return RuntimeCycleResult(
                    completed.candle_id,
                    signal.signal_type.value,
                    skipped_reason="volume_not_confirmed",
                )

        intent = BuyCandidateStrategy(self._config.strategy_rule, self._config.risk_rules).decide(
            signal=signal,
            observation=scoped_observation,
            instrument=instrument,
        )
        if intent is None:
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "no_intent",
                signal_id=signal.signal_id,
                processed_at=self._clock().isoformat(),
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, skipped_reason="no_intent")
        intent = _scoped_intent(intent, lane, trigger_set)
        self._trace_store.save_strategy_decision(intent)

        existing_execution = self._execution_store.get_by_intent(intent.intent_id)
        if existing_execution is not None and lane is Lane.ACTIVE:
            service = ExecutionService(
                config=self._config,
                adapter=adapter,
                store=self._execution_store,
                instrument=instrument,
                available_quote_balance=self._config.paper_runtime.paper_quote_balance,
                execution_lane=lane.value,
                operator_trading_state=self._operator_state_value,
            )
            record = service.reconcile(existing_execution)
            record = replace(record, lane=lane.value, trigger_set_id=trigger_set.set_id, trigger_set_version=trigger_set.version)
            self._execution_store.update(record)
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
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, record.risk_decision_id, True, record.status.value)

        risk = RiskManager(
            config=self._config,
            risk_config=self._config.risk_rules,
            execution_store=self._execution_store,
        ).evaluate(
            intent=intent,
            observation=scoped_observation,
            available_quote_balance=self._config.paper_runtime.paper_quote_balance,
            now=self._clock(),
        )
        risk = _scoped_risk(risk, lane, trigger_set)
        self._trace_store.save_risk_decision(risk)
        self._save_lane_lifecycle(
            lane,
            trigger_set,
            completed,
            "risk_recorded",
            signal_id=signal.signal_id,
            intent_id=intent.intent_id,
            risk_decision_id=risk.risk_decision_id,
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
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, False)

        if lane is Lane.TEST:
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "test_recorded",
                signal_id=signal.signal_id,
                intent_id=intent.intent_id,
                risk_decision_id=risk.risk_decision_id,
                processed_at=self._clock().isoformat(),
            )
            self._checkpoint_lane(lane, trigger_set, completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, True, "test_recorded")

        try:
            service = ExecutionService(
                config=self._config,
                adapter=adapter,
                store=self._execution_store,
                instrument=instrument,
                available_quote_balance=self._config.paper_runtime.paper_quote_balance,
                execution_lane=lane.value,
                operator_trading_state=self._operator_state_value,
            )
            record = service.submit_approved_limit_order(intent=intent, risk_decision=risk)
            record = service.reconcile(record)
        except ExecutionError as exc:
            if "operator pause" in str(exc):
                self._save_lane_lifecycle(
                    lane,
                    trigger_set,
                    completed,
                    "active_execution_paused",
                    signal_id=signal.signal_id,
                    intent_id=intent.intent_id,
                    risk_decision_id=risk.risk_decision_id,
                    processed_at=self._clock().isoformat(),
                    error="operator_paused",
                )
                self._checkpoint_lane(lane, trigger_set, completed)
                return RuntimeCycleResult(
                    completed.candle_id,
                    signal.signal_type.value,
                    intent.intent_id,
                    risk.risk_decision_id,
                    False,
                    skipped_reason="operator_paused",
                )
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "execution_error",
                signal_id=signal.signal_id,
                intent_id=intent.intent_id,
                risk_decision_id=risk.risk_decision_id,
                error=exc.__class__.__name__,
            )
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, True, skipped_reason="execution_error")
        except Exception as exc:
            self._save_lane_lifecycle(
                lane,
                trigger_set,
                completed,
                "execution_error",
                signal_id=signal.signal_id,
                intent_id=intent.intent_id,
                risk_decision_id=risk.risk_decision_id,
                error=exc.__class__.__name__,
            )
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, True, skipped_reason="execution_error")
        record = replace(record, lane=lane.value, trigger_set_id=trigger_set.set_id, trigger_set_version=trigger_set.version)
        self._execution_store.update(record)
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
        )
        self._checkpoint_lane(lane, trigger_set, completed)
        return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, True, record.status.value)

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
                runtime_version=self._config.paper_runtime.version,
            )
        )

    def _validate_safe_config(self) -> None:
        from triggertrade.services.runtime import PaperTradingRuntime

        PaperTradingRuntime(
            config=self._config,
            market_client=self._market_client,
            execution_store=self._execution_store,
            trace_store=self._trace_store,
            runtime_store=self._runtime_store,
        )._validate_safe_config()
        if self._config.execution_venue is not ExecutionVenue.LOCAL_PAPER:
            raise ConfigError("dual-lane runtime requires local paper execution")

    def _log(self, message: str) -> None:
        self._logger(f"triggertrade dual-lane runtime: {message}")

    def _operator_state_value(self) -> str:
        if self._operator_state_store is None:
            return "TRADING_ENABLED"
        return self._operator_state_store.get_trading_state().state.value



def _volume_signal(
    *,
    completed: CompletedCandle,
    candles,
    lane: Lane,
    trigger_set: TriggerSetVersion,
    now: datetime,
    stale_after_seconds: int,
) -> Signal:
    previous = tuple(
        candle
        for candle in sorted(candles, key=lambda item: item.start_time_ms)
        if candle.start_time_ms < completed.candle.start_time_ms
    )
    evaluation = RobustVolumeConfirmationTrigger(
        VolumeConfirmationConfig(stale_after_seconds=stale_after_seconds),
        symbol=completed.symbol,
    ).evaluate(
        VolumeCandleWindow(
            symbol=completed.symbol,
            timeframe=completed.timeframe,
            observed_at=completed.close_time,
            current_candle=completed.candle,
            previous_candles=previous[-60:],
            current_candle_completed=True,
        ),
        now=now,
    )
    snapshot = {
        "current_volume": evaluation.current_volume or "",
        "median_volume_60": evaluation.median_volume_60 or "",
        "relative_volume": evaluation.relative_volume or "",
        "volume_percentile": evaluation.volume_percentile or "",
        "relative_volume_threshold": evaluation.relative_volume_threshold,
        "percentile_threshold": evaluation.percentile_threshold,
        "missing_data_reason": evaluation.missing_data_reason or "",
        "stale_data_reason": evaluation.stale_data_reason or "",
        "stale_after_seconds": str(stale_after_seconds),
    }
    return Signal(
        signal_id=_scoped_id(evaluation.evaluation_id, lane, trigger_set),
        trigger_rule_id=evaluation.rule_id,
        trigger_rule_version=evaluation.rule_version,
        symbol=evaluation.symbol,
        observed_at=evaluation.observed_at,
        window=evaluation.timeframe,
        input_snapshot=snapshot,
        condition_result=evaluation.condition_result,
        signal_type=SignalType.CONFIRMED if evaluation.result is VolumeConfirmationResult.CONFIRMED else SignalType.NOT_CONFIRMED,
        reason=evaluation.missing_data_reason or evaluation.stale_data_reason or evaluation.result.value.lower(),
        lane=lane.value,
        trigger_set_id=trigger_set.set_id,
        trigger_set_version=trigger_set.version,
    )

def _scoped_signal(signal, lane: Lane, trigger_set: TriggerSetVersion):
    scoped_id = _scoped_id(signal.signal_id, lane, trigger_set)
    return replace(signal, signal_id=scoped_id, lane=lane.value, trigger_set_id=trigger_set.set_id, trigger_set_version=trigger_set.version)


def _scoped_intent(intent, lane: Lane, trigger_set: TriggerSetVersion):
    scoped_id = _scoped_id(intent.intent_id, lane, trigger_set)
    return replace(
        intent,
        intent_id=scoped_id,
        lane=lane.value,
        trigger_set_id=trigger_set.set_id,
        trigger_set_version=trigger_set.version,
    )


def _scoped_risk(risk, lane: Lane, trigger_set: TriggerSetVersion):
    scoped_id = _scoped_id(risk.risk_decision_id, lane, trigger_set)
    return replace(risk, risk_decision_id=scoped_id, lane=lane.value, trigger_set_id=trigger_set.set_id, trigger_set_version=trigger_set.version)


def _scoped_id(value: str, lane: Lane, trigger_set: TriggerSetVersion) -> str:
    digest = sha256(f"{lane.value}|{trigger_set.set_id}|{trigger_set.version}|{value}".encode("utf-8")).hexdigest()[:24]
    prefix = value.split("-", 1)[0] if "-" in value else "id"
    return f"{prefix}-{digest}"


def _bybit_interval(timeframe: str) -> str:
    if timeframe.strip().lower() in {"1", "1m"}:
        return "1"
    raise ValueError("only 1m candle interval is supported")
