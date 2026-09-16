# F-009 FULL COUNCIL REVIEW CYCLE 1

formula_id: F-009
review_mode: FULL_REVIEW
FULL_COUNCIL_APPROVED: NO
ANOTHER_REVIEW_CYCLE_REQUIRED: YES

## Result

F-009 can certify stop integration without recertifying F-006/F-007. Two
specification defects require revision. Missing parameter calibration or a
default percentage is not a blocker.

## Eight Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Formula Specification Architect | CHANGES_REQUIRED | Integration scope is coherent; fixed-mode validity and terminal rejection need explicit definitions. |
| Mathematical Correctness Reviewer | APPROVE_WITH_LIMITATIONS | LONG `E * (1 - S / 100)` with floor and SHORT `E * (1 + S / 100)` with ceiling are correct within a valid domain. |
| Numeric Precision and Determinism Reviewer | CHANGES_REQUIRED | Exact quantizers are sufficient; mandatory output invariants and failure handling are incomplete. |
| Trading Fitness / Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Configured percentage stops and certified structural stops are suitable protective-price constructs; effectiveness remains unproven. |
| Risk and Trade Management Reviewer | CHANGES_REQUIRED | Downstream geometry alone cannot exclude a zero or negative LONG stop. |
| Market Microstructure / Execution Reviewer | APPROVE_WITH_LIMITATIONS | Outward rounding preserves the intended price boundary. Tick alignment does not establish venue acceptance or execution quality. |
| Dependency and Architecture Boundary Reviewer | APPROVE_WITH_LIMITATIONS | Preserve certified entry and dynamic outputs unchanged; downstream certifications remain separate. |
| Replay / State / Auditability Reviewer | APPROVE_WITH_LIMITATIONS | Supplied configuration, identity and metadata pins support deterministic replay; implementation is unverified. |

## Blockers

### F009-C01 - SPECIFICATION_DEFECT

`fixed_sl_pct` must be "valid," but its admissible domain and invalid-value
outcomes are undefined. Missing-value handling alone does not settle zero,
negative, malformed or nonfinite values, or LONG percentages producing
nonpositive prices.

Required closure:

```text
S is an exact finite percentage
1 means 1%
S > 0
LONG requires S < 100
no universal SHORT upper bound inferred from LONG mathematics
missing, malformed, nonfinite or out-of-domain FIXED configuration -> CONFIG_INVALID
no implicit default
DYNAMIC does not consume fixed_pct
```

### F009-C02 - SPECIFICATION_DEFECT

Fixed mode lacks an explicit positive, finite, tick-aligned output contract and
terminal failure mapping. Example: LONG `E=1`, `S=1`, `t=1` gives
`raw_sl=0.99`, rounded `SL=0`, yet a later geometry gate can still pass.

Required closure:

```text
E and t finite positive
SL finite
SL > 0
SL / t integer
LONG SL < E
SHORT SL > E
SL equals prescribed exact floor/ceil quantization
arithmetic or post-rounding invariant failure -> ROUNDING_ERROR
no actionable stop exposed on failure
```

## Additional Required Revision Instructions

1. Consume dynamic mode only from the matching F-006/F-007 branch when
   `usable = true` and `reason = AVAILABLE`, bound to the same instrument,
   direction, frozen handoff/cycle, F-008 entry, configuration and tick
   provenance.
2. Preserve original dynamic branch result and reason on integration rejection;
   never reround, clamp, substitute, retry or change branch feasibility.
3. Preserve F-009 specification identity, dependency identities, frozen handoff
   digest, mode, exact inputs, fixed raw/rounded outputs or linked dynamic
   result, and validation outcomes.
4. Restart must reproduce the result without refreshing configuration, entry or
   tick metadata.
5. Add conformance fixtures for exact-grid and off-grid rounding, invalid
   percentages, rounded zero, dependency failure/mismatch, unchanged dynamic
   pass-through and restart equality.

## Dependency Evidence Needed

None. The supplied N-004 and `TT_NUMERIC_V1` extracts sufficiently establish
positive instrument tick facts, provenance and exact quantization.

## Limitations To Preserve

- `fixed_sl_pct` is a required FIXED configuration parameter; calibration and
  any default remain empirical questions.
- Dynamic constants retain their existing certification limitations.
- Use exact arithmetic without binary floats, epsilon comparisons or
  intermediate rounding.
- Outward fixed rounding adds distance `delta`, where `0 <= delta < t`; the
  resulting distance can exceed the configured percentage.
- After final Entry/SL/TP resolution, downstream consumers must recompute and
  validate geometry, gross R:R and Minimum Net Edge using final prices.
- No repair is permitted. F-010, F-011 and F-012 are not certified by this
  review.
- Dynamic `post_rounding.pct` remains uncertified, non-decision diagnostics.
- Preserve Order Spec v5 fields: decimal-string price, `MARKET`, `LAST_PRICE`,
  `PARTIAL_QUANTITY`, and applicable/nullable `fixed_pct`.
- A planned stop does not guarantee maximum realized loss, liquidation
  protection, coverage of every fill, exchange acceptance or execution.

## Empirical Validation Required

Evaluate fixed percentages and inherited dynamic parameters chronologically out
of sample across symbols, sides, regimes and tick-to-stop-distance ratios,
including rejected and unfilled opportunities. Measure adverse excursion, stop
frequency, realized loss, costs, slippage, gaps and partial-fill outcomes.
Candle touches cannot establish fills or exit ordering.

## Final Approval Record

null.
