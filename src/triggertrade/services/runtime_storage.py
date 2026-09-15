"""Runtime-state storage policy for canonical process roles."""

from __future__ import annotations

from collections.abc import Mapping

from triggertrade.config import ConfigError


POSTGRES_DSN_ENV = "TRIGGERTRADE_POSTGRES_DSN"
FILESYSTEM_ARTIFACT_KINDS = frozenset(
    {
        "historical_kline_cache",
        "runtime_backup_export",
        "isolated_restore_verification",
    }
)


def require_canonical_durable_runtime_state(env: Mapping[str, str], *, component: str) -> None:
    """Require canonical runtime state to be backed by PostgreSQL."""

    if str(env.get(POSTGRES_DSN_ENV) or "").strip():
        return
    raise ConfigError(
        f"{component} requires {POSTGRES_DSN_ENV}; local filesystem state is allowed only for "
        "explicit local/dev compatibility, caches, or backup/export artifacts"
    )


def canonical_runtime_state_store_from_env(env: Mapping[str, str], *, component: str):
    """Build the canonical PostgreSQL-backed runtime state store."""

    require_canonical_durable_runtime_state(env, component=component)
    import triggertrade.persistence as persistence

    settings = persistence.PostgresSettings.from_env(env)
    persistence.apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
    return persistence.PostgresRuntimeStore(
        persistence.PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
    )


def is_filesystem_artifact_kind(kind: str) -> bool:
    """Return whether a filesystem artifact is explicitly non-canonical durable state."""

    return kind.strip().lower() in FILESYSTEM_ARTIFACT_KINDS
