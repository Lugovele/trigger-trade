"""Continuous paper trading runtime for the proven TriggerTrade slice."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
import time
from typing import Callable

from triggertrade.config import (
    AppConfig,
    BybitEnvironment,
    ConfigError,
    ExecutionVenue,
    Market,
    TradingMode,
    load_config,
)
from triggertrade.execution import ExecutionError, ExecutionService, PaperExecutionAdapter
from triggertrade.execution.service import client_order_id_for_intent
from triggertrade.exchanges import BybitApiError, BybitDemoClient
from triggertrade.market_data import BybitCandle, BybitInstrument, MarketObservation, parse_spot_candles, parse_spot_instrument
from triggertrade.persistence import (
    CandleLifecycle,
    ExecutionStore,
    RuntimeCheckpoint,
    RuntimeStore,
    TraceStore,
)
from triggertrade.risk import RiskManager
from triggertrade.services.bootstrap import ensure_runtime_registry_initialized, merged_runtime_env, runtime_db_path
from triggertrade.strategies import BuyCandidateStrategy
from triggertrade.triggers import PercentagePriceMoveTrigger, SignalType


class RuntimeStatus(StrEnum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass(frozen=True)
class RuntimeCycleResult:
    candle_id: str | None
    signal_type: str | None
    intent_id: str | None = None
    risk_decision_id: str | None = None
    risk_approved: bool | None = None
    execution_status: str | None = None
    skipped_reason: str | None = None


@dataclass(frozen=True)
class CompletedCandle:
    symbol: str
    timeframe: str
    candle_id: str
    open_time: datetime
    close_time: datetime
    candle: BybitCandle
    previous_candle: BybitCandle


class PaperTradingRuntime:
    def __init__(
        self,
        *,
        config: AppConfig,
        market_client: BybitDemoClient,
        execution_store: ExecutionStore,
        trace_store: TraceStore,
        runtime_store: RuntimeStore,
        paper_adapter: PaperExecutionAdapter | None = None,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[int], None] | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        self._config = config
        self._market_client = market_client
        self._execution_store = execution_store
        self._trace_store = trace_store
        self._runtime_store = runtime_store
        self._paper_adapter = paper_adapter or PaperExecutionAdapter(clock_ms=lambda: int(time.time() * 1000))
        self._clock = clock or (lambda: datetime.now(UTC))
        self._sleeper = sleeper or time.sleep
        self._logger = logger or (lambda message: print(message))
        self.status = RuntimeStatus.STOPPED
        self._stop_requested = False

    def process_once(self) -> RuntimeCycleResult:
        self._validate_safe_config()
        try:
            instrument = parse_spot_instrument(
                self._market_client.instrument_metadata(self._config.paper_runtime.symbol).result
            )
            candles = parse_spot_candles(
                self._market_client.recent_candles(
                    self._config.paper_runtime.symbol,
                    interval=_bybit_interval(self._config.paper_runtime.candle_interval),
                    limit=4,
                ).result
            )
            checkpoint = self._runtime_store.get_checkpoint(
                self._config.paper_runtime.symbol,
                self._config.paper_runtime.candle_interval,
            )
            completed = next_completed_candle(
                candles,
                symbol=self._config.paper_runtime.symbol,
                timeframe=self._config.paper_runtime.candle_interval,
                now=self._clock(),
                checkpoint=checkpoint,
            )
        except RuntimeGapError as exc:
            self._log(f"runtime checkpoint gap: {exc.__class__.__name__}")
            return RuntimeCycleResult(None, None, skipped_reason="checkpoint_gap")
        except (BybitApiError, ValueError) as exc:
            self._log(f"market data unavailable: {exc.__class__.__name__}")
            return RuntimeCycleResult(None, None, skipped_reason="market_data_unavailable")

        if completed is None:
            latest = latest_completed_candle(
                candles,
                symbol=self._config.paper_runtime.symbol,
                timeframe=self._config.paper_runtime.candle_interval,
                now=self._clock(),
            )
            if latest is not None and self._is_checkpointed(latest):
                return RuntimeCycleResult(latest.candle_id, None, skipped_reason="already_processed")
            return RuntimeCycleResult(None, None, skipped_reason="no_completed_candle")

        existing = self._runtime_store.get_lifecycle(completed.candle_id)
        if existing is not None and existing.status in {"no_signal", "no_intent", "risk_rejected", "completed"}:
            self._checkpoint(completed)
            return RuntimeCycleResult(completed.candle_id, None, skipped_reason="already_durable")

        observation = observation_from_completed_candle(
            completed,
            source="bybit_demo_public_candles",
            stale_after_seconds=self._config.risk_rules.stale_after_seconds,
        )
        trigger = PercentagePriceMoveTrigger(self._config.trigger_rule, symbol=self._config.paper_runtime.symbol)
        signal = trigger.evaluate(observation, now=self._clock())
        self._trace_store.save_trigger_evaluation(signal)
        self._runtime_store.save_lifecycle(
            CandleLifecycle(
                candle_id=completed.candle_id,
                symbol=completed.symbol,
                timeframe=completed.timeframe,
                candle_open_time=completed.open_time.isoformat(),
                status="trigger_evaluated",
                signal_id=signal.signal_id,
            )
        )

        if signal.signal_type is SignalType.NO_SIGNAL:
            self._runtime_store.save_lifecycle(
                CandleLifecycle(
                    candle_id=completed.candle_id,
                    symbol=completed.symbol,
                    timeframe=completed.timeframe,
                    candle_open_time=completed.open_time.isoformat(),
                    status="no_signal",
                    signal_id=signal.signal_id,
                    processed_at=self._clock().isoformat(),
                )
            )
            self._checkpoint(completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value)

        strategy = BuyCandidateStrategy(self._config.strategy_rule, self._config.risk_rules)
        intent = strategy.decide(signal=signal, observation=observation, instrument=instrument)
        if intent is None:
            self._runtime_store.save_lifecycle(
                CandleLifecycle(
                    candle_id=completed.candle_id,
                    symbol=completed.symbol,
                    timeframe=completed.timeframe,
                    candle_open_time=completed.open_time.isoformat(),
                    status="no_intent",
                    signal_id=signal.signal_id,
                    processed_at=self._clock().isoformat(),
                )
            )
            self._checkpoint(completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, skipped_reason="no_intent")

        self._trace_store.save_strategy_decision(intent)
        existing_execution = self._execution_store.get_by_intent(intent.intent_id)
        if existing_execution is not None:
            service = ExecutionService(
                config=self._config,
                adapter=self._paper_adapter,
                store=self._execution_store,
                instrument=instrument,
                available_quote_balance=self._config.paper_runtime.paper_quote_balance,
            )
            record = service.reconcile(existing_execution)
            if record.status.value == "unknown":
                self._runtime_store.save_lifecycle(
                    CandleLifecycle(
                        candle_id=completed.candle_id,
                        symbol=completed.symbol,
                        timeframe=completed.timeframe,
                        candle_open_time=completed.open_time.isoformat(),
                        status="execution_unknown",
                        signal_id=signal.signal_id,
                        intent_id=intent.intent_id,
                        execution_intent_id=record.intent_id,
                        error="execution_reconciliation_unknown",
                    )
                )
                return RuntimeCycleResult(
                    completed.candle_id,
                    signal.signal_type.value,
                    intent.intent_id,
                    execution_status=record.status.value,
                    skipped_reason="execution_unknown",
                )
            self._runtime_store.save_lifecycle(
                CandleLifecycle(
                    candle_id=completed.candle_id,
                    symbol=completed.symbol,
                    timeframe=completed.timeframe,
                    candle_open_time=completed.open_time.isoformat(),
                    status="completed",
                    signal_id=signal.signal_id,
                    intent_id=intent.intent_id,
                    risk_decision_id=existing_execution.risk_decision_id,
                    execution_intent_id=record.intent_id,
                    processed_at=self._clock().isoformat(),
                )
            )
            self._checkpoint(completed)
            return RuntimeCycleResult(
                completed.candle_id,
                signal.signal_type.value,
                intent.intent_id,
                existing_execution.risk_decision_id,
                True,
                record.status.value,
            )

        risk = RiskManager(
            config=self._config,
            risk_config=self._config.risk_rules,
            execution_store=self._execution_store,
        ).evaluate(
            intent=intent,
            observation=observation,
            available_quote_balance=self._config.paper_runtime.paper_quote_balance,
            now=self._clock(),
        )
        self._trace_store.save_risk_decision(risk)
        self._runtime_store.save_lifecycle(
            CandleLifecycle(
                candle_id=completed.candle_id,
                symbol=completed.symbol,
                timeframe=completed.timeframe,
                candle_open_time=completed.open_time.isoformat(),
                status="risk_recorded",
                signal_id=signal.signal_id,
                intent_id=intent.intent_id,
                risk_decision_id=risk.risk_decision_id,
            )
        )

        if not risk.approved:
            self._runtime_store.save_lifecycle(
                CandleLifecycle(
                    candle_id=completed.candle_id,
                    symbol=completed.symbol,
                    timeframe=completed.timeframe,
                    candle_open_time=completed.open_time.isoformat(),
                    status="risk_rejected",
                    signal_id=signal.signal_id,
                    intent_id=intent.intent_id,
                    risk_decision_id=risk.risk_decision_id,
                    processed_at=self._clock().isoformat(),
                )
            )
            self._checkpoint(completed)
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, False)

        service = ExecutionService(
            config=self._config,
            adapter=self._paper_adapter,
            store=self._execution_store,
            instrument=instrument,
            available_quote_balance=self._config.paper_runtime.paper_quote_balance,
        )
        try:
            record = service.submit_approved_limit_order(intent=intent, risk_decision=risk)
            record = service.reconcile(record)
        except ExecutionError as exc:
            self._runtime_store.save_lifecycle(
                CandleLifecycle(
                    candle_id=completed.candle_id,
                    symbol=completed.symbol,
                    timeframe=completed.timeframe,
                    candle_open_time=completed.open_time.isoformat(),
                    status="execution_error",
                    signal_id=signal.signal_id,
                    intent_id=intent.intent_id,
                    risk_decision_id=risk.risk_decision_id,
                    error=exc.__class__.__name__,
                )
            )
            return RuntimeCycleResult(completed.candle_id, signal.signal_type.value, intent.intent_id, risk.risk_decision_id, True, skipped_reason="execution_error")
        if record.status.value == "unknown":
            self._runtime_store.save_lifecycle(
                CandleLifecycle(
                    candle_id=completed.candle_id,
                    symbol=completed.symbol,
                    timeframe=completed.timeframe,
                    candle_open_time=completed.open_time.isoformat(),
                    status="execution_unknown",
                    signal_id=signal.signal_id,
                    intent_id=intent.intent_id,
                    risk_decision_id=risk.risk_decision_id,
                    execution_intent_id=record.intent_id,
                    error="execution_reconciliation_unknown",
                )
            )
            return RuntimeCycleResult(
                completed.candle_id,
                signal.signal_type.value,
                intent.intent_id,
                risk.risk_decision_id,
                True,
                record.status.value,
                skipped_reason="execution_unknown",
            )

        self._runtime_store.save_lifecycle(
            CandleLifecycle(
                candle_id=completed.candle_id,
                symbol=completed.symbol,
                timeframe=completed.timeframe,
                candle_open_time=completed.open_time.isoformat(),
                status="completed",
                signal_id=signal.signal_id,
                intent_id=intent.intent_id,
                risk_decision_id=risk.risk_decision_id,
                execution_intent_id=record.intent_id,
                processed_at=self._clock().isoformat(),
            )
        )
        self._checkpoint(completed)
        return RuntimeCycleResult(
            completed.candle_id,
            signal.signal_type.value,
            intent.intent_id,
            risk.risk_decision_id,
            True,
            record.status.value,
        )

    def run_forever(self, max_cycles: int | None = None) -> None:
        self._validate_safe_config()
        self.status = RuntimeStatus.STARTING
        cycles = 0
        try:
            self.status = RuntimeStatus.RUNNING
            while not self._stop_requested:
                self.process_once()
                cycles += 1
                if max_cycles is not None and cycles >= max_cycles:
                    break
                self._sleeper(self._config.paper_runtime.poll_interval_seconds)
        except KeyboardInterrupt:
            self._log("shutdown requested")
        except Exception as exc:
            self.status = RuntimeStatus.ERROR
            self._log(f"runtime error: {exc.__class__.__name__}")
            return
        finally:
            if self.status is not RuntimeStatus.ERROR:
                self.status = RuntimeStatus.STOPPED

    def stop(self) -> None:
        self._stop_requested = True
        self.status = RuntimeStatus.STOPPING

    def _validate_safe_config(self) -> None:
        if self._config.trading_mode is not TradingMode.PAPER:
            raise ConfigError("paper runtime requires paper trading mode")
        if self._config.live_trading_enabled:
            raise ConfigError("paper runtime requires live trading disabled")
        if self._config.execution_venue is not ExecutionVenue.LOCAL_PAPER:
            raise ConfigError("continuous paper runtime requires local_paper execution venue")
        if self._config.bybit.environment is not BybitEnvironment.DEMO:
            raise ConfigError("paper runtime requires Bybit Demo public market data")
        if self._config.bybit.base_url != "https://api-demo.bybit.com":
            raise ConfigError("paper runtime requires the Bybit Demo base URL")
        if self._config.market is not Market.SPOT:
            raise ConfigError("paper runtime supports only spot market data")
        if self._config.paper_runtime.symbol != "BTCUSDT":
            raise ConfigError("paper runtime supports only BTCUSDT")
        if _bybit_interval(self._config.paper_runtime.candle_interval) != "1":
            raise ConfigError("paper runtime currently supports only the 1 minute BTCUSDT candle interval")

    def _is_checkpointed(self, candle: CompletedCandle) -> bool:
        checkpoint = self._runtime_store.get_checkpoint(candle.symbol, candle.timeframe)
        return checkpoint is not None and checkpoint.last_processed_candle_id == candle.candle_id

    def _checkpoint(self, candle: CompletedCandle) -> None:
        self._runtime_store.checkpoint(
            RuntimeCheckpoint(
                symbol=candle.symbol,
                timeframe=candle.timeframe,
                last_processed_candle_id=candle.candle_id,
                last_processed_candle_open_time=candle.open_time.isoformat(),
                last_processed_at=self._clock().isoformat(),
                runtime_version=self._config.paper_runtime.version,
            )
        )

    def _log(self, message: str) -> None:
        self._logger(f"triggertrade paper runtime: {message}")


def latest_completed_candle(
    candles: tuple[BybitCandle, ...],
    *,
    symbol: str,
    timeframe: str,
    now: datetime,
) -> CompletedCandle | None:
    interval = interval_delta(timeframe)
    sorted_candles = sorted(candles, key=lambda candle: candle.start_time_ms)
    completed = [
        candle
        for candle in sorted_candles
        if _open_time(candle).replace(tzinfo=UTC) + interval <= now
    ]
    if len(completed) < 2:
        return None
    latest = completed[-1]
    previous = completed[-2]
    return _completed_candle(symbol, timeframe, interval, latest, previous)


def next_completed_candle(
    candles: tuple[BybitCandle, ...],
    *,
    symbol: str,
    timeframe: str,
    now: datetime,
    checkpoint: RuntimeCheckpoint | None,
) -> CompletedCandle | None:
    interval = interval_delta(timeframe)
    sorted_candles = sorted(candles, key=lambda candle: candle.start_time_ms)
    completed = [
        candle
        for candle in sorted_candles
        if _open_time(candle).replace(tzinfo=UTC) + interval <= now
    ]
    if len(completed) < 2:
        return None
    candidates = [
        _completed_candle(symbol, timeframe, interval, completed[index], completed[index - 1])
        for index in range(1, len(completed))
    ]
    if checkpoint is None:
        return candidates[-1]
    last_open = datetime.fromisoformat(checkpoint.last_processed_candle_open_time)
    for candidate in candidates:
        if candidate.open_time > last_open:
            if candidate.open_time != last_open + interval:
                raise RuntimeGapError("first new completed candle is outside the checkpoint continuity window")
            return candidate
    return None


def _completed_candle(
    symbol: str,
    timeframe: str,
    interval: timedelta,
    latest: BybitCandle,
    previous: BybitCandle,
) -> CompletedCandle:
    open_time = _open_time(latest)
    return CompletedCandle(
        symbol=symbol,
        timeframe=timeframe,
        candle_id=candle_id(symbol, timeframe, open_time),
        open_time=open_time,
        close_time=open_time + interval,
        candle=latest,
        previous_candle=previous,
    )


def observation_from_completed_candle(
    candle: CompletedCandle,
    *,
    source: str,
    stale_after_seconds: int,
) -> MarketObservation:
    return MarketObservation(
        symbol=candle.symbol,
        observed_at=candle.close_time,
        current_price=candle.candle.close,
        previous_price=candle.previous_candle.close,
        window=_window_label(candle.timeframe),
        source=source,
        stale_after_seconds=stale_after_seconds,
    )


def candle_id(symbol: str, timeframe: str, open_time: datetime) -> str:
    return f"{symbol.upper()}:{_window_label(timeframe)}:{open_time.astimezone(UTC).isoformat()}"


def interval_delta(timeframe: str) -> timedelta:
    normalized = _window_label(timeframe)
    if normalized != "1m":
        raise ValueError("only 1m candle interval is supported")
    return timedelta(minutes=1)


def _bybit_interval(timeframe: str) -> str:
    if timeframe.strip().lower() in {"1", "1m"}:
        return "1"
    raise ValueError("only 1m candle interval is supported")


def _window_label(timeframe: str) -> str:
    if timeframe.strip().lower() in {"1", "1m"}:
        return "1m"
    raise ValueError("only 1m candle interval is supported")


def _open_time(candle: BybitCandle) -> datetime:
    return datetime.fromtimestamp(candle.start_time_ms / 1000, UTC)


class RuntimeGapError(RuntimeError):
    pass


def build_runtime_from_env(env: dict[str, str]):
    from triggertrade.persistence import TriggerSetStore
    from triggertrade.persistence import OperatorStateStore
    from triggertrade.services.dual_lane_runtime import DualLaneRuntime

    runtime_env = dict(env)
    runtime_env["TRIGGERTRADE_EXECUTION_VENUE"] = ExecutionVenue.LOCAL_PAPER.value
    config = load_config(runtime_env)
    db_path = runtime_db_path(config, runtime_env)
    ensure_runtime_registry_initialized(db_path)
    market_client = BybitDemoClient(config=config.bybit)
    return DualLaneRuntime(
        config=config,
        market_client=market_client,
        execution_store=ExecutionStore(db_path),
        trace_store=TraceStore(db_path),
        runtime_store=RuntimeStore(db_path),
        trigger_set_store=TriggerSetStore(db_path),
        operator_state_store=OperatorStateStore(db_path),
    )


def main() -> int:
    env = merged_runtime_env()
    try:
        build_runtime_from_env(env).run_forever()
    except ConfigError as exc:
        print(f"paper runtime refused to start: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
