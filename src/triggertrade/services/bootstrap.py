"""Shared startup bootstrap for TriggerTrade runtime registries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
from typing import Mapping

from triggertrade.config import AppConfig, load_config
from triggertrade.persistence import TriggerSetStore, bootstrap_current_trigger_sets


@dataclass(frozen=True)
class RegistryBootstrapResult:
    db_path: Path
    rules_count: int
    trigger_sets_count: int
    recommendations_count: int


def load_env_file(path: str | Path = ".env") -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = Path(path)
    if not env_path.exists():
        return values
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def merged_runtime_env(
    process_env: Mapping[str, str] | None = None,
    *,
    env_file: str | Path = ".env",
) -> dict[str, str]:
    merged = load_env_file(env_file)
    merged.update(dict(os.environ if process_env is None else process_env))
    return merged


def load_runtime_config(
    process_env: Mapping[str, str] | None = None,
    *,
    env_file: str | Path = ".env",
) -> AppConfig:
    return load_config(merged_runtime_env(process_env, env_file=env_file))


def runtime_db_path(config: AppConfig, env: Mapping[str, str] | None = None) -> Path:
    source = os.environ if env is None else env
    return Path(source.get("TRIGGERTRADE_RUNTIME_DB_PATH", config.paper_runtime.db_path).strip())


def ensure_runtime_registry_initialized(
    db_path: str | Path,
    *,
    created_at: str = "2026-09-05T00:00:00+00:00",
) -> RegistryBootstrapResult:
    store = TriggerSetStore(db_path)
    bootstrap_current_trigger_sets(store, created_at=created_at)
    return RegistryBootstrapResult(
        db_path=Path(db_path),
        rules_count=len(store.list_rules()),
        trigger_sets_count=len(store.list_sets()),
        recommendations_count=len(store.list_recommendations()),
    )


def ensure_runtime_registry_for_env(
    env: Mapping[str, str],
    *,
    created_at: str = "2026-09-05T00:00:00+00:00",
) -> tuple[AppConfig, RegistryBootstrapResult]:
    config = load_config(env)
    db_path = runtime_db_path(config, env)
    result = ensure_runtime_registry_initialized(db_path, created_at=created_at)
    return config, result


def ensure_configured_runtime_registry(
    process_env: Mapping[str, str] | None = None,
    *,
    env_file: str | Path = ".env",
    created_at: str = "2026-09-05T00:00:00+00:00",
) -> tuple[AppConfig, RegistryBootstrapResult]:
    env = merged_runtime_env(process_env, env_file=env_file)
    return ensure_runtime_registry_for_env(env, created_at=created_at)