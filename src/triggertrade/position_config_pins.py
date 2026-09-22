"""Position-owned immutable configuration pins."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.contracts import ContractError
from triggertrade.contracts.bindings import ContractBindingError, validate_contract_edge
from triggertrade.rules.trading import TradingRulesVersion, draft_to_json


class PositionConfigPinError(ValueError):
    """Raised when a Position configuration pin cannot be represented."""


@dataclass(frozen=True)
class PositionConfigPin:
    position_decision_id: str
    decision_cycle_id: str
    set_result_id: str
    symbol: str
    market_handoff_digest: str
    configuration_id: str
    configuration_version: str
    configuration_content_digest: str
    pinned_at: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "position_decision_id", _text(self.position_decision_id, field="position_decision_id"))
        object.__setattr__(self, "decision_cycle_id", _text(self.decision_cycle_id, field="decision_cycle_id"))
        object.__setattr__(self, "set_result_id", _text(self.set_result_id, field="set_result_id"))
        object.__setattr__(self, "symbol", _text(self.symbol, field="symbol").upper())
        object.__setattr__(self, "market_handoff_digest", _digest(self.market_handoff_digest, field="market_handoff_digest"))
        object.__setattr__(self, "configuration_id", _text(self.configuration_id, field="configuration_id"))
        object.__setattr__(self, "configuration_version", _text(self.configuration_version, field="configuration_version"))
        object.__setattr__(self, "configuration_content_digest", _digest(self.configuration_content_digest, field="configuration_content_digest"))
        object.__setattr__(self, "pinned_at", _text(self.pinned_at, field="pinned_at"))

    def to_payload(self) -> dict[str, Any]:
        return {
            "position_config_pin": {
                "pin_version": 1,
                "position_decision_id": self.position_decision_id,
                "decision_cycle_id": self.decision_cycle_id,
                "set_result_id": self.set_result_id,
                "symbol": self.symbol,
                "market_handoff_digest": self.market_handoff_digest,
                "configuration_id": self.configuration_id,
                "configuration_version": self.configuration_version,
                "configuration_content_digest": self.configuration_content_digest,
                "pinned_at": self.pinned_at,
            }
        }


def build_position_config_pin(
    *,
    position_decision_id: str,
    market_handoff: Mapping[str, Any],
    rules_version: TradingRulesVersion,
    pinned_at: str,
) -> PositionConfigPin:
    """Bind the current Position configuration before opportunity evaluation.

    The caller supplies the selected governed rules version. This function
    validates and binds identities only; it does not calculate Position gates.
    """

    try:
        parsed_handoff = validate_contract_edge(
            producer="Set",
            consumer="Position",
            contract_type="MARKET_HANDOFF",
            payload=market_handoff,
            definition="MARKET_HANDOFF",
        )
    except (ContractError, ContractBindingError) as exc:
        raise PositionConfigPinError(str(exc)) from exc
    handoff_payload = parsed_handoff.to_payload()
    body = handoff_payload["market_handoff"]
    return PositionConfigPin(
        position_decision_id=position_decision_id,
        decision_cycle_id=body["decision_cycle_id"],
        set_result_id=body["set_result_id"],
        symbol=body["symbol"],
        market_handoff_digest=canonical_json_digest(handoff_payload),
        configuration_id=rules_version.rules_version_id,
        configuration_version=rules_version.version,
        configuration_content_digest=position_rules_content_digest(rules_version),
        pinned_at=pinned_at,
    )


def position_config_pin_digest(pin: PositionConfigPin) -> str:
    return canonical_json_digest(pin.to_payload())


def position_rules_content_digest(rules_version: TradingRulesVersion) -> str:
    payload = {
        "position_rules_configuration": json.loads(draft_to_json(rules_version.draft)),
        "schema_version": rules_version.schema_version,
    }
    return canonical_json_digest(payload)


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PositionConfigPinError(f"{field} is required")
    return value


def _digest(value: object, *, field: str) -> str:
    text = _text(value, field=field)
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise PositionConfigPinError(f"{field} must be a sha256 hex digest")
    return text
