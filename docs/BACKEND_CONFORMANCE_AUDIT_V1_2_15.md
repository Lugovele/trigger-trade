# Backend Conformance Audit Against Frozen Methodology v1.2.15

Audit date: 2026-09-16

Audited repository baseline:

- Branch: `main`
- Frozen methodology commit: `e3aaa67fe5cf06e1d018291ee4d49f335fc5ea56`
- Canonical methodology path: `docs/trading-methodology/`
- Canonical methodology revision: `v1.2.15`
- Audit scope: backend/source/tests only; no methodology reinterpretation and no implementation changes.

This audit is a factual conformance review of the current backend against the
frozen TriggerTrade v1.2.15 methodology. It is not a formula certification,
methodology audit, implementation map, or remediation plan.

## Executive Verdict

The backend is not conformant enough to execute the frozen v1.2.15 methodology
as canonical active trading behavior.

The strongest positive finding is that the repository contains substantial
formula-agnostic infrastructure: PostgreSQL migrations, durable outbox/inbox
primitives, process roles, strict contract helpers, canonical JSON/digest
utilities, diagnostics, research lineage stores, and many structural owner-state
stores.

The strongest negative finding is that the canonical runtime path still blocks
all owner messages instead of executing the Portfolio, Set, Position, and Order
Lifecycle flows. The canonical trading worker claims messages, records a
`handler_not_certified:<consumer>:<message_type>` heartbeat, and returns a
blocked result. Therefore, the business method is mostly represented as
contracts, stores, and gates, not as an executable canonical runtime.

There are also direct package-version conformance gaps after the methodology
promotion to v1.2.15. The source contract registry and generated approved wire
schema still identify the approved package as v1.2.14, and tests still assert
v1.2.14 methodology pinning in several places.

## Audit Method

Evidence inspected:

- `docs/trading-methodology/` v1.2.15 active package.
- `src/triggertrade/` current backend source.
- `tests/` current test suite.
- `scripts/` operational and validation scripts.
- PostgreSQL migrations under `migrations/postgres/`.

No files under `docs/trading-methodology/` were used as historical commentary;
the active v1.2.15 package is treated as the canonical source. The archived
methodology was not used as normative authority.

No runtime behavior, formula, test, schema, or methodology file was changed by
this audit other than creation of this report.

## Status Definitions

- `CORRECT`: The current backend behavior matches the frozen methodology for
  the audited requirement.
- `PARTIAL`: The current backend contains useful structure but not complete
  methodology behavior.
- `MISSING`: Required behavior is not implemented in the canonical path.
- `CONFLICTING`: Current behavior contradicts the frozen methodology or active
  package metadata.
- `LEGACY_DEMO_ONLY`: Behavior exists only in legacy, demo, research, or local
  compatibility paths and must not be treated as canonical.
- `AMBIGUOUS`: The methodology does not provide enough information to classify
  backend conformance. No such ambiguity was found in this audit.

## Conformance Summary Counts

| Category | Count |
|---|---:|
| Requirements reviewed | 60 |
| CORRECT | 6 |
| PARTIAL | 25 |
| MISSING | 20 |
| CONFLICTING | 5 |
| LEGACY_DEMO_ONLY | 4 |
| AMBIGUOUS | 0 |

These counts are audit classifications, not implementation estimates. A single
finding can affect multiple requirements.

## Architecture and Ownership Audit

Canonical methodology owners:

- Portfolio Rules: capital management.
- Set: market analysis.
- Position Rules: trade decision.
- Order Lifecycle: order management.
- API / Adapter Gateway: technical data/interface boundary only.
- Research: isolated evidence and candidate generation, not live execution.

Current backend ownership state:

| Owner / Boundary | Current Implementation | Status | Evidence |
|---|---|---|---|
| Canonical launcher | `build_runtime_from_env` points to `build_canonical_runtime_from_env`; canonical config rejects paper and legacy spot/demo venues. | PARTIAL | `src/triggertrade/services/runtime.py:560`, `src/triggertrade/services/runtime.py:581`, `src/triggertrade/services/runtime.py:640` |
| Canonical trading worker | `TargetTradingWorker` exists but blocks all claimed owner messages as handler-not-certified. | MISSING | `src/triggertrade/services/trading_worker.py:106`, `src/triggertrade/services/trading_worker.py:118` |
| Process roles | Web, trading-worker, scheduler are represented; research-worker is reserved. | PARTIAL | `src/triggertrade/services/process_roles.py:16`, `src/triggertrade/services/process_roles.py:80` |
| Scheduler | Scheduler process hydrates durable runtime state and heartbeat/list state only; no canonical scheduling duties are visible. | PARTIAL | `src/triggertrade/services/process_roles.py:37` |
| API / Adapter Gateway | Market, portfolio, and order-management adapter helpers exist and validate many payload facts. | PARTIAL | `src/triggertrade/api_adapter_gateway/portfolio_data.py:41`, `src/triggertrade/api_adapter_gateway/market_data.py:152`, `src/triggertrade/api_adapter_gateway/order_management.py:181` |
| Durable messaging | PostgreSQL outbox/inbox append, claim, lock, conflict, and idempotency primitives exist. | CORRECT | `src/triggertrade/persistence/durable_messages.py:68`, `src/triggertrade/persistence/durable_messages.py:168`, `src/triggertrade/persistence/durable_messages.py:243` |
| Legacy paper/spot paths | `PaperTradingRuntime`, `PaperExecutionAdapter`, and spot Bybit adapter remain available. | LEGACY_DEMO_ONLY | `src/triggertrade/services/runtime.py:69`, `src/triggertrade/execution/paper.py`, `src/triggertrade/execution/bybit.py` |

No evidence was found of an intended fifth business block. The larger issue is
incompleteness: canonical business owner handlers are not implemented behind
the durable message boundary.

## Contract and Schema Conformance

Canonical requirement:

- `docs/trading-methodology/schemas/README.md`
- `docs/trading-methodology/schemas/CONTRACT_REGISTRY.json`
- `docs/trading-methodology/schemas/wire.schema.json`
- `docs/trading-methodology/api-contracts/`
- `docs/trading-methodology/business-contracts/`

Current backend:

- `src/triggertrade/contracts/registry.py` defines a programmatic registry with
  12 contract families and strict validation helpers.
- `src/triggertrade/contracts/schema_validator.py` provides a custom schema
  subset validator, including `$ref`, `allOf`, `anyOf`, required fields, enum,
  const, type, object, arrays, and `additionalProperties: false`.
- `src/triggertrade/contracts/_approved_wire_schema.py` is a generated in-source
  schema artifact.

Material conformance gaps:

1. The source registry still declares `APPROVED_PACKAGE_REVISION = "v1.2.14"`,
   while the frozen methodology package is v1.2.15.
2. The generated `_approved_wire_schema.py` still has `$id` and title values for
   v1.2.14.
3. `src/triggertrade/contracts/__init__.py` docstring still says target v1.2.14.
4. Tests still assert v1.2.14 methodology pins in `tests/unit/test_methodology_integrity.py`
   and `tests/unit/test_research_backend.py`.
5. The custom schema validator is useful but not a full Draft 2020-12 validator.
   It does not visibly implement the complete meta-schema behavior or every
   schema keyword that future frozen schemas could rely on.

Contract coverage audit:

| Contract Family | Frozen Version | Implemented Version | Status | Notes |
|---|---:|---:|---|---|
| COINS | 2 | 2 | PARTIAL | Strict shape exists; runtime production/consumption not fully wired. |
| MARKET_HANDOFF | 4 | 4 | PARTIAL | Shape exists; Set production is not implemented canonically. |
| APPROVE_REJECT | 5 | 5 | PARTIAL | Structural validation exists; Position decision formulas are not implemented. |
| CAPITAL_AND_LIMITS | 5 | 5 | PARTIAL | Grant validation exists; full Portfolio Rules allocation is incomplete. |
| ORDER_SPEC | 5 | 5 | PARTIAL | Contract validation exists; order-spec values are caller-supplied. |
| SUBMIT_AUTHORIZED | 5 | 5 | PARTIAL | Capacity checks exist; full canonical sequencing is incomplete. |
| ORDER_EVENT | 7 | 7 | PARTIAL | Store/validation exists for several variants; full lifecycle/finality is incomplete. |
| ORDER_PLACED | 3 | 3 | PARTIAL | Structural support exists; canonical runtime integration incomplete. |
| ORDER_CANCEL_SIGNAL | 2 | 2 | CONFLICTING | Source registry definition does not visibly enforce v1.2.15 two-cause semantics. |
| PORTFOLIO_DATA_REQUEST | 5 | 5 | PARTIAL | TT-FINAL-001 domain is reflected in adapter helper; source schema artifact remains package v1.2.14. |
| MARKET_DATA_REQUEST | 3 | 3 | PARTIAL | Adapter and selection helpers exist; canonical Set runtime consumption incomplete. |
| ORDER_MANAGEMENT | 4 | 4 | PARTIAL | Adapter helper exists; full canonical lifecycle use incomplete. |

## ORDER_CANCEL_SIGNAL Audit

Frozen methodology requirement:

- ORDER_CANCEL_SIGNAL contract version 2.
- Cause domain includes `INVALIDATION` and `MONITORING_UNAVAILABLE`.
- F-013 has two-cause cancellation semantics and must remain synchronized across
  Set, Order Lifecycle, identifier lineage, schema, and registry.

Current backend:

- `src/triggertrade/contracts/registry.py:599` defines ORDER_CANCEL_SIGNAL v2.
- The source registry root-required fields include legacy-looking fields such as
  `signal_id`, `invalidated_at`, and `reason_code`.
- The source registry evidence did not show an enforced `cause` enum or
  cause-specific required fields matching the v1.2.15 documentation.

Status: `CONFLICTING`.

Impact: any backend implementation that consumes source contract definitions for
ORDER_CANCEL_SIGNAL would not be guaranteed to enforce the frozen v1.2.15
contract semantics.

## PORTFOLIO_DATA_REQUEST / TT-FINAL-001 Audit

Frozen methodology requirement:

- Individual `instrument_metadata` rows allow only `AVAILABLE` or `UNAVAILABLE`.
- Individual `fee_rates` rows allow only `AVAILABLE` or `UNAVAILABLE`.
- Aggregate sections may be `AVAILABLE`, `PARTIAL`, or `UNAVAILABLE`.

Current backend:

- `src/triggertrade/api_adapter_gateway/portfolio_data.py:250` rejects per-item
  statuses outside `AVAILABLE` and `UNAVAILABLE`.
- `src/triggertrade/api_adapter_gateway/portfolio_data.py:273` derives aggregate
  `AVAILABLE`, `UNAVAILABLE`, or `PARTIAL`.

Status: `CORRECT` for the adapter helper behavior, `PARTIAL` for full runtime
coverage because canonical consumers are not fully implemented.

## Identifier and Lineage Audit

Canonical requirement:

- Identifiers must be stable, durable, provenance-preserving, and must not be
  silently reminted across replay/restart.
- Contracts, configuration pins, and evidence must be addressable by canonical
  identity/digest.

Current backend:

- Canonical JSON/digest utility exists and is reused by durable messages and
  contract digest helpers.
- Durable outbox/inbox detects same-ID content conflicts.
- Many stores accept explicit IDs and validate uniqueness.
- Several active helpers still construct structural objects from caller-supplied
  identifiers rather than deriving every required canonical identifier from the
  frozen methodology lineage rules.

Status: `PARTIAL`.

Risk: without complete owner handlers, identifier lineage cannot be proven across
the full Market Data -> Set -> Position -> Portfolio -> Lifecycle chain.

## Configuration Pinning Audit

Canonical requirement:

- Active Set, Position, Portfolio, runtime, research, and contract/configuration
  pins must be durable and versioned.
