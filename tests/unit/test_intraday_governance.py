from decimal import Decimal
from datetime import UTC, datetime
from http import HTTPStatus
from http.client import HTTPConnection
import re
import threading

import pytest

from triggertrade.config import ExecutionVenue, load_config
from triggertrade.execution import ExecutionError, ExecutionService, OrderType, RiskDecision, Side, TradeIntent
from triggertrade.governance import (
    EvidenceCapability,
    EvidenceReadiness,
    GovernanceEvidence,
    GovernancePolicy,
    RecommendationAction,
    evaluate_readiness,
)
from triggertrade.market_data import BybitInstrument
from triggertrade.persistence import (
    ExecutionStore,
    OperatorStateStore,
    RuntimeStore,
    TraceStore,
    TriggerSetStore,
    TradingState,
    bootstrap_current_trigger_sets,
)
from triggertrade.services.dual_lane_runtime import DualLaneRuntime
from triggertrade.execution import PaperExecutionAdapter
from tests.unit.test_dual_lane_runtime import VolumeConfirmedMarketClient, _runtime


def test_empty_evidence_is_collecting_and_does_not_promote():
    result = evaluate_readiness(_evidence(signals=0, closed=None, closed_capability=EvidenceCapability.UNAVAILABLE))

    assert result.readiness is EvidenceReadiness.COLLECTING
    assert result.recommendation_action is RecommendationAction.CONTINUE_TEST
    assert "closed trade accounting unavailable" in result.evidence_gaps


def test_partial_evidence_extends_sample():
    result = evaluate_readiness(_evidence(age_days=3, signals=31, closed=12))

    assert result.readiness is EvidenceReadiness.EARLY
    assert result.recommendation_action is RecommendationAction.EXTEND_SAMPLE
    assert any("31 / 100" in gap for gap in result.evidence_gaps)
    assert result.remaining_trades_to_gate == 38


def test_gates_met_are_review_ready_not_auto_promotion():
    result = evaluate_readiness(_evidence(age_days=7, signals=100, closed=50))

    assert result.readiness is EvidenceReadiness.REVIEW_READY
    assert result.recommendation_action is RecommendationAction.READY_FOR_PROMOTION_REVIEW


def test_strong_evidence_is_separate_from_lifecycle_status():
    result = evaluate_readiness(_evidence(age_days=14, signals=200, closed=100))

    assert result.readiness is EvidenceReadiness.STRONG_EVIDENCE
    assert result.recommendation_action is RecommendationAction.READY_FOR_PROMOTION_REVIEW


def test_blocker_and_missing_regime_behavior_are_explicit():
    result = evaluate_readiness(_evidence(critical_failures=1))

    assert result.readiness is EvidenceReadiness.BLOCKED
    assert result.regime_coverage == "unavailable"
    assert "regime diversity unavailable" not in result.blocking_reasons

    strict = evaluate_readiness(_evidence(), GovernancePolicy(regime_diversity_required=True))
    assert strict.readiness is EvidenceReadiness.BLOCKED
    assert "regime diversity unavailable" in strict.blocking_reasons


def test_create_new_version_requires_explicit_evidence_flag():
    result = evaluate_readiness(_evidence(age_days=2, signals=10, closed=2, new_version_recommended=True))

    assert result.recommendation_action is RecommendationAction.CREATE_NEW_VERSION


def test_operator_pause_default_persistence_and_resume(tmp_path):
    db = tmp_path / "operator.sqlite3"
    store = OperatorStateStore(db)

    assert store.get_trading_state().state is TradingState.TRADING_ENABLED
    paused = store.pause(changed_at="2026-09-05T01:00:00+00:00", reason="unit pause")

    assert paused.state is TradingState.TRADING_PAUSED
    assert OperatorStateStore(db).get_trading_state().state is TradingState.TRADING_PAUSED
    resumed = OperatorStateStore(db).resume(changed_at="2026-09-05T01:05:00+00:00")
    assert resumed.state is TradingState.TRADING_ENABLED
    assert len(OperatorStateStore(db).audit_rows()) == 2


