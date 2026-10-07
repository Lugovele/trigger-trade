# Research Execution Observability Map

This map is for the first real Research V1 execution. It identifies the current factual read paths that can be observed without mutating production state.

## Execution Chain

`Research Run` -> `Research Config` -> `Set Version` -> `Trigger Evaluations` -> `Set Resolution` -> `Direction` -> `Position APPROVE/REJECT` -> `Portfolio Capital/Limits` -> `Order Spec` -> `Submit Authorization` -> `Lifecycle` -> `Execution` -> `Accounting` -> `Research Result`

## Core Stores

| Stage | Authoritative read path | Keys | Healthy evidence | Blocked / failed evidence |
| --- | --- | --- | --- | --- |
| Research config | `triggertrade_owner_state_records` where `owner='ResearchConfigurationRegistry'` and `state_type='RESEARCH_DEFINITION'` | `state_id=research_id` | payload has `research_id`, `set_id`, `set_version`, `rules_version_id` | missing record or pins that do not match launch intent |
| Trigger Set config | `triggertrade_owner_state_records` where `state_type='TRIGGER_SET_VERSION'`; tabular registry in `triggertrade_research_set_versions` and `triggertrade_research_set_memberships` | `set_id`, `set_version` | exact set version exists and membership rows resolve to trigger definitions | missing version, missing member, duplicate/ambiguous trigger version |
| Rules config | `triggertrade_owner_state_records` where `state_type='TRADING_RULES_VERSION'` | `rules_version_id` | exact rules version exists | missing rules version |
| Trigger definitions | `triggertrade_rule_definitions` | `rule_id`, `version` | membership trigger/version resolves to `status='ACTIVE'` or intended imported status | missing trigger definition |
| Research mutable state | `triggertrade_owner_state_records` where `owner='ResearchRunStore'`, `state_type='RESEARCH_MUTABLE_STATE'` | `state_id=research_id` | status advances through expected Research states | `BLOCKED` or `FAILED` |
| Backtest run | `triggertrade_owner_state_records` where `owner='ResearchRunStore'`, `state_type='RESEARCH_BACKTEST_RUN'` | `payload_json->>'research_id'`, `payload_json->>'run_id'` | `RUNNING` then `COMPLETED` or `COMPLETED_NO_TRADES`; `engine_run_id` appears on completion | `FAILED`; `unavailable_reason` populated |
| Demo run projection | `triggertrade_owner_state_records` where `owner='ResearchRunStore'`, `state_type='RESEARCH_DEMO_RUN'` | `research_id`, `run_id` | `RUNNING` with `started_at`; terminal projection after completion | `BLOCKED` or `FAILED`; `blocked_reason` populated |
| Demo execution owner | `triggertrade_owner_state_records` where `owner='ResearchDemoExecution'`, `state_type='RESEARCH_DEMO_RUN'` | `state_id=demo_run_id` | `status='RUNNING'`, progress observed, `execution_owner='trading-worker'` | terminal `FAILED` or `BLOCKED`; `error` populated |
| Worker heartbeat | `triggertrade_owner_state_records` where `owner='Cross-System'`, `state_type='runtime_heartbeat'` | component state id | `status='RUNNING'`, fresh `observed_at`, detail `idle`, `processed:*`, or `research_dispatch_active` | stale heartbeat, `BLOCKED`, `DEGRADED`, `UNAVAILABLE` |
| Outbox lease | `triggertrade_outbox_messages` | `message_id`, `consumer`, `correlation_id`, `aggregate_id` | `IN_FLIGHT` has `locked_by`, `lock_expires_at > now()`; long jobs renew lock; terminal becomes `CONSUMED` | repeated attempt count increase, expired lock while still active, stuck `PENDING` |
| Inbox | `triggertrade_inbox_messages` | `consumer`, `message_id` | claimed work appears as `PROCESSED` | missing inbox row for consumed message or non-progressing `RECEIVED` |
| Runtime lane checkpoints | `triggertrade_owner_state_records` where `owner='Cross-System'`, `state_type in ('runtime_lane_checkpoint','runtime_lane_lifecycle')` | lane, symbol, timeframe, set id/version | checkpoint/lifecycle state advances by candle | checkpoint gap, stale lifecycle |
| Position decision | owner-state `owner='Position'`, `state_type='position_opportunity'`; `triggertrade_position_config_pins` | `position_decision_id`, `decision_cycle_id`, `set_result_id` | decision payload shows `APPROVE` or supported rejection, config pin exists | missing pin, decision/reason contradicts upstream Set handoff |
| Portfolio decision | owner-state `owner='Portfolio'`, `state_type='portfolio_grant_decision'`; `triggertrade_capital_grants` | `position_decision_id`, `capital_grant_id` | grant decision `ALLOWED` with capital grant or factual rejection reason | missing grant decision, conflicting grant payload |
| Position construction | `triggertrade_position_construction_results` | `capital_grant_id`, `position_decision_id`, `order_spec_id` | `outcome='CONSTRUCTED'` and order spec id/digest present, or `REJECT` with no order spec | invalid mixed outcome/order_spec fields |
| Order spec | `triggertrade_order_specs` | `order_spec_id`, `tranche_id` | immutable order spec exists with `direction` LONG/SHORT and payload digest | missing order spec after constructed position |
| Submit authorization | `triggertrade_submit_authorizations` | `authorization_id`, `order_spec_id` | authorization exists and references same order spec digest | missing authorization after grant/construction |
| Lifecycle start gate | `triggertrade_lifecycle_start_gates` | `start_gate_id`, `order_spec_id` | `lifecycle_state='READY_TO_SUBMIT'` | missing start gate after authorization |
| Lifecycle submission | `triggertrade_lifecycle_submission_intents` | `submission_intent_id`, `order_spec_id` | state advances from `READY_TO_SUBMIT` to `SUBMITTING` / `SUBMITTED` | `SUBMISSION_UNCERTAIN`, growing dispatch attempts without resolution |
| Lifecycle events | `triggertrade_lifecycle_order_events`; `triggertrade_lifecycle_set_sync`; reconciliation and close-authority tables | `tranche_id`, `order_spec_id`, `decision_cycle_id` | placement/fill/terminal events recorded with monotonically increasing lifecycle revision | reconciliation tombstone unresolved, integrity `CONFLICT`, close intent stuck |
| Portfolio accounting day | `triggertrade_portfolio_accounting_days`, `triggertrade_portfolio_accounting_day_results` | `portfolio_id`, `accounting_day_id`, `tranche_id` | `rollover_state='PROVEN'`, daily/equity fields populated | `RECONCILING`, daily loss latch, missing result for closed tranche |
| Local backtest evidence | SQLite backtest DB tables: `backtest_runs`, `backtest_results`, `backtest_run_trades`, `trigger_evaluations`, `strategy_decisions`, `risk_decisions`, `futures_accounting_*` | `engine_run_id`, `backtest_run_id`, `trade_id` | engine run and result rows exist after backtest completion | missing local evidence for completed backtest |

