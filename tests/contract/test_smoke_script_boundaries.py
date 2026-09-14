import importlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.smoke_guards import MANUAL_NONCANONICAL_SMOKE, require_manual_smoke_opt_in, smoke_metadata
from triggertrade.config import ConfigError
from triggertrade.services.runtime import PaperTradingRuntime


ROOT = Path(__file__).resolve().parents[2]


def test_smoke_guard_requires_explicit_manual_opt_in():
    with pytest.raises(RuntimeError, match="manual/noncanonical"):
        require_manual_smoke_opt_in({}, "RUN_EXAMPLE_SMOKE", "example smoke")

    require_manual_smoke_opt_in({"RUN_EXAMPLE_SMOKE": "1"}, "RUN_EXAMPLE_SMOKE", "example smoke")


def test_smoke_metadata_marks_harnesses_noncanonical():
    assert smoke_metadata("RUN_EXAMPLE_SMOKE") == {
        "classification": MANUAL_NONCANONICAL_SMOKE,
        "opt_in_flag": "RUN_EXAMPLE_SMOKE",
    }


@pytest.mark.parametrize(
    "module_name, flag",
    (
        ("scripts.bybit_demo_futures_smoke", "RUN_BYBIT_DEMO_FUTURES_SMOKE"),
        ("scripts.triggertrade_demo_soak", "RUN_TRIGGERTRADE_DEMO_SOAK"),
        ("scripts.paper_runtime_smoke", "RUN_TRIGGERTRADE_PAPER_RUNTIME_SMOKE"),
    ),
)
def test_traced_smoke_scripts_have_explicit_opt_in_flags(module_name, flag):
    module = importlib.import_module(module_name)

    assert module.OPT_IN_FLAG == flag


def test_futures_smoke_script_skips_without_manual_opt_in(monkeypatch, capsys):
    module = importlib.import_module("scripts.bybit_demo_futures_smoke")
    monkeypatch.delenv(module.OPT_IN_FLAG, raising=False)

    assert module.main() == 0

    assert "manual/noncanonical" in capsys.readouterr().out


def test_paper_runtime_smoke_script_skips_without_manual_opt_in(monkeypatch, capsys):
    module = importlib.import_module("scripts.paper_runtime_smoke")
    monkeypatch.delenv(module.OPT_IN_FLAG, raising=False)

    assert module.main() == 0

    assert "manual/noncanonical" in capsys.readouterr().out


@pytest.mark.parametrize(
    "script, flag",
    (
        ("scripts/bybit_demo_futures_smoke.py", "RUN_BYBIT_DEMO_FUTURES_SMOKE"),
        ("scripts/triggertrade_demo_soak.py", "RUN_TRIGGERTRADE_DEMO_SOAK"),
        ("scripts/paper_runtime_smoke.py", "RUN_TRIGGERTRADE_PAPER_RUNTIME_SMOKE"),
    ),
)
def test_direct_smoke_script_cli_skips_without_manual_opt_in(script, flag):
    env = os.environ.copy()
    env.pop(flag, None)

    completed = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert "manual/noncanonical" in completed.stdout


def test_demo_soak_requires_manual_noncanonical_opt_in(tmp_path):
    module = importlib.import_module("scripts.triggertrade_demo_soak")

    with pytest.raises(RuntimeError, match="manual/noncanonical"):
        module.run_soak(
            {
                "TRIGGERTRADE_RUNTIME_DB_PATH": str(tmp_path / "soak.sqlite3"),
                "TRIGGERTRADE_MARKET": "linear",
                "TRIGGERTRADE_CATEGORY": "linear",
                "TRIGGERTRADE_EXECUTION_VENUE": "bybit_demo_futures",
                "TRIGGERTRADE_ACTIVE_EXECUTION_VENUE": "bybit_demo_futures",
                "TRIGGERTRADE_TEST_EXECUTION_VENUE": "local_test_simulation",
                "TRIGGERTRADE_BYBIT_ENV": "demo",
                "BYBIT_BASE_URL": "https://api-demo.bybit.com",
                "BYBIT_API_KEY": "unit-key",
                "BYBIT_API_SECRET": "unit-secret",
            },
            cycles=1,
        )


def test_paper_runtime_smoke_uses_explicit_legacy_compatibility_builder(tmp_path):
    module = importlib.import_module("scripts.paper_runtime_smoke")

    runtime = module.build_legacy_paper_runtime_from_env(
        {
            "TRIGGERTRADE_RUNTIME_DB_PATH": str(tmp_path / "paper.sqlite3"),
            "BYBIT_API_KEY": "unit-key",
            "BYBIT_API_SECRET": "unit-secret",
        }
    )

    assert isinstance(runtime, PaperTradingRuntime)
    assert not hasattr(module, "build_runtime_from_env")


def test_paper_runtime_smoke_rejects_canonical_futures_config(tmp_path):
    module = importlib.import_module("scripts.paper_runtime_smoke")

    with pytest.raises(ConfigError, match="legacy/demo-only"):
        module.build_legacy_paper_runtime_from_env(
            {
                "TRIGGERTRADE_RUNTIME_DB_PATH": str(tmp_path / "paper.sqlite3"),
                "TRIGGERTRADE_MARKET": "linear",
                "TRIGGERTRADE_CATEGORY": "linear",
                "TRIGGERTRADE_EXECUTION_VENUE": "bybit_demo_futures",
                "BYBIT_API_KEY": "unit-key",
                "BYBIT_API_SECRET": "unit-secret",
            }
        )
