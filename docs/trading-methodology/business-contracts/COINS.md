# TriggerTrade — Coins Contract

**Flow:** `Portfolio Rules → Set`  
**Contract version:** `2`  

## Purpose

Carries the current Portfolio Rules request-state for each symbol and tells Set whether new-opportunity analysis for that symbol is active.

## Payload

```yaml
coins:
  contract_version: 2
  event_id: string
  occurred_at: RFC3339-timestamp
  symbols:
  - symbol: string
    scope_revision: nonnegative-integer
    action: OPEN | CLOSE
```

## Semantics

`OPEN / CLOSE` is the state of the Portfolio Rules request for that symbol.

Example:

```text
SOL OPEN
→ Portfolio Rules currently wants Set to search for new SOL opportunities
→ Set keeps SOL in active analysis scope

SOL CLOSE
→ Portfolio Rules no longer wants new SOL opportunities
→ Set removes SOL from new-opportunity analysis scope
```

Canonical:

```text
OPEN
= keep this symbol active for new-position search

CLOSE
= stop searching for new positions for this symbol
```

This contract controls **new-opportunity analysis scope**.

It does not itself cancel an already-placed exchange order.

If a previously created `decision_cycle_id` already has an accepted pending order, its frozen-condition monitoring is lifecycle-driven and remains tied to that existing order until the entry lifecycle becomes terminal.

## Ownership

Portfolio Rules owns whether a symbol needs analysis.

Set owns how and when market analysis is performed.

## Invariants

- No direction is carried.
- No market analysis is carried.
- No `decision_cycle_id` is required.
- `CLOSE` never cancels an existing order.


## Ordering and delta semantics

Each symbol action is a delta update with a Portfolio-owned monotonic `scope_revision`. Set applies only a revision newer than the last applied revision for that symbol. Omitted symbols are unchanged. A delayed older OPEN cannot overwrite a newer CLOSE. For unfinished Set formation, every effective newer OPEN revision establishes a fresh formation epoch and invalidates unfinished state from every older OPEN epoch; an effective CLOSE terminates/resets unfinished formation. Thus OPEN rev12 received before delayed CLOSE rev11 still starts epoch 12 and prevents any rev10 partial formation from reviving. These scope changes do not alter any already-created `decision_cycle_id`, accepted/placed order or existing pending-order monitor.

Set's owner-local Trigger results, transition events, consumption claims and freshness/window anchors belong to that same formation epoch (`methodology/SET.md`, Part I §§10 and 17). A new epoch inherits none of the old pre-MATCH Trigger state. In a new epoch a first authoritative TRUE can satisfy CURRENT_STATE but cannot create FRESH_EVENT without an authoritative FALSE -> TRUE transition in that epoch. No wire field or version is added.

## Shared schema and replay boundary


The YAML is a generated shape illustration; `nullable: TYPE` denotes a nullable value, not a literal object. Strict types, requiredness, unknown-field rejection and variants are defined in [`wire.schema.json`](../schemas/wire.schema.json), with shared producer/consumer bindings in [`CONTRACT_REGISTRY.json`](../schemas/CONTRACT_REGISTRY.json). Decimal values are exact strings. All invariants below are mandatory in addition to schema validation.

Exact identifier ownership is specified in `../IDENTIFIER_LINEAGE.md`. This contract does not create grant/plan identities before their owners do. Entry-terminal tombstones dominate late placement and survive restart.
