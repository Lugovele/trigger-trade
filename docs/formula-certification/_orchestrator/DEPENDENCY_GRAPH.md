# Formula Certification Dependency Graph

Status: ORCHESTRATOR_WORKING_GRAPH
Baseline: active methodology v1.2.14
Catalog: `docs/FORMULA_METRICS_CATALOG.md`
Updated: 2026-09-15

This file tracks certification dependencies only. It does not certify formula
semantics, change active methodology, or authorize backend implementation.

## Dependency Classes

- `CERTIFIED_FORMULA`: final formula specification exists with
  `FULL_COUNCIL_APPROVED = YES`.
- `UNCERTIFIED_FORMULA`: formula requires certification before dependent final
  certification can complete.
- `APPROVED_POLICY`: catalog or active methodology marks the dependency
  approved as defined.
- `CONFIG_PARAMETER`: configurable setting whose mechanics may be defined while
  value remains configurable.
- `RESEARCH_PARAMETER`: parameter or assumption reserved for research or
  calibration.
- `DOCUMENTATION_DEPENDENCY`: non-formula active methodology or contract text.
- `UNKNOWN`: identifier or dependency meaning not yet resolved.

## Primary Queue Graph

| ID | Formula | Current dependency classification | Downstream consumers |
|---|---|---|---|
| F-003 | Set ATR and true-range calculation | N-001 `APPROVED_POLICY`; N-008 `APPROVED_POLICY` | F-001, F-004, downstream Position volatility context |
| F-001 | Price-move trigger calculation | F-003 `CERTIFIED_FORMULA`; N-008 `APPROVED_POLICY`; active Set trigger framework `DOCUMENTATION_DEPENDENCY` | F-004, Set trigger formation |
| F-002 | Volume confirmation calculation | N-008 `APPROVED_POLICY`; active Set trigger framework `DOCUMENTATION_DEPENDENCY` | F-004, Set trigger formation |
| F-004 | Set normalization, percentile, and score calculation | F-001 `CERTIFIED_FORMULA`; F-002 `CERTIFIED_FORMULA`; F-003 `CERTIFIED_FORMULA` for 15m ATR/PCT; local 5m ATR_PCT instance certified within F-004; N-008 `APPROVED_POLICY`; active Set methodology `DOCUMENTATION_DEPENDENCY` | F-005, Set analytics/handoff |
| F-005 | Set direction classifier and LONG/SHORT handoff | F-004 `CERTIFIED_FORMULA`; Set direction and Market Handoff contracts `DOCUMENTATION_DEPENDENCY` | F-008, F-006, F-007 |
| F-008 | Planned entry reference selection | F-005 `CERTIFIED_FORMULA`; Position construction and Market Handoff consumption `DOCUMENTATION_DEPENDENCY` | F-006, F-007, F-010, F-011, F-012 |
| F-006 | Position Rules LONG formula | F-003 `CERTIFIED_FORMULA`; F-005 `CERTIFIED_FORMULA`; F-008 `CERTIFIED_FORMULA`; Market Handoff v4 `DOCUMENTATION_DEPENDENCY`; Position Rules Dynamic Stop Loss / LONG section `DOCUMENTATION_DEPENDENCY`; Dynamic SL constants `RESEARCH_PARAMETER` | F-009, F-011/F-012 indirectly |
| F-007 | Position Rules SHORT formula | F-003 `CERTIFIED_FORMULA`; F-005 `CERTIFIED_FORMULA`; F-008 `CERTIFIED_FORMULA`; Position Rules Dynamic Stop Loss / SHORT section `DOCUMENTATION_DEPENDENCY`; Dynamic SL constants `RESEARCH_PARAMETER` | F-009, F-011/F-012 indirectly |
| F-009 | Stop calculation and stop rounding | F-006 `CERTIFIED_FORMULA`; F-007 `CERTIFIED_FORMULA`; F-008 `CERTIFIED_FORMULA`; N-004 `APPROVED_POLICY`; T-004 `RESEARCH_PARAMETER`; Position Rules configuration `CONFIG_PARAMETER` | F-011, F-012 |
| F-010 | Dynamic Take Profit selection and rounding | F-008 `CERTIFIED_FORMULA`; N-004 `APPROVED_POLICY`; T-003 `RESEARCH_PARAMETER` | F-011, F-012 |
| F-011 | Position size, quantity, and actual notional construction | F-008 `CERTIFIED_FORMULA`; F-009 `CERTIFIED_FORMULA`; F-010 `CERTIFIED_FORMULA`; F-014 `APPROVED_POLICY`; F-015 `APPROVED_POLICY`; T-001/T-002 `RESEARCH_PARAMETER` | Order Spec, F-012 |
| F-012 | Risk/reward and minimum net edge calculation | F-008 `CERTIFIED_FORMULA`; F-009 `CERTIFIED_FORMULA`; F-010 `CERTIFIED_FORMULA`; F-011 `CERTIFIED_FORMULA`; A-003 `APPROVED_POLICY`; T-005/T-006/T-010 `RESEARCH_PARAMETER` | Position eligibility, Order Spec economics |
| A-002 | Net final result calculation | A-001 `APPROVED_POLICY`; A-003 `APPROVED_POLICY`; A-004 `CERTIFIED_FORMULA`; A-005 `APPROVED_POLICY`; A-006 `APPROVED_POLICY` | A-009, accounting final result |
| A-004 | Funding calculation and allocation | N-007 `APPROVED_POLICY`; funding/accounting contracts `DOCUMENTATION_DEPENDENCY` | A-002 |
| A-009 | Accounting-day realized totals and daily loss gate input | A-002 `CERTIFIED_FORMULA`; N-007 `APPROVED_POLICY`; T-009 `RESEARCH_PARAMETER` | Daily loss gate input |

