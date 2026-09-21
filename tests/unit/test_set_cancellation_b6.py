from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.contracts import parse_contract
from triggertrade.persistence import (
    DurableMessageStore,
    OwnerStateStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.set_engine import (
    F013Action,
    F013EvaluationRequest,
    F013OrderPlacedBinding,
    F013PendingEntryMonitor,
    F013PendingValidity,
    F013PredicateObservation,
    F013PredicateStatus,
    F013TerminalBinding,
    F013UnavailableReason,
)


pytest.importorskip("psycopg")

NOW = "2026-09-21T00:00:00Z"
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def test_f013_true_frozen_predicate_persists_invalidation_signal_and_outbox_replay_is_inert():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(setup.connection)

        request = _request(
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.AVAILABLE, "101", DIGEST_A, NOW),
            )
        )
        with PostgresUnitOfWork(factory) as uow:
            result = F013PendingEntryMonitor(uow.connection).evaluate(request)
            replay = F013PendingEntryMonitor(uow.connection).evaluate(request)

        with PostgresUnitOfWork(factory) as restarted:
            outbox = DurableMessageStore(restarted.connection).get_outbox(message_id=result.signal_id or "")

        assert result.pending_validity is F013PendingValidity.INVALID
        assert result.action is F013Action.EMIT_ORDER_CANCEL_SIGNAL
        assert result.state_inserted is True
        assert result.outbox_inserted is True
        assert replay.state_inserted is False
        assert replay.outbox_inserted is False
        assert replay.signal_id == result.signal_id
        assert result.signal_payload is not None
        parsed = parse_contract("ORDER_CANCEL_SIGNAL", result.signal_payload)
        root = parsed.to_payload()["order_cancel_signal"]
        assert root["cause"] == "INVALIDATION"
        assert root["condition_record_id"] == "condition-record-1"
        assert root["condition_id"] == "price-above-entry"
        assert root["evidence_digest"] == DIGEST_A
        assert root["invalidated_at"] == NOW
        assert outbox is not None
        assert outbox.producer == "Set"
        assert outbox.consumer == "Order Lifecycle"
        assert outbox.message_type == "ORDER_CANCEL_SIGNAL"
    finally:
        _drop_schema(settings)


def test_f013_terminal_entry_event_takes_precedence_over_true_predicate_and_publishes_no_signal():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(setup.connection)

        request = _request(
            terminal=F013TerminalBinding.from_payload(_terminal_payload(lifecycle_revision=3)),
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.AVAILABLE, "101", DIGEST_A, NOW),
            ),
        )
        with PostgresUnitOfWork(factory) as uow:
            result = F013PendingEntryMonitor(uow.connection).evaluate(request)

        with PostgresUnitOfWork(factory) as restarted:
            assert _outbox_count(restarted.connection) == 0

        assert result.pending_validity is F013PendingValidity.STOPPED
        assert result.action is F013Action.NO_MESSAGE
        assert result.signal_id is None
    finally:
        _drop_schema(settings)


def test_f013_persisted_terminal_tombstone_prevents_later_resurrection_without_terminal_payload():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(setup.connection)

        terminal_first = _request(terminal=F013TerminalBinding.from_payload(_terminal_payload(lifecycle_revision=3)))
        later_true = _request(
            source_event_id="market-after-terminal",
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.AVAILABLE, "101", DIGEST_A, NOW),
            ),
        )
        with PostgresUnitOfWork(factory) as uow:
            terminal_result = F013PendingEntryMonitor(uow.connection).evaluate(terminal_first)
            resurrected = F013PendingEntryMonitor(uow.connection).evaluate(later_true)

        with PostgresUnitOfWork(factory) as restarted:
            assert _outbox_count(restarted.connection) == 0

        assert terminal_result.pending_validity is F013PendingValidity.STOPPED
        assert resurrected.pending_validity is F013PendingValidity.STOPPED
        assert resurrected.state_inserted is False
        assert resurrected.signal_id is None
    finally:
        _drop_schema(settings)


def test_f013_stale_terminal_revision_does_not_suppress_newer_active_placement():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(setup.connection)

        request = _request(
            placement=F013OrderPlacedBinding.from_payload(_placement_payload(lifecycle_revision=5)),
            terminal=F013TerminalBinding.from_payload(_terminal_payload(lifecycle_revision=4)),
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.AVAILABLE, "101", DIGEST_A, NOW),
            ),
        )
        with PostgresUnitOfWork(factory) as uow:
            result = F013PendingEntryMonitor(uow.connection).evaluate(request)

        assert result.pending_validity is F013PendingValidity.INVALID
        assert result.signal_payload is not None
        assert result.signal_payload["order_cancel_signal"]["cause"] == "INVALIDATION"
    finally:
        _drop_schema(settings)


