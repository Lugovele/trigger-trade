# Research V1 Set Catalog

Package revision: `RESEARCH_V1_FOCUSED_CORRECTION_R3`

## Summary

- Total operative Set versions: 33
- BTC-specific Set versions: 16
- V1 versions: 8
- V2 versions: 25
- Final hypotheses covered: 30/30
- Trigger membership references: 242
- Unresolved trigger references: 0
- Production Set import readiness: BLOCKED: POSTGRES_PATH_EXISTS_BUT_INCOMPLETE

## Authority

- Primary Set definitions and mappings: `C:/Users/Елена/Documents/trigger-trade/docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md`.
- Execution/reporting semantics: `C:/Users/Елена/Documents/trigger-trade/docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md`.
- Frozen Set methodology: `C:/Users/Елена/Documents/trigger-trade/docs/trading-methodology/methodology/SET.md`.
- Trigger IDs/versions resolved from: `C:/Users/Елена/Documents/trigger-trade/docs/research-import/triggers/RESEARCH_V1_TRIGGERS_WEB_IMPORT.json`.

## Set Versions

### SET-R-001-V1

- Backend identity candidate: `SET-R-001@v1`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-001, R-002, R-003, R-004, R-005, R-006, R-007, R-008, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030
- Candidates: C-001, C-003, C-007, C-008, C-009, C-010, C-011, C-012, C-015, C-016, C-031, C-032, C-034, C-035, C-036, C-037, C-039, C-040, C-041, C-042, C-043, C-051, C-052, C-054, C-055, C-059, C-060
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 1201; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 3 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 4 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-001-V2

- Backend identity candidate: `SET-R-001@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-001, R-030
- Candidates: C-001, C-060
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 1327; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-002` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 3 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 4 | `TR-R-030` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-003-V2

- Backend identity candidate: `SET-R-003@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-002, R-029
- Candidates: C-003, C-059
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 1579; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 4 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 5 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-007-V2

- Backend identity candidate: `SET-R-007@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-003
- Candidates: C-007
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 1708; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 3 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 4 | `TR-R-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.50 |
| 5 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-008-V2

- Backend identity candidate: `SET-R-008@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-004
- Candidates: C-008
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 1837; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 3 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 4 | `TR-R-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 30 |
| 5 | `TR-R-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 85 |
| 6 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-009-V2

- Backend identity candidate: `SET-R-009@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-005
- Candidates: C-009
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 1969; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 3 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 4 | `TR-R-009` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | LONG | SWING_SEQUENCE_STATE(asset,1h) = BULLISH |
| 5 | `TR-R-010` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | SHORT | SWING_SEQUENCE_STATE(asset,1h) = BEARISH |
| 6 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-010-V2

- Backend identity candidate: `SET-R-010@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-006
- Candidates: C-010
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 2099; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 3 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 4 | `TR-R-011` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | LONG | RELATIVE_RETURN_15m >= 0 |
| 5 | `TR-R-012` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | SHORT | RELATIVE_RETURN_15m <= 0 |
| 6 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-011-V2

- Backend identity candidate: `SET-R-011@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-007
- Candidates: C-011
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 2229; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 3 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 4 | `TR-R-013` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | LONG | AGGRESSIVE_VOLUME_DELTA_PCT >= 0 |
| 5 | `TR-R-014` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | SHORT | AGGRESSIVE_VOLUME_DELTA_PCT <= 0 |
| 6 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-012-V2

- Backend identity candidate: `SET-R-012@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-022
- Candidates: C-012
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 2359; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 3 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 4 | `TR-R-018` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | LONG | BTC_CONTEXT_SCORE >= 0 |
| 5 | `TR-R-019` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | SHORT | BTC_CONTEXT_SCORE <= 0 |
| 6 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-015-V2

- Backend identity candidate: `SET-R-015@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-026
- Candidates: C-015
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 2748; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 3 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 4 | `TR-R-022` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | LONG | VNM_5m_z >= 0 |
| 5 | `TR-R-023` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | SHORT | VNM_5m_z <= 0 |
| 6 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-016-V2

- Backend identity candidate: `SET-R-016@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-008
- Candidates: C-016
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 2878; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 3 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 4 | `TR-R-015` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 5 | `TR-R-016` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 6 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-019-V1

