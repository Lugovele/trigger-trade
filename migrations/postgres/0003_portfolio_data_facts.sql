CREATE TABLE IF NOT EXISTS triggertrade_portfolio_data_requests (
    request_id TEXT PRIMARY KEY,
    request_mode TEXT NOT NULL,
    requested_at TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS triggertrade_portfolio_data_responses (
    response_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES triggertrade_portfolio_data_requests (request_id),
    request_mode TEXT NOT NULL,
    as_of TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_portfolio_data_responses_request
    ON triggertrade_portfolio_data_responses (request_id, created_at);
