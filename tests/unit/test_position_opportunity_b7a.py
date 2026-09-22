from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import os
import uuid

import pytest

from triggertrade.contracts import parse_contract
from triggertrade.contracts.bindings import validate_contract_edge
from triggertrade.position_config_pins import position_rules_content_digest
from triggertrade.persistence import (
    DurableMessageStore,
    PositionConfigPinStore,
    PositionOpportunityConflict,
    PositionOpportunityStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.position_rules import PositionOpportunityCommand, PositionOpportunityHandler
from triggertrade.rules.trading import TakeProfitMode, TradingRulesVersion, TradingRulesVersionDraft, DirectionMode, CoinRule
from tests.unit.test_target_contracts import valid_payload


NOW = "2026-09-15T10:00:00Z"


def test_b7a_dynamic_tp_is_independent_when_required_dynamic_stop_is_unavailable():
    command = command_for(
        handoff=handoff(
            reference_price="102",
            atr="10",
            tick="0.1",
            levels=[
                level("low-1", "SWING_LOW_15M", "100", "BELOW_REFERENCE"),
                level("high-1", "SWING_HIGH_15M", "110", "ABOVE_REFERENCE"),
            ],
        ),
        rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC, metadata={"stop_loss_mode": "DYNAMIC"}),
    )

    result = PositionOpportunityHandler().evaluate(command)
    state = result.to_state_payload()["position_opportunity_state"]
    evaluation = state["evaluation"]
    decision = result.decision.to_payload()["position_decision"]

    assert decision["decision"] == "REJECT"
    assert decision["construction_gates"] == "NOT_YET_EVALUATED"
    assert decision["opportunity_checks"] == {
        "configuration": "PASS",
        "set_direction": "PASS",
        "market_context": "PASS",
        "price_geometry": "UNAVAILABLE",
        "minimum_rr": "UNAVAILABLE",
    }
    assert evaluation["entry"]["price"] == "100"
    assert evaluation["entry"]["reference_level_id"] == "low-1"
    assert evaluation["stop"]["status"] == "UNAVAILABLE"
    assert evaluation["stop"]["reason_code"] == "NO_ELIGIBLE_REFERENCE"
    assert evaluation["take_profit"]["status"] == "AVAILABLE"
    assert evaluation["take_profit"]["price"] == "110"
    assert evaluation["take_profit"]["reference_level_id"] == "high-1"
    assert "capital_grant_id" not in decision
    assert "position_plan_id" not in decision
    parse_contract("APPROVE_REJECT", result.decision.to_payload(), definition="APPROVE_REJECT.initial")


def test_b7a_initial_approve_requires_exact_gross_risk_reward_boundary():
    command = command_for(
        handoff=handoff(
            reference_price="102",
            atr="10",
            tick="0.1",
            levels=[
                level("low-1", "SWING_LOW_15M", "100", "BELOW_REFERENCE"),
                level("high-1", "SWING_HIGH_15M", "110", "ABOVE_REFERENCE"),
            ],
        ),
        rules=rules_version(
            take_profit_mode=TakeProfitMode.DYNAMIC,
            stop_loss_pct=Decimal("0.05"),
            minimum_risk_reward=Decimal("2"),
        ),
    )

    result = PositionOpportunityHandler().evaluate(command)
    decision = result.decision.to_payload()["position_decision"]
    evaluation = result.to_state_payload()["position_opportunity_state"]["evaluation"]

    assert decision["decision"] == "APPROVE"
    assert decision["opportunity_checks"]["minimum_rr"] == "PASS"
    assert evaluation["stop"]["price"] == "95"
    assert evaluation["gross_risk_reward"] == "2"

    stricter = command_for(
        handoff=command.market_handoff,
        rules=rules_version(
            take_profit_mode=TakeProfitMode.DYNAMIC,
            stop_loss_pct=Decimal("0.05"),
            minimum_risk_reward=Decimal("2.000000000000000001"),
        ),
    )
    rejected = PositionOpportunityHandler().evaluate(stricter).decision.to_payload()["position_decision"]
    assert rejected["decision"] == "REJECT"
    assert rejected["opportunity_checks"]["minimum_rr"] == "FAIL"


