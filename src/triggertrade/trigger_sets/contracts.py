"""Small versioned Trigger Set contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping


class Lane(StrEnum):
    ACTIVE = "ACTIVE"
    TEST = "TEST"


class RuleStatus(StrEnum):
    DRAFT = "DRAFT"
    TESTING = "TESTING"
    ACTIVE = "ACTIVE"
    ARCHIVE = "ARCHIVE"


class TriggerSetStatus(StrEnum):
    DRAFT = "DRAFT"
    TESTING = "TESTING"
    ACTIVE = "ACTIVE"
    ARCHIVE = "ARCHIVE"


class RuleType(StrEnum):
    TRIGGER = "trigger"
    STRATEGY = "strategy"
    RISK = "risk"


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    version: str
    name: str
    status: RuleStatus
    asset_scope: str
    rule_type: RuleType
    condition: str
    definition: Mapping[str, str]
    created_at: str
    provenance: str
    updated_at: str | None = None


@dataclass(frozen=True)
class TriggerSetVersion:
    set_id: str
    version: str
    purpose: str
    status: TriggerSetStatus
    symbol: str
    timeframe: str
    rule_versions: tuple[tuple[str, str], ...]
    strategy_version: str
    risk_profile_version: str
    config_snapshot: Mapping[str, str]
    created_at: str
    provenance: str
