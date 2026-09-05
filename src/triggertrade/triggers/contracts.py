"""Trigger contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping


class SignalType(StrEnum):
    BUY_CANDIDATE = "BUY_CANDIDATE"
    NO_SIGNAL = "NO_SIGNAL"


@dataclass(frozen=True)
class Signal:
    signal_id: str
    trigger_rule_id: str
    trigger_rule_version: str
    symbol: str
    observed_at: str
    window: str
    input_snapshot: Mapping[str, str]
    condition_result: bool
    signal_type: SignalType
    reason: str | None = None
    lane: str | None = None
    trigger_set_id: str | None = None
    trigger_set_version: str | None = None
