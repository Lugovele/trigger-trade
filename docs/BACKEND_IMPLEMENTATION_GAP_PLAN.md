# TriggerTrade Backend Implementation Gap Plan

Inputs used: `docs/BACKEND_AS_IS_REVIEW.md`, `docs/BACKEND_TARGET_MODEL.md`, `docs/trading-methodology/`, and verified current implementation paths under `src/`, `tests/`, `scripts/`, `Dockerfile`, `.dockerignore`, and `pyproject.toml`. Archived methodology was not used as normative evidence.

## 1. Executive Migration Summary

The current backend is a Python/SQLite implementation centered on a Bybit Demo futures polling runtime, local dashboard, versioned demo rule registries, futures execution/accounting stores, and research/backtest support. The target backend is a four-business-block message architecture: Portfolio Rules, Set, Position Rules, Order Lifecycle, plus factual API, durable messaging, owner-local persistence, replay-safe identifiers, and cloud-independent workers.

Major gap matrix rows: 57. Reusable assets: 10. Transition counts are KEEP_AS_IS 3, EXTEND 5, REFACTOR 18, REPLACE 2, ISOLATE_LEGACY 4, REMOVE_FROM_CANONICAL_PATH 4, CREATE_NEW 19, REVIEW_NEEDED 2. The largest architectural transition is replacing the current trigger/strategy/risk/execution pipeline with target Portfolio -> Set -> Position -> Lifecycle contracts. The largest persistence transition is moving from local SQLite stores toward durable transactional owner state, outbox/inbox, evidence journals, and replay-safe concurrency. The largest runtime transition is adding worker/orchestrator separation behind durable messaging. The largest legacy cleanup requirement is isolating spot/paper/demo pipelines from canonical execution. The biggest formula-gated area is Position Rules Entry/Stop/Dynamic Take and Set trigger/direction semantics.

## 2. As-Is vs Target Architecture Map

| Target Component | Current Equivalent | Match Quality | Required Transition | Notes |
|---|---|---|---|---|
| Web/API process | `src/triggertrade/dashboard/__main__.py`, `read_model.py` | Partial | REFACTOR | Local HTTP server directly opens stores and calls services. |
| Trading worker | `src/triggertrade/services/futures_runtime.py` | Partial | REFACTOR | Polling loop hosts trigger/strategy/risk/execution directly. |
| Research/backtest worker | `src/triggertrade/backtest/*`, `services/research.py` | Partial | EXTEND | Useful run models, but not target block replay. |
| Scheduler/orchestrator | runtime polling/sleep loops | Weak | CREATE_NEW | No durable scheduler/orchestrator abstraction. |
| Exchange adapter/API layer | `exchanges/bybit.py`, `execution/bybit_futures.py`, market parsers, catalog service | Partial | REFACTOR | Bybit access exists but not target factual API contracts. |
| Persistence layer | `src/triggertrade/persistence/*.py`, backtest store | Partial | REFACTOR | SQLite domain stores exist; target needs owner-local transaction boundaries and likely PostgreSQL. |
| portfolio_state_service | `DailyLossStore`, accounting snapshots, runtime account refresh | Weak | CREATE_NEW | No Portfolio-owned four-bucket capital state machine. |
| portfolio_scope_projector | current trigger set/rules selection | Weak | CREATE_NEW | No Coins v2 OPEN/CLOSE contract/outbox. |
| portfolio_grant_service | risk sizing/rules code | Weak | CREATE_NEW | No immutable Capital and Limits grant. |
| portfolio_hold_authorizer | `FuturesRiskManager`, execution service checks | Weak | CREATE_NEW | No post-construction SUBMISSION_HOLD authorization boundary. |
| portfolio_accounting_service | `daily_loss.py`, futures accounting stores | Partial | REFACTOR | Useful calculations; target receipt/day/finality semantics missing. |
| set_scope_service | runtime active/testing set lookup | Weak | CREATE_NEW | No scope revisions or formation epochs. |
| set_market_data_selector | `backtest/data.py`, market parsers, runtime candle fetch | Partial | REFACTOR | Needs Market Data Request v3 selectors/pages/evidence. |
| set_trigger_engine | `triggers/*`, `trace_store.py` | Partial | REFACTOR | Existing deterministic triggers do not satisfy generic tri-state event contract. |
| set_match_engine | `trigger_set_store.py`, futures strategy lane logic | Weak | CREATE_NEW | No Set MATCHED result/Market Handoff v4. |
| set_monitor_service | none material | Missing | CREATE_NEW | No frozen pending-order invalidation monitor. |
| position_decision_service | `strategies/futures_directional.py`, `execution/position_lifecycle.py` | Weak | REPLACE | Current strategy opens demo intents, not two-stage Position decision. |
| position_construction_service | `position_lifecycle.py`, `execution/futures.py` | Partial | REFACTOR | Sizing/exits exist, but no Capital and Limits, spec digest, construction result. |
| position_formula_engine | `position_lifecycle.py`, `rules/trading.py` | Partial | REFACTOR | Fixed exits/sizing exist; dynamic target interfaces incomplete. |
| lifecycle_start_gate | `FuturesExecutionService.submit_approved_limit_order` | Weak | CREATE_NEW | Current service consumes risk decision, not Order Spec + authorization. |
| lifecycle_submission_service | `execution/futures.py`, `execution/bybit_futures.py` | Partial | REFACTOR | Useful adapter/service but wrong authority boundary. |
| lifecycle_entry_ledger | `FuturesExecutionStore`, `FuturesPositionStore` | Partial | EXTEND | Basic persisted orders/positions; target event variants missing. |
| lifecycle_close_authority | `position_lifecycle.py` | Partial | REFACTOR | Close exists but no acquire-or-join ledger/residual child protocol. |
| lifecycle_reconciliation_service | execution reconcile methods, recovery loops | Partial | CREATE_NEW | Need native observations/resolutions/evidence preflight. |
| lifecycle_financial_finality | `accounting/futures.py`, accounting bridge/store | Partial | REFACTOR | Useful arithmetic; finality/evidence/currency semantics missing. |
| api_adapter_gateway | Bybit client/parsers/catalog | Partial | REFACTOR | Need strict factual API envelopes and provenance. |
| durable_messaging | `MessageStore` only user messages | Weak | CREATE_NEW | No business outbox/inbox. |
| research_run_service | `services/research.py`, `backtest/*` | Partial | EXTEND | Preserve structure, align pins/isolation. |

## 3. Current Assets to Preserve

