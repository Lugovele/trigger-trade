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
    assert "useradd --system --gid triggertrade" in dockerfile
    assert "chown -R triggertrade:triggertrade /app" in dockerfile
    assert "USER triggertrade" in dockerfile
    assert "TRIGGERTRADE_POSTGRES_MIGRATIONS_DIR=/app/migrations/postgres" in dockerfile
    assert "COPY migrations ./migrations" in dockerfile
    assert "CMD python -m triggertrade.services.container_health" in dockerfile
    assert 'CMD ["python", "-m", "triggertrade.services.runtime"]' in dockerfile
    assert "triggertrade.dashboard" not in dockerfile


def test_deploy_script_can_target_web_worker_and_scheduler_roles():
    script = _read("scripts/deploy-azure.ps1")

    assert '[ValidateSet("web", "trading-worker", "scheduler")]' in script
    assert '[string[]] $Roles = @("web", "trading-worker", "scheduler")' in script
    assert '$AcrRepository = "triggertrade-web"' in script
    assert '"web" = "triggertrade-web-centralus"' in script
    assert '"trading-worker" = "triggertrade-trading-worker-centralus"' in script
    assert '"scheduler" = "triggertrade-scheduler-centralus"' in script
    assert '$UserAssignedIdentity = "triggertrade-pull-id"' in script
    assert '"containerapp", "identity", "assign"' in script
    assert '"--user-assigned", $UserAssignedIdentityId' in script
    assert '"--min-replicas", [string] $Scale.min' in script
    assert '"--max-replicas", [string] $Scale.max' in script
    assert "TRIGGERTRADE_RUNTIME_MODE=production" in script
    assert "TRIGGERTRADE_POSTGRES_DSN=secretref:postgres-dsn" in script
    assert "BYBIT_API_KEY=secretref:bybit-api-key" in script
    assert "BYBIT_API_SECRET=secretref:bybit-api-secret" in script
    assert '"--set-env-vars"' in script
    assert '$RoleEnvVars = @($CommonEnvVars + "TRIGGERTRADE_PROCESS_ROLE=$Role")' in script
    assert "Wait-ContainerAppReady" in script
    assert "Custom domain and DNS cutover are intentionally not modified by this script." in script


def test_github_workflow_has_cloud_build_only_mode_before_deploy():
    workflow = _read(".github/workflows/deploy-production.yml")

    assert "workflow_dispatch:" in workflow
    assert "deploy:" in workflow
    assert "type: boolean" in workflow
    assert "default: false" in workflow
    assert "triggertradeacr-dcfmhtd6fmaubtac.azurecr.io" in workflow
    assert "ACR_REPOSITORY: triggertrade-web" in workflow
    assert 'IMAGE_TAG="${GITHUB_SHA}"' in workflow
    assert 'echo "IMAGE_TAG=${IMAGE_TAG}" >> "$GITHUB_ENV"' in workflow
    assert "docker build" in workflow
    assert "docker push" in workflow
    assert "az acr manifest show-metadata" in workflow
    assert '--name "${ACR_REPOSITORY}:${IMAGE_TAG}"' in workflow
    assert "--query digest" in workflow
    assert "DIGEST_LINE_COUNT" in workflow
    assert "sha256:*" in workflow
    assert "docker buildx imagetools inspect" not in workflow
    assert "{{.Digest}}" not in workflow
    assert "Build-only mode complete" in workflow
    assert "Container Apps were not modified" in workflow
    assert "if: ${{ github.event_name == 'workflow_dispatch' && github.event.inputs.deploy != 'true' }}" in workflow
    assert workflow.count("if: ${{ github.event_name == 'push' || github.event.inputs.deploy == 'true' }}") >= 6
    assert "triggertrade-web-centralus" in workflow
    assert "triggertrade-trading-worker-centralus" in workflow
    assert "triggertrade-scheduler-centralus" in workflow
    assert "BYBIT_API_KEY=secretref:bybit-api-key" in workflow
    assert "BYBIT_API_SECRET=secretref:bybit-api-secret" in workflow
    assert "custom domain" not in workflow.lower()
    assert "dns" not in workflow.lower()


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