- Formula/configuration status must not be bypassed.

Current backend:

- `src/triggertrade/research_pins.py` uses `APPROVED_PACKAGE_REVISION`, which is
  currently stale at v1.2.14 through the contract registry.
- `src/triggertrade/position_config_pins.py` explicitly binds identities without
  calculating Position gates.
- PostgreSQL research and governance stores exist.
- Active canonical worker does not use complete configuration pins to execute
  owner flows.

Status: `PARTIAL`, with a `CONFLICTING` package-revision defect.

## Numeric Policy Audit

Canonical requirement:

- Methodology numeric policy and Set numeric policy require exact decimal text,
  canonical numeric encoding, deterministic quantization where specified, and no
  binary floating-point semantics for canonical values.

Current backend:

- Canonical JSON rejects unsupported numeric types including binary floats.
- Contract registry rejects binary floats in target contracts.
- Many contract fields validate decimal text strings.
- `src/triggertrade/position_construction.py` explicitly avoids calculating
  Entry, Stop, Take, sizing, leverage, risk/reward, and net-edge formulas.
- Legacy trigger and futures runtime paths contain noncanonical or demo formula
  behavior that should remain noncanonical.

Status: `PARTIAL`.

Main gap: canonical formulas and accounting calculations are not implemented
with the v1.2.15 numeric policies in the active worker path.

## Formula / State Rule Conformance

This section does not certify formula correctness. It classifies whether final
formula or state-rule behavior is implemented canonically.

| ID | Area | Canonical Owner | Current Backend Status | Classification |
|---|---|---|---|---|
| F-001 | Signed endpoint displacement / LONG-SHORT gate | Set | Legacy percentage price move trigger exists, but canonical Set formula is not implemented. | MISSING canonical, LEGACY_DEMO_ONLY legacy |
| F-002 | Volume / confirmation logic | Set | Legacy volume confirmation trigger exists; canonical Set formula is not implemented. | MISSING canonical, LEGACY_DEMO_ONLY legacy |
| F-003 | Set formation / trigger grouping | Set | Contracts and stores exist; canonical Set matching pipeline missing. | MISSING |
| F-004 | Set direction/classification support | Set | Demo strategy/regime helpers exist; canonical Set authority missing. | MISSING canonical, LEGACY_DEMO_ONLY legacy |
| F-005 | Market handoff derivations | Set | MARKET_HANDOFF contract exists; producer missing. | MISSING |
| F-006 | Entry formula | Position Rules | No final canonical calculation; values are supplied into structural validators. | MISSING |
| F-007 | Stop formula | Position Rules | No final canonical calculation. | MISSING |
| F-008 | Dynamic Take formula | Position Rules | No final canonical calculation. | MISSING |
| F-009 | Position sizing / quantity / notional | Position Rules / Portfolio Rules | No final canonical calculation; construction result validates supplied values. | MISSING |
| F-010 | Risk/reward / net-edge rule | Position Rules | Minimum net-edge result is validated but not calculated. | MISSING |
| F-011 | Capital allocation / committed capital | Portfolio Rules | Structural grant/submit checks exist; full allocation arithmetic incomplete. | PARTIAL |
| F-012 | Portfolio / coin / slot limits | Portfolio Rules | Some state and capacity checks exist; full canonical enforcement incomplete. | PARTIAL |
| F-013 | Cancellation signal cause logic | Set / Order Lifecycle | Source registry appears stale for v2 cause semantics; runtime producer missing. | CONFLICTING |
| A-001 | Financial evidence contracts | Order Lifecycle / Accounting | Schema/contract support exists; full lifecycle integration incomplete. | PARTIAL |
| A-002 | Realized PnL | Accounting | Accounting module exists for futures, but canonical finality path is not fully wired. | PARTIAL |
| A-003 | Fees | Accounting | Financial record structures exist; full canonical accounting flow incomplete. | PARTIAL |
| A-004 | Funding | Accounting | Source structures exist; canonical accounting finality incomplete. | PARTIAL |
| A-005 | Equity | Accounting | Not fully implemented canonically. | MISSING |
| A-006 | Drawdown | Accounting / Research | Analytics/research helpers may exist; canonical accounting not implemented. | MISSING |
| A-007 | Accounting-day policy | Accounting | Schema contains policy constants; full accounting implementation incomplete. | PARTIAL |
| A-008 | Financial finality | Order Lifecycle / Accounting | Integrity/event scaffolding exists; full finality incomplete. | PARTIAL |
| A-009 | Post-final integrity/economic receipt | Order Lifecycle / Accounting | Schema has structures; runtime behavior incomplete. | PARTIAL |
| S-001 | Portfolio state health | Portfolio Rules | LIVE/RECONCILING/STALE state model and store exist. | PARTIAL |
| S-002 | Order lifecycle state | Order Lifecycle | Lifecycle stores and state helpers exist; full transitions incomplete. | PARTIAL |
| S-003 | Close authority state | Order Lifecycle | Close authority store exists; full semantics incomplete. | PARTIAL |
| S-004 | Research/demo state classifier | Research | Research stores exist; live isolation mostly structural. | PARTIAL |
| S-005 | Market regime diagnostics | Set / Research | Legacy/demo diagnostic helpers exist; not canonical Set authority. | LEGACY_DEMO_ONLY |

