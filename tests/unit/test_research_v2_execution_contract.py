from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from triggertrade.backtest.models import HistoricalCandle
from triggertrade.order_specs import order_spec_digest, validate_order_spec
from triggertrade.position_rules import PositionOpportunityHandler
from triggertrade.research_v2 import load_research_v2_jobs, resolve_research_v2_set_resolution, ret5_ret15_or_signal
from triggertrade.research_v2_execution import (
    ORDER_SPEC_V2_CONTRACT_VERSION,
    V2PortfolioExposureState,
    VenueConstraints,
    build_research_v2_canonical_execution_profile,
    construct_research_v2_order_spec,
    evaluate_research_v2_portfolio_grant,
    research_v2_order_validity_status,
)
from triggertrade.research_v2_handoff import produce_research_v2_market_handoff
from triggertrade.services.research_backtest_execution import (
    _research_v1_backtest_funding_amount,
    _simulate_research_v1_backtest_lifecycle,
)
from tests.unit.test_research_v2_set_contract import _command_for, _handoff_facts, _resolution, _rules_version


OBSERVED_AT = "2026-08-20T10:15:00Z"


def test_v2_execution_profile_fingerprint_changes_for_ttl_and_stop_family():
    jobs = load_research_v2_jobs()
    j0 = build_research_v2_canonical_execution_profile(jobs["J0"])
    j1 = build_research_v2_canonical_execution_profile(jobs["J1"])
    j4 = build_research_v2_canonical_execution_profile(jobs["J4"])
    j7 = build_research_v2_canonical_execution_profile(jobs["J7"])

    assert j0.config_fingerprint != j1.config_fingerprint
    assert j4.config_fingerprint != j7.config_fingerprint
    assert j4.stop_profile["type"] == "HYBRID_STRUCTURAL"
    assert j7.stop_profile["type"] == "ATR_ONLY"


def test_v2_portfolio_grant_enforces_pending_inclusive_slots_and_caps():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J3"])

    assert evaluate_research_v2_portfolio_grant(
        profile=profile,
        state=V2PortfolioExposureState(Decimal("1000"), open_pending_count=3),
    ).reason_code == "MAX_OPEN_PENDING_REACHED"
    assert evaluate_research_v2_portfolio_grant(
        profile=profile,
        state=V2PortfolioExposureState(Decimal("1000"), coin_open_pending_count=1),
    ).reason_code == "MAX_COIN_OPEN_PENDING_REACHED"
    assert evaluate_research_v2_portfolio_grant(
        profile=profile,
        state=V2PortfolioExposureState(Decimal("1000"), committed_margin=Decimal("600")),
    ).reason_code == "TOTAL_MARGIN_CAP_REACHED"
    assert evaluate_research_v2_portfolio_grant(
        profile=profile,
        state=V2PortfolioExposureState(Decimal("1000"), coin_committed_margin=Decimal("330")),
    ).reason_code == "PER_COIN_MARGIN_CAP_REACHED"
    assert evaluate_research_v2_portfolio_grant(
        profile=profile,
        state=V2PortfolioExposureState(Decimal("1000"), gross_notional=Decimal("1800")),
    ).reason_code == "GROSS_NOTIONAL_CAP_REACHED"
    assert evaluate_research_v2_portfolio_grant(
        profile=profile,
        state=V2PortfolioExposureState(Decimal("1000"), stop_risk=Decimal("15")),
    ).reason_code == "TOTAL_STOP_RISK_CAP_REACHED"


def test_v2_risk_sizing_has_no_slot_auto_division():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J3"])
    one_slot = _constructed_order(profile, max_open_pending=1)
    three_slots = _constructed_order(profile, max_open_pending=3)

    assert one_slot["order_spec"]["economics"]["actual_order_notional"] == three_slots["order_spec"]["economics"]["actual_order_notional"]


