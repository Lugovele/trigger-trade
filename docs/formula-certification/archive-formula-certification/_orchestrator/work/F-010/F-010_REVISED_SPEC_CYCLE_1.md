# F-010 REVISED SPECIFICATION CYCLE 1

# F-010 - Dynamic Take Profit Selection and Rounding

## 1. Identity

| Field | Value |
|---|---|
| Formula ID | F-010 |
| Formula name | Dynamic Take Profit selection and rounding |
| Owner | Position Rules |
| Formula family | DYNAMIC_TAKE |
| Certification artifact | Revised candidate |
| Review cycle | 1 |
| Active methodology baseline | v1.2.14 |
| Dynamic TP methodology id | TT-METH-017 |
| Dynamic TP methodology version | 0.2.2 |

## 2. Council Status

```text
FULL_COUNCIL_APPROVED = NO
ANOTHER_REVIEW_CYCLE_REQUIRED = YES
SPECIFICATION_STATUS = REVISED_CANDIDATE_FOR_REVIEW
```

This candidate closes Cycle 1 blockers:

```text
F010-C01: handoff/thesis-binding validation precedence
F010-C02: portable deterministic candidate ordering
F010-C03: permitted type, pool and reason-precedence definitions
```

## 3. Intended Purpose

F-010 constructs the Dynamic Take Profit candidate for a Position Plan. It
consumes the frozen Market Handoff, the certified F-008 planned entry, N-004
tick facts and Position Rules Dynamic TP configuration. It produces either a
usable rounded TP candidate or a deterministic unavailable/rejection reason.

F-010 answers:

```text
Given a committed LONG or SHORT handoff and certified planned entry, which
governed favorable-side structural target is reachable under the Dynamic TP
rules, and what inward-rounded target price is valid for downstream Position
geometry and economics?
```

F-010 does not choose Entry, calculate Stop Loss, derive TP from desired R:R or
stop distance, size the position, compute net edge, approve capital, or submit
orders.

## 4. Actual Construct

Dynamic TP is:

```text
governed favorable-side structural target
+
ATR-normalized reachability
+
tick-normalized realizability
```

Selection is sequential by structural priority. `TOO_CLOSE` can skip to the
next target. `TOO_FAR` terminates selection and rejects Dynamic TP. Distance
must not globally reorder structural priority.

## 5. Exact Formula and Rule

### 5.1 Symbols

```text
direction = LONG | SHORT
E = planned_entry_reference from certified F-008
A = received volatility.atr_15m from Market Handoff
t = tick_size
r = candidate/target level price
R = selected_target_price
TP = rounded_target_price
d = abs(r - E)
```

`E`, `A` and `t` must be exact finite positive decimals. Position consumes the
received Q18 ATR unchanged and must not recompute ATR or recover hidden
precision.

### 5.2 F-008 dependency and configuration prerequisites

F-010 consumes an AVAILABLE certified F-008 result bound to the same:

```text
instrument
direction
decision_cycle_id
set_result_id
Market Handoff identity/digest
tick provenance
```

`take_profit_mode` must be `DYNAMIC`. Invalid TP mode or a missing pinned
Position configuration is `CONFIG_INVALID`.

### 5.3 Directional permitted target types

LONG default and thesis candidates may use only:

```text
SWING_HIGH_15M
SWING_HIGH_1H
PREVIOUS_DAY_HIGH
RANGE_HIGH
```

SHORT default and thesis candidates may use only:

```text
SWING_LOW_15M
SWING_LOW_1H
PREVIOUS_DAY_LOW
RANGE_LOW
```

Do not silently infer an opposite-type conversion.

### 5.4 Basic favorable-side eligibility

LONG:

```text
r > E + t
```

SHORT:

```text
r < E - t
```

A level within one tick of planned entry is ineligible.

A basic eligible target must:

```text
exist in references.levels[]
have a unique canonical level_id
available_at <= matched_at
price finite and > 0
have a directionally permitted target type
satisfy favorable-side geometry vs E
```

### 5.5 Handoff and thesis-binding validation precedence

Before thesis/default selection:

1. Validate handoff identity, provenance and digest.
2. Validate F-008 identity and same-cycle entry binding.
3. Validate required primitives: direction, `E`, `A`, `t`, `references.levels[]`,
   `tp_context.set_family`, `tp_context.thesis_reference_policy`, configuration
   identity/version/digest and instrument metadata revision.