def test_f013_persisted_stale_terminal_does_not_suppress_later_newer_placement_without_terminal_payload():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(setup.connection)

        stale_terminal = _request(
            placement=F013OrderPlacedBinding.from_payload(_placement_payload(lifecycle_revision=4)),
            terminal=F013TerminalBinding.from_payload(_terminal_payload(lifecycle_revision=4)),
        )
        newer_placement_true = _request(
            placement=F013OrderPlacedBinding.from_payload(_placement_payload(lifecycle_revision=5)),
            terminal=None,
            source_event_id="market-after-stale-terminal",
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.AVAILABLE, "101", DIGEST_A, NOW),
            ),
        )
        with PostgresUnitOfWork(factory) as uow:
            terminal_result = F013PendingEntryMonitor(uow.connection).evaluate(stale_terminal)
            newer_result = F013PendingEntryMonitor(uow.connection).evaluate(newer_placement_true)

        assert terminal_result.pending_validity is F013PendingValidity.STOPPED
        assert newer_result.pending_validity is F013PendingValidity.INVALID
        assert newer_result.signal_payload is not None
        assert newer_result.signal_payload["order_cancel_signal"]["cause"] == "INVALIDATION"
    finally:
        _drop_schema(settings)


def test_f013_unavailable_requirement_is_sticky_and_recovery_does_not_withdraw_signal():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(setup.connection)

        missing_evidence = _request(
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.UNAVAILABLE, None, None, None),
            )
        )
        recovered_false = _request(
            source_event_id="market-recovery-1",
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.AVAILABLE, "99", DIGEST_B, NOW),
            ),
        )
        with PostgresUnitOfWork(factory) as uow:
            first = F013PendingEntryMonitor(uow.connection).evaluate(missing_evidence)
            replay_after_recovery = F013PendingEntryMonitor(uow.connection).evaluate(recovered_false)

        assert first.pending_validity is F013PendingValidity.UNAVAILABLE
        assert first.reason_code == F013UnavailableReason.REQUIRED_EVIDENCE_UNAVAILABLE.value
        assert first.signal_payload is not None
        root = first.signal_payload["order_cancel_signal"]
        assert root["cause"] == "MONITORING_UNAVAILABLE"
        assert root["signal_id"] == root["unavailable_requirement_id"]
        assert replay_after_recovery.pending_validity is F013PendingValidity.UNAVAILABLE
        assert replay_after_recovery.signal_id == first.signal_id
        assert replay_after_recovery.signal_payload == first.signal_payload
        assert replay_after_recovery.state_inserted is False
    finally:
        _drop_schema(settings)


def test_f013_conflicting_placement_lineage_is_retained_without_outbound_signal():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(setup.connection)

        mismatched = _request(
            placement=F013OrderPlacedBinding.from_payload(
                {
                    "order_placed": {
                        **_placement_payload()["order_placed"],
                        "set_result_id": "other-set-result",
                    }
                }
            ),
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.UNAVAILABLE, None, None, None),
            ),
        )
        with PostgresUnitOfWork(factory) as uow:
            result = F013PendingEntryMonitor(uow.connection).evaluate(mismatched)

        with PostgresUnitOfWork(factory) as restarted:
            assert _outbox_count(restarted.connection) == 0

        assert result.pending_validity is F013PendingValidity.DEFERRED_UNBOUND
        assert result.action is F013Action.RETAIN_UNBOUND_TRANSITION
        assert result.signal_payload is None
    finally:
        _drop_schema(settings)


def test_f013_unbound_unavailable_transition_is_retained_without_guessed_outbound_signal():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(setup.connection)

        request = _request(
            placement=None,
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.UNAVAILABLE, None, None, None),
            ),
        )
        with PostgresUnitOfWork(factory) as uow:
            result = F013PendingEntryMonitor(uow.connection).evaluate(request)

        with PostgresUnitOfWork(factory) as restarted:
            assert _outbox_count(restarted.connection) == 0

        assert result.pending_validity is F013PendingValidity.DEFERRED_UNBOUND
        assert result.action is F013Action.RETAIN_UNBOUND_TRANSITION
        assert result.signal_payload is None
    finally:
        _drop_schema(settings)


