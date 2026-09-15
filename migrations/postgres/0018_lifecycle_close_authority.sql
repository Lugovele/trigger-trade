CREATE TABLE IF NOT EXISTS triggertrade_lifecycle_close_intents (
    close_intent_id TEXT PRIMARY KEY,
    tranche_id TEXT NOT NULL,
    intent_revision INTEGER NOT NULL CHECK (intent_revision >= 0),
    state TEXT NOT NULL CHECK (
        state IN (
            'ACQUIRED',
            'RECONCILING_CHILDREN',
            'REDUCTION_AUTHORIZED',
            'REDUCTION_UNCERTAIN',
            'AWAITING_EXECUTIONS',
            'AWAITING_FINALITY',
            'RESOLVED'
        )
    ),
    native_side TEXT,
    confirmed_target_quantity TEXT NOT NULL,
    confirmed_residual_quantity TEXT NOT NULL,
    authorized_reduction_quantity TEXT NOT NULL,
    executed_reduction_quantity TEXT NOT NULL,
    close_commitment_quantity_basis TEXT NOT NULL,
    cause_event_ids JSONB NOT NULL,
    entry_order_ids JSONB NOT NULL,
    protection_child_ids JSONB NOT NULL,
    unresolved_request_ids JSONB NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    acquired_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_triggertrade_close_intents_active_tranche
    ON triggertrade_lifecycle_close_intents (tranche_id)
    WHERE state <> 'RESOLVED';

CREATE INDEX IF NOT EXISTS idx_triggertrade_close_intents_tranche
    ON triggertrade_lifecycle_close_intents (tranche_id, intent_revision);

CREATE TABLE IF NOT EXISTS triggertrade_lifecycle_close_intent_causes (
    close_intent_id TEXT NOT NULL REFERENCES triggertrade_lifecycle_close_intents (close_intent_id),
    cause_event_id TEXT NOT NULL,
    cause_type TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    PRIMARY KEY (close_intent_id, cause_event_id)
);

CREATE TABLE IF NOT EXISTS triggertrade_lifecycle_close_children (
    close_child_id TEXT PRIMARY KEY,
    close_intent_id TEXT NOT NULL REFERENCES triggertrade_lifecycle_close_intents (close_intent_id),
    child_sequence INTEGER NOT NULL CHECK (child_sequence >= 1),
    child_revision INTEGER NOT NULL CHECK (child_revision >= 0),
    client_order_link_id TEXT NOT NULL UNIQUE,
    exchange_order_id TEXT,
    authorized_reduction_quantity TEXT NOT NULL,
    state TEXT NOT NULL CHECK (
        state IN (
            'AUTHORIZED',
            'SUBMITTED',
            'REDUCTION_UNCERTAIN',
            'AWAITING_EXECUTIONS',
            'TERMINAL',
            'DISABLED',
            'RESOLVED'
        )
    ),
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    authorized_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (close_intent_id, child_sequence)
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_close_children_intent
    ON triggertrade_lifecycle_close_children (close_intent_id, child_sequence);
