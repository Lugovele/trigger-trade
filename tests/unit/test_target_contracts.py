from __future__ import annotations

import pytest

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.contracts import (
    ContractError,
    ContractType,
    contract_digest,
    get_contract_definition,
    implemented_contract_registry,
    parse_contract,
    validate_contract,
)
from triggertrade.contracts._approved_wire_schema import WIRE_SCHEMA


@pytest.mark.parametrize("contract_type", [member.value for member in ContractType])
def test_valid_construction_for_each_approved_contract_family(contract_type):
    registry = implemented_contract_registry()

    for definition in registry[contract_type]["definitions"]:
        payload = valid_payload(contract_type, definition)
        parsed = parse_contract(contract_type, payload, definition=definition)

        assert parsed.contract_type.value == contract_type
        assert parsed.definition == definition
        assert parsed.version == registry[contract_type]["version"]
        assert parsed.to_payload() == payload


def test_missing_required_field_is_rejected():
    payload = valid_payload("COINS", "COINS")
    del payload["coins"]["event_id"]

    with pytest.raises(ContractError, match="missing required fields: event_id"):
        validate_contract("COINS", payload)


def test_unknown_top_level_field_is_rejected():
    payload = valid_payload("COINS", "COINS")
    payload["extra"] = {}

    with pytest.raises(ContractError, match="unknown fields: extra"):
        validate_contract("COINS", payload)


def test_unknown_contract_field_is_rejected():
    payload = valid_payload("ORDER_SPEC", "ORDER_SPEC")
    payload["order_spec"]["extra"] = "not-approved"

    with pytest.raises(ContractError, match="unknown fields: extra"):
        validate_contract("ORDER_SPEC", payload)


def test_invalid_enum_value_is_rejected():
    payload = valid_payload("ORDER_SPEC", "ORDER_SPEC")
    payload["order_spec"]["direction"] = "SIDEWAYS"

    with pytest.raises(ContractError, match="direction"):
        validate_contract("ORDER_SPEC", payload)


def test_invalid_contract_version_is_rejected():
    payload = valid_payload("SUBMIT_AUTHORIZED", "SUBMIT_AUTHORIZED")
    payload["submit_authorized"]["contract_version"] = 4

    with pytest.raises(ContractError, match="contract_version must be 5"):
        validate_contract("SUBMIT_AUTHORIZED", payload)


def test_unknown_contract_type_is_rejected():
    with pytest.raises(ContractError, match="unknown contract type"):
        validate_contract("NOT_A_CONTRACT", {})


def test_unknown_contract_definition_is_rejected():
    with pytest.raises(ContractError, match="unknown ORDER_SPEC contract definition"):
        get_contract_definition("ORDER_SPEC", definition="ORDER_SPEC.v999")


def test_multi_definition_contract_requires_definition_for_direct_lookup():
    with pytest.raises(ContractError, match="requires an explicit definition"):
        get_contract_definition("APPROVE_REJECT")


def test_definition_can_be_inferred_from_discriminator_fields():
    payload = valid_payload("ORDER_MANAGEMENT", "ORDER_MANAGEMENT.request.CANCEL_ENTRY_ORDER")

    parsed = parse_contract("ORDER_MANAGEMENT", payload)

    assert parsed.definition == "ORDER_MANAGEMENT.request.CANCEL_ENTRY_ORDER"


def test_nested_contract_values_reject_binary_float():
    payload = valid_payload("ORDER_SPEC", "ORDER_SPEC")
    payload["order_spec"]["entry"] = {"price": 751.10}

    with pytest.raises(ContractError, match="unsupported binary float"):
        validate_contract("ORDER_SPEC", payload)


def test_nested_unknown_fields_are_rejected_by_approved_schema():
    payload = valid_payload("MARKET_HANDOFF", "MARKET_HANDOFF")
    payload["market_handoff"]["instrument"]["unexpected"] = "x"

    with pytest.raises(ContractError, match="unknown fields: unexpected"):
        validate_contract("MARKET_HANDOFF", payload)


def test_nested_missing_required_fields_are_rejected_by_approved_schema():
    payload = valid_payload("ORDER_SPEC", "ORDER_SPEC")
    payload["order_spec"]["accounting_policy"] = {}

    with pytest.raises(ContractError, match="missing required fields"):
        validate_contract("ORDER_SPEC", payload)


def test_schema_max_items_restriction_is_rejected():
    payload = valid_payload("ORDER_EVENT", "ORDER_EVENT.logical")
    root = payload["order_event"]
    root["lifecycle_state"] = "CLOSED"
    root["exposure_qty"] = "0"
    root["remaining_entry_qty"] = "0"
    root["close_intent_active"] = False
    root["terminal_predicates"].update(
        {
            "logical_exposure_zero": True,
            "entry_remainder_terminal": True,
            "children_terminal_or_disabled": True,
            "close_intent_resolved": True,
            "financial_finality_established": True,
            "no_competing_execution_authority": True,
        }
    )
    root["financial_result"] = _value_for_schema(WIRE_SCHEMA["$defs"]["financial_result"])
    root["financial_result"]["source_coverage"]["missing_ranges"] = [
        {"from": "2026-09-14T00:00:00Z", "to": "2026-09-14T01:00:00Z"}
    ]

    with pytest.raises(ContractError, match="must have at most 0 items"):
        validate_contract("ORDER_EVENT", payload, definition="ORDER_EVENT.logical")


