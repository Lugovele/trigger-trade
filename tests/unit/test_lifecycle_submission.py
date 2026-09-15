from __future__ import annotations

import pytest

from triggertrade.execution.futures import futures_client_order_id
from triggertrade.lifecycle_submission import (
    LifecycleSubmissionError,
    build_lifecycle_submission_intent,
    lifecycle_client_order_id,
    lifecycle_submission_intent_digest,
)
from tests.unit.test_lifecycle_start_gate import valid_gate_inputs
from triggertrade.lifecycle_start_gate import lifecycle_start_gate_digest, match_lifecycle_start_gate


def test_lifecycle_submission_intent_binds_lineage_client_id_and_digest():
    spec, authorization = valid_gate_inputs()
    start_gate = match_lifecycle_start_gate(order_spec=spec, submit_authorized=authorization)
    payload = start_gate.to_payload()["lifecycle_start_gate"]
    payload["start_gate_id"] = "start-gate-1"

    intent = build_lifecycle_submission_intent(
        submission_intent_id="submission-1",
        start_gate=payload,
        start_gate_digest=lifecycle_start_gate_digest(start_gate),
    )

    assert intent.target_client_order_id == lifecycle_client_order_id("order-spec-1")
    assert intent.target_client_order_id == futures_client_order_id("order-spec-1")
    assert intent.lifecycle_state == "READY_TO_SUBMIT"
    assert intent.order_spec_digest == payload["order_spec_digest"]
    assert lifecycle_submission_intent_digest(intent) == (
        "2c8b8db8fc94af4bcd7f9cce0b5204bcb06d0fe2c75463c8a4177f62850edb33"
    )


def test_lifecycle_submission_intent_rejects_missing_lineage():
    spec, authorization = valid_gate_inputs()
    start_gate = match_lifecycle_start_gate(order_spec=spec, submit_authorized=authorization)
    payload = start_gate.to_payload()["lifecycle_start_gate"]
    payload["start_gate_id"] = "start-gate-1"
    payload["order_spec_id"] = ""

    with pytest.raises(LifecycleSubmissionError, match="order_spec_id"):
        build_lifecycle_submission_intent(
            submission_intent_id="submission-1",
            start_gate=payload,
            start_gate_digest=lifecycle_start_gate_digest(start_gate),
        )
