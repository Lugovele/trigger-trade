from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
import re

import pytest

from triggertrade.backtest.models import HistoricalCandle
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


def test_swing_sequence_state_remains_fail_closed_without_factual_tick_metadata():
    rule = _rule("TR-R-009")
    candles = _one_minute_buckets_15m(tuple(str(100 + index) for index in range(20)))

    with pytest.raises(
        ResearchV1HistoricalTriggerInputUnavailable,
        match="research_v1_historical_trigger_input_unavailable:TR-R-009",
    ):
        evaluate_research_v1_historical_triggers(
            rules=(rule,),
            candles=candles,
            symbol="BTCUSDT",
            trigger_set_id="SET-R-UNIT",
            trigger_set_version="v1",
        )

    assert metric_readiness("SWING_SEQUENCE_STATE(asset,1h)") == "KERNEL_EXISTS_BUT_ADAPTER_MISSING"
    assert "SWING_SEQUENCE_STATE(asset,1h)" not in HISTORICAL_READY_METRICS


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
    rule = _rule("TR-R-BTC-005")
    candles = tuple(_candle(index, close="100") for index in range(6))

    unsupported_rule = _rule("TR-R-BTC-008")

    with pytest.raises(ResearchV1HistoricalTriggerInputUnavailable, match="research_v1_historical_trigger_input_unavailable:TR-R-BTC-008"):
        evaluate_research_v1_historical_triggers(
            rules=(unsupported_rule,),
            candles=candles,
            symbol="BTCUSDT",
            trigger_set_id="SET-R-BTC-UNIT",
            trigger_set_version="v1",
        )

    assert metric_readiness("DE") == "HISTORICAL_READY"
    assert metric_readiness("ATR percentile") == "HISTORICAL_READY"
    assert metric_readiness("TOD_REL_TURNOVER") == "IMPLEMENTATION_MISSING"
    assert "TOD_REL_TURNOVER" not in HISTORICAL_READY_METRICS


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
