# Research V2 Capability Map

## 1. Scope and Source of Truth

This document inventories the current backend capability surface for TriggerTrade hypothesis research. Current runtime code is authoritative. Repository docs and manifests are used only when they match implementation, or are explicitly marked as `DOC_IMPLEMENTATION_MISMATCH`.

This is not a strategy redesign, recommendation set, or replay result. It maps what can currently be expressed by code/config/contracts/tests without running a full replay/backtest.

Primary evidence:

- `src/triggertrade/research_v2.py`
- `src/triggertrade/research_v2_execution.py`
- `tools/research_v2/run_7d_screen.py`
- `src/triggertrade/set_engine/formulas.py`
- `src/triggertrade/set_engine/handler.py`
- `src/triggertrade/triggers/declarative_metric_predicate.py`
- `src/triggertrade/rules/trading.py`
- `docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json`
- `docs/research-v2/jobs/INITIAL_7D_JOBS.json`
- focused unit evidence in `tests/unit/test_research_v2_set_contract.py`, `tests/unit/test_research_v2_screen_runner.py`, and `tests/unit/test_trading_rules_registry.py`

## 2. Executive Summary

The richest currently implemented research surface is Research V2 J0-J7: fixed job families over a three-symbol universe, completed OHLCV/turnover-derived features, four V2 signal kernels, two stop families, fixed 2R take profit, risk-based sizing, portfolio caps, daily-loss/cooldown gates, funding/mark accounting, and strict order-spec construction.

The engine can vary existing job profiles and already implemented trading-rule fields. It can also combine existing generic Set direction mechanisms and declarative metric predicates when upstream metric values already exist.

The engine cannot currently express arbitrary new indicators such as RSI/MACD, order-book imbalance, dynamic allocation, arbitrary trailing stops, strategic partial closes, market-entry fallback, or LLM-driven decision logic without code changes.

Frozen areas include exchange adapter isolation, mandatory risk before execution, paper/demo safety defaults, precision validation, duplicate submission prevention, immutable Set result identity, order-spec invariants, factual accounting, funding/MTM evidence requirements, no chase/reprice/market fallback in V2, and fail-closed behavior under critical uncertainty.

Two implementation mismatches matter for researchers:

- `DOC_IMPLEMENTATION_MISMATCH`: some research job JSON rows still say `SPECIFIED_NOT_IMPLEMENTED`, but current code loads J0-J7 through `load_research_v2_jobs`, constructs V2 profiles, and the screen runner has a default executor path. Actual behavior is implemented for J0-J7 capability mapping, not merely specified. Source: `docs/research-v2/jobs/INITIAL_7D_JOBS.json`; `src/triggertrade/research_v2.py:306`, `tools/research_v2/run_7d_screen.py:1296`, `tools/research_v2/run_7d_screen.py:1382`.
- `DOC_IMPLEMENTATION_MISMATCH`: the metrics-library F-006/F-007 narrative describes structural stop constants such as `BUFFER_ATR_MULTIPLIER = 0.20` and `MAX_DISTANCE_ATR = 2.00`, while current V2 G0 implementation/profile uses buffer `0.10`, minimum `0.5*ATR15` or `0.0025*entry`, and maximum `min(1.5*ATR15, 0.0125*entry)`. Actual V2 behavior is the code/profile values. Source: `src/triggertrade/research_v2.py:653`, `src/triggertrade/research_v2.py:671`, `src/triggertrade/research_v2.py:674`, `docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json`.

## 3. Market Inputs

| Input | Internal Name | Timeframe/Window | Value Type | Availability | Research-usable | Source |
| --- | --- | --- | --- | --- | --- | --- |
| Completed candle OHLCV | `HistoricalCandle`, `AggregatedBar` | 1m source, aggregate 5m/15m | Decimal OHLCV plus timestamps | Only completed candles are used; incomplete/missing bars make features unavailable | YES | `src/triggertrade/backtest/models.py`; `src/triggertrade/research_v2.py:61`, `src/triggertrade/research_v2.py:473` |
| Turnover | `AggregatedBar.turnover` | 5m/15m aggregation | Decimal | Summed from completed source candles | YES | `src/triggertrade/research_v2.py:71`, `src/triggertrade/research_v2.py:514` |
| Last traded/reference price | `set_match_reference_price`, `reference_price_source=LAST_TRADED_PRICE` | Set match snapshot | Decimal string | Required in `HandoffFacts`; must be positive in handoff | YES | `src/triggertrade/set_engine/handler.py:142`, `src/triggertrade/set_engine/handler.py:534` |
| Tick size | `tick_size`, `VenueConstraints.tick_size` | Instrument metadata | Decimal | Required positive; used for rounding | YES | `src/triggertrade/set_engine/handler.py:148`, `src/triggertrade/research_v2_execution.py:31` |
| Quantity step/min qty/min notional/max qty | `VenueConstraints` | Instrument metadata | Decimal | Enforced during V2 sizing/order construction | YES | `src/triggertrade/research_v2_execution.py:31`, `src/triggertrade/research_v2_execution.py:350` |
| Raw trades | `raw_trades_for_causal_fills`, `RawTradePoint` | Intrabar fill simulation | Decimal price/qty/time | Required input; missing/invalid evidence fails replay path | YES for fill simulation, not signals | `src/triggertrade/research_v2.py:889`, `tools/research_v2/run_7d_screen.py` `RawTradePoint` |
| Funding facts | `historical_funding_facts` | Funding boundaries while position held | Decimal rate/mark/cashflow | Required; missing mark/funding facts fail closed in tests | YES for accounting, not signal formation | `src/triggertrade/research_v2.py:891`; `tools/research_v2/run_7d_screen.py:2109`; `tests/unit/test_research_v2_screen_runner.py:1024` |
| Mark price facts | `historical_mark_facts_when_required`, `mark_price_1m` | Endpoint/open-position MTM and funding boundaries | Decimal | Required where MTM/funding needs marks; missing mark yields invalid/unavailable evidence | YES for accounting | `src/triggertrade/research_v2.py:892`; `tools/research_v2/run_7d_screen.py` `_equity_from_ledger_events` |
| Instrument metadata | `instrument_metadata`, `FuturesInstrument`, `VenueConstraints` | Per symbol | Decimals and limits | Required for tick/qty/notional/leverage constraints | YES | `src/triggertrade/research_v2.py:893`; `src/triggertrade/instruments/catalog.py` |
| BTC companion context | `context_only=["BTCUSDT"]`, `btc_filter=DISABLED` in J4/J7 | Context data requirement only in current V2 profile | Symbol context | Loaded as context requirement, but current continuation signal has BTC filter disabled | LIMITED | `docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json`; `src/triggertrade/research_v2.py:957` |
| Accounting day time | `ACCOUNTING_TIMEZONE="Asia/Jerusalem"` | Local accounting day | RFC3339/timezone | Used for accounting-day windows and daily-loss base | YES for portfolio accounting | `src/triggertrade/portfolio_accounting_day.py:16`, `src/triggertrade/portfolio_accounting_day.py:208` |

