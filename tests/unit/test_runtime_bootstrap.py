import sqlite3

import pytest

from triggertrade.dashboard.__main__ import create_server_from_env, render_dashboard
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.persistence import CandleLifecycle, RuntimeStore, TriggerSetStore, TriggerSetStoreError, current_rule_definitions, current_testing_trigger_set, current_volume_recommendation
from triggertrade.services.bootstrap import (
    ensure_configured_runtime_registry,
    ensure_runtime_registry_initialized,
    merged_runtime_env,
    runtime_db_path,
)
from triggertrade.services.runtime import build_runtime_from_env
from triggertrade.trigger_sets import RuleDefinition, TriggerSetStatus


def _counts(db_path):
    with sqlite3.connect(db_path) as conn:
        return {
            "rules": conn.execute("SELECT COUNT(*) FROM rule_definitions").fetchone()[0],
            "sets": conn.execute("SELECT COUNT(*) FROM trigger_set_versions").fetchone()[0],
            "memberships": conn.execute("SELECT COUNT(*) FROM trigger_set_memberships").fetchone()[0],
            "recommendations": conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0],
            "lane_lifecycles": _optional_count(conn, "runtime_lane_lifecycles"),
        }


def _optional_count(conn, table):
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.Error:
        return 0


def test_empty_runtime_db_bootstraps_canonical_registries_without_fake_evidence(tmp_path):
    db = tmp_path / "runtime.sqlite3"

    result = ensure_runtime_registry_initialized(db)
    model = DashboardReadModel(db)

    assert result.db_path == db
    assert result.rules_count == 4
    assert result.trigger_sets_count == 2
    assert result.recommendations_count == 1
    assert {rule.rule_id for rule in model.list_rules()} >= {"TRG-001", "TRG-002"}
    assert model.get_rule_detail("TRG-002", "0.1.0").rule["status"] == "TESTING"
    assert model.get_live_overview().rule_set == "v1"
    assert model.get_live_overview().rules_count == 3
    assert model.get_test_overview().rule_set == "v2-test"
    assert model.list_set_performance() == ()
    assert _counts(db)["lane_lifecycles"] == 0


def test_bootstrap_is_idempotent_across_repeated_startups(tmp_path):
    db = tmp_path / "runtime.sqlite3"

    ensure_runtime_registry_initialized(db)
    first = _counts(db)
    ensure_runtime_registry_initialized(db)
    second = _counts(db)
    ensure_runtime_registry_initialized(db)
    third = _counts(db)

    assert first == second == third
    assert first == {"rules": 4, "sets": 2, "memberships": 7, "recommendations": 1, "lane_lifecycles": 0}


def test_same_version_same_semantics_ok_and_different_semantics_fail_closed(tmp_path):
    db = tmp_path / "runtime.sqlite3"
    ensure_runtime_registry_initialized(db)
    store = TriggerSetStore(db)
    rule = store.get_rule("TRG-002", "0.1.0")

    store.save_rule(rule)
    mutated = RuleDefinition(**{**rule.__dict__, "condition": "relative_volume >= 1.5"})
    with pytest.raises(TriggerSetStoreError, match="immutable"):
        store.save_rule(mutated)


def test_legacy_runtime_history_survives_registry_bootstrap(tmp_path):
    db = tmp_path / "runtime.sqlite3"
    RuntimeStore(db).save_lifecycle(
        CandleLifecycle(
            candle_id="BTCUSDT:1m:2026-09-05T12:00:00+00:00",
            symbol="BTCUSDT",
            timeframe="1m",
            candle_open_time="2026-09-05T12:00:00+00:00",
            status="no_signal",
            processed_at="2026-09-05T12:01:01+00:00",
        )
    )

    ensure_runtime_registry_initialized(db)

    assert RuntimeStore(db).get_lifecycle("BTCUSDT:1m:2026-09-05T12:00:00+00:00") is not None
    assert TriggerSetStore(db).get_active_set("BTCUSDT", "1m").version == "v1"
    assert TriggerSetStore(db).get_set("triggertrade-core-candidate", "v2-test").status is TriggerSetStatus.TESTING


def test_configured_bootstrap_uses_env_file_and_process_env_precedence(tmp_path):
    env_db = tmp_path / "env.sqlite3"
    process_db = tmp_path / "process.sqlite3"
    env_file = tmp_path / ".env"
    env_file.write_text(f"TRIGGERTRADE_RUNTIME_DB_PATH={env_db}\n", encoding="utf-8")

    env = {"TRIGGERTRADE_RUNTIME_DB_PATH": str(process_db)}
    config, result = ensure_configured_runtime_registry(env, env_file=env_file)

    assert runtime_db_path(config, merged_runtime_env(env, env_file=env_file)) == process_db
    assert result.db_path == process_db
    assert process_db.exists()
    assert not env_db.exists()


def test_dashboard_startup_bootstraps_registry_before_read_only_render(tmp_path):
    db = tmp_path / "dashboard.sqlite3"
    server, initialized_db = create_server_from_env(
        {"TRIGGERTRADE_RUNTIME_DB_PATH": str(db), "TRIGGERTRADE_DASHBOARD_PORT": "0"},
        env_file=tmp_path / "missing.env",
    )
    try:
        assert initialized_db == db
        html = render_dashboard(server.read_model)
    finally:
        server.server_close()

    assert "No Trigger Sets registered yet." not in html
    assert "No rule registry records yet." not in html
    assert "No recommendations registered yet." not in html
    assert "triggertrade-core-candidate" in html
    assert "v2-test" in html
    assert "TRG-002" in html
    assert "Robust Volume Confirmation" in html
    assert "No set-level runtime evidence recorded yet." in html


def test_runtime_builder_bootstraps_same_configured_db_path(tmp_path):
    db = tmp_path / "runtime-builder.sqlite3"
    runtime = build_runtime_from_env({"TRIGGERTRADE_RUNTIME_DB_PATH": str(db)})

    assert runtime._trigger_set_store.path == db
    assert TriggerSetStore(db).get_active_set("BTCUSDT", "1m").version == "v1"
    assert TriggerSetStore(db).get_set("triggertrade-core-candidate", "v2-test") is not None

def test_bootstrap_fails_closed_on_existing_candidate_set_semantic_mismatch(tmp_path):
    db = tmp_path / "runtime.sqlite3"
    store = TriggerSetStore(db)
    created_at = "2026-09-05T00:00:00+00:00"
    for rule in current_rule_definitions(created_at=created_at):
        store.save_rule(rule)
    canonical = current_testing_trigger_set(created_at=created_at)
    mismatched = canonical.__class__(
        **{
            **canonical.__dict__,
            "rule_versions": (("TRG-001", "0.1.0"), ("STR-001", "0.1.0"), ("RSK-PAPER-001", "0.1.0")),
        }
    )
    store.create_set(mismatched)

    with pytest.raises(TriggerSetStoreError, match="immutable"):
        ensure_runtime_registry_initialized(db)


def test_bootstrap_fails_closed_on_existing_recommendation_payload_mismatch(tmp_path):
    db = tmp_path / "runtime.sqlite3"
    store = TriggerSetStore(db)
    created_at = "2026-09-05T00:00:00+00:00"
    rec = current_volume_recommendation(created_at=created_at)
    stale = rec.__class__(**{**rec.__dict__, "hypothesis": "stale local hypothesis"})
    store.save_recommendation(stale)

    with pytest.raises(TriggerSetStoreError, match="immutable"):
        ensure_runtime_registry_initialized(db)