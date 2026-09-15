# A-009 SOURCE PACK

## 1. Identity

| Field | Extracted value | Evidence |
|---|---|---|
| Formula ID | A-009 | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula name | Accounting-day realized totals and daily loss gate input | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Owner | Accounting / Portfolio Rules | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Type | ACCOUNTING_FORMULA | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula family | DRAWDOWN | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Certification status | CERTIFICATION_REQUIRED | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Backend gate | BLOCK_FINAL_IMPLEMENTATION | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Catalog canonical-definition pointer | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` :: Accounting day and cash postings | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Current implementation pointer | `src/triggertrade/services/daily_loss.py` DEMO_ONLY | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Active methodology baseline | v1.2.14 | `docs/trading-methodology/` |

Catalog note: final daily-loss calculation/gate must remain blocked until
certified.

## 2. Source Index

| # | Source | Section | Authority | Relevance |
|---:|---|---|---|---|
| 1 | `docs/FORMULA_METRICS_CATALOG.md` | Master Catalog; Certification Queue | CATALOG / GATE | Identifies A-009, dependencies A-002, N-007, T-009 and backend gate. |
| 2 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` | §23 Daily Loss Limit | PRIMARY FORMULA | Defines daily loss amount, daily realized PnL aggregation and latch rule. |
| 3 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` | Accounting day appendix / metric scopes | PRIMARY SCOPE | Defines Asia/Jerusalem day boundary, fixed daily base and distinct metric scopes. |
| 4 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` | Appendix F | RECEIPT / STATE | Defines once-only receipt, immutable day posting, restart behavior and API native P&L exclusion. |
| 5 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md` | P8 Economic time, operational time and accounting day | TIME / STATE POLICY | Defines `accounting_effective_at`, `accounting_day_id`, late historical posting and replay. |
| 6 | `docs/trading-methodology/business-contracts/ORDER_EVENT.md` | Financial result fields | INPUT CONTRACT | Defines final result timestamps, accounting policy and payload fields consumed by Portfolio. |
| 7 | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` | Monetary evidence, provenance and boundaries | PORTFOLIO/API BOUNDARY | Confirms Portfolio uses Lifecycle FINAL results for logical Daily Loss and not wallet rows. |
| 8 | `docs/formula-certification/A-002/A-002_FINAL_FORMULA_SPECIFICATION.md` | Final specification | CERTIFIED_FORMULA | Supplies certified `net_realized_result` input and posting interface. |
| 9 | `src/triggertrade/services/daily_loss.py` | `DailyLossEvaluator` | NON-NORMATIVE IMPLEMENTATION EVIDENCE | Demo implementation evaluates UTC trading day and active accounting store values. |
| 10 | `src/triggertrade/persistence/futures_accounting_store.py` | `realized_net_pnl_for_utc_day` | NON-NORMATIVE IMPLEMENTATION EVIDENCE | Demo query sums `net_pnl` from `closed_at` UTC day, not certified A-002/P8 day. |
| 11 | `tests/unit/test_daily_loss.py` | Daily loss tests | NON-NORMATIVE TEST EVIDENCE | Demonstrates demo UTC-day latch, baseline and fail-closed behavior. |

## 3. Purpose and Trading Context

A-009 defines the Portfolio-owned accounting-day realized total used as the
input to the Daily Loss gate for new exposure.

Its trading role is protective risk control: if realized losses for the current
accounting day reach the configured Daily Loss threshold, Portfolio blocks new
Coin OPEN and new grants/holds. It does not force-close existing exposure,
cancel existing entries/protection, or create a funding/time-based exit.

## 4. Exact Formula Reconstruction

The active methodology defines:

```text
daily_loss_limit_amount = daily_portfolio_base * daily_loss_limit_pct / 100

daily_realized_pnl[accounting_day_id]
= sum(FINAL logical net results bound to that accounting_day_id)

if enabled and current_day.daily_realized_pnl <= -daily_loss_limit_amount:
    latch DAILY_LOSS_LIMIT_REACHED for the current day
```

The certified A-002 input is:

```text
net_realized_result = gross_realized_trading_result
                    - actual_fees_rebates
                    + allocated_funding
                    - other_supported_exchange_costs
```

