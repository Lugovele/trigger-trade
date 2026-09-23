from __future__ import annotations

from datetime import UTC, datetime
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

import pytest

from triggertrade.contracts import ContractBindingError, approved_contract_graph, validate_contract_edge
from triggertrade.lifecycle_order_events import build_closed_order_event_from_submission
from triggertrade.persistence import (
    DurableMessageStore,
    LifecycleOrderEventStore,
    LifecycleStartGateStore,
    LifecycleSubmissionStore,
    PortfolioFinalReceiptStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    ResearchStore,
    apply_postgres_migrations,
)
from triggertrade.services.trading_worker import build_target_trading_worker
from triggertrade.set_engine import DirectionResolutionScope, SetDurableHandler
from tests.integration.test_canonical_dispatcher_b12 import _prepare_spec_and_authorization
from tests.unit.test_lifecycle_order_events import valid_financial_result
from tests.unit.test_research_backend import _diagnostic_report_source_payload, _research_db, _service
from tests.unit.test_set_handler_b5b import _long_classifier, _request
from tests.unit.test_target_contracts import valid_payload


pytest.importorskip("psycopg")


def test_b13_integrated_owner_flow_dispatches_supported_routes_once_and_preserves_graph():
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
        assert set_record.result_inserted is True
        assert set_record.handoff_payload["market_handoff"]["snapshot"]["direction"] == "LONG"

        order_spec_id, authorization_id = _prepare_spec_and_authorization(factory)
        lifecycle_worker = _worker(factory, consumers=("Lifecycle",))
        assert lifecycle_worker.process_once().blocked is False
        assert lifecycle_worker.process_once().blocked is False

        with PostgresUnitOfWork(factory) as lifecycle_uow:
            start_gate = LifecycleStartGateStore(lifecycle_uow.connection).get_by_order_spec_id(
                order_spec_id=order_spec_id
            )
            assert start_gate is not None
            assert start_gate.authorization_id == authorization_id
            submission_store = LifecycleSubmissionStore(lifecycle_uow.connection)
            submission, _ = submission_store.prepare(
                submission_intent_id="submission-b13",
                start_gate=start_gate,
            )
            submission_store.mark_submitting(
                submission_intent_id=submission.submission_intent_id,
                dispatch_cutpoint_id="dispatch-b13",
                started_at="2026-09-15T12:00:00Z",
            )
            submitted = submission_store.mark_submitted(
                submission_intent_id=submission.submission_intent_id,
                exchange_order_id="exchange-b13",
                exchange_status="create_accepted",
            )
            event_payload = build_closed_order_event_from_submission(
                submitted,
                event_id="order-event-b13-final",
                financial_result=valid_financial_result(),
                occurred_at="2026-09-15T12:05:00Z",
                lifecycle_revision=7,
                cumulative_entry_filled_qty="1",
                close_commitment_quantity_basis="1",
            ).payload
            LifecycleOrderEventStore(lifecycle_uow.connection).append(event_payload)
            messages = DurableMessageStore(lifecycle_uow.connection)
            messages.append_outbox(
                message_id="order-event-b13-final",
                producer="Lifecycle",
                consumer="Portfolio",
                message_type="ORDER_EVENT",
                message_version="7",
                payload=event_payload,
                aggregate_id="tranche-1",
                correlation_id="submission-b13",
            )
            for setup_message in ("construction-result-1", "position-decision-1:event"):
                if messages.get_outbox(message_id=setup_message) is not None:
                    messages.mark_outbox_consumed(message_id=setup_message)

        portfolio_worker = _worker(factory, consumers=("Portfolio",))
        first = portfolio_worker.process_once()
        second = portfolio_worker.process_once()

        assert first.blocked is False
        assert second.blocked is False
        with PostgresUnitOfWork(factory) as verify:
            receipt = PortfolioFinalReceiptStore(verify.connection).get_by_result_id(result_id="result-1")
            order_event_outbox = DurableMessageStore(verify.connection).get_outbox(message_id="order-event-b13-final")
            order_spec_outbox = DurableMessageStore(verify.connection).get_outbox(message_id=order_spec_id)
            authorization_outbox = DurableMessageStore(verify.connection).get_outbox(message_id=authorization_id)

        assert receipt is not None
        assert receipt.result_id == "result-1"
        assert receipt.tranche_id == "tranche-1"
        assert order_event_outbox is not None and order_event_outbox.status == "CONSUMED"
        assert order_spec_outbox is not None and order_spec_outbox.status == "CONSUMED"
        assert authorization_outbox is not None and authorization_outbox.status == "CONSUMED"
        assert not any({edge.producer.value, edge.consumer.value} == {"Position", "API"} for edge in approved_contract_graph())
    finally:
        if migrated:
            _drop_schema(settings)


