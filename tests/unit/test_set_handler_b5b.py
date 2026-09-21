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
from triggertrade.persistence.durable_messages import DurableMessageConflict
from triggertrade.set_engine import (
    ClassifierInputs,
    DeclaredConflictRule,
    Direction,
    DirectionResolutionScope,
    GenericFixedDirectionBinding,
    GenericBranchEvidence,
    HandoffContext,
    HandoffFacts,
    HandoffReferenceLevel,
    SetDurableHandler,
    SetHandlerError,
    SetMatchStatus,
    SetResolutionRequest,
    SetResultConflict,
    SwingSequenceState,
    TriggerResult,
    generic_fixed_direction_binding_digest,
)
from triggertrade.set_scope import SetFormationEpoch
from tests.unit.test_set_scope import configuration_binding


pytest.importorskip("psycopg")

NOW = "2026-09-21T00:00:00Z"
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def test_set_handler_governed_f005_match_persists_result_frozen_record_and_handoff_outbox():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        request = _request(
            direction_scope=DirectionResolutionScope.F005_GOVERNED,
            classifier_inputs=_long_classifier(),
        )

        with PostgresUnitOfWork(factory) as uow:
            result = SetDurableHandler(uow.connection).resolve(request)
            replay = SetDurableHandler(uow.connection).resolve(request)
            outbox = DurableMessageStore(uow.connection).get_outbox(message_id=result.decision_cycle_id or "")
            frozen = OwnerStateStore(uow.connection).get(
                owner="SET",
                state_type="SET_FROZEN_CONDITION",
                state_id=result.result_payload["set_result"]["decision_cycle_id"].replace("decision-cycle-", "condition-record-"),
            )

        assert result.status is SetMatchStatus.MATCHED
        assert result.direction is Direction.LONG
        assert result.result_inserted is True
        assert result.outbox_inserted is True
        assert replay.result_inserted is False
        assert replay.outbox_inserted is False
        assert replay.set_result_id == result.set_result_id
        assert result.handoff_payload is not None
        assert parse_contract("MARKET_HANDOFF", result.handoff_payload, definition="MARKET_HANDOFF")
        assert result.handoff_payload["market_handoff"]["snapshot"]["direction"] == "LONG"
        assert result.handoff_payload["market_handoff"]["decision_cycle_id"] == result.decision_cycle_id
        assert result.handoff_payload["market_handoff"]["set_result_id"] == result.set_result_id
        assert result.result_payload["set_result"]["classifier_evidence"]["f005_classifier"]["direction"] == "LONG"
        assert outbox is not None
        assert outbox.producer == "Set"
        assert outbox.consumer == "Position"
        assert outbox.message_type == "MARKET_HANDOFF"
        assert frozen is not None
    finally:
        _drop_schema(settings)


def test_set_handler_rejects_changed_handoff_content_under_same_cycle_identity():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        original = _request(
            direction_scope=DirectionResolutionScope.F005_GOVERNED,
            classifier_inputs=_long_classifier(),
        )
        changed = _request(
            direction_scope=DirectionResolutionScope.F005_GOVERNED,
            classifier_inputs=_long_classifier(),
            handoff_facts=_handoff_facts(tick_size="0.2"),
        )
        with PostgresUnitOfWork(factory) as uow:
            first = SetDurableHandler(uow.connection).resolve(original)
        with pytest.raises(DurableMessageConflict):
            with PostgresUnitOfWork(factory) as uow:
                SetDurableHandler(uow.connection).resolve(changed)
        with PostgresUnitOfWork(factory) as restarted:
            outbox = DurableMessageStore(restarted.connection).get_outbox(message_id=first.decision_cycle_id or "")
        assert outbox is not None
        assert outbox.payload["market_handoff"]["instrument"]["tick_size"] == "0.1"
    finally:
        _drop_schema(settings)


