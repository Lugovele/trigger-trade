# F-008 SOURCE PACK

## 1. Identity

| Field | Extracted value | Evidence |
|---|---|---|
| Formula ID | F-008 | `docs/FORMULA_METRICS_CATALOG.md` |
| Formula name | Planned entry reference selection | `docs/FORMULA_METRICS_CATALOG.md` |
| Owner | Position Rules | `docs/FORMULA_METRICS_CATALOG.md` |
| Type | TRADING_FORMULA | `docs/FORMULA_METRICS_CATALOG.md` |
| Formula family | ENTRY | `docs/FORMULA_METRICS_CATALOG.md` |
| Certification status | CERTIFICATION_REQUIRED | `docs/FORMULA_METRICS_CATALOG.md` |
| Backend gate | BLOCK_FINAL_IMPLEMENTATION | `docs/FORMULA_METRICS_CATALOG.md` |
| Catalog canonical-definition pointer | `docs/trading-methodology/methodology/POSITION_RULES.md` :: Position construction and canonical Set value consumption | `docs/FORMULA_METRICS_CATALOG.md` |
| Current implementation pointer | `src/triggertrade/services/futures_runtime.py::_intent_price` DEMO_ONLY | `docs/FORMULA_METRICS_CATALOG.md` |
| Active methodology baseline | v1.2.14 | `docs/trading-methodology/` |

## 2. Source Index

| # | Source | Section | Authority | Relevance |
|---:|---|---|---|---|
| 1 | `docs/FORMULA_METRICS_CATALOG.md` | Master Catalog; Certification Queue | CATALOG / GATE | Identifies F-008, dependency F-005 and downstream consumers. |
| 2 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Part I §§1, 1B, 2, 5A, 13-16 | POSITION BOUNDARY | Defines Position-owned decision, immutable Market Handoff input, Dynamic Limit Entry sequencing and direction gate. |
| 3 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Dynamic Limit Entry §§1-15 | ENTRY CORE | Defines purpose, invariant, constants, required inputs, supported directions, order policy, reference types, geometry and thesis policy. |
| 4 | `docs/trading-methodology/methodology/POSITION_RULES.md` | Dynamic Limit Entry §§16-33, 39-49 | ENTRY FORMULA | Defines family hierarchies, improvement bands, selection, tick rounding, outputs and LONG/SHORT algorithms. |
| 5 | `docs/trading-methodology/methodology/POSITION_RULES.md` | §§42-47 | REASONS / OUTPUT | Defines reason codes, missing input handling and output contract. |
| 6 | `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md` | Contract v4 | INPUT CONTRACT | Defines frozen Set-produced direction, reference geometry and entry context consumed by Position. |
| 7 | `docs/formula-certification/F-005/F-005_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies certified immutable direction and handoff/no-handoff boundary. |
| 8 | `docs/formula-certification/F-003/F-003_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies certified 15m ATR semantics consumed via Market Handoff. |

## 3. Purpose and Trading Context

F-008 is the Position Rules-owned Dynamic Limit Entry calculation. It converts
the frozen Set Market Handoff and governed entry context into either:

```text
usable planned_entry_reference
limit_order_price
order_type = LIMIT
post_only = true
```

or an explicit entry-unavailable rejection reason.

F-008 supplies the planned entry used by downstream stop, take-profit, sizing
and risk/reward formulas. It does not determine market direction, stop, target,
quantity, notional, leverage, fees, risk/reward, Portfolio capital approval or
order submission.

## 4. Exact Formula Reconstruction

### Core invariant

Dynamic Limit Entry contains one Position Rules-owned price-construction phase:

```text
Structural Entry Price Generation
=
Set-consistent structural price improvement
+
ATR-normalized entry-depth admissibility
+
tick-safe Entry rounding
```

It is not derived from:

```text
SL distance
TP distance
desired R:R
position size
leverage
direction score
market chase
```

### Baseline constants

```text
MIN_ENTRY_IMPROVEMENT_ATR = 0.10
MAX_ENTRY_DEVIATION_ATR   = 1.25
```

