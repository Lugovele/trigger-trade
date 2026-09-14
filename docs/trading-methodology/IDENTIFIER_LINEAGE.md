# Identifier lineage — v1.2.14

**Status: IMPLEMENTATION SPECIFICATION BASELINE — APPROVED FOR IMPLEMENTATION**

Identifiers are opaque immutable persisted identities, not estimates inferred from symbol, timestamp, arrival order or heuristic matching. The table specifies semantic ownership; concrete UUID/ULID encoding is an implementation detail unless the native API restricts a client identifier. Proposal/plan identity alone implies neither reserved capital nor an existing native order/exposure.

| Identity | Sole creator / creation timing | Binding, persistence and consumer |
|---|---|---|
| `decision_cycle_id` | Set, before initial Position decision, when a concrete MATCHED opportunity is persisted | Exact symbol, configuration/version, matched Core Set and frozen contexts; preserved through decision, grant, plan, authorization and lifecycle. Not created by Portfolio. |
| Set formation epoch/config binding | Set, on each effective newer Coins OPEN before MATCHED | Keyed by symbol + OPEN `scope_revision`; persists Set/Trigger/Core Set `configuration_id`, version and content digest. Newer CLOSE or OPEN terminates unfinished older epoch state; MATCHED cycle retains its pinned configuration and is not reset by later Coins scope changes. |
| Set-local Trigger evaluation / transition-event binding | Set, before the evaluation/event advances unfinished formation | Binds Trigger ID/version, symbol, OPEN formation epoch, pinned configuration and exact authoritative evaluation/source identities. FALSE -> TRUE event binds its FALSE and TRUE evaluations and the TRUE effective timestamp; UNAVAILABLE interrupts continuity. Persist consumption, original deadlines and deduplication through restart. Old-epoch events never enter a new epoch. These internal identities do not replace P4 matched `trigger_occurrence_id` creation. See `methodology/SET.md` Part I §10. |
| Position configuration binding | Position, atomically when first evaluating Market Handoff for initial APPROVE/REJECT | `position_decision_id + decision_cycle_id` -> Position `configuration_id`, version, content digest. Same binding governs later post-grant construction and ORDER_SPEC provenance; restart never selects latest config. |
| Portfolio attempt configuration / cooldown binding | Portfolio, in atomic hold/authorization transaction before authorization publication | Existing `authorization_id + tranche_id` attempt binds Portfolio configuration identity/version/content digest and `pinned_cooldown_duration`; late acceptance computes deadline from this persisted duration, never current settings. |
| `set_result_id` | Set, when that concrete result is persisted | One immutable result for the cycle; replay never substitutes a newer result. |
| `core_set_id`, constituent occurrence IDs, Trigger version/reference IDs | Set/configuration producer; configured slots precede matching, concrete occurrences are persisted at MATCHED | `core_set_constituent_id + trigger_id + trigger_version + reference_key` binds the participating occurrence to concrete `level_id`. |
| `role_id`, `binding_id`, `level_id` | Set; role namespace in configuration, concrete binding/level identity from the actual matched Trigger/Core Set | P4 producer-side resolution only; Position validates/consumes, never reconstructs or ranks a replacement thesis reference. |
| `position_decision_id` | Position, persisted with initial OPPORTUNITY_DECISION | Bound to exact cycle/result. APPROVE/REJECT has this identity but no capital grant or finalized plan/tranche/spec. |
| Initial decision `event_id` | Position, same decision/outbox transaction | Delivery deduplication; semantic uniqueness also enforced by decision/cycle. |
| `capital_grant_id` | Portfolio, **only after persisted initial APPROVE**, in Capital and Limits issue transaction | Immutable capital/fact provenance plus cycle/result/decision. Duplicate APPROVE returns same grant. No reservation, no TTL, no supersession by revision age. |
| `construction_result_id` | Position, after receiving the exact grant and evaluating final construction | One persisted outcome. Successful outcome binds the completed spec; failure has no fabricated successful spec. Published on existing Approve / Reject edge. |
| `position_plan_id`, `tranche_id`, `order_spec_id` | Position, finalized only during successful post-grant construction | Immutable plan/spec, exact approved actual economics and all earlier lineage. A tranche is logical and may share a native side with another tranche. |
| `order_spec_digest` | Position, SHA-256 of canonical exact immutable spec envelope | Identical construction/authorization binding; consumers validate rather than recalculate a different trade. No self-referential digest field inside the spec. |
| `authorization_id` | Portfolio, atomically with successful current-gate/capacity check, grant consumption and SUBMISSION_HOLD | Binds grant/cycle/decision/construction/plan/tranche/spec/digest. Survives delayed spec and restart; no creation before hold. |
| `close_intent_id` | Lifecycle, only inside atomic durable acquire-or-join keyed by `tranche_id` | At most one active intent. All callers join; resolved tombstone survives replay. A losing pre-commit candidate ID has no durable authority. |
| Close child ID | Lifecycle, under the intent/authority transaction before side effect | One exact immutable authorized residual budget and parent intent; new child only after all earlier authority resolved. |
| Protective child ID/generation | Lifecycle logical child identity persisted before requested attachment; exchange supplies native-generated child identity | Persist all generations and exact parent/tranche lineage. No invented client ID for a native-generated child lacking one. |
| `client_order_link_id` | Lifecycle, persisted before the corresponding supported native create/close request | Same identity across ambiguous dispatch/restart; never mint a new client ID merely to retry a timeout. Null when unsupported for a native-generated child. |
| `exchange_order_id` | Exchange only, when supplied by authoritative response/event/history | Null/absent before supplied; acknowledgements do not prove execution/terminality. Lookup uses proven client/native linkage. |
| `execution_id` | Exchange fact (namespaced by account/venue/product where needed) | Lifecycle persists immutable execution plus exact tranche/child allocation. Duplicate streams/history representations do not double-apply quantity or fees. |
| `transaction_id`, funding transaction ID | Exchange financial source | Effective-time native transaction identity and provenance; never guessed from equal amounts/timestamps. Funding allocation eligibility/weights are persisted for that exact source. |
| `cashflow_id` | API normalization layer's stable factual identity backed by native transaction or exact execution-component identity | Includes proven aliases across endpoints; Lifecycle owns logical attribution, not the API or Portfolio. P7 forbids heuristic alias merging. |
| `native_observation_id` | Lifecycle normalization, when a distinct factual native observation is durably recorded | Independent of any Set cycle. Original source evidence and native scope immutable. No fabricated tranche/cycle identity. |
| `native_scope_revision` | Lifecycle durable per-native-scope sequence | Scope is account/environment/symbol/native side/position index. Same observation replay retains original revision. Higher watermark does not discard a previously unseen older observation. |
| `attribution_resolution_id` | Lifecycle, one durable resolution ledger identity per observation | Complete expected allocation set and all publication outboxes in one transaction; partial progress cannot clear exposure block. |
| `resolution_revision` | Lifecycle, within the resolution identity | Persist complete revision/digest and tombstones. Older replay cannot undo completion. Conflicting complete content is an integrity incident. |
| `allocation_id` | Lifecycle, when exact logical allocation is durably established | Bound to observation/resolution, tranche, quantity, source executions/evidence. Portfolio applies each once and clears only after complete manifest plus all expected allocations. |
| `lifecycle_revision` | Lifecycle, monotonic known-cycle/tranche state stream | Strict logical events only. Never required on lineage-free native observation/resolution variants. |
| `accounting_day_id` | Lifecycle derives and persists using Portfolio-owned accounting policy copied grant → spec | Day containing proven permanent final closing execution, not arrival/finalization/temporary zero. Portfolio verifies policy/day on receipt. |
| Financial `result_id` | Lifecycle, exactly once per tranche at canonical final transaction | Immutable FINAL value/source evidence, accounting timestamps/day, resolved close intent and CLOSED outbox. Portfolio deduplicates both result ID and tranche terminal posting. |
| `delivered_at` | Portfolio receiver's receipt record, first successful receipt/application transaction | Not a mutable field in producer's immutable result; late delivery does not change accounting day or wallet cashflow. |

