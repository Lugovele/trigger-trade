"""Immutable one-minute source versions; no exchange or corpus access."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import isfinite
from typing import Mapping

MINUTE = timedelta(minutes=1)
SYMBOLS = ("BTCUSDT", "AVAXUSDT", "SUIUSDT", "1000PEPEUSDT")


def utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be UTC-aware")
    return value.astimezone(UTC)


def physical_symbol(value: str) -> str:
    return "1000PEPEUSDT" if value == "PEPEUSDT" else value


@dataclass(frozen=True)
class SourceMinute:
    physical_symbol: str
    interval_start: datetime
    interval_end: datetime
    open: float
    high: float
    low: float
    close: float
    version_id: str
    completed: bool
    collector_received_at: datetime | None = None
    collector_receipt_ref: str | None = None
    evidence_available_at: tuple[datetime, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    availability_contract_id: str | None = None
    completion_contract_id: str | None = None
    source_ref: str | None = None

    def __post_init__(self) -> None:
        for field in ("interval_start", "interval_end", "collector_received_at"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, utc(value))
        object.__setattr__(self, "evidence_available_at", tuple(utc(t) for t in self.evidence_available_at))
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        for field in ("open", "high", "low", "close"):
            object.__setattr__(self, field, float(getattr(self, field)))
        if not self.version_id:
            raise ValueError("version identity required")
        if not isinstance(self.completed, bool):
            raise ValueError("completed must be a boolean, not a truthy status string")

    @property
    def source_available_at(self) -> datetime | None:
        if (self.collector_received_at is None or not self.collector_receipt_ref or
                not self.availability_contract_id or not self.evidence_available_at or not self.evidence_refs):
            return None
        if len(self.evidence_available_at) != len(self.evidence_refs):
            return None
        available = max(self.collector_received_at, *self.evidence_available_at)
        return available if available >= self.interval_end else None

    @property
    def valid_ohlc(self) -> bool:
        o, h, l, c = self.open, self.high, self.low, self.close
        return all(isfinite(x) and x > 0 for x in (o, h, l, c)) and l <= o <= h and l <= c <= h

    @classmethod
    def from_historical_row(cls, row: Mapping[str, object], *, version_id: str,
                            source_ref: str | None = None,
                            completion_contract_id: str | None = None) -> SourceMinute:
        """Parse the repository's decimal-text CSV OHLC directly to binary64.

        The canonical CSV reader also ends with float64 OHLC. This adapter
        does not invent historical receipt/finalization timestamps.
        """
        start = datetime.fromisoformat(str(row["open_time"]).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(row["close_time"]).replace("Z", "+00:00"))
        # Historical corpus uses exclusive closes. A provider's explicit
        # last-millisecond stamp is normalized to the same exclusive end.
        if end == start + timedelta(milliseconds=59_999):
            end = start + MINUTE
        if "completed" in row:
            completed = row["completed"]
        elif completion_contract_id:
            # The repository's historical CSV omits a per-row completed flag;
            # its verified final-vintage dataset contract must be supplied.
            completed = True
        else:
            raise ValueError("historical row lacks completion evidence")
        return cls(
            physical_symbol=str(row["symbol"]), interval_start=start, interval_end=end,
            open=float(str(row["open"])), high=float(str(row["high"])),
            low=float(str(row["low"])), close=float(str(row["close"])),
            version_id=version_id, completed=completed, source_ref=source_ref,
            completion_contract_id=completion_contract_id,
        )
