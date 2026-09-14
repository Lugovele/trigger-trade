# TriggerTrade Derived Metrics Catalog

**Document ID:** TT-DATA-002
**Version:** 0.5.0
**Status:** REVIEWED BASELINE — ALL TIERS CATALOGED
**Scope:** Canonical derived metrics, candidate metrics, and deferred/conditional metric families for TriggerTrade methodology
**Dependency:** `BYBIT_RAW_DATA_CATALOG` accepted baseline

---

## 1. Purpose

This version consolidates the reviewed metric architecture into one governed catalog: Tier A is fully specified; Tier B is retained only for genuinely incremental candidate metrics; Tier C preserves deferred/conditional metrics without implying edge.

A metric is a deterministic measurement of market state. It is **not** a trigger, a setup, a strategy, or evidence of edge.

No threshold, timeframe, cross-timeframe relationship, or combination defined later may be treated as profitable until it passes the TriggerTrade methodology lifecycle.

---

## 2. Governing rules

### 2.1 Metric identity and temporal parameters

A canonical metric may have many simultaneous instances.

Examples:

```text
RETURN(horizon=5m)
RETURN(horizon=1h)

OI_CHANGE_PCT(horizon=5m)
OI_CHANGE_PCT(horizon=15m)
OI_CHANGE_PCT(horizon=1h)
```

The metric name identifies **what is measured**. The temporal parameters identify **over what data and horizon it is measured**.

Allowed temporal parameter types:

- `input_timeframe` — granularity of bar-like inputs;
- `window` — number of input observations;
- `horizon` — elapsed measurement interval;
- `anchor` — reset/reference point such as UTC day or session open;
- `clock_bucket` — fixed time-of-day bucket used for seasonal normalization.

### 2.2 Timeframe is part of every metric instance

A trigger may later compare several instances of the same metric across horizons. Therefore implementations must preserve the full metric key, including temporal parameters.

### 2.3 Normalization is not a separate factor

Supported normalization modes may include:

- raw;
- percentage;
- ratio;
- percentile;
- z-score;
- ATR-normalized;
- volatility-normalized;
- time-of-day normalized;
- cross-sectional percentile rank.

Percentile/z-score transforms do not become separate canonical metrics unless they change the economic meaning.

### 2.4 Historical testability

Historical testability means only whether the metric can be reconstructed from approved historical sources defined by the raw-data baseline.

TriggerTrade does **not** require proprietary high-frequency archive collection to improve testability.

Statuses:

- `FULL` — reconstructable from approved historical data at the stated granularity;
- `LIMITED` — only some horizons/granularities are historically reconstructable;
- `NONE` — not suitable for the core historical trigger-evidence path under the current data baseline.

### 2.5 No implicit look-ahead

Every metric must be computable using only information available at its evaluation timestamp.

Confirmed structural features may depend on later bars **only if their availability time is shifted to the confirmation timestamp**.

---

# 3. Tier A full metric specifications


## 3.1 `TT-MET-PRICE-001` — RETURN

**Family:** Price
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure signed price change over a specified horizon.

**Approved raw dependencies**
`MKT-KLINE-001` trade-price close series; live implementation may use last traded price where explicitly specified.

**Canonical formula / definition**
`RETURN(t,h) = P_t / P_(t-h) - 1`

**Temporal parameters**
`horizon` required. Candidate research horizons are not fixed by this catalog.

**Allowed normalization / representation**
raw decimal return; percentage; percentile/z-score over a historical baseline where needed.

**Interpretation**
Positive = price appreciation; negative = price decline; magnitude measures directional displacement.

**Does NOT prove**
Trend persistence, future continuation, reversal probability, or whether the move is informed.

**Historical testability**
`FULL for horizons reconstructable from historical trade-price data.`

**Potential methodology roles**
context; momentum input; relative-performance input; trigger component candidate.

**Invalid / undefined cases**
Undefined when the reference price is missing/zero or when the required horizon is not fully available.

**Implementation invariants**
The price convention used for a study (close-to-close, event-price, last trade) must be explicit and consistent between research and live.


## 3.2 `TT-MET-PRICE-002` — CANDLE_RANGE_PCT

**Family:** Price / Candle geometry
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure total high-low excursion of a completed bar relative to its opening price.

**Approved raw dependencies**
`MKT-KLINE-001`: open, high, low.

**Canonical formula / definition**
`100 × (High - Low) / Open`

**Temporal parameters**
`input_timeframe` required.

**Allowed normalization / representation**
raw %; percentile/z-score by symbol and timeframe.

**Interpretation**
Higher values indicate larger bar-level realized excursion.

**Does NOT prove**
Direction, continuation, rejection, or whether volatility is abnormal without a baseline.

**Historical testability**
`FULL for historical kline intervals.`

**Potential methodology roles**
volatility context; candle-behavior input.

**Invalid / undefined cases**
Undefined when Open <= 0 or the bar is incomplete when a closed-bar metric is required.

**Implementation invariants**
Research must not mix open-candle and closed-candle versions under the same metric key.


## 3.3 `TT-MET-PRICE-003` — CANDLE_BODY_TO_RANGE

**Family:** Price / Candle geometry
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure how much of a bar's total range was converted into net open-to-close displacement.

**Approved raw dependencies**
`MKT-KLINE-001`: open, high, low, close.

**Canonical formula / definition**
`abs(Close - Open) / (High - Low)`

**Temporal parameters**
`input_timeframe` required.

**Allowed normalization / representation**
ratio in [0,1]; signed companion may be created by multiplying by `sign(Close-Open)` only when explicitly requested.

**Interpretation**
Near 1 = directional close with little intrabar retracement; near 0 = little net displacement relative to total excursion.

**Does NOT prove**
Continuation, reversal, buyer/seller control after the close, or future edge.

**Historical testability**
`FULL.`

**Potential methodology roles**
candle quality; setup/context component.

**Invalid / undefined cases**
Undefined when High == Low.

