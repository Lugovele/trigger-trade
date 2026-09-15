from __future__ import annotations

import pytest

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.portfolio_state import (
    CoinPortfolioState,
    CommitmentBuckets,
    PortfolioHealth,
    PortfolioState,
    PortfolioStateError,
    initial_portfolio_state,
    mark_live,
    mark_reconciling,
    mark_stale,
)


NOW = "2026-09-15T00:00:00Z"


def test_portfolio_state_models_health_and_four_commitment_buckets():
    state = PortfolioState(
        portfolio_id="portfolio-main",
        revision=1,
        health=PortfolioHealth.LIVE,
        as_of=NOW,
        evidence_id="portfolio-facts-1",
        global_buckets=CommitmentBuckets(
            held_committed_capital="1.2300",
            reserved_committed_capital="2",
            filled_committed_capital="3.000000000000",
            closing_retained_committed_capital="4",
            committed_tranches=2,
        ),
        coins=(
            CoinPortfolioState(
                symbol="btcusdt",
                buckets=CommitmentBuckets(held_committed_capital="1", committed_tranches=1),
                cooldown_until=None,
            ),
        ),
    )

    payload = state.to_payload()["portfolio_state"]

    assert payload["health"] == "LIVE"
    assert payload["global"]["held_committed_capital"] == "1.23"
    assert payload["global"]["reserved_committed_capital"] == "2"
    assert payload["global"]["filled_committed_capital"] == "3"
    assert payload["global"]["closing_retained_committed_capital"] == "4"
    assert payload["coins"][0]["symbol"] == "BTCUSDT"
    assert PortfolioState.from_payload(state.to_payload()) == state


def test_portfolio_health_transitions_preserve_unresolved_local_commitments():
    initial = PortfolioState(
        portfolio_id="portfolio-main",
        revision=1,
        health=PortfolioHealth.LIVE,
        as_of=NOW,
        evidence_id="initial",
        global_buckets=CommitmentBuckets(held_committed_capital="10", committed_tranches=1),
        coins=(CoinPortfolioState(symbol="BTCUSDT", buckets=CommitmentBuckets(held_committed_capital="10")),),
    )

    reconciling = mark_reconciling(
        state=initial,
        as_of="2026-09-15T00:01:00Z",
        evidence_id="order-event-1",
        reason_code="ORDER_EVENT_RECEIVED",
    )
    stale = mark_stale(
        state=reconciling,
        as_of="2026-09-15T00:02:00Z",
        evidence_id="portfolio-data-unavailable-1",
        reason_code="PORTFOLIO_FACTS_UNAVAILABLE",
    )
    live = mark_live(
        state=stale,
        as_of="2026-09-15T00:03:00Z",
        evidence_id="portfolio-data-confirmed-1",
    )

    assert [state.health for state in (reconciling, stale, live)] == [
        PortfolioHealth.RECONCILING,
        PortfolioHealth.STALE,
        PortfolioHealth.LIVE,
    ]
    assert [state.revision for state in (reconciling, stale, live)] == [2, 3, 4]
    assert live.global_buckets.held_committed_capital == "10"
    assert live.coins[0].buckets.held_committed_capital == "10"


def test_portfolio_state_digest_is_stable_after_round_trip_reconstruction():
    state = mark_reconciling(
        state=initial_portfolio_state(portfolio_id="portfolio-main", as_of=NOW),
        as_of="2026-09-15T00:01:00Z",
        evidence_id="order-event-1",
        reason_code="ORDER_EVENT_RECEIVED",
    )

    reconstructed = PortfolioState.from_payload(state.to_payload())

    assert canonical_json_digest(state.to_payload()) == canonical_json_digest(reconstructed.to_payload())


def test_portfolio_state_rejects_invalid_numeric_and_duplicate_coin_state():
    with pytest.raises(PortfolioStateError, match="held_committed_capital"):
        CommitmentBuckets(held_committed_capital="-1")
    with pytest.raises(PortfolioStateError, match="committed_tranches"):
        CommitmentBuckets(committed_tranches=1.5)
    with pytest.raises(PortfolioStateError, match="committed_tranches"):
        CommitmentBuckets.from_payload(
            {
                "held_committed_capital": "0",
                "reserved_committed_capital": "0",
                "filled_committed_capital": "0",
                "closing_retained_committed_capital": "0",
                "committed_tranches": 1.5,
            }
        )
    with pytest.raises(PortfolioStateError, match="revision"):
        PortfolioState(portfolio_id="portfolio-main", revision=1.5, health=PortfolioHealth.LIVE, as_of=NOW)
    fractional_revision_payload = initial_portfolio_state(portfolio_id="portfolio-main", as_of=NOW).to_payload()
    fractional_revision_payload["portfolio_state"]["revision"] = 1.5
    with pytest.raises(PortfolioStateError, match="revision"):
        PortfolioState.from_payload(fractional_revision_payload)
    with pytest.raises(PortfolioStateError, match="coin symbols must be unique"):
        PortfolioState(
            portfolio_id="portfolio-main",
            revision=1,
            health=PortfolioHealth.LIVE,
            as_of=NOW,
            coins=(CoinPortfolioState(symbol="BTCUSDT"), CoinPortfolioState(symbol="btcusdt")),
        )
