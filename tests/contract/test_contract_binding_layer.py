from __future__ import annotations

import pytest

from triggertrade.contracts import (
    ContractBindingError,
    ContractType,
    approved_contract_graph,
    contract_body,
    contract_digest,
    parse_contract,
    require_digest_binding,
    require_expected_fields,
    require_matching_fields,
    validate_contract_edge,
    validate_order_spec_construction_binding,
    validate_position_config_pin_binding,
)
from triggertrade.position_config_pins import (
    build_position_config_pin,
    position_rules_content_digest,
)
from tests.unit.test_capital_grants import build_grant
from tests.unit.test_order_specs import valid_order_spec
from tests.unit.test_position_config_pins import market_handoff, rules_version
from tests.unit.test_position_construction import constructed_result
from tests.unit.test_target_contracts import valid_payload


def test_b4_approved_graph_covers_all_twelve_families_without_position_api_edge():
    graph = approved_contract_graph()

    assert {edge.contract_type for edge in graph} == set(ContractType)
    assert not any(
        {edge.producer.value, edge.consumer.value} == {"Position", "API"}
        for edge in graph
    )


def test_b4_approved_graph_matches_frozen_edge_matrix():
    actual = {
        (edge.producer.value, edge.consumer.value, edge.contract_type.value, edge.version, edge.definitions)
        for edge in approved_contract_graph()
    }

    assert actual == {
        ("Portfolio", "Set", "COINS", 2, ("COINS",)),
        ("Set", "Position", "MARKET_HANDOFF", 4, ("MARKET_HANDOFF",)),
        ("Position", "Portfolio", "APPROVE_REJECT", 5, ("APPROVE_REJECT.initial", "APPROVE_REJECT.constructed", "APPROVE_REJECT.failed")),
        ("Portfolio", "Position", "CAPITAL_AND_LIMITS", 5, ("CAPITAL_AND_LIMITS",)),
        ("Position", "Lifecycle", "ORDER_SPEC", 5, ("ORDER_SPEC",)),
        ("Portfolio", "Lifecycle", "SUBMIT_AUTHORIZED", 5, ("SUBMIT_AUTHORIZED",)),
        (
            "Lifecycle",
            "Portfolio",
            "ORDER_EVENT",
            7,
            (
                "ORDER_EVENT.logical",
                "ORDER_EVENT.native",
                "ORDER_EVENT.resolution",
                "ORDER_EVENT.scope_observation",
                "ORDER_EVENT.scope_resolution",
                "ORDER_EVENT.integrity",
            ),
        ),
        ("Lifecycle", "Set", "ORDER_PLACED", 3, ("ORDER_PLACED.placed", "ORDER_PLACED.terminal")),
        ("Set", "Lifecycle", "ORDER_CANCEL_SIGNAL", 2, ("ORDER_CANCEL_SIGNAL",)),
        ("Portfolio", "API", "PORTFOLIO_DATA_REQUEST", 5, ("PORTFOLIO_DATA_REQUEST.request",)),
        ("API", "Portfolio", "PORTFOLIO_DATA_REQUEST", 5, ("PORTFOLIO_DATA_REQUEST.response",)),
        ("Set", "API", "MARKET_DATA_REQUEST", 3, ("MARKET_DATA_REQUEST.request",)),
        ("API", "Set", "MARKET_DATA_REQUEST", 3, ("MARKET_DATA_REQUEST.response",)),
        (
            "Lifecycle",
            "API",
            "ORDER_MANAGEMENT",
            4,
            (
                "ORDER_MANAGEMENT.request.CREATE_ENTRY_ORDER",
                "ORDER_MANAGEMENT.request.CANCEL_ENTRY_ORDER",
                "ORDER_MANAGEMENT.request.GET_ORDER",
                "ORDER_MANAGEMENT.request.GET_OPEN_ORDERS",
                "ORDER_MANAGEMENT.request.GET_ORDER_HISTORY",
                "ORDER_MANAGEMENT.request.GET_EXECUTIONS",
                "ORDER_MANAGEMENT.request.GET_POSITION",
                "ORDER_MANAGEMENT.request.SET_OR_ATTACH_TP_SL",
                "ORDER_MANAGEMENT.request.CANCEL_PROTECTIVE_ORDER",
                "ORDER_MANAGEMENT.request.CLOSE_POSITION_QUANTITY",
                "ORDER_MANAGEMENT.request.GET_ACCOUNT_EXECUTION_FACTS",
                "ORDER_MANAGEMENT.request.GET_FINANCIAL_FACTS",
                "ORDER_MANAGEMENT.request.GET_HARD_EXECUTION_FACTS",
            ),
        ),
        (
            "API",
            "Lifecycle",
            "ORDER_MANAGEMENT",
            4,
            ("ORDER_MANAGEMENT.response.financial", "ORDER_MANAGEMENT.response.hard", "ORDER_MANAGEMENT.response.operation"),
        ),
    }


