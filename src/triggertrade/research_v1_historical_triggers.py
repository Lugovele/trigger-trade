"""Research V1 historical metric and trigger evaluation.

This module is intentionally Phase 1 only: it produces factual metric
observations and declarative trigger evaluations from completed historical
candles. It does not form Sets, resolve direction, create Market Handoffs, or
enter Position.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from typing import Any

from triggertrade.backtest.models import HistoricalCandle
from triggertrade.canonical_json import canonical_decimal_text as canonical_json_decimal_text
from triggertrade.canonical_json import canonical_json_digest
from triggertrade.numeric_policy import NumericPolicyError, canonical_decimal_text, exact_divide, q36_working
from triggertrade.set_engine import (
    Candle,
    IndicatorStatus,
    TriggerResult,
    directional_efficiency,
    evaluate_f001_price_displacement,
    evaluate_f002_participation,
    wilder_atr_seed,
    wilder_atr_update,
)
from triggertrade.trigger_sets import RuleDefinition
from triggertrade.triggers import DeclarativeMetricPredicateTrigger, DeclarativeTriggerContext, Signal


RESEARCH_V1_HISTORICAL_TRIGGER_PRODUCER_VERSION = "research-v1-historical-trigger-producer-v1"

_AGGREGATED_CANDLE_CONSTITUENTS: dict[int, tuple[str, ...]] = {}

HISTORICAL_READY_METRICS = frozenset(
    {
        "F-001 trigger_result",
        "F-002 trigger_result",
        "ATR percentile",
        "DE",
        "RETURN(asset,5m)",
    }
)

KERNEL_EXISTS_BUT_ADAPTER_MISSING_METRICS = frozenset(
    {
        "SWING_SEQUENCE_STATE(asset,1h)",
    }
)

IMPLEMENTATION_MISSING_METRICS = frozenset(
    {
        "AGGRESSIVE_VOLUME_DELTA_PCT",
        "BTC_CONTEXT_SCORE",
        "RELATIVE_RETURN_15m",
        "TOD_REL_TURNOVER",
        "VNM_5m_z",
        "classifier_direction",
    }
)


class ResearchV1HistoricalTriggerError(ValueError):
    """Raised when factual historical trigger evaluation cannot proceed."""


class ResearchV1HistoricalTriggerInputUnavailable(ResearchV1HistoricalTriggerError):
    """Raised for unsupported or unavailable factual trigger inputs."""


@dataclass(frozen=True)
class HistoricalMetricObservation:
    metric_ref: str
    value: str
    status: str
    observed_at: str
    available_at: str
    source_candle_ids: tuple[str, ...]
    evidence_id: str
    evidence_digest: str
    reason_code: str | None = None
    payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class HistoricalTriggerEvaluation:
    trigger_id: str
    trigger_version: str
    metric_ref: str
    metric_value: str
    operator: str
    threshold: str
    condition_result: bool
    output_state: str
    signal_type: str
    observed_at: str
    available_at: str
    evidence_id: str
    evidence_digest: str
    metric_evidence_id: str
    metric_evidence_digest: str
    signal: Signal


def metric_readiness(metric_ref: str) -> str:
    """Classify a Research V1 metric reference for historical replay readiness."""

    if metric_ref in HISTORICAL_READY_METRICS:
        return "HISTORICAL_READY"
    if metric_ref in KERNEL_EXISTS_BUT_ADAPTER_MISSING_METRICS:
        return "KERNEL_EXISTS_BUT_ADAPTER_MISSING"
    if metric_ref in IMPLEMENTATION_MISSING_METRICS:
        return "IMPLEMENTATION_MISSING"
    return "IMPLEMENTATION_MISSING"


def evaluate_research_v1_historical_triggers(
    *,
    rules: Sequence[RuleDefinition],
    candles: Sequence[HistoricalCandle],
    symbol: str,
    trigger_set_id: str,
    trigger_set_version: str,
    observed_at: datetime | None = None,
) -> tuple[HistoricalTriggerEvaluation, ...]:
    """Evaluate pinned declarative Research V1 triggers from factual candles.

    Unsupported required metric references fail closed with a deterministic
    `research_v1_historical_trigger_input_unavailable:<trigger_id>` reason.
    """

    results: list[HistoricalTriggerEvaluation] = []
    for rule in rules:
        metric_ref = _metric_ref(rule)
        if metric_ref not in HISTORICAL_READY_METRICS:
            raise ResearchV1HistoricalTriggerInputUnavailable(
                f"research_v1_historical_trigger_input_unavailable:{rule.rule_id}"
            )
        observation = produce_research_v1_historical_metric(
            metric_ref=metric_ref,
            rule=rule,
            candles=candles,
            symbol=symbol,
            observed_at=observed_at,
        )
        context_time = _parse_iso(observation.observed_at)
        signal = DeclarativeMetricPredicateTrigger(rule).evaluate(
            DeclarativeTriggerContext(
                symbol=symbol.upper(),
                observed_at=context_time,
                window=_metric_context_window(metric_ref),
                metric_values={metric_ref: observation.value},
                source=f"{RESEARCH_V1_HISTORICAL_TRIGGER_PRODUCER_VERSION}:{observation.evidence_id}",
                lane="BACKTEST",
                trigger_set_id=trigger_set_id,
                trigger_set_version=trigger_set_version,
            )
        )
        output_state = str(signal.input_snapshot.get("output_state") or "")
        digest_basis = {
            "producer": RESEARCH_V1_HISTORICAL_TRIGGER_PRODUCER_VERSION,
            "trigger_id": rule.rule_id,
            "trigger_version": rule.version,
            "metric_evidence_digest": observation.evidence_digest,
            "signal_id": signal.signal_id,
            "condition_result": signal.condition_result,
            "output_state": output_state,
        }
        evidence_digest = canonical_json_digest(digest_basis)
        results.append(
            HistoricalTriggerEvaluation(
                trigger_id=rule.rule_id,
                trigger_version=rule.version,
                metric_ref=metric_ref,
                metric_value=observation.value,
                operator=str(rule.definition.get("operator") or ""),
                threshold=str(rule.definition.get("threshold") or ""),
                condition_result=signal.condition_result,
                output_state=output_state,
                signal_type=signal.signal_type.value,
                observed_at=observation.observed_at,
                available_at=observation.available_at,
                evidence_id=f"rv1-trigger-eval-{evidence_digest[:24]}",
                evidence_digest=evidence_digest,
                metric_evidence_id=observation.evidence_id,
                metric_evidence_digest=observation.evidence_digest,
                signal=signal,
            )
        )
    return tuple(results)


def produce_research_v1_historical_metric(
    *,
    metric_ref: str,
    rule: RuleDefinition,
    candles: Sequence[HistoricalCandle],
    symbol: str,
    observed_at: datetime | None = None,
) -> HistoricalMetricObservation:
    """Produce one factual Research V1 metric observation from historical candles."""

    if metric_ref not in HISTORICAL_READY_METRICS:
        raise ResearchV1HistoricalTriggerInputUnavailable(f"research_v1_historical_metric_unavailable:{metric_ref}")
    ordered = _eligible_candles(
        candles,
        symbol=symbol,
        observed_at=observed_at,
        timeframe=_metric_source_timeframe(metric_ref),
    )
    if not ordered:
        raise ResearchV1HistoricalTriggerInputUnavailable(f"research_v1_historical_metric_unavailable:{metric_ref}")
    return _metric_observation(metric_ref=metric_ref, rule=rule, candles=ordered)


def _metric_observation(
    *,
    metric_ref: str,
    rule: RuleDefinition,
    candles: Sequence[HistoricalCandle],
) -> HistoricalMetricObservation:
    if metric_ref == "F-001 trigger_result":
        return _f001_observation(rule=rule, candles=candles)
    if metric_ref == "F-002 trigger_result":
        return _f002_observation(candles=candles)
    if metric_ref == "DE":
        return _de_observation(candles=candles)
    if metric_ref == "ATR percentile":
        return _atr_percentile_observation(candles=candles)
    if metric_ref == "RETURN(asset,5m)":
        return _return_5m_observation(candles=candles)
    raise ResearchV1HistoricalTriggerInputUnavailable(f"research_v1_historical_metric_unavailable:{metric_ref}")


def _f001_observation(*, rule: RuleDefinition, candles: Sequence[HistoricalCandle]) -> HistoricalMetricObservation:
    if len(candles) < 2:
        return _unavailable_observation("F-001 trigger_result", candles, reason_code="INSUFFICIENT_HISTORY")
    if not _is_contiguous_one_minute_window(candles[-2:]):
        return _unavailable_observation("F-001 trigger_result", candles, reason_code="NON_CONTINUOUS_1M_WINDOW")
    theta = _theta_move_pct(rule)
    reference = _set_candle(candles[-2])
    observed = _set_candle(candles[-1])
    result = evaluate_f001_price_displacement(
        reference=reference,
        observed=observed,
        theta_move_pct=theta,
        requested_slot=_iso(candles[-1].close_time),
    )
    value = result.trigger_result.value
    status = "AVAILABLE" if result.arithmetic_status is IndicatorStatus.AVAILABLE else "UNAVAILABLE"
    return _observation(
        metric_ref="F-001 trigger_result",
        value=value,
        status=status,
        candles=(candles[-2], candles[-1]),
        reason_code=result.reason_code,
        payload=result.to_payload(),
    )


def _f002_observation(*, candles: Sequence[HistoricalCandle]) -> HistoricalMetricObservation:
    if len(candles) < 61:
        return _unavailable_observation("F-002 trigger_result", candles, reason_code="INSUFFICIENT_HISTORY")
    if not _is_contiguous_one_minute_window(candles[-61:]):
        return _unavailable_observation("F-002 trigger_result", candles, reason_code="NON_CONTINUOUS_1M_WINDOW")
    current = _set_candle(candles[-1])
    historical = tuple(_set_candle(item) for item in candles[-61:-1])
    result = evaluate_f002_participation(
        current=current,
        historical=historical,
        evaluation_slot=_iso(candles[-1].close_time),
    )
    value = result.trigger_result.value
    status = "AVAILABLE" if result.status is IndicatorStatus.AVAILABLE else "UNAVAILABLE"
    return _observation(
        metric_ref="F-002 trigger_result",
        value=value,
        status=status,
        candles=tuple(candles[-61:]),
        reason_code=result.reason_code,
        payload=result.to_payload(),
    )


def _return_5m_observation(*, candles: Sequence[HistoricalCandle]) -> HistoricalMetricObservation:
    if len(candles) < 6:
        return _unavailable_observation("RETURN(asset,5m)", candles, reason_code="INSUFFICIENT_HISTORY")
    window = tuple(candles[-6:])
    if not _is_contiguous_one_minute_window(window):
        return _unavailable_observation("RETURN(asset,5m)", candles, reason_code="NON_CONTINUOUS_5M_WINDOW")
    reference = window[0]
    current = candles[-1]
    try:
        reference_close = Fraction(reference.close)
        current_close = Fraction(current.close)
        if reference_close <= 0:
            raise NumericPolicyError("reference close must be positive")
        value = canonical_decimal_text(q36_working(exact_divide(current_close - reference_close, reference_close)).value)
        return _observation(
            metric_ref="RETURN(asset,5m)",
            value=value,
            status="AVAILABLE",
            candles=window,
            reason_code=None,
            payload={
                "return_5m": {
                    "status": "AVAILABLE",
                    "reference_candle_id": _candle_id(reference),
                    "current_candle_id": _candle_id(current),
                    "source_window_candle_ids": tuple(_candle_id(candle) for candle in window),
                    "value": value,
                }
            },
        )
    except (ArithmeticError, NumericPolicyError, ValueError) as exc:
        return _observation(
            metric_ref="RETURN(asset,5m)",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=window,
            reason_code=str(exc),
            payload={"return_5m": {"status": "UNAVAILABLE", "reason_code": str(exc)}},
        )


def _de_observation(*, candles: Sequence[HistoricalCandle]) -> HistoricalMetricObservation:
    fifteen_minute = _aggregate_completed_candles(candles, timeframe="15m")
    if len(fifteen_minute) < 9:
        return _unavailable_observation("DE", candles, reason_code="research_v1_historical_de_unavailable:INSUFFICIENT_HISTORY")
    window = tuple(fifteen_minute[-9:])
    if not _is_contiguous_window(window, timedelta(minutes=15)):
        return _unavailable_observation("DE", candles, reason_code="research_v1_historical_de_unavailable:NON_CONTINUOUS_15M_WINDOW")
    try:
        value = directional_efficiency(closes=tuple(_decimal_text(candle.close) for candle in window))
        if value is None:
            raise NumericPolicyError("DE unavailable")
        return _observation(
            metric_ref="DE",
            value=value,
            status="AVAILABLE",
            candles=window,
            reason_code=None,
            payload={
                "directional_efficiency": {
                    "status": "AVAILABLE",
                    "input_timeframe": "15m",
                    "window": 8,
                    "source_window_candle_ids": tuple(_candle_id(candle) for candle in window),
                    "value": value,
                }
            },
        )
    except (NumericPolicyError, ValueError) as exc:
        return _observation(
            metric_ref="DE",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=window,
            reason_code=f"research_v1_historical_de_unavailable:{exc}",
            payload={"directional_efficiency": {"status": "UNAVAILABLE", "reason_code": str(exc)}},
        )


def _atr_percentile_observation(*, candles: Sequence[HistoricalCandle]) -> HistoricalMetricObservation:
    fifteen_minute = _aggregate_completed_candles(candles, timeframe="15m")
    if len(fifteen_minute) < 15:
        return _unavailable_observation(
            "ATR percentile",
            candles,
            reason_code="research_v1_historical_atr_percentile_unavailable:INSUFFICIENT_ATR_HISTORY",
        )
    if not _is_contiguous_window(fifteen_minute, timedelta(minutes=15)):
        return _unavailable_observation(
            "ATR percentile",
            candles,
            reason_code="research_v1_historical_atr_percentile_unavailable:NON_CONTINUOUS_15M_ATR_CHAIN",
        )
    series = _atr_pct_series(fifteen_minute)
    if not series:
        return _unavailable_observation(
            "ATR percentile",
            candles,
            reason_code="research_v1_historical_atr_percentile_unavailable:ATR_SERIES_UNAVAILABLE",
        )
    current_candle, current_update = series[-1]
    if current_update.atr_pct_work is None or current_update.status is not IndicatorStatus.AVAILABLE:
        return _observation(
            metric_ref="ATR percentile",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(current_candle,),
            reason_code="research_v1_historical_atr_percentile_unavailable:CURRENT_ATR_PCT_UNAVAILABLE",
            payload={"atr_percentile": {"status": "UNAVAILABLE", "atr_update": current_update.to_payload()}},
        )
    reference_population = _eligible_atr_percentile_reference_population(series, evaluation_at=current_candle.close_time)
    if reference_population is None:
        return _observation(
            metric_ref="ATR percentile",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(current_candle,),
            reason_code="research_v1_historical_atr_percentile_unavailable:INSUFFICIENT_COMPLETED_UTC_DAYS",
            payload={"atr_percentile": {"status": "UNAVAILABLE", "minimum_warmup_days": 14}},
        )
    try:
        current = Fraction(Decimal(current_update.atr_pct_work))
        reference_values = tuple(Fraction(Decimal(value)) for value in reference_population["values"])
        count = len(reference_values)
        rank = sum(1 for value in reference_values if value <= current)
        percentile = canonical_decimal_text(q36_working(exact_divide(100 * rank, count)).value)
    except (ArithmeticError, NumericPolicyError, ValueError) as exc:
        return _observation(
            metric_ref="ATR percentile",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(current_candle,),
            reason_code=f"research_v1_historical_atr_percentile_unavailable:{exc}",
            payload={"atr_percentile": {"status": "UNAVAILABLE", "reason_code": str(exc)}},
        )
    return _observation(
        metric_ref="ATR percentile",
        value=percentile,
        status="AVAILABLE",
        candles=(current_candle,),
        reason_code=None,
        payload={
            "atr_percentile": {
                "status": "AVAILABLE",
                "input_timeframe": "15m",
                "atr_window": 14,
                "smoothing": "Wilder",
                "lookback": "30_completed_UTC_calendar_days",
                "minimum_warmup_days": 14,
                "reference_count": count,
                "rank_count": rank,
                "comparison": "reference <= current",
                "selection_start": reference_population["selection_start"],
                "selection_end": reference_population["selection_end"],
                "eligible_completed_utc_days": reference_population["eligible_completed_utc_days"],
                "reference_population_digest": reference_population["reference_population_digest"],
                "reference_observation_count": reference_population["reference_observation_count"],
                "current_atr_observation_digest": _atr_observation_provenance(current_candle, current_update)["digest"],
                "current_atr_pct_work": current_update.atr_pct_work,
                "current_atr_update": current_update.to_payload(),
                "value": percentile,
            }
        },
    )


def _eligible_candles(
    candles: Sequence[HistoricalCandle],
    *,
    symbol: str,
    observed_at: datetime | None,
    timeframe: str,
) -> tuple[HistoricalCandle, ...]:
    symbol = symbol.upper()
    selected = tuple(
        candle
        for candle in sorted(candles, key=lambda item: item.close_time)
        if candle.symbol.upper() == symbol
        and candle.timeframe == timeframe
        and candle.category == "linear"
        and candle.completed
        and (observed_at is None or candle.close_time <= observed_at)
    )
    seen: set[datetime] = set()
    for candle in selected:
        if candle.close_time.tzinfo is None or candle.open_time.tzinfo is None:
            raise ResearchV1HistoricalTriggerInputUnavailable("research_v1_historical_trigger_inputs_unavailable:naive_timestamp")
        if candle.close_time in seen:
            raise ResearchV1HistoricalTriggerInputUnavailable("research_v1_historical_trigger_inputs_unavailable:duplicate_candle")
        seen.add(candle.close_time)
        if min(candle.open, candle.high, candle.low, candle.close, candle.volume, candle.turnover) < Decimal("0"):
            raise ResearchV1HistoricalTriggerInputUnavailable("research_v1_historical_trigger_inputs_unavailable:negative_candle_value")
        if candle.low > candle.close or candle.close > candle.high:
            raise ResearchV1HistoricalTriggerInputUnavailable("research_v1_historical_trigger_inputs_unavailable:invalid_ohlc")
    return selected


def _aggregate_completed_candles(candles: Sequence[HistoricalCandle], *, timeframe: str) -> tuple[HistoricalCandle, ...]:
    source = tuple(candles)
    if not source:
        return ()
    duration = _timeframe_delta(timeframe)
    per_bucket = int(duration / timedelta(minutes=1))
    buckets: dict[datetime, list[HistoricalCandle]] = {}
    for candle in source:
        start = _bucket_start(candle.open_time, duration)
        buckets.setdefault(start, []).append(candle)
    aggregated: list[HistoricalCandle] = []
    for bucket_start in sorted(buckets):
        bucket = tuple(sorted(buckets[bucket_start], key=lambda item: item.open_time))
        expected_open_times = tuple(bucket_start + timedelta(minutes=index) for index in range(per_bucket))
        if len(bucket) != per_bucket:
            continue
        if tuple(item.open_time.astimezone(UTC) for item in bucket) != expected_open_times:
            continue
        if not _is_contiguous_one_minute_window(bucket):
            continue
        aggregated_candle = HistoricalCandle(
            symbol=bucket[0].symbol.upper(),
            category=bucket[0].category,
            timeframe=timeframe,
            open_time=bucket_start,
            close_time=bucket_start + duration,
            open=bucket[0].open,
            high=max(item.high for item in bucket),
            low=min(item.low for item in bucket),
            close=bucket[-1].close,
            volume=sum((item.volume for item in bucket), Decimal("0")),
            turnover=sum((item.turnover for item in bucket), Decimal("0")),
            completed=True,
        )
        _AGGREGATED_CANDLE_CONSTITUENTS[id(aggregated_candle)] = tuple(_candle_id(item) for item in bucket)
        aggregated.append(aggregated_candle)
    return tuple(aggregated)


def _atr_pct_series(candles: Sequence[HistoricalCandle]) -> tuple[tuple[HistoricalCandle, Any], ...]:
    ordered = tuple(candles)
    if len(ordered) < 15:
        return ()
    seed_candles = tuple(_set_candle(candle) for candle in ordered[1:15])
    seed = wilder_atr_seed(seed_candles=seed_candles, predecessor_close=_decimal_text(ordered[0].close))
    if seed.status is not IndicatorStatus.AVAILABLE or seed.atr_work is None:
        return ()
    series: list[tuple[HistoricalCandle, Any]] = [(ordered[14], seed)]
    prior_atr = seed.atr_work
    for index in range(15, len(ordered)):
        update = wilder_atr_update(
            prior_atr_work=prior_atr,
            candle=_set_candle(ordered[index]),
            previous_close=_decimal_text(ordered[index - 1].close),
        )
        if update.status is not IndicatorStatus.AVAILABLE or update.atr_work is None:
            return tuple(series)
        series.append((ordered[index], update))
        prior_atr = update.atr_work
    return tuple(series)


def _eligible_atr_percentile_reference_population(
    series: Sequence[tuple[HistoricalCandle, Any]],
    *,
    evaluation_at: datetime,
) -> dict[str, Any] | None:
    evaluation_day = evaluation_at.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start = evaluation_day - timedelta(days=30)
    grouped: dict[datetime, list[dict[str, Any]]] = {}
    for candle, update in series:
        opened = candle.open_time.astimezone(UTC)
        closed = candle.close_time.astimezone(UTC)
        if opened < start or closed > evaluation_day:
            continue
        if update.atr_pct_work is None:
            continue
        day = opened.replace(hour=0, minute=0, second=0, microsecond=0)
        grouped.setdefault(day, []).append(_atr_observation_provenance(candle, update))
    eligible: list[dict[str, Any]] = []
    eligible_days = 0
    day_labels: list[str] = []
    for day in sorted(grouped):
        values = tuple(sorted(grouped[day], key=lambda item: str(item["closed_at"])))
        if len(values) == 96:
            eligible_days += 1
            day_labels.append(_iso(day))
            eligible.extend(values)
    if eligible_days < 14 or not eligible:
        return None
    population_digest = canonical_json_digest(
        {
            "selection_start": _iso(start),
            "selection_end": _iso(evaluation_day),
            "minimum_warmup_days": 14,
            "comparison": "reference <= current",
            "observations": eligible,
        }
    )
    return {
        "selection_start": _iso(start),
        "selection_end": _iso(evaluation_day),
        "eligible_completed_utc_days": tuple(day_labels),
        "reference_population_digest": population_digest,
        "reference_observation_count": len(eligible),
        "values": tuple(str(item["atr_pct_work"]) for item in eligible),
    }


def _atr_observation_provenance(candle: HistoricalCandle, update: Any) -> dict[str, Any]:
    payload = {
        "candle_id": _candle_id(candle),
        "opened_at": _iso(candle.open_time),
        "closed_at": _iso(candle.close_time),
        "atr_work": update.atr_work,
        "atr_pct_work": update.atr_pct_work,
        "atr_wire": update.atr_wire,
        "atr_pct_wire": update.atr_pct_wire,
        "true_range_work": update.true_range_work,
        "processed_candle_id": update.processed_candle_id,
    }
    return {**payload, "digest": canonical_json_digest(payload)}


def _observation(
    *,
    metric_ref: str,
    value: str,
    status: str,
    candles: Sequence[HistoricalCandle],
    reason_code: str | None,
    payload: Mapping[str, Any] | None,
) -> HistoricalMetricObservation:
    current = candles[-1]
    source_ids = tuple(_candle_id(candle) for candle in candles)
    basis = {
        "producer": RESEARCH_V1_HISTORICAL_TRIGGER_PRODUCER_VERSION,
        "metric_ref": metric_ref,
        "value": value,
        "status": status,
        "observed_at": _iso(current.close_time),
        "source_candle_ids": list(source_ids),
        "reason_code": reason_code,
        "payload": dict(payload or {}),
    }
    digest = canonical_json_digest(basis)
    return HistoricalMetricObservation(
        metric_ref=metric_ref,
        value=value,
        status=status,
        observed_at=_iso(current.close_time),
        available_at=_iso(current.close_time),
        source_candle_ids=source_ids,
        evidence_id=f"rv1-metric-{digest[:24]}",
        evidence_digest=digest,
        reason_code=reason_code,
        payload=payload,
    )


def _unavailable_observation(
    metric_ref: str,
    candles: Sequence[HistoricalCandle],
    *,
    reason_code: str,
) -> HistoricalMetricObservation:
    if not candles:
        raise ResearchV1HistoricalTriggerInputUnavailable(f"research_v1_historical_metric_unavailable:{metric_ref}")
    return _observation(
        metric_ref=metric_ref,
        value="UNAVAILABLE",
        status="UNAVAILABLE",
        candles=candles[-1:],
        reason_code=reason_code,
        payload={metric_ref: {"status": "UNAVAILABLE", "reason_code": reason_code}},
    )


def _metric_source_timeframe(metric_ref: str) -> str:
    if metric_ref in {"F-001 trigger_result", "F-002 trigger_result", "RETURN(asset,5m)", "DE", "ATR percentile"}:
        return "1m"
    raise ResearchV1HistoricalTriggerInputUnavailable(f"research_v1_historical_metric_unavailable:{metric_ref}")


def _metric_context_window(metric_ref: str) -> str:
    if metric_ref in {"F-001 trigger_result", "F-002 trigger_result"}:
        return "1m"
    if metric_ref == "RETURN(asset,5m)":
        return "5m"
    if metric_ref in {"DE", "ATR percentile"}:
        return "15m"
    if metric_ref == "SWING_SEQUENCE_STATE(asset,1h)":
        return "1h"
    return _metric_source_timeframe(metric_ref)


def _is_contiguous_one_minute_window(candles: Sequence[HistoricalCandle]) -> bool:
    return _is_contiguous_window(candles, timedelta(minutes=1))


def _is_contiguous_window(candles: Sequence[HistoricalCandle], duration: timedelta) -> bool:
    if not candles:
        return False
    previous_close: datetime | None = None
    for candle in candles:
        if candle.close_time - candle.open_time != duration:
            return False
        if previous_close is not None and candle.close_time - previous_close != duration:
            return False
        previous_close = candle.close_time
    return True


def _timeframe_delta(timeframe: str) -> timedelta:
    if timeframe == "15m":
        return timedelta(minutes=15)
    if timeframe == "1h":
        return timedelta(hours=1)
    raise ResearchV1HistoricalTriggerInputUnavailable(f"research_v1_historical_timeframe_bucket_unavailable:{timeframe}")


def _bucket_start(value: datetime, duration: timedelta) -> datetime:
    instant = value.astimezone(UTC)
    midnight = instant.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed_minutes = int((instant - midnight).total_seconds() // 60)
    duration_minutes = int(duration.total_seconds() // 60)
    bucket_minutes = (elapsed_minutes // duration_minutes) * duration_minutes
    return midnight + timedelta(minutes=bucket_minutes)


def _set_candle(candle: HistoricalCandle) -> Candle:
    return Candle(
        candle_id=_candle_id(candle),
        symbol=candle.symbol.upper(),
        timeframe=candle.timeframe,
        opened_at=_iso(candle.open_time),
        closed_at=_iso(candle.close_time),
        high=_decimal_text(candle.high),
        low=_decimal_text(candle.low),
        close=_decimal_text(candle.close),
        volume=_decimal_text(candle.volume),
        venue="BYBIT",
        product="USDT_LINEAR_PERPETUAL",
        source="HISTORICAL_KLINES",
        completed=candle.completed,
        source_final=candle.completed,
        coverage_complete=candle.completed,
    )


def _theta_move_pct(rule: RuleDefinition) -> str | None:
    params = rule.definition.get("params")
    if isinstance(params, Mapping) and params.get("theta_move_pct") is not None:
        return str(params["theta_move_pct"])
    if rule.parameter_snapshot and rule.parameter_snapshot.get("theta_move_pct") is not None:
        return str(rule.parameter_snapshot["theta_move_pct"])
    return None


def _metric_ref(rule: RuleDefinition) -> str:
    value = rule.definition.get("metric_ref")
    if value in {None, ""}:
        raise ResearchV1HistoricalTriggerInputUnavailable(f"research_v1_historical_trigger_input_unavailable:{rule.rule_id}")
    return str(value)


def _candle_id(candle: HistoricalCandle) -> str:
    constituent_ids = _AGGREGATED_CANDLE_CONSTITUENTS.get(id(candle))
    basis = {
        "symbol": candle.symbol.upper(),
        "category": candle.category,
        "timeframe": candle.timeframe,
        "open_time": _iso(candle.open_time),
        "close_time": _iso(candle.close_time),
        "open": _decimal_text(candle.open),
        "high": _decimal_text(candle.high),
        "low": _decimal_text(candle.low),
        "close": _decimal_text(candle.close),
        "volume": _decimal_text(candle.volume),
        "turnover": _decimal_text(candle.turnover),
    }
    if constituent_ids is not None:
        basis["aggregation_constituent_candle_ids"] = list(constituent_ids)
    return f"hist-candle-{canonical_json_digest(basis)[:24]}"


def _decimal_text(value: Decimal) -> str:
    return canonical_json_decimal_text(value)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def research_v1_trigger_metric_inventory(
    *,
    sets_package: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Return source-derived trigger requirement rows from the Set package."""

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for set_row in sets_package.get("sets", ()):
        if not isinstance(set_row, Mapping):
            continue
        for member in set_row.get("trigger_members", ()):
            if not isinstance(member, Mapping):
                continue
            key = (str(member.get("trigger_id")), str(member.get("trigger_version")))
            if key in seen:
                continue
            seen.add(key)
            metric_refs = tuple(str(item) for item in member.get("metric_references", ()))
            rows.append(
                {
                    "trigger_id": key[0],
                    "trigger_version": key[1],
                    "condition": str(member.get("condition") or ""),
                    "operator": str(member.get("operator") or ""),
                    "threshold": str(member.get("threshold") or ""),
                    "metric_references": metric_refs,
                    "formula_references": tuple(str(item) for item in member.get("formula_references", ())),
                    "readiness": tuple(metric_readiness(metric) for metric in metric_refs),
                }
            )
    return tuple(sorted(rows, key=lambda row: (row["trigger_id"], row["trigger_version"])))
