"""Durable Lifecycle submission-intent records and dispatch cutpoints."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Any

from triggertrade.canonical_json import canonical_json_text
from triggertrade.lifecycle_submission import (
    LifecycleSubmissionError,
    LifecycleSubmissionIntent,
    SUBMISSION_STATES,
    SUBMISSION_UNCERTAIN,
    SUBMITTED,
    SUBMITTING,
    build_lifecycle_submission_intent,
    lifecycle_submission_intent_digest,
)

from .lifecycle_start_gate_store import LifecycleStartGateRecord
from .postgres import PostgresPersistenceError


class LifecycleSubmissionConflict(PostgresPersistenceError):
    """Raised when a submission intent identity is replayed with different content."""


@dataclass(frozen=True)
class LifecycleSubmissionRecord:
    submission_intent_id: str
    start_gate_id: str
    order_spec_id: str
    authorization_id: str
    capital_grant_id: str
    decision_cycle_id: str
    set_result_id: str
    position_decision_id: str
    construction_result_id: str
    position_plan_id: str
    tranche_id: str
    symbol: str
    direction: str
    target_client_order_id: str
    lifecycle_state: str
    order_spec_digest: str
    submit_authorized_digest: str
    start_gate_digest: str
    payload: dict[str, Any]
    payload_digest: str
    dispatch_attempts: int
    last_dispatch_cutpoint_id: str | None
    last_dispatch_started_at: str | None
    last_uncertain_at: str | None
    last_error_code: str | None
    exchange_order_id: str | None
    exchange_status: str | None


class LifecycleSubmissionStore:
    """Persist create-intent/client-order authority before exchange side effects."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def prepare(
        self,
        *,
        submission_intent_id: str,
        start_gate: LifecycleStartGateRecord,
        target_client_order_id: str | None = None,
    ) -> tuple[LifecycleSubmissionRecord, bool]:
        try:
            intent = build_lifecycle_submission_intent(
                submission_intent_id=submission_intent_id,
                start_gate=_start_gate_body(start_gate),
                start_gate_digest=start_gate.payload_digest,
                target_client_order_id=target_client_order_id,
            )
        except LifecycleSubmissionError as exc:
            raise PostgresPersistenceError(str(exc)) from exc
        payload = intent.to_payload()
        payload_text = canonical_json_text(payload)
        digest = lifecycle_submission_intent_digest(intent)
        body = payload["lifecycle_submission_intent"]
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triggertrade_lifecycle_submission_intents (
                    submission_intent_id, start_gate_id, order_spec_id, authorization_id,
                    capital_grant_id, decision_cycle_id, set_result_id,
                    position_decision_id, construction_result_id, position_plan_id,
                    tranche_id, symbol, direction, target_client_order_id,
                    lifecycle_state, order_spec_digest, submit_authorized_digest,
                    start_gate_digest, payload_json, payload_digest
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s::jsonb, %s
                )
                ON CONFLICT DO NOTHING
                RETURNING
                    submission_intent_id, start_gate_id, order_spec_id, authorization_id,
                    capital_grant_id, decision_cycle_id, set_result_id,
                    position_decision_id, construction_result_id, position_plan_id,
                    tranche_id, symbol, direction, target_client_order_id,
                    lifecycle_state, order_spec_digest, submit_authorized_digest,
                    start_gate_digest, payload_json::text, payload_digest,
                    dispatch_attempts, last_dispatch_cutpoint_id,
                    last_dispatch_started_at::text, last_uncertain_at::text,
                    last_error_code, exchange_order_id, exchange_status
                """,
                (
                    body["submission_intent_id"],
                    body["start_gate_id"],
                    body["order_spec_id"],
                    body["authorization_id"],
                    body["capital_grant_id"],
                    body["decision_cycle_id"],
                    body["set_result_id"],
                    body["position_decision_id"],
                    body["construction_result_id"],
                    body["position_plan_id"],
                    body["tranche_id"],
                    body["symbol"],
                    body["direction"],
                    body["target_client_order_id"],
                    body["lifecycle_state"],
                    body["order_spec_digest"],
                    body["submit_authorized_digest"],
                    body["start_gate_digest"],
                    payload_text,
                    digest,
                ),
            )
            row = cursor.fetchone()
        if row is not None:
            return _record_from_row(row), True
        existing = (
            self.get_by_submission_intent_id(submission_intent_id=submission_intent_id)
            or self.get_by_start_gate_id(start_gate_id=start_gate.start_gate_id)
            or self.get_by_target_client_order_id(target_client_order_id=body["target_client_order_id"])
        )
        if existing is None:
            raise PostgresPersistenceError("lifecycle submission insert conflicted but no record was found")
        if (
            existing.payload_digest != digest
            or existing.submission_intent_id != submission_intent_id
            or existing.start_gate_id != start_gate.start_gate_id
            or existing.target_client_order_id != body["target_client_order_id"]
        ):
            raise LifecycleSubmissionConflict("lifecycle submission intent already exists with different content")
        return existing, False

    def mark_submitting(
        self,
        *,
        submission_intent_id: str,
        dispatch_cutpoint_id: str,
        started_at: str,
    ) -> LifecycleSubmissionRecord:
        return self._mark_dispatch(
            submission_intent_id=submission_intent_id,
            lifecycle_state=SUBMITTING,
            dispatch_cutpoint_id=dispatch_cutpoint_id,
            started_at=started_at,
            exchange_order_id=None,
            exchange_status=None,
            error_code=None,
        )

    def mark_uncertain(
        self,
        *,
        submission_intent_id: str,
        dispatch_cutpoint_id: str,
        uncertain_at: str,
        error_code: str,
    ) -> LifecycleSubmissionRecord:
        record = self._get_required(submission_intent_id)
        if record.last_dispatch_cutpoint_id != dispatch_cutpoint_id:
            raise LifecycleSubmissionConflict("uncertain dispatch cutpoint must match the active submit attempt")
        with self._connection.cursor() as cursor:
            cursor.execute(
                _UPDATE_STATE
                + """
                lifecycle_state = %s,
                last_uncertain_at = %s::timestamptz,
                last_error_code = %s,
                updated_at = now()
                WHERE submission_intent_id = %s
                  AND lifecycle_state IN ('SUBMITTING', 'SUBMISSION_UNCERTAIN')
                RETURNING
                    submission_intent_id, start_gate_id, order_spec_id, authorization_id,
                    capital_grant_id, decision_cycle_id, set_result_id,
                    position_decision_id, construction_result_id, position_plan_id,
                    tranche_id, symbol, direction, target_client_order_id,
                    lifecycle_state, order_spec_digest, submit_authorized_digest,
                    start_gate_digest, payload_json::text, payload_digest,
                    dispatch_attempts, last_dispatch_cutpoint_id,
                    last_dispatch_started_at::text, last_uncertain_at::text,
                    last_error_code, exchange_order_id, exchange_status
                """,
                (SUBMISSION_UNCERTAIN, uncertain_at, error_code, submission_intent_id),
            )
            row = cursor.fetchone()
        if row is None:
            current = self._get_required(submission_intent_id)
            if current.lifecycle_state == SUBMITTED:
                raise LifecycleSubmissionConflict("submitted lifecycle intent cannot become uncertain")
            raise PostgresPersistenceError(f"lifecycle submission intent not found: {submission_intent_id}")
        return _record_from_row(row)

    def mark_submitted(
        self,
        *,
        submission_intent_id: str,
        exchange_order_id: str,
        exchange_status: str,
    ) -> LifecycleSubmissionRecord:
        record = self._get_required(submission_intent_id)
        if record.dispatch_attempts < 1:
            raise LifecycleSubmissionConflict("cannot mark submitted before a persisted dispatch cutpoint")
        if record.lifecycle_state == SUBMITTED:
            if record.exchange_order_id == exchange_order_id and record.exchange_status == exchange_status:
                return record
            raise LifecycleSubmissionConflict("submitted lifecycle intent already has a different exchange identity")
        with self._connection.cursor() as cursor:
            cursor.execute(
                _UPDATE_STATE
                + """
                lifecycle_state = %s,
                exchange_order_id = %s,
                exchange_status = %s,
                updated_at = now()
                WHERE submission_intent_id = %s
                  AND lifecycle_state IN ('SUBMITTING', 'SUBMISSION_UNCERTAIN')
                RETURNING
                    submission_intent_id, start_gate_id, order_spec_id, authorization_id,
                    capital_grant_id, decision_cycle_id, set_result_id,
                    position_decision_id, construction_result_id, position_plan_id,
                    tranche_id, symbol, direction, target_client_order_id,
                    lifecycle_state, order_spec_digest, submit_authorized_digest,
                    start_gate_digest, payload_json::text, payload_digest,
                    dispatch_attempts, last_dispatch_cutpoint_id,
                    last_dispatch_started_at::text, last_uncertain_at::text,
                    last_error_code, exchange_order_id, exchange_status
                """,
                (SUBMITTED, exchange_order_id, exchange_status, submission_intent_id),
            )
            row = cursor.fetchone()
        if row is not None:
            return _record_from_row(row)
        existing = self._get_required(submission_intent_id)
        if existing.lifecycle_state == SUBMITTED:
            if existing.exchange_order_id == exchange_order_id and existing.exchange_status == exchange_status:
                return existing
            raise LifecycleSubmissionConflict("submitted lifecycle intent already has a different exchange identity")
        raise LifecycleSubmissionConflict("submission intent is not submittable")

    def get_by_submission_intent_id(self, *, submission_intent_id: str) -> LifecycleSubmissionRecord | None:
        return self._get("submission_intent_id", submission_intent_id)

    def get_by_start_gate_id(self, *, start_gate_id: str) -> LifecycleSubmissionRecord | None:
        return self._get("start_gate_id", start_gate_id)

    def get_by_target_client_order_id(self, *, target_client_order_id: str) -> LifecycleSubmissionRecord | None:
        return self._get("target_client_order_id", target_client_order_id)

    def unresolved(self) -> tuple[LifecycleSubmissionRecord, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                _SELECT_SUBMISSION
                + """
                WHERE lifecycle_state IN ('READY_TO_SUBMIT', 'SUBMITTING', 'SUBMISSION_UNCERTAIN')
                ORDER BY updated_at, submission_intent_id
                """
            )
            rows = cursor.fetchall()
        return tuple(_record_from_row(row) for row in rows)

    def _mark_dispatch(
        self,
        *,
        submission_intent_id: str,
        lifecycle_state: str,
        dispatch_cutpoint_id: str,
        started_at: str,
        exchange_order_id: str | None,
        exchange_status: str | None,
        error_code: str | None,
    ) -> LifecycleSubmissionRecord:
        if lifecycle_state not in SUBMISSION_STATES:
            raise PostgresPersistenceError("unsupported lifecycle submission state")
        with self._connection.cursor() as cursor:
            cursor.execute(
                _UPDATE_STATE
                + """
                lifecycle_state = %s,
                dispatch_attempts = dispatch_attempts + 1,
                last_dispatch_cutpoint_id = %s,
                last_dispatch_started_at = %s::timestamptz,
                last_error_code = %s,
                exchange_order_id = %s,
                exchange_status = %s,
                updated_at = now()
                WHERE submission_intent_id = %s
                  AND lifecycle_state = 'READY_TO_SUBMIT'
                RETURNING
                    submission_intent_id, start_gate_id, order_spec_id, authorization_id,
                    capital_grant_id, decision_cycle_id, set_result_id,
                    position_decision_id, construction_result_id, position_plan_id,
                    tranche_id, symbol, direction, target_client_order_id,
                    lifecycle_state, order_spec_digest, submit_authorized_digest,
                    start_gate_digest, payload_json::text, payload_digest,
                    dispatch_attempts, last_dispatch_cutpoint_id,
                    last_dispatch_started_at::text, last_uncertain_at::text,
                    last_error_code, exchange_order_id, exchange_status
                """,
                (
                    lifecycle_state,
                    dispatch_cutpoint_id,
                    started_at,
                    error_code,
                    exchange_order_id,
                    exchange_status,
                    submission_intent_id,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            existing = self._get_required(submission_intent_id)
            if existing.last_dispatch_cutpoint_id == dispatch_cutpoint_id and existing.lifecycle_state == lifecycle_state:
                return existing
            raise LifecycleSubmissionConflict("submission intent is not dispatchable")
        return _record_from_row(row)

    def _get_required(self, submission_intent_id: str) -> LifecycleSubmissionRecord:
        record = self.get_by_submission_intent_id(submission_intent_id=submission_intent_id)
        if record is None:
            raise PostgresPersistenceError("lifecycle submission intent does not exist")
        return record

    def _get(self, field: str, value: str) -> LifecycleSubmissionRecord | None:
        with self._connection.cursor() as cursor:
            cursor.execute(_SELECT_SUBMISSION + f" WHERE {field} = %s", (value,))
            row = cursor.fetchone()
        return None if row is None else _record_from_row(row)


_SELECT_SUBMISSION = """
SELECT
    submission_intent_id, start_gate_id, order_spec_id, authorization_id,
    capital_grant_id, decision_cycle_id, set_result_id,
    position_decision_id, construction_result_id, position_plan_id,
    tranche_id, symbol, direction, target_client_order_id,
    lifecycle_state, order_spec_digest, submit_authorized_digest,
    start_gate_digest, payload_json::text, payload_digest,
    dispatch_attempts, last_dispatch_cutpoint_id,
    last_dispatch_started_at::text, last_uncertain_at::text,
    last_error_code, exchange_order_id, exchange_status
