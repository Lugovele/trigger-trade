"""Execution service enforcing risk, safety, idempotency, and audit trail."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Callable

from triggertrade.config import (
    AppConfig,
    BybitEnvironment,
    ExecutionVenue,
    Market,
    TradingMode,
)
from triggertrade.execution.bybit import BybitExecutionAdapter, map_bybit_order_status
from triggertrade.execution.contracts import OrderStatus, OrderType, RiskDecision, TradeIntent
from triggertrade.exchanges import BybitApiError
from triggertrade.market_data import BybitInstrument
from triggertrade.persistence import ExecutionFill, ExecutionRecord, ExecutionStore

from .precision import validate_limit_order_precision


_MANDATORY_RISK_RULE_IDS = frozenset({"RSK-001", "RSK-002", "RSK-003", "RSK-004", "RSK-005"})


class ExecutionError(RuntimeError):
    """Raised when execution must fail closed."""


class ExecutionService:
    def __init__(
        self,
        *,
        config: AppConfig,
        adapter: BybitExecutionAdapter,
        store: ExecutionStore,
        instrument: BybitInstrument,
        available_quote_balance: Decimal | None = None,
        execution_lane: str | None = None,
        operator_trading_state: Callable[[], str] | None = None,
    ) -> None:
        self._config = config
        self._adapter = adapter
        self._store = store
        self._instrument = instrument
        self._available_quote_balance = available_quote_balance
        self._execution_lane = execution_lane
        self._operator_trading_state = operator_trading_state

    def submit_approved_limit_order(
        self,
        *,
        intent: TradeIntent,
        risk_decision: RiskDecision,
    ) -> ExecutionRecord:
        self._validate_environment(intent)
        self._validate_risk(intent, risk_decision)
        validate_limit_order_precision(
            instrument=self._instrument,
            quantity=intent.quantity,
            price=intent.price,
        )
        self._validate_available_balance(intent)
        self._validate_operator_trading_state()

        now = _now()
        client_order_id = client_order_id_for_intent(intent.intent_id)
        record = ExecutionRecord(
            intent_id=intent.intent_id,
            risk_decision_id=risk_decision.risk_decision_id,
            client_order_id=client_order_id,
            exchange_order_id=None,
            symbol=intent.symbol,
            side=intent.side.value,
            order_type=intent.order_type.value,
            requested_qty=str(intent.quantity),
            requested_price=str(intent.price),
            status=OrderStatus.CREATED,
            created_at=now,
            updated_at=now,
            reconciliation_state="reserved",
        )
        record, created = self._store.reserve(record)
        if not created:
            return self.reconcile(record)

        submitting = replace(record, status=OrderStatus.SUBMITTING, updated_at=_now())
        self._store.update(submitting)

        try:
            response = self._adapter.create_limit_order(
                symbol=intent.symbol,
                side=intent.side,
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

        result = response.result
        submitted = replace(
            submitting,
            status=OrderStatus.SUBMITTED,
            exchange_order_id=result.get("orderId") or submitting.exchange_order_id,
            updated_at=_now(),
            exchange_status="create_accepted",
            reconciliation_state="submitted",
        )
        return self._store.update(submitted)

    def cancel(self, record: ExecutionRecord) -> ExecutionRecord:
        if record.status in {OrderStatus.CANCELLED, OrderStatus.FILLED, OrderStatus.REJECTED}:
            return record
        pending = replace(
            record,
            status=OrderStatus.CANCEL_PENDING,
            updated_at=_now(),
            reconciliation_state="cancel_requested",
        )
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

    def reconcile(self, record: ExecutionRecord) -> ExecutionRecord:
        try:
            order = self._adapter.reconcile_order(
                symbol=record.symbol,
                client_order_id=record.client_order_id,
            )
        except BybitApiError as exc:
            updated = replace(
                record,
                status=OrderStatus.UNKNOWN,
                updated_at=_now(),
                reconciliation_state="reconcile_failed",
                last_error_code=_error_code(exc),
            )
            return self._store.update(updated)

        if order is None:
            if not getattr(self._adapter, "uses_private_exchange_orders", True):
                order = _paper_order_from_record(record)
            else:
                updated = replace(
                    record,
                    status=OrderStatus.UNKNOWN,
                    updated_at=_now(),
                    reconciliation_state="not_found",
                )
                return self._store.update(updated)

        if order is None:
            updated = replace(
                record,
                status=OrderStatus.UNKNOWN,
                updated_at=_now(),
                reconciliation_state="not_found",
            )
            return self._store.update(updated)

        status = map_bybit_order_status(order.get("orderStatus"))
        updated = replace(
            record,
            status=status,
            exchange_order_id=order.get("orderId") or record.exchange_order_id,
            updated_at=_now(),
            exchange_status=order.get("orderStatus"),
            reconciliation_state="reconciled",
            last_error_code=None,
        )
        for fill in order.get("fills") or ():
            self._store.save_fill(
                ExecutionFill(
                    fill_id=str(fill.get("execId") or f"{record.client_order_id}-fill"),
                    intent_id=record.intent_id,
                    client_order_id=record.client_order_id,
                    symbol=record.symbol,
                    side=record.side,
                    quantity=str(fill.get("execQty") or record.requested_qty),
                    price=str(fill.get("execPrice") or record.requested_price),
                    fee=str(fill.get("execFee") or "0"),
                    created_at=str(fill.get("execTime") or _now()),
                )
            )
        return self._store.update(updated)

    def recover_unresolved(self) -> tuple[ExecutionRecord, ...]:
        return tuple(self.reconcile(record) for record in self._store.unresolved())

    def _validate_risk(self, intent: TradeIntent, risk_decision: RiskDecision) -> None:
        if risk_decision.intent_id != intent.intent_id:
            raise ExecutionError("risk decision is not bound to this intent")
        if not risk_decision.approved:
            raise ExecutionError("risk decision rejected this intent")
        checked_rule_ids = frozenset(risk_decision.checked_rule_ids)
        if not _MANDATORY_RISK_RULE_IDS.issubset(checked_rule_ids):
            raise ExecutionError("approved risk decision is missing mandatory rule evidence")
        if risk_decision.blocking_rule_ids:
            raise ExecutionError("approved risk decision contains blocking rule evidence")
        if risk_decision.approved_quantity is None or risk_decision.approved_notional is None:
            raise ExecutionError("approved risk decision is missing approved quantity or notional")
        if risk_decision.approved_quantity != intent.quantity:
            raise ExecutionError("approved risk quantity does not match intent quantity")
        if risk_decision.approved_notional != intent.quantity * intent.price:
            raise ExecutionError("approved risk notional does not match intent notional")

    def _validate_environment(self, intent: TradeIntent) -> None:
        if self._config.trading_mode is not TradingMode.PAPER:
            raise ExecutionError("execution requires paper trading mode for this demo slice")
        if self._config.live_trading_enabled:
            raise ExecutionError("live trading must remain disabled")
        if self._config.execution_venue is ExecutionVenue.LOCAL_PAPER:
            if getattr(self._adapter, "uses_private_exchange_orders", True):
                raise ExecutionError("local paper execution requires a paper adapter")
        elif self._config.execution_venue is ExecutionVenue.BYBIT_DEMO:
            if self._config.bybit.environment is not BybitEnvironment.DEMO:
                raise ExecutionError("Bybit environment must be demo")
            if self._config.bybit.base_url != "https://api-demo.bybit.com":
                raise ExecutionError("Bybit Demo execution requires the demo base URL")
        else:
            raise ExecutionError("execution venue must be local_paper or bybit_demo")
        if self._config.market is not Market.SPOT:
            raise ExecutionError("only spot market is supported")
        if intent.symbol != "BTCUSDT":
            raise ExecutionError("only BTCUSDT is supported")
        if intent.order_type is not OrderType.LIMIT:
            raise ExecutionError("only limit orders are supported")

    def _validate_available_balance(self, intent: TradeIntent) -> None:
        if intent.side is not intent.side.BUY:
            return
        if self._available_quote_balance is None:
            raise ExecutionError("available quote balance is required before buy submission")
        if self._available_quote_balance < intent.quantity * intent.price:
            raise ExecutionError("available quote balance is below requested order notional")

    def _validate_operator_trading_state(self) -> None:
        if self._execution_lane != "ACTIVE" or self._operator_trading_state is None:
            return
        state = self._operator_trading_state()
        if state == "TRADING_PAUSED":
            raise ExecutionError("new ACTIVE execution is blocked by persistent operator pause")
        if state != "TRADING_ENABLED":
            raise ExecutionError("unknown operator trading state; execution fails closed")


def client_order_id_for_intent(intent_id: str) -> str:
    return f"tt-{sha256(intent_id.encode('utf-8')).hexdigest()[:24]}"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _error_code(exc: BybitApiError) -> str:
    return getattr(exc, "code", None) or exc.__class__.__name__


def _paper_order_from_record(record: ExecutionRecord) -> dict[str, object]:
    return {
        "orderId": record.exchange_order_id or f"paper-{record.client_order_id}",
        "orderStatus": "Filled",
        "fills": (
            {
                "execId": f"paper-fill-{record.client_order_id}",
                "execQty": record.requested_qty,
                "execPrice": record.requested_price,
                "execFee": "0",
                "execTime": _now(),
            },
        ),
    }
