```yaml
formula_id: F-012
review_mode: FULL_REVIEW
FULL_COUNCIL_APPROVED: YES
ANOTHER_REVIEW_CYCLE_REQUIRED: NO
```

Approval covers the Source Pack with the Council-defined semantics below, for
specification correctness and trading fitness in its declared role. All five
permitted files were reviewed; no additional sources were read, agents spawned,
or files modified.

## Eight Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE_WITH_LIMITATIONS | Gross structural R:R and TP-scenario net edge are coherent eligibility filters; neither establishes positive expectancy. |
| Market Microstructure & Order Flow Researcher | APPROVE_WITH_LIMITATIONS | Maker-entry and taker-exit fee assumptions match the declared mechanics. Actual fills, slippage and adverse selection remain unmodeled. |
| Market Regime & Context Analyst | APPROVE_WITH_LIMITATIONS | Frozen, direction-consistent evaluation is appropriate. Threshold effectiveness and stale-price effects remain regime-dependent. |
| Quant Strategy Researcher | APPROVE | Directional geometry, monetary formulas, denominator validation and exact comparisons are consistent under the defined linear contract scope. |
| Risk & Trade Management Architect | APPROVE_WITH_LIMITATIONS | Mandatory prerequisites, independent gates and terminal rejection preserve risk boundaries. Planned SL loss is not a maximum-loss guarantee. |
| Execution & Exchange Mechanics Specialist | APPROVE_WITH_LIMITATIONS | Supplied fee facts and unchanged certified prices preserve ownership. Exchange acceptance, execution and actual fee settlement are excluded. |
| Adversarial Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Definitions below resolve disabled gates, malformed inputs, unsupported costs, undefined ratios and deterministic failure precedence. |
| Performance & Strategy Diagnostics Analyst | APPROVE_WITH_LIMITATIONS | Exact audit values, explicit availability and immutable evidence support reproducible diagnostics. Persistence implementation and empirical effectiveness remain unverified. |

## Blockers

Remaining blockers: NONE for this candidate. The following source deficiencies
are closed by the recorded definitions; the immutable Source Pack itself is not
rewritten.

| Finding | Classification | Disposition |
|---|---|---|
| F012-C01: Ambiguous R:R branching, threshold domain and threshold units | SPECIFICATION_DEFECT | Closed: explicit gate mapping; finite configured thresholds; R:R threshold is dimensionless. |
| F012-C02: Formula outputs versus construction payload; disabled gate versus required economics | SPECIFICATION_DEFECT | Closed: local R:R result, existing external fields, and separate mandatory economics availability. |
| F012-C03: Unenumerated other costs and incomplete SL diagnostics | SPECIFICATION_DEFECT | Closed: fee-only baseline and explicitly non-gating SL diagnostics. |
| F012-C04: Geometry, arithmetic, failure precedence and replay completeness | SPECIFICATION_DEFECT | Closed: definitions and ordered reasons below. |
| F012-C05: F-011 omitted from the historical catalog dependency list | DEPENDENCY_GAP | Closed for this review: F-011 is a mandatory direct dependency, consistent with its certified construction contract. |

## Approved Candidate Semantics

