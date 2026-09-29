from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
import re

import pytest

from triggertrade.backtest.models import HistoricalCandle
from triggertrade.instruments import FuturesInstrument
import triggertrade.research_v1_historical_triggers as historical_triggers
from triggertrade.research_v1_execution import RESEARCH_V1_SYMBOLS
from triggertrade.research_v1_historical_triggers import (
    HISTORICAL_READY_METRICS,
    ResearchV1HistoricalTriggerInputUnavailable,
    evaluate_research_v1_historical_triggers,
    metric_readiness,
    produce_research_v1_historical_metric,
    research_v1_trigger_metric_inventory,
)
from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType


def test_aggregation_provenance_has_no_process_local_side_map_or_id_lookup():
    source = Path("src/triggertrade/research_v1_historical_triggers.py").read_text(encoding="utf-8")

    assert not hasattr(historical_triggers, "_AGGREGATED_CANDLE_CONSTITUENTS")
    assert "_AGGREGATED_CANDLE_CONSTITUENTS" not in source
    assert re.search(r"\bid\s*\(", source) is None


def test_research_v1_trigger_inventory_is_source_derived_from_set_package():
    package = json.loads(Path("docs/research-import/sets/RESEARCH_V1_SETS.json").read_text(encoding="utf-8"))

    rows = research_v1_trigger_metric_inventory(sets_package=package)

    assert len(rows) == 31
    assert ("F-001 trigger_result" in {metric for row in rows for metric in row["metric_references"]})
    assert ("RETURN(asset,5m)" in {metric for row in rows for metric in row["metric_references"]})
    assert {row["trigger_id"] for row in rows if "RETURN(asset,5m)" in row["metric_references"]} == {
        "TR-R-BTC-001",
        "TR-R-BTC-002",
        "TR-R-BTC-003",
        "TR-R-BTC-004",
    }


def test_historical_f001_trigger_uses_factual_candles_and_exact_pinned_version():
    rule = _rule("TR-R-001")
    candles = (
        _candle(0, close="100"),
        _candle(1, close="100.40"),
        _candle(2, close="100.60"),
    )

    evaluation = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )[0]

    assert evaluation.trigger_id == "TR-R-001"
    assert evaluation.trigger_version == "1.0.0"
    assert evaluation.metric_ref == "F-001 trigger_result"
    assert evaluation.metric_value == "FALSE"
    assert evaluation.condition_result is False
    assert evaluation.signal.input_snapshot["metric_value"] == "FALSE"
    assert evaluation.signal.trigger_set_id == "SET-R-UNIT"
    assert evaluation.signal.trigger_set_version == "v1"


def test_config_snapshot_metric_values_are_not_used_as_market_facts():
    rule = _rule("TR-R-001")

    with pytest.raises(ResearchV1HistoricalTriggerInputUnavailable):
        evaluate_research_v1_historical_triggers(
            rules=(rule,),
            candles=(),
            symbol="BTCUSDT",
            trigger_set_id="SET-R-UNIT",
            trigger_set_version="v1",
        )


def test_empty_metric_input_fails_closed_without_synthetic_placeholder_candle():
    rule = _rule("TR-R-001")

    with pytest.raises(
        ResearchV1HistoricalTriggerInputUnavailable,
        match="research_v1_historical_metric_unavailable:F-001 trigger_result",
    ):
        produce_research_v1_historical_metric(
            metric_ref="F-001 trigger_result",
            rule=rule,
            candles=(),
            symbol="BTCUSDT",
        )


def test_historical_f001_does_not_leak_future_candle():
    rule = _rule("TR-R-001")
    candles = (
        _candle(0, close="100"),
        _candle(1, close="101"),
        _candle(2, close="200"),
    )

    without_future = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
        observed_at=candles[1].close_time,
    )[0]
    with_future = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )[0]

    assert without_future.metric_value == "TRUE"
    assert with_future.metric_value == "TRUE"
    assert without_future.metric_evidence_digest != with_future.metric_evidence_digest
    assert without_future.observed_at == candles[1].close_time.isoformat()


def test_insufficient_warmup_produces_unavailable_metric_observation():
    rule = _rule("TR-R-003")
    candles = tuple(_candle(index, volume="5") for index in range(60))

    observation = produce_research_v1_historical_metric(
        metric_ref="F-002 trigger_result",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )
    evaluation = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )[0]

    assert observation.status == "UNAVAILABLE"
    assert observation.value == "UNAVAILABLE"
    assert evaluation.output_state == "UNAVAILABLE"
    assert evaluation.condition_result is False


def test_f002_uses_current_and_sixty_preceding_completed_candles():
    rule = _rule("TR-R-003")
    candles = tuple(_candle(index, volume="1") for index in range(60)) + (_candle(60, volume="2"),)

    evaluation = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )[0]

    assert evaluation.metric_ref == "F-002 trigger_result"
    assert evaluation.metric_value == "TRUE"
    assert evaluation.condition_result is True


def test_de_uses_factual_15m_closes_from_completed_source_candles():
    rule = _rule("TR-R-006")
    candles = _one_minute_buckets_15m(tuple(str(100 + index) for index in range(9)))

    evaluation = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )[0]

    assert evaluation.metric_ref == "DE"
    assert evaluation.metric_value == "1"
    assert evaluation.condition_result is True
    assert evaluation.signal.window == "15m"


def test_de_gap_in_source_candles_is_unavailable():
    rule = _rule("TR-R-006")
    candles = tuple(
        candle
        for offset, candle in enumerate(_one_minute_buckets_15m(tuple(str(100 + index) for index in range(9))))
        if offset != 14
    )

    evaluation = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )[0]

    assert evaluation.metric_value == "UNAVAILABLE"
    assert evaluation.output_state == "UNAVAILABLE"
    assert evaluation.condition_result is False


def test_de_deterministic_replay_produces_same_evidence():
    rule = _rule("TR-R-006")
    candles = _one_minute_buckets_15m(tuple(str(100 + index) for index in range(9)))

    first = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )[0]
    second = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=tuple(reversed(candles)),
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )[0]

    assert first.metric_evidence_id == second.metric_evidence_id
    assert first.evidence_id == second.evidence_id


def test_de_independent_aggregation_rebuild_preserves_evidence_identity():
    rule = _rule("TR-R-006")
    candles = _one_minute_buckets_15m(tuple(str(100 + index) for index in range(9)))
    rebuilt = tuple(replace(candle) for candle in candles)

    first = produce_research_v1_historical_metric(
        metric_ref="DE",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )
    second = produce_research_v1_historical_metric(
        metric_ref="DE",
        rule=rule,
        candles=rebuilt,
        symbol="BTCUSDT",
    )

    assert first.status == "AVAILABLE"
    assert second.status == "AVAILABLE"
    assert first.evidence_id == second.evidence_id


def test_de_evidence_binds_15m_constituent_candle_provenance():
    rule = _rule("TR-R-006")
    candles = _one_minute_buckets_15m(tuple(str(100 + index) for index in range(9)))
    changed = list(candles)
    changed[21] = replace(changed[21], volume=Decimal("2"), turnover=changed[21].close * Decimal("2"))

    first = produce_research_v1_historical_metric(
        metric_ref="DE",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )
    second = produce_research_v1_historical_metric(
        metric_ref="DE",
        rule=rule,
        candles=tuple(changed),
        symbol="BTCUSDT",
    )

    assert first.status == "AVAILABLE"
    assert second.status == "AVAILABLE"
    assert first.value == second.value == "1"
    assert first.evidence_id != second.evidence_id