## Current Dependency-Safe Order

1. F-003 is already `CERTIFIED`.
2. F-001 is `CERTIFIED`.
3. F-002 is `CERTIFIED`.
4. F-004 is `CERTIFIED`.
5. F-005 is `CERTIFIED`.
6. F-008 is `CERTIFIED`.
7. F-006 is `CERTIFIED`.
8. F-007 is `CERTIFIED`.
9. F-009 is `CERTIFIED`.
10. F-010 is `CERTIFIED`.
11. F-011 is `CERTIFIED`.
12. F-012 is `CERTIFIED`.
13. A-004 is `CERTIFIED`.
14. A-002 is `CERTIFIED`.
15. A-009 is `CERTIFIED`.

## REVIEW_NEEDED Objects

| ID | Status | Queue treatment |
|---|---|---|
| F-013 | CERTIFIED | Final spec approved for generic Set-owned pending-entry invalidation framework. Depends on certified F-001 through F-005 where concrete conditions reference them, N-008, Set lifecycle methodology, SYSTEM_PROTOCOLS evidence eligibility/configuration binding and Order Lifecycle pending-entry state. |
| S-004 | CERTIFIED | Final spec approved as conservative Order Lifecycle finality and release-eligibility rule. Depends on certified A-002/A-004/A-009, approved A-005/A-006/Numeric Policy, SYSTEM_PROTOCOLS P5-P13/P15 and Order Management factual evidence. |
| S-005 | CERTIFIED | Final spec approved only as research/demo diagnostic boundary. It is not a canonical trading input and does not affect Set, Position, Portfolio, Order Lifecycle or execution behavior. |

## System Certification

```text
FORMULA_SYSTEM_FULL_COUNCIL_APPROVED = YES
ANOTHER_SYSTEM_REVIEW_REQUIRED = NO
```

System integration artifacts:

1. `docs/formula-certification/FORMULA_SYSTEM_INTEGRATION_PACK.md`
2. `docs/formula-certification/FORMULA_SYSTEM_FINAL_CERTIFICATION.md`
