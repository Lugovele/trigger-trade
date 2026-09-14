from __future__ import annotations

import json
from pathlib import Path

import pytest

from triggertrade.contracts import ContractError, implemented_contract_registry, parse_contract
from tests.unit.test_target_contracts import valid_payload


APPROVED_REGISTRY_PATH = Path("docs/trading-methodology/schemas/CONTRACT_REGISTRY.json")


def test_implemented_contract_registry_matches_approved_current_registry():
    approved = json.loads(APPROVED_REGISTRY_PATH.read_text(encoding="utf-8"))
    implemented = implemented_contract_registry()

    assert set(implemented) == set(approved)
    for contract_type, approved_entry in approved.items():
        assert implemented[contract_type]["version"] == approved_entry["version"]
        assert set(implemented[contract_type]["definitions"]) == set(approved_entry["definitions"])


def test_representative_approved_fixtures_validate_for_every_registry_definition():
    for contract_type, entry in implemented_contract_registry().items():
        for definition in entry["definitions"]:
            parsed = parse_contract(contract_type, valid_payload(contract_type, definition), definition=definition)
            assert parsed.version == entry["version"]


def test_invalid_fixture_fails_deterministically():
    payload = valid_payload("MARKET_DATA_REQUEST", "MARKET_DATA_REQUEST.request")
    payload["market_data_request"]["purpose"] = "UNAPPROVED_PURPOSE"

    with pytest.raises(ContractError, match="purpose"):
        parse_contract("MARKET_DATA_REQUEST", payload, definition="MARKET_DATA_REQUEST.request")


def test_unknown_fields_fail_for_contract_fixtures():
    payload = valid_payload("ORDER_CANCEL_SIGNAL", "ORDER_CANCEL_SIGNAL")
    payload["order_cancel_signal"]["unexpected"] = "x"

    with pytest.raises(ContractError, match="unknown fields: unexpected"):
        parse_contract("ORDER_CANCEL_SIGNAL", payload)


def test_digest_fields_accept_canonical_sha256_hex_values():
    payload = valid_payload("APPROVE_REJECT", "APPROVE_REJECT.constructed")
    payload["position_construction_result"]["order_spec_digest"] = "0" * 64

    parsed = parse_contract("APPROVE_REJECT", payload, definition="APPROVE_REJECT.constructed")

    assert parsed.to_payload()["position_construction_result"]["order_spec_digest"] == "0" * 64