def test_atr_percentile_uses_wilder_atr_and_completed_utc_day_population():
    high_rule = _rule("TR-R-007")
    low_rule = _rule("TR-R-008")
    candles = _flat_atr_source_minutes(days=15, extra_buckets=1)

    high_eval, low_eval = evaluate_research_v1_historical_triggers(
        rules=(high_rule, low_rule),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )

    assert high_eval.metric_ref == "ATR percentile"
    assert high_eval.metric_value == "100"
    assert high_eval.condition_result is True
    assert low_eval.condition_result is False
    assert high_eval.signal.window == "15m"
    assert high_eval.signal.input_snapshot["metric_value"] == "100"
    observation = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=high_rule,
        candles=candles,
        symbol="BTCUSDT",
    )
    atr_payload = (observation.payload or {})["atr_percentile"]
    assert atr_payload["selection_start"] == "2026-07-17T00:00:00+00:00"
    assert atr_payload["selection_end"] == "2026-08-16T00:00:00+00:00"
    assert len(atr_payload["eligible_completed_utc_days"]) == 14
    assert atr_payload["comparison"] == "reference <= current"
    assert atr_payload["reference_population_digest"]
    assert atr_payload["current_atr_observation_digest"]


def test_atr_percentile_incomplete_15m_bucket_is_unavailable():
    rule = _rule("TR-R-007")
    candles = tuple(_candle(index, close="100", high="101", low="99") for index in range(14))

    observation = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )

    assert observation.status == "UNAVAILABLE"
    assert observation.value == "UNAVAILABLE"


def test_atr_percentile_missing_1m_constituent_inside_history_is_unavailable():
    rule = _rule("TR-R-007")
    candles = tuple(
        candle
        for offset, candle in enumerate(_flat_atr_source_minutes(days=15, extra_buckets=1))
        if offset != (7 * 24 * 60 + 30)
    )

    observation = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )

    assert observation.status == "UNAVAILABLE"
    assert observation.reason_code == "research_v1_historical_atr_percentile_unavailable:NON_CONTINUOUS_15M_ATR_CHAIN"


def test_atr_percentile_missing_complete_15m_bucket_inside_history_is_unavailable():
    rule = _rule("TR-R-007")
    missing_start = 7 * 24 * 60 + 4 * 15
    candles = tuple(
        candle
        for offset, candle in enumerate(_flat_atr_source_minutes(days=15, extra_buckets=1))
        if not (missing_start <= offset < missing_start + 15)
    )

    observation = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )

    assert observation.status == "UNAVAILABLE"
    assert observation.reason_code == "research_v1_historical_atr_percentile_unavailable:NON_CONTINUOUS_15M_ATR_CHAIN"


def test_atr_percentile_gap_before_current_inside_wilder_chain_is_unavailable():
    rule = _rule("TR-R-007")
    missing_start = 14 * 24 * 60 - 15
    candles = tuple(
        candle
        for offset, candle in enumerate(_flat_atr_source_minutes(days=15, extra_buckets=1))
        if not (missing_start <= offset < missing_start + 15)
    )

    observation = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )

    assert observation.status == "UNAVAILABLE"
    assert observation.reason_code == "research_v1_historical_atr_percentile_unavailable:NON_CONTINUOUS_15M_ATR_CHAIN"


def test_atr_percentile_requires_fourteen_completed_utc_days():
    rule = _rule("TR-R-007")
    candles = _flat_atr_source_minutes(days=13, extra_buckets=1)

    observation = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )

    assert observation.status == "UNAVAILABLE"
    assert observation.reason_code == "research_v1_historical_atr_percentile_unavailable:INSUFFICIENT_COMPLETED_UTC_DAYS"


def test_atr_percentile_deterministic_replay_and_no_price_percentage_payload():
    rule = _rule("TR-R-007")
    candles = _flat_atr_source_minutes(days=15, extra_buckets=1)

    first = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )
    second = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=tuple(reversed(candles)),
        symbol="BTCUSDT",
    )

    assert first.value == "100"
    assert first.evidence_id == second.evidence_id
    assert "current_atr_update" in (first.payload or {})["atr_percentile"]
    assert "price_percentage_approximation" not in json.dumps(first.payload)


def test_atr_percentile_reference_population_change_changes_evidence():
    rule = _rule("TR-R-007")
    candles = _flat_atr_source_minutes(days=15, extra_buckets=1)
    changed = list(candles)
    changed[7 * 24 * 60 + 30] = replace(changed[7 * 24 * 60 + 30], high=Decimal("102"))

    first = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )
    second = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=tuple(changed),
        symbol="BTCUSDT",
    )

    assert first.status == "AVAILABLE"
    assert second.status == "AVAILABLE"
    assert first.evidence_id != second.evidence_id
    assert first.payload["atr_percentile"]["reference_population_digest"] != second.payload["atr_percentile"]["reference_population_digest"]


def test_atr_percentile_same_rank_different_reference_population_changes_evidence():
    rule = _rule("TR-R-007")
    candles = _flat_atr_source_minutes(days=15, extra_buckets=1)
    changed = list(candles)
    changed[7 * 24 * 60 + 30] = replace(
        changed[7 * 24 * 60 + 30],
        volume=Decimal("2"),
        turnover=changed[7 * 24 * 60 + 30].close * Decimal("2"),
    )

    first = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )
    second = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=tuple(changed),
        symbol="BTCUSDT",
    )

    assert first.status == "AVAILABLE"
    assert second.status == "AVAILABLE"
    assert first.value == second.value == "100"
    assert first.evidence_id != second.evidence_id
    assert first.payload["atr_percentile"]["reference_population_digest"] != second.payload["atr_percentile"]["reference_population_digest"]


def test_atr_percentile_independent_aggregation_rebuild_preserves_evidence_identity():
    rule = _rule("TR-R-007")
    candles = _flat_atr_source_minutes(days=15, extra_buckets=1)
    rebuilt = tuple(replace(candle) for candle in candles)

    first = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )
    second = produce_research_v1_historical_metric(
        metric_ref="ATR percentile",
        rule=rule,
        candles=rebuilt,
        symbol="BTCUSDT",
    )

    assert first.status == "AVAILABLE"
    assert second.status == "AVAILABLE"
    assert first.evidence_id == second.evidence_id
    assert first.payload["atr_percentile"]["reference_population_digest"] == second.payload["atr_percentile"]["reference_population_digest"]


def test_tod_rel_turnover_uses_same_clock_5m_turnover_median():
    rule = _rule("TR-R-017")
    candles = _same_clock_5m_turnover_minutes(
        current_turnover="20",
        prior_turnovers=tuple("10" for _ in range(14)),
    )

    observation = produce_research_v1_historical_metric(
        metric_ref="TOD_REL_TURNOVER",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )

    assert observation.status == "AVAILABLE"
    assert observation.value == "2"
    assert observation.payload["tod_rel_turnover"]["reference_count"] == 14
    assert observation.payload["tod_rel_turnover"]["turnover_basis"] == "quote_notional_turnover"


def test_tod_rel_turnover_missing_same_clock_day_is_unavailable():
    rule = _rule("TR-R-017")
    candles = _same_clock_5m_turnover_minutes(
        current_turnover="20",
        prior_turnovers=tuple("10" for _ in range(15)),
        missing_offsets={7},
    )

    observation = produce_research_v1_historical_metric(
        metric_ref="TOD_REL_TURNOVER",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )

    assert observation.status == "UNAVAILABLE"
    assert observation.reason_code == "research_v1_historical_tod_rel_turnover_unavailable:INSUFFICIENT_SAME_CLOCK_HISTORY"


