from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    CapitalGrantStore,
    DurableMessageStore,
    PortfolioCurrentBookingWorkflow,
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresSettings,
    PostgresUnitOfWork,
    PositionConstructionWorkflow,
    SubmitAuthorizationStore,
    apply_postgres_migrations,
)
from triggertrade.portfolio_current_booking import (
    PortfolioCurrentBookingPolicy,
    PortfolioCurrentBookingStatus,
    evaluate_current_portfolio_booking,
)
from triggertrade.position_rules import evaluate_position_construction
from tests.unit.test_capital_grants import NOW, approved_decision
from tests.unit.test_portfolio_grants_b8b import portfolio_state
from tests.unit.test_position_construction_b7b import command


def test_b8c_authorizes_exact_h_without_holding_grant_c_or_recomputing_position_outputs():
    construction = _constructed_result()
    grant = _grant()
    evaluation = evaluate_current_portfolio_booking(
        booking_id="booking-1",
        authorization_id="auth-1",
        capital_grant=grant,
        construction_result=construction,
        portfolio_state=portfolio_state(global_held="749.65", coin_held="249.65", global_tranches=3, coin_tranches=1),
        policy=policy(),
        authorized_at=NOW,
    )

    assert evaluation.status is PortfolioCurrentBookingStatus.AUTHORIZED
    authorization = evaluation.submit_authorized.to_payload()["submit_authorized"]
    assert authorization["held_committed_capital"] == "250.35"
    assert authorization["held_committed_capital"] != grant["capital_and_limits"]["requested_capital_per_tranche"]
    assert evaluation.gate_results["global_capital"]["after"] == "1000"
    assert evaluation.gate_results["coin_capital"]["after"] == "500"


def test_b8c_current_capacity_blocks_even_when_stale_grant_snapshot_has_capacity():
    grant = _grant()
    assert grant["capital_and_limits"]["remaining_global_capital"] == "1000"

    evaluation = evaluate_current_portfolio_booking(
        booking_id="booking-1",
        authorization_id="auth-1",
        capital_grant=grant,
        construction_result=_constructed_result(),
        portfolio_state=portfolio_state(global_held="749.650000000001", coin_held="0"),
        policy=policy(),
        authorized_at=NOW,
    )

    assert evaluation.status is PortfolioCurrentBookingStatus.BLOCKED
    assert evaluation.primary_reason == "GLOBAL_CAPITAL_EXCEEDED"
    assert evaluation.submit_authorized is None
    assert evaluation.gate_results["global_capital"]["after"] == "1000.000000000001"


def test_b8c_unavailable_and_frontier_gates_fail_closed_without_authorization():
    evaluation = evaluate_current_portfolio_booking(
        booking_id="booking-1",
        authorization_id="auth-1",
        capital_grant=_grant(),
        construction_result=_constructed_result(),
        portfolio_state=portfolio_state(health="RECONCILING"),
        policy=policy(daily_loss_blocked=True, cooldown_status="UNAVAILABLE", incident_frontier_clear=False),
        authorized_at=NOW,
    )

    assert evaluation.status is PortfolioCurrentBookingStatus.UNAVAILABLE
    assert evaluation.submit_authorized is None
    assert evaluation.evaluated_reasons == (
        "PORTFOLIO_STATE_UNAVAILABLE",
        "DAILY_LOSS_BLOCKED",
        "COOLDOWN_UNAVAILABLE",
        "INCIDENT_FRONTIER_BLOCKED",
    )


def test_b8c_store_authorizes_replays_and_publishes_submit_authorized_with_cooldown_pin():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            _seed_constructed_position(uow.connection)
            workflow = PortfolioCurrentBookingWorkflow(uow.connection)
            record, inserted = workflow.evaluate_and_record(
                booking_id="booking-1",
                authorization_id="auth-1",
                construction_result_id="construction-result-1",
                portfolio_state=portfolio_state(global_held="749.65", coin_held="249.65", global_tranches=3, coin_tranches=1),
                policy=policy(),
                authorized_at=NOW,
            )
            replayed, replay_inserted = workflow.evaluate_and_record(
                booking_id="booking-1",
                authorization_id="auth-1",
                construction_result_id="construction-result-1",
                portfolio_state=portfolio_state(global_held="0", coin_held="0"),
                policy=policy(global_position_cap="999999", coin_allocation_cap="999999"),
                authorized_at=NOW,
            )

            assert inserted is True
            assert replay_inserted is False
            assert replayed.payload_digest == record.payload_digest
            assert record.authorization is not None
            assert record.authorization.held_committed_capital == "250.35"
            assert record.cooldown is not None
            assert record.cooldown.pin.portfolio_config_id == "portfolio-config-1"
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id="auth-1")
            assert outbox is not None
            assert outbox.producer == "Portfolio"
            assert outbox.consumer == "Lifecycle"
            assert outbox.message_type == "SUBMIT_AUTHORIZED"
            assert _outbox_count(uow.connection, message_id="auth-1") == 1

        with PostgresUnitOfWork(factory) as restarted:
            stored = PortfolioCurrentBookingWorkflow(restarted.connection).get_by_construction_result_id(
                construction_result_id="construction-result-1"
            )
            assert stored is not None
            assert stored.status == "AUTHORIZED"
            assert stored.authorization is not None
            assert stored.cooldown is not None
    finally:
        _drop_schema(settings)