def test_active_execution_blocked_while_paused_but_reconciliation_continues(tmp_path):
    db = tmp_path / "orders.sqlite3"
    operator = OperatorStateStore(db)
    operator.pause(changed_at="2026-09-05T01:00:00+00:00")
    adapter = CountingPaperAdapter()
    service = _execution_service(
        db,
        adapter=adapter,
        operator_state=lambda: operator.get_trading_state().state.value,
        lane="ACTIVE",
    )

    with pytest.raises(ExecutionError, match="operator pause"):
        service.submit_approved_limit_order(intent=_intent(), risk_decision=_risk())

    assert adapter.create_calls == 0
    record = ExecutionStore(db).reserve(_execution_record())[0]
    assert service.reconcile(record).status.value == "filled"


def test_test_lane_execution_gate_is_not_blocked_by_operator_pause(tmp_path):
    db = tmp_path / "orders.sqlite3"
    operator = OperatorStateStore(db)
    operator.pause(changed_at="2026-09-05T01:00:00+00:00")
    adapter = CountingPaperAdapter()
    service = _execution_service(
        db,
        adapter=adapter,
        operator_state=lambda: operator.get_trading_state().state.value,
        lane="TEST",
    )

    service.submit_approved_limit_order(intent=_intent(), risk_decision=_risk())

    assert adapter.create_calls == 1


def test_dual_lane_pause_blocks_active_execution_but_test_continues(tmp_path):
    db = tmp_path / "dual.sqlite3"
    operator = OperatorStateStore(db)
    operator.pause(changed_at="2026-09-05T01:00:00+00:00")
    runtime = _runtime_with_operator(tmp_path, db, operator)

    result = runtime.process_once()

    assert result.active[0].skipped_reason == "operator_paused"
    assert result.test[0].execution_status == "test_recorded"
    test = RuntimeStore(db).get_lane_lifecycle(
        lane="TEST",
        symbol="BTCUSDT",
        timeframe="1m",
        candle_id=result.candle_id,
        trigger_set_id="triggertrade-core-candidate",
        trigger_set_version="v2-test",
    )
    assert test.status == "test_recorded"


def test_paused_runtime_checkpoints_active_and_test_continues_next_candle(tmp_path):
    db = tmp_path / "dual.sqlite3"
    operator = OperatorStateStore(db)
    operator.pause(changed_at="2026-09-05T01:00:00+00:00")
    first = _runtime_with_operator(tmp_path, db, operator)
    first_result = first.process_once()

    second = _runtime_with_operator(
        tmp_path,
        db,
        operator,
        market_client=TwoCompletedVolumeConfirmedMarketClient(),
        clock=lambda: datetime(2026, 9, 5, 13, 2, 30, tzinfo=UTC),
    )
    second_result = second.process_once()

    assert first_result.active[0].skipped_reason == "operator_paused"
    assert second_result.candle_id == "BTCUSDT:1m:2026-09-05T13:01:00+00:00"
    assert second_result.active[0].skipped_reason == "operator_paused"
    assert second_result.test[0].execution_status == "test_recorded"
    checkpoint = RuntimeStore(db).get_lane_checkpoint(
        lane="ACTIVE",
        symbol="BTCUSDT",
        timeframe="1m",
        trigger_set_id="triggertrade-core",
        trigger_set_version="v1",
    )
    assert checkpoint.last_processed_candle_id == second_result.candle_id


def test_resume_does_not_execute_old_paused_candle(tmp_path):
    db = tmp_path / "dual.sqlite3"
    operator = OperatorStateStore(db)
    operator.pause(changed_at="2026-09-05T01:00:00+00:00")
    _runtime_with_operator(tmp_path, db, operator).process_once()
    operator.resume(changed_at="2026-09-05T01:10:00+00:00")
    adapter = PaperExecutionAdapter(clock_ms=lambda: 789)
    runtime = _runtime_with_operator(tmp_path, db, operator, active_adapter=adapter)

    result = runtime.process_once()

    assert result.active[0].skipped_reason == "already_processed"
    assert adapter.create_calls == 0


