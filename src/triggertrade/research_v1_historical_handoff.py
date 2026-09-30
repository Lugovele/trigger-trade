"""Research V1 factual historical MARKET_HANDOFF producer.

The producer starts from an already resolved historical Set result and builds
canonical HandoffFacts only from explicit factual historical inputs. It does
not form Sets, compute Position outputs, or synthesize missing market facts.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import ceil
from typing import Any

from triggertrade.backtest.models import HistoricalCandle
from triggertrade.canonical_json import canonical_json_digest
from triggertrade.contracts import contract_body
from triggertrade.instruments import FuturesInstrument
from triggertrade.numeric_policy import NumericPolicyError, canonical_decimal_text, parse_decimal_text
from triggertrade.persistence.postgres_research_set_registry import ResearchSetVersion
from triggertrade.research_v1_historical_sets import HistoricalSetResolution
from triggertrade.research_v1_historical_triggers import (
    AggregatedHistoricalCandle,
    _aggregate_completed_candles,
    _atr_observation_provenance,
    _atr_pct_series,
    _candle_id,
    _coerce_instrument_metadata,
    _decimal_text,
    _iso,
    _set_candle,
)
from triggertrade.set_engine import (
    Direction,
    DirectionResolutionScope,
    HandoffContext,
    HandoffFacts,
    HandoffReferenceLevel,
    SetMatchStatus,
    SetResolutionRequest,
    TriggerResult,
    build_validated_market_handoff_payload,
    swing_points,
)
from triggertrade.set_scope import SetConfigurationBinding, SetFormationEpoch


RESEARCH_V1_HISTORICAL_HANDOFF_PRODUCER_VERSION = "research_v1_historical_market_handoff@1"


class ResearchV1HistoricalMarketHandoffUnavailable(ValueError):
    """Raised when a factual historical MARKET_HANDOFF cannot be produced."""


@dataclass(frozen=True)
class HistoricalMarketHandoff:
    set_id: str
    set_version: str
    symbol: str
    decision_cycle_id: str
    set_result_id: str
    facts: HandoffFacts
    payload: Mapping[str, Any]
    evidence_digest: str
    evidence_id: str


@dataclass(frozen=True)
class _LastTradedPriceReference:
    price: str
    observed_at: str
    source_endpoint: str
    evidence_digest: str


@dataclass(frozen=True)
class _ATRReference:
    atr_15m: str
    atr_pct_15m: str
    observed_at: str
    evidence_digest: str


def produce_research_v1_historical_market_handoff(
    *,
    research_set: ResearchSetVersion,
    set_resolution: HistoricalSetResolution,
    candles: Sequence[HistoricalCandle],
    symbol: str,
    instrument_metadata: FuturesInstrument,
    last_traded_price_responses: Sequence[Mapping[str, Any]],
) -> HistoricalMarketHandoff | None:
    """Produce one canonical historical MARKET_HANDOFF for a MATCHED Set result."""

    logical_symbol = symbol.upper()

    if research_set.set_id != set_resolution.set_id:
        raise ResearchV1HistoricalMarketHandoffUnavailable(
            "research_v1_historical_market_handoff_unavailable:SET_ID_MISMATCH"
        )
    if research_set.set_version != set_resolution.set_version:
        raise ResearchV1HistoricalMarketHandoffUnavailable(
            "research_v1_historical_market_handoff_unavailable:SET_VERSION_MISMATCH"
        )
    if logical_symbol != set_resolution.symbol.upper():
        raise ResearchV1HistoricalMarketHandoffUnavailable(
            "research_v1_historical_market_handoff_unavailable:SET_SYMBOL_MISMATCH"
        )

    binding = set_resolution.configuration_binding
    if (
        str(binding.get("set_config_id", "")) != research_set.set_id
        or str(binding.get("set_config_version", "")) != research_set.set_version
    ):
        raise ResearchV1HistoricalMarketHandoffUnavailable(
            "research_v1_historical_market_handoff_unavailable:SET_CONFIGURATION_BINDING_MISMATCH"
        )

    if set_resolution.status != SetMatchStatus.MATCHED.value:
        return None
    if set_resolution.direction not in {Direction.LONG.value, Direction.SHORT.value}:
        raise ResearchV1HistoricalMarketHandoffUnavailable("research_v1_historical_market_handoff_unavailable:SET_DIRECTION_UNAVAILABLE")
    if set_resolution.decision_cycle_id is None:
        raise ResearchV1HistoricalMarketHandoffUnavailable("research_v1_historical_market_handoff_unavailable:DECISION_CYCLE_ID_UNAVAILABLE")
    decision_slot = _decision_slot(set_resolution)
    metadata, metadata_reason = _coerce_instrument_metadata(symbol=logical_symbol, instrument_metadata=instrument_metadata)
    if metadata is None:
        raise ResearchV1HistoricalMarketHandoffUnavailable(
            f"research_v1_historical_market_handoff_unavailable:{metadata_reason or 'INSTRUMENT_METADATA_UNAVAILABLE'}"
        )
    reference_price = _last_traded_price_reference(
        last_traded_price_responses=last_traded_price_responses,
        symbol=logical_symbol,
        matched_at=decision_slot,
    )
    atr = _atr_reference(candles=candles, matched_at=decision_slot)
    levels = _reference_levels(
        candles=candles,
        symbol=logical_symbol,
        matched_at=decision_slot,
        reference_price=reference_price.price,
        tick_size=metadata.tick_size,
    )
    if not levels:
        raise ResearchV1HistoricalMarketHandoffUnavailable("research_v1_historical_market_handoff_unavailable:REFERENCE_GEOMETRY_UNAVAILABLE")
    context = _context_from_research_set(research_set)
    market_snapshot_digest = canonical_json_digest(
        {
            "producer": RESEARCH_V1_HISTORICAL_HANDOFF_PRODUCER_VERSION,
            "set_result_id": set_resolution.set_result_id,
            "decision_cycle_id": set_resolution.decision_cycle_id,
            "matched_at": _iso(decision_slot),
            "last_traded_price_evidence_digest": reference_price.evidence_digest,
            "atr_evidence_digest": atr.evidence_digest,
            "instrument_metadata_digest": metadata.metadata_digest,
            "reference_levels": [level.to_payload() for level in levels],
        }
    )
    facts = HandoffFacts(
        symbol=logical_symbol,
        created_at=_iso(decision_slot),
        matched_at=_iso(decision_slot),
        market_snapshot_at=_iso(decision_slot),
        market_snapshot_id=f"rv1-market-snapshot-{market_snapshot_digest[:24]}",
        set_match_reference_price=reference_price.price,
        reference_price_observed_at=reference_price.observed_at,
        reference_price_source=reference_price.source_endpoint,
        tick_size=metadata.tick_size,
        metadata_revision=metadata.metadata_revision,
        metadata_as_of=metadata.metadata_as_of,
        atr_15m=atr.atr_15m,
        atr_pct_15m=atr.atr_pct_15m,
        reference_levels=levels,
        entry_context=context,
        sl_context=context,
        tp_context=context,
        core_set_id=research_set.set_id,
        set_family=context.set_family,
    )
    request = SetResolutionRequest(
        formation_epoch=SetFormationEpoch(
            symbol=logical_symbol,
            formation_epoch=int(decision_slot.timestamp()),
            open_event_id=f"rv1-set-open-{set_resolution.source_evidence_digest[:24]}",
            opened_at=_iso(decision_slot),
            open_payload_digest=set_resolution.source_evidence_digest,
            configuration_binding=SetConfigurationBinding.from_payload(set_resolution.configuration_binding),
        ),
        direction_scope=DirectionResolutionScope(str(set_resolution.result_payload["set_result"]["direction_scope"])),
        formation_result=TriggerResult(set_resolution.formation_result),
        evaluation_event_ids=tuple(set_resolution.evaluation_event_ids),
        source_evidence_digest=set_resolution.source_evidence_digest,
        handoff_facts=facts,
        frozen_condition=set_resolution.frozen_condition,
    )
    payload = build_validated_market_handoff_payload(
        request=request,
        direction=Direction(set_resolution.direction),
        decision_cycle_id=set_resolution.decision_cycle_id,
        set_result_id=set_resolution.set_result_id,
    )
    evidence_digest = canonical_json_digest(
        {
            "producer": RESEARCH_V1_HISTORICAL_HANDOFF_PRODUCER_VERSION,
            "set_id": research_set.set_id,
            "set_version": research_set.set_version,
            "set_resolution_evidence_digest": set_resolution.evidence_digest,
            "market_handoff_payload": payload,
        }
    )
    return HistoricalMarketHandoff(
        set_id=research_set.set_id,
        set_version=research_set.set_version,
        symbol=logical_symbol,
        decision_cycle_id=set_resolution.decision_cycle_id,
        set_result_id=set_resolution.set_result_id,
        facts=facts,
        payload=payload,
        evidence_digest=evidence_digest,
        evidence_id=f"rv1-market-handoff-{evidence_digest[:24]}",
    )


def _decision_slot(set_resolution: HistoricalSetResolution) -> datetime:
    slot = set_resolution.frozen_condition.get("decision_slot")
    if not isinstance(slot, str) or not slot:
        raise ResearchV1HistoricalMarketHandoffUnavailable("research_v1_historical_market_handoff_unavailable:DECISION_SLOT_UNAVAILABLE")
    parsed = datetime.fromisoformat(slot.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _last_traded_price_reference(
    *,
    last_traded_price_responses: Sequence[Mapping[str, Any]],
    symbol: str,
    matched_at: datetime,
) -> _LastTradedPriceReference:
    candidates: list[tuple[datetime, Mapping[str, Any], Mapping[str, Any]]] = []
    for response in last_traded_price_responses:
        body = contract_body(response, contract_type="MARKET_DATA_REQUEST", definition="MARKET_DATA_REQUEST.response")
        if str(body.get("symbol", "")).upper() != symbol.upper():
            raise ResearchV1HistoricalMarketHandoffUnavailable(
                "research_v1_historical_market_handoff_unavailable:LAST_TRADED_PRICE_SYMBOL_MISMATCH"
            )
        for result in body.get("selection_results", ()):
            selection = result.get("selection")
            payload = result.get("payload")
            coverage = result.get("coverage")
            if not isinstance(selection, Mapping) or not isinstance(payload, Mapping) or not isinstance(coverage, Mapping):
                continue
            if selection.get("dataset") != "LAST_TRADED_PRICE" or selection.get("mode") != "AS_OF":
                continue
            if not _complete_market_coverage(result):
                raise ResearchV1HistoricalMarketHandoffUnavailable(
                    "research_v1_historical_market_handoff_unavailable:LAST_TRADED_PRICE_COVERAGE_UNAVAILABLE"
                )
            last_traded_price = payload.get("LAST_TRADED_PRICE")
            if not isinstance(last_traded_price, Mapping) or last_traded_price.get("status") != "AVAILABLE":
                raise ResearchV1HistoricalMarketHandoffUnavailable(
                    "research_v1_historical_market_handoff_unavailable:LAST_TRADED_PRICE_UNAVAILABLE"
                )
            data = last_traded_price.get("data")
            if not isinstance(data, Mapping) or data.get("price") in {None, ""}:
                raise ResearchV1HistoricalMarketHandoffUnavailable(
                    "research_v1_historical_market_handoff_unavailable:LAST_TRADED_PRICE_UNAVAILABLE"
                )
            observed_at = _parse_timestamp(str(data.get("observed_at") or ""))
            if observed_at > matched_at:
                raise ResearchV1HistoricalMarketHandoffUnavailable(
                    "research_v1_historical_market_handoff_unavailable:LAST_TRADED_PRICE_FUTURE_LEAKAGE"
                )
            try:
                price = canonical_decimal_text(parse_decimal_text(str(data["price"])))
            except NumericPolicyError as exc:
                raise ResearchV1HistoricalMarketHandoffUnavailable(
                    "research_v1_historical_market_handoff_unavailable:LAST_TRADED_PRICE_UNAVAILABLE"
                ) from exc
            if parse_decimal_text(price) <= 0:
                raise ResearchV1HistoricalMarketHandoffUnavailable(
                    "research_v1_historical_market_handoff_unavailable:LAST_TRADED_PRICE_UNAVAILABLE"
                )
            candidates.append(
                (
                    observed_at,
                    result,
                    {
                        "price": price,
                        "source_endpoint": str(last_traded_price.get("source_endpoint") or ""),
                        "source_record_id": str(data.get("source_record_id") or ""),
                        "instrument_symbol": str(data.get("instrument_symbol") or ""),
                        "venue": str(data.get("venue") or ""),
                    },
                )
            )
    if not candidates:
        raise ResearchV1HistoricalMarketHandoffUnavailable(
            "research_v1_historical_market_handoff_unavailable:LAST_TRADED_PRICE_UNAVAILABLE"
        )
    observed_at, result, parsed = max(candidates, key=lambda item: (item[0], str(item[1].get("page_id", ""))))
    if not parsed["source_endpoint"]:
        raise ResearchV1HistoricalMarketHandoffUnavailable(
            "research_v1_historical_market_handoff_unavailable:LAST_TRADED_PRICE_SOURCE_UNAVAILABLE"
        )
    digest = canonical_json_digest(
        {
            "dataset": "LAST_TRADED_PRICE",
            "symbol": symbol.upper(),
            "matched_at": _iso(matched_at),
            "observed_at": _iso(observed_at),
            "price": parsed["price"],
            "source_record_id": parsed["source_record_id"],
            "instrument_symbol": parsed["instrument_symbol"],
            "venue": parsed["venue"],
            "selection_digest": result.get("selection_digest"),
            "page_id": result.get("page_id"),
            "source_snapshot_id": result.get("source_snapshot_id"),
            "source_endpoint": parsed["source_endpoint"],
            "coverage": result.get("coverage"),
        }
    )
    return _LastTradedPriceReference(parsed["price"], _iso(observed_at), parsed["source_endpoint"], digest)


def _complete_market_coverage(result: Mapping[str, Any]) -> bool:
    coverage = result.get("coverage")
    if not isinstance(coverage, Mapping):
        return False
    expected = coverage.get("expected_page_ids")
    return (
        coverage.get("coverage_complete") is True
        and coverage.get("pagination_complete") is True
        and coverage.get("source_finality_confirmed") is True
        and coverage.get("next_cursor") is None
        and coverage.get("missing_ranges") == []
        and isinstance(expected, list)
        and result.get("page_id") in expected
    )


def _atr_reference(*, candles: Sequence[HistoricalCandle], matched_at: datetime) -> _ATRReference:
    eligible = tuple(
        candle
        for candle in candles
        if candle.completed and _aware(candle.close_time) <= matched_at and str(candle.timeframe) == "1m"
    )
    if not eligible:
        raise ResearchV1HistoricalMarketHandoffUnavailable("research_v1_historical_market_handoff_unavailable:ATR_15M_UNAVAILABLE")
    fifteen_minute = _aggregate_completed_candles(eligible, timeframe="15m")
    _require_contiguous(fifteen_minute, timeframe_minutes=15, reason="ATR_15M_NON_CONTIGUOUS")
    series = _atr_pct_series(fifteen_minute)
    available = tuple((candle, update) for candle, update in series if _aware(candle.close_time) <= matched_at)
    if not available:
        raise ResearchV1HistoricalMarketHandoffUnavailable("research_v1_historical_market_handoff_unavailable:ATR_15M_UNAVAILABLE")
    candle, update = available[-1]
    expected_close = _floor_completed_slot(matched_at, timedelta(minutes=15))
    if _aware(candle.close_time) != expected_close:
        raise ResearchV1HistoricalMarketHandoffUnavailable(
            "research_v1_historical_market_handoff_unavailable:ATR_15M_STALE"
        )
    if update.atr_wire is None or update.atr_pct_wire is None:
        raise ResearchV1HistoricalMarketHandoffUnavailable("research_v1_historical_market_handoff_unavailable:ATR_15M_UNAVAILABLE")
    if parse_decimal_text(update.atr_wire) <= 0 or parse_decimal_text(update.atr_pct_wire) <= 0:
        raise ResearchV1HistoricalMarketHandoffUnavailable("research_v1_historical_market_handoff_unavailable:ATR_15M_UNAVAILABLE")
    provenance = _atr_observation_provenance(candle, update)
    return _ATRReference(
        atr_15m=update.atr_wire,
        atr_pct_15m=update.atr_pct_wire,
        observed_at=_iso(candle.close_time),
        evidence_digest=str(provenance["digest"]),
    )


def _reference_levels(
    *,
    candles: Sequence[HistoricalCandle],
    symbol: str,
    matched_at: datetime,
    reference_price: str,
    tick_size: str,
) -> tuple[HandoffReferenceLevel, ...]:
    eligible = tuple(
        candle
        for candle in candles
        if candle.completed and _aware(candle.close_time) <= matched_at and str(candle.timeframe) == "1m"
    )
    levels: list[HandoffReferenceLevel] = []
    for timeframe in ("15m", "1h"):
        aggregated = _aggregate_completed_candles(eligible, timeframe=timeframe)
        _require_contiguous(aggregated, timeframe_minutes=15 if timeframe == "15m" else 60, reason=f"REFERENCE_{timeframe.upper()}_NON_CONTIGUOUS")
        levels.extend(
            _swing_reference_levels(
                aggregated=aggregated,
                symbol=symbol,
                timeframe=timeframe,
                matched_at=matched_at,
                reference_price=reference_price,
                tick_size=tick_size,
            )
        )
    levels.extend(_previous_day_reference_levels(candles=eligible, matched_at=matched_at, reference_price=reference_price, tick_size=tick_size))
    return tuple(sorted(levels, key=lambda level: (level.available_at, level.level_type, level.level_id)))


def _swing_reference_levels(
    *,
    aggregated: Sequence[AggregatedHistoricalCandle],
    symbol: str,
    timeframe: str,
    matched_at: datetime,
    reference_price: str,
    tick_size: str,
) -> tuple[HandoffReferenceLevel, ...]:
    if len(aggregated) < 5:
        return ()
    candles = tuple(_set_candle(candle) for candle in aggregated)
    by_id = {candle.candle_id: source for candle, source in zip(candles, aggregated, strict=True)}
    levels: list[HandoffReferenceLevel] = []
    for point_type in ("HIGH", "LOW"):
        for point in swing_points(candles, point_type=point_type):
            available_at = _parse_timestamp(point.confirmed_at)
            if available_at > matched_at:
                continue
            source = by_id[point.candle_id]
            level_type = f"SWING_{point_type}_{timeframe.upper()}"
            levels.append(
                _reference_level(
                    level_type=level_type,
                    timeframe=timeframe,
                    price=point.price,
                    formed_at=_iso(source.close_time),
                    confirmed_at=_iso(available_at),
                    available_at=_iso(available_at),
                    source_metric=f"SWING_POINTS_{timeframe.upper()}",
                    matched_at=matched_at,
                    reference_price=reference_price,
                    tick_size=tick_size,
                    source_payload={
                        "point_type": point.point_type,
                        "point_candle_id": point.candle_id,
                        "point_price": point.price,
                        "point_confirmed_at": point.confirmed_at,
                        "source_candle_id": _candle_id(source),
                        "source_aggregation_digest": source.aggregation_provenance_digest,
                        "symbol": symbol.upper(),
                    },
                )
            )
    return tuple(levels)


def _previous_day_reference_levels(
    *,
    candles: Sequence[HistoricalCandle],
    matched_at: datetime,
    reference_price: str,
    tick_size: str,
) -> tuple[HandoffReferenceLevel, ...]:
    day_start = matched_at.replace(hour=0, minute=0, second=0, microsecond=0)
    prior_start = day_start - timedelta(days=1)
    prior = tuple(sorted((candle for candle in candles if prior_start <= _aware(candle.open_time) < day_start), key=lambda item: item.open_time))
    if len(prior) != 24 * 60:
        return ()
    if any(_aware(candle.open_time) != prior_start + timedelta(minutes=index) for index, candle in enumerate(prior)):
        return ()
    high = max(prior, key=lambda candle: (candle.high, candle.close_time))
    low = min(prior, key=lambda candle: (candle.low, candle.close_time))
    available_at = _iso(day_start)
    return (
        _reference_level(
            level_type="PREVIOUS_DAY_HIGH",
            timeframe="1d",
            price=_decimal_text(high.high),
            formed_at=_iso(high.close_time),
            confirmed_at=available_at,
            available_at=available_at,
            source_metric="PREVIOUS_UTC_DAY_HIGH_LOW",
            matched_at=matched_at,
            reference_price=reference_price,
            tick_size=tick_size,
            source_payload={"source_candle_id": _candle_id(high), "source_day_start": _iso(prior_start), "source_day_end": _iso(day_start)},
        ),
        _reference_level(
            level_type="PREVIOUS_DAY_LOW",
            timeframe="1d",
            price=_decimal_text(low.low),
            formed_at=_iso(low.close_time),
            confirmed_at=available_at,
            available_at=available_at,
            source_metric="PREVIOUS_UTC_DAY_HIGH_LOW",
            matched_at=matched_at,
            reference_price=reference_price,
            tick_size=tick_size,
            source_payload={"source_candle_id": _candle_id(low), "source_day_start": _iso(prior_start), "source_day_end": _iso(day_start)},
        ),
    )


def _reference_level(
    *,
    level_type: str,
    timeframe: str,
    price: str,
    formed_at: str,
    confirmed_at: str,
    available_at: str,
    source_metric: str,
    matched_at: datetime,
    reference_price: str,
    tick_size: str,
    source_payload: Mapping[str, Any],
) -> HandoffReferenceLevel:
    payload = {
        "producer": RESEARCH_V1_HISTORICAL_HANDOFF_PRODUCER_VERSION,
        "level_type": level_type,
        "timeframe": timeframe,
        "price": price,
        "formed_at": formed_at,
        "confirmed_at": confirmed_at,
        "available_at": available_at,
        "source_metric": source_metric,
        "source_payload": dict(source_payload),
    }
    return HandoffReferenceLevel(
        level_id=f"rv1-reference-level-{canonical_json_digest(payload)[:24]}",
        level_type=level_type,
        price=canonical_decimal_text(parse_decimal_text(price)),
        timeframe=timeframe,
        formed_at=formed_at,
        confirmed_at=confirmed_at,
        available_at=available_at,
        source_metric=source_metric,
        age_seconds=max(0, ceil((matched_at - _parse_timestamp(available_at)).total_seconds())),
        relative_position=_relative_position(price=price, reference_price=reference_price, tick_size=tick_size),
    )


def _relative_position(*, price: str, reference_price: str, tick_size: str) -> str:
    level = parse_decimal_text(price)
    reference = parse_decimal_text(reference_price)
    tick = parse_decimal_text(tick_size)
    if abs(level - reference) <= tick:
        return "AT_REFERENCE"
    if level < reference:
        return "BELOW_REFERENCE"
    return "ABOVE_REFERENCE"


def _context_from_research_set(research_set: ResearchSetVersion) -> HandoffContext:
    excerpt = research_set.source_yaml_excerpt
    required_markers = (
        "set_family: GENERIC",
        "role_bindings: []",
        "entry_context:",
        "sl_context:",
        "tp_context:",
        "thesis_reference_policy: NONE",
        "thesis_reference_level_id: null",
        "origin_binding: null",
    )
    if any(marker not in excerpt for marker in required_markers):
        raise ResearchV1HistoricalMarketHandoffUnavailable(
            "research_v1_historical_market_handoff_unavailable:POSITION_CONTEXT_POLICY_UNSUPPORTED"
        )
    return HandoffContext(
        set_family="GENERIC",
        thesis_reference_policy="NONE",
        thesis_reference_level_id=None,
        origin_binding=None,
    )


def _require_contiguous(candles: Sequence[AggregatedHistoricalCandle], *, timeframe_minutes: int, reason: str) -> None:
    for previous, current in zip(candles, candles[1:]):
        if _aware(current.open_time) != _aware(previous.open_time) + timedelta(minutes=timeframe_minutes):
            raise ResearchV1HistoricalMarketHandoffUnavailable(f"research_v1_historical_market_handoff_unavailable:{reason}")


def _parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ResearchV1HistoricalMarketHandoffUnavailable("research_v1_historical_market_handoff_unavailable:TIMESTAMP_UNAVAILABLE")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _floor_completed_slot(value: datetime, duration: timedelta) -> datetime:
    instant = _aware(value)
    midnight = instant.replace(hour=0, minute=0, second=0, microsecond=0)
    duration_seconds = int(duration.total_seconds())
    elapsed_seconds = int((instant - midnight).total_seconds())
    completed_seconds = (elapsed_seconds // duration_seconds) * duration_seconds
    return midnight + timedelta(seconds=completed_seconds)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = [
    "HistoricalMarketHandoff",
    "RESEARCH_V1_HISTORICAL_HANDOFF_PRODUCER_VERSION",
    "ResearchV1HistoricalMarketHandoffUnavailable",
    "produce_research_v1_historical_market_handoff",
]
