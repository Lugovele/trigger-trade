from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

from triggertrade.accounting import ClosedTradeResult, EquitySnapshot
from triggertrade.config import load_config
from triggertrade.execution import PositionState
from triggertrade.market_data import ContractCategory, FuturesAccountState
from triggertrade.persistence import DailyLossStore, MessageStore, TradingRulesStore
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.rules import TradingRulesService
from triggertrade.services.daily_loss import DAILY_LOSS_BLOCKING_RULE, DailyLossEvaluator


def test_daily_loss_disabled_does_not_require_accounting_baseline(tmp_path):
    db = tmp_path / "daily-loss.sqlite3"
    rules = _rules(db, enabled=False)

    result = _evaluator(db).evaluate(rules_version=rules, now=_now(), account=None)

    assert result.status == "DISABLED"
    assert result.blocked is False


def test_daily_loss_uses_active_exchange_net_pnl_and_ignores_test_and_backtest_rows(tmp_path):
    db = tmp_path / "daily-loss.sqlite3"
    accounting = FuturesAccountingStore(db)
    accounting.record_equity_snapshot(_equity("eq-1", "2026-09-05T00:00:01+00:00", Decimal("100")))
    accounting.record_closed_trade(_trade("active-loss", "BTCUSDT", Decimal("-1.99"), evidence_source="exchange"))
    accounting.record_closed_trade(_trade("test-loss", "ETHUSDT", Decimal("-99"), evidence_source="test_simulation"))
    accounting.record_closed_trade(_trade("backtest-loss", "SOLUSDT", Decimal("-99"), evidence_source="BACKTEST"))

    result = _evaluator(db).evaluate(rules_version=_rules(db, pct=Decimal("0.02")), now=_now())

    assert result.blocked is False
    assert result.realized_net_pnl == Decimal("-1.99")


def test_daily_loss_baseline_ignores_non_authoritative_equity_snapshots(tmp_path):
    db = tmp_path / "daily-loss.sqlite3"
    accounting = FuturesAccountingStore(db)
    accounting.record_equity_snapshot(_equity("research-eq", "2026-09-05T00:00:01+00:00", Decimal("10"), source="test_simulation"))
    accounting.record_equity_snapshot(_equity("exchange-eq", "2026-09-05T00:00:02+00:00", Decimal("100"), source="exchange_wallet"))

    result = _evaluator(db).evaluate(rules_version=_rules(db, pct=Decimal("0.02")), now=_now())

    assert result.baseline_equity == Decimal("100")
    assert result.baseline_source == "exchange_wallet"


def test_daily_loss_blocks_at_inclusive_threshold_and_latches_with_one_message(tmp_path):
    db = tmp_path / "daily-loss.sqlite3"
    accounting = FuturesAccountingStore(db)
    accounting.record_equity_snapshot(_equity("eq-1", "2026-09-05T00:00:01+00:00", Decimal("100")))
    accounting.record_closed_trade(_trade("active-loss", "BTCUSDT", Decimal("-2"), evidence_source="ACTIVE"))
    message_store = MessageStore(db)

    evaluator = _evaluator(db, message_store=message_store)
    result = evaluator.evaluate(rules_version=_rules(db, pct=Decimal("0.02")), now=_now(), notify=True)
    repeated = evaluator.evaluate(rules_version=_rules(db, pct=Decimal("0.02")), now=_now(), notify=True)

    assert result.blocked is True
    assert result.status == "LATCHED"
    assert result.reason == DAILY_LOSS_BLOCKING_RULE
    assert repeated.blocked is True
    assert len(message_store.list_messages()) == 1
    assert message_store.list_messages()[0].title == "Daily loss limit reached"


def test_daily_loss_latch_persists_even_after_later_profit_and_resets_next_utc_day(tmp_path):
    db = tmp_path / "daily-loss.sqlite3"
    accounting = FuturesAccountingStore(db)
    accounting.record_equity_snapshot(_equity("eq-1", "2026-09-05T00:00:01+00:00", Decimal("100")))
    accounting.record_closed_trade(_trade("loss", "BTCUSDT", Decimal("-2"), closed_at="2026-09-05T01:00:00+00:00"))
    evaluator = _evaluator(db)
    rules = _rules(db, pct=Decimal("0.02"))

    assert evaluator.evaluate(rules_version=rules, now=_now()).blocked is True
    accounting.record_closed_trade(_trade("profit", "ETHUSDT", Decimal("5"), closed_at="2026-09-05T02:00:00+00:00"))

    restarted = _evaluator(db)
    assert restarted.evaluate(rules_version=rules, now=datetime(2026, 9, 5, 3, tzinfo=UTC)).blocked is True

    assert restarted.evaluate(
        rules_version=rules,
        now=datetime(2026, 9, 6, 0, 1, tzinfo=UTC),
        account=_account(Decimal("120")),
    ).blocked is False


