from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    PortfolioAccountingDayConflict,
    PortfolioAccountingDayStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.portfolio_accounting_day import establish_day_from_boundary_snapshot


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b8a_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_portfolio_accounting_day_store_restores_base_metrics_latch_and_result_after_restart():
    settings = _settings()
    try:
        applied = apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        assert applied[-1].version == "0022"
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        day = establish_day_from_boundary_snapshot(
            portfolio_id="portfolio-main",
            boundary_instant="2026-09-05T21:00:00Z",
            strategy_wallet_capital_excluding_unrealized_pnl="1080",
            evidence_id="wallet-boundary-2026-09-06",
        )

        with PostgresUnitOfWork(factory) as uow:
            store = PortfolioAccountingDayStore(uow.connection)
            recorded, inserted = store.record_day(day)
            assert inserted is True
            replayed, inserted = store.record_day(day)
            assert inserted is False
            assert replayed.payload_digest == recorded.payload_digest
            store.update_live_metrics(
                portfolio_id="portfolio-main",
                accounting_day_id="2026-09-06",
                current_portfolio_equity="1065",
                unrealized_pnl="-35",
            )
            result, posted, updated_day = store.post_final_result_once(
                portfolio_id="portfolio-main",
                accounting_day_id="2026-09-06",
                result_id="final-1",
                tranche_id="tranche-1",
                realized_pnl="20",
                delivered_at="2026-09-07T09:00:00Z",
            )
            assert posted is True
            assert result.realized_pnl == "20"
            assert updated_day.day.daily_realized_pnl == "20"
            store.latch_daily_loss_once(
                portfolio_id="portfolio-main",
                accounting_day_id="2026-09-06",
                latched_at="2026-09-06T10:00:00Z",
            )
            replayed_after_mutation, inserted = store.record_day(day)
            assert inserted is False
            assert replayed_after_mutation.day.daily_portfolio_base == "1080"
            assert replayed_after_mutation.day.current_portfolio_equity == "1065"
            assert replayed_after_mutation.day.daily_realized_pnl == "20"
            assert replayed_after_mutation.day.daily_loss_latched is True

        with PostgresUnitOfWork(factory) as restarted:
            store = PortfolioAccountingDayStore(restarted.connection)
            current = store.get_day(portfolio_id="portfolio-main", accounting_day_id="2026-09-06")
            result = store.get_result(result_id="final-1")

        assert current is not None
        assert current.day.daily_portfolio_base == "1080"
        assert current.day.boundary_start_at == "2026-09-05T21:00:00Z"
        assert current.day.current_portfolio_equity == "1065"
        assert current.day.daily_realized_pnl == "20"
        assert current.day.unrealized_pnl == "-35"
        assert current.day.total_pnl == "-15"
        assert current.day.daily_loss_latched is True
        assert result is not None
        assert result.tranche_id == "tranche-1"
    finally:
        _drop_schema(settings)


def test_portfolio_accounting_day_store_rejects_base_rewrite_and_posts_final_once():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        day = establish_day_from_boundary_snapshot(
            portfolio_id="portfolio-main",
            boundary_instant="2026-09-05T21:00:00Z",
            strategy_wallet_capital_excluding_unrealized_pnl="1080",
            evidence_id="wallet-boundary-2026-09-06",
        )
        changed_day = establish_day_from_boundary_snapshot(
            portfolio_id="portfolio-main",
            boundary_instant="2026-09-05T21:00:00Z",
            strategy_wallet_capital_excluding_unrealized_pnl="999",
            evidence_id="different-boundary-evidence",
        )

        with PostgresUnitOfWork(factory) as uow:
            store = PortfolioAccountingDayStore(uow.connection)
            store.record_day(day)
            with pytest.raises(PortfolioAccountingDayConflict):
                store.record_day(changed_day)
            _, posted, updated_day = store.post_final_result_once(
                portfolio_id="portfolio-main",
                accounting_day_id="2026-09-06",
                result_id="final-1",
                tranche_id="tranche-1",
                realized_pnl="-25",
                delivered_at="2026-09-07T09:00:00Z",
            )
            assert posted is True
            replay, posted, replay_day = store.post_final_result_once(
                portfolio_id="portfolio-main",
                accounting_day_id="2026-09-06",
                result_id="final-1",
                tranche_id="tranche-1",
                realized_pnl="-25",
                delivered_at="2026-09-07T09:00:00Z",
            )
            assert posted is False
            assert replay.result_id == "final-1"
            assert replay_day.day.daily_realized_pnl == updated_day.day.daily_realized_pnl == "-25"
            with pytest.raises(PortfolioAccountingDayConflict):
                store.post_final_result_once(
                    portfolio_id="portfolio-main",
                    accounting_day_id="2026-09-06",
                    result_id="final-1",
                    tranche_id="tranche-1",
                    realized_pnl="-30",
                    delivered_at="2026-09-07T09:00:00Z",
                )
    finally:
        _drop_schema(settings)
