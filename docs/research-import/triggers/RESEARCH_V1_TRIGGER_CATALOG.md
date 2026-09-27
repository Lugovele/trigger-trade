# Research V1 Trigger Catalog

Package revision: `RESEARCH_V1_FOCUSED_CORRECTION_R3`

This catalog extracts the operative trigger predicates referenced by the current Research V1 R3 final program. It preserves Research-source semantics and does not create executable backend trigger logic.

## Authority

- `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md`
- `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/RESEARCH_HYPOTHESES_COVERAGE_MATRIX.md`
- `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/RESEARCH_HYPOTHESES_FINAL_30.md`
- `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md`
- `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/validation/R3_PACKAGE_VALIDATION.json`
- `docs/trading-methodology/` and `docs/formula-certification/FINAL_FORMULA_SPECIFICATION/` for referenced formula/state-rule contracts

## Current Trigger Import Contract

No public Research trigger import endpoint was found. The existing loadable backend representation is the `RuleDefinition`/`TriggerVersion` registry contract.

Required fields: `rule_id`, `version`, `name`, `status`, `asset_scope`, `rule_type`, `condition`, `definition`, `created_at`, `provenance`
Optional fields: `updated_at`, `logical_name`, `description`, `supersedes_version`, `formula`, `parameter_snapshot`, `input_contract`, `output_contract`, `boundary_semantics`, `stale_data_semantics`, `missing_data_semantics`, `semantic_hash`, `change_summary`
Validation rules:
- Trigger versions must use semantic versioning.
- Trigger versions require implementation_key.
- condition is required.
- Current selectable triggers are hard-coded separately as TRG-001@0.2.0.

## Summary Counts

- `registry_trigger_definitions_total`: 39
- `operative_research_triggers`: 31
- `trigger_versions`: 31
- `final_hypotheses_count`: 30
- `final_hypotheses_covered`: 30
- `source_set_versions_count`: 33
- `btc_specific_triggers`: 8
- `triggers_with_coin_exclusions`: 6
- `unresolved_import_issues`: 31
- `unused_reserve_trigger_definitions`: TR-R-020, TR-R-021, TR-R-024, TR-R-025, TR-R-026, TR-R-027, TR-R-028, TR-R-031

## Operative Trigger Definitions

### TR-R-001 - F-001 trigger_result = TRUE

- Identity: `TR-R-001` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `SET_FORMATION_PREDICATE` / `price_displacement`
- Definition: Research predicate over F-001 trigger_result: F-001 trigger_result = TRUE.
- Operator/threshold: `EQ` / `TRUE` / unit `tri-state; none`
- Timeframe/context: Current completed 1m slot ending at completed-5m Set cutoff
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics F-001 trigger_result; formula refs F-001
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-001, R-002, R-003, R-004, R-005, R-006, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030; candidates C-001, C-003, C-007, C-008, C-009, C-010, C-011, C-012, C-015, C-016, C-019, C-020, C-021, C-031, C-032, C-034, C-035, C-036, C-037, C-039, C-040, C-041, C-042, C-043, C-051, C-052, C-054, C-055, C-059, C-060
- Set usage: SET-R-001-V1, SET-R-003-V2, SET-R-007-V2, SET-R-008-V2, SET-R-009-V2, SET-R-010-V2, SET-R-011-V2, SET-R-012-V2, SET-R-015-V2, SET-R-016-V2, SET-R-019-V1, SET-R-019-V2, SET-R-020-V1, SET-R-020-V2, SET-R-021-V1, SET-R-021-V2, SET-R-BTC-001-V1, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 217; metric source `methodology/SET.md Part I §8A L617–843`

### TR-R-002 - F-001 trigger_result = TRUE

- Identity: `TR-R-002` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `SET_FORMATION_PREDICATE` / `price_displacement`
- Definition: Research predicate over F-001 trigger_result: F-001 trigger_result = TRUE.
- Operator/threshold: `EQ` / `TRUE` / unit `tri-state; none`
- Timeframe/context: Current completed 1m slot ending at completed-5m Set cutoff
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics F-001 trigger_result; formula refs F-001
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-001, R-030; candidates C-001, C-060
- Set usage: SET-R-001-V2, SET-R-BTC-001-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 238; metric source `methodology/SET.md Part I §8A L617–843`

### TR-R-003 - F-002 trigger_result = TRUE

