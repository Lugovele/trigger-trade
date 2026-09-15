from __future__ import annotations

import pytest

from triggertrade.capital_grants import (
    CapitalGrantError,
    build_capital_and_limits_grant,
    validate_capital_grant_for_decision,
)
from triggertrade.contracts import parse_contract
from tests.unit.test_target_contracts import valid_payload


NOW = "2026-09-15T00:00:00Z"


def test_build_capital_and_limits_grant_binds_approved_decision():
    decision = approved_decision()
    parsed = build_capital_and_limits_grant(
        capital_grant_id="grant-1",
        approved_decision=decision,
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

    payload = parsed.to_payload()
    grant = payload["capital_and_limits"]

    assert grant["capital_grant_id"] == "grant-1"
    assert grant["position_decision_id"] == decision["position_decision"]["position_decision_id"]
    assert grant["grant_state_at_issue"] == "ISSUED"
    assert grant["numeric_policy_version"] == "TT_NUMERIC_V1"
    assert parse_contract("CAPITAL_AND_LIMITS", payload).to_payload() == payload


def test_capital_grant_rejects_reject_decision_and_mismatched_binding():
    decision = approved_decision()
    rejected = approved_decision()
    rejected["position_decision"]["decision"] = "REJECT"
    with pytest.raises(CapitalGrantError, match="APPROVE"):
        build_capital_and_limits_grant(
            capital_grant_id="grant-1",
            approved_decision=rejected,
            created_at=NOW,
            as_of=NOW,
            portfolio_state_revision=4,
            requested_capital_per_tranche="1",
            minimum_tranche_capital="1",
            remaining_coin_capital="1",
            remaining_global_capital="1",
            remaining_coin_slots=1,
            remaining_global_slots=1,
            relevant_portfolio_limits=relevant_limits(),
            accounting_policy=accounting_policy(),
            venue_facts=venue_facts(),
        )

    grant = build_grant(decision)
    grant["capital_and_limits"]["position_decision_id"] = "different-decision"
    with pytest.raises(CapitalGrantError, match="position_decision_id"):
        validate_capital_grant_for_decision(approved_decision=decision, capital_grant=grant)


def test_capital_grant_rejects_invalid_integer_inputs_before_contract_build():
    with pytest.raises(CapitalGrantError, match="remaining_coin_slots"):
        build_capital_and_limits_grant(
            capital_grant_id="grant-1",
            approved_decision=approved_decision(),
            created_at=NOW,
            as_of=NOW,
            portfolio_state_revision=4,
            requested_capital_per_tranche="1",
            minimum_tranche_capital="1",
            remaining_coin_capital="1",
            remaining_global_capital="1",
            remaining_coin_slots=1.5,
            remaining_global_slots=1,
            relevant_portfolio_limits=relevant_limits(),
            accounting_policy=accounting_policy(),
            venue_facts=venue_facts(),
        )


def approved_decision() -> dict[str, object]:
    payload = valid_payload("APPROVE_REJECT", "APPROVE_REJECT.initial")
    decision = payload["position_decision"]
    decision.update(
        {
            "event_id": "decision-event-1",
            "position_decision_id": "position-decision-1",
            "decision_cycle_id": "decision-cycle-1",
            "set_result_id": "set-result-1",
            "symbol": "BTCUSDT",
            "decision": "APPROVE",
            "reason_code": "APPROVED",
        }
    )
    return payload


def build_grant(decision: dict[str, object] | None = None) -> dict[str, object]:
    return build_capital_and_limits_grant(
        capital_grant_id="grant-1",
        approved_decision=approved_decision() if decision is None else decision,
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
    ).to_payload()


def relevant_limits() -> dict[str, object]:
    return {
        "global_position_cap": "1000",
        "coin_allocation_cap": "500",
        "max_open_positions": 4,
        "max_positions_per_coin": 2,
        "daily_loss_blocked": False,
    }


def accounting_policy() -> dict[str, object]:
    return {
        "accounting_timezone": "Asia/Jerusalem",
        "day_boundary_local": "00:00:00",
        "accounting_policy_version": "ACCOUNTING_DAY_V1",
    }


def venue_facts() -> dict[str, object]:
    return {
        "instrument": {
            "tick_size": "0.1",
            "qty_step": "0.001",
            "min_order_qty": "0.001",
            "min_notional": "5",
            "max_order_qty": "100",
            "max_order_qty_status": "AVAILABLE",
            "max_order_qty_source_field": "lotSizeFilter.maxOrderQty",
            "max_leverage": "50",
            "contract_type": "LINEAR_USDT_PERPETUAL",
            "metadata_revision": "instrument:BTCUSDT:1",
            "native_profile_revision": "bybit-demo-linear-profile-v1",
            "instrument_supported": True,
            "position_mode": "HEDGE_MODE",
            "margin_mode": "ISOLATED",
            "as_of": NOW,
            "source_ref": "linear:BTCUSDT",
        },
        "fees": {
            "maker_fee_rate": "0.0002",
            "taker_fee_rate": "0.00055",
            "fee_schedule_version": "bybit-demo-linear-fees",
            "effective_at": NOW,
            "as_of": NOW,
            "source_ref": "fee-rate:BTCUSDT",
        },
    }
