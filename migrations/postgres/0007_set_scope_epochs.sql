CREATE TABLE IF NOT EXISTS triggertrade_set_scope_epochs (
    symbol TEXT NOT NULL,
    formation_epoch INTEGER NOT NULL CHECK (formation_epoch >= 0),
    epoch_state TEXT NOT NULL CHECK (epoch_state IN ('ACTIVE', 'TERMINATED')),
    open_event_id TEXT NOT NULL,
    opened_at TIMESTAMPTZ NOT NULL,
    open_payload_digest TEXT NOT NULL,
    configuration_binding_json JSONB NOT NULL,
    configuration_binding_digest TEXT NOT NULL,
    terminated_by_scope_revision INTEGER CHECK (terminated_by_scope_revision >= 0),
    terminated_by_event_id TEXT,
    terminated_at TIMESTAMPTZ,
    terminated_by_action TEXT CHECK (terminated_by_action IN ('OPEN', 'CLOSE')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, formation_epoch)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_triggertrade_set_scope_epochs_active
    ON triggertrade_set_scope_epochs (symbol)
    WHERE epoch_state = 'ACTIVE';
