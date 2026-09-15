CREATE TABLE IF NOT EXISTS triggertrade_capital_grants (
    capital_grant_id TEXT PRIMARY KEY,
    position_decision_id TEXT NOT NULL UNIQUE,
    decision_cycle_id TEXT NOT NULL,
    set_result_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    as_of TIMESTAMPTZ NOT NULL,
    portfolio_state_revision INTEGER NOT NULL CHECK (portfolio_state_revision >= 0),
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_capital_grants_cycle
    ON triggertrade_capital_grants (decision_cycle_id, set_result_id);
