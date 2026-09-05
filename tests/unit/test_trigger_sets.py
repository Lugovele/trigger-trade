import pytest

from triggertrade.persistence import (
    TriggerSetStore,
    TriggerSetStoreError,
    current_active_trigger_set,
    current_rule_definitions,
    current_testing_trigger_set,
)
from triggertrade.trigger_sets import TriggerSetStatus


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
    with pytest.raises(TriggerSetStoreError, match="immutable"):
        store.save_rule(mutated_rule)

    trigger_set = current_active_trigger_set(created_at="2026-09-05T00:00:00+00:00")
    store.create_set(trigger_set)
    mutated_set = trigger_set.__class__(**{**trigger_set.__dict__, "purpose": "changed"})
    with pytest.raises(TriggerSetStoreError, match="immutable"):
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


def _store(tmp_path):
    store = TriggerSetStore(tmp_path / "trigger_sets.sqlite3")
    for rule in current_rule_definitions(created_at="2026-09-05T00:00:00+00:00"):
        store.save_rule(rule)
    return store
