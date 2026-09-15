# FINAL_FORMULA_SPECIFICATION

# F-012 - Risk/Reward and Minimum Net Edge Calculation

## 1. Identity

| Field | Value |
|---|---|
| Formula ID | F-012 |
| Formula name | Risk/reward and minimum net edge calculation |
| Owner | Position Rules |
| Formula family | RISK_REWARD |
| Certification artifact | Final formula specification |
| Approved candidate | `F-012_COUNCIL_DEFINED_CYCLE_1` |
| Active methodology baseline | v1.2.14 |

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = YES
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
SPECIFICATION_STATUS = FINAL_APPROVED
TRADING_FITNESS = ADEQUATE_FOR_DECLARED_ROLE_WITH_LIMITATIONS
```

Closed findings:

```text
F012-C01: R:R branching, threshold domain and threshold units
F012-C02: formula outputs versus construction payload and disabled gate economics
F012-C03: other costs and SL diagnostics
F012-C04: geometry, arithmetic, failure precedence and replay completeness
F012-C05: F-011 direct dependency
```

## 3. Intended Purpose

F-012 evaluates final Position construction eligibility from certified Entry,
Stop, Take Profit, final quantity/notional, governed fee facts and configured
thresholds. It calculates gross structural R:R and planned TP-scenario Minimum
Net Edge.

F-012 does not choose Entry, Stop, Take Profit, leverage, quantity, grant,
Portfolio hold, submit authorization, execution, realized fee attribution,
funding, liquidation, or realized PnL.

## 4. Actual Construct

F-012 is:

```text
certified final prices and quantity
+ directional structural distance validation
+ gross R:R comparator
+ deterministic planned entry/TP fee economics
+ planned TP net edge comparator
+ final construction eligibility result
```

Certification is restricted to the inherited linear USDT convention:

```text
N = Q * E
```

No contract multiplier or currency conversion is introduced.

## 5. Exact Formula and Rule

### 5.1 Symbols

```text
direction = LONG | SHORT
s = 1 for LONG, -1 for SHORT
E = certified Entry
SL = certified Stop
TP = certified Take Profit
Q = certified final quantity
N = certified actual_order_notional
m = maker_fee_rate
t = taker_fee_rate
```

### 5.2 Scope and prerequisites

Require usable certified F-008 Entry, F-009 Stop, F-010 Dynamic TP and
successful F-011 sizing, with matching instrument, direction, cycle, handoff,
configuration, grant and metadata bindings. `E`, `SL`, `TP`, `Q` and `N` must
be positive finite exact decimals.

Preserve LIMIT POST_ONLY entry and MARKET exits. F-012 consumes final values
without rerounding, resizing or repairing them.

### 5.3 Directional geometry

```text
dr = s * (E - SL)
dw = s * (TP - E)
```

Require:

```text
dr > 0
dw > 0
```

Then:

```text
risk_distance_price = dr
reward_distance_price = dw
risk_distance_pct = 100 * dr / E
reward_distance_pct = 100 * dw / E
gross_rr = dw / dr
gross_profit_tp = dw * Q
gross_loss_sl = dr * Q
```

R:R and its threshold are dimensionless.

### 5.4 Planned TP fee economics

Fee rates are fractional rates.

```text
entry_fee = N * m
tp_exit_notional = TP * Q
tp_exit_fee = TP * Q * t
tp_total_cost = entry_fee + tp_exit_fee
net_profit_tp = gross_profit_tp - tp_total_cost
net_edge_pct = 100 * net_profit_tp / N
```

Edge and its threshold use percent units.

Neither committed capital nor target notional replaces `N` in the denominator.

### 5.5 Fees, other costs and funding

A-003 `APPROVED_AS_DEFINED` policy/factual basis is sufficient for this planned
calculation. Certification of realized attribution is unnecessary for this
interface.

Require exact finite signed rates and governed provenance, including schedule
version, effective time and source reference, applicable to the bound
instrument/account fee schedule and mechanics at frozen construction time. Zero
fees and negative rebates require factual support and preserve their signs. No
fee refresh, guessed rate or missing-value zero-fill is permitted.

The approved baseline contains only entry and TP fees:

```text
other_exchange_costs_if_deterministic = 0
```

A claimed applicable additional cost requires separately approved deterministic
definition and reviewed integration; otherwise economics is unavailable.

Funding remains excluded:

```text
funding_in_planned_net_edge = false
```

### 5.6 Gate semantics

Enabled flags must be actual booleans.

Enabled thresholds must be present and exact finite decimals. No default or
additional positive lower bound is inferred. Disabled thresholds are unused.

Minimum R:R:

```text
if disabled:
    status = NOT_APPLICABLE
