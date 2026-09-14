# TriggerTrade — Position Rules Methodology

**File:** `POSITION_RULES.md`  
**Version:** 1.2.14  
**Architecture role:** `Position Rules — Trade Decision`


**Shared normative protocols:** `../SYSTEM_PROTOCOLS.md` (P1–P17). **ID ownership:** `../IDENTIFIER_LINEAGE.md`. Generated wire-shape illustrations use the strict schema registry in `../schemas/`; nullable annotations are not literal payload objects.

## Purpose

This is the single canonical methodology document for the TriggerTrade **Position Rules** block.

It consolidates the previously approved Position Rules decision methodology and the approved calculation methodologies for:

- Dynamic Limit Entry;
- Fixed / Dynamic Stop Loss;
- Fixed / Dynamic Take Profit;
- leverage and notional conversion;
- quantity normalization;
- fee-aware economics;
- gross Risk / Reward;
- Minimum Net Edge;
- initial opportunity `APPROVE / REJECT` and post-grant construction result;
- final `Order Spec`.

Canonical external flows:

```text
Portfolio Rules → Position Rules
Capital and Limits

Set → Position Rules
Market Handoff

Position Rules → Portfolio Rules
Approve / Reject

Position Rules → Order Lifecycle
Order Spec

Portfolio Rules → Order Lifecycle
Submit Authorized
```

Position Rules has no direct API flow.

`decision_cycle_id` is created by Set and must be propagated unchanged through Position Rules into `Order Spec`.

No Position Rules-owned methodology should remain as a separate top-level architecture document after this document is approved.

---

# Part I — Canonical Position Rules Decision Methodology

# 1. Purpose

Position Rules owns the opportunity decision and final trade construction for one Set-created cycle. It first decides APPROVE / REJECT from the immutable Market Handoff and configured market/geometry rules. Only after APPROVE does Portfolio issue Capital and Limits. Position then constructs and validates the final sizing, leverage, notional, committed capital and fee-aware economics, and emits the immutable Order Spec if construction succeeds.

This is the P1 two-stage protocol on the existing boundaries. No market re-analysis, direction change, new strategy or direct Position API query is introduced. The formulas in this document retain their original numerical meaning.

---

# 1A. Logical tranche as Position Rules decision unit

A successful post-grant construction creates one TriggerTrade logical tranche. Native exchange positions may aggregate multiple same-symbol/same-side tranches; logical counts and ownership remain separate.

Before the initial opportunity decision, only Set-owned `decision_cycle_id`, `set_result_id` and Position-owned `position_decision_id` exist. No grant or final plan/tranche/spec is required or permitted in initial APPROVE/REJECT. Portfolio creates the immutable `capital_grant_id` only when issuing Capital and Limits after APPROVE. Position finalizes `position_plan_id`, `tranche_id`, `order_spec_id` and `construction_result_id` during successful post-grant construction. Failure has an outcome ID, not fabricated successful plan/spec data.

IDs alone reserve no capital, prove no native order and imply no exposure. The complete owner/timing table is `../IDENTIFIER_LINEAGE.md`.

---


# 1B. Position Rules configuration selection and immutable binding

The canonical Position configuration-selection boundary is the first evaluation of the concrete Market Handoff for the initial `OPPORTUNITY_DECISION`. Before calculating or persisting APPROVE/REJECT, Position selects the then-effective governed Position Rules configuration and atomically persists with `position_decision_id` and `decision_cycle_id` its `configuration_id`, `configuration_version` and canonical `configuration_content_digest`. This is the pinned Position configuration for the entire decision cycle.

Every initial market/geometry gate and every later post-grant construction step—leverage, sizing, quantity, notional, fee-aware economics, Minimum Net Edge and final Order Spec—uses that same pinned configuration. If configuration Cn+1 becomes active while the approved cycle is waiting for Capital and Limits, Cn+1 applies only to future Position decision cycles; this cycle continues under Cn. Frozen Entry/SL/TP geometry is not recomputed under a later configuration. Replay/restart hydrates the persisted binding and fails closed on conflicting content for the same identity/version.

`ORDER_SPEC.provenance.position_rules_version` names the pinned Position Rules version selected at initial evaluation, never the version current at construction time. The owner-local decision record retains the corresponding configuration identity and content digest, so the wire provenance version is auditable against one immutable configuration. No new Position↔API or business edge is created.

# 2. Governing architecture

Position Rules is the TriggerTrade **Trade Decision** block.

Canonical external flows:

```text
Portfolio Rules → Position Rules
Capital and Limits

Set → Position Rules
Market Handoff

Position Rules → Portfolio Rules
Approve / Reject

Position Rules → Order Lifecycle
Order Spec
```

Position Rules has **no direct API flow** in the canonical architecture.

It consumes only the governed facts and constraints delivered through its upstream contracts.

It does not:
- re-analyze the market;
- change Set direction;
- own portfolio capital state;
- manage order lifecycle after handoff.

---
# 3. Responsibility boundary — Set

Set owns:

```text
market match
direction = LONG | SHORT
Market Handoff
decision_cycle_id creation
```

Position Rules receives:

```text
decision_cycle_id
set_result_id
symbol
direction
Market Handoff
```

Direction is immutable downstream.

Position Rules must not:
- infer direction independently;
- reverse direction;
- request Set to recalculate the historical match;
- receive Market Invalidation Inputs;
- participate in pending-order market-validity monitoring.

Market Invalidation Inputs remain internal to Set.

---
# 4. Responsibility boundary — Portfolio Rules

Portfolio owns own-capital allocation, limits, slots, grants, holds, cooldown and free-capital accounting. Position first sends the Set-correlated opportunity APPROVE/REJECT. Only an APPROVE permits Portfolio to issue Capital and Limits with the exact cycle/decision binding. Position cannot invent the grant before that message.

Position consumes the immutable grant for final construction without increasing requested capital or changing Portfolio allocation. It confirms the exact constructed spec/economics to Portfolio through the CONSTRUCTION_RESULT variant on the same Approve / Reject boundary. Portfolio then atomically rechecks current gates and books a hold; initial APPROVE alone creates no hold. The separate Order Spec goes to Lifecycle, which waits for matching authorization. See P1–P2.

---

# 5. Governed venue facts used by Position Rules

Position Rules may require venue facts such as:

```text
tick_size
qty_step
min_order_qty
min_notional
allowed leverage / instrument constraints
maker_fee_rate
taker_fee_rate
fee_schedule_version / effective_at
```

Position Rules does **not** query the API directly.

Required venue facts must be supplied through the governed `Portfolio Data Request → Portfolio Rules → Capital and Limits` route and must include enough provenance to prove which version/effective state was used for the decision. The immutable grant context carries the required instrument constraints and account fee-rate snapshot; Position Rules never fills these facts from local defaults.

Canonical principle:

```text
API-derived fact
→ upstream contract
→ Position Rules
```

Position Rules consumes the fact; it does not own the API dependency.

During post-grant construction, if a required factual value is missing or invalid (P2; no grant-age TTL):

```text
REJECT
```

Position Rules must never guess venue facts.

Actual post-submission execution facts remain Order Lifecycle-owned.

---


# 5A. Canonical input binding

Initial opportunity evaluation consumes only the concrete Market Handoff and configured Position rules. It persists its decision identity and market/geometry result before emitting APPROVE/REJECT. Capital-dependent gates are NOT_YET_EVALUATED at this stage, not fabricated PASS/UNAVAILABLE.

Only final construction joins that exact approved Market Handoff with the Capital and Limits carrying the same decision_cycle_id, set_result_id and position_decision_id. It persists capital_grant_id, source revisions and the completed plan/spec. The immutable grant and market snapshot are not selected by symbol, time, latest revision or arrival order. P2 defines delayed grants and compatible newer hard facts. No age-based grant expiry or silent geometry repair exists.

---

# 6. Responsibility boundary — Order Lifecycle

Position emits Order Spec only after successful post-grant construction. The same transaction persists CONSTRUCTION_RESULT(CONSTRUCTED) for Portfolio with the matching digest/economics. Initial APPROVE is neither a completed Order Spec nor capital authorization.

Lifecycle requires matching Order Spec + Submit Authorized across all lineage and digest fields. Portfolio creates authorization only with the successful current-gate/capacity hold transaction. A spec without authorization cannot execute; a missing spec does not erase an existing hold. Delivery order is irrelevant and introduces no TTL.

Lifecycle owns technical submission, native acknowledgement, fills, cancellation, reconciliation, protective children and close execution. It performs only P2 hard non-market technical compatibility before submit, not market analysis, bid/ask crossing prediction, economic recalculation, price movement, chase or reprice. Set alone owns market invalidation after placement. A Position construction REJECT produces no spec or hold.

---

# 7. Position close conditions

An open position may close only by:

```text
TAKE_PROFIT
STOP_LOSS
MANUAL_CLOSE
```

Not valid automatic exit conditions:

```text
midnight
session end
calendar day end
maximum holding hours
funding event
arbitrary timer
```

Funding may affect realized economics but is never an exit trigger.

`MANUAL_CLOSE` must identify the logical `tranche_id` to be closed. The lifecycle/execution layer is responsible for translating that logical close into the correct reduction of aggregate exchange exposure.

---

# 8. User Position Rules configuration

Canonical v0.2.1 configuration:

```yaml
position_rules:
  stop_loss:
    mode: DYNAMIC | FIXED
    fixed_pct: nullable

  take_profit:
    mode: DYNAMIC | FIXED
    fixed_pct: nullable

  minimum_risk_reward:
    enabled: true | false
    value:

  minimum_net_edge:
    enabled: true | false
    pct:

  leverage:
    value:
```

`Position Size` is not a Position Rules field.

Activation of an edited configuration does not mutate any already-started Position decision cycle. Selection/pinning follows §1B and P17.

---

# 9. Fixed Stop Loss semantics

If:

```text
stop_loss.mode = FIXED
```

then the user supplies:

```text
fixed_sl_pct = S
```

## LONG

```text
raw_sl =
Entry × (1 - S / 100)
```

## SHORT

```text
raw_sl =
Entry × (1 + S / 100)
```

Then normalize to tick size while preserving direction.

No market-structure SL logic runs in FIXED mode.

---

# 10. Dynamic Stop Loss semantics

If:

```text
stop_loss.mode = DYNAMIC
```

use the approved Dynamic Stop Loss methodology.

Input includes:

```text
planned_entry_reference
Set Market Handoff
sl_context
```

Output:

```text
stop_loss_price
SL feasibility
SL diagnostics
```

If unusable:

```text
SL_UNAVAILABLE
→ REJECT
```

---

# 11. Fixed Take Profit semantics

If:

```text
take_profit.mode = FIXED
```

and:

```text
fixed_tp_pct = P
```

then:

## LONG

```text
raw_tp =
Entry × (1 + P / 100)
```

## SHORT

```text
raw_tp =
Entry × (1 - P / 100)
```

Then normalize to tick size while preserving direction.

No structural TP selection runs in FIXED mode.

---

# 12. Dynamic Take Profit semantics

If:

```text
take_profit.mode = DYNAMIC
```

use the approved Dynamic Take Profit methodology.

Input includes:

```text
planned_entry_reference
Set Market Handoff
tp_context
```

Output:

```text
take_profit_price
TP feasibility
TP diagnostics
```

If unusable:

```text
TP_UNAVAILABLE
→ REJECT
```

---

# 13. Dynamic Limit Entry semantics

Baseline Entry is the approved Dynamic Limit Entry methodology.

It returns:

```text
planned_entry_reference
limit_order_price
order_type = LIMIT
post_only = true
Entry feasibility
```

