# TriggerTrade Backend Implementation Traceability

Authoritative inputs: `docs/trading-methodology/`, `docs/BACKEND_TARGET_MODEL.md`, `docs/BACKEND_IMPLEMENTATION_GAP_PLAN.md`, current implementation under `src/`, current tests under `tests/`, and runtime assets `Dockerfile`, `.dockerignore`, and `scripts/`. Archived methodology is not used as normative evidence.

## 1. Executive Traceability Summary

Total implementation IDs: 57. Total mapped gap IDs: 57. All 57 gap rows from `docs/BACKEND_IMPLEMENTATION_GAP_PLAN.md` are traced; missing gap IDs: none.

Count by transition: KEEP_AS_IS 3; EXTEND 5; REFACTOR 18; REPLACE 2; ISOLATE_LEGACY 4; REMOVE_FROM_CANONICAL_PATH 4; CREATE_NEW 19; REVIEW_NEEDED 2.

Count by wave: Wave 1 - Contract Foundation 7; Wave 2 - Durable Persistence 2; Wave 3 - Portfolio Core 7; Wave 4 - Set Core 7; Wave 5 - Position Core 6; Wave 6 - Lifecycle Core 12; Wave 7 - Research Alignment 4; Wave 8 - Runtime and Dashboard Separation 12.

Count by status: READY 11; NOT_STARTED 25; BLOCKED_FORMULA 13; BLOCKED_PERSISTENCE_DECISION 2; BLOCKED_TECHNICAL_DECISION 3; LEGACY_ONLY 0; ALREADY_ALIGNED 3.

Formula-gated implementation count: 14. Persistence-dependent implementation count: 51, including REQUIRED and PARTIAL rows. Technical-decision blocked count: 3. Already aligned count: 3. Legacy-only count: 0 because legacy rows require active isolation work before they can become noncanonical.

## Master Traceability Matrix

