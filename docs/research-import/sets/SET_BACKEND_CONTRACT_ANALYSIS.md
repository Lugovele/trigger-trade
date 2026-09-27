# Set Backend Contract Analysis

## Current Set Import Contract

- Model: `triggertrade.trigger_sets.TriggerSetVersion` in `src/triggertrade/trigger_sets/contracts.py`.
- Required fields: `set_id`, `version`, `purpose`, `status`, `symbol`, `timeframe`, `rule_versions`, `strategy_version`, `risk_profile_version`, `config_snapshot`, `created_at`, `provenance`.
- SQLite store/import path: `TriggerSetStore.sync_trigger_sets()` / `_create_set_result()` in `src/triggertrade/persistence/trigger_set_store.py`.
- SQLite validation: `_validate_trigger_set_version()` requires `vN` Set version naming, non-empty exact rule memberships, and semantic trigger versions for trigger memberships. `_validate_membership()` verifies each membership exists in SQLite `rule_definitions`.
- SQLite digest: `composition_hash(trigger_set)` includes identity, purpose, scope, composition mode, ordered member refs, strategy/risk versions, and `config_snapshot`.
- PostgreSQL Research configuration path: `PostgresResearchConfigurationRegistry.put_trigger_set_version()`, `get_trigger_set_version()`, `list_trigger_set_versions()` in `src/triggertrade/persistence/postgres_research_registry.py`, stored as owner-state `ResearchConfigurationRegistry / TRIGGER_SET_VERSION`.
- PostgreSQL owner-state behavior: `put_if_absent()` provides immutable identity/content protection, but this path does not provide a standalone Set registry table, does not validate member trigger refs against `PostgresTriggerRegistry`, and reconstructs `TriggerSetStatus.TESTING` on read.

## Research Set Registry Contract

- Model: `ResearchSetVersion` / `ResearchSetTriggerMember` in `src/triggertrade/persistence/postgres_research_set_registry.py`.
- PostgreSQL import path: `PostgresResearchSetRegistry.sync_research_sets()`.
- Migration: `migrations/postgres/0024_research_set_registry.sql`.
- Storage model: dedicated immutable Research Set version table plus normalized trigger-membership table.
- Required fields preserve the source Research Set artifact: `set_id`, `set_version`, `backend_set_id`, `backend_version`, `display_name`, `status`, Research source references, applicability, ordered trigger members, composition logic, direction semantics, edge behavior, provenance, source excerpt, backend mapping, and canonical digest.
- Trigger membership validation: every `(trigger_id, trigger_version)` resolves through `PostgresTriggerRegistry` before persistence.
- Exact replay returns unchanged. Changed canonical payload under the same `(set_id, set_version)` is rejected.
- The Research Set registry intentionally does not require `strategy_version` or `risk_profile_version`; those belong to a later trading Rules/activation artifact.

## Readiness Classification

`POSTGRES_RESEARCH_SET_REGISTRY_READY`

The repository now has a standalone PostgreSQL Research Set registry/import path for immutable Research-only trigger compositions. Production import remains a separate controlled task and must first verify the 31 trigger definitions exist in the target schema.
