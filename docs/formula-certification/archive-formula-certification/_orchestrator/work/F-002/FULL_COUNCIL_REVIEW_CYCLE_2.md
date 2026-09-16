# FULL_COUNCIL_REVIEW_CYCLE_2

Formula: F-002 - Volume confirmation calculation
Mode: REVALIDATION
Date: 2026-09-15
Council model: FULL_COUNCIL

## Council Record

F-002 is approved for formula-specification certification after
product-decision revision.

```text
formula_id: F-002
review_mode: REVALIDATION
review_structure: ALL_EIGHT_PERSPECTIVES_APPLIED_IN_ONE_COUNCIL
specification_verdict: APPROVED
blocking_findings: NONE
full_council_approved: YES
another_review_cycle_required: NO
```

Evidence reviewed exclusively:

```text
docs/formula-certification/_orchestrator/work/F-002/F-002_REVISED_SPEC_CYCLE_1.md
```

All eight perspectives were applied in this single review. Referenced
dependencies and prior artifacts were not independently inspected by the
Council.

## Eight Role Verdicts

| Perspective | Verdict | Council assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVED | Suitable as relative participation confirmation for Set formation. It supplies neither trade direction nor an entry decision. |
| Market Microstructure & Order Flow Researcher | APPROVED | Base-volume measurement is coherent. Aggregated candle volume cannot establish aggressor direction, authentic activity, liquidity or execution capacity. |
| Market Regime & Context Analyst | APPROVED | The preceding 60 minutes provide an explicit local reference. Regime transitions, sparse trading and event activity remain empirical sensitivities. |
| Quant Strategy Researcher | APPROVED | Median, inclusive empirical rank, conjunction and division-free equivalent are mathematically correct within the stated valid domain. |
| Risk & Trade Management Architect | APPROVED | Invalid evidence remains `UNAVAILABLE`; stale satisfaction cannot carry forward. The formula grants no execution authority or exemption from risk checks. |
| Execution & Exchange Mechanics Specialist | APPROVED | Futures instrument and base-coin KLINES volume are explicitly bound. Turnover, contract-count, raw-trade-notional and spot substitutions are prohibited. |
| Adversarial Strategy Reviewer | APPROVED | Zero-median, incomplete, contradictory and mismatched evidence cannot produce a valid Boolean result. Ties and sparse histories remain interpretable limitations. |
| Performance & Strategy Diagnostics Analyst | APPROVED | Persisted identities and local intermediates support reproducibility and diagnosis. Profitability and threshold optimality remain unproven. |

## Finding Classification

| Classification | Finding and disposition |
|---|---|
| SPECIFICATION_DEFECT | None identified that blocks certification. |
| DEPENDENCY_GAP | No blocking gap in the stated formula contract. Numeric, KLINES and generic Trigger dependencies remain required contracts; their implementations were outside this review. |
| PRODUCT_DECISION | Prior blockers are resolved: Bybit USDT linear perpetual futures, base-coin volume, 1-minute candles and 60 historical bars, Set formation use, direction-neutral CURRENT_STATE, evaluation each completed minute, slot-bound freshness, ordinary 30-day/14-day baseline non-applicability, and explicit UNAVAILABLE handling. |
| EMPIRICAL_QUESTION | Confirmation frequency, threshold usefulness, sparse-volume sensitivity, regime effects, liquidation/event effects, interaction with F-001 and downstream outcomes require research. These do not invalidate the defined calculation. |
| NON_BLOCKING_LIMITATION | Inclusive rank is discrete and tie-sensitive; it is not statistical significance or proof of strictly exceeding 90% of observations. High relative volume does not establish liquidity, activity authenticity or profitable execution. |

The candidate does not retain spot-market scope. Missing, invalid and
zero-median evidence are not `FALSE`.

## Final Semantic Record

1. F-002 confirms unusually high recent relative participation for Set
   formation. It does not change active methodology.
2. Use exchange `KLINES.volume` in base-coin units for the same Bybit USDT
   linear perpetual futures instrument and factual source throughout.
3. `c` is the current completed 1-minute candle volume. History contains
   exactly the immediately preceding 60 completed consecutive 1-minute candles,
   excluding `c`.
4. Evaluate within active Set analysis scope and active formation epoch, with
   pinned configuration and complete source-final covered evidence.
5. Sort history ascending using one-based indices. Set:

```text
M = (v_sorted(30) + v_sorted(31)) / 2
K = count(v(i) <= c)
R = c / M
P = 100K / 60
```

6. Return `TRUE` exactly when:

```text
R >= 2 AND P >= 90
```

7. After establishing `M > 0`, the predicate is exactly:

```text
c >= v_sorted(30) + v_sorted(31) AND K >= 54
```

8. Missing, insufficient, nonconsecutive, unfinished, non-final, uncovered,
   mismatched, invalid or contradictory inputs yield `UNAVAILABLE`; zero median
   also yields `UNAVAILABLE`.
9. Evaluate once per completed minute. Satisfaction requires authoritative
   `TRUE` for the current completed slot with freshness still valid. At the
   next minute boundary, a new slot evaluation is required.
10. Preserve tri-state result, effective slot/evaluation time and trigger-local
    `M`, `K`, `R`, `P`. These intermediates are not exported Set metrics
    without a later certified formula or handoff contract.
11. Persist identities, source revisions, volume basis, numeric policy,
    intermediates and result. Identical duplicates are no-ops; conflicting
    accepted content invokes reconciliation.
12. Pin market/product, basis, timeframe, history count, thresholds, role,
    freshness and numeric policy for the formation epoch.
13. Ordinary 30-day/14-day normalization is explicitly `NOT_APPLICABLE`. F-001
    has no mathematical dependency here.

## Arithmetic Boundary Checks

```text
54 historical volumes of 1, six of 3, c = 2:
M = 1, R = 2, K = 54, P = 90 -> TRUE

53 historical volumes of 1, seven of 3, c = 2:
rank fails -> FALSE

all historical volumes and c equal 1:
P = 100, R = 1 -> FALSE

zero-median history:
UNAVAILABLE
```

This approval establishes a coherent, reproducible confirmation specification.
It does not establish trading profitability or authorize deployment.
