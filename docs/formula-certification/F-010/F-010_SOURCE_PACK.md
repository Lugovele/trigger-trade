# F-010 SOURCE PACK

## 1. Identity

| Field | Extracted value | Evidence |
|---|---|---|
| Formula ID | F-010 | `docs/FORMULA_METRICS_CATALOG.md` |
| Formula name | Dynamic Take Profit selection and rounding | `docs/FORMULA_METRICS_CATALOG.md` |
| Owner | Position Rules | `docs/FORMULA_METRICS_CATALOG.md` |
| Type | TRADING_FORMULA | `docs/FORMULA_METRICS_CATALOG.md` |
| Formula family | DYNAMIC_TAKE | `docs/FORMULA_METRICS_CATALOG.md` |
| Certification status | CERTIFICATION_REQUIRED | `docs/FORMULA_METRICS_CATALOG.md` |
| Backend gate | BLOCK_FINAL_IMPLEMENTATION | `docs/FORMULA_METRICS_CATALOG.md` |
| Catalog canonical-definition pointer | `docs/trading-methodology/methodology/POSITION_RULES.md` :: Part IV Dynamic Take Profit and §45-§46 algorithms | `docs/FORMULA_METRICS_CATALOG.md` |
| Catalog note | Includes favorable-side eligibility, priority, distance ranking, ATR constraints, and tick rounding. | `docs/FORMULA_METRICS_CATALOG.md` |
| Active methodology baseline | v1.2.14 | `docs/trading-methodology/` |

## 2. Source Index

| # | Source | Section | Authority | Relevance |
|---:|---|---|---|---|
| 1 | `docs/FORMULA_METRICS_CATALOG.md` | F-010 row and queue | CATALOG / GATE | Identifies F-010, dependencies F-008 and N-004, and DYNAMIC_TAKE scope. |
| 2 | `docs/FORMULA_METRICS_CATALOG.md` | T-003 row | RESEARCH_PARAMETER | Fixed/minimum take-profit thresholds must not replace certified Dynamic TP logic. |
| 3 | `docs/trading-methodology/methodology/POSITION_RULES.md` | §12 Dynamic Take Profit semantics | POSITION BOUNDARY | Routes dynamic TP mode to the approved Dynamic Take Profit methodology. |
| 4 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part IV §§1-4 | PURPOSE / INPUTS | Defines Dynamic TP purpose, invariant, constants and required inputs. |
| 5 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part IV §§5-13 | ELIGIBILITY / THESIS POLICY | Defines supported directions, target level types, favorable-side eligibility, Set family and thesis-reference policy. |
| 6 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part IV §§14-18 | HIERARCHY / RANKING | Defines Set-family target hierarchies and ranking within same priority type. |
| 7 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part IV §§19-24 | REACHABILITY / PRECEDENCE | Defines distance calculations, reachability bands, sequential selection, too-close and too-far behavior, and failure precedence. |
| 8 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part IV §§25-33 | FALLBACKS / ROUNDING | Defines no ATR-only fallback, no SL-derived target, audit trail, inward tick rounding, post-rounding geometry and distance checks. |
| 9 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part IV §§34-40 | EXCLUDED CONTEXT / BOUNDARIES | Excludes liquidity, flow, OI, BTC/breadth, direction score, session context and partial TP from baseline TP modification. |
| 10 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part IV §§41-48 | REASONS / OUTPUT / ALGORITHMS / RESEARCH | Defines warning codes, reason codes, missing-input handling, output contract, LONG/SHORT algorithms and research reporting. |
| 11 | `docs/formula-certification/F-008/F-008_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies certified planned entry, tick/ATR/reference handoff consumption boundary. |
| 12 | `docs/formula-certification/F-009/F-009_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies certified stop integration boundary; TP must not be derived from SL. |
| 13 | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` | §§1-2 | APPROVED_POLICY | Defines exact arithmetic and `floor_q`/`ceil_q` quantizers for price ticks. |
| 14 | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` | Instrument metadata | APPROVED_POLICY | Supplies N-004 instrument tick facts and provenance. |

## 3. Purpose and Trading Context

F-010 is the Position Rules-owned Dynamic Take Profit formula. It converts:

```text
frozen Set Market Handoff
+
certified planned_entry_reference
+
active Position Rules TP configuration
```

into either:

```text
usable Dynamic TP candidate
```

or:

```text
explicit rejection / unavailable reason
```

F-010 chooses one primary structurally governed favorable-side target, checks
ATR-normalized reachability, rounds the target inward toward realizability, and
returns the rounded TP candidate for later geometry, gross R:R, net-edge and
Order Spec stages.

F-010 does not derive TP from stop distance, desired R:R, desired profit
percentage, position size, leverage or direction score. R:R and net economics
are evaluated later.

## 4. Exact Formula Reconstruction

### Core invariant

Dynamic TP is:

```text
governed favorable-side structural target
+
ATR-normalized reachability
+
tick-normalized realizability
```

It is not derived from:

```text
SL distance
fixed R:R
desired profit %
position size
leverage
direction score
```

### Baseline calibration constants

```text
MIN_TP_DISTANCE_ATR = 0.75
MAX_TP_DISTANCE_ATR = 4.00
```

These are calibration defaults for research, not validated optima.

### Required inputs

From Set handoff:

```text
direction
matched_at
market_snapshot_at
tick_size
ATR_15m
references.levels[]
tp_context.set_family
tp_context.thesis_reference_policy
tp_context.thesis_reference_level_id
```

From Position Rules:

```text
planned_entry_reference
take_profit_mode = DYNAMIC
```

### Supported directions

```text
LONG
SHORT
```

`NONE` is invalid for Dynamic TP creation.

### Approved target level types

```text
SWING_HIGH_15M
SWING_LOW_15M
SWING_HIGH_1H
SWING_LOW_1H
PREVIOUS_DAY_HIGH
PREVIOUS_DAY_LOW
RANGE_HIGH
RANGE_LOW
```

### Favorable-side eligibility recomputed vs planned entry

The Set cached side is audit-only for final TP selection.

LONG:

```text
level.price > planned_entry_reference + tick_size
```

SHORT:

```text
level.price < planned_entry_reference - tick_size
```

A level within one tick of planned entry is ineligible.

### General target eligibility

A level must satisfy:

```text
exists in references.levels[]
available_at <= matched_at
price finite and > 0
approved level_type
correct favorable-side geometry vs planned_entry_reference
```

No synthetic target may be invented.

### Set family

Read only from:

```text
tp_context.set_family
```

Allowed:

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

No inference is allowed.

### Thesis-reference policy

Read:

```text
tp_context.thesis_reference_policy
```

Allowed:

```text
REQUIRED
PREFERRED
NONE
```

P4 applies: Position consumes the exact Set origin binding. Default hierarchy is
calculation fallback only; it never rewrites a thesis reference or resolves a
missing producer role.

If policy is `REQUIRED`, the referenced level must exist, be available as-of
`matched_at`, be favorable-side eligible vs planned entry, and lie within the
approved reachability band. If not:

```text
usable = false
reason = THESIS_REFERENCE_INVALID
```

No fallback.

If `PREFERRED` target is fully eligible and reachable:

```text
selected target = thesis reference
```

If invalid or outside reachability band:

```text
warning = INVALID_THESIS_REFERENCE_OVERRIDE
continue with default target hierarchy
```

If policy is `NONE`:

```text
thesis_reference_level_id = null
default hierarchy applies
```

### Target hierarchies

TREND_CONTINUATION and GENERIC:

```text
LONG:
1. SWING_HIGH_15M
2. SWING_HIGH_1H
3. PREVIOUS_DAY_HIGH
4. RANGE_HIGH

SHORT:
1. SWING_LOW_15M
2. SWING_LOW_1H
3. PREVIOUS_DAY_LOW
4. RANGE_LOW
```

RANGE:

```text
LONG:
1. RANGE_HIGH
2. SWING_HIGH_15M
3. SWING_HIGH_1H
4. PREVIOUS_DAY_HIGH

SHORT:
1. RANGE_LOW
2. SWING_LOW_15M
3. SWING_LOW_1H
4. PREVIOUS_DAY_LOW
```

BREAKOUT_RECLAIM:

```text
If a valid REQUIRED/PREFERRED thesis target exists, thesis-reference rules
control selection. Otherwise use GENERIC hierarchy.
```

No free-form breakout target is permitted.

### Ranking within same priority type

If multiple eligible levels share the same level type:

```text
1. latest available_at
2. smaller favorable-side distance to planned_entry_reference
3. lexical level_id
```

`age_seconds` remains diagnostic only.

### Distance calculation

For every structurally eligible favorable-side level:

```text
distance_price = abs(level.price - planned_entry_reference)
distance_pct = 100 * distance_price / planned_entry_reference
distance_atr = distance_price / ATR_15m
```

### Reachability bands

```text
TOO_CLOSE: distance_atr < 0.75
ELIGIBLE:  0.75 <= distance_atr <= 4.00
TOO_FAR:   distance_atr > 4.00
```

### Sequential structural selection rule

Target selection must preserve structural priority:

```text
1. construct the Set-family structural hierarchy
2. evaluate candidates in priority order
3. for each candidate:

   if basic geometry is invalid:
       record ineligible
       continue

   calculate distance_atr

   if distance_atr < 0.75:
       record TOO_CLOSE
       continue

   if 0.75 <= distance_atr <= 4.00:
       select target
       stop

   if distance_atr > 4.00:
       record TOO_FAR
       terminate selection
       reject Dynamic TP
```

Distance does not globally reorder structural targets.

### Too-close behavior

If a higher-priority target is `TOO_CLOSE`:

```text
record target in too_close_level_ids[]
increment too_close_skipped_count
continue to next structural target
```

This is the only baseline distance condition that permits continuing down the
hierarchy.

### Too-far behavior

If the next structurally valid target has:

```text
distance_atr > 4.00
```

return:

```text
usable = false
reason = TARGET_TOO_FAR
```

Persist:

```text
selection_terminated_by_too_far = true
first_too_far_level_id
first_too_far_distance_atr
```

Do not select a lower-priority target after a TOO_FAR termination.

### Failure-reason precedence

```text
missing required primitive
-> NO_FAVORABLE_SIDE_GEOMETRY if capability absent
-> NO_ELIGIBLE_REFERENCE if zero basic eligible references
-> traverse structural hierarchy
   -> TOO_CLOSE may continue
   -> ELIGIBLE selects
   -> TOO_FAR terminates as TARGET_TOO_FAR
-> hierarchy exhausted after TOO_CLOSE only
   -> NO_REACHABLE_TARGET
```

### Fallback exclusions

No ATR-only fallback:

```text
TP = entry +/- K * ATR
```

No SL-derived target:

```text
TP = entry + N * SL_distance
```

SL output may be used later only by Joint TP/SL Feasibility.

### Candidate audit trail

Persist:

```text
candidate_level_ids_before_distance_filter[]
ineligible_level_ids_with_reason[]
too_close_level_ids[]
too_close_skipped_count
too_far_level_ids[]
selection_terminated_by_too_far
first_too_far_level_id
first_too_far_distance_atr
eligible_target_level_ids[]
selected_target_priority_rank
alternative_eligible_target_level_ids[]
```

### Tick rounding

TP is rounded inward toward realizability, never beyond the structural target.

LONG:

```text
rounded_tp = floor(selected_target_price / tick_size) * tick_size
```

SHORT:

```text
rounded_tp = ceil(selected_target_price / tick_size) * tick_size
```

Use decimal-safe arithmetic.

### Post-rounding geometry validation

LONG:

```text
rounded_tp > planned_entry_reference
rounded_tp <= selected_target_price
```

SHORT:

```text
rounded_tp < planned_entry_reference
rounded_tp >= selected_target_price
```

Violation:

```text
ROUNDING_ERROR
```

### Post-rounding distance validation

Recompute:

```text
rounded_distance_atr = abs(rounded_tp - planned_entry_reference) / ATR_15m
```

If:

```text
rounded_distance_atr < 0.75
```

return:

```text
TARGET_TOO_CLOSE_AFTER_ROUNDING
```

Also require:

```text
rounded_distance_atr <= 4.00
```

