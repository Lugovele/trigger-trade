# Research Launch Acceptance Criteria

## RESEARCH_LAUNCH_HEALTHY

Declare the first Research V1 launch healthy only when all checks below are true.

- The intended Research ID exists in `ResearchConfigurationRegistry/RESEARCH_DEFINITION`.
- The Research mutable state exists in `ResearchRunStore/RESEARCH_MUTABLE_STATE`.
- The pinned Set ID/version in the Research record matches the launch intent.
- The pinned Rules version in the Research record matches the launch intent.
- The Set version exists in both configuration owner-state and `triggertrade_research_set_versions`.
- Every `triggertrade_research_set_memberships` trigger ID/version resolves in `triggertrade_rule_definitions`.
- The expected Research run record exists for the selected mode.
- The durable outbox message exists for the run and is either `PENDING`, healthy `IN_FLIGHT`, or terminal `CONSUMED`.
- While `IN_FLIGHT`, the message has `locked_by`, `locked_at`, `lock_expires_at > now()`, and a nondecreasing stable `attempt_count`.
- The `trading-worker` heartbeat is fresh and `RUNNING`.
- Long Research dispatch records heartbeat detail `research_dispatch_active` and renews the outbox lease.
- Progress advances: Backtest moves to a terminal status, or Demo progress `observed_at` / `elapsed_seconds` advances.
- Trigger evidence appears for the run mode where the runtime currently persists it.
- Position, Portfolio, and Lifecycle records either advance consistently or remain absent because no actionable signal was produced.
- No unexpected `BLOCKED`, `FAILED`, `SUBMISSION_UNCERTAIN`, reconciliation `CONFLICT`, or stale lease state appears.

## Stop-Investigation Conditions

These are investigation triggers only. They are not automatic kill actions.

- `trading-worker` heartbeat is stale for more than the operator-defined freshness window.
- Heartbeat status is `BLOCKED`, `DEGRADED`, or `UNAVAILABLE`.
- Outbox `attempt_count` repeatedly increases for the same Research message.
- Outbox `lock_expires_at <= now()` while Research status is still active.
- An `IN_FLIGHT` message changes `locked_by` unexpectedly during an active run.
- No Research run `updated_at` movement occurs during the expected interval for the mode.
- Backtest remains `RUNNING` without `engine_run_id` or terminal metrics beyond the expected compute window.
- Demo `progress.observed_at` stops advancing while heartbeat and lease remain active.
- Trigger evaluations stop appearing while runtime lane checkpoints advance.
- Set membership cannot resolve to trigger definitions.
- Set resolution cannot produce a downstream direction when trigger evidence says it should.
- Position decision contradicts Set handoff evidence.
- Portfolio rejects or holds without a factual reason.
- Lifecycle has submit authorization but no start gate.
- Lifecycle has a start gate but no submission intent.
- Submission remains `SUBMITTING` or `SUBMISSION_UNCERTAIN` without matching reconciliation evidence.
- Lifecycle reconciliation tombstone remains `UNRESOLVED`, or integrity is `CONFLICT`.
- Close intent remains nonterminal with unresolved children.
- Fills, closed trades, Portfolio accounting day results, and equity snapshots disagree.

## Readiness Boundaries

- Do not start Research until trigger version correction and Rules extraction/readiness are complete.
- Do not infer live trading approval from Research-only metrics.
- Do not use local SQLite backtest evidence as proof of production PostgreSQL lifecycle state.
- Do not treat a missing observability record as zero activity; classify it as missing evidence.
- Do not mutate rows from the launch console. Use read-only transactions and snapshots.
