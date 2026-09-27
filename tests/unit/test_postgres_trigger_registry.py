from __future__ import annotations

import json
import os
from pathlib import Path
import uuid

import pytest

from triggertrade.persistence import (
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresTriggerRegistry,
    PostgresTriggerRegistryError,
    PostgresUnitOfWork,
    TriggerSetStoreError,
    current_rule_definitions,
    definition_hash,
    apply_postgres_migrations,
)
from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType
from triggertrade.triggers import implementation_exists, implementation_key
from triggertrade.triggers.declarative_metric_predicate import DeclarativeMetricPredicateConfig


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_trigreg_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def _migrate(settings: PostgresSettings) -> PostgresConnectionFactory:
    applied = apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
    assert applied[-1].version == "0024"
    assert apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema) == ()
    return PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)


def test_postgres_trigger_registry_creates_reimports_and_rejects_conflicts():
    settings = _settings()
    try:
        factory = _migrate(settings)
        rule = _trigger_rule(version="1.0.0", threshold="1.5")
        changed = _trigger_rule(version="1.0.0", threshold="2.0")

        with PostgresUnitOfWork(factory) as uow:
            store = PostgresTriggerRegistry(uow.connection)
            report = store.sync_trigger_registry((rule,))
            assert report.new_versions_registered == ("TRG-PG@1.0.0",)
            saved = store.get_trigger_version("TRG-PG", "1.0.0")
            assert saved is not None
            assert saved.semantic_hash == definition_hash(rule)
            assert saved.definition["parameter_snapshot"]["threshold"] == "1.5"

        with PostgresUnitOfWork(factory) as uow:
            store = PostgresTriggerRegistry(uow.connection)
            exact = store.sync_trigger_registry((rule,))
            conflict = store.sync_trigger_registry((changed,))
            assert exact.unchanged_versions == ("TRG-PG@1.0.0",)
            assert conflict.conflicts
            assert "semantic definition changed without Trigger Version bump" in conflict.conflicts[0]
            assert store.get_exact_rule("TRG-PG", "1.0.0").definition["parameter_snapshot"]["threshold"] == "1.5"
    finally:
        _drop_schema(settings)


def test_postgres_trigger_registry_lists_versions_and_preserves_current_bootstrap_triggers():
    settings = _settings()
    try:
        factory = _migrate(settings)
        bootstrap_rules = current_rule_definitions(created_at="2026-09-05T00:00:00+00:00")
        with PostgresUnitOfWork(factory) as uow:
            store = PostgresTriggerRegistry(uow.connection)
            report = store.sync_trigger_registry(bootstrap_rules)
            assert ("TRG-001@0.2.0" in report.new_versions_registered)
            assert ("TRG-002@0.2.0" in report.new_versions_registered)
            all_rules = store.list_rules()
            trigger_versions = store.list_trigger_versions()
            assert len(all_rules) == len(bootstrap_rules)
            assert {rule.rule_id for rule in trigger_versions} >= {"TRG-001", "TRG-002"}
            assert store.get_rule("TRG-001", "0.2.0").semantic_hash == definition_hash(
                next(rule for rule in bootstrap_rules if rule.rule_id == "TRG-001" and rule.version == "0.2.0")
            )
    finally:
        _drop_schema(settings)


def test_postgres_trigger_registry_rejects_invalid_trigger_definitions():
    settings = _settings()
    try:
        factory = _migrate(settings)
        missing_implementation = RuleDefinition(
            rule_id="TRG-BAD",
            version="1.0.0",
            name="Invalid trigger",
            status=RuleStatus.DRAFT,
            asset_scope="BTCUSDT",
            rule_type=RuleType.TRIGGER,
            condition="metric >= 1",
            definition={},
            created_at="2026-09-27T00:00:00+00:00",
            provenance="unit test",
        )
        bad_hash = _trigger_rule(version="1.0.0", threshold="1.5")
        bad_hash = RuleDefinition(**{**bad_hash.__dict__, "semantic_hash": "not-the-current-digest"})

        with PostgresUnitOfWork(factory) as uow:
            store = PostgresTriggerRegistry(uow.connection)
            with pytest.raises(TriggerSetStoreError, match="implementation_key is required"):
                store.save_rule(missing_implementation)
            with pytest.raises(PostgresTriggerRegistryError, match="definition_hash does not match"):
                store.save_rule(bad_hash)
    finally:
        _drop_schema(settings)


