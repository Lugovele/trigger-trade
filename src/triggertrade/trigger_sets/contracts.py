"""Small versioned Trigger Set contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping


TRIGGER_REGISTRY_SCHEMA_VERSION = "trigger-definition@1"
TRIGGER_SET_REGISTRY_SCHEMA_VERSION = "trigger-set-composition@1"


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
    CONTEXT = "context"


@dataclass(frozen=True)
class RuleIdentity:
    rule_id: str
    name: str
    rule_type: RuleType
    asset_scope: str
    description: str
    created_at: str


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
    logical_name: str | None = None
    description: str | None = None
    supersedes_version: str | None = None
    formula: str | None = None
    parameter_snapshot: Mapping[str, Any] | None = None
    input_contract: Mapping[str, Any] | None = None
    output_contract: Mapping[str, Any] | None = None
    boundary_semantics: str | None = None
    stale_data_semantics: str | None = None
    missing_data_semantics: str | None = None
    semantic_hash: str | None = None
    change_summary: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class TriggerVersion(RuleDefinition):
    """Immutable semantic version of a code-defined trigger.

    The current persistence table is still named rule_definitions for
    compatibility because it also stores strategy, risk, and context versions.
    """


@dataclass(frozen=True)
class RuleVersion(RuleDefinition):
    """Immutable semantic version of a logical trading rule.

    RuleDefinition remains as a backwards-compatible name for the stored
    version record used by existing code.
    """


@dataclass(frozen=True)
class Recommendation:
    recommendation_id: str
    created_at: str
    status: str
    title: str
    observation_window_start: str | None
    observation_window_end: str | None
    source_set_versions: tuple[tuple[str, str], ...]
    source_rule_versions: tuple[tuple[str, str], ...]
    observation: str
    evidence: str
    hypothesis: str
    recommended_experiment: str
    proposed_rule_changes: Mapping[str, Any]
    proposed_trigger_set_definition: Mapping[str, Any]
    minimum_test_duration: str
    minimum_sample_size: str
    resulting_test_set_id: str | None = None
    resulting_test_set_version: str | None = None
    evaluation_summary: str | None = None
    decision: str | None = None
    closed_at: str | None = None


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


@dataclass(frozen=True)
class RegistrySyncReport:
    unchanged_versions: tuple[str, ...] = ()
    new_versions_registered: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    invalid_definitions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
