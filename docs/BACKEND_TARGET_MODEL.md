# TriggerTrade Backend Target Model

Canonical source: `docs/trading-methodology/` v1.2.14 only. This document is a technical projection, not a methodology change. `TECHNICAL_DERIVATION` marks minimum software structure inferred from mandatory behavior.

## 1. Executive Target Model

The approved backend target preserves exactly four business blocks plus the factual API layer:

1. Portfolio Rules - Capital Management.
2. Set - Market Analysis.
3. Position Rules - Trade Decision.
4. Order Lifecycle - Order Management.
5. API - technical data/interface layer only, not a business block.

Directly mandated boundaries and sequence are Portfolio -> Set `Coins`, Set -> Position `Market Handoff`, Position -> Portfolio `Approve / Reject`, Portfolio -> Position `Capital and Limits`, Position -> Lifecycle `Order Spec`, Portfolio -> Lifecycle `Submit Authorized`, Lifecycle -> Portfolio `Order Event`, Lifecycle -> Set `Order Placed`, Set -> Lifecycle `Order Cancel Signal`, and each owner's API boundary where specified. Source: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P1 - Topology and approval/construction sequence`; `docs/trading-methodology/methodology/PORTFOLIO_RULES.md`, `Purpose`; `docs/trading-methodology/methodology/SET.md`, `Purpose`; `docs/trading-methodology/methodology/POSITION_RULES.md`, `Purpose`; `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`, `Purpose`.

TECHNICAL_DERIVATION: the minimum faithful backend needs durable business-state services for the four blocks, a factual exchange/API adapter layer, persistent message/outbox/inbox infrastructure, and workers able to resume after crash before performing side effects. A web/API surface may exist for reads and operator commands, but it cannot own trading logic or calculate business state.

```text
                         UI / Operator Boundary
                    read models | idempotent commands
                               |
                               v
TECHNICAL INFRASTRUCTURE: web/API process, workers, scheduler, outbox/inbox
                               |
BUSINESS BLOCKS:
Portfolio Rules --Coins--> Set --Market Handoff--> Position Rules
      ^                     ^                         |
      |                     |                         |
      |                 Order Placed                  |
      |                     |                         v
      +--Order Event-- Order Lifecycle <--Order Spec--+
                         ^        ^
                         |        |
               Submit Authorized  Order Cancel Signal
                         |
PERSISTENCE: immutable facts/events, versioned config, current state, checkpoints,
             evidence, accounting records, research results
                         |
EXTERNAL / FACTUAL API: market facts, portfolio/account facts, order/fill/financial facts
                         |
EXCHANGE / VENUE: Bybit linear USDT perpetual profile where proven
```

Research/backtest/demo must use the same versioned semantics for the same Set version and be isolated from active/live execution. Source: `docs/trading-methodology/methodology/SET.md`, `Part V - Canonical Runtime Invariants`; `docs/trading-methodology/README.md`.

## 2. Target Runtime Topology

| Runtime Component | Type | Responsibilities | Business Blocks Hosted | Long-Running? | Restart-Safe? | Persistent State? |
|---|---|---|---|---|---|---|
| Web/API process | TECHNICAL_DERIVATION | Read models, operator command ingress, authentication/authorization boundary, health/readiness | None as owner | Yes if serving UI/API | Required for commands/read consistency | Command audit, operator receipts, read-model checkpoints |
| Trading worker | TECHNICAL_DERIVATION | Consume durable messages, run Portfolio, Set, Position, Lifecycle state machines, drive outboxes | Portfolio, Set, Position, Lifecycle | Yes for 24/7 behavior | Mandatory | All business state and outbox/inbox facts |
| Research/backtest worker | TECHNICAL_DERIVATION | Run pinned research/backtest/demo using same versioned semantics, no live side effects | Simulated copies of blocks only | May be long-running | Required for resumable runs | Research identity, pins, inputs, outputs, metrics |
| Scheduler/orchestrator | TECHNICAL_DERIVATION | Trigger market-data selection, rollovers, reconciliation, retry due durable outboxes | None as owner | Yes | Mandatory | Leases/checkpoints only; business truth remains in owners |
| Exchange adapter/API layer | Direct factual API layer plus TECHNICAL_DERIVATION implementation | Normalize market/account/order/financial facts, submit/cancel when Lifecycle authorizes | API only | May be library or process | Must preserve request/response identities | Technical request/response facts, provenance |
| Persistence layer | TECHNICAL_DERIVATION | Transactions, unique identities, immutable journals, current projections, outbox/inbox, replay | None as business owner | Service dependency | Mandatory | Yes |

