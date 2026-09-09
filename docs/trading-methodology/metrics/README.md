# TriggerTrade Derived Metrics Foundation

This directory defines the computed market-variable layer between normalized raw
exchange data and later TriggerTrade methodology layers.

Conceptual chain:

```text
Raw Exchange Data
        ↓
Normalized TriggerTrade Raw Data
        ↓
Derived Metrics
        ↓
Composite Market States / Conditions
        ↓
Hypotheses
        ↓
Triggers
        ↓
Trading Rule Sets
```

## Catalogs

- `TRIGGERTRADE_DERIVED_METRICS_CATALOG.md` — authoritative derived-variable
  vocabulary for TriggerTrade methodology.

## Boundaries

- `Metric != Trigger`.
- A metric measures a market property or derived state.
- Timeframe, horizon, window, and anchor are metric parameters where
  applicable.
- One metric may be instantiated on multiple timeframes/horizons
  simultaneously.
- Future triggers may combine or compare the same metric across multiple
  timeframes.
- Thresholds, crossovers, breakout conditions, divergences, and
  multi-timeframe alignment belong to later methodology layers unless
  explicitly defined as a metric in the catalog.
- Presence of a metric in the catalog does not imply that it is a proven
  trading edge.
