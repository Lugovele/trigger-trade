# TriggerTrade Formula System Integration Pack

**Artifact:** `FORMULA_SYSTEM_INTEGRATION_PACK.md`
**Status:** `SYSTEM_INTEGRATION_REVIEW_PACK`
**Prepared:** 2026-09-15
**Active methodology baseline:** v1.2.14

## 1. Purpose

This pack summarizes the certified formula/state-rule system for final
cross-object coherence review. It does not change active methodology, approve
implementation, promote anything to TESTING or ACTIVE, deploy, or authorize
paper/live trading.

The review question is:

```text
Do the certified formula and state-rule specifications cohere as a complete
TriggerTrade certification layer under the approved architecture and dependency
boundaries?
```

## 2. Canonical Architecture Boundary

Preserved ownership:

1. Portfolio Rules - Capital Management
2. Set - Market Analysis
3. Position Rules - Trade Decision
4. Order Lifecycle - Order Management
5. API - factual/technical interface
6. Research - isolated diagnostics/backtest/research only

Canonical flows:

```text
Portfolio Rules -> Set:
Coins

Portfolio Rules -> Position Rules:
Capital and Limits

Set -> Position Rules:
Market Handoff

Position Rules -> Portfolio Rules:
Approve / Reject

Position Rules -> Order Lifecycle:
Order Spec / approved execution intent

Order Lifecycle <-> API
```

## 3. Certified Objects

| ID | Certified role | Final artifact | Council status |
|---|---|---|---|
| F-003 | Set ATR and true-range calculation | `F-003/F-003_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| F-001 | Price-move trigger calculation | `F-001/F-001_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| F-002 | Volume confirmation calculation | `F-002/F-002_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| F-004 | Set normalization, percentile and score calculation | `F-004/F-004_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| F-005 | Set direction classifier and LONG/SHORT handoff | `F-005/F-005_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| F-008 | Planned entry reference selection | `F-008/F-008_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| F-006 | Position Rules LONG formula | `F-006/F-006_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| F-007 | Position Rules SHORT formula | `F-007/F-007_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| F-009 | Stop calculation and stop rounding | `F-009/F-009_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| F-010 | Dynamic Take Profit selection and rounding | `F-010/F-010_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| F-011 | Position size, quantity and actual notional construction | `F-011/F-011_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| F-012 | Risk/reward and minimum net edge calculation | `F-012/F-012_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| A-004 | Funding calculation and allocation | `A-004/A-004_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| A-002 | Net final result calculation | `A-002/A-002_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| A-009 | Accounting-day realized totals and daily loss gate input | `A-009/A-009_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| F-013 | Set pending invalidation and stale-signal eligibility | `F-013/F-013_FINAL_FORMULA_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| S-004 | Order Lifecycle finality and closed-state predicate | `S-004/S-004_FINAL_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |
| S-005 | Market regime classifier research/demo diagnostic boundary | `S-005/S-005_FINAL_SPECIFICATION.md` | `FULL_COUNCIL_APPROVED = YES` |

Each final artifact also records:

```text
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
```

## 4. Dependency Order and System Chain

### Set chain

```text
F-001 price displacement
F-002 relative volume confirmation
F-003 ATR / true range
        ↓
F-004 normalization / percentiles / score
        ↓
F-005 Set direction classifier and Market Handoff
        ↓
F-013 pending-entry invalidation framework after Order Placed
```

Set certification preserves these boundaries:

- F-001 is signed 1m endpoint displacement, not ATR-normalized.
- F-002 is short-horizon futures relative participation confirmation.
- F-003 is volatility context, separate from F-001 arithmetic.
- F-004 consumes certified trigger/volatility evidence and remains Set-local.
- F-005 owns LONG/SHORT/NONE direction and handoff/no-handoff boundary.
- F-013 governs only already placed pending LIMIT entry market-validity
  monitoring and never closes filled exposure.

### Position chain

```text
F-005 Market Handoff / direction
        ↓
F-008 planned entry reference
        ↓
F-006 LONG stop-side construction
F-007 SHORT stop-side construction
        ↓
F-009 stop calculation / rounding
F-010 dynamic take-profit selection / rounding
        ↓
F-011 final quantity / notional / committed capital
        ↓
