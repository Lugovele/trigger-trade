# F-007 FULL COUNCIL REVIEW CYCLE 2

formula_id: F-007
review_mode: REVALIDATION
FULL_COUNCIL_APPROVED: YES
ANOTHER_REVIEW_CYCLE_REQUIRED: NO
specification_status: FINAL_APPROVED
trading_fitness: ADEQUATE_FOR_DECLARED_SHORT_DYNAMIC_SL_ROLE_WITH_LIMITATIONS

## Result

The Council reviewed `F-007_REVISED_SPEC_CYCLE_1.md`. Blockers F007-C01,
F007-C02 and F007-C03 are closed. No regression was identified in the supplied
specification evidence.

## Eight Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Formula Specification Architect | APPROVE | Eligibility, validation precedence, selection, calculation and terminal outcomes form a coherent specification. |
| Mathematical Correctness Reviewer | APPROVE | `max(R + 0.20A, E + 0.50A)` and outward ceiling preserve SHORT geometry; both inclusive `2A` checks are correct. |
| Numeric Precision and Determinism Reviewer | APPROVE | Exact received decimals, explicit grid invariants and Unicode code-point ordering close numeric and selection ambiguity. |
| Trading Fitness / Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Structural invalidation with an ATR buffer is suitable for the declared SHORT stop role. Hierarchies and calibration remain unvalidated. |
| Risk and Trade Management Reviewer | APPROVE_WITH_LIMITATIONS | Infeasible stops reject without inward movement or weaker-reference retry. Planned distance does not bound realized loss. |
| Market Microstructure / Execution Reviewer | APPROVE_WITH_LIMITATIONS | Outward tick construction is sound. Venue acceptance, trigger mechanics, liquidity and realized fills remain separate. |
| Dependency and Architecture Boundary Reviewer | APPROVE_WITH_LIMITATIONS | Preserves F-003 received Q18 ATR, F-005 committed direction, F-008 frozen entry and F-006 sibling boundaries. F-009 cannot alter the approved candidate under this certification. |
| Replay / State / Auditability Reviewer | APPROVE_WITH_LIMITATIONS | Frozen identity/digest, binding, configuration, exact sort keys and selection evidence support reproducibility. Persistence implementation is unverified. |

## Blocker Closure Assessment

| Blocker | Classification | Disposition |
|---|---|---|
| F007-C01 | SPECIFICATION_DEFECT | CLOSED. Valid finite positive operands, finite positive grid-aligned output, exact outward ceiling, `Sstop > R` and `Sstop > E` are required. Arithmetic/invariant failures terminate with `ROUNDING_ERROR`. |
| F007-C02 | SPECIFICATION_DEFECT | CLOSED. Duplicate/conflicting IDs are rejected and candidate ordering uses latest exact availability, smallest exact `price - E`, then ascending case-sensitive Unicode code points. |
| F007-C03 | SPECIFICATION_DEFECT | CLOSED. Identity, provenance/digest, bindings, availability and canonical IDs are validated before selection. Invalid producer evidence terminates consumption; `REQUIRED` never falls back. |

## Limitations To Preserve

- Frozen structure and lagging ATR can become stale; SHORT squeeze/gap behavior
  and execution costs are not modeled.
- The `2 ATR` cap bounds planned price distance only.
- Tick alignment does not establish venue acceptance, stop fills, liquidation
  protection or complete Position approval.
- Shared required entry/SL references reject; coarse ticks can eliminate
  availability.
- `post_rounding.pct` remains diagnostic and prohibited from decision use.
- F-003 corrected-history acceptance/reconciliation release remains externally
  unresolved and non-blocking for F-007.
- Constants, family priorities, recency preference and realized strategy benefit
  remain unvalidated.

## Empirical Validation Required

YES. Preserve chronological out-of-sample evaluation of all SHORT
opportunities, including rejections and nonfills, across symbols, families,
regimes, reference ages, thesis policies and tick/ATR ratios. Measure adverse
excursion, stop frequency/severity, squeeze/gap outcomes, costs, applicable
funding and downstream net results. Candle touches establish neither fills nor
exit ordering.

## Final Approval Record

```yaml
approved_by: FULL_COUNCIL
review_date: 2026-09-15
reviewed_candidate: F-007_REVISED_SPEC_CYCLE_1.md
reviewed_candidate_sha256: 52c9e29a48d3e4f3f9eeeb9b03f0dfd10bf1b37acb86735cc3d12e5544331785
blocker_disposition: {F007-C01: CLOSED, F007-C02: CLOSED, F007-C03: CLOSED}
approved_scope: SHORT Dynamic SL reference selection, stop construction and feasibility
pinned_identity: TT-METH-016 v0.2.1; baseline v1.2.14; Market Handoff v4; TT_SET_NUMERIC_V1
pinned_constants: {buffer: 0.20, minimum_distance: 0.50, maximum_distance: 2.00, corroboration: 0.25}
new_council_semantic_definitions: NONE
excluded_certifications: [F-009, F-010, F-011, F-012]
implementation_promotion_execution_deployment_git_authority: NOT_GRANTED
```
