from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from triggertrade.backtest import BACKTEST_EVIDENCE_SOURCE, BacktestPlan, BacktestResult, BacktestStatus
from triggertrade.canonical_json import canonical_json_digest
from triggertrade.analytics import ENTRY_REPORT_ITEMS, ENTRY_SOURCE_ROWS, TAKE_PROFIT_REPORT_ITEMS, TAKE_PROFIT_SOURCE_ROWS
from triggertrade.persistence import (
    MessageStore,
    ResearchStore,
    ResearchStoreError,
    ResearchBacktestStatus,
    ResearchDemoStatus,
    ResearchDecision,
    ResearchStatus,
    FuturesPositionRecord,
    FuturesPositionStore,
    TradingRulesStore,
    TriggerSetStore,
    bootstrap_current_trigger_sets,
    current_futures_testing_trigger_set,
)
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.persistence.futures_execution_store import FuturesExecutionStore
from triggertrade.persistence.runtime_store import RuntimeStore
from triggertrade.persistence.trace_store import TraceStore
from triggertrade.rules import TakeProfitMode, TradingRulesService
from triggertrade.research_pins import research_pin_digest, research_pin_payload
from triggertrade.services.research import (
    ResearchDemoExecutionHandoffResult,
    ResearchDemoIsolation,
    ResearchPromotionCommand,
    ResearchService,
    ResearchServiceError,
)
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
    assert restarted.pin_digest == research_pin_digest(restarted.pin_payload)
    assert restarted.pin_payload["methodology_package_revision"] == "v1.2.15"
    assert restarted.pin_payload["config_pins"]["trigger_set"]["set_id"] == "triggertrade-futures-core"
    assert restarted.pin_payload["config_pins"]["trading_rules"]["rules_version_id"] == current.rules_version_id
    assert "MARKET_HANDOFF" in restarted.pin_payload["contract_versions"]


def test_research_pin_defaults_to_v1_2_15_and_preserves_explicit_historical_revision():
    current = research_pin_payload(config_pins={"config": "current"}, created_source="unit")
    historical = research_pin_payload(
        config_pins={"config": "historical"},
        created_source="unit",
        methodology_package_revision="v1.2.14",
    )

    assert current["methodology_package_revision"] == "v1.2.15"
    assert historical["methodology_package_revision"] == "v1.2.14"
    assert research_pin_digest(historical) != research_pin_digest(current)


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
    assert run.pin_payload["parent_research_pin_digest"] == research.pin_digest
    assert run.pin_payload["run_inputs"]["plan"]["symbol"] == "BTCUSDT"
    assert run.pin_payload["execution_pins"]["simulator_version"] == "backtest-sim-v1-next-candle"
    assert run.pin_digest == research_pin_digest(run.pin_payload)
    assert selected.selected_backtest_run_id == run.run_id
    assert set(FuturesAccountingStore(db).list_closed_trades(limit=20)[0].keys()) >= {"evidence_source"}
    assert {row["evidence_source"] for row in FuturesAccountingStore(db).list_closed_trades(limit=20)} == {BACKTEST_EVIDENCE_SOURCE}
    assert ResearchStore(db).get_backtest_run(research.research_id, run.run_id).engine_run_id == run.engine_run_id


def test_research_preserves_multiple_short_runs_without_overwriting_lineage(tmp_path):
    db, rules = _research_db(tmp_path)
    store = ResearchStore(db)
    research = _service(db).create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=rules.get_current_rules_version().rules_version_id,
    )

    first = store.add_backtest_run(
        research_id=research.research_id,
        period_start="2026-09-01T00:00:00+00:00",
        period_end="2026-09-08T00:00:00+00:00",
        timeframe="1m",
        status=ResearchBacktestStatus.COMPLETED,
        engine_run_id="engine-week-1",
        metrics={"net_pnl": "1.25", "closed_trades": 7},
        created_at="2026-09-08T00:01:00+00:00",
    )
    second = store.add_backtest_run(
        research_id=research.research_id,
        period_start="2026-09-08T00:00:00+00:00",
        period_end="2026-09-15T00:00:00+00:00",
        timeframe="1m",
        status=ResearchBacktestStatus.COMPLETED,
        engine_run_id="engine-week-2",
        metrics={"net_pnl": "-0.10", "closed_trades": 5},
        created_at="2026-09-15T00:01:00+00:00",
    )

    selected = store.select_backtest_run(research.research_id, second.run_id)
    runs = store.list_backtest_runs(research.research_id)
    by_id = {run.run_id: run for run in runs}

    assert selected.selected_backtest_run_id == second.run_id
    assert {first.run_id, second.run_id} == set(by_id)
    assert by_id[first.run_id].selected_for_use is False
    assert by_id[second.run_id].selected_for_use is True
    assert by_id[first.run_id].period_start == "2026-09-01T00:00:00+00:00"
    assert by_id[second.run_id].period_start == "2026-09-08T00:00:00+00:00"
    assert by_id[first.run_id].metrics == {"closed_trades": 7, "net_pnl": "1.25"}
    assert by_id[second.run_id].metrics == {"closed_trades": 5, "net_pnl": "-0.10"}
    assert by_id[first.run_id].pin_payload["parent_research_pin_digest"] == research.pin_digest
    assert by_id[second.run_id].pin_payload["parent_research_pin_digest"] == research.pin_digest
    assert by_id[first.run_id].pin_digest == research_pin_digest(by_id[first.run_id].pin_payload)
    assert by_id[second.run_id].pin_digest == research_pin_digest(by_id[second.run_id].pin_payload)
    assert by_id[first.run_id].pin_digest != by_id[second.run_id].pin_digest


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


