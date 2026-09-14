# TriggerTrade — Order Lifecycle → Set Sync Contract

**Flow:** `Order Lifecycle → Set`  
**Diagram label:** `Order Placed`  
**Contract version:** `3`  

## Purpose

Defines the single canonical Order Lifecycle → Set communication boundary.

This boundary carries two message variants:

```text
1. ORDER_PLACED
2. ENTRY_LIFECYCLE_EVENT
```

This does **not** create a second architecture arrow.

The architecture diagram may continue to label this boundary simply:

```text
Order Placed
```

---

## Variant 1 — ORDER_PLACED

Sent only after the exchange has actually accepted the entry order.

```yaml
order_placed:
  contract_version: 3
  event_id: string
  lifecycle_revision: nonnegative-integer
  decision_cycle_id: string
  set_result_id: string
  position_plan_id: string
  tranche_id: string
  symbol: string
  client_order_link_id: string
  exchange_order_id: string
  order_placed_at: RFC3339-timestamp
```

Set uses `decision_cycle_id` to locate the exact frozen invalidation conditions created for that cycle.

Canonical:

```text
ORDER_PLACED
→ Set locates frozen conditions
→ Set starts monitoring
```

If frozen conditions remain valid:

```text
Set sends nothing
```

If they become invalid:

```text
Set
→ Order Cancel Signal
→ Order Lifecycle
```

---

## Variant 2 — ENTRY_LIFECYCLE_EVENT

Used only to stop or update the pending-entry monitor when the entry phase changes materially or becomes terminal.

```yaml
entry_lifecycle_event:
  contract_version: 3
  event_id: string
  lifecycle_revision: nonnegative-integer
  decision_cycle_id: string
  set_result_id: string
  tranche_id: string
  symbol: string
  event_type: FULL_FILL | CANCELLED_ZERO_FILL | ENTRY_REMAINDER_CANCELLED | SUBMISSION_FAILED_AFTER_PLACEMENT_RECONCILIATION
  occurred_at: RFC3339-timestamp
```

Baseline event types:

```text
FULL_FILL
CANCELLED_ZERO_FILL
ENTRY_REMAINDER_CANCELLED
SUBMISSION_FAILED_AFTER_PLACEMENT_RECONCILIATION
```

Set uses these events only to synchronize monitor state.

They do not trigger a new market analysis or Position Rules calculation.

## Idempotency

Both message variants are idempotent by:

```text
event_id
```

Duplicate delivery must not start, stop, or mutate monitoring twice.

## Invariants

- No `ORDER_PLACED` before exchange acceptance.
- No `ORDER_PLACED` for an ambiguous submit.
- Both variants travel over the same Order Lifecycle → Set boundary.
- No additional architecture arrow is introduced.
- Set market logic remains Set-owned.


## Monotonic terminal dominance

Set applies messages per `decision_cycle_id` by `lifecycle_revision`, not arrival order. Any terminal entry event creates a durable tombstone. A later delayed ORDER_PLACED with an older/equal revision cannot activate or reactivate that cycle. Terminal state is replay-safe across restart.

## Shared schema and replay boundary


The YAML is a generated shape illustration; `nullable: TYPE` denotes a nullable value, not a literal object. Strict types, requiredness, unknown-field rejection and variants are defined in [`wire.schema.json`](../schemas/wire.schema.json), with shared producer/consumer bindings in [`CONTRACT_REGISTRY.json`](../schemas/CONTRACT_REGISTRY.json). Decimal values are exact strings. All invariants below are mandatory in addition to schema validation.

Exact identifier ownership is specified in `../IDENTIFIER_LINEAGE.md`. This contract does not create grant/plan identities before their owners do. Entry-terminal tombstones dominate late placement and survive restart.

## Timestamp clarification (contract v3)

P10 separates current live-order proof from proof of the original acceptance instant. order_placed_at is the once-persisted placement-notification timestamp after native live existence is proven; replay preserves it. It is not a substitute for entry_accepted_at and never determines Portfolio cooldown. Set continues matching the same decision_cycle_id/set_result_id to its stored Frozen Condition. Terminal entry-lifecycle synchronization remains on this same boundary; no new Set logic or API edge is introduced.
