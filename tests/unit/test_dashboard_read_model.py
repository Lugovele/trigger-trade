from decimal import Decimal
import sqlite3

from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.execution import OrderStatus, OrderType, RiskDecision, Side, TradeIntent
from triggertrade.execution.service import client_order_id_for_intent
from triggertrade.persistence import (
    CandleLifecycle,
    ExecutionFill,
    ExecutionRecord,
    ExecutionStore,
    RuntimeCheckpoint,
    LaneCandleLifecycle,
    RuntimeStore,
    TraceStore,
    TriggerSetStore,
    bootstrap_current_trigger_sets,
)
from triggertrade.triggers import Signal, SignalType


def test_empty_db_view_models_are_safe(tmp_path):
    model = DashboardReadModel(tmp_path / "missing.sqlite3")

    assert model.get_latest_runtime_state().db_health == "missing_db"
    assert model.get_latest_decision().reason == "No runtime activity yet."
    assert model.list_recent_activity() == ()
    assert model.list_recent_paper_trades() == ()
    assert model.get_trace("missing") is None


def test_latest_runtime_state_and_no_signal_lifecycle(tmp_path):
    db = _empty_db(tmp_path)
    _save_no_signal(db)
    model = DashboardReadModel(db)

    state = model.get_latest_runtime_state()
    latest = model.get_latest_decision()
    activity = model.list_recent_activity()

    assert state.last_processed_candle_id == "BTCUSDT:1m:2026-09-05T12:00:00+00:00"
    assert latest.signal_type == "NO_SIGNAL"
    assert latest.strategy_result == "not evaluated"
    assert latest.risk_result == "not evaluated"
    assert activity[0].trigger_result == "NO_SIGNAL"


def test_buy_lifecycle_trade_and_full_trace(tmp_path):
    db = _empty_db(tmp_path)
    _save_buy_lifecycle(db)
    model = DashboardReadModel(db)

    latest = model.get_latest_decision()
    trades = model.list_recent_paper_trades()
    trace = model.get_trace("BTCUSDT:1m:2026-09-05T12:01:00+00:00")

    assert latest.signal_type == "BUY_CANDIDATE"
    assert latest.strategy_result == "BUY intent"
    assert latest.risk_result == "APPROVED"
    assert latest.execution_result == "filled"
    assert trades[0].fill_price == "10000.00"
    assert trace is not None
    assert trace.trigger["trigger_rule_id"] == "TRG-001"
    assert trace.signal["signal_id"] == "sig-buy"
    assert trace.strategy["strategy_rule_id"] == "STR-001"
    assert trace.trade_intent["intent_id"] == "intent-buy"
    assert trace.risk["checked_rule_ids"] == ["RSK-001", "RSK-002", "RSK-003", "RSK-004", "RSK-005"]
    assert trace.execution["status"] == "filled"
    assert len(trace.fills) == 1


def test_risk_rejection_reason_is_visible(tmp_path):
    db = _empty_db(tmp_path)
    _save_rejected_lifecycle(db)
    model = DashboardReadModel(db)

    latest = model.get_latest_decision()

    assert latest.risk_result == "REJECTED: RSK-003"
    assert "Risk blocked execution" in latest.reason


def test_missing_optional_relations_do_not_crash(tmp_path):
    db = _empty_db(tmp_path)
    RuntimeStore(db).save_lifecycle(
        CandleLifecycle(
            candle_id="BTCUSDT:1m:2026-09-05T12:03:00+00:00",
            symbol="BTCUSDT",
            timeframe="1",
            candle_open_time="2026-09-05T12:03:00+00:00",
            status="trigger_evaluated",
            signal_id="missing-signal",
        )
    )

    trace = DashboardReadModel(db).get_trace("BTCUSDT:1m:2026-09-05T12:03:00+00:00")

    assert trace is not None
    assert trace.trigger is None
    assert trace.strategy is None
    assert trace.risk is None
    assert trace.execution is None


def test_secret_like_persisted_error_is_redacted(tmp_path):
    db = _empty_db(tmp_path)
    RuntimeStore(db).save_lifecycle(
        CandleLifecycle(
            candle_id="BTCUSDT:1m:2026-09-05T12:06:00+00:00",
            symbol="BTCUSDT",
            timeframe="1",
            candle_open_time="2026-09-05T12:06:00+00:00",
            status="execution_error",
            error="BYBIT_API_SECRET=unit-signing-value",
        )
    )

    trace = DashboardReadModel(db).get_trace("BTCUSDT:1m:2026-09-05T12:06:00+00:00")

    assert trace.lifecycle["error"] == "[redacted]"


