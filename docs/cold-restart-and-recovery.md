# Cold Restart and Recovery Verification

Cold restart means the TriggerTrade runtime process is fully stopped, the
configured SQLite runtime database remains on disk, and a new process starts
with no in-memory state from the previous run.

## Persistence Classes

The following state must survive exactly and must not be reconstructed from the
latest code when a persisted exact identity exists:

- immutable Trading Rules versions and the current Rules pointer;
- immutable Trigger definitions, Set versions, memberships, transitions, and
  active Set pointer;
- Research entities, pinned Set/Rules identities, selected runs, archive state,
  decisions, and Make Active evidence;
- orders, fills, positions, closed trades, accounting facts, operator actions,
  Messages/read state, Audit Trail rows, and Daily Loss latch/baseline state.

The following state must be rehydrated after restart before it is considered
fresh runtime truth:

- market data progress;
- account and Portfolio snapshot freshness;
- runtime heartbeat;
- readiness;
- exchange reconciliation;
- instrument catalog freshness when the cache requires refresh.

Persisted heartbeat, readiness, account, market, and catalog rows may be useful
historical evidence, but they are not a green startup signal by themselves.

## Startup Order

A safe cold start opens the configured DB, runs idempotent registry bootstrap,
loads the exact persisted active Set + current Rules pair, loads operator state,
detects checkpoint continuity, recovers any completed-candle gap, refreshes
account data, reconciles open or unknown execution state where required, and
only then allows readiness to become RUNNING.

If the operator had paused entries before shutdown, restart must preserve that
pause. Reconciliation and protective/close paths may continue according to the
execution contract, but new ACTIVE entries remain blocked until the operator
explicitly resumes and all required freshness/reconciliation gates pass.

## Checkpoint Recovery

The ACTIVE futures lane checkpoint in `runtime_lane_state` is the source of
truth. When recent candles no longer include the next expected completed candle,
the runtime fetches bounded Bybit Demo linear historical klines, validates
complete one-minute continuity, processes missing completed candles oldest to
newest, and advances the checkpoint only after the corresponding lane lifecycle
row is durable. Large recoverable gaps are streamed as repeated bounded
historical batches; each request and in-memory batch remains limited, while
total recovery may span as many batches as needed when Bybit supplies complete
data and every batch advances the checkpoint.

Recovered historical entry opportunities are persisted as recovery evidence and
are not allowed to submit late stale orders. Normal fresh execution resumes only
after continuity is restored. Missing, duplicate/conflicting, out-of-order,
malformed, repeated/non-progressing, unavailable, or checkpoint-ahead evidence
fails closed and keeps readiness non-green.

## Duplicate Prevention

Cold start and second restart must not create duplicate immutable versions,
Research rows, order identities, fills, position rows, operator actions, or
Messages. Recovery may append new factual audit/lifecycle evidence and may
rehydrate an unresolved order with exchange status, but it must not replace
semantic identities or submit duplicate orders.

## Verification Evidence

The cold-restart verification suite captures a pre-restart fingerprint, creates
a verified pre-test backup, rebuilds runtime objects against the same DB,
exercises checkpoint recovery and account rehydration, verifies a post-restart
backup, runs the DB integrity audit, and performs a second fresh runtime object
start to prove idempotency. Synthetic fixtures cover open-position
reconciliation, Daily Loss latch persistence, Make Active persistence, Rules
version pinning, Set persistence, Messages/read state, and failure cases without
placing real orders.

Operational Bybit Demo proof should additionally stop any confirmed
TriggerTrade runtime process, wait long enough to create a small completed
candle gap, cold start using the approved Demo linear configuration, verify
checkpoint recovery, account refresh, Portfolio freshness, readiness, Audit
Trail/System History evidence, and confirm that no startup order was submitted
before recovery and reconciliation completed.
