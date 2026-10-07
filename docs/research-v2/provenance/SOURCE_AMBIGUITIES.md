# Source Ambiguities

Status: **IMPLEMENTATION_MAPPING_PENDING**. Ambiguities are preserved rather than guessed.

## AMB-001 RET5/RET15 backend mapping

- Status: IMPLEMENTATION_MAPPING_PENDING
- Detail: Sources define threshold logic and reset semantics but do not identify final native backend formula/config field names.
- Sources: candidates_12.json, TriggerTrade_Research_V2_Economic_Redesign_RU.md

## AMB-002 G0/G1 native config fields

- Status: IMPLEMENTATION_MAPPING_PENDING
- Detail: Sources define stop geometry values but not the final repository-native config field mapping.
- Sources: common_profile.json, candidates_12.json

## AMB-003 TTL lifecycle contract field

- Status: IMPLEMENTATION_MAPPING_PENDING
- Detail: Sources require TTL=15m and terminal cancellation semantics; exact lifecycle field/wire mapping remains pending.
- Sources: common_profile.json, candidates_12.json

## AMB-004 Historical mark-price source

- Status: IMPLEMENTATION_MAPPING_PENDING
- Detail: Sources require end-window mark valuation and leverage margin/liquidation readiness but do not provide a concrete historical mark-price adapter path.
- Sources: common_profile.json, TriggerTrade_Research_V2_Economic_Redesign_RU.md

## AMB-005 Historical funding source adapter path

- Status: IMPLEMENTATION_MAPPING_PENDING
- Detail: Sources require factual funding; latest implementation report says a funding-facts path exists, but source package does not specify the repository adapter/file path for sourcing those facts.
- Sources: common_profile.json, TriggerTrade_Research_V2_Economic_Redesign_RU.md

## AMB-006 V2 daily-loss native representation

- Status: IMPLEMENTATION_MAPPING_PENDING
- Detail: Sources define daily-loss basis and missing-data semantics; final native representation for V2 campaign configs is not specified.
- Sources: common_profile.json, TriggerTrade_Research_V2_Economic_Redesign_RU.md

## AMB-007 Risk-based sizing implementation mapping

- Status: IMPLEMENTATION_MAPPING_PENDING
- Detail: Sources give sizing formula and caps; exact canonical sizing component split remains pending.
- Sources: common_profile.json, candidates_12.json

## AMB-008 Numeric config equivalence

- Status: IMPLEMENTATION_MAPPING_PENDING
- Detail: Evidence says some config IDs share exported numeric drafts while metadata differs; do not collapse them without operational fingerprints and discriminator fixtures.
- Sources: TriggerTrade_Research_V2_Economic_Redesign_RU.md, witnesses.json
