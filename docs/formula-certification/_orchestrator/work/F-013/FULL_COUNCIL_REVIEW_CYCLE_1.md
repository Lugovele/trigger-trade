# FULL_COUNCIL_REVIEW_CYCLE_1

# F-013 - Set Pending Invalidation and Stale-Signal Eligibility

## Council Record

```text
FULL_COUNCIL_APPROVED = NO
ANOTHER_REVIEW_CYCLE_REQUIRED = YES
REVISION_REQUIRED = YES
DEPENDENCY_EVIDENCE_REQUIRED = YES
PRODUCT_DECISION_REQUIRED = CONDITIONAL_ON_EMPTY_CONDITION_SUPPORT
```

Council conclusion:

F-013 is appropriately classified as a Set-owned, parameterized system
formula/state predicate. The supplied evidence supports ownership and purpose,
but does not yet establish a complete deterministic specification for every
relevant state and input combination.

A universal numeric predicate list and proof of profitability are not
prerequisites for certifying the generic predicate framework. Approval of
particular deployed condition sets requires additional configuration and
trading evidence.

## Eight Expert Verdicts

| Expert perspective | Verdict | Assessment |
|---|---|---|
| Trading Methodology and Product | SCOPE_SUPPORTED | Monitoring the original frozen thesis is coherent; loss of full Set match, newer opportunities and Coins CLOSE are correctly distinguished from hard invalidation. Empty-condition admissibility remains unspecified. |
| Formal Logic and State Machines | REVISION_REQUIRED | Define mutually exclusive outcomes, precedence, malformed-input handling and terminal-state behavior. |
| Quantitative Research and Trading Fitness | FITNESS_NOT_ESTABLISHED | Hard invalidation can reduce stale-entry exposure, but actual benefit depends on selected predicates and cancellation costs. Upstream certification does not validate those selections. |
| Market Data and Temporal Integrity | DEPENDENCY_EVIDENCE_REQUIRED | Freshness, coverage and eligibility are required conceptually; executable definitions and time semantics were not supplied in the first evidence bundle. |
| Numerical Consistency and Replay | DEPENDENCY_EVIDENCE_REQUIRED | Frozen configuration and original-cycle selection are sound requirements. Exact comparison semantics and immutable dependency binding need evidence. |
| Architecture and Ownership | BOUNDARY_SUPPORTED | Set evaluates validity and emits signals; Lifecycle reconciles and executes cancellation. Filled exposure remains outside F-013. |
| Execution, Risk and Security | REVISION_AND_EVIDENCE_REQUIRED | Remainder-only cancellation is sound. Race handling, uncertain identity, duplicate events and durable cancellation intent need explicit contracts. |
| Verification and Auditability | CERTIFICATION_EVIDENCE_REQUIRED | Invariants provide a useful basis, but reviewable expected outcomes for boundary cases and decision traces are missing. |

## Blocking Findings

### B1 - Outcome precedence is not explicit

The candidate rule permits a known TRUE predicate and another unavailable
required predicate simultaneously, satisfying both INVALID and UNAVAILABLE
clauses. Specify one reduction rule and its action.

### B2 - Frozen-condition validity needs a normative contract

Define admissible operators, typed metric/reference identifiers,
threshold/reference binding, timeframe/horizon, freshness, unavailable behavior
and version binding. Explicitly handle empty, missing, malformed and unsupported
condition sets; they must not accidentally produce VALID through an empty "all
false" evaluation. Per-condition unavailable policies must preserve the stated
fail-safe cancellation requirement.

### B3 - Cancellation and event progression need deterministic semantics

Specify what persists after invalidation or unavailable-data detection, how
reconciliation gates action, and how duplicate, delayed or reordered
Order Placed, fill and terminal events are handled. Market recovery must not
silently erase an already-required unavailable cancellation. Define signal
identity/idempotency and restart recovery. When order identity is uncertain,
Lifecycle must reconcile before targeting cancellation; F-013 must never infer
the nearest order or treat a cancel request as confirmation.

### B4 - Referenced dependency contracts are not supplied

Provide narrowly scoped evidence for N-008/TT_SET_NUMERIC_V1 comparisons;
SYSTEM_PROTOCOLS immutable configuration/selector binding and evidence
eligibility; and Lifecycle identity, remainder reconciliation and cancellation
handling. Clarify event/evaluation timestamps, live versus completed
observations, late data and comparison boundaries.

### B5 - Certification examples are missing

Supply expected-state/action cases covering mixed TRUE/unavailable predicates,
equality boundaries, expired evidence, empty or corrupt frozen inputs, duplicate
and reordered events, outage followed by recovery, partial/full fill during
cancellation, restart, later configuration changes and independent fresh
formations.

## Known Limitations

- The condition-to-trigger/score mapping is not supplied for any deployable
  F-013 configuration.
- Generic framework certification would not automatically approve concrete
  mappings, thresholds or trading fitness.
- Cancellation cannot guarantee prevention of fills before exchange
  acknowledgement.
- Event-driven semantics do not establish operational detection latency.
- F-013 provides neither a profitability guarantee nor authority to close filled
  exposure.

## Empirical Questions

1. Do selected hard predicates reduce adverse fills enough to offset missed
   profitable fills, fees and cancellation/re-entry costs?
2. How often do predicates invalidate and then recover, and how sensitive are
   cancellations to threshold boundaries, data freshness and observation timing?
3. What exposure accumulates between invalidation detection and cancellation
   acknowledgement, including partial fills and fast markets?
4. How frequently does unavailable-data cancellation occur, and what are its
   opportunity costs and operational failure rates?
