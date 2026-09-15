# FINAL_FORMULA_SPECIFICATION

# F-011 - Position Size, Quantity, and Actual Notional Construction

## 1. Identity

| Field | Value |
|---|---|
| Formula ID | F-011 |
| Formula name | Position size, quantity, and actual notional construction |
| Owner | Position Rules |
| Formula family | POSITION_SIZING |
| Certification artifact | Final formula specification |
| Approved candidate | `F-011_COUNCIL_DEFINED_CYCLE_1` |
| Active methodology baseline | v1.2.14 |

## 2. Council Status

```text
FULL_COUNCIL_APPROVED = YES
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
SPECIFICATION_STATUS = FINAL_APPROVED
TRADING_FITNESS = ADEQUATE_FOR_DECLARED_ROLE_WITH_LIMITATIONS
```

The Full Council approved the Source Pack plus Council-defined semantics. These
findings are closed:

```text
F011-C01: min_qty versus min_order_qty ambiguity
F011-C02: complete failure mapping and precedence
F011-C03: exact quotient, persisted liability and rational replay
F011-C04: maximum-status applicability and inconsistent venue facts
```

## 3. Intended Purpose

F-011 converts a matching Portfolio own-capital grant into final order quantity,
actual order notional and persisted actual committed own-capital liability for a
single immutable Position construction cycle.

It answers:

```text
Given approved Entry, Stop, Take Profit, a matching Capital and Limits grant,
pinned leverage configuration and venue quantity/notional facts, what final
quantity and actual capital commitment can be constructed without exceeding the
grant or violating sizing constraints?
```

F-011 does not choose Entry, Stop, Take Profit, direction, leverage policy,
capital grant amount, Portfolio hold authority, Order Spec authorization,
exchange acceptance, fills, fees, funding, gross R:R or minimum net edge.

## 4. Actual Construct

F-011 is:

```text
own-capital grant
-> leveraged target notional
-> raw quantity at certified Entry
-> quantity-step floor
-> actual order notional
-> exact committed-capital quotient
-> ceiling-quantized persisted own-capital liability
-> venue quantity/notional and capital-bound gates
```

The approved scope is the declared linear USDT quantity convention where:

```text
quantity * Entry = notional
```

No contract multiplier or currency conversion is introduced.

## 5. Exact Formula and Rule

### 5.1 Symbols

```text
C = requested_capital_per_tranche
L = configured leverage
E = certified F-008 Entry / planned_entry_reference
q = qty_step
p = Qcapital = 0.000000000001
T = target_order_notional
R = raw_qty
Q = final_qty
N = actual_order_notional
A = actual_committed_capital_exact
H = actual_committed_capital_persisted
```

### 5.2 Scope and bindings

Require:

```text
initial Position approval
matching Portfolio Capital and Limits grant
pinned Position configuration
AVAILABLE/usable certified F-008 Entry
AVAILABLE/usable certified F-009 Stop
AVAILABLE/usable certified F-010 Take Profit
same instrument, direction, cycle, handoff, grant, configuration and metadata bindings
```

F-011 consumes F-008's identical planned Entry / LIMIT price unchanged and
retains LIMIT POST_ONLY. F-009 Stop and F-010 Take Profit are construction
prerequisites, not sizing operands. LONG maps to BUY and SHORT maps to SELL.

### 5.3 Input domain and aliases

`C`, `L`, `E`, `q`, minimum quantity, minimum notional and venue maximum leverage
must be positive finite exact decimal values with required provenance.

Require:

```text
C / Qcapital is an integer
L > 0
L <= venue_max_leverage
E > 0
q > 0
```

Reject an unaligned grant without rounding it.

`min_qty` means the same venue minimum as canonical contract field
`min_order_qty`, not another configurable threshold. The required contract field
remains `min_order_qty`. Conflicting supplied aliases or inconsistent
units/provenance reject. Do not round min/max thresholds to the quantity grid.

Beyond finite decimal representation, `L > 0` and the supplied maximum, F-011
adds no integer, step, precision or `L >= 1` restriction.

### 5.4 Maximum facts

`max_order_qty_status = AVAILABLE` requires:

```text
max_order_qty > 0
applicable provenance
max_order_qty >= min_order_qty
```

For the declared Bybit linear LIMIT POST_ONLY profile, require the applicable:

```text
lotSizeFilter.maxOrderQty
```

`max_order_qty_status = UNAVAILABLE` always prevents usable construction, even
if a stale numeric maximum accompanies it.

