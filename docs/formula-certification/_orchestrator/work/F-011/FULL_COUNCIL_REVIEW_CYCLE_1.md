```yaml
formula_id: F-011
review_mode: FULL_REVIEW
FULL_COUNCIL_APPROVED: YES
ANOTHER_REVIEW_CYCLE_REQUIRED: NO
```

Approval applies to `F-011_COUNCIL_DEFINED_CYCLE_1`, comprising the Source Pack
plus the definitions below. Only the four authorized files were read; no files
were modified or additional agents spawned.

## Eight Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE_WITH_LIMITATIONS | Coherent conversion of granted capital into size. It does not size risk from stop distance or establish profitability. |
| Market Microstructure & Order Flow Researcher | APPROVE_WITH_LIMITATIONS | Quantity flooring respects the supplied grid. Venue minima and maxima establish neither liquidity nor fill probability. |
| Market Regime & Context Analyst | APPROVE_WITH_LIMITATIONS | Direction-neutral arithmetic and frozen inputs are appropriate. Regime sensitivity remains with grant/leverage calibration and downstream risk. |
| Quant Strategy Researcher | APPROVE | Exact construction, inclusive limits and liability ceiling are mathematically consistent under the specified input domain. |
| Risk & Trade Management Architect | APPROVE_WITH_LIMITATIONS | Both capital bounds are enforced; failures cannot trigger resizing. Committed capital is not a maximum-loss guarantee. |
| Execution & Exchange Mechanics Specialist | APPROVE_WITH_LIMITATIONS | Fact applicability, quantity grid and maximum-status behavior are sufficiently defined below. Native acceptance remains outside certification. |
| Adversarial Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Explicit rejection, alias conflict handling, dependency binding and defensive arithmetic checks close the identified ambiguities. |
| Performance & Strategy Diagnostics Analyst | APPROVE_WITH_LIMITATIONS | Exact audit values and deterministic failure precedence support replay and analysis; persistence implementation remains unverified. |

## Blockers

No unresolved blockers remain after adopting these Council definitions.

| Finding | Classification | Disposition |
|---|---|---|
| F011-C01: `min_qty` versus `min_order_qty` ambiguity | SPECIFICATION_DEFECT | Closed by canonical alias and conflict rules below. |
| F011-C02: incomplete failure mapping and precedence | SPECIFICATION_DEFECT | Closed by the ordered failure table below. |
| F011-C03: exact quotient, persisted liability and rational replay ambiguity | SPECIFICATION_DEFECT | Closed by exact arithmetic, scalar binding and lossless audit representation below. |
| F011-C04: maximum-status applicability and inconsistent venue facts | SPECIFICATION_DEFECT | Closed by explicit status predicates below. |
| F011-L01: no separately certified F-014/F-015 final specifications supplied | NON_BLOCKING_LIMITATION | Their declared `APPROVED_POLICY` evidence suffices for these consumed interfaces; upstream calculation and approval provenance are not independently certified. |
| F011-P01: additional leverage step/precision restrictions unspecified | PRODUCT_DECISION | Non-blocking for this arithmetic role; no new restriction is invented or native leverage acceptance inferred. |
| F011-E01: grant/leverage effectiveness and realized outcomes unvalidated | EMPIRICAL_QUESTION | Retained for empirical validation. |

## Approved Candidate Semantics