- Identity: `TR-R-003` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `SET_FORMATION_PREDICATE` / `participation_activity`
- Definition: Research predicate over F-002 trigger_result: F-002 trigger_result = TRUE.
- Operator/threshold: `EQ` / `TRUE` / unit `tri-state; none`
- Timeframe/context: Current completed 1m slot; 60 preceding consecutive 1m base-volume candles
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics F-002 trigger_result; formula refs F-002
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-002, R-009, R-010, R-011, R-029; candidates C-003, C-019, C-020, C-021, C-059
- Set usage: SET-R-003-V2, SET-R-019-V1, SET-R-019-V2, SET-R-020-V1, SET-R-020-V2, SET-R-021-V1, SET-R-021-V2, SET-R-BTC-003-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 259; metric source `methodology/SET.md Part I §8B L847–1078`

### TR-R-004 - classifier_direction = LONG

- Identity: `TR-R-004` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `DIRECTION_PREDICATE` / `direction`
- Definition: Research predicate over classifier_direction: classifier_direction = LONG.
- Operator/threshold: `EQ` / `LONG` / unit `enum LONG / SHORT / NONE; none`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE, LONG; direction applicability `LONG`
- Dependencies: metrics classifier_direction; formula refs F-005
- Applicability: coins ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded BTC
- Research usage: hypotheses R-001, R-002, R-003, R-004, R-005, R-006, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030; candidates C-001, C-003, C-007, C-008, C-009, C-010, C-011, C-012, C-015, C-016, C-019, C-020, C-021, C-031, C-032, C-034, C-035, C-036, C-037, C-039, C-040, C-041, C-042, C-043, C-051, C-052, C-054, C-055, C-059, C-060
- Set usage: SET-R-001-V1, SET-R-001-V2, SET-R-003-V2, SET-R-007-V2, SET-R-008-V2, SET-R-009-V2, SET-R-010-V2, SET-R-011-V2, SET-R-012-V2, SET-R-015-V2, SET-R-016-V2, SET-R-019-V1, SET-R-019-V2, SET-R-020-V1, SET-R-020-V2, SET-R-021-V1, SET-R-021-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 282; metric source `methodology/SET.md Part II §§34A–37 L3155–3435; methodology/SET.md Part I §5 L509–530`

### TR-R-005 - classifier_direction = SHORT

- Identity: `TR-R-005` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `DIRECTION_PREDICATE` / `direction`
- Definition: Research predicate over classifier_direction: classifier_direction = SHORT.
- Operator/threshold: `EQ` / `SHORT` / unit `enum LONG / SHORT / NONE; none`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE, SHORT; direction applicability `SHORT`
- Dependencies: metrics classifier_direction; formula refs F-005
- Applicability: coins ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded BTC
- Research usage: hypotheses R-001, R-002, R-003, R-004, R-005, R-006, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030; candidates C-001, C-003, C-007, C-008, C-009, C-010, C-011, C-012, C-015, C-016, C-019, C-020, C-021, C-031, C-032, C-034, C-035, C-036, C-037, C-039, C-040, C-041, C-042, C-043, C-051, C-052, C-054, C-055, C-059, C-060
- Set usage: SET-R-001-V1, SET-R-001-V2, SET-R-003-V2, SET-R-007-V2, SET-R-008-V2, SET-R-009-V2, SET-R-010-V2, SET-R-011-V2, SET-R-012-V2, SET-R-015-V2, SET-R-016-V2, SET-R-019-V1, SET-R-019-V2, SET-R-020-V1, SET-R-020-V2, SET-R-021-V1, SET-R-021-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 304; metric source `methodology/SET.md Part II §§34A–37 L3155–3435; methodology/SET.md Part I §5 L509–530`

### TR-R-006 - DE >= 0.50

- Identity: `TR-R-006` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `SET_FORMATION_PREDICATE` / `directional_efficiency`
- Definition: Research predicate over DE: DE >= 0.50.
- Operator/threshold: `GTE` / `0.50` / unit `numeric 0..1; dimensionless`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics DE; formula refs source methodology sections only
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-003; candidates C-007
- Set usage: SET-R-007-V2, SET-R-BTC-007-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 326; metric source `methodology/SET.md Part II §§11–12 L2317–2405`

### TR-R-007 - ATR percentile >= 30

