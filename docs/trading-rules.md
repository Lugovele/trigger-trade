# TriggerTrade Trading Rules

## Purpose

Trading behavior must be explicit, deterministic, versioned, and testable.

This document defines the rule framework. It does not claim that any strategy is profitable.

## Rule families

Use stable identifiers:

```text
TRG-xxx  trigger rule
STR-xxx  strategy rule
RSK-xxx  risk rule
EXE-xxx  execution rule
```

Examples:

```text
TRG-001  percentage price move trigger
TRG-002  robust volume confirmation candidate
TRG-003  reserved for future trigger

STR-001  candidate buy from confirmed oversold condition

RSK-001  maximum position size
RSK-002  stop-loss rule
RSK-003  maximum daily loss
RSK-004  cooldown after execution

EXE-001  duplicate-order prevention
EXE-002  partial-fill handling
```

## Rule contract

Every material rule should define:

- `rule_id`
- `version`
- `status`
- purpose
- exact inputs
- exact condition
- exact output
- units
- timeframe/window
- boundary semantics
- missing-data behavior
- required state
- whether it is blocking
- effective version/date where relevant

## Trigger contract

A trigger returns a signal; it does not return an exchange order.

Conceptual result:

```text
signal_id
trigger_rule_id
trigger_rule_version
symbol
observed_at
timeframe
input_snapshot
condition_result
signal_type
```

Keep signal types deliberately small, for example:

```text
BUY_CANDIDATE
SELL_CANDIDATE
EXIT_CANDIDATE
NO_SIGNAL
```

## Strategy contract

Strategy receives market state, position state, trigger results, and strategy configuration.

It returns a `TradeIntent`, for example:

```text
intent_id
strategy_rule_id
strategy_rule_version
symbol
side
intent_type
reason_trigger_ids
requested_position_logic
created_at
```

A trade intent is not permission to place an order.

## Risk contract

Risk receives a trade intent and current account/position state.

It returns:

```text
risk_decision_id
approved
checked_rule_ids
blocking_rule_ids
position_size
rejection_reason
created_at
```

Any blocking risk failure prevents execution.

## Boundary behavior

Boundary behavior must be tested explicitly.

Example:

```text
Rule: price_change_pct <= -5.0%

-4.999% -> false
-5.000% -> true
-5.001% -> true
```

Never leave inclusive versus strict comparisons implicit.

## Open rules

An undecided trading idea must remain open.

Do not convert:

`maybe use a 5% drop`

into:

`TRG-001 threshold = -5%`

without an explicit decision.

Suggested lifecycle:

```text
DRAFT
CONFIRMED
ACTIVE
DISABLED
RETIRED
```

Only confirmed/active rules may affect runtime behavior.

## Trigger Set Lifecycle

Runtime behavior is selected through versioned trigger sets, not by editing a live rule in place. A trigger set is an immutable membership snapshot containing specific trigger, strategy, and risk rule versions.

Lifecycle statuses:

```text
DRAFT
TESTING
ACTIVE
ARCHIVE
```

Rules and trigger sets must remain immutable once used for `TESTING` or `ACTIVE` runtime evidence. To change behavior, create a new rule version or a new trigger set version. At most one trigger set may be `ACTIVE` for the same symbol/timeframe. Multiple `TESTING` sets may evaluate the same completed candle in a separate TEST lane.

ACTIVE and TEST lane results must be attributed with:

```text
lane
trigger_set_id
trigger_set_version
rule ids and rule versions
```

The initial `TRG-001` threshold remains a development/demo configuration value. It is not evidence of a profitable trading edge. Visual dashboard fixtures may mention reference-only ideas such as RSI or momentum, but those fixture labels are not production rule definitions and must not affect runtime behavior.

Intraday governance thresholds, such as the initial 7-day / 100-signal /
50-closed-trade readiness gates, are lifecycle review policy. They are not
trigger, strategy, or risk alpha semantics and must not be treated as proof of
profitability or automatic promotion criteria.

## Perpetual Futures Domain Rules

