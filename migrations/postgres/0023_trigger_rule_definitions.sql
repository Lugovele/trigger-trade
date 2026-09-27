CREATE TABLE IF NOT EXISTS triggertrade_rule_definitions (
    rule_id TEXT NOT NULL,
    version TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('DRAFT', 'TESTING', 'ACTIVE', 'ARCHIVE')),
    asset_scope TEXT NOT NULL,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('trigger', 'strategy', 'risk', 'context')),
    condition TEXT NOT NULL,
    definition_json JSONB NOT NULL,
    definition_hash TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    provenance TEXT NOT NULL,
    inserted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (rule_id, version)
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_rule_definitions_type
    ON triggertrade_rule_definitions (rule_type, rule_id, version);

CREATE INDEX IF NOT EXISTS idx_triggertrade_rule_definitions_status
    ON triggertrade_rule_definitions (status, rule_id, version);
