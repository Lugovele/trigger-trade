CREATE TABLE IF NOT EXISTS triggertrade_outbox_messages (
    message_id TEXT PRIMARY KEY,
    producer TEXT NOT NULL,
    consumer TEXT NOT NULL,
    message_type TEXT NOT NULL,
    message_version TEXT NOT NULL,
    aggregate_id TEXT,
    causation_id TEXT,
    correlation_id TEXT,
    dedupe_key TEXT,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'IN_FLIGHT', 'CONSUMED')),
    available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    locked_by TEXT,
    locked_at TIMESTAMPTZ,
    lock_expires_at TIMESTAMPTZ,
    consumed_at TIMESTAMPTZ,
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_triggertrade_outbox_producer_dedupe
    ON triggertrade_outbox_messages (producer, dedupe_key)
    WHERE dedupe_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_triggertrade_outbox_pending
    ON triggertrade_outbox_messages (consumer, status, available_at, created_at);

CREATE TABLE IF NOT EXISTS triggertrade_inbox_messages (
    consumer TEXT NOT NULL,
    message_id TEXT NOT NULL,
    producer TEXT NOT NULL,
    message_type TEXT NOT NULL,
    message_version TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'RECEIVED'
        CHECK (status IN ('RECEIVED', 'PROCESSED')),
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ,
    PRIMARY KEY (consumer, message_id)
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_inbox_consumer_status
    ON triggertrade_inbox_messages (consumer, status, received_at);
