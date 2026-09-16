# F-011 Source Pack

# F-011 - Position Size, Quantity, and Actual Notional Construction

## 1. Identity

| Field | Value |
|---|---|
| Formula ID | F-011 |
| Formula name | Position size, quantity, and actual notional construction |
| Owner | Position Rules |
| Formula family | POSITION_SIZING |
| Certification phase | Source Pack |
| Active methodology baseline | v1.2.14 |
| Source Pack status | Immutable pre-review provenance |

F-011 is a post-grant Position Rules construction formula. It converts a
Portfolio-owned own-capital grant into leveraged target notional, exchange-step
quantity, exact actual order notional, and actual committed own-capital
liability for the immutable Order Spec and construction confirmation.

## 2. Source Index

| Source | Evidence |
|---|---|
| `docs/FORMULA_METRICS_CATALOG.md` | Catalog row marks F-011 certification-required and points to `NUMERIC_POLICY.md` Section 4 and `POSITION_RULES.md` Appendix D. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 562-670 | Canonical leverage-to-notional, raw quantity, quantity normalization, actual notional/capital, min/max quantity and notional checks. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 682-719 | Leverage requirements and margin calculation context. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 723-745 | Portfolio accounting boundary: only actual committed capital returns to Portfolio accounting/holds; actual notional remains execution/risk/economics data. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 1231-1235 | Mandatory sequence: initial Position APPROVE precedes Portfolio Capital and Limits, then post-grant construction. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 1239-1310 | Order Spec output shape including quantity, leverage, notional, actual committed capital and venue validation fields. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 4660-4680 | Position Rules invariants: Position may convert own capital into leveraged notional but may not increase granted capital; no failed gate may be repaired by modifying quantity/capital. |
| `docs/trading-methodology/methodology/POSITION_RULES.md` lines 4735-4745 | Appendix D canonical economics/construction equality and no-overcommit binding. |
| `docs/trading-methodology/schemas/NUMERIC_POLICY.md` lines 1-27 | `TT_NUMERIC_V1` exact arithmetic model and output classes, including quantity step, exact notional, own-capital liability ceiling, and ratio reporting. |
| `docs/trading-methodology/schemas/NUMERIC_POLICY.md` lines 53-61 | Position final construction: exact target notional, raw quantity, quantity floor, actual notional, exact committed capital formula, persisted liability ceiling, no overcommit. |
| `docs/trading-methodology/business-contracts/CAPITAL_AND_LIMITS.md` lines 6-18, 24-79 | Capital grant timing, binding, required venue facts, and Capital and Limits payload. |
| `docs/trading-methodology/business-contracts/ORDER_SPEC.md` lines 6-18, 22-101 | Immutable Order Spec creation and output fields. |
| `docs/trading-methodology/business-contracts/APPROVE_REJECT.md` lines 6-18, 45-120 | Construction result semantics and approved economics fields. |
| `docs/formula-certification/F-008/F-008_FINAL_FORMULA_SPECIFICATION.md` | Certified planned entry input and ownership boundary. |
| `docs/formula-certification/F-009/F-009_FINAL_FORMULA_SPECIFICATION.md` | Certified stop output and downstream boundary. |
| `docs/formula-certification/F-010/F-010_FINAL_FORMULA_SPECIFICATION.md` | Certified take-profit output and downstream boundary. |

## 3. Purpose and Trading Context

F-011 answers:

```text
Given an immutable Position opportunity that has already passed initial
opportunity checks and received a Portfolio Capital and Limits grant, what
final order quantity, actual order notional and actual committed own-capital
liability may be constructed without exceeding the grant or violating exchange
quantity/notional facts?
```

Trading role:

- produce final quantity and notional used by the Order Spec;
- preserve capital discipline by preventing overcommit after exchange-step
  quantity flooring and own-capital liability quantization;
- provide the size inputs later consumed by F-012 net-edge and risk/reward
  economics;
- reject construction when sizing or venue facts cannot support a valid order.

F-011 does not select Entry, SL, TP, direction, leverage policy, capital grant
amount, Portfolio hold authority, or exchange submission.

## 4. Exact Formula If Available

Source formulas:

```text
C = requested_capital_per_tranche
L = user-configured leverage
E = planned_entry_reference / final Entry
q = qty_step

target_order_notional = C * L

raw_qty = target_order_notional / E

final_qty = floor(raw_qty / q) * q

actual_order_notional = final_qty * E

actual_committed_capital_exact = actual_order_notional / L

actual_committed_capital_persisted =
  ceil_Qcapital(actual_committed_capital_exact)
```

`Qcapital = 0.000000000001`.

Construction must independently require:

```text
actual_committed_capital_exact <= C
actual_committed_capital_persisted <= C
```

Venue checks:

```text
final_qty >= min_order_qty
actual_order_notional >= min_notional
if max_order_qty_status = AVAILABLE:
    final_qty <= max_order_qty
if max_order_qty_status = UNAVAILABLE and applicable:
    construction is UNAVAILABLE / fail-closed
```

Leverage checks:

```text
L > 0
L <= venue_max_leverage
```

## 5. Inputs

| Input | Source | Required semantics |
|---|---|---|
| `C` / `requested_capital_per_tranche` | Portfolio Capital and Limits / F-014 | Positive own-capital grant, same settlement/accounting currency, exact decimal string, Qcapital-aligned by Portfolio policy. |
| `L` / leverage | Position Rules configuration / T-002 | Positive configured leverage compatible with venue maximum. |
| `E` / Entry | Certified F-008 | Positive final planned entry reference for the same decision cycle and Order Spec. |
| `qty_step` / `q` | Capital and Limits venue facts / N-004 | Positive exact quantity step fact with provenance. |
| `min_order_qty` | Capital and Limits venue facts / N-004 | Positive minimum order quantity fact. |
| `min_notional` | Capital and Limits venue facts / N-004 | Positive minimum notional fact. |
| `max_order_qty` and status | Capital and Limits venue facts / N-004 | `AVAILABLE`, `UNAVAILABLE`, or `NOT_APPLICABLE`; Bybit linear LIMIT + POST_ONLY source is `lotSizeFilter.maxOrderQty`. |
| `venue_max_leverage` | Capital and Limits venue facts / T-002 policy validation | Maximum leverage allowed for the current instrument/profile. |
| Position configuration identity/version/digest | Position Rules | Pinned from initial Position evaluation through post-grant construction. |
| decision, grant and instrument identities | Market Handoff / Position / Portfolio | Same `decision_cycle_id`, `set_result_id`, `position_decision_id`, symbol, grant and instrument metadata revision. |

## 6. Outputs

Primary F-011 outputs:

```text
target_order_notional
final_qty
actual_order_notional
actual_committed_capital_exact
actual_committed_capital_persisted
quantity_gate_result
notional_gate_result
capital_bound_result
```

Order Spec / construction outputs include:

```yaml
entry:
  quantity: decimal-string
leverage: decimal-string
economics:
  target_order_notional: decimal-string
  actual_order_notional: decimal-string
  actual_committed_capital: decimal-string
venue_validation:
  max_order_qty_status: AVAILABLE | NOT_APPLICABLE
  max_order_qty:
    nullable: decimal-string
  max_order_qty_source_field: lotSizeFilter.maxOrderQty
  max_order_qty_source_ref: string
numeric_policy_version: TT_NUMERIC_V1
```

Construction confirmation repeats:

```text
approved_quantity
approved_leverage
approved_actual_order_notional
approved_actual_committed_capital
```

## 7. Units

| Item | Unit |
|---|---|
| `C`, actual committed capital | Own capital in governed accounting/settlement currency |
| target and actual order notional | Quote/settlement notional for the linear USDT perpetual |
| `E` | Instrument quote price unit |
| `final_qty`, `raw_qty`, `qty_step`, min/max order quantity | Base contract/coin quantity units governed by instrument facts |
| `L` | Dimensionless leverage multiplier |
| `min_notional` | Quote/settlement notional |

## 8. Parameters

| Parameter | Class | Notes |
|---|---|---|
| Position size percentage / grant sizing upstream | `RESEARCH_PARAMETER` / T-001 | F-011 consumes the resulting grant `C`; it does not choose the grant value. |
| Leverage `L` | `RESEARCH_PARAMETER` / T-002 plus venue constraint | Mechanics validate configured leverage; the value remains configurable/research-governed. |
| `Qcapital` | `APPROVED_POLICY` / `TT_NUMERIC_V1` | `0.000000000001`; own-capital liability is ceiling-quantized. |
| `qty_step`, `min_order_qty`, `min_notional`, `max_order_qty` | `APPROVED_POLICY` / exchange facts | N-004 quantity and notional constraints transported through Capital and Limits. |

