from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.lifecycle_order_events import build_closed_order_event_from_submission, build_order_event_from_submission
from triggertrade.persistence import (
    PortfolioFinalReceiptConflict,
    PortfolioFinalReceiptStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from tests.unit.test_lifecycle_order_events import valid_financial_result
from tests.unit.test_lifecycle_submission_store import fake_submission_record


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b10_receipt_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_portfolio_final_receipt_store_posts_closed_final_once_and_replays():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        event = _closed_event()

        with PostgresUnitOfWork(factory) as uow:
            store = PortfolioFinalReceiptStore(uow.connection)
            receipt, inserted = store.accept_order_event(
                order_event_payload=event,
                delivered_at="2026-09-14T12:05:01Z",
            )
            replay, replay_inserted = store.accept_order_event(
                order_event_payload=event,
                delivered_at="2026-09-14T12:05:01Z",
            )
            redelivery, redelivery_inserted = store.accept_order_event(
                order_event_payload=event,
                delivered_at="2026-09-14T12:07:59Z",
            )

        with PostgresUnitOfWork(factory) as restarted:
            restarted_store = PortfolioFinalReceiptStore(restarted.connection)
            by_result = restarted_store.get_by_result_id(result_id="result-1")
            by_tranche = restarted_store.get_by_tranche_id(tranche_id="tranche-1")

        assert inserted is True
        assert replay_inserted is False
        assert redelivery_inserted is False
        assert replay.payload_digest == receipt.payload_digest
        assert redelivery.payload_digest == receipt.payload_digest
        assert redelivery.delivered_at == "2026-09-14T12:05:01Z"
        assert receipt.accounting_day_id == "2026-09-14/Asia-Jerusalem"
        assert receipt.net_realized_result == "18.9"
        assert by_result == receipt
        assert by_tranche == receipt
    finally:
        _drop_schema(settings)


def test_portfolio_final_receipt_store_rejects_non_closed_or_conflicting_receipts():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        closed = _closed_event()
        open_event = build_order_event_from_submission(
            fake_submission_record(lifecycle_state="SUBMITTED", exchange_order_id="exchange-1"),
            event_id="order-event-open-1",
            occurred_at="2026-09-14T12:00:00Z",
            lifecycle_revision=1,
        ).payload
        changed_same_result = _closed_event(
            event_id="order-event-final-2",
            result_overrides={"net_realized_result": "19.0", "gross_realized_trading_result": "20.1"},
        )
        changed_same_tranche = _closed_event(
            event_id="order-event-final-3",
            result_overrides={"result_id": "result-2"},
        )
        unbalanced_result = _closed_event(event_id="order-event-final-4")
        unbalanced_result["order_event"]["financial_result"]["net_realized_result"] = "18.8"

        with PostgresUnitOfWork(factory) as uow:
            store = PortfolioFinalReceiptStore(uow.connection)
            with pytest.raises(PortfolioFinalReceiptConflict, match="CLOSED"):
                store.accept_order_event(order_event_payload=open_event, delivered_at="2026-09-14T12:05:01Z")
            store.accept_order_event(order_event_payload=closed, delivered_at="2026-09-14T12:05:01Z")
            with pytest.raises(PortfolioFinalReceiptConflict, match="different content"):
                store.accept_order_event(
                    order_event_payload=changed_same_result,
                    delivered_at="2026-09-14T12:05:01Z",
                )
            with pytest.raises(PortfolioFinalReceiptConflict, match="different content"):
                store.accept_order_event(
                    order_event_payload=changed_same_tranche,
                    delivered_at="2026-09-14T12:05:01Z",
                )
            with pytest.raises(PortfolioFinalReceiptConflict, match="equation"):
                store.accept_order_event(
                    order_event_payload=unbalanced_result,
                    delivered_at="2026-09-14T12:05:01Z",
                )
    finally:
        _drop_schema(settings)


def test_portfolio_final_receipt_store_rejects_mismatched_event_result_tranche():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        mismatched = _closed_event()
        mismatched["order_event"]["financial_result"]["tranche_id"] = "other-tranche"

        with PostgresUnitOfWork(factory) as uow:
            store = PortfolioFinalReceiptStore(uow.connection)
            with pytest.raises(PortfolioFinalReceiptConflict, match="tranche"):
                store.accept_order_event(
                    order_event_payload=mismatched,
                    delivered_at="2026-09-14T12:05:01Z",
                )
    finally:
        _drop_schema(settings)


def _closed_event(
    *,
    event_id: str = "order-event-final-1",
    result_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
    result = valid_financial_result()
    if result_overrides:
        result.update(result_overrides)
    return build_closed_order_event_from_submission(
        fake_submission_record(lifecycle_state="SUBMITTED", exchange_order_id="exchange-1"),
        event_id=event_id,
        financial_result=result,
        occurred_at="2026-09-14T12:05:00Z",
        lifecycle_revision=7,
        cumulative_entry_filled_qty="1",
        close_commitment_quantity_basis="1",
    ).payload
