"""Persistent daily loss baseline and latch state."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class DailyLossRecord:
    trading_day: str
    baseline_equity: Decimal
    baseline_source: str
    baseline_observed_at: str
    latched: bool
    latched_at: str | None
    latched_rules_version_id: str | None
    latched_reason: str | None
    notified_at: str | None
    updated_at: str


class DailyLossStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3", *, initialize: bool = True) -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        if initialize:
            self._init_schema()

    def get_record(self, trading_day: str) -> DailyLossRecord | None:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM daily_loss_state WHERE trading_day = ?",
                    (trading_day,),
                ).fetchone()
        except sqlite3.Error:
            return None
        return None if row is None else _record_from_row(row)

    def ensure_baseline(
        self,
        *,
        trading_day: str,
        baseline_equity: Decimal,
        baseline_source: str,
        baseline_observed_at: str,
        updated_at: str,
    ) -> DailyLossRecord:
        if baseline_equity <= 0:
            raise ValueError("daily loss baseline requires positive equity")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO daily_loss_state (
                    trading_day, baseline_equity, baseline_source,
                    baseline_observed_at, latched, latched_at,
                    latched_rules_version_id, latched_reason, notified_at, updated_at
                ) VALUES (?, ?, ?, ?, 0, NULL, NULL, NULL, NULL, ?)
                """,
                (trading_day, str(baseline_equity), baseline_source, baseline_observed_at, updated_at),
            )
        record = self.get_record(trading_day)
        if record is None:
            raise RuntimeError("daily loss baseline was not persisted")
        return record

    def latch(
        self,
        *,
        trading_day: str,
        latched_at: str,
        rules_version_id: str,
        reason: str,
    ) -> DailyLossRecord:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE daily_loss_state
                SET latched = 1,
                    latched_at = COALESCE(latched_at, ?),
                    latched_rules_version_id = COALESCE(latched_rules_version_id, ?),
                    latched_reason = COALESCE(latched_reason, ?),
                    updated_at = ?
                WHERE trading_day = ?
                """,
                (latched_at, rules_version_id, reason, latched_at, trading_day),
            )
        record = self.get_record(trading_day)
        if record is None:
            raise RuntimeError("daily loss latch requires baseline")
        return record

    def mark_notified(self, *, trading_day: str, notified_at: str) -> DailyLossRecord:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE daily_loss_state
                SET notified_at = COALESCE(notified_at, ?), updated_at = ?
                WHERE trading_day = ?
                """,
                (notified_at, notified_at, trading_day),
            )
        record = self.get_record(trading_day)
        if record is None:
            raise RuntimeError("daily loss notification requires baseline")
        return record

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_loss_state (
                    trading_day TEXT PRIMARY KEY,
                    baseline_equity TEXT NOT NULL,
                    baseline_source TEXT NOT NULL,
                    baseline_observed_at TEXT NOT NULL,
                    latched INTEGER NOT NULL DEFAULT 0,
                    latched_at TEXT,
                    latched_rules_version_id TEXT,
                    latched_reason TEXT,
                    notified_at TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


def _record_from_row(row: sqlite3.Row) -> DailyLossRecord:
    return DailyLossRecord(
        trading_day=row["trading_day"],
        baseline_equity=Decimal(str(row["baseline_equity"])),
        baseline_source=row["baseline_source"],
        baseline_observed_at=row["baseline_observed_at"],
        latched=bool(row["latched"]),
        latched_at=row["latched_at"],
        latched_rules_version_id=row["latched_rules_version_id"],
        latched_reason=row["latched_reason"],
        notified_at=row["notified_at"],
        updated_at=row["updated_at"],
    )