def test_b7a_entry_is_gated_after_directional_rounding():
    result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                reference_price="102",
                atr="10",
                tick="1",
                levels=[
                    level("low-too-far-after-rounding", "SWING_LOW_15M", "89.9", "BELOW_REFERENCE"),
                    level("high-1", "SWING_HIGH_15M", "110", "ABOVE_REFERENCE"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC),
        )
    )

    evaluation = result.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert evaluation["entry"]["status"] == "UNAVAILABLE"
    assert evaluation["entry"]["reason_code"] == "ATR_DISTANCE_OUT_OF_RANGE_AFTER_ROUNDING"
    assert evaluation["decision"] == "REJECT"


def test_b7a_short_entry_is_gated_after_directional_rounding():
    result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                direction="SHORT",
                reference_price="98",
                atr="10",
                tick="1",
                levels=[
                    level("high-too-far-after-rounding", "SWING_HIGH_15M", "110.1", "ABOVE_REFERENCE"),
                    level("target-low", "SWING_LOW_15M", "90", "BELOW_REFERENCE"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC),
        )
    )

    evaluation = result.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert evaluation["entry"]["status"] == "UNAVAILABLE"
    assert evaluation["entry"]["reason_code"] == "ATR_DISTANCE_OUT_OF_RANGE_AFTER_ROUNDING"
    assert evaluation["decision"] == "REJECT"


def test_b7a_dynamic_stop_applies_buffer_min_distance_and_max_risk():
    result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                reference_price="102",
                atr="10",
                tick="0.1",
                levels=[
                    level("entry-low", "SWING_LOW_15M", "100", "BELOW_REFERENCE"),
                    level("stop-low", "SWING_LOW_15M", "99", "BELOW_REFERENCE"),
                    level("target-high", "SWING_HIGH_15M", "110", "ABOVE_REFERENCE"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC, metadata={"stop_loss_mode": "DYNAMIC"}),
        )
    )

    evaluation = result.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert evaluation["stop"]["status"] == "AVAILABLE"
    assert evaluation["stop"]["price"] == "95"
    assert evaluation["stop"]["raw_price"] == "97"
    assert evaluation["stop"]["distance_atr"] == "0.5"

    rejected = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                reference_price="102",
                atr="10",
                tick="0.1",
                levels=[
                    level("entry-low", "SWING_LOW_15M", "100", "BELOW_REFERENCE"),
                    level("wide-stop-low", "SWING_LOW_15M", "70", "BELOW_REFERENCE"),
                    level("target-high", "SWING_HIGH_15M", "110", "ABOVE_REFERENCE"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC, metadata={"stop_loss_mode": "DYNAMIC"}),
        )
    )
    rejected_evaluation = rejected.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert rejected_evaluation["stop"]["status"] == "UNAVAILABLE"
    assert rejected_evaluation["stop"]["reason_code"] == "SL_TOO_WIDE"


def test_b7a_dynamic_stop_selection_uses_latest_available_at_before_distance():
    result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                reference_price="102",
                atr="10",
                tick="0.1",
                levels=[
                    level("entry-low", "SWING_LOW_15M", "100", "BELOW_REFERENCE"),
                    level("older-closer-stop", "SWING_LOW_15M", "99", "BELOW_REFERENCE", available_at="2026-09-15T09:58:00Z"),
                    level("newer-farther-stop", "SWING_LOW_15M", "98", "BELOW_REFERENCE", available_at="2026-09-15T09:59:00Z"),
                    level("target-high", "SWING_HIGH_15M", "110", "ABOVE_REFERENCE"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC, metadata={"stop_loss_mode": "DYNAMIC"}),
        )
    )

    evaluation = result.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert evaluation["stop"]["status"] == "AVAILABLE"
    assert evaluation["stop"]["reference_level_id"] == "newer-farther-stop"
    assert evaluation["stop"]["raw_price"] == "96"


