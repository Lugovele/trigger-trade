from __future__ import annotations

from triggertrade.contracts import contract_digest, implemented_contract_registry, parse_contract
from tests.unit.test_capital_grants import build_grant
from tests.unit.test_order_specs import valid_order_spec


def test_order_spec_uses_approved_current_order_spec_v5_contract():
    registry = implemented_contract_registry()
    assert registry["ORDER_SPEC"] == {"version": 5, "definitions": ("ORDER_SPEC",)}
    payload = valid_order_spec(build_grant())

    assert parse_contract("ORDER_SPEC", payload).to_payload() == payload
    assert contract_digest(payload) == "eefeadceb45741cfa14bbf476f5496f65acb4777a83a1e25ff8db58799528463"