## 4. Derived Metrics / Features

| Metric | Internal Ref | Formula/Implementation | Window | Type | Explicit Range | Research-usable | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ATR15 | `ATR15` | Wilder ATR(14) on completed 15m bars | 15m, period 14 | Decimal price distance | `EXPLICIT_RANGE: NONE_FOUND`; unavailable if insufficient bars | YES | `src/triggertrade/research_v2.py:521`, `src/triggertrade/research_v2.py:542` |
| Return pct points | `return5_pct_points`, `return15_pct_points` | `(latest.close/reference.close - 1) * 100` | 5m or 15m | Decimal percentage points | `EXPLICIT_RANGE: NONE_FOUND`; denominator requires reference close through candle data | YES | `src/triggertrade/research_v2.py:551`; tests `tests/unit/test_research_v2_set_contract.py` |
| RVOL5 | `RVOL5` | Latest completed 5m turnover / mean preceding 20 nonoverlapping 5m turnover bars | 5m with 20-bar baseline | Decimal ratio | `EXPLICIT_RANGE: NONE_FOUND`; unavailable on insufficient bars/zero baseline | YES | `src/triggertrade/research_v2.py:562`, `docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json` |
| Turnover acceleration | `turnover_acceleration` | Latest completed 5m turnover / immediately preceding completed 5m turnover | 5m | Decimal ratio | `EXPLICIT_RANGE: NONE_FOUND`; unavailable on zero previous turnover | YES | `src/triggertrade/research_v2.py:574` |
| EMA20 15m | `EMA20_15m` | EMA over completed 15m bars | 15m, period 20 | Decimal price | `EXPLICIT_RANGE: NONE_FOUND` | YES | `src/triggertrade/research_v2.py:585` |
| EMA50 15m | `EMA50_15m` | EMA over completed 15m bars | 15m, period 50 | Decimal price | `EXPLICIT_RANGE: NONE_FOUND` | YES | `src/triggertrade/research_v2.py:585` |
| Confirmed swing5 references | `swing_long`, `swing_short`, `SwingReference` | 2 bars left/right; available after second right bar close | 5m | Price reference | `EXPLICIT_RANGE: price > 0 by usage`; no explicit age bound except G0 evidence/profile | YES for G0 | `src/triggertrade/research_v2.py:598`, `src/triggertrade/research_v2.py:615` |
| Compression ATR median | `compression_atr_median96` | Median of preceding 96 ATR15 values | 96 ATR observations | Decimal | `EXPLICIT_RANGE: NONE_FOUND`; requires 96 values | YES for J5 | `src/triggertrade/research_v2.py:825`, `src/triggertrade/research_v2.py:836` |
| Prior range high/low | `prior_12_range` | Prior range high/low used by compression breakout | Current runner timeline | Decimal pair | `EXPLICIT_RANGE: NONE_FOUND` | YES for J5 | `tools/research_v2/run_7d_screen.py` `FeatureTimeline` |
| F-001 price displacement | `f001_price_displacement`, `move_pct_work`, `sign_evidence` | Signed close-to-close 1m percent displacement, thresholded by `theta_move_pct` | 1m | Decimal pct and enum | `theta_move_pct > 0`; inclusive `abs(move) >= theta` | Existing Set kernel | `src/triggertrade/set_engine/formulas.py:89`, `src/triggertrade/set_engine/formulas.py:198` |
| F-002 participation | `f002_participation`, `relative_volume`, `rank_percent` | Current 1m volume vs median/rank of exactly 60 prior 1m candles | 1m + 60 history | Decimal ratio/percent | Hard-coded trigger: relative volume >= 2 and rank_count >= 54 | Existing Set kernel | `src/triggertrade/set_engine/formulas.py:103`, `src/triggertrade/set_engine/formulas.py:227` |
| F-003 ATR / ATR pct | `atr_update`, `atr_wire`, `atr_pct_wire` | Wilder ATR seed/update for 5m or 15m, Q36/Q18 policy | 5m or 15m, period 14 | Decimal strings | Timeframe enum `5m`, `15m`; requires 14 seed candles | Existing Set kernel | `src/triggertrade/set_engine/formulas.py:119`, `src/triggertrade/set_engine/formulas.py:264` |
| Directional efficiency | `directional_efficiency` | `abs(last-first)/sum(abs(delta))` over 9 closes | N=8 transitions | Decimal 0..1 by formula | Requires exactly 9 closes | Existing Set kernel | `src/triggertrade/set_engine/formulas.py:361` |
| Swing sequence state | `SwingSequenceState` | Compares last two swing highs/lows with tick | Any validated candle timeframe | Enum | `BULLISH`, `BEARISH`, `AMBIGUOUS`, `UNAVAILABLE` | Existing Set kernel | `src/triggertrade/set_engine/formulas.py:398` |
| F-005 classifier | `classify_direction`, `DIRECTION_SCORE` | Weighted structure, momentum, relative, flow, BTC context with gates/vetoes | Mixed Set inputs | Direction enum | Hard gates: DE >= 0.30, TOD >= 0.70, ATR pct percentile 15..97; score >= 0.35 LONG, <= -0.35 SHORT | Existing Set kernel, not arbitrary V2 J3-J7 | `src/triggertrade/set_engine/formulas.py:416` |

## 5. Triggers