def test_research_pin_replay_ignores_later_current_rules_changes(tmp_path):
    db, rules = _research_db(tmp_path)
    original = rules.get_current_rules_version()
    service = _service(db, with_backtest_runtime=True)
    research = service.create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=original.rules_version_id,
    )
    replacement = rules.create_rules_version_from_current(
        changes={"fixed_take_profit_pct": Decimal("0.018")},
        created_source="unit",
    ).rules
    _set_current_rules(db, replacement.rules_version_id)
    candles = _trade_candles()
    plan = BacktestPlan("BTCUSDT", "linear", "1m", candles[60].close_time, candles[-2].close_time)

    restarted = ResearchStore(db).get_research(research.research_id)
    run = service.run_backtest(research_id=research.research_id, plan=plan, candles=candles)

    assert restarted is not None
    assert restarted.pin_digest == research.pin_digest
    assert restarted.pin_payload["config_pins"]["trading_rules"]["rules_version_id"] == original.rules_version_id
    assert restarted.pin_payload["config_pins"]["trading_rules"]["rules_version_id"] != replacement.rules_version_id
    assert run.pin_payload["parent_research_pin_digest"] == research.pin_digest
    assert run.pin_digest == research_pin_digest(run.pin_payload)


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
    assert first.pin_payload["parent_research_pin_digest"] == research.pin_digest
    assert first.pin_payload["execution_pins"]["live_side_effects"] == "forbidden"
    assert first.pin_digest == research_pin_digest(first.pin_payload)
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


def test_research_demo_rejects_unattributed_or_live_like_isolation_scopes(tmp_path):
    db, rules = _research_db(tmp_path)
    research = _service(db).create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=rules.get_current_rules_version().rules_version_id,
    )
    missing_state = _service(
        db,
        demo_isolation=ResearchDemoIsolation(
            available=True,
            execution_scope_id="research-safe",
            account_scope="research-account",
            adapter_scope_id="research-demo-paper",
        ),
    ).start_demo_run(research.research_id)
    live_scope = _service(
        db,
        demo_isolation=ResearchDemoIsolation(
            available=True,
            execution_scope_id="research-safe",
            account_scope="live",
            adapter_scope_id="research-demo-paper",
            state_scope_id="research-demo-state",
        ),
    ).start_demo_run(research.research_id)

    assert missing_state.status is ResearchDemoStatus.BLOCKED
    assert missing_state.blocked_reason == "research_demo_isolation_scope_unattributed"
    assert live_scope.status is ResearchDemoStatus.BLOCKED
    assert live_scope.blocked_reason == "research_demo_live_side_effect_scope_forbidden"
    assert FuturesExecutionStore(db).unresolved() == ()


def test_research_demo_safe_isolation_still_requires_canonical_handoff(tmp_path):
    db, rules = _research_db(tmp_path)
    research = _service(db).create_research(
        set_id="triggertrade-futures-core",
        set_version="v1",
        rules_version_id=rules.get_current_rules_version().rules_version_id,
    )

    demo = _service(
        db,
        demo_isolation=_safe_demo_isolation(),
        demo_execution_handoff=False,
    ).start_demo_run(research.research_id, created_at="2026-09-08T12:00:00+00:00")

    assert demo.status is ResearchDemoStatus.BLOCKED
    assert demo.blocked_reason == "research_demo_canonical_execution_handoff_unavailable"
    assert ResearchStore(db).get_research(research.research_id).status is ResearchStatus.BLOCKED
    assert FuturesExecutionStore(db).unresolved() == ()