## 9. Thresholds

Extracted thresholds and comparisons:

```text
C > 0
L > 0
L <= venue_max_leverage
E > 0
qty_step > 0
final_qty >= min_order_qty
actual_order_notional >= min_notional
if max_order_qty_status = AVAILABLE:
    final_qty <= max_order_qty
actual_committed_capital_exact <= C
actual_committed_capital_persisted <= C
```

All gate comparisons use exact pre-report values.

## 10. Sign and Direction Semantics

F-011 is quantity/capital construction and is direction-neutral for arithmetic.
Direction remains immutable from certified F-005 / Market Handoff and already
certified F-008/F-009/F-010 prices. F-011 must not re-infer, reverse or repair
direction.

Order side is part of Order Spec construction:

```text
LONG -> BUY entry side
SHORT -> SELL entry side
```

The source pack found no separate F-011-specific directional sizing formula.

## 11. Domain and Preconditions

F-011 runs only after:

1. A Position opportunity was initially approved.
2. Portfolio issued matching Capital and Limits.
3. Certified F-008 Entry is available for the same cycle.
4. Certified F-009 Stop and F-010 Take Profit are available for final Order Spec
   construction and downstream F-012 economics.
5. Position configuration identity/version/content digest remains pinned from
   initial opportunity decision.
6. Venue facts required for quantity, notional and leverage validation are
   present with provenance through Capital and Limits.

Missing required inputs are not guessed, zero-filled, refreshed by Position
Rules, or repaired by changing Entry, SL, TP, leverage, quantity or capital.

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

## 13. Precision

`TT_NUMERIC_V1` applies:

- decimal strings parse exactly;
- add/subtract/multiply are exact;
- division retains exact rational value until the required output quantizer;
- no binary floats, exponent canonical decimals, epsilon comparisons or
  finite-precision intermediate rounding;
- quantity floor uses exact `floor_q(x) = q * floor(x / q)`;
- exact monetary products such as `final_qty * Entry` retain all exact finite
  digits;
- own-capital liability is persisted as `ceil_Qcapital(exact_requirement)`;
- report serialization cannot change gate results.

## 14. Time Semantics