`max_order_qty_status = NOT_APPLICABLE` requires a null maximum and affirmative
evidence from the pinned profile that no maximum applies. Missing evidence
cannot establish non-applicability.

Unknown statuses, contradictory facts and unsupported non-applicability reject.
Facts come through Capital and Limits; Position performs no API refresh.

### 5.5 Construction

Compute exactly:

```text
T = C * L
R = T / E
Q = q * floor(R / q)
N = Q * E
A = N / L
H = p * ceil(A / p)
```

Require:

```text
Q > 0
Q / q is an integer
Q = q * floor(R / q)
T = C * L
R = T / E
N = Q * E
A = N / L
H = p * ceil(A / p)
Q >= min_order_qty
if max_order_qty_status = AVAILABLE: Q <= max_order_qty
N >= min_notional
A <= C
H <= C
```

Equality passes every inclusive boundary.

Flooring proves `A <= C`; since `C / p` is integral, it also proves `H <= C`.
The capital-bound checks remain mandatory defensive integrity checks. A
capital-bound failure is not an ordinary rounding outcome.

No failed gate permits clamping, splitting, resizing, changing leverage, or
revising any price or grant.

### 5.6 Failure mapping and precedence

Table order determines the primary reason. Preserve all determinable secondary
failures in that order, using ordinal field-name order for ties. Absent
dependency objects use their dependency reason; inconsistent supplied bindings
use `IDENTITY_INVALID`. A prerequisite-blocked gate is `UNAVAILABLE`, never
`PASS`; only a proven inapplicable maximum subcheck is `NOT_APPLICABLE`. Every
non-PASS construction exposes no approved/actionable sizing.

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

## 6. Inputs

| Input | Source | Required semantics |
|---|---|---|
| `C` / `requested_capital_per_tranche` | Capital and Limits / F-014 policy | Positive finite own-capital grant, Qcapital-aligned and bound to the same decision. |
| `L` / leverage | Position configuration / T-002 | Positive finite configured leverage not greater than valid venue maximum. |
| `E` / Entry | Certified F-008 | Positive final planned entry reference for the same cycle; unchanged. |
| F-009 Stop | Certified F-009 | AVAILABLE/usable prerequisite; not a sizing operand. |
| F-010 Take Profit | Certified F-010 | AVAILABLE/usable prerequisite; not a sizing operand. |
| `q` / `qty_step` | Capital and Limits venue facts / N-004 | Positive finite exact quantity step with provenance. |
| `min_order_qty` | Capital and Limits venue facts / N-004 | Positive finite venue minimum quantity; canonical alias for methodology `min_qty`. |
| `min_notional` | Capital and Limits venue facts / N-004 | Positive finite venue minimum notional. |
| `max_order_qty_status`, `max_order_qty` | Capital and Limits venue facts / N-004 | AVAILABLE / UNAVAILABLE / NOT_APPLICABLE with Council-defined predicates. |
| `venue_max_leverage` | Capital and Limits venue facts | Positive finite maximum leverage. |
| identities and digests | Market Handoff / Position / Portfolio | Same cycle, grant, configuration, instrument metadata and native profile bindings. |

## 7. Outputs

Primary outputs:

```text
target_order_notional = T
raw_qty = R
final_qty = Q
actual_order_notional = N
actual_committed_capital_exact = A
actual_committed_capital_persisted = H
quantity_gate_result
notional_gate_result
capital_bound_result
primary_status / reason
secondary_failures[]
```

Order Spec / construction confirmation bindings:

```text
entry.quantity = Q
leverage = L
economics.target_order_notional = T
economics.actual_order_notional = N
economics.actual_committed_capital = H
approved_quantity = Q
approved_leverage = L
approved_actual_order_notional = N
approved_actual_committed_capital = H
```

`R` and `A` may recur and are audit values, not external scalar contracts.
Preserve each as a reduced integer numerator / positive denominator pair
encoded as strings.

## 8. Units

| Item | Unit |
|---|---|
| `C`, `A`, `H` | Own capital in governed accounting/settlement currency |
| `T`, `N`, `min_notional` | Linear USDT quote/settlement notional |
| `E` | Instrument quote price unit |
| `R`, `Q`, `q`, `min_order_qty`, `max_order_qty` | Base contract/coin quantity units governed by instrument facts |
| `L`, `venue_max_leverage` | Dimensionless leverage multipliers |

## 9. Parameters

