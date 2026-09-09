from decimal import Decimal

from triggertrade.execution import OrderType, RiskDecision, Side, TradeIntent
import pytest

from triggertrade.persistence import TraceStore
from triggertrade.persistence.trace_store import TraceStoreError
from triggertrade.triggers import Signal, SignalType


def test_trace_store_reconstructs_signal_strategy_and_risk(tmp_path):
    store = TraceStore(tmp_path / "trace.sqlite3")
    signal = Signal(
        signal_id="sig-1",
        trigger_rule_id="TRG-001",
        trigger_rule_version="0.1.0",
        symbol="BTCUSDT",
        observed_at="2026-09-05T00:00:00+00:00",
        window="1m",
        input_snapshot={"price_change_pct": "-1.0"},
        condition_result=True,
        signal_type=SignalType.BUY_CANDIDATE,
    )
    intent = TradeIntent(
        intent_id="intent-1",
        symbol="BTCUSDT",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.0001"),
        price=Decimal("50000"),
        strategy_rule_id="STR-001",
        strategy_rule_version="0.1.0",
        reason_signal_ids=("sig-1",),
        reason_trigger_ids=("TRG-001",),
    )
    risk = RiskDecision(
        risk_decision_id="risk-1",
        intent_id="intent-1",
        approved=True,
        checked_rule_ids=("RSK-001",),
        approved_notional=Decimal("5"),
        approved_quantity=Decimal("0.0001"),
    )

    store.save_trigger_evaluation(signal)
    store.save_strategy_decision(intent)
    store.save_risk_decision(risk)

    trace = store.trace_for_intent("intent-1")

    assert trace["signals"][0]["signal_id"] == "sig-1"
    assert trace["strategy"]["strategy_rule_id"] == "STR-001"
    assert trace["risk"]["risk_decision_id"] == "risk-1"

    events = store.list_audit_events(limit=10)
    assert {event.event_type for event in events} == {"TRIGGER_EVALUATED"}
    assert events[0].entity_id == "sig-1"


def test_audit_events_are_append_only_idempotent_and_sanitized(tmp_path):
    store = TraceStore(tmp_path / "trace.sqlite3")

    first = store.record_audit_event(
        event_type="operator_action",
        source_type="user_operator",
        source_id="unit",
        scope="active",
        entity_type="operator_action",
        entity_id="pause:2026-09-08T12:00:00+00:00",
        result="success",
        reason_code="Authorization: Bearer secret-token",
        safe_metadata={"symbol": "BTCUSDT", "api_secret": "unit-secret-value"},
        created_at="2026-09-08T12:00:00+00:00",
        event_id="audit-unit-1",
    )
    second = store.record_audit_event(
        event_type="operator_action",
        source_type="user_operator",
        source_id="unit",
        scope="active",
        entity_type="operator_action",
        entity_id="pause:2026-09-08T12:00:00+00:00",
        result="success",
        reason_code="Authorization: Bearer secret-token",
        safe_metadata={"symbol": "BTCUSDT", "api_secret": "unit-secret-value"},
        created_at="2026-09-08T12:00:00+00:00",
        event_id="audit-unit-1",
    )

    assert first == second
    assert store.list_audit_events(limit=10)[0].reason_code == "[redacted]"
    assert store.list_audit_events(limit=10)[0].safe_metadata["redacted_field_1"] == "[redacted]"

    with pytest.raises(TraceStoreError, match="immutable audit event conflict"):
        store.record_audit_event(
            event_type="operator_action",
            source_type="user_operator",
            source_id="unit",
            scope="active",
            entity_type="operator_action",
            entity_id="pause:2026-09-08T12:00:00+00:00",
            result="failed",
            created_at="2026-09-08T12:00:00+00:00",
            event_id="audit-unit-1",
        )


def test_audit_event_listing_is_bounded_and_filterable(tmp_path):
    store = TraceStore(tmp_path / "trace.sqlite3")
    for index in range(300):
        store.record_audit_event(
            event_type="entry_rejected" if index % 2 else "set_evaluated",
            source_type="runtime",
            scope="active",
            entity_type="runtime_candle",
            entity_id=f"BTCUSDT:1m:2026-09-08T12:{index:03d}:00+00:00",
            result="recorded",
            created_at=f"2026-09-08T12:{index:03d}:00+00:00",
        )

    all_events = store.list_audit_events(limit=999)
    rejected = store.list_audit_events(limit=20, event_type="ENTRY_REJECTED")

    assert len(all_events) == 250
    assert len(rejected) == 20
    assert {event.event_type for event in rejected} == {"ENTRY_REJECTED"}
