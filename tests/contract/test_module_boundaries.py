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


def test_canonical_runtime_construction_does_not_load_legacy_strategy_or_risk_modules(tmp_path):
    code = (
        "import sys; "
        "from triggertrade.services.runtime import build_canonical_runtime_from_env; "
        "runtime = build_canonical_runtime_from_env({"
        f"'TRIGGERTRADE_RUNTIME_DB_PATH': {str(tmp_path / 'canonical.sqlite3')!r}, "
        "'TRIGGERTRADE_MARKET': 'linear', "
        "'TRIGGERTRADE_CATEGORY': 'linear', "
        "'TRIGGERTRADE_EXECUTION_VENUE': 'bybit_demo_futures', "
        "'BYBIT_API_KEY': 'contract-key', "
        "'BYBIT_API_SECRET': 'contract-secret'"
        "}); "
        "forbidden = {'triggertrade.strategies.buy_candidate', 'triggertrade.risk', 'triggertrade.risk.manager'} & set(sys.modules); "
        "raise SystemExit('loaded legacy strategy/risk modules: ' + ', '.join(sorted(forbidden)) if forbidden else 0)"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    completed = subprocess.run([sys.executable, "-c", code], env=env, text=True, capture_output=True, check=False)

    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_legacy_strategy_and_risk_paths_remain_explicit_compatibility_imports():
    strategies = importlib.import_module("triggertrade.strategies")
    risk = importlib.import_module("triggertrade.risk")

    assert hasattr(strategies, "BuyCandidateStrategy")
    assert hasattr(risk, "RiskManager")


def test_legacy_execution_stores_remain_explicit_compatibility_imports():
    persistence = importlib.import_module("triggertrade.persistence")

    assert hasattr(persistence, "ExecutionStore")
    assert hasattr(persistence, "FuturesExecutionStore")
    assert persistence.is_legacy_execution_evidence_store(persistence.ExecutionStore)
    assert persistence.is_legacy_execution_evidence_store(persistence.FuturesExecutionStore)
