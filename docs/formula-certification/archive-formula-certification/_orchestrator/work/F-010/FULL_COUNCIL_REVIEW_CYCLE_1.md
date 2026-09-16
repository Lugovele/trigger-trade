# F-010 FULL COUNCIL REVIEW CYCLE 1

formula_id: F-010
review_mode: FULL_REVIEW
FULL_COUNCIL_APPROVED: NO
ANOTHER_REVIEW_CYCLE_REQUIRED: YES

## Result

The core Dynamic TP selection mathematics and declared trading role are coherent.
Approval requires closing specification ambiguities affecting binding integrity
and deterministic outcomes. Unvalidated thresholds and hierarchy effectiveness
are not blockers.

## Eight Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Formula Specification Architect | CHANGES_REQUIRED | Candidate-pool definitions, thesis validation and failure precedence need explicit rules. |
| Mathematical Correctness Reviewer | APPROVE | Inclusive bands and inward rounding are correct. For valid selection, rounded distance equals raw distance minus `delta`, where `0 <= delta < tick_size`. |
| Numeric Precision and Determinism Reviewer | CHANGES_REQUIRED | Supplied N-004/TT_NUMERIC_V1-style quantizers suffice; lexical comparison remains unspecified. |
| Trading Fitness / Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Structural priority with bounded ATR distance is coherent. Thresholds, recency preference and terminal too-far rejection require empirical validation. |
| Risk and Trade Management Reviewer | CHANGES_REQUIRED | Corrupt bindings must reject before fallback. Selected-target rounding failure must remain terminal, including under PREFERRED. |
| Market Microstructure / Execution Reviewer | APPROVE_WITH_LIMITATIONS | LONG floor and SHORT ceiling move inward correctly. Tick alignment establishes neither liquidity nor execution probability. |
| Dependency and Architecture Boundary Reviewer | CHANGES_REQUIRED | Entry/stop ownership is correct, but thesis-binding validation needs the explicit integrity boundary established in F-008. |
| Replay / State / Auditability Reviewer | CHANGES_REQUIRED | Frozen inputs support replay; comparator semantics, configuration identity and diagnostic traversal semantics need pinning. |

## Blockers

### F010-C01 - SPECIFICATION_DEFECT

Preferred fallback must distinguish calculation ineligibility from corrupt
producer evidence. Dangling IDs, conflicting canonical IDs, invalid bindings and
`NONE` with non-null ID/binding must not become ordinary fallback cases.

### F010-C02 - SPECIFICATION_DEFECT

"Lexical level_id" does not define a portable total order. Different collations
can select different targets, including changing whether selection terminates
at `TOO_FAR`.

### F010-C03 - SPECIFICATION_DEFECT

The relationship between the eight approved level types, directional hierarchy
membership and thesis eligibility is incomplete. The basic eligible pool,
traversable pool, `NO_FAVORABLE_SIDE_GEOMETRY` predicate and missing-primitive
primary-reason ordering need deterministic definitions.

## Required Revision Instructions

1. Validate handoff integrity before thesis/default selection. Require unique
   canonical IDs and exact, consistent producer role, occurrence, type,
   timeframe, price and availability evidence. Reject dangling/conflicting IDs
   and invalid bindings under every policy. `NONE` requires both ID and binding
   null. `REQUIRED` missing-reference rejection has no fallback. `PREFERRED`
   fallback is allowed only for a contract-valid null pair or a valid bound
   reference failing calculation eligibility; preserve
   `INVALID_THESIS_REFERENCE_OVERRIDE`.
2. Order candidates by family/type priority, latest exact `available_at`,
   smallest exact favorable distance, then case-sensitive ordinal Unicode
   code-point `level_id`, with shorter prefixes first and no locale-dependent
   comparison or normalization. Array order and `age_seconds` cannot decide
   selection. `TOO_FAR` terminates traversal before any later candidate,
   including an older candidate of the same type. `PREFERRED` preselection
   fallback is a separate permitted branch.
3. Explicitly define permitted types for default and thesis candidates; do not
   silently infer an opposite-type conversion. Define capability predicate,
   basic pool and traversable pool, including empty-pool outcomes. Publish one
   reason-precedence table covering invalid handoff/configuration/dependencies,
   invalid REQUIRED thesis, missing primitives, geometry/pool failures and
   traversal outcomes. Preserve secondary diagnostics.
4. Consume an AVAILABLE certified F-008 result with matching instrument,
   direction, cycle, handoff and tick provenance; use the received Q18 ATR
   unchanged. Require finite positive tick-grid output and exact inward
   geometry. Once a target is selected, post-rounding failure is terminal under
   every policy; failed prices remain non-actionable. Persist immutable
   handoff/binding evidence, F-008 identity, configuration ID/version/digest,
   threshold/hierarchy/comparator identity, numeric-policy version and
   instrument metadata revision. Distinguish unvisited candidates from evaluated
   alternatives; optional diagnostic traversal must never affect the primary
   result.

## Dependency Evidence Needed

None beyond the supplied bundle. F-008 supplies binding/entry precedent and
F-009 supplies stop-boundary and exact-quantization precedent.

## Limitations To Preserve

- `0.75` and `4.00` ATR, hierarchy order and recency preference are research
  parameters, not validated optima or reach probabilities.
- Preserve strict one-tick exclusion, `TOO_CLOSE` continuation and terminal
  `TOO_FAR` behavior.
- Distance must not globally reorder structural priority.
- F-008 owns entry. F-009 stop distance, desired R:R and downstream failures
  cannot construct or repair TP.
- Final-price geometry and economic gates remain downstream.
- Frozen structure can become stale. Inward rounding does not establish fills,
  exchange acceptance or profitability.
- Implementation, persistence, execution, F-011 and F-012 remain uncertified.

## Empirical Validation Required

Use chronological out-of-sample opportunities, including rejected and unfilled
cases, segmented by instrument, direction, family, thesis policy, regime,
reference age and tick/ATR ratio. Assess threshold sensitivity,
hierarchy/recency preference, too-far rejection effects, target-before-stop
outcomes and realized results after costs. Candle touches cannot establish
fills or exit ordering.

Add conformance fixtures for exact boundaries, strict one-tick exclusion,
same-type ordering, binding failures, preferred fallback, terminal rounding
failures and restart equality.

## Final Approval Record

null.
