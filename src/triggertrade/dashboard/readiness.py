"""Dependency-aware dashboard readiness checks."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import re
from typing import Any

from triggertrade.dashboard.read_model import DashboardReadModel, ReadinessCheckView
from triggertrade.config import ConfigError, load_config
from triggertrade.services.runtime import validate_bybit_demo_runtime_env
from triggertrade.persistence.postgres import (
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresSettings,
    PostgresUnitOfWork,
)
from triggertrade.persistence.postgres_research_registry import RESEARCH_CONFIG_OWNER
from triggertrade.persistence.postgres_runtime_store import PostgresRuntimeStore
from triggertrade.services.operator_auth import MANAGED_OIDC_AUTH_SOURCE


READINESS_STATUSES = frozenset({"RUNNING", "DEGRADED", "BLOCKED", "UNAVAILABLE"})
_SECRET_RE = re.compile(
    r"(postgres(?:ql)?://\S+|api[_-]?key|api[_-]?secret|authorization|bearer|cookie|csrf|session|token|password|credential|signature|\.env)",
    re.I,
)


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
PostgresRuntimeProbe = Callable[[Mapping[str, str]], tuple[DashboardReadinessCheck, ...]]
PostgresRegistryProbe = Callable[[Mapping[str, str]], DashboardReadinessCheck]


def evaluate_dashboard_readiness(
    read_model: DashboardReadModel,
    *,
    env: Mapping[str, str],
    postgres_probe: PostgresHealthProbe | None = None,
    postgres_runtime_probe: PostgresRuntimeProbe | None = None,
    postgres_registry_probe: PostgresRegistryProbe | None = None,
    execution_bridge: object | None = None,
) -> DashboardReadinessReport:
    demo_readiness = read_model.get_demo_readiness()
    postgres_check = _postgres_persistence_check(env, postgres_probe=postgres_probe)
    production_postgres = bool(str(env.get("TRIGGERTRADE_POSTGRES_DSN") or "").strip())
    if production_postgres:
        local_checks = [_production_local_check(check) for check in demo_readiness.checks]
        checks = [check for check in local_checks if check is not None]
        checks.append(postgres_check)
        registry_probe = _postgres_registry_check if postgres_registry_probe is None else postgres_registry_probe
        checks.append(registry_probe(env) if postgres_check.status == "RUNNING" else _registry_blocked_by_postgres())
        runtime_checks = (
            _postgres_runtime_heartbeat_checks(env)
            if postgres_runtime_probe is None
            else postgres_runtime_probe(env)
        )
        checks.extend(runtime_checks)
        checks.append(_worker_safety_check(runtime_checks))
    else:
        checks = [_view_check(check) for check in demo_readiness.checks]
        checks.append(postgres_check)
        checks.append(_worker_safety_check(demo_readiness.checks))
    checks.append(_operator_auth_boundary_check(env))
    checks.append(_bybit_demo_config_check(env))
    checks.append(_execution_bridge_check(execution_bridge))
    checks = [_safe_check(check) for check in checks]

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


def _postgres_runtime_heartbeat_checks(env: Mapping[str, str]) -> tuple[DashboardReadinessCheck, ...]:
    try:
        settings = PostgresSettings.from_env(env)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        heartbeats = PostgresRuntimeStore(factory).list_heartbeats()
    except Exception as exc:  # noqa: BLE001 - readiness must report unavailable, not crash.
        return (
            DashboardReadinessCheck(
                "heartbeat:trading-worker",
                "UNAVAILABLE",
                f"PostgreSQL runtime heartbeat check failed: {_safe_readiness_detail(exc.__class__.__name__)}",
            ),
        )
    if not heartbeats:
        return (
            DashboardReadinessCheck(
                "heartbeat:trading-worker",
                "DEGRADED",
                "no distributed runtime heartbeat recorded",
            ),
        )
    checks: list[DashboardReadinessCheck] = []
    for heartbeat in heartbeats:
        name = f"heartbeat:{heartbeat.component}"
        status = str(heartbeat.status or "UNAVAILABLE").upper()
        _validate_status(status, name)
        if _timestamp_is_stale(heartbeat.observed_at, timedelta(minutes=5)) and status == "RUNNING":
            status = "DEGRADED"
            detail = f"distributed heartbeat is stale: {_safe_readiness_detail(heartbeat.detail or heartbeat.observed_at)}"
        else:
            detail = _safe_readiness_detail(heartbeat.detail) if heartbeat.detail else f"distributed heartbeat reported {status}"
        checks.append(DashboardReadinessCheck(name, status, detail, heartbeat.observed_at))
    return tuple(checks)


def _postgres_registry_check(env: Mapping[str, str]) -> DashboardReadinessCheck:
    try:
        settings = PostgresSettings.from_env(env)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            with uow.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT state_type, COUNT(*)
                    FROM triggertrade_owner_state_records
                    WHERE owner = %s
                    GROUP BY state_type
                    """,
                    (RESEARCH_CONFIG_OWNER,),
                )
                rows = cursor.fetchall()
    except Exception as exc:  # noqa: BLE001 - readiness must report unavailable, not crash.
        return DashboardReadinessCheck(
            "research_config_registry",
            "UNAVAILABLE",
            f"PostgreSQL Research configuration registry check failed: {_safe_readiness_detail(exc.__class__.__name__)}",
        )
    counts = {str(state_type): int(count) for state_type, count in rows}
    detail = (
        "PostgreSQL Research configuration registry reachable; "
        f"research={counts.get('RESEARCH_DEFINITION', 0)}, "
        f"sets={counts.get('TRIGGER_SET_VERSION', 0)}, "
        f"rules={counts.get('TRADING_RULES_VERSION', 0)}"
    )
    return DashboardReadinessCheck("research_config_registry", "RUNNING", detail)


