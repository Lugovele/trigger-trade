# TriggerTrade Metrics Library V1

## Purpose

This library is the human-readable catalog for the 47 canonical, system, accounting, research, numeric, and state-rule objects used by TriggerTrade. It translates the normative formula and methodology sources into operational explanations suitable for later display under Trading Configuration -> Metrics.

The library is documentation only. It does not change formulas, thresholds, trading methodology, runtime behavior, source code, schemas, migrations, import logic, or UI logic.

## Scope

Included families:

- F-series: formula and system formula objects, F-001 through F-016.
- A-series: accounting objects, A-001 through A-009.
- M-series: research-only metric and aggregation objects, M-001 through M-008.
- N-series: numeric and normalization policies, N-001 through N-008.
- S-series: state and classification rules, S-001 through S-006.

Explicitly excluded:

- T-series objects. T-001 through T-011 are trading rules, configuration parameters, or thresholds, not Metrics Library entries.

## How to read this library

Each object has an owner, type, family, current canonical status, source-backed rule, direct dependencies, direct consumers, and boundaries. A formula object produces a numeric value or predicate. A state object classifies a state or decision condition. A policy object governs numeric representation, normalization, identity, time, or runtime separation. A research object is reporting-only and must not be promoted into the live trading decision path.

`UNAVAILABLE` means the object cannot produce an eligible result. It is not zero and does not permit a fallback unless the authoritative rule explicitly says so.

## Source authority

Source precedence for this library:

1. Final certified object specifications in `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/`.
2. Frozen methodology v1.2.15 under `docs/trading-methodology/`.
3. `docs/BACKEND_IMPLEMENTATION_MAP_V1_2_15.md` only for owner boundaries, dependency relationships, producer/consumer flow, canonical identity, and integration boundaries.
4. `docs/BACKEND_TARGET_MODEL.md` primarily for research-only M-series behavior and runtime isolation.
5. Current source code under `src/triggertrade/` only as an implementation cross-check.

This library does not use archived methodology, archived formula certification artifacts, old source packs, old review cycles, historical audit findings, legacy/demo code, or hardcoded Metrics UI text as primary semantic authority.

## Library Index

| ID | Display Name | Owner | Type | Family | Status |
|---|---|---|---|---|---|
| F-001 | 1m Price-Move Trigger | Set | TRADING_FORMULA | TRIGGER | CERTIFIED |
| F-002 | 1m Relative Participation Volume Confirmation | Set | TRADING_FORMULA | TRIGGER | CERTIFIED |
| F-003 | ATR / True Range / ATR_PCT | Set | TRADING_FORMULA | SET_ANALYTICS | CERTIFIED |
| F-004 | Set Normalization / Percentile / Direction Score | Set | TRADING_FORMULA | MARKET_NORMALIZATION | CERTIFIED |
| F-005 | Set Direction Classifier | Set | TRADING_FORMULA | LONG_SHORT | CERTIFIED |
| F-006 | LONG Dynamic Stop Branch | Position Rules | TRADING_FORMULA | LONG_SHORT | CERTIFIED |
| F-007 | SHORT Dynamic Stop Branch | Position Rules | TRADING_FORMULA | LONG_SHORT | CERTIFIED |
| F-008 | Planned Entry Reference Selection | Position Rules | TRADING_FORMULA | ENTRY | CERTIFIED |
| F-009 | Stop Calculation and Stop Rounding | Position Rules | TRADING_FORMULA | STOP | CERTIFIED |
| F-010 | Dynamic Take Profit Selection and Rounding | Position Rules | TRADING_FORMULA | DYNAMIC_TAKE | CERTIFIED |
| F-011 | Position Quantity and Actual Notional Construction | Position Rules | TRADING_FORMULA | POSITION_SIZING | CERTIFIED |
| F-012 | Risk/Reward and Minimum Net Edge | Position Rules | TRADING_FORMULA | RISK_REWARD | CERTIFIED |
| F-013 | Pending Entry Market Invalidation | Set | SYSTEM_FORMULA | SET_ANALYTICS | CERTIFIED |
| F-014 | Portfolio Free-Capital and Grant | Portfolio Rules | SYSTEM_FORMULA | CAPITAL_ALLOCATION | APPROVED_POLICY |
| F-015 | Actual Committed Capital | Portfolio Rules | SYSTEM_FORMULA | CAPITAL_ALLOCATION | APPROVED_POLICY |
| F-016 | Attempt Cooldown Contribution | Portfolio Rules | SYSTEM_FORMULA | PORTFOLIO_LIMITS | APPROVED_POLICY |
| A-001 | Gross PnL | Accounting | ACCOUNTING_FORMULA | PNL | APPROVED_POLICY |
| A-002 | Net Final Result | Accounting / Order Lifecycle | ACCOUNTING_FORMULA | PNL | CERTIFIED |
| A-003 | Fee Cashflow Attribution | Accounting | ACCOUNTING_FORMULA | FEES_COSTS | APPROVED_POLICY |
| A-004 | Funding Allocation | Accounting | ACCOUNTING_FORMULA | FUNDING | CERTIFIED |
| A-005 | Fill Quantity / Remaining Quantity / VWAP | Order Lifecycle | ACCOUNTING_FORMULA | EXECUTION | APPROVED_POLICY |
| A-006 | Execution-Linked Cashflow Allocation | Accounting | ACCOUNTING_FORMULA | PNL | APPROVED_POLICY |
| A-007 | Equity / Unrealized PnL / Live Drawdown Snapshot | Accounting | ACCOUNTING_FORMULA | EQUITY | APPROVED_POLICY |
| A-008 | Pre-Close Partial-Entry Capital Apportionment | Accounting | ACCOUNTING_FORMULA | CAPITAL_ALLOCATION | APPROVED_POLICY |
| A-009 | Accounting-Day Realized Totals and Daily Loss Gate Input | Accounting | ACCOUNTING_FORMULA | DRAWDOWN | CERTIFIED |
| M-001 | Research Net P/L | Research | RESEARCH_METRIC | RESEARCH_PERFORMANCE | RESEARCH_ONLY |
| M-002 | Research Win Rate | Research | RESEARCH_METRIC | RESEARCH_PERFORMANCE | RESEARCH_ONLY |
| M-003 | Research Profit Factor | Research | RESEARCH_METRIC | RESEARCH_PERFORMANCE | RESEARCH_ONLY |
| M-004 | Research Max Drawdown | Research | RESEARCH_METRIC | DRAWDOWN | RESEARCH_ONLY |
| M-005 | Research Expectancy and Average Outcomes | Research | RESEARCH_METRIC | RESEARCH_PERFORMANCE | RESEARCH_ONLY |
| M-006 | Research Fee Drag / Concentration / Quality Warnings | Research | RESEARCH_METRIC | RESEARCH_PERFORMANCE | RESEARCH_ONLY |
| M-007 | Backtest Spread / Slippage / Cost Assumptions | Research | RESEARCH_METRIC | BACKTEST | RESEARCH_ONLY |
| M-008 | Research Grouping / Direction Mix / Regime Aggregation | Research | AGGREGATION_RULE | RESEARCH_PERFORMANCE | RESEARCH_ONLY |
| N-001 | Exact Decimal Arithmetic | Cross-System | NUMERIC_POLICY | MARKET_NORMALIZATION | APPROVED_POLICY |
| N-002 | Quantization Classes | Cross-System | NUMERIC_POLICY | MARKET_NORMALIZATION | APPROVED_POLICY |
| N-003 | Canonical JSON and Digest Encoding | Cross-System | NUMERIC_POLICY | OTHER:CANONICAL_IDENTITY | APPROVED_POLICY |
| N-004 | Price and Quantity Tick/Step Normalization | API / Execution | NORMALIZATION_RULE | EXECUTION | APPROVED_POLICY |
| N-005 | Native Exchange Fact Sign and Source Normalization | API | NORMALIZATION_RULE | MARKET_NORMALIZATION | APPROVED_POLICY |
| N-006 | Governed Accounting Currency | Accounting | NORMALIZATION_RULE | PNL | APPROVED_POLICY |
| N-007 | UTC Windows and Asia/Jerusalem Accounting Day | Cross-System | NORMALIZATION_RULE | MARKET_NORMALIZATION | APPROVED_POLICY |
| N-008 | Canonical Set Numeric Output Precision | Set | NORMALIZATION_RULE | SET_ANALYTICS | APPROVED_POLICY |
| S-001 | Portfolio Capacity and Eligibility State | Portfolio Rules | STATE_CLASSIFICATION_RULE | PORTFOLIO_LIMITS | APPROVED_POLICY |
| S-002 | Set Outcome and Unavailable State | Set | STATE_CLASSIFICATION_RULE | SET_ANALYTICS | APPROVED_POLICY |
| S-003 | Position Validation Outcome and Rejection Reason | Position Rules | STATE_CLASSIFICATION_RULE | EXECUTION | APPROVED_POLICY |
| S-004 | Order Lifecycle Closed-State Predicate | Order Lifecycle | STATE_CLASSIFICATION_RULE | EXECUTION | CERTIFIED |
| S-005 | Market Regime Diagnostic Classifier | Research | STATE_CLASSIFICATION_RULE | RESEARCH_PERFORMANCE | RESEARCH_ONLY |
| S-006 | Research / Demo / Live Runtime Path Classification | Cross-System | NOT_A_FORMULA | OTHER:RUNTIME_BOUNDARY | ARCHITECTURE_RULE |

# F - Formula / System Formula Library

### F-001 - 1m Price-Move Trigger

#### Classification

| Field | Value |
|---|---|
| ID | F-001 |
| Owner | Set |
| Type | TRADING_FORMULA |
| Family | TRIGGER |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-001_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-001 is the certified one-minute price-move trigger calculation. It compares the close of the current completed 1m candle with the close of the immediately preceding completed 1m candle.

#### What it means

The output says whether the latest completed 1m candle moved far enough, in percent terms, to satisfy the configured price-move trigger. The move is signed for diagnostics, but the predicate uses absolute movement.

#### Why it exists

It supplies Set formation evidence. It can help identify a sudden directional displacement, but it does not by itself choose direction, approve a Set, or authorize a trade.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `observed_price` | Current completed 1m candle close | Exchange KLINES via Set Market Data | Price decimal |
| `reference_price` | Immediately preceding completed 1m candle close | Exchange KLINES via Set Market Data | Price decimal |
| `theta_move_pct` | Configured movement threshold | Versioned Set configuration | Percent where `1` means one percent |
| Source identity and completion evidence | Proof candles are completed, ordered, and same series | Market Data API / Set | Provenance records |

#### Data source

The factual prices come from exchange completed 1m KLINES selected by Set. The trigger value is a derived Set value.

#### Formula or rule

```text
move_pct_work = Q36(100 * (observed_price - reference_price) / reference_price)
trigger_true = abs(move_pct_work) >= theta_move_pct
```

The comparison is exact and inclusive.

#### Calculation / evaluation steps

1. Select the current and immediately preceding completed 1m candles from the same authoritative series.
2. Reject missing, incomplete, unordered, conflicting, nonpositive-denominator, or mismatched source evidence.
3. Parse prices exactly; do not use binary floating point.
4. Compute signed percent movement in the formula order.
5. Round the named working output to the Set working grid where required by `TT_SET_NUMERIC_V1`.
6. Compare absolute movement to the configured threshold exactly and inclusively.

#### Output

Signed price-move diagnostic and `TRUE` / `FALSE` / `UNAVAILABLE` trigger predicate.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when either candle is missing, not completed, not adjacent as required, has invalid source identity, has malformed decimal data, or when `reference_price` is zero or invalid. Do not convert unavailable to zero or infer a candle from current price.

#### Dependencies

- Policy dependency: N-001 exact arithmetic.
- Policy dependency: N-008 Set numeric precision.
- Factual data dependency: completed 1m KLINES.
- Configuration dependency: configured movement threshold.

#### Used by

- Set formation.
- F-004 as compatible formation evidence and signed 1m movement diagnostic.
- F-005 indirectly through Set formation and scoring context.

#### Important boundaries

F-001 does not determine LONG/SHORT. It does not create a Market Handoff by itself. It does not use volume, ATR, Stop, Entry, or Take Profit. It does not place, cancel, or reconcile orders.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-001_FINAL_FORMULA_SPECIFICATION.md` sections 5-17. Supporting: `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`; `docs/FORMULA_METRICS_CATALOG.md` inventory row F-001.

### F-002 - 1m Relative Participation Volume Confirmation

#### Classification

| Field | Value |
|---|---|
| ID | F-002 |
| Owner | Set |
| Type | TRADING_FORMULA |
| Family | TRIGGER |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-002_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-002 is the certified 1m futures-volume confirmation trigger. It compares the current completed 1m base-coin volume to the immediately preceding 60 completed 1m volumes.

#### What it means

The output says whether the current 1m candle shows unusually high participation relative to the last 60 completed 1m candles. It requires both high relative volume and high empirical rank. This is not the old UI placeholder "5m Relative Turnover" concept.

#### Why it exists

It confirms that a Set formation signal is supported by current participation rather than price movement alone.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `c` | Current completed 1m candle volume | Exchange KLINES via Set Market Data | Base-coin volume |
| `v(1)..v(60)` | Immediately preceding 60 completed 1m volumes | Exchange KLINES via Set Market Data | Base-coin volume |
| Market/profile | Bybit USDT linear perpetual futures | Market Data API | Venue/product identity |

#### Data source

The factual volumes come from exchange completed 1m KLINES. Relative volume, median, rank, and trigger predicate are derived Set values.

#### Formula or rule

```text
v_sorted(1) <= ... <= v_sorted(60)
M = (v_sorted(30) + v_sorted(31)) / 2
K = count(v(i) <= c)
R = c / M
P = 100 * K / 60
trigger_true = (R >= 2) AND (P >= 90)
```

After `M > 0` is established, the equivalent boundary is:

```text
c >= v_sorted(30) + v_sorted(31)
AND K >= 54
```

#### Calculation / evaluation steps

1. Select the current completed 1m candle and the immediately preceding 60 completed 1m candles.
2. Validate source identity, completion, order, and continuity.
3. Sort the 60 historical volumes ascending.
4. Compute median `M`.
5. Reject zero or invalid median before computing `R`.
6. Count prior values `<= c` to get `K`.
7. Compute `R` and `P` exactly.
8. Return true only when both thresholds pass.

#### Output

Relative volume `R`, empirical rank percent `P`, and `TRUE` / `FALSE` / `UNAVAILABLE`.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when the current volume, any required historical volume, ordering, continuity, or source provenance is missing or invalid. If the median denominator is zero, the relative-volume quotient is unavailable; do not substitute infinity, zero, or a previous median.

#### Dependencies

- Policy dependency: N-001 exact arithmetic.
- Policy dependency: N-008 Set numeric precision.
- Factual data dependency: completed 1m KLINES volume.

#### Used by

- Set formation.
- F-004 as compatible direction-neutral formation evidence.
- F-005 indirectly through Set matching.

#### Important boundaries

F-002 is a 1m relative participation and volume confirmation trigger. It is not 5m relative turnover, not a direction classifier, not a liquidity guarantee, and not an execution authorization.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-002_FINAL_FORMULA_SPECIFICATION.md` sections 5-17. Supporting: `docs/FORMULA_METRICS_CATALOG.md` row F-002. Non-authority explicitly avoided: `src/triggertrade/dashboard/product_ui.py`.

### F-003 - ATR / True Range / ATR_PCT

#### Classification

| Field | Value |
|---|---|
| ID | F-003 |
| Owner | Set |
| Type | TRADING_FORMULA |
| Family | SET_ANALYTICS |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-003_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-003 defines Set-owned True Range, Wilder ATR(14), and ATR_PCT for completed 15m candles.

#### What it means

ATR measures the recent size of price movement in price units. ATR_PCT expresses the same movement scale relative to the current completed candle close, making volatility comparable across instruments with different price levels. The handoff values are canonical rounded exports; Position consumes them exactly and does not recompute ATR.

#### Why it exists

It provides volatility context for Set analytics and downstream Position formulas that need a certified ATR value.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| 15m completed candles | High, low, close and predecessor close | Exchange KLINES via Set Market Data | Price decimals |
| Seed ancestry | First complete native history with factual predecessor close | Set source manifest | Ordered candle IDs and TR values |
| Prior ATR work state | Previous recursive ATR value | Set checkpoint | Q36 work value |
| Close for ATR_PCT | Current eligible completed 15m close | Exchange KLINES | Price decimal |

#### Data source

