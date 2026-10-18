"""Frozen origin-T selection of exact source-minute versions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
import json
from typing import Iterable, Mapping

from .source import MINUTE, SYMBOLS, SourceMinute, physical_symbol, utc

SUPPORT_MINUTES = 1445
EVENT_TIME_ONLY = "EVENT_TIME_ONLY"
ASOF_VERIFIED = "ASOF_VERIFIED"
REASON_ORDER = (
    "UNSUPPORTED_SYMBOL", "INVALID_ORIGIN", "SOURCE_VERSION_CONFLICT",
    "MISSING_REQUIRED_MINUTE", "INVALID_REQUIRED_OHLC", "INCOMPLETE_FINALIZATION",
    "UNVERIFIED_AVAILABILITY", "DATA_LATE", "INVALID_PREDICTOR_SCALE",
    "NUMERICAL_FEATURE_ERROR",
)


@dataclass(frozen=True)
class SupersessionPolicy:
    """Authenticated provider precedence supplied by an upstream adapter.

    Missing policy means conflicting versions fail closed. Ranks are never
    derived from row receipt or iterable order.
    """

    policy_id: str
    rank_by_version: Mapping[str, int]


@dataclass(frozen=True)
class OriginSnapshot:
    physical_symbol: str
    prediction_origin: datetime
    feature_timestamp: datetime
    information_cutoff: datetime
    provenance_mode: str
    local_minutes: tuple[SourceMinute, ...]
    btc_minutes: tuple[SourceMinute, ...]
    source_snapshot_id: str


@dataclass(frozen=True)
class SnapshotResult:
    snapshot: OriginSnapshot | None
    reasons: tuple[str, ...]


def _select(rows: list[SourceMinute], mode: str, cutoff: datetime, policy: SupersessionPolicy | None) -> tuple[SourceMinute | None, set[str]]:
    reasons: set[str] = set()
    if not rows:
        return None, {"MISSING_REQUIRED_MINUTE"}
    candidates: list[SourceMinute] = []
    for row in rows:
        if not row.completed:
            reasons.add("INCOMPLETE_FINALIZATION")
            continue
        if mode == ASOF_VERIFIED:
            available = row.source_available_at
            if available is None:
                reasons.add("UNVERIFIED_AVAILABILITY")
                continue
            if available > cutoff:
                reasons.add("DATA_LATE")
                continue
        candidates.append(row)
    if not candidates:
        return None, reasons
    # Exact retransmissions are harmless; same version with different content is not.
    unique: dict[str, SourceMinute] = {}
    for row in candidates:
        previous = unique.get(row.version_id)
        if previous is not None and previous != row:
            return None, {"SOURCE_VERSION_CONFLICT"}
        unique[row.version_id] = row
    if len(unique) > 1:
        if policy is None or not policy.policy_id or any(v not in policy.rank_by_version for v in unique):
            return None, {"SOURCE_VERSION_CONFLICT"}
        highest = max(policy.rank_by_version[v] for v in unique)
        winners = [r for v, r in unique.items() if policy.rank_by_version[v] == highest]
        if len(winners) != 1:
            return None, {"SOURCE_VERSION_CONFLICT"}
        selected = winners[0]
    else:
        selected = next(iter(unique.values()))
    if not selected.valid_ohlc:
        return None, {"INVALID_REQUIRED_OHLC"}
    return selected, set()


def build_snapshot(
    physical: str, origin: datetime, rows: Iterable[SourceMinute], *,
    mode: str, policy: SupersessionPolicy | None = None,
) -> SnapshotResult:
    """Select exactly 1,445 local minutes and (for altcoins) BTC minutes.

    All selected values are copied into immutable tuples. Caller data added or
    revised later cannot change a returned snapshot.
    """
    reasons: set[str] = set()
    symbol = physical_symbol(physical)
    if symbol not in SYMBOLS:
        reasons.add("UNSUPPORTED_SYMBOL")
    try:
        origin = utc(origin)
        if origin.second or origin.microsecond or origin.minute % 5:
            reasons.add("INVALID_ORIGIN")
    except (ValueError, AttributeError, TypeError):
        reasons.add("INVALID_ORIGIN")
    if mode not in (EVENT_TIME_ONLY, ASOF_VERIFIED):
        raise ValueError("unknown provenance mode")
    if reasons:
        return SnapshotResult(None, tuple(r for r in REASON_ORDER if r in reasons))
    u = origin - MINUTE
    first = u - SUPPORT_MINUTES * MINUTE
    required_symbols = (symbol,) if symbol == "BTCUSDT" else (symbol, "BTCUSDT")
    indexed: dict[tuple[str, datetime], list[SourceMinute]] = {}
    for row in rows:
        if row.physical_symbol not in required_symbols or not first <= row.interval_start < u:
            continue
        indexed.setdefault((row.physical_symbol, row.interval_start), []).append(row)
    selected: dict[str, tuple[SourceMinute, ...]] = {}
    for needed in required_symbols:
        minutes: list[SourceMinute] = []
        for i in range(SUPPORT_MINUTES):
            start = first + i * MINUTE
            interval_rows = indexed.get((needed, start), [])
            exact = [r for r in interval_rows if r.interval_end == start + MINUTE]
            if interval_rows and not exact:
                reasons.add("MISSING_REQUIRED_MINUTE")
            minute, minute_reasons = _select(exact, mode, origin, policy)
            reasons.update(minute_reasons)
            if minute is not None:
                minutes.append(minute)
        selected[needed] = tuple(minutes)
    if reasons:
        return SnapshotResult(None, tuple(r for r in REASON_ORDER if r in reasons))
    local = selected[symbol]
    btc = local if symbol == "BTCUSDT" else selected["BTCUSDT"]
    identity = [
        (r.physical_symbol, r.interval_start.isoformat(), r.version_id, r.open, r.high, r.low, r.close,
         r.collector_received_at.isoformat() if r.collector_received_at else None, r.collector_receipt_ref,
         tuple(t.isoformat() for t in r.evidence_available_at), r.evidence_refs,
         r.availability_contract_id, r.completion_contract_id, r.source_ref)
        for group in (local,) if group
        for r in group
    ]
    if symbol != "BTCUSDT":
        identity.extend(
            (r.physical_symbol, r.interval_start.isoformat(), r.version_id, r.open, r.high, r.low, r.close,
             r.collector_received_at.isoformat() if r.collector_received_at else None, r.collector_receipt_ref,
             tuple(t.isoformat() for t in r.evidence_available_at), r.evidence_refs,
             r.availability_contract_id, r.completion_contract_id, r.source_ref)
            for r in btc
        )
    digest = sha256(json.dumps((mode, origin.isoformat(), policy.policy_id if policy else None, identity),
                               separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return SnapshotResult(OriginSnapshot(symbol, origin, u, origin, mode, local, btc, digest), ())
