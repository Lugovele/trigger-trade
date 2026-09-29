from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import inspect

import pytest

from triggertrade.api_adapter_gateway.market_data import (
    build_market_data_response,
    coverage,
    dataset_payload,
    market_selection,
    market_selection_result,
)
from triggertrade.contracts import BindingRole, validate_contract_edge
from triggertrade.research_v1_historical_handoff import (
    ResearchV1HistoricalMarketHandoffUnavailable,
    produce_research_v1_historical_market_handoff,
)
from triggertrade.research_v1_historical_sets import resolve_research_v1_historical_set
from triggertrade.research_v1_historical_sets import resolve_research_v1_historical_set_from_trigger_evaluations
from triggertrade.set_engine import SetMatchStatus, SetResolutionRequest

from tests.unit.test_research_v1_historical_sets import (
    _evaluations_for_set,
    _research_set,
    _rules_for,
)
from tests.unit.test_research_v1_historical_triggers import (
    _btc_context_source_minutes,
    _instrument,
)


def test_matched_set_produces_canonical_factual_market_handoff():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _btc_context_source_minutes()
    matched_at = candles[-1].close_time
    resolution = _matched_btc_resolution()

    handoff = produce_research_v1_historical_market_handoff(
        research_set=research_set,
        set_resolution=resolution,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
        ticker_responses=(_ticker_response("BTCUSDT", matched_at, "125"),),
    )

    assert handoff is not None
    payload = handoff.payload
    parsed = validate_contract_edge(
        producer=BindingRole.SET,
        consumer=BindingRole.POSITION,
        contract_type="MARKET_HANDOFF",
        payload=payload,
        definition="MARKET_HANDOFF",
    )
    body = parsed.to_payload()["market_handoff"]
    assert body["contract_version"] == 4
    assert body["decision_cycle_id"] == resolution.decision_cycle_id
    assert body["set_result_id"] == resolution.set_result_id
    assert body["snapshot"]["direction"] == resolution.direction
    assert body["snapshot"]["reference_price_basis"] == "LAST_TRADED_PRICE"
    assert body["snapshot"]["set_match_reference_price"] == "125"
    assert body["instrument"]["tick_size"] == "0.5"
    assert body["instrument"]["metadata_revision"] == "instrument:BTCUSDT:1"
    assert body["instrument"]["metadata_as_of"] == "2026-09-05T00:00:00+00:00"
    assert body["volatility"]["atr_15m"] == handoff.facts.atr_15m
    assert body["volatility"]["atr_pct_15m"] == handoff.facts.atr_pct_15m
    assert body["reference_geometry"]["levels"]
    assert {body["entry_context"]["thesis_reference_policy"], body["sl_context"]["thesis_reference_policy"], body["tp_context"]["thesis_reference_policy"]} == {"NONE"}


def test_unmatched_or_unavailable_set_produces_no_market_handoff():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _btc_context_source_minutes()
    matched_at = candles[-1].close_time
    zero = _btc_resolution(
        {
            "TR-R-002": ("TRUE", True),
            "TR-R-030": ("FALSE", False),
            "TR-R-BTC-001": ("ZERO", False),
            "TR-R-BTC-002": ("ZERO", False),
            "TR-R-BTC-005": ("TRUE", True),
            "TR-R-BTC-006": ("TRUE", True),
            "TR-R-BTC-007": ("TRUE", True),
            "TR-R-BTC-008": ("TRUE", True),
        }
    )
    unavailable = _btc_resolution(
        {
            "TR-R-002": ("TRUE", True),
            "TR-R-030": ("FALSE", False),
            "TR-R-BTC-001": ("UNAVAILABLE", False),
            "TR-R-BTC-002": ("ZERO", False),
            "TR-R-BTC-005": ("TRUE", True),
            "TR-R-BTC-006": ("TRUE", True),
            "TR-R-BTC-007": ("TRUE", True),
            "TR-R-BTC-008": ("TRUE", True),
        }
    )

    assert zero.status == SetMatchStatus.UNMATCHED.value
    assert unavailable.status == SetMatchStatus.UNMATCHED.value
    assert produce_research_v1_historical_market_handoff(
        research_set=research_set,
        set_resolution=zero,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
        ticker_responses=(_ticker_response("BTCUSDT", matched_at, "125"),),
    ) is None
    assert produce_research_v1_historical_market_handoff(
        research_set=research_set,
        set_resolution=unavailable,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
        ticker_responses=(_ticker_response("BTCUSDT", matched_at, "125"),),
    ) is None



