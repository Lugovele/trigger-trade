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

Order lifecycle keeps the same safety shape as Spot: reserve before submit,
stable client order id, no blind retry after timeout, `UNKNOWN` for ambiguous
state, explicit reconciliation, and cancellation/recovery allowed while trading
is paused.

No futures bootstrap or dashboard path may call transfer, withdrawal,
cancel-all, close-all, leverage escalation, or mainnet endpoints. Emergency
close semantics remain out of scope.