elif gross_rr >= configured_minimum_rr:
    status = PASS
else:
    status = FAIL
    reason = RR_BELOW_MINIMUM
```

Minimum Net Edge:

```text
if disabled:
    status = NOT_APPLICABLE
elif net_edge_pct >= configured_minimum_net_edge_pct:
    status = PASS
else:
    status = FAIL
    reason = NET_EDGE_BELOW_MINIMUM
```

An enabled prerequisite-blocked gate is `UNAVAILABLE`. Zero or negative net edge
is valid signed data; the comparison determines result, including when a
configured threshold is nonpositive.

F-012 owns local `minimum_rr_result` semantics and audit evidence plus existing
`economics.gross_rr`; it adds no `minimum_rr` field to construction v5.
Preserve the existing `minimum_net_edge` wire result.

For rule results, disabled `configured_value` is null; `calculated_value`
contains the valid reported ratio when available, otherwise null;
PASS/NOT_APPLICABLE reasons are null. Unknown flags cannot be represented as
disabled.

### 5.7 Required economics versus disabled gates

The successful Order Spec requires numeric planned edge, maker/taker rates and
fee provenance even when Minimum Net Edge is disabled. Therefore missing or
invalid fees block successful construction while that disabled gate remains
`NOT_APPLICABLE`.

Both gates disabled never bypass dependency, geometry, integrity or required
economics checks. Successful F-012 evaluation requires all mandatory checks and
every enabled gate to pass; disabled gates remain `NOT_APPLICABLE`.

### 5.8 SL diagnostics

Retain gross SL loss magnitude. SL fee/notional and net-R:R extensions are
optional local diagnostics, without external fields or hard gates:

```text
sl_exit_notional = SL * Q
sl_exit_fee = SL * Q * t
sl_total_cost = entry_fee + sl_exit_fee
net_loss_sl = gross_loss_sl + sl_total_cost
```

When:

```text
net_loss_sl > 0
```

then:

```text
net_rr = net_profit_tp / net_loss_sl
```

Otherwise return diagnostic:

```text
UNAVAILABLE / NONPOSITIVE_NET_LOSS_SL
```

with null ratio. Never use absolute value, infinity or fabricated zero to
repair it. Diagnostic absence or undefined net R:R does not reject an otherwise
valid construction.

### 5.9 Failure precedence

Table order determines the primary local F-012 result. Retain every
independently determinable secondary failure in order, with ordinal field-name
ordering for ties. Missing whole dependency objects use dependency reasons;
inconsistent supplied bindings use `IDENTITY_INVALID`. Blocked enabled gates
are `UNAVAILABLE`; validated disabled gates remain `NOT_APPLICABLE`.

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

With no failures:

```text
PASS / AVAILABLE
```

Any overall non-PASS result prevents successful construction and approved /
actionable economics. Available values remain diagnostic.

## 6. Inputs

| Input | Source | Required semantics |
|---|---|---|
| `E` / Entry | Certified F-008 | Positive final Entry for same decision cycle. |
| `SL` | Certified F-009 | Positive final Stop for same direction/cycle. |
| `TP` | Certified F-010 | Positive final Take Profit for same direction/cycle. |
| `Q`, `N` | Certified F-011 | Positive final quantity and actual order notional. |
| `direction` | Market Handoff / Position | Immutable `LONG` or `SHORT`. |
| `maker_fee_rate`, `taker_fee_rate` | Capital and Limits fee facts / A-003 policy | Exact finite signed fractional rates with factual support. |
| fee provenance | Capital and Limits | Schedule version, effective time and source reference. |
| Minimum R:R enabled flag and threshold | Position configuration / T-005 | Boolean flag; threshold exact finite decimal when enabled. |
| Minimum Net Edge enabled flag and threshold | Position configuration / T-006 | Boolean flag; threshold exact finite percent value when enabled. |
| Position configuration identity/version/digest | Position Rules | Pinned for the cycle. |

## 7. Outputs

Primary local outputs:

```text
risk_distance_price
risk_distance_pct
reward_distance_price
reward_distance_pct
gross_rr
gross_profit_tp
gross_loss_sl
entry_fee
tp_exit_notional
tp_exit_fee
tp_total_cost
net_profit_tp
net_edge_pct
minimum_rr_result
minimum_net_edge_result
funding_in_planned_net_edge = false
secondary_failures[]
```

Optional local diagnostics:

```text
sl_exit_notional
sl_exit_fee
sl_total_cost
net_loss_sl
net_rr or NONPOSITIVE_NET_LOSS_SL
```

Order Spec economics:

```yaml
economics:
  gross_rr: decimal-string
  planned_net_edge_pct: decimal-string
  minimum_net_edge_enabled: boolean
  minimum_net_edge_result: PASS | NOT_APPLICABLE
  maker_fee_rate: decimal-string
  taker_fee_rate: decimal-string
  fee_schedule_version: string
  fee_rate_source_ref: string
  funding_in_planned_net_edge: false
