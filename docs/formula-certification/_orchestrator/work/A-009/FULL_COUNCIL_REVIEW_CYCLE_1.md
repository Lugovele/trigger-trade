# FULL_COUNCIL_REVIEW_CYCLE_1

Formula: A-009 - Accounting-day realized totals and daily loss gate input
Mode: FULL_REVIEW
Date: 2026-09-15
Council model: FULL_COUNCIL

## Council Record

A-009 is approved for its declared accounting and new-exposure gate role.
Exact arithmetic and exact comparison are sufficient. The reported demo
implementation mismatch does not expose a specification defect.

```text
formula_id: A-009
review_mode: FULL_REVIEW
review_structure: ALL_EIGHT_PERSPECTIVES_APPLIED_IN_ONE_COUNCIL
specification_verdict: APPROVED
dependency_compatibility: PASS_AT_SUPPLIED_CONTRACT_BOUNDARIES
blocking_findings: NONE
full_council_approved: YES
another_review_cycle_required: NO
```

Evidence reviewed:

- `docs/formula-certification/A-009/A-009_SOURCE_PACK.md`, sections 3-21
- `docs/formula-certification/A-002/A-002_FINAL_FORMULA_SPECIFICATION.md`, especially sections 5-18

Only these files were read. No subagents, edits, tests or trading actions were
performed by the Council.

## Eight Role Verdicts

| Perspective | Verdict | Council assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE | Appropriate for stopping additional exposure after an observed realized-loss breach. Existing exposure and previously authorized entries can still produce losses; this is not a guaranteed daily loss ceiling. |
| Market Microstructure & Order Flow Researcher | APPROVE | FINAL execution-derived A-002 results provide the correct declared input, including supported fees, rebates, funding and costs. Attribution and finality delays limit how quickly the gate sees economic losses. |
| Market Regime & Context Analyst | APPROVE | A fixed accounting-day control is coherent across regimes without claiming to measure regime conditions. Effectiveness across volatility, liquidity and holding-period regimes remains empirical. |
| Quant Strategy Researcher | APPROVE | Signed aggregation, percentage scaling, inclusive comparison and persistent latch are mathematically consistent. No threshold quantization is required. |
| Risk & Trade Management Architect | APPROVE | Portfolio ownership, fixed daily base, fail-closed prerequisites and atomic authorization checks support the declared protection. The gate creates no forced-exit authority. |
| Execution & Exchange Mechanics Specialist | APPROVE | Final economic closing time, immutable day binding, dual-identity receipt checks and historical posting agree with A-002. Actual crash consistency and exchange conformance remain implementation obligations. |
| Adversarial Strategy Reviewer | APPROVE | Identical replay cannot add money twice; conflicting identities cannot overwrite frozen results; subsequent gains cannot clear a latch. Display rounding and receipt-time reassignment are prohibited. |
| Performance & Strategy Diagnostics Analyst | APPROVE | Amounts, latch, accounting policy and provenance support diagnosis. Final daily totals alone cannot explain every historical gate decision; receipt timing and latch history matter. |

## Finding Classification

| Classification | Finding and disposition |
|---|---|
| SPECIFICATION_DEFECT | None identified within the declared role and supplied evidence. |
| DEPENDENCY_GAP | None blocking. A-002 compatibility is directly supported. N-007/P8 and numeric-policy compatibility are accepted as carried in the Source Pack. Detailed daily-base construction remains an approved external contract, not independently certified here. |
| PRODUCT_DECISION | Asia/Jerusalem midnight, fixed daily base, net realized aggregation and protection limited to new exposure are accepted policy choices. Portfolio configuration owns enablement and the T-009 value; this Council selects neither. |
| EMPIRICAL_QUESTION | T-009 calibration, risk reduction, missed opportunities and sensitivity to finality latency require evaluation. Formula approval makes no optimality or profitability claim. |
| NON_BLOCKING_LIMITATION | No output quantum is specified for `daily_loss_limit_amount`. Resolved: preserve the exact value and comparison; do not introduce rounding. |
| NON_BLOCKING_LIMITATION | The Source Pack reports a demo path using UTC day, `closed_at` and stored `net_pnl`. This is implementation nonconformance, not conflicting normative authority. Formula approval does not certify that implementation. |
| NON_BLOCKING_LIMITATION | No persisted `daily_loss_used_pct` definition is supplied. The certified gate requires amounts and latch state; an additional percentage metric is unnecessary for certification. |
| NON_BLOCKING_LIMITATION | FINAL-result timing, whole-tranche accounting, unrealized losses, pre-latch profit offsets and existing order fills limit protection. These limits must remain explicit. |

## Semantics For Final Specification

1. Ownership and scope. Lifecycle produces the immutable FINAL A-002 result.
   Portfolio receives it, owns daily totals/base/latch, and supplies gate
   evidence for new Coin OPEN and new grants/holds. Portfolio does not
   recompute A-002 components. Passing this gate does not replace other risk
   or execution authorization requirements.