**Implementation invariants**
The canonical metric is unsigned. Direction comes from return/candle direction rather than being silently embedded.


## 3.4 `TT-MET-VOL-002` — ATR_PCT

**Family:** Volatility
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure local realized trading range normalized by price.

**Approved raw dependencies**
`MKT-KLINE-001`: high, low, close and previous close.

**Canonical formula / definition**
First compute `TR_t = max(H_t-L_t, abs(H_t-C_(t-1)), abs(L_t-C_(t-1)))`; then ATR using the declared smoothing rule; `ATR_PCT = 100 × ATR / Close`.

**Temporal parameters**
`window`, `input_timeframe`, and `smoothing` required. Default smoothing must never be implicit in research artifacts.

**Allowed normalization / representation**
raw %; percentile/z-score.

**Interpretation**
Higher ATR% means larger typical local range relative to price.

**Does NOT prove**
Direction, trend quality, or whether volatility will expand/contract next.

**Historical testability**
`FULL.`

**Potential methodology roles**
regime/context; volatility normalization; stop/risk research input.

**Invalid / undefined cases**
Undefined until sufficient warm-up observations exist or Close <= 0.

**Implementation invariants**
Wilder, SMA, or other smoothing variants must have distinct parameter keys. No silent substitution.


## 3.5 `TT-MET-VOL-003` — REALIZED_VOLATILITY

**Family:** Volatility
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure dispersion of observed returns over a declared sampling grid and window.

**Approved raw dependencies**
`MKT-KLINE-001` close series or approved sampled trade-price series.

**Canonical formula / definition**
Canonical unannualized form: `RV = sqrt(sum(r_i^2))` over the measurement window, where `r_i = ln(P_i/P_(i-1))`.

**Temporal parameters**
`sampling_interval` and `window`/`horizon` required. Annualization is optional output metadata, not the canonical value.

**Allowed normalization / representation**
raw unannualized RV; annualized transform; percentile/z-score.

**Interpretation**
Higher values indicate more realized price variability over the observed interval.

**Does NOT prove**
Direction, tradability by itself, or future volatility.

**Historical testability**
`FULL where sampling data is historically available.`

**Potential methodology roles**
regime/context; volatility normalization; cross-asset comparison.

**Invalid / undefined cases**
Undefined with insufficient observations, missing sampling points beyond the declared gap policy, or non-positive prices.

**Implementation invariants**
Sampling interval and gap handling must be identical between backtest and live calculations.


## 3.6 `TT-MET-VOL-004` — VOLATILITY_RATIO

**Family:** Volatility
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure short-horizon volatility relative to a longer baseline.

**Approved raw dependencies**
Derived from one approved volatility definition such as `ATR_PCT` or `REALIZED_VOLATILITY`.

**Canonical formula / definition**
`VOL_SHORT / VOL_LONG`

**Temporal parameters**
`volatility_definition`, `short_window/horizon`, `long_window/horizon`, and input granularity required.

**Allowed normalization / representation**
raw ratio; percentile/z-score.

**Interpretation**
>1 indicates current/short volatility exceeds the longer baseline; <1 indicates relative contraction.

**Does NOT prove**
That expansion will continue, that contraction precedes breakout, or directional bias.

**Historical testability**
`FULL if both component volatility metrics are FULL.`

**Potential methodology roles**
regime/context; compression/expansion input.

**Invalid / undefined cases**
Undefined when long baseline is zero or unavailable.

**Implementation invariants**
Numerator and denominator must use the same volatility definition and compatible sampling.


## 3.7 `TT-MET-ACT-002` — RELATIVE_TURNOVER

**Family:** Activity / Liquidity
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure current traded notional relative to the asset's own recent baseline.

**Approved raw dependencies**
`MKT-KLINE-001` turnover or equivalent approved aggregation from public trades.

**Canonical formula / definition**
`CurrentTurnoverBucket / BaselineTurnover`, where the baseline statistic is declared (mean or median) over prior comparable buckets.

**Temporal parameters**
`input_timeframe`/bucket size, `lookback`, and `baseline_statistic` required.

**Allowed normalization / representation**
raw ratio; percentile/z-score.

**Interpretation**
>1 means current notional activity exceeds the chosen recent baseline.

**Does NOT prove**
Direction, informed trading, breakout validity, or abnormality relative to the same time of day.

**Historical testability**
`FULL using historical turnover bars.`

**Potential methodology roles**
activity context; liquidity context; trigger component candidate.

**Invalid / undefined cases**
Undefined when baseline is zero or warm-up is incomplete.

**Implementation invariants**
Current bucket must not be included in its own baseline unless explicitly specified.


## 3.8 `TT-MET-ACT-003` — TIME_OF_DAY_RELATIVE_TURNOVER

**Family:** Activity / Temporal
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure current traded notional relative to what is normal for the same clock-time bucket.

**Approved raw dependencies**
`MKT-KLINE-001` turnover plus UTC timestamp.

**Canonical formula / definition**
`CurrentTurnover(clock_bucket) / BaselineSameClockBucket`, using prior days only.

**Temporal parameters**
`clock_bucket`, `lookback_days`, `baseline_statistic`, and timezone/session taxonomy required.

**Allowed normalization / representation**
raw ratio; percentile/z-score relative to same-time history.

**Interpretation**
Separates genuinely unusual activity from routine intraday liquidity seasonality.

**Does NOT prove**
Direction, edge, or whether activity is abnormal under a different session taxonomy.

**Historical testability**
`FULL where historical turnover and timestamps are available.`

**Potential methodology roles**
intraday context; abnormal-activity detection; regime component.

**Invalid / undefined cases**
Undefined with insufficient same-clock history or invalid/missing bucket assignment.

**Implementation invariants**
Only completed historical days/buckets preceding evaluation time may enter the baseline.


## 3.9 `TT-MET-TREND-004` — DIRECTIONAL_EFFICIENCY

**Family:** Trend
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure how efficiently price travelled in one net direction versus the total path travelled.

