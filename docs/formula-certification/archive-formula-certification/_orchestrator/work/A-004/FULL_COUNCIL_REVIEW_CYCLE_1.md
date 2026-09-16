# A-004 FULL COUNCIL REVIEW CYCLE 1

Mode: FULL_REVIEW
Council route: `FULL_COUNCIL`
Result: `FULL_COUNCIL_APPROVED = YES`
Another review cycle required: NO

## Council Summary

A-004 is certified for allocation of factual funding cashflows to logical
tranches for realized accounting. Exchange funding-rate calculation,
forecasting and trading signals are outside the certified role.

Council reported that only
`docs/formula-certification/A-004/A-004_SOURCE_PACK.md` was read, all eight
required perspectives were applied in one review, no subagents were used, and
no repository search, edits or execution were performed.

## Certified Algorithm

```text
FUNDING_ALLOC_V1_DECIMAL18_TOWARD_ZERO_LARGEST_ABS_LEXICAL
```

For `n` eligible tranches, nonnegative weights summing to one, and source
amount `F`, the base allocation is:

```text
b_i = sign(F) * q * floor((abs(F) / q) * w_i)
q = 0.000000000000000001
```

The residue:

```text
R = F - sum(b_i)
```

is an exact multiple of `q`, with `abs(R) <= (n - 1)q`. Assigning it once to the
largest absolute unrounded allocation, with lowest lexical `tranche_id` as the
tie-breaker, proves exact conservation and sign symmetry.

## Specification Checks

| Area | Assessment |
|---|---|
| Source identity | PASS. Allocate each unique funding transaction once. Duplicate representations require resolved aliases; reusing an identity with changed content is a contradiction. |
| Coverage and finality | PASS. COMPLETE identity, coverage and finality evidence are prerequisites for financial FINAL. Missing rows establish zero only with complete coverage or evidenced non-applicability. |
| Currency admissibility | PASS. Funding must already use the tranche's pinned accounting/settlement currency. Other-currency facts remain retained and block FINAL. Settlement price supplies weights and cannot perform FX conversion. |
| Sign semantics | PASS. Normalized funding uses wallet effect: receipts positive, payments negative. Preserve `CREDIT_POSITIVE` funding signs. |
| Eligibility and weights | PASS within declared domain. Use attributable open quantities at funding effective time within one symbol/native-side scope. A common settlement price gives `w_i = Q_i / sum(Q)`. |
| Decimal-18 allocation | PASS. Source amount must be exactly representable at `q = 10^-18`; otherwise reconcile without rounding the source. |
| Residue assignment | PASS. Assign entire signed residue to the largest absolute unrounded allocation, tie lowest lexical `tranche_id`. |
| Replay and restart | PASS at specification level. Persist eligibility evidence, basis, source identity, allocations and version; restore accepted coverage/certificate history before new evidence. |
| A-002 compatibility | PASS at supplied interface. Add signed allocated funding in `gross - fees + allocated_funding - other costs`; consume once and preserve exact amount. |

## Eight Expert Verdicts

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

## Findings Classification

| Class | Finding | Certification effect |
|---|---|---|
| SOURCE_GAP | Venue/profile evidence for source identity, currency, settlement basis, sequencing, complete coverage and managed-account scope is not supplied. | Non-blocking for formula specification; unresolved conformance prevents qualified runtime use. |
| SOURCE_GAP | Full A-002 numeric/finality behavior and executable replay/persistence evidence are outside this pack. | Interface compatibility supported; downstream and implementation certification remain outstanding. |
| PRODUCT_DECISION | Entire residue goes to largest raw allocation, lexical tie-break. Repeated ties can favor same ID. | Accepted as explicit deterministic accounting policy. |
| EMPIRICAL_QUESTION | Actual funding burden, residue concentration, delayed evidence frequency and reconciliation duration unknown. | Operational/performance diagnostics only. |
| SPECIFICATION_DEFECT | None identified. | No blocking defect. |
| NON_BLOCKING_LIMITATION | Pack lacks normative numeric examples and current helpers are noncanonical. | Council examples clarify arithmetic; implementation/venue conformance not certified. |

## Council Decision

```text
formula_id: A-004
formula_name: Funding calculation and allocation
specification_correctness: CERTIFIED
accounting_trading_fitness: APPROVED_AS_REALIZED_ACCOUNTING_ATTRIBUTION
blocking_findings: NONE
full_council_approved: YES
another_review_cycle_required: NO
```

Authority boundary: this record is formula-certification evidence only. It
authorizes no implementation, promotion, commit, deployment, paper/live
execution, exchange interaction, or runtime trading decision.
