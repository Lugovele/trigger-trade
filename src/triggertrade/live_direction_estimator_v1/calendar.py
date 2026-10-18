"""Immutable UTC calendar and pure LDE V1 temporal eligibility rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import IntEnum

PURGE = timedelta(minutes=120)
FIVE_MINUTES = timedelta(minutes=5)
D0 = datetime(2024, 10, 2, tzinfo=UTC)
H1_START = datetime(2026, 7, 1, tzinfo=UTC)
H1_END = datetime(2026, 10, 1, tzinfo=UTC)
DECLARED_HISTORICAL_SOURCE_END = datetime(2026, 9, 30, tzinfo=UTC)


class Horizon(IntEnum):
    E60 = 60
    E120 = 120


def utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timezone-aware UTC datetime required")
    return value.astimezone(UTC)


def origin(value: datetime) -> datetime:
    result = utc(value)
    if result.minute % 5 or result.second or result.microsecond:
        raise ValueError("prediction origin must lie on the exact UTC five-minute grid")
    return result


def iso(value: datetime) -> str:
    return utc(value).isoformat(timespec="microseconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class SegmentDefinition:
    kind: str
    nominal_start: datetime
    nominal_end: datetime
    right_embargo: bool
    left_purge: bool

    def __post_init__(self) -> None:
        if self.kind not in {"BASE", "CALIBRATION", "SCORE", "H1", "PROSPECTIVE"}:
            raise ValueError("unsupported segment kind")
        if origin(self.nominal_start) >= origin(self.nominal_end):
            raise ValueError("invalid segment bounds")

    def contains(self, timestamp: datetime) -> bool:
        t = origin(timestamp)
        lower = self.nominal_start + (PURGE if self.right_embargo else timedelta(0))
        if t < lower:
            return False
        return t + PURGE < self.nominal_end if self.left_purge else t < self.nominal_end

    @property
    def inequality(self) -> str:
        left = f"t >= {iso(self.nominal_start + (PURGE if self.right_embargo else timedelta(0)))}"
        right = (f"t + 120m < {iso(self.nominal_end)}" if self.left_purge
                 else f"t < {iso(self.nominal_end)}")
        return f"{left} AND {right}"


@dataclass(frozen=True)
class FoldDefinition:
    fit_id: str
    base: SegmentDefinition
    calibration: SegmentDefinition
    score: SegmentDefinition | None

    def __post_init__(self) -> None:
        if self.fit_id not in {"F1", "F2", "F3", "F4", "F5", "FINAL"}:
            raise ValueError("unsupported fit ID")
        if self.base.kind != "BASE" or self.calibration.kind != "CALIBRATION":
            raise ValueError("invalid fold segments")
        if self.fit_id == "FINAL" and self.score is not None:
            raise ValueError("FINAL has no development score segment")
        if self.fit_id != "FINAL" and (self.score is None or self.score.kind != "SCORE"):
            raise ValueError("development fold needs a scored segment")

    def segment(self, kind: str) -> SegmentDefinition:
        match = {"BASE": self.base, "CALIBRATION": self.calibration, "SCORE": self.score}
        if kind not in match or match[kind] is None:
            raise ValueError("segment unavailable for this fit")
        return match[kind]


def _date(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


def _fold(fit_id: str, c: datetime, v: datetime, e: datetime | None) -> FoldDefinition:
    return FoldDefinition(fit_id,
                          SegmentDefinition("BASE", D0, c, False, True),
                          SegmentDefinition("CALIBRATION", c, v, True, True),
                          SegmentDefinition("SCORE", v, e, True, True) if e else None)


FOLDS = (
    _fold("F1", _date(2025, 3, 1), _date(2025, 4, 1), _date(2025, 7, 1)),
    _fold("F2", _date(2025, 6, 1), _date(2025, 7, 1), _date(2025, 10, 1)),
    _fold("F3", _date(2025, 9, 1), _date(2025, 10, 1), _date(2026, 1, 1)),
    _fold("F4", _date(2025, 12, 1), _date(2026, 1, 1), _date(2026, 4, 1)),
    _fold("F5", _date(2026, 3, 1), _date(2026, 4, 1), _date(2026, 7, 1)),
)
FINAL = _fold("FINAL", _date(2026, 6, 1), _date(2026, 7, 1), None)
FIT_DEFINITIONS = {fold.fit_id: fold for fold in (*FOLDS, FINAL)}


@dataclass(frozen=True)
class H1Governance:
    nominal_start: datetime = H1_START
    nominal_end: datetime = H1_END
    declared_source_end: datetime = DECLARED_HISTORICAL_SOURCE_END
    cleanliness_status: str = "CLEANLINESS_UNVERIFIED"
    audit_evidence_ref: str | None = None
    prior_exposure_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (self.nominal_start, self.nominal_end, self.declared_source_end) != (
                H1_START, H1_END, DECLARED_HISTORICAL_SOURCE_END):
            raise ValueError("H1 dates/source limitation are frozen")
        if self.cleanliness_status not in {"ESTIMATOR_RESERVED_CLEAN", "CONTAMINATED", "CLEANLINESS_UNVERIFIED"}:
            raise ValueError("invalid H1 cleanliness status")
        if self.cleanliness_status != "CLEANLINESS_UNVERIFIED" and not self.audit_evidence_ref:
            raise ValueError("affirmative audit evidence reference required")


def ceil_5m(value: datetime) -> datetime:
    value = utc(value)
    day_start = value.replace(hour=0, minute=0, second=0, microsecond=0)
    since = value - day_start
    microseconds = since.seconds * 1_000_000 + since.microseconds
    slots = microseconds // (300 * 1_000_000)
    candidate = day_start + slots * FIVE_MINUTES
    return candidate if candidate == value else candidate + FIVE_MINUTES


@dataclass(frozen=True)
class ReadinessEvidence:
    horizon_minutes: int
    kind: str
    ready_at: datetime
    evidence_ref: str
    authentication_status: str = "UNVERIFIED"

    def __post_init__(self) -> None:
        Horizon(self.horizon_minutes)
        utc(self.ready_at)
        if self.kind not in {"FINAL_ARTIFACT", "COLLECTOR"} or not self.evidence_ref:
            raise ValueError("readiness kind and evidence reference required")
        if self.authentication_status not in {"UNVERIFIED", "AUTHENTICATED", "SYNTHETIC_FIXTURE"}:
            raise ValueError("invalid readiness authentication status")


@dataclass(frozen=True)
class ProspectiveSchedule:
    horizon_minutes: int
    final_ready: ReadinessEvidence
    collector_ready: ReadinessEvidence
    start: datetime
    end: datetime
    outcome_seal: datetime
    registration_status: str = "UNREGISTERED"

    @property
    def operationally_registrable(self) -> bool:
        return (self.final_ready.authentication_status == "AUTHENTICATED" and
                self.collector_ready.authentication_status == "AUTHENTICATED")


def schedule_prospective(final_ready: ReadinessEvidence,
                         collector_ready: ReadinessEvidence) -> ProspectiveSchedule:
    if (final_ready.kind != "FINAL_ARTIFACT" or collector_ready.kind != "COLLECTOR" or
            final_ready.horizon_minutes != collector_ready.horizon_minutes):
        raise ValueError("independent same-horizon final and collector readiness required")
    start = ceil_5m(max(utc(final_ready.ready_at), utc(collector_ready.ready_at)) + PURGE)
    end = start + timedelta(days=90)
    return ProspectiveSchedule(final_ready.horizon_minutes, final_ready, collector_ready,
                               start, end, end + timedelta(days=7))
