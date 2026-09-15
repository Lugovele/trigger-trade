# S-004 Source Pack

# S-004 - Order Lifecycle Finality and Closed-State Predicate

## 1. Identity

| Field | Value |
|---|---|
| Object ID | S-004 |
| Object name | Order Lifecycle finality and closed-state predicate |
| Owner | Order Lifecycle |
| Object family | STATE_CLASSIFICATION_RULE |
| Certification phase | Source Pack |
| Active methodology baseline | v1.2.14 |
| Source Pack status | Immutable pre-review provenance |

S-004 covers the predicate that classifies a logical tranche as canonical
`CLOSED` after close processing, financial finality and terminal outbox commit.

## 2. Source Index

| Source | Evidence |
|---|---|
| `docs/FORMULA_METRICS_CATALOG.md` | Catalog row marks S-004 REVIEW_NEEDED and BLOCK_FINAL_IMPLEMENTATION; final state predicate is coupled to final accounting result and lifecycle/accounting review. |
| `docs/trading-methodology/SYSTEM_PROTOCOLS.md` lines 87-106 | Unique active close intent, serialized close execution order and cleanup + financial finality + atomic canonical CLOSED. |
| `docs/trading-methodology/SYSTEM_PROTOCOLS.md` lines 114-127 | P6 defines CLOSED as one unified predicate of six required authoritative conditions; physical flatness alone is not CLOSED. |
| `docs/trading-methodology/SYSTEM_PROTOCOLS.md` lines 129-135 | Capital/slot commitment remains retained while closing, even at zero exposure, until canonical CLOSED releases it once. |
| `docs/trading-methodology/SYSTEM_PROTOCOLS.md` lines 137-157 | P7/P7.1 financial finality: complete mandatory evidence, attribution, currency admissibility and finality requirements inside P6. |
| `docs/trading-methodology/SYSTEM_PROTOCOLS.md` lines 191-218 | Result identity, no provisional correction stream, accounting-effective time/day and atomic terminalization. |
| `docs/trading-methodology/SYSTEM_PROTOCOLS.md` lines 331-335 | Closure proof binds durable revision vector; before FINAL/CLOSED one atomic transaction verifies current predicates; post-final contradictions quarantine. |
| `docs/trading-methodology/SYSTEM_PROTOCOLS.md` lines 373-379 | Current finality evidence and terminal quarantine; cached flags are not certificates; transaction recomputes proof and commits terminal timestamps. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 522-585 | Canonical lifecycle states and `CLOSED` meaning; all six P6 predicates must be established and commit atomically. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 1003-1015 | TP, SL and Manual Close all use common P6 CLOSED transaction with FINAL result; zero exposure without child/finance evidence remains nonterminal. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 1116-1159 | Reconciliation evidence precedence, restart recovery and P6 closure after restart. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 1268-1285 | Authoritative logical financial result; P7/P8 evidence; net formula; one result ID and atomic P6 CLOSED. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 1570-1602 | Invariants: no reprice/chase/fallback, factual execution authority, no arbitrary TTL, full logical commitment until CLOSED, FINAL requires complete mandatory financial evidence. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 1710-1729 | Close intent record, active uniqueness, serialized authority and zero residual not CLOSED until P6. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 1758-1780 | No strategic partial close; P6 retains commitment and slot; P12/P13 financial and closure proof requirements. |
| `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` lines 1796-1800 | Closure eligibility is revision-bound; recheck all six P6 predicates before FINAL/CLOSED and outbox commit. |
| `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` lines 16-40 | Financial row currency/finality transport; COMPLETE coverage requirements and unsupported-currency finality block. |
| `docs/formula-certification/A-002/A-002_FINAL_FORMULA_SPECIFICATION.md` | Certified final realized accounting composition dependency. |
| `docs/formula-certification/A-004/A-004_FINAL_FORMULA_SPECIFICATION.md` | Certified funding allocation dependency. |
| `docs/formula-certification/A-009/A-009_FINAL_FORMULA_SPECIFICATION.md` | Certified accounting-day realized totals and daily loss input dependency. |

## 3. Purpose and Trading Context

S-004 answers:

```text
Has this logical tranche reached the one canonical Order Lifecycle CLOSED state,
with all execution, authority, protection, close-intent and financial-finality
proofs complete, so its retained capital/slot can be released exactly once and
its final Order Event can be published?
```

Trading role:

- prevent capital/slot release from physical flatness alone;
- prevent duplicate or premature final P&L posting;
- ensure TP, SL, Manual Close and external reduction paths converge through the
  same closure predicate;
- preserve correct accounting-effective time and immutable accounting day;
- keep contradictory post-final evidence in integrity quarantine rather than
  silently rewriting final results.