def test_nullability_is_preserved_for_json_compatible_payloads():
    payload = valid_payload("ORDER_MANAGEMENT", "ORDER_MANAGEMENT.response.operation")
    payload["order_management_response"]["client_order_link_id"] = None
    payload["order_management_response"]["exchange_order_id"] = None
    payload["order_management_response"]["position"] = None

    parsed = parse_contract("ORDER_MANAGEMENT", payload, definition="ORDER_MANAGEMENT.response.operation")

    assert parsed.to_payload()["order_management_response"]["client_order_link_id"] is None


def test_invalid_digest_field_is_rejected():
    payload = valid_payload("SUBMIT_AUTHORIZED", "SUBMIT_AUTHORIZED")
    payload["submit_authorized"]["order_spec_digest"] = "not-a-digest"

    with pytest.raises(ContractError, match="sha256 hex string"):
        validate_contract("SUBMIT_AUTHORIZED", payload)


def test_contract_digest_uses_canonical_json_foundation():
    payload = valid_payload("COINS", "COINS")
    parsed = parse_contract("COINS", payload)

    assert contract_digest(parsed) == canonical_json_digest(payload)
    assert contract_digest(parsed) == "ae7de1610440863f35c603c3ee7f5a938ab7816cac67c106e857442a459d6b30"


def test_schema_approved_optional_fields_are_accepted():
    portfolio = valid_payload("PORTFOLIO_DATA_REQUEST", "PORTFOLIO_DATA_REQUEST.response")
    portfolio["portfolio_data_response"]["account"] = _value_for_schema(
        WIRE_SCHEMA["$defs"]["PORTFOLIO_DATA_REQUEST.response"]["properties"]["portfolio_data_response"]["properties"]["account"]
    )
    portfolio["portfolio_data_response"]["positions"] = _value_for_schema(
        WIRE_SCHEMA["$defs"]["PORTFOLIO_DATA_REQUEST.response"]["properties"]["portfolio_data_response"]["properties"]["positions"]
    )
    validate_contract("PORTFOLIO_DATA_REQUEST", portfolio, definition="PORTFOLIO_DATA_REQUEST.response")

    market = valid_payload("MARKET_DATA_REQUEST", "MARKET_DATA_REQUEST.request")
    market["market_data_request"]["decision_cycle_id"] = None
    market["market_data_request"]["set_result_id"] = "set-result-1"
    validate_contract("MARKET_DATA_REQUEST", market, definition="MARKET_DATA_REQUEST.request")


def valid_payload(contract_type: str, definition: str) -> dict[str, object]:
    spec = get_contract_definition(contract_type, definition=definition)
    payload = _value_for_schema(WIRE_SCHEMA["$defs"][definition])
    payload[spec.top_key]["contract_version"] = spec.version
    for field in spec.digest_fields:
        payload[spec.top_key][field] = "a" * 64
    return payload


def _value_for_schema(schema: dict[str, object]):
    if "$ref" in schema:
        return _value_for_schema(WIRE_SCHEMA["$defs"][schema["$ref"].removeprefix("#/$defs/")])
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return schema["enum"][0]
    if "anyOf" in schema:
        choices = schema["anyOf"]
        null_choices = [choice for choice in choices if choice.get("type") == "null"]
        if null_choices:
            return None
        non_null = [choice for choice in choices if choice.get("type") != "null"]
        return _value_for_schema(non_null[0] if non_null else choices[0])

    schema_type = schema.get("type")
    if schema_type == "object":
        value = {
            field: _value_for_schema(schema["properties"][field])
            for field in schema.get("required", [])
        }
        if not value and schema.get("minProperties", 0) > 0 and schema.get("properties"):
            first_property = next(iter(schema["properties"]))
            value[first_property] = _value_for_schema(schema["properties"][first_property])
        if set(value) >= {"dataset", "mode", "range_from", "range_to", "completed_only", "timeframe", "count"}:
            value.update(
                {
                    "dataset": "TICKER",
                    "mode": "AS_OF",
                    "range_from": None,
                    "range_to": None,
                    "completed_only": False,
                    "timeframe": None,
                    "count": None,
                }
            )
        if set(value) >= {"entry_acceptance_status", "entry_accepted_at", "entry_acceptance_provenance"}:
            value["entry_acceptance_status"] = "NOT_APPLICABLE"
            value["entry_accepted_at"] = None
            value["entry_acceptance_provenance"] = None
        if set(value) >= {"enabled", "status"}:
            value["enabled"] = False
            value["status"] = "NOT_APPLICABLE"
        if set(value) >= {"minimum_net_edge_enabled", "minimum_net_edge_result"}:
            value["minimum_net_edge_enabled"] = False
            value["minimum_net_edge_result"] = "NOT_APPLICABLE"
        return value
    if schema_type == "array":
        min_items = schema.get("minItems", 0)
        if min_items:
            return [_value_for_schema(schema["items"])]
        return []
    if schema_type == "integer":
        return schema.get("minimum", 1)
    if schema_type == "boolean":
        return False
    if schema_type == "null":
        return None
    if schema_type == "string":
        if schema.get("format") == "date-time":
            return "2026-09-14T00:00:00Z"
        pattern = schema.get("pattern", "")
        if "[0-9a-f]{64}" in pattern:
            return "a" * 64
        if "\\." in pattern or "[0-9]" in pattern:
            return "1"
        return "value"
    raise AssertionError(f"unsupported fixture schema: {schema}")
