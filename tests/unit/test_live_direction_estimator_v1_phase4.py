"""Offline IO-boundary and replay-firewall tests for Bybit capture evidence."""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json

import pytest

from triggertrade.exchanges.bybit import BybitApiError, BybitDemoClient
from triggertrade.live_direction_estimator_v1.bybit_rest_source import (
    CollectorClockEvidence, adapt_bybit_linear_rest_capture,
)
from triggertrade.live_direction_estimator_v1.capture import (
    BybitKlineCaptureHook, CaptureError, MemoryCaptureSink,
    CAPTURED_LIVE, REPLAYED_OR_IMPORTED, load_capture_record,
)


T = datetime(2026, 1, 2, 12, tzinfo=UTC)
MINUTE = timedelta(minutes=1)


def _raw(close: str = "100", *, whitespace: bool = False) -> bytes:
    start = T - timedelta(minutes=4)
    rows = []
    for i in range(2):
        rows.append([str(int((start + i * MINUTE).timestamp() * 1000)),
                     "100", "101", "99", close, "2", "200"])
    body = {"retCode": 0, "time": "0", "result": {
        "category": "linear", "symbol": "BTCUSDT", "list": rows,
    }}
    return json.dumps(body, indent=2 if whitespace else None).encode()


def _collect(raw: bytes, *, receipt=T, attestor=None, allow_parse_error=False):
    order = []
    sink = MemoryCaptureSink()
    hook = BybitKlineCaptureHook(sink, clock_attestor=attestor,
                                 request_id_factory=lambda: "request-1")

    def transport(request, timeout):
        order.append("io-complete")
        return raw

    def receipt_clock():
        order.append("receipt-clock")
        return receipt

    client = BybitDemoClient(transport=transport, public_kline_capture=hook,
                             receipt_clock=receipt_clock)
    try:
        client.linear_recent_candles("BTCUSDT", interval="1", limit=2)
    except BybitApiError:
        if not allow_parse_error:
            raise
    return sink.records()[0], sink, order


def _verified(ref: str, received: datetime) -> CollectorClockEvidence:
    return CollectorClockEvidence("fixture-utc-bound", ref, received, timedelta(0))


def test_io_capture_exact_bytes_receipt_reference_and_handoff():
    raw = _raw(whitespace=True)
    record, sink, order = _collect(raw, attestor=_verified)
    assert order == ["io-complete", "receipt-clock"]
    assert record.provenance_mode == CAPTURED_LIVE
    assert record.raw_response == raw
    assert record.raw_response_sha256 == sha256(raw).hexdigest()
    assert record.collector_received_at == T
    assert record.collector_receipt_ref.startswith("bybit-rest-receipt:")
    assert record.request_id == "request-1"
    assert ("category", "linear") in record.request_parameters
    handed = record.to_bybit_rest_capture()
    assert handed.raw_response == raw and handed.collector_received_at == T
    assert handed.collector_receipt_ref == record.collector_receipt_ref
    assert handed.clock_evidence.receipt_ref == record.collector_receipt_ref
    adapted = adapt_bybit_linear_rest_capture(handed)
    assert adapted.versions[1].source_available_at == T
    assert sink.authenticated_record(record.collector_receipt_ref) is record


def test_raw_hash_exact_bytes_and_serialized_original_receipt():
    plain, sink, _ = _collect(_raw(), attestor=_verified)
    one_byte = bytearray(plain.raw_response)
    one_byte[one_byte.index(b'"100"') + 3] = ord("1")
    assert sum(left != right for left, right in zip(plain.raw_response, one_byte)) == 1
    assert sha256(one_byte).hexdigest() != plain.raw_response_sha256
    spaced, _, _ = _collect(_raw(whitespace=True), attestor=_verified)
    assert json.loads(plain.raw_response) == json.loads(spaced.raw_response)
    assert plain.raw_response_sha256 != spaced.raw_response_sha256
    assert plain.collector_receipt_ref != spaced.collector_receipt_ref
    serialized = json.loads(json.dumps(plain.to_dict()))
    restored = load_capture_record(serialized, sink=sink)
    assert restored is plain
    assert restored.collector_received_at == T
    assert restored.collector_receipt_ref == plain.collector_receipt_ref
    altered = dict(serialized, raw_response_sha256="0" * 64)
    with pytest.raises(CaptureError, match="SHA-256 mismatch"):
        load_capture_record(altered, sink=sink)
    missing = dict(serialized, raw_response_base64="")
    with pytest.raises(CaptureError, match="missing raw"):
        load_capture_record(missing, sink=sink)


