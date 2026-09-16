# A-004 SOURCE PACK

## 1. Identity

| Field | Extracted value | Evidence |
|---|---|---|
| Formula ID | A-004 | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula name | Funding calculation and allocation | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Owner | Accounting | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Type | ACCOUNTING_FORMULA | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula family | FUNDING | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Certification status | CERTIFICATION_REQUIRED | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Backend gate | BLOCK_FINAL_IMPLEMENTATION | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Catalog canonical-definition pointer | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` :: Funding postings; `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` :: funding remains separate algorithm | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Current implementation pointer | `src/triggertrade/backtest/simulator.py::_crosses_funding_boundary` RESEARCH/DEMO_ONLY | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Active methodology baseline | v1.2.14 | `docs/trading-methodology/` |

Catalog note: "Current simulator uses simplified funding boundaries; final canonical allocation requires review."

## 2. Source Index

| # | Source | Section | Authority | Relevance |
|---:|---|---|---|---|
| 1 | `docs/FORMULA_METRICS_CATALOG.md` | Master Catalog; Certification Queue | CATALOG / GATE | Identifies A-004, dependency N-007 and implementation gate. |
| 2 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` | §32 Funding attribution | PRIMARY FORMULA | Defines canonical funding retrieval, eligibility, pro-rata allocation, quantum, residue and version. |
| 3 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` | §30 Dedicated trading account baseline | CONTEXT | States managed futures account/subaccount contains only TriggerTrade-managed activity. |
| 4 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` | §34 Authoritative logical financial result | DOWNSTREAM ACCOUNTING | Includes allocated funding in final net result and defines finality context. |
| 5 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P7 Complete Lifecycle financial evidence | EVIDENCE / FINALITY | Requires Lifecycle to retrieve financial evidence through Order Management and complete coverage/finality. |
| 6 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P7.1 Currency admissibility | CURRENCY / FINALITY | Required monetary sources, including funding, must be in governed accounting/settlement currency before FINAL. |
| 7 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P7 sign normalization | SIGN SEMANTICS | Funding with CREDIT_POSITIVE source preserves wallet-effect sign. |
| 8 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P12 | BOUNDARY | Non-funding allocation is separate; funding keeps its separate algorithm. |
| 9 | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` | GET_FINANCIAL_FACTS | INPUT CONTRACT | Supplies funding rows, coverage, source identity, settlement price/basis and sign conventions. |
| 10 | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` | Monetary evidence; funding/cashflows shape | INPUT CONTRACT / SHARED ROWS | Shared financial row definitions and funding typed view. |
| 11 | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` | §2 Output classes; §2A | NUMERIC / CURRENCY POLICY | Funding has separate decimal-18 algorithm; unsupported currency blocks FINAL. |
| 12 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Funding sections | PLANNED ECONOMICS BOUNDARY | Funding is excluded from planned Minimum Net Edge and never an exit trigger. |
| 13 | `src/triggertrade/backtest/simulator.py` | `_crosses_funding_boundary` | NON-NORMATIVE IMPLEMENTATION EVIDENCE | Demo backtest blocks positions crossing 0/8/16 UTC funding times. |
| 14 | `src/triggertrade/accounting/futures.py` | `_funding_amount` | NON-NORMATIVE IMPLEMENTATION EVIDENCE | Current simple funding summation by directly attributed trade events; not pro-rata multi-tranche algorithm. |

## 3. Purpose and Trading Context

A-004 determines how factual funding cashflows are attributed to TriggerTrade logical tranches for realized accounting. Funding affects realized economics after it occurs. It is accounting data only, never an entry/exit signal, funding-triggered close, or planned pre-trade edge component.

The active methodology states funding is retrieved directly by Lifecycle through Order Management `GET_FINANCIAL_FACTS` with complete source identity and coverage, not forwarded by Portfolio.

## 4. Exact Formula Reconstruction

The active Order Lifecycle methodology defines the canonical funding allocation algorithm.

Managed-account premise:

```text
funding for managed symbol/side
=
TriggerTrade funding for that symbol/side
```

When multiple logical TriggerTrade tranches share the same symbol/native side, allocate each unique funding transaction pro-rata using one common settlement-notional basis at the funding effective time:

```text
tranche_funding
=
total_triggertrade_funding_for_symbol_side
*
(tranche_open_notional_at_funding_time
 /
 total_triggertrade_open_notional_for_symbol_side_at_funding_time)
