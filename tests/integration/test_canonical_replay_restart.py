from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
import os
from pathlib import Path
import uuid

import pytest

from triggertrade.lifecycle_order_events import build_closed_order_event_from_submission
from triggertrade.persistence import (
    DurableMessageStore,
    FactualEvidenceConflict,
    FactualEvidenceStore,
    LifecycleReconciliationConflict,
    LifecycleReconciliationStore,
    LifecycleOrderEventStore,
    LifecycleStartGateStore,
    LifecycleSubmissionStore,
    PortfolioCurrentBookingWorkflow,
    PortfolioFinalReceiptStore,
    PortfolioGrantDecisionStore,
    PositionConstructionWorkflow,
    PositionOpportunityStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    ResearchStore,
    ResearchStoreError,
    apply_postgres_migrations,
)
from triggertrade.set_engine import DirectionResolutionScope, SetDurableHandler
from tests.unit.test_lifecycle_reconciliation import native_event, resolution_event
from tests.unit.test_capital_grants import NOW, approved_decision, venue_facts
from tests.unit.test_lifecycle_order_events import valid_financial_result
from tests.unit.test_portfolio_current_booking_b8c import policy as booking_policy
from tests.unit.test_portfolio_grants_b8b import policy_for as grant_policy
from tests.unit.test_portfolio_grants_b8b import portfolio_state
from tests.unit.test_position_construction_b7b import command as construction_command
from tests.unit.test_position_opportunity_b7a import command_for as opportunity_command
from tests.unit.test_position_opportunity_b7a import handoff as opportunity_handoff
from tests.unit.test_position_opportunity_b7a import rules_version
from tests.unit.test_set_handler_b5b import _long_classifier, _request


pytest.importorskip("psycopg")


START = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
END = START + timedelta(minutes=1)


