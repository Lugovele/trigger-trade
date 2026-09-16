# TriggerTrade — Order Cancel Signal Contract

**Flow:** `Set → Order Lifecycle`  
**Contract version:** `2`  

## Purpose

Communicates either TRUE frozen-condition invalidation (`cause = INVALIDATION`)
or the certified F-013 fail-closed request (`cause = MONITORING_UNAVAILABLE`)
for the exact original accepted pending LIMIT entry. Both causes use only the
existing Set → Order Lifecycle boundary and family/version 2. The unavailable
request is reconciled before any cancel-required execution step; only a proven
active unfilled remainder may be cancelled. Neither cause closes filled
exposure, releases Portfolio capital or changes the certified reducer.

## Payload

The wrapper is `order_cancel_signal`. `cause` is mandatory; omission has no
legacy/default interpretation. The two strict variants are:

### INVALIDATION

```yaml
order_cancel_signal:
  contract_version: 2
  cause: INVALIDATION
  signal_id: string
  decision_cycle_id: string
  set_result_id: string
  tranche_id: string
  symbol: string
  invalidated_at: RFC3339-timestamp
  reason_code: string
  condition_record_id: string
  condition_id: string
  evidence_digest: string
```

### MONITORING_UNAVAILABLE

```yaml
order_cancel_signal:
  contract_version: 2
  cause: MONITORING_UNAVAILABLE
  signal_id: string
  decision_cycle_id: string
  set_result_id: string
  tranche_id: string
  symbol: string
  unavailable_requirement_id: string
  unavailable_at: RFC3339-timestamp
  unavailable_reason_code: ACTIVATION_IDENTITY_INVALID | FROZEN_RECORD_INVALID_OR_UNRESOLVED | INVALID_CONDITION | REQUIRED_EVIDENCE_UNAVAILABLE
```

All shown fields are required for their respective cause. Identifiers and
reason strings are nonempty; timestamps are RFC3339 date-times. In
MONITORING_UNAVAILABLE only, `condition_record_id` is optional and must be
omitted unless its exact immutable matched-cycle identity is independently
known and correctly bound. It is never null or guessed; a known record ID does
not assert that its contents are valid or that any condition is TRUE.
`condition_id`, `evidence_digest`, `invalidated_at` and `reason_code` are
forbidden in this variant. The three `unavailable_*` fields are forbidden in
INVALIDATION. No nullable placeholder or implicit/default cause is permitted.
For MONITORING_UNAVAILABLE, `signal_id == unavailable_requirement_id` is a
mandatory semantic invariant; the two fields name the same logical identity.

The existing inner schema validates common field types and uses `oneOf` with
cause constants and variant required/forbidden fields. Both the inner object
and wrapper retain `additionalProperties: false`. Only the unavailable variant
permits omission of `condition_record_id`. No field meanings are overloaded.

## Semantics

### Common authority and exact targeting

Set owns the validity evaluation and the unavailable requirement. Order
Lifecycle owns entry state, reconciliation, cancel execution and terminal
confirmation; it does not redo market, Trigger or direction analysis. Schema
validation is necessary, not sufficient: exact identity/content, provenance,
timestamp ownership and semantic binding checks below are mandatory.

Every message binds the exact `decision_cycle_id`, `set_result_id`, `tranche_id`
and symbol to the original accepted LIMIT entry via the already persisted
Order Placed/client/native entry lineage. Lifecycle must validate the same
binding, including its account/environment scope. The accepted entry identity
is recovered only by that exact retained relationship, never by the latest
Set result, symbol alone, timestamp proximity, nearest pending order or current
market state. A conflicting/missing routing binding is an integrity/
reconciliation condition, not permission to cancel a different order.

### INVALIDATION: existing factual semantics

A frozen hard condition has evaluated TRUE. `condition_record_id` is the exact
frozen record, `condition_id` its exact TRUE predicate and `evidence_digest` the
actual selected factual evidence. `invalidated_at` is the authoritative
evidence-effective time that made the predicate TRUE, never local evaluation,
delivery or retry time. `reason_code` retains the existing invalidation reason.

