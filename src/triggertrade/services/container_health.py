"""Role-aware container health checks for TriggerTrade process containers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import os
from typing import Protocol
from urllib.error import URLError
from urllib.request import urlopen

from triggertrade.dashboard.readiness import DashboardReadinessCheck, default_postgres_health_probe
from triggertrade.services.process_roles import RuntimeProcessRole, resolve_process_role


class UrlOpen(Protocol):
    def __call__(self, url: str, *, timeout: float): ...


PostgresProbe = Callable[[Mapping[str, str]], DashboardReadinessCheck]


@dataclass(frozen=True)
class ContainerHealthReport:
    role: RuntimeProcessRole
    ready: bool
    status: str
    detail: str


def evaluate_container_health(
    env: Mapping[str, str] | None = None,
    *,
    web_probe: UrlOpen | None = None,
    postgres_probe: PostgresProbe | None = None,
) -> ContainerHealthReport:
    """Evaluate the selected container role without exposing secret-bearing config."""

    values = dict(os.environ if env is None else env)
    role = resolve_process_role(values).role
    if role is RuntimeProcessRole.WEB:
        return _web_health(values, web_probe=web_probe)
    if role in {RuntimeProcessRole.TRADING_WORKER, RuntimeProcessRole.SCHEDULER}:
        return _durable_role_health(role, values, postgres_probe=postgres_probe)
    return ContainerHealthReport(
        role=role,
        ready=False,
        status="UNAVAILABLE",
        detail=f"{role.value} role is not deployable in this container image",
    )


def main() -> int:
    report = evaluate_container_health()
    print(f"{report.role.value} {report.status}: {report.detail}")
    return 0 if report.ready else 1


def _web_health(env: Mapping[str, str], *, web_probe: UrlOpen | None) -> ContainerHealthReport:
    port = _dashboard_port(env)
    probe = urlopen if web_probe is None else web_probe
    url = f"http://127.0.0.1:{port}/healthz"
    try:
        response = probe(url, timeout=5)
        status_code = int(getattr(response, "status", getattr(response, "code", 0)))
        close = getattr(response, "close", None)
        if callable(close):
            close()
    except (OSError, URLError) as exc:
        return ContainerHealthReport(
            role=RuntimeProcessRole.WEB,
            ready=False,
            status="UNAVAILABLE",
            detail=f"web health endpoint failed: {exc.__class__.__name__}",
        )
    if status_code == 200:
        return ContainerHealthReport(
            role=RuntimeProcessRole.WEB,
            ready=True,
            status="RUNNING",
            detail="web /healthz returned HTTP 200",
        )
    return ContainerHealthReport(
        role=RuntimeProcessRole.WEB,
        ready=False,
        status="UNAVAILABLE",
        detail=f"web /healthz returned HTTP {status_code}",
    )


def _durable_role_health(
    role: RuntimeProcessRole,
    env: Mapping[str, str],
    *,
    postgres_probe: PostgresProbe | None,
) -> ContainerHealthReport:
    probe = default_postgres_health_probe if postgres_probe is None else postgres_probe
    check = probe(env)
    ready = check.status == "RUNNING"
    return ContainerHealthReport(
        role=role,
        ready=ready,
        status=check.status,
        detail=f"{role.value} durable PostgreSQL check: {check.detail}",
    )


def _dashboard_port(env: Mapping[str, str]) -> int:
    raw = str(env.get("TRIGGERTRADE_DASHBOARD_PORT") or "8765").strip()
    try:
        port = int(raw)
    except ValueError:
        return 8765
    return port if 0 < port < 65536 else 8765


if __name__ == "__main__":
    raise SystemExit(main())