def test_b7a_short_dynamic_stop_rejects_max_risk():
    result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                direction="SHORT",
                reference_price="98",
                atr="10",
                tick="0.1",
                levels=[
                    level("entry-high", "SWING_HIGH_15M", "100", "ABOVE_REFERENCE"),
                    level("wide-stop-high", "SWING_HIGH_15M", "130", "ABOVE_REFERENCE"),
                    level("target-low", "SWING_LOW_15M", "90", "BELOW_REFERENCE"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC, metadata={"stop_loss_mode": "DYNAMIC"}),
        )
    )

    evaluation = result.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert evaluation["stop"]["status"] == "UNAVAILABLE"
    assert evaluation["stop"]["reason_code"] == "SL_TOO_WIDE"


def test_b7a_dynamic_tp_is_gated_after_directional_rounding():
    result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                reference_price="102",
                atr="10",
                tick="1",
                levels=[
                    level("entry-low", "SWING_LOW_15M", "100", "BELOW_REFERENCE"),
                    level("target-too-close-after-rounding", "SWING_HIGH_15M", "107.51", "ABOVE_REFERENCE"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC, stop_loss_pct=Decimal("0.05")),
        )
    )

    evaluation = result.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert evaluation["take_profit"]["status"] == "UNAVAILABLE"
    assert evaluation["take_profit"]["reason_code"] == "TARGET_TOO_CLOSE_AFTER_ROUNDING"


def test_b7a_short_path_uses_directional_rounding_for_entry_stop_and_take_profit():
    result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                direction="SHORT",
                reference_price="98",
                atr="10",
                tick="0.1",
                levels=[
                    level("entry-high", "SWING_HIGH_15M", "100.01", "ABOVE_REFERENCE"),
                    level("target-low", "SWING_LOW_15M", "90.04", "BELOW_REFERENCE"),
                ],
            ),
            rules=rules_version(
                take_profit_mode=TakeProfitMode.DYNAMIC,
                stop_loss_pct=Decimal("0.049"),
                minimum_risk_reward=Decimal("1.9"),
            ),
        )
    )

    evaluation = result.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert evaluation["entry"]["price"] == "100.1"
    assert evaluation["stop"]["price"] == "105.1"
    assert evaluation["take_profit"]["price"] == "90.1"
    assert result.decision.to_payload()["position_decision"]["decision"] == "APPROVE"


def test_b7a_short_dynamic_stop_and_tp_apply_post_round_boundaries():
    stop_result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                direction="SHORT",
                reference_price="98",
                atr="10",
                tick="0.1",
                levels=[
                    level("entry-high", "SWING_HIGH_15M", "100", "ABOVE_REFERENCE"),
                    level("stop-high", "SWING_HIGH_15M", "101", "ABOVE_REFERENCE"),
                    level("target-low", "SWING_LOW_15M", "90", "BELOW_REFERENCE"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC, metadata={"stop_loss_mode": "DYNAMIC"}),
        )
    )
    stop_eval = stop_result.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert stop_eval["stop"]["status"] == "AVAILABLE"
    assert stop_eval["stop"]["price"] == "105"
    assert stop_eval["stop"]["raw_price"] == "103"
    assert stop_eval["stop"]["distance_atr"] == "0.5"

    tp_result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                direction="SHORT",
                reference_price="98",
                atr="10",
                tick="1",
                levels=[
                    level("entry-high", "SWING_HIGH_15M", "100", "ABOVE_REFERENCE"),
                    level("target-too-close-after-rounding", "SWING_LOW_15M", "92.49", "BELOW_REFERENCE"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC, stop_loss_pct=Decimal("0.05")),
        )
    )
    tp_eval = tp_result.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert tp_eval["take_profit"]["status"] == "UNAVAILABLE"
    assert tp_eval["take_profit"]["reason_code"] == "TARGET_TOO_CLOSE_AFTER_ROUNDING"