## Trigger-Level Observability

Backtest trigger evaluations are persisted in the local SQLite trace store through `trigger_evaluations` and audit events. Research Demo trigger evaluations are persisted into PostgreSQL owner-state records by `ResearchDemoExecution` with `state_type='research_demo_trigger_evaluation'`. The payload includes `demo_run_id`, `signal_id`, `trigger_rule_id`, `trigger_rule_version`, `symbol`, `observed_at`, `window`, `input_snapshot`, `condition_result`, `signal_type`, `lane`, `trigger_set_id`, and `trigger_set_version`.

OBSERVABILITY_GAP: there is no single PostgreSQL table that stores every Backtest per-trigger evaluation with the Research `run_id`; Backtest detailed trigger evidence remains tied to the local engine run trace store unless separately exported.

## Set-Level Observability

The exact Set version and membership are observable from `triggertrade_research_set_versions`, `triggertrade_research_set_memberships`, and the Research configuration owner-state pin. Runtime lane checkpoints prove candle progression for a set/lane.

OBSERVABILITY_GAP: the current PostgreSQL schema does not expose a first-class per-run Set-resolution table containing the exact trigger-result vector, Set formation result, direction, and rejection reason. Those facts must be inferred from trace evidence, downstream `set_result_id` linkage, and lifecycle/Position records.

## Position, Portfolio, Lifecycle Observability

Position approval/rejection is owned by `Position` owner-state `position_opportunity` plus `triggertrade_position_config_pins`. Portfolio capital and limit authority is owned by `Portfolio` owner-state `portfolio_grant_decision`, `triggertrade_capital_grants`, and `triggertrade_submit_authorizations`. Lifecycle start, submission, exchange-event, reconciliation, close, and Set sync evidence is owned by the lifecycle tables listed above.

OBSERVABILITY_GAP: the Research Demo path can persist strategy/risk trace evidence under `ResearchDemoExecution`, while canonical Position/Portfolio/Lifecycle evidence is keyed by decision, set, tranche, order, and authorization identifiers rather than directly by `research_id`. Operators must follow IDs from Research -> Set -> trigger/strategy/risk -> Position/Portfolio/Lifecycle.

## Worker and Lease Health

Healthy in-flight Research work has all of the following:

- `triggertrade_outbox_messages.status='IN_FLIGHT'` for `ResearchBacktestExecution` or `ResearchDemoExecution`.
- `locked_by` populated and `lock_expires_at > now()`.
- `attempt_count` stable while the same worker renews the lease.
- `Cross-System/runtime_heartbeat` for `trading-worker` is fresh and `RUNNING`.
- heartbeat detail is `research_dispatch_active` during long-running dispatch, with metadata `lease_renewed='true'` after renewal.

Investigate immediately when `lock_expires_at <= now()` while the run is not terminal, `attempt_count` repeatedly increases for the same message, heartbeat status is `BLOCKED`, or heartbeat detail reports lease renewal failure/loss.

## Progress Observability

Backtest progress is partially observable through Research run status, `updated_at`, `engine_run_id`, and completed metrics such as `candles_processed`. The local backtest result records hold final candle and trade counts after completion.

Demo progress is observable through `ResearchDemoExecution` owner-state payload fields: `started_at`, `progress.observed_at`, `progress.elapsed_seconds`, `progress.duration_seconds`, `progress.duration_elapsed`, `cycle`, `unresolved_obligations`, and final `result`.

OBSERVABILITY_GAP: Backtest does not currently expose a PostgreSQL live per-candle progress counter while the engine is still computing.

## Result Observability

Backtest result metrics are projected in the Research backtest owner-state payload `metrics` after terminal status. Local backtest/accounting tables hold trade IDs, closed trades, PnL, fees, funding, drawdown, expectancy, profit factor, long/short counts, and regime counts.

Demo result projection is computed from attributed accounting evidence and stored in the `ResearchDemoExecution` terminal payload. Portfolio accounting day records provide accounting-day totals.

OBSERVABILITY_GAP: not every Research-spec result slice is currently projected in PostgreSQL by coin, segment, and direction for every mode. Use the terminal Research payload first, then local backtest/accounting stores or attributed Research Demo accounting evidence where available.
