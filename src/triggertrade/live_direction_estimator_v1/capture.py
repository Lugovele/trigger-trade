"""Capture-time handoff for public Bybit linear REST kline response bytes.

Imported JSON has no live authority by itself. Only a trusted capture sink can
return the original in-process receipt object after exact identity comparison.
The repository currently has no production UTC synchronization attestor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from hashlib import sha256
import base64
import json
from typing import Callable, Protocol
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from .bybit_rest_source import BybitRestCapture, CollectorClockEvidence, PROVIDER_ID, STREAM_ID
from .source import SYMBOLS, utc


CAPTURED_LIVE = "CAPTURED_LIVE"
REPLAYED_OR_IMPORTED = "REPLAYED_OR_IMPORTED"
_LIVE_TOKEN = object()


class CaptureError(ValueError):
    """A capture or its serialized audit evidence is invalid."""


@dataclass(frozen=True)
class KlineCaptureRecord:
    provider_id: str
    stream_id: str
    physical_symbol: str
    request_parameters: tuple[tuple[str, str], ...]
    request_id: str
    raw_response: bytes
    raw_response_sha256: str
    collector_received_at: datetime | None
    collector_receipt_ref: str | None
    clock_evidence: CollectorClockEvidence | None
    receipt_status: str
    clock_status: str
    provenance_mode: str
    _live_token: object | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.raw_response, bytes) or not self.raw_response:
            raise CaptureError("missing raw response bytes")
        if sha256(self.raw_response).hexdigest() != self.raw_response_sha256:
            raise CaptureError("raw payload SHA-256 mismatch")
        if self.provenance_mode == CAPTURED_LIVE and self._live_token is not _LIVE_TOKEN:
            raise CaptureError("live capture authority cannot be imported or constructed")

    def to_bybit_rest_capture(self) -> BybitRestCapture:
        valid = (self.provenance_mode == CAPTURED_LIVE and self._live_token is _LIVE_TOKEN and
                 self.receipt_status == "VALID")
        return BybitRestCapture(
            self.raw_response, self.physical_symbol,
            self.collector_received_at if valid else None,
            self.collector_receipt_ref if valid else None,
            self.clock_evidence if valid and self.clock_status == "VERIFIED" else None,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id, "stream_id": self.stream_id,
            "physical_symbol": self.physical_symbol,
            "request_parameters": [list(pair) for pair in self.request_parameters],
            "request_id": self.request_id,
            "raw_response_base64": base64.b64encode(self.raw_response).decode("ascii"),
            "raw_response_sha256": self.raw_response_sha256,
            "collector_received_at": self.collector_received_at.isoformat() if self.collector_received_at else None,
            "collector_receipt_ref": self.collector_receipt_ref,
            "clock_evidence": None if self.clock_evidence is None else {
                "reference": self.clock_evidence.reference,
                "receipt_ref": self.clock_evidence.receipt_ref,
                "verified_at": self.clock_evidence.verified_at.isoformat(),
                "maximum_error_microseconds": self.clock_evidence.maximum_error // timedelta(microseconds=1),
            },
            "receipt_status": self.receipt_status, "clock_status": self.clock_status,
            "provenance_mode": self.provenance_mode,
        }


class CaptureSink(Protocol):
    """Append-only handoff; production deployment must supply durable storage."""

    def append(self, record: KlineCaptureRecord) -> None: ...
    def authenticated_record(self, receipt_ref: str) -> KlineCaptureRecord | None: ...


class MemoryCaptureSink:
    """Bounded fixture sink; live deployment needs an immutable durable sink."""

    def __init__(self) -> None:
        self._records: dict[str, KlineCaptureRecord] = {}

    def append(self, record: KlineCaptureRecord) -> None:
        if record.provenance_mode != CAPTURED_LIVE or record._live_token is not _LIVE_TOKEN:
            raise CaptureError("only original live captures may enter the sink")
        ref = record.collector_receipt_ref
        if not ref or ref in self._records:
            raise CaptureError("missing or duplicate collector receipt reference")
        self._records[ref] = record

    def authenticated_record(self, receipt_ref: str) -> KlineCaptureRecord | None:
        return self._records.get(receipt_ref)

    def records(self) -> tuple[KlineCaptureRecord, ...]:
        return tuple(self._records.values())


ClockAttestor = Callable[[str, datetime], CollectorClockEvidence | None]


class BybitKlineCaptureHook:
    """Callable installed on BybitDemoClient's post-IO, pre-parse boundary."""

    def __init__(self, sink: CaptureSink, *, clock_attestor: ClockAttestor | None = None,
                 request_id_factory: Callable[[], str] | None = None) -> None:
        self._sink = sink
        self._clock_attestor = clock_attestor
        self._request_id_factory = request_id_factory or (lambda: uuid4().hex)

    def __call__(self, request_url: str, raw_response: bytes, received_at: datetime) -> None:
        parsed = urlsplit(request_url)
        params = parse_qs(parsed.query, strict_parsing=True)
        if parsed.path != "/v5/market/kline" or params.get("category") != ["linear"]:
            return
        if params.get("interval") != ["1"] or len(params.get("symbol", ())) != 1:
            return
        symbol = params["symbol"][0]
        if symbol not in SYMBOLS:
            return
        if not isinstance(raw_response, bytes) or not raw_response:
            raise CaptureError("missing raw response bytes")
        digest = sha256(raw_response).hexdigest()
        request_id = self._request_id_factory()
        if not request_id:
            raise CaptureError("request identity required")
        if received_at is None:
            timestamp = None
            receipt_status = "MISSING"
        else:
            try:
                timestamp = utc(received_at)
            except (ValueError, AttributeError, TypeError):
                timestamp = received_at
                receipt_status = "INVALID_NON_UTC"
            else:
                receipt_status = "VALID"
        parameters = tuple(sorted((key, value) for key, values in params.items() for value in values))
        receipt_ref = capture_receipt_reference(
            PROVIDER_ID, STREAM_ID, symbol, parameters, request_id, timestamp, digest)
        evidence = self._clock_attestor(receipt_ref, timestamp) if self._clock_attestor and receipt_status == "VALID" else None
        clock_ok = (evidence is not None and evidence.receipt_ref == receipt_ref and
                    evidence.verified_at == timestamp)
        record = KlineCaptureRecord(
            PROVIDER_ID, STREAM_ID, symbol, parameters, request_id, raw_response, digest,
            timestamp, receipt_ref, evidence if clock_ok else None,
            receipt_status, "VERIFIED" if clock_ok else ("INVALID" if evidence else "UNVERIFIED"),
            CAPTURED_LIVE, _LIVE_TOKEN,
        )
        self._sink.append(record)