def test_market_handoff_rejects_mismatched_set_identity_version_and_symbol():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _btc_context_source_minutes()
    matched_at = candles[-1].close_time
    resolution = _matched_btc_resolution()

    with pytest.raises(ResearchV1HistoricalMarketHandoffUnavailable, match="SET_ID_MISMATCH"):
        produce_research_v1_historical_market_handoff(
            research_set=replace(research_set, set_id="SET-R-WRONG"),
            set_resolution=resolution,
            candles=candles,
            symbol="BTCUSDT",
            instrument_metadata=_instrument("BTCUSDT"),
            ticker_responses=(_ticker_response("BTCUSDT", matched_at, "125"),),
        )

    with pytest.raises(ResearchV1HistoricalMarketHandoffUnavailable, match="SET_VERSION_MISMATCH"):
        produce_research_v1_historical_market_handoff(
            research_set=replace(research_set, set_version="SET-R-BTC-WRONG"),
            set_resolution=resolution,
            candles=candles,
            symbol="BTCUSDT",
            instrument_metadata=_instrument("BTCUSDT"),
            ticker_responses=(_ticker_response("BTCUSDT", matched_at, "125"),),
        )

    with pytest.raises(ResearchV1HistoricalMarketHandoffUnavailable, match="SET_SYMBOL_MISMATCH"):
        produce_research_v1_historical_market_handoff(
            research_set=research_set,
            set_resolution=resolution,
            candles=candles,
            symbol="ETHUSDT",
            instrument_metadata=_instrument("ETHUSDT"),
            ticker_responses=(_ticker_response("ETHUSDT", matched_at, "125"),),
        )


def test_market_handoff_rejects_stale_atr_instead_of_carrying_previous_15m_value():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = list(_btc_context_source_minutes())
    resolution = _matched_btc_resolution()
    matched_at = candles[-1].close_time

    expected_slot_start = matched_at - timedelta(minutes=15)
    damaged = tuple(
        candle
        for candle in candles
        if not (
            expected_slot_start <= candle.open_time < matched_at
        )
    )

    with pytest.raises(ResearchV1HistoricalMarketHandoffUnavailable, match="ATR_15M_STALE|ATR_15M_NON_CONTIGUOUS"):
        produce_research_v1_historical_market_handoff(
            research_set=research_set,
            set_resolution=resolution,
            candles=damaged,
            symbol="BTCUSDT",
            instrument_metadata=_instrument("BTCUSDT"),
            ticker_responses=(_ticker_response("BTCUSDT", matched_at, "125"),),
        )


def test_market_handoff_uses_set_owned_direction_not_candle_color():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _btc_context_source_minutes()
    bearish_last_candle = replace(candles[-1], open=candles[-1].close + 10, high=candles[-1].close + 11)
    changed_color = (*candles[:-1], bearish_last_candle)
    resolution = _matched_btc_resolution()

    handoff = produce_research_v1_historical_market_handoff(
        research_set=research_set,
        set_resolution=resolution,
        candles=changed_color,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
        ticker_responses=(_ticker_response("BTCUSDT", candles[-1].close_time, "125"),),
    )

    assert handoff is not None
    assert handoff.payload["market_handoff"]["snapshot"]["direction"] == "LONG"


def test_reference_geometry_is_factual_not_atr_multiple_synthetic_geometry():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _btc_context_source_minutes()
    handoff = produce_research_v1_historical_market_handoff(
        research_set=research_set,
        set_resolution=_matched_btc_resolution(),
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
        ticker_responses=(_ticker_response("BTCUSDT", candles[-1].close_time, "125"),),
    )

    assert handoff is not None
    levels = handoff.payload["market_handoff"]["reference_geometry"]["levels"]
    assert levels
    assert {level["source_metric"] for level in levels} <= {
        "SWING_POINTS_15M",
        "SWING_POINTS_1H",
        "PREVIOUS_UTC_DAY_HIGH_LOW",
    }
    assert {level["level_type"] for level in levels} <= {
        "SWING_HIGH_15M",
        "SWING_LOW_15M",
        "SWING_HIGH_1H",
        "SWING_LOW_1H",
        "PREVIOUS_DAY_HIGH",
        "PREVIOUS_DAY_LOW",
    }