def test_b7a_short_dynamic_stop_ceil_rounding_can_fail_post_round_max_risk():
    result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                direction="SHORT",
                reference_price="98",
                atr="10",
                tick="7",
                levels=[
                    level("entry-high", "SWING_HIGH_15M", "100.01", "ABOVE_REFERENCE"),
                    level("stop-high", "SWING_HIGH_15M", "117.9", "ABOVE_REFERENCE"),
                    level("target-low", "SWING_LOW_15M", "90", "BELOW_REFERENCE"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC, metadata={"stop_loss_mode": "DYNAMIC"}),
        )
    )

    evaluation = result.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert evaluation["entry"]["price"] == "105"
    assert evaluation["stop"]["status"] == "UNAVAILABLE"
    assert evaluation["stop"]["reason_code"] == "SL_TOO_WIDE"
    assert evaluation["stop"]["traversal"][0]["raw_stop"] == "119.9"
    assert evaluation["stop"]["traversal"][0]["adjusted_stop"] == "119.9"
    assert evaluation["stop"]["traversal"][0]["rounded_stop"] == "126"
    assert evaluation["stop"]["traversal"][0]["rounded_distance_atr"] == "2.1"


def test_b7a_candidate_selection_uses_latest_available_at_before_distance():
    result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                reference_price="102",
                atr="10",
                tick="0.1",
                levels=[
                    level("older-closer-entry", "SWING_LOW_15M", "101", "BELOW_REFERENCE", available_at="2026-09-15T09:58:00Z"),
                    level("newer-farther-entry", "SWING_LOW_15M", "100", "BELOW_REFERENCE", available_at="2026-09-15T09:59:00Z"),
                    level("older-closer-target", "SWING_HIGH_15M", "109", "ABOVE_REFERENCE", available_at="2026-09-15T09:58:00Z"),
                    level("newer-farther-target", "SWING_HIGH_15M", "110", "ABOVE_REFERENCE", available_at="2026-09-15T09:59:00Z"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC, stop_loss_pct=Decimal("0.05")),
        )
    )

    evaluation = result.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert evaluation["entry"]["reference_level_id"] == "newer-farther-entry"
    assert evaluation["take_profit"]["reference_level_id"] == "newer-farther-target"


def test_b7a_dynamic_tp_latest_too_far_terminates_before_older_candidate():
    result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(
                reference_price="102",
                atr="10",
                tick="0.1",
                levels=[
                    level("entry-low", "SWING_LOW_15M", "100", "BELOW_REFERENCE"),
                    level("older-valid-target", "SWING_HIGH_15M", "110", "ABOVE_REFERENCE", available_at="2026-09-15T09:58:00Z"),
                    level("newer-too-far-target", "SWING_HIGH_15M", "145", "ABOVE_REFERENCE", available_at="2026-09-15T09:59:00Z"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC, stop_loss_pct=Decimal("0.05")),
        )
    )

    evaluation = result.to_state_payload()["position_opportunity_state"]["evaluation"]
    assert evaluation["take_profit"]["status"] == "UNAVAILABLE"
    assert evaluation["take_profit"]["reason_code"] == "TARGET_TOO_FAR"
    assert evaluation["take_profit"]["traversal"][0]["level_id"] == "newer-too-far-target"


def test_b7a_rejects_missing_market_context_without_fetching_latest_or_guessing():
    result = PositionOpportunityHandler().evaluate(
        command_for(handoff=handoff(levels=[]), rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC))
    )

    state = result.to_state_payload()["position_opportunity_state"]
    assert state["decision"]["decision"] == "REJECT"
    assert state["decision"]["opportunity_checks"]["market_context"] == "UNAVAILABLE"
    assert state["evaluation"]["entry"]["status"] == "UNAVAILABLE"
    assert state["evaluation"]["report"]["available_level_ids"] == []