def test_dashboard_readiness_and_pause_controls_render(tmp_path):
    from triggertrade.dashboard.__main__ import render_dashboard
    from triggertrade.dashboard.read_model import DashboardReadModel

    db = tmp_path / "dashboard.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db), created_at="2026-09-01T00:00:00+00:00")
    html = render_dashboard(DashboardReadModel(db), initial_page="analytics")

    assert "TEST SET EVIDENCE" in html
    assert "COLLECTING" in html or "EARLY" in html
    assert "closed trade accounting unavailable" in html
    assert "STOP TRADING" in html
    assert "Stop new trades?" in html
    assert "BYBIT_API_SECRET" not in html


def test_dashboard_pause_resume_requires_confirmation_and_persists(tmp_path):
    from triggertrade.dashboard.__main__ import create_server

    db = tmp_path / "dashboard.sqlite3"
    bootstrap_current_trigger_sets(TriggerSetStore(db))
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("POST", "/operator/pause", body="confirm=no", headers={"Content-Type": "application/x-www-form-urlencoded"})
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.BAD_REQUEST
        assert OperatorStateStore(db).get_trading_state().state is TradingState.TRADING_ENABLED

        conn.request("GET", "/")
        response = conn.getresponse()
        html = response.read().decode("utf-8")
        assert response.status == HTTPStatus.OK
        token = _operator_token(html)

        conn.request("POST", "/operator/pause", body="confirm=yes", headers={"Content-Type": "application/x-www-form-urlencoded"})
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.BAD_REQUEST
        assert OperatorStateStore(db).get_trading_state().state is TradingState.TRADING_ENABLED

        conn.request("POST", "/operator/pause", body=f"confirm=yes&token={token}", headers={"Content-Type": "application/x-www-form-urlencoded"})
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.SEE_OTHER
        assert OperatorStateStore(db).get_trading_state().state is TradingState.TRADING_PAUSED

        conn.request("POST", "/operator/resume", body=f"confirm=yes&token={token}", headers={"Content-Type": "application/x-www-form-urlencoded"})
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.SEE_OTHER
        assert OperatorStateStore(db).get_trading_state().state is TradingState.TRADING_ENABLED
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_test_no_intent_reason_is_not_critical_governance_failure(tmp_path):
    from triggertrade.dashboard.read_model import DashboardReadModel

    db = tmp_path / "runtime.sqlite3"
    runtime = _runtime(tmp_path, closes=("100", "98"), path=db)
    result = runtime.process_once()

    assert result.test[0].skipped_reason == "volume_not_confirmed"
    row = DashboardReadModel(db).list_test_set_evidence()[0]
    assert row.readiness != EvidenceReadiness.BLOCKED.value
    assert "volume_not_confirmed" not in row.blocking_reasons


def _evidence(
    *,
    age_days=0,
    signals=0,
    closed=0,
    closed_capability=EvidenceCapability.AVAILABLE,
    critical_failures=0,
    new_version_recommended=False,
):
    return GovernanceEvidence(
        testing_started_at="2026-09-05T00:00:00+00:00",
        age_days=age_days,
        signals_observed=signals,
        closed_trades_observed=closed,
        closed_trades_capability=closed_capability,
        regime_coverage=None,
        regime_capability=EvidenceCapability.UNAVAILABLE,
        baseline_comparison_available=True,
        critical_failures=critical_failures,
        new_version_recommended=new_version_recommended,
    )


def _operator_token(html: str) -> str:
    match = re.search(r"name='token' value='([^']+)'", html)
    assert match is not None
    return match.group(1)


