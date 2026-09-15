"""Immutable Research run pin payloads and canonical digests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from triggertrade.canonical_json import CanonicalJsonError, canonical_json_digest, canonical_json_text
from triggertrade.contracts import APPROVED_PACKAGE_REVISION, implemented_contract_registry


RESEARCH_PIN_SCHEMA_VERSION = "research-run-pins-v1"
TARGET_MODEL_VERSION = "backend-target-model-v1"
NUMERIC_POLICY_IDS = ("TT_NUMERIC_V1", "TT_SET_NUMERIC_V1")


class ResearchPinError(ValueError):
    pass


def research_pin_payload(
    *,
    config_pins: Mapping[str, Any],
    created_source: str,
    source_pins: Mapping[str, Any] | None = None,
    adapter_profile_pins: Mapping[str, Any] | None = None,
    simulation_assumptions: Mapping[str, Any] | None = None,
    contract_versions: Mapping[str, Any] | None = None,
    target_version: str = TARGET_MODEL_VERSION,
    methodology_package_revision: str = APPROVED_PACKAGE_REVISION,
    numeric_policy_ids: Sequence[str] = NUMERIC_POLICY_IDS,
) -> dict[str, Any]:
    payload = {
        "pin_schema_version": RESEARCH_PIN_SCHEMA_VERSION,
        "target_version": _required_text(target_version, "target_version"),
        "methodology_package_revision": _required_text(methodology_package_revision, "methodology_package_revision"),
        "contract_versions": _json_value(contract_versions if contract_versions is not None else implemented_contract_registry()),
        "numeric_policy_ids": tuple(_required_text(item, "numeric_policy_id") for item in numeric_policy_ids),
        "config_pins": _json_value(config_pins),
        "source_pins": _json_value(source_pins or {}),
        "adapter_profile_pins": _json_value(adapter_profile_pins or {}),
        "simulation_assumptions": _json_value(simulation_assumptions or {}),
        "created_source": _required_text(created_source, "created_source"),
    }
    research_pin_digest(payload)
    return payload


def research_run_pin_payload(
    *,
    research_pin_digest_value: str,
    run_kind: str,
    run_inputs: Mapping[str, Any],
    execution_pins: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "pin_schema_version": RESEARCH_PIN_SCHEMA_VERSION,
        "parent_research_pin_digest": _required_text(research_pin_digest_value, "research_pin_digest"),
        "run_kind": _required_text(run_kind, "run_kind"),
        "run_inputs": _json_value(run_inputs),
        "execution_pins": _json_value(execution_pins or {}),
    }
    research_pin_digest(payload)
    return payload


def research_pin_digest(payload: Mapping[str, Any]) -> str:
    try:
        return canonical_json_digest(_json_value(payload))
    except CanonicalJsonError as exc:
        raise ResearchPinError(str(exc)) from exc


def research_pin_text(payload: Mapping[str, Any]) -> str:
    try:
        return canonical_json_text(_json_value(payload))
    except CanonicalJsonError as exc:
        raise ResearchPinError(str(exc)) from exc


def default_store_research_pin_payload(
    *,
    set_id: str,
    set_version: str,
    rules_version_id: str,
    rules_display_version: str,
    created_source: str,
    schema_version: str,
) -> dict[str, Any]:
    return research_pin_payload(
        config_pins={
            "trigger_set": {"set_id": set_id, "set_version": set_version},
            "trading_rules": {
                "rules_version_id": rules_version_id,
                "display_version": rules_display_version,
            },
            "research_store": {"schema_version": schema_version},
        },
        created_source=created_source,
    )


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ResearchPinError(f"{field} is required")
    return " ".join(value.replace("\x00", "").split())


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, float):
        raise ResearchPinError("binary floats are not supported in research pins")
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    raise ResearchPinError(f"unsupported research pin value type: {type(value).__name__}")