Raw facts are completed 15m exchange candles with source manifests. TR, ATR, and ATR_PCT are Set-derived values.

#### Formula or rule

```text
TR = max(high - low, abs(high - previous_close), abs(low - previous_close))
seed_ATR = Q36(mean(first 14 consecutive TR values))
ATR_t = Q36((13 * ATR_(t-1) + TR_t) / 14)
ATR_PCT_t = Q36(100 * ATR_work_t / close_t) when close_t > 0
```

Market Handoff exports round eligible positive ATR and ATR_PCT once to Q18.

#### Calculation / evaluation steps

1. Validate completed 15m source candles, order, continuity, and exact decimal values.
2. Require each current candle to satisfy `0 <= Low <= Close <= High`.
3. Use factual predecessor close; it may lie outside the current range.
4. Establish canonical seed ancestry from 14 consecutive eligible TRs.
5. Round the seed mean once to Q36 with HALF_EVEN.
6. For each later completed candle, compute TR exactly and apply Wilder recurrence, rounded once to Q36.
7. Persist update and processed source identity together.
8. Compute ATR_PCT only when the corresponding close is strictly positive.
9. Export only positive available Q18 ATR and ATR_PCT values.

#### Output

True Range diagnostics, Q36 ATR work state, Q18 `volatility.atr_15m`, and Q18 `volatility.atr_pct_15m`, or `UNAVAILABLE`.

#### Worked example

Authoritative policy gives this technical boundary example: fourteen seed TR values of `1`, followed by `TR=2`, produce work ATR `1.071428571428571428571428571428571429`; the handoff ATR is `1.071428571428571429`. This is a representation example, not a trading threshold.

#### Unavailable / invalid behavior

Unavailable for fewer than 14 seed TRs, missing intervals, incomplete pages, ambiguous order, invalid geometry, invalid checkpoint, zero close for ATR_PCT, positive work values that export to zero, or source conflicts. Do not skip malformed candles, hold prior ATR constant, reseed from an arbitrary fetch window, clamp values, or substitute zero.

#### Dependencies

- Policy dependency: N-001 exact arithmetic.
- Policy dependency: N-008 Set output precision and Set numeric policy.
- Factual data dependency: completed 15m KLINES and source manifests.

#### Used by

- F-004.
- F-005 indirectly.
- F-006, F-007, F-008, F-010, F-012 through the frozen Market Handoff.
- Set analytics and Market Handoff volatility context.

#### Important boundaries

Position must not recompute, reseed, or recover hidden ATR precision. F-003 does not determine direction, Entry, Stop, Take Profit, position size, or profitability.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-003_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` sections 1-5; `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md`.

### F-004 - Set Normalization / Percentile / Direction Score

#### Classification

| Field | Value |
|---|---|
| ID | F-004 |
| Owner | Set |
| Type | TRADING_FORMULA |
| Family | MARKET_NORMALIZATION |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-004_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-004 is the certified Set normalization and scoring object. It combines required Set context inputs such as structure, directional efficiency, VNM, relative return, aggressive delta, time-of-day relative turnover, ATR_PCT percentile, and BTC context.

#### What it means

The output is the normalized Set context used by the direction classifier. It translates heterogeneous market observations into canonical working values, gates, percentiles, and a direction score without fabricating missing inputs.

#### Why it exists

It provides the normalized analytical foundation for Set direction classification and Set matching.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Asset structure 1h / 15m | Structural market context | Set market analysis | Classified context |
| DE 15m | Directional efficiency | Set analytics | Q36 diagnostic |
| VNM 15m / 5m | Volume-normalized movement context | Set analytics | Q36 diagnostic |
| Relative return 15m | Asset relative return context | Set analytics | Q36 diagnostic |
| Aggressive delta 5m | Flow context | Set analytics | Q36 diagnostic |
| Time-of-day relative turnover 5m | Activity context | Set analytics | Q36 diagnostic |
| ATR_PCT 15m percentile | Volatility percentile | F-003 / Set analytics | Percentile |
| BTC structure and return z-score | Market context | Set analytics | Classification / Q36 |

#### Data source

Raw facts come from Set-owned market-data selections. Derived values come from Set analytics under `TT_SET_NUMERIC_V1`.

#### Formula or rule

F-004 applies the certified Set methodology for required normalized values, percentile ranks, gates, and canonical `DIRECTION_SCORE`. Required inputs must be available; context-only metrics may be unavailable without making F-004 unavailable.

#### Calculation / evaluation steps

1. Validate all required inputs at the governed Set analytical cutoff.
2. Apply exact Set arithmetic and required Q36 working-grid rounding.
3. Use exact counts and ranks for percentile/rank operations.
4. Use F-003 only for certified 15m ATR and ATR_PCT semantics.
5. Compute gates and direction score from the certified Set methodology.
6. Preserve missing, malformed, stale, or contradictory required input as unavailable.

#### Output

Canonical normalized Set diagnostics, gate diagnostics, percentile diagnostics, and `DIRECTION_SCORE`.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when any required input or required derived diagnostic is missing, malformed, contradictory, stale, source-incompatible, or unavailable. Do not fabricate, carry forward, replace with zero, infer from downstream state, or substitute F-001/F-002 for distinct 15m/5m context operands.

#### Dependencies

- Formula dependency: F-001, as compatible formation evidence and signed 1m movement diagnostic.
- Formula dependency: F-002, as compatible direction-neutral formation evidence.
- Formula dependency: F-003 for 15m ATR and ATR_PCT.
- Policy dependency: N-008.
- Factual data dependency: Set market-data selections.

#### Used by

- F-005 Set direction classifier.
- Set formation diagnostics.

#### Important boundaries

F-004 does not itself select LONG/SHORT or create a trade. It does not replace F-001, F-002, or F-003. It does not infer missing activity, volatility, flow, or BTC-context evidence.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-004_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/methodology/SET.md`; `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`.

### F-005 - Set Direction Classifier

#### Classification

| Field | Value |
|---|---|
| ID | F-005 |
| Owner | Set |
| Type | TRADING_FORMULA |
| Family | LONG_SHORT |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-005_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-005 is the certified Set-owned direction classifier. It converts available normalized Set evidence into `LONG`, `SHORT`, or `NONE`.

#### What it means

The output indicates whether Set sees a directional branch eligible for downstream Position Rules. A result of `NONE` means no directional branch is satisfied; it does not mean the opposite side is valid.

#### Why it exists

It is the only certified source of Set direction for the Market Handoff. Position Rules consume direction as frozen input and do not reclassify it.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Required F-004 normalized inputs | Structure, DE, VNM, relative return, flow, turnover, ATR percentile, BTC context | Set / F-004 | Q36 and classifications |
| `DIRECTION_SCORE` | Canonical score from F-004 | Set / F-004 | Q36 |
| Direction-specific veto diagnostics | BTC, relative, and local momentum contradiction vetoes | Set | Boolean diagnostics |
| Set expression and lifecycle evidence | Formation epoch, config, event consumption, freshness, expiry | Set | Durable identities and states |

#### Data source

The factual inputs come from Set market data. The classifier consumes Set-derived normalized diagnostics.

#### Formula or rule

Hard gates:

```text
DE_15m < 0.30 -> reject
TOD_REL_TURNOVER < 0.70 -> reject
ATR_PCT_15m_PERCENTILE < 15 -> reject
ATR_PCT_15m_PERCENTILE > 97 -> reject
```

Classifier:

```text
DIRECTION_SCORE >= +0.35 -> LONG candidate, unless LONG-side veto active
DIRECTION_SCORE <= -0.35 -> SHORT candidate, unless SHORT-side veto active
otherwise -> NONE
```

The dead zone is `(-0.35, +0.35)`. Equality passes the threshold on either side.

#### Calculation / evaluation steps

1. Require all eleven required inputs and derived diagnostics.
2. If any required item is unavailable or incompatible, return `NONE`, primary stage `DATA_UNAVAILABLE`, and `matched=false`.
3. Apply hard gates exactly; equality passes.
4. Compare `DIRECTION_SCORE` exactly to the positive and negative thresholds.
5. Apply only the candidate side's active vetoes.
6. Return `LONG`, `SHORT`, or `NONE`.
7. Separately require the governing versioned Set expression to be authoritatively true before a matched Set exists.

#### Output

`LONG`, `SHORT`, or `NONE`, with rejection stage/diagnostics and match eligibility context.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Missing required data returns `NONE` with `DATA_UNAVAILABLE`; it is not a neutral score contribution. `FALSE` or `UNAVAILABLE` Set evidence cannot become a match. Missing local 5m veto evidence cannot be treated as false.

#### Dependencies

- Formula dependency: F-004.
- Policy dependency: N-008.
- Factual data dependency: Set evidence and lifecycle state.

#### Used by

- Market Handoff.
- F-006, F-007, F-008, F-010, F-011, F-012 through frozen direction.
- Position Rules initial approval/construction flow.

#### Important boundaries

F-005 is Set-owned. Position must not reinterpret or recompute direction. F-005 does not approve capital, size a position, submit orders, or force an opposite side when vetoes or dead-zone checks fail.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-005_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/methodology/SET.md`; `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md`.

### F-006 - LONG Dynamic Stop Branch

#### Classification

| Field | Value |
|---|---|
| ID | F-006 |
| Owner | Position Rules |
| Type | TRADING_FORMULA |
| Family | LONG_SHORT |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-006_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-006 is the certified LONG dynamic stop branch. It selects and rounds an adverse-side stop reference for a LONG opportunity.

#### What it means

The output is a usable LONG stop price, or a reason no usable dynamic stop exists. It chooses only permitted low-side structural references below Entry.

#### Why it exists

It supports dynamic stop construction for LONG Position Rules opportunities.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `E` | Planned entry reference | F-008 | Positive price decimal |
| `A` | Received ATR 15m | F-003 via Market Handoff | Q18 positive decimal |
| `t` | Tick size | Instrument metadata / Capital and Limits | Positive decimal |
| Reference levels | Candidate low-side levels | Market Handoff | Typed prices and IDs |
| `sl_context` | Set family and thesis-reference policy | Market Handoff / Position config | Enumerated values |

#### Data source

References and direction come from the frozen Market Handoff. Tick facts come from instrument metadata. Entry comes from F-008.

#### Formula or rule

LONG requires direction `LONG` and candidate levels of type `SWING_LOW_15M`, `SWING_LOW_1H`, `PREVIOUS_DAY_LOW`, or `RANGE_LOW`. A candidate is eligible only when `level.price < E - t`.

Family priority selects a reference, then the branch applies certified distance/ATR constraints and directional tick rounding from the final specification.

#### Calculation / evaluation steps

1. Require immutable handoff direction `LONG`.
2. Validate F-008 entry, received ATR, tick size, producer bindings, thesis IDs, and unique canonical level IDs.
3. Apply thesis-reference policy: `REQUIRED` has no fallback; `PREFERRED` can fall back only under certified conditions; `NONE` requires null thesis binding.
4. Filter to permitted low reference types available as of `matched_at`.
5. Require strict adverse-side geometry below `E - t`.
6. Traverse family priority order.
7. Apply certified rounding and post-rounding invariants.
8. Return usable stop or the certified reason.

#### Output

Usable LONG rounded stop price and diagnostics, or `usable=false` with reason.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable or invalid for wrong direction, missing Entry/ATR/tick, invalid handoff identity, invalid thesis binding, duplicate/conflicting level IDs, no eligible low-side reference, rounding failure, or failed post-rounding invariants. Do not synthesize levels or use high-side levels for LONG stops.

#### Dependencies

- Formula dependency: F-003 through received ATR.
- Formula dependency: F-005 through frozen direction.
- Formula dependency: F-008 entry.
- Policy dependency: N-004 tick normalization.
- Factual data dependency: Market Handoff reference geometry and instrument metadata.

#### Used by

- F-009 in dynamic LONG stop mode.
- F-011 as a construction prerequisite through F-009.
- F-012 geometry checks through final stop.

#### Important boundaries

F-006 applies only to LONG. It does not select Entry, Take Profit, size, or risk/reward. It does not call APIs or refresh market data.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-006_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/methodology/POSITION_RULES.md`.

### F-007 - SHORT Dynamic Stop Branch

#### Classification

| Field | Value |
|---|---|
| ID | F-007 |
| Owner | Position Rules |
| Type | TRADING_FORMULA |
| Family | LONG_SHORT |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-007_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-007 is the certified SHORT dynamic stop branch. It selects and rounds an adverse-side stop reference for a SHORT opportunity.

#### What it means

The output is a usable SHORT stop price, or a reason no usable dynamic stop exists. It chooses only permitted high-side structural references above Entry.

#### Why it exists

It supports dynamic stop construction for SHORT Position Rules opportunities.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `E` | Planned entry reference | F-008 | Positive price decimal |
| `A` | Received ATR 15m | F-003 via Market Handoff | Q18 positive decimal |
| `t` | Tick size | Instrument metadata / Capital and Limits | Positive decimal |
| Reference levels | Candidate high-side levels | Market Handoff | Typed prices and IDs |
| `sl_context` | Set family and thesis-reference policy | Market Handoff / Position config | Enumerated values |

#### Data source

References and direction come from the frozen Market Handoff. Tick facts come from instrument metadata. Entry comes from F-008.

#### Formula or rule

SHORT requires direction `SHORT` and candidate levels of type `SWING_HIGH_15M`, `SWING_HIGH_1H`, `PREVIOUS_DAY_HIGH`, or `RANGE_HIGH`. A candidate is eligible only when `level.price > E + t`.

#### Calculation / evaluation steps

1. Require immutable handoff direction `SHORT`.
2. Validate F-008 entry, received ATR, tick size, producer bindings, thesis IDs, and unique canonical level IDs.
3. Apply thesis-reference policy.
4. Filter to permitted high reference types available as of `matched_at`.
5. Require strict adverse-side geometry above `E + t`.
6. Traverse family priority order.
7. Apply certified rounding and post-rounding invariants.
8. Return usable stop or the certified reason.

#### Output

Usable SHORT rounded stop price and diagnostics, or `usable=false` with reason.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable or invalid for wrong direction, missing Entry/ATR/tick, invalid handoff identity, invalid thesis binding, duplicate/conflicting level IDs, no eligible high-side reference, rounding failure, or failed post-rounding invariants. Do not synthesize levels or use low-side levels for SHORT stops.

#### Dependencies

- Formula dependency: F-003 through received ATR.
- Formula dependency: F-005 through frozen direction.
- Formula dependency: F-008 entry.
- Policy dependency: N-004 tick normalization.
- Factual data dependency: Market Handoff reference geometry and instrument metadata.

#### Used by

- F-009 in dynamic SHORT stop mode.
- F-011 as a construction prerequisite through F-009.
- F-012 geometry checks through final stop.

#### Important boundaries

F-007 applies only to SHORT. It does not select Entry, Take Profit, size, or risk/reward. It does not call APIs or refresh market data.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-007_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/methodology/POSITION_RULES.md`.

### F-008 - Planned Entry Reference Selection

#### Classification

| Field | Value |
|---|---|
| ID | F-008 |
| Owner | Position Rules |
| Type | TRADING_FORMULA |
| Family | ENTRY |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-008_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-008 selects the planned LIMIT entry reference from the frozen Market Handoff reference geometry.

#### What it means

The output is the exact planned entry price Position Rules may use for a post-only LIMIT entry. It is selected from governed reference levels; no market/taker fallback exists.

#### Why it exists

Entry is the price anchor for stop, take-profit, sizing, notional, and planned economics.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Direction | LONG or SHORT | F-005 via Market Handoff | Enum |
| `set_match_reference_price` | Match reference price | Market Handoff | Positive price decimal |
| `ATR_15m` | Volatility scale | F-003 via Market Handoff | Q18 positive decimal |
| `tick_size` | Instrument price grid | Instrument metadata | Positive decimal |
| Reference levels | Entry candidates | Market Handoff | Typed levels |
| Entry context | Set family and thesis-reference policy | Market Handoff / Position config | Enums and IDs |

#### Data source

All market references come from the frozen Market Handoff. Instrument tick facts come from approved instrument metadata. F-008 does not query the exchange.

#### Formula or rule

Candidate raw eligibility:

```text
LONG: r < S
SHORT: r > S
d = abs(S - r)
0.10 <= d / A <= 1.25
```

Equivalent exact comparisons:

```text
10 * d >= A
4 * d <= 5 * A
```

Successful output is always `LIMIT` and `post_only=true`.

#### Calculation / evaluation steps

1. Validate contract identity, direction, provenance, required structure, match price, ATR, tick, family, and thesis policy.
2. Accept only `LONG` or `SHORT`.
3. Filter levels by directionally permitted structural type.
4. Require positive finite price and availability as of `matched_at`.
5. Apply strict improvement side and raw ATR band.
6. Apply thesis-reference policy and family hierarchy.
7. Select the certified candidate.
8. Apply side-preserving tick rounding.
9. Validate positivity, grid membership, side geometry, and rounded ATR band.

#### Output

`planned_entry_reference`, order policy `LIMIT POST_ONLY`, selected level identity, raw/rounded improvement diagnostics, and usable/unavailable reason.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable or invalid for missing match price, ATR, tick, set family, thesis policy, invalid direction, dangling thesis ID, producer availability violation, duplicate/conflicting level IDs, no eligible reference, or rounding failure. Raw-ineligible candidates cannot be rescued by tick rounding.

#### Dependencies

- Formula dependency: F-003 through received ATR.
- Formula dependency: F-005 through direction.
- Policy dependency: N-004 tick normalization.
- Factual data dependency: Market Handoff reference geometry and instrument metadata.

#### Used by

- F-006.
- F-007.
- F-009.
- F-010.
- F-011.
- F-012.
- Order Spec construction after successful post-grant construction.

#### Important boundaries

F-008 does not use Stop as an operand. It does not create a market order, change direction, synthesize ATR-only prices, or refresh current market state. It preserves LIMIT POST_ONLY.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-008_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/methodology/POSITION_RULES.md` Part II; `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md`.