```

Construction confirmation retains the existing `minimum_net_edge` rule result.

## 8. Units

| Item | Unit |
|---|---|
| Entry, SL, TP, distances | Instrument quote price units |
| `Q` / final quantity | Base contract/coin quantity units |
| gross profit/loss, fees, costs, actual order notional | Governed quote/settlement monetary unit |
| `gross_rr`, `net_rr`, configured minimum R:R | Dimensionless ratios |
| `risk_distance_pct`, `reward_distance_pct`, `net_edge_pct`, configured minimum net edge | Percent units; numeric `1` means one percent |
| fee rates | Fractional rates |

## 9. Parameters

| Parameter | Class | Notes |
|---|---|---|
| Minimum Risk / Reward threshold | `RESEARCH_PARAMETER` / T-005 | Dimensionless; calibration remains empirical. |
| Minimum Net Edge threshold | `RESEARCH_PARAMETER` / T-006 | Percent units; calibration remains empirical. |
| Maker/taker fee rates | A-003 / fee facts | Factual planned fee inputs; realized attribution implementation not certified. |
| Additional deterministic costs | T-010 / future approved policy | Empty set in the approved baseline unless separately approved and integrated. |

## 10. Domain and Preconditions

F-012 can evaluate only when:

```text
F-008 Entry is usable and identity-matched
F-009 Stop is usable and identity-matched
F-010 Take Profit is usable and identity-matched
F-011 sizing is successful and identity-matched
E, SL, TP, Q and N are positive finite exact decimals
N = Q * E
direction in {LONG, SHORT}
pinned configuration has valid enabled flags and required thresholds
required fee facts and provenance are available
```

Missing values are not guessed, zero-filled or replaced by assumptions.

## 11. Missing / Invalid Behavior

Use Section 5.9 failure precedence. Non-PASS results expose no approved /
actionable economics and cannot create a successful Order Spec.

## 12. Boundaries

F-012 includes:

```text
gross structural R:R
planned TP scenario fee economics
planned TP net edge percent
minimum R:R and minimum net edge gate semantics
diagnostic SL-side economics
Order Spec economics values
construction minimum_net_edge rule result
```

F-012 excludes:

```text
Entry / Stop / Take Profit selection
position sizing and quantity construction
Portfolio grant / hold / authorization
Order Lifecycle execution and fills
realized fee cashflow attribution
funding prediction in planned net edge
liquidation, maintenance margin or maximum-loss modeling
spread/slippage/funding assumptions outside separately approved deterministic costs
realized PnL accounting
```

## 13. Precision / Rounding

Apply `TT_NUMERIC_V1`:

- exact decimal parsing and finite monetary products/sums;
- exact rational division;
- no intermediate rounding, binary floats or epsilon;
- compare `dw >= configured_minimum_rr * dr` directly;
- compare `100 * net_profit_tp >= configured_minimum_net_edge_pct * N`
  directly;
- report ratios with `10^-18 * floor(exact_ratio / 10^-18)`, including floor
  toward negative infinity for negative values;
- preserve reduced signed numerator / positive denominator pairs for exact
  ratios alongside canonical reports.

Gate decisions use exact pre-report values.

## 14. Time Semantics

F-012 uses one immutable construction cycle and pinned Position configuration.
Fee facts are the governed facts supplied through upstream contracts for the
frozen construction time. F-012 does not fetch or refresh fees. Funding events
after opening are realized downstream and excluded from planned Minimum Net
Edge.

## 15. State, Replay and Restart

Replay/restart must preserve:

```text
decision_cycle_id
set_result_id
position_decision_id
capital_grant_id
construction_result_id
position_plan_id
tranche_id
F-012_COUNCIL_DEFINED_CYCLE_1
certified F-008/F-009/F-010/F-011 dependency identities and values
direction
configuration identity/version/content digest
fee facts, effective time, schedule version and source reference
empty-cost baseline policy
enabled flags and thresholds
exact ratio numerator/denominator pairs
reported ratio fields
gate statuses and ordered reasons
Order Spec economics bindings
construction confirmation bindings
numeric_policy_version = TT_NUMERIC_V1
```

Restart must reproduce values and statuses from frozen evidence. Missing
evidence, changed content under an identity or inconsistent persisted outputs
fails closed.

## 16. Configuration Pinning

Known pins:

```text
active methodology baseline = v1.2.14
F-012_COUNCIL_DEFINED_CYCLE_1
TT_NUMERIC_V1
Capital and Limits v5
Order Spec v5
Approve/Reject v5
Position Rules configuration identity/version/content digest
certified F-008 final specification
certified F-009 final specification
certified F-010 final specification
certified F-011 final specification
```

## 17. Dependencies

| Dependency | Class | Use |
|---|---|---|
| F-008 | `CERTIFIED_FORMULA` | Entry price. |
| F-009 | `CERTIFIED_FORMULA` | Stop price. |
| F-010 | `CERTIFIED_FORMULA` | Take Profit price. |
| F-011 | `CERTIFIED_FORMULA` | Final quantity and actual order notional. |
| A-003 | `APPROVED_POLICY` | Planned fee factual basis; realized attribution implementation excluded. |
| T-005 | `RESEARCH_PARAMETER` | Minimum R:R threshold. |
| T-006 | `RESEARCH_PARAMETER` | Minimum Net Edge threshold. |
| T-010 | `RESEARCH_PARAMETER` | No planned additional costs without approved deterministic integration. |
| TT_NUMERIC_V1 | `APPROVED_POLICY` | Exact arithmetic and ratio report quantization. |
| Capital and Limits v5 | `DOCUMENTATION_DEPENDENCY` | Fee facts and provenance. |
| Order Spec v5 | `DOCUMENTATION_DEPENDENCY` | Economics output fields. |
| Approve/Reject v5 | `DOCUMENTATION_DEPENDENCY` | Construction result rule output. |

## 18. Ownership

Position Rules owns F-012 planned evaluation. Upstream contracts own certified
prices, sizing and factual fee inputs. Portfolio owns authorization. Lifecycle
owns execution and realized cashflows. Accounting owns realized fee attribution.

## 19. Pipeline Role

```text
F-008 Entry + F-009 Stop + F-010 TP + F-011 sizing
-> F-012 gross R:R and planned net edge
-> CONSTRUCTED or construction REJECT
-> Order Spec economics
-> Portfolio hold / Submit Authorized
-> Order Lifecycle execution
```

## 20. Approved Uses

F-012 may be used to:

```text
evaluate gross structural R:R
evaluate planned TP scenario net edge
populate Order Spec economics fields
populate construction minimum_net_edge rule result
reject construction on failed/unavailable mandatory economics gates
provide deterministic diagnostic SL-side economics
```

## 21. Prohibited Interpretations

F-012 must not be interpreted as:

```text
expected return proof
profitability guarantee
fill probability model
maximum loss guarantee
liquidation model
funding forecast
realized PnL accounting
permission to repair prices, leverage, quantity, grant, fees or configuration
Portfolio authorization
Order Lifecycle submit authority
```

## 22. Known Limitations

1. Planned TP edge is a conditional scenario, not expected value.
2. Gross R:R and planned SL diagnostics do not bound realized loss.
3. Actual fills, slippage, adverse selection and execution ordering are outside
   certification.
4. A-003 implementation, fee settlement/rounding and attribution, persistence,
   execution, Portfolio authorization and realized accounting remain
   uncertified.

## 23. Research Parameters

```text
T-005 minimum R:R threshold
T-006 minimum net edge threshold
fee schedule sensitivity
execution cost sensitivity
target-before-stop outcomes
```

## 24. Empirical Validation Requirements

Validate T-005/T-006 calibration chronologically out of sample across
instruments, directions, regimes and fee schedules, including rejected,
unfilled and partially filled opportunities. Measure execution costs, funding
separately, adverse selection, target-before-stop outcomes and realized
results. Candle touches establish neither fills nor exit ordering.

## 25. Edge and Regression Fixtures

### LONG passing example

```text
E = 100
SL = 99
TP = 102
Q = 2
N = 200
m = 0.0002
t = 0.0006

