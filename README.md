# TriggerTrade Development Infrastructure

TriggerTrade is a small personal automated crypto trading bot for a limited watchlist of coins.

Runtime flow:

Market Data -> Triggers -> Signals -> Strategy -> Trade Intent -> Risk -> Execution -> Exchange

The project is intentionally small. The infrastructure exists to keep money-moving logic deterministic, testable, traceable, and reviewable.

## Included

- `AGENTS.md`
- `.codex/agents/triggertrade-change-lifecycle-orchestrator.toml`
- `.codex/agents/triggertrade-architecture-reviewer.toml`
- `.codex/agents/triggertrade-trading-rules-reviewer.toml`
- `.codex/agents/triggertrade-change-reviewer.toml`
- `.codex/agents/triggertrade-review-remediation-agent.toml`
- `.codex/agents/triggertrade-test-planner.toml`
- `docs/architecture.md`
- `docs/trading-rules.md`
- `docs/execution-and-safety.md`
- `docs/development-lifecycle.md`
- `docs/mvp-scope.md`

## Local Dashboard

Run the read-only local dashboard with:

```bash
python -m triggertrade.dashboard
```

Default URL: `http://127.0.0.1:8765/`.

The dashboard reads the continuous paper runtime SQLite state from
`runtime/triggertrade_paper.sqlite3` unless `TRIGGERTRADE_RUNTIME_DB_PATH` is
set. It shows runtime checkpoint state, latest decision, recent candle
lifecycles, paper trades/fills, and the full trace from candle to trigger,
strategy, risk, and execution records.

The dashboard is intentionally read-only. It does not evaluate triggers, create
strategy decisions, approve risk, call execution services, place/cancel orders,
read `.env`, or expose API credentials. P&L, portfolio accounting, alerts, and
operator controls are intentionally deferred until backend semantics exist.

## Trigger Sets and Lanes

The runtime now bootstraps versioned trigger sets and evaluates the current ACTIVE set alongside TESTING sets over the same completed candle. ACTIVE remains the only lane connected to paper execution. TEST lanes are persisted for comparison and dashboard visibility only; they do not submit Bybit orders or change trading configuration.

Dashboard views show ACTIVE/TEST lane summaries, trigger set versions, rule registry details, runtime logs, and local-only read models. The interface intentionally keeps promotion, rule editing, P&L, portfolio accounting, and trading controls deferred.
