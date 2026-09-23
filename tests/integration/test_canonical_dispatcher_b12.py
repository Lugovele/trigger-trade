from __future__ import annotations

from datetime import UTC, datetime
import os
import uuid

import pytest

from triggertrade.lifecycle_order_events import build_closed_order_event_from_submission
from triggertrade.persistence import (
    DurableMessageStore,
    LifecycleOrderEventStore,
    LifecycleStartGateStore,
    LifecycleSubmissionStore,
    PortfolioCurrentBookingWorkflow,
    PortfolioFinalReceiptStore,
    PortfolioGrantDecisionStore,
    PositionConstructionWorkflow,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.services.trading_worker import TargetTradingWorker
from triggertrade.services.owner_dispatch import CanonicalOwnerDispatcher
from tests.unit.test_capital_grants import NOW, approved_decision, venue_facts
from tests.unit.test_lifecycle_order_events import valid_financial_result
from tests.unit.test_portfolio_current_booking_b8c import policy as booking_policy
from tests.unit.test_portfolio_grants_b8b import policy_for as grant_policy
from tests.unit.test_portfolio_grants_b8b import portfolio_state
from tests.unit.test_position_construction_b7b import command as construction_command


pytest.importorskip("psycopg")


def test_b12_worker_dispatches_payload_complete_lifecycle_start_gate_routes():
    settings = _settings()
    migrated = False
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        migrated = True
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        order_spec_id, authorization_id = _prepare_spec_and_authorization(factory)
        worker = _worker(factory, consumers=("Lifecycle",))

        first = worker.process_once()
        second = worker.process_once()

        assert first.blocked is False
        assert second.blocked is False
        with PostgresUnitOfWork(factory) as uow:
            start_gate = LifecycleStartGateStore(uow.connection).get_by_order_spec_id(order_spec_id=order_spec_id)
            order_spec_outbox = DurableMessageStore(uow.connection).get_outbox(message_id=order_spec_id)
            authorization_outbox = DurableMessageStore(uow.connection).get_outbox(message_id=authorization_id)
            order_spec_inbox = DurableMessageStore(uow.connection).get_inbox(
                consumer="Lifecycle",
                message_id=order_spec_id,
            )
            authorization_inbox = DurableMessageStore(uow.connection).get_inbox(
                consumer="Lifecycle",
                message_id=authorization_id,
            )

        assert start_gate is not None
        assert start_gate.authorization_id == authorization_id
        assert order_spec_outbox is not None and order_spec_outbox.status == "CONSUMED"
        assert authorization_outbox is not None and authorization_outbox.status == "CONSUMED"
        assert order_spec_inbox is not None and order_spec_inbox.status == "PROCESSED"
        assert authorization_inbox is not None and authorization_inbox.status == "PROCESSED"
    finally:
        if migrated:
            _drop_schema(settings)


def test_b12_worker_dispatches_final_order_event_to_portfolio_receipt_once():
    settings = _settings()
    migrated = False
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        migrated = True
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        order_spec_id, authorization_id = _prepare_spec_and_authorization(factory)
        with PostgresUnitOfWork(factory) as uow:
            start_gate, _ = LifecycleStartGateStore(uow.connection).accept(
                start_gate_id="start-gate-b12",
                order_spec=_required_payload(DurableMessageStore(uow.connection).get_outbox(message_id=order_spec_id)),
                submit_authorized=_required_payload(DurableMessageStore(uow.connection).get_outbox(message_id=authorization_id)),
            )
            submission_store = LifecycleSubmissionStore(uow.connection)
            submission, _ = submission_store.prepare(
                submission_intent_id="submission-b12",
                start_gate=start_gate,
            )
            submission_store.mark_submitting(
                submission_intent_id=submission.submission_intent_id,
                dispatch_cutpoint_id="dispatch-b12",
                started_at="2026-09-14T12:00:00Z",
            )
            submitted = submission_store.mark_submitted(
                submission_intent_id=submission.submission_intent_id,
                exchange_order_id="exchange-b12",
                exchange_status="create_accepted",
            )
            event_payload = build_closed_order_event_from_submission(
                submitted,
                event_id="order-event-b12-final",
                financial_result=valid_financial_result(),
                occurred_at="2026-09-14T12:05:00Z",
                lifecycle_revision=7,
                cumulative_entry_filled_qty="1",
                close_commitment_quantity_basis="1",
            ).payload
            LifecycleOrderEventStore(uow.connection).append(event_payload)
            DurableMessageStore(uow.connection).append_outbox(
                message_id="order-event-b12-final",
                producer="Lifecycle",
                consumer="Portfolio",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=event_payload,
                aggregate_id="tranche-1",
                correlation_id="submission-b12",
            )
            for blocked_setup_message in (
                "construction-result-1",
                "position-decision-1:event",
            ):
                outbox = DurableMessageStore(uow.connection).get_outbox(message_id=blocked_setup_message)
                if outbox is not None:
                    DurableMessageStore(uow.connection).mark_outbox_consumed(message_id=blocked_setup_message)

        first = _worker(factory, consumers=("Portfolio",)).process_once()
        second = _worker(factory, consumers=("Portfolio",)).process_once()

        assert first.blocked is False
        assert second.blocked is False
        with PostgresUnitOfWork(factory) as uow:
            receipt = PortfolioFinalReceiptStore(uow.connection).get_by_result_id(result_id="result-1")
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id="order-event-b12-final")
            inbox = DurableMessageStore(uow.connection).get_inbox(
                consumer="Portfolio",
                message_id="order-event-b12-final",
            )

        assert receipt is not None
        assert outbox is not None and outbox.status == "CONSUMED"
        assert inbox is not None and inbox.status == "PROCESSED"
    finally:
        if migrated:
            _drop_schema(settings)


