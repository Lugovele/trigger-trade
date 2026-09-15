CREATE TABLE IF NOT EXISTS triggertrade_coins_scope_revisions (
    symbol TEXT NOT NULL,
    scope_revision INTEGER NOT NULL CHECK (scope_revision >= 0),
    action TEXT NOT NULL CHECK (action IN ('OPEN', 'CLOSE')),
    event_id TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, scope_revision)
);

CREATE TABLE IF NOT EXISTS triggertrade_set_scope_current (
    symbol TEXT PRIMARY KEY,
    scope_revision INTEGER NOT NULL CHECK (scope_revision >= 0),
    action TEXT NOT NULL CHECK (action IN ('OPEN', 'CLOSE')),
    event_id TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    payload_digest TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_coins_scope_revisions_event
    ON triggertrade_coins_scope_revisions (event_id);