One process may safely host web, scheduler and worker only if durable outbox/inbox, transaction boundaries, side-effect fencing, and restart hydration obligations are still met. Separation is technically required when 24/7 processing, long-running research, exchange side effects, or operator serving would otherwise block each other or make replay/health isolation unsafe. Sources: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P5 - Atomic acquire-or-join and reduction authority`, `P17 - Immutable configuration binding for started cycles and attempts`; `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`, `Appendix C - Durable messaging and monotonic Set synchronization`.

## 3. Business Block Technical Projection

### Portfolio Rules

Responsibility: own-capital accounting, limits, coin allocation, active analysis need, grants, submission holds, cooldown, daily loss, API-backed portfolio synchronization. Inputs: `Order Event`, `Approve / Reject`, Portfolio API facts, configuration, time/rollover triggers. Outputs: `Coins`, `Capital and Limits`, `Submit Authorized`, accounting/read state. Owned state: daily base, realized/unrealized/live equity views, holds/reserved/filled/closing-retained commitments, slots, grants, receipts, cooldown contributions, daily loss latch. Required persistence: grants, holds, receipts, accounting days, cooldown pins, scope revisions, state health, outbox/inbox. Identifiers: `capital_grant_id`, `authorization_id`, `accounting_day_id`, `delivered_at`, Portfolio attempt config/cooldown binding. Restart obligations: restore receipts, day records, latch/base, commitment buckets and unresolved native observations before processing events. Concurrency obligations: atomic grant issue and atomic current capacity hold. Interactions: Portfolio sends Coins to Set, grants to Position, authorization to Lifecycle; consumes Position decisions and Lifecycle events. Sources: `docs/trading-methodology/methodology/PORTFOLIO_RULES.md`, `Purpose`, `9. Portfolio Rules-owned state`, `13. Submission hold and reservation start`, `23. Daily Loss Limit`, `24. Cooldown`, `Appendix D - Durable decision/authorization publication`, `Appendix F - Final financial results, accounting days and receipts`.

### Set

Responsibility: active-scope market analysis, Trigger composition, direction, `decision_cycle_id` and `set_result_id`, frozen Market Handoff, frozen Market Invalidation Inputs, pending-order monitoring and cancel signals. Inputs: `Coins`, Market Data API facts, `Order Placed`/entry lifecycle sync. Outputs: `Market Handoff`, `Order Cancel Signal`, Set diagnostics. Owned state: active coin scope by revision, formation epochs, Trigger evaluations/events, matched results, frozen conditions, monitor state, historical selection/page assembly/checkpoints. Required persistence: formation epoch/config binding, evaluations, event consumption, source selectors, page manifests, Set numeric checkpoints, frozen handoff bytes/evidence, terminal monitor tombstones. Identifiers: `decision_cycle_id`, `set_result_id`, `core_set_id`, `trigger_occurrence_id`, `binding_id`, `selection_id`, `request_id`, `source_snapshot_id`, `page_id`, `checkpoint_id`. Restart obligations: apply scope revisions monotonically, never bridge UNAVAILABLE, never synthesize fresh events, restore selections/checkpoints/frozen conditions and monitor tombstones. Concurrency obligations: epoch isolation and one matched result per concrete cycle. Interactions: consumes Portfolio scope and Lifecycle placed/terminal sync; calls Market Data API; sends Position handoff and Lifecycle cancel signal. Sources: `docs/trading-methodology/methodology/SET.md`, `2. Set inputs`, `2.1A OPEN scope revision as formation epoch`, `4. Set outputs`, `6. Market Handoff`, `10. Trigger result and event contract`, `Part IV - Pending Order Market Validity`, `Appendix A - Ordered scope and monitor synchronization`; `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`, `1. Source identity, order and completeness`, `3. Wilder ATR(14) seed and recursive state`.

### Position Rules

Responsibility: opportunity APPROVE/REJECT, two-stage post-grant construction, Entry/SL/TP, leverage, quantity, notional, gross R:R, Minimum Net Edge, immutable Order Spec. Inputs: `Market Handoff`, `Capital and Limits`, pinned Position config. Outputs: initial `OPPORTUNITY_DECISION`, post-grant `CONSTRUCTION_RESULT`, `Order Spec`. Owned state: Position configuration binding, initial decision, construction outcome, final plan/tranche/spec and digest when constructed, diagnostics. Required persistence: decision record and outbox, pinned config identity/version/digest, grant binding, construction result, successful spec bytes and digest. Identifiers: `position_decision_id`, initial decision `event_id`, `construction_result_id`, `position_plan_id`, `tranche_id`, `order_spec_id`, `order_spec_digest`. Restart obligations: hydrate pinned config and exact market/grant binding; no latest config or symbol/time rebinding. Concurrency obligations: one initial decision and one post-grant construction outcome per cycle/grant binding. Interactions: consumes Set handoff and Portfolio grant; sends Portfolio decision/construction and Lifecycle spec. Sources: `docs/trading-methodology/methodology/POSITION_RULES.md`, `1. Purpose`, `1A. Logical tranche as Position Rules decision unit`, `1B. Position Rules configuration selection and immutable binding`, `14. Deterministic dependency order`, `Part V-A - Approval and Capital Hold Invariant`; `docs/trading-methodology/business-contracts/APPROVE_REJECT.md`, `Two-stage meaning on one existing boundary`; `docs/trading-methodology/business-contracts/ORDER_SPEC.md`, `Immutable post-grant construction`.

### Order Lifecycle

Responsibility: wait for matching spec + authorization, technical serialization, hard execution fact compatibility, exchange submit/cancel/reconcile, pending entry, fills, protection, close intent, native observations, financial finality, Order Events. Inputs: `Order Spec`, `Submit Authorized`, `Order Cancel Signal`, operator close/cancel commands, Order Management API facts/responses. Outputs: `Order Event`, `Order Placed`/entry lifecycle sync, native submit/cancel requests. Owned state: lifecycle state, create/cancel dispatch records, client IDs, exchange IDs, executions, fill aggregates, protection child generations, close intent ledger, native observations, attribution resolutions, financial source/coverage/allocation/finality records, post-final incidents. Required persistence: everything material before side effects, outbox/inbox, source proof, evidence identities, resolved tombstones. Identifiers: `client_order_link_id`, `exchange_order_id`, `execution_id`, `close_intent_id`, close/protection child IDs, `native_observation_id`, `native_scope_revision`, `attribution_resolution_id`, `resolution_revision`, `allocation_id`, `lifecycle_revision`, `result_id`, incident/evidence IDs. Restart obligations: restore spec/authorization matching, create intent, outboxes, open authority, reconciliation state, financial evidence, and tombstones before side effects. Concurrency obligations: one active close intent per tranche; serialized residual/child authority; idempotent cancel/create and event application. Sources: `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`, `1. Canonical ownership boundaries`, `3. Order Lifecycle start condition`, `4. Technical submission boundary`, `5. Entry submission`, `7. Canonical lifecycle states`, `Appendix A - Tranche-isolated protection and close protocol`, `Appendix G - F01-F08 factual recovery and financial synchronization`.

### API

Responsibility: factual transport, normalization and exchange interaction only. Inputs: technical requests from Set, Portfolio and Lifecycle; native exchange responses/events. Outputs: normalized market, portfolio/account, order/fill/financial facts with provenance, plus outbound order/cancel results. Owned state: none as business truth; TECHNICAL_DERIVATION may persist request/response/evidence logs and idempotency records. Required persistence: request/response identities and raw/normalized provenance where owner obligations require replay. Identifiers: `request_id`, `response_id`, source endpoint/record IDs, source snapshots, native IDs, cashflow IDs. Restart obligations: retry identical technical requests where specified, preserve raw evidence and provenance. Concurrency obligations: no business decisions, no ownership inference, no hidden calculations. Sources: `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md`, `1. Authority and version`; `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md`, `Purpose and authority`; `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md`, `F01 / F02 / F04 / F06 normalized factual semantics (contract v4)`; `docs/trading-methodology/api-contracts/NATIVE_FACT_PROFILE.md`, `1. Evidence, not outbound intent`.

## 4. Target Module Map

| Target Module | Business Owner | Responsibility | Inputs | Outputs | Persistent State | Formula-Dependent? |
|---|---|---|---|---|---|---|
| portfolio_state_service | Portfolio | Own-capital state merge and health | Order Events, Portfolio API facts | LIVE/RECONCILING/STALE state | Current state, revisions | Yes |
| portfolio_scope_projector | Portfolio | Emit Coins OPEN/CLOSE | Portfolio state/config | Coins v2 | scope_revision/outbox | Yes |
| portfolio_grant_service | Portfolio | Issue immutable grants after APPROVE | OPPORTUNITY_DECISION | Capital and Limits v5 | grants/outbox | Yes |
| portfolio_hold_authorizer | Portfolio | Atomic current gate/capacity hold | CONSTRUCTED, grants/state | Submit Authorized v5 | holds/authorization/tombstone | Yes |
| portfolio_accounting_service | Portfolio | Daily base, daily loss, receipts, cooldown | FINAL Order Events, API facts, rollover | accounting state, latches | accounting days, receipts | Yes |
| set_scope_service | Set | Apply Coins revisions and formation epochs | Coins v2 | active scope | scope state/epochs | No |
| set_market_data_selector | Set | Persist factual selectors/page requests | active scope/monitors | Market Data Request v3 | selections/requests | No |
| set_trigger_engine | Set | Evaluate Trigger tri-state and events | market facts/config | trigger state | evaluations/events | Yes |
| set_match_engine | Set | Create matched Set result and handoff | trigger states/facts | Market Handoff v4 | result/frozen handoff | Yes |
| set_monitor_service | Set | Frozen pending-order invalidation | Order Placed, market facts | Order Cancel Signal v2 | frozen conditions/tombstones | Yes |
| position_decision_service | Position | Initial APPROVE/REJECT | Market Handoff, config | APPROVE_REJECT.initial | decision/config binding | Yes |
| position_construction_service | Position | Post-grant final plan/spec | Capital and Limits, decision | CONSTRUCTION_RESULT, Order Spec | construction/spec/digest | Yes |
| position_formula_engine | Position | Entry, SL, TP, R:R, Net Edge interfaces | frozen handoff/grant/config | calculation records | diagnostics | Yes |
| lifecycle_start_gate | Lifecycle | Match spec and authorization | Order Spec, Submit Authorized | READY_TO_SUBMIT or failure | inbox/correlation | No |
| lifecycle_submission_service | Lifecycle | Submit exact LIMIT POST_ONLY | ready tranche/hard facts | native create request/events | create intent/client ID | No |
| lifecycle_entry_ledger | Lifecycle | Pending/fill/cancel entry state | API order/execution facts | Order Events, Order Placed sync | fills/order state | Yes |
| lifecycle_close_authority | Lifecycle | Acquire/join close and child authority | TP/SL/manual/native causes | close child requests | close intent ledger | Yes |
| lifecycle_reconciliation_service | Lifecycle | Native observations/resolutions/protection | API facts | Order Events/incidents | evidence/tombstones | No |
| lifecycle_financial_finality | Lifecycle | FINAL result and accounting day | executions/cashflows/coverage | ORDER_EVENT.final | financial records | Yes |
| api_adapter_gateway | API | Normalize factual APIs and exchange requests | technical requests/native responses | normalized facts | request/response evidence | No |
| durable_messaging | TECHNICAL_DERIVATION | Outbox/inbox, dedupe, replay | owner events | deliveries | message journals | No |
| research_run_service | TECHNICAL_DERIVATION | Pinned research/backtest/demo execution | versioned inputs | metrics/results | run records/results | Yes |

## 5. Contract and Message Boundary Map

| Producer | Consumer | Contract / Message | Purpose | Identifier Pins | Persistence Requirement | Replay Requirement |
|---|---|---|---|---|---|---|
| Portfolio | Set | Coins v2 | OPEN/CLOSE new-analysis scope | `event_id`, symbol `scope_revision` | Durable scope/outbox | Apply only newer per-symbol revision |
| Set | Position | Market Handoff v4 | Frozen matched market opportunity | `decision_cycle_id`, `set_result_id`, Set/config/reference IDs | Immutable result/handoff/evidence | No replacement with newer Set result |
| Position | Portfolio | APPROVE_REJECT.initial v5 | Initial opportunity decision | `event_id`, `position_decision_id`, `decision_cycle_id`, `set_result_id` | Decision + outbox | Duplicate no-op; changed content fail closed |
| Portfolio | Position | Capital and Limits v5 | Immutable grant and governed venue/capital facts | `capital_grant_id`, decision/cycle/result IDs | Grant + fact provenance + outbox | Duplicate APPROVE returns same grant |
| Position | Portfolio | APPROVE_REJECT.constructed/failed v5 | Post-grant construction outcome | `construction_result_id`, grant/cycle/spec IDs when constructed | Construction result + outbox | One outcome; no fabricated successful spec |
| Position | Lifecycle | Order Spec v5 | Immutable executable trade spec proposal | `order_spec_id`, `tranche_id`, digest, lineage IDs | Spec bytes/digest + outbox | Spec without authorization waits |
| Portfolio | Lifecycle | Submit Authorized / Order Submit v5 | Execution authority after exact hold | `authorization_id`, `order_spec_digest`, lineage IDs | Hold + authorization + outbox | Identical replay creates no extra hold/create |
| Lifecycle | Portfolio | Order Event v7 logical | Lifecycle state, fills, terminal FINAL result | `event_id`, `tranche_id`, `result_id`, `lifecycle_revision` where applicable | Lifecycle state + outbox; Portfolio inbox/receipt | Exactly-once effects and receipt fence |
| Lifecycle | Portfolio | Order Event v7 native observation/resolution | Native unresolved or resolved attribution evidence | `native_observation_id`, `native_scope_revision`, resolution IDs | Evidence/tombstone/outbox | No fabricated logical IDs; duplicates no-op |
| Lifecycle | Portfolio | Order Event v7 POST_FINAL_INTEGRITY | Post-final contradictions | `incident_id`, `incident_revision`, parent result | Incident journal/outbox | Independent result/incident dedupe |
| Lifecycle | Set | Order Placed / ENTRY_LIFECYCLE_EVENT v3 | Activate/stop pending monitor | `event_id`, `decision_cycle_id`, `lifecycle_revision` | Outbox; Set monitor state/tombstone | Terminal revision dominates delayed placement |
| Set | Lifecycle | Order Cancel Signal v2 | Frozen-condition invalidation | `signal_id`, cycle/result/tranche IDs | Signal/outbox | Retry same signal; no duplicate close |
| Set | API | Market Data Request v3 | Factual market data | `request_id`, `selection_id`, `selection_digest`, `page_id` | Selections/pages/provenance | Retry identical bytes; assemble deterministically |
| Portfolio | API | Portfolio Data Request v5 | Account/portfolio/instrument/fee facts | `request_id`, response/source IDs | Facts/provenance | Missing/partial blocks LIVE/new exposure |
| Lifecycle | API | Order Management v4 | Create/cancel/reconcile/order/fill/financial facts | `request_id`, native/client/order/execution/cashflow IDs | Request/response/evidence | Ambiguous create reconciles, no blind retry |

Sources: all files under `docs/trading-methodology/business-contracts/`; `docs/trading-methodology/api-contracts/`; `docs/trading-methodology/schemas/README.md`.

## 6. Identifier and Lineage Model

| Identifier | Created By | Immutable? | Parent / Lineage | Must Persist? | Replay Role |
|---|---|---|---|---|---|
| `decision_cycle_id` | Set | Yes | matched Core Set/config/symbol | Yes | Cross-component cycle key |
| Set formation epoch/config binding | Set | Yes per epoch | symbol + OPEN `scope_revision` | Yes | Prevent old epoch carry-over |
| Trigger evaluation/event binding | Set | Yes | trigger/version/symbol/epoch/source | Yes | Deduplicate, prevent bridged events |
| `set_result_id` | Set | Yes | `decision_cycle_id` | Yes | One immutable result |
| `core_set_id` / constituent IDs / trigger refs | Set/config producer | Yes | Set version and occurrences | Yes | Exact reference lineage |
| `role_id` / `binding_id` / `level_id` | Set | Yes | concrete matched reference | Yes | Position validates, does not infer |
| Position configuration binding | Position | Yes | `position_decision_id + decision_cycle_id` | Yes | Pins config across construction |
| `position_decision_id` | Position | Yes | cycle/result | Yes | Initial decision uniqueness |
| Initial decision `event_id` | Position | Yes | decision/outbox | Yes | Delivery dedupe |
| `capital_grant_id` | Portfolio | Yes | approved decision/cycle/result | Yes | Duplicate APPROVE same grant |
| `construction_result_id` | Position | Yes | grant + decision | Yes | One construction outcome |
| `position_plan_id` | Position | Yes | successful construction | Yes | Plan lineage |
| `tranche_id` | Position | Yes | successful construction | Yes | Logical position identity |
| `order_spec_id` | Position | Yes | successful construction | Yes | Spec identity |
| `order_spec_digest` | Position | Yes | canonical spec envelope | Yes | Validate spec/confirmation/authorization |
| Portfolio attempt config/cooldown binding | Portfolio | Yes | `authorization_id + tranche_id` | Yes | Late acceptance cooldown uses pin |
| `authorization_id` | Portfolio | Yes | successful hold/grant/spec | Yes | Execution authority uniqueness |
| `client_order_link_id` | Lifecycle | Yes | persisted native create/close intent | Yes | Ambiguous dispatch reconciliation |
| `exchange_order_id` | Exchange | Yes when supplied | native order | Yes when known | Fact lookup, not guessed |
| `execution_id` | Exchange fact | Yes | account/venue/product namespace | Yes | Exactly-once quantity/fee application |
| `transaction_id` / funding transaction ID | Exchange financial source | Yes | financial source | Yes | Funding/cashflow attribution |
| `cashflow_id` | API normalization | Yes | native transaction/execution component | Yes | Alias/source dedupe |
| `close_intent_id` | Lifecycle | Yes | `tranche_id` active intent | Yes | Acquire-or-join and resolved tombstone |
| Close child ID | Lifecycle | Yes | close intent/residual budget | Yes | Prevent duplicate reduction |
| Protective child ID/generation | Lifecycle/native | Yes | parent/tranche generation | Yes | Protection proof/recovery |
| `native_observation_id` | Lifecycle normalization | Yes | native scope/source evidence | Yes | Independent unresolved native fact |
| `native_scope_revision` | Lifecycle | Yes | account/env/symbol/side/index | Yes | Scope revision, not global order |
| `attribution_resolution_id` | Lifecycle | Yes | native observation | Yes | Complete allocation manifest |
| `resolution_revision` | Lifecycle | Yes | resolution ID | Yes | Tombstone/content conflict checks |
| `allocation_id` | Lifecycle | Yes | observation/resolution/tranche/source | Yes | Once-only logical allocation |
| `lifecycle_revision` | Lifecycle | Yes | logical tranche state stream | Yes | Set/Portfolio ordering where applicable |
| `accounting_day_id` | Lifecycle derives using Portfolio policy | Yes | permanent final execution day | Yes | Daily posting attribution |
| Financial `result_id` | Lifecycle | Yes | canonical final transaction | Yes | Once-only final result |
| `delivered_at` | Portfolio receiver | Yes once set | receipt transaction | Yes | Receipt chronology, not producer result |
| No-reduction reconciliation IDs | Lifecycle | Yes | native observation/scope/order | Yes | Clearance without quantity effect |
| Acceptance conflict/resolution IDs | Lifecycle | Yes | attempt acceptance evidence | Yes | Cooldown/integrity blocking |
| Market `selection_id` | Set | Yes | symbol/dataset/window/cutoff | Yes | Historical request ownership |
| Market `request_id` | Set | Yes | exact technical page request | Yes | Retry identical request |
| `source_snapshot_id` / `page_id` | API adapter | Yes | governed source selection page | Yes | Assembly and contradiction detection |
| Indicator `checkpoint_id` | Set | Yes | TT_SET_NUMERIC/source ancestry | Yes | Deterministic restart/replay |
| `incident_id` / `incident_revision` | Lifecycle | Yes | post-final contradiction parent result | Yes | Quarantine without rewriting result |
| `evidence_id` / content digest | Lifecycle evidence journal | Yes | normalized source proof | Yes | Known-content comparison |
| Terminal receipt | Portfolio | Yes | result/tranche/day | Yes | Once-only capital/slot effect |

Source: `docs/trading-methodology/IDENTIFIER_LINEAGE.md`, table `Identity | Sole creator / creation timing | Binding, persistence and consumer`, `Timestamp ownership`, `Technical identities`, `T01/T02 incident identities and T04 source-effect proof`.

## 7. Configuration Pinning Model

Pinned items: Set/Trigger/Core Set configuration for each formation epoch and matched cycle; Position configuration for each decision cycle; Portfolio configuration and cooldown duration for each authorization attempt; accounting policy and governed currency/accounting profile inherited through grant/spec/Lifecycle; numeric policy versions `TT_NUMERIC_V1` and `TT_SET_NUMERIC_V1`; native profile/instrument/fee revisions used in grants/specs.

Pin timing: Set pins on each effective newer Coins OPEN before MATCHED and retains matched config after cycle creation. Position pins before first initial APPROVE/REJECT evaluation. Portfolio pins attempt configuration and cooldown in the atomic hold/authorization transaction. Lifecycle durably retains the already-pinned accounting/settlement currency/profile at the tranche's first accounting use.

Immutability: later config changes affect only future cycles/attempts. Started work hydrates its persisted pins and fails closed on conflicting identity/version/content. TECHNICAL_DERIVATION: pins require versioned configuration records with canonical content digests and transactionally written references in owner state. Sources: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P17 - Immutable configuration binding for started cycles and attempts`; `docs/trading-methodology/methodology/POSITION_RULES.md`, `1B. Position Rules configuration selection and immutable binding`; `docs/trading-methodology/schemas/NUMERIC_POLICY.md`, `2A. One governed accounting unit; unsupported currency blocks FINAL`.

