# F-004 Revised Specification Cycle 2

# Set Normalization, Percentile and Score Calculation

## 1. Identity

| Field | Value |
|---|---|
| Formula ID | F-004 |
| Formula name | Set normalization, percentile, and score calculation |
| Owner | Set |
| Formula family | MARKET_NORMALIZATION |
| Status | Revised candidate after Full Council Cycle 2 |
| Active baseline | `v1.2.14` |
| Numeric policy | `TT_SET_NUMERIC_V1` |
| Scope | `ALTCOIN_VS_BTC` Set direction-analysis scope |

This candidate incorporates the Council-defined arithmetic subset from Cycle 1,
the Cycle 2 closure of the local 5m ATR dependency, and the remaining
population-selector fixes required for F004-C02:

```text
F004-C02: inception/initialization-day eligibility and midnight same-clock selection
```

It does not modify active methodology files and does not implement runtime
logic.

## 2. Full Council Status

```text
FULL_COUNCIL_APPROVED = NO
ANOTHER_REVIEW_CYCLE_REQUIRED = YES
CURRENT_CANDIDATE = F-004_REVISED_SPEC_CYCLE_2
```

This document is the self-contained candidate for the next Full Council
re-review.

## 3. Intended Purpose

F-004 computes Set-owned normalized analytical values, percentiles, hard-gate
diagnostics, side-specific veto diagnostics, weighted factor contributions and
the pre-classification `DIRECTION_SCORE`.

F-004 supports Set formation and downstream direction classification. It does
not itself choose `LONG`, `SHORT` or `NONE`, does not produce a Market Handoff,
does not authorize an order, and does not measure profitability, executable
liquidity, trade authenticity or expected return.

## 4. Boundary With F-005

F-004 owns:

- canonical normalized values and percentiles;
- current and historical factor values required for the Set score;
- required-data status;
- hard-gate diagnostics;
- separate LONG-side and SHORT-side veto predicates;
- weighted contribution diagnostics;
- `DIRECTION_SCORE`.

F-005 owns:

- inclusive `+0.35` and `-0.35` score thresholds;
- candidate-side selection;
- application of the relevant side-specific vetoes;
- `LONG` / `SHORT` / `NONE`;
- primary rejection-stage resolution for final classification;
- directional matching and handoff.

No F-004 score, gate pass or veto state independently creates a match,
execution intent, Position approval or order authority.

## 5. Required Inputs

For altcoin classification support, the F-004 computation requires these
canonical inputs at the governed Set analytical cutoff:

```text
asset structure 1h
asset structure 15m
DE 15m
VNM 15m
VNM 5m
relative return 15m
aggressive delta 5m
time-of-day relative turnover 5m
ATR_PCT 15m percentile
BTC structure 1h
BTC return 15m z-score
```

Additional context-only metrics may be unavailable without making F-004
unavailable. Required inputs may not be fabricated, carried forward, replaced
with zero, replaced with a stale value or inferred from downstream state.

Certified upstream compatibility:

| Dependency | F-004 use |
|---|---|
| F-001 | Compatible formation evidence and signed 1m movement diagnostic; not an operand for 15m return, VNM or `DIRECTION_SCORE`. |
| F-002 | Compatible direction-neutral formation evidence; not a substitute for time-of-day quote turnover, aggressive flow or participation strength. |
| F-003 | Certified 15m ATR and ATR_PCT semantics for 15m volatility context and current/historical 15m ATR_PCT work values. F-003 does not certify the 5m instance. |
| Active SET methodology | Defines directional efficiency, swing states, time-of-day turnover, aggressive delta, BTC context, weights and gates. |
| `TT_SET_NUMERIC_V1` | Governs exact arithmetic, Q36 outputs, population variance, sqrt, exact counts/ranks and serialization boundaries. |

## 6. Numeric Semantics

Let:

```text
Q36(x) = exact value x rounded to 36 fractional decimal places
         using ROUND_HALF_EVEN
```