### F-009 - Stop Calculation and Stop Rounding

#### Classification

| Field | Value |
|---|---|
| ID | F-009 |
| Owner | Position Rules |
| Type | TRADING_FORMULA |
| Family | STOP |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-009_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-009 resolves the final Stop Loss price. It supports fixed percentage mode and dynamic pass-through from the certified LONG or SHORT dynamic stop branch.

#### What it means

The output is the protective stop price used by downstream construction and risk/economics checks. It is actionable only when all mode, dependency, and rounding checks pass.

#### Why it exists

Stop price defines risk geometry for construction and planned economics.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Direction | LONG or SHORT | F-005 via Market Handoff | Enum |
| `E` | Planned entry | F-008 | Positive price decimal |
| `t` | Tick size | Instrument metadata | Positive decimal |
| Stop mode | FIXED or DYNAMIC | Pinned Position config | Enum |
| `fixed_sl_pct` | Fixed stop distance | Pinned Position config | Percent |
| Dynamic branch result | Certified stop branch | F-006 or F-007 | Rounded stop and reason |

#### Data source

Entry and direction come from the frozen handoff/F-008 chain. Tick facts come from instrument metadata. Stop configuration is pinned Position configuration.

#### Formula or rule

Fixed mode:

```text
LONG raw_sl = E * (1 - S / 100)
SHORT raw_sl = E * (1 + S / 100)
LONG SL = floor_t(raw_sl)
SHORT SL = ceil_t(raw_sl)
```

Dynamic mode consumes the matching certified branch:

```text
LONG -> F-006
SHORT -> F-007
```

#### Calculation / evaluation steps

1. Validate Entry and tick as positive exact decimals.
2. Select mode from pinned configuration.
3. In fixed mode, require valid `fixed_sl_pct`; LONG additionally requires `S < 100`.
4. Compute raw fixed stop exactly with no intermediate rounding.
5. Round LONG down and SHORT up to tick.
6. Validate price is finite, positive, on-grid, and adverse to Entry.
7. In dynamic mode, consume only the matching certified branch result with same binding.
8. Preserve dependency reasons when dynamic branch is unavailable.

#### Output

`stop_loss_price` or `usable=false` with reason and diagnostics.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable or invalid for bad mode, missing fixed percentage, invalid Entry/tick, branch mismatch, unavailable dynamic branch, rounding failure, nonpositive stop, or invalid geometry. Do not clamp, offset, retry, substitute, switch modes, or alter Entry.

#### Dependencies

- Formula dependency: F-006 for dynamic LONG.
- Formula dependency: F-007 for dynamic SHORT.
- Formula dependency: F-008.
- Policy dependency: N-004.
- Configuration dependency: pinned stop mode and fixed percentage where applicable.

#### Used by

- F-011 as construction prerequisite.
- F-012 risk/reward and net-edge geometry.
- Order Spec through successful construction.

#### Important boundaries

F-009 does not select Entry or Take Profit. Stop failure cannot be repaired by resizing, changing leverage, changing capital, or issuing a replacement grant.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-009_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/methodology/POSITION_RULES.md` Part III.

### F-010 - Dynamic Take Profit Selection and Rounding

#### Classification

| Field | Value |
|---|---|
| ID | F-010 |
| Owner | Position Rules |
| Type | TRADING_FORMULA |
| Family | DYNAMIC_TAKE |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-010_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-010 selects and rounds the dynamic Take Profit target from frozen Market Handoff reference geometry.

#### What it means

The output is the primary favorable-side target price. It is selected by direction, family hierarchy, reachability, exact ATR distance, and tick rounding.

#### Why it exists

Take Profit defines the reward side of planned trade geometry and downstream economics.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Direction | LONG or SHORT | F-005 via Market Handoff | Enum |
| `E` | Planned entry | F-008 | Positive price decimal |
| `A` | Received ATR 15m | F-003 via Market Handoff | Q18 positive decimal |
| `t` | Tick size | Instrument metadata | Positive decimal |
| Reference levels | Favorable-side target candidates | Market Handoff | Typed prices and IDs |
| TP context/config | Set family, thesis policy, dynamic mode | Market Handoff / Position config | Enums and IDs |

#### Data source

Reference levels and family come from frozen Market Handoff. Tick and metadata come from instrument facts. Configuration is pinned Position configuration.

#### Formula or rule

Basic favorable-side geometry:

```text
LONG: r > E + t
SHORT: r < E - t
```

Reachability:

```text
TOO_CLOSE: 4 * distance_price < 3 * A
ELIGIBLE:  4 * distance_price >= 3 * A and distance_price <= 4 * A
TOO_FAR:   distance_price > 4 * A
```

Rounding:

```text
LONG TP = floor(R / t) * t
SHORT TP = ceil(R / t) * t
```

#### Calculation / evaluation steps

1. Require same-bound available F-008 result and dynamic TP configuration.
2. Validate handoff, F-008 binding, primitives, configuration, metadata, thesis IDs, and unique level IDs.
3. Build the directional pool from permitted favorable-side level types.
4. Build the basic pool using strict favorable-side geometry.
5. Traverse the active family hierarchy in certified order.
6. Skip too-close candidates; terminate on too-far where the spec requires.
7. Select the first eligible target.
8. Round inward to tick.
9. Validate on-grid, positive, favorable-side, and post-rounding reachability.
10. Preserve diagnostics without letting optional diagnostic traversal change the selected target.

#### Output

Usable rounded Take Profit price, selected target identity, traversal diagnostics, or `usable=false` with reason.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable or invalid for missing dynamic config, invalid handoff/F-008 binding, missing Entry/ATR/tick/family/policy, unusable reference geometry, invalid thesis reference, no eligible target, target too far, no reachable target, target too close after rounding, or rounding error. Do not synthesize an ATR target or select an alternate after terminal rounding failure.

#### Dependencies

- Formula dependency: F-003.
- Formula dependency: F-005.
- Formula dependency: F-008.
- Policy dependency: N-004.
- Configuration dependency: pinned dynamic TP mode.

#### Used by

- F-011 as construction prerequisite.
- F-012 as reward geometry.
- Order Spec through successful construction.

#### Important boundaries

F-010 produces one primary TP. It does not use Stop distance as a target selector, does not introduce partial TP or multi-target behavior, and does not alter Entry.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-010_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/methodology/POSITION_RULES.md` Part IV.

### F-011 - Position Quantity and Actual Notional Construction

#### Classification

| Field | Value |
|---|---|
| ID | F-011 |
| Owner | Position Rules |
| Type | TRADING_FORMULA |
| Family | POSITION_SIZING |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-011_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-011 constructs final quantity, actual order notional, and actual committed capital from the approved grant, leverage, Entry, and instrument limits.

#### What it means

The output tells exactly how much quantity may be submitted and how much own capital must be held. The construction is conservative: quantity floors to venue step and committed own-capital liability ceilings to `Qcapital`.

#### Why it exists

It prevents overcommitment and creates the final executable construction basis for Order Spec and Portfolio authorization.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `C` | Requested capital per tranche | Portfolio Capital and Limits | Qcapital-aligned own capital |
| `L` | Configured leverage | Pinned Position config / venue facts | Exact positive decimal |
| `E` | Final Entry | F-008 | Positive price decimal |
| `q` | Quantity step | Instrument metadata | Positive decimal |
| Min/max order facts | Venue quantity/notional constraints | Capital and Limits / API facts | Exact decimals / status |
| Stop and TP | Construction prerequisites | F-009 / F-010 | Usable prices |

#### Data source

Capital comes from Portfolio. Entry/Stop/TP come from Position formulas. Venue constraints come from instrument metadata carried through approved factual boundaries.

#### Formula or rule

```text
T = C * L
R = T / E
Q = q * floor(R / q)
N = Q * E
A = N / L
H = Qcapital * ceil(A / Qcapital)
```

Required checks include `Q > 0`, grid alignment, minimum quantity, maximum quantity when available, minimum notional, `A <= C`, and `H <= C`.

#### Calculation / evaluation steps

1. Require initial Position approval, matching Portfolio grant, pinned config, usable Entry, Stop, and TP, and same-bound identities.
2. Validate capital, leverage, Entry, quantity step, min/max facts, and provenance.
3. Reject unaligned grants rather than rounding them.
4. Compute target notional, raw quantity, floored final quantity, actual notional, exact committed capital, and persisted committed capital.
5. Apply all quantity, notional, leverage, maximum, and capital-bound checks.
6. Preserve ordered failure reasons and all determinable secondary failures.

#### Output

Final quantity, actual order notional, exact committed capital, persisted committed capital, and construction pass/fail result.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable or invalid for identity mismatch, missing config, invalid grant, unusable Entry/Stop/TP, invalid leverage, invalid venue facts, unavailable max quantity status, zero quantity, below-minimum quantity/notional, above maximum quantity, or capital overcommitment. Do not clamp, split, resize, change leverage, alter prices, or request a replacement grant.

#### Dependencies

- Formula dependency: F-008.
- Formula dependency: F-009.
- Formula dependency: F-010.
- Policy dependency: F-014 grant mechanics.
- Policy dependency: F-015 committed capital semantics.
- Policy dependency: N-001, N-002, N-004.
- Factual data dependency: venue instrument metadata.

#### Used by

- F-012.
- Position construction result.
- Order Spec.
- Portfolio hold/authorization.

#### Important boundaries

F-011 consumes Stop and TP only as prerequisites, not as sizing operands. It does not increase granted own capital, refresh API facts directly, or authorize submission.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-011_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 4; `docs/trading-methodology/methodology/POSITION_RULES.md` Appendix D.

### F-012 - Risk/Reward and Minimum Net Edge

#### Classification

| Field | Value |
|---|---|
| ID | F-012 |
| Owner | Position Rules |
| Type | TRADING_FORMULA |
| Family | RISK_REWARD |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-012_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-012 calculates final risk/reward geometry and planned minimum net edge from certified Entry, Stop, Take Profit, quantity, notional, and fee rates.

#### What it means

The output says whether the constructed opportunity passes the configured gross R:R and planned net-edge gates. The calculation is about planned eligibility, not proof of eventual profitability.

#### Why it exists

It is the final planned economics gate before a successful constructed spec can be considered eligible.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `E` | Certified Entry | F-008 | Positive price decimal |
| `SL` | Certified Stop | F-009 | Positive price decimal |
| `TP` | Certified Take Profit | F-010 | Positive price decimal |
| `Q` | Final quantity | F-011 | Quantity decimal |
| `N` | Actual order notional | F-011 | Monetary decimal |
| Fee rates | Maker entry and taker TP rates | Portfolio/API fee facts | Fractional rates |
| Gate flags/thresholds | Minimum R:R and net-edge configuration | Pinned Position config | Boolean and decimals |

#### Data source

Prices and quantity come from certified Position formulas. Fee rates come from governed factual fee schedule evidence. Thresholds are configuration, not Metrics Library entries.

#### Formula or rule

```text
s = 1 for LONG, -1 for SHORT
dr = s * (E - SL)
dw = s * (TP - E)
risk_distance_pct = 100 * dr / E
reward_distance_pct = 100 * dw / E
gross_rr = dw / dr
gross_profit_tp = dw * Q
gross_loss_sl = dr * Q
entry_fee = N * maker_fee_rate
tp_exit_fee = TP * Q * taker_fee_rate
net_profit_tp = gross_profit_tp - entry_fee - tp_exit_fee
net_edge_pct = 100 * net_profit_tp / N
```

Enabled gates compare exact calculated values to exact configured thresholds.

#### Calculation / evaluation steps

1. Require usable certified Entry, Stop, TP, and successful F-011 sizing with matching bindings.
2. Validate all prices, quantity, notional, fee rates, and flags.
3. Compute directional risk and reward distances.
4. Require both distances to be strictly positive.
5. Compute gross R:R, planned TP profit/loss, fee costs, and net-edge percent exactly.
6. For each enabled gate, compare exact value to configured threshold.
7. Mark disabled gates `NOT_APPLICABLE`.
8. Preserve unavailable dependency reasons.

#### Output

Risk distance, reward distance, gross R:R, planned fee economics, net-edge percent, and gate states `PASS` / `FAIL` / `UNAVAILABLE` / `NOT_APPLICABLE`.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable for blocked prerequisites, nonpositive or malformed values, invalid geometry, missing fee facts, unsupported additional deterministic costs, missing enabled thresholds, or unknown flags. Zero or negative net edge is valid signed data; the gate comparison determines pass/fail.

#### Dependencies

- Formula dependency: F-008.
- Formula dependency: F-009.
- Formula dependency: F-010.
- Formula dependency: F-011.
- Approved policy dependency: A-003 for planned fee factual basis.
- Policy dependency: N-001 and N-002.
- Configuration dependency: enabled flags and configured thresholds.

#### Used by

- Position construction result.
- Order Spec eligibility.
- Research diagnostics.

#### Important boundaries

F-012 excludes funding from planned net edge. It does not change Entry, Stop, TP, quantity, leverage, capital, or configuration after a failed gate. It is not realized PnL.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-012_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/methodology/POSITION_RULES.md` Part V and Appendix D.

### F-013 - Pending Entry Market Invalidation

#### Classification

| Field | Value |
|---|---|
| ID | F-013 |
| Owner | Set |
| Type | SYSTEM_FORMULA |
| Family | SET_ANALYTICS |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-013_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

F-013 is the Set-owned pending-entry market invalidation rule. It evaluates frozen hard market conditions after an accepted/placed pending LIMIT entry.

#### What it means

The output says whether the still-pending entry remains valid, is invalidated by a frozen condition, is stopped because no pending remainder remains, or is unavailable and must fail closed.

#### Why it exists

It protects pending orders from silently remaining active when the Set-owned market condition that justified them has become invalid or cannot be evaluated.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Frozen condition record | Hard invalidation predicates | Set | Versioned durable record |
| Order Placed sync | Proof of accepted/placed order binding | Order Lifecycle -> Set | IDs and timestamps |
| Current factual measurements | Measurements selected by frozen predicates | Market Data API / Set | Typed factual values |
| Entry remainder evidence | Whether active unfilled remainder remains | Order Lifecycle | State proof |

#### Data source

Frozen conditions are Set-derived at match time. Current measurements come from Set-selected market facts. Pending remainder proof comes from Order Lifecycle synchronization.

#### Formula or rule

Per hard condition:

```text
TRUE
FALSE
UNAVAILABLE
INVALID_CONDITION
```

Outcome precedence:

```text
1. Terminal/no active unfilled remainder -> STOPPED
2. Invalid activation or frozen record -> UNAVAILABLE fail closed
3. Any hard condition TRUE -> INVALID and emit cancel signal
4. Any required condition UNAVAILABLE/INVALID_CONDITION -> UNAVAILABLE fail closed
5. All valid required conditions FALSE -> VALID
```

#### Calculation / evaluation steps

1. Persist a frozen condition record for each matched cycle capable of a pending LIMIT entry.
2. Activate monitoring only when Order Placed IDs match the frozen decision cycle, Set result, and linked tranche.
3. Validate frozen record and hard conditions.
4. Evaluate each hard condition using only frozen predicates and selected current facts.
5. Apply outcome precedence.
6. Emit idempotent cancel signal only for `INVALID`.
7. For `UNAVAILABLE`, record fail-closed monitoring-unavailable state and request reconcile-then-cancel-if-still-pending handling.

#### Output

`VALID`, `INVALID`, `UNAVAILABLE`, or `STOPPED`, plus optional idempotent `Order Cancel Signal`.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when activation identity is ambiguous, frozen condition record is missing/malformed/unsupported, required facts are unavailable, conditions are invalid, or source evidence is incompatible. Do not activate by symbol, nearest order, latest Set result, timestamp, or current configuration.

#### Dependencies

- Policy dependency: N-008 for Set numeric comparisons.
- Architecture dependency: Order Placed synchronization.
- Factual data dependency: current market facts selected by frozen predicates.
- Documentation dependency: Order Cancel Signal contract.

#### Used by

- Order Cancel Signal.
- Order Lifecycle pending-entry cancellation handling.
- Set monitor state.

#### Important boundaries

F-013 does not change the original Entry, Stop, TP, Set direction, or configuration. It does not cancel by itself; it emits a Set-owned signal that Lifecycle reconciles before execution.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/F-013_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/methodology/SET.md`; `docs/trading-methodology/business-contracts/ORDER_CANCEL_SIGNAL.md`.