| Parameter | Class | Notes |
|---|---|---|
| Position size percentage / upstream grant sizing | `RESEARCH_PARAMETER` / T-001 | F-011 consumes the resulting grant; it does not choose it. |
| Leverage `L` | `RESEARCH_PARAMETER` / T-002 plus venue constraint | Mechanics validate configured value and venue maximum. |
| `Qcapital` | `APPROVED_POLICY` / `TT_NUMERIC_V1` | `0.000000000001`; own-capital liability is ceiling-quantized. |
| `qty_step`, `min_order_qty`, `min_notional`, `max_order_qty` | `APPROVED_POLICY` / exchange facts | N-004 quantity and notional constraints transported through Capital and Limits. |

## 10. Domain and Preconditions

F-011 can evaluate only when:

```text
initial opportunity decision was APPROVE
matching Capital and Limits exists
Position configuration identity/version/content digest is pinned
F-008 Entry is usable and identity-matched
F-009 Stop is usable and identity-matched
F-010 Take Profit is usable and identity-matched
C, L, E, q, min_order_qty, min_notional and venue_max_leverage are positive finite exact decimals
max_order_qty_status satisfies Section 5.4
all cycle/grant/instrument/profile/currency/provenance bindings match
```

Missing values are never guessed, zero-filled or refreshed by Position Rules.

## 11. Missing / Invalid Behavior

Use the failure mapping in Section 5.6. Non-PASS construction exposes no
approved quantity, actionable notional, successful Order Spec, construction
confirmation, Portfolio hold or submit authorization.

## 12. Boundaries

F-011 includes:

```text
leverage-to-target-notional conversion
raw quantity calculation
quantity-step floor normalization
actual order notional calculation
exact actual committed capital quotient
persisted committed-capital liability ceiling to Qcapital
capital non-overcommit checks
minimum quantity and notional checks
maximum quantity status and limit checks
approved sizing/economics scalar output for Order Spec and construction confirmation
```

F-011 excludes:

```text
Portfolio free-capital grant calculation
Portfolio hold and authorization
Entry selection
Stop calculation
Take Profit calculation
gross R:R
minimum net edge
fee calculation
funding
Order Lifecycle execution, acceptance, fills or native reconciliation
implementation of exchange adapters
```

## 13. Precision / Rounding

Apply `TT_NUMERIC_V1`:

- decimal strings parse exactly;
- add/subtract/multiply are exact;
- division retains exact rational value until the required output quantizer;
- no binary floats, exponent canonical decimals, epsilon comparisons or
  finite-precision intermediate rounding;
- quantity floor uses exact `floor_q(x) = q * floor(x / q)`;
- `T`, `Q` and `N` serialize as complete exact finite decimal values;
- `R` and `A` preserve reduced rational audit representations when recurring;
- `H` is `ceil_Qcapital(A)`;
- report serialization cannot change gate results.

`margin_required = A` exactly under this formula. The persisted accounting
liability is `H`, with:

```text
0 <= H - A < Qcapital
```

No approximate-equality gate is allowed.

## 14. Time Semantics

