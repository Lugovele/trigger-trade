# TriggerTrade Operational Runbooks

Status: formula-agnostic post-freeze operations.

These runbooks describe the current frozen backend only. They do not certify formulas, change thresholds, promote research automatically, or authorize live mainnet trading.

## Operating Boundary

- Canonical business blocks remain Portfolio Rules, Set, Position Rules, Order Lifecycle, and API / Adapter Gateway.
- Formula and accounting items gated in `docs/FORMULA_METRICS_CATALOG.md` must not be implemented or activated as final calculation behavior.
- `docs/formula-certification/` is separate certification work and is not part of backend operations.
- Legacy/demo scripts remain compatibility tools, not canonical deployed runtime paths.

## Environment

Required for canonical durable roles:

```powershell
$env:TRIGGERTRADE_POSTGRES_DSN = "<postgres dsn>"
```

Optional:

```powershell
$env:TRIGGERTRADE_POSTGRES_SCHEMA = "public"
$env:TRIGGERTRADE_PROCESS_ROLE = "web"              # web | trading-worker | scheduler
$env:TRIGGERTRADE_DASHBOARD_HOST = "0.0.0.0"
$env:TRIGGERTRADE_DASHBOARD_PORT = "8765"
```

Deployed dashboard/API access must use managed OIDC / Entra-compatible authentication. The process-local token mode is local/dev compatibility only and is not canonical deployed authentication.

Never print, paste, commit, or include DSNs, API keys, authorization headers, cookies, OIDC tokens, or local-dev tokens in tickets, logs, screenshots, fixtures, or audit payloads.

## Local Startup

Apply PostgreSQL migrations:

```powershell
python scripts\apply_postgres_migrations.py
```

Run one role:

```powershell
$env:TRIGGERTRADE_PROCESS_ROLE = "web"
python -m triggertrade.services.runtime
```

```powershell
$env:TRIGGERTRADE_PROCESS_ROLE = "trading-worker"
python -m triggertrade.services.runtime
```

```powershell
$env:TRIGGERTRADE_PROCESS_ROLE = "scheduler"
python -m triggertrade.services.runtime
```

`research-worker` is reserved for later traced implementation and must not be launched as a canonical role yet.

## Azure Deployment

Use the existing deployment script only from a clean tracked working tree:

```powershell
.\scripts\deploy-azure.ps1 -Roles web,trading-worker,scheduler
```

The script sets `TRIGGERTRADE_PROCESS_ROLE` per Container App role and checks web `/healthz`. Azure/container supervision owns process restart for `web`, `trading-worker`, and `scheduler`.

## Readiness And Diagnostics

Web liveness/readiness:

```powershell
Invoke-WebRequest http://127.0.0.1:8765/healthz
Invoke-WebRequest http://127.0.0.1:8765/api/readiness
```

Container role health:

```powershell
python -m triggertrade.services.container_health
```

Sanitized PostgreSQL diagnostics:

```powershell
python scripts\diagnose_backend.py --pretty
```

The diagnostic snapshot reports migration state, durable outbox/inbox counts, owner-state counts, heartbeat status, and durable research promotion request count. It does not emit payload JSON, DSNs, secrets, tokens, authorization headers, or raw heartbeat details.

## Worker Restart

1. Stop the affected `trading-worker` container or local process with normal process supervision.
2. Confirm no manual database edits were made.
3. Start the `trading-worker` role again.
4. Run:

```powershell
python scripts\diagnose_backend.py --pretty
```

5. Investigate `outbox`, `inbox`, and `role_heartbeat` checks if status is `DEGRADED`, `BLOCKED`, or `UNAVAILABLE`.

Do not replay or delete durable outbox/inbox rows manually. Fail closed when durable state is uncertain.

## Scheduler Restart

1. Stop and restart only the `scheduler` role.
2. Confirm PostgreSQL reachability:

```powershell
python -m triggertrade.services.container_health
```

3. Use diagnostics to inspect Scheduler-consumer outbox rows:

```powershell
python scripts\diagnose_backend.py --pretty
```

The current scheduler role hydrates durable state and remains formula-agnostic. Do not add formula execution or automatic research promotion through operational action.

## Graceful Shutdown

Use container/runtime stop signals or Ctrl+C for local processes. The role launcher installs stop handlers where supported. After restart, rely on durable PostgreSQL state, outbox/inbox idempotency, and readiness diagnostics rather than in-memory assumptions.