| Trigger ID | Version | Family | Metric | Operator | Threshold/Params | Allowed Range | Direction Effect | Research-usable | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `TRG-001` | config default `0.1.0`; selectable `0.2.0` | percentage price move | current/previous price | `price_change_pct <= threshold_pct` | env/config `TRIGGERTRADE_TRG_001_THRESHOLD_PCT`, default `-1.0` | `EXPLICIT_RANGE: NONE_FOUND`; previous price must be >0 | `BUY_CANDIDATE` when true | Legacy/demo, not V2 J3-J7 signal | `src/triggertrade/triggers/percentage_price_move.py`; `src/triggertrade/config/settings.py` |
| `TRG-002` | code default `0.1.0`; strategy checks `0.2.0` membership | robust volume confirmation | volume, median, percentile | relative >= threshold AND percentile >= threshold | lookback 60, relative threshold 2.0, percentile threshold 90, 1m, stale 120s | `EXPLICIT_RANGE: NONE_FOUND`; exactly enough prior candles; median >0 | `CONFIRMED`/`NOT_CONFIRMED`; no side direction | Legacy/demo | `src/triggertrade/triggers/volume_confirmation.py`; `src/triggertrade/strategies/futures_directional.py` |
| declarative metric predicate | schema `research-v1-declarative-metric-predicate@1` | generic metric predicate | supplied `metric_ref` | `EQ`, `GTE`, `LTE`, `GT`, `LT` | string/Decimal `threshold`; output states list | operators enum; output states enum `TRUE`, `FALSE`, `ZERO`, `UNAVAILABLE`, `LONG`, `SHORT`, `NONE`; no numeric min/max | `LONG` output maps to `BUY_CANDIDATE`; other true maps to `CONFIRMED` | CONFIG_ONLY only when metric exists upstream | `src/triggertrade/triggers/declarative_metric_predicate.py` |
| RET5 OR RET15 | `V2-SIGNAL-RET5-RET15-OR-V1` | V2 signal | return5/return15 pct points | `>=` long, `<= -threshold` short, OR | return5 0.30, return15 0.50 | Defaults explicit; no external min/max | LONG/SHORT/NONE | YES, J3 and base for J4/J7 | `src/triggertrade/research_v2.py:777`; `src/triggertrade/research_v2.py:950` |
| Momentum continuation | `V2-SIGNAL-CONTINUATION-V1` | V2 signal | base RET_OR, EMA20/EMA50, return15, RVOL5 | base pass AND trend/return sign AND RVOL minimum | RVOL5 >= 1.2; EMA20>EMA50 for LONG, EMA20<EMA50 for SHORT | Hard-coded threshold, no range | Preserves base direction if filters pass | YES, J4/J7 | `src/triggertrade/research_v2.py:806`; `src/triggertrade/research_v2.py:952` |
| Compression breakout | `V2-SIGNAL-COMPRESSION-BREAKOUT-V1` | V2 signal | ATR15/median96, close vs prior range, RVOL5, turnover acceleration | ratio <= max, RVOL/turnover thresholds, breakout buffer | ATR/median <= 0.80; RVOL5 >= 1.5; turnover acceleration >= 1.2; buffer 0.10*ATR15; validity 15m | Requires at least 96 ATR history; no external range | LONG above range+buffer; SHORT below range-buffer | YES, J5 | `src/triggertrade/research_v2.py:825`; `src/triggertrade/research_v2.py:960` |
| Exhaustion reversal | `V2-SIGNAL-EXHAUSTION-REVERSAL-V1` | V2 signal | return15, latest close, 15m high/low, ATR15, last two closes, turnover acceleration | impulse and reversal confirmation | abs return15 >= 1.0; turnover acceleration <= 1.0; 0.5*ATR reversal distance; validity 15m | Needs two closes; no external range | Positive impulse can produce SHORT; negative impulse can produce LONG | YES, J6 | `src/triggertrade/research_v2.py:852`; `src/triggertrade/research_v2.py:969` |

## 6. Set / Strategy Formation Controls

| Control | Exact Field/Mechanism | Type | Allowed Values/Range | Default | Classification | Source |
| --- | --- | --- | --- | --- | --- | --- |
| V2 job identity | `ResearchV2JobConfig.job_id` | String | Implemented branches J0-J7; other `job_id` raises error in `_signal_profile_for_job` | loaded from `INITIAL_7D_JOBS.json` | CONFIG_ONLY for J0-J7 selection | `src/triggertrade/research_v2.py:314`, `src/triggertrade/research_v2.py:946` |
| V2 signal family | `runtime_profile["signal"]["family"]` | String | `LEGACY_SET`, `RET5_OR_RET15`, `MOMENTUM_CONTINUATION`, `COMPRESSION_BREAKOUT`, `EXHAUSTION_REVERSAL` | job-specific | CONFIG_ONLY among existing jobs; new family requires code | `src/triggertrade/research_v2.py:916`, `src/triggertrade/research_v2.py:946` |
| Set result direction scope | `DirectionResolutionScope` | Enum | `F005_GOVERNED`, `GENERIC_FIXED`, `GENERIC_MATCHED_BRANCH` | V2 uses `GENERIC_FIXED` | EXISTING_ENGINE_COMBINATION | `src/triggertrade/set_engine/handler.py:26`, `src/triggertrade/research_v2.py:997` |
| Fixed direction binding | `GenericFixedDirectionBinding.fixed_direction` | Enum | `LONG`, `SHORT`; `NONE` rejected | V2 signal direction | EXISTING_ENGINE_COMBINATION | `src/triggertrade/set_engine/handler.py:50`, `src/triggertrade/set_engine/handler.py:713` |
| Generic matched branches | `GenericBranchEvidence` plus `DeclaredConflictRule` | Tuple/config mechanism | Branch directions must be LONG/SHORT; conflict rule required for mixed directions | None in V2 J3-J7 | EXISTING_ENGINE_COMBINATION | `src/triggertrade/set_engine/handler.py:38`, `src/triggertrade/set_engine/handler.py:423` |
| F-005 governed classifier | `classifier_inputs`, `classify_direction` | Structured inputs | Direction `LONG`, `SHORT`, `NONE`; unavailable on missing inputs | Not used by generic fixed V2 signals | EXISTING_ENGINE_COMBINATION | `src/triggertrade/set_engine/handler.py:391`; `src/triggertrade/set_engine/formulas.py:416` |
| Set family in handoff context | `HandoffContext.set_family` | Enum | `TREND_CONTINUATION`, `RANGE`, `BREAKOUT_RECLAIM`, `GENERIC` | V2 generic contexts | EXISTING_ENGINE_COMBINATION | `src/triggertrade/set_engine/handler.py:69` |
| Thesis reference policy | `HandoffContext.thesis_reference_policy` | Enum | `REQUIRED`, `PREFERRED`, `NONE` | V2 mostly generic/no thesis | EXISTING_ENGINE_COMBINATION | `src/triggertrade/set_engine/handler.py:70` |
| Trigger set status/lane | `Lane`, `RuleStatus`, `TriggerSetStatus` | Enums | `ACTIVE`, `TEST`; `DRAFT`, `TESTING`, `ACTIVE`, `ARCHIVE` | runtime registry | CONFIG_ONLY via registry lifecycle | `src/triggertrade/trigger_sets/contracts.py` |
| Current selectable trigger versions | `CURRENT_SELECTABLE_TRIGGER_VERSIONS` | Frozen set | only `("TRG-001", "0.2.0")` | hard-coded | CODE_CHANGE_REQUIRED to broaden selectable versions | `src/triggertrade/trigger_sets/contracts.py` |
| Current selectable trigger set | `CURRENT_SELECTABLE_TRIGGER_SETS` | Frozen set | only `("triggertrade-futures-core", "v1")` | hard-coded | CODE_CHANGE_REQUIRED to broaden selectable sets | `src/triggertrade/trigger_sets/contracts.py` |

