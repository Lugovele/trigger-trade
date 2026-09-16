# F-007 REVISED SPECIFICATION CYCLE 1

# F-007 - Position Rules SHORT Formula

## 1. Identity

| Field | Value |
|---|---|
| Formula ID | F-007 |
| Formula name | Position Rules SHORT formula |
| Owner | Position Rules |
| Formula family | LONG_SHORT |
| Certification artifact | Revised candidate |
| Review cycle | 1 |
| Active methodology baseline | v1.2.14 |
| Dynamic SL methodology id | TT-METH-016 |
| Dynamic SL methodology version | 0.2.1 |

## 2. Council Status

```text
FULL_COUNCIL_APPROVED = NO
ANOTHER_REVIEW_CYCLE_REQUIRED = YES
SPECIFICATION_STATUS = REVISED_CANDIDATE_FOR_REVIEW
```

This candidate closes Cycle 1 blockers:

```text
F007-C01: finite positive tick-grid output and terminal numeric failure contract
F007-C02: canonical deterministic level_id tie-break
F007-C03: handoff/provenance/thesis-binding validation precedence
```

## 3. Intended Purpose

F-007 constructs the SHORT Dynamic Stop Loss candidate for a Position Plan. It
consumes a frozen committed SHORT Market Handoff, the certified planned entry
from F-008, and Position Rules Dynamic Stop Loss configuration. It produces
either a usable SHORT stop candidate or an explicit unavailable/rejection
reason.

F-007 answers:

```text
Given a committed SHORT Set handoff and a certified planned entry, where is the
governed SHORT structural stop, and is that stop feasible under the configured
ATR risk-distance cap after outward tick rounding?
```

It does not answer whether the trade is profitable, whether the entry will fill,
whether the exchange will accept the order, or whether the complete Position
Plan should be approved after target, sizing, risk/reward, fee and Portfolio
checks.

## 4. Actual Construct

Dynamic Stop Loss is:

```text
governed market invalidation
+
ATR noise buffer
+
minimum technical distance
+
maximum feasibility constraint
+
outward tick rounding
```

For SHORT, the stop must be above the selected adverse reference and above the
planned entry. If the structurally correct stop is too wide or cannot be
represented as a finite positive outward-rounded tick-grid price, Position
rejects the Position Plan. It must not clamp, move the stop inward, retry a
weaker reference, synthesize an ATR-only stop, reprice the entry, or repair
producer bindings.

## 5. Exact Formula and Rule

### 5.1 Symbols

```text
E = planned_entry_reference from certified F-008
A = received volatility.atr_15m from Market Handoff, certified by F-003
t = tick_size
R = selected_reference_price
Sstop = rounded_stop
```

All are exact positive decimals before F-007 calculation. Position consumes
`A` as the received Q18 Market Handoff value and must not recompute ATR, recover
hidden precision, or use display rounding.

### 5.2 Required SHORT direction

F-007 evaluates only when the immutable Market Handoff direction is:

```text
SHORT
```

`NONE` is invalid. `LONG` belongs to F-006.

### 5.3 Directional reference types

F-007 SHORT permits only these adverse high reference types for both thesis
references and default selection:

```text
SWING_HIGH_15M
SWING_HIGH_1H
PREVIOUS_DAY_HIGH
RANGE_HIGH
```

Low reference types are not eligible for F-007.

### 5.4 General candidate eligibility

A candidate level is eligible only if all are true:

```text
level exists in references.levels[]
level_id is unique within the canonical handoff level set
available_at <= matched_at
price is finite and > 0
level_type is one of the four permitted SHORT high types
level.price > E + t
```

The final adverse-side test is recomputed against `planned_entry_reference`.
The Set cached side is audit-only for Dynamic SL. A level within one tick of the
planned entry is ineligible.

No synthetic level is permitted.

### 5.5 Handoff and thesis-binding validation precedence

Before F-007 reference selection:

1. Reject invalid handoff identity, provenance or digest.
2. Reject invalid or conflicting producer bindings.
3. Reject dangling thesis IDs.
4. Reject producer availability violations.
5. Reject duplicate or conflicting canonical level IDs.
6. Reject `sl_context.thesis_reference_policy = NONE` when either the thesis
   reference ID or the binding is non-null.

