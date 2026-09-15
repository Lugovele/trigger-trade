CREATE TABLE IF NOT EXISTS triggertrade_position_construction_results (
    construction_result_id TEXT PRIMARY KEY,
    capital_grant_id TEXT NOT NULL UNIQUE,
    position_decision_id TEXT NOT NULL,
    decision_cycle_id TEXT NOT NULL,
    set_result_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('CONSTRUCTED', 'REJECT')),
    occurred_at TIMESTAMPTZ NOT NULL,
    position_plan_id TEXT,
    tranche_id TEXT,
    order_spec_id TEXT UNIQUE,
    order_spec_digest TEXT,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (
        (outcome = 'CONSTRUCTED'
            AND position_plan_id IS NOT NULL
            AND tranche_id IS NOT NULL
            AND order_spec_id IS NOT NULL
            AND order_spec_digest IS NOT NULL)
        OR
        (outcome = 'REJECT'
            AND position_plan_id IS NULL
            AND tranche_id IS NULL
            AND order_spec_id IS NULL
            AND order_spec_digest IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_position_construction_results_grant
    ON triggertrade_position_construction_results (capital_grant_id);

CREATE INDEX IF NOT EXISTS idx_triggertrade_position_construction_results_cycle
    ON triggertrade_position_construction_results (decision_cycle_id, position_decision_id);