FROM triggertrade_lifecycle_submission_intents
"""

_UPDATE_STATE = """
UPDATE triggertrade_lifecycle_submission_intents
SET
"""


def _start_gate_body(record: LifecycleStartGateRecord) -> dict[str, Any]:
    payload = dict(record.payload["lifecycle_start_gate"])
    payload["start_gate_id"] = record.start_gate_id
    return payload


def _record_from_row(row: tuple[Any, ...]) -> LifecycleSubmissionRecord:
    return LifecycleSubmissionRecord(
        submission_intent_id=str(row[0]),
        start_gate_id=str(row[1]),
        order_spec_id=str(row[2]),
        authorization_id=str(row[3]),
        capital_grant_id=str(row[4]),
        decision_cycle_id=str(row[5]),
        set_result_id=str(row[6]),
        position_decision_id=str(row[7]),
        construction_result_id=str(row[8]),
        position_plan_id=str(row[9]),
        tranche_id=str(row[10]),
        symbol=str(row[11]),
        direction=str(row[12]),
        target_client_order_id=str(row[13]),
        lifecycle_state=str(row[14]),
        order_spec_digest=str(row[15]),
        submit_authorized_digest=str(row[16]),
        start_gate_digest=str(row[17]),
        payload=json.loads(str(row[18]), parse_float=Decimal),
        payload_digest=str(row[19]),
        dispatch_attempts=int(row[20]),
        last_dispatch_cutpoint_id=None if row[21] is None else str(row[21]),
        last_dispatch_started_at=None if row[22] is None else str(row[22]),
        last_uncertain_at=None if row[23] is None else str(row[23]),
        last_error_code=None if row[24] is None else str(row[24]),
        exchange_order_id=None if row[25] is None else str(row[25]),
        exchange_status=None if row[26] is None else str(row[26]),
    )


def _require_row(row: tuple[Any, ...] | None, submission_intent_id: str) -> LifecycleSubmissionRecord:
    if row is None:
        raise PostgresPersistenceError(f"lifecycle submission intent not found: {submission_intent_id}")
    return _record_from_row(row)
