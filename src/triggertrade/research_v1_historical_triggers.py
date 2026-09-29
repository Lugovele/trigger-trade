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
from triggertrade.research_v1_execution import RESEARCH_V1_INSTRUMENT_SYMBOL_OVERRIDES
from triggertrade.instruments import FuturesInstrument
from triggertrade.set_engine import (
    Candle,
    IndicatorStatus,
    SwingPoint,
    SwingSequenceState,
    TriggerResult,
    directional_efficiency,
    evaluate_f001_price_displacement,
    evaluate_f002_participation,
    swing_points,
    swing_sequence_state,
    wilder_atr_seed,
    wilder_atr_update,
    zscore_working,
)
from triggertrade.set_engine.formulas import SetKernelError
from triggertrade.trigger_sets import RuleDefinition
from triggertrade.triggers import DeclarativeMetricPredicateTrigger, DeclarativeTriggerContext, Signal


RESEARCH_V1_HISTORICAL_TRIGGER_PRODUCER_VERSION = "research-v1-historical-trigger-producer-v1"

HISTORICAL_READY_METRICS = frozenset(
    {
        "F-001 trigger_result",
        "F-002 trigger_result",
        "AGGRESSIVE_VOLUME_DELTA_PCT",
        "ATR percentile",
        "BTC_CONTEXT_SCORE",
        "BTC_RETURN_Z",
        "DE",
        "RELATIVE_RETURN_Z",
        "RELATIVE_RETURN_15m",
        "RELATIVE_SCORE",
        "RETURN(asset,5m)",
        "SWING_SEQUENCE_STATE(asset,15m)",
        "SWING_SEQUENCE_STATE(asset,1h)",
        "TOD_REL_TURNOVER",
    }
)

KERNEL_EXISTS_BUT_ADAPTER_MISSING_METRICS = frozenset(
    {
    }
)

IMPLEMENTATION_MISSING_METRICS = frozenset(
    {
        "VNM_5m_z",
        "classifier_direction",
    }
)


class ResearchV1HistoricalTriggerError(ValueError):
    """Raised when factual historical trigger evaluation cannot proceed."""


class ResearchV1HistoricalTriggerInputUnavailable(ResearchV1HistoricalTriggerError):
    """Raised for unsupported or unavailable factual trigger inputs."""


@dataclass(frozen=True)
class AggregatedHistoricalCandle:
    candle: HistoricalCandle
    constituent_candle_ids: tuple[str, ...]
    aggregation_provenance_digest: str

    @property
    def symbol(self) -> str:
        return self.candle.symbol

    @property
    def category(self) -> str:
        return self.candle.category

    @property
    def timeframe(self) -> str:
        return self.candle.timeframe

    @property
    def open_time(self) -> datetime:
        return self.candle.open_time

    @property
    def close_time(self) -> datetime:
        return self.candle.close_time

    @property
    def open(self) -> Decimal:
        return self.candle.open

    @property
    def high(self) -> Decimal:
        return self.candle.high

    @property
    def low(self) -> Decimal:
        return self.candle.low

    @property
    def close(self) -> Decimal:
        return self.candle.close

    @property
    def volume(self) -> Decimal:
        return self.candle.volume

    @property
    def turnover(self) -> Decimal:
        return self.candle.turnover

    @property
    def completed(self) -> bool:
        return self.candle.completed


@dataclass(frozen=True)
class ResearchV1HistoricalInstrumentMetadata:
    logical_symbol: str
    instrument_symbol: str
    tick_size: str
    metadata_revision: str
    metadata_source: str
    metadata_as_of: str
    metadata_digest: str


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
    instrument_metadata: FuturesInstrument | None = None,
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None = None,
    companion_instrument_metadata: Mapping[str, FuturesInstrument] | None = None,
    raw_trades_pages: Sequence[Mapping[str, Any]] | None = None,
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
            instrument_metadata=instrument_metadata,
            companion_candles=companion_candles,
            companion_instrument_metadata=companion_instrument_metadata,
            raw_trades_pages=raw_trades_pages,
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
    instrument_metadata: FuturesInstrument | None = None,
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None = None,
    companion_instrument_metadata: Mapping[str, FuturesInstrument] | None = None,
    raw_trades_pages: Sequence[Mapping[str, Any]] | None = None,
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
    return _metric_observation(
        metric_ref=metric_ref,
        rule=rule,
        candles=ordered,
        symbol=symbol,
        instrument_metadata=instrument_metadata,
        companion_candles=companion_candles,
        companion_instrument_metadata=companion_instrument_metadata,
        raw_trades_pages=raw_trades_pages,
    )


def _metric_observation(
    *,
    metric_ref: str,
    rule: RuleDefinition,
    candles: Sequence[HistoricalCandle],
    symbol: str,
    instrument_metadata: FuturesInstrument | None,
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None,
    companion_instrument_metadata: Mapping[str, FuturesInstrument] | None,
    raw_trades_pages: Sequence[Mapping[str, Any]] | None,
) -> HistoricalMetricObservation:
    if metric_ref == "F-001 trigger_result":
        return _f001_observation(rule=rule, candles=candles)
    if metric_ref == "F-002 trigger_result":
        return _f002_observation(candles=candles)
    if metric_ref == "DE":
        return _de_observation(candles=candles)
    if metric_ref == "AGGRESSIVE_VOLUME_DELTA_PCT":
        return _aggressive_volume_delta_pct_observation(
            candles=candles,
            symbol=symbol,
            raw_trades_pages=raw_trades_pages,
        )
    if metric_ref == "ATR percentile":
        return _atr_percentile_observation(candles=candles)
    if metric_ref == "BTC_CONTEXT_SCORE":
        return _btc_context_score_observation(
            candles=candles,
            companion_candles=companion_candles,
            companion_instrument_metadata=companion_instrument_metadata,
        )
    if metric_ref == "BTC_RETURN_Z":
        return _btc_return_z_metric_observation(
            candles=candles,
            companion_candles=companion_candles,
        )
    if metric_ref == "RELATIVE_RETURN_15m":
        return _relative_return_15m_observation(
            candles=candles,
            symbol=symbol,
            companion_candles=companion_candles,
        )
    if metric_ref == "RELATIVE_RETURN_Z":
        return _relative_return_z_observation(
            candles=candles,
            symbol=symbol,
            companion_candles=companion_candles,
        )
    if metric_ref == "RELATIVE_SCORE":
        return _relative_score_observation(
            candles=candles,
            symbol=symbol,
            companion_candles=companion_candles,
        )
    if metric_ref == "RETURN(asset,5m)":
        return _return_5m_observation(candles=candles)
    if metric_ref == "TOD_REL_TURNOVER":
        return _tod_rel_turnover_observation(candles=candles)
    if metric_ref == "SWING_SEQUENCE_STATE(asset,1h)":
        return _swing_sequence_observation(
            candles=candles,
            symbol=symbol,
            instrument_metadata=instrument_metadata,
            metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
            timeframe="1h",
            unavailable_prefix="research_v1_historical_swing_sequence_unavailable",
        )
    if metric_ref == "SWING_SEQUENCE_STATE(asset,15m)":
        return _swing_sequence_observation(
            candles=candles,
            symbol=symbol,
            instrument_metadata=instrument_metadata,
            metric_ref="SWING_SEQUENCE_STATE(asset,15m)",
            timeframe="15m",
            unavailable_prefix="research_v1_historical_swing_sequence_15m_unavailable",
        )
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


