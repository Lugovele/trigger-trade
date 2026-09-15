import pytest

from triggertrade.config import ConfigError
from triggertrade.services.process_roles import (
    ProcessRoleError,
    RuntimeProcessRole,
    resolve_process_role,
    run_process_role,
)


class FakeWorker:
    def __init__(self):
        self.max_cycles = None
        self.stopped = False

    def run_forever(self, *, max_cycles=None):
        self.max_cycles = max_cycles

    def stop(self):
        self.stopped = True


class FakeServer:
    server_address = ("127.0.0.1", 0)

    def __init__(self):
        self.served = False
        self.closed = False
        self.shutdown_requested = False

    def serve_forever(self):
        self.served = True

    def shutdown(self):
        self.shutdown_requested = True

    def server_close(self):
        self.closed = True


def test_process_role_resolution_defaults_to_trading_worker_and_accepts_aliases():
    assert resolve_process_role({}).role is RuntimeProcessRole.TRADING_WORKER
    assert resolve_process_role({"TRIGGERTRADE_PROCESS_ROLE": "web"}).role is RuntimeProcessRole.WEB
    assert resolve_process_role({"TRIGGERTRADE_ROLE": "scheduler"}).role is RuntimeProcessRole.SCHEDULER
    assert resolve_process_role({"TRIGGERTRADE_ROLE": "worker"}).role is RuntimeProcessRole.TRADING_WORKER


def test_process_role_resolution_fails_closed_for_unknown_role():
    with pytest.raises(ProcessRoleError, match="unsupported TriggerTrade process role"):
        resolve_process_role({"TRIGGERTRADE_PROCESS_ROLE": "all-in-one"})


def test_trading_worker_role_runs_injected_canonical_worker_with_cycle_limit():
    worker = FakeWorker()

    result = run_process_role(
        {"TRIGGERTRADE_PROCESS_ROLE": "trading-worker"},
        max_cycles=2,
        trading_worker_factory=lambda env: worker,
        install_signal_handlers=False,
    )

    assert result == 0
    assert worker.max_cycles == 2


def test_default_trading_worker_role_excludes_legacy_demo_runtime():
    with pytest.raises(ConfigError, match="target message-driven trading worker"):
        run_process_role(
            {"TRIGGERTRADE_PROCESS_ROLE": "trading-worker"},
            install_signal_handlers=False,
        )


def test_web_role_serves_injected_dashboard_and_closes_server():
    server = FakeServer()

    result = run_process_role(
        {"TRIGGERTRADE_PROCESS_ROLE": "web"},
        web_server_factory=lambda env: (server, "unit.sqlite3"),
        install_signal_handlers=False,
    )

    assert result == 0
    assert server.served is True
    assert server.closed is True


def test_scheduler_role_is_explicit_and_container_supervised():
    scheduler = FakeWorker()

    result = run_process_role(
        {"TRIGGERTRADE_PROCESS_ROLE": "scheduler"},
        max_cycles=1,
        scheduler_factory=lambda env: scheduler,
        install_signal_handlers=False,
    )

    assert result == 0
    assert scheduler.max_cycles == 1


def test_research_worker_role_is_reserved_for_later_traced_implementation():
    with pytest.raises(ProcessRoleError, match="reserved for a later traced implementation"):
        run_process_role(
            {"TRIGGERTRADE_PROCESS_ROLE": "research-worker"},
            install_signal_handlers=False,
        )
