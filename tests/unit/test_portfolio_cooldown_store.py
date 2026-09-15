from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    PortfolioCooldownConflict,
    PortfolioCooldownStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.portfolio_cooldown import CooldownPin


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_pr006_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_portfolio_cooldown_store_persists_replays_and_recovers_effective_gate():
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
        ]
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = PortfolioCooldownStore(uow.connection)
            record, inserted = store.create_pin(
                authorization_id="authorization-1",
                tranche_id="tranche-1",
                symbol="btcusdt",
                portfolio_config_id="portfolio-config-1",
                portfolio_config_version="v1",
                portfolio_config_digest="0" * 64,
                pinned_cooldown_duration_seconds=3600,
            )
            replayed, replay_inserted = store.create_pin(
                authorization_id="authorization-1",
                tranche_id="tranche-1",
                symbol="BTCUSDT",
                portfolio_config_id="portfolio-config-1",
                portfolio_config_version="v1",
                portfolio_config_digest="0" * 64,
                pinned_cooldown_duration_seconds=3600,
            )
            applied = store.apply_order_event(
                order_event(entry_acceptance_status="PROVEN", entry_accepted_at="2026-09-15T10:00:00Z")
            )

        with PostgresUnitOfWork(factory) as restarted:
            gate = PortfolioCooldownStore(restarted.connection).gate_for_symbol(
                symbol="BTCUSDT",
                as_of="2026-09-15T10:30:00Z",
            )

        assert inserted is True
        assert replay_inserted is False
        assert replayed.pin_payload_digest == record.pin_payload_digest
        assert applied.pin.cooldown_until == "2026-09-15T11:00:00Z"
        assert gate.status == "BLOCKED"
        assert gate.cooldown_until == "2026-09-15T11:00:00Z"
    finally:
        _drop_schema(settings)


def test_portfolio_cooldown_store_rejects_changed_pin_and_clears_zero_fill():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = PortfolioCooldownStore(uow.connection)
            store.create_pin(
                authorization_id="authorization-1",
                tranche_id="tranche-1",
                symbol="BTCUSDT",
                portfolio_config_id="portfolio-config-1",
                portfolio_config_version="v1",
                portfolio_config_digest="0" * 64,
                pinned_cooldown_duration_seconds=3600,
            )
            with pytest.raises(PortfolioCooldownConflict):
                store.create_pin(
                    authorization_id="authorization-1",
                    tranche_id="tranche-1",
                    symbol="BTCUSDT",
                    portfolio_config_id="portfolio-config-1",
                    portfolio_config_version="v1",
                    portfolio_config_digest="0" * 64,
                    pinned_cooldown_duration_seconds=7200,
                )
            store.apply_order_event(
                order_event(entry_acceptance_status="PROVEN", entry_accepted_at="2026-09-15T10:00:00Z", revision=2)
            )
            cleared = store.apply_order_event(order_event(lifecycle_state="CANCELLED_ZERO_FILL", revision=3))
            gate = store.gate_for_symbol(symbol="BTCUSDT", as_of="2026-09-15T10:30:00Z")

        assert cleared.pin.cooldown_state == "CLEARED"
        assert gate.status == "PASS"
    finally:
        _drop_schema(settings)


def cooldown_pin(
    *,
    authorization_id: str = "authorization-1",
    tranche_id: str = "tranche-1",
    duration_seconds: int = 3600,
) -> CooldownPin:
    return CooldownPin(
        authorization_id=authorization_id,
        tranche_id=tranche_id,
        symbol="BTCUSDT",
        portfolio_config_id="portfolio-config-1",
        portfolio_config_version="v1",
        portfolio_config_digest="0" * 64,
        pinned_cooldown_duration_seconds=duration_seconds,
    )


def order_event(
    *,
    authorization_id: str = "authorization-1",
    tranche_id: str = "tranche-1",
    lifecycle_state: str = "PENDING_ENTRY",
    entry_acceptance_status: str = "UNAVAILABLE",
    entry_accepted_at: str | None = None,
    integrity_state: str = "CLEAR",
    revision: int = 1,
) -> dict:
    provenance = {
        "source_endpoint": "bybit.private.order",
        "source_record_id": "exchange-order-1",
        "source_field": "createdTime",
        "native_value": "2026-09-15T10:00:00Z",
        "mapping_profile_version": "ENTRY_ACCEPTANCE_MAPPING_V1",
        "evidence_ref": "evidence://entry-acceptance/order-event-1",
    }
    return {
        "order_event": {
            "contract_version": 7,
            "event_variant": "LOGICAL_TRANCHE",
            "event_id": f"order-event-{authorization_id}-{tranche_id}-{revision}",
            "event_type": "ENTRY_ACCEPTANCE_STATE",
            "occurred_at": "2026-09-15T10:00:00Z",
            "lifecycle_revision": revision,
            "authorization_id": authorization_id,
            "capital_grant_id": "capital-grant-1",
            "decision_cycle_id": "decision-cycle-1",
            "set_result_id": "set-result-1",
            "position_decision_id": "position-decision-1",
            "construction_result_id": "construction-result-1",
            "position_plan_id": "position-plan-1",
            "tranche_id": tranche_id,
            "order_spec_id": "order-spec-1",
            "symbol": "BTCUSDT",
            "order_leg": {
                "role": "ENTRY",
                "client_order_link_id": "client-order-1",
                "exchange_order_id": "exchange-order-1",
                "parent_exchange_order_id": None,
                "protection_generation": None,
                "close_intent_id": None,
                "close_child_id": None,
                "protection_child_id": None,
            },
            "native_allocation": None,
            "lifecycle_state": lifecycle_state,
            "exposure_qty": "0",
            "cumulative_entry_filled_qty": "0",
            "remaining_entry_qty": "0",
            "close_intent_active": False,
            "close_commitment_quantity_basis": None,
            "terminal_predicates": {
                "logical_exposure_zero": False,
                "entry_remainder_terminal": False,
                "children_terminal_or_disabled": False,
                "close_intent_resolved": False,
                "financial_finality_established": False,
                "no_competing_execution_authority": False,
            },
            "external_cause": None,
            "financial_result": None,
            "entry_accepted_at": entry_accepted_at,
            "entry_acceptance_status": entry_acceptance_status,
            "entry_acceptance_provenance": provenance if entry_acceptance_status == "PROVEN" else None,
            "numeric_policy_version": "TT_NUMERIC_V1",
            "entry_acceptance_integrity": {
                "state": integrity_state,
                "revision": 0,
                "conflict_id": "acceptance-conflict-1" if integrity_state == "CONFLICT" else None,
                "evidence": [provenance] if integrity_state == "CONFLICT" else [],
                "resolution_id": None,
                "resolution_evidence_ref": None,
            },
        }
    }