- Identity: `TR-R-007` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `SET_FORMATION_PREDICATE` / `volatility`
- Definition: Research predicate over ATR percentile: ATR percentile >= 30.
- Operator/threshold: `GTE` / `30` / unit `numeric 0..100; percentile rank`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics ATR percentile; formula refs F-003
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-004; candidates C-008
- Set usage: SET-R-008-V2, SET-R-BTC-008-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 348; metric source `methodology/SET.md Part II §§13–15 L2410–2508; methodology/SET.md Part II §§3–6 L1739–1961`

### TR-R-008 - ATR percentile <= 85

- Identity: `TR-R-008` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `SET_FORMATION_PREDICATE` / `volatility`
- Definition: Research predicate over ATR percentile: ATR percentile <= 85.
- Operator/threshold: `LTE` / `85` / unit `numeric 0..100; percentile rank`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics ATR percentile; formula refs F-003
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-004; candidates C-008
- Set usage: SET-R-008-V2, SET-R-BTC-008-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 370; metric source `methodology/SET.md Part II §§13–15 L2410–2508; methodology/SET.md Part II §§3–6 L1739–1961`

### TR-R-009 - SWING_SEQUENCE_STATE(asset,1h) = BULLISH

- Identity: `TR-R-009` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `CONTEXTUAL_AGREEMENT_PREDICATE` / `structure`
- Definition: Research predicate over SWING_SEQUENCE_STATE(asset,1h): SWING_SEQUENCE_STATE(asset,1h) = BULLISH.
- Operator/threshold: `EQ` / `BULLISH` / unit `enum BULLISH / BEARISH / AMBIGUOUS / UNAVAILABLE; none`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG`
- Dependencies: metrics SWING_SEQUENCE_STATE(asset,1h); formula refs source methodology sections only
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-005; candidates C-009
- Set usage: SET-R-009-V2, SET-R-BTC-009-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 392; metric source `methodology/SET.md Part II §§9–10 L2136–2313`

### TR-R-010 - SWING_SEQUENCE_STATE(asset,1h) = BEARISH

- Identity: `TR-R-010` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `CONTEXTUAL_AGREEMENT_PREDICATE` / `structure`
- Definition: Research predicate over SWING_SEQUENCE_STATE(asset,1h): SWING_SEQUENCE_STATE(asset,1h) = BEARISH.
- Operator/threshold: `EQ` / `BEARISH` / unit `enum BULLISH / BEARISH / AMBIGUOUS / UNAVAILABLE; none`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `SHORT`
- Dependencies: metrics SWING_SEQUENCE_STATE(asset,1h); formula refs source methodology sections only
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-005; candidates C-009
- Set usage: SET-R-009-V2, SET-R-BTC-009-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 414; metric source `methodology/SET.md Part II §§9–10 L2136–2313`

### TR-R-011 - RELATIVE_RETURN_15m >= 0

- Identity: `TR-R-011` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `CONTEXTUAL_AGREEMENT_PREDICATE` / `context_momentum`
- Definition: Research predicate over RELATIVE_RETURN_15m: RELATIVE_RETURN_15m >= 0.
- Operator/threshold: `GTE` / `0` / unit `signed decimal; fractional return / z / bounded score, respectively`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG`
- Dependencies: metrics RELATIVE_RETURN_15m; formula refs source methodology sections only
- Applicability: coins ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded BTC
- Research usage: hypotheses R-006; candidates C-010
- Set usage: SET-R-010-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 436; metric source `methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§3–6 L1739–1961`

### TR-R-012 - RELATIVE_RETURN_15m <= 0

- Identity: `TR-R-012` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `CONTEXTUAL_AGREEMENT_PREDICATE` / `context_momentum`
- Definition: Research predicate over RELATIVE_RETURN_15m: RELATIVE_RETURN_15m <= 0.
- Operator/threshold: `LTE` / `0` / unit `signed decimal; fractional return / z / bounded score, respectively`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `SHORT`
- Dependencies: metrics RELATIVE_RETURN_15m; formula refs source methodology sections only
- Applicability: coins ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded BTC
- Research usage: hypotheses R-006; candidates C-010
- Set usage: SET-R-010-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 458; metric source `methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§3–6 L1739–1961`

### TR-R-013 - AGGRESSIVE_VOLUME_DELTA_PCT >= 0