The signal's identity/content remains bound to that frozen
condition/evidence/active remainder. Identical evaluation, delivery or restart
returns the same logical signal/original `signal_id`. Lifecycle verifies
identity and authoritative remainder state and cancels only a still-live
unfilled remainder; a terminal race is an idempotent no-op. The explicit cause
is the only discriminator added to this already-defined route.

### MONITORING_UNAVAILABLE: truthful requirement fields

`unavailable_requirement_id` identifies one Set-owned sticky fail-closed
requirement for the original accepted entry. `signal_id` equals that same ID;
it is not a separately minted delivery or retry identity.

`unavailable_at` is the effective timestamp captured once on the first durable
Set MONITORING_UNAVAILABLE state transition establishing this requirement.
Persist that transition and its timestamp before publication. This is an
owner-local state event's authoritative time, not an invented timestamp for
missing market evidence, a TRUE invalidation time, or the later receipt/
reconciliation/retry time. When exact target linkage is deferred, preserve the
original transition time on eventual binding; never backdate or refresh it
from newly recovered market data.

`unavailable_reason_code` records the first establishment's failure class. Apply
the following reporting precedence only after the unchanged F-013 reducer has
returned UNAVAILABLE; it cannot override a known TRUE invalidator or an
authoritative terminal remainder:

| Order | Code | Truthful class |
|---|---|---|
| 1 | ACTIVATION_IDENTITY_INVALID | Activation identity is invalid, conflicting, ambiguous or unresolved. Independently proven routing to the original accepted entry is still mandatory before publication. |
| 2 | FROZEN_RECORD_INVALID_OR_UNRESOLVED | Frozen record is missing, invalid, unresolved, unsupported or has no valid nonempty condition list. |
| 3 | INVALID_CONDITION | A required frozen condition is malformed/unsupported or otherwise evaluates INVALID_CONDITION. |
| 4 | REQUIRED_EVIDENCE_UNAVAILABLE | Required condition evaluation is UNAVAILABLE because its selected factual evidence/coverage is missing, stale, invalid or otherwise unusable. |

For simultaneous failures retain every independently known cause locally in
this order; the first applicable row is the immutable wire reason. Subsequent
failure classes are diagnostics, not a new requirement or a change of reason.
No condition is relabeled TRUE. An optional `condition_record_id` is permitted
only from an independently trusted immutable matched-cycle binding. Its
absence, or exact supplied value, is part of the original message content and
cannot be enriched on a replay. A known ID does not validate missing record
contents. All TRUE-only fields remain forbidden.

### Requirement identity and atomic persistence

The logical uniqueness key is:

```text
(F013_MONITORING_UNAVAILABLE,
 decision_cycle_id, set_result_id, tranche_id,
 original accepted entry client_order_link_id)
```

This key is inside the entry's existing account/environment identity domain.
Persist its exact client/native entry pair and original placement binding
locally; no new native identifier or wire targeting field is invented. A
partial fill or a newer remainder-state revision is still the same entry, not
a new key. Changes in evidence, individual failed conditions, primary reason
diagnostics, delivery attempts or restored market health do not rekey it.
All unavailable observations for that entry join its already-sticky
requirement until authoritative terminal proof. Thus the same unavailable
condition/cycle/active remainder always yields the same logical requirement.

Set atomically acquires-or-joins one committed identity for this key. A first
commit persists the transition reference/effective time, initial reason and
locally known failure evidence, exact lineage, optional-record presence/value,
immutable message content and pending outbox record together. Publication can
occur only after commit. A concurrent duplicate or replay returns the winning
committed identity and content, not its own pre-commit candidate. IDs remain
opaque under IDENTIFIER_LINEAGE; the unique durable key-to-ID mapping, not a
choice of UUID/ULID spelling, supplies semantic determinism. A crash before
commit publishes nothing; after commit, retries use the exact stored message.

