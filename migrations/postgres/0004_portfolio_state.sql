CREATE TABLE IF NOT EXISTS triggertrade_portfolio_state_revisions (
    portfolio_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    evidence_id TEXT NOT NULL,
    evidence_kind TEXT NOT NULL,
    health TEXT NOT NULL CHECK (health IN ('LIVE', 'RECONCILING', 'STALE')),
    as_of TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (portfolio_id, revision),
    UNIQUE (portfolio_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS triggertrade_portfolio_state_current (
    portfolio_id TEXT PRIMARY KEY,
    revision INTEGER NOT NULL CHECK (revision > 0),
    health TEXT NOT NULL CHECK (health IN ('LIVE', 'RECONCILING', 'STALE')),
    as_of TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_portfolio_state_revisions_health
    ON triggertrade_portfolio_state_revisions (health, created_at);