### F-014 - Portfolio Free-Capital and Grant

#### Classification

| Field | Value |
|---|---|
| ID | F-014 |
| Owner | Portfolio Rules |
| Type | SYSTEM_FORMULA |
| Family | CAPITAL_ALLOCATION |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 3 |

#### What it is

F-014 is the approved Portfolio free-capital and grant calculation. It computes spendable capacity and requested grant per tranche using exact arithmetic and final `Qcapital` flooring.

#### What it means

The output is how much own capital Portfolio may offer to a candidate tranche. It is conservative: floors never create extra spendable capital.

#### Why it exists

It lets Portfolio issue grants while preserving capital capacity and slot boundaries.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Exact free capital | Current available own capital after commitments | Portfolio state | Monetary rational/decimal |
| Remaining slots `S` | Available tranche slots | Portfolio state/config | Positive integer |
| Capacity limits | Global and per-coin limits | Portfolio Rules config/state | Exact monetary values |

#### Data source

Inputs come from Portfolio accounting state, commitments, holds, limits, and slots. They are derived system values, not raw exchange signals.

#### Formula or rule

```text
Cfree = floor_Qcapital(exact_free_capital)
requested_grant = floor_Qcapital(Cfree / S)
```

Zero slots, nonpositive resulting grant, missing inputs, or negative capacity do not create a trade.

#### Calculation / evaluation steps

1. Compute existing free-capital and limit expressions exactly.
2. Floor spendable capacity to `Qcapital`.
3. If remaining slots are positive, divide by slot count exactly.
4. Floor the grant to `Qcapital`.
5. Leave division residue in free capital.
6. Recheck current capacity atomically at hold authorization later.

#### Output

Quantum-aligned requested grant amount, or unavailable/rejected capacity state.

#### Worked example

Policy example: `751.10 / 3` yields grant `250.366666666666`, leaving `0.000000000002` unallocated if three such commitments are made. This is a numeric policy example, not a trading recommendation.

#### Unavailable / invalid behavior

Unavailable or invalid for missing Portfolio state, stale/reconciling capacity, zero slots, negative capacity, nonpositive floored grant, invalid configuration, or unresolved holds. Do not round upward or distribute residue to an arbitrary grant.

#### Dependencies

- Policy dependency: N-001.
- Policy dependency: N-002 `Qcapital`.
- State dependency: S-001 capacity state.
- Factual data dependency: Portfolio accounting state.

#### Used by

- Portfolio grant issuance.
- F-011 through Capital and Limits.
- S-001.

#### Important boundaries

A grant is not a reservation. Concurrent grants do not change available capital. F-014 does not authorize submission and does not bypass later current-capacity hold checks.

#### Technical traceability

Primary: `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 3. Supporting: `docs/trading-methodology/methodology/PORTFOLIO_RULES.md`; `docs/FORMULA_METRICS_CATALOG.md` row F-014.

### F-015 - Actual Committed Capital

#### Classification

| Field | Value |
|---|---|
| ID | F-015 |
| Owner | Portfolio Rules |
| Type | SYSTEM_FORMULA |
| Family | CAPITAL_ALLOCATION |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 4 |

#### What it is

F-015 is the approved actual committed capital calculation from final quantity, entry price, and leverage.

#### What it means

It gives the own-capital liability Portfolio must hold for the constructed order. The persisted liability is conservatively rounded up to `Qcapital`.

#### Why it exists

It prevents Portfolio from under-holding capital after Position floors quantity to the venue step.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Final quantity | Quantity after F-011 flooring | F-011 | Quantity decimal |
| Entry | Immutable planned entry | F-008 / F-011 | Price decimal |
| Leverage | Configured leverage | Pinned Position config | Positive decimal |
| `Qcapital` | Capital quantum | N-002 | `0.000000000001` |

#### Data source

Inputs are constructed Position values and pinned configuration carried to Portfolio.

#### Formula or rule

```text
actual_order_notional = final_quantity * Entry
actual_committed_capital_exact = actual_order_notional / leverage
actual_committed_capital_persisted = ceil_Qcapital(actual_committed_capital_exact)
```

#### Calculation / evaluation steps

1. Consume the final quantity and immutable Entry selected by Position.
2. Compute actual order notional exactly.
3. Divide by leverage exactly.
4. Ceiling the nonnegative liability to `Qcapital`.
5. Require exact and persisted committed capital to remain `<=` granted capital.
6. Copy this persisted liability into submission hold; do not quantize again.

#### Output

Exact actual committed capital and persisted quantum-aligned committed capital.

#### Worked example

Policy example: actual notional `202` at leverage `3` gives exact requirement `202/3`; persisted liability is `67.333333333334`.

#### Unavailable / invalid behavior

Unavailable or invalid when quantity, Entry, leverage, grant, or binding is missing/malformed, when capital exceeds grant, or when construction failed. Do not round liability down, clamp it to grant, or treat unused grant capacity as held.

#### Dependencies

- Formula dependency: F-011.
- Policy dependency: N-001.
- Policy dependency: N-002.

#### Used by

- Portfolio submission hold.
- F-011 integrity checks.
- A-008 apportionment.
- S-001 capacity state.

#### Important boundaries

F-015 does not choose Entry or quantity. It does not create spendable capital and does not release capital during close; close release remains governed by lifecycle finality.

#### Technical traceability

Primary: `docs/trading-methodology/schemas/NUMERIC_POLICY.md` sections 4 and 7. Supporting: `docs/FORMULA_METRICS_CATALOG.md` row F-015.

### F-016 - Attempt Cooldown Contribution

#### Classification

| Field | Value |
|---|---|
| ID | F-016 |
| Owner | Portfolio Rules |
| Type | SYSTEM_FORMULA |
| Family | PORTFOLIO_LIMITS |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` sections 24-26 and appendices |

#### What it is

F-016 defines attempt-scoped cooldown contribution and effective symbol cooldown.

#### What it means

Each accepted attempt can contribute a symbol cooldown ending at its accepted time plus its pinned cooldown duration. The effective symbol cooldown is the maximum surviving contribution.

#### Why it exists

It prevents immediate repeated new exposure for the same symbol while preserving durable attempt lineage.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `entry_accepted_at` | Proven exchange acceptance time | Order Lifecycle / API evidence | Timestamp |
| Pinned cooldown duration | Cooldown duration bound to attempt | Portfolio config pin | Duration |
| Attempt identity | Durable attempt/tranche lineage | Portfolio / Lifecycle | IDs |
| Terminal/release evidence | Whether contribution survives | Lifecycle / Portfolio | State evidence |

#### Data source

Acceptance time is factual execution evidence from Lifecycle/API. Duration is pinned Portfolio configuration. Effective cooldown is Portfolio-derived state.

#### Formula or rule

```text
cooldown_contribution_until = entry_accepted_at + pinned_cooldown_duration
effective_symbol_cooldown_until = max(surviving cooldown_contribution_until values)
```

#### Calculation / evaluation steps

1. Require durable attempt identity and pinned cooldown duration.
2. Require proven `entry_accepted_at`; do not substitute request creation time.
3. Compute the attempt's contribution time.
4. Persist contribution with lineage.
5. Remove only contributions that are no longer surviving under approved state rules.
6. Publish the symbol's effective cooldown as the maximum surviving contribution.

#### Output

Attempt cooldown contribution and effective symbol cooldown timestamp/state.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when accepted time, attempt lineage, pinned duration, or restart state is missing or contradictory. Do not silently fall back to current configuration or local clock timestamps.

#### Dependencies

- State dependency: Order Lifecycle acceptance evidence.
- Configuration dependency: pinned cooldown duration.
- Policy dependency: N-007 for timestamp handling.
- Architecture dependency: durable attempt lineage.

#### Used by

- S-001 Portfolio capacity and eligibility.
- Portfolio Coins OPEN/CLOSE decisions.

#### Important boundaries

F-016 is not a trading signal and does not close positions. The duration value is configuration, not a Metrics Library formula. Cooldown does not authorize Portfolio release.

#### Technical traceability

Primary: `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` sections 24-26 and appendices. Supporting: `docs/FORMULA_METRICS_CATALOG.md` row F-016; `docs/BACKEND_IMPLEMENTATION_MAP_V1_2_15.md` cooldown boundaries.

# A - Accounting Library

### A-001 - Gross PnL

#### Classification

| Field | Value |
|---|---|
| ID | A-001 |
| Owner | Accounting |
| Type | ACCOUNTING_FORMULA |
| Family | PNL |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` financial factual response and lifecycle attribution |

#### What it is

A-001 computes directional gross realized trading result from actual entry and exit executions for a logical tranche.

#### What it means

Gross PnL measures price movement times executed quantity before fees, funding, and other supported exchange costs.

#### Why it exists

It supplies the gross result component consumed by certified net final result accounting.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Entry executions | Actual open-side fills | Order Lifecycle / Order Management facts | Quantity and price |
| Exit executions | Actual close-side fills | Order Lifecycle / Order Management facts | Quantity and price |
| Direction | LONG or SHORT | Lifecycle / Position lineage | Enum |
| Execution lineage | Proof of logical tranche attribution | Lifecycle | Execution IDs |

#### Data source

Raw facts come from Order Management execution records. Gross PnL is a Lifecycle/accounting derived value.

#### Formula or rule

For equivalent matched quantities:

```text
LONG gross = sum(exit_qty * exit_price) - sum(entry_qty * entry_price)
SHORT gross = sum(entry_qty * entry_price) - sum(exit_qty * exit_price)
```

#### Calculation / evaluation steps

1. Collect complete attributed entry and exit executions.
2. Validate quantity attribution, direction, currency/account context, and execution IDs.
3. Compute exact quantity times actual price for each side.
4. Apply directional sign.
5. Preserve exact finite monetary value with no display rounding as accounting input.

#### Output

Exact gross realized trading result.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when execution attribution is incomplete, quantities cannot be reconciled, direction is missing, factual prices/quantities are malformed, or source identity conflicts exist. Do not use native aggregate PnL as a substitute.

#### Dependencies

- Policy dependency: N-001.
- Factual data dependency: A-005 execution aggregation.
- Architecture dependency: Lifecycle execution attribution.

#### Used by

- A-002.
- Lifecycle final financial result.

#### Important boundaries

A-001 excludes fees, rebates, funding, and other costs. It does not determine daily loss by itself and does not release capital.

#### Technical traceability

Primary: `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md`; `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` sections 34 and financial finality. Implementation cross-check: `src/triggertrade/accounting/futures.py::gross_pnl`.

### A-002 - Net Final Result

#### Classification

| Field | Value |
|---|---|
| ID | A-002 |
| Owner | Accounting / Order Lifecycle final result |
| Type | ACCOUNTING_FORMULA |
| Family | PNL |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/A-002_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

A-002 is the certified net realized result calculation for one logical tranche.

#### What it means

It combines gross trading result, attributed fee/rebate cost effects, certified funding allocations, and other supported exchange costs into exactly one immutable final result.

#### Why it exists

It is the authoritative realized accounting result consumed by Portfolio and daily realized aggregation.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `gross_realized_trading_result` | Directional gross result | A-001 | Governed currency |
| `actual_fees_rebates` | Fee/rebate cost-effect total | A-003 | Charges positive, rebates negative |
| `allocated_funding` | Certified funding allocations | A-004 | Signed governed currency |
| `other_supported_exchange_costs` | Other supported cost-effect total | A-006 / financial facts | Costs positive, refunds negative |
| Currency and coverage | Common governed currency and complete coverage | N-006 / Order Management | Currency and certificates |
| Source lineage | Execution and cashflow identities | Lifecycle | IDs and provenance |

#### Data source

Inputs come from complete Lifecycle financial evidence and certified/approved accounting components.

#### Formula or rule

```text
net_realized_result =
  gross_realized_trading_result
  - actual_fees_rebates
  + allocated_funding
  - other_supported_exchange_costs
```

All components must already be admissible in the tranche's pinned governed accounting currency.

#### Calculation / evaluation steps

1. Require complete financial coverage and source finality.
2. Validate common governed currency for every required monetary component.
3. Resolve duplicate aliases before summing.
4. Consume each component after its own output-class quantization.
5. Apply exact arithmetic with no A-002 intermediate rounding.
6. Persist exactly one immutable final result ID per logical tranche.
7. Publish a FINAL Order Event for Portfolio consumption.

#### Output

`net_realized_result`, final financial result payload, immutable `result_id`, and Portfolio FINAL event.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

No FINAL result when mandatory coverage is missing, facts are partial/unavailable, sign convention is unknown, currency is unsupported, aliases are unresolved, planned estimates are present without actual facts, or native aggregate PnL is offered as substitute. Contrary post-FINAL evidence follows integrity/fence rules and does not silently rewrite the final result.

#### Dependencies

- Formula dependency: A-001.
- Approved policy dependency: A-003.
- Formula dependency: A-004.
- Approved policy dependency: A-005.
- Approved policy dependency: A-006.
- Policy dependency: N-001 and N-006.
- Documentation dependency: P6/P7 finality and evidence protocols.

#### Used by

- A-009.
- S-004.
- Portfolio realized accounting and release receipts.
- Research metrics M-001 through M-006 when using finalized accounting facts.

#### Important boundaries

A-002 is not native aggregate PnL, not a provisional estimate, and not a Portfolio-created result. Portfolio posts it once; Position does not supply or alter it.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/A-002_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md`; `docs/trading-methodology/SYSTEM_PROTOCOLS.md` P6/P7.

### A-003 - Fee Cashflow Attribution

#### Classification