def test_tod_rel_turnover_replay_order_and_input_provenance_are_deterministic():
    rule = _rule("TR-R-017")
    candles = _same_clock_5m_turnover_minutes(
        current_turnover="20",
        prior_turnovers=tuple("10" for _ in range(14)),
    )
    changed = tuple(
        replace(candle, volume=Decimal("0.4"), turnover=Decimal("4"))
        if candle.open_time == datetime(2026, 9, 19, 12, 0, tzinfo=UTC)
        else candle
        for candle in candles
    )

    first = produce_research_v1_historical_metric(
        metric_ref="TOD_REL_TURNOVER",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
    )
    reversed_order = produce_research_v1_historical_metric(
        metric_ref="TOD_REL_TURNOVER",
        rule=rule,
        candles=tuple(reversed(candles)),
        symbol="BTCUSDT",
    )
    changed_input = produce_research_v1_historical_metric(
        metric_ref="TOD_REL_TURNOVER",
        rule=rule,
        candles=changed,
        symbol="BTCUSDT",
    )

    assert first.evidence_digest == reversed_order.evidence_digest
    assert first.evidence_digest != changed_input.evidence_digest


def test_relative_return_15m_uses_exact_aligned_asset_and_btc_windows():
    rule = _rule("TR-R-011")
    asset, btc = _relative_return_15m_streams(asset_current="103", btc_previous="200", btc_current="202")

    observation = produce_research_v1_historical_metric(
        metric_ref="RELATIVE_RETURN_15m",
        rule=rule,
        candles=asset,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": btc},
    )

    assert observation.status == "AVAILABLE"
    assert observation.value == "0.02"
    assert observation.payload["relative_return_15m"]["formula"] == "RETURN(asset,15m) - RETURN(BTC,15m)"
    assert observation.payload["relative_return_15m"]["asset_symbol"] == "ETHUSDT"
    assert observation.payload["relative_return_15m"]["benchmark_symbol"] == "BTCUSDT"


def test_relative_return_15m_btc_stream_absent_or_wrong_symbol_is_unavailable():
    rule = _rule("TR-R-011")
    asset, btc = _relative_return_15m_streams()

    absent = produce_research_v1_historical_metric(
        metric_ref="RELATIVE_RETURN_15m",
        rule=rule,
        candles=asset,
        symbol="ETHUSDT",
        companion_candles=None,
    )
    wrong_symbol = produce_research_v1_historical_metric(
        metric_ref="RELATIVE_RETURN_15m",
        rule=rule,
        candles=asset,
        symbol="ETHUSDT",
        companion_candles={"ETHUSDT": btc},
    )

    assert absent.status == "UNAVAILABLE"
    assert absent.reason_code == "research_v1_historical_relative_return_15m_unavailable:BTC_STREAM_UNAVAILABLE"
    assert wrong_symbol.status == "UNAVAILABLE"
    assert wrong_symbol.reason_code == "research_v1_historical_relative_return_15m_unavailable:BTC_STREAM_UNAVAILABLE"


def test_relative_return_15m_missing_asset_or_btc_interval_is_unavailable():
    rule = _rule("TR-R-011")
    asset, btc = _relative_return_15m_streams()

    missing_asset = produce_research_v1_historical_metric(
        metric_ref="RELATIVE_RETURN_15m",
        rule=rule,
        candles=asset[:20],
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": btc},
    )
    missing_btc = produce_research_v1_historical_metric(
        metric_ref="RELATIVE_RETURN_15m",
        rule=rule,
        candles=asset,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": btc[:20]},
    )

    assert missing_asset.status == "UNAVAILABLE"
    assert missing_asset.reason_code == "research_v1_historical_relative_return_15m_unavailable:INCOMPLETE_ASSET_15M_INTERVAL"
    assert missing_btc.status == "UNAVAILABLE"
    assert missing_btc.reason_code == "research_v1_historical_relative_return_15m_unavailable:BTC_15M_ENDPOINT_MISMATCH"


def test_relative_return_15m_endpoint_mismatch_and_future_leakage_are_unavailable_or_excluded():
    rule = _rule("TR-R-011")
    asset, btc = _relative_return_15m_streams()
    shifted_btc = tuple(replace(candle, open_time=candle.open_time + timedelta(minutes=1), close_time=candle.close_time + timedelta(minutes=1)) for candle in btc)
    asset_future, btc_future = _relative_return_15m_streams(
        asset_current="103",
        btc_previous="200",
        btc_current="202",
        extra_future=True,
    )

    mismatch = produce_research_v1_historical_metric(
        metric_ref="RELATIVE_RETURN_15m",
        rule=rule,
        candles=asset,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": shifted_btc},
    )
    without_future = produce_research_v1_historical_metric(
        metric_ref="RELATIVE_RETURN_15m",
        rule=rule,
        candles=asset_future,
        symbol="ETHUSDT",
        observed_at=asset[29].close_time,
        companion_candles={"BTCUSDT": btc_future},
    )

    assert mismatch.status == "UNAVAILABLE"
    assert mismatch.reason_code == "research_v1_historical_relative_return_15m_unavailable:BTC_15M_ENDPOINT_MISMATCH"
    assert without_future.status == "AVAILABLE"
    assert without_future.value == "0.02"


def test_relative_return_15m_replay_order_and_both_sides_bind_evidence():
    rule = _rule("TR-R-011")
    asset, btc = _relative_return_15m_streams(asset_current="103", btc_previous="200", btc_current="202")
    changed_asset = tuple(replace(candle, close=Decimal("104"), high=Decimal("104")) if candle.open_time == asset[-1].open_time else candle for candle in asset)
    changed_btc = tuple(replace(candle, close=Decimal("203"), high=Decimal("203")) if candle.open_time == btc[-1].open_time else candle for candle in btc)

    first = produce_research_v1_historical_metric(
        metric_ref="RELATIVE_RETURN_15m",
        rule=rule,
        candles=asset,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": btc},
    )
    reversed_order = produce_research_v1_historical_metric(
        metric_ref="RELATIVE_RETURN_15m",
        rule=rule,
        candles=tuple(reversed(asset)),
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": tuple(reversed(btc))},
    )
    asset_changed = produce_research_v1_historical_metric(
        metric_ref="RELATIVE_RETURN_15m",
        rule=rule,
        candles=changed_asset,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": btc},
    )
    btc_changed = produce_research_v1_historical_metric(
        metric_ref="RELATIVE_RETURN_15m",
        rule=rule,
        candles=asset,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": changed_btc},
    )

    assert first.evidence_digest == reversed_order.evidence_digest
    assert first.evidence_digest != asset_changed.evidence_digest
    assert first.evidence_digest != btc_changed.evidence_digest


def test_relative_return_15m_trigger_uses_exact_pinned_version():
    rule = _rule("TR-R-011")
    asset, btc = _relative_return_15m_streams(asset_current="103", btc_previous="200", btc_current="202")

    evaluation = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=asset,
        symbol="ETHUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
        companion_candles={"BTCUSDT": btc},
    )[0]

    assert evaluation.trigger_id == "TR-R-011"
    assert evaluation.trigger_version == "1.0.0"
    assert evaluation.metric_ref == "RELATIVE_RETURN_15m"
    assert evaluation.metric_value == "0.02"
    assert evaluation.condition_result is True