F-011 consumes one immutable post-grant construction cycle. It does not refresh
market data, Entry, Stop, Take Profit, configuration, grant, instrument facts or
fee facts while constructing. Newer compatible hard execution facts may be
evaluated by Lifecycle later without mutating the spec. Incompatible hard facts
block execution rather than causing Position to resize.

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
symbol and direction
candidate identity F-011_COUNCIL_DEFINED_CYCLE_1
Position configuration identity/version/content digest
Capital and Limits contract version and payload digest
requested_capital_per_tranche
instrument metadata revision
native profile revision
qty_step, min_order_qty, min_notional, max_order_qty/status/provenance
venue_max_leverage
certified F-008 Entry identity/value
certified F-009 Stop identity/value
certified F-010 Take Profit identity/value
numeric_policy_version = TT_NUMERIC_V1
target_order_notional
raw_qty rational audit value
final_qty
actual_order_notional
actual_committed_capital_exact rational audit value
actual_committed_capital_persisted
gate outcomes and ordered reasons
Order Spec digest and construction confirmation scalars
```

Identical evidence must reproduce identical numerical outputs and primary
rejection. Changed content under an existing identity, missing required replay
evidence or inconsistent persisted outputs fails closed. Replay creates no new
approval, grant or resized spec.

## 16. Configuration Pinning

Known pins:

```text
active methodology baseline = v1.2.14
F-011_COUNCIL_DEFINED_CYCLE_1
Capital and Limits contract_version = 5
Order Spec contract_version = 5
Approve/Reject contract_version = 5
TT_NUMERIC_V1
Qcapital = 0.000000000001
Position Rules configuration identity/version/content digest
instrument metadata revision
native profile revision
certified F-008 final specification
certified F-009 final specification
certified F-010 final specification
```

## 17. Dependencies

| Dependency | Class | Use |
|---|---|---|
| F-008 | `CERTIFIED_FORMULA` | Supplies final Entry `E`; F-011 must not modify it. |
| F-009 | `CERTIFIED_FORMULA` | Supplies final Stop prerequisite; not a sizing operand. |
| F-010 | `CERTIFIED_FORMULA` | Supplies final Take Profit prerequisite; not a sizing operand. |
| F-014 | `APPROVED_POLICY` | Portfolio free-capital and grant calculation produces `C`. |
| F-015 | `APPROVED_POLICY` | Actual committed capital from final quantity; covered through `TT_NUMERIC_V1` Section 4. |
| N-004 | `APPROVED_POLICY` | Quantity step and min/max quantity/notional normalization facts. |
| T-001 | `RESEARCH_PARAMETER` | Position size percentage / upstream grant sizing value. |
| T-002 | `RESEARCH_PARAMETER` / `CONFIG_PARAMETER` | Leverage value; mechanics validate configured value and venue maximum. |
| Capital and Limits v5 | `DOCUMENTATION_DEPENDENCY` | Post-APPROVE grant, venue facts and provenance. |
| Order Spec v5 | `DOCUMENTATION_DEPENDENCY` | Output shape and immutable spec semantics. |
| Approve/Reject v5 | `DOCUMENTATION_DEPENDENCY` | Construction confirmation semantics. |
| TT_NUMERIC_V1 | `APPROVED_POLICY` | Exact arithmetic, quantity floor, liability ceiling and canonical serialization. |

## 18. Ownership

Portfolio Rules owns free-capital calculation, capacity limits, grant creation,
and later hold/authorization. Position Rules owns post-grant sizing and final
Order Spec construction. API/instrument facts own venue quantity/notional facts
and max leverage facts as transported through Portfolio. Order Lifecycle owns
submission, exchange acceptance, fills and reconciliation.

F-011 must not introduce a direct Position Rules to API lookup.

## 19. Pipeline Role

```text
initial Position APPROVE
-> Portfolio Capital and Limits
-> F-011 final quantity / notional / actual committed capital
-> F-012 final gross R:R and minimum net edge
-> immutable Order Spec + CONSTRUCTION_RESULT
-> Portfolio hold / Submit Authorized
-> Order Lifecycle execution gate
```

## 20. Approved Uses

F-011 may be used to:

```text
construct final order quantity
construct actual order notional
construct persisted actual committed capital
validate capital non-overcommit
validate quantity and notional venue gates from supplied facts
populate approved sizing scalars in Order Spec and construction confirmation
produce deterministic rejection reasons for unsuccessful construction
```

## 21. Prohibited Interpretations

F-011 must not be interpreted as:

```text
a stop-distance risk sizing formula
a profitability formula
a leverage recommendation
a Portfolio grant formula
a Portfolio hold or authorization
a maximum-loss guarantee
a liquidation model
a venue leverage acceptance guarantee
a fill or liquidity guarantee
a permission to repair failed construction by resizing, splitting, repricing, changing leverage, changing prices or replacing the grant
```

## 22. Known Limitations

1. F-014/F-015 are consumed as `APPROVED_POLICY`; their implementation and
   provenance are not independently certified here.
2. F-011 adds no leverage step, precision or `L >= 1` restriction beyond finite
   decimal representation, `L > 0` and the supplied maximum.
3. Committed capital is not a maximum-loss guarantee.
4. Venue quantity/notional facts do not establish liquidity, acceptance, queue
   priority or fill probability.
5. Implementation, persistence, Portfolio holds, exchange adapters, execution,
   F-012, fees, funding, maintenance margin and liquidation protection remain
   uncertified.

## 23. Research Parameters

```text
T-001 position size percentage / upstream grant sizing
T-002 leverage value
grant/leverage calibration
quantity-step-to-target utilization effects
```

## 24. Empirical Validation Requirements

Evaluate across instruments, directions, regimes, grant/leverage settings and
quantity-step-to-target ratios, including rejected, unfilled and partially
filled opportunities. Measure capital utilization, rejection rates, realized
exposure, costs, adverse selection and losses chronologically out of sample.
Candle touches do not establish fills.

## 25. Edge and Regression Fixtures

### Complete passing example

```text
C = 67.34
L = 3
E = 101
q = 1
min_order_qty = 1
max_order_qty_status = AVAILABLE
max_order_qty = 2
min_notional = 202
venue_max_leverage = 3