def test_b8c_store_denial_retains_reasons_without_partial_authorization_or_outbox():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            _seed_constructed_position(uow.connection)
            record, inserted = PortfolioCurrentBookingWorkflow(uow.connection).evaluate_and_record(
                booking_id="booking-1",
                authorization_id="auth-1",
                construction_result_id="construction-result-1",
                portfolio_state=portfolio_state(global_held="999", coin_held="499"),
                policy=policy(),
                authorized_at=NOW,
            )

            assert inserted is True
            assert record.status == "BLOCKED"
            assert record.authorization is None
            assert record.payload["portfolio_current_booking_workflow"]["booking"]["evaluated_reasons"] == [
                "GLOBAL_CAPITAL_EXCEEDED",
                "COIN_CAPITAL_EXCEEDED",
            ]
            assert SubmitAuthorizationStore(uow.connection).get_by_authorization_id(authorization_id="auth-1") is None
            assert DurableMessageStore(uow.connection).get_outbox(message_id="auth-1") is None

        with PostgresUnitOfWork(factory) as restarted:
            stored = PortfolioCurrentBookingWorkflow(restarted.connection).get_by_construction_result_id(
                construction_result_id="construction-result-1"
            )
            assert stored is not None
            assert stored.status == "BLOCKED"
            assert stored.authorization is None
    finally:
        _drop_schema(settings)


def test_b8c_store_conflicts_changed_replay_and_rolls_back_authorization_cutpoints(monkeypatch):
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            _seed_constructed_position(uow.connection)
            workflow = PortfolioCurrentBookingWorkflow(uow.connection)
            workflow.evaluate_and_record(
                booking_id="booking-1",
                authorization_id="auth-1",
                construction_result_id="construction-result-1",
                portfolio_state=portfolio_state(global_held="749.65", coin_held="249.65", global_tranches=3, coin_tranches=1),
                policy=policy(),
                authorized_at=NOW,
            )
            retained, inserted = workflow.evaluate_and_record(
                booking_id="different-booking",
                authorization_id="auth-1",
                construction_result_id="construction-result-1",
                portfolio_state=portfolio_state(global_held="999", coin_held="499"),
                policy=policy(daily_loss_blocked=True),
                authorized_at=NOW,
            )
            assert inserted is False
            assert retained.status == "AUTHORIZED"

        with pytest.raises(RuntimeError):
            with PostgresUnitOfWork(factory) as uow:
                _seed_constructed_position(uow.connection, suffix="2")
                workflow = PortfolioCurrentBookingWorkflow(uow.connection)

                def fail_auth(*args, **kwargs):
                    raise RuntimeError("auth cutpoint")

                monkeypatch.setattr(workflow._authorizations, "authorize", fail_auth)
                workflow.evaluate_and_record(
                    booking_id="booking-2",
                    authorization_id="auth-2",
                    construction_result_id="construction-result-2",
                    portfolio_state=portfolio_state(global_held="0", coin_held="0"),
                    policy=policy(global_position_cap="1000", coin_allocation_cap="500"),
                    authorized_at=NOW,
                )

        with PostgresUnitOfWork(factory) as uow:
            assert PortfolioCurrentBookingWorkflow(uow.connection).get_by_construction_result_id(
                construction_result_id="construction-result-2"
            ) is None
            assert SubmitAuthorizationStore(uow.connection).get_by_authorization_id(authorization_id="auth-2") is None
            assert DurableMessageStore(uow.connection).get_outbox(message_id="auth-2") is None
    finally:
        _drop_schema(settings)


