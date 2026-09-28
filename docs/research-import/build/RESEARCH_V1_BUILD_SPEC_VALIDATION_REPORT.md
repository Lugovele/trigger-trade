# Research V1 Build Spec Validation Report

## Inputs Inspected

- `docs\research-v1\RESEARCH_V1_FOCUSED_CORRECTION_R3\operative\RESEARCH_HYPOTHESES_FINAL_30.md`
- `docs\research-v1\RESEARCH_V1_FOCUSED_CORRECTION_R3\operative\WEB_RESEARCH_CONFIGURATION_MODEL.md`
- `docs\research-v1\RESEARCH_V1_FOCUSED_CORRECTION_R3\operative\RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md`
- `docs\research-import\sets\RESEARCH_V1_SETS.json`
- `docs\research-import\sets\RESEARCH_V1_SET_IMPORT_MAP.md`
- `docs\research-import\sets\RESEARCH_V1_SET_VALIDATION_REPORT.md`
- `docs\research-import\rules\RESEARCH_V1_RULES.json`
- `docs\research-import\rules\RESEARCH_V1_RULES_CATALOG.md`
- `docs\research-import\rules\RESEARCH_V1_RULES_RECONCILIATION_REPORT.md`

## Authority Resolution

The Build Spec follows frozen methodology v1.2.15 first, then certified formula/state-rule specifications by reference, then corrected/final Research V1 documents, then approved/imported Trigger, Set, and Rules artifacts. No methodology conflict requiring an `UNRESOLVED_BUILD_SPEC_MAPPING` marker was found.

The `RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md` compare order including `ACTIVE` is used for the canonical compare profile.

## Mapping Result

- RESEARCH_DEFINITIONS: 30/30
- UNIQUE_RESEARCH_IDS: 30/30
- UNIQUE_HYPOTHESIS_IDS: 30/30
- Final hypotheses covered: R-001 through R-030
- Extra hypotheses: 0
- UNRESOLVED_BUILD_SPEC_MAPPINGS: 0

## Set Resolution

- Primary Set references resolved: 30/30
- Unique Set versions referenced across all baseline/variant/cell bindings: 33
- Binding Set references resolved: 33/33
- Missing Set references: None
- Trigger composition duplicated in ResearchDefinitions: NO

## Rules Resolution

- Primary Rules references resolved: 30/30
- Unique TradingRulesVersion IDs referenced across all bindings: 16
- Binding Rules references resolved: 16/16
- Missing Rules references: None
- Combined TradingRulesVersion is used; Position and Portfolio components are not split into separate ResearchDefinition dependencies.

## Reusable Profile Validation

- UNIVERSE_COINS: 10/10
- Universe order: BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB
- ALLOCATION_TOTAL_PCT: 100
- RUN_PROFILES_VALID: YES
- RESULT_SCOPES_VALID: YES
- COMPARE_ORDER_VALID: YES
- UNVERSIONED_REFERENCES: 0
- LATEST_REFERENCES: 0
- Launch-time values baked into immutable identities: NO

## BTC Special-Case Validation

- BTC remains in `UNIVERSE-CORE-V1` with 10% allocation.
- R-006 BTC result scope is explicitly `NOT_APPLICABLE` with reason `SOURCE_LOGIC_NOT_MEANINGFUL_FOR_BTC`.
- Allocation redistribution for R-006 BTC is `NONE`.
- Corrected BTC Set versions are referenced where BTC Set bindings are applicable.
- Build Spec references Set versions; it does not independently rewrite or duplicate trigger composition.

## Cross-Reference Summary

Unique primary Set versions referenced: 14

| Primary Set Version | Hypotheses |
|---|---|
| `SET-R-001-V1` | `R-012`, `R-013`, `R-014`, `R-015`, `R-016`, `R-017`, `R-018`, `R-019`, `R-020`, `R-021`, `R-023`, `R-024`, `R-025`, `R-027`, `R-028` |
| `SET-R-001-V2` | `R-001`, `R-030` |
| `SET-R-003-V2` | `R-002`, `R-029` |
| `SET-R-007-V2` | `R-003` |
| `SET-R-008-V2` | `R-004` |
| `SET-R-009-V2` | `R-005` |
| `SET-R-010-V2` | `R-006` |
| `SET-R-011-V2` | `R-007` |
| `SET-R-012-V2` | `R-022` |
| `SET-R-015-V2` | `R-026` |
| `SET-R-016-V2` | `R-008` |
| `SET-R-019-V2` | `R-009` |
| `SET-R-020-V2` | `R-010` |
| `SET-R-021-V2` | `R-011` |

Unique primary Rules versions referenced: 16

| Primary Rules Version | Hypotheses |
|---|---|
| `TRV-R-POS-001-PR-201` | `R-001`, `R-002`, `R-003`, `R-004`, `R-005`, `R-006`, `R-007`, `R-008`, `R-009`, `R-010`, `R-011`, `R-022`, `R-026` |
| `TRV-R-POS-001-PR-204` | `R-024` |
| `TRV-R-POS-001-PR-205` | `R-025` |
| `TRV-R-POS-001-PR-207` | `R-027`, `R-029` |
| `TRV-R-POS-001-PR-208` | `R-028` |
| `TRV-R-POS-002-PR-201` | `R-012` |
| `TRV-R-POS-003-PR-201` | `R-013`, `R-030` |
| `TRV-R-POS-005-PR-201` | `R-014` |
| `TRV-R-POS-006-PR-201` | `R-015` |
| `TRV-R-POS-007-PR-201` | `R-023` |
| `TRV-R-POS-008-PR-201` | `R-016` |
| `TRV-R-POS-010-PR-201` | `R-017` |
| `TRV-R-POS-011-PR-201` | `R-018` |
| `TRV-R-POS-012-PR-201` | `R-019` |
| `TRV-R-POS-013-PR-201` | `R-020` |
| `TRV-R-POS-014-PR-201` | `R-021` |

Hypotheses with special BTC or nonstandard applicability:

| Hypothesis | Condition |
|---|---|
| `R-006` | BTC result scope `NOT_APPLICABLE`; universe/allocation membership retained. |
| `R-022` | R3 replacement correction; BTC contextual agreement. |
| `R-026` | R3 replacement correction; local-momentum agreement. |
| `R-029` | Cross-layer interaction cells preserved. |
| `R-030` | Cross-layer interaction cells preserved. |

## Unresolved Mappings

None.

## Deterministic Builder Readiness Verdict

READY. The JSON Build Spec contains exactly 30 source-pinned ResearchDefinitions, exact immutable Set and Rules references, reusable universe/allocation/run/result/compare/evidence profiles, explicit BTC handling, and deterministic builder constraints. No production mutation is authorized by this artifact.
