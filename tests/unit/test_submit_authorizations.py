from __future__ import annotations

import pytest

from triggertrade.contracts import parse_contract
from triggertrade.submit_authorizations import (
    SubmitAuthorizationError,
    build_submit_authorized,
    validate_submit_authorized,
)
from tests.unit.test_capital_grants import NOW, approved_decision, build_grant
from tests.unit.test_target_contracts import valid_payload


def test_build_submit_authorized_binds_constructed_result_and_grant():
    grant = build_grant()
    construction = constructed_result(grant)

    parsed = build_submit_authorized(
        authorization_id="auth-1",
        capital_grant=grant,
        construction_result=construction,
        authorized_at=NOW,
    )
    payload = parsed.to_payload()
    authorization = payload["submit_authorized"]

    assert authorization["authorization_id"] == "auth-1"
    assert authorization["capital_grant_id"] == grant["capital_and_limits"]["capital_grant_id"]
    assert authorization["construction_result_id"] == construction["position_construction_result"]["construction_result_id"]
    assert authorization["held_committed_capital"] == "100"
    assert authorization["numeric_policy_version"] == "TT_NUMERIC_V1"
    assert parse_contract("SUBMIT_AUTHORIZED", payload).to_payload() == payload


def test_submit_authorized_rejects_mismatched_grant_binding():
    grant = build_grant()
    construction = constructed_result(grant)
    construction["position_construction_result"]["capital_grant_id"] = "different-grant"

    with pytest.raises(SubmitAuthorizationError, match="capital_grant_id"):
        build_submit_authorized(
            authorization_id="auth-1",
            capital_grant=grant,
            construction_result=construction,
            authorized_at=NOW,
        )


def test_submit_authorized_rejects_grant_bound_and_capacity_violations():
    grant = build_grant()
    construction = constructed_result(grant)
    construction["position_construction_result"]["approved_economics"]["approved_actual_committed_capital"] = "251"

    with pytest.raises(SubmitAuthorizationError, match="requested_capital_per_tranche"):
        build_submit_authorized(
            authorization_id="auth-1",
            capital_grant=grant,
            construction_result=construction,
            authorized_at=NOW,
        )

    no_slot_grant = build_grant()
    no_slot_grant["capital_and_limits"]["remaining_coin_slots"] = 0
    with pytest.raises(SubmitAuthorizationError, match="remaining_coin_slots"):
        build_submit_authorized(
            authorization_id="auth-1",
            capital_grant=no_slot_grant,
            construction_result=constructed_result(no_slot_grant),
            authorized_at=NOW,
        )


def test_submit_authorized_validation_rejects_changed_payload_fields():
    grant = build_grant()
    construction = constructed_result(grant)
    authorization = build_submit_authorized(
        authorization_id="auth-1",
        capital_grant=grant,
        construction_result=construction,
        authorized_at=NOW,
    ).to_payload()
    authorization["submit_authorized"]["order_spec_digest"] = "b" * 64

    with pytest.raises(SubmitAuthorizationError, match="order_spec_digest"):
        validate_submit_authorized(
            capital_grant=grant,
            construction_result=construction,
            submit_authorized=authorization,
        )


def constructed_result(grant: dict[str, object] | None = None) -> dict[str, object]:
    grant_payload = build_grant(approved_decision()) if grant is None else grant
    body = grant_payload["capital_and_limits"]
    payload = valid_payload("APPROVE_REJECT", "APPROVE_REJECT.constructed")
    construction = payload["position_construction_result"]
    construction.update(
        {
            "event_id": "construction-event-1",
            "occurred_at": NOW,
            "position_decision_id": body["position_decision_id"],
            "construction_result_id": "construction-result-1",
            "capital_grant_id": body["capital_grant_id"],
            "decision_cycle_id": body["decision_cycle_id"],
            "set_result_id": body["set_result_id"],
            "symbol": body["symbol"],
            "reason_code": "CONSTRUCTED",
            "position_plan_id": "position-plan-1",
            "tranche_id": "tranche-1",
            "order_spec_id": "order-spec-1",
            "order_spec_digest": "a" * 64,
            "approved_economics": {
                "approved_entry": "100",
                "approved_quantity": "1",
                "approved_leverage": "1",
                "approved_actual_order_notional": "100",
                "approved_actual_committed_capital": "100",
            },
            "direction": "LONG",
            "order_spec_contract_version": 5,
        }
    )
    return payload