## 7. Position Rules

| Rule | Exact Field | Type | Allowed Values/Range | Default | Frozen? | Classification | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Direction mode | `TradingRulesVersionDraft.direction_mode` | Enum | `LONG_SHORT`, `LONG_ONLY`, `SHORT_ONLY` | `LONG_SHORT` | No | CONFIG_ONLY | `src/triggertrade/rules/trading.py` |
| Position size percent | `position_size_pct` | Decimal | `EXPLICIT_RANGE: >0 and <=1` | futures runtime `0.10` | No | CONFIG_ONLY for trading rules; not V2 risk profile | `src/triggertrade/rules/trading.py:201`; `src/triggertrade/config/settings.py` |
| V2 entry order type | `order_spec.entry.order_type` | String | Hard-coded `LIMIT` | `LIMIT` | Yes | FROZEN_INVARIANT | `src/triggertrade/research_v2_execution.py:224` |
| V2 post-only | `order_spec.entry.post_only` | Bool | Hard-coded `True` | `True` | Yes | FROZEN_INVARIANT | `src/triggertrade/research_v2_execution.py:225` |
| V2 entry pullback | `_entry_price`, common profile `pullback_ATR15` | Decimal multiplier | Hard-coded/profile `0.10*ATR15`; no min/max beyond positive ATR/tick | `0.10` | No, but not arbitrary without profile/code wiring | CONFIG_ONLY for common profile value currently consumed as profile evidence; code uses hard-coded 0.10 in bridge | `src/triggertrade/research_v2_execution.py:418`; `docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json` |
| V2 entry TTL | `entry_profile["TTL_minutes"]`, `_expires_at` | Integer or null | `None` -> GTC; otherwise `int(ttl_minutes)`; no explicit min/max in bridge | 15 for J2-J7; J0 null; J1 15 in lower-case key path | CONFIG_ONLY | `src/triggertrade/research_v2_execution.py:206`, `src/triggertrade/research_v2_execution.py:500` |
| Chase/reprice/market fallback | `entry.validity.chase/reprice/market_fallback` | Bool | Must be false or validation fails | false | Yes | FROZEN_INVARIANT | `src/triggertrade/research_v2_execution.py:232`, `src/triggertrade/research_v2_execution.py:305` |
| Stop family G0 | `stop_profile["type"]="HYBRID_STRUCTURAL"` | String/profile | Uses structural reference plus `buffer_ATR15`, floors/ceilings from profile; actual stop must be protective | common `stop_G0` | No | CONFIG_ONLY among existing profile fields; new stop type code change | `src/triggertrade/research_v2_execution.py:423`; `docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json` |
| Stop family G1 | `stop_profile["type"]="ATR_ONLY"` | String/profile | `distance_ATR15`, `distance_fraction_floor`, `distance_fraction_ceiling` | J7 only | No | CONFIG_ONLY by choosing J7/G1; arbitrary families require code | `src/triggertrade/research_v2_execution.py:432`; `docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json` |
| Fixed stop-loss pct | `TradingRulesVersionDraft.stop_loss_pct` | Decimal or null | Fixed mode requires positive; dynamic mode optional positive | runtime `0.0025` | No | CONFIG_ONLY for trading rules | `src/triggertrade/rules/trading.py:211`; `tests/unit/test_trading_rules_registry.py:142` |
| Stop-loss mode | `stop_loss_mode` | Enum | `FIXED`, `DYNAMIC` | `FIXED` | No | CONFIG_ONLY | `src/triggertrade/rules/trading.py` |
| V2 take profit | `take_profit.mode=R_MULTIPLE`, `r_multiple=2` | Fixed mode | Hard-coded 2R, market exit, last price, full position | 2R | Mostly frozen in V2 bridge | FROZEN_INVARIANT unless code/profile changed | `src/triggertrade/research_v2_execution.py:239`, `src/triggertrade/research_v2_execution.py:461` |
| Trading-rule take profit | `take_profit_mode`, `fixed_take_profit_pct`, `minimum_take_profit_pct` | Enum/Decimals | modes `FIXED`, `DYNAMIC`; fixed pct >0 in FIXED; minimum pct positive when set | runtime `0.01` | No | CONFIG_ONLY outside V2 fixed 2R bridge | `src/triggertrade/rules/trading.py:201` |
| Minimum risk reward | `minimum_risk_reward_enabled`, `minimum_risk_reward` | Bool/Decimal | enabled requires >0; disabled retained value >=0 | true, `1.5` | No | CONFIG_ONLY | `src/triggertrade/rules/trading.py:219` |
| Minimum net edge | `minimum_net_edge_enabled`, `minimum_net_edge_pct` | Bool/Decimal | enabled requires nonnegative pct | true, runtime `0.01` | No | CONFIG_ONLY | `src/triggertrade/rules/trading.py:223` |
| Leverage | `TradingRulesVersionDraft.leverage`; V2 job `leverage` | Decimal | trading rules require >0; futures risk also constrains to instrument min/max/step and max configured leverage | V2 `1` | No | CONFIG_ONLY for existing values; exchange bounds runtime-specific | `src/triggertrade/rules/trading.py:225`; `src/triggertrade/execution/futures.py:166` |
| Minimum tranche capital | `minimum_tranche_capital`; V2 `minimum_tranche_usdt` | Decimal | trading rules `>=0` if set; V2 rejects below profile minimum | V2 `25` | No | CONFIG_ONLY | `src/triggertrade/rules/trading.py:236`; `src/triggertrade/research_v2_execution.py:359` |
| Cooldown | `cooldown_minutes`; V2 profile `cooldown_minutes` | Integer | trading rules `>=0` if set; V2 common profile 15 | V2 `15` | No | CONFIG_ONLY | `src/triggertrade/rules/trading.py:238`; `tools/research_v2/run_7d_screen.py:1504` |
| Strategic partial close | `take_profit.scope=FULL_POSITION`; no partial strategy field in V2 order spec | Fixed string | `FULL_POSITION` | full position | Yes | CODE_CHANGE_REQUIRED | `src/triggertrade/research_v2_execution.py:244`, `src/triggertrade/research_v2_execution.py:251` |