**Approved raw dependencies**
`MKT-KLINE-001` close series.

**Canonical formula / definition**
`abs(P_t - P_(t-n)) / sum_{i=1..n} abs(P_i - P_(i-1))`

**Temporal parameters**
`window`, `input_timeframe` required.

**Allowed normalization / representation**
ratio [0,1]; percentile optional.

**Interpretation**
Near 1 = smooth directional path; near 0 = high path noise relative to net movement.

**Does NOT prove**
Direction itself, future continuation, or economic cause.

**Historical testability**
`FULL.`

**Potential methodology roles**
trend/regime context; setup-quality candidate.

**Invalid / undefined cases**
Undefined when total path denominator is zero.

**Implementation invariants**
The metric is unsigned; pair with `RETURN` for direction.


## 3.10 `TT-MET-TREND-006` — VWAP_DISTANCE

**Family:** Trend / Location
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure price location relative to a volume-weighted average price anchored to a declared period.

**Approved raw dependencies**
`MKT-KLINE-001` price/turnover/volume or `FLOW-TRADE-001` executions, depending declared implementation.

**Canonical formula / definition**
`VWAP = sum(price_i × volume_i) / sum(volume_i)`; `VWAP_DISTANCE = 100 × (P_t - VWAP) / VWAP`.

**Temporal parameters**
`anchor` required (e.g., UTC day/session); source granularity required.

**Allowed normalization / representation**
percentage; ATR-normalized; percentile optional.

**Interpretation**
Positive means price above anchored VWAP; magnitude measures extension from the volume-weighted reference.

**Does NOT prove**
Fair value, reversion probability, continuation, or institutional positioning.

**Historical testability**
`FULL when reconstructed from historical bars using the declared approximation; exact trade-tape VWAP depends on archive availability.`

**Potential methodology roles**
location/context; setup component.

**Invalid / undefined cases**
Undefined when cumulative anchored volume is zero or anchor data is incomplete.

**Implementation invariants**
Bar-based VWAP and trade-level VWAP are distinct calculation modes and must not be silently mixed.


## 3.11 `TT-MET-MOM-001` — VOLATILITY_NORMALIZED_MOMENTUM

**Family:** Momentum
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure directional price displacement relative to prevailing volatility.

**Approved raw dependencies**
`RETURN` plus a declared volatility metric (`ATR_PCT` or `REALIZED_VOLATILITY`).

**Canonical formula / definition**
Canonical family form: `RETURN(horizon) / VOLATILITY_SCALE`, with scale definition explicitly declared.

**Temporal parameters**
`horizon`, `volatility_definition`, volatility parameters required.

**Allowed normalization / representation**
signed ratio; percentile/z-score.

**Interpretation**
Large positive/negative magnitude means movement is large relative to normal volatility.

**Does NOT prove**
Continuation, reversal, trend quality, or edge.

**Historical testability**
`FULL when both components are FULL.`

**Potential methodology roles**
momentum/context; cross-asset comparability; trigger component candidate.

**Invalid / undefined cases**
Undefined when volatility scale is zero/unavailable.

**Implementation invariants**
The exact volatility denominator is part of the metric key; ATR-normalized and RV-normalized instances are not interchangeable.


## 3.12 `TT-MET-STRUCT-001` — SWING_POINT

**Family:** Market Structure
**Specification status:** `DEFINED — TIER A`

**Purpose**
Create an objective confirmed local high or low using a declared pivot rule.

**Approved raw dependencies**
`MKT-KLINE-001` high/low series.

**Canonical formula / definition**
For symmetric pivot `(L,R)`: a swing high at bar i requires `High_i` greater than the selected comparison rule across L bars before and R bars after; swing low analogously.

**Temporal parameters**
`input_timeframe`, `left_bars`, `right_bars`, tie rule, strict/non-strict comparison required.

**Allowed normalization / representation**
price level plus categorical side (`HIGH`/`LOW`); optional ATR-normalized prominence may be added later.

**Interpretation**
Defines reproducible structural pivots instead of discretionary visual swings.

**Does NOT prove**
That the level will hold, reverse price, contain liquidity, or create edge.

**Historical testability**
`FULL.`

**Potential methodology roles**
structure construction; level generation; setup/context.

**Invalid / undefined cases**
A candidate pivot is not available until the required right-side confirmation bars have closed.

**Implementation invariants**
Availability timestamp = confirmation time, not pivot bar time. Backtests must never expose the pivot earlier.


## 3.13 `TT-MET-STRUCT-002` — SWING_SEQUENCE_STATE

**Family:** Market Structure
**Specification status:** `DEFINED — TIER A`

**Purpose**
Describe structural progression from consecutive confirmed swing highs and lows.

**Approved raw dependencies**
`SWING_POINT` outputs.

**Canonical formula / definition**
Compare the latest confirmed same-side pivots and alternating structure to classify `HH`, `HL`, `LH`, `LL`, or an explicitly defined neutral/ambiguous state.

**Temporal parameters**
inherits pivot parameters; `lookback_swings` if more than the last pair is used.

**Allowed normalization / representation**
categorical state; optional persistence count.

**Interpretation**
Summarizes whether confirmed structure is progressing upward, downward, or ambiguously.

**Does NOT prove**
Trend continuation, reversal, or predictive edge.

**Historical testability**
`FULL if underlying swings are FULL.`

**Potential methodology roles**
market-structure context; regime input.

**Invalid / undefined cases**
Undefined when insufficient confirmed pivots exist.

**Implementation invariants**
Classification rules must be deterministic, including equal-high/equal-low tolerance.


## 3.14 `TT-MET-STRUCT-003` — RANGE_BOUNDARY

**Family:** Market Structure
**Specification status:** `DEFINED — TIER A`

**Purpose**
Define current upper/lower boundaries of a reproducible local trading range.

**Approved raw dependencies**
`MKT-KLINE-001` high/low/close; optional `SWING_POINT` depending rule.