def test_research_demo_stop_select_compare_and_make_active_requests_canonical_governance(tmp_path):
    db, rules = _research_db(tmp_path)
    governance = _FakePromotionGovernanceStore()
    service = _service(db, demo_isolation=_safe_demo_isolation(), promotion_governance_store=governance)
    pinned_rules = rules.create_rules_version_from_current(
        changes={"fixed_take_profit_pct": Decimal("0.017")},
        created_source="unit",
    ).rules
    previous_rules = pinned_rules.created_from_version_id
    _set_current_rules(db, previous_rules)
    research = service.create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=pinned_rules.rules_version_id,
    )

    running = service.start_demo_run(research.research_id, created_at="2026-09-08T12:00:00+00:00")
    stopped = service.stop_demo_run(research.research_id, running.run_id, stopped_at="2026-09-08T13:00:00+00:00")
    stopped_again = service.stop_demo_run(research.research_id, running.run_id, stopped_at="2026-09-08T14:00:00+00:00")
    selected = service.select_demo_run(research.research_id, running.run_id)
    compare = service.compare(research.research_id)
    requested = service.request_make_active(research.research_id, command=_promotion_command("promote-main"))
    pair = TriggerSetStore(db).get_active_trading_pair("BTCUSDT", "1m")
    idempotent = service.request_make_active(research.research_id, command=_promotion_command("promote-main"))
    promotion_message = next(
        message for message in MessageStore(db).list_messages() if message.dedupe_key == f"research:{research.research_id}:promotion_requested"
    )

    assert running.status is ResearchDemoStatus.RUNNING
    assert running.execution_scope_id == "research-safe"
    assert running.account_scope == "research-account"
    assert running.pin_payload["execution_pins"]["adapter_scope_id"] == "research-demo-paper"
    assert running.pin_payload["execution_pins"]["state_scope_id"] == "research-demo-state"
    assert running.pin_payload["execution_pins"]["live_side_effects"] == "forbidden"
    assert stopped.status.value == "STOPPED"
    assert stopped_again.stopped_at == "2026-09-08T13:00:00+00:00"
    assert selected.selected_demo_run_id == running.run_id
    assert compare.available is False
    assert compare.reason == "selected Research Demo metrics unavailable"
    assert requested.decision is ResearchDecision.PROMOTION_REQUESTED
    assert requested.made_active_at is None
    assert requested.promoted_set_id is None
    assert requested.promoted_set_version is None
    assert requested.promoted_rules_version_id is None
    assert requested.previous_active_set_id == "triggertrade-futures-core"
    assert requested.previous_active_set_version == "v1"
    assert requested.previous_rules_version_id == previous_rules
    assert pair is not None
    assert pair.trigger_set.set_id == "triggertrade-futures-core"
    assert pair.trigger_set.version == "v1"
    assert pair.rules_version.rules_version_id == previous_rules
    assert TriggerSetStore(db).get_set("triggertrade-futures-core", "v1").status.value == "ACTIVE"
    assert idempotent.made_active_at is None
    assert idempotent.promotion_result_metadata == requested.promotion_result_metadata
    assert MessageStore(db).get_unread_message_count() == 2
    assert promotion_message.severity.value == "ATTENTION"
    assert promotion_message.title == "Research promotion requested"
    assert "Active configuration was not changed" in promotion_message.body
    assert promotion_message.entity_type == "research"
    assert promotion_message.entity_id == research.research_id
    assert promotion_message.source == "research_service"
    assert promotion_message.metadata == {
        "canonical_request_id": "research-promotion:promote-main",
        "command_idempotency_key": "promote-main",
    }
    assert governance.requests["research-promotion:promote-main"]["research_promotion_request"]["target"] == {
        "set_id": "triggertrade-futures-candidate",
        "set_version": "v2-test",
        "rules_version_id": pinned_rules.rules_version_id,
        "rules_display_version": pinned_rules.version,
        "rules_config_hash": pinned_rules.config_hash,
    }
    audit_types = {event.event_type for event in TraceStore(db).list_audit_events(limit=20, entity_id=research.research_id)}
    assert {
        "RESEARCH_CREATED",
        "DEMO_RUN_STARTED",
        "DEMO_RUN_STOPPED",
        "DEMO_SELECTED_FOR_USE",
        "RESEARCH_PROMOTION_OPERATOR_COMMAND",
        "RESEARCH_PROMOTION_REQUESTED",
    }.issubset(audit_types)
    requested_audit = TraceStore(db).list_audit_events(limit=10, event_type="RESEARCH_PROMOTION_REQUESTED")[0]
    assert requested_audit.set_id == "triggertrade-futures-candidate"
    assert requested_audit.set_version == "v2-test"
    assert requested_audit.rules_version_id == pinned_rules.rules_version_id
    assert requested_audit.safe_metadata["operator_principal"] == "unit-operator"
    assert requested_audit.safe_metadata["command_idempotency_key"] == "promote-main"


def test_make_active_requires_operator_command_and_selected_evidence(tmp_path):
    db, rules = _research_db(tmp_path)
    service = _service(db)
    candidate_rules = rules.create_rules_version_from_current(changes={"fixed_take_profit_pct": Decimal("0.026")}, created_source="unit").rules
    research = service.create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=candidate_rules.rules_version_id,
    )

    with pytest.raises(ResearchServiceError, match="legacy SQLite research promotion is compatibility-only"):
        service.make_active(research.research_id)

    blocked = service.request_make_active(research.research_id, command=_promotion_command("promote-no-evidence"))

    assert blocked.decision is ResearchDecision.MAKE_ACTIVE_BLOCKED
    assert blocked.made_active_at is None
    assert TraceStore(db).list_audit_events(event_type="RESEARCH_PROMOTION_OPERATOR_COMMAND")[0].source_id == "unit-operator"
    blocked_message = next(
        message
        for message in MessageStore(db).list_messages()
        if message.dedupe_key == f"research:{research.research_id}:make_active_blocked:research_promotion_requires_selected_evidence"
    )
    assert blocked_message.metadata == {"reason": "research_promotion_requires_selected_evidence"}