## 8. Portfolio Rules

| Rule | Exact Field | Type | Allowed Values/Range | Default | Frozen? | Classification | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Capital | common profile `capital_usdt`; V2 grant `account_capital` | Decimal | V2 sizing raises if capital <=0 | `1000` | No | CONFIG_ONLY | `docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json`; `src/triggertrade/research_v2.py:752` |
| Nominal margin fraction | `nominal_margin_fraction` | Decimal | `EXPLICIT_RANGE: NONE_FOUND`; participates in min sizing formula | `0.25` | No | CONFIG_ONLY | `src/triggertrade/research_v2_execution.py:340`; common profile |
| Total margin cap | `total_margin_fraction_max` | Decimal | `EXPLICIT_RANGE: NONE_FOUND`; block when remaining <=0 | `0.6` | No | CONFIG_ONLY | `src/triggertrade/research_v2_execution.py:101` |
| Per-coin margin cap | `per_coin_margin_fraction_cap` | Decimal | `EXPLICIT_RANGE: NONE_FOUND`; block when remaining <=0 | `0.33` | No | CONFIG_ONLY | `src/triggertrade/research_v2_execution.py:102` |
| Gross notional cap | `gross_notional_fraction_max` | Decimal | `EXPLICIT_RANGE: NONE_FOUND`; block when remaining <=0 | `1.8` | No | CONFIG_ONLY | `src/triggertrade/research_v2_execution.py:103` |
| Portfolio open/pending stop-risk cap | `portfolio_open_and_pending_stop_risk_fraction_max` | Decimal | `EXPLICIT_RANGE: NONE_FOUND`; block when remaining <=0 | `0.015` | No | CONFIG_ONLY | `src/triggertrade/research_v2_execution.py:104` |
| Per-trade risk cap | `risk_per_trade_fraction_max` | Decimal | `EXPLICIT_RANGE: NONE_FOUND`; post-rounding rechecked | `0.0075` | No | CONFIG_ONLY | `src/triggertrade/research_v2_execution.py:341`, `src/triggertrade/research_v2_execution.py:367` |
| Max open and pending orders | `max_open_and_pending_orders` | Integer | `EXPLICIT_RANGE: NONE_FOUND`; block at <=0 remaining | `3` | No | CONFIG_ONLY | `src/triggertrade/research_v2_execution.py:105` |
| Max positions per coin | `max_positions_per_coin` | Integer | V2 no explicit min; trading rules enabled value must >0 and <= max_open_positions | `1` | No | CONFIG_ONLY | `src/triggertrade/research_v2_execution.py:106`; `src/triggertrade/rules/trading.py:229` |
| Trading-rule max capital in positions | `max_capital_in_positions_pct` | Decimal | `>0 and <=1` | derived from runtime cap | No | CONFIG_ONLY | `src/triggertrade/rules/trading.py:225` |
| Coin allocation pct | `CoinRule.max_allocation_pct`, `PortfolioLimitConfiguration.coin_allocation_pct` | Decimal map | `>0 and <=1` for `CoinRule`; accounting config percent text `0..100` | none in initial BTC rule; V2 uses margin cap | No | CONFIG_ONLY outside V2 profile | `src/triggertrade/rules/trading.py:243`; `src/triggertrade/portfolio_accounting_day.py:174` |
| Daily loss guard | `daily_loss_limit_enabled`, `daily_loss_limit_pct`; V2 `daily_loss_fraction_max` | Bool/Decimal | enabled pct must >0 in trading rules; V2 common `0.0225` | disabled in initial trading rules; V2 profile `0.0225` | Guard mechanics frozen | CONFIG_ONLY threshold, FROZEN mechanics | `src/triggertrade/services/daily_loss.py`; `src/triggertrade/rules/trading.py:233`; `tools/research_v2/run_7d_screen.py:1443` |
| Job-isolated portfolio book | `_portfolio_book_key` | Function | Keyed by job/profile; no user range | per job | Yes for V2 replay economics | FROZEN_INVARIANT | `tools/research_v2/run_7d_screen.py:2254`; tests `tests/unit/test_research_v2_screen_runner.py:247` |
| Dynamic allocation | No implemented V2 allocation optimizer | N/A | N/A | N/A | N/A | CODE_CHANGE_REQUIRED | Absence from V2 sizing bridge; closest is fixed caps/min formula |

## 9. Coin / Universe Controls