| Current Asset | Path | Why Preserve | Target Role | Required Changes |
|---|---|---|---|---|
| Futures accounting pure functions | `src/triggertrade/accounting/futures.py` | Deterministic and tested arithmetic contracts | Lifecycle financial calculations | EXTEND only after finality/evidence boundary exists |
| Instrument catalog parsing | `src/triggertrade/instruments/catalog.py` | Good Bybit linear metadata normalization | API factual instrument facts | EXTEND provenance/profile fields |
| Instrument catalog service/store | `src/triggertrade/services/instrument_catalog.py`, `src/triggertrade/persistence/instrument_catalog_store.py` | Cached linear catalog with refresh history | API/Portfolio/Lifecycle hard facts | EXTEND into target API envelope |
| Bybit low-level client | `src/triggertrade/exchanges/bybit.py` | Narrow endpoint allowlist and sanitized errors | Adapter transport | REFACTOR wrapper, keep transport |
| Trigger/rule version stores | `src/triggertrade/persistence/trigger_set_store.py`, `trading_rules_store.py` | Immutable versions/current pointers and hashes | Versioned configuration foundation | EXTEND to target pins/digests |
| Trace store | `src/triggertrade/persistence/trace_store.py` | Durable audit event patterns | Evidence/read diagnostics | EXTEND or migrate schema |
| Backtest model/store immutability | `src/triggertrade/backtest/models.py`, `store.py` | Versioned runs with conflict checks | Research/backtest result persistence | EXTEND target pins |
| Dashboard read model concept | `src/triggertrade/dashboard/read_model.py` | Centralized projections | Target read models | Move behind application read boundary |
| Backup/restore checks | `src/triggertrade/services/backup_restore.py` | Integrity/fingerprint approach | Ops validation | Rework for target DB |
| Tests around stores/adapters/accounting | `tests/unit/*store*.py`, `test_futures_accounting.py`, adapter tests | Valuable regression scaffolding | Migration safety net | Expand for target contracts |

## 4. Current Assets to Extend

| Current Asset | Path | Missing Target Capability | Required Extension | Dependencies |
|---|---|---|---|---|
| Trading rules registry | `src/triggertrade/rules/trading.py`, `persistence/trading_rules_store.py` | Target Portfolio/Position config pinning, content digests by cycle/attempt | Add immutable owner-scoped config records and pin references | Persistence foundation |
| Trigger set registry | `src/triggertrade/persistence/trigger_set_store.py`, `trigger_sets/contracts.py` | Set/Trigger/Core Set role bindings and formation epoch pins | Add target Set config/version/reference binding model | Formula certification, persistence |
| Backtest/research stores | `src/triggertrade/backtest/store.py`, `persistence/research_store.py` | Exact methodology/config/API selector pins and target block replay | Add target run identity/pin/result fields | Contract models |
| Futures execution store | `src/triggertrade/persistence/futures_execution_store.py` | Order Spec/authorization matching, lifecycle revisions, event outbox | Extend or supersede with lifecycle stores | Durable messaging |
| Daily loss store/service | `src/triggertrade/persistence/daily_loss_store.py`, `services/daily_loss.py` | Accounting-day receipt/latch semantics from final results | Extend after Lifecycle final result contract | Portfolio accounting |

## 5. Current Assets to Refactor

| Current Asset | Path | Current Problem | Target Responsibility | Required Refactor |
|---|---|---|---|---|
| Futures runtime | `src/triggertrade/services/futures_runtime.py` | Single polling pipeline owns mixed Set/Position/Risk/Execution decisions | Trading worker/orchestrator | Split into durable message-driven block handlers |
| Runtime bootstrap | `src/triggertrade/services/bootstrap.py` | SQLite/env/local setup coupled to current runtime | Configuration and persistence bootstrap | Add target config source and migration checks |
| Futures risk manager | `src/triggertrade/execution/futures.py` | Risk/execution gates combine Portfolio, Position and Lifecycle concerns | Position construction plus Portfolio authorization plus Lifecycle hard checks | Move checks to correct owners |
| Position lifecycle service | `src/triggertrade/execution/position_lifecycle.py` | Opens/closes directly through execution service | Order Lifecycle plus Position construction support | Separate spec construction from lifecycle side effects |
| Futures accounting bridge | `src/triggertrade/services/futures_accounting_bridge.py` | Ingests execution rows into accounting without target finality/evidence protocol | Lifecycle financial finality | Refactor around complete evidence, allocation and FINAL result |
| Bybit futures adapter | `src/triggertrade/execution/bybit_futures.py` | Execution adapter returns narrow native order rows | Order Management factual API | Add strict facts, provenance, coverage, hard facts |
| Market-data runtime | `src/triggertrade/market_data/*`, runtime candle functions | Direct candle fetch/parsing without selectors/pages | Market Data Request v3 | Add selector/request/page assembly layer |
| Dashboard server | `src/triggertrade/dashboard/__main__.py` | Direct store/service mutation and process-local token | Web/operator boundary | Move writes behind command handlers |
| Dashboard read model | `src/triggertrade/dashboard/read_model.py` | Reads current SQLite tables directly | Read projections over target owner state | Rebuild projections after persistence migration |
| Research service | `src/triggertrade/services/research.py` | Current workflows are tied to present runtime stores and partial demo isolation | Research run service | Pin target semantics and isolate execution |
| Store layer | `src/triggertrade/persistence/*.py` | Many SQLite-specific tables and per-store connections | Persistence layer | Introduce transaction/unit-of-work and target schemas |
| Docker/deploy operation | `Dockerfile`, `scripts/deploy-azure.ps1` | Container starts dashboard only | Cloud runtime | Add worker/runtime process model after topology decision |

## 6. Current Assets to Replace

| Current Asset | Path | Why Replacement Is Required | Replacement Target Area | Migration Risk |
|---|---|---|---|---|
| Demo futures strategy | `src/triggertrade/strategies/futures_directional.py` | Docstring and logic are demo-only OPEN_LONG strategy, not Set/Position target semantics | Set + Position decision services | Medium; current runtime depends on it |
| Legacy paper risk path | `src/triggertrade/risk/manager.py` | Demo e2e notional/balance risk is not Portfolio/Position/Lifecycle target ownership | Portfolio grants/holds plus Position/Lifecycle gates | Low if isolated first |
| Spot execution canonical path | `src/triggertrade/execution/bybit.py`, `execution/service.py`, `execution/contracts.py` | Spot path conflicts with target Bybit linear perpetual canonical profile | Isolated compatibility only | Low-medium; dashboard/backtest references must be checked |
| Current direct runtime trade pipeline | `FuturesDualLaneRuntime._process_lane` in `src/triggertrade/services/futures_runtime.py` | It bypasses target contracts and owner sequence | Message-driven trading worker | High; primary active behavior |

## 7. Legacy Isolation Plan

| Legacy Area | Path | Current Reachability | Required Canonical Isolation | Safe to Keep Temporarily? |
|---|---|---|---|---|
| Spot execution | `src/triggertrade/execution/bybit.py`, `execution/service.py`, `execution/precision.py` | Legacy paper runtime/tests/scripts | Remove from canonical imports/entry points | YES |
| PaperTradingRuntime | `src/triggertrade/services/runtime.py::PaperTradingRuntime` | Class exists; main builds futures runtime | Mark compatibility/demo-only and keep outside target worker | YES |
| DualLaneRuntime | `src/triggertrade/services/dual_lane_runtime.py` | Earlier runtime class, unclear active entry | Remove from canonical runtime selection | YES |
| Demo futures strategy | `src/triggertrade/strategies/futures_directional.py` | Active futures runtime path | Replace canonical use; keep as demo fixture if needed | PARTIAL |
| Old risk path | `src/triggertrade/risk/manager.py`, parts of `execution/futures.py` | Paper/futures runtime | Isolate from target Portfolio/Position/Lifecycle ownership | YES |
| Old execution stores | `persistence/execution_store.py`, `futures_execution_store.py` | Legacy and current execution records | Freeze as legacy/migration source until target lifecycle store exists | YES |
| Smoke scripts | `scripts/*smoke*.py`, `scripts/triggertrade_demo_soak.py` | Manual opt-in | Keep opt-in only; prevent canonical certification meaning | YES |

