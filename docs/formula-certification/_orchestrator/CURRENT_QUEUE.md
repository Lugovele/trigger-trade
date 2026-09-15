# Current Formula Certification Queue

Status: ORCHESTRATOR_QUEUE
Updated: 2026-09-15

## Product Decision Required

Decision register:
`docs/formula-certification/_orchestrator/PRODUCT_DECISIONS_REQUIRED.md`

Resolved by product owner on 2026-09-15. See revised candidates:

1. `_orchestrator/work/F-001/F-001_REVISED_SPEC_CYCLE_1.md`
2. `_orchestrator/work/F-002/F-002_REVISED_SPEC_CYCLE_1.md`

## Actionable Now

1. F-010 — Dynamic Take Profit selection and rounding
   - State: `CERTIFIED`
   - Evidence: `F-010/F-010_FINAL_FORMULA_SPECIFICATION.md`
2. F-011 — Position size, quantity, and actual notional construction
   - State: `CERTIFIED`
   - Evidence: `F-011/F-011_FINAL_FORMULA_SPECIFICATION.md`
3. F-012 — Risk/reward and minimum net edge calculation
   - State: `CERTIFIED`
   - Evidence: `F-012/F-012_FINAL_FORMULA_SPECIFICATION.md`
   - Evidence bundle: catalog, active methodology excerpts, certified F-008,
     F-009, F-010 and F-011 final specifications, plus approved A-003 policy
     and T-005/T-006/T-010 research-parameter evidence if referenced.

## Certified

1. F-003 — Set ATR and true-range calculation
2. F-001 — Price-move trigger calculation
3. F-002 — Volume confirmation calculation
4. F-004 — Set normalization, percentile, and score calculation
5. F-005 — Set direction classifier and LONG/SHORT handoff
6. F-008 — Planned entry reference selection
7. F-006 — Position Rules LONG formula
8. F-007 — Position Rules SHORT formula
9. F-009 — Stop calculation and stop rounding
10. F-010 — Dynamic Take Profit selection and rounding
11. F-011 — Position size, quantity, and actual notional construction
12. F-012 — Risk/reward and minimum net edge calculation
13. A-004 — Funding calculation and allocation
14. A-002 — Net final result calculation
15. A-009 — Accounting-day realized totals and daily loss gate input

## Waiting For Dependencies

None.

## Source Pack Ready For Later

None.

## Not Started But Dependency-Available Later

None currently identified.

## Completion

All primary queue formulas are `CERTIFIED`.

## Excluded Unless Required

1. F-013
2. S-004
3. S-005