| Control | Exact Field/Mechanism | Allowed Values/Range | Classification | Source |
| --- | --- | --- | --- | --- |
| V2 initial universe | common `symbols` and job `symbols` | `AVAXUSDT`, `SUIUSDT`, `PEPEUSDT` in current V2 profile/jobs | CONFIG_ONLY inside job/common files; adding unsupported data needs dataset/instrument evidence | `docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json`; `docs/research-v2/jobs/INITIAL_7D_JOBS.json` |
| Physical symbol mapping | `physical_symbol_for_research_v2`, `physical_binding` | `PEPEUSDT -> 1000PEPEUSDT`; default identity otherwise | CONFIG_ONLY for mapping file/profile | `src/triggertrade/research_v2.py:334`; common profile |
| Runtime watchlist | `TRIGGERTRADE_WATCHLIST`, `WatchlistItem` | comma-separated symbols, no explicit catalog validation in loader | CONFIG_ONLY for runtime, not V2 J0-J7 research universe | `src/triggertrade/config/settings.py:269` |
| Trading-rules coins | `CoinRule(symbol, enabled, max_allocation_pct)` | normalized `*USDT`, alnum base; at least one enabled; optional symbol validator | CONFIG_ONLY | `src/triggertrade/rules/trading.py:240`, `src/triggertrade/rules/trading.py:269` |
| Instrument catalog validation | optional `symbol_validator` in `TradingRulesService` | rejects enabled coin not valid in futures catalog when validator supplied | EXISTING_ENGINE_COMBINATION | `src/triggertrade/rules/trading.py:31`, `src/triggertrade/rules/trading.py:246` |
| Segment allocation from Research V1 docs | `docs/research-import/rules/RESEARCH_V1_RULES.json` | Documented allocations exist but are not current V2 engine controls | CODE_CHANGE_REQUIRED for V2 use | docs only; no V2 bridge consumption |

## 10. Time / Regime Controls

| Control | Existing Primitive | Parameters | Range | Classification | Source |
| --- | --- | --- | --- | --- |
| Research window | `window_start`, `window_end` | ISO start inclusive/end exclusive per job | No explicit min/max; dates from jobs | CONFIG_ONLY | `src/triggertrade/research_v2.py:226`; jobs JSON |
| Warmup | `warmup_days` | V2 data requirement | hard-coded `15` | CONFIG_ONLY in profile; code requirement hard-coded | `src/triggertrade/research_v2.py:885` |
| Evaluation cadence | common `features.evaluation_cadence_seconds` | seconds | profile `60`; runner evaluates completed timelines | CONFIG_ONLY if runner honors profile; no general scheduler knob proven | common profile; `tools/research_v2/run_7d_screen.py` |
| Accounting day | `ACCOUNTING_TIMEZONE` | Asia/Jerusalem | fixed string | FROZEN_INVARIANT | `src/triggertrade/portfolio_accounting_day.py:16` |
| Legacy market regime | `MarketRegimeContext.label` | `DOWNTREND`, `STRONG_DOWNTREND`, etc. | strategy only opens long in downtrend/strong downtrend reversal context | EXISTING_ENGINE_COMBINATION for demo strategy, not V2 signals | `src/triggertrade/strategies/futures_directional.py` |
| V2 volatility regime | ATR15 and ATR median compression | ATR15/median96 <= 0.80 for J5; ATR15 stop bounds | hard-coded/profile values | CONFIG_ONLY among existing job/profile values | `src/triggertrade/research_v2.py:836`; common profile |
| V2 trend regime | EMA20/EMA50 plus return15 sign | EMA20 >/< EMA50; return15 sign | hard-coded | CONFIG_ONLY by choosing J4/J7 | `src/triggertrade/research_v2.py:806` |
| V2 turnover regime | RVOL5 and turnover acceleration | J4/J7 RVOL >=1.2; J5 RVOL >=1.5 and turnover >=1.2; J6 turnover <=1.0 | hard-coded | CONFIG_ONLY by job family only | `src/triggertrade/research_v2.py:816`, `src/triggertrade/research_v2.py:840`, `src/triggertrade/research_v2.py:864` |
| BTC context in V2 | `btc_filter` | `DISABLED` in continuation profile | current supported value for V2 profile is disabled | CODE_CHANGE_REQUIRED for active BTC filter in V2 signal | `src/triggertrade/research_v2.py:957` |
| Day-of-week/session filter | No current V2 primitive found | N/A | N/A | CODE_CHANGE_REQUIRED | inspected V2/profile/trading-rule code |

## 11. Exit / Holding Controls

| Control | Exact Field/Mechanism | Allowed Values/Range | Frozen? | Classification | Source |
| --- | --- | --- | --- | --- |
| V2 take profit | `_tp_price`, `take_profit.r_multiple=2` | exactly 2R in current bridge; TP rounded away from entry | Yes | FROZEN_INVARIANT | `src/triggertrade/research_v2_execution.py:239`, `src/triggertrade/research_v2_execution.py:461` |
| V2 TP net floor | `net_TP_fraction_of_notional_min` | profile `0.003`; no explicit min/max | No | CONFIG_ONLY | `src/triggertrade/research_v2_execution.py:403`; common profile |
| V2 stop loss | `stop_profile.type` | `HYBRID_STRUCTURAL`, `ATR_ONLY` currently implemented | No | CONFIG_ONLY between existing stop profiles | `src/triggertrade/research_v2_execution.py:423` |
| Entry timeout | `TTL_minutes` and `research_v2_order_validity_status` | `GTC` when null; `TTL` when expires_at exists; expired zero fill cancels; partial/fill keeps protection | Mechanics frozen; value configurable | CONFIG_ONLY value, FROZEN mechanics | `src/triggertrade/research_v2_execution.py:310`; tests `tests/unit/test_research_v2_screen_runner.py:440` |
| Holding period | Lifecycle simulation / endpoint MTM | No strategic max holding period knob found; endpoint open MTM reported | Yes for current V2 | CODE_CHANGE_REQUIRED for arbitrary hold timeout | `tools/research_v2/run_7d_screen.py` ledger/finalization |
| Dynamic exit trigger | No strategic dynamic exit signal found in V2 | N/A | N/A | CODE_CHANGE_REQUIRED | V2 order spec only TP/SL full-position exits |
| Partial close | `scope=FULL_POSITION` | full position only | Yes | CODE_CHANGE_REQUIRED | `src/triggertrade/research_v2_execution.py:244`, `src/triggertrade/research_v2_execution.py:251` |
| Market entry fallback | `market_fallback=False` and validator forbids true | false only | Yes | CODE_CHANGE_REQUIRED | `src/triggertrade/research_v2_execution.py:234`, `src/triggertrade/research_v2_execution.py:305` |
| Acceptance cooldown | `cooldown_evidence` keyed by job/symbol acceptance | common 15 minutes; accepted attempts block same job+symbol until boundary | Mechanics frozen; value configurable | CONFIG_ONLY value, FROZEN mechanics | `tools/research_v2/run_7d_screen.py:510`, `tools/research_v2/run_7d_screen.py:1504`; tests `tests/unit/test_research_v2_screen_runner.py:488` |

