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

Research records are backend-owned product state. They persist exact Trigger
Set Version identity, exact Trading Rules Version identity, selected backtest
and Demo run ids, decision state, archive state, and schema version. Research
does not duplicate raw trade history from backtest/accounting tables.

### `dashboard/`
Read-oriented monitoring surface. It must not become a second trading engine.

Messages are a dashboard-facing operational read model, not a raw log viewer.
They live in their own persistence table with stable ids, explicit
INFO/ATTENTION/WARNING/ERROR vocabulary, deterministic newest-first listing,
and persisted read/unread state. Opening the Messages surface may mark the
currently returned unread rows read through a protected backend write that has
no trading or execution side effects.

System History export is a separate backend-owned technical snapshot for later
debugging, audit, or AI-assisted analysis. The browser must request the export
from the backend and copy the returned sanitized text; it must not assemble the
history from DOM state, read files directly, pass arbitrary paths, or expose a
raw logs page.

Demo readiness is a backend read model, not a dashboard color heuristic. The
readiness rollup uses explicit `RUNNING`, `DEGRADED`, `BLOCKED`, and
`UNAVAILABLE` states from bounded checks: database readability, persisted
runtime heartbeat, processed market-data freshness, instrument catalog state,
and operator pause state. The dashboard may display this projection, but it
must not infer healthy operation from missing data.

Runtime heartbeat is component-scoped persisted state. Each component updates
one latest heartbeat row with an allowlisted status and bounded metadata, so
restart can recover the latest known liveness signal without converting
heartbeats into an unbounded technical log stream.

Research follows `Backtest -> Demo -> Compare -> Decision`. It is separate
from the older runtime evidence lanes. Backtests reference immutable
historical replay runs from backend-owned replay inputs, never browser-supplied
candle arrays. If pinned rules require semantics the replay engine cannot fully
honor, Research records unavailable evidence instead of substituting behavior.
Demo is blocked unless Research-specific exchange and accounting isolation are
positively available. Compare reports unavailable when selected Research Demo
or overlapping ACTIVE benchmark facts are missing. Make Active does not change
ACTIVE Trigger Sets or Trading Rules until exact activation semantics receive a
separate reviewed implementation.

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

Trigger, strategy, context, and risk rules are grouped into immutable `TriggerSetVersion` records. A trigger set version records its symbol/timeframe scope, lifecycle status, exact rule membership, creation metadata, and deterministic composition hash. Existing rule formulas keep their own stable rule ids and versions with deterministic definition hashes; the trigger set is the runtime unit that chooses which versions run together.

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

The TEST lane is analysis-only. It may run trigger, strategy, and risk logic and may persist decisions, but it must not call Bybit private/order APIs or affect ACTIVE paper execution. Promotion from TESTING to ACTIVE is an explicit audited transition; the dashboard does not provide automatic promotion, rule editing, order placement, or strategy/risk controls. Its only operator control is the persisted local STOP/RESUME gate for new ACTIVE submissions.

The current production runtime target is Bybit Demo `BTCUSDT` linear
perpetuals. It consumes one canonical completed `category=linear` 1m candle
stream for ACTIVE and TEST lanes. ACTIVE may create `FuturesTradeIntent`
records and submit only through `FuturesExecutionService` and the Bybit Demo
futures adapter after futures risk approval. TEST uses a source-aware local
simulation model for closed-trade evidence and must never call Bybit
private/order endpoints.

## Rule Analytics and Recommendations

Rule identity is split between a logical rule id and immutable rule versions. Trigger Sets must reference exact `rule_id + version` pairs. Once a rule version has been recorded for TESTING or ACTIVE evidence, semantic fields such as formula, thresholds, inputs, boundary behavior, stale-data behavior, missing-data behavior, and output semantics must not be edited in place. Any material change creates a new version and preserves historical reproducibility.

Recommendations are audited experiment proposals. The lifecycle is `Observation -> Hypothesis -> Recommendation -> Candidate Trigger Set -> TESTING -> Evaluation -> Decision`. A recommendation may create or reference a TESTING candidate set through explicit reviewed code/config, but it must never promote TESTING to ACTIVE, mutate ACTIVE, or call execution. Analytics evaluates performance at Trigger Set version level, not by declaring an isolated trigger profitable.

