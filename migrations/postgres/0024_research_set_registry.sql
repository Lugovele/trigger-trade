CREATE TABLE IF NOT EXISTS triggertrade_research_set_versions (
    set_id TEXT NOT NULL,
    set_version TEXT NOT NULL,
    display_name TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    provenance TEXT NOT NULL,
    inserted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (set_id, set_version)
);

CREATE TABLE IF NOT EXISTS triggertrade_research_set_memberships (
    set_id TEXT NOT NULL,
    set_version TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position >= 1),
    trigger_id TEXT NOT NULL,
    trigger_version TEXT NOT NULL,
    role TEXT NOT NULL,
    direction_applicability TEXT,
    required BOOLEAN NOT NULL DEFAULT true,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    inserted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (set_id, set_version, position),
    UNIQUE (set_id, set_version, trigger_id, trigger_version),
    FOREIGN KEY (set_id, set_version)
        REFERENCES triggertrade_research_set_versions (set_id, set_version)
        ON DELETE RESTRICT,
    FOREIGN KEY (trigger_id, trigger_version)
        REFERENCES triggertrade_rule_definitions (rule_id, version)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_research_set_versions_status
    ON triggertrade_research_set_versions (status, set_id, set_version);

CREATE INDEX IF NOT EXISTS idx_triggertrade_research_set_memberships_trigger
    ON triggertrade_research_set_memberships (trigger_id, trigger_version);