def test_set_handler_rejects_changed_same_epoch_source_evidence_without_reminting_result():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        original = _request(
            direction_scope=DirectionResolutionScope.F005_GOVERNED,
            classifier_inputs=_long_classifier(),
        )
        changed_source = SetResolutionRequest(
            formation_epoch=original.formation_epoch,
            direction_scope=original.direction_scope,
            formation_result=original.formation_result,
            evaluation_event_ids=original.evaluation_event_ids,
            source_evidence_digest=DIGEST_B,
            handoff_facts=original.handoff_facts,
            classifier_inputs=original.classifier_inputs,
            fixed_direction_binding=original.fixed_direction_binding,
            generic_branches=original.generic_branches,
            declared_conflict_rule=original.declared_conflict_rule,
            frozen_condition=original.frozen_condition,
        )
        with PostgresUnitOfWork(factory) as uow:
            first = SetDurableHandler(uow.connection).resolve(original)
        with pytest.raises(SetResultConflict):
            with PostgresUnitOfWork(factory) as uow:
                SetDurableHandler(uow.connection).resolve(changed_source)
        with PostgresUnitOfWork(factory) as restarted:
            original_record = OwnerStateStore(restarted.connection).get(
                owner="SET",
                state_type="SET_RESULT",
                state_id=first.set_result_id,
            )
            new_record = OwnerStateStore(restarted.connection).get(
                owner="SET",
                state_type="SET_RESULT",
                state_id=changed_source.source_evidence_digest,
            )
        assert original_record is not None
        assert original_record.payload["set_result"]["source_evidence_digest"] == DIGEST_A
        assert new_record is None
    finally:
        _drop_schema(settings)


def test_set_handler_does_not_publish_when_formation_fails_but_retains_classifier_evidence():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        request = _request(
            direction_scope=DirectionResolutionScope.F005_GOVERNED,
            classifier_inputs=_long_classifier(),
            formation_result=TriggerResult.FALSE,
        )
        with PostgresUnitOfWork(factory) as uow:
            result = SetDurableHandler(uow.connection).resolve(request)
        assert result.status is SetMatchStatus.UNMATCHED
        assert result.reason_code == "FORMATION_FALSE"
        assert result.decision_cycle_id is None
        assert result.handoff_payload is None
        assert result.outbox_inserted is False
        assert result.result_payload["set_result"]["classifier_evidence"]["f005_classifier"]["direction"] == "LONG"
    finally:
        _drop_schema(settings)


def test_set_handler_preserves_generic_fixed_direction_without_f005_and_rejects_spurious_classifier():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        request = _request(
            direction_scope=DirectionResolutionScope.GENERIC_FIXED,
            fixed_direction_binding=_fixed_binding(Direction.SHORT),
        )
        with PostgresUnitOfWork(factory) as uow:
            result = SetDurableHandler(uow.connection).resolve(request)
        assert result.status is SetMatchStatus.MATCHED
        assert result.direction is Direction.SHORT
        assert result.handoff_payload["market_handoff"]["snapshot"]["direction"] == "SHORT"  # type: ignore[index]

        with pytest.raises(SetHandlerError, match="must not invoke F-005"):
            _request(
                direction_scope=DirectionResolutionScope.GENERIC_FIXED,
                fixed_direction_binding=_fixed_binding(Direction.LONG),
                classifier_inputs=_long_classifier(),
            )
            with PostgresUnitOfWork(factory) as uow:
                SetDurableHandler(uow.connection).resolve(
                    _request(
                        direction_scope=DirectionResolutionScope.GENERIC_FIXED,
                        fixed_direction_binding=_fixed_binding(Direction.LONG),
                        classifier_inputs=_long_classifier(),
                    )
                )
    finally:
        _drop_schema(settings)


