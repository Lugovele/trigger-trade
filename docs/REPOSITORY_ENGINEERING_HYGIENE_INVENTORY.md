# Repository Engineering Hygiene Inventory

Status: post-freeze formula-agnostic repository inventory.

This inventory classifies the current TriggerTrade backend surfaces after the
approved non-formula backend freeze. It does not certify formulas, change
thresholds, revise methodology, or authorize Formula Integration.

The approved `docs/trading-methodology/` package remains the highest normative
source. Formula and accounting gates in `docs/FORMULA_METRICS_CATALOG.md`
remain binding for any code path listed here.

## Classification Values

- `CANONICAL`: current target backend source, validation, or operation surface.
- `LOCAL_DEV_COMPATIBILITY`: supported local development path, not deployed
  canonical authority.
- `LEGACY_COMPATIBILITY`: retained historical or compatibility path; future
  work must not target it as canonical truth.
- `MIGRATION_ONLY`: schema or transition support, not runtime business logic.
- `DEMO_ONLY`: Bybit Demo or local simulation evidence path.
- `RESEARCH_ONLY`: research evidence, lineage, comparison, or promotion
  governance path isolated from live order execution.
- `FORMULA_BLOCKED`: structure may exist, but final calculation behavior is
  gated by `docs/FORMULA_METRICS_CATALOG.md`.
- `CANDIDATE_FOR_REMOVAL_AFTER_FORMULA_INTEGRATION`: may be removed or
  collapsed only after Formula Integration and compatibility review.

## Canonical Surfaces

| Surface | Classification | Notes |
| --- | --- | --- |
| `docs/trading-methodology/` | CANONICAL | Approved methodology source. Do not edit during backend hardening. |
| `docs/FORMULA_METRICS_CATALOG.md` | CANONICAL, FORMULA_BLOCKED | Hard implementation gate for formulas, metrics, thresholds, and accounting calculations. |
| `docs/BACKEND_TARGET_MODEL.md` | CANONICAL | Target architecture and ownership model. Source and commit history override stale status prose in planning documents. |
| `docs/BACKEND_IMPLEMENTATION_GAP_PLAN.md` | CANONICAL | Gap definitions and intended transitions. |
| `docs/BACKEND_IMPLEMENTATION_TRACEABILITY.md` | CANONICAL, CANDIDATE_FOR_REMOVAL_AFTER_FORMULA_INTEGRATION | Traceability map remains authoritative for scope, but progress/status markers may lag completed commits. Reconcile in a separate documentation/status task. |
| `scripts/validate_methodology_integrity.py` | CANONICAL | Guards approved methodology source integrity and canonical references. |
| `scripts/validate_non_formula_backend.py` | CANONICAL | Current formula-agnostic backend regression harness. |
| `src/triggertrade/canonical_json.py` | CANONICAL | Shared canonical JSON and digest utility. |
| `src/triggertrade/contracts/` | CANONICAL | Target v1.2.14 typed contract package and registry. |
| `src/triggertrade/services/process_roles.py` | CANONICAL | Process role boundary for `web`, `trading-worker`, and `scheduler`; `research-worker` is reserved. |
| `src/triggertrade/services/trading_worker.py` | CANONICAL, FORMULA_BLOCKED | Canonical message-driven worker over durable PostgreSQL outbox/inbox; handlers fail closed until certified owner logic exists. |
| `src/triggertrade/services/runtime.py::build_canonical_runtime_from_env` | CANONICAL | Canonical runtime builder. Requires PostgreSQL durable state and must not fall back to legacy paper/spot paths. |
| `src/triggertrade/services/runtime.py::build_runtime_from_env` | CANONICAL | Alias to the canonical runtime builder. |
| `src/triggertrade/services/runtime_storage.py` | CANONICAL | Canonical durable runtime-state selection and local/dev rejection boundary. |
| `src/triggertrade/persistence/postgres.py` | CANONICAL | PostgreSQL migration and connection foundation. |
| `src/triggertrade/persistence/durable_messages.py` | CANONICAL | Durable outbox/inbox dispatch foundation. |
| `src/triggertrade/persistence/postgres_runtime_store.py` | CANONICAL | PostgreSQL runtime heartbeat/state store. |
| `src/triggertrade/persistence/research_promotion_governance.py` | CANONICAL, RESEARCH_ONLY | Durable operator-authorized research promotion governance. |
| `src/triggertrade/services/operator_auth.py` | CANONICAL, LOCAL_DEV_COMPATIBILITY | App-level command authorization and audit. Process-local token compatibility is local/dev only, not deployed authentication. |
| `src/triggertrade/api_adapter_gateway/` | CANONICAL | Technical API/adapter gateway boundary; not a business-owner shortcut. |
| `src/triggertrade/portfolio_state.py`, `src/triggertrade/capital_grants.py`, `src/triggertrade/coins_scope.py` | CANONICAL | Portfolio Rules state and contract scaffolding where formula gates allow structure. |
| `src/triggertrade/position_construction.py`, `src/triggertrade/position_config_pins.py` | CANONICAL, FORMULA_BLOCKED | Position Rules contract and pin scaffolding. Final entry/stop/take/sizing formulas remain blocked. |
| `src/triggertrade/lifecycle_*.py`, `src/triggertrade/order_specs.py`, `src/triggertrade/submit_authorizations.py` | CANONICAL, FORMULA_BLOCKED | Order Lifecycle structural state, specs, and authorization boundaries. Final accounting-coupled predicates remain gated where cataloged. |
| `scripts/apply_postgres_migrations.py` | CANONICAL, MIGRATION_ONLY | PostgreSQL migration command. |
| `scripts/diagnose_backend.py` | CANONICAL | Sanitized operational diagnostics. |
| `scripts/postgres_recovery_drill.py` | CANONICAL | Backup/restore/recovery drill for isolated PostgreSQL environments. |
| `docs/OPERATIONAL_RUNBOOKS.md` | CANONICAL | Formula-agnostic operations procedures for the frozen backend. |
| `docs/POSTGRES_BACKUP_RESTORE_DRILL.md` | CANONICAL | PostgreSQL recovery drill runbook. |