def test_make_active_blocks_running_demo_without_changing_pair(tmp_path):
    db, rules = _research_db(tmp_path)
    service = _service(db, demo_isolation=_safe_demo_isolation())
    original_rules = rules.get_current_rules_version()
    new_rules = rules.create_rules_version_from_current(changes={"fixed_take_profit_pct": Decimal("0.018")}, created_source="unit").rules
    _set_current_rules(db, original_rules.rules_version_id)
    research = service.create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=new_rules.rules_version_id,
    )
    service.start_demo_run(research.research_id, created_at="2026-09-08T12:00:00+00:00")

    blocked = service.request_make_active(research.research_id, command=_promotion_command("promote-running-demo"))
    pair = TriggerSetStore(db).get_active_trading_pair("BTCUSDT", "1m")
    blocked_message = next(
        message
        for message in MessageStore(db).list_messages()
        if message.dedupe_key == f"research:{research.research_id}:make_active_blocked:research_demo_must_be_stopped_before_promotion"
    )

    assert blocked.decision is ResearchDecision.MAKE_ACTIVE_BLOCKED
    assert blocked.made_active_at is None
    assert blocked_message.severity.value == "WARNING"
    assert blocked_message.title == "Research promotion blocked"
    assert "did not change the active configuration" in blocked_message.body
    assert blocked_message.entity_type == "research"
    assert blocked_message.entity_id == research.research_id
    assert blocked_message.source == "research_service"
    assert blocked_message.metadata == {"reason": "research_demo_must_be_stopped_before_promotion"}
    assert pair is not None
    assert pair.trigger_set.set_id == "triggertrade-futures-core"
    assert pair.trigger_set.version == "v1"
    assert pair.rules_version.rules_version_id == original_rules.rules_version_id


def test_make_active_rolls_back_if_promotion_fails_mid_transaction(tmp_path):
    db, rules = _research_db(tmp_path)
    service = _service(db, legacy_sqlite_promotion_enabled=True)
    original_rules = rules.get_current_rules_version()
    new_rules = rules.create_rules_version_from_current(changes={"fixed_take_profit_pct": Decimal("0.019")}, created_source="unit").rules
    _set_current_rules(db, original_rules.rules_version_id)
    research = service.create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=new_rules.rules_version_id,
    )
    _select_stopped_demo_evidence(service, research.research_id)

    with pytest.raises(ResearchServiceError, match="injected promotion failure"):
        service.make_active(research.research_id, command=_promotion_command("promote-fault-rules"), _fault_after="rules")

    pair = TriggerSetStore(db).get_active_trading_pair("BTCUSDT", "1m")
    reloaded = ResearchStore(db).get_research(research.research_id)

    assert pair is not None
    assert pair.trigger_set.set_id == "triggertrade-futures-core"
    assert pair.trigger_set.version == "v1"
    assert pair.rules_version.rules_version_id == original_rules.rules_version_id
    assert TriggerSetStore(db).get_set("triggertrade-futures-candidate", "v2-test").status.value == "TESTING"
    assert reloaded.decision is ResearchDecision.NONE


def test_make_active_rolls_back_if_set_update_fails_mid_transaction(tmp_path):
    db, rules = _research_db(tmp_path)
    service = _service(db, legacy_sqlite_promotion_enabled=True)
    original_rules = rules.get_current_rules_version()
    candidate_rules = rules.create_rules_version_from_current(changes={"fixed_take_profit_pct": Decimal("0.020")}, created_source="unit").rules
    _set_current_rules(db, original_rules.rules_version_id)
    research = service.create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=candidate_rules.rules_version_id,
    )
    _select_stopped_demo_evidence(service, research.research_id)

    with pytest.raises(ResearchServiceError, match="injected promotion failure"):
        service.make_active(research.research_id, command=_promotion_command("promote-fault-set"), _fault_after="set")

    pair = TriggerSetStore(db).get_active_trading_pair("BTCUSDT", "1m")
    reloaded = ResearchStore(db).get_research(research.research_id)

    assert pair is not None
    assert pair.trigger_set.set_id == "triggertrade-futures-core"
    assert pair.trigger_set.version == "v1"
    assert pair.rules_version.rules_version_id == original_rules.rules_version_id
    assert TriggerSetStore(db).get_set("triggertrade-futures-candidate", "v2-test").status.value == "TESTING"
    assert reloaded.decision is ResearchDecision.NONE