| Field | Value |
|---|---|
| ID | A-003 |
| Owner | Accounting |
| Type | ACCOUNTING_FORMULA |
| Family | FEES_COSTS |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` and `ORDER_MANAGEMENT.md` financial facts |

#### What it is

A-003 normalizes and attributes actual trading fee and rebate cashflows to the logical tranche.

#### What it means

The output is the fee/rebate cost-effect total used by final accounting. Fees increase cost; rebates reduce cost.

#### Why it exists

It supplies actual fee economics for final realized accounting and planned fee facts for F-012 where approved.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Fee rows | Native fee/rebate cashflows | Order Management / Portfolio Data facts | Currency, amount, sign convention |
| Execution linkage | Which execution/cashflow belongs to tranche | Lifecycle | IDs |
| Source sign profile | COST_POSITIVE, CREDIT_POSITIVE, etc. | API normalization | Enum/provenance |
| Coverage | Completeness proof | API / Lifecycle | Coverage certificate |

#### Data source

Raw fee facts come from exchange/API financial records. Attribution is Lifecycle/accounting derived.

#### Formula or rule

Normalize actual source fee/rebate rows into a cost-effect total:

```text
fees_rebates_cost_effect = sum(charges as positive costs, rebates as negative costs)
```

#### Calculation / evaluation steps

1. Collect complete fee/rebate rows for the relevant executions.
2. Preserve native source amount, source field, currency, quantum, and identity.
3. Apply the approved source sign convention.
4. Resolve aliases and duplicates.
5. Attribute rows to the logical tranche.
6. Sum exact cost-effect values in the governed currency.

#### Output

Attributed fee/rebate cost-effect total and source lineage.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when coverage is partial/unavailable, sign mapping is unknown, currency is unsupported, aliases are unresolved, or factual linkage is incomplete. Do not use planned fee estimates as actual realized fees.

#### Dependencies

- Policy dependency: N-001.
- Policy dependency: N-005.
- Policy dependency: N-006.
- Factual data dependency: execution and financial facts.

#### Used by

- A-002.
- F-012 planned fee economics where applicable fee facts are provided.
- Research fee-drag metrics.

#### Important boundaries

A-003 does not allocate funding. It does not infer missing actual fees from configured rates for final accounting.

#### Technical traceability

Primary: `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` GET_FINANCIAL_FACTS; `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` cash postings. Implementation cross-check: `src/triggertrade/backtest/simulator.py` is research/demo only.

### A-004 - Funding Allocation

#### Classification

| Field | Value |
|---|---|
| ID | A-004 |
| Owner | Accounting |
| Type | ACCOUNTING_FORMULA |
| Family | FUNDING |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/A-004_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

A-004 is the certified funding calculation and allocation formula for attributing exchange funding cashflows to eligible logical tranches.

#### What it means

The output assigns the exact signed source funding amount across eligible tranches while conserving the source amount exactly.

#### Why it exists

Funding affects realized economics and must be allocated deterministically rather than guessed, omitted, or double-counted.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Source funding transaction | Stable funding cashflow identity | Order Management financial facts | Signed source amount, currency, quantum |
| Eligible tranche set | Tranches exposed during funding interval | Lifecycle/accounting state | IDs and intervals |
| Allocation basis | Exposure/time basis defined by spec | Lifecycle evidence | Exact rational weights |
| Coverage interval | Funding interval evidence | API / Lifecycle | Half-open `[from, to)` |

#### Data source

Funding facts come from exchange/API financial records. Eligibility and exposure windows come from Lifecycle accounting state.

#### Formula or rule

A-004 computes exact rational raw allocations by eligible weights, truncates base allocations toward zero to the source quantum, computes residue:

```text
residue = signed_source_funding_amount - sum(base_allocations)
```

and assigns the entire signed residue to the tranche with the largest absolute unrounded allocation, tie-broken by lowest `tranche_id` in ascending case-sensitive Unicode code-point order.

#### Calculation / evaluation steps

1. Require complete funding cashflow identity, amount, currency, quantum, settlement basis, and coverage.
2. Determine eligible tranches and exact allocation weights.
3. Compute raw signed allocations exactly.
4. Truncate each base allocation toward zero to the source quantum.
5. Compute residue exactly.
6. Select residue recipient by largest absolute raw allocation, then `tranche_id` tie-break.
7. Add residue to that recipient.
8. Persist allocation manifest and source conservation evidence.

#### Output

Per-tranche signed funding allocations and allocation manifest.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Finality is blocked when source amount is unrepresentable at required precision, coverage is partial, settlement evidence is missing, eligible set is unresolved, currency is unsupported, or source identity conflicts exist. Do not round source amount, omit funding, or use an estimated funding rate as realized allocation.

#### Dependencies

- Policy dependency: N-001.
- Policy dependency: N-006.
- Policy dependency: N-007.
- Factual data dependency: Order Management `GET_FINANCIAL_FACTS`.
- Architecture dependency: Lifecycle exposure and finality evidence.

#### Used by

- A-002.
- S-004.
- A-009 through final results.

#### Important boundaries

A-004 allocates realized funding; it is not planned net edge and is excluded from F-012 planned minimum net edge unless a future approved methodology changes that.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/A-004_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md` section 32.

### A-005 - Fill Quantity / Remaining Quantity / VWAP

#### Classification

| Field | Value |
|---|---|
| ID | A-005 |
| Owner | Order Lifecycle |
| Type | ACCOUNTING_FORMULA |
| Family | EXECUTION |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` order events, executions, and financial factual response |

#### What it is

A-005 aggregates factual executions into cumulative fill quantity, remaining quantity, and VWAP.

#### What it means

It tells how much of an order/tranche has actually executed and at what weighted average price.

#### Why it exists

It supports lifecycle state, exposure tracking, gross PnL, finality, and reconciliation.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Execution rows | Actual fills | Order Management API | Execution ID, quantity, price |
| Ordered/attributed quantity | Quantity authorized for logical order/tranche | Lifecycle | Quantity decimal |
| Native chronology/provenance | Ordering and source proof | API / native profile | Timestamps/sequences |

#### Data source

Raw facts are native execution records normalized by the API adapter. Aggregates are Lifecycle-derived.

#### Formula or rule

```text
cumulative_fill_qty = sum(attributed_execution_qty)
remaining_qty = authorized_qty - cumulative_fill_qty
VWAP = sum(qty_i * price_i) / sum(qty_i)
```

#### Calculation / evaluation steps

1. Collect executions with stable identities and provenance.
2. Attribute each execution to the logical tranche/order.
3. Deduplicate by accepted source identity.
4. Sum quantities exactly.
5. Compute remaining quantity from authorized quantity.
6. Compute VWAP only when cumulative quantity is positive.
7. Preserve chronology and contradiction evidence for replay.

#### Output

Cumulative fill quantity, remaining quantity, VWAP when defined, and execution lineage.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

VWAP is unavailable when no attributed quantity exists. Aggregation is unavailable or reconciling when attribution, source identity, quantity, price, or chronology is unresolved. Do not infer fills from order status alone.

#### Dependencies

- Policy dependency: N-001.
- Policy dependency: N-005.
- Factual data dependency: native execution records.

#### Used by

- A-001.
- A-002.
- A-008.
- S-004.
- Lifecycle state transitions.

#### Important boundaries

A-005 is factual aggregation, not a trading strategy. It does not create execution authority and does not substitute for financial finality.

#### Technical traceability

Primary: `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md`; `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`. Implementation cross-check: `src/triggertrade/accounting/futures.py::compute_vwap`.

### A-006 - Execution-Linked Cashflow Allocation

#### Classification

| Field | Value |
|---|---|
| ID | A-006 |
| Owner | Accounting |
| Type | ACCOUNTING_FORMULA |
| Family | PNL |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 2 output classes |

#### What it is

A-006 governs allocation of non-funding execution-linked cashflows and residue assignment.

#### What it means

It distributes exact source cashflows to logical tranches while preserving the exact source amount and quantum.

#### Why it exists

It prevents rounding drift, double attribution, or loss of small residue amounts in final accounting.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Source cashflow | Non-funding exchange cost/refund | Order Management facts | Signed amount and source quantum |
| Eligible recipients | Logical tranche/execution links | Lifecycle | IDs and weights |
| Allocation weights | Basis for allocation | Lifecycle/accounting | Exact rational values |

#### Data source

Source cashflows come from exchange financial facts. Eligibility and weights come from Lifecycle attribution.

#### Formula or rule

Use exact rational weights, truncate allocations toward zero to the authoritative positive source quantum, then assign residue so the allocated total equals the exact signed source amount.

#### Calculation / evaluation steps

1. Validate source identity, signed amount, quantum, currency, and coverage.
2. Determine eligible linked recipients.
3. Compute exact raw allocations.
4. Truncate toward zero to source quantum.
5. Compute exact residue.
6. Assign residue per the approved residue rule.
7. Persist manifest and conservation proof.

#### Output

Per-recipient execution-linked cashflow allocations and residue recipient.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable for missing source identity, unsupported currency, invalid quantum, incomplete coverage, unresolved recipient set, or duplicate aliases. Do not round the source amount or drop residue.

#### Dependencies

- Policy dependency: N-001.
- Policy dependency: N-002.
- Policy dependency: N-006.
- Factual data dependency: financial cashflow facts.

#### Used by

- A-002.
- S-004.

#### Important boundaries

A-006 is not funding allocation; A-004 remains separate. It does not decide whether a trade is profitable or eligible.

#### Technical traceability

Primary: `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 2; `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` financial facts.

### A-007 - Equity / Unrealized PnL / Live Drawdown Snapshot

#### Classification

| Field | Value |
|---|---|
| ID | A-007 |
| Owner | Accounting |
| Type | ACCOUNTING_FORMULA |
| Family | EQUITY |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md` account facts and balances |

#### What it is

A-007 is the live account snapshot of equity, unrealized PnL, and drawdown state from Portfolio/account facts.

#### What it means

It shows current live financial state, including open-position unrealized effects. It is not the same as research max drawdown and not the same as accounting-day realized loss.

#### Why it exists

Portfolio needs live state for health, display, reconciliation, and capacity context.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Wallet/account balances | Current account facts | Portfolio Data API | Currency amounts |
| Open positions | Current exposure and mark/valuation facts | Portfolio Data API | Position facts |
| Unrealized PnL | Native or derived live unrealized component | Portfolio Data API / Portfolio | Governed currency where admissible |
| Daily base | Fixed day base | Portfolio state | Governed currency |

#### Data source

Raw facts come from Portfolio Data API account, wallet, and position facts. Portfolio derives/merges snapshot state.

#### Formula or rule

The methodology requires Portfolio to track:

```text
current_portfolio_equity
daily_realized_pnl
unrealized_pnl
total_pnl = daily_realized_pnl + unrealized_pnl
```

Drawdown snapshot is derived from live equity/base context according to approved Portfolio state semantics.

#### Calculation / evaluation steps

1. Refresh Portfolio state from account and position facts.
2. Preserve unresolved local holds and commitments.
3. Validate currency and provenance.
4. Merge API-confirmed facts with local Portfolio state.
5. Compute current equity, unrealized PnL, total PnL, and drawdown snapshot for display/diagnostics.

#### Output

Live equity, unrealized PnL, total PnL, and drawdown snapshot/state.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable or stale when Portfolio facts are partial, stale, unsupported-currency, contradictory, or cannot be reconciled with local holds/commitments. Do not erase local holds because they are absent from API data.

#### Dependencies

- Policy dependency: N-006.
- Policy dependency: N-007.
- Factual data dependency: Portfolio Data API account and position facts.
- State dependency: Portfolio state health.

#### Used by

- Portfolio state/read models.
- S-001.
- Operator display and diagnostics.

#### Important boundaries

A-007 is live/account snapshot state. It is distinct from M-004 research max drawdown and from A-009 accounting-day realized totals. It does not produce a FINAL logical result.

#### Technical traceability

Primary: `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md`; `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` sections 4 and 9. Implementation cross-check: `src/triggertrade/accounting/futures.py`.

### A-008 - Pre-Close Partial-Entry Capital Apportionment

#### Classification

| Field | Value |
|---|---|
| ID | A-008 |
| Owner | Accounting |
| Type | ACCOUNTING_FORMULA |
| Family | CAPITAL_ALLOCATION |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 5 |

#### What it is

A-008 apportions approved committed capital between filled and still-authorized entry remainder before any close acquire.

#### What it means

It tells Portfolio how much capital remains tied to the filled part and how much remains reserved for unfilled entry remainder.

#### Why it exists

It prevents over-release or under-retention during partial entry fills before close authority begins.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `A` | Approved quantum-aligned actual capital | F-015 | Qcapital |
| `Q` | Approved quantity | F-011 | Quantity |
| `F` | Cumulative entry-filled quantity | A-005 | Quantity |
| `R` | Still-authorized entry remainder | A-005 / Lifecycle | Quantity |

#### Data source

Approved capital and quantity come from construction. Fill and remainder come from Lifecycle execution aggregation.

#### Formula or rule

Validate:

```text
Q > 0
0 <= F
0 <= R
F + R <= Q
```

Before close acquire:

```text
retained_entry_total = ceil_Qcapital(A * (F + R) / Q)
if R > 0:
    filled_committed_capital = floor_Qcapital(A * F / Q)
    remaining_reserved_capital = retained_entry_total - filled_committed_capital
else:
    filled_committed_capital = retained_entry_total
    remaining_reserved_capital = 0
released_unfilled_capital = A - retained_entry_total
```

#### Calculation / evaluation steps

1. Validate approved capital, quantity, filled quantity, and remainder.
2. Compute exact retained entry total.
3. If remainder exists, floor filled committed capital and assign residue to reserved remainder.
4. If no remainder exists, retain the ceiling of filled exact liability.
5. Compute released unfilled capital.
6. Preserve all values as Portfolio accounting state.

#### Output

Filled committed capital, remaining reserved capital, retained total, and released unfilled capital.

#### Worked example

Policy example: with `A=1`, `Q=3`, `F=1`, `R=2`, filled capital is `0.333333333333`, reserved is `0.666666666667`, total is `1`.

#### Unavailable / invalid behavior

Unavailable when inputs are missing, malformed, negative, inconsistent, or when `F + R > Q`. Do not use this rule after close acquire to proportionally release closing capital.

#### Dependencies

- Formula dependency: A-005.
- Policy dependency: F-015.
- Policy dependency: N-001 and N-002.

#### Used by

- Portfolio accounting state.
- S-001 capacity/hold state.

#### Important boundaries

A-008 applies before close acquire. It cannot be reused to release capital during close; P6 keeps committed capital and slot retained until canonical CLOSED.

#### Technical traceability

Primary: `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 5.

### A-009 - Accounting-Day Realized Totals and Daily Loss Gate Input

#### Classification

| Field | Value |
|---|---|
| ID | A-009 |
| Owner | Accounting |
| Type | ACCOUNTING_FORMULA |
| Family | DRAWDOWN |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/A-009_FINAL_FORMULA_SPECIFICATION.md` |

#### What it is

A-009 aggregates FINAL net realized results by accounting day and evaluates the daily loss gate input/state.

#### What it means

It tracks realized loss for the current accounting day and determines whether new exposure must be blocked because the daily loss limit has been reached or state is unavailable.

#### Why it exists

It enforces daily realized-loss discipline using final accounting results rather than research drawdown or live unrealized snapshot alone.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `net_realized_result_i` | Final logical result | A-002 | Governed currency |
| `accounting_day_id_i` | Day assigned by final closing execution policy | Lifecycle / N-007 | Accounting day |
| `daily_portfolio_base_d` | Fixed day base | Portfolio | Governed currency |
| `daily_loss_limit_pct` | Configured threshold | Portfolio config | Percent |
| Latch state | Current day daily-loss latch | Portfolio state | State |

#### Data source

Final results come from Lifecycle FINAL events. Day/base/configuration/latch state comes from Portfolio accounting.

#### Formula or rule

```text
R_d = sum(net_realized_result_i)
      for eligible FINAL logical result i
      with accounting_day_id_i = d
      posted exactly once under result_id and tranche_id

L_d = daily_portfolio_base_d * daily_loss_limit_pct / 100
daily_loss_used_amount_d = max(-R_d, 0)
```

Gate:

```text
disabled -> not blocking
latched -> blocking
unavailable required state -> fail closed blocking
R_current_day <= -L_current_day -> latch and block
otherwise -> OK
```

#### Calculation / evaluation steps

1. Consume each FINAL result exactly once by `result_id` and `tranche_id`.
2. Assign result to its authoritative accounting day.
3. Sum net realized results for the day.
4. Compute current daily loss limit from fixed day base and configured percent.
5. Preserve existing latch if set.
6. Fail closed when required day/base/config/recovery state is unavailable.
7. Latch when exact comparison reaches or breaches the limit.

#### Output

Accounting-day realized total, daily loss used amount, daily loss status, and whether new exposure is blocked.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable/fail-closed when day state, base, configuration, recovery, result receipt, or final-result evidence is missing or contradictory. Do not count provisional results, research metrics, unrealized PnL, or duplicate FINAL events.

#### Dependencies

- Formula dependency: A-002.
- Policy dependency: N-007.
- Configuration dependency: daily loss enabled flag and threshold.
- State dependency: Portfolio accounting day and latch.

#### Used by

- S-001 Portfolio eligibility.
- Portfolio grant/hold decisions for new exposure.
- Operator read models.

#### Important boundaries

A-009 is accounting-day realized aggregation, not research drawdown. It does not rewrite A-002 results and does not use M-004. Threshold value remains configuration.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/A-009_FINAL_FORMULA_SPECIFICATION.md`. Supporting: `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` daily accounting and daily loss sections.

# M - Research Metrics Library

### M-001 - Research Net P/L

#### Classification

| Field | Value |
|---|---|
| ID | M-001 |
| Owner | Research |
| Type | RESEARCH_METRIC |
| Family | RESEARCH_PERFORMANCE |
| Canonical status | RESEARCH_ONLY |
| Canonical source | `docs/BACKEND_TARGET_MODEL.md` section 13; `src/triggertrade/analytics/futures.py` |