def test_btc_return_z_uses_completed_15m_population_and_ddof_zero():
    btc = _btc_context_source_minutes()
    observation = historical_triggers._btc_return_z_observation(  # noqa: SLF001 - phase contract evidence
        btc_candles=btc,
        evaluation_at=btc[-1].close_time,
    )

    assert observation.status == "AVAILABLE"
    assert observation.payload["btc_return_z"]["ddof"] == 0
    assert observation.payload["btc_return_z"]["minimum_warmup_days"] == 14
    assert observation.payload["btc_return_z"]["reference_observation_count"] >= 14 * 96
    assert observation.payload["btc_return_z"]["value"] == observation.value


def test_btc_return_z_fail_closed_cases_and_deterministic_provenance():
    btc = _btc_context_source_minutes()
    missing_bucket = btc[:2000] + btc[2001:]
    zero_variance = _flat_btc_return_z_minutes()
    changed = tuple(
        replace(candle, close=candle.close + Decimal("0.5"), high=candle.high + Decimal("0.5"))
        if candle.open_time == datetime(2026, 8, 10, 9, 17, tzinfo=UTC)
        else candle
        for candle in btc
    )

    missing = historical_triggers._btc_return_z_observation(  # noqa: SLF001
        btc_candles=missing_bucket,
        evaluation_at=btc[-1].close_time,
    )
    short = historical_triggers._btc_return_z_observation(  # noqa: SLF001
        btc_candles=btc[:100],
        evaluation_at=btc[99].close_time,
    )
    flat = historical_triggers._btc_return_z_observation(  # noqa: SLF001
        btc_candles=zero_variance,
        evaluation_at=zero_variance[-1].close_time,
    )
    first = historical_triggers._btc_return_z_observation(  # noqa: SLF001
        btc_candles=btc,
        evaluation_at=btc[-1].close_time,
    )
    reversed_order = historical_triggers._btc_return_z_observation(  # noqa: SLF001
        btc_candles=tuple(reversed(btc)),
        evaluation_at=btc[-1].close_time,
    )
    changed_input = historical_triggers._btc_return_z_observation(  # noqa: SLF001
        btc_candles=changed,
        evaluation_at=btc[-1].close_time,
    )

    assert missing.status == "UNAVAILABLE"
    assert missing.reason_code == "research_v1_historical_btc_return_z_unavailable:NON_CONTINUOUS_15M_RETURN_CHAIN"
    assert short.status == "UNAVAILABLE"
    assert flat.status == "UNAVAILABLE"
    assert flat.reason_code == "research_v1_historical_btc_return_z_unavailable:ZERO_OR_UNAVAILABLE_SIGMA"
    assert first.evidence_digest == reversed_order.evidence_digest
    assert first.evidence_digest != changed_input.evidence_digest


def test_btc_return_z_excludes_future_candles_at_cutoff():
    btc = _btc_context_source_minutes(extra_future=True)
    cutoff = datetime(2026, 8, 17, 0, 15, tzinfo=UTC)

    with_future = historical_triggers._btc_return_z_observation(  # noqa: SLF001
        btc_candles=btc,
        evaluation_at=cutoff,
    )
    without_future = historical_triggers._btc_return_z_observation(  # noqa: SLF001
        btc_candles=tuple(candle for candle in btc if candle.close_time <= cutoff),
        evaluation_at=cutoff,
    )

    assert with_future.evidence_digest == without_future.evidence_digest


def test_btc_context_score_composes_structure_and_momentum_exactly():
    rule = _rule("TR-R-018")
    btc = _btc_context_source_minutes()
    primary = (_primary_cutoff_candle("ETHUSDT", btc[-1].close_time),)

    observation = produce_research_v1_historical_metric(
        metric_ref="BTC_CONTEXT_SCORE",
        rule=rule,
        candles=primary,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": btc},
        companion_instrument_metadata={"BTCUSDT": _instrument("BTCUSDT")},
    )

    payload = observation.payload["btc_context_score"]
    expected = Decimal(payload["btc_structure_score"]) * Decimal("0.60") + Decimal(payload["btc_momentum_score"]) * Decimal("0.40")
    assert observation.status == "AVAILABLE"
    assert payload["btc_structure_state"] == "BULLISH"
    assert payload["btc_structure_score"] == "1"
    assert Decimal(observation.value) == expected


def test_btc_context_score_unavailable_when_structure_or_momentum_unavailable():
    rule = _rule("TR-R-018")
    btc = _btc_context_source_minutes()
    primary = (_primary_cutoff_candle("ETHUSDT", btc[-1].close_time),)
    flat = _flat_btc_return_z_minutes()
    flat_primary = (_primary_cutoff_candle("ETHUSDT", flat[-1].close_time),)

    missing_metadata = produce_research_v1_historical_metric(
        metric_ref="BTC_CONTEXT_SCORE",
        rule=rule,
        candles=primary,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": btc},
    )
    missing_momentum = produce_research_v1_historical_metric(
        metric_ref="BTC_CONTEXT_SCORE",
        rule=rule,
        candles=flat_primary,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": flat},
        companion_instrument_metadata={"BTCUSDT": _instrument("BTCUSDT")},
    )

    assert missing_metadata.status == "UNAVAILABLE"
    assert missing_metadata.reason_code == "research_v1_historical_btc_context_score_unavailable:INSTRUMENT_METADATA_UNAVAILABLE"
    assert missing_momentum.status == "UNAVAILABLE"
    assert missing_momentum.reason_code == "research_v1_historical_btc_context_score_unavailable:BTC_RETURN_Z_UNAVAILABLE"


def test_btc_context_score_binds_structure_and_momentum_evidence():
    rule = _rule("TR-R-018")
    btc = _btc_context_source_minutes()
    changed_momentum = tuple(
        replace(candle, close=candle.close + Decimal("0.5"), high=candle.high + Decimal("0.5"))
        if candle.open_time == datetime(2026, 8, 10, 9, 17, tzinfo=UTC)
        else candle
        for candle in btc
    )
    changed_structure = _btc_context_source_minutes(structure_state="bearish")
    primary = (_primary_cutoff_candle("ETHUSDT", btc[-1].close_time),)

    first = produce_research_v1_historical_metric(
        metric_ref="BTC_CONTEXT_SCORE",
        rule=rule,
        candles=primary,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": btc},
        companion_instrument_metadata={"BTCUSDT": _instrument("BTCUSDT")},
    )
    reversed_order = produce_research_v1_historical_metric(
        metric_ref="BTC_CONTEXT_SCORE",
        rule=rule,
        candles=primary,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": tuple(reversed(btc))},
        companion_instrument_metadata={"BTCUSDT": _instrument("BTCUSDT")},
    )
    momentum_changed = produce_research_v1_historical_metric(
        metric_ref="BTC_CONTEXT_SCORE",
        rule=rule,
        candles=primary,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": changed_momentum},
        companion_instrument_metadata={"BTCUSDT": _instrument("BTCUSDT")},
    )
    structure_changed = produce_research_v1_historical_metric(
        metric_ref="BTC_CONTEXT_SCORE",
        rule=rule,
        candles=primary,
        symbol="ETHUSDT",
        companion_candles={"BTCUSDT": changed_structure},
        companion_instrument_metadata={"BTCUSDT": _instrument("BTCUSDT")},
    )

    assert first.evidence_digest == reversed_order.evidence_digest
    assert first.evidence_digest != momentum_changed.evidence_digest
    assert first.evidence_digest != structure_changed.evidence_digest