pytest.importorskip("psycopg")


def test_b7a_position_opportunity_store_persists_replays_recovers_and_publishes_outbox():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        command = command_for(
            handoff=handoff(
                reference_price="102",
                atr="10",
                tick="0.1",
                levels=[
                    level("low-1", "SWING_LOW_15M", "100", "BELOW_REFERENCE"),
                    level("high-1", "SWING_HIGH_15M", "110", "ABOVE_REFERENCE"),
                    level("retained-unvisited-low", "SWING_LOW_15M", "80", "BELOW_REFERENCE"),
                ],
            ),
            rules=rules_version(take_profit_mode=TakeProfitMode.DYNAMIC, stop_loss_pct=Decimal("0.05")),
        )

        with PostgresUnitOfWork(factory) as uow:
            store = PositionOpportunityStore(uow.connection)
            record, inserted = store.evaluate_and_record(command)
            assert inserted is True
            replayed, inserted = store.evaluate_and_record(command)
            assert inserted is False
            assert replayed.payload_digest == record.payload_digest
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id="position-decision-event-1")
            assert outbox is not None
            assert outbox.producer == "Position"
            assert outbox.consumer == "Portfolio"
            assert outbox.message_type == "APPROVE_REJECT"
            assert outbox.dedupe_key == "OPPORTUNITY_DECISION:position-decision-1"
            parsed_outbox = parse_contract("APPROVE_REJECT", outbox.payload, definition="APPROVE_REJECT.initial")
            validate_contract_edge(
                producer="Position",
                consumer="Portfolio",
                contract_type="APPROVE_REJECT",
                payload=parsed_outbox.to_payload(),
                definition="APPROVE_REJECT.initial",
            )
            pin = PositionConfigPinStore(uow.connection).get_by_position_decision_id(
                position_decision_id="position-decision-1"
            )
            assert pin is not None
            assert pin.pin.position_decision_id == "position-decision-1"
            assert pin.pin.decision_cycle_id == "decision-cycle-1"
            assert pin.pin.set_result_id == "set-result-1"
            assert pin.pin.symbol == "BTCUSDT"
            assert pin.pin.configuration_id == "rules-v1"
            assert pin.pin.configuration_version == "v1"
            assert pin.pin.configuration_content_digest == position_rules_content_digest(command.rules_version)

        with PostgresUnitOfWork(factory) as restarted:
            stored = PositionOpportunityStore(restarted.connection).get_by_position_decision_id(
                position_decision_id="position-decision-1"
            )
        assert stored is not None
        assert stored.decision == "APPROVE"
        assert stored.payload["position_opportunity_state"]["evaluation"]["entry"]["price"] == "100"
        source = stored.payload["position_opportunity_state"]["source_contracts"]["market_handoff"]["market_handoff"]
        assert source["reference_geometry"]["levels"][0]["level_id"] == "low-1"
        assert source["reference_geometry"]["levels"][1]["level_id"] == "high-1"
        assert source["reference_geometry"]["levels"][2]["level_id"] == "retained-unvisited-low"
        config = stored.payload["position_opportunity_state"]["source_configuration"]
        assert config["rules_version"]["rules_version_id"] == "rules-v1"
        assert config["rules_version"]["draft"]["take_profit_mode"] == "DYNAMIC"
    finally:
        _drop_schema(settings)


def test_b7a_position_opportunity_store_rejects_changed_replay():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        command = command_for(handoff=handoff(), rules=rules_version())
        changed = command_for(handoff=handoff(reference_price="103"), rules=rules_version())

        with PostgresUnitOfWork(factory) as uow:
            store = PositionOpportunityStore(uow.connection)
            store.evaluate_and_record(command)
            with pytest.raises(PositionOpportunityConflict):
                store.evaluate_and_record(changed)
    finally:
        _drop_schema(settings)


