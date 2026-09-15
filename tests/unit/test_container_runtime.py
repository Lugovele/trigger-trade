from triggertrade.dashboard.readiness import DashboardReadinessCheck
from triggertrade.services.container_health import evaluate_container_health
from triggertrade.services.process_roles import RuntimeProcessRole


class FakeResponse:
    status = 200

    def close(self):
        pass


def test_dockerfile_runs_process_role_launcher_with_role_aware_healthcheck():
    dockerfile = _read("Dockerfile")

    assert "TRIGGERTRADE_PROCESS_ROLE=web" not in dockerfile
    assert "TRIGGERTRADE_RUNTIME_DB_PATH=/app/runtime/triggertrade_paper.sqlite3" not in dockerfile
    assert 'VOLUME ["/app/runtime"]' not in dockerfile
    assert "CMD python -m triggertrade.services.container_health" in dockerfile
    assert 'CMD ["python", "-m", "triggertrade.services.runtime"]' in dockerfile
    assert "triggertrade.dashboard" not in dockerfile


def test_deploy_script_can_target_web_worker_and_scheduler_roles():
    script = _read("scripts/deploy-azure.ps1")

    assert '[ValidateSet("web", "trading-worker", "scheduler")]' in script
    assert '[string[]] $Roles = @("web", "trading-worker", "scheduler")' in script
    assert '"trading-worker" = "triggertrade-trading-worker"' in script
    assert '"scheduler" = "triggertrade-scheduler"' in script
    assert '"--set-env-vars", "TRIGGERTRADE_PROCESS_ROLE=$Role"' in script
    assert "Wait-ContainerAppReady" in script


def test_web_container_health_uses_local_healthz_endpoint():
    captured: dict[str, object] = {}

    def fake_probe(url, *, timeout):
        captured["url"] = url
        captured["timeout"] = timeout
        return FakeResponse()

    report = evaluate_container_health(
        {"TRIGGERTRADE_PROCESS_ROLE": "web", "TRIGGERTRADE_DASHBOARD_PORT": "9999"},
        web_probe=fake_probe,
    )

    assert report.ready is True
    assert report.role is RuntimeProcessRole.WEB
    assert captured == {"url": "http://127.0.0.1:9999/healthz", "timeout": 5}


def test_worker_container_health_uses_durable_postgres_probe():
    def fake_postgres_probe(env):
        assert env["TRIGGERTRADE_POSTGRES_DSN"] == "postgresql://unit/db"
        return DashboardReadinessCheck("postgres_persistence", "RUNNING", "PostgreSQL persistence reachable")

    report = evaluate_container_health(
        {
            "TRIGGERTRADE_PROCESS_ROLE": "trading-worker",
            "TRIGGERTRADE_POSTGRES_DSN": "postgresql://unit/db",
        },
        postgres_probe=fake_postgres_probe,
    )

    assert report.ready is True
    assert report.role is RuntimeProcessRole.TRADING_WORKER
    assert "durable PostgreSQL check" in report.detail


def test_scheduler_container_health_fails_without_durable_postgres_config():
    report = evaluate_container_health({"TRIGGERTRADE_PROCESS_ROLE": "scheduler"})

    assert report.ready is False
    assert report.role is RuntimeProcessRole.SCHEDULER
    assert report.status == "UNAVAILABLE"
    assert "TRIGGERTRADE_POSTGRES_DSN is required" in report.detail


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()
