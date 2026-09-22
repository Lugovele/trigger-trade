"""Initial Position opportunity handler for v1.2.15 B7A."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping

from triggertrade.contracts import ContractError, TargetContract, parse_contract
from triggertrade.contracts.bindings import ContractBindingError, validate_contract_edge
from triggertrade.position_config_pins import PositionConfigPin, build_position_config_pin
from triggertrade.rules.trading import TradingRulesVersion, draft_to_json

from .formulas import PositionOpportunityError, PositionOpportunityEvaluation, evaluate_initial_position_opportunity


@dataclass(frozen=True)
class PositionOpportunityCommand:
    event_id: str
    position_decision_id: str
    occurred_at: str
    market_handoff: Mapping[str, Any]
    rules_version: TradingRulesVersion


@dataclass(frozen=True)
class PositionOpportunityResult:
    pin: PositionConfigPin
    market_handoff: TargetContract
    rules_version_payload: dict[str, Any]
    evaluation: PositionOpportunityEvaluation
    decision: TargetContract

    def to_state_payload(self) -> dict[str, Any]:
        market_handoff_payload = self.market_handoff.to_payload()
        return {
            "position_opportunity_state": {
                "state_version": 1,
                "pin": self.pin.to_payload()["position_config_pin"],
                "source_contracts": {
                    "market_handoff": market_handoff_payload,
                },
                "source_configuration": {
                    "rules_version_id": self.pin.configuration_id,
                    "version": self.pin.configuration_version,
                    "content_digest": self.pin.configuration_content_digest,
                    "rules_version": dict(self.rules_version_payload),
                },
                "evaluation": self.evaluation.to_payload()["position_opportunity"],
                "decision": self.decision.to_payload()["position_decision"],
            }
        }


class PositionOpportunityHandler:
    """Pure B7A handler for one initial Position opportunity."""

    def evaluate(self, command: PositionOpportunityCommand) -> PositionOpportunityResult:
        try:
            market_handoff = validate_contract_edge(
                producer="Set",
                consumer="Position",
                contract_type="MARKET_HANDOFF",
                payload=command.market_handoff,
                definition="MARKET_HANDOFF",
            )
        except (ContractError, ContractBindingError) as exc:
            raise PositionOpportunityError(str(exc)) from exc
        market_handoff_payload = market_handoff.to_payload()
        pin = build_position_config_pin(
            position_decision_id=command.position_decision_id,
            market_handoff=market_handoff_payload,
            rules_version=command.rules_version,
            pinned_at=command.occurred_at,
        )
        evaluation = evaluate_initial_position_opportunity(
            position_decision_id=command.position_decision_id,
            market_handoff=market_handoff_payload,
            rules_version=command.rules_version,
        )
        decision = build_initial_position_decision(
            event_id=command.event_id,
            occurred_at=command.occurred_at,
            evaluation=evaluation,
        )
        return PositionOpportunityResult(
            pin=pin,
            market_handoff=market_handoff,
            rules_version_payload=_rules_version_payload(command.rules_version),
            evaluation=evaluation,
            decision=decision,
        )


def build_initial_position_decision(
    *,
    event_id: str,
    occurred_at: str,
    evaluation: PositionOpportunityEvaluation,
) -> TargetContract:
    """Build and validate the initial APPROVE_REJECT v5 opportunity decision."""

    payload = {
        "position_decision": {
            "contract_version": 5,
            "event_variant": "OPPORTUNITY_DECISION",
            "event_id": _text(event_id, field="event_id"),
            "occurred_at": _text(occurred_at, field="occurred_at"),
            "position_decision_id": evaluation.position_decision_id,
            "decision_cycle_id": evaluation.decision_cycle_id,
            "set_result_id": evaluation.set_result_id,
            "symbol": evaluation.symbol,
            "decision": evaluation.decision,
            "reason_code": evaluation.reason_code,
            "opportunity_checks": dict(evaluation.opportunity_checks),
            "construction_gates": "NOT_YET_EVALUATED",
        }
    }
    try:
        parsed = parse_contract("APPROVE_REJECT", payload, definition="APPROVE_REJECT.initial")
        return validate_contract_edge(
            producer="Position",
            consumer="Portfolio",
            contract_type="APPROVE_REJECT",
            payload=parsed.to_payload(),
            definition="APPROVE_REJECT.initial",
        )
    except (ContractError, ContractBindingError) as exc:
        raise PositionOpportunityError(str(exc)) from exc


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PositionOpportunityError(f"{field} is required")
    return value


def _rules_version_payload(rules_version: TradingRulesVersion) -> dict[str, Any]:
    return {
        "rules_version_id": rules_version.rules_version_id,
        "version": rules_version.version,
        "created_at": rules_version.created_at,
        "created_from_version_id": rules_version.created_from_version_id,
        "created_source": rules_version.created_source,
        "change_summary": rules_version.change_summary,
        "config_hash": rules_version.config_hash,
        "schema_version": rules_version.schema_version,
        "is_current": rules_version.is_current,
        "draft": json.loads(draft_to_json(rules_version.draft)),
    }
