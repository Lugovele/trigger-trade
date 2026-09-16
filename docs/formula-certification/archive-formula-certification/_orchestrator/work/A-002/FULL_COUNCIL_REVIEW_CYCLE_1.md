# FULL_COUNCIL_REVIEW_CYCLE_1

Formula: A-002 - Net final result calculation
Mode: FULL_REVIEW
Date: 2026-09-15
Council model: FULL_COUNCIL

## FULL_COUNCIL_RECORD

Decision: APPROVE the specification for its declared role: deterministic final
realized accounting for a logical tranche, consuming eligible upstream
components. This approval accepts the supplied dependency contracts; it does
not independently recertify their internal mechanics.

Evidence reviewed exclusively:

- `docs/formula-certification/A-002/A-002_SOURCE_PACK.md`
- `docs/formula-certification/A-004/A-004_FINAL_FORMULA_SPECIFICATION.md`

Referenced files were not inspected by the Council.

## Specification Assessment

```text
net_realized_result = gross_realized_trading_result
                    - actual_fees_rebates
                    + allocated_funding
                    - other_supported_exchange_costs
```

1. Formula and signs: PASS. Gross is already directional; A-002 adds no
   long/short sign adjustment. Fees and other costs use cost-effect totals:
   charges are positive, rebates/refunds negative. Funding retains
   wallet-effect signs: receipts positive, payments negative. Equivalently,
   net equals gross plus attributed signed fee, funding and other-cost
   cashflows.
2. Upstream sufficiency: YES, for composition certification. The source pack
   identifies A-001, A-003, A-005 and A-006 as catalog-approved policies and
   states the contracts A-002 consumes. Separate certification folders are not
   necessary for this review. A-001 supplies execution-derived gross; A-005
   supports execution aggregation; A-003/A-006 supply attributed fee and
   non-funding totals. Catalog status is accepted as supplied evidence, not
   independently verified.
3. A-004 compatibility: PASS. Consume each unique event's final signed tranche
   allocation, then sum applicable allocations. Preserve A-004's event-time
   eligibility, source conservation, decimal-18 representability,
   deterministic residue assignment and pinned algorithm. A-002 must neither
   reallocate funding under A-006 nor round the net result to the funding
   quantum.
4. Evidence and finality: PASS at the declared boundary. FINAL requires
   complete overall and component coverage, attributed executions/cashflows,
   resolved identities/signs/ordering, and satisfied P6 terminality. Empty
   funding/cost rows establish zero only with complete coverage or evidenced
   non-applicability. Planned fees cannot replace actual evidence. A zero net
   result does not waive these requirements. Detailed P6 and post-final fence
   procedures remain delegated protocol dependencies.
5. Currency and precision: PASS. Every required monetary source and component
   must already match the pinned governed currency. Cross-currency facts
   remain in native units and block FINAL; cancellation between incompatible
   currencies cannot establish admissibility. Apply exact arithmetic to
   eligible component outputs, preserving their individual output rules without
   introducing intermediate or display rounding.
6. Double-counting: PASS. A-003 and A-006 describe production/allocation of
   the fee component, not two additive fee amounts. Funding and other costs
   remain distinct components; aliases resolve to one economic source.
   Aggregate native P&L is neither a substitute nor another summand.
   Execution-price effects already embedded in gross must not be charged again
   as an invented slippage component.
7. Identity, replay and restart: PASS as specified requirements. Persist one
   final result identity per tranche with frozen values, versions, currency,
   source/coverage evidence and closing/accounting timestamps. Identical
   replay produces no monetary effect; Portfolio records receipt once.
   Contrary post-FINAL evidence follows integrity/fence rules without
   rewriting or issuing another result. Persistence atomicity and crash
   recovery remain implementation verification obligations.
