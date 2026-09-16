# TriggerTrade — Order Lifecycle Methodology

**File:** `ORDER_LIFECYCLE.md`  
**Version:** 1.2.15
**Architecture role:** `Order Lifecycle — Order Management`


**Shared normative protocols:** `../SYSTEM_PROTOCOLS.md` (P1–P17). **ID ownership:** `../IDENTIFIER_LINEAGE.md`. Generated wire-shape illustrations use the strict schema registry in `../schemas/`; nullable annotations are not literal payload objects.

## Purpose

This is the single canonical methodology document for the TriggerTrade **Order Lifecycle** block.

Order Lifecycle owns the execution lifecycle after Position Rules has produced an approved `Order Spec`.

Canonical external flows:

```text
Position Rules → Order Lifecycle
Order Spec

Portfolio Rules → Order Lifecycle
Submit Authorized

Order Lifecycle → Portfolio Rules
Order Event

Order Lifecycle → Set
Order Placed

Set → Order Lifecycle
Order Cancel Signal

Order Lifecycle ↔ API
Order Management
```

Order Lifecycle owns:
- technical order serialization and submission;
- exchange submission;
- exchange acknowledgement;
- pending order state;
- partial and full fills;
- cancellation execution;
- TP / SL lifecycle;
- Manual Close execution;
- reconciliation and restart recovery;
- logical tranche execution ledger;
- execution event normalization.

Order Lifecycle does **not**:
- perform market analysis;
- determine direction;
- calculate Entry / SL / TP;
- change Entry / SL / TP;
- choose leverage;
- choose capital allocation;
- approve or reject the trade economically;
- decide whether a coin should be analyzed;
- decide whether a pending order is still market-valid.

---

# 1. Canonical ownership boundaries

## 1.1 Position Rules boundary

Position Rules owns the approved trade intent and supplies:

```text
decision_cycle_id
set_result_id
position_plan_id
tranche_id
symbol
direction
entry side
LIMIT price
quantity
leverage
TP
SL
planned economics
```

Order Lifecycle may serialize these into exchange API format.

It may not:
- reverse direction;
- move Entry;
- move TP;
- move SL;
- change leverage;
- resize quantity for economic reasons;
- substitute MARKET for the approved LIMIT entry;
- repair failed economics.

If the prepared order cannot be submitted exactly under the approved intent:

```text
do not submit
```

No chase and no automatic reprice exist in the baseline.

## 1.2 Portfolio Rules boundary

Portfolio Rules owns:
- own-capital accounting;
- `capital_grant_id`;
- `SUBMISSION_HOLD`;
- reservation / filled / free capital;
- tranche-slot accounting;
- cooldown;
- portfolio state and limits.

Order Lifecycle does not book or release portfolio capital directly.

Instead, it emits:

```text
Order Event
```

and Portfolio Rules performs its own API-backed reconciliation/accounting.

## 1.3 Set boundary

Set owns pending-order **market validity**.

Order Lifecycle does not inspect:
- market regime;
- direction changes;
- trigger state;
- market structure;
- invalidation predicates.

When Set determines that a still-pending entry is no longer valid:

```text
Set → Order Lifecycle
Order Cancel Signal
```

Order Lifecycle executes the cancellation.

## 1.4 API boundary

Order Lifecycle owns:

```text
Order Lifecycle ↔ API
Order Management
```

This includes exchange-facing:
- create order;
- cancel order;
- open-order lookup;
- order history;
- execution history;
- position state needed for execution reconciliation;
- TP/SL order state;
- reduce-only close operations;
- complete financial/cashflow evidence and coverage via GET_FINANCIAL_FACTS;
- current hard non-market execution facts via GET_HARD_EXECUTION_FACTS.

API is a factual/execution interface, not a decision owner.

---

# 2. Core lifecycle identity

Every lifecycle instance belongs to one logical TriggerTrade tranche.

Canonical lineage:

```text
authorization_id
capital_grant_id
decision_cycle_id
set_result_id
position_decision_id
construction_result_id
position_plan_id
tranche_id
order_spec_id
symbol
```

Exchange-facing identity adds:

```text
client_order_link_id
exchange_order_id
execution_id / execId
```

Rules:

1. `decision_cycle_id` and `set_result_id` come from Set through Position Rules. Unknown native observations are independent records, not lifecycle instances fabricated without these IDs; P9 defines their scope/revisions.
2. `capital_grant_id` comes from Portfolio Rules and remains bound to the immutable approved plan.
3. Position finalizes position_plan_id, tranche_id and order_spec_id only after the post-APPROVE Capital and Limits; position_decision_id identifies the earlier opportunity and construction_result_id the final construction.
4. `authorization_id` comes from Portfolio Rules atomically with successful SUBMISSION_HOLD.
5. `client_order_link_id` is created only by Order Lifecycle and persisted before the first exchange create request.
6. `exchange_order_id` is created by the exchange and remains absent/null until known.
7. None of these IDs may be silently substituted by symbol/time matching.

---

# 3. Order Lifecycle start condition

Order Lifecycle does not start exchange submission merely because an `Order Spec` exists.

It requires **two independent inputs for the same logical tranche**:

```text
Position Rules → Order Lifecycle
Order Spec

Portfolio Rules → Order Lifecycle
Submit Authorized
```

The execution gate is:

```text
matching Order Spec
AND
matching Submit Authorized
→ submit path may start
```

The two inputs must correlate at minimum by:

```text
capital_grant_id
decision_cycle_id
position_plan_id
tranche_id
order_spec_id
symbol
```

`Submit Authorized` means:

```text
Portfolio Rules successfully booked SUBMISSION_HOLD
for the capital grant associated with this approved trade
```

Canonical minimum payload:

```yaml
submit_authorized:
  contract_version: 5
  authorization_id: string
  capital_grant_id: string
  decision_cycle_id: string
  set_result_id: string
  position_decision_id: string
  construction_result_id: string
  position_plan_id: string
  tranche_id: string
  order_spec_id: string
  symbol: string
  order_spec_digest: string
  held_committed_capital: decimal-string
  authorized_at: RFC3339-timestamp
  numeric_policy_version: TT_NUMERIC_V1
  order_spec_contract_version: 5
```

Order Lifecycle may receive these two inputs in either arrival order.

Therefore it must support:

```text
Order Spec first → wait for authorization
Submit Authorized first → wait for Order Spec
```

Only after both exist and identity matches does the tranche become:

```text
READY_TO_SUBMIT
```

If identities do not match:

```text
IDENTITY_MISMATCH
→ do not submit
```

If Portfolio Rules never authorizes because the hold fails:

```text
no Submit Authorized
→ no exchange submission
```

This is the explicit communication step between capital reservation and order execution.

---

# 4. Technical submission boundary

After matching `Order Spec + Submit Authorized`, Order Lifecycle prepares the exact approved order for exchange submission.

The baseline entry is:

```text
LIMIT
POST_ONLY
```

Order Lifecycle may perform only technical serialization/validation required to form a valid exchange request, such as:
- required API fields;
- symbol/instrument identifiers;
- current venue metadata needed for serialization;
- valid quantity/price formatting;
- supported leverage/order mode;
- API request construction.

It must not:
- recalculate Entry;
- compare Entry to current best bid/ask as a local business gate;
- move Entry;
- cross the spread intentionally;
- switch to MARKET;
- chase price;
- rerun trade economics;
- rerun market analysis.

`POST_ONLY` is an exchange order instruction.

Canonical behavior:

```text
submit exact approved LIMIT + POST_ONLY
→ exchange decides whether to accept/reject under venue rules
```

If the order is accepted and then fills milliseconds later, that is completely valid.

TriggerTrade does not impose any minimum resting time in the book.

Therefore:

```text
accepted → lifecycle continues normally
rejected → exchange rejection lifecycle event
```

No separate local `POST_ONLY_NOT_SUBMITTABLE` gate exists in the canonical baseline.

---

P2 additionally requires current hard execution fact comparison through Order Management.GET_HARD_EXECUTION_FACTS. New compatible revisions do not invalidate the grant/spec; incompatible exact values fail technically without repair. Required unavailable facts retain reconciliation/hold. This is not a marketability check.

# 4A. Supported native operating profile