These are handoff-consumption failures, not warning-only fallback cases.

`PREFERRED` fallback is allowed only when the thesis pair is contract-valid
null, or when a valid bound reference exists but fails F-007 eligibility.

`REQUIRED` has no fallback. If the required thesis reference is absent,
dangling, unavailable as-of `matched_at`, not one of the four SHORT high types,
nonpositive, nonfinite, or not adverse-side eligible against `E`, return:

```text
usable = false
reason = THESIS_REFERENCE_INVALID
```

If `PREFERRED` has a valid bound reference and it is eligible, select it. If it
is validly bound but fails F-007 eligibility, record:

```text
warning = INVALID_THESIS_REFERENCE_OVERRIDE
```

and continue to the default hierarchy. If policy is `NONE`, both thesis ID and
binding must be null and default hierarchy applies.

Calculation fallback never rewrites the producer binding.

### 5.6 Family priority

`sl_context.set_family` is read only from the frozen Market Handoff and must be
one of:

```text
TREND_CONTINUATION
RANGE
BREAKOUT_RECLAIM
GENERIC
```

If missing or invalid:

```text
MISSING_SET_FAMILY
```

For `TREND_CONTINUATION` and `GENERIC`:

```text
1. SWING_HIGH_15M
2. SWING_HIGH_1H
3. PREVIOUS_DAY_HIGH
4. RANGE_HIGH
```

For `RANGE`:

```text
1. RANGE_HIGH
2. SWING_HIGH_15M
3. SWING_HIGH_1H
4. PREVIOUS_DAY_HIGH
```

For `BREAKOUT_RECLAIM`, a valid `REQUIRED` or `PREFERRED` thesis reference
controls selection. Otherwise default:

```text
1. SWING_HIGH_15M
2. SWING_HIGH_1H
3. PREVIOUS_DAY_HIGH
4. RANGE_HIGH
```

No free-form breakout reference is created.

### 5.7 Total ordering within the same priority type

When multiple eligible levels share the same priority type, sort by:

```text
1. latest exact available_at
2. smallest exact level.price - E
3. ascending case-sensitive ordinal Unicode code-point level_id
```

This is a total deterministic ordering over valid distinct canonical level IDs.
No locale collation, case folding, natural sort, numeric substring sort,
arrival order, array order, or implementation-default string comparator is
allowed.

`age_seconds` is diagnostic only and is derived from `available_at`.

### 5.8 Audit trail

Before selection persist:

```text
candidate_level_ids_before_ranking[]
ineligible_level_ids_with_reason[]
```

For the selected reference persist:

```text
selected_level_id
selected_level_type
selected_reference_price
selected_reference_timeframe
selected_reference_available_at
selected_reference_age_seconds
reference_priority_rank
```

### 5.9 Corroborating levels

Eligible adverse-side levels corroborate the selected reference if:

```text
4 * abs(other_level.price - R) <= A
```

This is exactly equivalent to:

```text
abs(other_level.price - R) / A <= 0.25
```

Exclude the selected level itself. If the resulting list is non-empty, record:

```text
warning = MULTIPLE_NEARBY_LEVELS
```

This warning is diagnostic only.

### 5.10 Stop calculation

For selected reference `R`:

```text
buffer_price = 0.20 * A
raw_stop = R + buffer_price

minimum_distance_price = 0.50 * A
minimum_stop = E + minimum_distance_price

adjusted_stop = max(raw_stop, minimum_stop)
minimum_distance_adjustment_applied = (raw_stop < minimum_stop)
```

### 5.11 Pre-rounding risk feasibility

```text
pre_rounding_risk_price = adjusted_stop - E
```

The pre-rounding candidate is feasible only if:

```text
pre_rounding_risk_price <= 2.00 * A
```

Equivalent diagnostic:

```text
pre_rounding_risk_atr = pre_rounding_risk_price / A
pre_rounding_risk_atr <= 2.00
```

