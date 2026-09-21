"""Pure Set formula kernels for the frozen v1.2.15 B5A checkpoint."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Iterable

from triggertrade.numeric_policy import (
    NumericPolicyError,
    canonical_decimal_text,
    compare_exact,
    exact_divide,
    exact_midpoint_sqrt,
    parse_decimal_text,
    q18_wire,
    q36_working,
)


class SetKernelError(ValueError):
    """Raised when a Set kernel receives invalid structural inputs."""


class IndicatorStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class TriggerResult(StrEnum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNAVAILABLE = "UNAVAILABLE"


class SignEvidence(StrEnum):
    UP = "UP"
    DOWN = "DOWN"
    FLAT = "FLAT"
    UNAVAILABLE = "UNAVAILABLE"


class Direction(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


class SwingSequenceState(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    AMBIGUOUS = "AMBIGUOUS"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class Candle:
    candle_id: str
    symbol: str
    timeframe: str
    opened_at: str
    closed_at: str
    high: str
    low: str
    close: str
    volume: str = "0"
    venue: str = "BYBIT"
    product: str = "USDT_LINEAR_PERPETUAL"
    source: str = "KLINES"
    completed: bool = True
    source_final: bool = True
    coverage_complete: bool = True

    def require_common(self, *, timeframe: str, symbol: str | None = None) -> None:
        _text(self.candle_id, "candle_id")
        _text(self.symbol, "symbol")
        _text(self.opened_at, "opened_at")
        _text(self.closed_at, "closed_at")
        if self.timeframe != timeframe:
            raise SetKernelError("candle timeframe mismatch")
        if symbol is not None and self.symbol.upper() != symbol.upper():
            raise SetKernelError("candle symbol mismatch")
        if not self.completed or not self.source_final or not self.coverage_complete:
            raise SetKernelError("candle is not completed/final/complete")

    @property
    def high_value(self) -> Fraction:
        return _nonnegative_decimal(self.high, "high")

    @property
    def low_value(self) -> Fraction:
        return _nonnegative_decimal(self.low, "low")

    @property
    def close_value(self) -> Fraction:
        return _nonnegative_decimal(self.close, "close")

    @property
    def volume_value(self) -> Fraction:
        return _nonnegative_decimal(self.volume, "volume")

    def require_ohlc_geometry(self) -> None:
        low = self.low_value
        close = self.close_value
        high = self.high_value
        if low > close or close > high:
            raise SetKernelError("candle OHLC geometry is invalid")


@dataclass(frozen=True)
class PriceDisplacementResult:
    arithmetic_status: IndicatorStatus
    trigger_result: TriggerResult
    move_pct_work: str | None
    sign_evidence: SignEvidence
    reason_code: str | None
    evaluation_slot: str
    freshness_policy_version: str = "F001_FRESHNESS_V1_CURRENT_COMPLETED_1M_SLOT_ONLY"

    def to_payload(self) -> dict[str, object]:
        return {
            "f001_price_displacement": {
                "arithmetic_status": self.arithmetic_status.value,
                "trigger_result": self.trigger_result.value,
                "move_pct_work": self.move_pct_work,
                "sign_evidence": self.sign_evidence.value,
                "reason_code": self.reason_code,
                "evaluation_slot": self.evaluation_slot,
                "freshness_policy_version": self.freshness_policy_version,
            }
        }


@dataclass(frozen=True)
class ParticipationResult:
    status: IndicatorStatus
    trigger_result: TriggerResult
    median_baseline: str | None
    rank_count: int | None
    relative_volume: str | None
    rank_percent: str | None
    reason_code: str | None
    evaluation_slot: str

    def to_payload(self) -> dict[str, object]:
        return {
            "f002_participation": {
                "status": self.status.value,
                "trigger_result": self.trigger_result.value,
                "median_baseline": self.median_baseline,
                "rank_count": self.rank_count,
                "relative_volume": self.relative_volume,
                "rank_percent": self.rank_percent,
                "reason_code": self.reason_code,
                "evaluation_slot": self.evaluation_slot,
            }
        }


@dataclass(frozen=True)
class ATRUpdateResult:
    status: IndicatorStatus
    atr_work: str | None
    true_range_work: str | None
    close_for_pct: str | None
    atr_pct_work: str | None
    atr_wire: str | None
    atr_pct_wire: str | None
    reason_code: str | None
    processed_candle_id: str | None

    def to_payload(self) -> dict[str, object]:
        return {
            "atr_update": {
                "status": self.status.value,
                "atr_work": self.atr_work,
                "true_range_work": self.true_range_work,
                "close_for_pct": self.close_for_pct,
                "atr_pct_work": self.atr_pct_work,
                "atr_wire": self.atr_wire,
                "atr_pct_wire": self.atr_pct_wire,
                "reason_code": self.reason_code,
                "processed_candle_id": self.processed_candle_id,
            }
        }


@dataclass(frozen=True)
class SwingPoint:
    point_type: str
    candle_id: str
    price: str
    confirmed_at: str


@dataclass(frozen=True)
class ClassifierInputs:
    structure_1h: SwingSequenceState
    structure_15m: SwingSequenceState
    de_15m: str
    momentum_score: str
    vnm_5m_z: str
    relative_score: str
    relative_return_z: str
    aggressive_delta_pct: str
    tod_relative_turnover: str
    atr_pct_percentile_15m: str
    btc_structure_1h: SwingSequenceState
    btc_return_z: str


@dataclass(frozen=True)
class ClassifierResult:
    status: IndicatorStatus
    direction: Direction
    score_work: str | None
    rejection_stage: str | None
    veto_reason: str | None
    hard_gate_passed: bool

    def to_payload(self) -> dict[str, object]:
        return {
            "f005_classifier": {
                "status": self.status.value,
                "direction": self.direction.value,
                "score_work": self.score_work,
                "rejection_stage": self.rejection_stage,
                "veto_reason": self.veto_reason,
                "hard_gate_passed": self.hard_gate_passed,
            }
        }


def evaluate_f001_price_displacement(
    *,
    reference: Candle,
    observed: Candle,
    theta_move_pct: str | None,
    requested_slot: str,
) -> PriceDisplacementResult:
    try:
        reference.require_common(timeframe="1m")
        observed.require_common(timeframe="1m", symbol=reference.symbol)
        if reference.candle_id == observed.candle_id:
            raise SetKernelError("reference and observed candles must have distinct source identities")
        reference.require_ohlc_geometry()
        observed.require_ohlc_geometry()
        if reference.venue != observed.venue or reference.product != observed.product or reference.source != observed.source:
            raise SetKernelError("reference and observed candles must share venue/product/source")
        reference_price = reference.close_value
        observed_price = observed.close_value
        if reference_price <= 0:
            raise SetKernelError("reference_price must be positive")
        move = q36_working(exact_divide((observed_price - reference_price) * 100, reference_price)).value
        move_text = canonical_decimal_text(move)
        sign = SignEvidence.UP if move > 0 else SignEvidence.DOWN if move < 0 else SignEvidence.FLAT
    except (NumericPolicyError, SetKernelError) as exc:
        return PriceDisplacementResult(IndicatorStatus.UNAVAILABLE, TriggerResult.UNAVAILABLE, None, SignEvidence.UNAVAILABLE, str(exc), requested_slot)
    try:
        if theta_move_pct is None:
            raise SetKernelError("theta_move_pct is required")
        theta = parse_decimal_text(theta_move_pct)
        if theta <= 0:
            raise SetKernelError("theta_move_pct must be positive")
    except (NumericPolicyError, SetKernelError) as exc:
        return PriceDisplacementResult(IndicatorStatus.AVAILABLE, TriggerResult.UNAVAILABLE, move_text, sign, str(exc), requested_slot)
    result = TriggerResult.TRUE if abs(move) >= theta else TriggerResult.FALSE
    return PriceDisplacementResult(IndicatorStatus.AVAILABLE, result, move_text, sign, None, requested_slot)


def evaluate_f002_participation(
    *,
    current: Candle,
    historical: Iterable[Candle],
    evaluation_slot: str,
) -> ParticipationResult:
    try:
        current.require_common(timeframe="1m")
        history = tuple(historical)
        if len(history) != 60:
            raise SetKernelError("F-002 requires exactly 60 historical candles")
        _require_unique_candle_ids((current, *history))
        current.require_ohlc_geometry()
        volumes: list[Fraction] = []
        for candle in history:
            candle.require_common(timeframe="1m", symbol=current.symbol)
            candle.require_ohlc_geometry()
            if candle.venue != current.venue or candle.product != current.product or candle.source != current.source:
                raise SetKernelError("historical candles must share venue/product/source")
            volumes.append(candle.volume_value)
        c = current.volume_value
        sorted_volumes = sorted(volumes)
        median = exact_divide(sorted_volumes[29] + sorted_volumes[30], 2)
        if median <= 0:
            raise SetKernelError("F-002 median baseline must be positive")
        rank_count = sum(1 for value in volumes if value <= c)
        relative_volume = exact_divide(c, median)
        rank_percent = exact_divide(100 * rank_count, 60)
        trigger = TriggerResult.TRUE if relative_volume >= 2 and rank_count >= 54 else TriggerResult.FALSE
        return ParticipationResult(
            IndicatorStatus.AVAILABLE,
            trigger,
            canonical_decimal_text(median),
            rank_count,
            _rational_text(relative_volume),
            _rational_text(rank_percent),
            None,
            evaluation_slot,
        )
    except (NumericPolicyError, SetKernelError) as exc:
        return ParticipationResult(IndicatorStatus.UNAVAILABLE, TriggerResult.UNAVAILABLE, None, None, None, None, str(exc), evaluation_slot)


def true_range(candle: Candle, *, previous_close: str) -> Fraction:
    candle.require_common(timeframe="15m")
    candle.require_ohlc_geometry()
    predecessor = _nonnegative_decimal(previous_close, "previous_close")
    high = candle.high_value
    low = candle.low_value
    return max(high - low, abs(high - predecessor), abs(low - predecessor))


def wilder_atr_seed(*, seed_candles: Iterable[Candle], predecessor_close: str) -> ATRUpdateResult:
    candles = tuple(seed_candles)
    if len(candles) != 14:
        return ATRUpdateResult(IndicatorStatus.UNAVAILABLE, None, None, None, None, None, None, "ATR seed requires 14 candles", None)
    prior = predecessor_close
    ranges: list[Fraction] = []
    try:
        _require_unique_candle_ids(candles)
        for candle in candles:
            candle.require_common(timeframe="15m", symbol=candles[0].symbol)
            if candle.venue != candles[0].venue or candle.product != candles[0].product or candle.source != candles[0].source:
                raise SetKernelError("seed candles must share venue/product/source")
            tr = true_range(candle, previous_close=prior)
            ranges.append(tr)
            prior = candle.close
        seed = q36_working(exact_divide(sum(ranges, Fraction(0)), 14)).value
        current = candles[-1]
        return _atr_result(seed, ranges[-1], current)
    except (NumericPolicyError, SetKernelError) as exc:
        return ATRUpdateResult(IndicatorStatus.UNAVAILABLE, None, None, None, None, None, None, str(exc), None)


def wilder_atr_update(*, prior_atr_work: str, candle: Candle, previous_close: str) -> ATRUpdateResult:
    try:
        prior = parse_decimal_text(prior_atr_work)
        if prior < 0:
            raise SetKernelError("prior ATR must be nonnegative")
        if q36_working(prior).value != prior:
            raise SetKernelError("prior ATR must be a persisted Q36 work value")
        candle.require_common(timeframe="15m")
        tr = true_range(candle, previous_close=previous_close)
        updated = q36_working(exact_divide(13 * prior + tr, 14)).value
        return _atr_result(updated, tr, candle)
    except (NumericPolicyError, SetKernelError) as exc:
        return ATRUpdateResult(IndicatorStatus.UNAVAILABLE, None, None, None, None, None, None, str(exc), candle.candle_id)


def atr_pct_exports(*, atr_work: str, close: str) -> tuple[str | None, str | None, str | None]:
    atr = parse_decimal_text(atr_work)
    close_value = _nonnegative_decimal(close, "close")
    atr_wire = q18_wire(atr).value
    if close_value <= 0:
        return canonical_decimal_text(atr_wire), None, None
    atr_pct = q36_working(exact_divide(100 * atr, close_value)).value
    return canonical_decimal_text(atr_wire), canonical_decimal_text(atr_pct), canonical_decimal_text(q18_wire(atr_pct).value)


def normalize_working(*, current: str, population: Iterable[str]) -> str | None:
    z = zscore_working(current=current, population=population)
    if z is None:
        return None
    clipped = _clip(exact_divide(z, 2), Fraction(-1), Fraction(1))
    return canonical_decimal_text(q36_working(clipped).value)


def zscore_working(*, current: str, population: Iterable[str]) -> Fraction | None:
    values = tuple(parse_decimal_text(value) for value in population)
    if not values:
        return None
    current_value = parse_decimal_text(current)
    mean = exact_divide(sum(values, Fraction(0)), len(values))
    variance = exact_divide(sum((value - mean) * (value - mean) for value in values), len(values))
    stddev = exact_midpoint_sqrt(variance).value
    if stddev == 0:
        return None
    return q36_working(exact_divide(current_value - mean, stddev)).value


def directional_efficiency(*, closes: Iterable[str]) -> str | None:
    values = tuple(parse_decimal_text(value) for value in closes)
    if len(values) != 9:
        raise SetKernelError("directional efficiency requires 9 close values for N=8")
    denominator = sum(abs(values[i] - values[i - 1]) for i in range(1, len(values)))
    if denominator == 0:
        return "0"
    return canonical_decimal_text(q36_working(exact_divide(abs(values[-1] - values[0]), denominator)).value)


def swing_points(candles: Iterable[Candle], *, point_type: str) -> tuple[SwingPoint, ...]:
    point_type = point_type.upper()
    if point_type not in {"HIGH", "LOW"}:
        raise SetKernelError("point_type must be HIGH or LOW")
    values = tuple(candles)
    _require_unique_candle_ids(values)
    if values:
        first = values[0]
        first.require_common(timeframe=first.timeframe)
        for candle in values:
            candle.require_common(timeframe=first.timeframe, symbol=first.symbol)
            if candle.venue != first.venue or candle.product != first.product or candle.source != first.source:
                raise SetKernelError("swing candles must share venue/product/source")
            candle.require_ohlc_geometry()
    points: list[SwingPoint] = []
    for index in range(2, len(values) - 2):
        candidate = values[index]
        if point_type == "HIGH":
            price = candidate.high_value
            qualifies = (
                price > values[index - 1].high_value
                and price > values[index - 2].high_value
                and price >= values[index + 1].high_value
                and price >= values[index + 2].high_value
            )
            price_text = candidate.high
        else:
            price = candidate.low_value
            qualifies = (
                price < values[index - 1].low_value
                and price < values[index - 2].low_value
                and price <= values[index + 1].low_value
                and price <= values[index + 2].low_value
            )
            price_text = candidate.low
        if qualifies:
            points.append(SwingPoint(point_type, candidate.candle_id, canonical_decimal_text(parse_decimal_text(price_text)), values[index + 2].closed_at))
    return tuple(points)


def swing_sequence_state(*, highs: Iterable[SwingPoint], lows: Iterable[SwingPoint], tick_size: str) -> SwingSequenceState:
    high_points = tuple(point for point in highs if point.point_type == "HIGH")
    low_points = tuple(point for point in lows if point.point_type == "LOW")
    if len(high_points) < 2 or len(low_points) < 2:
        return SwingSequenceState.UNAVAILABLE
    tick = parse_decimal_text(tick_size)
    if tick <= 0:
        raise SetKernelError("tick_size must be positive")
    h1, h2 = parse_decimal_text(high_points[-2].price), parse_decimal_text(high_points[-1].price)
    l1, l2 = parse_decimal_text(low_points[-2].price), parse_decimal_text(low_points[-1].price)
    if h2 > h1 + tick and l2 > l1 + tick:
        return SwingSequenceState.BULLISH
    if h2 < h1 - tick and l2 < l1 - tick:
        return SwingSequenceState.BEARISH
    return SwingSequenceState.AMBIGUOUS


def classify_direction(inputs: ClassifierInputs) -> ClassifierResult:
    try:
        mapped = [_structure_score(inputs.structure_1h), _structure_score(inputs.structure_15m), _structure_score(inputs.btc_structure_1h)]
        if any(value is None for value in mapped):
            return _classifier_unavailable("DATA_UNAVAILABLE")
        de = parse_decimal_text(inputs.de_15m)
        momentum_score_input = parse_decimal_text(inputs.momentum_score)
        vnm_5m_z = parse_decimal_text(inputs.vnm_5m_z)
        relative_score_input = parse_decimal_text(inputs.relative_score)
        relative_return_z = parse_decimal_text(inputs.relative_return_z)
        aggressive_delta_pct = parse_decimal_text(inputs.aggressive_delta_pct)
        tod = parse_decimal_text(inputs.tod_relative_turnover)
        atr_percentile = parse_decimal_text(inputs.atr_pct_percentile_15m)
        btc_return_z = parse_decimal_text(inputs.btc_return_z)
        if de < Fraction(30, 100):
            return _classifier_none("DIRECTIONAL_EFFICIENCY_GATE")
        if tod < Fraction(70, 100):
            return _classifier_none("ACTIVITY_GATE")
        if atr_percentile < 15 or atr_percentile > 97:
            return _classifier_none("VOLATILITY_GATE")

        structure_score = _q36(exact_divide(mapped[0] + mapped[1], 2))  # type: ignore[operator]
        de_strength = _q36(_clip(exact_divide(de - Fraction(30, 100), Fraction(40, 100)), Fraction(0), Fraction(1)))
        momentum_score = _q36(_clip(momentum_score_input, Fraction(-1), Fraction(1)))
        momentum_effective = _q36(momentum_score * _q36(Fraction(1, 2) + Fraction(1, 2) * de_strength))
        relative_score = _q36(_clip(relative_score_input, Fraction(-1), Fraction(1)))
        flow_raw = _q36(exact_divide(aggressive_delta_pct, 100))
        participation_strength = _q36(_clip(exact_divide(tod - Fraction(70, 100), Fraction(130, 100)), Fraction(0), Fraction(1)))
        flow_effective = _q36(flow_raw * _q36(Fraction(1, 2) + Fraction(1, 2) * participation_strength))
        btc_momentum = _q36(_clip(exact_divide(btc_return_z, 2), Fraction(-1), Fraction(1)))
        btc_context = _q36(Fraction(60, 100) * mapped[2] + Fraction(40, 100) * btc_momentum)  # type: ignore[operator]
        score = q36_working(
            Fraction(35, 100) * structure_score
            + Fraction(25, 100) * momentum_effective
            + Fraction(15, 100) * relative_score
            + Fraction(15, 100) * flow_effective
            + Fraction(10, 100) * btc_context
        ).value
        score_text = canonical_decimal_text(score)
        if score >= Fraction(35, 100):
            veto = _candidate_veto(Direction.LONG, btc_context, relative_return_z, vnm_5m_z)
            return ClassifierResult(IndicatorStatus.AVAILABLE, Direction.NONE if veto else Direction.LONG, score_text, None, veto, True)
        if score <= Fraction(-35, 100):
            veto = _candidate_veto(Direction.SHORT, btc_context, relative_return_z, vnm_5m_z)
            return ClassifierResult(IndicatorStatus.AVAILABLE, Direction.NONE if veto else Direction.SHORT, score_text, None, veto, True)
        return ClassifierResult(IndicatorStatus.AVAILABLE, Direction.NONE, score_text, None, None, True)
    except (NumericPolicyError, SetKernelError):
        return _classifier_unavailable("DATA_UNAVAILABLE")


def q18_export_text(value: str) -> str:
    return canonical_decimal_text(q18_wire(parse_decimal_text(value)).value)


def _q36(value: Fraction | int) -> Fraction:
    return q36_working(value).value


def _rational_text(value: Fraction) -> str:
    try:
        return canonical_decimal_text(value)
    except NumericPolicyError:
        return f"{value.numerator}/{value.denominator}"


def _atr_result(atr: Fraction, true_range_value: Fraction, candle: Candle) -> ATRUpdateResult:
    atr_text = canonical_decimal_text(atr)
    atr_wire, atr_pct_work, atr_pct_wire = atr_pct_exports(atr_work=atr_text, close=candle.close)
    return ATRUpdateResult(
        IndicatorStatus.AVAILABLE,
        atr_text,
        canonical_decimal_text(q36_working(true_range_value).value),
        candle.close,
        atr_pct_work,
        atr_wire,
        atr_pct_wire,
        None if atr_pct_work is not None else "ATR_PCT_CLOSE_ZERO",
        candle.candle_id,
    )


def _candidate_veto(direction: Direction, btc_context: Fraction, relative_z: Fraction, local_vnm_z: Fraction) -> str | None:
    if direction is Direction.LONG:
        if btc_context <= Fraction(-70, 100):
            return "BTC_CONTRADICTION_VETO"
        if relative_z <= -2:
            return "RELATIVE_CONTRADICTION_VETO"
        if local_vnm_z <= -2:
            return "LOCAL_MOMENTUM_VETO"
    else:
        if btc_context >= Fraction(70, 100):
            return "BTC_CONTRADICTION_VETO"
        if relative_z >= 2:
            return "RELATIVE_CONTRADICTION_VETO"
        if local_vnm_z >= 2:
            return "LOCAL_MOMENTUM_VETO"
    return None


def _classifier_none(stage: str) -> ClassifierResult:
    return ClassifierResult(IndicatorStatus.AVAILABLE, Direction.NONE, None, stage, None, False)


def _classifier_unavailable(stage: str) -> ClassifierResult:
    return ClassifierResult(IndicatorStatus.UNAVAILABLE, Direction.NONE, None, stage, None, False)


def _structure_score(state: SwingSequenceState) -> Fraction | None:
    if state is SwingSequenceState.BULLISH:
        return Fraction(1)
    if state is SwingSequenceState.BEARISH:
        return Fraction(-1)
    if state is SwingSequenceState.AMBIGUOUS:
        return Fraction(0)
    return None


def _clip(value: Fraction, lower: Fraction, upper: Fraction) -> Fraction:
    return min(max(value, lower), upper)


def _text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise SetKernelError(f"{field} is required")


def _nonnegative_decimal(value: str, field: str) -> Fraction:
    parsed = parse_decimal_text(value)
    if parsed < 0:
        raise SetKernelError(f"{field} must be nonnegative")
    return parsed


def _require_unique_candle_ids(candles: Iterable[Candle]) -> None:
    seen: set[str] = set()
    for candle in candles:
        if candle.candle_id in seen:
            raise SetKernelError("duplicate candle identity is not allowed")
        seen.add(candle.candle_id)