If violated due to arithmetic/precision inconsistency:

```text
ROUNDING_ERROR
```

### LONG algorithm summary

```text
E = planned entry
A = ATR_15m

for target in LONG structural priority order:
    if target.price <= E + tick:
        record ineligible
        continue

    distance_atr = (target.price - E) / A

    if distance_atr < 0.75:
        record TOO_CLOSE
        continue

    if distance_atr > 4.00:
        record TOO_FAR
        TARGET_TOO_FAR
        stop

    selected target = target
    break

if zero basic eligible references:
    NO_ELIGIBLE_REFERENCE
elif no target selected and no TOO_FAR termination:
    NO_REACHABLE_TARGET

raw_tp = selected target price
rounded_tp = floor(raw_tp / tick) * tick

recompute rounded distance

if rounded distance < 0.75 ATR:
    TARGET_TOO_CLOSE_AFTER_ROUNDING
else:
    AVAILABLE
```

### SHORT algorithm summary

```text
E = planned entry
A = ATR_15m

for target in SHORT structural priority order:
    if target.price >= E - tick:
        record ineligible
        continue

    distance_atr = (E - target.price) / A

    if distance_atr < 0.75:
        record TOO_CLOSE
        continue

    if distance_atr > 4.00:
        record TOO_FAR
        TARGET_TOO_FAR
        stop

    selected target = target
    break

if zero basic eligible references:
    NO_ELIGIBLE_REFERENCE
elif no target selected and no TOO_FAR termination:
    NO_REACHABLE_TARGET

raw_tp = selected target price
rounded_tp = ceil(raw_tp / tick) * tick

recompute rounded distance

if rounded distance < 0.75 ATR:
    TARGET_TOO_CLOSE_AFTER_ROUNDING
else:
    AVAILABLE
```

## 5. Inputs

| Input | Source | Required semantics |
|---|---|---|
| `direction` | F-005 / Market Handoff | Must be `LONG` or `SHORT`; `NONE` invalid. |
| `planned_entry_reference` / `E` | F-008 | Certified positive planned entry for the same handoff/cycle. |
| `tick_size` | N-004 / Market Handoff | Positive price tick quantum with provenance. |
| `ATR_15m` / `A` | F-003 via Market Handoff | Positive received ATR; do not recompute. |
| `references.levels[]` | Market Handoff | Frozen governed structural levels available as-of `matched_at`. |
| `tp_context.set_family` | Market Handoff | One of allowed Set families. |
| `tp_context.thesis_reference_policy` | Market Handoff | `REQUIRED`, `PREFERRED`, or `NONE`. |
| `tp_context.thesis_reference_level_id` | Market Handoff | Required/optional/null depending on policy. |
| `take_profit_mode` | Position configuration | Must be `DYNAMIC` for F-010. |

## 6. Outputs

Primary output:

```text
rounded_target_price
```

Dynamic TP output contract:

```yaml
dynamic_tp:
  methodology:
    id: TT-METH-017
    version: 0.2.2
  snapshot:
    set_result_id:
    matched_at:
    market_snapshot_at:
    direction:
    planned_entry_reference:
  thesis_context:
    set_family:
    thesis_reference_policy:
    thesis_reference_level_id:
  target_selection:
    candidate_level_ids_before_distance_filter: []
    ineligible_level_ids_with_reason: []
    too_close_level_ids: []
    too_close_skipped_count:
    too_far_level_ids: []
    selection_terminated_by_too_far:
    first_too_far_level_id:
    first_too_far_distance_atr:
    eligible_target_level_ids: []
    selected_level_id:
    selected_level_type:
    selected_target_price:
    selected_target_timeframe:
    selected_target_available_at:
    selected_target_age_seconds:
    selected_target_priority_rank:
    alternative_eligible_target_level_ids: []
  reachability:
    atr_15m:
    min_distance_atr: 0.75
    max_distance_atr: 4.00
    raw_distance:
      price:
      pct:
      atr_units:
    rounded_distance:
      price:
      pct:
      atr_units:
  calculation:
    raw_target_price:
    rounded_target_price:
  feasibility:
    usable:
    reason:
  fallback_used: false
  warnings: []
```

