"""Collector-facing provenance records for future ASOF_VERIFIED sources.

No network collector is installed by this module. The collector must supply
actual receipt and evidence times and authenticate any version precedence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Iterable

from .snapshot import ASOF_VERIFIED, SnapshotResult, SupersessionPolicy, build_snapshot
from .source import SourceMinute, utc


@dataclass(frozen=True)
class AvailabilityEvidence:
    kind: str
    reference: str
    available_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "available_at", utc(self.available_at))
        if not self.kind or not self.reference:
            raise ValueError("evidence kind and reference required")

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "reference": self.reference,
                "available_at": self.available_at.isoformat()}


@dataclass(frozen=True)
class ProspectiveSourceVersion:
    physical_symbol: str
    interval_start: datetime
    interval_end: datetime
    open: float
    high: float
    low: float
    close: float
    provider_id: str
    source_stream_id: str
    provider_version_id: str
    completed: bool
    collector_received_at: datetime | None
    collector_receipt_ref: str | None
    evidence: tuple[AvailabilityEvidence, ...]
    required_evidence_kinds: tuple[str, ...]
    availability_contract_id: str
    raw_payload_ref: str | None = None
    raw_payload_sha256: str | None = None
    supersedes_version_id: str | None = None
    supersession_evidence_ref: str | None = None
    collector_clock_evidence_ref: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "interval_start", utc(self.interval_start))
        object.__setattr__(self, "interval_end", utc(self.interval_end))
        if self.collector_received_at is not None:
            object.__setattr__(self, "collector_received_at", utc(self.collector_received_at))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "required_evidence_kinds", tuple(self.required_evidence_kinds))
        if not all((self.provider_id, self.source_stream_id, self.provider_version_id,
                    self.availability_contract_id)):
            raise ValueError("provider, source stream, version and availability contract required")
        if "FINALIZATION" not in self.required_evidence_kinds:
            raise ValueError("finalization evidence must be required")
        if self.raw_payload_sha256 is not None and (len(self.raw_payload_sha256) != 64 or
                                                    any(ch not in "0123456789abcdef" for ch in self.raw_payload_sha256)):
            raise ValueError("raw payload SHA-256 must be lowercase hex")

    @property
    def canonical_version_id(self) -> str:
        payload = (self.provider_id, self.source_stream_id, self.physical_symbol,
                   self.interval_start.isoformat(), self.provider_version_id)
        return "asof:" + sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()

    @property
    def source_available_at(self) -> datetime | None:
        if (not self.completed or self.collector_received_at is None or not self.collector_receipt_ref or
                not self.required_evidence_kinds or len(set(self.required_evidence_kinds)) != len(self.required_evidence_kinds)):
            return None
        present = {item.kind for item in self.evidence}
        if not set(self.required_evidence_kinds) <= present:
            return None
        if not self.evidence:
            return None
        available = max(self.collector_received_at, *(item.available_at for item in self.evidence))
        return available if available >= self.interval_end else None

    def to_source_minute(self) -> SourceMinute:
        # Withhold the availability contract when required evidence is absent.
        contract = self.availability_contract_id if self.source_available_at is not None else None
        audit = (
            ("provenance_mode", ASOF_VERIFIED), ("provider_id", self.provider_id),
            ("source_stream_id", self.source_stream_id), ("provider_version_id", self.provider_version_id),
            ("raw_payload_ref", self.raw_payload_ref or ""),
            ("raw_payload_sha256", self.raw_payload_sha256 or ""),
            ("supersedes_version_id", self.supersedes_version_id or ""),
            ("supersession_evidence_ref", self.supersession_evidence_ref or ""),
            ("collector_clock_evidence_ref", self.collector_clock_evidence_ref or ""),
            ("required_evidence_kinds", ",".join(self.required_evidence_kinds)),
        )
        return SourceMinute(
            physical_symbol=self.physical_symbol, interval_start=self.interval_start,
            interval_end=self.interval_end, open=self.open, high=self.high, low=self.low, close=self.close,
            version_id=self.canonical_version_id, completed=self.completed,
            collector_received_at=self.collector_received_at, collector_receipt_ref=self.collector_receipt_ref,
            evidence_available_at=tuple(item.available_at for item in self.evidence),
            evidence_refs=tuple(f"{item.kind}:{item.reference}" for item in self.evidence),
            availability_contract_id=contract, source_ref=self.raw_payload_ref, audit_fields=audit,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "provenance_mode": ASOF_VERIFIED if self.source_available_at is not None else None,
            "physical_symbol": self.physical_symbol,
            "interval_start": self.interval_start.isoformat(), "interval_end": self.interval_end.isoformat(),
            "open": self.open, "high": self.high, "low": self.low, "close": self.close,
            "provider_id": self.provider_id, "source_stream_id": self.source_stream_id,
            "provider_version_id": self.provider_version_id, "canonical_version_id": self.canonical_version_id,
            "completed": self.completed,
            "collector_received_at": self.collector_received_at.isoformat() if self.collector_received_at else None,
            "collector_receipt_ref": self.collector_receipt_ref,
            "evidence": [item.to_dict() for item in self.evidence],
            "required_evidence_kinds": list(self.required_evidence_kinds),
            "availability_contract_id": self.availability_contract_id,
            "source_available_at": self.source_available_at.isoformat() if self.source_available_at else None,
            "raw_payload_ref": self.raw_payload_ref, "raw_payload_sha256": self.raw_payload_sha256,
            "supersedes_version_id": self.supersedes_version_id,
            "supersession_evidence_ref": self.supersession_evidence_ref,
            "collector_clock_evidence_ref": self.collector_clock_evidence_ref,
        }


@dataclass(frozen=True)
class AuthenticatedSupersession:
    """Precedence attested outside this package by a provider/collector rule."""

    policy_id: str
    authority_ref: str
    authenticated_at: datetime
    version_ranks: tuple[tuple[str, int], ...]

    def to_policy(self, cutoff: datetime) -> SupersessionPolicy | None:
        if not self.policy_id or not self.authority_ref or utc(self.authenticated_at) > utc(cutoff):
            return None
        ranks = dict(self.version_ranks)
        if len(ranks) != len(self.version_ranks) or any(not isinstance(v, int) for v in ranks.values()):
            return None
        return SupersessionPolicy(self.policy_id, ranks, self.authority_ref, utc(self.authenticated_at))


def build_prospective_snapshot(physical_symbol: str, origin: datetime,
                               records: Iterable[ProspectiveSourceVersion], *,
                               supersession: AuthenticatedSupersession | None = None) -> SnapshotResult:
    policy = supersession.to_policy(origin) if supersession else None
    return build_snapshot(physical_symbol, origin, (record.to_source_minute() for record in records),
                          mode=ASOF_VERIFIED, policy=policy)
