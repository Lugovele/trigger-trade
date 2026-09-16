# FINAL_FORMULA_SPECIFICATION

# A-002 - Net final result calculation

**Artifact:** `A-002_FINAL_FORMULA_SPECIFICATION.md`
**Specification status:** `FINAL_APPROVED`
**Review:** Full Expert Council Review - Cycle 1
**Review date:** 2026-09-15

## 1. Identity

| Field | Approved value |
|---|---|
| Formula ID | A-002 |
| Name | Net final result calculation |
| Owner | Accounting / Order Lifecycle final result |
| Formula family | PNL |
| Type | ACCOUNTING_FORMULA |
| Methodology baseline | v1.2.14 |
| Source Pack | `A-002_SOURCE_PACK.md` |
| Final approval cycle | 1 |

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = YES
SPECIFICATION_STATUS = FINAL_APPROVED
TRADING_FITNESS = APPROVED_AS_FINAL_REALIZED_ACCOUNTING
BLOCKING_FINDINGS_REMAINING = NONE
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
EMPIRICAL_EFFECTIVENESS = NOT_APPLICABLE_TO_ACCOUNTING_IDENTITY
LIVE_DEPLOYMENT_SAFETY = NOT_CERTIFIED_BY_THIS_REVIEW
```

Approval certifies A-002 for deterministic final realized accounting
composition at the logical-tranche boundary. It does not independently certify
the internal mechanics of A-001, A-003, A-005 or A-006; it accepts their
catalog-approved contracts as supplied evidence. It does not certify
implementation, venue conformance, A-009 daily totals, deployment, paper/live
execution, or any trading signal.

## 3. Intended Purpose

A-002 produces the authoritative final net realized result for a logical
tranche after all required executions, fees, funding, supported exchange costs,
attribution, currency admissibility, coverage and terminality requirements are
satisfied.

The result is realized accounting data. It is not:

- an entry signal;
- an exit trigger;
- a price forecast;
- an exposure estimator;
- a substitute for current open-risk state;
- permission to submit, cancel, resize or close orders.

## 4. Actual Construct

A-002 is an accounting composition identity over already-eligible component
outputs. It combines execution-derived gross trading result, attributed
cost-effect fee/rebate total, certified signed funding allocation, and
attributed cost-effect other supported exchange costs into one immutable final
net result for a logical tranche.

Gross is already directional. A-002 adds no long/short sign adjustment.

## 5. Exact Formula / Rule

```text
net_realized_result = gross_realized_trading_result
                    - actual_fees_rebates
                    + allocated_funding
                    - other_supported_exchange_costs
```

Equivalent wallet-effect expression:

```text
net_realized_result
= gross_realized_trading_result
 + sum(attributed TRADING_FEE signed_amount)
 + sum(attributed FUNDING allocated signed_amount)
 + sum(attributed OTHER_EXCHANGE_COST signed_amount)