def _aggressive_volume_delta_pct_observation(
    *,
    candles: Sequence[HistoricalCandle],
    symbol: str,
    raw_trades_pages: Sequence[Mapping[str, Any]] | None,
) -> HistoricalMetricObservation:
    current = candles[-1]
    interval_end = current.close_time
    interval_start = interval_end - timedelta(minutes=5)
    unavailable_payload_base = {
        "aggressive_volume_delta_pct": {
            "status": "UNAVAILABLE",
            "formula": "100 * (AggBuyNotional - AggSellNotional) / (AggBuyNotional + AggSellNotional)",
            "quantity_basis": "quote_notional",
            "interval_start": _iso(interval_start),
            "interval_end": _iso(interval_end),
            "logical_symbol": symbol.upper(),
            "instrument_symbol": _expected_instrument_symbol(symbol.upper()),
        }
    }
    if not raw_trades_pages:
        return _observation(
            metric_ref="AGGRESSIVE_VOLUME_DELTA_PCT",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(current,),
            reason_code="research_v1_historical_aggressive_volume_delta_unavailable:MISSING_RAW_TRADES",
            payload={
                "aggressive_volume_delta_pct": {
                    **unavailable_payload_base["aggressive_volume_delta_pct"],
                    "reason_code": "MISSING_RAW_TRADES",
                }
            },
        )
    parsed = _parse_aggressive_raw_trades_pages(
        raw_trades_pages,
        logical_symbol=symbol.upper(),
        interval_start=interval_start,
        interval_end=interval_end,
    )
    if parsed["status"] != "AVAILABLE":
        return _observation(
            metric_ref="AGGRESSIVE_VOLUME_DELTA_PCT",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(current,),
            reason_code=f"research_v1_historical_aggressive_volume_delta_unavailable:{parsed['reason_code']}",
            payload={
                "aggressive_volume_delta_pct": {
                    **unavailable_payload_base["aggressive_volume_delta_pct"],
                    "reason_code": parsed["reason_code"],
                    "page_provenance_digest": parsed.get("page_provenance_digest"),
                }
            },
        )
    trades = tuple(parsed["trades"])
    try:
        buy_notional = sum((Decimal(trade["notional_quote"]) for trade in trades if trade["taker_side"] == "BUY"), Decimal("0"))
        sell_notional = sum((Decimal(trade["notional_quote"]) for trade in trades if trade["taker_side"] == "SELL"), Decimal("0"))
        denominator = buy_notional + sell_notional
        if denominator == 0:
            raise NumericPolicyError("DENOMINATOR_ZERO")
        value_fraction = exact_divide(Fraction(100) * Fraction(buy_notional - sell_notional), Fraction(denominator))
        value = canonical_decimal_text(q36_working(value_fraction).value)
    except (ArithmeticError, NumericPolicyError, ValueError) as exc:
        reason = str(exc)
        return _observation(
            metric_ref="AGGRESSIVE_VOLUME_DELTA_PCT",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(current,),
            reason_code=f"research_v1_historical_aggressive_volume_delta_unavailable:{reason}",
            payload={
                "aggressive_volume_delta_pct": {
                    **unavailable_payload_base["aggressive_volume_delta_pct"],
                    "reason_code": reason,
                    "buy_notional": _decimal_text(buy_notional) if "buy_notional" in locals() else "0",
                    "sell_notional": _decimal_text(sell_notional) if "sell_notional" in locals() else "0",
                    "denominator": _decimal_text(denominator) if "denominator" in locals() else "0",
                    "trade_population_digest": parsed.get("trade_population_digest"),
                    "page_provenance_digest": parsed.get("page_provenance_digest"),
                }
            },
        )
    payload = {
        "status": "AVAILABLE",
        "formula": "100 * (AggBuyNotional - AggSellNotional) / (AggBuyNotional + AggSellNotional)",
        "quantity_basis": "quote_notional",
        "interval": "[from,to)",
        "interval_start": _iso(interval_start),
        "interval_end": _iso(interval_end),
        "logical_symbol": symbol.upper(),
        "instrument_symbol": parsed["instrument_symbol"],
        "buy_notional": _decimal_text(buy_notional),
        "sell_notional": _decimal_text(sell_notional),
        "denominator": _decimal_text(denominator),
        "trade_count": len(trades),
        "trade_population_digest": parsed["trade_population_digest"],
        "page_provenance_digest": parsed["page_provenance_digest"],
        "source_identity": parsed["source_identity"],
        "pages": parsed["pages"],
        "value": value,
    }
    payload = {**payload, "aggressive_volume_delta_digest": canonical_json_digest(payload)}
    return _observation(
        metric_ref="AGGRESSIVE_VOLUME_DELTA_PCT",
        value=value,
        status="AVAILABLE",
        candles=(current,),
        reason_code=None,
        payload={"aggressive_volume_delta_pct": payload},
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


def _relative_return_15m_observation(
    *,
    candles: Sequence[HistoricalCandle],
    symbol: str,
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None,
) -> HistoricalMetricObservation:
    asset_15m = _aggregate_completed_candles(candles, timeframe="15m")
    if len(asset_15m) < 2:
        return _unavailable_observation(
            "RELATIVE_RETURN_15m",
            candles,
            reason_code="research_v1_historical_relative_return_15m_unavailable:INCOMPLETE_ASSET_15M_INTERVAL",
        )
    asset_current = asset_15m[-1]
    asset_previous = asset_15m[-2]
    if asset_current.close_time - asset_previous.close_time != timedelta(minutes=15):
        return _observation(
            metric_ref="RELATIVE_RETURN_15m",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(asset_current,),
            reason_code="research_v1_historical_relative_return_15m_unavailable:ASSET_15M_GAP",
            payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": "ASSET_15M_GAP"}},
        )
    btc_source = _btc_companion_source(companion_candles)
    if btc_source is None:
        return _observation(
            metric_ref="RELATIVE_RETURN_15m",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(asset_current,),
            reason_code="research_v1_historical_relative_return_15m_unavailable:BTC_STREAM_UNAVAILABLE",
            payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": "BTC_STREAM_UNAVAILABLE"}},
        )
    try:
        btc_eligible = _eligible_candles(
            btc_source,
            symbol="BTCUSDT",
            observed_at=asset_current.close_time,
            timeframe="1m",
        )
    except ResearchV1HistoricalTriggerInputUnavailable as exc:
        return _observation(
            metric_ref="RELATIVE_RETURN_15m",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(asset_current,),
            reason_code=f"research_v1_historical_relative_return_15m_unavailable:{exc}",
            payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": str(exc)}},
        )
    if not btc_eligible:
        return _observation(
            metric_ref="RELATIVE_RETURN_15m",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(asset_current,),
            reason_code="research_v1_historical_relative_return_15m_unavailable:BTC_STREAM_UNAVAILABLE",
            payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": "BTC_STREAM_UNAVAILABLE"}},
        )
    btc_15m = _aggregate_completed_candles(btc_eligible, timeframe="15m")
    btc_by_close = {candle.close_time: candle for candle in btc_15m}
    btc_current = btc_by_close.get(asset_current.close_time)
    btc_previous = btc_by_close.get(asset_previous.close_time)
    if btc_current is None or btc_previous is None:
        return _observation(
            metric_ref="RELATIVE_RETURN_15m",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(asset_current,),
            reason_code="research_v1_historical_relative_return_15m_unavailable:BTC_15M_ENDPOINT_MISMATCH",
            payload={
                "relative_return_15m": {
                    "status": "UNAVAILABLE",
                    "reason_code": "BTC_15M_ENDPOINT_MISMATCH",
                    "asset_interval": _interval_payload(asset_previous, asset_current),
                }
            },
        )
    if btc_current.open_time != asset_current.open_time or btc_previous.open_time != asset_previous.open_time:
        return _observation(
            metric_ref="RELATIVE_RETURN_15m",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(asset_current,),
            reason_code="research_v1_historical_relative_return_15m_unavailable:BTC_15M_ENDPOINT_MISMATCH",
            payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": "BTC_15M_ENDPOINT_MISMATCH"}},
        )
    try:
        asset_return = _return_between(asset_previous, asset_current)
        btc_return = _return_between(btc_previous, btc_current)
        relative = q36_working(asset_return - btc_return).value
        value = canonical_decimal_text(relative)
    except (ArithmeticError, NumericPolicyError, ValueError) as exc:
        return _observation(
            metric_ref="RELATIVE_RETURN_15m",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(asset_current,),
            reason_code=f"research_v1_historical_relative_return_15m_unavailable:{exc}",
            payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": str(exc)}},
        )
    payload = {
        "status": "AVAILABLE",
        "formula": "RETURN(asset,15m) - RETURN(BTC,15m)",
        "input_timeframe": "15m",
        "benchmark_symbol": "BTCUSDT",
        "alignment": "exact completed 15m close endpoints",
        "asset_symbol": symbol.upper(),
        "asset_interval": _interval_payload(asset_previous, asset_current),
        "btc_interval": _interval_payload(btc_previous, btc_current),
        "asset_return_15m": canonical_decimal_text(asset_return),
        "btc_return_15m": canonical_decimal_text(btc_return),
        "value": value,
    }
    payload = {**payload, "cross_symbol_digest": canonical_json_digest(payload)}
    return _observation(
        metric_ref="RELATIVE_RETURN_15m",
        value=value,
        status="AVAILABLE",
        candles=(asset_previous, asset_current, btc_previous, btc_current),
        reason_code=None,
        payload={"relative_return_15m": payload},
    )


def _relative_return_15m_series(
    *,
    candles: Sequence[HistoricalCandle],
    symbol: str,
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None,
) -> tuple[dict[str, Any], ...] | HistoricalMetricObservation:
    asset_15m = _aggregate_completed_candles(candles, timeframe="15m")
    if len(asset_15m) < 2:
        return _unavailable_observation(
            "RELATIVE_RETURN_15m",
            candles,
            reason_code="research_v1_historical_relative_return_15m_unavailable:INCOMPLETE_ASSET_15M_INTERVAL",
        )
    if not _is_contiguous_window(asset_15m, timedelta(minutes=15)):
        return _observation(
            metric_ref="RELATIVE_RETURN_15m",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=asset_15m[-1:],
            reason_code="research_v1_historical_relative_return_15m_unavailable:ASSET_15M_GAP",
            payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": "ASSET_15M_GAP"}},
        )
    btc_source = _btc_companion_source(companion_candles)
    if btc_source is None:
        return _observation(
            metric_ref="RELATIVE_RETURN_15m",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=asset_15m[-1:],
            reason_code="research_v1_historical_relative_return_15m_unavailable:BTC_STREAM_UNAVAILABLE",
            payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": "BTC_STREAM_UNAVAILABLE"}},
        )
    try:
        btc_eligible = _eligible_candles(
            btc_source,
            symbol="BTCUSDT",
            observed_at=asset_15m[-1].close_time,
            timeframe="1m",
        )
    except ResearchV1HistoricalTriggerInputUnavailable as exc:
        return _observation(
            metric_ref="RELATIVE_RETURN_15m",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=asset_15m[-1:],
            reason_code=f"research_v1_historical_relative_return_15m_unavailable:{exc}",
            payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": str(exc)}},
        )
    btc_15m = _aggregate_completed_candles(btc_eligible, timeframe="15m")
    if len(btc_15m) < 2:
        return _observation(
            metric_ref="RELATIVE_RETURN_15m",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=asset_15m[-1:],
            reason_code="research_v1_historical_relative_return_15m_unavailable:BTC_STREAM_UNAVAILABLE",
            payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": "BTC_STREAM_UNAVAILABLE"}},
        )
    if not _is_contiguous_window(btc_15m, timedelta(minutes=15)):
        return _observation(
            metric_ref="RELATIVE_RETURN_15m",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=asset_15m[-1:],
            reason_code="research_v1_historical_relative_return_15m_unavailable:BTC_15M_GAP",
            payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": "BTC_15M_GAP"}},
        )
    btc_by_close = {candle.close_time: candle for candle in btc_15m}
    observations: list[dict[str, Any]] = []
    for asset_previous, asset_current in zip(asset_15m, asset_15m[1:]):
        btc_current = btc_by_close.get(asset_current.close_time)
        btc_previous = btc_by_close.get(asset_previous.close_time)
        if (
            btc_current is None
            or btc_previous is None
            or btc_current.open_time != asset_current.open_time
            or btc_previous.open_time != asset_previous.open_time
        ):
            return _observation(
                metric_ref="RELATIVE_RETURN_15m",
                value="UNAVAILABLE",
                status="UNAVAILABLE",
                candles=(asset_current,),
                reason_code="research_v1_historical_relative_return_15m_unavailable:BTC_15M_ENDPOINT_MISMATCH",
                payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": "BTC_15M_ENDPOINT_MISMATCH"}},
            )
        try:
            asset_return = _return_between(asset_previous, asset_current)
            btc_return = _return_between(btc_previous, btc_current)
            value = canonical_decimal_text(q36_working(asset_return - btc_return).value)
        except (ArithmeticError, NumericPolicyError, ValueError) as exc:
            return _observation(
                metric_ref="RELATIVE_RETURN_15m",
                value="UNAVAILABLE",
                status="UNAVAILABLE",
                candles=(asset_current,),
                reason_code=f"research_v1_historical_relative_return_15m_unavailable:{exc}",
                payload={"relative_return_15m": {"status": "UNAVAILABLE", "reason_code": str(exc)}},
            )
        payload = {
            "previous_candle_id": _candle_id(asset_previous),
            "current_candle_id": _candle_id(asset_current),
            "previous_close_time": _iso(asset_previous.close_time),
            "current_close_time": _iso(asset_current.close_time),
            "asset_symbol": symbol.upper(),
            "benchmark_symbol": "BTCUSDT",
            "asset_interval": _interval_payload(asset_previous, asset_current),
            "btc_interval": _interval_payload(btc_previous, btc_current),
            "relative_return_15m": value,
            "return_15m": value,
        }
        observations.append(
            {
                **payload,
                "return_15m": value,
                "digest": canonical_json_digest(payload),
                "current_candle": asset_current,
                "closed_at_dt": asset_current.close_time,
            }
        )
    return tuple(observations)


def _relative_return_z_observation(
    *,
    candles: Sequence[HistoricalCandle],
    symbol: str,
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None,
) -> HistoricalMetricObservation:
    relative_series = _relative_return_15m_series(
        candles=candles,
        symbol=symbol,
        companion_candles=companion_candles,
    )
    if isinstance(relative_series, HistoricalMetricObservation):
        return _relative_z_unavailable_from_dependency(relative_series, candles=candles)
    if not relative_series:
        return _unavailable_observation(
            "RELATIVE_RETURN_Z",
            candles,
            reason_code="research_v1_historical_relative_return_z_unavailable:RETURN_SERIES_UNAVAILABLE",
        )
    current = relative_series[-1]
    reference_population = _eligible_15m_return_reference_population(
        relative_series,
        evaluation_at=current["closed_at_dt"],
    )
    if reference_population is None:
        return _observation(
            metric_ref="RELATIVE_RETURN_Z",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(current["current_candle"],),
            reason_code="research_v1_historical_relative_return_z_unavailable:INSUFFICIENT_COMPLETED_UTC_DAYS",
            payload={"relative_return_z": {"status": "UNAVAILABLE", "minimum_warmup_days": 14}},
        )
    z = zscore_working(current=current["return_15m"], population=reference_population["values"])
    if z is None:
        return _observation(
            metric_ref="RELATIVE_RETURN_Z",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(current["current_candle"],),
            reason_code="research_v1_historical_relative_return_z_unavailable:ZERO_OR_UNAVAILABLE_SIGMA",
            payload={"relative_return_z": {"status": "UNAVAILABLE", "reason_code": "ZERO_OR_UNAVAILABLE_SIGMA"}},
        )
    value = canonical_decimal_text(z)
    return _observation(
        metric_ref="RELATIVE_RETURN_Z",
        value=value,
        status="AVAILABLE",
        candles=(current["current_candle"],),
        reason_code=None,
        payload={
            "relative_return_z": {
                "status": "AVAILABLE",
                "formula": "Q36((RELATIVE_RETURN_15m - mean(reference_relative_returns)) / population_stddev(reference_relative_returns))",
                "input_timeframe": "15m",
                "lookback": "30_completed_UTC_calendar_days",
                "minimum_warmup_days": 14,
                "ddof": 0,
                "zero_variance_behavior": "UNAVAILABLE",
                "current_relative_return_observation_digest": current["digest"],
                "reference_population_digest": reference_population["reference_population_digest"],
                "reference_observation_count": reference_population["reference_observation_count"],
                "eligible_completed_utc_days": reference_population["eligible_completed_utc_days"],
                "selection_start": reference_population["selection_start"],
                "selection_end": reference_population["selection_end"],
                "value": value,
            }
        },
    )


def _relative_score_observation(
    *,
    candles: Sequence[HistoricalCandle],
    symbol: str,
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None,
) -> HistoricalMetricObservation:
    return_z = _relative_return_z_observation(
        candles=candles,
        symbol=symbol,
        companion_candles=companion_candles,
    )
    if return_z.status != "AVAILABLE":
        return _observation(
            metric_ref="RELATIVE_SCORE",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=candles[-1:],
        observed_at_override=return_z.observed_at,
        available_at_override=return_z.available_at,
        source_candle_ids_override=return_z.source_candle_ids,
            reason_code="research_v1_historical_relative_score_unavailable:RELATIVE_RETURN_Z_UNAVAILABLE",
            payload={
                "relative_score": {
                    "status": "UNAVAILABLE",
                    "reason_code": "RELATIVE_RETURN_Z_UNAVAILABLE",
                    "relative_return_z": return_z.payload,
                    "relative_return_z_evidence_digest": return_z.evidence_digest,
                }
            },
        )
    try:
        score = q36_working(
            _clip_fraction(exact_divide(Fraction(Decimal(return_z.value)), 2), Fraction(-1), Fraction(1))
        ).value
        value = canonical_decimal_text(score)
    except (ArithmeticError, NumericPolicyError, ValueError) as exc:
        return _observation(
            metric_ref="RELATIVE_SCORE",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=candles[-1:],
        observed_at_override=return_z.observed_at,
        available_at_override=return_z.available_at,
        source_candle_ids_override=return_z.source_candle_ids,
            reason_code=f"research_v1_historical_relative_score_unavailable:{exc}",
            payload={"relative_score": {"status": "UNAVAILABLE", "reason_code": str(exc)}},
        )
    payload = {
        "status": "AVAILABLE",
        "formula": "Q36(clip(relative_return_z / 2.0, -1, +1))",
        "relative_return_z": return_z.value,
        "relative_return_z_evidence_digest": return_z.evidence_digest,
        "value": value,
    }
    payload = {**payload, "relative_score_digest": canonical_json_digest(payload)}
    return _observation(
        metric_ref="RELATIVE_SCORE",
        value=value,
        status="AVAILABLE",
        candles=candles[-1:],
        observed_at_override=return_z.observed_at,
        available_at_override=return_z.available_at,
        source_candle_ids_override=return_z.source_candle_ids,
        reason_code=None,
        payload={"relative_score": payload},
    )


def _relative_z_unavailable_from_dependency(
    dependency: HistoricalMetricObservation,
    *,
    candles: Sequence[HistoricalCandle],
) -> HistoricalMetricObservation:
    return _observation(
        metric_ref="RELATIVE_RETURN_Z",
        value="UNAVAILABLE",
        status="UNAVAILABLE",
        candles=candles[-1:],
        reason_code="research_v1_historical_relative_return_z_unavailable:RELATIVE_RETURN_15M_UNAVAILABLE",
        payload={
            "relative_return_z": {
                "status": "UNAVAILABLE",
                "reason_code": "RELATIVE_RETURN_15M_UNAVAILABLE",
                "relative_return_15m": dependency.payload,
                "relative_return_15m_evidence_digest": dependency.evidence_digest,
            }
        },
    )


def _btc_context_score_observation(
    *,
    candles: Sequence[HistoricalCandle],
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None,
    companion_instrument_metadata: Mapping[str, FuturesInstrument] | None,
) -> HistoricalMetricObservation:
    evaluation_at = candles[-1].close_time
    btc_source = _btc_companion_source(companion_candles)
    if btc_source is None:
        return _unavailable_observation(
            "BTC_CONTEXT_SCORE",
            candles,
            reason_code="research_v1_historical_btc_context_score_unavailable:BTC_STREAM_UNAVAILABLE",
        )
    btc_metadata = _btc_companion_metadata(companion_instrument_metadata)
    if btc_metadata is None:
        return _unavailable_observation(
            "BTC_CONTEXT_SCORE",
            candles,
            reason_code="research_v1_historical_btc_context_score_unavailable:INSTRUMENT_METADATA_UNAVAILABLE",
        )
    btc_eligible = _eligible_candles(
        btc_source,
        symbol="BTCUSDT",
        observed_at=evaluation_at,
        timeframe="1m",
    )
    if not btc_eligible:
        return _unavailable_observation(
            "BTC_CONTEXT_SCORE",
            candles,
            reason_code="research_v1_historical_btc_context_score_unavailable:BTC_STREAM_UNAVAILABLE",
        )
    return_z = _btc_return_z_observation(btc_candles=btc_eligible, evaluation_at=evaluation_at)
    if return_z.status != "AVAILABLE":
        return _observation(
            metric_ref="BTC_CONTEXT_SCORE",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=btc_eligible[-1:],
            reason_code="research_v1_historical_btc_context_score_unavailable:BTC_RETURN_Z_UNAVAILABLE",
            payload={
                "btc_context_score": {
                    "status": "UNAVAILABLE",
                    "reason_code": "BTC_RETURN_Z_UNAVAILABLE",
                    "btc_return_z": return_z.payload,
                    "btc_return_z_evidence_digest": return_z.evidence_digest,
                }
            },
        )
    structure = _swing_sequence_observation(
        candles=btc_eligible,
        symbol="BTCUSDT",
        instrument_metadata=btc_metadata,
        metric_ref="SWING_SEQUENCE_STATE(asset,1h)",
        timeframe="1h",
        unavailable_prefix="research_v1_historical_swing_sequence_unavailable",
    )
    if structure.status != "AVAILABLE":
        return _observation(
            metric_ref="BTC_CONTEXT_SCORE",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=btc_eligible[-1:],
            reason_code="research_v1_historical_btc_context_score_unavailable:BTC_STRUCTURE_UNAVAILABLE",
            payload={
                "btc_context_score": {
                    "status": "UNAVAILABLE",
                    "reason_code": "BTC_STRUCTURE_UNAVAILABLE",
                    "btc_structure": structure.payload,
                    "btc_structure_evidence_digest": structure.evidence_digest,
                }
            },
        )
    try:
        structure_score = _structure_score(structure.value)
        momentum_score = _clip_fraction(exact_divide(Fraction(Decimal(return_z.value)), 2), Fraction(-1), Fraction(1))
        context_score = q36_working(
            Fraction(3, 5) * structure_score + Fraction(2, 5) * momentum_score
        ).value
        value = canonical_decimal_text(context_score)
    except (ArithmeticError, NumericPolicyError, ValueError) as exc:
        return _observation(
            metric_ref="BTC_CONTEXT_SCORE",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=btc_eligible[-1:],
            reason_code=f"research_v1_historical_btc_context_score_unavailable:{exc}",
            payload={"btc_context_score": {"status": "UNAVAILABLE", "reason_code": str(exc)}},
        )
    payload = {
        "status": "AVAILABLE",
        "formula": "Q36(0.60 * BTC_STRUCTURE_SCORE + 0.40 * BTC_MOMENTUM_SCORE)",
        "btc_structure_state": structure.value,
        "btc_structure_score": canonical_decimal_text(structure_score),
        "btc_momentum_score": canonical_decimal_text(q36_working(momentum_score).value),
        "btc_return_z": return_z.value,
        "btc_structure_evidence_digest": structure.evidence_digest,
        "btc_return_z_evidence_digest": return_z.evidence_digest,
        "structure_weight": "0.60",
        "momentum_weight": "0.40",
        "value": value,
    }
    payload = {**payload, "btc_context_digest": canonical_json_digest(payload)}
    return _observation(
        metric_ref="BTC_CONTEXT_SCORE",
        value=value,
        status="AVAILABLE",
        candles=btc_eligible[-1:],
        reason_code=None,
        payload={"btc_context_score": payload},
    )


def _tod_rel_turnover_observation(*, candles: Sequence[HistoricalCandle]) -> HistoricalMetricObservation:
    five_minute = _aggregate_completed_candles(candles, timeframe="5m")
    if not five_minute:
        return _unavailable_observation(
            "TOD_REL_TURNOVER",
            candles,
            reason_code="research_v1_historical_tod_rel_turnover_unavailable:INCOMPLETE_5M_BUCKET",
        )
    current = five_minute[-1]
    reference = _eligible_same_clock_turnover_population(five_minute, current=current)
    if reference is None:
        return _observation(
            metric_ref="TOD_REL_TURNOVER",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(current,),
            reason_code="research_v1_historical_tod_rel_turnover_unavailable:INSUFFICIENT_SAME_CLOCK_HISTORY",
            payload={
                "tod_rel_turnover": {
                    "status": "UNAVAILABLE",
                    "input_timeframe": "5m",
                    "lookback_days": 30,
                    "minimum_warmup_days": 14,
                    "reason_code": "INSUFFICIENT_SAME_CLOCK_HISTORY",
                }
            },
        )
    try:
        current_turnover = Fraction(current.turnover)
        median_turnover = reference["median_turnover"]
        if median_turnover <= 0:
            raise NumericPolicyError("same-clock median turnover must be positive")
        value = canonical_decimal_text(q36_working(exact_divide(current_turnover, median_turnover)).value)
    except (ArithmeticError, NumericPolicyError, ValueError) as exc:
        return _observation(
            metric_ref="TOD_REL_TURNOVER",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(current,),
            reason_code=f"research_v1_historical_tod_rel_turnover_unavailable:{exc}",
            payload={"tod_rel_turnover": {"status": "UNAVAILABLE", "reason_code": str(exc)}},
        )
    return _observation(
        metric_ref="TOD_REL_TURNOVER",
        value=value,
        status="AVAILABLE",
        candles=(current,),
        reason_code=None,
        payload={
            "tod_rel_turnover": {
                "status": "AVAILABLE",
                "input_timeframe": "5m",
                "timezone": "UTC",
                "lookback_days": 30,
                "minimum_warmup_days": 14,
                "baseline_statistic": "median",
                "same_clock_bucket": True,
                "turnover_basis": "quote_notional_turnover",
                "current_bucket_candle_id": _candle_id(current),
                "current_bucket_start": _iso(current.open_time),
                "current_bucket_end": _iso(current.close_time),
                "reference_count": len(reference["observations"]),
                "reference_population_digest": reference["population_digest"],
                "reference_observations": reference["observations"],
                "median_prior_same_clock_turnover": canonical_decimal_text(median_turnover),
                "value": value,
            }
        },
    )


def _swing_sequence_observation(
    *,
    candles: Sequence[HistoricalCandle],
    symbol: str,
    instrument_metadata: FuturesInstrument | None,
    metric_ref: str,
    timeframe: str,
    unavailable_prefix: str,
) -> HistoricalMetricObservation:
    metadata, metadata_error = _coerce_instrument_metadata(symbol=symbol, instrument_metadata=instrument_metadata)
    if metadata_error is not None:
        return _unavailable_observation(
            metric_ref,
            candles,
            reason_code=f"{unavailable_prefix}:{metadata_error}",
        )
    assert metadata is not None
    if Decimal(metadata.tick_size) <= 0:
        return _unavailable_observation(
            metric_ref,
            candles,
            reason_code=f"{unavailable_prefix}:INVALID_TICK_SIZE",
        )
    aggregated = _aggregate_completed_candles(candles, timeframe=timeframe)
    duration = _timeframe_delta(timeframe)
    if len(aggregated) < 7:
        return _unavailable_observation(
            metric_ref,
            candles,
            reason_code=f"{unavailable_prefix}:INSUFFICIENT_{timeframe.upper()}_HISTORY",
        )
    if not _is_contiguous_window(aggregated, duration):
        return _unavailable_observation(
            metric_ref,
            candles,
            reason_code=f"{unavailable_prefix}:NON_CONTINUOUS_{timeframe.upper()}_WINDOW",
        )
    try:
        kernel_candles = tuple(_set_candle(candle) for candle in aggregated)
        highs = swing_points(kernel_candles, point_type="HIGH")
        lows = swing_points(kernel_candles, point_type="LOW")
        state = swing_sequence_state(highs=highs, lows=lows, tick_size=metadata.tick_size)
        if state is SwingSequenceState.UNAVAILABLE:
            return _observation(
                metric_ref=metric_ref,
                value=SwingSequenceState.UNAVAILABLE.value,
                status="UNAVAILABLE",
                candles=aggregated[-1:],
                reason_code=f"{unavailable_prefix}:INSUFFICIENT_CONFIRMED_SWING_POINTS",
                payload={
                    "swing_sequence_state": {
                        "status": "UNAVAILABLE",
                        "reason_code": "INSUFFICIENT_CONFIRMED_SWING_POINTS",
                        "input_timeframe": timeframe,
                        "pivot_window": "2_LEFT_2_RIGHT",
                        "confirmation_delay": f"2_COMPLETED_{timeframe.upper()}_CANDLES",
                        "high_count": len(highs),
                        "low_count": len(lows),
                        "instrument_metadata": _instrument_metadata_payload(metadata),
                    }
                },
            )
        payload = _swing_sequence_payload(
            state=state,
            highs=highs,
            lows=lows,
            candles=aggregated,
            timeframe=timeframe,
            metadata=metadata,
        )
        return _observation(
            metric_ref=metric_ref,
            value=state.value,
            status="AVAILABLE",
            candles=aggregated,
            reason_code=None,
            payload={"swing_sequence_state": payload},
        )
    except (SetKernelError, NumericPolicyError, ArithmeticError, ValueError) as exc:
        return _observation(
            metric_ref=metric_ref,
            value=SwingSequenceState.UNAVAILABLE.value,
            status="UNAVAILABLE",
            candles=aggregated[-1:],
            reason_code=f"{unavailable_prefix}:{exc}",
            payload={"swing_sequence_state": {"status": "UNAVAILABLE", "reason_code": str(exc)}},
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


def _aggregate_completed_candles(candles: Sequence[HistoricalCandle], *, timeframe: str) -> tuple[AggregatedHistoricalCandle, ...]:
    source = tuple(candles)
    if not source:
        return ()
    duration = _timeframe_delta(timeframe)
    per_bucket = int(duration / timedelta(minutes=1))
    buckets: dict[datetime, list[HistoricalCandle]] = {}
    for candle in source:
        start = _bucket_start(candle.open_time, duration)
        buckets.setdefault(start, []).append(candle)
    aggregated: list[AggregatedHistoricalCandle] = []
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
        constituent_candle_ids = tuple(_candle_id(item) for item in bucket)
        aggregation_digest = canonical_json_digest(
            {
                "timeframe": timeframe,
                "aggregated_candle_id": _raw_candle_id(aggregated_candle),
                "constituent_candle_ids": constituent_candle_ids,
            }
        )
        aggregated.append(
            AggregatedHistoricalCandle(
                candle=aggregated_candle,
                constituent_candle_ids=constituent_candle_ids,
                aggregation_provenance_digest=aggregation_digest,
            )
        )
    return tuple(aggregated)


def _atr_pct_series(candles: Sequence[AggregatedHistoricalCandle]) -> tuple[tuple[AggregatedHistoricalCandle, Any], ...]:
    ordered = tuple(candles)
    if len(ordered) < 15:
        return ()
    seed_candles = tuple(_set_candle(candle) for candle in ordered[1:15])
    seed = wilder_atr_seed(seed_candles=seed_candles, predecessor_close=_decimal_text(ordered[0].close))
    if seed.status is not IndicatorStatus.AVAILABLE or seed.atr_work is None:
        return ()
    series: list[tuple[AggregatedHistoricalCandle, Any]] = [(ordered[14], seed)]
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
    series: Sequence[tuple[AggregatedHistoricalCandle, Any]],
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


def _eligible_same_clock_turnover_population(
    candles: Sequence[AggregatedHistoricalCandle],
    *,
    current: AggregatedHistoricalCandle,
) -> dict[str, Any] | None:
    by_open = {candle.open_time.astimezone(UTC): candle for candle in candles}
    earliest_open = candles[0].open_time.astimezone(UTC)
    observations: list[dict[str, Any]] = []
    turnovers: list[Fraction] = []
    for offset in range(1, 31):
        expected_open = current.open_time.astimezone(UTC) - timedelta(days=offset)
        expected_close = current.close_time.astimezone(UTC) - timedelta(days=offset)
        if expected_open < earliest_open:
            continue
        candle = by_open.get(expected_open)
        if candle is None or candle.close_time.astimezone(UTC) != expected_close:
            return None
        payload = {
            "candle_id": _candle_id(candle),
            "bucket_start": _iso(candle.open_time),
            "bucket_end": _iso(candle.close_time),
            "turnover": _decimal_text(candle.turnover),
        }
        observations.append({**payload, "digest": canonical_json_digest(payload)})
        turnovers.append(Fraction(candle.turnover))
    if len(observations) < 14:
        return None
    median = _median_fraction(turnovers)
    population_digest = canonical_json_digest(
        {
            "selection_rule": "same UTC clock 5m bucket on the thirty prior UTC dates",
            "current_bucket_start": _iso(current.open_time),
            "current_bucket_end": _iso(current.close_time),
            "minimum_warmup_days": 14,
            "baseline_statistic": "median",
            "observations": tuple(reversed(observations)),
        }
    )
    return {
        "observations": tuple(reversed(observations)),
        "population_digest": population_digest,
        "median_turnover": median,
    }


def _btc_companion_source(
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None,
) -> Sequence[HistoricalCandle] | None:
    if companion_candles is None:
        return None
    for key, values in companion_candles.items():
        if str(key).upper() == "BTCUSDT":
            return values
    return None


def _btc_companion_metadata(
    companion_instrument_metadata: Mapping[str, FuturesInstrument] | None,
) -> FuturesInstrument | None:
    if companion_instrument_metadata is None:
        return None
    for key, value in companion_instrument_metadata.items():
        if str(key).upper() == "BTCUSDT":
            return value
    return None


def _btc_return_z_observation(
    *,
    btc_candles: Sequence[HistoricalCandle],
    evaluation_at: datetime,
) -> HistoricalMetricObservation:
    source = tuple(candle for candle in btc_candles if candle.close_time <= evaluation_at)
    if not source:
        return _unavailable_observation(
            "BTC_RETURN_Z",
            btc_candles,
            reason_code="research_v1_historical_btc_return_z_unavailable:BTC_STREAM_UNAVAILABLE",
        )
    fifteen_minute = _aggregate_completed_candles(source, timeframe="15m")
    if len(fifteen_minute) < 2:
        return _unavailable_observation(
            "BTC_RETURN_Z",
            btc_candles,
            reason_code="research_v1_historical_btc_return_z_unavailable:INSUFFICIENT_15M_HISTORY",
        )
    if not _is_contiguous_window(fifteen_minute, timedelta(minutes=15)):
        return _observation(
            metric_ref="BTC_RETURN_Z",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=fifteen_minute[-1:],
            reason_code="research_v1_historical_btc_return_z_unavailable:NON_CONTINUOUS_15M_RETURN_CHAIN",
            payload={"btc_return_z": {"status": "UNAVAILABLE", "reason_code": "NON_CONTINUOUS_15M_RETURN_CHAIN"}},
        )
    returns = _return_15m_series(fifteen_minute)
    if not returns:
        return _observation(
            metric_ref="BTC_RETURN_Z",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=fifteen_minute[-1:],
            reason_code="research_v1_historical_btc_return_z_unavailable:RETURN_SERIES_UNAVAILABLE",
            payload={"btc_return_z": {"status": "UNAVAILABLE", "reason_code": "RETURN_SERIES_UNAVAILABLE"}},
        )
    current = returns[-1]
    reference_population = _eligible_15m_return_reference_population(returns, evaluation_at=current["closed_at_dt"])
    if reference_population is None:
        return _observation(
            metric_ref="BTC_RETURN_Z",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(current["current_candle"],),
            reason_code="research_v1_historical_btc_return_z_unavailable:INSUFFICIENT_COMPLETED_UTC_DAYS",
            payload={"btc_return_z": {"status": "UNAVAILABLE", "minimum_warmup_days": 14}},
        )
    z = zscore_working(current=current["return_15m"], population=reference_population["values"])
    if z is None:
        return _observation(
            metric_ref="BTC_RETURN_Z",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=(current["current_candle"],),
            reason_code="research_v1_historical_btc_return_z_unavailable:ZERO_OR_UNAVAILABLE_SIGMA",
            payload={"btc_return_z": {"status": "UNAVAILABLE", "reason_code": "ZERO_OR_UNAVAILABLE_SIGMA"}},
        )
    value = canonical_decimal_text(z)
    return _observation(
        metric_ref="BTC_RETURN_Z",
        value=value,
        status="AVAILABLE",
        candles=(current["current_candle"],),
        reason_code=None,
        payload={
            "btc_return_z": {
                "status": "AVAILABLE",
                "formula": "Q36((RETURN(BTC,15m) - mean(reference_returns)) / population_stddev(reference_returns))",
                "input_timeframe": "15m",
                "benchmark_symbol": "BTCUSDT",
                "lookback": "30_completed_UTC_calendar_days",
                "minimum_warmup_days": 14,
                "ddof": 0,
                "zero_variance_behavior": "UNAVAILABLE",
                "current_return_observation_digest": current["digest"],
                    "reference_population_digest": reference_population["reference_population_digest"],
                "reference_observation_count": reference_population["reference_observation_count"],
                "eligible_completed_utc_days": reference_population["eligible_completed_utc_days"],
                "selection_start": reference_population["selection_start"],
                "selection_end": reference_population["selection_end"],
                "value": value,
            }
        },
    )


def _btc_return_z_metric_observation(
    *,
    candles: Sequence[HistoricalCandle],
    companion_candles: Mapping[str, Sequence[HistoricalCandle]] | None,
) -> HistoricalMetricObservation:
    evaluation_at = candles[-1].close_time
    btc_source = _btc_companion_source(companion_candles)
    if btc_source is None and candles[-1].symbol.upper() == "BTCUSDT":
        btc_source = candles
    if btc_source is None:
        return _unavailable_observation(
            "BTC_RETURN_Z",
            candles,
            reason_code="research_v1_historical_btc_return_z_unavailable:BTC_STREAM_UNAVAILABLE",
        )
    try:
        btc_eligible = _eligible_candles(
            btc_source,
            symbol="BTCUSDT",
            observed_at=evaluation_at,
            timeframe="1m",
        )
    except ResearchV1HistoricalTriggerInputUnavailable as exc:
        return _observation(
            metric_ref="BTC_RETURN_Z",
            value="UNAVAILABLE",
            status="UNAVAILABLE",
            candles=candles[-1:],
            reason_code=f"research_v1_historical_btc_return_z_unavailable:{exc}",
            payload={"btc_return_z": {"status": "UNAVAILABLE", "reason_code": str(exc)}},
        )
    if not btc_eligible:
        return _unavailable_observation(
            "BTC_RETURN_Z",
            candles,
            reason_code="research_v1_historical_btc_return_z_unavailable:BTC_STREAM_UNAVAILABLE",
        )
    return _btc_return_z_observation(btc_candles=btc_eligible, evaluation_at=evaluation_at)


def _return_15m_series(candles: Sequence[AggregatedHistoricalCandle]) -> tuple[dict[str, Any], ...]:
    observations: list[dict[str, Any]] = []
    for previous, current in zip(candles, candles[1:]):
        if current.close_time - previous.close_time != timedelta(minutes=15):
            return ()
        try:
            value = canonical_decimal_text(_return_between(previous, current))
        except (ArithmeticError, NumericPolicyError, ValueError):
            return ()
        payload = {
            "previous_candle_id": _candle_id(previous),
            "current_candle_id": _candle_id(current),
            "previous_close_time": _iso(previous.close_time),
            "current_close_time": _iso(current.close_time),
            "return_15m": value,
        }
        observations.append(
            {
                **payload,
                "digest": canonical_json_digest(payload),
                "current_candle": current,
                "closed_at_dt": current.close_time,
            }
        )
    return tuple(observations)


def _eligible_15m_return_reference_population(
    series: Sequence[dict[str, Any]],
    *,
    evaluation_at: datetime,
) -> dict[str, Any] | None:
    evaluation_day = evaluation_at.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start = evaluation_day - timedelta(days=30)
    grouped: dict[datetime, list[dict[str, Any]]] = {}
    for item in series:
        candle = item["current_candle"]
        opened = candle.open_time.astimezone(UTC)
        closed = candle.close_time.astimezone(UTC)
        if opened < start or closed > evaluation_day:
            continue
        day = opened.replace(hour=0, minute=0, second=0, microsecond=0)
        grouped.setdefault(day, []).append(item)
    complete_days: list[datetime] = []
    observations: list[dict[str, Any]] = []
    for day in sorted(grouped):
        values = tuple(sorted(grouped[day], key=lambda item: str(item["current_close_time"])))
        if len(values) != 96:
            continue
        complete_days.append(day)
        observations.extend(_return_15m_public_observation(value) for value in values)
    for previous, current in zip(complete_days, complete_days[1:]):
        if current - previous != timedelta(days=1):
            return None
    if len(complete_days) < 14 or not observations:
        return None
    population_digest = canonical_json_digest(
        {
            "selection_start": _iso(start),
            "selection_end": _iso(evaluation_day),
            "minimum_warmup_days": 14,
            "ddof": 0,
            "observations": observations,
        }
    )
    return {
        "selection_start": _iso(start),
        "selection_end": _iso(evaluation_day),
        "eligible_completed_utc_days": tuple(_iso(day) for day in complete_days),
        "reference_population_digest": population_digest,
        "reference_observation_count": len(observations),
        "values": tuple(str(item["return_15m"]) for item in observations),
    }


def _return_15m_public_observation(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "previous_candle_id": str(item["previous_candle_id"]),
        "current_candle_id": str(item["current_candle_id"]),
        "previous_close_time": str(item["previous_close_time"]),
        "current_close_time": str(item["current_close_time"]),
        "return_15m": str(item["return_15m"]),
        "digest": str(item["digest"]),
    }


def _return_between(previous: AggregatedHistoricalCandle, current: AggregatedHistoricalCandle) -> Fraction:
    previous_close = Fraction(previous.close)
    current_close = Fraction(current.close)
    if previous_close <= 0:
        raise NumericPolicyError("previous close must be positive")
    return q36_working(exact_divide(current_close - previous_close, previous_close)).value


def _interval_payload(previous: AggregatedHistoricalCandle, current: AggregatedHistoricalCandle) -> dict[str, Any]:
    return {
        "previous_candle_id": _candle_id(previous),
        "current_candle_id": _candle_id(current),
        "previous_close_time": _iso(previous.close_time),
        "current_close_time": _iso(current.close_time),
        "interval_start": _iso(current.open_time),
        "interval_end": _iso(current.close_time),
        "source_candle_ids": (_candle_id(previous), _candle_id(current)),
    }


def _structure_score(state: str) -> Fraction:
    if state == SwingSequenceState.BULLISH.value:
        return Fraction(1)
    if state == SwingSequenceState.AMBIGUOUS.value:
        return Fraction(0)
    if state == SwingSequenceState.BEARISH.value:
        return Fraction(-1)
    raise NumericPolicyError(f"unavailable BTC structure state: {state}")


def _clip_fraction(value: Fraction, lower: Fraction, upper: Fraction) -> Fraction:
    return max(lower, min(upper, value))


def _median_fraction(values: Sequence[Fraction]) -> Fraction:
    ordered = tuple(sorted(values))
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return exact_divide(ordered[midpoint - 1] + ordered[midpoint], 2)


def _atr_observation_provenance(candle: AggregatedHistoricalCandle, update: Any) -> dict[str, Any]:
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


def _swing_sequence_payload(
    *,
    state: SwingSequenceState,
    highs: Sequence[SwingPoint],
    lows: Sequence[SwingPoint],
    candles: Sequence[AggregatedHistoricalCandle],
    timeframe: str,
    metadata: ResearchV1HistoricalInstrumentMetadata,
) -> dict[str, Any]:
    selected_highs = tuple(highs[-2:])
    selected_lows = tuple(lows[-2:])
    high_payloads = tuple(_swing_point_payload(point) for point in selected_highs)
    low_payloads = tuple(_swing_point_payload(point) for point in selected_lows)
    equality_basis = {
        "tick_size": metadata.tick_size,
        "highs": high_payloads,
        "lows": low_payloads,
        "state": state.value,
        "semantics": "BULLISH if h2 > h1 + tick and l2 > l1 + tick; BEARISH if h2 < h1 - tick and l2 < l1 - tick; else AMBIGUOUS",
    }
    source_candle_ids = tuple(_candle_id(candle) for candle in candles)
    payload = {
        "status": "AVAILABLE",
        "input_timeframe": timeframe,
        "pivot_window": "2_LEFT_2_RIGHT",
        "confirmation_delay": f"2_COMPLETED_{timeframe.upper()}_CANDLES",
        "availability": f"candidate swing is available at the second completed {timeframe} candle after the pivot candle",
        "state": state.value,
        "tick_equality": {
            "tolerance": "1_tick",
            "instrument_symbol": metadata.instrument_symbol,
            "tick_size": metadata.tick_size,
            "metadata_revision": metadata.metadata_revision,
            "metadata_digest": metadata.metadata_digest,
            "decision_digest": canonical_json_digest(equality_basis),
        },
        "selected_confirmed_highs": high_payloads,
        "selected_confirmed_lows": low_payloads,
        "all_confirmed_high_count": len(tuple(highs)),
        "all_confirmed_low_count": len(tuple(lows)),
        f"source_{timeframe}_candle_ids": source_candle_ids,
        f"source_{timeframe}_population_digest": canonical_json_digest(
            {
                "timeframe": timeframe,
                f"source_{timeframe}_candle_ids": source_candle_ids,
                "aggregation_provenance": tuple(
                    {
                        "candle_id": _candle_id(candle),
                        "aggregation_provenance_digest": candle.aggregation_provenance_digest,
                        "constituent_candle_ids": candle.constituent_candle_ids,
                    }
                    for candle in candles
                ),
            }
        ),
        "instrument_metadata": _instrument_metadata_payload(metadata),
    }
    return {**payload, "digest": canonical_json_digest(payload)}


def _swing_point_payload(point: SwingPoint) -> dict[str, str]:
    payload = {
        "point_type": point.point_type,
        "candle_id": point.candle_id,
        "price": point.price,
        "confirmed_at": point.confirmed_at,
    }
    return {**payload, "digest": canonical_json_digest(payload)}


def _coerce_instrument_metadata(
    *,
    symbol: str,
    instrument_metadata: FuturesInstrument | None,
) -> tuple[ResearchV1HistoricalInstrumentMetadata | None, str | None]:
    if instrument_metadata is None:
        return None, "INSTRUMENT_METADATA_UNAVAILABLE"
    if not isinstance(instrument_metadata, FuturesInstrument):
        return None, "INSTRUMENT_METADATA_UNAVAILABLE"
    logical_symbol = symbol.upper()
    expected_instrument_symbol = _expected_instrument_symbol(logical_symbol)
    instrument_symbol = instrument_metadata.symbol.upper()
    if instrument_symbol != expected_instrument_symbol:
        return None, "INSTRUMENT_BINDING_MISMATCH"
    if instrument_metadata.quote_coin.upper() != "USDT" or instrument_metadata.settle_coin.upper() != "USDT":
        return None, "UNSUPPORTED_INSTRUMENT_CONTRACT"
    if instrument_metadata.contract_type != "LinearPerpetual":
        return None, "UNSUPPORTED_INSTRUMENT_CONTRACT"
    if instrument_metadata.status != "Trading" or not instrument_metadata.is_tradeable:
        return None, "UNSUPPORTED_INSTRUMENT_CONTRACT"
    metadata_revision = instrument_metadata.catalog_hash or ""
    if not metadata_revision:
        return None, "METADATA_REVISION_UNAVAILABLE"
    metadata_source = instrument_metadata.source or ""
    if not metadata_source:
        return None, "METADATA_SOURCE_UNAVAILABLE"
    metadata_as_of = instrument_metadata.updated_at or ""
    if not metadata_as_of:
        return None, "METADATA_AS_OF_UNAVAILABLE"
    try:
        tick = Decimal(str(instrument_metadata.tick_size))
    except Exception:
        return None, "INVALID_TICK_SIZE"
    if tick <= 0:
        return None, "INVALID_TICK_SIZE"
    metadata_payload = {
        "logical_symbol": logical_symbol,
        "instrument_symbol": instrument_symbol,
        "tick_size": _decimal_text(tick),
        "metadata_revision": metadata_revision,
        "metadata_source": metadata_source,
        "metadata_as_of": metadata_as_of,
    }
    return ResearchV1HistoricalInstrumentMetadata(
        logical_symbol=logical_symbol,
        instrument_symbol=instrument_symbol,
        tick_size=_decimal_text(tick),
        metadata_revision=metadata_revision,
        metadata_source=metadata_source,
        metadata_as_of=metadata_as_of,
        metadata_digest=canonical_json_digest(metadata_payload),
    ), None


def _expected_instrument_symbol(logical_symbol: str) -> str:
    asset = logical_symbol.removesuffix("USDT")
    return str(RESEARCH_V1_INSTRUMENT_SYMBOL_OVERRIDES.get(asset, logical_symbol)).upper()


def _instrument_metadata_payload(metadata: ResearchV1HistoricalInstrumentMetadata) -> dict[str, str]:
    return {
        "logical_symbol": metadata.logical_symbol,
        "instrument_symbol": metadata.instrument_symbol,
        "tick_size": metadata.tick_size,
        "metadata_revision": metadata.metadata_revision,
        "metadata_source": metadata.metadata_source,
        "metadata_as_of": metadata.metadata_as_of,
        "metadata_digest": metadata.metadata_digest,
    }


def _observation(
    *,
    metric_ref: str,
    value: str,
    status: str,
    candles: Sequence[HistoricalCandle | AggregatedHistoricalCandle],
    reason_code: str | None,
    payload: Mapping[str, Any] | None,
    observed_at_override: str | None = None,
    available_at_override: str | None = None,
    source_candle_ids_override: Sequence[str] | None = None,
) -> HistoricalMetricObservation:
    current = candles[-1]
    source_ids = (
        tuple(source_candle_ids_override)
        if source_candle_ids_override is not None
        else tuple(_candle_id(candle) for candle in candles)
    )
    observed_at = observed_at_override or _iso(current.close_time)
    available_at = available_at_override or observed_at
    basis = {
        "producer": RESEARCH_V1_HISTORICAL_TRIGGER_PRODUCER_VERSION,
        "metric_ref": metric_ref,
        "value": value,
        "status": status,
        "observed_at": observed_at,
        "source_candle_ids": list(source_ids),
        "reason_code": reason_code,
        "payload": dict(payload or {}),
    }
    if available_at_override is not None:
        basis["available_at"] = available_at
    digest = canonical_json_digest(basis)
    return HistoricalMetricObservation(
        metric_ref=metric_ref,
        value=value,
        status=status,
        observed_at=observed_at,
        available_at=available_at,
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


def _parse_aggressive_raw_trades_pages(
    raw_trades_pages: Sequence[Mapping[str, Any]],
    *,
    logical_symbol: str,
    interval_start: datetime,
    interval_end: datetime,
) -> dict[str, Any]:
    expected_instrument = _expected_instrument_symbol(logical_symbol)
    pages = tuple(_iter_raw_trade_pages(raw_trades_pages))
    if not pages:
        return _raw_trades_unavailable("MISSING_RAW_TRADES")
    page_provenance: list[dict[str, Any]] = []
    by_trade_id: dict[str, dict[str, Any]] = {}
    provenance_by_trade_id: dict[str, list[dict[str, Any]]] = {}
    page_ids: set[str] = set()
    selection_digest: str | None = None
    source_identity: dict[str, str] | None = None
    for page in pages:
        response_symbol = page.get("_response_symbol")
        if response_symbol is None:
            return _raw_trades_unavailable("RAW_TRADES_LOGICAL_SYMBOL_PROVENANCE_UNAVAILABLE")
        if str(response_symbol).upper() != logical_symbol.upper():
            return _raw_trades_unavailable("RAW_TRADES_LOGICAL_SYMBOL_MISMATCH")
        selection = page.get("selection")
        payload = page.get("payload")
        coverage_payload = page.get("coverage")
        if not isinstance(selection, Mapping) or not isinstance(payload, Mapping) or not isinstance(coverage_payload, Mapping):
            return _raw_trades_unavailable("RAW_TRADES_PAGE_MALFORMED")
        if selection.get("dataset") != "RAW_TRADES" or selection.get("mode") != "INTERVAL":
            return _raw_trades_unavailable("RAW_TRADES_SELECTOR_MISMATCH")
        try:
            selected_from = _parse_iso(str(selection.get("range_from")))
            selected_to = _parse_iso(str(selection.get("range_to")))
        except (TypeError, ValueError):
            return _raw_trades_unavailable("RAW_TRADES_SELECTOR_MALFORMED")
        if selected_from != interval_start.astimezone(UTC) or selected_to != interval_end.astimezone(UTC):
            return _raw_trades_unavailable("RAW_TRADES_INTERVAL_MISMATCH")
        if selection.get("completed_only") not in {False, None} or selection.get("timeframe") is not None:
            return _raw_trades_unavailable("RAW_TRADES_SELECTOR_MISMATCH")
        missing_ranges = coverage_payload.get("missing_ranges")
        if (
            coverage_payload.get("coverage_complete") is not True
            or coverage_payload.get("source_finality_confirmed") is not True
            or coverage_payload.get("pagination_complete") is not True
            or missing_ranges not in ((), [])
        ):
            return _raw_trades_unavailable("RAW_TRADES_COVERAGE_INCOMPLETE")
        expected_page_ids = tuple(str(item) for item in coverage_payload.get("expected_page_ids") or ())
        page_id = str(page.get("page_id") or "")
        source_snapshot_id = str(page.get("source_snapshot_id") or "")
        if not page_id or not source_snapshot_id or page_id not in expected_page_ids:
            return _raw_trades_unavailable("RAW_TRADES_PAGE_PROVENANCE_UNAVAILABLE")
        if page_id in page_ids:
            return _raw_trades_unavailable("RAW_TRADES_DUPLICATE_PAGE_ID")
        page_ids.add(page_id)
        current_selection_digest = str(page.get("selection_digest") or "")
        if not current_selection_digest:
            return _raw_trades_unavailable("RAW_TRADES_PAGE_PROVENANCE_UNAVAILABLE")
        if selection_digest is None:
            selection_digest = current_selection_digest
        elif current_selection_digest != selection_digest:
            return _raw_trades_unavailable("RAW_TRADES_PAGE_SET_INCONSISTENT")
        dataset_payload = payload.get("RAW_TRADES")
        if not isinstance(dataset_payload, Mapping):
            return _raw_trades_unavailable("RAW_TRADES_PAYLOAD_MALFORMED")
        if dataset_payload.get("status") != "AVAILABLE":
            return _raw_trades_unavailable("RAW_TRADES_PAYLOAD_UNAVAILABLE")
        source_endpoint = str(dataset_payload.get("source_endpoint") or "")
        if not source_endpoint:
            return _raw_trades_unavailable("RAW_TRADES_SOURCE_PROVENANCE_UNAVAILABLE")
        endpoint_logical = _source_endpoint_token(source_endpoint, "logical")
        endpoint_instrument = _source_endpoint_token(source_endpoint, "instrument")
        endpoint_revision = _source_endpoint_token(source_endpoint, "revision")
        endpoint_manifest = _source_endpoint_token(source_endpoint, "manifest_digest")
        if endpoint_logical is None:
            return _raw_trades_unavailable("RAW_TRADES_LOGICAL_SYMBOL_PROVENANCE_UNAVAILABLE")
        if endpoint_instrument is None:
            return _raw_trades_unavailable("RAW_TRADES_INSTRUMENT_PROVENANCE_UNAVAILABLE")
        if endpoint_revision is None or endpoint_manifest is None:
            return _raw_trades_unavailable("RAW_TRADES_SOURCE_PROVENANCE_UNAVAILABLE")
        if endpoint_logical.upper() != logical_symbol.upper():
            return _raw_trades_unavailable("RAW_TRADES_LOGICAL_SYMBOL_MISMATCH")
        if endpoint_instrument.upper() != expected_instrument:
            return _raw_trades_unavailable("RAW_TRADES_INSTRUMENT_SYMBOL_MISMATCH")
        current_source_identity = {
            "logical_symbol": endpoint_logical.upper(),
            "instrument_symbol": endpoint_instrument.upper(),
            "source_revision": endpoint_revision,
            "manifest_digest": endpoint_manifest,
        }
        if source_identity is None:
            source_identity = current_source_identity
        elif current_source_identity != source_identity:
            return _raw_trades_unavailable("RAW_TRADES_PAGE_SET_INCONSISTENT")
        data = dataset_payload.get("data")
        if not isinstance(data, Sequence) or isinstance(data, (str, bytes)):
            return _raw_trades_unavailable("RAW_TRADES_PAYLOAD_MALFORMED")
        page_provenance.append(
            {
                "page_id": page_id,
                "page_index": page.get("page_index"),
                "selection_digest": page.get("selection_digest"),
                "source_snapshot_id": source_snapshot_id,
                "source_endpoint": source_endpoint,
                "coverage_digest": canonical_json_digest(coverage_payload),
            }
        )
        for raw_trade in data:
            trade, trade_provenance, reason = _parse_aggressive_raw_trade(
                raw_trade,
                page_id=page_id,
                source_snapshot_id=source_snapshot_id,
                source_endpoint=source_endpoint,
                interval_start=interval_start,
                interval_end=interval_end,
            )
            if reason is not None:
                return _raw_trades_unavailable(reason)
            assert trade is not None
            assert trade_provenance is not None
            existing = by_trade_id.get(trade["trade_id"])
            if existing is None:
                by_trade_id[trade["trade_id"]] = trade
                provenance_by_trade_id[trade["trade_id"]] = [trade_provenance]
                continue
            if existing != trade:
                return _raw_trades_unavailable("RAW_TRADES_DUPLICATE_CONFLICT")
            if trade_provenance not in provenance_by_trade_id[trade["trade_id"]]:
                provenance_by_trade_id[trade["trade_id"]].append(trade_provenance)
    trades = tuple(sorted(by_trade_id.values(), key=lambda item: (item["occurred_at"], item["trade_id"])))
    trade_population = tuple(
        {
            **trade,
            "source_provenance": tuple(
                sorted(
                    provenance_by_trade_id[trade["trade_id"]],
                    key=lambda item: (item["source_snapshot_id"], item["page_id"], item["source_endpoint"]),
                )
            ),
        }
        for trade in trades
    )
    trade_population_digest = canonical_json_digest(trade_population)
    page_provenance_ordered = tuple(sorted(page_provenance, key=lambda item: (str(item["page_index"]), item["page_id"])))
    return {
        "status": "AVAILABLE",
        "instrument_symbol": expected_instrument,
        "trades": trades,
        "trade_population": trade_population,
        "trade_population_digest": trade_population_digest,
        "page_provenance_digest": canonical_json_digest(page_provenance_ordered),
        "pages": page_provenance_ordered,
        "source_identity": source_identity or {},
    }


def _iter_raw_trade_pages(raw_trades_pages: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    pages: list[Mapping[str, Any]] = []
    for item in raw_trades_pages:
        response = item.get("market_data_response")
        if isinstance(response, Mapping):
            response_symbol = response.get("symbol")
            results = response.get("selection_results")
            if isinstance(results, Sequence) and not isinstance(results, (str, bytes)):
                pages.extend(
                    {**page, "_response_symbol": response_symbol}
                    for page in results
                    if isinstance(page, Mapping)
                )
            continue
        results = item.get("selection_results")
        if isinstance(results, Sequence) and not isinstance(results, (str, bytes)):
            pages.extend(page for page in results if isinstance(page, Mapping))
            continue
        pages.append(item)
    return tuple(pages)


def _parse_aggressive_raw_trade(
    raw_trade: Any,
    *,
    page_id: str,
    source_snapshot_id: str,
    source_endpoint: str,
    interval_start: datetime,
    interval_end: datetime,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    if not isinstance(raw_trade, Mapping):
        return None, None, "RAW_TRADES_ROW_MALFORMED"
    trade_id = str(raw_trade.get("trade_id") or "")
    if not trade_id:
        return None, None, "RAW_TRADES_ROW_MALFORMED"
    try:
        occurred_at = _parse_iso(str(raw_trade.get("occurred_at")))
    except (TypeError, ValueError):
        return None, None, "RAW_TRADES_ROW_MALFORMED"
    if not (interval_start.astimezone(UTC) <= occurred_at < interval_end.astimezone(UTC)):
        return None, None, "RAW_TRADES_ROW_OUT_OF_INTERVAL"
    side = str(raw_trade.get("taker_side") or "").upper()
    if side not in {"BUY", "SELL"}:
        return None, None, "RAW_TRADES_TAKER_SIDE_UNAVAILABLE"
    try:
        price = Decimal(str(raw_trade.get("price")))
        quantity = Decimal(str(raw_trade.get("quantity_base")))
        notional = Decimal(str(raw_trade.get("notional_quote")))
    except Exception:
        return None, None, "RAW_TRADES_ROW_MALFORMED"
    if price <= 0 or quantity <= 0 or notional <= 0:
        return None, None, "RAW_TRADES_ROW_MALFORMED"
    return {
        "trade_id": trade_id,
        "occurred_at": _iso(occurred_at),
        "taker_side": side,
        "price": _decimal_text(price),
        "quantity_base": _decimal_text(quantity),
        "notional_quote": _decimal_text(notional),
    }, {
        "trade_id": trade_id,
        "page_id": page_id,
        "source_snapshot_id": source_snapshot_id,
        "source_endpoint": source_endpoint,
    }, None


def _raw_trades_unavailable(reason_code: str) -> dict[str, Any]:
    return {"status": "UNAVAILABLE", "reason_code": reason_code}


def _source_endpoint_token(source_endpoint: str, token: str) -> str | None:
    for separator in ("#", ";"):
        for chunk in source_endpoint.split(separator):
            for part in chunk.split(";"):
                key, sep, value = part.partition("=")
                if sep and key == token:
                    return value
    return None


def _metric_source_timeframe(metric_ref: str) -> str:
    if metric_ref in {
        "F-001 trigger_result",
        "F-002 trigger_result",
        "AGGRESSIVE_VOLUME_DELTA_PCT",
        "RETURN(asset,5m)",
        "DE",
        "ATR percentile",
        "BTC_CONTEXT_SCORE",
        "BTC_RETURN_Z",
        "RELATIVE_RETURN_Z",
        "RELATIVE_RETURN_15m",
        "RELATIVE_SCORE",
        "SWING_SEQUENCE_STATE(asset,15m)",
        "SWING_SEQUENCE_STATE(asset,1h)",
        "TOD_REL_TURNOVER",
    }:
        return "1m"
    raise ResearchV1HistoricalTriggerInputUnavailable(f"research_v1_historical_metric_unavailable:{metric_ref}")


def _metric_context_window(metric_ref: str) -> str:
    if metric_ref in {"F-001 trigger_result", "F-002 trigger_result"}:
        return "1m"
    if metric_ref == "RETURN(asset,5m)":
        return "5m"
    if metric_ref in {"DE", "ATR percentile"}:
        return "15m"
    if metric_ref in {"RELATIVE_RETURN_15m", "RELATIVE_RETURN_Z", "RELATIVE_SCORE", "BTC_RETURN_Z"}:
        return "15m"
    if metric_ref == "TOD_REL_TURNOVER":
        return "5m"
    if metric_ref == "AGGRESSIVE_VOLUME_DELTA_PCT":
        return "5m"
    if metric_ref == "SWING_SEQUENCE_STATE(asset,1h)":
        return "1h"
    if metric_ref == "SWING_SEQUENCE_STATE(asset,15m)":
        return "15m"
    return _metric_source_timeframe(metric_ref)


def _is_contiguous_one_minute_window(candles: Sequence[HistoricalCandle]) -> bool:
    return _is_contiguous_window(candles, timedelta(minutes=1))


def _is_contiguous_window(candles: Sequence[Any], duration: timedelta) -> bool:
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
    if timeframe == "5m":
        return timedelta(minutes=5)
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


def _set_candle(candle: Any) -> Candle:
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


def _candle_id(candle: HistoricalCandle | AggregatedHistoricalCandle) -> str:
    if isinstance(candle, AggregatedHistoricalCandle):
        basis = {
            "aggregation_provenance_digest": candle.aggregation_provenance_digest,
            "constituent_candle_ids": list(candle.constituent_candle_ids),
            "candle_id": _raw_candle_id(candle.candle),
        }
        return f"hist-candle-{canonical_json_digest(basis)[:24]}"
    return _raw_candle_id(candle)


def _raw_candle_id(candle: HistoricalCandle) -> str:
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
