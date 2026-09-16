# FULL_COUNCIL_REVIEW_CYCLE_2

Formula: F-001 - Price-move trigger calculation
Mode: REVALIDATION
Date: 2026-09-15
Council model: FULL_COUNCIL

## Council Record

F-001 was not approved as a complete specification. The revised product choices
and arithmetic are coherent, but two blocking contract gaps remain.

```text
formula_id: F-001
review_mode: REVALIDATION
review_execution: all eight perspectives applied in this single review
full_council_approved: NO
another_review_cycle_required: YES
blocking_findings: F001-RV01, F001-RV02
```

Evidence reviewed:

- `docs/formula-certification/_orchestrator/work/F-001/F-001_REVISED_SPEC_CYCLE_1.md`
- `docs/formula-certification/F-003/F-003_FINAL_FORMULA_SPECIFICATION.md`

No additional dependencies were inspected. No edits, tests, subagents or
trading actions were performed by the Council.

## Blocking Findings

### F001-RV01 - DEPENDENCY_GAP

Operative freshness contract is missing. Sections 14-16 correctly require
current-slot membership, replacement at the next minute boundary, and
restoration without resetting time. However, satisfaction additionally requires
that "freshness requirements still hold," and a separate freshness policy is
material configuration. Neither its operative rule nor an identifiable
versioned contract is supplied.

Required closure: state whether freshness consists solely of current-slot
membership or includes additional conditions; specify those conditions and
their evaluation-time binding, and identify the persisted policy/evidence
needed to reproduce the decision after restart. This does not require inventing
a new timeout.

### F001-RV02 - SPECIFICATION_DEFECT

`UNAVAILABLE` does not have a complete associated-output contract. The output
table requires a signed working value and `UP`/`DOWN`/`FLAT`; sign is defined
exclusively from that value. With a missing candle or zero reference, no
eligible quotient exists. The specification does not state that these
associated outputs are unavailable, nor distinguish this case from valid prices
with an invalid threshold, where arithmetic could be calculable but Trigger
evaluation is disallowed.

Required closure: specify working-value and sign availability for these failure
branches, including whether eligible arithmetic evidence may survive a
threshold/configuration failure. Absent evidence must not become fabricated
zero, `FLAT`, or a previous value.

## Product-Decision Revalidation

| Area | Council disposition |
|---|---|
| Observed basis, reference, endpoints and horizon | Resolved: trade-price-derived closes from the current and immediately preceding completed one-minute candles, with matching source/venue/product/instrument. Missing intervals cannot be bypassed using an older available close. |
| Predicate | Resolved: inclusive `abs(move_pct_work) >= theta_move_pct`, with a mandatory positive pinned threshold in percent units. |
| Cadence and Trigger role | Resolved: once per completed one-minute candle; direction-neutral `CURRENT_STATE`. Additional freshness semantics remain blocked by RV01. |
| Direction ownership | Resolved: F-001 preserves movement sign; Set owns final direction. |
| F-003 relationship | Resolved: separate downstream volatility context, with no ATR operand, inherited 15m horizon, or imported ATR smoothing/export quantizer. |
| Legacy/demo inheritance | Excluded: no negative-threshold dip-buy rule, `BUY_CANDIDATE` mapping, or demo-only condition appears in the candidate. |

## Eight Expert Verdicts

| Expert perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | CHANGES_REQUIRED | Completed one-minute displacement fits the declared detection role. It establishes neither continuation nor reversal opportunity; usable signal timing remains incomplete under RV01. |
| Market Microstructure & Order Flow Researcher | APPROVE_WITH_LIMITATIONS | Trade-close displacement is a coherent measurement. Source finality does not establish spread, depth, activity, executable price, or whether the close represents substantial trading. |
| Market Regime & Context Analyst | APPROVE_WITH_LIMITATIONS | The magnitude predicate remains interpretable across regimes. Equal percentage displacement does not imply equal opportunity or risk; separate F-003 context does not itself classify the regime. |
| Quant Strategy Researcher | CHANGES_REQUIRED | Signed return, percent units, one Q36 quantizer, and inclusive absolute comparison are correct. RV02 prevents a complete output definition across the stated input domain. |
| Risk & Trade Management Architect | CHANGES_REQUIRED | Detection and direction ownership are appropriately separated. RV01 and RV02 leave freshness and availability of consumable evidence insufficiently specified; TRUE establishes no position eligibility or risk permission. |
| Execution & Exchange Mechanics Specialist | CHANGES_REQUIRED | Analytical prices and precision are correctly separated from execution. Restored current-state eligibility requires RV01 closure; observed displacement does not establish an executable order price. |
| Adversarial Strategy Reviewer | CHANGES_REQUIRED | Missing-data, source-conflict, duplicate, and frozen-handoff protections are directionally sound. Same-slot restored results and undefined numeric/sign outputs expose RV01 and RV02 respectively. |
| Performance & Strategy Diagnostics Analyst | APPROVE_WITH_LIMITATIONS | The construct supports controlled evaluation. Threshold sensitivity, directional asymmetry, regimes, latency, costs, and downstream contribution remain unvalidated. |

## Arithmetic and Boundary Record

The accepted core is:

```text
Q36(100 * (observed - reference) / reference)
```

followed by the exact inclusive absolute comparison. Q36 means 36 fractional
decimal places, retaining integer digits, with `ROUND_HALF_EVEN` and no
intermediate, threshold, display or execution rounding.

For eligible inputs:

- `100 -> 101` gives `+1%` and `UP`;
- `100 -> 99` gives `-1%` and `DOWN`;
- both pass threshold `1`;
- unchanged close gives zero, `FLAT`, and `FALSE` for every valid positive
  threshold.

Quantization precedes both sign and comparison. With `u = 10^-36`, an exact
displacement of `u/2` rounds to zero and therefore yields `FLAT`. An exact
displacement of `1 - u/2` rounds to `1` and passes threshold `1`.

A valid zero observed close gives `-100%`: it passes thresholds at or below
`100`, and fails larger thresholds. If that zero becomes the next reference,
that next evaluation is `UNAVAILABLE`; the reference cannot be replaced.

## Remaining Classifications

- `DEPENDENCY_GAP`, non-blocking: corrected-history acceptance and
  reconciliation release remain external governance. F-003 explicitly leaves
  these unresolved; its certification supplies no automatic recovery authority
  for F-001.
- `NON_BLOCKING_LIMITATION`: endpoint displacement omits intrabar path and
  microstructure. Sign describes the rounded movement, not trade direction.
  Percentage moves are not equivalent risk across instruments.
- `EMPIRICAL_QUESTION`: threshold calibration, one-minute timing suitability,
  F-002 interaction, downstream sign use and net trading benefit remain
  unestablished.

Disposition: retain the revised product decisions and arithmetic. Resolve RV01
and RV02, then repeat Council review.
