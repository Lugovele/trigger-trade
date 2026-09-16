# Set-derived numeric computation — TT_SET_NUMERIC_V1

**Policy version:** `TT_SET_NUMERIC_V1`  
**Package revision:** `v1.2.15` — stable policy ID remains `TT_SET_NUMERIC_V1`.

This is a technical computation/serialization contract for existing Set formulas, timeframes, windows and thresholds. It does not add a signal, indicator or fallback. Set owns derived state. Market Handoff v4 declares this policy; Position consumes the exact canonical handoff and must not run another indicator library to replace it. `TT_NUMERIC_V1` remains the independent monetary policy.

## Canonical integer freshness age

Where Set emits the existing integer `age_seconds` field for a reference level, compute the exact nonnegative timestamp delta first and then take the mathematical ceiling:

```text
age_exact_seconds = market_snapshot_at - available_at
age_seconds = ceil(age_exact_seconds)
```

Do not round either timestamp. Boundary examples: `60.000000 -> 60`, `60.000001 -> 61`, `60.750000 -> 61`. This rule prevents the freshness metric from understating actual age and requires no wire-version change.

## 1. Source identity, order and completeness

Parse raw decimals exactly as signed integer/scale values. Binary floating point, context-dependent parsing, NaN and infinity are forbidden. Preserve raw spelling separately as factual provenance. Source facts must have authoritative identities, times, symbol and dataset/series identity. De-duplicate equal source identities; conflicting equal IDs are integrity conditions, not a last-callback choice.

Set fixes one as-of cutoff and persists its per-dataset selectors before dispatch under Market Data Request v3. Sort closed candles by authoritative interval-open time, then verify non-overlap and continuity. Treat normalized candle close_time as the exclusive interval end, not an exchange's last-millisecond representation; the factual adapter documents that technical time normalization. No incomplete/still-forming candle or candle ending after as_of participates. Raw trades use authoritative event chronology; exact sums are order-independent. Any ambiguous order needed for a recursive computation or missing source interval is UNAVAILABLE until resolved.

### 1.1. Fixed UTC ordinary normalization calendar

