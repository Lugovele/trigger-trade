# Trigger Execution Gap Analysis

Package revision: `RESEARCH_V1_FOCUSED_CORRECTION_R3`

## Original Finding

No current generic declarative trigger evaluator was found that can execute the 31 Research V1 metric predicates from `RuleDefinition.definition`.

The current runtime/backtest trigger path is hardwired to:

- `TRG-001` -> `PercentagePriceMoveTrigger`.
- optionally `TRG-002` -> `RobustVolumeConfirmationTrigger`.

It does not evaluate arbitrary metric references such as `DE`, `ATR percentile`, `BTC_CONTEXT_SCORE`, `RETURN(asset,5m)`, or `classifier_direction` from stored `RuleDefinition` records.

## Smallest Correct Gap Closure

The smallest source-faithful reusable mechanism is one generic declarative metric-predicate implementation family, tentatively keyed as `triggertrade.research.DeclarativeMetricPredicateTrigger`, able to consume the backend `definition` payload in `RESEARCH_V1_TRIGGERS_WEB_IMPORT.json`.

Required capabilities:

- Resolve canonical metric/reference values from already-materialized Set/F-004/F-005/BTC branch evidence without recomputing methodology formulas.
- Compare `EQ`, `GTE`, `LTE`, `GT`, `LT` exactly against string-decimal or enum thresholds.
- Preserve `TRUE`, `FALSE`, `ZERO`, `NONE`, `LONG`, `SHORT`, and `UNAVAILABLE` semantics.
- Preserve source freshness, no-stale-substitution and unavailable propagation rules.
- Respect applicability by coin, BTC exceptions, direction applicability, Set version, and Research-only scope.

Explicit per-trigger implementation keys would be larger and more brittle. Multiple families may be justified later only if the single declarative evaluator cannot cover state-output predicates and numeric predicates without semantic branching.

## Do Not Use Existing Trigger Classes For Research Predicates

Mapping all Research predicates to `PercentagePriceMoveTrigger` or `RobustVolumeConfirmationTrigger` would be semantically lossy. Those classes only implement the legacy/current concrete TRG-001/TRG-002 paths and do not cover F-004/F-005-derived state, BTC return branch construction, contextual agreement, reset predicates, or Research-only applicability.

## Implemented Gap Closure

The generic implementation key `triggertrade.research.DeclarativeMetricPredicateTrigger` is now backed by `triggertrade.triggers.DeclarativeMetricPredicateTrigger`.

Supported declarative schema:

- `research-v1-declarative-metric-predicate@1`
- Operators: `EQ`, `GTE`, `LTE`, `GT`, `LT`.
- Output states: `TRUE`, `FALSE`, `ZERO`, `NONE`, `LONG`, `SHORT`, `UNAVAILABLE`.
- Missing/unavailable metric input propagates as `UNAVAILABLE` and produces no trade-driving signal.
- Numeric comparisons require decimal-compatible operands and fail closed for unsupported numeric input.
- String equality is supported for classifier/state outputs such as `classifier_direction`.

Runtime dispatch is intentionally conservative:

- `TRG-001` and `TRG-002` continue to use their existing concrete implementations.
- Declarative Research triggers are evaluated as additional trigger evidence when present in a futures trigger set and when their metric values are already materialized into the set `config_snapshot` under `declarative_metric_values` or `metric_values`.
- The existing futures strategy path is not changed; `TRG-001` remains the primary trade-driving signal in current futures runtime/backtest execution.

Remaining execution boundary:

- Import/loading is still a separate controlled operation through the existing internal `TriggerSetStore.save_rule()` / `sync_trigger_registry()` path.
- This correction does not create a public HTTP import endpoint and does not mutate production data.