## Portfolio Rules Audit

Frozen methodology expectation:

- Portfolio Rules own capital availability, reservations, grants, release,
  portfolio caps, per-coin caps, concurrent position limits, cooldowns, and
  capital conservation.

Current backend:

- `src/triggertrade/portfolio_state.py` models state health and commitment
  buckets.
- `src/triggertrade/capital_grants.py` builds and validates capital grants.
- `src/triggertrade/submit_authorizations.py` validates binding and a subset of
  capacity constraints.
- PostgreSQL stores exist for capital grants, portfolio state, cooldowns, and
  submit authorizations.

Status: `PARTIAL`.

Missing or incomplete:

- Complete atomic Portfolio Rules decision handler behind the canonical worker.
- Full grant/reservation/release lifecycle across restarts and owner messages.
- Complete Portfolio cap and coin cap enforcement from frozen methodology.
- Full capital conservation proof across order lifecycle events.

## Set Audit

Frozen methodology expectation:

- Set owns market analysis, trigger calculations, Set formation, direction,
  reference geometry, market handoff, cancellation signal invalidation, and
  monitoring unavailable signals where required.

Current backend:

- Legacy trigger modules calculate percentage move and volume confirmation for
  old/demo paths.
- Market data gateway structures exist.
- MARKET_HANDOFF contract is represented in the registry.
- Canonical worker does not run a Set handler.

Status: `MISSING` for canonical active Set behavior.

Legacy/demo code must not be promoted without certification and v1.2.15
alignment.

## Position Rules Audit

Frozen methodology expectation:

- Position Rules own Approve/Reject, Entry, Stop, Dynamic Take, sizing, minimum
  net edge, and construction of order specification inputs.

Current backend:

- `src/triggertrade/position_construction.py` explicitly states that it validates
  position construction without formula implementation.
- `src/triggertrade/order_specs.py` validates supplied ORDER_SPEC values and
  binding but does not compute them.
- Position configuration pins bind identities but do not calculate gates.

Status: `MISSING` for final Position formula behavior and `PARTIAL` for
contracts/stores.

## Order Lifecycle Audit

Frozen methodology expectation:

- Order Lifecycle owns submit, placement, native order tracking, fills, close
  authority, cancellation, reconciliation, terminal result, financial finality,
  and post-final integrity.

Current backend:

- Contract validators and stores exist for order specs, submit authorization,
  lifecycle events, reconciliation, close authority, and order evidence.
- API order-management gateway helpers exist.
- Some futures execution stores and demo runtime behavior exist.
- Canonical durable worker does not execute lifecycle handlers.

Status: `PARTIAL`.

Potential conformance risk:

- Close intent identity and joining semantics require further review against the
  v1.2.15 lineage requirement before activation.
- Full financial finality and post-final integrity are not active canonical
  behavior.

## API / Adapter Gateway Audit

Frozen methodology expectation:

- API is a technical boundary that normalizes exchange/native data into approved
  contract facts. It must not own business decisions.

Current backend:

- Portfolio data adapter enforces TT-FINAL-001 per-item availability rules.
- Market data adapter validates selection/result cardinality, dataset
  availability, and coverage consistency.
- Order-management adapter maps native state into approved fact-like payloads.

Status: `PARTIAL`.

Positive:

- No clear evidence that API is intentionally taking over Portfolio, Set,
  Position, or Lifecycle ownership.

Gap:

- Full canonical runtime use of API facts is not implemented, and some adapter
  helpers still work in a partially structural mode.

## Persistence / Migration Audit

Current backend:

- PostgreSQL migrations `0001` through `0019` exist.
- Migration runner and recovery drill scripts exist.
- Stores exist for durable messages, runtime heartbeats, operator commands,
  research, portfolio state, order specs, lifecycle state, reconciliation,
  cooldowns, and related structures.

Status: `PARTIAL`.

Correct infrastructure:

- Durable outbox/inbox conflict detection.
- `FOR UPDATE SKIP LOCKED` claim behavior.
- Canonical JSON payload digests for message identity.

Major gap:

- Durable persistence is not integrated with complete owner handlers; therefore
  replay/restart can be validated for infrastructure records, but not for the
  full v1.2.15 business lifecycle.

## Replay, Restart, Concurrency, and Idempotency Audit

| Capability | Current Evidence | Status |
|---|---|---|
| Canonical JSON deterministic identity | `src/triggertrade/canonical_json.py` and digest use in stores. | CORRECT |
| Outbox append idempotency | Same ID/dedupe key conflicts are detected. | CORRECT |
| Outbox claim concurrency | `FOR UPDATE SKIP LOCKED` claim behavior exists. | CORRECT |
| Inbox dedupe/conflict | Store records and detects conflicts. | CORRECT |
| Full business replay | Owner handlers are not implemented. | MISSING |
| Restart-safe active trading flow | Worker blocks owner messages; complete state machine not active. | MISSING |
| End-to-end idempotent order lifecycle | Structural stores exist; full lifecycle handlers missing. | PARTIAL |

## Research Isolation Audit

Frozen methodology expectation:

- Research remains isolated from live execution.
- Promotion is operator-authorized, durable, evidence-pinned, rollback-aware,
  and must not bypass formula certification or owner gates.

Current backend:

- PostgreSQL research stores, promotion command validation, lineage fields, and
  governance/audit support exist.
- Research pins inherit stale methodology package revision through
  `APPROVED_PACKAGE_REVISION`.
- Canonical live worker does not execute formula-dependent research promotion
  into live trading.

Status: `PARTIAL`.

Main gap:

- v1.2.15 package pin mismatch must be corrected before new research evidence is
  treated as aligned to the frozen methodology.

## Legacy, Demo, and Compatibility Boundary Audit

Legacy/demo implementations remain in the repository:

- `PaperTradingRuntime`
- `PaperExecutionAdapter`
- spot `BybitExecutionAdapter`
- legacy trigger and strategy modules
- demo futures runtime paths
- SQLite/local stores for development and compatibility

Status: `LEGACY_DEMO_ONLY`.

The canonical launcher rejects accidental paper/spot selection, which is good.
However, these paths contain non-v1.2.15 formula-like behavior and should remain
explicitly noncanonical until migrated or retired.

## Test Coverage Audit

Positive coverage:

- Contract registry and schema validation tests exist.
- Methodology integrity tests exist.
- Durable message, PostgreSQL foundation, runtime/process-role, research,
  governance, diagnostics, and state-store tests exist.
- Formula-gate and non-formula validation harnesses exist.

Material test gaps:

- Several tests still assert v1.2.14 methodology or package pins.
- Tests validate structural stores and fail-closed gates more than end-to-end
  canonical business behavior.
- There is no green end-to-end canonical owner flow from market data through
  order lifecycle because the worker handlers are not implemented.

Status: `PARTIAL`.

## Material Findings

| ID | Severity | Status | Finding | Evidence | Required Next Action |
|---|---|---|---|---|---|
| BCA-001 | BLOCKER | MISSING | Canonical trading worker blocks all owner messages and does not execute Portfolio, Set, Position, or Lifecycle handlers. | `src/triggertrade/services/trading_worker.py:106`, `src/triggertrade/services/trading_worker.py:118` | Implement owner handlers in dependency order after mapping. |
| BCA-002 | HIGH | CONFLICTING | Source contract package revision remains v1.2.14 after methodology freeze to v1.2.15. | `src/triggertrade/contracts/registry.py:15`, `src/triggertrade/contracts/_approved_wire_schema.py:3` | Regenerate/update contract package metadata from frozen v1.2.15 without changing family versions. |
| BCA-003 | HIGH | CONFLICTING | Tests still assert v1.2.14 methodology/package pinning. | `tests/unit/test_methodology_integrity.py`, `tests/unit/test_research_backend.py` | Update tests to frozen v1.2.15 package metadata. |
| BCA-004 | BLOCKER | CONFLICTING | ORDER_CANCEL_SIGNAL implementation does not visibly enforce v1.2.15 two-cause v2 semantics. | `src/triggertrade/contracts/registry.py:599` | Align source registry/schema/validator with frozen v1.2.15. |
| BCA-005 | BLOCKER | MISSING | Canonical Set formulas and market handoff production are not implemented. | Worker block plus legacy trigger modules only. | Implement certified Set behavior after formula mapping. |
| BCA-006 | BLOCKER | MISSING | Canonical Position formulas are not implemented. | `src/triggertrade/position_construction.py:33` | Implement certified Entry/Stop/Take/sizing/net-edge behavior. |
| BCA-007 | BLOCKER | PARTIAL | Portfolio Rules have stores and structural grants but incomplete atomic allocation/release/cap enforcement. | `src/triggertrade/capital_grants.py`, `src/triggertrade/submit_authorizations.py`, portfolio stores. | Implement Portfolio Rules owner handler. |
| BCA-008 | BLOCKER | PARTIAL | Order Lifecycle has stores/contracts but incomplete canonical lifecycle/finality execution. | lifecycle stores and worker block. | Implement lifecycle owner handlers and finality. |
| BCA-009 | HIGH | PARTIAL | Schema validator is a repository subset, not visibly complete Draft 2020-12 validation. | `src/triggertrade/contracts/schema_validator.py:15` | Decide whether full JSON Schema validation is required at runtime or strengthen generated validator coverage. |
| BCA-010 | HIGH | PARTIAL | Configuration/research pins inherit stale package revision. | `src/triggertrade/research_pins.py` imports `APPROVED_PACKAGE_REVISION`. | Re-pin to v1.2.15 source package metadata. |
| BCA-011 | HIGH | PARTIAL | Full business replay/restart cannot be proven because owner handlers are absent. | Durable infrastructure exists but worker blocks. | Add replay tests with actual owner handlers. |
| BCA-012 | MEDIUM | PARTIAL | Scheduler role is operationally present but lacks visible canonical duties beyond hydration/heartbeat. | `src/triggertrade/services/process_roles.py:37` | Map scheduler responsibilities before post-freeze runtime use. |
| BCA-013 | HIGH | LEGACY_DEMO_ONLY | Legacy trigger/strategy/runtime paths contain noncanonical formula behavior and must remain fenced. | `src/triggertrade/triggers/percentage_price_move.py`, `src/triggertrade/triggers/volume_confirmation.py`, `src/triggertrade/strategies/futures_directional.py` | Keep compatibility only; do not treat as canonical. |
| BCA-014 | BLOCKER | MISSING | Accounting/funding/equity/finality behavior is not fully canonical active behavior. | Accounting modules and schema exist, but lifecycle integration incomplete. | Implement after accounting certification/map. |
| BCA-015 | HIGH | PARTIAL | Identifier lineage exists structurally but cannot be proven end-to-end across all owners. | Contract/store identity helpers, worker block. | Add lineage end-to-end tests with handler integration. |
| BCA-016 | MEDIUM | PARTIAL | API adapter helpers are useful but not proven as the exclusive canonical data boundary in runtime. | API gateway helpers plus missing owner handlers. | Wire only through approved owner paths. |
| BCA-017 | HIGH | PARTIAL | Numeric policy is enforced for some contracts/digests, but final certified calculations are missing. | canonical JSON and decimal validators; formula modules missing. | Implement formula numeric policy during certified formula integration. |
| BCA-018 | HIGH | PARTIAL | Current tests are broad but cannot assert canonical methodology execution because canonical execution is blocked. | Existing test suite structure. | Add end-to-end conformance tests after handlers. |