Baseline adapter profile:

```text
product = Bybit linear USDT perpetual
position_mode = HEDGE_MODE
margin_mode = ISOLATED
native side identity = symbol + positionIdx/native side
```

Multiple logical tranches may share one native same-symbol/same-side position. A new tranche is technically submit-compatible only if its approved leverage is compatible with the leverage already configured for that native side. Order Lifecycle may reject an incompatible new create before exposure, but may not silently change approved leverage or existing exposure. Opposite-direction logical tranches use the opposite hedge side.

---

# 5. Entry submission

Canonical baseline:

```text
order_type = LIMIT
post_only = true
```

Submission request must carry a deterministic `client_order_link_id`.

The client order ID should be derivable from or durably mapped to:

```text
decision_cycle_id
+
tranche_id
```

so uncertain submission can be reconciled without blind duplicate creation.

Order Lifecycle persists:

```text
SUBMITTING
submitted_at
client_order_link_id
```

before or atomically with sending the external request.

---

# 6. Submission acknowledgement

Possible normalized results:

```text
ACCEPTED
REJECTED
AMBIGUOUS
```

## 6.1 ACCEPTED

Acceptance means the exchange confirms that the LIMIT entry order exists.

On acceptance:

```text
state = PENDING_ENTRY
exchange_order_id = known
entry_accepted_at = original exchange acceptance time if PROVEN, else null
entry_acceptance_status = PROVEN | UNAVAILABLE
entry_acceptance_provenance = source evidence if PROVEN, else null
```

Order Lifecycle must emit two canonical outputs.

To Portfolio Rules:

```text
Order Event = ORDER_ACCEPTED
```

To Set:

```text
Order Placed
```

`Order Placed` is sent **only after actual exchange acceptance/placement**.

Minimum `Order Placed` identity:

```text
decision_cycle_id
set_result_id
position_plan_id
tranche_id
symbol
client_order_link_id
exchange_order_id
order_placed_at
```

This activates Set's pending-order invalidation monitoring.

## 6.2 REJECTED

Definitive exchange rejection:

```text
state = SUBMISSION_FAILED
```

Emit:

```text
Order Event = SUBMISSION_REJECTED
```

Portfolio Rules releases the corresponding local hold after its own reconciliation.

No cooldown starts.

No blind retry.

## 6.3 AMBIGUOUS

Examples:
- request timeout after send;
- connection loss after send but before acknowledgement;
- client receives no definitive response.

Canonical rule:

```text
do not retry create blindly
```

Instead:

```text
state = SUBMISSION_UNCERTAIN
→ reconcile by client_order_link_id
→ inspect open orders / history / executions
```

Resolution:

```text
order exists
→ normalize to ACCEPTED / PENDING_ENTRY / filled state

order definitely does not exist
→ SUBMISSION_FAILED

cannot establish truth
→ remain RECONCILING
→ no new lifecycle action that could duplicate exposure
```

---

# 7. Canonical lifecycle states

Baseline internal states:

```text
READY_TO_SUBMIT
SUBMITTING
SUBMISSION_UNCERTAIN
PENDING_ENTRY
PARTIALLY_FILLED
OPEN
CANCEL_PENDING
CANCELLED_ZERO_FILL
CLOSE_PENDING
CLOSED
SUBMISSION_FAILED
RECONCILING
MANUAL_INTERVENTION_REQUIRED
```

State meanings:

### READY_TO_SUBMIT
Matching Order Spec and Submit Authorized exist and pass identity checks.

### SUBMITTING
Create-order request is in flight.

### SUBMISSION_UNCERTAIN
External create outcome is unknown.

### PENDING_ENTRY
Accepted entry order with zero fill.

### PARTIALLY_FILLED
Some entry quantity filled and unfilled remainder remains live.

### OPEN
No live entry remainder remains and filled exposure exists.

### CANCEL_PENDING
Cancel request sent for still-live entry remainder; terminal outcome not yet known.

### CANCELLED_ZERO_FILL
Entry terminated with zero fill.

### CLOSE_PENDING

A close intent exists, or operational/financial completion remains unresolved. Exposure may already be zero. This is not terminal and retains full commitment/slot under P6.

### CLOSED

All six P6 predicates must be authoritatively established:

```text
logical exposure = 0
entry remainder terminal
all tranche-owned protective/exit children terminal or authoritatively disabled
active close intent fully resolved
financial finality established
no unresolved competing execution authority
```

The FINAL result, resolved intent, CLOSED state and event outbox commit atomically. Until then use CLOSE_PENDING or RECONCILING, never a weaker CLOSED interpretation. Operational cleanup closed_at is a marker distinct from state=CLOSED; P8 defines all timestamps. Portfolio explicitly retains capital even at zero exposure.

---

### SUBMISSION_FAILED
Entry was definitively not created/accepted.

### RECONCILING
Local truth and exchange truth are being reconciled.

### MANUAL_INTERVENTION_REQUIRED
Automated reconciliation cannot safely establish or restore the lifecycle.

---

# 8. Pending LIMIT entry

While an accepted LIMIT entry remains pending:

```text
Order Lifecycle does not reprice it
Order Lifecycle does not chase
Order Lifecycle does not change direction
Order Lifecycle does not rerun Set
```

Baseline has:

```text
no automatic TTL cancellation
```

An old pending order may end through:
- fill;
- Set `Order Cancel Signal`;
- user Manual Cancel;
- exchange rejection/expiry external to TriggerTrade rules;
- operational reconciliation finding a terminal exchange state.

No arbitrary time-based cancellation is inferred.

---

# 9. Partial fill

Let:

```text
intended_qty = Q
cumulative_filled_qty = F
remaining_qty = Q - F
```

If:

```text
0 < F < Q
```

and no close intent is active, then:

```text
state = PARTIALLY_FILLED
```

Order Lifecycle must persist:
- each execution;
- cumulative filled quantity;
- average fill price;
- remaining entry quantity;
- realized entry fees;
- attached protection state.

Emit:

```text
Order Event = PARTIAL_FILL
```

Before close acquisition, Portfolio Rules separately reconciles filled actual committed capital and remaining reserved capital. During an active close intent, this execution is instead serialized into that intent's confirmed target/residual calculation and the complete closing commitment remains in closing_retained_committed_capital. A late partial/full entry fill never replaces CLOSE_PENDING/RECONCILING with PARTIALLY_FILLED/OPEN or authorizes independent competing protection/reduction children. P5 governs child authority; P6 governs capital retention.

Order Lifecycle must never assume the whole intended quantity is filled from a partial execution.

---

# 10. Full fill

If:

```text
cumulative_filled_qty = intended_qty
```

and no entry remainder remains and no close intent is active:

```text
state = OPEN
```

Persist:

```text
full_fill_at
final_entry_qty
average_entry_price
total_entry_fee
```

Emit:

```text
Order Event = FULL_FILL
```

Set pending-entry monitoring must terminate because no active unfilled entry remainder exists.

---

# 11. Cancel inputs

Order Lifecycle may receive a request to cancel a live entry remainder from only governed sources.

## 11.1 Set invalidation / monitoring-unavailable fail-safe

```text
Set → Order Lifecycle
Order Cancel Signal (contract_version 2)
```

Common correlation is `signal_id`, `cause`, `decision_cycle_id`,
`set_result_id`, `tranche_id` and `symbol`, bound to the original accepted entry.
For INVALIDATION, require `invalidated_at`, `reason_code`,
`condition_record_id`, `condition_id` and `evidence_digest`.
For MONITORING_UNAVAILABLE, require `unavailable_requirement_id`,
`unavailable_at` and `unavailable_reason_code`; `signal_id` equals the
requirement ID. Only a truthfully known `condition_record_id` is optional in
that cause. Its TRUE-only fields are forbidden, not nullable placeholders.

Order Lifecycle does not validate the market reason. It validates exact
identity/content and reconciles current authoritative order state before
cancelling the **unfilled remainder only**. MONITORING_UNAVAILABLE is a
conditional fail-closed request until pending remainder is proven, not a TRUE
market invalidator. §38 and Order Cancel Signal Semantics govern both variants,
sticky receipt/replay and terminal no-op handling.

## 11.2 Manual Cancel

