# FINAL_FORMULA_SPECIFICATION

# A-004 — Funding calculation and allocation

**Artifact:** `A-004_FINAL_FORMULA_SPECIFICATION.md`
**Specification status:** `FINAL_APPROVED`
**Review:** Full Expert Council Review — Cycle 1
**Review date:** 2026-09-15

## 1. Identity

| Field | Approved value |
|---|---|
| Formula ID | A-004 |
| Name | Funding calculation and allocation |
| Owner | Accounting / Order Lifecycle attribution |
| Formula family | FUNDING |
| Type | ACCOUNTING_FORMULA |
| Methodology baseline | v1.2.14 |
| Source Pack | `A-004_SOURCE_PACK.md` |
| Final approval cycle | 1 |

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = YES
SPECIFICATION_STATUS = FINAL_APPROVED
TRADING_FITNESS = APPROVED_AS_REALIZED_ACCOUNTING_ATTRIBUTION
BLOCKING_FINDINGS_REMAINING = NONE
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
EMPIRICAL_EFFECTIVENESS = NOT_APPLICABLE_TO_ACCOUNTING_ALLOCATION
LIVE_DEPLOYMENT_SAFETY = NOT_CERTIFIED_BY_THIS_REVIEW
```

Approval certifies the funding-allocation formula specification for the narrow
realized-accounting role. It does not certify implementation, venue conformance,
A-002 net final result, A-009 daily totals, deployment, live execution, or any
trading signal.

## 3. Intended Purpose

A-004 deterministically attributes factual exchange funding cashflows to
TriggerTrade logical tranches for realized accounting.

Funding is accounting data only. It is not:

- an entry signal;
- an exit trigger;
- a direction signal;
- a funding-rate forecast;
- a planned Minimum Net Edge input;
- a reason to close or resize a position.

## 4. Actual Construct

The formula allocates each unique signed source funding transaction across the
eligible logical tranches sharing the funded native symbol/side at the funding
effective time. Allocation weights are proportional to each tranche's
event-time open notional using one common settlement/mark price basis.

Because the common price cancels within a single homogeneous symbol/native-side
funding event, the practical weight is the tranche's attributable open quantity
divided by total eligible attributable open quantity, while retaining the
settlement/mark price and provenance as required funding basis evidence.

## 5. Exact Formula / Rule

For each unique source funding transaction:

```text
tranche_open_notional_at_funding_time
= attributable_open_quantity * common_funding_settlement_or_mark_price

total_triggertrade_open_notional_for_symbol_side_at_funding_time
= sum(tranche_open_notional_at_funding_time for all eligible tranches)

raw_tranche_funding
= signed_source_funding_amount
 * (tranche_open_notional_at_funding_time
    / total_triggertrade_open_notional_for_symbol_side_at_funding_time)
