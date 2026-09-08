# TriggerTrade Execution and Safety

## Purpose

Execution is the highest-risk technical layer. A timeout, duplicate retry, stale state, precision error, or bad reconciliation path can create unintended positions even when strategy logic is correct.

## Safety baseline

1. Paper mode is the development default.
2. Live mode requires explicit configuration.
3. API credentials come from environment variables or a local ignored secret store.
4. Withdrawal permissions are not required by the bot.
5. Use minimum exchange API permissions needed for trading and account-state reads.
6. Order submissions are auditable without logging secrets.
7. A kill switch must exist before live operation.
8. Risk checks cannot be bypassed by trigger, strategy, UI, retry handler, or exchange adapter.

## Order lifecycle

Minimum conceptual states:

```text
CREATED
SUBMITTING
SUBMITTED
PARTIALLY_FILLED
FILLED
CANCEL_PENDING
CANCELLED
REJECTED
UNKNOWN
```

Ambiguous exchange state must be represented explicitly rather than guessed.

## Idempotency

Before submitting an order, the system must know whether the same intended action was already submitted.

Use stable internal intent/order identifiers and exchange client-order identifiers where available.

A retry after timeout must not blindly submit a second order.

## Exchange uncertainty

Examples:

- network timeout after `place_order`;
- response lost after exchange accepted the order;
- local process crash after submission;
- partial fill;
- websocket disconnect;
- REST/websocket temporary disagreement.

Required behavior:

- persist intent before external submission where practical;
- reconcile against exchange state;
- represent unresolved state as `UNKNOWN`;
- do not submit replacement orders merely because a response was not received.

## Precision and limits

Validate before submission:

- price tick size;
- quantity step size;
- minimum quantity;
- minimum notional;
- supported order types;
- available balance;
- asset precision.

Do not rely on binary floating-point equality for money-sensitive comparisons.

## Kill switch

Minimum behavior:

- block new trading;
- allow state reconciliation;
- visibly indicate trading-disabled state.

Closing positions automatically should require a separately defined emergency rule.

## Restart recovery

On restart:

1. load persisted local state;
2. query relevant exchange orders/positions;
3. reconcile differences;
4. mark uncertain state explicitly;
5. resume new trading only when critical state is consistent.

## Paper/live parity

Paper mode should exercise the same trigger, strategy, risk, intent, persistence, and UI paths.

Only the execution adapter should differ materially.

## TEST Lane Safety

A TEST lane may evaluate candidate trigger sets against the same completed market data as ACTIVE, but it must remain isolated from exchange order placement. TEST records can include simulated analysis outcomes and persisted audit evidence; they cannot call Bybit private/order endpoints, transfer funds, change leverage, or affect ACTIVE paper/live state.

Execution idempotency must include lane and trigger-set identity so a TEST decision cannot collide with or replay an ACTIVE execution lifecycle.

## Perpetual Futures Safety

Futures execution is separated from the existing Spot execution path. The first
supported contract product is Bybit Demo `BTCUSDT` USDT perpetual with
`category="linear"` and Demo REST base URL `https://api-demo.bybit.com`.

Before any futures order submission the execution boundary must validate:

- approved futures risk decision;
- `TRADING_MODE=paper` and live trading disabled;
- Demo endpoint only;
- `category="linear"` only;
- position transition validity;
- configured leverage, default `1x`;
- available margin;
- margin mode and position mode validity;
- precision, tick, step, minimum quantity, and minimum notional;
- duplicate intent/client order id;
- net-edge evidence;
- operator pause for new ACTIVE entries.

The continuous futures runtime must not force the legacy `LOCAL_PAPER`
execution venue. ACTIVE uses the futures execution service and Bybit Demo
linear adapter; TEST uses the isolated local simulator and records
`evidence_source=test_simulation`. Operator pause is enforced at the ACTIVE
execution boundary before any new Bybit order submission, while reconciliation
and TEST simulation remain allowed.

Order lifecycle keeps the same safety shape as Spot: reserve before submit,
stable client order id, no blind retry after timeout, `UNKNOWN` for ambiguous
state, explicit reconciliation, and cancellation/recovery allowed while trading
is paused.

No futures bootstrap or dashboard path may call transfer, withdrawal,
leverage escalation, or mainnet endpoints. Backend manual close and close-all
are reviewed execution capabilities only: they submit reduce-only closing
orders through the futures execution boundary, persist audit events, and do
not expose dashboard order controls.

