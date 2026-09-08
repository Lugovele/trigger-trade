import pytest
import sqlite3

from triggertrade.persistence import (
    TriggerSetStore,
    TriggerSetStoreError,
    composition_hash,
    current_active_trigger_set,
    current_futures_active_trigger_set,
    current_rule_definitions,
    current_testing_trigger_set,
    definition_hash,
)
from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType, TriggerSetStatus, TriggerSetVersion


def test_trigger_set_requires_version_status_and_membership(tmp_path):
    store = _store(tmp_path)
    trigger_set = current_active_trigger_set(created_at="2026-09-05T00:00:00+00:00")

    saved = store.create_set(trigger_set)

    assert saved.version == "v1"
    assert saved.status is TriggerSetStatus.ACTIVE
    assert saved.rule_versions == (("TRG-001", "0.1.0"), ("STR-001", "0.1.0"), ("RSK-PAPER-001", "0.1.0"))


def test_missing_version_or_unknown_rule_is_rejected(tmp_path):
    store = _store(tmp_path)
    missing_version = current_active_trigger_set(created_at="2026-09-05T00:00:00+00:00")
    missing_version = missing_version.__class__(**{**missing_version.__dict__, "version": ""})
    with pytest.raises(TriggerSetStoreError, match="version"):
        store.create_set(missing_version)

    unknown = current_testing_trigger_set(created_at="2026-09-05T00:00:00+00:00")
    unknown = unknown.__class__(**{**unknown.__dict__, "rule_versions": (("TRG-404", "0.1.0"),)})
    with pytest.raises(TriggerSetStoreError, match="unknown rule"):
        store.create_set(unknown)


def test_rule_and_set_versions_are_immutable(tmp_path):
    store = _store(tmp_path)
    rule = current_rule_definitions(created_at="2026-09-05T00:00:00+00:00")[0]
    mutated_rule = rule.__class__(**{**rule.__dict__, "condition": "changed"})
    with pytest.raises(TriggerSetStoreError, match="Version bump"):
        store.save_rule(mutated_rule)

    trigger_set = current_active_trigger_set(created_at="2026-09-05T00:00:00+00:00")
    store.create_set(trigger_set)
    mutated_set = trigger_set.__class__(**{**trigger_set.__dict__, "purpose": "changed"})
    with pytest.raises(TriggerSetStoreError, match="Version bump"):
        store.create_set(mutated_set)


def test_only_one_active_set_and_multiple_testing_sets_are_allowed(tmp_path):
    store = _store(tmp_path)
    store.create_set(current_active_trigger_set(created_at="2026-09-05T00:00:00+00:00"))
    second_active = current_active_trigger_set(created_at="2026-09-05T00:00:00+00:00")
    second_active = second_active.__class__(**{**second_active.__dict__, "set_id": "second-active", "version": "v2"})

    with pytest.raises(TriggerSetStoreError, match="only one ACTIVE"):
        store.create_set(second_active)

    first_testing = current_testing_trigger_set(created_at="2026-09-05T00:00:00+00:00")
    second_testing = first_testing.__class__(**{**first_testing.__dict__, "set_id": "second-testing", "version": "v2-test"})
    store.create_set(first_testing)
    store.create_set(second_testing)

    assert len(store.list_testing_sets("BTCUSDT", "1m")) == 2


def test_explicit_promotion_archives_previous_active(tmp_path):
    store = _store(tmp_path)
    active = store.create_set(current_active_trigger_set(created_at="2026-09-05T00:00:00+00:00"))
    testing = store.create_set(current_testing_trigger_set(created_at="2026-09-05T00:00:00+00:00"))

    promoted = store.transition_status(
        set_id=testing.set_id,
        version=testing.version,
        status=TriggerSetStatus.ACTIVE,
        changed_at="2026-09-05T01:00:00+00:00",
        reason="explicit reviewer-approved promotion",
    )

    assert promoted.status is TriggerSetStatus.ACTIVE
    assert store.get_set(active.set_id, active.version).status is TriggerSetStatus.ARCHIVE
    assert store.get_active_set("BTCUSDT", "1m").version == testing.version


