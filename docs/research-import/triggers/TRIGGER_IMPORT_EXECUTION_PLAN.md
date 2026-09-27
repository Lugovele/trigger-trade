# Trigger Import Execution Plan

Package revision: `RESEARCH_V1_FOCUSED_CORRECTION_R3`

## Classification

`IMPORT_PATH: EXISTING_INTERNAL_IMPORT_PATH`

## Current State

- 31 canonical Research triggers are source-faithfully extracted.
- 27 backend `RuleDefinition` candidate records remain at deterministic backend version `1.0.0`; corrected BTC deterministic direction triggers `TR-R-BTC-001`, `TR-R-BTC-002`, `TR-R-BTC-003`, and `TR-R-BTC-004` use immutable correction version `1.0.1` with `supersedes_version=1.0.0`.
- 10 metric-reference blockers are reconciled to current Metrics Library formula/state objects.
- 31 records are ready for executable import through the generic declarative Research predicate implementation.

## Next Mechanical Sequence

1. Review the generated `READY` records in `RESEARCH_V1_TRIGGERS_WEB_IMPORT.json`.
2. Load records through `PostgresTriggerRegistry.sync_trigger_registry()` in an isolated-schema dry-run registry first.
3. Verify all 31 records persist with exact source Research IDs and implementation key `triggertrade.research.DeclarativeMetricPredicateTrigger`; 27 records must persist at semver `1.0.0`, while the four corrected BTC deterministic direction records must persist at semver `1.0.1`.
4. Verify target trigger sets materialize the source metric values referenced by each declarative predicate under the runtime-supported `declarative_metric_values`/`metric_values` snapshot contract.
5. Only after review, execute the same internal load path against the target environment; do not create a public HTTP endpoint unless product requirements demand one.

## Semver Mapping

Initial backend representations map to `1.0.0` except for the four corrected BTC deterministic direction triggers:

- `TR-R-BTC-001`: `1.0.0` -> `1.0.1`
- `TR-R-BTC-002`: `1.0.0` -> `1.0.1`
- `TR-R-BTC-003`: `1.0.0` -> `1.0.1`
- `TR-R-BTC-004`: `1.0.0` -> `1.0.1`

Source Research trigger identity and source revision remain preserved in `definition.source_revision` and canonical artifacts.