```

Let:

```text
q = 0.000000000000000001
F = signed_source_funding_amount
w_i = tranche_open_notional_i / total_open_notional
```

Base allocation:

```text
base_i = sign(F) * q * floor((abs(F) * w_i) / q)
```

Residue:

```text
residue = F - sum(base_i)
```

Assign the entire signed residue to the eligible tranche with the largest
absolute unrounded raw allocation. If tied, choose the lowest `tranche_id` by
lexical Unicode code-point order.

Final allocation:

```text
allocated_funding_i = base_i + residue   for the residue recipient
allocated_funding_i = base_i             for every other eligible tranche
```

Conservation requirement:

```text
sum(allocated_funding_i) = signed_source_funding_amount
```

Persist:

```text
funding_allocation_algorithm_version =
FUNDING_ALLOC_V1_DECIMAL18_TOWARD_ZERO_LARGEST_ABS_LEXICAL
```

## 6. Inputs

| Input | Requirement |
|---|---|
| Source funding transaction | Stable unique `cashflow_id` and source transaction/provenance. |
| Signed funding amount | Normalized wallet-effect amount, positive for receipt and negative for payment. |
| Currency | Must already equal the tranche's pinned governed accounting/settlement currency for FINAL. |
| Amount quantum | Factual source quantum retained as provenance. |
| Funding effective time | Event time used for eligibility and open-quantity state. |
| Native scope | Managed account/environment, symbol, native side and position identity as applicable. |
| Settlement/mark basis | Common funding settlement/mark price, basis, as-of and source ref for the event. |
| Eligible tranche set | Tranches with attributable open quantity on the funded native symbol/side at the funding event. |
| Attributable open quantity | Quantity proven by Lifecycle attribution at the event time. |
| Coverage/finality evidence | COMPLETE funding component and parent financial evidence under the existing financial evidence rules. |

## 7. Outputs

| Output | Requirement |
|---|---|
| Per-tranche funding allocation | Signed decimal-18 settlement-currency amount. |
| Allocation manifest | Source funding identity, eligible set, weights/basis, raw/base/residue allocation, recipient and algorithm version. |
| Allocated total | Exactly equals the source funding amount after residue assignment. |
| Downstream component | `allocated_funding` for later net-result calculation. |

## 8. Units

Allocations are in the source funding transaction's governed settlement/accounting
currency. The allocation quantum is:

```text
0.000000000000000001
```

No cross-currency valuation is authorized. Settlement/mark price is an
allocation weight basis only, not an FX conversion rate.

## 9. Parameters

A-004 has no research threshold or configurable trading parameter.

Fixed algorithm constants:

- allocation quantum: `10^-18`;
- base allocation rounding: truncate absolute magnitude toward zero, then
  reapply source sign;
- residue recipient: largest absolute unrounded allocation;
- tie-breaker: lowest `tranche_id` lexical order;
- algorithm version:
  `FUNDING_ALLOC_V1_DECIMAL18_TOWARD_ZERO_LARGEST_ABS_LEXICAL`.

## 10. Domain / Preconditions

A funding transaction is allocatable only when:

- source identity, alias resolution and duplicate detection are complete;
- source coverage/finality is COMPLETE, or non-applicability is evidenced for
  empty funding;
- the source amount is exactly representable at the decimal-18 funding quantum;
- the source currency matches the tranche's pinned governed accounting currency;
- every eligible tranche and its attributable open quantity at the event time
  are deterministically known;
- the common settlement/mark basis and provenance are available;
- total eligible open notional is positive;
- same-timestamp execution/funding ordering is authoritative or not material.

If these do not hold, funding attribution remains `RECONCILING` /
finality-blocked rather than guessed, rounded, converted or omitted.

## 11. Missing / Invalid Behavior

| Case | Required behavior |
|---|---|
| Missing funding rows | Zero only with COMPLETE coverage or evidenced non-applicability. Otherwise unresolved. |
| Duplicate funding representation | Resolve aliases to one source event; do not count twice. |
| Same source identity with changed content | Treat as contradiction. |
| Unsupported currency | Retain native fact and block FINAL; do not convert, zero or relabel. |
| Source amount not representable at `10^-18` | Reconcile; do not round source amount. |
| Unmatched nonzero funding event | Cannot produce certified allocation; reconcile. |
| Missing settlement basis for multi-tranche event | Reconcile. |
| Unresolved same-timestamp ordering | Reconcile. |

## 12. Boundaries

One eligible tranche receives the entire signed funding amount. Multiple
eligible tranches receive pro-rata allocations with deterministic decimal-18
truncation and residue assignment.

Zero source amount allocates zero to every established eligible tranche, but
does not by itself prove funding coverage complete.

Residue assignment is not a largest-fractional-remainder method. It uses the
largest absolute unrounded allocation, tie-broken lexically by `tranche_id`.

## 13. Precision / Rounding

All raw weight calculations are exact rational arithmetic. Base allocations are
computed by truncating the absolute allocation magnitude toward zero to
`10^-18` settlement-currency units and then restoring the source sign.

The final residue assignment must conserve the exact signed source funding
amount. Presentation rounding must not replace persisted allocation values.

## 14. Time Semantics

Eligibility and weights are evaluated at the funding effective time, not at
recorded time, retrieval time, current position state or accounting-day close.

Coverage intervals remain half-open `[from, to)`. The cutoff must include the
funding event and all causally applicable records. Equal timestamp ambiguity
without authoritative native sequencing remains unresolved.

## 15. State / Replay / Restart

Persist the complete funding allocation manifest:

- source funding identity and aliases;
- accepted coverage/certificate identity;
- funding effective time;
- eligible tranche set;
- attributable quantities;
- settlement/mark basis and provenance;
- raw/base/residue allocation values;
- residue recipient;
- final signed allocations;
- algorithm version.

On replay or restart, restore accepted source and coverage history before
processing new evidence. Duplicate delivery of identical evidence is idempotent.
Known identity with changed content remains a contradiction.

## 16. Configuration Pinning

The funding allocation algorithm version is fixed for this specification:

```text
FUNDING_ALLOC_V1_DECIMAL18_TOWARD_ZERO_LARGEST_ABS_LEXICAL
```

The tranche's governed accounting/settlement currency is pinned before final
accounting use and cannot be changed to fit incoming rows.

## 17. Dependencies

| Dependency | Role |
|---|---|
| N-007 | Approved factual window/accounting-day policy; A-004 uses factual event windows, while A-009 later aggregates by accounting day. |
| P7 / P7.1 financial evidence | Complete source coverage, sign normalization and currency admissibility. |
| Order Management `GET_FINANCIAL_FACTS` | Source of funding cashflows, settlement basis and coverage. |
| TT_NUMERIC_V1 | Confirms funding uses its separate decimal-18 algorithm and is not replaced by non-funding allocation rules. |
| A-002 | Downstream consumer of `allocated_funding`; not certified by this document. |

## 18. Ownership

Order Lifecycle owns funding attribution and final logical financial results.
API supplies factual rows only. Portfolio does not forward funding facts to
Lifecycle and does not derive a competing logical result. Position excludes
funding from planned Minimum Net Edge and does not use funding as an exit
trigger.

## 19. Pipeline Role

A-004 runs after funding cashflows are observed and before complete logical net
final result construction. It supplies the `allocated_funding` component for
later final accounting.

## 20. Approved Uses

- Deterministic attribution of factual funding transactions to logical tranches.
- Realized accounting and reconciliation.
- Diagnostics and audit of realized funding burden.
- Downstream A-002 net final result input, after A-002 is separately certified.

## 21. Prohibited Interpretations

A-004 must not be interpreted as:

- a funding-rate forecast;
- a trading signal;
- an entry or exit condition;
- a planned edge estimate;
- permission to close, resize or cancel;
- exchange funding-rate calculation certification;
- cross-currency conversion authority;
- implementation or live-deployment approval.

## 22. Known Limitations

- Venue/profile conformance for source identity, currency, settlement basis,
  sequencing, complete coverage and managed-account scope remains a runtime
  obligation.
- Persistence atomicity and restart behavior require implementation
  verification.
- A-002, A-009 and complete accounting finality are not certified by this
  formula.
- Repeated residue ties can systematically favor the same lexical tranche ID;
  this is an accepted deterministic accounting policy.

## 23. Research Parameters

None.

## 24. Empirical Validation Requirements

Profitability validation is not required for this accounting allocation.
Operational diagnostics should track:

- funding burden by symbol/side/regime;
- residue concentration;
- delayed or incomplete funding evidence frequency;
- reconciliation duration;
- unsupported-currency or source-identity incidents;
- duplicate/alias contradiction frequency.

These diagnostics do not change the certified formula.

## 25. Eight Final Expert Verdicts

| Required perspective | Verdict |
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
FINAL_COUNCIL_RECORD

formula_id: A-004
formula_name: Funding calculation and allocation

senior_intraday_crypto_trader: APPROVE
microstructure_order_flow_researcher: APPROVE
market_regime_context_analyst: APPROVE
quant_strategy_researcher: APPROVE
risk_trade_management_architect: APPROVE
execution_exchange_mechanics_specialist: APPROVE
adversarial_strategy_reviewer: APPROVE
performance_strategy_diagnostics_analyst: APPROVE

specification_status: FINAL_APPROVED
trading_fitness_status: APPROVED_AS_REALIZED_ACCOUNTING_ATTRIBUTION

blocking_findings: NONE
known_limitations:
- venue/profile conformance remains required
- runtime persistence/restart behavior not certified
- downstream A-002/A-009 not certified here
- repeated lexical residue ties can favor the same tranche ID
empirical_questions:
- operational funding burden and reconciliation diagnostics remain to be measured

full_council_approved: YES
another_review_cycle_required: NO
```