def test_replay_firewall_never_calls_clock_or_grants_imported_receipt():
    original, sink, _ = _collect(_raw(), attestor=_verified)
    data = json.loads(json.dumps(original.to_dict()))
    imported = load_capture_record(data)
    assert imported.provenance_mode == REPLAYED_OR_IMPORTED
    assert imported.collector_received_at == T  # retained for audit only
    untrusted = imported.to_bybit_rest_capture()
    assert untrusted.collector_received_at is None
    assert untrusted.collector_receipt_ref is None
    assert adapt_bybit_linear_rest_capture(untrusted).versions[1].source_available_at is None
    # Even a later altered receipt cannot authenticate against the original sink.
    data["collector_received_at"] = (T + MINUTE).isoformat()
    later_import = load_capture_record(data, sink=sink)
    assert later_import.provenance_mode == REPLAYED_OR_IMPORTED
    assert later_import.to_bybit_rest_capture().collector_received_at is None
    assert load_capture_record(original.to_dict(), sink=sink) is original


def test_unverified_mismatched_and_uncertain_clock_fail_closed():
    raw = _raw()
    no_clock, _, _ = _collect(raw)
    assert no_clock.clock_status == "UNVERIFIED"
    assert adapt_bybit_linear_rest_capture(no_clock.to_bybit_rest_capture()).versions[1].source_available_at is None

    wrong = lambda ref, received: CollectorClockEvidence(
        "wrong", "another-receipt", received, timedelta(0))
    mismatch, _, _ = _collect(raw, attestor=wrong)
    assert mismatch.clock_status == "INVALID"
    assert adapt_bybit_linear_rest_capture(mismatch.to_bybit_rest_capture()).versions[1].source_available_at is None

    def uncertain(ref, received):
        return CollectorClockEvidence("bounded", ref, received, timedelta(microseconds=1))
    late, _, _ = _collect(raw, attestor=uncertain)
    assert adapt_bybit_linear_rest_capture(late.to_bybit_rest_capture()).versions[1].source_available_at == T + timedelta(microseconds=1)


def test_invalid_receipt_and_malformed_provider_response_are_explicit():
    missing, _, _ = _collect(_raw(), receipt=None, attestor=_verified)
    assert missing.receipt_status == "MISSING"
    assert missing.to_bybit_rest_capture().collector_received_at is None
    naive, _, _ = _collect(_raw(), receipt=T.replace(tzinfo=None), attestor=_verified)
    assert naive.receipt_status == "INVALID_NON_UTC"
    assert naive.to_bybit_rest_capture().collector_received_at is None
    malformed, _, _ = _collect(b"not-json", attestor=_verified, allow_parse_error=True)
    from triggertrade.live_direction_estimator_v1.bybit_rest_source import BybitRestSourceError
    with pytest.raises(BybitRestSourceError, match="invalid captured"):
        adapt_bybit_linear_rest_capture(malformed.to_bybit_rest_capture())


def test_hook_does_not_capture_spot_kline_or_call_receipt_clock():
    sink = MemoryCaptureSink()
    hook = BybitKlineCaptureHook(sink)
    client = BybitDemoClient(
        transport=lambda request, timeout: _raw(),
        public_kline_capture=hook,
        receipt_clock=lambda: (_ for _ in ()).throw(AssertionError("spot must not capture")),
    )
    client.recent_candles("BTCUSDT", interval="1", limit=2)
    assert sink.records() == ()


def test_hook_preserves_linear_non_1m_requests():
    sink = MemoryCaptureSink()
    hook = BybitKlineCaptureHook(sink)
    client = BybitDemoClient(
        transport=lambda request, timeout: _raw(),
        public_kline_capture=hook,
        receipt_clock=lambda: (_ for _ in ()).throw(AssertionError("5m must not capture")),
    )
    client.linear_recent_candles("BTCUSDT", interval="5", limit=2)
    assert sink.records() == ()