#### What it is

M-001 sums net P/L across a research sample of closed trade facts.

#### What it means

It reports the total research-period net outcome for a pinned Set/version sample. It is diagnostic reporting, not live trading authority.

#### Why it exists

It lets research compare versions, samples, and backtest/demo runs using finalized or simulated accounting facts.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Closed trade facts | Research sample records | Research/backtest store | `TradePerformanceFact` |
| `net_pnl` | Net outcome per trade | Accounting or simulator | Decimal |
| Set identity/version | Sample membership | Research pin | IDs |

#### Data source

Research result set from isolated research/backtest/demo records. Live trading state is not modified.

#### Formula or rule

```text
research_net_pnl = sum(trade.net_pnl for trades in sample)
```

#### Calculation / evaluation steps

1. Load pinned research sample.
2. Validate trade membership against requested Set ID/version.
3. Sum `net_pnl` exactly across the sample.
4. Report with sample period and evidence source.

#### Output

Research-only net P/L decimal.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when sample is missing, membership mismatches, evidence sources are incompatible for comparison, or required accounting/simulation facts are missing. Do not fill missing trades with zero.

#### Dependencies

- Research data dependency: closed trade facts.
- Architecture dependency: S-006 research isolation.
- Optional formula dependency: A-002 when using finalized live accounting facts.

#### Used by

- Research reporting.
- Baseline/candidate comparison.

#### Important boundaries

M-001 does not affect live trading, activation, Portfolio release, or configuration promotion by itself.

#### Technical traceability

Primary: `docs/BACKEND_TARGET_MODEL.md` section 13. Implementation cross-check: `src/triggertrade/analytics/futures.py::compute_futures_performance`.

### M-002 - Research Win Rate

#### Classification

| Field | Value |
|---|---|
| ID | M-002 |
| Owner | Research |
| Type | RESEARCH_METRIC |
| Family | RESEARCH_PERFORMANCE |
| Canonical status | RESEARCH_ONLY |
| Canonical source | `docs/BACKEND_TARGET_MODEL.md` section 13; `src/triggertrade/analytics/futures.py` |

#### What it is

M-002 computes the percentage of research sample trades with positive net PnL.

#### What it means

It shows how often trades in a research sample were winners by net result. It does not measure magnitude or guarantee profitability.

#### Why it exists

It helps research characterize strategy behavior across samples.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Closed trade facts | Research sample | Research/backtest store | Records |
| `net_pnl` | Outcome per trade | Accounting or simulator | Decimal |

#### Data source

Research/backtest result set.

#### Formula or rule

```text
wins = count(trade.net_pnl > 0)
closed = count(trades)
win_rate_pct = wins / closed * 100
```

#### Calculation / evaluation steps

1. Validate sample membership.
2. Count closed trades.
3. Count trades where net PnL is greater than zero.
4. Divide by closed count and multiply by 100 when count is nonzero.

#### Output

Research-only win rate percentage, or unavailable when no closed trades exist.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when closed count is zero or sample data is missing/invalid. Break-even trades are neither wins nor losses under current implementation.

#### Dependencies

- Research data dependency: closed trade facts.
- Architecture dependency: S-006.

#### Used by

- Research reporting.
- M-006 quality observations indirectly.

#### Important boundaries

Win-rate acceptance thresholds are research policy/configuration unless frozen elsewhere. M-002 does not approve trading.

#### Technical traceability

Primary: `docs/BACKEND_TARGET_MODEL.md` section 13. Implementation cross-check: `src/triggertrade/analytics/futures.py::compute_futures_performance`.

### M-003 - Research Profit Factor

#### Classification

| Field | Value |
|---|---|
| ID | M-003 |
| Owner | Research |
| Type | RESEARCH_METRIC |
| Family | RESEARCH_PERFORMANCE |
| Canonical status | RESEARCH_ONLY |
| Canonical source | `docs/BACKEND_TARGET_MODEL.md` section 13; `src/triggertrade/analytics/futures.py` |

#### What it is

M-003 computes research profit factor from positive and negative net outcomes.

#### What it means

It compares total net winning outcomes to the absolute value of total net losing outcomes. It is undefined when there are no losing outcomes.

#### Why it exists

It helps research evaluate payoff asymmetry in a sample.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Net positive outcomes | Sum of net PnL > 0 | Research sample | Decimal |
| Net negative outcomes | Sum of net PnL < 0 | Research sample | Decimal |

#### Data source

Research/backtest result set.

#### Formula or rule

```text
profit_factor = sum(net_pnl > 0) / abs(sum(net_pnl < 0))
```

When gross loss denominator is zero, the result is unavailable/undefined with a reason.

#### Calculation / evaluation steps

1. Validate sample membership.
2. Sum positive net outcomes.
3. Sum negative net outcomes.
4. If loss sum is zero, return unavailable/undefined reason.
5. Otherwise divide positive sum by absolute negative sum.

#### Output

Research-only profit factor and optional unavailable reason.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when no losing outcomes exist, sample is missing, or membership is invalid. Do not represent undefined profit factor as zero.

#### Dependencies

- Research data dependency: closed trade facts.
- Architecture dependency: S-006.

#### Used by

- Research reporting.

#### Important boundaries

Profit-factor thresholds are not canonical trading rules in this library. M-003 does not block or authorize live trades.

#### Technical traceability

Primary: `docs/BACKEND_TARGET_MODEL.md` section 13. Implementation cross-check: `src/triggertrade/analytics/futures.py::_profit_factor`.

### M-004 - Research Max Drawdown

#### Classification

| Field | Value |
|---|---|
| ID | M-004 |
| Owner | Research |
| Type | RESEARCH_METRIC |
| Family | DRAWDOWN |
| Canonical status | RESEARCH_ONLY |
| Canonical source | `docs/BACKEND_TARGET_MODEL.md` section 13; `src/triggertrade/analytics/futures.py` |

#### What it is

M-004 is a research max drawdown metric over a research result set.

#### What it means

It reports drawdown for research/backtest analysis. It is not the live account snapshot in A-007 and not the accounting-day realized loss gate in A-009.

#### Why it exists

It helps evaluate research sample risk characteristics.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Research equity/result path | Backtest or research result sequence | Research/backtest worker | Decimal series |
| `max_drawdown` value | Supplied computed drawdown | Research calculation | Decimal or null |

#### Data source

Research/backtest result set. Current implementation accepts a `max_drawdown` input to performance aggregation.

#### Formula or rule

The target model classifies this as research aggregation. The current analytics surface reports the provided research `max_drawdown` value with the sample.

#### Calculation / evaluation steps

1. Load pinned research result set.
2. Validate run/sample identity.
3. Compute or consume research drawdown according to the research run's pinned method.
4. Report as research-only diagnostic.

#### Output

Research-only max drawdown value, or unavailable.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when the research path or drawdown value is missing, sample membership is invalid, or run evidence is incomplete. Do not substitute A-007 live drawdown or A-009 daily realized loss.

#### Dependencies

- Research data dependency: research result path.
- Architecture dependency: S-006.

#### Used by

- Research reporting.
- Research comparisons.

#### Important boundaries

M-004 is research-only. It does not affect live trading, daily loss latch, Portfolio release, or exposure eligibility.

#### Technical traceability

Primary: `docs/BACKEND_TARGET_MODEL.md` section 13. Supporting: `docs/FORMULA_METRICS_CATALOG.md` row M-004. Implementation cross-check: `src/triggertrade/analytics/futures.py::compute_futures_performance`.

### M-005 - Research Expectancy and Average Outcomes

#### Classification

| Field | Value |
|---|---|
| ID | M-005 |
| Owner | Research |
| Type | RESEARCH_METRIC |
| Family | RESEARCH_PERFORMANCE |
| Canonical status | RESEARCH_ONLY |
| Canonical source | `docs/BACKEND_TARGET_MODEL.md` section 13; `src/triggertrade/analytics/futures.py` |

#### What it is

M-005 computes research expectancy per trade, average winner, and average loser.

#### What it means

It summarizes average net outcome and the average size of positive and negative outcomes in a research sample.

#### Why it exists

It helps research understand whether performance comes from win frequency, payoff size, or both.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Closed trade facts | Research sample | Research/backtest store | Records |
| `net_pnl` | Outcome per trade | Accounting or simulator | Decimal |

#### Data source

Research/backtest result set.

#### Formula or rule

```text
expectancy_per_trade = sum(net_pnl) / closed_count
average_winner = sum(net_pnl > 0) / wins
average_loser = sum(net_pnl < 0) / losses
```

#### Calculation / evaluation steps

1. Validate sample membership.
2. Count closed trades, wins, and losses.
3. Sum total, positive, and negative net outcomes.
4. Divide by the appropriate count when nonzero.
5. Mark winner/loser averages unavailable when their denominator is zero.

#### Output

Research-only expectancy, average winner, and average loser.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Expectancy is unavailable when closed count is zero. Average winner is unavailable when wins are zero. Average loser is unavailable when losses are zero. Do not fill unavailable averages with zero.

#### Dependencies

- Research data dependency: closed trade facts.
- Architecture dependency: S-006.

#### Used by

- Research reporting.
- Baseline/candidate comparison.

#### Important boundaries

M-005 does not define acceptance thresholds and does not approve promotion to active trading.

#### Technical traceability

Primary: `docs/BACKEND_TARGET_MODEL.md` section 13. Implementation cross-check: `src/triggertrade/analytics/futures.py::compute_futures_performance`.

### M-006 - Research Fee Drag / Concentration / Quality Warnings

#### Classification

| Field | Value |
|---|---|
| ID | M-006 |
| Owner | Research |
| Type | RESEARCH_METRIC |
| Family | RESEARCH_PERFORMANCE |
| Canonical status | RESEARCH_ONLY |
| Canonical source | `docs/BACKEND_TARGET_MODEL.md` section 13; `src/triggertrade/analytics/futures.py` |

#### What it is

M-006 produces research quality diagnostics such as fee drag, sample size warning, symbol/direction concentration, and regime diversity warning.

#### What it means

The output highlights research-sample quality concerns. It is an advisory diagnostic, not a trading gate.

#### Why it exists

It helps prevent over-reading weak, concentrated, fee-heavy, or regime-thin research samples.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Closed trade sample | Research facts | Research/backtest store | Records |
| Fees | Sum of entry, exit, and other fees | Research facts | Decimal |
| Gross profit | Sum of positive gross outcomes | Research facts | Decimal |
| Quality policy | Warning thresholds | Research policy/config | Counts/percent |
| Symbol/direction/regime labels | Concentration and diversity dimensions | Research facts | Labels |

#### Data source

Research/backtest result set and research quality policy.

#### Formula or rule

Current implementation computes:

```text
fees_as_pct_of_gross_profit = fees / gross_profit * 100 when gross_profit > 0
top_concentration_pct = top_count / sample_count * 100
```

Warnings are emitted when sample size, concentration, regime diversity, or fee drag cross research policy settings.

#### Calculation / evaluation steps

1. Validate research sample.
2. Sum fees and gross profit.
3. Compute fee drag when denominator is positive.
4. Compute top concentration by symbol and direction.
5. Inspect regime-label diversity.
6. Compare to research quality policy thresholds.
7. Emit warning strings/observations.

#### Output

Research-only warnings, observations, fee drag percent, and concentration diagnostics.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Fee drag is unavailable when gross profit is nonpositive. Concentration is unavailable for empty samples. Regime diversity is unavailable when no regime labels exist. Warning thresholds remain research policy and must not be treated as canonical live rules.

#### Dependencies

- Research data dependency: closed trade facts.
- Research configuration dependency: quality policy.
- Architecture dependency: S-006.

#### Used by

- Research reporting.
- Research recommendation observations.

#### Important boundaries

M-006 does not reject live trades, change configuration, or approve activation. Its thresholds are not methodology truth unless separately frozen.

#### Technical traceability

Primary: `docs/BACKEND_TARGET_MODEL.md` section 13. Implementation cross-check: `src/triggertrade/analytics/futures.py::PerformanceQualityPolicy`, `_quality_warnings`, `_top_concentration_pct`.

### M-007 - Backtest Spread / Slippage / Cost Assumptions

#### Classification

| Field | Value |
|---|---|
| ID | M-007 |
| Owner | Research |
| Type | RESEARCH_METRIC |
| Family | BACKTEST |
| Canonical status | RESEARCH_ONLY |
| Canonical source | `docs/BACKEND_TARGET_MODEL.md` section 13; `src/triggertrade/backtest/simulator.py` |

#### What it is

M-007 records and applies research/backtest assumptions for spread, slippage, and simulated costs.

#### What it means

The output is a research simulation adjustment, not factual execution cost and not live accounting.

#### Why it exists

Backtests need explicit pinned assumptions to avoid pretending simulated fills are actual exchange facts.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Spread basis points | Simulated spread assumption | Research/backtest config | bps |
| Slippage basis points | Simulated slippage assumption | Research/backtest config | bps |
| Maker/taker fee rates | Simulated fee assumptions | Research/backtest config | Fractional rates |
| Historical candle | Simulated fill source | Backtest data | OHLC |

#### Data source

Research/backtest configuration and historical data, isolated from live exchange execution.

#### Formula or rule

Current simulator cost adjustment:

```text
long entry price = price * (1 + (spread_bps + slippage_bps) / 10000)
long exit price  = price * (1 - (spread_bps + slippage_bps) / 10000)
```

Fees are simulated from configured rates and simulated notional.

#### Calculation / evaluation steps

1. Pin research/backtest assumptions to the run.
2. Apply cost basis points to simulated entry/exit prices.
3. Compute simulated fees from configured rates.
4. Store the simulation model version and evidence source.
5. Keep results isolated from live accounting.

#### Output

Research-only simulated cost-adjusted fills, fees, and diagnostics.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when assumptions, historical candle data, or run pins are missing. Current simulator rejects unsupported profiles such as non-linear category, unsupported direction, or funding-boundary crossing. Do not use these assumptions as actual fees or live execution facts.

#### Dependencies

- Research configuration dependency: spread/slippage/fee assumptions.
- Research data dependency: historical candles.
- Architecture dependency: S-006.

#### Used by

- Backtest reports.
- M-001 through M-006 research metrics.

#### Important boundaries

M-007 is simulation-only. It does not set live spread/slippage gates, does not alter F-012 planned edge, and does not replace factual A-003/A-004 accounting.

#### Technical traceability

Primary: `docs/BACKEND_TARGET_MODEL.md` section 13. Implementation cross-check: `src/triggertrade/backtest/simulator.py::_apply_cost_bps`, `simulate_closed_trade`.

### M-008 - Research Grouping / Direction Mix / Regime Aggregation

#### Classification

| Field | Value |
|---|---|
| ID | M-008 |
| Owner | Research |
| Type | AGGREGATION_RULE |
| Family | RESEARCH_PERFORMANCE |
| Canonical status | RESEARCH_ONLY |
| Canonical source | `docs/BACKEND_TARGET_MODEL.md` section 13; `src/triggertrade/analytics/futures.py` |

#### What it is

M-008 groups research trade facts by dimensions such as trigger set, symbol, direction, and regime.

#### What it means

It explains where research outcomes came from across cohorts. It is aggregation/reporting, not live decision logic.

#### Why it exists

Research needs cohort-level comparisons and direction mix/regime diagnostics.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Trade facts | Research sample | Research/backtest store | Records |
| Grouping dimension | Desired cohort dimension | Research reporting request | `trigger_set`, `symbol`, `direction`, `regime` |
| Labels | Symbol, direction, regime labels | Research facts / S-005 diagnostic | Strings/enums |

#### Data source

Research/backtest result set and diagnostic labels.

#### Formula or rule

Current grouping keys:

```text
trigger_set -> trigger_set_id@trigger_set_version
symbol -> trade.symbol
direction -> trade.direction
regime -> trade.regime_label or "unavailable"
```

Direction mix:

```text
LONG long_count/total; SHORT short_count/total
```

#### Calculation / evaluation steps

1. Validate sample membership.
2. Select supported grouping dimension.
3. Assign each trade to exactly one group key.
4. Aggregate downstream metrics per group if requested.
5. Preserve unavailable regime labels as `"unavailable"`.

#### Output

Research-only grouped trade sets, direction mix strings, and cohort reporting inputs.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable or invalid for unsupported grouping dimension, missing sample, invalid membership, or unavailable labels. Do not infer missing regime labels as a specific market regime.

#### Dependencies

- Research data dependency: closed trade facts.
- Optional research dependency: S-005 diagnostic regime labels.
- Architecture dependency: S-006.

