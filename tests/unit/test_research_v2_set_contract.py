from __future__ import annotations

from decimal import Decimal

from triggertrade.position_rules import PositionOpportunityCommand, PositionOpportunityHandler
from triggertrade.research_v2 import (
    V2DecisionStatus,
    V2Direction,
    V2SignalResult,
    build_research_v2_execution_profile,
    continuation_signal,
    compression_breakout_signal,
    load_research_v2_jobs,
    resolve_research_v2_set_resolution,
    ret5_ret15_or_signal,
    reversal_signal,
)
from triggertrade.research_v2_handoff import produce_research_v2_market_handoff
from triggertrade.rules.trading import CoinRule, DirectionMode, TakeProfitMode, TradingRulesVersion, TradingRulesVersionDraft
from triggertrade.set_engine import HandoffContext, HandoffFacts, HandoffReferenceLevel


OBSERVED_AT = "2026-08-20T10:15:00Z"


def test_j3_signal_episode_resolves_matched_long_and_short():
    jobs = load_research_v2_jobs()
    long_resolution = _resolution(
        jobs["J3"],
        ret5_ret15_or_signal(return5_pct_points=Decimal("0.31"), return15_pct_points=Decimal("0.10")),
        evidence={"return5_pct_points": "0.31", "return15_pct_points": "0.10"},
    )
    short_resolution = _resolution(
        jobs["J3"],
        ret5_ret15_or_signal(return5_pct_points=Decimal("-0.10"), return15_pct_points=Decimal("-0.51")),
        evidence={"return5_pct_points": "-0.10", "return15_pct_points": "-0.51"},
    )

    assert long_resolution.status == "MATCHED"
    assert long_resolution.direction is V2Direction.LONG
    assert long_resolution.decision_cycle_id is not None
    assert short_resolution.status == "MATCHED"
    assert short_resolution.direction is V2Direction.SHORT
    assert short_resolution.decision_cycle_id is not None
    assert long_resolution.set_result_id != short_resolution.set_result_id


def test_j3_none_reset_case_resolves_unmatched_without_direction():
    jobs = load_research_v2_jobs()
    resolution = _resolution(
        jobs["J3"],
        ret5_ret15_or_signal(return5_pct_points=Decimal("0.10"), return15_pct_points=Decimal("-0.10")),
        evidence={"return5_pct_points": "0.10", "return15_pct_points": "-0.10"},
    )

    assert resolution.status == "UNMATCHED"
    assert resolution.direction is V2Direction.NONE
    assert resolution.decision_cycle_id is None
    assert resolution.reason_code == "FORMATION_FALSE"


def test_j4_signal_evidence_preserves_trend_and_rvol_facts():
    jobs = load_research_v2_jobs()
    base = ret5_ret15_or_signal(return5_pct_points=Decimal("0.35"), return15_pct_points=Decimal("0.60"))
    signal = continuation_signal(
        base=base,
        ema20=Decimal("105"),
        ema50=Decimal("100"),
        return15_pct_points=Decimal("0.60"),
        rvol5_value=Decimal("1.3"),
    )
    resolution = _resolution(
        jobs["J4"],
        signal,
        evidence={
            "return5_pct_points": "0.35",
            "return15_pct_points": "0.60",
            "ema20": "105",
            "ema50": "100",
            "rvol5": "1.3",
        },
    )

    payload = resolution.to_payload()["research_v2_set_resolution"]
    assert resolution.status == "MATCHED"
    assert payload["source_feature_evidence"]["ema20"] == "105"
    assert payload["source_feature_evidence"]["ema50"] == "100"
    assert payload["source_feature_evidence"]["rvol5"] == "1.3"