4. Reject invalid or conflicting producer bindings.
5. Reject dangling thesis IDs.
6. Reject producer availability violations.
7. Reject duplicate or conflicting canonical level IDs.
8. Reject `tp_context.thesis_reference_policy = NONE` when either thesis ID or
   binding is non-null.

These are handoff/configuration/dependency failures, not fallback cases.

`PREFERRED` fallback is allowed only when the thesis pair is contract-valid
null, or when a valid bound reference exists but fails F-010 calculation
eligibility.

`REQUIRED` has no fallback. If the required thesis reference is absent,
dangling, unavailable as-of `matched_at`, not directionally permitted,
nonpositive, nonfinite, not favorable-side eligible against `E`, or outside the
reachability band, return:

```text
usable = false
reason = THESIS_REFERENCE_INVALID
```

If `PREFERRED` has a valid bound reference and it is calculation-eligible,
select it before default traversal. If it is validly bound but fails F-010
calculation eligibility, record:

```text
warning = INVALID_THESIS_REFERENCE_OVERRIDE
```

and continue to the default hierarchy. Calculation fallback never rewrites the
producer binding.

### 5.6 Capability, basic pool and traversable pool

`NO_FAVORABLE_SIDE_GEOMETRY` applies when upstream favorable-side geometry
capability is unavailable for the relevant direction/family/handoff, so F-010
cannot establish whether governed favorable-side targets exist.

The `basic_pool` is the set of governed levels that pass Section 5.4 basic
favorable-side eligibility.

If geometry capability is available and `basic_pool` is empty:

```text
usable = false
reason = NO_ELIGIBLE_REFERENCE
```

The `traversable_pool` is the ordered subset of `basic_pool` whose level type
appears in the active Set-family directional hierarchy. If the basic pool is
non-empty but no basic eligible levels belong to the active hierarchy:

```text
usable = false
reason = NO_REACHABLE_TARGET
```

and preserve diagnostics showing the non-traversable basic eligible levels.

### 5.7 Set family and hierarchy

`tp_context.set_family` is read only from the frozen Market Handoff and must be:

```text
TREND_CONTINUATION
RANGE
BREAKOUT_RECLAIM
GENERIC
```

For `TREND_CONTINUATION` and `GENERIC`:

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

For `RANGE`:

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

For `BREAKOUT_RECLAIM`, a valid `REQUIRED` or `PREFERRED` thesis target controls
selection. Otherwise use the `GENERIC` hierarchy. No free-form breakout target
is permitted.

### 5.8 Total ordering within same priority type

For candidates sharing the same hierarchy type, order by:

```text
1. latest exact available_at
2. smallest exact favorable distance abs(level.price - E)
3. ascending case-sensitive ordinal Unicode code-point level_id,
   with shorter prefixes first
```

No locale-dependent comparison, normalization, case folding, natural sort,
numeric substring sort, array order, arrival order or `age_seconds` ordering is
allowed.

`TOO_FAR` terminates traversal before any later candidate, including an older
candidate of the same type. `PREFERRED` preselection fallback is a separate,
explicitly permitted branch and does not change default traversal ordering.

### 5.9 Distance and exact reachability comparisons

For each traversed candidate:

```text
distance_price = abs(r - E)
distance_pct = 100 * distance_price / E
distance_atr = distance_price / A
```

Use exact comparisons:

```text
TOO_CLOSE: 4 * distance_price < 3 * A
ELIGIBLE:  4 * distance_price >= 3 * A and distance_price <= 4 * A
TOO_FAR:   distance_price > 4 * A
```

These are equivalent to:

```text
distance_atr < 0.75
0.75 <= distance_atr <= 4.00
distance_atr > 4.00
```

Rounded quotient diagnostics must not drive decisions.

### 5.10 Sequential structural selection

Default hierarchy traversal:

```text
for target in structural priority order:
    if target not in traversable_pool:
        preserve diagnostic as appropriate
        continue

    d = abs(target.price - E)

    if 4 * d < 3 * A:
        record TOO_CLOSE
        continue

    if d > 4 * A:
        record TOO_FAR
        terminate selection
        return TARGET_TOO_FAR

    select target
    stop
```

If the hierarchy is exhausted after only `TOO_CLOSE` traversed candidates and no
target is selected:

```text
usable = false
reason = NO_REACHABLE_TARGET
```