All sums, differences, products and quotients are exact integer/rational
expressions until the specified named output quantizer. Binary floating point,
epsilon comparisons, significant-digit rounding and display-rounded gates are
forbidden.

Population standard deviation uses:

```text
ddof = 0
mu = exact arithmetic mean
variance = exact sum((x - mu)^2) / n
sigma = correctly rounded TT_SET_NUMERIC_V1 sqrt(variance)
```

If `n = 0`, any population member is unavailable, or rounded `sigma = 0`, the
affected normalization is `UNAVAILABLE`.

## 7. Ordinary Completed-Day Population Rule

Let `evaluation_at` be the persisted governed Set analytical cutoff, not
request time, receipt time or restart time. Let `D` be `00:00:00Z` at the start
of the UTC day containing `evaluation_at`.

The ordinary completed-day candidate interval is:

```text
[D - 30 UTC calendar days, D)
```

The current incomplete UTC day is excluded even if some candles inside it are
complete. This is not a trailing-hours window, local-timezone window,
Portfolio-accounting-day window or exchange-session window.

### 7.1 Eligible completed days during warmup

F-004 uses the eligible observations inside the ordinary 30-day interval. A day
is eligible for a metric's ordinary population only when the required factual
source coverage, source identity, finality, pagination/snapshot proof,
completed-candle or bucket membership, and all derived metric dependencies for
that day are available and contradiction-free.

If the instrument or required factual series has a proven inception later than
`D - 30 UTC calendar days`, the interval before inception is treated as proven
absence, not missing requested data. The population may contain 14 through 29
eligible completed UTC days in that initial-history case.

Partial inception days do not count for ordinary completed-day warmup. For each
metric, the first countable ordinary UTC day is the first complete UTC calendar
day that starts at or after the later of:

```text
instrument_or_series_inception_time
metric_source_series_inception_time
first_time_the_metric_can_have_all_required_derived_dependencies_available
```

rounded forward to the next UTC midnight if that later time is not already a
UTC midnight.

The leading interval before that first countable full UTC day is a proven
initialization prefix, not a missing-data gap, when its absence follows only
from instrument/series inception or from legitimate metric initialization
requirements such as canonical ATR seed formation. F-004 may exclude that
leading initialization prefix from the reference population. This exception is
only for the leading prefix before the first countable full UTC day. It does
not permit excluding, skipping or replacing any later unavailable observation
inside a countable day.

Canonical recursive dependencies still process their factual initialization
prefixes. For example, 5m ATR must preserve the seed candles and ordered ATR
ancestry through the prefix even though those pre-first-availability
observations are not countable VNM reference outputs. The population rule
selects eligible reference observations; it does not reset, reseed or discard
the recursive dependency.

Historical zero-close ATR_PCT observations and non-positive VNM denominators
remain unavailable outputs. If they occur inside the leading initialization
prefix before the first countable full UTC day, they are part of the startup
unavailability and are not reference observations. If they occur on or after
the first countable full UTC day, the affected metric is `UNAVAILABLE`; F-004
may not skip the day or shorten the population around it.

If the requested historical data should exist for a completed day but source
coverage, pagination, finality, continuity, identity or required derived-value
eligibility is missing or contradictory, that day is not silently skipped. The
affected F-004 metric is `UNAVAILABLE` until the source condition is resolved.

If fewer than 14 eligible completed UTC days are available after applying the
rules above:

```text
required normalized metric = UNAVAILABLE
directional classification support = unavailable to F-005
missing_reason = DATA_UNAVAILABLE
```

No expanding window, trailing-hours substitute, alternate timezone, omitted-gap
shortcut or current-day inclusion is permitted.

### 7.2 Observation membership inside eligible days

Point events at the lower boundary are included and point events at the upper
boundary are excluded. Completed candle intervals and factual buckets must be
wholly contained in the selected interval; an interval whose exclusive end
equals the upper boundary is included.

Recursive indicator ancestry remains distinct from the ordinary population
window. The population window selects reference observations; it does not
reseed ATR, VNM or any recursive dependency at `D - 30`.

