from __future__ import annotations

import pytest

from triggertrade.contracts import parse_contract
from triggertrade.position_construction import (
    PositionConstructionError,
    build_constructed_position_result,
    build_rejected_position_construction_result,
    validate_position_construction_result,
)
from tests.unit.test_capital_grants import NOW, build_grant


def test_build_constructed_position_result_binds_grant_without_formula_calculation():
    grant = build_grant()
    parsed = build_constructed_position_result(
        event_id="construction-event-1",
        occurred_at=NOW,
        construction_result_id="construction-result-1",
        capital_grant=grant,
        position_plan_id="position-plan-1",
        tranche_id="tranche-1",
        order_spec_id="order-spec-1",
        order_spec_digest="a" * 64,
        approved_economics=approved_economics(),
        minimum_net_edge=minimum_net_edge(enabled=True, status="PASS"),
        direction="LONG",
    )
    payload = parsed.to_payload()
    body = payload["position_construction_result"]

    assert body["capital_grant_id"] == grant["capital_and_limits"]["capital_grant_id"]
    assert body["approved_economics"]["approved_actual_committed_capital"] == "100"
    assert body["numeric_policy_version"] == "TT_NUMERIC_V1"
    assert body["order_spec_contract_version"] == 5
    assert parse_contract("APPROVE_REJECT", payload, definition="APPROVE_REJECT.constructed").to_payload() == payload


def test_build_rejected_position_construction_result_has_no_successful_spec_fields():
    grant = build_grant()
    parsed = build_rejected_position_construction_result(
        event_id="construction-event-reject-1",
        occurred_at=NOW,
        construction_result_id="construction-result-reject-1",
        capital_grant=grant,
        minimum_net_edge=minimum_net_edge(enabled=True, status="FAIL", calculated_value="-0.01"),
        failed_gates=("minimum_net_edge",),
        reason_code="MINIMUM_NET_EDGE_FAILED",
    )
    payload = parsed.to_payload()
    body = payload["position_construction_result"]

    assert body["outcome"] == "REJECT"
    assert body["failed_gates"] == ["minimum_net_edge"]
    assert "order_spec_id" not in body
    assert "approved_economics" not in body
    assert parse_contract("APPROVE_REJECT", payload, definition="APPROVE_REJECT.failed").to_payload() == payload


def test_position_construction_rejects_mismatched_grant_binding():
    grant = build_grant()
    payload = constructed_result(grant)
    payload["position_construction_result"]["decision_cycle_id"] = "different-cycle"

    with pytest.raises(PositionConstructionError, match="decision_cycle_id"):
        validate_position_construction_result(capital_grant=grant, construction_result=payload)


def test_position_construction_rejects_constructed_failed_minimum_net_edge():
    grant = build_grant()

    with pytest.raises(PositionConstructionError, match="minimum_net_edge"):
        build_constructed_position_result(
            event_id="construction-event-1",
            occurred_at=NOW,
            construction_result_id="construction-result-1",
            capital_grant=grant,
            position_plan_id="position-plan-1",
            tranche_id="tranche-1",
            order_spec_id="order-spec-1",
            order_spec_digest="a" * 64,
            approved_economics=approved_economics(),
            minimum_net_edge=minimum_net_edge(enabled=True, status="FAIL"),
            direction="LONG",
        )


def constructed_result(grant: dict[str, object] | None = None) -> dict[str, object]:
    grant_payload = build_grant() if grant is None else grant
    return build_constructed_position_result(
        event_id="construction-event-1",
        occurred_at=NOW,
        construction_result_id="construction-result-1",
        capital_grant=grant_payload,
        position_plan_id="position-plan-1",
        tranche_id="tranche-1",
        order_spec_id="order-spec-1",
        order_spec_digest="a" * 64,
        approved_economics=approved_economics(),
        minimum_net_edge=minimum_net_edge(enabled=True, status="PASS"),
        direction="LONG",
    ).to_payload()


def approved_economics() -> dict[str, str]:
    return {
        "approved_entry": "100",
        "approved_quantity": "1",
        "approved_leverage": "1",
        "approved_actual_order_notional": "100",
        "approved_actual_committed_capital": "100",
    }


def minimum_net_edge(
    *,
    enabled: bool,
    status: str,
    configured_value: str | None = "0.01",
    calculated_value: str | None = "0.02",
) -> dict[str, object]:
    return {
        "enabled": enabled,
        "status": status,
        "configured_value": configured_value,
        "calculated_value": calculated_value,
        "reason_code": None,
    }