## 12. Frozen Engine Invariants

| Invariant | Current Behavior | Why Not a Research Dimension | Source |
| --- | --- | --- | --- |
| Exchange API isolation | Execution services call adapters; triggers/sets do not place orders | Architecture boundary, not alpha dimension | `src/triggertrade/execution/futures.py`; `src/triggertrade/exchanges/contracts.py` |
| Risk before execution | Futures execution rejects unapproved or incomplete risk decisions | Safety gate | `src/triggertrade/execution/futures.py:635` |
| Paper/demo safety default | Config rejects live mode; futures demo requires paper mode, demo env, demo URL | Prevents live-money behavior during development | `src/triggertrade/config/settings.py:323`; `src/triggertrade/execution/futures.py:617` |
| Limit-only execution | `OrderType` only has `LIMIT`; V2 order spec uses LIMIT | Execution contract invariant | `src/triggertrade/execution/contracts.py`; `src/triggertrade/research_v2_execution.py:224` |
| POST_ONLY entry | V2 entry `post_only=True` | Maker-entry assumption and contract invariant | `src/triggertrade/research_v2_execution.py:225` |
| No chase/reprice/market fallback | V2 validity flags false; validator forbids true | Prevents hidden execution optimization | `src/triggertrade/research_v2_execution.py:232`, `src/triggertrade/research_v2_execution.py:305` |
| Full-position TP/SL | TP and SL scope `FULL_POSITION`; no strategic partial close | Avoids changing lifecycle/economics | `src/triggertrade/research_v2_execution.py:244`, `src/triggertrade/research_v2_execution.py:251` |
| Precision and exchange limits | Quantity, price, min notional, leverage bounds validated before submit | Exchange safety, not research knob | `src/triggertrade/execution/futures.py:649`; `src/triggertrade/research_v2_execution.py:350` |
| Duplicate submission prevention | Store checks intent/client order ID before submit/reserve | Idempotency invariant | `src/triggertrade/execution/futures.py:534`; `src/triggertrade/risk/manager.py:66` |
| Immutable Set result identity | Set result IDs/digests conflict on replay with different content | Traceability invariant | `src/triggertrade/set_engine/handler.py:194`, `src/triggertrade/set_engine/handler.py:610` |
| MARKET_HANDOFF evidence validation | Matched handoff requires reference levels, positive ATR exports, validated contract edge | Set/Position boundary invariant | `src/triggertrade/set_engine/handler.py:534` |
| Daily loss fail-closed uncertainty | Missing baseline/accounting blocks new entries | Safety invariant | `src/triggertrade/services/daily_loss.py:80`, `src/triggertrade/services/daily_loss.py:240` |
| Daily guard pending cancel | Daily guard cancels pending entries but does not remove protective exits | Safety/lifecycle invariant | `tools/research_v2/run_7d_screen.py:321`, `tools/research_v2/run_7d_screen.py:1448` |
| Acceptance-based cooldown | Cooldown is based on accepted entry time and survives close/unfilled expiry by job/symbol | Prevents overtrading via replay mechanics | `tools/research_v2/run_7d_screen.py:510`; tests `tests/unit/test_research_v2_screen_runner.py:542` |
| Funding/MTM factual accounting | Funding boundaries and endpoint MTM use factual source/mark evidence; missing required evidence invalidates | Accounting truth, not strategy dimension | `tools/research_v2/run_7d_screen.py:2109`; tests `tests/unit/test_research_v2_screen_runner.py:1024` |
| LLM exclusion from live path | No V2 or execution path calls an LLM for decisions | Architecture invariant | absence in inspected runtime decision modules; AGENTS invariant |

## 13. Unsupported but Common Research Ideas

| Idea | Current Status | Closest Existing Primitive | Requires Code Change? |
| --- | --- | --- | --- |
| RSI | No current backend metric/function found in inspected `src/triggertrade` Research V2, Set kernels, trigger primitives, or metrics data | return pct points, EMA trend, F-005 momentum score | YES |
| MACD | No current backend metric/function found in inspected implementation | EMA20/EMA50 comparison | YES |
| Order-book imbalance | No current V2 signal metric; required inputs list raw trades/candles/funding/marks/instrument metadata, not order book | raw trade causal fills, aggressive delta in legacy classifier inputs | YES |
| Arbitrary trailing stop | No trailing-stop order-spec or lifecycle primitive found | fixed full-position TP/SL; TTL entry expiry | YES |
| Strategic partial profit taking | Common profile says `partial_profit_taking=false`; V2 order spec uses `FULL_POSITION` | full-position 2R TP | YES |
| Dynamic allocation optimizer | No optimizer; V2 uses min of configured caps | nominal/risk/cap min formula | YES |
| Active BTC context filter in V2 | `btc_filter` is `DISABLED` for continuation profile | F-005 classifier has BTC context; V2 has BTC context requirement only | YES for V2 signals |
| Day/session filter | No current V2 primitive | accounting day/time windows only | YES |
| Market-entry fallback | Validator forbids market fallback | LIMIT post-only | YES |
| Arbitrary leverage sweep beyond profile/instrument bounds | V2 jobs use 1x and profile notes 2/3 scenario tests; runtime risk constrains leverage to instrument/config | leverage field and instrument validation | PARTIAL; new sweep orchestration may need code/config |

## 14. Hypothesis Construction Matrix

