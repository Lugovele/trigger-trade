CREATE TABLE IF NOT EXISTS triggertrade_transport_frontier_heads (
    scope_key TEXT PRIMARY KEY,
    committed_head BIGINT NOT NULL DEFAULT 0 CHECK (committed_head >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS triggertrade_transport_frontier_messages (
    scope_key TEXT NOT NULL REFERENCES triggertrade_transport_frontier_heads (scope_key),
    sequence BIGINT NOT NULL CHECK (sequence > 0),
    message_id TEXT NOT NULL REFERENCES triggertrade_outbox_messages (message_id),
    payload_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (scope_key, sequence),
    UNIQUE (scope_key, message_id)
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_transport_frontier_messages_message
    ON triggertrade_transport_frontier_messages (message_id);

CREATE TABLE IF NOT EXISTS triggertrade_transport_frontier_applied (
    scope_key TEXT NOT NULL REFERENCES triggertrade_transport_frontier_heads (scope_key),
    consumer TEXT NOT NULL,
    applied_sequence BIGINT NOT NULL DEFAULT 0 CHECK (applied_sequence >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (scope_key, consumer)
);
