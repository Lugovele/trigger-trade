# Trigger Import Execution Plan

Package revision: `RESEARCH_V1_FOCUSED_CORRECTION_R3`

## Classification

`IMPORT_PATH: EXISTING_INTERNAL_IMPORT_PATH`

## Current State

- 31 canonical Research triggers are source-faithfully extracted.
- 31 backend `RuleDefinition` candidate records are structurally representable with deterministic backend version `1.0.0`.
- 10 metric-reference blockers are reconciled to current Metrics Library formula/state objects.
- 31 records are ready for executable import through the generic declarative Research predicate implementation.

## Next Mechanical Sequence

1. Review the generated `READY` records in `RESEARCH_V1_TRIGGERS_WEB_IMPORT.json`.
2. Load records through `TriggerSetStore.sync_trigger_registry()` in a local/dry-run registry first.
3. Verify all 31 records persist with semver `1.0.0`, exact source Research IDs, and implementation key `triggertrade.research.DeclarativeMetricPredicateTrigger`.
4. Verify target trigger sets materialize the source metric values referenced by each declarative predicate under the runtime-supported `declarative_metric_values`/`metric_values` snapshot contract.
5. Only after review, execute the same internal load path against the target environment; do not create a public HTTP endpoint unless product requirements demand one.

## Semver Mapping

All first backend representations map to `1.0.0`; source Research trigger identity and source revision remain preserved in `definition.source_revision` and canonical artifacts.
