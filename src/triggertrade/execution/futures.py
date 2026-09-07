"""Perpetual futures execution contracts and safety checks."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from typing import Any, Callable

from triggertrade.config import BybitEnvironment, TradingMode
from triggertrade.execution.contracts import OrderStatus, OrderType, Side
from triggertrade.execution.service import ExecutionError
from triggertrade.exchanges import BybitApiError
from triggertrade.market_data.futures import ContractCategory, FuturesAccountState, FuturesInstrumentMetadata
from triggertrade.persistence.futures_execution_store import FuturesExecutionRecord, FuturesExecutionStore


class PositionState(StrEnum):
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"


class PositionAction(StrEnum):
    OPEN_LONG = "OPEN_LONG"
    CLOSE_LONG = "CLOSE_LONG"
    OPEN_SHORT = "OPEN_SHORT"
    CLOSE_SHORT = "CLOSE_SHORT"


class MarginMode(StrEnum):
    ISOLATED = "ISOLATED"
    CROSS = "CROSS"


class PositionMode(StrEnum):
    ONE_WAY = "ONE_WAY"
    HEDGE = "HEDGE"


@dataclass(frozen=True)
class CostEstimate:
    maker_fee_rate: Decimal
    taker_fee_rate: Decimal
    entry_fee: Decimal
    exit_fee: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    funding_cost: Decimal
    total_estimated_cost: Decimal
    units: str = "quote_asset"
    model_version: str = "futures-cost-v1"


@dataclass(frozen=True)
class FundingEstimate:
    funding_rate: Decimal | None
    next_funding_time: str | None
    expected_holding_overlap: Decimal
    estimated_funding_impact: Decimal
    capability: str = "available"


@dataclass(frozen=True)
class NetEdgeEstimate:
    expected_gross_price_move: Decimal | None
    minimum_net_edge: Decimal
    cost: CostEstimate
    funding: FundingEstimate
    expected_net_edge: Decimal | None
    approved: bool
    reason: str
    model_version: str = "futures-net-edge-v1"


@dataclass(frozen=True)
class FuturesTradeIntent:
    intent_id: str
    symbol: str
    category: ContractCategory
    action: PositionAction
    order_type: OrderType
    quantity: Decimal
    price: Decimal
    current_position_state: PositionState
    configured_leverage: Decimal = Decimal("1")
    strategy_rule_id: str = "manual-futures"
    strategy_rule_version: str = "0"
    expected_gross_price_move: Decimal | None = None
    created_at: str | None = None
    lane: str | None = None
    trigger_set_id: str | None = None
    trigger_set_version: str | None = None
    regime_context_id: str | None = None
    regime_rule_id: str | None = None
    regime_rule_version: str | None = None
    regime_state: str | None = None
    take_profit: Any | None = None
    stop_loss: Any | None = None
    minimum_risk_reward: Decimal | None = None
    rules_version_id: str | None = None
    rule_evaluation_snapshot: dict[str, str | None] | None = None


@dataclass(frozen=True)
class FuturesRiskDecision:
    risk_decision_id: str
    intent_id: str
    approved: bool
    checked_rule_ids: tuple[str, ...]
    blocking_rule_ids: tuple[str, ...] = ()
    approved_quantity: Decimal | None = None
    approved_notional: Decimal | None = None
    configured_leverage: Decimal = Decimal("1")
    position_state_before: PositionState = PositionState.FLAT
    position_state_after: PositionState | None = None
    net_edge: NetEdgeEstimate | None = None
    unsupported_capability_rule_ids: tuple[str, ...] = ()
    rejection_reason: str | None = None
    created_at: str | None = None
    lane: str | None = None


@dataclass(frozen=True)
class FuturesExecutionConfig:
    trading_mode: TradingMode = TradingMode.PAPER
    live_trading_enabled: bool = False
    bybit_environment: BybitEnvironment = BybitEnvironment.DEMO
    bybit_base_url: str = "https://api-demo.bybit.com"
    category: ContractCategory = ContractCategory.LINEAR
    symbol: str = "BTCUSDT"
    default_leverage: Decimal = Decimal("1")
    max_configured_leverage: Decimal = Decimal("1")
    minimum_liquidation_buffer_pct: Decimal | None = None


FUTURES_RISK_RULE_IDS = (
    "FRSK-001",
    "FRSK-002",
    "FRSK-003",
    "FRSK-004",
    "FRSK-005",
    "FRSK-006",
    "FRSK-007",
    "FRSK-008",
    "FRSK-009",
    "FRSK-010",
    "FRSK-011",
    "FRSK-012",
    "FRSK-013",
)


class FuturesRiskManager:
    """Deterministic futures risk gate without alpha assumptions."""

    def __init__(
        self,
        *,
        config: FuturesExecutionConfig,
        store: FuturesExecutionStore,
        minimum_net_edge: Decimal | None = Decimal("0"),
        max_position_notional: Decimal = Decimal("10"),
        max_simultaneous_exposure: Decimal = Decimal("10"),
        cooldown_open_intent_ids: frozenset[str] = frozenset(),
    ) -> None:
        self._config = config
        self._store = store
        self._minimum_net_edge = minimum_net_edge
        self._max_position_notional = max_position_notional
        self._max_simultaneous_exposure = max_simultaneous_exposure
        self._cooldown_open_intent_ids = cooldown_open_intent_ids

    def evaluate(
        self,
        *,
        intent: FuturesTradeIntent,
        instrument: FuturesInstrumentMetadata,
        account: FuturesAccountState,
        cost: CostEstimate,
        funding: FundingEstimate,
    ) -> FuturesRiskDecision:
        blocking: list[str] = []
        unsupported: list[str] = []
        notional = intent.quantity * intent.price
        after_state = next_position_state(intent.current_position_state, intent.action)

        if after_state is None:
            blocking.append("FRSK-005")
        if not _account_matches_intent(intent, instrument, account):
            blocking.append("FRSK-006")
        if not _position_state_matches_size(intent.current_position_state, account.position_size):
            blocking.append("FRSK-005")
        if not _close_quantity_is_covered(intent, account.position_size):
            blocking.append("FRSK-005")
        if notional > self._max_position_notional or notional > self._max_simultaneous_exposure:
            blocking.append("FRSK-001")
        leverage_valid = (
            intent.configured_leverage > 0
            and intent.configured_leverage >= instrument.min_leverage
            and intent.configured_leverage <= self._config.max_configured_leverage
            and intent.configured_leverage <= instrument.max_leverage
            and instrument.leverage_step > 0
            and intent.configured_leverage % instrument.leverage_step == 0
            and account.configured_leverage == intent.configured_leverage
        )
        if not leverage_valid:
            blocking.append("FRSK-003")
        elif account.available_margin < notional / intent.configured_leverage:
            blocking.append("FRSK-004")
        if account.margin_mode.upper() not in {MarginMode.ISOLATED.value, MarginMode.CROSS.value}:
            blocking.append("FRSK-006")
        if account.position_mode.upper() not in {PositionMode.ONE_WAY.value, PositionMode.HEDGE.value}:
            blocking.append("FRSK-006")
        if self._config.minimum_liquidation_buffer_pct is None or account.liquidation_price is None:
            unsupported.append("FRSK-007")
        if self._operator_pause_capability_missing():
            unsupported.append("FRSK-009")
        unsupported.append("FRSK-011")
        if self._store.get_by_intent(intent.intent_id) is not None or self._store.get_by_client_order_id(
            futures_client_order_id(intent.intent_id)
        ) is not None:
            blocking.append("FRSK-002")
        if intent.intent_id in self._cooldown_open_intent_ids:
            blocking.append("FRSK-008")
        if not _demo_linear_safety_ok(self._config, intent):
            blocking.append("FRSK-006")
        if intent.action in {PositionAction.OPEN_LONG, PositionAction.OPEN_SHORT}:
            try:
                from triggertrade.execution.position_lifecycle import evaluate_risk_reward, validate_protective_exit_plan

                validate_protective_exit_plan(
                    action=intent.action,
                    entry_price=intent.price,
                    take_profit=intent.take_profit,
                    stop_loss=intent.stop_loss,
                )
                rr = evaluate_risk_reward(
                    action=intent.action,
                    entry_price=intent.price,
                    take_profit=intent.take_profit,
                    stop_loss=intent.stop_loss,
                    minimum_ratio=intent.minimum_risk_reward or Decimal("0"),
                )
                if not rr.approved:
                    blocking.append("FRSK-013")
            except Exception:
                blocking.append("FRSK-012")

        if self._minimum_net_edge is None:
            net_edge = NetEdgeEstimate(
                expected_gross_price_move=intent.expected_gross_price_move,
                minimum_net_edge=Decimal("0"),
                cost=cost,
                funding=funding,
                expected_net_edge=None,
                approved=True,
                reason="minimum net edge disabled by current trading rules",
            )
        else:
            net_edge = estimate_net_edge(
                expected_gross_price_move=intent.expected_gross_price_move,
                minimum_net_edge=self._minimum_net_edge,
                cost=cost,
                funding=funding,
            )
            if not net_edge.approved:
                blocking.append("FRSK-010")

        approved = not blocking
        return FuturesRiskDecision(
            risk_decision_id=futures_risk_decision_id(intent.intent_id, tuple(blocking)),
            intent_id=intent.intent_id,
            approved=approved,
            checked_rule_ids=FUTURES_RISK_RULE_IDS,
            blocking_rule_ids=tuple(blocking),
            approved_quantity=intent.quantity if approved else None,
            approved_notional=notional if approved else None,
            configured_leverage=intent.configured_leverage,
            position_state_before=intent.current_position_state,
            position_state_after=after_state if approved else None,
            net_edge=net_edge,
            unsupported_capability_rule_ids=tuple(unsupported),
            rejection_reason=",".join(blocking) if blocking else None,
            created_at=datetime.now(UTC).isoformat(),
            lane=intent.lane,
        )

    def _operator_pause_capability_missing(self) -> bool:
        return True


class FuturesExecutionService:
    def __init__(
        self,
        *,
        config: FuturesExecutionConfig,
        adapter,
        store: FuturesExecutionStore,
        instrument: FuturesInstrumentMetadata,
        account: FuturesAccountState,
        execution_lane: str | None = None,
        operator_trading_state: Callable[[], str] | None = None,
    ) -> None:
        self._config = config
        self._adapter = adapter
        self._store = store
        self._instrument = instrument
        self._account = account
        self._execution_lane = execution_lane
        self._operator_trading_state = operator_trading_state

    def submit_approved_limit_order(
        self,
        *,
        intent: FuturesTradeIntent,
        risk_decision: FuturesRiskDecision,
    ) -> FuturesExecutionRecord:
        self._validate_environment(intent)
        self._validate_risk(intent, risk_decision)
        self._validate_precision(intent)
        self._validate_margin(intent)

        now = _now()
        client_order_id = futures_client_order_id(intent.intent_id)
        existing = self._store.get_by_intent(intent.intent_id) or self._store.get_by_client_order_id(client_order_id)
        if existing is not None:
            return self.reconcile(existing)

        self._validate_operator_trading_state(intent)
        record = FuturesExecutionRecord(
            intent_id=intent.intent_id,
            risk_decision_id=risk_decision.risk_decision_id,
            client_order_id=client_order_id,
            exchange_order_id=None,
            symbol=intent.symbol,
            category=intent.category.value,
            position_action=intent.action.value,
            exchange_side=futures_exchange_side(intent.action).value,
            order_type=intent.order_type.value,
            requested_qty=str(intent.quantity),
            requested_price=str(intent.price),
            leverage=str(intent.configured_leverage),
            status=OrderStatus.CREATED,
            created_at=now,
            updated_at=now,
            margin_mode=self._account.margin_mode,
            position_mode=self._account.position_mode,
            cost_model_version=risk_decision.net_edge.cost.model_version if risk_decision.net_edge else None,
            net_edge_model_version=risk_decision.net_edge.model_version if risk_decision.net_edge else None,
            expected_net_edge=str(risk_decision.net_edge.expected_net_edge) if risk_decision.net_edge else None,
            reconciliation_state="reserved",
            lane=intent.lane,
            trigger_set_id=intent.trigger_set_id,
            trigger_set_version=intent.trigger_set_version,
        )
        record, created = self._store.reserve(record)
        if not created:
            return self.reconcile(record)

        submitting = replace(record, status=OrderStatus.SUBMITTING, updated_at=_now())
        self._store.update(submitting)
        try:
            response = self._adapter.create_limit_order(
                symbol=intent.symbol,
                action=intent.action,
                quantity=intent.quantity,
                price=intent.price,
                client_order_id=client_order_id,
            )
        except BybitApiError as exc:
            unknown = replace(
                submitting,
                status=OrderStatus.UNKNOWN,
                updated_at=_now(),
                reconciliation_state="submit_failed_reconcile_required",
                last_error_code=_error_code(exc),
            )
            self._store.update(unknown)
            return self.reconcile(unknown)
        submitted = replace(
            submitting,
            status=OrderStatus.SUBMITTED,
            exchange_order_id=response.result.get("orderId") or submitting.exchange_order_id,
            updated_at=_now(),
            exchange_status="create_accepted",
            reconciliation_state="submitted",
        )
        return self._store.update(submitted)

    def cancel(self, record: FuturesExecutionRecord) -> FuturesExecutionRecord:
        if record.status in {OrderStatus.CANCELLED, OrderStatus.FILLED, OrderStatus.REJECTED}:
            return record
        pending = replace(record, status=OrderStatus.CANCEL_PENDING, updated_at=_now(), reconciliation_state="cancel_requested")
        self._store.update(pending)
        try:
            self._adapter.cancel_order(symbol=record.symbol, client_order_id=record.client_order_id)
        except BybitApiError as exc:
            unknown = replace(
                pending,
                status=OrderStatus.UNKNOWN,
                updated_at=_now(),
                reconciliation_state="cancel_failed_reconcile_required",
                last_error_code=_error_code(exc),
            )
            self._store.update(unknown)
            return self.reconcile(unknown)
        return self.reconcile(pending)

    def reconcile(self, record: FuturesExecutionRecord) -> FuturesExecutionRecord:
        try:
            order = self._adapter.reconcile_order(symbol=record.symbol, client_order_id=record.client_order_id)
        except BybitApiError as exc:
            return self._store.update(
                replace(record, status=OrderStatus.UNKNOWN, updated_at=_now(), reconciliation_state="reconcile_failed", last_error_code=_error_code(exc))
            )
        if order is None:
            return self._store.update(replace(record, status=OrderStatus.UNKNOWN, updated_at=_now(), reconciliation_state="not_found"))
        updated = replace(
            record,
            status=self._adapter.map_order_status(order.get("orderStatus")),
            exchange_order_id=order.get("orderId") or record.exchange_order_id,
            updated_at=_now(),
            exchange_status=order.get("orderStatus"),
            reconciliation_state="reconciled",
            last_error_code=None,
        )
        return self._store.update(updated)

    def recover_unresolved(self) -> tuple[FuturesExecutionRecord, ...]:
        return tuple(self.reconcile(record) for record in self._store.unresolved())

    def _validate_environment(self, intent: FuturesTradeIntent) -> None:
        if self._config.trading_mode is not TradingMode.PAPER:
            raise ExecutionError("futures demo execution requires paper-mode configuration")
        if self._config.live_trading_enabled:
            raise ExecutionError("live trading must remain disabled for futures demo")
        if self._config.bybit_environment is not BybitEnvironment.DEMO:
            raise ExecutionError("Bybit futures execution requires demo environment")
        if self._config.bybit_base_url != "https://api-demo.bybit.com":
            raise ExecutionError("Bybit futures execution requires demo base URL")
        if intent.category is not ContractCategory.LINEAR or self._config.category is not ContractCategory.LINEAR:
            raise ExecutionError("only Bybit linear USDT perpetual futures are supported")
        if intent.symbol != self._config.symbol:
            raise ExecutionError("futures intent symbol must match configured execution symbol")
        if intent.order_type is not OrderType.LIMIT:
            raise ExecutionError("only futures limit orders are supported")

    def _validate_risk(self, intent: FuturesTradeIntent, risk_decision: FuturesRiskDecision) -> None:
        if risk_decision.intent_id != intent.intent_id:
            raise ExecutionError("futures risk decision is not bound to this intent")
        if not risk_decision.approved:
            raise ExecutionError("futures risk decision rejected this intent")
        if set(risk_decision.checked_rule_ids) != set(FUTURES_RISK_RULE_IDS):
            raise ExecutionError("approved futures risk decision is missing mandatory rule evidence")
        if risk_decision.blocking_rule_ids:
            raise ExecutionError("approved futures risk decision contains blocking rule evidence")
        if risk_decision.approved_quantity != intent.quantity:
            raise ExecutionError("approved futures risk quantity does not match intent")
        if risk_decision.approved_notional != intent.quantity * intent.price:
            raise ExecutionError("approved futures risk notional does not match intent")
        if risk_decision.net_edge is None or not risk_decision.net_edge.approved:
            raise ExecutionError("approved futures risk requires approved net-edge evidence")

    def _validate_precision(self, intent: FuturesTradeIntent) -> None:
        if intent.quantity < self._instrument.minimum_order_quantity:
            raise ExecutionError("futures quantity is below minimum")
        if intent.quantity % self._instrument.quantity_step != 0:
            raise ExecutionError("futures quantity does not align with step size")
        if intent.price % self._instrument.price_tick != 0:
            raise ExecutionError("futures limit price does not align with tick size")
        if intent.quantity * intent.price < self._instrument.minimum_notional:
            raise ExecutionError("futures notional is below exchange minimum")
        if intent.configured_leverage < self._instrument.min_leverage:
            raise ExecutionError("futures leverage is below exchange minimum")
        if intent.configured_leverage > self._instrument.max_leverage:
            raise ExecutionError("futures leverage exceeds exchange maximum")

    def _validate_margin(self, intent: FuturesTradeIntent) -> None:
        required_margin = (intent.quantity * intent.price) / intent.configured_leverage
        if self._account.available_margin < required_margin:
            raise ExecutionError("available margin is below required initial margin")

    def _validate_operator_trading_state(self, intent: FuturesTradeIntent) -> None:
        if self._execution_lane != "ACTIVE":
            return
        if intent.action not in {PositionAction.OPEN_LONG, PositionAction.OPEN_SHORT}:
            return
        if self._operator_trading_state is None:
            raise ExecutionError("ACTIVE futures execution requires persistent operator trading state")
        state = self._operator_trading_state()
        if state == "TRADING_PAUSED":
            raise ExecutionError("new ACTIVE futures execution is blocked by persistent operator pause")
        if state != "TRADING_ENABLED":
            raise ExecutionError("unknown operator trading state; futures execution fails closed")


def next_position_state(current: PositionState, action: PositionAction) -> PositionState | None:
    allowed = {
        (PositionState.FLAT, PositionAction.OPEN_LONG): PositionState.LONG,
        (PositionState.LONG, PositionAction.CLOSE_LONG): PositionState.FLAT,
        (PositionState.FLAT, PositionAction.OPEN_SHORT): PositionState.SHORT,
        (PositionState.SHORT, PositionAction.CLOSE_SHORT): PositionState.FLAT,
    }
    return allowed.get((current, action))


def futures_exchange_side(action: PositionAction) -> Side:
    if action in {PositionAction.OPEN_LONG, PositionAction.CLOSE_SHORT}:
        return Side.BUY
    return Side.SELL


def estimate_costs(
    *,
    notional: Decimal,
    maker_fee_rate: Decimal,
    taker_fee_rate: Decimal,
    spread_cost: Decimal = Decimal("0"),
    slippage_cost: Decimal = Decimal("0"),
    funding_cost: Decimal = Decimal("0"),
) -> CostEstimate:
    entry_fee = notional * maker_fee_rate
    exit_fee = notional * taker_fee_rate
    total = entry_fee + exit_fee + spread_cost + slippage_cost + funding_cost
    return CostEstimate(
        maker_fee_rate=maker_fee_rate,
        taker_fee_rate=taker_fee_rate,
        entry_fee=entry_fee,
        exit_fee=exit_fee,
        spread_cost=spread_cost,
        slippage_cost=slippage_cost,
        funding_cost=funding_cost,
        total_estimated_cost=total,
    )


def estimate_net_edge(
    *,
    expected_gross_price_move: Decimal | None,
    minimum_net_edge: Decimal,
    cost: CostEstimate,
    funding: FundingEstimate,
) -> NetEdgeEstimate:
    if funding.capability != "available":
        return NetEdgeEstimate(
            expected_gross_price_move=expected_gross_price_move,
            minimum_net_edge=minimum_net_edge,
            cost=cost,
            funding=funding,
            expected_net_edge=None,
            approved=False,
            reason="funding estimate unavailable",
        )
    if expected_gross_price_move is None:
        return NetEdgeEstimate(
            expected_gross_price_move=None,
            minimum_net_edge=minimum_net_edge,
            cost=cost,
            funding=funding,
            expected_net_edge=None,
            approved=False,
            reason="expected gross move unavailable",
        )
    net = expected_gross_price_move - cost.total_estimated_cost - funding.estimated_funding_impact
    return NetEdgeEstimate(
        expected_gross_price_move=expected_gross_price_move,
        minimum_net_edge=minimum_net_edge,
        cost=cost,
        funding=funding,
        expected_net_edge=net,
        approved=net >= minimum_net_edge,
        reason="net edge meets gate" if net >= minimum_net_edge else "net edge below minimum",
    )


def futures_client_order_id(intent_id: str) -> str:
    return f"ttf-{sha256(intent_id.encode('utf-8')).hexdigest()[:24]}"


def futures_risk_decision_id(intent_id: str, blocking: tuple[str, ...]) -> str:
    raw = f"{intent_id}|{','.join(blocking)}"
    return f"frisk-{sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _demo_linear_safety_ok(config: FuturesExecutionConfig, intent: FuturesTradeIntent) -> bool:
    return (
        config.trading_mode is TradingMode.PAPER
        and not config.live_trading_enabled
        and config.bybit_environment is BybitEnvironment.DEMO
        and config.bybit_base_url == "https://api-demo.bybit.com"
        and config.category is ContractCategory.LINEAR
        and intent.category is ContractCategory.LINEAR
        and intent.symbol == config.symbol
    )


def _account_matches_intent(
    intent: FuturesTradeIntent,
    instrument: FuturesInstrumentMetadata,
    account: FuturesAccountState,
) -> bool:
    return (
        account.symbol == intent.symbol
        and account.category is intent.category
        and account.settlement_asset == instrument.settlement_asset
    )


def _position_state_matches_size(state: PositionState, position_size: Decimal) -> bool:
    if state is PositionState.FLAT:
        return position_size == 0
    if state is PositionState.LONG:
        return position_size > 0
    if state is PositionState.SHORT:
        return position_size < 0
    return False


def _close_quantity_is_covered(intent: FuturesTradeIntent, position_size: Decimal) -> bool:
    if intent.action is PositionAction.CLOSE_LONG:
        return position_size > 0 and intent.quantity <= abs(position_size)
    if intent.action is PositionAction.CLOSE_SHORT:
        return position_size < 0 and intent.quantity <= abs(position_size)
    return True


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _error_code(exc: BybitApiError) -> str:
    return getattr(exc, "code", None) or exc.__class__.__name__
