"""Process-role launcher boundary for TriggerTrade runtime components."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import os
import signal
import time
from typing import Callable, Mapping, Protocol

from triggertrade.config import ConfigError
from triggertrade.services.runtime_storage import canonical_runtime_state_store_from_env


class RuntimeProcessRole(StrEnum):
    WEB = "web"
    TRADING_WORKER = "trading-worker"
    SCHEDULER = "scheduler"
    RESEARCH_WORKER = "research-worker"


class ProcessRoleError(RuntimeError):
    """Raised when a runtime process role cannot be selected safely."""


class StoppableProcess(Protocol):
    def stop(self) -> None: ...


@dataclass(frozen=True)
class ProcessRoleSelection:
    role: RuntimeProcessRole
    source: str


class SchedulerProcess:
    """Minimal scheduler role scaffold.

    The scheduler is explicit and container-supervised, but final orchestration
    duties are owned by later traced tasks. This role only hydrates durable
    startup state and remains idle between supervised loops.
    """

    def __init__(
        self,
        *,
        env: Mapping[str, str],
        sleeper: Callable[[float], None] = time.sleep,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        self._env = dict(env)
        self._sleeper = sleeper
        self._logger = logger or (lambda message: print(message))
        self._stop_requested = False

    def run_forever(self, max_cycles: int | None = None) -> None:
        runtime_store = canonical_runtime_state_store_from_env(self._env, component="scheduler role")
        runtime_store.list_heartbeats()
        cycles = 0
        self._logger("triggertrade scheduler role hydrated durable runtime state")
        while not self._stop_requested:
            cycles += 1
            if max_cycles is not None and cycles >= max_cycles:
                break
            self._sleeper(_scheduler_poll_seconds(self._env))

    def stop(self) -> None:
        self._stop_requested = True


def resolve_process_role(env: Mapping[str, str]) -> ProcessRoleSelection:
    for key in ("TRIGGERTRADE_PROCESS_ROLE", "TRIGGERTRADE_ROLE"):
        raw = str(env.get(key) or "").strip()
        if raw:
            return ProcessRoleSelection(_parse_role(raw), key)
    return ProcessRoleSelection(RuntimeProcessRole.TRADING_WORKER, "default")


def run_process_role(
    env: Mapping[str, str] | None = None,
    *,
    max_cycles: int | None = None,
    web_server_factory: Callable[[Mapping[str, str]], tuple[object, object]] | None = None,
    trading_worker_factory: Callable[[Mapping[str, str]], object] | None = None,
    scheduler_factory: Callable[[Mapping[str, str]], object] | None = None,
    install_signal_handlers: bool = True,
) -> int:
    runtime_env = dict(os.environ if env is None else env)
    selection = resolve_process_role(runtime_env)
    if selection.role is RuntimeProcessRole.RESEARCH_WORKER:
        raise ProcessRoleError("research-worker role is reserved for a later traced implementation")
    if selection.role is RuntimeProcessRole.WEB:
        return _run_web_role(
            runtime_env,
            web_server_factory=web_server_factory,
            install_signal_handlers=install_signal_handlers,
        )
    if selection.role is RuntimeProcessRole.TRADING_WORKER:
        return _run_trading_worker_role(
            runtime_env,
            max_cycles=max_cycles,
            trading_worker_factory=trading_worker_factory,
            install_signal_handlers=install_signal_handlers,
        )
    if selection.role is RuntimeProcessRole.SCHEDULER:
        return _run_scheduler_role(
            runtime_env,
            max_cycles=max_cycles,
            scheduler_factory=scheduler_factory,
            install_signal_handlers=install_signal_handlers,
        )
    raise ProcessRoleError(f"unsupported TriggerTrade process role: {selection.role}")


def _run_web_role(
    env: Mapping[str, str],
    *,
    web_server_factory: Callable[[Mapping[str, str]], tuple[object, object]] | None,
    install_signal_handlers: bool,
) -> int:
    if web_server_factory is None:
        from triggertrade.dashboard.__main__ import create_server_from_env

        web_server_factory = lambda source: create_server_from_env(dict(source))
    server, db_path = web_server_factory(env)
    stop = getattr(server, "shutdown", None)
    if install_signal_handlers and callable(stop):
        _install_stop_signal_handlers(stop)
    host, port = getattr(server, "server_address", ("unknown", "unknown"))
    print(f"TriggerTrade web role: http://{host}:{port}/")
    print(f"TriggerTrade registry DB: {db_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def _run_trading_worker_role(
    env: Mapping[str, str],
    *,
    max_cycles: int | None,
    trading_worker_factory: Callable[[Mapping[str, str]], object] | None,
    install_signal_handlers: bool,
) -> int:
    if trading_worker_factory is None:
        from triggertrade.services.runtime import build_runtime_from_env

        trading_worker_factory = build_runtime_from_env
    worker = trading_worker_factory(env)
    stop = getattr(worker, "stop", None)
    if install_signal_handlers and callable(stop):
        _install_stop_signal_handlers(stop)
    worker.run_forever(max_cycles=max_cycles)
    return 0


def _run_scheduler_role(
    env: Mapping[str, str],
    *,
    max_cycles: int | None,
    scheduler_factory: Callable[[Mapping[str, str]], object] | None,
    install_signal_handlers: bool,
) -> int:
    scheduler = scheduler_factory(env) if scheduler_factory is not None else SchedulerProcess(env=env)
    stop = getattr(scheduler, "stop", None)
    if install_signal_handlers and callable(stop):
        _install_stop_signal_handlers(stop)
    scheduler.run_forever(max_cycles=max_cycles)
    return 0


def _install_stop_signal_handlers(stop: Callable[[], None]) -> None:
    def handle_stop(signum, frame):  # noqa: ANN001 - signal handler signature is fixed by stdlib.
        stop()

    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(signum, handle_stop)
        except (ValueError, OSError):
            continue


def _parse_role(value: str) -> RuntimeProcessRole:
    normalized = value.strip().lower().replace("_", "-")
    aliases = {
        "worker": RuntimeProcessRole.TRADING_WORKER,
        "trading": RuntimeProcessRole.TRADING_WORKER,
        "trading-worker": RuntimeProcessRole.TRADING_WORKER,
        "web": RuntimeProcessRole.WEB,
        "api": RuntimeProcessRole.WEB,
        "dashboard": RuntimeProcessRole.WEB,
        "scheduler": RuntimeProcessRole.SCHEDULER,
        "orchestrator": RuntimeProcessRole.SCHEDULER,
        "research-worker": RuntimeProcessRole.RESEARCH_WORKER,
        "research": RuntimeProcessRole.RESEARCH_WORKER,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        allowed = ", ".join(role.value for role in RuntimeProcessRole)
        raise ProcessRoleError(f"unsupported TriggerTrade process role {value!r}; expected one of: {allowed}") from exc


def _scheduler_poll_seconds(env: Mapping[str, str]) -> float:
    raw = str(env.get("TRIGGERTRADE_SCHEDULER_POLL_SECONDS") or "5").strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError("TRIGGERTRADE_SCHEDULER_POLL_SECONDS must be numeric") from exc
    if value <= 0:
        raise ConfigError("TRIGGERTRADE_SCHEDULER_POLL_SECONDS must be positive")
    return min(value, 300.0)
