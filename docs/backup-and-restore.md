# Backup and Restore

TriggerTrade backup is an operational recovery workflow for the configured
runtime SQLite database. It is not the System History export. System History is
a bounded readable diagnostic snapshot for humans or AI-assisted analysis;
backup is a verified SQLite restore point for application continuity.

## Scope

Backups preserve the runtime DB state needed to recover product continuity:

- immutable Trading Rules versions and the current Rules pointer;
- Trigger definitions, Trigger Set versions, memberships, and active Set state;
- Research entities, Backtest/Demo run metadata, selections, decisions, and
  Make Active evidence;
- futures orders, fills, open/closed positions, accounting, and equity
  snapshots;
- operator state and operator action audit;
- user-facing Messages and read state;
- structured Audit Trail events;
- heartbeat/readiness/catalog cache rows as historical evidence only.

Backups do not include `.env`, `.env.*`, API keys, API secrets, Authorization
headers, cookies, private keys, credential files, pytest artifacts, temp
directories, raw logs, or source code.

## Snapshot Method

`BackupService` uses SQLite's online backup API rather than a naive file copy.
This creates a transactionally consistent snapshot even when another connection
has recently written to the source DB. Each backup is written to the ignored
local `backups/` directory with a UTC id such as:

```text
triggertrade-20260909T030000Z.sqlite3
triggertrade-20260909T030000Z.json
```

The JSON manifest contains safe metadata only:

- backup id and creation timestamp;
- source DB filename;
- optional source app commit;
- backup filename and size;
- SHA-256 checksum;
- SQLite `PRAGMA integrity_check` result;
- table row-count summary;
- backup duration;
- `contains_secrets=false` when the backup secret scan passes.

Checksum detects corruption or tampering. It is not encryption.

## Verification

Every backup must pass checksum and SQLite integrity verification before it can
be restored to an isolated copy. Restore verification:

1. resolves the backup by managed backup id, not by arbitrary user path;
2. refuses traversal, absolute path injection, missing backups, checksum
   mismatch, and corrupted SQLite files;
3. copies the verified backup to `.tmp/restore-verification/`;
4. opens the restored copy through the real TriggerTrade persistence stores and
   read models;
5. compares critical source/restored identities and counts;
6. generates System History from the restored read model to prove readable,
   bounded, sanitized evidence.

Restore verification never overwrites the active runtime DB automatically.

## Manual Disaster Recovery

Use this procedure for an actual damaged runtime DB:

1. Stop the TriggerTrade runtime.
2. Select the intended backup id from the backup list.
3. Verify the backup checksum and SQLite integrity.
4. Move the damaged runtime DB aside for forensic inspection.
5. Copy the verified backup into the configured runtime DB location.
6. Start TriggerTrade in a safe, reconciliation-first posture.
7. Verify the exact active Set Version and current Rules Version.
8. Refresh account, market, catalog, heartbeat, and readiness evidence.
9. Reconcile open orders and positions against Bybit Demo.
10. Resume entries only after reconciliation succeeds.

If the restored backup contains open or unknown orders/positions, restore alone
does not prove exchange state is current. Bybit Demo may have changed while the
application was down. New entries must remain fail-closed until reconciliation
completes.

## Retention

Retention is intentionally manual in this unit. Scheduled backup automation and
destructive retention cleanup require a separate operational lifecycle review.
