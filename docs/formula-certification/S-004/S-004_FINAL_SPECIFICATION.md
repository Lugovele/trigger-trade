# FINAL_SPECIFICATION

# S-004 - Order Lifecycle Finality and Closed-State Predicate

**Artifact:** `S-004_FINAL_SPECIFICATION.md`
**Specification status:** `FINAL_APPROVED`
**Review:** Full Expert Council Review - Cycle 1
**Review date:** 2026-09-15

## 1. Identity

| Field | Approved value |
|---|---|
| Object ID | S-004 |
| Object name | Order Lifecycle finality and closed-state predicate |
| Owner | Order Lifecycle |
| Object family | STATE_CLASSIFICATION_RULE |
| Reviewed candidate | `S-004_SOURCE_PACK` |
| Active methodology baseline | v1.2.14 |

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = YES
SPECIFICATION_STATUS = FINAL_APPROVED
TRADING_FITNESS = APPROVED_AS_CONSERVATIVE_LIFECYCLE_FINALITY_AND_RELEASE_ELIGIBILITY_RULE
BLOCKING_FINDINGS_REMAINING = NONE
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
IMPLEMENTATION_AND_LIVE_DEPLOYMENT = NOT_CERTIFIED
```

Approval covers the canonical `CLOSED` boundary and release-eligibility
predicate. It does not certify implementation, adapter behavior, database
atomicity, Portfolio receipt handling, deployment, TESTING/ACTIVE promotion or
live/paper execution.

## 3. Intended Purpose

S-004 determines whether a logical tranche has reached canonical Order Lifecycle
`CLOSED` state:

```text
Have all execution, authority, protection, close-intent and financial-finality
proofs completed so the retained capital/slot can be released exactly once and
the FINAL Order Event can be published?
```

## 4. Actual Construct

S-004 is a conservative closed-state predicate over current durable Lifecycle
and financial evidence. It requires all six P6 predicates to be authoritatively
TRUE under the current durable proof vector before `CLOSED` can be committed.

It rejects shortcut closure from physical flatness, cleanup completion, cached
coverage flags, terminal callbacks, manual escalation or elapsed time.

## 5. Exact Formula / Rule

```text
CLOSED =
  logical_exposure_is_zero
  AND entry_remainder_terminal
  AND all_tranche_owned_protective_or_exit_children_terminal_or_disabled
  AND active_close_intent_fully_resolved
  AND financial_finality_established
  AND no_unresolved_competing_execution_authority
```

State transition:

```text
if CLOSED is TRUE under the current durable proof vector:
    atomically commit:
      FINAL financial result
      resolved close intent
      lifecycle_state = CLOSED
      terminal timestamps
      Order Event outbox
else:
    lifecycle_state remains CLOSE_PENDING or RECONCILING
    retained commitment and slot remain occupied