Only FINAL logical A-002 results with COMPLETE evidence and a valid immutable
`accounting_day_id` enter A-009.

## 5. Inputs

| Input | Meaning | Unit / type | Dependency | Required? |
|---|---|---|---|---|
| `accounting_day_id` | Immutable day identifier in Portfolio accounting policy | Date / string | N-007 / P8 | Required |
| `accounting_day_interval` | Half-open Asia/Jerusalem local-midnight interval `[local 00:00, next local 00:00)` | Time interval | N-007 / P8 | Required |
| FINAL A-002 result set | Exactly-once received final logical results bound to the day | Set of result IDs / tranche IDs | A-002 | Required |
| `net_realized_result` | Final net realized result per logical tranche | Governed accounting currency decimal | A-002 certified | Required |
| `result_id` and `tranche_id` | Idempotency keys for once-only posting | Identifiers | Order Event / P8 | Required |
| `accounting_effective_at` | Final economic closing execution timestamp | UTC/RFC3339 instant | P8 / P13 | Required |
| `accounting_policy` | `Asia/Jerusalem`, `00:00:00`, `ACCOUNTING_DAY_V1` | Policy object | N-007 | Required |
| `daily_portfolio_base` | Fixed capital base for the accounting day | Governed accounting currency decimal | Portfolio Rules | Required when gate enabled |
| `daily_loss_limit_pct` | Configured Daily Loss threshold percent | Percent / decimal | T-009 | Required when gate enabled |
| `daily_loss_limit_enabled` | Gate enabled flag | Boolean | Portfolio configuration | Required |
| Existing day latch state | Whether the current day already latched | Durable state | Portfolio Rules | Required |

## 6. Outputs

| Output | Meaning |
|---|---|
| `daily_realized_pnl[accounting_day_id]` | Sum of FINAL A-002 net results posted exactly once to the immutable day. |
| `daily_loss_limit_amount` | Currency amount threshold computed from daily base and configured threshold. |
| `daily_loss_status` | `DISABLED`, `OK`, `LIMIT_REACHED`, `LATCHED`, or an unavailable/fail-closed status. |
| `daily_loss_latch` | Durable current-day latch when threshold is reached. |
| Gate result | Permission/blocking evidence for new Coin OPEN and new grants/holds. |

## 7. Units

`daily_realized_pnl`, `daily_portfolio_base`, `daily_loss_limit_amount`, and
A-002 `net_realized_result` use the governed Portfolio accounting currency.

No cross-currency aggregation is authorized. A required final result with an
unsupported currency cannot enter the day total until upstream finality and
currency admissibility are resolved.

## 8. Parameters and Thresholds

| Identifier | Class | Meaning |
|---|---|---|
| `daily_loss_limit_enabled` | CONFIG_PARAMETER | Enables/disables the Daily Loss gate. |
| `daily_loss_limit_pct` / T-009 | RESEARCH_PARAMETER / CONFIG_PARAMETER | Configurable threshold value. Certification should define its use, not the optimal value. |
| `ACCOUNTING_DAY_V1` | APPROVED_POLICY | Named timezone `Asia/Jerusalem`, local midnight boundary. |

No empirical profitability claim is made for any threshold value.

## 9. Sign and Direction Semantics

`net_realized_result` is signed:

- positive means realized gain;
- negative means realized loss;
- zero means no net realized gain/loss after all certified components.

Loss consumed by the gate is:

```text
daily_loss_used_amount = max(-daily_realized_pnl[accounting_day_id], 0)
```

The latch condition in active methodology is inclusive:

```text
daily_realized_pnl <= -daily_loss_limit_amount
```

Positive realized results reduce the magnitude of a not-yet-latched current-day
loss total. After the current day latches, later profit does not unlatch it;
the latch resets only at next accounting-day rollover.

## 10. Domain and Preconditions

Before A-009 can produce a current-day gate decision:

1. The current accounting day and boundary instant are known under
   `ACCOUNTING_DAY_V1`.
2. The day's `daily_portfolio_base` is fixed from authoritative boundary
   evidence or complete deterministic reconstruction.
3. All included results are FINAL A-002 logical results with complete evidence,
   valid result/tranche identities, governed currency and immutable
   `accounting_day_id`.
