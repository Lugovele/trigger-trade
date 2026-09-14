# TriggerTrade — Order Management API Contract

**Boundary:** `Order Lifecycle ↔ API`  
**Contract version:** `4`  

## Existing boundary, complete factual input

Order Lifecycle owns native client identities, submission, order/protection/close state, attribution, reconciliation and final logical financial results. API only supplies facts/translates exact technical requests. Neither API nor Portfolio creates a competing logical accounting result. No Position ↔ API or Portfolio → Lifecycle financial-fact edge is added.

## Supported operations

CREATE_ENTRY_ORDER; CANCEL_ENTRY_ORDER; GET_ORDER; GET_OPEN_ORDERS; GET_ORDER_HISTORY; GET_EXECUTIONS; GET_POSITION; SET_OR_ATTACH_TP_SL; CANCEL_PROTECTIVE_ORDER; CLOSE_POSITION_QUANTITY; GET_ACCOUNT_EXECUTION_FACTS; GET_FINANCIAL_FACTS; GET_HARD_EXECUTION_FACTS.

Each operation's full request/response definition is in the registry. GET_ACCOUNT_EXECUTION_FACTS is execution-oriented and is **not** an implicit substitute for complete financial history. GET_FINANCIAL_FACTS supplies the required financial input explicitly. GET_HARD_EXECUTION_FACTS supplies non-market native constraints before entry create; it does not return a POST_ONLY marketability decision.

## Financial currency transport and finality

Financial rows retain actual native source `currency`, exact amount/quantum, identity/aliases and provenance. API does not relabel currencies, convert amounts, suppress an unsupported-currency fact or produce a logical valuation. COMPLETE coverage describes factual completeness, not eligibility for final monetary aggregation. Under SYSTEM_PROTOCOLS P7.1 and `../schemas/NUMERIC_POLICY.md` §2A, Lifecycle admits FINAL only when every required monetary source/component is already in the tranche's pinned governed accounting/settlement currency. A required source in another currency is retained and keeps finality/capital/slot release blocked; this baseline supports no general conversion. Existing funding settlement/mark fields are allocation evidence, not an FX profile. Accepted-evidence comparison/contradiction retention occurs before currency rejection. The financial row shape and contract version remain unchanged.

## Entry, cancellation and native acknowledgement

CREATE_ENTRY_ORDER sends exact approved LIMIT + POST_ONLY with unchanged prices, quantity and leverage. API/exchange determines acceptance/rejection. Immediate fill after native acceptance is valid; no minimum resting time is required. Transport/request acknowledgement alone must not be normalized as confirmed order acceptance. ACCEPTED requires authoritative native accepted/order or execution evidence. Missing certainty is AMBIGUOUS; reconcile by persisted client/native identity before any retry. No local best-bid/ask crossing gate or fallback exists.

CANCEL_REQUEST_ACCEPTED means only request receipt, never terminal cancellation. ALREADY_TERMINAL requires authoritative order history/executions. Fills racing cancellation remain factual exposure. Evidence precedence remains executions → terminal history → open orders → native position cross-check → local state. A weaker or older response cannot reduce cumulative execution truth.

## Protection and close

The pinned operating profile remains Bybit linear USDT perpetual, HEDGE_MODE, ISOLATED, native symbol + positionIdx/side. Approved leverage must be compatible with an already occupied native side; it is never silently changed. Relevant exposure-changing operations remain disabled until runtime conformance verifies logical quantity isolation, protective-child lifecycle and native request semantics.

