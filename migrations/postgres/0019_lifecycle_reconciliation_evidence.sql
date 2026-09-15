CREATE TABLE IF NOT EXISTS triggertrade_lifecycle_reconciliation_tombstones (
    native_observation_id TEXT PRIMARY KEY,
    native_scope_revision INTEGER NOT NULL CHECK (native_scope_revision >= 0),
    native_scope_json JSONB NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('UNRESOLVED', 'RESOLVED')),
    latest_revision_id TEXT,
    latest_evidence_revision INTEGER CHECK (latest_evidence_revision IS NULL OR latest_evidence_revision >= 0),
    complete_payload_digest TEXT,
    unresolved_block_active BOOLEAN NOT NULL,
    integrity_state TEXT NOT NULL CHECK (integrity_state IN ('CLEAR', 'CONFLICT')),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS triggertrade_lifecycle_reconciliation_records (
    evidence_id TEXT PRIMARY KEY,
    evidence_kind TEXT NOT NULL CHECK (
        evidence_kind IN (
            'NATIVE_UNATTRIBUTED_REDUCTION',
            'NATIVE_ATTRIBUTION_RESOLUTION',
            'NATIVE_SCOPE_RECONCILIATION_OBSERVED',
            'NATIVE_SCOPE_RECONCILIATION_RESOLUTION'
        )
    ),
    native_observation_id TEXT NOT NULL REFERENCES triggertrade_lifecycle_reconciliation_tombstones (native_observation_id),
    native_scope_revision INTEGER NOT NULL CHECK (native_scope_revision >= 0),
    revision_id TEXT NOT NULL,
    evidence_revision INTEGER NOT NULL CHECK (evidence_revision >= 0),
    native_scope_json JSONB NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    complete BOOLEAN NOT NULL,
    accepted BOOLEAN NOT NULL,
    integrity_state TEXT NOT NULL CHECK (integrity_state IN ('CLEAR', 'CONFLICT')),
    occurred_at TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_lifecycle_reconciliation_observation
    ON triggertrade_lifecycle_reconciliation_records (native_observation_id, evidence_revision);

CREATE UNIQUE INDEX IF NOT EXISTS ux_triggertrade_lifecycle_reconciliation_revision
    ON triggertrade_lifecycle_reconciliation_records (
        native_observation_id,
        revision_id,
        evidence_revision,
        payload_digest
    );
