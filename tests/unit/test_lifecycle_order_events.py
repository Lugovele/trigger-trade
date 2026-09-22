from __future__ import annotations

import pytest

from triggertrade.lifecycle_order_events import (
    LifecycleOrderEventError,
    build_closed_order_event_from_submission,
    build_order_event_from_submission,
    validate_order_event,
)
from tests.unit.test_lifecycle_submission_store import fake_submission_record


def test_order_event_from_submission_is_strict_v7_logical_contract():
    record = fake_submission_record(lifecycle_state="SUBMITTED", exchange_order_id="exchange-1")

    event = build_order_event_from_submission(
        record,
        event_id="order-event-1",
        occurred_at="2026-09-14T12:00:00Z",
        lifecycle_revision=1,
    )

    body = event.payload["order_event"]
    assert event.definition == "ORDER_EVENT.logical"
    assert body["contract_version"] == 7
    assert body["event_variant"] == "LOGICAL_TRANCHE"
    assert body["lifecycle_state"] == "PENDING_ENTRY"
    assert body["financial_result"] is None
    assert body["order_leg"]["client_order_link_id"] == "client-order-1"
    assert body["order_leg"]["exchange_order_id"] == "exchange-1"
    assert event.payload_digest == "90f1c88bdd4ecc0e3c6e7ff14cbab3659886659875e26c0994a9fe4bf5d6392e"


def test_order_event_rejects_unknown_field_and_invalid_revision():
    record = fake_submission_record()
    event = build_order_event_from_submission(
        record,
        event_id="order-event-1",
        occurred_at="2026-09-14T12:00:00Z",
    ).payload
    event["order_event"]["unexpected"] = "nope"

    with pytest.raises(LifecycleOrderEventError, match="unknown fields"):
        validate_order_event(event)
    with pytest.raises(LifecycleOrderEventError, match="lifecycle_revision"):
        build_order_event_from_submission(
            record,
            event_id="order-event-2",
            occurred_at="2026-09-14T12:00:00Z",
            lifecycle_revision=-1,
        )


def test_closed_order_event_requires_final_financial_result_and_terminal_predicates():
    record = fake_submission_record(lifecycle_state="SUBMITTED", exchange_order_id="exchange-1")

    event = build_closed_order_event_from_submission(
        record,
        event_id="order-event-final-1",
        financial_result=valid_financial_result(),
        occurred_at="2026-09-14T12:05:00Z",
        lifecycle_revision=7,
        cumulative_entry_filled_qty="1",
        close_commitment_quantity_basis="1",
    )

    body = event.payload["order_event"]
    assert event.definition == "ORDER_EVENT.logical"
    assert body["lifecycle_state"] == "CLOSED"
    assert body["financial_result"]["financial_state"] == "FINAL"
    assert body["financial_result"]["net_realized_result"] == "18.9"
    assert set(body["terminal_predicates"].values()) == {True}
    assert body["close_intent_active"] is False
    assert body["exposure_qty"] == "0"


def test_closed_order_event_rejects_incomplete_or_inconsistent_final_result():
    record = fake_submission_record(lifecycle_state="SUBMITTED", exchange_order_id="exchange-1")
    changed_net = valid_financial_result()
    changed_net["net_realized_result"] = "18.91"
    with pytest.raises(LifecycleOrderEventError, match="net_realized_result"):
        build_closed_order_event_from_submission(
            record,
            financial_result=changed_net,
            occurred_at="2026-09-14T12:05:00Z",
            lifecycle_revision=7,
        )

    partial_coverage = valid_financial_result()
    partial_coverage["source_coverage"]["status"] = "PARTIAL"
    with pytest.raises(LifecycleOrderEventError, match="source_coverage"):
        build_closed_order_event_from_submission(
            record,
            financial_result=partial_coverage,
            occurred_at="2026-09-14T12:05:00Z",
            lifecycle_revision=7,
        )

    balanced_high_precision = valid_financial_result()
    balanced_high_precision["gross_realized_trading_result"] = "99999999999999999999999999999"
    balanced_high_precision["actual_fees_rebates"] = "0.1"
    balanced_high_precision["allocated_funding"] = "0"
    balanced_high_precision["other_supported_exchange_costs"] = "0"
    balanced_high_precision["net_realized_result"] = "99999999999999999999999999998.9"
    build_closed_order_event_from_submission(
        record,
        financial_result=balanced_high_precision,
        occurred_at="2026-09-14T12:05:00Z",
        lifecycle_revision=7,
    )

    high_precision = valid_financial_result()
    high_precision["gross_realized_trading_result"] = "99999999999999999999999999999"
    high_precision["actual_fees_rebates"] = "0.1"
    high_precision["allocated_funding"] = "0"
    high_precision["other_supported_exchange_costs"] = "0"
    high_precision["net_realized_result"] = "100000000000000000000000000000"
    with pytest.raises(LifecycleOrderEventError, match="net_realized_result"):
        build_closed_order_event_from_submission(
            record,
            financial_result=high_precision,
            occurred_at="2026-09-14T12:05:00Z",
            lifecycle_revision=7,
        )


def valid_financial_result() -> dict[str, object]:
    return {
        "result_id": "result-1",
        "result_version": 3,
        "tranche_id": "tranche-1",
        "financial_state": "FINAL",
        "gross_realized_trading_result": "20",
        "actual_fees_rebates": "1.2",
        "allocated_funding": "0.5",
        "other_supported_exchange_costs": "0.4",
        "net_realized_result": "18.9",
        "currency": "USDT",
        "source_lineage": {
            "execution_ids": ["entry-exec-1", "exit-exec-1"],
            "cashflow_ids": ["fee-1", "funding-1"],
            "native_observation_ids": ["native-observation-1"],
            "final_closing_execution_id": "exit-exec-1",
        },
        "source_coverage": {
            "status": "COMPLETE",
            "coverage_from": "2026-09-14T12:00:00Z",
            "coverage_to": "2026-09-14T12:05:00Z",
            "missing_ranges": [],
            "pagination_complete": True,
            "next_cursor": None,
            "source_watermark_at": "2026-09-14T12:05:00Z",
            "source_finality_confirmed": True,
            "source_endpoints": ["order-management:financial-facts"],
            "reason_code": None,
        },
        "accounting_effective_at": "2026-09-14T12:04:00Z",
        "accounting_day_id": "2026-09-14/Asia-Jerusalem",
        "accounting_policy": {
            "accounting_timezone": "Asia/Jerusalem",
            "day_boundary_local": "00:00:00",
            "accounting_policy_version": "ACCOUNTING_DAY_V1",
        },
        "closed_at": "2026-09-14T12:04:30Z",
        "finalized_at": "2026-09-14T12:04:45Z",
        "terminalized_at": "2026-09-14T12:05:00Z",
        "accounting_algorithm_version": "FINAL_RESULT_V1",
        "non_funding_allocations": [],
        "numeric_policy_version": "TT_NUMERIC_V1",
    }