```

Only six authoritatively TRUE predicate values permit `CLOSED`. FALSE, UNKNOWN,
missing or contradictory evidence prevents the transition.

## 6. Inputs

| Input | Semantics |
|---|---|
| `tranche_id` | Logical tranche identity. |
| `close_intent_id` / intent state | At most one active close intent per tranche; must be fully resolved. |
| Execution ledger | Complete, deduplicated, attributed entry/exit executions in authoritative order. |
| Logical exposure quantity | Proven exactly zero after complete quantity attribution. |
| Entry remainder terminal proof | Entry remainder cannot refill after closure. |
| Protective/exit child proof | All tranche-owned child authority terminal or authoritatively disabled. |
| Financial evidence and allocations | Complete mandatory evidence, attribution, coverage, currency admissibility and final result. |
| Competing execution authority | No unresolved authority capable of changing exposure. |
| `accounting_effective_at` | Final economic closing execution time. |
| Accounting day policy | Immutable day policy from approved Order Spec / Portfolio policy. |
| Certified A-002 | Net final result composition. |
| Certified A-004 | Funding allocation. |
| Approved A-005/A-006 | Cumulative fill/VWAP and cashflow allocation/residue rules. |

## 7. Outputs

```text
lifecycle_state = CLOSED | CLOSE_PENDING | RECONCILING
```

On `CLOSED`:

- FINAL financial result;
- resolved close intent;
- terminal timestamps;
- Order Event outbox;
- capital/slot release eligibility.

Intermediate flat or partially closed states do not produce partial release.

## 8. Units

S-004 is a state predicate. It consumes exact execution quantities, exact
monetary evidence in pinned governed accounting/settlement currency, retained
native source currencies where relevant, timezone-aware authoritative timestamps
and `ACCOUNTING_DAY_V1` day identity.

## 9. Parameters

No user-tuned trading threshold controls S-004.

## 10. Domain / Preconditions

S-004 applies to logical tranches that have entered close processing, including
TP, SL, Manual Close, external factual reduction reconciliation or another
Lifecycle-governed close path.

Zero-fill cancellation and definitive no-create submission failure are distinct
terminal paths and are not fictitious filled-tranche `CLOSED` events.

## 11. Missing / Invalid Behavior

If any required P6 predicate is FALSE, UNKNOWN, missing, contradicted or stale
under the current durable proof vector, the tranche is not `CLOSED`.

Missing mandatory financial evidence, incomplete coverage, unresolved currency
admissibility, nonzero residual quantity, unresolved child authority or
competing execution authority retain the tranche in `CLOSE_PENDING` or
`RECONCILING`.

No timeout or manual escalation substitutes for finality.

## 12. Boundaries

Order Lifecycle owns S-004 predicate evaluation and terminal outbox creation.
Portfolio consumes the FINAL logical result exactly once and performs capital
accounting/release. API/Order Management supplies factual evidence but does not
choose logical finality.

## 13. Precision / Rounding

S-004 depends on exact factual quantities, exact source identities, exact
currency/quantum evidence and certified accounting formulas. Cached booleans,
display values and rounded summaries are insufficient.

## 14. Time Semantics

- `accounting_effective_at`: final economic closing execution time.
- `closed_at`: operational cleanup-complete marker, not by itself CLOSED.
- `finalized_at`: financial-evidence finalization time.
- `terminalized_at`: atomic canonical CLOSED transition.
- `delivered_at`: Portfolio first durable receipt/application time.

Accounting day is based on `accounting_effective_at`, not finalization,
delivery, cleanup or callback time.

## 15. State / Replay / Restart

On restart, Lifecycle restores tranche/spec/authorization bindings, close intent
records, child authority, execution/cashflow inboxes, coverage cursors,
accounting timestamps/result IDs, native observations/resolutions and outbox
state before any new native side effect.

Crash before final commit publishes no final result. Crash after final commit
republishes the same result. Identical replay is idempotent. Conflicting replay
or contradictory post-final evidence enters integrity quarantine.

## 16. Configuration Pinning

S-004 uses active baseline v1.2.14 and the pinned accounting/settlement policy
associated with the tranche's approved Order Spec / Portfolio policy. Later
policy or configuration edits do not reinterpret a historical final result.

## 17. Dependencies

| Dependency | Classification | Use |
|---|---|---|
| A-002 | CERTIFIED_FORMULA | Net final result calculation. |
| A-004 | CERTIFIED_FORMULA | Funding allocation. |
| A-009 | CERTIFIED_FORMULA | Accounting-day realized totals consumer. |
| A-005 | APPROVED_POLICY | Cumulative fill quantity, remaining quantity and VWAP. |
| A-006 | APPROVED_POLICY | Execution-linked cashflow allocation and residue assignment. |
| NUMERIC_POLICY / N-007 | APPROVED_POLICY | Monetary arithmetic, currency/funding policies and serialization. |
| SYSTEM_PROTOCOLS P5-P13/P15 | DOCUMENTATION_DEPENDENCY | Authority, finality, evidence, closure and replay constraints. |
| Order Management factual evidence | DOCUMENTATION_DEPENDENCY | Execution/financial facts and coverage. |

## 18. Ownership

Owner: Order Lifecycle.

## 19. Pipeline Role

```text
Close intent / factual reduction
→ reconcile entry remainder, child authority and executions
→ establish complete financial evidence and final result
→ verify all six P6 predicates atomically
→ commit FINAL result, resolved intent, CLOSED state and outbox
→ Portfolio may apply final receipt and release retained capital/slot once
```

## 20. Approved Uses

S-004 may be used as the certified canonical Order Lifecycle closed-state and
release-eligibility predicate.

## 21. Prohibited Interpretations

S-004 is not:

- proof from physical flatness alone;
- permission for timeout release;
- permission for manual escalation release;
- permission to use cached coverage or cleanup flags as finality;
- a formula for P&L, funding or daily-loss totals;
- implementation, adapter, database or deployment certification.

## 22. Known Limitations

- Adapter coverage, proof freshness at commit, database atomicity and Portfolio
  deduplication require implementation conformance evidence.
- Missing mandatory evidence or nonzero residual quantity can retain commitment
  and slot indefinitely.
- Integrity quarantine preserves historical FINAL result; later incident
  resolution is outside this object.
- `CLOSE_PENDING` versus `RECONCILING` subdivision and zero-fill terminal paths
  are outside this canonical CLOSED-boundary certification.

## 23. Research Parameters

None.

## 24. Empirical / Conformance Validation Requirements

Implementation validation must prove:

- reordered fills, delayed fees/funding, incomplete coverage and entry/cancel
  races prevent premature `CLOSED`;
- crashes around final commit and Portfolio application preserve one result
  identity, one accounting application and one capital/slot release;
- contradictory post-final facts enter quarantine without silently changing the
  result or accounting day;
- retention delays and missing-proof causes are observable.

## 25. Eight Final Expert Verdicts

| Expert perspective | Final verdict |
|---|---|
| Senior Intraday Crypto Trader | APPROVE |
| Market Microstructure & Order Flow Researcher | APPROVE |
| Market Regime & Context Analyst | APPROVE |
| Quant Strategy Researcher | APPROVE |
| Risk & Trade Management Architect | APPROVE |
| Execution & Exchange Mechanics Specialist | APPROVE |
| Adversarial Strategy Reviewer | APPROVE |
| Performance & Strategy Diagnostics Analyst | APPROVE |

## 26. Final Council Record

```text
FULL_COUNCIL_APPROVED = YES
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
SPECIFICATION_STATUS = APPROVED
TRADING_FITNESS_STATUS = APPROVED_AS_CONSERVATIVE_LIFECYCLE_FINALITY_AND_RELEASE_ELIGIBILITY_RULE
BLOCKING_FINDINGS = NONE
```
