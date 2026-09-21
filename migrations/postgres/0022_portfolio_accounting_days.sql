CREATE TABLE IF NOT EXISTS triggertrade_portfolio_accounting_days (
    portfolio_id TEXT NOT NULL,
    accounting_day_id TEXT NOT NULL,
    boundary_start_at TIMESTAMPTZ NOT NULL,
    boundary_end_at TIMESTAMPTZ NOT NULL,
    rollover_state TEXT NOT NULL CHECK (rollover_state IN ('PROVEN', 'RECONCILING')),
    daily_portfolio_base TEXT,
    base_evidence_id TEXT,
    base_evidence_source TEXT,
    base_evidence_json JSONB,
    base_identity_json JSONB NOT NULL,
    base_identity_digest TEXT NOT NULL,
    current_portfolio_equity TEXT,
    daily_realized_pnl TEXT NOT NULL DEFAULT '0',
    unrealized_pnl TEXT,
    total_pnl TEXT,
    external_capital_flow_amount TEXT NOT NULL DEFAULT '0',
    daily_loss_latched BOOLEAN NOT NULL DEFAULT FALSE,
    daily_loss_latched_at TIMESTAMPTZ,
    daily_loss_reason TEXT,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (portfolio_id, accounting_day_id),
    CHECK (
        (rollover_state = 'PROVEN' AND daily_portfolio_base IS NOT NULL AND base_evidence_id IS NOT NULL)
        OR (rollover_state = 'RECONCILING')
    )
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_portfolio_accounting_days_state
    ON triggertrade_portfolio_accounting_days (portfolio_id, rollover_state, boundary_start_at);

CREATE INDEX IF NOT EXISTS idx_triggertrade_portfolio_accounting_days_base_digest
    ON triggertrade_portfolio_accounting_days (portfolio_id, accounting_day_id, base_identity_digest);

CREATE TABLE IF NOT EXISTS triggertrade_portfolio_accounting_day_results (
    result_id TEXT PRIMARY KEY,
    tranche_id TEXT NOT NULL UNIQUE,
    portfolio_id TEXT NOT NULL,
    accounting_day_id TEXT NOT NULL,
    realized_pnl TEXT NOT NULL,
    delivered_at TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL,
    payload_digest TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (portfolio_id, accounting_day_id)
        REFERENCES triggertrade_portfolio_accounting_days (portfolio_id, accounting_day_id)
);

CREATE INDEX IF NOT EXISTS idx_triggertrade_portfolio_accounting_day_results_day
    ON triggertrade_portfolio_accounting_day_results (portfolio_id, accounting_day_id, delivered_at);