## 8. New Capabilities to Create

| New Capability | Target Owner | Why Needed | Dependencies | Formula-Gated? | Persistence-Gated? |
|---|---|---|---|---|---|
| Business contract models/validators | System | Target contracts do not exist in code | Schema registry decision | NO | PARTIAL |
| Durable outbox/inbox | System | Required for crash-safe boundaries | Persistence tech | NO | YES |
| Portfolio state machine | Portfolio | Four-bucket capital, health, Coins, receipts | Contract models, persistence | NO | YES |
| Capital grant service | Portfolio | Immutable Capital and Limits v5 | Portfolio state | NO | YES |
| Submission hold authorizer | Portfolio | Exact post-construction hold + authorization | Grant + construction | NO | YES |
| Set scope/epoch engine | Set | Coins revisions and formation epochs | Contract models | NO | YES |
| Market Data Request v3 assembler | Set/API | Stable selections/pages/completeness | Adapter gateway | OTHER:SET_NUMERIC | YES |
| Set match/handoff engine | Set | `decision_cycle_id`, frozen handoff, references | Formula certification | MULTIPLE | YES |
| Pending-order monitor | Set | Frozen invalidation and cancel signals | Lifecycle sync, market data | MULTIPLE | YES |
| Position two-stage decision/construction | Position | APPROVE/REJECT then spec construction | Formula certification, Portfolio grants | MULTIPLE | YES |
| Lifecycle start gate | Lifecycle | Requires spec + authorization matching | Contract models/outbox | NO | YES |
| Close intent authority ledger | Lifecycle | Acquire-or-join, residual child protocol | Persistence/concurrency | NO | YES |
| Native evidence/reconciliation ledger | Lifecycle | Observations/resolutions/preflight/quarantine | Adapter facts | NO | YES |
| Financial finality service | Lifecycle | FINAL result, accounting day, currency admissibility | Accounting/facts | OTHER:ACCOUNTING | YES |

## 9. Runtime Topology Migration

Current entry points are `python -m triggertrade.services.runtime`, `python -m triggertrade.dashboard`, `python -m triggertrade.backtest`, smoke scripts, and Azure deployment. The runtime entry survives only as a launcher; its direct lane processing becomes internal legacy until replaced by a target trading worker. The dashboard entry survives as a web/API process after write paths move behind commands. The backtest entry survives as a research/backtest worker after it replays target block contracts. Smoke scripts remain opt-in.

Target long-running services are web/API, trading worker, scheduler/orchestrator, and optionally research/backtest worker. Scheduler separation is required at least conceptually because market-data selection, rollovers, reconciliation retries, and outbox delivery cannot be tied to one in-memory polling loop. Physical process count remains an open technical decision.

## 10. Persistence Migration Plan

| Current Store / State | Current Technology | Target State Role | Keep Logical Model? | Requires PostgreSQL? | Migration Priority |
|---|---|---|---|---|---|
| Runtime checkpoints/lifecycles | SQLite | Worker checkpoints and Set source checkpoints | PARTIAL | LIKELY | High |
| Trace/audit events | SQLite | Evidence/read diagnostics | PARTIAL | LIKELY | Medium |
| Trigger/rule versions | SQLite | Versioned configuration | YES | LIKELY | High |
| Trading rules current pointer | SQLite | Current config pointer, not started-cycle truth | PARTIAL | LIKELY | High |
| Futures execution orders | SQLite | Legacy migration source; target lifecycle state | PARTIAL | YES | High |
| Futures positions/events | SQLite | Legacy migration source; target tranche state | PARTIAL | YES | High |
| Futures accounting | SQLite | Lifecycle/Portfolio accounting source | PARTIAL | YES | High |
| Instrument catalog | SQLite | API factual instrument cache | YES | LIKELY | Medium |
| Research store | SQLite | Research run identity/results | PARTIAL | LIKELY | Medium |
| Backtest store | SQLite | Backtest run/results | PARTIAL | LIKELY | Medium |
| Message/user notices | SQLite | Operator/read notifications | PARTIAL | LIKELY | Low |
| Operator state | SQLite plus process token | Operator command/audit state | PARTIAL | LIKELY | Medium |
| Daily loss state | SQLite | Portfolio day/latch | PARTIAL | YES | High |
| Historical kline cache | JSON filesystem | API evidence cache/research input | NO | LIKELY | Medium |
| Backup artifacts | Filesystem | Ops backup evidence | PARTIAL | YES | Low after DB choice |

## 11. PostgreSQL Provisioning Decision

Earliest required wave: Wave 2, Durable Messaging and Owner-State Persistence. Blocking capability: transactional outbox/inbox plus atomic Portfolio hold/authorization and Lifecycle close acquire-or-join. First state categories requiring it are immutable events/facts, mutable current state, versioned configuration pins, outbox/inbox, and close/authorization uniqueness.

SQLite is no longer sufficient at that point because target correctness depends on concurrent workers/processes, durable compare-and-set/serializable behavior, unique active close intents, outbox delivery fences, and cloud-independent persistence. Work that can safely happen before PostgreSQL: contract dataclasses/validators, module boundary scaffolding, legacy isolation flags, formula interfaces, and read-only tests.

## 12. Contract / Boundary Migration

| Target Contract | Current Equivalent | Status | Required Change | Affected Modules |
|---|---|---|---|---|
| Coins v2 | Current active/testing trigger set selection | MISSING | Add Portfolio -> Set scope messages with revisions | runtime, new Portfolio/Set modules |
| Market Handoff v4 | Signal/strategy decision context | MISSING | Add frozen Set result handoff model | triggers, trigger_sets, market_data |
| Approve / Reject v5 | `FuturesStrategyDecision`, risk rejection statuses | CONTRADICTORY | Replace with Position initial/construction variants | strategies, execution, trace |
| Capital and Limits v5 | trading rules/account/instrument snapshots | MISSING | Add immutable grants after APPROVE | Portfolio, rules, catalog |
| Order Spec v5 | `FuturesTradeIntent` | PARTIAL | Add immutable spec/digest/provenance | position_lifecycle, execution |
| Submit Authorized v5 | approved `FuturesRiskDecision` | CONTRADICTORY | Add Portfolio hold authorization | execution/futures, Portfolio |
| Order Event v7 | position/execution/accounting events | PARTIAL | Add strict variants and Portfolio receipt handling | lifecycle/accounting/stores |
| Order Placed v3 | no canonical Set sync | MISSING | Add Lifecycle -> Set placement/terminal messages | Lifecycle, Set monitor |
| Order Cancel Signal v2 | manual/strategy cancel paths | MISSING | Add Set invalidation signal | Set, Lifecycle |
| Market Data Request v3 | direct Bybit candle/ticker calls | PARTIAL | Add selectors/pages/completeness | market_data, Bybit |
| Portfolio Data Request v5 | account refresh methods | PARTIAL | Add strict account/instrument/fee facts | Portfolio, Bybit |
| Order Management v4 | futures adapter methods | PARTIAL | Add strict order/fill/financial/hard-fact operations | execution/bybit_futures |
| Research boundary | current research/backtest service | PARTIAL | Add target pins and isolated adapters | research, backtest |

