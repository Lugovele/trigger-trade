from datetime import UTC, datetime
from decimal import Decimal

import pytest

from triggertrade.backtest import BACKTEST_EVIDENCE_SOURCE, BacktestPlan, BacktestResult, BacktestStatus
from triggertrade.persistence import (
    MessageStore,
    ResearchStore,
    ResearchStoreError,
    ResearchDemoStatus,
    TradingRulesStore,
    TriggerSetStore,
    bootstrap_current_trigger_sets,
)
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.persistence.futures_execution_store import FuturesExecutionStore
from triggertrade.persistence.runtime_store import RuntimeStore
from triggertrade.persistence.trace_store import TraceStore
from triggertrade.rules import TakeProfitMode, TradingRulesService
from triggertrade.services.research import ResearchDemoIsolation, ResearchService, ResearchServiceError
from tests.unit.test_backtest_replay import _config, _instrument, _trade_candles
from tests.unit.test_futures_performance_analytics import _fill as _accounting_fill
from triggertrade.accounting import close_futures_trade


def test_research_persists_exact_set_and_rules_pins_and_survives_restart(tmp_path):
    db, rules = _research_db(tmp_path)
    current = rules.get_current_rules_version()
    service = _service(db)

    record = service.create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=current.rules_version_id,
        created_at="2026-09-08T10:00:00+00:00",
    )
    duplicate = service.create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=current.rules_version_id,
        created_at="2026-09-08T10:01:00+00:00",
    )
    restarted = ResearchStore(db).get_research(record.research_id)

    assert duplicate.research_id == record.research_id
    assert restarted is not None
    assert restarted.set_id == "triggertrade-futures-core"
    assert restarted.set_version == "v1"
    assert restarted.rules_version_id == current.rules_version_id
    assert restarted.rules_display_version == "v1"


def test_research_rejects_latest_or_display_only_version_selectors(tmp_path):
    db, rules = _research_db(tmp_path)
    service = _service(db)

    with pytest.raises((ResearchServiceError, ResearchStoreError)):
        service.create_research(set_id="triggertrade-futures-core", set_version="latest", rules_version_id=rules.get_current_rules_version().rules_version_id)
    with pytest.raises(ResearchServiceError):
        service.create_research(set_id="triggertrade-futures-core", set_version="v1", rules_version_id="v1")


def test_research_backtest_reuses_existing_engine_and_selects_by_reference(tmp_path):
    db, rules = _research_db(tmp_path)
    service = _service(db, with_backtest_runtime=True)
    research = service.create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=rules.get_current_rules_version().rules_version_id,
    )
    candles = _trade_candles()
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)

    run = service.run_backtest(research_id=research.research_id, plan=plan, candles=candles, created_at=datetime(2026, 9, 8, 11, tzinfo=UTC))
    selected = service.select_backtest_run(research.research_id, run.run_id)

    assert run.engine_run_id is not None
    assert run.metrics["closed_trades"] >= 1
    assert selected.selected_backtest_run_id == run.run_id
    assert set(FuturesAccountingStore(db).list_closed_trades(limit=20)[0].keys()) >= {"evidence_source"}
    assert {row["evidence_source"] for row in FuturesAccountingStore(db).list_closed_trades(limit=20)} == {BACKTEST_EVIDENCE_SOURCE}
    assert ResearchStore(db).get_backtest_run(research.research_id, run.run_id).engine_run_id == run.engine_run_id


def test_research_backtest_runner_receives_pinned_rules_config(tmp_path):
    db, rules = _research_db(tmp_path)
    pinned = rules.create_rules_version_from_current(
        changes={
            "fixed_take_profit_pct": Decimal("0.017"),
            "stop_loss_pct": Decimal("0.004"),
            "minimum_net_edge_pct": Decimal("0.006"),
            "leverage": Decimal("2"),
            "maker_fee_rate": Decimal("0.0001"),
            "taker_fee_rate": Decimal("0.0004"),
        },
        created_source="unit",
    ).rules
    captured = {}

    def runner(**kwargs):
        runtime = kwargs["config"].futures_runtime
        captured["runtime_version"] = runtime.version
        captured["take_profit_pct"] = runtime.take_profit_pct
        captured["stop_loss_pct"] = runtime.stop_loss_pct
        captured["minimum_net_edge"] = runtime.minimum_net_edge
        captured["leverage"] = runtime.leverage
        captured["maker_fee_rate"] = runtime.maker_fee_rate
        captured["taker_fee_rate"] = runtime.taker_fee_rate
        return BacktestResult("engine-pinned", BacktestStatus.COMPLETED, 2, 1, 1, 1, 1, 0, 0, 0, Decimal("1"), Decimal("1"), Decimal("1"), Decimal("0"), Decimal("0"), Decimal("0"), 1, 0, {})

    service = _service(db, with_backtest_runtime=True, backtest_runner=runner)
    research = service.create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=pinned.rules_version_id,
    )
    candles = _trade_candles()
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)

    run = service.run_backtest(research_id=research.research_id, plan=plan, candles=candles)

    assert run.engine_run_id == "engine-pinned"
    assert captured == {
        "runtime_version": pinned.rules_version_id,
        "take_profit_pct": Decimal("0.017"),
        "stop_loss_pct": Decimal("0.004"),
        "minimum_net_edge": Decimal("0.006"),
        "leverage": Decimal("2"),
        "maker_fee_rate": Decimal("0.0001"),
        "taker_fee_rate": Decimal("0.0004"),
    }