```

This equivalence holds only after fee and other-cost cashflows have been
classified and attributed under their approved contracts. Native aggregate P&L
is neither a substitute nor an additional summand.

Council arithmetic checks:

```text
100 - 3 + (-2) - 1 = 94
-10 - (-0.5) + 0.2 - (-0.1) = -9.2
```

These checks are explanatory examples, not implementation tests or normative
source examples.

## 6. Inputs

| Input | Requirement |
|---|---|
| `gross_realized_trading_result` | Directional execution-derived gross result for the logical tranche; consumed from A-001 contract. |
| `actual_fees_rebates` | Attributed trading fee/rebate cost-effect total; charges positive, rebates negative. |
| `allocated_funding` | Sum of certified A-004 final signed tranche funding allocations applicable to the logical tranche. |
| `other_supported_exchange_costs` | Attributed supported non-funding exchange-cost cost-effect total; costs positive, refunds negative. |
| `currency` | Pinned governed accounting/settlement currency common to every required monetary component. |
| `source_lineage` | Execution IDs, cashflow IDs, source identities, aliases, coverage references and final closing execution. |
| `source_coverage` | COMPLETE overall financial coverage plus component coverage/non-applicability evidence. |
| Accounting timestamps | Proven permanent final closing execution time, accounting day, close/finalize/terminalize times and policy IDs. |

## 7. Outputs

| Output | Requirement |
|---|---|
| `net_realized_result` | Final net realized result for the logical tranche. |
| `financial_result` | FINAL payload carrying components, net result, currency, lineage, coverage and accounting timestamps. |
| `result_id` | Exactly one immutable final result identity per logical tranche. |
| Portfolio event | FINAL Order Event consumed once by Portfolio. |

## 8. Units

Every monetary component must already be denominated in the tranche's pinned
governed accounting/settlement currency before A-002 produces FINAL. A required
source in another currency remains native evidence and blocks FINAL.

No FX conversion, relabeling, cancellation between incompatible currencies, or
currency inference from incoming rows is authorized.

## 9. Parameters

A-002 has no trading threshold, research parameter, calibration parameter or
optimization parameter.

Fixed algorithmic policy:

- use exact arithmetic over eligible component outputs;
- preserve each component's own output and quantization rules;
- do not introduce A-002 intermediate rounding;
- persist one immutable final result identity per tranche.

## 10. Domain / Preconditions

Before A-002 can produce FINAL:

1. COMPLETE mandatory financial evidence and overall/component coverage exist.
2. Entry/exit executions and all mandatory source components are
   deterministically attributed.
3. Every required monetary source and component is already in the pinned
   governed accounting/settlement currency.
4. No unresolved cross-currency source remains.
5. No unresolved duplicate, alias, ordering, sign-convention or
   source-identity contradiction remains.
6. All P6 terminality/finality requirements are satisfied.
7. A-004 funding allocation is complete for funding rows or complete evidence
   proves no applicable funding rows.
8. Non-funding cashflow allocations are complete and source-conserving under
   the approved A-006/P12 contract.

## 11. Missing / Invalid Behavior

| Case | Required behavior |
|---|---|
| Missing mandatory coverage | No FINAL result; remain reconciling. |
| PARTIAL or UNAVAILABLE financial facts | No FINAL result. |
| Empty funding/cost rows without complete coverage or non-applicability | No zero assumption; remain reconciling. |
| Unknown source sign convention | No FINAL result. |
| Duplicate financial source representation | Resolve identity/aliases; do not double add. |
| Unsupported currency | Retain native evidence and block FINAL. |
| Planned fee estimate present but actual fee absent | Planned value cannot substitute. |
| Native aggregate P&L view present | Cannot substitute for logical execution lineage or be double-added. |
| Zero net result | Does not waive source, coverage, identity, currency or finality requirements. |
| Contrary post-FINAL evidence | Preserve frozen result and use post-final integrity/fence rules; do not rewrite or duplicate result. |

## 12. Boundaries

A-002 begins only after component values are eligible, attributed and
admissible. It does not define:

- gross P&L mechanics (A-001);
- fee attribution mechanics (A-003);
- funding allocation mechanics (A-004);
- VWAP/cumulative execution aggregation (A-005);
- non-funding cashflow allocation/residue mechanics (A-006);
- accounting-day aggregation or Daily Loss input (A-009);
- implementation persistence, exchange integration or runtime recovery.

The word "net" covers the declared supported component domain only. It does
not certify arbitrary wallet economics, unsupported exchange costs,
cross-currency effects or native aggregate P&L views.

## 13. Precision / Rounding

Monetary arithmetic follows exact decimal/rational `TT_NUMERIC_V1` rules.
Finite products and sums retain exact finite digits. No finite-precision
intermediate rounding, epsilon comparison or display rounding may feed the
final net result.

Each component's own output class and quantization must already be satisfied
before A-002 consumes it. A-002 does not round A-004 funding to the funding
quantum again, does not round source cashflows, and does not convert
currencies.

## 14. Time Semantics

`accounting_effective_at` is the proven permanent final closing execution time.
`accounting_day_id` follows the pinned Portfolio accounting policy. `closed_at`,
`finalized_at` and `terminalized_at` remain distinct lifecycle/finality times.

Late historical posting updates only the immutable historical day. It never
moves the result to today, never enters current Daily Loss/current daily base,
and never duplicates wallet P&L.

## 15. State / Replay / Restart

Persist exactly one result ID per logical tranche with:

- frozen component values and net result;
- currency and accounting policy version;
- source lineage and coverage;
- final closing execution ID;
- close/finalize/terminalize/accounting timestamps;
- component algorithm versions and evidence references.

No provisional A-002 result exists. Replay restores the same result ID and
values. Identical event/result replay has no monetary side effect. Portfolio
records receipt once in its receipt ledger.

Contrary post-FINAL evidence follows the approved integrity/fence protocol
without rewriting the frozen result or issuing another result for the same
logical tranche.

## 16. Configuration Pinning

The final result carries:

- result version;
- accounting algorithm version;
- pinned governed accounting/settlement currency;
- accounting policy version;
- source lineage and coverage identifiers;
- component algorithm versions, including A-004 funding allocation version:
  `FUNDING_ALLOC_V1_DECIMAL18_TOWARD_ZERO_LARGEST_ABS_LEXICAL`.

The governed currency cannot be selected from incoming rows or changed during
recovery.

## 17. Dependencies

| Dependency | Role | Certification treatment |
|---|---|---|
| A-001 Gross PnL calculation | Supplies directional execution-derived gross result. | Accepted as catalog-approved contract evidence. |
| A-003 Fee cashflow calculation and attribution | Supplies attributed fee/rebate cost-effect total. | Accepted as catalog-approved contract evidence. |
| A-004 Funding calculation and allocation | Supplies certified signed funding allocations. | `CERTIFIED_FORMULA`; final spec approved. |
| A-005 Cumulative fill quantity, remaining quantity and VWAP | Supports execution aggregation and lineage. | Accepted as catalog-approved contract evidence. |
| A-006 Execution-linked cashflow allocation and residue assignment | Supplies non-funding exchange-cost attribution and source conservation. | Accepted as catalog-approved contract evidence. |
| P7/P7.1 financial evidence and currency | Defines complete coverage, sign normalization and currency admissibility. | Approved policy/documentation dependency. |
| P6 finality/fence protocol | Defines terminality and post-final integrity behavior. | Approved policy/documentation dependency. |
| TT_NUMERIC_V1 | Governs exact monetary arithmetic. | Approved policy. |

## 18. Ownership

Order Lifecycle owns final logical financial result production. API supplies
factual executions, cashflows and coverage only. Portfolio consumes the final
result once and does not recompute it. Position does not supply or alter the
final financial result.

## 19. Pipeline Role

A-002 runs after final component evidence is complete and before Portfolio
posts the final Order Event to the immutable accounting day.

Pipeline relationship:

```text
API factual evidence -> Order Lifecycle attribution/finality -> A-002 final net result -> Portfolio receipt/accounting-day posting
```

## 20. Approved Uses

- Final realized accounting for a logical tranche.
- Portfolio receipt and immutable accounting-day posting.
- Audit, diagnostics and component breakdown of realized economics.
- Downstream A-009 input at the supplied interface, after A-009 is separately
  certified.

## 21. Prohibited Interpretations

A-002 must not be interpreted as:

- a trading signal;
- a forecast;
- a position sizing input before final close;
- a substitute for open exposure or unrealized P&L;
- a native aggregate wallet P&L formula;
- an FX conversion rule;
- permission to infer zero components without complete evidence;
- implementation, paper/live deployment or exchange-interaction approval.

## 22. Known Limitations

- Upstream A-001, A-003, A-005 and A-006 mechanics are accepted at their
  catalog-approved contract boundary, not independently recertified here.
- Venue/profile conformance for source identity, coverage, sign normalization,
  currency and ordering remains an operational verification obligation.
- Persistence atomicity and crash recovery require implementation
  verification.
- No complete normative numeric example exists in active methodology.
- A-009 is compatible at the supplied interface but is not certified by this
  document.

## 23. Research Parameters

None.

## 24. Empirical Validation Requirements

Profitability validation is not applicable to this accounting identity.
Operational diagnostics should track:

- reconciliation latency;
- unsupported-source and unsupported-currency frequency;
- missing or partial coverage frequency;
- duplicate/alias contradiction frequency;
- post-final contradiction/fence events;
- final result delivery and Portfolio receipt idempotency;
- diagnostic completeness of component breakdowns.

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

formula_id: A-002
formula_name: Net final result calculation

senior_intraday_crypto_trader: APPROVE
microstructure_order_flow_researcher: APPROVE
market_regime_context_analyst: APPROVE
quant_strategy_researcher: APPROVE
risk_trade_management_architect: APPROVE
execution_exchange_mechanics_specialist: APPROVE
adversarial_strategy_reviewer: APPROVE
performance_strategy_diagnostics_analyst: APPROVE

specification_status: FINAL_APPROVED
trading_fitness_status: APPROVED_AS_FINAL_REALIZED_ACCOUNTING

catalog_approved_upstream_evidence_sufficient: YES_FOR_DECLARED_CONTRACTS
certified_A004_compatibility: PASS
downstream_A009_compatibility: PASS_AT_SUPPLIED_INTERFACE
blocking_findings: NONE
known_limitations:
- upstream A-001/A-003/A-005/A-006 mechanics accepted at catalog-approved contract boundary
- venue/profile conformance remains required
- runtime persistence/restart behavior not certified
- A-009 not certified here
empirical_questions:
- reconciliation latency, unsupported-source frequency and diagnostics completeness remain to be measured

full_council_approved: YES
another_review_cycle_required: NO
```
