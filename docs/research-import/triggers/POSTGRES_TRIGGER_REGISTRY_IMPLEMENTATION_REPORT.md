# PostgreSQL Trigger Definition Registry Implementation Report

## Summary

- Timestamp: `2026-09-27T17:21:06.7498877Z`
- Baseline HEAD: `838df7ab247fed7949db672280c5981c44da92b8`
- Persistence model: `DEDICATED_TABLES`
- Migration added: `migrations/postgres/0023_trigger_rule_definitions.sql`
- Production `public` mutated: `NO`
- Research V1 triggers imported into production: `NO`

## Chosen Persistence Model

The implementation adds a dedicated PostgreSQL table:

- `triggertrade_rule_definitions`

This mirrors the existing SQLite `rule_definitions` contract used by `TriggerSetStore.save_rule()` and `TriggerSetStore.sync_trigger_registry()`.

Dedicated tables were selected instead of generic owner-state because standalone rule/trigger definitions need first-class lookup, listing, identity/version uniqueness, schema-version storage, and digest-based immutable conflict detection equivalent to the SQLite registry.

## Schema

`triggertrade_rule_definitions` stores:

- `rule_id`
- `version`
- `name`
- `status`
- `asset_scope`
- `rule_type`
- `condition`
- `definition_json`
- `definition_hash`
- `schema_version`
- `created_at`
- `updated_at`
- `provenance`
- `inserted_at`

Primary key:

- `(rule_id, version)`

Indexes:

- `(rule_type, rule_id, version)`
- `(status, rule_id, version)`

## Store API

New store:

- `PostgresTriggerRegistry`

Supported methods:

- `save_rule(rule)`
- `save_trigger_version(rule)`
- `sync_trigger_registry(rules)`
- `register_trigger_definitions(rules)`
- `get_rule(rule_id, version=None)`
- `get_trigger_version(trigger_id, version)`
- `get_exact_rule(rule_id, version)`
- `list_rules()`
- `list_trigger_versions()`
- `list_rule_versions(rule_id)`

The store reuses the current `RuleDefinition`, `RuleStatus`, `RuleType`, `RegistrySyncReport`, `definition_hash()`, and trigger validation logic.

## Conflict Semantics

Absent identity:

- inserts the definition.

Exact replay:

- returns unchanged.

Same `rule_id` + `version` with different status, condition, definition payload, or digest:

- rejects as immutable conflict.

Caller-supplied mismatched `semantic_hash`:

- rejects before persistence.

No overwrite, delete, or silent mutation behavior was added.

## Idempotency Semantics

The 31-record Research V1 import dry-run was executed in an isolated PostgreSQL schema:

First import:

- created: `31`
- conflicts: `0`

Second import:

- exact/unchanged: `31`
- created: `0`
- conflicts: `0`

All 31 records resolved through the declarative trigger implementation registry.

The R3 import artifact contains historical `semantic_hash` fields that do not match the current `definition_hash()` computation. The dry-run used the persistence boundary as the digest authority and omitted those stale external hash values while preserving trigger IDs, versions, definitions, metadata, and semantics.

## Existing Trigger Compatibility

`TRG-001` and `TRG-002` bootstrap definitions were imported into an isolated PostgreSQL schema and verified unchanged by digest.

Production `TRG-001` / `TRG-002` data was not modified.

## Validation

Focused real-PostgreSQL tests:

- Command: `python -m pytest tests/unit/test_postgres_trigger_registry.py`
- Result: `4 passed in 149.42s`

Focused and adjacent real-PostgreSQL regression:

- Command: `python -m pytest --basetemp C:\Users\Public\tt-pg-trigger-registry-regression tests/unit/test_postgres_trigger_registry.py tests/unit/test_trigger_sets.py tests/unit/test_declarative_metric_predicate_trigger.py tests/unit/test_backtest_replay.py tests/unit/test_futures_runtime_integration.py tests/unit/test_research_backtest_execution.py tests/unit/test_research_demo_execution.py tests/unit/test_durable_messages.py tests/unit/test_postgres_persistence_foundation.py tests/unit/test_runtime_bootstrap.py tests/integration/test_v1_2_15_canonical_backend_flow.py tests/integration/test_canonical_dispatcher_b12.py`
- Result: `194 passed in 1066.00s`

Affected persistence migration regression:

- Command: `python -m pytest --basetemp C:\Users\Public\tt-pg-trigger-registry-persistence tests/unit/test_capital_grant_store.py tests/unit/test_coins_scope_store.py tests/unit/test_factual_evidence_store.py tests/unit/test_lifecycle_close_authority_store.py tests/unit/test_lifecycle_order_event_store.py tests/unit/test_lifecycle_reconciliation_store.py tests/unit/test_lifecycle_set_sync_store.py tests/unit/test_lifecycle_start_gate_store.py tests/unit/test_lifecycle_submission_store.py tests/unit/test_market_data_fact_store.py tests/unit/test_order_spec_store.py tests/unit/test_portfolio_accounting_day_store.py tests/unit/test_portfolio_cooldown_store.py tests/unit/test_portfolio_data_fact_store.py tests/unit/test_portfolio_state_store.py tests/unit/test_position_config_pin_store.py tests/unit/test_position_construction_store.py tests/unit/test_submit_authorization_store.py tests/unit/test_transport_frontier.py`
- Result: `60 passed in 1406.62s`

## Production Safety

- Production PostgreSQL `public` trigger records created: `NO`
- Production PostgreSQL `public` trigger records updated: `NO`
- Sets imported: `NO`
- Rules imported: `NO`
- Demo started: `NO`
- Backtest started: `NO`
- Deployment performed: `NO`