def test_j5_and_j6_set_identity_is_deterministic():
    jobs = load_research_v2_jobs()
    j5_signal = compression_breakout_signal(
        atr15_value=Decimal("1"),
        preceding_atr15_values=[Decimal("2")] * 96,
        close=Decimal("104"),
        prior_range_high=Decimal("103"),
        prior_range_low=Decimal("95"),
        rvol5_value=Decimal("1.6"),
        turnover_acceleration_value=Decimal("1.3"),
    )
    j6_signal = reversal_signal(
        return15_pct_points=Decimal("1.2"),
        latest_close=Decimal("101"),
        high_15m=Decimal("102"),
        low_15m=Decimal("98"),
        atr15_value=Decimal("1"),
        last_two_closes=[Decimal("101.5"), Decimal("101")],
        turnover_acceleration_value=Decimal("0.9"),
    )

    first_j5 = _resolution(jobs["J5"], j5_signal, evidence={"family": "compression", "close": "104"})
    second_j5 = _resolution(jobs["J5"], j5_signal, evidence={"family": "compression", "close": "104"})
    first_j6 = _resolution(jobs["J6"], j6_signal, evidence={"family": "reversal", "latest_close": "101"})
    second_j6 = _resolution(jobs["J6"], j6_signal, evidence={"family": "reversal", "latest_close": "101"})

    assert first_j5.set_result_id == second_j5.set_result_id
    assert first_j5.decision_cycle_id == second_j5.decision_cycle_id
    assert first_j6.set_result_id == second_j6.set_result_id
    assert first_j6.decision_cycle_id == second_j6.decision_cycle_id
    assert first_j5.set_result_id != first_j6.set_result_id


def test_changed_signal_evidence_changes_set_result_identity():
    jobs = load_research_v2_jobs()
    signal = ret5_ret15_or_signal(return5_pct_points=Decimal("0.31"), return15_pct_points=Decimal("0.10"))

    first = _resolution(jobs["J3"], signal, evidence={"return5_pct_points": "0.31"})
    second = _resolution(jobs["J3"], signal, evidence={"return5_pct_points": "0.32"})

    assert first.source_evidence_digest != second.source_evidence_digest
    assert first.set_result_id != second.set_result_id


def test_j4_and_j7_share_set_identity_but_have_different_execution_profiles():
    jobs = load_research_v2_jobs()
    signal = V2SignalResult(V2DecisionStatus.PASS, V2Direction.LONG, "V2-SIGNAL-CONTINUATION-V1")
    evidence = {"return15_pct_points": "0.60", "ema20": "105", "ema50": "100", "rvol5": "1.3"}

    j4_resolution = _resolution(jobs["J4"], signal, evidence=evidence)
    j7_resolution = _resolution(jobs["J7"], signal, evidence=evidence)
    j4_execution = build_research_v2_execution_profile(jobs["J4"])
    j7_execution = build_research_v2_execution_profile(jobs["J7"])

    assert j4_resolution.set_result_id == j7_resolution.set_result_id
    assert j4_resolution.decision_cycle_id == j7_resolution.decision_cycle_id
    assert j4_execution.config_fingerprint != j7_execution.config_fingerprint
    assert j4_execution.stop_profile != j7_execution.stop_profile


def test_v2_set_resolution_produces_valid_market_handoff_and_position_accepts_it():
    jobs = load_research_v2_jobs()
    resolution = _resolution(
        jobs["J3"],
        ret5_ret15_or_signal(return5_pct_points=Decimal("0.31"), return15_pct_points=Decimal("0.10")),
        evidence={"return5_pct_points": "0.31", "return15_pct_points": "0.10"},
    )

    handoff = produce_research_v2_market_handoff(resolution=resolution, facts=_handoff_facts(resolution.symbol))
    position = PositionOpportunityHandler().evaluate(
        _command_for(handoff=handoff.payload, rules=_rules_version())
    )
    decision = position.decision.to_payload()["position_decision"]

    assert handoff.payload["market_handoff"]["decision_cycle_id"] == resolution.decision_cycle_id
    assert handoff.payload["market_handoff"]["set_result_id"] == resolution.set_result_id
    assert handoff.payload["market_handoff"]["set_provenance"]["set_id"] == resolution.set_config_id
    assert decision["decision_cycle_id"] == resolution.decision_cycle_id
    assert decision["set_result_id"] == resolution.set_result_id
    assert decision["decision"] in {"APPROVE", "REJECT"}