def test_v2_fixed_capital_nominal_target_is_not_rescaled_from_free_margin():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J4"])
    grant = evaluate_research_v2_portfolio_grant(
        profile=profile,
        state=V2PortfolioExposureState(
            Decimal("1000"),
            committed_margin=Decimal("249.7134"),
            gross_notional=Decimal("249.7134"),
            stop_risk=Decimal("1.5"),
            open_pending_count=1,
        ),
    )

    result = _construct(profile, grant=grant, structural_reference=Decimal("101.4"))

    assert result.status == "CONSTRUCTED", result.reason_code
    assert result.order_spec["order_spec"]["economics"]["target_order_notional"] == "250"


def test_v2_fixed_capital_target_is_capped_by_actual_free_margin_only_when_binding():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J4"])
    grant = evaluate_research_v2_portfolio_grant(
        profile=profile,
        state=V2PortfolioExposureState(
            Decimal("1000"),
            committed_margin=Decimal("430"),
            gross_notional=Decimal("430"),
            stop_risk=Decimal("1.5"),
            open_pending_count=1,
        ),
    )

    result = _construct(profile, grant=grant, structural_reference=Decimal("101.4"))

    assert result.status == "CONSTRUCTED", result.reason_code
    assert result.order_spec["order_spec"]["economics"]["target_order_notional"] == "170"


def test_v2_fixed_capital_target_is_capped_by_coin_gross_and_stop_risk_limits():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J4"])
    cases = (
        (
            V2PortfolioExposureState(
                Decimal("1000"),
                coin_committed_margin=Decimal("200"),
            ),
            "coin_cap",
            "131",
        ),
        (
            V2PortfolioExposureState(
                Decimal("1000"),
                gross_notional=Decimal("1700"),
            ),
            "gross_exposure",
            "101",
        ),
        (
            V2PortfolioExposureState(
                Decimal("1000"),
                stop_risk=Decimal("14"),
            ),
            "portfolio_stop_risk",
            "250",
        ),
    )

    for state, expected_binding, expected_below in cases:
        grant = evaluate_research_v2_portfolio_grant(profile=profile, state=state)
        result = _construct(profile, grant=grant, structural_reference=Decimal("101.4"))
        assert result.status == "CONSTRUCTED", result.reason_code
        assert result.sizing["binding_constraint"] == expected_binding
        assert Decimal(result.order_spec["order_spec"]["economics"]["target_order_notional"]) < Decimal(expected_below)


def test_v2_fixed_capital_base_does_not_compound_with_realized_pnl():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J4"])
    grant = evaluate_research_v2_portfolio_grant(profile=profile, state=V2PortfolioExposureState(Decimal("1000")))

    result = _construct(profile, grant=grant, structural_reference=Decimal("101.4"))

    assert result.status == "CONSTRUCTED", result.reason_code
    assert result.order_spec["order_spec"]["economics"]["target_order_notional"] == "250"


def test_v2_order_spec_v6_parses_hashes_and_carries_ttl_to_lifecycle_contract():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J3"])
    spec = _constructed_order(profile)

    parsed = validate_order_spec(order_spec=spec)
    digest = order_spec_digest(spec)

    assert parsed.version == ORDER_SPEC_V2_CONTRACT_VERSION
    assert parsed.definition == "ORDER_SPEC.v6"
    assert len(digest) == 64
    assert spec["order_spec"]["entry"]["validity"]["time_in_force"] == "TTL"
    assert spec["order_spec"]["entry"]["validity"]["expires_at"] == "2026-08-20T10:30:00Z"
    assert research_v2_order_validity_status(spec, as_of="2026-08-20T10:29:00Z", filled_quantity=Decimal("0")) == "ACTIVE"
    assert research_v2_order_validity_status(spec, as_of="2026-08-20T10:30:00Z", filled_quantity=Decimal("0")) == "EXPIRED_CANCEL_UNFILLED"
    assert research_v2_order_validity_status(spec, as_of="2026-08-20T10:30:00Z", filled_quantity=Decimal("1")) == "EXPIRED_KEEP_FILLED_PROTECTION"


