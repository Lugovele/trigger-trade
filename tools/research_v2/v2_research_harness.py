"""Dormant LABEL_PROTOCOL_V2 research evaluator. No defaults or canonical output."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from statistics import median
from typing import Mapping, Sequence

TAU = 1e-12
HORIZONS = (60, 120)
FAILURES = ("INSUFFICIENT_NET_BOUNDED_EXPOSURE", "NONPOSITIVE_SIGNED_AREA",
            "NO_MATERIAL_ESTABLISHMENT", "MATERIAL_OPPOSING_PHASE",
            "NONPOSITIVE_REMAINDER", "INSUFFICIENT_RETAINED_ADVANTAGE")


def _ceil(x: Fraction) -> int:
    return -(-x.numerator // x.denominator)


def _parameter(name: str, value: object) -> tuple[str, Fraction, float]:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"INVALID_CONFIG: {name} requires an exact decimal string")
    try:
        d = Decimal(value)
        if not d.is_finite():
            raise ValueError()
        fraction = Fraction(d)
        binary = float(d)
    except (InvalidOperation, ValueError, OverflowError) as error:
        raise ValueError(f"INVALID_CONFIG: {name}") from error
    if not math.isfinite(binary) or binary <= 0 or fraction <= 0:
        raise ValueError(f"INVALID_CONFIG: {name} must be finite positive")
    return value, fraction, binary


@dataclass(frozen=True)
class ResearchConfig:
    exact: Mapping[str, str]
    rational: Mapping[str, Fraction]
    binary64: Mapping[str, float]
    config_hash: str

    @classmethod
    def from_explicit(cls, supplied: Mapping[str, object]) -> "ResearchConfig":
        if set(supplied) != {"a", "beta", "rho", "eta"}:
            raise ValueError("INVALID_CONFIG: exactly a, beta, rho, eta are mandatory")
        parsed = {name: _parameter(name, supplied[name]) for name in ("a", "beta", "rho", "eta")}
        exact = {k: v[0] for k, v in parsed.items()}
        rational = {k: v[1] for k, v in parsed.items()}
        binary = {k: v[2] for k, v in parsed.items()}
        if not (rational["beta"] < 1 and rational["rho"] < Fraction(1, 2) and rational["eta"] <= 1):
            raise ValueError("INVALID_CONFIG: domain")
        if not (binary["beta"] < 1 and binary["rho"] < .5 and binary["eta"] <= 1):
            raise ValueError("INVALID_CONFIG: binary64 domain")
        if (rational["beta"] <= Fraction(2, 10**12) or rational["eta"] <= Fraction(2, 10**12)
                or binary["beta"] <= 2*TAU or binary["eta"] <= 2*TAU):
            raise ValueError("INVALID_CONFIG: beta/eta numerical separation")
        result = cls(exact, rational, binary,
                     hashlib.sha256(json.dumps(exact, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest())
        for n in HORIZONS:
            result.counts(n, canonical=True)
        return result

    def counts(self, n: int, *, canonical: bool = False) -> tuple[int, int, int]:
        p = max(2, _ceil(self.rational["rho"] * n))
        w = 2*p-1
        lmin = max(p, _ceil(self.rational["beta"] * n))
        if w > n or (canonical and lmin >= Fraction(n, 2)):
            raise ValueError(f"INVALID_CONFIG: inadmissible N={n}")
        return p, w, lmin

    @classmethod
    def from_rho_probe(cls, registered: "ResearchConfig", numerator: str, denominator: str) -> "ResearchConfig":
        """Exact rational rho is allowed only for a tagged sensitivity probe."""
        if not (isinstance(numerator, str) and numerator.isdigit() and
                isinstance(denominator, str) and denominator.isdigit()):
            raise ValueError("INVALID_CONFIG: rho probe needs integer strings")
        rho = Fraction(int(numerator), int(denominator)) if int(denominator) else Fraction(0)
        if rho <= 0 or rho >= Fraction(1, 2):
            raise ValueError("INVALID_CONFIG: rho probe domain")
        binary = float(rho)
        if not math.isfinite(binary) or binary <= 0 or binary >= .5:
            raise ValueError("INVALID_CONFIG: binary64 rho probe")
        identity = dict(registered.exact)
        identity["rho"] = {"numerator": str(rho.numerator), "denominator": str(rho.denominator)}
        digest = hashlib.sha256(json.dumps(identity, separators=(",", ":"), sort_keys=True).encode()).hexdigest()
        config = cls(identity, {**registered.rational, "rho": rho},
                     {**registered.binary64, "rho": binary}, digest)
        for n in (55, 60, 65, 115, 120, 125):
            config.counts(n, canonical=n in HORIZONS)
        return config


def _ge(x: float, limit: float) -> bool:
    return x >= limit - TAU


def _side(y: Sequence[float], z: Sequence[float], n: int, p: int, w: int,
          beta: float, eta: float, q: int, j_long: float, m_long: float) -> dict:
    oriented = [q * value for value in y]
    medians = [(end, float(median(oriented[end-w:end]))) for end in range(w, n+1)]
    confirmations = [end for end, value in medians if _ge(value, 1)]
    b = max(0.0, *(value for _, value in medians))
    s = medians[-1][1]
    e = oriented[-1]
    remainder = min(s, e)
    required = min(eta*b, 1.0)
    hit = next((i for i, value in enumerate(oriented, 1) if _ge(value, 1)), None)
    confirm = confirmations[0] if confirmations else None
    support = (next(i for i in range(confirm-w+1, confirm+1) if _ge(oriented[i-1], 1))
               if confirm else None)
    j = q*j_long
    m = q*m_long
    area_pos = sum(max(q*value, 0.0) for value in z)
    area_neg = sum(max(-q*value, 0.0) for value in z)
    return {"J": j, "M": m, "B": b, "S": s, "E": e, "R": remainder,
            "required_retention": required, "retained_fraction": remainder/b if b > 0 else None,
            "giveback": max(0.0, b-remainder),
            "raw_occupancy": sum(value > 0 for value in oriented)/n,
            "material_occupancy": sum(_ge(value, 1) for value in oriented)/n,
            "signed_area_positive": area_pos, "signed_area_negative": area_neg,
            "first_material_minute": hit, "first_confirmation_minute": confirm,
            "first_supporting_minute": support,
            "minutes_from_support": n-support+1 if support else None,
            "minutes_after_confirmation": n-confirm if confirm else None,
            "material_minutes_after_support": sum(_ge(value, 1) for value in oriented[support-1:]) if support else None,
            "phase_confirmation_minutes": confirmations,
            "full_endpoint_giveback": _ge(b, 1) and e <= 0,
            "internal_return": bool(confirm and any(value <= 0 for value in oriented[confirm:])),
            "reestablishment_after_return": any(e1 < k < e2 and oriented[k-1] <= 0
                for e1 in confirmations for e2 in confirmations for k in range(e1+1, e2)),
            "close_favorable_max": max(0.0, *(q*value for value in z)),
            "close_adverse_max": max(0.0, *(-q*value for value in z))}


def evaluate_path(z: Sequence[float], config: ResearchConfig, *, horizon: int,
                  high_z: Sequence[float] | None = None, low_z: Sequence[float] | None = None,
                  origin_utc: str | None = None) -> dict:
    if len(z) != horizon or not all(math.isfinite(x) for x in z):
        return {"status": "UNAVAILABLE", "availability_reasons": ["INCOMPLETE_FUTURE"], "candidate_label": None}
    if (high_z is None) != (low_z is None):
        return {"status": "UNAVAILABLE", "availability_reasons": ["INCOMPLETE_FUTURE"], "candidate_label": None}
    if high_z is not None and (len(high_z) != horizon or len(low_z) != horizon or
            any(not all(map(math.isfinite, (hi, lo, close))) or lo > close or hi < close or lo > hi
                for hi, lo, close in zip(high_z, low_z, z))):
        return {"status": "UNAVAILABLE", "availability_reasons": ["INVALID_FUTURE_OHLC"], "candidate_label": None}
    p, w, lmin = config.counts(horizon, canonical=horizon in HORIZONS)
    a, beta, eta = (config.binary64[k] for k in ("a", "beta", "eta"))
    y = [float(value)/a for value in z]
    if not all(math.isfinite(value) for value in y):
        return {"status": "NUMERICAL_ERROR", "availability_reasons": ["NUMERICAL_ERROR"], "candidate_label": None}
    j_total = 0.0
    m_total = 0.0
    for yi, zi in zip(y, z):
        j_total += min(1.0, max(-1.0, yi))
        m_total += zi
    j_long = j_total/horizon
    m_long = m_total/horizon
    sides = {name: _side(y, z, horizon, p, w, beta, eta, q, j_long, m_long)
             for name, q in (("LONG", 1), ("SHORT", -1))}
    for side in sides.values():
        if any(not math.isfinite(side[key]) for key in ("J", "M", "B", "S", "E", "R",
                "required_retention", "signed_area_positive", "signed_area_negative")):
            return {"status": "NUMERICAL_ERROR", "availability_reasons": ["NUMERICAL_ERROR"], "candidate_label": None}
    sequence = []
    for end in range(w, horizon+1):
        plus = float(median(y[end-w:end]))
        minus = float(median([-v for v in y[end-w:end]]))
        state = "LONG" if _ge(plus, 1) else "SHORT" if _ge(minus, 1) else None
        if state and (not sequence or sequence[-1]["side"] != state):
            sequence.append({"side": state, "first_confirmation_minute": end})
    for name, opposite in (("LONG", "SHORT"), ("SHORT", "LONG")):
        side = sides[name]
        opp = sides[opposite]
        predicates = [_ge(side["J"], beta), side["M"] > 0, _ge(side["B"], 1),
                      not _ge(opp["B"], 1), side["R"] > 0,
                      _ge(side["R"], side["required_retention"])]
        margins = [side["J"]-beta, side["M"], side["B"]-1, 1-opp["B"],
                   side["R"], side["R"]-side["required_retention"]]
        side["opposing_phase"] = _ge(opp["B"], 1)
        side["predicates"] = dict(zip(FAILURES, predicates))
        side["failed_conditions"] = [key for key, passes in zip(FAILURES, predicates) if not passes]
        side["nominal_margins"] = dict(zip(FAILURES, margins))
        side["comparison_types"] = ["GE_TAU", "GT_ZERO", "GE_TAU", "NOT_GE_TAU", "GT_ZERO", "GE_TAU"]
        side["passes"] = all(predicates)
        side["retention_failure"] = _ge(side["B"], 1) and (side["R"] <= 0 or not predicates[5])
        if high_z is not None and low_z is not None:
            side["hl_favorable_max"] = max(0.0, *(high_z if name == "LONG" else [-x for x in low_z]))
            side["hl_adverse_max"] = max(0.0, *([-x for x in low_z] if name == "LONG" else high_z))
        if origin_utc is not None:
            origin = datetime.strptime(origin_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            for index_field, utc_field in (("first_material_minute", "first_material_utc"),
                                           ("first_confirmation_minute", "first_confirmation_utc"),
                                           ("first_supporting_minute", "first_supporting_utc")):
                minute = side[index_field]
                side[utc_field] = (origin+timedelta(minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ") if minute else None
    if sides["LONG"]["passes"] and sides["SHORT"]["passes"]:
        return {"status": "NUMERICAL_ERROR", "availability_reasons": ["IMPLEMENTATION_ERROR"], "candidate_label": None}
    label = "LONG_FAVORED" if sides["LONG"]["passes"] else "SHORT_FAVORED" if sides["SHORT"]["passes"] else "NO_DIRECTION"
    return {"status": "RESEARCH_CANDIDATE", "configuration_hash": config.config_hash,
            "exact_parameters": dict(config.exact), "horizon_minutes": horizon,
            "p_N": p, "w_N": w, "L_min_nominal": lmin,
            "candidate_label": label, "availability_reasons": [], "sides": sides,
            "phase_sequence": sequence, "supported_side_change": bool(
                sides["LONG"]["phase_confirmation_minutes"] and
                sides["SHORT"]["phase_confirmation_minutes"])}


def evaluate_pair(z60: Sequence[float], z120: Sequence[float], config: ResearchConfig) -> dict:
    """Independent candidate horizons and nullable pair relation; never canonical."""
    first = evaluate_path(z60, config, horizon=60)
    second = evaluate_path(z120, config, horizon=120)
    a, b = first["candidate_label"], second["candidate_label"]
    if a is None or b is None:
        relation = "UNAVAILABLE"
    elif a == b == "NO_DIRECTION":
        relation = "BOTH_NO_DIRECTION"
    elif a == b:
        relation = "SAME_DIRECTION"
    elif "NO_DIRECTION" in (a, b):
        relation = "DIRECTION_VS_NO_DIRECTION"
    else:
        relation = "OPPOSITE_DIRECTIONS"
    return {"status": "RESEARCH_CANDIDATE", "configuration_hash": config.config_hash,
            "horizon_60m": first, "horizon_120m": second, "pair_relation": relation,
            "canonical_label": None}


def evaluate_from_minute_arrays(closes: Sequence[float], origin_close_index: int,
                                config: ResearchConfig, horizon: int,
                                *, highs: Sequence[float] | None = None,
                                lows: Sequence[float] | None = None,
                                origin_utc: str | None = None) -> dict:
    """Recompute geometry from PREVALIDATED contiguous minute arrays only."""
    if origin_close_index % 5 != 4 or origin_close_index < 244:
        return {"status": "UNAVAILABLE", "availability_reasons": ["INVALID_TIMESTAMP" if origin_close_index % 5 != 4 else "INCOMPLETE_OR_INVALID_PAST"], "candidate_label": None}
    if origin_close_index+horizon >= len(closes):
        return {"status": "UNAVAILABLE", "availability_reasons": ["INCOMPLETE_FUTURE"], "candidate_label": None}
    required = closes[origin_close_index-240:origin_close_index+horizon+1]
    if not all(math.isfinite(x) and x > 0 for x in required):
        return {"status": "UNAVAILABLE", "availability_reasons": ["INVALID_REFERENCE"], "candidate_label": None}
    historical = [math.log(closes[k]) for k in range(origin_close_index-240, origin_close_index+1, 5)]
    total = 0.0
    for k in range(1, 49):
        r = historical[k]-historical[k-1]
        total += r*r
    v = math.sqrt(total/48)
    if not math.isfinite(v) or v <= 0:
        return {"status": "UNAVAILABLE", "availability_reasons": ["INVALID_SCALE"], "candidate_label": None}
    s = v*math.sqrt(horizon/5)
    anchor = math.log(closes[origin_close_index])
    z = [(math.log(closes[origin_close_index+j])-anchor)/s for j in range(1,horizon+1)]
    hz = [(math.log(highs[origin_close_index+j])-anchor)/s for j in range(1,horizon+1)] if highs is not None else None
    lz = [(math.log(lows[origin_close_index+j])-anchor)/s for j in range(1,horizon+1)] if lows is not None else None
    result = evaluate_path(z, config, horizon=horizon, high_z=hz, low_z=lz, origin_utc=origin_utc)
    result["rms48"] = v
    result["s_h"] = s
    result["p0"] = closes[origin_close_index]
    result["input_contract"] = "PREVALIDATED_CONTIGUOUS_MINUTE_ARRAYS"
    return result


def evaluate_from_candles(candles: Sequence[Mapping], origin_close_index: int,
                          config: ResearchConfig, horizon: int, *, dataset_id: str) -> dict:
    """Validate full required 1m OHLC/completion before a research evaluation.

    Each candle has integer open_time_s, physical_symbol, completed, open,
    high, low, close. The caller supplies a declared dataset_id.
    """
    if origin_close_index % 5 != 4 or origin_close_index < 244 or origin_close_index+horizon >= len(candles):
        reason = "INVALID_TIMESTAMP" if origin_close_index % 5 != 4 else "INCOMPLETE_OR_INVALID_PAST" if origin_close_index < 244 else "INCOMPLETE_FUTURE"
        return {"status": "UNAVAILABLE", "availability_reasons": [reason], "candidate_label": None}
    needed = candles[origin_close_index-244:origin_close_index+horizon+1]
    symbols = {row.get("physical_symbol") for row in needed}
    if len(symbols) != 1 or None in symbols or next(iter(symbols)) not in {"BTCUSDT", "AVAXUSDT", "SUIUSDT", "1000PEPEUSDT"}:
        return {"status": "UNAVAILABLE", "availability_reasons": ["UNSUPPORTED_SYMBOL"], "candidate_label": None}
    seen = set()
    previous = None
    for position, row in enumerate(needed):
        stamp = row.get("open_time_s")
        if not isinstance(stamp, int) or stamp % 60:
            return {"status": "UNAVAILABLE", "availability_reasons": ["INVALID_TIMESTAMP"], "candidate_label": None}
        if stamp in seen:
            return {"status": "UNAVAILABLE", "availability_reasons": ["DUPLICATE_REQUIRED_TIMESTAMP"], "candidate_label": None}
        seen.add(stamp)
        if previous is not None and stamp != previous+60:
            reason = "INCOMPLETE_OR_INVALID_PAST" if position <= 244 else "INCOMPLETE_FUTURE"
            return {"status": "UNAVAILABLE", "availability_reasons": [reason], "candidate_label": None}
        previous = stamp
        prices = [row.get(k) for k in ("open", "high", "low", "close")]
        if row.get("completed") is not True or any(not isinstance(x, (int,float)) or not math.isfinite(x) or x <= 0 for x in prices):
            reason = "INCOMPLETE_OR_INVALID_PAST" if position <= 244 else "INVALID_FUTURE_OHLC"
            return {"status": "UNAVAILABLE", "availability_reasons": [reason], "candidate_label": None}
        o, h, l, c = prices
        if not (l <= o <= h and l <= c <= h and l <= h):
            reason = "INCOMPLETE_OR_INVALID_PAST" if position <= 244 else "INVALID_FUTURE_OHLC"
            return {"status": "UNAVAILABLE", "availability_reasons": [reason], "candidate_label": None}
    origin_time = datetime.fromtimestamp(candles[origin_close_index]["open_time_s"]+60, timezone.utc)
    if int(origin_time.timestamp()) % 300:
        return {"status": "UNAVAILABLE", "availability_reasons": ["INVALID_TIMESTAMP"], "candidate_label": None}
    result = evaluate_from_minute_arrays([row["close"] for row in needed], 244,
                                          config, horizon, highs=[row["high"] for row in needed],
                                          lows=[row["low"] for row in needed],
                                          origin_utc=origin_time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    result["input_dataset_id"] = dataset_id
    result["physical_symbol"] = next(iter(symbols))
    result["origin_utc"] = origin_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    result["horizon_end_utc"] = (origin_time+timedelta(minutes=horizon)).strftime("%Y-%m-%dT%H:%M:%SZ")
    result["input_contract"] = "VALIDATED_COMPLETED_1M_OHLC"
    return result


def temporal_probe_at_origin(closes: Sequence[float], origin_close_index: int,
                             config: ResearchConfig) -> dict:
    """Dormant exact origin and horizon-end probe set for an explicit tuple."""
    evaluations = {}
    for shift in (-5, 0, 5):
        for horizon in ((60,120) if shift else (55,60,65,115,120,125)):
            evaluations[f"shift_{shift:+d}_horizon_{horizon}"] = evaluate_from_minute_arrays(
                closes, origin_close_index+shift, config, horizon)
    return {"status": "RESEARCH_CANDIDATE", "configuration_hash": config.config_hash,
            "evaluations": evaluations}


def temporal_probe_from_candles(candles: Sequence[Mapping], origin_close_index: int,
                                config: ResearchConfig, *, dataset_id: str) -> dict:
    """Validated T−5/T/T+5 and H−5/H/H+5 research probes."""
    evaluations = {}
    for shift in (-5, 0, 5):
        horizons = (60, 120) if shift else (55, 60, 65, 115, 120, 125)
        for horizon in horizons:
            evaluations[f"shift_{shift:+d}_horizon_{horizon}"] = evaluate_from_candles(
                candles, origin_close_index+shift, config, horizon, dataset_id=dataset_id)
    return {"status": "RESEARCH_CANDIDATE", "configuration_hash": config.config_hash,
            "evaluations": evaluations}


def parameter_probe_from_candles(candles: Sequence[Mapping], origin_close_index: int,
                                 config: ResearchConfig, *, dataset_id: str) -> dict:
    """Evaluate only predeclared one-at-a-time probes for a registered tuple."""
    evaluations = []
    for plan in sensitivity_plan(config):
        if plan["parameter"] == "rho":
            probed = ResearchConfig.from_rho_probe(config, plan["rho_numerator"], plan["rho_denominator"])
        else:
            probed = ResearchConfig.from_explicit(plan["exact_parameters"])
        evaluations.append({"probe": plan, "horizon_60m": evaluate_from_candles(
            candles, origin_close_index, probed, 60, dataset_id=dataset_id),
            "horizon_120m": evaluate_from_candles(
            candles, origin_close_index, probed, 120, dataset_id=dataset_id)})
    return {"status": "RESEARCH_CANDIDATE", "registered_configuration_hash": config.config_hash,
            "probes": evaluations}


def sensitivity_plan(config: ResearchConfig) -> list[dict]:
    """Declare probes only; do not evaluate corpus or select a winner."""
    plan = []
    for name in ("a", "beta", "eta"):
        for factor in ("0.90", "0.95", "1.05", "1.10"):
            proposal = dict(config.exact)
            proposal[name] = str(Decimal(proposal[name])*Decimal(factor))
            try:
                probed = ResearchConfig.from_explicit(proposal)
            except ValueError:
                continue
            plan.append({"parameter": name, "factor": factor, "configuration_hash": probed.config_hash,
                         "exact_parameters": proposal})
    for n in HORIZONS:
        p, _, _ = config.counts(n)
        for target in (p-1, p+1):
            if target < 2:
                continue
            rho = Fraction(2*target-1, 2*n)
            # Rational probes are research-only and must be validated for every evaluated N.
            counts = [(max(2, _ceil(rho*h)), 2*max(2, _ceil(rho*h))-1) for h in (55,60,65,115,120,125)]
            if rho >= Fraction(1,2) or any(w > h for (p2,w),h in zip(counts,(55,60,65,115,120,125))):
                continue
            if any(max(max(2, _ceil(rho*h)), _ceil(config.rational["beta"]*h)) >= Fraction(h,2)
                   for h in HORIZONS):
                continue
            probe = ResearchConfig.from_rho_probe(config, str(rho.numerator), str(rho.denominator))
            plan.append({"parameter": "rho", "target_horizon": n, "target_p": target,
                         "rho_numerator": str(rho.numerator), "rho_denominator": str(rho.denominator),
                         "configuration_hash": probe.config_hash,
                         "counts_55_60_65_115_120_125": counts})
    unique = {}
    for probe in plan:
        unique.setdefault(probe["configuration_hash"], probe)
    return list(unique.values())


def select_independent_panel(
    eligible_origin_times: Mapping[str, Sequence[str]],
    coverage: Mapping[str, tuple[str, str]],
    diagnostic_origin_times: Sequence[str],
    config: ResearchConfig,
) -> dict:
    """Select one hashed origin per complete symbol/week, using timestamps only.

    Caller must first authenticate validity for 55/60/65/115/120/125 and
    shifted origins. This function never reads labels or answer content.
    """
    for horizon in (55, 60, 65, 115, 120, 125):
        config.counts(horizon)
    parse = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    exclusion = [parse(t) for t in diagnostic_origin_times]
    selected = []
    empty = []
    for symbol, times in eligible_origin_times.items():
        if symbol not in coverage:
            raise ValueError(f"missing coverage for {symbol}")
        first, end = map(parse, coverage[symbol])
        monday = first + timedelta(days=(7-first.weekday()) % 7)
        monday = monday.replace(hour=0, minute=0, second=0)
        if monday < first:
            monday += timedelta(days=7)
        buckets: dict[datetime, list[tuple[str, str]]] = {}
        week = monday
        while week + timedelta(days=7) <= end:
            buckets[week] = []
            week += timedelta(days=7)
        for stamp in times:
            origin = parse(stamp)
            if origin.minute % 5 or origin.second:
                raise ValueError("INVALID_TIMESTAMP")
            week = origin - timedelta(days=origin.weekday(), hours=origin.hour, minutes=origin.minute)
            if week not in buckets or origin-timedelta(minutes=5) < week or origin+timedelta(minutes=125) > week+timedelta(days=7):
                continue
            # Closed dependency intervals overlap when their origin times differ by <=375m.
            if any(abs(origin-other) <= timedelta(minutes=375) for other in exclusion):
                continue
            key = f"LABEL_PROTOCOL_V2_SEMANTIC_VALIDATION_V1|{symbol}|{stamp}"
            buckets[week].append((hashlib.sha256(key.encode("utf-8")).hexdigest(), stamp))
        for week, candidates in buckets.items():
            if not candidates:
                empty.append({"physical_symbol": symbol, "week_start_utc": week.strftime("%Y-%m-%dT%H:%M:%SZ")})
            else:
                hash_value, stamp = min(candidates)
                selected.append({"physical_symbol": symbol, "origin_utc": stamp,
                                 "week_start_utc": week.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                 "selection_sha256": hash_value})
    return {"status": "RESEARCH_PANEL_MANIFEST", "configuration_hash": config.config_hash,
            "coverage": dict(coverage), "selected": selected, "empty_strata": empty,
            "diagnostic_timestamps_used_for_exclusion_only": len(exclusion)}
