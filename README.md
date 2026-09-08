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
- `.codex/agents/triggertrade-security-change-reviewer.toml`
- `.codex/agents/triggertrade-security-auditor.toml`
- `.codex/agents/triggertrade-agent-security-reviewer.toml`
- `.codex/agents/triggertrade-ux-reviewer.toml`
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

The dashboard product surface is futures-first: LIVE means the ACTIVE Bybit Demo linear-perpetual lane, not mainnet trading, and TEST means local deterministic futures simulation. It shows account/equity, position, trade, fee, funding, regime, readiness, and recommendation fields only when the backend has persisted authoritative facts. Take-profit, stop-loss, liquidation, margin, or P&L fields that do not yet have backend support are rendered as Not configured, Not available, or unavailable instead of being calculated in the frontend.

Portfolio is now backed by backend read models instead of fixture account rows.
`Total` is the latest authoritative account equity snapshot, `Available` is
the latest account available margin/capital for new entries, and `In positions`
is the sum of persisted open-position entry notionals. `Realized P&L today` is
closed-trade net P&L for the current UTC day, while aggregate `Unrealized P&L`
comes from the latest backend equity/accounting snapshot. If those facts are
missing or stale, the read model exposes `UNAVAILABLE` or `STALE`; the frontend
does not synthesize balances or recalculate portfolio metrics. Portfolio close
actions use protected backend POST contracts and fail closed when the dashboard
process has no attached futures lifecycle execution bridge.
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
operator-pause, and net-edge gates. If the minimum net-edge rule is enabled and expected move or cost evidence is
missing, the futures net-edge gate fails closed. If disabled in the current
TradingRulesVersion, the gate is explicitly excluded and recorded as such.

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

Market regime context is provided by `CTX-REGIME@0.1.0`. It classifies the
latest 30 completed 1m BTCUSDT linear-perpetual candles into
`STRONG_DOWNTREND`, `DOWNTREND`, `SIDEWAYS`, `UPTREND`,
`STRONG_UPTREND`, or explicit `UNKNOWN` / `INSUFFICIENT_DATA` states. The
runtime persists regime diagnostics and links them into strategy provenance,
but regime context never executes trades by itself.

Run the public-data regime smoke manually with:

```powershell
$env:RUN_TRIGGERTRADE_REGIME_SMOKE="1"
python -m triggertrade.services.regime_smoke
```

The smoke uses Bybit Demo public linear candles only; it does not load private
credentials or call order endpoints.

## Futures Position Lifecycle

TriggerTrade futures execution is Bybit Demo linear only. New ACTIVE entries
must pass risk with mandatory fixed take-profit and stop-loss plans, inclusive
risk/reward validation, net-edge validation, 1x default leverage, and one net
position per symbol. TP/SL, manual close, close-all and reconciliation are
backend services; the dashboard remains read-only and cannot place orders.
SHORT lifecycle plumbing is backend/manual/smoke capable, while the current
production strategy remains `STR-FUT-001@0.1.0` long-only pending a separate
short-entry rule review.

Run the opt-in lifecycle smoke manually with:

```powershell
$env:RUN_TRIGGERTRADE_FUTURES_LIFECYCLE_SMOKE="1"
python scripts/bybit_demo_futures_lifecycle_smoke.py
```

The smoke uses sanitized output only and stops rather than forcing unsafe
fills when a safe Demo PostOnly order does not become an actual position.

## Versioned Trading Rules

Trading rules are now a backend policy registry separate from Trigger Sets. A Trigger Set answers whether the current market context produced a signal; the current immutable `TradingRulesVersion` answers how a new futures position is sized and whether it may open.

The shared bootstrap creates one factual `v1` from the existing futures runtime configuration on an empty runtime DB. Later changes create a new immutable version and move a small current pointer; old versions are not mutated. New ACTIVE futures positions pin the exact `rules_version_id` and resolved values for position size, fixed TP, SL, R/R, optional net edge, leverage, portfolio caps, direction mode, coin config and cost assumptions. Existing positions keep their original snapshot when the current rules version changes.