def test_b13_fail_closed_paths_do_not_reach_legacy_demo_or_position_api():
    with pytest.raises(ContractBindingError, match="Position -> API"):
        validate_contract_edge(
            producer="Position",
            consumer="API",
            contract_type="MARKET_DATA_REQUEST",
            payload=valid_payload("MARKET_DATA_REQUEST", "MARKET_DATA_REQUEST.request"),
            definition="MARKET_DATA_REQUEST.request",
        )

    code = (
        "import sys; "
        "import triggertrade.services.owner_dispatch; "
        "import triggertrade.services.trading_worker; "
        "forbidden = {"
        "'triggertrade.execution.paper', "
        "'triggertrade.execution.bybit', "
        "'triggertrade.execution.position_lifecycle', "
        "'triggertrade.strategies.buy_candidate'"
        "} & set(sys.modules); "
        "raise SystemExit('loaded legacy modules: ' + ', '.join(sorted(forbidden)) if forbidden else 0)"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    completed = subprocess.run([sys.executable, "-c", code], env=env, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, completed.stderr or completed.stdout

    settings = _settings()
    migrated = False
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        migrated = True
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            DurableMessageStore(uow.connection).append_outbox(
                message_id="market-handoff-b13",
                producer="Set",
                consumer="Position",
                message_type="MARKET_HANDOFF",
                message_version="4",
                payload={"market_handoff": {"contract_version": 4, "decision_cycle_id": "cycle-b13"}},
            )

        result = _worker(factory, consumers=("Position",)).process_once()

        assert result.blocked is True
        assert result.detail == "handler_not_certified:Position:MARKET_HANDOFF:4"
        with PostgresUnitOfWork(factory) as verify:
            outbox = DurableMessageStore(verify.connection).get_outbox(message_id="market-handoff-b13")
            inbox = DurableMessageStore(verify.connection).get_inbox(
                consumer="Position",
                message_id="market-handoff-b13",
            )
        assert outbox is not None and outbox.status == "IN_FLIGHT"
        assert inbox is None
    finally:
        if migrated:
            _drop_schema(settings)


def test_b13_research_reports_restart_as_read_only_diagnostics_without_feedback():
    root = Path("runtime") / f"b13-research-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        db, _rules = _research_db(root)
        _assert_b13_research_reports_restart_without_feedback(db)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _assert_b13_research_reports_restart_without_feedback(db: Path) -> None:
    store = ResearchStore(db)
    dataset, _ = store.archive_diagnostic_dataset(
        dataset_id="diag-b13-report-source",
        source_payload=_diagnostic_report_source_payload(),
        source_provenance={
            "source_kind": "SUPPLIED_DIAGNOSTIC_DATASET",
            "retrieved_at": "2026-09-15T00:00:00Z",
        },
        manifest={
            "dataset_kind": "B13_RESEARCH_REPORT_SOURCE",
            "symbols": ["BTCUSDT"],
            "timeframe": "1m",
        },
    )

    service = _service(db)
    entry = service.publish_entry_diagnostic_report(
        report_id="entry-report-b13",
        dataset_id=dataset.dataset_id,
        report_config={"report_definition_version": "ENTRY_REPORT_V1"},
        created_at="2026-09-15T00:01:00Z",
    )
    take_profit = service.publish_take_profit_diagnostic_report(
        report_id="tp-report-b13",
        dataset_id=dataset.dataset_id,
        report_config={
            "report_definition_version": "TP_REPORT_V1",
            "minimum_distance_alternatives": ["1.25"],
            "maximum_distance_alternatives": ["3.00"],
        },
        created_at="2026-09-15T00:02:00Z",
    )

    restarted = ResearchStore(db)
    recovered_entry = restarted.get_diagnostic_report("entry-report-b13")
    recovered_take_profit = restarted.get_diagnostic_report("tp-report-b13")

    assert recovered_entry == entry
    assert recovered_take_profit == take_profit
    assert recovered_entry.report_payload["canonical_feedback"] is False
    assert recovered_take_profit.report_payload["canonical_feedback"] is False
    assert set(recovered_entry.report_payload["outputs"]) == set(entry.report_definition["items"])
    assert set(recovered_take_profit.report_payload["outputs"]) == set(take_profit.report_definition["items"])
    assert "promotion" not in recovered_entry.report_payload
    assert "canonical_decision" not in recovered_take_profit.report_payload


def _worker(
    factory: PostgresConnectionFactory,
    *,
    consumers=("Portfolio", "Set", "Position", "Lifecycle"),
):
    from triggertrade.persistence.postgres_runtime_store import PostgresRuntimeStore

    return build_target_trading_worker(
        factory=factory,
        runtime_store=PostgresRuntimeStore(factory),
        worker_id="b13-worker",
        consumers=consumers,
        poll_seconds=1,
    )


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b13_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')