def test_f013_invalidation_identity_is_stable_for_later_true_evidence_on_same_entry():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(setup.connection)

        first_true = _request(
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.AVAILABLE, "101", DIGEST_A, NOW),
            )
        )
        later_true = _request(
            source_event_id="market-later-true",
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.AVAILABLE, "102", DIGEST_B, NOW),
            ),
        )
        with PostgresUnitOfWork(factory) as uow:
            first = F013PendingEntryMonitor(uow.connection).evaluate(first_true)
        with pytest.raises(Exception, match="different content"):
            with PostgresUnitOfWork(factory) as uow:
                F013PendingEntryMonitor(uow.connection).evaluate(later_true)
        with PostgresUnitOfWork(factory) as restarted:
            assert _outbox_count(restarted.connection) == 1

        assert first.signal_id is not None
    finally:
        _drop_schema(settings)


def test_f013_missing_frozen_record_fails_closed_without_true_fields():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        request = _request(condition_record_id="missing-record")
        with PostgresUnitOfWork(factory) as uow:
            result = F013PendingEntryMonitor(uow.connection).evaluate(request)

        assert result.pending_validity is F013PendingValidity.UNAVAILABLE
        assert result.reason_code == F013UnavailableReason.FROZEN_RECORD_INVALID_OR_UNRESOLVED.value
        assert result.signal_payload is not None
        root = result.signal_payload["order_cancel_signal"]
        assert root["cause"] == "MONITORING_UNAVAILABLE"
        assert "condition_record_id" not in root
        assert "condition_id" not in root
        assert "evidence_digest" not in root
        assert "invalidated_at" not in root
    finally:
        _drop_schema(settings)


def test_f013_invalid_observation_status_fails_closed_as_invalid_condition():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(setup.connection)

        request = _request(
            observations=(
                F013PredicateObservation("price-above-entry", "BROKEN", "101", DIGEST_A, NOW),  # type: ignore[arg-type]
            )
        )
        with PostgresUnitOfWork(factory) as uow:
            result = F013PendingEntryMonitor(uow.connection).evaluate(request)

        assert result.pending_validity is F013PendingValidity.UNAVAILABLE
        assert result.signal_payload is not None
        assert result.signal_payload["order_cancel_signal"]["cause"] == "MONITORING_UNAVAILABLE"
        assert result.reason_code == F013UnavailableReason.INVALID_CONDITION.value
    finally:
        _drop_schema(settings)


def test_f013_invalid_condition_reason_precedes_required_evidence_unavailable():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(
                setup.connection,
                conditions=(
                    {"condition_id": "malformed", "operator": "GT", "threshold": "100", "required": True},
                    {"condition_id": "missing", "operator": "LT", "threshold": "90", "required": True},
                ),
            )

        request = _request(
            observations=(
                F013PredicateObservation("malformed", F013PredicateStatus.AVAILABLE, "not-a-decimal", DIGEST_A, NOW),
                F013PredicateObservation("missing", F013PredicateStatus.UNAVAILABLE, None, None, None),
            )
        )
        with PostgresUnitOfWork(factory) as uow:
            result = F013PendingEntryMonitor(uow.connection).evaluate(request)

        assert result.reason_code == F013UnavailableReason.INVALID_CONDITION.value
        assert result.signal_payload is not None
        assert result.signal_payload["order_cancel_signal"]["unavailable_reason_code"] == "INVALID_CONDITION"
    finally:
        _drop_schema(settings)


def test_f013_exact_decimal_boundary_uses_no_epsilon():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(
                setup.connection,
                conditions=(
                    {"condition_id": "strict-greater", "operator": "GT", "threshold": "100.000000000000000001", "required": True},
                ),
            )

        exactly_equal = _request(
            observations=(
                F013PredicateObservation(
                    "strict-greater",
                    F013PredicateStatus.AVAILABLE,
                    "100.000000000000000001",
                    DIGEST_A,
                    NOW,
                ),
            )
        )
        just_greater = _request(
            source_event_id="market-cross-1",
            observations=(
                F013PredicateObservation(
                    "strict-greater",
                    F013PredicateStatus.AVAILABLE,
                    "100.000000000000000002",
                    DIGEST_B,
                    NOW,
                ),
            ),
        )
        with PostgresUnitOfWork(factory) as uow:
            equal_result = F013PendingEntryMonitor(uow.connection).evaluate(exactly_equal)
            true_result = F013PendingEntryMonitor(uow.connection).evaluate(just_greater)

        assert equal_result.pending_validity is F013PendingValidity.VALID
        assert equal_result.signal_id is None
        assert true_result.pending_validity is F013PendingValidity.INVALID
        assert true_result.signal_payload["order_cancel_signal"]["evidence_digest"] == DIGEST_B  # type: ignore[index]
    finally:
        _drop_schema(settings)