**Canonical formula / definition**
No single universal formula. Allowed implementations must declare one range rule, e.g. rolling extrema or confirmed-pivot enclosure. Output is `(lower_bound, upper_bound)`.

**Temporal parameters**
`range_rule`, `input_timeframe`, lookback/pivot parameters required.

**Allowed normalization / representation**
price levels; optional ATR/percentage width derived separately.

**Interpretation**
Provides objective structural reference levels for location and later event definitions.

**Does NOT prove**
That price is mean-reverting, that a breakout will fail/succeed, or that the range is tradeable.

**Historical testability**
`FULL for approved deterministic bar-based rules.`

**Potential methodology roles**
structure/location; reference level generation.

**Invalid / undefined cases**
Undefined if the chosen rule has insufficient history or fails its own qualification criteria.

**Implementation invariants**
The range rule must be frozen inside a research specification; discretionary chart selection is prohibited.


## 3.15 `TT-MET-STRUCT-005` — DISTANCE_TO_LEVEL

**Family:** Market Structure / Location
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure signed distance from current price to a declared reference level.

**Approved raw dependencies**
Current price plus an approved level source such as `RANGE_BOUNDARY`, `SWING_POINT`, previous session/day high/low, VWAP, etc.

**Canonical formula / definition**
Percent form: `100 × (P_t - Level) / Level`; ATR-normalized form: `(P_t - Level) / ATR`.

**Temporal parameters**
`level_type`, level parameters, `normalization`, current-price convention required.

**Allowed normalization / representation**
signed percentage or normalized distance.

**Interpretation**
Shows whether price is above/below and how far from a defined level.

**Does NOT prove**
Support/resistance effectiveness, reversal probability, breakout validity, or edge.

**Historical testability**
`FULL when both price and level are historically reconstructable.`

**Potential methodology roles**
location/context; setup/trigger component candidate.

**Invalid / undefined cases**
Undefined if the level does not yet exist or its normalization denominator is invalid.

**Implementation invariants**
Level availability timestamps must be respected; future session/day highs or unconfirmed pivots cannot leak backward.


## 3.16 `TT-MET-OI-002` — OI_CHANGE_PCT

**Family:** Open Interest
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure expansion or contraction of outstanding derivative positioning over a specified horizon.

**Approved raw dependencies**
`DERIV-OI-001` historical open interest.

**Canonical formula / definition**
`100 × (OI_t / OI_(t-h) - 1)`

**Temporal parameters**
`horizon` required and must respect available historical OI granularity.

**Allowed normalization / representation**
raw %; percentile/z-score over comparable historical changes.

**Interpretation**
Positive = net open-interest expansion; negative = contraction.

**Does NOT prove**
Whether new positions are long or short, future price direction, or whether change represents informed positioning.

**Historical testability**
`FULL only for Bybit-supported historical OI intervals/horizons; sub-native historical claims are prohibited.`

**Potential methodology roles**
derivatives context; setup/trigger component candidate; cross-horizon comparison.

**Invalid / undefined cases**
Undefined when reference OI <=0, missing, or the requested horizon cannot be aligned to approved history.

**Implementation invariants**
Do not interpolate historical OI into unsupported finer horizons and label it native.


## 3.17 `TT-MET-DERIV-001` — FUNDING_RATE

**Family:** Derivatives Pricing
**Specification status:** `DEFINED — TIER A`

**Purpose**
Represent the exchange-native perpetual funding rate applicable to the instrument/funding interval.

**Approved raw dependencies**
`DERIV-FUND-001` funding history/current ticker context plus instrument metadata for interval semantics.

**Canonical formula / definition**
Pass-through exchange-native funding rate; no derived formula required.

**Temporal parameters**
`funding_interval` and observation timestamp required.

**Allowed normalization / representation**
raw rate; annualized display transform optional; percentile/z-score optional.

**Interpretation**
Sign and magnitude describe current funding transfer pressure between long and short sides under Bybit mechanics.

**Does NOT prove**
Future direction, crowding by itself, or that positive funding means longs will lose money on the trade overall.

**Historical testability**
`FULL for official funding history.`

**Potential methodology roles**
crowding/context; carry-cost input.

**Invalid / undefined cases**
Undefined/stale if no applicable funding observation is available for the instrument.

**Implementation invariants**
Never compare rates across instruments/periods without accounting for funding interval conventions.


## 3.18 `TT-MET-DERIV-003` — PREMIUM_INDEX

**Family:** Derivatives Pricing
**Specification status:** `DEFINED — TIER A`

**Purpose**
Represent the exchange-defined perpetual premium/discount signal relative to underlying reference mechanics.

**Approved raw dependencies**
`MKT-PREM-001` premium-index history.

**Canonical formula / definition**
Use exchange-native Premium Index value/series as defined by Bybit.

**Temporal parameters**
`input_timeframe`/horizon where bar series is used.

**Allowed normalization / representation**
raw; change over horizon; percentile/z-score as transforms.

**Interpretation**
Higher positive values indicate stronger perp premium pressure; negative values indicate discount pressure under the exchange definition.

**Does NOT prove**
Direction, future mean reversion, or positioning side by itself.

**Historical testability**
`FULL for supported historical premium-index kline intervals.`

**Potential methodology roles**
derivatives context; crowding/pressure input.

**Invalid / undefined cases**
Undefined where premium index is unavailable for the instrument/time.

**Implementation invariants**
Do not substitute mark-index spread for Premium Index; they are related but distinct constructs.


## 3.19 `TT-MET-DERIV-004` — MARK_INDEX_SPREAD_PCT

**Family:** Derivatives Pricing
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure mark-price deviation from the index-price reference.

**Approved raw dependencies**
`MKT-MARK-001` mark price and `MKT-INDEX-001` index price aligned in time.

**Canonical formula / definition**
`100 × (MarkPrice - IndexPrice) / IndexPrice`

**Temporal parameters**
observation timestamp or `input_timeframe` required; alignment tolerance required.