The futures architecture uses explicit position actions instead of ambiguous
BUY/SELL domain intent:

```text
OPEN_LONG
CLOSE_LONG
OPEN_SHORT
CLOSE_SHORT
```

Allowed position states are `FLAT`, `LONG`, and `SHORT`. Direct flips are not
valid trading rules in this version; they must be represented as close then
open in a future reviewed lifecycle.

Full futures position lifecycle is governed by `futures-position-risk-v1` and
`protective-exit-v1`. Every `OPEN_LONG` or `OPEN_SHORT` must include a fixed
take-profit and stop-loss plan. `DYNAMIC` take-profit exists only as an
interface value and is not approved for runtime execution.

Initial protective-exit v1 formulas:

```text
LONG TP  = entry * (1 + configured_take_profit_pct)
LONG SL  = entry * (1 - configured_stop_loss_pct)
SHORT TP = entry * (1 - configured_take_profit_pct)
SHORT SL = entry * (1 + configured_stop_loss_pct)
```

Prices are floored to the exchange tick and then side relationships are
validated. LONG requires TP above entry and SL below entry. SHORT requires TP
below entry and SL above entry.

Risk/reward is enforced separately from net edge:

```text
LONG reward = TP - entry
LONG risk   = entry - SL
SHORT reward = entry - TP
SHORT risk   = SL - entry
R/R = reward / risk
```

The boundary is inclusive: R/R equal to the configured minimum passes.
Zero/negative risk, invalid side geometry, missing TP/SL, and below-minimum
R/R fail closed. Close reasons are limited to `TAKE_PROFIT`, `STOP_LOSS`,
`MANUAL`, and `CLOSE_ALL`; `SIGNAL_EXIT` is not part of this unit.
`OPEN_SHORT`/`CLOSE_SHORT` are supported by the backend lifecycle and manual
Demo validation path. Production `STR-FUT-001@0.1.0` remains long-only until a
separate reviewed strategy rule approves short-entry semantics.

Default leverage is `1x`. Leverage is a risk parameter, not a source of
profitability, and the system must not auto-increase it. No artificial
`max trades per day = N` cap is introduced here; frequency is constrained by
signal quality, net edge, risk, duplicate protection, churn/cooldown, and
execution constraints.

Futures net-edge eligibility is deterministic and fee-aware:

```text
expected gross price move - entry fee - exit fee - spread - slippage - funding
```

The result must meet the configured minimum net edge. If expected move or cost
inputs are unavailable, futures risk fails closed rather than guessing.

Market regime is context, not a trigger or execution signal.
`CTX-REGIME@0.1.0` classifies observed intraday state for BTCUSDT linear
perpetuals from the last 30 completed 1m closes. Current incomplete candles
are excluded.

Features:

- `window_return_pct = (latest_close - oldest_close) / oldest_close * 100`.
- `avg_abs_step_return_pct = mean(abs(adjacent close-to-close return pct))`.
- `normalized_trend = window_return_pct / avg_abs_step_return_pct`; zero when
  all steps are zero.
- `directional_persistence = (up_steps - down_steps) / 29`; flat steps count in
  the denominator and contribute zero.

Inclusive boundaries:

- `STRONG_UPTREND`: return >= `0.50`, normalized trend >= `5`, persistence >=
  `0.65`.
- `UPTREND`: return >= `0.15`, normalized trend >= `2`, persistence >= `0.35`.
- `STRONG_DOWNTREND`: return <= `-0.50`, normalized trend <= `-5`,
  persistence <= `-0.65`.
- `DOWNTREND`: return <= `-0.15`, normalized trend <= `-2`, persistence <=
  `-0.35`.
- `SIDEWAYS`: all other valid completed-candle windows.
- `INSUFFICIENT_DATA`: fewer than 30 completed candles or a non-positive close.
- `UNKNOWN`: unsupported timeframe, incomplete current candle, malformed or
  non-contiguous candle window.

These are initial deterministic context thresholds, not validated profitable
market regime boundaries and not a predictive edge claim. Formula or threshold
changes require a new immutable context version.