## 7. Units

| Item | Unit |
|---|---|
| Entry, level price, raw target, rounded target, tick size, distance price | Instrument quote price units |
| ATR distance | Dimensionless ATR multiples |
| `distance_pct` | Percent units; numeric `1` means one percent |
| timestamps / ages | Source timestamps / seconds |

## 8. Parameters

| Parameter | Value | Class | Notes |
|---|---:|---|---|
| `MIN_TP_DISTANCE_ATR` | `0.75` | RESEARCH_PARAMETER | Minimum reachability/meaningfulness distance, not profitability guarantee. |
| `MAX_TP_DISTANCE_ATR` | `4.00` | RESEARCH_PARAMETER | Maximum reachability cap; too-far terminates selection. |
| `T-003` | configurable | RESEARCH_PARAMETER | Cataloged fixed/minimum TP thresholds; must not replace Dynamic TP logic. |

## 9. Thresholds

```text
LONG favorable side: level.price > E + tick_size
SHORT favorable side: level.price < E - tick_size
TOO_CLOSE: distance_atr < 0.75
ELIGIBLE: 0.75 <= distance_atr <= 4.00
TOO_FAR: distance_atr > 4.00
post-rounding minimum: rounded_distance_atr >= 0.75
post-rounding maximum: rounded_distance_atr <= 4.00
```

## 10. Sign and Direction Semantics

LONG targets are above entry and round down inward:

```text
rounded_tp > E
rounded_tp <= selected_target_price
```

SHORT targets are below entry and round up inward:

```text
rounded_tp < E
rounded_tp >= selected_target_price
```

F-010 does not determine LONG/SHORT direction; it consumes the immutable
direction from the Market Handoff.

## 11. Domain and Preconditions

F-010 can evaluate only when:

```text
direction is LONG or SHORT
take_profit_mode = DYNAMIC
planned_entry_reference > 0
ATR_15m > 0
tick_size > 0
tp_context.set_family is allowed
tp_context.thesis_reference_policy is allowed
references.levels[] are available for the frozen handoff
```

Missing values are never zero-filled.

## 12. Boundaries

F-010 includes:

```text
Dynamic TP target eligibility
target hierarchy traversal
reachability classification
too-close skip behavior
too-far terminal behavior
target selection
inward tick rounding
post-rounding geometry and reachability checks
Dynamic TP reason/warning/audit output
```

F-010 excludes:

```text
Entry selection
Stop calculation
fixed take-profit formula
gross R:R and Minimum Net Edge
position size and notional
Portfolio approval/rejection
Order Lifecycle execution/fill management
partial TP / multi-target exits
liquidity/session/flow/BTC/score-based TP modification
```

## 13. Precision

Use decimal-safe exact arithmetic. No binary floats, display rounding, hidden
ATR precision, epsilon comparisons or intermediate rounding.

Inward tick rounding:

```text
LONG:  rounded_tp = floor(selected_target_price / tick_size) * tick_size
SHORT: rounded_tp = ceil(selected_target_price / tick_size) * tick_size
```

## 14. Time Semantics

Reference availability uses:

```text
available_at <= matched_at
```

Dynamic TP consumes the frozen Market Handoff and F-008 planned entry for the
same decision cycle. It does not refresh levels, ATR, tick size or direction
after Set match.

## 15. State, Replay and Restart

Replay/restart must preserve:

```text
decision_cycle_id
set_result_id
matched_at
market_snapshot_at
direction
planned_entry_reference
tick_size and provenance
ATR_15m
tp_context
references.levels[]
candidate classifications
selection ordering
raw and rounded target calculations
warnings and reasons
```

Restart must reproduce the same target or rejection without refreshing market
data, repairing bindings, recomputing ATR, changing configuration or choosing a
lower-priority target after a terminal too-far result.

## 16. Version and Configuration Pinning

Known pins:

```text
methodology.id = TT-METH-017
methodology.version = 0.2.2
active methodology baseline = v1.2.14
MIN_TP_DISTANCE_ATR = 0.75
MAX_TP_DISTANCE_ATR = 4.00
Market Handoff v4 / TT_SET_NUMERIC_V1
N-004 tick-size evidence
F-008 final specification
```