Every new ACTIVE futures position must pin `protective-exit-v1` take-profit
and stop-loss plans before execution. The initial implementation is
runtime-managed rather than exchange-native because the current Bybit adapter
does not expose a reviewed TP/SL endpoint contract. Closing triggers use mark
price semantics: LONG closes at TP when mark price is greater than or equal to
TP and at SL when mark price is less than or equal to SL; SHORT closes at TP
when mark price is less than or equal to TP and at SL when mark price is
greater than or equal to SL. All protective, manual, and close-all exits use
reduce-only close actions and remain allowed while entries are paused. Runtime
startup reconciles unresolved executions and persisted open/unknown positions
before evaluating new entry decisions; unresolved disagreement for a symbol
continues to fail closed instead of submitting a blind duplicate.

## Trading Rules Runtime Safety

Futures runtime resolves the current `TradingRulesVersion` before creating an ACTIVE opening intent. The resolved rules snapshot is persisted with the position and includes the rules version id, sizing inputs, TP/SL percentages, leverage, R/R, optional net-edge state, cost assumptions, direction mode and account-capital denominator source. New openings without a rules version fail closed.

The current rules pointer is mutable; the rules version rows are not. Startup bootstrap may create the factual initial version on an empty DB, but it does not replace a later current version or silently change immutable semantics. Disabled optional gates are recorded as disabled and excluded, not represented by magic limits.

Dashboard Rules writes use the protected backend `Save as New Version` route. The request must carry the browser's expected current rules identity; if the backend pointer has advanced, the save fails with a conflict and does not create a new version. A Rules save never submits, cancels, reconciles, or enables exchange orders.


## Instrument Catalog Safety

Futures order parameters must be validated against the cached Bybit public USDT-linear-perpetual catalog before a new entry is submitted. The catalog source is `GET /v5/market/instruments-info` with `category=linear`; it uses no private credentials and cannot create orders.

Price normalization is Decimal and purpose/direction aware. Protective rounding must not overstate reward or increase planned risk: LONG TP rounds down to tick, LONG SL rounds up, SHORT TP rounds up, and SHORT SL rounds down. Quantity normalization rounds down to `qtyStep` and rejects quantities below `minOrderQty`, above limit `maxOrderQty`, or below `minNotionalValue` when price is known. Configured leverage above exchange max is rejected; it is not clamped.

Catalog refresh failures preserve the last valid cache. If no valid catalog exists, new entries fail closed. Existing positions are managed from their persisted instrument snapshot when possible, so refresh outage or later suspension blocks new entries without silently orphaning close/reconciliation paths.

The dashboard catalog refresh button calls the backend catalog service only. The browser receives normalized public catalog state and tradeable symbols, not Bybit URLs, credentials, request headers, or raw private data.

## Messages and History Export Safety

Dashboard Messages are persisted separately from raw runtime logs. They are
short user-facing operational facts with stable ids and bounded reads. Read
state updates require the protected local dashboard token, reject malformed or
unknown ids, and do not call trading, execution, reconciliation, exchange, or
configuration-changing code.

The System History export endpoint is backend-built, protected, and does not
accept file paths, shell commands, SQL snippets, or raw log-file selectors from
the browser. It exports bounded structured text from existing read models and
audit stores, marks truncated sections explicitly, and omits Research data
unless factual Research backend history exists. Export sanitization excludes
API keys, API secrets, authorization headers, cookies, session or CSRF tokens,
`.env` material, raw exchange payloads, and private credentials. Auditing the
export action records only action/result metadata, not the exported payload.

## Research Safety

Research backend state is non-execution product state unless a separately
reviewed Research Demo execution bridge is present. Creating Research,
selecting runs, archiving, and requesting comparison must not submit, cancel,
amend, or reconcile orders and must not mutate ACTIVE positions or daily-loss
latches.

Research Demo start fails closed by default. It remains blocked when
Research-specific exchange isolation is unavailable, when selected rules use
Dynamic TP, or when selected rules require Daily Loss before isolated Research
accounting exists. The service must not substitute Fixed TP, borrow ACTIVE
daily-loss accounting, use production credentials, enable mainnet, or present a
fake RUNNING Demo state.