| Research Dimension | Can Vary Now? | How | Range / Values | Classification |
| --- | --- | --- | --- | --- |
| Choose J0-J7 job | Yes | job selection/config | J0-J7 | CONFIG_ONLY |
| Choose V2 signal family | Partially | existing job profiles | legacy, ret-or, continuation, compression, reversal | CONFIG_ONLY |
| Vary RET5/RET15 thresholds | Not through generic job config currently | function defaults/code branch | 0.30, 0.50 implemented | CODE_CHANGE_REQUIRED for arbitrary sweep |
| Recombine existing declarative predicates | Yes if metric values exist | declarative trigger rules | EQ/GTE/LTE/GT/LT; output-state enum | EXISTING_ENGINE_COMBINATION |
| Add new metric predicate over new metric | No | requires upstream metric producer | N/A | CODE_CHANGE_REQUIRED |
| Choose G0 vs G1 stop | Yes | J7 vs G0 jobs/profile | `HYBRID_STRUCTURAL`, `ATR_ONLY` | CONFIG_ONLY |
| Change stop numeric constants | Partially | common profile values loaded by profile/bridge | no schema min/max; code supports named fields | CONFIG_ONLY with caution |
| Change TP R multiple | No | bridge hard-codes 2R | `2` | CODE_CHANGE_REQUIRED |
| Change TP net floor | Yes | common profile | default 0.003; no explicit bounds | CONFIG_ONLY |
| Change entry TTL | Yes | profile/job entry value | null -> GTC; int -> TTL; no explicit min/max | CONFIG_ONLY |
| Enable chase/reprice/fallback | No | validator forbids | false only | CODE_CHANGE_REQUIRED |
| Change nominal margin fraction | Yes | common profile sizing | default 0.25; no explicit bounds | CONFIG_ONLY |
| Change per-trade risk cap | Yes | common profile sizing | default 0.0075; no explicit bounds | CONFIG_ONLY |
| Change total margin cap | Yes | common profile sizing | default 0.6; no explicit bounds | CONFIG_ONLY |
| Change per-coin cap | Yes | common profile sizing | default 0.33; no explicit bounds | CONFIG_ONLY |
| Change gross exposure cap | Yes | common profile sizing | default 1.8; no explicit bounds | CONFIG_ONLY |
| Change max open/pending | Yes | common profile sizing | default 3; no explicit bounds | CONFIG_ONLY |
| Change max positions per coin | Yes | common profile / trading rules | V2 default 1; trading rule enabled >0 and <= max open | CONFIG_ONLY |
| Change daily loss threshold | Yes | V2 profile/trading rules | V2 0.0225; trading rules enabled >0 | CONFIG_ONLY |
| Disable daily loss mechanics | Trading rules allow disabled; V2 profile assumes guard evidence | boolean in rules | enabled/disabled | CONFIG_ONLY outside V2 profile; risky research boundary |
| Change cooldown minutes | Yes | V2 profile/trading rules | >=0 in trading rules; V2 default 15 | CONFIG_ONLY |
| Expand V2 universe within available data | Partially | job/common symbols and physical binding | current AVAX/SUI/PEPE mapped to 1000PEPE | CONFIG_ONLY if data/instruments exist; otherwise CODE_CHANGE_REQUIRED/data required |
| Add BTC active filter to V2 continuation | No | current profile says disabled; signal ignores BTC | disabled | CODE_CHANGE_REQUIRED |
| Use F-005 classifier direction | Engine supports | `DirectionResolutionScope.F005_GOVERNED` | existing classifier inputs | EXISTING_ENGINE_COMBINATION |
| Use generic branch conflict resolution | Engine supports | `GENERIC_MATCHED_BRANCH` + conflict rule | LONG/SHORT branches | EXISTING_ENGINE_COMBINATION |
| Add RSI/MACD/order-book imbalance | No | no metric producer | N/A | CODE_CHANGE_REQUIRED |
| Strategic partial exits | No | full position TP/SL only | `FULL_POSITION` | CODE_CHANGE_REQUIRED |
| Arbitrary max holding duration | No | endpoint MTM/TTL entry only | N/A | CODE_CHANGE_REQUIRED |
| Funding/MTM accounting | Yes but not mutable as alpha | factual evidence path | required factual source evidence | FROZEN_INVARIANT |
| Precision/limits validation | Yes but not mutable | venue/instrument constraints | venue metadata | FROZEN_INVARIANT |

## 15. Implementation Gaps

- No schema layer gives explicit min/max bounds for many Research V2 common-profile numeric values; code mostly converts to Decimal and enforces behavior through downstream rejection.
- V2 signal thresholds are hard-coded in functions and `_signal_profile_for_job`; arbitrary threshold sweeps require code or a generalized config bridge.
- V2 continuation declares `btc_filter=DISABLED`; BTC context is not currently a usable V2 filter.
- V2 TP is fixed at 2R in the execution bridge despite profile storage carrying take-profit metadata.
- No strategy-level partial close, trailing stop, max holding period, day/session filter, RSI, MACD, or order-book imbalance primitive is currently implemented.
- Research V1 import/config artifacts contain many richer set definitions, but current V2 J0-J7 path does not expose them as arbitrary GPT-selectable hypotheses without verifying registry/runtime binding.

## 16. Ambiguities / Unverified Items

1. Whether editing `docs/research-v2/RESEARCH_V2_COMMON_PROFILE.json` alone is an intended supported workflow for all common-profile numerics; code consumes these fields, but no dedicated schema/range validator was found.
2. Whether `margin_fraction` in `ResearchV2JobConfig` is operationally meaningful for J2-J7 beyond normalized config/fingerprint evidence; sizing uses `runtime_profile["sizing"]`.
3. Whether imported Research V1 trigger/set catalogs are fully registered in the current runtime database in the user's environment; static files exist, but this inventory did not query or mutate runtime stores.
4. Whether all dataset-required symbols beyond the current three V2 symbols have complete frozen candles/raw trades/funding/mark metadata; no data package validation was run.
5. Whether active/live trading-rule UI changes are meant to be considered valid Research V2 dimensions; rules support many fields, but V2 J0-J7 uses its own execution profile bridge.

CAPABILITY_MAP_CREATED: YES
FILE: docs/research-v2/RESEARCH_V2_CAPABILITY_MAP.md
CODE_MODIFIED: NO
FULL_REPLAY_RUN: NO
UNVERIFIED_ITEMS: 5
DOC_IMPLEMENTATION_MISMATCHES: 2

CONFIG_ONLY_COUNT: 18
EXISTING_ENGINE_COMBINATION_COUNT: 4
CODE_CHANGE_REQUIRED_COUNT: 7
FROZEN_INVARIANT_COUNT: 2
