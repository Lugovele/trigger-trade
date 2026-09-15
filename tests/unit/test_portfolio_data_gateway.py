from __future__ import annotations

from decimal import Decimal

import pytest

from triggertrade.api_adapter_gateway import (
    PortfolioDataGatewayError,
    build_portfolio_data_request,
    build_portfolio_data_response,
    fee_rate_item,
    instrument_metadata_item,
    portfolio_account_section,
    portfolio_position_item,
)


NOW = "2026-09-14T00:00:00Z"


def test_snapshot_request_requires_symbols_for_symbol_scoped_sections():
    parsed = build_portfolio_data_request(
        request_id="pdr-1",
        requested_at=NOW,
        scope={"account": True, "instrument_metadata": True, "fee_rates": True},
        symbols=("BTCUSDT", "ETHUSDT"),
    )

    payload = parsed.to_payload()["portfolio_data_request"]
    assert payload["contract_version"] == 5
    assert payload["scope"]["account"] is True
    assert payload["scope"]["positions"] is False
    assert payload["filters"]["symbols"] == ["BTCUSDT", "ETHUSDT"]

    with pytest.raises(PortfolioDataGatewayError, match="require explicit symbols"):
        build_portfolio_data_request(
            request_id="pdr-2",
            requested_at=NOW,
            scope={"instrument_metadata": True},
            symbols=(),
        )


def test_portfolio_response_builds_strict_account_position_and_symbol_sections():
    account = portfolio_account_section(
        status="AVAILABLE",
        as_of=NOW,
        source_endpoint="/v5/account/wallet-balance",
        account_id="UNIFIED",
        equity=Decimal("100.25"),
        wallet_balance="99.75",
        available_balance=90,
        unrealized_pnl="0.50",
        realized_pnl=None,
    )
    positions = {
        "status": "AVAILABLE",
        "as_of": NOW,
        "source_endpoint": "/v5/position/list",
        "coverage": None,
        "items": [
            portfolio_position_item(
                symbol="BTCUSDT",
                side="BUY",
                position_idx=1,
                size="0.01",
                avg_entry_price="65000",
                mark_price="65100",
                position_value="650",
                unrealized_pnl="1",
                realized_pnl="0",
            )
        ],
    }
    instrument = {
        "status": "AVAILABLE",
        "items": [
            instrument_metadata_item(
                symbol="BTCUSDT",
                status="AVAILABLE",
                facts=_instrument_facts("BTCUSDT", NOW),
                as_of=NOW,
                source_endpoint="/v5/market/instruments-info",
                source_record_id="linear:BTCUSDT",
                reason_code=None,
            )
        ],
    }
    fees = {
        "status": "AVAILABLE",
        "items": [
            fee_rate_item(
                symbol="BTCUSDT",
                status="AVAILABLE",
                facts=_fee_facts(NOW),
                as_of=NOW,
                source_endpoint="/v5/account/fee-rate",
                source_record_id="linear:BTCUSDT",
                reason_code=None,
            )
        ],
    }

    parsed = build_portfolio_data_response(
        request_id="pdr-1",
        response_id="pdr-res-1",
        request_mode="SNAPSHOT",
        snapshot_started_at=NOW,
        snapshot_completed_at=NOW,
        as_of=NOW,
        account=account,
        positions=positions,
        instrument_metadata=instrument,
        fee_rates=fees,
        requested_symbols=("BTCUSDT",),
    )

    payload = parsed.to_payload()["portfolio_data_response"]
    assert payload["source"] == "exchange_api"
    assert payload["account"]["equity"] == "100.25"
    assert payload["positions"]["items"][0]["size"] == "0.01"
    assert payload["instrument_metadata"]["items"][0]["facts"]["max_order_qty_source_field"] == "lotSizeFilter.maxOrderQty"
    assert payload["fee_rates"]["items"][0]["facts"]["fee_schedule_version"] == "bybit-demo-linear-fees"


def test_symbol_sections_must_exactly_cover_requested_symbols():
    instrument = {
        "status": "AVAILABLE",
        "items": [
            instrument_metadata_item(
                symbol="BTCUSDT",
                status="AVAILABLE",
                facts=_instrument_facts("BTCUSDT", NOW),
                as_of=NOW,
                source_endpoint="/v5/market/instruments-info",
                source_record_id="linear:BTCUSDT",
                reason_code=None,
            )
        ],
    }

    with pytest.raises(PortfolioDataGatewayError, match="exactly cover requested symbols"):
        build_portfolio_data_response(
            request_id="pdr-1",
            response_id="pdr-res-1",
            request_mode="SNAPSHOT",
            snapshot_started_at=NOW,
            snapshot_completed_at=NOW,
            as_of=NOW,
            instrument_metadata=instrument,
            requested_symbols=("BTCUSDT", "ETHUSDT"),
        )