These are versioned research defaults, not validated optima.

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
entry_context.set_family
entry_context.thesis_reference_policy
entry_context.thesis_reference_level_id
```

### Supported directions and order policy

Supported directions:

```text
LONG
SHORT
```

`NONE` is invalid for Dynamic Entry.

Order policy:

```text
order_type = LIMIT
post_only = true
```

No automatic market or taker fallback exists.

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

No free-form level is permitted.

### Structural entry side relative to Set match

LONG candidates must improve on Set match:

```text
candidate_price < set_match_reference_price
```

SHORT candidates must improve on Set match:

```text
candidate_price > set_match_reference_price
```

No zero-improvement baseline entry is allowed.

### General candidate eligibility

A candidate level must:

```text
exist in references.levels[]
available_at <= matched_at
price finite and > 0
use approved level_type
lie on the required improvement side of set_match_reference_price
```

### Thesis-reference policy

Read:

```text
entry_context.thesis_reference_policy
```

Allowed:

```text
REQUIRED
PREFERRED
NONE
```

P4 applies. Position consumes the exact Set `origin_binding`. Default candidate
ranking is calculation fallback only; it never rewrites a thesis reference or
resolves a missing producer role.

If policy is `REQUIRED`, the referenced level must exist, be available as-of
`matched_at`, be structurally valid for direction, satisfy price-improvement
side and lie inside the approved entry-improvement band. If any fail:

```text
usable = false
reason = THESIS_ENTRY_REFERENCE_INVALID
```

No fallback.

If policy is `PREFERRED` and the thesis reference is valid and inside the band:

```text
selected entry reference = thesis reference
```

If invalid, too shallow or too deep:

```text
warning = INVALID_THESIS_ENTRY_REFERENCE
continue with default candidate pool
```

If policy is `NONE`:

```text
thesis_reference_level_id = null
default hierarchy applies
```

### Family hierarchies

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

BREAKOUT_RECLAIM:

```text
If a valid REQUIRED/PREFERRED thesis entry reference exists, thesis policy
governs selection. Otherwise use GENERIC hierarchy.
```

No free-form breakout/reclaim price is permitted.

### Same-type tie breakers

If multiple eligible levels share the same structural type:

```text
1. latest available_at
2. smaller improvement distance to set_match_reference_price
3. lexical level_id
```

`age_seconds` is diagnostic only.

### Improvement distance

For each candidate:

```text
improvement_price =
abs(set_match_reference_price - candidate_price)

improvement_pct =
100 * improvement_price / set_match_reference_price

improvement_atr =
improvement_price / ATR_15m
```

### Entry improvement bands

```text
TOO_SHALLOW:
improvement_atr < 0.10

ELIGIBLE:
0.10 <= improvement_atr <= 1.25