## 8. State Ownership Model

| State | Canonical Owner | Mutable? | Persistence Required? | Transactional? | Replay-Relevant? | Concurrency-Sensitive? |
|---|---|---|---|---|---|---|
| Capital base/limits | Portfolio | Current mutable, day base immutable | Yes | Yes at rollover/gates | Yes | Yes |
| Reservations/holds/filled/closing-retained | Portfolio | Mutable by lifecycle events | Yes | Yes | Yes | Yes |
| Coin OPEN/CLOSE scope | Portfolio owns emission, Set owns applied scope | Mutable by revision | Yes | Yes | Yes | Yes |
| Set cycle/match state | Set | Immutable once matched | Yes | Yes | Yes | Yes |
| Direction | Set | Immutable downstream | Yes | Yes | Yes | No after match |
| Position decision | Position | Immutable per cycle | Yes | Yes | Yes | Yes |
| Construction/spec | Position | Immutable if constructed | Yes | Yes | Yes | Yes |
| Order lifecycle state | Lifecycle | Mutable until terminal | Yes | Yes | Yes | Yes |
| Fills/executions | Lifecycle consumes exchange facts | Immutable facts, mutable aggregate | Yes | Yes | Yes | Yes |
| Protection state | Lifecycle | Mutable by proven facts | Yes | Yes | Yes | Yes |
| Close intent/child authority | Lifecycle | Mutable revisions, terminal tombstone | Yes | Yes | Yes | Yes |
| Financial finality | Lifecycle | Immutable FINAL; quarantine later contradictions | Yes | Yes | Yes | Yes |
| Cooldown | Portfolio | Mutable by accepted attempts/tombstones | Yes | Yes | Yes | Yes |
| Accounting day | Lifecycle derives result day; Portfolio posts/receipts | Immutable per result/day | Yes | Yes | Yes | Yes |
| Reconciliation evidence | Lifecycle/API owner-local | Mostly immutable facts with mutable status | Yes | Yes | Yes | Yes |
| Source challenge/quarantine | Relevant owner, mostly Lifecycle/Set | Mutable incident state | Yes | Yes | Yes | Yes |
| Research state | TECHNICAL_DERIVATION, research service | Mutable until run terminal | Yes for resumability | Yes | Yes | Yes |