#### Used by

- Research reporting.
- M-006 concentration and diversity warnings.
- Baseline/candidate comparison.

#### Important boundaries

M-008 does not promote S-005 into a live trading input. Grouping dimensions and acceptance thresholds remain research/reporting choices unless frozen elsewhere.

#### Technical traceability

Primary: `docs/BACKEND_TARGET_MODEL.md` section 13. Implementation cross-check: `src/triggertrade/analytics/futures.py::group_trade_facts`, `_direction_mix`.

# N - Numeric / Normalization Library

### N-001 - Exact Decimal Arithmetic

#### Classification

| Field | Value |
|---|---|
| ID | N-001 |
| Owner | Cross-System |
| Type | NUMERIC_POLICY |
| Family | MARKET_NORMALIZATION |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 1 |

#### What it is

N-001 is the exact arithmetic rule for monetary/economic calculations.

#### What it means

Decimal strings are parsed exactly. Add, subtract, and multiply are exact; division retains exact rational value until an approved output quantizer applies.

#### Why it exists

It prevents hidden rounding, binary floating-point drift, and epsilon-based gate changes.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Decimal strings | Governed numeric values | Business contracts/API/config | Canonical decimal input |
| Formula operation order | Parentheses/dependency graph | Certified formulas/policies | Exact order |

#### Data source

Applies to system numeric inputs after factual/configuration validation.

#### Formula or rule

No finite-precision intermediate rounding is permitted. Binary floats, nonfinite numbers, exponent-encoded canonical decimals, and epsilon comparisons are forbidden.

#### Calculation / evaluation steps

1. Parse decimal strings exactly into integer/scale or exact rational representation.
2. Execute the formula's operation order exactly.
3. Avoid rounding each operand or intermediate quotient.
4. Apply only the formula's approved output-class quantizer.
5. Reject unrepresentable values explicitly rather than silently rounding.

#### Output

Exact intermediate values and approved final quantized outputs.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Invalid for binary floats, NaN, infinity, exponent-encoded canonical decimals, unknown rounding context, unrepresentable values, or epsilon comparisons. Do not silently coerce.

#### Dependencies

- Documentation dependency: certified formula operation order.
- Factual/configuration dependency: validated decimal strings.

#### Used by

- F-011, F-012, F-014, F-015.
- A-series accounting formulas.
- N-002 and N-003.

#### Important boundaries

N-001 does not approve any trading formula or threshold. It only governs arithmetic.

#### Technical traceability

Primary: `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 1.

### N-002 - Quantization Classes

#### Classification

| Field | Value |
|---|---|
| ID | N-002 |
| Owner | Cross-System |
| Type | NUMERIC_POLICY |
| Family | MARKET_NORMALIZATION |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 2 |

#### What it is

N-002 defines output quantization classes such as `Qcapital`, `Qratio`, tick, step, and source cashflow quantum.

#### What it means

Different values round in different directions for different reasons. Spendable capital floors; liability ceilings; quantity uses venue step; ratio serialization floors; source cashflows conserve their source quantum.

#### Why it exists

It prevents using one generic rounding rule for capital, ratios, quantities, prices, and source cashflows.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Exact value | Value ready for final output | Formula/policy | Exact rational/decimal |
| Output class | Required quantizer | Numeric policy | Enum/class |
| Quantum | Grid size | Policy or instrument/source fact | Decimal |

#### Data source

Quanta come from policy (`Qcapital`, `Qratio`), instrument facts (tick/step), or source facts (cashflow quantum).

#### Formula or rule

```text
floor_q(x) = q * floor(x / q)
ceil_q(x) = q * ceil(x / q)
trunc_q(x) = q * trunc_toward_zero(x / q)
```

#### Calculation / evaluation steps

1. Identify the output class from the governing formula/policy.
2. Select the correct quantum and direction.
3. Apply quantization only at the final boundary for that output.
4. Preserve exact values where policy says no rounding.
5. Persist the policy version.

#### Output

Quantized canonical numeric value for the specific output class.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Invalid when output class is unknown, quantum is missing/nonpositive, or an unrelated quantizer is applied. Do not use tick rounding for money or Qcapital for price.

#### Dependencies

- Policy dependency: N-001.
- Factual dependency: instrument tick/step or source quantum where applicable.

#### Used by

- F-009, F-010, F-011, F-014, F-015.
- A-006, A-008.
- N-004.

#### Important boundaries

N-002 is representation policy, not a market metric. It does not select prices, thresholds, or trades.

#### Technical traceability

Primary: `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 2.

### N-003 - Canonical JSON and Digest Encoding

#### Classification

| Field | Value |
|---|---|
| ID | N-003 |
| Owner | Cross-System |
| Type | NUMERIC_POLICY |
| Family | OTHER:CANONICAL_IDENTITY |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 6 |

#### What it is

N-003 defines canonical numeric encoding, JSON serialization, and digest identity rules.

#### What it means

The same semantic object must serialize the same way for replay, digest, and immutable identity. Display formatting cannot feed back into gates.

#### Why it exists

It supports immutable specs, replay, configuration pins, and content identity.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Canonical values | Already selected numeric/object values | Business owner | Canonical decimal strings |
| Object envelope | Immutable spec/config/event payload | Business contracts | JSON object |
| Versions | Policy/schema/config versions | Business owners | Strings |

#### Data source

Applies to persisted business objects and digests after value selection.

#### Formula or rule

Decimal encoding: decimal point only where needed; no exponent, plus sign, redundant leading integer zeros, trailing fractional zeros, or negative zero. JSON uses sorted keys and compact UTF-8.

#### Calculation / evaluation steps

1. Normalize decimal strings after approved value selection.
2. Normalize negative zero to `0`.
3. Serialize object with sorted keys and compact UTF-8 JSON.
4. Include required versions and immutable envelope fields.
5. Compute digest over canonical bytes.
6. Require deserialize/recompute/serialize to be byte-equivalent.

#### Output

Canonical JSON bytes and content digest.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Invalid for arbitrary Decimal context approximations, NaN, exponent forms, missing versions, unsorted/noncanonical object serialization, or display-formatted values. Do not change raw provenance spelling; canonical values and raw facts are distinct.

#### Dependencies

- Policy dependency: N-001.
- Policy dependency: N-002 when values require quantization.

#### Used by

- Configuration pins.
- Order Spec digest.
- Market Handoff identity.
- Research pins.
- Replay/proof infrastructure.

#### Important boundaries

N-003 does not define trading semantics. It protects identity and replay.

#### Technical traceability

Primary: `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 6. Implementation cross-check: `src/triggertrade/canonical_json.py`.

### N-004 - Price and Quantity Tick/Step Normalization

#### Classification

| Field | Value |
|---|---|
| ID | N-004 |
| Owner | API / Execution |
| Type | NORMALIZATION_RULE |
| Family | EXECUTION |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 2 and instrument facts in API contracts |

#### What it is

N-004 governs validation and use of price tick and quantity step facts.

#### What it means

Prices and quantities must align to the instrument's actual grid where formulas require it. Native factual values are preserved and not silently repaired.

#### Why it exists

It prevents submitting invalid exchange quantities/prices and prevents hidden rounding outside certified formulas.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `tick_size` | Price grid | Instrument metadata | Positive decimal |
| `qty_step` | Quantity grid | Instrument metadata | Positive decimal |
| Price/quantity value | Formula output or factual value | Position/API | Decimal |
| Provenance | Instrument fact source | Portfolio/API | Source refs |

#### Data source

Instrument metadata from API/Portfolio facts; formula values from Position.

#### Formula or rule

Use existing direction-specific Entry/SL/TP rounding and quantity floor where certified formulas specify it. Validate grid membership by exact division by tick/step.

#### Calculation / evaluation steps

1. Obtain instrument metadata with provenance.
2. Validate tick/step are positive exact decimals.
3. Apply formula-specific rounding only where authorized.
4. Check resulting value is on-grid.
5. Preserve native facts exactly for factual records.

#### Output

On-grid price/quantity validation or normalized formula output.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when instrument metadata is missing, partial, stale, contradictory, nonpositive, or not applicable without proof. Do not invent tick/step, use venue defaults without provenance, or repair native factual values.

#### Dependencies

- Policy dependency: N-001 and N-002.
- Factual dependency: instrument metadata.

#### Used by

- F-008, F-009, F-010, F-011.
- Order Spec validation.
- API hard execution facts.

#### Important boundaries

N-004 does not choose Entry/SL/TP. It validates and applies grids only under approved formula rules.

#### Technical traceability

Primary: `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 2; `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md`; `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md`.

### N-005 - Native Exchange Fact Sign and Source Normalization

#### Classification

| Field | Value |
|---|---|
| ID | N-005 |
| Owner | API |
| Type | NORMALIZATION_RULE |
| Family | MARKET_NORMALIZATION |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/api-contracts/NATIVE_FACT_PROFILE.md` and financial fact contracts |

#### What it is

N-005 normalizes native exchange facts, source signs, field provenance, and factual identities.

#### What it means

API records what the exchange actually said and maps it into governed factual fields without inventing business ownership or hiding unknowns.

#### Why it exists

It preserves evidence integrity for execution, accounting, reconciliation, and restart.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Native records | Orders, executions, financial rows | Exchange/API | Raw fields |
| Source endpoint/field IDs | Provenance | API | Strings |
| Sign convention | How source signs amount | API profile | Enum |
| Mapping profile | Supported normalization profile | API adapter | Version |

#### Data source

Raw exchange/native API facts.

#### Formula or rule

Normalize signs according to explicit source conventions; preserve raw amount, source field, source convention, native IDs, provenance, missing values, and unknown roles. Unknown required meanings remain unknown/unavailable, not false.

#### Calculation / evaluation steps

1. Capture raw source record and endpoint/field provenance.
2. Apply pinned normalization profile.
3. Preserve null/unknown where native meaning is unsupported.
4. Normalize signed amounts per convention.
5. Retain aliases and source identities for dedupe.
6. Surface facts to business owners without making business decisions.

#### Output

Normalized factual records with raw provenance and source sign semantics.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable or unresolved when source meaning, role, side, chronology, acceptance time, sign convention, currency, or provenance cannot be proven. Do not infer ownership from symbol/time/value heuristics.

#### Dependencies

- Factual dependency: native exchange records.
- Documentation dependency: native profile mapping.

#### Used by

- A-003, A-004, A-005, A-006, A-007.
- S-004.
- Lifecycle reconciliation.

#### Important boundaries

API normalizes facts only. It does not create grants, approve trades, allocate logical accounting by itself, or infer missing business IDs.

#### Technical traceability

Primary: `docs/trading-methodology/api-contracts/NATIVE_FACT_PROFILE.md`; `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md`; `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md`.

### N-006 - Governed Accounting Currency

#### Classification

| Field | Value |
|---|---|
| ID | N-006 |
| Owner | Accounting |
| Type | NORMALIZATION_RULE |
| Family | PNL |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 2A |

#### What it is

N-006 requires one governed accounting/settlement currency for FINAL logical accounting.

#### What it means

All required monetary components in a final result must already be denominated in the tranche's pinned governed currency. Unsupported currency blocks finality.

#### Why it exists

It prevents accidental FX conversion, scalar addition across currencies, or relabeling facts to force finality.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Governed currency binding | Pinned accounting currency | Portfolio/Position/Lifecycle config | Currency code |
| Monetary components | Fees, funding, gross result, other costs | Lifecycle/API facts | Currency amounts |
| Source currency evidence | Actual source currency | API facts | Currency code/provenance |

#### Data source

Pinned configuration and financial facts.

#### Formula or rule

FINAL result is allowed only when every required monetary source/component is already in the governed currency. Required unsupported cross-currency evidence is retained and blocks finality.

#### Calculation / evaluation steps

1. Pin governed currency at first accounting use.
2. Validate every required monetary component currency.
3. Retain unsupported currency evidence exactly.
4. Block FINAL while any required component fails currency admissibility.
5. Do not convert, relabel, net away, or zero unsupported amounts.

#### Output

Currency admissibility state for accounting/finality.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Finality unresolved when governed currency binding is missing, ambiguous, conflicting, or any required monetary source uses unsupported currency. COMPLETE coverage does not waive currency admissibility.

#### Dependencies

- Policy dependency: N-001.
- Factual dependency: financial rows with currency provenance.
- Configuration dependency: pinned accounting currency.

#### Used by

- A-002, A-003, A-004, A-006, A-007, A-009.
- S-004.

#### Important boundaries

N-006 grants no FX conversion authority. Future cross-currency support requires a separate governed specification.

#### Technical traceability

Primary: `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 2A; `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md` financial currency transport.

### N-007 - UTC Windows and Asia/Jerusalem Accounting Day

#### Classification

| Field | Value |
|---|---|
| ID | N-007 |
| Owner | Cross-System |
| Type | NORMALIZATION_RULE |
| Family | MARKET_NORMALIZATION |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` section 1.1 and Portfolio accounting-day policy |

#### What it is

N-007 defines factual time-window handling, fixed UTC analytical windows, and Portfolio accounting-day semantics.

#### What it means

Set analytical populations use fixed UTC completed-calendar windows. Portfolio accounting uses its approved accounting day policy. These are distinct and must not be substituted for each other.

#### Why it exists

It prevents lookahead, timezone drift, incomplete-current-day inclusion, and accounting-day misassignment.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `as_of` | Economic evaluation cutoff | Set/API | UTC RFC3339 |
| Market intervals | Completed candle/bucket windows | Market Data API | Half-open UTC intervals |
| Final close time | Permanent final closing execution time | Lifecycle | Timestamp |
| Accounting timezone | Portfolio accounting day policy | Portfolio config/methodology | Asia/Jerusalem baseline |

#### Data source

Market Data API timestamps, Lifecycle execution timestamps, and Portfolio accounting policy.

#### Formula or rule

Set ordinary normalization uses completed UTC calendar days:

```text
[D - N UTC calendar days, D)
```

where `D` is UTC midnight starting the day containing the cutoff. Portfolio accounting day follows the approved accounting-day policy and is applied to final results.

#### Calculation / evaluation steps

1. Parse timestamps as canonical UTC where required.
2. Use half-open intervals.
3. Exclude incomplete current UTC day from ordinary Set populations.
4. Require completed candles/buckets wholly contained in selected intervals.
5. Assign final accounting day from authoritative final closing execution and Portfolio accounting policy.

#### Output

Deterministic time-window membership and accounting-day IDs.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when timestamps are missing, malformed, ambiguous, noncanonical, incomplete, out-of-range, or when final close/accounting policy binding is unresolved. Do not replace UTC analytical windows with local, exchange, or trailing-hours windows.

#### Dependencies

- Factual dependency: source timestamps.
- Policy dependency: Set numeric policy and Portfolio accounting policy.

#### Used by

- F-003, F-004.
- A-004 and A-009.
- Market Data Request and Portfolio accounting.

#### Important boundaries

UTC analytical windows and Portfolio accounting days serve different purposes. N-007 is not a trading threshold.

#### Technical traceability

Primary: `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` section 1.1; `docs/trading-methodology/methodology/PORTFOLIO_RULES.md` daily accounting boundary; `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md`.

### N-008 - Canonical Set Numeric Output Precision

#### Classification

| Field | Value |
|---|---|
| ID | N-008 |
| Owner | Set |
| Type | NORMALIZATION_RULE |
| Family | SET_ANALYTICS |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md` |

#### What it is

N-008 governs Set-derived working arithmetic, output precision, and serialization.

#### What it means

Set metrics use exact arithmetic, Q36 working-grid rounding where specified, and Q18 handoff exports only at approved boundaries.

#### Why it exists

It prevents hidden precision, display rounding, library defaults, or inconsistent Set/Position handoff values.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Set formula values | Derived Set metric values | Set | Exact/Q36/Q18 as applicable |
| Source facts | Market data | Market Data API | Exact decimals |
| Handoff fields | Values crossing to Position | Market Handoff | Canonical decimal strings |

#### Data source

Set-derived values based on market data facts.

#### Formula or rule

At each named continuous Set metric output, recursive state update, and normalization output, round once to `10^-36` with ROUND_HALF_EVEN. Approved handoff volatility fields round to `10^-18` and must be positive and available.

#### Calculation / evaluation steps

1. Parse market decimals exactly.
2. Evaluate formula order exactly.
3. Round named work outputs once to Q36 where required.
4. Persist dependency values at their work precision.
5. Export only approved boundary values to Q18.
6. Serialize as canonical decimal strings.