def test_symbol_sections_reject_incorrect_aggregate_status_and_fact_state():
    available_item = instrument_metadata_item(
        symbol="BTCUSDT",
        status="AVAILABLE",
        facts=_instrument_facts("BTCUSDT", NOW),
        as_of=NOW,
        source_endpoint="/v5/market/instruments-info",
        source_record_id="linear:BTCUSDT",
        reason_code=None,
    )
    unavailable_item = instrument_metadata_item(
        symbol="ETHUSDT",
        status="UNAVAILABLE",
        facts=None,
        as_of=NOW,
        source_endpoint="/v5/market/instruments-info",
        source_record_id="linear:ETHUSDT",
        reason_code="SOURCE_UNAVAILABLE",
    )

    with pytest.raises(PortfolioDataGatewayError, match="status must be PARTIAL"):
        build_portfolio_data_response(
            request_id="pdr-1",
            response_id="pdr-res-1",
            request_mode="SNAPSHOT",
            snapshot_started_at=NOW,
            snapshot_completed_at=NOW,
            as_of=NOW,
            instrument_metadata={"status": "AVAILABLE", "items": [available_item, unavailable_item]},
            requested_symbols=("BTCUSDT", "ETHUSDT"),
        )

    broken_available = dict(available_item)
    broken_available["facts"] = None
    with pytest.raises(PortfolioDataGatewayError, match="AVAILABLE item requires facts"):
        build_portfolio_data_response(
            request_id="pdr-1",
            response_id="pdr-res-1",
            request_mode="SNAPSHOT",
            snapshot_started_at=NOW,
            snapshot_completed_at=NOW,
            as_of=NOW,
            instrument_metadata={"status": "AVAILABLE", "items": [broken_available]},
            requested_symbols=("BTCUSDT",),
        )

    broken_unavailable = dict(unavailable_item)
    broken_unavailable["facts"] = _instrument_facts("ETHUSDT", NOW)
    with pytest.raises(PortfolioDataGatewayError, match="UNAVAILABLE item facts must be null"):
        build_portfolio_data_response(
            request_id="pdr-1",
            response_id="pdr-res-1",
            request_mode="SNAPSHOT",
            snapshot_started_at=NOW,
            snapshot_completed_at=NOW,
            as_of=NOW,
            instrument_metadata={"status": "UNAVAILABLE", "items": [broken_unavailable]},
            requested_symbols=("ETHUSDT",),
        )

    broken_as_of = dict(available_item)
    broken_as_of["facts"] = {**_instrument_facts("BTCUSDT", NOW), "as_of": "2026-09-14T00:01:00Z"}
    with pytest.raises(PortfolioDataGatewayError, match="facts.as_of must equal item as_of"):
        build_portfolio_data_response(
            request_id="pdr-1",
            response_id="pdr-res-1",
            request_mode="SNAPSHOT",
            snapshot_started_at=NOW,
            snapshot_completed_at=NOW,
            as_of=NOW,
            instrument_metadata={"status": "AVAILABLE", "items": [broken_as_of]},
            requested_symbols=("BTCUSDT",),
        )


def test_unknown_fields_and_binary_float_values_are_rejected_by_contract_validation():
    account = portfolio_account_section(
        status="AVAILABLE",
        as_of=NOW,
        source_endpoint="/v5/account/wallet-balance",
        account_id="UNIFIED",
        equity="100",
        wallet_balance="100",
        available_balance="90",
        unrealized_pnl="0",
        realized_pnl="0",
    )
    account["unexpected"] = "x"

    with pytest.raises(PortfolioDataGatewayError, match="unknown fields: unexpected"):
        build_portfolio_data_response(
            request_id="pdr-1",
            response_id="pdr-res-1",
            request_mode="SNAPSHOT",
            snapshot_started_at=NOW,
            snapshot_completed_at=NOW,
            as_of=NOW,
            account=account,
        )

    with pytest.raises(PortfolioDataGatewayError, match="exact decimal string"):
        portfolio_account_section(
            status="AVAILABLE",
            as_of=NOW,
            source_endpoint="/v5/account/wallet-balance",
            account_id="UNIFIED",
            equity=100.0,
            wallet_balance="100",
            available_balance="90",
            unrealized_pnl="0",
            realized_pnl="0",
        )


def test_unavailable_symbol_fact_requires_reason_and_null_facts():
    instrument = {
        "status": "UNAVAILABLE",
        "items": [
            instrument_metadata_item(
                symbol="BTCUSDT",
                status="UNAVAILABLE",
                facts=None,
                as_of=NOW,
                source_endpoint="/v5/market/instruments-info",
                source_record_id="linear:BTCUSDT",
                reason_code="SOURCE_UNAVAILABLE",
            )
        ],
    }

    parsed = build_portfolio_data_response(
        request_id="pdr-1",
        response_id="pdr-res-1",
        request_mode="SNAPSHOT",
        snapshot_started_at=NOW,
        snapshot_completed_at=NOW,
        as_of=NOW,
        instrument_metadata=instrument,
        requested_symbols=("BTCUSDT",),
    )

    assert parsed.to_payload()["portfolio_data_response"]["instrument_metadata"]["items"][0]["facts"] is None


def _instrument_facts(symbol: str, as_of: str) -> dict[str, object]:
    return {
        "tick_size": "0.1",
        "qty_step": "0.001",
        "min_order_qty": "0.001",
        "min_notional": "5",
        "max_order_qty": "100",
        "max_order_qty_status": "AVAILABLE",
        "max_order_qty_source_field": "lotSizeFilter.maxOrderQty",
        "max_leverage": "50",
        "contract_type": "LINEAR_USDT_PERPETUAL",
        "metadata_revision": f"instrument:{symbol}:1",
        "native_profile_revision": "bybit-demo-linear-profile-v1",
        "instrument_supported": True,
        "position_mode": "HEDGE_MODE",
        "margin_mode": "ISOLATED",
        "as_of": as_of,
        "source_ref": f"linear:{symbol}",
    }


def _fee_facts(as_of: str) -> dict[str, object]:
    return {
        "maker_fee_rate": "0.0002",
        "taker_fee_rate": "0.00055",
        "fee_schedule_version": "bybit-demo-linear-fees",
        "effective_at": as_of,
        "as_of": as_of,
        "source_ref": "fee-rate:BTCUSDT",
    }