If the frozen record/activation is bad but the actual placement and complete
routing lineage are independently authoritative, the unavailable request is
still representable; omit an untrusted record ID and all TRUE-only fields.
If the target itself is ambiguous or unresolved, retain MONITORING_UNAVAILABLE
and its original timestamp/reason plus the integrity/reconciliation condition
under the existing exact initiating source/event identity. No addressed
message or native cancel is permitted until authoritative lineage uniquely
links that same incident to the original accepted entry. This is deferred
binding, not inference from a later opportunity. At resolution, acquire-or-join
the same entry-scoped requirement and retain its first durable establishment;
if several already-recorded incidents resolve together, use their persisted
Set transition order, never reconciliation-arrival order. If a requirement
already exists, join it without rewriting its earlier committed content.
Terminal proof instead ends applicability. Missing recovery state never
licenses a fresh requirement in place of a possibly committed one.

### Reconcile-first receipt and execution

Set first records MONITORING_UNAVAILABLE. A current authoritative terminal
tombstone means STOPPED and no new outbound request. Otherwise the unavailable
variant is the existing-boundary request for fail-closed reconciliation. Its
publication/durable receipt is **not** the INVALID route's market-cancel signal
and is not an assertion of current remaining quantity. No native cancellation
is authorized before Lifecycle reconciles authoritative entry state.

Lifecycle validates schema, exact lineage, `signal_id ==
unavailable_requirement_id`, and previously received identity/content. It
durably records receipt/deduplication before a side effect and reconciles the
original accepted entry. The ordered results are:

1. Authoritative terminal/no-unfilled-remainder proof: mark the request no
   longer applicable, retain its terminal revision/tombstone and deduplication
   identity, and emit no market/native cancellation. Never close filled
   exposure. An already transmitted request may reach this branch after a race.
2. Required identity or remainder proof still unresolved: retain the request
   and integrity/reconciliation condition; do not infer a target, treat missing
   quantity as zero, or issue a blind cancel. Continue existing Lifecycle
   reconciliation without dropping the obligation.
3. Exact accepted entry has a proven active unfilled remainder: preserve/admit
   its sticky cancel-required intention and execute only against that
   remainder through existing Lifecycle cancel/retry handling. Recheck current
   authoritative state before the side effect; fill/cancel races return to the
   existing reconciliation and terminal rules.

These are receipt/execution states, not new F-013 reducer outcomes or new wire
modes. The conditional request supplies the already-certified request-for-
fail-closed-handling step; only after positive pending proof does it become an
executable cancel intention. No second message is required. Both causes join
the existing entry cancel intent rather than create duplicate logical order
management or filled-exposure authority. Lifecycle returns terminal state on
the unchanged Order Placed/entry-lifecycle-event boundary, with the existing
monotonic `lifecycle_revision` and terminal dominance.

### Sticky recovery, delivery and terminal dominance

Set restores MONITORING_UNAVAILABLE/its outstanding requirement, semantic key,
immutable payload, original timestamp/reason, exact activation/entry lineage,
source transition and all outbox publication/delivery progress. Lifecycle
restores its accepted payload, receipt/deduplication record, reconciliation/
cancel progress and current authoritative remainder revision/tombstone. A lost
acknowledgement permits identical replay, not a new requirement. Delivery or
cancel-request acknowledgement alone is not terminal proof.

Same identity plus identical content is idempotent; changed content under the
same ID, a different ID claiming the same existing requirement key, or missing/
conflicting recovered bindings is an integrity/reconciliation condition, not a
last-writer update or automatic retargeting. Compare optional-field omission
as part of content. Concrete transport acknowledgement mechanics remain an
implementation detail; they do not change these persistence obligations.

Market recovery cannot clear, replace, reclassify or remint an established
requirement. A current VALID/NO_MESSAGE evaluation does not revoke earlier
sticky cancellation or its delivery retries. A separately proven INVALIDATION
keeps its own cause/evidence; it cannot rewrite the unavailable message.
Authoritative terminal proof ends applicability but retains the identity and
receipt/terminal tombstone. Replayed or delayed placement, condition or cancel
messages cannot resurrect that requirement or attach it to a newer entry.
There is no age expiry, TTL, newer-opportunity invalidator, KEEP, reprice,
chase, filled-exposure close or Portfolio-release authority. Canonical S-004
finality and all existing business/API owners and edges remain unchanged.

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