def test_daily_loss_first_evaluation_baseline_persists_and_stricter_rules_can_block(tmp_path):
    db = tmp_path / "daily-loss.sqlite3"
    rules_loose = _rules(db, pct=Decimal("0.03"))
    rules_strict = replace(rules_loose, rules_version_id="rules-strict", draft=replace(rules_loose.draft, daily_loss_limit_pct=Decimal("0.02")))
    accounting = FuturesAccountingStore(db)
    accounting.record_closed_trade(_trade("loss", "BTCUSDT", Decimal("-2.50")))
    evaluator = _evaluator(db)

    first = evaluator.evaluate(rules_version=rules_loose, now=_now(), account=_account(Decimal("100")))
    strict = evaluator.evaluate(rules_version=rules_strict, now=_now(), account=_account(Decimal("80")))

    assert first.blocked is False
    assert first.baseline_equity == Decimal("100")
    assert strict.blocked is True
    assert strict.baseline_equity == Decimal("100")


def test_daily_loss_enabled_fails_closed_without_safe_baseline(tmp_path):
    db = tmp_path / "daily-loss.sqlite3"
    result = _evaluator(db).evaluate(rules_version=_rules(db, pct=Decimal("0.02")), now=_now(), account=None)

    assert result.blocked is True
    assert result.status == "ACCOUNTING_UNAVAILABLE"


def _evaluator(path, *, message_store=None):
    return DailyLossEvaluator(
        accounting_store=FuturesAccountingStore(path),
        daily_loss_store=DailyLossStore(path),
        message_store=message_store,
    )


def _rules(path, *, enabled: bool = True, pct: Decimal = Decimal("0.02")):
    config = load_config(
        {
            "TRIGGERTRADE_RUNTIME_DB_PATH": str(path),
            "TRIGGERTRADE_WATCHLIST": "BTCUSDT",
            "TRIGGERTRADE_RUNTIME_SYMBOL": "BTCUSDT",
        }
    )
    service = TradingRulesService(TradingRulesStore(path))
    service.ensure_initial_version(config)
    return service.create_rules_version_from_current(
        changes={"daily_loss_limit_enabled": enabled, "daily_loss_limit_pct": pct if enabled else None},
        created_source="unit",
        created_at="2026-09-05T00:00:00+00:00",
    ).rules


def _now():
    return datetime(2026, 9, 5, 13, 10, tzinfo=UTC)


def _account(equity: Decimal):
    return FuturesAccountState(
        symbol="BTCUSDT",
        category=ContractCategory.LINEAR,
        settlement_asset="USDT",
        available_margin=equity,
        equity=equity,
        wallet_balance=equity,
        configured_leverage=Decimal("1"),
        margin_mode="ISOLATED",
        position_mode="ONE_WAY",
        position_size=Decimal("0"),
    )


def _equity(snapshot_id: str, observed_at: str, equity: Decimal, *, source: str = "exchange_wallet"):
    return EquitySnapshot(
        snapshot_id=snapshot_id,
        observed_at=observed_at,
        source=source,
        wallet_balance=equity,
        equity=equity,
        available_margin=equity,
        used_margin=Decimal("0"),
        unrealized_pnl=Decimal("0"),
        realized_pnl=Decimal("0"),
        running_peak=equity,
        drawdown_absolute=Decimal("0"),
        drawdown_percent=Decimal("0"),
        max_drawdown=Decimal("0"),
    )


def _trade(trade_id: str, symbol: str, net_pnl: Decimal, *, evidence_source: str = "exchange", closed_at: str = "2026-09-05T01:00:00+00:00"):
    return ClosedTradeResult(
        trade_id=trade_id,
        symbol=symbol,
        direction=PositionState.LONG,
        quantity=Decimal("1"),
        leverage=Decimal("1"),
        entry_vwap=Decimal("100"),
        exit_vwap=Decimal("99"),
        gross_pnl=net_pnl,
        entry_fee=Decimal("0"),
        exit_fee=Decimal("0"),
        other_fees=Decimal("0"),
        funding=Decimal("0"),
        net_pnl=net_pnl,
        opened_at="2026-09-05T00:00:00+00:00",
        closed_at=closed_at,
        duration_seconds=3600,
        evidence_source=evidence_source,
    )
