# Data Integrity and Retention

This document defines TriggerTrade's current persistence integrity and
retention policy. It is intentionally conservative: this unit enables auditing,
classification, and query/index hardening, but no automatic destructive
retention.

## Integrity Model

The configured runtime SQLite database is the persistence boundary for local
Demo operation. Domain stores remain canonical owners:

- `TradingRulesStore`: immutable Trading Rules versions, current pointer,
  coin rules, and usage attribution.
- `TriggerSetStore`: immutable Trigger definitions, Trigger Set versions,
  memberships, recommendations, and Set transitions.
- `ResearchStore`: Research identities, pinned Set/Rules pair, Backtest/Demo
  runs, selections, decisions, archive state, and Make Active evidence.
- `FuturesExecutionStore`: futures order lifecycle and idempotency evidence.
- `FuturesPositionStore`: open/closed positions, position events, and Close All
  operations.
- `FuturesAccountingStore`: fills, funding, closed trades, and equity
  snapshots.
- `OperatorStateStore`: current operator state and operator action/state audit.
- `MessageStore`: user-facing operational Messages and read state.
- `TraceStore`: trigger/strategy/risk traces and canonical `audit_events`.
- `RuntimeStore`: lane checkpoints, lane lifecycles, market regime evidence,
  and component heartbeats.
- `InstrumentCatalogStore`: reconstructable Bybit public instrument cache.

The read-only integrity audit checks SQLite integrity, SQLite foreign-key
health, required orphan relationships, duplicate semantic identities, active
pair coherence, enum values, timestamp interpretability, row counts, retention
class, and query plans. It does not dump record payloads, print secrets, mutate
semantic state, or repair data automatically.

## Retention Classes

| Class | Meaning | Automatic deletion now |
| --- | --- | --- |
| `PERMANENT_EVIDENCE` | Historical or causal evidence needed for audit, replay, attribution, or recovery. | No |
| `LONG_TERM_OPERATIONAL` | Operational state/history useful for recovery and diagnosis but potentially eligible for future archival/downsampling. | No |
| `RECONSTRUCTABLE_CACHE` | Data that can be refetched or rebuilt from authoritative external/source state. | No |
| `EPHEMERAL_RUNTIME` | Current liveness markers or transient runtime state. | No |

## Retention Matrix

| Category | Retention | Growth | Rationale | Future action |
| --- | --- | --- | --- | --- |
| Rules versions/current history | `PERMANENT_EVIDENCE` | Low | Required for exact trading attribution. | Keep forever. |
| Trigger versions | `PERMANENT_EVIDENCE` | Low | Immutable signal definition history. | Keep forever. |
| Set versions/memberships/transitions | `PERMANENT_EVIDENCE` | Low | Exact Set composition and active history. | Keep forever. |
| Research entities/decisions | `PERMANENT_EVIDENCE` | Medium | Evidence behind archive/Make Active decisions. | Keep forever. |
| Backtest/Demo run metadata | `PERMANENT_EVIDENCE` | High | Research evidence and comparison inputs. | Future archive of bulky run details only after review. |
| Orders/client order ids | `PERMANENT_EVIDENCE` | Medium | Execution idempotency and exchange traceability. | Keep forever. |
| Fills/funding/closed trades | `PERMANENT_EVIDENCE` | Medium | Accounting and realized P&L source. | Keep forever. |
| Positions/position events | `PERMANENT_EVIDENCE` | Medium | Exposure/reconciliation history. | Keep forever. |
| Operator actions/state audit | `PERMANENT_EVIDENCE` | Medium | Human action traceability. | Keep forever. |
| Audit Trail | `PERMANENT_EVIDENCE` | High | Cross-domain causal index. | Future archival partitioning only, not deletion. |
| Messages | `LONG_TERM_OPERATIONAL` | Medium | User-facing operational awareness. | Future resolved-message archive may be reviewed. |
| Equity snapshots | `LONG_TERM_OPERATIONAL` | High | Portfolio, readiness, Daily Loss, and account history. | Future downsampling after accounting review. |
| Runtime recovery summaries | `LONG_TERM_OPERATIONAL` | Medium | Restart/recovery diagnosis. | Keep long term. |
| Runtime lane checkpoints | `LONG_TERM_OPERATIONAL` | Low | Restart source of truth. | Keep latest/current state. |
| Runtime lane lifecycles | `LONG_TERM_OPERATIONAL` | Very high | Per-candle operational evidence. | First candidate for reviewed archival/downsampling. |
| Trigger evaluations | `PERMANENT_EVIDENCE` | Very high | Signal trace evidence. | Future archive by time range, not delete silently. |
| Market regime evaluations | `LONG_TERM_OPERATIONAL` | High | Per-candle context evidence. | Future downsampling/archive after review. |
| Instrument catalog cache | `RECONSTRUCTABLE_CACHE` | Medium | Public Bybit metadata can be refetched. | Rebuildable; safe cache refresh only. |
| Heartbeats | `EPHEMERAL_RUNTIME` | Low | Latest component liveness state. | Replaced in place; no retention job needed. |

## Query and Index Strategy

Indexes are justified by growing-table read paths:

- latest equity snapshot: `futures_equity_snapshots(observed_at DESC, snapshot_id DESC)`;
- latest runtime lane lifecycle: `runtime_lane_lifecycles(processed_at DESC)`;
- per-Research Backtest runs: `research_backtest_runs(research_id, created_at DESC)`;
- per-Research Demo runs: `research_demo_runs(research_id, created_at DESC)`.

System History remains bounded at query-call level. It requests recent slices
only and includes truncation markers where applicable; it is not a lifetime DB
dump.

## Repair Policy

Integrity findings are classified by impact:

- `AUTO_SAFE`: reconstructable cache refresh or idempotent index creation.
- `MANUAL_REVIEW_REQUIRED`: retention/archive decisions, timestamp
  interpretation changes, or non-critical support-table anomalies.
- `FATAL_BLOCKER`: dangling active Rules/Set references, missing immutable
  version referenced by trading history, orphaned Research selected runs,
  missing order for a fill, checkpoint regression, or corrupt SQLite integrity.

Semantic history must not be silently repaired. Historical trading, Research,
Rules/Set/Trigger, operator, accounting, and Audit Trail evidence must not be
deleted without a separate explicitly approved lifecycle.

## Future Research Scale

For one day of normal Demo/Research accumulation, the likely growth pressure is
runtime lane lifecycle rows, trigger evaluations, market regime evaluations,
audit events, and equity snapshots. Over seven days these become the first
tables to monitor for query-plan and backup-size growth. Over thirty days,
runtime and Research evidence may need reviewed archival/downsampling or
partitioning, but immutable trading/configuration evidence still remains
permanent.

Backups include all persistence classes because they are operational recovery
snapshots. Retention classification describes future data lifecycle policy; it
does not remove anything now.

Cold restart verification relies on this classification: permanent evidence and
long-term operational identities must survive exactly, while ephemeral runtime
freshness such as heartbeat/readiness must be rehydrated before it can become
current operational truth. The DB integrity audit remains read-only after
restart and must not repair, delete, or rewrite semantic history.
