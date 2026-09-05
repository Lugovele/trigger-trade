"""Deterministic accounting for linear perpetual futures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from triggertrade.execution.futures import PositionAction, PositionState


ACCOUNTING_VERSION = "futures-accounting-v1"


class AccountingError(ValueError):
    """Raised when accounting facts are incomplete or inconsistent."""


class ValuationPriceSource(StrEnum):
    MARK = "MARK"
    LAST = "LAST"
    INDEX = "INDEX"


@dataclass(frozen=True)
class FuturesFillEvent:
    event_id: str
    trade_id: str
    execution_id: str
    symbol: str
    direction: PositionState
    action: str
    quantity: Decimal
    price: Decimal
    fee: Decimal
    fee_asset: str
    occurred_at: str
    settlement_asset: str = "USDT"
    contract_size: Decimal = Decimal("1")
    requested_price: Decimal | None = None
    trigger_set_id: str | None = None
    trigger_set_version: str | None = None
    regime_label: str | None = None
    source: str = "exchange"


@dataclass(frozen=True)
class FuturesFundingEvent:
    event_id: str
    trade_id: str
    symbol: str
    direction: PositionState
    funding_time: str
    funding_rate: Decimal | None
    amount: Decimal
    asset: str
    source: str = "exchange"


@dataclass(frozen=True)
class SlippageMeasurement:
    reference_price: Decimal | None
    actual_vwap: Decimal
    quantity: Decimal
    slippage_per_unit: Decimal | None
    slippage_cost: Decimal | None
    convention: str = "diagnostic_only_actual_fill_price_already_in_gross_pnl"


@dataclass(frozen=True)
class ClosedTradeResult:
    trade_id: str
    symbol: str
    direction: PositionState
    quantity: Decimal
    leverage: Decimal
    entry_vwap: Decimal
    exit_vwap: Decimal
    gross_pnl: Decimal
    entry_fee: Decimal
    exit_fee: Decimal
    other_fees: Decimal
    funding: Decimal
    net_pnl: Decimal
    opened_at: str
    closed_at: str
    duration_seconds: int
    accounting_version: str = ACCOUNTING_VERSION
    settlement_asset: str = "USDT"
    contract_size: Decimal = Decimal("1")
    trigger_set_id: str | None = None
    trigger_set_version: str | None = None
    regime_label: str | None = None
    entry_slippage: SlippageMeasurement | None = None
    exit_slippage: SlippageMeasurement | None = None
    return_on_margin: Decimal | None = None
    return_on_equity: Decimal | None = None
    evidence_source: str = "exchange"
    simulation_model_version: str | None = None


@dataclass(frozen=True)
class UnrealizedPnl:
    symbol: str
    direction: PositionState
    quantity: Decimal
    entry_vwap: Decimal
    valuation_price: Decimal
    valuation_source: ValuationPriceSource
    observed_at: str
    unrealized_pnl: Decimal
    accounting_version: str = ACCOUNTING_VERSION
    settlement_asset: str = "USDT"


@dataclass(frozen=True)
class EquitySnapshot:
    snapshot_id: str
    observed_at: str
    source: str
    wallet_balance: Decimal
    equity: Decimal
    available_margin: Decimal
    used_margin: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    running_peak: Decimal
    drawdown_absolute: Decimal
    drawdown_percent: Decimal
    max_drawdown: Decimal
    accounting_version: str = ACCOUNTING_VERSION


def compute_vwap(fills: tuple[FuturesFillEvent, ...]) -> Decimal:
    if not fills:
        raise AccountingError("VWAP requires at least one fill")
    if any(fill.price <= 0 or fill.quantity <= 0 for fill in fills):
        raise AccountingError("VWAP requires positive fill price and quantity")
    quantity = sum((fill.quantity for fill in fills), Decimal("0"))
    if quantity <= 0:
        raise AccountingError("VWAP requires positive total quantity")
    return sum((fill.quantity * fill.price for fill in fills), Decimal("0")) / quantity


def gross_pnl(
    *,
    direction: PositionState,
    quantity: Decimal,
    entry_vwap: Decimal,
    exit_vwap: Decimal,
    contract_size: Decimal = Decimal("1"),
) -> Decimal:
    _validate_direction(direction)
    if quantity <= 0 or entry_vwap <= 0 or exit_vwap <= 0 or contract_size <= 0:
        raise AccountingError("P&L inputs must be positive")
    if direction is PositionState.LONG:
        return (exit_vwap - entry_vwap) * quantity * contract_size
    return (entry_vwap - exit_vwap) * quantity * contract_size


def close_futures_trade(
    *,
    trade_id: str,
    entry_fills: tuple[FuturesFillEvent, ...],
    exit_fills: tuple[FuturesFillEvent, ...],
    funding_events: tuple[FuturesFundingEvent, ...] = (),
    leverage: Decimal = Decimal("1"),
    other_fees: Decimal = Decimal("0"),
) -> ClosedTradeResult:
    if leverage <= 0:
        raise AccountingError("leverage must be positive")
    if other_fees < 0:
        raise AccountingError("other fees must be a positive cost")
    if any(fill.trade_id != trade_id for fill in entry_fills + exit_fills):
        raise AccountingError("fill attribution does not match trade")
    direction = _single_direction(entry_fills)
    if _single_direction(exit_fills) is not direction:
        raise AccountingError("entry and exit fills must share one direction")
    _validate_fill_actions(direction, entry_fills, exit_fills)
    symbol = _single_symbol(entry_fills + exit_fills)
    settlement_asset = _single_settlement_asset(entry_fills + exit_fills)
    _validate_fee_assets(entry_fills + exit_fills, settlement_asset)
    contract_size = _single_contract_size(entry_fills + exit_fills)

    entry_qty = sum((fill.quantity for fill in entry_fills), Decimal("0"))
    exit_qty = sum((fill.quantity for fill in exit_fills), Decimal("0"))
    if exit_qty <= 0:
        raise AccountingError("closed trade requires exit quantity")
    if exit_qty > entry_qty:
        raise AccountingError("exit quantity cannot exceed entry quantity")

    entry_vwap = compute_vwap(entry_fills)
    exit_vwap = compute_vwap(exit_fills)
    if any(fill.fee < 0 for fill in entry_fills + exit_fills):
        raise AccountingError("fees must be positive costs")
    entry_fee_total = sum((fill.fee for fill in entry_fills), Decimal("0"))
    exit_fee = sum((fill.fee for fill in exit_fills), Decimal("0"))
    entry_fee = entry_fee_total * (exit_qty / entry_qty)
    funding = _funding_amount(funding_events, trade_id, symbol, settlement_asset, direction)
    gross = gross_pnl(direction=direction, quantity=exit_qty, entry_vwap=entry_vwap, exit_vwap=exit_vwap, contract_size=contract_size)
    net = gross - entry_fee - exit_fee - other_fees + funding
    opened_at = min(fill.occurred_at for fill in entry_fills)
    closed_at = max(fill.occurred_at for fill in exit_fills)
    return ClosedTradeResult(
        trade_id=trade_id,
        symbol=symbol,
        direction=direction,
        quantity=exit_qty,
        leverage=leverage,
        entry_vwap=entry_vwap,
        exit_vwap=exit_vwap,
        gross_pnl=gross,
        entry_fee=entry_fee,
        exit_fee=exit_fee,
        other_fees=other_fees,
        funding=funding,
        net_pnl=net,
        opened_at=opened_at,
        closed_at=closed_at,
        duration_seconds=max(0, int((datetime.fromisoformat(closed_at) - datetime.fromisoformat(opened_at)).total_seconds())),
        settlement_asset=settlement_asset,
        contract_size=contract_size,
        trigger_set_id=entry_fills[0].trigger_set_id,
        trigger_set_version=entry_fills[0].trigger_set_version,
        regime_label=entry_fills[0].regime_label,
        entry_slippage=measure_slippage(entry_fills),
        exit_slippage=measure_slippage(exit_fills),
        evidence_source=_single_source(entry_fills + exit_fills),
        simulation_model_version=None,
    )


def calculate_unrealized_pnl(
    *,
    symbol: str,
    direction: PositionState,
    quantity: Decimal,
    entry_vwap: Decimal,
    mark_price: Decimal,
    observed_at: str,
    contract_size: Decimal = Decimal("1"),
) -> UnrealizedPnl:
    return UnrealizedPnl(
        symbol=symbol,
        direction=direction,
        quantity=quantity,
        entry_vwap=entry_vwap,
        valuation_price=mark_price,
        valuation_source=ValuationPriceSource.MARK,
        observed_at=observed_at,
        unrealized_pnl=gross_pnl(
            direction=direction,
            quantity=quantity,
            entry_vwap=entry_vwap,
            exit_vwap=mark_price,
            contract_size=contract_size,
        ),
    )


def calculate_drawdown_snapshot(
    *,
    snapshot_id: str,
    observed_at: str,
    source: str,
    wallet_balance: Decimal,
    equity: Decimal,
    available_margin: Decimal,
    used_margin: Decimal,
    unrealized_pnl: Decimal,
    realized_pnl: Decimal,
    previous_running_peak: Decimal | None = None,
    previous_max_drawdown: Decimal = Decimal("0"),
) -> EquitySnapshot:
    peak = max(equity, previous_running_peak if previous_running_peak is not None else equity)
    drawdown = peak - equity
    drawdown_pct = Decimal("0") if peak == 0 else drawdown / peak * Decimal("100")
    max_drawdown = max(previous_max_drawdown, drawdown)
    return EquitySnapshot(
        snapshot_id=snapshot_id,
        observed_at=observed_at,
        source=source,
        wallet_balance=wallet_balance,
        equity=equity,
        available_margin=available_margin,
        used_margin=used_margin,
        unrealized_pnl=unrealized_pnl,
        realized_pnl=realized_pnl,
        running_peak=peak,
        drawdown_absolute=drawdown,
        drawdown_percent=drawdown_pct,
        max_drawdown=max_drawdown,
    )


def measure_slippage(fills: tuple[FuturesFillEvent, ...]) -> SlippageMeasurement | None:
    if not fills:
        return None
    reference = fills[0].requested_price
    actual = compute_vwap(fills)
    quantity = sum((fill.quantity for fill in fills), Decimal("0"))
    if reference is None:
        return SlippageMeasurement(reference, actual, quantity, None, None)
    per_unit = actual - reference
    return SlippageMeasurement(reference, actual, quantity, per_unit, abs(per_unit) * quantity)


def _validate_direction(direction: PositionState) -> None:
    if direction not in {PositionState.LONG, PositionState.SHORT}:
        raise AccountingError("accounting direction must be LONG or SHORT")


def _single_direction(fills: tuple[FuturesFillEvent, ...]) -> PositionState:
    if not fills:
        raise AccountingError("fills are required")
    directions = {fill.direction for fill in fills}
    if len(directions) != 1:
        raise AccountingError("fills contain mixed directions")
    direction = directions.pop()
    _validate_direction(direction)
    return direction


def _single_symbol(fills: tuple[FuturesFillEvent, ...]) -> str:
    symbols = {fill.symbol for fill in fills}
    if len(symbols) != 1:
        raise AccountingError("fills contain mixed symbols")
    return symbols.pop()


def _single_settlement_asset(fills: tuple[FuturesFillEvent, ...]) -> str:
    assets = {fill.settlement_asset for fill in fills}
    if len(assets) != 1:
        raise AccountingError("fills contain mixed settlement assets")
    return assets.pop()


def _single_contract_size(fills: tuple[FuturesFillEvent, ...]) -> Decimal:
    sizes = {fill.contract_size for fill in fills}
    if len(sizes) != 1:
        raise AccountingError("fills contain mixed contract sizes")
    size = sizes.pop()
    if size <= 0:
        raise AccountingError("contract size must be positive")
    return size


def _single_source(fills: tuple[FuturesFillEvent, ...]) -> str:
    sources = {fill.source for fill in fills}
    if len(sources) != 1:
        raise AccountingError("fills contain mixed evidence sources")
    return sources.pop()


def _validate_fee_assets(fills: tuple[FuturesFillEvent, ...], settlement_asset: str) -> None:
    if any(fill.fee_asset != settlement_asset for fill in fills):
        raise AccountingError("fee asset conversion is unsupported in accounting v1")


def _validate_fill_actions(
    direction: PositionState,
    entry_fills: tuple[FuturesFillEvent, ...],
    exit_fills: tuple[FuturesFillEvent, ...],
) -> None:
    if direction is PositionState.LONG:
        entry_action = PositionAction.OPEN_LONG.value
        exit_action = PositionAction.CLOSE_LONG.value
    elif direction is PositionState.SHORT:
        entry_action = PositionAction.OPEN_SHORT.value
        exit_action = PositionAction.CLOSE_SHORT.value
    else:
        raise AccountingError("accounting direction must be LONG or SHORT")
    if any(fill.action != entry_action for fill in entry_fills):
        raise AccountingError("entry fill action does not match direction")
    if any(fill.action != exit_action for fill in exit_fills):
        raise AccountingError("exit fill action does not match direction")


def _funding_amount(
    funding_events: tuple[FuturesFundingEvent, ...],
    trade_id: str,
    symbol: str,
    settlement_asset: str,
    direction: PositionState,
) -> Decimal:
    amount = Decimal("0")
    seen: set[str] = set()
    for event in funding_events:
        if event.event_id in seen:
            raise AccountingError("duplicate funding event")
        seen.add(event.event_id)
        if event.trade_id != trade_id or event.symbol != symbol or event.asset != settlement_asset or event.direction is not direction:
            raise AccountingError("funding event attribution does not match trade")
        amount += event.amount
    return amount