If `pre_rounding_risk_price > 2.00 * A`, return:

```text
usable = false
reason = SL_TOO_WIDE
```

No weaker-reference retry is allowed.

### 5.12 Tick rounding and post-rounding validity

Use exact decimal-safe arithmetic:

```text
Sstop = rounded_stop = ceil(adjusted_stop / t) * t
```

Rounding is outward for SHORT.

After rounding, all invariants are mandatory:

```text
Sstop is finite
Sstop > 0
Sstop / t is an integer
Sstop = ceil(adjusted_stop / t) * t
Sstop > R
Sstop > E
```

If arithmetic fails or any invariant fails:

```text
usable = false
reason = ROUNDING_ERROR
```

Diagnostic stop prices may be persisted for audit, but they are non-actionable.
No clamp, offset, inward correction, alternate-reference retry, ATR-only
fallback, entry repricing, or exchange-specific repair is permitted.

### 5.13 Post-rounding risk feasibility

```text
post_rounding_risk_price = Sstop - E
```

The post-rounding candidate is feasible only if:

```text
post_rounding_risk_price <= 2.00 * A
```

Equivalent diagnostic:

```text
post_rounding_risk_atr = post_rounding_risk_price / A
post_rounding_risk_atr <= 2.00
```

If `post_rounding_risk_price > 2.00 * A`, return:

```text
usable = false
reason = SL_TOO_WIDE
```

### 5.14 Successful output

Only after all checks pass:

```text
usable = true
reason = AVAILABLE
rounded_stop_price = Sstop
```

## 6. Inputs

| Input | Source | Required semantics |
|---|---|---|
| `direction` | F-005 / Market Handoff | Must be committed `SHORT`. |
| `planned_entry_reference` / `E` | F-008 | Positive certified planned LIMIT entry for the same Market Handoff. |
| `ATR_15m` / `A` | F-003 via Market Handoff | Positive received Q18 ATR export; never recomputed by Position. |
| `tick_size` / `t` | Market Handoff / exchange facts | Positive exact decimal tick size. |
| `references.levels[]` | Market Handoff | Frozen governed structural levels available as-of `matched_at`. |
| `matched_at` | Market Handoff | Cutoff for reference availability. |
| `market_snapshot_at` | Market Handoff | Snapshot identity/time for audit. |
| `sl_context.set_family` | Market Handoff | One of the allowed Set families. |
| `sl_context.thesis_reference_policy` | Market Handoff | `REQUIRED`, `PREFERRED` or `NONE`. |
| `sl_context.thesis_reference_level_id` | Market Handoff | Required/optional/null depending on policy and binding validation. |
| `sl_context.origin_binding` | Market Handoff | Exact producer binding validated before selection. |
| `stop_loss_mode` | Position configuration | Must be `DYNAMIC`. |

## 7. Outputs

F-007 produces `dynamic_sl` with:

```yaml
dynamic_sl:
  methodology:
    id: TT-METH-016
    version: 0.2.1
  snapshot:
    set_result_id:
    matched_at:
    market_snapshot_at:
    direction: SHORT
    planned_entry_reference:
  thesis_context:
    set_family:
    thesis_reference_policy:
    thesis_reference_level_id:
  reference_selection:
    candidate_level_ids_before_ranking: []
    ineligible_level_ids_with_reason: []
    thesis_reference_override_used:
    selected_level_id:
    selected_level_type:
    selected_reference_price:
    selected_reference_timeframe:
    selected_reference_available_at:
    selected_reference_age_seconds:
    reference_priority_rank:
    corroborating_level_ids: []
  volatility:
    atr_15m:
    buffer_atr_multiplier: 0.20
    buffer_price:
    min_distance_atr_multiplier: 0.50
    min_distance_price:
    max_distance_atr: 2.00
  calculation:
    raw_stop_price:
    minimum_stop_price:
    minimum_distance_adjustment_applied:
    adjusted_stop_price:
    rounded_stop_price:
  risk_distance:
    pre_rounding:
      price:
      atr_units:
    post_rounding:
      price:
      pct:
      atr_units:
  feasibility:
    usable:
    reason:
  fallback_used: false
  warnings: []
```