S-004 does not calculate Entry, Stop, Take Profit, position size, gross/net P&L,
funding allocation or daily-loss totals. It depends on certified accounting
formulas and factual lifecycle evidence.

## 4. Exact Formula / Rule If Available

The core source predicate is P6:

```text
CLOSED requires all six authoritatively established predicates:

1. logical exposure = 0
2. entry remainder terminal
3. all tranche-owned protective/exit children terminal or authoritatively disabled
4. active close intent fully resolved
5. financial finality established
6. no unresolved competing execution authority
```

Candidate state rule extracted from sources:

```text
if all six P6 predicates are TRUE under the current durable proof vector:
    lifecycle_state = CLOSED
    commit FINAL result, resolved intent, CLOSED state and event outbox atomically
else:
    lifecycle_state remains CLOSE_PENDING or RECONCILING
    retained commitment and slot remain occupied
```

Physical flatness, cleanup completion, cached coverage, local complete flags,
manual-intervention escalation, elapsed time and terminal child callbacks are
not sufficient by themselves.

## 5. Inputs

| Input | Source | Required semantics |
|---|---|---|
| `tranche_id` | Order Lifecycle ledger | Logical tranche identity. |
| `close_intent_id` / intent state | Close intent record | At most one active close intent per tranche; resolved before CLOSED. |
| Execution ledger | Lifecycle / Order Management facts | Complete, deduplicated, attributed entry/exit executions in authoritative order. |
| Logical exposure quantity | Lifecycle reconstruction | Must be proven exactly zero after complete quantity attribution. |
| Entry remainder terminal proof | Lifecycle / exchange order state | Entry remainder cannot refill after closure. |
| Protective/exit child terminal/disabled proof | Lifecycle child authority | All tranche-owned child authority terminal or authoritatively disabled. |
| Financial evidence and allocations | Order Management / Lifecycle | Complete mandatory evidence, attribution, coverage, currency admissibility and final result. |
| Competing execution authority state | Lifecycle / native observations | No unresolved authority capable of changing exposure. |
| Accounting-effective timestamp | Lifecycle proof | Final economic closing execution time, not cleanup/finalization/delivery time. |
| Accounting day policy | Portfolio policy via Order Spec / Lifecycle | Immutable day from final economic closing execution. |
| Certified A-002 | Formula certification | Net final result composition. |
| Certified A-004 | Formula certification | Funding allocation. |
| A-005 / A-006 | Approved policy/formulas | Cumulative fills/VWAP and cashflow allocation/residue behavior. |

## 6. Outputs

Primary state:

```text
lifecycle_state = CLOSED | CLOSE_PENDING | RECONCILING
```

Terminal output on CLOSED:

```text
FINAL financial result
resolved close intent
CLOSED state
terminal timestamps
Order Event outbox
capital/slot release eligibility
```

No partial capital/slot release is produced by intermediate flat or partially
closed states.

## 7. Units

S-004 is a state predicate. Its input units inherit from dependencies:

- quantities: instrument quantity step / exact execution quantities;
- monetary evidence: pinned governed accounting/settlement currency and native
  source currencies retained as evidence;
- timestamps: timezone-aware authoritative event/effective times;
- accounting day: `Asia/Jerusalem` policy day under `ACCOUNTING_DAY_V1`.

## 8. Parameters

No user-tuned trading threshold controls S-004.

Relevant pinned policies include:

- P6 closed-state predicate;
- P7/P7.1 financial finality/currency admissibility;
- P8 accounting-effective time and day;
- P9/P12 execution and allocation proof;
- P13 closure eligibility proof;
- numeric/currency policy for accounting evidence.

## 9. Thresholds

All six P6 predicates are required conjunctively. There is no tolerance, timeout,
age threshold or percentage threshold that can substitute for any predicate.

## 10. Sign / Direction Semantics

S-004 does not determine LONG/SHORT direction. Direction matters only through
certified final-result and execution attribution dependencies. The close result
classification derives from factual close role and final economic closing
execution, not callback arrival order.

## 11. Domain / Preconditions

S-004 applies to a logical tranche that has entered close processing, including
TP, SL, Manual Close, external factual reduction reconciliation or another
Lifecycle-governed close path.

Zero-fill cancellation and definitive no-create submission failure are distinct
terminal paths and are not fictitious filled-tranche CLOSED events.

## 12. Boundaries

Order Lifecycle owns S-004 predicate evaluation and terminal outbox creation.

Portfolio consumes the FINAL logical result exactly once and performs capital
accounting/release. API/Order Management supplies factual evidence but does not
choose logical finality. Portfolio does not forward financial facts into
Lifecycle finality.

## 13. Precision

S-004 depends on exact factual quantities, exact source identities, exact
currency/quantum evidence and certified accounting formulas. Cached booleans,
display values and rounded summaries are not sufficient predicates.

