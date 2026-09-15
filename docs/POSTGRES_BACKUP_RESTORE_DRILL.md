# PostgreSQL Backup / Restore Drill

Status: formula-agnostic operational drill.

This drill verifies the durable PostgreSQL backend can be migrated, copied into an isolated restore schema, and read after restore without changing production data or formula semantics.

## Command

```powershell
$env:TRIGGERTRADE_POSTGRES_DSN = "<postgres dsn>"
python scripts\postgres_recovery_drill.py
```

Optional inspection mode:

```powershell
python scripts\postgres_recovery_drill.py --keep-schemas
```

The script only operates on schemas whose names start with `tt_recovery_drill_`.

## What It Verifies

- all PostgreSQL migrations apply to an isolated source schema;
- durable owner state can be written and recovered;
- durable outbox and inbox facts survive restore;
- research promotion governance owner state and Scheduler outbox survive restore;
- restored schema accepts a second migration application with zero pending migrations;
- source and restored table counts match;
- source and restored durable-state probes match.

## What It Does Not Do

- it does not touch production schemas;
- it does not run `pg_dump` or `pg_restore`;
- it does not certify formula or accounting calculations;
- it does not activate research output;
- it does not place orders.

Use managed database backup tooling for production point-in-time backup policy. This drill is the repository-level recoverability proof for the current durable schema and persistence contracts.
