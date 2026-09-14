# TriggerTrade — Capital and Limits

**Flow:** `Portfolio Rules → Position Rules`  
**Contract version:** `5`  

## Issue timing and binding

Issued **only after** Portfolio has durably accepted `OPPORTUNITY_DECISION(APPROVE)`. The Portfolio-owned `capital_grant_id` is created in that issue transaction, together with immutable provenance and durable publication. Initial APPROVE contains no such ID. The grant explicitly binds `decision_cycle_id`, `set_result_id`, `position_decision_id` and symbol. No capital is sent to Set.

All capital amounts are own-capital values. The grant itself consumes no capital or slot. It records a requested amount, not a promise that later Portfolio capacity remains available. Duplicate initial APPROVE or delayed grant delivery reuses the same immutable grant for the same opportunity. No cross-cycle rebinding, age expiry, automatic supersession, or trading TTL exists. New facts/grants do not mutate this one. Consumed/rejected construction cannot be reopened by replay.

## Required facts and revisions

See [P2](../SYSTEM_PROTOCOLS.md#p2--immutable-grants-and-current-hard-execution-compatibility). Position receives governed instrument/fee facts only through this route; Set supplies frozen market geometry. Instrument revision, native-profile revision, source references, as-of/effective times and fee schedule version are persisted. Missing required inputs fail post-grant construction rather than being guessed. A newer fact alone never invalidates an older grant; only incompatibility of the exact spec with a current hard native constraint can block execution. No changed Entry, leverage, quantity, TP or SL is permitted as a repair.

For the pinned linear LIMIT + POST_ONLY profile, `max_order_qty` is transported from `lotSizeFilter.maxOrderQty`. `postOnlyMaxOrderQty` is not a valid source. AVAILABLE requires a positive value/provenance. UNAVAILABLE is fail-closed when applicable. NOT_APPLICABLE requires adapter-profile evidence, never a missing field.

Portfolio supplies the unchanged accounting timezone/boundary policy; it is copied to Order Spec for Lifecycle's accounting-day derivation. Portfolio's later hold still atomically rechecks current gates/capacity. Lifecycle separately checks current hard non-market compatibility via Order Management. A fee-version change is not a local marketability or renewed economic gate.

## Canonical payloads

### CAPITAL_AND_LIMITS

```yaml
capital_and_limits:
  contract_version: 5
  capital_grant_id: string
  position_decision_id: string
  decision_cycle_id: string
  set_result_id: string
  symbol: string
  created_at: RFC3339-timestamp
  as_of: RFC3339-timestamp
  grant_state_at_issue: ISSUED
  portfolio_state_revision: nonnegative-integer
  requested_capital_per_tranche: decimal-string
  minimum_tranche_capital: decimal-string
  remaining_coin_capital: decimal-string
  remaining_global_capital: decimal-string
  remaining_coin_slots: nonnegative-integer
  remaining_global_slots: nonnegative-integer
  relevant_portfolio_limits:
    global_position_cap: decimal-string
    coin_allocation_cap: decimal-string
    max_open_positions: nonnegative-integer
    max_positions_per_coin: nonnegative-integer
    daily_loss_blocked: boolean
  accounting_policy:
    accounting_timezone: Asia/Jerusalem
    day_boundary_local: 00:00:00
    accounting_policy_version: ACCOUNTING_DAY_V1
  venue_facts:
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
    fees:
      maker_fee_rate: decimal-string
      taker_fee_rate: decimal-string
      fee_schedule_version: string
      effective_at: RFC3339-timestamp
      as_of: RFC3339-timestamp
      source_ref: string
  numeric_policy_version: TT_NUMERIC_V1
```

The YAML is a generated shape illustration; `nullable: TYPE` denotes a nullable value, not a literal object. Strict types, requiredness, unknown-field rejection and variants are defined in [`wire.schema.json`](../schemas/wire.schema.json), with shared producer/consumer bindings in [`CONTRACT_REGISTRY.json`](../schemas/CONTRACT_REGISTRY.json). Decimal values are exact strings. All invariants below are mandatory in addition to schema validation.

## F03 / F07 version synchronization

The grant is governed by TT_NUMERIC_V1 (`schemas/NUMERIC_POLICY.md`, P11) and exact P14 construction binding. Numeric value selection precedes canonical serialization/digest. All duplicated confirmation scalars and gate outputs equal the immutable spec independently of its digest. Confirmation and authorization explicitly target order_spec_contract_version 5; changed target identity/version/digest is non-submittable. Initial APPROVE still creates no grant or final trade IDs. A definitive no-create terminal authorization remains consumed; replay cannot restore a hold or resume submission. These checks add no business edge or trade-selection rule.