Sources: `docs/trading-methodology/methodology/PORTFOLIO_RULES.md`, `9. Portfolio Rules-owned state`; `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`, `7. Canonical lifecycle states`; `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `Y01-Y02 owner-local evidence retention synchronization`.

## 9. Persistence Model Requirements

| Category | Durability Requirement | Transaction Requirement | Uniqueness / Idempotency Requirement | Restart Requirement | Replay Requirement | Retention Importance |
|---|---|---|---|---|---|---|
| Immutable event/fact | Durable before dependent effects | Commit with outbox/inbox where material | Stable IDs/content digests; changed same ID fails closed | Hydrate before new processing | Duplicate identical no-op | High |
| Mutable current state | Durable projection from facts | Update atomically with accepted event | Revision/owner guards | Rebuild or restore consistently | Replay must produce same state | High |
| Versioned configuration | Durable canonical bytes/digest | Pin with first-use transaction | Identity/version/content digest unique | Restore exact pin | Later config cannot affect old work | High |
| Checkpoint | Durable with source ancestry/policy | Commit with processed source identity | Matching policy/ancestry only | Restore only authentic matching checkpoint | Full replay must match | High |
| Reconciliation evidence | Durable raw+normalized provenance | Retain contradictions before suppression/rejection | Evidence identity/digest and owner indexes | Restore blocks/tombstones | Known challenges survive duplicate/reorder | High |
| Accounting record | Durable immutable final/posting records | Final result/receipt/release atomic | `result_id` and `tranche_id` once-only | Restore receipts/day/latch/base | No duplicate P&L/release | High |
| Research result | Durable for reproducibility | Pin inputs/config/results together | `research_run_id` or equivalent TECHNICAL_DERIVATION | Resume or mark incomplete deterministically | Same pins produce comparable results | Medium-high |

Sources: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P11 - Exact numeric values, then canonical serialization`, `P16 - Set numeric state and historical market selectors`, `X03 - Durable known-evidence preflight before mixed-batch rejection`; `docs/trading-methodology/methodology/PORTFOLIO_RULES.md`, `Appendix D - Durable decision/authorization publication`.