def test_v2_order_spec_ttl_is_enforced_by_canonical_lifecycle():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J3"])
    spec = _constructed_order(profile)
    submitted = datetime(2026, 8, 20, 10, 15, tzinfo=UTC)
    candles = (
        _candle(submitted, low="102.0", high="102.4"),
        _candle(submitted + timedelta(minutes=15), low="101.0", high="102.2"),
    )

    result = _simulate_research_v1_backtest_lifecycle(
        order_spec=spec,
        position_state=_position_state_for_lifecycle(),
        candles=candles,
        submitted_at="2026-08-20T10:15:00Z",
    )

    assert result.status == "ACCEPTED_NOT_FILLED"
    assert result.reason_code == "ENTRY_ORDER_EXPIRED_UNFILLED"
    assert result.accepted is True
    assert result.filled is False
    assert result.completed is True


def test_v2_funding_lookup_uses_physical_symbol_for_pepe_contracts():
    funding = _research_v1_backtest_funding_amount(
        funding_facts=(
            {
                "symbol": "1000PEPEUSDT",
                "funding_time": "2026-08-20T00:00:00Z",
                "funding_rate": "0.0001",
                "mark_price": "0.012",
            },
        ),
        spec={"symbol": "PEPEUSDT", "physical_symbol": "1000PEPEUSDT"},
        direction="LONG",
        quantity=Decimal("1000"),
        entry=Decimal("0.012"),
        opened_at=datetime(2026, 8, 19, 23, 59, tzinfo=UTC),
        closed_at=datetime(2026, 8, 20, 0, 1, tzinfo=UTC),
    )

    assert funding == Decimal("-0.0012000")


def test_v2_physical_symbol_mapping_preserves_pepe_and_leaves_avax_sui_unchanged():
    pepe = _constructed_order_for_identity("PEPEUSDT", "1000PEPEUSDT")
    avax = _constructed_order_for_identity("AVAXUSDT", "AVAXUSDT")
    sui = _constructed_order_for_identity("SUIUSDT", "SUIUSDT")

    assert pepe["order_spec"]["symbol"] == "PEPEUSDT"
    assert pepe["order_spec"]["physical_symbol"] == "1000PEPEUSDT"
    assert avax["order_spec"]["symbol"] == "AVAXUSDT"
    assert avax["order_spec"]["physical_symbol"] == "AVAXUSDT"
    assert sui["order_spec"]["symbol"] == "SUIUSDT"
    assert sui["order_spec"]["physical_symbol"] == "SUIUSDT"


def test_v2_pepe_funding_does_not_fallback_to_wrong_logical_symbol_fact():
    funding = _research_v1_backtest_funding_amount(
        funding_facts=(
            {
                "symbol": "PEPEUSDT",
                "funding_time": "2026-08-20T00:00:00Z",
                "funding_rate": "0.0001",
            },
        ),
        spec={"symbol": "PEPEUSDT", "physical_symbol": "1000PEPEUSDT"},
        direction="LONG",
        quantity=Decimal("1000"),
        entry=Decimal("0.012"),
        opened_at=datetime(2026, 8, 19, 23, 59, tzinfo=UTC),
        closed_at=datetime(2026, 8, 20, 0, 1, tzinfo=UTC),
    )

    assert funding is None


def test_v2_pepe_lifecycle_crossing_funding_boundary_closes_with_physical_funding_fact():
    order = _constructed_order_for_identity("PEPEUSDT", "1000PEPEUSDT")
    spec = order["order_spec"]
    submitted = datetime(2026, 8, 19, 23, 55, tzinfo=UTC)
    candles = (
        _symbol_candle("1000PEPEUSDT", submitted, low="101.8", high="102.0"),
        _symbol_candle("1000PEPEUSDT", submitted + timedelta(minutes=1), low="101.9", high="102.2"),
        _symbol_candle("1000PEPEUSDT", datetime(2026, 8, 20, 0, 1, tzinfo=UTC), low="102.2", high="103.1"),
    )

    result = _simulate_research_v1_backtest_lifecycle(
        order_spec=order,
        position_state=_position_state_for_handoff(_handoff_for_identity("PEPEUSDT", "1000PEPEUSDT")),
        candles=candles,
        submitted_at=submitted.isoformat(),
        funding_facts=(
            {
                "symbol": "1000PEPEUSDT",
                "funding_time": "2026-08-20T00:00:00Z",
                "funding_rate": "0.0001",
                "mark_price": "101.9",
            },
        ),
    )

    assert spec["symbol"] == "PEPEUSDT"
    assert spec["physical_symbol"] == "1000PEPEUSDT"
    assert result.status == "CLOSED"
    assert result.reason_code == "TAKE_PROFIT"
    assert result.completed is True
    assert result.closed_result is not None
    assert Decimal(str(result.closed_result["funding"])) != Decimal("0")