`FIXED` take-profit is supported in runtime. `DYNAMIC` is represented as a contract value but fails closed until a separately reviewed deterministic algorithm exists. Minimum take-profit is a floor, not a cap. Optional rules use explicit enabled flags; disabled net edge is excluded from the gate rather than represented by magic zero/null thresholds.


## Bybit Linear Instrument Catalog

TriggerTrade caches authoritative Bybit Demo public instrument metadata for USDT-settled linear perpetual futures from `GET /v5/market/instruments-info?category=linear`. The catalog is backend-only and requires no credentials, private endpoints, or order calls.

The catalog exposes only TriggerTrade-compatible tradeable instruments: `LinearPerpetual`, settle coin `USDT`, exchange status `Trading`, and complete tick/quantity/leverage limits. Refresh is explicit and atomic: all paginated pages are fetched, normalized, deduplicated, hashed, then persisted; a failed refresh preserves the last valid cache.

Trading Rules coin configuration and futures runtime entry validation use the same catalog service. New entries fail closed for unknown, suspended, delisted, inverse, dated, non-USDT, or incomplete instruments. Existing positions keep an immutable instrument snapshot so TP/SL, manual close, close-all, and reconciliation can continue during a catalog outage or after later symbol-status changes. Price and quantity normalization use Decimal exchange constraints; leverage is rejected if it exceeds instrument metadata rather than silently clamped.

Run the public catalog smoke manually with:

```powershell
$env:RUN_TRIGGERTRADE_INSTRUMENT_CATALOG_SMOKE="1"
python scripts/bybit_instrument_catalog_smoke.py
```

## Continuous Futures Runtime

`python -m triggertrade.services.runtime` now starts the continuous futures
runtime, not the legacy Spot local-paper runner. It requires explicit safe
configuration:

- `TRIGGERTRADE_MARKET=linear`
- `TRIGGERTRADE_CATEGORY=linear`
- `TRIGGERTRADE_EXECUTION_VENUE=bybit_demo_futures`
- `TRIGGERTRADE_ACTIVE_EXECUTION_VENUE=bybit_demo_futures`
- `TRIGGERTRADE_TEST_EXECUTION_VENUE=local_test_simulation`
- Bybit Demo credentials in local ignored `.env`

The runtime consumes one canonical Bybit Demo `category=linear` completed 1m
BTCUSDT candle stream for both lanes. ACTIVE creates `FuturesTradeIntent`
records and may submit only through `FuturesExecutionService` plus
`BybitFuturesExecutionAdapter` after approved futures risk and operator-pause
checks. TEST uses an isolated deterministic simulator with
`evidence_source=test_simulation`; it never calls Bybit private/order APIs.

The first integrated futures strategy rule is `STR-FUT-001@0.1.0`. It is
demo-only and OPEN_LONG-only for this integration unit. It requires a
futures `TRG-001@0.2.0` BUY_CANDIDATE, downtrend regime context, FLAT position
state, and an explicit demo expected gross move input. It does not implement
OPEN_SHORT, closes, or flips yet.

Analytics keeps exchange accounting facts and TEST simulation facts
source-aware. Like-for-like baseline comparison is unavailable when evidence
sources differ; the dashboard must label that honestly instead of treating
simulated TEST results as equivalent to exchange fills.

## Historical Replay

`python -m triggertrade.backtest` runs the internal historical replay engine
when `RUN_TRIGGERTRADE_BACKTEST_SMOKE=1` is set. It downloads Bybit Demo public
`category=linear` BTCUSDT completed 1m candles into the ignored
`runtime/history/` cache and replays exact Trigger Set and Rule Version
definitions through the existing regime, trigger, strategy, futures risk,
accounting and performance contracts.

Historical replay is recorded with evidence source `BACKTEST`. It is separate
from exchange execution and from continuous TEST-lane simulation. It does not
load private credentials, submit orders, optimize parameters, auto-promote
sets, or fabricate missing evidence. Decisions at candle `t` may only use data
available through that completed candle; simulated fills occur no earlier than
the next completed candle under the pinned simulator version.

When the minimum net-edge gate is disabled, the current integration strategy does not require a demo expected gross move solely for net-edge calculation; direction and trigger/regime provenance still gate intent creation.