**Allowed normalization / representation**
signed %; percentile/z-score.

**Interpretation**
Positive = mark above index; negative = mark below index.

**Does NOT prove**
Tradable basis capture, future direction, or exact funding outcome.

**Historical testability**
`FULL where mark/index historical bars are available and alignable.`

**Potential methodology roles**
derivatives pricing context; stress/crowding input.

**Invalid / undefined cases**
Undefined if index price <=0 or timestamps cannot be aligned within declared tolerance.

**Implementation invariants**
No forward-fill across gaps beyond the explicit alignment policy.


## 3.20 `TT-MET-FLOW-001` — AGGRESSIVE_VOLUME_DELTA_PCT

**Family:** Aggressive Trade Flow
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure imbalance between taker-buy and taker-sell executed volume over a declared horizon.

**Approved raw dependencies**
`FLOW-TRADE-001` public executions with aggressor/taker side, price and size.

**Canonical formula / definition**
`100 × (BuyAggressiveVolume - SellAggressiveVolume) / (BuyAggressiveVolume + SellAggressiveVolume)`

**Temporal parameters**
`horizon` or aggregation bucket; quantity basis (`base_volume` or `notional`) must be declared.

**Allowed normalization / representation**
signed % in [-100,100]; percentile/z-score.

**Interpretation**
Positive = more executed aggressive buy volume; negative = more aggressive sell volume.

**Does NOT prove**
Future direction, passive-side weakness, or causality between flow and subsequent price.

**Historical testability**
`FULL where official historical public-trade archive provides adequate coverage; otherwise scope must match available archive.`

**Potential methodology roles**
order-flow context; setup/trigger component candidate.

**Invalid / undefined cases**
Undefined when total aggressive volume in the interval is zero.

**Implementation invariants**
Bybit side semantics must be mapped once in the raw-data adapter and kept consistent across history/live.


## 3.21 `TT-MET-FLOW-003` — TRADE_INTENSITY

**Family:** Aggressive Trade Flow
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure execution-event frequency per unit time.

**Approved raw dependencies**
`FLOW-TRADE-001` public trade events.

**Canonical formula / definition**
`TradeCount / HorizonDuration`

**Temporal parameters**
`horizon` and output unit (e.g. trades/sec or trades/min) required.

**Allowed normalization / representation**
raw rate; time-of-day normalized ratio; percentile/z-score.

**Interpretation**
Higher values mean more frequent matching/execution activity.

**Does NOT prove**
Direction, large notional participation, or informed flow.

**Historical testability**
`FULL where historical public trades are available.`

**Potential methodology roles**
activity/order-flow context; event-intensity input.

**Invalid / undefined cases**
Undefined for incomplete/gapped intervals that violate the declared data-completeness policy.

**Implementation invariants**
Aggregated multi-fill messages must be counted using actual trade records, not WebSocket message count.


## 3.22 `TT-MET-REL-001` — BENCHMARK_RETURN

**Family:** Cross-Market
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure price change of an explicitly selected benchmark such as BTC or ETH over the same horizon as the subject asset.

**Approved raw dependencies**
`MKT-KLINE-001` for benchmark instrument.

**Canonical formula / definition**
Same formula as `RETURN`: `P_t/P_(t-h)-1`.

**Temporal parameters**
`benchmark`, `horizon`, price convention required.

**Allowed normalization / representation**
raw/percentage return.

**Interpretation**
Represents broad directional movement of the chosen crypto benchmark.

**Does NOT prove**
Causality for the subject asset or market-wide regime by itself.

**Historical testability**
`FULL.`

**Potential methodology roles**
market context; relative-performance decomposition.

**Invalid / undefined cases**
Undefined if benchmark data is unavailable/alignment fails.

**Implementation invariants**
Asset and benchmark observations must use synchronized timestamps and equivalent horizon semantics.


## 3.23 `TT-MET-REL-002` — RELATIVE_RETURN

**Family:** Cross-Market
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure asset performance in excess of a selected benchmark's raw return.

**Approved raw dependencies**
`RETURN(asset)` and `BENCHMARK_RETURN`.

**Canonical formula / definition**
`RETURN_asset(h) - RETURN_benchmark(h)`

**Temporal parameters**
`benchmark`, `horizon` required.

**Allowed normalization / representation**
signed return difference; cross-sectional percentile optional.

**Interpretation**
Positive = asset outperformed benchmark over the same horizon; negative = underperformed.

**Does NOT prove**
Coin-specific alpha because differing beta is not removed.

**Historical testability**
`FULL.`

**Potential methodology roles**
relative-strength context; coin selection; setup component.

**Invalid / undefined cases**
Undefined if either aligned return is unavailable.

**Implementation invariants**
Use beta-adjusted relative return when the research question requires removing benchmark sensitivity.


## 3.24 `TT-MET-REL-005` — BETA_ADJUSTED_RELATIVE_RETURN

**Family:** Cross-Market
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure asset movement beyond the move implied by its estimated sensitivity to the benchmark.

**Approved raw dependencies**
Asset and benchmark returns; historical window for beta estimation.

**Canonical formula / definition**
`ResidualReturn = R_asset(h) - beta_est × R_benchmark(h)` where `beta_est = Cov(r_asset,r_benchmark)/Var(r_benchmark)` on the declared trailing estimation window.

**Temporal parameters**
`benchmark`, `horizon`, `beta_window`, `beta_sampling_interval` required.

**Allowed normalization / representation**
signed residual return; percentile/z-score.

**Interpretation**
Positive = asset outperformed what its estimated benchmark beta would imply.

**Does NOT prove**
True causal alpha, persistence, or independence from all market factors.

**Historical testability**
`FULL with historical aligned prices.`

**Potential methodology roles**
relative-strength context; coin selection; idiosyncratic-move input.

**Invalid / undefined cases**
Undefined when benchmark variance is zero, beta window is insufficient, or aligned observations are missing.