The user may cancel a pending entry manually.

Manual Cancel must identify the logical tranche or exact pending entry order.

It affects only unfilled entry quantity.

If zero filled:
- terminal result may become `CANCELLED_ZERO_FILL`.

If partially filled:
- terminal result becomes `ENTRY_REMAINDER_CANCELLED`;
- filled exposure remains real.

---

# 12. Cancel/fill race

A cancel request is not equivalent to confirmed cancellation.

Race example:

```text
cancel sent
↓
additional fill occurs before exchange cancel takes effect
```

Therefore:

```text
never release remaining reservation on cancel request alone
```

Only authoritative exchange facts determine:
- final filled quantity;
- final cancelled quantity;
- whether exposure remains.

Canonical:

```text
CANCEL_PENDING
→ reconcile final order + execution state
→ emit terminal Order Event
```

---

# 13. Cancellation semantics

## 13.1 Zero-fill cancellation

If final:

```text
filled_qty = 0
order terminal = CANCELLED
```

then:

```text
state = CANCELLED_ZERO_FILL
```

Emit:

```text
Order Event = CANCELLED_ZERO_FILL
```

Portfolio Rules then handles release of reservation/slot and baseline cooldown clearing.

## 13.2 Partial-fill remainder cancellation

If:

```text
filled_qty > 0
remaining_qty = 0 after cancel
```

then:

```text
event = ENTRY_REMAINDER_CANCELLED
```

If filled exposure remains and no close intent is active:

```text
state = OPEN
```

If a close intent is active, the entry-terminal event is ingested under the same tranche serialization and state remains CLOSE_PENDING or RECONCILING. Entry-remainder termination never independently reopens a closing tranche.

The ledger preserves:

```text
entry_terminal_reason = REMAINDER_CANCELLED
```

Emit:

```text
Order Event = ENTRY_REMAINDER_CANCELLED
```

and:

```text
Entry Lifecycle Event = ENTRY_REMAINDER_CANCELLED
→ Set stops pending-entry monitoring
```

For an ordinary entry cancellation completed before close-intent acquisition, Portfolio releases only the conclusively unfilled reserved capital. If close processing has begun, its entire still-committed amount is already represented by closing_retained_committed_capital under P6; this entry-terminal event does not release any part of that closing commitment. Release then requires canonical CLOSED. The distinction uses durable event order/intent ownership, not message arrival order.

No automatic top-up.

---

# 14. Cancellation retry policy

A cancel request must be idempotent.

If transport outcome is uncertain:

```text
do not assume cancelled
do not spam cancel blindly
```

Order Lifecycle should:
1. query/reconcile current order state;
2. if order remains live, retry the same cancel intent safely;
3. if already terminal, normalize terminal state;
4. if state cannot be established, remain `RECONCILING`.

Repeated cancel operations must never:
- release capital twice;
- generate duplicate close logic;
- corrupt cumulative filled quantity.

---

# 15. No replace / no reprice baseline

Baseline:

```text
automatic replace = disabled
automatic reprice = disabled
market chase = disabled
```

A stale or market-invalid pending entry is cancelled, not moved.

A later new opportunity requires:

```text
new Set match
→ new decision_cycle_id
→ new Position Rules initial APPROVE / REJECT
→ only after APPROVE, new Portfolio Capital and Limits
→ new Position final construction / Order Spec and CONSTRUCTED confirmation
→ new atomic Portfolio hold / Submit Authorized
→ matching-input Lifecycle submission (P1)
```

---

# 16. Attached TP / SL protection

The approved Order Spec baseline uses:
- entry = LIMIT + POST_ONLY;
- TP = MARKET when triggered;
- SL = MARKET when triggered;
- `tpsl_mode = PARTIAL` or equivalent quantity-scoped exchange semantics.

The execution objective is:

```text
every filled entry quantity must be protected
```

Order Lifecycle must verify after each partial/full fill that the exchange-side protective configuration covers the actually filled quantity as intended by the approved Order Spec.

If protection cannot be established or verified:

```text
PROTECTION_UNCONFIRMED
→ RECONCILING
```

and, if automated recovery cannot safely restore certainty:

```text
MANUAL_INTERVENTION_REQUIRED
```

Order Lifecycle may not invent new TP/SL prices.

---

# 17. Partial fill protection

For:

```text
filled_qty = F
remaining entry qty > 0
```

the filled exposure is already real.

Therefore:
- TP/SL protection applies to `F`;
- unfilled entry remainder remains pending;
- Set may still invalidate and cancel only the remainder.

If the filled exposure closes via TP/SL/Manual Close while entry remainder still exists:

```text
cancel remaining entry first / concurrently under safe exchange sequencing
```

The system must not leave a live entry remainder capable of reopening exposure after the logical tranche has closed.

---

# 18. Open logical tranche

A logical tranche is `OPEN` when:
- filled quantity exists;
- no active entry remainder remains;
- tranche has not been fully closed.

Exchange may aggregate same-symbol/same-direction exposure.

Therefore:

```text
logical tranche
!=
raw exchange position object
```

TriggerTrade must maintain its own tranche ledger.

---

# 19. Close conditions

A logical tranche may close only by:

```text
TAKE_PROFIT
STOP_LOSS
MANUAL_CLOSE
```

Order Lifecycle executes the close mechanics but does not invent another close reason.

No automatic close from:
- midnight;
- session end;
- arbitrary holding timer;
- funding event;
- Set direction change.

---

# 20. Take Profit close

TP execution first calls atomic durable acquire-or-join by tranche_id (P5), including callbacks that race another caller. Apply the unique factual execution to this tranche, cancel/reconcile entry remainder and competing children, and serialize residual authorization. Partial execution continues the same intent; no intermediate capital/slot release occurs. Only all six P6 predicates permit CLOSED and POSITION_CLOSED_TP with FINAL result. Sibling SL cleanup occurs before CLOSED, never afterward.

# 21. Stop Loss close

SL execution uses the same acquire-or-join and serialized residual protocol. TP/SL/Manual races cannot create separate residual owners. Entry fills racing cancellation belong to the same target; no child can consume another tranche's confirmed quantity. Cleanup, resolved execution authority and complete finance all precede CLOSED/POSITION_CLOSED_SL. Partial native fills are not strategic partial close.

# 22. Manual Close

Manual request identifies tranche_id and acquires/joins its unique durable intent. Cancel/reconcile the entry remainder and competing tranche-owned TP/SL/exit children before computing residual. Under serialized state, authorize at most one next exact quantity-scoped reduce-only child; ambiguous requests retain their full outstanding authority until reconciled. Never blindly issue another close after timeout or cancel another tranche's protection.

Zero exposure while child or finance evidence is unresolved remains CLOSE_PENDING/RECONCILING with full retained commitment and slot. POSITION_CLOSED_MANUAL is emitted only at the common P6 CLOSED transaction with FINAL result. Repeated requests, duplicated callbacks and restart join the same intent or return its resolved tombstone. P5's adapter-conformance gate is mandatory for actual native cross-tranche isolation; documentation examples are not exchange proof.

---

# 23. Aggregated exchange position handling

Bybit may represent multiple same-symbol/same-side TriggerTrade tranches as one aggregate exchange position.

TriggerTrade therefore maintains a logical ledger:

The following is an internal ledger inventory, not an alternative wire contract. Each collection stores all generations rather than a single assumed TP/SL pair. P5–P9 define its transaction and identity semantics.

```yaml
tranche_ledger_inventory:
  identity_fields: [decision_cycle_id, set_result_id, position_decision_id, capital_grant_id, construction_result_id, position_plan_id, tranche_id, order_spec_id, authorization_id]
  immutable_inputs: [order_spec, order_spec_digest, capital_grant_provenance, accounting_policy]
  entry: [client_order_link_id, exchange_order_id, execution_ids, cumulative_filled_qty, remaining_qty, entry_terminal]
  protection_children: [child_id, generation, kind, client_order_link_id, exchange_order_id, status, authorized_quantity, executed_quantity]
  close_children: [child_id, close_intent_id, client_order_link_id, exchange_order_id, status, authorized_quantity, executed_quantity, uncertain_dispatch]
  close_intent: [close_intent_id, intent_revision, state, cause_event_ids, confirmed_target_quantity, confirmed_residual_quantity, authorized_reduction_quantity, executed_reduction_quantity, close_commitment_quantity_basis]
  lifecycle: [state, lifecycle_revision, submitted_at, entry_accepted_at, entry_acceptance_status, entry_acceptance_provenance, close_started_at, closed_at, terminalized_at, final_closing_execution_id]
  finance: [cashflow_ids, source_aliases, component_coverage, pagination_state, source_finality, result_id, accounting_effective_at, accounting_day_id, finalized_at]
  replay: [inbox_keys, outbox_messages, native_observation_ids, attribution_resolution_ids, resolved_tombstones]
```


