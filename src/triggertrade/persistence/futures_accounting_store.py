"""SQLite persistence for deterministic futures accounting facts."""

from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
import sqlite3

from triggertrade.accounting import ClosedTradeResult, EquitySnapshot, FuturesFillEvent, FuturesFundingEvent
from triggertrade.execution.futures import PositionState


class FuturesAccountingStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def record_fill(self, event: FuturesFillEvent) -> bool:
        values = _fill_values(event)
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM futures_accounting_fills WHERE event_id = ?", (event.event_id,)).fetchone()
            if existing is not None:
                if tuple(existing[key] for key in _FILL_COLUMNS) != values:
                    raise ValueError("immutable futures fill event conflict")
                return False
            conn.execute(
                f"INSERT INTO futures_accounting_fills ({', '.join(_FILL_COLUMNS)}) VALUES ({', '.join('?' for _ in _FILL_COLUMNS)})",
                values,
            )
        return True

    def record_funding(self, event: FuturesFundingEvent) -> bool:
        values = _funding_values(event)
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM futures_accounting_funding WHERE event_id = ?", (event.event_id,)).fetchone()
            if existing is not None:
                if tuple(existing[key] for key in _FUNDING_COLUMNS) != values:
                    raise ValueError("immutable futures funding event conflict")
                return False
            conn.execute(
                f"INSERT INTO futures_accounting_funding ({', '.join(_FUNDING_COLUMNS)}) VALUES ({', '.join('?' for _ in _FUNDING_COLUMNS)})",
                values,
            )
        return True

    def record_closed_trade(self, result: ClosedTradeResult) -> bool:
        values = _closed_trade_values(result)
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM futures_closed_trades WHERE trade_id = ?", (result.trade_id,)).fetchone()
            if existing is not None:
                if tuple(existing[key] for key in _CLOSED_TRADE_COLUMNS) != values:
                    raise ValueError("immutable futures closed trade conflict")
                return False
            conn.execute(
                f"INSERT INTO futures_closed_trades ({', '.join(_CLOSED_TRADE_COLUMNS)}) VALUES ({', '.join('?' for _ in _CLOSED_TRADE_COLUMNS)})",
                values,
            )
        return True

    def record_equity_snapshot(self, snapshot: EquitySnapshot) -> bool:
        values = _equity_values(snapshot)
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM futures_equity_snapshots WHERE snapshot_id = ?", (snapshot.snapshot_id,)).fetchone()
            if existing is not None:
                if tuple(existing[key] for key in _EQUITY_COLUMNS) != values:
                    raise ValueError("immutable futures equity snapshot conflict")
                return False
            conn.execute(
                f"INSERT INTO futures_equity_snapshots ({', '.join(_EQUITY_COLUMNS)}) VALUES ({', '.join('?' for _ in _EQUITY_COLUMNS)})",
                values,
            )
        return True

    def list_fills(self, trade_id: str) -> tuple[FuturesFillEvent, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM futures_accounting_fills WHERE trade_id = ? ORDER BY occurred_at, event_id",
                (trade_id,),
            ).fetchall()
        return tuple(_row_to_fill(row) for row in rows)

    def list_funding(self, trade_id: str) -> tuple[FuturesFundingEvent, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM futures_accounting_funding WHERE trade_id = ? ORDER BY funding_time, event_id",
                (trade_id,),
            ).fetchall()
        return tuple(_row_to_funding(row) for row in rows)

    def list_closed_trades(self, limit: int = 20) -> tuple[sqlite3.Row, ...]:
        with self._connect() as conn:
            return tuple(
                conn.execute(
                    "SELECT * FROM futures_closed_trades ORDER BY closed_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            )

    def latest_equity_snapshot(self) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM futures_equity_snapshots ORDER BY observed_at DESC, snapshot_id DESC LIMIT 1"
            ).fetchone()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS futures_accounting_fills (
                    event_id TEXT PRIMARY KEY,
                    trade_id TEXT NOT NULL,
                    execution_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity TEXT NOT NULL,
                    price TEXT NOT NULL,
                    fee TEXT NOT NULL,
                    fee_asset TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    settlement_asset TEXT NOT NULL,
                    contract_size TEXT NOT NULL,
                    requested_price TEXT,
                    trigger_set_id TEXT,
                    trigger_set_version TEXT,
                    regime_label TEXT,
                    source TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS futures_accounting_funding (
                    event_id TEXT PRIMARY KEY,
                    trade_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    funding_time TEXT NOT NULL,
                    funding_rate TEXT,
                    amount TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    source TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS futures_closed_trades (
                    trade_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    quantity TEXT NOT NULL,
                    leverage TEXT NOT NULL,
                    entry_vwap TEXT NOT NULL,
                    exit_vwap TEXT NOT NULL,
                    gross_pnl TEXT NOT NULL,
                    entry_fee TEXT NOT NULL,
                    exit_fee TEXT NOT NULL,
                    other_fees TEXT NOT NULL,
                    funding TEXT NOT NULL,
                    net_pnl TEXT NOT NULL,
                    opened_at TEXT NOT NULL,
                    closed_at TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    accounting_version TEXT NOT NULL,
                    settlement_asset TEXT NOT NULL,
                    contract_size TEXT NOT NULL,
                    trigger_set_id TEXT,
                    trigger_set_version TEXT,
                    regime_label TEXT,
                    entry_slippage_cost TEXT,
                    exit_slippage_cost TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS futures_equity_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    observed_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    wallet_balance TEXT NOT NULL,
                    equity TEXT NOT NULL,
                    available_margin TEXT NOT NULL,
                    used_margin TEXT NOT NULL,
                    unrealized_pnl TEXT NOT NULL,
                    realized_pnl TEXT NOT NULL,
                    running_peak TEXT NOT NULL,
                    drawdown_absolute TEXT NOT NULL,
                    drawdown_percent TEXT NOT NULL,
                    max_drawdown TEXT NOT NULL,
                    accounting_version TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


_FILL_COLUMNS = tuple(asdict(FuturesFillEvent("", "", "", "", PositionState.LONG, "", Decimal("0"), Decimal("1"), Decimal("0"), "USDT", "")).keys())
_FUNDING_COLUMNS = tuple(asdict(FuturesFundingEvent("", "", "", PositionState.LONG, "", None, Decimal("0"), "USDT")).keys())
_CLOSED_TRADE_COLUMNS = (
    "trade_id",
    "symbol",
    "direction",
    "quantity",
    "leverage",
    "entry_vwap",
    "exit_vwap",
    "gross_pnl",
    "entry_fee",
    "exit_fee",
    "other_fees",
    "funding",
    "net_pnl",
    "opened_at",
    "closed_at",
    "duration_seconds",
    "accounting_version",
    "settlement_asset",
    "contract_size",
    "trigger_set_id",
    "trigger_set_version",
    "regime_label",
    "entry_slippage_cost",
    "exit_slippage_cost",
)
_EQUITY_COLUMNS = tuple(asdict(EquitySnapshot("", "", "", Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"))).keys())


def _fill_values(event: FuturesFillEvent) -> tuple[str | None, ...]:
    return (
        event.event_id,
        event.trade_id,
        event.execution_id,
        event.symbol,
        event.direction.value,
        event.action,
        str(event.quantity),
        str(event.price),
        str(event.fee),
        event.fee_asset,
        event.occurred_at,
        event.settlement_asset,
        str(event.contract_size),
        None if event.requested_price is None else str(event.requested_price),
        event.trigger_set_id,
        event.trigger_set_version,
        event.regime_label,
        event.source,
    )


def _funding_values(event: FuturesFundingEvent) -> tuple[str | None, ...]:
    return (
        event.event_id,
        event.trade_id,
        event.symbol,
        event.direction.value,
        event.funding_time,
        None if event.funding_rate is None else str(event.funding_rate),
        str(event.amount),
        event.asset,
        event.source,
    )


def _closed_trade_values(result: ClosedTradeResult) -> tuple[str | int | None, ...]:
    return (
        result.trade_id,
        result.symbol,
        result.direction.value,
        str(result.quantity),
        str(result.leverage),
        str(result.entry_vwap),
        str(result.exit_vwap),
        str(result.gross_pnl),
        str(result.entry_fee),
        str(result.exit_fee),
        str(result.other_fees),
        str(result.funding),
        str(result.net_pnl),
        result.opened_at,
        result.closed_at,
        result.duration_seconds,
        result.accounting_version,
        result.settlement_asset,
        str(result.contract_size),
        result.trigger_set_id,
        result.trigger_set_version,
        result.regime_label,
        None if result.entry_slippage is None or result.entry_slippage.slippage_cost is None else str(result.entry_slippage.slippage_cost),
        None if result.exit_slippage is None or result.exit_slippage.slippage_cost is None else str(result.exit_slippage.slippage_cost),
    )


def _equity_values(snapshot: EquitySnapshot) -> tuple[str, ...]:
    return (
        snapshot.snapshot_id,
        snapshot.observed_at,
        snapshot.source,
        str(snapshot.wallet_balance),
        str(snapshot.equity),
        str(snapshot.available_margin),
        str(snapshot.used_margin),
        str(snapshot.unrealized_pnl),
        str(snapshot.realized_pnl),
        str(snapshot.running_peak),
        str(snapshot.drawdown_absolute),
        str(snapshot.drawdown_percent),
        str(snapshot.max_drawdown),
        snapshot.accounting_version,
    )


def _row_to_fill(row: sqlite3.Row) -> FuturesFillEvent:
    return FuturesFillEvent(
        event_id=row["event_id"],
        trade_id=row["trade_id"],
        execution_id=row["execution_id"],
        symbol=row["symbol"],
        direction=PositionState(row["direction"]),
        action=row["action"],
        quantity=Decimal(row["quantity"]),
        price=Decimal(row["price"]),
        fee=Decimal(row["fee"]),
        fee_asset=row["fee_asset"],
        occurred_at=row["occurred_at"],
        settlement_asset=row["settlement_asset"],
        contract_size=Decimal(row["contract_size"]),
        requested_price=None if row["requested_price"] is None else Decimal(row["requested_price"]),
        trigger_set_id=row["trigger_set_id"],
        trigger_set_version=row["trigger_set_version"],
        regime_label=row["regime_label"],
        source=row["source"],
    )


def _row_to_funding(row: sqlite3.Row) -> FuturesFundingEvent:
    return FuturesFundingEvent(
        event_id=row["event_id"],
        trade_id=row["trade_id"],
        symbol=row["symbol"],
        direction=PositionState(row["direction"]),
        funding_time=row["funding_time"],
        funding_rate=None if row["funding_rate"] is None else Decimal(row["funding_rate"]),
        amount=Decimal(row["amount"]),
        asset=row["asset"],
        source=row["source"],
    )
