# F-006 SOURCE PACK

## 1. Identity

| Field | Extracted value | Evidence |
|---|---|---|
| Formula ID | F-006 | `docs/FORMULA_METRICS_CATALOG.md` |
| Formula name | Position Rules LONG formula | `docs/FORMULA_METRICS_CATALOG.md` |
| Owner | Position Rules | `docs/FORMULA_METRICS_CATALOG.md` |
| Type | TRADING_FORMULA | `docs/FORMULA_METRICS_CATALOG.md` |
| Formula family | LONG_SHORT | `docs/FORMULA_METRICS_CATALOG.md` |
| Certification status | CERTIFICATION_REQUIRED | `docs/FORMULA_METRICS_CATALOG.md` |
| Backend gate | BLOCK_FINAL_IMPLEMENTATION | `docs/FORMULA_METRICS_CATALOG.md` |
| Catalog canonical-definition pointer | `docs/trading-methodology/methodology/POSITION_RULES.md` :: §37 Mathematical Formula - LONG | `docs/FORMULA_METRICS_CATALOG.md` |
| Catalog note | Includes entry, stop candidate, ATR-risk checks, and tick rounding for LONG. | `docs/FORMULA_METRICS_CATALOG.md` |
| Active methodology baseline | v1.2.14 | `docs/trading-methodology/` |

## 2. Source Index

