# Research V1 Combined Rules Import Execution Plan

Status: PLAN_ONLY

No import is performed by this document.

## Current Result

The Research V1 Rules package is reconciled to combined `TradingRulesVersion` records. It is import-ready for review because 16/16 combined versions validate through the current backend without semantic loss.

## Required Next Steps

1. Review the combined Rules package and confirm the 16-version population.
2. Review `RESEARCH_V1_RULES_WEB_IMPORT.json`; it is generated from actual `TradingRulesVersionDraft` serialization.
3. Run a real PostgreSQL isolated-schema dry-run when `TRIGGERTRADE_POSTGRES_DSN` is available.
4. Import in production only through a controlled import step after review approval.

ATR construction bindings and asset labels are not Rules blockers after methodology-first reconciliation. Preserve ATR bindings as Position construction / certified formula references, and resolve asset labels through launch-time instrument binding.

## Non-Goals

- Do not create a separate Position Rules registry.
- Do not create a separate Portfolio Rules registry.
- Do not import production Rules in this package task.
- Do not change BTC triggers, Sets, frozen methodology, or production rows.
