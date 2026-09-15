from __future__ import annotations

from triggertrade.portfolio_state import (
    CommitmentBuckets,
    PortfolioHealth,
    PortfolioState,
    mark_reconciling,
)


def test_portfolio_state_payload_has_approved_health_and_bucket_shape():
    state = mark_reconciling(
        state=PortfolioState(
            portfolio_id="portfolio-main",
            revision=7,
            health=PortfolioHealth.LIVE,
            as_of="2026-09-15T00:00:00Z",
            evidence_id="portfolio-data-confirmed-1",
            global_buckets=CommitmentBuckets(
                held_committed_capital="1",
                reserved_committed_capital="2",
                filled_committed_capital="3",
                closing_retained_committed_capital="4",
                committed_tranches=4,
            ),
        ),
        as_of="2026-09-15T00:01:00Z",
        evidence_id="order-event-1",
        reason_code="ORDER_EVENT_RECEIVED",
    )

    payload = state.to_payload()

    assert set(payload) == {"portfolio_state"}
    assert payload["portfolio_state"] == {
        "portfolio_id": "portfolio-main",
        "revision": 8,
        "health": "RECONCILING",
        "as_of": "2026-09-15T00:01:00Z",
        "reason_code": "ORDER_EVENT_RECEIVED",
        "evidence_id": "order-event-1",
        "global": {
            "held_committed_capital": "1",
            "reserved_committed_capital": "2",
            "filled_committed_capital": "3",
            "closing_retained_committed_capital": "4",
            "committed_tranches": 4,
        },
        "coins": [],
    }