def test_btc_context_score_trigger_uses_exact_pinned_version():
    rule = _rule("TR-R-018")
    btc = _btc_context_source_minutes()
    primary = (_primary_cutoff_candle("ETHUSDT", btc[-1].close_time),)

    evaluation = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=primary,
        symbol="ETHUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
        companion_candles={"BTCUSDT": btc},
        companion_instrument_metadata={"BTCUSDT": _instrument("BTCUSDT")},
    )[0]

    assert evaluation.trigger_id == "TR-R-018"
    assert evaluation.trigger_version == "1.0.0"
    assert evaluation.metric_ref == "BTC_CONTEXT_SCORE"
    assert evaluation.metric_value != "UNAVAILABLE"


def test_vnm_5m_z_parallel_atr_implementation_is_removed():
    source = Path("src/triggertrade/research_v1_historical_triggers.py").read_text(encoding="utf-8")

    assert "_true_range_5m" not in source
    assert "_atr_5m_series" not in source
    assert "_vnm_5m_series" not in source
    assert "_vnm_5m_z_observation" not in source
    assert "VNM_5m_z" not in HISTORICAL_READY_METRICS
    assert metric_readiness("VNM_5m_z") == "IMPLEMENTATION_MISSING"


def test_vnm_5m_z_stays_fail_closed_because_certified_atr_contract_is_15m_only():
    rule = _rule("TR-R-022")
    candles = _vnm_5m_source_minutes(days=1, extra_buckets=0)
    five_minute = historical_triggers._aggregate_completed_candles(candles, timeframe="5m")
    seed = tuple(historical_triggers._set_candle(candle) for candle in five_minute[1:15])

    seed_result = historical_triggers.wilder_atr_seed(seed_candles=seed, predecessor_close=str(five_minute[0].close))

    assert seed_result.status is historical_triggers.IndicatorStatus.UNAVAILABLE
    assert seed_result.reason_code == "candle timeframe mismatch"
    with pytest.raises(
        ResearchV1HistoricalTriggerInputUnavailable,
        match="research_v1_historical_metric_unavailable:VNM_5m_z",
    ):
        produce_research_v1_historical_metric(
            metric_ref="VNM_5m_z",
            rule=rule,
            candles=candles,
            symbol="BTCUSDT",
        )


def test_vnm_5m_z_trigger_remains_fail_closed_without_stale_observation_fallback():
    rule = _rule("TR-R-022")
    candles = _vnm_5m_source_minutes(days=16, extra_buckets=1)

    with pytest.raises(
        ResearchV1HistoricalTriggerInputUnavailable,
        match="research_v1_historical_trigger_input_unavailable:TR-R-022",
    ):
        evaluate_research_v1_historical_triggers(
            rules=(rule,),
            candles=candles,
            symbol="BTCUSDT",
            trigger_set_id="SET-R-UNIT",
            trigger_set_version="v1",
        )


def test_remaining_phase4_metrics_stay_fail_closed_without_factual_sources():
    candles = _vnm_5m_source_minutes(days=16, extra_buckets=1)

    for trigger_id, metric_ref in (
        ("TR-R-004", "classifier_direction"),
        ("TR-R-013", "AGGRESSIVE_VOLUME_DELTA_PCT"),
    ):
        with pytest.raises(
            ResearchV1HistoricalTriggerInputUnavailable,
            match=f"research_v1_historical_trigger_input_unavailable:{trigger_id}",
        ):
            evaluate_research_v1_historical_triggers(
                rules=(_rule(trigger_id),),
                candles=candles,
                symbol="BTCUSDT",
                trigger_set_id="SET-R-UNIT",
                trigger_set_version="v1",
            )
        assert metric_readiness(metric_ref) == "IMPLEMENTATION_MISSING"


def test_swing_sequence_state_requires_factual_tick_metadata():
    rule = _rule("TR-R-009")
    candles = _one_minute_buckets_1h(_bullish_swing_hourly_ohlc())

    evaluation = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )[0]

    assert evaluation.metric_value == "UNAVAILABLE"
    assert evaluation.output_state == "UNAVAILABLE"
    assert evaluation.condition_result is False
    assert metric_readiness("SWING_SEQUENCE_STATE(asset,1h)") == "HISTORICAL_READY"
    assert "SWING_SEQUENCE_STATE(asset,1h)" in HISTORICAL_READY_METRICS


def test_swing_sequence_state_rejects_zero_tick_and_wrong_metadata_binding():
    rule = _rule("TR-R-009")
    candles = _one_minute_buckets_1h(_bullish_swing_hourly_ohlc())

    zero_tick = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT", tick="0"),
    )
    wrong_binding = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("ETHUSDT"),
    )

    assert zero_tick.status == "UNAVAILABLE"
    assert zero_tick.reason_code == "research_v1_historical_swing_sequence_unavailable:INVALID_TICK_SIZE"
    assert wrong_binding.status == "UNAVAILABLE"
    assert wrong_binding.reason_code == "research_v1_historical_swing_sequence_unavailable:INSTRUMENT_BINDING_MISMATCH"


def test_swing_sequence_state_requires_revision_source_and_as_of_identity():
    rule = _rule("TR-R-009")
    candles = _one_minute_buckets_1h(_bullish_swing_hourly_ohlc())

    missing_revision = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT", revision=""),
    )
    missing_source = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT", source=""),
    )
    missing_as_of = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT", updated_at=""),
    )

    assert missing_revision.reason_code == "research_v1_historical_swing_sequence_unavailable:METADATA_REVISION_UNAVAILABLE"
    assert missing_source.reason_code == "research_v1_historical_swing_sequence_unavailable:METADATA_SOURCE_UNAVAILABLE"
    assert missing_as_of.reason_code == "research_v1_historical_swing_sequence_unavailable:METADATA_AS_OF_UNAVAILABLE"


def test_swing_sequence_state_rejects_loose_metadata_mapping():
    rule = _rule("TR-R-009")
    candles = _one_minute_buckets_1h(_bullish_swing_hourly_ohlc())

    loose_mapping = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata={  # type: ignore[arg-type]
            "symbol": "BTCUSDT",
            "tick_size": "0.5",
            "metadata_revision": "instrument:BTCUSDT:loose",
            "metadata_source": "unit-test-catalog",
            "updated_at": "2026-09-05T00:00:00+00:00",
        },
    )

    assert loose_mapping.status == "UNAVAILABLE"
    assert loose_mapping.reason_code == "research_v1_historical_swing_sequence_unavailable:INSTRUMENT_METADATA_UNAVAILABLE"


def test_swing_sequence_state_rejects_unsupported_contract_metadata():
    rule = _rule("TR-R-009")
    candles = _one_minute_buckets_1h(_bullish_swing_hourly_ohlc())

    wrong_contract = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT", contract_type="InversePerpetual"),
    )
    not_tradeable = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT", status="Settled", is_tradeable=False),
    )

    assert wrong_contract.reason_code == "research_v1_historical_swing_sequence_unavailable:UNSUPPORTED_INSTRUMENT_CONTRACT"
    assert not_tradeable.reason_code == "research_v1_historical_swing_sequence_unavailable:UNSUPPORTED_INSTRUMENT_CONTRACT"


