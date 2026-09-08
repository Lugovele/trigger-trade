# Code-First Trigger and Set Workflow

TriggerTrade creates Trigger and Trigger Set versions through reviewed code, not
through UI editing. The dashboard remains a read-only projection over factual
registry rows.

## Source of Truth

The existing registry is the source of truth:

- `rule_definitions` stores immutable exact versions for triggers, strategy
  rules, risk profiles, and context rules.
- `trigger_set_versions` stores immutable exact Set Version composition plus
  lifecycle status.
- `trigger_set_memberships` stores exact member identities as
  `rule_id + rule_version`.

This intentionally evolves the current registry in place. Do not add a second
parallel Trigger or Set registry.

## Trigger Versions

A Trigger has a stable logical identity such as `TRG-002`.

A Trigger Version has an exact immutable identity such as `TRG-002@0.2.0`.
Semantic logic, implementation identity, version-defining parameters, input
contract, output contract, boundary semantics, stale-data behavior, and
missing-data behavior belong to the version definition.

Changing semantic logic or version-defining parameters requires a new semantic
version. Current Trigger versions use `MAJOR.MINOR.PATCH`:

- `PATCH`: behavior-preserving metadata or implementation correction only when
  semantic identity is unchanged.
- `MINOR`: compatible semantic or parameter evolution.
- `MAJOR`: fundamental logic or contract change.

## Definition Hash

Each stored rule/trigger version has a deterministic SHA-256 `definition_hash`.
The hash includes semantic fields such as identity, version, implementation key,
condition, definition payload, formula/contracts, and version-defining
parameters. It excludes volatile fields such as timestamps.

The same `trigger_id + version` may be re-registered only when the hash and
stored semantic payload match. A changed definition under the same version fails
closed with an explicit version-bump error.

## Set Versions

A Trigger Set has a stable logical identity such as `triggertrade-futures-core`.

A Set Version has an exact immutable identity such as
`triggertrade-futures-core@v1`. The Set Version records exact member versions.
Membership may include trigger, strategy, risk, and context rule versions because
that is the current TriggerTrade runtime composition model.

Changing membership, ordering where meaningful, role/gate meaning, strategy or
risk membership, context membership, or composition mode requires a new Set
Version. Set versions use monotonic `vN` names with optional existing suffixes
such as `v2-test`.

## Composition Hash

Each Set Version has a deterministic SHA-256 `composition_hash`. It includes
set identity, set version, scope, ordered exact member versions, inferred member
roles, strategy/risk profile identity, composition mode, config snapshot, and
schema version.

Lifecycle status is deliberately excluded from `composition_hash`. Status is a
controlled lifecycle state, not Set signal-composition semantics.

## Registration and Bootstrap

Use the official store/bootstrap path:

1. Register code-defined rule/trigger versions.
2. Register code-defined Set Versions.
3. Reconcile lifecycle/current activation where explicitly approved.

The APIs are:

- `TriggerSetStore.sync_trigger_registry(...)`
- `TriggerSetStore.sync_trigger_sets(...)`
- `bootstrap_current_trigger_sets(...)`
- `ensure_runtime_registry_initialized(...)`

The sync report lists unchanged versions, newly registered versions, conflicts,
invalid definitions, and warnings. Bootstrap fails closed if conflicts or invalid
definitions are present. New exact versions may register without manual SQL.

## Runtime and Backtest Resolution

Runtime and backtest resolution must start from an exact Set Version:

```text
set_id + set_version
        -> exact trigger_set_memberships
        -> exact Trigger Versions
        -> implementation_key / implementation
        -> deterministic signals
```

Do not resolve `trigger_id -> latest`. Missing exact Trigger Versions block Set
registration and should not be substituted at runtime or replay time.

## Developer Workflow

New Trigger:

1. Define the implementation.
2. Assign a new `trigger_id + version`.
3. Define metadata, contracts, and exact version-defining parameters.
4. Run registry sync/validation tests.
5. Complete required specialist review.
6. Commit and restart/bootstrap after approval.

Change existing Trigger:

1. Do not mutate a used version.
2. Create a new version.
3. Preserve old versions.
4. Create or update a new Set Version if desired.
5. Validate and review.

Change Set:

1. Create a new Set Version.
2. Reference exact member versions.
3. Preserve old Set Versions.
4. Do not auto-activate the new Set Version.

## Boundaries

Do not add frontend Trigger/Set CRUD. Do not add Research backend here. Do not
move Trading Rules into Sets. Do not change execution semantics, Dynamic TP,
SHORT alpha, or Daily Loss enforcement as part of registry sync work.
