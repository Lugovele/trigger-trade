# TriggerTrade MVP Scope

## Product definition

TriggerTrade v1 is a personal automated trading bot for a small watchlist of crypto assets.

The goal is:

```text
watch selected coins
    ->
evaluate deterministic triggers
    ->
apply strategy rules
    ->
apply risk rules
    ->
paper/live execution
    ->
record what happened and why
```

## MVP capabilities

### Watchlist
- configured symbols;
- enabled/disabled state per symbol.

### Market data
- required price/candle/volume inputs;
- normalized timestamps and numeric formats;
- stale/missing data detection.

### Triggers
A small initial set only. Candidate examples:

- percentage price move;
- RSI threshold;
- moving-average crossover;
- volume spike.

The actual initial trigger set must be explicitly selected before implementation.

### Strategy
- combine trigger signals;
- produce trade intents;
- no direct exchange calls.

### Risk
Minimum before live trading:

- max order/position size;
- balance check;
- duplicate order protection;
- cooldown;
- stop-loss/take-profit where strategy requires them;
- maximum daily loss or equivalent kill boundary;
- manual kill switch.

### Execution
- one exchange;
- paper adapter;
- live adapter;
- order status tracking;
- rejection handling;
- partial fills;
- reconciliation.

### Persistence
Store enough to answer:

- What did the bot observe?
- Which triggers fired?
- Which strategy rule produced the intent?
- Which risk rules were checked?
- Why was the trade approved or rejected?
- What order was submitted?
- What did the exchange do?
- What is the resulting position/P&L state?

### UI

Small private monitoring interface.

Suggested surfaces:

#### Overview
- balance/equity;
- open positions;
- unrealized P&L;
- today's realized P&L;
- trading enabled/disabled;
- paper/live mode.

#### Positions
- symbol;
- side;
- quantity;
- entry;
- current price;
- P&L;
- related strategy/rule.

#### Trade history
- time;
- symbol;
- action;
- requested price/quantity;
- fill;
- trigger IDs;
- strategy ID;
- risk result;
- P&L where available.

#### Signal log
- observation time;
- trigger inputs;
- trigger result;
- strategy result;
- risk result;
- final execution decision.

## Explicit non-goals

Do not add during MVP unless separately approved:

- advanced charting;
- multi-user auth;
- public SaaS;
- multi-exchange aggregation;
- copy trading;
- ML/LLM trading;
- autonomous strategy generation;
- complex portfolio optimization;
- options/futures;
- generalized plugin framework;
- generalized backtesting platform.

## MVP completion criterion

MVP is complete when one configured strategy can:

1. observe selected symbols;
2. produce deterministic signals;
3. generate a trade intent;
4. pass/fail deterministic risk checks;
5. execute through paper mode end-to-end;
6. persist and display the full decision/execution trail;
7. survive restart without silently corrupting order/position state.

Live trading is a separate acceptance step after paper-mode validation.

## Analytics MVP Scope

In MVP scope: immutable rule version history, exact Trigger Set membership, read-only Rule Detail pages, a Recommendation Registry, supported set-level evidence counts, and a first TESTING-only volume confirmation candidate.

Intraday governance is in MVP scope as review readiness, not auto-promotion.
The dashboard may show TEST set readiness, missing evidence, recommendation
actions, and a persistent local STOP TRADING control. It must not add new
trigger semantics, execution product models, P&L accounting, or futures support.

Out of scope: automatic promotion, automatic parameter optimization, LLM trading recommendations, backtesting platform, P&L/portfolio accounting, new SELL logic, and any direct execution from analytics or dashboard.
