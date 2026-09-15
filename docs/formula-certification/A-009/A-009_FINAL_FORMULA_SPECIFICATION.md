# FINAL_FORMULA_SPECIFICATION

# A-009 - Accounting-day realized totals and daily loss gate input

**Artifact:** `A-009_FINAL_FORMULA_SPECIFICATION.md`
**Specification status:** `FINAL_APPROVED`
**Review:** Full Expert Council Review - Cycle 1
**Review date:** 2026-09-15

## 1. Identity

| Field | Approved value |
|---|---|
| Formula ID | A-009 |
| Name | Accounting-day realized totals and daily loss gate input |
| Owner | Accounting / Portfolio Rules |
| Formula family | DRAWDOWN |
| Type | ACCOUNTING_FORMULA |
| Methodology baseline | v1.2.14 |
| Source Pack | `A-009_SOURCE_PACK.md` |
| Final approval cycle | 1 |

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = YES
SPECIFICATION_STATUS = FINAL_APPROVED
TRADING_FITNESS = APPROVED_AS_ACCOUNTING_DAY_NEW_EXPOSURE_GATE_INPUT
BLOCKING_FINDINGS_REMAINING = NONE
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
EMPIRICAL_EFFECTIVENESS = T009_CALIBRATION_REQUIRED
LIVE_DEPLOYMENT_SAFETY = NOT_CERTIFIED_BY_THIS_REVIEW
```

Approval certifies A-009 for its declared accounting and new-exposure gate
role. It does not certify backend implementation, venue conformance,
configuration optimality, deployment, paper/live execution, or any forced-exit
behavior.

## 3. Intended Purpose

A-009 defines the Portfolio-owned realized accounting-day total used as the
input to the Daily Loss gate for new exposure.

If the gate is enabled and the current accounting day's realized losses reach
the configured threshold, Portfolio blocks new Coin OPEN and new grants/holds.
The gate never force-closes existing exposure, cancels existing
entries/protection, or creates a funding/time-based exit.

## 4. Actual Construct

A-009 aggregates certified FINAL A-002 logical net results by immutable
Portfolio accounting day, computes the exact Daily Loss threshold amount from
the fixed daily base and configured threshold, and derives the current-day gate
state and durable latch.

It is not a wallet cashflow metric, intraday equity drawdown, gross
losing-trade metric, unrealized P&L measure, or current open-risk estimate.

## 5. Exact Formula / Rule

For accounting day `d`:

```text
R_d = sum(net_realized_result_i)
      for each eligible FINAL logical result i
      with accounting_day_id_i = d
      posted exactly once under result_id and tranche_id

L_d = daily_portfolio_base_d * daily_loss_limit_pct / 100

daily_loss_used_amount_d = max(-R_d, 0)
```

Gate rule:

```text
if daily_loss_limit_enabled is false:
    daily_loss_status = DISABLED
    daily_loss_blocks_new_exposure = false

else if current_day_latch is already set:
    daily_loss_status = LATCHED
    daily_loss_blocks_new_exposure = true

else if required day/base/configuration/recovery state is unavailable:
    daily_loss_status = UNAVAILABLE_OR_FAIL_CLOSED
    daily_loss_blocks_new_exposure = true

else if R_current_day <= -L_current_day:
    latch DAILY_LOSS_LIMIT_REACHED for the current accounting day
    daily_loss_status = LIMIT_REACHED or LATCHED
    daily_loss_blocks_new_exposure = true

else:
    daily_loss_status = OK
    daily_loss_blocks_new_exposure = false