def test_research_v1_trigger_package_imports_idempotently_into_postgres_registry():
    settings = _settings()
    try:
        factory = _migrate(settings)
        records = _research_v1_rules()
        assert len(records) == 31
        assert len({(rule.rule_id, rule.version) for rule in records}) == 31
        for rule in records:
            assert implementation_exists(implementation_key(rule))
            DeclarativeMetricPredicateConfig.from_rule(rule)

        with PostgresUnitOfWork(factory) as uow:
            store = PostgresTriggerRegistry(uow.connection)
            first = store.sync_trigger_registry(records)
            assert len(first.new_versions_registered) == 31
            assert first.conflicts == ()
            assert first.invalid_definitions == ()

        with PostgresUnitOfWork(factory) as uow:
            store = PostgresTriggerRegistry(uow.connection)
            second = store.sync_trigger_registry(records)
            assert len(second.unchanged_versions) == 31
            assert second.new_versions_registered == ()
            assert second.conflicts == ()
            assert second.invalid_definitions == ()
            assert len(store.list_trigger_versions()) == 31
            assert all(store.get_trigger_version(rule.rule_id, rule.version) is not None for rule in records)
            assert all(
                saved.semantic_hash == definition_hash(saved)
                for rule in records
                if (saved := store.get_trigger_version(rule.rule_id, rule.version)) is not None
            )
    finally:
        _drop_schema(settings)


def test_corrected_btc_direction_trigger_versions_import_idempotently_into_postgres_registry():
    settings = _settings()
    try:
        factory = _migrate(settings)
        records = tuple(
            rule for rule in _research_v1_rules() if rule.rule_id in {"TR-R-BTC-001", "TR-R-BTC-002", "TR-R-BTC-003", "TR-R-BTC-004"}
        )
        assert len(records) == 4
        assert {rule.version for rule in records} == {"1.0.1"}
        assert {rule.supersedes_version for rule in records} == {"1.0.0"}
        assert {
            rule.rule_id: tuple(rule.definition["output_states"]) for rule in records
        } == {
            "TR-R-BTC-001": ("LONG", "ZERO", "UNAVAILABLE"),
            "TR-R-BTC-002": ("SHORT", "ZERO", "UNAVAILABLE"),
            "TR-R-BTC-003": ("LONG", "ZERO", "UNAVAILABLE"),
            "TR-R-BTC-004": ("SHORT", "ZERO", "UNAVAILABLE"),
        }

        with PostgresUnitOfWork(factory) as uow:
            store = PostgresTriggerRegistry(uow.connection)
            first = store.sync_trigger_registry(records)
            assert len(first.new_versions_registered) == 4
            assert first.conflicts == ()
            assert first.invalid_definitions == ()

        with PostgresUnitOfWork(factory) as uow:
            store = PostgresTriggerRegistry(uow.connection)
            second = store.sync_trigger_registry(records)
            assert len(second.unchanged_versions) == 4
            assert second.new_versions_registered == ()
            assert second.conflicts == ()
            assert second.invalid_definitions == ()
            assert all(store.get_trigger_version(rule.rule_id, "1.0.1") is not None for rule in records)
            assert all(store.get_trigger_version(rule.rule_id, "1.0.0") is None for rule in records)
    finally:
        _drop_schema(settings)


def _trigger_rule(*, version: str, threshold: str) -> RuleDefinition:
    return RuleDefinition(
        rule_id="TRG-PG",
        version=version,
        name="Postgres trigger registry test",
        status=RuleStatus.TESTING,
        asset_scope="BTCUSDT linear perpetual",
        rule_type=RuleType.TRIGGER,
        condition=f"example_metric >= {threshold}",
        definition={
            "implementation_key": "tests.ExampleTrigger",
            "formula": "example_metric >= threshold",
            "parameter_snapshot": {"threshold": threshold},
        },
        created_at="2026-09-27T00:00:00+00:00",
        provenance="unit test",
    )


def _research_v1_rules() -> tuple[RuleDefinition, ...]:
    package = json.loads(Path("docs/research-import/triggers/RESEARCH_V1_TRIGGERS_WEB_IMPORT.json").read_text(encoding="utf-8"))
    rules: list[RuleDefinition] = []
    for record in package["records"]:
        data = dict(record["rule_definition"])
        # The production store owns the canonical digest calculation. The R3
        # import artifact carries a historical digest field that is validation
        # evidence, not trusted mutable input for this persistence boundary.
        data.pop("semantic_hash", None)
        data["status"] = RuleStatus(data["status"])
        data["rule_type"] = RuleType(data["rule_type"])
        rules.append(RuleDefinition(**data))
    return tuple(rules)
