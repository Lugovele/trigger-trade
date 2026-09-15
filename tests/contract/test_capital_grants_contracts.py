from __future__ import annotations

from triggertrade.capital_grants import build_capital_and_limits_grant
from triggertrade.contracts import contract_digest, implemented_contract_registry, parse_contract
from tests.unit.test_capital_grants import (
    NOW,
    accounting_policy,
    approved_decision,
    relevant_limits,
    venue_facts,
)


def test_capital_grant_uses_approved_current_capital_and_limits_v5_contract():
    registry = implemented_contract_registry()
    assert registry["CAPITAL_AND_LIMITS"] == {"version": 5, "definitions": ("CAPITAL_AND_LIMITS",)}

    grant = build_capital_and_limits_grant(
        capital_grant_id="grant-contract-1",
        approved_decision=approved_decision(),
        created_at=NOW,
        as_of=NOW,
        portfolio_state_revision=4,
        requested_capital_per_tranche="250.366666666666",
        minimum_tranche_capital="10",
        remaining_coin_capital="500",
        remaining_global_capital="1000",
        remaining_coin_slots=2,
        remaining_global_slots=4,
        relevant_portfolio_limits=relevant_limits(),
        accounting_policy=accounting_policy(),
        venue_facts=venue_facts(),
    )
    payload = grant.to_payload()

    assert parse_contract("CAPITAL_AND_LIMITS", payload).to_payload() == payload
    assert contract_digest(payload) == contract_digest(grant)
