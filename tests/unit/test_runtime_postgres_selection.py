from pathlib import Path

import triggertrade.persistence as persistence
from triggertrade.persistence import RuntimeStore
from triggertrade.services.runtime import runtime_state_store_from_env


def test_runtime_state_store_uses_postgres_when_dsn_is_configured(monkeypatch):
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

    monkeypatch.setattr(persistence, "PostgresSettings", DummySettings)
    monkeypatch.setattr(persistence, "PostgresConnectionFactory", DummyFactory)
    monkeypatch.setattr(persistence, "PostgresRuntimeStore", DummyPostgresRuntimeStore)
    monkeypatch.setattr(persistence, "apply_postgres_migrations", fake_migrations)

    store = runtime_state_store_from_env(
        {
            "TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit/db",
            "TRIGGERTRADE_POSTGRES_SCHEMA": "tt_unit",
        },
        Path("runtime/local.sqlite3"),
    )

    assert isinstance(store, DummyPostgresRuntimeStore)
    assert captured["migrations"] == ("postgresql://unit/db", "tt_unit")
    assert captured["factory"] == ("postgresql://unit/db", "tt_unit")


def test_runtime_state_store_keeps_sqlite_for_local_dev_without_postgres(tmp_path):
    store = runtime_state_store_from_env({}, tmp_path / "runtime.sqlite3")

    assert isinstance(store, RuntimeStore)
