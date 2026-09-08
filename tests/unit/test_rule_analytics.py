import pytest

from triggertrade.persistence import (
    TriggerSetStore,
    TriggerSetStoreError,
    bootstrap_current_trigger_sets,
    current_rule_definitions,
)
from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleVersion, TriggerSetStatus, TriggerSetVersion


def test_rule_versions_are_lookupable_and_immutable(tmp_path):
    store = TriggerSetStore(tmp_path / "rules.sqlite3")
    for rule in current_rule_definitions(created_at="2026-09-05T00:00:00+00:00"):
        store.save_rule(rule)

    trg2 = store.get_rule("TRG-002", "0.1.0")
    assert trg2 is not None
    assert trg2.status is RuleStatus.TESTING
    assert trg2.definition["logical_name"] == "TRG-VOLUME"
    assert issubclass(RuleVersion, RuleDefinition)

    mutated = RuleDefinition(**{**trg2.__dict__, "condition": "relative_volume >= 1.7"})
    with pytest.raises(TriggerSetStoreError, match="definition_hash"):
        store.save_rule(mutated)


def test_candidate_set_references_exact_volume_rule_version_without_active_mutation(tmp_path):
    store = TriggerSetStore(tmp_path / "sets.sqlite3")
    bootstrap_current_trigger_sets(store, created_at="2026-09-05T00:00:00+00:00")

    active = store.get_active_set("BTCUSDT", "1m")
    spot_candidate = store.get_set("triggertrade-core-candidate", "v2-test")
    candidate = store.get_set("triggertrade-futures-candidate", "v2-test")

    assert active.rule_versions == (
        ("TRG-001", "0.2.0"),
        ("STR-FUT-001", "0.1.0"),
        ("RSK-FUTURES-001", "0.1.0"),
        ("CTX-REGIME", "0.1.0"),
    )
    assert active.status is TriggerSetStatus.ACTIVE
    assert spot_candidate.status is TriggerSetStatus.ARCHIVE
    assert candidate.status is TriggerSetStatus.TESTING
    assert ("TRG-002", "0.2.0") in candidate.rule_versions



def test_bootstrap_adds_new_candidate_version_over_legacy_v1_test(tmp_path):
    store = TriggerSetStore(tmp_path / "sets.sqlite3")
    created_at = "2026-09-05T00:00:00+00:00"
    for rule in current_rule_definitions(created_at=created_at):
        store.save_rule(rule)
    store.create_set(
        TriggerSetVersion(
            set_id="triggertrade-core-candidate",
            version="v1-test",
            purpose="Legacy candidate set before TRG-002 volume experiment",
            status=TriggerSetStatus.TESTING,
            symbol="BTCUSDT",
            timeframe="1m",
            rule_versions=(("TRG-001", "0.1.0"), ("STR-001", "0.1.0"), ("RSK-PAPER-001", "0.1.0")),
            strategy_version="STR-001@0.1.0",
            risk_profile_version="RSK-PAPER-001@0.1.0",
            config_snapshot={"legacy": "true"},
            created_at=created_at,
            provenance="unit legacy fixture",
        )
    )

    bootstrap_current_trigger_sets(store, created_at="2026-09-06T00:00:00+00:00")

    legacy = store.get_set("triggertrade-core-candidate", "v1-test")
    spot_candidate = store.get_set("triggertrade-core-candidate", "v2-test")
    candidate = store.get_set("triggertrade-futures-candidate", "v2-test")
    assert ("TRG-002", "0.1.0") not in legacy.rule_versions
    assert ("TRG-002", "0.1.0") in spot_candidate.rule_versions
    assert spot_candidate.status is TriggerSetStatus.ARCHIVE
    assert ("TRG-002", "0.2.0") in candidate.rule_versions
    assert candidate.status is TriggerSetStatus.TESTING

def test_recommendation_registry_separates_observation_hypothesis_and_experiment(tmp_path):
    store = TriggerSetStore(tmp_path / "rec.sqlite3")
    bootstrap_current_trigger_sets(store, created_at="2026-09-05T00:00:00+00:00")

    rec = store.get_recommendation("REC-TRG-VOLUME-001")

    assert rec is not None
    assert rec.observation.startswith("The current active baseline")
    assert "may" in rec.hypothesis
    assert "TESTING trigger set" in rec.recommended_experiment
    assert rec.resulting_test_set_id == "triggertrade-core-candidate"
    assert "No historical performance" in rec.evidence


def test_recommendation_mutation_is_rejected(tmp_path):
    store = TriggerSetStore(tmp_path / "rec.sqlite3")
    bootstrap_current_trigger_sets(store, created_at="2026-09-05T00:00:00+00:00")
    rec = store.get_recommendation("REC-TRG-VOLUME-001")

    mutated = rec.__class__(**{**rec.__dict__, "hypothesis": "changed"})
    with pytest.raises(TriggerSetStoreError, match="immutable"):
        store.save_recommendation(mutated)



def test_recommendation_status_transition_is_explicit_and_audited(tmp_path):
    store = TriggerSetStore(tmp_path / "rec.sqlite3")
    bootstrap_current_trigger_sets(store, created_at="2026-09-05T00:00:00+00:00")

    transitioned = store.transition_recommendation_status(
        recommendation_id="REC-TRG-VOLUME-001",
        status="EVALUATED",
        changed_at="2026-09-06T00:00:00+00:00",
        reason="manual reviewer evaluation recorded",
    )

    assert transitioned.status == "EVALUATED"
    with pytest.raises(TriggerSetStoreError, match="invalid"):
        store.transition_recommendation_status(
            recommendation_id="REC-TRG-VOLUME-001",
            status="PROPOSED",
            changed_at="2026-09-06T00:01:00+00:00",
            reason="backwards transition is not allowed",
        )



def test_rule_version_semantic_metadata_is_immutable(tmp_path):
    store = TriggerSetStore(tmp_path / "rules.sqlite3")
    rule = RuleDefinition(
        rule_id="TRG-X",
        version="0.1.0",
        name="X",
        status=RuleStatus.TESTING,
        asset_scope="BTCUSDT spot",
        rule_type=current_rule_definitions(created_at="2026-09-05T00:00:00+00:00")[0].rule_type,
        condition="x >= 1",
        definition={"implementation_key": "tests.XTrigger", "threshold": "1"},
        created_at="2026-09-05T00:00:00+00:00",
        provenance="unit test",
        formula="x / y",
        boundary_semantics="inclusive >= 1",
    )
    store.save_rule(rule)

    changed_formula = RuleDefinition(**{**rule.__dict__, "formula": "x / z"})
    with pytest.raises(TriggerSetStoreError, match="Version bump"):
        store.save_rule(changed_formula)
