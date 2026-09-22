from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.contracts import parse_contract
from triggertrade.contracts.bindings import validate_contract_edge
from triggertrade.persistence import (
    DurableMessageStore,
    PortfolioGrantDecisionConflict,
    PortfolioGrantDecisionStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.portfolio_grants import PortfolioGrantError, PortfolioGrantPolicy, PortfolioGrantStatus, evaluate_portfolio_grant
from triggertrade.portfolio_state import CoinPortfolioState, CommitmentBuckets, PortfolioHealth, PortfolioState
from tests.unit.test_capital_grants import NOW, approved_decision, venue_facts


def test_b8b_allowed_grant_uses_floor_sequence_and_does_not_reserve_capital():
    state = portfolio_state(
        global_held="100",
        coin_held="248.9",
        global_tranches=1,
        coin_tranches=1,
    )
    policy = policy_for(coin_allocation_cap="1000", max_positions_per_coin=4)

    evaluation = evaluate_portfolio_grant(
        grant_decision_id="grant-decision-1",
        capital_grant_id="grant-1",
        approved_decision=approved_decision(),
        portfolio_state=state,
        policy=policy,
        venue_facts=venue_facts(),
        as_of=NOW,
    )

    assert evaluation.status is PortfolioGrantStatus.ALLOWED
    assert evaluation.evaluated_reasons == ("ALLOWED",)
    assert evaluation.capital_grant is not None
    grant = evaluation.capital_grant.to_payload()["capital_and_limits"]
    assert grant["requested_capital_per_tranche"] == "250.366666666666"
    assert grant["remaining_coin_capital"] == "751.1"
    assert grant["remaining_coin_slots"] == 3
    assert state.global_buckets.held_committed_capital == "100"
    assert state.coins[0].buckets.held_committed_capital == "248.9"
    parsed = parse_contract("CAPITAL_AND_LIMITS", evaluation.capital_grant.to_payload())
    validate_contract_edge(
        producer="Portfolio",
        consumer="Position",
        contract_type="CAPITAL_AND_LIMITS",
        payload=parsed.to_payload(),
        definition="CAPITAL_AND_LIMITS",
    )


def test_b8b_retains_multiple_blocked_gate_reasons_without_grant():
    evaluation = evaluate_portfolio_grant(
        grant_decision_id="grant-decision-1",
        capital_grant_id="grant-1",
        approved_decision=approved_decision(),
        portfolio_state=portfolio_state(global_held="560", coin_held="400", global_tranches=1, coin_tranches=0),
        policy=policy_for(global_position_cap="600", coin_allocation_cap="500", minimum_tranche_capital="100", max_positions_per_coin=2),
        venue_facts=venue_facts(),
        as_of=NOW,
    )

    assert evaluation.status is PortfolioGrantStatus.BLOCKED
    assert evaluation.primary_reason == "MINIMUM_TRANCHE_CAPITAL_NOT_MET"
    assert evaluation.evaluated_reasons == (
        "MINIMUM_TRANCHE_CAPITAL_NOT_MET",
        "INSUFFICIENT_GLOBAL_CAPITAL_FOR_TRANCHE",
    )
    assert evaluation.capital_grant is None
    payload = evaluation.to_payload()["portfolio_grant_decision"]
    assert payload["gate_results"]["minimum_tranche_capital"]["calculated"] == "50"
    assert payload["gate_results"]["global_capital"]["configured"] == "40"


def test_b8b_unavailable_state_is_distinct_from_blocked():
    evaluation = evaluate_portfolio_grant(
        grant_decision_id="grant-decision-1",
        capital_grant_id="grant-1",
        approved_decision=approved_decision(),
        portfolio_state=portfolio_state(health=PortfolioHealth.RECONCILING),
        policy=policy_for(),
        venue_facts=venue_facts(),
        as_of=NOW,
    )

    assert evaluation.status is PortfolioGrantStatus.UNAVAILABLE
    assert evaluation.primary_reason == "PORTFOLIO_STATE_UNAVAILABLE"
    assert evaluation.capital_grant is None


def test_b8b_blocks_nonpositive_qcapital_candidate_without_grant():
    evaluation = evaluate_portfolio_grant(
        grant_decision_id="grant-decision-1",
        capital_grant_id="grant-1",
        approved_decision=approved_decision(),
        portfolio_state=portfolio_state(coin_held="499.9999999999999"),
        policy=policy_for(minimum_tranche_capital="0", coin_allocation_cap="500", max_positions_per_coin=2),
        venue_facts=venue_facts(),
        as_of=NOW,
    )

    assert evaluation.status is PortfolioGrantStatus.BLOCKED
    assert evaluation.primary_reason == "MINIMUM_TRANCHE_CAPITAL_NOT_MET"
    assert evaluation.gate_results["minimum_tranche_capital"]["calculated"] == "0"
    assert evaluation.capital_grant is None


def test_b8b_hard_cap_breach_diagnostics_are_not_clamped_to_zero():
    evaluation = evaluate_portfolio_grant(
        grant_decision_id="grant-decision-1",
        capital_grant_id="grant-1",
        approved_decision=approved_decision(),
        portfolio_state=portfolio_state(global_held="1100", coin_held="600"),
        policy=policy_for(global_position_cap="1000", coin_allocation_cap="500"),
        venue_facts=venue_facts(),
        as_of=NOW,
    )

    assert evaluation.status is PortfolioGrantStatus.BLOCKED
    assert evaluation.gate_results["coin_allocation"]["calculated"] == "-100"
    assert evaluation.gate_results["grant_candidate"]["status"] == "UNAVAILABLE"
    assert evaluation.capital_grant is None


def test_b8b_zero_remaining_slots_blocks_without_grant():
    evaluation = evaluate_portfolio_grant(
        grant_decision_id="grant-decision-1",
        capital_grant_id="grant-1",
        approved_decision=approved_decision(),
        portfolio_state=portfolio_state(global_tranches=4, coin_tranches=2),
        policy=policy_for(max_open_positions=4, max_positions_per_coin=2),
        venue_facts=venue_facts(),
        as_of=NOW,
    )

    assert evaluation.status is PortfolioGrantStatus.BLOCKED
    assert evaluation.evaluated_reasons == (
        "MAX_OPEN_POSITIONS_REACHED",
        "MAX_COIN_POSITIONS_REACHED",
    )
    assert evaluation.capital_grant is None


def test_b8b_rejects_rejected_initial_decision_and_missing_venue_facts():
    rejected = approved_decision()
    rejected["position_decision"]["decision"] = "REJECT"
    with pytest.raises(PortfolioGrantError, match="APPROVE"):
        evaluate_portfolio_grant(
            grant_decision_id="grant-decision-1",
            capital_grant_id="grant-1",
            approved_decision=rejected,
            portfolio_state=portfolio_state(),
            policy=policy_for(),
            venue_facts=venue_facts(),
            as_of=NOW,
        )

    facts = venue_facts()
    del facts["fees"]
    with pytest.raises(PortfolioGrantError, match="fees"):
        evaluate_portfolio_grant(
            grant_decision_id="grant-decision-1",
            capital_grant_id="grant-1",
            approved_decision=approved_decision(),
            portfolio_state=portfolio_state(),
            policy=policy_for(),
            venue_facts=facts,
            as_of=NOW,
        )


def test_b8b_grant_preserves_valid_target_sum_above_global_cap_configuration():
    evaluation = evaluate_portfolio_grant(
        grant_decision_id="grant-decision-1",
        capital_grant_id="grant-1",
        approved_decision=approved_decision(),
        portfolio_state=portfolio_state(
            global_held="0",
            coin_held="0",
            extra_symbols=("ETHUSDT", "SOLUSDT", "XRPUSDT"),
        ),
        policy=policy_for(global_position_cap="600", coin_allocation_cap="200", max_positions_per_coin=2),
        venue_facts=venue_facts(),
        as_of=NOW,
    )

    assert evaluation.status is PortfolioGrantStatus.ALLOWED
    assert evaluation.capital_grant is not None
    grant = evaluation.capital_grant.to_payload()["capital_and_limits"]
    assert grant["relevant_portfolio_limits"]["global_position_cap"] == "600"
    assert grant["relevant_portfolio_limits"]["coin_allocation_cap"] == "200"
    assert grant["requested_capital_per_tranche"] == "100"


pytest.importorskip("psycopg")


def test_b8b_store_persists_allowed_replays_and_publishes_non_reserving_grant(monkeypatch):
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = PortfolioGrantDecisionStore(uow.connection)
            record, inserted = store.evaluate_and_record(
                grant_decision_id="grant-decision-1",
                capital_grant_id="grant-1",
                approved_decision=approved_decision(),
                portfolio_state=portfolio_state(global_held="100", coin_held="248.9", global_tranches=1, coin_tranches=1),
                policy=policy_for(coin_allocation_cap="1000", max_positions_per_coin=4),
                venue_facts=venue_facts(),
                as_of=NOW,
            )
            assert inserted is True
            replayed, inserted = store.evaluate_and_record(
                grant_decision_id="grant-decision-1",
                capital_grant_id="grant-1",
                approved_decision=approved_decision(),
                portfolio_state=portfolio_state(global_held="999", coin_held="999", global_tranches=3, coin_tranches=3),
                policy=policy_for(coin_allocation_cap="1000", max_positions_per_coin=4, minimum_tranche_capital="999"),
                venue_facts=venue_facts(),
                as_of=NOW,
            )
            assert inserted is False
            assert replayed.payload_digest == record.payload_digest
            assert replayed.capital_grant is not None
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id="grant-1")
            assert outbox is not None
            assert outbox.message_type == "CAPITAL_AND_LIMITS"
            assert outbox.producer == "Portfolio"
            assert outbox.consumer == "Position"
            assert _outbox_count(uow.connection, message_id="grant-1") == 1
            race_store = PortfolioGrantDecisionStore(uow.connection)
            original_get = race_store._owner_state.get
            get_calls = {"count": 0}

            def stale_first_get(*args, **kwargs):
                get_calls["count"] += 1
                if get_calls["count"] == 1:
                    return None
                return original_get(*args, **kwargs)

            monkeypatch.setattr(race_store._owner_state, "get", stale_first_get)
            race_replay, inserted = race_store.evaluate_and_record(
                grant_decision_id="grant-decision-1",
                capital_grant_id="grant-1",
                approved_decision=approved_decision(),
                portfolio_state=portfolio_state(global_held="999", coin_held="999", global_tranches=3, coin_tranches=3),
                policy=policy_for(coin_allocation_cap="1000", max_positions_per_coin=4, minimum_tranche_capital="999"),
                venue_facts=venue_facts(),
                as_of=NOW,
            )
            assert inserted is False
            assert race_replay.payload_digest == record.payload_digest
            assert race_replay.capital_grant is not None
            assert _outbox_count(uow.connection, message_id="grant-1") == 1

        with PostgresUnitOfWork(factory) as restarted:
            stored = PortfolioGrantDecisionStore(restarted.connection).get_by_position_decision_id(
                position_decision_id="position-decision-1"
            )
        assert stored is not None
        assert stored.status == "ALLOWED"
        assert stored.capital_grant is not None
        assert stored.payload["portfolio_grant_decision"]["capital_grant"]["capital_and_limits"]["requested_capital_per_tranche"] == "250.366666666666"
    finally:
        _drop_schema(settings)