## 10. Transaction and Concurrency Boundaries

| Operation | Must Be Atomic? | Why | State Touched | Concurrency Hazard | Required Guard |
|---|---|---|---|---|---|
| Initial Position decision publication | Yes | Decision and outbox must survive together | decision record, event outbox | Duplicate/conflicting initial decision | Unique cycle/decision identity |
| Portfolio grant issue | Yes | Grant identity and publication are one fact | grant, outbox | Duplicate APPROVE allocates multiple grants | Unique approved decision/cycle |
| Position construction publication | Yes | Spec and CONSTRUCTED confirmation must match | construction, spec, two outboxes | Portfolio sees confirmation without spec | Same transaction/equivalent |
| Portfolio hold/authorization | Yes | Current gates, grant consumption, hold and Submit Authorized are one decision | grant, commitments, slots, authorization | Competing constructions overbook capacity | Serializable/CAS plus unique authorization |
| Lifecycle spec+authorization matching | Yes for state transition | Execution only with matching identities/digest | inboxes, lifecycle state | One side arrives first/conflict | Correlation and digest validation |
| Native create intent before side effect | Yes | Retry must not mint duplicate client ID | create intent/client ID/outbox | Crash around send duplicates exposure | Persist before/with dispatch |
| Cancel intent handling | Yes | Cancel request is not terminal fact | cancel state/outbox | Duplicate cancel releases twice | Idempotent signal/intent |
| Close acquire-or-join | Yes | At most one active close intent | close intent ledger | TP/SL/manual race | Unique active-intent constraint |
| Reduction child authorization | Yes | One residual budget at a time | child IDs, residual, authority | Double reduction | Serialize on tranche/intent revision |
| Native quantity allocation | Yes | Source conservation and effect once-only | allocation proof, quantity receipt | Same execution assigned twice | Global allocation/source receipt |
| Financial FINAL/CLOSED | Yes | Result, resolved intent, CLOSED outbox commit together | financial evidence, final result, state, outbox | Release before complete evidence | Recheck P6/P13 revision vector |
| Portfolio result receipt/release | Yes | P&L posting and capital/slot release once | receipt, day, commitments, latch | Duplicate final event double-posts | Result and tranche dedupe |
| Known-evidence contradiction preflight | Yes | Challenge must survive ordinary rejection | evidence journal, quarantine | Malformed companion rolls back challenge | Preflight durable checkpoint |