- Backend identity candidate: `SET-R-019@v1`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-009
- Candidates: C-019
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 3268; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 4 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 5 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-019-V2

- Backend identity candidate: `SET-R-019@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-009
- Candidates: C-019
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 3397; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 4 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 5 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-020-V1

- Backend identity candidate: `SET-R-020@v1`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-010
- Candidates: C-020
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 3552; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 4 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 5 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-020-V2

- Backend identity candidate: `SET-R-020@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-010
- Candidates: C-020
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 3707; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 4 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 5 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-021-V1

- Backend identity candidate: `SET-R-021@v1`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-011
- Candidates: C-021
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 3863; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 4 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 5 | `TR-R-017` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 1.00 |
| 6 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-021-V2

- Backend identity candidate: `SET-R-021@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-011
- Candidates: C-021
- Coins: ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- Excluded coins: BTC
- Direction semantics: F-005 / TT-METH-014@0.4.1 ALTCOIN_VS_BTC; final side equals the same current classifier side, never F-001 sign or score-only substitute.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 3997; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-004` | `1.0.0` | `DIRECTION_PREDICATE` | LONG | classifier_direction = LONG |
| 4 | `TR-R-005` | `1.0.0` | `DIRECTION_PREDICATE` | SHORT | classifier_direction = SHORT |
| 5 | `TR-R-017` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 1.00 |
| 6 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-001-V1

- Backend identity candidate: `SET-R-BTC-001@v1`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-012, R-013, R-014, R-015, R-016, R-017, R-018, R-019, R-020, R-021, R-022, R-023, R-024, R-025, R-026, R-027, R-028, R-029, R-030
- Candidates: C-001, C-003, C-007, C-008, C-009, C-011, C-012, C-015, C-016, C-031, C-032, C-034, C-035, C-036, C-037, C-039, C-040, C-041, C-042, C-043, C-051, C-052, C-054, C-055, C-059, C-060
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 4135; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 3 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 4 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 5 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 6 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 7 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 8 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-001-V2

- Backend identity candidate: `SET-R-BTC-001@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-001, R-030
- Candidates: C-001, C-060
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 4321; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-002` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-030` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 3 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 4 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 5 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 6 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 7 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 8 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-003-V2

- Backend identity candidate: `SET-R-BTC-003@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-002, R-029
- Candidates: C-003, C-059
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 4507; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 4 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 5 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 6 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 7 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 8 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 9 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-007-V2

- Backend identity candidate: `SET-R-BTC-007@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-003
- Candidates: C-007
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 4703; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.50 |
| 3 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 4 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 5 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 6 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 7 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 8 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 9 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-008-V2

- Backend identity candidate: `SET-R-BTC-008@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-004
- Candidates: C-008
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 4899; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 30 |
| 3 | `TR-R-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 85 |
| 4 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 5 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 6 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 7 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 8 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 9 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 10 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-009-V2

- Backend identity candidate: `SET-R-BTC-009@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-005
- Candidates: C-009
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 5105; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-009` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | LONG | SWING_SEQUENCE_STATE(asset,1h) = BULLISH |
| 3 | `TR-R-010` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | SHORT | SWING_SEQUENCE_STATE(asset,1h) = BEARISH |
| 4 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 5 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 6 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 7 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 8 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 9 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 10 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-011-V2

- Backend identity candidate: `SET-R-BTC-011@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-007
- Candidates: C-011
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 5309; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-013` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | LONG | AGGRESSIVE_VOLUME_DELTA_PCT >= 0 |
| 3 | `TR-R-014` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | SHORT | AGGRESSIVE_VOLUME_DELTA_PCT <= 0 |
| 4 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 5 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 6 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 7 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 8 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 9 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 10 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-012-V2

- Backend identity candidate: `SET-R-BTC-012@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-022
- Candidates: C-012
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 7035; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-018` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | LONG | BTC_CONTEXT_SCORE >= 0 |
| 3 | `TR-R-019` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | SHORT | BTC_CONTEXT_SCORE <= 0 |
| 4 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 5 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 6 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 7 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 8 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 9 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 10 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-015-V2

- Backend identity candidate: `SET-R-BTC-015@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-026
- Candidates: C-015
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 7256; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-022` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | LONG | VNM_5m_z >= 0 |
| 3 | `TR-R-023` | `1.0.0` | `CONTEXTUAL_AGREEMENT_PREDICATE` | SHORT | VNM_5m_z <= 0 |
| 4 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 5 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 6 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 7 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 8 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 9 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 10 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-016-V2

- Backend identity candidate: `SET-R-BTC-016@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-008
- Candidates: C-016
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 5513; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 3 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 4 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 5 | `TR-R-BTC-003` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 6 | `TR-R-BTC-004` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 7 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 8 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 9 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 10 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-019-V1