Dashboard Rule Detail and Analytics pages are read-only projections over persistence. They may link rules, exact versions, trigger sets, recommendations, and supported evidence counts. They must not evaluate triggers, approve risk, place/cancel orders, expose arbitrary SQL, expose `.env`, or render secrets.

Analytics facts must preserve evidence source. Exchange-derived accounting and
TEST-lane simulation facts are not interchangeable; baseline comparisons are
available only for like-for-like accounting samples.

The production Sets and Trigger Catalog UI is backed by a registry read model
over `rule_definitions`, `trigger_set_versions`, and
`trigger_set_memberships`. The projection exposes exact Set Version identity,
exact Trigger Version membership, trigger parameters, readable factual
formula/logic metadata, exact Used In relationships, and factual version
history. Trigger Catalog includes only records whose canonical rule type is
`trigger`; strategy, risk, and context components remain members of Set
Versions but are not presented as independent trigger catalog rows. Multiple
ACTIVE sets for the same symbol/timeframe are reported as an integrity error
rather than silently collapsed to one winner. Legacy or incomplete registry
metadata is surfaced as unavailable/unknown, not replaced by dashboard
fixtures. Used Trigger Versions remain immutable/read-only and the dashboard
does not expose edit APIs.

Messages and System History consume existing runtime/read-model facts. Message
producers are limited to meaningful factual operational events, such as
operator control results or backend service failures. Research producers are
limited to factual state transitions such as backtest failure, Demo blocked, or
decision needed; they must not synthesize performance or price monitoring.
Repeated equivalent events may use a dedupe key to avoid flooding user-facing
storage. System History uses deterministic sections, bounded row counts,
explicit truncation markers, and allowlist-style field selection from existing
stores and read models.

Daily Loss is an accounting-backed new-entry gate owned by the futures runtime
and accounting persistence, not by the UI. When enabled in the current
`TradingRulesVersion`, ACTIVE opening intents are evaluated against the
current UTC-day realized net P&L from account-authoritative closed futures
trades only. TEST simulation, Research Demo, and backtest rows must not affect
the ACTIVE daily-loss latch. The day baseline is stable once established: use
the earliest eligible equity snapshot after UTC day start when available, or a
safe first-evaluation ACTIVE account equity value persisted for that day;
otherwise fail closed for new entries only. A reached threshold latches for the
rest of the UTC day and survives restart. Protective exits, manual closes,
Close All, and reconciliation remain outside this gate.

The registry is code-first. New Trigger Versions and Set Versions are introduced
through reviewed code, not UI CRUD. Re-registering an existing exact
`rule_id + version` or `set_id + version` is idempotent only when the stored
hash and semantic payload match; any changed semantic definition under the same
version fails closed and requires a new version. Set `composition_hash` excludes
lifecycle status so explicit status transitions do not mutate composition
semantics.

Portfolio is a read model over ACTIVE/live Demo portfolio state, not a second
portfolio engine. It reads persisted account equity snapshots, futures position
records, closed-position accounting records, and local operator state. `Total`
means the latest authoritative account equity snapshot. `Available` means the
latest account available margin/capital usable for new entries. `In positions`
and row `Value` use open-position entry notional so leveraged exposure is not
confused with free capital. `Realized P&L today` is net closed-trade P&L for
the current UTC day; aggregate `Unrealized P&L` is backend/accounting supplied
from the latest equity snapshot. Missing mark/current-price data is unavailable
rather than recomputed in frontend. Portfolio queries filter to ACTIVE/exchange
evidence sources and exclude Research Demo, Backtest, and TEST simulation facts.

ACTIVE account equity snapshots are operational freshness evidence, not signal
evidence. The futures runtime refreshes the Bybit Demo account state once per
normal completed-candle cycle before signal evaluation and persists the snapshot
atomically to the accounting store. No-signal cycles still update account
freshness when the private read succeeds. Refresh failure must retain the
previous factual snapshot, degrade/unavailable readiness as appropriate, and
must not create orders, reset balances to zero, or mix Research/TEST simulation
facts into the ACTIVE Portfolio read model.

