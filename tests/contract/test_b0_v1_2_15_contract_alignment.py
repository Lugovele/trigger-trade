from __future__ import annotations

import pytest

from triggertrade.contracts import (
    APPROVED_PACKAGE_REVISION,
    ContractError,
    implemented_contract_registry,
    parse_contract,
)
from triggertrade.contracts._approved_wire_schema import WIRE_SCHEMA
from tests.unit.test_portfolio_data_gateway import NOW, _fee_facts, _instrument_facts


EXPECTED_FAMILY_VERSIONS = {
    "COINS": 2,
    "MARKET_HANDOFF": 4,
    "APPROVE_REJECT": 5,
    "CAPITAL_AND_LIMITS": 5,
    "ORDER_SPEC": 5,
    "SUBMIT_AUTHORIZED": 5,
    "ORDER_EVENT": 7,
    "ORDER_PLACED": 3,
    "ORDER_CANCEL_SIGNAL": 2,
    "PORTFOLIO_DATA_REQUEST": 5,
    "MARKET_DATA_REQUEST": 3,
    "ORDER_MANAGEMENT": 4,
}


def test_active_package_revision_and_family_versions_match_frozen_v1_2_15():
    registry = implemented_contract_registry()

    assert APPROVED_PACKAGE_REVISION == "v1.2.15"
    assert WIRE_SCHEMA["$id"] == "https://triggertrade.invalid/spec/v1.2.15/wire.schema.json"
    assert WIRE_SCHEMA["title"] == "TriggerTrade v1.2.15 strict wire contracts"
    assert set(registry) == set(EXPECTED_FAMILY_VERSIONS)
    assert {family: item["version"] for family, item in registry.items()} == EXPECTED_FAMILY_VERSIONS


def test_unknown_family_and_version_are_rejected_by_public_parser():
    with pytest.raises(ContractError, match="unknown contract type"):
        parse_contract("UNKNOWN", {})

    payload = _invalidation_payload()
    payload["order_cancel_signal"]["contract_version"] = 1
    with pytest.raises(ContractError, match="contract_version"):
        parse_contract("ORDER_CANCEL_SIGNAL", payload)


def test_order_cancel_signal_public_parser_accepts_valid_invalidation():
    parsed = parse_contract("ORDER_CANCEL_SIGNAL", _invalidation_payload())

    assert parsed.definition == "ORDER_CANCEL_SIGNAL"


def test_order_cancel_signal_public_parser_accepts_valid_monitoring_unavailable():
    parsed = parse_contract("ORDER_CANCEL_SIGNAL", _monitoring_unavailable_payload())

    root = parsed.to_payload()["order_cancel_signal"]
    assert root["signal_id"] == root["unavailable_requirement_id"]


@pytest.mark.parametrize("field", ("invalidated_at", "reason_code", "condition_record_id", "condition_id", "evidence_digest"))
def test_order_cancel_signal_public_parser_rejects_invalidation_missing_required_branch_field(field):
    payload = _invalidation_payload()
    del payload["order_cancel_signal"][field]

    with pytest.raises(ContractError):
        parse_contract("ORDER_CANCEL_SIGNAL", payload)


@pytest.mark.parametrize("field", ("unavailable_requirement_id", "unavailable_at", "unavailable_reason_code"))
def test_order_cancel_signal_public_parser_rejects_monitoring_unavailable_missing_required_branch_field(field):
    payload = _monitoring_unavailable_payload()
    del payload["order_cancel_signal"][field]

    with pytest.raises(ContractError):
        parse_contract("ORDER_CANCEL_SIGNAL", payload)


@pytest.mark.parametrize("field", ("unavailable_requirement_id", "unavailable_at", "unavailable_reason_code"))
def test_order_cancel_signal_public_parser_rejects_invalidation_with_unavailable_only_field(field):
    payload = _invalidation_payload()
    payload["order_cancel_signal"][field] = "2026-09-14T00:00:00Z" if field.endswith("_at") else "value"

    with pytest.raises(ContractError):
        parse_contract("ORDER_CANCEL_SIGNAL", payload)


@pytest.mark.parametrize("field", ("invalidated_at", "reason_code", "condition_id", "evidence_digest"))
def test_order_cancel_signal_public_parser_rejects_monitoring_unavailable_with_invalidation_only_field(field):
    payload = _monitoring_unavailable_payload()
    payload["order_cancel_signal"][field] = "2026-09-14T00:00:00Z" if field.endswith("_at") else "value"

    with pytest.raises(ContractError):
        parse_contract("ORDER_CANCEL_SIGNAL", payload)


