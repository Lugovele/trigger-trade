# Formula Certification Status

Status: ORCHESTRATOR_DASHBOARD
Updated: 2026-09-15

State machine:

```text
NOT_STARTED
SOURCE_PACK_READY
REVIEWING
REVISION_REQUIRED
WAITING_FOR_DEPENDENCY
WAITING_FOR_PRODUCT_DECISION
FULL_COUNCIL_APPROVED
CERTIFIED
```

## Primary Queue

| Order | ID | Formula | State | Evidence / latest artifact | Notes |
|---:|---|---|---|---|---|
| 1 | F-003 | Set ATR and true-range calculation | CERTIFIED | `F-003/F-003_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`. |
| 2 | F-001 | Price-move trigger calculation | CERTIFIED | `F-001/F-001_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved for narrow completed-minute displacement Trigger role. |
| 3 | F-002 | Volume confirmation calculation | CERTIFIED | `F-002/F-002_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved as short-horizon relative participation confirmation. |
| 4 | F-004 | Set normalization, percentile, and score calculation | CERTIFIED | `F-004/F-004_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved for Set-local analytics, gates, veto diagnostics and pre-classification score. |
| 5 | F-005 | Set direction classifier and LONG/SHORT handoff | CERTIFIED | `F-005/F-005_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved for Set-owned direction classification and handoff/no-handoff boundary. |
| 6 | F-008 | Planned entry reference selection | CERTIFIED | `F-008/F-008_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved for Position-owned Dynamic Limit Entry. |
| 7 | F-006 | Position Rules LONG formula | CERTIFIED | `F-006/F-006_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved for LONG Dynamic SL reference selection, stop construction and feasibility. |
| 8 | F-007 | Position Rules SHORT formula | CERTIFIED | `F-007/F-007_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved for SHORT Dynamic SL reference selection, stop construction and feasibility. |
| 9 | F-009 | Stop calculation and stop rounding | CERTIFIED | `F-009/F-009_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved for stop integration, fixed stop calculation/rounding and dynamic stop pass-through. |
| 10 | F-010 | Dynamic Take Profit selection and rounding | CERTIFIED | `F-010/F-010_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved for Dynamic TP target selection and inward rounding. |
| 11 | F-011 | Position size, quantity, and actual notional construction | CERTIFIED | `F-011/F-011_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved for post-grant final sizing, quantity, notional and committed-capital construction. |
| 12 | F-012 | Risk/reward and minimum net edge calculation | CERTIFIED | `F-012/F-012_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved for gross R:R and planned minimum net edge eligibility. |
| 13 | A-002 | Net final result calculation | CERTIFIED | `A-002/A-002_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved for final realized accounting composition. |
| 14 | A-004 | Funding calculation and allocation | CERTIFIED | `A-004/A-004_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; dependency-safe reorder before A-002 complete. |
| 15 | A-009 | Accounting-day realized totals and daily loss gate input | CERTIFIED | `A-009/A-009_FINAL_FORMULA_SPECIFICATION.md` | Verified `FULL_COUNCIL_APPROVED = YES` and `ANOTHER_REVIEW_CYCLE_REQUIRED = NO`; approved as accounting-day new-exposure gate input. |

## Separate REVIEW_NEEDED Objects

| ID | State | Notes |
|---|---|---|
| F-013 | NOT_STARTED | Separate object; excluded unless required by a primary formula. |
| S-004 | NOT_STARTED | Separate object; excluded unless required by accounting/order lifecycle dependencies. |
| S-005 | NOT_STARTED | Separate object; excluded unless required by a primary formula. |

## Current Focus

```text
current_formula: NONE
current_action: primary queue complete
mode: COMPLETE
reason: all primary queue formulas are certified; separate REVIEW_NEEDED objects remain excluded unless explicitly required.
```
