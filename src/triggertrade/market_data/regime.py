"""Deterministic CTX-REGIME@0.1.0 market regime classifier."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256

from triggertrade.market_data.bybit import BybitCandle
from triggertrade.market_data.futures import MarketRegimeContext, MarketRegimeLabel, RegimeCapability


REGIME_RULE_ID = "CTX-REGIME"
REGIME_VERSION = "0.1.0"
REGIME_SYMBOL = "BTCUSDT"
REGIME_CATEGORY = "linear"
REGIME_LOOKBACK_CANDLES = 30
REGIME_TIMEFRAME = "1m"
STRONG_RETURN_PCT = Decimal("0.50")
MILD_RETURN_PCT = Decimal("0.15")
STRONG_NORMALIZED_TREND = Decimal("5")
MILD_NORMALIZED_TREND = Decimal("2")
STRONG_PERSISTENCE = Decimal("0.65")
MILD_PERSISTENCE = Decimal("0.35")


@dataclass(frozen=True)
class RegimeEvaluationWindow:
    symbol: str
    timeframe: str
    observed_at: datetime
    candles: tuple[BybitCandle, ...]
    category: str = REGIME_CATEGORY
    current_candle_completed: bool = True


def evaluate_market_regime(window: RegimeEvaluationWindow) -> MarketRegimeContext:
    """Classify observed market state without predicting or executing trades."""

    if window.symbol.strip().upper() != REGIME_SYMBOL:
        return _context(window, MarketRegimeLabel.UNKNOWN, "unsupported_symbol")
    if window.category.strip().lower() != REGIME_CATEGORY:
        return _context(window, MarketRegimeLabel.UNKNOWN, "unsupported_category")
    if window.timeframe.strip().lower() not in {"1", "1m"}:
        return _context(window, MarketRegimeLabel.UNKNOWN, "unsupported_timeframe")
    if not window.current_candle_completed:
        return _context(window, MarketRegimeLabel.UNKNOWN, "current_candle_not_completed")
    try:
        sorted_candles = tuple(sorted(window.candles, key=lambda candle: candle.start_time_ms))
    except Exception:
        return _context(window, MarketRegimeLabel.UNKNOWN, "malformed_candle_window")
    if len(sorted_candles) < REGIME_LOOKBACK_CANDLES:
        return _context(window, MarketRegimeLabel.INSUFFICIENT_DATA, "need_30_completed_candles")
    sample = sorted_candles[-REGIME_LOOKBACK_CANDLES:]
    if not _is_complete_contiguous(sample, window.observed_at):
        return _context(window, MarketRegimeLabel.UNKNOWN, "incomplete_or_non_contiguous_window")
    closes = tuple(candle.close for candle in sample)
    if any(close <= 0 for close in closes):
        return _context(window, MarketRegimeLabel.INSUFFICIENT_DATA, "non_positive_close")

    step_returns = tuple((closes[index] - closes[index - 1]) / closes[index - 1] * Decimal("100") for index in range(1, len(closes)))
    window_return_pct = (closes[-1] - closes[0]) / closes[0] * Decimal("100")
    avg_abs_step_return_pct = sum((abs(value) for value in step_returns), Decimal("0")) / Decimal(len(step_returns))
    normalized_trend = Decimal("0") if avg_abs_step_return_pct == 0 else window_return_pct / avg_abs_step_return_pct
    up_steps = sum(1 for value in step_returns if value > 0)
    down_steps = sum(1 for value in step_returns if value < 0)
    directional_persistence = Decimal(up_steps - down_steps) / Decimal(len(step_returns))
    label = _classify(window_return_pct, normalized_trend, directional_persistence)

    return _context(
        window,
        label,
        None,
        input_snapshot={
            "category": REGIME_CATEGORY,
            "first_candle_open_time": _dt(sample[0]).isoformat(),
            "last_candle_open_time": _dt(sample[-1]).isoformat(),
            "last_candle_close_time": (_dt(sample[-1]) + timedelta(minutes=1)).isoformat(),
            "first_close": str(closes[0]),
            "latest_close": str(closes[-1]),
            "lookback_completed_candles": str(REGIME_LOOKBACK_CANDLES),
            "candle_ids": ",".join(_candle_id(window.symbol, window.timeframe, candle) for candle in sample),
        },
        normalized_features={
            "window_return_pct": str(window_return_pct),
            "avg_abs_step_return_pct": str(avg_abs_step_return_pct),
            "normalized_trend": str(normalized_trend),
            "directional_persistence": str(directional_persistence),
            "up_steps": str(up_steps),
            "down_steps": str(down_steps),
            "flat_steps": str(len(step_returns) - up_steps - down_steps),
        },
    )


def regime_business_key(*, symbol: str, timeframe: str, observed_at: str, rule_id: str = REGIME_RULE_ID, version: str = REGIME_VERSION) -> str:
    raw = f"{symbol.upper()}|{_normalize_timeframe(timeframe)}|{observed_at}|{rule_id}|{version}"
    return f"regime-{sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _classify(
    window_return_pct: Decimal,
    normalized_trend: Decimal,
    directional_persistence: Decimal,
) -> MarketRegimeLabel:
    if (
        window_return_pct >= STRONG_RETURN_PCT
        and normalized_trend >= STRONG_NORMALIZED_TREND
        and directional_persistence >= STRONG_PERSISTENCE
    ):
        return MarketRegimeLabel.STRONG_UPTREND
    if (
        window_return_pct >= MILD_RETURN_PCT
        and normalized_trend >= MILD_NORMALIZED_TREND
        and directional_persistence >= MILD_PERSISTENCE
    ):
        return MarketRegimeLabel.UPTREND
    if (
        window_return_pct <= -STRONG_RETURN_PCT
        and normalized_trend <= -STRONG_NORMALIZED_TREND
        and directional_persistence <= -STRONG_PERSISTENCE
    ):
        return MarketRegimeLabel.STRONG_DOWNTREND
    if (
        window_return_pct <= -MILD_RETURN_PCT
        and normalized_trend <= -MILD_NORMALIZED_TREND
        and directional_persistence <= -MILD_PERSISTENCE
    ):
        return MarketRegimeLabel.DOWNTREND
    return MarketRegimeLabel.SIDEWAYS


def _context(
    window: RegimeEvaluationWindow,
    label: MarketRegimeLabel,
    reason: str | None,
    *,
    input_snapshot: dict[str, str] | None = None,
    normalized_features: dict[str, str] | None = None,
) -> MarketRegimeContext:
    observed_at = _as_utc(window.observed_at).isoformat()
    return MarketRegimeContext(
        context_id=regime_business_key(symbol=window.symbol, timeframe=window.timeframe, observed_at=observed_at),
        symbol=window.symbol.upper(),
        timeframe=_normalize_timeframe(window.timeframe),
        observed_at=observed_at,
        capability=RegimeCapability.AVAILABLE,
        label=label,
        input_snapshot=input_snapshot
        or {
            "category": window.category.strip().lower(),
            "lookback_completed_candles": str(REGIME_LOOKBACK_CANDLES),
        },
        normalized_features=normalized_features or {},
        thresholds={
            "strong_return_pct": str(STRONG_RETURN_PCT),
            "mild_return_pct": str(MILD_RETURN_PCT),
            "strong_normalized_trend": str(STRONG_NORMALIZED_TREND),
            "mild_normalized_trend": str(MILD_NORMALIZED_TREND),
            "strong_directional_persistence": str(STRONG_PERSISTENCE),
            "mild_directional_persistence": str(MILD_PERSISTENCE),
            "boundary": "inclusive",
            "flat_step_denominator": "29",
        },
        reason=reason,
    )


def _is_complete_contiguous(candles: tuple[BybitCandle, ...], observed_at: datetime) -> bool:
    expected_ms = 60_000
    if not candles:
        return False
    for previous, current in zip(candles, candles[1:]):
        if current.start_time_ms - previous.start_time_ms != expected_ms:
            return False
    last_close_time = _dt(candles[-1]) + timedelta(minutes=1)
    return _as_utc(observed_at) == last_close_time


def _candle_id(symbol: str, timeframe: str, candle: BybitCandle) -> str:
    return f"{symbol.upper()}:{_normalize_timeframe(timeframe)}:{_dt(candle).isoformat()}"


def _dt(candle: BybitCandle) -> datetime:
    return datetime.fromtimestamp(candle.start_time_ms / 1000, UTC)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _normalize_timeframe(value: str) -> str:
    return "1m" if value.strip().lower() in {"1", "1m"} else value.strip().lower()
