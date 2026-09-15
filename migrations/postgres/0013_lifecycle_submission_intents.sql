CREATE TABLE IF NOT EXISTS triggertrade_lifecycle_submission_intents (
    submission_intent_id TEXT PRIMARY KEY,
    start_gate_id TEXT NOT NULL UNIQUE REFERENCES triggertrade_lifecycle_start_gates(start_gate_id),
    order_spec_id TEXT NOT NULL UNIQUE,
    authorization_id TEXT NOT NULL UNIQUE,
    capital_grant_id TEXT NOT NULL,
    decision_cycle_id TEXT NOT NULL,
    set_result_id TEXT NOT NULL,
    position_decision_id TEXT NOT NULL,
    construction_result_id TEXT NOT NULL,
    position_plan_id TEXT NOT NULL,
    tranche_id TEXT NOT NULL UNIQUE,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
    target_client_order_id TEXT NOT NULL UNIQUE,
    lifecycle_state TEXT NOT NULL CHECK (
        lifecycle_state IN ('READY_TO_SUBMIT', 'SUBMITTING', 'SUBMISSION_UNCERTAIN', 'SUBMITTED')
    ),
    order_spec_digest TEXT NOT NULL,
    submit_authorized_digest TEXT NOT NULL,
    start_gate_digest TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    dispatch_attempts INTEGER NOT NULL DEFAULT 0 CHECK (dispatch_attempts >= 0),
    last_dispatch_cutpoint_id TEXT,
    last_dispatch_started_at TIMESTAMPTZ,
    last_uncertain_at TIMESTAMPTZ,
    last_error_code TEXT,
    exchange_order_id TEXT,
    exchange_status TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (
        (lifecycle_state = 'READY_TO_SUBMIT' AND dispatch_attempts = 0 AND last_dispatch_cutpoint_id IS NULL)
        OR (lifecycle_state IN ('SUBMITTING', 'SUBMISSION_UNCERTAIN', 'SUBMITTED') AND dispatch_attempts >= 1)
    )
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_lifecycle_submission_intents_client
    ON triggertrade_lifecycle_submission_intents (target_client_order_id);

CREATE INDEX IF NOT EXISTS idx_triggertrade_lifecycle_submission_intents_state
    ON triggertrade_lifecycle_submission_intents (lifecycle_state, updated_at);