def test_set_handler_rejects_unbound_or_opposite_generic_fixed_direction_replay():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        missing_binding = _request(
            direction_scope=DirectionResolutionScope.GENERIC_FIXED,
            fixed_direction_binding=GenericFixedDirectionBinding(Direction.LONG, DIGEST_A),
        )
        long_request = _request(
            direction_scope=DirectionResolutionScope.GENERIC_FIXED,
            fixed_direction_binding=_fixed_binding(Direction.LONG),
        )
        short_replay = _request(
            direction_scope=DirectionResolutionScope.GENERIC_FIXED,
            fixed_direction_binding=_fixed_binding(Direction.SHORT),
        )

        with pytest.raises(SetHandlerError, match="immutable configuration binding"):
            with PostgresUnitOfWork(factory) as uow:
                SetDurableHandler(uow.connection).resolve(missing_binding)
        with PostgresUnitOfWork(factory) as uow:
            first = SetDurableHandler(uow.connection).resolve(long_request)
        with pytest.raises(SetResultConflict):
            with PostgresUnitOfWork(factory) as uow:
                SetDurableHandler(uow.connection).resolve(short_replay)
        with PostgresUnitOfWork(factory) as restarted:
            original = OwnerStateStore(restarted.connection).get(owner="SET", state_type="SET_RESULT", state_id=first.set_result_id)
        assert original is not None
        assert original.payload["set_result"]["direction"] == "LONG"
    finally:
        _drop_schema(settings)


def test_set_handler_generic_branch_conflicts_require_declared_rule_and_replay_rule_result():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        branches = (
            GenericBranchEvidence("branch-long", Direction.LONG, NOW, DIGEST_A),
            GenericBranchEvidence("branch-short", Direction.SHORT, NOW, DIGEST_B),
        )
        unresolved = _request(
            direction_scope=DirectionResolutionScope.GENERIC_MATCHED_BRANCH,
            generic_branches=branches,
        )
        resolved = _request(
            direction_scope=DirectionResolutionScope.GENERIC_MATCHED_BRANCH,
            generic_branches=branches,
            declared_conflict_rule=DeclaredConflictRule("rule-explicit-short", "branch-short", DIGEST_C),
            formation_epoch=_epoch(formation_epoch=11, open_event_id="coins-open-11"),
        )
        with PostgresUnitOfWork(factory) as uow:
            failed = SetDurableHandler(uow.connection).resolve(unresolved)
            matched = SetDurableHandler(uow.connection).resolve(resolved)
        assert failed.status is SetMatchStatus.UNMATCHED
        assert failed.reason_code == "GENERIC_CONFLICT_UNRESOLVED"
        assert failed.handoff_payload is None
        assert matched.status is SetMatchStatus.MATCHED
        assert matched.direction is Direction.SHORT
        assert matched.result_payload["set_result"]["selected_branch_id"] == "branch-short"
    finally:
        _drop_schema(settings)


def test_set_handler_rejects_changed_branch_or_conflict_rule_content_on_replay():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        accepted = _request(
            direction_scope=DirectionResolutionScope.GENERIC_MATCHED_BRANCH,
            generic_branches=(
                GenericBranchEvidence("branch-long", Direction.LONG, NOW, DIGEST_A),
                GenericBranchEvidence("branch-short", Direction.SHORT, NOW, DIGEST_B),
            ),
            declared_conflict_rule=DeclaredConflictRule("rule-explicit-short", "branch-short", DIGEST_C),
        )
        changed_branch = _request(
            direction_scope=DirectionResolutionScope.GENERIC_MATCHED_BRANCH,
            generic_branches=(
                GenericBranchEvidence("branch-long", Direction.LONG, NOW, DIGEST_B),
                GenericBranchEvidence("branch-short", Direction.SHORT, NOW, DIGEST_B),
            ),
            declared_conflict_rule=DeclaredConflictRule("rule-explicit-short", "branch-short", DIGEST_C),
        )
        changed_rule = _request(
            direction_scope=DirectionResolutionScope.GENERIC_MATCHED_BRANCH,
            generic_branches=accepted.generic_branches,
            declared_conflict_rule=DeclaredConflictRule("rule-explicit-short", "branch-short", DIGEST_A),
        )
        with PostgresUnitOfWork(factory) as uow:
            first = SetDurableHandler(uow.connection).resolve(accepted)
        with pytest.raises(SetResultConflict):
            with PostgresUnitOfWork(factory) as uow:
                SetDurableHandler(uow.connection).resolve(changed_branch)
        with pytest.raises(SetResultConflict):
            with PostgresUnitOfWork(factory) as uow:
                SetDurableHandler(uow.connection).resolve(changed_rule)
        with PostgresUnitOfWork(factory) as restarted:
            original = OwnerStateStore(restarted.connection).get(owner="SET", state_type="SET_RESULT", state_id=first.set_result_id)
        assert original is not None
        assert original.payload["set_result"]["generic_branches"][0]["evidence_digest"] == DIGEST_A
        assert original.payload["set_result"]["declared_conflict_rule"]["rule_digest"] == DIGEST_C
    finally:
        _drop_schema(settings)


