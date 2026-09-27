# Research V1 Set Import Execution Plan

## Current Status

Set import is implementation-ready for controlled production preflight after deployment of the PostgreSQL Research Set registry. Canonical extraction is complete, trigger references resolve in the package, and isolated PostgreSQL validation must confirm all references against `PostgresTriggerRegistry`.

## Next Mechanical Sequence

1. Review `RESEARCH_V1_SETS.json` and `RESEARCH_V1_SET_VALIDATION_REPORT.md`.
2. Ensure migration `0024_research_set_registry` is applied in the target environment.
3. Verify the 31 approved Research V1 trigger definitions are present in `PostgresTriggerRegistry`.
4. Load `RESEARCH_V1_SETS_WEB_IMPORT.json`.
5. Parse all 33 records as `ResearchSetVersion`.
6. Preflight with `PostgresResearchSetRegistry.sync_research_sets()` in dry-run/classification mode or equivalent import script: `ABSENT / EXACT_MATCH / CONFLICT`.
7. Stop if any conflict appears.
8. If conflicts are zero, persist only absent Research Set versions through `PostgresResearchSetRegistry`.
9. Run a second idempotency pass; expected result is `CREATED: 0`, `EXACT_MATCH: 33`, `CONFLICTS: 0`.
10. Verify exact readback for 33/33 records and 242/242 trigger memberships.
11. Resolve the Rules dependency later by importing or explicitly linking approved Trading Rules/Position/Portfolio artifacts in their own controlled task.

## Prohibited In This Step

Do not import Sets into production, import Rules, activate Sets, start Demo, or mutate production state.
