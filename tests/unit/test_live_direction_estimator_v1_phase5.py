"""Small offline durable-capture and UTC-bound conformance fixtures."""

from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import hmac
from pathlib import Path
import base64
import json
import tempfile

import pytest

from triggertrade.exchanges.bybit import BybitDemoClient
from triggertrade.live_direction_estimator_v1.bybit_rest_source import adapt_bybit_linear_rest_capture
from triggertrade.live_direction_estimator_v1.capture import (
    BybitKlineCaptureHook, REPLAYED_OR_IMPORTED, load_capture_record,
)
from triggertrade.live_direction_estimator_v1.clock_attestation import (
    ClockAttestationError, ExternalBoundClockAttestor, UnverifiedClockAttestor,
    UtcReceiptBound,
)
from triggertrade.live_direction_estimator_v1.durable_capture import (
    CaptureIntegrityError, CaptureStorageError, ConflictingCaptureReceipt,
    DuplicateCaptureReceipt, DurableCaptureSink,
)


T = datetime(2026, 1, 2, 12, tzinfo=UTC)
MINUTE = timedelta(minutes=1)
FIXTURE_AUTHENTICATION_KEY = bytes(range(32))  # synthetic test key, never deployed


@contextmanager
def _fixture_directory():
    with tempfile.TemporaryDirectory(prefix="lde-v1-capture-", dir=Path.cwd()) as name:
        yield Path(name)


def _raw(close="100"):
    first = T - timedelta(minutes=4)
    rows = [[str(int((first + i * MINUTE).timestamp() * 1000)),
             "100", "101", "99", close, "2", "200"] for i in range(2)]
    return json.dumps({"retCode": 0, "result": {
        "category": "linear", "symbol": "BTCUSDT", "list": rows,
    }}, separators=(",", ":")).encode()


class _FixtureUtcSource:
    def __init__(self, error=timedelta(0), wrong_receipt=False):
        self.error = error
        self.wrong_receipt = wrong_receipt

    def bound_receipt(self, receipt_ref, received_at):
        return UtcReceiptBound(
            "wrong" if self.wrong_receipt else receipt_ref,
            received_at, self.error, "fixture-bounded-utc-source",
        )


def _capture(directory, *, attestor=None, raw=None):
    sink = DurableCaptureSink(directory, authentication_key=FIXTURE_AUTHENTICATION_KEY)
    hook = BybitKlineCaptureHook(sink, clock_attestor=attestor,
                                 request_id_factory=lambda: "fixture-request-1")
    client = BybitDemoClient(
        transport=lambda request, timeout: raw if raw is not None else _raw(),
        public_kline_capture=hook,
        receipt_clock=lambda: T,
    )
    client.linear_recent_candles("BTCUSDT", interval="1", limit=2)
    paths = tuple(directory.rglob("*.json"))
    assert len(paths) == 1
    path = paths[0]
    ref = "bybit-rest-receipt:" + path.stem
    return sink.authenticated_record(ref), sink, path


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _reseal_fixture_envelope(envelope):
    body = _canonical(envelope["record"])
    envelope["record_sha256"] = sha256(body).hexdigest()
    envelope["record_hmac_sha256"] = hmac.new(FIXTURE_AUTHENTICATION_KEY, body, sha256).hexdigest()


def test_durable_append_restart_and_trusted_reload_preserve_original_receipt():
    with _fixture_directory() as directory:
        record, sink, path = _capture(
            directory, attestor=ExternalBoundClockAttestor(_FixtureUtcSource()))
        assert path.read_bytes()
        assert record.raw_response == _raw()
        assert record.raw_response_sha256 == sha256(_raw()).hexdigest()
        assert record.collector_received_at == T
        assert record.clock_status == "VERIFIED"
        after_restart = DurableCaptureSink(directory, authentication_key=FIXTURE_AUTHENTICATION_KEY)
        restored = after_restart.authenticated_record(record.collector_receipt_ref)
        assert restored.to_dict() == record.to_dict()
        assert restored.to_bybit_rest_capture().collector_received_at == T
        assert adapt_bybit_linear_rest_capture(restored.to_bybit_rest_capture()).versions[1].source_available_at == T
        serialized = json.loads(json.dumps(record.to_dict()))
        assert load_capture_record(serialized, sink=after_restart).to_dict() == record.to_dict()
        imported = load_capture_record(serialized)
        assert imported.provenance_mode == REPLAYED_OR_IMPORTED
        assert imported.to_bybit_rest_capture().collector_received_at is None
        with pytest.raises(CaptureStorageError, match="original live"):
            after_restart.append(imported)
        altered = dict(serialized, collector_received_at=(T + MINUTE).isoformat())
        assert load_capture_record(altered, sink=after_restart).to_bybit_rest_capture().collector_received_at is None
        assert sink.authenticated_record(record.collector_receipt_ref).to_dict() == record.to_dict()
        with pytest.raises(CaptureIntegrityError, match="authenticator"):
            DurableCaptureSink(directory, authentication_key=bytes(range(1, 33))).authenticated_record(
                record.collector_receipt_ref)


