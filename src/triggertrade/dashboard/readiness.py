"""Dependency-aware dashboard readiness checks."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from triggertrade.dashboard.read_model import DashboardReadModel, ReadinessCheckView
from triggertrade.config import ConfigError, load_config
from triggertrade.services.runtime import validate_bybit_demo_runtime_env
from triggertrade.persistence.postgres import (
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresSettings,
)


READINESS_STATUSES = frozenset({"RUNNING", "DEGRADED", "BLOCKED", "UNAVAILABLE"})


@dataclass(frozen=True)
class DashboardReadinessCheck:
    name: str
    status: str
    detail: str
    observed_at: str | None = None


@dataclass(frozen=True)
class DashboardReadinessReport:
    status: str
    ready: bool
    checks: tuple[DashboardReadinessCheck, ...]
    unavailable_dependencies: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "ready": self.ready,
            "unavailable_dependencies": list(self.unavailable_dependencies),
            "checks": [
                {
                    "name": check.name,
                    "status": check.status,
                    "detail": check.detail,
                    "observed_at": check.observed_at,
                }
                for check in self.checks
            ],
        }


PostgresHealthProbe = Callable[[Mapping[str, str]], DashboardReadinessCheck]


def evaluate_dashboard_readiness(
    read_model: DashboardReadModel,
    *,
    env: Mapping[str, str],
    postgres_probe: PostgresHealthProbe | None = None,
    execution_bridge: object | None = None,
) -> DashboardReadinessReport:
    demo_readiness = read_model.get_demo_readiness()
    checks: list[DashboardReadinessCheck] = [_view_check(check) for check in demo_readiness.checks]
    checks.append(_postgres_persistence_check(env, postgres_probe=postgres_probe))
    checks.append(_worker_safety_check(demo_readiness.checks))
    checks.append(_bybit_demo_config_check(env))
    checks.append(_execution_bridge_check(execution_bridge))

    status = _rollup(check.status for check in checks)
    unavailable = tuple(
        check.name
        for check in checks
        if check.status in {"BLOCKED", "UNAVAILABLE"}
    )
    return DashboardReadinessReport(
        status=status,
        ready=status == "RUNNING",
        checks=tuple(checks),
        unavailable_dependencies=unavailable,
    )


def default_postgres_health_probe(env: Mapping[str, str]) -> DashboardReadinessCheck:
    try:
        settings = PostgresSettings.from_env(env)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with factory.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    except PostgresPersistenceError as exc:
        return DashboardReadinessCheck("postgres_persistence", "UNAVAILABLE", str(exc))
    except Exception as exc:  # noqa: BLE001 - readiness must report unavailable, not crash.
        return DashboardReadinessCheck(
            "postgres_persistence",
            "UNAVAILABLE",
            f"PostgreSQL reachability check failed: {exc.__class__.__name__}",
        )
    return DashboardReadinessCheck("postgres_persistence", "RUNNING", "PostgreSQL persistence reachable")


def _bybit_demo_config_check(env: Mapping[str, str]) -> DashboardReadinessCheck:
    try:
        source = dict(env)
        config = load_config(source)
        validate_bybit_demo_runtime_env(source, config)
    except ConfigError as exc:
        return DashboardReadinessCheck("bybit_demo_config", "BLOCKED", _safe_config_error(exc))
    return DashboardReadinessCheck("bybit_demo_config", "RUNNING", "Bybit Demo linear endpoint configuration present")


def _execution_bridge_check(bridge: object | None) -> DashboardReadinessCheck:
    if bridge is None:
        return DashboardReadinessCheck(
            "execution_bridge_attached",
            "BLOCKED",
            "Dashboard execution bridge is not attached",
        )
    if not getattr(bridge, "canonical_execution_bridge", False):
        return DashboardReadinessCheck(
            "execution_bridge_attached",
            "BLOCKED",
            "Dashboard execution bridge is not a certified canonical execution bridge",
        )
    if callable(getattr(bridge, "close_position", None)) and callable(getattr(bridge, "close_all_positions", None)):
        return DashboardReadinessCheck("execution_bridge_attached", "RUNNING", "Canonical dashboard execution bridge is attached")
    return DashboardReadinessCheck(
        "execution_bridge_attached",
        "BLOCKED",
        "Dashboard execution bridge is missing required close operations",
    )


def _postgres_persistence_check(
    env: Mapping[str, str],
    *,
    postgres_probe: PostgresHealthProbe | None,
) -> DashboardReadinessCheck:
    probe = default_postgres_health_probe if postgres_probe is None else postgres_probe
    check = probe(env)
    _validate_status(check.status, check.name)
    return check


def _worker_safety_check(checks: tuple[ReadinessCheckView, ...]) -> DashboardReadinessCheck:
    heartbeat = next(
        (check for check in checks if check.name == "heartbeat:trading-worker"),
        None,
    )
    heartbeat = heartbeat or next(
        (check for check in checks if check.name == "heartbeat:futures_runtime"),
        None,
    )
    if heartbeat is None:
        return DashboardReadinessCheck(
            "worker_safety",
            "DEGRADED",
            "futures worker heartbeat has not been recorded",
        )
    status = heartbeat.status
    _validate_status(status, heartbeat.name)
    if status == "RUNNING":
        return DashboardReadinessCheck(
            "worker_safety",
            "RUNNING",
            "futures worker reports safe processing state",
            heartbeat.observed_at,
        )
    if status == "BLOCKED":
        return DashboardReadinessCheck(
            "worker_safety",
            "BLOCKED",
            f"futures worker blocked: {heartbeat.detail}",
            heartbeat.observed_at,
        )
    if status == "UNAVAILABLE":
        return DashboardReadinessCheck(
            "worker_safety",
            "UNAVAILABLE",
            f"futures worker unavailable: {heartbeat.detail}",
            heartbeat.observed_at,
        )
    return DashboardReadinessCheck(
        "worker_safety",
        "DEGRADED",
        f"futures worker degraded: {heartbeat.detail}",
        heartbeat.observed_at,
    )


def _view_check(check: ReadinessCheckView) -> DashboardReadinessCheck:
    _validate_status(check.status, check.name)
    return DashboardReadinessCheck(
        check.name,
        check.status,
        check.detail,
        check.observed_at,
    )


def _rollup(statuses) -> str:
    values = tuple(statuses)
    if not values:
        return "UNAVAILABLE"
    if any(status == "BLOCKED" for status in values):
        return "BLOCKED"
    if any(status == "UNAVAILABLE" for status in values):
        return "UNAVAILABLE"
    if any(status == "DEGRADED" for status in values):
        return "DEGRADED"
    return "RUNNING"


def _validate_status(status: str, name: str) -> None:
    if status not in READINESS_STATUSES:
        raise ValueError(f"readiness check {name!r} returned unsupported status {status!r}")


def _safe_config_error(exc: Exception) -> str:
    text = str(exc)
    lower = text.lower()
    if any(token in lower for token in ("secret", "api_key", "api-secret", "token", "password", "authorization")):
        return exc.__class__.__name__
    return text[:240]
