from __future__ import annotations

import pytest

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.lifecycle_start_gate import (
    READY_TO_SUBMIT,
    LifecycleStartGateError,
    lifecycle_start_gate_digest,
    match_lifecycle_start_gate,
)
from triggertrade.order_specs import order_spec_digest
from triggertrade.submit_authorizations import build_submit_authorized
from tests.unit.test_capital_grants import NOW, build_grant
from tests.unit.test_order_specs import valid_order_spec
from tests.unit.test_position_construction import constructed_result


def test_lifecycle_start_gate_matches_spec_and_authorization():
    spec, authorization = valid_gate_inputs()

    match = match_lifecycle_start_gate(order_spec=spec, submit_authorized=authorization)

    assert match.lifecycle_state == READY_TO_SUBMIT
    assert match.order_spec_id == "order-spec-1"
    assert match.authorization_id == "auth-1"
    assert match.tranche_id == "tranche-1"
    assert match.order_spec_digest == order_spec_digest(spec)
    assert match.submit_authorized_digest == canonical_json_digest(authorization)
    assert lifecycle_start_gate_digest(match) == (
        "c225b6ce26bf4adf8a49317cda74cf97d06ed5b37605c015d760d199e1a9827c"
    )


def test_lifecycle_start_gate_rejects_identity_mismatch():
    spec, authorization = valid_gate_inputs()
    authorization["submit_authorized"]["tranche_id"] = "different-tranche"

    with pytest.raises(LifecycleStartGateError, match="tranche_id"):
        match_lifecycle_start_gate(order_spec=spec, submit_authorized=authorization)


def test_lifecycle_start_gate_rejects_digest_mismatch():
    spec, authorization = valid_gate_inputs()
    authorization["submit_authorized"]["order_spec_digest"] = "b" * 64

    with pytest.raises(LifecycleStartGateError, match="order_spec_digest"):
        match_lifecycle_start_gate(order_spec=spec, submit_authorized=authorization)


def test_lifecycle_start_gate_rejects_held_capital_mismatch():
    spec, authorization = valid_gate_inputs()
    authorization["submit_authorized"]["held_committed_capital"] = "99"

    with pytest.raises(LifecycleStartGateError, match="held_committed_capital"):
        match_lifecycle_start_gate(order_spec=spec, submit_authorized=authorization)


def test_lifecycle_start_gate_rejects_invalid_pre_submit_spec_gate_state():
    spec, authorization = valid_gate_inputs()
    spec["order_spec"]["economics"]["minimum_net_edge_result"] = "FAIL"

    with pytest.raises(LifecycleStartGateError, match="minimum_net_edge"):
        match_lifecycle_start_gate(order_spec=spec, submit_authorized=authorization)


def test_lifecycle_start_gate_rejects_available_max_order_quantity_violation():
    spec, authorization = valid_gate_inputs()
    spec["order_spec"]["venue_validation"]["max_order_qty"] = "0.5"
    authorization["submit_authorized"]["order_spec_digest"] = order_spec_digest(spec)

    with pytest.raises(LifecycleStartGateError, match="max_order_qty"):
        match_lifecycle_start_gate(order_spec=spec, submit_authorized=authorization)


def valid_gate_inputs() -> tuple[dict[str, object], dict[str, object]]:
    grant = build_grant()
    spec = valid_order_spec(grant)
    construction = constructed_result(grant, order_spec_digest_value=order_spec_digest(spec))
    authorization = build_submit_authorized(
        authorization_id="auth-1",
        capital_grant=grant,
        construction_result=construction,
        authorized_at=NOW,
    ).to_payload()
    return spec, authorization
