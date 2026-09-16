# A-002 SOURCE PACK

## 1. Identity

| Field | Extracted value | Evidence |
|---|---|---|
| Formula ID | A-002 | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula name | Net final result calculation | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Owner | Accounting | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Type | ACCOUNTING_FORMULA | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula family | PNL | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Certification status | CERTIFICATION_REQUIRED | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Backend gate | BLOCK_FINAL_IMPLEMENTATION | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Catalog canonical-definition pointer | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` :: Financial factual response; `docs/BACKEND_IMPLEMENTATION_TRACEABILITY.md` :: Formula Parallelization Map, Accounting final result | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Current implementation pointer | `src/triggertrade/accounting/futures.py::close_futures_trade` DEMO_ONLY | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Active methodology baseline | v1.2.14 | `docs/trading-methodology/` |

Catalog note: Traceability marks accounting final result as formula-gated.

## 2. Source Index

| # | Source | Section | Authority | Relevance |
|---:|---|---|---|---|
| 1 | `docs/FORMULA_METRICS_CATALOG.md` | Master Catalog; Certification Queue | CATALOG / GATE | Identifies A-002 and dependencies A-001, A-003, A-004, A-005, A-006. |
| 2 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` | §34 Authoritative logical financial result | PRIMARY FORMULA | Defines exact net result formula, finality and persistence requirements. |
| 3 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P7 Complete Lifecycle financial evidence | EVIDENCE / FINALITY | Requires complete executions, fees, funding, costs, attribution and coverage. |
| 4 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P7.1 Currency admissibility | CURRENCY / FINALITY | Requires all monetary components in pinned governed accounting/settlement currency before FINAL. |
| 5 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P7 sign normalization | SIGN SEMANTICS | Defines wallet-effect signs and cost-effect conversions. |
| 6 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P12 non-funding cashflow allocation | DEPENDENCY / A-006 | Defines non-funding allocation and cost-effect totals consumed by A-002. |
| 7 | `docs/trading-methodology/business-contracts/ORDER_EVENT.md` | Financial result | OUTPUT CONTRACT | Defines final financial_result payload fields and once-only producer/consumer boundaries. |
| 8 | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` | GET_FINANCIAL_FACTS | INPUT CONTRACT | Supplies executions, cashflows, coverage and component coverage. |
| 9 | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` | §§1-2A | NUMERIC / CURRENCY POLICY | Exact monetary arithmetic, output classes, no cross-currency conversion. |
| 10 | `docs/formula-certification/A-004/A-004_FINAL_FORMULA_SPECIFICATION.md` | Final specification | CERTIFIED_FORMULA | Certified funding allocation input to A-002. |
| 11 | `src/triggertrade/accounting/futures.py` | `gross_pnl`, `close_futures_trade` | NON-NORMATIVE IMPLEMENTATION EVIDENCE | Demo formula calculates gross, fees, funding and net PnL. |
| 12 | `tests/unit/test_futures_accounting.py` | Accounting unit tests | NON-NORMATIVE TEST EVIDENCE | Demonstrates demo behavior for gross, fees, funding and fail-closed cases. |

## 3. Purpose and Accounting Context

A-002 produces the authoritative final net realized result for a logical
tranche after all required financial evidence, attribution, currency
admissibility and terminality requirements are satisfied.

Lifecycle is the sole logical-tranche final financial producer. Portfolio
receives the final Order Event and posts it once to the immutable economic day.
Portfolio does not recompute logical P&L from aggregate native position or
wallet facts.

## 4. Exact Formula Reconstruction

The active methodology defines:

```text
net_realized_result = gross_realized_trading_result
                    - actual_fees_rebates
                    + allocated_funding
                    - other_supported_exchange_costs
```

Component meanings:

- `gross_realized_trading_result`: execution-derived gross result computed by
  logical execution lineage, not by duplicate aggregate native P&L.
- `actual_fees_rebates`: cost-effect total. Fees increase the value; rebates
  make it negative and therefore increase net result when subtracted.
- `allocated_funding`: signed funding receipt/payment from certified A-004.
  Receipts are positive; payments are negative.
- `other_supported_exchange_costs`: cost-effect total. Costs increase the
  value; refunds make it negative and therefore increase net result when
  subtracted.

Planned fees and aggregate native P&L are never substitutes for actual
component evidence.

## 5. Inputs

