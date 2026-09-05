from decimal import Decimal

import pytest

from triggertrade.accounting import (
    ACCOUNTING_VERSION,
    AccountingError,
    calculate_drawdown_snapshot,
    calculate_unrealized_pnl,
    close_futures_trade,
    compute_vwap,
    gross_pnl,
)
from triggertrade.accounting.futures import FuturesFillEvent, FuturesFundingEvent
from triggertrade.dashboard.__main__ import render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.execution.futures import PositionState
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore


def test_linear_long_short_and_zero_gross_pnl_formulas():
    assert gross_pnl(direction=PositionState.LONG, quantity=Decimal("0.01"), entry_vwap=Decimal("100"), exit_vwap=Decimal("110")) == Decimal("0.10")
    assert gross_pnl(direction=PositionState.LONG, quantity=Decimal("0.01"), entry_vwap=Decimal("110"), exit_vwap=Decimal("100")) == Decimal("-0.10")
    assert gross_pnl(direction=PositionState.SHORT, quantity=Decimal("0.01"), entry_vwap=Decimal("110"), exit_vwap=Decimal("100")) == Decimal("0.10")
    assert gross_pnl(direction=PositionState.SHORT, quantity=Decimal("0.01"), entry_vwap=Decimal("100"), exit_vwap=Decimal("110")) == Decimal("-0.10")
    assert gross_pnl(direction=PositionState.SHORT, quantity=Decimal("0.01"), entry_vwap=Decimal("100"), exit_vwap=Decimal("100")) == Decimal("0.00")


def test_vwap_single_multi_fill_and_zero_quantity_fail_closed():
    fills = (
        _fill("entry-1", quantity=Decimal("0.01"), price=Decimal("100")),
        _fill("entry-2", quantity=Decimal("0.03"), price=Decimal("108")),
    )

    assert compute_vwap(fills) == Decimal("106")
    with pytest.raises(AccountingError, match="at least one fill"):
        compute_vwap(())
    with pytest.raises(AccountingError, match="positive fill"):
        compute_vwap((_fill("bad", quantity=Decimal("0"), price=Decimal("100")),))


def test_closed_long_trade_net_pnl_fees_funding_and_duration():
    result = close_futures_trade(
        trade_id="trade-long",
        entry_fills=(
            _fill("e1", trade_id="trade-long", quantity=Decimal("0.01"), price=Decimal("100"), fee=Decimal("0.001")),
            _fill("e2", trade_id="trade-long", quantity=Decimal("0.01"), price=Decimal("102"), fee=Decimal("0.001")),
        ),
        exit_fills=(_fill("x1", trade_id="trade-long", action="CLOSE_LONG", quantity=Decimal("0.02"), price=Decimal("111"), fee=Decimal("0.002")),),
        funding_events=(_funding("f1", amount=Decimal("-0.003")),),
    )

    assert result.entry_vwap == Decimal("101")
    assert result.exit_vwap == Decimal("111")
    assert result.gross_pnl == Decimal("0.20")
    assert result.entry_fee == Decimal("0.002")
    assert result.exit_fee == Decimal("0.002")
    assert result.funding == Decimal("-0.003")
    assert result.net_pnl == Decimal("0.193")
    assert result.duration_seconds == 3600
    assert result.accounting_version == ACCOUNTING_VERSION


def test_closed_short_trade_profit_and_loss():
    profit = close_futures_trade(
        trade_id="trade-short-profit",
        entry_fills=(_fill("se", trade_id="trade-short-profit", direction=PositionState.SHORT, action="OPEN_SHORT", price=Decimal("110")),),
        exit_fills=(_fill("sx", trade_id="trade-short-profit", direction=PositionState.SHORT, action="CLOSE_SHORT", price=Decimal("100")),),
    )
    loss = close_futures_trade(
        trade_id="trade-short-loss",
        entry_fills=(_fill("se2", trade_id="trade-short-loss", direction=PositionState.SHORT, action="OPEN_SHORT", price=Decimal("100")),),
        exit_fills=(_fill("sx2", trade_id="trade-short-loss", direction=PositionState.SHORT, action="CLOSE_SHORT", price=Decimal("110")),),
    )

    assert profit.gross_pnl == Decimal("0.010")
    assert loss.gross_pnl == Decimal("-0.010")


def test_partial_close_prorates_entry_fee_and_rejects_overclose():
    result = close_futures_trade(
        trade_id="partial",
        entry_fills=(_fill("entry", trade_id="partial", quantity=Decimal("0.03"), price=Decimal("100"), fee=Decimal("0.006")),),
        exit_fills=(_fill("exit", trade_id="partial", action="CLOSE_LONG", quantity=Decimal("0.01"), price=Decimal("110"), fee=Decimal("0.002")),),
    )

    assert result.quantity == Decimal("0.01")
    assert result.entry_fee == Decimal("0.002")
    assert result.net_pnl == Decimal("0.096")

    with pytest.raises(AccountingError, match="cannot exceed"):
        close_futures_trade(
            trade_id="overclose",
            entry_fills=(_fill("entry-o", trade_id="overclose", quantity=Decimal("0.01")),),
            exit_fills=(_fill("exit-o", trade_id="overclose", action="CLOSE_LONG", quantity=Decimal("0.02")),),
        )


