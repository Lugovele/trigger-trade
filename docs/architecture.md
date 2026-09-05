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

## Versioned Trigger Sets and Parallel Lanes

Trigger, strategy, and risk rules are grouped into immutable `TriggerSetVersion` records. A trigger set version records its symbol/timeframe scope, lifecycle status, rule membership, creation metadata, and a semantic hash. Existing rule formulas keep their own stable rule ids and versions; the trigger set is the runtime unit that chooses which versions run together.

Supported trigger set statuses are:

```text
DRAFT -> TESTING -> ACTIVE -> ARCHIVE
```

Only one trigger set may be `ACTIVE` for a symbol/timeframe at a time. Multiple `TESTING` sets may run in parallel for comparison. `DRAFT` and `ARCHIVE` sets are retained for review/history and must not be evaluated by the runtime.

The continuous runtime fans out one canonical completed market observation into isolated lanes:

```text
completed market candle
        -> ACTIVE lane for the active trigger set
        -> TEST lane for each testing trigger set
```

Lane identity is part of the business key for every runtime lifecycle: `lane + symbol + timeframe + candle_id + trigger_set_id + trigger_set_version`. This prevents ACTIVE and TEST records from colliding while still proving that both lanes evaluated the same market event.

The TEST lane is analysis-only. It may run trigger, strategy, and risk logic and may persist decisions, but it must not call Bybit private/order APIs or affect ACTIVE paper execution. Promotion from TESTING to ACTIVE is an explicit audited transition; the dashboard does not provide automatic promotion or trading controls.

## Rule Analytics and Recommendations

Rule identity is split between a logical rule id and immutable rule versions. Trigger Sets must reference exact `rule_id + version` pairs. Once a rule version has been recorded for TESTING or ACTIVE evidence, semantic fields such as formula, thresholds, inputs, boundary behavior, stale-data behavior, missing-data behavior, and output semantics must not be edited in place. Any material change creates a new version and preserves historical reproducibility.

Recommendations are audited experiment proposals. The lifecycle is `Observation -> Hypothesis -> Recommendation -> Candidate Trigger Set -> TESTING -> Evaluation -> Decision`. A recommendation may create or reference a TESTING candidate set through explicit reviewed code/config, but it must never promote TESTING to ACTIVE, mutate ACTIVE, or call execution. Analytics evaluates performance at Trigger Set version level, not by declaring an isolated trigger profitable.

Dashboard Rule Detail and Analytics pages are read-only projections over persistence. They may link rules, exact versions, trigger sets, recommendations, and supported evidence counts. They must not evaluate triggers, approve risk, place/cancel orders, expose arbitrary SQL, expose `.env`, or render secrets.

Canonical registry bootstrap is a shared service-layer startup concern. It writes only configured RuleDefinitions, immutable TriggerSetVersions, memberships, and Recommendations into the intended runtime SQLite database before runtime/dashboard services open their stores. Runtime evidence remains separate: bootstrap must not create candle lifecycles, orders, fills, performance history, P&L, or synthetic analytics rows. If an existing exact rule/set/recommendation identity has different semantics, bootstrap fails closed through persistence immutability instead of silently mutating history.