1. Scope and bindings - COUNCIL_DEFINED. Require initial Position approval, a matching Portfolio grant, pinned configuration and AVAILABLE/usable certified F-008/F-009/F-010 outputs. Preserve instrument, direction, cycle, handoff, grant, configuration and metadata bindings. Consume F-008's identical planned Entry/LIMIT price unchanged; retain LIMIT POST_ONLY. F-009 Stop and F-010 TP are construction prerequisites, not sizing operands. LONG maps to BUY and SHORT to SELL. This approval covers the declared linear USDT quantity convention where `quantity * Entry` is notional; it introduces no contract multiplier or currency conversion.
2. Input domain and aliases - COUNCIL_DEFINED. `C`, `L`, `E`, `q`, minimum quantity, minimum notional and venue maximum leverage must be positive finite exact decimal values with required provenance. Require `C / Qcapital` integral and `L <= venue_max_leverage`; reject an unaligned grant without rounding it. `min_qty` means the same venue minimum as canonical contract field `min_order_qty`, not another configurable threshold. The required contract field remains `min_order_qty`; conflicting supplied aliases or inconsistent units/provenance reject. Do not round min/max thresholds to the quantity grid. Beyond finite decimal representation, `L > 0` and the supplied maximum, this specification adds no integer, step, precision or `L >= 1` restriction.
3. Maximum facts - COUNCIL_DEFINED. `AVAILABLE` requires a positive exact `max_order_qty`, applicable provenance and `max_order_qty >= min_order_qty`. `UNAVAILABLE` always prevents usable construction, even if a stale numeric maximum accompanies it. `NOT_APPLICABLE` requires a null maximum and affirmative evidence from the pinned profile that no maximum applies; missing evidence cannot establish non-applicability. For the declared Bybit linear LIMIT POST_ONLY profile, require the applicable `lotSizeFilter.maxOrderQty` fact. Unknown statuses, contradictory facts and unsupported non-applicability reject. Facts come through Capital and Limits; Position performs no API refresh.
4. Construction and proof. With `p = Qcapital = 0.000000000001`, compute exactly: `T=C*L`, `R=T/E`, `Q=q*floor(R/q)`, `N=Q*E`, `A=N/L`, `H=p*ceil(A/p)`. Require `Q>0`, integral `Q/q`, correct flooring, all defining equalities, `Q>=min_order_qty`, applicable `Q<=max_order_qty`, `N>=min_notional`, `A<=C` and `H<=C` independently. Equality passes every inclusive boundary. Flooring proves `A<=C`; since `C/p` is integral, it also proves `H<=C`. Thus capital-bound failures are defensive integrity failures for valid inputs, not ordinary rounding outcomes. Keep both checks. No failed gate permits clamping, splitting, resizing, changing leverage, or revising any price or grant.
5. Precision and output binding - COUNCIL_DEFINED. `T`, `Q` and `N` always terminate as decimals because their operands are finite decimals and the quantity multiplier is integral; serialize their complete exact values. `R` and `A` can recur: preserve each audit value as a reduced integer numerator/positive-denominator pair, encoded as strings, without changing external scalar contracts. `margin_required=A` exactly under this formula; the persisted accounting liability is `H`, with `0<=H-A<p`. Order Spec `economics.actual_committed_capital` and confirmation `approved_actual_committed_capital` both equal `H`; quantity, leverage and actual-notional confirmations equal `Q`, `L`, `N` respectively. No approximate-equality gate, floating-point arithmetic, intermediate rounding or display-derived decision is allowed. `C-H` is informational unused capacity, not authority to release or regrant capital.
6. Replay and ownership - COUNCIL_DEFINED. Preserve all Source Pack Section 15 evidence, explicitly including exact `L`, the candidate identity, original input digests, rational audit values, gate outcomes and ordered reasons. Identical evidence must reproduce identical numerical outputs and primary rejection. Changed content under an existing identity, missing required replay evidence or inconsistent persisted outputs fails closed. Replay creates no new approval, grant or resized spec. F-011 success supplies usable sizing; final geometry/economics, Portfolio hold authorization and Lifecycle execution remain separate mandatory owners and gates.

## Failure Mapping

All mappings and precedence below are COUNCIL_DEFINED, retaining the three
existing minimum/maximum reason names. Table order determines the primary
reason; preserve all determinable secondary failures in that order, using
ordinal field-name order for ties. Absent dependency objects use their
dependency reason; inconsistent supplied bindings use `IDENTITY_INVALID`. A
prerequisite-blocked gate is `UNAVAILABLE`, never `PASS`; only a proven
inapplicable maximum subcheck is `NOT_APPLICABLE`. Every non-PASS construction
exposes no approved/actionable sizing.

