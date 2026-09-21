from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    FactualEvidenceConflict,
    FactualEvidenceStore,
    PostgresConnectionFactory,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b3_facts_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_factual_evidence_store_persists_replays_and_recovers_accepted_content():
    settings = _settings()
    try:
        applied = apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        assert applied[-1].version == "0022"
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        payload = _payload(price="25000.1")
        raw = {"native_id": "raw-1", "lastPrice": "25000.10"}

        with PostgresUnitOfWork(factory) as uow:
            store = FactualEvidenceStore(uow.connection)
            record, inserted = store.put_evidence(
                evidence_id="md-page-1",
                owner="Set",
                evidence_kind="MARKET_DATA_PAGE",
                payload=payload,
                raw_payload=raw,
                provenance={"source_endpoint": "/v5/market/tickers", "source_record_id": "BTCUSDT"},
                anchors=("market:/v5/market/tickers:BTCUSDT",),
            )
            replayed, replay_inserted = store.put_evidence(
                evidence_id="md-page-1",
                owner="Set",
                evidence_kind="MARKET_DATA_PAGE",
                payload=payload,
                raw_payload=raw,
                provenance={"source_endpoint": "/v5/market/tickers", "source_record_id": "BTCUSDT"},
                anchors=("market:/v5/market/tickers:BTCUSDT",),
            )

        with PostgresUnitOfWork(factory) as restarted:
            store = FactualEvidenceStore(restarted.connection)
            recovered = store.get_evidence_by_anchor(anchor_key="market:/v5/market/tickers:BTCUSDT")

        assert inserted is True
        assert replay_inserted is False
        assert replayed.payload_digest == record.payload_digest
        assert recovered is not None
        assert recovered.evidence_id == "md-page-1"
    finally:
        _drop_schema(settings)


def test_factual_evidence_store_rejects_changed_accepted_identity_and_anchor_conflicts():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            store = FactualEvidenceStore(uow.connection)
            store.put_evidence(
                evidence_id="portfolio-response-1",
                owner="Portfolio Rules",
                evidence_kind="PORTFOLIO_DATA_RESPONSE",
                payload={"response_id": "pdr-1", "wallet": {"status": "AVAILABLE"}},
                anchors=("portfolio:response:pdr-1",),
            )
            with pytest.raises(FactualEvidenceConflict):
                store.put_evidence(
                    evidence_id="portfolio-response-1",
                    owner="Portfolio Rules",
                    evidence_kind="PORTFOLIO_DATA_RESPONSE",
                    payload={"response_id": "pdr-1", "wallet": {"status": "UNAVAILABLE"}},
                    anchors=("portfolio:response:pdr-1",),
                )
            with pytest.raises(FactualEvidenceConflict):
                store.put_evidence(
                    evidence_id="portfolio-response-2",
                    owner="Portfolio Rules",
                    evidence_kind="PORTFOLIO_DATA_RESPONSE",
                    payload={"response_id": "pdr-2"},
                    anchors=("portfolio:response:pdr-1",),
                )
        with PostgresUnitOfWork(factory) as verify:
            store = FactualEvidenceStore(verify.connection)
            assert store.get_evidence(evidence_id="portfolio-response-2") is None
            owner = store.get_evidence_by_anchor(anchor_key="portfolio:response:pdr-1")
            assert owner is not None
            assert owner.evidence_id == "portfolio-response-1"
    finally:
        _drop_schema(settings)


