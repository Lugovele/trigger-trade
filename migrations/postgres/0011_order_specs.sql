CREATE TABLE IF NOT EXISTS triggertrade_order_specs (
    order_spec_id TEXT PRIMARY KEY,
    construction_result_id TEXT NOT NULL UNIQUE,
    capital_grant_id TEXT NOT NULL,
    position_decision_id TEXT NOT NULL,
    decision_cycle_id TEXT NOT NULL,
    set_result_id TEXT NOT NULL,
    position_plan_id TEXT NOT NULL,
    tranche_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
    spec_created_at TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_order_specs_construction
    ON triggertrade_order_specs (construction_result_id);

CREATE INDEX IF NOT EXISTS idx_triggertrade_order_specs_tranche
    ON triggertrade_order_specs (tranche_id, payload_digest);