- Identity: `TR-R-013` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `CONTEXTUAL_AGREEMENT_PREDICATE` / `flow`
- Definition: Research predicate over AGGRESSIVE_VOLUME_DELTA_PCT: AGGRESSIVE_VOLUME_DELTA_PCT >= 0.
- Operator/threshold: `GTE` / `0` / unit `decimal; percent`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG`
- Dependencies: metrics AGGRESSIVE_VOLUME_DELTA_PCT; formula refs source methodology sections only
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-007; candidates C-011
- Set usage: SET-R-011-V2, SET-R-BTC-011-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 480; metric source `methodology/SET.md Part II §§21–23 L2760–2858; api-contracts/MARKET_DATA_REQUEST.md §§1–6 L6–46`

### TR-R-014 - AGGRESSIVE_VOLUME_DELTA_PCT <= 0

- Identity: `TR-R-014` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `CONTEXTUAL_AGREEMENT_PREDICATE` / `flow`
- Definition: Research predicate over AGGRESSIVE_VOLUME_DELTA_PCT: AGGRESSIVE_VOLUME_DELTA_PCT <= 0.
- Operator/threshold: `LTE` / `0` / unit `decimal; percent`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `SHORT`
- Dependencies: metrics AGGRESSIVE_VOLUME_DELTA_PCT; formula refs source methodology sections only
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-007; candidates C-011
- Set usage: SET-R-011-V2, SET-R-BTC-011-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 502; metric source `methodology/SET.md Part II §§21–23 L2760–2858; api-contracts/MARKET_DATA_REQUEST.md §§1–6 L6–46`

### TR-R-015 - classifier_direction = LONG

- Identity: `TR-R-015` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `DIRECTION_PREDICATE` / `direction`
- Definition: Research predicate over classifier_direction: classifier_direction = LONG.
- Operator/threshold: `EQ` / `LONG` / unit `enum LONG / SHORT / NONE; none`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE, LONG; direction applicability `LONG`
- Dependencies: metrics classifier_direction; formula refs F-005
- Applicability: coins ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded BTC
- Research usage: hypotheses R-008; candidates C-016
- Set usage: SET-R-016-V2
- Edge behavior: FRESH_EVENT: same-epoch uninterrupted FALSE -> TRUE of the direction-equality predicate; initial TRUE and UNAVAILABLE -> TRUE do not qualify; max_age=0 at formation use; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 524; metric source `methodology/SET.md Part II §§34A–37 L3155–3435; methodology/SET.md Part I §5 L509–530`

### TR-R-016 - classifier_direction = SHORT

- Identity: `TR-R-016` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `DIRECTION_PREDICATE` / `direction`
- Definition: Research predicate over classifier_direction: classifier_direction = SHORT.
- Operator/threshold: `EQ` / `SHORT` / unit `enum LONG / SHORT / NONE; none`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE, SHORT; direction applicability `SHORT`
- Dependencies: metrics classifier_direction; formula refs F-005
- Applicability: coins ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded BTC
- Research usage: hypotheses R-008; candidates C-016
- Set usage: SET-R-016-V2
- Edge behavior: FRESH_EVENT: same-epoch uninterrupted FALSE -> TRUE of the direction-equality predicate; initial TRUE and UNAVAILABLE -> TRUE do not qualify; max_age=0 at formation use; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 550; metric source `methodology/SET.md Part II §§34A–37 L3155–3435; methodology/SET.md Part I §5 L509–530`

### TR-R-017 - TOD_REL_TURNOVER >= 1.00

- Identity: `TR-R-017` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `SET_FORMATION_PREDICATE` / `participation_activity`
- Definition: Research predicate over TOD_REL_TURNOVER: TOD_REL_TURNOVER >= 1.00.
- Operator/threshold: `GTE` / `1.00` / unit `nonnegative numeric; ratio`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics TOD_REL_TURNOVER; formula refs source methodology sections only
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-011; candidates C-021
- Set usage: SET-R-021-V1, SET-R-021-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 576; metric source `methodology/SET.md Part II §8 L2013–2131; methodology/SET.md Part II §§21–23 L2760–2858`

### TR-R-018 - BTC_CONTEXT_SCORE >= 0

- Identity: `TR-R-018` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `CONTEXTUAL_AGREEMENT_PREDICATE` / `context_momentum`
- Definition: Research predicate over BTC_CONTEXT_SCORE: BTC_CONTEXT_SCORE >= 0.
- Operator/threshold: `GTE` / `0` / unit `numeric; z-score for BTC_RETURN_Z; otherwise bounded score`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG`
- Dependencies: metrics BTC_CONTEXT_SCORE; formula refs source methodology sections only
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-022; candidates C-012
- Set usage: SET-R-012-V2, SET-R-BTC-012-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 598; metric source `methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §28 L2962–2996; methodology/SET.md Part II §§31–34 L3050–3150; methodology/SET.md Part II §§34A–37 L3155–3435`