## 8. Units

| Item | Unit |
|---|---|
| `E`, `R`, `A`, `t`, stop prices and price distances | Instrument quote price units |
| ATR risk distances | Dimensionless ATR multiples |
| `post_rounding.pct` | Diagnostic only; formula and serialization not certified by F-007 |
| `available_at`, `matched_at`, `market_snapshot_at` | Timestamps |
| `selected_reference_age_seconds` | Seconds |

## 9. Parameters

| Parameter | Value | Class | Notes |
|---|---:|---|---|
| `BUFFER_ATR_MULTIPLIER` | `0.20` | RESEARCH_PARAMETER | Stop buffer calibration. |
| `MIN_DISTANCE_ATR` | `0.50` | RESEARCH_PARAMETER | Minimum technical stop distance from planned entry. |
| `MAX_DISTANCE_ATR` | `2.00` | RESEARCH_PARAMETER | Maximum risk-distance calibration. |
| `CORROBORATION_DISTANCE_ATR` | `0.25` | RESEARCH_PARAMETER | Diagnostic nearby-level threshold. |

## 10. Domain and Preconditions

F-007 can evaluate only when:

```text
Market Handoff is valid and committed
direction = SHORT
stop_loss_mode = DYNAMIC
planned_entry_reference > 0
ATR_15m > 0
tick_size > 0
sl_context.set_family is allowed
sl_context.thesis_reference_policy is allowed
references.levels[] is available for the same frozen handoff
```

Missing values are never zero-filled.

## 11. Missing / Invalid Behavior

| Condition | Reason |
|---|---|
| `ATR_15m` missing or `<= 0` | `MISSING_ATR` |
| `tick_size` missing or `<= 0` | `MISSING_TICK_SIZE` |
| `planned_entry_reference` missing or `<= 0` | `MISSING_ENTRY_REFERENCE` |
| `set_family` missing/invalid | `MISSING_SET_FAMILY` |
| thesis policy missing/invalid | `MISSING_THESIS_REFERENCE_POLICY` |
| no adverse-side geometry capability | `NO_ADVERSE_SIDE_GEOMETRY` |
| no eligible governed adverse-side reference | `NO_ELIGIBLE_REFERENCE` |
| required thesis reference invalid for any required condition | `THESIS_REFERENCE_INVALID` |
| pre/post risk price exceeds `2.00 * A` | `SL_TOO_WIDE` |
| rounded stop is nonfinite, nonpositive, off grid, not outward, not above `R`, or not above `E` | `ROUNDING_ERROR` |

## 12. Boundaries

F-007 includes:

```text
SHORT adverse-reference selection
SHORT stop-price construction
SHORT outward tick rounding
SHORT pre/post ATR risk-distance feasibility checks
Dynamic SL output/reason/warning production
```

F-007 excludes:

```text
Set direction classification
planned entry selection
LONG stop calculation
take-profit target selection
position size and actual notional construction
minimum risk/reward and net edge
Portfolio approval/rejection
Order Lifecycle submission/cancel/reconcile behavior
live quote marketability
post-only exchange acceptance
desired R:R, leverage, position size, conviction or profitability optimization
```

F-007 consumes F-008 entry and does not recalculate it. If entry and REQUIRED SL
share reference `r`, SHORT entry gives `E >= r`, so that reference fails F-007's
`r > E + t` eligibility and the result is `THESIS_REFERENCE_INVALID`; F-007
must not rebind it.

F-007 certifies only the SHORT stop candidate and feasibility result. F-009
later certifies broader stop/rounding integration and cannot change F-007's
selected reference, rounded candidate or feasibility result while retaining
F-007 approval.

## 13. Precision / Rounding

Use exact decimal-safe arithmetic. Do not use binary floats, epsilon, display
rounding, hidden ATR precision, or recomputed ATR.

Exact comparisons are made in price units where possible:

```text
pre_rounding_risk_price <= 2.00 * A
post_rounding_risk_price <= 2.00 * A
4 * abs(other_level.price - R) <= A
```

