CREATE TABLE IF NOT EXISTS triggertrade_portfolio_cooldown_pins (
    authorization_id TEXT NOT NULL,
    tranche_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    portfolio_config_id TEXT NOT NULL,
    portfolio_config_version TEXT NOT NULL,
    portfolio_config_digest TEXT NOT NULL,
    pinned_cooldown_duration_seconds INTEGER NOT NULL CHECK (pinned_cooldown_duration_seconds >= 0),
    cooldown_state TEXT NOT NULL CHECK (
        cooldown_state IN ('PENDING_ACCEPTANCE', 'ACTIVE', 'UNRESOLVED_ACCEPTANCE_TIME', 'UNRESOLVED_CONFLICT', 'CLEARED')
    ),
    entry_accepted_at TIMESTAMPTZ,
    cooldown_until TIMESTAMPTZ,
    last_order_event_id TEXT,
    last_lifecycle_revision INTEGER CHECK (last_lifecycle_revision IS NULL OR last_lifecycle_revision >= 0),
    cleared_at TIMESTAMPTZ,
    pin_payload_json JSONB NOT NULL,
    pin_payload_digest TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (authorization_id, tranche_id),
    CHECK (
        (cooldown_state = 'ACTIVE' AND entry_accepted_at IS NOT NULL AND cooldown_until IS NOT NULL)
        OR (cooldown_state <> 'ACTIVE')
    ),
    CHECK (
        (cooldown_state = 'CLEARED' AND cleared_at IS NOT NULL)
        OR (cooldown_state <> 'CLEARED')
    )
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_portfolio_cooldown_symbol
    ON triggertrade_portfolio_cooldown_pins (symbol, cooldown_state, cooldown_until);

CREATE INDEX IF NOT EXISTS idx_triggertrade_portfolio_cooldown_event
    ON triggertrade_portfolio_cooldown_pins (last_order_event_id);