def test_swing_sequence_state_uses_canonical_kernel_and_one_tick_equality():
    bullish = _rule("TR-R-009")
    bearish = _rule("TR-R-010")
    candles = _one_minute_buckets_1h(_bullish_swing_hourly_ohlc())

    bullish_eval, bearish_eval = evaluate_research_v1_historical_triggers(
        rules=(bullish, bearish),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
        instrument_metadata=_instrument("BTCUSDT", tick="0.5", revision="instrument:BTCUSDT:tick-0.5"),
    )

    assert bullish_eval.metric_ref == "SWING_SEQUENCE_STATE(asset,1h)"
    assert bullish_eval.metric_value == "BULLISH"
    assert bullish_eval.condition_result is True
    assert bearish_eval.metric_value == "BULLISH"
    assert bearish_eval.condition_result is False
    assert bullish_eval.signal.window == "1h"


def test_swing_sequence_state_one_tick_tolerance_can_change_state():
    rule = _rule("TR-R-009")
    candles = _one_minute_buckets_1h(_bullish_swing_hourly_ohlc())

    loose_tick = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT", tick="1.5", revision="instrument:BTCUSDT:tick-1.5"),
    )

    assert loose_tick.value == "AMBIGUOUS"
    payload = loose_tick.payload["swing_sequence_state"]
    assert payload["tick_equality"]["tick_size"] == "1.5"
    assert payload["tick_equality"]["metadata_revision"] == "instrument:BTCUSDT:tick-1.5"


def test_swing_sequence_state_accepts_pepe_logical_and_factual_instrument_binding():
    rule = _rule("TR-R-009")
    candles = _one_minute_buckets_1h(_bullish_swing_hourly_ohlc(), symbol="PEPEUSDT")

    observation = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="PEPEUSDT",
        instrument_metadata=_instrument("1000PEPEUSDT", tick="0.000001", revision="instrument:1000PEPEUSDT:1"),
    )

    assert observation.status == "AVAILABLE"
    assert observation.value == "BULLISH"
    metadata = observation.payload["swing_sequence_state"]["instrument_metadata"]
    assert metadata["logical_symbol"] == "PEPEUSDT"
    assert metadata["instrument_symbol"] == "1000PEPEUSDT"


def test_swing_sequence_state_1h_aggregation_is_gap_safe_and_excludes_partial_current_hour():
    rule = _rule("TR-R-009")
    candles = _one_minute_buckets_1h(_bullish_swing_hourly_ohlc())
    missing_constituent = tuple(candle for index, candle in enumerate(candles) if index != 3 * 60 + 17)
    partial_current = candles + tuple(replace(candles[-1], open_time=candles[-1].close_time, close_time=candles[-1].close_time + timedelta(minutes=1), completed=False) for _ in range(1))

    missing = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=missing_constituent,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
    )
    complete = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
    )
    with_partial = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=partial_current,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
    )

    assert missing.status == "UNAVAILABLE"
    assert missing.reason_code == "research_v1_historical_swing_sequence_unavailable:NON_CONTINUOUS_1H_WINDOW"
    assert complete.status == "AVAILABLE"
    assert with_partial.evidence_id == complete.evidence_id


def test_swing_sequence_state_confirmation_delay_and_no_future_leakage():
    rule = _rule("TR-R-009")
    candles = _one_minute_buckets_1h(_bullish_swing_hourly_ohlc())

    before_second_high_confirmed = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles[:-60],
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
    )
    confirmed = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
    )

    assert before_second_high_confirmed.status == "UNAVAILABLE"
    assert before_second_high_confirmed.reason_code == "research_v1_historical_swing_sequence_unavailable:INSUFFICIENT_CONFIRMED_SWING_POINTS"
    assert confirmed.value == "BULLISH"
    assert confirmed.payload["swing_sequence_state"]["selected_confirmed_highs"][-1]["confirmed_at"] == "2026-09-05T22:00:00+00:00"


def test_swing_sequence_state_deterministic_replay_and_provenance_binding():
    rule = _rule("TR-R-009")
    candles = _one_minute_buckets_1h(_bullish_swing_hourly_ohlc())
    changed = list(candles)
    changed[6 * 60 + 20] = replace(changed[6 * 60 + 20], high=Decimal("16"), close=Decimal("14"), turnover=Decimal("14"))

    first = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
    )
    second = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=tuple(reversed(candles)),
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
    )
    changed_observation = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=tuple(changed),
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT"),
    )
    changed_revision = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT", revision="instrument:BTCUSDT:2"),
    )
    changed_source = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT", source="unit-test-catalog-v2"),
    )
    changed_as_of = produce_research_v1_historical_metric(
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        rule=rule,
        candles=candles,
        symbol="BTCUSDT",
        instrument_metadata=_instrument("BTCUSDT", updated_at="2026-09-06T00:00:00+00:00"),
    )

    assert first.evidence_id == second.evidence_id
    assert first.evidence_id != changed_observation.evidence_id
    assert first.evidence_id != changed_revision.evidence_id
    assert first.evidence_id != changed_source.evidence_id
    assert first.evidence_id != changed_as_of.evidence_id


def test_btc_return_trigger_uses_factual_5m_return_and_directional_outputs():
    long_rule = _rule("TR-R-BTC-001")
    short_rule = _rule("TR-R-BTC-002")
    candles = tuple(_candle(index, close="100") for index in range(5)) + (_candle(5, close="101"),)

    long_eval, short_eval = evaluate_research_v1_historical_triggers(
        rules=(long_rule, short_rule),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-BTC-UNIT",
        trigger_set_version="v1",
    )

    assert long_eval.metric_ref == "RETURN(asset,5m)"
    assert long_eval.metric_value == "0.01"
    assert long_eval.output_state == "LONG"
    assert short_eval.output_state == "FALSE"
    assert short_eval.condition_result is False


def test_btc_return_trigger_requires_exact_contiguous_5m_interval():
    rule = _rule("TR-R-BTC-001")
    candles = (
        _candle(0, close="100"),
        _candle(1, close="100"),
        _candle(2, close="100"),
        _candle(4, close="100"),
        _candle(5, close="100"),
        _candle(6, close="101"),
    )

    evaluation = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-BTC-UNIT",
        trigger_set_version="v1",
    )[0]

    assert evaluation.metric_value == "UNAVAILABLE"
    assert evaluation.output_state == "UNAVAILABLE"
    assert evaluation.condition_result is False


def test_pepe_logical_symbol_remains_distinct_from_instrument_mapping_for_metric_identity():
    assert "PEPEUSDT" in RESEARCH_V1_SYMBOLS
    assert "1000PEPEUSDT" not in RESEARCH_V1_SYMBOLS
    rule = _rule("TR-R-BTC-001")
    candles = tuple(_candle(index, symbol="PEPEUSDT", close="100") for index in range(5)) + (
        _candle(5, symbol="PEPEUSDT", close="101"),
    )

    evaluation = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=candles,
        symbol="PEPEUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )[0]

    assert evaluation.signal.symbol == "PEPEUSDT"
    assert evaluation.metric_ref == "RETURN(asset,5m)"


def test_deterministic_replay_produces_same_metric_and_trigger_evidence():
    rule = _rule("TR-R-BTC-001")
    candles = tuple(_candle(index, close="100") for index in range(5)) + (_candle(5, close="101"),)

    first = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=candles,
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )[0]
    second = evaluate_research_v1_historical_triggers(
        rules=(rule,),
        candles=tuple(reversed(candles)),
        symbol="BTCUSDT",
        trigger_set_id="SET-R-UNIT",
        trigger_set_version="v1",
    )[0]

    assert first.metric_evidence_id == second.metric_evidence_id
    assert first.evidence_id == second.evidence_id
    assert first.signal.signal_id == second.signal.signal_id