def test_v2_market_handoff_does_not_require_synthetic_research_set_version():
    jobs = load_research_v2_jobs()
    resolution = _resolution(
        jobs["J3"],
        V2SignalResult(V2DecisionStatus.PASS, V2Direction.SHORT, "V2-SIGNAL-RET5-RET15-OR-V1"),
        evidence={"return5_pct_points": "-0.31"},
    )

    handoff = produce_research_v2_market_handoff(resolution=resolution, facts=_handoff_facts(resolution.symbol, short=True))

    assert "research_set" not in resolution.to_payload()["research_v2_set_resolution"]
    assert handoff.payload["market_handoff"]["snapshot"]["direction"] == "SHORT"


def _resolution(job, signal, *, evidence):
    return resolve_research_v2_set_resolution(
        job=job,
        symbol="AVAXUSDT",
        physical_symbol="AVAXUSDT",
        observed_at=OBSERVED_AT,
        signal_result=signal,
        source_feature_evidence=evidence,
    )


def _handoff_facts(symbol: str, *, short: bool = False) -> HandoffFacts:
    levels = (
        HandoffReferenceLevel(
            level_id="low-1",
            level_type="SWING_LOW_15M",
            price="100",
            timeframe="15m",
            formed_at=OBSERVED_AT,
            confirmed_at=OBSERVED_AT,
            available_at=OBSERVED_AT,
            source_metric="unit",
            age_seconds=0,
            relative_position="BELOW_REFERENCE",
        ),
        HandoffReferenceLevel(
            level_id="high-1",
            level_type="SWING_HIGH_15M",
            price="110",
            timeframe="15m",
            formed_at=OBSERVED_AT,
            confirmed_at=OBSERVED_AT,
            available_at=OBSERVED_AT,
            source_metric="unit",
            age_seconds=0,
            relative_position="ABOVE_REFERENCE",
        ),
    )
    return HandoffFacts(
        symbol=symbol,
        created_at=OBSERVED_AT,
        matched_at=OBSERVED_AT,
        market_snapshot_at=OBSERVED_AT,
        market_snapshot_id="research-v2-snapshot-1",
        set_match_reference_price="108" if short else "102",
        reference_price_observed_at=OBSERVED_AT,
        reference_price_source="UNIT_LAST_TRADED_PRICE",
        tick_size="0.1",
        metadata_revision=f"instrument:{symbol}:unit",
        metadata_as_of=OBSERVED_AT,
        atr_15m="10",
        atr_pct_15m="0.1",
        reference_levels=levels,
        entry_context=HandoffContext("GENERIC", "NONE", None, None),
        sl_context=HandoffContext("GENERIC", "NONE", None, None),
        tp_context=HandoffContext("GENERIC", "NONE", None, None),
        core_set_id="RESEARCH_V2_UNIT_CORE",
    )


def _command_for(*, handoff: dict[str, object], rules: TradingRulesVersion) -> PositionOpportunityCommand:
    return PositionOpportunityCommand(
        event_id="position-decision-event-v2-1",
        position_decision_id="position-decision-v2-1",
        occurred_at=OBSERVED_AT,
        market_handoff=handoff,
        rules_version=rules,
    )


def _rules_version() -> TradingRulesVersion:
    draft = TradingRulesVersionDraft(
        position_size_pct=Decimal("0.05"),
        take_profit_mode=TakeProfitMode.DYNAMIC,
        fixed_take_profit_pct=Decimal("0.03"),
        minimum_take_profit_pct=Decimal("0.03"),
        stop_loss_pct=Decimal("0.01"),
        minimum_risk_reward_enabled=True,
        minimum_risk_reward=Decimal("2"),
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
        coins=(CoinRule("AVAXUSDT", enabled=True, max_allocation_pct=None),),
        metadata={"source": "research-v2-unit"},
    )
    return TradingRulesVersion(
        rules_version_id="rules-v2-unit",
        version="v2-unit",
        created_at=OBSERVED_AT,
        created_from_version_id=None,
        created_source="unit",
        change_summary="research v2 unit fixture",
        config_hash="1" * 64,
        schema_version="trading-rules-v1",
        draft=draft,
        is_current=True,
    )