def test_slippage_is_diagnostic_not_subtracted_twice():
    result = close_futures_trade(
        trade_id="slip",
        entry_fills=(_fill("entry-s", trade_id="slip", quantity=Decimal("0.01"), price=Decimal("100"), requested_price=Decimal("99")),),
        exit_fills=(_fill("exit-s", trade_id="slip", action="CLOSE_LONG", quantity=Decimal("0.01"), price=Decimal("110"), requested_price=Decimal("111")),),
    )

    assert result.gross_pnl == Decimal("0.10")
    assert result.entry_slippage is not None
    assert result.entry_slippage.slippage_cost == Decimal("0.01")
    assert result.exit_slippage is not None
    assert result.exit_slippage.slippage_cost == Decimal("0.01")
    assert result.net_pnl == result.gross_pnl


def test_fee_asset_conversion_and_duplicate_funding_fail_closed():
    with pytest.raises(AccountingError, match="fee asset conversion"):
        close_futures_trade(
            trade_id="fee-asset",
            entry_fills=(_fill("entry-asset", trade_id="fee-asset", fee_asset="BTC"),),
            exit_fills=(_fill("exit-asset", trade_id="fee-asset", action="CLOSE_LONG"),),
        )

    with pytest.raises(AccountingError, match="duplicate funding"):
        close_futures_trade(
            trade_id="dup-funding",
            entry_fills=(_fill("entry-f", trade_id="dup-funding"),),
            exit_fills=(_fill("exit-f", trade_id="dup-funding", action="CLOSE_LONG"),),
            funding_events=(_funding("same", trade_id="dup-funding"), _funding("same", trade_id="dup-funding")),
        )


def test_fill_actions_must_match_trade_direction():
    with pytest.raises(AccountingError, match="entry fill action"):
        close_futures_trade(
            trade_id="bad-entry-action",
            entry_fills=(_fill("bad-entry", trade_id="bad-entry-action", action="CLOSE_LONG"),),
            exit_fills=(_fill("bad-exit", trade_id="bad-entry-action", action="CLOSE_LONG"),),
        )
    with pytest.raises(AccountingError, match="exit fill action"):
        close_futures_trade(
            trade_id="bad-exit-action",
            entry_fills=(_fill("good-entry", trade_id="bad-exit-action", action="OPEN_SHORT", direction=PositionState.SHORT),),
            exit_fills=(_fill("bad-exit-2", trade_id="bad-exit-action", action="OPEN_SHORT", direction=PositionState.SHORT),),
        )


def test_individual_negative_fee_and_funding_direction_fail_closed():
    with pytest.raises(AccountingError, match="fees must be positive"):
        close_futures_trade(
            trade_id="negative-fee",
            entry_fills=(
                _fill("negative-fee-1", trade_id="negative-fee", fee=Decimal("-1")),
                _fill("negative-fee-2", trade_id="negative-fee", fee=Decimal("2")),
            ),
            exit_fills=(_fill("negative-fee-exit", trade_id="negative-fee", action="CLOSE_LONG"),),
        )

    with pytest.raises(AccountingError, match="funding event attribution"):
        close_futures_trade(
            trade_id="bad-funding-direction",
            entry_fills=(_fill("bad-funding-entry", trade_id="bad-funding-direction"),),
            exit_fills=(_fill("bad-funding-exit", trade_id="bad-funding-direction", action="CLOSE_LONG"),),
            funding_events=(
                _funding("bad-funding", trade_id="bad-funding-direction", direction=PositionState.SHORT),
            ),
        )


def test_unrealized_pnl_uses_mark_price_source():
    unrealized = calculate_unrealized_pnl(
        symbol="BTCUSDT",
        direction=PositionState.LONG,
        quantity=Decimal("0.02"),
        entry_vwap=Decimal("100"),
        mark_price=Decimal("105"),
        observed_at="2026-09-05T01:00:00+00:00",
    )

    assert unrealized.valuation_source.value == "MARK"
    assert unrealized.unrealized_pnl == Decimal("0.10")


