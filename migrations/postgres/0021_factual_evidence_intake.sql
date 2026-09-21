CREATE TABLE IF NOT EXISTS triggertrade_factual_evidence_records (
    evidence_id TEXT PRIMARY KEY,
    owner TEXT NOT NULL,
    evidence_kind TEXT NOT NULL,
    accepted_revision INTEGER NOT NULL DEFAULT 1 CHECK (accepted_revision >= 1),
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    raw_json JSONB NOT NULL,
    raw_digest TEXT NOT NULL,
    provenance_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS triggertrade_factual_evidence_anchors (
    anchor_key TEXT PRIMARY KEY,
    evidence_id TEXT NOT NULL REFERENCES triggertrade_factual_evidence_records (evidence_id),
    anchor_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_factual_evidence_anchors_evidence
    ON triggertrade_factual_evidence_anchors (evidence_id);

CREATE TABLE IF NOT EXISTS triggertrade_factual_preflight_challenges (
    challenge_id TEXT PRIMARY KEY,
    challenge_scope TEXT NOT NULL,
    challenge_kind TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'QUARANTINED',
    anchor_keys_json JSONB NOT NULL,
    accepted_evidence_ids_json JSONB NOT NULL,
    accepted_payload_digest TEXT,
    candidate_payload_digest TEXT,
    raw_json JSONB NOT NULL,
    raw_digest TEXT NOT NULL,
    reason TEXT NOT NULL,
    challenge_digest TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_factual_preflight_challenges_scope
    ON triggertrade_factual_preflight_challenges (challenge_scope, created_at);
