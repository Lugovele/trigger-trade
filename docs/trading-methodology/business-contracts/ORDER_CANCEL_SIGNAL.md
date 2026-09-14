# TriggerTrade — Order Cancel Signal Contract

**Flow:** `Set → Order Lifecycle`  
**Contract version:** `2`  

## Purpose

Tells Order Lifecycle that the frozen market-validity condition for a still-pending entry has become invalid.

## Payload

```yaml
order_cancel_signal:
  contract_version: 2
  signal_id: string
  decision_cycle_id: string
  set_result_id: string
  tranche_id: string
  symbol: string
  invalidated_at: RFC3339-timestamp
  reason_code: string
```

## Semantics

Set decides market invalidity.

Order Lifecycle performs the exchange cancellation.

```text
Set detects frozen-condition invalidation
→ Order Cancel Signal
→ Order Lifecycle cancels still-live entry/remainder
```

## Partial fill

If part of the order is already filled:

```text
filled quantity remains real exposure
only unfilled entry remainder is cancelled
```

After confirmed cancellation:

```text
Order Lifecycle
→ Order Event
→ Portfolio Rules
```

## Invariants

- Set never directly calls exchange cancel.
- Order Lifecycle does not re-evaluate the market reason.
- Signal never closes already-filled exposure.
- No KEEP signal exists.
- No reprice/chase is permitted.


Retries retain the original `signal_id`. Lifecycle verifies authoritative remaining entry quantity before cancellation; if none remains the signal is an idempotent no-op and never closes filled exposure.

## Shared schema and replay boundary


The YAML is a generated shape illustration; `nullable: TYPE` denotes a nullable value, not a literal object. Strict types, requiredness, unknown-field rejection and variants are defined in [`wire.schema.json`](../schemas/wire.schema.json), with shared producer/consumer bindings in [`CONTRACT_REGISTRY.json`](../schemas/CONTRACT_REGISTRY.json). Decimal values are exact strings. All invariants below are mandatory in addition to schema validation.

Exact identifier ownership is specified in `../IDENTIFIER_LINEAGE.md`. This contract does not create grant/plan identities before their owners do. Entry-terminal tombstones dominate late placement and survive restart.
