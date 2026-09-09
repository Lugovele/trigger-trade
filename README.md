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
- `docs/trading-methodology/README.md`

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

Dashboard Sets, Trigger Catalog, and Trigger Detail views are read-only projections over the canonical registry tables. They render exact `set_id + version` and `trigger_id + version` identities, trigger membership, Used In relationships, and factual version history from backend read models rather than frontend fixture rows. Trigger lifecycle status is not separate; lifecycle status belongs to Trigger Set versions. If registry metadata is missing or unavailable, the dashboard shows an explicit unavailable/empty state instead of fabricating a trigger version or historical usage.

The interface intentionally keeps promotion, trigger editing, and rule editing out of the Sets/Trigger surfaces. Financial values are displayed only when persisted by backend accounting.

Trigger and Set changes are code-first. `rule_definitions` stores immutable exact Trigger/Rule Versions with deterministic `definition_hash` values; `trigger_set_versions` stores immutable exact Set Versions with deterministic `composition_hash` values; memberships reference exact `rule_id + version` pairs. Startup bootstrap is idempotent for matching hashes and fails closed when code changes a historical semantic definition without a version bump. See `docs/code-first-trigger-set-workflow.md`.

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

The local dashboard Rules page is wired to this backend registry. It reads the exact current version, lists factual history, opens immutable historical detail, and saves changes only through the protected backend `Save as New Version` contract with stale edit detection. Coin search and catalog refresh go through the backend Bybit linear instrument catalog; the browser never calls Bybit or the database directly.

Daily loss limit enforcement is accounting-backed for new ACTIVE entries when
`daily_loss_limit_enabled=true`. The gate uses current UTC-day realized net P&L
from account-authoritative futures closed trades, excludes TEST/backtest rows,
uses a persisted day baseline from the first eligible equity snapshot or safe
first-evaluation account equity, and blocks inclusively when realized net P&L
is at or below the configured loss amount. Once reached, the block is latched
for the rest of the UTC day and survives restart; existing positions continue
their protective exits, manual closes, Close All, and reconciliation.

## Messages and System History

Dashboard Messages are persisted user-facing operational messages, separate
from raw technical logs. They survive restart, use stable message ids, expose a
factual unread count, and persist read/unread state. Opening the Messages page
loads backend rows and marks the visible unread messages read through a
protected non-trading backend write contract.

The header Copy action requests a backend-built System History export and then
copies the returned text to the clipboard. The export is a bounded, sanitized
technical snapshot for debugging, audit, or AI-assisted analysis. It includes
available portfolio, operator, Rules, Set/Trigger, execution, risk/decision, and
Research facts, including Daily Loss state when available. It never accepts
browser file paths or exposes raw logs, request headers, `.env` contents,
cookies, tokens, or exchange credentials.

Material runtime and operator transitions also write append-only structured
audit events. The audit trail is a compact causal index over existing
authoritative records, not a replacement for orders, fills, positions, Rules,
Sets, Research, Messages, or accounting tables. Events include stable ids,
source/scope, entity identity, Set/Rules/Trigger pins where available, result,
reason code, and sanitized metadata. System History includes the latest
bounded audit slice with truncation markers so an operator can connect
trigger/set evaluation, entry approval or rejection, execution,
reconciliation, Research, recovery, and operator actions without dumping the
whole database.

## Backup and Restore

Operational backups are separate from System History. Backup snapshots preserve
the local SQLite persistence state needed to recover product continuity:
immutable Rules and Trigger Set histories, the active Set + Rules pair,
Research evidence, orders, fills, positions, accounting, operator state,
Messages, and the structured audit trail. System History remains the bounded
human/AI-readable diagnostic export; it is not a restore point.

`BackupService` creates SQLite-consistent snapshots with the SQLite backup API
into ignored local `backups/` files and writes a safe JSON manifest containing
the backup id, UTC timestamp, source DB name, SHA-256 checksum, integrity-check
result, table counts, size, duration, and `contains_secrets=false`. It never
backs up `.env`, credentials, private keys, pytest temp state, or arbitrary
browser-supplied paths. Restore verification copies a verified backup only into
an isolated ignored location such as `.tmp/restore-verification/`, opens it
through the real persistence stores/read models, compares critical identities,
and refuses corrupted, checksum-mismatched, missing, or traversal-style backup
ids.

