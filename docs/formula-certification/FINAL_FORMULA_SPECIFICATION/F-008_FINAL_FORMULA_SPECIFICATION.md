# FINAL_FORMULA_SPECIFICATION

# F-008 — Planned Entry Reference Selection

**Artifact:** `F-008_FINAL_FORMULA_SPECIFICATION.md`
**Specification status:** `FINAL_APPROVED`
**Review:** Full Expert Council Review — Cycle 1
**Review date:** 2026-09-15

## 1. Identity

| Field | Approved value |
|---|---|
| Formula ID | F-008 |
| Formula name | Planned entry reference selection |
| Owner | Position Rules |
| Formula family | ENTRY |
| Reviewed candidate | `F-008_COUNCIL_DEFINED_CYCLE_1` |
| Active methodology baseline | v1.2.14 |
| Entry methodology | `TT-METH-018`, version `0.2.2` |
| Market Handoff contract | v4 |

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = YES
SPECIFICATION_STATUS = FINAL_APPROVED
TRADING_FITNESS = ADEQUATE_FOR_DECLARED_ROLE_WITH_LIMITATIONS
BLOCKING_FINDINGS_REMAINING = NONE
ANOTHER_REVIEW_CYCLE_REQUIRED = NO
EMPIRICAL_EFFECTIVENESS = NOT_ESTABLISHED
PARAMETER_CALIBRATION = NOT_ESTABLISHED
IMPLEMENTATION_DOWNSTREAM_FORMULAS_AND_EXECUTION = NOT_CERTIFIED
```

## 3. Intended Purpose

F-008 constructs one Position-owned structural entry from a valid committed
LONG/SHORT Market Handoff. It returns a frozen `planned_entry_reference` and
identical `limit_order_price`, or an explicit unavailable reason.

It does not calculate stop, target, sizing, risk/reward, Portfolio approval,
exchange execution, live quote marketability or repricing.

## 4. Actual Construct

F-008 performs:

```text
structural reference selection
+ ATR-normalized improvement-depth admissibility
+ side-preserving tick rounding
```

It consumes exact received direction, match price, tick size,
`volatility.atr_15m`, `reference_geometry.levels[]` and `entry_context` from the
Market Handoff. It uses F-003's received Q18 ATR export without recomputation or
hidden precision. It does not reconstruct Set formation or infer direction.

## 5. Exact Formula / Rule

### 5.1 Required inputs

```text
direction
matched_at
market_snapshot_at
set_match_reference_price
tick_size
ATR_15m
reference_geometry.levels[]
entry_context.set_family
entry_context.thesis_reference_policy
entry_context.thesis_reference_level_id
```

`references.levels[]` in calculation notation denotes wire
`reference_geometry.levels[]`.

### 5.2 Input rejection

Invalid contract identity, direction, provenance or required structure
terminates handoff consumption before selection. Defensive numeric diagnostics
map missing, malformed, nonfinite or nonpositive match price, ATR and tick to
their corresponding `MISSING_*` codes; invalid family/policy maps likewise.

Primary diagnostic precedence:

```text
MISSING_SET_MATCH_REFERENCE
> MISSING_ATR
> MISSING_TICK_SIZE
> MISSING_SET_FAMILY
> MISSING_THESIS_REFERENCE_POLICY
```

Retain all known failures. These diagnostics never authorize an invalid
handoff.

### 5.3 Supported directions and order policy

Only:

```text
LONG
SHORT
```

may proceed. `NONE` is invalid for Dynamic Entry.

Success always emits:

```text
order_type = LIMIT
post_only = true
```

No market/taker fallback exists.

### 5.4 Directional structural types

LONG permits:

```text
SWING_LOW_15M
SWING_LOW_1H
PREVIOUS_DAY_LOW
RANGE_LOW
```

SHORT permits:

```text
SWING_HIGH_15M
SWING_HIGH_1H
PREVIOUS_DAY_HIGH
RANGE_HIGH
```

Apply these sets to both thesis and default candidates. `BREAKOUT_RECLAIM` adds
no implicit high-to-support or low-to-resistance conversion. Supporting such
conversions would require a separately specified entry rule.

### 5.5 Candidate eligibility

Filter references for:

```text
positive finite price
approved directional type
exact availability as-of matched_at
```

Then apply strict improvement side and raw ATR band before default ranking:

```text
LONG:  r < S
SHORT: r > S
```

where:

```text
S = set_match_reference_price
A = received ATR_15m
r = candidate price
d = abs(S - r)
```

Raw eligibility:

```text
0.10 <= d / A <= 1.25
```

Equivalent exact comparisons:

```text
10 * d >= A
4 * d <= 5 * A
```

Percent improvement:

```text
100 * d / S
```

No epsilon, display rounding, extra quantizer or ATR-only synthesized price
participates. A raw-ineligible candidate cannot be rescued by tick rounding.

### 5.6 Thesis-reference policy

Non-null thesis references require unique exact IDs and consistent originating
role, occurrence, type, timeframe and price evidence. Missing/conflicting
bindings, dangling IDs or producer availability violations are handoff errors,
never heuristic fallback.

`NONE` requires both thesis ID and binding null.

`REQUIRED` has no fallback. If the reference fails F-008 type, side or depth
eligibility:

```text
THESIS_ENTRY_REFERENCE_INVALID
```

A contract-valid `PREFERRED` null pair, or valid bound reference failing F-008
type/side/depth eligibility, records:

```text
INVALID_THESIS_ENTRY_REFERENCE
```

and uses the default pool.

### 5.7 Family hierarchies

TREND_CONTINUATION and GENERIC:

```text
LONG:
1. SWING_LOW_15M
2. SWING_LOW_1H
3. PREVIOUS_DAY_LOW
4. RANGE_LOW