def test_v2_full_contract_fixture_reaches_position_portfolio_construction_order_spec():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J3"])
    spec = _constructed_order(profile)
    economics = spec["order_spec"]["economics"]

    assert spec["order_spec"]["contract_version"] == 6
    assert spec["order_spec"]["entry"]["order_type"] == "LIMIT"
    assert spec["order_spec"]["entry"]["post_only"] is True
    assert economics["execution_profile_fingerprint"] == profile.config_fingerprint
    assert Decimal(economics["actual_committed_margin"]) <= Decimal("250")
    assert Decimal(economics["actual_stop_risk"]) <= Decimal("7.5")
    assert economics["net_tp_floor_result"] == "PASS"
    assert spec["order_spec"]["stop_loss"]["mode"] == "HYBRID_STRUCTURAL"


def test_v2_g1_constructs_atr_only_stop_and_j4_j7_differ_only_downstream():
    jobs = load_research_v2_jobs()
    j4 = build_research_v2_canonical_execution_profile(jobs["J4"])
    j7 = build_research_v2_canonical_execution_profile(jobs["J7"])

    j4_spec = _constructed_order(j4)
    j7_spec = _constructed_order(j7)

    assert j4_spec["order_spec"]["set_result_id"] == j7_spec["order_spec"]["set_result_id"]
    assert j4_spec["order_spec"]["stop_loss"]["mode"] == "HYBRID_STRUCTURAL"
    assert j7_spec["order_spec"]["stop_loss"]["mode"] == "ATR_ONLY"
    assert j4_spec["order_spec"]["provenance"]["research_v2_execution_profile_fingerprint"] != j7_spec["order_spec"]["provenance"]["research_v2_execution_profile_fingerprint"]


def test_v2_sui_fine_tick_preserves_stop_ceiling_after_rounding():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J7"])
    grant = evaluate_research_v2_portfolio_grant(profile=profile, state=V2PortfolioExposureState(Decimal("1000")))
    result = _construct(
        profile,
        grant=grant,
        venue=VenueConstraints(
            tick_size=Decimal("0.00010"),
            qty_step=Decimal("10"),
            min_qty=Decimal("10"),
            min_notional=Decimal("5"),
            max_qty=Decimal("330000"),
        ),
        reference_price=Decimal("0.6581"),
        atr15=Decimal("0.001779432712078983"),
        structural_reference=Decimal("0.5982"),
    )

    assert result.status == "CONSTRUCTED", result.reason_code
    spec = result.order_spec["order_spec"]
    entry = Decimal(spec["entry"]["price"])
    stop = Decimal(spec["stop_loss"]["price"])
    assert entry == Decimal("0.6579")
    assert abs(entry - stop) / entry <= Decimal("0.0125")


def test_v2_final_stop_ceiling_rejects_post_rounding_coarse_tick_geometry():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J7"])
    grant = evaluate_research_v2_portfolio_grant(profile=profile, state=V2PortfolioExposureState(Decimal("1000")))
    result = _construct(
        profile,
        grant=grant,
        venue=VenueConstraints(
            tick_size=Decimal("0.1"),
            qty_step=Decimal("0.001"),
            min_qty=Decimal("0.001"),
            min_notional=Decimal("5"),
            max_qty=Decimal("100000"),
        ),
        reference_price=Decimal("0.6581"),
        atr15=Decimal("0.001779432712078983"),
        structural_reference=Decimal("0.5982"),
    )

    assert result.status == "REJECT"
    assert result.reason_code == "FINAL_STOP_DISTANCE_EXCEEDS_MAXIMUM"