If unusable:

```text
ENTRY_UNAVAILABLE
→ REJECT
```

No market fallback.

---

# 14. Deterministic dependency order

The calculation formulas below are unchanged. P1 governs when their inputs legally exist:

```text
OPPORTUNITY stage:
configuration + concrete Market Handoff completeness
→ immutable Set direction
→ Dynamic Limit Entry
→ Fixed/Dynamic Stop Loss
→ Fixed/Dynamic Take Profit
→ feasibility and Entry/SL/TP geometry
→ gross structural risk/reward and enabled Minimum R:R
→ initial APPROVE / REJECT to Portfolio

Only after APPROVE:
Capital and Limits issued by Portfolio
→ bind immutable grant/cycle/decision
→ requested own capital and governed leverage
→ target notional / raw quantity / quantity normalization
→ actual notional / actual committed capital
→ venue, sizing, leverage and grant consistency
→ actual fee-rate planned TP/SL economics and net diagnostics
→ enabled Minimum Net Edge
→ CONSTRUCTION_RESULT(CONSTRUCTED | REJECT)
→ immutable Order Spec only for CONSTRUCTED
```

All independently evaluable gates in each stage are evaluated. No final gate status is fabricated before its required grant input exists. Failed final construction does not rerun Set or revise frozen Entry/SL/TP. Before native submit Lifecycle applies only P2 current hard compatibility to the exact spec.

---

# 15. Set direction gate

If:

```text
direction = NONE
```

return:

```text
REJECT
reason = SET_DIRECTION_NONE
```

Only:

```text
LONG
SHORT
```

may proceed.

---

# 16. Position geometry gate

After Entry, SL and TP are resolved:

## LONG

```text
SL < Entry < TP
```

## SHORT

```text
TP < Entry < SL
```

Otherwise:

```text
GEOMETRY_INVALID
→ REJECT
```

Position Rules may not move any price to fix the geometry.

---

# 17. Requested capital per tranche

The capital/quantity/leverage/fees/fee-aware economics gates in §§17–22 and §§28–40 execute only after Capital and Limits. Their REJECT outcomes mean the post-grant CONSTRUCTION_RESULT(REJECT), not a second initial opportunity decision. Geometry and gross R:R gates that can be evaluated from the frozen opportunity run at the initial stage as specified in P1. Rechecking unchanged mathematical consistency during final construction does not rerun Set or select new market references.

Input:

```text
requested_capital_per_tranche
```

Source:

```text
Portfolio Rules
```

Semantic:

```text
the user's own portfolio capital allocated to this logical tranche
```

Requirements:

```text
requested_capital_per_tranche > 0
finite
same settlement/accounting currency as Portfolio Rules
```

If invalid:

```text
REQUESTED_CAPITAL_INVALID
```

---

# 18. Leverage-to-notional conversion

Let:

```text
C = requested_capital_per_tranche
L = user-configured leverage
```

For baseline linear USDT-settled futures:

```text
target_order_notional =
C × L
```

This is a Position Rules technical calculation.

Portfolio Rules continues to account only:

```text
C
```

The leveraged order notional is not fed back into portfolio allocation logic.

---

# 19. Raw quantity

```text
raw_qty =
target_order_notional
/
planned_entry_reference
```

Baseline scope assumes linear USDT-settled futures.

---

# 20. Quantity normalization and actual capital

Exchange facts:

```text
qty_step
min_qty
max_order_qty + max_order_qty_status + provenance when applicable
min_notional
```

Baseline:

```text
final_qty =
floor(raw_qty / qty_step)
× qty_step
```

Then:

```text
actual_order_notional =
final_qty × Entry
```

and:

```text
actual_committed_capital =
actual_order_notional / L
```

Only TT_NUMERIC_V1 output-class rounding is permitted. Arbitrary small numerical differences are not acceptable; the grant-aligned actual commitment invariant must hold exactly.

Portfolio Rules reconciliation should use:

```text
actual_committed_capital
```

while trade history stores both:

```text
actual_committed_capital
actual_order_notional
```

Position Rules does not increase quantity merely to force exact capital equality.

---

# 21. Minimum quantity and notional checks

Require:

```text
final_qty >= min_qty
actual_order_notional >= min_notional
```

For the pinned linear USDT perpetual `LIMIT + POST_ONLY` entry, if `max_order_qty_status = AVAILABLE`:

```text
final_qty <= max_order_qty
```

If the applicable maximum is required but `max_order_qty_status = UNAVAILABLE`, the quantity gate is `UNAVAILABLE` and cannot produce CONSTRUCTED or an Order Spec. `max_order_qty` is sourced only through `API → Portfolio Rules → Capital and Limits`; Position Rules never queries Bybit directly. `lotSizeFilter.maxOrderQty` is the canonical native source field for this baseline; deprecated `postOnlyMaxOrderQty` is prohibited.

Failure codes:

```text
QTY_BELOW_MINIMUM
QTY_ABOVE_MAXIMUM
NOTIONAL_BELOW_MINIMUM
```

---

# 22. Leverage

User config:

```text
leverage = L
```

Requirements:

```text
L > 0
L <= venue_max_leverage
```

Leverage does not modify:

```text
Entry
SL
TP
gross price distances
```

For baseline linear contract:

```text
margin_required =
actual_order_notional / L
```

which should approximately equal:

```text
actual_committed_capital
```

Venue-specific maintenance margin / liquidation mechanics are technical constraints and may be added later.

---

# 22A. Portfolio accounting boundary

Position Rules returns both:

```text
actual_committed_capital
actual_order_notional
```

Only:

```text
actual_committed_capital
```

is used by Portfolio Rules for:
- Coin Allocation;
- Max Capital in Positions;
- reservations/fills;
- free allocation;
- tranche balancing.

`actual_order_notional` is retained for order execution, risk diagnostics, fees, P/L, and trade history.

---

# 23. Gross risk distance

```text
risk_distance_price =
abs(Entry - SL)
```

```text
risk_distance_pct =
100 × risk_distance_price / Entry
```

---

# 24. Gross reward distance

```text
reward_distance_price =
abs(TP - Entry)
```

```text
reward_distance_pct =
100 × reward_distance_price / Entry
```

---

# 25. Gross Risk / Reward

Canonical user-rule comparator:

```text
gross_rr =
reward_distance_price
/
risk_distance_price
```

Equivalent monetary ratio may also be logged.

The explicit user `Minimum Risk / Reward` rule uses `gross_rr`.

---

# 26. Gross TP scenario P/L

Let:

```text
Q = final_qty
```

## LONG

```text
gross_profit_tp =
(TP - Entry) × Q
```

## SHORT

```text
gross_profit_tp =
(Entry - TP) × Q
```

---

# 27. Gross SL scenario P/L

Positive loss magnitude:

## LONG

```text
gross_loss_sl =
(Entry - SL) × Q
```

## SHORT

```text
gross_loss_sl =
(SL - Entry) × Q
```

---

# 28. Fee facts

Position Rules consumes governed fee facts supplied through upstream contracts:

```text
maker_fee_rate
taker_fee_rate
fee_schedule_version
fee_effective_at
fee_rate_source_ref
```

Fee values are not manually invented and are not fetched directly by Position Rules.

If a required fee fact is unavailable:

```text
MISSING_FEE_RATE
→ REJECT
```

---
# 29. Entry fee

Approved Dynamic Entry baseline:

```text
LIMIT + POST_ONLY
```

Therefore plan-stage expected entry fee uses governed maker fee rate:

```text
expected_entry_fee =
actual_order_notional
× maker_fee_rate
```

This is a plan-stage fee calculation based on the intended order mechanics.

---

# 30. TP exit fee

Baseline attached TP execution is `MARKET`, so Position Rules uses the governed current **taker fee rate**.

```text
expected_tp_exit_fee =
tp_exit_notional × taker_fee_rate
```

where:

```text
tp_exit_notional =
TP × final_qty
```

The rate comes from the governed upstream fee-fact contract.

---

# 31. SL exit fee

Baseline attached Stop Loss execution is `MARKET`, so Position Rules uses the governed current **taker fee rate**.

```text
expected_sl_exit_fee =
sl_exit_notional × taker_fee_rate
```

where:

```text
sl_exit_notional =
SL × final_qty
```

The rate comes from the governed upstream fee-fact contract.

---

# 32. Funding

Funding is not an exit condition.

Funding is **excluded from the baseline pre-trade Minimum Net Edge hard gate**.

Reason:

```text
position closes only by TP / SL / Manual Close
→ holding duration is not fixed
→ number and timing of future funding events are not known at plan creation
```

Therefore:

```text
funding_in_planned_net_edge = false
```

Position Rules must not invent future funding cost or credit.

If funding is actually incurred while the position remains open, it is recorded as realized position economics and included in realized PnL / diagnostics downstream.

A future separately approved expected-cost model may change this policy.

---

# 33. TP scenario total cost

```text
tp_total_cost =
expected_entry_fee
+
expected_tp_exit_fee
+
other_exchange_costs_if_deterministic
```

Credits must preserve sign.

---

# 34. Net TP profit

```text
net_profit_tp =
gross_profit_tp
-
tp_total_cost
```

---

# 35. Planned Minimum Net Edge

Portfolio capital accounting and trading-performance economics are separate units.

The change to `requested_capital_per_tranche` does not by itself redefine the already-approved Net Edge comparator.

Baseline pre-trade economics use only costs deterministically known from the planned order mechanics.

Funding is excluded from planned Net Edge and tracked separately after it is actually incurred.

Canonical:

```text
net_edge_pct =
100 × net_profit_tp
/
actual_order_notional
```

This is the Position Rules comparator for the user-configured:

```text
Minimum Net Edge
```

Hard gate:

```text
net_edge_pct >= configured_minimum_net_edge_pct
```

Failure:

```text
NET_EDGE_BELOW_MINIMUM
```

Position Rules must not move TP or Entry to repair this failure.

---

# 36. SL scenario total cost

```text
sl_total_cost =
expected_entry_fee
+
expected_sl_exit_fee
+
other_deterministic_sl_costs
```

---

# 37. Net SL loss

Positive loss magnitude:

```text
net_loss_sl =
gross_loss_sl
+
sl_total_cost
```

Planned SL economics exclude funding, just as planned Net Edge does. Signed actual funding receipts/payments are accounted only after they occur by Lifecycle; planned fee/rebate signs remain preserved.

---

# 38. Net R:R diagnostic

```text
net_rr =
net_profit_tp
/
net_loss_sl
```

This is diagnostic only in baseline v0.2.1.

It is not the comparator for user `Minimum Risk / Reward`.

---

# 39. Minimum Risk / Reward hard gate

If enabled:

```text
gross_rr >= configured_minimum_rr
```

Else:

```text
RR_BELOW_MINIMUM
→ REJECT
```

No price repair is permitted.

---

# 40. Minimum Net Edge hard gate

If enabled and evaluation succeeds:

```text
net_edge_pct >= configured_minimum_net_edge_pct
→ status = PASS
```

If enabled and the comparison fails:

```text
status = FAIL
reason = NET_EDGE_BELOW_MINIMUM
→ REJECT
```

If enabled but any required dependency is unavailable:

```text
status = UNAVAILABLE
→ REJECT
```

If disabled:

```text
status = NOT_APPLICABLE
```

A disabled gate is never represented as fabricated `PASS`. All fee effects remain inside an enabled calculation.

---

# 41. Fixed SL/TP tick normalization

For FIXED mode, raw percentages are converted from Entry and then normalized.

Canonical mandatory direction-preserving normalization:

## LONG

