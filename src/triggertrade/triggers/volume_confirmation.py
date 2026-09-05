"""TRG-002 robust volume confirmation trigger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from typing import Iterable

from triggertrade.market_data import BybitCandle


class VolumeConfirmationResult(StrEnum):
    CONFIRMED = "CONFIRMED"
    NOT_CONFIRMED = "NOT_CONFIRMED"


@dataclass(frozen=True)
class VolumeConfirmationConfig:
    rule_id: str = "TRG-002"
    version: str = "0.1.0"
    logical_name: str = "TRG-VOLUME"
    display_name: str = "Robust Volume Confirmation"
    lookback_candles: int = 60
    relative_volume_threshold: Decimal = Decimal("2.0")
    percentile_threshold: Decimal = Decimal("90")
    timeframe: str = "1m"
    stale_after_seconds: int = 120


@dataclass(frozen=True)
class VolumeConfirmationEvaluation:
    evaluation_id: str
    rule_id: str
    rule_version: str
    logical_name: str
    symbol: str
    timeframe: str
    observed_at: str
    current_volume: str | None
    median_volume_60: str | None
    relative_volume: str | None
    volume_percentile: str | None
    relative_volume_threshold: str
    percentile_threshold: str
    condition_result: bool
    result: VolumeConfirmationResult
    missing_data_reason: str | None = None
    stale_data_reason: str | None = None


@dataclass(frozen=True)
class VolumeCandleWindow:
    symbol: str
    timeframe: str
    observed_at: datetime
    current_candle: BybitCandle | None
    previous_candles: tuple[BybitCandle, ...]
    current_candle_completed: bool = True

    def is_stale(self, *, now: datetime, stale_after_seconds: int) -> bool:
        observed = self.observed_at
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=UTC)
        return (now - observed).total_seconds() > stale_after_seconds


class RobustVolumeConfirmationTrigger:
    def __init__(self, config: VolumeConfirmationConfig | None = None, *, symbol: str = "BTCUSDT") -> None:
        self.config = config or VolumeConfirmationConfig()
        self.symbol = symbol

    def evaluate(self, window: VolumeCandleWindow, *, now: datetime | None = None) -> VolumeConfirmationEvaluation:
        now = now or datetime.now(UTC)
        missing: str | None = None
        stale: str | None = None
        current_volume: Decimal | None = None
        median: Decimal | None = None
        relative: Decimal | None = None
        percentile: Decimal | None = None
        condition = False

        if window.symbol != self.symbol:
            missing = "wrong_symbol"
        elif window.timeframe != self.config.timeframe:
            missing = "wrong_timeframe"
        elif not window.current_candle_completed:
            missing = "current_candle_not_completed"
        elif window.current_candle is None:
            missing = "missing_current_volume"
        elif window.is_stale(now=now, stale_after_seconds=self.config.stale_after_seconds):
            stale = "stale_candle"
        elif len(window.previous_candles) < self.config.lookback_candles:
            missing = "insufficient_previous_candles"
        else:
            current_volume = window.current_candle.volume
            previous = tuple(candle.volume for candle in window.previous_candles[-self.config.lookback_candles :])
            if current_volume is None:
                missing = "missing_current_volume"
            else:
                median = median_decimal(previous)
                if median <= 0:
                    missing = "zero_median_volume"
                else:
                    relative = current_volume / median
                    percentile = empirical_percentile_rank(current_volume, previous)
                    condition = (
                        relative >= self.config.relative_volume_threshold
                        and percentile >= self.config.percentile_threshold
                    )

        result = VolumeConfirmationResult.CONFIRMED if condition else VolumeConfirmationResult.NOT_CONFIRMED
        return VolumeConfirmationEvaluation(
            evaluation_id=_evaluation_id(self.config, window, current_volume, median, relative, percentile, result),
            rule_id=self.config.rule_id,
            rule_version=self.config.version,
            logical_name=self.config.logical_name,
            symbol=window.symbol,
            timeframe=window.timeframe,
            observed_at=_iso(window.observed_at),
            current_volume=None if current_volume is None else str(current_volume),
            median_volume_60=None if median is None else str(median),
            relative_volume=None if relative is None else str(relative),
            volume_percentile=None if percentile is None else str(percentile),
            relative_volume_threshold=str(self.config.relative_volume_threshold),
            percentile_threshold=str(self.config.percentile_threshold),
            condition_result=condition,
            result=result,
            missing_data_reason=missing,
            stale_data_reason=stale,
        )


def median_decimal(values: Iterable[Decimal]) -> Decimal:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("median requires at least one value")
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / Decimal("2")


def empirical_percentile_rank(current: Decimal, previous_values: Iterable[Decimal]) -> Decimal:
    previous = tuple(previous_values)
    if not previous:
        raise ValueError("percentile rank requires previous values")
    less_or_equal = sum(1 for value in previous if value <= current)
    return (Decimal(less_or_equal) / Decimal(len(previous))) * Decimal("100")


def _evaluation_id(
    config: VolumeConfirmationConfig,
    window: VolumeCandleWindow,
    current: Decimal | None,
    median: Decimal | None,
    relative: Decimal | None,
    percentile: Decimal | None,
    result: VolumeConfirmationResult,
) -> str:
    payload = "|".join(
        [
            config.rule_id,
            config.version,
            window.symbol,
            window.timeframe,
            _iso(window.observed_at),
            "" if current is None else str(current),
            "" if median is None else str(median),
            "" if relative is None else str(relative),
            "" if percentile is None else str(percentile),
            result.value,
        ]
    )
    return f"trg002-{sha256(payload.encode('utf-8')).hexdigest()[:24]}"


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()