F-012 gross R:R / planned minimum net edge
```

Position certification preserves these boundaries:

- Position consumes, but does not reinterpret, Set direction.
- Position selects and constructs trade terms after Market Handoff.
- Portfolio grants and exchange facts constrain sizing but do not move into
  Set-owned market analysis.
- Planned edge/R:R is an eligibility calculation, not profitability proof.

### Accounting and lifecycle chain

```text
A-004 funding allocation
        ↓
A-002 net final result
        ↓
A-009 accounting-day realized totals / daily loss input

A-002/A-004/A-005/A-006 evidence
        ↓
S-004 canonical CLOSED predicate
```

Accounting/lifecycle certification preserves these boundaries:

- Lifecycle owns final execution/finality proof and final Order Event.
- Portfolio consumes final results once and owns capital accounting/release.
- Accounting day is bound to final economic closing execution time.
- Physical flatness is not canonical `CLOSED`.

### Research boundary

```text
S-005 = research/demo diagnostic only
```

S-005 is not a certified trading input and must not affect Set matching,
Position decisions, Portfolio approvals, Order Lifecycle behavior or execution.

## 5. Dependency Classes

Certified formula dependencies:

- F-001 through F-005 feed Set analytics and handoff.
- F-008, F-006, F-007, F-009, F-010, F-011 and F-012 form the Position
  construction and eligibility chain.
- A-004 feeds A-002; A-002 feeds A-009 and S-004 finality context.

Approved policy/configuration dependencies:

- `TT_SET_NUMERIC_V1` governs Set-derived arithmetic where applicable.
- `TT_NUMERIC_V1` and related numeric policies govern monetary, quantity and
  capital arithmetic.
- F-014/F-015 and A-005/A-006 remain approved as defined / implementable policy
  dependencies where referenced by certified specs.
- Research/configuration parameters remain configurable and are not frozen as
  optimal values.

Documentation dependencies:

- Active methodology v1.2.14;
- `docs/trading-methodology/`;
- business contracts and schemas referenced by final specs;
- `SYSTEM_PROTOCOLS.md` evidence, replay, finality, configuration and selector
  binding rules.

## 6. Cross-Object Coherence Checks

### Ownership

No certified final spec transfers ownership across architecture boundaries:

- Set owns market analysis, direction and F-013 pending market validity.
- Position owns trade construction and Position eligibility.
- Portfolio owns capital, grants, holds, approvals and release accounting.
- Order Lifecycle owns submission/cancel/close/finality mechanics.
- API owns factual transport/normalization only.
- Research owns S-005 diagnostic context only.

### Direction

F-005 remains final direction owner. F-001 and F-002 do not determine LONG/SHORT.
Position does not re-infer or reverse Set direction. S-005 cannot override or
influence F-005.

### Time and evidence

Certified specs require closed-candle/factual evidence, immutable selectors,
replay/restart determinism and no look-ahead. S-004 distinguishes economic,
cleanup, finalization, terminalization and delivery timestamps.

### State and finality

F-013 governs active unfilled pending entry remainder only. S-004 governs
canonical final close of a logical tranche. These do not conflict:

- F-013 never closes filled exposure.
- S-004 never treats pending-entry market invalidation as filled-tranche
  closure.
- Portfolio release waits for S-004 canonical finality, not F-013 cancellation.

### Trading fitness boundaries

Council approvals certify specification correctness and conceptual fitness for
declared roles. They do not prove profitability, parameter optimality, runtime
implementation correctness, exchange adapter conformance or live readiness.

## 7. Known System Limitations

- Implementation, database atomicity, adapter conformance, runtime performance,
  TESTING/ACTIVE promotion and live/paper execution are not certified here.
- Research parameters remain unvalidated unless explicitly marked otherwise.
- Concrete F-013 hard-condition sets may need further review before deployment.
- S-005 is research/demo diagnostic only and has no live decision authority.
- Formula certification does not rewrite active methodology; integration into
  active methodology is a separate controlled task.

## 8. Final Council Review Request

The Council should review whether the certified object set is coherent as a
system certification layer:

1. no formula contradicts another certified formula;
2. dependencies are satisfied or correctly bounded;
3. ownership and canonical architecture remain intact;
4. research/configuration limitations are preserved;
5. REVIEW_NEEDED objects F-013, S-004 and S-005 are correctly integrated;
6. no formula approval is being misread as implementation, deployment, live
   execution or profitability approval.

If approved, Council should return:

```text
FORMULA_SYSTEM_FULL_COUNCIL_APPROVED = YES
ANOTHER_SYSTEM_REVIEW_REQUIRED = NO
```