The raw exchange position is never sufficient as the sole logical tranche record.

---

# 24. Event idempotency

Every exchange event must be processed idempotently.

Required protections:

```text
deduplicate execution IDs
deduplicate terminal order transitions
ignore already-applied transition
preserve monotonic cumulative filled quantity
never release quantity/capital implication twice
never add fee twice
never add realized P/L twice
```

Idempotency is mandatory across:
- live WebSocket;
- REST/order-history reconciliation;
- restart recovery.

---

# 25. Event ordering

Exchange events may be:
- duplicated;
- delayed;
- delivered out of order across streams.

Order Lifecycle must use:
- stable order/execution IDs;
- exchange timestamps;
- cumulative filled quantities;
- terminal exchange states;
- reconciliation.

Do not assume:

```text
arrival order = execution order
```

A later-arriving event with lower cumulative fill must never reduce known cumulative fill.

---

# 26. Reconciliation

Reconciliation is required when:
- process starts/restarts;
- private stream reconnects;
- submission outcome is ambiguous;
- cancel outcome is ambiguous;
- local and exchange state disagree;
- protective TP/SL state is uncertain.

Canonical:

```text
local lifecycle state → RECONCILING
↓
fetch authoritative exchange facts
↓
rebuild / correct tranche ledger
↓
emit normalized Order Event(s) when state changed
↓
LIVE lifecycle only after consistency restored
```

Order Lifecycle reconciliation covers execution, child authority, native attribution and mandatory financial finality through its own Order Management boundary (P5–P9).

Portfolio Rules performs its own portfolio/account refresh after receiving Order Event.

---

# 27. Reconciliation evidence precedence

Use facts according to their semantic authority.

Baseline precedence:

```text
executions / fills
→ strongest evidence of executed quantity

terminal order history
→ authoritative order terminal state

open orders
→ current live order presence

current position
→ aggregate exposure cross-check

local state
→ correlation/history, never superior to confirmed exchange execution facts
```

When sources conflict:
- never erase a confirmed execution;
- preserve monotonic cumulative fill;
- mark lifecycle `RECONCILING`;
- resolve before creating new execution actions.

---

# 28. Restart recovery

Before any new native side effect, restore tranche/authorization/spec bindings and digests, entry/client/native IDs, unique tranche→close-intent index, intent revisions, all protection/close children and outstanding quantity authorizations, execution/cashflow inbox/aliases, financial component coverage/cursors, accounting timestamps/result IDs, native observations/resolutions and outgoing message outboxes.

Reconcile native order/execution/child state by exact IDs. Unknown submit/close outcomes retain authority and prohibit blind retry. Recover actual quantities from deduplicated executions, not local guesses. Replay complete native-resolution manifests and expected allocation events under their original IDs. Resume only the missing financial ranges; no planned estimates fill gaps. Restore the pinned governed accounting currency and all retained unsupported-currency sources/finality blocks under P7.1; COMPLETE coverage or restart cannot clear those blocks without the existing admissible evidence and integrity conditions.

Restore entry-terminal Set tombstones/publication revisions; terminal synchronization is replayed on the existing boundary and a late placement cannot reactivate a monitor. Apply P6 CLOSED only after all predicates, otherwise retain CLOSE_PENDING/RECONCILING and full logical commitment/slot. Final financial result/state/outbox is atomic; crash before commit publishes none, crash after commit republishes the same result. Portfolio's own receipt deduplication prevents duplicate money.

---

# 29. API / WebSocket outage

During execution connectivity uncertainty:

```text
new submission = blocked unless technical submit truth is known
```

Existing exchange-side TP/SL remain active independently of TriggerTrade connectivity.

For already submitted orders:
- do not invent state;
- do not blind-retry create;
- recover/reconcile after connectivity returns.

If Set has generated an `Order Cancel Signal` while cancellation cannot be sent:
- persist cancel intent;
- attempt cancellation when exchange connectivity permits;
- reconcile before assuming success.

---

# 30. Dedicated trading account / subaccount baseline

Canonical baseline assumption:

```text
the futures account/subaccount used by TriggerTrade
contains only TriggerTrade-managed trading activity
```

There is no unmanaged/manual futures exposure in the same managed account.

This allows TriggerTrade to treat exchange-reported:
- positions;
- executions;
- fees;
- funding;
- realized P&L

as belonging to TriggerTrade.

Portfolio/account facts are retrieved through API.

# 32. Funding attribution

Funding is retrieved directly by Lifecycle through Order Management.GET_FINANCIAL_FACTS with COMPLETE source identity/coverage (P7), not forwarded by Portfolio. Required funding amounts must already be in the governed accounting/settlement currency before contributing to FINAL (P7.1); other-currency facts remain retained and block finality. The common settlement/mark price below supplies the existing funding allocation basis only and cannot convert a source currency.

Because the managed futures account/subaccount is TriggerTrade-only:

```text
funding for managed symbol/side
=
TriggerTrade funding for that symbol/side
```

If multiple logical TriggerTrade tranches share the same symbol/native side, funding attribution is mandatory and deterministic. For each unique funding transaction, allocate pro-rata using one common settlement-notional basis at the funding effective time:

```text
tranche_funding
=
total_triggertrade_funding_for_symbol_side
×
(tranche_open_notional_at_funding_time
 /
 total_triggertrade_open_notional_for_symbol_side_at_funding_time)
```

Requirements:
- the source funding transaction has a stable `cashflow_id` and is posted exactly once;
- eligible tranches are those with attributable open quantity on the funded native symbol/side at the funding effective event;
- `tranche_open_notional_at_funding_time = attributable_open_quantity × common funding settlement/mark price for that event`;
- event ordering at the same exchange timestamp follows authoritative execution/cashflow sequence, or requires proof that the ambiguity is immaterial to funding eligibility/weights; materially unresolved ties enter reconciliation rather than arbitrary attribution;
- accounting allocation quantum is exactly `0.000000000000000001` settlement-currency units (decimal 18);
- the normalized signed source funding amount must be exactly representable at that quantum; otherwise financial attribution remains `RECONCILING` rather than rounding the source cashflow;
- compute each raw signed allocation with exact rational weights, then quantize its absolute magnitude **toward zero** to the allocation quantum and reapply the source sign;
- `residue = signed_source_funding_amount - sum(base_allocations)`; assign the entire signed residue to the tranche with the largest absolute unrounded allocation (tie: lowest `tranche_id` in ascending case-sensitive Unicode code-point order);
- persist `funding_allocation_algorithm_version = FUNDING_ALLOC_V1_DECIMAL18_TOWARD_ZERO_LARGEST_ABS_LEXICAL`;
- eligibility set, settlement price/basis, source transaction ID and signed allocations are persisted;
- allocated total must equal the unique signed exchange funding amount exactly after deterministic residue assignment;
- no funding transaction may be counted again from another API representation.

Funding is accounting data only.

It never triggers a close.

A-004 allocation requires complete source identity/alias/deduplication and
COMPLETE source coverage/finality, or evidenced non-applicability for empty
funding. A missing row or zero amount does not itself prove complete coverage.
Every eligible tranche and attributable quantity at the funding effective event,
the common settlement/mark basis and provenance, and positive total eligible
open notional must be deterministically known. Missing basis, unmatched nonzero
funding, unresolved eligibility/order, unsupported currency, source not exactly
representable at the funding quantum, or incomplete required evidence retains
RECONCILING/finality-blocked status; no guessing, source rounding, conversion,
omission or current-position substitution is permitted.

The exact allocation is:

For each unique source funding transaction:

```text
tranche_open_notional_at_funding_time
= attributable_open_quantity * common_funding_settlement_or_mark_price

total_triggertrade_open_notional_for_symbol_side_at_funding_time
= sum(tranche_open_notional_at_funding_time for all eligible tranches)

raw_tranche_funding
= signed_source_funding_amount
 * (tranche_open_notional_at_funding_time
    / total_triggertrade_open_notional_for_symbol_side_at_funding_time)
```

Let:

```text
q = 0.000000000000000001
F = signed_source_funding_amount
w_i = tranche_open_notional_i / total_open_notional
```

Base allocation:

```text
base_i = sign(F) * q * floor((abs(F) * w_i) / q)
```

Residue:

```text
residue = F - sum(base_i)
```

Assign the entire signed residue to the eligible tranche with the largest
absolute unrounded raw allocation. If tied, choose the lowest `tranche_id` by
lexical Unicode code-point order.

Final allocation:

```text
allocated_funding_i = base_i + residue   for the residue recipient
allocated_funding_i = base_i             for every other eligible tranche
```

Conservation requirement:

```text
sum(allocated_funding_i) = signed_source_funding_amount
```

Persist:

```text
funding_allocation_algorithm_version =
FUNDING_ALLOC_V1_DECIMAL18_TOWARD_ZERO_LARGEST_ABS_LEXICAL
```

The residue recipient is selected by greatest absolute **unrounded allocation**,
not greatest fractional remainder. Retain the entire signed residue with that
one recipient; presentation rounding cannot replace persisted allocations.
Coverage remains half-open [from, to), including the funding event and all
causally applicable records. Eligibility/weights use funding effective time,
not recorded/retrieval time, current position state or accounting-day close.
Proof that ordering is immaterial here is limited to funding eligibility and
weights: it never waives P13's independent final-execution chronology.

Persist source identity and aliases, accepted coverage/certificate identity,
funding effective time, eligible tranche IDs and attributable quantities,
settlement/mark basis and provenance, exact weights and raw/base allocations,
residue/recipient, final signed allocations and the unchanged algorithm version.
On restart restore accepted source and coverage history before new evidence.
Identical duplicate evidence is idempotent; changed content under a known
identity remains a contradiction. This only supplies A-002's existing allocated
funding component; canonical result/CLOSED and Portfolio release rules remain
unchanged.

---

# 33. Fee attribution

Fees are attributed from actual executions.

For each execution:

```text
execution fee
→ exact logical tranche via order/execution lineage
```

Exchange-reported execution fees are authoritative. Because the managed account is TriggerTrade-only, no separation from external/manual trading is required.

Do not use planned fee estimates as realized fees. Preserve each source fee/rebate's actual native amount, currency, quantum, identity and provenance. Proven execution linkage or a completed allocation does not authorize adding a different-currency fee to the accounting result; P7.1 keeps the affected component/result reconciliation-blocked without relabeling, zeroing or heuristic conversion.

---

# 34. Authoritative logical financial result

P7 is the mandatory evidence/sign/finality protocol; P8 supplies accounting-effective time and immutable day. Lifecycle requires COMPLETE entry/exit executions, actual fees/rebates, funding, supported attributable costs and deterministic attribution, all obtained through its own Order Management boundary. Missing coverage, ambiguous aliases/ordering or unknown source sign conventions remain RECONCILING. Planned fees and native aggregate P&L are never substitutes.

Before component/parent financial FINAL, enforce P7.1 and `../schemas/NUMERIC_POLICY.md` §2A: complete all mandatory financial evidence, resolve all mandatory source attribution, verify that every participating monetary component and required source amount is already denominated in the tranche's pinned governed accounting/settlement currency, retain a finality block for every unresolved required cross-currency source, and satisfy all existing finality/integrity conditions. No cross-currency valuation is supported by this baseline. `financial_result.currency` must equal that pinned unit; it cannot be selected from incoming rows or changed at recovery.

Unsupported-currency evidence remains durably retained in native units, with provenance/identity/coverage and existing attribution/conservation. Do not omit it, zero it, classify it as non-applicable solely because it is unsupported, add currencies directly, infer FX or use current market/execution price as conversion. Source coverage may remain factually COMPLETE while the logical component/result remains RECONCILING. The full closing-retained capital and slot remain blocked by the unchanged financial-finality predicate inside P6's six-condition CLOSED rule, even after exposure becomes zero. Contrary post-FINAL evidence follows existing integrity/receipt-fence handling and never rewrites frozen results.

```text
net_realized_result = gross_realized_trading_result
                    - actual_fees_rebates
                    + allocated_funding
                    - other_supported_exchange_costs
```

actual_fees_rebates and other costs are cost-effect totals; negative rebate/refund increases net result. Normalized API signed_amount is wallet-effect and converts per component under P7. Gross result is computed by logical execution lineage without double-adding a realized-P&L cashflow view.

Persist exactly one result_id per tranche and the complete source set/coverage, final_closing_execution_id, accounting_effective_at/day/policy, closed_at, finalized_at and terminalized_at. Atomic P6 CLOSED also resolves the close intent and creates the FINAL Order Event outbox. No provisional result exists. Replay keeps the same result_id/values. Portfolio records delivered_at and posts once to the immutable economic day; delivery never moves it to today or adds wallet P&L again.

---

# 35. Universal lifecycle event propagation

Every material Order Lifecycle state change is an event.

Canonical rule:

```text
Order Lifecycle event
→ Order Event
→ Portfolio Rules
→ Portfolio Data Request
→ API
→ Portfolio Rules refreshes factual state
```

This applies to:
- order accepted;
- order rejected;
- submission failed;
- partial fill;
- full fill;
- zero-fill cancel;
- partial-fill remainder cancel;
- TP close;
- SL close;
- Manual Close;
- execution reconciliation;
- any other capacity/P&L-relevant terminal lifecycle fact.

Order Lifecycle does not directly mutate Portfolio capital accounting.

Portfolio Rules receives the event, queries API, and updates the authoritative portfolio state.

---

# 36. Order Event contract to Portfolio Rules

Every capacity/P&L-relevant lifecycle transition emits:

```text
Order Lifecycle → Portfolio Rules
Order Event
```

Canonical examples:

```text
ORDER_ACCEPTED
SUBMISSION_REJECTED
SUBMISSION_FAILED
PARTIAL_FILL
FULL_FILL
CANCELLED_ZERO_FILL
ENTRY_REMAINDER_CANCELLED
POSITION_CLOSED_TP
POSITION_CLOSED_SL
POSITION_CLOSED_MANUAL
EXECUTION_RECONCILED
```

The canonical wire contract is `business-contracts/ORDER_EVENT.md`, contract version 7, with six strict variants:

```text
LOGICAL_TRANCHE
NATIVE_UNATTRIBUTED_REDUCTION
NATIVE_ATTRIBUTION_RESOLUTION
NATIVE_SCOPE_RECONCILIATION_OBSERVED
NATIVE_SCOPE_RECONCILIATION_RESOLUTION
POST_FINAL_INTEGRITY
```

Known-tranche events require the canonical logical lineage. Native unattributed reductions contain only native/account-scoped factual identity and must not fabricate logical lineage. A financially complete authoritative logical result, when available, is carried only on the strict `LOGICAL_TRANCHE` variant. Event replay retains original event/result/native-observation identities. Portfolio Rules still performs required API-backed reconciliation.

---

# 37. Order Placed and entry lifecycle synchronization to Set

`Order Placed` is sent only after actual exchange acceptance.

Minimum payload:

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

Set uses `decision_cycle_id` to locate the exact frozen pending-order invalidation conditions created for that cycle.

Canonical:

```text
Order Placed
→ Set locates frozen conditions for decision_cycle_id
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

Order Lifecycle then cancels the still-live entry order/remainder.

To prevent stale monitoring, Order Lifecycle also sends a minimal `Entry Lifecycle Event` to Set when the pending-entry phase becomes terminal.

Event types:

```text
FULL_FILL
CANCELLED_ZERO_FILL
ENTRY_REMAINDER_CANCELLED
SUBMISSION_FAILED_AFTER_PLACEMENT_RECONCILIATION
```

Minimum identity:

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

Set uses this only to stop/update the pending-order monitor.

It does not change market logic.

Do not send `Order Placed`:
- before exchange acceptance;
- merely because submission was attempted;
- while submission is ambiguous.

---

---

# 38. Order Cancel Signal consumption

Canonical input uses two strict causes in the same family/version 2:

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

Canonical field semantics, reason classes and requirement identity are defined
in [`ORDER_CANCEL_SIGNAL.md`](../business-contracts/ORDER_CANCEL_SIGNAL.md),
Semantics; §11.1 is the condensed input description.

Order Lifecycle validates schema, identity/content and the exact persisted
cycle/result/tranche/symbol-to-original-accepted-entry relationship. It does
not validate the market condition, Trigger logic or direction logic. An
unusable frozen record does not authorize replacing this independent routing
lineage with symbol/time/latest-result inference.

For INVALIDATION, preserve the existing Set-owned frozen record/condition/
factual evidence, evidence-effective invalidated_at and original signal_id.
Verify the current authoritative remainder and cancel only its unfilled
quantity; a fully filled or otherwise terminal entry makes the signal an
idempotent no-op. No evidence authorizes closure of filled exposure.

For MONITORING_UNAVAILABLE:

1. Validate `signal_id == unavailable_requirement_id`, the exact routing
   lineage and the entry-scoped requirement key in Order Cancel Signal
   Semantics. Persist the first accepted payload and receipt/deduplication
   before any side effect. Identical retries return the prior receipt/progress;
   changed content under an identity, or a second identity claiming the same
   requirement key, is an integrity/reconciliation condition, not an update.
2. Reconcile authoritative state of that original accepted entry first. If
   terminal/no unfilled remainder is proven, retain the terminal revision/
   tombstone, record the requirement as no longer applicable and issue no
   market/native cancellation. Never close filled exposure. If routing or
   remainder truth is unresolved, retain the request for reconciliation with
   no guessed target, assumed zero quantity or blind cancel.
3. If an exact active unfilled remainder is proven, admit/preserve and execute
   the sticky cancel-required intention using existing entry cancel handling.
   Recheck authoritative state before a native side effect; reconcile any fill/
   cancel race. A partial fill changes quantity, not the requirement identity.
4. `unavailable_at` remains the original Set state-transition effective time,
   not a TRUE invalidation or Lifecycle receipt time. Preserve its initial
   unavailable_reason_code and optional-record presence/value. Market recovery
   cannot erase or replace this requirement. Lifecycle never asks current
   market analysis to grant or withdraw its execution applicability.
5. Restore the immutable receipt/payload, requirement-to-entry binding,
   delivery/deduplication and reconciliation/cancel progress, and current
   authoritative Lifecycle remainder revision/tombstone after restart.
   Delivery/cancel acknowledgement is not terminal proof. Terminal dominance
   ends applicability without deleting replay identity; a delayed message
   cannot reactivate the entry. Missing/conflicting recovery state is an
   integrity/reconciliation condition, never permission to remint or retarget.

Receipt of the unavailable envelope is the fail-closed reconciliation request;
it is not itself a market invalidation or authorization to cancel before
reconciliation. Known terminal proof suppresses any new Set request, while a
terminal race after transmission follows the idempotent no-op branch above.
The same envelope becomes an executable intention only on positive pending
proof, without another message family. Multiple causes for one entry join its
existing cancel intent. Terminal state returns through the unchanged Order
Placed/entry-lifecycle-event boundary with monotonic lifecycle_revision.

The F-013 four-outcome reducer is unchanged. Neither route creates a new
execution edge, closes filled exposure, modifies TP/SL/Manual Close, replaces
S-004 CLOSED, or releases Portfolio capital before canonical finality.

---

# 39. Set-monitor termination synchronization

Set monitoring concerns only unfilled entry remainder.

Order Lifecycle must make terminal entry state observable such that monitoring can stop when:
- full fill leaves no remainder;
- zero-fill cancel completes;
- partial-fill remainder cancel completes;
- entry is definitively rejected/failed.

`Order Placed` is the activation event.

The exact transport may use the canonical lifecycle correlation, but Order Lifecycle must not leave stale pending-entry monitors after terminal entry state.

---

# 40. Manual user visibility

User-facing lifecycle should expose at least:

```text
Pending
Partially Filled
Open
Cancel Pending
Closed
Failed
Reconciling
```

Diagnostics may show finer internal states.

For every tranche the UI/audit layer should be able to answer:
- Was the order submitted?
- Was it accepted?
- How much filled?
- How much remains pending?
- Is TP/SL protection confirmed?
- Was cancellation requested?
- Why did it cancel?
- Is the tranche open or closed?
- What was the close reason?
- What are realized fees/funding/P&L?
- Is the system reconciling uncertainty?

---

# 41. Reason codes

Canonical baseline families:

```text
SUBMIT_*
ACK_*
FILL_*
CANCEL_*
PROTECTION_*
CLOSE_*
RECONCILIATION_*
API_*
IDENTITY_*
```

Baseline explicit codes:

```text
NO_SUBMISSION_AUTHORIZATION
IDENTITY_MISMATCH
SUBMISSION_REJECTED
SUBMISSION_UNCERTAIN
ORDER_NOT_FOUND_AFTER_RECONCILIATION
CANCEL_REQUESTED
CANCEL_UNCERTAIN
CANCEL_FILL_RACE
PROTECTION_UNCONFIRMED
TP_SL_STATE_MISMATCH
EXECUTION_DUPLICATE_IGNORED
OUT_OF_ORDER_EVENT_RECONCILED
API_UNAVAILABLE
MANUAL_INTERVENTION_REQUIRED
```

---

# 42. Hard invariants

1. Order Lifecycle never performs market analysis.
2. Order Lifecycle never changes Set direction.
3. Order Lifecycle never recalculates Entry / SL / TP.
4. No submit until matching `Order Spec` and `Submit Authorized` are both received; `Submit Authorized` is emitted only after successful Portfolio `SUBMISSION_HOLD`.
5. Entry baseline is LIMIT + POST_ONLY.
6. POST_ONLY is submitted as an exchange instruction; TriggerTrade does not impose a local minimum resting-time or bid/ask marketability gate.
7. No automatic market fallback.
8. No automatic replace/reprice/chase.
9. No blind retry after ambiguous submit.
10. `client_order_link_id` must support exact reconciliation.
11. `Order Placed` is sent to Set only after actual exchange acceptance.
12. `Order Cancel Signal` cancels only unfilled entry remainder.
13. Set invalidation never closes already filled exposure.
14. Partial fill is real exposure.
15. Cancel request does not release anything until exchange terminal truth is reconciled.
16. Cumulative filled quantity is monotonic.
17. Duplicate executions never double-count quantity, fees, or P/L.
18. Every filled quantity must have confirmed protective handling, and sibling TP/SL cleanup must be confirmed when a tranche closes.
19. If filled exposure closes while entry remainder exists, remainder must not be left able to refill later.
20. Logical tranche identity remains distinct from aggregate exchange position.
21. Manual Close identifies logical `tranche_id`.
22. Reconciliation uses exchange execution facts as authority for executed quantity.
23. Existing exchange TP/SL remain active during TriggerTrade connectivity outage.
24. No arbitrary pending-order TTL exists in the baseline.
25. Funding is accounting data and never an exit trigger.
26. Portfolio Rules receives lifecycle changes through `Order Event`.
27. Portfolio Rules owns capital accounting; Order Lifecycle does not mutate portfolio bookkeeping directly.
28. Set owns pending-order market validity.
29. A new opportunity after cancellation requires a new Set match and new decision cycle.
30. Terminal lifecycle state must be reconstructable after restart.
31. Every material lifecycle event is propagated to Portfolio Rules as `Order Event`.
32. The managed futures account/subaccount is dedicated to TriggerTrade-only trading activity.
33. CLOSED always requires all six P6 predicates; full logical commitment and a slot remain occupied until that transaction.
34. All close-related paths atomically acquire-or-join by tranche_id; residual authorization shares that serialized authority.
35. FINAL requires complete mandatory financial evidence obtained on this block's own API boundary, with accounting day fixed by P8.

---

# 43. Research and diagnostics

Persist at least:

```text
submission attempts
submission acceptance rate
submission rejection reasons
ambiguous submission frequency
native POST_ONLY rejection/cancellation observations (not local predictions)