def command_for(*, handoff: dict[str, object] | None = None, rules: TradingRulesVersion | None = None) -> PositionOpportunityCommand:
    return PositionOpportunityCommand(
        event_id="position-decision-event-1",
        position_decision_id="position-decision-1",
        occurred_at=NOW,
        market_handoff=handoff if handoff is not None else globals()["handoff"](),
        rules_version=rules if rules is not None else rules_version(),
    )


def handoff(
    *,
    direction: str = "LONG",
    reference_price: str = "102",
    atr: str = "10",
    tick: str = "0.1",
    levels: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    payload = valid_payload("MARKET_HANDOFF", "MARKET_HANDOFF")
    body = payload["market_handoff"]
    body.update(
        {
            "decision_cycle_id": "decision-cycle-1",
            "set_result_id": "set-result-1",
            "symbol": "BTCUSDT",
            "created_at": NOW,
        }
    )
    body["snapshot"].update(
        {
            "matched_at": NOW,
            "market_snapshot_at": NOW,
            "market_snapshot_id": "snapshot-1",
            "direction": direction,
            "set_match_reference_price": reference_price,
            "reference_price_observed_at": NOW,
        }
    )
    body["instrument"].update({"tick_size": tick, "metadata_revision": "instrument:BTCUSDT:1", "metadata_as_of": NOW})
    body["volatility"].update({"atr_15m": atr, "atr_pct_15m": "0.1"})
    body["reference_geometry"]["levels"] = levels if levels is not None else [
        level("low-1", "SWING_LOW_15M", "100", "BELOW_REFERENCE"),
        level("high-1", "SWING_HIGH_15M", "110", "ABOVE_REFERENCE"),
    ]
    body["entry_context"].update({"set_family": "GENERIC", "thesis_reference_policy": "NONE"})
    body["sl_context"].update({"set_family": "GENERIC", "thesis_reference_policy": "NONE"})
    body["tp_context"].update({"set_family": "GENERIC", "thesis_reference_policy": "NONE"})
    return payload


def level(
    level_id: str,
    level_type: str,
    price: str,
    relative_position: str,
    *,
    available_at: str = NOW,
) -> dict[str, object]:
    return {
        "level_id": level_id,
        "level_type": level_type,
        "price": price,
        "timeframe": "15m",
        "formed_at": NOW,
        "confirmed_at": NOW,
        "available_at": available_at,
        "source_metric": "unit",
        "age_seconds": 0,
        "relative_position": relative_position,
    }


def rules_version(
    *,
    take_profit_mode: TakeProfitMode = TakeProfitMode.DYNAMIC,
    stop_loss_pct: Decimal = Decimal("0.01"),
    minimum_risk_reward: Decimal = Decimal("2"),
    metadata: dict[str, str] | None = None,
) -> TradingRulesVersion:
    draft = TradingRulesVersionDraft(
        position_size_pct=Decimal("0.05"),
        take_profit_mode=take_profit_mode,
        fixed_take_profit_pct=Decimal("0.03"),
        minimum_take_profit_pct=Decimal("0.03"),
        stop_loss_pct=stop_loss_pct,
        minimum_risk_reward=minimum_risk_reward,
        minimum_net_edge_enabled=True,
        minimum_net_edge_pct=Decimal("0.01"),
        leverage=Decimal("2"),
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
        metadata={"source": "unit", **(metadata or {})},
    )
    return TradingRulesVersion(
        rules_version_id="rules-v1",
        version="v1",
        created_at="2026-09-15T09:00:00Z",
        created_from_version_id=None,
        created_source="unit",
        change_summary="unit fixture",
        config_hash="0" * 64,
        schema_version="trading-rules-v1",
        draft=draft,
        is_current=True,
    )


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b7a_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')
