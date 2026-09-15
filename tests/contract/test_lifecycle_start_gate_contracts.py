from __future__ import annotations

import pytest

from triggertrade.contracts import parse_contract
from triggertrade.lifecycle_start_gate import LifecycleStartGateError, match_lifecycle_start_gate
from tests.unit.test_lifecycle_start_gate import valid_gate_inputs


def test_lifecycle_start_gate_consumes_approved_v5_contracts():
    spec, authorization = valid_gate_inputs()

    assert parse_contract("ORDER_SPEC", spec).to_payload() == spec
    assert parse_contract("SUBMIT_AUTHORIZED", authorization).to_payload() == authorization
    assert match_lifecycle_start_gate(order_spec=spec, submit_authorized=authorization).lifecycle_state == "READY_TO_SUBMIT"


def test_lifecycle_start_gate_rejects_invalid_contract_version():
    spec, authorization = valid_gate_inputs()
    authorization["submit_authorized"]["contract_version"] = 4

    with pytest.raises(LifecycleStartGateError, match="version"):
        match_lifecycle_start_gate(order_spec=spec, submit_authorized=authorization)


def test_lifecycle_start_gate_rejects_unknown_contract_fields():
    spec, authorization = valid_gate_inputs()
    authorization["submit_authorized"]["unexpected"] = "not-approved"

    with pytest.raises(LifecycleStartGateError, match="unknown fields"):
        match_lifecycle_start_gate(order_spec=spec, submit_authorized=authorization)
