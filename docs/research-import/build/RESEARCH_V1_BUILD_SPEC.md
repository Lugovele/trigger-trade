# Research V1 Build Specification

## Purpose

This document defines the canonical, machine-oriented Research V1 build specification. It normalizes the approved Research V1 documentation into deterministic builder input for exactly 30 ResearchDefinition objects.

The relationship modeled here is:

`Hypothesis -> Set Version -> TradingRulesVersion -> Universe/Allocation -> Run Profiles -> Result Scopes -> Compare Order`

Trigger composition is not re-encoded in ResearchDefinition records. Trigger membership, ordering, roles, conditions, and BTC trigger-version corrections remain owned by the referenced immutable Research Set versions.

## Authority

Authority order for this build spec:

1. Frozen TriggerTrade methodology v1.2.15.
2. Certified formula/state-rule specifications referenced by methodology.
3. Corrected/final Research V1 documentation.
4. Current approved/imported Trigger artifacts.
5. Current approved/imported Set artifacts.
6. Current corrected Rules artifacts.
7. Existing backend representations where conformant.

No source conflict was identified while creating this specification. The `RESEARCH_V1_EXECUTION_AND_REPORTING_PROFILE.md` compare order is authoritative for this spec: `ACTIVE`, `DEMO_7D`, `BACKTEST_7D`, `BACKTEST_30D`, `BACKTEST_90D`.

## Schema

The canonical JSON artifact is `RESEARCH_V1_BUILD_SPEC.json`. Its top-level sections are:

- `schema_version`
- `research_program`
- `schema_contract`
- `universe_profiles`
- `allocation_profiles`
- `run_profiles`
- `result_scope_profiles`
- `compare_profiles`
- `evidence_export_profiles`
- `build_time_immutable_fields`
- `launch_time_fields`
- `research_definitions`
- `validation_invariants`
- `provenance`
- `validation_summary`

Each ResearchDefinition contains at least:

`research_id`, `hypothesis_id`, `title`, `description`, `status`, `set_version_id`, `rules_version_id`, `universe_id`, `allocation_profile_id`, `segment_scope`, `applicable_coins`, `excluded_coins`, `direction_scope`, `run_profiles`, `result_scopes`, `compare_order`, `evidence_export_profile`, `special_applicability`, `source_refs`, `provenance`, and `notes`.

The JSON also includes `set_version_bindings` and `rules_version_bindings` because approved Research V1 sources distinguish baseline, variant, and cross-layer interaction cells. The singular `set_version_id` and `rules_version_id` fields identify the primary variant or primary interaction cell for the hypothesis; the binding objects preserve the full approved comparison structure.

## Identity And Versioning Rules

All Set references are exact immutable Set version IDs such as `SET-R-003-V2` or `SET-R-BTC-003-V2`. All Rules references are exact immutable combined TradingRulesVersion IDs such as `TRV-R-POS-001-PR-207`.

The spec does not use `latest`, implicit current versions, generated UUIDs, timestamps as identity, or environment-specific paths. A builder must fail closed if a referenced Set, Rules version, reusable profile, or source-version pin is absent or conflicting.

## Build-Time And Launch-Time Ownership

Build-time immutable fields include hypothesis identity, Set version, TradingRulesVersion, universe profile, allocation profile, allowed run profiles, result scopes, compare order, and evidence export profile.

Launch-time fields are intentionally excluded from identity-bearing ResearchDefinition payloads. These include exact start time, exact backtest window endpoint, exchange instrument binding, test/live account selection, execution environment, and operator-entered limits that are not part of the immutable Research definition.

## Reusable Profiles

Universe profile: `UNIVERSE-CORE-V1`, exactly 10 assets: `BTC`, `ETH`, `SOL`, `XRP`, `DOGE`, `SUI`, `PEPE`, `AVAX`, `LINK`, `BNB`.

Allocation profile: `ALLOC-R-V1-FIXED-10X10`, static 10% per coin, total 100%, segments `MAJORS=20`, `HIGH_VOLATILITY_HIGH_BETA=60`, and `DIVERSIFIERS=20`. There is no dynamic allocation, no optimization, no reweighting, and no redistribution.

Run profiles: `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D`.

Result scopes: `OVERALL`, `BY_SEGMENT`, `BY_COIN`, `BY_DIRECTION`.

Compare order: `ACTIVE`, `DEMO_7D`, `BACKTEST_7D`, `BACKTEST_30D`, `BACKTEST_90D`.

Evidence export profile: `EVIDENCE-R-V1-R2`, with root `RESEARCH_RECORD`. It must preserve attempts, failures, metrics, triggers, Set, Position, Portfolio, Lifecycle, financials, comparisons, and decisions.

Intrabar policy is referenced by identifier only: `FACTUAL_SEQUENCE_THEN_REFINEMENT_THEN_ORDER_INVARIANCE_OR_CENSOR_V1`. This spec does not duplicate the intrabar algorithm.

## ResearchDefinition Mapping

