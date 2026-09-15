CREATE TABLE IF NOT EXISTS triggertrade_lifecycle_set_sync (
    decision_cycle_id TEXT PRIMARY KEY,
    set_result_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    last_lifecycle_revision INTEGER NOT NULL CHECK (last_lifecycle_revision >= 0),
    terminal_lifecycle_revision INTEGER CHECK (terminal_lifecycle_revision IS NULL OR terminal_lifecycle_revision >= 0),
    terminal_event_id TEXT,
    terminal_event_type TEXT CHECK (
        terminal_event_type IS NULL
        OR terminal_event_type IN (
            'FULL_FILL',
            'CANCELLED_ZERO_FILL',
            'ENTRY_REMAINDER_CANCELLED',
            'SUBMISSION_FAILED_AFTER_PLACEMENT_RECONCILIATION'
        )
    ),
    placement_event_id TEXT,
    placement_lifecycle_revision INTEGER CHECK (placement_lifecycle_revision IS NULL OR placement_lifecycle_revision >= 0),
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_lifecycle_set_sync_terminal
    ON triggertrade_lifecycle_set_sync (decision_cycle_id, terminal_lifecycle_revision);

CREATE INDEX IF NOT EXISTS idx_triggertrade_lifecycle_set_sync_placement
    ON triggertrade_lifecycle_set_sync (placement_event_id);
