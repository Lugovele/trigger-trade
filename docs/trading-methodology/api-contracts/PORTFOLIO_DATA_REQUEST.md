# TriggerTrade — Portfolio Data Request API Contract

**Boundary:** `Portfolio Rules ↔ API`  
**Contract version:** `5`  

## Purpose and authority

Portfolio independently requests API account facts for its capital/gate/rollover state. It owns capital allocation, cooldown, Daily Loss, Coins, post-APPROVE grants and submission holds. The API creates neither grant nor cycle identity. It never decides eligibility. Lifecycle independently retrieves its financial evidence over Order Management; Portfolio does not forward financial facts to Lifecycle or produce logical-tranche accounting.

## Request modes and coherence

SNAPSHOT requests current account/wallet/positions/orders and governed instrument/fee facts. HISTORY requests the explicit half-open interval of executions, cashflows/funding/order history needed for reconciliation or boundary reconstruction. Empty symbols means the dedicated managed-account scope only when neither instrument_metadata nor fee_rates is requested. Either symbol-scoped section requires an explicit nonempty unique symbol list. Historical and current sections do not pretend to be one atomic snapshot. ATOMIC is legal only with authoritative atomic source evidence; otherwise COMPOSITE preserves per-section source/as-of and overall collection times.

Every requested section must appear with status AVAILABLE, PARTIAL or UNAVAILABLE. Unrequested symbol-scoped sections must be omitted; unrequested other sections may be omitted. Requested wallet, equity, realized/unrealized account metrics are transported in account; fee/funding/realized cash postings use cashflows with component classification, with funding as a typed filtered view. No duplicate view is new money. Requested instruments/fees use their dedicated sections. Missing account values are null when unavailable, never fabricated zero. Available mandatory values must be non-null. Partial/inconsistent evidence prevents LIVE/new exposure.

Coherence is established by reconciled executions/known lifecycle transitions, persisted source watermark/coverage and complete current authoritative refresh, not by an invented grant-age threshold. A required endpoint outage or contradictory source scope is unavailable. Native factual revisions remain source identities; arrival order or lexical revision comparison never selects truth. A newer compatible revision does not invalidate the immutable grant. Portfolio atomically rechecks gates/capacity at hold time.

## Monetary evidence, provenance and boundaries

The financial row/coverage types are the same shared definitions used independently by Order Management. cashflow_id and aliases identify one actual source monetary event across representations. signed_amount is wallet-effect; fee and funding source conventions remain component-specific (SYSTEM_PROTOCOLS P7). Source identity, execution/order lineage, effective time, native currency/amount/quantum, funding settlement-basis evidence and source normalization mapping remain available for reconciliation. No cross-currency valuation is supported by this baseline; SYSTEM_PROTOCOLS P7.1 and `../schemas/NUMERIC_POLICY.md` §2A require every monetary source/component of a logical FINAL result to already be in its pinned governed accounting/settlement currency. Retain contrary native currency facts unchanged; they block logical finality rather than disappearing, becoming zero or being converted heuristically. COMPLETE source coverage and an arbitrary nonempty currency string in the shared schema do not override this semantic rule. Portfolio uses wallet/API facts for account capital and Lifecycle FINAL results for logical Daily Loss; it does not derive a competing logical result from these rows.

HISTORY is COMPLETE only with exhaustive requested intervals, pagination/completeness/watermark/finality evidence and no missing ranges. Required partial/unavailable evidence fails closed. A direct authoritative boundary wallet snapshot or COMPLETE deterministic cashflow reconstruction establishes daily base; a later arbitrary snapshot never replaces a missed boundary. The unchanged day policy is Asia/Jerusalem local midnight. Late logical results post to their immutable economic day, do not rebase the current base and are not added again to wallet capital.

## Governed instrument and fees

After an initial Position APPROVE, Portfolio copies current required instrument/fee facts and exact provenance into the immutable Capital and Limits for that decision. No grant exists in the initial approval. For linear LIMIT/PostOnly entry, max_order_qty comes from lotSizeFilter.maxOrderQty, not deprecated postOnlyMaxOrderQty. AVAILABLE requires a positive value and provenance; missing applicable required max remains UNAVAILABLE, never guessed. NOT_APPLICABLE requires verified adapter-profile evidence. No direct Position API lookup is introduced.

## State merge and triggers

Order Event, rollover, restart, reconnect and explicit/health reconciliation may trigger refresh. API-confirmed account/native facts are merged with durable Portfolio holds and logical allocation state. Absence of a native order does not erase a local hold. Physical zero native exposure does not release a CLOSE_PENDING tranche's closing_retained_committed_capital. P6 and the strict CLOSED event control logical release. P8 controls final-only Daily Loss and accounting days. P9 controls native block clearing; one partial allocation never clears an observation.

## Canonical request/response

### PORTFOLIO_DATA_REQUEST.request