def test_preflight_records_known_content_challenge_before_ordinary_rejection_and_replays_it():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            FactualEvidenceStore(setup.connection).put_evidence(
                evidence_id="native-order-1",
                owner="Order Lifecycle",
                evidence_kind="ORDER_MANAGEMENT_FACT",
                payload={"exchange_order_id": "order-1", "status": "NEW"},
                raw_payload={"orderId": "order-1", "orderStatus": "New"},
                anchors=("bybit:/v5/order/realtime:order-1",),
            )

        with PostgresUnitOfWork(factory) as checkpoint:
            result = FactualEvidenceStore(checkpoint.connection).preflight_known_evidence(
                challenge_scope="ORDER_MANAGEMENT",
                anchors=("bybit:/v5/order/realtime:order-1",),
                raw_payload={"orderId": "order-1", "orderStatus": "Filled"},
                candidate_payload={"exchange_order_id": "order-1", "status": "FILLED"},
            )
            assert result.challenge is not None
            challenge_id = result.challenge.challenge_id

        with pytest.raises(RuntimeError):
            with PostgresUnitOfWork(factory) as ordinary_rejection:
                store = FactualEvidenceStore(ordinary_rejection.connection)
                assert store.get_challenge(challenge_id=challenge_id) is not None
                raise RuntimeError("ordinary parser rejection")

        with PostgresUnitOfWork(factory) as verify:
            store = FactualEvidenceStore(verify.connection)
            challenge = store.get_challenge(challenge_id=challenge_id)
            repeated = store.preflight_known_evidence(
                challenge_scope="ORDER_MANAGEMENT",
                anchors=("bybit:/v5/order/realtime:order-1",),
                raw_payload={"orderId": "order-1", "orderStatus": "Filled"},
                candidate_payload={"exchange_order_id": "order-1", "status": "FILLED"},
            )

        assert challenge is not None
        assert challenge.status == "QUARANTINED"
        assert challenge.challenge_kind == "CONTENT_CONTRADICTION"
        assert repeated.inserted is False
        assert repeated.challenge is not None
        assert repeated.challenge.challenge_id == challenge_id
    finally:
        _drop_schema(settings)


def test_preflight_handles_malformed_known_raw_ambiguous_anchors_and_unrecognized_input():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as setup:
            store = FactualEvidenceStore(setup.connection)
            store.put_evidence(
                evidence_id="exec-1",
                owner="Order Lifecycle",
                evidence_kind="NATIVE_EXECUTION_FACT",
                payload={"execution_id": "exec-1", "quantity": "1"},
                anchors=("bybit:execution:exec-1",),
            )
            store.put_evidence(
                evidence_id="order-2",
                owner="Order Lifecycle",
                evidence_kind="NATIVE_ORDER_FACT",
                payload={"exchange_order_id": "order-2", "status": "NEW"},
                anchors=("bybit:order:order-2",),
            )

        with PostgresUnitOfWork(factory) as uow:
            store = FactualEvidenceStore(uow.connection)
            malformed = store.preflight_known_evidence(
                challenge_scope="ORDER_MANAGEMENT",
                anchors=("bybit:execution:exec-1",),
                raw_payload={"execId": "exec-1", "malformed": True},
                candidate_payload=None,
                reason="known raw failed ordinary parsing",
            )
            ambiguous = store.preflight_known_evidence(
                challenge_scope="ORDER_MANAGEMENT",
                anchors=("bybit:execution:exec-1", "bybit:order:order-2"),
                raw_payload={"mixed": True},
                candidate_payload={"mixed": True},
            )
            unknown = store.preflight_known_evidence(
                challenge_scope="ORDER_MANAGEMENT",
                anchors=("bybit:unknown:nope",),
                raw_payload={"unrecognized": True},
                candidate_payload=None,
            )

        assert malformed.challenge is not None
        assert malformed.challenge.challenge_kind == "CONTENT_CONTRADICTION"
        assert ambiguous.challenge is not None
        assert ambiguous.challenge.challenge_kind == "AMBIGUOUS_OWNER"
        assert unknown.recognized is False
        assert unknown.challenge is None
    finally:
        _drop_schema(settings)