def load_capture_record(data: dict[str, object], *, sink: CaptureSink | None = None) -> KlineCaptureRecord:
    """Import bytes without granting new receipt authority; restore only from trusted sink."""
    try:
        raw = base64.b64decode(str(data["raw_response_base64"]), validate=True)
        digest = str(data["raw_response_sha256"])
        if not raw:
            raise CaptureError("missing raw response bytes")
        if sha256(raw).hexdigest() != digest:
            raise CaptureError("raw payload SHA-256 mismatch")
        ref = str(data["collector_receipt_ref"]) if data.get("collector_receipt_ref") is not None else None
        received = datetime.fromisoformat(str(data["collector_received_at"])) if data.get("collector_received_at") else None
        clock_data = data.get("clock_evidence")
        evidence = None
        if isinstance(clock_data, dict):
            evidence = CollectorClockEvidence(
                str(clock_data["reference"]), str(clock_data["receipt_ref"]),
                datetime.fromisoformat(str(clock_data["verified_at"])),
                timedelta(microseconds=int(clock_data["maximum_error_microseconds"])),
            )
        imported = KlineCaptureRecord(
            str(data["provider_id"]), str(data["stream_id"]), str(data["physical_symbol"]),
            tuple(tuple(pair) for pair in data["request_parameters"]), str(data["request_id"]),
            raw, digest, received, ref, evidence,
            str(data["receipt_status"]), str(data["clock_status"]), REPLAYED_OR_IMPORTED,
        )
    except (KeyError, TypeError, ValueError, base64.binascii.Error) as exc:
        if isinstance(exc, CaptureError):
            raise
        raise CaptureError("invalid serialized capture record") from exc
    if sink is not None and ref:
        original = sink.authenticated_record(ref)
        if original is not None and original.to_dict() == data:
            return original
    return imported


def capture_receipt_reference(provider_id: str, stream_id: str, symbol: str,
                              parameters: tuple[tuple[str, str], ...], request_id: str,
                              received_at: datetime | None, raw_sha256: str) -> str:
    """The Phase 4 identity rule, shared with durable reload verification."""
    identity = (provider_id, stream_id, symbol, parameters, request_id,
                received_at.isoformat() if isinstance(received_at, datetime) else None, raw_sha256)
    return "bybit-rest-receipt:" + sha256(json.dumps(identity, separators=(",", ":")).encode()).hexdigest()