def test_make_active_does_not_rewrite_existing_open_positions(tmp_path):
    db, rules = _research_db(tmp_path)
    original_rules = rules.get_current_rules_version()
    position = FuturesPositionRecord(
        position_id="pos-existing",
        trade_id="trade-existing",
        symbol="BTCUSDT",
        side="LONG",
        status="OPEN",
        opened_at="2026-09-08T11:00:00+00:00",
        closed_at=None,
        entry_price="100",
        current_qty="0.01",
        initial_qty="0.01",
        leverage="1",
        position_value="1",
        tp_price="101",
        tp_pct="0.01",
        sl_price="99",
        sl_pct="0.01",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
        strategy_rule_id="STR-FUT-001",
        strategy_rule_version="0.1.0",
        risk_rule_version="0.1.0",
        protective_exit_version="protective-exit-v1",
        evidence_source="ACTIVE",
        open_intent_id="intent-existing",
        open_risk_decision_id="risk-existing",
        open_execution_id="exec-existing",
        close_intent_id=None,
        close_risk_decision_id=None,
        close_execution_id=None,
        close_reason=None,
        rule_snapshot={"rules_version_id": original_rules.rules_version_id},
        updated_at="2026-09-08T11:00:00+00:00",
        rules_version_id=original_rules.rules_version_id,
    )
    FuturesPositionStore(db).save_open_position(position)
    candidate_rules = rules.create_rules_version_from_current(changes={"fixed_take_profit_pct": Decimal("0.022")}, created_source="unit").rules
    _set_current_rules(db, original_rules.rules_version_id)
    research = _service(db).create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=candidate_rules.rules_version_id,
    )
    _select_stopped_demo_evidence(_service(db), research.research_id)

    _service(db, promotion_governance_store=_FakePromotionGovernanceStore()).request_make_active(
        research.research_id,
        command=_promotion_command("promote-open-position-safe"),
    )
    reloaded = FuturesPositionStore(db).get_position("pos-existing")

    assert reloaded.trigger_set_id == "triggertrade-futures-core"
    assert reloaded.trigger_set_version == "v1"
    assert reloaded.rules_version_id == original_rules.rules_version_id
    assert reloaded.tp_price == "101"
    assert reloaded.sl_price == "99"


def test_make_active_survives_restart_and_blocks_unknown_or_unsupported_rules(tmp_path):
    db, rules = _research_db(tmp_path)
    original_rules = rules.get_current_rules_version()
    candidate_rules = rules.create_rules_version_from_current(changes={"fixed_take_profit_pct": Decimal("0.023")}, created_source="unit").rules
    dynamic_rules = rules.create_rules_version_from_current(
        changes={"take_profit_mode": TakeProfitMode.DYNAMIC, "fixed_take_profit_pct": None},
        created_source="unit",
    ).rules
    _set_current_rules(db, original_rules.rules_version_id)
    service = _service(db, promotion_governance_store=_FakePromotionGovernanceStore())
    with pytest.raises(ResearchServiceError, match="research id not found"):
        service.request_make_active("res-unknown", command=_promotion_command("promote-unknown"))
    dynamic_research = service.create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=dynamic_rules.rules_version_id,
    )
    blocked = service.request_make_active(dynamic_research.research_id, command=_promotion_command("promote-dynamic-blocked"))
    research = service.create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=candidate_rules.rules_version_id,
    )
    _select_stopped_demo_evidence(service, research.research_id)

    requested = service.request_make_active(research.research_id, command=_promotion_command("promote-restart"))
    restarted_pair = TriggerSetStore(db).get_active_trading_pair("BTCUSDT", "1m")
    restarted_research = ResearchStore(db).get_research(research.research_id)

    assert blocked.decision is ResearchDecision.MAKE_ACTIVE_BLOCKED
    assert blocked.made_active_at is None
    assert blocked.promotion_result_metadata == {}
    assert requested.decision is ResearchDecision.PROMOTION_REQUESTED
    assert restarted_pair is not None
    assert restarted_pair.trigger_set.version == "v1"
    assert restarted_pair.rules_version.rules_version_id == original_rules.rules_version_id
    assert restarted_research.made_active_at is None
    assert restarted_research.promotion_result_metadata["result"] == "promotion_requested"


def test_concurrent_make_active_requests_leave_one_coherent_pair(tmp_path):
    db, rules = _research_db(tmp_path)
    original_rules = rules.get_current_rules_version()
    candidate_rules = rules.create_rules_version_from_current(changes={"fixed_take_profit_pct": Decimal("0.021")}, created_source="unit").rules
    _set_current_rules(db, original_rules.rules_version_id)
    research = _service(db).create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=candidate_rules.rules_version_id,
    )
    _select_stopped_demo_evidence(_service(db), research.research_id)

    def promote():
        return _service(db, promotion_governance_store=_FakePromotionGovernanceStore()).request_make_active(
            research.research_id,
            command=_promotion_command("promote-concurrent-same"),
        ).decision.value

    with ThreadPoolExecutor(max_workers=2) as pool:
        decisions = tuple(pool.map(lambda _: promote(), range(2)))

    pair = TriggerSetStore(db).get_active_trading_pair("BTCUSDT", "1m")
    messages = MessageStore(db).list_messages()

    assert decisions == ("PROMOTION_REQUESTED", "PROMOTION_REQUESTED")
    assert pair is not None
    assert pair.trigger_set.set_id == "triggertrade-futures-core"
    assert pair.trigger_set.version == "v1"
    assert pair.rules_version.rules_version_id == original_rules.rules_version_id
    assert sum(1 for message in messages if message.dedupe_key == f"research:{research.research_id}:promotion_requested") == 1