1. Scope and prerequisites - COUNCIL_DEFINED. Candidate: `F-012_COUNCIL_DEFINED_CYCLE_1`. Restrict certification to the inherited linear USDT convention `N = Q * E`, without contract multipliers or currency conversion. Require usable certified F-008 Entry, F-009 Stop, F-010 Dynamic TP and successful F-011 sizing, with matching instrument, direction, cycle, handoff, configuration, grant and metadata bindings. `E`, `SL`, `TP`, `Q`, `N` must be positive finite exact decimals. Preserve LIMIT POST_ONLY entry and MARKET exits. F-012 consumes final values without rerounding, resizing or repairing them.
2. Mathematics and units - COUNCIL_DEFINED completion. Let `s = 1` for LONG and `s = -1` for SHORT; `dr = s*(E-SL)` and `dw = s*(TP-E)`. Require both distances strictly positive before evaluating gates. Then `gross_rr = dw/dr`, distance percentages are `100*dr/E` and `100*dw/E`, `gross_profit_tp = dw*Q`, and `gross_loss_sl = dr*Q`. With fractional fee rates `m,t`: `entry_fee = N*m`, `tp_exit_notional = TP*Q`, `tp_exit_fee = TP*Q*t`, `tp_total_cost = entry_fee + tp_exit_fee`, `net_profit_tp = gross_profit_tp - tp_total_cost`, and `net_edge_pct = 100*net_profit_tp/N`. R:R and its threshold are dimensionless; edge and its threshold use percent units. Neither committed capital nor target notional replaces `N`.
3. Fees and other costs - COUNCIL_DEFINED. A-003's recorded `APPROVED_AS_DEFINED` policy/factual basis is sufficient for this planned calculation; certification of realized attribution is unnecessary for this interface. Require exact finite signed rates and governed provenance, including schedule version, effective time and source reference, applicable to the bound instrument/account fee schedule and mechanics at the frozen construction time. Zero fees and negative rebates require factual support; preserve their signs. No fee refresh, guessed rate or missing-value zero-fill is permitted. The approved baseline contains only entry and TP fees: other costs form an explicitly empty set, whose sum is zero. A claimed applicable additional cost requires a separately approved deterministic definition and reviewed integration; otherwise economics is unavailable. Funding remains excluded.
4. Configuration, gates and outputs - COUNCIL_DEFINED. Enabled flags must be actual booleans. An enabled threshold must be present and an exact finite decimal; no default or additional positive lower bound is inferred. Disabled thresholds are unused. Each validated disabled gate returns `NOT_APPLICABLE`; an enabled evaluable gate returns `PASS` on inclusive equality or superiority, otherwise `FAIL` with its threshold reason. An enabled prerequisite-blocked gate returns `UNAVAILABLE`. Thus zero or negative net edge is valid signed data: its comparison determines the result, including when a configured threshold is nonpositive. F-012 owns local `minimum_rr_result` semantics and audit evidence, plus the existing `economics.gross_rr`; it adds no `minimum_rr` field to construction v5. Preserve the existing `minimum_net_edge` wire result. For rule results, disabled `configured_value` is null; `calculated_value` contains the valid reported ratio when available, otherwise null; PASS/NOT_APPLICABLE reasons are null. Unknown flags cannot be represented as disabled.
5. Required economics versus disabled gates - COUNCIL_DEFINED. The listed successful Order Spec requires numeric planned edge, maker/taker rates and fee provenance even when Minimum Net Edge is disabled. Consequently missing/invalid fees block successful construction while that disabled gate remains `NOT_APPLICABLE`. A valid independent R:R gate may still produce its own result. Both gates being disabled never bypass dependency, geometry, integrity or required-economics checks. Successful F-012 evaluation requires all mandatory checks and every enabled gate to pass; disabled gates remain `NOT_APPLICABLE`. This establishes Position construction eligibility only, not Portfolio authorization.
6. SL diagnostics - COUNCIL_DEFINED. Retain gross SL loss magnitude. Reclassify SL fee/notional and net-R:R extensions as optional local diagnostics, without adding external fields or hard gates: `sl_exit_notional = SL*Q`, `sl_exit_fee = SL*Q*t`, `sl_total_cost = entry_fee + sl_exit_fee`, `net_loss_sl = gross_loss_sl + sl_total_cost`. When `net_loss_sl > 0`, `net_rr = net_profit_tp/net_loss_sl`; otherwise return diagnostic `UNAVAILABLE / NONPOSITIVE_NET_LOSS_SL`, with a null ratio. Never use absolute value, infinity or a fabricated zero to repair it. Diagnostic absence or undefined net R:R does not reject an otherwise valid construction.
7. Precision, replay and ownership - COUNCIL_DEFINED completion. Apply `TT_NUMERIC_V1`: exact decimal parsing and finite monetary products/sums; exact rational division; no intermediate rounding, binary floats or epsilon. Compare `dw >= minimum_rr*dr` and `100*net_profit_tp >= minimum_edge*N` directly. Report ratios with `10^-18 * floor(exact_ratio/10^-18)`, including floor toward negative infinity for negative values. Preserve reduced signed numerator/positive-denominator pairs for exact ratios, alongside canonical reports. Preserve all Source Pack Sections 15-16 identities/pins, the Council candidate identity, dependency values/digests, profile/currency bindings, fee facts/effective time, empty-cost policy, gate configuration, ordered reasons and output bindings. Restart must reproduce values and statuses from frozen evidence; missing evidence, changed content under an identity or inconsistent persisted outputs fails closed. Position owns evaluation; upstream contracts own facts, Portfolio owns authorization, and Lifecycle owns execution and realized cashflows.