def test_paper_trades_are_constrained_to_runtime_lifecycle_executions(tmp_path):
    db = _empty_db(tmp_path)
    _save_buy_lifecycle(db)
    ExecutionStore(db).reserve(
        ExecutionRecord(
            intent_id="manual-demo-order",
            risk_decision_id="manual-risk",
            client_order_id="tt-manual",
            exchange_order_id="real-demo-order",
            symbol="BTCUSDT",
            side="Buy",
            order_type="Limit",
            requested_qty="0.001",
            requested_price="10000.00",
            status=OrderStatus.FILLED,
            created_at="2026-09-05T12:10:00+00:00",
            updated_at="2026-09-05T12:10:00+00:00",
        )
    )

    trades = DashboardReadModel(db).list_recent_paper_trades()

    assert [trade.intent_id for trade in trades] == ["intent-buy"]


def test_secrets_are_not_present_in_view_models(tmp_path):
    db = _empty_db(tmp_path)
    _save_buy_lifecycle(db)
    model = DashboardReadModel(db)
    rendered = repr((model.get_latest_runtime_state(), model.get_latest_decision(), model.list_recent_activity(), model.list_recent_paper_trades()))

    assert "BYBIT_API_SECRET" not in rendered
    assert "PASTE_YOUR" not in rendered
    assert "unit-signing-value" not in rendered


def test_transient_sqlite_lock_is_handled_safely(tmp_path):
    db = _empty_db(tmp_path)
    _save_no_signal(db)
    blocker = sqlite3.connect(db, timeout=1)
    blocker.execute("BEGIN EXCLUSIVE")
    try:
        model = DashboardReadModel(db)
        assert model.get_latest_runtime_state().db_health in {"OK", "db_unavailable"}
        assert isinstance(model.list_recent_activity(), tuple)
    finally:
        blocker.rollback()
        blocker.close()


def _empty_db(tmp_path):
    db = tmp_path / "dashboard.sqlite3"
    RuntimeStore(db)
    TraceStore(db)
    ExecutionStore(db)
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")
    return db


def _save_no_signal(db):
    signal = Signal(
        signal_id="sig-no-signal",
        trigger_rule_id="TRG-001",
        trigger_rule_version="0.1.0",
        symbol="BTCUSDT",
        observed_at="2026-09-05T12:01:00+00:00",
        window="1m",
        input_snapshot={"price_change_pct": "-0.5"},
        condition_result=False,
        signal_type=SignalType.NO_SIGNAL,
    )
    TraceStore(db).save_trigger_evaluation(signal)
    RuntimeStore(db).save_lifecycle(
        CandleLifecycle(
            candle_id="BTCUSDT:1m:2026-09-05T12:00:00+00:00",
            symbol="BTCUSDT",
            timeframe="1",
            candle_open_time="2026-09-05T12:00:00+00:00",
            status="no_signal",
            signal_id=signal.signal_id,
            processed_at="2026-09-05T12:01:01+00:00",
        )
    )
    RuntimeStore(db).checkpoint(
        RuntimeCheckpoint(
            symbol="BTCUSDT",
            timeframe="1",
            last_processed_candle_id="BTCUSDT:1m:2026-09-05T12:00:00+00:00",
            last_processed_candle_open_time="2026-09-05T12:00:00+00:00",
            last_processed_at="2026-09-05T12:01:01+00:00",
            runtime_version="paper-runtime-v1",
        )
    )