def test_concurrent_different_research_promotions_leave_one_exact_pair(tmp_path):
    db, rules = _research_db(tmp_path)
    store = TriggerSetStore(db)
    alt = replace(current_futures_testing_trigger_set(created_at="2026-09-08T12:00:00+00:00"), set_id="triggertrade-futures-alt", version="v3-test")
    store.create_set(alt)
    original_rules = rules.get_current_rules_version()
    first_rules = rules.create_rules_version_from_current(changes={"fixed_take_profit_pct": Decimal("0.024")}, created_source="unit").rules
    second_rules = rules.create_rules_version_from_current(changes={"fixed_take_profit_pct": Decimal("0.025")}, created_source="unit").rules
    _set_current_rules(db, original_rules.rules_version_id)
    first = _service(db).create_research(
        set_id="triggertrade-futures-candidate",
        set_version="v2-test",
        rules_version_id=first_rules.rules_version_id,
    )
    second = _service(db).create_research(
        set_id=alt.set_id,
        set_version=alt.version,
        rules_version_id=second_rules.rules_version_id,
    )
    _select_stopped_demo_evidence(_service(db), first.research_id)
    _select_stopped_demo_evidence(_service(db), second.research_id)

    def promote(research_id):
        return _service(db, promotion_governance_store=_FakePromotionGovernanceStore()).request_make_active(
            research_id,
            command=_promotion_command(f"promote-concurrent-{research_id[-8:]}"),
        ).decision.value

    with ThreadPoolExecutor(max_workers=2) as pool:
        decisions = tuple(pool.map(promote, (first.research_id, second.research_id)))

    pair = TriggerSetStore(db).get_active_trading_pair("BTCUSDT", "1m")
    active_sets = [item for item in TriggerSetStore(db).list_sets() if item.status.value == "ACTIVE" and item.symbol == "BTCUSDT"]

    assert decisions == ("PROMOTION_REQUESTED", "PROMOTION_REQUESTED")
    assert pair is not None
    assert pair.trigger_set.set_id == "triggertrade-futures-core"
    assert pair.trigger_set.version == "v1"
    assert pair.rules_version.rules_version_id == original_rules.rules_version_id
    assert len(active_sets) == 1


def test_research_compare_available_for_selected_demo_and_active_overlap(tmp_path):
    db, rules = _research_db(tmp_path)
    service = _service(db, demo_isolation=_safe_demo_isolation())
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


def test_research_service_publishes_complete_read_only_entry_and_tp_reports(tmp_path):
    db, _rules = _research_db(tmp_path)
    store = ResearchStore(db)
    dataset, _ = store.archive_diagnostic_dataset(
        dataset_id="diag-report-source-1",
        source_payload=_diagnostic_report_source_payload(),
        source_provenance={
            "source_kind": "SUPPLIED_DIAGNOSTIC_DATASET",
            "retrieved_at": "2026-09-15T00:00:00Z",
        },
        manifest={
            "dataset_kind": "B12_RESEARCH_REPORT_SOURCE",
            "symbols": ["BTCUSDT"],
            "timeframe": "1m",
        },
    )
    service = _service(db)

    entry = service.publish_entry_diagnostic_report(
        report_id="entry-report-service-1",
        dataset_id=dataset.dataset_id,
        report_config={
            "report_definition_version": "ENTRY_REPORT_V1",
            "distance_bands": [{"lower": "0.10", "upper": "0.50"}],
        },
        created_at="2026-09-15T00:01:00Z",
    )
    tp = service.publish_take_profit_diagnostic_report(
        report_id="tp-report-service-1",
        dataset_id=dataset.dataset_id,
        report_config={
            "report_definition_version": "TP_REPORT_V1",
            "minimum_distance_alternatives": ["1.25"],
            "maximum_distance_alternatives": ["3.00"],
        },
        created_at="2026-09-15T00:02:00Z",
    )
    replay = service.publish_entry_diagnostic_report(
        report_id="entry-report-service-1",
        dataset_id=dataset.dataset_id,
        report_config={
            "report_definition_version": "ENTRY_REPORT_V1",
            "distance_bands": [{"lower": "0.10", "upper": "0.50"}],
        },
        created_at="2026-09-15T00:03:00Z",
    )

    assert replay == entry
    assert tuple(entry.report_definition["items"]) == ENTRY_REPORT_ITEMS
    assert tuple(entry.report_definition["source_rows"]) == ENTRY_SOURCE_ROWS
    assert tuple(tp.report_definition["items"]) == TAKE_PROFIT_REPORT_ITEMS
    assert tuple(tp.report_definition["source_rows"]) == TAKE_PROFIT_SOURCE_ROWS
    assert set(entry.report_payload["availability"]) == set(ENTRY_REPORT_ITEMS)
    assert set(tp.report_payload["availability"]) == set(TAKE_PROFIT_REPORT_ITEMS)
    assert entry.report_payload["outputs"]["ENTRY-RPT-04"]["ratio"] == {"numerator": "100", "denominator": "51"}
    assert entry.report_payload["outputs"]["ENTRY-RPT-13"]["mean"] == {
        "numerator": str(10 * 10**18),
        "denominator": str(2 * 10**18),
    }
    assert entry.report_payload["outputs"]["ENTRY-RPT-14"]["path_extrema"] == {
        "adverse_numerator": str(2 * 10**18),
        "favorable_numerator": str(12 * 10**18),
        "denominator": str(10**18),
    }
    assert tp.report_payload["outputs"]["TP-RPT-14"]["report_config"]["minimum_distance_alternatives"] == ["1.25"]
    assert tp.report_payload["outputs"]["TP-RPT-14"]["sensitivity"] == {
        "status": "AVAILABLE",
        "axis": "minimum_distance",
        "results": [{"alternative": "1.25", "selected_count": "1", "candidate_count": "2"}],
    }
    assert tp.report_payload["outputs"]["TP-RPT-15"]["sensitivity"] == {
        "status": "AVAILABLE",
        "axis": "maximum_distance",
        "results": [{"alternative": "3.00", "selected_count": "0", "candidate_count": "1"}],
    }
    assert entry.report_payload["canonical_feedback"] is False
    assert tp.report_payload["canonical_feedback"] is False
    assert entry.dataset_manifest_digest == dataset.manifest_digest
    assert tp.dataset_manifest_digest == dataset.manifest_digest
    assert ResearchStore(db).list_diagnostic_reports() == (entry, tp)


