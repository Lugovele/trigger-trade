from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import os
import uuid

import pytest

from triggertrade.contracts import parse_contract
from triggertrade.persistence import (
    DurableMessageStore,
    PositionConstructionWorkflow,
    PositionConstructionWorkflowConflict,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.position_rules import (
    ConstructionStatus,
    PositionConstructionCommand,
    evaluate_position_construction,
)
from tests.unit.test_capital_grants import NOW as GRANT_NOW, build_grant
from tests.unit.test_position_opportunity_b7a import NOW, PositionOpportunityHandler, command_for, handoff, rules_version


def test_b7b_constructs_exact_sizing_economics_and_order_spec_from_grant():
    evaluation = evaluate_position_construction(command())

    assert evaluation.status is ConstructionStatus.CONSTRUCTED
    assert evaluation.failed_gates == ()
    assert evaluation.order_spec is not None
    assert evaluation.sizing["target_order_notional"] == "500.733333333332"
    assert evaluation.sizing["final_qty"] == "5.007"
    assert evaluation.sizing["actual_order_notional"] == "500.7"
    assert evaluation.sizing["actual_committed_capital_exact"] == {"numerator": "5007", "denominator": "20"}
    assert evaluation.sizing["actual_committed_capital"] == "250.35"
    assert evaluation.economics["gross_rr"] == "10"
    assert evaluation.economics["gross_profit_tp"] == "50.07"
    assert evaluation.economics["expected_entry_fee"] == "0.10014"
    assert evaluation.economics["tp_exit_notional"] == "550.77"
    assert evaluation.economics["expected_tp_exit_fee"] == "0.3029235"
    assert evaluation.economics["net_profit_tp"] == "49.6669365"
    assert evaluation.economics["planned_net_edge_pct"] == "9.9195"
    assert evaluation.economics["funding_in_planned_net_edge"] is False

    spec = evaluation.order_spec.to_payload()
    construction = evaluation.construction_result.to_payload()
    parse_contract("ORDER_SPEC", spec)
    parse_contract("APPROVE_REJECT", construction, definition="APPROVE_REJECT.constructed")
    assert spec["order_spec"]["entry"]["quantity"] == "5.007"
    assert spec["order_spec"]["economics"]["actual_committed_capital"] == "250.35"
    assert spec["order_spec"]["economics"]["planned_net_edge_pct"] == "9.9195"
    assert construction["position_construction_result"]["approved_economics"]["approved_quantity"] == "5.007"
    assert construction["position_construction_result"]["rule_results"]["minimum_net_edge"]["calculated_value"] == "9.9195"


def test_b7b_rejects_zero_quantity_without_spec_or_repair():
    grant = build_grant()
    grant["capital_and_limits"]["requested_capital_per_tranche"] = "0.000000000001"

    evaluation = evaluate_position_construction(command(capital_grant=grant))

    assert evaluation.status is ConstructionStatus.REJECT
    assert evaluation.primary_reason == "QTY_ZERO_AFTER_FLOOR"
    assert evaluation.order_spec is None
    body = evaluation.construction_result.to_payload()["position_construction_result"]
    assert body["outcome"] == "REJECT"
    assert "order_spec_id" not in body


def test_b7b_rejects_net_edge_failure_without_spec():
    evaluation = evaluate_position_construction(
        command(rules=rules_with(minimum_net_edge_pct=Decimal("100")))
    )

    assert evaluation.status is ConstructionStatus.REJECT
    assert evaluation.primary_reason == "NET_EDGE_BELOW_MINIMUM"
    assert evaluation.order_spec is None
    rule = evaluation.construction_result.to_payload()["position_construction_result"]["rule_results"]["minimum_net_edge"]
    assert rule["enabled"] is True
    assert rule["status"] == "FAIL"
    assert rule["reason_code"] == "NET_EDGE_BELOW_MINIMUM"


def test_b7b_exact_threshold_equality_passes_and_just_over_rejects():
    exact = evaluate_position_construction(command(rules=rules_with(minimum_net_edge_pct=Decimal("9.9195"))))
    assert exact.status is ConstructionStatus.CONSTRUCTED

    just_over_net_edge = evaluate_position_construction(
        command(rules=rules_with(minimum_net_edge_pct=Decimal("9.919500000000000001")))
    )
    assert just_over_net_edge.status is ConstructionStatus.REJECT
    assert just_over_net_edge.primary_reason == "NET_EDGE_BELOW_MINIMUM"

    rr_equal_command = command()
    rr_equal_state = _copy(rr_equal_command.position_opportunity_state)
    rr_equal_state["position_opportunity_state"]["source_configuration"]["rules_version"]["draft"]["minimum_risk_reward"] = "10"
    rr_equal = evaluate_position_construction(_replace_state(rr_equal_command, rr_equal_state))
    assert rr_equal.status is ConstructionStatus.CONSTRUCTED

    rr_just_over_state = _copy(rr_equal_command.position_opportunity_state)
    rr_just_over_state["position_opportunity_state"]["source_configuration"]["rules_version"]["draft"][
        "minimum_risk_reward"
    ] = "10.000000000000000001"
    rr_just_over = evaluate_position_construction(_replace_state(rr_equal_command, rr_just_over_state))
    assert rr_just_over.status is ConstructionStatus.REJECT
    assert rr_just_over.primary_reason == "RR_BELOW_MINIMUM"


def test_b7b_rejects_leverage_above_venue_maximum():
    evaluation = evaluate_position_construction(command(rules=rules_with(leverage=Decimal("100"))))

    assert evaluation.status is ConstructionStatus.REJECT
    assert evaluation.primary_reason == "LEVERAGE_ABOVE_MAXIMUM"
    assert evaluation.order_spec is None


def test_b7b_max_leverage_equality_passes_and_report_ratios_use_qratio_floor():
    grant = build_grant()
    grant["capital_and_limits"]["venue_facts"]["instrument"]["max_order_qty"] = "200"
    equal_max = evaluate_position_construction(command(capital_grant=grant, rules=rules_with(leverage=Decimal("50"))))
    assert equal_max.status is ConstructionStatus.CONSTRUCTED

    altered = command(rules=rules_with(minimum_risk_reward=Decimal("0.3")))
    state = _copy(altered.position_opportunity_state)
    state["position_opportunity_state"]["evaluation"]["stop"]["price"] = "97"
    state["position_opportunity_state"]["evaluation"]["take_profit"]["price"] = "101"
    one_third = evaluate_position_construction(
        PositionConstructionCommand(
            event_id=altered.event_id,
            occurred_at=altered.occurred_at,
            construction_result_id=altered.construction_result_id,
            position_plan_id=altered.position_plan_id,
            tranche_id=altered.tranche_id,
            order_spec_id=altered.order_spec_id,
            capital_grant=altered.capital_grant,
            position_opportunity_state=state,
        )
    )
    assert one_third.status is ConstructionStatus.CONSTRUCTED
    assert one_third.economics["gross_rr"] == "0.333333333333333333"
    assert one_third.economics["gross_rr_exact"] == {"numerator": "1", "denominator": "3"}


def test_b7b_rejects_inconsistent_max_quantity_facts():
    max_below_min = changed_grant()
    max_below_min["capital_and_limits"]["requested_capital_per_tranche"] = "250.366666666666"
    max_below_min["capital_and_limits"]["venue_facts"]["instrument"]["max_order_qty"] = "0.0001"
    evaluation = evaluate_position_construction(command(capital_grant=max_below_min))
    assert evaluation.status is ConstructionStatus.REJECT
    assert evaluation.primary_reason == "INVALID_EXCHANGE_FACT"

    unsupported_na = build_grant()
    instrument = unsupported_na["capital_and_limits"]["venue_facts"]["instrument"]
    instrument["max_order_qty_status"] = "NOT_APPLICABLE"
    instrument["max_order_qty"] = "10"
    evaluation = evaluate_position_construction(command(capital_grant=unsupported_na))
    assert evaluation.status is ConstructionStatus.REJECT
    assert evaluation.primary_reason == "INVALID_EXCHANGE_FACT"

    unsupported_na_null = build_grant()
    instrument = unsupported_na_null["capital_and_limits"]["venue_facts"]["instrument"]
    instrument["max_order_qty_status"] = "NOT_APPLICABLE"
    instrument["max_order_qty"] = None
    evaluation = evaluate_position_construction(command(capital_grant=unsupported_na_null))
    assert evaluation.status is ConstructionStatus.REJECT
    assert evaluation.primary_reason == "INVALID_EXCHANGE_FACT"


pytest.importorskip("psycopg")


def test_b7b_workflow_persists_success_replays_and_publishes_two_outboxes():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            workflow = PositionConstructionWorkflow(uow.connection)
            record, inserted = workflow.evaluate_and_record(command())
            assert inserted is True
            replayed, inserted = workflow.evaluate_and_record(command())
            assert inserted is False
            assert replayed.payload_digest == record.payload_digest
            construction_outbox = DurableMessageStore(uow.connection).get_outbox(message_id="construction-result-1")
            spec_outbox = DurableMessageStore(uow.connection).get_outbox(message_id="order-spec-1")
            assert construction_outbox is not None
            assert construction_outbox.producer == "Position"
            assert construction_outbox.consumer == "Portfolio"
            assert construction_outbox.message_type == "APPROVE_REJECT"
            assert spec_outbox is not None
            assert spec_outbox.producer == "Position"
            assert spec_outbox.consumer == "Lifecycle"
            assert spec_outbox.message_type == "ORDER_SPEC"
            assert _outbox_count(uow.connection) == 2

        with PostgresUnitOfWork(factory) as restarted:
            stored = PositionConstructionWorkflow(restarted.connection).get_by_construction_result_id(
                construction_result_id="construction-result-1"
            )
        assert stored is not None
        assert stored.status == "CONSTRUCTED"
        assert stored.order_spec is not None
        assert stored.payload["position_construction_evaluation"]["sizing"]["actual_committed_capital"] == "250.35"
    finally:
        _drop_schema(settings)


def test_b7b_workflow_persists_failure_without_order_spec_or_lifecycle_outbox():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            record, inserted = PositionConstructionWorkflow(uow.connection).evaluate_and_record(
                command(rules=rules_with(minimum_net_edge_pct=Decimal("100")))
            )
            assert inserted is True
            assert record.status == "REJECT"
            assert record.order_spec is None
            construction_outbox = DurableMessageStore(uow.connection).get_outbox(message_id="construction-result-1")
            assert construction_outbox is not None
            assert DurableMessageStore(uow.connection).get_outbox(message_id="order-spec-1") is None
            assert _outbox_count(uow.connection) == 1

        with PostgresUnitOfWork(factory) as restarted:
            stored = PositionConstructionWorkflow(restarted.connection).get_by_construction_result_id(
                construction_result_id="construction-result-1"
            )
        assert stored is not None
        assert stored.status == "REJECT"
        assert stored.order_spec is None
    finally:
        _drop_schema(settings)


def test_b7b_workflow_conflicts_changed_replay_and_rolls_back_all_cutpoints():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with pytest.raises(RuntimeError):
            with PostgresUnitOfWork(factory) as uow:
                PositionConstructionWorkflow(uow.connection).evaluate_and_record(command())
                raise RuntimeError("rollback cutpoint")

        with PostgresUnitOfWork(factory) as uow:
            assert PositionConstructionWorkflow(uow.connection).get_by_construction_result_id(
                construction_result_id="construction-result-1"
            ) is None
            assert DurableMessageStore(uow.connection).get_outbox(message_id="construction-result-1") is None
            assert DurableMessageStore(uow.connection).get_outbox(message_id="order-spec-1") is None

            workflow = PositionConstructionWorkflow(uow.connection)
            workflow.evaluate_and_record(command())
            with pytest.raises(PositionConstructionWorkflowConflict):
                workflow.evaluate_and_record(command(capital_grant=changed_grant()))
    finally:
        _drop_schema(settings)


def test_b7b_workflow_rolls_back_after_construction_before_spec(monkeypatch):
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with pytest.raises(RuntimeError):
            with PostgresUnitOfWork(factory) as uow:
                workflow = PositionConstructionWorkflow(uow.connection)

                def fail_spec(*args, **kwargs):
                    raise RuntimeError("spec cutpoint")

                monkeypatch.setattr(workflow._specs, "record", fail_spec)
                workflow.evaluate_and_record(command())

        with PostgresUnitOfWork(factory) as uow:
            assert PositionConstructionWorkflow(uow.connection).get_by_construction_result_id(
                construction_result_id="construction-result-1"
            ) is None
            assert DurableMessageStore(uow.connection).get_outbox(message_id="construction-result-1") is None
            assert DurableMessageStore(uow.connection).get_outbox(message_id="order-spec-1") is None
    finally:
        _drop_schema(settings)


def test_b7b_workflow_rolls_back_after_owner_state_before_construction(monkeypatch):
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with pytest.raises(RuntimeError):
            with PostgresUnitOfWork(factory) as uow:
                workflow = PositionConstructionWorkflow(uow.connection)

                def fail_construction(*args, **kwargs):
                    raise RuntimeError("construction cutpoint")

                monkeypatch.setattr(workflow._constructions, "record", fail_construction)
                workflow.evaluate_and_record(command())

        with PostgresUnitOfWork(factory) as uow:
            assert PositionConstructionWorkflow(uow.connection).get_by_construction_result_id(
                construction_result_id="construction-result-1"
            ) is None
            assert DurableMessageStore(uow.connection).get_outbox(message_id="construction-result-1") is None
            assert DurableMessageStore(uow.connection).get_outbox(message_id="order-spec-1") is None
    finally:
        _drop_schema(settings)


def test_b7b_constructed_workflow_without_spec_fails_closed_on_restart():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            PositionConstructionWorkflow(uow.connection).evaluate_and_record(command())
            with uow.connection.cursor() as cursor:
                cursor.execute("DELETE FROM triggertrade_order_specs WHERE order_spec_id = %s", ("order-spec-1",))

        with PostgresUnitOfWork(factory) as restarted:
            with pytest.raises(Exception, match="without order spec"):
                PositionConstructionWorkflow(restarted.connection).get_by_construction_result_id(
                    construction_result_id="construction-result-1"
                )
    finally:
        _drop_schema(settings)


def command(*, capital_grant: dict[str, object] | None = None, rules=None) -> PositionConstructionCommand:
    result = PositionOpportunityHandler().evaluate(
        command_for(
            handoff=handoff(),
            rules=rules if rules is not None else rules_version(),
        )
    )
    return PositionConstructionCommand(
        event_id="construction-event-1",
        occurred_at=GRANT_NOW,
        construction_result_id="construction-result-1",
        position_plan_id="position-plan-1",
        tranche_id="tranche-1",
        order_spec_id="order-spec-1",
        capital_grant=build_grant() if capital_grant is None else capital_grant,
        position_opportunity_state=result.to_state_payload(),
    )


def changed_grant() -> dict[str, object]:
    grant = build_grant()
    grant["capital_and_limits"]["requested_capital_per_tranche"] = "200"
    return grant


def rules_with(
    *,
    minimum_net_edge_pct: Decimal | None = None,
    minimum_risk_reward: Decimal | None = None,
    leverage: Decimal | None = None,
):
    current = rules_version()
    draft = current.draft
    if minimum_net_edge_pct is not None:
        draft = replace(draft, minimum_net_edge_pct=minimum_net_edge_pct)
    if minimum_risk_reward is not None:
        draft = replace(draft, minimum_risk_reward=minimum_risk_reward)
    if leverage is not None:
        draft = replace(draft, leverage=leverage)
    return replace(current, draft=draft)


def _copy(payload):
    import copy

    return copy.deepcopy(payload)


def _replace_state(command: PositionConstructionCommand, state) -> PositionConstructionCommand:
    return PositionConstructionCommand(
        event_id=command.event_id,
        occurred_at=command.occurred_at,
        construction_result_id=command.construction_result_id,
        position_plan_id=command.position_plan_id,
        tranche_id=command.tranche_id,
        order_spec_id=command.order_spec_id,
        capital_grant=command.capital_grant,
        position_opportunity_state=state,
    )


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b7b_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def _outbox_count(connection) -> int:
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM triggertrade_outbox_messages")
        return int(cursor.fetchone()[0])