def test_v2_g0_final_geometry_rejects_after_tick_rounding_exceeds_maximum():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J3"])
    grant = evaluate_research_v2_portfolio_grant(profile=profile, state=V2PortfolioExposureState(Decimal("1000")))
    result = _construct(
        profile,
        grant=grant,
        venue=VenueConstraints(
            tick_size=Decimal("0.1"),
            qty_step=Decimal("0.001"),
            min_qty=Decimal("0.001"),
            min_notional=Decimal("5"),
            max_qty=Decimal("100000"),
        ),
        reference_price=Decimal("0.6581"),
        atr15=Decimal("0.001779432712078983"),
        structural_reference=Decimal("0.5982"),
    )

    assert result.status == "REJECT"
    assert result.reason_code == "FINAL_STOP_DISTANCE_EXCEEDS_MAXIMUM"


def test_v2_g0_wrong_side_reference_is_rejected_not_reflected():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J3"])
    grant = evaluate_research_v2_portfolio_grant(profile=profile, state=V2PortfolioExposureState(Decimal("1000")))

    with pytest.raises(Exception, match="G0_STRUCTURAL_REFERENCE_NOT_PROTECTIVE"):
        _construct(
            profile,
            grant=grant,
            reference_price=Decimal("100"),
            atr15=Decimal("1"),
            structural_reference=Decimal("100.2"),
        )


def test_v2_sizing_limiters_reject_minimum_tranche_and_g0_too_wide():
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J3"])
    grant = evaluate_research_v2_portfolio_grant(
        profile=profile,
        state=V2PortfolioExposureState(Decimal("50")),
    )
    rejected = _construct(profile, grant=grant)
    assert rejected.reason_code == "MINIMUM_TRANCHE_NOT_MET"

    with pytest.raises(Exception, match="G0_STRUCTURAL_STOP_BEYOND_MAXIMUM"):
        _constructed_order(profile, structural_reference=Decimal("90"))


def _constructed_order(profile, *, max_open_pending: int = 3, structural_reference: Decimal = Decimal("101.4")):
    grant = evaluate_research_v2_portfolio_grant(
        profile=profile,
        state=V2PortfolioExposureState(Decimal("1000"), open_pending_count=3 - max_open_pending),
    )
    result = _construct(profile, grant=grant, structural_reference=structural_reference)
    assert result.status == "CONSTRUCTED", result.reason_code
    assert result.order_spec is not None
    return result.order_spec


def _position_state_for_lifecycle() -> dict[str, object]:
    resolution = _resolution(
            load_research_v2_jobs()["J3"],
            ret5_ret15_or_signal(return5_pct_points=Decimal("0.31"), return15_pct_points=Decimal("0.10")),
            evidence={"return5_pct_points": "0.31", "return15_pct_points": "0.10"},
    )
    handoff = produce_research_v2_market_handoff(
        resolution=resolution,
        facts=_handoff_facts(resolution.symbol),
    )
    return {
        "position_opportunity_state": {
            "source_contracts": {
                "market_handoff": handoff.payload,
            },
        },
    }


def _candle(open_time: datetime, *, low: str, high: str) -> HistoricalCandle:
    close_time = open_time + timedelta(minutes=1)
    return HistoricalCandle(
        "AVAXUSDT",
        "linear",
        "1m",
        open_time,
        close_time,
        Decimal("102.0"),
        Decimal(high),
        Decimal(low),
        Decimal("102.1"),
        Decimal("100"),
        Decimal("10210"),
        True,
    )