def test_research_service_report_assembly_rejects_incomplete_or_mutated_sources(tmp_path):
    db, _rules = _research_db(tmp_path)
    source = _diagnostic_report_source_payload()
    source["entry_report"]["source_rows"].pop("E19")
    dataset, _ = ResearchStore(db).archive_diagnostic_dataset(
        dataset_id="diag-report-source-incomplete",
        source_payload=source,
        source_provenance={
            "source_kind": "SUPPLIED_DIAGNOSTIC_DATASET",
            "retrieved_at": "2026-09-15T00:00:00Z",
        },
        manifest={
            "dataset_kind": "B12_RESEARCH_REPORT_SOURCE",
            "symbols": ["BTCUSDT"],
            "timeframe": "1m",
        },
    )

    with pytest.raises(ValueError, match="missing required entries"):
        _service(db).publish_entry_diagnostic_report(
            report_id="entry-report-incomplete",
            dataset_id=dataset.dataset_id,
        )


def test_research_service_report_assembly_rejects_binary_float_source_values(tmp_path):
    db, _rules = _research_db(tmp_path)
    source = _diagnostic_report_source_payload()
    source["entry_report"]["source_rows"]["E18"]["path"]["anchor_price"] = 100.0
    with pytest.raises(Exception, match="binary floats"):
        ResearchStore(db).archive_diagnostic_dataset(
            dataset_id="diag-report-source-float",
            source_payload=source,
            source_provenance={
                "source_kind": "SUPPLIED_DIAGNOSTIC_DATASET",
                "retrieved_at": "2026-09-15T00:00:00Z",
            },
            manifest={
                "dataset_kind": "B12_RESEARCH_REPORT_SOURCE",
                "symbols": ["BTCUSDT"],
                "timeframe": "1m",
            },
        )


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
    service = _service(db, with_backtest_runtime=True, demo_isolation=_safe_demo_isolation())
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
        service.request_make_active(research.research_id, command=_promotion_command("promote-archived"))


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


def _service(
    db,
    *,
    with_backtest_runtime=False,
    demo_isolation=None,
    demo_execution_handoff=None,
    backtest_runner=None,
    promotion_governance_store=None,
    legacy_sqlite_promotion_enabled=False,
):
    if demo_execution_handoff is None and demo_isolation is not None:
        demo_execution_handoff = _FakeResearchDemoExecutionHandoff()
    elif demo_execution_handoff is False:
        demo_execution_handoff = None
    return ResearchService(
        store=ResearchStore(db),
        trigger_set_store=TriggerSetStore(db),
        trading_rules_store=TradingRulesStore(db),
        message_store=MessageStore(db),
        config=_config(db) if with_backtest_runtime else None,
        instrument=_instrument() if with_backtest_runtime else None,
        demo_isolation=demo_isolation,
        demo_execution_handoff=demo_execution_handoff,
        backtest_runner=backtest_runner,
        promotion_governance_store=promotion_governance_store,
        legacy_sqlite_promotion_enabled=legacy_sqlite_promotion_enabled,
    )