Current direct calls bypassing target boundaries include `FuturesDualLaneRuntime` calling strategy/risk/lifecycle directly, `PositionLifecycleService.open_position` submitting through `FuturesExecutionService`, dashboard POST handlers calling stores/services directly, and adapters returning raw-ish Bybit rows rather than governed API responses.

## 13. Identifier / Lineage Migration

| Target Identifier | Current Equivalent | Missing / Mismatch | Migration Requirement | Persistence Impact |
|---|---|---|---|---|
| `decision_cycle_id` | signal/intent IDs | Missing Set-owned cycle | Create Set cycle table/state | New durable Set store |
| Set epoch/config binding | trigger set version/current | Missing per OPEN revision epoch | Persist scope revisions and config pins | New Set state |
| Trigger evaluation/event binding | `Signal.signal_id`, trace rows | Partial, not tri-state/event | Add evaluation identities and consumption | Trace/Set store |
| `set_result_id` | none | Missing | Add immutable Set result | New Set store |
| role/binding/level IDs | partial trigger metadata | Missing exact reference lineage | Add role/reference model | Set config/result |
| `position_decision_id` | intent/risk IDs | Wrong owner/timing | Add Position decision identity | Position store |
| `capital_grant_id` | none | Missing | Add Portfolio grant identity | Portfolio store |
| `construction_result_id` | none | Missing | Add construction outcome identity | Position store |
| `position_plan_id`/`tranche_id`/`order_spec_id` | `position_id`, `trade_id`, intent IDs | Partial mismatch | Introduce target IDs; map legacy for migration only | Position/Lifecycle stores |
| `authorization_id` | risk decision ID | Wrong semantics | Add Portfolio authorization | Portfolio/outbox |
| `client_order_link_id` | `futures_client_order_id(intent_id)` | Partial | Bind to lifecycle create/close intent | Lifecycle store |
| exchange/order/execution IDs | Bybit rows/store fields | Partial | Preserve with provenance and namespace | API/Lifecycle evidence |
| close intent/child IDs | close intent string by position/reason | Partial/inadequate | Durable acquire-or-join IDs | Lifecycle close ledger |
| native observation/resolution/allocation IDs | none material | Missing | Add native evidence identity model | Lifecycle evidence store |
| accounting day/result/receipt IDs | closed trade/day-ish fields | Partial | Add final result and Portfolio receipt ledger | Accounting stores |
| research run IDs | backtest/research IDs | Partial | Add exact target pins | Research store |

## 14. Configuration Pinning Migration

Already immutable: trigger/rule definitions and trigger set versions use hashes in `trigger_set_store.py`; trading rules versions use `config_hash` and current pointers in `trading_rules_store.py`; backtest plans carry version/cache assumptions.

Current-pointer based and unsafe for target started work: `FuturesDualLaneRuntime` reads current active pair/current rules during processing; Position-like sizing uses the current `TradingRulesVersion`; Portfolio-like gates are not pinned by authorization attempt; Lifecycle does not persist accounting profile/currency pins at first accounting use.

Missing: Set formation epoch pins, Position decision-cycle config pins, Portfolio attempt/cooldown pins, Order Spec digest binding to all duplicated scalars, Lifecycle hard-fact check revisions, accepted evidence content histories, native profile conformance pins, and research pins for all target contracts.

## 15. Portfolio Rules Gap Plan

Preserve daily loss concepts, accounting snapshots, instrument/rules stores, and some capital limit values from `rules/trading.py`. Refactor `DailyLossEvaluator` and futures accounting consumption so Portfolio receives only Lifecycle FINAL results and posts receipts once. Create Portfolio-owned state for LIVE/RECONCILING/STALE, daily base, four commitment buckets, slots, grants, holds, scope revisions, cooldown contributions and receipts. Replace current risk-manager capital decisions in the canonical path with grant/hold services. Add restart/replay tests for unresolved SUBMISSION_HOLD and late final receipt.

## 16. Set Gap Plan

Preserve trigger definitions, trigger set versioning and market parsers where useful. Refactor current `PercentagePriceMoveTrigger`, `RobustVolumeConfirmationTrigger`, regime code and runtime candle processing behind Set-owned tri-state evaluation, formation epochs, source selectors and deterministic checkpoints. Create Coins intake, Market Data Request v3 selector/page assembly, Set MATCHED result, Market Handoff v4 and frozen pending-order monitor. Formula certification gates Set trigger/direction/frozen invalidation internals; scope, storage and contract plumbing can start now.

## 17. Position Rules Gap Plan

Current Position-like work is split across demo strategy, trading rules, futures risk and position lifecycle. Replace the demo strategy as canonical decision-maker. Refactor fixed TP/SL, sizing, risk/reward and net-edge logic into Position-owned decision/construction modules. Create two-stage APPROVE/REJECT and CONSTRUCTION_RESULT flows, Position config pinning, Capital and Limits intake, immutable Order Spec v5, digest validation and no direct API access. Formula-gated internals are LONG/SHORT, Entry, Stop and Dynamic Take; orchestration, pins, schemas and failure-state tests can start before certification.

## 18. Order Lifecycle Gap Plan

Reusable pieces include Bybit futures adapter transport, futures execution store ideas, client order IDs, reconcile methods, position lifecycle tests, and accounting calculations. Refactor around Order Spec + Submit Authorized matching rather than risk decisions. Create lifecycle state store, material outbox, hard execution fact checks, Order Event v7 variants, Order Placed v3 sync, idempotent cancel signal handling, close acquire-or-join ledger, child generation state, native observation/resolution ledger, protection proof, finality proof and POST_FINAL_INTEGRITY quarantine. Existing open/close logic is semantically incomplete because it can mark closed from fill reconciliation without all six target CLOSED predicates.

## 19. API / Exchange Boundary Gap Plan

Public market facts: Bybit ticker/kline/instrument calls exist but need Market Data Request selectors, stable pages, coverage and source snapshots. Instrument facts: catalog is a strong starting point but needs `max_order_qty_status`, source field/provenance and profile pins. Account/equity facts: wallet/position parsing exists in runtime but needs Portfolio Data Request v5 envelopes and coherence. Order/fill facts: linear create/cancel/order/execution calls exist but need Order Management v4 strict responses, native field provenance, acceptance status, hard execution facts and financial coverage. Business logic currently leaks into adapters/services through direct precision, environment and risk validations; target adapters must stay factual except Lifecycle-authorized side effects.

## 20. Accounting Gap Plan

Current `accounting/futures.py` computes VWAP, gross/net P&L, unrealized P&L, drawdown and funding with useful deterministic tests. It is incomplete for target finality because Lifecycle must own FINAL result production from complete execution/fee/funding/cost evidence, currency admissibility, source coverage, allocation manifests and accounting-day derivation. Portfolio must own once-only result receipt, day posting, daily loss latch and capital/slot release. Preserve pure arithmetic where compatible; add provenance, immutable source records, accepted coverage certificates, result IDs, receipt fences and replay tests.

## 21. Research / Backtest / Demo Gap Plan

