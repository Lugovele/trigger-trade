# F-004 SOURCE PACK

## 1. Identity

| Field | Extracted value | Evidence |
|---|---|---|
| Formula ID | F-004 | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula name | Set normalization, percentile, and score calculation | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Owner | Set | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Type | TRADING_FORMULA | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Formula family | MARKET_NORMALIZATION | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Certification status | CERTIFICATION_REQUIRED | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Backend gate | BLOCK_FINAL_IMPLEMENTATION | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Catalog canonical-definition pointer | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` :: §2 Canonical Set Value Representation and `docs/trading-methodology/methodology/SET.md` :: Set analytics | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Current implementation pointer | `src/triggertrade/triggers/volume_confirmation.py::empirical_percentile_rank` LEGACY/DEMO_ONLY | `docs/FORMULA_METRICS_CATALOG.md`, Master Catalog |
| Active methodology baseline | v1.2.14 | `docs/trading-methodology/` |

Catalog note: demo percentile or score behavior must not be promoted as
canonical without certification.

## 2. Source Index

| # | Source | Section | Authority | Relevance |
|---:|---|---|---|---|
| 1 | `docs/FORMULA_METRICS_CATALOG.md` | Master Catalog; Certification Queue | CATALOG / GATE | Identifies F-004, dependencies F-001/F-002/F-003 and implementation gate. |
| 2 | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` | §§1-2, 4-5, 7 | NUMERIC POLICY / N-008 | Governs exact Set arithmetic, Q36 named outputs, z-score variance/sqrt and internal normalization. |
| 3 | `docs/trading-methodology/methodology/SET.md` | Part II §6 | NORMALIZATION BASELINE | Defines 30 completed UTC calendar day lookback and 14-day warmup for ordinary normalization. |
| 4 | `docs/trading-methodology/methodology/SET.md` | Part II §7 | Z-SCORE CONVENTION | Defines z-score, population standard deviation, zero-sigma UNAVAILABLE and `clip(z/2,-1,+1)`. |
| 5 | `docs/trading-methodology/methodology/SET.md` | Part II §§14-15 | ATR percentile / volatility gate | Defines ATR_PCT percentile, empirical rank and initial [15,97] volatility hard gate. |
| 6 | `docs/trading-methodology/methodology/SET.md` | Part II §§16-23 | Normalized momentum, relative, flow and activity factors | Defines factor normalization and participation adjustment. |
| 7 | `docs/trading-methodology/methodology/SET.md` | Part II §§24-32 | BTC context, structure, top-level weights and Direction Score | Defines weighted scoring inputs and final score formula. |
| 8 | `docs/trading-methodology/methodology/SET.md` | Part II §33 | Classification thresholds | Downstream boundary: F-005 likely owns final LONG/SHORT/NONE classification. |
| 9 | `docs/trading-methodology/methodology/SET.md` | Part III §§37-38 | Direction evidence and frozen-at-match invariant | Defines audit payload and freeze of raw/normalized factors, weighted contributions and score. |
| 10 | `docs/formula-certification/F-001/F-001_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies certified price-move Trigger evidence and sign/availability semantics. |
| 11 | `docs/formula-certification/F-002/F-002_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies certified volume confirmation/participation evidence and limitations. |
| 12 | `docs/formula-certification/F-003/F-003_FINAL_FORMULA_SPECIFICATION.md` | Final spec | CERTIFIED_FORMULA | Supplies certified ATR and ATR_PCT semantics for volatility context. |
| 13 | `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md` | Dataset selection/completeness | INPUT CONTRACT | Set owns analytical windows/selectors; API supplies factual data only. |
| 14 | `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md` | Handoff numeric policy and context | OUTPUT CONTRACT | Defines handoff consumption boundary and Set-owned provenance. |

## 3. Purpose and Trading Context

F-004 is the Set-owned normalization, percentile and score layer that turns
available Set facts and certified upstream Trigger/volatility outputs into
normalized factors, local diagnostics and a direction-score value for later Set
direction classification.

