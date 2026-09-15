CREATE TABLE IF NOT EXISTS triggertrade_lifecycle_order_events (
    event_id TEXT PRIMARY KEY,
    contract_version INTEGER NOT NULL CHECK (contract_version = 7),
    event_variant TEXT NOT NULL,
    event_type TEXT,
    occurred_at TIMESTAMPTZ,
    lifecycle_revision INTEGER CHECK (lifecycle_revision IS NULL OR lifecycle_revision >= 0),
    tranche_id TEXT,
    decision_cycle_id TEXT,
    order_spec_id TEXT,
    client_order_link_id TEXT,
    exchange_order_id TEXT,
    lifecycle_state TEXT,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (event_variant, tranche_id, lifecycle_revision)
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_lifecycle_order_events_tranche
    ON triggertrade_lifecycle_order_events (tranche_id, lifecycle_revision);

CREATE INDEX IF NOT EXISTS idx_triggertrade_lifecycle_order_events_client
    ON triggertrade_lifecycle_order_events (client_order_link_id);

CREATE INDEX IF NOT EXISTS idx_triggertrade_lifecycle_order_events_variant
    ON triggertrade_lifecycle_order_events (event_variant, recorded_at);