def test_set_handler_generic_branch_replay_is_order_invariant_and_uses_stable_branch_identity():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        ordered = _request(
            direction_scope=DirectionResolutionScope.GENERIC_MATCHED_BRANCH,
            generic_branches=(
                GenericBranchEvidence("branch-a", Direction.LONG, NOW, DIGEST_A),
                GenericBranchEvidence("branch-b", Direction.LONG, NOW, DIGEST_B),
            ),
        )
        reversed_order = _request(
            direction_scope=DirectionResolutionScope.GENERIC_MATCHED_BRANCH,
            generic_branches=(
                GenericBranchEvidence("branch-b", Direction.LONG, NOW, DIGEST_B),
                GenericBranchEvidence("branch-a", Direction.LONG, NOW, DIGEST_A),
            ),
        )
        with PostgresUnitOfWork(factory) as uow:
            first = SetDurableHandler(uow.connection).resolve(ordered)
            replay = SetDurableHandler(uow.connection).resolve(reversed_order)
        assert first.set_result_id == replay.set_result_id
        assert replay.result_inserted is False
        assert first.result_payload == replay.result_payload
        assert first.result_payload["set_result"]["selected_branch_id"] == "branch-a"
        assert [branch["branch_id"] for branch in first.result_payload["set_result"]["generic_branches"]] == [
            "branch-a",
            "branch-b",
        ]
    finally:
        _drop_schema(settings)


def test_set_handler_rejects_empty_generic_branch_and_conflict_rule_identities():
    invalid_branch = _request(
        direction_scope=DirectionResolutionScope.GENERIC_MATCHED_BRANCH,
        generic_branches=(GenericBranchEvidence("", Direction.LONG, NOW, DIGEST_A),),
    )
    invalid_rule = _request(
        direction_scope=DirectionResolutionScope.GENERIC_MATCHED_BRANCH,
        generic_branches=(
            GenericBranchEvidence("branch-long", Direction.LONG, NOW, DIGEST_A),
            GenericBranchEvidence("branch-short", Direction.SHORT, NOW, DIGEST_B),
        ),
        declared_conflict_rule=DeclaredConflictRule("rule", "", DIGEST_C),
    )

    with pytest.raises(SetHandlerError, match="branch_id"):
        SetDurableHandler(_NoopConnection()).resolve(invalid_branch)
    with pytest.raises(SetHandlerError, match="selected_branch_id"):
        SetDurableHandler(_NoopConnection()).resolve(invalid_rule)


def test_set_handler_rejects_missing_required_reference_or_rounded_to_zero_atr_without_partial_commit():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        missing_reference = _request(
            direction_scope=DirectionResolutionScope.GENERIC_FIXED,
            fixed_direction=Direction.LONG,
            handoff_facts=_handoff_facts(entry_context=_context(level_id="missing-level")),
        )
        zero_atr = _request(
            direction_scope=DirectionResolutionScope.GENERIC_FIXED,
            fixed_direction=Direction.LONG,
            handoff_facts=_handoff_facts(atr_15m="0"),
        )
        with pytest.raises(SetHandlerError, match="required thesis reference"):
            with PostgresUnitOfWork(factory) as uow:
                SetDurableHandler(uow.connection).resolve(missing_reference)
        with pytest.raises(SetHandlerError, match="ATR"):
            with PostgresUnitOfWork(factory) as uow:
                SetDurableHandler(uow.connection).resolve(zero_atr)
        with PostgresUnitOfWork(factory) as restarted:
            owner_rows = _owner_state_count(restarted.connection)
            outbox_rows = _outbox_count(restarted.connection)
            frontier_rows = _frontier_count(restarted.connection)
        assert owner_rows == 0
        assert outbox_rows == 0
        assert frontier_rows == 0
    finally:
        _drop_schema(settings)