It is not itself the final LONG/SHORT handoff decision unless Council finds the
catalog scope necessarily includes the score formula but not the classifier.
F-005 is separately queued as "Set direction classifier and LONG/SHORT
handoff," so the Source Pack treats final classification as downstream.

## 4. Exact Formula Reconstruction

### Normalization baseline

Ordinary rolling z-scores, ATR/volatility percentiles and metrics explicitly
reusing the ordinary baseline use:

```text
lookback = 30 completed UTC calendar days
minimum_warmup = 14 completed UTC calendar days
mode = rolling
scope = same symbol
future observations = prohibited
```

Let `evaluation_at` be the governed persisted Set analytical cutoff. Let `D`
be `00:00:00Z` at the start of the UTC day containing that cutoff. The ordinary
30 completed UTC calendar day population is:

```text
[D - 30 UTC calendar days, D)
```

Current incomplete UTC day is excluded. Fewer than 14 completed UTC calendar
days makes required normalized metrics `UNAVAILABLE`.

### Z-score convention

```text
z = (x - μ) / σ
μ = rolling arithmetic mean
σ = rolling population standard deviation
ddof = 0
```

If `σ = 0` or normalization is otherwise undefined:

```text
metric normalization = UNAVAILABLE
```

Default normalized score transform:

```text
normalized_score = clip(z / 2.0, -1, +1)
```

unless a metric has an explicitly different transform.

### ATR percentile

For current:

```text
ATR_PCT(15m,14,Wilder)
```

compute empirical percentile rank against completed same-symbol 15m ATR_PCT
observations in the ordinary 30 completed UTC calendar day window:

```text
percentile = 100 * count(reference_values <= current_value) / count(reference_values)
```

Volatility hard gate uses:

```text
ATR percentile < 15 -> NONE
ATR percentile > 97 -> NONE
```

### Normalized factor formulas

Primary 15m momentum:

```text
VNM(H) = RETURN(H) / ATR_PCT_decimal
MOMENTUM_SCORE = clip(momentum_z / 2.0, -1, +1)
```

Directional-efficiency modifier:

```text
MOMENTUM_EFFECTIVE =
MOMENTUM_SCORE * (0.5 + 0.5 * DE_STRENGTH)
```

Relative strength:

```text
RELATIVE_RETURN_15m = RETURN(asset,15m) - RETURN(BTC,15m)
RELATIVE_SCORE = clip(relative_return_z / 2.0, -1, +1)
```

Aggressive volume delta:

```text
AGGRESSIVE_VOLUME_DELTA_PCT =
100 * (AggBuyNotional - AggSellNotional)
/
(AggBuyNotional + AggSellNotional)
```

If denominator is zero:

```text
UNAVAILABLE
```

Flow factor:

```text
FLOW_RAW = AGGRESSIVE_VOLUME_DELTA_PCT / 100

FLOW_EFFECTIVE =
FLOW_RAW * (0.5 + 0.5 * PARTICIPATION_STRENGTH)
```

Activity gate and participation strength:

```text
TOD_REL_TURNOVER < 0.70 -> NONE, rejection_stage = ACTIVITY_GATE

PARTICIPATION_STRENGTH =
clip((TOD_REL_TURNOVER - 0.70) / 1.30, 0, 1)
```

BTC context:

```text
BTC_MOMENTUM_SCORE = clip(BTC_RETURN_Z / 2.0, -1, +1)

BTC_CONTEXT_SCORE =
0.60 * BTC_STRUCTURE_SCORE
+
0.40 * BTC_MOMENTUM_SCORE
```

Structure:

```text
BULLISH   -> +1
AMBIGUOUS -> 0
BEARISH   -> -1

STRUCTURE_SCORE =
0.50 * STRUCTURE_1H
+
0.50 * STRUCTURE_15M
```

### Top-level score

Canonical v0.4 weights:

```text
STRUCTURE            0.35
MOMENTUM             0.25
RELATIVE_STRENGTH    0.15
FLOW                  0.15
BTC_CONTEXT           0.10
```

Final direction-score arithmetic:

```text
DIRECTION_SCORE =
0.35 * STRUCTURE_SCORE
+
0.25 * MOMENTUM_EFFECTIVE
+
0.15 * RELATIVE_SCORE
+
0.15 * FLOW_EFFECTIVE
+
0.10 * BTC_CONTEXT_SCORE
```

Range:

```text
[-1,+1]
```

## 5. Inputs

| Input | Meaning | Unit/type | Dependency |
|---|---|---|---|
| F-001 price-move result/sign | Certified short-horizon price displacement evidence | Trigger result and sign evidence | F-001 certified |
| F-002 participation result/diagnostics | Certified short-horizon relative participation evidence | Trigger result; local M/K/R/P | F-002 certified |
| ATR / ATR_PCT | Certified volatility context | Percent / decimal work values | F-003 certified |
| Completed candles/returns | Price return populations | Exact decimal | Market Data Request / Set selectors |
| Raw trades | Aggressive buy/sell notional | Quote notional | Market Data Request |
| Time-of-day turnover | Participation / activity metric | Ratio | Active Set methodology |
| Swing sequence states | Structure state | BULLISH/AMBIGUOUS/BEARISH | Set structural methodology |
| BTC returns/structure | BTC context | Scores / z-scores | Set methodology |
| Numeric policy | Exact work grid, variance/sqrt and serialization | `TT_SET_NUMERIC_V1` | N-008 |
| Configuration | Weights, thresholds, windows and versions | Pinned config | Set / P17 |

## 6. Outputs

| Output | Meaning |
|---|---|
| Normalized metric values | z-scores, clipped scores, percentiles and effective factors. |
| Gate outputs | Data/volatility/activity gate status and failed-gate lists. |
| Veto diagnostics | BTC, relative and local momentum veto states. |
| Weighted contributions | Structure, momentum, relative, flow and BTC-context weighted components. |
| `DIRECTION_SCORE` | Weighted score in range `[-1,+1]`, before downstream classification. |
| Audit payload evidence | Raw factor snapshot, normalized factors and score values for frozen Set Result. |

Downstream F-005 is expected to consume score/gates/vetoes for final
LONG/SHORT/NONE classification and Market Handoff.

## 7. Units

All continuous Set-derived values use exact decimal/rational arithmetic under
`TT_SET_NUMERIC_V1`. Percent values use numerical `100` factor where specified.
Scores are dimensionless and generally bounded to `[-1,+1]` after clipping.

## 8. Parameters and Thresholds

| Parameter | Value / source |
|---|---|
| Ordinary lookback | 30 completed UTC calendar days |
| Minimum warmup | 14 completed UTC calendar days |
| Z-score ddof | 0 |
| Default score transform | `clip(z/2.0,-1,+1)` |
| ATR percentile allowed range | `[15, 97]` |
| Activity minimum | `0.70` |
| Participation strength denominator | `1.30` |
| Local momentum veto z | `2.0` |
| Relative contradiction veto z | `2.0` |
| BTC veto threshold | `0.70` |
| Score weights | Structure `0.35`, Momentum `0.25`, Relative `0.15`, Flow `0.15`, BTC `0.10` |

Direction thresholds `+0.35` and `-0.35` appear in Set §33 and likely belong
to downstream F-005 classification rather than F-004 normalization/score
calculation. Council should decide whether to certify those only as downstream
consumer context here.

## 9. Sign / Direction Semantics

F-004 produces signed normalized factors and a signed direction-score. Positive
score indicates bullish directional evidence; negative score indicates bearish
directional evidence. Final LONG/SHORT/NONE ownership is expected to remain
with F-005 / Set direction classifier.

F-001 sign evidence is not itself LONG/SHORT. F-002 is direction-neutral.

## 10. Domain and Preconditions

Before a normalized metric or score is available:

1. Required upstream formula outputs are certified and available.
2. Set has selected exact source populations and as-of cutoffs.
3. Source data are complete, final, correctly ordered and contradiction-free.
4. Ordinary normalization has at least 14 completed UTC calendar days.
5. Population standard deviation is nonzero where z-score is required.
6. Metric-specific denominators are nonzero.
7. Configuration and numeric policy are pinned for the active formation epoch.

If a required metric/gate input is unavailable, the affected normalized metric,
score component or complete score should be unavailable rather than fabricated.

## 11. Missing / Invalid Behavior

| Case | Expected behavior from active sources |
|---|---|
| Fewer than 14 completed UTC days | Required normalized metric `UNAVAILABLE`; direction `NONE`; rejection `DATA_UNAVAILABLE`. |
| `σ = 0` | Metric normalization `UNAVAILABLE`. |
| Aggressive volume denominator zero | `AGGRESSIVE_VOLUME_DELTA_PCT` `UNAVAILABLE`. |
| Missing/incomplete source interval | Affected computation `UNAVAILABLE`. |
| Conflicting source identity/content | Integrity/reconciliation condition; no silent recomputation. |
| Future/still-forming data | Excluded; cannot satisfy computation. |
| Missing F-001/F-002/F-003 input | Dependent component unavailable. |

## 12. Boundaries

Known boundaries:

- Percentile rank counts `reference_values <= current_value`.
- ATR percentile below `15` or above `97` activates volatility gate.
- Activity below `0.70` activates activity gate.
- Local momentum veto thresholds are inclusive by formulas using `<= -2.0` and
  `>= +2.0`.
- Relative contradiction veto thresholds are inclusive by formulas using
  `<= -2.0` and `>= +2.0`.
- BTC veto thresholds are inclusive by formulas using `<= -0.70` and
  `>= +0.70`.

Open boundary for Council: whether F-004 final score itself includes final
LONG/SHORT thresholding or only computes `DIRECTION_SCORE` and diagnostics for
F-005.

## 13. Precision

`TT_SET_NUMERIC_V1` governs:

- exact decimal parsing;
- exact sums/differences/products/quotients;
- formula-order evaluation;
- one Q36 HALF_EVEN round at each named continuous Set metric output,
  recursive state update and normalization output;
- exact integer/rational counts/ranks;
- exact variance and integer sqrt;
- no binary floating point, epsilon or display-rounded gates.

Market Handoff serialization may round permitted continuous handoff values to
18 fractional decimals only at defined boundaries. Internal Set gates consume
working precision, not display or handoff serialization.

## 14. Time Semantics

Ordinary normalization uses completed UTC calendar days, not trailing hours.
Current incomplete UTC day is excluded. Completed candles/buckets must be
wholly contained in selected half-open intervals. Set persists as-of and
dataset selectors before dispatch. Receipt/restart time cannot replace the
governed analytical cutoff.

Explicit metric-specific temporal selectors retain their own rules.

## 15. State / Replay / Restart

Set must persist:

- analytical cutoff and selector identities;
- source manifests/page coverage;
- numeric policy version;
- upstream formula versions;
- baseline population identities;
- intermediate normalized values;
- gate/veto outputs;
- weighted contributions;
- score;
- configuration/weights/thresholds.

Restart restores authentic matching checkpoints and source identities before
continuing computation. Conflicting historical source content invalidates
affected derived state and blocks new eligible decisions rather than silently
splicing inconsistent history into frozen handoffs.

## 16. Version / Configuration Pinning

Material F-004 configuration includes:

- numeric policy version `TT_SET_NUMERIC_V1`;
- ordinary baseline window and warmup;
- metric definitions and timeframes;
- thresholds/gates/veto parameters;
- score weights;
- upstream formula versions;
- active Set/Trigger/Core Set configuration.

Later edits apply only to future epochs/cycles under existing Set
configuration binding rules.

## 17. Ownership

Set owns derived normalization, percentiles, score calculations, state,
checkpoints and frozen match evidence. API supplies factual data only. Position
consumes frozen Market Handoff and must not recompute Set metrics.