def test_order_cancel_signal_public_parser_accepts_monitoring_unavailable_optional_condition_record_id():
    payload = _monitoring_unavailable_payload()
    payload["order_cancel_signal"]["condition_record_id"] = "condition-record-1"

    parsed = parse_contract("ORDER_CANCEL_SIGNAL", payload)

    assert parsed.to_payload()["order_cancel_signal"]["condition_record_id"] == "condition-record-1"


def test_order_cancel_signal_public_parser_rejects_unknown_cause_and_unavailable_identity_mismatch():
    payload = _monitoring_unavailable_payload()
    payload["order_cancel_signal"]["cause"] = "UNKNOWN"
    with pytest.raises(ContractError, match="cause"):
        parse_contract("ORDER_CANCEL_SIGNAL", payload)

    payload = _monitoring_unavailable_payload()
    payload["order_cancel_signal"]["unavailable_requirement_id"] = "different"
    with pytest.raises(ContractError, match="signal_id"):
        parse_contract("ORDER_CANCEL_SIGNAL", payload)


@pytest.mark.parametrize("section", ("instrument_metadata", "fee_rates"))
@pytest.mark.parametrize("status", ("AVAILABLE", "UNAVAILABLE"))
def test_portfolio_data_public_parser_accepts_binary_symbol_fact_item_statuses(section, status):
    response = _portfolio_response_payload(section, (status,))

    parsed = parse_contract("PORTFOLIO_DATA_REQUEST", response, definition="PORTFOLIO_DATA_REQUEST.response")

    assert parsed.to_payload()["portfolio_data_response"][section]["items"][0]["status"] == status


@pytest.mark.parametrize("section", ("instrument_metadata", "fee_rates"))
def test_portfolio_data_public_parser_rejects_partial_symbol_fact_item_status(section):
    response = _portfolio_response_payload(section, ("PARTIAL",))

    with pytest.raises(ContractError, match="AVAILABLE.*UNAVAILABLE"):
        parse_contract("PORTFOLIO_DATA_REQUEST", response, definition="PORTFOLIO_DATA_REQUEST.response")


@pytest.mark.parametrize("section", ("instrument_metadata", "fee_rates"))
def test_portfolio_data_public_parser_accepts_mixed_binary_items_with_partial_aggregate(section):
    response = _portfolio_response_payload(section, ("AVAILABLE", "UNAVAILABLE"))

    parsed = parse_contract("PORTFOLIO_DATA_REQUEST", response, definition="PORTFOLIO_DATA_REQUEST.response")

    body = parsed.to_payload()["portfolio_data_response"][section]
    assert body["status"] == "PARTIAL"
    assert [item["symbol"] for item in body["items"]] == ["BTCUSDT", "ETHUSDT"]


@pytest.mark.parametrize("section", ("instrument_metadata", "fee_rates"))
def test_portfolio_data_public_parser_rejects_duplicate_symbol_rows(section):
    response = _portfolio_response_payload(section, ("AVAILABLE", "UNAVAILABLE"))
    response["portfolio_data_response"][section]["items"][1]["symbol"] = "BTCUSDT"

    with pytest.raises(ContractError, match="duplicate symbols"):
        parse_contract("PORTFOLIO_DATA_REQUEST", response, definition="PORTFOLIO_DATA_REQUEST.response")


def test_portfolio_data_request_rejects_duplicate_or_empty_symbol_scope_for_symbol_sections():
    request = _portfolio_request_payload(symbols=["BTCUSDT", "BTCUSDT"])
    with pytest.raises(ContractError, match="unique"):
        parse_contract("PORTFOLIO_DATA_REQUEST", request, definition="PORTFOLIO_DATA_REQUEST.request")

    request = _portfolio_request_payload(symbols=[])
    with pytest.raises(ContractError, match="nonempty"):
        parse_contract("PORTFOLIO_DATA_REQUEST", request, definition="PORTFOLIO_DATA_REQUEST.request")

    account_only = _portfolio_request_payload(symbols=[], instrument_metadata=False, fee_rates=False)
    parsed = parse_contract("PORTFOLIO_DATA_REQUEST", account_only, definition="PORTFOLIO_DATA_REQUEST.request")
    assert parsed.to_payload()["portfolio_data_request"]["filters"]["symbols"] == []


