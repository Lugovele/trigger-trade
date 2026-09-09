# TriggerTrade Methodology Data Foundation

This directory defines the methodology data foundation for TriggerTrade.

The data layer establishes the raw exchange-data universe, normalization
requirements, historical testability constraints, and dependency boundary that
future metrics, triggers, Sets, Research, and Trading Rule Sets must trace back
to.

Conceptual sequence:

```text
Raw Exchange Data
        ↓
Normalized TriggerTrade Raw Data
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

- `BYBIT_RAW_DATA_CATALOG.md` — authoritative Bybit raw-data universe and
  TriggerTrade raw-data normalization contract.

## Constraints

- TriggerTrade does not maintain its own large historical archive of
  high-frequency market streams solely for backtesting.
- Historical research is constrained by data that is officially available from
  Bybit or other explicitly approved sources.
- Realtime availability alone does not qualify a data source for the core
  TriggerTrade trigger-evidence path.
- The raw-data catalog is the authoritative dependency boundary for future
  metric definitions.

## Forward dependency

```text
data
↓
metrics
↓
triggers
↓
sets
↓
future rules
```

The next methodology layer is `../metrics/`, which defines derived metrics that
depend on this raw-data foundation.
