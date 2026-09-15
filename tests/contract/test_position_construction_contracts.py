from __future__ import annotations

from triggertrade.contracts import contract_digest, implemented_contract_registry, parse_contract
from tests.unit.test_capital_grants import build_grant
from tests.unit.test_position_construction import constructed_result


def test_position_construction_uses_approved_current_approve_reject_v5_contract():
    registry = implemented_contract_registry()
    assert registry["APPROVE_REJECT"] == {
        "version": 5,
        "definitions": ("APPROVE_REJECT.initial", "APPROVE_REJECT.constructed", "APPROVE_REJECT.failed"),
    }
    payload = constructed_result(build_grant())

    assert parse_contract("APPROVE_REJECT", payload, definition="APPROVE_REJECT.constructed").to_payload() == payload
    assert contract_digest(payload) == contract_digest(parse_contract("APPROVE_REJECT", payload))
