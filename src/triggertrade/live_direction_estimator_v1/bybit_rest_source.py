"""Bounded adapter for captured Bybit linear REST kline responses.

The repository's runtime calls a 1m candle completed when its interval has
ended according to the local clock and a preceding candle is present. The
REST response has no final flag, version sequence, or correction authority.
This module does not collect messages or infer receipt times.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import InvalidOperation
from hashlib import sha256
import json

from triggertrade.market_data.bybit import parse_spot_candles

from .prospective_source import AvailabilityEvidence, ProspectiveSourceVersion, build_prospective_snapshot
from .snapshot import SnapshotResult
from .source import MINUTE, SYMBOLS, utc


PROVIDER_ID = "bybit_v5_linear_rest"
STREAM_ID = "/v5/market/kline|category=linear|interval=1"
FINALIZATION_CONTRACT_ID = "triggertrade_bybit_rest_1m_local_clock_completion_v1"
CLOCK_VERIFIED = "VERIFIED"
CLOCK_UNAVAILABLE = "UNAVAILABLE"


class BybitRestSourceError(ValueError):
    """A captured response cannot be represented faithfully."""


@dataclass(frozen=True)
class CollectorClockEvidence:
    """Receipt-specific external UTC bound; no current runtime emits one."""

    reference: str
    receipt_ref: str
    verified_at: datetime
    maximum_error: timedelta

    def __post_init__(self) -> None:
        object.__setattr__(self, "verified_at", utc(self.verified_at))
        if not self.reference or not self.receipt_ref or self.maximum_error < timedelta(0):
            raise ValueError("clock evidence needs reference, receipt and nonnegative error bound")


@dataclass(frozen=True)
class BybitRestCapture:
    raw_response: bytes
    physical_symbol: str
    collector_received_at: datetime | None
    collector_receipt_ref: str | None
    clock_evidence: CollectorClockEvidence | None = None


@dataclass(frozen=True)
class AdaptedBybitRestCapture:
    versions: tuple[ProspectiveSourceVersion, ...]
    raw_payload_sha256: str
    receipt_status: str
    clock_status: str
    captured_received_at: datetime | None
    clock_evidence_ref: str | None


def adapt_bybit_linear_rest_capture(capture: BybitRestCapture) -> AdaptedBybitRestCapture:
    """Adapt exact retained response bytes; caller must capture receipt at IO time.

    The runtime completion rule is represented as evidence only if a separate
    collector-clock attestation covers the actual receipt timestamp. A replay
    cannot substitute its own clock. No supersession policy is produced.
    """
    if capture.physical_symbol not in SYMBOLS:
        raise BybitRestSourceError("unsupported physical symbol")
    if not capture.raw_response:
        raise BybitRestSourceError("raw response bytes required")
    digest = sha256(capture.raw_response).hexdigest()
    try:
        payload = json.loads(capture.raw_response.decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("retCode") != 0:
            raise ValueError("Bybit response is not successful")
        result = payload["result"]
        if result.get("category") != "linear" or result.get("symbol") != capture.physical_symbol:
            raise ValueError("response category/symbol mismatch")
        raw_rows = result["list"]
        if not isinstance(raw_rows, list):
            raise ValueError("kline list required")
        candles = parse_spot_candles(result)
        if len(candles) != len(raw_rows):
            raise ValueError("kline parse mismatch")
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError,
            IndexError, InvalidOperation) as exc:
        raise BybitRestSourceError("invalid captured Bybit kline response") from exc

    received = capture.collector_received_at
    if received is None:
        receipt_status = "MISSING"
    else:
        try:
            received = utc(received)
        except ValueError:
            received = None
            receipt_status = "INVALID_NON_UTC"
        else:
            receipt_status = "VALID" if capture.collector_receipt_ref else "MISSING_REFERENCE"
    clock_ok = (received is not None and capture.clock_evidence is not None and
                capture.clock_evidence.receipt_ref == capture.collector_receipt_ref and
                capture.clock_evidence.verified_at == received and
                bool(capture.collector_receipt_ref))
    clock_status = CLOCK_VERIFIED if clock_ok else CLOCK_UNAVAILABLE
    # This is the repository runtime's predecessor plus elapsed-interval rule.
    starts = {candle.start_time_ms for candle in candles}
    if len(starts) != len(candles):
        raise BybitRestSourceError("duplicate interval in captured response")
    versions = []
    for candle, raw_row in zip(candles, raw_rows, strict=True):
        start_ms = candle.start_time_ms
        if start_ms % 60_000:
            raise BybitRestSourceError("unaligned one-minute interval")
        try:
            start = datetime.fromtimestamp(start_ms / 1000, tz=UTC)
        except (OverflowError, OSError, ValueError) as exc:
            raise BybitRestSourceError("invalid kline start timestamp") from exc
        end = start + MINUTE
        # The Bybit REST row has no provider version ID. Content identity
        # distinguishes retained OHLC revisions without ordering them.
        material = [str(item) for item in raw_row]
        row_digest = sha256(json.dumps(material, separators=(",", ":")).encode()).hexdigest()
        error = capture.clock_evidence.maximum_error if clock_ok else timedelta(0)
        completed = bool(clock_ok and end <= received - error and start_ms - 60_000 in starts)
        evidence = ((
            AvailabilityEvidence("FINALIZATION", f"{FINALIZATION_CONTRACT_ID}:{digest}:{start_ms}", received),
            # A conservative upper bound proves by-T eligibility when nonzero
            # clock uncertainty exists. It is retained separately in audit.
            AvailabilityEvidence("CLOCK_CUTOFF_BOUND", capture.clock_evidence.reference, received + error),
        ) if completed else ())
        versions.append(ProspectiveSourceVersion(
            physical_symbol=capture.physical_symbol, interval_start=start, interval_end=end,
            open=float(candle.open), high=float(candle.high), low=float(candle.low), close=float(candle.close),
            provider_id=PROVIDER_ID, source_stream_id=STREAM_ID, provider_version_id=row_digest,
            completed=completed, collector_received_at=received if clock_ok else None,
            collector_receipt_ref=capture.collector_receipt_ref if clock_ok else None,
            evidence=evidence, required_evidence_kinds=("FINALIZATION", "CLOCK_CUTOFF_BOUND"),
            availability_contract_id=FINALIZATION_CONTRACT_ID,
            raw_payload_ref=f"{capture.collector_receipt_ref}:{start_ms}" if capture.collector_receipt_ref else None,
            raw_payload_sha256=digest,
            collector_clock_evidence_ref=capture.clock_evidence.reference if clock_ok else None,
        ))
    return AdaptedBybitRestCapture(tuple(versions), digest, receipt_status, clock_status,
                                   capture.collector_received_at,
                                   capture.clock_evidence.reference if capture.clock_evidence else None)


def build_bybit_rest_snapshot(physical_symbol: str, origin: datetime,
                              captures: tuple[AdaptedBybitRestCapture, ...]) -> SnapshotResult:
    """Collapse identical REST retransmissions, then use Phase 2 selection.

    Earlier *evidence* for the same content is retained. Different content
    versions remain separate and conflict without provider precedence.
    """
    unique: dict[str, ProspectiveSourceVersion] = {}
    for capture in captures:
        for version in capture.versions:
            key = version.canonical_version_id
            previous = unique.get(key)
            if previous is None:
                unique[key] = version
            elif (previous.physical_symbol != version.physical_symbol or
                  previous.interval_start != version.interval_start or
                  (previous.open, previous.high, previous.low, previous.close) !=
                  (version.open, version.high, version.low, version.close)):
                raise BybitRestSourceError("content identity collision")
            elif _retransmission_key(version) < _retransmission_key(previous):
                unique[key] = version
    return build_prospective_snapshot(physical_symbol, origin, unique.values())


def _retransmission_key(version: ProspectiveSourceVersion) -> tuple[str, str, str]:
    # Only identical content reaches this comparison. This chooses stable
    # evidence, not authority to supersede a different source version.
    return (version.source_available_at.isoformat() if version.source_available_at else "9999",
            version.collector_receipt_ref or "", version.raw_payload_sha256 or "")