SHORT:
1. SWING_HIGH_15M
2. SWING_HIGH_1H
3. PREVIOUS_DAY_HIGH
4. RANGE_HIGH
```

RANGE:

```text
LONG:
1. RANGE_LOW
2. SWING_LOW_15M
3. SWING_LOW_1H
4. PREVIOUS_DAY_LOW

SHORT:
1. RANGE_HIGH
2. SWING_HIGH_15M
3. SWING_HIGH_1H
4. PREVIOUS_DAY_HIGH
```

BREAKOUT_RECLAIM uses valid thesis priority; otherwise GENERIC.

Within type:

```text
1. latest exact available_at
2. smallest raw improvement distance
3. case-sensitive ordinal Unicode code-point level_id
```

Array order and diagnostic integer `age_seconds` cannot decide selection.

### 5.8 Candidate-exhaustion reasons

For default selection, define the base pool before strict price-side and depth
checks.

```text
empty base pool -> NO_ELIGIBLE_ENTRY_REFERENCE
nonempty base pool with no strictly improving reference -> NO_ENTRY_SIDE_GEOMETRY
improving references but none inside raw band -> NO_ADMISSIBLE_ENTRY_DEPTH
```

`REQUIRED` thesis eligibility failure takes precedence over these pool reasons.
Preserve candidate exclusions and preferred-thesis warnings.

### 5.9 Tick rounding

For selected `r`:

```text
LONG:  E = floor(r / t) * t
SHORT: E = ceil(r / t) * t
```

where `t = tick_size`.

Require:

```text
finite E > 0
integer E / t
correct outward rounding
strict improvement side
0.10 <= abs(S - E) / A <= 1.25
```

Arithmetic failure or failed positivity/grid/rounding/side invariants:

```text
ROUNDING_ERROR
```

Band failure after rounding:

```text
ENTRY_TOO_SHALLOW_AFTER_ROUNDING
ENTRY_TOO_DEEP_AFTER_ROUNDING
```

Invalid input ticks belong to input rejection. Once selected, rounding failure
is terminal: no alternative-reference retry, clamp, offset or repricing,
including under `PREFERRED`.

### 5.10 Final output

Success returns:

```text
planned_entry_reference = E
limit_order_price = E
order_type = LIMIT
post_only = true
feasibility = AVAILABLE
```

Failure exposes no usable entry price. Diagnostic prices are explicitly
non-actionable.

## 6. Inputs

| Input | Meaning | Unit/type |
|---|---|---|
| `direction` | Immutable Set direction | `LONG` or `SHORT` |
| `S` | `set_match_reference_price` | positive decimal |
| `A` | received `volatility.atr_15m` | positive decimal |
| `t` | `tick_size` | positive decimal |
| `reference_geometry.levels[]` | frozen governed levels | array |
| `entry_context.set_family` | hierarchy selector | enum |
| `entry_context.thesis_reference_policy` | REQUIRED / PREFERRED / NONE | enum |
| `entry_context.thesis_reference_level_id` | optional thesis level | nullable id |
| `matched_at` | match availability cutoff | timestamp |

## 7. Outputs

| Output | Meaning |
|---|---|
| `planned_entry_reference` | frozen rounded entry reference price |
| `limit_order_price` | identical LIMIT order price |
| `order_type` | `LIMIT` |
| `post_only` | `true` |
| `feasibility.reason` | `AVAILABLE` or rejection code |
| reference-selection diagnostics | candidates, exclusions, selected reference and alternatives |
| distance diagnostics | raw/rounded improvement in price, percent and ATR units |
| warnings | non-terminal warnings such as invalid preferred thesis fallback |

## 8. Units

Prices use instrument price units. Percent improvement is percent units.
Improvement ATR values are dimensionless ATR multiples.

## 9. Parameters

| Parameter | Value |
|---|---|
| `MIN_ENTRY_IMPROVEMENT_ATR` | `0.10` |
| `MAX_ENTRY_DEVIATION_ATR` | `1.25` |
| order type | `LIMIT` |
| post only | `true` |

These are pinned research defaults, not validated optima.

## 10. Domain / Preconditions

Before F-008 can return `AVAILABLE`:

1. Market Handoff is valid and committed for `LONG` or `SHORT`.
2. `S > 0`, `A > 0`, and `t > 0`.
3. Set family and thesis policy are valid.
4. Candidate references have valid provenance, allowed type, positive finite
   price and availability as-of `matched_at`.
5. The selected candidate satisfies side geometry and raw ATR band.
6. Tick rounding preserves positivity, grid membership, side geometry and
   rounded ATR band.

## 11. Missing / Invalid Behavior

Canonical reasons:

```text
AVAILABLE
NO_ENTRY_SIDE_GEOMETRY
NO_ELIGIBLE_ENTRY_REFERENCE
NO_ADMISSIBLE_ENTRY_DEPTH
THESIS_ENTRY_REFERENCE_INVALID
MISSING_ATR
MISSING_TICK_SIZE
MISSING_SET_MATCH_REFERENCE
MISSING_SET_FAMILY
MISSING_THESIS_REFERENCE_POLICY
ENTRY_TOO_SHALLOW_AFTER_ROUNDING
ENTRY_TOO_DEEP_AFTER_ROUNDING
ROUNDING_ERROR
```

Missing values are never zero-filled.

## 12. Boundaries

- Exact raw depths `0.10` and `1.25` pass.
- Correct outward rounding increases improvement by `delta`, where
  `0 <= delta < tick_size`.
- Too-shallow-after-rounding is unreachable after valid raw admission and
  remains defensive.
- A raw-ineligible candidate cannot be selected.
- No live bid/ask, gap expansion, crossing or minimum-resting validation is
  performed by Position Rules.
- No market/taker fallback, chase, reprice or structural refresh exists.

## 13. Precision / Rounding

Use exact decimal-safe arithmetic. Do not use binary floats, epsilon,
display-rounded values, hidden ATR precision, or recomputed ATR. Tick rounding
uses exact floor/ceil formulas and validates positivity, grid membership and
side geometry after rounding.

## 14. Time Semantics

Reference levels must be available as-of `matched_at`. F-008 uses the frozen
Market Handoff for the same `decision_cycle_id` and `set_result_id`. It does
not refresh references or market prices after the Set match.

## 15. State / Replay / Restart

Persist:

- cycle/result identity;
- immutable handoff digest;
- Position configuration and Council-rule identity;
- thresholds and hierarchy;
- original thesis binding;
- selected calculation reference;
- raw/rounded distances;
- exclusions, reasons and warnings.

Replay restores the binding without refreshing values or reselecting under a
newer configuration.

## 16. Configuration Pinning

F-008 pins:

```text
TT-METH-018 v0.2.2
Market Handoff v4
Position Rules configuration id/version/content digest
MIN_ENTRY_IMPROVEMENT_ATR = 0.10
MAX_ENTRY_DEVIATION_ATR = 1.25
family hierarchy tables
thesis-reference policy
Council-defined candidate F-008_COUNCIL_DEFINED_CYCLE_1
```

## 17. Dependencies

| Dependency | Class | Status |
|---|---|---|
| F-005 | CERTIFIED_FORMULA | Immutable direction and handoff/no-handoff boundary. |
| F-003 | CERTIFIED_FORMULA | ATR semantics consumed through Market Handoff. |
| Market Handoff v4 | DOCUMENTATION_DEPENDENCY | Direction, match price, ATR, tick, references and entry context. |
| Position Rules Dynamic Entry | DOCUMENTATION_DEPENDENCY | Formula source for structural entry. |
| Entry thresholds | RESEARCH_PARAMETER | Pinned defaults; effectiveness unvalidated. |

## 18. Ownership

F-008 owns entry for both sides. F-006/F-007 consume it. F-009/F-010 consume
the frozen planned entry for their own calculations and cannot cause F-008 to
revise it. Set owns handoff production. Order Lifecycle owns submit/cancel/fill
facts and does not analyze or reprice entry.

## 19. Pipeline Role

```text
F-005 matched direction + Market Handoff -> F-008 planned entry -> F-006/F-007/F-009/F-010
```

## 20. Approved Uses

F-008 may be used to produce the frozen planned entry and LIMIT POST_ONLY price
for a Position decision cycle when all required inputs and checks pass.

## 21. Prohibited Interpretations

F-008 is not:

- an execution-quality estimate;
- a fill-probability model;
- a liquidity or queue-priority measure;
- a profitability finding;
- a stop/target/sizing/risk/reward formula;
- an exchange submission or post-only marketability gate;
- permission to chase, reprice, cross, or switch to MARKET.

## 22. Known Limitations

Frozen prices can become stale. Entries may miss fills or suffer adverse
selection. Coarse ticks can eliminate availability. F-003 corrected-history
acceptance remains externally unresolved.

## 23. Research Parameters

Thresholds, family priorities, thesis preference, recency ranking and realized
benefit remain unvalidated.

## 24. Empirical Validation Requirements

Research must cover all candidate opportunities, including rejection and
nonfill outcomes, across symbol, side, family, policy, regime, reference age
and tick/ATR ratio. Assess fill rate/time, adverse selection, missed
opportunities and downstream outcomes after costs using chronological
out-of-sample evidence. Do not assume a candle touch establishes a fill.

## 25. Eight Final Expert Verdicts

| Expert perspective | Final verdict | Assessment |
|---|---|---|
| Senior Intraday Crypto Trader | APPROVE_WITH_LIMITATIONS | Structural pullback selection is coherent for the declared entry role. Improvement is relative to frozen Set price; better realized outcomes are unproven. |
| Market Microstructure & Order Flow Researcher | APPROVE_WITH_LIMITATIONS | Excluding live quotes is consistent with this boundary. Structural levels and ATR do not establish liquidity, queue priority, fill probability or adverse-selection protection. |
| Market Regime & Context Analyst | APPROVE_WITH_LIMITATIONS | Frozen family selection is deterministic. Family hierarchies and smoothed ATR remain sensitive to transitions, shocks and stale structure. |
| Quant Strategy Researcher | APPROVE_WITH_LIMITATIONS | Exact comparisons, total candidate ordering and rounding definitions close determinism gaps. The inclusive band is coherent; calibration is unproven. |
| Risk & Trade Management Architect | APPROVE_WITH_LIMITATIONS | Entry remains independent of stop, target, sizing and approval. The 1.25 ATR cap limits planned displacement from Set match, not loss or exposure. |
| Execution & Exchange Mechanics Specialist | APPROVE_WITH_LIMITATIONS | Directional tick rounding is correct once positivity, grid membership and geometry are checked. LIMIT/post-only is order policy, not guaranteed acceptance or execution. |
| Adversarial Strategy Reviewer | APPROVE_WITH_LIMITATIONS | The candidate distinguishes corrupt producer bindings from permissible fallback, rejects rounded zero, prohibits rounding rescue and makes selected-reference rounding failure terminal. |
| Performance & Strategy Diagnostics Analyst | APPROVE_WITH_LIMITATIONS | Selection and rejection diagnostics support research if the denominator includes all opportunities. Fill-only results or candle-touch assumptions cannot establish effectiveness. |

## 26. Final Council Record

```text
FINAL_COUNCIL_RECORD

