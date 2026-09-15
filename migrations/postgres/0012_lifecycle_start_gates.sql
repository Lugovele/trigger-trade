CREATE TABLE IF NOT EXISTS triggertrade_lifecycle_start_gates (
    start_gate_id TEXT PRIMARY KEY,
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
    lifecycle_state TEXT NOT NULL CHECK (lifecycle_state = 'READY_TO_SUBMIT'),
    order_spec_digest TEXT NOT NULL,
    submit_authorized_digest TEXT NOT NULL,
    held_committed_capital NUMERIC NOT NULL CHECK (held_committed_capital >= 0),
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    accepted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_lifecycle_start_gates_spec
    ON triggertrade_lifecycle_start_gates (order_spec_id, order_spec_digest);

CREATE INDEX IF NOT EXISTS idx_triggertrade_lifecycle_start_gates_auth
    ON triggertrade_lifecycle_start_gates (authorization_id, submit_authorized_digest);