def test_set_handler_rejects_non_producer_bound_thesis_reference_before_wire_publication():
    dangling_reference = _request(
        direction_scope=DirectionResolutionScope.GENERIC_FIXED,
        fixed_direction_binding=_fixed_binding(Direction.LONG),
        handoff_facts=_handoff_facts(
            entry_context=HandoffContext(
                set_family="GENERIC",
                thesis_reference_policy="PREFERRED",
                thesis_reference_level_id="level-entry",
                origin_binding=None,
            )
        ),
    )
    foreign_reference = _request(
        direction_scope=DirectionResolutionScope.GENERIC_FIXED,
        fixed_direction_binding=_fixed_binding(Direction.LONG),
        handoff_facts=_handoff_facts(
            entry_context=HandoffContext(
                set_family="GENERIC",
                thesis_reference_policy="PREFERRED",
                thesis_reference_level_id="other-level",
                origin_binding={**_origin_binding("other-level"), "level_id": "other-level"},
            )
        ),
    )
    mismatched_binding = _request(
        direction_scope=DirectionResolutionScope.GENERIC_FIXED,
        fixed_direction_binding=_fixed_binding(Direction.LONG),
        handoff_facts=_handoff_facts(
            extra_level=HandoffReferenceLevel(
                level_id="level-other",
                level_type="SWING_LOW",
                price="90",
                timeframe="15m",
                formed_at=NOW,
                confirmed_at=NOW,
                available_at=NOW,
                source_metric="SWING",
                age_seconds=0,
                relative_position="BELOW_REFERENCE",
            ),
            entry_context=HandoffContext(
                set_family="GENERIC",
                thesis_reference_policy="PREFERRED",
                thesis_reference_level_id="level-entry",
                origin_binding=_origin_binding("level-other"),
            ),
        ),
    )

    with pytest.raises(SetHandlerError, match="origin binding"):
        SetDurableHandler(_NoopConnection()).resolve(dangling_reference)
    with pytest.raises(SetHandlerError, match="thesis reference"):
        SetDurableHandler(_NoopConnection()).resolve(foreign_reference)
    with pytest.raises(SetHandlerError, match="origin binding level_id"):
        SetDurableHandler(_NoopConnection()).resolve(mismatched_binding)


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b5b_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def _owner_state_count(connection) -> int:
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM triggertrade_owner_state_records WHERE owner = 'SET'")
        row = cursor.fetchone()
    return int(row[0])


def _outbox_count(connection) -> int:
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM triggertrade_outbox_messages WHERE producer = 'Set'")
        row = cursor.fetchone()
    return int(row[0])


def _frontier_count(connection) -> int:
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM triggertrade_transport_frontier_messages WHERE scope_key LIKE 'SET:%'")
        row = cursor.fetchone()
    return int(row[0])


def _request(
    *,
    direction_scope: DirectionResolutionScope,
    formation_result: TriggerResult = TriggerResult.TRUE,
    classifier_inputs: ClassifierInputs | None = None,
    fixed_direction: Direction | None = None,
    fixed_direction_binding: GenericFixedDirectionBinding | None = None,
    generic_branches: tuple[GenericBranchEvidence, ...] = (),
    declared_conflict_rule: DeclaredConflictRule | None = None,
    handoff_facts: HandoffFacts | None = None,
    formation_epoch: SetFormationEpoch | None = None,
) -> SetResolutionRequest:
    return SetResolutionRequest(
        formation_epoch=formation_epoch or _epoch(),
        direction_scope=direction_scope,
        formation_result=formation_result,
        evaluation_event_ids=("event-1", "event-2"),
        source_evidence_digest=DIGEST_A,
        handoff_facts=handoff_facts or _handoff_facts(),
        classifier_inputs=classifier_inputs,
        fixed_direction_binding=fixed_direction_binding or (_fixed_binding(fixed_direction) if fixed_direction is not None else None),
        generic_branches=generic_branches,
        declared_conflict_rule=declared_conflict_rule,
        frozen_condition={"predicate": "price_above_reference", "source_digest": DIGEST_A},
    )