def test_b8b_store_persists_blocked_without_grant_or_outbox_and_conflicts_changed_replay():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = PortfolioGrantDecisionStore(uow.connection)
            record, inserted = store.evaluate_and_record(
                grant_decision_id="grant-decision-1",
                capital_grant_id="grant-1",
                approved_decision=approved_decision(),
                portfolio_state=portfolio_state(global_held="560", coin_held="400", global_tranches=1, coin_tranches=0),
                policy=policy_for(global_position_cap="600", coin_allocation_cap="500", minimum_tranche_capital="100", max_positions_per_coin=2),
                venue_facts=venue_facts(),
                as_of=NOW,
            )
            assert inserted is True
            assert record.status == "BLOCKED"
            assert record.capital_grant is None
            assert DurableMessageStore(uow.connection).get_outbox(message_id="grant-1") is None
            replayed, inserted = store.evaluate_and_record(
                grant_decision_id="grant-decision-1",
                capital_grant_id="grant-1",
                approved_decision=approved_decision(),
                portfolio_state=portfolio_state(global_held="0", coin_held="0"),
                policy=policy_for(),
                venue_facts=venue_facts(),
                as_of=NOW,
            )
            assert inserted is False
            assert replayed.status == "BLOCKED"
            assert replayed.primary_reason == "MINIMUM_TRANCHE_CAPITAL_NOT_MET"
            changed_decision = approved_decision()
            changed_decision["position_decision"]["event_id"] = "different-decision-event"
            with pytest.raises(PortfolioGrantDecisionConflict):
                store.evaluate_and_record(
                    grant_decision_id="grant-decision-1",
                    capital_grant_id="grant-1",
                    approved_decision=changed_decision,
                    portfolio_state=portfolio_state(global_held="0", coin_held="0"),
                    policy=policy_for(),
                    venue_facts=venue_facts(),
                    as_of=NOW,
                )

        with PostgresUnitOfWork(factory) as restarted:
            stored = PortfolioGrantDecisionStore(restarted.connection).get_by_position_decision_id(
                position_decision_id="position-decision-1"
            )
        assert stored is not None
        assert stored.status == "BLOCKED"
        assert stored.capital_grant is None
        assert stored.primary_reason == "MINIMUM_TRANCHE_CAPITAL_NOT_MET"
        assert stored.payload["portfolio_grant_decision"]["evaluated_reasons"] == [
            "MINIMUM_TRANCHE_CAPITAL_NOT_MET",
            "INSUFFICIENT_GLOBAL_CAPITAL_FOR_TRANCHE",
        ]
    finally:
        _drop_schema(settings)


