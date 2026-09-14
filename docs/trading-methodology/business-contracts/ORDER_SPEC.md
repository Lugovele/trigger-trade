# TriggerTrade — Order Spec

**Flow:** `Position Rules → Order Lifecycle`  
**Contract version:** `5`  

## Immutable post-grant construction

Created only after initial opportunity APPROVE and its matching Capital and Limits. Position owns all final plan/tranche/spec identities and approved prices, quantity, leverage, notional and economics. The spec and `CONSTRUCTION_RESULT(CONSTRUCTED)` are durably published together. The report carries the SHA-256 digest of this exact envelope; Portfolio's matching authorization repeats it. The spec itself does not contain its own digest.

`economics.funding_in_planned_net_edge: false` is required and canonical in every embedded/standalone representation. An enabled Minimum Net Edge is PASS; a disabled one is NOT_APPLICABLE. No failed/unavailable gate materializes a spec. Scope PARTIAL_QUANTITY denotes tranche-specific native protection, not scale-out, multiple TP targets or strategic partial close.

Lifecycle creates client order identities only when persisting the corresponding execution intent. Position must not create them. Exchange order IDs remain unknown until the exchange supplies them. Receipt alone never authorizes submission. Matching Order Spec + Submit Authorized, full lineage and digest are required.

## Exact execution and revisions

See P2–P3 in `../SYSTEM_PROTOCOLS.md`. The instrument/fee revisions used for construction remain immutable provenance. Lifecycle compares the exact spec with current hard technical constraints; a newer compatible revision is accepted without altering the spec. An incompatible hard constraint follows technical failure/reconciliation. No local bid/ask marketability gate, grant TTL, repricing, quantity resize, leverage change, chase or market fallback exists.

The accounting policy is copied unchanged from the grant; it creates no Position accounting authority. Approved Entry/SL/TP formulas and thresholds remain in the Position methodology. Same native symbol/side aggregation does not merge logical-tranche ownership.

## Canonical payloads

### ORDER_SPEC

```yaml
order_spec:
  contract_version: 5
  order_spec_id: string
  spec_created_at: RFC3339-timestamp
  capital_grant_id: string
  decision_cycle_id: string
  set_result_id: string
  position_decision_id: string
  construction_result_id: string
  position_plan_id: string
  tranche_id: string
  symbol: string
  direction: LONG | SHORT
  side: BUY | SELL
  entry:
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
  economics:
    target_order_notional: decimal-string
    actual_order_notional: decimal-string
    actual_committed_capital: decimal-string
    gross_rr: decimal-string
    planned_net_edge_pct: decimal-string
    minimum_net_edge_enabled: boolean
    minimum_net_edge_result: PASS | NOT_APPLICABLE
    maker_fee_rate: decimal-string
    taker_fee_rate: decimal-string
    fee_schedule_version: string
    fee_rate_source_ref: string
    funding_in_planned_net_edge: false
  venue_validation:
    max_order_qty_status: AVAILABLE | NOT_APPLICABLE
    max_order_qty:
      nullable: decimal-string
    max_order_qty_source_field: lotSizeFilter.maxOrderQty
    max_order_qty_source_ref: string
    native_profile_revision: string
  accounting_policy:
    accounting_timezone: Asia/Jerusalem
    day_boundary_local: 00:00:00
    accounting_policy_version: ACCOUNTING_DAY_V1
  provenance:
    set_version: string
    position_rules_version: string
    instrument_metadata_revision: string
    market_snapshot_at: RFC3339-timestamp
  numeric_policy_version: TT_NUMERIC_V1
```

The YAML is a generated shape illustration; `nullable: TYPE` denotes a nullable value, not a literal object. Strict types, requiredness, unknown-field rejection and variants are defined in [`wire.schema.json`](../schemas/wire.schema.json), with shared producer/consumer bindings in [`CONTRACT_REGISTRY.json`](../schemas/CONTRACT_REGISTRY.json). Decimal values are exact strings. All invariants below are mandatory in addition to schema validation.

## Pinned configuration provenance

`provenance.position_rules_version` is the exact Position Rules version pinned when Position first evaluated the originating Market Handoff, not whatever version is active when Capital and Limits arrives. Position's durable decision-cycle record also retains the pinned configuration identity and canonical content digest under P17. The final Order Spec, construction confirmation and all calculations therefore remain bound to one immutable Position configuration across replay/restart. `provenance.set_version` likewise identifies the Set configuration version frozen by the originating MATCHED cycle. Contract version 5 is unchanged because the required wire provenance fields already exist.

## F03 / F07 version synchronization

The spec is governed by TT_NUMERIC_V1 (`schemas/NUMERIC_POLICY.md`, P11) and exact P14 construction binding. Numeric value selection precedes canonical serialization/digest. All duplicated confirmation scalars and gate outputs equal the immutable spec independently of its digest. Confirmation and authorization explicitly target order_spec_contract_version 5; changed target identity/version/digest is non-submittable. Initial APPROVE still creates no grant or final trade IDs. A definitive no-create terminal authorization remains consumed; replay cannot restore a hold or resume submission. These checks add no business edge or trade-selection rule.
