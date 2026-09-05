"""Historical replay engine reusing TriggerTrade runtime domain components."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import sqlite3

from triggertrade.accounting import ACCOUNTING_VERSION
from triggertrade.analytics import TradePerformanceFact, compute_futures_performance
from triggertrade.config import AppConfig
from triggertrade.execution.futures import FundingEstimate, FuturesExecutionConfig, FuturesRiskManager, PositionState, estimate_costs
from triggertrade.market_data import FuturesAccountState, FuturesInstrumentMetadata, RegimeEvaluationWindow, evaluate_market_regime, futures_event_from_completed_candle, volume_window_from_futures_event
from triggertrade.market_data.futures import ContractCategory
from triggertrade.persistence import FuturesExecutionStore, RuntimeStore, TraceStore, TriggerSetStore
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.services.futures_runtime import _intent_price, _intent_quantity, _is_futures_set
from triggertrade.services.runtime import CompletedCandle, candle_id
from triggertrade.strategies import IntegrationDirectionalFuturesStrategy
from triggertrade.trigger_sets import Lane, TriggerSetVersion
from triggertrade.triggers import PercentagePriceMoveTrigger, RobustVolumeConfirmationTrigger, Signal, SignalType, VolumeConfirmationConfig, VolumeConfirmationResult

from .data import cache_hash, historical_to_bybit, validate_historical_candles
from .models import BACKTEST_COST_MODEL_VERSION, BACKTEST_DATA_SOURCE_VERSION, BACKTEST_EVIDENCE_SOURCE, BACKTEST_SIMULATOR_VERSION, BacktestPlan, BacktestResult, BacktestRun, BacktestStatus, HistoricalCandle
from .simulator import BacktestFuturesSimulator, BacktestSimulationError
from .store import BacktestStore


class BacktestEngineError(ValueError):
    pass


class BacktestEngine:
    def __init__(
        self,
        *,
        config: AppConfig,
        trigger_set_store: TriggerSetStore,
        accounting_store: FuturesAccountingStore,
        execution_store: FuturesExecutionStore,
        trace_store: TraceStore,
        runtime_store: RuntimeStore,
        backtest_store: BacktestStore,
        instrument: FuturesInstrumentMetadata,
    ) -> None:
        self._config = config
        self._trigger_set_store = trigger_set_store
        self._accounting_store = accounting_store
        self._execution_store = execution_store
        self._trace_store = trace_store
        self._runtime_store = runtime_store
        self._backtest_store = backtest_store
        self._instrument = instrument

    def run(self, *, plan: BacktestPlan, trigger_set_id: str, trigger_set_version: str, candles: tuple[HistoricalCandle, ...], created_at: datetime | None = None) -> BacktestResult:
        validated = validate_historical_candles(candles, symbol=plan.symbol, category=plan.category, timeframe=plan.timeframe)
        trigger_set = self._trigger_set_store.get_set(trigger_set_id, trigger_set_version)
        if trigger_set is None:
            raise BacktestEngineError("unknown trigger set version")
        if not _is_futures_set(trigger_set):
            raise BacktestEngineError("backtest v1 replays futures trigger sets only")
        if trigger_set.symbol != plan.symbol or trigger_set.timeframe != "1m":
            raise BacktestEngineError("trigger set scope does not match backtest plan")
        _validate_warmup(plan, validated)
        run = _run_from_inputs(config=self._config, plan=plan, trigger_set=trigger_set, candles=validated, instrument=self._instrument, created_at=created_at or plan.research_end)
        created = self._backtest_store.create_run(run)
        if not created:
            existing = self._backtest_store.get_run(run.backtest_run_id)
            if existing is not None and existing["result_payload"] is not None:
                return _result_from_payload(existing["result_payload"])
        self._backtest_store.update_status(run.backtest_run_id, BacktestStatus.RUNNING)
        result, trade_ids = self._run_events(run=run, trigger_set=trigger_set, candles=validated)
        self._backtest_store.save_run_trades(run_id=run.backtest_run_id, trade_ids=tuple(trade_ids))
        self._backtest_store.save_result(result)
        self._backtest_store.update_status(run.backtest_run_id, BacktestStatus.COMPLETED)
        return result

    def _run_events(self, *, run: BacktestRun, trigger_set: TriggerSetVersion, candles: tuple[HistoricalCandle, ...]) -> tuple[BacktestResult, tuple[str, ...]]:
        signals = intents = trades = rejected = no_action = technical = candles_processed = 0
        trade_ids: list[str] = []
        by_regime: dict[str, int] = {}
        simulator = BacktestFuturesSimulator(accounting_store=self._accounting_store, maker_fee_rate=run.maker_fee_rate, taker_fee_rate=run.taker_fee_rate, spread_bps=run.spread_bps, slippage_bps=run.slippage_bps)
        by_open = {item.open_time: item for item in candles}
        evaluation_start = datetime.fromisoformat(run.evaluation_start)
        evaluation_end = datetime.fromisoformat(run.evaluation_end)
        for index in range(1, len(candles) - 1):
            current = candles[index]
            if current.close_time < evaluation_start or current.close_time > evaluation_end:
                continue
            candles_processed += 1
            completed = _completed_from_history(current, candles[index - 1])
            event = futures_event_from_completed_candle(completed=completed, source=f"{BACKTEST_EVIDENCE_SOURCE.lower()}_linear_kline", instrument_version="LinearPerpetual:USDT")
            history_to_now = tuple(historical_to_bybit(candle) for candle in candles[: index + 1])
            regime = evaluate_market_regime(RegimeEvaluationWindow(symbol=event.symbol, timeframe=event.timeframe, observed_at=event.close_time, candles=history_to_now, category=event.category, current_candle_completed=True))
            signal = self._price_signal(trigger_set=trigger_set, completed=completed, event=event)
            self._trace_store.save_trigger_evaluation(replace(signal, lane=BACKTEST_EVIDENCE_SOURCE))
            if signal.signal_type is SignalType.NO_SIGNAL:
                no_action += 1
                continue
            signals += 1
            signal_ids = [signal.signal_id]
            volume_signal = None
            if ("TRG-002", "0.2.0") in trigger_set.rule_versions:
                volume_signal = self._volume_signal(trigger_set=trigger_set, completed=completed, event=event, history=history_to_now[:-1])
                self._trace_store.save_trigger_evaluation(replace(volume_signal, lane=BACKTEST_EVIDENCE_SOURCE))
                signal_ids.append(volume_signal.signal_id)
                if volume_signal.signal_type is not SignalType.CONFIRMED:
                    no_action += 1
                    continue
            quantity = _intent_quantity(event.close, self._instrument, self._config.futures_runtime.max_position_notional)
            if quantity is None:
                no_action += 1
                continue
            decision = IntegrationDirectionalFuturesStrategy().decide(
                lane=Lane.TEST,
                trigger_set=trigger_set,
                event=event,
                primary_signal=signal,
                volume_signal=volume_signal,
                regime_context=regime,
                position_state=PositionState.FLAT,
                quantity=quantity,
                limit_price=_intent_price(event.close, self._instrument, passive=False),
                leverage=self._config.futures_runtime.leverage,
                expected_gross_move=self._config.futures_runtime.demo_expected_gross_move,
                created_at=event.close_time,
            )
            if decision.intent is None:
                no_action += 1
                continue
            intent = replace(decision.intent, lane=BACKTEST_EVIDENCE_SOURCE, intent_id=f"bt-{decision.intent.intent_id}")
            self._trace_store.save_futures_strategy_decision(intent, tuple(signal_ids))
            intents += 1
            cost = estimate_costs(
                notional=intent.quantity * intent.price,
                maker_fee_rate=run.maker_fee_rate,
                taker_fee_rate=run.taker_fee_rate,
                spread_cost=intent.quantity * intent.price * run.spread_bps / Decimal("10000"),
                slippage_cost=intent.quantity * intent.price * run.slippage_bps / Decimal("10000"),
                funding_cost=Decimal("0"),
            )
            risk = FuturesRiskManager(config=_execution_config(self._config), store=self._execution_store, minimum_net_edge=self._config.futures_runtime.minimum_net_edge, max_position_notional=self._config.futures_runtime.max_position_notional, max_simultaneous_exposure=self._config.futures_runtime.max_position_notional).evaluate(
                intent=intent,
                instrument=self._instrument,
                account=_backtest_account(self._instrument, self._config.futures_runtime.leverage, self._config.futures_runtime.max_position_notional),
                cost=cost,
                funding=FundingEstimate(None, None, Decimal("0"), Decimal("0"), capability="available"),
            )
            self._trace_store.save_futures_risk_decision(risk, trigger_set_id=trigger_set.set_id, trigger_set_version=trigger_set.version)
            if not risk.approved:
                rejected += 1
                continue
            next_candle = by_open.get(current.close_time)
            if next_candle is None:
                technical += 1
                continue
            try:
                trade_id = simulator.simulate_closed_trade(backtest_run_id=run.backtest_run_id, intent=intent, next_candle=next_candle)
            except BacktestSimulationError:
                technical += 1
                continue
            trade_ids.append(trade_id)
            trades += 1
            by_regime[intent.regime_state or "unavailable"] = by_regime.get(intent.regime_state or "unavailable", 0) + 1
        facts = _trade_facts(self._accounting_store, trade_ids)
        metrics = compute_futures_performance(set_id=trigger_set.set_id, version=trigger_set.version, status="BACKTEST", trades=facts, include_direction_breakdown=True)
        return BacktestResult(run.backtest_run_id, BacktestStatus.COMPLETED, candles_processed, signals, intents, trades, metrics.closed_trades, rejected, no_action, technical, metrics.net_pnl, metrics.expectancy_per_trade, metrics.profit_factor, metrics.max_drawdown, metrics.fees, metrics.funding, metrics.long.closed_trades if metrics.long else 0, metrics.short.closed_trades if metrics.short else 0, by_regime), tuple(trade_ids)

    def _price_signal(self, *, trigger_set: TriggerSetVersion, completed: CompletedCandle, event) -> Signal:
        observation = event.to_market_observation(stale_after_seconds=self._config.risk_rules.stale_after_seconds)
        observation = replace(observation, source=f"{observation.source}|BACKTEST|{trigger_set.set_id}|{trigger_set.version}")
        signal = PercentagePriceMoveTrigger(replace(self._config.trigger_rule, version="0.2.0"), symbol=self._config.futures_runtime.symbol).evaluate(observation, now=event.close_time)
        return replace(signal, signal_id=_backtest_signal_id(trigger_set, signal.signal_id), lane=Lane.TEST.value, trigger_set_id=trigger_set.set_id, trigger_set_version=trigger_set.version)

    def _volume_signal(self, *, trigger_set: TriggerSetVersion, completed: CompletedCandle, event, history) -> Signal:
        evaluation = RobustVolumeConfirmationTrigger(VolumeConfirmationConfig(version="0.2.0", stale_after_seconds=self._config.risk_rules.stale_after_seconds), symbol=completed.symbol).evaluate(volume_window_from_futures_event(event, previous_candles=tuple(history[-60:])), now=event.close_time)
        return Signal(_backtest_signal_id(trigger_set, evaluation.evaluation_id), evaluation.rule_id, evaluation.rule_version, evaluation.symbol, evaluation.observed_at, evaluation.timeframe, {"category": "linear", "evidence_source": BACKTEST_EVIDENCE_SOURCE}, evaluation.condition_result, SignalType.CONFIRMED if evaluation.result is VolumeConfirmationResult.CONFIRMED else SignalType.NOT_CONFIRMED, evaluation.missing_data_reason or evaluation.stale_data_reason or evaluation.result.value.lower(), Lane.TEST.value, trigger_set.set_id, trigger_set.version)


def _backtest_signal_id(trigger_set: TriggerSetVersion, raw_id: str) -> str:
    digest = sha256("|".join([BACKTEST_EVIDENCE_SOURCE, trigger_set.set_id, trigger_set.version, raw_id]).encode("utf-8")).hexdigest()[:16]
    return f"btsig-{digest}-{raw_id}"


def run_backtest(*, config: AppConfig, db_path, trigger_set_id: str, trigger_set_version: str, plan: BacktestPlan, candles: tuple[HistoricalCandle, ...], instrument: FuturesInstrumentMetadata) -> BacktestResult:
    return BacktestEngine(config=config, trigger_set_store=TriggerSetStore(db_path), accounting_store=FuturesAccountingStore(db_path), execution_store=FuturesExecutionStore(db_path), trace_store=TraceStore(db_path), runtime_store=RuntimeStore(db_path), backtest_store=BacktestStore(db_path), instrument=instrument).run(plan=plan, trigger_set_id=trigger_set_id, trigger_set_version=trigger_set_version, candles=candles)


def _run_from_inputs(*, config: AppConfig, plan: BacktestPlan, trigger_set: TriggerSetVersion, candles: tuple[HistoricalCandle, ...], instrument: FuturesInstrumentMetadata, created_at: datetime) -> BacktestRun:
    assumptions = _assumptions_snapshot(config=config, plan=plan, trigger_set=trigger_set, instrument=instrument)
    digest = sha256(
        json.dumps(
            {
                "set": [trigger_set.set_id, trigger_set.version, trigger_set.rule_versions],
                "plan": assumptions,
                "cache_hash": cache_hash(candles),
                "versions": [BACKTEST_SIMULATOR_VERSION, BACKTEST_COST_MODEL_VERSION, ACCOUNTING_VERSION, BACKTEST_DATA_SOURCE_VERSION],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:24]
    return BacktestRun(f"btr-{digest}", created_at.astimezone(UTC).isoformat(), BacktestStatus.CREATED, plan.symbol, plan.category, plan.timeframe, plan.research_start.astimezone(UTC).isoformat(), plan.research_end.astimezone(UTC).isoformat(), trigger_set.set_id, trigger_set.version, trigger_set.rule_versions, trigger_set.strategy_version, "CTX-REGIME@0.1.0", trigger_set.risk_profile_version, BACKTEST_SIMULATOR_VERSION, BACKTEST_COST_MODEL_VERSION, ACCOUNTING_VERSION, BACKTEST_DATA_SOURCE_VERSION, cache_hash(candles), candles[0].open_time.astimezone(UTC).isoformat(), plan.research_start.astimezone(UTC).isoformat(), plan.research_end.astimezone(UTC).isoformat(), config.futures_runtime.spread_cost, config.futures_runtime.slippage_cost, config.futures_runtime.maker_fee_rate, config.futures_runtime.taker_fee_rate, assumptions)


def _validate_warmup(plan: BacktestPlan, candles: tuple[HistoricalCandle, ...]) -> None:
    warmup = [candle for candle in candles if candle.close_time < plan.research_start]
    if len(warmup) < plan.warmup_candles:
        raise BacktestEngineError("insufficient historical warmup before evaluation_start")
    if plan.research_start >= plan.research_end:
        raise BacktestEngineError("invalid backtest evaluation period")


def _assumptions_snapshot(*, config: AppConfig, plan: BacktestPlan, trigger_set: TriggerSetVersion, instrument: FuturesInstrumentMetadata) -> dict[str, str]:
    return {
        "plan_symbol": plan.symbol,
        "plan_category": plan.category,
        "plan_timeframe": plan.timeframe,
        "plan_research_start": plan.research_start.astimezone(UTC).isoformat(),
        "plan_research_end": plan.research_end.astimezone(UTC).isoformat(),
        "plan_validation_start": "" if plan.validation_start is None else plan.validation_start.astimezone(UTC).isoformat(),
        "plan_validation_end": "" if plan.validation_end is None else plan.validation_end.astimezone(UTC).isoformat(),
        "warmup_candles": str(plan.warmup_candles),
        "trigger_set_config_snapshot": json.dumps(dict(trigger_set.config_snapshot), sort_keys=True),
        "trigger_rule_id": config.trigger_rule.rule_id,
        "trigger_rule_version": "0.2.0",
        "trigger_threshold_pct": str(config.trigger_rule.threshold_pct),
        "trigger_lookback_window": config.trigger_rule.lookback_window,
        "risk_stale_after_seconds": str(config.risk_rules.stale_after_seconds),
        "runtime_version": config.futures_runtime.version,
        "runtime_symbol": config.futures_runtime.symbol,
        "runtime_category": config.futures_runtime.category,
        "runtime_candle_interval": config.futures_runtime.candle_interval,
        "configured_leverage": str(config.futures_runtime.leverage),
        "margin_mode": config.futures_runtime.margin_mode,
        "position_mode": config.futures_runtime.position_mode,
        "minimum_net_edge": str(config.futures_runtime.minimum_net_edge),
        "max_position_notional": str(config.futures_runtime.max_position_notional),
        "demo_expected_gross_move": "" if config.futures_runtime.demo_expected_gross_move is None else str(config.futures_runtime.demo_expected_gross_move),
        "maker_fee_rate": str(config.futures_runtime.maker_fee_rate),
        "taker_fee_rate": str(config.futures_runtime.taker_fee_rate),
        "spread_bps": str(config.futures_runtime.spread_cost),
        "slippage_bps": str(config.futures_runtime.slippage_cost),
        "funding_cost": str(config.futures_runtime.funding_cost),
        "instrument_symbol": instrument.symbol,
        "instrument_category": instrument.category.value,
        "instrument_contract_type": instrument.contract_type,
        "instrument_settlement_asset": instrument.settlement_asset,
        "instrument_quantity_step": str(instrument.quantity_step),
        "instrument_price_tick": str(instrument.price_tick),
        "instrument_minimum_order_quantity": str(instrument.minimum_order_quantity),
        "instrument_minimum_notional": str(instrument.minimum_notional),
        "instrument_min_leverage": str(instrument.min_leverage),
        "instrument_max_leverage": str(instrument.max_leverage),
        "instrument_leverage_step": str(instrument.leverage_step),
        "instrument_contract_size": "" if instrument.contract_size is None else str(instrument.contract_size),
    }


def _completed_from_history(current: HistoricalCandle, previous: HistoricalCandle) -> CompletedCandle:
    return CompletedCandle(current.symbol, current.timeframe, candle_id(current.symbol, current.timeframe, current.open_time), current.open_time, current.close_time, historical_to_bybit(current), historical_to_bybit(previous))


def _execution_config(config: AppConfig) -> FuturesExecutionConfig:
    return FuturesExecutionConfig(trading_mode=config.trading_mode, live_trading_enabled=config.live_trading_enabled, bybit_environment=config.bybit.environment, bybit_base_url=config.bybit.base_url, category=ContractCategory.LINEAR, symbol=config.futures_runtime.symbol, default_leverage=config.futures_runtime.leverage, max_configured_leverage=config.futures_runtime.leverage)


def _backtest_account(instrument: FuturesInstrumentMetadata, leverage: Decimal, max_position_notional: Decimal) -> FuturesAccountState:
    return FuturesAccountState(instrument.symbol, instrument.category, instrument.settlement_asset, max_position_notional * Decimal("10"), max_position_notional * Decimal("10"), max_position_notional * Decimal("10"), leverage, "ISOLATED", "ONE_WAY", Decimal("0"))


def _trade_facts(store: FuturesAccountingStore, trade_ids: list[str]) -> tuple[TradePerformanceFact, ...]:
    if not trade_ids:
        return ()
    placeholders = ", ".join("?" for _ in trade_ids)
    with sqlite3.connect(store.path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT trade_id, trigger_set_id, trigger_set_version, symbol, direction,
                   closed_at, net_pnl, gross_pnl, entry_fee, exit_fee, other_fees,
                   funding, duration_seconds, regime_label, evidence_source
            FROM futures_closed_trades
            WHERE trade_id IN ({placeholders})
            ORDER BY closed_at, trade_id
            """,
            tuple(trade_ids),
        ).fetchall()
    facts = []
    for row in rows:
        facts.append(TradePerformanceFact(row["trade_id"], row["trigger_set_id"], row["trigger_set_version"], row["symbol"], row["direction"], row["closed_at"], Decimal(row["net_pnl"]), Decimal(row["gross_pnl"]), Decimal(row["entry_fee"]), Decimal(row["exit_fee"]), Decimal(row["other_fees"]), Decimal(row["funding"]), int(row["duration_seconds"]), row["regime_label"], row["evidence_source"]))
    return tuple(facts)


def _result_from_payload(payload: str) -> BacktestResult:
    import json

    data = json.loads(payload)
    return BacktestResult(
        backtest_run_id=data["backtest_run_id"],
        status=BacktestStatus(data["status"]),
        candles_processed=int(data["candles_processed"]),
        signals=int(data["signals"]),
        intents=int(data["intents"]),
        trades=int(data["trades"]),
        closed_trades=int(data["closed_trades"]),
        rejected_intents=int(data["rejected_intents"]),
        no_action_count=int(data["no_action_count"]),
        technical_failures=int(data["technical_failures"]),
        net_pnl=Decimal(data["net_pnl"]),
        expectancy=None if data["expectancy"] is None else Decimal(data["expectancy"]),
        profit_factor=None if data["profit_factor"] is None else Decimal(data["profit_factor"]),
        max_drawdown=None if data["max_drawdown"] is None else Decimal(data["max_drawdown"]),
        fees=Decimal(data["fees"]),
        funding=Decimal(data["funding"]),
        long_trades=int(data["long_trades"]),
        short_trades=int(data["short_trades"]),
        by_regime=dict(data["by_regime"]),
    )