T = 202.02
R = 10101 / 5050
Q = 2
N = 202
A = 202 / 3
H = 67.333333333334
unused capacity = 0.006666666666
result = PASS / AVAILABLE
```

### Required conformance cases

```text
zero flooring -> QTY_ZERO_AFTER_FLOOR
positive Q below min_order_qty -> QTY_BELOW_MINIMUM
available maximum with Q above max_order_qty -> QTY_ABOVE_MAXIMUM
N below min_notional -> NOTIONAL_BELOW_MINIMUM
unaligned grant -> INVALID_CAPITAL_GRANT
missing max status/provenance -> MISSING_EXCHANGE_FACT
unsupported NOT_APPLICABLE -> INVALID_EXCHANGE_FACT
max_order_qty_status = UNAVAILABLE -> MAX_ORDER_QTY_UNAVAILABLE
L above venue maximum -> LEVERAGE_ABOVE_MAXIMUM
defensive exact or persisted capital bound violation -> CAPITAL_BOUND_VIOLATION
recurring R/A rational audit values -> replay-equivalent reduced numerator/denominator
```

### Restart equality

Restart with identical frozen grant, dependency values, configuration, venue
facts and numeric policy must reproduce the same `T`, `R`, `Q`, `N`, `A`, `H`,
primary reason and ordered secondary failures.

## 26. Eight Final Expert Verdicts

| Perspective | Verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE_WITH_LIMITATIONS | Coherent conversion of granted capital into size. It does not size risk from stop distance or establish profitability. |
| Market Microstructure & Order Flow Researcher | APPROVE_WITH_LIMITATIONS | Quantity flooring respects the supplied grid. Venue minima and maxima establish neither liquidity nor fill probability. |
| Market Regime & Context Analyst | APPROVE_WITH_LIMITATIONS | Direction-neutral arithmetic and frozen inputs are appropriate. Regime sensitivity remains with grant/leverage calibration and downstream risk. |
| Quant Strategy Researcher | APPROVE | Exact construction, inclusive limits and liability ceiling are mathematically consistent under the specified input domain. |
| Risk & Trade Management Architect | APPROVE_WITH_LIMITATIONS | Both capital bounds are enforced; failures cannot trigger resizing. Committed capital is not a maximum-loss guarantee. |
| Execution & Exchange Mechanics Specialist | APPROVE_WITH_LIMITATIONS | Fact applicability, quantity grid and maximum-status behavior are sufficiently defined. Native acceptance remains outside certification. |
| Adversarial Strategy Reviewer | APPROVE_WITH_LIMITATIONS | Explicit rejection, alias conflict handling, dependency binding and defensive arithmetic checks close the identified ambiguities. |
| Performance & Strategy Diagnostics Analyst | APPROVE_WITH_LIMITATIONS | Exact audit values and deterministic failure precedence support replay and analysis; persistence implementation remains unverified. |

## 27. Final Council Record

```yaml
formula_id: F-011
review_mode: FULL_REVIEW
FULL_COUNCIL_APPROVED: YES
ANOTHER_REVIEW_CYCLE_REQUIRED: NO
approved_by: FULL_COUNCIL
candidate: F-011_COUNCIL_DEFINED_CYCLE_1
date: 2026-09-15
trading_fitness: ADEQUATE_FOR_DECLARED_ROLE_WITH_LIMITATIONS
remaining_blockers: NONE
source_pack_sha256: 404f9ad11315a17cb55b5424a74fbf19b473168335e5eb5ca4dadcf6242be267
closed_findings:
  F011-C01: CLOSED
  F011-C02: CLOSED
  F011-C03: CLOSED
  F011-C04: CLOSED
non_blocking:
  F011-L01: F-014/F-015 APPROVED_POLICY evidence sufficient for consumed interfaces.
  F011-P01: no additional leverage step/precision restriction invented.
  F011-E01: empirical grant/leverage effectiveness retained for research.
preserved_dependencies:
  - baseline v1.2.14
  - TT_NUMERIC_V1
  - Capital and Limits v5
  - Order Spec v5
  - Approve/Reject v5
  - F-008 final specification
  - F-009 final specification
  - F-010 final specification
excluded_certifications:
  - implementation
  - persistence
  - F-012
  - F-014/F-015 implementation
  - Portfolio holds
  - exchange adapters
  - execution
```