Restoring a backup that contains open or unknown execution state is not enough
to resume trading. Stop the runtime, verify the backup, restore manually only
after preserving the damaged DB, start in a safe/reconciliation-first posture,
refresh account/market/readiness evidence, reconcile Bybit Demo state, and keep
new entries fail-closed until reconciliation is complete.

## Data Integrity and Retention

TriggerTrade classifies persistence into explicit retention groups instead of
deleting historical evidence to control growth. Rules, Trigger Versions, Set
Versions, Research evidence, orders, fills, positions, accounting, operator
actions, and material Audit Trail events are permanent evidence. Messages,
equity snapshots, runtime recovery summaries, and current operator state are
long-term operational state. Instrument catalog rows are reconstructable cache,
while component heartbeats are ephemeral runtime evidence.

`run_database_integrity_audit()` is a read-only service for SQLite integrity,
foreign-key checks, orphan/dangling reference checks, duplicate semantic
identity checks, enum/timestamp sanity, active pair integrity, row counts,
growth classification, and query-plan review. It prints no record payloads and
does not repair or delete data. Automatic destructive retention is intentionally
not enabled; future archival or downsampling requires a separate reviewed
lifecycle.

## Demo Health and Soak Harness

The dashboard exposes a read-only `/api/readiness` contract with
`RUNNING`, `DEGRADED`, `BLOCKED`, and `UNAVAILABLE` states. The rollup is built
from factual backend checks such as database readability, persisted runtime
heartbeats, latest processed market data, instrument catalog state, and
operator pause state. Missing heartbeat or stale data is reported as degraded
or unavailable rather than a green running state.

Runtime heartbeat rows are persisted by component and updated idempotently, so
restart can recover the latest known liveness state without accumulating an
unbounded log stream. System History includes the readiness rollup and bounded
heartbeat rows for later diagnosis.

On futures runtime restart, the ACTIVE lane checkpoint is the source of truth
for completed-candle continuity. If recent Bybit Demo candles no longer include
the next expected candle, the runtime uses bounded historical linear kline
backfill, validates that every completed 1m candle from checkpoint+1 through
the latest completed candle is present, then replays them oldest to newest.
Recovered historical signals are recorded as recovery evidence but cannot place
late entry orders; normal execution resumes only after the checkpoint catches
up to fresh completed candles. Missing, conflicting, out-of-order, oversized,
or checkpoint-ahead data leaves readiness degraded/blocked instead of silently
skipping candles.

The futures runtime refreshes the ACTIVE Bybit Demo account snapshot once per
normal completed-candle cycle, before signal evaluation. This keeps Portfolio
`Total`, `Available`, `Unrealized P&L`, and account freshness factual during
ordinary no-signal operation without submitting, cancelling, or modifying
orders. Failed account refreshes preserve the previous snapshot and degrade
readiness instead of fabricating fresh values.

A bounded Bybit Demo soak harness is available but never automatic:

```powershell
$env:RUN_TRIGGERTRADE_DEMO_SOAK="1"
python scripts/triggertrade_demo_soak.py
```

The soak harness refuses mainnet, Spot, live trading, non-Demo URLs, and
nonlinear venues. It does not enable Dynamic TP or production SHORT alpha.

## Research Backend

Research is now a backend-owned product entity with persistent records for the
approved lifecycle:

```text
Backtest -> Demo -> Compare -> Decision
```

Each Research record pins an exact Trigger Set identity
(`set_id + set_version`) and an exact `rules_version_id`; the backend does not
accept `current`, `latest`, or display-version-only selectors. Backtest runs
reuse the existing immutable historical replay engine with backend-owned replay
inputs; the browser cannot submit candle arrays as evidence. Research stores
only references to the engine run plus bounded metrics in the Research record.
Raw backtest trades remain in the existing backtest/accounting evidence stores.
If the pinned Trading Rules Version contains semantics the current replay engine
cannot fully honor, such as Dynamic TP or isolated Research Daily Loss,
Research records an unavailable backtest instead of substituting behavior.

Research Demo orchestration is fail-closed in this foundation. Demo start is
blocked unless Research-specific execution and accounting isolation can be
positively established. Dynamic TP rules are not substituted with Fixed TP, and
Rules requiring Daily Loss block Research Demo until isolated Research
accounting exists. Make Active promotes exactly the Research-pinned Trigger
Set Version plus Trading Rules Version atomically when eligibility passes. It
does not rewrite Research evidence or existing positions, and it records
promotion evidence in Research state, Messages, System History, and the audit
trail.


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
