"""Small, offline conformance fixtures for captured Bybit REST klines."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json

import pytest

from triggertrade.live_direction_estimator_v1.bybit_rest_source import (
    BybitRestCapture, BybitRestSourceError, CollectorClockEvidence,
    adapt_bybit_linear_rest_capture, build_bybit_rest_snapshot,
)


T = datetime(2026, 1, 2, 12, tzinfo=UTC)
MINUTE = timedelta(minutes=1)


def _row(start: datetime, close: str = "100") -> list[str]:
    return [str(int(start.timestamp() * 1000)), "100", "101", "99", close, "2", "200"]


def _capture(rows: list[list[str]], *, received=T, receipt="receipt-1", clock=True):
    raw = json.dumps({"retCode": 0, "time": "0", "result": {
        "category": "linear", "symbol": "BTCUSDT", "list": rows,
    }}, separators=(",", ":")).encode()
    evidence = (CollectorClockEvidence("external-clock-proof-1", receipt, received, timedelta(0))
                if clock and received and receipt else None)
    return BybitRestCapture(raw, "BTCUSDT", received, receipt, evidence)


def _support() -> tuple[BybitRestCapture, datetime]:
    first = T - timedelta(minutes=1447)
    # First item is a predecessor. Exactly 1,445 following items are needed.
    return _capture([_row(first + i * MINUTE) for i in range(1446)]), first


def test_finalization_receipt_and_audit_from_repository_rest_shape():
    start = T - timedelta(minutes=4)
    capture = _capture([_row(start), _row(start + MINUTE)])
    result = adapt_bybit_linear_rest_capture(capture)
    row = result.versions[1]
    assert result.receipt_status == "VALID" and result.clock_status == "VERIFIED"
    assert row.completed and row.source_available_at == T
    assert row.collector_received_at == T
    assert row.to_dict()["collector_clock_evidence_ref"] == "external-clock-proof-1"
    assert row.raw_payload_sha256 == result.raw_payload_sha256
    assert row.raw_payload_ref == f"receipt-1:{int((start + MINUTE).timestamp() * 1000)}"
    assert not result.versions[0].completed  # no preceding row in captured response
    assert json.loads(json.dumps(row.to_dict()))["source_available_at"] == T.isoformat()


def test_nonfinal_missing_receipt_invalid_clock_and_no_inferred_provider_time():
    start = T
    rows = [_row(start - MINUTE), _row(start)]
    nonfinal = adapt_bybit_linear_rest_capture(_capture(rows)).versions[1]
    assert not nonfinal.completed and nonfinal.source_available_at is None
    missing = adapt_bybit_linear_rest_capture(_capture(rows, received=None, clock=False))
    assert missing.receipt_status == "MISSING"
    assert missing.versions[1].source_available_at is None
    unverified = adapt_bybit_linear_rest_capture(_capture(rows, clock=False))
    assert unverified.clock_status == "UNAVAILABLE"
    assert unverified.captured_received_at == T
    assert unverified.versions[1].collector_received_at is None
    naive = adapt_bybit_linear_rest_capture(_capture(rows, received=T.replace(tzinfo=None), clock=False))
    assert naive.receipt_status == "INVALID_NON_UTC"
    assert naive.versions[1].source_available_at is None
    missing_ref = adapt_bybit_linear_rest_capture(_capture(rows, receipt=None))
    assert missing_ref.receipt_status == "MISSING_REFERENCE"
    assert missing_ref.versions[1].source_available_at is None


def test_exact_cutoff_late_message_retransmission_and_snapshot_immutability():
    capture, first = _support()
    base = adapt_bybit_linear_rest_capture(capture)
    snapshot = build_bybit_rest_snapshot("BTCUSDT", T, (base,)).snapshot
    assert snapshot is not None and len(snapshot.local_minutes) == 1445
    assert snapshot.local_minutes[-1].interval_end == T - MINUTE
    assert build_bybit_rest_snapshot("BTCUSDT", T, (base, base)).snapshot == snapshot
    later = adapt_bybit_linear_rest_capture(_capture(
        [_row(first), _row(first + MINUTE)], received=T + MINUTE))
    assert build_bybit_rest_snapshot("BTCUSDT", T, (later,)).snapshot is None
    assert "DATA_LATE" in build_bybit_rest_snapshot("BTCUSDT", T, (later,)).reasons
    corrected = adapt_bybit_linear_rest_capture(_capture(
        [_row(first), _row(first + MINUTE, "100.5")], received=T + MINUTE,
        receipt="receipt-correction"))
    unchanged = build_bybit_rest_snapshot("BTCUSDT", T, (base, corrected)).snapshot
    assert unchanged == snapshot
    assert unchanged.source_snapshot_id == snapshot.source_snapshot_id


def test_content_identity_conflict_and_no_rest_supersession_authority():
    capture, first = _support()
    base = adapt_bybit_linear_rest_capture(capture)
    duplicate = adapt_bybit_linear_rest_capture(_capture(
        [_row(first), _row(first + MINUTE)], receipt="receipt-retransmit"))
    assert base.versions[1].canonical_version_id == duplicate.versions[1].canonical_version_id
    forward = build_bybit_rest_snapshot("BTCUSDT", T, (base, duplicate)).snapshot
    reverse = build_bybit_rest_snapshot("BTCUSDT", T, (duplicate, base)).snapshot
    assert forward is not None and forward == reverse
    correction = adapt_bybit_linear_rest_capture(_capture(
        [_row(first), _row(first + MINUTE, "100.5")], receipt="receipt-correction"))
    assert correction.raw_payload_sha256 != duplicate.raw_payload_sha256
    assert correction.versions[1].canonical_version_id != duplicate.versions[1].canonical_version_id
    assert correction.versions[1].supersedes_version_id is None
    result = build_bybit_rest_snapshot("BTCUSDT", T, (base, correction))
    assert result.snapshot is None and "SOURCE_VERSION_CONFLICT" in result.reasons


def test_invalid_response_and_duplicate_intervals_fail_closed():
    start = T - timedelta(minutes=4)
    with pytest.raises(BybitRestSourceError, match="duplicate interval"):
        adapt_bybit_linear_rest_capture(_capture([_row(start), _row(start)]))
    bad = replace(_capture([_row(start)]), raw_response=b'{"retCode": 1}')
    with pytest.raises(BybitRestSourceError, match="invalid captured"):
        adapt_bybit_linear_rest_capture(bad)
    malformed = _capture([_row(start), [*_row(start + MINUTE)[:3], "not-a-number", "100", "2", "200"]])
    with pytest.raises(BybitRestSourceError, match="invalid captured"):
        adapt_bybit_linear_rest_capture(malformed)


def test_clock_evidence_must_cover_receipt_and_uncertainty_cutoff():
    start = T - timedelta(minutes=4)
    capture = _capture([_row(start), _row(start + MINUTE)])
    stale = replace(capture, clock_evidence=CollectorClockEvidence(
        "old-proof", "receipt-1", T - MINUTE, timedelta(0)))
    assert adapt_bybit_linear_rest_capture(stale).versions[1].source_available_at is None
    wrong_receipt = replace(capture, clock_evidence=CollectorClockEvidence(
        "wrong-receipt", "another-receipt", T, timedelta(0)))
    assert adapt_bybit_linear_rest_capture(wrong_receipt).versions[1].source_available_at is None
    uncertain = replace(capture, clock_evidence=CollectorClockEvidence(
        "bounded-proof", "receipt-1", T, timedelta(microseconds=1)))
    row = adapt_bybit_linear_rest_capture(uncertain).versions[1]
    assert row.completed and row.source_available_at == T + timedelta(microseconds=1)
    assert "DATA_LATE" in build_bybit_rest_snapshot("BTCUSDT", T, (
        adapt_bybit_linear_rest_capture(uncertain),)).reasons