def test_schema_constructs_used_by_frozen_package_are_enforced_through_public_parser():
    payload = _invalidation_payload()
    payload["order_cancel_signal"]["unavailable_requirement_id"] = "forbidden-by-not"
    with pytest.raises(ContractError):
        parse_contract("ORDER_CANCEL_SIGNAL", payload)

    request = _portfolio_request_payload(symbols=[""])
    with pytest.raises(ContractError, match="empty"):
        parse_contract("PORTFOLIO_DATA_REQUEST", request, definition="PORTFOLIO_DATA_REQUEST.request")

    request = _portfolio_request_payload(symbols=["BTCUSDT"])
    request["portfolio_data_request"]["requested_at"] = "not-a-date"
    with pytest.raises(ContractError, match="date-time"):
        parse_contract("PORTFOLIO_DATA_REQUEST", request, definition="PORTFOLIO_DATA_REQUEST.request")


def _invalidation_payload() -> dict[str, object]:
    return {
        "order_cancel_signal": {
            "contract_version": 2,
            "cause": "INVALIDATION",
            "signal_id": "cancel-signal-1",
            "decision_cycle_id": "cycle-1",
            "set_result_id": "set-result-1",
            "tranche_id": "tranche-1",
            "symbol": "BTCUSDT",
            "invalidated_at": NOW,
            "reason_code": "ENTRY_PRICE_INVALIDATED",
            "condition_record_id": "condition-record-1",
            "condition_id": "condition-1",
            "evidence_digest": "0" * 64,
        }
    }


def _monitoring_unavailable_payload() -> dict[str, object]:
    return {
        "order_cancel_signal": {
            "contract_version": 2,
            "cause": "MONITORING_UNAVAILABLE",
            "signal_id": "unavailable-requirement-1",
            "decision_cycle_id": "cycle-1",
            "set_result_id": "set-result-1",
            "tranche_id": "tranche-1",
            "symbol": "BTCUSDT",
            "unavailable_requirement_id": "unavailable-requirement-1",
            "unavailable_at": NOW,
            "unavailable_reason_code": "REQUIRED_EVIDENCE_UNAVAILABLE",
        }
    }


def _portfolio_request_payload(
    *,
    symbols: list[str],
    instrument_metadata: bool = True,
    fee_rates: bool = False,
) -> dict[str, object]:
    scope = {
        "account": not instrument_metadata and not fee_rates,
        "wallet": False,
        "positions": False,
        "open_orders": False,
        "recent_orders": False,
        "executions": False,
        "fees": False,
        "funding": False,
        "realized_pnl": False,
        "unrealized_pnl": False,
        "instrument_metadata": instrument_metadata,
        "fee_rates": fee_rates,
        "cashflows": False,
    }
    return {
        "portfolio_data_request": {
            "contract_version": 5,
            "request_id": "pdr-1",
            "requested_at": NOW,
            "request_mode": "SNAPSHOT",
            "scope": scope,
            "filters": {"symbols": symbols, "since": None, "until": None},
        }
    }


def _portfolio_response_payload(section: str, statuses: tuple[str, ...]) -> dict[str, object]:
    return {
        "portfolio_data_response": {
            "contract_version": 5,
            "request_id": "pdr-1",
            "response_id": "pdr-response-1",
            "request_mode": "SNAPSHOT",
            "response_consistency": {"mode": "COMPOSITE"},
            "snapshot_started_at": NOW,
            "snapshot_completed_at": NOW,
            "as_of": NOW,
            "source": "exchange_api",
            section: {
                "status": _aggregate_status(statuses),
                "items": [_symbol_item(section, symbol, status) for symbol, status in zip(("BTCUSDT", "ETHUSDT"), statuses)],
            },
        }
    }


def _symbol_item(section: str, symbol: str, status: str) -> dict[str, object]:
    return {
        "symbol": symbol,
        "status": status,
        "facts": _symbol_facts(section, symbol) if status == "AVAILABLE" else None,
        "as_of": NOW,
        "source_endpoint": "/v5/account/fee-rate" if section == "fee_rates" else "/v5/market/instruments-info",
        "source_record_id": f"linear:{symbol}",
        "reason_code": None if status == "AVAILABLE" else "SOURCE_UNAVAILABLE",
    }


def _symbol_facts(section: str, symbol: str) -> dict[str, object]:
    if section == "instrument_metadata":
        return _instrument_facts(symbol, NOW)
    return _fee_facts(NOW)


def _aggregate_status(statuses: tuple[str, ...]) -> str:
    unique = set(statuses)
    if unique == {"AVAILABLE"}:
        return "AVAILABLE"
    if unique == {"UNAVAILABLE"}:
        return "UNAVAILABLE"
    return "PARTIAL"