## 14. Time Semantics

Important timestamps:

- `accounting_effective_at`: final economic closing execution time;
- `closed_at`: operational cleanup-complete marker, not by itself CLOSED;
- `finalized_at`: financial-evidence finalization time;
- `terminalized_at`: atomic canonical CLOSED transition;
- `delivered_at`: Portfolio first durable receipt/application time.

Accounting day is based on `accounting_effective_at`, not finalization,
delivery, cleanup or callback time.

## 15. State / Replay / Restart

On restart, Lifecycle must restore tranche/spec/authorization bindings, close
intent records, child authority, execution/cashflow inboxes, coverage cursors,
accounting timestamps/result IDs, native observations/resolutions and outbox
state before any new native side effect.

Crash before final commit publishes no final result; crash after final commit
republishes the same result. Identical replay is idempotent; conflicting
payloads are integrity incidents.

## 16. Version / Configuration Pinning

S-004 uses active baseline v1.2.14 and the pinned accounting/settlement policy
associated with the tranche's approved Order Spec/Portfolio policy. Later policy
or configuration edits do not reinterpret a historical final result.

## 17. Ownership

Owner: Order Lifecycle.

S-004 certification does not approve backend implementation, deployment,
TESTING/ACTIVE promotion, exchange interaction or live/paper order activity.

## 18. Downstream Consumers

| Consumer | Use |
|---|---|
| Portfolio Rules | Applies final result receipt once, posts to immutable accounting day, releases retained capital/slot after CLOSED. |
| Accounting / A-009 | Uses FINAL result/day for realized totals and daily loss gate input. |
| Order Event consumers | Receive final lifecycle state and integrity incidents. |
| System integration certification | Verifies finality boundary between execution, accounting and portfolio release. |

## 19. Dependencies

| Dependency | Classification | Notes |
|---|---|---|
| A-002 | CERTIFIED_FORMULA | Net final result calculation. |
| A-004 | CERTIFIED_FORMULA | Funding allocation. |
| A-009 | CERTIFIED_FORMULA | Accounting-day realized totals consumer. |
| A-005 | APPROVED_POLICY | Cumulative fill quantity, remaining quantity and VWAP are factual lifecycle accounting. |
| A-006 | APPROVED_POLICY | Execution-linked cashflow allocation and residue assignment. |
| NUMERIC_POLICY / N-007 | APPROVED_POLICY | Monetary arithmetic, currency/funding policies and serialization. |
| SYSTEM_PROTOCOLS P5-P13/P15 | DOCUMENTATION_DEPENDENCY | Authority, finality, evidence, closure and replay constraints. |
| Order Management factual evidence | DOCUMENTATION_DEPENDENCY | Execution/financial facts and coverage. |

## 20. Existing Worked Examples

Source example:

```text
accepted commitment 100; exposure 5
close starts -> closing-retained 100, slot 1
exposure later becomes 0 with unresolved SL -> still 100 and slot 1
financial history PARTIAL -> still 100 and slot 1
only all six predicates true -> commitment 0 and slot 0
```

Timestamp example:

```text
2026-09-11 23:59:59+03:00: final economic closing execution
2026-09-12 00:00:02+03:00: operational cleanup complete
2026-09-12 00:00:06+03:00: financial finalization and canonical CLOSED
2026-09-12 00:00:08+03:00: Portfolio receipt
accounting_day_id = 2026-09-11
```

## 21. Explicit Source Gaps

1. S-004 needs Council confirmation that the six P6 predicates plus P7/P8/P13
   evidence are sufficient as the canonical closed-state rule now that A-002 and
   A-004 are certified.
2. The Source Pack does not independently restate every possible native exchange
   reconciliation incident; it relies on SYSTEM_PROTOCOLS and Order Lifecycle
   evidence taxonomy.
3. Adapter/database conformance is explicitly runtime evidence, not formula
   certification evidence.
4. The exact `CLOSE_PENDING` versus `RECONCILING` subdivision is operational
   state-machine detail; the certification question is the boundary for
   canonical `CLOSED`.

## 22. Reviewer Handoff Summary

Council should certify whether S-004 can be approved as the Order Lifecycle
closed-state predicate:

- all six P6 predicates are required conjunctively;
- financial finality includes certified A-002/A-004 semantics and complete
  mandatory evidence;
- physical flatness, cleanup, cached flags, timers or manual escalation cannot
  substitute for CLOSED;
- full retained commitment and slot persist until canonical CLOSED;
- FINAL result, resolved intent, CLOSED state and outbox commit atomically;
- replay/restart is idempotent and contradictory post-final evidence enters
  integrity quarantine.

Council should identify whether remaining gaps are specification defects,
dependency gaps, runtime conformance requirements, empirical questions or
non-blocking limitations.