Sources: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P1`, `P5`, `P6`, `T04`, `X03`, `Y01-Y02`; `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`, `Appendix A - Tranche-isolated protection and close protocol`.

## 11. Restart / Replay / Recovery Model

After process crash, container restart, or redeploy, each owner hydrates durable IDs, pins, current state, outboxes/inboxes, evidence journals and tombstones before any new side effect. Crashes before durable commit create no durable authority; crashes after commit rejoin the same identity. Sources: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P5`, `P17`; `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`, `Appendix G - F01-F08 factual recovery and financial synchronization`.

Duplicate events: identical replays are no-ops under their IDs; changed content under an accepted identity is an integrity condition. Delayed events: owners apply monotonic revisions or exact effective chronology, not arrival order. Out-of-order evidence: known accepted content is compared before stale/terminal suppression. Partial completion: unresolved holds, ambiguous submissions, active close intents, partial fills, partial coverage and pending incidents retain blocking state. Reconciliation interruption: restart restores request IDs, source proofs, accepted certificates, native observations, allocation manifests and unresolved authority before continuing.

Recomputable state: derived current projections and read models may be rebuilt from persisted facts. Non-recomputable differently: immutable handoff bytes, specs, grants, authorization, terminal financial results, accepted evidence bindings, accounting-day assignments and receipt effects. Immutable facts must remain immutable even when later contradictions are quarantined.

## 12. Formula Integration Boundaries

| Formula Boundary | Inputs | Output | Business Owner | When Evaluated | State/Pins Required | Can Surrounding Code Be Built Before Formula Approval? |
|---|---|---|---|---|---|---|
| Set Trigger predicates | market selections, Trigger config | TRUE/FALSE/UNAVAILABLE | Set | formation epoch and monitoring | Set/Trigger config, source evidence | Yes, as plugin boundary; formulas must be governed |
| Set direction classifier | matched Core Set/context | LONG/SHORT/NONE | Set | initial analysis | Set config/result | Yes |
| Set normalization/ATR | historical source facts | working values, ATR handoff values | Set | before handoff/monitor gates | TT_SET_NUMERIC_V1, checkpoint ancestry | Yes |
| Dynamic Entry | Market Handoff, direction, entry_context | planned entry reference, LIMIT price | Position | initial opportunity stage | pinned Position config, frozen handoff | Yes |
| Fixed/Dynamic Stop | Entry, handoff, sl_context/config | stop price/feasibility | Position | initial opportunity stage | pinned Position config | Yes |
| Fixed/Dynamic Take | Entry, handoff, tp_context/config | TP price/feasibility | Position | initial opportunity stage | pinned Position config | Yes |
| Gross R:R | Entry, SL, TP | gross_rr | Position | initial opportunity stage | pinned config/handoff | Yes |
| Sizing/notional/quantity | grant, leverage, Entry, venue facts | final qty/notional/actual capital | Position | post-grant construction | Capital and Limits, TT_NUMERIC_V1 | Yes |
| Minimum Net Edge | planned TP/SL economics, fees, actual notional | PASS/FAIL/UNAVAILABLE/NA | Position | post-grant construction | grant, fee facts, TT_NUMERIC_V1 | Yes |
| Portfolio capacity/tranche sizing | state, limits, slots, daily base | grant/block/hold | Portfolio | grant and hold points | Portfolio config, TT_NUMERIC_V1 | Yes |
| Lifecycle financial final result | actual executions, fees, funding, costs | FINAL result or blocked | Lifecycle | canonical close finality | governed currency, TT_NUMERIC_V1, evidence | Yes |

Surrounding orchestration, persistence and contract validation can be built before individual formula implementations only if they preserve these owner boundaries and do not substitute placeholder business outputs. Sources: `docs/trading-methodology/methodology/POSITION_RULES.md`, `9. Fixed Stop Loss semantics` through `31. Minimum Net Edge formula`; `docs/trading-methodology/methodology/SET.md`, `10. Trigger result and event contract`; `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`; `docs/trading-methodology/schemas/NUMERIC_POLICY.md`.

## 13. Research / Backtest / Demo Target Model