def _epoch(*, formation_epoch: int = 10, open_event_id: str = "coins-open-10") -> SetFormationEpoch:
    return SetFormationEpoch(
        symbol="SOLUSDT",
        formation_epoch=formation_epoch,
        open_event_id=open_event_id,
        opened_at=NOW,
        open_payload_digest=DIGEST_A,
        configuration_binding=configuration_binding(),
    )


def _long_classifier() -> ClassifierInputs:
    return ClassifierInputs(
        structure_1h=SwingSequenceState.BULLISH,
        structure_15m=SwingSequenceState.BULLISH,
        de_15m="0.70",
        momentum_score="1",
        vnm_5m_z="0",
        relative_score="1",
        relative_return_z="0",
        aggressive_delta_pct="100",
        tod_relative_turnover="2",
        atr_pct_percentile_15m="50",
        btc_structure_1h=SwingSequenceState.BULLISH,
        btc_return_z="2",
    )


def _handoff_facts(
    *,
    tick_size: str = "0.1",
    atr_15m: str = "1",
    entry_context: HandoffContext | None = None,
    extra_level: HandoffReferenceLevel | None = None,
) -> HandoffFacts:
    context = entry_context or _context(level_id="level-entry")
    levels = [
        HandoffReferenceLevel(
            level_id="level-entry",
            level_type="SWING_HIGH",
            price="99",
            timeframe="15m",
            formed_at=NOW,
            confirmed_at=NOW,
            available_at=NOW,
            source_metric="SWING",
            age_seconds=0,
            relative_position="BELOW_REFERENCE",
        )
    ]
    if extra_level is not None:
        levels.append(extra_level)
    return HandoffFacts(
        symbol="SOLUSDT",
        created_at=NOW,
        matched_at=NOW,
        market_snapshot_at=NOW,
        market_snapshot_id="snapshot-1",
        set_match_reference_price="100",
        reference_price_observed_at=NOW,
        reference_price_source="ticker.last_price",
        tick_size=tick_size,
        metadata_revision="instrument:SOLUSDT:1",
        metadata_as_of=NOW,
        atr_15m=atr_15m,
        atr_pct_15m="1",
        reference_levels=tuple(levels),
        entry_context=context,
        sl_context=_context(level_id="level-entry"),
        tp_context=_context(level_id="level-entry"),
        core_set_id="core-set-main",
        set_family="GENERIC",
    )


def _context(*, level_id: str) -> HandoffContext:
    return HandoffContext(
        set_family="GENERIC",
        thesis_reference_policy="REQUIRED",
        thesis_reference_level_id=level_id,
        origin_binding=_origin_binding(level_id),
    )


def _origin_binding(level_id: str) -> dict[str, object]:
    return {
        "binding_id": "binding-entry",
        "role_id": "entry",
        "core_set_id": "core-set-main",
        "core_set_constituent_id": "constituent-1",
        "trigger_id": "trigger-1",
        "trigger_version": "trigger-v1",
        "trigger_occurrence_id": "occurrence-1",
        "reference_key": "entry",
        "indicator_id": None,
        "timeframe": "15m",
        "level_id": level_id,
    }


def _fixed_binding(direction: Direction) -> GenericFixedDirectionBinding:
    return GenericFixedDirectionBinding(
        fixed_direction=direction,
        binding_digest=generic_fixed_direction_binding_digest(
            configuration_binding_digest=configuration_binding().digest,
            fixed_direction=direction,
        ),
    )


class _NoopConnection:
    def cursor(self):  # pragma: no cover - these tests raise before persistence is touched
        raise AssertionError("persistence should not be touched")
