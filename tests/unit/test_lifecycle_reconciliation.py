from __future__ import annotations

import pytest

from triggertrade.lifecycle_reconciliation import (
    LifecycleReconciliationError,
    attribution_resolution_id_for_observation,
    native_observation_id_for_scope,
    reconciliation_resolution_id_for_observation,
    validate_reconciliation_event,
)


def _scope() -> dict[str, object]:
    return {
        "account_id": "acct-1",
        "environment": "TEST",
        "symbol": "BTCUSDT",
        "native_side": "SELL",
        "position_idx": 2,
    }


def native_event(**overrides):
    observation = {
        "native_observation_id": "obs-1",
        "native_scope_revision": 1,
        "native_scope": _scope(),
        "source_event_id": "source-event-1",
        "source_execution_id": "exec-1",
        "exchange_order_id": "exchange-order-1",
        "parent_exchange_order_id": None,
        "client_order_link_id": None,
        "quantity": "0.25",
        "price": "100",
        "effective_at": "2026-09-15T10:00:00Z",
        "external_cause": "OTHER_EXCHANGE",
        "logical_attribution_state": "UNRESOLVED",
        "source_ref": "GET_EXECUTIONS:exec-1",
    }
    observation.update(overrides)
    return {
        "order_event": {
            "contract_version": 7,
            "event_variant": "NATIVE_UNATTRIBUTED_REDUCTION",
            "event_id": "native-event-1",
            "event_type": "NATIVE_EXPOSURE_REDUCTION_UNATTRIBUTED",
            "occurred_at": "2026-09-15T10:00:01Z",
            "native_observation": observation,
        }
    }


def resolution_event(*, revision: int = 1, complete: bool = True, event_id: str = "resolution-event-1"):
    observation_id = "obs-1"
    return {
        "order_event": {
            "contract_version": 7,
            "event_variant": "NATIVE_ATTRIBUTION_RESOLUTION",
            "event_id": event_id,
            "occurred_at": "2026-09-15T10:00:02Z",
            "resolution": {
                "native_observation_id": observation_id,
                "native_scope_revision": 1,
                "attribution_resolution_id": "resolution-1",
                "resolution_revision": revision,
                "native_scope": _scope(),
                "expected_allocation_ids": ["allocation-1"],
                "affected_tranche_ids": ["tranche-1"],
                "allocations": [
                    {
                        "allocation_id": "allocation-1",
                        "tranche_id": "tranche-1",
                        "decision_cycle_id": "cycle-1",
                        "allocated_quantity": "0.25",
                        "source_execution_ids": ["exec-1"],
                        "allocation_evidence": ["evidence-1"],
                    }
                ],
                "observed_quantity": "0.25",
                "resolution_complete": complete,
                "resolved_at": "2026-09-15T10:00:02Z" if complete else None,
            },
        }
    }


def scope_observation_event():
    return {
        "order_event": {
            "contract_version": 7,
            "event_variant": "NATIVE_SCOPE_RECONCILIATION_OBSERVED",
            "event_id": "scope-observed-1",
            "event_type": "NATIVE_SCOPE_RECONCILIATION_OBSERVED",
            "occurred_at": "2026-09-15T10:00:00Z",
            "native_observation": {
                "native_observation_id": "scope-obs-1",
                "native_scope_revision": 1,
                "native_scope": _scope(),
                "exchange_order_id": "protective-order-1",
                "order_role": "TP",
                "native_position_mode": "HEDGE_MODE",
                "observation_class": "PROTECTIVE_CHILD_LINEAGE_UNRESOLVED",
                "quantity_effect": "NONE",
                "factual_linkage": {
                    "native_parent_order_id": None,
                    "native_parent_client_order_link_id": None,
                    "native_link_group_id": "link-group-1",
                    "client_order_link_id": None,
                },
                "logical_attribution_state": "UNRESOLVED",
                "blocking_scope": _scope(),
                "source_endpoint": "GET_OPEN_ORDERS",
                "source_record_id": "protective-order-1",
                "provenance": [],
                "observed_at": "2026-09-15T10:00:00Z",
                "reason_code": "UNBOUND_PROTECTIVE_CHILD",
                "reconciliation_resolution_id": None,
                "resolution_revision": 0,
            },
        }
    }


def scope_resolution_event():
    return {
        "order_event": {
            "contract_version": 7,
            "event_variant": "NATIVE_SCOPE_RECONCILIATION_RESOLUTION",
            "event_id": "scope-resolution-event-1",
            "occurred_at": "2026-09-15T10:00:02Z",
            "resolution": {
                "native_observation_id": "scope-obs-1",
                "native_scope_revision": 1,
                "native_scope": _scope(),
                "exchange_order_id": "protective-order-1",
                "reconciliation_resolution_id": "scope-resolution-1",
                "resolution_revision": 1,
                "expected_binding_ids": ["binding-1"],
                "bindings": [
                    {
                        "binding_id": "binding-1",
                        "exchange_order_id": "protective-order-1",
                        "tranche_id": "tranche-1",
                        "decision_cycle_id": "cycle-1",
                        "order_role": "TP",
                        "evidence_refs": ["evidence-1"],
                    }
                ],
                "disposition": "OWNERSHIP_PROVEN",
                "resolution_complete": True,
                "no_unresolved_execution_authority": True,
                "native_order_terminal_or_disabled": False,
                "evidence_refs": ["evidence-1"],
                "resolved_at": "2026-09-15T10:00:02Z",
            },
        }
    }


def test_native_observation_event_validates_and_binds_digest():
    evidence = validate_reconciliation_event(native_event())

    assert evidence.evidence_kind == "NATIVE_UNATTRIBUTED_REDUCTION"
    assert evidence.native_observation_id == "obs-1"
    assert evidence.native_scope_revision == 1
    assert evidence.evidence_revision == 1
    assert evidence.complete is False
    assert len(evidence.payload_digest) == 64


def test_complete_resolution_event_validates_as_complete():
    evidence = validate_reconciliation_event(resolution_event())

    assert evidence.evidence_kind == "NATIVE_ATTRIBUTION_RESOLUTION"
    assert evidence.revision_id == "resolution-1"
    assert evidence.evidence_revision == 1
    assert evidence.complete is True


def test_scope_observation_and_resolution_variants_validate():
    observed = validate_reconciliation_event(scope_observation_event())
    resolved = validate_reconciliation_event(scope_resolution_event())

    assert observed.evidence_kind == "NATIVE_SCOPE_RECONCILIATION_OBSERVED"
    assert observed.complete is False
    assert resolved.evidence_kind == "NATIVE_SCOPE_RECONCILIATION_RESOLUTION"
    assert resolved.complete is True


def test_unknown_fields_and_logical_events_are_rejected():
    payload = native_event()
    payload["order_event"]["native_observation"]["extra"] = "not-approved"

    with pytest.raises(LifecycleReconciliationError, match="unknown fields"):
        validate_reconciliation_event(payload)


def test_stable_ids_use_canonical_scope_not_insertion_order():
    scope_a = _scope()
    scope_b = {
        "symbol": "BTCUSDT",
        "environment": "TEST",
        "position_idx": 2,
        "native_side": "SELL",
        "account_id": "acct-1",
    }

    assert native_observation_id_for_scope(scope_a, source_identity="exchange-order-1") == native_observation_id_for_scope(
        scope_b,
        source_identity="exchange-order-1",
    )
    assert attribution_resolution_id_for_observation("obs-1").startswith("attribution-resolution-")
    assert reconciliation_resolution_id_for_observation("obs-1").startswith("scope-resolution-")