8. A-009 compatibility: PASS at the supplied interface. Attribute the result
   using the proven permanent final closing execution and pinned
   accounting-day policy, not delivery/finalization time. Late posting affects
   its original historical day, without entering today's Daily Loss/current
   daily base or duplicating wallet P&L. This establishes compatibility with
   the stated interface; it does not certify A-009.

Council-derived arithmetic checks, not executed tests or normative source
examples:

```text
100 - 3 + (-2) - 1 = 94
-10 - (-0.5) + 0.2 - (-0.1) = -9.2
```

## Eight Expert Verdicts

| Required perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE | Measures completed tranche economics including actual fees, funding and supported costs. Suitable for realized accounting; it supplies no forecast or entry/exit criterion. |
| Market Microstructure & Order Flow Researcher | APPROVE | Execution lineage and actual cashflows preserve factual trading outcomes. Alias resolution and exclusion of duplicate native P&L protect attribution. |
| Market Regime & Context Analyst | APPROVE | Accounting identity is regime-independent. Regime changes may affect component magnitudes and evidence latency, not the formula or signs. |
| Quant Strategy Researcher | APPROVE | Signs, units and additive structure are consistent. Exact arithmetic and upstream conservation support deterministic composition without parameter fitting. |
| Risk & Trade Management Architect | APPROVE | Incomplete or inadmissible evidence blocks FINAL. Historical posting rules are explicit; delayed final results alone cannot establish current exposure or loss completeness. |
| Execution & Exchange Mechanics Specialist | APPROVE | Preserves certified funding mechanics, actual fee requirements and governed currency. Venue-specific source completeness and restart behavior still require operational verification. |
| Adversarial Strategy Reviewer | APPROVE | Stated rules address missing-row zero assumptions, rebates, duplicate representations, currency mismatch and replay. These are specification protections, not evidence of implementation resistance. |
| Performance & Strategy Diagnostics Analyst | APPROVE | Component breakdown, lineage and accounting times support attribution and audit. Delayed finalization must remain distinguishable from absent losses or improved performance. |

## Finding Classification

| Classification | Finding | Disposition |
|---|---|---|
| SOURCE_GAP | Original upstream definitions/catalog entries, detailed P6/fence procedures and A-009 internals are not reproduced in the supplied evidence. | Non-blocking for A-002's explicitly delegated composition boundary; those dependencies are not independently certified here. |
| PRODUCT_DECISION | Single pinned currency without FX, one immutable final result, and historical-day posting are explicit policies. | Accepted for the declared role; no unresolved product decision identified. |
| EMPIRICAL_QUESTION | Reconciliation latency, unsupported-source frequency and diagnostics completeness remain unmeasured. | Non-blocking operational questions. Profitability validation is not applicable to this accounting identity. |
| SPECIFICATION_DEFECT | No contradiction or missing arithmetic rule identified within A-002's declared boundary. | None blocking. |
| NON_BLOCKING_LIMITATION | No complete normative numeric example; runtime/venue conformance and downstream certification are unavailable. "Net" covers the declared supported component domain. | Approval does not extend to arbitrary wallet economics or unverified runtime behavior. |

## Machine Record

```text
formula_id: A-002
review_mode: FULL_REVIEW
required_expert_perspectives_completed: 8
specification_status: APPROVED_FOR_DECLARED_COMPOSITION_ROLE
trading_fitness_status: APPROVED_AS_FINAL_REALIZED_ACCOUNTING
catalog_approved_upstream_evidence_sufficient: YES_FOR_DECLARED_CONTRACTS
certified_A004_compatibility: PASS
downstream_A009_compatibility: PASS_AT_SUPPLIED_INTERFACE
blocking_findings: NONE
full_council_approved: YES
another_review_cycle_required: NO_FOR_THIS_SPECIFICATION_SCOPE
```

Authority boundary: `FULL_COUNCIL_APPROVED` is formula-certification evidence
only. It authorizes no implementation, promotion, commit, deployment, paper or
live execution, exchange interaction or runtime trading decision.