Research backtests also fail closed when the pinned Trading Rules Version uses
semantics the current historical replay engine cannot fully honor. The
dashboard may submit bounded plan parameters, but not raw candle arrays or
filesystem paths; replay inputs are backend-owned.

Make Active is not an execution or promotion path in this foundation. A Make
Active request records a blocked decision with a factual reason and leaves
ACTIVE Trigger Sets, Trading Rules, positions, orders, and execution state
unchanged.

## Demo Readiness and Heartbeat

Sustained Bybit Demo operation uses a factual readiness projection rather than
an unconditional running indicator. The read-only readiness contract reports
`RUNNING`, `DEGRADED`, `BLOCKED`, or `UNAVAILABLE` from backend evidence:
database readability, component heartbeat, market-data progress, instrument
catalog freshness, and operator pause state.

Heartbeat rows are persisted by stable component id. A new observation replaces
the previous heartbeat for that component and stores only bounded diagnostic
metadata. Unknown status values and path-like component ids are rejected. A
missing or stale heartbeat is degraded/unavailable evidence, not success.

The optional Demo soak harness is explicit opt-in through
`RUN_TRIGGERTRADE_DEMO_SOAK=1`. It runs bounded cycles only against Bybit Demo
linear futures in paper mode, refuses mainnet and Spot configuration, and
records heartbeat evidence before and after the run. It does not enable
Dynamic TP, does not introduce SHORT alpha, and does not perform destructive
production testing.

Each normal futures runtime cycle performs at most one ACTIVE account refresh
using the existing Bybit Demo private account read path. The refresh is
account-scoped rather than per-symbol, persists the canonical equity snapshot
used by Portfolio and System History, and has no order submission,
cancellation, amendment, or close authority. If the read fails, the previous
snapshot remains the latest factual Portfolio evidence, account readiness
degrades or becomes unavailable, and new entries cannot proceed with fabricated
fresh account state.

## Futures Accounting Safety

Futures accounting consumes explicit execution/fill/funding/equity facts and
does not create orders. It must not infer actual fills from requested quantity
or from a terminal order status unless the source is an explicit local paper
simulation. Exchange-discovered fill and fee events require stable event ids so
restart/reconciliation cannot duplicate financial facts.

Closed-trade net P&L subtracts actual positive fee costs and adds signed actual
funding impact. Actual slippage is recorded as diagnostic evidence relative to
requested/reference price, but it is not subtracted again because gross P&L is
already based on actual fill prices. If fee currency differs from settlement
asset and no explicit conversion is available, accounting fails closed.

Unrealized P&L records its valuation source. Missing or stale mark/valuation
data is unavailable, not zero. Equity drawdown uses real persisted equity
snapshots only; synthetic series are forbidden.

Daily loss limit enforcement is accounting-backed for new ACTIVE entries. When
`daily_loss_limit_enabled=true`, futures runtime evaluates only actual opening
intents against current UTC-day realized net P&L from account-authoritative
closed futures trades, excluding TEST simulation, Research Demo, and backtest
rows. The daily baseline is persisted and stable for the UTC day: it comes from
the earliest eligible equity snapshot after UTC day start, or from a safe
first-evaluation ACTIVE account equity value when no snapshot exists. Missing
or uncertain accounting/baseline state fails closed for new entries only.

The threshold is inclusive and latches for the rest of the UTC day once
reached, surviving restart and operator Resume. The latch resets only with the
next UTC day. Existing positions still run protective TP/SL monitoring,
manual close, Close All, and reconciliation; daily loss does not force close or
alter reduce-only close semantics. `max_positions_per_coin`, when enabled, is
constrained to `1` because the approved lifecycle invariant is still one net
position per symbol; pyramiding requires a later reviewed change.

## Portfolio Operator Contracts

The Portfolio dashboard may request Pause Entries, Resume Entries, Close One,
and Close All only through protected local backend POST contracts. Pause and
Resume update persisted operator state and write audit rows. Close One and
Close All require an attached futures lifecycle execution bridge; without that
bridge the dashboard returns an explicit service-unavailable failure and audits
the failed operator action instead of pretending that a reduce-only close was
submitted.

Close One must identify a stable `position_id` and symbol. Close All is scoped
to ACTIVE/live Demo portfolio positions and must not include Research Demo,
Backtest, or TEST simulation evidence. The browser never receives Bybit
credentials or calls exchange/order endpoints directly.
