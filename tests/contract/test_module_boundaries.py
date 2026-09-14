import importlib
import os
import subprocess
import sys


def test_primary_module_boundaries_are_importable():
    modules = [
        "triggertrade.config",
        "triggertrade.market_data",
        "triggertrade.triggers",
        "triggertrade.strategies",
        "triggertrade.risk",
        "triggertrade.execution",
        "triggertrade.exchanges",
        "triggertrade.persistence",
        "triggertrade.services",
        "triggertrade.dashboard",
        "triggertrade.exchanges.bybit",
        "triggertrade.market_data.bybit",
    ]

    for module in modules:
        assert importlib.import_module(module)


def test_execution_and_exchange_contracts_are_available():
    execution = importlib.import_module("triggertrade.execution")
    exchanges = importlib.import_module("triggertrade.exchanges")

    assert hasattr(execution, "OrderStatus")
    assert hasattr(execution, "ExecutionService")
    assert hasattr(execution, "TradeIntent")
    assert hasattr(exchanges, "ExchangeAdapter")


def test_legacy_spot_and_paper_paths_remain_explicit_compatibility_imports():
    runtime = importlib.import_module("triggertrade.services.runtime")
    execution = importlib.import_module("triggertrade.execution")
    spot_execution = importlib.import_module("triggertrade.execution.bybit")

    assert hasattr(runtime, "PaperTradingRuntime")
    assert hasattr(execution, "PaperExecutionAdapter")
    assert hasattr(spot_execution, "BybitExecutionAdapter")


def test_canonical_runtime_builder_is_the_public_runtime_launcher():
    runtime = importlib.import_module("triggertrade.services.runtime")

    assert runtime.CANONICAL_RUNTIME_KIND == "futures_dual_lane"
    assert runtime.build_runtime_from_env is runtime.build_canonical_runtime_from_env


def test_canonical_runtime_module_import_does_not_load_legacy_execution_modules():
    code = (
        "import sys; "
        "import triggertrade.services.runtime; "
        "forbidden = {'triggertrade.execution.paper', 'triggertrade.execution.bybit'} & set(sys.modules); "
        "raise SystemExit('loaded legacy modules: ' + ', '.join(sorted(forbidden)) if forbidden else 0)"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    completed = subprocess.run([sys.executable, "-c", code], env=env, text=True, capture_output=True, check=False)

    assert completed.returncode == 0, completed.stderr or completed.stdout
