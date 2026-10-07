-- TriggerTrade Research V1 first-run monitoring queries.
-- Read-only operator use. Provide psql variables when possible:
--   -v research_id='...' -v run_id='...'

\if :{?research_id}
\else
\set research_id ''
\endif
\if :{?run_id}
\else
\set run_id ''
\endif

BEGIN READ ONLY;

-- Snapshot A - Research run summary.
WITH params AS (
  SELECT NULLIF(:'research_id', '') AS research_id, NULLIF(:'run_id', '') AS run_id
)
SELECT
  'RUN' AS section,
  r.state_id AS research_id,
  r.payload_json->>'status' AS research_status,
  r.payload_json->>'set_id' AS set_id,
  r.payload_json->>'set_version' AS set_version,
  r.payload_json->>'rules_version_id' AS rules_version_id,
  r.updated_at AS research_updated_at,
  b.payload_json->>'run_id' AS backtest_run_id,
  b.payload_json->>'status' AS backtest_status,
  b.payload_json->>'engine_run_id' AS engine_run_id,
  d.payload_json->>'run_id' AS demo_run_id,
  d.payload_json->>'status' AS demo_status
FROM triggertrade_owner_state_records r
CROSS JOIN params p
LEFT JOIN LATERAL (
  SELECT payload_json
  FROM triggertrade_owner_state_records
  WHERE owner = 'ResearchRunStore'
    AND state_type = 'RESEARCH_BACKTEST_RUN'
    AND payload_json->>'research_id' = r.state_id
    AND (p.run_id IS NULL OR payload_json->>'run_id' = p.run_id)
  ORDER BY updated_at DESC
  LIMIT 1
) b ON true
LEFT JOIN LATERAL (
  SELECT payload_json
  FROM triggertrade_owner_state_records
  WHERE owner = 'ResearchRunStore'
    AND state_type = 'RESEARCH_DEMO_RUN'
    AND payload_json->>'research_id' = r.state_id
    AND (p.run_id IS NULL OR payload_json->>'run_id' = p.run_id)
  ORDER BY updated_at DESC
  LIMIT 1
) d ON true
WHERE r.owner = 'ResearchRunStore'
  AND r.state_type = 'RESEARCH_MUTABLE_STATE'
  AND (p.research_id IS NULL OR r.state_id = p.research_id)
ORDER BY r.updated_at DESC
LIMIT 20;

-- Snapshot B - Trigger evaluations.
WITH params AS (
  SELECT NULLIF(:'research_id', '') AS research_id, NULLIF(:'run_id', '') AS run_id
)
SELECT
  'TRIGGERS' AS section,
  state_id,
  payload_json->>'demo_run_id' AS demo_run_id,
  payload_json->>'trigger_rule_id' AS trigger_id,
  payload_json->>'trigger_rule_version' AS trigger_version,
  payload_json->>'symbol' AS symbol,
  payload_json->>'observed_at' AS observed_at,
  payload_json->>'window' AS window,
  payload_json->>'condition_result' AS condition_result,
  payload_json->>'signal_type' AS signal_type,
  payload_json->>'trigger_set_id' AS set_id,
  payload_json->>'trigger_set_version' AS set_version
FROM triggertrade_owner_state_records
CROSS JOIN params p
WHERE owner = 'ResearchDemoExecution'
  AND state_type = 'research_demo_trigger_evaluation'
  AND (p.run_id IS NULL OR payload_json->>'demo_run_id' = p.run_id)
ORDER BY payload_json->>'observed_at' DESC, state_id DESC
LIMIT 100;

-- Snapshot C - Set resolution and membership.
WITH params AS (
  SELECT NULLIF(:'research_id', '') AS research_id
),
selected_research AS (
  SELECT payload_json->>'set_id' AS set_id, payload_json->>'set_version' AS set_version
  FROM triggertrade_owner_state_records, params
  WHERE owner = 'ResearchRunStore'
    AND state_type = 'RESEARCH_MUTABLE_STATE'
    AND (params.research_id IS NULL OR state_id = params.research_id)
  ORDER BY updated_at DESC
  LIMIT 1
)
SELECT
  'SET' AS section,
  m.set_id,
  m.set_version,
  m.position,
  m.trigger_id,
  m.trigger_version,
  m.role,
  m.direction_applicability,
  m.required,
  rd.status AS trigger_status,
  rd.condition AS trigger_condition
FROM selected_research sr
JOIN triggertrade_research_set_memberships m
  ON m.set_id = sr.set_id AND m.set_version = sr.set_version
LEFT JOIN triggertrade_rule_definitions rd
  ON rd.rule_id = m.trigger_id AND rd.version = m.trigger_version
ORDER BY m.position, m.trigger_id, m.trigger_version;

-- Snapshot D - Position / Portfolio / Lifecycle.
SELECT
  'POSITION_PORTFOLIO_LIFECYCLE' AS section,
  po.state_id AS position_decision_id,
  po.payload_json#>>'{position_opportunity_state,decision,decision}' AS position_decision,
  po.payload_json#>>'{position_opportunity_state,decision,reason}' AS position_reason,
  pg.payload_json#>>'{portfolio_grant_decision,status}' AS portfolio_status,
  pg.payload_json#>>'{portfolio_grant_decision,primary_reason}' AS portfolio_reason,
  cg.capital_grant_id,
  pc.outcome AS construction_outcome,
  os.order_spec_id,
  os.direction,
  sa.authorization_id,
  lsg.lifecycle_state AS start_gate_state,
  lsi.lifecycle_state AS submission_state,
  lsi.dispatch_attempts,
  lsi.exchange_order_id,
  lsi.exchange_status,
  lsi.last_error_code