Current backtest/research has run records, cache, simulator, comparisons, archive/select/make-active request handling, and opt-in demo smoke flows. It should be extended, not replaced wholesale. Needed gaps are target block replay, exact methodology/config pins, Market Data Request selector replay, isolated paper/demo adapters, metrics aligned to target events, and explicit prevention of research/live contamination. Promotion/make-active is not fully determined by target docs, so keep existing promotion-like flows behind REVIEW_NEEDED gates until methodology-aligned governance is specified.

## 22. Dashboard / Backend Separation Plan

| Area | Current Path | Classification | Target Move |
|---|---|---|---|
| Read-only dashboards | `dashboard/read_model.py` | MOVE_BEHIND_READ_MODEL | Rebuild over target projections |
| HTTP server/routes | `dashboard/__main__.py` | MOVE_BEHIND_APPLICATION_SERVICE | Keep serving, remove direct owner mutations |
| Rules editing API | `dashboard/__main__.py`, `rules/trading.py` | MOVE_BEHIND_COMMAND_BOUNDARY | Commands create versioned config, not direct target owner state |
| Research API | `dashboard/__main__.py`, `services/research.py` | MOVE_BEHIND_COMMAND_BOUNDARY | Queue research runs with pins |
| Operator pause/resume | `operator_state_store.py` | MOVE_BEHIND_COMMAND_BOUNDARY | Stable audited command IDs |
| Manual close/cancel | dashboard to lifecycle service | MOVE_BEHIND_COMMAND_BOUNDARY | Lifecycle command inbox only |
| Process-local token | `DashboardServer.__init__` | REMOVE_FROM_CANONICAL_PATH | Replace with persistent/auth boundary decision |
| Direct SQLite reads | `DashboardReadModel` | MOVE_BEHIND_READ_MODEL | Acceptable only through target read projections |

## 23. Formula Certification Interface Plan

| Formula Family | Current Code | Target Boundary | What Can Be Implemented Now | What Must Wait | Tests Needed After Approval |
|---|---|---|---|---|---|
| LONG/SHORT direction | `strategies/futures_directional.py`, `market_data/regime.py` | Set direction and Position direction consumption | Message contracts, direction enum plumbing | Approved Set direction formulas | Golden vectors and no-reinfer tests |
| Entry | current intent price helpers in `futures_runtime.py` | Position Dynamic Entry | Interface, diagnostics, pin storage | Approved Entry formula certification | Boundary, rounding, missing-input tests |
| Stop | `build_fixed_protective_exit_plan` | Position Fixed/Dynamic Stop | Fixed-mode interface and storage | Dynamic Stop certification | LONG/SHORT geometry and tick tests |
| Dynamic Take | currently disabled in runtime | Position Fixed/Dynamic Take | Mode plumbing and failure states | Dynamic Take certification | hierarchy, ATR distance, rounding tests |
| Gross R:R / Net Edge | `evaluate_risk_reward`, `estimate_net_edge` | Position initial/final gates | Exact numeric harness and result shape | Formula/golden vectors for target values | exact rational, thresholds, disabled mode |
| Set normalization/ATR | `market_data/regime.py`, volume trigger | Set numeric policy | Selector/checkpoint interfaces | TT_SET_NUMERIC conformance implementation | sqrt, ATR seed, replay tests |
| Accounting final result | `accounting/futures.py` | Lifecycle finality | Evidence/result envelope | Allocation/finality conformance | source/currency/funding/replay tests |

## 24. Test Migration Plan

Wave 1: contract and unit tests for target dataclasses/enums, canonical JSON/digests, config pins. Wave 2: persistence, concurrency and outbox/inbox tests for PostgreSQL-backed or DB-abstracted atomic operations. Wave 3: Portfolio state-machine, replay and daily accounting tests. Wave 4: Set state-machine, selector, checkpoint, historical replay and formula golden vector tests. Wave 5: Position two-stage construction, formula boundary and spec digest tests. Wave 6: Lifecycle state-machine, idempotency, restart, reconciliation, close authority and finality tests. Wave 7: research/backtest isolation and deterministic replay tests. Wave 8: end-to-end demo/paper and exchange adapter conformance tests.

## 25. Implementation Waves

| Wave | Goal | Main Gaps | Current Modules Affected | New Modules Needed | Formula Dependency | PostgreSQL Dependency | Exit Criteria |
|---|---|---|---|---|---|---|---|
| Wave 1 - Contract Foundation | Add target contract models and legacy fences | GAP-SYS-001, GAP-API-001 | contracts, trigger_sets, rules | contract package, validators | None | No | Schemas validate fixtures; legacy paths marked |
| Wave 2 - Durable Persistence | Add outbox/inbox and owner state foundation | GAP-SYS-002, GAP-INFRA-001 | persistence stores | persistence unit-of-work, message store | None | Yes | Atomic/dedupe tests pass |
| Wave 3 - Portfolio Core | Implement Portfolio state, grants, holds | GAP-PR-* | daily_loss, accounting stores | Portfolio services/stores | None | Yes | Portfolio state-machine tests pass |
| Wave 4 - Set Core | Implement Coins, epochs, selectors, handoff skeleton | GAP-SET-* | triggers, market_data, trigger_set_store | Set services/stores | Partial | Yes | Scope/replay/handoff tests pass with formula stubs |
| Wave 5 - Position Core | Implement two-stage decision/construction | GAP-POS-* | strategies, execution/futures, position_lifecycle | Position services/stores | Multiple | Yes | APPROVE/grant/spec tests pass |
| Wave 6 - Lifecycle Core | Implement spec+auth start, events, close/finality | GAP-OL-* | execution, position_lifecycle, accounting | Lifecycle services/stores | Accounting | Yes | Restart/replay/reconciliation tests pass |
| Wave 7 - Research Alignment | Replay target blocks in research/backtest | GAP-RES-* | backtest, research | research worker adapters | Multiple | Likely | Deterministic isolated run tests pass |
| Wave 8 - Runtime and Dashboard Separation | Launch workers/web cleanly | GAP-INFRA-*, dashboard gaps | runtime, dashboard, Docker | launcher, command/read API | None | Yes | E2E local/container tests pass |

## 26. Parallel Workstreams

Backend Foundations can start with contracts, validators and legacy isolation. Formula Certification can run in parallel because orchestration boundaries can accept approved formulas later. Persistence Migration starts before Portfolio/Lifecycle correctness work and blocks Waves 3 and 6. Order Lifecycle can design state machines in parallel with Portfolio after contract foundation, but side-effecting implementation waits for durable persistence. Research Infrastructure can extend run pins while block replay waits for Set/Position formulas. Dashboard/Application Boundary can move writes behind command interfaces after Wave 1 and finish after persistence/read models. Testing/Verification runs across all waves and owns fixtures for replay/restart/concurrency.

## 27. Critical Path

A. Methodology-faithful backend core: contract foundation -> durable persistence -> Portfolio core -> Set core -> Position core -> Lifecycle core.

B. Safe research execution: contract foundation -> research pin model -> Set selector/checkpoint model -> formula-certified Set/Position boundaries -> isolated replay worker.

C. 24/7 restart-safe runtime: durable persistence -> outbox/inbox -> worker hydration -> Lifecycle side-effect fencing -> scheduler/orchestrator -> container process model.

D. Production-ready live execution boundary: contract foundation -> API factual envelopes -> Bybit native profile conformance -> Lifecycle hard facts/reconciliation/finality -> security/auth/operator controls -> deployment validation. This does not claim live trading readiness by itself.

