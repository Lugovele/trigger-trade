# Set Persistence Gap Analysis

## Finding

The previous PostgreSQL Set persistence path was incomplete for a controlled production import of the 33 Research V1 Set versions.

Status after implementation: `CLOSED_FOR_RESEARCH_SET_PERSISTENCE`.

## Evidence

- `PostgresTriggerRegistry` now provides a production PostgreSQL registry for immutable trigger `RuleDefinition` records.
- No analogous `PostgresTriggerSetRegistry` or PostgreSQL `trigger_set_versions`/`trigger_set_memberships` import table was found.
- `PostgresResearchConfigurationRegistry.put_trigger_set_version()` can store `TriggerSetVersion` as Research owner-state, but it does not validate trigger memberships against `PostgresTriggerRegistry` and is coupled to Research configuration records.
- `TriggerSetVersion` requires `strategy_version` and `risk_profile_version`; the current task explicitly excludes Rules import, and Research Set definitions themselves are trigger-composition artifacts, not Position/Portfolio rule definitions.
- PostgreSQL owner-state readback currently sets `status=TriggerSetStatus.TESTING` instead of preserving a payload status, making it unsuitable for exact round-trip status fidelity.

## Implemented Closure

1. Added authoritative `PostgresResearchSetRegistry` for immutable Research Set composition records.
2. Added dedicated PostgreSQL tables in migration `0024_research_set_registry`.
3. Validates all 242 member trigger refs against `PostgresTriggerRegistry` using exact IDs/versions.
4. Preserves source Set status exactly.
5. Defers `strategy_version` and `risk_profile_version` because Research Sets are trigger-composition artifacts; no placeholders are used.
6. Keeps import idempotent: absent creates; exact match remains unchanged; semantic conflict fails closed.

No production mutation is required by this implementation task.
