"""Research V2 canonical MARKET_HANDOFF bridge.

The bridge starts from a resolved Research V2 Set result and explicit factual
handoff facts, then delegates the MARKET_HANDOFF payload construction to the
generic Set engine. It does not construct Position, Portfolio, Order, or
lifecycle results.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.research_v2 import ResearchV2SetResolution, V2Direction
from triggertrade.set_engine import (
    Direction,
    DirectionResolutionScope,
    GenericFixedDirectionBinding,
    HandoffFacts,
    SetHandlerError,
    SetResolutionRequest,
    TriggerResult,
    build_validated_market_handoff_payload,
    generic_fixed_direction_binding_digest,
)
from triggertrade.set_scope import SetFormationEpoch


@dataclass(frozen=True)
class ResearchV2MarketHandoff:
    job_id: str
    signal_episode_id: str
    symbol: str
    decision_cycle_id: str
    set_result_id: str
    facts: HandoffFacts
    payload: Mapping[str, Any]
    evidence_digest: str
    evidence_id: str


def produce_research_v2_market_handoff(
    *,
    resolution: ResearchV2SetResolution,
    facts: HandoffFacts,
) -> ResearchV2MarketHandoff:
    """Build a canonical Set -> Position MARKET_HANDOFF for a V2 Set result."""

    if resolution.status != "MATCHED":
        raise SetHandlerError("Research V2 MARKET_HANDOFF requires a MATCHED Set resolution")
    if resolution.decision_cycle_id is None:
        raise SetHandlerError("Research V2 MATCHED Set resolution requires decision_cycle_id")
    if resolution.direction not in {V2Direction.LONG, V2Direction.SHORT}:
        raise SetHandlerError("Research V2 MARKET_HANDOFF requires LONG or SHORT direction")
    if facts.symbol.upper() != resolution.symbol.upper():
        raise SetHandlerError("Research V2 MARKET_HANDOFF facts symbol must match Set resolution")

    direction = Direction.LONG if resolution.direction is V2Direction.LONG else Direction.SHORT
    binding = GenericFixedDirectionBinding(
        fixed_direction=direction,
        binding_digest=generic_fixed_direction_binding_digest(
            configuration_binding_digest=resolution.configuration_binding.digest,
            fixed_direction=direction,
        ),
    )
    request = SetResolutionRequest(
        formation_epoch=SetFormationEpoch(
            symbol=resolution.symbol,
            formation_epoch=_epoch_seconds(resolution.observed_at),
            open_event_id=resolution.signal_episode_id,
            opened_at=resolution.observed_at,
            open_payload_digest=resolution.source_evidence_digest,
            configuration_binding=resolution.configuration_binding,
        ),
        direction_scope=DirectionResolutionScope.GENERIC_FIXED,
        formation_result=TriggerResult.TRUE,
        evaluation_event_ids=(resolution.signal_episode_id,),
        source_evidence_digest=resolution.source_evidence_digest,
        handoff_facts=facts,
        fixed_direction_binding=binding,
        frozen_condition={
            "producer": "RESEARCH_V2_SIGNAL",
            "signal_episode_id": resolution.signal_episode_id,
            "observed_at": resolution.observed_at,
            "set_result_id": resolution.set_result_id,
        },
    )
    payload = build_validated_market_handoff_payload(
        request=request,
        direction=direction,
        decision_cycle_id=resolution.decision_cycle_id,
        set_result_id=resolution.set_result_id,
    )
    evidence_digest = canonical_json_digest(
        {
            "producer": "RESEARCH_V2_MARKET_HANDOFF_V1",
            "set_result_id": resolution.set_result_id,
            "decision_cycle_id": resolution.decision_cycle_id,
            "facts": _handoff_fact_digest_basis(facts),
        }
    )
    return ResearchV2MarketHandoff(
        job_id=resolution.job_id,
        signal_episode_id=resolution.signal_episode_id,
        symbol=resolution.symbol,
        decision_cycle_id=resolution.decision_cycle_id,
        set_result_id=resolution.set_result_id,
        facts=facts,
        payload=payload,
        evidence_digest=evidence_digest,
        evidence_id=f"research-v2-market-handoff-{evidence_digest[:32]}",
    )


def _epoch_seconds(value: str) -> int:
    from datetime import datetime

    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def _handoff_fact_digest_basis(facts: HandoffFacts) -> dict[str, Any]:
    return {
        "symbol": facts.symbol.upper(),
        "created_at": facts.created_at,
        "matched_at": facts.matched_at,
        "market_snapshot_at": facts.market_snapshot_at,
        "market_snapshot_id": facts.market_snapshot_id,
        "set_match_reference_price": facts.set_match_reference_price,
        "reference_price_observed_at": facts.reference_price_observed_at,
        "reference_price_source": facts.reference_price_source,
        "tick_size": facts.tick_size,
        "metadata_revision": facts.metadata_revision,
        "metadata_as_of": facts.metadata_as_of,
        "atr_15m": facts.atr_15m,
        "atr_pct_15m": facts.atr_pct_15m,
        "reference_levels": [level.to_payload() for level in facts.reference_levels],
        "core_set_id": facts.core_set_id,
        "set_family": facts.set_family,
    }
