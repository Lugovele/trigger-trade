from __future__ import annotations

from triggertrade.contracts import contract_digest, implemented_contract_registry, parse_contract
from triggertrade.submit_authorizations import build_submit_authorized
from tests.unit.test_capital_grants import NOW, build_grant
from tests.unit.test_submit_authorizations import constructed_result


def test_submit_authorization_uses_approved_current_submit_authorized_v5_contract():
    registry = implemented_contract_registry()
    assert registry["SUBMIT_AUTHORIZED"] == {"version": 5, "definitions": ("SUBMIT_AUTHORIZED",)}
    grant = build_grant()
    construction = constructed_result(grant)

    authorization = build_submit_authorized(
        authorization_id="auth-contract-1",
        capital_grant=grant,
        construction_result=construction,
        authorized_at=NOW,
    )
    payload = authorization.to_payload()

    assert parse_contract("SUBMIT_AUTHORIZED", payload).to_payload() == payload
    assert contract_digest(payload) == contract_digest(authorization)
