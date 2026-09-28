# Research Trigger / Set Web Completion Report

## Scope

This task completed read-only dashboard/API visibility for immutable Research V1 Triggers and Research V1 Sets.

No production data was mutated. No Trigger, Set, Rules, or methodology semantics were changed.

## Files Changed

- `src/triggertrade/dashboard/__main__.py`
- `src/triggertrade/dashboard/product_ui.py`
- `src/triggertrade/dashboard/research_triggers.py`
- `src/triggertrade/dashboard/research_sets.py`
- `tests/e2e/test_dashboard_user_journeys.py`
- `tests/unit/test_runtime_bootstrap.py`
- `tests/unit/test_research_trigger_web_read.py`
- `tests/unit/test_postgres_research_set_registry.py`
- `docs/research-import/web/RESEARCH_TRIGGER_SET_WEB_COMPLETION_REPORT.md`

## Read API Changes

- Existing Research Trigger API remains read-only:
  - `GET /api/research/triggers`
  - `GET /api/research/triggers/<trigger_id>`
  - `GET /api/research/triggers/<trigger_id>/<version>`
- Added read-only Research Set API backed by `PostgresResearchSetRegistry`:
  - `GET /api/research/sets`
  - `GET /api/research/sets/<set_id>/<set_version>`
- No write route was added for Triggers or Sets.

## UI / Routes Added

- `/research/triggers` opens the Research Triggers inspection table.
- `/research/sets` opens the Research Sets inspection table.
- The Research page now has Research-owned `Overview`, `Triggers`, and `Sets` subnavigation.
- Imported Research Trigger and Set inspection panels are no longer presented as Trading Configuration tabs.
- Research Triggers now show:
  - Trigger
  - Version
  - Metric
  - Formula
  - Condition
  - Output
  - Applicability
  - Status
  - Version State
- Research Sets now show:
  - Set
  - Version
  - Hypothesis
  - Direction
  - Coin / Scope
  - Trigger Count
  - Status
  - Version State
- Detail panes expose exact immutable raw config for human verification.

## Trigger Version-State Logic

For each logical trigger ID, the highest persisted version is projected as `CURRENT`; all lower persisted versions are projected as `HISTORICAL`.

This is generic version ordering and does not hard-code BTC trigger IDs.

## Set Version-State Logic

For each logical Research Set ID, the highest persisted Set version is projected as `CURRENT`; all lower persisted versions are projected as `HISTORICAL`.

This is generic version ordering and does not derive from Research status such as `RESEARCH_ONLY`.

## BTC Trigger Verification

The projection renders authoritative persisted `output_states`.

Expected current BTC rows are supported:

- `TR-R-BTC-001@1.0.1`: `LONG, ZERO, UNAVAILABLE`
- `TR-R-BTC-002@1.0.1`: `SHORT, ZERO, UNAVAILABLE`
- `TR-R-BTC-003@1.0.1`: `LONG, ZERO, UNAVAILABLE`
- `TR-R-BTC-004@1.0.1`: `SHORT, ZERO, UNAVAILABLE`

## BTC Set Verification

The Set dashboard/API reads exact `ResearchSetTriggerMember` records from `PostgresResearchSetRegistry`.

Real PostgreSQL validation confirmed the 16 affected BTC Set versions expose corrected `TR-R-BTC-001..004@1.0.1` memberships and zero superseded BTC `1.0.0` memberships for those trigger IDs.

Affected BTC Set versions verified:

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

## Tests

Focused local tests:

- `python -m py_compile src\triggertrade\dashboard\research_triggers.py src\triggertrade\dashboard\research_sets.py src\triggertrade\dashboard\__main__.py src\triggertrade\dashboard\product_ui.py tests\unit\test_research_trigger_web_read.py tests\unit\test_postgres_research_set_registry.py`
- `python -m pytest tests\unit\test_research_trigger_web_read.py -q` -> `6 passed`
- `python -m pytest --basetemp .tt-tmp\pytest-web-ui-2 tests\unit\test_research_trigger_web_read.py tests\unit\test_runtime_bootstrap.py::test_dashboard_startup_bootstraps_registry_before_read_only_render -q` -> `7 passed` when rerun outside the sandbox after pytest temp-directory permission failures.
- `python -m pytest tests\unit\test_dashboard_research_api.py -q` -> `19 passed` when rerun outside the sandbox after pytest temp-directory permission failures.

Real PostgreSQL isolated-schema validation:

- Resolved existing Azure Container App `postgres-dsn` secret into the local process environment without printing or writing the DSN.
- `python -m pytest tests\unit\test_postgres_trigger_registry.py::test_research_v1_trigger_package_imports_idempotently_into_postgres_registry tests\unit\test_postgres_trigger_registry.py::test_corrected_btc_direction_trigger_versions_import_idempotently_into_postgres_registry -q` -> `2 passed`
- `python -m pytest tests\unit\test_postgres_research_set_registry.py::test_research_v1_set_package_imports_idempotently_and_round_trips_exactly tests\unit\test_postgres_research_set_registry.py::test_dashboard_reads_research_sets_from_postgres_registry -q` -> `2 passed`
- Final combined real PostgreSQL run for the trigger package, corrected BTC versions, Research Set package, and dashboard Set API checks -> `4 passed`

The real PostgreSQL Set package test validated:

- `33/33` Research Sets persisted/read back.
- `242/242` memberships persisted/read back.
- First pass created `33`.
- Second pass exact/unchanged `33`.
- Conflicts `0`.

The real PostgreSQL dashboard Set API test validated:

- `33/33` Research Sets returned.
- `16/16` affected BTC Set versions visible.
- Corrected BTC `1.0.1` references in affected Sets: `34`.
- Superseded BTC `1.0.0` references in affected Sets: `0`.
- Detail route returns ordered trigger memberships.
- POST mutation path remains blocked by operator authorization and no Set write endpoint was added.

## Deployment

Deployment is still pending. No push, deploy, Research run, Demo run, or production mutation was performed.