def test_snapshot_identity_binds_reference_price_and_atr_evidence():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _btc_context_source_minutes()
    matched_at = candles[-1].close_time
    resolution = _matched_btc_resolution()
    first = produce_research_v1_historical_market_handoff(
        research_set=research_set,
        set_resolution=resolution,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
        ticker_responses=(_ticker_response("BTCUSDT", matched_at, "125"),),
    )
    changed_price = produce_research_v1_historical_market_handoff(
        research_set=research_set,
        set_resolution=resolution,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
        ticker_responses=(_ticker_response("BTCUSDT", matched_at, "126"),),
    )
    changed_atr_input = list(candles)
    changed_atr_input[-30] = replace(changed_atr_input[-30], high=changed_atr_input[-30].high + 3)
    changed_atr = produce_research_v1_historical_market_handoff(
        research_set=research_set,
        set_resolution=resolution,
        candles=tuple(changed_atr_input),
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
        ticker_responses=(_ticker_response("BTCUSDT", matched_at, "125"),),
    )

    assert first is not None and changed_price is not None and changed_atr is not None
    assert first.facts.market_snapshot_id != changed_price.facts.market_snapshot_id
    assert first.facts.market_snapshot_id != changed_atr.facts.market_snapshot_id


def test_incomplete_required_handoff_inputs_fail_closed():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _btc_context_source_minutes()
    resolution = _matched_btc_resolution()
    matched_at = candles[-1].close_time

    with pytest.raises(ResearchV1HistoricalMarketHandoffUnavailable, match="TICKER_FUTURE_LEAKAGE"):
        produce_research_v1_historical_market_handoff(
            research_set=research_set,
            set_resolution=resolution,
            candles=candles,
            symbol="BTCUSDT",
            instrument_metadata=_instrument("BTCUSDT"),
            ticker_responses=(_ticker_response("BTCUSDT", matched_at + timedelta(minutes=1), "125"),),
        )

    with pytest.raises(ResearchV1HistoricalMarketHandoffUnavailable, match="TICKER_COVERAGE_UNAVAILABLE"):
        produce_research_v1_historical_market_handoff(
            research_set=research_set,
            set_resolution=resolution,
            candles=candles,
            symbol="BTCUSDT",
            instrument_metadata=_instrument("BTCUSDT"),
            ticker_responses=(_ticker_response("BTCUSDT", matched_at, "125", coverage_complete=False),),
        )

    missing_atr = candles[:100] + candles[101:]
    with pytest.raises(ResearchV1HistoricalMarketHandoffUnavailable, match="ATR_15M_NON_CONTIGUOUS"):
        produce_research_v1_historical_market_handoff(
            research_set=research_set,
            set_resolution=resolution,
            candles=missing_atr,
            symbol="BTCUSDT",
            instrument_metadata=_instrument("BTCUSDT"),
            ticker_responses=(_ticker_response("BTCUSDT", matched_at, "125"),),
        )


def test_pepe_logical_and_factual_instrument_binding_preserved():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = tuple(replace(candle, symbol="PEPEUSDT") for candle in _btc_context_source_minutes())
    matched_at = candles[-1].close_time
    resolution = replace(_matched_btc_resolution(), symbol="PEPEUSDT")

    handoff = produce_research_v1_historical_market_handoff(
        research_set=research_set,
        set_resolution=resolution,
        candles=candles,
        symbol="PEPEUSDT",
        instrument_metadata=_instrument("1000PEPEUSDT"),
        ticker_responses=(
            _ticker_response(
                "PEPEUSDT",
                matched_at,
                "0.00125",
                source_symbol="1000PEPEUSDT",
            ),
        ),
    )

    assert handoff is not None
    body = handoff.payload["market_handoff"]
    assert body["symbol"] == "PEPEUSDT"
    assert body["instrument"]["metadata_revision"] == "instrument:1000PEPEUSDT:1"


def test_durable_set_resolution_request_still_requires_handoff_facts():
    durable = inspect.signature(SetResolutionRequest)

    assert durable.parameters["handoff_facts"].default is inspect.Parameter.empty