def _diagnostic_report_source_payload():
    entry_rows = {
        row: {
            "status": "AVAILABLE",
            "member_ids": [f"{row.lower()}-member"],
            "report_items": [ENTRY_REPORT_ITEMS[index % len(ENTRY_REPORT_ITEMS)]],
            "basis": {"source": row},
        }
        for index, row in enumerate(ENTRY_SOURCE_ROWS)
    }
    tp_rows = {
        row: {
            "status": "AVAILABLE",
            "member_ids": [f"{row.lower()}-member"],
            "report_items": [TAKE_PROFIT_REPORT_ITEMS[index % len(TAKE_PROFIT_REPORT_ITEMS)]],
            "basis": {"source": row},
        }
        for index, row in enumerate(TAKE_PROFIT_SOURCE_ROWS)
    }
    entry_rows["E19"]["report_items"].append("ENTRY-RPT-15")
    entry_rows["E07"]["report_items"].append("ENTRY-RPT-04")
    entry_rows["E07"]["ratio"] = {"numerator": "100", "denominator": "51"}
    entry_rows["E17"]["report_items"].append("ENTRY-RPT-13")
    entry_rows["E17"]["values"] = ["18.9", "-8.9"]
    entry_rows["E18"]["report_items"].append("ENTRY-RPT-14")
    entry_rows["E18"]["path"] = {"direction": "LONG", "anchor_price": "100", "prices": ["100", "98", "105", "110", "112", "109"]}
    entry_rows["E19"]["report_items"].append("ENTRY-RPT-14")
    entry_rows["E19"]["path"] = {"direction": "SHORT", "anchor_price": "100", "prices": ["100", "102", "95", "90", "88", "91"]}
    tp_rows["T16"]["report_items"].append("TP-RPT-14")
    tp_rows["T16"]["baseline_distances"] = ["1.0", "1.5"]
    tp_rows["T17"]["report_items"].append("TP-RPT-15")
    tp_rows["T17"]["baseline_distances"] = ["3.5"]
    return {
        "entry_report": {
            "source_rows": entry_rows,
            "outputs": {
                item: {
                    "status": "AVAILABLE" if index % 2 == 0 else "UNAVAILABLE",
                    "basis": {"source_rows": [ENTRY_SOURCE_ROWS[index % len(ENTRY_SOURCE_ROWS)]]},
                }
                for index, item in enumerate(ENTRY_REPORT_ITEMS)
            },
        },
        "take_profit_report": {
            "source_rows": tp_rows,
            "outputs": {
                item: {
                    "status": "AVAILABLE" if index % 2 == 0 else "INCOMPLETE",
                    "basis": {"source_rows": [TAKE_PROFIT_SOURCE_ROWS[index % len(TAKE_PROFIT_SOURCE_ROWS)]]},
                }
                for index, item in enumerate(TAKE_PROFIT_REPORT_ITEMS)
            },
        },
    }


class _FakePromotionGovernanceStore:
    def __init__(self) -> None:
        self.requests = {}

    def request_promotion(self, *, request_id, payload, research_id, idempotency_key):
        inserted = request_id not in self.requests
        stored_payload = self.requests.setdefault(request_id, payload)
        digest = canonical_json_digest(stored_payload)
        return SimpleNamespace(
            request_id=request_id,
            state=SimpleNamespace(payload=stored_payload, payload_digest=digest),
            outbox=SimpleNamespace(message_id=request_id, payload_digest=digest),
            inserted=inserted,
        )


class _FakeResearchDemoExecutionHandoff:
    canonical_worker_handoff = True

    def __init__(self) -> None:
        self.requests = []

    def start_research_demo(self, *, research, trigger_set, rules, isolation, started_at, pin_payload, demo_run_id):
        self.requests.append(
            {
                "demo_run_id": demo_run_id,
                "research_id": research.research_id,
                "set_id": trigger_set.set_id,
                "set_version": trigger_set.version,
                "rules_version_id": rules.rules_version_id,
                "execution_scope_id": isolation.execution_scope_id,
                "started_at": started_at,
                "pin_digest": canonical_json_digest(pin_payload),
            }
        )
        return ResearchDemoExecutionHandoffResult(
            handoff_id=f"research-demo-handoff:{research.research_id}:{started_at}",
            execution_owner="trading-worker",
            durable=True,
        )


def _safe_demo_isolation() -> ResearchDemoIsolation:
    return ResearchDemoIsolation(
        available=True,
        execution_scope_id="research-safe",
        account_scope="research-account",
        adapter_scope_id="research-demo-paper",
        state_scope_id="research-demo-state",
    )


def _promotion_command(idempotency_key: str) -> ResearchPromotionCommand:
    return ResearchPromotionCommand(
        operator_principal="unit-operator",
        authorization_source="unit-test-operator-auth",
        idempotency_key=idempotency_key,
    )


def _select_stopped_demo_evidence(service: ResearchService, research_id: str) -> None:
    run = ResearchStore(service._store.path).add_demo_run(
        research_id=research_id,
        status=ResearchDemoStatus.STOPPED,
        started_at="2026-09-08T12:00:00+00:00",
        stopped_at="2026-09-08T13:00:00+00:00",
        execution_scope_id="research-safe",
        account_scope="research-account",
        metrics={},
    )
    service.select_demo_run(research_id, run.run_id)


def _set_current_rules(db, rules_version_id: str) -> None:
    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE trading_rules_current SET rules_version_id = ?, updated_at = ? WHERE scope = ?",
            (rules_version_id, "2026-09-08T12:30:00+00:00", "LIVE"),
        )