def _runtime_with_operator(tmp_path, db, operator, *, market_client=None, clock=None, active_adapter=None):
    env = {
        "TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.LOCAL_PAPER.value,
        "TRIGGERTRADE_WATCHLIST": "BTCUSDT",
        "TRIGGERTRADE_RUNTIME_SYMBOL": "BTCUSDT",
        "TRIGGERTRADE_CANDLE_INTERVAL": "1",
        "TRIGGERTRADE_POLL_INTERVAL_SECONDS": "1",
        "TRIGGERTRADE_STALE_AFTER_SECONDS": "120",
    }
    config = load_config(env)
    trigger_sets = TriggerSetStore(db)
    bootstrap_current_trigger_sets(trigger_sets)
    return DualLaneRuntime(
        config=config,
        market_client=market_client or VolumeConfirmedMarketClient(),
        execution_store=ExecutionStore(db),
        trace_store=TraceStore(db),
        runtime_store=RuntimeStore(db),
        trigger_set_store=trigger_sets,
        operator_state_store=operator,
        active_adapter=active_adapter or PaperExecutionAdapter(clock_ms=lambda: 123),
        test_adapter_factory=lambda: PaperExecutionAdapter(clock_ms=lambda: 456),
        clock=clock or (lambda: datetime(2026, 9, 5, 13, 1, 30, tzinfo=UTC)),
        logger=lambda message: None,
    )


def _execution_service(db, *, adapter, operator_state, lane):
    return ExecutionService(
        config=load_config({"TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.LOCAL_PAPER.value}),
        adapter=adapter,
        store=ExecutionStore(db),
        instrument=BybitInstrument(
            symbol="BTCUSDT",
            base_coin="BTC",
            quote_coin="USDT",
            price_tick=Decimal("0.01"),
            quantity_step=Decimal("0.000001"),
            min_order_quantity=Decimal("0.00001"),
            min_order_amount=Decimal("5"),
        ),
        available_quote_balance=Decimal("100"),
        execution_lane=lane,
        operator_trading_state=operator_state,
    )


def _intent():
    return TradeIntent(
        intent_id="intent-1",
        symbol="BTCUSDT",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.001"),
        price=Decimal("10000.00"),
    )


def _risk():
    return RiskDecision(
        "risk-1",
        "intent-1",
        True,
        checked_rule_ids=("RSK-001", "RSK-002", "RSK-003", "RSK-004", "RSK-005"),
        approved_quantity=Decimal("0.001"),
        approved_notional=Decimal("10.00000"),
    )


def _execution_record():
    from triggertrade.execution import OrderStatus
    from triggertrade.persistence import ExecutionRecord

    return ExecutionRecord(
        intent_id="intent-1",
        risk_decision_id="risk-1",
        client_order_id="tt-intent-1",
        exchange_order_id=None,
        symbol="BTCUSDT",
        side="Buy",
        order_type="Limit",
        requested_qty="0.001",
        requested_price="10000.00",
        status=OrderStatus.SUBMITTED,
        created_at="2026-09-05T00:00:00+00:00",
        updated_at="2026-09-05T00:00:00+00:00",
    )


class CountingPaperAdapter(PaperExecutionAdapter):
    def create_limit_order(self, **kwargs):
        return super().create_limit_order(**kwargs)


class TwoCompletedVolumeConfirmedMarketClient(VolumeConfirmedMarketClient):
    def recent_candles(self, symbol, interval, limit):
        from tests.unit.test_dual_lane_runtime import _volume_candle
        from tests.unit.test_paper_runtime import FakeResponse
        from datetime import timedelta

        rows = []
        for i in range(60):
            rows.append(_volume_candle(self.start + timedelta(minutes=i), "100", "1"))
        rows.append(_volume_candle(self.start + timedelta(minutes=60), "98", "2"))
        rows.append(_volume_candle(self.start + timedelta(minutes=61), "96", "2"))
        rows.append(_volume_candle(self.start + timedelta(minutes=62), "96", "1"))
        return FakeResponse({"list": list(reversed(rows))})