time from submit to acceptance
time to first fill
time to full fill
partial-fill frequency
fill ratio
cancel frequency
cancel/fill race frequency

Set-driven cancel frequency
manual cancel frequency
zero-fill cancel frequency
partial-fill remainder cancel frequency

TP close frequency
SL close frequency
Manual Close frequency

reconciliation frequency
reconciliation duration
restart recovery corrections
duplicate event count
out-of-order event count

protection verification failures
manual intervention count

authorization_id
authorization_received_at
authorization_consumed_at

entry_terminal_event_sent_to_set_at

sibling_protection_cancel_started_at
sibling_protection_cancel_confirmed_at

close_remainder_race_detected
additional_fill_after_close_intent_qty

funding_allocation_basis

realized entry fees
realized exit fees
realized funding
gross realized P&L
net realized P&L
```

---

# 44. Source consolidation map

This methodology consolidates and supersedes the active architectural role of:

```text
TRIGGERTRADE_ORDER_LIFECYCLE_INPUT_ROLE_ASSIGNMENT_v0.1
```

while preserving its useful execution mechanics:
- stable logical tranche identity;
- acknowledgement handling;
- partial/full fill distinction;
- cancel/fill race handling;
- event idempotency;
- event ordering;
- reconciliation;
- restart recovery;
- execution fee/funding/P&L attribution;
- aggregate-exchange-position vs logical-tranche separation.

The following old assumptions are superseded:
- separate Portfolio State architecture block;
- legacy portfolio_request_id / request_item_id;
- automatic/future reprice as ordinary lifecycle behavior;
- post-submission market structure refresh in Order Lifecycle;
- Order Lifecycle ownership of market validity.

Canonical replacement:

```text
Order Event → Portfolio Rules → Portfolio Data Request
Order Placed → Set
Set → Order Cancel Signal
```

---

# Appendix A — Tranche-isolated protection and close protocol (v1.1.0)

P5 is the single active protocol: atomic durable acquire-or-join keyed by tranche_id; at most one active intent; serialized residual calculation/child authorization; reconciliation before any next reduction. Every TP/SL/Manual/retry/restart callback joins it, never independently creates an intent.

Canonical durable intent record:

```yaml
close_intent_record:
  close_intent_id:
  tranche_id:
  intent_revision:
  state: ACQUIRED | RECONCILING_CHILDREN | REDUCTION_AUTHORIZED | REDUCTION_UNCERTAIN | AWAITING_EXECUTIONS | AWAITING_FINALITY | RESOLVED
  cause_event_ids: []
  close_commitment_quantity_basis:
  confirmed_target_quantity:
  confirmed_residual_quantity:
  authorized_reduction_quantity:
  executed_reduction_quantity:
  execution_authority_revision:
  entry_remainder_terminal: false
  protection_child_ids: []
  close_child_ids: []
  unresolved_request_ids: []
  resolved_at: null