| # | Source | Section | Authority | Relevance |
|---:|---|---|---|---|
| 1 | `docs/FORMULA_METRICS_CATALOG.md` | F-006 row | CATALOG / GATE | Identifies F-006, owner, scope, canonical pointer and downstream impact. |
| 2 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part III, Dynamic Stop Loss Methodology §§1-3 | POSITION BOUNDARY | Defines Dynamic Stop Loss purpose, Position ownership, core invariant and calibration constants. |
| 3 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part III §§4-13 | INPUTS / ELIGIBILITY | Defines required Market Handoff and Position inputs, supported directions, approved levels, adverse-side eligibility and thesis-reference policy. |
| 4 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part III §§14-21 | REFERENCE SELECTION | Defines LONG default reference priority by Set family, ranking within priority type, audit trail and corroborating-level diagnostics. |
| 5 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part III §§22-30 | STOP FORMULA | Defines ATR buffer, minimum distance, pre-risk check, no weaker-reference retry, no ATR-only fallback, tick rounding, post-rounding structural checks and post-risk check. |
| 6 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part III §§31-36 | AVAILABILITY / OUTPUT | Defines missing-input reasons, entry-drift handling, excluded context, warnings, reason codes and `dynamic_sl` output contract. |
| 7 | `docs/trading-methodology/methodology/POSITION_RULES.md` | §37 Mathematical Formula - LONG | FORMULA SUMMARY | Provides the compact LONG formula with `R`, `A`, `E`, raw/adjusted/rounded stop and ATR risk checks. |
| 8 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part V and consolidation note | PIPELINE / NUMERIC CONTRACT | Confirms Position consumes exact Market Handoff values and does not recompute/seed ATR independently. |
| 9 | `docs/formula-certification/F-003/F-003_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies certified 15m ATR semantics consumed through Market Handoff. |
| 10 | `docs/formula-certification/F-005/F-005_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies certified Set direction classifier and Market Handoff/no-handoff boundary. |
| 11 | `docs/formula-certification/F-008/F-008_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies certified planned entry reference and limit order price consumed by F-006. |

## 3. Purpose and Trading Context

F-006 is the Position Rules-owned LONG Dynamic Stop Loss calculation. It
converts:

```text
frozen Set Market Handoff
+
certified LONG direction
+
certified planned_entry_reference
+
active Position Rules Dynamic Stop Loss configuration
```

into either:

```text
usable Dynamic SL candidate for a LONG Position Plan
```

or:

```text
explicit rejection / unavailable reason
```

F-006 protects the LONG thesis by anchoring the stop beyond governed adverse
market structure, adding ATR noise buffer, enforcing minimum technical
distance, rejecting stops that are too wide, and rounding outward to exchange
tick size. It does not determine whether the Set direction is LONG, choose the
planned entry, determine take profit, compute position size, compute final
risk/reward, approve Portfolio capital, or submit/cancel orders.

## 4. Exact Formula Reconstruction

### Core invariant

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

It is not derived from desired reward/risk, leverage, position size or
conviction. If the structurally correct stop is too wide, Position rejects the
Position Plan and must not move the stop inward.

### Baseline calibration constants

```text
BUFFER_ATR_MULTIPLIER       = 0.20
MIN_DISTANCE_ATR            = 0.50
MAX_DISTANCE_ATR            = 2.00
CORROBORATION_DISTANCE_ATR  = 0.25
```

These are calibration defaults for research, not validated optima.

### Required frozen inputs

From Set Market Handoff:

```text
direction
matched_at
market_snapshot_at
set_match_reference_price
tick_size
ATR_15m
references.levels[]
sl_context.set_family
sl_context.thesis_reference_policy
sl_context.thesis_reference_level_id
```

From Position Rules:

```text
planned_entry_reference
stop_loss_mode = DYNAMIC
```

### Supported direction for this formula

F-006 covers only:

```text
LONG
```

`NONE` is invalid for SL creation. `SHORT` belongs to F-007.

### Approved reference level types

```text
SWING_LOW_15M
SWING_HIGH_15M
SWING_LOW_1H
SWING_HIGH_1H
PREVIOUS_DAY_LOW
PREVIOUS_DAY_HIGH
RANGE_LOW
RANGE_HIGH
```

For the LONG branch, only governed adverse-side lows can become eligible under
the geometry rules below.

### Candidate eligibility recomputed vs planned entry

The Set's cached side is audit-only for Dynamic SL selection. F-006 recomputes
adverse-side eligibility from the actual certified `planned_entry_reference`
with a one-tick exclusion zone.

For LONG:

```text
level.price < planned_entry_reference - tick_size
```

A level within one tick of planned entry is not eligible.

### General level eligibility

A candidate level must satisfy all:

```text
level exists in references.levels[]
available_at <= matched_at
price is finite and > 0
approved level_type
correct adverse-side geometry vs planned_entry_reference
```

No synthetic level is permitted.

### Set family

Read only from:

```text
sl_context.set_family
```

Allowed values:

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

Do not infer it.

### Thesis-reference policy

Read:

```text
sl_context.thesis_reference_policy
```

Allowed values:

```text
REQUIRED
PREFERRED
NONE
```

P4 applies: Position consumes the exact Set origin binding. Default candidate
ranking is only the existing `PREFERRED` / `NONE` calculation fallback; it never
rewrites a thesis reference or resolves a missing producer role.

If policy is `REQUIRED`, `thesis_reference_level_id` must exist, reference an
existing canonical level, be available as-of `matched_at`, and be adverse-side
eligible vs planned entry. If any fail:

```text
usable = false
reason = THESIS_REFERENCE_INVALID
```

No default hierarchy fallback is allowed.

If policy is `PREFERRED` and the thesis reference is eligible:

```text
selected reference = thesis reference
```

If invalid or unavailable:

```text
warning = INVALID_THESIS_REFERENCE_OVERRIDE
continue to default hierarchy
```

If policy is `NONE`, `thesis_reference_level_id` must be null and default
reference ranking is used. If a non-null ID is supplied with `NONE`:

```text
warning = UNUSED_THESIS_REFERENCE_ID
```

### LONG default reference priorities

For `TREND_CONTINUATION` and `GENERIC`:

```text
1. SWING_LOW_15M
2. SWING_LOW_1H
3. PREVIOUS_DAY_LOW
4. RANGE_LOW
```

For `RANGE`:

```text
1. RANGE_LOW
2. SWING_LOW_15M
3. SWING_LOW_1H
4. PREVIOUS_DAY_LOW
```

For `BREAKOUT_RECLAIM`, if policy is `REQUIRED` or `PREFERRED` with a valid
thesis reference, the thesis-reference sections control selection. Otherwise
default:

```text
1. SWING_LOW_15M
2. SWING_LOW_1H
3. PREVIOUS_DAY_LOW
4. RANGE_LOW
```

No free-form breakout reference is created.

### Ranking within same priority type

If multiple eligible levels share the same level type:

```text
1. latest available_at
2. smaller adverse-side distance to planned_entry_reference
3. lexical level_id
```

`age_seconds` is diagnostic only and is not a separate ranking criterion because
it is derived from `available_at`.

### Candidate audit trail

Before selection persist:

```text
candidate_level_ids_before_ranking[]
ineligible_level_ids_with_reason[]
```

For the selected reference also persist:

```text
reference_priority_rank
```

### Corroborating levels

Eligible adverse-side levels corroborate the selected reference if:

```text
abs(other_level.price - selected_reference.price) / ATR_15m <= 0.25
```

Exclude the selected level itself. Output:

```text
corroborating_level_ids[]
```

If non-empty:

```text
warning = MULTIPLE_NEARBY_LEVELS
```

This is diagnostic only.

### Structural invalidation anchor and ATR buffer

The selected reference price is the invalidation anchor. The stop is placed
beyond it.

Let:

```text
R = selected_reference_price
A = ATR_15m
E = planned_entry_reference
t = tick_size
```

For LONG:

```text
buffer_price = 0.20 * A
raw_stop = R - buffer_price
```

### Minimum technical distance

For LONG:

```text
minimum_distance_price = 0.50 * A
minimum_stop = E - minimum_distance_price
adjusted_stop = min(raw_stop, minimum_stop)
```

Persist:

```text
minimum_distance_adjustment_applied = true | false
```

### Pre-rounding risk distance

For LONG:

```text
pre_rounding_risk_price = E - adjusted_stop
pre_rounding_risk_atr = pre_rounding_risk_price / A
```

If:

```text
pre_rounding_risk_atr > 2.00
```

return:

```text
SL_TOO_WIDE
```

No alternative weaker reference retry is allowed. Once the structurally
highest-priority eligible reference is selected, F-006 calculates and validates
that stop. It must not choose a lower-priority reference solely to make the
trade cheaper.

If no eligible governed adverse-side reference exists:

```text
NO_ELIGIBLE_REFERENCE
```

No ATR-only fallback exists.

### Tick rounding

Use decimal-safe arithmetic.

For LONG:

```text
rounded_stop = floor(adjusted_stop / t) * t
```

Rounding is always outward.

### Post-rounding structural checks

For LONG:

```text
rounded_stop < R
rounded_stop < E
```

Violation:

```text
ROUNDING_ERROR
```

### Post-rounding risk distance

For LONG:

```text
post_rounding_risk_price = E - rounded_stop
post_rounding_risk_atr = post_rounding_risk_price / A
```

Final feasibility rule:

```text
if post_rounding_risk_atr > 2.00:
    usable = false
    reason = SL_TOO_WIDE