### 5.11 Target selection output and diagnostics

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
unvisited_level_ids[]
```

Optional diagnostic traversal after primary selection may populate
`alternative_eligible_target_level_ids[]`, but it must be explicitly marked as
diagnostic and must never affect the primary selected target, reason or
feasibility.

### 5.12 Tick rounding

TP is rounded inward toward realizability, never beyond the structural target.

LONG:

```text
TP = floor(R / t) * t
```

SHORT:

```text
TP = ceil(R / t) * t
```

Use exact decimal-safe arithmetic.

### 5.13 Post-rounding output validity

Before exposing a usable TP:

```text
TP is finite
TP > 0
TP / t is an integer
```

LONG:

```text
TP = floor(R / t) * t
TP > E
TP <= R
```

SHORT:

```text
TP = ceil(R / t) * t
TP < E
TP >= R
```

Arithmetic failure or invariant failure:

```text
usable = false
reason = ROUNDING_ERROR
```

Failed prices are non-actionable. Post-rounding failure is terminal under every
policy, including `PREFERRED`; F-010 must not select an alternate lower-priority
target, reprice Entry, use SL distance, or synthesize an ATR target as repair.

### 5.14 Post-rounding reachability

Compute:

```text
rounded_distance_price = abs(TP - E)
```

Minimum:

```text
if 4 * rounded_distance_price < 3 * A:
    usable = false
    reason = TARGET_TOO_CLOSE_AFTER_ROUNDING
```

Maximum:

```text
if rounded_distance_price > 4 * A:
    usable = false
    reason = ROUNDING_ERROR
```

The maximum violation should not occur after valid raw selection and inward
rounding unless arithmetic/precision inconsistency occurred.

### 5.15 Reason precedence

Primary reason precedence:

```text
1. CONFIG_INVALID
   - invalid or missing pinned TP mode/configuration

2. IDENTITY_INVALID
   - invalid handoff/F-008 identity, digest, provenance or binding consistency

3. missing primitive reasons
   MISSING_ENTRY_REFERENCE
   MISSING_ATR
   MISSING_TICK_SIZE
   MISSING_SET_FAMILY
   MISSING_THESIS_REFERENCE_POLICY

4. NO_FAVORABLE_SIDE_GEOMETRY
   - favorable geometry capability unavailable

5. THESIS_REFERENCE_INVALID
   - REQUIRED thesis reference missing or invalid after valid handoff primitives

6. NO_ELIGIBLE_REFERENCE
   - geometry capability available but zero levels pass basic favorable-side eligibility

7. traversal outcomes
   TARGET_TOO_FAR
   NO_REACHABLE_TARGET
   TARGET_TOO_CLOSE_AFTER_ROUNDING
   ROUNDING_ERROR
   AVAILABLE