## 8. Same-Clock Time-of-Day Turnover Population

For `TOD_REL_TURNOVER`, the metric-specific selector is:

```text
input_timeframe = 5m
timezone = UTC
lookback_days = 30
minimum_warmup_days = 14
baseline_statistic = median
same_clock_bucket = true
turnover_basis = quote notional turnover
```

For a current completed 5m bucket, compare current 5m quote-notional turnover
to the median turnover of the same UTC clock bucket over prior completed
eligible days. The current observation never enters its own reference baseline.

The exact selector is the thirty prior completed eligible same-clock buckets
strictly before the current completed bucket. Let the current bucket be the
half-open interval:

```text
[bucket_start, bucket_end)
```

with `bucket_end <= evaluation_at`. The candidate reference buckets are the
same UTC clock bucket on the prior thirty UTC dates before `bucket_start`'s UTC
calendar date:

```text
[bucket_start - 1 UTC day, bucket_end - 1 UTC day)
[bucket_start - 2 UTC days, bucket_end - 2 UTC days)
...
[bucket_start - 30 UTC days, bucket_end - 30 UTC days)
```

The current bucket is excluded by the strict-prior rule even when `bucket_end`
is exactly UTC midnight. Therefore, for current bucket `[D - 5m, D)` at
`evaluation_at = D`, the reference set is the same `23:55-00:00 UTC` bucket on
the thirty preceding UTC dates:

```text
[D - 1 day - 5m, D - 1 day)
...
[D - 30 days - 5m, D - 30 days)
```

This metric-specific same-clock selector may reach one bucket whose start lies
before the ordinary `[D - 30 days, D)` day-window lower boundary at midnight.
That is intentional for `TOD_REL_TURNOVER` because SET defines it as a
same-clock lookback over prior completed eligible days, and the current
observation must never be included in its own baseline.

The same eligible-day rule in Section 7 applies to same-clock references:

- proven pre-inception or leading-initialization absence may yield 14 through
  29 eligible prior same-clock observations;
- missing or contradictory evidence for a day that should exist makes the
  metric `UNAVAILABLE`;
- fewer than 14 eligible prior same-clock observations makes the metric
  `UNAVAILABLE`.

F-004 must persist the selected same-clock bucket identities, their UTC
intervals and their source coverage proof. Replaying the same cutoff must select
the same bucket identities.

For eligible references, compute the median exactly. With an even count, use
the exact arithmetic average of the two middle sorted values. If the median
denominator is zero or undefined:

```text
TOD_REL_TURNOVER = UNAVAILABLE
```

Otherwise:

```text
TOD_REL_TURNOVER =
current_5m_turnover / median_prior_same_clock_5m_turnover
```

## 9. Local 5m ATR_PCT Dependency for VNM 5m

The local 5m VNM veto requires its own ATR_PCT instance:

```text
input_timeframe = 5m
window = 14
smoothing = Wilder
metric = ATR_PCT
```

This is an F-004-local dependency candidate for review. It reuses the same
formula family, exact arithmetic, source-eligibility principles and state
ancestry pattern as the certified F-003 ATR formula, but with the explicit
5-minute timeframe required by SET §16.2. It is not certified merely because
F-003 certifies the 15-minute instance.

For completed 5m candle `t`:

```text
TR_t = max(
    High_t - Low_t,
    abs(High_t - Close_(t-1)),
    abs(Low_t - Close_(t-1))
)
```

Canonical 5m seed:

```text
A_14_5m = Q36((TR_1 + TR_2 + ... + TR_14) / 14)
```

Canonical 5m recursive update:

```text
A_t_5m = Q36((13 * A_(t-1)_5m + TR_t) / 14)
```

When the current 5m ATR work state is available and the corresponding completed
5m close is positive:

```text
ATR_PCT_5m = Q36((100 * A_t_5m) / Close_t_5m)
ATR_PCT_decimal_5m = ATR_PCT_5m / 100
```

5m candle eligibility requires:

```text
0 <= Low <= Close <= High
```

with exact source identity, completed-only status, continuity, finality,
pagination/snapshot proof and canonical ordering. A factual predecessor close
need not lie inside the current candle range.

If a completed 5m candle is malformed, missing, incomplete, out of order,
contradictory, not final, or lacks the factual immediate predecessor close, the
affected 5m ATR/VNM computation is `UNAVAILABLE`. The ATR state does not
advance through that candle, the seed does not skip it, and no stale prior 5m
ATR_PCT may stand in for the current dependency.

If an otherwise eligible completed 5m candle has `Close_t_5m = 0`, the
`ATR_PCT_5m` quotient is not evaluated and `ATR_PCT_5m` is `UNAVAILABLE`. The
5m TR and ATR recurrence still preserve the factual candle and ancestry, as in
the F-003 zero-close pattern.

If `ATR_PCT_5m` is unavailable or `ATR_PCT_decimal_5m <= 0`, then `VNM_5m` and
the local momentum veto input are `UNAVAILABLE`.

5m ATR state must persist seed manifest, processed candle identities, prior
work value, source proof, numeric policy version and checkpoint digest. Restart
may restore only an authentic matching checkpoint and canonical subsequent
facts. Revised historical source content invalidates affected derived state and
does not authorize automatic correction acceptance, reseeding or reconciliation
release.

## 10. Normalized Metrics

For any required ordinary z-score metric with current value `x` and eligible
reference population `b_1..b_n`:

```text
z = Q36((x - mu) / sigma)
normalized_score = Q36(clip(z / 2, -1, +1))
```

Mean, variance and standard deviation use Section 6. The mean and variance are
not separately rounded. Missing current value, missing reference population,
fewer than 14 eligible completed UTC days, rounded `sigma = 0`, source
contradiction or invalid dependency makes the affected normalized metric
`UNAVAILABLE`.

Centered z-score sign is deviation from the historical population mean. A
positive raw return can produce negative momentum evidence if it is below its
historical mean.

## 11. Percentiles

For current value `x` and eligible reference values `b_1..b_n`:

```text
K = count(b_i <= x)
percentile = Q36(100 * K / n)
```

Ties count as `<=`. Equal-valued valid references do not make the percentile
undefined; if every reference equals current value, the percentile is `100`.
If `n = 0` or the required eligible-day minimum is not met, the percentile is
`UNAVAILABLE`.

## 12. Factor Formulas

### 12.1 Structure

Structure states map to:

```text
BULLISH   -> +1
AMBIGUOUS -> 0
BEARISH   -> -1
```

The structure score is:

```text
STRUCTURE_SCORE =
Q36(0.50 * STRUCTURE_1H + 0.50 * STRUCTURE_15M)
```

The active swing methodology defines pivot confirmation, ties, one-tick
structural comparisons and two-high/two-low requirements. F-004 consumes those
canonical states; it does not redefine them.

### 12.2 Directional Efficiency

The 15m directional-efficiency hard gate is:

```text
if DE_15m < 0.30:
    hard_gate = DIRECTIONAL_EFFICIENCY_GATE
```

The modifier is:

```text
DE_STRENGTH =
Q36(clip((DE_15m - 0.30) / 0.40, 0, 1))
```

Boundaries:

```text
DE_15m = 0.30 -> DE_STRENGTH = 0
DE_15m = 0.50 -> DE_STRENGTH = 0.50
DE_15m >= 0.70 -> DE_STRENGTH = 1
```

### 12.3 Primary 15m Momentum

```text
VNM_15m = RETURN_15m / ATR_PCT_decimal_15m
MOMENTUM_SCORE = Q36(clip(momentum_z / 2, -1, +1))
MOMENTUM_EFFECTIVE =
Q36(MOMENTUM_SCORE * (0.5 + 0.5 * DE_STRENGTH))
```

