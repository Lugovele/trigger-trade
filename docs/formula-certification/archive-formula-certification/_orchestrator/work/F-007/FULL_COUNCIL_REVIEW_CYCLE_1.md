# F-007 FULL COUNCIL REVIEW CYCLE 1

formula_id: F-007
review_mode: FULL_REVIEW
FULL_COUNCIL_APPROVED: NO
ANOTHER_REVIEW_CYCLE_REQUIRED: YES

## Result

The SHORT construction is mathematically coherent and trading-fit in concept,
but three specification defects require revision. Calibration uncertainty is
not a certification blocker.

## Eight Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Formula Specification Architect | CHANGES_REQUIRED | Close terminal numeric validation, total ordering and handoff-validation ambiguities. |
| Mathematical Correctness Reviewer | APPROVE | SHORT signs, maximum adjustment, ceiling rounding and inclusive feasibility bounds are correct. |
| Numeric Precision and Determinism Reviewer | CHANGES_REQUIRED | Specify the canonical ID comparator, exact comparisons and numeric failure contract. |
| Trading Fitness / Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Coherent structural SHORT stop; reference quality and calibration remain unvalidated. |
| Risk and Trade Management Reviewer | CHANGES_REQUIRED | Invalid producer evidence must never reach warning-only fallback. Preserve terminal rejection without stop repair. |
| Market Microstructure / Execution Reviewer | CHANGES_REQUIRED | Explicitly require valid finite tick-grid output. Exchange acceptance and realized protection remain outside scope. |
| Dependency and Architecture Boundary Reviewer | CHANGES_REQUIRED | Align thesis validation with F-005/F-008/F-006 and record the resolved entry/integration boundaries. |
| Replay / State / Auditability Reviewer | CHANGES_REQUIRED | Canonical tie-breaking and persisted original bindings/configuration must determine replay. |

## Blockers

### F007-C01 - SPECIFICATION_DEFECT

The post-rounding contract specifies only `rounded_stop > R` and
`rounded_stop > E`; finite/grid validity and terminal arithmetic-failure
handling need explicit closure. Positivity already follows from valid positive
SHORT inputs and correct arithmetic, but the output validity contract must still
require it.

Required closure:

```text
E, A, t and selected R finite and positive
Sstop = ceil(adjusted_stop / t) * t
Sstop finite
Sstop > 0
Sstop / t integer
Sstop is exact outward rounding
Sstop > R
Sstop > E
```

Arithmetic failure or failed output invariants must return terminal
`usable = false`, `reason = ROUNDING_ERROR`; diagnostics remain
non-actionable. No clamp, offset, inward correction, reference retry or entry
repricing.

### F007-C02 - SPECIFICATION_DEFECT

"Lexical level_id" leaves collation implementation-dependent. Equal-time and
equal-price candidates can select different IDs and produce different audit
records.

Required closure:

```text
1. latest exact available_at
2. smallest exact level.price - E
3. ascending case-sensitive ordinal Unicode code-point level_id
```

Duplicate/conflicting canonical IDs must be rejected. Locale collation, case
folding, natural/numeric sorting and array order are not allowed.

### F007-C03 - SPECIFICATION_DEFECT

The thesis policy permits insufficiently qualified invalid/unavailable
`PREFERRED` fallback and warning-only `NONE` with a non-null ID. This conflicts
with certified producer-binding validation.

Required closure:

```text
validate handoff identity, provenance, unique IDs, availability and exact
sl_context.origin_binding before selection
```

Dangling/conflicting bindings and `NONE` with either ID or binding non-null
terminate consumption. `PREFERRED` fallback is allowed only for a
contract-valid null pair or a valid bound reference failing F-007 eligibility.
`REQUIRED` eligibility failure yields `THESIS_REFERENCE_INVALID` without
fallback.

## Additional Required Revision Instructions

1. Both thesis and default candidates permit only `SWING_HIGH_15M`,
   `SWING_HIGH_1H`, `PREVIOUS_DAY_HIGH`, `RANGE_HIGH`, with
   `available_at <= matched_at` and strict `price > E + t`.
2. Define `minimum_distance_adjustment_applied = (raw_stop < minimum_stop)`.
3. Gate using exact `Dpre <= 2A`, `Dpost <= 2A`, and corroboration
   `4 * abs(other.price - R) <= A`; rounded quotients must not drive decisions.
4. F-007 consumes the frozen F-008 entry for the same handoff/cycle/result. If
   entry and REQUIRED SL share reference `r`, SHORT entry gives `E >= r`,
   making `r > E + t` impossible; return `THESIS_REFERENCE_INVALID` without
   rebinding.
5. F-009 may separately validate or reject integration but cannot alter F-007's
   selected reference, rounded candidate or formula-feasibility result while
   retaining F-007 certification.
6. Persist handoff identity/digest, exact received Q18 ATR, frozen entry/tick,
   original thesis binding, configuration identity/version/digest,
   methodology/numeric-policy pins, constants, selection keys, exclusions,
   calculations, warnings and result.
7. Add fixtures for strict one-tick equality, minimum-adjustment equality,
   exact cap acceptance, rounding-induced rejection, tied IDs/permuted arrays,
   corrupt bindings versus valid `PREFERRED` fallback, shared entry/SL
   reference, terminal numeric failures and identical restart.

## Dependency Evidence Needed

None blocking. Certified F-003, F-005, F-008 and F-006 provide sufficient
authority for revision. No product decision or downstream certification is
required.

## Limitations To Preserve

- `dynamic_sl.risk_distance.post_rounding.pct` remains diagnostic and
  uncertified. It must not be inferred or used for selection, feasibility,
  sizing or risk/reward.
- The `2 ATR` cap bounds planned price distance, not realized loss, exposure or
  liquidation risk.
- Stop triggers, liquidity, slippage, gaps, partial fills and outages remain
  outside F-007.
- Tick alignment alone does not satisfy every venue price constraint.
- F-003's unresolved corrected-history acceptance/release boundary remains
  non-blocking; frozen evidence cannot be rewritten or automatically repaired.
- Constants `0.20`, `0.50`, `2.00`, `0.25`, family priorities and recency
  preference remain unvalidated research defaults.

## Empirical Validation Required

Evaluate all SHORT opportunities, including rejections and nonfills, across
symbols, regimes, reference ages, thesis policies and tick/ATR ratios. Use
chronological out-of-sample evidence to measure adverse excursion, stop
frequency/severity, squeeze/gap outcomes, execution costs, funding where
applicable and downstream net results. Candle touches cannot establish fills or
exit ordering. Calibration research is not a certification blocker.

## Final Approval Record

Not issued.