dr = 1
dw = 2
gross_rr = 2
entry_fee = 0.04
tp_exit_fee = 0.1224
tp_total_cost = 0.1624
net_profit_tp = 3.8376
net_edge_pct = 1.9188

thresholds 2 and 1.9188 both pass.
```

### SHORT counterpart

```text
E = 100
SL = 101
TP = 98
Q = 2
N = 200
m = 0.0002
t = 0.0006

dr = 1
dw = 2
gross_rr = 2
tp_exit_fee = 0.1176
net_edge_pct = 1.9212
```

### Exact comparison versus report quantization

```text
exact gross_rr = 2 / 3
reported gross_rr = 0.666666666666666666
threshold = 0.6666666666666666665
result = PASS
```

Conformance must also cover all enable combinations, absent/invalid thresholds,
signed/zero fees, zero/negative edge, wrong-side/equal prices, invalid sizing,
simultaneous failures, undefined SL diagnostics, negative report flooring and
restart equality.

## 26. Eight Final Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE_WITH_LIMITATIONS | Gross structural R:R and TP-scenario net edge are coherent eligibility filters; neither establishes positive expectancy. |
| Market Microstructure & Order Flow Researcher | APPROVE_WITH_LIMITATIONS | Maker-entry and taker-exit fee assumptions match the declared mechanics. Actual fills, slippage and adverse selection remain unmodeled. |
| Market Regime & Context Analyst | APPROVE_WITH_LIMITATIONS | Frozen, direction-consistent evaluation is appropriate. Threshold effectiveness and stale-price effects remain regime-dependent. |
| Quant Strategy Researcher | APPROVE | Directional geometry, monetary formulas, denominator validation and exact comparisons are consistent under the defined linear contract scope. |
| Risk & Trade Management Architect | APPROVE_WITH_LIMITATIONS | Mandatory prerequisites, independent gates and terminal rejection preserve risk boundaries. Planned SL loss is not a maximum-loss guarantee. |
| Execution & Exchange Mechanics Specialist | APPROVE_WITH_LIMITATIONS | Supplied fee facts and unchanged certified prices preserve ownership. Exchange acceptance, execution and actual fee settlement are excluded. |
| Adversarial Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Definitions resolve disabled gates, malformed inputs, unsupported costs, undefined ratios and deterministic failure precedence. |
| Performance & Strategy Diagnostics Analyst | APPROVE_WITH_LIMITATIONS | Exact audit values, explicit availability and immutable evidence support reproducible diagnostics. Persistence implementation and empirical effectiveness remain unverified. |

## 27. Final Council Record

```yaml
formula_id: F-012
review_mode: FULL_REVIEW
FULL_COUNCIL_APPROVED: YES
ANOTHER_REVIEW_CYCLE_REQUIRED: NO
approved_by: FULL_COUNCIL
candidate: F-012_COUNCIL_DEFINED_CYCLE_1
date: 2026-09-15
remaining_blockers: NONE
source_pack_sha256: a9eb48c0204b033b9441261b049ef2d99fbd6d456feeb55fa62a5974a1c9ddc1
closed_findings:
  F012-C01: CLOSED
  F012-C02: CLOSED
  F012-C03: CLOSED
  F012-C04: CLOSED
  F012-C05: CLOSED
excluded_certifications:
  - A-003 implementation
  - fee settlement/rounding and attribution
  - persistence
  - execution
  - Portfolio authorization
  - realized accounting
```