def test_research_demo_start_fails_closed_without_isolation_and_dedupes_message(tmp_path):
    db, rules = _research_db(tmp_path)
    service = _service(db)
    research = service.create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=rules.get_current_rules_version().rules_version_id,
    )

    first = service.start_demo_run(research.research_id, created_at="2026-09-08T12:00:00+00:00")
    second = service.start_demo_run(research.research_id, created_at="2026-09-08T12:01:00+00:00")

    assert first.status.value == "BLOCKED"
    assert second.status.value == "BLOCKED"
    assert first.blocked_reason == "research_demo_exchange_isolation_unavailable"
    assert MessageStore(db).get_unread_message_count() == 1
    assert FuturesExecutionStore(db).unresolved() == ()


def test_dynamic_tp_and_daily_loss_rules_block_research_demo_start(tmp_path):
    db, rules = _research_db(tmp_path)
    dynamic = rules.create_rules_version_from_current(
        changes={"take_profit_mode": TakeProfitMode.DYNAMIC, "fixed_take_profit_pct": None},
        created_source="unit",
    ).rules
    dynamic_research = _service(db).create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=dynamic.rules_version_id,
    )
    dynamic_demo = _service(db).start_demo_run(dynamic_research.research_id)
    candles = _trade_candles()
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)
    dynamic_backtest = _service(db, with_backtest_runtime=True).run_backtest(
        research_id=dynamic_research.research_id,
        plan=plan,
        candles=candles,
    )

    daily = rules.create_rules_version_from_current(
        changes={
            "take_profit_mode": TakeProfitMode.FIXED,
            "fixed_take_profit_pct": Decimal("0.01"),
            "daily_loss_limit_enabled": True,
            "daily_loss_limit_pct": Decimal("0.02"),
        },
        created_source="unit",
    ).rules
    daily_research = _service(db).create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=daily.rules_version_id,
    )
    daily_demo = _service(db).start_demo_run(daily_research.research_id)

    assert dynamic_demo.blocked_reason == "dynamic_take_profit_requires_unimplemented_research_demo_runtime"
    assert dynamic_backtest.unavailable_reason == "dynamic_take_profit_requires_unimplemented_research_backtest_runtime"
    assert dynamic_backtest.engine_run_id is None
    assert daily_demo.blocked_reason == "research_daily_loss_accounting_isolation_unavailable"


def test_research_demo_stop_select_compare_and_make_active_fail_closed(tmp_path):
    db, rules = _research_db(tmp_path)
    service = _service(db, demo_isolation=ResearchDemoIsolation(available=True, execution_scope_id="research-safe", account_scope="research-account"))
    research = service.create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=rules.get_current_rules_version().rules_version_id,
    )

    running = service.start_demo_run(research.research_id, created_at="2026-09-08T12:00:00+00:00")
    stopped = service.stop_demo_run(research.research_id, running.run_id, stopped_at="2026-09-08T13:00:00+00:00")
    stopped_again = service.stop_demo_run(research.research_id, running.run_id, stopped_at="2026-09-08T14:00:00+00:00")
    selected = service.select_demo_run(research.research_id, running.run_id)
    compare = service.compare(research.research_id)
    blocked = service.request_make_active(research.research_id)

    assert stopped.status.value == "STOPPED"
    assert stopped_again.stopped_at == "2026-09-08T13:00:00+00:00"
    assert selected.selected_demo_run_id == running.run_id
    assert compare.available is False
    assert compare.reason == "selected Research Demo metrics unavailable"
    assert blocked.decision.value == "MAKE_ACTIVE_BLOCKED"
    assert blocked.made_active_at is None