```

with:

```text
tranche_open_notional_at_funding_time
=
attributable_open_quantity * common funding settlement/mark price for that event
```

Allocation quantum:

```text
0.000000000000000001 settlement-currency units
```

Raw allocation is computed at arbitrary precision, then each absolute magnitude is quantized toward zero to the allocation quantum and the source sign is reapplied. The signed residue:

```text
residue = signed_source_funding_amount - sum(base_allocations)
```

is assigned entirely to the tranche with the largest absolute unrounded allocation; ties use lowest `tranche_id` lexical order.

Persisted algorithm version:

```text
FUNDING_ALLOC_V1_DECIMAL18_TOWARD_ZERO_LARGEST_ABS_LEXICAL
```

## 5. Inputs

| Input | Meaning | Unit / type | Source | Required? |
|---|---|---|---|---|
| `cashflow_id` | Stable unique source funding transaction identity | Identifier | GET_FINANCIAL_FACTS / financial rows | Required |
| `signed_source_funding_amount` | Normalized wallet-effect funding amount | Governed settlement currency decimal | GET_FINANCIAL_FACTS; P7 sign rules | Required |
| `amount_quantum` | Factual source quantum | Decimal | Financial row | Required |
| `currency` | Native source currency | Currency code/string | Financial row | Required; must satisfy P7.1 for FINAL |
| `effective_at` | Funding effective event time | UTC timestamp | Financial row | Required |
| `recorded_at` | Source recorded time | UTC timestamp | Financial row | Required provenance |
| `symbol` / `native_side` / `position_idx` | Native funding scope | Identifiers | Financial row/native scope | Required for attribution |
| Settlement/mark price | Common funding allocation basis | Decimal price | Financial row settlement fields | Required when multiple tranches share scope |
| Settlement price basis/as-of/source ref | Provenance for allocation price | Strings/timestamps/ref | Financial row | Required |
| Eligible tranches | Tranches with attributable open quantity on funded symbol/side at event | Tranche IDs and quantities | Lifecycle state/execution lineage | Required |
| Attributable open quantity | Open quantity per eligible tranche at funding time | Quantity | Lifecycle attribution | Required |
| Total open notional | Sum of eligible tranche notionals at event | Settlement-currency notional | Derived | Required |
| Source coverage/finality | Complete interval/pagination/watermark/finality proof | Evidence | GET_FINANCIAL_FACTS/P7 | Required |

## 6. Outputs

| Output | Meaning | Unit / type |
|---|---|---|
| Per-tranche funding allocation | Signed funding amount attributed to one tranche | Settlement-currency decimal at 18-place quantum |
| Allocation manifest | Eligibility set, settlement price/basis, source transaction ID and signed allocations | Durable accounting evidence |
| Algorithm version | Funding allocation algorithm identifier | `FUNDING_ALLOC_V1_DECIMAL18_TOWARD_ZERO_LARGEST_ABS_LEXICAL` |
| Allocated total | Sum of tranche allocations | Must equal unique signed exchange funding amount exactly after residue assignment |

## 7. Units

Funding allocation is in settlement-currency units at decimal-18 allocation quantum. Required funding amounts must already be in the tranche's governed accounting/settlement currency before contributing to FINAL. Settlement/mark price supplies allocation weights only; it is not an FX conversion rate.

## 8. Parameters and Thresholds

No research threshold or configurable trading parameter is part of the canonical allocation formula.

Fixed algorithmic constants:

- allocation quantum: `0.000000000000000001`;
- quantization direction: toward zero on absolute magnitude, then reapply source sign;
- residue recipient: largest absolute unrounded allocation, tie lowest `tranche_id` lexical order;
- algorithm version: `FUNDING_ALLOC_V1_DECIMAL18_TOWARD_ZERO_LARGEST_ABS_LEXICAL`.

## 9. Sign Semantics

Canonical `cashflows[].signed_amount` is wallet effect: credit positive, debit negative. Funding with `CREDIT_POSITIVE` source convention is preserved as receipt positive and payment negative. Source-sign mappings are component-specific and must not be replaced by one generic sign rule.

The allocation formula conserves the signed source funding amount. Base allocations are signed after truncating absolute magnitude toward zero; residue is signed by subtraction from the signed source amount.

## 10. Domain and Preconditions

| Precondition | Behavior if not satisfied |
|---|---|
| Unique source funding transaction with stable `cashflow_id` | Duplicate representation must not count again; unresolved aliases block clean finality. |
| COMPLETE funding source identity/coverage/finality | PARTIAL/UNAVAILABLE prevents financial FINAL. |
| Funding source already in governed accounting/settlement currency | Other-currency facts are retained and block finality; no conversion. |
| Eligible tranches established by attributable open quantity at funding effective event | Ambiguity enters reconciliation, not arbitrary attribution. |
| Common settlement/mark price and provenance available for event | Missing basis prevents deterministic multi-tranche allocation. |
| Source amount exactly representable at decimal-18 quantum | Otherwise financial attribution remains RECONCILING rather than rounding source cashflow. |
| Authoritative event ordering for same exchange timestamp available when needed | Unresolved ties enter reconciliation. |

## 11. Boundary Conditions

| Boundary | Canonical behavior |
|---|---|
| One eligible tranche | Entire signed funding amount attributes to that tranche, subject to source/currency/finality requirements. |
| Multiple eligible tranches | Use pro-rata settlement-notional formula with deterministic quantum/residue algorithm. |
| Equal largest absolute unrounded allocation | Residue recipient is lowest `tranche_id` lexical order. |
| Zero source funding amount | Allocated total must equal zero; zero allocations are possible. |
| Missing funding rows | Counts as zero only with COMPLETE coverage or evidenced non-applicability; absence of rows is not proof of zero. |
| Duplicate API representation of same transaction | No second count; aliases/provenance must resolve to one source event. |
| Cross-currency source | Retain source and block FINAL; no FX conversion. |
| Same timestamp execution/cashflow ambiguity | Reconciliation until authoritative sequence resolves ordering. |

## 12. Precision and Rounding

The funding algorithm is separate from P12 non-funding cashflow allocation. It uses decimal-18 settlement-currency quantum and the specified toward-zero/residue algorithm. Source amount itself must be exactly representable at that quantum; do not round the source funding cashflow.

## 13. Time Semantics

Funding eligibility and weights are evaluated at the funding effective time. The source coverage interval is half-open `[from, to)` and must include all causally applicable records through the required cutoff. Equal timestamp ambiguity without native sequencing remains unresolved.

N-007 supplies approved factual window/accounting-day semantics, but A-004's allocation event is funding effective time, not Portfolio accounting-day posting. A-009 later consumes final results by accounting day.

## 14. State / Replay / Restart

Persist eligibility set, settlement price/basis, source transaction ID, signed allocations and algorithm version. Duplicate source identities and aliases must be resolved before counting. Accepted financial coverage/certificate history is restored across restart before new evidence. Reusing a known certificate/source identity with changed content is a contradiction, not a new allocation.

## 15. Version / Configuration Pinning

The formula pins:

```text
funding_allocation_algorithm_version =
FUNDING_ALLOC_V1_DECIMAL18_TOWARD_ZERO_LARGEST_ABS_LEXICAL
```

The tranche governed accounting/settlement currency is pinned at first accounting use under P17/P7.1 and cannot be changed at finalization to fit incoming rows.

## 16. Ownership

Lifecycle owns funding attribution and final logical financial results. API supplies factual financial rows only. Portfolio does not forward financial facts to Lifecycle and does not derive a competing logical result. Position excludes funding from planned Minimum Net Edge and does not use funding as an exit trigger.

## 17. Downstream Consumers

| Consumer | Relationship |
|---|---|
| A-002 Net final result | Consumes allocated funding in `net_realized_result = gross - fees + allocated_funding - other costs`. |
| A-009 Accounting-day realized totals | Indirectly consumes finalized A-002 results by accounting day. |
| Portfolio Daily Loss | Consumes logical final results, not raw funding rows. |
| Diagnostics/research | May analyze realized funding; does not make it a trading signal. |

## 18. Dependencies

| Dependency | Class | Status |
|---|---|---|
| N-007 UTC factual windows and Asia/Jerusalem accounting day | APPROVED_POLICY | A-004 depends on factual window rules; accounting-day aggregation is downstream in A-009. |
| P7/P7.1 financial evidence and currency admissibility | APPROVED_POLICY / DOCUMENTATION_DEPENDENCY | Required for funding source eligibility and finality. |
| Order Management GET_FINANCIAL_FACTS | DOCUMENTATION_DEPENDENCY | Supplies funding facts, settlement basis and coverage. |
| TT_NUMERIC_V1 | APPROVED_POLICY | Funding is a separate decimal-18 algorithm preserved by the numeric policy. |

## 19. Worked / Conformance Examples Present

No explicit numeric multi-tranche funding allocation worked example was found in the extracted active methodology. The formula text provides enough deterministic mechanics to construct examples for Council or later conformance tests.

Non-normative current code:

- backtest simulator blocks a simulated trade crossing 0/8/16 UTC funding boundaries because funding is unsupported there;
- accounting helper sums directly attributed funding events by trade ID/symbol/asset/direction and rejects duplicates/mismatches.

Those are not the canonical multi-tranche pro-rata allocation algorithm.

## 20. Source Gaps and Ambiguities

| # | Gap / ambiguity | Impact |
|---:|---|---|
| 1 | No explicit numeric worked example in active methodology. | Non-blocking if Council accepts formula completeness; useful for final spec examples. |
| 2 | Native venue/profile conformance that all required funding sources settle in governed currency is not certified by methodology. | Runtime conformance gate; not a formula arithmetic gap. |
| 3 | Same-timestamp ordering depends on authoritative native sequence when available; unresolved ties reconcile. | Boundary/finality behavior is defined as blocking, not arbitrary. |
| 4 | Relationship to A-002 final result is downstream; A-004 alone does not certify complete net result. | Requires A-002 review after A-004. |

## 21. Reviewer Handoff Summary

```text
FORMULA_ID: A-004
FORMULA_NAME: Funding calculation and allocation

EXACT_FORMULA_RECONSTRUCTABLE:
YES

DECLARED_ACCOUNTING_PURPOSE_RECONSTRUCTABLE:
YES

INPUT_DOMAIN_COMPLETE:
YES_WITH_RUNTIME_CONFORMANCE_BOUNDARIES

BOUNDARY_BEHAVIOR_COMPLETE:
YES

TIME_SEMANTICS_COMPLETE:
YES

DIRECTION_OR_SIGN_SEMANTICS_COMPLETE:
YES

PARAMETER_PROVENANCE_COMPLETE:
YES

STATE_REPLAY_SEMANTICS_COMPLETE:
YES

SOURCE_GAP_COUNT:
4_NON_BLOCKING_OR_EXTERNAL_CONFORMANCE

READY_FOR_FULL_EXPERT_COUNCIL_REVIEW:
YES

BLOCKING_EXTRACTION_GAPS:
NONE IDENTIFIED
```
