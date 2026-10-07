# Research V2 Canonical Set Contract

Status: IMPLEMENTED_FOR_J0_J7_BRIDGE

Research V2 signal episodes enter the existing trading pipeline through the
generic Set engine contract, not through synthetic Research V1 Set versions.

Pipeline boundary:

`Research V2 signal episode -> ResearchV2SetResolution -> MARKET_HANDOFF -> Position -> Portfolio -> Order Spec -> BACKTEST lifecycle`

## Canonical Interface

The repository-native Set interface is the existing generic Set engine:

- `SetConfigurationBinding`
- `SetFormationEpoch`
- `SetResultResolutionRequest`
- `SetResolutionRequest`
- `SetResolutionRecord`
- `build_validated_market_handoff_payload`

Research V2 adds `ResearchV2SetResolution` as the immutable V2 adapter record.
It preserves:

- `job_id`
- `signal_family`
- `signal_episode_id`
- logical `symbol`
- `physical_symbol`
- `observed_at`
- Set-owned `direction`
- Set `status`
- signal/set `config_fingerprint`
- job execution `job_config_fingerprint`
- source feature evidence and digest
- canonical `decision_cycle_id`
- canonical `set_result_id`
- Set configuration binding

## Identity Derivation

V2 Set identity is derived from immutable Set-owned inputs only:

- signal family/version
- logical/physical symbol
- decision time
- V2 signal status/direction/reason
- causal feature evidence
- signal/set configuration fingerprint

Execution-only fields such as stop family, sizing profile, TTL, and take-profit
configuration are excluded from V2 Set identity.

This is why J4 and J7 share a Set identity for identical market facts: their
signal logic is identical and they differ only by downstream stop family.

## MARKET_HANDOFF Boundary

`produce_research_v2_market_handoff` accepts a matched
`ResearchV2SetResolution` plus explicit factual `HandoffFacts`, then delegates
payload construction and validation to the generic Set engine.

Position, Portfolio, Order Spec, and lifecycle code consume the same validated
`MARKET_HANDOFF` shape used by legacy Set producers.

## Backward Compatibility

Legacy J0/J1/J2 may keep using existing legacy Set resolution where appropriate.
The downstream boundary is shared because both legacy and V2 producers emit the
same canonical Set-owned `MARKET_HANDOFF`.
