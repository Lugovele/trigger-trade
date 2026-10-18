"""Append-only, content-checked file sink for LDE Bybit capture evidence.

The configured directory and externally supplied authentication key form the
trust boundary. A copied or edited file cannot gain live receipt authority
without a valid keyed authenticator over the exact record metadata and bytes.
"""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import re
import tempfile

from .capture import (
    CAPTURED_LIVE, CaptureError, KlineCaptureRecord, _LIVE_TOKEN,
    capture_receipt_reference, load_capture_record,
)
from .bybit_rest_source import PROVIDER_ID, STREAM_ID
from .source import SYMBOLS, utc


_RECEIPT_PATTERN = re.compile(r"bybit-rest-receipt:([0-9a-f]{64})\Z")


class CaptureStorageError(CaptureError):
    """The durable capture directory could not complete an operation."""


class DuplicateCaptureReceipt(CaptureError):
    """An identical receipt reference already exists."""


class ConflictingCaptureReceipt(CaptureError):
    """A receipt reference exists with different stored content."""


class CaptureIntegrityError(CaptureError):
    """Persisted capture evidence failed an integrity check."""


class DurableCaptureSink:
    """One immutable JSON envelope per receipt; raw bytes are base64 lossless.

    The final path is installed from an fsynced same-directory temp file.
    Windows rename and POSIX hard-link both fail if the final path exists.
    No journal or mutable head is needed for receipt authentication.
    """

    def __init__(self, root: Path | str, *, authentication_key: bytes) -> None:
        if not isinstance(authentication_key, bytes) or len(authentication_key) < 32:
            raise CaptureStorageError("external capture authentication key must be at least 32 bytes")
        self.root = Path(root).resolve()
        self._authentication_key = authentication_key

    def append(self, record: KlineCaptureRecord) -> None:
        if record.provenance_mode != CAPTURED_LIVE or record._live_token is not _LIVE_TOKEN:
            raise CaptureStorageError("only original live captures may be appended")
        ref = record.collector_receipt_ref
        final = self._path(ref)
        body = record.to_dict()
        if final.exists():
            existing = self.authenticated_record(ref)
            if existing is not None and existing.to_dict() == body:
                raise DuplicateCaptureReceipt("collector receipt reference already exists")
            raise ConflictingCaptureReceipt("collector receipt reference has different content")
        try:
            _validate_identity(load_capture_record(body))
        except CaptureError as exc:
            raise CaptureStorageError("capture record provenance is invalid") from exc
        body_bytes = _canonical(body)
        envelope = {
            "record": body, "record_sha256": sha256(body_bytes).hexdigest(),
            "record_hmac_sha256": hmac.new(self._authentication_key, body_bytes, sha256).hexdigest(),
        }
        wire = _canonical(envelope)
        try:
            final.parent.mkdir(parents=True, exist_ok=True)
            if final.parent.is_symlink():
                raise CaptureStorageError("capture directory is a symlink")
            with tempfile.NamedTemporaryFile(mode="wb", dir=final.parent, prefix=".capture-",
                                             suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(wire)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                if os.name == "nt":
                    # Windows os.rename fails when destination exists.
                    os.rename(temporary, final)
                else:
                    os.link(temporary, final)
                    directory_fd = os.open(final.parent, os.O_RDONLY)
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
            except FileExistsError:
                existing = self.authenticated_record(ref)
                if existing is not None and existing.to_dict() == body:
                    raise DuplicateCaptureReceipt("collector receipt reference already exists")
                raise ConflictingCaptureReceipt("collector receipt reference has different content")
            finally:
                temporary.unlink(missing_ok=True)
        except (OSError, ValueError) as exc:
            if isinstance(exc, CaptureError):
                raise
            raise CaptureStorageError("capture storage unavailable") from exc

    def authenticated_record(self, receipt_ref: str) -> KlineCaptureRecord | None:
        path = self._path(receipt_ref)
        try:
            if path.is_symlink():
                raise CaptureIntegrityError("stored capture path is a symlink")
            wire = path.read_bytes()
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise CaptureStorageError("capture storage unavailable") from exc
        try:
            envelope = json.loads(wire)
            if not isinstance(envelope, dict) or set(envelope) != {"record", "record_sha256", "record_hmac_sha256"}:
                raise CaptureIntegrityError("invalid stored capture envelope")
            body = envelope["record"]
            if not isinstance(body, dict):
                raise CaptureIntegrityError("invalid stored capture record")
            body_bytes = _canonical(body)
            if sha256(body_bytes).hexdigest() != envelope["record_sha256"]:
                raise CaptureIntegrityError("stored capture metadata digest mismatch")
            expected_mac = hmac.new(self._authentication_key, body_bytes, sha256).hexdigest()
            if not hmac.compare_digest(expected_mac, str(envelope["record_hmac_sha256"])):
                raise CaptureIntegrityError("stored capture authenticator mismatch")
            if body.get("collector_receipt_ref") != receipt_ref:
                raise CaptureIntegrityError("stored receipt reference mismatch")
            # The only authority-restoring path follows a verified file read.
            imported = load_capture_record(body)
            _validate_identity(imported)
            return replace(imported, provenance_mode=CAPTURED_LIVE, _live_token=_LIVE_TOKEN)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError, CaptureError) as exc:
            if isinstance(exc, CaptureIntegrityError):
                raise
            raise CaptureIntegrityError("stored capture integrity failure") from exc

    def _path(self, receipt_ref: str | None) -> Path:
        match = _RECEIPT_PATTERN.fullmatch(receipt_ref or "")
        if match is None:
            raise CaptureStorageError("invalid collector receipt reference")
        digest = match.group(1)
        return self.root / digest[:2] / f"{digest}.json"


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _validate_identity(record: KlineCaptureRecord) -> None:
    if record.provider_id != PROVIDER_ID or record.stream_id != STREAM_ID or record.physical_symbol not in SYMBOLS:
        raise CaptureIntegrityError("stored provider identity mismatch")
    expected = capture_receipt_reference(
        record.provider_id, record.stream_id, record.physical_symbol,
        record.request_parameters, record.request_id,
        record.collector_received_at, record.raw_response_sha256)
    if record.collector_receipt_ref != expected:
        raise CaptureIntegrityError("stored collector receipt identity mismatch")
    if record.receipt_status == "VALID":
        if record.collector_received_at is None:
            raise CaptureIntegrityError("stored valid receipt timestamp is missing")
        try:
            utc(record.collector_received_at)
        except ValueError as exc:
            raise CaptureIntegrityError("stored receipt timestamp is not UTC") from exc
    elif record.receipt_status == "MISSING":
        if record.collector_received_at is not None:
            raise CaptureIntegrityError("stored missing receipt has a timestamp")
    elif record.receipt_status == "INVALID_NON_UTC":
        if record.collector_received_at is None:
            raise CaptureIntegrityError("stored invalid receipt has no timestamp")
        try:
            utc(record.collector_received_at)
        except ValueError:
            pass
        else:
            raise CaptureIntegrityError("stored invalid receipt is actually UTC")
    else:
        raise CaptureIntegrityError("stored receipt status is invalid")
    if record.clock_status == "VERIFIED":
        evidence = record.clock_evidence
        if (record.receipt_status != "VALID" or evidence is None or
                evidence.receipt_ref != expected or evidence.verified_at != record.collector_received_at):
            raise CaptureIntegrityError("stored clock attestation mismatch")
    elif record.clock_status in {"UNVERIFIED", "INVALID"}:
        if record.clock_evidence is not None:
            raise CaptureIntegrityError("unverified stored capture carries clock authority")
    else:
        raise CaptureIntegrityError("stored clock status is invalid")