def test_equity_drawdown_uses_real_snapshots_only():
    first = calculate_drawdown_snapshot(
        snapshot_id="eq-1",
        observed_at="2026-09-05T00:00:00+00:00",
        source="exchange_wallet",
        wallet_balance=Decimal("100"),
        equity=Decimal("100"),
        available_margin=Decimal("95"),
        used_margin=Decimal("5"),
        unrealized_pnl=Decimal("0"),
        realized_pnl=Decimal("0"),
    )
    second = calculate_drawdown_snapshot(
        snapshot_id="eq-2",
        observed_at="2026-09-05T00:01:00+00:00",
        source="exchange_wallet",
        wallet_balance=Decimal("98"),
        equity=Decimal("98"),
        available_margin=Decimal("93"),
        used_margin=Decimal("5"),
        unrealized_pnl=Decimal("-2"),
        realized_pnl=Decimal("0"),
        previous_running_peak=first.running_peak,
        previous_max_drawdown=first.max_drawdown,
    )

    assert second.running_peak == Decimal("100")
    assert second.drawdown_absolute == Decimal("2")
    assert second.drawdown_percent == Decimal("2.00")
    assert second.max_drawdown == Decimal("2")


def test_accounting_store_idempotency_restart_and_attribution(tmp_path):
    store = FuturesAccountingStore(tmp_path / "accounting.sqlite3")
    fill = _fill(
        "persist-fill",
        trade_id="persist-trade",
        trigger_set_id="triggertrade-core",
        trigger_set_version="v1",
        regime_label="UPTREND",
    )
    result = close_futures_trade(
        trade_id="persist-trade",
        entry_fills=(fill,),
        exit_fills=(_fill("persist-exit", trade_id="persist-trade", action="CLOSE_LONG", trigger_set_id="triggertrade-core", trigger_set_version="v1"),),
    )

    assert store.record_fill(fill) is True
    assert store.record_fill(fill) is False
    assert store.record_closed_trade(result) is True

    reopened = FuturesAccountingStore(tmp_path / "accounting.sqlite3")
    rows = reopened.list_closed_trades()

    assert len(rows) == 1
    assert rows[0]["trigger_set_id"] == "triggertrade-core"
    assert rows[0]["regime_label"] == "UPTREND"
    with pytest.raises(ValueError, match="immutable futures fill"):
        reopened.record_fill(_fill("persist-fill", trade_id="persist-trade", price=Decimal("101")))


def test_dashboard_renders_only_accounting_backed_values(tmp_path):
    db = tmp_path / "dashboard-accounting.sqlite3"
    store = FuturesAccountingStore(db)
    result = close_futures_trade(
        trade_id="dash-trade",
        entry_fills=(_fill("dash-entry", trade_id="dash-trade"),),
        exit_fills=(_fill("dash-exit", trade_id="dash-trade", action="CLOSE_LONG", price=Decimal("110")),),
    )
    snapshot = calculate_drawdown_snapshot(
        snapshot_id="dash-equity",
        observed_at="2026-09-05T00:02:00+00:00",
        source="exchange_wallet",
        wallet_balance=Decimal("100"),
        equity=Decimal("101"),
        available_margin=Decimal("96"),
        used_margin=Decimal("5"),
        unrealized_pnl=Decimal("0"),
        realized_pnl=result.net_pnl,
    )
    store.record_closed_trade(result)
    store.record_equity_snapshot(snapshot)

    html = render_dashboard(DashboardReadModel(db), initial_page="analytics")

    assert "Futures Accounting" in html
    assert "dash-trade" in html
    assert "101" in html
    assert "BYBIT_API_SECRET" not in html
    assert "frontend financial calculations" in html


def _fill(
    event_id: str,
    *,
    trade_id: str = "trade-1",
    direction: PositionState = PositionState.LONG,
    action: str = "OPEN_LONG",
    quantity: Decimal = Decimal("0.001"),
    price: Decimal = Decimal("100"),
    fee: Decimal = Decimal("0"),
    fee_asset: str = "USDT",
    requested_price: Decimal | None = None,
    trigger_set_id: str | None = None,
    trigger_set_version: str | None = None,
    regime_label: str | None = None,
) -> FuturesFillEvent:
    occurred_at = "2026-09-05T00:00:00+00:00" if action.startswith("OPEN") else "2026-09-05T01:00:00+00:00"
    return FuturesFillEvent(
        event_id=event_id,
        trade_id=trade_id,
        execution_id=f"exec-{event_id}",
        symbol="BTCUSDT",
        direction=direction,
        action=action,
        quantity=quantity,
        price=price,
        fee=fee,
        fee_asset=fee_asset,
        occurred_at=occurred_at,
        requested_price=requested_price,
        trigger_set_id=trigger_set_id,
        trigger_set_version=trigger_set_version,
        regime_label=regime_label,
    )


def _funding(
    event_id: str,
    *,
    amount: Decimal = Decimal("0.001"),
    trade_id: str | None = None,
    direction: PositionState = PositionState.LONG,
) -> FuturesFundingEvent:
    return FuturesFundingEvent(
        event_id=event_id,
        trade_id=trade_id or ("trade-long" if event_id == "f1" else "trade-1"),
        symbol="BTCUSDT",
        direction=direction,
        funding_time="2026-09-05T00:30:00+00:00",
        funding_rate=Decimal("0.0001"),
        amount=amount,
        asset="USDT",
    )