```text
Fixed SL → round DOWN
Fixed TP → round DOWN
```

## SHORT

```text
Fixed SL → round UP
Fixed TP → round UP
```

Rationale:
- SL rounding must not move inward through intended protection boundary.
- TP rounding must not move beyond intended target and should preserve realizability.

After rounding, geometry, gross R:R, and Minimum Net Edge must be recomputed and revalidated. Lifecycle never repairs a rounded result.

---

# 42. Validation result model

Every rule/gate returns:

```yaml
rule_result:
  rule_id:
  enabled:
  configured_value:
  calculated_value:
  operator:
  status: PASS | FAIL | UNAVAILABLE | NOT_APPLICABLE
  reason_code:
  dependency_reason:
```

Semantics:

```text
PASS
→ enabled rule evaluated and satisfied

FAIL
→ enabled rule evaluated and violated

UNAVAILABLE
→ enabled rule cannot be evaluated because required data/calculation is missing

NOT_APPLICABLE
→ rule is disabled or irrelevant for selected mode
```

Required `UNAVAILABLE` rejects the position.

---

# 43. Failure aggregation

Calculate all independently evaluable gates in the current stage. Initial opportunity FAIL/required UNAVAILABLE yields REJECT; otherwise initial APPROVE. Capital-dependent gates do not participate until the grant is issued; they are recorded only as NOT_YET_EVALUATED in the initial envelope.

During post-grant construction, any mandatory FAIL or required UNAVAILABLE yields CONSTRUCTION_RESULT(REJECT), otherwise CONSTRUCTED with immutable Order Spec. Disabled gates retain NOT_APPLICABLE. No second initial APPROVE is emitted and no failed gate is repaired by modifying the trade.

---

# 44. Dependency failures

Example:

```text
Entry unavailable
→ SL unavailable
→ TP unavailable
→ geometry unavailable
→ economics unavailable
```

Downstream unavailable calculations must be marked as dependency failures, not independent business failures.

Example:

```text
status = UNAVAILABLE
dependency_reason = UPSTREAM_ENTRY_UNAVAILABLE
```

---

# 45. No-repair invariant

Position Rules is forbidden from repairing a failing trade by:

```text
changing direction
moving Entry
moving SL
moving TP
changing fixed percentages
changing requested_capital
changing leverage for the purpose of repairing price geometry
```

It may only:

```text
calculate
validate
approve
reject
```

---

# 46. Canonical Portfolio Rules integration

The mandatory sequence is P1: Set MATCHED → Market Handoff → initial Position APPROVE/REJECT → only after APPROVE, Portfolio Capital and Limits → Position final construction/spec and construction confirmation → atomic Portfolio hold → Submit Authorized → matching-input Lifecycle gate.

requested_capital_per_tranche is own capital, not leveraged notional. No grant, plan or tranche is fabricated at initial APPROVE. No old Set result is reused for a different opportunity. Replaying the same immutable cycle/grant is recovery, not a fresh trade or an age-based failure.

---

# 49. Technical logical-tranche order specification

Only successful post-grant construction emits this exact canonical wire shape. Strict requiredness and types are `schemas/wire.schema.json` definition ORDER_SPEC; it is byte/structure synchronized with the standalone business contract.

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

Position does not supply client_order_link_id. Lifecycle creates/persists it before native submit. Native PARTIAL_QUANTITY protection expresses logical-tranche isolation, not strategic partial close. The adapter may translate field names, not invent trading values. The required funding_in_planned_net_edge=false is canonical in both schemas.

---

# 49A. Exchange aggregation invariant

For same symbol and same direction, Bybit may expose aggregated position state rather than one independent exchange position per TriggerTrade tranche.

TriggerTrade must therefore maintain its own tranche ledger.

Required mapping:

```text
tranche_id
→ entry order / fills
→ attached TP/SL pair
→ allocated filled quantity
→ realized fees
→ realized PnL
→ realized funding allocation
→ close reason
```

A Portfolio Rules count such as:

```text
max 4 SOL positions
```

means:

```text
max 4 active TriggerTrade logical tranches
```

not four raw Bybit position objects.

---

# 50. Side mapping

Canonical:

```text
direction LONG
→ entry side BUY

direction SHORT
→ entry side SELL
```

Closing order sides are derived downstream from the open position direction and configured TP/SL mechanics.

---

# 51. Decision output contract

One initial OPPORTUNITY_DECISION is emitted before the grant; one post-grant construction outcome follows only if a grant was issued. These travel over the same existing Position → Portfolio boundary. P1 and APPROVE_REJECT.md govern their exact meaning.

## Initial opportunity decision

```yaml
position_decision:
  contract_version: 5
  event_variant: OPPORTUNITY_DECISION
  event_id: string
  occurred_at: RFC3339-timestamp
  position_decision_id: string
  decision_cycle_id: string
  set_result_id: string
  symbol: string
  decision: APPROVE | REJECT
  reason_code: string
  opportunity_checks:
    configuration: PASS | FAIL | UNAVAILABLE
    set_direction: PASS | FAIL | UNAVAILABLE
    market_context: PASS | FAIL | UNAVAILABLE
    price_geometry: PASS | FAIL | UNAVAILABLE
    minimum_rr: PASS | FAIL | UNAVAILABLE | NOT_APPLICABLE
  construction_gates: NOT_YET_EVALUATED
```

## Successful post-grant construction confirmation

```yaml
position_construction_result:
  contract_version: 5
  event_variant: CONSTRUCTION_RESULT
  event_id: string
  occurred_at: RFC3339-timestamp
  position_decision_id: string
  construction_result_id: string
  capital_grant_id: string
  decision_cycle_id: string
  set_result_id: string
  symbol: string
  reason_code: string
  rule_results:
    minimum_net_edge:
      enabled: boolean
      status: PASS | FAIL | UNAVAILABLE | NOT_APPLICABLE
      configured_value:
        nullable: decimal-string
      calculated_value:
        nullable: decimal-string
      reason_code:
        nullable: string
  outcome: CONSTRUCTED
  position_plan_id: string
  tranche_id: string
  order_spec_id: string
  order_spec_digest: string
  approved_economics:
    approved_entry: decimal-string
    approved_quantity: decimal-string
    approved_leverage: decimal-string
    approved_actual_order_notional: decimal-string
    approved_actual_committed_capital: decimal-string
  numeric_policy_version: TT_NUMERIC_V1
  direction: LONG | SHORT
  order_spec_contract_version: 5
```

## Failed post-grant construction

```yaml
position_construction_result:
  contract_version: 5
  event_variant: CONSTRUCTION_RESULT
  event_id: string
  occurred_at: RFC3339-timestamp
  position_decision_id: string
  construction_result_id: string
  capital_grant_id: string
  decision_cycle_id: string
  set_result_id: string
  symbol: string
  reason_code: string
  rule_results:
    minimum_net_edge:
      enabled: boolean
      status: PASS | FAIL | UNAVAILABLE | NOT_APPLICABLE
      configured_value:
        nullable: decimal-string
      calculated_value:
        nullable: decimal-string
      reason_code:
        nullable: string
  outcome: REJECT
  failed_gates:
  - string
```

Initial REJECT has no grant and no final plan/tranche/spec. Construction REJECT has its actual received grant but no successful spec/economics. CONSTRUCTED publishes the immutable Order Spec and this confirmation durably together. No message identity is reconstructed by symbol or arrival order. Initial APPROVE never contains capital_grant_id.

---

# 52. Reason-code families

Canonical families:

```text
CONFIG_*
SET_*
ENTRY_*
SL_*
TP_*
GEOMETRY_*
CAPITAL_*
QTY_*
LEVERAGE_*
VENUE_*
RR_*
NET_EDGE_*
PORTFOLIO_*
DEPENDENCY_*
```

Baseline explicit codes include:

```text
CONFIG_INVALID
IDENTITY_INVALID
SET_DIRECTION_NONE

ENTRY_UNAVAILABLE
SL_UNAVAILABLE
TP_UNAVAILABLE

GEOMETRY_INVALID

REQUESTED_CAPITAL_INVALID
QTY_BELOW_MINIMUM
QTY_ABOVE_MAXIMUM
NOTIONAL_BELOW_MINIMUM

LEVERAGE_INVALID
LEVERAGE_ABOVE_VENUE_MAX

MISSING_EXCHANGE_FACT
MISSING_FEE_RATE

RR_BELOW_MINIMUM
NET_EDGE_BELOW_MINIMUM

DEPENDENCY_ENTRY_UNAVAILABLE
DEPENDENCY_SL_UNAVAILABLE
DEPENDENCY_TP_UNAVAILABLE

```

---

# 53. Hard gates

Baseline mandatory gates:

```text
CONFIGURATION
SET_DIRECTION
ENTRY
STOP_LOSS
TAKE_PROFIT
POSITION_GEOMETRY
CAPITAL_INPUT
QUANTITY / VENUE VALIDITY
LEVERAGE
MINIMUM_RR if enabled
MINIMUM_NET_EDGE if enabled
```

Portfolio constraints relevant to the current trade decision are supplied through `Capital and Limits`.

Position Rules does not independently re-run global portfolio policy.

It verifies only that:
- required capital/limit inputs are present;
- the current trade remains within the explicit grant supplied for this `decision_cycle_id`;
- no upstream constraint marks the decision as unavailable or blocked.

---

# 54. Configuration validation

Examples:

```text
FIXED SL mode + fixed_sl_pct missing
→ CONFIG_INVALID

DYNAMIC SL mode + fixed_sl_pct present
→ allowed but ignored / NOT_APPLICABLE field

FIXED TP mode + fixed_tp_pct missing
→ CONFIG_INVALID

minimum_rr enabled + value missing
→ CONFIG_INVALID

minimum_net_edge enabled + value missing
→ CONFIG_INVALID

leverage <= 0
→ CONFIG_INVALID
```

---

# 55. Position Rules approval semantics

Initial APPROVE means the frozen market/trade idea passed its opportunity-stage gates; it precedes Capital and Limits and says nothing about reserved capital or final quantity. CONSTRUCTED means post-grant construction and every applicable final gate succeeded and the immutable spec exists. It still is not native submit authority; only a matching Portfolio authorization supplies that.

Neither outcome proves profitability, statistical edge, a fill or native acceptance. No grant is fabricated to complete the initial decision.

---

# Part II — Dynamic Entry Methodology

This Part incorporates the approved Dynamic Limit Entry methodology into Position Rules.

Binding ownership:

```text
Dynamic Entry = Position Rules internal calculation
```

It consumes the frozen Set Market Handoff and produces the planned LIMIT entry used by the same decision cycle.

The approved calculation rules below are preserved in substance.

# 1. Purpose

This methodology converts:

```text
frozen Set market handoff
+
governed entry context
```

into either:

```text
usable planned_entry_reference
+
LIMIT POST_ONLY order price
```

or:

```text
explicit rejection / unavailable reason
```

---

# 2. Core invariant

Dynamic Limit Entry contains one Position Rules-owned price-construction phase:

```text
Structural Entry Price Generation
=
Set-consistent structural price improvement
+
ATR-normalized entry-depth admissibility
+
tick-safe Entry rounding
```

Order Lifecycle performs no local quote-based POST_ONLY marketability business gate. It serializes the immutable LIMIT + POST_ONLY order and relies on authoritative exchange acceptance/rejection/fill facts. Non-market technical incompatibility may block submission, but Entry is never altered.

It is not derived from:

```text
SL distance
TP distance
desired R:R
position size
leverage
direction score
market chase
```

---

# 3. Baseline calibration constants