def test_b12_dispatcher_replays_processed_inbox_without_duplicate_owner_effect():
    settings = _settings()
    migrated = False
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        migrated = True
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        order_spec_id, authorization_id = _prepare_spec_and_authorization(factory)
        with PostgresUnitOfWork(factory) as uow:
            start_gate, _ = LifecycleStartGateStore(uow.connection).accept(
                start_gate_id="start-gate-b12",
                order_spec=_required_payload(DurableMessageStore(uow.connection).get_outbox(message_id=order_spec_id)),
                submit_authorized=_required_payload(DurableMessageStore(uow.connection).get_outbox(message_id=authorization_id)),
            )
            submission_store = LifecycleSubmissionStore(uow.connection)
            submission, _ = submission_store.prepare(
                submission_intent_id="submission-b12",
                start_gate=start_gate,
            )
            submission_store.mark_submitting(
                submission_intent_id=submission.submission_intent_id,
                dispatch_cutpoint_id="dispatch-b12",
                started_at="2026-09-14T12:00:00Z",
            )
            submitted = submission_store.mark_submitted(
                submission_intent_id=submission.submission_intent_id,
                exchange_order_id="exchange-b12",
                exchange_status="create_accepted",
            )
            event_payload = build_closed_order_event_from_submission(
                submitted,
                event_id="order-event-b12-replay",
                financial_result=valid_financial_result(),
                occurred_at="2026-09-14T12:05:00Z",
                lifecycle_revision=7,
                cumulative_entry_filled_qty="1",
                close_commitment_quantity_basis="1",
            ).payload
            LifecycleOrderEventStore(uow.connection).append(event_payload)
            store = DurableMessageStore(uow.connection)
            store.append_outbox(
                message_id="order-event-b12-replay",
                producer="Lifecycle",
                consumer="Portfolio",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=event_payload,
                aggregate_id="tranche-1",
                correlation_id="submission-b12",
            )
            store.record_inbox(
                consumer="Portfolio",
                message_id="order-event-b12-replay",
                producer="Lifecycle",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=event_payload,
            )
            store.mark_inbox_processed(
                consumer="Portfolio",
                message_id="order-event-b12-replay",
            )
            message = store.get_outbox(message_id="order-event-b12-replay")
            assert message is not None

        with PostgresUnitOfWork(factory) as uow:
            result = CanonicalOwnerDispatcher(uow.connection).dispatch(message)

        assert result.processed is False
        assert result.detail == "inbox_replay_already_processed"
        with PostgresUnitOfWork(factory) as uow:
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id="order-event-b12-replay")
            receipt = PortfolioFinalReceiptStore(uow.connection).get_by_result_id(result_id="result-1")

        assert outbox is not None and outbox.status == "CONSUMED"
        assert receipt is None
    finally:
        if migrated:
            _drop_schema(settings)


