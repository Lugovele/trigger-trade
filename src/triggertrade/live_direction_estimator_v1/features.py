"""Exact ordered LDE_V1_ADJ35_U1M raw feature construction."""

from __future__ import annotations

from dataclasses import dataclass
from math import asinh, cos, isfinite, log, log1p, pi, sin, sqrt, tanh
from typing import Iterable

from .snapshot import OriginSnapshot, SnapshotResult, SUPPORT_MINUTES, build_snapshot
from .source import SourceMinute

NAMES = (
    "mom_1", "mom_3", "mom_6", "mom_12", "mom_24", "mom_48",
    "abs_mom_12", "abs_mom_48", "sign_balance_12", "sign_balance_48",
    "sign_switch_12", "body_5", "range_5", "close_location_5",
    "zero_range_5", "drawdown_12", "rebound_12", "drawdown_48",
    "rebound_48", "log_pred_rms48_u", "vol_fast", "vol_slow",
    "rms_dominance_48", "btc_mom_12", "btc_mom_48", "btc_vol_fast",
    "btc_vol_slow", "relative_12", "relative_48", "btc_local_alignment_12",
    "tod_sin", "tod_cos", "is_AVAXUSDT", "is_SUIUSDT", "is_1000PEPEUSDT",
)
GROUPS = tuple("I" if i in (14, 30, 31, 32, 33, 34) else "S" if i == 19 else "A" if 23 <= i <= 29 else "P" for i in range(35))


class FeatureError(ValueError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Aggregate:
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class RawFeatureRow:
    physical_symbol: str
    prediction_origin: object
    feature_timestamp: object
    source_snapshot_id: str
    values: tuple[float, ...]


@dataclass(frozen=True)
class FeatureResult:
    row: RawFeatureRow | None
    reasons: tuple[str, ...]


def aggregates(minutes: tuple[SourceMinute, ...]) -> tuple[Aggregate, ...]:
    if len(minutes) != SUPPORT_MINUTES:
        raise FeatureError("MISSING_REQUIRED_MINUTE")
    bars = []
    for k in range(289):
        stop = len(minutes) - 5 * k
        group = minutes[stop - 5:stop]
        bars.append(Aggregate(group[0].open, max(m.high for m in group), min(m.low for m in group), group[-1].close))
    return tuple(bars)


def _ordered_sum(values: Iterable[float]) -> float:
    total = 0.0
    for value in values:
        total += value
    return total


def _sign(value: float) -> int:
    return (value > 0) - (value < 0)


def _context(bars: tuple[Aggregate, ...]) -> dict[str, object]:
    c = tuple(log(bar.close) for bar in bars)
    r = tuple(c[k] - c[k + 1] for k in range(288))
    # k=0 is newest. Every reduction traverses oldest to newest.
    squares = tuple(value * value for value in r)
    sums = {n: _ordered_sum(squares[k] for k in range(n - 1, -1, -1)) for n in (12, 48, 288)}
    sigmas = {n: sqrt(sums[n] / n) for n in (12, 48, 288)}
    s48, s288 = sigmas[48], sigmas[288]
    if not isfinite(s48) or s48 <= 0 or not isfinite(s288) or s288 <= 0:
        raise FeatureError("INVALID_PREDICTOR_SCALE")
    moments = {n: (c[0] - c[n]) / (s48 * sqrt(n)) for n in (1, 3, 6, 12, 24, 48)}
    if not all(isfinite(x) for x in moments.values()):
        raise FeatureError("NUMERICAL_FEATURE_ERROR")
    return {"bars": bars, "c": c, "r": r, "s": sigmas, "sum_sq": sums, "sq": squares, "m": moments}


def _local(ctx: dict[str, object]) -> list[float]:
    bars, c, r, s, sums, squares, m = (ctx[key] for key in ("bars", "c", "r", "s", "sum_sq", "sq", "m"))
    bar = bars[0]
    log_o, log_h, log_l = log(bar.open), log(bar.high), log(bar.low)
    if bar.high == bar.low:
        range_5, close_location, flat = 0.0, 0.0, 1.0
    else:
        log_range = log_h - log_l
        if not isfinite(log_range) or log_range <= 0:
            raise FeatureError("NUMERICAL_FEATURE_ERROR")
        range_5 = log1p(log_range / s[48])
        close_location = ((c[0] - log_l) - (log_h - c[0])) / log_range
        flat = 0.0
    out = [asinh(m[n]) for n in (1, 3, 6, 12, 24, 48)]
    out.extend((abs(out[3]), abs(out[5])))
    out.extend((_ordered_sum(_sign(r[k]) for k in range(n - 1, -1, -1)) / n for n in (12, 48)))
    out.append(_ordered_sum(1 if _sign(r[k]) * _sign(r[k + 1]) < 0 else 0 for k in range(10, -1, -1)) / 11)
    out.extend((asinh((c[0] - log_o) / s[48]), range_5, close_location, flat))
    for n in (12, 48):
        denom = s[48] * sqrt(n)
        out.extend((asinh((max(c[:n + 1]) - c[0]) / denom), asinh((c[0] - min(c[:n + 1])) / denom)))
    out.extend((log(s[48]), s[12] / s[48], s[48] / s[288], max(squares[:48]) / sums[48]))
    return out


def compute_features(snapshot: OriginSnapshot) -> FeatureResult:
    try:
        local = _context(aggregates(snapshot.local_minutes))
        values = _local(local)
        if snapshot.physical_symbol == "BTCUSDT":
            values.extend((0.0,) * 7)
        else:
            btc = _context(aggregates(snapshot.btc_minutes))
            lm, bm, bs = local["m"], btc["m"], btc["s"]
            values.extend((
                asinh(bm[12]), asinh(bm[48]), bs[12] / bs[48], bs[48] / bs[288],
                asinh(lm[12] - bm[12]), asinh(lm[48] - bm[48]), tanh(lm[12]) * tanh(bm[12]),
            ))
        t = snapshot.prediction_origin
        seconds = t.hour * 3600 + t.minute * 60
        values.extend((sin(2 * pi * seconds / 86400), cos(2 * pi * seconds / 86400)))
        values.extend(float(snapshot.physical_symbol == s) for s in ("AVAXUSDT", "SUIUSDT", "1000PEPEUSDT"))
        if len(values) != 35 or not all(isfinite(v) for v in values):
            raise FeatureError("NUMERICAL_FEATURE_ERROR")
        return FeatureResult(RawFeatureRow(snapshot.physical_symbol, t, snapshot.feature_timestamp, snapshot.source_snapshot_id, tuple(values)), ())
    except (OverflowError, ValueError, ZeroDivisionError) as exc:
        reason = exc.reason if isinstance(exc, FeatureError) else "NUMERICAL_FEATURE_ERROR"
        return FeatureResult(None, (reason,))


def build_feature_row(physical: str, origin: object, rows: Iterable[SourceMinute], *, mode: str, policy=None) -> FeatureResult:
    result: SnapshotResult = build_snapshot(physical, origin, rows, mode=mode, policy=policy)
    if result.snapshot is None:
        return FeatureResult(None, result.reasons)
    return compute_features(result.snapshot)


def build_feature_rows(requests: Iterable[tuple[str, object]], rows: Iterable[SourceMinute], *, mode: str, policy=None) -> tuple[FeatureResult, ...]:
    frozen_rows = tuple(rows)
    return tuple(build_feature_row(symbol, origin, frozen_rows, mode=mode, policy=policy) for symbol, origin in requests)
