"""PostgreSQL persistence for immutable rule and trigger definitions."""

from __future__ import annotations

import json
from typing import Iterable

from triggertrade.persistence.postgres import PostgresPersistenceError
from triggertrade.persistence.trigger_set_store import (
    TriggerSetStoreError,
    _rule_definition_payload,
    _validate_rule_definition,
    definition_hash,
)
from triggertrade.trigger_sets import (
    TRIGGER_REGISTRY_SCHEMA_VERSION,
    RegistrySyncReport,
    RuleDefinition,
    RuleStatus,
    RuleType,
)


class PostgresTriggerRegistryError(PostgresPersistenceError):
    """Raised when PostgreSQL trigger definition persistence cannot proceed."""


class PostgresTriggerRegistry:
    """Immutable RuleDefinition registry backed by PostgreSQL.

    This mirrors the standalone rule-definition semantics of TriggerSetStore:
    absent versions are inserted, exact replays are unchanged, and changed
    semantic content under the same rule_id/version fails closed.
    """

    def __init__(self, connection) -> None:
        self._connection = connection

    def save_rule(self, rule: RuleDefinition) -> RuleDefinition:
        self._save_rule_result(rule)
        return rule

    def save_trigger_version(self, rule: RuleDefinition) -> RuleDefinition:
        if rule.rule_type is not RuleType.TRIGGER:
            raise PostgresTriggerRegistryError("trigger version must have rule_type=trigger")
        return self.save_rule(rule)

    def register_trigger_definitions(self, rules: Iterable[RuleDefinition]) -> RegistrySyncReport:
        return self.sync_trigger_registry(rules)

    def sync_trigger_registry(self, rules: Iterable[RuleDefinition]) -> RegistrySyncReport:
        unchanged: list[str] = []
        registered: list[str] = []
        conflicts: list[str] = []
        invalid: list[str] = []
        for rule in rules:
            try:
                result = self._save_rule_result(rule)
            except (TriggerSetStoreError, PostgresTriggerRegistryError) as exc:
                message = f"{rule.rule_id}@{rule.version}: {exc}"
                if "invalid" in str(exc) or "required" in str(exc) or "must use" in str(exc):
                    invalid.append(message)
                else:
                    conflicts.append(message)
            else:
                (unchanged if result == "unchanged" else registered).append(f"{rule.rule_id}@{rule.version}")
        return RegistrySyncReport(tuple(unchanged), tuple(registered), tuple(conflicts), tuple(invalid), ())

    def get_rule(self, rule_id: str, version: str | None = None) -> RuleDefinition | None:
        with self._connection.cursor() as cursor:
            if version is None:
                cursor.execute(
                    """
                    SELECT rule_id, version, name, status, asset_scope, rule_type,
                           condition, definition_json::text, definition_hash,
                           schema_version, created_at, updated_at, provenance
                    FROM triggertrade_rule_definitions
                    WHERE rule_id = %s
                    ORDER BY created_at DESC, version DESC
                    LIMIT 1
                    """,
                    (rule_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT rule_id, version, name, status, asset_scope, rule_type,
                           condition, definition_json::text, definition_hash,
                           schema_version, created_at, updated_at, provenance
                    FROM triggertrade_rule_definitions
                    WHERE rule_id = %s AND version = %s
                    """,
                    (rule_id, version),
                )
            row = cursor.fetchone()
        return None if row is None else _row_to_rule(row)

    def get_trigger_version(self, trigger_id: str, version: str) -> RuleDefinition | None:
        rule = self.get_rule(trigger_id, version)
        if rule is None or rule.rule_type is not RuleType.TRIGGER:
            return None
        return rule

    def get_exact_rule(self, rule_id: str, version: str) -> RuleDefinition:
        rule = self.get_rule(rule_id, version)
        if rule is None:
            raise PostgresTriggerRegistryError(f"unknown rule version: {rule_id}@{version}")
        return rule

    def list_rules(self) -> tuple[RuleDefinition, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT rule_id, version, name, status, asset_scope, rule_type,
                       condition, definition_json::text, definition_hash,
                       schema_version, created_at, updated_at, provenance
                FROM triggertrade_rule_definitions
                ORDER BY rule_id, version
                """
            )
            rows = cursor.fetchall()
        return tuple(_row_to_rule(row) for row in rows)

    def list_trigger_versions(self) -> tuple[RuleDefinition, ...]:
        return tuple(rule for rule in self.list_rules() if rule.rule_type is RuleType.TRIGGER)

    def list_rule_versions(self, rule_id: str) -> tuple[RuleDefinition, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT rule_id, version, name, status, asset_scope, rule_type,
                       condition, definition_json::text, definition_hash,
                       schema_version, created_at, updated_at, provenance
                FROM triggertrade_rule_definitions
                WHERE rule_id = %s
                ORDER BY created_at DESC, version DESC
                """,
                (rule_id,),
            )
            rows = cursor.fetchall()
        return tuple(_row_to_rule(row) for row in rows)

    def _save_rule_result(self, rule: RuleDefinition) -> str:
        _validate_rule_definition(rule)
        definition_payload = _rule_definition_payload(rule)
        definition_text = json.dumps(definition_payload, sort_keys=True)
        rule_hash = definition_hash(rule)
        if rule.semantic_hash is not None and rule.semantic_hash != rule_hash:
            raise PostgresTriggerRegistryError("definition_hash does not match canonical trigger definition")
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT rule_id, version, status, condition, definition_json::text,
                       definition_hash
                FROM triggertrade_rule_definitions
                WHERE rule_id = %s AND version = %s
                """,
                (rule.rule_id, rule.version),
            )
            existing = cursor.fetchone()
            if existing is not None:
                existing_definition = json.loads(str(existing[4]))
                if (
                    str(existing[5]) != rule_hash
                    or str(existing[2]) != rule.status.value
                    or str(existing[3]) != rule.condition
                    or existing_definition != definition_payload
                ):
                    raise PostgresTriggerRegistryError("semantic definition changed without Trigger Version bump")
                return "unchanged"
            cursor.execute(
                """
                INSERT INTO triggertrade_rule_definitions (
                    rule_id, version, name, status, asset_scope, rule_type,
                    condition, definition_json, definition_hash, schema_version,
                    created_at, updated_at, provenance
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
                """,
                (
                    rule.rule_id,
                    rule.version,
                    rule.name,
                    rule.status.value,
                    rule.asset_scope,
                    rule.rule_type.value,
                    rule.condition,
                    definition_text,
                    rule_hash,
                    TRIGGER_REGISTRY_SCHEMA_VERSION,
                    rule.created_at,
                    rule.updated_at,
                    rule.provenance,
                ),
            )
        return "registered"


def _row_to_rule(row) -> RuleDefinition:
    definition = json.loads(str(row[7]))
    metadata = definition.pop("_version_metadata", None)
    if not isinstance(metadata, dict):
        metadata = {}
    return RuleDefinition(
        rule_id=str(row[0]),
        version=str(row[1]),
        name=str(row[2]),
        status=RuleStatus(str(row[3])),
        asset_scope=str(row[4]),
        rule_type=RuleType(str(row[5])),
        condition=str(row[6]),
        definition=definition,
        semantic_hash=str(row[8]),
        created_at=str(row[10]),
        updated_at=None if row[11] is None else str(row[11]),
        provenance=str(row[12]),
        logical_name=metadata.get("logical_name"),
        description=metadata.get("description"),
        supersedes_version=metadata.get("supersedes_version"),
        formula=metadata.get("formula"),
        parameter_snapshot=metadata.get("parameter_snapshot"),
        input_contract=metadata.get("input_contract"),
        output_contract=metadata.get("output_contract"),
        boundary_semantics=metadata.get("boundary_semantics"),
        stale_data_semantics=metadata.get("stale_data_semantics"),
        missing_data_semantics=metadata.get("missing_data_semantics"),
        change_summary=metadata.get("change_summary"),
    )