## 18. Downstream Consumers

| Consumer | Relationship |
|---|---|
| F-005 | Consumes score/gates/vetoes for direction classifier and LONG/SHORT handoff. |
| F-008 | Indirectly depends on F-005 and Market Handoff. |
| Position Rules | Consume frozen handoff fields; no Set recomputation. |
| Diagnostics/dashboard | Display score, factors, gates, vetoes and evidence. |

## 19. Dependencies

| Dependency | Class | Status |
|---|---|---|
| F-001 Price-move trigger | CERTIFIED_FORMULA | Final spec approved. |
| F-002 Volume confirmation | CERTIFIED_FORMULA | Final spec approved. |
| F-003 ATR/TR/ATR_PCT | CERTIFIED_FORMULA | Final spec approved. |
| N-008 / TT_SET_NUMERIC_V1 | APPROVED_POLICY | Exact Set arithmetic and output precision. |
| Market Data Request | DOCUMENTATION_DEPENDENCY | Factual source data and selectors. |
| Active Set methodology | DOCUMENTATION_DEPENDENCY | Factor formulas, baseline and score weights. |

## 20. Worked / Conformance Examples Present

Active numeric policy examples cover ATR quantization and exact boundary
representation but not a complete F-004 weighted score example.

No complete normative worked example for full `DIRECTION_SCORE` across all
factors was found in this extraction.

## 21. Source Gaps and Ambiguities

| # | Gap / ambiguity | Impact |
|---:|---|---|
| 1 | F-004 catalog name combines normalization, percentile and score, while F-005 separately owns direction classifier/handoff. | Council should define whether F-004 finalizes `DIRECTION_SCORE` only or includes threshold classification context. |
| 2 | Some score factor inputs, such as directional efficiency, swing sequence state, time-of-day turnover and aggressive volume delta, are not in the primary queue as certified formulas. | Council should classify them as approved active-methodology formulas/policies or dependency gaps. |
| 3 | Complete worked score example absent. | Likely non-blocking if formulas and boundaries are complete. |
| 4 | Relationship between certified F-001/F-002 short-horizon triggers and broader F-004 factor score is not explicitly mapped one-to-one in active excerpts. | Council should decide whether upstream certifications are sufficient context or whether F-004's active score formulas are independent Set analytics. |
| 5 | Market Handoff export set may not include all local diagnostics. | Final spec should distinguish internal working values from exported handoff fields. |

## 22. Reviewer Handoff Summary

```text
FORMULA_ID: F-004
FORMULA_NAME: Set normalization, percentile, and score calculation

EXACT_FORMULA_RECONSTRUCTABLE:
PARTIALLY

DECLARED_TRADING_PURPOSE_RECONSTRUCTABLE:
YES

INPUT_DOMAIN_COMPLETE:
PARTIALLY_WITH_DEPENDENCY_CLASSIFICATION_REQUIRED

BOUNDARY_BEHAVIOR_COMPLETE:
PARTIALLY

TIME_SEMANTICS_COMPLETE:
YES_FOR_ORDINARY_BASELINE

DIRECTION_SEMANTICS_COMPLETE:
PARTIALLY_BOUNDARY_WITH_F005

PARAMETER_PROVENANCE_COMPLETE:
YES_FOR_EXTRACTED_ACTIVE_METHOD_VALUES

STATE_REPLAY_SEMANTICS_COMPLETE:
YES_GENERIC_SET_NUMERIC_POLICY

SOURCE_GAP_COUNT:
5_CLASSIFICATION_OR_SCOPE_DECISION_REQUIRED

READY_FOR_FULL_EXPERT_COUNCIL_REVIEW:
YES

BLOCKING_EXTRACTION_GAPS:
NONE IDENTIFIED BY ORCHESTRATOR; COUNCIL SHOULD DEFINE F004/F005 BOUNDARY AND DEPENDENCY CLASSIFICATION
```