## 28. First 10 Implementation Tasks

| Task ID | Objective | Files/modules likely affected | Dependencies | Formula Dependency | Persistence Dependency | Required Validation | Definition of Done |
|---|---|---|---|---|---|---|---|
| TT-BE-001 | Add target contract package and enums without wiring runtime | new `src/triggertrade/contracts/*`, tests | None | None | No | contract unit tests | All v1.2.14 message names/versions represented |
| TT-BE-002 | Add legacy canonical-path fences | runtime, strategies, risk, execution imports | TT-BE-001 | None | No | module boundary tests | Demo/spot paths cannot be selected as canonical |
| TT-BE-003 | Decide and scaffold persistence abstraction | persistence package | TT-BE-001 | None | PostgreSQL decision | persistence smoke tests | Unit-of-work interface supports atomic operations |
| TT-BE-004 | Implement durable outbox/inbox model | persistence, services | TT-BE-003 | None | Yes | dedupe/replay tests | Message append/consume is idempotent |
| TT-BE-005 | Create Portfolio state schema/service skeleton | new Portfolio modules | TT-BE-004 | None | Yes | state-machine tests | LIVE/RECONCILING/STALE and four buckets modeled |
| TT-BE-006 | Implement Capital and Limits grant issue | Portfolio modules, contract tests | TT-BE-005 | None | Yes | grant replay tests | Duplicate APPROVE returns same grant |
| TT-BE-007 | Implement SUBMISSION_HOLD authorization skeleton | Portfolio modules | TT-BE-006 | None | Yes | concurrency tests | Hold+authorization atomic and exact |
| TT-BE-008 | Create Set scope/epoch service | new Set modules | TT-BE-004 | None | Yes | scope revision tests | OPEN/CLOSE epochs replay correctly |
| TT-BE-009 | Create Market Data Request selector/page model | Set/API modules | TT-BE-008 | SET_NUMERIC later | Yes | selector/restart tests | Stable selectors and page identities persist |
| TT-BE-010 | Create Position decision/config pin skeleton | new Position modules | TT-BE-004 | Entry/Stop/Take later | Yes | pin/replay tests | Initial decision pins config before formulas |

## 29. Technical Decisions Required Before Implementation

| Decision | Resolution Timing | Why | Affected Waves |
|---|---|---|---|
| HTTP/web framework | CAN_DEFER | Existing dashboard can remain during foundations | Wave 8 |
| Worker framework/process supervisor | BEFORE_SPECIFIC_WAVE | Needed before final runtime orchestration | Wave 8 |
| Queue/outbox implementation technology | BEFORE_WAVE_1 | Contract design needs message durability assumptions | Waves 1-2 |
| Physical database engine and schema | BEFORE_SPECIFIC_WAVE | PostgreSQL needed before atomic owner state | Wave 2 |
| ORM/query layer | BEFORE_SPECIFIC_WAVE | Determines persistence implementation style | Wave 2 |
| Canonical JSON implementation | BEFORE_WAVE_1 | Digests and contract validation need it | Waves 1, 5 |
| Exchange SDK vs direct REST/WebSocket | CAN_DEFER | Current REST client can be wrapped initially | Wave 6, 8 |
| Exact cloud topology | CAN_DEFER | Local target worker can be built first | Wave 8 |
| Authentication/authorization product | BEFORE_SPECIFIC_WAVE | Needed before operator commands are canonical | Wave 8 |
| Observability stack | CAN_DEFER | Basic logs/read models can precede final stack | Wave 8 |
| Research job orchestration tooling | BEFORE_SPECIFIC_WAVE | Needed for resumable research worker | Wave 7 |
| Migration tool/deployment pipeline | BEFORE_SPECIFIC_WAVE | Needed once PostgreSQL/schema migrations begin | Wave 2 |

## 30. Migration Risks

| Risk | Mitigation |
|---|---|
| State migration corrupts open positions/orders | Freeze canonical switch behind migration audit and reconciliation tests |
| Legacy code remains reachable | Add module boundary tests and explicit canonical launcher selection |
| Identifier mismatch across blocks | Contract tests and lineage persistence fixtures |
| Incorrect configuration pinning | Pin-first transaction tests and replay with changed current config |
| Duplicate order effects | Persist create intent/client ID before side effects; restart cutpoint tests |
| Financial state corruption | FINAL result/receipt dedupe tests and source/currency evidence validation |
| SQLite/PostgreSQL transition | Introduce persistence abstraction before owner state; migration dry runs |
| Dashboard/runtime races | Move writes to command boundary; read from projections only |
| Research/runtime contamination | Isolated adapters, DB scopes and no-live-side-effect tests |
| Formula interface drift | Golden vector fixtures and contract tests around formula boundaries |

## 31. Final Implementation Readiness Verdict

READY_FOR_IMPLEMENTATION_TRACEABILITY

No blockers prevent turning this plan into traceable implementation tasks. Formula certification and PostgreSQL decisions gate specific waves, not the ability to begin contract, boundary and persistence-foundation work.

## Main Gap Matrix