def test_unsupported_required_metric_fails_closed_and_no_set_formation_occurs():
    candles = tuple(_candle(index, close="100") for index in range(6))

    unsupported_rule = _rule("TR-R-013")

    with pytest.raises(ResearchV1HistoricalTriggerInputUnavailable, match="research_v1_historical_trigger_input_unavailable:TR-R-013"):
        evaluate_research_v1_historical_triggers(
            rules=(unsupported_rule,),
            candles=candles,
            symbol="BTCUSDT",
            trigger_set_id="SET-R-BTC-UNIT",
            trigger_set_version="v1",
        )

    assert metric_readiness("DE") == "HISTORICAL_READY"
    assert metric_readiness("ATR percentile") == "HISTORICAL_READY"
    assert metric_readiness("BTC_CONTEXT_SCORE") == "HISTORICAL_READY"
    assert metric_readiness("RELATIVE_RETURN_15m") == "HISTORICAL_READY"
    assert metric_readiness("TOD_REL_TURNOVER") == "HISTORICAL_READY"
    assert metric_readiness("VNM_5m_z") == "IMPLEMENTATION_MISSING"
    assert "BTC_CONTEXT_SCORE" in HISTORICAL_READY_METRICS
    assert "RELATIVE_RETURN_15m" in HISTORICAL_READY_METRICS
    assert "TOD_REL_TURNOVER" in HISTORICAL_READY_METRICS
    assert "VNM_5m_z" not in HISTORICAL_READY_METRICS
    assert metric_readiness("AGGRESSIVE_VOLUME_DELTA_PCT") == "IMPLEMENTATION_MISSING"


def _rule(trigger_id: str) -> RuleDefinition:
    package = json.loads(Path("docs/research-import/triggers/RESEARCH_V1_TRIGGERS_WEB_IMPORT.json").read_text(encoding="utf-8"))
    record = next(item for item in package["records"] if item["canonical_trigger_id"] == trigger_id)
    payload = dict(record["rule_definition"])
    return RuleDefinition(
        rule_id=str(payload["rule_id"]),
        version=str(payload["version"]),
        name=str(payload["name"]),
        status=RuleStatus(str(payload["status"])),
        asset_scope=str(payload["asset_scope"]),
        rule_type=RuleType(str(payload["rule_type"])),
        condition=str(payload["condition"]),
        definition=dict(payload["definition"]),
        created_at=str(payload["created_at"]),
        provenance=str(payload["provenance"]),
        logical_name=payload.get("logical_name"),
        description=payload.get("description"),
        supersedes_version=payload.get("supersedes_version"),
        formula=payload.get("formula"),
        parameter_snapshot=payload.get("parameter_snapshot"),
        input_contract=payload.get("input_contract"),
        output_contract=payload.get("output_contract"),
        boundary_semantics=payload.get("boundary_semantics"),
        stale_data_semantics=payload.get("stale_data_semantics"),
        missing_data_semantics=payload.get("missing_data_semantics"),
    )


def _candle(
    index: int,
    *,
    symbol: str = "BTCUSDT",
    close: str = "100",
    high: str | None = None,
    low: str | None = None,
    volume: str = "1",
) -> HistoricalCandle:
    start = datetime(2026, 9, 5, 13, 0, tzinfo=UTC) + timedelta(minutes=index)
    close_value = Decimal(close)
    high_value = Decimal(high) if high is not None else close_value
    low_value = Decimal(low) if low is not None else close_value
    return HistoricalCandle(
        symbol=symbol,
        category="linear",
        timeframe="1m",
        open_time=start,
        close_time=start + timedelta(minutes=1),
        open=close_value,
        high=high_value,
        low=low_value,
        close=close_value,
        volume=Decimal(volume),
        turnover=close_value * Decimal(volume),
        completed=True,
    )


def _one_minute_buckets_15m(closes: tuple[str, ...], *, symbol: str = "BTCUSDT") -> tuple[HistoricalCandle, ...]:
    candles: list[HistoricalCandle] = []
    for bucket_index, close in enumerate(closes):
        for minute in range(15):
            candles.append(_candle(bucket_index * 15 + minute, symbol=symbol, close=close, high=close, low=close))
    return tuple(candles)


def _flat_atr_source_minutes(*, days: int, extra_buckets: int) -> tuple[HistoricalCandle, ...]:
    total_minutes = days * 24 * 60 + extra_buckets * 15
    start = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
    candles: list[HistoricalCandle] = []
    for index in range(total_minutes):
        opened = start + timedelta(minutes=index)
        close_value = Decimal("100")
        candles.append(
            HistoricalCandle(
                symbol="BTCUSDT",
                category="linear",
                timeframe="1m",
                open_time=opened,
                close_time=opened + timedelta(minutes=1),
                open=close_value,
                high=Decimal("101"),
                low=Decimal("99"),
                close=close_value,
                volume=Decimal("1"),
                turnover=close_value,
                completed=True,
            )
        )
    return tuple(candles)


def _same_clock_5m_turnover_minutes(
    *,
    current_turnover: str,
    prior_turnovers: tuple[str, ...],
    missing_offsets: set[int] | None = None,
) -> tuple[HistoricalCandle, ...]:
    missing_offsets = missing_offsets or set()
    current_start = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)
    candles: list[HistoricalCandle] = []
    entries = [(0, current_turnover)] + [
        (offset, turnover)
        for offset, turnover in enumerate(prior_turnovers, start=1)
        if offset not in missing_offsets
    ]
    for offset, turnover in entries:
        bucket_start = current_start - timedelta(days=offset)
        minute_turnover = Decimal(turnover) / Decimal("5")
        close = Decimal("10")
        volume = minute_turnover / close
        for minute in range(5):
            opened = bucket_start + timedelta(minutes=minute)
            candles.append(
                HistoricalCandle(
                    symbol="BTCUSDT",
                    category="linear",
                    timeframe="1m",
                    open_time=opened,
                    close_time=opened + timedelta(minutes=1),
                    open=close,
                    high=close,
                    low=close,
                    close=close,
                    volume=volume,
                    turnover=minute_turnover,
                    completed=True,
                )
            )
    return tuple(candles)


def _relative_return_15m_streams(
    *,
    asset_previous: str = "100",
    asset_current: str = "102",
    btc_previous: str = "200",
    btc_current: str = "202",
    extra_future: bool = False,
) -> tuple[tuple[HistoricalCandle, ...], tuple[HistoricalCandle, ...]]:
    start = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)
    asset_closes = (asset_previous,) * 15 + (asset_current,) * 15
    btc_closes = (btc_previous,) * 15 + (btc_current,) * 15
    if extra_future:
        asset_closes = asset_closes + ("150",) * 15
        btc_closes = btc_closes + ("300",) * 15
    return (
        _minute_stream_from_closes(symbol="ETHUSDT", start=start, closes=asset_closes),
        _minute_stream_from_closes(symbol="BTCUSDT", start=start, closes=btc_closes),
    )


