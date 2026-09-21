"""Durable Set analytical checkpoint wrapper over OwnerStateStore."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.numeric_policy import NumericPolicyError, canonical_decimal_text, parse_decimal_text

from .postgres import OwnerStateConflict, OwnerStateRecord, OwnerStateStore, PostgresPersistenceError


class SetIndicatorCheckpointConflict(PostgresPersistenceError):
    """Raised when a Set checkpoint identity is replayed with different content."""


@dataclass(frozen=True)
class SetIndicatorCheckpointRecord:
    checkpoint_id: str
    indicator_type: str
    payload: dict[str, Any]
    payload_digest: str
    inserted: bool


class SetIndicatorCheckpointStore:
    """Persist immutable Set-owned indicator/checkpoint payloads."""

    def __init__(self, connection) -> None:
        self._owner_store = OwnerStateStore(connection)

    def put_checkpoint(
        self,
        *,
        checkpoint_id: str,
        indicator_type: str,
        payload: Mapping[str, Any],
    ) -> SetIndicatorCheckpointRecord:
        indicator_type = _indicator_type(indicator_type)
        payload_dict = dict(payload)
        _validate_checkpoint_payload(indicator_type=indicator_type, payload=payload_dict)
        wrapped = {
            "set_indicator_checkpoint": {
                "checkpoint_id": checkpoint_id,
                "indicator_type": indicator_type,
                "payload": payload_dict,
            }
        }
        try:
            record, inserted = self._owner_store.put_if_absent(
                owner="SET",
                state_type=f"SET_INDICATOR_{indicator_type}",
                state_id=checkpoint_id,
                payload=wrapped,
            )
        except OwnerStateConflict as exc:
            raise SetIndicatorCheckpointConflict("set indicator checkpoint already exists with different content") from exc
        return _from_owner_state(record, inserted=inserted)

    def get_checkpoint(self, *, checkpoint_id: str, indicator_type: str) -> SetIndicatorCheckpointRecord | None:
        indicator_type = _indicator_type(indicator_type)
        record = self._owner_store.get(
            owner="SET",
            state_type=f"SET_INDICATOR_{indicator_type}",
            state_id=checkpoint_id,
        )
        return None if record is None else _from_owner_state(record, inserted=False)


def _from_owner_state(record: OwnerStateRecord, *, inserted: bool) -> SetIndicatorCheckpointRecord:
    body = record.payload["set_indicator_checkpoint"]
    payload = dict(body["payload"])
    return SetIndicatorCheckpointRecord(
        checkpoint_id=str(body["checkpoint_id"]),
        indicator_type=str(body["indicator_type"]),
        payload=payload,
        payload_digest=canonical_json_digest(record.payload),
        inserted=inserted,
    )


def _validate_checkpoint_payload(*, indicator_type: str, payload: Mapping[str, Any]) -> None:
    required_common = {
        "numeric_policy_version",
        "source_manifest",
        "processed_source_ids",
        "work_value",
        "source_proof_digest",
        "checkpoint_digest_basis",
    }
    missing = required_common - set(payload)
    if missing:
        raise PostgresPersistenceError(f"set indicator checkpoint missing fields: {', '.join(sorted(missing))}")
    if payload["numeric_policy_version"] != "TT_SET_NUMERIC_V1":
        raise PostgresPersistenceError("set indicator checkpoint numeric_policy_version must be TT_SET_NUMERIC_V1")
    if not isinstance(payload["source_manifest"], Mapping) or not payload["source_manifest"]:
        raise PostgresPersistenceError("set indicator checkpoint source_manifest is required")
    required_manifest = {
        "series_id",
        "seed_anchor",
        "predecessor_close",
        "source_digest",
        "first_complete_history_evidence_ref",
    }
    missing_manifest = required_manifest - set(payload["source_manifest"])
    if missing_manifest:
        raise PostgresPersistenceError(f"set indicator checkpoint source_manifest missing fields: {', '.join(sorted(missing_manifest))}")
    for field in required_manifest:
        value = payload["source_manifest"][field]
        if not isinstance(value, str) or not value:
            raise PostgresPersistenceError(f"set indicator checkpoint source_manifest.{field} is required")
    if not isinstance(payload["processed_source_ids"], list) or not payload["processed_source_ids"]:
        raise PostgresPersistenceError("set indicator checkpoint processed_source_ids must be non-empty")
    for field in ("work_value", "source_proof_digest", "checkpoint_digest_basis"):
        value = payload[field]
        if not isinstance(value, str) or not value:
            raise PostgresPersistenceError(f"set indicator checkpoint {field} is required")
    try:
        work_value = parse_decimal_text(str(payload["work_value"]))
    except NumericPolicyError as exc:
        raise PostgresPersistenceError("set indicator checkpoint work_value must be a canonical decimal string") from exc
    if canonical_decimal_text(work_value) != payload["work_value"]:
        raise PostgresPersistenceError("set indicator checkpoint work_value must be a canonical decimal string")
    if indicator_type in {"ATR15", "ATR5", "LOCAL5"}:
        required_atr = {"seed_candle_ids", "true_ranges", "last_candle_id"}
        missing_atr = required_atr - set(payload)
        if missing_atr:
            raise PostgresPersistenceError(f"ATR checkpoint missing fields: {', '.join(sorted(missing_atr))}")
        seed_ids = _string_list(payload["seed_candle_ids"], field="seed_candle_ids")
        processed_ids = _string_list(payload["processed_source_ids"], field="processed_source_ids")
        if len(seed_ids) != 14:
            raise PostgresPersistenceError("ATR checkpoint seed_candle_ids must contain 14 source IDs")
        if len(set(seed_ids)) != len(seed_ids) or len(set(processed_ids)) != len(processed_ids):
            raise PostgresPersistenceError("ATR checkpoint source IDs must be unique")
        if processed_ids[:14] != seed_ids:
            raise PostgresPersistenceError("ATR checkpoint processed_source_ids must start with seed_candle_ids")
        last_candle_id = payload["last_candle_id"]
        if not isinstance(last_candle_id, str) or not last_candle_id:
            raise PostgresPersistenceError("ATR checkpoint last_candle_id is required")
        if last_candle_id != processed_ids[-1]:
            raise PostgresPersistenceError("ATR checkpoint last_candle_id must match the last processed source ID")
        true_ranges = _string_list(payload["true_ranges"], field="true_ranges")
        if len(true_ranges) != 14:
            raise PostgresPersistenceError("ATR checkpoint true_ranges must contain 14 values")
        for value in true_ranges:
            try:
                parsed = parse_decimal_text(value)
            except NumericPolicyError as exc:
                raise PostgresPersistenceError("ATR checkpoint true_ranges must be canonical decimal strings") from exc
            if parsed < 0:
                raise PostgresPersistenceError("ATR checkpoint true_ranges must be nonnegative")
            if canonical_decimal_text(parsed) != value:
                raise PostgresPersistenceError("ATR checkpoint true_ranges must be canonical decimal strings")
    _require_digest_like(payload["source_manifest"]["source_digest"], field="source_manifest.source_digest")
    _require_digest_like(payload["source_proof_digest"], field="source_proof_digest")


def _indicator_type(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PostgresPersistenceError("indicator_type is required")
    return value.upper()


def _string_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise PostgresPersistenceError(f"set indicator checkpoint {field} must be a non-empty list")
    if any(not isinstance(item, str) or not item for item in value):
        raise PostgresPersistenceError(f"set indicator checkpoint {field} must contain only non-empty strings")
    return list(value)


_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _require_digest_like(value: Any, *, field: str) -> None:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise PostgresPersistenceError(f"set indicator checkpoint {field} must be a lowercase sha256 digest")
