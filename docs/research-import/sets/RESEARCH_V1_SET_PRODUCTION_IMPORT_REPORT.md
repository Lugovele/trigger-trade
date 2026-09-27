# Research V1 Set Production Import Report

## Import Context

- Production image / commit: `83b378f61737feedd8f703641ce84bd49a8c0db0`
- Import timestamp: `2026-09-27T20:54:35.324314+00:00`
- Source package: `docs/research-import/sets/RESEARCH_V1_SETS.json`
- Source package SHA-256: `37c74bceee989bcf44c0cc1d70ef37bf75b9a1fe4c07756211c991beb422051d`
- Production registry: `PostgresResearchSetRegistry`
- Production migration baseline: `0024 research_set_registry`

## Rebind Decision

Decision: `CORRECT_EXISTING_PREIMPORT_ARTIFACTS`

Production Research Set versions had not yet been imported when the corrected BTC directional trigger versions were introduced. The Set package therefore corrected the existing pre-import artifacts in place instead of creating unnecessary new Set versions.

## Affected Set Versions

- `SET-R-BTC-001-V1`
- `SET-R-BTC-001-V2`
- `SET-R-BTC-003-V2`
- `SET-R-BTC-007-V2`
- `SET-R-BTC-008-V2`
- `SET-R-BTC-009-V2`
- `SET-R-BTC-011-V2`
- `SET-R-BTC-012-V2`
- `SET-R-BTC-015-V2`
- `SET-R-BTC-016-V2`
- `SET-R-BTC-019-V1`
- `SET-R-BTC-019-V2`
- `SET-R-BTC-020-V1`
- `SET-R-BTC-020-V2`
- `SET-R-BTC-021-V1`
- `SET-R-BTC-021-V2`

## BTC Trigger Version Updates

- `TR-R-BTC-001@1.0.0` -> `TR-R-BTC-001@1.0.1`
- `TR-R-BTC-002@1.0.0` -> `TR-R-BTC-002@1.0.1`
- `TR-R-BTC-003@1.0.0` -> `TR-R-BTC-003@1.0.1`
- `TR-R-BTC-004@1.0.0` -> `TR-R-BTC-004@1.0.1`

Affected member references rebound: `34`.
Superseded BTC `1.0.0` references remaining in affected Sets: `0`.

## Isolated PostgreSQL Dry Run

- Isolated schema: `tt_sets_rebind_a20b9691ad5f4df5`
- Migrations applied through: `0024`
- Trigger seed records: `31`
- First pass created: `33`
- First pass exact matches: `0`
- First pass conflicts: `0`
- First pass invalid definitions: `0`
- Second pass created: `0`
- Second pass exact matches: `33`
- Second pass conflicts: `0`
- Membership rows: `242`
- Unresolved trigger references: `0`
- Exact round-trip: `33/33`

## Production Import

Preflight before mutation:

- `SET_IMPORT_TOTAL`: `33`
- `ABSENT`: `33`
- `EXACT_MATCH`: `0`
- `CONFLICT`: `0`

Import result:

- Created: `33`
- Already exact: `0`
- Conflicts: `0`
- Invalid definitions: `0`

Idempotency result:

- Absent after import: `0`
- Exact after import: `33`
- Conflicts after import: `0`
- Second-pass created: `0`
- Second-pass exact: `33`
- Second-pass conflicts: `0`
- Second-pass invalid definitions: `0`

## Registry Verification

- Research Set versions present: `33/33`
- Membership rows present: `242`
- Trigger references resolved: `242/242`
- Exact round-trip: `33/33`
- Corrected BTC `1.0.1` references in affected Sets: `34`
- Superseded BTC `1.0.0` references in affected Sets: `0`

## Production Health

Before import:

- PostgreSQL: `RUNNING`
- Migrations: `RUNNING`, latest `0024 research_set_registry`
- Outbox: `DEGRADED`, with one expired in-flight message lock
- Inbox: `RUNNING`
- Runtime heartbeat: `RUNNING`

After import:

- PostgreSQL: `RUNNING`
- Migrations: `RUNNING`, latest `0024 research_set_registry`
- Outbox: `DEGRADED`, with one expired in-flight message lock
- Inbox: `RUNNING`
- Runtime heartbeat: `RUNNING`

No new production degradation was observed from the Set import. The outbox degradation was present before the import and remained in the same condition afterward.

## Web Visibility

Current dashboard/API code does not expose the standalone `PostgresResearchSetRegistry` as a Research Set web/read endpoint. Existing dashboard Set read paths target the older Research configuration registry / TriggerSetVersion projections, not `triggertrade_research_set_versions`.

`WEB_SET_READ_VISIBLE`: `NOT_EXPOSED`

## Boundaries Preserved

- Trigger definitions were not modified.
- Old BTC trigger `1.0.0` versions were not deleted or overwritten.
- Rules were not imported.
- Research was not started.
- Demo was not started.
- No deployment, commit, or push was performed.
