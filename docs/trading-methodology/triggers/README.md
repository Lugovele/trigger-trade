# TriggerTrade Trigger Foundation

This directory defines the TriggerTrade trigger layer.

A TriggerTrade trigger is the smallest deterministic evaluable market rule
built directly from approved metrics and explicit comparison semantics.

Core form:

```text
metric + parameters + operator + comparison operand = trigger
```

Examples:

```text
OI_CHANGE_PCT(horizon=15m) >= X
```

```text
EMA(window=20, input_timeframe=5m)
crosses_above
EMA(window=50, input_timeframe=5m)
```

## Methodology Chain

```text
Raw Data
↓
Derived Metrics
↓
Triggers
↓
Sets
↓
Research
↓
Trading Rule Sets
```

## Catalogs

- `TRIGGERTRADE_TRIGGER_CONTRACT.md` — authoritative TriggerTrade trigger
  representation and evaluation contract.

## Boundaries

- `Trigger != Metric`.
- `Trigger != Set`.
- `Trigger != proven edge`.
- A Trigger may later be used inside a Set.
- Trigger thresholds may remain `PARAMETER_TO_TEST`.
- Timeframe, horizon, window, normalization, and baseline are explicit parts of
  trigger identity where applicable.
- Trigger evaluation supports `TRUE / FALSE / UNAVAILABLE`.
- Multi-timeframe trigger definitions are allowed.
- Backtest and live evaluation must use the same timing and availability
  semantics.