def _btc_context_source_minutes(
    *,
    days: int = 16,
    extra_future: bool = False,
    structure_state: str = "bullish",
) -> tuple[HistoricalCandle, ...]:
    start = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
    total_minutes = days * 24 * 60 + 15
    if extra_future:
        total_minutes += 15
    candles: list[HistoricalCandle] = []
    for index in range(total_minutes):
        opened = start + timedelta(minutes=index)
        bucket = index // 15
        close = Decimal("100") + Decimal(bucket) / Decimal("500") + Decimal(bucket % 11) / Decimal("100")
        candles.append(
            HistoricalCandle(
                symbol="BTCUSDT",
                category="linear",
                timeframe="1m",
                open_time=opened,
                close_time=opened + timedelta(minutes=1),
                open=close,
                high=close + Decimal("1"),
                low=close - Decimal("1"),
                close=close,
                volume=Decimal("1"),
                turnover=close,
                completed=True,
            )
        )
    pattern = _bullish_swing_hourly_ohlc() if structure_state == "bullish" else _bearish_swing_hourly_ohlc()
    overlay_start = start + timedelta(days=days) - timedelta(hours=len(pattern))
    by_open = {candle.open_time: index for index, candle in enumerate(candles)}
    for hour_index, (high, low, close) in enumerate(pattern):
        high_value = Decimal(high)
        low_value = Decimal(low)
        close_value = Decimal(close)
        hour_start = overlay_start + timedelta(hours=hour_index)
        for minute in range(60):
            opened = hour_start + timedelta(minutes=minute)
            index = by_open[opened]
            minute_close = close_value
            candles[index] = replace(
                candles[index],
                open=minute_close,
                high=high_value,
                low=low_value,
                close=minute_close,
                volume=Decimal("1"),
                turnover=minute_close,
            )
    return tuple(candles)


def _flat_btc_return_z_minutes() -> tuple[HistoricalCandle, ...]:
    start = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
    total_minutes = 16 * 24 * 60 + 15
    candles: list[HistoricalCandle] = []
    for index in range(total_minutes):
        opened = start + timedelta(minutes=index)
        close = Decimal("100")
        candles.append(
            HistoricalCandle(
                symbol="BTCUSDT",
                category="linear",
                timeframe="1m",
                open_time=opened,
                close_time=opened + timedelta(minutes=1),
                open=close,
                high=close,
                low=close,
                close=close,
                volume=Decimal("1"),
                turnover=close,
                completed=True,
            )
        )
    return tuple(candles)


def _primary_cutoff_candle(symbol: str, close_time: datetime) -> HistoricalCandle:
    close = Decimal("100")
    return HistoricalCandle(
        symbol=symbol,
        category="linear",
        timeframe="1m",
        open_time=close_time - timedelta(minutes=1),
        close_time=close_time,
        open=close,
        high=close,
        low=close,
        close=close,
        volume=Decimal("1"),
        turnover=close,
        completed=True,
    )


def _minute_stream_from_closes(
    *,
    symbol: str,
    start: datetime,
    closes: tuple[str, ...],
) -> tuple[HistoricalCandle, ...]:
    candles: list[HistoricalCandle] = []
    for index, close in enumerate(closes):
        opened = start + timedelta(minutes=index)
        close_value = Decimal(close)
        candles.append(
            HistoricalCandle(
                symbol=symbol,
                category="linear",
                timeframe="1m",
                open_time=opened,
                close_time=opened + timedelta(minutes=1),
                open=close_value,
                high=close_value,
                low=close_value,
                close=close_value,
                volume=Decimal("1"),
                turnover=close_value,
                completed=True,
            )
        )
    return tuple(candles)


def _vnm_5m_source_minutes(*, days: int, extra_buckets: int) -> tuple[HistoricalCandle, ...]:
    total_minutes = days * 24 * 60 + extra_buckets * 5
    start = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
    candles: list[HistoricalCandle] = []
    for index in range(total_minutes):
        opened = start + timedelta(minutes=index)
        bucket = index // 5
        minute = index % 5
        trend = Decimal(bucket) / Decimal("200")
        oscillation = Decimal((bucket % 17) - 8) / Decimal("100")
        close = Decimal("100") + trend + oscillation + Decimal(minute) / Decimal("1000")
        high = close + Decimal("1") + Decimal(bucket % 5) / Decimal("100")
        low = close - Decimal("1") - Decimal(bucket % 3) / Decimal("100")
        volume = Decimal("1") + Decimal(bucket % 7) / Decimal("10")
        candles.append(
            HistoricalCandle(
                symbol="BTCUSDT",
                category="linear",
                timeframe="1m",
                open_time=opened,
                close_time=opened + timedelta(minutes=1),
                open=close,
                high=high,
                low=low,
                close=close,
                volume=volume,
                turnover=close * volume,
                completed=True,
            )
        )
    return tuple(candles)


def _bullish_swing_hourly_ohlc() -> tuple[tuple[str, str, str], ...]:
    return (
        ("10", "8", "9"),
        ("11", "7", "10"),
        ("13", "6", "9"),
        ("12", "8", "10"),
        ("11", "9", "10"),
        ("12", "7", "10"),
        ("15", "10", "14"),
        ("14", "11", "13"),
        ("13", "12", "13"),
    )


def _bearish_swing_hourly_ohlc() -> tuple[tuple[str, str, str], ...]:
    return (
        ("15", "13", "14"),
        ("16", "12", "15"),
        ("18", "11", "14"),
        ("17", "13", "15"),
        ("16", "14", "15"),
        ("15", "10", "11"),
        ("14", "8", "9"),
        ("13", "9", "10"),
        ("12", "10", "11"),
    )


def _one_minute_buckets_1h(
    hourly: tuple[tuple[str, str, str], ...],
    *,
    symbol: str = "BTCUSDT",
) -> tuple[HistoricalCandle, ...]:
    start = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    candles: list[HistoricalCandle] = []
    for hour_index, (high, low, close) in enumerate(hourly):
        high_value = Decimal(high)
        low_value = Decimal(low)
        close_value = Decimal(close)
        open_value = close_value
        for minute in range(60):
            opened = start + timedelta(hours=hour_index, minutes=minute)
            minute_high = high_value if minute == 20 else max(open_value, close_value)
            minute_low = low_value if minute == 20 else min(open_value, close_value)
            candles.append(
                HistoricalCandle(
                    symbol=symbol,
                    category="linear",
                    timeframe="1m",
                    open_time=opened,
                    close_time=opened + timedelta(minutes=1),
                    open=open_value,
                    high=minute_high,
                    low=minute_low,
                    close=close_value,
                    volume=Decimal("1"),
                    turnover=close_value,
                    completed=True,
                )
            )
    return tuple(candles)


def _instrument(
    symbol: str,
    *,
    tick: str = "0.5",
    revision: str | None = None,
    source: str = "unit-test-catalog",
    updated_at: str = "2026-09-05T00:00:00+00:00",
    contract_type: str = "LinearPerpetual",
    status: str = "Trading",
    is_tradeable: bool = True,
) -> FuturesInstrument:
    base_coin = symbol.removesuffix("USDT")
    return FuturesInstrument(
        symbol=symbol,
        base_coin=base_coin,
        quote_coin="USDT",
        settle_coin="USDT",
        contract_type=contract_type,
        status=status,
        tick_size=Decimal(tick),
        price_scale=1,
        min_order_qty=Decimal("0.001"),
        max_order_qty=Decimal("1000"),
        qty_step=Decimal("0.001"),
        min_notional_value=Decimal("5"),
        max_market_order_qty=Decimal("1000"),
        min_leverage=Decimal("1"),
        max_leverage=Decimal("100"),
        leverage_step=Decimal("0.01"),
        launch_time=None,
        delivery_time=None,
        is_tradeable=is_tradeable,
        updated_at=updated_at,
        source=source,
        catalog_hash=f"instrument:{symbol}:1" if revision is None else revision,
    )