def test_arbitrary_import_has_no_public_live_rehydration_path():
    from triggertrade.live_direction_estimator_v1 import capture as capture_module

    assert not hasattr(capture_module, "rehydrate_trusted_capture")
    with _fixture_directory() as directory:
        record, _, path = _capture(directory)
        forged = json.loads(path.read_bytes())
        forged["record"]["request_id"] = "forged-request"
        forged["record_sha256"] = sha256(_canonical(forged["record"])).hexdigest()
        path.write_bytes(_canonical(forged))
        sink = DurableCaptureSink(directory, authentication_key=FIXTURE_AUTHENTICATION_KEY)
        with pytest.raises(CaptureIntegrityError, match="authenticator"):
            sink.authenticated_record(record.collector_receipt_ref)
        imported = load_capture_record(forged["record"])
        assert imported.provenance_mode == REPLAYED_OR_IMPORTED
        assert imported.to_bybit_rest_capture().collector_received_at is None


def test_duplicate_conflict_and_no_overwrite():
    with _fixture_directory() as directory:
        record, sink, path = _capture(directory)
        original = path.read_bytes()
        with pytest.raises(DuplicateCaptureReceipt):
            sink.append(record)
        changed_raw = _raw("100.5")
        changed = replace(record, raw_response=changed_raw,
                          raw_response_sha256=sha256(changed_raw).hexdigest())
        with pytest.raises(ConflictingCaptureReceipt):
            sink.append(changed)
        assert path.read_bytes() == original


def test_raw_hash_metadata_and_missing_payload_corruption_fail_reload():
    with _fixture_directory() as directory:
        record, sink, path = _capture(directory)
        original = path.read_bytes()
        envelope = json.loads(original)
        raw = bytearray(record.raw_response)
        raw[raw.index(b'"100"') + 3] = ord("1")
        envelope["record"]["raw_response_base64"] = base64.b64encode(raw).decode()
        _reseal_fixture_envelope(envelope)
        path.write_bytes(_canonical(envelope))
        with pytest.raises(CaptureIntegrityError, match="integrity"):
            sink.authenticated_record(record.collector_receipt_ref)
        path.write_bytes(original)
        envelope = json.loads(original)
        envelope["record"]["collector_received_at"] = (T + MINUTE).isoformat()
        path.write_bytes(_canonical(envelope))
        with pytest.raises(CaptureIntegrityError, match="metadata digest"):
            sink.authenticated_record(record.collector_receipt_ref)
        path.write_bytes(original)
        envelope = json.loads(original)
        envelope["record"].pop("raw_response_base64")
        _reseal_fixture_envelope(envelope)
        path.write_bytes(_canonical(envelope))
        with pytest.raises(CaptureIntegrityError, match="integrity"):
            sink.authenticated_record(record.collector_receipt_ref)


def test_clock_unavailable_positive_bound_and_receipt_mismatch():
    with _fixture_directory() as directory:
        record, _, _ = _capture(directory, attestor=UnverifiedClockAttestor())
        assert record.clock_status == "UNVERIFIED"
        assert adapt_bybit_linear_rest_capture(record.to_bybit_rest_capture()).versions[1].source_available_at is None
    with _fixture_directory() as directory:
        bound = ExternalBoundClockAttestor(_FixtureUtcSource(timedelta(microseconds=1)))
        record, _, _ = _capture(directory, attestor=bound)
        assert adapt_bybit_linear_rest_capture(record.to_bybit_rest_capture()).versions[1].source_available_at == T + timedelta(microseconds=1)
    with _fixture_directory() as directory:
        bad = ExternalBoundClockAttestor(_FixtureUtcSource(wrong_receipt=True))
        with pytest.raises(ClockAttestationError, match="does not cover"):
            _capture(directory, attestor=bad)
        assert tuple(directory.rglob("*.json")) == ()
    with pytest.raises(ClockAttestationError, match="does not cover"):
        ExternalBoundClockAttestor(_FixtureUtcSource(timedelta(microseconds=-1)))("receipt", T)


def test_storage_unavailable_fails_without_capture():
    with _fixture_directory() as directory:
        blocked = directory / "not-a-directory"
        blocked.write_text("occupied", encoding="utf-8")
        with pytest.raises(CaptureStorageError, match="storage unavailable"):
            _capture(blocked)