2. Eligible inputs. Include only FINAL logical results with COMPLETE evidence,
   valid `result_id` and `tranche_id`, the governed currency, and a valid
   immutable accounting day consistent with the pinned policy. Preserve A-002
   signs and component precision. Do not add native/API aggregate P&L, wallet
   movements, fees or funding again.
3. Accounting time. `ACCOUNTING_DAY_V1` means `Asia/Jerusalem`, local
   midnight, interval `[local 00:00, next local 00:00)`. The exact boundary
   belongs to the following day. Compute successive local boundaries under the
   named timezone, without assuming every interval is 24 elapsed hours. Use the
   execution that permanently reduced the tranche to zero; delivery, receipt,
   cleanup and finalization timestamps cannot substitute.
4. Daily total. For day `d`, `R_d = sum(net_realized_result)` over its
   eligible, uniquely posted results. Positive values are gains; negative
   values are losses. A genuinely empty eligible set sums to zero; missing
   receipt or recovery state must not be represented as an empty set.
   Non-FINAL and incomplete results are excluded without provisional posting.
5. Threshold and usage. `L_d = daily_portfolio_base * daily_loss_limit_pct /
   100`; `daily_loss_used_amount = max(-R_d, 0)`. Monetary inputs share the
   governed currency. The base must come from authoritative boundary evidence
   or complete deterministic reconstruction and remain fixed for that day. An
   enabled threshold must be present, valid and positive. No fallback base,
   threshold, extra percentage ceiling or calibration value is introduced.
6. Gate decision. When disabled, this gate supplies no blocking and requires no
   base/final-result evidence for that decision. When enabled, an existing
   current-day latch blocks new exposure. Otherwise, valid current-day state
   trips the gate exactly when `R_d <= -L_d`, including equality. Missing
   required day/base/configuration or unresolved critical recovery state yields
   unavailable/fail-closed behavior, never fabricated `OK`.
7. Latch semantics. A qualifying breach sets the durable day latch. Positive
   results offset losses before latching; subsequent profit does not clear an
   existing latch. The latch resets only at accounting-day rollover. Disabling
   bypasses this gate without implying latch deletion; re-enabling during the
   same day encounters the retained latch. Configuration changes cannot erase
   it.
8. Rollover and historical posting. Rollover establishes the next
   policy-defined day, its base and its current-day latch state. A first valid
   late historical result posts once to its immutable historical day. It does
   not enter today's total, change today's base or latch, or add wallet capital
   again. Historical posting cannot silently rewrite an already posted FINAL
   result.
9. Identity and integrity. Enforce once-only receipt under both result and
   tranche identity. Identical replay is a no-op, including zero-valued
   results. A changed payload under an existing identity, or another final
   result identity for an already posted tranche, is an integrity conflict.
   Preserve frozen values and follow the inherited integrity/fence protocol.
10. Persistence and authorization. Restore day records/boundaries, base, latch,
    receipt ledger, totals, terminal-release state, commitment buckets and
    unresolved incidents/native observations before processing events. Posting,
    deduplication and latch effects must survive crashes consistently. Atomic
    hold/authorization must consult current Daily Loss state. Rebuilding a
    final aggregate alone cannot recover whether the day previously latched.
11. Traceability and outputs. Retain accounting-policy and rules versions,
    boundary/base evidence, included result/tranche identities, receipt state
    and evaluation time. Report the daily total, exact threshold, durable latch
    and applicable `DISABLED`, `OK`, `LIMIT_REACHED`, `LATCHED` or
    unavailable/fail-closed status. A disabled gate does not waive accounting
    receipt integrity.

## Precision Decision

`daily_loss_limit_amount` is an exact comparison threshold, not an exchange
order quantity or a newly quantized cash posting. Finite decimal multiplication
and division by 100 can retain their exact digits; exact rational
representation also suffices. An equivalent comparison is:

```text
100 * R_d <= -(daily_portfolio_base * daily_loss_limit_pct)
```

Arbitrary decimal context, binary floating point, epsilon and presentation
rounding must not affect either expression.

For example, base `100.01` and threshold `1%` produce exactly `1.0001`:
`R_d = -1.00` does not trip; `R_d = -1.0001` does. Rounding the threshold to
cents changes the rule. Preserve the signed predicate: if the upstream base
policy admits a zero base, it trips at `R_d <= 0`; substituting
`daily_loss_used_amount >= L_d` would incorrectly trip even with positive
realized P&L.

## Trading Fitness

The entire FINAL tranche result belongs to its final economic closing day,
potentially incorporating economics accumulated across earlier days.
Consequently, this total is not daily wallet cashflow, intraday equity
drawdown, gross losing-trade totals or current open risk. Pending finality and
late historical delivery can leave losses outside today's gate input. Existing
entries may still fill after latching, and existing exposure retains its
independent management and protection.

Empirical evaluation should measure finality/receipt latency, losses absent
from the gate when exposure was authorized, losses incurred after latching,
blocked opportunities, and results across regimes and candidate T-009 values.
Diagnostics should distinguish the latest historical total from the state
available at each authorization and preserve latch history. These requirements
support operational validation and threshold research; they do not change the
certified formula or authorize implementation promotion or live trading.
