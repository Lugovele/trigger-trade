param(
    [Parameter(Mandatory = $true)]
    [string] $DatabaseUrl,

    [string] $ResearchId = "",

    [string] $RunId = "",

    [string] $PsqlPath = "psql"
)

$ErrorActionPreference = "Stop"

$sql = @'
\pset pager off
\pset tuples_only off
\pset format aligned
\set ON_ERROR_STOP on
BEGIN READ ONLY;

SELECT 'RUN' AS section;
WITH params AS (SELECT NULLIF(:'research_id', '') AS research_id, NULLIF(:'run_id', '') AS run_id)
SELECT
  r.state_id AS research_id,
  r.payload_json->>'status' AS research_status,
  r.payload_json->>'set_id' AS set_id,
  r.payload_json->>'set_version' AS set_version,
  r.payload_json->>'rules_version_id' AS rules_version_id,
  b.payload_json->>'run_id' AS backtest_run_id,
  b.payload_json->>'status' AS backtest_status,
  d.payload_json->>'run_id' AS demo_run_id,
  d.payload_json->>'status' AS demo_status,
  r.updated_at
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
LIMIT 5;

SELECT 'PROGRESS' AS section;
WITH params AS (SELECT NULLIF(:'research_id', '') AS research_id, NULLIF(:'run_id', '') AS run_id)
SELECT owner, state_type, state_id, payload_json->>'status' AS status,
       payload_json->>'run_id' AS run_id,
       payload_json->>'engine_run_id' AS engine_run_id,
       payload_json#>>'{progress,observed_at}' AS progress_observed_at,
       payload_json#>>'{progress,elapsed_seconds}' AS elapsed_seconds,
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
LIMIT 10;

SELECT 'TRIGGERS' AS section;
WITH params AS (SELECT NULLIF(:'run_id', '') AS run_id)
SELECT payload_json->>'observed_at' AS observed_at,
       payload_json->>'trigger_rule_id' AS trigger_id,
       payload_json->>'trigger_rule_version' AS version,
       payload_json->>'condition_result' AS condition_result,
       payload_json->>'signal_type' AS signal_type,
       payload_json->>'symbol' AS symbol,
       payload_json->>'window' AS window
FROM triggertrade_owner_state_records
CROSS JOIN params p
WHERE owner = 'ResearchDemoExecution'
  AND state_type = 'research_demo_trigger_evaluation'
  AND (p.run_id IS NULL OR payload_json->>'demo_run_id' = p.run_id)
ORDER BY payload_json->>'observed_at' DESC, state_id DESC
LIMIT 12;

SELECT 'SET' AS section;
WITH params AS (SELECT NULLIF(:'research_id', '') AS research_id),
selected_research AS (
  SELECT payload_json->>'set_id' AS set_id, payload_json->>'set_version' AS set_version
  FROM triggertrade_owner_state_records, params
  WHERE owner = 'ResearchRunStore'
    AND state_type = 'RESEARCH_MUTABLE_STATE'
    AND (params.research_id IS NULL OR state_id = params.research_id)
  ORDER BY updated_at DESC
  LIMIT 1
)
SELECT m.position, m.trigger_id, m.trigger_version, m.role, m.direction_applicability, m.required, rd.status
FROM selected_research sr
JOIN triggertrade_research_set_memberships m ON m.set_id = sr.set_id AND m.set_version = sr.set_version
LEFT JOIN triggertrade_rule_definitions rd ON rd.rule_id = m.trigger_id AND rd.version = m.trigger_version
ORDER BY m.position
LIMIT 40;

SELECT 'POSITION' AS section;
SELECT state_id AS position_decision_id,
       payload_json#>>'{position_opportunity_state,decision,decision}' AS decision,
       payload_json#>>'{position_opportunity_state,decision,reason}' AS reason,
       updated_at
FROM triggertrade_owner_state_records
WHERE owner = 'Position' AND state_type = 'position_opportunity'
ORDER BY updated_at DESC
LIMIT 10;

SELECT 'PORTFOLIO' AS section;
SELECT state_id AS position_decision_id,
       payload_json#>>'{portfolio_grant_decision,status}' AS status,
       payload_json#>>'{portfolio_grant_decision,primary_reason}' AS reason,
       updated_at
FROM triggertrade_owner_state_records
WHERE owner = 'Portfolio' AND state_type = 'portfolio_grant_decision'
ORDER BY updated_at DESC
LIMIT 10;

SELECT 'LIFECYCLE' AS section;
SELECT si.submission_intent_id, si.order_spec_id, si.lifecycle_state, si.dispatch_attempts,
       si.exchange_order_id, si.exchange_status, si.last_error_code, si.updated_at
FROM triggertrade_lifecycle_submission_intents si
ORDER BY si.updated_at DESC
LIMIT 10;

SELECT 'TRADES' AS section;
SELECT tranche_id, order_spec_id, event_type, lifecycle_state, exchange_order_id, occurred_at
FROM triggertrade_lifecycle_order_events
ORDER BY occurred_at DESC, lifecycle_revision DESC
LIMIT 10;

SELECT 'ACCOUNTING' AS section;
SELECT portfolio_id, accounting_day_id, rollover_state, current_portfolio_equity,
       daily_realized_pnl, unrealized_pnl, total_pnl, daily_loss_latched, updated_at
FROM triggertrade_portfolio_accounting_days
ORDER BY updated_at DESC
LIMIT 5;

SELECT 'WORKER' AS section;
SELECT payload_json->>'component' AS component,
       payload_json->>'status' AS status,
       payload_json->>'observed_at' AS observed_at,
       payload_json->>'detail' AS detail,
       payload_json->'metadata' AS metadata
FROM triggertrade_owner_state_records
WHERE owner = 'Cross-System' AND state_type = 'runtime_heartbeat'
ORDER BY payload_json->>'observed_at' DESC;

SELECT 'BLOCKERS' AS section;
WITH params AS (SELECT NULLIF(:'research_id', '') AS research_id, NULLIF(:'run_id', '') AS run_id),
outbox AS (
  SELECT message_id, consumer, message_type, status, aggregate_id, correlation_id, attempt_count,
         locked_by, locked_at, lock_expires_at, consumed_at,
         CASE
           WHEN status = 'IN_FLIGHT' AND lock_expires_at <= now() THEN 'expired_in_flight'
           WHEN status = 'IN_FLIGHT' THEN 'healthy_in_flight'
           WHEN status = 'PENDING' AND available_at <= now() THEN 'ready_pending'
           ELSE 'not_due_or_terminal'
         END AS lease_health
  FROM triggertrade_outbox_messages, params
  WHERE consumer IN ('ResearchBacktestExecution', 'ResearchDemoExecution')
    AND (params.research_id IS NULL OR aggregate_id = params.research_id)
    AND (params.run_id IS NULL OR correlation_id = params.run_id OR causation_id = params.run_id)
)
SELECT * FROM outbox
WHERE status <> 'CONSUMED' OR lease_health = 'expired_in_flight'
ORDER BY lock_expires_at NULLS FIRST, attempt_count DESC
LIMIT 20;

COMMIT;
'@

$temp = [System.IO.Path]::GetTempFileName()
try {
    Set-Content -LiteralPath $temp -Value $sql -Encoding UTF8
    & $PsqlPath $DatabaseUrl -v "research_id=$ResearchId" -v "run_id=$RunId" -f $temp
    if ($LASTEXITCODE -ne 0) {
        throw "psql exited with code $LASTEXITCODE"
    }
}
finally {
    Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
}
