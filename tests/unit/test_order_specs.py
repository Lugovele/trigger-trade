from __future__ import annotations

import pytest

from triggertrade.contracts import contract_digest, parse_contract
from triggertrade.order_specs import (
    OrderSpecError,
    build_order_spec,
    order_spec_digest,
    validate_order_spec_for_construction,
)
from tests.unit.test_capital_grants import NOW, build_grant
from tests.unit.test_position_construction import constructed_result


def test_build_order_spec_binds_grant_and_preserves_formula_inputs():
    grant = build_grant()
    parsed = build_order_spec(
        order_spec_id="order-spec-1",
        spec_created_at=NOW,
        construction_result_id="construction-result-1",
        capital_grant=grant,
        position_plan_id="position-plan-1",
        tranche_id="tranche-1",
        direction="LONG",
        side="BUY",
        entry={"order_type": "LIMIT", "post_only": True, "price": "100", "quantity": "1"},
        leverage="1",
        take_profit=take_profit(),
        stop_loss=stop_loss(),
        economics=economics(),
        venue_validation=venue_validation(),
        provenance=provenance(),
    )
    payload = parsed.to_payload()
    spec = payload["order_spec"]

    assert spec["capital_grant_id"] == grant["capital_and_limits"]["capital_grant_id"]
    assert spec["entry"]["price"] == "100"
    assert spec["economics"]["actual_committed_capital"] == "100"
    assert order_spec_digest(parsed) == contract_digest(payload)
    assert parse_contract("ORDER_SPEC", payload).to_payload() == payload


def test_order_spec_validation_requires_construction_digest_and_duplicated_scalars():
    grant = build_grant()
    spec = valid_order_spec(grant)
    digest = order_spec_digest(spec)
    construction = constructed_result(grant, order_spec_digest_value=digest)

    parsed = validate_order_spec_for_construction(construction_result=construction, order_spec=spec)

    assert parsed.to_payload() == spec
    assert digest == "eefeadceb45741cfa14bbf476f5496f65acb4777a83a1e25ff8db58799528463"


def test_order_spec_validation_rejects_changed_digest_or_scalar():
    grant = build_grant()
    spec = valid_order_spec(grant)
    construction = constructed_result(grant, order_spec_digest_value=order_spec_digest(spec))

    changed_digest = constructed_result(grant, order_spec_digest_value="b" * 64)
    with pytest.raises(OrderSpecError, match="order_spec_digest"):
        validate_order_spec_for_construction(construction_result=changed_digest, order_spec=spec)

    changed_scalar = valid_order_spec(grant)
    changed_scalar["order_spec"]["entry"]["quantity"] = "2"
    construction_for_changed_scalar = constructed_result(grant, order_spec_digest_value=order_spec_digest(changed_scalar))
    with pytest.raises(OrderSpecError, match="approved_quantity"):
        validate_order_spec_for_construction(construction_result=construction_for_changed_scalar, order_spec=changed_scalar)


def test_order_spec_validation_rejects_minimum_net_edge_binding_mismatch():
    grant = build_grant()
    spec = valid_order_spec(grant)
    construction = constructed_result(grant, order_spec_digest_value=order_spec_digest(spec))
    construction["position_construction_result"]["rule_results"]["minimum_net_edge"]["calculated_value"] = "0.03"

    with pytest.raises(OrderSpecError, match="planned_net_edge_pct"):
        validate_order_spec_for_construction(construction_result=construction, order_spec=spec)


def valid_order_spec(grant: dict[str, object] | None = None) -> dict[str, object]:
    grant_payload = build_grant() if grant is None else grant
    return build_order_spec(
        order_spec_id="order-spec-1",
        spec_created_at=NOW,
        construction_result_id="construction-result-1",
        capital_grant=grant_payload,
        position_plan_id="position-plan-1",
        tranche_id="tranche-1",
        direction="LONG",
        side="BUY",
        entry={"order_type": "LIMIT", "post_only": True, "price": "100", "quantity": "1"},
        leverage="1",
        take_profit=take_profit(),
        stop_loss=stop_loss(),
        economics=economics(),
        venue_validation=venue_validation(),
        provenance=provenance(),
    ).to_payload()


def take_profit() -> dict[str, object]:
    return {
        "mode": "FIXED",
        "price": "110",
        "execution_type": "MARKET",
        "trigger_by": "LAST_PRICE",
        "scope": "PARTIAL_QUANTITY",
        "fixed_pct": "0.05",
    }


def stop_loss() -> dict[str, object]:
    return {
        "mode": "FIXED",
        "price": "95",
        "execution_type": "MARKET",
        "trigger_by": "LAST_PRICE",
        "scope": "PARTIAL_QUANTITY",
        "fixed_pct": "0.02",
    }


def economics() -> dict[str, object]:
    return {
        "target_order_notional": "100",
        "actual_order_notional": "100",
        "actual_committed_capital": "100",
        "gross_rr": "2",
        "planned_net_edge_pct": "0.02",
        "minimum_net_edge_enabled": True,
        "minimum_net_edge_result": "PASS",
        "maker_fee_rate": "0.001",
        "taker_fee_rate": "0.002",
        "fee_schedule_version": "fees-v1",
        "fee_rate_source_ref": "portfolio-data:fees-v1",
        "funding_in_planned_net_edge": False,
    }


def venue_validation() -> dict[str, object]:
    return {
        "max_order_qty_status": "AVAILABLE",
        "max_order_qty": "10",
        "max_order_qty_source_field": "lotSizeFilter.maxOrderQty",
        "max_order_qty_source_ref": "portfolio-data:instrument-v1",
        "native_profile_revision": "native-profile-v1",
    }


def provenance() -> dict[str, object]:
    return {
        "set_version": "set-v1",
        "position_rules_version": "position-rules-v1",
        "instrument_metadata_revision": "instrument-v1",
        "market_snapshot_at": NOW,
    }