## Timestamp ownership

`accounting_effective_at` is the effective time of the actual execution proven after reconciliation to have permanently reduced this logical tranche to zero. `closed_at` is the operational cleanup-complete marker; it does **not** alone assert lifecycle CLOSED. `finalized_at` is complete financial evidence/attribution finalization. `terminalized_at` records the atomic transition after all six CLOSED predicates. These markers are persisted, not inferred from receipt order. P8 specifies midnight, late-result and restart behavior.

## No pre-creation requirements

Initial decision → no grant/plan/tranche/spec. Grant → includes already-existing cycle/result/decision. Successful construction → final plan/tranche/spec. Hold → authorization. Native side effect intent → supported client/child identity first. Native order/execution → only exchange-supplied identity. Unknown native observation → its own identity/revision, no logical IDs until actual attribution. A complete resolution record names known logical IDs; no consumer invents missing lineage.

## Focused lineage additions (P10–P14)

Original entry_accepted_at and its native provenance are immutable exchange facts, persisted by Lifecycle and merged into Portfolio cooldown independently of delivery revision. Native parent order/client/group IDs are factual only; recover logical protection through a unique proven registry binding. Notification order_placed_at is not acceptance time.

P12 cashflow manifest_id and financial allocation_id are Lifecycle-owned deterministic identities derived from the exact source/exec/native-scope/resolution/tranche tuple, under EXEC_CASHFLOW_ALLOC_V1. They are distinct from P9 quantity allocation IDs; a source-commit tombstone prevents revised-ID double posting. Non-funding financial allocation occurs only after complete native quantity proof.

