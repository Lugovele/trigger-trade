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

## TRG-002 Robust Volume Confirmation

Canonical rule id: `TRG-002`. Logical/display name: `TRG-VOLUME` / `Robust Volume Confirmation`. Initial version: `0.1.0`. Status: `TESTING` candidate only.

Input is the Bybit Spot base volume of the current completed BTCUSDT `1m` candle and the previous 60 completed BTCUSDT `1m` candles. The current candle is excluded from the lookback.

Median definition: sort the 60 previous volumes ascending and average positions 30 and 31 using 1-based indexing.

Relative volume: `current_volume / median_volume_60`. If the median is zero, the rule fails closed as `NOT_CONFIRMED`.

Percentile rank: `count(previous_volume <= current_volume) / 60 * 100`. Ties count as less-or-equal.

Condition: `relative_volume >= 2.0 AND volume_percentile >= 90`. Both boundaries are inclusive, so exactly `2.0` and exactly `90` pass.

Failure behavior: fewer than 60 previous completed candles, missing current volume, stale candle, incomplete current candle, wrong symbol/timeframe, or zero median returns `NOT_CONFIRMED` and cannot create an order path. Parameters `60 / 2.0 / 90` are candidate TEST values only and are not validated profitable production rules. The ACTIVE set is unchanged.