**Implementation invariants**
Beta must be estimated using only data strictly prior to the evaluated return interval unless the study explicitly defines a contemporaneous estimator without leakage.


## 3.25 `TT-MET-REL-009` — MARKET_BREADTH

**Family:** Cross-Market
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure the proportion of the eligible trading universe satisfying a declared directional/performance condition.

**Approved raw dependencies**
Historical/current price data for the approved TriggerTrade universe.

**Canonical formula / definition**
`Count(condition_i == true) / Count(eligible_i)`

**Temporal parameters**
`universe`, `horizon`, `condition`, eligibility timestamp required.

**Allowed normalization / representation**
ratio [0,1] or percentage.

**Interpretation**
Shows how broad or narrow a market move is across eligible instruments.

**Does NOT prove**
Future direction, causality, or that all constituents carry equal economic importance.

**Historical testability**
`FULL for historically reconstructable universe membership and price condition.`

**Potential methodology roles**
market/regime context; confirmation input.

**Invalid / undefined cases**
Undefined when eligible universe count is below the declared minimum.

**Implementation invariants**
Universe membership must be point-in-time to avoid survivorship bias once historical listing data is available/used.


## 3.26 `TT-MET-REL-007` — CROSS_SECTIONAL_MOMENTUM_RANK

**Family:** Cross-Market / Selection
**Specification status:** `DEFINED — TIER A`

**Purpose**
Rank each eligible coin's momentum relative to the contemporaneous tradable universe.

**Approved raw dependencies**
`RETURN` or declared momentum metric for all eligible universe members.

**Canonical formula / definition**
Percentile rank of the declared momentum value across the point-in-time eligible universe.

**Temporal parameters**
`universe`, `momentum_definition`, `horizon`, tie rule required.

**Allowed normalization / representation**
percentile rank [0,1] or [0,100].

**Interpretation**
High rank = stronger contemporaneous momentum than most eligible coins.

**Does NOT prove**
Absolute bullishness, future continuation, or tradability.

**Historical testability**
`FULL if point-in-time universe and underlying metric are reconstructable.`

**Potential methodology roles**
coin selection; relative-strength context.

**Invalid / undefined cases**
Undefined when too few eligible assets have valid observations.

**Implementation invariants**
Ranking must not include future-listed/delisted assets outside the point-in-time universe.


## 3.27 `TT-MET-TIME-001` — SESSION_ID

**Family:** Temporal Context
**Specification status:** `DEFINED — TIER A`

**Purpose**
Map each timestamp into a deterministic intraday session/context bucket.

**Approved raw dependencies**
UTC timestamp only; session taxonomy is methodology configuration.

**Canonical formula / definition**
Deterministic categorical mapping from timestamp to configured session windows.

**Temporal parameters**
`session_taxonomy`, timezone required. UTC is canonical storage; named market sessions are labels.

**Allowed normalization / representation**
categorical.

**Interpretation**
Identifies recurring liquidity/activity context without asserting directional bias.

**Does NOT prove**
That a session is profitable, volatile, trending, or directionally biased.

**Historical testability**
`FULL.`

**Potential methodology roles**
context/regime segmentation; diagnostics.

**Invalid / undefined cases**
Undefined only if timestamp is invalid or taxonomy has uncovered/overlapping buckets contrary to its rules.

**Implementation invariants**
Session definitions must be versioned. Daylight-saving handling for named regional sessions must be explicit.


## 3.28 `TT-MET-EXEC-001` — SPREAD_PCT

**Family:** Execution / Tradability
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure instantaneous top-of-book bid-ask friction.

**Approved raw dependencies**
`FLOW-BOOK-001` best bid and best ask, or an approved top-of-book source.

**Canonical formula / definition**
`100 × (Ask1 - Bid1) / ((Ask1 + Bid1)/2)`

**Temporal parameters**
`observation_time`; optional aggregation statistic over horizon.

**Allowed normalization / representation**
raw % or basis points.

**Interpretation**
Higher spread means higher immediate crossing friction and typically poorer tradability.

**Does NOT prove**
Depth, slippage for larger orders, direction, or future volatility.

**Historical testability**
`LIMITED under the current baseline because full historical top-of-book replay is not assumed.`

**Potential methodology roles**
live execution eligibility; current tradability; cost model input where historically supported.

**Invalid / undefined cases**
Undefined for crossed/invalid book, missing side, or non-positive mid.

**Implementation invariants**
Do not use as a core historically validated trigger input when equivalent historical fidelity is unavailable.


## 3.29 `TT-MET-EXEC-002` — TURNOVER_LIQUIDITY

**Family:** Execution / Tradability
**Specification status:** `DEFINED — TIER A`

**Purpose**
Measure recent traded notional as a coarse historically reconstructable liquidity/tradability proxy.

**Approved raw dependencies**
`MKT-KLINE-001` turnover.

**Canonical formula / definition**
`sum(Turnover_i)` over the declared trailing window.

**Temporal parameters**
`window/horizon`, input granularity required.

**Allowed normalization / representation**
raw notional; log transform; percentile/rank across universe.

**Interpretation**
Higher recent turnover generally indicates more active, more practically tradable markets.

**Does NOT prove**
Actual order-book depth, guaranteed low slippage, or execution quality at a specific order size.

**Historical testability**
`FULL.`

**Potential methodology roles**
universe eligibility; tradability filter; execution context.

**Invalid / undefined cases**
Undefined when historical turnover is missing beyond accepted gap policy.

**Implementation invariants**
Use as a proxy only; never label it direct market depth.


## 3.30 `TT-MET-EXEC-003` — ESTIMATED_ROUND_TRIP_COST

**Family:** Execution / Costs
**Specification status:** `DEFINED — TIER A`

**Purpose**
Estimate total expected explicit trading drag for entering and exiting a candidate position.

**Approved raw dependencies**
Fee configuration plus approved spread/slippage/funding inputs according to the research fidelity available.