P13 execution chronology retains stable execution_id, authoritative timestamp and verified native sequence/domain/subsequence. IDs are not sorted as economic truth. P14's order_spec_contract_version and numeric_policy_version join the existing target/digest binding. Definitive no-create authorization terminality is durable; no replay creates another grant/hold or reuses released authority.

## Technical identities (existing owners and edges)

| Identity | Creator / first existence | Persistence and replay role |
|---|---|---|
| No-reduction native_observation_id | Lifecycle when an actual native order/scope is observed unresolved | Versioned factual scope+native-order identity; no symbol/time logical reconstruction; durable journal/tombstone. |
| No-reduction native_scope_revision | Lifecycle within that native observation | Monotonic source-content revision; not a global ordering or a different observation's revision. |
| reconciliation_resolution_id / resolution_revision | Lifecycle on authoritative clearance evidence | Bound to native observation/scope/order; partial-to-complete proof and resolved tombstone. |
| binding_id (no-reduction clearance) | Lifecycle only after factual child ownership is proven | Full declared binding set; never minted from matching trigger geometry. |
| acceptance conflict_id / integrity revision | Lifecycle for an attempt's authoritative acceptance contradiction | Stable attempt-bound incident plus monotonic evidence state, separately consumed by Portfolio. |
| acceptance resolution_id | Lifecycle on explicit authoritative incident resolution | Immutable evidence reference and covered-evidence tombstone; cannot change original accepted_at. |
| selection_id | Set before historical/as-of data request | Fixed symbol/dataset/window/cutoff identity across page requests and restart. |
| request_id | Set per persisted technical page request | Retry of identical request is idempotent; cursor does not mutate selection identity. |
| source_snapshot_id / page_id | Factual API adapter for one governed source selection snapshot | Stable page identities and complete page manifest; no mixing source snapshots. |
| indicator checkpoint_id | Set after canonical ordered source processing | TT_SET_NUMERIC_V1 state and source-manifest digest; restore only matching policy/ancestry. |

No new business owner, premature grant/tranche ID or fifth block is created. Existing economic allocation IDs, funding IDs, close intent IDs and execution chronology retain their original ownership.

## Global receipts and derived-evidence bindings

The existing native quantity allocation ID immutably binds native_observation_id, attribution_resolution_id, account/environment/native scope and its revision, source execution/evidence identity with source revision/content, target tranche_id and allocated quantity. Its once-only application registry is global in the existing namespace, not a dictionary local to one observation. Original binding, staged proof, committed quantity receipt and complete-resolution tombstone survive restart. Quantity effect and receipt commit together. A conflicting rebinding is an integrity incident; a new allocation ID cannot disguise reuse of the same source under a different observation. Complete manifest-first delivery retains explicit native scope/revision, total and resolution identity, never symbol/time reconstruction.

Derived closure proofs identify their complete durable revision vector and authoritative source certificates. Derived market assemblies identify the immutable selector, request(s), source snapshot, complete page manifest and page/record/completeness content digests. Native-scope cleared tombstones retain actual accepted observation-revision content history before replay filtering. These are durable technical evidence bindings within existing owners; no business edge, new wire message, or heuristic logical identity is introduced.


## T01/T02 incident identities and T04 source-effect proof

| Identifier / proof | Creator and first existence | Immutable binding / replay |
|---|---|---|
| incident_id | Lifecycle, first post-final contradiction transaction | Protected result ID/digest, known tranche, scope, reason, factual evidence identity/digest; independent of result dedupe |
| incident_revision | Lifecycle incident journal | Per-incident monotonic domain; known same-version content conflict blocks before stale filtering |
| evidence_id / content_digest | Lifecycle evidence journal over normalized source proof | Native revision nullable when unavailable; no fabricated revision from local arrival |
| incident event_id | Lifecycle outbox | Canonical incident revision payload; same payload retries retain first observed_at |
| terminal receipt | Portfolio at fenced first application | Unique result_id and tranche_id; immutable result/day; incident discovered later cannot reverse or duplicate it |
| scope committed-prefix frontier | Existing-edge technical outbox/inbox transport | Orders append against receipt/final-gate transaction only; not a lifecycle/native revision or new business block |
| source quantity proof | Lifecycle native attribution from authoritative factual evidence | Scope, observation/resolution, execution/evidence revision/content, original total; no guessed lineage |
| source slice | Lifecycle complete attribution proof | Half-open exact quantity interval within original source; per-allocation lengths equal allocated_qty; complete partition disjoint and conserved |
| source consumption receipt | Lifecycle atomic quantity application | Full allocation binding + frozen complete proof digest; source consumed total and tranche effect commit once together |