Canonical registry bootstrap is a shared service-layer startup concern. It writes only configured RuleDefinitions, immutable TriggerSetVersions, memberships, and Recommendations into the intended runtime SQLite database before runtime/dashboard services open their stores. Bootstrap order is rule/trigger versions first, Set Versions second, then explicit lifecycle/status reconciliation. Runtime evidence remains separate: bootstrap must not create candle lifecycles, orders, fills, performance history, P&L, or synthetic analytics rows. If an existing exact rule/set/recommendation identity has different semantics, bootstrap fails closed through persistence immutability instead of silently mutating history.

## Intraday Experiment Governance

TriggerTrade's primary strategy class is intraday systematic trading. Evidence
is accumulated from frequent completed-candle observations and evaluated at
Trigger Set version level, not as an isolated trigger profit claim.

`EvidenceReadiness` is separate from `TriggerSetStatus`. A set may remain
`TESTING` while its readiness projection moves through `COLLECTING`, `EARLY`,
`REVIEW_READY`, `STRONG_EVIDENCE`, `INSUFFICIENT_DIVERSITY`, or `BLOCKED`.
Readiness is a deterministic backend projection over persisted runtime evidence
and a versioned governance policy. It is not an automatic promotion criterion.

Recommendation actions are advisory only: continue testing, extend sample,
create a new version, compare with baseline, reject candidate, or mark ready for
human promotion review. Governance code must not mutate ACTIVE sets, promote
TESTING sets, call execution, or invent unsupported P&L/regime/accounting
metrics.

Local operator pause state is persisted separately from trading rules. The
dashboard may request confirmed `TRADING_PAUSED` / `TRADING_ENABLED` changes,
but new ACTIVE execution is blocked in the execution service before submission.
TEST lane evidence collection, analytics, market-data processing, and
reconciliation of existing orders remain allowed while paused.

## Perpetual Futures Architecture

The next product direction is an automated event-driven intraday perpetual
futures bot. Perpetual futures are introduced for LONG/SHORT symmetry,
intraday execution, fee-aware testing, and directional flexibility. They are
not introduced as a high-leverage premise; the default leverage target is `1x`
unless explicit reviewed configuration says otherwise.

Futures domain intent is position-oriented, not exchange-side-oriented:
`OPEN_LONG`, `CLOSE_LONG`, `OPEN_SHORT`, and `CLOSE_SHORT`. Adapter-level
Bybit `Buy` / `Sell` mapping is contained inside execution. The position state
machine is explicit:

```text
FLAT -> LONG
LONG -> FLAT
FLAT -> SHORT
SHORT -> FLAT
```

Direct `LONG -> SHORT` or `SHORT -> LONG` transitions fail closed. Any future
flip support must decompose into audited close plus new entry.

Bybit Demo USDT perpetuals use V5 `category="linear"` for `BTCUSDT`
`LinearPerpetual` contracts. Futures execution remains demo-only:
`https://api-demo.bybit.com`, no mainnet, no inverse/options, no transfer,
withdrawal, or generic private endpoint escape hatch. Spot execution history
remains backward-readable, but the new futures execution audit path is stored
separately.

Market regime is a first-class versioned context contract with labels
`STRONG_DOWNTREND`, `DOWNTREND`, `SIDEWAYS`, `UPTREND`, and
`STRONG_UPTREND`, plus explicit `UNKNOWN` and `INSUFFICIENT_DATA` states.
`CTX-REGIME@0.1.0` is implemented in the market-data boundary as a
deterministic 30-completed-1m-candle classifier using window return,
volatility-normalized trend and directional persistence. It classifies observed
state only; it must not create signals, intents, risk approvals or orders.
Runtime persists the context before trigger/strategy evaluation and links the
context id/state into lane lifecycle and strategy-decision provenance.
Unsupported, insufficient or malformed regime data is explicit and must not be
silently treated as `SIDEWAYS`.

Position lifecycle state is persisted separately from order lifecycle state.
`FuturesPositionStore` is the backend authority for open/closing/closed/unknown
positions, protective-exit plans, rule snapshots, set attribution, close
reasons, and closed-position accounting links. Order records remain immutable
execution facts; accounting consumes linked open/close fills under the stable
position trade id.

