from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.lifecycle_submission import lifecycle_client_order_id
from triggertrade.persistence import (
    LifecycleStartGateStore,
    LifecycleSubmissionConflict,
    LifecycleSubmissionRecord,
    LifecycleSubmissionStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from tests.unit.test_lifecycle_start_gate import valid_gate_inputs


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_ol002_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_lifecycle_submission_store_persists_replays_and_recovers_dispatch_cutpoints():
    settings = _settings()
    try:
        assert [migration.version for migration in apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)] == [
            "0001",
            "0002",
            "0003",
            "0004",
            "0005",
            "0006",
            "0007",
            "0008",
            "0009",
            "0010",
            "0011",
            "0012",
            "0013",
            "0014",
            "0015",
            "0016",
            "0017",
            "0018",
            "0019",
            "0020",
            "0021",
            "0022",
        ]
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            start_gate = _start_gate(uow)
            store = LifecycleSubmissionStore(uow.connection)
            record, inserted = store.prepare(submission_intent_id="submission-1", start_gate=start_gate)
            replayed, replay_inserted = store.prepare(submission_intent_id="submission-1", start_gate=start_gate)
            submitting = store.mark_submitting(
                submission_intent_id="submission-1",
                dispatch_cutpoint_id="dispatch-1",
                started_at="2026-09-14T12:00:00Z",
            )
            uncertain = store.mark_uncertain(
                submission_intent_id="submission-1",
                dispatch_cutpoint_id="dispatch-1",
                uncertain_at="2026-09-14T12:00:01Z",
                error_code="TimeoutError",
            )
            with pytest.raises(LifecycleSubmissionConflict, match="not dispatchable"):
                store.mark_submitting(
                    submission_intent_id="submission-1",
                    dispatch_cutpoint_id="dispatch-2",
                    started_at="2026-09-14T12:00:02Z",
                )

        with PostgresUnitOfWork(factory) as restarted:
            stored = LifecycleSubmissionStore(restarted.connection).get_by_target_client_order_id(
                target_client_order_id=lifecycle_client_order_id("order-spec-1")
            )
            unresolved = LifecycleSubmissionStore(restarted.connection).unresolved()

        assert inserted is True
        assert replay_inserted is False
        assert replayed.payload_digest == record.payload_digest
        assert record.lifecycle_state == "READY_TO_SUBMIT"
        assert submitting.lifecycle_state == "SUBMITTING"
        assert uncertain.lifecycle_state == "SUBMISSION_UNCERTAIN"
        assert uncertain.dispatch_attempts == 1
        assert uncertain.last_dispatch_cutpoint_id == "dispatch-1"
        assert uncertain.last_error_code == "TimeoutError"
        assert stored is not None
        assert stored.submission_intent_id == "submission-1"
        assert [item.submission_intent_id for item in unresolved] == ["submission-1"]
    finally:
        _drop_schema(settings)


def test_lifecycle_submission_store_rejects_conflicting_client_id_and_requires_cutpoint_before_submitted():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            start_gate = _start_gate(uow)
            store = LifecycleSubmissionStore(uow.connection)
            store.prepare(submission_intent_id="submission-1", start_gate=start_gate)
            with pytest.raises(LifecycleSubmissionConflict):
                store.prepare(
                    submission_intent_id="submission-2",
                    start_gate=start_gate,
                    target_client_order_id="different-client-id",
                )
            with pytest.raises(LifecycleSubmissionConflict, match="before a persisted dispatch"):
                store.mark_submitted(
                    submission_intent_id="submission-1",
                    exchange_order_id="exchange-1",
                    exchange_status="create_accepted",
                )
    finally:
        _drop_schema(settings)


def test_lifecycle_submission_store_submitted_state_is_restart_visible():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            start_gate = _start_gate(uow)
            store = LifecycleSubmissionStore(uow.connection)
            store.prepare(submission_intent_id="submission-1", start_gate=start_gate)
            store.mark_submitting(
                submission_intent_id="submission-1",
                dispatch_cutpoint_id="dispatch-1",
                started_at="2026-09-14T12:00:00Z",
            )
            submitted = store.mark_submitted(
                submission_intent_id="submission-1",
                exchange_order_id="exchange-1",
                exchange_status="create_accepted",
            )
            replayed = store.mark_submitted(
                submission_intent_id="submission-1",
                exchange_order_id="exchange-1",
                exchange_status="create_accepted",
            )
            with pytest.raises(LifecycleSubmissionConflict, match="different exchange identity"):
                store.mark_submitted(
                    submission_intent_id="submission-1",
                    exchange_order_id="exchange-2",
                    exchange_status="create_accepted",
                )

        with PostgresUnitOfWork(factory) as restarted:
            stored = LifecycleSubmissionStore(restarted.connection).get_by_submission_intent_id(
                submission_intent_id="submission-1"
            )
            unresolved = LifecycleSubmissionStore(restarted.connection).unresolved()

        assert stored is not None
        assert replayed == submitted
        assert stored.lifecycle_state == "SUBMITTED"
        assert stored.exchange_order_id == "exchange-1"
        assert unresolved == ()
    finally:
        _drop_schema(settings)


def _start_gate(uow):
    spec, authorization = valid_gate_inputs()
    record, _ = LifecycleStartGateStore(uow.connection).accept(
        start_gate_id="start-gate-1",
        order_spec=spec,
        submit_authorized=authorization,
    )
    return record


def fake_submission_record(
    *,
    lifecycle_state: str = "READY_TO_SUBMIT",
    exchange_order_id: str | None = None,
) -> LifecycleSubmissionRecord:
    return LifecycleSubmissionRecord(
        submission_intent_id="submission-1",
        start_gate_id="start-gate-1",
        order_spec_id="order-spec-1",
        authorization_id="authorization-1",
        capital_grant_id="capital-grant-1",
        decision_cycle_id="decision-cycle-1",
        set_result_id="set-result-1",
        position_decision_id="position-decision-1",
        construction_result_id="construction-result-1",
        position_plan_id="position-plan-1",
        tranche_id="tranche-1",
        symbol="BTCUSDT",
        direction="LONG",
        target_client_order_id="client-order-1",
        lifecycle_state=lifecycle_state,
        order_spec_digest="0" * 64,
        submit_authorized_digest="1" * 64,
        start_gate_digest="2" * 64,
        payload={"lifecycle_submission_intent": {"submission_intent_id": "submission-1"}},
        payload_digest="3" * 64,
        dispatch_attempts=1 if lifecycle_state != "READY_TO_SUBMIT" else 0,
        last_dispatch_cutpoint_id="dispatch-1" if lifecycle_state != "READY_TO_SUBMIT" else None,
        last_dispatch_started_at="2026-09-14 12:00:00+00" if lifecycle_state != "READY_TO_SUBMIT" else None,
        last_uncertain_at=None,
        last_error_code=None,
        exchange_order_id=exchange_order_id,
        exchange_status="create_accepted" if exchange_order_id else None,
    )
