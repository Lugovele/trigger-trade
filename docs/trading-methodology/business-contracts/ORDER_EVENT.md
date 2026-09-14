# TriggerTrade — Order Event and Native Attribution Resolution

**Flow:** `Order Lifecycle → Portfolio Rules`  
**Contract version:** `7`  

## Strict variants and authority

LOGICAL_TRANCHE is lineage-strict and comes only after successful Position construction. Native observations do not use its IDs. Native/exchange-generated children may have null client identity when none exists; no client ID is fabricated. Accepted order-specific facts require a known exchange order ID. Lifecycle revisions are monotonic by decision cycle; snapshots cannot regress cumulative fills or terminal facts. A delayed event does not erase newer truth.

NATIVE_UNATTRIBUTED_REDUCTION has only native/account factual scope, stable observation identity and **native_scope_revision**, independent of decision_cycle_id. It blocks affected new exposure without inventing logical lineage. NATIVE_ATTRIBUTION_RESOLUTION is the complete/progress manifest on this same boundary, not another edge.

See [P9](../SYSTEM_PROTOCOLS.md#p9--native-observation-and-complete-attribution-resolution). A complete manifest identifies the entire expected allocation set, exact amounts/evidence and complete revision. Known-tranche allocation events reference that resolution and allocation ID. Portfolio may clear an observation only after complete evidence **and all expected allocations applied exactly once**. A first allocation or manifest without all allocations is insufficient. Resolution-first delivery creates a provisional unresolved tombstone from the provided native identity/scope; a complete validated manifest plus every expected allocation can resolve it before the original observation message arrives (P9). The later matching observation cannot regress that resolved tombstone. Resolved/unresolved tombstones, revisions and deduplication survive restart. Old replay cannot regress resolved state. Other outstanding observations continue to block.

## Cumulative closing state and commitment

`exposure_qty` is actual attributable exposure; it is never fabricated for accounting. `close_commitment_quantity_basis` is null until close acquisition, then the fixed committed quantity at that acquisition (filled plus still-committed entry remainder). It lets Portfolio retain the entire logical own-capital commitment even when physical exposure is zero. `close_intent_active` and terminal predicates must agree with the lifecycle state. P6 governs the retained accounting bucket and exact CLOSED predicate. All six terminal predicates must be true for CLOSED, the entry remainder and exposure must be zero, the intent resolved and FINAL result present. Intermediate TP/SL/Manual executions never release capital/slot. Definitive zero-fill/no-create terminals remain separate.

## Financial result

Lifecycle is the sole logical-tranche final financial producer. It gets mandatory evidence through its own Order Management API boundary. `financial_result` is null until the atomic canonical CLOSED publication and is FINAL only with COMPLETE mandatory coverage, deterministic execution/funding/fee attribution and stable result ID. P7.1 additionally requires every participating monetary component and required underlying source amount to already be in the tranche's pinned governed accounting/settlement currency; `financial_result.currency` is that unit. Unsupported cross-currency evidence remains retained and keeps the result absent/null and finality/release blocked, even with COMPLETE source coverage. No cross-currency conversion is supported. No provisional result exists. Portfolio does not recompute logical P&L from an aggregate native position.

P7 defines signs: actual_fees_rebates and other_supported_exchange_costs are cost-effect totals (negative rebate/refund increases net result); allocated_funding is signed receipt/payment. Gross result is reconstructed from tranche executions; duplicate financial source representations cannot be added as new money. Planned fees never substitute for actual fees.

P8 fixes `accounting_effective_at` to the proven permanent final closing execution, `accounting_day_id` to its Portfolio accounting policy, `closed_at` to operational cleanup completion and `finalized_at` to financial evidence completion. `terminalized_at` marks the final CLOSED transaction. Portfolio records first `delivered_at` in its receipt ledger, not inside an immutable producer financial result. Late historical posting updates only its immutable historical day, never current Daily Loss or current daily base, and never adds P&L to wallet twice.

API facts remain authoritative for wallet/equity/native executions. Portfolio retains its own holds and logical allocation state; an API snapshot is not authority to erase a local hold or release a flat-but-nonterminal commitment. Material Lifecycle state and event outbox commit atomically. A first final result posts/releases once only after the T01 committed-prefix/incident fence permits it; identical event or result replay has no monetary side effect.

## Canonical payloads

### ORDER_EVENT.logical

```yaml
order_event:
  contract_version: 7
  event_variant: LOGICAL_TRANCHE
  event_id: string
  event_type: string
  occurred_at: RFC3339-timestamp
  lifecycle_revision: nonnegative-integer
  authorization_id:
    nullable: string
  capital_grant_id: string
  decision_cycle_id: string
  set_result_id: string
  position_decision_id: string
  construction_result_id: string
  position_plan_id: string
  tranche_id: string
  order_spec_id: string
  symbol: string
  order_leg:
    role: ENTRY | TP | SL | MANUAL_CLOSE | EXTERNAL_REDUCTION | OTHER
    client_order_link_id:
      nullable: string
    exchange_order_id:
      nullable: string
    parent_exchange_order_id:
      nullable: string
    protection_generation:
      nullable: nonnegative-integer
    close_intent_id:
      nullable: string
    close_child_id:
      nullable: string
    protection_child_id:
      nullable: string
  native_allocation:
    nullable:
      native_observation_id: string
      native_scope_revision: nonnegative-integer
      attribution_resolution_id: string
      resolution_revision: nonnegative-integer
      allocation_id: string
      allocated_quantity: decimal-string
      source_execution_ids:
      - string
  lifecycle_state: READY_TO_SUBMIT | SUBMITTING | SUBMISSION_UNCERTAIN | PENDING_ENTRY
    | PARTIALLY_FILLED | OPEN | CANCEL_PENDING | CANCELLED_ZERO_FILL | CLOSE_PENDING
    | CLOSED | SUBMISSION_FAILED | RECONCILING | MANUAL_INTERVENTION_REQUIRED
  exposure_qty: decimal-string
  cumulative_entry_filled_qty: decimal-string
  remaining_entry_qty: decimal-string
  close_intent_active: boolean
  close_commitment_quantity_basis:
    nullable: decimal-string
  terminal_predicates:
    logical_exposure_zero: boolean
    entry_remainder_terminal: boolean
    children_terminal_or_disabled: boolean
    close_intent_resolved: boolean
    financial_finality_established: boolean
    no_competing_execution_authority: boolean
  external_cause:
    nullable: LIQUIDATION | ADL | OTHER_EXCHANGE
  financial_result:
    nullable:
      result_id: string
      result_version: 3
      tranche_id: string
      financial_state: FINAL
      gross_realized_trading_result: decimal-string
      actual_fees_rebates: decimal-string
      allocated_funding: decimal-string
      other_supported_exchange_costs: decimal-string
      net_realized_result: decimal-string
      currency: string
      source_lineage:
        execution_ids:
        - string
        cashflow_ids:
        - string
        native_observation_ids:
        - string
        final_closing_execution_id: string
      source_coverage:
        status: COMPLETE
        coverage_from: RFC3339-timestamp
        coverage_to: RFC3339-timestamp
        missing_ranges:
        - from: RFC3339-timestamp
          to: RFC3339-timestamp
        pagination_complete: true
        next_cursor: null
        source_watermark_at: RFC3339-timestamp
        source_finality_confirmed: true
        source_endpoints:
        - string
        reason_code:
          nullable: string
      accounting_effective_at: RFC3339-timestamp
      accounting_day_id: string
      accounting_policy:
        accounting_timezone: Asia/Jerusalem
        day_boundary_local: 00:00:00
        accounting_policy_version: ACCOUNTING_DAY_V1
      closed_at: RFC3339-timestamp
      finalized_at: RFC3339-timestamp
      terminalized_at: RFC3339-timestamp
      accounting_algorithm_version: string
      non_funding_allocations:
      - allocation_id: string
        manifest_id: string
        source_cashflow_id: string
        source_execution_id: string
        native_scope:
          account_id: string
          environment: LIVE | TEST
          symbol: string
          native_side: BUY | SELL
          position_idx: nonnegative-integer
        attribution_resolution_id:
          nullable: string
        attribution_resolution_revision:
          nullable: nonnegative-integer
        tranche_id: string
        allocation_revision: 1
        allocation_algorithm_version: EXEC_CASHFLOW_ALLOC_V1
        source_signed_amount: decimal-string
        source_amount_quantum: decimal-string
        allocated_quantity: decimal-string
        execution_price: decimal-string
        weight: decimal-string
        total_weight: decimal-string
        allocated_signed_amount: decimal-string
        residue_recipient_tranche_id: string
      numeric_policy_version: TT_NUMERIC_V1
  entry_accepted_at:
    nullable: RFC3339-timestamp
  entry_acceptance_status: PROVEN | UNAVAILABLE | NOT_APPLICABLE | CONFLICT
  entry_acceptance_provenance:
    nullable:
      source_endpoint: string
      source_record_id: string
      source_field: string
      native_value: string
      mapping_profile_version: string
      evidence_ref: string
  numeric_policy_version: TT_NUMERIC_V1
  entry_acceptance_integrity:
    state: CLEAR | CONFLICT | RESOLVED
    revision: nonnegative-integer
    conflict_id:
      nullable: string
    evidence:
    - source_endpoint: string
      source_record_id: string
      source_field: string
      native_value: string
      mapping_profile_version: string
      evidence_ref: string
    resolution_id:
      nullable: string
    resolution_evidence_ref:
      nullable: string
```

### ORDER_EVENT.native

```yaml
order_event:
  contract_version: 7
  event_variant: NATIVE_UNATTRIBUTED_REDUCTION
  event_id: string
  event_type: NATIVE_EXPOSURE_REDUCTION_UNATTRIBUTED
  occurred_at: RFC3339-timestamp
  native_observation:
    native_observation_id: string
    native_scope_revision: nonnegative-integer
    native_scope:
      account_id: string
      environment: LIVE | TEST
      symbol: string
      native_side: BUY | SELL
      position_idx: nonnegative-integer
    source_event_id: string
    source_execution_id:
      nullable: string
    exchange_order_id:
      nullable: string
    parent_exchange_order_id:
      nullable: string
    client_order_link_id:
      nullable: string
    quantity: decimal-string
    price:
      nullable: decimal-string
    effective_at: RFC3339-timestamp
    external_cause: LIQUIDATION | ADL | OTHER_EXCHANGE
    logical_attribution_state: UNRESOLVED
    source_ref: string
```

### ORDER_EVENT.resolution

```yaml
order_event:
  contract_version: 7
  event_variant: NATIVE_ATTRIBUTION_RESOLUTION
  event_id: string
  occurred_at: RFC3339-timestamp
  resolution:
    native_observation_id: string
    native_scope_revision: nonnegative-integer
    attribution_resolution_id: string
    resolution_revision: nonnegative-integer
    native_scope:
      account_id: string
      environment: LIVE | TEST
      symbol: string
      native_side: BUY | SELL
      position_idx: nonnegative-integer
    expected_allocation_ids:
    - string
    affected_tranche_ids:
    - string
    allocations:
    - allocation_id: string
      tranche_id: string
      decision_cycle_id: string
      allocated_quantity: decimal-string
      source_execution_ids:
      - string
      allocation_evidence:
      - string
    observed_quantity: decimal-string
    resolution_complete: boolean
    resolved_at:
      nullable: RFC3339-timestamp
```

The YAML is a generated shape illustration; `nullable: TYPE` denotes a nullable value, not a literal object. Strict types, requiredness, unknown-field rejection and variants are defined in [`wire.schema.json`](../schemas/wire.schema.json), with shared producer/consumer bindings in [`CONTRACT_REGISTRY.json`](../schemas/CONTRACT_REGISTRY.json). Decimal values are exact strings. All invariants below are mandatory in addition to schema validation.

## Acceptance and final split evidence (contract v7)

The cumulative logical variant carries numeric_policy_version and immutable original entry_accepted_at/status/provenance under P10. A higher lifecycle revision cannot change that timestamp; an older event may enrich a missing proven fact without reverting cumulative state. Unknown acceptance remains null, never updated_at/fill/receipt time. Cancellation tombstones prevent contribution resurrection. Native observation/resolution variants continue to prohibit fabricated logical identities.

financial_result version 3 carries numeric_policy_version and the current tranche's committed non_funding_allocations under P12. Shared-source mandatory allocations must be complete and atomically committed before FINAL; direct one-tranche attribution may leave the collection empty. Source/execution/resolution identity and exact signed allocations are evidence, not a request for Portfolio to allocate. P13 derives the immutable permanent final closing execution/time in economic chronology; P8 still controls the accounting day and historical loss attribution.

## Acceptance integrity and no-reduction variants — current family v7

Every cumulative logical event includes `entry_acceptance_integrity`. CLEAR means no unresolved contradictory authoritative acceptance evidence; CONFLICT is independently blocking even when the immutable first timestamp is known; RESOLVED requires an explicit newer authoritative incident resolution. Integrity revision is per authorization/attempt, not a global event order. Publish acceptance_status CONFLICT for CONFLICT; do not project a conflicted ledger as PROVEN. Original/conflicting provenance and resolution tombstones survive restart and stale replay. P10 governs the exact merge and clearance rules.

NATIVE_SCOPE_RECONCILIATION_OBSERVED is truthful native-scope evidence for a live/unresolved protective child or contradictory native facts with no proven reduction. It contains no logical IDs. Its native order/scope/provenance and quantity_effect NONE cannot be relabeled as an execution reduction. Portfolio persists the observation and affected scope block without changing quantities or financial balances.

NATIVE_SCOPE_RECONCILIATION_RESOLUTION carries partial or complete authoritative clearance on this same boundary. Its full expected binding set must be delivered and verified for OWNERSHIP_PROVEN; for a single observed child this is one proven owner. AUTHORITATIVELY_TERMINAL instead requires terminal/disabled proof and no outstanding authority, without fabricated bindings. No source-cashflow or quantity allocation is implied. P15 governs identity, per-observation revisions, partial delivery, resolution-first processing, post-clearance conflicts and persistent tombstones; P9 reduction attribution remains separate.

Lifecycle financial finalization and CLOSED publication use the current P13 revision-bound proof. The retained acceptance-integrity wire semantics do not loosen any existing terminal predicate, accounting-day rule or once-only result handling.

### ORDER_EVENT.scope_observation

```yaml
order_event:
  contract_version: 7
  event_variant: NATIVE_SCOPE_RECONCILIATION_OBSERVED
  event_id: string
  event_type: NATIVE_SCOPE_RECONCILIATION_OBSERVED
  occurred_at: RFC3339-timestamp
  native_observation:
    native_observation_id: string
    native_scope_revision: nonnegative-integer
    native_scope:
      account_id: string
      environment: LIVE | TEST
      symbol: string
      native_side: BUY | SELL
      position_idx: nonnegative-integer
    exchange_order_id: string
    order_role: ENTRY | TP | SL | MANUAL_CLOSE | EXTERNAL_REDUCTION | OTHER | UNKNOWN
    native_position_mode:
      nullable: HEDGE_MODE | ONE_WAY_MODE
    observation_class: PROTECTIVE_CHILD_LINEAGE_UNRESOLVED | NATIVE_ORDER_FACT_CONFLICT
    quantity_effect: NONE
    factual_linkage:
      native_parent_order_id:
        nullable: string
      native_parent_client_order_link_id:
        nullable: string
      native_link_group_id:
        nullable: string
      client_order_link_id:
        nullable: string
    logical_attribution_state: UNRESOLVED
    blocking_scope:
      account_id: string
      environment: LIVE | TEST
      symbol: string
      native_side: BUY | SELL
      position_idx: nonnegative-integer
    source_endpoint: string
    source_record_id: string
    provenance:
    - normalized_field: string
      source_endpoint: string
      source_record_id: string
      source_field: string
      native_value: string
      mapping_profile_version: string
      evidence_ref: string
    observed_at: RFC3339-timestamp
    reason_code: string
    reconciliation_resolution_id:
      nullable: string
    resolution_revision: nonnegative-integer
```

### ORDER_EVENT.scope_resolution

```yaml
order_event:
  contract_version: 7
  event_variant: NATIVE_SCOPE_RECONCILIATION_RESOLUTION
  event_id: string
  occurred_at: RFC3339-timestamp
  resolution:
    native_observation_id: string
    native_scope_revision: nonnegative-integer
    native_scope:
      account_id: string
      environment: LIVE | TEST
      symbol: string
      native_side: BUY | SELL
      position_idx: nonnegative-integer
    exchange_order_id: string
    reconciliation_resolution_id: string
    resolution_revision: nonnegative-integer
    expected_binding_ids:
    - string
    bindings:
    - binding_id: string
      exchange_order_id: string
      tranche_id: string
      decision_cycle_id: string
      order_role: TP | SL | MANUAL_CLOSE | ENTRY
      evidence_refs:
      - string
    disposition: PENDING | OWNERSHIP_PROVEN | AUTHORITATIVELY_TERMINAL
    resolution_complete: boolean
    no_unresolved_execution_authority: boolean
    native_order_terminal_or_disabled: boolean
    evidence_refs:
    - string
    resolved_at:
      nullable: RFC3339-timestamp
```

## Semantic synchronization (contract version unchanged)

Order Event version 7 remains the governed wire contract. Its finalized logical financial result is computed from every attributable factual execution price exactly once, with a source-revision-bound authoritative checkpoint only where exactly equivalent. Planned Entry or a stale original average must not replace actual later entry costs. LONG fully closed gross is exit value minus entry value; SHORT uses the reverse sign. Actual fee/rebate, funding and supported costs keep their existing independent factual evidence and signs.

CLOSED publication binds current closure/authority/coverage proofs and an atomically resolved close intent. Contradictory post-final execution evidence creates durable integrity quarantine rather than a rewritten final result or repeated receipt. For native-scope no-reduction variants, equal accepted observation revision with changed canonical content must be checked before a cleared tombstone suppresses stale replay; resulting safety blocking has zero execution/cashflow effect. See SYSTEM_PROTOCOLS S01/S03/S05/S06. No new wire fields or version changes are introduced.


## Post-final integrity — active ORDER_EVENT v7

`POST_FINAL_INTEGRITY` is a distinct governed variant, not a logical lifecycle
regression. The producer is Order Lifecycle and the consumer is Portfolio Rules.
SYSTEM_PROTOCOLS T01 defines its immutable identity, source proof, monotonic
revision/state, resolution-first conflict handling, scope block and receipt
linearization. T02 reuses it for financial contradictions. It never reopens CLOSED,
changes an accepted result, supplies a quantity reduction, starts another close,
or reverses a posted receipt. UNKNOWN economic receipt status is valid because
Portfolio, not Lifecycle, owns that ledger. Incident and result dedupe are separate.

Producer incident persistence, quarantine and outbox append are atomic. Portfolio
must consume the committed scope prefix and recheck its incident index at the
same receipt/final-gate fence; undelivered committed incidents therefore withhold
pending receipt/release. A mere local boolean or ungoverned event_type is invalid.
The transport frontier is an existing-edge technical ordering fact, not a native
revision or business owner. See SYSTEM_PROTOCOLS T01 for the precise transaction.

Native quantity variants retain their shapes at this family version. T04 requires
pre-manifest allocations to be staged with zero quantity effect, and complete
membership/source conservation before applying any valid member. Complete
attribution and absence of all integrity blocks are distinct predicates.

### Deterministic incident_class taxonomy

The required enum is classified by the subject of the contradiction, not by which handler discovered it:

- `POST_FINAL_EXECUTION_CONTRADICTION`: factual execution/exposure chronology changes, including a newly discovered/conflicting fill, execution quantity/price/side/source, or a native observation contradiction with a factual quantity/execution effect.
- `POST_FINAL_FINANCIAL_CONTRADICTION`: monetary evidence changes, including fees, rebates, funding, supported realized costs/cashflows, financial source-set membership, financial coverage/completeness, immutable financial-source core, or monetary attribution/finality evidence.
- `POST_FINAL_PROOF_CONTRADICTION`: only non-monetary control/ownership/authority/terminality proof changes, including acceptance, protection, close/child authority, native-scope ownership/clearance, or lifecycle/reconciliation proof.

Precedence: execution/fill-history effect -> EXECUTION; otherwise monetary-accounting effect -> FINANCIAL; otherwise control/ownership/terminality proof -> PROOF. Financial coverage certificates are FINANCIAL. Lineage/ownership-only native observations are PROOF. Classification does not change the existing blocking, receipt or release semantics.

### Strict post-final integrity wire shape

```yaml
order_event:
  contract_version: 7
  event_variant: POST_FINAL_INTEGRITY
  event_id: string
  integrity_incident:
    incident_id: string
    incident_revision: nonnegative-integer
    incident_state: OPEN | RESOLVED
    incident_class: POST_FINAL_EXECUTION_CONTRADICTION | POST_FINAL_FINANCIAL_CONTRADICTION
      | POST_FINAL_PROOF_CONTRADICTION
    reason_code: string
    terminal_result_id: string
    terminal_result_digest: sha256-hex-string
    tranche_id: string
    decision_cycle_id:
      nullable: string
    authorization_id:
      nullable: string
    blocking_scope:
      account_id: string
      environment: LIVE | TEST
      symbol: string
      native_side: BUY | SELL
      position_idx: nonnegative-integer
    observed_at: RFC3339-timestamp
    evidence:
      evidence_id: string
      evidence_revision:
        nullable: nonnegative-integer
      content_digest: sha256-hex-string
      source: string
      provenance_ref: string
      evidence_ref: string
    economic_receipt_observation:
      status: UNKNOWN | PENDING | APPLIED
      receipt_id:
        nullable: string
      as_of:
        nullable: RFC3339-timestamp
      evidence_ref:
        nullable: string
    resolution:
      nullable:
        resolution_id: string
        resolved_at: RFC3339-timestamp
        evidence_ref: string
        terminal_result_unchanged: true
        evidence_reconciled: true
```


### T04 evidence references and consumer authority

The existing allocation_evidence strings name Lifecycle-retained source partition
and attribution proof. Lifecycle must validate that proof before producing a
complete resolution. Portfolio verifies the complete manifest and exact allocation
member bindings/observed total, not a newly invented independent native allocation
algorithm. Pre-manifest delivery stages zero effects. Missing/conflicting source
proof blocks COMPLETE at Lifecycle; it is not guessed by the receiving owner.

## Producer/consumer clarification — no version change

Contract version7 is retained byte-for-byte in the strict wire schema. SYSTEM_PROTOCOLS.md U02 expands the complete immutable source-core contradictions that must produce the existing POST_FINAL_INTEGRITY variant through explicit parent-result linkage. U03 requires owner and consumer to persist and compare canonical acceptance-resolution content before tombstone suppression; the existing resolution_evidence_ref binds immutable proof/reason. U04 preserves executed exposure, commitment and slot despite contradictory rejection. These are corrections to already required behavior, not new variants, fields, owners or dedupe domains. Pending receipt fencing and exactly-once already-applied posting are unchanged.


## V02/V03 expanded producer detection — version7 retained

SYSTEM_PROTOCOLS.md V02 expands only producer-side detection: all terminal authority/coverage handlers and previously observed proof revisions can publish the already defined POST_FINAL_INTEGRITY variant. The terminal result stays immutable, incident identity remains independent, and existing pending-receipt/future-eligibility semantics are unchanged. V03 revisionless native acceptance inconsistency is published through existing logical acceptance-integrity fields; it does not require another event variant or a new cooldown origin. No wire shape, contract_version value or producer/consumer ownership changes.


## W01/W03 — Expanded detection, unchanged v7 incident boundary

The v7 envelope, variants, producer/consumer and identifiers are unchanged. Conflicts at ANY accepted financial basis/allocation-resolution revision, and conflicts against owned native financial aliases, reach the existing POST_FINAL_INTEGRITY path when an explicit frozen parent result exists. Retain full raw evidence locally under the existing incident evidence reference. Pending receipt fencing and already-applied once-only posting remain unchanged. Native-only clearance-resolution contradictions use the existing native-scope block and retain the resolved tombstone; they require no fabricated financial-result or quantity lineage.


## X01 / X03 local persistence clarification

Contract version remains 7; no fields, variants, edges or producer/consumer ownership change. Acceptance consumers persist actual complete CLEAR, CONFLICT and RESOLVED revision bindings, including accepted UNAVAILABLE-CLEAR content. Compare any known revision before covered/stale suppression, regardless of a later resolution. Changed accepted content retains the original acceptance origin and tombstones while restoring integrity blocking; evidence-set ordering is not a change. Delivery event IDs are not acceptance proof IDs.

Authority ingestion retains known-evidence contradictions independently of unrelated invalid companion proofs. A parent result uses the existing POST_FINAL_INTEGRITY variant and committed-prefix receipt fence; already-applied postings remain once-only. These are local persistence/processing requirements in SYSTEM_PROTOCOLS X01/X03, not additional wire payloads.
