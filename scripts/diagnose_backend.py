"""Emit a sanitized TriggerTrade backend diagnostics snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from triggertrade.services.backend_diagnostics import collect_backend_diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    args = parser.parse_args()

    report = collect_backend_diagnostics()
    print(report.to_json(indent=2 if args.pretty else None))
    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