def _registry_blocked_by_postgres() -> DashboardReadinessCheck:
    return DashboardReadinessCheck(
        "research_config_registry",
        "UNAVAILABLE",
        "PostgreSQL Research configuration registry unavailable because PostgreSQL is unreachable",
    )


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


def _operator_auth_boundary_check(env: Mapping[str, str]) -> DashboardReadinessCheck:
    runtime_mode = str(env.get("TRIGGERTRADE_RUNTIME_MODE") or "").strip().lower()
    process_role = str(env.get("TRIGGERTRADE_PROCESS_ROLE") or env.get("TRIGGERTRADE_ROLE") or "").strip().lower().replace("_", "-")
    production_web = runtime_mode == "production" or process_role in {"web", "api", "dashboard"}
    auth_mode = str(env.get("TRIGGERTRADE_AUTH_MODE") or MANAGED_OIDC_AUTH_SOURCE).strip().lower()
    if production_web and auth_mode in {"local", "local_dev", "local_dev_compat"}:
        return DashboardReadinessCheck(
            "operator_auth_boundary",
            "BLOCKED",
            "production web operator commands cannot use local_dev_compat auth",
        )
    if auth_mode in {"managed_oidc", "entra", "entra_oidc", ""}:
        if not _split_csv(str(env.get("TRIGGERTRADE_OPERATOR_PRINCIPALS") or "")):
            return DashboardReadinessCheck(
                "operator_auth_boundary",
                "BLOCKED",
                "managed operator principal allowlist is not configured",
            )
        return DashboardReadinessCheck(
            "operator_auth_boundary",
            "RUNNING",
            "managed OIDC operator authorization boundary configured",
        )
    if auth_mode in {"local", "local_dev", "local_dev_compat"}:
        return DashboardReadinessCheck(
            "operator_auth_boundary",
            "RUNNING",
            "local development operator authorization boundary configured",
        )
    return DashboardReadinessCheck(
        "operator_auth_boundary",
        "BLOCKED",
        "unsupported operator auth mode",
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


def _worker_safety_check(checks) -> DashboardReadinessCheck:
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
            f"futures worker blocked: {_safe_readiness_detail(heartbeat.detail)}",
            heartbeat.observed_at,
        )
    if status == "UNAVAILABLE":
        return DashboardReadinessCheck(
            "worker_safety",
            "UNAVAILABLE",
            f"futures worker unavailable: {_safe_readiness_detail(heartbeat.detail)}",
            heartbeat.observed_at,
        )
    return DashboardReadinessCheck(
        "worker_safety",
        "DEGRADED",
        f"futures worker degraded: {_safe_readiness_detail(heartbeat.detail)}",
        heartbeat.observed_at,
    )


def _production_local_check(check: ReadinessCheckView) -> DashboardReadinessCheck | None:
    if check.name == "operator":
        return _view_check(check)
    if check.status == "RUNNING":
        return _view_check(check)
    if check.name == "database":
        return DashboardReadinessCheck(
            "web_read_model",
            "DEGRADED",
            "local compatibility read model is unavailable; PostgreSQL is authoritative in production",
            check.observed_at,
        )
    if check.name in {"heartbeat", "heartbeat:futures_runtime"}:
        return None
    if check.name in {"market_data", "account_data", "instrument_catalog"}:
        return DashboardReadinessCheck(
            check.name,
            "DEGRADED",
            f"{_safe_readiness_detail(check.detail)}; no authoritative distributed {check.name.replace('_', ' ')} evidence is currently exposed to web readiness",
            check.observed_at,
        )
    return _view_check(check)


def _view_check(check: ReadinessCheckView) -> DashboardReadinessCheck:
    _validate_status(check.status, check.name)
    return DashboardReadinessCheck(
        check.name,
        check.status,
        _safe_readiness_detail(check.detail),
        check.observed_at,
    )


def _safe_check(check: DashboardReadinessCheck) -> DashboardReadinessCheck:
    return DashboardReadinessCheck(
        check.name,
        check.status,
        _safe_readiness_detail(check.detail),
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


def _timestamp_is_stale(value: str | None, max_age: timedelta) -> bool:
    if not value:
        return True
    try:
        observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return True
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=UTC)
    return datetime.now(UTC) - observed.astimezone(UTC) > max_age


def _safe_config_error(exc: Exception) -> str:
    text = str(exc)
    lower = text.lower()
    if any(token in lower for token in ("secret", "api_key", "api-secret", "token", "password", "authorization")):
        return exc.__class__.__name__
    return text[:240]


def _split_csv(raw: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _safe_readiness_detail(value: object) -> str:
    text = str(value or "").replace("\x00", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "unavailable"
    if _SECRET_RE.search(text):
        return "redacted"
    return text[:240]