TOO_DEEP:
improvement_atr > 1.25
```

Candidates outside the band are not selected. No ATR-only fallback may synthesize:

```text
entry = set_match_reference_price +/- K * ATR
```

### Raw entry price

For the selected reference:

```text
raw_entry_price = selected_reference_price
```

No extra offset is added in baseline v0.2.2.

### Tick rounding

LONG buy-limit rounds down:

```text
rounded_entry_price =
floor(raw_entry_price / tick_size) * tick_size
```

SHORT sell-limit rounds up:

```text
rounded_entry_price =
ceil(raw_entry_price / tick_size) * tick_size
```

This preserves requested price improvement.

### Post-rounding improvement validation

Recompute:

```text
rounded_improvement_atr =
abs(set_match_reference_price - rounded_entry_price) / ATR_15m
```

Require:

```text
0.10 <= rounded_improvement_atr <= 1.25
```

If below:

```text
ENTRY_TOO_SHALLOW_AFTER_ROUNDING
```

If above:

```text
ENTRY_TOO_DEEP_AFTER_ROUNDING
```

### Final output

After structural selection, ATR admissibility and tick rounding pass:

```text
planned_entry_reference = rounded_entry_price
limit_order_price = rounded_entry_price
order_type = LIMIT
post_only = true
feasibility = AVAILABLE
```

For baseline v0.2.2, `planned_entry_reference` and `limit_order_price` are
identical.

## 5. Inputs

| Input | Meaning | Unit/type | Dependency |
|---|---|---|---|
| Market Handoff direction | Immutable `LONG` or `SHORT` | enum | F-005 certified / Market Handoff |
| `set_match_reference_price` | Frozen Set match reference price | positive decimal string | Market Handoff |
| `tick_size` | Instrument price increment | positive decimal string | Market Handoff / instrument metadata |
| `ATR_15m` | Volatility scale | positive decimal string | F-003 via Market Handoff |
| `references.levels[]` | Governed structural references | array of levels | Market Handoff |
| `entry_context.set_family` | Set family | enum | Market Handoff |
| `entry_context.thesis_reference_policy` | REQUIRED / PREFERRED / NONE | enum | Market Handoff |
| `entry_context.thesis_reference_level_id` | Optional bound thesis reference | nullable level id | Market Handoff |
| `matched_at` / `market_snapshot_at` | Frozen Set match timestamps | timestamps | Market Handoff |

## 6. Outputs

| Output | Meaning |
|---|---|
| `planned_entry_reference` | Rounded entry reference price used by downstream Position formulas. |
| `limit_order_price` | Same rounded price for the LIMIT POST_ONLY order. |
| `order_type` | Always `LIMIT` on success. |
| `post_only` | Always `true` on success. |
| Feasibility status | `AVAILABLE` or explicit reason. |
| Reference-selection diagnostics | Candidate lists, ineligible reasons, shallow/deep lists, selected reference and alternatives. |
| Distance diagnostics | Raw and rounded improvement in price, percent and ATR units. |
| Warnings | Canonical warning codes such as invalid preferred thesis or fallback use. |

## 7. Units

Prices are exact decimal price units for the instrument. `improvement_pct` is
percent units. `improvement_atr` and `rounded_improvement_atr` are dimensionless
ATR multiples. Counts and ranks are exact integers.

## 8. Parameters and Thresholds

| Parameter | Value |
|---|---|
| `MIN_ENTRY_IMPROVEMENT_ATR` | `0.10` |
| `MAX_ENTRY_DEVIATION_ATR` | `1.25` |
| Order type | `LIMIT` |
| Post-only | `true` |
| Dynamic Entry methodology | `TT-METH-018`, version `0.2.2` |

## 9. Sign / Direction Semantics

For LONG, the entry candidate must be below the Set match reference price and
rounds down to tick. For SHORT, the candidate must be above the Set match
reference price and rounds up to tick. Direction is consumed from the immutable
Market Handoff and may not be inferred or reversed by Position Rules.

## 10. Domain and Preconditions

Before F-008 can return an available entry:

1. Market Handoff is valid and frozen for a matched `LONG` or `SHORT`.
2. `direction` is `LONG` or `SHORT`.
3. `set_match_reference_price > 0`.
4. `ATR_15m > 0`.
5. `tick_size > 0`.
6. `entry_context.set_family` is valid.
7. `entry_context.thesis_reference_policy` is valid.
8. Governed reference levels needed by the selected policy/hierarchy are
   available as of `matched_at`.

## 11. Missing / Invalid Behavior

Canonical reason codes:

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

Missing input handling:

```text
ATR_15m missing or <= 0 -> MISSING_ATR
tick_size missing or <= 0 -> MISSING_TICK_SIZE
set_match_reference_price missing or <= 0 -> MISSING_SET_MATCH_REFERENCE
set_family missing/invalid -> MISSING_SET_FAMILY
thesis policy missing/invalid -> MISSING_THESIS_REFERENCE_POLICY
```

Missing values are never zero-filled.

## 12. Boundaries

- `improvement_atr = 0.10` is eligible.
- `improvement_atr = 1.25` is eligible.
- `improvement_atr < 0.10` is too shallow.
- `improvement_atr > 1.25` is too deep.
- A `REQUIRED` thesis reference outside the band rejects with
  `THESIS_ENTRY_REFERENCE_INVALID`; no fallback.
- A `PREFERRED` thesis reference outside the band produces a warning and falls
  back to the default pool.
- No live bid/ask, gap expansion, crossing or minimum-resting validation is
  performed by Position Rules.

## 13. Precision

Use decimal-safe arithmetic. Tick rounding uses exact floor/ceil relative to
`tick_size`. Position consumes exact canonical Market Handoff values and must
not recompute Set ATR or recover hidden precision. Display rounding must not
feed eligibility or rounding decisions.

## 14. Time Semantics

F-008 uses frozen Market Handoff evidence from the same `decision_cycle_id` and
`set_result_id`. Reference levels must be available as-of `matched_at`. The
entry price is frozen for this Position Rules decision cycle after success.

Dynamic Entry does not refresh structure, use current bid/ask or chase the
market after the Set match.

## 15. State / Replay / Restart

Position persists:

- pinned Position Rules configuration selected on first Market Handoff
  evaluation;
- `decision_cycle_id` and `set_result_id`;
- frozen Market Handoff identity and digest;
- selected reference level id/type/timeframe/price/availability;
- raw and rounded entry values;
- tick size, ATR and match price used;
- feasibility reason and warnings.

Replay/restart hydrates the persisted binding. Failed final construction does
not rerun Set or revise frozen Entry/SL/TP. Later configuration applies only to
future decision cycles.

## 16. Version / Configuration Pinning

Material F-008 configuration includes:

- Dynamic Entry methodology `TT-METH-018`, version `0.2.2`;
- Position Rules configuration id/version/content digest;
- Market Handoff contract version `4`;
- Set result and handoff identities;
- `MIN_ENTRY_IMPROVEMENT_ATR = 0.10`;
- `MAX_ENTRY_DEVIATION_ATR = 1.25`;
- structural family hierarchy tables;
- thesis-reference policy.

## 17. Ownership

Position Rules owns Dynamic Entry calculation and planned entry reference
selection. Set owns Market Handoff production and reference provenance. Position
validates/consumes, never selects a replacement thesis reference. Order
Lifecycle submits/cancels/reconciles but does not perform market analysis,
structure refresh or automatic repricing.

## 18. Downstream Consumers

| Consumer | Relationship |
|---|---|
| F-006 / F-007 | Consume planned entry for LONG/SHORT Position formulas. |
| F-009 | Stop calculation uses planned entry. |
| F-010 | Dynamic Take Profit selection uses planned entry. |
| F-011 | Sizing/notional construction consumes planned entry downstream. |
| F-012 | Risk/reward and edge calculations consume planned entry, stop and target. |
| Order Spec | Uses `limit_order_price` after successful construction and authorization. |

## 19. Dependencies

| Dependency | Class | Status |
|---|---|---|
| F-005 direction and handoff/no-handoff boundary | CERTIFIED_FORMULA | Final spec approved. |
| F-003 ATR/TR/ATR_PCT | CERTIFIED_FORMULA | Supplies ATR semantics via Market Handoff. |
| Market Handoff v4 | DOCUMENTATION_DEPENDENCY | Supplies direction, match price, references, contexts and volatility. |
| Position Rules Dynamic Entry v0.2.2 | DOCUMENTATION_DEPENDENCY | Provides entry selection formula. |
| Tick-size / instrument metadata | CONFIG_PARAMETER / DOCUMENTATION_DEPENDENCY | Must be positive and frozen in handoff/config. |
| Entry thresholds 0.10 / 1.25 ATR | RESEARCH_PARAMETER | Pinned defaults; performance not validated. |

## 20. Worked / Conformance Examples Present

Active methodology provides algorithmic examples for LONG and SHORT, but no
complete numeric worked example with concrete levels, ATR, tick size, selected
reference, rounding and final output.

## 21. Source Gaps and Ambiguities

| # | Gap / ambiguity | Impact |
|---:|---|---|
| 1 | Section 26 uses `NO_ELIGIBLE_ENTRY_REFERENCE`, while Section 45 includes `NO_ENTRY_SIDE_GEOMETRY` and `NO_ELIGIBLE_ENTRY_REFERENCE`. | Council should confirm exact reason-code distinction when no governed references exist versus no reference passes basic side geometry. |
| 2 | `NO_ENTRY_SIDE_GEOMETRY` appears in reason codes but is not explicitly defined in the extracted algorithm text. | Council should define or classify as documentation gap. |
| 3 | Rounding error behavior is named but exact malformed tick/decimal failure boundaries are not fully enumerated. | Council may need to specify fail-closed cases. |
| 4 | Relationship between F-008 planned entry and F-006/F-007 side-specific formulas should be fixed: F-008 appears to own entry for both sides; F-006/F-007 consume it. | Council should verify boundary. |
| 5 | Entry thresholds are pinned research defaults; empirical quality is not established. | Likely non-blocking if retained. |

## 22. Reviewer Handoff Summary

```text
FORMULA_ID: F-008
FORMULA_NAME: Planned entry reference selection

EXACT_FORMULA_RECONSTRUCTABLE:
YES_WITH_REASON_CODE_CLARIFICATION

DECLARED_TRADING_PURPOSE_RECONSTRUCTABLE:
YES

INPUT_DOMAIN_COMPLETE:
PARTIALLY_REASON_CODES_AND_ROUNDING_ERROR_BOUNDARIES

BOUNDARY_BEHAVIOR_COMPLETE:
PARTIALLY

TIME_SEMANTICS_COMPLETE:
YES

DIRECTION_SEMANTICS_COMPLETE:
YES

PARAMETER_PROVENANCE_COMPLETE:
YES_FOR_ACTIVE_METHOD_VALUES

STATE_REPLAY_SEMANTICS_COMPLETE:
YES_GENERIC_POSITION_DECISION_BINDING

SOURCE_GAP_COUNT:
5_CLASSIFICATION_OR_SCOPE_DECISION_REQUIRED

READY_FOR_FULL_EXPERT_COUNCIL_REVIEW:
YES

BLOCKING_EXTRACTION_GAPS:
NONE IDENTIFIED BY ORCHESTRATOR; COUNCIL SHOULD DEFINE REASON-CODE AND F008/F006/F007 BOUNDARIES
```