[Set methodology, Part II §6](../methodology/SET.md#6-canonical-normalization-baseline) defines the ordinary analytical population: UTC is fixed system semantics, not a Set configuration parameter. A completed UTC calendar day is `[00:00:00Z, next 00:00:00Z)` whose exclusive end is at or before the persisted evaluation cutoff. Let `D` be UTC midnight starting the day containing that cutoff; N completed UTC calendar days select exactly `[D - N UTC calendar days, D)`. The ordinary 30-day lookback is `[D - 30 UTC calendar days, D)`, excluding the current incomplete UTC day.

The 14-completed-UTC-calendar-day minimum warmup uses the same day boundaries. Ordinary z-scores, ATR/volatility percentiles and all explicit baseline reuses cannot substitute local, account, Portfolio-accounting or exchange-session calendars, or a trailing-hours window. A UTC timestamp format alone is not an analytical selector.

Observation membership follows the governed factual timestamps and existing dataset-specific half-open rules in [Market Data Request](../api-contracts/MARKET_DATA_REQUEST.md), §§3 and 5, including completed candles/buckets wholly contained in the selected interval. Source completeness/finality, pagination/snapshot binding and no-future-data requirements remain unchanged. Explicit metric-specific temporal selectors retain their own rules. This fixed calendar introduces no configuration/wire field and does not change numeric working precision, formulas, thresholds, observation sampling or the stable `TT_SET_NUMERIC_V1` identity.

## 2. Working arithmetic and operation order

Inputs, sums, differences, products and rational quotients inside each named formula are exact integer/rational expressions, evaluated in the written formula order; algebraic regrouping must not introduce extra rounding. At each named continuous Set metric output, recursive state update and normalization output, round once to a working grid of `10^-36` with ROUND_HALF_EVEN. A bounded decimal context alone is not the rule: 36 is a fractional scale, not 36 significant digits. Large values retain all integer digits. Integer/rational implementations or arbitrarily extended decimal calculations that give the same correctly rounded result are acceptable.

Dependent formulas consume the persisted working value of their named dependencies, not a library's hidden extra precision. Sum/mean/variance terms inside a normalization formula remain exact until its specified sqrt/output quantizer. Percent conversion is the existing exact factor 100 or 1/100; clamp, sign and comparisons are applied in the existing formula order to these canonical values without an epsilon. Integer counts/ranks retain exact integer semantics. Window selection, percentile rank definition and thresholds remain the existing Set rules.

## 3. Wilder ATR(14) seed and recursive state

The canonical series anchor is the first complete native candle history for the instrument/series for which the factual preceding close is available and authoritative history completeness is proven. It is identified in an immutable source manifest (`series_id`, `seed_anchor`, `predecessor_close`, `source_digest`, `first_complete_history_evidence_ref`, ordered `seed_candle_ids`). It is not the first candle a library happens to fetch. If this anchor/history or a checkpoint descending from it cannot be proven, ATR is UNAVAILABLE; do not switch to an arbitrary rolling bootstrap or library default. This is an initialization rule, not an additional market-analysis window or trading threshold.

Compute existing true range exactly: max(high-low, abs(high-previous_close), abs(low-previous_close)). The seed is the arithmetic mean of the first 14 consecutive true ranges, rounded HALF_EVEN to 36 fractional decimals. Fewer than 14 true ranges is UNAVAILABLE. For each subsequent completed candle, the unchanged Wilder formula is `(13 * prior_atr_work + current_TR) / 14`, rounded once to the same work grid. Persist the update and processed source identity together. The seed checkpoint includes all 14 ordered source candle IDs/true ranges and the last processed candle, not merely a scalar ATR. Out-of-order incremental facts require ordered replay, not another recursive update. Replay of the same candle is idempotent; changed same-ID source content is an integrity condition. A checkpoint includes policy, seed manifest, processed ordinal/source identities, last candle and exact work value, with canonical content digest. Restore only an authentic matching checkpoint and replay subsequent canonical ordered facts. Full replay from the identical anchor must match checkpoint continuation byte for byte. A revised historical source invalidates affected derived state; do not splice an inconsistent history into a frozen handoff.

Ordinary normalization/percentile baselines use 30 completed UTC calendar days, and their minimum data requirement is 14 completed UTC calendar days, under §1.1 and Set methodology Part II §6. Their existing lengths and formulas are unchanged. Recursive seed ancestry and those analytical population windows are distinct; the fixed UTC lookback does not replace the governed ATR seed/checkpoint ancestry. No host library default selects either.

**F-003 candle eligibility and state progression.** The canonical input timeframe is 15m. In addition to the source, completion, cutoff, continuity and exact-decimal rules above, current high, low and close and the factual immediately preceding close MUST be finite and nonnegative. Each current completed candle MUST satisfy:

```text
0 <= low <= close <= high
```

The predecessor close is not required to lie within the current candle's range. Equal bounds and a zero low/close are admissible when the full ordering and all other source requirements hold. A factual price gap is not a missing interval. The current close participates in eligibility and in the next predecessor binding even though it is not an operand of the current TR expression. TR is exact; there is no separate TR quantizer before the seed mean or recurrence.

A malformed or otherwise ineligible required candle makes the affected computation `UNAVAILABLE`, with its source-validity reason persisted. It MUST NOT form or advance ATR, be omitted to complete a seed, be bridged by holding prior ATR constant, be repaired or authorize a later anchor/reseed. No valid dependent Market Handoff may be emitted. Known accepted historical request/selection/page/snapshot/native-source ownership and immutable-content checks precede semantic rejection: a geometry error cannot conceal an existing identity/content contradiction. Geometry failure alone does not create a new integrity-conflict class.

An otherwise eligible zero-close candle retains its exact TR, membership in the consecutive seed, and any prescribed Q36 seed/recurrence update. Persist that update and source identity once; its factual zero close remains the next candle's predecessor. Zero close alone MUST NOT discard the candle or reset/reseed ancestry. ATR_PCT is separately unavailable under §5. A zero-close candle that fails another eligibility rule is not within this exception.

Zero is a valid internal ATR work state. The first work ATR can become available on the fourteenth eligible completed seed candle after proof; fourteen seed candles plus the factual initial predecessor close are required, not a full extra predecessor-candle payload. Fourteen zero TRs seed zero; the next recurrence from zero remains `Q36(TR / 14)`. Nonpositive or rounded-to-zero export eligibility never changes the recurrence. After restart, an eligible zero-close update is neither repeated nor discarded because no handoff was emitted.

## 4. Population standard deviation and sqrt

For the existing population standard deviation, `n` is the exact population count and ddof=0. Compute exact mean = sum(x)/n and exact variance = sum((x-mean)^2)/n using the stored canonical source metric values. Negative variance is invalid; zero standard deviation makes the existing normalization unavailable.

Square root is correctly rounded to the work grid using integers. For variance a/b >= 0 and F=10^36, let k=floor(sqrt(a*F^2/b)), determined by integer square root and exact bounds. Compare `4*a*F^2` with `b*(2*k+1)^2`: below midpoint retains k; above increments k; equality chooses the even integer. The result is that integer/F. Never use binary floating point or platform libm. Then use this work-grid standard deviation in the existing normalized formula and round its named output to the work grid. All other existing sqrt operations use the same primitive.

## 5. Boundary values, quantization and serialization

| Value crossing Market Handoff | Value policy |
|---|---|
| `volatility.atr_15m` | Round persisted ATR work state once HALF_EVEN to 10^-18; must be positive and available. |
| `volatility.atr_pct_15m` | Only when the corresponding eligible completed candle close is strictly positive and ATR work is available, compute `100 * atr_work / closed_candle_close` exactly, round to Q36, then HALF_EVEN to 10^-18; the export must be positive and available. At an otherwise eligible zero close the ratio is UNAVAILABLE and the division is not evaluated; retain the separate TR/ATR update under §3. Do not derive the ratio from wire-rounded ATR. |
| Exact factual prices/tick/lot sizes, bound reference prices | Preserve factual decimal value or the already-specified reference price/tick normalization; do not apply ATR rounding or invent another level. |
| Integer ages, counts, ordinals | Exact integer. No decimal approximation. |
| Direction, bindings, IDs and policy version | Exact existing discrete semantics; no numeric inference or reselection. |

No other new continuous field may cross this strict schema. A future derived numeric field requires an explicit policy class/version change before use; API does not compute Set trading decisions. Local continuous derived metrics use the work grid above, with a single 18-fractional-decimal canonical representation when retained in a diagnostic export. Such diagnostic rounding must not replace internal values used by Set gates.

Use plain canonical decimal strings: no exponent, plus sign, negative zero, redundant leading integer zero or trailing fractional zeros. Object serialization uses sorted-key compact UTF-8 JSON. Position uses exactly the received wire values for its existing formulas/comparisons and compares ratios by exact rational cross multiplication. Display rounding must not feed any gate.

Example: seed fourteen TR values of 1, then TR=2 gives work ATR `1.071428571428571428571428571428571429`; handoff ATR is exactly `1.071428571428571429`. At close=100 the canonical ATR percentage is the same number. Existing improvement minimum 0.10 ATR is met exactly by `0.1071428571428571429`; below fails and above passes. This selects one technical boundary representation, not a new threshold.

For F-003, with available current Q36 ATR work `A_t` and the corresponding eligible completed 15m close `C_t > 0`, the boundaries are:

```text
P_t = Q36(100 * A_t / C_t)
ATR_wire_t = Q18(A_t)
ATR_PCT_wire_t = Q18(P_t)
```

Numerical ATR_PCT `1` means one percent. When an otherwise eligible `C_t = 0`, `P_t` and the required ATR_PCT export are `UNAVAILABLE`; persist the reason and emit no valid required volatility handoff. Do not substitute zero, a previous ratio, a minimum positive value, NaN or infinity, or evaluate the quotient. Missing/malformed source data are not this zero-close branch. A valid zero ATR with positive close yields zero internal ATR_PCT, but cannot satisfy the positive-export requirement.

Both Q18 `volatility.atr_15m` and `volatility.atr_pct_15m` MUST be strictly positive and available for a valid handoff. A positive working value that rounds to zero remains ineligible; preserve its working state without clamping or reseeding. `UNAVAILABLE` is absence of an eligible value, never a numeric wire value. Position consumes exactly the received Q18 values and cannot recover hidden precision.

## 6. Implementation conformance

Acceptance tests derived from this policy must cover integer/rational quantization, exact midpoint sqrt, recursive seed/checkpoints, handoff validation, nonterminating ATR, exact boundaries and neighboring quanta, restart and raw-history replay. These tests do not certify a native source's completeness or a production indicator engine.


## 7. Internal normalization interface — T05 clarification

The Set-owned working-normalization operation, denoted normalize_working, returns
the section-2 working-grid normalized value as a canonical decimal string; normalize
is an alias with identical semantics. The separate Set-owned serialization operation,
denoted serialize_normalized_for_handoff, validates a canonical working-grid input and
rounds it to the existing export class only when a defined boundary permits it.
It is not part of normalization and cannot feed an internal Set gate. Checkpoints
retain the working value plus policy/source proof. Exact-threshold and ±one
working-quantum tests on both signs precede export; no epsilon or policy-version
change is introduced. The serialization operation does not add a wire field.