Only diagnostics need quotient forms:

```text
pre_rounding_risk_atr = pre_rounding_risk_price / A
post_rounding_risk_atr = post_rounding_risk_price / A
```

The `post_rounding.pct` output is diagnostic only. Its source formula, units
and serialization are not certified here and must not feed selection,
feasibility, sizing or risk/reward decisions.

## 14. Time Semantics

Reference eligibility uses:

```text
available_at <= matched_at
```

The Set handoff remains frozen. If planned entry moves relative to frozen
geometry after Set match, F-007 recomputes candidate adverse-side eligibility
against the planned entry, but the Set itself is not recomputed.

## 15. State, Replay and Restart

F-007 is deterministic from:

```text
frozen Market Handoff
certified F-008 planned_entry_reference
active Dynamic SL configuration
exact numeric policy
candidate ordering defined in this document
```

Replay/restart must restore the same handoff identity and digest, exact
received Q18 ATR, frozen entry and tick, original thesis binding, configuration
identity/version/digest, methodology and numeric-policy pins, constants,
candidate exclusions, sort keys and selected reference. It must not refresh
references, reconstruct ATR, infer direction, repair a dangling binding, retry
a weaker reference, or substitute a new configuration.

## 16. Configuration Pinning

```text
methodology.id = TT-METH-016
methodology.version = 0.2.1
active methodology baseline = v1.2.14
BUFFER_ATR_MULTIPLIER = 0.20
MIN_DISTANCE_ATR = 0.50
MAX_DISTANCE_ATR = 2.00
CORROBORATION_DISTANCE_ATR = 0.25
Market Handoff v4
TT_SET_NUMERIC_V1
```

## 17. Dependencies

| Dependency | Class | Use |
|---|---|---|
| F-003 | CERTIFIED_FORMULA | Supplies certified 15m ATR semantics consumed through Market Handoff. |
| F-005 | CERTIFIED_FORMULA | Supplies certified SHORT direction and Market Handoff/no-handoff boundary. |
| F-008 | CERTIFIED_FORMULA | Supplies certified planned entry reference and limit order price. |
| F-006 | CERTIFIED_FORMULA | Supplies certified LONG Dynamic SL boundary precedent; not used for SHORT arithmetic. |
| Market Handoff v4 | DOCUMENTATION_DEPENDENCY | Supplies frozen direction, timestamps, tick size, ATR, references and `sl_context`. |
| Position Rules Dynamic Stop Loss methodology | DOCUMENTATION_DEPENDENCY | Supplies source formula, selection policy, reason codes and output contract. |
| Dynamic SL constants | RESEARCH_PARAMETER | Calibration defaults requiring empirical validation. |

## 18. Ownership

Position Rules owns F-007. Set owns direction and frozen Market Handoff
production. F-008 owns planned entry selection. F-003 owns ATR calculation.
F-006 owns the certified LONG sibling formula only. Portfolio owns capital
approval/rejection. Order Lifecycle owns order submission/cancel/reconcile
behavior. API/exchange adapters own factual exchange interfaces and exchange
precision facts.

## 19. Pipeline Role

```text
F-005 matched SHORT direction
-> Market Handoff
-> F-008 planned entry
-> F-007 SHORT Dynamic SL candidate
-> F-009 stop integration
-> F-011/F-012 downstream sizing and edge checks
```

## 20. Approved Uses Requested

If approved, F-007 may be used to:

```text
construct the SHORT Dynamic SL candidate
reject SHORT Position Plans whose governed stop is infeasible
provide deterministic stop diagnostics and audit trail
feed later stop integration, sizing and risk/reward formulas
```

## 21. Prohibited Interpretations

F-007 must not be interpreted as:

```text
a profitability finding
a guarantee of exchange acceptance
a guarantee of stop fill
a liquidation-risk model
a position sizing formula
a take-profit formula
a complete risk/reward formula
a permission to move stops inward
a permission to retry weaker references
a permission to synthesize ATR-only stops
a permission to repair handoff producer bindings
```

## 22. Known Limitations