**Canonical formula / definition**
Canonical decomposition: `EntryFee + ExitFee + ExpectedEntryCrossing/Slippage + ExpectedExitCrossing/Slippage + ExpectedFundingCost` expressed as % of notional or price.

**Temporal parameters**
`entry_order_type`, `exit_order_type`, fee tier/config, holding horizon, cost model version required.

**Allowed normalization / representation**
percentage/bps of notional; optionally R-units inside TRS research.

**Interpretation**
Provides the cost deduction required to convert gross statistical edge into net edge.

**Does NOT prove**
Exact realized cost, future fill quality, or directional alpha.

**Historical testability**
`FULL for fee/funding components; spread/slippage components may be LIMITED depending on historical fidelity. Research must use only components supported by its evidence source.`

**Potential methodology roles**
mandatory net-edge evaluation; execution/risk.

**Invalid / undefined cases**
Undefined when a required cost component/model input is absent for the declared study design.

**Implementation invariants**
Backtest cost assumptions must be conservative, explicit, versioned, and never silently replaced by live-only microstructure data.


---

# 4. Cross-timeframe use

The metric layer explicitly supports simultaneous instances of the same canonical metric.

Example:

```text
OI_CHANGE_PCT(horizon=5m)
OI_CHANGE_PCT(horizon=15m)
OI_CHANGE_PCT(horizon=1h)
```

A later hypothesis may evaluate:

- alignment;
- disagreement;
- acceleration/deceleration;
- threshold crossings;
- relative magnitude;
- sequencing across horizons.

None of these relationships is defined as a trading signal in this catalog.

---

# 5. Tier architecture

Tier A, Tier B, and Tier C are all retained in this catalog. Tier A contains the fully specified core metrics. Tier B contains only metrics that may add genuinely new information and therefore require incremental-value research. Tier C preserves classical indicators, microstructure, liquidation-derived, and external-source metrics for benchmark or hypothesis-specific use.

---

# 6. Baseline review requirements

This baseline has been reviewed against the following requirements; future revisions must preserve them:

1. every Tier A metric has an unambiguous economic meaning;
2. formulas do not duplicate another Tier A latent factor without a reason;
3. all temporal parameters are explicit;
4. live and historical calculation semantics are equivalent wherever historical validation is claimed;
5. structural metrics contain no look-ahead leakage;
6. cross-sectional metrics use point-in-time universe membership;
7. cost metrics distinguish historically evidenced components from current/live execution observations;
8. no metric definition contains an untested trading threshold or implied edge.

---

# 7. Next methodology layer

After the metric catalog baseline, the methodology defines triggers directly
from approved metrics and explicit comparison semantics. Sets may later combine
triggers; no separate mandatory Composite Market State or Condition layer is
required.

Examples of future research themes:

```text
PRICE_OI_RELATIONSHIP
VOLATILITY_STATE
TREND_STATE
STRUCTURE_LOCATION_STATE
RELATIVE_STRENGTH_STATE
FLOW_STATE
MARKET_BREADTH_STATE
TRADABILITY_STATE
```

Those conditions may then become components of explicit hypotheses and later trigger candidates.

---

**Current status:** `REVIEWED BASELINE — v0.5.0`
**Evidence status:** No metric, timeframe, threshold, relationship, or condition in this document constitutes a proven trading edge.


# 8. Final review decisions

The final review made the following governance corrections:

- removed duplicate Tier B entries that were only normalizations of Tier A metrics;
- kept `CROSS_SECTIONAL_MOMENTUM_RANK` only in Tier A;
- kept `SPREAD_PCT` only in Tier A and left deeper order-book microstructure in Tier C;
- clarified that standalone rolling beta may be researched in Tier B while beta estimation can remain an internal parameter of Tier A beta-adjusted relative return;
- preserved RSI, MACD, Stochastic, ADX/DMI, Bollinger Bands, MA-crossover families, and other classical indicators in Tier C so they are not lost;
- preserved liquidation and deep order-book metrics in Tier C without granting them core trigger-evidence status;
- reinforced that normalization, thresholds, crossover events, breakout/reclaim events, divergences, and multi-timeframe relationships belong to parameterization or later condition layers rather than becoming duplicate atomic metrics.

No Tier assignment constitutes evidence of trading edge.

# Tier B — Candidate / Incremental Value Required

Tier B contains metrics that may be useful, but must demonstrate incremental information value beyond Tier A before promotion into the core methodology.

Presence in Tier B does not imply trading edge. Promotion requires evidence that the metric materially improves regime classification, setup quality, trigger discrimination, execution quality, or risk diagnostics without merely re-expressing an existing Tier A factor.

## Tier B inventory

### Tier B normalization rule
Percentile, z-score, cross-sectional rank, and time-of-day normalization are **not separate Tier B metrics** when the underlying Tier A metric already supports that transform. They remain parameterized representations of the canonical metric. Tier B is reserved for constructs that change economic meaning or combine information in a genuinely new way.


### Trend / Directional Structure
- EMA slope
- SMA slope
- Moving-average spread
- EMA alignment state
- MA distance normalized by ATR
- Trend persistence ratio
- Directional persistence score

### Momentum / Acceleration
- Momentum acceleration
- Return acceleration
- Multi-horizon momentum alignment
- Price-momentum divergence candidates

### Volume / Activity Efficiency
- Volume-per-range
- Turnover-per-range
- Price movement per unit turnover
- Volume acceleration
- Turnover acceleration
- Abnormal activity score

### Open Interest / Derivatives Interaction
- OI-to-turnover ratio
- OI-to-volume ratio
- OI expansion score
- OI contraction score
- OI acceleration
- Price × OI state
- OI × Funding interaction

### Funding / Premium / Basis
- Funding change
- Funding acceleration
- Premium change
- Basis change
- Basis percentile
- Funding × OI crowding state

### Positioning
- Long/short ratio change
- Long/short percentile
- Long/short z-score
- Positioning acceleration
- Price-positioning divergence