```

Equivalent exact comparison:

```text
100 * R_current_day <= -(daily_portfolio_base_current_day * daily_loss_limit_pct)
```

## 6. Inputs

| Input | Requirement |
|---|---|
| `accounting_day_id` | Immutable Portfolio accounting day under `ACCOUNTING_DAY_V1`. |
| `accounting_day_interval` | Half-open `Asia/Jerusalem` local-midnight interval `[local 00:00, next local 00:00)`. |
| FINAL A-002 result set | Eligible, uniquely posted final logical results with COMPLETE evidence. |
| `net_realized_result` | Certified A-002 signed final net result in governed currency. |
| `result_id` and `tranche_id` | Dual identity used for exactly-once posting and replay safety. |
| `accounting_effective_at` | Final economic closing execution timestamp that permanently reduced the tranche to zero. |
| `accounting_policy` | `Asia/Jerusalem`, `00:00:00`, `ACCOUNTING_DAY_V1`. |
| `daily_portfolio_base` | Fixed current-day base from authoritative boundary evidence or complete deterministic reconstruction. |
| `daily_loss_limit_pct` | Enabled gate's configured positive threshold value. |
| `daily_loss_limit_enabled` | Portfolio configuration flag. |
| Existing latch/receipt/day state | Restored durable state needed before processing events or authorizing exposure. |

## 7. Outputs

| Output | Requirement |
|---|---|
| `daily_realized_pnl[accounting_day_id]` / `R_d` | Exact sum of eligible FINAL A-002 net results posted to the immutable day. |
| `daily_loss_limit_amount` / `L_d` | Exact threshold amount, not rounded for decision. |
| `daily_loss_used_amount` | `max(-R_d, 0)`. |
| `daily_loss_status` | `DISABLED`, `OK`, `LIMIT_REACHED`, `LATCHED`, or unavailable/fail-closed status. |
| `daily_loss_latch` | Durable current-day latch when threshold is reached. |
| Gate evidence | Blocking/permission evidence for new Coin OPEN and new grants/holds. |

## 8. Units

`R_d`, `daily_portfolio_base`, `L_d`, `daily_loss_used_amount` and all included
A-002 results use the governed Portfolio accounting currency.

No cross-currency aggregation, FX conversion, currency relabeling, or
cancellation between incompatible currencies is authorized.

## 9. Parameters

| Identifier | Certification treatment |
|---|---|
| `daily_loss_limit_enabled` | Portfolio configuration parameter. |
| `daily_loss_limit_pct` / T-009 | Configurable research parameter; certification defines its use, not its optimal value. |
| `ACCOUNTING_DAY_V1` | Approved policy: `Asia/Jerusalem`, local midnight, half-open interval. |

No additional fallback threshold, percentage ceiling, calibration value, or
empirical optimality claim is introduced.

## 10. Domain / Preconditions

Before A-009 can produce an enabled current-day gate decision:

1. The current accounting day and exact boundary instants are known under
   `ACCOUNTING_DAY_V1`.
2. The day's `daily_portfolio_base` is fixed from authoritative boundary
   evidence or complete deterministic reconstruction.
3. `daily_loss_limit_pct` is present, valid and positive.
4. Day records, boundary evidence, receipt ledger, current latch/base,
   commitment buckets and unresolved critical incidents are restored.
5. Every included result is a FINAL A-002 logical result with COMPLETE
   evidence, governed currency, valid accounting day, `result_id` and
   `tranche_id`.
6. Each result is posted at most once under both result and tranche identity.

When disabled, A-009 supplies no blocking and requires no base/final-result
evidence for that decision. Disabled status does not waive receipt-integrity
rules for accounting records.

## 11. Missing / Invalid Behavior

| Case | Required behavior |
|---|---|
| Daily Loss disabled | No Daily Loss blocking. |
| Missing or invalid threshold while enabled | Fail closed for new exposure. |
| Missing current-day base while enabled | Fail closed for new exposure. |
| Missing or unresolved accounting day while enabled | Fail closed for new exposure. |
| Unresolved critical recovery state | Fail closed; do not fabricate `OK`. |
| Non-FINAL or incomplete logical result | Exclude; no provisional posting. |
| Genuinely empty eligible final-result set with recovered receipt/day state | Sum is zero. |
| Missing receipt or recovery state | Must not be represented as an empty set. |
| Duplicate identical result receipt | No-op; no second monetary effect. |
| Conflicting result under existing `result_id` or `tranche_id` | Integrity conflict; do not rewrite totals. |
| Late historical result | Post once to immutable historical day only. |
| Native/API aggregate P&L row | Cannot substitute for logical result or be double-added. |
| Cross-currency result | Inadmissible until upstream finality/currency is resolved; no conversion. |

## 12. Boundaries

A-009 does not define:

- A-002 net final result internals;
- daily base construction beyond consuming the fixed Portfolio base;
- the optimal T-009 threshold value;
- entry or exit signals;
- forced liquidation;
- current wallet equity;
- unrealized P&L;
- research drawdown metrics such as M-004;
- backend implementation details.

Passing A-009 does not replace other risk, capacity, cooldown, symbol-scope,
grant, hold or execution authorization requirements.

## 13. Precision / Rounding

`daily_loss_limit_amount` is an exact comparison threshold, not an exchange
order quantity or newly quantized cash posting. No output quantum is required
for the decision.

Finite decimal multiplication and division by 100 may retain exact digits;
exact rational representation is also acceptable. Arbitrary decimal context,
binary floating point, epsilon comparison, presentation rounding or report
formatting must not affect the gate.

Example:

```text
daily_portfolio_base = 100.01
daily_loss_limit_pct = 1
L_d = 1.0001