def test_real_historical_trigger_to_set_to_handoff_chain_without_mocked_producers():
    research_set = _research_set("SET-R-BTC-001-V2")
    candles = _matched_btc_fact_candles()
    matched_at = candles[-1].close_time
    resolution = resolve_research_v1_historical_set(
        research_set=research_set,
        trigger_rules=_rules_for(research_set),
        candles=candles,
        symbol="BTCUSDT",
    )

    assert resolution.status == SetMatchStatus.MATCHED.value
    handoff = produce_research_v1_historical_market_handoff(
        research_set=research_set,
        set_resolution=resolution,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
        ticker_responses=(_ticker_response("BTCUSDT", matched_at, "125"),),
    )

    assert handoff is not None
    assert handoff.payload["market_handoff"]["decision_cycle_id"] == resolution.decision_cycle_id
    assert handoff.payload["market_handoff"]["snapshot"]["direction"] == resolution.direction


def _matched_btc_fact_candles():
    candles = list(_btc_context_source_minutes())
    final_close = candles[-1].close
    for offset in range(len(candles) - 15, len(candles)):
        candle = candles[offset]
        close = final_close if offset == len(candles) - 1 else final_close - Decimal("2")
        candles[offset] = replace(
            candle,
            open=close,
            high=close + Decimal("0.1"),
            low=close - Decimal("0.1"),
            close=close,
            turnover=close * candle.volume,
        )
    for bucket in range(12 * 24 * 4, 12 * 24 * 4 + 20):
        for offset in range(bucket * 15, bucket * 15 + 15):
            candle = candles[offset]
            candles[offset] = replace(
                candle,
                high=candle.high + Decimal("30"),
                low=max(Decimal("0.01"), candle.low - Decimal("30")),
            )
    return tuple(candles)


def _matched_btc_resolution():
    return _btc_resolution(
        {
            "TR-R-002": ("TRUE", True),
            "TR-R-030": ("FALSE", False),
            "TR-R-BTC-001": ("LONG", True),
            "TR-R-BTC-002": ("ZERO", False),
            "TR-R-BTC-005": ("TRUE", True),
            "TR-R-BTC-006": ("TRUE", True),
            "TR-R-BTC-007": ("TRUE", True),
            "TR-R-BTC-008": ("TRUE", True),
        }
    )


def _btc_resolution(outputs):
    research_set = _research_set("SET-R-BTC-001-V2")
    return resolve_research_v1_historical_set_from_trigger_evaluations(
        research_set=research_set,
        trigger_evaluations=_evaluations_for_set(research_set, outputs),
        trigger_rules=_rules_for(research_set),
        symbol="BTCUSDT",
    )


def _ticker_response(
    symbol: str,
    as_of: datetime,
    last_price: str,
    *,
    coverage_complete: bool = True,
    source_symbol: str | None = None,
) -> dict[str, object]:
    selection = market_selection(
        selection_id=f"ticker-{symbol}",
        dataset="TICKER",
        mode="AS_OF",
        as_of=as_of,
        completed_only=False,
        page_size=1,
    )
    page_id = f"ticker-page-{symbol}"
    page = market_selection_result(
        symbol=symbol,
        selection=selection,
        page_id=page_id,
        page_index=0,
        source_snapshot_id=f"ticker-snapshot-{symbol}-{as_of.isoformat()}",
        payload=dataset_payload(
            dataset="TICKER",
            status="AVAILABLE",
            as_of=as_of,
            source_endpoint=f"bybit-v5-market-tickers:{source_symbol or symbol}",
            data={"last_price": last_price, "mark_price": last_price, "index_price": last_price},
        ),
        coverage=coverage(
            coverage_complete=coverage_complete,
            pagination_complete=True,
            next_cursor=None,
            expected_page_ids=(page_id,),
            source_finality_confirmed=coverage_complete,
            reason_code=None if coverage_complete else "INCOMPLETE_FIXTURE",
        ),
    )
    return build_market_data_response(
        request_id=f"ticker-request-{symbol}",
        response_id=f"ticker-response-{symbol}",
        symbol=symbol,
        snapshot_started_at=as_of,
        snapshot_completed_at=as_of,
        as_of=as_of,
        selection_results=(page,),
        expected_selections=(selection,),
    ).to_payload()
