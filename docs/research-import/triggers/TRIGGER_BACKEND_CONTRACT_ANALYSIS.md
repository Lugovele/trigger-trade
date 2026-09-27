# Trigger Backend Contract Analysis

Package revision: `RESEARCH_V1_FOCUSED_CORRECTION_R3`

## Contract Sources

- `src/triggertrade/trigger_sets/contracts.py`: `RuleDefinition`, `TriggerVersion`, `RuleStatus`, `RuleType`, current selectable constants.
- `src/triggertrade/persistence/trigger_set_store.py`: `save_rule`, `sync_trigger_registry`, `_validate_rule_definition`, `_implementation_key`, exact rule/set resolution.
- `src/triggertrade/services/futures_runtime.py` and `src/triggertrade/backtest/engine.py`: concrete trigger execution paths.
- `src/triggertrade/triggers/percentage_price_move.py` and `src/triggertrade/triggers/volume_confirmation.py`: current executable trigger classes.

## Required Backend Fields

`RuleDefinition` requires: `rule_id`, `version`, `name`, `status`, `asset_scope`, `rule_type`, `condition`, `definition`, `created_at`, `provenance`.

Optional fields are: `updated_at`, `logical_name`, `description`, `supersedes_version`, `formula`, `parameter_snapshot`, `input_contract`, `output_contract`, `boundary_semantics`, `stale_data_semantics`, `missing_data_semantics`, `semantic_hash`, `change_summary`.

## Validation Rules

- Trigger versions must use semantic versioning (`^\d+\.\d+\.\d+$`).
- Trigger records require a non-empty `implementation_key` resolved by explicit `definition[implementation_key]` or hardcoded known rule IDs.
- `condition` is required.
- Current selectable trigger versions are separate hard-coded production-selection constants, currently `TRG-001@0.2.0` only.

## Implementation Key Findings

`implementation_key` is required because trigger versions are expected to map to executable runtime behavior. The store validates non-empty key material; runtime/backtest execution resolves the generic Research implementation key when evaluating declarative Research predicate members.

Current executable trigger implementations found:

- `triggertrade.triggers.PercentagePriceMoveTrigger` for `TRG-001`.
- `triggertrade.triggers.RobustVolumeConfirmationTrigger` for `TRG-002`.
- `triggertrade.research.DeclarativeMetricPredicateTrigger` for declarative Research V1 metric predicates.

Other implementation keys in the registry are strategy/risk/context implementations.

The generic declarative implementation intentionally consumes already-materialized metric/state values from trigger-set runtime context (`declarative_metric_values` or `metric_values`) and does not recompute frozen methodology formulas inside trigger code.

## Import Path Classification

`EXISTING_INTERNAL_IMPORT_PATH`: `TriggerSetStore.save_rule()` / `TriggerSetStore.sync_trigger_registry()` can load structurally valid `RuleDefinition` records. No public HTTP trigger import endpoint, CLI, or Research trigger-specific import service was found.
