# Research V1 Combined Rules Validation Report

Status: READ_ONLY_RECONCILED_PACKAGE

## Validation Summary

| Check | Result |
|---|---:|
| Combined TradingRulesVersion model confirmed | YES |
| Component Position definitions retained as provenance | 12 |
| Component Portfolio definitions retained as provenance | 5 |
| Operative combined Rules versions | 16 |
| Final hypotheses with Rules context | 30/30 |
| Set relationship coverage | 33/33 |
| Backend-valid combined Rules | 16/16 |
| Ownership violations | 0 |
| Unresolved Rules references | 0 |
| Web import package created | YES |

## Source Fidelity

PASS: The 16 combined versions are derived from actual `BASELINE_CONFIGURATION` and `VARIANT_CONFIGURATION` pairings in the final 30 hypotheses.

PASS: No Cartesian product was created.

PASS: The 10x10 allocation remains operative and old 20%/30% allocations remain provenance only.

PASS: `PR-R-203` remains non-operative.

PASS: `POS-R-007` remains the R-023 replacement Position component.

## Backend Validation

PASS: 16/16 combined versions instantiate through the current `TradingRulesVersionDraft` without semantic loss.

Constructor check against `TradingRulesVersionDraft` + `validate_rules_draft`:

- Result: `BACKEND_VALID=16/16`.
- Dynamic TP validates without fabricated `minimum_take_profit_pct`.
- `max_positions_per_coin` values 2 and 3 validate as methodology-owned per-symbol tranche-slot capacity.
- `minimum_tranche_capital`, `cooldown_minutes`, `stop_loss.mode`, and `minimum_risk_reward.enabled` are present in the serialized draft and participate in the semantic hash.

Non-Rules blockers removed by methodology-first reconciliation:

- Position ATR bindings are preserved as Position construction / certified formula references, not TradingRulesVersion draft fields.
- Fee/cost/funding values are launch, execution, backtest-profile and accounting evidence, not immutable Rules constants.
- Source asset labels are Research universe metadata and launch-time instrument bindings, not Rules semantics.

## Import Readiness

`RULES_READY_FOR_IMPORT: 16`

The documentation package is corrected to the combined model, and `RESEARCH_V1_RULES_WEB_IMPORT.json` is generated for import review. Production import remains intentionally unrun.