### TR-R-019 - BTC_CONTEXT_SCORE <= 0

- Identity: `TR-R-019` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `CONTEXTUAL_AGREEMENT_PREDICATE` / `context_momentum`
- Definition: Research predicate over BTC_CONTEXT_SCORE: BTC_CONTEXT_SCORE <= 0.
- Operator/threshold: `LTE` / `0` / unit `numeric; z-score for BTC_RETURN_Z; otherwise bounded score`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `SHORT`
- Dependencies: metrics BTC_CONTEXT_SCORE; formula refs source methodology sections only
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-022; candidates C-012
- Set usage: SET-R-012-V2, SET-R-BTC-012-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 620; metric source `methodology/SET.md Part II §§24–27 L2863–2958; methodology/SET.md Part II §28 L2962–2996; methodology/SET.md Part II §§31–34 L3050–3150; methodology/SET.md Part II §§34A–37 L3155–3435`

### TR-R-022 - VNM_5m_z >= 0

- Identity: `TR-R-022` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `CONTEXTUAL_AGREEMENT_PREDICATE` / `context_momentum`
- Definition: Research predicate over VNM_5m_z: VNM_5m_z >= 0.
- Operator/threshold: `GTE` / `0` / unit `decimal; z-score`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG`
- Dependencies: metrics VNM_5m_z; formula refs source methodology sections only
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-026; candidates C-015
- Set usage: SET-R-015-V2, SET-R-BTC-015-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 692; metric source `methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§3–6 L1739–1961; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110`

### TR-R-023 - VNM_5m_z <= 0

- Identity: `TR-R-023` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `CONTEXTUAL_AGREEMENT_PREDICATE` / `context_momentum`
- Definition: Research predicate over VNM_5m_z: VNM_5m_z <= 0.
- Operator/threshold: `LTE` / `0` / unit `decimal; z-score`
- Timeframe/context: completed 5m evaluation; source metric retains its own horizon
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `SHORT`
- Dependencies: metrics VNM_5m_z; formula refs source methodology sections only
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-026; candidates C-015
- Set usage: SET-R-015-V2, SET-R-BTC-015-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 714; metric source `methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§3–6 L1739–1961; schemas/SET_NUMERIC_POLICY.md §§1–7 L19–110`

### TR-R-029 - F-001 trigger_result = FALSE

- Identity: `TR-R-029` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `SET_RESET_PREDICATE` / `price_displacement`
- Definition: Research predicate over F-001 trigger_result: F-001 trigger_result = FALSE.
- Operator/threshold: `EQ` / `FALSE` / unit `tri-state; none`
- Timeframe/context: Current completed 1m slot ending at completed-5m Set cutoff
- Output: FALSE, TRUE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics F-001 trigger_result; formula refs F-001
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-001, R-002, R-003, R-004, R-005, R-006, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030; candidates C-001, C-003, C-007, C-008, C-009, C-010, C-011, C-012, C-015, C-016, C-019, C-020, C-021, C-031, C-032, C-034, C-035, C-036, C-037, C-039, C-040, C-041, C-042, C-043, C-051, C-052, C-054, C-055, C-059, C-060
- Set usage: SET-R-001-V1, SET-R-003-V2, SET-R-007-V2, SET-R-008-V2, SET-R-009-V2, SET-R-010-V2, SET-R-011-V2, SET-R-012-V2, SET-R-015-V2, SET-R-016-V2, SET-R-019-V1, SET-R-019-V2, SET-R-020-V1, SET-R-020-V2, SET-R-021-V1, SET-R-021-V2, SET-R-BTC-001-V1, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED. | Reset predicate: canonical F-001 FALSE evidence only; UNAVAILABLE is not treated as FALSE.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 861; metric source `methodology/SET.md Part I §8A L617–843`

### TR-R-030 - F-001 trigger_result = FALSE

- Identity: `TR-R-030` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `SET_RESET_PREDICATE` / `price_displacement`
- Definition: Research predicate over F-001 trigger_result: F-001 trigger_result = FALSE.
- Operator/threshold: `EQ` / `FALSE` / unit `tri-state; none`
- Timeframe/context: Current completed 1m slot ending at completed-5m Set cutoff
- Output: FALSE, TRUE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics F-001 trigger_result; formula refs F-001
- Applicability: coins BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB; excluded NONE
- Research usage: hypotheses R-001, R-030; candidates C-001, C-060
- Set usage: SET-R-001-V2, SET-R-BTC-001-V2
- Edge behavior: CURRENT_STATE; same source identity and authoritative cutoff; UNAVAILABLE propagates; no stale substitution | All canonical metric inputs and TT_SET_NUMERIC_V1; current F-005 qualification remains required before final MATCHED. | Reset predicate: canonical F-001 FALSE evidence only; UNAVAILABLE is not treated as FALSE.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 883; metric source `methodology/SET.md Part I §8A L617–843`

### TR-R-BTC-001 - RETURN(asset,5m) > 0

- Identity: `TR-R-BTC-001` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `BTC_DIRECTION_CONSTRUCTION` / `direction`
- Definition: Research predicate over RETURN(asset,5m): RETURN(asset,5m) > 0.
- Operator/threshold: `GT` / `0` / unit `signed decimal; fractional return`
- Timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
- Output: LONG, ZERO, UNAVAILABLE; direction applicability `LONG`
- Dependencies: metrics RETURN(asset,5m); formula refs source methodology sections only
- Applicability: coins BTC; excluded NONE
- Research usage: hypotheses R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030; candidates C-001, C-003, C-007, C-008, C-009, C-011, C-012, C-015, C-016, C-019, C-020, C-021, C-031, C-032, C-034, C-035, C-036, C-037, C-039, C-040, C-041, C-042, C-043, C-051, C-052, C-054, C-055, C-059, C-060
- Set usage: SET-R-BTC-001-V1, SET-R-BTC-001-V2, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2
- Edge behavior: CURRENT_STATE at the source-authoritative completed cutoff; required UNAVAILABLE is never FALSE or zero; no stale substitution. | Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing BTC Set. No classifier object or classifier gate is evaluated for BTC. | RETURN(BTC,5m) > 0 yields LONG, < 0 yields SHORT, = 0 yields ZERO, and unavailable return yields UNAVAILABLE.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 929; metric source `methodology/SET.md Part II §§3–6 L1739–1961; methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§24–27 L2863–2958`

### TR-R-BTC-002 - RETURN(asset,5m) < 0

- Identity: `TR-R-BTC-002` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `BTC_DIRECTION_CONSTRUCTION` / `direction`
- Definition: Research predicate over RETURN(asset,5m): RETURN(asset,5m) < 0.
- Operator/threshold: `LT` / `0` / unit `signed decimal; fractional return`
- Timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
- Output: SHORT, ZERO, UNAVAILABLE; direction applicability `SHORT`
- Dependencies: metrics RETURN(asset,5m); formula refs source methodology sections only
- Applicability: coins BTC; excluded NONE
- Research usage: hypotheses R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030; candidates C-001, C-003, C-007, C-008, C-009, C-011, C-012, C-015, C-016, C-019, C-020, C-021, C-031, C-032, C-034, C-035, C-036, C-037, C-039, C-040, C-041, C-042, C-043, C-051, C-052, C-054, C-055, C-059, C-060
- Set usage: SET-R-BTC-001-V1, SET-R-BTC-001-V2, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2
- Edge behavior: CURRENT_STATE at the source-authoritative completed cutoff; required UNAVAILABLE is never FALSE or zero; no stale substitution. | Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing BTC Set. No classifier object or classifier gate is evaluated for BTC. | RETURN(BTC,5m) > 0 yields LONG, < 0 yields SHORT, = 0 yields ZERO, and unavailable return yields UNAVAILABLE.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 963; metric source `methodology/SET.md Part II §§3–6 L1739–1961; methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§24–27 L2863–2958`

### TR-R-BTC-003 - RETURN(asset,5m) > 0

- Identity: `TR-R-BTC-003` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `BTC_DIRECTION_CONSTRUCTION` / `direction`
- Definition: Research predicate over RETURN(asset,5m): RETURN(asset,5m) > 0.
- Operator/threshold: `GT` / `0` / unit `signed decimal; fractional return`
- Timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
- Output: LONG, ZERO, UNAVAILABLE; direction applicability `LONG`
- Dependencies: metrics RETURN(asset,5m); formula refs source methodology sections only
- Applicability: coins BTC; excluded NONE
- Research usage: hypotheses R-008; candidates C-016
- Set usage: SET-R-BTC-016-V2
- Edge behavior: FRESH_EVENT: same-epoch observed FALSE→TRUE of this existing return-side predicate; unconsumed event at the current cutoff only. Initial TRUE and UNAVAILABLE→TRUE are not events; unavailable breaks event ancestry. Current side remains required at MATCHED. | Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing BTC Set. No classifier object or classifier gate is evaluated for BTC. | RETURN(BTC,5m) > 0 yields LONG, < 0 yields SHORT, = 0 yields ZERO, and unavailable return yields UNAVAILABLE.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 997; metric source `methodology/SET.md Part II §§3–6 L1739–1961; methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§24–27 L2863–2958`

### TR-R-BTC-004 - RETURN(asset,5m) < 0

- Identity: `TR-R-BTC-004` / `RESEARCH_V1_FOCUSED_CORRECTION_R3` / status `RESEARCH_ONLY`
- Role/family: `BTC_DIRECTION_CONSTRUCTION` / `direction`
- Definition: Research predicate over RETURN(asset,5m): RETURN(asset,5m) < 0.
- Operator/threshold: `LT` / `0` / unit `signed decimal; fractional return`
- Timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
- Output: SHORT, ZERO, UNAVAILABLE; direction applicability `SHORT`
- Dependencies: metrics RETURN(asset,5m); formula refs source methodology sections only
- Applicability: coins BTC; excluded NONE
- Research usage: hypotheses R-008; candidates C-016
- Set usage: SET-R-BTC-016-V2
- Edge behavior: FRESH_EVENT: same-epoch observed FALSE→TRUE of this existing return-side predicate; unconsumed event at the current cutoff only. Initial TRUE and UNAVAILABLE→TRUE are not events; unavailable breaks event ancestry. Current side remains required at MATCHED. | Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing BTC Set. No classifier object or classifier gate is evaluated for BTC. | RETURN(BTC,5m) > 0 yields LONG, < 0 yields SHORT, = 0 yields ZERO, and unavailable return yields UNAVAILABLE.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 1032; metric source `methodology/SET.md Part II §§3–6 L1739–1961; methodology/SET.md Part II §§16–18 L2512–2697; methodology/SET.md Part II §§19–20 L2701–2755; methodology/SET.md Part II §§24–27 L2863–2958`

### TR-R-BTC-005 - DE >= 0.30

- Identity: `TR-R-BTC-005` / `RESEARCH_V1_FOCUSED_CORRECTION_R2` / status `RESEARCH_ONLY`
- Role/family: `SET_FORMATION_PREDICATE` / `directional_efficiency`
- Definition: Research predicate over DE: DE >= 0.30.
- Operator/threshold: `GTE` / `0.30` / unit `numeric 0..1; dimensionless`
- Timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics DE; formula refs source methodology sections only
- Applicability: coins BTC; excluded NONE
- Research usage: hypotheses R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030; candidates C-001, C-003, C-007, C-008, C-009, C-011, C-012, C-015, C-016, C-019, C-020, C-021, C-031, C-032, C-034, C-035, C-036, C-037, C-039, C-040, C-041, C-042, C-043, C-051, C-052, C-054, C-055, C-059, C-060
- Set usage: SET-R-BTC-001-V1, SET-R-BTC-001-V2, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2
- Edge behavior: CURRENT_STATE at the source-authoritative completed cutoff; required UNAVAILABLE is never FALSE or zero; no stale substitution. | Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing BTC Set. No classifier object or classifier gate is evaluated for BTC.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 1067; metric source `methodology/SET.md Part II §§11–12 L2317–2405`

### TR-R-BTC-006 - ATR percentile >= 15

- Identity: `TR-R-BTC-006` / `RESEARCH_V1_FOCUSED_CORRECTION_R2` / status `RESEARCH_ONLY`
- Role/family: `SET_FORMATION_PREDICATE` / `volatility`
- Definition: Research predicate over ATR percentile: ATR percentile >= 15.
- Operator/threshold: `GTE` / `15` / unit `numeric 0..100; percentile rank`
- Timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics ATR percentile; formula refs F-003
- Applicability: coins BTC; excluded NONE
- Research usage: hypotheses R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030; candidates C-001, C-003, C-007, C-008, C-009, C-011, C-012, C-015, C-016, C-019, C-020, C-021, C-031, C-032, C-034, C-035, C-036, C-037, C-039, C-040, C-041, C-042, C-043, C-051, C-052, C-054, C-055, C-059, C-060
- Set usage: SET-R-BTC-001-V1, SET-R-BTC-001-V2, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2
- Edge behavior: CURRENT_STATE at the source-authoritative completed cutoff; required UNAVAILABLE is never FALSE or zero; no stale substitution. | Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing BTC Set. No classifier object or classifier gate is evaluated for BTC.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 1099; metric source `methodology/SET.md Part II §§13–15 L2410–2508; methodology/SET.md Part II §§3–6 L1739–1961`

### TR-R-BTC-007 - ATR percentile <= 97

- Identity: `TR-R-BTC-007` / `RESEARCH_V1_FOCUSED_CORRECTION_R2` / status `RESEARCH_ONLY`
- Role/family: `SET_FORMATION_PREDICATE` / `volatility`
- Definition: Research predicate over ATR percentile: ATR percentile <= 97.
- Operator/threshold: `LTE` / `97` / unit `numeric 0..100; percentile rank`
- Timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics ATR percentile; formula refs F-003
- Applicability: coins BTC; excluded NONE
- Research usage: hypotheses R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030; candidates C-001, C-003, C-007, C-008, C-009, C-011, C-012, C-015, C-016, C-019, C-020, C-021, C-031, C-032, C-034, C-035, C-036, C-037, C-039, C-040, C-041, C-042, C-043, C-051, C-052, C-054, C-055, C-059, C-060
- Set usage: SET-R-BTC-001-V1, SET-R-BTC-001-V2, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2
- Edge behavior: CURRENT_STATE at the source-authoritative completed cutoff; required UNAVAILABLE is never FALSE or zero; no stale substitution. | Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing BTC Set. No classifier object or classifier gate is evaluated for BTC.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 1131; metric source `methodology/SET.md Part II §§13–15 L2410–2508; methodology/SET.md Part II §§3–6 L1739–1961`

### TR-R-BTC-008 - TOD_REL_TURNOVER >= 0.70

- Identity: `TR-R-BTC-008` / `RESEARCH_V1_FOCUSED_CORRECTION_R2` / status `RESEARCH_ONLY`
- Role/family: `SET_FORMATION_PREDICATE` / `participation_activity`
- Definition: Research predicate over TOD_REL_TURNOVER: TOD_REL_TURNOVER >= 0.70.
- Operator/threshold: `GTE` / `0.70` / unit `nonnegative numeric; ratio`
- Timeframe/context: Current completed-5m evaluation; underlying DE, ATR percentile and TOD histories/horizons unchanged
- Output: TRUE, FALSE, UNAVAILABLE; direction applicability `LONG and SHORT`
- Dependencies: metrics TOD_REL_TURNOVER; formula refs source methodology sections only
- Applicability: coins BTC; excluded NONE
- Research usage: hypotheses R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030; candidates C-001, C-003, C-007, C-008, C-009, C-011, C-012, C-015, C-016, C-019, C-020, C-021, C-031, C-032, C-034, C-035, C-036, C-037, C-039, C-040, C-041, C-042, C-043, C-051, C-052, C-054, C-055, C-059, C-060
- Set usage: SET-R-BTC-001-V1, SET-R-BTC-001-V2, SET-R-BTC-003-V2, SET-R-BTC-007-V2, SET-R-BTC-008-V2, SET-R-BTC-009-V2, SET-R-BTC-011-V2, SET-R-BTC-012-V2, SET-R-BTC-015-V2, SET-R-BTC-016-V2, SET-R-BTC-019-V1, SET-R-BTC-019-V2, SET-R-BTC-020-V1, SET-R-BTC-020-V2, SET-R-BTC-021-V1, SET-R-BTC-021-V2
- Edge behavior: CURRENT_STATE at the source-authoritative completed cutoff; required UNAVAILABLE is never FALSE or zero; no stale substitution. | Canonical source history, exact metric ancestry and TT_SET_NUMERIC_V1; explicitly NON-F-005 enclosing BTC Set. No classifier object or classifier gate is evaluated for BTC.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 1163; metric source `methodology/SET.md Part II §8 L2013–2131; methodology/SET.md Part II §§21–23 L2760–2858`

## Non-Operative Reserve Definitions

The following source registry definitions exist in R3 but are not referenced by the current trigger-to-Set/current30 usage table and are therefore excluded from the operative import package: `TR-R-020`, `TR-R-021`, `TR-R-024`, `TR-R-025`, `TR-R-026`, `TR-R-027`, `TR-R-028`, `TR-R-031`.