1. The stop is structural and ATR-buffered, but it does not model order-book
   depth, stop-market slippage, liquidation, latency, partial fills or exchange
   outage behavior.
2. The `2 ATR` cap bounds planned price distance, not realized loss, exposure
   or liquidation risk.
3. Family priority and recency rules are deterministic but empirically
   unvalidated.
4. A valid stop candidate does not imply that a complete Position Plan will
   pass target, sizing, fee, risk/reward or Portfolio checks.
5. `post_rounding.pct` remains diagnostic and uncertified for decision use.
6. Tick alignment alone does not satisfy every venue price constraint.

## 23. Research Parameters

```text
BUFFER_ATR_MULTIPLIER = 0.20
MIN_DISTANCE_ATR = 0.50
MAX_DISTANCE_ATR = 2.00
CORROBORATION_DISTANCE_ATR = 0.25
family priority order
recency preference within priority type
```

## 24. Empirical Validation Requirements

Evaluate all SHORT opportunities, including rejections and nonfills, across
symbols, regimes, reference ages, thesis policies and tick/ATR ratios. Use
chronological out-of-sample evidence to measure adverse excursion, stop
frequency/severity, squeeze/gap outcomes, execution costs, funding where
applicable and downstream net results. Candle touches cannot establish fills or
exit ordering. Calibration research is not a certification blocker.

## 25. Edge and Regression Fixtures

### Strict one-tick exclusion

```text
E = 100
t = 0.1
level.price = 100.1

level.price > E + t is false
result = ineligible
```

### Minimum-adjustment equality

```text
E = 100
A = 2
R = 100.6

raw_stop = 101.0
minimum_stop = 101.0
adjusted_stop = 101.0
minimum_distance_adjustment_applied = false
```

### Exact 2 ATR acceptance

```text
E = 100
A = 2
t = 0.1
R = 103.6

raw_stop = 104.0
minimum_stop = 101.0
adjusted_stop = 104.0
rounded_stop = 104.0
post_rounding_risk_price = 4.0
2 * A = 4.0
result = AVAILABLE if all other checks pass
```

### Rounding-induced rejection

```text
E = 100
A = 1.03
t = 0.1
R = 101.85

raw_stop = 102.056
minimum_stop = 100.515
adjusted_stop = 102.056
pre_rounding_risk_price = 2.056
2 * A = 2.06
rounded_stop = 102.1
post_rounding_risk_price = 2.1
result = SL_TOO_WIDE
```

### Tied-ID selection

Two otherwise equal candidates with the same type, same `available_at` and same
price select the lower ascending case-sensitive ordinal Unicode code-point
`level_id`.

### Corrupt binding vs valid preferred fallback

Dangling/conflicting producer binding terminates handoff consumption. A valid
bound `PREFERRED` reference that fails F-007 eligibility records
`INVALID_THESIS_REFERENCE_OVERRIDE` and falls back to the default pool.

### Shared entry/SL reference

If entry and REQUIRED SL share reference `r`, SHORT entry gives `E >= r`, so
`r > E + t` is impossible. The result is `THESIS_REFERENCE_INVALID`, without
rebinding or repricing.

### Restart determinism

Restart with the same frozen handoff, entry, constants, tick, ATR, thesis
bindings and candidate set must reproduce the same selected reference, stop,
warnings and reason. Restart must not refresh data or repair invalid bindings.

## 26. Revision Record

| Cycle | Change | Reason |
|---:|---|---|
| 1 | Added mandatory finite positive rounded stop, tick-grid membership and terminal `ROUNDING_ERROR` for failed post-rounding invariants. | Closes F007-C01. |
| 1 | Replaced unspecified lexical ordering with latest `available_at`, smallest exact `level.price - E`, then ascending case-sensitive ordinal Unicode code-point `level_id`. | Closes F007-C02. |
| 1 | Added handoff identity/provenance/thesis binding validation precedence aligned with certified F-008 and F-006. | Closes F007-C03. |
| 1 | Added exact comparison forms, edge fixtures and restart determinism requirements. | Supports deterministic re-review and future tests. |