def test_preflight_preserves_coverage_nulls_as_distinct_from_omitted_fields():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        accepted = _financial_coverage_payload(
            {
                "status": "COMPLETE",
                "coverage_from": "2026-09-14T12:00:00Z",
                "coverage_to": "2026-09-14T12:00:00Z",
                "missing_ranges": [],
                "pagination_complete": True,
                "next_cursor": None,
                "source_watermark_at": None,
                "source_finality_confirmed": True,
                "source_endpoints": ["/v5/execution/list"],
                "reason_code": None,
            },
            component_not_applicable_evidence=None,
        )
        omitted = _financial_coverage_payload(
            {
                "status": "COMPLETE",
                "coverage_from": "2026-09-14T12:00:00Z",
                "coverage_to": "2026-09-14T12:00:00Z",
                "missing_ranges": [],
                "pagination_complete": True,
                "source_finality_confirmed": True,
                "source_endpoints": ["/v5/execution/list"],
            },
            component_not_applicable_evidence="OMIT",
        )
        with PostgresUnitOfWork(factory) as setup:
            FactualEvidenceStore(setup.connection).put_evidence(
                evidence_id="financial-coverage-1",
                owner="Order Lifecycle",
                evidence_kind="ORDER_MANAGEMENT_FINANCIAL_FACTS",
                payload=accepted,
                raw_payload={"requestId": "om-fin-req-1", "responseId": "om-fin-resp-1"},
                anchors=("order-management:financial:om-fin-req-1:om-fin-resp-1",),
            )

        with PostgresUnitOfWork(factory) as preflight:
            result = FactualEvidenceStore(preflight.connection).preflight_known_evidence(
                challenge_scope="ORDER_MANAGEMENT",
                anchors=("order-management:financial:om-fin-req-1:om-fin-resp-1",),
                raw_payload={"requestId": "om-fin-req-1", "responseId": "om-fin-resp-1", "coverage_shape": "omitted-null-fields"},
                candidate_payload=omitted,
                reason="coverage null fields omitted from replay",
            )

        assert result.challenge is not None
        assert result.challenge.challenge_kind == "CONTENT_CONTRADICTION"
        assert result.challenge.accepted_payload_digest != result.challenge.candidate_payload_digest
    finally:
        _drop_schema(settings)


def test_factual_evidence_rolls_back_uncommitted_acceptance_on_crash():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with pytest.raises(RuntimeError):
            with PostgresUnitOfWork(factory) as uow:
                FactualEvidenceStore(uow.connection).put_evidence(
                    evidence_id="uncommitted",
                    owner="Set",
                    evidence_kind="MARKET_DATA_PAGE",
                    payload={"page_id": "page-crash"},
                    anchors=("market:page-crash",),
                )
                raise RuntimeError("crash before commit")

        with PostgresUnitOfWork(factory) as verify:
            assert FactualEvidenceStore(verify.connection).get_evidence(evidence_id="uncommitted") is None
    finally:
        _drop_schema(settings)


def _payload(*, price: str) -> dict[str, object]:
    return {
        "selection_id": "sel-1",
        "page_id": "page-1",
        "dataset": "TICKER",
        "symbol": "BTCUSDT",
        "facts": {"last_price": price},
    }


def _financial_coverage_payload(coverage: dict[str, object], *, component_not_applicable_evidence: str | None) -> dict[str, object]:
    component_coverage = {
        "component": "TRADING_FEE",
        "applicable": True,
        "coverage": dict(coverage),
    }
    if component_not_applicable_evidence != "OMIT":
        component_coverage["not_applicable_evidence"] = component_not_applicable_evidence
    return {
        "order_management_response": {
            "contract_version": 4,
            "request_id": "om-fin-req-1",
            "response_id": "om-fin-resp-1",
            "operation": "GET_FINANCIAL_FACTS",
            "as_of": "2026-09-14T12:00:00Z",
            "result": "COMPLETE",
            "financial_facts": {
                "native_scope": {
                    "account_id": "acct-demo",
                    "environment": "TEST",
                    "symbol": "BTCUSDT",
                    "native_side": "BUY",
                    "position_idx": 1,
                },
                "requested_from": "2026-09-14T12:00:00Z",
                "requested_to": "2026-09-14T12:00:00Z",
                "coverage": coverage,
                "component_coverage": [component_coverage],
                "executions": [],
                "cashflows": [],
            },
            "exchange_error": None,
        }
    }
