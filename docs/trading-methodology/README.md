# TriggerTrade Methodology Council

This documentation defines the methodology council used to design, challenge, validate, and evolve TriggerTrade trading rules.

The council is not a collection of independent opinion agents. It is a staged research and review system.

## Core lifecycle

```text
Trading idea / market observation
        ↓
Senior Intraday Crypto Trader
        ↓
Market Microstructure & Order Flow Researcher
        ↓
Market Regime & Context Analyst
        ↓
Quant Strategy Researcher
        ↓
Risk & Trade Management Architect
        ↓
Execution & Exchange Mechanics Specialist
        ↓
Adversarial Strategy Reviewer
        ↓
Trading Rule Set decision
        ↓
Backtest / paper / live evidence
        ↓
Performance & Strategy Diagnostics Analyst
        ↓
Iteration or promotion
```

## Principle

No agent may promote a plausible idea into a production rule without evidence.

Every rule must move through explicit states:

`IDEA → HYPOTHESIS → RESEARCH_CANDIDATE → BACKTESTED → PAPER_VALIDATED → LIVE_CANDIDATE → LIVE_VALIDATED`

A rule may move to `REJECTED` at any stage.

## Canonical artifacts

- `data/` — authoritative raw-data universe and normalization contract on which
  future metrics, regimes, setups, triggers, and Trading Rule Sets depend.
- `contracts/TRADING_RULE_SET.md` — canonical methodology object.
- `contracts/AGENT_HANDOFF_CONTRACT.md` — inter-agent handoff contract.
- `contracts/REVIEW_AND_PROMOTION_CONTRACT.md` — evidence and promotion gates.
- `contracts/METHODOLOGY_LIFECYCLE.md` — end-to-end lifecycle.

## Agents

- `agents/senior-intraday-crypto-trader.md`
- `agents/microstructure-order-flow-researcher.md`
- `agents/market-regime-context-analyst.md`
- `agents/quant-strategy-researcher.md`
- `agents/risk-trade-management-architect.md`
- `agents/execution-exchange-mechanics-specialist.md`
- `agents/adversarial-strategy-reviewer.md`
- `agents/performance-strategy-diagnostics-analyst.md`

## Non-negotiable rules

1. A trigger is not a strategy.
2. Market context and regime precede entry logic.
3. LONG and SHORT are first-class directions.
4. Gross PnL is never treated as net PnL.
5. Fees, funding, slippage, fill assumptions, and correlated exposure must be modeled.
6. Thresholds that have not been empirically justified are marked `PARAMETER_TO_TEST`.
7. No agent invents live prices, OI, funding, liquidation data, or market statistics.
8. A 20% net monthly return is a target to test, never an assumption or guarantee.
