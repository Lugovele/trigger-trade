"""Append-only local research audit chain; hashes are not digital signatures."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Callable

from . import SPEC_ID, SPEC_VERSION
from .calendar import Horizon, iso, utc
from .manifests import canonical_json

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ENTRY_NAME = re.compile(r"[0-9]{12}\.json\Z")
_GENESIS = "0" * 64


class LedgerIntegrityError(ValueError):
    pass


class LedgerBusyError(ValueError):
    pass


@dataclass(frozen=True)
class ExperimentEntry:
    sequence: int
    entry_time: str
    clock_source: str
    actor: str
    action: str
    horizon_minutes: int
    fit_or_cohort_id: str
    partition_accessed: str
    spec_id: str
    spec_version: str
    manifest_hashes: tuple[tuple[str, str], ...]
    artifact_hashes: tuple[tuple[str, str], ...]
    code_revision_or_hash: str
    seed: int | None
    previous_entry_sha256: str
    entry_sha256: str

    def body(self) -> dict[str, object]:
        value = asdict(self)
        value.pop("entry_sha256")
        return value

    def to_json(self) -> str:
        return canonical_json(asdict(self))


def _entry_hash(body: dict[str, object]) -> str:
    return sha256(canonical_json(body).encode("utf-8")).hexdigest()


class ExperimentLedger:
    """Exclusive append, immutable numbered files, full-chain verification on read.

    A lock collision or interrupted append fails closed. This local hash chain
    detects ordinary mutation but does not provide a signature or trusted UTC
    clock. Those authorities must be supplied by a later evidence seal.
    """

    def __init__(self, root: Path | str, *, clock: Callable[[], datetime] | None = None) -> None:
        requested_root = Path(root)
        if requested_root.is_symlink():
            raise LedgerIntegrityError("ledger root is a symlink")
        self.root = requested_root.resolve()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._clock_source = "SYSTEM_UTC_UNATTESTED" if clock is None else "INJECTED_FIXTURE_CLOCK"

    def read_all(self) -> tuple[ExperimentEntry, ...]:
        if not self.root.exists():
            return ()
        if self.root.is_symlink() or not self.root.is_dir():
            raise LedgerIntegrityError("ledger root is not a trusted directory")
        paths = sorted(self.root.glob("*.json"))
        if any(not _ENTRY_NAME.fullmatch(path.name) or path.is_symlink() for path in paths):
            raise LedgerIntegrityError("unexpected ledger entry path")
        result = []
        previous = _GENESIS
        for expected_sequence, path in enumerate(paths, 1):
            if path.name != f"{expected_sequence:012d}.json":
                raise LedgerIntegrityError("ledger sequence gap or duplicate")
            try:
                body = json.loads(path.read_bytes())
                body["manifest_hashes"] = tuple(tuple(item) for item in body["manifest_hashes"])
                body["artifact_hashes"] = tuple(tuple(item) for item in body["artifact_hashes"])
                entry = ExperimentEntry(**body)
                if (entry.sequence != expected_sequence or entry.previous_entry_sha256 != previous or
                        entry.spec_id != SPEC_ID or entry.spec_version != SPEC_VERSION or
                        entry.entry_sha256 != _entry_hash(entry.body())):
                    raise LedgerIntegrityError("ledger hash chain mismatch")
                utc(datetime.fromisoformat(entry.entry_time.replace("Z", "+00:00")))
                Horizon(entry.horizon_minutes)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError, ValueError) as exc:
                if isinstance(exc, LedgerIntegrityError):
                    raise
                raise LedgerIntegrityError("corrupted ledger entry") from exc
            result.append(entry)
            previous = entry.entry_sha256
        return tuple(result)

    def append(self, *, actor: str, action: str, horizon_minutes: int,
               fit_or_cohort_id: str, partition_accessed: str,
               manifest_hashes: tuple[tuple[str, str], ...],
               artifact_hashes: tuple[tuple[str, str], ...],
               code_revision_or_hash: str, seed: int | None = None) -> ExperimentEntry:
        Horizon(horizon_minutes)
        if not actor or not action or not fit_or_cohort_id or not partition_accessed or not code_revision_or_hash:
            raise ValueError("complete ledger identity fields required")
        if seed is not None and (not isinstance(seed, int) or seed < 0):
            raise ValueError("invalid seed")
        for pairs in (manifest_hashes, artifact_hashes):
            if (tuple(sorted(pairs)) != pairs or len({name for name, _ in pairs}) != len(pairs) or
                    any(not name or not _SHA.fullmatch(value) for name, value in pairs)):
                raise ValueError("sorted unique SHA-256 identity pairs required")
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise LedgerIntegrityError("ledger root is a symlink")
        lock = self.root / ".append.lock"
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise LedgerBusyError("ledger append is locked") from exc
        try:
            os.close(fd)
            existing = self.read_all()
            recorded_at = utc(self._clock())
            previous = existing[-1].entry_sha256 if existing else _GENESIS
            provisional = ExperimentEntry(len(existing) + 1, iso(recorded_at), self._clock_source,
                                          actor, action, horizon_minutes, fit_or_cohort_id,
                                          partition_accessed, SPEC_ID, SPEC_VERSION,
                                          manifest_hashes, artifact_hashes, code_revision_or_hash,
                                          seed, previous, "")
            entry = ExperimentEntry(**{**provisional.body(), "entry_sha256": _entry_hash(provisional.body())})
            final = self.root / f"{entry.sequence:012d}.json"
            if final.exists():
                raise LedgerIntegrityError("ledger entry already exists")
            wire = entry.to_json().encode("utf-8")
            with tempfile.NamedTemporaryFile(mode="wb", dir=self.root, prefix=".ledger-",
                                             suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(wire)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                if os.name == "nt":
                    os.rename(temporary, final)  # Windows: fails if destination exists.
                else:
                    os.link(temporary, final)  # POSIX: never replaces destination.
                    directory_fd = os.open(self.root, os.O_RDONLY)
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
            except FileExistsError as exc:
                raise LedgerIntegrityError("ledger entry collision") from exc
            finally:
                temporary.unlink(missing_ok=True)
            return entry
        finally:
            lock.unlink(missing_ok=True)
