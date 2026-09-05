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

The dashboard and continuous paper runtime resolve the same SQLite path from `.env` plus process environment, with process environment taking precedence. The default is `runtime/triggertrade_paper.sqlite3` unless `TRIGGERTRADE_RUNTIME_DB_PATH` is set.

On startup they call the shared canonical registry bootstrap before opening runtime/read services. Configured Rule Versions, Trigger Sets, and Recommendations are visible even before runtime evidence exists.

The dashboard is intentionally read-only for trading logic after startup initialization. It does not evaluate triggers, create strategy decisions, approve risk, call execution services, place/cancel orders, or expose API credentials. The startup bootstrap stores only canonical registry metadata, not fake candles, trades, fills, P&L, or performance evidence. Futures P&L shown in the dashboard must come from the backend accounting store; alerts remain deferred.
## Trigger Sets and Lanes

The runtime now bootstraps versioned trigger sets and evaluates the current ACTIVE set alongside TESTING sets over the same completed candle. ACTIVE remains the only lane connected to paper execution. TEST lanes are persisted for comparison and dashboard visibility only; they do not submit Bybit orders or change trading configuration.

Dashboard views show ACTIVE/TEST lane summaries, trigger set versions, rule registry details, runtime logs, and local-only read models. The interface intentionally keeps promotion and rule editing out of the UI. Financial values are displayed only when persisted by backend accounting.

## Rule Analytics and Recommendations

Rules now have a logical identity and immutable versions. Trigger Set membership references exact `rule_id + version` pairs so historical TEST/ACTIVE evidence remains reproducible. A parameter or formula change must create a new rule version instead of mutating historical records.

The first candidate analytics experiment is `TRG-002@0.1.0`, display name `Robust Volume Confirmation`, logical name `TRG-VOLUME`. It is TESTING only and uses candidate/demo parameters: previous 60 completed BTCUSDT spot candles, median base volume baseline, `relative_volume >= 2.0`, and empirical percentile rank `count(previous_volume <= current_volume) / 60 * 100 >= 90`. These parameters are not validated production trading edge.

The local dashboard adds read-only Rule Detail pages under `/rules/<rule_id>/<version>` and an Analytics tab with set-level supported counts plus Recommendation Registry entries. Analytics never promotes a set, mutates rules, calls execution, or fabricates unsupported win-rate/return metrics. P&L, equity, fees, funding and drawdown are shown only from deterministic backend accounting records.

## Intraday Governance

TriggerTrade is treated as an intraday systematic trading project: evidence is
collected from many short-interval observations and evaluated at Trigger Set
level. TESTING Trigger Sets have a separate `EvidenceReadiness` projection
(`COLLECTING`, `EARLY`, `REVIEW_READY`, `STRONG_EVIDENCE`,
`INSUFFICIENT_DIVERSITY`, `BLOCKED`) that does not change Trigger Set lifecycle
status and never auto-promotes a set.

The initial governance policy is versioned as
`intraday-governance-defaults@0.1.0`: 7 calendar days, 100 candidate signals,
and 50 closed trades. These are configurable governance defaults for review
readiness only, not statistically proven trading thresholds. Closed-trade and
market-regime metrics are shown as unavailable until backend accounting/regime
semantics exist.

The local dashboard includes a persistent `STOP TRADING` control. When paused,
new ACTIVE executions fail closed at the execution boundary, while TEST lane
collection, analytics, market-data processing, and reconciliation continue.
Pause state survives restart and requires an explicit Resume action.

## Perpetual Futures Direction

TriggerTrade is moving from the initial Spot-oriented prototype toward an
automated event-driven intraday perpetual futures bot. The first futures
contract target is Bybit Demo `BTCUSDT` USDT perpetual using V5
`category=linear`.

The futures model is additive. Existing Spot/paper records remain readable,
while new futures contracts use explicit position actions: `OPEN_LONG`,
`CLOSE_LONG`, `OPEN_SHORT`, and `CLOSE_SHORT`. The default configured leverage
is `1x`; leverage is treated as a risk parameter, not a profit lever.

Futures risk includes Decimal-based margin, leverage, cost, funding, duplicate,
operator-pause, and net-edge gates. If expected move or cost evidence is
missing, the futures net-edge gate fails closed.

Deterministic futures accounting lives behind the backend accounting boundary
with `futures-accounting-v1`. Closed-trade gross P&L for Bybit Demo
`BTCUSDT` linear perpetuals is `LONG = (exit - entry) * quantity` and
`SHORT = (entry - exit) * quantity`, with exchange contract size applied if
metadata provides a non-1 value. Fees are positive costs, actual funding is a
signed account impact, and slippage is diagnostic because actual fill prices
already determine gross P&L. Dashboard futures rows are read-only projections
from persistence.

Futures performance analytics are calculated only above accounting facts and
are scored by Trigger Set Version. The dashboard can show closed trades, win
rate, expectancy, profit factor, fees, funding, baseline comparison and sample
warnings when samples exist. Empty samples and zero denominators stay
unavailable; analytics does not auto-promote sets or mutate rules.