def test_sync_registers_new_trigger_version_with_deterministic_definition_hash(tmp_path):
    store = _store(tmp_path)
    rule = _trigger_rule(version="0.3.0", threshold="1.5")

    report = store.sync_trigger_registry((rule,))

    saved = store.get_rule("TRG-X", "0.3.0")
    assert report.new_versions_registered == ("TRG-X@0.3.0",)
    assert saved.semantic_hash == definition_hash(rule)
    assert definition_hash(rule) == definition_hash(rule)


def test_sync_rejects_duplicate_trigger_version_with_changed_parameters(tmp_path):
    store = _store(tmp_path)
    first = _trigger_rule(version="0.3.0", threshold="1.5")
    changed = _trigger_rule(version="0.3.0", threshold="2.0")

    assert store.sync_trigger_registry((first,)).new_versions_registered == ("TRG-X@0.3.0",)
    report = store.sync_trigger_registry((changed,))

    assert report.conflicts
    assert "semantic definition changed without Trigger Version bump" in report.conflicts[0]
    assert store.get_rule("TRG-X", "0.3.0").definition["parameter_snapshot"]["threshold"] == "1.5"


def test_sync_accepts_new_trigger_version_without_mutating_old_version(tmp_path):
    store = _store(tmp_path)
    old = _trigger_rule(version="0.3.0", threshold="1.5")
    new = _trigger_rule(version="0.4.0", threshold="2.0")

    report = store.sync_trigger_registry((old, new))

    assert report.new_versions_registered == ("TRG-X@0.3.0", "TRG-X@0.4.0")
    assert store.get_rule("TRG-X", "0.3.0").definition["parameter_snapshot"]["threshold"] == "1.5"
    assert store.get_rule("TRG-X", "0.4.0").definition["parameter_snapshot"]["threshold"] == "2.0"


def test_set_sync_registers_exact_memberships_with_composition_hash(tmp_path):
    store = _store(tmp_path)
    store.save_rule(_trigger_rule(version="0.3.0", threshold="1.5"))
    trigger_set = _trigger_set(version="v3", rule_versions=(("TRG-X", "0.3.0"),))

    report = store.sync_trigger_sets((trigger_set,))

    assert report.new_versions_registered == ("set-x@v3",)
    assert store.get_set("set-x", "v3").rule_versions == (("TRG-X", "0.3.0"),)
    assert composition_hash(trigger_set) == composition_hash(trigger_set)


def test_set_sync_rejects_same_set_version_with_changed_membership_hash(tmp_path):
    store = _store(tmp_path)
    store.save_rule(_trigger_rule(version="0.3.0", threshold="1.5"))
    store.save_rule(_trigger_rule(version="0.4.0", threshold="2.0"))
    first = _trigger_set(version="v3", rule_versions=(("TRG-X", "0.3.0"),))
    changed = _trigger_set(version="v3", rule_versions=(("TRG-X", "0.4.0"),))

    store.create_set(first)
    report = store.sync_trigger_sets((changed,))

    assert report.conflicts
    assert "semantic composition changed without Set Version bump" in report.conflicts[0]
    assert store.get_set("set-x", "v3").rule_versions == (("TRG-X", "0.3.0"),)


def test_set_sync_rejects_missing_exact_trigger_version_reference(tmp_path):
    store = _store(tmp_path)

    report = store.sync_trigger_sets((_trigger_set(version="v3", rule_versions=(("TRG-X", "0.9.0"),)),))

    assert report.invalid_definitions
    assert "unknown rule version: TRG-X@0.9.0" in report.invalid_definitions[0]