```

Secondary diagnostics must preserve all discovered contributing conditions.

## 6. Inputs

| Input | Source | Required semantics |
|---|---|---|
| `direction` | F-005 / Market Handoff | `LONG` or `SHORT`; `NONE` invalid. |
| `E` | F-008 | Certified positive planned entry for same instrument/direction/cycle/handoff. |
| `A` | F-003 via Market Handoff | Positive received Q18 ATR; not recomputed. |
| `t` | N-004 / Market Handoff | Positive tick size with instrument metadata provenance. |
| `references.levels[]` | Market Handoff | Frozen governed levels available as-of `matched_at`. |
| `tp_context.set_family` | Market Handoff | Allowed family. |
| `tp_context.thesis_reference_policy` | Market Handoff | `REQUIRED`, `PREFERRED`, or `NONE`. |
| `tp_context.thesis_reference_level_id` and binding | Market Handoff | Validated before selection. |
| `take_profit_mode` | Position configuration | Must be `DYNAMIC`. |

## 7. Outputs

Primary output:

```text
rounded_target_price
```

Dynamic TP contract:

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
    unvisited_level_ids: []
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

## 8. Units

| Item | Unit |
|---|---|
| Entry, target price, rounded target, tick size, distance price | Instrument quote price units |
| ATR distance | Dimensionless ATR multiples |
| distance percent | Percent units; numeric `1` means one percent |
| timestamps / ages | Source timestamps / seconds |

## 9. Parameters

| Parameter | Value | Class | Notes |
|---|---:|---|---|
| `MIN_TP_DISTANCE_ATR` | `0.75` | RESEARCH_PARAMETER | Reachability/meaningfulness threshold, not profit guarantee. |
| `MAX_TP_DISTANCE_ATR` | `4.00` | RESEARCH_PARAMETER | Maximum structural reachability threshold; too-far terminates traversal. |
| hierarchy order | versioned tables | RESEARCH_PARAMETER | Deterministic but empirically unvalidated. |
| recency preference | latest `available_at` | RESEARCH_PARAMETER | Deterministic but empirically unvalidated. |

## 10. Domain and Preconditions

F-010 can evaluate only when:

```text
take_profit_mode = DYNAMIC
direction in {LONG, SHORT}
E > 0
A > 0
t > 0
tp_context.set_family valid
tp_context.thesis_reference_policy valid
references.levels[] available from the frozen handoff
F-008 result is AVAILABLE and identity-matched
```

Missing values are never zero-filled.

## 11. Missing / Invalid Behavior

| Condition | Reason |
|---|---|
| invalid/missing TP mode/configuration | `CONFIG_INVALID` |
| invalid F-008/handoff identity, digest, provenance, duplicate/conflicting IDs or invalid binding | `IDENTITY_INVALID` |
| `E` missing or `<= 0` | `MISSING_ENTRY_REFERENCE` |
| `A` missing or `<= 0` | `MISSING_ATR` |
| `t` missing or `<= 0` | `MISSING_TICK_SIZE` |
| `set_family` missing/invalid | `MISSING_SET_FAMILY` |
| thesis policy missing/invalid | `MISSING_THESIS_REFERENCE_POLICY` |
| favorable geometry capability unavailable | `NO_FAVORABLE_SIDE_GEOMETRY` |
| required thesis reference invalid after valid handoff primitives | `THESIS_REFERENCE_INVALID` |
| zero basic eligible favorable-side references | `NO_ELIGIBLE_REFERENCE` |
| no reachable target after allowed too-close skips | `NO_REACHABLE_TARGET` |
| next traversed candidate too far | `TARGET_TOO_FAR` |
| inward rounding makes target too close | `TARGET_TOO_CLOSE_AFTER_ROUNDING` |
| arithmetic or rounded-output invariant failure | `ROUNDING_ERROR` |

## 12. Boundaries

F-010 includes:

```text
Dynamic TP target eligibility
handoff/thesis-binding validation for TP selection
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

F-009 stop distance, desired R:R and downstream failures cannot construct or
repair TP.

## 13. Precision / Rounding

Use exact decimal-safe arithmetic. No binary floats, display rounding, hidden
ATR precision, epsilon comparisons or intermediate rounding.

Use exact integer comparisons:

```text
4 * d >= 3 * A
d <= 4 * A
```

for the raw reachability band.

Inward tick rounding:

```text
LONG:  TP = floor(R / t) * t
SHORT: TP = ceil(R / t) * t
```

Diagnostic quotient/percent fields do not drive decisions.

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
F-008 identity
configuration ID/version/content digest
threshold/hierarchy/comparator identity
numeric-policy version
instrument metadata revision
tick_size and provenance
received Q18 ATR_15m
tp_context and original binding evidence
references.levels[]
candidate classifications
selection ordering
unvisited vs evaluated diagnostic alternatives
raw and rounded target calculations
warnings and reasons
```

Restart must reproduce the same target or rejection without refreshing market
data, repairing bindings, recomputing ATR, changing configuration or choosing a
lower-priority target after a terminal too-far or post-rounding failure.

## 16. Configuration Pinning

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
F-009 stop boundary specification
candidate comparator: latest available_at, smallest favorable distance, Unicode code-point level_id
```

## 17. Dependencies

| Dependency | Class | Use |
|---|---|---|
| F-008 | CERTIFIED_FORMULA | Supplies certified planned entry and handoff consumption boundary. |
| F-003 | CERTIFIED_FORMULA | Supplies certified 15m ATR semantics consumed through Market Handoff. |
| N-004 | APPROVED_POLICY | Tick-size normalization and instrument tick facts. |
| Market Handoff v4 | DOCUMENTATION_DEPENDENCY | Supplies direction, ATR, tick, references and `tp_context`. |
| T-003 | RESEARCH_PARAMETER | Fixed/minimum TP thresholds; must not replace Dynamic TP logic. |
| Position Rules Part IV | DOCUMENTATION_DEPENDENCY | Source for Dynamic TP methodology. |

## 18. Ownership

Position Rules owns F-010. Set owns direction, reference geometry, `tp_context`
and frozen Market Handoff. F-008 owns planned entry. F-009 owns stop
integration and may only be used later by joint TP/SL feasibility, not by target
selection. Portfolio owns capital approval. Order Lifecycle owns execution and
fills. API/instrument facts own tick-size evidence under N-004.

