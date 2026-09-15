"""Run an isolated PostgreSQL backup/restore/recovery drill for TriggerTrade."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from triggertrade.persistence import (  # noqa: E402
    DurableMessageStore,
    OwnerStateStore,
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresSettings,
    PostgresUnitOfWork,
    ResearchPromotionGovernanceStore,
    apply_postgres_migrations,
)


_SCHEMA_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
_DRILL_PREFIX = "tt_recovery_drill_"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-schema", default=None, help="Isolated source schema. Defaults to a generated drill schema.")
    parser.add_argument("--restore-schema", default=None, help="Isolated restore schema. Defaults to a generated drill schema.")
    parser.add_argument("--keep-schemas", action="store_true", help="Leave isolated schemas in place for manual inspection.")
    args = parser.parse_args()

    settings = PostgresSettings.from_env()
    suffix = uuid.uuid4().hex[:12]
    source_schema = _drill_schema(args.source_schema or f"{_DRILL_PREFIX}src_{suffix}")
    restore_schema = _drill_schema(args.restore_schema or f"{_DRILL_PREFIX}restore_{suffix}")
    if source_schema == restore_schema:
        raise PostgresPersistenceError("source and restore schemas must differ")

    result = run_drill(settings.dsn, source_schema=source_schema, restore_schema=restore_schema, keep_schemas=args.keep_schemas)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def run_drill(dsn: str, *, source_schema: str, restore_schema: str, keep_schemas: bool = False) -> dict[str, object]:
    source_schema = _drill_schema(source_schema)
    restore_schema = _drill_schema(restore_schema)
    created_schemas = (source_schema, restore_schema)
    try:
        _drop_schema(dsn, source_schema)
        _drop_schema(dsn, restore_schema)
        applied = apply_postgres_migrations(dsn=dsn, schema=source_schema)
        _seed_source(dsn, source_schema)
        source_counts = _table_counts(dsn, source_schema)
        source_probe = _probe_state(dsn, source_schema)

        restore_applied = apply_postgres_migrations(dsn=dsn, schema=restore_schema)
        _copy_schema_data(dsn, source_schema=source_schema, restore_schema=restore_schema)
        restore_second_apply = apply_postgres_migrations(dsn=dsn, schema=restore_schema)
        restore_counts = _table_counts(dsn, restore_schema)
        restore_probe = _probe_state(dsn, restore_schema)

        if source_counts != restore_counts:
            raise PostgresPersistenceError("restored table counts do not match source")
        if source_probe != restore_probe:
            raise PostgresPersistenceError("restored durable state probe does not match source")
        if restore_second_apply:
            raise PostgresPersistenceError("restore schema has pending migrations after data restore")

        return {
            "status": "PASS",
            "source_schema": source_schema,
            "restore_schema": restore_schema,
            "source_migrations_applied": [item.version for item in applied],
            "restore_migrations_applied": [item.version for item in restore_applied],
            "restore_second_apply_applied": [],
            "table_counts": restore_counts,
            "durable_state": restore_probe,
            "schemas_retained": keep_schemas,
        }
    finally:
        if not keep_schemas:
            for schema in reversed(created_schemas):
                _drop_schema(dsn, schema)


def _seed_source(dsn: str, schema: str) -> None:
    factory = PostgresConnectionFactory(dsn=dsn, schema=schema)
    with PostgresUnitOfWork(factory) as uow:
        owner = OwnerStateStore(uow.connection)
        owner.put_if_absent(
            owner="Portfolio Rules",
            state_type="portfolio_state",
            state_id="portfolio:main",
            payload={"status": "LIVE", "bucket": "portfolio", "source": "recovery-drill"},
        )
        messages = DurableMessageStore(uow.connection)
        payload = {"contract_type": "COINS", "event_id": "drill-coins-1", "coins": [{"symbol": "BTCUSDT"}]}
        messages.append_outbox(
            message_id="drill-outbox-1",
            producer="Portfolio Rules",
            consumer="Set",
            message_type="COINS",
            message_version="2",
            aggregate_id="scope:BTCUSDT",
            dedupe_key="scope:BTCUSDT:drill",
            payload=payload,
        )
        messages.record_inbox(
            consumer="Lifecycle",
            message_id="drill-inbox-1",
            producer="Position Rules",
            message_type="ORDER_SPEC",
            message_version="5",
            payload={"contract_type": "ORDER_SPEC", "order_spec_id": "order-spec-drill"},
        )
        ResearchPromotionGovernanceStore(uow.connection).request_promotion(
            request_id="research-promotion:drill-1",
            research_id="research-drill-1",
            idempotency_key="drill-1",
            payload={
                "research_promotion_request": {
                    "request_id": "research-promotion:drill-1",
                    "research_id": "research-drill-1",
                    "target": {"set_id": "set-drill", "set_version": "v1", "rules_version_id": "rules-drill"},
                    "safety": {"sqlite_active_mutation": False, "live_order_side_effect": False},
                }
            },
        )


def _copy_schema_data(dsn: str, *, source_schema: str, restore_schema: str) -> None:
    with _connect(dsn, autocommit=False) as conn:
        with conn.cursor() as cursor:
            for table in _table_names(conn, source_schema):
                cursor.execute(f'TRUNCATE TABLE "{restore_schema}"."{table}" CASCADE')
                cursor.execute(f'INSERT INTO "{restore_schema}"."{table}" SELECT * FROM "{source_schema}"."{table}"')
        conn.commit()


def _probe_state(dsn: str, schema: str) -> dict[str, object]:
    factory = PostgresConnectionFactory(dsn=dsn, schema=schema)
    with PostgresUnitOfWork(factory) as uow:
        owner = OwnerStateStore(uow.connection)
        portfolio = owner.get(owner="Portfolio Rules", state_type="portfolio_state", state_id="portfolio:main")
        promotion = owner.get(owner="Research", state_type="research_promotion_request", state_id="research-promotion:drill-1")
        messages = DurableMessageStore(uow.connection)
        outbox = messages.get_outbox(message_id="drill-outbox-1")
        promotion_outbox = messages.get_outbox(message_id="research-promotion:drill-1")
        inbox = messages.get_inbox(consumer="Lifecycle", message_id="drill-inbox-1")
    return {
        "portfolio_digest": None if portfolio is None else portfolio.payload_digest,
        "promotion_digest": None if promotion is None else promotion.payload_digest,
        "outbox_digest": None if outbox is None else outbox.payload_digest,
        "promotion_outbox_consumer": None if promotion_outbox is None else promotion_outbox.consumer,
        "inbox_status": None if inbox is None else inbox.status,
    }


def _table_counts(dsn: str, schema: str) -> dict[str, int]:
    with _connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            counts = {}
            for table in _table_names(conn, schema):
                cursor.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
                counts[table] = int(cursor.fetchone()[0])
            return counts


def _table_names(conn, schema: str) -> tuple[str, ...]:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            (schema,),
        )
        return tuple(str(row[0]) for row in cursor.fetchall())


def _drop_schema(dsn: str, schema: str) -> None:
    schema = _drill_schema(schema)
    with _connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


def _connect(dsn: str, *, autocommit: bool):
    try:
        import psycopg
    except ImportError as exc:
        raise PostgresPersistenceError("psycopg is required for PostgreSQL recovery drills") from exc
    return psycopg.connect(dsn, autocommit=autocommit)


def _drill_schema(value: str) -> str:
    if not _SCHEMA_RE.fullmatch(value):
        raise PostgresPersistenceError("drill schema must be a safe PostgreSQL identifier")
    if not value.startswith(_DRILL_PREFIX):
        raise PostgresPersistenceError(f"drill schema must start with {_DRILL_PREFIX!r}")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
