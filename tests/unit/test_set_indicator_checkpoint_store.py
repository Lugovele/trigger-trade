from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.persistence import (
    PostgresConnectionFactory,
    PostgresPersistenceError,
    PostgresSettings,
    PostgresUnitOfWork,
    SetIndicatorCheckpointConflict,
    SetIndicatorCheckpointStore,
    apply_postgres_migrations,
)
from triggertrade.persistence.set_indicator_checkpoint_store import _validate_checkpoint_payload


pytest.importorskip("psycopg")


def test_set_indicator_checkpoint_payload_validation_without_postgres_rejects_digest_and_work_value_spelling():
    uppercase_digest = _atr_checkpoint_payload("1.2")
    uppercase_digest["source_manifest"] = {
        **uppercase_digest["source_manifest"],  # type: ignore[arg-type]
        "source_digest": "A" * 64,
    }
    with pytest.raises(PostgresPersistenceError, match="sha256"):
        _validate_checkpoint_payload(indicator_type="ATR15", payload=uppercase_digest)

    noncanonical_work = _atr_checkpoint_payload("1.0")
    with pytest.raises(PostgresPersistenceError, match="work_value"):
        _validate_checkpoint_payload(indicator_type="ATR15", payload=noncanonical_work)

    canonical = _atr_checkpoint_payload("1.2")
    _validate_checkpoint_payload(indicator_type="atr15", payload=canonical)


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_b5a_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_set_indicator_checkpoint_store_replays_same_content_and_rejects_changed_content():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)

        with PostgresUnitOfWork(factory) as uow:
            store = SetIndicatorCheckpointStore(uow.connection)
            payload = _atr_checkpoint_payload("1.071428571428571428571428571428571429")
            first = store.put_checkpoint(
                checkpoint_id="atr15-sol-001",
                indicator_type="ATR15",
                payload=payload,
            )
            replay = store.put_checkpoint(
                checkpoint_id="atr15-sol-001",
                indicator_type="ATR15",
                payload=payload,
            )
            assert first.inserted is True
            assert replay.inserted is False
            assert replay.payload_digest == first.payload_digest
            with pytest.raises(SetIndicatorCheckpointConflict):
                store.put_checkpoint(
                    checkpoint_id="atr15-sol-001",
                    indicator_type="ATR15",
                    payload=_atr_checkpoint_payload("1.2"),
                )
            with pytest.raises(PostgresPersistenceError, match="missing fields"):
                store.put_checkpoint(
                    checkpoint_id="atr15-sol-scalar-only",
                    indicator_type="ATR15",
                    payload={"symbol": "SOLUSDT", "atr_work": "1.2"},
                )
            incomplete_manifest = _atr_checkpoint_payload("1.2")
            incomplete_manifest["source_manifest"] = {"x": "y"}
            with pytest.raises(PostgresPersistenceError, match="source_manifest missing fields"):
                store.put_checkpoint(
                    checkpoint_id="atr15-sol-incomplete-manifest",
                    indicator_type="ATR15",
                    payload=incomplete_manifest,
                )
            duplicate_ids = _atr_checkpoint_payload("1.2")
            duplicate_ids["seed_candle_ids"] = ["candle-0", "candle-0", *[f"candle-{i}" for i in range(2, 14)]]
            duplicate_ids["processed_source_ids"] = duplicate_ids["seed_candle_ids"]
            duplicate_ids["last_candle_id"] = "candle-13"
            with pytest.raises(PostgresPersistenceError, match="unique"):
                store.put_checkpoint(
                    checkpoint_id="atr15-sol-duplicate-ids",
                    indicator_type="ATR15",
                    payload=duplicate_ids,
                )
            mismatched_last = _atr_checkpoint_payload("1.2")
            mismatched_last["last_candle_id"] = "not-last"
            with pytest.raises(PostgresPersistenceError, match="last processed"):
                store.put_checkpoint(
                    checkpoint_id="atr15-sol-bad-last",
                    indicator_type="ATR15",
                    payload=mismatched_last,
                )
            bad_range = _atr_checkpoint_payload("1.2")
            bad_range["true_ranges"] = ["1" for _ in range(13)] + ["1/3"]
            with pytest.raises(PostgresPersistenceError, match="canonical decimal"):
                store.put_checkpoint(
                    checkpoint_id="atr15-sol-bad-range",
                    indicator_type="ATR15",
                    payload=bad_range,
                )
            trailing_zero_range = _atr_checkpoint_payload("1.2")
            trailing_zero_range["true_ranges"] = ["1" for _ in range(13)] + ["1.0"]
            with pytest.raises(PostgresPersistenceError, match="canonical decimal"):
                store.put_checkpoint(
                    checkpoint_id="atr15-sol-trailing-zero-range",
                    indicator_type="ATR15",
                    payload=trailing_zero_range,
                )
            negative_zero_range = _atr_checkpoint_payload("1.2")
            negative_zero_range["true_ranges"] = ["1" for _ in range(13)] + ["-0"]
            with pytest.raises(PostgresPersistenceError, match="canonical decimal"):
                store.put_checkpoint(
                    checkpoint_id="atr15-sol-negative-zero-range",
                    indicator_type="ATR15",
                    payload=negative_zero_range,
                )
            bad_digest = _atr_checkpoint_payload("1.2")
            bad_digest["source_proof_digest"] = "not-a-digest"
            with pytest.raises(PostgresPersistenceError, match="sha256"):
                store.put_checkpoint(
                    checkpoint_id="atr15-sol-bad-digest",
                    indicator_type="ATR15",
                    payload=bad_digest,
                )
            with pytest.raises(SetIndicatorCheckpointConflict):
                store.put_checkpoint(
                    checkpoint_id="atr15-sol-001",
                    indicator_type="atr15",
                    payload=_atr_checkpoint_payload("1.3"),
                )

        with PostgresUnitOfWork(factory) as restarted:
            store = SetIndicatorCheckpointStore(restarted.connection)
            restored = store.get_checkpoint(checkpoint_id="atr15-sol-001", indicator_type="ATR15")
        assert restored is not None
        assert restored.payload["work_value"] == "1.071428571428571428571428571428571429"
    finally:
        _drop_schema(settings)


def _atr_checkpoint_payload(work_value: str) -> dict[str, object]:
    return {
        "numeric_policy_version": "TT_SET_NUMERIC_V1",
        "source_manifest": {
            "series_id": "SOLUSDT:15m:KLINES",
            "seed_anchor": "2026-09-21T00:00:00Z",
            "predecessor_close": "100",
            "source_digest": "a" * 64,
            "first_complete_history_evidence_ref": "history-proof-1",
        },
        "processed_source_ids": [f"candle-{i}" for i in range(14)],
        "seed_candle_ids": [f"candle-{i}" for i in range(14)],
        "true_ranges": ["1" for _ in range(14)],
        "last_candle_id": "candle-13",
        "work_value": work_value,
        "source_proof_digest": "b" * 64,
        "checkpoint_digest_basis": "ATR15_Q36_WILDER_V1",
    }
