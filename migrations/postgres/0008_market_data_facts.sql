CREATE TABLE IF NOT EXISTS triggertrade_market_data_pages (
    page_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    response_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    selection_id TEXT NOT NULL,
    selection_digest TEXT NOT NULL,
    dataset TEXT NOT NULL,
    page_index INTEGER NOT NULL CHECK (page_index >= 0),
    source_snapshot_id TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_market_data_pages_selection
    ON triggertrade_market_data_pages (selection_id, selection_digest, source_snapshot_id, page_index);

CREATE INDEX IF NOT EXISTS idx_triggertrade_market_data_pages_request
    ON triggertrade_market_data_pages (request_id);