Research, backtest, paper/demo and live implementations must use the same versioned semantics for the same Set version. Source: `docs/trading-methodology/methodology/SET.md`, `Part V - Canonical Runtime Invariants`. TECHNICAL_DERIVATION: research/backtest/demo execution should run against isolated simulated adapters and persisted run records that pin methodology package revision, contract versions, Set/Trigger/Position/Portfolio configuration IDs and content digests, numeric policy IDs, historical market selectors/source snapshots, adapter/profile assumptions, and execution simulation assumptions.

Backtest execution replays historical Market Data Request selections and deterministic owner state machines without live side effects. Demo/paper execution may use the same business modules with non-live adapters, but must preserve the same contracts and identifier semantics. Active comparison and promotion/make-active gates are not fully specified as software workflow in the canonical docs; the docs require research reporting and versioned/auditable formulas but do not prescribe a backend promotion UI or database design. Sources: `docs/trading-methodology/methodology/PORTFOLIO_RULES.md`, `63. Research and diagnostics`; `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`, `43. Research and diagnostics`; `docs/trading-methodology/methodology/POSITION_RULES.md`, `47. Research parameters`, `48. Required research reporting`; `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`, `6. Implementation conformance`.

## 14. API / Exchange Adapter Target Model

The API/exchange adapter boundary transports and normalizes facts and performs native order/cancel operations only under Lifecycle authority. Market facts include ticker, bid/ask, klines, volume, open interest, funding rate, raw trades, turnover and instrument metadata under Set-owned selections. Portfolio facts include account/wallet/equity/positions/orders/history, instrument and fee facts, but API creates no grant/cycle/eligibility decision. Order facts include create/cancel responses, open orders, order history, executions, positions, hard execution facts and financial facts for Lifecycle.

Normalization must preserve raw source values, source endpoint/record IDs, field-level provenance, native IDs, missing/UNAVAILABLE distinctions, pagination/completeness and native profile versions. Error/unavailable behavior returns unavailable/partial/retryable classifications; required missing or contradictory facts block owner state instead of being guessed. Idempotency uses persisted request IDs, client order IDs, native IDs and accepted evidence bindings. Ordering uses authoritative timestamps/profile sequencing where proven, never arrival order or lexical IDs. Sources: `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md`, `1. Authority and version`, `5. Pagination, completeness and deterministic assembly`; `docs/trading-methodology/api-contracts/PORTFOLIO_DATA_REQUEST.md`, `Purpose and authority`; `docs/trading-methodology/api-contracts/ORDER_MANAGEMENT.md`, `F01 / F02 / F04 / F06 normalized factual semantics (contract v4)`; `docs/trading-methodology/api-contracts/NATIVE_FACT_PROFILE.md`, `Runtime verification still required`.

## 15. Accounting / Financial Finality Target Model

Portfolio owns daily realized P&L posting, daily loss latch, base, capital/slot release and receipts. Lifecycle is the sole logical-tranche final financial producer; it computes gross result from actual executions, allocates fees/rebates/funding/supported costs from complete evidence, derives `accounting_day_id` from proven permanent final closing execution using the copied Portfolio accounting policy, and publishes one FINAL result only when coverage and currency admissibility are complete. API supplies factual wallet/equity/cashflow/execution rows but does not allocate logical tranche accounting.

Realized P&L: Lifecycle computes FINAL logical result; Portfolio posts once by `result_id` and `tranche_id`. Unrealized P&L and current equity: API facts exposed/merged by Portfolio for live state, not a substitute for final logical result. Fees/rebates/funding/costs: exchange/API facts attributed by Lifecycle; funding uses the separate existing algorithm. Unsupported cross-currency monetary evidence is retained and blocks FINAL; no conversion is authorized. Final records are immutable; later contradictions create post-final integrity incidents and may block future eligibility or pending receipt release, but do not silently rewrite the final ledger. Sources: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P7 - Complete Lifecycle financial evidence`, `P7.1 - Currency admissibility before logical financial FINAL`, `P8 - Economic time, operational time and accounting day`, `T01 - Separate terminal result and post-final integrity incident`; `docs/trading-methodology/business-contracts/ORDER_EVENT.md`, `Financial result`.

## 16. Web / API / Operator Boundary

TECHNICAL_DERIVATION: the web/API/operator layer should expose read models from persisted owner state and submit idempotent audited commands into owner inboxes. It must not own market analysis, capital rules, Position formulas, exchange mechanics, accounting finality or state repair. Read paths can query projections for Portfolio health, Set cycles, Position decisions, Lifecycle states, evidence/quarantine, accounting and research results. Command paths may request manual cancel/close, reconciliation, configuration activation, or research runs only through owner-command handlers.

Operator actions that can affect orders, exposure, configuration or reconciliation must be authenticated/authorized conceptually, have stable command IDs, be auditable, and be replay-safe. UI cannot calculate Entry/SL/TP, approve trades, release capital, infer filled exposure, compute final P&L, or decide market invalidation. Sources: `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`, `11.2 Manual Cancel`, `7. Position close conditions`; `docs/trading-methodology/methodology/PORTFOLIO_RULES.md`, `54A. No-repair invariant`; `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P1`.

## 17. Cloud / Container Runtime Requirements

TECHNICAL_DERIVATION from restart/replay and 24/7 obligations: durable state cannot depend on a developer machine or ephemeral local filesystem. Runtime configuration and secrets must come from environment or secret storage, not source files or UI payloads. Processes need health/readiness that reflects ability to hydrate state, reach persistent storage and safely process/outbox side effects. Graceful shutdown must stop new side effects after lease loss and leave committed outboxes/inboxes resumable. Migrations must be reproducible because state schemas carry immutable facts, versioned config, checkpoints and receipts. Worker recovery must hydrate consumed authorization tombstones, close intents, child authority, market selectors, accepted evidence, incidents and receipts before processing.

No specific cloud vendor, queue product, ORM or database physical schema is mandated by methodology. Persistent database capability is technically necessary because in-memory state cannot satisfy durable transaction, restart and replay obligations. Sources: `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`, `Appendix A - Tranche-isolated protection and close protocol`, `Appendix F - Native adapter conformance gate`; `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `X03`, `Y01-Y02`; `docs/trading-methodology/README.md`.

## 18. Target Testing Model