#### Output

Canonical Set working values and approved handoff/export values.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable for missing source intervals, ambiguous order, malformed values, invalid zero-close ATR_PCT export, nonpositive required handoff exports, or positive working values rounded to zero at required export. Do not recover hidden precision downstream.

#### Dependencies

- Policy dependency: N-001 conceptually for exact arithmetic, with separate Set policy.
- Factual data dependency: market data source facts.

#### Used by

- F-001 through F-005.
- F-013.
- Market Handoff.
- Position formulas consuming Set values.

#### Important boundaries

N-008 does not add a signal, indicator, or fallback. API does not compute Set trading decisions. Position consumes the exact received values.

#### Technical traceability

Primary: `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`.

# S - State / Classification Library

### S-001 - Portfolio Capacity and Eligibility State

#### Classification

| Field | Value |
|---|---|
| ID | S-001 |
| Owner | Portfolio Rules |
| Type | STATE_CLASSIFICATION_RULE |
| Family | PORTFOLIO_LIMITS |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 3 and Portfolio Rules methodology |

#### What it is

S-001 classifies Portfolio capacity and eligibility state for issuing grants/holds and opening new exposure.

#### What it means

It tells whether Portfolio state is synchronized and capacity gates allow the next step, or whether the system must block/fail closed.

#### Why it exists

Portfolio must protect capital, slots, daily loss, cooldown, and reconciliation state before new exposure.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Portfolio health | LIVE / RECONCILING / STALE | Portfolio | State enum |
| Free capacity | Available own capital | F-014 / Portfolio state | Qcapital |
| Holds/commitments | Existing capital/slot usage | Portfolio | State records |
| Daily loss state | Daily loss gate | A-009 | State |
| Cooldown | Effective symbol cooldown | F-016 | Timestamp/state |

#### Data source

Portfolio state, local holds, Lifecycle events, and Portfolio Data API facts.

#### Formula or rule

Capacity/eligibility is approved when required Portfolio state is synchronized, slots/capital limits pass exactly, daily loss does not block, cooldown does not block, and current atomic hold checks pass.

#### Calculation / evaluation steps

1. Confirm Portfolio state health is eligible for new grants/holds.
2. Recompute exact capital and slot state.
3. Apply daily loss state.
4. Apply symbol cooldown state.
5. Apply configured limits and exact current capacity gates.
6. Classify as eligible, rejected, or unavailable/fail-closed with reasons.

#### Output

Portfolio eligibility/capacity state and rejection/unavailable reasons.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable/fail-closed when Portfolio state is RECONCILING/STALE, required facts are missing, daily loss is unavailable, cooldown lineage is uncertain, capacity state conflicts, or current hold cannot be atomically proven.

#### Dependencies

- Formula/policy dependency: F-014, F-015, F-016.
- Accounting dependency: A-007, A-009.
- Policy dependency: N-001 and N-002.

#### Used by

- Portfolio grant issuance.
- Portfolio submission authorization.
- Coins OPEN/CLOSE decisions.

#### Important boundaries

S-001 does not calculate Entry/Stop/TP and does not submit orders. It classifies Portfolio readiness and capacity.

#### Technical traceability

Primary: `docs/trading-methodology/schemas/NUMERIC_POLICY.md` section 3; `docs/trading-methodology/methodology/PORTFOLIO_RULES.md`. Supporting: `docs/FORMULA_METRICS_CATALOG.md` row S-001.

### S-002 - Set Outcome and Unavailable State

#### Classification

| Field | Value |
|---|---|
| ID | S-002 |
| Owner | Set |
| Type | STATE_CLASSIFICATION_RULE |
| Family | SET_ANALYTICS |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/methodology/SET.md` |

#### What it is

S-002 classifies Set outcomes and unavailable states.

#### What it means

It distinguishes matched opportunities, false/no-match outcomes, unavailable evidence, and lifecycle/monitor states without turning unavailable into false or true.

#### Why it exists

Set must make deterministic handoff decisions and preserve evidence/state boundaries.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Trigger evaluations | TRUE/FALSE/UNAVAILABLE trigger results | F-series Set formulas | Tri-state |
| Direction | LONG/SHORT/NONE | F-005 | Enum |
| Formation epoch | Active scope/config binding | Set | IDs |
| Source evidence | Market data completeness/provenance | Market Data API / Set | Evidence records |

#### Data source

Set-owned evaluations over market data facts and lifecycle events.

#### Formula or rule

Set outcome classification preserves `FALSE`, `TRUE`, and `UNAVAILABLE` distinctly. A valid Market Handoff requires authoritative matched Set evidence and frozen identities.

#### Calculation / evaluation steps

1. Evaluate required Set formulas and source evidence.
2. Preserve unavailable evidence and source conflicts.
3. Apply Set lifecycle/event-consumption rules.
4. Classify outcome as matched, not matched, unavailable, pending/monitoring state, or terminal as applicable.
5. Emit Market Handoff only for a valid matched opportunity.

#### Output

Set outcome/state classification and unavailable reasons.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable when required market facts, source identity, formula outputs, epoch binding, or lifecycle evidence are missing/incompatible. Do not bridge `FALSE -> TRUE` across `UNAVAILABLE`.

#### Dependencies

- Formula dependencies: F-001 through F-005 and F-013 where monitoring applies.
- Policy dependency: N-008.
- Factual data dependency: Market Data API facts.

#### Used by

- Market Handoff.
- F-013 monitoring.
- Position Rules.

#### Important boundaries

S-002 is Set-owned. It does not place orders, manage capital, or approve Position construction.

#### Technical traceability

Primary: `docs/trading-methodology/methodology/SET.md`; `docs/FORMULA_METRICS_CATALOG.md` row S-002.

### S-003 - Position Validation Outcome and Rejection Reason

#### Classification

| Field | Value |
|---|---|
| ID | S-003 |
| Owner | Position Rules |
| Type | STATE_CLASSIFICATION_RULE |
| Family | EXECUTION |
| Canonical status | APPROVED_POLICY |
| Canonical source | `docs/trading-methodology/methodology/POSITION_RULES.md` |

#### What it is

S-003 classifies Position validation outcomes and rejection reasons.

#### What it means

It records whether Position approved, rejected, constructed, failed construction, or marked a dependency/gate unavailable, with reason codes.

#### Why it exists

It makes Position decisions auditable and prevents silent repair or fallback when required inputs fail.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Market Handoff | Frozen opportunity | Set | IDs and facts |
| Position config | Pinned rules/config | Position | Versions/digest |
| Formula results | Entry/Stop/TP/size/economics | F-006 through F-012 | Pass/fail/unavailable |
| Grant | Capital and Limits | Portfolio | Grant IDs/amounts |

#### Data source

Set Market Handoff, Portfolio grant, pinned Position configuration, and Position formula outputs.

#### Formula or rule

Position returns explicit state variants and reasons such as APPROVE/REJECT, CONSTRUCTED/FAILED, PASS/FAIL/UNAVAILABLE/NOT_APPLICABLE gate results, and certified dependency reasons.

#### Calculation / evaluation steps

1. Validate handoff/configuration identity.
2. Evaluate initial opportunity stage.
3. If approved, await matching Portfolio grant.
4. Evaluate construction formulas and gates.
5. Classify each failure with certified reason precedence.
6. Publish only successful immutable Order Spec after successful construction.

#### Output

Position decision/construction state and rejection/unavailable reason codes.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable/rejected for missing handoff, config, grant, formula dependency, venue facts, or invalid identity/provenance. Do not guess missing inputs, reuse old results for another cycle, or repair by changing prices/capital.

#### Dependencies

- Formula dependencies: F-005 through F-012.
- Portfolio dependency: F-014 grant.
- Policy dependency: N-003 for spec digest.

#### Used by

- Portfolio grant/hold flow.
- Order Spec creation.
- Operator diagnostics.

#### Important boundaries

Position has no direct API flow and does not manage reservations or cooldown. It cannot submit orders without Lifecycle and Portfolio authorization.

#### Technical traceability

Primary: `docs/trading-methodology/methodology/POSITION_RULES.md`; `docs/FORMULA_METRICS_CATALOG.md` row S-003.

### S-004 - Order Lifecycle Closed-State Predicate

#### Classification

| Field | Value |
|---|---|
| ID | S-004 |
| Owner | Order Lifecycle |
| Type | STATE_CLASSIFICATION_RULE |
| Family | EXECUTION |
| Canonical status | CERTIFIED |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/S-004_FINAL_SPECIFICATION.md` |

#### What it is

S-004 is the certified closed-state and release-eligibility predicate for a logical tranche.

#### What it means

The order lifecycle is CLOSED only when all six required predicates are authoritatively true. Zero exposure alone is insufficient.

#### Why it exists

It prevents premature capital/slot release and ensures financial finality, child-order resolution, and execution authority resolution are complete.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Logical exposure state | Whether exposure is zero | Lifecycle/API facts | Boolean proof |
| Entry remainder state | Whether entry remainder terminal | Lifecycle | State proof |
| Protective/exit child states | Whether children terminal/disabled | Lifecycle | State proof |
| Close intent state | Whether active close intent resolved | Lifecycle | State proof |
| Financial finality | FINAL result established | A-002 / Lifecycle | Result/evidence |
| Execution authority state | No unresolved competing authority | Lifecycle | State proof |

#### Data source

Lifecycle state, native/order facts, financial accounting evidence, and durable proof vector.

#### Formula or rule

```text
CLOSED =
  logical_exposure_is_zero
  AND entry_remainder_terminal
  AND all_tranche_owned_protective_or_exit_children_terminal_or_disabled
  AND active_close_intent_fully_resolved
  AND financial_finality_established
  AND no_unresolved_competing_execution_authority
```

#### Calculation / evaluation steps

1. Evaluate each of the six predicates against durable proof.
2. Treat false, unknown, missing, or contradictory evidence as not closed.
3. If all are true, atomically commit FINAL financial result, resolved close intent, lifecycle state `CLOSED`, terminal timestamps, and Order Event outbox.
4. Otherwise remain `CLOSE_PENDING` or `RECONCILING` and retain commitment/slot.

#### Output

`CLOSED` true/false state and release eligibility.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Missing, contradictory, partial, unknown, or unresolved evidence prevents CLOSED. No timeout, manual escalation, cached boolean, zero physical quantity, or display-rounded accounting value substitutes for finality.

#### Dependencies

- Formula dependency: A-002.
- Formula dependency: A-004.
- Formula dependency: A-009 as accounting-day consumer.
- Approved policy dependencies: A-005, A-006, N-007.
- Documentation dependency: SYSTEM_PROTOCOLS P5-P13/P15.

#### Used by

- Portfolio capital/slot release.
- A-009 final result posting.
- Lifecycle terminal state.

#### Important boundaries

S-004 is not a numerical indicator. API supplies facts but does not classify CLOSED. Portfolio cannot release capital solely from zero exposure.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/S-004_FINAL_SPECIFICATION.md`. Supporting: `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`; `docs/trading-methodology/SYSTEM_PROTOCOLS.md`.

### S-005 - Market Regime Diagnostic Classifier

#### Classification

| Field | Value |
|---|---|
| ID | S-005 |
| Owner | Research |
| Type | STATE_CLASSIFICATION_RULE |
| Family | RESEARCH_PERFORMANCE |
| Canonical status | RESEARCH_ONLY |
| Canonical source | `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/S-005_FINAL_SPECIFICATION.md` |

#### What it is

S-005 is a research/demo diagnostic market-regime classifier candidate.

#### What it means

It labels a research/demo candle window as uptrend, downtrend, strong trend, or sideways under the candidate rule. It is explicitly not approved as a canonical live trading input.

#### Why it exists

It supports research grouping and diagnostics without entering active trading decisions.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| `symbol` | Candidate implementation symbol | Research/demo data | Current candidate BTCUSDT |
| `category` | Product category | Research/demo data | Current candidate linear |
| `timeframe` | Candle timeframe | Research/demo data | 1m |
| `candles` | Completed candles | Research/demo data | At least 30 contiguous 1m candles |
| Close prices | Positive close values | Research/demo data | Price decimals |

#### Data source

Research/demo market data. The current implementation is non-authoritative evidence of candidate behavior only.

#### Formula or rule

Non-normative candidate:

```text
window_return_pct = 100 * (latest_close - first_close) / first_close
avg_abs_step_return_pct = mean(abs(step_return_pct over 29 steps))
normalized_trend = 0 if avg_abs_step_return_pct == 0 else window_return_pct / avg_abs_step_return_pct
directional_persistence = (up_steps - down_steps) / 29
```

Candidate labels use thresholds from the final diagnostic-only specification. This rule is not promoted to canonical product truth.

#### Calculation / evaluation steps

1. Use only research/demo data.
2. Require at least 30 contiguous completed 1m candles and positive closes.
3. Compute candidate return, average absolute step return, normalized trend, and directional persistence.
4. Assign candidate label by ordered threshold rules.
5. Store/report as research/demo diagnostic only.

#### Output

Research/demo diagnostic regime label.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable for missing candles, noncontiguous data, nonpositive closes, unsupported live/canonical use, or missing research boundary. Do not infer labels into live Set/Position decisions.

#### Dependencies

- Research dependency: M-008.
- Architecture dependency: S-006.
- Current implementation reference: non-normative only.

#### Used by

- M-008 research grouping.
- M-006 regime diversity warning.

#### Important boundaries

S-005 must not affect certified F-005 direction, Set matching, Position approval, Portfolio capacity, Lifecycle execution, or live trading decisions.

#### Technical traceability

Primary: `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/S-005_FINAL_SPECIFICATION.md`. Implementation cross-check only: `src/triggertrade/market_data/regime.py`.

### S-006 - Research / Demo / Live Runtime Path Classification

#### Classification

| Field | Value |
|---|---|
| ID | S-006 |
| Owner | Cross-System |
| Type | NOT_A_FORMULA |
| Family | OTHER:RUNTIME_BOUNDARY |
| Canonical status | ARCHITECTURE_RULE |
| Canonical source | `docs/BACKEND_TARGET_MODEL.md` sections 13 and 17 |

#### What it is

S-006 classifies runtime paths as research, backtest, demo/paper, or live and enforces boundary separation.

#### What it means

It determines which runtime path may use which adapters, side effects, and persistence boundaries. It is an architecture/runtime classification rule, not a numerical formula.

#### Why it exists

It keeps research/backtest/demo isolated from live execution and prevents LLMs, simulations, or research assumptions from entering live trading decisions.

#### Inputs

| Input | Meaning | Owner/source | Unit or representation |
|---|---|---|---|
| Runtime mode/config | Declared environment mode | Runtime configuration | Enum/string |
| Adapter profile | Paper/demo/live adapter binding | Runtime/service setup | Adapter identity |
| Research run identity | Pinned research/backtest context | Research service | IDs/digests |
| Live enablement evidence | Explicit live enablement when applicable | Runtime config/ops | Boolean/config evidence |

#### Data source

Runtime configuration, service setup, adapter bindings, and research run records.

#### Formula or rule

No numerical formula. This is a runtime path-classification rule.

Research/backtest/demo must remain isolated from live side effects. Live mode must be explicitly enabled and cannot be the development default.

#### Calculation / evaluation steps

1. Read runtime mode and adapter binding from configuration.
2. Classify path as research/backtest, demo/paper, or live.
3. Enforce adapter and side-effect boundaries for that path.
4. Require pinned research inputs for research/backtest runs.
5. Require explicit live enablement for live trading.
6. Fail closed on ambiguous or conflicting runtime classification.

#### Output

Runtime path classification and allowed side-effect boundary.

#### Worked example

No canonical worked example specified.

#### Unavailable / invalid behavior

Unavailable/fail-closed when runtime mode, adapter binding, research identity, or live enablement is missing, ambiguous, contradictory, or unsafe. Do not silently fall back from live to research assumptions or from research to live adapters.

#### Dependencies

- Architecture dependency: Backend target model research/backtest boundary.
- Runtime configuration dependency: mode and adapter setup.

#### Used by

- Research/backtest worker.
- Demo/paper runtime.
- Live runtime guardrails.
- M-series research metrics.

#### Important boundaries

S-006 is not a formula and produces no trading signal. It does not affect live trading decisions except by enforcing allowed runtime path and side-effect boundaries.

#### Technical traceability

Primary: `docs/BACKEND_TARGET_MODEL.md` sections 13 and 17. Supporting: `docs/FORMULA_METRICS_CATALOG.md` row S-006. Implementation cross-check: `src/triggertrade/services/runtime.py`.