## Compatibility, Legacy, Demo, And Research Surfaces

| Surface | Classification | Notes |
| --- | --- | --- |
| `docs/archive/trading-methodology-pre-v1.2.14/` | LEGACY_COMPATIBILITY | Historical archive only. It is not normative authority. |
| `docs/formula-certification/` | RESEARCH_ONLY, FORMULA_BLOCKED | Separate untracked formula-certification work. Do not modify in backend hardening. |
| `src/triggertrade/services/runtime.py::PaperTradingRuntime` | LEGACY_COMPATIBILITY, DEMO_ONLY | Legacy local paper runtime retained for direct compatibility imports only. |
| `src/triggertrade/services/runtime.py::build_legacy_demo_futures_runtime_from_env` | LEGACY_COMPATIBILITY, DEMO_ONLY, FORMULA_BLOCKED | Explicit opt-in demo futures runtime. It may run demo formula code only when separately opted in; it is not canonical runtime selection. |
| `src/triggertrade/services/futures_runtime.py` | DEMO_ONLY, FORMULA_BLOCKED | Demo dual-lane runtime and compatibility evidence path. Canonical active formula execution remains fenced by default. |
| `src/triggertrade/services/dual_lane_runtime.py` | LEGACY_COMPATIBILITY, DEMO_ONLY | Older dual-lane local paper/runtime support. |
| `src/triggertrade/execution/paper.py` | LEGACY_COMPATIBILITY, DEMO_ONLY | Local paper adapter retained for explicit compatibility and tests. |
| `src/triggertrade/execution/bybit.py` | LEGACY_COMPATIBILITY, DEMO_ONLY | Legacy spot Bybit adapter. Canonical runtime must not select it. |
| `src/triggertrade/execution/bybit_futures.py` | CANONICAL, DEMO_ONLY | Bybit Demo linear futures adapter boundary. Native profile gaps remain gated by conformance tests and Formula/Accounting gates where applicable. |
| `src/triggertrade/persistence/legacy_execution_boundary.py` | CANONICAL | Explicit marker proving legacy execution stores are not target Lifecycle truth. |
| `src/triggertrade/persistence/execution_store.py` | LEGACY_COMPATIBILITY | Legacy execution evidence store; not canonical target Lifecycle truth. |
| `src/triggertrade/persistence/futures_execution_store.py` | DEMO_ONLY, LEGACY_COMPATIBILITY | Demo futures execution evidence used by compatibility/runtime tests. |
| `src/triggertrade/persistence/futures_accounting_store.py` | DEMO_ONLY, FORMULA_BLOCKED | Demo accounting persistence. Final accounting formulas remain catalog-gated. |
| `src/triggertrade/persistence/trading_rules_store.py` | LOCAL_DEV_COMPATIBILITY, DEMO_ONLY | SQLite-backed rules registry used by local/dev and demo compatibility paths. Do not treat as canonical deployed truth. |
| `src/triggertrade/persistence/trigger_set_store.py` | LOCAL_DEV_COMPATIBILITY, DEMO_ONLY | SQLite-backed trigger/set registry used by local/dev and demo compatibility paths. |
| `src/triggertrade/dashboard/read_model.py` | LOCAL_DEV_COMPATIBILITY | Dashboard read model can read SQLite compatibility state and PostgreSQL-backed operational facts. It must remain read-model only. |
| `src/triggertrade/dashboard/commands.py` | CANONICAL, RESEARCH_ONLY | Operator command facade. Research promotion must route through durable governance, not direct SQLite mutation. |
| `src/triggertrade/services/research.py` | RESEARCH_ONLY, FORMULA_BLOCKED | Research lineage, backtest, demo, compare, and promotion request service. Metrics remain research parameters. |
| `src/triggertrade/backtest/` | RESEARCH_ONLY, FORMULA_BLOCKED | Research replay/simulation evidence. Not canonical live trading logic. |
| `src/triggertrade/analytics/futures.py` | RESEARCH_ONLY, FORMULA_BLOCKED | Research metrics only; values must remain parameterized. |
| `src/triggertrade/market_data/regime.py` | RESEARCH_ONLY, FORMULA_BLOCKED | Current classifier lacks canonical trading definition and must not become a trading input before review. |
| `src/triggertrade/triggers/` | LEGACY_COMPATIBILITY, DEMO_ONLY, FORMULA_BLOCKED | Existing trigger calculations are cataloged legacy/demo implementations until formula certification. |
| `src/triggertrade/strategies/` | LEGACY_COMPATIBILITY, DEMO_ONLY, FORMULA_BLOCKED | Existing demo strategy paths are not final Position Rules behavior. |
| `src/triggertrade/risk/` | LEGACY_COMPATIBILITY, DEMO_ONLY, FORMULA_BLOCKED | Existing demo risk manager is not final Portfolio/Position Rules behavior. |
| `src/triggertrade/accounting/futures.py` | DEMO_ONLY, FORMULA_BLOCKED | Some factual accounting helpers are allowed by catalog, but net final result and accounting-day logic remain blocked. |
| `src/triggertrade/services/daily_loss.py` | DEMO_ONLY, FORMULA_BLOCKED | Daily-loss structure exists; final accounting-day calculation remains blocked by A-009. |
| `scripts/paper_runtime_smoke.py` | LEGACY_COMPATIBILITY, DEMO_ONLY | Requires explicit legacy local-paper builder. |
| `scripts/bybit_demo_*smoke.py`, `scripts/triggertrade_*demo*.py`, `scripts/volume_trigger_smoke.py` | DEMO_ONLY, FORMULA_BLOCKED | Explicit opt-in smoke and demo harnesses. Not canonical deployed runtime. |
| `tests/integration/test_*demo*`, `tests/unit/test_*demo*`, `tests/unit/test_dual_lane_runtime.py` | DEMO_ONLY, FORMULA_BLOCKED | Compatibility and demo proof tests. Do not use them as final formula evidence. |