| Test Layer | Purpose | Major Areas Covered |
|---|---|---|
| Unit | Validate owner-local deterministic functions | formulas, gate predicates, serialization, identifier validation |
| Contract | Validate strict message/API schemas | all business contracts, API requests/responses, unknown-field rejection |
| State-machine | Validate lifecycle transitions | Portfolio health/holds, Set epochs/monitors, Position two-stage flow, Lifecycle states |
| Formula golden vectors | Prove numeric behavior | TT_NUMERIC_V1, TT_SET_NUMERIC_V1, Entry/SL/TP/R:R/Net Edge |
| Persistence | Prove durability and hydration | pins, facts, current state, checkpoints, receipts, tombstones |
| Concurrency | Prove atomic boundaries | grants, holds, close acquire/join, child authority, allocation receipts |
| Replay | Prove duplicate/reordered behavior | outbox/inbox dedupe, delayed messages, known-content challenges |
| Restart | Prove crash cutpoints | before/after commits, ambiguous dispatch, resumed reconciliation |
| Reconciliation | Prove source/evidence handling | native observations, protection proof, financial coverage, post-final incidents |
| Integration | Prove components together | full contract edges, persisted worker flows |
| Exchange adapter | Prove factual/native profile conformance | Bybit mappings, pagination, chronology, acceptance, hard facts |
| Research/backtest | Prove isolated deterministic runs | version pins, historical selectors, metrics, no live side effects |
| End-to-end | Prove material flows | paper/demo/live-disabled submission, cancel, close, final accounting |

Sources: `docs/trading-methodology/schemas/NUMERIC_POLICY.md`, `6. Canonical serialization and replay`; `docs/trading-methodology/schemas/SET_NUMERIC_POLICY.md`, `6. Implementation conformance`; `docs/trading-methodology/api-contracts/MARKET_DATA_REQUEST.md`, `6. Producer/consumer validation`; `docs/trading-methodology/api-contracts/NATIVE_FACT_PROFILE.md`, `Runtime verification still required`.

## 19. Target Backend Invariants

1. Business topology remains four blocks plus factual API, no fifth business block. Source: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P1 - Topology and approval/construction sequence`.
2. Portfolio manages own committed capital, not leveraged notional. Source: `docs/trading-methodology/methodology/PORTFOLIO_RULES.md`, `Part IX - Canonical Portfolio Rules Invariants`.
3. Set alone creates `decision_cycle_id` for MATCHED opportunities. Source: `docs/trading-methodology/methodology/SET.md`, `2.3 Canonical decision-cycle correlation ID`.
4. Direction is Set-owned and immutable downstream. Source: `docs/trading-methodology/methodology/SET.md`, `5. Direction belongs to Set`.
5. Position has no direct API flow. Source: `docs/trading-methodology/methodology/POSITION_RULES.md`, `2. Governing architecture`.
6. Initial APPROVE has no grant, hold, tranche, spec or final economics. Source: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P1`.
7. Capital and Limits is an immutable grant, not a reservation. Source: `docs/trading-methodology/business-contracts/CAPITAL_AND_LIMITS.md`, `Issue timing and binding`.
8. Successful construction publishes immutable spec and Portfolio confirmation together. Source: `docs/trading-methodology/business-contracts/ORDER_SPEC.md`, `Immutable post-grant construction`.
9. Lifecycle submits only after matching Order Spec and Submit Authorized. Source: `docs/trading-methodology/methodology/ORDER_LIFECYCLE.md`, `3. Order Lifecycle start condition`.
10. POST_ONLY marketability is decided by the exchange, not a local bid/ask gate. Source: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P3 - POST_ONLY belongs to the exchange`.
11. One active close intent per tranche; all close callers acquire-or-join. Source: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P5 - Atomic acquire-or-join and reduction authority`.
12. CLOSED requires all six P6 predicates; zero exposure alone is insufficient. Source: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P6 - CLOSED is one unified predicate composed of six required conditions and explicit retained commitment`.
13. Lifecycle is sole logical-tranche final financial producer. Source: `docs/trading-methodology/business-contracts/ORDER_EVENT.md`, `Financial result`.
14. Started cycles and attempts retain immutable configuration pins across restart. Source: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P17 - Immutable configuration binding for started cycles and attempts`.
15. Duplicate/reordered evidence must not duplicate effects or erase known contradictions. Source: `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `Y01-Y02 owner-local evidence retention synchronization`.

## 20. Technical Decisions NOT Determined by Methodology

| Decision | Status |
|---|---|
| HTTP/web framework | OPEN_TECHNICAL_DECISION |
| Worker framework/process supervisor | OPEN_TECHNICAL_DECISION |
| Queue/outbox implementation technology | OPEN_TECHNICAL_DECISION |
| Physical database engine and schema | OPEN_TECHNICAL_DECISION |
| ORM/query layer | OPEN_TECHNICAL_DECISION |
| Serialization library and canonical JSON implementation | OPEN_TECHNICAL_DECISION |
| Exchange SDK vs direct REST/WebSocket implementation | OPEN_TECHNICAL_DECISION |
| Exact cloud provider/topology | OPEN_TECHNICAL_DECISION |
| Authentication/authorization product | OPEN_TECHNICAL_DECISION |
| Observability/logging/metrics stack | OPEN_TECHNICAL_DECISION |
| Research job orchestration tooling | OPEN_TECHNICAL_DECISION |
| Migration tool and deployment pipeline shape | OPEN_TECHNICAL_DECISION |

These choices must be made later without changing approved business behavior. Source: `docs/trading-methodology/README.md`; `docs/trading-methodology/SYSTEM_PROTOCOLS.md`, `P1`; `docs/trading-methodology/api-contracts/NATIVE_FACT_PROFILE.md`, `Runtime verification still required`.

## Final Summary Inputs

- Target runtime components identified: 6.
- Target modules identified: 22.
- Contract/message boundaries identified: 15.
- Persistent state categories identified: 7.
- Identifier/lineage entities identified: 40.
- Transaction/concurrency boundaries identified: 13.
- Formula integration boundaries identified: 11.
- Target backend invariants identified: 15.
- OPEN_TECHNICAL_DECISION items identified: 12.
- Sufficiency for As-Is vs To-Be comparison: yes, subject to comparing current implementation against these projected components, state categories, contracts, identifiers, and invariants.