```text
MIN_ENTRY_IMPROVEMENT_ATR = 0.10
MAX_ENTRY_DEVIATION_ATR   = 1.25
```

These are versioned research defaults, not validated optima.

---

# 4. Required frozen inputs

From Set handoff:

```text
direction
matched_at
market_snapshot_at
set_match_reference_price
tick_size
ATR_15m
references.levels[]
entry_context.set_family
entry_context.thesis_reference_policy
entry_context.thesis_reference_level_id
```

---

# 5. Submission-time exchange validation boundary

Dynamic Entry is computed from frozen Set geometry without a mandatory live quote. Before submit Lifecycle may validate only hard **non-market** technical compatibility under P2–P3: identifiers/schema, instrument/profile support, precision, quantity/notional limits, leverage compatibility and request construction. It must not predict POST_ONLY marketability from bid/ask or require a resting time.

The exact approved LIMIT + POST_ONLY is submitted when hard constraints permit; native rejection/cancellation and immediate accepted fills follow actual exchange evidence. No reprice, chase, Entry movement or MARKET fallback exists.

---

# 6. Supported directions

```text
LONG
SHORT
```

`NONE` is invalid for Dynamic Entry.

---

# 7. Entry order policy

Baseline:

```text
order_type = LIMIT
post_only = true
```

No automatic market fallback.

No taker fallback.

---

# 8. Approved entry reference level types

```text
SWING_LOW_15M
SWING_HIGH_15M
SWING_LOW_1H
SWING_HIGH_1H
PREVIOUS_DAY_LOW
PREVIOUS_DAY_HIGH
RANGE_LOW
RANGE_HIGH
```

No free-form level is permitted.

---

# 9. Structural entry side relative to Set match

## LONG

Candidate structural entry must improve on Set match:

```text
candidate_price < set_match_reference_price
```

## SHORT

```text
candidate_price > set_match_reference_price
```

No zero-improvement baseline entry.

---

# 10. General candidate eligibility

A candidate level must:

```text
exist in references.levels[]
available_at <= matched_at
price finite and > 0
use approved level_type
lie on the required improvement side of set_match_reference_price
```

---

# 11. Set family

Read only from:

```text
entry_context.set_family
```

Allowed:

```text
TREND_CONTINUATION
RANGE
BREAKOUT_RECLAIM
GENERIC
```

If missing/invalid:

```text
MISSING_SET_FAMILY
```

Do not infer it.

---

# 12. Thesis-reference policy

P4 applies: consume the exact Set origin_binding. Default candidate ranking below is only the existing PREFERRED/NONE calculation fallback; it never rewrites a thesis reference or resolves a missing producer role.

Read:

```text
entry_context.thesis_reference_policy
```

Allowed:

```text
REQUIRED
PREFERRED
NONE
```

---

# 13. Thesis-reference REQUIRED

If policy is `REQUIRED`, the referenced level must:

```text
exist
be available as-of matched_at
be structurally valid for direction
satisfy price-improvement side
lie within the approved entry-improvement band
```

If any fail:

```text
usable = false
reason = THESIS_ENTRY_REFERENCE_INVALID
```

No fallback.

If valid:

```text
selected entry reference = thesis reference
```

---

# 14. Thesis-reference PREFERRED

If the preferred thesis reference is valid and inside the allowed band:

```text
selected entry reference = thesis reference
```

If invalid, TOO_SHALLOW, or TOO_DEEP:

```text
warning = INVALID_THESIS_ENTRY_REFERENCE
continue with default candidate pool
```

The preferred thesis reference does not terminate the default pool when it is outside the admissibility band.

---

# 15. Thesis-reference NONE

If:

```text
policy = NONE
```

then:

```text
thesis_reference_level_id = null
```

and default hierarchy applies.

---

# 16. Entry hierarchy — TREND_CONTINUATION

LONG:

```text
1. SWING_LOW_15M
2. SWING_LOW_1H
3. PREVIOUS_DAY_LOW
4. RANGE_LOW
```

SHORT:

```text
1. SWING_HIGH_15M
2. SWING_HIGH_1H
3. PREVIOUS_DAY_HIGH
4. RANGE_HIGH
```

---

# 17. Entry hierarchy — GENERIC

Same as TREND_CONTINUATION.

---

# 18. Entry hierarchy — RANGE

LONG:

```text
1. RANGE_LOW
2. SWING_LOW_15M
3. SWING_LOW_1H
4. PREVIOUS_DAY_LOW
```

SHORT:

```text
1. RANGE_HIGH
2. SWING_HIGH_15M
3. SWING_HIGH_1H
4. PREVIOUS_DAY_HIGH
```

---

# 19. Entry hierarchy — BREAKOUT_RECLAIM

If a valid REQUIRED/PREFERRED thesis entry reference exists, Sections 13–14 govern selection.

Otherwise use GENERIC hierarchy.

No free-form breakout/reclaim price is permitted.

---

# 20. Same-type tie breakers

If multiple eligible levels share the same structural type:

```text
1. latest available_at
2. smaller improvement distance to set_match_reference_price
3. lexical level_id
```

`age_seconds` is diagnostic only.

---

# 21. Improvement distance

For each candidate:

```text
improvement_price =
abs(set_match_reference_price - candidate_price)
```

```text
improvement_pct =
100 × improvement_price / set_match_reference_price
```

```text
improvement_atr =
improvement_price / ATR_15m
```

---

# 22. Entry improvement bands

Classify:

```text
TOO_SHALLOW:
improvement_atr < 0.10

ELIGIBLE:
0.10 <= improvement_atr <= 1.25

TOO_DEEP:
improvement_atr > 1.25
```

---

# 23. Phase A — Structural Entry Price Generation

The default candidate pool is evaluated in two steps.

## Step A1 — Build and classify governed candidates

For every Set-family candidate:

```text
if basic geometry invalid:
    record ineligible
    continue

calculate improvement_atr

if improvement_atr < 0.10:
    classify TOO_SHALLOW

if 0.10 <= improvement_atr <= 1.25:
    classify ELIGIBLE

if improvement_atr > 1.25:
    classify TOO_DEEP
```

No candidate outside the admissibility band is selected.

## Step A2 — Select among ELIGIBLE candidates

Among default-pool candidates classified `ELIGIBLE`:

```text
select highest structural priority
```

Then apply same-type tie breakers.

Distance does not synthesize or move a price.

It only determines whether an existing governed structural reference is admissible.

---

# 24. TOO_SHALLOW behavior

A shallow reference does not provide meaningful baseline limit-price improvement.

Persist:

```text
too_shallow_level_ids[]
too_shallow_count
```

It remains unselected.

Other governed candidates may still be evaluated.

---

# 25. TOO_DEEP behavior

A default-pool reference beyond:

```text
1.25 ATR
```

is classified:

```text
TOO_DEEP
```

and excluded from the admissible pool.

Persist:

```text
too_deep_level_ids[]
too_deep_count
```

This does **not** automatically terminate default selection.

A different pre-existing governed reference may be selected if it independently lies inside the fixed admissibility band.

No price may be moved closer to market.

Special thesis behavior remains:

```text
REQUIRED thesis reference TOO_DEEP
→ THESIS_ENTRY_REFERENCE_INVALID

PREFERRED thesis reference TOO_DEEP
→ warning + evaluate default pool
```

---

# 26. No eligible entry reference

Use:

```text
NO_ELIGIBLE_ENTRY_REFERENCE
```

when structural reference geometry exists but zero governed references pass basic direction/improvement-side eligibility.

---

# 27. No admissible entry depth

Use:

```text
NO_ADMISSIBLE_ENTRY_DEPTH
```

when one or more references pass basic structural eligibility but **none** fall inside:

```text
0.10 <= improvement_atr <= 1.25
```

This includes default pools containing only TOO_SHALLOW and/or TOO_DEEP candidates.

---

# 28. No ATR-only fallback

Do not synthesize:

```text
entry = set_match_reference_price ± K × ATR
```

when no structural entry reference is usable.

Baseline has no ATR-only entry fallback.

---

# 29. Raw entry price

For the selected reference:

```text
raw_entry_price = selected_reference_price
```

No extra offset is added in baseline v0.2.2.

The structural level itself is the limit-entry anchor.

---

# 30. Tick rounding

Use decimal-safe arithmetic.

## LONG buy-limit

Round DOWN:

```text
rounded_entry_price =
floor(raw_entry_price / tick_size)
× tick_size
```

## SHORT sell-limit

Round UP:

```text
rounded_entry_price =
ceil(raw_entry_price / tick_size)
× tick_size
```

This preserves requested price improvement.

---

# 31. Post-rounding improvement validation

Recompute:

```text
rounded_improvement_atr =
abs(set_match_reference_price - rounded_entry_price)
/
ATR_15m
```

Require:

```text
0.10 <= rounded_improvement_atr <= 1.25
```

If:

```text
rounded_improvement_atr < 0.10
```

return:

```text
ENTRY_TOO_SHALLOW_AFTER_ROUNDING
```

If:

```text
rounded_improvement_atr > 1.25
```

return:

```text
ENTRY_TOO_DEEP_AFTER_ROUNDING
```

---

# 32. Live Placement Validation — REMOVED

The former live quote / gap-expansion / crossing phase is removed from the canonical baseline. It must not be implemented. Structural Entry ends after frozen-context selection, ATR admissibility, and tick normalization.

Exchange POST_ONLY behavior belongs to Order Lifecycle / exchange facts and never changes the approved Entry.

---


# 33. Final Entry output

After structural selection, ATR admissibility, and tick rounding pass:

```text
planned_entry_reference = rounded_entry_price
limit_order_price = rounded_entry_price
order_type = LIMIT
post_only = true
```

The Entry price is frozen for this Position Rules decision cycle.

Order Lifecycle submits this exact `LIMIT + POST_ONLY` price after matching Order Spec with Submit Authorized and passing non-market technical compatibility checks. Exchange acceptance/rejection is authoritative. No local quote-based placement gate exists.

---

# 39. Planned entry reference

If all checks pass:

```text
planned_entry_reference =
rounded_entry_price
```

and:

```text
limit_order_price =
rounded_entry_price
```

For baseline v0.2.2 these are identical.

---

# 40. No chase invariant

If the market has moved away:

```text
do not move limit toward market
do not cross spread
do not switch to MARKET
```

Dynamic Entry either returns its precomputed valid limit price or rejects.

Any later cancellation behavior belongs to Order Lifecycle. Automatic replace/reprice is disabled in the baseline.

---

# 41. Creation-time vs order-lifecycle boundary

Dynamic Entry owns:

```text
reference selection
price calculation
tick rounding
frozen-reference availability as-of matched_at
structural geometry and tick validation
```

Order Lifecycle owns:

```text
submit
hard non-market technical compatibility (P2)
cancel execution
partial fill
remaining quantity handling
reconciliation
close processing
```

Order Lifecycle does not perform market analysis, structure refresh, or automatic repricing.

---

# 42. Relation to SL and TP

Correct downstream sequence:

```text
Dynamic Entry
→ planned_entry_reference

Dynamic SL
→ calculate against planned entry

Dynamic TP
→ calculate against planned entry

Position Rules / Position Plan Feasibility
→ evaluate Entry + SL + TP together
```

Dynamic Entry does not change itself to improve R:R.

---

# 43. Context excluded from baseline entry price

Do not directly use:

```text
direction score
BTC context
market breadth
session
aggressive flow
OI
funding
premium
activity
liquidity
SL
TP
desired R:R
position size
leverage
portfolio allocation
```

These may be retained for diagnostics only.

---

# 44. Warning codes

Canonical:

```text
REFERENCE_1H_FALLBACK
PREVIOUS_DAY_ENTRY_USED
RANGE_ENTRY_USED
INVALID_THESIS_ENTRY_REFERENCE
MULTIPLE_ELIGIBLE_ENTRY_REFERENCES
```

---

# 45. Reason codes

Canonical:

```text
AVAILABLE
NO_ENTRY_SIDE_GEOMETRY
NO_ELIGIBLE_ENTRY_REFERENCE
NO_ADMISSIBLE_ENTRY_DEPTH
THESIS_ENTRY_REFERENCE_INVALID
MISSING_ATR
MISSING_TICK_SIZE
MISSING_SET_MATCH_REFERENCE
MISSING_SET_FAMILY
MISSING_THESIS_REFERENCE_POLICY
ENTRY_TOO_SHALLOW_AFTER_ROUNDING
ENTRY_TOO_DEEP_AFTER_ROUNDING
ROUNDING_ERROR
```

---

# 46. Missing-input handling

```text
ATR_15m missing or <= 0
→ MISSING_ATR

tick_size missing or <= 0
→ MISSING_TICK_SIZE

set_match_reference_price missing or <= 0
→ MISSING_SET_MATCH_REFERENCE

set_family missing/invalid
→ MISSING_SET_FAMILY

thesis policy missing/invalid
→ MISSING_THESIS_REFERENCE_POLICY

```

Missing values are never zero-filled.

---

# 47. Dynamic Entry output contract

```yaml
dynamic_entry:
  methodology:
    id: TT-METH-018
    version: 0.2.2

  snapshot:
    set_result_id:
    matched_at:
    market_snapshot_at:
    direction:
    set_match_reference_price:

  entry_context:
    set_family:
    thesis_reference_policy:
    thesis_reference_level_id:

  reference_selection:
    candidate_level_ids_before_selection: []
    ineligible_level_ids_with_reason: []
    too_shallow_level_ids: []
    too_shallow_count:
    too_deep_level_ids: []
    too_deep_count:
    eligible_entry_level_ids: []
    selected_level_id:
    selected_level_type:
    selected_reference_price:
    selected_reference_timeframe:
    selected_reference_available_at:
    selected_reference_age_seconds:
    selected_priority_rank:
    alternative_reference_level_ids: []

  distance:
    raw_improvement:
      price:
      pct:
      atr_units:
    rounded_improvement:
      price:
      pct:
      atr_units:
    min_improvement_atr: 0.10
    max_deviation_atr: 1.25

  execution:
    order_type: LIMIT
    post_only: true
    raw_entry_price:
    rounded_entry_price:
    limit_order_price:

  feasibility:
    usable:
    reason:

  warnings: []
```

---

# 48. LONG algorithm

```text
PHASE A — PRICE GENERATION

M = set_match_reference_price
A = ATR_15m

validate REQUIRED/PREFERRED/NONE thesis policy

build LONG default structural pool using:
hierarchy_for(entry_context.set_family)

where the canonical family tables in Sections 16–19 are authoritative; for RANGE this starts with RANGE_LOW.

for every basic-valid reference:
    require reference.price < M
    improvement_atr = (M - reference.price) / A

    if improvement_atr < 0.10:
        classify TOO_SHALLOW

    elif improvement_atr <= 1.25:
        classify ELIGIBLE

    else:
        classify TOO_DEEP

REQUIRED thesis reference:
    if not ELIGIBLE:
        THESIS_ENTRY_REFERENCE_INVALID
    else:
        select it

PREFERRED thesis reference:
    if ELIGIBLE:
        select it
    else:
        warning + use default ELIGIBLE pool

default pool:
    if zero basic-valid refs:
        NO_ELIGIBLE_ENTRY_REFERENCE

    if zero ELIGIBLE refs:
        NO_ADMISSIBLE_ENTRY_DEPTH

    select highest structural-priority ELIGIBLE ref

raw_entry = selected reference price
rounded_entry = floor(raw_entry / tick) × tick

recompute rounded improvement:
    < 0.10 → ENTRY_TOO_SHALLOW_AFTER_ROUNDING
    > 1.25 → ENTRY_TOO_DEEP_AFTER_ROUNDING

EMIT IMMUTABLE ENTRY

planned_entry_reference = rounded_entry
limit_order_price = rounded_entry
order_type = LIMIT
post_only = true
AVAILABLE

No current bid/ask, gap-expansion, crossing, or minimum-resting validation is performed by Position Rules.
```
---

# 49. SHORT algorithm

```text
PHASE A — PRICE GENERATION

M = set_match_reference_price
A = ATR_15m

validate REQUIRED/PREFERRED/NONE thesis policy

build SHORT default structural pool using:
hierarchy_for(entry_context.set_family)

where the canonical family tables in Sections 16–19 are authoritative; for RANGE this starts with RANGE_HIGH.

for every basic-valid reference:
    require reference.price > M
    improvement_atr = (reference.price - M) / A

    if improvement_atr < 0.10:
        classify TOO_SHALLOW

    elif improvement_atr <= 1.25:
        classify ELIGIBLE

    else:
        classify TOO_DEEP

REQUIRED thesis reference:
    if not ELIGIBLE:
        THESIS_ENTRY_REFERENCE_INVALID
    else:
        select it

PREFERRED thesis reference:
    if ELIGIBLE:
        select it
    else:
        warning + use default ELIGIBLE pool

default pool:
    if zero basic-valid refs:
        NO_ELIGIBLE_ENTRY_REFERENCE

    if zero ELIGIBLE refs:
        NO_ADMISSIBLE_ENTRY_DEPTH

    select highest structural-priority ELIGIBLE ref

raw_entry = selected reference price
rounded_entry = ceil(raw_entry / tick) × tick

recompute rounded improvement:
    < 0.10 → ENTRY_TOO_SHALLOW_AFTER_ROUNDING
    > 1.25 → ENTRY_TOO_DEEP_AFTER_ROUNDING

EMIT IMMUTABLE ENTRY

planned_entry_reference = rounded_entry
limit_order_price = rounded_entry
order_type = LIMIT
post_only = true
AVAILABLE

No current bid/ask, gap-expansion, crossing, or minimum-resting validation is performed by Position Rules.
```
---

# 50. Research parameters

Versioned baseline candidates:

```text
MIN_ENTRY_IMPROVEMENT_ATR = 0.10
MAX_ENTRY_DEVIATION_ATR   = 1.25
```

Structural hierarchy must also be tested by Set family.

Do not run unrestricted combinatorial optimization.

---

# 51. Required research reporting

At minimum:

```text
LONG separately
SHORT separately
coin
Set family
selected entry reference type
entry improvement ATR
entry improvement %
fill rate
time to fill
missed-trade rate
TOO_SHALLOW skip frequency
too-deep candidate frequency
ENTRY_TOO_DEEP_AFTER_ROUNDING frequency
native POST_ONLY rejection/cancellation frequency
hard non-market technical incompatibility frequency
entry-reference age
eventual expectancy by entry-distance band
adverse excursion after fill
favorable excursion after fill
```

---

# Part III — Dynamic Stop Loss Methodology

This Part incorporates the approved Dynamic Stop Loss methodology into Position Rules.

Binding ownership:

```text
Dynamic Stop Loss = Position Rules internal calculation
```

It consumes the planned Entry plus frozen Set `sl_context` / Market Handoff.

The approved calculation rules below are preserved in substance.

# 1. Purpose

This methodology converts:

```text
frozen Set market handoff
+
planned_entry_reference
+
active Position Rules SL configuration
```

into either:

```text
usable Dynamic SL candidate
```

or:

```text
explicit rejection / unavailable reason
```

---

# 2. Core invariant

Dynamic SL is:

```text
governed market invalidation
+
ATR noise buffer
+
minimum technical distance
+
maximum feasibility constraint
+
outward tick rounding
```

It is not derived from desired reward/risk, leverage, position size, or conviction.

If the structurally correct stop is too wide:

```text
reject the Position Plan
```

Do not move the stop inward.

---

# 3. Baseline calibration constants

```text
BUFFER_ATR_MULTIPLIER = 0.20
MIN_DISTANCE_ATR      = 0.50
MAX_DISTANCE_ATR      = 2.00
CORROBORATION_DISTANCE_ATR = 0.25
```

These are calibration defaults for research, not validated optima.

---

# 4. Required inputs

From Set handoff:

```text
direction
matched_at
market_snapshot_at
set_match_reference_price
tick_size
ATR_15m
references.levels[]
sl_context.set_family
sl_context.thesis_reference_policy
sl_context.thesis_reference_level_id
```

From Position Rules:

```text
planned_entry_reference
stop_loss_mode = DYNAMIC
```

---

# 5. Supported directions

```text
LONG
SHORT
```

`NONE` is invalid for SL creation.

---

# 6. Approved level types

```text
SWING_LOW_15M
SWING_HIGH_15M
SWING_LOW_1H
SWING_HIGH_1H
PREVIOUS_DAY_LOW
PREVIOUS_DAY_HIGH
RANGE_LOW
RANGE_HIGH
```

---

# 7. Candidate eligibility must be recomputed vs planned entry

The Set's cached side (`relative_position.side` in calculation notation, `relative_position` in the wire projection defined by Set) is relative to the Set-match reference and is audit-only for Dynamic SL selection.

Final adverse-side eligibility is recomputed from the actual:

```text
planned_entry_reference
```

with one-tick exclusion zone.

## LONG

Eligible only if:

```text
level.price < planned_entry_reference - tick_size
```

## SHORT

Eligible only if:

```text
level.price > planned_entry_reference + tick_size
```

A level within ±1 tick of planned entry is not eligible.

---

# 8. General level eligibility

A candidate level must satisfy all:

```text
level exists in references.levels[]
available_at <= matched_at
price is finite and > 0
approved level_type
correct adverse-side geometry vs planned_entry_reference
```

No synthetic level is permitted.

---

# 9. Set family

Read only from:

```text
sl_context.set_family
```

Allowed:

```text
TREND_CONTINUATION
RANGE
BREAKOUT_RECLAIM
GENERIC
```

If missing or invalid:

```text
MISSING_SET_FAMILY
```

Do not infer it.

---

# 10. Thesis-reference policy

P4 applies: consume the exact Set origin_binding. Default candidate ranking below is only the existing PREFERRED/NONE calculation fallback; it never rewrites a thesis reference or resolves a missing producer role.

Read:

```text
sl_context.thesis_reference_policy
```

Allowed:

```text
REQUIRED
PREFERRED
NONE
```

---

# 11. Thesis-reference REQUIRED

If:

```text
policy = REQUIRED
```

then `thesis_reference_level_id` must:

```text
exist
reference an existing canonical level
be available as-of matched_at
be adverse-side eligible vs planned entry
```

If any fail:

```text
usable = false
reason = THESIS_REFERENCE_INVALID
```

No default hierarchy fallback is allowed.

If valid:

```text
selected reference = thesis reference
```

---

# 12. Thesis-reference PREFERRED

If:

```text
policy = PREFERRED
```

and the thesis reference is eligible:

```text
selected reference = thesis reference
```

If invalid/unavailable:

```text
add warning = INVALID_THESIS_REFERENCE_OVERRIDE
continue to default hierarchy
```

---

# 13. Thesis-reference NONE

If:

```text
policy = NONE
```

then:

```text
thesis_reference_level_id must be null
```

and default reference ranking is used.

If a non-null ID is supplied with `NONE`:

```text
warning = UNUSED_THESIS_REFERENCE_ID
```

---

# 14. Reference priority — TREND_CONTINUATION

LONG:

```text
1. SWING_LOW_15M
2. SWING_LOW_1H
3. PREVIOUS_DAY_LOW
4. RANGE_LOW
```

SHORT:

```text
1. SWING_HIGH_15M
2. SWING_HIGH_1H
3. PREVIOUS_DAY_HIGH
4. RANGE_HIGH
```

---

# 15. Reference priority — RANGE

LONG:

```text
1. RANGE_LOW
2. SWING_LOW_15M
3. SWING_LOW_1H
4. PREVIOUS_DAY_LOW
```

SHORT:

```text
1. RANGE_HIGH
2. SWING_HIGH_15M
3. SWING_HIGH_1H
4. PREVIOUS_DAY_HIGH
```

---

# 16. Reference priority — BREAKOUT_RECLAIM

If policy is REQUIRED/PREFERRED with a valid thesis reference, Sections 11–12 control selection.

Otherwise default:

LONG:

```text
1. SWING_LOW_15M
2. SWING_LOW_1H
3. PREVIOUS_DAY_LOW
4. RANGE_LOW
```

SHORT:

```text
1. SWING_HIGH_15M
2. SWING_HIGH_1H
3. PREVIOUS_DAY_HIGH
4. RANGE_HIGH
```

No free-form breakout reference is created.

---

# 17. Reference priority — GENERIC

Same as TREND_CONTINUATION.

---

# 18. Ranking within same priority type

If multiple eligible levels share the same level type:

```text
1. latest available_at
2. smaller adverse-side distance to planned_entry_reference
3. lexical level_id
```

`age_seconds` is diagnostic only and is not a separate ranking criterion because it is derived from `available_at`.

---

# 19. Candidate audit trail

Before selection persist:

```text
candidate_level_ids_before_ranking[]
ineligible_level_ids_with_reason[]
```

For selected reference also persist:

```text
reference_priority_rank
```

---

# 20. Corroborating levels

Eligible adverse-side levels corroborate selected reference if:

```text
abs(other_level.price - selected_reference.price)
/
ATR_15m
<= 0.25
```

Exclude the selected level itself.

Output:

```text
corroborating_level_ids[]
```

If non-empty:

```text
warning = MULTIPLE_NEARBY_LEVELS
```

This is diagnostic only.

---

# 21. Structural invalidation anchor

The selected reference price is the invalidation anchor.

The stop is placed beyond it.

---

# 22. ATR buffer

```text
buffer_price =
0.20 × ATR_15m
```

LONG:

```text
raw_stop =
selected_reference_price - buffer_price
```

SHORT:

```text
raw_stop =
selected_reference_price + buffer_price
```

---

# 23. Minimum technical distance

```text
minimum_distance_price =
0.50 × ATR_15m
```

LONG:

```text
minimum_stop =
planned_entry_reference - minimum_distance_price

adjusted_stop =
min(raw_stop, minimum_stop)
```

SHORT:

```text
minimum_stop =
planned_entry_reference + minimum_distance_price

adjusted_stop =
max(raw_stop, minimum_stop)
```

Persist:

```text
minimum_distance_adjustment_applied = true | false
```

---

# 24. Pre-rounding risk distance

LONG:

```text
pre_rounding_risk_price =
planned_entry_reference - adjusted_stop
```

SHORT:

```text
pre_rounding_risk_price =
adjusted_stop - planned_entry_reference
```

Then:

```text
pre_rounding_risk_atr =
pre_rounding_risk_price / ATR_15m
```

If:

```text
pre_rounding_risk_atr > 2.00
```

return:

```text
SL_TOO_WIDE
```

No alternative weaker reference retry.

---

# 25. No weaker-reference retry

Once the structurally highest-priority eligible reference is selected:

```text
calculate stop
→ validate
```

If too wide:

```text
reject
```

Do not choose a lower-priority reference solely to make the trade cheaper.

---

# 26. No ATR-only fallback

If no eligible governed adverse-side reference exists:

```text
NO_ELIGIBLE_REFERENCE
```

No:

```text
entry ± K × ATR
```

fallback exists in v0.2.

---

# 27. Tick rounding

Use decimal-safe arithmetic.

LONG:

```text
rounded_stop =
floor(adjusted_stop / tick_size)
× tick_size
```

SHORT:

```text
rounded_stop =
ceil(adjusted_stop / tick_size)
× tick_size
```

Rounding is always outward.

---

# 28. Post-rounding structural checks

LONG:

```text
rounded_stop < selected_reference_price
rounded_stop < planned_entry_reference
```

SHORT:

```text
rounded_stop > selected_reference_price
rounded_stop > planned_entry_reference
```

Violation:

```text
ROUNDING_ERROR
```

---

# 29. Post-rounding risk distance

Recompute from rounded stop.

LONG:

```text
post_rounding_risk_price =
planned_entry_reference - rounded_stop
```

SHORT:

```text
post_rounding_risk_price =
rounded_stop - planned_entry_reference
```

Then:

```text
post_rounding_risk_atr =
post_rounding_risk_price / ATR_15m
```

Final feasibility rule:

```text
if post_rounding_risk_atr > 2.00:
    usable = false
    reason = SL_TOO_WIDE
```

Thus tick rounding cannot silently push the final stop beyond the maximum risk-distance constraint.

---

# 30. Planned-entry geometry validity

Any selected reference must satisfy planned-entry adverse-side rules from Section 7.

If a REQUIRED thesis reference fails:

```text
THESIS_REFERENCE_INVALID
```

If a default/PREFERRED fallback selection yields no eligible levels:

```text
NO_ELIGIBLE_REFERENCE
```

---

# 31. Missing inputs

```text
ATR_15m missing or <= 0
→ MISSING_ATR

tick_size missing or <= 0
→ MISSING_TICK_SIZE

planned_entry_reference missing or <= 0
→ MISSING_ENTRY_REFERENCE

set_family missing/invalid
→ MISSING_SET_FAMILY

thesis policy missing/invalid
→ MISSING_THESIS_REFERENCE_POLICY

no adverse-side geometry capability
→ NO_ADVERSE_SIDE_GEOMETRY
```

Missing values are never zero-filled.

---

# 32. Entry drift after Set match

The Set handoff remains frozen.

If the planned limit entry moves relative to frozen geometry:

```text
recompute candidate adverse-side eligibility vs planned entry
```

Do not recompute the Set.

If no eligible geometry remains:

```text
NO_ELIGIBLE_REFERENCE
```

or for REQUIRED thesis reference:

```text
THESIS_REFERENCE_INVALID
```

---

# 33. Context excluded from baseline stop price

Do not use directly:

```text
direction_score
direction_band
BTC context
aggressive flow
OI
funding
premium
market breadth
session context
position size
leverage
desired R:R
TP target
fees
spread
slippage
```

These may be retained for diagnostics or downstream feasibility only.

---

# 34. Warning codes

```text
REFERENCE_1H_FALLBACK
PREVIOUS_DAY_FALLBACK
RANGE_REFERENCE_USED
INVALID_THESIS_REFERENCE_OVERRIDE
UNUSED_THESIS_REFERENCE_ID
MULTIPLE_NEARBY_LEVELS
```

No `REFERENCE_OLD` warning is emitted because no governed age threshold exists.

---

# 35. Reason codes

```text
AVAILABLE
NO_ADVERSE_SIDE_GEOMETRY
NO_ELIGIBLE_REFERENCE
THESIS_REFERENCE_INVALID
MISSING_ATR
MISSING_TICK_SIZE
MISSING_ENTRY_REFERENCE
MISSING_SET_FAMILY
MISSING_THESIS_REFERENCE_POLICY
SL_TOO_WIDE
ROUNDING_ERROR
```

---

# 36. Output contract

```yaml
dynamic_sl:
  methodology:
    id: TT-METH-016
    version: 0.2.1

  snapshot:
    set_result_id:
    matched_at:
    market_snapshot_at:
    direction:
    planned_entry_reference:

  thesis_context:
    set_family:
    thesis_reference_policy:
    thesis_reference_level_id:

  reference_selection:
    candidate_level_ids_before_ranking: []
    ineligible_level_ids_with_reason: []
    thesis_reference_override_used:
    selected_level_id:
    selected_level_type:
    selected_reference_price:
    selected_reference_timeframe:
    selected_reference_available_at:
    selected_reference_age_seconds:
    reference_priority_rank:
    corroborating_level_ids: []

  volatility:
    atr_15m:
    buffer_atr_multiplier: 0.20
    buffer_price:
    min_distance_atr_multiplier: 0.50
    min_distance_price:
    max_distance_atr: 2.00

  calculation:
    raw_stop_price:
    minimum_stop_price:
    minimum_distance_adjustment_applied:
    adjusted_stop_price:
    rounded_stop_price:

  risk_distance:
    pre_rounding:
      price:
      atr_units:
    post_rounding:
      price:
      pct:
      atr_units:

  feasibility:
    usable:
    reason:

  fallback_used: false
  warnings: []
```

---

# 37. LONG formula

```text
R = selected adverse reference
A = ATR_15m
E = planned entry

raw_stop = R - 0.20A
minimum_stop = E - 0.50A
adjusted_stop = min(raw_stop, minimum_stop)

pre_risk_atr = (E - adjusted_stop)/A
if pre_risk_atr > 2.0:
    reject

rounded_stop = floor(adjusted_stop/tick)×tick

post_risk_atr = (E - rounded_stop)/A
if post_risk_atr > 2.0:
    reject
```

---

# 38. SHORT formula

```text
R = selected adverse reference
A = ATR_15m
E = planned entry

raw_stop = R + 0.20A
minimum_stop = E + 0.50A
adjusted_stop = max(raw_stop, minimum_stop)

pre_risk_atr = (adjusted_stop - E)/A
if pre_risk_atr > 2.0:
    reject

rounded_stop = ceil(adjusted_stop/tick)×tick

post_risk_atr = (rounded_stop - E)/A
if post_risk_atr > 2.0:
    reject
```

---

# 39. Research parameters

Fixed versioned defaults for v0.2:

```text
BUFFER = 0.20 ATR
MIN_DISTANCE = 0.50 ATR
MAX_DISTANCE = 2.00 ATR
CORROBORATION = 0.25 ATR
```

Research must test sensitivity rather than intuition-retune before evidence.

---

# Part IV — Dynamic Take Profit Methodology

This Part incorporates the approved Dynamic Take Profit methodology into Position Rules.

Binding ownership:

```text
Dynamic Take Profit = Position Rules internal calculation
```

It consumes the planned Entry plus frozen Set `tp_context` / Market Handoff.

The approved calculation rules below are preserved in substance.

# 1. Purpose

This methodology converts:

```text
frozen Set market handoff
+
planned_entry_reference
+
active Position Rules TP configuration
```

into either:

```text
usable Dynamic TP candidate
```

or:

```text
explicit rejection / unavailable reason
```

---

# 2. Core invariant

Dynamic TP is:

```text
governed favorable-side structural target
+
ATR-normalized reachability
+
tick-normalized realizability
```

It is not derived from:

```text
SL distance
fixed R:R
desired profit %
position size
leverage
direction score
```

R:R is evaluated later in Joint TP/SL Feasibility.

---

# 3. Baseline calibration constants

```text
MIN_TP_DISTANCE_ATR = 0.75
MAX_TP_DISTANCE_ATR = 4.00
```

These are calibration defaults for research, not validated optima.

---

# 4. Required inputs

From Set handoff:

```text
direction
matched_at
market_snapshot_at
tick_size
ATR_15m
references.levels[]
tp_context.set_family
tp_context.thesis_reference_policy
tp_context.thesis_reference_level_id
```

From Position Rules:

```text
planned_entry_reference
take_profit_mode = DYNAMIC
```

---

# 5. Supported directions

```text
LONG
SHORT
```

`NONE` is invalid for Dynamic TP creation.

---

# 6. Approved target level types

```text
SWING_HIGH_15M
SWING_LOW_15M
SWING_HIGH_1H
SWING_LOW_1H
PREVIOUS_DAY_HIGH
PREVIOUS_DAY_LOW
RANGE_HIGH
RANGE_LOW
```

---

# 7. Favorable-side eligibility is recomputed vs planned entry

The cached Set side (`relative_position.side` in calculation notation, `relative_position` in the wire projection defined by Set) is relative to Set-match price and is audit-only for final TP selection.

## LONG

A target level is favorable-side eligible only if:

```text
level.price > planned_entry_reference + tick_size
```

## SHORT

Eligible only if:

```text
level.price < planned_entry_reference - tick_size
```

A level within ±1 tick of planned entry is ineligible.

---

# 8. General target eligibility

A level must satisfy:

```text
exists in references.levels[]
available_at <= matched_at
price finite and > 0
approved level_type
correct favorable-side geometry vs planned_entry_reference
```

No synthetic target may be invented.

---

# 9. Set family

Read only from:

```text
tp_context.set_family
```

Allowed:

```text
TREND_CONTINUATION
RANGE
BREAKOUT_RECLAIM
GENERIC
```

If missing/invalid:

```text
MISSING_SET_FAMILY
```

No inference is allowed.

---

# 10. Thesis-reference policy

P4 applies: consume the exact Set origin_binding. Default candidate ranking below is only the existing PREFERRED/NONE calculation fallback; it never rewrites a thesis reference or resolves a missing producer role.

Read:

```text
tp_context.thesis_reference_policy
```

Allowed:

```text
REQUIRED
PREFERRED
NONE
```

---

# 11. Thesis-reference REQUIRED

If policy is:

```text
REQUIRED
```

then the referenced level must:

```text
exist
be available as-of matched_at
be favorable-side eligible vs planned entry
lie within the approved reachability band
```

If not:

```text
usable = false
reason = THESIS_REFERENCE_INVALID
```

No fallback.

If valid:

```text
selected target = thesis reference
```

---

# 12. Thesis-reference PREFERRED

If PREFERRED target is fully eligible and reachable:

```text
selected target = thesis reference
```

If invalid or outside reachability band:

```text
warning = INVALID_THESIS_REFERENCE_OVERRIDE
continue with default target hierarchy
```

---

# 13. Thesis-reference NONE

If:

```text
policy = NONE
```

then:

```text
thesis_reference_level_id = null
```

and default hierarchy applies.

---

# 14. Target hierarchy — TREND_CONTINUATION

LONG:

```text
1. SWING_HIGH_15M
2. SWING_HIGH_1H
3. PREVIOUS_DAY_HIGH
4. RANGE_HIGH
```

SHORT:

```text
1. SWING_LOW_15M
2. SWING_LOW_1H
3. PREVIOUS_DAY_LOW
4. RANGE_LOW
```

This is a timeframe-first baseline prior.

---

# 15. Target hierarchy — GENERIC

Same as TREND_CONTINUATION.

---

# 16. Target hierarchy — RANGE

LONG:

```text
1. RANGE_HIGH
2. SWING_HIGH_15M
3. SWING_HIGH_1H
4. PREVIOUS_DAY_HIGH
```

SHORT:

```text
1. RANGE_LOW
2. SWING_LOW_15M
3. SWING_LOW_1H
4. PREVIOUS_DAY_LOW
```

---

# 17. Target hierarchy — BREAKOUT_RECLAIM

If a valid REQUIRED/PREFERRED thesis target exists, Sections 11–12 control selection.

Otherwise use GENERIC hierarchy.

No free-form breakout target is permitted.

---

# 18. Ranking within same priority type

If multiple eligible levels share the same level type:

```text
1. latest available_at
2. smaller favorable-side distance to planned_entry_reference
3. lexical level_id
```

`age_seconds` remains diagnostic only.

---

# 19. Distance calculation

For every structurally eligible favorable-side level:

```text
distance_price =
abs(level.price - planned_entry_reference)
```

```text
distance_pct =
100 × distance_price / planned_entry_reference
```

```text
distance_atr =
distance_price / ATR_15m
```

---

# 20. Reachability bands

Classify every candidate:

```text
TOO_CLOSE:
distance_atr < 0.75

ELIGIBLE:
0.75 <= distance_atr <= 4.00

TOO_FAR:
distance_atr > 4.00
```

---

# 21. Sequential structural selection rule

Target selection must preserve structural priority.

The canonical sequence is:

```text
1. construct the Set-family structural hierarchy
2. evaluate candidates in priority order
3. for each candidate:

   if basic geometry is invalid:
       record ineligible
       continue

   calculate distance_atr

   if distance_atr < 0.75:
       record TOO_CLOSE
       continue

   if 0.75 <= distance_atr <= 4.00:
       select target
       stop

   if distance_atr > 4.00:
       record TOO_FAR
       terminate selection
       reject Dynamic TP
```

Distance does not globally reorder structural targets.

---

# 22. Too-close target behavior

If a higher-priority target is:

```text
TOO_CLOSE
```

it is treated as a nearby intermediate obstacle rather than the terminal TP.

Canonical behavior:

```text
record target in too_close_level_ids[]
increment too_close_skipped_count
continue to next structural target
```

This is the only baseline distance condition that permits continuing down the hierarchy.

---

# 23. Too-far target behavior

If the next structurally valid target satisfies:

```text
distance_atr > 4.00
```

the baseline selection terminates immediately.

Return:

```text
usable = false
reason = TARGET_TOO_FAR
```

Persist:

```text
selection_terminated_by_too_far = true
first_too_far_level_id
first_too_far_distance_atr
```

Do not select a lower-priority target after a TOO_FAR termination.

Reason:

Feasibility may reject the structural target, but must not silently replace the trade thesis with a weaker target.

---

# 24. Failure-reason precedence for target availability

Use mutually distinct outcomes.

## `NO_FAVORABLE_SIDE_GEOMETRY`

Use when the upstream favorable-side geometry capability is unavailable.

## `NO_ELIGIBLE_REFERENCE`

Use when governed reference geometry exists, but **zero** governed levels pass the basic favorable-side eligibility rules relative to `planned_entry_reference`.

## `NO_REACHABLE_TARGET`

Use when at least one governed level passes basic favorable-side eligibility, but the structural hierarchy is exhausted after all traversed candidates are classified `TOO_CLOSE`, with no `ELIGIBLE` or `TOO_FAR` candidate encountered.

## `TARGET_TOO_FAR`

Use when, after any allowed `TOO_CLOSE` skips, the next structurally traversed candidate has:

```text
distance_atr > 4.00
```

Selection terminates immediately.

Reason precedence:

```text
missing required primitive
→ NO_FAVORABLE_SIDE_GEOMETRY if capability absent
→ NO_ELIGIBLE_REFERENCE if zero basic eligible references
→ traverse structural hierarchy
   → TOO_CLOSE may continue
   → ELIGIBLE selects
   → TOO_FAR terminates as TARGET_TOO_FAR
→ hierarchy exhausted after TOO_CLOSE only
   → NO_REACHABLE_TARGET
```

---

# 25. No ATR-only fallback

Do not synthesize:

```text
TP = entry ± K × ATR
```

when no structural target is reachable.

Baseline v0.2.2 has no ATR-only fallback.

---

# 26. No SL-derived target

Do not derive:

```text
TP = entry + N × SL_distance
```

or equivalent.

SL output may be used later only by:

```text
Joint TP/SL Feasibility
```

---

# 27. Candidate audit trail

Persist:

```text
candidate_level_ids_before_distance_filter[]
ineligible_level_ids_with_reason[]
too_close_level_ids[]
too_close_skipped_count
too_far_level_ids[]
selection_terminated_by_too_far
first_too_far_level_id
first_too_far_distance_atr
eligible_target_level_ids[]
selected_target_priority_rank
alternative_eligible_target_level_ids[]
```

---

# 28. Target selection

Selection is sequential, not global.

Canonical behavior:

```text
iterate structural hierarchy in priority order

TOO_CLOSE → continue
ELIGIBLE  → select and stop
TOO_FAR   → reject and stop
```

If a target is selected, lower-priority ELIGIBLE levels may still be persisted as diagnostic alternatives only if they are evaluated separately for audit after the primary decision.

They must not affect the primary selection outcome.

---

# 29. Tick rounding

TP is rounded inward toward realizability, never beyond the structural target.

## LONG

```text
rounded_tp =
floor(selected_target_price / tick_size)
× tick_size
```

## SHORT

```text
rounded_tp =
ceil(selected_target_price / tick_size)
× tick_size
```

Use decimal-safe arithmetic.

---

# 30. Post-rounding geometry validation

## LONG

Require:

```text
rounded_tp > planned_entry_reference
rounded_tp <= selected_target_price
```

## SHORT

Require:

```text
rounded_tp < planned_entry_reference
rounded_tp >= selected_target_price
```

Violation:

```text
ROUNDING_ERROR
```

---

# 31. Post-rounding minimum-distance validation

Recompute:

```text
rounded_distance_atr =
abs(rounded_tp - planned_entry_reference) / ATR_15m
```

If:

```text
rounded_distance_atr < 0.75
```

return:

```text
TARGET_TOO_CLOSE_AFTER_ROUNDING
```

---

# 32. Post-rounding maximum-distance validation

Because inward rounding cannot increase target distance beyond the raw structural target, the max-distance rule normally remains satisfied.

Still recompute and require:

```text
rounded_distance_atr <= 4.00
```

If violated due to arithmetic/precision inconsistency:

```text
ROUNDING_ERROR
```

---

# 33. Minimum target distance vs economic profitability

`0.75 ATR` is a reachability/meaningfulness candidate, not a guarantee of profitable net economics.

Fees/spread/slippage are checked later.

Do not move TP for costs inside this methodology.

---

# 34. Activity / liquidity

Inputs may be logged:

```text
TIME_OF_DAY_RELATIVE_TURNOVER
RELATIVE_TURNOVER
TURNOVER_LIQUIDITY
TRADE_INTENSITY
```

but do not modify baseline TP.

---

# 35. Flow / OI / funding / premium

Do not modify baseline target price.

Context-only for research.

---

# 36. BTC / relative / breadth

Do not alter baseline TP.

Direction already incorporates BTC context.

Avoid double counting.

---

# 37. Direction score

Explicitly excluded from baseline target selection.

No:

```text
stronger score → farther target
```

rule exists in v0.2.2.

---

# 38. Session context

No baseline session-dependent TP adjustment.

No forced TP compression near arbitrary UTC/session boundaries.

---

# 39. LONG/SHORT symmetry

Baseline uses identical:

```text
MIN_TP_DISTANCE_ATR = 0.75
MAX_TP_DISTANCE_ATR = 4.00
```

for LONG and SHORT.

Research must report separately.

---

# 40. Partial TP / multi-target boundary

Baseline produces one primary TP.

Do not implement partial exits here.

Preserve:

```text
alternative_eligible_target_level_ids[]
```

for future TP1/TP2 methodology.

---

# 41. Warning codes

Canonical:

```text
REFERENCE_1H_FALLBACK
PREVIOUS_DAY_TARGET_USED
RANGE_TARGET_USED
INVALID_THESIS_REFERENCE_OVERRIDE
MULTIPLE_ELIGIBLE_TARGETS
```

---

# 42. Reason codes

Canonical:

```text
AVAILABLE
NO_FAVORABLE_SIDE_GEOMETRY
NO_ELIGIBLE_REFERENCE
NO_REACHABLE_TARGET
TARGET_TOO_FAR
THESIS_REFERENCE_INVALID
MISSING_ATR
MISSING_TICK_SIZE
MISSING_ENTRY_REFERENCE
MISSING_SET_FAMILY
MISSING_THESIS_REFERENCE_POLICY
TARGET_TOO_CLOSE_AFTER_ROUNDING
ROUNDING_ERROR
```

---

# 43. Missing-input handling

```text
ATR_15m missing or <= 0
→ MISSING_ATR

tick_size missing or <= 0
→ MISSING_TICK_SIZE

planned_entry_reference missing or <= 0
→ MISSING_ENTRY_REFERENCE

set_family missing/invalid
→ MISSING_SET_FAMILY

thesis policy missing/invalid
→ MISSING_THESIS_REFERENCE_POLICY

favorable geometry capability unavailable
→ NO_FAVORABLE_SIDE_GEOMETRY
```

Missing values are never zero-filled.

---

# 44. Dynamic TP output contract

```yaml
dynamic_tp:
  methodology:
    id: TT-METH-017
    version: 0.2.2

  snapshot:
    set_result_id:
    matched_at:
    market_snapshot_at:
    direction:
    planned_entry_reference:

  thesis_context:
    set_family:
    thesis_reference_policy:
    thesis_reference_level_id:

  target_selection:
    candidate_level_ids_before_distance_filter: []
    ineligible_level_ids_with_reason: []
    too_close_level_ids: []
    too_close_skipped_count:
    too_far_level_ids: []
    selection_terminated_by_too_far:
    first_too_far_level_id:
    first_too_far_distance_atr:
    eligible_target_level_ids: []

    selected_level_id:
    selected_level_type:
    selected_target_price:
    selected_target_timeframe:
    selected_target_available_at:
    selected_target_age_seconds:
    selected_target_priority_rank:

    alternative_eligible_target_level_ids: []

  reachability:
    atr_15m:
    min_distance_atr: 0.75
    max_distance_atr: 4.00

    raw_distance:
      price:
      pct:
      atr_units:

    rounded_distance:
      price:
      pct:
      atr_units:

  calculation:
    raw_target_price:
    rounded_target_price:

  feasibility:
    usable:
    reason:

  fallback_used: false
  warnings: []
```

---

# 45. LONG algorithm

```text
E = planned entry
A = ATR_15m

for target in LONG structural priority order:

    if target.price <= E + tick:
        record ineligible
        continue

    distance_atr = (target.price - E)/A

    if distance_atr < 0.75:
        record TOO_CLOSE
        continue

    if distance_atr > 4.00:
        record TOO_FAR
        TARGET_TOO_FAR
        stop

    selected target = target
    break

if zero basic eligible references:
    NO_ELIGIBLE_REFERENCE
elif no target selected and no TOO_FAR termination:
    NO_REACHABLE_TARGET

raw_tp = selected target price
rounded_tp = floor(raw_tp/tick)×tick

recompute rounded distance

if rounded distance < 0.75 ATR:
    TARGET_TOO_CLOSE_AFTER_ROUNDING
else:
    AVAILABLE
```

---

# 46. SHORT algorithm

```text
E = planned entry
A = ATR_15m

for target in SHORT structural priority order:

    if target.price >= E - tick:
        record ineligible
        continue

    distance_atr = (E - target.price)/A

    if distance_atr < 0.75:
        record TOO_CLOSE
        continue

    if distance_atr > 4.00:
        record TOO_FAR
        TARGET_TOO_FAR
        stop

    selected target = target
    break

if zero basic eligible references:
    NO_ELIGIBLE_REFERENCE
elif no target selected and no TOO_FAR termination:
    NO_REACHABLE_TARGET

raw_tp = selected target price
rounded_tp = ceil(raw_tp/tick)×tick

recompute rounded distance

if rounded distance < 0.75 ATR:
    TARGET_TOO_CLOSE_AFTER_ROUNDING
else:
    AVAILABLE
```

---

# 47. Research parameters

Versioned candidates:

```text
MIN_TP_DISTANCE_ATR = 0.75
MAX_TP_DISTANCE_ATR = 4.00
```

Structural hierarchy should also be tested by Set family.

Avoid unrestricted combinatorial optimization.

---

# 48. Required research reporting

At minimum:

```text
LONG separately
SHORT separately
coin
Set family
selected target type
thesis override frequency
NO_REACHABLE_TARGET frequency
too-close frequency
too-far frequency
target distance ATR
time-to-target
MAE before target
MFE
target hit rate
previous-day vs 1h target behavior
minimum-distance sensitivity
maximum-distance sensitivity
```

---

# Part V — Canonical Position Rules Invariants

1. Position Rules receives one immutable `decision_cycle_id` from Set.
2. Direction is immutable and cannot be re-inferred or reversed.
3. Market Invalidation Inputs never enter Position Rules.
4. Portfolio Rules owns `requested_capital_per_tranche`.
5. Position Rules may convert own capital into leveraged order notional but may not increase the granted own capital.
6. Entry is determined before SL and TP feasibility is finalized.
7. Fixed and Dynamic SL/TP modes are deterministic and mutually governed by user configuration.
8. Dynamic Entry / SL / TP use the frozen Market Handoff from the same Set match.
9. No missing required input may be guessed.
10. No failed gate may be silently repaired by modifying Entry, SL, TP, leverage, quantity, or capital.
11. `Minimum Risk / Reward` uses the approved gross structural R:R semantics.
12. `Minimum Net Edge` uses planned net TP profit relative to actual order notional.
13. Funding is excluded from planned Minimum Net Edge unless a future approved methodology explicitly changes this; realized funding remains lifecycle/accounting data.
14. Initial opportunity APPROVE / REJECT reaches Portfolio before it can issue Capital and Limits.
15. Order Spec follows only successful post-grant CONSTRUCTED; actual submit additionally requires matching Submit Authorized.
16. Order Spec must preserve `decision_cycle_id`.
17. Position Rules does not submit, cancel, reprice, reconcile, or manage fills.
18. Position Rules does not query API directly.
19. Position Rules does not manage portfolio reservations or cooldown.
20. Close conditions remain limited to TP / SL / Manual Close unless a future approved version explicitly changes them.
21. All formulas, thresholds, reason codes, and user-configurable settings must be versioned and auditable.

---

# Part V-A — Approval and Capital Hold Invariant

P1 is the single canonical sequence. Portfolio learns Set's cycle from initial APPROVE/REJECT. It issues a grant only after APPROVE, with that exact cycle/decision binding. Position then constructs the final spec and confirms its immutable capital basis on the existing return boundary. Portfolio validates current gates/capacity and books a hold only for CONSTRUCTED; authorization follows atomically. No hold or final spec is created at initial APPROVE.

A rejected initial opportunity has no grant. A failed post-grant construction has no hold/spec. Failed hold creates no authorization. Missing durable messages are recovered under the same IDs; no age TTL, old-result reuse for a different cycle, or new analysis is introduced.

---

# Part VI — Source Consolidation Map

The following prior documents are consolidated into this methodology:

```text
TRIGGERTRADE_POSITION_RULES_DECISION_METHODOLOGY_v0.3_APPROVED_CAPITAL_SEMANTICS
→ Part I

TRIGGERTRADE_DYNAMIC_LIMIT_ENTRY_METHODOLOGY_v0.2.2_APPROVED
→ Part II

TRIGGERTRADE_DYNAMIC_STOP_LOSS_METHODOLOGY_v0.2.1_APPROVED
→ Part III

TRIGGERTRADE_DYNAMIC_TAKE_PROFIT_METHODOLOGY_v0.2.2_APPROVED
→ Part IV
```

The approved Entry / SL / TP Set-Handoff context amendments remain upstream Set contract evidence and are consumed through `Market Handoff`; they are not separate Position Rules architecture blocks.

After approval of `POSITION_RULES.md`, the source files remain historical methodology/review artifacts rather than parallel canonical Position Rules methodologies.

---


# Appendix A — Identifier and provenance invariants (v1.1.0)

The normative owner/creation timing table is `../IDENTIFIER_LINEAGE.md`. Set creates decision_cycle_id/set_result_id at concrete MATCHED. Position creates position_decision_id before initial APPROVE/REJECT. Portfolio creates capital_grant_id only when issuing Capital and Limits after APPROVE. Final plan/tranche/spec are created during successful post-grant construction. Lifecycle creates supported client IDs before native requests; exchange IDs remain absent until supplied.

## Durable publication and native compatibility

Initial decision persistence/publication is its own transaction. Grant issue is Portfolio's later transaction. Successful construction persistence plus immutable Order Spec and CONSTRUCTED confirmation outboxes is atomic. Hold plus authorization is another atomic Portfolio transaction. Replays preserve all IDs and content. P1–P2 govern current hard compatibility without new economics, resizing or grant TTL.

## Gate serialization

CONSTRUCTION_RESULT.rule_results.minimum_net_edge preserves PASS/FAIL/UNAVAILABLE/NOT_APPLICABLE as actually evaluated after the grant. Successful CONSTRUCTED/spec accepts only true/PASS or false/NOT_APPLICABLE. Applicable max quantity is evaluated during construction, not before initial APPROVE. Above-max/unavailable is fail-closed. PARTIAL_QUANTITY is native isolation, not strategic partial closing.

## Thesis-binding boundary

P4 binds the exact producer reference. The unchanged default Entry/SL/TP candidate hierarchies below PREFERRED/NONE are calculation fallback only, not authority to replace the immutable thesis ID. REQUIRED never falls back. Position cannot infer or repair a missing binding.

---

# Appendix D — Canonical economics and construction equality

All retained Entry/SL/TP expressions, threshold values, trigger/reference selection and price/quantity rounding rules above remain unchanged. P11 and `schemas/NUMERIC_POLICY.md` determine exact arithmetic and persisted monetary/economic values: rational intermediates, existing grid rounding, conservative actual capital at Qcapital, exact threshold comparisons and ratio-only report quantization. The actual capital formula's exact quotient and its canonical persisted liability are distinguished explicitly; no epsilon or unspecified venue-rounding difference is allowed.

Before persisting the successful construction and both outboxes, independently check every P14 duplicated scalar/identity/gate against the entire immutable Order Spec. Then compute its digest and target version. A unchanged digest accompanying a changed external approved_quantity, leverage, notional, capital or planned gate scalar is invalid. Failure publishes no successful spec/confirmation and cannot be repaired by resizing the existing opportunity. Initial APPROVE still precedes grant creation and contains no final plan/tranche/spec; the existing CONSTRUCTION_RESULT variant remains the sole post-grant return to Portfolio. No direct Position Rules ↔ API dependency exists.

## Canonical Set value consumption and actual hold binding

Market Handoff v4 requires TT_SET_NUMERIC_V1. Position parses and compares the exact canonical received `volatility.atr_15m` and `atr_pct_15m`; it must not recompute/seed ATR independently, recover extra precision from another source or use display rounding at a gate. Existing Entry/SL/TP formulas, directional tick normalization and thresholds are unchanged. No direct Position ↔ API is added.

Post-grant construction continues to persist the immutable spec plus identical confirmation atomically. The canonical actual liability must not exceed the grant bound. Portfolio holds that exact actual commitment, not the grant, using SUBMIT_AUTHORIZED v5; Lifecycle independently checks the held scalar and all existing duplicated identity/economic/digest/version bindings before dispatch. An excess fails without silent resize, hold or authorization.
