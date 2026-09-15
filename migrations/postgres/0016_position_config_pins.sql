CREATE TABLE IF NOT EXISTS triggertrade_position_config_pins (
    position_decision_id TEXT PRIMARY KEY,
    decision_cycle_id TEXT NOT NULL UNIQUE,
    set_result_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    market_handoff_digest TEXT NOT NULL,
    configuration_id TEXT NOT NULL,
    configuration_version TEXT NOT NULL,
    configuration_content_digest TEXT NOT NULL,
    pinned_at TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_position_config_pins_config
    ON triggertrade_position_config_pins (configuration_id, configuration_version);