## Stale Or Potentially Misleading Documentation

| Location | Classification | Required Handling |
| --- | --- | --- |
| `docs/BACKEND_IMPLEMENTATION_TRACEABILITY.md` status fields | CANDIDATE_FOR_REMOVAL_AFTER_FORMULA_INTEGRATION | Some status and technical-decision prose can lag completed commits. Use current source and Git history for factual completion; reconcile status in a separate docs/status task. |
| `docs/architecture.md` sections describing local SQLite backup/runtime state | LOCAL_DEV_COMPATIBILITY | These describe retained local/dev and compatibility behavior. Canonical deployed durable state is PostgreSQL unless a surface is explicitly local/dev or legacy. |
| `docs/architecture.md` sections describing futures runtime formula/accounting mechanics | FORMULA_BLOCKED | Read through `docs/FORMULA_METRICS_CATALOG.md`; descriptive demo mechanics do not certify final formulas. |
| `README.md` runtime/dashboard passages mentioning SQLite | LOCAL_DEV_COMPATIBILITY | Valid for local/dev compatibility, not deployed canonical durable truth. |
| `docs/trading-rules.md` candidate parameter language | FORMULA_BLOCKED | Candidate/test values must not be treated as certified calibration. |

## Duplicate Or Parallel Helpers To Preserve For Now

