# TriggerTrade Set Foundation

This directory defines the TriggerTrade Set layer.

A TriggerTrade Set is a deterministic market configuration composed from
approved Triggers plus explicit logical and temporal relationships.

Core boundary:

```text
SET = when the market configuration exists
RULES = what to do with it
```

Core form:

```text
SET
=
TRIGGERS
+
LOGICAL RELATIONSHIPS
+
TEMPORAL RELATIONSHIPS
+
SET-FORMATION LIFECYCLE
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
Rules
↓
Research
↓
Trading Rule Sets
```

## Catalogs

- `TRIGGERTRADE_SET_CONTRACT.md` — authoritative TriggerTrade Set
  representation and evaluation contract.

## Boundaries

- `Set != Trigger`.
- `Set != Rule`.
- `Set != Research`.
- `Set != proven edge`.
- `SET MATCHED` does not mean enter a trade.
- `SET MATCHED` means only that the specified market configuration has formed.
- Trading Rules are defined in a separate later layer.
- Set semantics must be identical in methodology, research, backtest, paper,
  and live evaluation.
