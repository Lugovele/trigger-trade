# First Research Run Checklist

## Before Launch

- Confirm the expected Metrics Library is available in the web app.
- Confirm Research trigger import is complete and the BTC directional trigger correction is complete.
- Confirm Research Set import is complete.
- Confirm Rules extraction/readiness is complete.
- Record intended `research_id`, `set_id`, `set_version`, `rules_version_id`, symbol, mode, period, and operator.
- Verify `ResearchConfigurationRegistry/RESEARCH_DEFINITION` exists or will be created by the launch path.
- Verify `triggertrade_research_set_versions` contains the intended Set version.
- Verify `triggertrade_research_set_memberships` contains the exact intended trigger membership.
- Verify each membership trigger ID/version resolves in `triggertrade_rule_definitions`.
- Verify the `trading-worker` heartbeat is fresh and `RUNNING`.
- Verify `triggertrade_outbox_messages` has no old stuck Research messages for the same Research ID.
- Verify no lifecycle reconciliation tombstones are in `CONFLICT`.
- Prepare a read-only database connection for the operator snapshot script.

## At Launch

- Record the created Research run ID.
- Record the handoff/outbox message ID if the UI/API returns it.
- Capture Snapshot A: Research run summary.
- Capture Snapshot E: worker heartbeat and outbox lease.
- Confirm the Research message is `PENDING`, `IN_FLIGHT`, or already `CONSUMED`.
- Confirm `locked_by`, `locked_at`, and `lock_expires_at` if the message is `IN_FLIGHT`.

## During

- Re-run the compact operator snapshot at a steady interval.
- Confirm progress advances:
  - Backtest: Research run `updated_at` changes and eventually terminal metrics appear.
  - Demo: `ResearchDemoExecution` progress `observed_at` or `elapsed_seconds` advances.
- Inspect trigger evidence:
  - Backtest: local trace store `trigger_evaluations` for the engine run where available.
  - Demo: owner-state `ResearchDemoExecution/research_demo_trigger_evaluation`.
- Verify the exact Set version stays pinned.
- Verify Position evidence only appears after an actionable Set handoff.
- Verify Portfolio evidence only appears after Position approval.
- Verify order spec and submit authorization only appear after Portfolio authorization.
- Verify Lifecycle start gate, submission intent, order events, reconciliation, close, and Set sync advance in order.
- Confirm no unexpected orders are submitted outside the Research/Demo scope.
- Watch blockers:
  - stale heartbeat;
  - lease expiry;
  - repeated `attempt_count` growth;
  - `BLOCKED`/`FAILED`;
  - no progress update;
  - lifecycle uncertainty;
  - accounting mismatch.

## After

- Capture final Research run summary.
- Capture final trigger evidence for the mode.
- Capture final Position/Portfolio/Lifecycle evidence.
- Capture final trades/accounting evidence.
- Confirm terminal Research status is expected.
- Confirm final metrics match the authoritative terminal payload and accounting evidence.
- Confirm no unresolved lifecycle obligations remain.
- Confirm no outbox message for the run remains `PENDING` or expired `IN_FLIGHT`.
- Export comparison/report inputs only after final accounting consistency is verified.

## Known Observability Gaps

- Backtest live per-candle progress is not currently exposed in PostgreSQL while the engine is computing.
- Backtest per-trigger evidence is persisted in the local trace store rather than a canonical PostgreSQL trigger-evaluation table keyed by Research run.
- Set resolution does not currently have a single canonical PostgreSQL row containing trigger vector, formation result, direction, and rejection reason.
- Some Research result slices require local backtest/accounting evidence or Research Demo attribution rather than a unified PostgreSQL projection.