| Input | Meaning | Unit / type | Dependency | Required? |
|---|---|---|---|---|
| `gross_realized_trading_result` | Directional gross result from entry/exit executions | Governed accounting currency decimal | A-001 | Required |
| `actual_fees_rebates` | Cost-effect total from attributed fee/rebate cashflows | Governed accounting currency decimal | A-003 / A-006 | Required |
| `allocated_funding` | Signed funding allocation | Governed accounting currency decimal | A-004 certified | Required, zero only with complete coverage or non-applicability |
| `other_supported_exchange_costs` | Cost-effect total from supported other exchange costs | Governed accounting currency decimal | A-006 / P7 | Required if applicable; zero only with complete coverage or non-applicability |
| `currency` | Pinned governed accounting/settlement currency | Currency identifier | P7.1 / numeric policy | Required |
| `source_lineage` | Execution IDs, cashflow IDs, native observations and final closing execution | Identifiers | Order Event v7 | Required |
| `source_coverage` | COMPLETE financial coverage and component coverage | Evidence envelope | GET_FINANCIAL_FACTS / P7 | Required |
| Accounting timestamps | `accounting_effective_at`, day, closed/finalized/terminalized times | UTC / policy IDs | P8 / Order Event | Required |

## 6. Outputs

| Output | Meaning |
|---|---|
| `net_realized_result` | Final net realized result for the logical tranche. |
| `financial_result` | FINAL payload containing gross, fees, funding, other costs, net result, currency, lineage, coverage and accounting timestamps. |
| `result_id` | Exactly one final result identity per tranche. |
| Portfolio event | FINAL Order Event consumed once by Portfolio. |

## 7. Units

All monetary components that participate in FINAL must already be in the
tranche's pinned governed accounting/settlement currency. A required source in
a different currency is retained in native units and blocks FINAL. No FX
conversion is supported.

## 8. Parameters and Thresholds

A-002 has no trading threshold, research parameter or optimization parameter.
It is deterministic accounting arithmetic over final eligible components.

## 9. Sign Semantics

Normalized API `signed_amount` is wallet effect:

- credit positive;
- debit negative.

A-002 consumes component totals after component-specific conversion:

- `actual_fees_rebates = -sum(attributed TRADING_FEE signed_amount)`;
- `other_supported_exchange_costs = -sum(attributed OTHER_EXCHANGE_COST signed_amount)`;
- `allocated_funding` remains signed receipt/payment from A-004.

Therefore:

- fee charge: positive cost-effect total, subtracts from net;
- fee rebate: negative cost-effect total, increases net when subtracted;
- funding receipt: positive, increases net;
- funding payment: negative, decreases net;
- other cost: positive cost-effect total, subtracts from net;
- other refund: negative cost-effect total, increases net when subtracted.

## 10. Domain and Preconditions

Before A-002 can produce FINAL:

1. COMPLETE mandatory financial evidence and component/overall coverage exist.
2. Entry/exit executions and all mandatory source components are deterministically attributed.
3. Every component and required source amount is already denominated in the pinned governed accounting/settlement currency.
4. No unresolved cross-currency source remains.
5. No unresolved duplicate, alias, ordering, sign-convention or source-identity contradiction remains.
6. All P6 terminality and finality conditions hold.
7. A-004 funding allocation is complete for funding sources or complete evidence proves no applicable funding rows.
8. Non-funding cashflow allocations are complete and source-conserving under A-006/P12.

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
| Contrary post-FINAL evidence | Preserve frozen result and use post-final integrity/fence rules; do not rewrite or duplicate result. |

## 12. Boundaries

A-002 begins only after component values are eligible and attributed. It does
not define:

- gross PnL mechanics (A-001);
- fee attribution mechanics (A-003);
- funding allocation mechanics (A-004);
- VWAP/cumulative execution aggregation (A-005);
- non-funding cashflow allocation/residue mechanics (A-006);
- accounting-day aggregation (A-009).

A-002 combines these approved/certified component outputs into the final net
result and preserves their evidence/finality boundaries.

## 13. Precision

Monetary arithmetic follows exact decimal/rational `TT_NUMERIC_V1` rules.
Finite products and sums retain exact finite digits. No finite-precision
intermediate rounding, epsilon comparison or display rounding may feed the
final net result.

Each component's own output class and quantization must already be satisfied
before A-002 consumes it. A-002 does not round source cashflows or convert
currencies.

## 14. Time Semantics