`ATR_PCT_decimal_15m` uses certified F-003 work values converted from percent
to decimal. If the required 15m ATR_PCT is unavailable or not positive,
`VNM_15m`, `momentum_z`, `MOMENTUM_SCORE` and `MOMENTUM_EFFECTIVE` are
`UNAVAILABLE`.

### 12.4 Local 5m Momentum Veto

```text
VNM_5m = RETURN_5m / ATR_PCT_decimal_5m
```

The `VNM_5m` z-score uses a separate same-symbol baseline of completed 5m VNM
observations over the eligible ordinary completed-day population. The local
momentum veto is side-specific:

```text
LONG-side veto active when local_5m_vnm_z <= -2.0
SHORT-side veto active when local_5m_vnm_z >= +2.0
```

The exact veto consumption belongs to F-005. F-004 produces the side-specific
boolean diagnostics and preserves the underlying z-score and availability
reason.

### 12.5 Relative Strength

```text
RELATIVE_RETURN_15m =
RETURN(asset, 15m) - RETURN(BTC, 15m)

RELATIVE_SCORE =
Q36(clip(relative_return_z / 2, -1, +1))
```

The relative-return z-score uses the same altcoin 15m relative-return
population under the ordinary eligible-day rule.

Relative contradiction veto diagnostics are side-specific:

```text
LONG-side relative veto active when relative_return_z <= -2.0
SHORT-side relative veto active when relative_return_z >= +2.0
```

### 12.6 Flow and Activity

Aggressive volume delta uses 5m buyer/seller-initiated quote notional:

```text
AGGRESSIVE_VOLUME_DELTA_PCT =
Q36(100 * (AggBuyNotional - AggSellNotional)
        / (AggBuyNotional + AggSellNotional))
```

If the denominator is zero, aggressive volume delta is `UNAVAILABLE`.

```text
FLOW_RAW = Q36(AGGRESSIVE_VOLUME_DELTA_PCT / 100)
```

Activity hard gate:

```text
if TOD_REL_TURNOVER < 0.70:
    hard_gate = ACTIVITY_GATE
```

Participation strength:

```text
PARTICIPATION_STRENGTH =
Q36(clip((TOD_REL_TURNOVER - 0.70) / 1.30, 0, 1))
```

Flow effective:

```text
FLOW_EFFECTIVE =
Q36(FLOW_RAW * (0.5 + 0.5 * PARTICIPATION_STRENGTH))
```

### 12.7 Volatility Percentile and Gate

The 15m ATR_PCT percentile uses certified F-003 work ATR_PCT observations in
the ordinary eligible completed-day population:

```text
ATR_PCT_15m_PERCENTILE =
Q36(100 * count(reference_ATR_PCT_15m <= current_ATR_PCT_15m) / n)
```

Volatility hard gate:

```text
if ATR_PCT_15m_PERCENTILE < 15:
    hard_gate = VOLATILITY_GATE

if ATR_PCT_15m_PERCENTILE > 97:
    hard_gate = VOLATILITY_GATE
```

Boundary values `15` and `97` pass.

### 12.8 BTC Context

```text
BTC_MOMENTUM_SCORE =
Q36(clip(BTC_RETURN_Z / 2, -1, +1))

BTC_CONTEXT_SCORE =
Q36(0.60 * BTC_STRUCTURE_SCORE + 0.40 * BTC_MOMENTUM_SCORE)
```

BTC uses its own aligned 15m return population over the ordinary eligible-day
baseline and confirmed 1h structure per active methodology.

BTC veto diagnostics are side-specific:

```text
LONG-side BTC veto active when BTC_CONTEXT_SCORE <= -0.70
SHORT-side BTC veto active when BTC_CONTEXT_SCORE >= +0.70
```

## 13. Direction Score

Weights are pinned methodology parameters:

```text
STRUCTURE          = 0.35
MOMENTUM           = 0.25
RELATIVE_STRENGTH  = 0.15
FLOW               = 0.15
BTC_CONTEXT        = 0.10
```

The canonical score is:

```text
DIRECTION_SCORE =
Q36(
    0.35 * STRUCTURE_SCORE
  + 0.25 * MOMENTUM_EFFECTIVE
  + 0.15 * RELATIVE_SCORE
  + 0.15 * FLOW_EFFECTIVE
  + 0.10 * BTC_CONTEXT_SCORE
)
```

All products and the sum remain exact until the single `DIRECTION_SCORE`
quantizer. The score range is `[-1, +1]` if all factors are available and in
range.

If any required factor is unavailable, the complete `DIRECTION_SCORE` is
`UNAVAILABLE`. Missing factors may not be replaced with zero, stale values,
neutral values or redistributed weights.

## 14. Weighted Contributions

For diagnostics, F-004 separately retains:

```text
STRUCTURE_CONTRIBUTION = Q36(0.35 * STRUCTURE_SCORE)
MOMENTUM_CONTRIBUTION  = Q36(0.25 * MOMENTUM_EFFECTIVE)
RELATIVE_CONTRIBUTION  = Q36(0.15 * RELATIVE_SCORE)
FLOW_CONTRIBUTION      = Q36(0.15 * FLOW_EFFECTIVE)
BTC_CONTRIBUTION       = Q36(0.10 * BTC_CONTEXT_SCORE)
```

These diagnostic values do not feed back into `DIRECTION_SCORE`. Their rounded
sum may differ from the canonical score by one or more working quanta.

## 15. Outputs

F-004 outputs:

- normalized z-scores and clipped factor scores;
- ATR_PCT percentile and gate status;
- `TOD_REL_TURNOVER`, `PARTICIPATION_STRENGTH` and activity status;
- `DE_STRENGTH` and directional-efficiency gate status;
- `MOMENTUM_EFFECTIVE`, `RELATIVE_SCORE`, `FLOW_EFFECTIVE`,
  `BTC_CONTEXT_SCORE`, `STRUCTURE_SCORE`;
- side-specific BTC, relative and local-momentum veto diagnostics;
- weighted contribution diagnostics;
- `DIRECTION_SCORE`;
- complete availability and missing-reason diagnostics.

F-004 does not output final direction, Market Handoff approval, order spec,
position size, stop, take profit, risk/reward, execution permission or live
trading authority.

## 16. Missing and Invalid Behavior

| Case | Required behavior |
|---|---|
| Fewer than 14 eligible completed UTC days | Required normalized metric `UNAVAILABLE`; F-005 classification support unavailable. |
| Proven 14-29 eligible completed UTC days during initial-history period | Use all eligible observations inside `[D - 30, D)`; do not expand backward outside provenance or include current incomplete day. |
| Missing day that should exist | Affected metric `UNAVAILABLE`; do not skip or shorten population. |
| Rounded `sigma = 0` | Affected z-score and normalized score `UNAVAILABLE`. |
| `TOD_REL_TURNOVER` denominator zero/undefined | `TOD_REL_TURNOVER`, participation strength and dependent flow effective value `UNAVAILABLE`. |
| Aggressive notional denominator zero | Aggressive delta and dependent flow values `UNAVAILABLE`. |
| 5m ATR_PCT unavailable or non-positive | `VNM_5m` and local momentum veto input `UNAVAILABLE`. |
| 15m ATR_PCT unavailable or non-positive | `VNM_15m` and dependent momentum values `UNAVAILABLE`. |
| Required factor unavailable | Complete `DIRECTION_SCORE` `UNAVAILABLE`; no weight redistribution. |
| Source contradiction or incomplete selected range | Affected computation `UNAVAILABLE` pending deterministic resolution. |
| Future or still-forming data | Excluded; cannot satisfy any F-004 input. |

`UNAVAILABLE` is not `FALSE`, not zero, not `FLAT`, not stale state and not a
neutral contribution.

## 17. Gates and Veto Diagnostics

Hard gates produced by F-004:

```text
DATA_UNAVAILABLE
DIRECTIONAL_EFFICIENCY_GATE
ACTIVITY_GATE
VOLATILITY_GATE
```

Veto diagnostics produced by F-004:

```text
BTC_VETO_LONG
BTC_VETO_SHORT
RELATIVE_VETO_LONG
RELATIVE_VETO_SHORT
LOCAL_MOMENTUM_VETO_LONG
LOCAL_MOMENTUM_VETO_SHORT
```

F-004 preserves `all_failed_gates[]`, `all_active_vetoes[]`, every underlying
value, threshold, comparison direction and availability reason. F-005 owns the
final primary rejection priority and side-specific consumption for
classification.

## 18. Time Semantics

F-004 is evaluated against a persisted governed Set analytical cutoff and the
selected completed-source populations. Restart, receipt time or a later
snapshot cannot replace that cutoff.

Ordinary reference populations use completed UTC calendar days. Current
incomplete UTC day data are excluded from ordinary normalization even when
individual candles are complete. Same-clock turnover uses its explicit UTC
5-minute clock-bucket selector. Recursive ATR ancestry is not reset by the
ordinary population boundary.

## 19. State, Replay and Restart

Set must persist:

- analytical cutoff and source selector identities;
- source manifests, coverage and finality evidence;
- numeric policy version;
- upstream formula versions;
- 5m ATR seed/checkpoint ancestry used by local VNM;
- reference population member identities;
- current values, z-scores, percentiles and normalized values;
- gate and veto diagnostics;
- weighted contributions and `DIRECTION_SCORE`;
- configuration versions, thresholds and weights.

Replay from identical admissible facts must reproduce identical named outputs.
Duplicate source identities cannot add observations. Out-of-order source facts
must be ordered before recursive processing. A recovered cycle reuses its
selection identity, cutoff and checkpoints.

Conflicting historical source content invalidates affected derived state and
blocks new eligible decisions rather than silently splicing inconsistent
history into frozen evidence. This document does not define automatic
corrected-history acceptance or reconciliation release.

## 20. Ownership

Set owns F-004 calculations, source selectors, derived state, diagnostics,
checkpoints and frozen evidence. API supplies factual data only. Position Rules
consume frozen Set/Market Handoff outputs and must not recompute F-004.

## 21. Approved Uses Candidate

If approved, F-004 may be used as:

- Set-local normalization and percentile calculation;
- Set-local factor and `DIRECTION_SCORE` producer;
- gate and veto diagnostic producer for F-005;
- audit/diagnostic evidence for Set formation.

## 22. Prohibited Interpretations

F-004 must not be interpreted as:

- final LONG/SHORT/NONE classification;
- probability of success;
- expected return;
- liquidity or execution-quality measure;
- proof of authentic market participation;
- complete regime classifier;
- risk model;
- order authorization;
- profitability validation.

## 23. Known Limitations

The score is a heuristic mixture of structure, historical anomalies and signed
flow. It can be centered against recent history such that positive raw movement
becomes negative evidence. It is backward-looking, sensitive to regime changes,
dependent on source completeness and not calibrated here as a predictor of net
profitability.

Activity and flow measure participation conditions, not executable depth,
slippage, spread or authenticity. ATR/VNM context measures relative movement,
not risk-adjusted edge.

## 24. Research Parameters and Empirical Validation

The following remain research/calibration questions, not blockers to a complete
mathematical specification if they are explicitly retained:

- gate thresholds `DE_MIN = 0.30`, activity `0.70`, volatility `[15,97]`;
- veto thresholds `2.0` and `0.70`;
- score weights `0.35/0.25/0.15/0.15/0.10`;
- centered-sign usefulness;
- symbol/side asymmetry;
- incremental net benefit after costs;
- robustness across regimes and liquidity states.

Approval of F-004 would not establish empirical trading effectiveness or live
deployment safety.

## 25. Re-Review Request

Council should re-review this candidate for:

1. closure of F004-C02 population eligibility;
2. closure of F004-C03 local 5m ATR_PCT dependency;
3. regression against the Council-defined arithmetic subset;
4. F-004/F-005 boundary preservation;
5. all eight expert perspectives and final approval decision.