- Backend identity candidate: `SET-R-BTC-019@v1`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-009
- Candidates: C-019
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 5703; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 4 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 5 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 6 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 7 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 8 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 9 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-019-V2

- Backend identity candidate: `SET-R-BTC-019@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-009
- Candidates: C-019
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 5899; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 4 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 5 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 6 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 7 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 8 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 9 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-020-V1

- Backend identity candidate: `SET-R-BTC-020@v1`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-010
- Candidates: C-020
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 6137; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 4 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 5 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 6 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 7 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 8 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 9 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-020-V2

- Backend identity candidate: `SET-R-BTC-020@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-010
- Candidates: C-020
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 6375; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 4 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 5 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 6 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 7 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 8 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 9 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-021-V1

- Backend identity candidate: `SET-R-BTC-021@v1`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-011
- Candidates: C-021
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 6615; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-017` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 1.00 |
| 4 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 5 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 6 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 7 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 8 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 9 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 10 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.

### SET-R-BTC-021-V2

- Backend identity candidate: `SET-R-BTC-021@v2`
- Status: `RESEARCH_ONLY`
- Hypotheses: R-011
- Candidates: C-021
- Coins: BTC
- Excluded coins: NONE
- Direction semantics: DB-R-BTC-001 generic deterministic BTC direction: RETURN(BTC,5m)>0 -> LONG; <0 -> SHORT; =0 -> ZERO; unavailable -> UNAVAILABLE. BTC floor predicates DE>=0.30, ATR percentile>=15, ATR percentile<=97, TOD_REL_TURNOVER>=0.70 remain actual predicates.
- Composition: OR of documented direction branches, each branch ANDs the side predicate with common gates; UNAVAILABLE is not FALSE and blocks that predicate.
- Provenance: `docs/research-v1/RESEARCH_V1_FOCUSED_CORRECTION_R3/operative/WEB_RESEARCH_CONFIGURATION_MODEL.md` line 6823; §9 mapping table.

| Position | Trigger | Version | Role | Direction | Condition |
|---:|---|---|---|---|---|
| 1 | `TR-R-001` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-001 trigger_result = TRUE |
| 2 | `TR-R-003` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | F-002 trigger_result = TRUE |
| 3 | `TR-R-017` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 1.00 |
| 4 | `TR-R-029` | `1.0.0` | `SET_RESET_PREDICATE` | LONG and SHORT | F-001 trigger_result = FALSE |
| 5 | `TR-R-BTC-001` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | LONG | RETURN(asset,5m) > 0 |
| 6 | `TR-R-BTC-002` | `1.0.1` | `BTC_DIRECTION_CONSTRUCTION` | SHORT | RETURN(asset,5m) < 0 |
| 7 | `TR-R-BTC-005` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | DE >= 0.30 |
| 8 | `TR-R-BTC-006` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile >= 15 |
| 9 | `TR-R-BTC-007` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | ATR percentile <= 97 |
| 10 | `TR-R-BTC-008` | `1.0.0` | `SET_FORMATION_PREDICATE` | LONG and SHORT | TOD_REL_TURNOVER >= 0.70 |

Edge behavior: UNAVAILABLE is not false or zero; ZERO/NONE are preserved where documented; incomplete trigger evidence is fail-closed/unavailable; Set direction is not reinterpreted downstream.