```yaml
portfolio_data_request:
  contract_version: 5
  request_id: string
  requested_at: RFC3339-timestamp
  request_mode: SNAPSHOT | HISTORY
  scope:
    account: boolean
    wallet: boolean
    positions: boolean
    open_orders: boolean
    recent_orders: boolean
    executions: boolean
    fees: boolean
    funding: boolean
    realized_pnl: boolean
    unrealized_pnl: boolean
    instrument_metadata: boolean
    fee_rates: boolean
    cashflows: boolean
  filters:
    symbols:
    - string
    since:
      nullable: RFC3339-timestamp
    until:
      nullable: RFC3339-timestamp
```

### PORTFOLIO_DATA_REQUEST.response

```yaml
portfolio_data_response:
  contract_version: 5
  request_id: string
  response_id: string
  request_mode: SNAPSHOT | HISTORY
  response_consistency:
    mode: ATOMIC | COMPOSITE
  snapshot_started_at: RFC3339-timestamp
  snapshot_completed_at: RFC3339-timestamp
  as_of: RFC3339-timestamp
  source: exchange_api
  account:
    status: AVAILABLE | PARTIAL | UNAVAILABLE
    as_of: RFC3339-timestamp
    source_endpoint: string
    account_id: string
    equity:
      nullable: decimal-string
    wallet_balance:
      nullable: decimal-string
    available_balance:
      nullable: decimal-string
    unrealized_pnl:
      nullable: decimal-string
    realized_pnl:
      nullable: decimal-string
  positions:
    status: AVAILABLE | PARTIAL | UNAVAILABLE
    as_of: RFC3339-timestamp
    source_endpoint: string
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
    items:
    - symbol: string
      side: BUY | SELL
      position_idx: nonnegative-integer
      size: decimal-string
      avg_entry_price: decimal-string
      mark_price: decimal-string
      position_value: decimal-string
      unrealized_pnl: decimal-string
      realized_pnl: decimal-string
  open_orders:
    status: AVAILABLE | PARTIAL | UNAVAILABLE
    as_of: RFC3339-timestamp
    source_endpoint: string
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
    items:
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
  recent_orders:
    status: AVAILABLE | PARTIAL | UNAVAILABLE
    as_of: RFC3339-timestamp
    source_endpoint: string
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
    items:
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
    status: AVAILABLE | PARTIAL | UNAVAILABLE
    as_of: RFC3339-timestamp
    source_endpoint: string
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
    items:
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
  funding:
    status: AVAILABLE | PARTIAL | UNAVAILABLE
    as_of: RFC3339-timestamp
    source_endpoint: string
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
    items:
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
  cashflows:
    status: AVAILABLE | PARTIAL | UNAVAILABLE
    as_of: RFC3339-timestamp
    source_endpoint: string
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
    items:
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
  instrument_metadata:
    status: AVAILABLE | PARTIAL | UNAVAILABLE
    items:
    - symbol: string
      status: AVAILABLE | PARTIAL | UNAVAILABLE
      facts:
        nullable:
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
      as_of: RFC3339-timestamp
      source_endpoint: string
      source_record_id: string
      reason_code:
        nullable: string
  fee_rates:
    status: AVAILABLE | PARTIAL | UNAVAILABLE
    items:
    - symbol: string
      status: AVAILABLE | PARTIAL | UNAVAILABLE
      facts:
        nullable:
          maker_fee_rate: decimal-string
          taker_fee_rate: decimal-string
          fee_schedule_version: string
          effective_at: RFC3339-timestamp
          as_of: RFC3339-timestamp
          source_ref: string
      as_of: RFC3339-timestamp
      source_endpoint: string
      source_record_id: string
      reason_code:
        nullable: string
```

The YAML is a generated shape illustration; `nullable: TYPE` denotes a nullable value, not a literal object. Strict types, requiredness, unknown-field rejection and variants are defined in [`wire.schema.json`](../schemas/wire.schema.json), with shared producer/consumer bindings in [`CONTRACT_REGISTRY.json`](../schemas/CONTRACT_REGISTRY.json). Decimal values are exact strings. All invariants below are mandatory in addition to schema validation.

## F08 batched symbol sections (contract v5)

The selected policy is **multi-symbol batch**, not single-symbol-only. Each requested instrument_metadata and fee_rates section is `{status, items}`. Items must exactly cover filters.symbols once each. Each strict item carries symbol, status AVAILABLE/UNAVAILABLE, facts/non-null or facts/null respectively, as_of, source_endpoint, source_record_id and reason_code. Available facts.as_of equals item.as_of. Aggregate status is AVAILABLE/all, UNAVAILABLE/none, PARTIAL/mixed. Empty wildcard symbols are legal only for requests without these scopes. Technical adapter fan-out does not add a business edge.

A requested BTC+ETH batch cannot silently return only BTC. If ETH is unavailable, an explicit ETH unavailable item is required. Consumer validation rejects duplicates, missing/extra symbols, incorrect aggregate status or fabricated available facts. Partial mandatory evidence cannot open new exposure. Shared order/execution row extensions use the same F01/F02/F06 semantics as Order Management; they do not transfer logical accounting ownership to Portfolio.
