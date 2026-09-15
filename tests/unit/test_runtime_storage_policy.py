import pytest

from triggertrade.config import ConfigError
from triggertrade.services.process_roles import SchedulerProcess
from triggertrade.services.runtime_storage import (
    canonical_runtime_state_store_from_env,
    is_filesystem_artifact_kind,
    require_canonical_durable_runtime_state,
)


def test_canonical_durable_runtime_state_requires_postgres_dsn():
    with pytest.raises(ConfigError, match="TRIGGERTRADE_POSTGRES_DSN"):
        require_canonical_durable_runtime_state({}, component="trading worker")


def test_canonical_durable_runtime_state_accepts_postgres_dsn():
    require_canonical_durable_runtime_state(
        {"TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit/db"},
        component="trading worker",
    )


def test_filesystem_artifact_kinds_are_explicitly_non_canonical_state():
    assert is_filesystem_artifact_kind("historical_kline_cache") is True
    assert is_filesystem_artifact_kind("runtime_backup_export") is True
    assert is_filesystem_artifact_kind("isolated_restore_verification") is True
    assert is_filesystem_artifact_kind("runtime_checkpoint") is False


def test_canonical_runtime_state_store_uses_postgres_without_local_db(monkeypatch):
    captured: dict[str, object] = {}

    class DummySettings:
        dsn = "postgresql://unit/db"
        schema = "tt_unit"

        @classmethod
        def from_env(cls, env):
            captured["env"] = dict(env)
            return cls()

    class DummyFactory:
        def __init__(self, *, dsn, schema):
            captured["factory"] = (dsn, schema)

    class DummyPostgresRuntimeStore:
        def __init__(self, factory):
            captured["runtime_factory"] = factory

    def fake_migrations(*, dsn, schema):
        captured["migrations"] = (dsn, schema)

    import triggertrade.persistence as persistence

    monkeypatch.setattr(persistence, "PostgresSettings", DummySettings)
    monkeypatch.setattr(persistence, "PostgresConnectionFactory", DummyFactory)
    monkeypatch.setattr(persistence, "PostgresRuntimeStore", DummyPostgresRuntimeStore)
    monkeypatch.setattr(persistence, "apply_postgres_migrations", fake_migrations)

    store = canonical_runtime_state_store_from_env(
        {
            "TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit/db",
            "TRIGGERTRADE_POSTGRES_SCHEMA": "tt_unit",
            "TRIGGERTRADE_RUNTIME_DB_PATH": "runtime/should-not-open.sqlite3",
        },
        component="scheduler role",
    )

    assert isinstance(store, DummyPostgresRuntimeStore)
    assert captured["migrations"] == ("postgresql://unit/db", "tt_unit")
    assert captured["factory"] == ("postgresql://unit/db", "tt_unit")


def test_scheduler_role_fails_closed_before_local_filesystem_bootstrap():

    with pytest.raises(ConfigError, match="scheduler role requires TRIGGERTRADE_POSTGRES_DSN"):
        SchedulerProcess(env={}).run_forever(max_cycles=1)


def test_scheduler_role_hydrates_only_after_durable_state_is_configured(monkeypatch):
    captured: dict[str, object] = {}
    messages: list[str] = []

    class FakeRuntimeStore:
        def list_heartbeats(self):
            captured["hydrated"] = True
            return ()

    def fake_runtime_store(env, *, component):
        captured["env"] = dict(env)
        captured["component"] = component
        return FakeRuntimeStore()

    monkeypatch.setattr(
        "triggertrade.services.process_roles.canonical_runtime_state_store_from_env",
        fake_runtime_store,
    )

    SchedulerProcess(
        env={"TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit/db"},
        sleeper=lambda _: None,
        logger=messages.append,
    ).run_forever(max_cycles=1)

    assert captured["env"] == {"TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit/db"}
    assert captured["component"] == "scheduler role"
    assert captured["hydrated"] is True
    assert messages == ["triggertrade scheduler role hydrated durable runtime state"]