def test_b11_integrated_owner_restart_replay_keeps_canonical_bytes_and_once_only_effects():
    settings = _settings()
    migrated = False
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        migrated = True
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as set_uow:
            set_record = SetDurableHandler(set_uow.connection).resolve(
                _request(
                    direction_scope=DirectionResolutionScope.F005_GOVERNED,
                    classifier_inputs=_long_classifier(),
                )
            )
        with PostgresUnitOfWork(factory) as set_restart:
            set_replay = SetDurableHandler(set_restart.connection).resolve(
                _request(
                    direction_scope=DirectionResolutionScope.F005_GOVERNED,
                    classifier_inputs=_long_classifier(),
                )
            )

        assert set_record.result_inserted is True
        assert set_replay.result_inserted is False
        assert set_replay.result_payload == set_record.result_payload

        with PostgresUnitOfWork(factory) as position_uow:
            opportunity, opportunity_inserted = PositionOpportunityStore(position_uow.connection).evaluate_and_record(
                opportunity_command(handoff=opportunity_handoff(), rules=rules_version())
            )
        with PostgresUnitOfWork(factory) as position_restart:
            opportunity_replay = PositionOpportunityStore(position_restart.connection).get_by_position_decision_id(
                position_decision_id=opportunity.position_decision_id
            )

        assert opportunity_inserted is True
        assert opportunity_replay is not None
        assert opportunity_replay.payload_digest == opportunity.payload_digest

        with PostgresUnitOfWork(factory) as grant_uow:
            grant, grant_inserted = PortfolioGrantDecisionStore(grant_uow.connection).evaluate_and_record(
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
        assert grant_inserted is True
        assert grant.capital_grant is not None

        with PostgresUnitOfWork(factory) as construction_uow:
            construction, construction_inserted = PositionConstructionWorkflow(
                construction_uow.connection
            ).evaluate_and_record(
                construction_command(capital_grant=grant.capital_grant.payload)
            )
        assert construction_inserted is True
        assert construction.order_spec is not None

        with PostgresUnitOfWork(factory) as booking_uow:
            booking, booking_inserted = PortfolioCurrentBookingWorkflow(booking_uow.connection).evaluate_and_record(
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
        assert booking_inserted is True
        assert booking.authorization is not None

        with PostgresUnitOfWork(factory) as lifecycle_uow:
            start_gate, _ = LifecycleStartGateStore(lifecycle_uow.connection).accept(
                start_gate_id="start-gate-1",
                order_spec=construction.order_spec.payload,
                submit_authorized=booking.authorization.payload,
            )
            submission_store = LifecycleSubmissionStore(lifecycle_uow.connection)
            submission, submission_inserted = submission_store.prepare(
                submission_intent_id="submission-1",
                start_gate=start_gate,
            )
            submission_store.mark_submitting(
                submission_intent_id=submission.submission_intent_id,
                dispatch_cutpoint_id="dispatch-1",
                started_at="2026-09-14T12:00:00Z",
            )
            submitted = submission_store.mark_submitted(
                submission_intent_id=submission.submission_intent_id,
                exchange_order_id="exchange-1",
                exchange_status="create_accepted",
            )
            event_payload = build_closed_order_event_from_submission(
                submitted,
                event_id="order-event-final-1",
                financial_result=valid_financial_result(),
                occurred_at="2026-09-14T12:05:00Z",
                lifecycle_revision=7,
                cumulative_entry_filled_qty="1",
                close_commitment_quantity_basis="1",
            ).payload
            event, event_inserted = LifecycleOrderEventStore(lifecycle_uow.connection).append(event_payload)
            receipt, receipt_inserted = PortfolioFinalReceiptStore(lifecycle_uow.connection).accept_order_event(
                order_event_payload=event_payload,
                delivered_at="2026-09-14T12:05:01Z",
            )

        assert submission_inserted is True
        assert event_inserted is True
        assert receipt_inserted is True

        with PostgresUnitOfWork(factory) as replay_uow:
            grant_replay = PortfolioGrantDecisionStore(replay_uow.connection).get_by_position_decision_id(
                position_decision_id=grant.position_decision_id
            )
            construction_replay = PositionConstructionWorkflow(replay_uow.connection).get_by_construction_result_id(
                construction_result_id=construction.construction_result_id
            )
            booking_replay = PortfolioCurrentBookingWorkflow(replay_uow.connection).get_by_construction_result_id(
                construction_result_id=construction.construction_result_id
            )
            submission_replay = LifecycleSubmissionStore(replay_uow.connection).get_by_submission_intent_id(
                submission_intent_id="submission-1"
            )
            event_replay = LifecycleOrderEventStore(replay_uow.connection).append(event_payload)[0]
            receipt_replay, receipt_replay_inserted = PortfolioFinalReceiptStore(
                replay_uow.connection
            ).accept_order_event(
                order_event_payload=event_payload,
                delivered_at="2026-09-14T12:07:59Z",
            )
            outbox_summary = _outbox_summary(replay_uow.connection)

        assert grant_replay is not None
        assert grant_replay.payload_digest == grant.payload_digest
        assert construction_replay is not None
        assert construction_replay.payload_digest == construction.payload_digest
        assert booking_replay is not None
        assert booking_replay.payload_digest == booking.payload_digest
        assert submission_replay is not None
        assert submission_replay.exchange_order_id == "exchange-1"
        assert event_replay.payload_digest == event.payload_digest
        assert receipt_replay_inserted is False
        assert receipt_replay.payload_digest == receipt.payload_digest
        assert receipt_replay.delivered_at == "2026-09-14T12:05:01Z"
        assert set_record.decision_cycle_id is not None
        position_decision_event_id = opportunity.payload["position_opportunity_state"]["decision"]["event_id"]
        assert outbox_summary == {
            ("APPROVE_REJECT", "construction-result-1"): 1,
            ("APPROVE_REJECT", position_decision_event_id): 1,
            ("CAPITAL_AND_LIMITS", "grant-1"): 1,
            ("MARKET_HANDOFF", set_record.decision_cycle_id): 1,
            ("ORDER_SPEC", "order-spec-1"): 1,
            ("SUBMIT_AUTHORIZED", "auth-1"): 1,
        }
        assert _owner_state_count(factory, "Portfolio", "portfolio_final_receipt") == 1
    finally:
        if migrated:
            _drop_schema(settings)


def test_b11_concurrent_final_receipt_redelivery_records_one_portfolio_effect():
    settings = _settings()
    migrated = False
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        migrated = True
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        event_payload = _closed_event_from_real_submission(factory)

        def accept(delivered_at: str):
            with PostgresUnitOfWork(factory) as uow:
                return PortfolioFinalReceiptStore(uow.connection).accept_order_event(
                    order_event_payload=event_payload,
                    delivered_at=delivered_at,
                )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(accept, "2026-09-14T12:05:01Z"),
                executor.submit(accept, "2026-09-14T12:05:02Z"),
            ]
            results = [future.result(timeout=30) for future in futures]

        records = [record for record, _inserted in results]
        insertions = [inserted for _record, inserted in results]
        assert sorted(insertions) == [False, True]
        assert records[0].payload_digest == records[1].payload_digest
        assert records[0].delivered_at in {"2026-09-14T12:05:01Z", "2026-09-14T12:05:02Z"}
        assert records[1].delivered_at == records[0].delivered_at

        with PostgresUnitOfWork(factory) as restarted:
            by_result = PortfolioFinalReceiptStore(restarted.connection).get_by_result_id(result_id="result-1")
            by_tranche = PortfolioFinalReceiptStore(restarted.connection).get_by_tranche_id(tranche_id="tranche-1")
        assert by_result is not None
        assert by_tranche is not None
        assert by_result.payload_digest == records[0].payload_digest
        assert by_tranche.payload_digest == records[0].payload_digest
        assert _owner_state_count(factory, "Portfolio", "portfolio_final_receipt") == 1
    finally:
        if migrated:
            _drop_schema(settings)


def test_b11_source_history_and_diagnostic_manifest_recover_without_fabricated_data(tmp_path: Path):
    settings = _settings()
    migrated = False
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        migrated = True
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            fact_store = FactualEvidenceStore(uow.connection)
            b3_record, _ = fact_store.put_evidence(
                evidence_id="rpt-b3-market-page-1",
                owner="Set",
                evidence_kind="MARKET_DATA_PAGE",
                payload={
                    "selection_id": "sel-b11",
                    "page_id": "page-b11",
                    "dataset": "TICKER",
                    "symbol": "BTCUSDT",
                    "facts": {"last_price": "25000.1"},
                },
                raw_payload={"native_id": "raw-b11", "lastPrice": "25000.10"},
                provenance={
                    "source_endpoint": "/v5/market/tickers",
                    "source_record_id": "BTCUSDT",
                    "retrieved_at": "2026-09-14T12:00:00Z",
                },
                anchors=("market:/v5/market/tickers:BTCUSDT:b11",),
            )
            challenge = fact_store.preflight_known_evidence(
                challenge_scope="MARKET_DATA",
                anchors=("market:/v5/market/tickers:BTCUSDT:b11",),
                raw_payload={"native_id": "raw-b11", "lastPrice": "25001.00"},
                candidate_payload={
                    "selection_id": "sel-b11",
                    "page_id": "page-b11",
                    "dataset": "TICKER",
                    "symbol": "BTCUSDT",
                    "facts": {"last_price": "25001"},
                },
                reason="source history replay produced changed accepted facts",
            )

        with pytest.raises(RuntimeError):
            with PostgresUnitOfWork(factory) as failed_import:
                FactualEvidenceStore(failed_import.connection).put_evidence(
                    evidence_id="rpt-b3-uncommitted",
                    owner="Set",
                    evidence_kind="MARKET_DATA_PAGE",
                    payload={"page_id": "uncommitted"},
                    anchors=("market:uncommitted",),
                )
                raise RuntimeError("failed source-history import")

        with PostgresUnitOfWork(factory) as restarted:
            fact_store = FactualEvidenceStore(restarted.connection)
            recovered = fact_store.get_evidence_by_anchor(anchor_key="market:/v5/market/tickers:BTCUSDT:b11")
            recovered_challenges = fact_store.list_challenges(challenge_scope="MARKET_DATA")
            missing = fact_store.get_evidence(evidence_id="rpt-b3-uncommitted")

        assert challenge.challenge is not None
        assert challenge.challenge.challenge_kind == "CONTENT_CONTRADICTION"
        assert recovered is not None
        assert recovered.evidence_id == b3_record.evidence_id
        assert recovered.payload_digest == b3_record.payload_digest
        assert missing is None
        assert [item.challenge_id for item in recovered_challenges] == [challenge.challenge.challenge_id]

        research_store = ResearchStore(tmp_path / "research.sqlite3")
        manifest = {
            "dataset_kind": "OWNER_HISTORY_DIAGNOSTIC",
            "symbols": ["BTCUSDT"],
            "timeframe": "1m",
            "period_start": START.isoformat().replace("+00:00", "Z"),
            "period_end": END.isoformat().replace("+00:00", "Z"),
            "members": [
                {"record_id": b3_record.evidence_id, "digest": b3_record.payload_digest, "owner": "Set"},
                {"record_id": "position-decision-1", "owner": "Position"},
                {"record_id": "order-event-final-1", "owner": "Order Lifecycle"},
                {"record_id": "result-1", "owner": "Portfolio"},
            ],
        }
        diagnostic, inserted = research_store.archive_diagnostic_dataset(
            dataset_id="diag-b11-owner-history-1",
            source_payload={
                "accepted_evidence": [b3_record.payload],
                "challenges": [challenge.challenge.challenge_id],
                "note": "B11 source-history recovery evidence only",
            },
            source_provenance={
                "source_kind": "B11_OWNER_HISTORY_STRESS",
                "retrieved_at": START.isoformat().replace("+00:00", "Z"),
                "source_ref": "unit://b11/source-history",
            },
            manifest=manifest,
            created_at=START.isoformat().replace("+00:00", "Z"),
        )
        replayed, replay_inserted = research_store.archive_diagnostic_dataset(
            dataset_id="diag-b11-owner-history-1",
            source_payload={
                "accepted_evidence": [b3_record.payload],
                "challenges": [challenge.challenge.challenge_id],
                "note": "B11 source-history recovery evidence only",
            },
            source_provenance={
                "source_kind": "B11_OWNER_HISTORY_STRESS",
                "retrieved_at": START.isoformat().replace("+00:00", "Z"),
                "source_ref": "unit://b11/source-history",
            },
            manifest=manifest,
            created_at=START.isoformat().replace("+00:00", "Z"),
        )

        assert inserted is True
        assert replay_inserted is False
        assert replayed.manifest_digest == diagnostic.manifest_digest
        assert diagnostic.manifest["members"][0]["digest"] == b3_record.payload_digest
        assert (tmp_path / "research-diagnostic-objects" / f"{diagnostic.content_digest}.json").exists()
        with pytest.raises(ResearchStoreError, match="different content"):
            research_store.archive_diagnostic_dataset(
                dataset_id="diag-b11-owner-history-1",
                source_payload={"accepted_evidence": [], "challenges": []},
                source_provenance={
                    "source_kind": "B11_OWNER_HISTORY_STRESS",
                    "retrieved_at": START.isoformat().replace("+00:00", "Z"),
                    "source_ref": "unit://b11/source-history",
                },
                manifest=manifest,
            )
    finally:
        if migrated:
            _drop_schema(settings)


def test_b11_reconciliation_history_handles_incomplete_prefix_stale_revision_and_conflict():
    settings = _settings()
    migrated = False
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        migrated = True
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleReconciliationStore(uow.connection)
            incomplete = store.record_event(native_event())

        with PostgresUnitOfWork(factory) as after_incomplete_restart:
            tombstone = LifecycleReconciliationStore(after_incomplete_restart.connection).get_tombstone(
                native_observation_id="obs-1"
            )

        assert incomplete.inserted is True
        assert incomplete.resolved is False
        assert tombstone is not None
        assert tombstone.state == "UNRESOLVED"
        assert tombstone.unresolved_block_active is True

        with PostgresUnitOfWork(factory) as uow:
            store = LifecycleReconciliationStore(uow.connection)
            resolved = store.record_event(resolution_event())
            stale_resolution_event = resolution_event(event_id="resolution-event-stale-obs")
            stale_resolution = stale_resolution_event["order_event"]["resolution"]
            stale_resolution["native_observation_id"] = "obs-stale"
            stale_resolution["attribution_resolution_id"] = "resolution-stale"
            stale_resolution_event["order_event"]["resolution"] = stale_resolution
            store.record_event(stale_resolution_event)
            stale_observation_event = native_event(
                native_observation_id="obs-stale",
                source_event_id="source-event-stale",
                source_execution_id="exec-stale",
                source_ref="GET_EXECUTIONS:exec-stale",
            )
            stale_observation_event["order_event"]["event_id"] = "native-event-after-resolution"
            stale_after_resolution = store.record_event(stale_observation_event)

        with PostgresUnitOfWork(factory) as restarted:
            store = LifecycleReconciliationStore(restarted.connection)
            final_tombstone = store.get_tombstone(native_observation_id="obs-1")
            records = store.list_records(native_observation_id="obs-1")

        assert resolved.resolved is True
        assert stale_after_resolution.stale is True
        assert stale_after_resolution.record.accepted is False
        assert final_tombstone is not None
        assert final_tombstone.state == "RESOLVED"
        assert final_tombstone.unresolved_block_active is False
        assert [record.accepted for record in records] == [True, True]
        assert stale_after_resolution.stale is True
        assert stale_after_resolution.record.accepted is False

        with PostgresUnitOfWork(factory) as conflict_uow:
            changed_same_revision = native_event(quantity="0.50")
            changed_same_revision["order_event"]["event_id"] = "native-event-conflict"
            with pytest.raises(LifecycleReconciliationConflict, match="different content"):
                LifecycleReconciliationStore(conflict_uow.connection).record_event(changed_same_revision)

        with PostgresUnitOfWork(factory) as conflict_restart:
            conflicted = LifecycleReconciliationStore(conflict_restart.connection).get_tombstone(
                native_observation_id="obs-1"
            )
        assert conflicted is not None
        assert conflicted.integrity_state == "CONFLICT"
    finally:
        if migrated:
            _drop_schema(settings)


def _closed_event_from_real_submission(factory: PostgresConnectionFactory) -> dict[str, object]:
    with PostgresUnitOfWork(factory) as uow:
        grant_record, _ = PortfolioGrantDecisionStore(uow.connection).evaluate_and_record(
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
        assert grant_record.capital_grant is not None
        construction, _ = PositionConstructionWorkflow(uow.connection).evaluate_and_record(
            construction_command(capital_grant=grant_record.capital_grant.payload)
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
        start_gate, _ = LifecycleStartGateStore(uow.connection).accept(
            start_gate_id="start-gate-1",
            order_spec=construction.order_spec.payload,
            submit_authorized=booking.authorization.payload,
        )
        submission_store = LifecycleSubmissionStore(uow.connection)
        submission, _ = submission_store.prepare(submission_intent_id="submission-1", start_gate=start_gate)
        submission_store.mark_submitting(
            submission_intent_id=submission.submission_intent_id,
            dispatch_cutpoint_id="dispatch-1",
            started_at="2026-09-14T12:00:00Z",
        )
        submitted = submission_store.mark_submitted(
            submission_intent_id=submission.submission_intent_id,
            exchange_order_id="exchange-1",
            exchange_status="create_accepted",
        )
        event_payload = build_closed_order_event_from_submission(
            submitted,
            event_id="order-event-final-1",
            financial_result=valid_financial_result(),
            occurred_at="2026-09-14T12:05:00Z",
            lifecycle_revision=7,
            cumulative_entry_filled_qty="1",
            close_commitment_quantity_basis="1",
        ).payload
        LifecycleOrderEventStore(uow.connection).append(event_payload)
        return event_payload


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b11_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def _outbox_summary(connection) -> dict[tuple[str, str], int]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT message_type, message_id, count(*)
            FROM triggertrade_outbox_messages
            GROUP BY message_type, message_id
            """
        )
        return {(str(message_type), str(message_id)): int(count) for message_type, message_id, count in cursor.fetchall()}


def _owner_state_count(factory: PostgresConnectionFactory, owner: str, state_type: str) -> int:
    with PostgresUnitOfWork(factory) as uow:
        with uow.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT count(*)
                FROM triggertrade_owner_state_records
                WHERE owner = %s AND state_type = %s
                """,
                (owner, state_type),
            )
            return int(cursor.fetchone()[0])
