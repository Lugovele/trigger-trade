from decimal import Decimal
from datetime import UTC, datetime
import sqlite3

from triggertrade.accounting import calculate_drawdown_snapshot
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
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.persistence.futures_position_store import FuturesClosedPositionRecord, FuturesPositionRecord, FuturesPositionStore
from triggertrade.persistence.operator_state_store import OperatorStateStore
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
    assert {version["version"] for version in detail.versions} >= {"0.1.0", "0.2.0"}
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


def test_set_summaries_are_backend_backed_with_exact_trigger_versions(tmp_path):
    db = tmp_path / "read_model.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")
    model = DashboardReadModel(db)

    sets = model.list_set_summaries()
    futures_active = next(row for row in sets if row.set_id == "triggertrade-futures-core" and row.version == "v1")
    futures_candidate = next(row for row in sets if row.set_id == "triggertrade-futures-candidate" and row.version == "v2-test")

    assert sets[0].status == "ACTIVE"
    assert futures_active.is_active is True
    assert tuple((row.trigger_id, row.display_name, row.version) for row in futures_active.trigger_versions) == (
        ("TRG-001", "Percentage price move", "0.2.0"),
    )
    assert ("TRG-002", "0.2.0") in tuple((row.trigger_id, row.version) for row in futures_candidate.trigger_versions)
    assert ("TRG-002", "0.1.0") not in tuple((row.trigger_id, row.version) for row in futures_candidate.trigger_versions)
    assert not futures_active.integrity_errors


def test_trigger_catalog_and_detail_are_exact_trigger_only_read_models(tmp_path):
    db = tmp_path / "read_model.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")
    model = DashboardReadModel(db)

    catalog = model.list_trigger_catalog()
    identities = {(row.trigger_id, row.version) for row in catalog}
    detail_spot = model.get_trigger_detail("TRG-002", "0.1.0")
    detail_futures = model.get_trigger_detail("TRG-002", "0.2.0")

    assert ("TRG-001", "0.1.0") in identities
    assert ("TRG-001", "0.2.0") in identities
    assert ("TRG-002", "0.1.0") in identities
    assert ("TRG-002", "0.2.0") in identities
    assert all(not row.trigger_id.startswith("STR-") and not row.trigger_id.startswith("RSK-") for row in catalog)
    assert detail_spot is not None
    assert detail_futures is not None
    assert detail_spot.version == "0.1.0"
    assert detail_futures.version == "0.2.0"
    assert detail_spot.used_in[0]["set_id"] == "triggertrade-core-candidate"
    assert detail_futures.used_in[0]["set_id"] == "triggertrade-futures-candidate"
    assert {row["version"] for row in detail_futures.version_history} == {"0.1.0", "0.2.0"}
    assert detail_futures.immutable is True
    assert any(row["name"] == "lookback_completed_candles" and row["value"] == "60" for row in detail_futures.parameters)


def test_trigger_detail_missing_exact_version_does_not_fall_back_to_latest(tmp_path):
    db = tmp_path / "read_model.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-05T00:00:00+00:00")

    assert DashboardReadModel(db).get_trigger_detail("TRG-002", "9.9.9") is None