4. Each result is posted at most once by both `result_id` and `tranche_id`.
5. Existing day records, receipt deduplication, latch/base state and late
   historical posting state are restored before processing events.
6. If the gate is enabled, `daily_loss_limit_pct` is present and positive.

## 11. Missing / Invalid Behavior

| Case | Required behavior |
|---|---|
| Daily Loss disabled | No blocking; no baseline/final-result evidence required for the gate. |
| Missing or invalid threshold while enabled | Fail closed for new exposure; no fabricated threshold. |
| Missing current-day base while enabled | Fail closed for new exposure; state remains reconciling. |
| Missing or unresolved accounting day | Fail closed for new exposure. |
| Non-FINAL or incomplete logical result | Exclude from realized total; no provisional posting. |
| Duplicate identical result receipt | No-op; no second monetary effect. |
| Conflicting result under `result_id` or `tranche_id` | Integrity error; do not silently rewrite totals. |
| Late historical result | Post once to its immutable historical day only; do not affect current Daily Loss/latch/base. |
| Native/API aggregate P&L row | Cannot substitute for the logical result and cannot be double-added. |
| Cross-currency result | Block upstream finality or exclude until admissible; do not convert or net across currencies. |

## 12. Boundaries

A-009 defines accounting-day aggregation and the Daily Loss gate input. It does
not define:

- A-002 final net result internals;
- daily base construction beyond consuming the fixed Portfolio base;
- the optimal T-009 threshold value;
- entry/exit signals;
- forced liquidation;
- current wallet equity or unrealized P&L;
- research drawdown metrics such as M-004;
- backend implementation details.

## 13. Precision

All arithmetic uses exact decimal/rational monetary rules from the active
numeric policy. `daily_loss_limit_amount` is an exact product/division
expression. No arbitrary decimal context, floating-point conversion, epsilon,
presentation rounding, or report formatting may feed the gate decision.

The Council should decide whether the threshold comparison needs an explicit
output quantum/rounding class or whether exact comparison is sufficient.

## 14. Time Semantics

N-007 / P8 define:

```text
accounting_timezone = Asia/Jerusalem
day_boundary_local = 00:00:00
accounting_policy_version = ACCOUNTING_DAY_V1
accounting_day_interval = [local 00:00, next local 00:00)
```

`accounting_effective_at` is the timestamp of the final economic closing
execution that permanently reduced the logical tranche to zero. Delivery,
cleanup, callback, finalization and receipt time are not substitutes.

`accounting_day_id` is the immutable date in the accounting timezone containing
`accounting_effective_at`.

Late delivery posts only to the immutable historical day. It never rebases the
current day, never relatches the current day as if the result occurred today,
and never adds cash to wallet capital again.

## 15. State / Replay / Restart

Portfolio persists:

- accounting-day records and boundary instants;
- fixed daily base;
- current-day latch state;
- result receipt ledger keyed by result ID and tranche ID;
- day totals;
- terminal release application state;
- unresolved integrity/reconciliation incidents.

Restart must restore receipts, day records, latch/base, commitment buckets and
unresolved native observations before processing events.

Identical result replay is a no-op. Conflicting result replay is an integrity
error. A historical day remains open to first exactly-once final posting, but
already posted final values cannot be silently changed.

## 16. Version / Configuration Pinning

The gate decision carries:

- accounting policy version `ACCOUNTING_DAY_V1`;
- rules version containing `daily_loss_limit_enabled` and
  `daily_loss_limit_pct`;
- day boundary instant evidence;
- base source/evidence;
- included result IDs and tranche IDs;
- result receipt ledger state;
- evaluation time.

## 17. Ownership

Portfolio Rules owns Daily Loss, daily base, accounting-day records, receipts
and gate decisions.

Lifecycle owns A-002 final logical financial result production. API supplies
wallet/native facts for capital and factual evidence only. API does not decide
eligibility, create grants, or produce logical-tranche accounting. Position
does not own Daily Loss.

## 18. Downstream Consumers