| ID | Target Area | Target Capability | Target Source | Current Implementation | Current State | Gap | Transition | Formula-Gated? | Persistence-Gated? | Can Start Now? | Dependencies | Required Tests |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GAP-SYS-001 | Contracts | Typed v1.2.14 business/API contracts | `docs/BACKEND_TARGET_MODEL.md` §5; `docs/trading-methodology/schemas/README.md` | no target contract package; current dataclasses in `execution/*`, `trigger_sets/contracts.py` | PARTIAL | Contract versions/shapes missing | CREATE_NEW | NO | PARTIAL | YES | canonical JSON decision | schema/contract tests |
| GAP-SYS-002 | Messaging | Durable outbox/inbox across business edges | Target §2, §9; `SYSTEM_PROTOCOLS.md` P1/P5 | `persistence/message_store.py` user messages only | MISSING | No business message journal | CREATE_NEW | NO | YES | YES | persistence tech | outbox replay/dedupe |
| GAP-SYS-003 | Runtime topology | Worker/scheduler/web separation | Target §2, §17 | `services/futures_runtime.py`, dashboard separate manual processes | PARTIAL | No target worker orchestration | REFACTOR | NO | PARTIAL | PARTIAL | outbox | restart/launcher tests |
| GAP-SYS-004 | Canonical JSON/digests | Stable serialization and spec digest | Target §7, §9; `NUMERIC_POLICY.md` §6 | ad hoc hashes in stores | PARTIAL | No shared canonical serializer | CREATE_NEW | NO | PARTIAL | YES | contract models | digest vectors |
| GAP-INFRA-001 | Database | Durable transactional persistence | Target §9-11 | SQLite stores in `persistence/*.py` | PARTIAL | Concurrency/cloud durability insufficient | REFACTOR | NO | YES | PARTIAL | DB decision | transaction tests |
| GAP-INFRA-002 | Container runtime | Web + worker process model | Target §17 | `Dockerfile` runs dashboard only | PARTIAL | Trading worker not deployed | REFACTOR | NO | YES | PARTIAL | runtime topology | container smoke |
| GAP-INFRA-003 | Health/readiness | State-aware readiness | Target §17 | dashboard `/healthz` only | PARTIAL | No persistence/worker safety readiness | EXTEND | NO | PARTIAL | YES | persistence | health tests |
| GAP-INFRA-004 | Secrets/auth | Durable operator auth boundary | Target §16-17 | process-local dashboard token | PARTIAL | Not canonical auth | REFACTOR | NO | PARTIAL | PARTIAL | auth decision | command auth tests |
| GAP-PR-001 | Portfolio state | LIVE/RECONCILING/STALE and four buckets | Target §3/§8; `PORTFOLIO_RULES.md` §9/§14 | account snapshots, daily loss, positions | PARTIAL | No Portfolio-owned state machine | CREATE_NEW | NO | YES | YES | contracts/persistence | Portfolio state-machine |
| GAP-PR-002 | Coins | Portfolio -> Set OPEN/CLOSE revisions | Target §5; `COINS.md` | current active set/rules polling | MISSING | No Coins v2 boundary | CREATE_NEW | NO | YES | YES | Portfolio state | revision replay |
| GAP-PR-003 | Grants | Capital and Limits immutable grants | Target §3/§5; `CAPITAL_AND_LIMITS.md` | none material | MISSING | No `capital_grant_id` or grant outbox | CREATE_NEW | NO | YES | YES | approve contract | grant idempotency |
| GAP-PR-004 | Holds | SUBMISSION_HOLD + Submit Authorized | Target §10; `SUBMIT_AUTHORIZED.md` | `FuturesRiskManager` approves direct execution | CONTRADICTORY | Wrong owner and timing | CREATE_NEW | NO | YES | YES | construction result | concurrency tests |
| GAP-PR-005 | Daily loss | Result-day latch and receipts | Target §15; `PORTFOLIO_RULES.md` §23 | `DailyLossEvaluator`, `DailyLossStore` | PARTIAL | Uses current accounting snapshots, not target FINAL receipts | REFACTOR | NO | YES | PARTIAL | Lifecycle finality | receipt/day tests |
| GAP-PR-006 | Cooldown | Attempt-scoped acceptance cooldown | Target §7/§8; `PORTFOLIO_RULES.md` §24 | cooldown open intent IDs in `execution/futures.py` | PARTIAL | No acceptance-time attempt pins | REFACTOR | NO | YES | PARTIAL | Lifecycle acceptance | cooldown replay |
| GAP-SET-001 | Scope epochs | Coins OPEN formation epoch reset | Target §3; `SET.md` §2.1A | no scope epoch model | MISSING | Current runtime evaluates latest candle/set | CREATE_NEW | NO | YES | YES | Coins | epoch tests |
| GAP-SET-002 | Trigger contract | Tri-state evaluations/events | Target §3; `SET.md` §10 | `SignalType` BUY/NO/CONFIRMED | PARTIAL | No TRUE/FALSE/UNAVAILABLE event continuity | REFACTOR | MULTIPLE | YES | PARTIAL | formula certification | trigger replay |
| GAP-SET-003 | Market selectors | Market Data Request v3 | Target §14; `MARKET_DATA_REQUEST.md` | direct Bybit candle methods/cache | PARTIAL | No selectors/pages/coverage | REFACTOR | OTHER:SET_NUMERIC | YES | YES | API gateway | selector assembly |
| GAP-SET-004 | MATCHED result | `decision_cycle_id`, `set_result_id` | Target §6; `SET.md` §4 | signal/intent IDs only | MISSING | No immutable Set result | CREATE_NEW | LONG_SHORT | YES | PARTIAL | Set formulas | result replay |
| GAP-SET-005 | Market Handoff | Frozen Handoff v4 | Target §5; `MARKET_HANDOFF.md` | strategy context/regime objects | MISSING | No wire handoff/reference bindings | CREATE_NEW | MULTIPLE | YES | PARTIAL | Set result | contract fixtures |
| GAP-SET-006 | Pending monitor | Frozen invalidation + cancel signal | Target §3; `SET.md` Part IV | none material | MISSING | No Set-owned pending monitor | CREATE_NEW | MULTIPLE | YES | PARTIAL | Lifecycle sync | monitor tests |
| GAP-POS-001 | Initial decision | APPROVE/REJECT before grant | Target §3; `APPROVE_REJECT.md` | demo strategy/risk direct intent | CONTRADICTORY | Current sequence bypasses Position boundary | REPLACE | MULTIPLE | YES | PARTIAL | Handoff | decision tests |
| GAP-POS-002 | Config pin | Position config pinned at first handoff | Target §7; `POSITION_RULES.md` §1B | current rules version usage | PARTIAL | No decision-cycle binding | CREATE_NEW | NO | YES | YES | config store | pin replay |
| GAP-POS-003 | Construction | Post-grant construction result | Target §3; `POSITION_RULES.md` §14 | sizing in runtime/lifecycle | PARTIAL | No construction_result_id/outcome | CREATE_NEW | MULTIPLE | YES | PARTIAL | grants/formulas | construction tests |
| GAP-POS-004 | Order Spec | Immutable spec v5/digest | Target §5; `ORDER_SPEC.md` | `FuturesTradeIntent` | PARTIAL | Missing digest/provenance/contract fields | REFACTOR | MULTIPLE | YES | PARTIAL | construction | digest tests |
| GAP-POS-005 | Dynamic formulas | Entry, Stop, Dynamic Take target boundaries | Target §12; `POSITION_RULES.md` Parts II-IV | fixed helpers; dynamic TP disabled | PARTIAL | Formula-certified implementations absent | CREATE_NEW | ENTRY | PARTIAL | NO | formula certification | golden vectors |
| GAP-POS-006 | Remove direct execution | Position must not submit/cancel | Target §3; `POSITION_RULES.md` §6 | `position_lifecycle.open_position` submits | CONTRADICTORY | Wrong side-effect ownership | REMOVE_FROM_CANONICAL_PATH | NO | PARTIAL | YES | lifecycle start gate | boundary tests |
| GAP-OL-001 | Start gate | Match Order Spec + Submit Authorized | Target §3/§5; `ORDER_LIFECYCLE.md` §3 | `FuturesExecutionService` takes intent+risk | CONTRADICTORY | Missing dual-input gate | CREATE_NEW | NO | YES | YES | contracts/outbox | start-gate tests |
| GAP-OL-002 | Submission intent | Persist client ID before side effect | Target §10; `ORDER_LIFECYCLE.md` §5 | `futures_client_order_id`, store create before adapter | PARTIAL | Needs target lineage/digest and uncertain dispatch | EXTEND | NO | YES | YES | lifecycle store | crash cutpoint |
| GAP-OL-003 | Order events | ORDER_EVENT v7 variants | Target §5; `ORDER_EVENT.md` | position/execution events, accounting rows | PARTIAL | Strict variants missing | CREATE_NEW | NO | YES | YES | event store | contract/replay |
| GAP-OL-004 | Order Placed sync | Lifecycle -> Set v3 | Target §5; `ORDER_PLACED.md` | none material | MISSING | Set monitor not notified canonically | CREATE_NEW | NO | YES | YES | lifecycle events | revision tests |
| GAP-OL-005 | Cancel signal | Set invalidation cancellation only | Target §5; `ORDER_CANCEL_SIGNAL.md` | manual/service cancel paths | PARTIAL | No governed signal handling | REFACTOR | NO | YES | YES | Set monitor | cancel idempotency |
| GAP-OL-006 | Close authority | Acquire-or-join close intent | Target §10; `SYSTEM_PROTOCOLS.md` P5 | close intent based on position/reason | PARTIAL | No unique active intent ledger | REFACTOR | NO | YES | YES | persistence | concurrency tests |
| GAP-OL-007 | CLOSED predicate | Six-condition CLOSED | Target §19; `SYSTEM_PROTOCOLS.md` P6 | `mark_closed` after filled close | CONTRADICTORY | Terminal state too weak | REPLACE | OTHER:ACCOUNTING | YES | PARTIAL | financial finality | state-machine |
| GAP-OL-008 | Native observations | P9/P15 observation/resolution | Target §6/§13 | none material | MISSING | No native observation ledger | CREATE_NEW | NO | YES | YES | API facts | reconciliation tests |
| GAP-OL-009 | Financial finality | FINAL result, coverage, currency | Target §15; `ORDER_EVENT.md` Financial result | accounting bridge/store | PARTIAL | No finality/evidence/currency block | REFACTOR | OTHER:ACCOUNTING | YES | PARTIAL | API financial facts | finality tests |
| GAP-OL-010 | Post-final integrity | Incident/quarantine and receipt fence | Target §19; `SYSTEM_PROTOCOLS.md` T01/Y01 | none material | MISSING | No post-final incident path | CREATE_NEW | NO | YES | YES | finality/event store | incident tests |
| GAP-API-001 | Market API | Strict market data factual boundary | Target §14; `MARKET_DATA_REQUEST.md` | `exchanges/bybit.py`, `market_data/bybit.py` | PARTIAL | No v3 request/response/coverage | REFACTOR | OTHER:SET_NUMERIC | YES | YES | selector model | API contract |
| GAP-API-002 | Portfolio API | Account/equity/instrument/fee facts | Target §14; `PORTFOLIO_DATA_REQUEST.md` | wallet/position parsing in runtime/client | PARTIAL | No v5 coherent envelope | REFACTOR | NO | YES | YES | Portfolio state | factual tests |
| GAP-API-003 | Order API | Order Management v4 operations | Target §14; `ORDER_MANAGEMENT.md` | `bybit_futures.py` narrow methods | PARTIAL | Missing hard facts, financial facts, provenance | REFACTOR | NO | YES | YES | Lifecycle | adapter contract |
| GAP-API-004 | Native profile | Bybit conformance evidence | Target §14; `NATIVE_FACT_PROFILE.md` | Bybit Demo client and tests | PARTIAL | Spec says runtime verification not certified | REVIEW_NEEDED | NO | PARTIAL | PARTIAL | conformance plan | native smoke |
| GAP-RES-001 | Research pins | Exact target version/config/source pins | Target §13 | `ResearchStore`, `BacktestPlan` | PARTIAL | Pins incomplete for target contracts | EXTEND | NO | PARTIAL | YES | contract models | research store tests |
| GAP-RES-002 | Target replay | Backtest runs target blocks | Target §13 | `BacktestEngine` reuses current runtime pieces | PARTIAL | Not four-block replay | REFACTOR | MULTIPLE | PARTIAL | PARTIAL | Set/Position | replay tests |
| GAP-RES-003 | Demo isolation | No live side effects | Target §13 | `ResearchDemoIsolation.available` often false | PARTIAL | Isolation not fully implemented | EXTEND | NO | PARTIAL | YES | adapter scopes | isolation tests |
| GAP-RES-004 | Promotion governance | Make-active gates | Target §13 notes unclear | `ResearchService.request_make_active` | UNCLEAR | Target docs do not fully define workflow | REVIEW_NEEDED | NO | PARTIAL | PARTIAL | alignment decision | governance tests |
| GAP-SYS-005 | Dashboard boundary | UI read/command only | Target §16 | `dashboard/__main__.py` direct calls | PARTIAL | UI/server owns too much coupling | REFACTOR | NO | PARTIAL | PARTIAL | commands/read models | dashboard API tests |
| GAP-SYS-006 | Legacy spot/paper | Remove from canonical path | Target §1/§17 | spot adapters, paper runtime | LEGACY | Wrong product/profile for target | ISOLATE_LEGACY | NO | NO | YES | canonical launcher | boundary tests |
| GAP-SYS-007 | Demo futures pipeline | Isolate current demo strategy/runtime path | Target §1 | `FuturesDualLaneRuntime`, `futures_directional.py` | LEGACY | Demo path bypasses target blocks | ISOLATE_LEGACY | NO | PARTIAL | YES | new worker | e2e legacy tests |
| GAP-SYS-008 | Smoke scripts | Keep opt-in only | Target §17 | `scripts/*smoke*.py` | LEGACY | Smoke is not canonical validation | ISOLATE_LEGACY | NO | NO | YES | none | script guards |
| GAP-SYS-009 | Local filesystem cache | Cloud-independent durable state | Target §17 | `runtime/history`, backups | PARTIAL | Durable state depends on local files | REFACTOR | NO | YES | PARTIAL | DB/storage decision | restart tests |
| GAP-SYS-010 | Existing tests | Target conformance taxonomy | Target §18 | broad current tests | PARTIAL | Tests cover current behavior, not target contracts | EXTEND | MULTIPLE | PARTIAL | YES | all waves | wave tests |
| GAP-SYS-011 | Old direct strategy/risk path | Remove from canonical launch | Target §3-5 | `BuyCandidateStrategy`, `RiskManager` | LEGACY | Spot-style flow conflicts with target | REMOVE_FROM_CANONICAL_PATH | NO | NO | YES | launcher fence | import tests |
| GAP-SYS-012 | Direct dashboard token | Remove as canonical auth | Target §16 | process-local token in dashboard | LEGACY | Restart-local auth only | REMOVE_FROM_CANONICAL_PATH | NO | PARTIAL | PARTIAL | auth decision | auth tests |
| GAP-SYS-013 | Legacy execution stores | Keep as migration/read history only | Target §9 | `execution_store.py`, parts of futures stores | LEGACY | Schemas do not map target contracts | ISOLATE_LEGACY | NO | PARTIAL | YES | target stores | migration tests |
| GAP-INFRA-005 | Azure deploy | Deploy target worker/web | Target §17 | `scripts/deploy-azure.ps1` dashboard app | PARTIAL | No worker/process deployment | REMOVE_FROM_CANONICAL_PATH | NO | YES | PARTIAL | Wave 8 topology | deploy smoke |
| GAP-INFRA-006 | Existing mature utilities | Preserve where target-compatible | Target §3/§14/§15 | accounting pure funcs, catalog, Bybit transport | IMPLEMENTED | Useful but not whole capability | KEEP_AS_IS | NO | NO | YES | wrapper interfaces | unit regression |
| GAP-INFRA-007 | Backup/integrity audit | Operational continuity checks | Target §17 | `backup_restore.py`, `db_integrity_audit.py` | IMPLEMENTED | Useful until DB migration, then adapt | KEEP_AS_IS | NO | NO | YES | none | existing tests |
| GAP-INFRA-008 | Read-only docs/spec baseline | Approved methodology docs | Target source | `docs/trading-methodology/*` | IMPLEMENTED | No implementation change needed | KEEP_AS_IS | NO | NO | YES | none | link checks |
