CREATE TABLE IF NOT EXISTS triggertrade_schema_migrations (
    version TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS triggertrade_owner_state_records (
    owner TEXT NOT NULL,
    state_type TEXT NOT NULL,
    state_id TEXT NOT NULL,
    revision BIGINT NOT NULL DEFAULT 1 CHECK (revision > 0),
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (owner, state_type, state_id)
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_owner_state_owner_type
    ON triggertrade_owner_state_records (owner, state_type);

CREATE TABLE IF NOT EXISTS triggertrade_unit_of_work_log (
    transaction_id UUID PRIMARY KEY,
    owner TEXT NOT NULL,
    idempotency_key TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (owner, idempotency_key)
);
