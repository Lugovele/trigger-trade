"""Minimal exchange contracts isolated from trigger/strategy/risk layers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExchangeHealth:
    name: str
    reachable: bool


class ExchangeAdapter(Protocol):
    def health(self) -> ExchangeHealth:
        """Return adapter health without exposing exchange SDK details."""