### Trade Flow
- CVD slope
- CVD acceleration
- Trade-count imbalance
- Average aggressive trade size
- Large-trade volume
- Large-trade imbalance
- Burst intensity
- Flow divergence candidates

### Market Structure
- Consolidation duration
- Consolidation width
- Range compression score
- Range expansion score
- Structure compression score
- Distance to nearest confirmed swing
- Multi-timeframe structure alignment

### Cross-Market / Relative
- Rolling beta to BTC/benchmark (standalone context metric; beta estimation remains an internal dependency of `BETA_ADJUSTED_RELATIVE_RETURN`)
- Rolling correlation to BTC
- Rolling correlation to ETH
- Relative volatility
- Cross-sectional volatility rank
- Market dispersion
- Relative turnover rank

### Temporal / Session
- Session-relative return
- Session-relative volatility

## Promotion rule for Tier B
A Tier B metric may be promoted to Tier A only when research demonstrates at least one of the following:
- materially better regime discrimination;
- materially better setup or trigger separation;
- lower false-positive rate;
- improved robustness across coins/regimes;
- improved cost-adjusted expectancy;
- unique information not recoverable from existing Tier A metrics.

If it does not add incremental value, it remains Tier B or is dropped.

---

# Tier C — Deferred / Conditional

Tier C contains metrics that must remain available in the methodology catalog but are not part of the default core evidence layer.

Presence in catalog != endorsement as edge.

Tier C includes classic technical indicators, microstructure metrics, and metrics whose historical validation is structurally limited.

## Tier C.1 — Classical Technical Indicators

These indicators are retained because they are widely used in trading, may be useful for benchmark comparisons, and may become relevant to specific hypotheses.

### RSI
- Relative Strength Index
- Parameters: window, input timeframe
- Typical benchmark windows: 14 and alternatives
- Potential role: momentum / overextension context
- Constraint: derived entirely from price; incremental value versus Tier A momentum metrics must be demonstrated.

### MACD
- Moving Average Convergence Divergence
- Parameters: fast EMA, slow EMA, signal EMA, timeframe
- Components: MACD line, signal line, histogram
- Potential role: trend/momentum state
- Constraint: strongly derived from moving averages and price momentum.

### Stochastic Oscillator
- Parameters: lookback window, smoothing parameters, timeframe
- Components: %K, %D
- Potential role: relative close position within recent range
- Constraint: may duplicate range-position and momentum information.

### ADX / DMI
- Components: ADX, +DI, -DI
- Parameters: window, timeframe
- Potential role: trend-strength context
- Constraint: requires incremental-value testing against directional-efficiency and volatility/trend metrics.

### Bollinger Bands
- Parameters: moving-average window, standard-deviation multiplier, timeframe
- Components: middle band, upper band, lower band, bandwidth, %B
- Potential role: volatility regime, range position, expansion/compression context
- Constraint: bandwidth may overlap with Tier A realized-volatility/compression metrics.

### Moving-Average Crossover Family
- SMA/SMA crossover
- EMA/EMA crossover
- Price/MA crossover
- Fast/slow MA spread and crossover state
- Parameters: fast window, slow window, timeframe
- Potential role: trend-state benchmark or candidate setup component
- Constraint: crossover event is a condition, while MA values/spreads remain metrics.

## Tier C.2 — Additional Classical / Benchmark Indicators
- Commodity Channel Index (CCI)
- Williams %R
- Rate-of-Change oscillator variants
- TRIX
- KAMA-derived measures
- Donchian Channel position/bandwidth
- Keltner Channel position/bandwidth
- Average directional variants
- Classical pivot-based indicators

These remain deferred unless a specific hypothesis requires them.

## Tier C.3 — Order Book / Liquidity Microstructure

`SPREAD_PCT` itself remains Tier A as an execution/tradability metric. The deeper order-book constructs below are retained in Tier C and are not part of the default core trigger evidence path where sufficient historical validation is unavailable.

- Bid depth
- Ask depth
- Total depth
- Order-book imbalance
- Multi-level depth imbalance
- Microprice
- Microprice deviation
- Book slope
- Liquidity concentration
- Distance to largest bid liquidity
- Distance to largest ask liquidity
- Depth addition/removal rate
- Replenishment
- Depletion
- Sweep intensity
- Short-horizon book pressure

Methodology rule:
Realtime availability alone does not promote these metrics into core trigger evidence.

## Tier C.4 — Liquidation-Derived Metrics

- Long liquidation volume
- Short liquidation volume
- Total liquidation notional
- Liquidation delta
- Liquidation imbalance
- Liquidation count
- Liquidation intensity
- Liquidation / turnover ratio
- Liquidation spike score
- Liquidation clustering metrics

These remain cataloged but conditional where historical evidence is insufficient for robust validation.

## Tier C.5 — Other Conditional External Metrics

Potential future metrics from explicitly approved external sources may include:
- broader market breadth outside Bybit;
- derivatives positioning from other exchanges;
- options-implied volatility / skew;
- stablecoin flow proxies;
- BTC dominance or macro proxies.

These are outside the current Bybit-native baseline and require separate source approval before inclusion in the active methodology.

---

# Tier Governance

## Tier A — Core
Canonical metrics required for the default TriggerTrade methodology and fully specified in this document. Tier A means core observability, not proven predictive value.

#
# Tier B — Candidate / Incremental Value Required
Potentially useful metrics that must prove unique or incremental value before promotion.

## Tier C — Deferred / Conditional
Retained metrics that may be used for benchmarks or hypothesis-specific research, but are not default core evidence.

No metric tier implies trading profitability.
No metric becomes a trigger merely because it is available in the catalog.
No event predicate such as crossover, breakout, reclaim, threshold breach, divergence confirmation, or multi-timeframe alignment becomes an atomic metric merely because it is calculated from metrics. Such predicates belong to future trigger definitions or set/research layers when explicitly specified.

The promotion path remains:

Metric defined
→ trigger definition specified
→ Set or hypothesis formulated
→ research candidate
→ backtested evidence
→ subsequent methodology lifecycle stages