def test_runtime_resolution_uses_set_exact_trigger_version_not_latest(tmp_path):
    store = _store(tmp_path)
    store.sync_trigger_registry((_trigger_rule(version="0.3.0", threshold="1.5"), _trigger_rule(version="0.4.0", threshold="2.0")))
    store.create_set(_trigger_set(version="v3", rule_versions=(("TRG-X", "0.3.0"),)))

    resolved = store.resolve_trigger_version(store.get_set("set-x", "v3"), "TRG-X")

    assert resolved.version == "0.3.0"
    assert resolved.definition["parameter_snapshot"]["threshold"] == "1.5"


def test_composition_hash_excludes_lifecycle_status(tmp_path):
    active = current_futures_active_trigger_set(created_at="2026-09-05T00:00:00+00:00")
    archived = active.__class__(**{**active.__dict__, "status": TriggerSetStatus.ARCHIVE})

    assert composition_hash(active) == composition_hash(archived)


def test_set_sync_fails_closed_when_persisted_memberships_do_not_match_stored_hash(tmp_path):
    store = _store(tmp_path)
    store.save_rule(_trigger_rule(version="0.3.0", threshold="1.5"))
    store.save_rule(_trigger_rule(version="0.4.0", threshold="2.0"))
    trigger_set = _trigger_set(version="v3", rule_versions=(("TRG-X", "0.3.0"),))
    store.create_set(trigger_set)

    with sqlite3.connect(store.path) as conn:
        conn.execute(
            """
            UPDATE trigger_set_memberships
            SET rule_version = '0.4.0'
            WHERE set_id = 'set-x' AND set_version = 'v3' AND rule_id = 'TRG-X'
            """
        )

    report = store.sync_trigger_sets((trigger_set,))

    assert report.conflicts
    assert "persisted trigger set membership does not match composition_hash" in report.conflicts[0]


def test_resolve_trigger_version_rejects_unverified_definition_hash(tmp_path):
    store = _store(tmp_path)
    store.save_rule(_trigger_rule(version="0.3.0", threshold="1.5"))
    trigger_set = store.create_set(_trigger_set(version="v3", rule_versions=(("TRG-X", "0.3.0"),)))
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE rule_definitions SET definition_hash = NULL WHERE rule_id = 'TRG-X' AND version = '0.3.0'"
        )

    with pytest.raises(TriggerSetStoreError, match="unverified trigger definition hash"):
        store.resolve_trigger_version(trigger_set, "TRG-X")


def _store(tmp_path):
    store = TriggerSetStore(tmp_path / "trigger_sets.sqlite3")
    for rule in current_rule_definitions(created_at="2026-09-05T00:00:00+00:00"):
        store.save_rule(rule)
    return store


def _trigger_rule(*, version: str, threshold: str) -> RuleDefinition:
    return RuleDefinition(
        rule_id="TRG-X",
        version=version,
        name="Example code-first trigger",
        status=RuleStatus.TESTING,
        asset_scope="BTCUSDT linear perpetual",
        rule_type=RuleType.TRIGGER,
        condition=f"example_metric >= {threshold}",
        definition={
            "implementation_key": "tests.ExampleTrigger",
            "formula": "example_metric >= threshold",
            "parameter_snapshot": {"threshold": threshold},
        },
        created_at="2026-09-08T00:00:00+00:00",
        provenance="unit test code-first definition",
    )


def _trigger_set(*, version: str, rule_versions: tuple[tuple[str, str], ...]) -> TriggerSetVersion:
    return TriggerSetVersion(
        set_id="set-x",
        version=version,
        purpose="Code-first set sync test",
        status=TriggerSetStatus.TESTING,
        symbol="BTCUSDT",
        timeframe="1m",
        rule_versions=rule_versions,
        strategy_version="STR-FUT-001@0.1.0",
        risk_profile_version="RSK-FUTURES-001@0.1.0",
        config_snapshot={"composition_mode": "ordered_all", "execution": "local_test_simulation"},
        created_at="2026-09-08T00:00:00+00:00",
        provenance="unit test code-first set definition",
    )