def test_f013_repeated_valid_monitoring_ticks_do_not_conflict_or_emit_signal():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            _put_frozen_condition(setup.connection)

        first_false = _request(
            source_event_id="market-valid-1",
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.AVAILABLE, "99", DIGEST_A, NOW),
            ),
        )
        second_false = _request(
            source_event_id="market-valid-2",
            observations=(
                F013PredicateObservation("price-above-entry", F013PredicateStatus.AVAILABLE, "98", DIGEST_B, NOW),
            ),
        )
        with PostgresUnitOfWork(factory) as uow:
            first = F013PendingEntryMonitor(uow.connection).evaluate(first_false)
            second = F013PendingEntryMonitor(uow.connection).evaluate(second_false)

        with PostgresUnitOfWork(factory) as restarted:
            assert _outbox_count(restarted.connection) == 0

        assert first.pending_validity is F013PendingValidity.VALID
        assert second.pending_validity is F013PendingValidity.VALID
        assert first.signal_id is None
        assert second.signal_id is None
        assert first.state_inserted is True
        assert second.state_inserted is True
    finally:
        _drop_schema(settings)


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b6_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def _put_frozen_condition(connection, *, conditions: tuple[dict[str, object], ...] | None = None) -> None:
    OwnerStateStore(connection).put_if_absent(
        owner="SET",
        state_type="SET_FROZEN_CONDITION",
        state_id="condition-record-1",
        payload={
            "set_frozen_condition": {
                "schema_version": "SET_FROZEN_CONDITION_B5B_V1",
                "condition_record_id": "condition-record-1",
                "frozen_condition_record_id": "condition-record-1",
                "condition_id": "condition-1",
                "decision_cycle_id": "decision-cycle-1",
                "set_result_id": "set-result-1",
                "direction": "LONG",
                "symbol": "BTCUSDT",
                "configuration_binding_digest": DIGEST_A,
                "source_condition": {
                    "conditions": list(
                        conditions
                        or (
                            {
                                "condition_id": "price-above-entry",
                                "operator": "GT",
                                "threshold": "100",
                                "required": True,
                            },
                        )
                    )
                },
            }
        },
    )


_DEFAULT_PLACEMENT = object()


def _request(
    *,
    placement: F013OrderPlacedBinding | None | object = _DEFAULT_PLACEMENT,
    terminal: F013TerminalBinding | None = None,
    condition_record_id: str = "condition-record-1",
    observations: tuple[F013PredicateObservation, ...] = (),
    source_event_id: str = "market-evaluation-1",
) -> F013EvaluationRequest:
    resolved_placement = (
        F013OrderPlacedBinding.from_payload(_placement_payload()) if placement is _DEFAULT_PLACEMENT else placement
    )
    return F013EvaluationRequest(
        decision_cycle_id="decision-cycle-1",
        set_result_id="set-result-1",
        tranche_id="tranche-1",
        symbol="BTCUSDT",
        condition_record_id=condition_record_id,
        evaluated_at=NOW,
        source_event_id=source_event_id,
        placement=resolved_placement,
        terminal=terminal,
        observations=observations,
    )


def _placement_payload(*, lifecycle_revision: int = 1) -> dict[str, object]:
    return {
        "order_placed": {
            "contract_version": 3,
            "event_id": "order-placed-1",
            "lifecycle_revision": lifecycle_revision,
            "decision_cycle_id": "decision-cycle-1",
            "set_result_id": "set-result-1",
            "position_plan_id": "position-plan-1",
            "tranche_id": "tranche-1",
            "symbol": "BTCUSDT",
            "client_order_link_id": "client-order-1",
            "exchange_order_id": "exchange-1",
            "order_placed_at": NOW,
        }
    }


def _terminal_payload(*, lifecycle_revision: int) -> dict[str, object]:
    return {
        "entry_lifecycle_event": {
            "contract_version": 3,
            "event_id": "entry-terminal-1",
            "lifecycle_revision": lifecycle_revision,
            "decision_cycle_id": "decision-cycle-1",
            "set_result_id": "set-result-1",
            "tranche_id": "tranche-1",
            "symbol": "BTCUSDT",
            "event_type": "FULL_FILL",
            "occurred_at": NOW,
        }
    }


def _outbox_count(connection) -> int:
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM triggertrade_outbox_messages WHERE producer = 'Set'")
        row = cursor.fetchone()
    return int(row[0])
