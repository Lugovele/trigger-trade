CREATE TABLE IF NOT EXISTS triggertrade_submit_authorizations (
    authorization_id TEXT PRIMARY KEY,
    capital_grant_id TEXT NOT NULL UNIQUE,
    position_decision_id TEXT NOT NULL,
    construction_result_id TEXT NOT NULL UNIQUE,
    decision_cycle_id TEXT NOT NULL,
    set_result_id TEXT NOT NULL,
    position_plan_id TEXT NOT NULL,
    tranche_id TEXT NOT NULL,
    order_spec_id TEXT NOT NULL UNIQUE,
    symbol TEXT NOT NULL,
    order_spec_digest TEXT NOT NULL,
    held_committed_capital NUMERIC NOT NULL CHECK (held_committed_capital >= 0),
    authorized_at TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_submit_authorizations_grant
    ON triggertrade_submit_authorizations (capital_grant_id);

CREATE INDEX IF NOT EXISTS idx_triggertrade_submit_authorizations_tranche
    ON triggertrade_submit_authorizations (tranche_id, order_spec_digest);