formula_id: F-008
formula_name: Planned entry reference selection
reviewed_candidate: F-008_COUNCIL_DEFINED_CYCLE_1
specification_status: APPROVED_WITH_RECORDED_COUNCIL_DEFINITIONS
trading_fitness_status: ADEQUATE_FOR_DECLARED_ROLE_WITH_LIMITATIONS

senior_intraday_crypto_trader: APPROVE_WITH_LIMITATIONS
microstructure_order_flow_researcher: APPROVE_WITH_LIMITATIONS
market_regime_context_analyst: APPROVE_WITH_LIMITATIONS
quant_strategy_researcher: APPROVE_WITH_LIMITATIONS
risk_trade_management_architect: APPROVE_WITH_LIMITATIONS
execution_exchange_mechanics_specialist: APPROVE_WITH_LIMITATIONS
adversarial_strategy_reviewer: APPROVE_WITH_LIMITATIONS
performance_strategy_diagnostics_analyst: APPROVE_WITH_LIMITATIONS

F008-C01: CLOSED_BY_RECORDED_SPECIFICATION
F008-C02: CLOSED_BY_RECORDED_SPECIFICATION
F008-C03: CLOSED_BY_RECORDED_SPECIFICATION
F008-C04: CLOSED_BY_RECORDED_SPECIFICATION
F008-C05: CLOSED_BY_RECORDED_SPECIFICATION
F008-C06: CLOSED_BY_RECORDED_SPECIFICATION
F008-C07: RETAINED_EMPIRICAL_QUESTION_NON_BLOCKING
F008-C08: RETAINED_NON_BLOCKING_LIMITATION

blocking_findings_remaining: NONE
empirical_effectiveness_and_parameter_calibration: NOT_ESTABLISHED
implementation_downstream_formulas_and_execution: NOT_CERTIFIED

full_council_approved: YES
another_review_cycle_required: NO
```