## Stuck Outbox Or Inbox

Run:

```powershell
python scripts\diagnose_backend.py --pretty
```

Interpretation:

- `outbox` DEGRADED with pending messages: a consumer role may be stopped, blocked, or intentionally fail-closed behind formula gates.
- `outbox` DEGRADED with expired in-flight locks: a worker likely stopped after claiming work; restart the correct role and verify it reclaims safely.
- `inbox` DEGRADED: messages were received but not marked processed; inspect the owning role before retrying any side effect.
- `role_heartbeat` BLOCKED: the worker recorded a fail-closed condition; do not bypass it manually.

Manual row mutation is not an approved recovery procedure.

## PostgreSQL Unavailable

1. Confirm `TRIGGERTRADE_POSTGRES_DSN` is configured in the process environment.
2. Run:

```powershell
python -m triggertrade.services.container_health
```

3. Confirm migrations separately only after connectivity is restored:

```powershell
python scripts\apply_postgres_migrations.py
```

Canonical deployed roles must not fall back to filesystem or SQLite state.

## Authentication Failure

For deployed dashboard/API failures:

1. Verify the managed OIDC / Entra-compatible access layer is configured outside TriggerTrade.
2. Confirm the authenticated principal is authorized for the requested operator/admin command.
3. Inspect durable operator command audit records through approved application views or restricted database operations.

Do not enable process-local token mode to repair deployed authentication. Do not log or paste token contents.

## Worker Heartbeat Missing

Run:

```powershell
python scripts\diagnose_backend.py --pretty
```

If `role_heartbeat` is missing or degraded:

1. Confirm the correct process role is running.
2. Confirm PostgreSQL is reachable from that role.
3. Confirm no outbox message caused a fail-closed block.
4. Restart through container supervision if the process is absent.

Do not treat a stale or missing heartbeat as success.

## Backup / Restore Drill

Run the isolated repository drill against a test PostgreSQL database or schema:

```powershell
python scripts\postgres_recovery_drill.py
```

Optional inspection:

```powershell
python scripts\postgres_recovery_drill.py --keep-schemas
```

See `docs/POSTGRES_BACKUP_RESTORE_DRILL.md`. The drill uses only schemas prefixed `tt_recovery_drill_` and does not touch production schemas.

Production point-in-time recovery policy belongs to managed PostgreSQL backup tooling. After any restore, re-run migrations and diagnostics before starting canonical roles.

## Research Promotion Incident

Research promotion is an authorized operator command only. It must be evidence-pinned, idempotent, durably audited, rollback-aware, and isolated from live order execution.

If promotion appears blocked:

1. Confirm selected research evidence exists and required demo state is stopped where applicable.
2. Confirm Formula Certification gates still permit only structure/parameterization where required.
3. Inspect durable research promotion requests with:

```powershell
python scripts\diagnose_backend.py --pretty
```

Do not mutate SQLite trigger/rules state to make research active. Do not promote automatically. Do not bypass Formula Certification or owner gates.

## Legacy / Demo Compatibility

Compatibility scripts under `scripts/` may still exercise legacy/demo paths when explicitly invoked. They are not canonical deployed runtime launchers.

Examples:

- `scripts\paper_runtime_smoke.py`
- `scripts\triggertrade_demo_soak.py`
- `scripts\bybit_demo_futures_smoke.py`

Do not use compatibility scripts as proof that canonical deployed roles are healthy.

## Validation Before And After Operations

Run the formula-agnostic backend validation contract:

```powershell
python scripts\validate_non_formula_backend.py
```

Run methodology integrity validation:

```powershell
python scripts\validate_methodology_integrity.py
```

Run diagnostics when PostgreSQL is configured:

```powershell
python scripts\diagnose_backend.py --pretty
```

Do not weaken tests, formula gates, or readiness checks to obtain a green run.

## Formula Certification Period: What Not To Do

- Do not implement or activate final formula/accounting behavior for gated catalog items.
- Do not change thresholds, calibration values, Entry, Stop, Dynamic Take, sizing, allocation, P&L, funding, drawdown, or research metric semantics.
- Do not manually promote research output into canonical active configuration.
- Do not use SQLite/filesystem stores as canonical deployed truth.
- Do not place live orders or enable mainnet behavior through operational shortcuts.
- Do not edit approved methodology or archived methodology during operations.