def test_research_compare_available_for_selected_demo_and_active_overlap(tmp_path):
    db, rules = _research_db(tmp_path)
    service = _service(db, demo_isolation=ResearchDemoIsolation(available=True, execution_scope_id="research-safe", account_scope="research-account"))
    research = service.create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=rules.get_current_rules_version().rules_version_id,
    )
    active = close_futures_trade(
        trade_id="active-overlap",
        entry_fills=(_accounting_fill("active-entry", trade_id="active-overlap", set_id="triggertrade-futures-core", set_version="v1"),),
        exit_fills=(_accounting_fill("active-exit", trade_id="active-overlap", action="CLOSE_LONG", price=Decimal("110"), set_id="triggertrade-futures-core", set_version="v1"),),
    )
    FuturesAccountingStore(db).record_closed_trade(active)
    demo = ResearchStore(db).add_demo_run(
        research_id=research.research_id,
        status=ResearchDemoStatus.STOPPED,
        started_at="2026-09-05T00:00:00+00:00",
        stopped_at="2026-09-05T00:20:00+00:00",
        execution_scope_id="research-safe",
        account_scope="research-account",
        metrics={
            "closed_trades": [
                {
                    "trade_id": "demo-overlap",
                    "symbol": "BTCUSDT",
                    "direction": "LONG",
                    "closed_at": "2026-09-05T00:10:00+00:00",
                    "net_pnl": "0.7",
                    "gross_pnl": "1",
                    "entry_fee": "0.1",
                    "exit_fee": "0.1",
                    "other_fees": "0",
                    "funding": "0",
                    "duration_seconds": 600,
                }
            ]
        },
    )

    service.select_demo_run(research.research_id, demo.run_id)
    compare = service.compare(research.research_id)

    assert compare.available is True
    assert compare.research_demo["closed_trades"] == 1
    assert compare.active_benchmark["closed_trades"] == 1
    assert compare.difference["net_pnl"] == str(Decimal("0.7") - active.net_pnl)


def test_research_archive_preserves_evidence(tmp_path):
    db, rules = _research_db(tmp_path)
    service = _service(db, with_backtest_runtime=True)
    research = service.create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=rules.get_current_rules_version().rules_version_id,
    )
    candles = _trade_candles()
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)
    run = service.run_backtest(research_id=research.research_id, plan=plan, candles=candles)

    archived = service.archive_research(research.research_id)

    assert archived.status.value == "ARCHIVED"
    assert archived.set_id == research.set_id
    assert archived.rules_version_id == research.rules_version_id
    assert ResearchStore(db).get_backtest_run(research.research_id, run.run_id) is not None


def test_archived_research_is_immutable(tmp_path):
    db, rules = _research_db(tmp_path)
    service = _service(db, with_backtest_runtime=True, demo_isolation=ResearchDemoIsolation(available=True, execution_scope_id="research-safe", account_scope="research-account"))
    research = service.create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=rules.get_current_rules_version().rules_version_id,
    )
    candles = _trade_candles()
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)
    backtest = service.run_backtest(research_id=research.research_id, plan=plan, candles=candles)
    demo = service.start_demo_run(research.research_id)

    service.archive_research(research.research_id)

    with pytest.raises(ResearchStoreError, match="archived research is immutable"):
        service.select_backtest_run(research.research_id, backtest.run_id)
    with pytest.raises(ResearchStoreError, match="archived research is immutable"):
        service.stop_demo_run(research.research_id, demo.run_id)
    with pytest.raises(ResearchStoreError, match="archived research is immutable"):
        service.select_demo_run(research.research_id, demo.run_id)
    with pytest.raises(ResearchStoreError, match="archived research is immutable"):
        service.request_make_active(research.research_id)


def _research_db(tmp_path):
    db = tmp_path / "research.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")
    FuturesAccountingStore(db)
    FuturesExecutionStore(db)
    RuntimeStore(db)
    TraceStore(db)
    rules = TradingRulesService(TradingRulesStore(db))
    rules.ensure_initial_version(_config(db))
    return db, rules


def _service(db, *, with_backtest_runtime=False, demo_isolation=None, backtest_runner=None):
    return ResearchService(
        store=ResearchStore(db),
        trigger_set_store=TriggerSetStore(db),
        trading_rules_store=TradingRulesStore(db),
        message_store=MessageStore(db),
        config=_config(db) if with_backtest_runtime else None,
        instrument=_instrument() if with_backtest_runtime else None,
        demo_isolation=demo_isolation,
        backtest_runner=backtest_runner,
    )
