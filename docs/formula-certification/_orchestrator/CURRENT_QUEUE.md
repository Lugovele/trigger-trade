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

1. F-013 — Set pending invalidation and stale-signal eligibility
   - State: `CERTIFIED`
   - Evidence: `F-013/F-013_FINAL_FORMULA_SPECIFICATION.md`
2. S-004 — Order Lifecycle finality and closed-state predicate
   - State: `CERTIFIED`
   - Evidence: `S-004/S-004_FINAL_SPECIFICATION.md`
3. S-005 — Market regime classifier
   - State: `CERTIFIED`
   - Evidence: `S-005/S-005_FINAL_SPECIFICATION.md`

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
16. F-013 — Set pending invalidation and stale-signal eligibility
17. S-004 — Order Lifecycle finality and closed-state predicate
18. S-005 — Market regime classifier research/demo diagnostic boundary

## Waiting For Dependencies

None.

## Source Pack Ready For Later

None.

## Not Started But Dependency-Available Later

None.

## Primary Queue Completion

All primary queue formulas are `CERTIFIED`.

## REVIEW_NEEDED Queue

1. F-013 — `CERTIFIED`
2. S-004 — `CERTIFIED`
3. S-005 — `CERTIFIED`

## System Integration

Status:

```text
FORMULA_SYSTEM_FULL_COUNCIL_APPROVED = YES
ANOTHER_SYSTEM_REVIEW_REQUIRED = NO
```

Artifacts:

1. `FORMULA_SYSTEM_INTEGRATION_PACK.md`
2. `FORMULA_SYSTEM_FINAL_CERTIFICATION.md`