@pytest.mark.parametrize(
    ("producer", "consumer", "contract_type", "definition"),
    [
        (edge.producer.value, edge.consumer.value, edge.contract_type.value, definition)
        for edge in approved_contract_graph()
        for definition in edge.definitions
    ],
)
def test_b4_all_approved_contract_edges_validate_through_public_parser(producer, consumer, contract_type, definition):
    payload = valid_payload(contract_type, definition)

    parsed = validate_contract_edge(
        producer=producer,
        consumer=consumer,
        contract_type=contract_type,
        payload=payload,
        definition=definition,
    )

    assert parsed.definition == definition
    assert parsed.to_payload() == payload


def test_b4_rejects_unapproved_position_api_edge_even_with_valid_api_payload():
    payload = valid_payload("MARKET_DATA_REQUEST", "MARKET_DATA_REQUEST.request")

    with pytest.raises(ContractBindingError, match="Position -> API"):
        validate_contract_edge(
            producer="Position",
            consumer="API",
            contract_type="MARKET_DATA_REQUEST",
            payload=payload,
            definition="MARKET_DATA_REQUEST.request",
        )


def test_b4_rejects_wrong_consumer_for_valid_contract_family():
    payload = valid_payload("ORDER_SPEC", "ORDER_SPEC")

    with pytest.raises(ContractBindingError, match="ORDER_SPEC"):
        validate_contract_edge(
            producer="Position",
            consumer="Portfolio",
            contract_type="ORDER_SPEC",
            payload=payload,
            definition="ORDER_SPEC",
        )


def test_b4_rejects_wrong_contract_stage_for_successful_ids():
    initial_decision = valid_payload("APPROVE_REJECT", "APPROVE_REJECT.initial")
    order_spec = valid_order_spec(build_grant())

    with pytest.raises(ContractBindingError, match="APPROVE_REJECT.constructed"):
        validate_order_spec_construction_binding(
            construction_result=initial_decision,
            order_spec=order_spec,
        )


def test_b4_exact_lineage_does_not_accept_similar_symbol_or_latest_record_substitution():
    accepted = {
        "decision_cycle_id": "cycle-1",
        "set_result_id": "set-result-1",
        "symbol": "BTCUSDT",
    }

    require_expected_fields(
        payload_name="market_handoff",
        payload=accepted,
        expected=accepted,
    )

    similar_symbol_time_record = {
        "decision_cycle_id": "cycle-2",
        "set_result_id": "set-result-2",
        "symbol": "BTCUSDT",
    }
    with pytest.raises(ContractBindingError, match="decision_cycle_id"):
        require_expected_fields(
            payload_name="market_handoff",
            payload=similar_symbol_time_record,
            expected=accepted,
        )


def test_b4_contract_body_rejects_preparsed_wrong_family_or_stage():
    parsed_coins = parse_contract("COINS", valid_payload("COINS", "COINS"))

    with pytest.raises(ContractBindingError, match="does not match requested ORDER_SPEC"):
        contract_body(parsed_coins, contract_type="ORDER_SPEC", definition="ORDER_SPEC")

    parsed_initial = parse_contract(
        "APPROVE_REJECT",
        valid_payload("APPROVE_REJECT", "APPROVE_REJECT.initial"),
        definition="APPROVE_REJECT.initial",
    )
    with pytest.raises(ContractBindingError, match="does not match requested APPROVE_REJECT.constructed"):
        contract_body(
            parsed_initial,
            contract_type="APPROVE_REJECT",
            definition="APPROVE_REJECT.constructed",
        )


def test_b4_binding_checks_reject_missing_fields_instead_of_equal_absence():
    with pytest.raises(ContractBindingError, match="source.tranche_id is required"):
        require_matching_fields(
            source_name="source",
            source={"decision_cycle_id": "cycle-1"},
            target_name="target",
            target={"decision_cycle_id": "cycle-1"},
            fields=("decision_cycle_id", "tranche_id"),
        )

    with pytest.raises(ContractBindingError, match="position_config_pin.configuration_version is required"):
        require_expected_fields(
            payload_name="position_config_pin",
            payload={"configuration_id": "rules-v1"},
            expected={"configuration_id": "rules-v1", "configuration_version": None},
        )