def _construct(
    profile,
    *,
    grant,
    structural_reference: Decimal = Decimal("101.4"),
    venue: VenueConstraints | None = None,
    reference_price: Decimal = Decimal("102"),
    atr15: Decimal = Decimal("1"),
):
    resolution = _resolution(
        load_research_v2_jobs()["J3"],
        ret5_ret15_or_signal(return5_pct_points=Decimal("0.31"), return15_pct_points=Decimal("0.10")),
        evidence={"return5_pct_points": "0.31", "return15_pct_points": "0.10"},
    )
    handoff = produce_research_v2_market_handoff(resolution=resolution, facts=_handoff_facts(resolution.symbol))
    position = PositionOpportunityHandler().evaluate(_command_for(handoff=handoff.payload, rules=_rules_version()))
    assert position.decision.to_payload()["position_decision"]["decision"] == "APPROVE"
    return construct_research_v2_order_spec(
        order_spec_id=f"v2-order-{profile.job_id}",
        spec_created_at=OBSERVED_AT,
        market_handoff=handoff.payload,
        profile=profile,
        portfolio_grant=grant,
        venue=venue or VenueConstraints(
            tick_size=Decimal("0.1"),
            qty_step=Decimal("0.001"),
            min_qty=Decimal("0.001"),
            min_notional=Decimal("5"),
            max_qty=Decimal("100"),
        ),
        reference_price=reference_price,
        atr15=atr15,
        structural_reference_price=structural_reference,
    )


def _constructed_order_for_identity(logical_symbol: str, physical_symbol: str):
    profile = build_research_v2_canonical_execution_profile(load_research_v2_jobs()["J3"])
    grant = evaluate_research_v2_portfolio_grant(profile=profile, state=V2PortfolioExposureState(Decimal("1000")))
    handoff = _handoff_for_identity(logical_symbol, physical_symbol)
    return construct_research_v2_order_spec(
        order_spec_id=f"v2-order-{logical_symbol.lower()}",
        spec_created_at="2026-08-19T23:55:00Z",
        market_handoff=handoff.payload,
        profile=profile,
        portfolio_grant=grant,
        venue=VenueConstraints(
            tick_size=Decimal("0.1"),
            qty_step=Decimal("0.001"),
            min_qty=Decimal("0.001"),
            min_notional=Decimal("5"),
            max_qty=Decimal("100"),
        ),
        reference_price=Decimal("102"),
        atr15=Decimal("1"),
        structural_reference_price=Decimal("101.4"),
    ).order_spec


def _handoff_for_identity(logical_symbol: str, physical_symbol: str):
    job = load_research_v2_jobs()["J3"]
    resolution = resolve_research_v2_set_resolution(
        job=job,
        symbol=logical_symbol,
        physical_symbol=physical_symbol,
        observed_at="2026-08-19T23:55:00Z",
        signal_result=ret5_ret15_or_signal(return5_pct_points=Decimal("0.31"), return15_pct_points=Decimal("0.10")),
        source_feature_evidence={"return5_pct_points": "0.31", "return15_pct_points": "0.10"},
    )
    facts = replace(
        _handoff_facts(logical_symbol),
        created_at="2026-08-19T23:55:00Z",
        matched_at="2026-08-19T23:55:00Z",
        market_snapshot_at="2026-08-19T23:55:00Z",
        reference_price_observed_at="2026-08-19T23:55:00Z",
        metadata_revision=f"research-v2-dataset:{physical_symbol}",
        metadata_as_of="2026-08-19T23:55:00Z",
    )
    return produce_research_v2_market_handoff(resolution=resolution, facts=facts)


def _position_state_for_handoff(handoff) -> dict[str, object]:
    return {
        "position_opportunity_state": {
            "source_contracts": {
                "market_handoff": handoff.payload,
            },
        },
    }


def _symbol_candle(symbol: str, open_time: datetime, *, low: str, high: str) -> HistoricalCandle:
    return HistoricalCandle(
        symbol,
        "linear",
        "1m",
        open_time,
        open_time + timedelta(minutes=1),
        Decimal("102.0"),
        Decimal(high),
        Decimal(low),
        Decimal("102.1"),
        Decimal("100"),
        Decimal("10210"),
        True,
    )
