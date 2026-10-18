"""Sealed diagnostic status metadata; never a primary-readiness dependency."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
import json
import re

from . import SPEC_ID, SPEC_VERSION
from .calendar import FIT_DEFINITIONS, iso, utc
from .manifests import canonical_json, digest

_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
ROLES = {"C1_SHALLOW_RF", "SIX_MONTH_ROLLING_SHADOW"}
STATUSES = {"FITTED", "FIT_FAILED", "NOT_ASSESSED"}


@dataclass(frozen=True)
class ReportOnlyStatus:
    spec_id: str
    spec_version: str
    role: str
    horizon_minutes: int
    fit_id: str
    status: str
    reason: str
    primary_bundle_sha256: str
    artifact_sha256: str | None
    artifact_available_at: str | None
    evidence_ref: str | None
    status_sha256: str

    def body(self) -> dict[str, object]:
        body = asdict(self)
        body.pop("status_sha256")
        return body

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    @classmethod
    def from_json(cls, value: str) -> ReportOnlyStatus:
        result = cls(**json.loads(value))
        result.verify()
        return result

    def verify(self) -> None:
        if (self.spec_id != SPEC_ID or self.spec_version != SPEC_VERSION or
                self.role not in ROLES or self.horizon_minutes not in (60, 120) or
                self.fit_id not in FIT_DEFINITIONS or self.status not in STATUSES or
                not _HEX64.fullmatch(self.primary_bundle_sha256) or
                not _HEX64.fullmatch(self.status_sha256) or self.status_sha256 != digest(self.body())):
            raise ValueError("report-only status contract or hash mismatch")
        if self.status == "FITTED":
            if (not self.artifact_sha256 or not _HEX64.fullmatch(self.artifact_sha256) or
                    not self.artifact_available_at or not self.evidence_ref):
                raise ValueError("fitted diagnostic requires artifact and actual availability evidence")
            from datetime import datetime as _datetime
            utc(_datetime.fromisoformat(self.artifact_available_at.replace("Z", "+00:00")))
        elif self.artifact_sha256 is not None or self.artifact_available_at is not None or not self.reason:
            raise ValueError("unfitted diagnostic requires reason and no fabricated artifact")


def seal_report_only_status(*, role: str, horizon_minutes: int, fit_id: str,
                            status: str, reason: str, primary_bundle_sha256: str,
                            artifact_sha256: str | None = None,
                            artifact_available_at: datetime | None = None,
                            evidence_ref: str | None = None) -> ReportOnlyStatus:
    provisional = ReportOnlyStatus(
        SPEC_ID, SPEC_VERSION, role, horizon_minutes, fit_id, status, reason,
        primary_bundle_sha256, artifact_sha256,
        iso(artifact_available_at) if artifact_available_at is not None else None,
        evidence_ref, "")
    result = replace(provisional, status_sha256=digest(provisional.body()))
    result.verify()
    return result