FROM triggertrade_owner_state_records po
LEFT JOIN triggertrade_owner_state_records pg
  ON pg.owner = 'Portfolio'
 AND pg.state_type = 'portfolio_grant_decision'
 AND pg.state_id = po.state_id
LEFT JOIN triggertrade_capital_grants cg
  ON cg.position_decision_id = po.state_id
LEFT JOIN triggertrade_position_construction_results pc
  ON pc.position_decision_id = po.state_id
LEFT JOIN triggertrade_order_specs os
  ON os.position_decision_id = po.state_id
LEFT JOIN triggertrade_submit_authorizations sa
  ON sa.position_decision_id = po.state_id
LEFT JOIN triggertrade_lifecycle_start_gates lsg
  ON lsg.position_decision_id = po.state_id
LEFT JOIN triggertrade_lifecycle_submission_intents lsi
  ON lsi.position_decision_id = po.state_id
WHERE po.owner = 'Position'
  AND po.state_type = 'position_opportunity'
ORDER BY COALESCE(lsi.updated_at, lsg.accepted_at, os.recorded_at, cg.recorded_at, po.updated_at) DESC
LIMIT 50;

-- Snapshot E - Worker health and leases.
SELECT
  'WORKER_HEARTBEAT' AS section,
  state_id,
  payload_json->>'component' AS component,
  payload_json->>'status' AS status,
  payload_json->>'observed_at' AS observed_at,
  payload_json->>'detail' AS detail,
  payload_json->'metadata' AS metadata
FROM triggertrade_owner_state_records
WHERE owner = 'Cross-System'
  AND state_type = 'runtime_heartbeat'
ORDER BY payload_json->>'observed_at' DESC;

WITH params AS (
  SELECT NULLIF(:'research_id', '') AS research_id, NULLIF(:'run_id', '') AS run_id
)
SELECT
  'OUTBOX' AS section,
  message_id,
  producer,
  consumer,
  message_type,
  status,
  aggregate_id,
  causation_id,
  correlation_id,
  attempt_count,
  available_at,
  created_at,
  locked_by,
  locked_at,
  lock_expires_at,
  consumed_at,
  CASE
    WHEN status = 'IN_FLIGHT' AND lock_expires_at > now() THEN 'healthy_in_flight'
    WHEN status = 'IN_FLIGHT' AND lock_expires_at <= now() THEN 'expired_in_flight'
    WHEN status = 'PENDING' AND available_at <= now() THEN 'ready_pending'
    ELSE 'not_due_or_terminal'
  END AS lease_health
FROM triggertrade_outbox_messages
CROSS JOIN params p
WHERE consumer IN ('ResearchBacktestExecution', 'ResearchDemoExecution')
  AND (p.research_id IS NULL OR aggregate_id = p.research_id)
  AND (p.run_id IS NULL OR correlation_id = p.run_id OR causation_id = p.run_id)
ORDER BY created_at DESC
LIMIT 50;

-- Snapshot F - Trades/accounting from PostgreSQL lifecycle/accounting projections.
WITH recent_lifecycle AS (
  SELECT DISTINCT decision_cycle_id, set_result_id, tranche_id, order_spec_id
  FROM triggertrade_lifecycle_order_events
  ORDER BY decision_cycle_id DESC
  LIMIT 100
)
SELECT
  'TRADES' AS section,
  e.tranche_id,
  e.order_spec_id,
  e.event_type,
  e.lifecycle_state,
  e.exchange_order_id,
  e.occurred_at,
  e.payload_json->'financial_result' AS financial_result
FROM triggertrade_lifecycle_order_events e
JOIN recent_lifecycle r
  ON r.tranche_id = e.tranche_id
ORDER BY e.occurred_at DESC, e.lifecycle_revision DESC
LIMIT 100;

SELECT
  'ACCOUNTING' AS section,
  portfolio_id,
  accounting_day_id,
  rollover_state,
  boundary_start_at,
  boundary_end_at,
  current_portfolio_equity,
  daily_realized_pnl,
  unrealized_pnl,
  total_pnl,
  daily_loss_latched,
  updated_at
FROM triggertrade_portfolio_accounting_days
ORDER BY updated_at DESC
LIMIT 20;

-- Snapshot G - Progress.
WITH params AS (
  SELECT NULLIF(:'research_id', '') AS research_id, NULLIF(:'run_id', '') AS run_id
)
SELECT
  'PROGRESS' AS section,
  owner,
  state_type,
  state_id,
  payload_json->>'status' AS status,
  payload_json->>'run_id' AS run_id,
  payload_json->>'engine_run_id' AS engine_run_id,
  payload_json#>>'{progress,observed_at}' AS progress_observed_at,
  payload_json#>>'{progress,elapsed_seconds}' AS elapsed_seconds,
  payload_json#>>'{progress,duration_seconds}' AS duration_seconds,
  payload_json#>>'{progress,duration_elapsed}' AS duration_elapsed,
  updated_at
FROM triggertrade_owner_state_records
CROSS JOIN params p
WHERE (
    owner = 'ResearchRunStore'
    AND state_type IN ('RESEARCH_BACKTEST_RUN', 'RESEARCH_DEMO_RUN')
    AND (p.research_id IS NULL OR payload_json->>'research_id' = p.research_id)
    AND (p.run_id IS NULL OR payload_json->>'run_id' = p.run_id)
  )
  OR (
    owner = 'ResearchDemoExecution'
    AND state_type = 'RESEARCH_DEMO_RUN'
    AND (p.run_id IS NULL OR state_id = p.run_id)
  )
ORDER BY updated_at DESC
LIMIT 50;

COMMIT;
