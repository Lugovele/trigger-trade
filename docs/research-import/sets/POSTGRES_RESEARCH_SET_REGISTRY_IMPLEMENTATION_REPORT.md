# PostgreSQL Research Set Registry Implementation Report

## Scope

Implemented a dedicated PostgreSQL persistence path for Research V1 Set versions as Research trigger-composition artifacts.

This does not import production Sets, import Rules, activate trading Sets, or bind Research Sets to Strategy/Risk/Portfolio/Position rule versions.

## Persistence Model

- Migration: `migrations/postgres/0024_research_set_registry.sql`
- Store: `PostgresResearchSetRegistry`
- Model: `ResearchSetVersion`
- Membership model: `ResearchSetTriggerMember`
- Tables:
  - `triggertrade_research_set_versions`
  - `triggertrade_research_set_memberships`

The model is dedicated to Research Set version identity, source-faithful trigger membership/composition, status, applicability, provenance, and canonical digest.

## Immutable Semantics

- Primary identity: `(set_id, set_version)`.
- Exact replay returns unchanged.
- Changed canonical payload under an existing identity/version is rejected.
- Duplicate trigger memberships are rejected.
- Exact source status is persisted and round-tripped.

## Trigger Reference Validation

Every member `(trigger_id, trigger_version)` resolves through `PostgresTriggerRegistry` before persistence.

Required Research V1 package coverage:

- Research Set versions: 33
- Trigger memberships: 242
- Trigger references resolved: 242/242

## Rules Boundary

The registry does not require:

- `strategy_version`
- `risk_profile_version`
- Position Rules version
- Portfolio Rules version

No placeholder Strategy/Risk/Rules versions are used.

## Validation Evidence

Focused real-PostgreSQL isolated-schema validation covers:

- 31 Research trigger definitions seeded through `PostgresTriggerRegistry`.
- First Research Set import creates 33 records.
- Second import returns 33 exact matches.
- 242 trigger memberships persist.
- 33/33 exact round-trip.
- Missing trigger refs fail closed.
- Duplicate memberships fail closed.
- Immutable conflicts fail closed for membership, trigger ref, role, composition, status, applicability, and direction-semantics changes.

## Production Safety

Production `public` was not mutated by this implementation task.

Production Set import remains a separate controlled operation after deployment and preflight.