## 19. Pipeline Role

```text
F-005 matched direction
-> Market Handoff
-> F-008 planned entry
-> F-010 Dynamic TP candidate
-> Position geometry gate
-> F-012 gross R:R / minimum net edge
-> Order Spec take_profit block
```

## 20. Approved Uses Requested

If approved, F-010 may be used to:

```text
select a governed Dynamic TP target
reject unavailable/unreachable Dynamic TP cases
produce rounded_target_price for downstream Position geometry and economics
persist deterministic selection and rejection diagnostics
```

## 21. Prohibited Interpretations

F-010 must not be interpreted as:

```text
a fixed take-profit formula
a gross R:R or net edge formula
a stop-distance-derived target
a profitability guarantee
a fill or execution guarantee
a partial-exit or multi-target methodology
a permission to repair failed downstream gates by changing TP
a permission to refresh or repair Market Handoff bindings
```

## 22. Known Limitations

1. `0.75` and `4.00` ATR, hierarchy order and recency preference are research
   parameters, not validated optima or reach probabilities.
2. Frozen structure can become stale.
3. Inward rounding does not establish fills, exchange acceptance or
   profitability.
4. Final-price geometry and economic gates remain downstream.
5. Implementation, persistence, execution, F-011 and F-012 remain uncertified.

## 23. Research Parameters

```text
MIN_TP_DISTANCE_ATR = 0.75
MAX_TP_DISTANCE_ATR = 4.00
hierarchy order
recency preference
T-003 fixed/minimum TP thresholds for separate fixed/configuration context
```

## 24. Empirical Validation Requirements

Use chronological out-of-sample opportunities, including rejected and unfilled
cases, segmented by instrument, direction, family, thesis policy, regime,
reference age and tick/ATR ratio. Assess threshold sensitivity,
hierarchy/recency preference, too-far rejection effects, target-before-stop
outcomes and realized results after costs. Candle touches cannot establish
fills or exit ordering.

## 25. Edge and Regression Fixtures

### Exact raw boundaries

```text
E = 100
A = 4
t = 0.25

LONG raw lower boundary target = 103
SHORT raw lower boundary target = 97
LONG raw upper boundary target = 116
SHORT raw upper boundary target = 84

All are raw-band eligible before rounding if all other checks pass.
```

### Rounding-induced too-close

```text
E = 100
A = 4.04
t = 0.25

LONG target = 103.03
raw distance = 3.03
minimum = 0.75 * A = 3.03
rounded TP = 103.00
rounded distance = 3.00
result = TARGET_TOO_CLOSE_AFTER_ROUNDING

SHORT target = 96.97
raw distance = 3.03
rounded TP = 97.00
rounded distance = 3.00
result = TARGET_TOO_CLOSE_AFTER_ROUNDING
```

### Strict one-tick exclusion

```text
LONG: target.price = E + t -> ineligible
SHORT: target.price = E - t -> ineligible
```

### Too-close skip

A higher-priority traversed target with `4*d < 3*A` is recorded in
`too_close_level_ids[]`; traversal continues to the next structural candidate.

### Too-far termination

A traversed target with `d > 4*A` records `TARGET_TOO_FAR` and stops traversal
before any lower-priority or later same-type candidate.

### Same-type ordering

Two same-type candidates order by latest `available_at`, then smallest exact
favorable distance, then ascending case-sensitive ordinal Unicode code-point
`level_id` with shorter prefixes first.

### Binding failures vs preferred fallback

Dangling/conflicting binding rejects before selection. A validly bound
`PREFERRED` target failing calculation eligibility records
`INVALID_THESIS_REFERENCE_OVERRIDE` and falls back to default hierarchy.

### Restart equality

Restart with the same frozen handoff, F-008 entry, configuration, ATR, tick,
bindings and levels reproduces the same target or rejection.

## 26. Revision Record

| Cycle | Change | Reason |
|---:|---|---|
| 1 | Added handoff/thesis-binding validation precedence and valid fallback rules. | Closes F010-C01. |
| 1 | Replaced unspecified lexical ordering with exact available_at, favorable distance and Unicode code-point level_id comparator. | Closes F010-C02. |
| 1 | Defined directional permitted types, capability/basic/traversable pools and reason precedence. | Closes F010-C03. |
| 1 | Added rounded-output invariants, replay requirements and conformance fixtures. | Supports deterministic re-review and future tests. |