def test_b8b_store_persists_zero_slot_block_without_grant_or_outbox():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            record, inserted = PortfolioGrantDecisionStore(uow.connection).evaluate_and_record(
                grant_decision_id="grant-decision-1",
                capital_grant_id="grant-1",
                approved_decision=approved_decision(),
                portfolio_state=portfolio_state(global_tranches=4, coin_tranches=2),
                policy=policy_for(max_open_positions=4, max_positions_per_coin=2),
                venue_facts=venue_facts(),
                as_of=NOW,
            )
            assert inserted is True
            assert record.status == "BLOCKED"
            assert record.payload["portfolio_grant_decision"]["evaluated_reasons"] == [
                "MAX_OPEN_POSITIONS_REACHED",
                "MAX_COIN_POSITIONS_REACHED",
            ]
            assert record.capital_grant is None
            assert DurableMessageStore(uow.connection).get_outbox(message_id="grant-1") is None
    finally:
        _drop_schema(settings)


def portfolio_state(
    *,
    health: PortfolioHealth = PortfolioHealth.LIVE,
    global_held: str = "0",
    coin_held: str = "0",
    global_tranches: int = 0,
    coin_tranches: int = 0,
    extra_symbols: tuple[str, ...] = (),
) -> PortfolioState:
    coins = [
        CoinPortfolioState(
            symbol="BTCUSDT",
            buckets=CommitmentBuckets(held_committed_capital=coin_held, committed_tranches=coin_tranches),
        )
    ]
    coins.extend(
        CoinPortfolioState(
            symbol=symbol,
            buckets=CommitmentBuckets(held_committed_capital="0", committed_tranches=0),
        )
        for symbol in extra_symbols
    )
    return PortfolioState(
        portfolio_id="portfolio-main",
        revision=4,
        health=health,
        as_of=NOW,
        evidence_id="portfolio-state-1",
        global_buckets=CommitmentBuckets(held_committed_capital=global_held, committed_tranches=global_tranches),
        coins=tuple(coins),
    )


def policy_for(
    *,
    minimum_tranche_capital: str = "10",
    global_position_cap: str = "1000",
    coin_allocation_cap: str = "500",
    max_open_positions: int = 4,
    max_positions_per_coin: int = 2,
    daily_loss_blocked: bool = False,
) -> PortfolioGrantPolicy:
    return PortfolioGrantPolicy(
        minimum_tranche_capital=minimum_tranche_capital,
        global_position_cap=global_position_cap,
        coin_allocation_cap=coin_allocation_cap,
        max_open_positions=max_open_positions,
        max_positions_per_coin=max_positions_per_coin,
        daily_loss_blocked=daily_loss_blocked,
    )


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b8b_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def _outbox_count(connection, *, message_id: str) -> int:
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM triggertrade_outbox_messages WHERE message_id = %s", (message_id,))
        return int(cursor.fetchone()[0])