Protective exits are runtime-managed in `protective-exit-v1`. They monitor
backend mark-price facts and submit reduce-only closing orders through
`FuturesExecutionService`; dashboard/read models do not own TP/SL logic and do
not expose order actions. Manual close and close-all are backend service
contracts with persisted audit events. Pause blocks only new ACTIVE entries;
TP/SL, manual close, close-all, reconciliation, TEST lane, and analytics
continue.

Futures risk requires position-state validity, maximum position/exposure,
configured leverage, available margin, margin/position mode validity,
liquidation-buffer capability, duplicate intent checks, churn/cooldown hooks,
operator pause, session/daily loss capability hooks, mandatory TP/SL plans,
one net position per symbol, position sizing by configured available-capital
percentage, inclusive risk/reward validation, and a deterministic net-edge
gate. Expected net edge is:

```text
expected gross price move
- entry fee
- exit fee
- spread
- estimated slippage
- relevant funding
= expected net edge
```

If expected gross move or required cost/funding inputs are unsupported, trade
eligibility fails closed. Dashboard views may display backend-provided futures
fields, but they do not calculate P&L, net edge, risk, or place orders.

## Versioned Trading Rules Registry

`TradingRulesVersion` is the backend authority for current futures money/risk policy and is intentionally separate from `TriggerSetVersion`. Trigger Sets choose exact signal/strategy/context rule membership. Trading Rules choose resolved position sizing, fixed take-profit, stop-loss, risk/reward, optional net-edge gate, leverage, portfolio caps, direction filters, coin enablement and cost assumptions for new entries.

Trading rules versions are immutable rows. The current live rules selection is a separate pointer, so creating `v2` or later does not mutate `v1`. Shared startup bootstrap creates only the factual initial `v1` when the DB has no current rules pointer; if a current pointer already exists, bootstrap leaves it unchanged. A conflicting immutable `v1` definition fails closed rather than rewriting history.

Production futures runtime resolves the current rules version before sizing and risk. New positions must carry `rules_version_id` and a resolved rule snapshot. Existing positions and closed trades retain their original rules attribution even after the current pointer advances. Dashboard/read models may display those persisted facts later, but they must not compute or create trading rules.

The local dashboard exposes a thin Rules API over this same registry. `GET` reads the current version, newest-first history, and exact historical detail. `POST /api/rules/versions` accepts a submitted draft with the expected current identity, validates it through `TradingRulesService`, creates a new immutable version when semantics change, and atomically advances the current pointer. A stale browser edit receives a conflict response with the actual current version identity; the dashboard must not silently branch from stale state.

Rules UI state is local draft state only. It may render backend fields and submit the draft, but it must not infer trading semantics, fabricate versions, or mutate historical versions. The historical detail view resolves the requested version exactly and is read-only.


## Bybit Linear Instrument Catalog

Instrument metadata is a backend catalog boundary, not dashboard logic and not strategy logic. `InstrumentCatalogService` fetches Bybit public V5 instrument pages for `category="linear"`, normalizes them into cached `FuturesInstrument` records, and persists them through `InstrumentCatalogStore` before runtime or Rules code consumes them.

The product filter for tradeable symbols is intentionally strict: USDT quote/settle coin, `LinearPerpetual`, status `Trading`, positive tick size, quantity step, minimum quantity, maximum limit-order quantity, and leverage bounds. Instruments outside that product class may be retained only as rejected catalog rows with an exclusion reason; they are not valid for new entries.

Refresh is all-or-nothing from the perspective of the live cache. The service fetches every paginated page, detects cursor loops, deduplicates by symbol, computes a catalog hash, and only then replaces the persisted normalized catalog. If a public refresh fails, the previous valid cache remains authoritative and staleness/error metadata is exposed.

New TradingRulesVersion creation validates enabled coins through this catalog service. Historical rules versions remain immutable if an instrument later becomes unavailable. New futures entries resolve instrument metadata from the cached catalog before sizing, risk, and execution. Open positions pin an immutable instrument metadata snapshot, so close/reconcile/TP/SL management can use the snapshot even when current catalog status blocks new entries.