```

Tick rounding cannot silently push the final stop beyond the maximum
risk-distance constraint.

## 5. Inputs

| Input | Source | Required semantics |
|---|---|---|
| `direction` | F-005 / Market Handoff | Must be committed `LONG`; `NONE` invalid and `SHORT` belongs to F-007. |
| `planned_entry_reference` / `E` | F-008 | Positive certified planned LIMIT entry for the same Market Handoff. |
| `ATR_15m` / `A` | F-003 via Market Handoff | Positive received Q18 ATR export; Position must not recompute or recover hidden precision. |
| `tick_size` / `t` | Market Handoff / exchange facts | Positive decimal tick size. |
| `references.levels[]` | Market Handoff | Frozen governed structural levels available as-of `matched_at`. |
| `matched_at` | Market Handoff | Cutoff for reference availability. |
| `market_snapshot_at` | Market Handoff | Snapshot identity/time for audit. |
| `sl_context.set_family` | Market Handoff | One of the allowed Set families; missing/invalid is unavailable. |
| `sl_context.thesis_reference_policy` | Market Handoff | `REQUIRED`, `PREFERRED` or `NONE`; missing/invalid is unavailable. |
| `sl_context.thesis_reference_level_id` | Market Handoff | Required/optional/null depending on policy. |
| `stop_loss_mode` | Position configuration | Must be `DYNAMIC` for this formula. |

## 6. Outputs

F-006 produces a `dynamic_sl` candidate with:

```text
selected_level_id
selected_level_type
selected_reference_price
reference_priority_rank
raw_stop_price
minimum_stop_price
minimum_distance_adjustment_applied
adjusted_stop_price
rounded_stop_price
pre_rounding_risk_price
pre_rounding_risk_atr
post_rounding_risk_price
post_rounding_risk_atr
usable
reason
warnings[]
```

The active output contract also contains snapshot, thesis context, reference
selection audit trail, volatility fields, corroborating levels, percent
diagnostic under post-rounding risk distance, and `fallback_used: false`.

## 7. Units

| Item | Unit |
|---|---|
| `E`, `R`, `A`, `t`, stop prices and price distances | Instrument quote price units |
| ATR risk distances | Dimensionless ATR multiples |
| Post-rounding percent diagnostic | Percent or percentage-style diagnostic as defined by the output contract; exact source formula not specified in the extracted F-006 source text |
| `available_at`, `matched_at`, `market_snapshot_at` | Timestamps |
| `selected_reference_age_seconds` | Seconds |

## 8. Parameters

| Parameter | Value | Class | Notes |
|---|---:|---|---|
| `BUFFER_ATR_MULTIPLIER` | `0.20` | RESEARCH_PARAMETER | Calibration default; not validated optimum. |
| `MIN_DISTANCE_ATR` | `0.50` | RESEARCH_PARAMETER | Minimum technical stop distance from planned entry. |
| `MAX_DISTANCE_ATR` | `2.00` | RESEARCH_PARAMETER | Maximum allowed stop distance before/after rounding. |
| `CORROBORATION_DISTANCE_ATR` | `0.25` | RESEARCH_PARAMETER | Diagnostic nearby-level threshold. |

## 9. Thresholds

```text
level.price < planned_entry_reference - tick_size
pre_rounding_risk_atr <= 2.00
post_rounding_risk_atr <= 2.00
rounded_stop < selected_reference_price
rounded_stop < planned_entry_reference
abs(other_level.price - selected_reference.price) / ATR_15m <= 0.25
```

Risk-distance rejection uses `>` against `2.00`, so exactly `2.00 ATR` is
accepted if all other checks pass.

## 10. Sign and Direction Semantics

F-006 is LONG-only. Its stop lies below the planned entry and below the selected
adverse reference after outward rounding. A lower stop increases LONG loss
distance, so floor rounding is outward for LONG. F-006 does not infer LONG from
score or price movement; the LONG direction must already be established by
F-005 and present in the immutable Market Handoff.

## 11. Domain and Preconditions

F-006 can evaluate only when:

```text
Market Handoff is valid and committed
direction = LONG
stop_loss_mode = DYNAMIC
planned_entry_reference > 0
ATR_15m > 0
tick_size > 0
sl_context.set_family is allowed
sl_context.thesis_reference_policy is allowed
references.levels[] is available for the same frozen handoff
```

Missing values are never zero-filled.

## 12. Boundaries

F-006 includes:

```text
LONG adverse-reference selection
LONG stop-price construction
LONG outward tick rounding
LONG pre/post ATR risk-distance feasibility checks
Dynamic SL output/reason/warning production
```

F-006 excludes:

```text
Set direction classification
planned entry selection
SHORT stop calculation
take-profit target selection
position size and actual notional construction
minimum risk/reward and net edge
Portfolio approval/rejection
Order Lifecycle submission/cancel/reconcile behavior
live quote marketability
post-only exchange acceptance
desired R:R, leverage, position size, conviction or profitability optimization
```

Catalog F-009 separately covers "Stop calculation and stop rounding" across
LONG/SHORT and Part V tick-size alignment. The extracted F-006 source includes
LONG stop candidate construction and LONG tick rounding; F-009 remains a
downstream/broader stop-boundary formula and is not certified by this Source
Pack.

## 13. Precision

The source requires decimal-safe arithmetic. F-006 consumes exact canonical
received Market Handoff decimals and the certified F-008 planned entry. It must
not use display-rounded values, hidden ATR precision, binary floating-point
shortcuts, epsilon comparisons, or recomputed ATR.

Tick rounding:

```text
rounded_stop = floor(adjusted_stop / tick_size) * tick_size
```

The Source Pack did not locate a separate F-006-specific quotient rounding rule
for `post_rounding.risk_distance.pct`.

## 14. Time Semantics

Reference eligibility uses:

```text
available_at <= matched_at
```

The Set handoff remains frozen. If planned entry moves relative to frozen
geometry after Set match, candidate adverse-side eligibility is recomputed
against the planned entry, but the Set itself is not recomputed.

## 15. State, Replay and Restart

F-006 is deterministic from the frozen Market Handoff, F-008 planned entry,
active Dynamic SL configuration, and exact numeric policy. Required audit
fields include the selected level, rejected candidates with reasons,
thesis-reference override state, corroborating levels, stop calculation stages,
risk distances, warnings and final feasibility reason.

Replay/restart must preserve the same input handoff, reference availability
cutoff, selected `planned_entry_reference`, configuration constants, tick size,
ATR value and candidate ordering.

## 16. Version and Configuration Pinning

Known pins from source:

```text
methodology.id = TT-METH-016
methodology.version = 0.2.1
active methodology baseline = v1.2.14
BUFFER_ATR_MULTIPLIER = 0.20
MIN_DISTANCE_ATR = 0.50
MAX_DISTANCE_ATR = 2.00
CORROBORATION_DISTANCE_ATR = 0.25
Market Handoff v4 / TT_SET_NUMERIC_V1 consumed via certified upstream specs
```

## 17. Ownership

Position Rules owns F-006. Set owns direction and frozen Market Handoff
production. F-008 owns planned entry selection. F-003 owns ATR calculation.
Portfolio owns capital approval/rejection. Order Lifecycle owns order
submission/cancel/reconcile behavior. API/exchange adapters own factual
exchange interfaces and exchange precision facts.

## 18. Downstream Consumers

Direct downstream:

```text
F-009 — Stop calculation and stop rounding
Position Plan / protective stop candidate
```

Indirect downstream:

```text
F-011 — Position size, quantity, and actual notional construction
F-012 — Risk/reward and minimum net edge calculation
Order Lifecycle protective exit construction
```

## 19. Dependencies

| Dependency | Class | Use |
|---|---|---|
| F-003 | CERTIFIED_FORMULA | Supplies certified 15m ATR semantics consumed through Market Handoff. |
| F-005 | CERTIFIED_FORMULA | Supplies certified LONG direction and Market Handoff/no-handoff boundary. |
| F-008 | CERTIFIED_FORMULA | Supplies certified planned entry reference and limit order price. |
| Market Handoff v4 | DOCUMENTATION_DEPENDENCY | Supplies frozen direction, timestamps, tick size, ATR, references and `sl_context`. |
| Position Rules Dynamic Stop Loss methodology | DOCUMENTATION_DEPENDENCY | Supplies source formula, selection policy, reason codes and output contract. |
| `BUFFER_ATR_MULTIPLIER` | RESEARCH_PARAMETER | Stop buffer calibration. |
| `MIN_DISTANCE_ATR` | RESEARCH_PARAMETER | Minimum stop-distance calibration. |
| `MAX_DISTANCE_ATR` | RESEARCH_PARAMETER | Maximum risk-distance calibration. |
| `CORROBORATION_DISTANCE_ATR` | RESEARCH_PARAMETER | Diagnostic nearby-level calibration. |

## 20. Existing Worked Examples

No numeric worked example was found in the extracted F-006 source text.

## 21. Explicit Source Gaps

1. The catalog says F-006 includes "entry, stop candidate, ATR-risk checks, and tick rounding for LONG," while F-008 already certifies planned entry selection. The likely boundary is that F-006 consumes F-008 entry rather than recalculating it, but Council should verify this boundary.
2. F-009 separately covers stop calculation and stop rounding. The F-006 source itself includes LONG stop construction and rounding. Council should verify whether F-006 may certify the LONG branch candidate while F-009 later certifies cross-side stop/rounding integration.
3. The output contract includes a post-rounding risk-distance `pct` field, but the extracted F-006 source text does not specify its exact formula.
4. The source does not include a numeric worked example for tie/corner cases around one-tick exclusion, exact 2.00 ATR distance, or rounding-induced `SL_TOO_WIDE`.

## 22. Reviewer Handoff Summary

F-006 appears to be a complete LONG Dynamic Stop Loss candidate:

```text
R = selected adverse LONG reference
A = received ATR_15m
E = certified planned_entry_reference
t = tick_size

raw_stop = R - 0.20 * A
minimum_stop = E - 0.50 * A
adjusted_stop = min(raw_stop, minimum_stop)

pre_rounding_risk_atr = (E - adjusted_stop) / A
if pre_rounding_risk_atr > 2.00:
    reject SL_TOO_WIDE

rounded_stop = floor(adjusted_stop / t) * t

require rounded_stop < R
require rounded_stop < E

post_rounding_risk_atr = (E - rounded_stop) / A
if post_rounding_risk_atr > 2.00:
    reject SL_TOO_WIDE
```

The Council should review specification correctness, determinism, dependency
compatibility, ownership boundaries and trading fitness for the LONG stop-loss
role. Special attention should be paid to F-006/F-008 and F-006/F-009
boundaries, exact handling of `pct` diagnostics, and whether the extracted
research parameters and no-fallback/no-retry semantics are complete enough for
certification.
