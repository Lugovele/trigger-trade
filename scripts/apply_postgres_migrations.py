"""Apply TriggerTrade PostgreSQL migrations from the configured DSN."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from triggertrade.persistence.postgres import PostgresSettings, apply_postgres_migrations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--schema",
        default=None,
        help="PostgreSQL schema to migrate. Defaults to TRIGGERTRADE_POSTGRES_SCHEMA or public.",
    )
    args = parser.parse_args()
    settings = PostgresSettings.from_env()
    schema = args.schema or settings.schema
    applied = apply_postgres_migrations(dsn=settings.dsn, schema=schema)
    print(f"postgres migrations applied: {len(applied)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
