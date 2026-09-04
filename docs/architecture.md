# TriggerTrade Architecture

## Purpose

TriggerTrade is a small automated trading bot for a limited set of crypto assets. It is not a general-purpose trading platform, portfolio-management suite, or charting product.

## Runtime pipeline

```text
Exchange Market Data
        |
        v
Market Data Adapter
        |
        v
Trigger Engine
        |
        v
Signals
        |
        v
Strategy Engine
        |
        v
Trade Intent
        |
        v
Risk Manager
        |
        v
Approved / Rejected Intent
        |
        v
Execution Engine
        |
        v
Exchange Adapter
        |
        v
Exchange

All material states and decisions
        |
        v
Persistence
        |
        v
Monitoring UI
```

## Architecture invariants

1. Exchange API details are isolated behind exchange adapters.
2. A trigger never places an order directly.
3. A trigger produces a deterministic signal only.
4. Strategy logic converts signals into a trade intent.
5. Risk checks are mandatory before execution.
6. Only the execution layer may submit, cancel, or reconcile orders.
7. Paper and live trading implement the same execution contract through different adapters.
8. Trading decisions must not be made in the UI.
9. Trading decisions must not depend on an LLM.
10. Secrets must never be committed, logged, rendered in the UI, or included in fixtures.
11. Every order must be traceable to the observation, trigger(s), strategy decision, risk decision, execution request, and exchange response.
12. Restarts must not silently lose knowledge of open positions, submitted orders, or unresolved execution state.
13. Duplicate order submission must be prevented through explicit idempotency/state checks.
14. Exchange precision, tick size, step size, minimum notional, and supported order constraints must be validated before submission.
15. The runtime must fail closed when critical state is uncertain.
16. Live trading must be explicitly enabled; paper mode is the safe default during development.

## Suggested module boundaries

```text
src/triggertrade/
    config/
    market_data/
    triggers/
    strategies/
    risk/
    execution/
    exchanges/
    persistence/
    services/
    dashboard/
```

### `market_data/`
Normalizes exchange market data into stable internal objects.

### `triggers/`
Deterministic trigger implementations.

### `strategies/`
Combines trigger outputs and current state into trade intents.

### `risk/`
Position sizing, exposure limits, daily loss limits, cooldowns, stop rules, and blocking checks.

### `execution/`
Order lifecycle, idempotency, retries, reconciliation, fill handling, and paper/live execution contracts.

### `exchanges/`
Exchange-specific adapters only.

### `persistence/`
Signals, decisions, orders, fills, positions, and rule/config versions needed for traceability.

### `dashboard/`
Read-oriented monitoring surface. It must not become a second trading engine.

## Dependency direction

Preferred:

```text
domain logic -> abstract contracts
exchange adapters -> abstract contracts
dashboard -> read/query models
```

Avoid:

```text
triggers -> exchange SDK
strategy -> exchange SDK
risk -> dashboard
dashboard -> place_order()
```

## Out of scope for MVP

- multi-exchange smart routing;
- high-frequency trading;
- portfolio optimization;
- ML/LLM-directed trading;
- TradingView-style charting;
- public multi-user product;
- complex generalized backtesting infrastructure;
- derivatives unless explicitly added later.