`accounting_effective_at` is the proven permanent final closing execution time.
`accounting_day_id` follows the Portfolio accounting policy. `closed_at`,
`finalized_at` and `terminalized_at` are distinct lifecycle/finality times.

Late historical posting updates only the immutable historical day; it never
moves the result to today, current Daily Loss, or current daily base, and never
adds wallet P&L twice.

## 15. State / Replay / Restart

Persist exactly one result ID per tranche and the complete source set/coverage,
final closing execution ID, accounting timestamps, accounting policy, component
values and net result.

No provisional result exists. Replay keeps the same result ID and values.
Identical event/result replay has no monetary side effect. Portfolio records
delivery once in its receipt ledger.

## 16. Version / Configuration Pinning

The financial result carries:

- result version;
- accounting algorithm version;
- pinned governed accounting/settlement currency;
- accounting policy version;
- source lineage and coverage.

The governed currency cannot be selected from incoming rows or changed at
recovery.

## 17. Ownership

Lifecycle owns final logical financial result production. API supplies factual
executions/cashflows and coverage only. Portfolio consumes the final result
once and does not recompute it. Position does not supply the final financial
result.

## 18. Downstream Consumers

| Consumer | Relationship |
|---|---|
| Portfolio Rules | Consumes final Order Event and posts once. |
| A-009 | Aggregates realized totals and Daily Loss gate input by accounting day. |
| Dashboard / diagnostics | Display final result and source lineage; must not recompute from aggregate native wallet facts. |

## 19. Dependencies

| Dependency | Class | Status |
|---|---|---|
| A-001 Gross PnL calculation | APPROVED_POLICY | Catalog says approved as defined / implement allowed. |
| A-003 Fee cashflow calculation and attribution | APPROVED_POLICY | Catalog says approved as defined / implement allowed. |
| A-004 Funding calculation and allocation | CERTIFIED_FORMULA | `A-004_FINAL_FORMULA_SPECIFICATION.md` has `FULL_COUNCIL_APPROVED = YES`. |
| A-005 Cumulative fill quantity, remaining quantity and VWAP | APPROVED_POLICY | Catalog says approved as defined / implement allowed. |
| A-006 Execution-linked cashflow allocation and residue assignment | APPROVED_POLICY | Catalog says approved as defined / implement allowed. |
| P7/P7.1 financial evidence/currency | APPROVED_POLICY / DOCUMENTATION_DEPENDENCY | Required for finality and component eligibility. |
| TT_NUMERIC_V1 | APPROVED_POLICY | Governs exact monetary arithmetic. |

## 20. Worked / Conformance Examples Present

Active methodology provides the formula but no complete normative numeric
worked example for all components.

Non-normative current tests demonstrate demo behavior:

- long gross 0.20, entry fee 0.002, exit fee 0.002, funding -0.003 gives net
  0.193;
- short gross profit/loss examples;
- partial close prorates entry fee in demo code;
- duplicate funding and mismatched funding attribution fail closed.

These examples are useful for candidate comparison only. They do not certify
current implementation or replace active methodology.

## 21. Source Gaps and Ambiguities

| # | Gap / ambiguity | Impact |
|---:|---|---|
| 1 | No normative full numeric example in active methodology. | Non-blocking if Council accepts formula and component boundaries. |
| 2 | A-001/A-003/A-005/A-006 are approved as defined by catalog but do not have final certification folders. | Catalog classifies them implementable; Council should decide whether this evidence is sufficient dependency closure. |
| 3 | Runtime venue/profile conformance is not supplied. | Implementation/live-readiness boundary, not formula arithmetic. |
| 4 | A-009 accounting-day aggregation is downstream and not certified here. | Does not block A-002 unless Council finds daily posting semantics essential. |

## 22. Reviewer Handoff Summary

```text
FORMULA_ID: A-002
FORMULA_NAME: Net final result calculation

EXACT_FORMULA_RECONSTRUCTABLE:
YES

DECLARED_ACCOUNTING_PURPOSE_RECONSTRUCTABLE:
YES

INPUT_DOMAIN_COMPLETE:
YES_WITH_DEPENDENCY_AND_RUNTIME_CONFORMANCE_BOUNDARIES

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
4_NON_BLOCKING_OR_DEPENDENCY_CLASSIFICATION

READY_FOR_FULL_EXPERT_COUNCIL_REVIEW:
YES

BLOCKING_EXTRACTION_GAPS:
NONE IDENTIFIED BY ORCHESTRATOR
```