| Hypothesis | Research ID | Set Version | Rules Version | Direction | Applicability | Special Case | Allowed Run Profiles | Status |
|---|---|---|---|---|---|---|---|---|
| `R-001` | `R-001` | `SET-R-001-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-002` | `R-002` | `SET-R-003-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-003` | `R-003` | `SET-R-007-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-004` | `R-004` | `SET-R-008-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-005` | `R-005` | `SET-R-009-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-006` | `R-006` | `SET-R-010-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | BTC NOT_APPLICABLE; non-BTC applicable | BTC result scope NOT_APPLICABLE | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-007` | `R-007` | `SET-R-011-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-008` | `R-008` | `SET-R-016-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-009` | `R-009` | `SET-R-019-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-010` | `R-010` | `SET-R-020-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-011` | `R-011` | `SET-R-021-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-012` | `R-012` | `SET-R-001-V1` | `TRV-R-POS-002-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-013` | `R-013` | `SET-R-001-V1` | `TRV-R-POS-003-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-014` | `R-014` | `SET-R-001-V1` | `TRV-R-POS-005-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-015` | `R-015` | `SET-R-001-V1` | `TRV-R-POS-006-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-016` | `R-016` | `SET-R-001-V1` | `TRV-R-POS-008-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-017` | `R-017` | `SET-R-001-V1` | `TRV-R-POS-010-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-018` | `R-018` | `SET-R-001-V1` | `TRV-R-POS-011-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-019` | `R-019` | `SET-R-001-V1` | `TRV-R-POS-012-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-020` | `R-020` | `SET-R-001-V1` | `TRV-R-POS-013-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-021` | `R-021` | `SET-R-001-V1` | `TRV-R-POS-014-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-022` | `R-022` | `SET-R-012-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | R3 replacement correction | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-023` | `R-023` | `SET-R-001-V1` | `TRV-R-POS-007-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-024` | `R-024` | `SET-R-001-V1` | `TRV-R-POS-001-PR-204` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-025` | `R-025` | `SET-R-001-V1` | `TRV-R-POS-001-PR-205` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-026` | `R-026` | `SET-R-015-V2` | `TRV-R-POS-001-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | R3 replacement correction | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-027` | `R-027` | `SET-R-001-V1` | `TRV-R-POS-001-PR-207` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-028` | `R-028` | `SET-R-001-V1` | `TRV-R-POS-001-PR-208` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | None | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-029` | `R-029` | `SET-R-003-V2` | `TRV-R-POS-001-PR-207` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | Interaction cells preserved | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |
| `R-030` | `R-030` | `SET-R-001-V2` | `TRV-R-POS-003-PR-201` | LONG/SHORT | 10-coin universe; BTC uses DB-R-BTC-001 | Interaction cells preserved | `BACKTEST_90D`, `BACKTEST_30D`, `BACKTEST_7D`, `DEMO_7D` | `FINAL_RESEARCH_V1` |

## Special Cases

`R-006` keeps BTC in the global universe and allocation profile, but BTC result scope for that hypothesis is `NOT_APPLICABLE` because BTC-vs-BTC relative-return logic is not meaningful. The spec does not remove BTC from `UNIVERSE-CORE-V1`, does not redistribute BTC's 10% allocation, and does not report a synthetic BTC result for that hypothesis.

`R-022` and `R-026` preserve the R3 replacement corrections. Historical candidate meanings remain historical only and are not silently reused.

`R-029` and `R-030` preserve cross-layer interaction cells in `set_version_bindings` and `rules_version_bindings`. They remain one ResearchDefinition each, not one definition per cell or run profile.

BTC-specific Set bindings reference corrected BTC Set versions that were rebound to trigger version `1.0.1` before production Set import. The Build Spec refers to Set versions only; it does not rewrite trigger references.

## Validation Invariants

A conforming builder must validate:

- exactly 30 ResearchDefinitions;
- 30 unique `research_id` values;
- 30 unique `hypothesis_id` values;
- all final hypotheses R-001 through R-030 covered with no extras;
- every Set reference exists in `RESEARCH_V1_SETS.json`;
- every TradingRulesVersion reference exists in `RESEARCH_V1_RULES.json`;
- no unversioned Set or Rules references;
- no `latest` references;
- allocation total equals 100%;
- universe assets equal BTC, ETH, SOL, XRP, DOGE, SUI, PEPE, AVAX, LINK, BNB;
- run profile set is exactly BACKTEST_90D, BACKTEST_30D, BACKTEST_7D, DEMO_7D;
- result scopes are exactly OVERALL, BY_SEGMENT, BY_COIN, BY_DIRECTION;
- compare order is exactly ACTIVE, DEMO_7D, BACKTEST_7D, BACKTEST_30D, BACKTEST_90D;
- BTC exceptions are explicit;
- ResearchDefinition records do not duplicate trigger memberships;
- no launch-time values are baked into immutable identities.

## Builder Contract

The future Research Definition Builder must be deterministic, idempotent, fail-closed, source-version pinned, side-effect free during build, production-agnostic, and forbidden from implicit `latest` resolution or placeholder creation.

Required builder behavior:

1. Load `RESEARCH_V1_BUILD_SPEC.json`.
2. Validate schema and invariants.
3. Validate all Set references.
4. Validate all Rules references.
5. Validate reusable profile references.
6. Compile exactly 30 ResearchDefinition objects.
7. Emit a canonical import package.
8. Emit a deterministic validation report.
9. Make no production writes.

Production import remains a separate controlled operation.

## Deterministic Serialization

Canonical serialization rules for future implementation:

- UTF-8 text.
- Stable key ordering when canonicalization is used.
- Stable array ordering exactly as declared in this spec.
- No generated timestamps inside identity-bearing canonical payloads.
- No random IDs.
- No environment-specific absolute paths.
- No secrets.
- Exact immutable version pins.

If digesting is implemented later, the digest input should be the canonical JSON payload after stable key ordering and stable array preservation, excluding only fields explicitly classified as validation-output metadata.

## Future Import Flow

The future flow is:

`Approved Research docs -> RESEARCH_V1_BUILD_SPEC.json -> deterministic builder -> ResearchDefinition import package -> validation report -> separate controlled production import`.

No backend implementation, migrations, web routes, production writes, or Research/Demo launch are part of this specification task.
