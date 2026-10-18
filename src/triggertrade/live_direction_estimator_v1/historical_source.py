"""Manifest-bound adapter for the retained direction-regime-history CSV rows.

This module accepts rows from the existing CSV reader. It never scans or
rehashes a member file, and it never creates historical availability times.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
from hashlib import sha256
from io import BytesIO, TextIOWrapper
import csv
import gzip
import json
from pathlib import Path
from typing import Iterable, Mapping

from .snapshot import EVENT_TIME_ONLY, SnapshotResult, build_snapshot
from .source import MINUTE, SYMBOLS, SourceMinute, utc

SPEC_SOURCE_MANIFEST_SHA256 = "f600c0546344259911075f479de583c69d88435321e06c41e0e61acbf49bf45e"
SPEC_CORPUS_ID = "direction-regime-history-20240930-20260930-bybit-linear-1m-v1"
_LOGICAL = {"BTCUSDT": "BTCUSDT", "AVAXUSDT": "AVAXUSDT", "SUIUSDT": "SUIUSDT", "1000PEPEUSDT": "PEPEUSDT"}
_CSV_FIELDS = ("open_time", "close_time", "symbol", "logical_symbol", "category", "timeframe",
               "open", "high", "low", "close", "volume", "turnover")


class HistoricalSourceError(ValueError):
    """The retained-source identity or row contract is not established."""


@dataclass(frozen=True)
class HistoricalMember:
    physical_symbol: str
    logical_symbol: str
    local_path: str
    declared_sha256: str
    declared_rows: int
    first_open: str
    exclusive_end: str
    member_bytes_verified: bool = False


@dataclass(frozen=True)
class HistoricalSourceContract:
    corpus_id: str
    manifest_sha256: str
    completion_contract_id: str
    members: tuple[HistoricalMember, ...]
    provenance_mode: str = EVENT_TIME_ONLY

    def member(self, symbol: str) -> HistoricalMember:
        for member in self.members:
            if member.physical_symbol == symbol:
                return member
        raise HistoricalSourceError(f"symbol absent from authenticated manifest: {symbol}")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class HistoricalObservation:
    minute: SourceMinute
    corpus_id: str
    manifest_sha256: str
    member_declared_sha256: str
    member_bytes_verified: bool
    row_membership_verified: bool
    row_number: int
    raw_row_sha256: str
    provenance_mode: str = EVENT_TIME_ONLY

    def to_dict(self) -> dict[str, object]:
        return {
            "provenance_mode": self.provenance_mode,
            "corpus_id": self.corpus_id,
            "manifest_sha256": self.manifest_sha256,
            "member_declared_sha256": self.member_declared_sha256,
            "member_bytes_verified": self.member_bytes_verified,
            "row_membership_verified": self.row_membership_verified,
            "row_number": self.row_number,
            "raw_row_sha256": self.raw_row_sha256,
            "physical_symbol": self.minute.physical_symbol,
            "interval_start": self.minute.interval_start.isoformat(),
            "interval_end": self.minute.interval_end.isoformat(),
            "version_id": self.minute.version_id,
            "completed": self.minute.completed,
            "source_available_at": None,
            "collector_received_at": None,
            "evidence_available_at": None,
        }


def authenticate_historical_manifest(
    manifest_path: Path, *, expected_sha256: str = SPEC_SOURCE_MANIFEST_SHA256,
    expected_corpus_id: str = SPEC_CORPUS_ID,
) -> HistoricalSourceContract:
    """Hash only the small manifest; member hashes remain declared evidence."""
    return authenticate_historical_manifest_bytes(manifest_path.read_bytes(),
                                                  expected_sha256=expected_sha256,
                                                  expected_corpus_id=expected_corpus_id)


def authenticate_historical_manifest_bytes(
    raw: bytes, *, expected_sha256: str = SPEC_SOURCE_MANIFEST_SHA256,
    expected_corpus_id: str = SPEC_CORPUS_ID,
) -> HistoricalSourceContract:
    """Authenticate a bounded manifest byte payload without member reads."""
    actual = sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise HistoricalSourceError("source manifest SHA-256 mismatch")
    try:
        manifest = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise HistoricalSourceError("invalid source manifest JSON") from exc
    if (manifest.get("corpus_id") != expected_corpus_id or manifest.get("status") != "DATA_READY" or
            manifest.get("category") != "linear" or manifest.get("timeframe") != "1m" or
            tuple(manifest.get("symbols", {}).get("physical", ())) != SYMBOLS):
        raise HistoricalSourceError("source manifest identity/schema mismatch")
    files = manifest.get("files", ())
    integrity = manifest.get("integrity", {})
    if len(files) != 4 or set(integrity) != set(SYMBOLS):
        raise HistoricalSourceError("source manifest member set mismatch")
    members = []
    seen = set()
    for record in files:
        symbol = record.get("physical_symbol")
        if symbol not in SYMBOLS or symbol in seen:
            raise HistoricalSourceError("duplicate or unsupported manifest member")
        seen.add(symbol)
        check = integrity[symbol]
        digest = record.get("sha256")
        path = record.get("local_path")
        rows = record.get("rows")
        if (record.get("symbol") != _LOGICAL[symbol] or record.get("category") != "linear" or
                record.get("timeframe") != "1m" or record.get("type") != "candles_1m_csv_gz" or
                not isinstance(digest, str) or len(digest) != 64 or
                not isinstance(path, str) or path != f"runtime/data/direction-regime-history/{symbol}_1m.csv.gz" or
                not isinstance(rows, int) or rows <= 0 or
                record.get("start") != check.get("start") or record.get("end") != check.get("end") or
                check.get("status") != "PASS" or check.get("sha256") != digest or check.get("rows") != rows or
                check.get("expected_minutes") != rows or check.get("continuous_minutes") != rows or
                any(check.get(key) != 0 for key in ("duplicate_timestamps", "missing_minutes", "non_monotonic_timestamps",
                                                    "invalid_ohlc", "non_positive_prices"))):
            raise HistoricalSourceError(f"invalid historical completion/member contract: {symbol}")
        members.append(HistoricalMember(symbol, _LOGICAL[symbol], path, digest, rows,
                                        record["start"], record["end"]))
    if seen != set(SYMBOLS):
        raise HistoricalSourceError("source manifest physical universe mismatch")
    return HistoricalSourceContract(expected_corpus_id, actual, f"frozen-final-vintage:{actual}", tuple(members))


def adapt_historical_row(
    row: Mapping[str, object], *, contract: HistoricalSourceContract,
    physical_symbol: str, row_number: int,
) -> HistoricalObservation:
    """Bind one existing reader row to its manifest member and row position."""
    member = contract.member(physical_symbol)
    if row_number < 1 or not isinstance(row_number, int):
        raise HistoricalSourceError("positive source row number required")
    if (set(row) != set(_CSV_FIELDS) or str(row.get("symbol")) != physical_symbol or
            str(row.get("logical_symbol")) != member.logical_symbol or
            str(row.get("category")) != "linear" or str(row.get("timeframe")) != "1m"):
        raise HistoricalSourceError("historical CSV row schema/identity mismatch")
    raw_fields = {key: str(row[key]) for key in _CSV_FIELDS}
    raw_hash = sha256(json.dumps(raw_fields, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    version_payload = (contract.corpus_id, contract.manifest_sha256, member.declared_sha256,
                       physical_symbol, row_number, raw_hash)
    version_id = "hist:" + sha256(json.dumps(version_payload, separators=(",", ":")).encode()).hexdigest()
    minute = SourceMinute.from_historical_row(row, version_id=version_id,
                                              source_ref=f"{member.local_path}#row={row_number}",
                                              completion_contract_id=contract.completion_contract_id)
    if (minute.interval_end != minute.interval_start + MINUTE or minute.interval_start.second or
            minute.interval_start.microsecond or not minute.valid_ohlc or
            not datetime.fromisoformat(member.first_open.replace("Z", "+00:00")) <= minute.interval_start <
            datetime.fromisoformat(member.exclusive_end.replace("Z", "+00:00"))):
        raise HistoricalSourceError("historical CSV minute interval/OHLC outside completion contract")
    first = datetime.fromisoformat(member.first_open.replace("Z", "+00:00"))
    if row_number != int((minute.interval_start - first) / MINUTE) + 1 or row_number > member.declared_rows:
        raise HistoricalSourceError("historical row number does not match frozen interval order")
    minute = replace(minute, audit_fields=(
        ("provenance_mode", EVENT_TIME_ONLY), ("corpus_id", contract.corpus_id),
        ("manifest_sha256", contract.manifest_sha256), ("member_declared_sha256", member.declared_sha256),
        ("member_bytes_verified", str(member.member_bytes_verified)),
        ("row_membership_verified", "False"),
        ("row_number", str(row_number)), ("raw_row_sha256", raw_hash),
    ))
    return HistoricalObservation(minute, contract.corpus_id, contract.manifest_sha256,
                                 member.declared_sha256, member.member_bytes_verified, False, row_number, raw_hash)


def adapt_historical_rows(rows: Iterable[tuple[int, Mapping[str, object]]], *,
                          contract: HistoricalSourceContract, physical_symbol: str) -> tuple[HistoricalObservation, ...]:
    observations = tuple(adapt_historical_row(row, contract=contract, physical_symbol=physical_symbol,
                                               row_number=number) for number, row in rows)
    if (len({o.row_number for o in observations}) != len(observations) or
            len({o.minute.interval_start for o in observations}) != len(observations)):
        raise HistoricalSourceError("duplicate historical row/interval in selected input")
    return observations


def build_historical_snapshot(physical_symbol: str, origin: datetime,
                              observations: Iterable[HistoricalObservation], *,
                              contract: HistoricalSourceContract) -> SnapshotResult:
    frozen = tuple(observations)
    if any(o.provenance_mode != EVENT_TIME_ONLY or o.minute.source_available_at is not None or
           o.corpus_id != contract.corpus_id or o.manifest_sha256 != contract.manifest_sha256 or
           o.member_declared_sha256 != contract.member(o.minute.physical_symbol).declared_sha256 or
           not o.member_bytes_verified or not o.row_membership_verified or
           not contract.member(o.minute.physical_symbol).member_bytes_verified or
           o.minute.completion_contract_id != contract.completion_contract_id for o in frozen):
        raise HistoricalSourceError("mixed or unverified historical source contract")
    return build_snapshot(physical_symbol, utc(origin), (o.minute for o in frozen), mode=EVENT_TIME_ONLY)


def adapt_verified_historical_member_bytes(
    member_bytes: bytes, *, contract: HistoricalSourceContract,
    physical_symbol: str, row_numbers: Iterable[int],
) -> tuple[HistoricalSourceContract, tuple[HistoricalObservation, ...]]:
    """Bind selected rows to the exact gzip member bytes before adaptation.

    This function is for small fixtures or a future separately authorized
    member-byte verification. It is not called on the retained full corpus in
    this phase. Supplied arbitrary mappings never gain row-membership status.
    """
    wanted = tuple(row_numbers)
    if not wanted or len(set(wanted)) != len(wanted) or any(not isinstance(n, int) or n < 1 for n in wanted):
        raise HistoricalSourceError("distinct positive source row numbers required")
    wanted_set = set(wanted)
    verified = with_verified_member_digest(contract, physical_symbol, sha256(member_bytes).hexdigest())
    chosen: dict[int, HistoricalObservation] = {}
    try:
        with gzip.GzipFile(fileobj=BytesIO(member_bytes), mode="rb") as compressed:
            with TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                reader = csv.DictReader(text)
                for number, row in enumerate(reader, 1):
                    if number in wanted_set:
                        observation = adapt_historical_row(row, contract=verified,
                                                           physical_symbol=physical_symbol,
                                                           row_number=number)
                        minute = replace(observation.minute, audit_fields=tuple(
                            (key, "True") if key == "row_membership_verified" else (key, value)
                            for key, value in observation.minute.audit_fields
                        ))
                        chosen[number] = replace(observation, minute=minute, row_membership_verified=True)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise HistoricalSourceError("invalid historical member gzip/CSV bytes") from exc
    if set(chosen) != wanted_set:
        raise HistoricalSourceError("required row absent from verified member bytes")
    return verified, tuple(chosen[number] for number in wanted)


def with_verified_member_digest(contract: HistoricalSourceContract, physical_symbol: str,
                                actual_sha256: str) -> HistoricalSourceContract:
    """Accept a digest computed by a separate authorized byte verifier.

    This function does not read the member file or imply current-byte
    authentication merely from its manifest entry or an earlier audit.
    """
    member = contract.member(physical_symbol)
    if actual_sha256 != member.declared_sha256:
        raise HistoricalSourceError("historical member SHA-256 mismatch")
    return replace(contract, members=tuple(
        replace(item, member_bytes_verified=True) if item.physical_symbol == physical_symbol else item
        for item in contract.members
    ))