| Condition, in precedence order | Result / reason |
|---|---|
| Invalid initial-approval binding; inconsistent supplied identity, digest, provenance, direction, currency/unit/profile or required version | `UNAVAILABLE / IDENTITY_INVALID` |
| Missing or invalid pinned configuration envelope | `UNAVAILABLE / CONFIG_INVALID` |
| Missing grant or missing/malformed/nonfinite/nonpositive/Qcapital-unaligned `C` | `UNAVAILABLE / INVALID_CAPITAL_GRANT` |
| Missing/unusable F-008 Entry, F-009 Stop or F-010 TP; invalid respective price | `UNAVAILABLE / DEPENDENCY_ENTRY_UNAVAILABLE`, then `DEPENDENCY_STOP_UNAVAILABLE`, then `DEPENDENCY_TP_UNAVAILABLE`; preserve upstream reasons |
| Missing/malformed/nonfinite/nonpositive configured `L` | `FAIL / INVALID_LEVERAGE` |
| Missing required venue fact, status or provenance, accounting for the maximum-status rules | `UNAVAILABLE / MISSING_EXCHANGE_FACT` |
| Malformed/nonfinite/nonpositive required venue value; alias conflict; inconsistent min/max; unknown status or unsupported `NOT_APPLICABLE` | `UNAVAILABLE / INVALID_EXCHANGE_FACT` |
| `max_order_qty_status = UNAVAILABLE` | `UNAVAILABLE / MAX_ORDER_QTY_UNAVAILABLE` |
| `L >` valid `venue_max_leverage` | `FAIL / LEVERAGE_ABOVE_MAXIMUM` |
| Arithmetic failure or inconsistent floor/grid/product/ceiling/serialized-output invariant, excluding the separately checked capital bounds | `UNAVAILABLE / NUMERIC_INVARIANT_VIOLATION` |
| `A > C` or `H > C` | `FAIL / CAPITAL_BOUND_VIOLATION`; retain separate exact/persisted check results |
| Correctly floored `Q = 0` | `FAIL / QTY_ZERO_AFTER_FLOOR` |
| Positive `Q < min_order_qty` | `FAIL / QTY_BELOW_MINIMUM` |
| `AVAILABLE` maximum and `Q > max_order_qty` | `FAIL / QTY_ABOVE_MAXIMUM` |
| `N < min_notional` | `FAIL / NOTIONAL_BELOW_MINIMUM` |
| All required prerequisites, invariants and gates pass | `PASS / AVAILABLE` |

## Final Approval Record

```yaml
approved_by: FULL_COUNCIL
candidate: F-011_COUNCIL_DEFINED_CYCLE_1
date: 2026-09-15
trading_fitness: ADEQUATE_FOR_DECLARED_ROLE_WITH_LIMITATIONS
remaining_blockers: NONE
source_pack_sha256: 404f9ad11315a17cb55b5424a74fbf19b473168335e5eb5ca4dadcf6242be267
preserve:
  - baseline v1.2.14
  - TT_NUMERIC_V1
  - Capital and Limits v5
  - Order Spec v5
  - Approve/Reject v5
  - supplied F-008, F-009 and F-010 dependency identities
revised_review_cycle_required: NO
```

## Validation And Limits

Exact-integer arithmetic checked this complete example: `C=67.34`, `L=3`,
`E=101`, `q=1`, minimum quantity `1`, AVAILABLE maximum `2`, minimum notional
`202`, venue maximum leverage `3`. It yields `T=202.02`, `R=10101/5050`, `Q=2`,
`N=202`, `A=202/3`, `H=67.333333333334`, unused capacity `0.006666666666`; all
gates pass.

Future conformance verification must cover zero flooring, inclusive boundaries,
each rejection path, conflicting aliases/statuses, unaligned grants, defensive
bound violations, recurring quotients and restart equality. No implementation
tests were performed.

Preserve empirical evaluation across instruments, directions, regimes,
grant/leverage settings and quantity-step-to-target ratios, including rejected,
unfilled and partially filled opportunities. Measure capital utilization,
rejection rates, realized exposure, costs, adverse selection and losses
chronologically out of sample. Candle touches do not establish fills. This
review certifies neither implementation/persistence, F-012, F-014/F-015
implementation, Portfolio holds, exchange adapters nor execution. Fees, funding,
maintenance margin, liquidation protection, native leverage admissibility and
maximum realized loss are not established by `N/L`.