def _save_buy_lifecycle(db):
    signal = Signal(
        signal_id="sig-buy",
        trigger_rule_id="TRG-001",
        trigger_rule_version="0.1.0",
        symbol="BTCUSDT",
        observed_at="2026-09-05T12:02:00+00:00",
        window="1m",
        input_snapshot={"price_change_pct": "-2.0"},
        condition_result=True,
        signal_type=SignalType.BUY_CANDIDATE,
    )
    intent = TradeIntent(
        intent_id="intent-buy",
        strategy_rule_id="STR-001",
        strategy_rule_version="0.1.0",
        symbol="BTCUSDT",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.001"),
        price=Decimal("10000.00"),
        reason_signal_ids=(signal.signal_id,),
        reason_trigger_ids=("TRG-001",),
        created_at="2026-09-05T12:02:01+00:00",
    )
    risk = RiskDecision(
        risk_decision_id="risk-buy",
        intent_id=intent.intent_id,
        approved=True,
        checked_rule_ids=("RSK-001", "RSK-002", "RSK-003", "RSK-004", "RSK-005"),
        approved_quantity=Decimal("0.001"),
        approved_notional=Decimal("10.00000"),
        created_at="2026-09-05T12:02:02+00:00",
    )
    trace = TraceStore(db)
    trace.save_trigger_evaluation(signal)
    trace.save_strategy_decision(intent)
    trace.save_risk_decision(risk)
    client_order_id = client_order_id_for_intent(intent.intent_id)
    ExecutionStore(db).reserve(
        ExecutionRecord(
            intent_id=intent.intent_id,
            risk_decision_id=risk.risk_decision_id,
            client_order_id=client_order_id,
            exchange_order_id=f"paper-{client_order_id}",
            symbol="BTCUSDT",
            side="Buy",
            order_type="Limit",
            requested_qty="0.001",
            requested_price="10000.00",
            status=OrderStatus.FILLED,
            created_at="2026-09-05T12:02:03+00:00",
            updated_at="2026-09-05T12:02:03+00:00",
            exchange_status="Filled",
            reconciliation_state="reconciled",
        )
    )
    ExecutionStore(db).save_fill(
        ExecutionFill(
            fill_id=f"paper-fill-{client_order_id}",
            intent_id=intent.intent_id,
            client_order_id=client_order_id,
            symbol="BTCUSDT",
            side="Buy",
            quantity="0.001",
            price="10000.00",
            fee="0",
            created_at="2026-09-05T12:02:03+00:00",
        )
    )
    RuntimeStore(db).save_lifecycle(
        CandleLifecycle(
            candle_id="BTCUSDT:1m:2026-09-05T12:01:00+00:00",
            symbol="BTCUSDT",
            timeframe="1",
            candle_open_time="2026-09-05T12:01:00+00:00",
            status="completed",
            signal_id=signal.signal_id,
            intent_id=intent.intent_id,
            risk_decision_id=risk.risk_decision_id,
            execution_intent_id=intent.intent_id,
            processed_at="2026-09-05T12:02:04+00:00",
        )
    )


def _save_rejected_lifecycle(db):
    _save_buy_lifecycle(db)
    risk = RiskDecision(
        risk_decision_id="risk-rejected",
        intent_id="intent-rejected",
        approved=False,
        checked_rule_ids=("RSK-001", "RSK-002", "RSK-003", "RSK-004", "RSK-005"),
        blocking_rule_ids=("RSK-003",),
        rejection_reason="RSK-003",
        created_at="2026-09-05T12:04:00+00:00",
    )
    TraceStore(db).save_risk_decision(risk)
    RuntimeStore(db).save_lifecycle(
        CandleLifecycle(
            candle_id="BTCUSDT:1m:2026-09-05T12:04:00+00:00",
            symbol="BTCUSDT",
            timeframe="1",
            candle_open_time="2026-09-05T12:04:00+00:00",
            status="risk_rejected",
            risk_decision_id=risk.risk_decision_id,
            processed_at="2026-09-05T12:05:00+00:00",
        )
    )


def test_lane_trace_reconstructs_full_keyed_lifecycle(tmp_path):
    db = _empty_db(tmp_path)
    _save_buy_lifecycle(db)
    RuntimeStore(db).save_lane_lifecycle(
        LaneCandleLifecycle(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            candle_id="BTCUSDT:1m:2026-09-05T12:01:00+00:00",
            candle_open_time="2026-09-05T12:01:00+00:00",
            trigger_set_id="triggertrade-core",
            trigger_set_version="v1",
            status="completed",
            signal_id="sig-buy",
            intent_id="intent-buy",
            risk_decision_id="risk-buy",
            execution_intent_id="intent-buy",
            processed_at="2026-09-05T12:02:04+00:00",
        )
    )

    trace = DashboardReadModel(db).get_lane_trace(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id="BTCUSDT:1m:2026-09-05T12:01:00+00:00",
        trigger_set_id="triggertrade-core",
        trigger_set_version="v1",
    )

    assert trace is not None
    assert trace.lifecycle["lane"] == "ACTIVE"
    assert trace.lifecycle["trigger_set_id"] == "triggertrade-core"
    assert trace.trigger["trigger_rule_id"] == "TRG-001"
    assert trace.strategy["strategy_rule_id"] == "STR-001"
    assert trace.risk["risk_decision_id"] == "risk-buy"
    assert trace.execution["intent_id"] == "intent-buy"


