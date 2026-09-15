"""Run the frozen non-formula backend validation contract."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pytest-basetemp",
        default=None,
        help="Optional pytest basetemp. Defaults to a unique directory under .tmp.",
    )
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Run non-pytest validation only.",
    )
    args = parser.parse_args()

    basetemp = Path(args.pytest_basetemp) if args.pytest_basetemp else ROOT / ".tmp" / f"pytest-nonformula-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    commands: list[list[str]] = [
        [sys.executable, "scripts/validate_methodology_integrity.py"],
    ]
    if not args.skip_pytest:
        commands.append(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/unit",
                "tests/contract",
                "tests/integration",
                "--tb=short",
                "--basetemp",
                str(basetemp),
            ]
        )

    for command in commands:
        print(f"+ {' '.join(command)}", flush=True)
        completed = subprocess.run(command, cwd=ROOT)
        if completed.returncode != 0:
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