def test_registry_integrity_reports_multiple_active_without_silent_winner(tmp_path):
    db = tmp_path / "bad_registry.sqlite3"
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE rule_definitions (
                rule_id TEXT, version TEXT, name TEXT, status TEXT, asset_scope TEXT,
                rule_type TEXT, condition TEXT, definition TEXT, created_at TEXT,
                updated_at TEXT, provenance TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE trigger_set_versions (
                set_id TEXT, version TEXT, purpose TEXT, status TEXT, symbol TEXT,
                timeframe TEXT, strategy_version TEXT, risk_profile_version TEXT,
                config_snapshot TEXT, semantic_hash TEXT, created_at TEXT, provenance TEXT
            )
            """
        )
        conn.execute(
            "CREATE TABLE trigger_set_memberships (set_id TEXT, set_version TEXT, rule_id TEXT, rule_version TEXT, position INTEGER)"
        )
        conn.executemany(
            """
            INSERT INTO trigger_set_versions (
                set_id, version, purpose, status, symbol, timeframe, strategy_version,
                risk_profile_version, config_snapshot, semantic_hash, created_at, provenance
            ) VALUES (?, ?, ?, 'ACTIVE', 'BTCUSDT', '1m', 'STR@1', 'RSK@1', '{}', ?, '2026-09-05T00:00:00+00:00', 'unit')
            """,
            (("set-a", "v1", "first", "a"), ("set-b", "v1", "second", "b")),
        )

    rows = DashboardReadModel(db).list_set_summaries()

    assert rows
    assert rows[0].integrity_errors == ("multiple ACTIVE trigger sets for BTCUSDT 1m: 2",)


def test_registry_read_models_are_empty_without_registry_tables(tmp_path):
    db = tmp_path / "empty.sqlite3"
    sqlite3.connect(db).close()
    model = DashboardReadModel(db)

    assert model.list_set_summaries() == ()
    assert model.list_trigger_catalog() == ()
    assert model.get_trigger_detail("TRG-001", "0.1.0") is None


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

def test_futures_closed_trades_are_source_separated_and_trade_detail_is_read_only(tmp_path):
    from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore

    db = _empty_db(tmp_path)
    FuturesAccountingStore(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            INSERT INTO futures_closed_trades (
                trade_id, symbol, direction, quantity, leverage, entry_vwap, exit_vwap,
                gross_pnl, entry_fee, exit_fee, other_fees, funding, net_pnl,
                opened_at, closed_at, duration_seconds, accounting_version,
                settlement_asset, contract_size, trigger_set_id, trigger_set_version,
                regime_label, entry_slippage_cost, exit_slippage_cost,
                evidence_source, simulation_model_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "trade-active-1", "BTCUSDT", "LONG", "0.010", "1", "95000", "95100",
                "1.0", "0.02", "0.02", "0", "0", "0.96",
                "2026-09-05T12:00:00+00:00", "2026-09-05T12:10:00+00:00", 600,
                "futures-accounting-v1", "USDT", "1", "triggertrade-futures-core", "v1",
                "DOWNTREND", None, None, "exchange", None,
            ),
        )
        conn.execute(
            """
            INSERT INTO futures_closed_trades (
                trade_id, symbol, direction, quantity, leverage, entry_vwap, exit_vwap,
                gross_pnl, entry_fee, exit_fee, other_fees, funding, net_pnl,
                opened_at, closed_at, duration_seconds, accounting_version,
                settlement_asset, contract_size, trigger_set_id, trigger_set_version,
                regime_label, entry_slippage_cost, exit_slippage_cost,
                evidence_source, simulation_model_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "trade-test-1", "BTCUSDT", "SHORT", "0.010", "1", "95000", "95000",
                "0", "0.02", "0.02", "0", "0", "-0.04",
                "2026-09-05T12:00:00+00:00", "2026-09-05T12:01:00+00:00", 60,
                "futures-accounting-v1", "USDT", "1", "triggertrade-futures-candidate", "v2-test",
                "SIDEWAYS", "0", "0", "test_simulation", "test-sim-v1",
            ),
        )
        for index in range(25):
            conn.execute(
                """
                INSERT INTO futures_closed_trades (
                    trade_id, symbol, direction, quantity, leverage, entry_vwap, exit_vwap,
                    gross_pnl, entry_fee, exit_fee, other_fees, funding, net_pnl,
                    opened_at, closed_at, duration_seconds, accounting_version,
                    settlement_asset, contract_size, trigger_set_id, trigger_set_version,
                    regime_label, entry_slippage_cost, exit_slippage_cost,
                    evidence_source, simulation_model_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"trade-test-newer-{index}", "BTCUSDT", "SHORT", "0.010", "1", "95000", "95000",
                    "0", "0.02", "0.02", "0", "0", "-0.04",
                    "2026-09-05T12:00:00+00:00", f"2026-09-05T13:{index:02d}:00+00:00", 60,
                    "futures-accounting-v1", "USDT", "1", "triggertrade-futures-candidate", "v2-test",
                    "SIDEWAYS", "0", "0", "test_simulation", "test-sim-v1",
                ),
            )

    model = DashboardReadModel(db)

    assert [row.trade_id for row in model.list_closed_trades_by_source("exchange", limit=1)] == ["trade-active-1"]
    assert model.list_closed_trades_by_source("test_simulation", limit=1)[0].trade_id.startswith("trade-test-newer-")
    detail = model.get_futures_trade_detail("trade-test-1")
    assert detail is not None
    assert detail["evidence_source"] == "test_simulation"
    assert detail["trigger_set"] == "triggertrade-futures-candidate@v2-test"


def test_current_futures_position_is_honest_when_no_authoritative_snapshot_exists(tmp_path):
    db = _empty_db(tmp_path)
    position = DashboardReadModel(db).get_current_futures_position()

    assert position.state == "Not available"
    assert position.direction == "Not available"
    assert position.take_profit == "Not configured"
    assert position.stop_loss == "Not configured"
    assert "no authoritative" in position.source


def test_portfolio_snapshot_uses_backend_equity_positions_and_accounting(tmp_path):
    db = _empty_db(tmp_path)
    _save_portfolio_facts(db)

    model = DashboardReadModel(db)
    snapshot = model.get_portfolio_snapshot()
    open_rows = model.list_portfolio_open_positions()
    closed_rows = model.list_portfolio_closed_positions()
    open_summary = model.get_portfolio_open_summary()
    closed_summary = model.get_portfolio_closed_summary()

    assert snapshot.total_equity == "1000"
    assert snapshot.available_capital == "910"
    assert snapshot.in_positions == "100.00"
    assert snapshot.unrealized_pnl == "4.20"
    assert snapshot.open_positions_count == 1
    assert snapshot.entries_paused is False
    assert open_summary.capital_in_open_positions == "100.00"
    assert open_rows[0].position_id == "pos-btc"
    assert open_rows[0].symbol == "BTCUSDT"
    assert open_rows[0].side == "LONG"
    assert open_rows[0].value == "100.00"
    assert open_rows[0].current_price is None
    assert open_rows[0].price_source == "MARK_UNAVAILABLE"
    assert open_rows[0].set_version == "v1"
    assert open_rows[0].rules_version_id == "rules-v1"
    assert closed_rows[0].close_reason == "TAKE_PROFIT"
    assert closed_rows[0].realized_pnl_amount == "1.20"
    assert closed_summary.closed_today_count == 1
    assert closed_summary.realized_pnl_today == "1.20"
    assert closed_summary.win_rate_today == "100.00"


def test_portfolio_filters_and_source_isolation(tmp_path):
    db = _empty_db(tmp_path)
    _save_portfolio_facts(db)
    store = FuturesPositionStore(db)
    store.save_open_position(_position_record("pos-research", "trade-research", "ETHUSDT", "SHORT", "RESEARCH_DEMO"))

    model = DashboardReadModel(db)

    assert [row.symbol for row in model.list_portfolio_open_positions(symbol="BTCUSDT")] == ["BTCUSDT"]
    assert model.list_portfolio_open_positions(symbol="ETHUSDT") == ()
    assert [row.symbol for row in model.list_portfolio_open_positions(side="LONG")] == ["BTCUSDT"]
    assert [row.close_reason for row in model.list_portfolio_closed_positions(close_reason="TAKE_PROFIT")] == ["TAKE_PROFIT"]
    assert model.list_portfolio_closed_positions(close_reason="STOP_LOSS") == ()


def test_portfolio_empty_unavailable_and_operator_pause_state_are_explicit(tmp_path):
    db = _empty_db(tmp_path)
    OperatorStateStore(db).pause(changed_at="2026-09-08T00:00:00+00:00", source="unit")

    snapshot = DashboardReadModel(db).get_portfolio_snapshot()

    assert snapshot.freshness_state == "UNAVAILABLE"
    assert snapshot.total_equity is None
    assert snapshot.available_capital is None
    assert snapshot.realized_pnl_today is None
    assert snapshot.entries_paused is True
    assert "authoritative account equity snapshot unavailable" in snapshot.data_warnings


def _save_portfolio_facts(db):
    FuturesAccountingStore(db).record_equity_snapshot(
        calculate_drawdown_snapshot(
            snapshot_id="portfolio-equity",
            observed_at=datetime.now(UTC).isoformat(),
            source="bybit_demo_account",
            wallet_balance=Decimal("1000"),
            equity=Decimal("1000"),
            available_margin=Decimal("910"),
            used_margin=Decimal("90"),
            unrealized_pnl=Decimal("4.20"),
            realized_pnl=Decimal("1.20"),
        )
    )
    store = FuturesPositionStore(db)
    store.save_open_position(_position_record("pos-btc", "trade-btc", "BTCUSDT", "LONG", "ACTIVE"))
    today = datetime.now(UTC).date().isoformat()
    store.save_closed_position(
        FuturesClosedPositionRecord(
            trade_id="trade-closed-btc",
            position_id="pos-closed-btc",
            symbol="BTCUSDT",
            direction="LONG",
            entry_vwap="100",
            exit_vwap="101.2",
            qty="1",
            position_value="100",
            leverage="1",
            planned_tp_pct="0.01",
            planned_tp_price="101",
            planned_sl_pct="0.005",
            planned_sl_price="99.5",
            realized_pnl_pct="1.20",
            gross_pnl="1.20",
            fees="0",
            funding="0",
            net_pnl="1.20",
            opened_at=f"{today}T00:00:00+00:00",
            closed_at=f"{today}T00:10:00+00:00",
            duration_seconds=600,
            close_reason="TAKE_PROFIT",
            trigger_set_id="triggertrade-futures-core",
            trigger_set_version="v1",
            strategy_rule_id="STR-FUTURES",
            strategy_rule_version="0.1.0",
            risk_rule_version="futures-position-risk-v1",
            evidence_source="ACTIVE",
            accounting_version="futures-accounting-v1",
            rules_version_id="rules-v1",
        )
    )


def _position_record(position_id: str, trade_id: str, symbol: str, side: str, evidence_source: str) -> FuturesPositionRecord:
    return FuturesPositionRecord(
        position_id=position_id,
        trade_id=trade_id,
        symbol=symbol,
        side=side,
        status="OPEN",
        opened_at=datetime.now(UTC).isoformat(),
        closed_at=None,
        entry_price="100",
        current_qty="1",
        initial_qty="1",
        leverage="1",
        position_value="100.00",
        tp_price="101",
        tp_pct="0.01",
        sl_price="99.5",
        sl_pct="0.005",
        trigger_set_id="triggertrade-futures-core",
        trigger_set_version="v1",
        strategy_rule_id="STR-FUTURES",
        strategy_rule_version="0.1.0",
        risk_rule_version="futures-position-risk-v1",
        protective_exit_version="protective-exit-v1",
        evidence_source=evidence_source,
        open_intent_id=f"intent-{position_id}",
        open_risk_decision_id=f"risk-{position_id}",
        open_execution_id=f"execution-{position_id}",
        close_intent_id=None,
        close_risk_decision_id=None,
        close_execution_id=None,
        close_reason=None,
        rule_snapshot={"rules_version_id": "rules-v1"},
        updated_at=datetime.now(UTC).isoformat(),
        rules_version_id="rules-v1",
    )