## Futures Accounting Conventions

Accounting is not an alpha rule and does not change Trigger Set promotion on
its own. It records deterministic financial facts so later analytics can
compare Trigger Sets honestly.

For Bybit Demo `BTCUSDT` USDT linear perpetuals, gross P&L uses actual entry
and exit VWAP:

```text
LONG  = (exit_vwap - entry_vwap) * quantity * contract_size
SHORT = (entry_vwap - exit_vwap) * quantity * contract_size
```

Fees are actual positive costs. Funding is an actual signed account impact:
positive funding improves net P&L and negative funding reduces it. Slippage is
diagnostic-only in closed-trade net P&L because actual fill prices already
affect gross P&L. Unrealized P&L prefers mark price and records the valuation
source. Return-on-margin and return-on-equity remain unsupported until their
capital-base semantics are separately reviewed.

## Futures Performance Metric Semantics

Strategy performance is scored at Trigger Set Version level. Rule-level
diagnostics may explain filtering or contribution, but a single trigger must
not be labeled independently profitable when the full set, strategy, risk, and
execution contract produced the trade.

For a closed-trade sample:

- `wins`: `net_pnl > 0`.
- `losses`: `net_pnl < 0`.
- Breakeven trades are neither wins nor losses.
- `win_rate`: `wins / closed_trades * 100`; unavailable when sample is empty.
- `gross_profit`: sum of positive accounting `gross_pnl` values.
- `gross_loss`: signed sum of negative accounting `gross_pnl` values.
- `expectancy_per_trade`: `mean(net_pnl)` in settlement currency, not percent.
- `profit_factor`: sum of positive net outcomes divided by absolute sum of
  negative net outcomes. If no losing outcomes exist, it is unavailable with an
  explicit reason instead of infinity.
- `fees_as_pct_of_gross_profit`: total actual fees divided by positive
  accounting gross P&L; unavailable when gross profit is non-positive.

Baseline comparison is only fair over overlapping ACTIVE and TESTING
closed-trade periods. Missing overlap, missing sample, or unavailable accounting
facts must be shown as unavailable, not filled with defaults. Performance
analytics do not auto-promote, mutate rules, or claim statistical significance.

## Historical Replay Rule Use

Historical replay must execute exact immutable Trigger Set and Rule Versions.
It is evidence collection, not a new alpha rule and not a parameter optimizer.
Replay may compare ACTIVE and TESTING sets only over the same historical period,
source, simulator, accounting and cost model. A replay result can support human
review, but it cannot promote a set, mutate thresholds, create a new rule
version, or imply that a single trigger is independently profitable.

Replay decisions obey no-lookahead semantics: the strategy decision at candle
`t` may use only completed data available through `t`, and simulated execution
may fill no earlier than candle `t+1`.

## TRG-002 Robust Volume Confirmation

Canonical rule id: `TRG-002`. Logical/display name: `TRG-VOLUME` / `Robust Volume Confirmation`. Initial version: `0.1.0`. Status: `TESTING` candidate only.

Input is the Bybit Spot base volume of the current completed BTCUSDT `1m` candle and the previous 60 completed BTCUSDT `1m` candles. The current candle is excluded from the lookback.

Median definition: sort the 60 previous volumes ascending and average positions 30 and 31 using 1-based indexing.

Relative volume: `current_volume / median_volume_60`. If the median is zero, the rule fails closed as `NOT_CONFIRMED`.

Percentile rank: `count(previous_volume <= current_volume) / 60 * 100`. Ties count as less-or-equal.

Condition: `relative_volume >= 2.0 AND volume_percentile >= 90`. Both boundaries are inclusive, so exactly `2.0` and exactly `90` pass.

Failure behavior: fewer than 60 previous completed candles, missing current volume, stale candle, incomplete current candle, wrong symbol/timeframe, or zero median returns `NOT_CONFIRMED` and cannot create an order path. Parameters `60 / 2.0 / 90` are candidate TEST values only and are not validated profitable production rules. The ACTIVE set is unchanged.