| Consumer | Relationship |
|---|---|
| Portfolio entry gate | Blocks or permits new Coin OPEN and new grants/holds. |
| Capital and Limits | Supplies accounting policy and receives current-day gate status. |
| Dashboard / diagnostics | Displays daily realized PnL, threshold, latch and evidence. |
| Runtime authorization | Must use current Daily Loss latch during atomic hold/authorization. |

## 19. Dependencies

| Dependency | Class | Status |
|---|---|---|
| A-002 Net final result calculation | CERTIFIED_FORMULA | `A-002_FINAL_FORMULA_SPECIFICATION.md` has `FULL_COUNCIL_APPROVED = YES`. |
| N-007 UTC factual windows and Asia/Jerusalem accounting day | APPROVED_POLICY | Catalog says approved as defined / implement allowed. |
| T-009 Daily loss limit threshold | RESEARCH_PARAMETER | Threshold value remains configurable; certification should not choose optimal value. |
| P8 economic time/accounting day | DOCUMENTATION_DEPENDENCY / APPROVED_POLICY | Defines day binding, late posting and replay behavior. |
| Portfolio daily base policy | DOCUMENTATION_DEPENDENCY / APPROVED_POLICY | Required for threshold amount. |
| TT_NUMERIC_V1 | APPROVED_POLICY | Governs exact arithmetic. |

## 20. Worked / Conformance Examples Present

Normative active methodology examples:

- final economic closing execution at `2026-09-11 23:59:59+03:00`, cleanup and
  delivery after midnight, still has `accounting_day_id = 2026-09-11`;
- current-day Daily Loss sums FINAL results bound to the current day;
- late historical result updates only the historical day and not current latch
  or base.

Non-normative demo tests show:

- threshold is inclusive;
- latch persists even after later profit and resets next UTC day in demo code;
- missing safe baseline while enabled blocks new entries;
- demo code ignores test/backtest rows and sums active/exchange closed trades.

These implementation examples are useful only as contrast. They do not replace
the active methodology's Asia/Jerusalem day policy or certified A-002 result
source.

## 21. Source Gaps and Ambiguities

| # | Gap / ambiguity | Impact |
|---:|---|---|
| 1 | Active text states exact threshold formula but does not explicitly define a persisted `daily_loss_used_pct` formula. | Non-blocking if Council treats amount/latch as the certified gate input and diagnostics as derivative. |
| 2 | Output quantum/rounding for `daily_loss_limit_amount` is not explicitly stated. | Council should decide whether exact arithmetic plus exact comparison is sufficient. |
| 3 | Implementation is demo-only and uses UTC day / `closed_at` / stored `net_pnl`, while active methodology requires Asia/Jerusalem `accounting_day_id` and FINAL A-002 result receipts. | Likely implementation nonconformance; should not block formula certification if final spec preserves active methodology. |
| 4 | T-009 value remains a research/configuration parameter. | Non-blocking if final spec avoids optimality claims. |
| 5 | Detailed daily base reconstruction is policy evidence, not fully formula-certified here. | A-009 consumes the fixed base and should fail closed if unavailable. |

## 22. Reviewer Handoff Summary

```text
FORMULA_ID: A-009
FORMULA_NAME: Accounting-day realized totals and daily loss gate input

EXACT_FORMULA_RECONSTRUCTABLE:
YES

DECLARED_TRADING_PURPOSE_RECONSTRUCTABLE:
YES

INPUT_DOMAIN_COMPLETE:
YES_WITH_DAILY_BASE_AND_THRESHOLD_CONFIGURATION_BOUNDARIES

BOUNDARY_BEHAVIOR_COMPLETE:
YES

TIME_SEMANTICS_COMPLETE:
YES

DIRECTION_OR_SIGN_SEMANTICS_COMPLETE:
YES

PARAMETER_PROVENANCE_COMPLETE:
YES_WITH_T009_VALUE_AS_RESEARCH_PARAMETER

STATE_REPLAY_SEMANTICS_COMPLETE:
YES

SOURCE_GAP_COUNT:
5_NON_BLOCKING_OR_COUNCIL_CLASSIFICATION_REQUIRED

READY_FOR_FULL_EXPERT_COUNCIL_REVIEW:
YES

BLOCKING_EXTRACTION_GAPS:
NONE IDENTIFIED BY ORCHESTRATOR
```