## 17. Ownership

Position Rules owns F-010. Set owns direction, reference geometry, `tp_context`
and frozen Market Handoff. F-008 owns planned entry. F-009 owns stop
integration and may only be used later by joint TP/SL feasibility, not by target
selection. Portfolio owns capital approval. Order Lifecycle owns execution and
fills. API/instrument facts own tick-size evidence under N-004.

## 18. Downstream Consumers

Direct downstream:

```text
Position geometry gate
F-011 — Position size, quantity, and actual notional construction
F-012 — Risk/reward and minimum net edge calculation
Order Spec take_profit block
Order Lifecycle target-exit handling after authorization
```

## 19. Dependencies

| Dependency | Class | Use |
|---|---|---|
| F-008 | CERTIFIED_FORMULA | Supplies certified planned entry and handoff consumption boundary. |
| F-003 | CERTIFIED_FORMULA | Supplies certified 15m ATR semantics consumed through Market Handoff. |
| N-004 | APPROVED_POLICY | Tick-size normalization and instrument tick facts. |
| Market Handoff v4 | DOCUMENTATION_DEPENDENCY | Supplies direction, ATR, tick, references and `tp_context`. |
| T-003 | RESEARCH_PARAMETER | Fixed/minimum TP thresholds; must not replace Dynamic TP logic. |
| Position Rules Part IV | DOCUMENTATION_DEPENDENCY | Source for Dynamic TP methodology. |

## 20. Existing Worked Examples

No numeric worked example was found in the extracted F-010 source text.

## 21. Explicit Source Gaps

1. Ranking within the same priority type uses "lexical level_id" without
   specifying comparator/collation. F-006/F-007 resolved analogous gaps with
   case-sensitive ordinal Unicode code-point ordering.
2. Thesis-reference policy text does not explicitly say how to handle invalid
   producer bindings, dangling IDs, duplicate/conflicting canonical IDs, or
   `NONE` with a non-null thesis ID/binding. F-006/F-007 resolved analogous
   handoff-validation precedence.
3. Tick rounding requires geometry validation but does not explicitly require
   finite positive rounded TP, exact tick-grid membership, or terminal handling
   for nonpositive rounded output.
4. The source says lower-priority eligible levels may be persisted as
   diagnostics only if evaluated separately after primary decision; it does not
   fully define ordering/audit rules for that optional diagnostic pass.
5. The source contains no worked examples for strict one-tick exclusion,
   too-close skip, too-far termination, exact 0.75/4.00 boundaries, or rounding
   causing `TARGET_TOO_CLOSE_AFTER_ROUNDING`.

## 22. Reviewer Handoff Summary

F-010 appears to be a complete Dynamic TP candidate:

```text
E = certified planned entry
A = received ATR_15m
t = tick_size

Traverse Set-family hierarchy sequentially.

For LONG:
    basic favorable side: target.price > E + t
    distance_atr = (target.price - E) / A
    selected target rounds down:
        rounded_tp = floor(target.price / t) * t
    require rounded_tp > E and rounded_tp <= target.price

For SHORT:
    basic favorable side: target.price < E - t
    distance_atr = (E - target.price) / A
    selected target rounds up:
        rounded_tp = ceil(target.price / t) * t
    require rounded_tp < E and rounded_tp >= target.price

Reachability:
    distance_atr < 0.75 -> TOO_CLOSE and continue
    0.75 <= distance_atr <= 4.00 -> select and stop
    distance_atr > 4.00 -> TARGET_TOO_FAR and stop/reject

After rounding:
    rounded_distance_atr < 0.75 -> TARGET_TOO_CLOSE_AFTER_ROUNDING
    rounded_distance_atr > 4.00 -> ROUNDING_ERROR
    otherwise AVAILABLE
```

The Council should review specification correctness, determinism, dependency
compatibility, ownership boundaries and trading fitness for Dynamic TP
selection. Special attention should be paid to comparator determinism,
handoff/thesis-binding validation, rounded-output invariants, sequential
too-close/too-far behavior, F-008/F-009 boundaries, and whether research
parameters can remain unvalidated without blocking specification certification.