def test_b4_order_spec_binding_verifies_digest_and_duplicated_scalars_independently():
    grant = build_grant()
    order_spec = valid_order_spec(grant)
    construction = constructed_result(grant, order_spec_digest_value=contract_digest(order_spec))

    parsed = validate_order_spec_construction_binding(
        construction_result=construction,
        order_spec=order_spec,
    )

    assert parsed.to_payload() == order_spec

    changed_digest = constructed_result(grant, order_spec_digest_value="b" * 64)
    with pytest.raises(ContractBindingError, match="digest mismatch"):
        validate_order_spec_construction_binding(
            construction_result=changed_digest,
            order_spec=order_spec,
        )

    changed_scalar = valid_order_spec(grant)
    changed_scalar["order_spec"]["economics"]["actual_committed_capital"] = "101"
    changed_scalar_construction = constructed_result(grant, order_spec_digest_value=contract_digest(changed_scalar))
    with pytest.raises(ContractBindingError, match="approved_actual_committed_capital"):
        validate_order_spec_construction_binding(
            construction_result=changed_scalar_construction,
            order_spec=changed_scalar,
        )

    changed_lineage = valid_order_spec(grant)
    changed_lineage["order_spec"]["tranche_id"] = "tranche-from-latest-similar-record"
    changed_lineage_construction = constructed_result(grant, order_spec_digest_value=contract_digest(changed_lineage))
    with pytest.raises(ContractBindingError, match="tranche_id"):
        validate_order_spec_construction_binding(
            construction_result=changed_lineage_construction,
            order_spec=changed_lineage,
        )

    changed_gate = valid_order_spec(grant)
    changed_gate["order_spec"]["economics"]["planned_net_edge_pct"] = "0.03"
    changed_gate_construction = constructed_result(grant, order_spec_digest_value=contract_digest(changed_gate))
    with pytest.raises(ContractBindingError, match="calculated_value"):
        validate_order_spec_construction_binding(
            construction_result=changed_gate_construction,
            order_spec=changed_gate,
        )


def test_b4_rejects_self_referential_order_spec_digest_shortcut():
    order_spec = valid_order_spec(build_grant())
    order_spec["order_spec"]["order_spec_digest"] = contract_digest(order_spec)

    with pytest.raises(ContractBindingError, match="unknown fields"):
        validate_contract_edge(
            producer="Position",
            consumer="Lifecycle",
            contract_type="ORDER_SPEC",
            payload=order_spec,
            definition="ORDER_SPEC",
        )


def test_b4_digest_binding_uses_independent_canonical_payload_digest():
    payload = valid_payload("COINS", "COINS")

    require_digest_binding(
        payload_name="coins",
        payload=payload,
        supplied_digest=contract_digest(payload),
    )

    with pytest.raises(ContractBindingError, match="digest mismatch"):
        require_digest_binding(
            payload_name="coins",
            payload=payload,
            supplied_digest="0" * 64,
        )


def test_b4_position_config_pin_binding_preserves_historical_configuration_identity():
    handoff = market_handoff()
    rules = rules_version(version="v1")
    pin = build_position_config_pin(
        position_decision_id="position-decision-1",
        market_handoff=handoff,
        rules_version=rules,
        pinned_at="2026-09-15T10:00:00Z",
    )

    validate_position_config_pin_binding(
        pin_payload=pin.to_payload(),
        market_handoff=handoff,
        configuration_id=rules.rules_version_id,
        configuration_version=rules.version,
        configuration_content_digest=position_rules_content_digest(rules),
    )

    current_rules = rules_version(version="v2", rules_version_id="rules-v2")
    with pytest.raises(ContractBindingError, match="configuration_id"):
        validate_position_config_pin_binding(
            pin_payload=pin.to_payload(),
            market_handoff=handoff,
            configuration_id=current_rules.rules_version_id,
            configuration_version=current_rules.version,
            configuration_content_digest=position_rules_content_digest(current_rules),
        )

    with pytest.raises(ContractBindingError, match="configuration_version"):
        validate_position_config_pin_binding(
            pin_payload=pin.to_payload(),
            market_handoff=handoff,
            configuration_id=rules.rules_version_id,
            configuration_version="v2",
            configuration_content_digest=position_rules_content_digest(rules),
        )

    changed_content_rules = rules_version(version="v1", rules_version_id=rules.rules_version_id, leverage=rules.draft.leverage + 1)
    with pytest.raises(ContractBindingError, match="configuration_content_digest"):
        validate_position_config_pin_binding(
            pin_payload=pin.to_payload(),
            market_handoff=handoff,
            configuration_id=rules.rules_version_id,
            configuration_version=rules.version,
            configuration_content_digest=position_rules_content_digest(changed_content_rules),
        )