```

An active-uniqueness database constraint or equivalent durable compare-and-set is required; an in-memory flag or outbox alone is insufficient. Quantity authorizations and source execution application serialize on that same logical authority. Child status/identity arrays retain every generation, not a single assumed pair. Native-generated child IDs are preserved without invented client IDs. Zero residual is not CLOSED until P6. Native competing-child conformance is a separate enforced runtime gate.

---

# Appendix B — External exchange reductions

Liquidation, ADL, or another venue-originated reduction is a factual reconciliation classification, not a fourth deliberate strategy close reason. Normalize events as:

```text
EXTERNAL_REDUCTION
EXTERNAL_CLOSE
external_cause = LIQUIDATION | ADL | OTHER_EXCHANGE
```

Preserve actual exchange executions/costs and reconcile them to logical tranches where deterministically possible. Never label them TAKE_PROFIT, STOP_LOSS, or MANUAL_CLOSE and never reopen reduced quantity. If attribution is ambiguous, retain reconciliation/manual-intervention state and block new exposure until resolved.

# Appendix C — Durable messaging and monotonic Set synchronization

Material lifecycle state and outgoing Order Event / Order Lifecycle→Set messages are persisted atomically through a transactional outbox or equivalent before delivery. Replays retain original IDs.

For each `decision_cycle_id`, Order Lifecycle publishes monotonically increasing `lifecycle_revision`. Entry-terminal events create a durable terminal tombstone at Set. Terminal revision dominates any delayed lower/equal placement revision; a late `ORDER_PLACED` can never reactivate a terminal monitor.


## Order Spec gate-state validation

Before submit eligibility, Lifecycle validates the immutable approved spec representation: `minimum_net_edge_enabled=true` requires `minimum_net_edge_result=PASS`; `minimum_net_edge_enabled=false` requires `minimum_net_edge_result=NOT_APPLICABLE`. Any other pairing is a contract/integrity failure and cannot be submitted. Lifecycle preserves the status on replay and never converts NOT_APPLICABLE into PASS.

For `venue_validation.max_order_qty_status=AVAILABLE`, `entry.quantity` must be `<= max_order_qty`; violation is an integrity failure, not a resize opportunity.

# Appendix D — No strategic partial close / capital-release semantics

Strategic partial close, multi-TP and scale-out are absent. Partial TP/SL/Manual/native reduction is execution progress in the same close intent. P6 retains the entire logical own-capital commitment and slot through every intermediate/flat-but-unclean state. All six common terminal predicates, including financial finality and no competing authority, are required before CLOSED.

# Appendix E — Native observations and complete attribution

P9 specifies the independent native_scope_revision domain (account/environment/symbol/side), stable native_observation_id, one attribution_resolution_id and monotonic resolution_revision. Native events never fabricate cycle/tranche IDs or use cycle lifecycle_revision. Persist unknown observations and their block; after exact evidence, atomically publish the complete expected allocation manifest and strict per-tranche allocation events through Order Event.

First partial logical delivery never resolves the native block. Portfolio clears only when complete evidence and every expected allocation have been applied once, retains resolved tombstones and ignores only genuine identical old replay. A different previously unseen observation remains unresolved even with an older scope revision. Restart restores manifests, allocations and outboxes; no symbol/time matching is allowed.

---

# Appendix F — Native adapter conformance gate

Documentation does not certify native close/protection isolation. The relevant exposure-changing adapter feature remains disabled until conformance tests pass for the pinned Bybit linear USDT perpetual, hedge mode, isolated margin, native `symbol + positionIdx` side model, including quantity-scoped close/protection invariants and restart/reconciliation behavior.

# Appendix G — F01–F08 factual recovery and financial synchronization

P10 governs native protective recovery and immutable entry acceptance. Persist all normalized source records/provenance, native-child mappings, acceptance fact/provenance or unresolved status and cumulative outboxes before effects. Outbound attachment success is not installed protection proof. Query actual children on restart, prove unique native relationship and verify immutable geometry/quantity/semantics; insufficient or conflicting facts stay RECONCILING. No guessed ownership or blind resubmission. The same enhanced factual order/execute types are used by Order Management's operation and financial-history responses.

P12 governs **only** shared execution-linked non-funding allocations after complete P9 quantity proof. Lifecycle persists the full manifest/staged rows/source aliases/source-commit tombstone and emits per-tranche committed rows in financial_result version 3. Fees/rebates and other costs use their distinct cost-effect totals; funding retains §32 exactly. Split financial publication can be delivered separately only after the atomic complete source posting; neither Portfolio nor API allocates logical fees. Missing rows, aliases with conflicting values, unresolved lineage or incomplete mandatory coverage prohibit FINAL and CLOSED.

P13 governs authoritative execution-ledger reconstruction and permanent zero across restart, duplicate/reordered callbacks and temporary zero followed by entry refill. Execution ID/time/native sequencing, opening checkpoint evidence, complete prefix coverage and terminal entry state are durable. The final accounting timestamp is never overwritten by the last callback. P8's historical accounting-day and Daily Loss rules remain unchanged. P11/TT_NUMERIC_V1 governs non-funding economic output classes, not a new funding calculation.

P14's consumed authorization tombstone is restored before any submission. Definitive no-create terminal means no dispatch, no recreated hold/slot, regardless of later compatible metadata or duplicate authorization. This is distinct from ambiguous submission, which retains existing reconciliation and no-blind-create-retry safety.

Acceptance/restart tests derived from these paths are specification conformance tests only; native adapter and database conformance remain runtime obligations.

## Execution-evidence implementation rules

The active Order Event contract is **version 7**. Its six registered variants are LOGICAL_TRANCHE, NATIVE_UNATTRIBUTED_REDUCTION, NATIVE_ATTRIBUTION_RESOLUTION, NATIVE_SCOPE_RECONCILIATION_OBSERVED, NATIVE_SCOPE_RECONCILIATION_RESOLUTION and POST_FINAL_INTEGRITY. POST_FINAL_INTEGRITY follows T01; the two NATIVE_SCOPE variants follow P15. The two NATIVE_SCOPE variants represent no-reduction unresolved native-order observations and authoritative clearance; they neither fabricate logical IDs nor post execution/financial effects. See SYSTEM_PROTOCOLS P15 for scope blocking, complete bindings and tombstones.

Under P10 merge protection evidence by field: allow authoritative null-to-known enrichment, keep proved immutable facts, retain per-field provenance, order mutable facts using the pinned native profile and reject real contradictions. An incomplete early callback cannot permanently poison later complete recovery, and an older incomplete callback cannot erase proven coverage. Persist merged facts and conflict evidence before their derived reconciliation state/outbox is published.

Acceptance conflict is independently durable. Order Event v7 publishes CONFLICT with `entry_acceptance_integrity` whenever contradictory authoritative acceptance evidence exists, even if the first `entry_accepted_at` is known. Portfolio receives the unresolved incident through this same edge. Stale evidence cannot clear it; explicit authoritative resolution preserves the first original acceptance timestamp and a tombstone covering the discredited conflict evidence.

P12 financial allocation consumes monotonic quantity-resolution proof. Preserve accepted source/identity/revision/digest and complete set; ignore older progress, reject same-revision differences, and bind staged/committed source cashflows to the accepted complete proof. Finality remains blocked until all mandatory source allocations and coverage are complete. Existing funding allocation is unchanged.

P13 closure eligibility is a revision-bound proof over current execution, entry authority, protective/exit authority, coverage, close-intent and financial-evidence revisions. Recompute after any relevant change. A newly proven entry refill invalidates an earlier zero/cleanup/day proof. Before FINAL/CLOSED and its release-authorizing outbox, atomically recheck all six P6 predicates against the current revisions and zero exposure. Repeated cleanup cannot mutate terminal timestamps. Contradictory post-final evidence creates a durable integrity incident without silently rewriting the already-final result/day or duplicating receipts. Native acceptance mappings, updated-state ordering, cleanup certificates and persistence atomicity remain runtime conformance gates.

## Focused close, evidence and accounting requirements

Apply SYSTEM_PROTOCOLS S01–S06 to all Lifecycle paths, including close and quantity-attribution processing. Current closure is a certificate-backed conjunction, not a cached COMPLETE/flat flag. Re-evaluate the complete source-revision vector before the atomic result/resolved-intent/CLOSED outbox commit. A later entry execution before final commit invalidates stale zero/coverage/day proof; economic chronology still determines accounting_effective_at. After committed terminal finality, contradictory evidence enters durable integrity quarantine without rewriting the committed ledger/result/day or re-authorizing a resolved close. The Portfolio receipt remains once-only and cannot newly release under known unresolved integrity.

Protection recovery accepts first proven mutable field enrichment over UNKNOWN/unproven values at an equal enclosing timestamp. Persist per-field proven version/history, keeping real same-version conflicts, cumulative regressions and terminal resurrection blocking. Native-scope tombstones preserve accepted observation content history before stale-revision filtering; no-reduction integrity events have no quantity/P&L effect.

Quantity allocations have global immutable source/observation/resolution/tranche bindings and atomic quantity/application receipts. Complete native manifests contain explicit source scope/revision and total, so manifest-first recovery never reconstructs ownership heuristically. Independently proven reconciliation quantities may still be ingested while eligibility remains blocked by an incident.

Gross final trading result uses all attributable actual entry and exit executions exactly once (LONG exit proceeds minus entry cost; SHORT entry proceeds minus exit cost). An authoritative opening cost checkpoint covers explicit factual executions/source revision and cannot be synthesized from planned Entry. Missing price or incomplete chronology/coverage prevents finality. Partial native fill reporting remains nonfinal until the existing full-tranche close predicates and factual fee/funding/cost evidence are complete. No execution formula, protection strategy or funding allocation is changed.


## T01–T04 — Terminal integrity and evidence eligibility

The active ORDER_EVENT family is v7. Emit the strict POST_FINAL_INTEGRITY variant
for post-final execution, authority, financial source or coverage contradictions.
Persist first observation/evidence, incident revision and real outbox append
atomically. Preserve committed FINAL/CLOSED basis/result/day and resolved close
intent; new evidence belongs to quarantine, not the accepted terminal ledger.
See SYSTEM_PROTOCOLS T01/T02 and ORDER_EVENT for exact payload, independent dedupe,
resolution proof and the transport receipt fence. Lifecycle does not own or guess
Portfolio's receipt state. An undelivered committed incident is not a safe reason
for Portfolio to release; a receipt already applied is never silently reversed.

Every financial-finality path, including component allocation consumers, binds
execution/source/coverage/attribution/day revisions at commit. Component FINAL is
not full-tranche FINAL. Use explicit actual parent-result links to report a later
component contradiction to each affected terminal result; do not fabricate those
links. Identical replay is idempotent; changed evidence quarantines; supplemental
coverage never replaces the immutable final basis.

Current live protection is derived from the applicable complete query generation,
not the union of old rows. Preserve historical child identity after a newer
complete empty/subset same-scope query, invalidate live verification, and obtain
field-proven history/execution facts. Absence neither proves terminality nor
authorizes blind replacement. S02 equal-timestamp unproven enrichment remains
unchanged; query membership consistency is a separate T03 proof.

T04 requires staged native allocations with zero pre-manifest quantity effect.
Validate complete membership and disjoint exact source slices against original
authoritative quantities before atomically consuming source quantity and posting
logical receipts. Preserve legitimate multi-tranche partitions; reject overlapping
IDs/aliases, over-total and outside-manifest claims without a second effect.
Independent valid quantities can reconcile while integrity retains the scope
block. These internal proof records do not change the architecture or add new
trading execution semantics.

## U01–U05 implementation binding

SYSTEM_PROTOCOLS.md U01–U05 is normative for these existing responsibilities: current accepted-source/coverage/allocation proof equality at component FINAL; full immutable `financial_record` core before terminal dedupe; explicit-parent T01 incidents for post-FINAL source contradictions; canonical acceptance-resolution content before stale suppression; confirmed execution precedence over rejection; and raw magnitude/direction validation before signing. A locally FINAL component is not authority to finalize a parent while its source completeness or quarantine is unresolved. No financial-accounting ownership moves to Portfolio. The existing allocation formulas, CLOSED predicates, accounting-effective chronology, close concurrency, protection proof and execution rules remain unchanged.


## V01–V04 evidence-ingestion refinement

The normative V01–V04 clauses in SYSTEM_PROTOCOLS.md apply to this existing owner. Known cashflow identities are compared before pre-FINAL routing rejection; full immutable source/sign/finality rules remain unchanged. Authority and coverage facts—including terminal entry, protection disable and close-child terminal evidence—are checked against persisted revision/content history before terminal or stale suppression. Corroborating post-final revisions are history, not a replacement final proof. POST_FINAL_INTEGRITY remains the existing ORDER_EVENT v7 variant with explicit parent-result linkage.

Revisionless acceptance is the complete normalized status/time/provenance binding, not provenance membership alone. Internally contradictory replay preserves the original acceptance time, durably reblocks integrity and propagates conflict to Portfolio. Current protection proof is invalidated in the same native-fact merge transaction whenever an effective dependency changes, regardless of query operation; hydration revalidates it before exposure. Historical mapping remains intact; terminal child facts do not automatically replace protection or close the tranche. These changes add no trading authority, API edge or accounting owner.