def test_b12_worker_keeps_incomplete_routes_blocked_and_unconsumed():
    settings = _settings()
    migrated = False
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        migrated = True
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            DurableMessageStore(uow.connection).append_outbox(
                message_id="market-handoff-b12",
                producer="Set",
                consumer="Position",
                message_type="MARKET_HANDOFF",
                message_version="4",
                payload={
                    "market_handoff": {
                        "contract_version": 4,
                        "decision_cycle_id": "cycle-b12",
                    }
                },
            )

        result = _worker(factory).process_once()

        assert result.blocked is True
        assert result.detail == "handler_not_certified:Position:MARKET_HANDOFF:4"
        with PostgresUnitOfWork(factory) as uow:
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id="market-handoff-b12")
            inbox = DurableMessageStore(uow.connection).get_inbox(
                consumer="Position",
                message_id="market-handoff-b12",
            )
        assert outbox is not None and outbox.status == "IN_FLIGHT"
        assert inbox is None
    finally:
        if migrated:
            _drop_schema(settings)


def _prepare_spec_and_authorization(factory: PostgresConnectionFactory) -> tuple[str, str]:
    with PostgresUnitOfWork(factory) as uow:
        grant, _ = PortfolioGrantDecisionStore(uow.connection).evaluate_and_record(
            grant_decision_id="grant-decision-1",
            capital_grant_id="grant-1",
            approved_decision=approved_decision(),
            portfolio_state=portfolio_state(
                global_held="100",
                coin_held="248.9",
                global_tranches=1,
                coin_tranches=1,
            ),
            policy=grant_policy(coin_allocation_cap="1000", max_positions_per_coin=4),
            venue_facts=venue_facts(),
            as_of=NOW,
        )
        assert grant.capital_grant is not None
        construction, _ = PositionConstructionWorkflow(uow.connection).evaluate_and_record(
            construction_command(capital_grant=grant.capital_grant.payload)
        )
        assert construction.order_spec is not None
        booking, _ = PortfolioCurrentBookingWorkflow(uow.connection).evaluate_and_record(
            booking_id="booking-1",
            authorization_id="auth-1",
            construction_result_id=construction.construction_result_id,
            portfolio_state=portfolio_state(
                global_held="749.65",
                coin_held="249.65",
                global_tranches=3,
                coin_tranches=1,
            ),
            policy=booking_policy(),
            authorized_at=NOW,
        )
        assert booking.authorization is not None
        return construction.order_spec.order_spec_id, booking.authorization.authorization_id


def _worker(
    factory: PostgresConnectionFactory,
    *,
    consumers=("Portfolio", "Set", "Position", "Lifecycle"),
) -> TargetTradingWorker:
    from triggertrade.persistence.postgres_runtime_store import PostgresRuntimeStore
    from triggertrade.services.trading_worker import build_target_trading_worker

    return build_target_trading_worker(
        factory=factory,
        runtime_store=PostgresRuntimeStore(factory),
        worker_id="b12-worker",
        consumers=consumers,
        poll_seconds=1,
    )


def _required_payload(record) -> dict:
    assert record is not None
    return record.payload


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b12_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')