def test_lane_trades_are_joined_through_lane_lifecycle(tmp_path):
    db = _empty_db(tmp_path)
    _save_buy_lifecycle(db)
    RuntimeStore(db).save_lane_lifecycle(
        LaneCandleLifecycle(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            candle_id="BTCUSDT:1m:2026-09-05T12:01:00+00:00",
            candle_open_time="2026-09-05T12:01:00+00:00",
            trigger_set_id="triggertrade-core",
            trigger_set_version="v1",
            status="completed",
            signal_id="sig-buy",
            intent_id="intent-buy",
            risk_decision_id="risk-buy",
            execution_intent_id="intent-buy",
            processed_at="2026-09-05T12:02:04+00:00",
        )
    )
    ExecutionStore(db).reserve(
        ExecutionRecord(
            intent_id="orphan-lane-order",
            risk_decision_id="orphan-risk",
            client_order_id="tt-orphan",
            exchange_order_id="paper-orphan",
            symbol="BTCUSDT",
            side="Buy",
            order_type="Limit",
            requested_qty="0.001",
            requested_price="10000.00",
            status=OrderStatus.FILLED,
            created_at="2026-09-05T12:10:00+00:00",
            updated_at="2026-09-05T12:10:00+00:00",
            lane="ACTIVE",
            trigger_set_id="triggertrade-core",
            trigger_set_version="v1",
        )
    )

    trades = DashboardReadModel(db).list_lane_trades("ACTIVE")

    assert [trade.intent_id for trade in trades] == ["intent-buy"]



def test_rule_detail_and_recommendations_read_model(tmp_path):
    db = tmp_path / "read_model.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")
    model = DashboardReadModel(db)

    detail = model.get_rule_detail("TRG-002", "0.1.0")

    assert detail is not None
    assert detail.rule["definition"]["logical_name"] == "TRG-VOLUME"
    assert detail.versions[0]["version"] == "0.1.0"
    assert detail.used_in_sets[0]["set_id"] == "triggertrade-core-candidate"
    assert detail.recommendations[0]["recommendation_id"] == "REC-TRG-VOLUME-001"

    recommendations = model.list_recommendations()
    assert recommendations[0].resulting_test_set == "triggertrade-core-candidate@v2-test"
    assert "No historical performance" in recommendations[0].evidence

    rec_detail = model.get_recommendation("REC-TRG-VOLUME-001")
    assert rec_detail.linked_set.version == "v2-test"
    assert rec_detail.recommendation["hypothesis"].startswith("Price moves")

    TriggerSetStore(db).transition_recommendation_status(
        recommendation_id="REC-TRG-VOLUME-001",
        status="EVALUATED",
        changed_at="2026-09-05T01:00:00+00:00",
        reason="unit regression for dashboard detail live status",
    )
    transitioned_detail = model.get_recommendation("REC-TRG-VOLUME-001")
    assert transitioned_detail.recommendation["status"] == "EVALUATED"
    assert model.list_recommendations()[0].status == "EVALUATED"
    transitioned_rule = model.get_rule_detail("TRG-002", "0.1.0")
    assert transitioned_rule.recommendations[0]["status"] == "EVALUATED"


def test_set_performance_uses_supported_counts_only(tmp_path):
    db = tmp_path / "read_model.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")

    assert DashboardReadModel(db).list_set_performance() == ()

    RuntimeStore(db).save_lane_lifecycle(
        LaneCandleLifecycle(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            candle_id="BTCUSDT:1m:2026-09-05T12:10:00+00:00",
            candle_open_time="2026-09-05T12:10:00+00:00",
            trigger_set_id="triggertrade-core",
            trigger_set_version="v1",
            status="no_signal",
            processed_at="2026-09-05T12:11:00+00:00",
        )
    )

    rows = DashboardReadModel(db).list_set_performance()

    assert len(rows) == 1
    assert rows[0].set_id == "triggertrade-core"
    assert rows[0].candles_processed == 1
    assert "P&L" in rows[0].unavailable_metrics