| Implementation ID | Gap ID | Canonical Requirement | Target Component | Current Code | Required Change | Transition | Wave | Formula Dependency | Persistence Dependency | Required Tests | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TT-BE-SYS-001 | GAP-SYS-001 | `docs/trading-methodology/schemas/README.md :: Schema Package`; `docs/BACKEND_TARGET_MODEL.md :: §5 Contract and Message Boundary Map` | durable_messaging; api_adapter_gateway | `src/triggertrade/execution/contracts.py`; `src/triggertrade/trigger_sets/contracts.py` | Introduce typed v1.2.14 contract models, versions, validators, and unknown-field rejection without wiring canonical runtime behavior. | CREATE_NEW | Wave 1 - Contract Foundation | NONE | PARTIAL | unit: contract construction; contract: canonical schema fixtures; persistence: digest fields accepted | READY |
| TT-BE-SYS-002 | GAP-SYS-002 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md :: P1`; `docs/trading-methodology/SYSTEM_PROTOCOLS.md :: P5`; `docs/BACKEND_TARGET_MODEL.md :: §9 Persistence Model Requirements` | durable_messaging | `src/triggertrade/persistence/message_store.py` | Create durable business outbox/inbox for inter-block messages with append, consume, dedupe, and replay semantics distinct from user notifications. | CREATE_NEW | Wave 2 - Durable Persistence | NONE | REQUIRED | persistence: append/consume durability; replay: duplicate message no duplicate effect; concurrency: competing consumers | BLOCKED_PERSISTENCE_DECISION |
| TT-BE-SYS-003 | GAP-SYS-003 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md :: P1`; `docs/BACKEND_TARGET_MODEL.md :: §2 Target Runtime Topology`; `docs/BACKEND_TARGET_MODEL.md :: §17 Cloud / Container Runtime Requirements` | trading worker; scheduler/orchestrator; web/API process | `src/triggertrade/services/futures_runtime.py`; `src/triggertrade/dashboard/__main__.py` | Refactor launch/runtime ownership so web, trading worker, scheduler, and recovery paths are explicit and hydrate from durable state. | REFACTOR | Wave 8 - Runtime and Dashboard Separation | NONE | PARTIAL | restart: worker hydration; integration: launcher roles; e2e: web plus worker smoke | NOT_STARTED |
| TT-BE-SYS-004 | GAP-SYS-004 | `docs/trading-methodology/schemas/NUMERIC_POLICY.md :: §6 Canonical Numeric Encoding`; `docs/BACKEND_TARGET_MODEL.md :: §7 Configuration Pinning Model` | configuration pinning support | hash helpers in `src/triggertrade/persistence/trading_rules_store.py`; `src/triggertrade/persistence/trigger_set_store.py` | Add shared canonical JSON and digest service used by contracts, pins, specs, and replay evidence. | CREATE_NEW | Wave 1 - Contract Foundation | NONE | PARTIAL | unit: stable serialization; contract: digest golden vectors; replay: changed key order same digest | READY |
| TT-BE-INFRA-001 | GAP-INFRA-001 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md :: P1`; `docs/BACKEND_TARGET_MODEL.md :: §9 Persistence Model Requirements`; `docs/BACKEND_TARGET_MODEL.md :: §10 Transaction and Concurrency Boundaries` | persistence layer | `src/triggertrade/persistence/*.py` | Refactor persistence behind durable transactional owner-state and unit-of-work boundaries suitable for concurrent workers and cloud restart. | REFACTOR | Wave 2 - Durable Persistence | NONE | REQUIRED | persistence: transaction rollback; concurrency: atomic uniqueness; restart: state survives process restart | BLOCKED_PERSISTENCE_DECISION |
| TT-BE-INFRA-002 | GAP-INFRA-002 | `docs/BACKEND_TARGET_MODEL.md :: §17 Cloud / Container Runtime Requirements` | web/API process; trading worker; scheduler/orchestrator | `Dockerfile`; `scripts/deploy-azure.ps1` | Extend container/deployment process model so target web and worker roles are deployable and independently health checked. | REFACTOR | Wave 8 - Runtime and Dashboard Separation | NONE | REQUIRED | integration: container starts selected role; e2e: web+worker deployment smoke | NOT_STARTED |
| TT-BE-INFRA-003 | GAP-INFRA-003 | `docs/BACKEND_TARGET_MODEL.md :: §17 Cloud / Container Runtime Requirements` | web/API process; persistence layer | `src/triggertrade/dashboard/__main__.py` | Extend `/healthz`-style readiness to include persistence reachability, worker safety state, and unavailable dependencies. | EXTEND | Wave 8 - Runtime and Dashboard Separation | NONE | PARTIAL | unit: readiness states; integration: dependency failure returns not-ready | READY |
| TT-BE-INFRA-004 | GAP-INFRA-004 | `docs/BACKEND_TARGET_MODEL.md :: §16 Web / API / Operator Boundary`; `docs/BACKEND_TARGET_MODEL.md :: §20 Technical Decisions NOT Determined by Methodology` | web/API process | `src/triggertrade/dashboard/__main__.py` | Replace process-local dashboard token as canonical operator authorization with a durable audited command-auth boundary after auth decision. | REFACTOR | Wave 8 - Runtime and Dashboard Separation | NONE | PARTIAL | unit: command auth; audit: operator identity on commands; restart: auth boundary not process-local | BLOCKED_TECHNICAL_DECISION |
| TT-BE-PR-001 | GAP-PR-001 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md :: §9`; `docs/trading-methodology/methodology/PORTFOLIO_RULES.md :: §14`; `docs/BACKEND_TARGET_MODEL.md :: §3 Portfolio Rules` | portfolio_state_service | `src/triggertrade/services/daily_loss.py`; `src/triggertrade/persistence/futures_position_store.py` | Create Portfolio-owned LIVE/RECONCILING/STALE state machine with four commitment buckets and durable replay recovery. | CREATE_NEW | Wave 3 - Portfolio Core | NONE | REQUIRED | state-machine: Portfolio health; persistence: bucket recovery; replay: stale evidence handling | NOT_STARTED |
| TT-BE-PR-002 | GAP-PR-002 | `docs/trading-methodology/business-contracts/COINS.md :: COINS v2`; `docs/BACKEND_TARGET_MODEL.md :: §5 Contract and Message Boundary Map` | portfolio_scope_projector; set_scope_service | current active set polling in `src/triggertrade/services/futures_runtime.py` | Create Portfolio-produced Coins OPEN/CLOSE revisions and Set intake, replacing current-pointer polling as canonical scope input. | CREATE_NEW | Wave 3 - Portfolio Core | NONE | REQUIRED | contract: Coins v2; replay: OPEN/CLOSE revisions; restart: Set resumes current scope | NOT_STARTED |
| TT-BE-PR-003 | GAP-PR-003 | `docs/trading-methodology/business-contracts/CAPITAL_AND_LIMITS.md :: CAPITAL_AND_LIMITS v5`; `docs/BACKEND_TARGET_MODEL.md :: §3 Portfolio Rules` | portfolio_grant_service | NONE | Create immutable Capital and Limits grant issuance with `capital_grant_id`, pin references, outbox publication, and duplicate approve idempotency. | CREATE_NEW | Wave 3 - Portfolio Core | NONE | REQUIRED | contract: grant schema; concurrency: duplicate APPROVE same grant; replay: grant immutable | NOT_STARTED |
| TT-BE-PR-004 | GAP-PR-004 | `docs/trading-methodology/business-contracts/SUBMIT_AUTHORIZED.md :: SUBMIT_AUTHORIZED v5`; `docs/BACKEND_TARGET_MODEL.md :: §10 Transaction and Concurrency Boundaries` | portfolio_hold_authorizer | `src/triggertrade/execution/futures.py::FuturesRiskManager` | Move SUBMISSION_HOLD and Submit Authorized ownership to Portfolio after construction and make hold+authorization atomic. | CREATE_NEW | Wave 3 - Portfolio Core | NONE | REQUIRED | concurrency: double hold blocked; contract: Submit Authorized; replay: unresolved hold recovers | NOT_STARTED |
| TT-BE-PR-005 | GAP-PR-005 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md :: §23`; `docs/BACKEND_TARGET_MODEL.md :: §15 Accounting / Financial Finality Target Model` | portfolio_accounting_service | `src/triggertrade/services/daily_loss.py`; `src/triggertrade/persistence/daily_loss_store.py` | Refactor daily loss to consume Lifecycle FINAL receipts once per accounting day instead of current accounting snapshots. | REFACTOR | Wave 3 - Portfolio Core | NONE | REQUIRED | unit: result-day latch; replay: duplicate receipt ignored; persistence: day survives restart | NOT_STARTED |
| TT-BE-PR-006 | GAP-PR-006 | `docs/trading-methodology/methodology/PORTFOLIO_RULES.md :: §24`; `docs/BACKEND_TARGET_MODEL.md :: §7 Configuration Pinning Model` | portfolio_accounting_service; portfolio_hold_authorizer | cooldown open intent IDs in `src/triggertrade/execution/futures.py` | Refactor cooldown into attempt-scoped acceptance pins owned by Portfolio and driven by Lifecycle acceptance/final signals. | REFACTOR | Wave 3 - Portfolio Core | NONE | REQUIRED | replay: acceptance cooldown survives config changes; state-machine: cooldown release | NOT_STARTED |
| TT-BE-SET-001 | GAP-SET-001 | `docs/trading-methodology/methodology/SET.md :: §2.1A`; `docs/BACKEND_TARGET_MODEL.md :: §3 Set` | set_scope_service | NONE | Create Set scope epoch model that resets on Coins OPEN formation epochs and persists epoch/cycle state. | CREATE_NEW | Wave 4 - Set Core | NONE | REQUIRED | state-machine: epoch reset; persistence: epoch recovery; contract: Coins intake | NOT_STARTED |
| TT-BE-SET-002 | GAP-SET-002 | `docs/trading-methodology/methodology/SET.md :: §10`; `docs/BACKEND_TARGET_MODEL.md :: §12 Formula Integration Boundaries` | set_trigger_engine | `src/triggertrade/triggers/percentage_price_move.py`; `src/triggertrade/triggers/volume_confirmation.py` | Refactor triggers into tri-state TRUE/FALSE/UNAVAILABLE evaluations with event continuity and formula-certified numeric behavior. | REFACTOR | Wave 4 - Set Core | MULTIPLE | REQUIRED | state-machine: tri-state continuity; replay: unavailable event retained; formula: golden vectors | BLOCKED_FORMULA |
| TT-BE-SET-003 | GAP-SET-003 | `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md :: MARKET_DATA_REQUEST v3`; `docs/BACKEND_TARGET_MODEL.md :: §14 API / Exchange Adapter Target Model` | set_market_data_selector; api_adapter_gateway | `src/triggertrade/market_data/bybit.py`; `src/triggertrade/exchanges/bybit.py` | Refactor market requests through v3 selectors, pages, coverage, source attribution, and stable replayable request identities. | REFACTOR | Wave 4 - Set Core | OTHER:SET_NUMERIC | REQUIRED | contract: selector/page schema; persistence: coverage page recovery; integration: Bybit public facts | BLOCKED_FORMULA |
| TT-BE-SET-004 | GAP-SET-004 | `docs/trading-methodology/methodology/SET.md :: §4`; `docs/BACKEND_TARGET_MODEL.md :: §6 Identifier and Lineage Model` | set_match_engine | signal/intent IDs in `src/triggertrade/strategies/futures_directional.py` | Create immutable `decision_cycle_id` and `set_result_id` MATCHED result lineage with direction formula pins. | CREATE_NEW | Wave 4 - Set Core | LONG_SHORT | REQUIRED | contract: Set result identity; replay: identical inputs same outcome; formula: direction vectors | BLOCKED_FORMULA |
| TT-BE-SET-005 | GAP-SET-005 | `docs/trading-methodology/business-contracts/MARKET_HANDOFF.md :: MARKET_HANDOFF v4`; `docs/BACKEND_TARGET_MODEL.md :: §5 Contract and Message Boundary Map` | set_match_engine | strategy context in `src/triggertrade/strategies/context.py` | Create frozen Market Handoff v4 from Set to Position with wire references, duplicated scalar bindings, and immutable source links. | CREATE_NEW | Wave 4 - Set Core | MULTIPLE | REQUIRED | contract: Handoff fixtures; replay: handoff immutability; persistence: reference bindings | BLOCKED_FORMULA |
| TT-BE-SET-006 | GAP-SET-006 | `docs/trading-methodology/methodology/SET.md :: Part IV`; `docs/trading-methodology/business-contracts/ORDER_CANCEL_SIGNAL.md :: ORDER_CANCEL_SIGNAL v2`; `docs/BACKEND_TARGET_MODEL.md :: §3 Set` | set_monitor_service | NONE | Create Set-owned pending monitor for frozen invalidation and canonical cancellation signals synchronized with Lifecycle order placement. | CREATE_NEW | Wave 4 - Set Core | MULTIPLE | REQUIRED | state-machine: pending monitor; contract: cancel signal; replay: delayed placement/cancel ordering | BLOCKED_FORMULA |
| TT-BE-POS-001 | GAP-POS-001 | `docs/trading-methodology/business-contracts/APPROVE_REJECT.md :: APPROVE_REJECT v5`; `docs/BACKEND_TARGET_MODEL.md :: §3 Position Rules` | position_decision_service | `src/triggertrade/strategies/futures_directional.py`; `src/triggertrade/execution/futures.py` | Replace canonical demo strategy/risk direct-intent sequence with Position-owned initial APPROVE/REJECT before Portfolio grant. | REPLACE | Wave 5 - Position Core | MULTIPLE | REQUIRED | state-machine: initial decision; contract: APPROVE/REJECT; formula: decision vectors | BLOCKED_FORMULA |
| TT-BE-POS-002 | GAP-POS-002 | `docs/trading-methodology/methodology/POSITION_RULES.md :: §1B`; `docs/BACKEND_TARGET_MODEL.md :: §7 Configuration Pinning Model` | position_decision_service | `src/triggertrade/rules/trading.py`; `src/triggertrade/persistence/trading_rules_store.py` | Create Position config pin at first Market Handoff intake, bound to `decision_cycle_id` and immutable through construction. | CREATE_NEW | Wave 5 - Position Core | NONE | REQUIRED | persistence: pin creation; replay: current config change ignored; contract: pin references | NOT_STARTED |
| TT-BE-POS-003 | GAP-POS-003 | `docs/trading-methodology/methodology/POSITION_RULES.md :: §14`; `docs/BACKEND_TARGET_MODEL.md :: §3 Position Rules` | position_construction_service | sizing in `src/triggertrade/services/futures_runtime.py`; `src/triggertrade/execution/position_lifecycle.py` | Create post-grant construction result with `construction_result_id`, outcome, grant binding, and formula-owned calculations. | CREATE_NEW | Wave 5 - Position Core | MULTIPLE | REQUIRED | state-machine: construction outcomes; contract: grant binding; formula: construction vectors | BLOCKED_FORMULA |
| TT-BE-POS-004 | GAP-POS-004 | `docs/trading-methodology/business-contracts/ORDER_SPEC.md :: ORDER_SPEC v5`; `docs/BACKEND_TARGET_MODEL.md :: §5 Contract and Message Boundary Map` | position_construction_service | `src/triggertrade/execution/futures.py::FuturesTradeIntent` | Refactor current trade intent into immutable Order Spec v5 with digest, provenance, duplicated scalars, and lineage bindings. | REFACTOR | Wave 5 - Position Core | MULTIPLE | REQUIRED | contract: Order Spec; unit: digest equality; persistence: spec immutable | BLOCKED_FORMULA |
| TT-BE-POS-005 | GAP-POS-005 | `docs/trading-methodology/methodology/POSITION_RULES.md :: Parts II-IV`; `docs/BACKEND_TARGET_MODEL.md :: §12 Formula Integration Boundaries` | position_formula_engine | fixed helpers in `src/triggertrade/execution/position_lifecycle.py`; `src/triggertrade/rules/trading.py` | Add formula interfaces for LONG/SHORT, Entry, Stop, and Dynamic Take; final implementations wait for certification. | CREATE_NEW | Wave 5 - Position Core | ENTRY | PARTIAL | unit: interface contracts now; formula: golden vectors after approval | BLOCKED_FORMULA |
| TT-BE-POS-006 | GAP-POS-006 | `docs/trading-methodology/methodology/POSITION_RULES.md :: §6`; `docs/BACKEND_TARGET_MODEL.md :: §3 Position Rules` | position_construction_service; lifecycle_start_gate | `src/triggertrade/execution/position_lifecycle.py::PositionLifecycleService.open_position` | Remove direct order submission from canonical Position path; Position may only emit construction/spec outputs for Lifecycle. | REMOVE_FROM_CANONICAL_PATH | Wave 5 - Position Core | NONE | PARTIAL | contract: no API side effects; module-boundary: Position cannot import execution adapter | READY |
| TT-BE-OL-001 | GAP-OL-001 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md :: §3`; `docs/BACKEND_TARGET_MODEL.md :: §5 Contract and Message Boundary Map` | lifecycle_start_gate | `src/triggertrade/execution/futures.py::FuturesExecutionService` | Create Lifecycle start gate that requires matching Order Spec and Submit Authorized before any exchange side effect. | CREATE_NEW | Wave 6 - Lifecycle Core | NONE | REQUIRED | state-machine: start gate; contract: spec/auth matching; concurrency: duplicate start blocked | NOT_STARTED |
| TT-BE-OL-002 | GAP-OL-002 | `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md :: §5`; `docs/BACKEND_TARGET_MODEL.md :: §10 Transaction and Concurrency Boundaries` | lifecycle_submission_service | `src/triggertrade/execution/futures.py::futures_client_order_id`; `src/triggertrade/persistence/futures_execution_store.py` | Extend submission intent persistence so target client ID, lineage, digest, and uncertain dispatch cutpoints are recorded before side effects. | EXTEND | Wave 6 - Lifecycle Core | NONE | REQUIRED | restart: crash before/after submit; idempotency: duplicate client ID; integration: adapter not called twice | NOT_STARTED |
| TT-BE-OL-003 | GAP-OL-003 | `docs/trading-methodology/business-contracts/ORDER_EVENT.md :: ORDER_EVENT v7`; `docs/BACKEND_TARGET_MODEL.md :: §5 Contract and Message Boundary Map` | lifecycle_entry_ledger | `src/triggertrade/persistence/futures_execution_store.py`; `src/triggertrade/persistence/futures_accounting_store.py` | Create strict Order Event v7 event ledger and map native/execution/accounting facts into immutable lifecycle events. | CREATE_NEW | Wave 6 - Lifecycle Core | NONE | REQUIRED | contract: event variants; replay: duplicate events deduped; persistence: append-only facts | NOT_STARTED |
| TT-BE-OL-004 | GAP-OL-004 | `docs/trading-methodology/business-contracts/ORDER_PLACED.md :: ORDER_PLACED v3`; `docs/BACKEND_TARGET_MODEL.md :: §5 Contract and Message Boundary Map` | lifecycle_entry_ledger; set_monitor_service | NONE | Create Lifecycle-to-Set Order Placed and terminal synchronization messages for pending monitor continuity. | CREATE_NEW | Wave 6 - Lifecycle Core | NONE | REQUIRED | contract: Order Placed; replay: Set monitor resumes; integration: placement sync | NOT_STARTED |
| TT-BE-OL-005 | GAP-OL-005 | `docs/trading-methodology/business-contracts/ORDER_CANCEL_SIGNAL.md :: ORDER_CANCEL_SIGNAL v2`; `docs/BACKEND_TARGET_MODEL.md :: §10 Transaction and Concurrency Boundaries` | lifecycle_submission_service; set_monitor_service | manual/service cancel paths in `src/triggertrade/execution/position_lifecycle.py` | Refactor cancellation into governed Set invalidation signal handling with idempotent Lifecycle application. | REFACTOR | Wave 6 - Lifecycle Core | NONE | REQUIRED | contract: cancel signal; idempotency: duplicate cancel; state-machine: accepted/too-late cancellation | NOT_STARTED |
| TT-BE-OL-006 | GAP-OL-006 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md :: P5`; `docs/BACKEND_TARGET_MODEL.md :: §10 Transaction and Concurrency Boundaries` | lifecycle_close_authority | close intent logic in `src/triggertrade/execution/position_lifecycle.py` | Refactor close handling into durable acquire-or-join close intent ledger with active uniqueness and child order lineage. | REFACTOR | Wave 6 - Lifecycle Core | NONE | REQUIRED | concurrency: two close requests join; restart: active close recovers; state-machine: child lineage | NOT_STARTED |
| TT-BE-OL-007 | GAP-OL-007 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md :: P6`; `docs/BACKEND_TARGET_MODEL.md :: §19 Target Backend Invariants` | lifecycle_reconciliation_service; lifecycle_financial_finality | `mark_closed` paths in `src/triggertrade/execution/position_lifecycle.py` | Replace weak close marking with six-condition CLOSED predicate and terminal finalization guard. | REPLACE | Wave 6 - Lifecycle Core | OTHER:ACCOUNTING | REQUIRED | state-machine: six predicates; replay: cannot close early; accounting: finality prerequisite | BLOCKED_FORMULA |
| TT-BE-OL-008 | GAP-OL-008 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md :: P9`; `docs/trading-methodology/SYSTEM_PROTOCOLS.md :: P15`; `docs/BACKEND_TARGET_MODEL.md :: §13 Research / Backtest / Demo Target Model` | lifecycle_reconciliation_service | NONE | Create native observation, resolution, allocation, and reconciliation evidence ledger with provenance and replay behavior. | CREATE_NEW | Wave 6 - Lifecycle Core | NONE | REQUIRED | persistence: evidence immutable; replay: delayed/out-of-order evidence; reconciliation: resolution audit | NOT_STARTED |
| TT-BE-OL-009 | GAP-OL-009 | `docs/trading-methodology/business-contracts/ORDER_EVENT.md :: Financial result`; `docs/BACKEND_TARGET_MODEL.md :: §15 Accounting / Financial Finality Target Model` | lifecycle_financial_finality | `src/triggertrade/accounting/futures.py`; `src/triggertrade/services/futures_accounting_bridge.py` | Refactor accounting bridge into Lifecycle-owned FINAL result production with evidence coverage, currency, allocation, and Portfolio receipt. | REFACTOR | Wave 6 - Lifecycle Core | OTHER:ACCOUNTING | REQUIRED | accounting: final result fixtures; replay: receipt once; persistence: evidence coverage certificate | BLOCKED_FORMULA |
| TT-BE-OL-010 | GAP-OL-010 | `docs/trading-methodology/SYSTEM_PROTOCOLS.md :: T01`; `docs/trading-methodology/SYSTEM_PROTOCOLS.md :: Y01`; `docs/BACKEND_TARGET_MODEL.md :: §19 Target Backend Invariants` | lifecycle_financial_finality | NONE | Create post-final integrity incident/quarantine path and receipt fence for facts arriving after finality. | CREATE_NEW | Wave 6 - Lifecycle Core | NONE | REQUIRED | state-machine: post-final incident; replay: final facts immutable; audit: quarantine recorded | NOT_STARTED |
| TT-BE-API-001 | GAP-API-001 | `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md :: MARKET_DATA_REQUEST v3`; `docs/BACKEND_TARGET_MODEL.md :: §14 API / Exchange Adapter Target Model` | api_adapter_gateway; set_market_data_selector | `src/triggertrade/exchanges/bybit.py`; `src/triggertrade/market_data/bybit.py` | Refactor Bybit public market access into strict factual Market Data Request/response envelopes with coverage and source lineage. | REFACTOR | Wave 4 - Set Core | OTHER:SET_NUMERIC | REQUIRED | contract: API envelope; integration: Bybit public facts; replay: cached page identity | BLOCKED_FORMULA |
| TT-BE-API-002 | GAP-API-002 | `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md :: PORTFOLIO_DATA_REQUEST v5`; `docs/BACKEND_TARGET_MODEL.md :: §14 API / Exchange Adapter Target Model` | api_adapter_gateway; portfolio_state_service | wallet/position parsing in `src/triggertrade/services/futures_runtime.py`; `src/triggertrade/exchanges/bybit.py` | Refactor account, equity, instrument, and fee facts into coherent Portfolio Data Request envelopes with source attribution. | REFACTOR | Wave 3 - Portfolio Core | NONE | REQUIRED | contract: portfolio facts; integration: Bybit account parsing; restart: stale/unavailable state handling | NOT_STARTED |
| TT-BE-API-003 | GAP-API-003 | `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md :: ORDER_MANAGEMENT v4`; `docs/BACKEND_TARGET_MODEL.md :: §14 API / Exchange Adapter Target Model` | api_adapter_gateway; lifecycle_submission_service | `src/triggertrade/execution/bybit_futures.py` | Refactor order create/cancel/query/fill calls into strict Order Management facts, hard facts, financial facts, and provenance envelopes. | REFACTOR | Wave 6 - Lifecycle Core | NONE | REQUIRED | contract: order API facts; integration: Bybit demo order events; idempotency: retry handling | NOT_STARTED |
| TT-BE-API-004 | GAP-API-004 | `docs/trading-methodology/api-contracts/NATIVE_FACT_PROFILE.md :: NATIVE_FACT_PROFILE`; `docs/BACKEND_TARGET_MODEL.md :: §14 API / Exchange Adapter Target Model` | api_adapter_gateway | Bybit demo smoke tests in `tests/integration/test_bybit_demo_futures_lifecycle_smoke.py`; `src/triggertrade/execution/bybit_futures.py` | Review and document Bybit native fact conformance evidence; keep runtime uncertified paths gated until profile gaps are resolved. | REVIEW_NEEDED | Wave 8 - Runtime and Dashboard Separation | NONE | PARTIAL | integration: native profile smoke; contract: field coverage evidence; review: conformance report | READY |
| TT-BE-RES-001 | GAP-RES-001 | `docs/BACKEND_TARGET_MODEL.md :: §13 Research / Backtest / Demo Target Model`; `docs/trading-methodology/IDENTIFIER_LINEAGE.md :: Identifier Lineage` | research_run_service | `src/triggertrade/persistence/research_store.py`; `src/triggertrade/backtest/models.py` | Extend research run identity with exact target version, config, contract, source, and digest pins. | EXTEND | Wave 7 - Research Alignment | NONE | PARTIAL | persistence: run pins; replay: current config change ignored; e2e: research run immutable | READY |
| TT-BE-RES-002 | GAP-RES-002 | `docs/BACKEND_TARGET_MODEL.md :: §13 Research / Backtest / Demo Target Model`; `docs/BACKEND_TARGET_MODEL.md :: §11 Restart / Replay / Recovery Model` | research_run_service | `src/triggertrade/backtest/engine.py`; `src/triggertrade/backtest/simulator.py` | Refactor backtest execution to replay target Portfolio, Set, Position, Lifecycle, and API fact contracts rather than current runtime pieces. | REFACTOR | Wave 7 - Research Alignment | MULTIPLE | PARTIAL | replay: four-block deterministic run; formula: golden vectors; e2e: isolated research replay | BLOCKED_FORMULA |
| TT-BE-RES-003 | GAP-RES-003 | `docs/BACKEND_TARGET_MODEL.md :: §13 Research / Backtest / Demo Target Model` | research_run_service; api_adapter_gateway | `src/triggertrade/services/research.py::ResearchDemoIsolation` | Extend demo isolation so research/demo runs cannot emit live side effects and use explicitly scoped adapters/state. | EXTEND | Wave 7 - Research Alignment | NONE | PARTIAL | integration: no live adapter called; persistence: isolated run state; e2e: demo safety | READY |
| TT-BE-RES-004 | GAP-RES-004 | `docs/BACKEND_TARGET_MODEL.md :: §13 Research / Backtest / Demo Target Model`; `docs/BACKEND_TARGET_MODEL.md :: §20 Technical Decisions NOT Determined by Methodology` | research_run_service | `src/triggertrade/services/research.py::ResearchService.request_make_active` | Review promotion/make-active governance against approved docs and keep current promotion-like actions noncanonical until resolved. | REVIEW_NEEDED | Wave 7 - Research Alignment | NONE | PARTIAL | review: governance decision; contract: command audit if retained; e2e: no accidental active mutation | BLOCKED_TECHNICAL_DECISION |
| TT-BE-SYS-005 | GAP-SYS-005 | `docs/BACKEND_TARGET_MODEL.md :: §16 Web / API / Operator Boundary` | web/API process | `src/triggertrade/dashboard/__main__.py`; `src/triggertrade/dashboard/read_model.py` | Refactor dashboard into read-model and idempotent command boundary; remove direct business ownership from route handlers. | REFACTOR | Wave 8 - Runtime and Dashboard Separation | NONE | PARTIAL | unit: command handlers; integration: route delegates; audit: command IDs persisted | NOT_STARTED |
| TT-BE-SYS-006 | GAP-SYS-006 | `docs/BACKEND_TARGET_MODEL.md :: §1 Executive Target Model`; `docs/BACKEND_TARGET_MODEL.md :: §17 Cloud / Container Runtime Requirements` | trading worker | `src/triggertrade/execution/bybit.py`; `src/triggertrade/execution/paper.py`; `src/triggertrade/services/runtime.py` | Isolate spot execution and PaperTradingRuntime from canonical launcher and keep them compatibility/demo-only. | ISOLATE_LEGACY | Wave 1 - Contract Foundation | NONE | NONE | contract: module boundary; smoke: legacy opt-in still imports | READY |
| TT-BE-SYS-007 | GAP-SYS-007 | `docs/BACKEND_TARGET_MODEL.md :: §1 Executive Target Model` | trading worker | `src/triggertrade/services/futures_runtime.py`; `src/triggertrade/strategies/futures_directional.py` | Isolate current futures demo lane so it cannot be mistaken for target canonical Set/Position/Lifecycle runtime. | ISOLATE_LEGACY | Wave 8 - Runtime and Dashboard Separation | NONE | PARTIAL | module-boundary: canonical launcher excludes demo lane; e2e: demo path opt-in | NOT_STARTED |
| TT-BE-SYS-008 | GAP-SYS-008 | `docs/BACKEND_TARGET_MODEL.md :: §17 Cloud / Container Runtime Requirements` | testing/ops support | `scripts/bybit_demo_futures_smoke.py`; `scripts/triggertrade_demo_soak.py`; `scripts/paper_runtime_smoke.py` | Keep smoke scripts opt-in and prevent them from serving as canonical validation or production entry points. | ISOLATE_LEGACY | Wave 1 - Contract Foundation | NONE | NONE | script guards: opt-in flags; docs lint: smoke not canonical | READY |
| TT-BE-SYS-009 | GAP-SYS-009 | `docs/BACKEND_TARGET_MODEL.md :: §17 Cloud / Container Runtime Requirements` | persistence layer | runtime/history state label from gap plan; filesystem backups via `src/triggertrade/services/backup_restore.py` | Refactor durable runtime state away from local filesystem dependence; keep files only as explicit cache/export artifacts. | REFACTOR | Wave 8 - Runtime and Dashboard Separation | NONE | REQUIRED | restart: container rebuild no state loss; persistence: cache rebuild; ops: backup/export tests | NOT_STARTED |
| TT-BE-SYS-010 | GAP-SYS-010 | `docs/BACKEND_TARGET_MODEL.md :: §18 Target Testing Model` | testing/verification | `tests/unit`; `tests/integration`; `tests/contract` | Extend tests from current behavior coverage into contract, state-machine, persistence, concurrency, replay, restart, formula, reconciliation, and E2E taxonomy. | EXTEND | Wave 1 - Contract Foundation | MULTIPLE | PARTIAL | meta: test taxonomy present; unit/contract: first fixtures; later: wave-specific suites | READY |
| TT-BE-SYS-011 | GAP-SYS-011 | `docs/BACKEND_TARGET_MODEL.md :: §3 Business Block Technical Projection`; `docs/BACKEND_TARGET_MODEL.md :: §5 Contract and Message Boundary Map` | trading worker; position_decision_service | `src/triggertrade/strategies/buy_candidate.py`; `src/triggertrade/risk/manager.py` | Remove old trigger/strategy/risk direct path from canonical launch while keeping compatibility code if tests need it. | REMOVE_FROM_CANONICAL_PATH | Wave 1 - Contract Foundation | NONE | NONE | module-boundary: canonical path cannot import old strategy/risk; smoke: legacy opt-in | READY |
| TT-BE-SYS-012 | GAP-SYS-012 | `docs/BACKEND_TARGET_MODEL.md :: §16 Web / API / Operator Boundary` | web/API process | process-local token in `src/triggertrade/dashboard/__main__.py` | Remove direct dashboard token as canonical auth mechanism once durable operator auth boundary is chosen; keep current token only legacy/local. | REMOVE_FROM_CANONICAL_PATH | Wave 8 - Runtime and Dashboard Separation | NONE | PARTIAL | auth: restart-safe command authorization; audit: operator command facts | BLOCKED_TECHNICAL_DECISION |
| TT-BE-SYS-013 | GAP-SYS-013 | `docs/BACKEND_TARGET_MODEL.md :: §9 Persistence Model Requirements` | persistence layer; lifecycle_entry_ledger | `src/triggertrade/persistence/execution_store.py`; `src/triggertrade/persistence/futures_execution_store.py` | Isolate legacy execution stores as migration/read-history sources and prevent them from being canonical Lifecycle truth. | ISOLATE_LEGACY | Wave 6 - Lifecycle Core | NONE | PARTIAL | migration: legacy read fixtures; module-boundary: canonical lifecycle store selected | NOT_STARTED |
| TT-BE-INFRA-005 | GAP-INFRA-005 | `docs/BACKEND_TARGET_MODEL.md :: §17 Cloud / Container Runtime Requirements` | web/API process; trading worker | `scripts/deploy-azure.ps1`; `Dockerfile` | Remove dashboard-only Azure deployment path from canonical runtime once target worker/web deployment exists. | REMOVE_FROM_CANONICAL_PATH | Wave 8 - Runtime and Dashboard Separation | NONE | REQUIRED | deploy: worker/web smoke; config: role env validation; health: readiness gates | NOT_STARTED |
| TT-BE-INFRA-006 | GAP-INFRA-006 | `docs/BACKEND_TARGET_MODEL.md :: §3 Business Block Technical Projection`; `docs/BACKEND_TARGET_MODEL.md :: §14 API / Exchange Adapter Target Model`; `docs/BACKEND_TARGET_MODEL.md :: §15 Accounting / Financial Finality Target Model` | api_adapter_gateway; lifecycle_financial_finality | `src/triggertrade/accounting/futures.py`; `src/triggertrade/instruments/catalog.py`; `src/triggertrade/exchanges/bybit.py` | Preserve mature pure utilities behind target-compatible wrappers; do not rewrite arithmetic, catalog parsing, or Bybit transport unnecessarily. | KEEP_AS_IS | Wave 8 - Runtime and Dashboard Separation | NONE | NONE | unit: current regression tests remain green; contract: wrapper compatibility when added | ALREADY_ALIGNED |
| TT-BE-INFRA-007 | GAP-INFRA-007 | `docs/BACKEND_TARGET_MODEL.md :: §17 Cloud / Container Runtime Requirements` | persistence layer; ops support | `src/triggertrade/services/backup_restore.py`; `src/triggertrade/services/db_integrity_audit.py` | Preserve current backup/integrity audit concepts until database migration, then adapt rather than discard. | KEEP_AS_IS | Wave 8 - Runtime and Dashboard Separation | NONE | NONE | unit: existing backup/integrity tests; later: DB migration adaptation tests | ALREADY_ALIGNED |
| TT-BE-INFRA-008 | GAP-INFRA-008 | `docs/trading-methodology/README.md :: IMPLEMENTATION SPECIFICATION BASELINE`; `docs/BACKEND_TARGET_MODEL.md :: Target Source` | approved methodology baseline | `docs/trading-methodology/*` | Preserve approved methodology docs read-only as canonical source for implementation traceability and validation. | KEEP_AS_IS | Wave 1 - Contract Foundation | NONE | NONE | docs: link/integrity checks; traceability: no archived normative refs | ALREADY_ALIGNED |

## 2. Gap Coverage Audit

| Gap ID | Implementation IDs | Coverage | Notes |
|---|---|---|---|
| GAP-SYS-001 | TT-BE-SYS-001 | FULL | Contract foundation row. |
| GAP-SYS-002 | TT-BE-SYS-002 | FULL | Durable outbox/inbox row. |
| GAP-SYS-003 | TT-BE-SYS-003 | FULL | Runtime topology row. |
| GAP-SYS-004 | TT-BE-SYS-004 | FULL | Canonical JSON/digest row. |
| GAP-INFRA-001 | TT-BE-INFRA-001 | FULL | Database persistence row. |
| GAP-INFRA-002 | TT-BE-INFRA-002 | FULL | Container runtime row. |
| GAP-INFRA-003 | TT-BE-INFRA-003 | FULL | Health/readiness row. |
| GAP-INFRA-004 | TT-BE-INFRA-004 | FULL | Secrets/auth row. |
| GAP-PR-001 | TT-BE-PR-001 | FULL | Portfolio state row. |
| GAP-PR-002 | TT-BE-PR-002 | FULL | Coins row. |
| GAP-PR-003 | TT-BE-PR-003 | FULL | Grants row. |
| GAP-PR-004 | TT-BE-PR-004 | FULL | Holds row. |
| GAP-PR-005 | TT-BE-PR-005 | FULL | Daily loss row. |
| GAP-PR-006 | TT-BE-PR-006 | FULL | Cooldown row. |
| GAP-SET-001 | TT-BE-SET-001 | FULL | Scope epoch row. |
| GAP-SET-002 | TT-BE-SET-002 | FULL | Trigger contract row. |
| GAP-SET-003 | TT-BE-SET-003 | FULL | Market selector row. |
| GAP-SET-004 | TT-BE-SET-004 | FULL | MATCHED result row. |
| GAP-SET-005 | TT-BE-SET-005 | FULL | Market Handoff row. |
| GAP-SET-006 | TT-BE-SET-006 | FULL | Pending monitor row. |
| GAP-POS-001 | TT-BE-POS-001 | FULL | Initial decision row. |
| GAP-POS-002 | TT-BE-POS-002 | FULL | Position pin row. |
| GAP-POS-003 | TT-BE-POS-003 | FULL | Construction row. |
| GAP-POS-004 | TT-BE-POS-004 | FULL | Order Spec row. |
| GAP-POS-005 | TT-BE-POS-005 | FULL | Formula boundary row. |
| GAP-POS-006 | TT-BE-POS-006 | FULL | Direct execution removal row. |
| GAP-OL-001 | TT-BE-OL-001 | FULL | Lifecycle start gate row. |
| GAP-OL-002 | TT-BE-OL-002 | FULL | Submission intent row. |
| GAP-OL-003 | TT-BE-OL-003 | FULL | Order Event row. |
| GAP-OL-004 | TT-BE-OL-004 | FULL | Order Placed row. |
| GAP-OL-005 | TT-BE-OL-005 | FULL | Cancel signal row. |
| GAP-OL-006 | TT-BE-OL-006 | FULL | Close authority row. |
| GAP-OL-007 | TT-BE-OL-007 | FULL | CLOSED predicate row. |
| GAP-OL-008 | TT-BE-OL-008 | FULL | Native observations row. |
| GAP-OL-009 | TT-BE-OL-009 | FULL | Financial finality row. |
| GAP-OL-010 | TT-BE-OL-010 | FULL | Post-final integrity row. |
| GAP-API-001 | TT-BE-API-001 | FULL | Market API row. |
| GAP-API-002 | TT-BE-API-002 | FULL | Portfolio API row. |
| GAP-API-003 | TT-BE-API-003 | FULL | Order API row. |
| GAP-API-004 | TT-BE-API-004 | FULL | Native profile row. |
| GAP-RES-001 | TT-BE-RES-001 | FULL | Research pins row. |
| GAP-RES-002 | TT-BE-RES-002 | FULL | Target replay row. |
| GAP-RES-003 | TT-BE-RES-003 | FULL | Demo isolation row. |
| GAP-RES-004 | TT-BE-RES-004 | FULL | Promotion governance row. |
| GAP-SYS-005 | TT-BE-SYS-005 | FULL | Dashboard boundary row. |
| GAP-SYS-006 | TT-BE-SYS-006 | FULL | Legacy spot/paper row. |
| GAP-SYS-007 | TT-BE-SYS-007 | FULL | Demo futures pipeline row. |
| GAP-SYS-008 | TT-BE-SYS-008 | FULL | Smoke scripts row. |
| GAP-SYS-009 | TT-BE-SYS-009 | FULL | Filesystem cache row. |
| GAP-SYS-010 | TT-BE-SYS-010 | FULL | Test taxonomy row. |
| GAP-SYS-011 | TT-BE-SYS-011 | FULL | Old strategy/risk path row. |
| GAP-SYS-012 | TT-BE-SYS-012 | FULL | Dashboard token row. |
| GAP-SYS-013 | TT-BE-SYS-013 | FULL | Legacy execution stores row. |
| GAP-INFRA-005 | TT-BE-INFRA-005 | FULL | Azure deploy row. |
| GAP-INFRA-006 | TT-BE-INFRA-006 | FULL | Mature utilities row. |
| GAP-INFRA-007 | TT-BE-INFRA-007 | FULL | Backup/integrity row. |
| GAP-INFRA-008 | TT-BE-INFRA-008 | FULL | Methodology baseline row. |

## 3. Requirement Coverage Audit

| Canonical Area | Requirement Group | Implementation IDs | Coverage |
|---|---|---|---|
| Portfolio Rules | State, Coins, grants, holds, daily loss, cooldown | TT-BE-PR-001, TT-BE-PR-002, TT-BE-PR-003, TT-BE-PR-004, TT-BE-PR-005, TT-BE-PR-006, TT-BE-API-002 | FULL |
| Set | Scope epochs, triggers, selectors, MATCHED, handoff, pending monitor | TT-BE-SET-001, TT-BE-SET-002, TT-BE-SET-003, TT-BE-SET-004, TT-BE-SET-005, TT-BE-SET-006, TT-BE-API-001 | FULL |
| Position Rules | Initial decision, pins, construction, Order Spec, formulas, no direct execution | TT-BE-POS-001, TT-BE-POS-002, TT-BE-POS-003, TT-BE-POS-004, TT-BE-POS-005, TT-BE-POS-006 | FULL |
| Order Lifecycle | Start gate, submission, events, placement sync, cancel, close, CLOSED, reconciliation, finality | TT-BE-OL-001, TT-BE-OL-002, TT-BE-OL-003, TT-BE-OL-004, TT-BE-OL-005, TT-BE-OL-006, TT-BE-OL-007, TT-BE-OL-008, TT-BE-OL-009, TT-BE-OL-010, TT-BE-API-003 | FULL |
| API | Market, portfolio, order, native profile facts | TT-BE-API-001, TT-BE-API-002, TT-BE-API-003, TT-BE-API-004 | FULL |
| Accounting | FINAL result, receipts, daily loss, source coverage | TT-BE-OL-009, TT-BE-PR-005, TT-BE-INFRA-006 | FULL |
| Research / Backtest / Demo | Pins, replay, demo isolation, promotion review | TT-BE-RES-001, TT-BE-RES-002, TT-BE-RES-003, TT-BE-RES-004, TT-BE-SYS-007 | FULL |
| Cross-system | Contracts, durable messaging, canonical JSON, tests | TT-BE-SYS-001, TT-BE-SYS-002, TT-BE-SYS-004, TT-BE-SYS-010 | FULL |
| Runtime / cloud | Worker/web/scheduler, container, health, auth, filesystem independence | TT-BE-SYS-003, TT-BE-INFRA-002, TT-BE-INFRA-003, TT-BE-INFRA-004, TT-BE-SYS-009, TT-BE-INFRA-005 | FULL |
| Persistence | Durable owner state, outbox/inbox, legacy store isolation | TT-BE-INFRA-001, TT-BE-SYS-002, TT-BE-SYS-013 | FULL |
| Replay / restart / reconciliation | Message replay, state recovery, native observations, post-final incidents | TT-BE-SYS-002, TT-BE-INFRA-001, TT-BE-OL-008, TT-BE-OL-010 | FULL |
| Configuration pinning | Canonical JSON, Position pins, Set/Portfolio lineage, research pins | TT-BE-SYS-004, TT-BE-POS-002, TT-BE-SET-001, TT-BE-RES-001 | FULL |
| Identifier lineage | Cycle, result, grant, construction, order, fill, close, receipt, research IDs | TT-BE-SET-004, TT-BE-PR-003, TT-BE-POS-003, TT-BE-POS-004, TT-BE-OL-002, TT-BE-OL-006, TT-BE-OL-009, TT-BE-RES-001 | FULL |

## 4. Target Component Coverage

| Target Component | Implementation IDs | Existing Current Equivalent | Final Transition |
|---|---|---|---|
| web/API process | TT-BE-SYS-003, TT-BE-SYS-005, TT-BE-INFRA-003, TT-BE-INFRA-004, TT-BE-SYS-012 | `src/triggertrade/dashboard/__main__.py` | REFACTOR |
| trading worker | TT-BE-SYS-003, TT-BE-SYS-006, TT-BE-SYS-007, TT-BE-SYS-011 | `src/triggertrade/services/futures_runtime.py` | REFACTOR |
| research/backtest worker | TT-BE-RES-001, TT-BE-RES-002, TT-BE-RES-003, TT-BE-RES-004 | `src/triggertrade/backtest/*`; `src/triggertrade/services/research.py` | EXTEND/REFACTOR |
| scheduler/orchestrator | TT-BE-SYS-003, TT-BE-SYS-002 | polling loops in `src/triggertrade/services/futures_runtime.py` | CREATE_NEW/REFACTOR |
| exchange adapter | TT-BE-API-001, TT-BE-API-002, TT-BE-API-003, TT-BE-API-004, TT-BE-INFRA-006 | `src/triggertrade/exchanges/bybit.py`; `src/triggertrade/execution/bybit_futures.py` | REFACTOR |
| persistence layer | TT-BE-INFRA-001, TT-BE-SYS-002, TT-BE-SYS-009, TT-BE-SYS-013 | `src/triggertrade/persistence/*.py` | REFACTOR |
| portfolio_state_service | TT-BE-PR-001, TT-BE-API-002 | daily loss/accounting snapshots | CREATE_NEW |
| portfolio_scope_projector | TT-BE-PR-002 | current set polling | CREATE_NEW |
| portfolio_grant_service | TT-BE-PR-003 | none material | CREATE_NEW |
| portfolio_hold_authorizer | TT-BE-PR-004 | `FuturesRiskManager` | CREATE_NEW |
| portfolio_accounting_service | TT-BE-PR-005, TT-BE-PR-006 | `daily_loss.py`; accounting stores | REFACTOR |
| set_scope_service | TT-BE-SET-001, TT-BE-PR-002 | active set lookup | CREATE_NEW |
| set_market_data_selector | TT-BE-SET-003, TT-BE-API-001 | direct candle calls | REFACTOR |
| set_trigger_engine | TT-BE-SET-002 | trigger modules | REFACTOR |
| set_match_engine | TT-BE-SET-004, TT-BE-SET-005 | strategy context/signal IDs | CREATE_NEW |
| set_monitor_service | TT-BE-SET-006, TT-BE-OL-004, TT-BE-OL-005 | none material | CREATE_NEW |
| position_decision_service | TT-BE-POS-001, TT-BE-POS-002 | demo strategy/risk | REPLACE/CREATE_NEW |
| position_construction_service | TT-BE-POS-003, TT-BE-POS-004, TT-BE-POS-006 | position lifecycle/risk helpers | CREATE_NEW/REFACTOR |
| position_formula_engine | TT-BE-POS-005, TT-BE-SET-002 | fixed helpers/triggers | CREATE_NEW/REFACTOR |
| lifecycle_start_gate | TT-BE-OL-001 | execution service risk input | CREATE_NEW |
| lifecycle_submission_service | TT-BE-OL-002, TT-BE-OL-005, TT-BE-API-003 | futures execution service/adapter | EXTEND/REFACTOR |
| lifecycle_entry_ledger | TT-BE-OL-003, TT-BE-OL-004 | futures execution store | CREATE_NEW/EXTEND |
| lifecycle_close_authority | TT-BE-OL-006 | close intent strings | REFACTOR |
| lifecycle_reconciliation_service | TT-BE-OL-007, TT-BE-OL-008 | reconcile methods | CREATE_NEW/REPLACE |
| lifecycle_financial_finality | TT-BE-OL-009, TT-BE-OL-010, TT-BE-INFRA-006 | accounting bridge/pure funcs | REFACTOR |
| api_adapter_gateway | TT-BE-API-001, TT-BE-API-002, TT-BE-API-003, TT-BE-API-004 | Bybit client/adapters/catalog | REFACTOR |
| durable_messaging | TT-BE-SYS-001, TT-BE-SYS-002 | user `MessageStore` only | CREATE_NEW |
| research_run_service | TT-BE-RES-001, TT-BE-RES-002, TT-BE-RES-003, TT-BE-RES-004 | research/backtest services | EXTEND/REFACTOR |

## 5. Current Code Impact Map

| Current Module / Area | Implementation IDs | Intended Fate | Primary Wave |
|---|---|---|---|
| `src/triggertrade/accounting/futures.py` | TT-BE-INFRA-006, TT-BE-OL-009 | PRESERVE | Wave 8 - Runtime and Dashboard Separation |
| `src/triggertrade/backtest/*` | TT-BE-RES-001, TT-BE-RES-002 | REFACTOR | Wave 7 - Research Alignment |
| `src/triggertrade/dashboard/__main__.py` | TT-BE-SYS-005, TT-BE-INFRA-003, TT-BE-INFRA-004, TT-BE-SYS-012 | REFACTOR | Wave 8 - Runtime and Dashboard Separation |
| `src/triggertrade/dashboard/read_model.py` | TT-BE-SYS-005 | REFACTOR | Wave 8 - Runtime and Dashboard Separation |
| `src/triggertrade/exchanges/bybit.py` | TT-BE-API-001, TT-BE-API-002, TT-BE-INFRA-006 | REFACTOR | Wave 4 - Set Core |
| `src/triggertrade/execution/bybit.py` | TT-BE-SYS-006 | LEGACY | Wave 1 - Contract Foundation |
| `src/triggertrade/execution/bybit_futures.py` | TT-BE-API-003, TT-BE-API-004 | REFACTOR | Wave 6 - Lifecycle Core |
| `src/triggertrade/execution/contracts.py` | TT-BE-SYS-001 | REFACTOR | Wave 1 - Contract Foundation |
| `src/triggertrade/execution/futures.py` | TT-BE-PR-004, TT-BE-POS-001, TT-BE-OL-001, TT-BE-OL-002 | REFACTOR | Wave 6 - Lifecycle Core |
| `src/triggertrade/execution/paper.py` | TT-BE-SYS-006 | LEGACY | Wave 1 - Contract Foundation |
| `src/triggertrade/execution/position_lifecycle.py` | TT-BE-POS-003, TT-BE-POS-004, TT-BE-POS-006, TT-BE-OL-005, TT-BE-OL-006, TT-BE-OL-007 | REFACTOR | Wave 5 - Position Core |
| `src/triggertrade/instruments/catalog.py` | TT-BE-INFRA-006, TT-BE-API-002 | PRESERVE | Wave 8 - Runtime and Dashboard Separation |
| `src/triggertrade/market_data/*` | TT-BE-SET-003, TT-BE-API-001 | REFACTOR | Wave 4 - Set Core |
| `src/triggertrade/persistence/*.py` | TT-BE-INFRA-001, TT-BE-SYS-002, TT-BE-SYS-013 | REFACTOR | Wave 2 - Durable Persistence |
| `src/triggertrade/risk/manager.py` | TT-BE-SYS-011, TT-BE-POS-001 | REMOVE_FROM_CANONICAL_PATH | Wave 1 - Contract Foundation |
| `src/triggertrade/rules/trading.py` | TT-BE-POS-002, TT-BE-POS-005 | EXTEND | Wave 5 - Position Core |
| `src/triggertrade/services/backup_restore.py` | TT-BE-INFRA-007, TT-BE-SYS-009 | PRESERVE | Wave 8 - Runtime and Dashboard Separation |
| `src/triggertrade/services/db_integrity_audit.py` | TT-BE-INFRA-007 | PRESERVE | Wave 8 - Runtime and Dashboard Separation |
| `src/triggertrade/services/futures_runtime.py` | TT-BE-SYS-003, TT-BE-SYS-007, TT-BE-SET-003, TT-BE-POS-003 | REFACTOR | Wave 8 - Runtime and Dashboard Separation |
| `src/triggertrade/services/research.py` | TT-BE-RES-001, TT-BE-RES-003, TT-BE-RES-004 | EXTEND | Wave 7 - Research Alignment |
| `src/triggertrade/services/runtime.py` | TT-BE-SYS-006 | LEGACY | Wave 1 - Contract Foundation |
| `src/triggertrade/strategies/buy_candidate.py` | TT-BE-SYS-011 | REMOVE_FROM_CANONICAL_PATH | Wave 1 - Contract Foundation |
| `src/triggertrade/strategies/futures_directional.py` | TT-BE-POS-001, TT-BE-SYS-007 | REPLACE | Wave 5 - Position Core |
| `src/triggertrade/triggers/*` | TT-BE-SET-002 | REFACTOR | Wave 4 - Set Core |
| `src/triggertrade/trigger_sets/contracts.py` | TT-BE-SYS-001, TT-BE-SET-001 | EXTEND | Wave 1 - Contract Foundation |
| `scripts/*` | TT-BE-SYS-008, TT-BE-INFRA-005 | LEGACY | Wave 1 - Contract Foundation |
| `Dockerfile` | TT-BE-INFRA-002, TT-BE-INFRA-005 | REFACTOR | Wave 8 - Runtime and Dashboard Separation |
| `docs/trading-methodology/*` | TT-BE-INFRA-008 | PRESERVE | Wave 1 - Contract Foundation |

## 6. Wave Execution Map

### Wave 1 - Contract Foundation

| Order | Implementation ID | Objective | Prerequisites | Exit Proof |
|---|---|---|---|---|
| 1 | TT-BE-INFRA-008 | Preserve approved methodology as read-only source. | none | Link/integrity check passes. |
| 2 | TT-BE-SYS-004 | Add canonical JSON/digest service. | TT-BE-INFRA-008 | Digest vector tests pass. |
| 3 | TT-BE-SYS-001 | Add typed target contracts and validators. | TT-BE-SYS-004 | Contract fixtures validate. |
| 4 | TT-BE-SYS-006 | Isolate spot/paper compatibility paths. | TT-BE-SYS-001 | Canonical boundary test passes. |
| 5 | TT-BE-SYS-011 | Remove old strategy/risk direct path from canonical launch. | TT-BE-SYS-001 | Canonical launcher cannot select old path. |
| 6 | TT-BE-SYS-008 | Fence smoke scripts as opt-in validation only. | none | Smoke scripts remain manual and noncanonical. |
| 7 | TT-BE-SYS-010 | Start target test taxonomy scaffolding. | TT-BE-SYS-001 | First contract/state test groups exist. |

### Wave 2 - Durable Persistence

| Order | Implementation ID | Objective | Prerequisites | Exit Proof |
|---|---|---|---|---|
| 1 | TT-BE-INFRA-001 | Introduce durable transaction/unit-of-work foundation. | PostgreSQL/ORM decision; TT-BE-SYS-001 | Transaction and concurrency tests pass. |
| 2 | TT-BE-SYS-002 | Add durable outbox/inbox. | TT-BE-INFRA-001 | Replay/dedupe tests pass. |
| 3 | TT-BE-SYS-013 | Fence legacy execution stores as noncanonical truth. | TT-BE-INFRA-001 | Canonical lifecycle store selection proven. |
| 4 | TT-BE-SYS-009 | Move durable runtime state away from local filesystem. | TT-BE-INFRA-001 | Restart tests without local files pass. |
| 5 | TT-BE-INFRA-007 | Preserve/adapt backup integrity concepts. | TT-BE-INFRA-001 | Backup/integrity regression remains green. |

### Wave 3 - Portfolio Core

| Order | Implementation ID | Objective | Prerequisites | Exit Proof |
|---|---|---|---|---|
| 1 | TT-BE-API-002 | Add Portfolio API factual envelopes. | TT-BE-SYS-001, TT-BE-INFRA-001 | Portfolio fact contract tests pass. |
| 2 | TT-BE-PR-001 | Create Portfolio state machine. | TT-BE-API-002, TT-BE-SYS-002 | Bucket/state replay tests pass. |
| 3 | TT-BE-PR-002 | Emit Coins OPEN/CLOSE revisions. | TT-BE-PR-001 | Coins replay tests pass. |
| 4 | TT-BE-PR-003 | Issue Capital and Limits grants. | TT-BE-PR-001 | Grant idempotency tests pass. |
| 5 | TT-BE-PR-004 | Authorize SUBMISSION_HOLD. | TT-BE-PR-003, TT-BE-POS-003 interface | Hold concurrency tests pass. |
| 6 | TT-BE-PR-006 | Implement acceptance cooldown pins. | TT-BE-PR-004, TT-BE-OL-002 signals | Cooldown replay tests pass. |
| 7 | TT-BE-PR-005 | Implement daily loss receipts. | TT-BE-OL-009 | Receipt/day latch tests pass. |

### Wave 4 - Set Core

| Order | Implementation ID | Objective | Prerequisites | Exit Proof |
|---|---|---|---|---|
| 1 | TT-BE-SET-001 | Create Set scope epochs. | TT-BE-PR-002 | Epoch recovery tests pass. |
| 2 | TT-BE-SET-003 | Add Market Data Request selector/page model. | TT-BE-SET-001, TT-BE-API-001 | Selector coverage tests pass. |
| 3 | TT-BE-API-001 | Refactor market facts envelope. | TT-BE-SYS-001 | API contract tests pass. |
| 4 | TT-BE-SET-002 | Refactor trigger tri-state events. | formula approval; TT-BE-SET-003 | Trigger replay tests pass. |
| 5 | TT-BE-SET-004 | Create MATCHED result lineage. | formula approval; TT-BE-SET-002 | Set result replay tests pass. |
| 6 | TT-BE-SET-005 | Emit Market Handoff v4. | TT-BE-SET-004 | Handoff contract fixtures pass. |
| 7 | TT-BE-SET-006 | Add pending monitor. | TT-BE-SET-005, TT-BE-OL-004 | Monitor/cancel ordering tests pass. |

### Wave 5 - Position Core

| Order | Implementation ID | Objective | Prerequisites | Exit Proof |
|---|---|---|---|---|
| 1 | TT-BE-POS-002 | Pin Position configuration at handoff intake. | TT-BE-SET-005 | Pin replay tests pass. |
| 2 | TT-BE-POS-006 | Remove direct Position submission. | TT-BE-OL-001 interface | Boundary tests pass. |
| 3 | TT-BE-POS-005 | Add formula boundary interfaces. | TT-BE-POS-002 | Interface tests pass before formulas. |
| 4 | TT-BE-POS-001 | Implement initial APPROVE/REJECT. | formula approval; TT-BE-SET-005 | Decision tests pass. |
| 5 | TT-BE-POS-003 | Implement construction result. | TT-BE-PR-003, formula approval | Construction tests pass. |
| 6 | TT-BE-POS-004 | Emit immutable Order Spec. | TT-BE-POS-003 | Spec digest tests pass. |

### Wave 6 - Lifecycle Core

| Order | Implementation ID | Objective | Prerequisites | Exit Proof |
|---|---|---|---|---|
| 1 | TT-BE-OL-001 | Add Order Spec plus Submit Authorized start gate. | TT-BE-POS-004, TT-BE-PR-004 | Start-gate tests pass. |
| 2 | TT-BE-API-003 | Add Order Management factual envelopes. | TT-BE-OL-001 | Adapter contract tests pass. |
| 3 | TT-BE-OL-002 | Extend submission intent persistence. | TT-BE-OL-001, TT-BE-API-003 | Crash cutpoint tests pass. |
| 4 | TT-BE-OL-003 | Add Order Event v7 ledger. | TT-BE-OL-002 | Event replay tests pass. |
| 5 | TT-BE-OL-004 | Emit Order Placed sync. | TT-BE-OL-003 | Set sync tests pass. |
| 6 | TT-BE-OL-005 | Apply cancel signals idempotently. | TT-BE-SET-006, TT-BE-OL-004 | Cancel idempotency tests pass. |
| 7 | TT-BE-OL-006 | Add close acquire-or-join ledger. | TT-BE-OL-003 | Close concurrency tests pass. |
| 8 | TT-BE-OL-008 | Add native observation/resolution ledger. | TT-BE-API-003 | Reconciliation tests pass. |
| 9 | TT-BE-OL-009 | Produce FINAL financial result. | accounting certification; TT-BE-OL-008 | Finality tests pass. |
| 10 | TT-BE-OL-007 | Enforce six-condition CLOSED predicate. | TT-BE-OL-009 | CLOSED state-machine tests pass. |
| 11 | TT-BE-OL-010 | Add post-final integrity incidents. | TT-BE-OL-009 | Quarantine/incident tests pass. |

### Wave 7 - Research Alignment

| Order | Implementation ID | Objective | Prerequisites | Exit Proof |
|---|---|---|---|---|
| 1 | TT-BE-RES-001 | Extend research pins. | TT-BE-SYS-001 | Research pin tests pass. |
| 2 | TT-BE-RES-003 | Enforce demo/research isolation. | TT-BE-RES-001 | No-live-side-effect tests pass. |
| 3 | TT-BE-RES-004 | Review promotion governance. | target governance decision | Decision recorded; noncanonical gates remain safe. |
| 4 | TT-BE-RES-002 | Replay target blocks. | formulas; TT-BE-SET-005, TT-BE-POS-004, TT-BE-OL-003 | Deterministic replay tests pass. |

### Wave 8 - Runtime and Dashboard Separation

| Order | Implementation ID | Objective | Prerequisites | Exit Proof |
|---|---|---|---|---|
| 1 | TT-BE-API-004 | Complete native profile review. | TT-BE-API-003 | Conformance evidence accepted. |
| 2 | TT-BE-INFRA-006 | Preserve reusable utilities. | wrapper points from Waves 3-6 | Regression tests remain green. |
| 3 | TT-BE-INFRA-004 | Resolve durable operator auth. | auth technical decision | Command auth tests pass. |
| 4 | TT-BE-SYS-012 | Remove local token from canonical auth. | TT-BE-INFRA-004 | Restart-safe auth tests pass. |
| 5 | TT-BE-SYS-005 | Move dashboard behind read/command boundaries. | TT-BE-INFRA-004, target stores | Dashboard API tests pass. |
| 6 | TT-BE-SYS-003 | Finalize worker/scheduler/web topology. | TT-BE-SYS-002, target blocks | Worker restart tests pass. |
| 7 | TT-BE-SYS-007 | Isolate current demo futures pipeline. | TT-BE-SYS-003 | Canonical launcher excludes demo path. |
| 8 | TT-BE-INFRA-003 | Extend health/readiness. | TT-BE-SYS-003, persistence | Dependency-aware health tests pass. |
| 9 | TT-BE-INFRA-002 | Make container roles deployable. | TT-BE-SYS-003 | Container role smoke tests pass. |
| 10 | TT-BE-INFRA-005 | Remove dashboard-only Azure path from canonical deployment. | TT-BE-INFRA-002 | Deployment smoke tests pass. |

## 7. Dependency Graph

| Implementation ID | Depends On | Blocks |
|---|---|---|
| TT-BE-INFRA-008 | none | TT-BE-SYS-004, TT-BE-SYS-001 |
| TT-BE-SYS-004 | TT-BE-INFRA-008 | TT-BE-SYS-001, TT-BE-POS-004, TT-BE-RES-001 |
| TT-BE-SYS-001 | TT-BE-SYS-004 | most contract consumers |
| TT-BE-INFRA-001 | PostgreSQL/ORM decision, TT-BE-SYS-001 | TT-BE-SYS-002, owner state, Lifecycle |
| TT-BE-SYS-002 | TT-BE-INFRA-001 | TT-BE-PR-001, TT-BE-SYS-003, TT-BE-OL-001 |
| TT-BE-API-002 | TT-BE-SYS-001, TT-BE-INFRA-001 | TT-BE-PR-001 |
| TT-BE-PR-001 | TT-BE-SYS-002, TT-BE-API-002 | TT-BE-PR-002, TT-BE-PR-003 |
| TT-BE-PR-002 | TT-BE-PR-001 | TT-BE-SET-001 |
| TT-BE-PR-003 | TT-BE-PR-001 | TT-BE-PR-004, TT-BE-POS-003 |
| TT-BE-SET-001 | TT-BE-PR-002 | TT-BE-SET-003 |
| TT-BE-API-001 | TT-BE-SYS-001 | TT-BE-SET-003 |
| TT-BE-SET-003 | TT-BE-SET-001, TT-BE-API-001 | TT-BE-SET-002 |
| TT-BE-SET-002 | formula approval, TT-BE-SET-003 | TT-BE-SET-004 |
| TT-BE-SET-004 | formula approval, TT-BE-SET-002 | TT-BE-SET-005 |
| TT-BE-SET-005 | TT-BE-SET-004 | TT-BE-POS-002, TT-BE-POS-001, TT-BE-RES-002 |
| TT-BE-POS-002 | TT-BE-SET-005 | TT-BE-POS-005 |
| TT-BE-POS-005 | formula approval | TT-BE-POS-001, TT-BE-POS-003 |
| TT-BE-POS-001 | TT-BE-SET-005, formula approval | TT-BE-PR-003 |
| TT-BE-POS-003 | TT-BE-PR-003, formula approval | TT-BE-PR-004, TT-BE-POS-004 |
| TT-BE-POS-004 | TT-BE-POS-003 | TT-BE-OL-001 |
| TT-BE-PR-004 | TT-BE-POS-003 | TT-BE-OL-001 |
| TT-BE-OL-001 | TT-BE-POS-004, TT-BE-PR-004 | TT-BE-API-003, TT-BE-OL-002 |
| TT-BE-API-003 | TT-BE-OL-001 | TT-BE-OL-002, TT-BE-OL-008 |
| TT-BE-OL-002 | TT-BE-OL-001, TT-BE-API-003 | TT-BE-OL-003, TT-BE-PR-006 |
| TT-BE-OL-003 | TT-BE-OL-002 | TT-BE-OL-004, TT-BE-OL-006 |
| TT-BE-OL-004 | TT-BE-OL-003 | TT-BE-SET-006 |
| TT-BE-SET-006 | TT-BE-SET-005, TT-BE-OL-004 | TT-BE-OL-005 |
| TT-BE-OL-005 | TT-BE-SET-006 | none |
| TT-BE-OL-006 | TT-BE-OL-003 | TT-BE-OL-008 |
| TT-BE-OL-008 | TT-BE-API-003 | TT-BE-OL-009 |
| TT-BE-OL-009 | TT-BE-OL-008, accounting certification | TT-BE-OL-007, TT-BE-OL-010, TT-BE-PR-005 |
| TT-BE-OL-007 | TT-BE-OL-009 | terminal Lifecycle completion |
| TT-BE-OL-010 | TT-BE-OL-009 | terminal integrity completion |
| TT-BE-RES-001 | TT-BE-SYS-001 | TT-BE-RES-003, TT-BE-RES-002 |
| TT-BE-RES-003 | TT-BE-RES-001 | safe research/demo execution |
| TT-BE-RES-002 | target block contracts and formulas | research alignment |
| TT-BE-SYS-003 | TT-BE-SYS-002, target blocks | TT-BE-INFRA-002, TT-BE-INFRA-003, TT-BE-SYS-007 |
| TT-BE-INFRA-004 | auth technical decision | TT-BE-SYS-012, TT-BE-SYS-005 |
| TT-BE-SYS-005 | TT-BE-INFRA-004, target read models | operator UI separation |
| TT-BE-INFRA-002 | TT-BE-SYS-003 | TT-BE-INFRA-005 |

## 8. PostgreSQL Traceability

| Implementation ID | PostgreSQL Relation | Reason |
|---|---|---|
| TT-BE-SYS-001 | PRE_POSTGRES | Contracts can be built before physical DB. |
| TT-BE-SYS-004 | PRE_POSTGRES | Canonical serialization can be pure. |
| TT-BE-SYS-006 | PRE_POSTGRES | Legacy fences do not require DB. |
| TT-BE-SYS-008 | PRE_POSTGRES | Script guards do not require DB. |
| TT-BE-SYS-011 | PRE_POSTGRES | Launcher/import fences do not require DB. |
| TT-BE-SYS-010 | CROSSES_POSTGRES_BOUNDARY | Test taxonomy starts now and expands after DB. |
| TT-BE-INFRA-008 | PRE_POSTGRES | Read-only docs preservation. |
| TT-BE-INFRA-006 | PRE_POSTGRES | Preserved utilities are DB-independent. |
| TT-BE-INFRA-007 | CROSSES_POSTGRES_BOUNDARY | Current backup/integrity remains, later DB adaptation needed. |
| TT-BE-RES-001 | CROSSES_POSTGRES_BOUNDARY | Pin model can start, durable run state finishes after DB. |
| TT-BE-API-004 | CROSSES_POSTGRES_BOUNDARY | Review can start; evidence persistence depends on DB. |
| TT-BE-INFRA-001 | REQUIRES_POSTGRES | Durable transactional owner state foundation. |
| TT-BE-SYS-002 | REQUIRES_POSTGRES | Business outbox/inbox must be durable and concurrent. |
| TT-BE-PR-001 | REQUIRES_POSTGRES | Portfolio mutable state and buckets must be transactional. |
| TT-BE-PR-002 | REQUIRES_POSTGRES | Coins revisions must be durable/replayable. |
| TT-BE-PR-003 | REQUIRES_POSTGRES | Grants require idempotent durable identity. |
| TT-BE-PR-004 | REQUIRES_POSTGRES | Holds and authorization need atomic uniqueness. |
| TT-BE-PR-005 | REQUIRES_POSTGRES | Receipts/day latch require exactly-once posting. |
| TT-BE-PR-006 | REQUIRES_POSTGRES | Cooldown pins require durable attempt lineage. |
| TT-BE-SET-001 | REQUIRES_POSTGRES | Scope epochs must survive restart. |
| TT-BE-SET-002 | REQUIRES_POSTGRES | Trigger events require durable continuity. |
| TT-BE-SET-003 | REQUIRES_POSTGRES | Selector/page coverage must persist. |
| TT-BE-SET-004 | REQUIRES_POSTGRES | Set result identities must persist. |
| TT-BE-SET-005 | REQUIRES_POSTGRES | Handoff references must persist. |
| TT-BE-SET-006 | REQUIRES_POSTGRES | Pending monitor state must persist. |
| TT-BE-POS-001 | REQUIRES_POSTGRES | Decisions must be replay-safe. |
| TT-BE-POS-002 | REQUIRES_POSTGRES | Config pins must persist. |
| TT-BE-POS-003 | REQUIRES_POSTGRES | Construction results must persist. |
| TT-BE-POS-004 | REQUIRES_POSTGRES | Order Specs must be immutable durable facts. |
| TT-BE-POS-005 | CROSSES_POSTGRES_BOUNDARY | Interfaces can start; formula result persistence later. |
| TT-BE-POS-006 | CROSSES_POSTGRES_BOUNDARY | Boundary tests can start; final lifecycle handoff depends on DB. |
| TT-BE-OL-001 | REQUIRES_POSTGRES | Start gate must atomically match spec and authorization. |
| TT-BE-OL-002 | REQUIRES_POSTGRES | Submit cutpoints and client IDs must persist before side effects. |
| TT-BE-OL-003 | REQUIRES_POSTGRES | Event ledger must be durable. |
| TT-BE-OL-004 | REQUIRES_POSTGRES | Placement sync must be durable. |
| TT-BE-OL-005 | REQUIRES_POSTGRES | Cancel idempotency requires persisted state. |
| TT-BE-OL-006 | REQUIRES_POSTGRES | Close acquire-or-join requires transactional uniqueness. |
| TT-BE-OL-007 | REQUIRES_POSTGRES | CLOSED predicate relies on persisted evidence/finality. |
| TT-BE-OL-008 | REQUIRES_POSTGRES | Native evidence ledger must be durable. |
| TT-BE-OL-009 | REQUIRES_POSTGRES | FINAL result and receipts are durable facts. |
| TT-BE-OL-010 | REQUIRES_POSTGRES | Post-final incidents/quarantine must persist. |
| TT-BE-API-001 | REQUIRES_POSTGRES | Market facts and coverage are replay evidence. |
| TT-BE-API-002 | REQUIRES_POSTGRES | Portfolio facts feed durable Portfolio state. |
| TT-BE-API-003 | REQUIRES_POSTGRES | Order/fill facts feed Lifecycle ledger. |
| TT-BE-RES-002 | CROSSES_POSTGRES_BOUNDARY | Replay logic can design now; deterministic runs persist after DB. |
| TT-BE-RES-003 | CROSSES_POSTGRES_BOUNDARY | Isolation fences can start; durable scopes later. |
| TT-BE-RES-004 | CROSSES_POSTGRES_BOUNDARY | Review can start; final governance state later. |
| TT-BE-SYS-003 | CROSSES_POSTGRES_BOUNDARY | Topology design starts; restart-safe workers require DB/outbox. |
| TT-BE-INFRA-002 | REQUIRES_POSTGRES | Target container roles need durable state. |
| TT-BE-INFRA-003 | CROSSES_POSTGRES_BOUNDARY | Health can start, DB checks after persistence. |
| TT-BE-INFRA-004 | CROSSES_POSTGRES_BOUNDARY | Auth decision can start; durable command auth later. |
| TT-BE-SYS-005 | CROSSES_POSTGRES_BOUNDARY | Command/read boundary can start; projections depend on target stores. |
| TT-BE-SYS-007 | CROSSES_POSTGRES_BOUNDARY | Isolation starts after canonical worker. |
| TT-BE-SYS-009 | REQUIRES_POSTGRES | Durable state must not depend on local files. |
| TT-BE-SYS-012 | CROSSES_POSTGRES_BOUNDARY | Auth migration depends on durable auth. |
| TT-BE-SYS-013 | CROSSES_POSTGRES_BOUNDARY | Legacy isolation starts; target stores later. |
| TT-BE-INFRA-005 | REQUIRES_POSTGRES | Deployment changes depend on target worker/state. |

## 9. Formula Parallelization Map

### Can complete before formula approval

TT-BE-INFRA-008, TT-BE-SYS-004, TT-BE-SYS-001, TT-BE-SYS-006, TT-BE-SYS-008, TT-BE-SYS-011, TT-BE-INFRA-001, TT-BE-SYS-002, TT-BE-API-002, TT-BE-PR-001, TT-BE-PR-002, TT-BE-PR-003, TT-BE-PR-004, TT-BE-PR-006, TT-BE-POS-002, TT-BE-POS-006, TT-BE-OL-001, TT-BE-OL-002, TT-BE-OL-003, TT-BE-OL-004, TT-BE-OL-005, TT-BE-OL-006, TT-BE-OL-008, TT-BE-OL-010, TT-BE-API-003, TT-BE-RES-001, TT-BE-RES-003, TT-BE-API-004.

### Can partially implement before formula approval

LONG/SHORT: TT-BE-SET-004, TT-BE-POS-001. Entry: TT-BE-POS-005. Stop: TT-BE-POS-005. Dynamic Take: TT-BE-POS-005. Set numeric: TT-BE-SET-003, TT-BE-API-001. Accounting final result: TT-BE-OL-007, TT-BE-OL-009, TT-BE-PR-005. Multiple formula families: TT-BE-SET-002, TT-BE-SET-005, TT-BE-SET-006, TT-BE-POS-003, TT-BE-POS-004, TT-BE-RES-002, TT-BE-SYS-010.

### Must wait for formula approval

Final semantic implementations for TT-BE-SET-002, TT-BE-SET-003, TT-BE-SET-004, TT-BE-SET-005, TT-BE-SET-006, TT-BE-POS-001, TT-BE-POS-003, TT-BE-POS-004, TT-BE-POS-005, TT-BE-OL-007, TT-BE-OL-009, TT-BE-API-001, TT-BE-RES-002, and formula-specific portions of TT-BE-SYS-010.

## 10. Legacy Isolation Traceability

| Legacy Area | Current Path | Isolation Implementation ID | Target Final State |
|---|---|---|---|
| Spot execution | `src/triggertrade/execution/bybit.py` | TT-BE-SYS-006 | Compatibility/demo-only; not canonical runtime. |
| Paper execution/runtime | `src/triggertrade/execution/paper.py`; `src/triggertrade/services/runtime.py` | TT-BE-SYS-006 | Opt-in compatibility path. |
| Dual lane runtime | `src/triggertrade/services/dual_lane_runtime.py` | TT-BE-SYS-007 | Noncanonical once target worker exists. |
| Demo futures strategy | `src/triggertrade/strategies/futures_directional.py` | TT-BE-SYS-007, TT-BE-POS-001 | Demo fixture only; canonical decision replaced. |
| Old risk path | `src/triggertrade/risk/manager.py`; `src/triggertrade/execution/futures.py` | TT-BE-SYS-011, TT-BE-PR-004 | Not reachable from canonical execution. |
| Legacy execution stores | `src/triggertrade/persistence/execution_store.py`; `src/triggertrade/persistence/futures_execution_store.py` | TT-BE-SYS-013 | Migration/read-history only. |
| Smoke scripts | `scripts/bybit_demo_futures_smoke.py`; `scripts/triggertrade_demo_soak.py`; `scripts/paper_runtime_smoke.py` | TT-BE-SYS-008 | Manual opt-in, not certification. |
| Dashboard process-local token | `src/triggertrade/dashboard/__main__.py` | TT-BE-SYS-012 | Legacy/local until auth boundary replaces it. |
| Dashboard-only Azure deployment | `scripts/deploy-azure.ps1`; `Dockerfile` | TT-BE-INFRA-005 | Replaced by target worker/web deployment path. |

## 11. Persistence Migration Traceability

| Current Store / State | Target State Category | Implementation IDs | Migration Action |
|---|---|---|---|
| Runtime checkpoints/lifecycles | checkpoint; mutable current state | TT-BE-INFRA-001, TT-BE-SYS-003, TT-BE-SYS-009 | MIGRATE |
| Trace/audit events | immutable event/fact; reconciliation evidence | TT-BE-OL-008, TT-BE-SYS-010 | EXTEND_MODEL |
| Trigger/rule versions | versioned configuration | TT-BE-SYS-004, TT-BE-POS-002, TT-BE-SET-001 | EXTEND_MODEL |
| Trading rules current pointer | mutable current state, not started-work truth | TT-BE-POS-002, TT-BE-SYS-004 | EXTEND_MODEL |
| Futures execution orders | immutable event/fact; mutable lifecycle state | TT-BE-OL-002, TT-BE-OL-003, TT-BE-SYS-013 | MIGRATE |
| Futures positions/events | mutable lifecycle state; reconciliation evidence | TT-BE-OL-006, TT-BE-OL-007, TT-BE-OL-008 | MIGRATE |
| Futures accounting | accounting record; immutable event/fact | TT-BE-OL-009, TT-BE-PR-005 | MIGRATE |
| Instrument catalog | immutable API fact/cache | TT-BE-API-002, TT-BE-INFRA-006 | EXTEND_MODEL |
| Research store | research result; versioned configuration pins | TT-BE-RES-001, TT-BE-RES-002 | EXTEND_MODEL |
| Backtest store | research result | TT-BE-RES-001, TT-BE-RES-002 | EXTEND_MODEL |
| Message/user notices | read/operator notifications | TT-BE-SYS-002, TT-BE-SYS-005 | EXTEND_MODEL |
| Operator state | mutable current state; audit record | TT-BE-INFRA-004, TT-BE-SYS-012 | MIGRATE |
| Daily loss state | accounting record; mutable Portfolio state | TT-BE-PR-005 | REPLACE |
| Historical kline cache | API fact cache/research input | TT-BE-SET-003, TT-BE-API-001, TT-BE-SYS-009 | REPLACE |
| Backup artifacts | operational backup evidence | TT-BE-INFRA-007, TT-BE-SYS-009 | EXTEND_MODEL |

## 12. Test Traceability

| Implementation ID | Unit | Contract | Persistence | State Machine | Replay | Restart | Concurrency | Integration | E2E |
|---|---|---|---|---|---|---|---|---|---|
| TT-BE-SYS-001 | REQUIRED | REQUIRED | LATER | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED |
| TT-BE-SYS-002 | REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-SYS-003 | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | REQUIRED | REQUIRED |
| TT-BE-SYS-004 | REQUIRED | REQUIRED | LATER | NOT_REQUIRED | REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED |
| TT-BE-INFRA-001 | REQUIRED | NOT_REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER |
| TT-BE-INFRA-002 | NOT_REQUIRED | NOT_REQUIRED | LATER | NOT_REQUIRED | NOT_REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED |
| TT-BE-INFRA-003 | REQUIRED | NOT_REQUIRED | REQUIRED | NOT_REQUIRED | NOT_REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | LATER |
| TT-BE-INFRA-004 | REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER |
| TT-BE-PR-001 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-PR-002 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER | LATER |
| TT-BE-PR-003 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-PR-004 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-PR-005 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-PR-006 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-SET-001 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER | LATER |
| TT-BE-SET-002 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER | LATER |
| TT-BE-SET-003 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | LATER |
| TT-BE-SET-004 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER | LATER |
| TT-BE-SET-005 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER | LATER |
| TT-BE-SET-006 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-POS-001 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER | LATER |
| TT-BE-POS-002 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER | LATER |
| TT-BE-POS-003 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-POS-004 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER | LATER |
| TT-BE-POS-005 | REQUIRED | REQUIRED | LATER | NOT_REQUIRED | LATER | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | LATER |
| TT-BE-POS-006 | REQUIRED | REQUIRED | LATER | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | LATER |
| TT-BE-OL-001 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-OL-002 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER |
| TT-BE-OL-003 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-OL-004 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER | LATER |
| TT-BE-OL-005 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER |
| TT-BE-OL-006 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-OL-007 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-OL-008 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER |
| TT-BE-OL-009 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER |
| TT-BE-OL-010 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER | LATER |
| TT-BE-API-001 | REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | LATER |
| TT-BE-API-002 | REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | LATER |
| TT-BE-API-003 | REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | LATER |
| TT-BE-API-004 | NOT_REQUIRED | REQUIRED | LATER | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | REQUIRED | LATER |
| TT-BE-RES-001 | REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | LATER | REQUIRED |
| TT-BE-RES-002 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | LATER | REQUIRED |
| TT-BE-RES-003 | REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED |
| TT-BE-RES-004 | REQUIRED | REQUIRED | LATER | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | LATER | REQUIRED |
| TT-BE-SYS-005 | REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED |
| TT-BE-SYS-006 | REQUIRED | REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | LATER |
| TT-BE-SYS-007 | REQUIRED | REQUIRED | LATER | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | LATER | REQUIRED |
| TT-BE-SYS-008 | REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | LATER | NOT_REQUIRED |
| TT-BE-SYS-009 | REQUIRED | NOT_REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED |
| TT-BE-SYS-010 | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED | REQUIRED |
| TT-BE-SYS-011 | REQUIRED | REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | LATER |
| TT-BE-SYS-012 | REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | REQUIRED | LATER |
| TT-BE-SYS-013 | REQUIRED | REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED | LATER | LATER | LATER |
| TT-BE-INFRA-005 | NOT_REQUIRED | NOT_REQUIRED | LATER | NOT_REQUIRED | NOT_REQUIRED | REQUIRED | NOT_REQUIRED | REQUIRED | REQUIRED |
| TT-BE-INFRA-006 | REQUIRED | LATER | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | LATER | NOT_REQUIRED |
| TT-BE-INFRA-007 | REQUIRED | NOT_REQUIRED | REQUIRED | NOT_REQUIRED | LATER | REQUIRED | NOT_REQUIRED | LATER | NOT_REQUIRED |
| TT-BE-INFRA-008 | NOT_REQUIRED | REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED | NOT_REQUIRED |

## 13. Technical Decision Traceability

| Decision ID | Decision | Required Before | Affected Implementation IDs | Current Status |
|---|---|---|---|---|
| TD-001 | HTTP/web framework | Wave 8 - Runtime and Dashboard Separation | TT-BE-SYS-005, TT-BE-INFRA-003 | DEFERRED |
| TD-002 | Worker framework/process supervisor | Wave 8 - Runtime and Dashboard Separation | TT-BE-SYS-003, TT-BE-INFRA-002 | OPEN |
| TD-003 | Queue/outbox implementation technology | Wave 1 - Contract Foundation | TT-BE-SYS-001, TT-BE-SYS-002 | OPEN |
| TD-004 | Physical database engine and schema | Wave 2 - Durable Persistence | TT-BE-INFRA-001, TT-BE-SYS-002, all owner-state rows | OPEN |
| TD-005 | ORM/query layer | Wave 2 - Durable Persistence | TT-BE-INFRA-001, TT-BE-SYS-002 | OPEN |
| TD-006 | Canonical JSON implementation | Wave 1 - Contract Foundation | TT-BE-SYS-004, TT-BE-SYS-001, TT-BE-POS-004 | OPEN |
| TD-007 | Exchange SDK vs direct REST/WebSocket | Wave 6 - Lifecycle Core | TT-BE-API-001, TT-BE-API-002, TT-BE-API-003, TT-BE-API-004 | DEFERRED |
| TD-008 | Exact cloud topology | Wave 8 - Runtime and Dashboard Separation | TT-BE-INFRA-002, TT-BE-INFRA-005 | DEFERRED |
| TD-009 | Authentication/authorization product | Wave 8 - Runtime and Dashboard Separation | TT-BE-INFRA-004, TT-BE-SYS-012, TT-BE-SYS-005 | OPEN |
| TD-010 | Observability stack | Wave 8 - Runtime and Dashboard Separation | TT-BE-SYS-003, TT-BE-INFRA-003 | DEFERRED |
| TD-011 | Research job orchestration tooling | Wave 7 - Research Alignment | TT-BE-RES-002, TT-BE-RES-003 | OPEN |
| TD-012 | Migration tool/deployment pipeline | Wave 2 - Durable Persistence | TT-BE-INFRA-001, TT-BE-INFRA-002 | OPEN |

## 14. First Executable Implementation Queue

| Priority | Implementation ID | Why Now | Dependencies Satisfied? | Formula Blocked? | PostgreSQL Blocked? |
|---|---|---|---|---|---|
| 1 | TT-BE-INFRA-008 | Locks traceability to the approved canonical docs and prevents archived-doc drift. | YES | NO | NO |
| 2 | TT-BE-SYS-004 | Canonical JSON/digests unblock contract identity and future pins. | YES | NO | NO |
| 3 | TT-BE-SYS-001 | Contract models are the shared foundation for every block. | AFTER TT-BE-SYS-004 | NO | NO |
| 4 | TT-BE-SYS-006 | Legacy spot/paper fencing can be done before persistence and lowers accidental reachability risk. | AFTER TT-BE-SYS-001 | NO | NO |
| 5 | TT-BE-SYS-011 | Old direct strategy/risk path can be removed from canonical launch early. | AFTER TT-BE-SYS-001 | NO | NO |
| 6 | TT-BE-SYS-008 | Smoke script guards are low-risk and clarify validation semantics. | YES | NO | NO |
| 7 | TT-BE-SYS-010 | Test taxonomy should begin with contract foundation and grow by wave. | AFTER TT-BE-SYS-001 | PARTIAL | PARTIAL |
| 8 | TT-BE-RES-001 | Research pin extension can start against contracts before full replay formulas. | AFTER TT-BE-SYS-001 | NO | PARTIAL |
| 9 | TT-BE-API-004 | Native profile review can start from existing Bybit demo evidence. | YES | NO | PARTIAL |
| 10 | TT-BE-INFRA-003 | Readiness extension can start conceptually and expand after persistence. | YES | NO | PARTIAL |

This ordering intentionally differs from the gap plan's first 10 tasks by pulling read-only baseline preservation and early conformance review into the executable queue, while deferring PostgreSQL-dependent outbox work until the database and queue decisions are resolved.

Gap plan first-task mapping:

| Gap Plan Task ID | Gap Plan Objective | Traceability Implementation IDs |
|---|---|---|
| TT-BE-001 | Add target contract package and enums without wiring runtime | TT-BE-SYS-001, TT-BE-SYS-004 |
| TT-BE-002 | Add legacy canonical-path fences | TT-BE-SYS-006, TT-BE-SYS-008, TT-BE-SYS-011 |
| TT-BE-003 | Decide and scaffold persistence abstraction | TT-BE-INFRA-001 |
| TT-BE-004 | Implement durable outbox/inbox model | TT-BE-SYS-002 |
| TT-BE-005 | Create Portfolio state schema/service skeleton | TT-BE-PR-001 |
| TT-BE-006 | Implement Capital and Limits grant issue | TT-BE-PR-003 |
| TT-BE-007 | Implement SUBMISSION_HOLD authorization skeleton | TT-BE-PR-004 |
| TT-BE-008 | Create Set scope/epoch service | TT-BE-SET-001 |
| TT-BE-009 | Create Market Data Request selector/page model | TT-BE-SET-003, TT-BE-API-001 |
| TT-BE-010 | Create Position decision/config pin skeleton | TT-BE-POS-001, TT-BE-POS-002, TT-BE-POS-005 |

## 15. Codex Task Boundaries

| Implementation ID | Task Scope | Expected Files/Areas | Validation Required |
|---|---|---|---|
| TT-BE-INFRA-008 | Add a read-only spec integrity/link validation task without editing approved docs. | docs validation script or test area only; `docs/trading-methodology/*` read-only | `git diff --check`; docs link/schema checks; no methodology diff |
| TT-BE-SYS-004 | Implement canonical JSON/digest utility and fixtures. | new target contract/support module; focused unit tests | digest golden vectors; determinism across ordering |
| TT-BE-SYS-001 | Add v1.2.14 contract models/validators. | new contract package; contract tests | all approved contract versions represented; schema fixtures validate |
| TT-BE-SYS-006 | Fence paper/spot paths from canonical launch. | `src/triggertrade/services/runtime.py`; `src/triggertrade/execution/bybit.py`; `src/triggertrade/execution/paper.py`; boundary tests | canonical launch cannot select legacy paper/spot; legacy opt-in imports remain |
| TT-BE-SYS-011 | Fence old strategy/risk path. | `src/triggertrade/strategies/buy_candidate.py`; `src/triggertrade/risk/manager.py`; launcher/module-boundary tests | canonical path cannot import direct strategy/risk execution |
| TT-BE-SYS-008 | Guard smoke scripts as manual-only. | `scripts/bybit_demo_futures_smoke.py`; `scripts/triggertrade_demo_soak.py`; `scripts/paper_runtime_smoke.py`; tests if present | scripts remain opt-in; no canonical certification wording |
| TT-BE-SYS-010 | Start target test taxonomy scaffolding. | `tests/contract`; `tests/unit`; test planning docs if needed | test categories exist and first contract tests run |
| TT-BE-RES-001 | Extend research pin records behind contracts. | `src/triggertrade/services/research.py`; `src/triggertrade/persistence/research_store.py`; `src/triggertrade/backtest/models.py` | research pin persistence and replay tests |
| TT-BE-API-004 | Produce native profile conformance review gate in code/tests without certifying unknown facts. | Bybit adapter tests and conformance fixtures | smoke/conformance report; unresolved fields stay gated |
| TT-BE-INFRA-003 | Extend health/readiness boundary. | `src/triggertrade/dashboard/__main__.py`; new health/readiness support tests | dependency-aware health tests; no trading side effects |

## 16. Completion Criteria by Wave

Wave 1 - Contract Foundation: approved docs remain untouched; canonical JSON and contract fixtures pass; legacy paths are fenced from canonical launch; first target test taxonomy exists.

Wave 2 - Durable Persistence: transaction/unit-of-work, durable outbox/inbox, and owner-state persistence primitives pass atomicity, dedupe, replay, restart, and concurrency tests.

Wave 3 - Portfolio Core: Portfolio state, Coins revisions, grants, holds, cooldown, and FINAL-result receipts are durable and replay-safe with current-pointer changes unable to affect started work.

Wave 4 - Set Core: Coins intake, epochs, market selectors, tri-state trigger events, MATCHED results, Market Handoff, and pending monitor behavior pass replay tests and formula golden vectors where applicable.

Wave 5 - Position Core: Position initial decision, config pins, construction result, formula interfaces, immutable Order Spec, and no-direct-execution boundary are proven by contract and state-machine tests.

Wave 6 - Lifecycle Core: Order Spec + Submit Authorized gate, submission cutpoints, Order Event ledger, Set sync, cancel handling, close authority, native observation ledger, CLOSED predicate, FINAL result, and post-final incident path pass restart/replay/concurrency tests.

Wave 7 - Research Alignment: research/demo runs have exact pins, no-live-side-effect isolation, target block replay, and deterministic result persistence; promotion/make-active remains governed by resolved decision.

Wave 8 - Runtime and Dashboard Separation: web/API, worker, scheduler, read model, command boundary, health/readiness, auth, deployment, and legacy demo isolation operate without local machine assumptions.

## 17. Backend Completion Definition

Backend implementation is complete against approved v1.2.14 when every implementation ID is complete or explicitly retired by a higher-authority methodology change; every approved business block has canonical code ownership; every contract edge is typed, durable, and replay-tested; every formula boundary has certified implementation/golden vectors; persistence supports restart, replay, uniqueness, and concurrency; Lifecycle reconciliation and financial finality are durable and audited; research/demo cannot contaminate active execution; dashboard writes flow only through audited commands; cloud runtime runs web and worker roles with readiness; and legacy paths are unreachable from canonical execution.

## 18. Traceability Issues

NONE

## 19. Readiness Verdict

READY_TO_BEGIN_BACKEND_IMPLEMENTATION

Every material gap is mapped, every target component is covered, the first executable queue exists, the dependency graph is coherent, and there are no unresolved blocking traceability contradictions. Formula-gated work and PostgreSQL-dependent work are isolated from the first executable queue.
