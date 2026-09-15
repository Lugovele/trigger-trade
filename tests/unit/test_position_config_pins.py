from __future__ import annotations

from decimal import Decimal

import pytest

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.position_config_pins import (
    PositionConfigPinError,
    build_position_config_pin,
    position_config_pin_digest,
    position_rules_content_digest,
)
from triggertrade.rules.trading import TradingRulesVersion, TradingRulesVersionDraft, TakeProfitMode, DirectionMode, CoinRule
from tests.unit.test_target_contracts import valid_payload


def test_position_config_pin_binds_market_handoff_to_rules_version():
    handoff = market_handoff()
    rules = rules_version(version="v1")

    pin = build_position_config_pin(
        position_decision_id="position-decision-1",
        market_handoff=handoff,
        rules_version=rules,
        pinned_at="2026-09-15T10:00:00Z",
    )

    assert pin.decision_cycle_id == handoff["market_handoff"]["decision_cycle_id"]
    assert pin.set_result_id == handoff["market_handoff"]["set_result_id"]
    assert pin.symbol == handoff["market_handoff"]["symbol"].upper()
    assert pin.market_handoff_digest == canonical_json_digest(handoff)
    assert pin.configuration_id == rules.rules_version_id
    assert pin.configuration_version == "v1"
    assert pin.configuration_content_digest == position_rules_content_digest(rules)
    assert position_config_pin_digest(pin) == "720ffe67876c7f081d1be443adf0fa71b5283e49e85531c761c6b21c2b614550"


def test_position_config_pin_uses_canonical_content_not_current_pointer():
    first = rules_version(version="v1")
    later = rules_version(version="v2", rules_version_id="rules-v2", leverage=Decimal("3"))

    assert first.rules_version_id != later.rules_version_id
    assert position_rules_content_digest(first) != position_rules_content_digest(later)


def test_position_config_pin_rejects_invalid_handoff_and_digest():
    handoff = market_handoff()
    del handoff["market_handoff"]["set_result_id"]

    with pytest.raises(PositionConfigPinError, match="set_result_id"):
        build_position_config_pin(
            position_decision_id="position-decision-1",
            market_handoff=handoff,
            rules_version=rules_version(),
            pinned_at="2026-09-15T10:00:00Z",
        )


def market_handoff() -> dict[str, object]:
    return valid_payload("MARKET_HANDOFF", "MARKET_HANDOFF")


def rules_version(
    *,
    version: str = "v1",
    rules_version_id: str = "rules-v1",
    leverage: Decimal = Decimal("2"),
) -> TradingRulesVersion:
    draft = TradingRulesVersionDraft(
        position_size_pct=Decimal("0.05"),
        take_profit_mode=TakeProfitMode.FIXED,
        fixed_take_profit_pct=Decimal("0.03"),
        minimum_take_profit_pct=Decimal("0.03"),
        stop_loss_pct=Decimal("0.01"),
        minimum_risk_reward=Decimal("2"),
        minimum_net_edge_enabled=True,
        minimum_net_edge_pct=Decimal("0.01"),
        leverage=leverage,
        max_capital_in_positions_pct=Decimal("0.50"),
        max_open_positions_enabled=True,
        max_open_positions=3,
        max_positions_per_coin_enabled=True,
        max_positions_per_coin=1,
        direction_mode=DirectionMode.LONG_SHORT,
        daily_loss_limit_enabled=False,
        daily_loss_limit_pct=None,
        maker_fee_rate=Decimal("0.0002"),
        taker_fee_rate=Decimal("0.00055"),
        spread_cost=Decimal("0.0001"),
        slippage_cost=Decimal("0.0002"),
        funding_cost=Decimal("0.0001"),
        coins=(CoinRule("BTCUSDT", enabled=True, max_allocation_pct=None),),
        metadata={"source": "unit"},
    )
    return TradingRulesVersion(
        rules_version_id=rules_version_id,
        version=version,
        created_at="2026-09-15T09:00:00Z",
        created_from_version_id=None,
        created_source="unit",
        change_summary="unit fixture",
        config_hash="0" * 64,
        schema_version="trading-rules-v1",
        draft=draft,
        is_current=True,
    )