F-011 uses the same immutable decision cycle and grant. It does not refresh
market data, Entry, SL, TP, configuration, grant, instrument facts or fee facts
while constructing. Newer compatible hard execution facts may be evaluated by
Lifecycle later without mutating the spec; incompatible hard facts block
execution rather than causing Position to resize.

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
raw_qty
final_qty
actual_order_notional
actual_committed_capital_exact
actual_committed_capital_persisted
gate results and reason codes
Order Spec digest and construction confirmation scalars
```

Changed content under an existing identity fails closed. Replays must not create
a second initial approval, replacement grant, resized order, or refreshed spec.

## 16. Version and Configuration Pinning

Known pins:

```text
active methodology baseline = v1.2.14
Capital and Limits contract_version = 5
Order Spec contract_version = 5
Approve/Reject contract_version = 5
TT_NUMERIC_V1
Position Rules configuration identity/version/content digest
instrument metadata revision
native profile revision
certified F-008 final specification
certified F-009 final specification
certified F-010 final specification
```

## 17. Ownership

Portfolio Rules owns free-capital calculation, capacity limits, grant creation,
and later hold/authorization. Position Rules owns post-grant sizing and final
Order Spec construction. API/instrument facts own venue quantity/notional facts
and max leverage facts as transported through Portfolio. Order Lifecycle owns
submission, exchange acceptance, fills and reconciliation.

F-011 must not introduce a direct Position Rules -> API lookup.

## 18. Downstream Consumers

F-011 feeds:

- F-012 Risk/reward and minimum net edge calculation;
- Order Spec `entry.quantity`, `leverage`, and economics scalars;
- Approve/Reject `CONSTRUCTION_RESULT` approved economics;
- Portfolio hold/authorization comparison through actual committed capital;
- Order Lifecycle hard-compatibility checks and execution request construction.

## 19. Dependencies

| Dependency | Class | Use |
|---|---|---|
| F-008 | `CERTIFIED_FORMULA` | Supplies final Entry `E`; F-011 must not modify it. |
| F-009 | `CERTIFIED_FORMULA` | Supplies final Stop for full Order Spec / downstream construction context. |
| F-010 | `CERTIFIED_FORMULA` | Supplies final Take Profit for full Order Spec / downstream construction context. |
| F-014 | `APPROVED_POLICY` | Portfolio free-capital and grant calculation produces `C`. |
| F-015 | `APPROVED_POLICY` | Actual committed capital from final quantity; overlaps with `TT_NUMERIC_V1` Section 4. |
| N-004 | `APPROVED_POLICY` | Quantity step and min/max quantity/notional normalization facts. |
| T-001 | `RESEARCH_PARAMETER` | Position size percentage / upstream grant sizing value. |
| T-002 | `RESEARCH_PARAMETER` / `CONFIG_PARAMETER` | Leverage value; mechanics validate configured value and venue maximum. |
| Capital and Limits v5 | `DOCUMENTATION_DEPENDENCY` | Post-APPROVE grant, venue facts and provenance. |
| Order Spec v5 | `DOCUMENTATION_DEPENDENCY` | Output shape and immutable spec semantics. |
| Approve/Reject v5 | `DOCUMENTATION_DEPENDENCY` | Construction confirmation semantics. |
| TT_NUMERIC_V1 | `APPROVED_POLICY` | Exact arithmetic, quantity floor, liability ceiling and canonical serialization. |

## 20. Existing Worked Examples

`NUMERIC_POLICY.md` supplies:

```text
actual_order_notional = 202
leverage = 3
actual_committed_capital_exact = 202 / 3
actual_committed_capital_persisted = 67.333333333334
grant = 67.34
unused capacity = 0.006666666666
```

The example states that rounding the liability down would create incorrectly
spendable capital; the hold must use the persisted liability, not the grant.

No complete F-011 example combining grant, entry, quantity step, min/max
quantity, min notional and max leverage was found in the extracted sources.

## 21. Explicit Source Gaps and Review Questions

Source gaps for Full Council review:

1. The methodology uses `min_qty` in one section and `min_order_qty` in
   contract payloads; the certification should decide whether these are the
   same fact for F-011.
2. Failure-code mapping is partial. Extracted codes include
   `QTY_BELOW_MINIMUM`, `QTY_ABOVE_MAXIMUM`, and `NOTIONAL_BELOW_MINIMUM`;
   explicit reason codes for invalid grant, invalid leverage, missing/invalid
   venue facts, zero final quantity, `max_order_qty_status = UNAVAILABLE`, and
   capital-bound violation may need Council definition.
3. The source says `margin_required = actual_order_notional / L` should
   approximately equal actual committed capital, while `TT_NUMERIC_V1` requires
   exact quotient plus persisted ceiling liability. The final spec should use
   the numeric policy distinction and avoid treating "approximately" as a gate.
4. F-014 and F-015 are approved-as-defined policies rather than separately
   certified formula final specs in the formula-certification tree.
5. The source pack found no explicit upper/lower product bound for leverage
   precision or leverage step beyond `L > 0` and `L <= venue_max_leverage`.
6. It is not yet explicit whether `target_order_notional = C * L` is serialized
   exactly or only as a final finite decimal if terminating; Council should
   verify output treatment under `TT_NUMERIC_V1`.

## 22. Reviewer Handoff Summary

F-011 has a largely explicit canonical construction:

```text
grant C
-> target notional C * L
-> raw quantity target / Entry
-> final quantity floored to qty_step
-> actual order notional final_qty * Entry
-> actual committed capital exact quotient / L
-> persisted own-capital liability ceil_Qcapital
-> exact non-overcommit and venue quantity/notional gates
```

The principal review needs are:

- certify mathematical correctness and determinism under `TT_NUMERIC_V1`;
- reconcile `min_qty` vs `min_order_qty`;
- make failure/rejection reasons complete;
- preserve Portfolio/Position/API/Lifecycle ownership boundaries;
- confirm trading fitness as a conservative post-grant sizing construction;
- preserve that F-011 never repairs a failed trade by changing Entry, SL, TP,
  leverage, quantity or capital.