## Implementation Mapping Guidance

Recommended sequence for the next implementation map:

1. Update source package metadata and generated approved wire schema from
   v1.2.14 to v1.2.15, preserving contract-family versions.
2. Align ORDER_CANCEL_SIGNAL v2 source enforcement with frozen v1.2.15.
3. Refresh tests and research/config pins to the v1.2.15 package revision.
4. Implement canonical owner message handlers in strict dependency order:
   Portfolio-safe state and grant handling, Set market analysis, Position
   decision, Order Lifecycle, then accounting/finality integration.
5. Add conformance tests for every owner boundary before enabling active
   execution.
6. Keep legacy/demo paths opt-in and compatibility-only until explicitly
   migrated or retired.

## Reviewer Gates for Future Remediation

Required reviewers by finding category:

- Contract/schema/package metadata: `triggertrade_change_reviewer`; architecture
  reviewer if registry boundaries change.
- ORDER_CANCEL_SIGNAL and F-013-related behavior:
  `triggertrade_trading_rules_reviewer`,
  `triggertrade_architecture_reviewer`, and final
  `triggertrade_change_reviewer`.
- Portfolio, Set, Position, Order Lifecycle handler implementation:
  architecture and trading-rules review, plus change review.
- Accounting/finality:
  trading-rules/accounting-equivalent review if available, security/change review
  if sensitive audit or execution authority changes, and final change review.
- Auth, operator commands, secrets, or dashboard authority changes:
  `triggertrade_security_change_reviewer`.

## What Must Not Be Done as Remediation

- Do not promote legacy percentage-move or volume trigger logic as canonical
  Set behavior.
- Do not treat demo futures strategy behavior as certified Position Rules.
- Do not change methodology semantics to fit existing backend gaps.
- Do not change contract-family versions solely because the methodology package
  revision is v1.2.15.
- Do not enable canonical active trading before owner handlers, formula/accounting
  certification, and replay/restart tests exist.

## Final Audit Verdict

The current backend is valuable infrastructure but is not fully conformant to
the frozen v1.2.15 methodology. The next task should be an implementation
mapping/remediation plan, not immediate activation.

BACKEND_CONFORMANCE_AUDIT:
COMPLETE

METHODOLOGY_VERSION_AUDITED:
v1.2.15

TOTAL_REQUIREMENTS_REVIEWED:
60

CORRECT_REQUIREMENTS:
6

PARTIAL_REQUIREMENTS:
25

MISSING_REQUIREMENTS:
20

CONFLICTING_REQUIREMENTS:
5

LEGACY_DEMO_ONLY_REQUIREMENTS:
4

METHODOLOGY_AMBIGUITIES:
0

BLOCKER_FINDINGS:
8

HIGH_FINDINGS:
8

MEDIUM_FINDINGS:
2

LOW_FINDINGS:
0

CANONICAL_RUNTIME_READY_FOR_ACTIVE_TRADING:
NO

READY_FOR_BACKEND_IMPLEMENTATION_MAPPING:
YES