## Failure Precedence

| Priority | Condition | Local result / reason |
|---:|---|---|
| 1 | Invalid/missing required identity within supplied evidence; conflicting digest, direction, version, unit, profile or provenance binding | `UNAVAILABLE / IDENTITY_INVALID` |
| 2 | Missing/invalid pinned configuration, invalid enabled flag, or missing/malformed/nonfinite enabled threshold | `UNAVAILABLE / CONFIG_INVALID` |
| 3 | Missing/unusable dependency or missing/malformed/nonfinite/nonpositive required output | `UNAVAILABLE / DEPENDENCY_ENTRY_UNAVAILABLE`, then `DEPENDENCY_STOP_UNAVAILABLE`, then `DEPENDENCY_TP_UNAVAILABLE`, then `DEPENDENCY_SIZING_UNAVAILABLE`; retain upstream reasons |
| 4 | Required arithmetic failure, `N != Q*E`, or inconsistent required exact/report/output invariant | `UNAVAILABLE / NUMERIC_INVARIANT_VIOLATION` |
| 5 | Valid positive Entry and Stop coincide: `dr = 0` | `FAIL / ZERO_RISK_DISTANCE`; R:R is unavailable, never divided |
| 6 | Otherwise `dr < 0` or `dw <= 0` | `FAIL / INVALID_GEOMETRY`; enabled economic gates are unavailable |
| 7 | Required maker/taker fact or required fee provenance is absent/unavailable | `UNAVAILABLE / MISSING_EXCHANGE_FACT`, identifying the fee field |
| 8 | Supplied fee is malformed/nonfinite, has unsupported units, or fails established applicability; binding conflicts already use priority 1 | `UNAVAILABLE / INVALID_EXCHANGE_FACT` |
| 9 | Applicable additional cost lacks the separately approved deterministic definition/integration required above | `UNAVAILABLE / COST_POLICY_UNAVAILABLE` |
| 10 | Evaluable enabled gross R:R comparison fails | `FAIL / RR_BELOW_MINIMUM` |
| 11 | Evaluable enabled net-edge comparison fails | `FAIL / NET_EDGE_BELOW_MINIMUM` |

With no failures, the local result is `PASS / AVAILABLE`. Any overall non-PASS
result prevents successful construction and approved/actionable economics;
available values remain explicitly diagnostic.

## Validation And Limits

Reference arithmetic: LONG `E=100, SL=99, TP=102, Q=2, N=200, m=0.0002,
t=0.0006` gives `gross_rr=2`, entry fee `0.04`, TP fee `0.1224`, TP cost
`0.1624`, net profit `3.8376`, and edge `1.9188%`; thresholds `2` and `1.9188`
both pass. SHORT with `SL=101, TP=98` gives edge `1.9212%`, reflecting the
different TP notional. Exact `2/3` passes threshold `0.6666666666666666665`
although its Q18 report is `0.666666666666666666`.

Preserve conformance cases for all enable combinations, absent/invalid
thresholds, signed/zero fees, zero/negative edge, wrong-side/equal prices,
invalid sizing, simultaneous failures, undefined SL diagnostics, negative
report flooring and restart equality. These are specification checks and future
implementation requirements, not implementation certification.

## Non-Blocking Limitations And Empirical Questions

`NON_BLOCKING_LIMITATION`: A-003 implementation, fee settlement/rounding and
attribution, persistence, execution, Portfolio authorization and realized
accounting remain uncertified. Planned TP edge is a conditional scenario, not
expected return; gross R:R and planned SL economics do not bound realized loss.

`EMPIRICAL_QUESTION`: Validate T-005/T-006 calibration chronologically out of
sample across instruments, directions, regimes and fee schedules, including
rejected, unfilled and partially filled opportunities. Measure execution costs,
funding separately, adverse selection, target-before-stop outcomes and realized
results; candle touches establish neither fills nor exit ordering.

```yaml
final_approval_record: {candidate: F-012_COUNCIL_DEFINED_CYCLE_1, approved_by: FULL_COUNCIL, date: 2026-09-15, remaining_blockers: NONE}
source_pack_sha256: a9eb48c0204b033b9441261b049ef2d99fbd6d456feeb55fa62a5974a1c9ddc1
```
