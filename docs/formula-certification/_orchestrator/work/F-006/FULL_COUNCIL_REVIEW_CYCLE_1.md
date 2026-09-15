# F-006 FULL COUNCIL REVIEW CYCLE 1

formula_id: F-006
review_mode: FULL_REVIEW
FULL_COUNCIL_APPROVED: NO
ANOTHER_REVIEW_CYCLE_REQUIRED: YES

## Result

The LONG construction is conceptually fit for its declared structural stop
role, but two specification defects require revision. Calibration uncertainty
does not block certification.

## Eight Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Formula Specification Architect | CHANGES_REQUIRED | Successful output needs an explicit positive-stop invariant and fully specified selection ordering. |
| Mathematical Correctness Reviewer | CHANGES_REQUIRED | Buffer, minimum distance and outward rounding are correct; the accepted output domain currently includes nonpositive stops. |
| Numeric Precision and Determinism Reviewer | CHANGES_REQUIRED | Exact received decimals and rational comparisons are appropriate. "Lexical" ID ordering lacks an explicit comparator. |
| Trading Fitness / Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Structural invalidation plus ATR buffer is coherent. Hierarchies, recency preference and thresholds have unproven effectiveness. |
| Risk and Trade Management Reviewer | CHANGES_REQUIRED | Rejecting excessive distance without moving inward is appropriate. A nonpositive stop cannot qualify as usable protection. |
| Market Microstructure / Execution Reviewer | CHANGES_REQUIRED | LONG floor rounding is correct, but positivity is mandatory. Tick alignment alone establishes neither exchange acceptance nor execution. |
| Dependency and Architecture Boundary Reviewer | APPROVE_WITH_LIMITATIONS | Upstream consumption is compatible under strict handoff validation. F-009 integration remains outside this certification. |
| Replay / State / Auditability Reviewer | CHANGES_REQUIRED | Frozen inputs support reproducibility; selected identity needs a canonical tie-break. Restore original configuration and bindings on restart. |

## Blockers

### F006-C01 - SPECIFICATION_DEFECT

Nonpositive stops can pass the Source Pack checks. Post-rounding checks require
only `stop < R`, `stop < E` and acceptable ATR distance. With `E = 1`,
`A = 1`, `t = 0.1`, selecting `R = 0.25` produces stop `0`, while
`R = 0.15` produces stop `-0.1`. Both pass the listed checks. Upstream entry
constraints do not eliminate these cases.

Required closure:

```text
rounded_stop finite
rounded_stop > 0
rounded_stop exactly on tick grid
correct outward rounding
rounded_stop < R
rounded_stop < E
```

Invariant failure must return `usable = false`, reason `ROUNDING_ERROR`, with
diagnostic prices explicitly non-actionable. No clamp, reference retry or
inward correction.

### F006-C02 - SPECIFICATION_DEFECT

Final selection tie-break is underspecified. "Lexical level_id" does not define
case or collation, so equal-type, equal-time, equal-price candidates can yield
different selected IDs and audit records across implementations.

Required closure:

```text
1. latest exact available_at
2. smallest exact E - level.price
3. case-sensitive ordinal Unicode code-point level_id
```

Duplicate/conflicting canonical IDs must be rejected through handoff
validation.

## Additional Required Revision Instructions

1. State validation precedence explicitly: invalid producer bindings, dangling
   IDs, producer availability violations and `NONE` with non-null thesis
   ID/binding fail handoff consumption. `PREFERRED` fallback applies only to a
   contract-valid null pair or a valid bound reference failing F-006
   eligibility. Warning-only `NONE` cannot authorize an invalid handoff.
2. Apply the four LONG low types to both thesis and default selection.
3. Define `minimum_distance_adjustment_applied = (raw_stop > minimum_stop)`.
4. Preserve exact comparisons: `risk_price <= 2 * A` and
   `4 * abs(other - R) <= A`.
5. Include fixtures for nonpositive stops, strict one-tick exclusion, exact
   `2 ATR` acceptance, rounding-induced rejection, tied-ID selection and
   restart.

## Boundary Assessment

- F-003/F-005: Consume positive received Q18 ATR and committed LONG handoff for
  the same instrument and cycle. Never reconstruct ATR, infer direction or
  refresh frozen evidence.
- F-006/F-008: F-006 consumes the successful frozen entry. If entry and REQUIRED
  SL share reference `r`, LONG entry rounding gives `E <= r`, so that reference
  necessarily fails `r < E - t`; reject without rebinding.
- F-006/F-009: F-006 may certify its LONG candidate, selected reference,
  rounded candidate and feasibility result. F-009 integration remains separate
  and cannot change the F-006 result while retaining F-006 approval.

## Post-Rounding pct Gap

Classification: NON_BLOCKING_LIMITATION.

This diagnostic does not affect F-006 stop selection or feasibility. Its formula,
units and serialization remain uncertified. A future convention may define it as
`100 * (E - rounded_stop) / E` in percent units with pinned diagnostic rounding,
but that would be a new definition, not extracted source fact, and it must never
feed back into decisions.

## Empirical Validation Required

Classification: EMPIRICAL_QUESTION, non-blocking.

Evaluate pinned `0.20`, `0.50`, `2.00` and `0.25` defaults, family priorities
and recency across LONG opportunities, including rejections and nonfills.
Stratify by symbol, regime, reference age, thesis policy and tick/ATR ratio.
Measure adverse excursion, stop frequency and loss severity, execution costs
and downstream outcomes with chronological out-of-sample evidence. Candle
touches do not establish fills or exit ordering.

## Final Approval Record

null. Approval withheld pending F006-C01 and F006-C02 closure.