| Surface | Classification | Rationale |
| --- | --- | --- |
| SQLite stores and PostgreSQL stores | LOCAL_DEV_COMPATIBILITY, CANONICAL | Both are currently required: PostgreSQL for canonical durable roles; SQLite for local/dev, historical evidence, and compatibility tests. Do not collapse without a traced migration task. |
| Store-local JSON/digest payload helpers | CANONICAL, LOCAL_DEV_COMPATIBILITY | Several stores use canonical JSON where identity matters. Local helper shape differs by table contract; consolidate only if a future task touches the affected stores together. |
| Dashboard read-model projections and diagnostic snapshot projections | CANONICAL, LOCAL_DEV_COMPATIBILITY | Dashboard presents operator-facing read models; diagnostics presents sanitized operations facts. Keep surfaces separate to avoid raw operational data in the UI. |
| Legacy/demo smoke harnesses and canonical validation harness | DEMO_ONLY, CANONICAL | Smoke harnesses prove opt-in compatibility; `scripts/validate_non_formula_backend.py` is the regression contract. |

## Candidate Removal Or Consolidation After Formula Integration

These are not removal instructions. They are review targets once certified
Formula Integration and compatibility migration are complete.

| Surface | Reason To Revisit Later |
| --- | --- |
| `PaperTradingRuntime` and `PaperExecutionAdapter` compatibility paths | Could be removed only after local/demo compatibility is intentionally retired or replaced. |
| Legacy spot `BybitExecutionAdapter` path | Retained for historical smoke coverage and explicit demo compatibility. |
| Demo dual-lane futures runtime opt-in path | May be superseded by certified canonical worker handlers after Formula Integration. |
| SQLite research promotion compatibility flag | Should stay disabled by default; removal depends on migration/support needs. |
| SQLite runtime backup/integrity docs and tests | May be narrowed after all canonical durable state is PostgreSQL-backed and historical compatibility needs are resolved. |
| Stale traceability progress/status prose | Should be reconciled in a documentation/status task, not during formula integration. |

## Future Formula Integration Targeting Rules

1. Target canonical contracts, PostgreSQL durable stores, process roles,
   durable outbox/inbox, owner-state stores, and API/adapter gateway surfaces.
2. Do not target `PaperTradingRuntime`, legacy spot execution, legacy local
   paper execution, demo smoke scripts, or SQLite-only compatibility stores as
   canonical runtime authority.
3. Do not promote any `DEMO_ONLY`, `RESEARCH_ONLY`, or
   `LEGACY_COMPATIBILITY` calculation to canonical behavior unless its catalog
   item has first been certified or reclassified.
4. Do not treat research metrics as trading approval criteria. Research output
   can support evidence and operator promotion governance only.
5. Do not use archived methodology as authority for formula or runtime target
   behavior.
6. Do not implement a Position Rules to API direct shortcut; execution must
   remain through approved owner boundaries and durable lifecycle authority.

## Workstream 7 Result

The repository now has an explicit classification map for canonical,
local-dev, legacy, demo, research, migration-only, and formula-blocked
surfaces. No compatibility path is deleted. No formula, threshold, accounting
calculation, calibration value, methodology file, or formula-certification file
is changed by this inventory.
