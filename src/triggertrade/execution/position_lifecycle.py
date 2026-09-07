"""Deterministic futures position lifecycle and protective exits."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256

from triggertrade.accounting import calculate_unrealized_pnl, close_futures_trade
from triggertrade.execution.contracts import OrderStatus, OrderType
from triggertrade.execution.futures import (
    CostEstimate,
    FUTURES_RISK_RULE_IDS,
    FundingEstimate,
    FuturesExecutionConfig,
    FuturesExecutionService,
    FuturesRiskDecision,
    FuturesTradeIntent,
    PositionAction,
    PositionState,
    futures_risk_decision_id,
    next_position_state,
)
from triggertrade.execution.service import ExecutionError
from triggertrade.market_data import ContractCategory, FuturesAccountState, FuturesInstrumentMetadata
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.persistence.futures_execution_store import FuturesExecutionRecord, FuturesExecutionStore
from triggertrade.persistence.futures_position_store import (
    FuturesClosedPositionRecord,
    FuturesPositionEvent,
    FuturesPositionRecord,
    FuturesPositionStore,
)
from triggertrade.services.futures_accounting_bridge import FuturesAccountingBridge
from triggertrade.rules import TradingRulesUsage
from triggertrade.persistence.trading_rules_store import TradingRulesStore


PROTECTIVE_EXIT_VERSION = "protective-exit-v1"
FUTURES_POSITION_RISK_VERSION = "futures-position-risk-v1"


class ProtectiveExitMode(StrEnum):
    FIXED = "FIXED"
    DYNAMIC = "DYNAMIC"


class CloseReason(StrEnum):
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_LOSS = "STOP_LOSS"
    MANUAL = "MANUAL"
    CLOSE_ALL = "CLOSE_ALL"


class PositionStatus(StrEnum):
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class TakeProfitPlan:
    mode: ProtectiveExitMode
    target_pct: Decimal
    target_price: Decimal
    source_rule_version: str
    calculated_at: str
    calculation_inputs: dict[str, str]


@dataclass(frozen=True)
class StopLossPlan:
    stop_pct: Decimal
    stop_price: Decimal
    source_rule_version: str
    calculated_at: str
    calculation_inputs: dict[str, str]


@dataclass(frozen=True)
class RiskRewardEvaluation:
    reward: Decimal
    risk: Decimal
    ratio: Decimal | None
    minimum_ratio: Decimal
    approved: bool
    reason: str


@dataclass(frozen=True)
class PositionSizingPlan:
    quantity: Decimal
    notional: Decimal
    available_capital: Decimal
    capital_pct: Decimal
    leverage: Decimal
    source_rule_version: str = FUTURES_POSITION_RISK_VERSION


@dataclass(frozen=True)
class PositionRiskConfig:
    take_profit_pct: Decimal = Decimal("0.01")
    stop_loss_pct: Decimal = Decimal("0.0025")
    minimum_risk_reward: Decimal = Decimal("1.5")
    position_size_pct_of_available_capital: Decimal = Decimal("0.10")
    max_position_notional: Decimal = Decimal("10")
    max_total_position_notional: Decimal = Decimal("30")
    max_open_positions: int | None = 3
    denominator_source: str = "available_margin"
    rules_version_id: str | None = None


@dataclass(frozen=True)
class PositionOpenResult:
    position: FuturesPositionRecord | None
    execution: FuturesExecutionRecord | None
    risk_decision: FuturesRiskDecision | None
    reason: str


@dataclass(frozen=True)
class PositionCloseResult:
    position: FuturesPositionRecord
    execution: FuturesExecutionRecord | None
    closed_trade: FuturesClosedPositionRecord | None
    reason: str


@dataclass(frozen=True)
class CloseAllResult:
    close_all_id: str
    results: tuple[PositionCloseResult, ...]
    failures: tuple[str, ...]


def build_fixed_protective_exit_plan(
    *,
    action: PositionAction,
    entry_price: Decimal,
    take_profit_pct: Decimal,
    stop_loss_pct: Decimal,
    price_tick: Decimal,
    calculated_at: str | None = None,
) -> tuple[TakeProfitPlan, StopLossPlan]:
    if action not in {PositionAction.OPEN_LONG, PositionAction.OPEN_SHORT}:
        raise ExecutionError("protective exits are defined only for opening intents")
    if entry_price <= 0 or take_profit_pct <= 0 or stop_loss_pct <= 0:
        raise ExecutionError("protective exit percentages and entry price must be positive")
    now = calculated_at or datetime.now(UTC).isoformat()
    if action is PositionAction.OPEN_LONG:
        tp = _floor_to_step(entry_price * (Decimal("1") + take_profit_pct), price_tick)
        sl = _ceil_to_step(entry_price * (Decimal("1") - stop_loss_pct), price_tick)
    else:
        tp = _ceil_to_step(entry_price * (Decimal("1") - take_profit_pct), price_tick)
        sl = _floor_to_step(entry_price * (Decimal("1") + stop_loss_pct), price_tick)
    inputs = {
        "entry_price": str(entry_price),
        "take_profit_pct": str(take_profit_pct),
        "stop_loss_pct": str(stop_loss_pct),
        "price_tick": str(price_tick),
    }
    take_profit = TakeProfitPlan(ProtectiveExitMode.FIXED, take_profit_pct, tp, PROTECTIVE_EXIT_VERSION, now, inputs)
    stop_loss = StopLossPlan(stop_loss_pct, sl, PROTECTIVE_EXIT_VERSION, now, inputs)
    validate_protective_exit_plan(action=action, entry_price=entry_price, take_profit=take_profit, stop_loss=stop_loss)
    return take_profit, stop_loss


def validate_protective_exit_plan(
    *,
    action: PositionAction,
    entry_price: Decimal,
    take_profit: TakeProfitPlan | None,
    stop_loss: StopLossPlan | None,
) -> None:
    if take_profit is None or stop_loss is None:
        raise ExecutionError("opening futures positions require take-profit and stop-loss plans")
    if take_profit.mode is not ProtectiveExitMode.FIXED:
        raise ExecutionError("dynamic take-profit mode is not approved for runtime execution")
    if take_profit.source_rule_version != PROTECTIVE_EXIT_VERSION or stop_loss.source_rule_version != PROTECTIVE_EXIT_VERSION:
        raise ExecutionError("protective exit plans must pin protective-exit-v1")
    if action is PositionAction.OPEN_LONG:
        valid = take_profit.target_price > entry_price and stop_loss.stop_price < entry_price
    elif action is PositionAction.OPEN_SHORT:
        valid = take_profit.target_price < entry_price and stop_loss.stop_price > entry_price
    else:
        valid = False
    if not valid:
        raise ExecutionError("protective exit side/price relationship is invalid")


def evaluate_risk_reward(
    *,
    action: PositionAction,
    entry_price: Decimal,
    take_profit: TakeProfitPlan,
    stop_loss: StopLossPlan,
    minimum_ratio: Decimal,
) -> RiskRewardEvaluation:
    if action is PositionAction.OPEN_LONG:
        reward = take_profit.target_price - entry_price
        risk = entry_price - stop_loss.stop_price
    elif action is PositionAction.OPEN_SHORT:
        reward = entry_price - take_profit.target_price
        risk = stop_loss.stop_price - entry_price
    else:
        return RiskRewardEvaluation(Decimal("0"), Decimal("0"), None, minimum_ratio, False, "R/R applies only to opening actions")
    if risk <= 0 or reward <= 0:
        return RiskRewardEvaluation(reward, risk, None, minimum_ratio, False, "invalid reward/risk geometry")
    ratio = reward / risk
    return RiskRewardEvaluation(
        reward=reward,
        risk=risk,
        ratio=ratio,
        minimum_ratio=minimum_ratio,
        approved=ratio >= minimum_ratio,
        reason="risk/reward meets gate" if ratio >= minimum_ratio else "risk/reward below minimum",
    )


def should_trigger_protective_exit(
    *,
    position: FuturesPositionRecord,
    mark_price: Decimal,
) -> CloseReason | None:
    if position.status != PositionStatus.OPEN.value:
        return None
    if position.side == PositionState.LONG.value:
        if mark_price >= Decimal(position.tp_price):
            return CloseReason.TAKE_PROFIT
        if mark_price <= Decimal(position.sl_price):
            return CloseReason.STOP_LOSS
    if position.side == PositionState.SHORT.value:
        if mark_price <= Decimal(position.tp_price):
            return CloseReason.TAKE_PROFIT
        if mark_price >= Decimal(position.sl_price):
            return CloseReason.STOP_LOSS
    return None


def calculate_position_size(
    *,
    account: FuturesAccountState,
    instrument: FuturesInstrumentMetadata,
    entry_price: Decimal,
    leverage: Decimal,
    config: PositionRiskConfig,
) -> PositionSizingPlan:
    if entry_price <= 0 or leverage <= 0:
        raise ExecutionError("position sizing requires positive entry price and leverage")
    if not (Decimal("0") < config.position_size_pct_of_available_capital <= Decimal("1")):
        raise ExecutionError("position size percent must be > 0 and <= 1")
    capital = account.available_margin * config.position_size_pct_of_available_capital
    notional_cap = min(capital * leverage, config.max_position_notional, config.max_total_position_notional)
    quantity = _floor_to_step(notional_cap / entry_price, instrument.quantity_step)
    notional = quantity * entry_price
    if quantity <= 0 or quantity < instrument.minimum_order_quantity or notional < instrument.minimum_notional:
        raise ExecutionError("position sizing produced an invalid exchange quantity")
    if instrument.maximum_order_quantity is not None and quantity > instrument.maximum_order_quantity:
        raise ExecutionError("position sizing exceeds exchange maximum limit order quantity")
    return PositionSizingPlan(quantity, notional, account.available_margin, config.position_size_pct_of_available_capital, leverage)


class FuturesPositionLifecycleService:
    """Backend-only authority for futures position lifecycle state."""

    def __init__(
        self,
        *,
        execution_config: FuturesExecutionConfig,
        risk_config: PositionRiskConfig,
        execution_store: FuturesExecutionStore,
        position_store: FuturesPositionStore,
        accounting_store: FuturesAccountingStore,
        adapter,
        instrument: FuturesInstrumentMetadata,
        account: FuturesAccountState,
        operator_trading_state,
        execution_lane: str = "ACTIVE",
        trading_rules_store: TradingRulesStore | None = None,
    ) -> None:
        self._execution_config = execution_config
        self._risk_config = risk_config
        self._execution_store = execution_store
        self._position_store = position_store
        self._accounting_store = accounting_store
        self._adapter = adapter
        self._instrument = instrument
        self._account = account
        self._operator_trading_state = operator_trading_state
        self._execution_lane = execution_lane
        self._trading_rules_store = trading_rules_store

    def open_position(
        self,
        *,
        intent: FuturesTradeIntent,
        risk_decision: FuturesRiskDecision,
        take_profit: TakeProfitPlan,
        stop_loss: StopLossPlan,
        cost: CostEstimate | None = None,
        funding: FundingEstimate | None = None,
    ) -> PositionOpenResult:
        if intent.action not in {PositionAction.OPEN_LONG, PositionAction.OPEN_SHORT}:
            raise ExecutionError("open_position requires OPEN_LONG or OPEN_SHORT intent")
        if not intent.rules_version_id:
            raise ExecutionError("new futures positions require an immutable rules_version_id")
        validate_protective_exit_plan(action=intent.action, entry_price=intent.price, take_profit=take_profit, stop_loss=stop_loss)
        rr = evaluate_risk_reward(action=intent.action, entry_price=intent.price, take_profit=take_profit, stop_loss=stop_loss, minimum_ratio=self._risk_config.minimum_risk_reward)
        if not rr.approved:
            raise ExecutionError(rr.reason)
        if self._position_store.open_position_for_symbol(intent.symbol) is not None:
            raise ExecutionError("only one net futures position per symbol is allowed")
        if self._risk_config.max_open_positions is not None and self._position_store.open_position_count() >= self._risk_config.max_open_positions:
            raise ExecutionError("maximum open futures positions reached")
        if self._position_store.total_open_notional() + (intent.quantity * intent.price) > self._risk_config.max_total_position_notional:
            raise ExecutionError("maximum total futures position notional exceeded")
        if self._position_store.has_unresolved_for_symbol(intent.symbol):
            raise ExecutionError("unresolved futures position/execution state blocks new entries")

        service = self._execution_service(symbol=intent.symbol)
        record = service.submit_approved_limit_order(intent=intent, risk_decision=risk_decision)
        record = service.reconcile(record)
        position_id = futures_position_id(intent.intent_id)
        trade_id = f"trade-{position_id}"
        FuturesAccountingBridge(accounting_store=self._accounting_store, adapter=self._adapter).ingest_execution(record=record, intent=intent, trade_id=trade_id)
        now = datetime.now(UTC).isoformat()
        side = PositionState.LONG if intent.action is PositionAction.OPEN_LONG else PositionState.SHORT
        filled_quantity, entry_vwap = _entry_fill_totals(self._accounting_store, trade_id)
        position_status = _position_status_from_open_record(record, filled_quantity)
        position_quantity = filled_quantity if filled_quantity > 0 else intent.quantity
        position_entry_price = entry_vwap if entry_vwap is not None else intent.price
        position = FuturesPositionRecord(
            position_id=position_id,
            trade_id=trade_id,
            symbol=intent.symbol,
            side=side.value,
            status=position_status.value,
            opened_at=now,
            closed_at=now if position_status is PositionStatus.CLOSED else None,
            entry_price=str(position_entry_price),
            current_qty=str(position_quantity if position_status is not PositionStatus.CLOSED else Decimal("0")),
            initial_qty=str(intent.quantity),
            leverage=str(intent.configured_leverage),
            position_value=str(position_quantity * position_entry_price),
            tp_price=str(take_profit.target_price),
            tp_pct=str(take_profit.target_pct),
            sl_price=str(stop_loss.stop_price),
            sl_pct=str(stop_loss.stop_pct),
            trigger_set_id=intent.trigger_set_id,
            trigger_set_version=intent.trigger_set_version,
            strategy_rule_id=intent.strategy_rule_id,
            strategy_rule_version=intent.strategy_rule_version,
            risk_rule_version=FUTURES_POSITION_RISK_VERSION,
            protective_exit_version=PROTECTIVE_EXIT_VERSION,
            evidence_source=intent.lane or "ACTIVE",
            open_intent_id=intent.intent_id,
            open_risk_decision_id=risk_decision.risk_decision_id,
            open_execution_id=record.client_order_id,
            close_intent_id=None,
            close_risk_decision_id=None,
            close_execution_id=None,
            close_reason=None,
            rule_snapshot={
                **(intent.rule_evaluation_snapshot or {}),
                "rules_version_id": intent.rules_version_id,
                "position_size_pct_of_available_capital": str(self._risk_config.position_size_pct_of_available_capital),
                "max_position_notional": str(self._risk_config.max_position_notional),
                "max_total_position_notional": str(self._risk_config.max_total_position_notional),
                "max_open_positions": None if self._risk_config.max_open_positions is None else str(self._risk_config.max_open_positions),
                "capital_denominator_source": self._risk_config.denominator_source,
                "take_profit_pct": str(self._risk_config.take_profit_pct),
                "stop_loss_pct": str(self._risk_config.stop_loss_pct),
                "minimum_risk_reward": str(self._risk_config.minimum_risk_reward),
                "minimum_net_edge": None if risk_decision.net_edge is None else str(risk_decision.net_edge.minimum_net_edge),
                "configured_leverage": str(intent.configured_leverage),
                "protective_exit_version": PROTECTIVE_EXIT_VERSION,
                "risk_version": FUTURES_POSITION_RISK_VERSION,
            },
            updated_at=now,
            rules_version_id=intent.rules_version_id,
            instrument_snapshot=_instrument_metadata_snapshot(self._instrument),
        )
        self._position_store.save_open_position(position)
        self._position_store.record_event(FuturesPositionEvent(_event_id(position_id, "OPEN", record.client_order_id), position_id, "OPEN", now, "open_position", record.client_order_id, None))
        self._record_rules_usage(intent.rules_version_id, "LIVE_POSITION", position_id, intent.trigger_set_version, now)
        if position_status is PositionStatus.CLOSED:
            self._position_store.record_event(
                FuturesPositionEvent(
                    _event_id(position_id, "OPEN_TERMINAL_NO_FILL", record.client_order_id),
                    position_id,
                    "OPEN_TERMINAL_NO_FILL",
                    now,
                    record.status.value,
                    record.client_order_id,
                    None,
                )
            )
        return PositionOpenResult(position, record, risk_decision, "opened_or_submitted")

    def monitor_protective_exit(self, *, position_id: str, mark_price: Decimal) -> PositionCloseResult | None:
        position = self._position_store.get_position(position_id)
        if position is None:
            raise ExecutionError("position not found")
        reason = should_trigger_protective_exit(position=position, mark_price=mark_price)
        if reason is None:
            return None
        return self.close_position(position_id=position_id, close_reason=reason, price=mark_price)

    def close_position(self, *, position_id: str, close_reason: CloseReason = CloseReason.MANUAL, price: Decimal | None = None) -> PositionCloseResult:
        position = self._position_store.get_position(position_id)
        if position is None:
            raise ExecutionError("position not found")
        if position.status == PositionStatus.CLOSED.value:
            return PositionCloseResult(position, None, self._position_store.get_closed_position(position_id), "already_closed")
        if position.status not in {PositionStatus.OPEN.value, PositionStatus.CLOSING.value, PositionStatus.UNKNOWN.value}:
            raise ExecutionError("only open futures positions can be closed")
        action = PositionAction.CLOSE_LONG if position.side == PositionState.LONG.value else PositionAction.CLOSE_SHORT
        position_instrument = instrument_metadata_from_position_snapshot(position) or self._instrument
        close_price = _normalize_reduce_only_close_price(
            price or self._account.mark_price or Decimal(position.entry_price),
            action=action,
            price_tick=position_instrument.price_tick,
        )
        intent = FuturesTradeIntent(
            intent_id=futures_close_intent_id(position_id, close_reason),
            symbol=position.symbol,
            category=ContractCategory.LINEAR,
            action=action,
            order_type=OrderType.LIMIT,
            quantity=Decimal(position.current_qty),
            price=close_price,
            current_position_state=PositionState(position.side),
            configured_leverage=Decimal(position.leverage),
            strategy_rule_id="manual-close-service",
            strategy_rule_version="0.1.0",
            expected_gross_price_move=Decimal("1"),
            lane=self._execution_lane,
            trigger_set_id=position.trigger_set_id,
            trigger_set_version=position.trigger_set_version,
            rules_version_id=position.rules_version_id,
        )
        risk = FuturesRiskDecision(
            risk_decision_id=futures_risk_decision_id(intent.intent_id, ()),
            intent_id=intent.intent_id,
            approved=True,
            checked_rule_ids=FUTURES_RISK_RULE_IDS,
            approved_quantity=intent.quantity,
            approved_notional=intent.quantity * intent.price,
            configured_leverage=intent.configured_leverage,
            position_state_before=PositionState(position.side),
            position_state_after=PositionState.FLAT,
            net_edge=_approved_close_edge(),
            lane=self._execution_lane,
        )
        closing = self._position_store.mark_closing(position_id, intent.intent_id, risk.risk_decision_id, close_reason.value)
        service = self._execution_service(symbol=position.symbol, instrument=position_instrument)
        record = service.submit_approved_limit_order(intent=intent, risk_decision=risk)
        record = service.reconcile(record)
        self._position_store.attach_close_execution(position_id, record.client_order_id)
        FuturesAccountingBridge(accounting_store=self._accounting_store, adapter=self._adapter).ingest_execution(record=record, intent=intent, trade_id=position.trade_id)
        if record.status is OrderStatus.FILLED:
            closed = self._finalize_closed_position(closing, record, close_reason)
            return PositionCloseResult(self._position_store.get_position(position_id) or closing, record, closed, "closed")
        return PositionCloseResult(closing, record, None, "close_submitted")

    def close_all_positions(self) -> CloseAllResult:
        close_all_id = f"closeall-{sha256(datetime.now(UTC).isoformat().encode('utf-8')).hexdigest()[:16]}"
        self._position_store.begin_close_all(close_all_id)
        results: list[PositionCloseResult] = []
        failures: list[str] = []
        for position in self._position_store.list_open_positions():
            try:
                results.append(self.close_position(position_id=position.position_id, close_reason=CloseReason.CLOSE_ALL))
            except Exception as exc:
                failures.append(f"{position.position_id}:{exc.__class__.__name__}")
        self._position_store.complete_close_all(close_all_id, "completed_with_failures" if failures else "completed")
        return CloseAllResult(close_all_id, tuple(results), tuple(failures))

    def recover_after_restart(self) -> tuple[FuturesPositionRecord, ...]:
        for position in self._position_store.list_open_positions(include_unknown=True):
            self.reconcile_position(position.position_id)
        return self._position_store.list_open_positions(include_unknown=True)

    def reconcile_position(self, position_id: str) -> FuturesPositionRecord | None:
        position = self._position_store.get_position(position_id)
        if position is None or position.status == PositionStatus.CLOSED.value:
            return position
        position_instrument = instrument_metadata_from_position_snapshot(position) or self._instrument
        service = self._execution_service(symbol=position.symbol, instrument=position_instrument)
        bridge = FuturesAccountingBridge(accounting_store=self._accounting_store, adapter=self._adapter)
        if position.close_intent_id:
            close_record = self._execution_store.get_by_intent(position.close_intent_id)
            if close_record is not None:
                close_record = service.reconcile(close_record)
                bridge.ingest_execution(record=close_record, trade_id=position.trade_id)
                if close_record.status is OrderStatus.FILLED:
                    self._finalize_closed_position(position, close_record, CloseReason(position.close_reason or CloseReason.MANUAL.value))
                    return self._position_store.get_position(position_id)
            return self._position_store.get_position(position_id)
        open_record = self._execution_store.get_by_intent(position.open_intent_id) or self._execution_store.get_by_client_order_id(position.open_execution_id)
        if open_record is not None:
            open_record = service.reconcile(open_record)
            bridge.ingest_execution(record=open_record, trade_id=position.trade_id)
            filled_quantity, entry_vwap = _entry_fill_totals(self._accounting_store, position.trade_id)
            if filled_quantity > 0 and entry_vwap is not None:
                self._position_store.update_open_fill(
                    position_id,
                    current_qty=str(filled_quantity),
                    entry_price=str(entry_vwap),
                    position_value=str(filled_quantity * entry_vwap),
                    status=PositionStatus.OPEN.value,
                    updated_at=datetime.now(UTC).isoformat(),
                )
            elif open_record.status in {OrderStatus.CANCELLED, OrderStatus.REJECTED}:
                self._position_store.mark_closed(position_id, datetime.now(UTC).isoformat())
        return self._position_store.get_position(position_id)

    def _finalize_closed_position(self, position: FuturesPositionRecord, record: FuturesExecutionRecord, close_reason: CloseReason) -> FuturesClosedPositionRecord:
        fills = self._accounting_store.list_fills(position.trade_id)
        entry = tuple(fill for fill in fills if fill.action in {PositionAction.OPEN_LONG.value, PositionAction.OPEN_SHORT.value})
        exits = tuple(fill for fill in fills if fill.action in {PositionAction.CLOSE_LONG.value, PositionAction.CLOSE_SHORT.value})
        closed = close_futures_trade(trade_id=position.trade_id, entry_fills=entry, exit_fills=exits, leverage=Decimal(position.leverage))
        self._accounting_store.record_closed_trade(closed)
        realized_pct = Decimal("0") if Decimal(position.position_value) == 0 else closed.net_pnl / Decimal(position.position_value) * Decimal("100")
        now = datetime.now(UTC).isoformat()
        result = FuturesClosedPositionRecord(
            trade_id=position.trade_id,
            position_id=position.position_id,
            symbol=position.symbol,
            direction=position.side,
            entry_vwap=str(closed.entry_vwap),
            exit_vwap=str(closed.exit_vwap),
            qty=str(closed.quantity),
            position_value=position.position_value,
            leverage=position.leverage,
            planned_tp_pct=position.tp_pct,
            planned_tp_price=position.tp_price,
            planned_sl_pct=position.sl_pct,
            planned_sl_price=position.sl_price,
            realized_pnl_pct=str(realized_pct),
            gross_pnl=str(closed.gross_pnl),
            fees=str(closed.entry_fee + closed.exit_fee + closed.other_fees),
            funding=str(closed.funding),
            net_pnl=str(closed.net_pnl),
            opened_at=closed.opened_at,
            closed_at=closed.closed_at,
            duration_seconds=closed.duration_seconds,
            close_reason=close_reason.value,
            trigger_set_id=position.trigger_set_id,
            trigger_set_version=position.trigger_set_version,
            strategy_rule_id=position.strategy_rule_id,
            strategy_rule_version=position.strategy_rule_version,
            risk_rule_version=position.risk_rule_version,
            evidence_source=position.evidence_source,
            accounting_version=closed.accounting_version,
            rules_version_id=position.rules_version_id,
        )
        self._position_store.save_closed_position(result)
        self._record_rules_usage(position.rules_version_id, "LIVE_TRADE", position.trade_id, position.trigger_set_version, now)
        self._position_store.mark_closed(position.position_id, now)
        self._position_store.record_event(FuturesPositionEvent(_event_id(position.position_id, "CLOSE", record.client_order_id), position.position_id, "CLOSE", now, close_reason.value, record.client_order_id, None))
        return result

    def _record_rules_usage(self, rules_version_id: str | None, usage_type: str, entity_id: str, entity_version: str | None, created_at: str) -> None:
        if rules_version_id and self._trading_rules_store is not None:
            self._trading_rules_store.record_usage(
                TradingRulesUsage(
                    rules_version_id=rules_version_id,
                    usage_type=usage_type,
                    entity_id=entity_id,
                    entity_version=entity_version,
                    context=self._execution_lane,
                    created_at=created_at,
                )
            )

    def _execution_service(self, *, symbol: str | None = None, instrument: FuturesInstrumentMetadata | None = None) -> FuturesExecutionService:
        resolved_instrument = instrument or self._instrument
        return FuturesExecutionService(
            config=replace(self._execution_config, symbol=symbol or self._execution_config.symbol),
            adapter=self._adapter,
            store=self._execution_store,
            instrument=resolved_instrument,
            account=self._account,
            execution_lane=self._execution_lane,
            operator_trading_state=self._operator_trading_state,
        )



def _instrument_metadata_snapshot(instrument: FuturesInstrumentMetadata) -> dict[str, str | None]:
    return {
        "symbol": instrument.symbol,
        "category": instrument.category.value,
        "contract_type": instrument.contract_type,
        "settle_coin": instrument.settlement_asset,
        "quote_coin": instrument.settlement_asset,
        "tick_size": str(instrument.price_tick),
        "qty_step": str(instrument.quantity_step),
        "min_order_qty": str(instrument.minimum_order_quantity),
        "max_order_qty": None if instrument.maximum_order_quantity is None else str(instrument.maximum_order_quantity),
        "min_notional_value": str(instrument.minimum_notional),
        "max_market_order_qty": None if instrument.max_market_order_quantity is None else str(instrument.max_market_order_quantity),
        "min_leverage": str(instrument.min_leverage),
        "max_leverage": str(instrument.max_leverage),
        "leverage_step": str(instrument.leverage_step),
        "catalog_hash": instrument.catalog_hash,
        "source": instrument.catalog_source,
        "status": "Trading",
    }


def instrument_metadata_from_position_snapshot(position: FuturesPositionRecord) -> FuturesInstrumentMetadata | None:
    snapshot = position.instrument_snapshot or {}
    required = {"symbol", "category", "contract_type", "settle_coin", "tick_size", "qty_step", "min_order_qty", "min_notional_value", "max_leverage"}
    if not required.issubset(snapshot):
        return None
    max_order = snapshot.get("max_order_qty")
    max_market = snapshot.get("max_market_order_qty")
    return FuturesInstrumentMetadata(
        symbol=str(snapshot["symbol"]),
        category=ContractCategory(str(snapshot.get("category") or ContractCategory.LINEAR.value)),
        contract_type=str(snapshot["contract_type"]),
        settlement_asset=str(snapshot["settle_coin"]),
        quantity_step=Decimal(str(snapshot["qty_step"])),
        price_tick=Decimal(str(snapshot["tick_size"])),
        minimum_order_quantity=Decimal(str(snapshot["min_order_qty"])),
        minimum_notional=Decimal(str(snapshot["min_notional_value"])),
        max_leverage=Decimal(str(snapshot["max_leverage"])),
        min_leverage=Decimal(str(snapshot.get("min_leverage") or "1")),
        leverage_step=Decimal(str(snapshot.get("leverage_step") or "0.01")),
        maximum_order_quantity=None if max_order in {None, ""} else Decimal(str(max_order)),
        max_market_order_quantity=None if max_market in {None, ""} else Decimal(str(max_market)),
        catalog_hash=snapshot.get("catalog_hash"),
        catalog_source=snapshot.get("source"),
    )


def _instrument_from_position_snapshot(position: FuturesPositionRecord) -> FuturesInstrumentMetadata | None:
    return instrument_metadata_from_position_snapshot(position)

def _normalize_reduce_only_close_price(price: Decimal, *, action: PositionAction, price_tick: Decimal) -> Decimal:
    if action is PositionAction.CLOSE_LONG:
        return _floor_to_step(price, price_tick)
    if action is PositionAction.CLOSE_SHORT:
        return _ceil_to_step(price, price_tick)
    raise ExecutionError("reduce-only close price normalization requires a close action")


def futures_position_id(intent_id: str) -> str:
    return f"fpos-{sha256(intent_id.encode('utf-8')).hexdigest()[:24]}"


def futures_close_intent_id(position_id: str, reason: CloseReason) -> str:
    return f"fclose-{sha256(f'{position_id}|{reason.value}'.encode('utf-8')).hexdigest()[:24]}"


def unrealized_pnl_pct(*, position: FuturesPositionRecord, mark_price: Decimal) -> Decimal:
    value = Decimal(position.position_value)
    if value <= 0:
        raise ExecutionError("position value must be positive")
    result = calculate_unrealized_pnl(
        symbol=position.symbol,
        direction=PositionState(position.side),
        quantity=Decimal(position.current_qty),
        entry_vwap=Decimal(position.entry_price),
        mark_price=mark_price,
        observed_at=datetime.now(UTC).isoformat(),
    )
    return result.unrealized_pnl / value * Decimal("100")


def _approved_close_edge():
    from triggertrade.execution.futures import CostEstimate, FundingEstimate, NetEdgeEstimate

    cost = CostEstimate(Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"))
    funding = FundingEstimate(Decimal("0"), None, Decimal("0"), Decimal("0"))
    return NetEdgeEstimate(Decimal("0"), Decimal("0"), cost, funding, Decimal("0"), True, "closing existing exposure")


def _event_id(position_id: str, event_type: str, key: str) -> str:
    return f"fpe-{sha256(f'{position_id}|{event_type}|{key}'.encode('utf-8')).hexdigest()[:24]}"


def _position_status_from_open_record(record: FuturesExecutionRecord, filled_quantity: Decimal) -> PositionStatus:
    if filled_quantity > 0:
        return PositionStatus.OPEN
    if record.status in {OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED}:
        return PositionStatus.OPEN
    if record.status in {OrderStatus.CANCELLED, OrderStatus.REJECTED}:
        return PositionStatus.CLOSED
    return PositionStatus.UNKNOWN


def _entry_fill_totals(store: FuturesAccountingStore, trade_id: str) -> tuple[Decimal, Decimal | None]:
    fills = tuple(fill for fill in store.list_fills(trade_id) if fill.action in {PositionAction.OPEN_LONG.value, PositionAction.OPEN_SHORT.value})
    quantity = sum((fill.quantity for fill in fills), Decimal("0"))
    if quantity <= 0:
        return quantity, None
    notional = sum((fill.quantity * fill.price for fill in fills), Decimal("0"))
    return quantity, notional / quantity


def _floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        raise ExecutionError("exchange step must be positive")
    return (value // step) * step


def _ceil_to_step(value: Decimal, step: Decimal) -> Decimal:
    floored = _floor_to_step(value, step)
    return floored if floored == value else floored + step