Existing IDs, ownership and edges remain unchanged. T01 wire payload is
ORDER_EVENT.integrity v7. T04 slices are internal proof, not new API operations.


## V01–V05 retained identity bindings

No new wire identifier is introduced. SYSTEM_PROTOCOLS.md V01 compares accepted canonical cashflow identity before applicability routing; V02 retains complete authority/coverage content for each observed accepted/supplemental revision without changing final result identity. V03 binds the complete acceptance observation to its governed provenance identity and preserves accepted resolution tombstones. V04 separates current effective proof-dependency digests from historical child identities. V05 retains known page/snapshot/manifest/record contradictions without allocating replacement page revisions. Existing post_final_incident_id, terminal-result identity, decision_cycle_id, tranche identity, source-set revision and exact-once receipt domains remain unchanged.


## W01–W03 retained identity history

Proof identity/revision is owner-local and binds full accepted canonical content plus digest, evidence/member set and completeness, including partial and permitted supplemental proof. Numeric age does not suppress a changed known revision. Hydration retains actual historical bindings; it never reconstructs old contents from latest. Native clearance tombstones survive reblocking and imply no quantity effect.

Historical page ownership is the accepted request/selection/page/snapshot/native-source relationship, not an incoming selection echo or arbitrary page label. An ownership contradiction invalidates the originally bound CURRENT selection and retains raw evidence without changing frozen handoffs.

Financial ownership can be reached by canonical cashflow ID or accepted primary/alias provenance. A new claimed cashflow ID cannot evade a known native owner. Governed same-canonical-ID representation enrichment remains allowed; conflicting ownership is quarantined before routing. No identifier creator, wire field, financial allocation identity or business boundary changes.


## X01–X03 durable content identities

No new wire identifier is introduced. Within the existing acceptance attempt lineage, integrity_revision indexes actual canonical accepted/published content for every state, not only a latest RESOLVED tombstone. An event_id identifies delivery, not a replacement acceptance fact. Hydration must retain each actual old binding.

Historical request -> governed selection/digest -> accepted pages/snapshot -> scoped source-record identity remains authoritative even if both incoming selector/page echoes change. Incoming values cannot rewrite those accepted edges.

Known authority/coverage/native-proof challenges retain their existing incident identity and parent-result linkage across companion semantic failure. Normal proof updates are a separate atomic outcome from integrity capture. Frozen financial_result_id and once-only Portfolio receipt keys remain unchanged; post-final incident identity remains independent.


## Y01/Y02 persistence clarification — no new wire identity

Order Lifecycle's owner-local observation_bindings index is keyed by the existing native_observation_id. It persists original accepted_scope_revision, authoritative_source_quantity, full native_scope, actually supplied additional source/provenance facts and referenced accepted source-quantity provenance. The original observation, allocation-binding/receipt domain and resolution tombstone are not rekeyed. A raw conflicting replay has a stable content-deduplicated incident; JSON hydration must preserve it and scope blocking.

Coverage history remains indexed by actual component and accepted revision and retains complete certificate bindings, not only current values. Raw preflight may recover the actual owner from accepted certificate identity when an incoming echo is missing; it must not rewrite ownership from the echo. Raw omitted/malformed challenges, quarantine and existing post-final incident identities persist separately from immutable coverage and terminal-result histories. Parent-result linkage, receipt identity and posting deduplication are unchanged. Accepted-evidence identity/ownership lookup is part of Order Lifecycle-owned evidence preflight and owns no separate business state.


## Financial coverage certificate identity — current binding

No wire identifier is added. Lifecycle's accepted overall certificate key is `(request_id, response_id, GET_FINANCIAL_FACTS, OVERALL)`. A component certificate key is `(request_id, response_id, GET_FINANCIAL_FACTS, COMPONENT, component)`. Lifecycle creates the owner-local accepted record at first accepted proof and assigns a monotonic `accepted_certificate_revision` in the request/kind/component scope. The immutable record persists the parent request/response, native scope and requested interval, complete coverage fields, component applicability fields where relevant, raw response evidence/provenance reference, canonical basis digest and exact accepted source-member set.

Indexes persist the primary key plus exact unique anchors permitted by SYSTEM_PROTOCOLS Y02 (`response_id`; request + kind/component; evidence/provenance reference; or exact basis/source-member identity when present in raw evidence). Hydration restores those historical indexes and certificate content before ingestion. Missing or malformed ordinary echoes do not authorize heuristic reconstruction. One exact anchor may recover one accepted owner; ambiguity quarantines, no match is unrelated. Reusing an accepted key/revision with changed content is an integrity contradiction. Omission and explicit null are distinct canonical states during raw preflight.