R_d = -1.00   -> does not trip
R_d = -1.0001 -> trips
```

Rounding `L_d` to cents changes the rule and is prohibited for the decision.
Preserve the signed predicate. Substituting `daily_loss_used_amount >= L_d`
would incorrectly trip on positive realized P&L if an upstream base policy ever
admitted zero base.

## 14. Time Semantics

`ACCOUNTING_DAY_V1` means:

```text
accounting_timezone = Asia/Jerusalem
day_boundary_local = 00:00:00
accounting_day_interval = [local 00:00, next local 00:00)
```

The exact boundary instant belongs to the following day. Compute successive
local boundaries under the named timezone; do not assume every interval is 24
elapsed hours.

`accounting_effective_at` is the final economic closing execution that
permanently reduced the logical tranche to zero. Delivery, receipt, cleanup,
callback and finalization timestamps cannot substitute.

A first valid late historical result posts once to its immutable historical
day. It does not enter today's total, change today's base or latch, or add
wallet capital again.

## 15. State / Replay / Restart

Portfolio persists:

- accounting-day records and boundary instants;
- fixed daily base;
- current-day latch state;
- result receipt ledger keyed by result ID and tranche ID;
- day totals;
- terminal-release state;
- commitment buckets;
- unresolved incidents/native observations.

Restart restores this state before processing events or authorizing exposure.
Identical replay is a no-op, including zero-valued results. A changed payload
under an existing identity, or another final result identity for an already
posted tranche, is an integrity conflict.

Rebuilding a final aggregate alone is insufficient to recover whether the day
previously latched; latch history is durable state.

## 16. Configuration Pinning

A gate evaluation carries:

- accounting policy version `ACCOUNTING_DAY_V1`;
- rules version with `daily_loss_limit_enabled` and `daily_loss_limit_pct`;
- day boundary/base evidence;
- included result IDs and tranche IDs;
- receipt ledger state;
- evaluation time;
- current latch state.

Configuration changes cannot erase an existing current-day latch. Disabling
bypasses the gate while disabled but does not imply latch deletion; re-enabling
during the same day encounters the retained latch.

## 17. Dependencies

| Dependency | Role | Certification treatment |
|---|---|---|
| A-002 Net final result calculation | Supplies signed FINAL logical results. | `CERTIFIED_FORMULA`; final spec approved. |
| N-007 / P8 accounting day | Defines `Asia/Jerusalem` day, final economic time and late posting. | Approved policy/documentation dependency accepted at supplied boundary. |
| T-009 Daily loss limit threshold | Supplies configurable threshold value. | Research/configuration parameter; value not certified as optimal. |
| Portfolio daily base policy | Supplies fixed daily base. | Approved external contract; unavailable base fails closed. |
| TT_NUMERIC_V1 | Governs exact arithmetic. | Approved policy. |

## 18. Ownership

Portfolio Rules owns Daily Loss, daily base, accounting-day records, receipts,
latch and gate decisions.

Lifecycle owns A-002 final logical financial result production. API supplies
wallet/native facts for capital and factual evidence only. API does not decide
eligibility, create grants, or produce logical-tranche accounting. Position
does not own Daily Loss.

## 19. Pipeline Role

A-009 operates after Lifecycle has produced and Portfolio has received FINAL
A-002 results. It feeds the Portfolio atomic authorization path for new Coin
OPEN and new grants/holds.

```text
A-002 FINAL logical result -> Portfolio receipt ledger -> A-009 daily total/latch -> Portfolio new-exposure gate
```

## 20. Approved Uses

- Accounting-day realized P&L total for the declared Portfolio day.
- Daily Loss threshold comparison and current-day latch.
- New-exposure gate evidence for Portfolio authorization.
- Diagnostics of realized daily loss, threshold, latch and evidence.

## 21. Prohibited Interpretations

A-009 must not be interpreted as:

- a guaranteed daily loss ceiling;
- a forced-exit authority;
- an entry/exit signal;
- current open-risk measurement;
- unrealized P&L measurement;
- native wallet P&L formula;
- gross losing-trade total;
- cash-period P&L metric;
- permission to use UTC day, `closed_at`, receipt time or finalization time in
  place of `ACCOUNTING_DAY_V1`;
- implementation or live-deployment approval.

## 22. Known Limitations

- FINAL-result timing and late delivery can leave losses outside the gate input
  at the time new exposure is authorized.
- The entire FINAL tranche result belongs to its final economic closing day,
  even if economics accumulated across earlier days.
- Positive results offset losses before latching; after latching, later gains
  do not clear the latch.
- Existing exposure and previously authorized entries can still lose money
  after the latch.
- Demo implementation using UTC day, `closed_at` and stored `net_pnl` is not
  certified by this specification.
- Daily base construction is consumed as an approved external contract, not
  independently certified here.

## 23. Research Parameters

T-009 `daily_loss_limit_pct` remains a research/configuration parameter.
Certification defines how the threshold is used and compared; it does not
select or optimize the value.

## 24. Empirical Validation Requirements

Empirical and operational validation should measure:

- finality and receipt latency;
- losses absent from the gate when exposure was authorized;
- losses incurred after latching;
- blocked opportunities;
- sensitivity across candidate T-009 values;
- regime-specific outcomes;
- restart/replay/latch persistence behavior;
- difference between latest historical total and state available at each
  authorization.

These requirements support threshold research and operational validation; they
do not alter the certified formula.

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

formula_id: A-009
formula_name: Accounting-day realized totals and daily loss gate input

senior_intraday_crypto_trader: APPROVE
microstructure_order_flow_researcher: APPROVE
market_regime_context_analyst: APPROVE
quant_strategy_researcher: APPROVE
risk_trade_management_architect: APPROVE
execution_exchange_mechanics_specialist: APPROVE
adversarial_strategy_reviewer: APPROVE
performance_strategy_diagnostics_analyst: APPROVE

specification_status: FINAL_APPROVED
trading_fitness_status: APPROVED_AS_ACCOUNTING_DAY_NEW_EXPOSURE_GATE_INPUT

dependency_compatibility: PASS_AT_SUPPLIED_CONTRACT_BOUNDARIES
certified_A002_compatibility: PASS
N007_P8_accounting_day_compatibility: PASS
precision_decision: EXACT_ARITHMETIC_AND_EXACT_COMPARISON_NO_THRESHOLD_ROUNDING

blocking_findings: NONE
known_limitations:
- finality and receipt latency can delay gate visibility
- no guaranteed daily loss ceiling
- existing exposure and previously authorized entries can still lose money
- demo UTC-day implementation is not certified
empirical_questions:
- T-009 calibration and risk-reduction effectiveness
- blocked-opportunity and post-latch loss behavior
- regime and finality-latency sensitivity

full_council_approved: YES
another_review_cycle_required: NO
```