## Futures Accounting

Futures accounting is a separate backend layer between execution facts and
analytics aggregation. Execution records exchange lifecycle events; accounting
converts explicit fill, fee, funding, valuation and equity facts into
deterministic financial records; analytics may aggregate those records in a
later lifecycle unit.

Accounting version `futures-accounting-v1` supports Bybit Demo `BTCUSDT`
USDT linear perpetuals. Quantity is an absolute base/contract quantity and
direction determines P&L sign. For linear USDT contracts:

```text
LONG gross P&L  = (exit_vwap - entry_vwap) * quantity * contract_size
SHORT gross P&L = (entry_vwap - exit_vwap) * quantity * contract_size
```

For the current BTCUSDT linear contract, `contract_size` defaults to `1`
unless exchange metadata provides a different Decimal value. VWAP is
`sum(fill_qty * fill_price) / sum(fill_qty)` and fails closed for missing,
zero, or mixed-symbol facts.

Actual fees are stored as positive costs and subtracted from closed net P&L.
Actual funding is stored separately as a signed account impact and added to
net P&L. Estimated fees, funding, and slippage remain distinct from actual
accounting facts. Because gross P&L uses actual fill prices, actual slippage is
stored as diagnostic attribution and is not subtracted again in v1.

Unrealized P&L uses a recorded valuation price, with mark price preferred for
futures. Equity and drawdown are computed only from persisted real snapshots:
running peak, current equity, absolute drawdown, drawdown percent, and maximum
drawdown. Dashboard pages may only render accounting-backed persisted values;
they must not recompute financial results in HTML or JavaScript.

## Futures Performance Analytics

Performance analytics sit above deterministic accounting facts. The strategy
performance unit is a Trigger Set Version, not an individual trigger. Trigger
level views may explain contribution or filtering behavior, but they must not
label a single trigger profitable when results depend on full Trigger Set
membership, strategy, risk and execution context.

Analytics may group accounting-backed closed trades by Trigger Set version,
symbol, direction, market regime when available, and time window. Baseline
comparison between TESTING and ACTIVE sets is valid only over overlapping
closed-trade periods; missing overlap or missing sample is reported as
unavailable, not inferred.

Core performance metrics are backend-computed from closed trades: wins,
losses, win rate, net P&L, expectancy per trade, profit factor, fees, funding,
fees as percent of gross profit, average duration, and LONG/SHORT breakdowns.
Gross profit/loss are derived from accounting `gross_pnl`; profit factor and
winner/loser averages use signed net trade outcomes.
Max drawdown is used only where accounting-backed drawdown is available for
the relevant scope. The dashboard renders these backend values without
financial arithmetic.

## Historical Replay

Historical replay is an internal evidence path for Trigger Set Versions, not a
general-purpose backtesting platform. It consumes Bybit Demo public historical
`category=linear` BTCUSDT completed 1m candles, validates ordering, duplicates,
gaps, completion state and source metadata, then replays the existing runtime
pipeline:

```text
historical completed candle
        -> CTX-REGIME@0.1.0
        -> pinned Trigger Set / Rule Versions
        -> existing strategy contract
        -> futures risk
        -> historical futures simulator
        -> futures-accounting-v1
        -> performance analytics
        -> BacktestRun evidence
```

Backtest evidence uses source `BACKTEST` and must not be merged silently with
exchange fills or continuous TEST-lane simulation. A run records exact set,
rule, regime, strategy, risk, simulator, accounting, cost, data-source,
timeframe, period, warmup, cache hash and parameter versions. Completed run
facts are immutable; rerunning the same exact inputs must be idempotent, while
semantic mismatch for the same identity fails closed.

No-lookahead is mandatory. A decision at candle `t` may use only candles
completed at or before `t`; simulated fills can occur no earlier than the next
completed candle. Funding support in replay v1 is explicit: the simulator
blocks entries whose modeled holding interval crosses a funding timestamp until
historical funding attribution is implemented. Dashboard analytics may display
historical runs and comparisons, but remains read-only and must not synthesize
runtime evidence, mutate rules, promote sets or call execution.