Use [P5](../SYSTEM_PROTOCOLS.md#p5--atomic-acquire-or-join-and-reduction-authority) for every close-related caller. Acquire-or-join is atomic/durable by tranche_id, with at most one active intent. It is an internal Lifecycle transaction, not an API business decision. Residual calculation and next-child authorization serialize with attributed entry/exit executions, protection states, all earlier authorized quantity and ambiguous requests. No timeout authorizes a new full-quantity close. Partial native execution is continuation of the same complete close intent, not strategic scale-out.

Every close request carries the durable close child, intent/revision, exact target/residual/authorized/executed quantities and execution-authority revision. Child state stores native order ID only once known. Native-generated children may have null user client IDs. Never cancel another tranche's protection. Entry remainder and competing children are reconciled before the next reduction; sibling protection is cleaned before canonical CLOSED, not afterward. A native reduce-only flag alone does not identify a logical tranche.

Definitive no-create technical failures follow SUBMISSION_FAILED with proof; ambiguity remains RECONCILING/incident escalation with hold retained. Exchange error retryable is a transport fact and cannot override no-blind-retry safety.

## GET_FINANCIAL_FACTS

The request declares native account/environment/symbol/side scope, half-open coverage interval, mandatory components, known factual identities and pagination cursor. No logical IDs are invented for native observations; correlation may be null for native/account-scoped factual lookup. The response includes executions and the shared normalized financial rows, overall and per-component coverage. Funding requires common effective-time settlement/mark price and provenance for the unchanged allocation algorithm.

COMPLETE requires every mandatory component interval covered, exhausted pagination, no missing ranges, authoritative watermark through the cutoff and confirmed source finality. PARTIAL/UNAVAILABLE prevents financial FINAL. Empty funding/cost rows count as zero only when COMPLETE or evidenced non-applicability proves that absence. Unknown sign mappings or duplicate aliases without proven identity also keep reconciliation unresolved. Source finality is evidence-based, not a timer.

Normalized signed_amount is wallet-effect (positive credit, negative debit). TRADING_FEE with a COST_POSITIVE source is negated; FUNDING with a CREDIT_POSITIVE source is preserved; other costs and wallet cashflows use their declared endpoint/field convention. Source amount, field, convention, direction, fee/rebate/funding classification and normalization profile are retained. These mappings must not be replaced by one generic sign rule. The pinned native adapter's mapping is a runtime conformance obligation. See P7 for exact examples and logical-result cost-effect conversion.

cashflow_id is one stable canonical posting identity with native transaction/execution evidence; overlapping endpoints are aliases, not additional money. No symbol/time/amount heuristic is allowed. Planned fee estimates and aggregate native P&L cannot fill missing actual logical evidence. Financial ledger, aliases, coverage/cursors and allocation identity are persisted across restart.

## GET_HARD_EXECUTION_FACTS

The API returns factual current instrument/profile/leverage compatibility inputs with complete provenance. Lifecycle compares them with the exact immutable spec under P2. A known newer max quantity 80 permits exact quantity 70 but forbids 90. A changed fee revision or mere revision age is not a hard entry gate. Unavailable required hard inputs keep reconciliation; incompatible exact inputs cause definitive no-create failure when no submit was sent. No resizing, Set rerun, price/SL/TP/leverage change or native POST_ONLY prediction occurs.

## External reductions

LIQUIDATION, ADL and OTHER_EXCHANGE are factual causes, not new strategy close triggers. Preserve actual native execution/order/parent identities. Unknown logical attribution is emitted through the native Order Event variant and later resolved by the complete allocation protocol P9. Never fabricate client, cycle or tranche IDs.

## Full request/response shape illustrations

### ORDER_MANAGEMENT.request.CREATE_ENTRY_ORDER

```yaml
order_management_request:
  contract_version: 4
  request_id: string
  operation: CREATE_ENTRY_ORDER
  requested_at: RFC3339-timestamp
  correlation:
    nullable:
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
  exchange_identity:
    client_order_link_id:
      nullable: string
    exchange_order_id:
      nullable: string
  payload:
    side: BUY | SELL
    order_type: LIMIT
    post_only: true
    price: decimal-string
    quantity: decimal-string
    leverage: decimal-string
    take_profit:
      mode: DYNAMIC | FIXED
      price: decimal-string
      execution_type: MARKET
      trigger_by: LAST_PRICE
      scope: PARTIAL_QUANTITY
      fixed_pct:
        nullable: decimal-string
    stop_loss:
      mode: DYNAMIC | FIXED
      price: decimal-string
      execution_type: MARKET
      trigger_by: LAST_PRICE
      scope: PARTIAL_QUANTITY
      fixed_pct:
        nullable: decimal-string
```

### ORDER_MANAGEMENT.request.CLOSE_POSITION_QUANTITY

```yaml
order_management_request:
  contract_version: 4
  request_id: string
  operation: CLOSE_POSITION_QUANTITY
  requested_at: RFC3339-timestamp
  correlation:
    nullable:
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
  exchange_identity:
    client_order_link_id:
      nullable: string
    exchange_order_id:
      nullable: string
  payload:
    close_intent_id: string
    intent_revision: nonnegative-integer
    tranche_id: string
    close_child_id: string
    native_side: BUY | SELL
    position_idx: nonnegative-integer
    role: MANUAL_CLOSE | TP | SL | EXTERNAL_REDUCTION
    confirmed_target_quantity: decimal-string
    confirmed_residual_quantity: decimal-string
    authorized_reduction_quantity: decimal-string
    executed_reduction_quantity: decimal-string
    quantity: decimal-string
    reduce_only: true
    client_order_link_id: string
    execution_authority_revision: nonnegative-integer
```

### ORDER_MANAGEMENT.request.GET_FINANCIAL_FACTS

```yaml
order_management_request:
  contract_version: 4
  request_id: string
  operation: GET_FINANCIAL_FACTS
  requested_at: RFC3339-timestamp
  correlation:
    nullable:
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
  exchange_identity:
    client_order_link_id:
      nullable: string
    exchange_order_id:
      nullable: string
  payload:
    native_scope:
      account_id: string
      environment: LIVE | TEST
      symbol: string
      native_side: BUY | SELL
      position_idx: nonnegative-integer
    coverage_from: RFC3339-timestamp
    coverage_to: RFC3339-timestamp
    required_components:
    - EXECUTIONS | TRADING_FEE | FUNDING | OTHER_EXCHANGE_COST
    exchange_order_ids:
    - string
    client_order_link_ids:
    - string
    execution_ids:
    - string
    cashflow_ids:
    - string
    cursor:
      nullable: string
```

## Financial coverage certificate identity and preflight

For accepted `GET_FINANCIAL_FACTS` evidence, Lifecycle—not API—maintains the durable certificate history defined by SYSTEM_PROTOCOLS Y02. No new wire field exists. Overall coverage is recognized by existing tuple `(request_id, response_id, GET_FINANCIAL_FACTS, OVERALL)`; each component certificate is recognized by `(request_id, response_id, GET_FINANCIAL_FACTS, COMPONENT, component)`. Lifecycle persists owner-local accepted revisions, canonical content/basis digests, source membership, provenance/evidence references and exact indexes needed for raw recognizable-proof preflight and restart.

Strict parsing does not precede comparison against an already accepted certificate. Raw omission and explicit null are distinct during preflight. If ordinary echoes are malformed/missing, only an exact uniquely indexed existing anchor permitted by Y02 may recover ownership; heuristic matching by symbol/time/value is forbidden. Financial coverage contradictions after FINAL map to `POST_FINAL_FINANCIAL_CONTRADICTION`. Contract version 4 is unchanged because identity is composed from existing envelope/component fields and owner-local persistence.

### ORDER_MANAGEMENT.response.financial

```yaml
order_management_response:
  contract_version: 4
  request_id: string
  response_id: string
  operation: GET_FINANCIAL_FACTS
  as_of: RFC3339-timestamp
  result: COMPLETE | PARTIAL | UNAVAILABLE
  financial_facts:
    native_scope:
      account_id: string
      environment: LIVE | TEST
      symbol: string
      native_side: BUY | SELL
      position_idx: nonnegative-integer
    requested_from: RFC3339-timestamp
    requested_to: RFC3339-timestamp
    coverage:
      status: COMPLETE | PARTIAL | UNAVAILABLE
      coverage_from: RFC3339-timestamp
      coverage_to: RFC3339-timestamp
      missing_ranges:
      - from: RFC3339-timestamp
        to: RFC3339-timestamp
      pagination_complete: boolean
      next_cursor:
        nullable: string
      source_watermark_at:
        nullable: RFC3339-timestamp
      source_finality_confirmed: boolean
      source_endpoints:
      - string
      reason_code:
        nullable: string
    component_coverage:
    - component: EXECUTIONS | TRADING_FEE | FUNDING | OTHER_EXCHANGE_COST
      applicable: boolean
      not_applicable_evidence:
        nullable: string
      coverage:
        status: COMPLETE | PARTIAL | UNAVAILABLE
        coverage_from: RFC3339-timestamp
        coverage_to: RFC3339-timestamp
        missing_ranges:
        - from: RFC3339-timestamp
          to: RFC3339-timestamp
        pagination_complete: boolean
        next_cursor:
          nullable: string
        source_watermark_at:
          nullable: RFC3339-timestamp
        source_finality_confirmed: boolean
        source_endpoints:
        - string
        reason_code:
          nullable: string
    executions:
    - execution_id: string
      client_order_link_id:
        nullable: string
      exchange_order_id: string
      parent_exchange_order_id:
        nullable: string
      symbol: string
      native_side: BUY | SELL
      position_idx: nonnegative-integer
      order_side: BUY | SELL
      quantity: decimal-string
      price: decimal-string
      executed_at: RFC3339-timestamp
      native_sequence:
        nullable: string
      fee_cashflow_id:
        nullable: string
      source_endpoint: string
      source_record_id: string
      native_sequence_domain:
        nullable: string
      native_subsequence:
        nullable: string
      chronology_profile_version:
        nullable: string
      chronology_provenance:
        nullable:
          normalized_field: string
          source_endpoint: string
          source_record_id: string
          source_field: string
          native_value: string
          mapping_profile_version: string
          evidence_ref: string
    cashflows:
    - cashflow_id: string
      transaction_id:
        nullable: string
      execution_id:
        nullable: string
      component_type: TRADING_FEE | FUNDING | REALIZED_TRADING_PNL | OTHER_EXCHANGE_COST
        | DEPOSIT | WITHDRAWAL
      currency: string
      signed_amount: decimal-string
      amount_quantum: decimal-string
      effective_at: RFC3339-timestamp
      recorded_at: RFC3339-timestamp
      symbol:
        nullable: string
      native_side:
        nullable: BUY | SELL
      position_idx:
        nullable: nonnegative-integer
      client_order_link_id:
        nullable: string
      exchange_order_id:
        nullable: string
      parent_exchange_order_id:
        nullable: string
      child_id:
        nullable: string
      fee_classification: FEE | REBATE | NOT_APPLICABLE
      funding_classification: PAYMENT | RECEIPT | NOT_APPLICABLE
      cost_classification: COST | REFUND | NOT_APPLICABLE
      source_endpoint: string
      source_record_id: string
      source_field: string
      source_amount: decimal-string
      source_sign_convention: COST_POSITIVE | CREDIT_POSITIVE | MAGNITUDE_WITH_DIRECTION
      economic_direction: DEBIT | CREDIT | ZERO
      normalization_profile_version: string
      aliases:
      - source_endpoint: string
        source_record_id: string
        source_field: string
      settlement_price:
        nullable: decimal-string
      settlement_price_basis:
        nullable: string
      settlement_price_as_of:
        nullable: RFC3339-timestamp
      settlement_source_ref:
        nullable: string
      pnl_scope: GROSS | NET | NOT_APPLICABLE
      period_scope: EVENT | INTERVAL | LIFETIME | NOT_APPLICABLE
  exchange_error:
    nullable:
      code: string
      message: string
      retryable: boolean
      category: VALIDATION | AUTH | RATE_LIMIT | CONNECTIVITY | EXCHANGE_UNAVAILABLE
        | ORDER_REJECTED | NOT_FOUND | UNKNOWN
```

### ORDER_MANAGEMENT.request.GET_HARD_EXECUTION_FACTS

```yaml
order_management_request:
  contract_version: 4
  request_id: string
  operation: GET_HARD_EXECUTION_FACTS
  requested_at: RFC3339-timestamp
  correlation:
    nullable:
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
  exchange_identity:
    client_order_link_id:
      nullable: string
    exchange_order_id:
      nullable: string
  payload:
    symbol: string
    native_side: BUY | SELL
    position_idx: nonnegative-integer
    approved_metadata_revision: string
    approved_native_profile_revision: string
    order_spec_id: string
```

### ORDER_MANAGEMENT.response.hard

```yaml
order_management_response:
  contract_version: 4
  request_id: string
  response_id: string
  operation: GET_HARD_EXECUTION_FACTS
  as_of: RFC3339-timestamp
  result: AVAILABLE | UNAVAILABLE
  hard_execution_facts:
    nullable:
      instrument:
        tick_size: decimal-string
        qty_step: decimal-string
        min_order_qty: decimal-string
        min_notional: decimal-string
        max_order_qty:
          nullable: decimal-string
        max_order_qty_status: AVAILABLE | UNAVAILABLE | NOT_APPLICABLE
        max_order_qty_source_field: lotSizeFilter.maxOrderQty
        max_leverage: decimal-string
        contract_type: LINEAR_USDT_PERPETUAL
        metadata_revision: string
        native_profile_revision: string
        instrument_supported: boolean
        position_mode: HEDGE_MODE
        margin_mode: ISOLATED
        as_of: RFC3339-timestamp
        source_ref: string
      native_configured_leverage:
        nullable: decimal-string
      supported_native_profile: boolean
      facts_complete: boolean
      checked_at: RFC3339-timestamp
      source_ref: string
  exchange_error:
    nullable:
      code: string
      message: string
      retryable: boolean
      category: VALIDATION | AUTH | RATE_LIMIT | CONNECTIVITY | EXCHANGE_UNAVAILABLE
        | ORDER_REJECTED | NOT_FOUND | UNKNOWN
```

### ORDER_MANAGEMENT.response.operation

```yaml
order_management_response:
  contract_version: 4
  request_id: string
  response_id: string
  operation: CREATE_ENTRY_ORDER | CANCEL_ENTRY_ORDER | GET_ORDER | GET_OPEN_ORDERS
    | GET_ORDER_HISTORY | GET_EXECUTIONS | GET_POSITION | SET_OR_ATTACH_TP_SL | CANCEL_PROTECTIVE_ORDER
    | CLOSE_POSITION_QUANTITY | GET_ACCOUNT_EXECUTION_FACTS
  as_of: RFC3339-timestamp
  result: ACCEPTED | REJECTED | AMBIGUOUS | CANCEL_REQUEST_ACCEPTED | ALREADY_TERMINAL
    | AVAILABLE | PARTIAL | UNAVAILABLE
  client_order_link_id:
    nullable: string
  exchange_order_id:
    nullable: string
  exchange_status:
    nullable: string
  orders:
  - client_order_link_id:
      nullable: string
    exchange_order_id: string
    symbol: string
    native_side: BUY | SELL
    position_idx: nonnegative-integer
    status: string
    cumulative_filled_quantity: decimal-string
    remaining_quantity: decimal-string
    average_fill_price:
      nullable: decimal-string
    updated_at: RFC3339-timestamp
    source_ref: string
    native_parent_order_id:
      nullable: string
    native_parent_client_order_link_id:
      nullable: string
    native_link_group_id:
      nullable: string
    order_role: ENTRY | TP | SL | MANUAL_CLOSE | EXTERNAL_REDUCTION | OTHER | UNKNOWN
    order_side:
      nullable: BUY | SELL
    order_type:
      nullable: LIMIT | MARKET
    order_quantity:
      nullable: decimal-string
    order_price:
      nullable: decimal-string
    trigger_price:
      nullable: decimal-string
    trigger_direction:
      nullable: RISE | FALL | NOT_APPLICABLE
    trigger_type:
      nullable: CONDITIONAL_PRICE | NOT_APPLICABLE
    trigger_source:
      nullable: LAST_PRICE | MARK_PRICE | INDEX_PRICE | NOT_APPLICABLE
    protected_qty:
      nullable: decimal-string
    protection_scope:
      nullable: PARTIAL_QUANTITY | FULL_POSITION
    reduce_only:
      nullable: boolean
    close_on_trigger:
      nullable: boolean
    native_position_mode:
      nullable: HEDGE_MODE | ONE_WAY_MODE
    stop_order_type:
      nullable: string
    native_create_type:
      nullable: string
    native_created_at:
      nullable: RFC3339-timestamp
    entry_accepted_at:
      nullable: RFC3339-timestamp
    entry_acceptance_status: PROVEN | UNAVAILABLE | NOT_APPLICABLE
    entry_acceptance_provenance:
      nullable:
        source_endpoint: string
        source_record_id: string
        source_field: string
        native_value: string
        mapping_profile_version: string
        evidence_ref: string
    source_endpoint: string
    source_record_id: string
    native_fact_provenance:
    - normalized_field: string
      source_endpoint: string
      source_record_id: string
      source_field: string
      native_value: string
      mapping_profile_version: string
      evidence_ref: string
  executions:
  - execution_id: string
    client_order_link_id:
      nullable: string
    exchange_order_id: string
    parent_exchange_order_id:
      nullable: string
    symbol: string
    native_side: BUY | SELL
    position_idx: nonnegative-integer
    order_side: BUY | SELL
    quantity: decimal-string
    price: decimal-string
    executed_at: RFC3339-timestamp
    native_sequence:
      nullable: string
    fee_cashflow_id:
      nullable: string
    source_endpoint: string
    source_record_id: string
    native_sequence_domain:
      nullable: string
    native_subsequence:
      nullable: string
    chronology_profile_version:
      nullable: string
    chronology_provenance:
      nullable:
        normalized_field: string
        source_endpoint: string
        source_record_id: string
        source_field: string
        native_value: string
        mapping_profile_version: string
        evidence_ref: string
  position:
    nullable:
      native_scope:
        account_id: string
        environment: LIVE | TEST
        symbol: string
        native_side: BUY | SELL
        position_idx: nonnegative-integer
      quantity: decimal-string
      as_of: RFC3339-timestamp
  coverage:
    nullable:
      status: COMPLETE | PARTIAL | UNAVAILABLE
      coverage_from: RFC3339-timestamp
      coverage_to: RFC3339-timestamp
      missing_ranges:
      - from: RFC3339-timestamp
        to: RFC3339-timestamp
      pagination_complete: boolean
      next_cursor:
        nullable: string
      source_watermark_at:
        nullable: RFC3339-timestamp
      source_finality_confirmed: boolean
      source_endpoints:
      - string
      reason_code:
        nullable: string
  exchange_error:
    nullable:
      code: string
      message: string
      retryable: boolean
      category: VALIDATION | AUTH | RATE_LIMIT | CONNECTIVITY | EXCHANGE_UNAVAILABLE
        | ORDER_REJECTED | NOT_FOUND | UNKNOWN
```

The YAML is a generated shape illustration; `nullable: TYPE` denotes a nullable value, not a literal object. Strict types, requiredness, unknown-field rejection and variants are defined in [`wire.schema.json`](../schemas/wire.schema.json), with shared producer/consumer bindings in [`CONTRACT_REGISTRY.json`](../schemas/CONTRACT_REGISTRY.json). Decimal values are exact strings. All invariants below are mandatory in addition to schema validation.


All other operation-specific request shapes are strict definitions in the same registry, using the same envelope and their declared lookup/protection payload. They are not permissive unknown-field extensions.

## F01 / F02 / F04 / F06 normalized factual semantics (contract v4)

The strict shared order_fact includes native parent order/client/group relationships, native protective role/types, trigger geometry/source, protected quantity/scope, reduce-only/close semantics, native position identity, creation time and field-level endpoint/record provenance. See `NATIVE_FACT_PROFILE.md` and P10: nullable missing facts stay missing; API does not invent logical IDs, child pairing or ownership. An outbound protection request is not a factual installed order.

Original entry acceptance is separately represented by entry_accepted_at/status/provenance. Creation/updated/fill/local time is never substituted. A live order with unknown original time remains a valid factual response with UNAVAILABLE acceptance; Lifecycle keeps cooldown evidence unresolved. Every shared producer/consumer uses the same strict definition, including Portfolio factual order collections.

Execution chronology fields preserve available native order evidence under P13. API supplies executions/cashflows and aliases only; Lifecycle proves quantity lineage and applies P12's non-funding split. The factual financial response never contains invented tranche allocations. Source cashflow quantum and identity remain factual; shared-source logical rows exist only in Lifecycle internal manifests and final Order Event results. Funding uses its unchanged separate algorithm.

## Consumer fact-merge clarification (wire unchanged)

Order Management remains contract v4. Its existing native fields/provenance can express enrichment; no new business decision is delegated to API. Lifecycle distinguishes immutable proven facts, unavailable-to-known enrichment and mutable factual state. Retain per-field authoritative provenance independently of the most recently observed endpoint; whole-row equality is not native consistency. The pinned profile must define mutable status/cumulative-fill/remaining/update ordering and terminal monotonicity. Without that evidence, do not overwrite proven state. The documented synthetic conformance profile uses authoritative updated_at plus nondecreasing cumulative fill and no terminal resurrection; this is a test profile, not certified native exchange behavior.

Acceptance source mappings remain exact and factual. API exposes the original accepted_at evidence, while Lifecycle aggregates contradictions and publishes their separate integrity state in Order Event v7. A known timestamp plus conflicting proof cannot become PROVEN eligibility. See SYSTEM_PROTOCOLS P10. Native deployment must verify mapping semantics, historical linkage recovery and mutable state order empirically.


## T03 — Current protection query evidence (active clarification, wire unchanged)

The caller persists request_id → exact native scope/selectors and response
identity/as_of/completeness evidence. A complete GET_OPEN_ORDERS result describes
that query generation's current members, not an append-only all-time union.
A later same-scope COMPLETE empty/subset response makes previous live-protection
verification insufficient. Lifecycle retains historical mapping, invalidates the
current-live proof and queries GET_ORDER_HISTORY/GET_EXECUTIONS on this same
boundary. Empty membership is not a terminal cancellation/fill certificate or
replacement authorization. Stale older complete queries do not restore current
proof; same-generation conflicting complete memberships require reconciliation.
History may enrich status under the existing field-aware native provenance rules
but does not itself declare current open membership. No new API wire field or
contract version is introduced; query completeness remains adapter-proven.

## Factual validation clarification — no version change

SYSTEM_PROTOCOLS.md U02 enumerates all immutable fields already present in financial_record. The adapter's factual aliases may supply explicitly proven equivalent representations, not inferred economic identity. U05 requires raw magnitude/direction semantic validation before signing, in addition to strict schema validation; COMPLETE coverage cannot legitimize an invalid sign pair. U04's zero-execution, terminal attempt and outstanding-authority predicates must come from factual order/execution evidence, never the word REJECTED alone. API remains factual/technical; Order Lifecycle owns logical attribution and final accounting. Existing coverage, normalized native facts, POST_ONLY behavior and contract version4 are unchanged.


## V02–V04 consumer synchronization — no wire change

Contract version remains 4. SYSTEM_PROTOCOLS.md V02–V04 require Lifecycle to ingest factual proof content before terminal/stale suppression, validate complete native acceptance time/status/provenance before covered replay suppression, and invalidate current protection proof atomically when facts returned by any operation change its dependencies. GET_ORDER_HISTORY terminal child facts cannot leave PROTECTION_VERIFIED merely because a later reconcile action has not run. The API still returns governed facts only; it does not resolve business ownership, create cooldown origins, replace protection or decide tranche closure. Existing provenance/lineage/query fields already represent the required evidence.


## W01/W03 — Known evidence before financial routing

Wire version, sign convention and financial arithmetic are unchanged. Lifecycle resolves canonical and accepted native primary/alias identity before execution, component or scope routing rejection, then compares the complete immutable source core. A changed claimed cashflow ID retaining an owned native identity is a contradiction, not foreign input; preserve source/effects and durably quarantine with raw evidence. Existing governed same-canonical-ID alias enrichment remains unchanged. Accepted financial factual-basis and allocation-resolution revisions retain complete canonical history before stale suppression, including partial/supplemental accepted proof. Existing ORDER_EVENT v7 incidents fence pending release or block future eligibility without rewriting frozen results.