def test_b8c_store_rolls_back_authorization_if_cooldown_pin_fails_and_restart_fails_closed():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with pytest.raises(RuntimeError):
            with PostgresUnitOfWork(factory) as uow:
                _seed_constructed_position(uow.connection)
                workflow = PortfolioCurrentBookingWorkflow(uow.connection)

                def fail_cooldown(*args, **kwargs):
                    raise RuntimeError("cooldown cutpoint")

                monkeypatch = pytest.MonkeyPatch()
                monkeypatch.setattr(workflow._cooldowns, "create_pin", fail_cooldown)
                try:
                    workflow.evaluate_and_record(
                        booking_id="booking-1",
                        authorization_id="auth-1",
                        construction_result_id="construction-result-1",
                        portfolio_state=portfolio_state(global_held="749.65", coin_held="249.65", global_tranches=3, coin_tranches=1),
                        policy=policy(),
                        authorized_at=NOW,
                    )
                finally:
                    monkeypatch.undo()

        with PostgresUnitOfWork(factory) as uow:
            assert PortfolioCurrentBookingWorkflow(uow.connection).get_by_construction_result_id(
                construction_result_id="construction-result-1"
            ) is None
            assert SubmitAuthorizationStore(uow.connection).get_by_authorization_id(authorization_id="auth-1") is None
            assert DurableMessageStore(uow.connection).get_outbox(message_id="auth-1") is None

        with PostgresUnitOfWork(factory) as uow:
            _seed_constructed_position(uow.connection)
            PortfolioCurrentBookingWorkflow(uow.connection).evaluate_and_record(
                booking_id="booking-1",
                authorization_id="auth-1",
                construction_result_id="construction-result-1",
                portfolio_state=portfolio_state(global_held="749.65", coin_held="249.65", global_tranches=3, coin_tranches=1),
                policy=policy(),
                authorized_at=NOW,
            )
            with uow.connection.cursor() as cursor:
                cursor.execute("DELETE FROM triggertrade_submit_authorizations WHERE authorization_id = %s", ("auth-1",))

        with PostgresUnitOfWork(factory) as restarted:
            with pytest.raises(PostgresPersistenceError, match="without submit authorization"):
                PortfolioCurrentBookingWorkflow(restarted.connection).get_by_construction_result_id(
                    construction_result_id="construction-result-1"
                )
    finally:
        _drop_schema(settings)


def policy(
    *,
    global_position_cap: str = "1000",
    coin_allocation_cap: str = "500",
    max_open_positions: int = 4,
    max_positions_per_coin: int = 2,
    daily_loss_blocked: bool = False,
    cooldown_status: str = "PASS",
    incident_frontier_clear: bool = True,
) -> PortfolioCurrentBookingPolicy:
    return PortfolioCurrentBookingPolicy(
        global_position_cap=global_position_cap,
        coin_allocation_cap=coin_allocation_cap,
        max_open_positions=max_open_positions,
        max_positions_per_coin=max_positions_per_coin,
        portfolio_config_id="portfolio-config-1",
        portfolio_config_version="v1.2.15",
        portfolio_config_digest="c" * 64,
        pinned_cooldown_duration_seconds=3600,
        daily_loss_blocked=daily_loss_blocked,
        cooldown_status=cooldown_status,
        incident_frontier_clear=incident_frontier_clear,
    )


def _grant() -> dict[str, object]:
    return command().capital_grant


def _constructed_result() -> dict[str, object]:
    return evaluate_position_construction(command()).construction_result.to_payload()


def _seed_constructed_position(connection, *, suffix: str = "1") -> None:
    grant = command().capital_grant
    if suffix != "1":
        grant = _copy(grant)
        grant["capital_and_limits"]["capital_grant_id"] = f"grant-{suffix}"
        grant["capital_and_limits"]["position_decision_id"] = f"position-decision-{suffix}"
        grant["capital_and_limits"]["decision_cycle_id"] = f"decision-cycle-{suffix}"
        grant["capital_and_limits"]["set_result_id"] = f"set-result-{suffix}"
        decision = _copy(approved_decision())
        decision["position_decision"]["position_decision_id"] = f"position-decision-{suffix}"
        decision["position_decision"]["decision_cycle_id"] = f"decision-cycle-{suffix}"
        decision["position_decision"]["set_result_id"] = f"set-result-{suffix}"
    else:
        decision = approved_decision()
    CapitalGrantStore(connection).issue(approved_decision=decision, capital_grant=grant)
    construction_command = command(capital_grant=grant)
    if suffix != "1":
        construction_command = type(construction_command)(
            event_id=f"construction-event-{suffix}",
            occurred_at=construction_command.occurred_at,
            construction_result_id=f"construction-result-{suffix}",
            position_plan_id=f"position-plan-{suffix}",
            tranche_id=f"tranche-{suffix}",
            order_spec_id=f"order-spec-{suffix}",
            capital_grant=grant,
            position_opportunity_state=_copy(construction_command.position_opportunity_state),
        )
        state = construction_command.position_opportunity_state["position_opportunity_state"]
        state["decision"]["position_decision_id"] = f"position-decision-{suffix}"
        state["decision"]["decision_cycle_id"] = f"decision-cycle-{suffix}"
        state["decision"]["set_result_id"] = f"set-result-{suffix}"
        state["evaluation"]["position_decision_id"] = f"position-decision-{suffix}"
        state["evaluation"]["decision_cycle_id"] = f"decision-cycle-{suffix}"
        state["evaluation"]["set_result_id"] = f"set-result-{suffix}"
    PositionConstructionWorkflow(connection).evaluate_and_record(construction_command)


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b8c_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def _outbox_count(connection, *, message_id: str) -> int:
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM triggertrade_outbox_messages WHERE message_id = %s", (message_id,))
        return int(cursor.fetchone()[0])


def _copy(payload):
    import copy

    return copy.deepcopy(payload)
